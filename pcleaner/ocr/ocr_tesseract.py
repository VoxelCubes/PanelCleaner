from functools import cache
from pathlib import Path

import pytesseract
from loguru import logger
from PIL import Image

import pcleaner.ocr.supported_languages as osl


@cache
def verify_tesseract():
    try:
        pytesseract.get_tesseract_version()
        return True
    except (pytesseract.TesseractNotFoundError, SystemExit) as e:
        logger.error(f"Tesseract verification failed: {e}")
        return False


@cache
def available_langs() -> set[osl.LanguageCode]:
    try:
        # We don't cover all languages, so abuse StrEnum string equality to compare
        # against membership before casting to LanguageCode.
        return set(
            osl.LanguageCode(code)
            for code in pytesseract.get_languages(config="")
            if code in osl.LanguageCode.__members__
        )
    except pytesseract.TesseractNotFoundError as e:
        logger.error(f"Error checking Tesseract available language data: {e}")
        return set()


def load_image(img_or_path) -> Image.Image:
    if isinstance(img_or_path, (str, Path)):
        return Image.open(img_or_path)
    elif isinstance(img_or_path, Image.Image):
        return img_or_path
    else:
        raise ValueError(f"img_or_path must be a path or PIL.Image, got: {type(img_or_path)}")


def cleanup_text(text: str) -> str:
    """
    Strip newlines and multiple spaces.
    """
    return text.replace("\n", " ").replace("\r", " ").replace("\t", " ").replace("\f", " ").strip()


class TesseractOcr:
    def __init__(self, lang: str | None = None):
        self.lang = lang
        # self.config = r'--psm 4 -c preserve_interword_spaces=1'
        # self.config = r'--psm 4'
        self.config = r""

    @staticmethod
    def is_tesseract_available() -> bool:
        return verify_tesseract()

    @staticmethod
    def langs() -> set[osl.LanguageCode]:
        return available_langs()

    def __call__(
        self,
        img_or_path: Image.Image | Path | str,
        lang: str | None = None,
        config: str | None = None,
        **kwargs,
    ) -> str:
        if not self.is_tesseract_available():
            raise RuntimeError("Tesseract OCR is not installed or not found.")
        if lang and lang not in self.langs():
            raise RuntimeError(f"Tesseract OCR language pack '{lang}' not found.")
        img = load_image(img_or_path)
        try:
            raw_text = pytesseract.image_to_string(
                img, lang=lang or self.lang, config=config or self.config
            )
        except Exception:
            raw_text = ""
        if not raw_text:  # try again with sparse text
            try:
                d = pytesseract.image_to_data(
                    img,
                    lang=lang or self.lang,
                    config=r"--psm 11",
                    output_type=pytesseract.Output.DICT,
                )
                raw_text = " ".join(_ for _ in d.get("text", ()) if _)
            except Exception as e:
                logger.error(f"Failed to run Tesseract with --psm 11: {e}")
        return cleanup_text(raw_text)
