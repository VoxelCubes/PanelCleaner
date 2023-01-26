"""Panel Cleaner

Usage:
    pcleaner clean [<image_path> ...] [--output_dir=<output_dir>] [--profile=<profile>] [--keep-cache]
        [--save-only-mask | --save-only-cleaned] [--cache-masks] [--separate-noise-mask] [--hide-analytics]
        [--skip-text-detection] [--skip-pre-processing] [--skip-cleaning] [--skip-denoising] [--debug]
    pcleaner profile (list | new <profile_name> [<profile_path>] | add <profile_name> <profile_path> |
        open <profile_name> | delete <profile_name> | set-default <profile_name> | repair <profile_name> |
        purge-missing) [--debug]
    pcleaner ocr [<image_path> ...] [--output-path=<output_path>] [--debug]
    pcleaner config (show | open)
    pcleaner cache clear (all | models | cleaner)
    pcleaner load model [--cuda | --cpu | --both] [--force]
    pcleaner --help
    pcleaner --version

Subcommands:
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
    ocr              Run only the OCR on the given image(s). Any number of images and directories can be given.
                     The output will be saved in a single text file for the whole batch.
    config           View or edit the config file. This stores setting independent of profiles.
        show         Show the current configuration. This doesn't show the current profile.
        open         Open the config file in the default editor (unless specified in the config).
    cache clear      Clear the cache. This is where the program stores downloaded models and other files.
        all          Clear all cache files.
        models       Clear only the models.
        cleaner      Clear only the temporary masks and debug data.
    load models      Download the models used by the program. If neither --cuda nor --cpu is specified, the program will
                     try to use CUDA if available. If it is not, it will fall back to CPU.
                     This is done automatically when needed, but can be done manually.


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
    -n --separate-noise-mask        Save the noise mask separately from the main mask.
    -T --skip-text-detection        Do not run the text detection AI model. This is step 1/4.
    -P --skip-pre-processing        Do not run data pre-processing. This is step 2/4.
    -C --skip-cleaning              Do not run the cleaning process. This is step 3/4.
    -D --skip-denoising             Do not run the denoising process. This an optional step 4/4.
    -s --cache-masks                Save the masks used to clean the image in the cache directory.
    -a --hide-analytics             Hide the analytics. These are the statistics about the
                                    cleaning accuracy.
    <profile_path>                  The path to the profile file to add.
    <profile_name>                  The saved name of the profile to open, delete, or set as default.
    --output-path=<output_path>     The path to save the OCR output file to.
    --cuda                          Load the torch models that support CUDA. They will only be used if supported.
    --cpu                           Load the open cv2 models that are optimized for CPU.
                                    They will only be used as a fallback, unless specified in the config.
    --both                          Load both the torch and open cv2 models.
    --force                         Force the models to be downloaded, even if they already exist.
    -d --debug                      Show debug information.
    -v --version                    Show the version and exit.
    -h --help                       Show this screen.

Examples:
    pcleaner myfolder               This will clean all images in the folder, saving the output to
                                    a folder inside myfolder called cleaned.

    pcleaner myfolder -o myoutput   This will clean all images in the folder, saving the output to
                                    a folder called myoutput, placed inside myfolder.

    pcleaner myfolder myfolder2 mypng myjpg  This will clean all images in the folders and all given files,
                                    saving the outputs to folders called cleaned, placed inside of these folders
                                    or in the parent directory of the input files, respectively.

    pcleaner myfolder -p myprofile  This will clean all the images, but use the settings from the profile
                                    called myprofile.

    pcleaner myfolder -p myprofile2 -TP  This will skip the text detection and pre-processing steps,
                                    but still run the cleaning process using the settings from the profile
                                    called myprofile2. This can be useful when you tweaked settings only
                                    related to the cleaning process. You can save time skipping the first one
                                    or two steps, since the results are saved in the cache directory (unless
                                    you choose to delete them).

"""


