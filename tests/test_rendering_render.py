"""Tests for rendering translated text onto a canvas."""

from PIL import Image

from pcleaner.rendering import render as rnd
from pcleaner.rendering.config import RenderConfig
from pcleaner.rendering.fonts import FontRegistry
from pcleaner.translator.structures import PageTranslation, TranslationResult


def _ink_pixels_in_box(image, box):
    """Count non-white pixels within a box region (a proxy for drawn text)."""
    x1, y1, x2, y2 = box
    region = image.convert("L").crop((x1, y1, x2, y2))
    return sum(1 for px in region.tobytes() if px < 250)


def make_page(box, text, lang="th"):
    return PageTranslation(
        image_path="/img/001.png",
        source_lang="ja",
        target_lang=lang,
        results=[TranslationResult(box=box, source_text="src", target_text=text)],
    )


def test_render_page_draws_text():
    canvas = Image.new("RGB", (200, 100), "white")
    box = (10, 10, 190, 90)
    page = make_page(box, "Hello World")
    config = RenderConfig()
    config.text_color = "#000000"
    config.stroke_width = 0
    out = rnd.render_page(canvas, page, config, FontRegistry())
    assert _ink_pixels_in_box(out, box) > 0


def test_render_page_blank_text_draws_nothing():
    canvas = Image.new("RGB", (200, 100), "white")
    box = (10, 10, 190, 90)
    page = make_page(box, "   ")
    out = rnd.render_page(canvas, page, RenderConfig(), FontRegistry())
    assert _ink_pixels_in_box(out, box) == 0


def test_render_page_respects_scale():
    canvas = Image.new("RGB", (400, 200), "white")
    # Box in half-resolution; scale 2.0 maps it into the full-res canvas.
    box = (5, 5, 95, 45)
    page = make_page(box, "Scaled")
    out = rnd.render_page(canvas, page, RenderConfig(), FontRegistry(), scale=2.0)
    scaled_box = (10, 10, 190, 90)
    assert _ink_pixels_in_box(out, scaled_box) > 0


def test_render_to_file_writes_png(tmp_path):
    src = tmp_path / "clean.png"
    Image.new("RGB", (200, 100), "white").save(src)
    page = make_page((10, 10, 190, 90), "Saved")
    out = tmp_path / "out_rendered.png"
    result = rnd.render_to_file(src, page, out, RenderConfig(), FontRegistry())
    assert result == out
    assert out.is_file()
    with Image.open(out) as img:
        assert img.size == (200, 100)


def test_render_vertical_mode():
    canvas = Image.new("RGB", (120, 200), "white")
    box = (10, 10, 110, 190)
    page = make_page(box, "縦書き", lang="ja")
    config = RenderConfig()
    config.vertical = True
    out = rnd.render_page(canvas, page, config, FontRegistry())
    assert _ink_pixels_in_box(out, box) > 0


def test_render_converts_non_rgb_canvas():
    canvas = Image.new("P", (200, 100))
    page = make_page((10, 10, 190, 90), "Hi")
    out = rnd.render_page(canvas, page, RenderConfig(), FontRegistry())
    assert out.mode in ("RGB", "RGBA")
