"""
Font management for text rendering.

Resolves which font file to use for a given language and loads it at a requested size.
Resolution order for a configured font (a name or a path):
1. an explicit per-language override (``RenderConfig`` + the workspace ``[fonts]`` map),
2. the configured default font,
3. the bundled fallback font (LiberationSans).

A configured value may be an existing file path, or a font name that is matched against
user font directories and the bundled ``pcleaner/data`` (and ``pcleaner/data/fonts``)
directories. This module only depends on PIL and ``pcleaner.data`` (a resource-only
package), so it stays lightweight.
"""

from importlib import resources
from pathlib import Path

from loguru import logger
from PIL import ImageFont

import pcleaner.data

# The always-available fallback shipped with Panel Cleaner.
BUNDLED_FALLBACK = "LiberationSans-Regular.ttf"
FONT_SUFFIXES = (".ttf", ".otf", ".ttc")


def _bundled_dirs() -> list[Path]:
    """Return the bundled font search directories (``pcleaner/data`` and its ``fonts`` subdir)."""
    base = resources.files(pcleaner.data)
    dirs: list[Path] = []
    with resources.as_file(base) as data_dir:
        data_dir = Path(data_dir)
        dirs.append(data_dir)
        fonts_dir = data_dir / "fonts"
        if fonts_dir.is_dir():
            dirs.append(fonts_dir)
    return dirs


def _find_in_dir(directory: Path, name: str) -> Path | None:
    """Find a font file in a directory by exact filename, ``<name>.ext`` or stem prefix."""
    if not directory.is_dir():
        return None
    # Exact filename (e.g. "NotoSansJP-Regular.ttf").
    candidate = directory / name
    if candidate.is_file():
        return candidate
    # name + known suffix (e.g. "NotoSansJP" -> "NotoSansJP.ttf").
    for suffix in FONT_SUFFIXES:
        candidate = directory / f"{name}{suffix}"
        if candidate.is_file():
            return candidate
    # Stem prefix match (e.g. "LiberationSans" -> "LiberationSans-Regular.ttf").
    lowered = name.lower()
    matches = sorted(
        p
        for p in directory.iterdir()
        if p.suffix.lower() in FONT_SUFFIXES and p.stem.lower().startswith(lowered)
    )
    return matches[0] if matches else None


class FontRegistry:
    """Resolves and loads fonts for rendering, with per-language overrides and a fallback."""

    def __init__(
        self,
        default_font: str = "",
        per_language: dict[str, str] | None = None,
        user_font_dirs: list[Path] | None = None,
    ) -> None:
        self.default_font = default_font
        self.per_language = {k.lower(): v for k, v in (per_language or {}).items()}
        self.user_font_dirs = [Path(d) for d in (user_font_dirs or [])]
        self._resolve_cache: dict[str | None, Path] = {}

    def _search_dirs(self) -> list[Path]:
        return self.user_font_dirs + _bundled_dirs()

    def _locate(self, font_value: str) -> Path | None:
        """Locate a font from a config value that is either a path or a name."""
        if not font_value:
            return None
        as_path = Path(font_value)
        if as_path.is_file():
            return as_path
        for directory in self._search_dirs():
            found = _find_in_dir(directory, font_value)
            if found is not None:
                return found
        return None

    def fallback_path(self) -> Path:
        """The bundled fallback font path (always available)."""
        for directory in _bundled_dirs():
            candidate = directory / BUNDLED_FALLBACK
            if candidate.is_file():
                return candidate
        # As a last resort, let _find_in_dir try a prefix match.
        for directory in _bundled_dirs():
            found = _find_in_dir(directory, "LiberationSans")
            if found is not None:
                return found
        raise FileNotFoundError("Bundled fallback font not found.")

    def resolve(self, language: str | None = None) -> Path:
        """
        Resolve the font file to use for a language.

        :param language: The target language code (or None to use the default font).
        :return: A path to a usable font file (falling back to the bundled font).
        """
        key = language.lower() if language else None
        if key in self._resolve_cache:
            return self._resolve_cache[key]

        candidates: list[str] = []
        if key and key in self.per_language:
            candidates.append(self.per_language[key])
        if self.default_font:
            candidates.append(self.default_font)

        resolved: Path | None = None
        for value in candidates:
            resolved = self._locate(value)
            if resolved is not None:
                break
        if resolved is None:
            if candidates:
                logger.debug(
                    f"Could not locate configured font(s) {candidates} for language "
                    f"'{language}', using bundled fallback."
                )
            resolved = self.fallback_path()

        self._resolve_cache[key] = resolved
        return resolved

    def load(self, language: str | None, size: int) -> ImageFont.FreeTypeFont:
        """
        Load the resolved font for a language at the given pixel size.

        :param language: The target language code.
        :param size: The font size in pixels (clamped to at least 1).
        :return: A PIL truetype font.
        """
        path = self.resolve(language)
        return ImageFont.truetype(str(path), max(1, int(size)))
