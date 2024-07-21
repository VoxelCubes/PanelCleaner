from pathlib import Path
from typing import Mapping, Protocol, TypeAlias
from io import StringIO
import itertools
import csv

from PIL import Image
from natsort import natsorted
from loguru import logger

import pcleaner.config as cfg
import pcleaner.structures as st
import pcleaner.helpers as hp
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
    # noinspection PyTypeChecker
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


def format_output(
    ocr_analytics: list[st.OCRAnalytic],
    csv_output: bool,
    csv_column_names: tuple[str, str, str, str, str, str],
) -> str:
    """
    Format the output of the OCR process.

    :param ocr_analytics: A list of the OCR analytics per image.
    :param csv_output: If True, output the data in CSV format, otherwise in plain text.
    :param csv_column_names: The (localized) names of the columns in the CSV output:
        filename, startx, starty, endx, endy, text.
    :return: The formatted output.
    """
    # Format of the analytics:
    # number of boxes | sizes of all boxes | sizes of boxes that were OCRed | path to image, text, box coordinates
    # We do not need to show the first three columns, so we simplify the data structure.
    path_texts_coords: list[tuple[Path, str, st.Box]] = list(
        itertools.chain.from_iterable(a.removed_box_data for a in ocr_analytics)
    )
    if path_texts_coords:
        paths, texts, boxes = zip(*path_texts_coords)
        paths = hp.trim_prefix_from_paths(paths)
        path_texts_coords = list(zip(paths, texts, boxes))
        # Sort by path.
        path_texts_coords = natsorted(path_texts_coords, key=lambda x: x[0])

    if csv_output:
        return format_output_csv(path_texts_coords, csv_column_names)
    return format_output_plain(path_texts_coords)


def format_output_csv(
    path_texts_coords: list[tuple[Path, str, st.Box]],
    csv_column_names: tuple[str, str, str, str, str, str],
) -> str:
    buffer = StringIO()
    writer = csv.writer(buffer, quoting=csv.QUOTE_MINIMAL)
    writer.writerow(csv_column_names)

    for path, bubble, box in path_texts_coords:
        if "\n" in bubble:
            logger.warning(f"Detected newline in bubble: {path} {bubble} {box}")
            bubble = bubble.replace("\n", "\\n")
        writer.writerow([path, *box.as_tuple, bubble])

    return buffer.getvalue()


def format_output_plain(path_texts_coords: list[tuple[Path, str, st.Box]]) -> str:
    # Place the file path on it's own line, and only if it's different from the previous one.
    buffer = StringIO()
    current_path = ""
    for path, bubble, _ in path_texts_coords:
        if path != current_path:
            buffer.write(f"\n\n{path}: ")
            current_path = path
        buffer.write(f"\n{bubble}")
        if "\n" in bubble:
            logger.warning(f"Detected newline in bubble: {path} {bubble}")

    return buffer.getvalue()
