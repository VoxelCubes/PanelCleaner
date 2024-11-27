import re
import sys
import shutil
import base64
from collections import defaultdict
from pathlib import Path
from typing import Any, NewType

import configupdater as cu
from attrs import define, field
from loguru import logger

from pcleaner.helpers import tr
from pcleaner import cli_utils as cli
from pcleaner import helpers as hp
from pcleaner import model_downloader as md
from pcleaner.ocr import supported_languages as osl

# If using Python 3.10 or older, use the 3rd party StrEnum.
if sys.version_info < (3, 11):
    from strenum import StrEnum
else:
    from enum import StrEnum

# Logging session markers.
STARTUP_MESSAGE = "---- Starting up ----"
SHUTDOWN_MESSAGE = "---- Shutting down ----"

# Supported image suffixes.
SUPPORTED_IMG_TYPES = [
    ".jpeg",
    ".jpg",
    ".png",
    ".bmp",
    ".tiff",
    ".tif",
    ".jp2",
    ".dib",
    ".webp",
    ".ppm",
]

SUPPORTED_MASK_TYPES = [".png", ".bmp", ".tiff", ".tif", ".dib", ".webp", ".ppm"]

# image types:
# - image-bmp.svg
# - image-jpeg.svg
# - image-png.svg
# - image-tiff.svg
# - image-x-generic.svg
SUFFIX_TO_ICON = defaultdict(lambda: "image-x-generic.svg")
SUFFIX_TO_ICON.update(
    {
        ".bmp": "image-bmp",
        ".jpeg": "image-jpeg",
        ".jpg": "image-jpeg",
        ".png": "image-png",
        ".tiff": "image-tiff",
        ".tif": "image-tiff",
        ".jp2": "image-jpeg",
        ".dib": "image-x-generic",
        ".webp": "image-x-generic",
        ".ppm": "image-x-generic",
    }
)

# Create a dummy type to signify numbers need to be greater than 0.
GreaterZero = NewType("GreaterZero", int)

# Create a special type for the thread limit to add additional gui information.
# When it is < 1 then that means unlimited threads (well, up to the number of cores).
ThreadLimit = NewType("ThreadLimit", int)

# Create a new type to signify a long description string.
LongString = NewType("LongString", str)

# Create a new type for regular expressions, so they can be validated at load time.
RegexPattern = NewType("RegexPattern", str)

# Create a new type for percentages as floats. These are between 0 and 100.
Percentage = NewType("Percentage", float)

# Create a new type for pixel values.
Pixels = NewType("Pixels", int)
PixelsSquared = NewType("PixelsSquared", int)


class ReadingOrder(StrEnum):
    AUTO = "auto"
    MANGA = "manga"
    COMIC = "comic"


class OCREngine(StrEnum):
    AUTO = "auto"
    MANGAOCR = "manga-ocr"
    TESSERACT = "tesseract"


class LayeredExport(StrEnum):
    NONE = "none"
    PSD_PER_IMAGE = "psd-per-image"
    PSD_BULK = "psd-bulk"


"""
When adding new config options, follow these steps:
1. Add the new variable to the dataclass.
2. Add where it's written in the config template below, document the option for the user.
3. Add a try_to_load line in the import_from_conf method.
4. If it affects certain outputs, add sensitivity for that in the image_file.py file.
"""


@define
class GeneralConfig:
    notes: LongString = ""
    preferred_file_type: str | None = None
    preferred_mask_file_type: str = ".png"
    layered_export: LayeredExport = LayeredExport.NONE
    input_height_lower_target: Pixels = 1000
    input_height_upper_target: Pixels = 4000
    split_long_strips: bool = True
    preferred_split_height: Pixels = 2000
    split_tolerance_margin: Pixels = 500
    long_strip_aspect_ratio: float = 0.33
    merge_after_split: bool = True
    max_threads_export: ThreadLimit = 0

    def export_to_conf(self, config_updater: cu.ConfigUpdater, gui_mode: bool = False) -> None:
        """
        Write the config to the config updater object.

        No add_after_section here since it is the first section.

        :param config_updater: An existing config updater object.
        :param gui_mode: Whether the config is being exported for the GUI.
        """

        config_str = f"""\
        [General]

        # About this profile:
        notes = {escape_all(self.notes)}

        # Preferred file type to save the cleaned image as.
        # [CLI: If no file type is specified, the original file type will be used.]
        preferred_file_type = {self.preferred_file_type if self.preferred_file_type else ""}

        # Preferred file type to save the mask as.
        # Only image formats that allow for transparency are supported.
        preferred_mask_file_type = {self.preferred_mask_file_type if self.preferred_mask_file_type else ""}


        # Combine outputs into a single project file as layers.
        # Currently supported formats: Photoshop PSD.[GUI: <br>]
        # - none: Each image and mask are saved as basic files.[GUI: <br>]
        # - psd-per-image: Images and masks are saved together in a PSD file per input image.[GUI: <br>] 
        # - psd-bulk: All images and masks are saved together in a single PSD file, grouped by input image.
        layered_export = {self.layered_export}

        # The following are the lower and upper targets for the height of the input image.
        # It is only ever scaled down to fit within the range, preferring whole number factors
        # to minimize the impact on image quality. Images smaller than either target will remain unchanged.
        # You can disable this feature by setting one or both values less than or equal to 0.

        # This is useful for significantly speeding up processing on large images.
        # Also, since other options relying on pixel dimensions depend on size, this will help
        # normalize the results across different image sizes.

        # The image will be scaled down, processed, and then only the mask is scaled back up.
        # Meaning that the cleaned output will still use the original, unscaled image to prevent any loss in quality.
        # Only the height of the image is used to determine the scale factor, preserving the aspect ratio,
        # and ignoring the individual width of an image so that the factor remains consistent if one of
        # the pages is a double page spread.

        # E.g. for a lower target of 1000 and an upper target of 2000, an image with the size 5000x7000 (w, h) pixels
        # will be scaled down by a factor of 4, so that it has the size 1250x1750 pixels during processing.
        input_height_lower_target = {self.input_height_lower_target}
        input_height_upper_target = {self.input_height_upper_target}

        # Split long strips into individual pages.
        # If enabled, instead of squeezing the entire strip to fit into the preferred height,
        # the strip will be split into individual pages, each fitting the preferred height
        # plus/minus double the split tolerance margin (if the segment was in the middle of the strip).
        split_long_strips = {self.split_long_strips}
        
        # Preferred height to split long strips at.
        preferred_split_height = {self.preferred_split_height}
        
        # Tolerance margin for splitting long strips.
        # This is the maximum difference between the preferred split height and the actual height of the strip.
        # An algorithm determines the best split point within this margin, in an effort
        # to avoid splitting in the middle of a panel.
        split_tolerance_margin = {self.split_tolerance_margin}

        # Aspect ratio to use for splitting long strips.
        # This is the ratio of the width to the height of the image.
        # If the image's aspect ratio is smaller than this value, it will be considered a long strip.[GUI: <br>]
        # Example: 0.3 means that the width of the image is 0.3 times the height.
        long_strip_aspect_ratio = {self.long_strip_aspect_ratio}

        # Merge long strips back into a single image.
        # If enabled, the individual pages created from a long strip will be
        # merged back into a single image upon export.
        merge_after_split = {self.merge_after_split}

        # Maximum number of threads to use for exporting images.
        # You can leave it unspecified to use all available threads.
        # Lower this value if you run into memory issues, which will appear as random crashes.
        max_threads_export = {self.max_threads_export if self.max_threads_export > 0 else ""}

        """
        config_updater.read_string(multi_left_strip(format_for_version(config_str, gui_mode)))

    def import_from_conf(self, config_updater: cu.ConfigUpdater) -> None:
        """
        Read the config from the config updater object.

        :param config_updater: An existing config updater object.
        """
        section = "General"
        if not config_updater.has_section(section):
            logger.warning(f"No {section} section found in the profile, using defaults.")
            return

        try_to_load(self, config_updater, section, LongString, "notes")
        try_to_load(self, config_updater, section, str | None, "preferred_file_type")
        try_to_load(self, config_updater, section, str, "preferred_mask_file_type")
        try_to_load(self, config_updater, section, LayeredExport, "layered_export")
        try_to_load(self, config_updater, section, Pixels, "input_height_lower_target")
        try_to_load(self, config_updater, section, Pixels, "input_height_upper_target")
        try_to_load(self, config_updater, section, bool, "split_long_strips")
        try_to_load(self, config_updater, section, Pixels, "preferred_split_height")
        try_to_load(self, config_updater, section, Pixels, "split_tolerance_margin")
        try_to_load(self, config_updater, section, float, "long_strip_aspect_ratio")
        try_to_load(self, config_updater, section, bool, "merge_after_split")
        try_to_load(self, config_updater, section, ThreadLimit, "max_threads_export")

    def fix(self) -> None:
        """
        Fix the config values.
        """
        if (
            self.preferred_file_type is not None
            and self.preferred_file_type.lower() not in SUPPORTED_IMG_TYPES
        ):
            closest = hp.closest_match(self.preferred_file_type.lower(), SUPPORTED_IMG_TYPES)
            if closest is None:
                logger.error(
                    f"Could not recover from invalid preferred_file_type: {self.preferred_file_type}, using default."
                )
            self.preferred_file_type = closest

        if self.preferred_mask_file_type is None:
            self.preferred_mask_file_type = SUPPORTED_MASK_TYPES[0]

        if self.preferred_mask_file_type.lower() not in SUPPORTED_MASK_TYPES:
            closest = hp.closest_match(self.preferred_mask_file_type.lower(), SUPPORTED_MASK_TYPES)
            if closest is None:
                logger.error(
                    f"Could not recover from invalid preferred_mask_file_type: {self.preferred_mask_file_type}, using default."
                )
                closest = SUPPORTED_MASK_TYPES[0]
            self.preferred_mask_file_type = closest

        if self.max_threads_export < 0:
            self.max_threads_export = ThreadLimit(0)

        if self.input_height_lower_target < 0:
            self.input_height_lower_target = Pixels(0)
        if self.input_height_upper_target < 0:
            self.input_height_upper_target = Pixels(0)
        if self.input_height_upper_target < self.input_height_lower_target:
            self.input_height_upper_target = self.input_height_lower_target

        if self.preferred_split_height < 0:
            self.preferred_split_height = Pixels(0)
        if self.split_tolerance_margin < 0:
            self.split_tolerance_margin = Pixels(0)
        if self.long_strip_aspect_ratio < 0:
            self.long_strip_aspect_ratio = 0


