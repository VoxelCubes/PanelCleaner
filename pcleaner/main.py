"""Panel Cleaner

Usage:
    pcleaner clean [<image_path> ...] [--output_dir=<output_dir>] [--profile=<profile>]
        [--save-only-mask | --save-only-cleaned | --save-only-text]
        [--separate-noise-mask] [--separate-inpaint-mask] [--hide-analytics] [--extract-text]
        [--skip-text-detection] [--skip-pre-processing] [--skip-masking] [--skip-denoising] [--skip-inpainting]
        [--keep-cache] [--cache-masks] [--notify] [--debug]
    pcleaner profile (list | new <profile_name> [<profile_path>] | add <profile_name> <profile_path> |
        open <profile_name> | delete <profile_name> | set-default <profile_name> | repair <profile_name> |
        purge-missing) [--debug]
    pcleaner gui [<image_path> ...] [--debug]
    pcleaner ocr [<image_path> ...] [--output-path=<output_path>] [--csv] [--profile=<profile>] [--cache-masks] [--debug]
    pcleaner config (show | open)
    pcleaner cache clear (all | models | cleaner)
    pcleaner load models [--cuda | --cpu | --both] [--force]
    pcleaner languages list
    pcleaner --help
    pcleaner --version
    pcleaner [--debug]

Subcommands:
    (blank)          Open the GUI.
    clean            Clean the given image(s). Any number of images and directories can be given.
    profile          Manage profiles. These are files storing the settings for the program.
        list         List all saved profiles.
        new          Create a new profile. Supply a name to use and, optionally, a path to save it to.
                     By default, new profiles are saved in the config directory.
        add          Add an existing profile to the list of saved profiles. This way it can be loaded by name alone.
                     Provide the name to save it under and the path the file is located at.
        open         Open a saved profile in the default editor (unless specified in the config).
        delete       Delete a saved profile.
        set-default  Set a profile as the default profile. This way it will be loaded automatically.
        repair       Repair a profile. This will remove any invalid entries and save the profile.
                     Warning: Changes to the comments won't be preserved, only settings.
        purge-missing  Remove all profiles that link to a file that doesn't exist.
    gui              Open the GUI. This is also automatically invoked if no command is given.
    ocr              Run only the OCR on the given image(s). Any number of images and directories can be given.
                     The output will be saved in a single text file for the whole batch.
    config           View or edit the config file. This stores setting independent of profiles.
        show         Show the current configuration. This doesn't show the current profile.
        open         Open the config file in the default editor (unless specified in the config).
    cache clear      Clear the cache. This is where the program stores downloaded models and other files.
        all          Clear all cache files.
        models       Clear only the models.
        cleaner      Clear only the temporary masks and debug data.
    load models       Download the models used by the program. If neither --cuda nor --cpu is specified, the program will
                     try to use CUDA if available. If it is not, it will fall back to CPU.
                     This is done automatically when needed, but can be done manually.
    languages list   List the languages and their codes supported for OCR.


Options:
    <image_path>                    One or multiple files or directories to clean.
                                    Leave blank to use the current working directory.
    -o <output_dir> --output_dir=<output_dir>  The directory to save the output files to.
                                    By default, they are saved in the same directory as the input files.
    -p <profile> --profile=<profile>  The profile to use. Specify either the name of a saved profile
                                    or a path to a profile file. If a default profile is set, you can still use
                                    the builtin default by using the name "none" or "builtin".
    -k --keep-cache                 Keep the cache files from the previous run.
                                    These are normally deleted in the text detection step.
    -m --save-only-mask             Save only the mask image. This is the overlay to clean the original image.
    -c --save-only-cleaned          Save only the cleaned image. This is the original image with the mask applied.
    -t --save-only-text             Save only the text from the image cut out of the original image. This will
                                    automatically set the --extract-text option.
    -e --extract-text               Extract the text bubbles from the original image. Essentially deleting everything
                                    except the text. The cleaning or denoising step must be run for this to work.
    -n --separate-noise-mask        DEPRECATED Save the noise mask separately from the main mask.
    -i --separate-inpaint-mask      DEPRECATED Save the inpaint mask separately from the main mask.
    -T --skip-text-detection        Do not run the text detection AI model. This is step 1/5.
    -P --skip-pre-processing        Do not run data pre-processing. This is step 2/5.
    -M --skip-masking               Do not run the masking process. This is step 3/5.
    -D --skip-denoising             Do not run the denoising process. This an optional step 4/5.
    -I --skip-inpainting            Do not run the inpainting process. This is an optional step 5/5.
    -s --cache-masks                Save the masks used to clean the image in the cache directory.
    -a --hide-analytics             Hide the analytics. These are the statistics about the
                                    cleaning accuracy.
    --notify                        Show a notification when the program is done.
    <profile_path>                  The path to the profile file to add.
    <profile_name>                  The saved name of the profile to open, delete, or set as default.
    --output-path=<output_path>     The path to save the OCR output file to.
    --csv                           Save the output of the OCR as a CSV file
    --cuda                          Load the torch models that support CUDA. They will only be used if supported.
    --cpu                           Load the open cv2 models that are optimized for CPU.
                                    They will only be used as a fallback, unless specified in the config.
    --both                          Load both the torch and open cv2 models.
    --force                         Force the models to be downloaded, even if they already exist.
    -d --debug                      Show debug information.
    -v --version                    Show the version and exit.
    -h --help                       Show this screen.

Examples:
    pcleaner clean myfolder               This will clean all images in the folder, saving the output to
                                    a folder inside myfolder called cleaned.

    pcleaner clean myfolder -o myoutput   This will clean all images in the folder, saving the output to
                                    a folder called myoutput, placed inside myfolder.

    pcleaner clean myfolder myfolder2 mypng myjpg  This will clean all images in the folders and all given files,
                                    saving the outputs to folders called cleaned, placed inside of these folders
                                    or in the parent directory of the input files, respectively.

    pcleaner clean myfolder -p myprofile  This will clean all the images, but use the settings from the profile
                                    called myprofile.

    pcleaner clean myfolder -p myprofile2 -TP  This will skip the text detection and pre-processing steps,
                                    but still run the cleaning process using the settings from the profile
                                    called myprofile2. This can be useful when you tweaked settings only
                                    related to the cleaning process. You can save time skipping the first one
                                    or two steps, since the results are saved in the cache directory (unless
                                    you choose to delete them).

"""

