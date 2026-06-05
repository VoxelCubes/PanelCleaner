"""Tests for the render config (pcleaner/rendering/config.py)."""

from pcleaner.rendering.config import RenderConfig, Alignment, to_alignment


def test_to_alignment_unknown_defaults_to_center():
    assert to_alignment("left") == Alignment.LEFT
    assert to_alignment("???") == Alignment.CENTER


def test_render_config_roundtrip_and_fix():
    config = RenderConfig.from_dict(
        {
            "default_font": "",  # invalid -> default
            "min_font_size": 0,  # invalid -> clamped to 1
            "max_font_size": 5,  # below min after clamp? min becomes 1, max stays 5
            "alignment": "right",
            "stroke_width": -2,  # invalid -> clamped to 0
            "vertical": True,
        }
    )
    assert config.default_font
    assert config.min_font_size == 1
    assert config.max_font_size == 5
    assert config.alignment == Alignment.RIGHT
    assert config.stroke_width == 0
    assert config.vertical is True

    data = config.to_dict()
    again = RenderConfig.from_dict(data)
    assert again.to_dict() == data


def test_max_font_size_never_below_min():
    config = RenderConfig.from_dict({"min_font_size": 30, "max_font_size": 10})
    assert config.max_font_size >= config.min_font_size


def test_defaults_on_empty_dict():
    config = RenderConfig.from_dict({})
    assert config.alignment == Alignment.CENTER
    assert config.auto_fit is True
    assert config.text_color == "#000000"


def test_text_color_roundtrip():
    config = RenderConfig.from_dict({"text_color": "#112233", "stroke_color": "#abcdef"})
    assert config.text_color == "#112233"
    assert config.stroke_color == "#abcdef"
    assert RenderConfig.from_dict(config.to_dict()).text_color == "#112233"
