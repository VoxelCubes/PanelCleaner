from pathlib import Path

from PIL import Image
from loguru import logger


class MangaOcr:
    def __init__(self, *args, **kwargs):
        from manga_ocr import MangaOcr

        logger.warning("EXPENSIVE LOADING HAPPENING HERE\n\n====================\n\n")
        self._model = MangaOcr(*args, **kwargs)

    def __call__(self, img_or_path: Image.Image | Path | str, **kwargs) -> str:
        return self._model(img_or_path)
