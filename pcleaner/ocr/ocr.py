from pathlib import Path
from typing import Mapping, Protocol, TypeAlias

from PIL import Image

import pcleaner.config as cfg
import pcleaner.structures as st
from pcleaner.ocr.ocr_mangaocr import MangaOcr
from pcleaner.ocr.ocr_tesseract import TesseractOcr


class OCRModel(Protocol):
    def __call__(self, img_or_path: Image.Image | Path | str, **kwargs) -> str: ...


OcrProcsType: TypeAlias = Mapping[st.DetectedLang, OCRModel]


def tesseract_ok(profile: cfg.Profile) -> bool:
    want_tess = profile.preprocessor.ocr_use_tesseract
    tess_langs: set[str] = TesseractOcr.langs()
    return not want_tess or (want_tess and tess_langs != set())


def ocr_engines(profile: cfg.Profile):
    return {
        cfg.OCREngine.MANGAOCR: MangaOcr(),
        cfg.OCREngine.TESSERACT: TesseractOcr() if tesseract_ok(profile) else None,
    }


def get_ocr_processor(want_tess: bool, ocr_engine: cfg.OCREngine) -> OcrProcsType:
    # want_tess = profile.preprocessor.ocr_use_tesseract
    tess_langs: set[str] = TesseractOcr.langs()
    if want_tess and not tess_langs:
        print(
            f"Tesseract OCR is not installed or not found. "
            "Please see the instructions to install Tesseract correctly. Falling back to manga-ocr."
        )
    mangaocr = MangaOcr()
    ocr_processor: OcrProcsType = {
        st.DetectedLang.JA: mangaocr,
        st.DetectedLang.ENG: mangaocr,
        st.DetectedLang.UNKNOWN: mangaocr,
    }
    if want_tess and tess_langs:
        # ocr_engine = profile.preprocessor.ocr_engine
        if ocr_engine == cfg.OCREngine.AUTO:
            ocr_processor: OcrProcsType = {
                st.DetectedLang.JA: mangaocr,
                st.DetectedLang.ENG: TesseractOcr("eng"),
                st.DetectedLang.UNKNOWN: TesseractOcr(),
            }
        elif ocr_engine == cfg.OCREngine.TESSERACT:
            if "jpn" not in tess_langs:
                print(
                    f"Tesseract language pack for 'jpn' is not installed or not found. "
                    "Please see the instructions to install Tesseract correctly. Falling back to manga-ocr."
                )
            ocr_processor: OcrProcsType = {
                st.DetectedLang.JA: TesseractOcr("jpn") if "jpn" in tess_langs else mangaocr,
                st.DetectedLang.ENG: TesseractOcr("eng"),
                st.DetectedLang.UNKNOWN: TesseractOcr(),
            }
    return ocr_processor