@define
class TextDetectorConfig:
    model_path: str | None = None
    concurrent_models: int | GreaterZero = 1

    def export_to_conf(
        self, config_updater: cu.ConfigUpdater, add_after_section: str, gui_mode: bool = False
    ) -> None:
        """
        Write the config to the config updater object.

        :param config_updater: An existing config updater object.
        :param add_after_section: The section to add the config after.
        :param gui_mode: Whether the config is being exported for the GUI.
        """

        config_str = f"""\
        [TextDetector]
        
        # Path to the text detection model, leave empty to use the built-in model.
        # It is only recommended to override this if the version downloaded automatically
        # is older than the latest release.
        # The path must point directly to the comictextdetector.pt (CUDA) or
        # comictextdetector.pt.onnx (CPU) file.
        [CLI: # You can download older versions of the model here:]
        [CLI: # https://github.com/zyddnys/manga-image-translator/releases/latest]
        [GUI: # You can download older versions of the model ]
        [GUI: # <a href="https://github.com/zyddnys/manga-image-translator/releases/latest">here.</a>]
        model_path = {none_to_empty(self.model_path)}
        
        # Number of models to run in parallel. This is useful if you have enough RAM
        # (or VRAM with CUDA) to run multiple models at the same time.
        # This, of course, will increase the speed of the process, but can also
        # crash your computer if you overestimate your hardware.
        # I recommend using 1 model per 2 GB of memory available, or 1 model per 50 images.
        # Note: This is ignored if processing less than 50 files due to the overhead
        # of starting multiple models not being worth it below that.
        # Warning: This may cause program instability, use at your own risk.
        # [GUI: <br>]DO NOT report issues about this setting, as it's entirely hardware-dependent!
        concurrent_models = {self.concurrent_models}
        
        """
        detector_conf = cu.ConfigUpdater()
        detector_conf.read_string(multi_left_strip(format_for_version(config_str, gui_mode)))
        general_section = detector_conf["TextDetector"]
        config_updater[add_after_section].add_after.space(2).section(general_section.detach())

    def import_from_conf(self, config_updater: cu.ConfigUpdater) -> None:
        """
        Read the config from the config updater object.

        :param config_updater: An existing config updater object.
        """
        section = "TextDetector"
        if not config_updater.has_section(section):
            logger.warning(f"No {section} section found in the profile, using defaults.")
            return

        try_to_load(self, config_updater, section, str | None, "model_path")
        try_to_load(self, config_updater, section, int | GreaterZero, "concurrent_models")

    def fix(self) -> None:
        """
        Fix the config values.
        Numbers flagged as greater than zero are already fixed then loading.
        """
        if self.model_path is not None:
            if not Path(self.model_path).exists():
                logger.error(f"Could not find model file: {self.model_path}, using default.")
                self.model_path = None


