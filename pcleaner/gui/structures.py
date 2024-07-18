from typing import Generic, TypeVar, Optional
from pathlib import Path

from attrs import frozen

import pcleaner.gui.image_file as imf
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
class ReviewOptions:
    """
    A compact structure to hold the options for the output review window.
    This is stored in the Mainwindow driver and revisited upon process completion.
    Also stores the needed information to launch the export process after confirming
    the review.
    """

    review_output: imf.Output
    review_mask_outputs: list[imf.Output]
    show_isolated_text: bool
    export_afterwards: bool
    config: cfg.Config
    output_directory: Path
    requested_outputs: list[imf.Output]
    image_files: list[imf.ImageFile]
