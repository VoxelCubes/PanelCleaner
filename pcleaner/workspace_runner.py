"""
Workspace orchestration: tie the clean -> translate -> render stages together for a
whole series, tracking per-page state in the manifest and supporting resume.

The heavy clean/OCR stages are delegated to the existing pipeline by the CLI; this module
owns the testable parts: discovering pages, syncing the manifest, the page-state machine,
and translating + rendering across a workspace via injected seams (an OCR provider and a
translator client). That keeps the orchestration unit-testable without torch.
"""

from pathlib import Path
from uuid import uuid4

from attrs import define, field, frozen
from loguru import logger

from pcleaner.workspace import Workspace, PageState, PageEntry, ChapterEntry
from pcleaner.glossary import Glossary
from pcleaner.rendering.config import RenderConfig
from pcleaner.rendering.fonts import FontRegistry
from pcleaner.rendering import render as rnd
from pcleaner.translator import cache as tcache
from pcleaner.translator.batching import Bubble
from pcleaner.translator.config import TranslatorConfig
from pcleaner.translator.structures import CostAccounting
from pcleaner.translator.translate import TranslatePageData, translate_page, TranslatorClient

# Mirrors cfg.SUPPORTED_IMG_TYPES, kept local to avoid importing the heavy config module.
IMAGE_SUFFIXES = {
    ".png", ".jpg", ".jpeg", ".webp", ".bmp", ".tiff", ".tif", ".jp2", ".dib", ".ppm"
}

# The ordered stages a page advances through.
STAGE_RANK = {
    PageState.raw: 0,
    PageState.cleaned: 1,
    PageState.translated: 2,
    PageState.rendered: 3,
}


def stage_rank(state: PageState) -> int:
    """The ordinal of a page state in the processing pipeline."""
    return STAGE_RANK[state]


def at_least(state: PageState, target: PageState) -> bool:
    """True if ``state`` is at or past ``target`` in the pipeline."""
    return stage_rank(state) >= stage_rank(target)


def chapter_subdir(ws: Workspace, chapter_id: str, name: str) -> Path:
    """Return ``<root>/chapters/<chapter_id>/<name>``."""
    return ws.root / "chapters" / chapter_id / name


def build_font_registry(ws: Workspace) -> FontRegistry:
    """Build a font registry from a workspace's render config, fonts map and fonts dir."""
    user_dirs = []
    fonts_dir = ws.root / "fonts"
    if fonts_dir.is_dir():
        user_dirs.append(fonts_dir)
    return FontRegistry(
        default_font=ws.render.default_font,
        per_language=ws.fonts,
        user_font_dirs=user_dirs,
    )


@frozen
class PageJob:
    """A unit of work for one page, with its resolved input/output paths and state."""

    chapter_id: str
    file: str
    raw_path: Path
    cleaned_path: Path
    rendered_path: Path
    state: PageState
    uuid: str


def _list_chapter_dirs(ws: Workspace) -> list[str]:
    """List chapter ids that exist on disk under ``chapters/``."""
    chapters_root = ws.root / "chapters"
    if not chapters_root.is_dir():
        return []
    return sorted(p.name for p in chapters_root.iterdir() if p.is_dir())


def _list_raw_images(ws: Workspace, chapter_id: str) -> list[str]:
    """List raw image filenames for a chapter, sorted, found under ``chapters/<id>/raw/``."""
    raw_dir = chapter_subdir(ws, chapter_id, "raw")
    if not raw_dir.is_dir():
        return []
    return sorted(
        p.name for p in raw_dir.iterdir() if p.is_file() and p.suffix.lower() in IMAGE_SUFFIXES
    )


def sync_manifest(ws: Workspace, chapter_id: str | None = None) -> int:
    """
    Reflect the on-disk ``chapters/<id>/raw/`` images into the manifest.

    Adds any missing chapters and pages (assigning a uuid), preserving the state and uuid
    of pages that already exist. Does not remove entries whose files are gone. Returns the
    number of pages added.

    :param ws: The workspace (mutated in place; call ``ws.save()`` to persist).
    :param chapter_id: Limit to one chapter, or None for all chapters found on disk.
    :return: The number of new page entries added.
    """
    target_chapters = [chapter_id] if chapter_id else _list_chapter_dirs(ws)
    added = 0
    for cid in target_chapters:
        chapter = ws.get_chapter(cid)
        if chapter is None:
            chapter = ChapterEntry(id=cid, title=cid)
            ws.chapters.append(chapter)
        existing_files = {p.file for p in chapter.pages}
        for filename in _list_raw_images(ws, cid):
            if filename not in existing_files:
                chapter.pages.append(
                    PageEntry(file=filename, state=PageState.raw, uuid=uuid4().hex)
                )
                added += 1
        # Ensure every page has a uuid (older manifests may lack one).
        for page in chapter.pages:
            if not page.uuid:
                page.uuid = uuid4().hex
    return added