@define
class PreprocessorConfig:
    box_min_size: PixelsSquared = 20 * 20
    suspicious_box_min_size: PixelsSquared = 200 * 200
    box_overlap_threshold: Percentage = 20.0
    ocr_enabled: bool = True
    ocr_use_tesseract: bool = False
    ocr_language: osl.LanguageCode = osl.LanguageCode.detect_box
    ocr_engine: OCREngine = OCREngine.AUTO
    reading_order: ReadingOrder = ReadingOrder.AUTO
    ocr_max_size: PixelsSquared = 30 * 100
    ocr_blacklist_pattern: RegexPattern = "[～．ー！？０-９~.!?0-9-]*"
    ocr_strict_language: bool = False
    box_padding_initial: Pixels = 2
    box_right_padding_initial: Pixels = 3
    box_padding_extended: Pixels = 5
    box_right_padding_extended: Pixels = 5
    box_reference_padding: Pixels = 20

    def export_to_conf(
        self, config_updater: cu.ConfigUpdater, add_after_section: str, gui_mode: bool = False
    ) -> None:
        """
        Write the config to the config updater object.

        :param config_updater: An existing config updater object.
        :param add_after_section: The section to add the config after.
        :param gui_mode: Whether the config is being exported for the GUI.
        """
        config_str = f"""\
        [Preprocessor]
        
        # Box sizes are given in the total number of pixels, so a box of 200x200 pixels has a size of 200 * 200 = 40000.
        # [CLI: To see these boxes visualized, use the --show-masks flag when cleaning and look inside the cache folder.]

        # Minimum size of any box to keep it.
        box_min_size = {self.box_min_size}
        
        # Minimum size of a box with "unknown" language to keep it. This language is typically assigned to logos and other
        # badly behaved text elements.
        suspicious_box_min_size = {self.suspicious_box_min_size}
        
        # The minimum overlap between two boxes to merge them.
        # This percentage (0-100) means how much of the smaller box must be inside the larger box to be merged.
        # A higher value will require a larger overlap to merge the boxes.
        box_overlap_threshold = {self.box_overlap_threshold}
        
        # Whether to use OCR to detect boxes that aren't worth cleaning, like ones that only contain numbers or symbols.
        ocr_enabled = {self.ocr_enabled}
        
        # Whether to use Tesseract to perform OCR tasks.[GUI: <br>]
        # If [CLI: set to True][GUI: checked], Tesseract OCR can be used for text extraction, if available.[GUI: <br>]
        # If [CLI: set to False][GUI: unchecked], the built-in OCR model (manga-ocr) is always used, which is
        # best suited for vertical Japanese text.
        ocr_use_tesseract = {self.ocr_use_tesseract}
        
        # The language to use for OCR tasks.
        # The text detector can detect Japanese and English, for anything else, select a language
        # explicitly here. Detecting per box retains what the text detector detected, while per page
        # will assign the most prominent language to the entire page.[GUI: <br>]
        # Note: Only Japanese is supported out of the box, everything else requires Tesseract
        #       to be enabled and its associated language packs to be installed.
        # [CLI: The value must either be a language code, e.g. "jpn", "eng" etc. or one of "detect_box", "detect_page".]
        # [CLI: Use the `languages list` command to see all available languages.]
        ocr_language = {self.ocr_language}

        # Specifies which engine to use for performing OCR.[GUI: <br>]
        # - auto: Automatically selects the OCR engine based on the detected language of each text block
        #         within the image. Uses Manga Ocr for Japanese text, Tesseract for English or Unknown Text.[GUI: <br>]
        # - mangaocr: Forces Panel Cleaner to use the built-in manga-ocr model for all text recognition
        #             tasks. Best suited for vertical Japanese text.[GUI: <br>]
        # - tesseract: Forces Panel Cleaner to use Tesseract OCR for all text recognition tasks. This is a
        #              versatile option that supports English and multiple other languages.
        ocr_engine = {self.ocr_engine}

        # Defines the reading order for processing and sorting text boxes on the entire page, not
        # individual text blocks. This global setting influences how text boxes are ordered and
        # presented for further processing.[GUI: <br>]
        # - auto: Detects the reading order based on the detected language of each text block within the page.[GUI: <br>]
        # - manga: Right-to-left, top-to-bottom order. Suitable for Japanese manga.[GUI: <br>]
        # - comic: Left-to-right, top-to-bottom order. Suitable for Western comics and texts.[GUI: <br>]
        # Choose based on the predominant layout of your content.
        reading_order = {self.reading_order}

        # Maximum size of a box to perform OCR on.
        # These useless boxes are usually small, and OCR is slow, so use this as a cutoff.
        ocr_max_size = {self.ocr_max_size}
        
        # Regex pattern to match against OCR results.
        # Anything matching this pattern is discarded.[GUI: <br>]
        # Note: the MangaOCR model returns full-width characters, so this pattern should match them.
        ocr_blacklist_pattern = {self.ocr_blacklist_pattern}
        
        # The MangaOCR model can only handle Japanese text, so when strict is enabled, it will discard boxes where
        # the Text Detector isn't confident that they are Japanese. 
        # Sometimes, numbers or other symbols will lower its confidence, resulting in the detected language being unknown.
        # If strict is disabled, those will not be discarded. Anything that is confidently recognized
        # as a different language will be discarded regardless of this setting.[GUI: <br>]
        # Note: this setting is only relevant when ocr_language is set to detect per box or page.
        ocr_strict_language = {self.ocr_strict_language}
        
        # Padding to add to each side of a box.
        # This is added to the initial boxes created by the text detector AI.
        # These boxes are visualized in green[CLI:  with the --cache-masks flag].
        box_padding_initial = {self.box_padding_initial}
        
        # Padding to add to the right side of a box.
        # This extension helps to cover rubytext that floats off to the right of vertical text.
        box_right_padding_initial = {self.box_right_padding_initial}
        
        # Padding to add to each side of a box.
        # This is added to an extended set of boxes, used to cut out false positives by the text detector AI's mask.
        # These boxes are visualized in purple[CLI:  with the --cache-masks flag].
        box_padding_extended = {self.box_padding_extended}
        
        # Padding to add to the right side of a box.
        # This extension helps to cover rubytext that floats off to the right of vertical text.
        box_right_padding_extended = {self.box_right_padding_extended}
        
        # Padding to add to each side of a box.
        # This is added to the reference boxes used to sample the original image while analyzing what mask to use.
        # These boxes are visualized in blue[CLI:  with the --cache-masks flag].
        box_reference_padding = {self.box_reference_padding}

        """
        preproc_conf = cu.ConfigUpdater()
        preproc_conf.read_string(multi_left_strip(format_for_version(config_str, gui_mode)))
        preproc_section = preproc_conf["Preprocessor"]
        config_updater[add_after_section].add_after.space(2).section(preproc_section.detach())

    def import_from_conf(self, config_updater: cu.ConfigUpdater) -> None:
        """
        Read the config from the config updater object.

        :param config_updater: An existing config updater object.
        """
        section = "Preprocessor"
        if not config_updater.has_section(section):
            logger.warning(f"No {section} section found in the profile, using defaults.")
            return

        try_to_load(self, config_updater, section, PixelsSquared, "box_min_size")
        try_to_load(self, config_updater, section, PixelsSquared, "suspicious_box_min_size")
        try_to_load(self, config_updater, section, Percentage, "box_overlap_threshold")
        try_to_load(self, config_updater, section, bool, "ocr_enabled")
        try_to_load(self, config_updater, section, bool, "ocr_use_tesseract")
        try_to_load(self, config_updater, section, osl.LanguageCode, "ocr_language")
        try_to_load(self, config_updater, section, OCREngine, "ocr_engine")
        try_to_load(self, config_updater, section, ReadingOrder, "reading_order")
        try_to_load(self, config_updater, section, PixelsSquared, "ocr_max_size")
        try_to_load(self, config_updater, section, RegexPattern, "ocr_blacklist_pattern")
        try_to_load(self, config_updater, section, bool, "ocr_strict_language")
        try_to_load(self, config_updater, section, Pixels, "box_padding_initial")
        try_to_load(self, config_updater, section, Pixels, "box_right_padding_initial")
        try_to_load(self, config_updater, section, Pixels, "box_padding_extended")
        try_to_load(self, config_updater, section, Pixels, "box_right_padding_extended")
        try_to_load(self, config_updater, section, Pixels, "box_reference_padding")

    def fix(self) -> None:
        """
        Ensure all numbers are greater equal 0.
        """
        if self.box_min_size < 0:
            self.box_min_size = PixelsSquared(0)
        if self.suspicious_box_min_size < 0:
            self.suspicious_box_min_size = PixelsSquared(0)
        if self.box_overlap_threshold < 0:
            self.box_overlap_threshold = Percentage(0.0)
        if self.box_overlap_threshold > 100:
            self.box_overlap_threshold = Percentage(100.0)
        if self.ocr_max_size < 0:
            self.ocr_max_size = PixelsSquared(0)
        if self.box_padding_initial < 0:
            self.box_padding_initial = Pixels(0)
        if self.box_right_padding_initial < 0:
            self.box_right_padding_initial = Pixels(0)
        if self.box_padding_extended < 0:
            self.box_padding_extended = Pixels(0)
        if self.box_right_padding_extended < 0:
            self.box_right_padding_extended = Pixels(0)
        if self.box_reference_padding < 0:
            self.box_reference_padding = Pixels(0)


