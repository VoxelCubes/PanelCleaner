from pathlib import Path
from typing import Mapping
from typing import Protocol
from typing import TypeAlias

from PIL import Image

import pcleaner.config as cfg
import pcleaner.structures as st
from pcleaner.ocr.ocr_mangaocr import MangaOcr
from pcleaner.ocr.ocr_tesseract import TesseractOcr


class OCRModel(Protocol):
    def __call__(self, img_or_path: Image.Image | Path | str, **kwargs) -> str:
        ...

OcrProcsType: TypeAlias = Mapping[st.DetectedLang, OCRModel]

def get_ocr_processor(profile: cfg.Profile) -> OcrProcsType:
    want_tess = profile.preprocessor.ocr_engine == cfg.OCREngine.TESSERACT
    tess_langs: set[str] = TesseractOcr.langs()
    if want_tess and not tess_langs:
        print(f"Tesseract OCR is not installed or not found. "
            "Please see the instructions to install Tesseract correctly. Falling back to manga-ocr.")
    ocr_processor: OcrProcsType = {
        st.DetectedLang.JA: TesseractOcr('jpn') if want_tess and 'jpn' in tess_langs else MangaOcr(),
        st.DetectedLang.ENG: TesseractOcr('eng') if 'eng' in tess_langs else MangaOcr(),
        st.DetectedLang.UNKNOWN: TesseractOcr() if tess_langs else MangaOcr(),
    }
    return ocr_processor
