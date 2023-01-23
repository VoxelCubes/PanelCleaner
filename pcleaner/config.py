import sys
from dataclasses import dataclass, field
from pathlib import Path

import configupdater as cu
from logzero import logger

from pcleaner import cli_utils as cli
from pcleaner import model_downloader as md


RESERVED_PROFILE_NAMES = ["builtin", "none"]


@dataclass
class TextDetectorConfig:
    model_path: str | None = None

    def export_to_conf(self, config_updater: cu.ConfigUpdater) -> None:
        """
        Write the config to the config updater object.

        No add_after_section here since it is the first section.

        :param config_updater: An existing config updater object.
        """

        config_str = f"""\
        [TextDetector]
        
        # Path to the text detection model, leave empty to use the built-in model.
        # The model can be found here:
        # https://github.com/zyddnys/manga-image-translator/releases/latest
        model_path = {none_to_empty(self.model_path)}
        
        """
        config_updater.read_string(multi_left_strip(config_str))

    def import_from_conf(self, config_updater: cu.ConfigUpdater) -> None:
        """
        Read the config from the config updater object.

        :param config_updater: An existing config updater object.
        """
        if not config_updater.has_section("TextDetector"):
            logger.info("No TextDetector section found in the profile, using defaults.")
            return

        try_to_load(self, config_updater, "TextDetector", str | None, "model_path")


@dataclass
class PreProcessorConfig:
    box_min_size: int = 20 * 20
    suspicious_box_min_size: int = 200 * 200
    ocr_enabled: bool = True
    ocr_max_size: int = 30 * 100
    ocr_blacklist_pattern: str = "[～．ー！？０-９]*"
    box_padding_initial: int = 2
    box_right_padding_initial: int = 3
    box_padding_extended: int = 5
    box_right_padding_extended: int = 5
    box_reference_padding: int = 20

    def export_to_conf(self, config_updater: cu.ConfigUpdater, add_after_section: str) -> None:
        """
        Write the config to the config updater object.

        :param config_updater: An existing config updater object.
        :param add_after_section: The section to add the config after.
        """
        config_str = f"""\
        [PreProcessor]
        
        # Box sizes are given in the total number of pixels, so a box of 200x200 pixels has a size of 200 * 200 = 40000.
        # To see these boxes visualized, use the --show-masks flag when cleaning and look inside the cache folder.

        # Minimum size of any box to keep it. 
        box_min_size = {self.box_min_size}
        
        # Minimum size of a box with "unknown" language to keep it. This language is typically assigned to logos and other
        # badly behaved text elements.
        suspicious_box_min_size = {self.suspicious_box_min_size}
        
        # Whether to use OCR to detect boxes that aren't worth cleaning, like ones that only contain numbers or symbols.
        ocr_enabled = {self.ocr_enabled}
        
        # Maximum size of a box to perform OCR on.
        # These useless boxes are usually small, and OCR is slow, so use this as a cutoff.
        ocr_max_size = {self.ocr_max_size}
        
        # Regex pattern to match against OCR results. 
        # Anything matching this pattern is discarded.
        # Note that the OCR model returns full-width characters, so this pattern should match them.
        ocr_blacklist_pattern = {self.ocr_blacklist_pattern}
        
        # Padding to add to each side of a box.
        # This is added to the initial boxes created by the text detector AI.
        # These boxes are visualized in green with the --cache-masks flag.
        box_padding_initial = {self.box_padding_initial}
        
        # Padding to add to the right side of a box.
        # This extension helps to cover rubytext that floats off to the right of vertical text.
        box_right_padding_initial = {self.box_right_padding_initial}
        
        # Padding to add to each side of a box.
        # This is added to an extended set of boxes, used to cut out false positives by the text detector AI's mask.
        # These boxes are visualized in purple with the --cache-masks flag.
        box_padding_extended = {self.box_padding_extended}
        
        # Padding to add to the right side of a box.
        # This extension helps to cover rubytext that floats off to the right of vertical text.
        box_right_padding_extended = {self.box_right_padding_extended}
        
        # Padding to add to each side of a box.
        # This is added to the reference boxes used to sample the original image while analyzing what mask to use.
        # These boxes are visualized in blue with the --cache-masks flag.
        box_reference_padding = {self.box_reference_padding}

        """
        preproc_conf = cu.ConfigUpdater()
        preproc_conf.read_string(multi_left_strip(config_str))
        preproc_section = preproc_conf["PreProcessor"]
        config_updater[add_after_section].add_after.space(2).section(preproc_section.detach())

    def import_from_conf(self, config_updater: cu.ConfigUpdater) -> None:
        """
        Read the config from the config updater object.

        :param config_updater: An existing config updater object.
        """
        section = "PreProcessor"
        if not config_updater.has_section(section):
            logger.info(f"No {section} section found in the profile, using defaults.")
            return

        try_to_load(self, config_updater, section, int, "box_min_size")
        try_to_load(self, config_updater, section, int, "suspicious_box_min_size")
        try_to_load(self, config_updater, section, bool, "ocr_enabled")
        try_to_load(self, config_updater, section, int, "ocr_max_size")
        try_to_load(self, config_updater, section, str, "ocr_blacklist_pattern")
        try_to_load(self, config_updater, section, int, "box_padding_initial")
        try_to_load(self, config_updater, section, int, "box_right_padding_initial")
        try_to_load(self, config_updater, section, int, "box_padding_extended")
        try_to_load(self, config_updater, section, int, "box_right_padding_extended")
        try_to_load(self, config_updater, section, int, "box_reference_padding")