@define
class MaskerConfig:
    max_threads: ThreadLimit = 0
    mask_growth_step_pixels: Pixels | GreaterZero = 2
    mask_growth_steps: int | GreaterZero = 11
    min_mask_thickness: Pixels = 4
    allow_colored_masks: bool = True
    off_white_max_threshold: int = 240
    mask_max_standard_deviation: float = 15
    mask_improvement_threshold: float = 0.1
    mask_selection_fast: bool = False
    debug_mask_color: tuple[int, int, int, int] = (108, 30, 240, 127)

    def export_to_conf(
        self, config_updater: cu.ConfigUpdater, add_after_section: str, gui_mode: bool = False
    ) -> None:
        """
        Write the config to the config updater object.

        :param config_updater: An existing config updater object.
        :param add_after_section: The section to add the new section after.
        :param gui_mode: Whether to format the config for the GUI.
        """
        config_str = f"""\
        [Masker]
        
        # Maximum number of threads to use for mask generation.
        # You can leave it unspecified to use all available threads.
        # Lower this value if you run into memory issues, which will appear as random crashes.
        max_threads = {self.max_threads if self.max_threads > 0 else ""}
        
        # Number of pixels to grow the mask by each step.
        # This bulks up the outline of the mask, so smaller values will be more accurate but slower.
        mask_growth_step_pixels = {self.mask_growth_step_pixels}
        
        # Number of steps to grow the mask by.
        # A higher number will make more and larger masks, ultimately limited by the reference box size.
        mask_growth_steps = {self.mask_growth_steps}
        
        # Minimum thickness of a mask.
        # [CLI: This is like the first mask's growth step, the remaining will follow mask_growth_step_pixels.]
        # [GUI: This is like the first mask's growth step, the remaining will follow Mask Growth Step Pixels.]
        # This way, you can have a small step size for accuracy, but still prevent very thin masks
        # that might be used to clean text only surrounded by an outline, when inpainting would've been the
        # better choice.
        min_mask_thickness = {self.min_mask_thickness}
        
        # Whether to allow colored masks.
        # When true, the masker will allow masks to use any color, not just white, black, or gray.
        allow_colored_masks = {self.allow_colored_masks}
        
        # Maximum threshold for a pixel to be considered off-white.
        # The median color along the edge of a mask may not be pure white,
        # so to prevent slight off-white tones on a pure-white background,
        # anything lighter than this threshold value will be rounded up to pure white.
        # Value range: black (0) to pure white (255).
        off_white_max_threshold = {self.off_white_max_threshold}
        
        # The standard deviation of a mask represents the variation in color along the edge of the mask.
        # For this, only the single line of pixels along the outer edge of a mask is sampled from
        # the original image.
        # A low deviation means that the mask sits in a solid color,
        # which means it doesn't intersect any text or other objects.
        
        # The maximum standard deviation of a mask to consider.
        # A high value here means a higher tolerance for the mask intersecting text or other objects,
        # which isn't a good mask, as it will require inpainting anyway.
        # Setting this to 0 will only allow perfect masks, which is recommended for very high resolution images.
        mask_max_standard_deviation = {self.mask_max_standard_deviation}
        
        # Minimum improvement in standard deviation of the mask to continue growing it.
        # Setting a higher value here requires a higher improvement to consider a larger mask,
        # to give a preference to smaller masks.
        mask_improvement_threshold = {self.mask_improvement_threshold}
        
        # Whether to use the fast mask selection algorithm.
        # When true, the mask selection algorithm will pick the first perfect mask, if one is found early.
        # This is faster, but may not find the best mask, if a slightly bigger one would have been better.
        mask_selection_fast = {self.mask_selection_fast}
        
        # Color to use for the debug mask. [CLI: This is a tuple of RGBA values.]
        debug_mask_color = {','.join(map(str, self.debug_mask_color))}
        
        """
        masker_conf = cu.ConfigUpdater()
        masker_conf.read_string(multi_left_strip(format_for_version(config_str, gui_mode)))
        masker_section = masker_conf["Masker"]
        config_updater[add_after_section].add_after.space(2).section(masker_section.detach())

    def import_from_conf(self, config_updater: cu.ConfigUpdater) -> None:
        """
        Read the config from the config updater object.

        :param config_updater: An existing config updater object.
        """
        section = "Masker"
        if not config_updater.has_section(section):
            logger.warning(f"No {section} section found in the profile, using defaults.")
            return

        try_to_load(self, config_updater, section, ThreadLimit, "max_threads")
        try_to_load(self, config_updater, section, Pixels | GreaterZero, "mask_growth_step_pixels")
        try_to_load(self, config_updater, section, int | GreaterZero, "mask_growth_steps")
        try_to_load(self, config_updater, section, Pixels, "min_mask_thickness")
        try_to_load(self, config_updater, section, bool, "allow_colored_masks")
        try_to_load(self, config_updater, section, int, "off_white_max_threshold")
        try_to_load(self, config_updater, section, float, "mask_improvement_threshold")
        try_to_load(self, config_updater, section, bool, "mask_selection_fast")
        try_to_load(self, config_updater, section, float, "mask_max_standard_deviation")
        try:
            color_tuple: tuple[int, ...] = tuple(
                int(x) for x in config_updater["Masker"]["debug_mask_color"].value.split(",")
            )
            if len(color_tuple) != 4:
                raise ValueError(
                    f"Invalid color tuple length. Expected 4: 'Red, Green, Blue, Alpha' got {len(color_tuple)}"
                )
            color_tuple: tuple[int, int, int, int]
            self.debug_mask_color = color_tuple
        except (cu.NoOptionError, ValueError):
            pass

    def fix(self) -> None:
        """
        Keep the numbers greater or equal to zero.
        For numbers, ensure the range 0-255.
        """
        if self.max_threads < 0:
            self.max_threads = ThreadLimit(0)
        self.mask_growth_steps = max(0, self.mask_growth_steps)
        self.off_white_max_threshold = max(0, min(255, self.off_white_max_threshold))
        if self.mask_improvement_threshold < 0:
            self.mask_improvement_threshold = 0
        if self.mask_max_standard_deviation < 0:
            self.mask_max_standard_deviation = 0
        # We already ensured that it's a tuple of 4 ints.
        # noinspection PyTypeChecker
        self.debug_mask_color = tuple(max(0, min(255, x)) for x in self.debug_mask_color)


@define
class DenoiserConfig:
    denoising_enabled: bool = True
    max_threads: ThreadLimit = 0
    noise_min_standard_deviation: float = 0.25
    noise_outline_size: Pixels = 5
    noise_fade_radius: Pixels = 1
    colored_images: bool = False
    filter_strength: int = 10
    color_filter_strength: int = 10
    template_window_size: Pixels = 7
    search_window_size: Pixels = 21

    def export_to_conf(
        self, config_updater: cu.ConfigUpdater, add_after_section: str, gui_mode: bool = False
    ) -> None:
        """
        Write the config to the config updater object.

        :param config_updater: An existing config updater object.
        :param add_after_section: The section to add the new section after.
        :param gui_mode: Whether to format the config for the GUI.
        """
        config_str = f"""\
        [Denoiser]
        
        # When a bit of text is hard to mask off, the cleaning step likely had to choose a
        # small mask, which leaves a lot of jpeg-artifacts behind, if they were around the text.
        
        # This means that the color of pixels around the edge of a mask isn't uniform,
        # which is quantified as a standard deviation. The denoiser can target masks with
        # a minimum standard deviation and denoise the area right around the mask.
        # This preserves details in the rest of the image, but removes artifacts right around where
        # the text used to be.
        
        # Since this is an optional step and may even be superfluous for high-resolution images that 
        # don't suffer from jpeg-artifacts, it can be disabled here.
        # Set to False to disable denoising.
        denoising_enabled = {self.denoising_enabled}
        
        # Maximum number of threads to use for denoising.
        # You can leave it unspecified to use all available threads.
        # Lower this value if you run into memory issues, which will appear as random crashes.
        max_threads = {self.max_threads if self.max_threads > 0 else ""}
        
        # The minimum standard deviation of colors around the edge of a given mask
        # to perform denoising on the region around the mask.
        noise_min_standard_deviation = {self.noise_min_standard_deviation}
        
        # Note: If inpainting is enabled, the inpainting min std deviation will act as a maximum for this,
        # after which this mask is handed off to the inpainter.
        
        # The thickness of an outline to denoise around a mask.
        noise_outline_size = {self.noise_outline_size}
        
        # Fade the edges of the denoised cover mask by this amount to smoothly blend
        # the denoised parts into the rest of the image.
        noise_fade_radius = {self.noise_fade_radius}
        
        # Set to True to support colored images.
        colored_images = {self.colored_images}
        
        # How strongly to denoise the image. Higher values mean more denoising.
        filter_strength = {self.filter_strength}
        
        # How strongly to denoise the color channels, as opposed to lightness.
        # Higher values mean more denoising.
        color_filter_strength = {self.color_filter_strength}
        
        # Size in pixels of the template patch that is used to compute weights. Should be odd.
        template_window_size = {self.template_window_size}
        
        # Size in pixels of the window that is used to compute weighted average for given pixel. Should be odd.
        search_window_size = {self.search_window_size}
        
        """
        denoiser_conf = cu.ConfigUpdater()
        denoiser_conf.read_string(multi_left_strip(format_for_version(config_str, gui_mode)))
        denoiser_section = denoiser_conf["Denoiser"]
        config_updater[add_after_section].add_after.space(2).section(denoiser_section.detach())

    def import_from_conf(self, config_updater: cu.ConfigUpdater) -> None:
        """
        Read the config from the config updater object.

        :param config_updater: An existing config updater object.
        """
        section = "Denoiser"
        if not config_updater.has_section(section):
            logger.warning(f"No {section} section found in the profile, using defaults.")
            return

        try_to_load(self, config_updater, section, ThreadLimit, "max_threads")
        try_to_load(self, config_updater, section, bool, "denoising_enabled")
        try_to_load(self, config_updater, section, float, "noise_min_standard_deviation")
        try_to_load(self, config_updater, section, Pixels, "noise_outline_size")
        try_to_load(self, config_updater, section, Pixels, "noise_fade_radius")
        try_to_load(self, config_updater, section, bool, "colored_images")
        try_to_load(self, config_updater, section, int, "filter_strength")
        try_to_load(self, config_updater, section, int, "color_filter_strength")
        try_to_load(self, config_updater, section, Pixels, "template_window_size")
        try_to_load(self, config_updater, section, Pixels, "search_window_size")

    def fix(self) -> None:
        if self.max_threads < 0:
            self.max_threads = ThreadLimit(0)
        if self.noise_min_standard_deviation < 0:
            self.noise_min_standard_deviation = 0
        if self.noise_outline_size < 0:
            self.noise_outline_size = Pixels(0)
        if self.noise_fade_radius < 0:
            self.noise_fade_radius = Pixels(0)
        if self.filter_strength < 0:
            self.filter_strength = 0
        if self.color_filter_strength < 0:
            self.color_filter_strength = 0
        if self.template_window_size < 0:
            self.template_window_size = Pixels(0)
        if self.search_window_size < 0:
            self.search_window_size = Pixels(0)


