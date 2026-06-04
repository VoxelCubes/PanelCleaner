"""
Per-series Workspace system for the Webtoon Translate & Cleaner.

A workspace is the top-level concept that binds together everything needed to
translate one series:
- a reference to a cleaning ``Profile`` (by saved name or vendored path),
- a ``Glossary`` file,
- the source/target languages,
- the ``TranslatorConfig`` and ``RenderConfig``,
- and the chapter/page organization with per-page processing state.

The workspace owns languages, glossary, translation and render settings. The
``Profile`` keeps owning the cleaning settings exclusively; the workspace merely
references it. This clean ownership split is what keeps the four new systems from
conflicting (see docs/redesign/01-architecture.md).

The manifest is stored as ``workspace.toml`` in the workspace root.
"""

import sys
from datetime import datetime, timezone
from pathlib import Path

from attrs import define, field
from loguru import logger

from pcleaner import toml_utils as tu
from pcleaner.glossary import Glossary
from pcleaner.translator.config import TranslatorConfig
from pcleaner.rendering.config import RenderConfig

# If using Python 3.10 or older, use the 3rd party StrEnum.
if sys.version_info < (3, 11):
    from strenum import StrEnum
else:
    from enum import StrEnum


SCHEMA_VERSION = 1
MANIFEST_NAME = "workspace.toml"
DEFAULT_GLOSSARY_NAME = "glossary.toml"


class PageState(StrEnum):
    """The processing state of a page, advancing through the pipeline."""

    raw = "raw"
    cleaned = "cleaned"
    translated = "translated"
    rendered = "rendered"


def to_page_state(value: str) -> PageState:
    """Parse a string into a PageState, defaulting to ``raw``."""
    try:
        return PageState(str(value).strip().lower())
    except ValueError:
        logger.warning(f"Unknown page state '{value}', defaulting to 'raw'.")
        return PageState.raw


@define
class ProfileRef:
    """
    A reference to the cleaning profile a workspace uses.

    Exactly one of ``name`` (a saved-profile name resolved via the global Config) or
    ``path`` (a path, possibly relative to the workspace root) is meaningful.
    """

    name: str | None = None
    path: str | None = None

    def to_dict(self) -> dict:
        data: dict = {}
        if self.name is not None:
            data["name"] = self.name
        if self.path is not None:
            data["path"] = self.path
        return data

    @classmethod
    def from_dict(cls, data: dict) -> "ProfileRef":
        return cls(name=data.get("name"), path=data.get("path"))


@define
class PageEntry:
    """A single page within a chapter, tracking its processing state."""

    file: str
    state: PageState = PageState.raw
    uuid: str | None = None

    def to_dict(self) -> dict:
        data: dict = {"file": self.file, "state": str(self.state)}
        if self.uuid is not None:
            data["uuid"] = self.uuid
        return data

    @classmethod
    def from_dict(cls, data: dict) -> "PageEntry":
        return cls(
            file=str(data["file"]),
            state=to_page_state(data.get("state", "raw")),
            uuid=data.get("uuid"),
        )


@define
class ChapterEntry:
    """A chapter: an ordered group of pages."""

    id: str
    title: str = ""
    pages: list[PageEntry] = field(factory=list)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "title": self.title,
            "pages": [p.to_dict() for p in self.pages],
        }

    @classmethod
    def from_dict(cls, data: dict) -> "ChapterEntry":
        return cls(
            id=str(data["id"]),
            title=str(data.get("title", "")),
            pages=[PageEntry.from_dict(p) for p in data.get("pages", [])],
        )


