"""
Translation cache helpers.

The translation of a page is cached as a ``#translated.json`` sidecar (see
``structures.PageTranslation``). In workspace/pipeline mode the path is produced by
``OutputPathGenerator.translated_json``; in standalone mode (translating an OCR file)
the sidecar sits next to the page, named ``<image_stem>#translated.json``.
"""

from pathlib import Path

from loguru import logger

from pcleaner.translator.structures import PageTranslation


def sidecar_path(output_dir: Path, image_path: Path) -> Path:
    """
    Build the sidecar path for a page in standalone mode.

    :param output_dir: The directory to place the sidecar in.
    :param image_path: The page image path (only its stem is used).
    :return: ``<output_dir>/<image_stem>#translated.json``.
    """
    return Path(output_dir) / f"{Path(image_path).stem}#translated.json"


def load_if_exists(path: Path) -> PageTranslation | None:
    """
    Load a cached PageTranslation if the sidecar exists and is readable.

    :param path: The sidecar path.
    :return: The cached PageTranslation, or None if missing or unreadable.
    """
    path = Path(path)
    if not path.is_file():
        return None
    try:
        return PageTranslation.load(path)
    except Exception:
        logger.exception(f"Failed to load translation cache from {path}; ignoring it.")
        return None