@define
class InpainterConfig:
    inpainting_enabled: bool = False
    inpainting_min_std_dev: float = 15
    inpainting_max_mask_radius: Pixels = 6
    min_inpainting_radius: Pixels = 7
    max_inpainting_radius: Pixels = 20
    inpainting_radius_multiplier: float = 0.2
    inpainting_isolation_radius: Pixels = 5
    inpainting_fade_radius: Pixels = 4

    def export_to_conf(
        self, config_updater: cu.ConfigUpdater, add_after_section: str, gui_mode: bool = False
    ) -> None:
        """
        Write the config to the config updater object.

        :param config_updater: An existing config updater object.
        :param add_after_section: The section to add the new section after.
        :param gui_mode: Whether to format the config for the GUI.
        """
        config_str = f"""\
        [Inpainter]
        
        # EXPERIMENTAL FEATURE: If you find better default settings, please open an issue on github
        # to share the improvements with everyone. Note that inpainting isn't enabled by default.

        # Inpainting is when machine learning is used to replace the content of an image based on its surroundings.
        # For masks that couldn't be cleaned well (or at all), inpainting can be used.
        # To differentiate this from denoising, inpainting is meant for significantly worse masks that had
        # a tight fit. Any masks that were denoised won't be inpainted.

        # Since this step can provide poor results in some cases, it can be disabled here.
        # [CLI: Set to False to disable inpainting.]
        # [GUI: Uncheck to disable inpainting.]
        inpainting_enabled = {self.inpainting_enabled}

        # The minimum standard deviation of colors around the edge of a given mask
        # to perform inpainting on the region around the mask.
        # If this value matches the maximum deviation for masks, only failed bubbles will be inpainted,
        # making the following two settings irrelevant.
        inpainting_min_std_dev = {self.inpainting_min_std_dev}

        # The maximum radius of a mask to perform inpainting on.
        # Masks larger than this will be left as they are, because if the margin is that big,
        # it is likely that the mask is already good enough.
        inpainting_max_mask_radius = {self.inpainting_max_mask_radius}
        
        # The minimum radius around a mask to inpaint.
        # This is added to the optimal mask size to ensure that the inpainting covers the entire mask.
        min_inpainting_radius = {self.min_inpainting_radius}
        
        # For masks that proved far harder to clean, meaning they had a high standard deviation,
        # increase the radius of the inpainting to cover more of the mask.
        # This is additional margin is added to the min inpainting radius and is calculated as:
        # inpainting radius multiplier times mask standard deviation
        inpainting_radius_multiplier = {self.inpainting_radius_multiplier}
        
        # The maximum radius around a mask to inpaint.
        # This limits the size the inpainting can grow to, to prevent it from covering too much of the image,
        # if a large radius multiplier is used.
        max_inpainting_radius = {self.max_inpainting_radius}
        
        # After inpainting, cut the result out of the original image to prevent the inpainting
        # from affecting the rest of the image.
        # This ensures that the original image is preserved as much as possible.
        # This radius is added around the final inpainting radius, due to the inpainting model modifying a few pixels
        # outside of its dedicated region.
        inpainting_isolation_radius = {self.inpainting_isolation_radius}
        
        # Fade the edges of the inpainted cover mask by this many pixels to smoothly blend
        # the inpainted parts into the rest of the image.[GUI: <br>]
        # If you see faint outlines after inpainting, increase the min inpainting value and
        # set this one to half that amount.
        inpainting_fade_radius = {self.inpainting_fade_radius}

        """
        inpainter_conf = cu.ConfigUpdater()
        inpainter_conf.read_string(multi_left_strip(format_for_version(config_str, gui_mode)))
        inpainter_section = inpainter_conf["Inpainter"]
        config_updater[add_after_section].add_after.space(2).section(inpainter_section.detach())

    def import_from_conf(self, config_updater: cu.ConfigUpdater) -> None:
        """
        Read the config from the config updater object.

        :param config_updater: An existing config updater object.
        """
        section = "Inpainter"
        if not config_updater.has_section(section):
            logger.warning(f"No {section} section found in the profile, using defaults.")
            return

        try_to_load(self, config_updater, section, bool, "inpainting_enabled")
        try_to_load(self, config_updater, section, float, "inpainting_min_std_dev")
        try_to_load(self, config_updater, section, Pixels, "inpainting_max_mask_radius")
        try_to_load(self, config_updater, section, Pixels, "min_inpainting_radius")
        try_to_load(self, config_updater, section, Pixels, "max_inpainting_radius")
        try_to_load(self, config_updater, section, float, "inpainting_radius_multiplier")
        try_to_load(self, config_updater, section, Pixels, "inpainting_isolation_radius")
        try_to_load(self, config_updater, section, Pixels, "inpainting_fade_radius")

    def fix(self) -> None:
        if self.inpainting_min_std_dev < 0:
            self.inpainting_min_std_dev = 0
        if self.inpainting_max_mask_radius < 0:
            self.inpainting_max_mask_radius = Pixels(0)
        if self.min_inpainting_radius < 0:
            self.min_inpainting_radius = Pixels(0)
        if self.max_inpainting_radius < 0:
            self.max_inpainting_radius = Pixels(0)
        if self.inpainting_radius_multiplier < 0:
            self.inpainting_radius_multiplier = 0
        if self.inpainting_isolation_radius < 0:
            self.inpainting_isolation_radius = Pixels(0)
        if self.inpainting_fade_radius < 0:
            self.inpainting_fade_radius = Pixels(0)
        self.max_inpainting_radius = max(self.min_inpainting_radius, self.max_inpainting_radius)