@dataclass
class CleanerConfig:
    mask_growth_step_pixels: int = 2
    mask_growth_steps: int = 11
    off_white_max_threshold: int = 240
    mask_improvement_threshold: float = 0.1
    mask_max_standard_deviation: float = 15
    debug_mask_color: tuple[int, int, int, int] = (108, 30, 240, 127)

    def export_to_conf(self, config_updater: cu.ConfigUpdater, add_after_section: str) -> None:
        """
        Write the config to the config updater object.

        :param config_updater: An existing config updater object.
        :param add_after_section: The section to add the new section after.
        """
        config_str = f"""\
        [Cleaner]
        
        # Number of pixels to grow the mask by each step. 
        # This bulks up the outline of the mask, so smaller values will be more accurate but slower.
        mask_growth_step_pixels = {self.mask_growth_step_pixels}
        
        # Number of steps to grow the mask by.
        # A higher number will make more and larger masks, ultimately limited by the reference box size.
        mask_growth_steps = {self.mask_growth_steps}
        
        # Maximum threshold for a pixel to be considered off-white.
        # The median color along the edge of a mask may not be pure white,
        # so to prevent slight off-white tones on a pure-white background,
        # anything lighter than this threshold value will be rounded up to pure white.
        off_white_max_threshold = {self.off_white_max_threshold}
        
        # Minimum improvement in standard deviation of the mask to continue shrinking it.
        # The standard deviation refers to the variation is color along the edge of a mask.
        # A low variation means that the mask sits in a solid color,
        # which means it doesn't intersect any text or other objects.
        # Setting a higher value here requires a higher improvement to consider a smaller mask,
        # to give a preference to larger masks.
        mask_improvement_threshold = {self.mask_improvement_threshold}
        
        # The maximum standard deviation of a mask to consider.
        # A high value here means a higher tolerance for the mask intersecting text or other objects,
        # which isn't a good mask, as it will require inpainting anyway.
        mask_max_standard_deviation = {self.mask_max_standard_deviation}
        
        # Color to use for the debug mask. This is a tuple of RGBA values.
        debug_mask_color = {','.join(map(str, self.debug_mask_color))}
        
        """
        cleaner_conf = cu.ConfigUpdater()
        cleaner_conf.read_string(multi_left_strip(config_str))
        cleaner_section = cleaner_conf["Cleaner"]
        config_updater[add_after_section].add_after.space(2).section(cleaner_section.detach())

    def import_from_conf(self, config_updater: cu.ConfigUpdater) -> None:
        """
        Read the config from the config updater object.

        :param config_updater: An existing config updater object.
        """
        section = "Cleaner"
        if not config_updater.has_section(section):
            logger.info(f"No {section} section found in the profile, using defaults.")
            return

        try_to_load(self, config_updater, section, int, "mask_growth_step_pixels")
        try_to_load(self, config_updater, section, int, "mask_growth_steps")
        try_to_load(self, config_updater, section, int, "off_white_max_threshold")
        try_to_load(self, config_updater, section, float, "mask_improvement_threshold")
        try_to_load(self, config_updater, section, float, "mask_max_standard_deviation")
        try:
            color_tuple: tuple[int, ...] = tuple(
                int(x) for x in config_updater["Cleaner"]["debug_mask_color"].value.split(",")
            )
            if len(color_tuple) != 4:
                raise ValueError(
                    f"Invalid color tuple length. Expected 4: 'Red, Green, Blue, Alpha' got {len(color_tuple)}"
                )
            color_tuple: tuple[int, int, int, int]
            self.debug_mask_color = color_tuple
        except (cu.NoOptionError, ValueError):
            pass


