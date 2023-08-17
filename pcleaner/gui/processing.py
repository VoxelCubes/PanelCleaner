from copy import deepcopy
from functools import partial
from multiprocessing import Pool
from pathlib import Path
from typing import Callable

from logzero import logger
from manga_ocr import MangaOcr
import torch

import pcleaner.config as cfg
import pcleaner.denoiser as dn
import pcleaner.gui.ctd_interface_gui as ctm
import pcleaner.gui.image_file as imf
import pcleaner.masker as ma
import pcleaner.preprocessor as pp
import pcleaner.structures as st


def generate_output(
    image_objects: list[imf.ImageFile],
    target_outputs: list[imf.Output],
    output_dir: Path | None,
    config: cfg.Config,
    ocr_model: MangaOcr | None,
    progress_callback: imf.ProgressSignal,
    debug: bool = False,
):
    """
    Process all the images in the given image objects list until the target step is reached.
    The paths inside the image objects are updated as the processing progresses.
    If the profile checksum of a step hasn't changed, the step is skipped.

    The ocr model (or None) is passed in as arguments, so it can be reused
    across multiple runs. This is done because in gui mode the model does not need to be loaded
    repeatedly for single image runs, making iterations much faster, due to the slow
    initializations of the model taking several seconds.

    When setting the output dir to None, intermediate steps are saved to disk, offering
    additional visualizations that aren't necessary when you aren't viewing image details.

    :param image_objects: The image objects to process. These contain the image paths.
    :param target_outputs: The target outputs to reach, eg. the clean mask and image.
        Multiple outputs are only supported for those within the same step, as it's meant to accommodate
        the full run parameters.
    :param output_dir: The directory to save the outputs to. If None, the output remains in the cache directory.
    :param config: The config to use.
    :param ocr_model: The ocr model to use.
    :param progress_callback: A callback to report progress to the gui.
    :param debug: If True, debug messages are printed.
    """
    # Create an independant copy of the profile, since this instance is shared and mutated across threads.
    # Due to the checksum only being generated at the end, we don't want to erroneously claim this output
    # matches a profile that was changed in the meantime.
    profile = deepcopy(config.current_profile)

    cache_dir = config.get_cleaner_cache_dir()

    # Pick out the highest output we need to reach.
    # Other outputs are only considered if they are in the same step, used for final output runs.
    target_output = max(target_outputs)

    # Get the text detector model path from the config.
    cuda = torch.cuda.is_available()
    text_detector_model_path = config.get_model_path(cuda)

    def step_changed_clojure(process_step: imf.Step) -> Callable[[imf.ImageFile], bool]:
        """
        Check if the given step's representative output changed relative to the current profile.
        This is to see if the step needs to be rerun for an image file that this is checked with.

        :param process_step: The step to check.
        :return: A function that takes an image object and returns True if the step needs to be rerun for it.
        """

        def step_changed(image_object: imf.ImageFile) -> bool:
            nonlocal profile
            nonlocal process_step

            return image_object.outputs[imf.get_output_representing_step(process_step)].is_changed(
                profile
            )

        return step_changed

    def update_output(image_object: imf.ImageFile, output: imf.Output, suffix: str):
        """
        Update the output of the given image object.
        Check if the file actually exists, and if it does, update the output path.

        :param image_object: The image object to update.
        :param output: The output to update.
        :param suffix: The suffix to add to the output path.
        """
        nonlocal profile, cache_dir

        path = cache_dir / f"{image_object.uuid}_{image_object.path.stem}{suffix}"

        if path.is_file():
            image_object.outputs[output].update(path, profile)

    # ============================================== Text Detection ==============================================

    step_text_detector_images = list(
        filter(step_changed_clojure(imf.Step.text_detection), image_objects)
    )

    if step_text_detector_images:
        logger.info(
            f"Running text detection AI model for {len(step_text_detector_images)} images..."
        )
        ctm.model2annotations_gui(
            profile.general,
            profile.text_detector,
            text_detector_model_path,
            step_text_detector_images,
            cache_dir,
            no_text_detection=target_output == imf.Output.input,
            partial_progress_data=partial(
                imf.ProgressData,
                len(step_text_detector_images),
                target_output,
                imf.Step.text_detection,
            ),
            progress_callback=progress_callback,
        )

        # Update the outputs of the image objects.
        logger.debug(f"Updating text detection outputs...")
        for image_obj in step_text_detector_images:
            update_output(image_obj, imf.Output.input, ".png")
            update_output(image_obj, imf.Output.ai_mask, "_mask.png")

        progress_callback.emit(
            imf.ProgressData(
                len(step_text_detector_images),
                target_output,
                imf.Step.text_detection,
                imf.ProgressType.end,
            )
        )

    # ============================================== Preprocessing ==============================================

    if target_output > imf.get_output_representing_step(imf.Step.text_detection):
        step_preprocessor_images = list(
            filter(step_changed_clojure(imf.Step.preprocessor), image_objects)
        )

        if step_preprocessor_images:
            logger.info(f"Running preprocessing for {len(step_preprocessor_images)} images...")

            ocr_analytics = []

            progress_callback.emit(
                imf.ProgressData(
                    len(step_preprocessor_images),
                    target_output,
                    imf.Step.preprocessor,
                    imf.ProgressType.begin,
                )
            )

            # Find all the json files associated with the images.
            for image_obj in step_preprocessor_images:
                json_file_path = cache_dir / f"{image_obj.uuid}_{image_obj.path.stem}#raw.json"
                ocr_analytic = pp.prep_json_file(
                    json_file_path,
                    preprocessor_conf=profile.preprocessor,
                    cache_masks=target_output in imf.step_to_output[imf.Step.preprocessor]
                    or output_dir is None,
                    mocr=ocr_model if profile.preprocessor.ocr_enabled else None,
                )

                progress_callback.emit(
                    imf.ProgressData(
                        len(step_preprocessor_images),
                        target_output,
                        imf.Step.preprocessor,
                        imf.ProgressType.incremental,
                    )
                )

                if ocr_analytic:
                    ocr_analytics.append(ocr_analytic)

            # Update the outputs of the image objects.
            logger.debug(f"Updating preprocessing outputs...")
            for image_obj in step_preprocessor_images:
                update_output(image_obj, imf.Output.initial_boxes, "_boxes.png")
                update_output(image_obj, imf.Output.final_boxes, "_boxes_final.png")

            progress_callback.emit(
                imf.ProgressData(
                    len(step_preprocessor_images),
                    target_output,
                    imf.Step.preprocessor,
                    imf.ProgressType.end,
                    (ocr_analytics, profile.preprocessor.ocr_max_size),
                )
            )

    # ============================================== Masker ==============================================

    if target_output > imf.get_output_representing_step(imf.Step.preprocessor):
        step_masker_images = list(filter(step_changed_clojure(imf.Step.masker), image_objects))

        if step_masker_images:
            logger.info(f"Running masker for {len(step_masker_images)} images...")

            progress_callback.emit(
                imf.ProgressData(
                    len(step_masker_images),
                    target_output,
                    imf.Step.masker,
                    imf.ProgressType.begin,
                )
            )

            # Find all the json files associated with the images.
            json_files = (
                cache_dir / f"{image_obj.uuid}_{image_obj.path.stem}#clean.json"
                for image_obj in step_masker_images
            )

            # When denoising, we don't immediately output the cleaned image.
            # But when not, we do, since denoising is optional.
            if target_output in imf.step_to_output[imf.Step.denoiser]:
                masker_output_dir = None
            else:
                masker_output_dir = output_dir

            # Pack all the arguments into a dataclass.
            outputs_that_need_masks = (
                imf.Output.box_mask,
                imf.Output.cut_mask,
                imf.Output.mask_layers,
                imf.Output.mask_overlay,
            )
            # If any of out targeted outputs need to have intermediate masks generated,
            # we need to show the masks. Or if we explicitly want to show the masks.
            need_to_show_masks = output_dir is None or any(
                output in outputs_that_need_masks for output in target_outputs
            )

            data = [
                st.MaskerData(
                    json_file,
                    masker_output_dir,
                    cache_dir,
                    profile.general,
                    profile.masker,
                    save_only_mask=target_outputs == [imf.Output.final_mask],
                    save_only_cleaned=target_outputs == [imf.Output.masked_image],
                    save_only_text=target_outputs == [imf.Output.isolated_text],
                    extract_text=imf.Output.isolated_text in target_outputs,
                    show_masks=need_to_show_masks,
                    debug=debug,
                )
                for json_file in json_files
            ]

            masker_analytics_raw = []
            with Pool() as pool:
                for analytic in pool.imap(ma.clean_page, data):
                    masker_analytics_raw.extend(analytic)

                    progress_callback.emit(
                        imf.ProgressData(
                            len(step_masker_images),
                            target_output,
                            imf.Step.masker,
                            imf.ProgressType.incremental,
                        )
                    )

            # Update the outputs of the image objects.
            logger.debug(f"Updating masker outputs...")
            for image_obj in step_masker_images:
                update_output(image_obj, imf.Output.box_mask, "_box_mask.png")
                update_output(image_obj, imf.Output.cut_mask, "_cut_mask.png")
                update_output(image_obj, imf.Output.mask_layers, "_masks.png")
                update_output(image_obj, imf.Output.final_mask, "_combined_mask.png")
                update_output(image_obj, imf.Output.mask_overlay, "_with_masks.png")
                update_output(image_obj, imf.Output.isolated_text, "_text.png")
                update_output(image_obj, imf.Output.masked_image, "_clean.png")

            progress_callback.emit(
                imf.ProgressData(
                    len(step_masker_images),
                    target_output,
                    imf.Step.masker,
                    imf.ProgressType.end,
                    masker_analytics_raw,
                )
            )

    # ============================================== Denoiser ==============================================

    if target_output > imf.get_output_representing_step(imf.Step.masker):
        step_denoiser_images = list(filter(step_changed_clojure(imf.Step.denoiser), image_objects))

        if step_denoiser_images:
            logger.info(f"Running denoiser for {len(step_denoiser_images)} images...")

            progress_callback.emit(
                imf.ProgressData(
                    len(step_denoiser_images),
                    target_output,
                    imf.Step.denoiser,
                    imf.ProgressType.begin,
                )
            )

            # Find all the json files associated with the images.
            json_files = (
                cache_dir / f"{image_obj.uuid}_{image_obj.path.stem}#mask_data.json"
                for image_obj in step_denoiser_images
            )

            # Pack all the arguments into a dataclass.
            data = [
                st.DenoiserData(
                    json_file,
                    output_dir,
                    cache_dir,
                    profile.general,
                    profile.denoiser,
                    save_only_mask=target_outputs == [imf.Output.denoiser_mask],
                    save_only_cleaned=target_outputs == [imf.Output.denoised_image],
                    extract_text=imf.Output.isolated_denoised_text in target_outputs,
                    separate_noise_masks=False,
                    show_masks=output_dir is None,
                    debug=debug,
                )
                for json_file in json_files
            ]

            denoise_analytics_raw = []
            with Pool() as pool:
                for analytic in pool.imap(dn.denoise_page, data):
                    denoise_analytics_raw.append(analytic)

                    progress_callback.emit(
                        imf.ProgressData(
                            len(step_denoiser_images),
                            target_output,
                            imf.Step.denoiser,
                            imf.ProgressType.incremental,
                        )
                    )

            # Update the outputs of the image objects.
            logger.debug(f"Updating denoising outputs...")
            for image_obj in step_denoiser_images:
                update_output(image_obj, imf.Output.denoiser_mask, "_noise_mask.png")
                update_output(image_obj, imf.Output.denoised_image, "_clean_denoised.png")
                update_output(image_obj, imf.Output.isolated_denoised_text, "_text.png")

            progress_callback.emit(
                imf.ProgressData(
                    len(step_denoiser_images),
                    target_output,
                    imf.Step.denoiser,
                    imf.ProgressType.end,
                    (
                        denoise_analytics_raw,
                        profile.denoiser.noise_min_standard_deviation,
                        profile.masker.mask_max_standard_deviation,
                    ),
                )
            )

    logger.info("Done!")
