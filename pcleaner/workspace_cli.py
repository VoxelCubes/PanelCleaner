"""
CLI handlers for managing Webtoon Translate & Cleaner workspaces.

Mirrors the style of ``profile_cli.py``: each function takes the global ``Config`` and
operates on the registered workspaces, printing user-facing output directly.
"""

from pathlib import Path

import prettytable as pt

import pcleaner.cli_utils as cli
import pcleaner.config as cfg
from pcleaner.workspace import Workspace, ProfileRef, PageState
from pcleaner import workspace_runner as wr


def _resolve_root(config: cfg.Config, name: str) -> Path | None:
    """Resolve a workspace name (fuzzy) to its root directory, or None if not found."""
    match = cli.closest_match(name, list(config.saved_workspaces.keys()))
    if match is None:
        return None
    return config.saved_workspaces[match]


def list_workspaces(config: cfg.Config) -> None:
    """Display the registered workspaces in a table."""
    if not config.saved_workspaces:
        print(
            "No workspaces saved.\n\n"
            "Create a new workspace with:\n"
            "   pcleaner workspace new <name> --source=<lang> --target=<lang>\n"
            "or register an existing one with:\n"
            "   pcleaner workspace add <name> <path>"
        )
        return

    def check_status(path: Path) -> str:
        return "OK" if Workspace.exists(path) else "Manifest not found"

    table = pt.PrettyTable()
    table.set_style(pt.SINGLE_BORDER)
    table.field_names = ["Workspace", "Path", "Status", "Default"]
    table.align["Path"] = "l"
    for name, path in config.saved_workspaces.items():
        default = "Yes" if name == config.default_workspace else ""
        table.add_row([name, path, check_status(path), default])
    print(table)


def new_workspace(
    config: cfg.Config,
    name: str,
    path: str | None,
    source: str,
    target: str,
    profile: str | None,
) -> tuple[bool, str]:
    """
    Create a new workspace directory, manifest and empty glossary.

    :param config: The global config.
    :param name: The workspace name (used for registration and the default directory).
    :param path: Optional explicit path; defaults to the standard workspaces directory.
    :param source: Source language code.
    :param target: Target language code.
    :param profile: Optional saved-profile name to reference for cleaning.
    """
    if not name:
        return False, "Workspace name cannot be empty."
    if name in config.saved_workspaces:
        return False, "Workspace name already in use."

    root = Path(path) if path else cli.get_workspaces_path(name)
    if Workspace.exists(root):
        if not cli.get_confirmation(f"A workspace already exists at {root}. Overwrite manifest?"):
            return False, "Aborted."

    profile_ref = ProfileRef(name=profile) if profile else ProfileRef()
    if profile and profile not in config.saved_profiles:
        print(f"Warning: profile '{profile}' is not a saved profile; it may not resolve later.")

    workspace = Workspace.create(root, name, source, target, profile_ref)
    workspace.init_dirs()
    if not workspace.save():
        return False, f"Failed to write workspace manifest at {root}."

    config.add_workspace(name, root)
    config.save()
    return True, f"Workspace '{name}' created at {root}."


def add_workspace(config: cfg.Config, name: str, path: str) -> tuple[bool, str]:
    """Register an existing workspace directory under a name."""
    if not name:
        return False, "Workspace name cannot be empty."
    if name in config.saved_workspaces:
        return False, "Workspace name already in use."
    root = Path(path)
    if not Workspace.exists(root):
        return False, f"No workspace manifest found at {root}."
    config.add_workspace(name, root)
    config.save()
    return True, f"Workspace '{name}' added."


def info_workspace(config: cfg.Config, name: str) -> None:
    """Print the manifest details of a workspace."""
    root = _resolve_root(config, name)
    if root is None:
        print(f"Workspace '{name}' not found.")
        return
    try:
        ws = Workspace.load(root)
    except FileNotFoundError:
        print(f"Workspace manifest missing at {root}.")
        return

    profile_desc = ws.profile_ref.name or ws.profile_ref.path or "(built-in default)"
    print(f"Workspace: {ws.name}")
    print(f"  Path:      {root}")
    print(f"  Languages: {ws.source_lang or '?'} -> {ws.target_lang or '?'}")
    print(f"  Profile:   {profile_desc}")
    print(f"  Glossary:  {ws.resolve_glossary_path()}")
    print(f"  Model:     {ws.translator.model}")
    print(f"  Chapters:  {len(ws.chapters)}")