import json
import multiprocessing
import platform
import sys
import time
from uuid import uuid4
from multiprocessing import Pool
from pathlib import Path
import logging

import torch
from PIL import Image
from docopt import docopt
from loguru import logger
from tqdm import tqdm

import pcleaner.analytics as an
import pcleaner.cli_utils as cli
import pcleaner.config as cfg
import pcleaner.denoiser as dn
import pcleaner.helpers as hp
import pcleaner.image_export as ie
import pcleaner.inpainting as ip
import pcleaner.image_ops as ops
import pcleaner.masker as ma
import pcleaner.memory_watcher as mw
import pcleaner.model_downloader as md
import pcleaner.ocr.ocr as ocr
import pcleaner.ocr.supported_languages as osl
import pcleaner.output_structures as ost
import pcleaner.preprocessor as pp
import pcleaner.profile_cli as pc
import pcleaner.structures as st
from pcleaner import __version__
from pcleaner.config import LayeredExport


# Allow loading of large images.
Image.MAX_IMAGE_PIXELS = 2**32


def main() -> None:
    args = docopt(__doc__, version=f"Panel Cleaner {__version__}")
    # Loglevel is Warning by default.
    logger.remove()

    # When bundling an executable, this can be None if no console is supplied.
    if sys.stdout is not None:
        if args.debug:
            logger.add(sys.stdout, level="DEBUG")
        else:
            logger.add(sys.stdout, level="WARNING")

    logging.getLogger("transformers").setLevel(logging.ERROR)

    logger.debug(args)

    cli.get_log_path().parent.mkdir(parents=True, exist_ok=True)

    # Set up file logging.
    logger.add(str(cli.get_log_path()), rotation="10 MB", retention="1 week", level="DEBUG")

    cli.dump_system_info(__file__)

    # If save-only-text is set, set extract-text to true, as it is required.
    # Also, automatically skip the Denoising step, as it is not needed.
    # This also means that the save-only-text option will not be regarded in the
    # denoising step.
    if args.save_only_text:
        args.extract_text = True
        args.skip_denoising = True

    if args.profile:
        # Handle profile subcommands.
        config = cfg.load_config()

        if args.list:
            pc.list_profiles(config)
        elif args.new:
            _, msg = pc.new_profile(config, args.profile_name, args.profile_path, cli_mode=True)
            print(msg)
        elif args.add:
            _, msg = pc.add_profile(config, args.profile_name, args.profile_path)
            print(msg)
        elif args.open:
            pc.open_profile(config, args.profile_name)
        elif args.delete:
            pc.delete_profile(config, args.profile_name)
        elif args.set_default:
            pc.set_default_profile(config, args.profile_name)
        elif args.repair:
            pc.repair_profile(config, args.profile_name)
        elif args.purge_missing:
            pc.purge_missing_profiles(config)
        else:
            raise ValueError("Invalid profile subcommand.")

    elif args.ocr:
        config = cfg.load_config()
        config.load_profile(args["--profile"])
        # Ignore the rejected tiff list, as those are already visible in CLI mode.
        try:
            image_paths, _ = hp.discover_all_images(args.image_path, cfg.SUPPORTED_IMG_TYPES)
        except OSError as e:
            print(f"Error: {e}")
            sys.exit(1)
        run_ocr(config, image_paths, args.output_path, args.cache_masks, args.csv)

    elif args.cache and args.clear:
        config = cfg.load_config()
        clear_cache(config, args.all, args.models, args.cleaner)

    elif args.load and args.models:
        config = cfg.load_config()
        md.download_models(config, args.force, args.cuda or args.both, args.cpu or args.both)

    elif args.config:
        # Handle config subcommand.
        config = cfg.load_config()

        if args.show:
            config.show()
        elif args.open:
            cli.open_file_with_editor(cli.get_config_path(), config.profile_editor)
    elif args.languages and args.list:
        cli.list_all_languages()

    elif args.clean:
        img_paths: str = ""
        if args.notify:
            img_paths = ", ".join(map(str, args.image_path))
            # Prevent this fom getting too long.
            if len(img_paths) > 200:
                img_paths = img_paths[:200] + "..."
            hp.send_desktop_notification("Cleaning started.", f"Cleaning: {img_paths}")

        try:
            # Do the actual work.
            config = cfg.load_config()
            config.load_profile(args["--profile"])
            logger.debug(config)

            if args.output_dir is None:
                args.output_dir = Path("cleaned")
                args.relative_output = True
            else:
                args.output_dir = Path(args.output_dir)

            if args.separate_noise_mask or args.separate_inpaint_mask:
                print(
                    "Warning: saving noise and inpainting masks separately is DEPRECATED.\n"
                    "The --separate-noise-mask and --separate-inpaint-mask will be removed\n"
                    "entirely in the next version, they are no longer supported."
                )

            # start timer.
            start = time.time()
            run_cleaner(
                image_paths=args.image_path,
                output_dir=args.output_dir,
                config=config,
                skip_text_detection=args.skip_text_detection,
                skip_pre_processing=args.skip_pre_processing,
                skip_masking=args.skip_masking,
                skip_denoising=args.skip_denoising,
                skip_inpainting=args.skip_inpainting,
                save_only_mask=args.save_only_mask,
                save_only_cleaned=args.save_only_cleaned,
                save_only_text=args.save_only_text,
                extract_text=args.extract_text,
                cache_masks=args.cache_masks,
                hide_analytics=args.hide_analytics,
                keep_cache=args.keep_cache,
                debug=args.debug,
            )
            # end timer.
            end = time.time()
            print(f"\nTime elapsed: {end - start:.2f} seconds")
        except Exception as e:
            if args.notify:
                hp.send_desktop_notification("Cleaning failed.", str(e))
            raise e

        if args.notify:
            # Prevent this fom getting too long.
            hp.send_desktop_notification("Cleaning complete.", f"Cleaned: {img_paths}")

    else:
        # Launch the GUI. Either the user specified it, or no command was given.
        # This is done so that a bundled executable can be launched in gui mode without a command,
        # without hindering access to the cli.
        try:
            import pcleaner.gui.launcher as gui
        except ImportError:
            if not args.gui:
                print(
                    "This is the CLI version of Panel Cleaner. "
                    "Calling pcleaner-cli without any arguments will attempt to launch the GUI. "
                    "Please install the GUI version 'pcleaner' to use the GUI."
                )
            else:
                print(
                    "The GUI version of Panel Cleaner is not installed. "
                    "Please install the GUI version 'pcleaner' to use the GUI."
                )
            sys.exit(1)
        else:
            gui.launch(args.image_path, args.debug)


