import io
from enum import Enum, IntEnum, auto
from pathlib import Path
from typing import Iterable
from typing import Protocol, Any
from uuid import uuid4

import PySide6.QtGui as Qg
import attrs
import dictdiffer
import humanfriendly
from PIL import Image
from attrs import frozen, fields

import pcleaner.config as cfg
from pcleaner.helpers import tr


# The max size used for the icon and large thumbnail.
THUMBNAIL_SIZE = 64


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


class ProcessOutput:
    """
    This class represents an output in the image processing pipeline.
    The sensitivity filter is used to determine which entries in the profile will affect
    this output.
    """

    description: str
    step_name: str | None
    output_name: str | None
    _path: Path | None = None
    _sensitivity_filter: attrs.filters
    _current_profile_dict: dict[str, Any] | None = None
    # This used to use a current_dict_checksum, using the json representation of the filtered profile
    # for the digest, but that proved unreliable despite the json exporter having sort keys enabled.
    # The result were phantom differences that didn't exist, so using dictdiffer and comparing the filtered
    # dicts directly was chosen instead, since it's more reliable than some other handcrafted json output.

    def __init__(
        self,
        description: str,
        step_name: str | None,
        output_name: str | None,
        profile_sensitivity: Iterable[attrs.Attribute] | None = None,
    ):
        """
        Init the process output.

        Set up the filter for the profile sensitivity.
        Pass in a list of attrs attributes like this:
            [fields(Profile).some_attribute, fields(Profile).some_other_attribute]

        If the profile sensitivity is None, the output will include all profile entries.

        :param description: A description of the output.
        :param step_name: [Optional] The name of the step that this output belongs to. If none is given, this
            output will be hidden.
        :param output_name: [Optional] The name of the output. Left blank when it's the only output for the step.
        :param profile_sensitivity: [Optional] A list of attributes that this output is sensitive to. If None, all
            attributes will be included.
        """
        self.description = description
        self.step_name = step_name
        self.output_name = output_name
        if profile_sensitivity is None:
            self._sensitivity_filter = None
        else:
            self._sensitivity_filter = attrs.filters.include(*profile_sensitivity)

    def update(self, path: Path, profile: cfg.Profile) -> None:
        """
        Update the path of the output and the checksum of the profile entries that this output is sensitive to.

        :param path: The path to the output.
        :param profile: The profile to calculate the checksum for.
        """
        self._path = path
        self.update_checksum(profile)

    @property
    def path(self) -> Path | None:
        return self._path

    def has_path(self) -> bool:
        return self.path is not None

    def reset(self) -> None:
        """
        Clear the path and checksum.
        """
        self._path = None
        self._current_profile_dict = None

    def update_checksum(self, profile: cfg.Profile) -> None:
        """
        Update the checksum of the profile entries that this output is sensitive to.

        :param profile: The profile to calculate the checksum for.
        """
        self._current_profile_dict = self._profile_check_dict(profile)

    def is_changed(self, profile: cfg.Profile) -> bool:
        """
        Check if the profile entries that this output is sensitive to have changed.

        :param profile: The profile to check.
        :return: True if the profile has changed, False otherwise.
        """
        return self._current_profile_dict is None or next(
            dictdiffer.diff(self._current_profile_dict, self._profile_check_dict(profile)), False
        )

    def is_unchanged(self, profile: cfg.Profile) -> bool:
        """
        Check if the profile entries that this output is sensitive to haven't changed.

        :param profile: The profile to check.
        :return: True if the profile hasn't changed, False otherwise.
        """
        return not self.is_changed(profile)

    def _profile_check_dict(self, profile: cfg.Profile) -> dict:
        """
        Trim down the profile to only include entries that this output is sensitive to.

        :param profile: The profile to trim.
        :return: The trimmed profile.
        """
        profile_dict = attrs.asdict(profile, filter=self._sensitivity_filter, recurse=True)
        return profile_dict


