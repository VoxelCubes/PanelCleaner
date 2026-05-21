#!/usr/bin/env python3
"""Sync install_requires in setup-*.cfg from uv dependency groups."""
from __future__ import annotations

from pathlib import Path

try:
    import tomllib  # Python 3.11+
except ModuleNotFoundError:  # pragma: no cover - fallback for Python 3.10
    import tomli as tomllib

ROOT = Path(__file__).resolve().parents[1]
PYPROJECT = ROOT / "pyproject.toml"
SETUP_CLI = ROOT / "setup-cli.cfg"
SETUP_GUI = ROOT / "setup-cli-gui.cfg"


def load_groups() -> dict[str, list[str]]:
    data = tomllib.loads(PYPROJECT.read_text(encoding="utf-8"))
    groups = data.get("dependency-groups")
    if not isinstance(groups, dict):
        raise RuntimeError("Missing [dependency-groups] in pyproject.toml")
    return groups


def merge_groups(groups: dict[str, list[str]], names: list[str]) -> list[str]:
    merged: list[str] = []
    seen: set[str] = set()
    for name in names:
        if name not in groups:
            raise RuntimeError(f"Missing dependency group: {name}")
        for requirement in groups[name]:
            if requirement not in seen:
                merged.append(requirement)
                seen.add(requirement)
    return merged


def replace_install_requires(path: Path, requirements: list[str]) -> None:
    lines = path.read_text(encoding="utf-8").splitlines(keepends=True)
    start_index = None
    for i, line in enumerate(lines):
        if line.strip() == "install_requires =":
            start_index = i
            break
    if start_index is None:
        raise RuntimeError(f"install_requires not found in {path}")

    end_index = start_index + 1
    while end_index < len(lines):
        stripped = lines[end_index].strip()
        if not stripped:
            break
        if lines[end_index].startswith((" ", "\t")):
            end_index += 1
            continue
        break

    replacement = ["install_requires =\n"]
    replacement.extend(f"    {req}\n" for req in requirements)
    lines[start_index:end_index] = replacement
    path.write_text("".join(lines), encoding="utf-8")


def main() -> int:
    groups = load_groups()
    replace_install_requires(SETUP_CLI, merge_groups(groups, ["runtime-base"]))
    replace_install_requires(SETUP_GUI, merge_groups(groups, ["runtime-base", "runtime-gui"]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
