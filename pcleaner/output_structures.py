from enum import Enum, IntEnum, auto
from pathlib import Path
from typing import Protocol, Any
from uuid import uuid4

from attrs import frozen


class Output(IntEnum):
    """
    These enums represent all the output images displayed in the gui.
    These are an IntEnum so that they can be compared by order.
    This way, we can determine the last step in a set of outputs.
    """

    input = auto()
    ai_mask = auto()
    raw_boxes = auto()
    raw_json = auto()

    initial_boxes = auto()
    final_boxes = auto()
    ocr = auto()
    clean_json = auto()

    box_mask = auto()
    cut_mask = auto()
    mask_layers = auto()
    fitment_quality = auto()
    mask_overlay = auto()
    final_mask = auto()
    isolated_text = auto()
    masked_output = auto()
    mask_data_json = auto()

    denoise_mask = auto()
    denoised_output = auto()

    inpainted_mask = auto()
    inpainted_output = auto()

    write_output = auto()  # This is only used for the progress bar.


class Step(IntEnum):
    """
    These enums represent all the steps in the image processing pipeline.
    """

    text_detection = 1
    preprocessor = auto()
    masker = auto()
    denoiser = auto()
    inpainter = auto()
    output = auto()


class ProgressType(Enum):
    """
    The type of progress reported:
    - Begin: The step started, so the progress bar should be reset.
    - Incremental: One (or more) tasks were completed.
    - Absolute: The progress bar should be set to a specific value.
    - End: The step finished, so the progress bar should be set to 100%.
    """

    start = auto()
    begin_step = auto()
    incremental = auto()
    absolute = auto()
    textDetection_done = auto()
    analyticsOCR = auto()
    analyticsMasker = auto()
    analyticsDenoiser = auto()
    analyticsInpainter = auto()
    outputOCR = auto()
    end = auto()
    aborted = auto()


@frozen
class ProgressData:
    """
    A callback to report progress to the gui.

    Consists of:
    - The total number of images to process.
    - The target output to reach.
    - The current step.
    - The progress type.
    - A value for the case of absolute progress, or how much to increment by for incremental progress, or whatever analytics.
    """

    total_images: int
    target_outputs: list[Output]
    current_step: Step
    progress_type: ProgressType
    value: Any = 1  # Default value for incremental progress. Otherwise usually an analytics struct.


class ProgressSignal(Protocol):
    def emit(self, data: ProgressData) -> None:
        pass


output_to_step: dict[Output, Step] = {
    Output.input: Step.text_detection,
    Output.ai_mask: Step.text_detection,
    Output.raw_boxes: Step.text_detection,
    Output.raw_json: Step.text_detection,
    Output.initial_boxes: Step.preprocessor,
    Output.final_boxes: Step.preprocessor,
    Output.ocr: Step.preprocessor,
    Output.clean_json: Step.preprocessor,
    Output.box_mask: Step.masker,
    Output.cut_mask: Step.masker,
    Output.mask_layers: Step.masker,
    Output.fitment_quality: Step.masker,
    Output.mask_overlay: Step.masker,
    Output.final_mask: Step.masker,
    Output.isolated_text: Step.masker,
    Output.masked_output: Step.masker,
    Output.mask_data_json: Step.masker,
    Output.denoise_mask: Step.denoiser,
    Output.denoised_output: Step.denoiser,
    Output.inpainted_mask: Step.inpainter,
    Output.inpainted_output: Step.inpainter,
    Output.write_output: Step.output,
}

