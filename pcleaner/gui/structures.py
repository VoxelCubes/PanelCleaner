from typing import Generic, TypeVar, Optional
from pathlib import Path
import shlex

from attrs import frozen, define, field

import pcleaner.gui.image_file as imf
import pcleaner.output_structures as ost
import pcleaner.structures as st
import pcleaner.config as cfg
from pcleaner.helpers import tr


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
    split_files: dict[Path, list[imf.ImageFile]]


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


@define
class BatchMetadata:
    """
    A structure tracking what files were processed and output in a batch,
    to be used in the post-run actions.
    """

    input_files: list[Path] = field(factory=list)
    input_dirs: list[Path] = field(factory=list)
    output_files: list[Path] = field(factory=list)
    output_dirs: list[Path] = field(factory=list)
    profile_used: str = ""

    def set_input_paths_from_files(self, files: list[imf.ImageFile]) -> None:
        self.input_files = [f.export_path for f in files]
        self.input_dirs = list(set(f.export_path.parent for f in files))

    def calculate_output_parents(self) -> None:
        self.output_dirs = list(set(f.parent for f in self.output_files))

    @staticmethod
    def _shell_safe(paths: list[Path]) -> str:
        return " ".join(shlex.quote(str(f.resolve())) for f in paths)

    def substitute_placeholders(self, command: str) -> str:
        """
        In post action commands, we offer the following placeholders:
        %i - input files
        %id - input directories
        %o - output files
        %od - output directories
        %p - profile used

        :param command: the command to substitute
        :return: the command with placeholders substituted
        """
        return (
            command.replace(tr("%id"), self._shell_safe(self.input_dirs))
            .replace(tr("%i"), self._shell_safe(self.input_files))
            .replace(tr("%od"), self._shell_safe(self.output_dirs))
            .replace(tr("%o"), self._shell_safe(self.output_files))
            .replace(tr("%p"), shlex.quote(self.profile_used))
        )
