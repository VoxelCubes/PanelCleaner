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