# The final output representing each step.
# If this output is intact, consider the step complete.
step_to_output: dict[Step, tuple[Output, ...]] = {
    Step.text_detection: (Output.input, Output.ai_mask, Output.raw_boxes, Output.raw_json),
    Step.preprocessor: (Output.initial_boxes, Output.final_boxes, Output.ocr, Output.clean_json),
    Step.masker: (
        Output.box_mask,
        Output.cut_mask,
        Output.mask_layers,
        Output.fitment_quality,
        Output.mask_overlay,
        Output.isolated_text,
        Output.masked_output,
        Output.final_mask,
        Output.mask_data_json,
    ),
    Step.denoiser: (Output.denoise_mask, Output.denoised_output),
    Step.inpainter: (Output.inpainted_mask, Output.inpainted_output),
    Step.output: (Output.write_output,),
}

# When checking which outputs are affected by a profile change, we can check
# from the last step to the first step, and stop when we find an output that is
# unaffected by the profile change.
# But these outputs are affected by changes that the ones after them are not,
# so we can't use that optimization.
# In the case of mask_overlay, it's affected by the debug mask color, but nothing else is.
OUTPUTS_WITH_INDEPENDENT_PROFILE_SENSITIVITY = (Output.mask_overlay,)


class ImageAnalyticCategory(Enum):
    """
    The category of analytics.
    """

    ocr_removed = auto()
    mask_failed = auto()
    mask_perfect = auto()
    denoised = auto()
    inpainted = auto()


class ImageAnalytics:
    """
    Bundle all the necessary info to display the minimal analytics for an image.
    These numbers are shown below their corresponding icon in the file table.
    total means the number of boxes or masks from which the failed etc. numbers are derived.
    This total can shrink as the image is processed, since if a box is thrown out by ocr, there
    won't be a corresponding mask for it etc., hence the seemingly redundant multiple totals.

    The analytics per category are stored as simple strings in the form "value/total".

    If the analytic value is blank, it should be hidden in the gui, since it's not relevant.
    These analytics are supposed to give a quick overview of how bad or good the image is, or where
    problems might be.
    """

    _data: dict[ImageAnalyticCategory, str]

    def __init__(self) -> None:
        self._data = {category: "" for category in ImageAnalyticCategory}

    def get_category(self, category: ImageAnalyticCategory) -> str:
        return self._data[category]

    def set_category(self, category: ImageAnalyticCategory, value: int, total: int | None) -> None:
        """
        Set the analytic value for the category as a string internally.
        If either value is 0, the analytic is reset.

        :param category: The category to set the value for.
        :param value: The value to set.
        :param total: The total to set.
        """
        if value == 0 or total == 0:
            self._data[category] = ""
        elif total is None:
            self._data[category] = str(value)
        else:
            self._data[category] = f"{value}/{total}"


def get_output_representing_step(step: Step) -> Output:
    """
    Get the output representing the step, which is the last one in the pipeline.
    This is the json output for the first three steps, which forms the foundation for the
    next step to continue from.

    :param step: The step to get the output for.
    :return: The output representing the step.
    """
    return step_to_output[step][-1]