class ImageFile:
    """
    This class represents an image file.
    """

    path: Path  # Path to the image file.
    icon: Qg.QIcon  # Placeholder icon for the image type.
    uuid: str  # Unique identifier for the temp files to prevent name collisions.
    # The following attributes are lazy-loaded.
    thumbnail: Qg.QPixmap | None = None  # Thumbnail of the image, used as the icon.
    size: tuple[int, int] | None = None  # Size of the image.
    file_size: int | None = None  # Size of the image file in bytes.
    color_mode: str | None = None  # Color mode of the image.
    outputs: dict[Output, ProcessOutput]  # Map of steps to ProcessStep objects.
    loading_queued: bool = False  # Whether the image is queued to be loaded.
    analytics_data: ImageAnalytics = None

    error: Exception | None = None  # Error that occurred during any process.

    def __init__(self, path: Path) -> None:
        """
        Init the image file.

        :param path: Path to the image file.
        """
        self.path = path
        self.icon = Qg.QIcon.fromTheme(cfg.SUFFIX_TO_ICON[path.suffix.lower()])
        self.uuid = str(uuid4())
        self.outputs = {}
        self.analytics_data = ImageAnalytics()

        # Aggressively cast the profile attributes to fields.
        pro = fields(cfg.Profile)
        gen = fields(cfg.GeneralConfig)
        td = fields(cfg.TextDetectorConfig)
        pp = fields(cfg.PreprocessorConfig)
        mk = fields(cfg.MaskerConfig)
        dn = fields(cfg.DenoiserConfig)
        ip = fields(cfg.InpainterConfig)

        # Init the process steps.
        # Here I need to account for all the settings that affect each step.
        # The settings are passed as a list of attributes, note that the parent attribute
        # from the profile must be included, for child attributes to be included.

        # IMPORTANT: The output names must match the display name variant of the enum name.
        # "Input" <-> Output.input
        # When passing in None as the output name, the output will not have a name.
        # This is used for any step that only has one output, such as Input.

        # Text Detection:
        settings = [pro.general, gen.input_height_lower_target, gen.input_height_upper_target]
        self.outputs[Output.input] = ProcessOutput(
            "The original image with scaling applied (if needed).", "Input", None, settings
        )
        settings += [pro.text_detector, td.model_path]
        self.outputs[Output.ai_mask] = ProcessOutput(
            "The rough mask generated by the AI.", "Text Detection", "AI Mask", settings
        )
        self.outputs[Output.raw_boxes] = ProcessOutput(
            "The unfiltered box data generated by the AI.", "Text Detection", "Raw Boxes", settings
        )
        self.outputs[Output.raw_json] = ProcessOutput("Not visible", None, None, settings)

        # Preprocessor:
        settings += [
            pro.preprocessor,
            pp.box_min_size,
            pp.suspicious_box_min_size,
            pp.box_padding_initial,
            pp.box_right_padding_initial,
        ]

        self.outputs[Output.initial_boxes] = ProcessOutput(
            "The outlines of the text boxes the AI found.",
            "Preprocessor",
            "Initial Boxes",
            settings,
        )
        settings += [
            pp.box_overlap_threshold,
            pp.ocr_enabled,
            pp.ocr_engine,
            pp.reading_order,
            pp.ocr_max_size,
            pp.ocr_blacklist_pattern,
            pp.box_padding_extended,
            pp.box_right_padding_extended,
            pp.box_reference_padding,
        ]
        self.outputs[Output.final_boxes] = ProcessOutput(
            "The final boxes after expanding, merging and filtering unneeded boxes with OCR.\n"
            "Green: initial boxes. Red: extended boxes. Purple: merged (final) boxes. "
            "Blue: reference boxes for denoising.",
            "Preprocessor",
            "Final Boxes",
            settings,
        )
        self.outputs[Output.clean_json] = ProcessOutput("Not visible", None, None, settings)

        # Masker:
        self.outputs[Output.box_mask] = ProcessOutput(
            "The mask of the merged boxes.", "Masker", "Box Mask", settings
        )
        self.outputs[Output.cut_mask] = ProcessOutput(
            "The rough text detection mask with everything outside the box mask cut out.",
            "Masker",
            "Cut Mask",
            settings,
        )
        settings += [
            pro.masker,
            mk.mask_growth_step_pixels,
            mk.mask_growth_steps,
            mk.min_mask_thickness,
        ]
        self.outputs[Output.mask_layers] = ProcessOutput(
            "The different steps of growth around the cut mask displayed in different colors.",
            "Masker",
            "Mask Layers",
            settings,
        )
        settings += [
            mk.off_white_max_threshold,
            mk.mask_improvement_threshold,
            mk.mask_selection_fast,
            mk.mask_max_standard_deviation,
        ]
        self.outputs[Output.fitment_quality] = ProcessOutput(
            "The standard deviation (\u03C3) and outline thickness (in pixels) of each best mask chosen, if any. "
            "Lower \u03C3 is better, from perfect (purple) to failed (red).",
            "Masker",
            "Fitment Quality",
            settings,
        )
        self.outputs[Output.mask_overlay] = ProcessOutput(
            "The input image with the final mask overlaid in color.",
            "Masker",
            "Mask Overlay",
            settings + [mk.debug_mask_color],
        )
        self.outputs[Output.final_mask] = ProcessOutput(
            "The collection of masks for each bubble that fit best.",
            "Masker",
            "Final Mask",
            settings,
        )
        self.outputs[Output.isolated_text] = ProcessOutput(
            "The text layer isolated from the input image.", "Masker", "Isolated Text", settings
        )
        self.outputs[Output.masked_output] = ProcessOutput(
            "The input image with the final mask applied.", "Masker", "Masked Output", settings
        )
        self.outputs[Output.mask_data_json] = ProcessOutput("Not visible", None, None, settings)

        # Denoiser:
        denoise_settings = settings.copy()
        denoise_settings += [
            pro.denoiser,
            dn.denoising_enabled,
            dn.noise_min_standard_deviation,
            dn.noise_outline_size,
            dn.noise_fade_radius,
            dn.colored_images,
            dn.filter_strength,
            dn.color_filter_strength,
            dn.template_window_size,
            dn.search_window_size,
        ]
        self.outputs[Output.denoise_mask] = ProcessOutput(
            "The masks that required denoising, to be overlaid on the final mask when exporting.",
            "Denoiser",
            "Denoise Mask",
            denoise_settings,
        )
        self.outputs[Output.denoised_output] = ProcessOutput(
            "The input image with the denoised mask applied.",
            "Denoiser",
            "Denoised Output",
            denoise_settings,
        )

        # Inpainter:
        inpaint_settings = settings
        inpaint_settings += [
            dn.denoising_enabled,
            dn.noise_min_standard_deviation,
            pro.inpainter,
            ip.inpainting_enabled,
            ip.inpainting_min_std_dev,
            ip.inpainting_max_mask_radius,
            ip.min_inpainting_radius,
            ip.max_inpainting_radius,
            ip.inpainting_radius_multiplier,
            ip.inpainting_isolation_radius,
        ]
        self.outputs[Output.inpainted_mask] = ProcessOutput(
            "The inpainted sections around the text that was poorly cleaned, if at all.",
            "Inpainter",
            "Inpainted Mask",
            inpaint_settings,
        )
        self.outputs[Output.inpainted_output] = ProcessOutput(
            "The input image: cleaned, denoised (if enabled), and inpainted.",
            "Inpainter",
            "Inpainted Output",
            inpaint_settings,
        )

    @property
    def size_str(self) -> str:
        if self.size is None:
            return tr("Unknown")
        return f"{self.size[0]:n} × {self.size[1]:n}"

    @property
    def file_size_str(self) -> str:
        if self.file_size is None:
            return tr("Unknown")
        return humanfriendly.format_size(self.file_size, binary=True)

    @property
    def color_mode_str(self) -> str:
        if self.color_mode is None:
            return tr("Unknown")
        elif self.color_mode in ("RGB", "RGBA"):
            return tr("RGB", "Color mode")
        elif self.color_mode == "CMYK":
            return tr("CMYK", "Color mode")
        elif self.color_mode in ("L", "LA"):
            return tr("Grayscale", "Color mode")
        elif self.color_mode == "1":
            return tr("1-bit", "Color mode")
        elif self.color_mode == "P":
            return tr("Palette", "Color mode")
        else:
            return tr("Unknown")

    def data_loaded(self) -> bool:
        """
        Returns whether the lazily-loaded image data is ready.
        """
        return self.thumbnail is not None and self.size is not None

    def load_image(self) -> Path:
        """
        Loads the image data.

        :return: Path to the image file so that the callback knows which image was loaded.
        """
        image = Image.open(self.path)
        self.size = image.size
        self.file_size = self.path.stat().st_size
        self.color_mode = image.mode
        # Shrink the image down to a thumbnail size to reduce memory usage.
        thumbnail = image.copy()
        thumbnail.thumbnail((THUMBNAIL_SIZE, THUMBNAIL_SIZE))
        self.thumbnail = convert_PIL_to_QPixmap(thumbnail)

        return self.path


def convert_PIL_to_QPixmap(image: Image.Image) -> Qg.QPixmap:
    """
    Converts a PIL image to a QPixmap.

    :param image: PIL image.
    :return: QPixmap.
    """
    if image.mode == "CMYK":
        image = image.convert("RGB")
    byte_data = io.BytesIO()
    image.save(byte_data, format="PNG")
    byte_data.seek(0)
    qimage = Qg.QPixmap()
    # noinspection PyTypeChecker
    qimage.loadFromData(byte_data.read(), "PNG")
    return qimage