def run_cleaner(
    image_paths: list[Path],
    output_dir: Path,
    config: cfg.Config,
    skip_text_detection: bool,
    skip_pre_processing: bool,
    skip_masking: bool,
    skip_denoising: bool,
    skip_inpainting: bool,
    save_only_mask: bool,
    save_only_cleaned: bool,
    save_only_text: bool,
    extract_text: bool,
    cache_masks: bool,
    hide_analytics: bool,
    keep_cache: bool,
    debug: bool,
):
    """
    Run the masker on the given images.

    :param image_paths: The paths to the images to clean.
    :param output_dir: The directory to save the output files to.
    :param config: The config to use.
    :param skip_text_detection: Whether to skip the text detection step.
    :param skip_pre_processing: Whether to skip the pre-processing step.
    :param skip_masking: Whether to skip the masking step.
    :param skip_denoising: Whether to skip the denoising step.
    :param skip_inpainting: Whether to skip the inpainting step.
    :param save_only_mask: Whether to save only the mask.
    :param save_only_cleaned: Whether to save only the cleaned image.
    :param save_only_text: Whether to save only the text.
    :param extract_text: Whether to extract the text from the image.
    :param cache_masks: Whether to save the masks used to clean the image in the cache directory.
    :param hide_analytics: Whether to hide the analytics.
    :param keep_cache: Whether to keep the cache directory for the text detection step.
    :param debug: Whether to show debug information.
    """
    if config.show_oom_warnings:
        mw.start_memory_watcher()

    profile = config.current_profile

    # Override the skip denoising flag if the config disables denoising.
    if not profile.denoiser.denoising_enabled:
        logger.debug("Denoising is disabled in the config, skipping denoising step.")
        skip_denoising = True

    # Override the skip inpainting flag if the config disables inpainting.
    if not profile.inpainter.inpainting_enabled:
        logger.debug("Inpainting is disabled in the config, skipping inpainting step.")
        skip_inpainting = True

    # Catch jokesters who want to skip all 5 steps.
    if (
        skip_text_detection
        and skip_pre_processing
        and skip_masking
        and skip_denoising
        and skip_inpainting
    ):
        print("Well how about that, you want to skip all 5 steps? I guess I'm not needed here.")
        return

    cache_dir = config.get_cleaner_cache_dir()
    logger.debug(f"Cache directory: {cache_dir}")

    # If caching masks, direct the user to the cache directory.
    if cache_masks:
        print(
            f"You can find the masks being generated in real-time in the cache directory:\n\n{cache_dir}\n"
        )

    if not skip_text_detection:  # Text Detection ==================================================
        # Find all the images in the given image paths.
        # Ignore the rejected tiff list, as those are already visible in CLI mode.
        try:
            image_paths, _ = hp.discover_all_images(image_paths, cfg.SUPPORTED_IMG_TYPES)
        except OSError as e:
            print(f"Error: {e}")
            sys.exit(1)

        if not image_paths:
            print("No images found.")
            return
        else:
            print(f"Found {len(image_paths)} {hp.f_plural(len(image_paths), 'image', 'images')}.")
            debug_path_printout = "\n".join(map(str, image_paths))
            logger.debug(f"Image paths: \n{debug_path_printout}")

        # Delete the cache directory if not explicitly keeping it.
        if len(list(cache_dir.glob("*"))) > 0 and not keep_cache:
            cli.empty_cache_dir(cache_dir)
        # Get the model file, downloading it if necessary.
        gpu = torch.cuda.is_available() or torch.backends.mps.is_available()
        if torch.backends.mps.is_available():
            initialize_ocr_model()
        model_path = config.get_model_path(gpu)

        split_images(image_paths, profile, cache_dir)

        print("Running text detection AI model...")
        try:
            pp.generate_mask_data(
                image_paths,
                config_general=profile.general,
                config_detector=profile.text_detector,
                model_path=model_path,
                output_dir=cache_dir,
            )
        except NotImplementedError as e:
            if "CUDA" in str(e):
                # Get the current CUDA version.
                cuda_version = "Error, no version found."
                try:
                    version = torch.version.cuda
                    if version is not None:
                        cuda_version = version
                except Exception:
                    pass

                logger.error(
                    "Your GPU does not support the required CUDA operations.\n\n"
                    "Try uninstalling the current versions of torch and torchvision\n"
                    "and installing the CPU version (or a different CUDA version) instead.\n"
                    "You can find further instructions here: https://pytorch.org/get-started/locally/\n"
                    'Check the "Compute Platform" section to see the available versions.\n\n'
                    f"Your current CUDA version is: {cuda_version}\n"
                )
                raise e

        # Leave some extra space here if drawing analytics, so it looks better.
        if not hide_analytics:
            print("\n")

    if not skip_pre_processing:  # Pre-Processing ==================================================
        # Flush it so it shows up before the progress bar.
        print("Running box data Preprocessor...", flush=True)
        # Make sure it actually flushes at all costs = wait 100 ms.
        # (It takes several seconds to load the ocr model, so this is fine.)
        time.sleep(0.1)
        if profile.preprocessor.ocr_enabled:
            ocr_engine_factory = ocr.build_ocr_engine_factory(
                profile.preprocessor.ocr_use_tesseract, profile.preprocessor.ocr_engine
            )
        else:
            ocr_engine_factory = None

        # Warn the user if he's trying to force an unsupported language.
        if profile.preprocessor.ocr_language not in (
            osl.LanguageCode.detect_box,
            osl.LanguageCode.detect_page,
        ):
            if profile.preprocessor.ocr_language not in ocr.get_all_available_langs():
                lang_name = osl.LANGUAGE_CODE_TO_NAME[profile.preprocessor.ocr_language]
                print(
                    f"\nWarning: The language '{lang_name}' "
                    f"is not supported by any of your current OCR engines.\n"
                )

        ocr_analytics: list[st.OCRAnalytic] = []
        for json_file_path in tqdm(list(cache_dir.glob("*.json"))):
            ocr_analytics_of_a_page = pp.prep_json_file(
                json_file_path,
                preprocessor_conf=profile.preprocessor,
                cache_masks=cache_masks,
                ocr_engine_factory=ocr_engine_factory,
            )
            if ocr_analytics_of_a_page is not None:
                ocr_analytics.append(ocr_analytics_of_a_page)

        if ocr_analytics and not hide_analytics:
            print(
                an.show_ocr_analytics(
                    ocr_analytics, profile.preprocessor.ocr_max_size, an.terminal_width()
                )
            )

    if not skip_masking:  # Masking ================================================================
        print("Running Masker...")
        # Read the json files in the image directory.
        json_files = Path(cache_dir).glob("*#clean.json")

        data = [
            st.MaskerData(
                json_file,
                cache_dir,
                profile.masker,
                extract_text,
                cache_masks,
                debug,
            )
            for json_file in json_files
        ]

        masker_analytics_raw: list[st.MaskFittingAnalytic] = []

        # Check the size of the required pool, run sequentially if the size is 1.
        core_limit = profile.masker.max_threads
        if core_limit == 0:
            core_limit = multiprocessing.cpu_count()
        pool_size = min(core_limit, len(data))

        if pool_size > 1:
            with Pool(processes=pool_size) as pool:
                for analytic in tqdm(pool.imap(ma.mask_page, data), total=len(data)):
                    masker_analytics_raw.extend(analytic)
        else:
            for masker_data in tqdm(data):
                analytic = ma.mask_page(masker_data)
                masker_analytics_raw.extend(analytic)

        if not hide_analytics and masker_analytics_raw:
            print(
                an.show_masker_analytics(masker_analytics_raw, profile.masker, an.terminal_width())
            )

    if not skip_denoising:  # Denoising ============================================================
        print("Running Denoiser...")
        # Read the json files in the image directory.
        json_files = Path(cache_dir).glob("*#mask_data.json")

        data = [
            st.DenoiserData(
                json_file,
                cache_dir,
                profile.denoiser,
                debug,
            )
            for json_file in json_files
        ]

        denoise_analytics_raw = []

        # Check the size of the required pool, run sequentially if the size is 1.
        core_limit = profile.denoiser.max_threads
        if core_limit == 0:
            core_limit = multiprocessing.cpu_count()
        pool_size = min(core_limit, len(data))

        if pool_size > 1:
            with Pool(processes=pool_size) as pool:
                for analytic in tqdm(pool.imap(dn.denoise_page, data), total=len(data)):
                    denoise_analytics_raw.append(analytic)
        else:
            for denoise_data in tqdm(data):
                analytic = dn.denoise_page(denoise_data)
                denoise_analytics_raw.append(analytic)

        if not hide_analytics and denoise_analytics_raw:
            print(
                an.show_denoise_analytics(
                    denoise_analytics_raw,
                    profile.denoiser.noise_min_standard_deviation,
                    profile.masker.mask_max_standard_deviation,
                    an.terminal_width(),
                )
            )

    if not skip_inpainting:  # Inpainting ==========================================================
        print("Running Inpainter...")
        # Read the json files in the image directory.
        page_json_files = list(Path(cache_dir).glob("*#clean.json"))
        mask_json_files = list(Path(cache_dir).glob("*#mask_data.json"))
        # Zip together the matching json files.
        zipped_jsons = []
        for page_json_file in page_json_files:
            for mask_json_file in mask_json_files:
                if mask_json_file.name.startswith(page_json_file.name.split("#")[0]):
                    zipped_jsons.append((page_json_file, mask_json_file))
                    break

        # Sanity check.
        if not (len(zipped_jsons) == len(page_json_files) == len(mask_json_files)):
            print(f"Found: {len(page_json_files)} page json files.")
            print(f"Found: {len(mask_json_files)} mask json files.")
            print(f"Matching: {len(zipped_jsons)} json files.")
            raise ValueError("Mismatched number of json files.")

        md.ensure_inpainting_available(config)
        inpainter_model = ip.InpaintingModel(config)

        data = [
            st.InpainterData(
                page_json_file,
                mask_json_file,
                cache_dir,
                profile.masker,
                profile.denoiser,
                profile.inpainter,
                debug,
            )
            for page_json_file, mask_json_file in zipped_jsons
        ]

        inpaint_analytics_raw = []
        for inpaint_data in tqdm(data):
            analytic = ip.inpaint_page(inpaint_data, inpainter_model)
            inpaint_analytics_raw.append(analytic)

        if not hide_analytics and inpaint_analytics_raw:
            print(
                an.show_inpainting_analytics(
                    inpaint_analytics_raw,
                    profile.inpainter.min_inpainting_radius,
                    profile.inpainter.max_inpainting_radius,
                    an.terminal_width(),
                )
            )

    print("Exporting results...")  # Exporting =====================================================

    # Figure out what outputs should be exported.
    # They must be sorted from lowest to highest priority.
    cleaned_outputs_whitelist = [
        ost.Output.masked_output,
        ost.Output.denoised_output,
        ost.Output.inpainted_output,
    ]
    masked_outputs_whitelist = [
        ost.Output.final_mask,
        ost.Output.denoise_mask,
        ost.Output.inpainted_mask,
    ]
    text_outputs_whitelist = [
        ost.Output.isolated_text,
    ]

    def remove_output(output: ost.Output, whitelist: list[ost.Output]) -> None:
        if output in whitelist:
            whitelist.remove(output)

    if save_only_text:
        masked_outputs_whitelist = []
        cleaned_outputs_whitelist = []
    if save_only_cleaned:
        masked_outputs_whitelist = []
        text_outputs_whitelist = []
    if save_only_mask:
        cleaned_outputs_whitelist = []
        text_outputs_whitelist = []
    if skip_denoising:
        remove_output(ost.Output.denoised_output, cleaned_outputs_whitelist)
        remove_output(ost.Output.denoise_mask, masked_outputs_whitelist)
    if skip_inpainting:
        remove_output(ost.Output.inpainted_output, cleaned_outputs_whitelist)
        remove_output(ost.Output.inpainted_mask, masked_outputs_whitelist)
    if not extract_text:
        remove_output(ost.Output.isolated_text, text_outputs_whitelist)

    export_targets = ie.discover_viable_outputs(
        cache_dir, cleaned_outputs_whitelist, masked_outputs_whitelist, text_outputs_whitelist
    )

    # Merge the splits through the export targets.
    export_targets = merge_export_splits(
        export_targets, cache_dir, profile.general.merge_after_split
    )

    # Pack all the arguments in batches.
    data = [
        (
            target.original_path,
            target.export_path,
            cache_dir,
            target.uuid,
            target.outputs,
            output_dir,
            profile.general.preferred_file_type,
            profile.general.preferred_mask_file_type,
            profile.denoiser.denoising_enabled,
            profile.general.layered_export,
        )
        for target in export_targets
    ]

    # Check the size of the required pool, run sequentially if the size is 1.
    core_limit = profile.general.max_threads_export
    if core_limit == 0:
        core_limit = multiprocessing.cpu_count()
    pool_size = min(core_limit, len(data))

    if pool_size > 1:
        with Pool(processes=pool_size) as pool:
            for _ in tqdm(pool.imap_unordered(ie.copy_to_output_batched, data), total=len(data)):
                pass
    else:
        for export_data in tqdm(data):
            ie.copy_to_output_batched(export_data)

    # For bulk exports, we need a common parent directory.
    if not output_dir.is_absolute():
        common_parent = hp.common_path_parent(
            [image_object.original_path for image_object in export_targets]
        )
        output_dir = common_parent / output_dir

    if profile.general.layered_export == LayeredExport.PSD_BULK:
        print(f"Bulk exporting to {output_dir}...")
        ie.bundle_psd(
            output_dir,
            cache_dir,
            [export_target.original_path for export_target in export_targets],
            [export_target.uuid for export_target in export_targets],
        )

    print("\nDone!")


