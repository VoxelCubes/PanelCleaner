from typing import Generic, TypeVar, Optional
from pathlib import Path

from attrs import frozen, define

import pcleaner.gui.image_file as imf
import pcleaner.output_structures as ost
import pcleaner.structures as st
import pcleaner.config as cfg


T = TypeVar("T")


class Shared(Generic[T]):
    def __init__(self, initial_value: Optional[T] = None) -> None:
        self._container = {"data": initial_value}

    def get(self) -> Optional[T]:
        return self._container["data"]

    def set(self, value: T) -> None:
        self._container["data"] = value

    def is_none(self) -> bool:
        return self._container["data"] is None

        # class OCRModel(Protocol):
        #     def __call__(self, image: Image, **kwargs) -> str:
        # ...


@frozen
class CleaningReviewOptions:
    """
    A compact structure to hold the options for the output review window.
    This is stored in the Mainwindow driver and revisited upon process completion.
    Also stores the needed information to launch the export process after confirming
    the review.
    """

    review_output: ost.Output
    review_mask_outputs: list[ost.Output]
    show_isolated_text: bool
    export_afterwards: bool
    config: cfg.Config
    output_directory: Path
    requested_outputs: list[ost.Output]
    image_files: list[imf.ImageFile]


@define
class OcrReviewOptions:
    """
    A compact structure to hold the options for the OCR review window.
    This one needs to be mutable for the mainwindow to drop off the
    OCR results. The processors isn't run again after this so
    no configuration is needed.
    """

    image_files: list[imf.ImageFile]
    ocr_results: list[st.OCRAnalytic]
    output_path: Path
    csv_output: bool
    editing_old_data: bool
