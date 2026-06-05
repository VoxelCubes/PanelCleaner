"""Tests for text layout: wrapping, auto-fit and vertical layout."""

from PIL import ImageFont

from pcleaner.rendering import layout
from pcleaner.rendering.fonts import FontRegistry

FALLBACK = FontRegistry().fallback_path()


def load_font(size):
    return ImageFont.truetype(str(FALLBACK), size)


def test_wrap_text_wraps_on_words():
    font = load_font(20)
    lines = layout.wrap_text("the quick brown fox jumps", font, max_width=60)
    assert len(lines) > 1
    # Every wrapped line should fit the width (allowing the single-word edge case).
    for line in lines:
        if " " in line:
            assert layout.text_width(font, line) <= 60


def test_wrap_text_single_line_when_fits():
    font = load_font(20)
    lines = layout.wrap_text("hi", font, max_width=1000)
    assert lines == ["hi"]


def test_wrap_text_char_wraps_long_token():
    font = load_font(20)
    # A long token with no spaces must be split character-wise.
    lines = layout.wrap_text("aaaaaaaaaaaaaaaaaaaa", font, max_width=40)
    assert len(lines) > 1


def test_wrap_text_honors_newlines():
    font = load_font(20)
    lines = layout.wrap_text("line one\nline two", font, max_width=1000)
    assert lines == ["line one", "line two"]


def test_wrap_empty():
    font = load_font(20)
    assert layout.wrap_text("   ", font, 100) == [""]


def test_layout_text_autofit_fits_box():
    laid = layout.layout_text(
        "the quick brown fox jumps over the lazy dog",
        load_font,
        box_width=120,
        box_height=120,
        auto_fit=True,
        min_font_size=6,
        max_font_size=80,
    )
    assert laid.width <= 120
    assert laid.height <= 120
    assert 6 <= laid.font_size <= 80


def test_layout_text_autofit_smaller_box_smaller_font():
    big = layout.layout_text("hello world", load_font, 400, 400, min_font_size=6, max_font_size=80)
    small = layout.layout_text("hello world", load_font, 80, 40, min_font_size=6, max_font_size=80)
    assert small.font_size < big.font_size


def test_layout_text_no_autofit_uses_max():
    laid = layout.layout_text(
        "hi", load_font, 50, 20, auto_fit=False, min_font_size=6, max_font_size=40
    )
    assert laid.font_size == 40


def test_layout_text_floor_at_min_when_overflowing():
    # A long text in a tiny box can't fit; it should still render at the min size.
    laid = layout.layout_text(
        "averylongunbreakableword" * 3,
        load_font,
        box_width=10,
        box_height=10,
        min_font_size=8,
        max_font_size=40,
    )
    assert laid.font_size == 8
    assert laid.lines  # never empty


def test_layout_vertical_basic():
    vt = layout.layout_vertical(
        "abcdef", load_font, box_width=200, box_height=60, min_font_size=6, max_font_size=40
    )
    # Columns concatenated reproduce the input characters.
    assert "".join(vt.columns) == "abcdef"
    assert vt.width <= 200
    assert vt.height <= 60


def test_layout_vertical_empty():
    vt = layout.layout_vertical("   ", load_font, 100, 100)
    assert vt.columns == [""]