@define
class Profile:
    """
    A profile is a collection of settings that can be saved and loaded from disk.
    """

    general: GeneralConfig = field(factory=GeneralConfig)
    text_detector: TextDetectorConfig = field(factory=TextDetectorConfig)
    preprocessor: PreprocessorConfig = field(factory=PreprocessorConfig)
    masker: MaskerConfig = field(factory=MaskerConfig)
    denoiser: DenoiserConfig = field(factory=DenoiserConfig)
    inpainter: InpainterConfig = field(factory=InpainterConfig)

    def bundle_config(self, gui_mode: bool = False) -> cu.ConfigUpdater:
        """
        Bundle the config into a ConfigUpdater object.

        :param gui_mode: When true, strips out the CLI-specific options and keeps the GUI-specific ones,
            and vice versa.
        """
        config_updater = cu.ConfigUpdater()
        self.general.export_to_conf(config_updater, gui_mode=gui_mode)
        self.text_detector.export_to_conf(config_updater, "General", gui_mode=gui_mode)
        self.preprocessor.export_to_conf(config_updater, "TextDetector", gui_mode=gui_mode)
        self.masker.export_to_conf(config_updater, "Preprocessor", gui_mode=gui_mode)
        self.denoiser.export_to_conf(config_updater, "Masker", gui_mode=gui_mode)
        self.inpainter.export_to_conf(config_updater, "Denoiser", gui_mode=gui_mode)
        return config_updater

    def hash_current_values(self) -> int:
        """
        Hash the current values of the profile.
        This isn't implementing __hash__ because these objects are mutable.
        This is merely useful to tell when the profile has changed.

        :return: A hash of the current values of the profile.
        """
        return hash(str(self.bundle_config()))

    def safe_write(self, path: Path) -> bool:
        """
        Write to a temporary file and then move it to the destination.
        If the write fails, the temporary file is deleted.

        :param path: The path to write the profile to.
        :return: True if the profile was written successfully, False otherwise.
        """
        temp_path = path.with_suffix(".tmp")
        success = self.unsafe_write(temp_path)
        if success:
            try:
                shutil.move(temp_path, path)
            except Exception:
                logger.exception(f"Failed to rename {temp_path} to {path}")
                success = False
        if not success:
            try:
                if temp_path.exists():
                    temp_path.unlink()
            except Exception:
                logger.exception(f"Failed to delete {temp_path}")
        return success

    def unsafe_write(self, path: Path) -> bool:
        """
        Write the profile to a file.

        :param path: The path to write the profile to.
        :return: True if the profile was written successfully, False otherwise.
        """
        logger.debug("Writing profile to disk...")
        try:
            with open(path, "w", encoding="utf-8") as file:
                self.bundle_config().write(file)
            return True
        except Exception:
            logger.exception(f"Failed to write profile to {path}")
            return False

    @classmethod
    def load(cls, path: Path) -> "Profile":
        """
        Load a profile from a config file.
        """
        logger.info(f"Loading profile {path} from disk...")
        config = cu.ConfigUpdater()
        try:
            config.read(path, encoding="utf-8")
            profile = cls()
            profile.general.import_from_conf(config)
            profile.text_detector.import_from_conf(config)
            profile.preprocessor.import_from_conf(config)
            profile.masker.import_from_conf(config)
            profile.denoiser.import_from_conf(config)
            profile.inpainter.import_from_conf(config)
            profile.fix()
        except Exception:
            logger.exception(f"Failed to load profile from {path}")
            profile = cls()
            print("Failed to load profile, using default profile.")
        return profile

    def get(self, section: str, option: str) -> Any:
        """
        Get the value of a config option.
        """
        return getattr(getattr(self, section), option)

    def set(self, section: str, option: str, value: Any) -> None:
        """
        Set the value of a config option.
        """
        # Check that the attribute exists.
        if not hasattr(self, section):
            raise AttributeError(f"No such section: {section}")
        if not hasattr(getattr(self, section), option):
            raise AttributeError(f"No such option: {option}")
        setattr(getattr(self, section), option, value)

    def fix(self) -> None:
        """
        Correct any invalid values in the profile.
        """
        self.general.fix()
        self.text_detector.fix()
        self.preprocessor.fix()
        self.masker.fix()
        self.denoiser.fix()
        self.inpainter.fix()