def run_ocr(
    config: cfg.Config,
    image_paths: list[Path],
    output_path: str | None,
    cache_masks: bool,
    csv_output: bool,
):
    """
    Run OCR on the given images. This is a byproduct of the pre-processing step,
    expanded to all bubbles.

    :param config: The config to use.
    :param image_paths: The images to run OCR on.
    :param output_path: The path to output the results to.
    :param cache_masks: Whether to cache the masks.
    :param csv_output: Whether to output CSV data
    """
    if config.show_oom_warnings:
        mw.start_memory_watcher()

    cache_dir = config.get_cleaner_cache_dir()
    profile = config.current_profile

    ocr_processor = ocr.build_ocr_engine_factory(
        profile.preprocessor.ocr_use_tesseract, profile.preprocessor.ocr_engine
    )

    # Warn the user if he's trying to force an unsupported language.
    if profile.preprocessor.ocr_language not in (
        osl.LanguageCode.detect_box,
        osl.LanguageCode.detect_page,
    ):
        if profile.preprocessor.ocr_language not in ocr.get_all_available_langs():
            lang_name = osl.LANGUAGE_CODE_TO_NAME[profile.preprocessor.ocr_language]
            print(
                f"\nWarning: The language '{lang_name}' "
                f"is not supported by any of your current OCR engines.\n"
            )

    logger.debug(f"Cache directory: {cache_dir}")

    # If caching masks, direct the user to the cache directory.
    if cache_masks:
        print(
            f"You can find the masks being generated in real-time in the cache directory:\n\n{cache_dir}\n"
        )

    # Delete the cache directory if not explicitly keeping it.
    if len(list(cache_dir.glob("*"))) > 0:
        cli.empty_cache_dir(cache_dir)
    # Get the model file, downloading it if necessary.
    gpu = torch.cuda.is_available() or torch.backends.mps.is_available()
    if torch.backends.mps.is_available():
        initialize_ocr_model()
    model_path = config.get_model_path(gpu)

    split_images(image_paths, profile, cache_dir)

    print("Running text detection AI model...")
    # start = time.perf_counter()
    try:
        pp.generate_mask_data(
            image_paths,
            config_general=profile.general,
            config_detector=profile.text_detector,
            model_path=model_path,
            output_dir=cache_dir,
        )
    except NotImplementedError as e:
        if "CUDA" in str(e):
            # Get the current CUDA version.
            cuda_version = "Error, no version found."
            try:
                version = torch.version.cuda
                if version is not None:
                    cuda_version = version
            except Exception:
                pass

            logger.error(
                "Your GPU does not support the required CUDA operations.\n\n"
                "Try uninstalling the current versions of torch and torchvision\n"
                "and installing the CPU version (or a different CUDA version) instead.\n"
                "You can find further instructions here: https://pytorch.org/get-started/locally/\n"
                'Check the "Compute Platform" section to see the available versions.\n\n'
                f"Your current CUDA version is: {cuda_version}\n"
            )
            raise e
    # end = time.perf_counter()
    # print(f"\nTime elapsed: {end - start:.4f} seconds")
    print("\n")

    # Flush it so it shows up before the progress bar.
    print("Running box data Pre-Processor...", flush=True)
    # Make sure it actually flushes at all costs = wait 100 ms.
    # (It takes several seconds to load the ocr model, so this is fine.)
    time.sleep(0.1)

    # Modify the profile to OCR all boxes.
    # Make sure OCR is enabled.
    profile.preprocessor.ocr_enabled = True
    # Make sure the max size is infinite, so no boxes are skipped in the OCR process.
    profile.preprocessor.ocr_max_size = 10**10
    # Set the OCR blacklist pattern to match everything, so all text gets reported in the analytics.
    profile.preprocessor.ocr_blacklist_pattern = ".*"

    ocr_analytics = []
    for json_file_path in tqdm(list(cache_dir.glob("*.json"))):
        ocr_analytic = pp.prep_json_file(
            json_file_path,
            preprocessor_conf=profile.preprocessor,
            cache_masks=cache_masks,
            ocr_engine_factory=ocr_processor,
            cache_masks_ocr=True,
            performing_ocr=True,
        )
        if ocr_analytic:
            ocr_analytics.append(ocr_analytic)

    handle_merging_ocr_splits(cache_dir, profile.general.merge_after_split, ocr_analytics)

    print("\nDetected Text:")
    # Output the OCRed text from the analytics.
    text_out = ocr.format_output(
        ocr_analytics,
        csv_output,
        ("filename", "startx", "starty", "endx", "endy", "text"),
    )
    text_out = text_out.strip()  # Remove the leading newline.

    print(text_out)

    if output_path is None:
        path = Path.cwd() / ("detected_text.txt" if not csv_output else "detected_text.csv")
    else:
        path = Path(output_path)

    if path.exists():
        if not cli.get_confirmation(f"File {path} already exists. Overwrite?"):
            print("Aborting.")
            return
    try:
        path.write_text(text_out, encoding="utf-8")
        print(f"Saved detected text to {path}")
    except OSError as e:
        print(f"Failed to write detected text to {path}")
        logger.exception(e)


