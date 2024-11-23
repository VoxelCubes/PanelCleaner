import io
from pathlib import Path
from typing import Any
from typing import Iterable
from collections import namedtuple
from uuid import uuid4

import PySide6.QtGui as Qg
import attrs
import dictdiffer
import humanfriendly
from PIL import Image
from attrs import fields

import pcleaner.config as cfg
import pcleaner.image_export as ie
import pcleaner.output_structures as ost
from pcleaner.helpers import tr

# The max size used for the icon and large thumbnail.
THUMBNAIL_SIZE = 64


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

    path: Path  # Path to the image file. For split images, this isn't the export path.
    icon: Qg.QIcon  # Placeholder icon for the image type.
    uuid: str  # Unique identifier for the temp files to prevent name collisions.
    # The following attributes are lazy-loaded.
    thumbnail: Qg.QPixmap | None = None  # Thumbnail of the image, used as the icon.
    size: tuple[int, int] | None = None  # Size of the image.
    file_size: int | None = None  # Size of the image file in bytes.
    color_mode: str | None = None  # Color mode of the image.
    outputs: dict[ost.Output, ProcessOutput]  # Map of steps to ProcessStep objects.
    loading_queued: bool = False  # Whether the image is queued to be loaded.
    analytics_data: ost.ImageAnalytics = None
    split_from: Path | None = None  # Path to the original image that this image was split from.
    export_path: Path | None = (
        None  # Path to display in the UI and used for exporting if not merging splits.
    )

    error: Exception | None = None  # Error that occurred during any process.

    def __init__(self, path: Path, split_from: Path = None, export_path: Path = None) -> None:
        """
        Init the image file.

        :param path: Path to the image file.
        """
        self.path = path
        self.split_from = split_from
        if export_path is None:
            self.export_path = path
        else:
            self.export_path = export_path
        self.icon = Qg.QIcon.fromTheme(cfg.SUFFIX_TO_ICON[path.suffix.lower()])
        self.uuid = str(uuid4())
        self.outputs = {}
        self.analytics_data = ost.ImageAnalytics()

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
        # "Input" <-> ost.Output.input
        # When passing in None as the output name, the output will not have a name.
        # This is used for any step that only has one output, such as Input.

        # Text Detection:
        settings = [pro.general, gen.input_height_lower_target, gen.input_height_upper_target]
        self.outputs[ost.Output.input] = ProcessOutput(
            "The original image with scaling applied (if needed).", "Input", None, settings
        )
        settings += [pro.text_detector, td.model_path]
        self.outputs[ost.Output.ai_mask] = ProcessOutput(
            "The rough mask generated by the AI.", "Text Detection", "AI Mask", settings
        )
        self.outputs[ost.Output.raw_boxes] = ProcessOutput(
            "The unfiltered box data generated by the AI.", "Text Detection", "Raw Boxes", settings
        )
        self.outputs[ost.Output.raw_json] = ProcessOutput("Not visible", None, None, settings)

        # Preprocessor:
        settings += [
            pro.preprocessor,
            pp.box_min_size,
            pp.suspicious_box_min_size,
            pp.box_padding_initial,
            pp.box_right_padding_initial,
        ]

        self.outputs[ost.Output.initial_boxes] = ProcessOutput(
            "The outlines of the text boxes the AI found.",
            "Preprocessor",
            "Initial Boxes",
            settings,
        )
        settings += [
            pp.box_overlap_threshold,
            pp.ocr_enabled,
            pp.ocr_language,
            pp.ocr_engine,
            pp.reading_order,
            pp.ocr_max_size,
            pp.ocr_blacklist_pattern,
            pp.box_padding_extended,
            pp.box_right_padding_extended,
            pp.box_reference_padding,
        ]
        self.outputs[ost.Output.final_boxes] = ProcessOutput(
            "The final boxes after expanding, merging and filtering unneeded boxes with OCR.\n"
            "Green: initial boxes. Red: extended boxes. Purple: merged (final) boxes. "
            "Blue: reference boxes for denoising.",
            "Preprocessor",
            "Final Boxes",
            settings,
        )
        self.outputs[ost.Output.clean_json] = ProcessOutput("Not visible", None, None, settings)

        # Masker:
        self.outputs[ost.Output.box_mask] = ProcessOutput(
            "The mask of the merged boxes.", "Masker", "Box Mask", settings
        )
        self.outputs[ost.Output.cut_mask] = ProcessOutput(
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
        self.outputs[ost.Output.mask_layers] = ProcessOutput(
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
        self.outputs[ost.Output.fitment_quality] = ProcessOutput(
            "The standard deviation (\u03C3) and outline thickness (in pixels) of each best mask chosen, if any. "
            "Lower \u03C3 is better, from perfect (purple) to failed (red).",
            "Masker",
            "Fitment Quality",
            settings,
        )
        self.outputs[ost.Output.mask_overlay] = ProcessOutput(
            "The input image with the final mask overlaid in color.",
            "Masker",
            "Mask Overlay",
            settings + [mk.debug_mask_color],
        )
        self.outputs[ost.Output.final_mask] = ProcessOutput(
            "The collection of masks for each bubble that fit best.",
            "Masker",
            "Final Mask",
            settings,
        )
        self.outputs[ost.Output.isolated_text] = ProcessOutput(
            "The text layer isolated from the input image.", "Masker", "Isolated Text", settings
        )
        self.outputs[ost.Output.masked_output] = ProcessOutput(
            "The input image with the final mask applied.", "Masker", "Masked Output", settings
        )
        self.outputs[ost.Output.mask_data_json] = ProcessOutput("Not visible", None, None, settings)

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
        self.outputs[ost.Output.denoise_mask] = ProcessOutput(
            "The masks that required denoising, to be overlaid on the final mask when exporting.",
            "Denoiser",
            "Denoise Mask",
            denoise_settings,
        )
        self.outputs[ost.Output.denoised_output] = ProcessOutput(
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
            ip.inpainting_fade_radius,
        ]
        self.outputs[ost.Output.inpainted_mask] = ProcessOutput(
            "The inpainted sections around the text that was poorly cleaned, if at all.",
            "Inpainter",
            "Inpainted Mask",
            inpaint_settings,
        )
        self.outputs[ost.Output.inpainted_output] = ProcessOutput(
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


# We need to be able to deliver the .path attribute as a dummy output.
DummyOutput = namedtuple("DummyOutput", ["path"])


class MergedImageFile:
    """
    This class represents an image file.
    """

    # This is all we need for exporting.
    path: Path
    export_path: Path
    uuid: str
    outputs: dict[ost.Output, DummyOutput]

    def __init__(
        self, image_files: list[ImageFile], cache_dir: Path, for_ocr: bool = False
    ) -> None:
        """
        Create an amalgam from the given image files.
        Stitches the images together vertically as well.
        The image list must be sorted top to bottom.

        :param image_files: The image files to merge.
        :param cache_dir: The cache directory to store the merged image.
        :param for_ocr: When merging for ocr we need to forge some outputs data.
        """
        # Check that all images came from the same original image.
        split_from = {image.split_from for image in image_files}
        if len(split_from) != 1:
            raise ValueError("Bad splits. Images must be from the same original image.")

        self.path = split_from.pop()
        self.export_path = self.path

        # We need to merge the images together under a fresh UUID.
        # Add an identifying prefix so we can clean this up later.
        self.uuid = f"merger_{uuid4()}"

        merge_files = [
            ie.ExportTarget(image.export_path, image.export_path, image.uuid, [])
            for image in image_files
        ]
        path_gen_master = ie.merge_cached_images(
            self.path, merge_files, cache_dir, for_ocr, self.uuid
        )

        if for_ocr:
            # The OCR review driver will request the initial boxes output to grab it's path.
            self.outputs = {
                ost.Output.initial_boxes: DummyOutput(
                    path_gen_master.for_output(ost.Output.initial_boxes)
                ),
            }


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