@define
class Workspace:
    """A per-series workspace, persisted as ``workspace.toml``."""

    root: Path
    name: str
    source_lang: str
    target_lang: str
    profile_ref: ProfileRef = field(factory=ProfileRef)
    glossary_path: str = DEFAULT_GLOSSARY_NAME
    translator: TranslatorConfig = field(factory=TranslatorConfig)
    render: RenderConfig = field(factory=RenderConfig)
    fonts: dict[str, str] = field(factory=dict)
    chapters: list[ChapterEntry] = field(factory=list)
    created: str = ""

    # -- Construction / persistence ------------------------------------------------

    @classmethod
    def create(
        cls,
        root: Path,
        name: str,
        source_lang: str,
        target_lang: str,
        profile_ref: ProfileRef | None = None,
    ) -> "Workspace":
        """
        Create a new workspace in memory with sensible defaults.

        Does not write anything to disk; call :meth:`save` (and optionally
        :meth:`init_dirs`) to persist it.
        """
        return cls(
            root=Path(root),
            name=name,
            source_lang=source_lang,
            target_lang=target_lang,
            profile_ref=profile_ref if profile_ref is not None else ProfileRef(),
            created=datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        )

    @classmethod
    def manifest_path(cls, root: Path) -> Path:
        return Path(root) / MANIFEST_NAME

    @classmethod
    def exists(cls, root: Path) -> bool:
        return cls.manifest_path(root).is_file()

    @classmethod
    def load(cls, root: Path) -> "Workspace":
        """
        Load a workspace from its root directory.

        :param root: The workspace root directory (containing ``workspace.toml``).
        :raises FileNotFoundError: If the manifest does not exist.
        """
        root = Path(root)
        path = cls.manifest_path(root)
        if not path.is_file():
            raise FileNotFoundError(f"No workspace manifest found at {path}")
        data = tu.load_toml(path)

        ws_meta = data.get("workspace", {})
        languages = data.get("languages", {})
        return cls(
            root=root,
            name=str(ws_meta.get("name", root.name)),
            source_lang=str(languages.get("source", "")),
            target_lang=str(languages.get("target", "")),
            profile_ref=ProfileRef.from_dict(data.get("profile", {})),
            glossary_path=str(data.get("glossary", {}).get("path", DEFAULT_GLOSSARY_NAME)),
            translator=TranslatorConfig.from_dict(data.get("translator", {})),
            render=RenderConfig.from_dict(data.get("render", {})),
            fonts={str(k): str(v) for k, v in data.get("fonts", {}).items()},
            chapters=[ChapterEntry.from_dict(c) for c in data.get("chapters", [])],
            created=str(ws_meta.get("created", "")),
        )

    def to_dict(self) -> dict:
        """Serialize the manifest to a TOML-compatible dictionary."""
        data: dict = {
            "workspace": {
                "name": self.name,
                "created": self.created,
                "schema_version": SCHEMA_VERSION,
            },
            "languages": {
                "source": self.source_lang,
                "target": self.target_lang,
            },
            "profile": self.profile_ref.to_dict(),
            "glossary": {"path": self.glossary_path},
            "translator": self.translator.to_dict(),
            "render": self.render.to_dict(),
            "fonts": dict(self.fonts),
            "chapters": [c.to_dict() for c in self.chapters],
        }
        return data

    def save(self) -> bool:
        """Write the manifest to ``<root>/workspace.toml`` atomically."""
        self.root.mkdir(parents=True, exist_ok=True)
        return tu.safe_write_toml(self.to_dict(), self.manifest_path(self.root))

    def init_dirs(self) -> None:
        """Create the standard workspace directory skeleton and an empty glossary."""
        self.root.mkdir(parents=True, exist_ok=True)
        (self.root / "chapters").mkdir(parents=True, exist_ok=True)
        self.cache_dir().mkdir(parents=True, exist_ok=True)
        glossary_path = self.resolve_glossary_path()
        if not glossary_path.exists():
            glossary = Glossary(
                name=f"{self.name} glossary",
                source_lang=self.source_lang or None,
                target_lang=self.target_lang or None,
            )
            glossary.save(glossary_path)

    # -- Resolution helpers --------------------------------------------------------

    def cache_dir(self) -> Path:
        """The workspace-scoped cleaner cache directory."""
        return self.root / "cache"

    def resolve_glossary_path(self) -> Path:
        """Resolve the glossary path, relative to the workspace root if not absolute."""
        path = Path(self.glossary_path)
        if not path.is_absolute():
            path = self.root / path
        return path

    def resolve_glossary(self) -> Glossary:
        """Load the workspace's glossary, or an empty one if it is missing."""
        path = self.resolve_glossary_path()
        if not path.exists():
            return Glossary(
                name=f"{self.name} glossary",
                source_lang=self.source_lang or None,
                target_lang=self.target_lang or None,
            )
        return Glossary.load(path)

    def resolve_profile(self, config) -> "object":
        """
        Resolve this workspace's profile reference to a loaded ``config.Profile``.

        Bridges to the existing ``Profile.load`` machinery so the cleaning pipeline
        never needs to know a workspace is involved. Imported lazily to avoid pulling
        the heavy config/model dependency chain when only the manifest is needed.

        :param config: The global ``config.Config`` used to resolve saved-profile names.
        :return: A ``config.Profile`` instance (the built-in default if unresolved).
        """
        import pcleaner.config as cfg

        ref = self.profile_ref
        if ref.path:
            path = Path(ref.path)
            if not path.is_absolute():
                path = self.root / path
            if path.is_file():
                return cfg.Profile.load(path)
            logger.warning(f"Workspace profile path does not exist: {path}")
        if ref.name and ref.name in config.saved_profiles:
            return cfg.Profile.load(config.saved_profiles[ref.name])
        if ref.name:
            logger.warning(f"Workspace references unknown profile '{ref.name}', using default.")
        return cfg.Profile()

    # -- State tracking ------------------------------------------------------------

    def get_chapter(self, chapter_id: str) -> ChapterEntry | None:
        for chapter in self.chapters:
            if chapter.id == chapter_id:
                return chapter
        return None

    def set_page_state(
        self, chapter_id: str, page_file: str, state: PageState, uuid: str | None = None
    ) -> bool:
        """
        Update the processing state (and optionally uuid) of a page.

        This is the single source of truth for per-page progress. Returns True if the
        page was found and updated.
        """
        chapter = self.get_chapter(chapter_id)
        if chapter is None:
            return False
        for page in chapter.pages:
            if page.file == page_file:
                page.state = state
                if uuid is not None:
                    page.uuid = uuid
                return True
        return False

    def progress_summary(self) -> dict[PageState, int]:
        """Count pages across all chapters by their current state."""
        counts = {state: 0 for state in PageState}
        for chapter in self.chapters:
            for page in chapter.pages:
                counts[page.state] += 1
        return counts