def build_jobs(ws: Workspace, chapter_id: str | None = None) -> list[PageJob]:
    """
    Build the list of page jobs from the manifest (after :func:`sync_manifest`).

    :param ws: The workspace.
    :param chapter_id: Limit to one chapter, or None for all chapters.
    :return: The page jobs in chapter/page order.
    """
    jobs: list[PageJob] = []
    for chapter in ws.chapters:
        if chapter_id and chapter.id != chapter_id:
            continue
        raw_dir = chapter_subdir(ws, chapter.id, "raw")
        cleaned_dir = chapter_subdir(ws, chapter.id, "cleaned")
        rendered_dir = chapter_subdir(ws, chapter.id, "rendered")
        for page in chapter.pages:
            stem = Path(page.file).stem
            jobs.append(
                PageJob(
                    chapter_id=chapter.id,
                    file=page.file,
                    raw_path=raw_dir / page.file,
                    cleaned_path=cleaned_dir / page.file,
                    rendered_path=rendered_dir / f"{stem}.png",
                    state=page.state,
                    uuid=page.uuid or uuid4().hex,
                )
            )
    return jobs


def read_scale_from_clean_json(cache_dir: Path, image_path: Path) -> float:
    """
    Best-effort read of the original/processing scale from a page's ``#clean.json``.

    The cleaner writes ``{uuid}_{stem}#clean.json`` into its cache. Box coordinates are in
    the processing (png) space; ``PageData.scale`` is the size of the original relative to
    that png, so rendering onto the original-resolution cleaned image uses this scale.

    :param cache_dir: The cleaner cache directory to search.
    :param image_path: The page image (only its stem is used).
    :return: The scale factor, or 1.0 if it cannot be determined.
    """
    cache_dir = Path(cache_dir)
    if not cache_dir.is_dir():
        return 1.0
    stem = Path(image_path).stem
    matches = sorted(cache_dir.glob(f"*{stem}#clean.json")) + sorted(
        cache_dir.glob(f"{stem}#clean.json")
    )
    for candidate in matches:
        try:
            import json

            data = json.loads(candidate.read_text(encoding="utf-8"))
            scale = float(data.get("scale", 1.0))
            return scale if scale > 0 else 1.0
        except Exception:
            logger.debug(f"Could not read scale from {candidate}; using 1.0.")
    return 1.0


@define
class WorkspaceTranslateRender:
    """
    Translate and render page jobs for a workspace using injected seams.

    The OCR provider yields the source bubbles for a job; the translator client performs
    the LLM calls. Both are injected so the whole flow is testable without torch/network.
    """

    ws: Workspace
    glossary: Glossary
    fonts: FontRegistry
    client: TranslatorClient | None = None
    accounting: CostAccounting = field(factory=CostAccounting)

    def _sidecar(self, job: PageJob) -> Path:
        return tcache.sidecar_path(self.ws.cache_dir(), job.raw_path)

    def translate_job(self, job: PageJob, bubbles: list[Bubble], *, force: bool = False) -> bool:
        """
        Translate one page's bubbles and write its ``#translated.json`` sidecar.

        :return: True if the page is now translated, False if there was nothing to do.
        """
        if self.client is None:
            raise ValueError("A translator client is required to translate.")
        if not bubbles:
            return False
        config: TranslatorConfig = self.ws.translator
        sidecar = self._sidecar(job)
        existing = tcache.load_if_exists(sidecar)
        page = TranslatePageData(image_path=str(job.raw_path), bubbles=bubbles)
        result = translate_page(
            page,
            client=self.client,
            glossary=self.glossary,
            config=config,
            source_lang=self.ws.source_lang,
            target_lang=self.ws.target_lang,
            existing=existing,
            force=force,
            accounting=self.accounting,
        )
        self.ws.cache_dir().mkdir(parents=True, exist_ok=True)
        result.save(sidecar)
        self.ws.set_page_state(job.chapter_id, job.file, PageState.translated, job.uuid)
        return True

    def render_job(self, job: PageJob, *, scale: float = 1.0) -> bool:
        """
        Render a page's translations onto its cleaned image (falling back to the raw image).

        :return: True if a rendered image was produced, False if no translation exists.
        """
        page_translation = tcache.load_if_exists(self._sidecar(job))
        if page_translation is None:
            return False
        canvas_path = job.cleaned_path if job.cleaned_path.is_file() else job.raw_path
        if not canvas_path.is_file():
            logger.warning(f"No image to render onto for {job.file}; skipping.")
            return False
        config: RenderConfig = self.ws.render
        rnd.render_to_file(
            canvas_path, page_translation, job.rendered_path, config, self.fonts, scale
        )
        self.ws.set_page_state(job.chapter_id, job.file, PageState.rendered, job.uuid)
        return True