@dataclass
class DenoiserConfig:
    noise_min_standard_deviation: float = 0.25
    noise_outline_size: int = 5
    noise_fade_radius: int = 1
    colored_images: bool = False
    filter_strength: int = 10
    color_filter_strength: int = 10
    template_window_size: int = 7
    search_window_size: int = 21

    def export_to_conf(self, config_updater: cu.ConfigUpdater, add_after_section: str) -> None:
        """
        Write the config to the config updater object.

        :param config_updater: An existing config updater object.
        :param add_after_section: The section to add the new section after.
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
        
        # The minimum standard deviation of colors around the edge of a given mask
        # to perform denoising on the region around the mask.
        noise_min_standard_deviation = {self.noise_min_standard_deviation}
        
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
        denoiser_conf.read_string(multi_left_strip(config_str))
        denoiser_section = denoiser_conf["Denoiser"]
        config_updater[add_after_section].add_after.space(2).section(denoiser_section.detach())

    def import_from_conf(self, config_updater: cu.ConfigUpdater) -> None:
        """
        Read the config from the config updater object.

        :param config_updater: An existing config updater object.
        """
        section = "Denoiser"
        if not config_updater.has_section(section):
            logger.info(f"No {section} section found in the profile, using defaults.")
            return

        try_to_load(self, config_updater, section, float, "noise_min_standard_deviation")
        try_to_load(self, config_updater, section, int, "noise_outline_size")
        try_to_load(self, config_updater, section, int, "noise_fade_radius")
        try_to_load(self, config_updater, section, bool, "colored_images")
        try_to_load(self, config_updater, section, int, "filter_strength")
        try_to_load(self, config_updater, section, int, "color_filter_strength")
        try_to_load(self, config_updater, section, int, "template_window_size")
        try_to_load(self, config_updater, section, int, "search_window_size")


@dataclass
class Profile:
    """
    A profile is a collection of settings that can be saved and loaded from disk.
    """

    text_detector: TextDetectorConfig = TextDetectorConfig()
    pre_processor: PreProcessorConfig = PreProcessorConfig()
    cleaner: CleanerConfig = CleanerConfig()
    denoiser: DenoiserConfig = DenoiserConfig()

    def write(self, path: Path) -> bool:
        """
        Write the profile to a file.

        :param path: The path to write the profile to.
        :return: True if the profile was written successfully, False otherwise.
        """
        config_updater = cu.ConfigUpdater()
        self.text_detector.export_to_conf(config_updater)
        self.pre_processor.export_to_conf(config_updater, "TextDetector")
        self.cleaner.export_to_conf(config_updater, "PreProcessor")
        self.denoiser.export_to_conf(config_updater, "Cleaner")
        try:
            with open(path, "w") as file:
                config_updater.write(file)
            return True
        except Exception as e:
            logger.error(f"Failed to write profile to {path}:\n{e}")
            return False

    @classmethod
    def load(cls, path: Path) -> "Profile":
        """
        Load a profile from a config file.
        """
        config = cu.ConfigUpdater()
        try:
            config.read(path)
            profile = cls()
            profile.text_detector.import_from_conf(config)
            profile.pre_processor.import_from_conf(config)
            profile.cleaner.import_from_conf(config)
            profile.denoiser.import_from_conf(config)
        except Exception as e:
            logger.error(f"Failed to load profile from {path}:\n{e}")
            profile = cls()
            print("Failed to load profile, using default profile.")
        return profile


@dataclass
class Config:
    """
    The main configuration class.
    These setting are saved to disk.

    saved_profiles: Saved profiles contains a mapping from profile name to profile path, where it is saved.
    profile_editor: The program to use to edit the profile files. When blank, the default editor is used.
    """

    current_profile: Profile = Profile()
    default_profile: str | None = None
    saved_profiles: dict[str, Path] = field(default_factory=dict)
    profile_editor: str | None = None
    cache_dir: Path | None = None
    default_torch_model_path: Path | None = None  # CUDA
    default_cv2_model_path: Path | None = None  # CPU

    def show(self):
        """
        Print the current configuration to the console.
        """
        print("Current Configuration:\n")
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
            self.default_torch_model_path
            if self.default_torch_model_path is not None
            else "Not downloaded",
        )
        print(
            "Default CV2 Model Path:",
            self.default_cv2_model_path
            if self.default_cv2_model_path is not None
            else "Not downloaded",
        )

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

        conf_str = f"""\
        [General]
        
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
    def from_config_updater(cls, conf_updater: cu.ConfigUpdater):
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

        try_to_load(config, conf_updater, section, str | None, "default_profile")
        try_to_load(config, conf_updater, section, str | None, "profile_editor")
        try_to_load(config, conf_updater, section, Path | None, "cache_dir")
        config.saved_profiles = {
            k: Path(v.value) for k, v in conf_updater["Saved Profiles"].items()
        }
        try_to_load(config, conf_updater, section, Path | None, "default_torch_model_path")
        try_to_load(config, conf_updater, section, Path | None, "default_cv2_model_path")

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

    def load_profile(self, profile_name: str | None = None):
        """
        Load a profile from disk, if a name is given.
        First search if the profile is saved, otherwise treat it like a path.
        For None, attempt to load the default profile.

        Special case: Reserve the name "builtin" and "none" (case insensitive) to load the built-in default profile.

        :param profile_name: Name or path of the profile to load.
        """
        # If no override is given, use the default profile.
        if profile_name is None:
            profile_name = self.default_profile

        # If the default profile is not set, use the builtin default profile.
        if profile_name is None:
            return

        # Check the reserved names.
        if profile_name.lower() in RESERVED_PROFILE_NAMES:
            return

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

    def get_model_path(self, cuda: bool) -> Path:
        """
        Get the path to the default model.
        Check the current profile first. If it is None or the file does not exist,
        return the default model path from the config.
        If it is None, download the model first.

        :param cuda: When true, prefer the torch model.
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
        if cuda:
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
            conf_updater.read(config_path)
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
    bool, int, float, str, Path, str | None, Path | None

    Union types with None will return none if the bare string is empty.

    :param obj: The object to assign it to.
    :param attr_name: The name of the attribute to load.
    :param section: The config section name.
    :param attr_type: The type to construct.
    :param conf_updater: The ConfigUpdater object to load from.
    """
    try:
        conf_data = conf_updater.get(section, attr_name).value
    except cu.NoOptionError as e:
        print(f"Option {attr_name} not found in {section}. Using default.")
        logger.debug(e)
        return

    # Handle bool specially.
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
    elif attr_type == str:
        attr_value = conf_data
    elif attr_type == str | None:
        if conf_data == "":
            attr_value = None
        else:
            attr_value = conf_data
    elif attr_type == int:
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


def multi_left_strip(string: str) -> str:
    """
    Strip all leading whitespace from all lines in a string.

    :param string: The string to strip.
    :return: The stripped string.
    """
    stripped_lines = (line.lstrip() for line in string.splitlines())
    return "\n".join(stripped_lines)