@define
class Config:
    """
    The main configuration class.
    These setting are saved to disk.

    saved_profiles: Saved profiles contains a mapping from profile name to profile path, where it is saved.
    profile_editor: The program to use to edit the profile files. When blank, the default editor is used.
    """

    locale: str | None = None
    current_profile: Profile = field(factory=Profile)
    default_profile: str | None = None
    saved_profiles: dict[str, Path] = field(factory=dict)
    profile_editor: str | None = None
    cache_dir: Path | None = None
    default_torch_model_path: Path | None = None  # CUDA
    default_cv2_model_path: Path | None = None  # CPU
    gui_theme: str | None = None
    show_oom_warnings: bool = True
    pa_remember_action: bool = False
    pa_wait_time: int = 5
    pa_shutdown_command: str | None = None
    pa_cancel_on_error: bool = True
    pa_last_action: str | None = None
    pa_custom_commands: dict[str, str] = field(factory=dict)

    @staticmethod
    def reserved_profile_names() -> list[str]:
        """
        These names may not be used for profiles.
        """
        return [tr("default", "reserved profile name"), "builtin", "none"]

    @staticmethod
    def default_profile_name() -> str:
        """
        The name of the default profile.
        """
        return Config.reserved_profile_names()[0].capitalize()

    def show(self) -> None:
        """
        Print the current configuration to the console.
        """
        print("Current Configuration:\n")
        print("Locale:", self.locale if self.locale is not None else "System default")
        print(
            f"Default Profile: {self.default_profile if self.default_profile is not None else 'Built-in'}"
        )
        print("Saved Profiles:")
        if self.saved_profiles:
            for name, path in self.saved_profiles.items():
                print(f"- {name}: {path}")
        else:
            print("(No saved profiles)")
        print("")

        print(
            "Profile Editor:",
            self.profile_editor if self.profile_editor is not None else "System default",
        )
        print(
            "Cache Directory:", self.cache_dir if self.cache_dir is not None else "System default"
        )
        print(
            "Default Torch Model Path:",
            (
                self.default_torch_model_path
                if self.default_torch_model_path is not None
                else "Not downloaded"
            ),
        )
        print(
            "Default CV2 Model Path:",
            (
                self.default_cv2_model_path
                if self.default_cv2_model_path is not None
                else "Not downloaded"
            ),
        )
        print(
            "GUI Theme:",
            self.gui_theme if self.gui_theme is not None else "System default",
        )
        print("Show OOM Warnings:", self.show_oom_warnings)
        print("PA Remember Action:", self.pa_remember_action)
        print("PA Wait Time:", self.pa_wait_time)
        print("PA Shutdown Command:", self.pa_shutdown_command)
        print("PA Cancel on Error:", self.pa_cancel_on_error)
        print("PA Last Action:", self.pa_last_action)
        print("PA Custom Commands:")
        for name, command in self.pa_custom_commands.items():
            print(f"- {name}: {command}")

        print("\n" + "-" * 20 + "\n")
        print(f"Config file located at: {cli.get_config_path()}")
        print(f"System default cache directory: {cli.get_cache_path()}")

    def get_cache_dir(self) -> Path:
        """
        Get the cache directory.
        Get the system default cache directory if the user has not set a custom cache directory.
        """
        if self.cache_dir is None:
            return cli.get_cache_path()
        return self.cache_dir

    def get_model_cache_dir(self) -> Path:
        """
        Get the cache directory for models.
        """
        path = self.get_cache_dir() / "model"
        path.mkdir(parents=True, exist_ok=True)
        return path

    def get_cleaner_cache_dir(self) -> Path:
        """
        Get the cache directory for cleaner models.
        """
        path = self.get_cache_dir() / "cleaner"
        path.mkdir(parents=True, exist_ok=True)
        return path

    def add_profile(self, name: str, path: Path) -> None:
        """
        Add a profile to the saved profiles.
        """
        self.saved_profiles[name] = path

    def remove_profile(self, name: str) -> None:
        """
        Remove a profile from the saved profiles.
        """
        if self.default_profile == name:
            self.default_profile = None
        self.saved_profiles.pop(name, None)

    def save(self, config_path: Path | None = None) -> bool:
        """
        Write the configuration to disk.

        :param config_path: The path to write the config to. If None, the default config path is used.
        :return: True if the configuration was written successfully.
        """
        if config_path is None:
            config_path = cli.get_config_path()

        config = cu.ConfigUpdater()
        # Save the dict of saved profiles and the profile editor.
        saved_profiles_str = "\n".join(
            f"{name}={str(path.resolve())}" for name, path in self.saved_profiles.items()
        )
        custom_commands_str = "\n".join(
            f"{to_base32_modified(name)} = {to_base32_modified(command)}"
            for name, command in self.pa_custom_commands.items()
        )

        conf_str = f"""\
        [General]
        
        # Interface language. Leave blank to use the system default.
        locale = {none_to_empty(self.locale)}
        
        # The default profile to use. Leave blank to use the built-in default profile.
        default_profile = {none_to_empty(self.default_profile)}
        
        # This is the command used to open the profile files.
        # If blank, the system default editor is used.
        profile_editor = {none_to_empty(self.profile_editor)}
        
        # This is the directory where the program will store temporary files.
        # If blank, the default directory is used.
        cache_dir = {none_to_empty(self.cache_dir)}
        
        # This is the path to the default torch model.
        # It is downloaded automatically if blank.
        default_torch_model_path = {none_to_empty(self.default_torch_model_path)}
        
        # This is the path to the default cv2 model.
        # It is downloaded automatically if blank.
        default_cv2_model_path = {none_to_empty(self.default_cv2_model_path)}
        
        # This is the theme to use for the GUI.
        # If blank, the system default theme is used.
        # Built-in themes are Breeze and Breeze Dark
        gui_theme = {none_to_empty(self.gui_theme)}
        
        # Show out-of-memory warnings.
        show_oom_warnings = {self.show_oom_warnings}
        
        
        
        [Post-Action]
        # Post-Action settings from the GUI
        
        # Remember the last action taken.
        pa_remember_action = {self.pa_remember_action}
        
        # Last action taken.
        pa_last_action = {none_to_empty(self.pa_last_action)}
        
        # Wait time before executing the action.
        pa_wait_time = {self.pa_wait_time}
        
        # Shutdown command to use.
        pa_shutdown_command = {none_to_empty(self.pa_shutdown_command)}
        
        # Cancel the custom action if an error occurs.
        pa_cancel_on_error = {self.pa_cancel_on_error}
        
        # Commands are stored in Base32, to prevent issues with special characters.
        # This is a GUI-only feature, so readability isn't a concern.
        [Custom Commands]
        {custom_commands_str}
        
        
        [Saved Profiles]
        {saved_profiles_str}
        """
        config.read_string(multi_left_strip(conf_str))
        # Save the config.
        try:
            with open(config_path, "w", encoding="utf-8") as config_file:
                config.write(config_file)
        except OSError as e:
            logger.error(f"Failed to write configuration to {config_path}:\n{e}")
            return False
        return True

    @classmethod
    def from_config_updater(cls, conf_updater: cu.ConfigUpdater) -> "Config":
        """
        Create a Config object from a ConfigUpdater object.
        """

        config = cls()
        section = "General"
        if not conf_updater.has_section(section):
            print(
                f"Failed to load the {section} section from the config file. Proceeding with defaults."
            )
            return config

        try_to_load(config, conf_updater, section, str | None, "locale")
        try_to_load(config, conf_updater, section, str | None, "default_profile")
        try_to_load(config, conf_updater, section, str | None, "profile_editor")
        try_to_load(config, conf_updater, section, Path | None, "cache_dir")
        config.saved_profiles = {
            k: Path(v.value) for k, v in conf_updater["Saved Profiles"].items()
        }
        try_to_load(config, conf_updater, section, Path | None, "default_torch_model_path")
        try_to_load(config, conf_updater, section, Path | None, "default_cv2_model_path")
        try_to_load(config, conf_updater, section, str | None, "gui_theme")
        try_to_load(config, conf_updater, section, bool, "show_oom_warnings")

        section = "Post-Action"
        try_to_load(config, conf_updater, section, bool, "pa_remember_action")
        try_to_load(config, conf_updater, section, int, "pa_wait_time")
        try_to_load(config, conf_updater, section, str | None, "pa_shutdown_command")
        try_to_load(config, conf_updater, section, bool, "pa_cancel_on_error")
        if "Custom Commands" in conf_updater:
            config.pa_custom_commands = {
                from_base32_modified(k): from_base32_modified(v.value)
                for k, v in conf_updater["Custom Commands"].items()
            }

        # If the default profile isn't in the saved profiles, clear it.
        if (
            config.default_profile is not None
            and config.default_profile not in config.saved_profiles
        ):
            logger.error(
                f"Default profile {config.default_profile} not found in saved profiles. Clearing entry."
            )
            config.default_profile = None

        if config.default_torch_model_path is not None:
            # Verify that the model exists and has the correct hash.
            if not config.default_torch_model_path.is_file():
                print("Configured torch model does not exist. Clearing entry.")
                config.default_torch_model_path = None
            elif not md.check_hash(config.default_torch_model_path, md.TORCH_SHA256):
                print("Configured torch model has the wrong hash. Clearing entry.")
                config.default_torch_model_path = None
        if config.default_cv2_model_path is not None:
            # Verify that the model exists and has the correct hash.
            if not config.default_cv2_model_path.is_file():
                print("Configured cv2 model does not exist. Clearing entry.")
                config.default_cv2_model_path = None
            elif not md.check_hash(config.default_cv2_model_path, md.CV2_SHA256):
                print("Configured cv2 model has the wrong hash. Clearing entry.")
                config.default_cv2_model_path = None

        return config

    def load_profile(self, profile_name: str | None = None) -> tuple[bool, Exception | None]:
        """
        Load a profile from disk, if a name is given.
        First search if the profile is saved, otherwise treat it like a path.
        For None, attempt to load the default profile, be that the builtin default or the user's default.

        Special case: Reserve the name "builtin" and "none" (case insensitive) to load the built-in default profile.

        :param profile_name: [Optional] Name or path of the profile to load.
        :return: True if the profile was loaded successfully.
        """
        logger.debug(f"Loading profile {profile_name!r}...")
        # If no override is given, use the default profile.
        if profile_name is None:
            profile_name = self.default_profile

        # If the default profile is not set, use the builtin default profile.
        if profile_name is None or profile_name.lower() in self.reserved_profile_names():
            logger.debug("Loading builtin default profile")
            self.current_profile = Profile()
            return True, None

        found_profile = cli.closest_match(profile_name, list(self.saved_profiles.keys()))
        if found_profile is not None:
            profile_path = self.saved_profiles[found_profile]
            logger.debug(f"Loading profile {found_profile} from {profile_path}")
        else:
            profile_path = Path(profile_name)
            logger.debug(f"Loading profile from {profile_path}")

        # Try to load the profile from the path.
        try:
            self.current_profile = Profile.load(profile_path)
        except Exception as e:
            logger.error(f"Failed to load profile from {profile_path}:\n{e}")
            self.current_profile = Profile()
            return False, e

        return True, None

    def get_model_path(self, gpu: bool) -> Path:
        """
        Get the path to the default model.
        Check the current profile first. If it is None or the file does not exist,
        return the default model path from the config.
        If it is None, download the model first.

        :param gpu: When true, prefer the torch model.
        """
        if self.current_profile.text_detector.model_path is not None:
            model_path = Path(self.current_profile.text_detector.model_path)
            if model_path.exists():
                return model_path
            else:
                print(
                    f"Model path {model_path} selected in your current profile does not exist. Using default model."
                )

        # Models are downloaded to the folder: cache directory/models
        cache_dir = self.get_model_cache_dir()
        if gpu:
            if self.default_torch_model_path is None:
                self.default_torch_model_path = md.download_torch_model(cache_dir)
                if self.default_torch_model_path is None:
                    print("Failed to find torch model.")
                    sys.exit(1)
                self.save()
            return self.default_torch_model_path
        else:
            if self.default_cv2_model_path is None:
                self.default_cv2_model_path = md.download_cv2_model(cache_dir)
                if self.default_cv2_model_path is None:
                    print("Failed to find cv2 model.")
                    sys.exit(1)
                self.save()
            return self.default_cv2_model_path


def load_config() -> Config:
    """
    Try to load the config from disk, otherwise create a new one.
    :return:
    """
    config_path = cli.get_config_path()

    if config_path.is_file():
        conf_updater = cu.ConfigUpdater()
        try:
            conf_updater.read(config_path, encoding="utf-8")
        except OSError as e:
            logger.error(f"Failed to read configuration from {config_path}:\n{e}")
            if cli.get_confirmation("Do you want to create a new configuration file?"):
                config = Config()
                if not config.save(config_path):
                    print("\n\nProceeding with default configuration.")
                    return config
            else:
                print("Aborting.")
                sys.exit(1)
        # Parse the config from the ConfigUpdater.
        try:
            config = Config.from_config_updater(conf_updater)
        except cu.ParsingError as e:
            # When configupdater fails to parse the config, it raises a KeyError of the form:
            # ('No option `thing` found', {'key': 'thing'})
            if isinstance(e.args, tuple):
                e = e.args[0]
            logger.error(f"Failed to parse configuration from {config_path}:\n{e}")
            if cli.get_confirmation("Do you want to create a new configuration file?"):
                config = Config()
                if not config.save(config_path):
                    print("\n\nProceeding with default configuration.")
                    return config
            else:
                print("Aborting.")
                sys.exit(1)

    else:
        print("No config file found, creating a new one.")
        config = Config()
        config.save(config_path)

    return config