import time
from multiprocessing import Pool
from pathlib import Path
import itertools

from manga_ocr import MangaOcr
from docopt import magic_docopt
from logzero import logger, loglevel, DEBUG, INFO
from tqdm import tqdm
from natsort import natsorted
import torch

from pcleaner import __version__
import pcleaner.cleaner as cl
import pcleaner.config as cfg
import pcleaner.cli_utils as cli
import pcleaner.pre_processor as pp
import pcleaner.analytics as an
import pcleaner.structures as st
import pcleaner.profile_cli as pc
import pcleaner.denoiser as dn
import pcleaner.model_downloader as md


def main():

    args = magic_docopt(__doc__, version=f"Panel Cleaner {__version__}")
    # Loglevel is info by default.
    if args.debug:
        loglevel(DEBUG)
    else:
        loglevel(INFO)

    logger.debug(args)

    if args.profile:
        # Handle profile subcommands.
        config = cfg.load_config()

        if args.list:
            pc.list_profiles(config)
        elif args.new:
            pc.new_profile(config, args.profile_name, args.profile_path)
        elif args.add:
            pc.add_profile(config, args.profile_name, args.profile_path)
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
        run_ocr(config, args.image_path, args.output_path)

    elif args.cache and args.clear:
        config = cfg.load_config()
        clear_cache(config, args.all, args.models, args.cleaner)

    elif args.load and args.model:
        config = cfg.load_config()
        md.download_models(config, args.force, args.cuda or args.both, args.cpu or args.both)

    elif args.config:
        # Handle config subcommand.
        config = cfg.load_config()

        if args.show:
            config.show()
        elif args.open:
            cli.open_file_with_editor(cli.get_config_path(), config.profile_editor)
    else:
        # Do the actual work.
        config = cfg.load_config()
        config.load_profile(args["--profile"])
        logger.debug(config)

        if args.output_dir is None:
            args.output_dir = Path("cleaned")
            args.relative_output = True
        else:
            args.output_dir = Path(args.output_dir)

        # start timer.
        start = time.time()
        run_cleaner(
            image_paths=args.image_path,
            output_dir=args.output_dir,
            config=config,
            skip_text_detection=args.skip_text_detection,
            skip_pre_processing=args.skip_pre_processing,
            skip_cleaning=args.skip_cleaning,
            skip_denoising=args.skip_denoising,
            save_only_mask=args.save_only_mask,
            save_only_cleaned=args.save_only_cleaned,
            cache_masks=args.cache_masks,
            separate_noise_mask=args.separate_noise_mask,
            hide_analytics=args.hide_analytics,
            keep_cache=args.keep_cache,
            debug=args.debug,
        )
        # end timer.
        end = time.time()
        print(f"\nTime elapsed: {end - start:.2f} seconds")


