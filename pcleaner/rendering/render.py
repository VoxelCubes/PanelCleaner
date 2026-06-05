"""
Render translated text into cleaned bubbles.

``render_page`` draws each translated bubble from a ``PageTranslation`` onto a cleaned
canvas image, using the workspace's ``RenderConfig`` and font registry. Geometry comes
from the translation's boxes (which mirror the canonical ``#clean.json`` geometry); the
text is wrapped and auto-fitted to each box. Pure PIL — no heavy dependencies.
"""

from pathlib import Path

from loguru import logger
from PIL import Image, ImageDraw

from pcleaner.rendering import layout
from pcleaner.rendering.config import RenderConfig, Alignment
from pcleaner.rendering.fonts import FontRegistry
from pcleaner.translator.structures import PageTranslation


def _aligned_x(alignment: Alignment, box_x1: int, box_width: int, line_width: int) -> int:
    if alignment == Alignment.LEFT:
        return box_x1
    if alignment == Alignment.RIGHT:
        return box_x1 + box_width - line_width
    return box_x1 + (box_width - line_width) // 2


def _draw_horizontal(
    draw: "ImageDraw.ImageDraw",
    laid: "layout.LaidOutText",
    box: tuple[int, int, int, int],
    config: RenderConfig,
) -> None:
    x1, y1, x2, y2 = box
    box_width = x2 - x1
    box_height = y2 - y1
    start_y = y1 + max(0, (box_height - laid.height) // 2)
    y = start_y
    for line in laid.lines:
        line_width = layout.text_width(laid.font, line)
        x = _aligned_x(config.alignment, x1, box_width, line_width)
        draw.text(
            (x, y),
            line,
            font=laid.font,
            fill=config.text_color,
            stroke_width=config.stroke_width,
            stroke_fill=config.stroke_color if config.stroke_width > 0 else None,
        )
        y += laid.line_height


def _draw_vertical(
    draw: "ImageDraw.ImageDraw",
    laid: "layout.VerticalText",
    box: tuple[int, int, int, int],
    config: RenderConfig,
) -> None:
    x1, y1, x2, y2 = box
    box_width = x2 - x1
    box_height = y2 - y1
    total_width = len(laid.columns) * laid.col_width
    left = x1 + max(0, (box_width - total_width) // 2)
    num_cols = len(laid.columns)
    for i, column in enumerate(laid.columns):
        # Columns are drawn right-to-left.
        col_x = left + (num_cols - 1 - i) * laid.col_width
        col_height = len(column) * laid.char_height
        start_y = y1 + max(0, (box_height - col_height) // 2)
        for j, ch in enumerate(column):
            char_width = layout.text_width(laid.font, ch)
            cx = col_x + max(0, (laid.col_width - char_width) // 2)
            draw.text(
                (cx, start_y + j * laid.char_height),
                ch,
                font=laid.font,
                fill=config.text_color,
                stroke_width=config.stroke_width,
                stroke_fill=config.stroke_color if config.stroke_width > 0 else None,
            )


def render_page(
    canvas: "Image.Image",
    page_translation: PageTranslation,
    config: RenderConfig,
    fonts: FontRegistry,
    scale: float = 1.0,
) -> "Image.Image":
    """
    Draw all translated bubbles onto a cleaned canvas image.

    :param canvas: The cleaned page image to draw onto (modified and returned).
    :param page_translation: The translations and their box geometry.
    :param config: The render configuration.
    :param fonts: The font registry (provides per-language fonts).
    :param scale: Factor to scale box coordinates by, if the translation geometry is in a
        different resolution than the canvas (e.g. OCR ran on a downscaled image).
    :return: The canvas with text drawn (same object as the input).
    """
    if canvas.mode not in ("RGB", "RGBA"):
        canvas = canvas.convert("RGB")
    draw = ImageDraw.Draw(canvas)
    language = page_translation.target_lang

    for result in page_translation.results:
        text = result.target_text.strip()
        if not text:
            continue
        x1, y1, x2, y2 = (int(round(c * scale)) for c in result.box)
        box = (x1, y1, x2, y2)
        box_width = max(1, x2 - x1)
        box_height = max(1, y2 - y1)

        def load(size: int):
            return fonts.load(language, size)

        if config.vertical:
            laid = layout.layout_vertical(
                text,
                load,
                box_width,
                box_height,
                auto_fit=config.auto_fit,
                min_font_size=config.min_font_size,
                max_font_size=config.max_font_size,
            )
            _draw_vertical(draw, laid, box, config)
        else:
            laid = layout.layout_text(
                text,
                load,
                box_width,
                box_height,
                auto_fit=config.auto_fit,
                min_font_size=config.min_font_size,
                max_font_size=config.max_font_size,
            )
            _draw_horizontal(draw, laid, box, config)

    return canvas


def render_to_file(
    image_path: Path,
    page_translation: PageTranslation,
    out_path: Path,
    config: RenderConfig,
    fonts: FontRegistry,
    scale: float = 1.0,
) -> Path:
    """
    Render a single cleaned image with its translations and save the result.

    :param image_path: Path to the cleaned page image.
    :param page_translation: The translations to draw.
    :param out_path: Where to save the rendered image.
    :param config: The render configuration.
    :param fonts: The font registry.
    :param scale: Optional coordinate scale factor.
    :return: The output path.
    """
    image_path = Path(image_path)
    out_path = Path(out_path)
    with Image.open(image_path) as img:
        canvas = img.convert("RGB")
    canvas = render_page(canvas, page_translation, config, fonts, scale)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(out_path)
    logger.debug(f"Rendered {image_path.name} -> {out_path}")
    return out_path