def clear_cache(config: cfg.Config, all_cache: bool, models: bool, images: bool) -> None:
    """
    Clear the cache.

    :param config: The config to use.
    :param all_cache: Whether to clear all cache.
    :param models: Whether to clear the model cache.
    :param images: Whether to clear the image cache.
    """
    if all_cache:
        models = True
        images = True

    if models:
        model_cache_dir = config.get_model_cache_dir()
        cli.empty_cache_dir(model_cache_dir)
        print(f"Cleared model cache at {model_cache_dir}")
        # Delete the entries in the config.
        config.default_cv2_model_path = None
        config.default_torch_model_path = None
        config.save()

    if images:
        image_cache_dir = config.get_cleaner_cache_dir()
        cli.empty_cache_dir(image_cache_dir)
        print(f"Cleared image cache at {image_cache_dir}")


def split_images(image_paths: list[Path], profile: cfg.Profile, cache_dir: Path) -> None:
    # Perform image splitting, if the profile requires it.
    split_files: dict[str, list[str]] = {}
    files_to_remove = []
    files_to_add = []
    for image_path in image_paths:
        splits = ops.calculate_best_splits(
            image_path,
            profile.general.preferred_split_height,
            profile.general.split_tolerance_margin,
            profile.general.split_long_strips,
            profile.general.long_strip_aspect_ratio,
        )
        if not splits:
            # Nothing to do.
            continue
        else:
            segments = ops.split_image(image_path, splits)
            # Save these dummy files in the cache.
            splits_cache_dir = cache_dir / f"splits_{uuid4().hex}"
            splits_cache_dir.mkdir(parents=True, exist_ok=True)
            split_files[str(image_path.absolute())] = []
            for index, segment in enumerate(segments, 1):
                segment_name = f"{image_path.stem}_split_{index}{image_path.suffix}"
                segment_path = splits_cache_dir / segment_name
                segment.save(segment_path)
                split_files[str(image_path.absolute())].append(str(segment_path.absolute()))
                files_to_add.append(segment_path)
            files_to_remove.append(image_path)
    # Update the image paths.
    for file in files_to_remove:
        image_paths.remove(file)
    image_paths.extend(files_to_add)
    # We need to save the split info for the export later.
    if split_files:
        split_data_path = cache_dir / "splits.json"
        with open(split_data_path, "w") as f:
            json.dump(split_files, f)