def run_cleaner(
    image_paths: list[Path],
    output_dir: Path,
    config: cfg.Config,
    skip_text_detection: bool,
    skip_pre_processing: bool,
    skip_cleaning: bool,
    skip_denoising: bool,
    save_only_mask: bool,
    save_only_cleaned: bool,
    cache_masks: bool,
    separate_noise_mask: bool,
    hide_analytics: bool,
    keep_cache: bool,
    debug: bool,
):
    """
    Run the cleaner on the given images.

    :param image_paths: The paths to the images to clean.
    :param output_dir: The directory to save the output files to.
    :param config: The config to use.
    :param skip_text_detection: Whether to skip the text detection step.
    :param skip_pre_processing: Whether to skip the pre-processing step.
    :param skip_cleaning: Whether to skip the cleaning step.
    :param skip_denoising: Whether to skip the denoising step.
    :param save_only_mask: Whether to save only the mask.
    :param save_only_cleaned: Whether to save only the cleaned image.
    :param cache_masks: Whether to save the masks used to clean the image in the cache directory.
    :param separate_noise_mask: Whether to save the noise mask separately.
    :param hide_analytics: Whether to hide the analytics.
    :param keep_cache: Whether to keep the cache directory for the text detection step.
    :param debug: Whether to show debug information.
    """
    profile = config.current_profile

    # Catch jokesters who want to skip all 4 steps.
    if skip_text_detection and skip_pre_processing and skip_cleaning and skip_denoising:
        print("Well how about that, you want to skip all 4 steps? I guess I'm not needed here.")
        return

    cache_dir = config.get_cleaner_cache_dir()
    logger.debug(f"Cache directory: {cache_dir}")

    # If caching masks, direct the user to the cache directory.
    if cache_masks:
        print(
            f"You can find the masks being generated in real-time in the cache directory:\n\n{cache_dir}\n"
        )

    if not skip_text_detection:
        # Delete the cache directory if not explicitly keeping it.
        if len(list(cache_dir.glob("*"))) > 0 and not keep_cache:
            cli.empty_cache_dir(cache_dir)
        # Get the model file, downloading it if necessary.
        cuda = torch.cuda.is_available()
        model_path = config.get_model_path(cuda)

        print("Running text detection AI model...")
        pp.generate_mask_data(image_paths, model_path=model_path, output_dir=cache_dir)

        # Leave some extra space here if drawing analytics, so it looks better.
        if not hide_analytics:
            print("\n")

    if not skip_pre_processing:
        # Flush it so it shows up before the progress bar.
        print("Running box data Pre-Processor...", flush=True)
        # Make sure it actually flushes at all costs = wait 100 ms.
        # (It takes several seconds to load the ocr model, so this is fine.)
        time.sleep(0.1)
        if profile.pre_processor.ocr_enabled:
            mocr = MangaOcr()
        else:
            mocr = None

        ocr_analytics = []
        for json_file_path in tqdm(list(cache_dir.glob("*.json"))):
            ocr_analytic = pp.prep_json_file(
                json_file_path,
                pre_processor_conf=profile.pre_processor,
                cache_masks=cache_masks,
                mocr=mocr,
            )
            if ocr_analytic:
                ocr_analytics.append(ocr_analytic)

        if ocr_analytics and not hide_analytics:
            an.show_ocr_analytics(ocr_analytics, profile.pre_processor.ocr_max_size)

    if not skip_cleaning:
        print("Running Cleaner...")
        # Read the json files in the image directory.
        json_files = Path(cache_dir).glob("*_clean.json")

        # When denoising, we don't immediately output the cleaned image.
        # But when not, we do, since denoising is optional.
        if not skip_denoising:
            cleaner_output_dir = None
        else:
            cleaner_output_dir = output_dir

        # Zip together the json files and the out path thing.
        data = [
            st.CleanerData(
                json_file,
                cleaner_output_dir,
                cache_dir,
                profile.cleaner,
                save_only_mask,
                save_only_cleaned,
                cache_masks,
                debug,
            )
            for json_file in json_files
        ]

        cleaner_analytics_raw = []
        with Pool() as pool:
            for analytic in tqdm(pool.imap(cl.clean_page, data), total=len(data)):
                cleaner_analytics_raw.extend(analytic)

        if not hide_analytics and cleaner_analytics_raw:
            an.show_cleaner_analytics(cleaner_analytics_raw)

    if not skip_denoising:
        print("Running Denoiser...")
        # Read the json files in the image directory.
        json_files = Path(cache_dir).glob("*_mask_data.json")

        # Zip together the json files and the out path thing.
        data = [
            st.DenoiserData(
                json_file,
                output_dir,
                cache_dir,
                profile.denoiser,
                save_only_mask,
                save_only_cleaned,
                separate_noise_mask,
                cache_masks,
                debug,
            )
            for json_file in json_files
        ]

        denoise_analytics_raw = []
        with Pool() as pool:
            for analytic in tqdm(pool.imap(dn.denoise_page, data), total=len(data)):
                denoise_analytics_raw.append(analytic)

        if not hide_analytics and denoise_analytics_raw:
            an.show_denoise_analytics(
                denoise_analytics_raw,
                profile.denoiser.noise_min_standard_deviation,
                profile.cleaner.mask_max_standard_deviation,
            )

        print("Done!")


