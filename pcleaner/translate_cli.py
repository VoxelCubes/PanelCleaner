"""
CLI handler for the ``translate`` subcommand.

Reads an OCR output file (the CSV/TXT produced by ``pcleaner ocr``), translates each
page's bubbles via OpenRouter using the active workspace's languages, glossary and
translator settings, and writes a ``<image_stem>#translated.json`` sidecar per page.

The workspace owns the languages, glossary and model; the global config (or the
OPENROUTER_API_KEY environment variable) provides the API key.
"""

from pathlib import Path

import pcleaner.cli_utils as cli
import pcleaner.config as cfg
from pcleaner.workspace import Workspace
from pcleaner.translator import cache as tcache
from pcleaner.translator.batching import Bubble
from pcleaner.translator.structures import CostAccounting
from pcleaner.translator.translate import (
    TranslatePageData,
    translate_page,
    estimate_request_count,
    estimate_source_chars,
)


def _resolve_workspace_root(config: cfg.Config, workspace: str | None) -> Path | None:
    """Resolve the workspace root from a name/path option or the configured default."""
    target = workspace or config.default_workspace
    if target is None:
        return None
    as_path = Path(target)
    if Workspace.exists(as_path):
        return as_path
    match = cli.closest_match(target, list(config.saved_workspaces.keys()))
    if match is None:
        return None
    return config.saved_workspaces[match]


def _ocr_file_to_pages(ocr_file: Path) -> list[TranslatePageData]:
    """Parse an OCR output file into per-page translate data."""
    import pcleaner.ocr.parsers as parsers

    analytics, errors = parsers.parse_ocr_data(ocr_file)
    for error in errors:
        print(f"Warning: {error}")
    pages: list[TranslatePageData] = []
    for analytic in analytics:
        bubbles = [
            Bubble(index=i, box=box.as_tuple, text=text)
            for i, (text, box) in enumerate(analytic.removed_box_data)
        ]
        pages.append(TranslatePageData(image_path=str(analytic.path), bubbles=bubbles))
    return pages


def run_translate(
    config: cfg.Config,
    ocr_file: str,
    workspace: str | None,
    output: str | None,
    model: str | None,
    force: bool,
    dry_run: bool,
) -> None:
    """
    Translate the bubbles in an OCR output file using a workspace's settings.

    :param config: The global config (provides the API key).
    :param ocr_file: Path to the OCR output file (CSV or TXT) from ``pcleaner ocr``.
    :param workspace: The workspace name or path (falls back to the default workspace).
    :param output: Optional output directory for the sidecars (defaults to the workspace cache).
    :param model: Optional model override.
    :param force: Retranslate even if a cached sidecar exists.
    :param dry_run: Estimate work and cost without calling the API.
    """
    root = _resolve_workspace_root(config, workspace)
    if root is None:
        print(
            "No workspace specified or found. Pass --workspace=<name|path> "
            "or set a default workspace."
        )
        return
    try:
        ws = Workspace.load(root)
    except FileNotFoundError:
        print(f"Workspace manifest missing at {root}.")
        return

    if not ws.source_lang or not ws.target_lang:
        print("Workspace is missing source/target languages; set them in workspace.toml.")
        return

    ocr_path = Path(ocr_file)
    if not ocr_path.is_file():
        print(f"OCR file not found: {ocr_path}")
        return

    pages = _ocr_file_to_pages(ocr_path)
    if not pages:
        print("No OCR data found to translate.")
        return

    glossary = ws.resolve_glossary()
    translator_config = ws.translator
    used_model = model or config.openrouter_default_model or translator_config.model
    output_dir = Path(output) if output else ws.cache_dir()
    output_dir.mkdir(parents=True, exist_ok=True)

    total_bubbles = sum(len(p.bubbles) for p in pages)

    if dry_run:
        requests = sum(estimate_request_count(p, translator_config) for p in pages)
        chars = sum(estimate_source_chars(p) for p in pages)
        print("Dry run (no API calls):")
        print(f"  Pages:           {len(pages)}")
        print(f"  Bubbles:         {total_bubbles}")
        print(f"  Source chars:    {chars}")
        print(f"  Batch size:      {translator_config.batch_size}")
        print(f"  Est. requests:   {requests}")
        print(f"  Model:           {used_model}")
        print(f"  Languages:       {ws.source_lang} -> {ws.target_lang}")
        return

    api_key = config.get_openrouter_api_key()
    if not api_key:
        print(
            "No OpenRouter API key found. Set the OPENROUTER_API_KEY environment variable "
            "or the [OpenRouter] api_key option in the config."
        )
        return

    from pcleaner.translator.openrouter import OpenRouterClient, OpenRouterError

    client = OpenRouterClient(api_key, max_retries=translator_config.max_retries)
    accounting = CostAccounting()

    print(f"Translating {total_bubbles} bubble(s) across {len(pages)} page(s)...")
    for page in pages:
        sidecar = tcache.sidecar_path(output_dir, Path(page.image_path))
        existing = tcache.load_if_exists(sidecar)
        try:
            result = translate_page(
                page,
                client=client,
                glossary=glossary,
                config=translator_config,
                source_lang=ws.source_lang,
                target_lang=ws.target_lang,
                model=used_model,
                existing=existing,
                force=force,
                accounting=accounting,
            )
        except OpenRouterError as e:
            print(f"Translation failed for {page.image_path}: {e}")
            return
        result.save(sidecar)
        print(f"  {Path(page.image_path).name}: {len(result.results)} bubble(s) -> {sidecar.name}")

    print(accounting.summary())