class OutputPathGenerator:
    """
    Handle creating various output paths for all the different output options.
    """

    original_path: Path
    output_dir: Path
    uuid: str

    # A suffix-free str that acts as a prefix for all cached file paths.
    _output_base_path: str

    def __init__(
        self,
        original_path: Path,
        output_dir: Path,
        uuid_source: Path | str | None = None,
        export_mode: bool = False,
    ) -> None:
        """
        Provide the original image path and cache dir to generate subsequent paths.
        Optionally, provide a path that contains the uuid to use the same one, otherwise
        a new uuid for clobber protection is generated.

        :param original_path: Image path of the input image.
        :param output_dir: The cache directory that intermediate images end up in.
        :param uuid_source: [Optional] a path with the uuid or the uuid as a string.
        :param export_mode: [Optional] when True, don't attempt to add a uuid.
        """
        self.original_path = original_path.resolve()
        self.output_dir = output_dir.resolve()
        if uuid_source is None:
            uuid = uuid4()
        else:
            if isinstance(uuid_source, str):
                uuid = uuid_source
            elif isinstance(uuid_source, Path):
                # uuids are used as clobber protection, like: "{UUID}_filename_suffix.extension"
                # ex. d91d86d1-b8d2-400b-98b2-2d0337973631_0023_myimage_base.png
                uuid = uuid_source.stem.split("_")[0]
            else:
                raise TypeError("uuid_source expected to be Path, str, or None")

        if not export_mode:
            self._output_base_path = str(output_dir / f"{uuid}_{original_path.stem}")
        else:
            self._output_base_path = str(output_dir / original_path.stem)

        self.uuid = uuid

    def for_output(self, output: Output) -> Path:
        match output:
            case Output.input:
                return self.base_png
            case Output.ai_mask:
                return self.raw_mask
            case Output.raw_boxes:
                return self.raw_boxes
            case Output.raw_json:
                return self.raw_json
            case Output.initial_boxes:
                return self.boxes
            case Output.final_boxes:
                return self.final_boxes
            case Output.clean_json:
                return self.clean_json
            case Output.box_mask:
                return self.box_mask
            case Output.cut_mask:
                return self.cut_mask
            case Output.mask_layers:
                return self.mask_fitments
            case Output.final_mask:
                return self.combined_mask
            case Output.mask_overlay:
                return self.mask_overlay
            case Output.fitment_quality:
                return self.std_devs
            case Output.isolated_text:
                return self.text
            case Output.masked_output:
                return self.clean
            case Output.mask_data_json:
                return self.mask_data_json
            case Output.denoise_mask:
                return self.noise_mask
            case Output.denoised_output:
                return self.clean_denoised
            case Output.inpainted_mask:
                return self.inpainting
            case Output.inpainted_output:
                return self.clean_inpaint
            case _:
                raise ValueError(f"No path assigned for output {output}")

    def _attach(self, suffix: str) -> Path:
        return Path(self._output_base_path + suffix)

    @property
    def base_png(self) -> Path:
        return self._attach("_base.png")

    @property
    def raw_mask(self) -> Path:
        return self._attach("_raw_mask.png")

    @property
    def mask(self) -> Path:
        return self._attach("_mask.png")

    @property
    def raw_boxes(self) -> Path:
        return self._attach("_raw_boxes.png")

    @property
    def raw_json(self) -> Path:
        return self._attach("#raw.json")

    @property
    def boxes(self) -> Path:
        return self._attach("_boxes.png")

    @property
    def final_boxes(self) -> Path:
        return self._attach("_boxes_final.png")

    @property
    def clean_json(self) -> Path:
        return self._attach("#clean.json")

    @property
    def box_mask(self) -> Path:
        return self._attach("_box_mask.png")

    @property
    def with_masks(self) -> Path:
        return self._attach("_with_masks.png")

    @property
    def cut_mask(self) -> Path:
        return self._attach("_cut_mask.png")

    @property
    def mask_fitments(self) -> Path:
        return self._attach("_mask_fitments.png")

    @property
    def combined_mask(self) -> Path:
        return self._attach("_combined_mask.png")

    @property
    def mask_overlay(self) -> Path:
        return self._attach("_with_masks.png")

    @property
    def std_devs(self) -> Path:
        return self._attach("_std_devs.png")

    @property
    def clean(self) -> Path:
        return self._attach("_clean.png")

    @property
    def text(self) -> Path:
        return self._attach("_text.png")

    @property
    def mask_data_json(self) -> Path:
        return self._attach("#mask_data.json")

    @property
    def noise_mask(self) -> Path:
        return self._attach("_noise_mask.png")

    @property
    def clean_denoised(self) -> Path:
        return self._attach("_clean_denoised.png")

    @property
    def inpainting(self) -> Path:
        return self._attach("_inpainting.png")

    @property
    def clean_inpaint(self) -> Path:
        return self._attach("_clean_inpaint.png")

    @property
    def psd(self) -> Path:
        return self._attach("_out.psd")

    @property
    def psd_bulk(self) -> Path:
        return self._attach("_out_bulk.psd")