def merge_export_splits(
    export_targets: list[ie.ExportTarget], cache_dir: Path, merge_splits: bool
) -> list[ie.ExportTarget]:
    """
    Merge the split images into temporary files for export.

    :param export_targets: The export targets to merge the splits into.
    :param cache_dir: The cache directory.
    :param merge_splits: Whether to merge the splits.
    :return: The export targets with the splits merged.
    """

    split_data_path = cache_dir / "splits.json"
    if not split_data_path.exists():
        return export_targets

    with open(split_data_path, "r") as f:
        split_files = json.load(f)

    if not merge_splits:
        # Calculate a reverse lookup for the split files.
        reverse_lookup = {}
        for original_path, split_paths in split_files.items():
            for split_path in split_paths:
                path_split_path = Path(split_path)
                # We want to graft the split name onto the original path.
                reverse_lookup[path_split_path] = Path(original_path).parent / path_split_path.name

        # We need to still repair the export paths.
        for i in range(len(export_targets)):
            export_target = export_targets[i]
            if export_target.original_path in reverse_lookup:
                new_export_target = ie.ExportTarget(
                    export_target.original_path,
                    reverse_lookup[export_target.original_path],
                    export_target.uuid,
                    export_target.outputs,
                )
                export_targets[i] = new_export_target
    else:
        # Gather the export targets that need to be merged.
        for split_file, split_path_list in split_files.items():
            split_export_targets: dict[str, ie.ExportTarget] = {}
            for export_target in export_targets:
                if str(export_target.original_path) in split_path_list:
                    split_export_targets[str(export_target.original_path)] = export_target
            # Verify we found all of them.
            if len(split_export_targets) != len(split_path_list):
                logger.error(f"Could not find all split images for {split_file}." f"Skipping.")
                continue

            # Sort the export targets by the split path list.
            export_targets_in_order = [split_export_targets[path] for path in split_path_list]

            # We need to merge the images together under a fresh UUID.
            # Add an identifying prefix so we can clean this up later.
            uuid = f"merger_{uuid4()}"

            split_file = Path(split_file)
            path_gen_master = ie.merge_cached_images(
                split_file, export_targets_in_order, cache_dir, False, uuid
            )
            merged_outputs = []
            for output in export_targets_in_order[0].outputs:
                if all(output in target.outputs for target in export_targets_in_order):
                    merged_outputs.append(output)

            # Craft a replacement export target for the merged image.
            merged_export_target = ie.ExportTarget(
                path_gen_master.original_path,
                split_file,
                uuid,
                merged_outputs,
            )

            # Remove the split images from the export targets.
            for target in export_targets_in_order:
                export_targets.remove(target)
            export_targets.append(merged_export_target)

    return export_targets


