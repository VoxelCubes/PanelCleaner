"""
Render configuration.

``RenderConfig`` is owned by a workspace and serialized into the ``[render]`` table of
``workspace.toml``. It holds the settings for drawing translated text back into the
cleaned bubbles: font, auto-fit bounds, alignment, stroke and vertical-text mode.

Per-language font overrides are stored separately in the ``[fonts]`` table of the
manifest, since they map language codes to font names.
"""

import sys

from attrs import define
from loguru import logger

# If using Python 3.10 or older, use the 3rd party StrEnum.
if sys.version_info < (3, 11):
    from strenum import StrEnum
else:
    from enum import StrEnum


class Alignment(StrEnum):
    LEFT = "left"
    CENTER = "center"
    RIGHT = "right"


def to_alignment(value: str) -> Alignment:
    """Parse a string into an Alignment, defaulting to ``center``."""
    try:
        return Alignment(str(value).strip().lower())
    except ValueError:
        logger.warning(f"Unknown alignment '{value}', defaulting to 'center'.")
        return Alignment.CENTER


DEFAULT_FONT = "NotoSans"


@define
class RenderConfig:
    """Settings for the render step, stored per workspace."""

    default_font: str = DEFAULT_FONT
    auto_fit: bool = True
    min_font_size: int = 10
    max_font_size: int = 48
    alignment: Alignment = Alignment.CENTER
    text_color: str = "#000000"
    stroke_width: int = 0
    stroke_color: str = "#FFFFFF"
    vertical: bool = False

    def fix(self) -> None:
        """Clamp values into valid ranges, following the convention used by Profile configs."""
        if not str(self.default_font).strip():
            self.default_font = DEFAULT_FONT
        self.min_font_size = max(1, int(self.min_font_size))
        self.max_font_size = max(self.min_font_size, int(self.max_font_size))
        self.stroke_width = max(0, int(self.stroke_width))
        if not isinstance(self.alignment, Alignment):
            self.alignment = to_alignment(self.alignment)

    def to_dict(self) -> dict:
        """Serialize to a TOML-compatible dictionary."""
        return {
            "default_font": self.default_font,
            "auto_fit": self.auto_fit,
            "min_font_size": self.min_font_size,
            "max_font_size": self.max_font_size,
            "alignment": str(self.alignment),
            "text_color": self.text_color,
            "stroke_width": self.stroke_width,
            "stroke_color": self.stroke_color,
            "vertical": self.vertical,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "RenderConfig":
        """Build a RenderConfig from a (possibly partial) dictionary."""
        config = cls()
        if "default_font" in data:
            config.default_font = str(data["default_font"])
        if "auto_fit" in data:
            config.auto_fit = bool(data["auto_fit"])
        if "min_font_size" in data:
            config.min_font_size = int(data["min_font_size"])
        if "max_font_size" in data:
            config.max_font_size = int(data["max_font_size"])
        if "alignment" in data:
            config.alignment = to_alignment(data["alignment"])
        if "text_color" in data:
            config.text_color = str(data["text_color"])
        if "stroke_width" in data:
            config.stroke_width = int(data["stroke_width"])
        if "stroke_color" in data:
            config.stroke_color = str(data["stroke_color"])
        if "vertical" in data:
            config.vertical = bool(data["vertical"])
        config.fix()
        return config
