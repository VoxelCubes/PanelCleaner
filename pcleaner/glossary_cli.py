"""
CLI handlers for managing a workspace's glossary.

Glossary operations always act on a workspace's glossary file. The workspace is
resolved from the ``--workspace`` option (a saved name or a path), falling back to the
configured default workspace.
"""

import csv
from pathlib import Path

import prettytable as pt

import pcleaner.cli_utils as cli
import pcleaner.config as cfg
from pcleaner.glossary import Glossary, GlossaryEntry, TermType, to_term_type
from pcleaner.workspace import Workspace

CSV_FIELDS = ["source", "target", "type", "notes", "case_sensitive", "do_not_translate"]


def _resolve_workspace_root(config: cfg.Config, workspace: str | None) -> Path | None:
    """Resolve the workspace root from a name/path option or the configured default."""
    target = workspace or config.default_workspace
    if target is None:
        return None
    # Allow passing a direct path to a workspace directory.
    as_path = Path(target)
    if Workspace.exists(as_path):
        return as_path
    match = cli.closest_match(target, list(config.saved_workspaces.keys()))
    if match is None:
        return None
    return config.saved_workspaces[match]


def _load_glossary(config: cfg.Config, workspace: str | None) -> tuple[Glossary, Path] | None:
    """Load the glossary for the resolved workspace, returning it with its path."""
    root = _resolve_workspace_root(config, workspace)
    if root is None:
        print(
            "No workspace specified or found. Pass --workspace=<name|path> "
            "or set a default workspace."
        )
        return None
    try:
        ws = Workspace.load(root)
    except FileNotFoundError:
        print(f"Workspace manifest missing at {root}.")
        return None
    return ws.resolve_glossary(), ws.resolve_glossary_path()


def list_terms(config: cfg.Config, workspace: str | None) -> None:
    """Display all glossary entries in a table."""
    loaded = _load_glossary(config, workspace)
    if loaded is None:
        return
    glossary, path = loaded
    if not glossary.entries:
        print(f"Glossary at {path} is empty.")
        return

    table = pt.PrettyTable()
    table.set_style(pt.SINGLE_BORDER)
    table.field_names = ["Source", "Target", "Type", "DNT", "Notes"]
    table.align["Source"] = "l"
    table.align["Target"] = "l"
    table.align["Notes"] = "l"
    for entry in glossary.entries:
        table.add_row(
            [
                entry.source,
                entry.target,
                str(entry.type),
                "yes" if entry.do_not_translate else "",
                entry.notes,
            ]
        )
    print(table)


def validate_glossary(config: cfg.Config, workspace: str | None) -> None:
    """Validate the glossary and print any warnings."""
    loaded = _load_glossary(config, workspace)
    if loaded is None:
        return
    glossary, path = loaded
    warnings = glossary.validate()
    if not warnings:
        print(f"Glossary at {path} is valid ({len(glossary.entries)} entries).")
        return
    print(f"Glossary at {path} has {len(warnings)} issue(s):")
    for warning in warnings:
        print(f"  - {warning}")


def add_term(
    config: cfg.Config,
    workspace: str | None,
    source: str,
    target: str,
    term_type: str | None,
    notes: str | None,
) -> None:
    """Add or update a glossary entry."""
    loaded = _load_glossary(config, workspace)
    if loaded is None:
        return
    glossary, path = loaded
    resolved_type = to_term_type(term_type) if term_type else TermType.term
    entry = GlossaryEntry(
        source=source,
        target=target,
        type=resolved_type,
        notes=notes or "",
        do_not_translate=resolved_type == TermType.do_not_translate,
    )
    glossary.add(entry)
    if glossary.save(path):
        print(f"Added '{source}' -> '{target}' to glossary at {path}.")
    else:
        print(f"Failed to write glossary at {path}.")


def remove_term(config: cfg.Config, workspace: str | None, source: str) -> None:
    """Remove a glossary entry by its source term."""
    loaded = _load_glossary(config, workspace)
    if loaded is None:
        return
    glossary, path = loaded
    if glossary.remove(source):
        if glossary.save(path):
            print(f"Removed '{source}' from glossary at {path}.")
        else:
            print(f"Failed to write glossary at {path}.")
    else:
        print(f"Term '{source}' not found in glossary.")


def import_glossary(config: cfg.Config, workspace: str | None, file: str) -> None:
    """Import glossary entries from a CSV file, merging into the existing glossary."""
    loaded = _load_glossary(config, workspace)
    if loaded is None:
        return
    glossary, path = loaded
    csv_path = Path(file)
    if not csv_path.is_file():
        print(f"CSV file not found: {csv_path}")
        return

    count = 0
    with open(csv_path, "r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if not row.get("source"):
                continue
            glossary.add(GlossaryEntry.from_dict(row))
            count += 1
    if glossary.save(path):
        print(f"Imported {count} entries into glossary at {path}.")
    else:
        print(f"Failed to write glossary at {path}.")


def export_glossary(config: cfg.Config, workspace: str | None, file: str) -> None:
    """Export the glossary to a CSV file."""
    loaded = _load_glossary(config, workspace)
    if loaded is None:
        return
    glossary, _ = loaded
    csv_path = Path(file)
    with open(csv_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_FIELDS)
        writer.writeheader()
        for entry in glossary.entries:
            writer.writerow(entry.to_dict())
    print(f"Exported {len(glossary.entries)} entries to {csv_path}.")