def status_workspace(config: cfg.Config, name: str) -> None:
    """Print per-state page counts for a workspace."""
    root = _resolve_root(config, name)
    if root is None:
        print(f"Workspace '{name}' not found.")
        return
    try:
        ws = Workspace.load(root)
    except FileNotFoundError:
        print(f"Workspace manifest missing at {root}.")
        return

    counts = ws.progress_summary()
    total = sum(counts.values())
    print(f"Workspace '{ws.name}' progress ({total} page(s)):")
    for state in PageState:
        print(f"  {state.value:<11} {counts[state]}")


def open_workspace(config: cfg.Config, name: str) -> None:
    """Open the workspace manifest in the configured editor."""
    root = _resolve_root(config, name)
    if root is None:
        print(f"Workspace '{name}' not found.")
        return
    cli.open_file_with_editor(Workspace.manifest_path(root), config.profile_editor)


def _ocr_bubbles_by_stem(ocr_file) -> dict:
    """Parse an OCR output file into a mapping of image stem -> list of Bubbles."""
    from pathlib import Path
    import pcleaner.ocr.parsers as parsers
    from pcleaner.translator.batching import Bubble

    analytics, errors = parsers.parse_ocr_data(Path(ocr_file))
    for error in errors:
        print(f"Warning: {error}")
    out: dict[str, list] = {}
    for analytic in analytics:
        stem = Path(analytic.path).stem
        out[stem] = [
            Bubble(index=i, box=box.as_tuple, text=text)
            for i, (text, box) in enumerate(analytic.removed_box_data)
        ]
    return out


def _run_clean_stage(config: cfg.Config, ws: "Workspace", jobs: list, force: bool) -> None:
    """Delegate cleaning of raw pages to the existing pipeline, per chapter (full env only)."""
    from pathlib import Path
    import pcleaner.main as main

    by_chapter: dict[str, list] = {}
    for job in jobs:
        if force or not wr.at_least(job.state, PageState.cleaned):
            by_chapter.setdefault(job.chapter_id, []).append(job)
    for chapter_id, chapter_jobs in by_chapter.items():
        raw_images = [j.raw_path for j in chapter_jobs if j.raw_path.is_file()]
        if not raw_images:
            continue
        cleaned_dir = wr.chapter_subdir(ws, chapter_id, "cleaned")
        cleaned_dir.mkdir(parents=True, exist_ok=True)
        print(f"Cleaning {len(raw_images)} page(s) in chapter {chapter_id}...")
        main.run_cleaner(
            image_paths=raw_images,
            output_dir=cleaned_dir,
            config=config,
            skip_text_detection=False,
            skip_pre_processing=False,
            skip_masking=False,
            skip_denoising=False,
            skip_inpainting=False,
            save_only_mask=False,
            save_only_cleaned=True,
            save_only_text=False,
            extract_text=False,
            cache_masks=False,
            hide_analytics=True,
            keep_cache=True,
            debug=False,
        )
        for job in chapter_jobs:
            ws.set_page_state(job.chapter_id, job.file, PageState.cleaned, job.uuid)