def run_ocr(config: cfg.Config, image_paths: list[Path], output_path: str | None):
    """
    Run OCR on the given images. This is a byproduct of the pre-processing step,
    expanded to all bubbles.

    :param config: The config to use.
    :param image_paths: The images to run OCR on.
    :param output_path: The path to output the results to.
    """
    cache_dir = config.get_cleaner_cache_dir()
    logger.debug(f"Cache directory: {cache_dir}")

    # Delete the cache directory if not explicitly keeping it.
    if len(list(cache_dir.glob("*"))) > 0:
        cli.empty_cache_dir(cache_dir)
    # Get the model file, downloading it if necessary.
    cuda = torch.cuda.is_available()
    model_path = config.get_model_path(cuda)

    print("Running text detection AI model...")
    pp.generate_mask_data(image_paths, model_path=model_path, output_dir=cache_dir)

    print("\n")

    # Flush it so it shows up before the progress bar.
    print("Running box data Pre-Processor...", flush=True)
    # Make sure it actually flushes at all costs = wait 100 ms.
    # (It takes several seconds to load the ocr model, so this is fine.)
    time.sleep(0.1)

    # Modify the profile to OCR all boxes.
    # Make sure OCR is enabled.
    config.current_profile.pre_processor.ocr_enabled = True
    # Make sure the max size is infinite, so no boxes are skipped in the OCR process.
    config.current_profile.pre_processor.ocr_max_size = float("inf")
    # Make sure the sus box min size is infinite, so all boxes with "unknown" language are skipped.
    config.current_profile.pre_processor.suspicious_box_min_size = float("inf")
    # Set the OCR blacklist pattern to match everything, so all text gets reported in the analytics.
    config.current_profile.pre_processor.ocr_blacklist_pattern = ".*"

    mocr = MangaOcr()
    ocr_analytics = []
    for json_file_path in tqdm(list(cache_dir.glob("*.json"))):
        ocr_analytic = pp.prep_json_file(
            json_file_path,
            pre_processor_conf=config.current_profile.pre_processor,
            cache_masks=False,
            mocr=mocr,
        )
        if ocr_analytic:
            ocr_analytics.append(ocr_analytic)

    # Output the OCRed text from the analytics.
    removed_texts = list(itertools.chain.from_iterable(a[3] for a in ocr_analytics))

    # Find and then remove the longest common prefix from the file paths.
    prefix = an.longest_common_prefix([str(Path(path).parent) for path, _ in removed_texts])
    if prefix:
        removed_texts = [(path[len(prefix) :], text) for path, text in removed_texts]
    # Remove a rogue / or \ from the start of the path, if they all have one.
    if all(path.startswith("/") or path.startswith("\\") for path, _ in removed_texts):
        removed_texts = [(path[1:], text) for path, text in removed_texts]

    removed_texts = natsorted(removed_texts, key=lambda x: x[0])

    print("\nDetected Text:")
    text = "\n".join(f"{path}: {text}" for path, text in removed_texts)
    print(text)

    if output_path is None:
        path = Path.cwd() / "detected_text.txt"
    else:
        path = Path(output_path)

    if path.exists():
        if not cli.get_confirmation(f"File {path} already exists. Overwrite?"):
            print("Aborting.")
            return
    try:
        path.write_text(text, encoding="utf-8")
        print(f"Saved detected text to {path}")
    except OSError as e:
        print(f"Failed to write detected text to {path}")
        logger.exception(e)


def clear_cache(config: cfg.Config, all_cache: bool, models: bool, images: bool):
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


if __name__ == "__main__":
    main()