def try_to_load(
    obj: object, conf_updater: cu.ConfigUpdater, section: str, attr_type, attr_name: str
):
    """
    Try to load the attribute from the ConfigUpdater, validating the type.
    The key and the attribute name need to match.

    Supports attr_type:
    bool, int, float, str, Path, str | None, Path | None, StrEnum

    Union types with None will return none if the bare string is empty.

    :param obj: The object to assign it to.
    :param conf_updater: The ConfigUpdater object to load from.
    :param attr_name: The name of the attribute to load.
    :param section: The config section name.
    :param attr_type: The type to construct.
    """
    try:
        conf_data = conf_updater.get(section, attr_name).value
    except cu.NoOptionError as e:
        print(f"Option {attr_name} not found in {section}. Using default.")
        logger.debug(e)
        return
    except cu.NoSectionError as e:
        print(f"Section {section} not found in the config file. Using defaults.")
        logger.debug(e)
        return

    if attr_type == bool:
        if conf_data.lower() in ("1", "t", "true", "y", "yes", "on"):
            attr_value = True
        elif conf_data.lower() in ("0", "f", "false", "n", "no", "off"):
            attr_value = False
        else:
            print(
                f"Option {attr_name} in section {section} should be True or False, not '{conf_data}'"
            )
            return

    # check before: `StrEnum` is a `str`
    elif isinstance(attr_type, type) and issubclass(attr_type, StrEnum):
        if conf_data in attr_type.__members__.values():
            attr_value = conf_data
        else:
            print(
                f"Option {attr_name} in section {section} should be a one "
                f"of {', '.join(repr(str(_)) for _ in attr_type.__members__.values())}.\n"
                f"Failed to parse '{conf_data}'"
            )
            return

    elif attr_type == str:
        attr_value = conf_data
    elif attr_type == LongString:
        attr_value = conf_data.replace("\\n", "\n").replace("\\t", "\t").replace("\\r", "\r")
    elif attr_type == str | None:
        if conf_data == "":
            attr_value = None
        else:
            attr_value = conf_data
    elif attr_type == RegexPattern:
        try:
            attr_value = conf_data
            re.compile(attr_value)
        except re.error as e:
            print(
                f"Option {attr_name} in section {section} should be a valid regular expression.\n"
                f"Failed to parse '{conf_data}': {e}"
            )
            return
    elif attr_type in (int, Pixels, PixelsSquared):
        try:
            attr_value = int(conf_data)
        except ValueError as e:
            print(
                f"Option {attr_name} in section {section} should be an integer.\n"
                f"Failed to parse '{conf_data}': {e}"
            )
            return
    elif attr_type == float:
        try:
            attr_value = float(conf_data)
        except ValueError as e:
            print(
                f"Option {attr_name} in section {section} should be floating point number.\n"
                f"Failed to parse '{conf_data}': {e}"
            )
            return
    elif attr_type in (int | GreaterZero, Pixels | GreaterZero):
        # GreaterZero is just a signifier to check for positive numbers.
        try:
            attr_value = int(conf_data)
        except ValueError as e:
            print(
                f"Option {attr_name} in section {section} should be an integer.\n"
                f"Failed to parse '{conf_data}': {e}"
            )
            return
        if attr_value <= 0:
            print(
                f"Option {attr_name} in section {section} should be greater than zero. Limiting to 1."
            )
            attr_value = 1

    elif attr_type == ThreadLimit:
        if conf_data == "":
            attr_value = 0
        else:
            try:
                attr_value = int(conf_data)
            except ValueError as e:
                print(
                    f"Option {attr_name} in section {section} should be an integer.\n"
                    f"Failed to parse '{conf_data}': {e}"
                )
                return
            if attr_value < 0:
                print(
                    f"Option {attr_name} in section {section} should be a positive integer. Limiting to 0."
                )
                attr_value = 0

    elif attr_type == float | GreaterZero:
        # GreaterZero is just a signifier to check for positive numbers.
        try:
            attr_value = float(conf_data)
        except ValueError as e:
            print(
                f"Option {attr_name} in section {section} should be floating point number.\n"
                f"Failed to parse '{conf_data}': {e}"
            )
            return
        if attr_value <= 0:
            print(
                f"Option {attr_name} in section {section} should be greater than zero. Setting to 1."
            )
            attr_value = 0.01

    elif attr_type == Percentage:
        try:
            attr_value = float(conf_data)
        except ValueError as e:
            print(
                f"Option {attr_name} in section {section} should be a percentage.\n"
                f"Failed to parse '{conf_data}': {e}"
            )
            return
        if not 0.0 <= attr_value <= 100.0:
            print(
                f"Option {attr_name} in section {section} should be a percentage between 0 and 100. Setting to 20."
            )
            attr_value = 20.0

    elif attr_type == Path:
        try:
            attr_value = Path(conf_data)
        except ValueError as e:
            print(
                f"Option {attr_name} in section {section} should be file path.\n"
                f"Failed to parse '{conf_data}': {e}"
            )
            return
    elif attr_type == Path | None:
        if conf_data == "":
            attr_value = None
        else:
            try:
                attr_value = Path(conf_data)
            except ValueError as e:
                print(
                    f"Option {attr_name} in section {section} should be file path.\n"
                    f"Failed to parse '{conf_data}': {e}"
                )
                return
    else:
        logger.error(f"Unsupported attribute type {attr_type}.")
        return

    # Assign value.
    obj.__setattr__(attr_name, attr_value)


def none_to_empty(value: str | None) -> str:
    return "" if value is None else value


def escape_all(string: str) -> str:
    """
    Escape all special characters in a string.
    """
    return string.replace("\n", "\\n").replace("\t", "\\t").replace("\r", "\\r")


def multi_left_strip(string: str) -> str:
    """
    Strip all leading whitespace from all lines in a string.

    :param string: The string to strip.
    :return: The stripped string.
    """
    stripped_lines = (line.lstrip() for line in string.splitlines())
    return "\n".join(stripped_lines)


def format_for_version(conf_string: str, gui_mode: bool) -> str:
    """
    Format the config string for the current version of the program.

    In CLI mode, remove all GUI-only options, and vice versa.
    The comments that need to be replaces are marked as follows:
    [CLI: ...] and [GUI: ...]

    :param conf_string: The config string to format.
    :param gui_mode: Whether to format for GUI mode.
    :return: The formatted config string.
    """
    if gui_mode:
        conf_string = re.sub(r"^\s*\[CLI: (.*?)]\s*$", "", conf_string, flags=re.MULTILINE)
        conf_string = re.sub(r"^\s*\[GUI: (.*?)]\s*$", r"\1", conf_string, flags=re.MULTILINE)
        conf_string = re.sub(r"\[CLI: (.*?)]", "", conf_string)
        conf_string = re.sub(r"\[GUI: (.*?)]", r"\1", conf_string)
        # Additionally, strip out repeated spaces.
        conf_string = re.sub(r"  +", " ", conf_string)
    else:
        conf_string = re.sub(r"^\s*\[GUI: (.*?)]\s*$", "", conf_string, flags=re.MULTILINE)
        conf_string = re.sub(r"^\s*\[CLI: (.*?)]\s*$", r"\1", conf_string, flags=re.MULTILINE)
        conf_string = re.sub(r"\[GUI: (.*?)]", "", conf_string)
        conf_string = re.sub(r"\[CLI: (.*?)]", r"\1", conf_string)

    return conf_string


def from_base32_modified(data: str) -> str:
    """
    Decode a Base64 string, replacing the characters that are not valid in a command.
    """
    data = data.replace("_", "=").upper()
    return base64.b32decode(data).decode("utf-8", errors="replace")


def to_base32_modified(data: str) -> str:
    """
    Encode a string to Base64, replacing the characters that are not valid in a command.
    """
    return base64.b32encode(data.encode("utf-8")).decode("utf-8").replace("=", "_")