def initialize_ocr_model():
    # Pre-initialize OCR model to properly set up MPS environment
    print("Pre-initializing OCR model to set up MPS environment...")
    ocr.ocr_engines()[cfg.OCREngine.MANGAOCR].initialize_model()
    print("OCR model initialized for MPS")


def handle_merging_ocr_splits(
    cache_dir: Path,
    merge_after_split: bool,
    ocr_analytics: list[st.OCRAnalytic],
):
    """
    If merging the splits, merge them into a new image object and remove the split objects.

    :param cache_dir: The cache directory.
    :param merge_after_split: Whether to merge the OCR after splitting.
    :param ocr_analytics: The OCR analytics to merge.
    """

    split_data_path = cache_dir / "splits.json"
    if not split_data_path.exists():
        return

    with open(split_data_path, "r") as f:
        split_files = json.load(f)
    if not split_files:
        return

    if merge_after_split:
        logger.info("Merging split ocr...")

        for split_from in split_files:
            segment_paths = split_files[split_from]

            if not segment_paths:
                logger.error(f"Split file {split_from} has no split objects.")
                continue

            segment_paths = [Path(path) for path in segment_paths]
            st.merge_ocr_analytics(Path(split_from), segment_paths, ocr_analytics)


if __name__ == "__main__":
    # Freeze on windows for multiprocessing compatibility.
    if platform.system() == "Windows":
        multiprocessing.freeze_support()
    main()
