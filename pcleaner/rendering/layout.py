"""
Text layout for rendering translated bubbles.

Handles word-wrapping to fit a box width, binary-search auto-fit of the font size so the
wrapped text fits the box, and a basic vertical (CJK-style) column layout. Measurement is
done with PIL fonts; a ``load_font(size)`` callable is injected so this module does not
depend on the font registry directly.
"""

from typing import Callable

from attrs import frozen
from PIL import ImageFont

FontLoader = Callable[[int], "ImageFont.FreeTypeFont"]


@frozen
class LaidOutText:
    """A horizontally laid-out, wrapped block of text fitted to a box."""

    lines: list[str]
    font: "ImageFont.FreeTypeFont"
    font_size: int
    line_height: int
    width: int
    height: int


@frozen
class VerticalText:
    """A vertically laid-out block: columns of stacked characters, drawn right-to-left."""

    columns: list[str]
    font: "ImageFont.FreeTypeFont"
    font_size: int
    char_height: int
    col_width: int
    width: int
    height: int


def text_width(font: "ImageFont.FreeTypeFont", text: str) -> int:
    """The advance width of a single line of text in pixels."""
    if not text:
        return 0
    return int(round(font.getlength(text)))


def line_height_of(font: "ImageFont.FreeTypeFont") -> int:
    """The line height (ascent + descent) of a font in pixels."""
    ascent, descent = font.getmetrics()
    return ascent + descent


def _has_spaces(text: str) -> bool:
    return any(ch.isspace() for ch in text)


def _char_wrap(token: str, font: "ImageFont.FreeTypeFont", max_width: int) -> list[str]:
    """Wrap a single long token character-by-character to fit max_width."""
    lines: list[str] = []
    current = ""
    for ch in token:
        trial = current + ch
        if current and text_width(font, trial) > max_width:
            lines.append(current)
            current = ch
        else:
            current = trial
    if current:
        lines.append(current)
    return lines


def wrap_text(text: str, font: "ImageFont.FreeTypeFont", max_width: int) -> list[str]:
    """
    Greedily wrap text to fit ``max_width``.

    For space-separated scripts this wraps on word boundaries, falling back to
    character wrapping for any single word that is too long. For scripts without
    spaces (e.g. CJK) it wraps character by character.

    :param text: The text to wrap.
    :param font: The font used to measure widths.
    :param max_width: The maximum line width in pixels (clamped to at least 1).
    :return: The wrapped lines (never empty for non-empty input).
    """
    max_width = max(1, max_width)
    text = text.strip()
    if not text:
        return [""]

    # Honor explicit newlines first, then wrap each paragraph.
    paragraphs = text.split("\n")
    lines: list[str] = []
    for paragraph in paragraphs:
        paragraph = paragraph.strip()
        if not paragraph:
            lines.append("")
            continue
        if not _has_spaces(paragraph):
            lines.extend(_char_wrap(paragraph, font, max_width))
            continue
        current = ""
        for word in paragraph.split():
            trial = f"{current} {word}".strip()
            if current and text_width(font, trial) > max_width:
                lines.append(current)
                # A single word that is itself too wide must be char-wrapped.
                if text_width(font, word) > max_width:
                    wrapped = _char_wrap(word, font, max_width)
                    lines.extend(wrapped[:-1])
                    current = wrapped[-1]
                else:
                    current = word
            else:
                current = trial
        if current:
            lines.append(current)
    return lines or [""]


def _block_size(
    lines: list[str], font: "ImageFont.FreeTypeFont", line_height: int
) -> tuple[int, int]:
    width = max((text_width(font, line) for line in lines), default=0)
    height = line_height * len(lines)
    return width, height


def layout_text(
    text: str,
    load_font: FontLoader,
    box_width: int,
    box_height: int,
    *,
    auto_fit: bool = True,
    min_font_size: int = 10,
    max_font_size: int = 48,
) -> LaidOutText:
    """
    Lay out and wrap text to fit a box, optionally auto-fitting the font size.

    With ``auto_fit`` the largest font size in ``[min_font_size, max_font_size]`` whose
    wrapped text fits both the box width and height is chosen (binary search). Without it
    the text is wrapped at ``max_font_size``. The smallest size is used as a floor so the
    text is always rendered even if it overflows a very small box.

    :return: The chosen lines, font and measured block size.
    """
    box_width = max(1, box_width)
    box_height = max(1, box_height)
    lo = max(1, min_font_size)
    hi = max(lo, max_font_size)

    def fit_at(size: int) -> tuple[list[str], "ImageFont.FreeTypeFont", int, int, int]:
        font = load_font(size)
        lh = line_height_of(font)
        lines = wrap_text(text, font, box_width)
        w, h = _block_size(lines, font, lh)
        return lines, font, lh, w, h

    if not auto_fit:
        lines, font, lh, w, h = fit_at(hi)
        return LaidOutText(lines, font, hi, lh, w, h)

    best = lo
    while lo <= hi:
        mid = (lo + hi) // 2
        _, _, _, w, h = fit_at(mid)
        if w <= box_width and h <= box_height:
            best = mid
            lo = mid + 1
        else:
            hi = mid - 1

    lines, font, lh, w, h = fit_at(best)
    return LaidOutText(lines, font, best, lh, w, h)


def layout_vertical(
    text: str,
    load_font: FontLoader,
    box_width: int,
    box_height: int,
    *,
    auto_fit: bool = True,
    min_font_size: int = 10,
    max_font_size: int = 48,
) -> VerticalText:
    """
    Lay out text vertically: characters stacked top-to-bottom in columns, columns
    arranged right-to-left. Auto-fit picks the largest size whose columns fit the box.
    """
    box_width = max(1, box_width)
    box_height = max(1, box_height)
    chars = [ch for ch in text.strip() if not ch.isspace()]
    if not chars:
        font = load_font(max(1, min_font_size))
        return VerticalText([""], font, max(1, min_font_size), line_height_of(font), 0, 0, 0)

    lo = max(1, min_font_size)
    hi = max(lo, max_font_size)

    def columns_at(size: int):
        font = load_font(size)
        char_h = line_height_of(font)
        col_width = max((text_width(font, ch) for ch in chars), default=size)
        per_col = max(1, box_height // char_h)
        columns = ["".join(chars[i : i + per_col]) for i in range(0, len(chars), per_col)]
        total_w = len(columns) * col_width
        total_h = per_col * char_h
        return columns, font, char_h, col_width, total_w, total_h

    if not auto_fit:
        columns, font, char_h, col_width, total_w, total_h = columns_at(hi)
        return VerticalText(columns, font, hi, char_h, col_width, total_w, total_h)

    best = lo
    while lo <= hi:
        mid = (lo + hi) // 2
        _, _, _, _, total_w, total_h = columns_at(mid)
        if total_w <= box_width and total_h <= box_height:
            best = mid
            lo = mid + 1
        else:
            hi = mid - 1

    columns, font, char_h, col_width, total_w, total_h = columns_at(best)
    return VerticalText(columns, font, best, char_h, col_width, total_w, total_h)