def run_workspace(
    config: cfg.Config,
    name: str,
    ocr_file: str | None,
    chapter: str | None,
    stage: str | None,
    do_clean: bool,
    force: bool,
    dry_run: bool,
    scale: str | None,
) -> None:
    """
    Run the end-to-end pipeline for a workspace: (optional clean) -> translate -> render.

    Pages are discovered from ``chapters/<id>/raw/`` and synced into the manifest. Each
    stage advances the page state (raw -> cleaned -> translated -> rendered) and is skipped
    for pages already past it (unless ``--force``). The heavy clean stage is delegated to
    the existing pipeline; translate and render use the workspace's settings.

    :param config: The global config (provides the OpenRouter API key).
    :param name: The workspace name or path.
    :param ocr_file: OCR output file (from ``pcleaner ocr``) providing per-page text+boxes.
    :param chapter: Limit to one chapter id, or None for all.
    :param stage: The final stage to reach: ``clean``, ``translate`` or ``render`` (default).
    :param do_clean: Whether to run the (delegated) clean stage first.
    :param force: Re-run stages even for pages already past them.
    :param dry_run: Print the plan without translating, rendering or calling the API.
    :param scale: Optional render coordinate scale override (string parsed to float).
    """
    from pathlib import Path

    root = _resolve_root(config, name)
    if root is None:
        print(f"Workspace '{name}' not found.")
        return
    try:
        ws = Workspace.load(root)
    except FileNotFoundError:
        print(f"Workspace manifest missing at {root}.")
        return

    target_stage = (stage or "render").lower()
    if target_stage not in ("clean", "translate", "render"):
        print(f"Invalid --stage '{stage}'. Use clean, translate or render.")
        return

    added = wr.sync_manifest(ws, chapter)
    ws.save()
    jobs = wr.build_jobs(ws, chapter)
    if not jobs:
        print("No pages found. Add images under chapters/<id>/raw/ first.")
        return

    if dry_run:
        counts = ws.progress_summary()
        print(f"Workspace '{ws.name}' plan (target stage: {target_stage}):")
        print(f"  Pages discovered: {len(jobs)} ({added} newly added)")
        for state in PageState:
            print(f"  {state.value:<11} {counts[state]}")
        return

    want_translate = target_stage in ("translate", "render")
    want_render = target_stage == "render"

    if do_clean:
        _run_clean_stage(config, ws, jobs, force)
        ws.save()
        jobs = wr.build_jobs(ws, chapter)  # refresh states after cleaning

    if not want_translate:
        ws.save()
        print(f"Done. {_status_line(ws)}")
        return

    bubbles_by_stem: dict = {}
    if ocr_file:
        bubbles_by_stem = _ocr_bubbles_by_stem(ocr_file)
    else:
        print("No --ocr file provided; cannot translate. Run `pcleaner ocr` first.")
        return

    glossary = ws.resolve_glossary()
    fonts = wr.build_font_registry(ws)

    api_key = config.get_openrouter_api_key()
    if not api_key:
        print(
            "No OpenRouter API key found. Set OPENROUTER_API_KEY or the [OpenRouter] "
            "api_key option in the config."
        )
        return
    from pcleaner.translator.openrouter import OpenRouterClient, OpenRouterError

    client = OpenRouterClient(api_key, max_retries=ws.translator.max_retries)
    runner = wr.WorkspaceTranslateRender(ws=ws, glossary=glossary, fonts=fonts, client=client)

    try:
        scale_override = float(scale) if scale else None
    except ValueError:
        print(f"Invalid --scale value: {scale}")
        return

    cleaner_cache = config.get_cleaner_cache_dir()
    for job in jobs:
        if force or not wr.at_least(job.state, PageState.translated):
            bubbles = bubbles_by_stem.get(Path(job.file).stem, [])
            try:
                runner.translate_job(job, bubbles, force=force)
            except OpenRouterError as e:
                print(f"Translation failed for {job.file}: {e}")
                ws.save()
                return
        if want_render:
            page_scale = (
                scale_override
                if scale_override is not None
                else wr.read_scale_from_clean_json(cleaner_cache, job.raw_path)
            )
            runner.render_job(job, scale=page_scale)
        print(f"  {job.chapter_id}/{job.file}")

    ws.save()
    print(runner.accounting.summary())
    print(_status_line(ws))


def _status_line(ws: "Workspace") -> str:
    counts = ws.progress_summary()
    return " | ".join(f"{state.value}: {counts[state]}" for state in PageState)


def gui_workspace(config: cfg.Config, name: str | None) -> None:
    """
    Launch the Webtoon Translate & Cleaner GUI (workspace browser + glossary editor).

    :param config: The global config.
    :param name: Optional workspace name to open the glossary editor for directly.
    """
    try:
        from pcleaner.gui import webtoon_launcher
    except Exception as e:  # PySide6 missing or import error.
        print(f"The GUI is unavailable (is PySide6 installed?): {e}")
        return
    webtoon_launcher.launch(config, name)
