import itertools
import csv
from copy import deepcopy, copy
from functools import partial
from io import StringIO
from multiprocessing import Pool
from pathlib import Path
from typing import Callable

import torch
from PIL import Image
from loguru import logger
from natsort import natsorted

import pcleaner.config as cfg
import pcleaner.denoiser as dn
import pcleaner.gui.ctd_interface_gui as ctm
import pcleaner.gui.image_file as imf
import pcleaner.gui.worker_thread as wt
import pcleaner.helpers as hp
import pcleaner.image_ops as ops
import pcleaner.masker as ma
import pcleaner.preprocessor as pp
import pcleaner.inpainting as ip
import pcleaner.structures as st
import pcleaner.gui.gui_utils as gu
from pcleaner.helpers import tr
from pcleaner import model_downloader as md
import pcleaner.ocr.ocr as ocr


def generate_output(
    image_objects: list[imf.ImageFile],
    target_outputs: list[imf.Output],
    output_dir: Path | None,
    config: cfg.Config,
    ocr_processor: ocr.OcrProcsType | None,
    progress_callback: imf.ProgressSignal,
    abort_flag: wt.SharableFlag,
    debug: bool = False,
):
    """
    Process all the images in the given image objects list until the target step is reached.
    The paths inside the image objects are updated as the processing progresses.
    If the profile checksum of a step hasn't changed, the step is skipped.

    In GUI mode, the masker and denoiser never write the output directly, but instead
    place them in the cache directory. From there they may be copied to the output directory,
    to ensure that effort isn't duplicated where possible. For example, if the output was already
    generated for the viewer, it doesn't need to be generated again for the final output, or when
    only changing the output path for the final output.

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
    :param ocr_processor: The ocr models to use.
    :param progress_callback: A callback to report progress to the gui.
    :param abort_flag: A flag that is set to True when the thread should abort.
    :param debug: If True, debug messages are printed.
    """

    # We will check before each step and during each iteration of the step to see if the thread should abort.
    # The check is NOT done right before checking the outputs to avoid throwing away perfectly fine work.
    # This means that the abort check shouldn't interrupt the processing step on an image, leaving it in a
    # dirty state.
    def check_abortion() -> None:
        """
        Check if the thread should abort.
        If so, signal abortion to the progress callback and raise an AbortException.
        """
        if abort_flag.get():
            progress_callback.emit(
                imf.ProgressData(
                    0,
                    [],
                    imf.Step.output,
                    imf.ProgressType.aborted,
                )
            )
            raise wt.Abort()

    progress_callback.emit(
        imf.ProgressData(
            0,
            [],
            imf.Step.text_detection,
            imf.ProgressType.start,
        )
    )

    # Create an independent copy of the profile, since this instance is shared and mutated across threads.
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

    def step_needs_to_be_rerun_closure(current_step: imf.Step) -> Callable[[imf.ImageFile], bool]:
        """
        Check if any of the outputs for the given image object need to be rerun.

        :return: A function that takes an image object and returns True if the step needs to be rerun for it.
        """

        def step_changed(image_object: imf.ImageFile) -> bool:
            nonlocal profile
            nonlocal target_outputs
            nonlocal current_step
            # holy shit this is cursed I need to think about it more.
            # I think I got it sorted now...
            # Pretty sure it works :)
            # It didn't.
            # Now it is fr fr

            target_outputs_in_the_current_step: tuple[imf.Output] = tuple(
                filter(lambda o: o in imf.step_to_output[current_step], reversed(target_outputs))
            )

            if target_outputs_in_the_current_step:
                # We need to check each output we care about to know if we gotta rerun the step.
                return any(
                    image_object.outputs[o].is_changed(profile)
                    for o in target_outputs_in_the_current_step
                )
            else:
                # In this case we just need to know if the step's representative is complete.
                representative: imf.Output = imf.get_output_representing_step(current_step)
                return image_object.outputs[representative].is_changed(profile)

        return step_changed

    def update_output(image_object: imf.ImageFile, output: imf.Output, suffix: str) -> None:
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

    check_abortion()

    step_text_detector_images = tuple(
        filter(step_needs_to_be_rerun_closure(imf.Step.text_detection), image_objects)
    )

    if step_text_detector_images:
        logger.info(
            f"Running text detection AI model for {len(step_text_detector_images)} images..."
        )
        try:
            ctm.model2annotations_gui(
                profile.general,
                profile.text_detector,
                text_detector_model_path,
                step_text_detector_images,
                cache_dir,
                no_text_detection=target_output == imf.Output.input,
                visualize_raw_boxes=True,
                partial_progress_data=partial(
                    imf.ProgressData,
                    len(step_text_detector_images),
                    target_outputs,
                    imf.Step.text_detection,
                ),
                progress_callback=progress_callback if target_output != imf.Output.input else None,
                abort_flag=abort_flag,
            )
        except wt.Abort:
            # Send the progress callback a signal that the process was aborted,
            # and then raise the exception again to stop the processing.
            check_abortion()

        # Update the outputs of the image objects.
        for image_obj in step_text_detector_images:
            update_output(image_obj, imf.Output.input, ".png")
            update_output(image_obj, imf.Output.ai_mask, "_mask.png")
            update_output(image_obj, imf.Output.raw_boxes, "_raw_boxes.png")
            update_output(image_obj, imf.Output.raw_json, "#raw.json")

        progress_callback.emit(
            imf.ProgressData(
                len(step_text_detector_images),
                target_outputs,
                imf.Step.text_detection,
                imf.ProgressType.textDetection_done,
            )
        )

    # ============================================== Preprocessing ==============================================

    check_abortion()

    if target_output > imf.get_output_representing_step(imf.Step.text_detection):
        step_preprocessor_images = tuple(
            filter(step_needs_to_be_rerun_closure(imf.Step.preprocessor), image_objects)
        )

        if step_preprocessor_images:
            logger.info(f"Running preprocessing for {len(step_preprocessor_images)} images...")

            progress_callback.emit(
                imf.ProgressData(
                    len(step_preprocessor_images),
                    target_outputs,
                    imf.Step.preprocessor,
                    imf.ProgressType.begin_step,
                )
            )

            ocr_analytics: list[st.OCRAnalytic] = []
            # Find all the json files associated with the images.
            for image_obj in step_preprocessor_images:
                check_abortion()
                json_file_path = cache_dir / f"{image_obj.uuid}_{image_obj.path.stem}#raw.json"
                ocr_analytic = pp.prep_json_file(
                    json_file_path,
                    preprocessor_conf=profile.preprocessor,
                    cache_masks=target_output in imf.step_to_output[imf.Step.preprocessor]
                    or output_dir is None,
                    mocr=ocr_processor if profile.preprocessor.ocr_enabled else None,
                )

                if ocr_analytic is not None:
                    ocr_analytics.append(ocr_analytic)

                progress_callback.emit(
                    imf.ProgressData(
                        len(step_preprocessor_images),
                        target_outputs,
                        imf.Step.preprocessor,
                        imf.ProgressType.incremental,
                    )
                )

            # Update the outputs of the image objects.
            for image_obj in step_preprocessor_images:
                update_output(image_obj, imf.Output.initial_boxes, "_boxes.png")
                update_output(image_obj, imf.Output.final_boxes, "_boxes_final.png")
                update_output(image_obj, imf.Output.clean_json, "#clean.json")

            progress_callback.emit(
                imf.ProgressData(
                    len(step_preprocessor_images),
                    target_outputs,
                    imf.Step.preprocessor,
                    imf.ProgressType.analyticsOCR,
                    (ocr_analytics, profile.preprocessor.ocr_max_size),
                )
            )

    # ============================================== Masker ==============================================

    check_abortion()

    if target_output > imf.get_output_representing_step(imf.Step.preprocessor):
        step_masker_images = tuple(
            filter(step_needs_to_be_rerun_closure(imf.Step.masker), image_objects)
        )

        if step_masker_images:
            logger.info(f"Running masker for {len(step_masker_images)} images...")

            progress_callback.emit(
                imf.ProgressData(
                    len(step_masker_images),
                    target_outputs,
                    imf.Step.masker,
                    imf.ProgressType.begin_step,
                )
            )

            # Find all the json files associated with the images.
            json_files = (
                cache_dir / f"{image_obj.uuid}_{image_obj.path.stem}#clean.json"
                for image_obj in step_masker_images
            )

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
                    None,
                    cache_dir,
                    profile.general,
                    profile.masker,
                    save_only_mask=target_outputs == [imf.Output.final_mask],
                    save_only_cleaned=target_outputs == [imf.Output.masked_output],
                    save_only_text=target_outputs == [imf.Output.isolated_text],
                    extract_text=imf.Output.isolated_text in target_outputs,
                    show_masks=need_to_show_masks,
                    debug=debug,
                )
                for json_file in json_files
            ]

            masker_analytics_raw = []

            if len(step_masker_images) > 2:
                # Only use multiprocessing if there are more than 2 images.
                with Pool() as pool:
                    for analytic in pool.imap(ma.clean_page, data):
                        check_abortion()
                        masker_analytics_raw.extend(analytic)

                        progress_callback.emit(
                            imf.ProgressData(
                                len(step_masker_images),
                                target_outputs,
                                imf.Step.masker,
                                imf.ProgressType.incremental,
                            )
                        )
            else:
                for data_obj in data:
                    check_abortion()
                    analytic = ma.clean_page(data_obj)
                    masker_analytics_raw.extend(analytic)

                    progress_callback.emit(
                        imf.ProgressData(
                            len(step_masker_images),
                            target_outputs,
                            imf.Step.masker,
                            imf.ProgressType.incremental,
                        )
                    )

            # Update the outputs of the image objects.
            for image_obj in step_masker_images:
                update_output(image_obj, imf.Output.box_mask, "_box_mask.png")
                update_output(image_obj, imf.Output.cut_mask, "_cut_mask.png")
                update_output(image_obj, imf.Output.mask_layers, "_masks.png")
                update_output(image_obj, imf.Output.final_mask, "_combined_mask.png")
                update_output(image_obj, imf.Output.mask_overlay, "_with_masks.png")
                update_output(image_obj, imf.Output.fitment_quality, "_std_devs.png")
                update_output(image_obj, imf.Output.isolated_text, "_text.png")
                update_output(image_obj, imf.Output.masked_output, "_clean.png")
                update_output(image_obj, imf.Output.mask_data_json, "#mask_data.json")

            progress_callback.emit(
                imf.ProgressData(
                    len(step_masker_images),
                    target_outputs,
                    imf.Step.masker,
                    imf.ProgressType.analyticsMasker,
                    (masker_analytics_raw, copy(profile.masker)),  # Make a copy to avoid a mutex.
                )
            )

    # ============================================== Denoiser ==============================================

    check_abortion()

    if (
        target_output > imf.get_output_representing_step(imf.Step.masker)
        and profile.denoiser.denoising_enabled
    ):
        step_denoiser_images = tuple(
            filter(step_needs_to_be_rerun_closure(imf.Step.denoiser), image_objects)
        )

        if step_denoiser_images:
            logger.info(f"Running denoiser for {len(step_denoiser_images)} images...")

            progress_callback.emit(
                imf.ProgressData(
                    len(step_denoiser_images),
                    target_outputs,
                    imf.Step.denoiser,
                    imf.ProgressType.begin_step,
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
                    None,
                    cache_dir,
                    profile.general,
                    profile.denoiser,
                    profile.inpainter,
                    save_only_mask=target_outputs == [imf.Output.denoise_mask],
                    save_only_cleaned=target_outputs == [imf.Output.denoised_output],
                    extract_text=imf.Output.isolated_text in target_outputs,
                    separate_noise_masks=False,
                    show_masks=True,
                    debug=debug,
                )
                for json_file in json_files
            ]

            denoise_analytics_raw = []
            if len(step_denoiser_images) > 2:
                with Pool() as pool:
                    for analytic in pool.imap(dn.denoise_page, data):
                        check_abortion()
                        denoise_analytics_raw.append(analytic)

                        progress_callback.emit(
                            imf.ProgressData(
                                len(step_denoiser_images),
                                target_outputs,
                                imf.Step.denoiser,
                                imf.ProgressType.incremental,
                            )
                        )
            else:
                for data_obj in data:
                    check_abortion()
                    analytic = dn.denoise_page(data_obj)
                    denoise_analytics_raw.append(analytic)

                    progress_callback.emit(
                        imf.ProgressData(
                            len(step_denoiser_images),
                            target_outputs,
                            imf.Step.denoiser,
                            imf.ProgressType.incremental,
                        )
                    )

            # Update the outputs of the image objects.
            for image_obj in step_denoiser_images:
                update_output(image_obj, imf.Output.denoise_mask, "_noise_mask.png")
                update_output(image_obj, imf.Output.denoised_output, "_clean_denoised.png")
                update_output(image_obj, imf.Output.isolated_text, "_text.png")

            progress_callback.emit(
                imf.ProgressData(
                    len(step_denoiser_images),
                    target_outputs,
                    imf.Step.denoiser,
                    imf.ProgressType.analyticsDenoiser,
                    (
                        denoise_analytics_raw,
                        profile.denoiser.noise_min_standard_deviation,
                        profile.masker.mask_max_standard_deviation,
                    ),
                )
            )

    # ============================================== Inpainting ==============================================

    check_abortion()

    if (
        target_output > imf.get_output_representing_step(imf.Step.denoiser)
        and profile.inpainter.inpainting_enabled
    ):
        step_inpainting_images = tuple(
            filter(step_needs_to_be_rerun_closure(imf.Step.inpainter), image_objects)
        )

        if step_inpainting_images:
            logger.info(f"Running inpainting for {len(step_inpainting_images)} images...")

            progress_callback.emit(
                imf.ProgressData(
                    len(step_inpainting_images),
                    target_outputs,
                    imf.Step.inpainter,
                    imf.ProgressType.begin_step,
                )
            )

            # Find all the json files associated with the images.
            mask_json_files = list(
                cache_dir / f"{image_obj.uuid}_{image_obj.path.stem}#mask_data.json"
                for image_obj in step_inpainting_images
            )
            page_json_files = list(
                cache_dir / f"{image_obj.uuid}_{image_obj.path.stem}#clean.json"
                for image_obj in step_inpainting_images
            )
            # Zip together the matching json files.
            zipped_jsons = []
            for page_json_file in page_json_files:
                for mask_json_file in mask_json_files:
                    if mask_json_file.name.startswith(page_json_file.name.split("#")[0]):
                        zipped_jsons.append((page_json_file, mask_json_file))
                        break

            if not (len(zipped_jsons) == len(page_json_files) == len(mask_json_files)):
                logger.debug(f"Found: {len(page_json_files)} page json files.")
                logger.debug(f"Found: {len(mask_json_files)} mask json files.")
                logger.debug(f"Matching: {len(zipped_jsons)} json files.")
                logger.warning("Mismatched number of json files for inpainting.")

            # Check the inpainting model is avaliable.
            if not md.is_inpainting_downloaded(config):
                raise FileNotFoundError(tr("Inpainting model not found."))

            inpainter_model = ip.InpaintingModel(config)

            # Pack all the arguments into a dataclass.
            data = [
                st.InpainterData(
                    page_json_file,
                    mask_json_file,
                    None,
                    cache_dir,
                    profile.general,
                    profile.masker,
                    profile.denoiser,
                    profile.inpainter,
                    save_only_mask=target_outputs == [imf.Output.inpainted_mask],
                    save_only_cleaned=target_outputs == [imf.Output.inpainted_output],
                    extract_text=imf.Output.isolated_text in target_outputs,
                    separate_inpaint_masks=False,
                    show_masks=True,
                    debug=debug,
                )
                for page_json_file, mask_json_file in zipped_jsons
            ]

            # Single threaded due to model loading overhead.
            inpaint_analytics_raw = []
            for data_obj in data:
                check_abortion()
                analytic = ip.inpaint_page(data_obj, inpainter_model)
                inpaint_analytics_raw.append(analytic)

                progress_callback.emit(
                    imf.ProgressData(
                        len(step_inpainting_images),
                        target_outputs,
                        imf.Step.inpainter,
                        imf.ProgressType.incremental,
                    )
                )

            # Update the outputs of the image objects.
            for image_obj in step_inpainting_images:
                update_output(image_obj, imf.Output.inpainted_mask, "_inpainting.png")
                update_output(image_obj, imf.Output.inpainted_output, "_clean_inpaint.png")
                update_output(image_obj, imf.Output.isolated_text, "_text.png")

            progress_callback.emit(
                imf.ProgressData(
                    len(step_inpainting_images),
                    target_outputs,
                    imf.Step.inpainter,
                    imf.ProgressType.analyticsInpainter,
                    (
                        inpaint_analytics_raw,
                        profile.inpainter.min_inpainting_radius,
                        profile.inpainter.max_inpainting_radius,
                    ),
                )
            )

    # ============================================== Final Output ==============================================

    logger.info(f"Finished processing {len(image_objects)} images.")

    check_abortion()

    if target_output == imf.Output.write_output:
        progress_callback.emit(
            imf.ProgressData(
                len(image_objects),
                target_outputs,
                imf.Step.output,
                imf.ProgressType.begin_step,
            )
        )

        for image_obj in image_objects:
            check_abortion()
            copy_to_output(image_obj, target_outputs, output_dir, profile)

            progress_callback.emit(
                imf.ProgressData(
                    len(image_objects),
                    target_outputs,
                    imf.Step.output,
                    imf.ProgressType.incremental,
                )
            )

    progress_callback.emit(
        imf.ProgressData(
            0,
            [],
            imf.Step.output,
            imf.ProgressType.end,
        )
    )


def copy_to_output(
    image_object: imf.ImageFile,
    outputs: list[imf.Output],
    output_directory: Path,
    profile: cfg.Profile,
):
    """
    Copy or export the outputs from the cache directory to the output directory.
    Output paths and preferred file types are taken into account.

    Supported outputs:
    - Masked image: Output.masked_output
    - Final mask: Output.final_mask
    - Isolated text: Output.isolated_text
    - Denoised image: Output.denoised_output
    - Denoised Mask: Output.denoise_mask
    - Inpainted image: Output.inpainted_output
    - Inpainted Mask: Output.inpainted_mask

    This may raise OSError in various circumstances.

    :param image_object: The image object to copy the outputs for.
    :param outputs: The outputs to copy.
    :param output_directory: The directory to write the outputs to.
    :param profile: The profile to use.
    """

    if output_directory.is_absolute():
        # When absolute, the output directory is used as is.
        final_out_path = output_directory / image_object.path.name
    else:
        # Otherwise, the output directory is relative to the original image's parent directory.
        final_out_path = image_object.path.parent / output_directory / image_object.path.name

    final_out_path.parent.mkdir(parents=True, exist_ok=True)

    # Create png paths for the outputs.
    cleaned_out_path = final_out_path.with_name(final_out_path.stem + "_clean.png")
    masked_out_path = final_out_path.with_name(final_out_path.stem + "_mask.png")
    text_out_path = final_out_path.with_name(final_out_path.stem + "_text.png")

    # Check what the preferred output format is.
    if profile.general.preferred_file_type is None:
        # Use the original file type by default.
        cleaned_out_path = cleaned_out_path.with_suffix(image_object.path.suffix)
    else:
        cleaned_out_path = cleaned_out_path.with_suffix(profile.general.preferred_file_type)

    if profile.general.preferred_mask_file_type is None:
        # Use png by default.
        masked_out_path = masked_out_path.with_suffix(".png")
        text_out_path = text_out_path.with_suffix(".png")
    else:
        masked_out_path = masked_out_path.with_suffix(profile.general.preferred_mask_file_type)
        text_out_path = text_out_path.with_suffix(profile.general.preferred_mask_file_type)

    # Output optimized images for all requested outputs.
    if imf.Output.masked_output in outputs:
        ops.save_optimized(
            image_object.outputs[imf.Output.masked_output].path, cleaned_out_path, image_object.path
        )

    if imf.Output.final_mask in outputs:
        # First scale the output mask to the original image size.
        final_mask = Image.open(image_object.outputs[imf.Output.final_mask].path)
        final_mask = final_mask.resize(image_object.size, Image.NEAREST)
        ops.save_optimized(final_mask, masked_out_path)

    if imf.Output.isolated_text in outputs:
        ops.save_optimized(image_object.outputs[imf.Output.isolated_text].path, text_out_path)

    if imf.Output.denoised_output in outputs:
        ops.save_optimized(
            image_object.outputs[imf.Output.denoised_output].path,
            cleaned_out_path,
            image_object.path,
        )

    if imf.Output.denoise_mask in outputs:
        # Special case: Here we need to take the final mask, scale it up, and then paste this on top.
        final_mask = Image.open(image_object.outputs[imf.Output.final_mask].path)
        final_mask = final_mask.resize(image_object.size, Image.BILINEAR)
        denoised_mask = Image.open(image_object.outputs[imf.Output.denoise_mask].path)
        # Ensure both images are RGBA to safely alpha composite them.
        final_mask = final_mask.convert("RGBA")
        denoised_mask = denoised_mask.convert("RGBA")
        final_mask.alpha_composite(denoised_mask)

        ops.save_optimized(final_mask, masked_out_path)

    if imf.Output.inpainted_output in outputs:
        ops.save_optimized(
            image_object.outputs[imf.Output.inpainted_output].path,
            cleaned_out_path,
            image_object.path,
        )

    if imf.Output.inpainted_mask in outputs:
        # Special case: Here we need to take the final mask, scale it up, and then paste the denoising
        # mask on top (if denoising), and then paste the inpainting mask on top of that.
        final_mask = Image.open(image_object.outputs[imf.Output.final_mask].path)
        final_mask = final_mask.resize(image_object.size, Image.NEAREST)
        final_mask = final_mask.convert("RGBA")

        if profile.denoiser.denoising_enabled:
            denoised_mask = Image.open(image_object.outputs[imf.Output.denoise_mask].path)
            denoised_mask = denoised_mask.convert("RGBA")
            final_mask.alpha_composite(denoised_mask)

        inpainted_mask = Image.open(image_object.outputs[imf.Output.inpainted_mask].path)
        inpainted_mask = inpainted_mask.convert("RGBA")
        final_mask.alpha_composite(inpainted_mask)

        ops.save_optimized(final_mask, masked_out_path)


def perform_ocr(
    image_objects: list[imf.ImageFile],
    output_file: Path | None,
    csv_output: bool,
    config: cfg.Config,
    ocr_processor: ocr.OcrProcsType | None,
    progress_callback: imf.ProgressSignal,
    abort_flag: wt.SharableFlag,
    debug: bool = False,
):
    """
    Perform OCR on all the images in the given image objects list.
    If a path is given, the output is written to that path.
    Output is either a plain text file or csv.

    The ocr model (or None) is passed in as arguments, so it can be reused
    across multiple runs. This is done because in gui mode the model does not need to be loaded
    repeatedly for single image runs, making iterations much faster, due to the slow
    initializations of the model taking several seconds.

    When setting the output dir to None, intermediate steps are saved to disk, offering
    additional visualizations that aren't necessary when you aren't viewing image details.

    :param image_objects: The image objects to process. These contain the image paths.
    :param output_file: The directory to save the outputs to. If None, the output remains in the cache directory.
    :param csv_output: If True, the output is written as a csv file.
    :param config: The config to use.
    :param ocr_processor: The ocr processors to use.
    :param progress_callback: A callback to report progress to the gui.
    :param abort_flag: A flag that is set to True when the thread should abort.
    :param debug: If True, debug messages are printed.
    """

    def check_abortion() -> None:
        """
        Check if the thread should abort.
        If so, signal abortion to the progress callback and raise an AbortException.
        """
        if abort_flag.get():
            progress_callback.emit(
                imf.ProgressData(
                    0,
                    [],
                    imf.Step.output,
                    imf.ProgressType.aborted,
                )
            )
            raise wt.Abort()

    target_outputs = [imf.Output.ocr]

    progress_callback.emit(
        imf.ProgressData(
            0,
            [],
            imf.Step.text_detection,
            imf.ProgressType.start,
        )
    )

    # Create an independant copy of the profile, since this instance is shared and mutated across threads.
    # Due to the checksum only being generated at the end, we don't want to erroneously claim this output
    # matches a profile that was changed in the meantime.
    # Also, we will be editing this profile to get OCR working.
    profile = deepcopy(config.current_profile)

    # Make sure OCR is enabled.
    profile.preprocessor.ocr_enabled = True
    # Make sure the max size is infinite, so no boxes are skipped in the OCR process.
    profile.preprocessor.ocr_max_size = 10**10
    # Make sure the sus box min size is infinite, so all boxes with "unknown" language are skipped.
    profile.preprocessor.suspicious_box_min_size = 10**10
    # Set the OCR blacklist pattern to match everything, so all text gets reported in the analytics.
    profile.preprocessor.ocr_blacklist_pattern = ".*"

    cache_dir = config.get_cleaner_cache_dir()

    # Get the text detector model path from the config.
    cuda = torch.cuda.is_available()
    text_detector_model_path = config.get_model_path(cuda)

    def step_needs_to_be_rerun_closure(current_step: imf.Step) -> Callable[[imf.ImageFile], bool]:
        """
        Check if any of the outputs for the given image object need to be rerun.

        :return: A function that takes an image object and returns True if the step needs to be rerun for it.
        """

        def step_changed(image_object: imf.ImageFile) -> bool:
            nonlocal profile
            nonlocal target_outputs
            nonlocal current_step

            target_outputs_in_the_current_step: tuple[imf.Output] = tuple(
                filter(lambda o: o in imf.step_to_output[current_step], reversed(target_outputs))
            )

            if target_outputs_in_the_current_step:
                # We need to check each output we care about to know if we gotta rerun the step.
                return any(
                    image_object.outputs[o].is_changed(profile)
                    for o in target_outputs_in_the_current_step
                )
            else:
                # In this case we just need to know if the step's representative is complete.
                representative: imf.Output = imf.get_output_representing_step(current_step)
                return image_object.outputs[representative].is_changed(profile)

        return step_changed

    def update_output(image_object: imf.ImageFile, output: imf.Output, suffix: str) -> None:
        """
        Update the output of the given image object.
        Check if the file actually exists, and if it does, update the output path.

        :param image_object: The image object to update.
        :param output: The output to update.
        :param suffix: The suffix to add to the output path.
        """
        nonlocal profile, cache_dir

        _path = cache_dir / f"{image_object.uuid}_{image_object.path.stem}{suffix}"

        if _path.is_file():
            image_object.outputs[output].update(_path, profile)

    # ============================================== Text Detection ==============================================

    check_abortion()

    step_text_detector_images = tuple(
        filter(step_needs_to_be_rerun_closure(imf.Step.text_detection), image_objects)
    )

    if step_text_detector_images:
        logger.info(
            f"Running text detection AI model for {len(step_text_detector_images)} images..."
        )
        try:
            ctm.model2annotations_gui(
                profile.general,
                profile.text_detector,
                text_detector_model_path,
                step_text_detector_images,
                cache_dir,
                no_text_detection=False,
                visualize_raw_boxes=True,
                partial_progress_data=partial(
                    imf.ProgressData,
                    len(step_text_detector_images),
                    target_outputs,
                    imf.Step.text_detection,
                ),
                progress_callback=progress_callback,
                abort_flag=abort_flag,
            )
        except wt.Abort:
            # Send the progress callback a signal that the process was aborted,
            # and then raise the exception again to stop the processing.
            check_abortion()

        # Update the outputs of the image objects.
        for image_obj in step_text_detector_images:
            update_output(image_obj, imf.Output.input, ".png")
            update_output(image_obj, imf.Output.ai_mask, "_mask.png")
            update_output(image_obj, imf.Output.raw_boxes, "_raw_boxes.png")
            update_output(image_obj, imf.Output.raw_json, "#raw.json")

    # ============================================== Preprocessing ==============================================

    check_abortion()

    logger.info(f"Running preprocessing for {len(image_objects)} images...")

    progress_callback.emit(
        imf.ProgressData(
            len(image_objects),
            target_outputs,
            imf.Step.preprocessor,
            imf.ProgressType.begin_step,
        )
    )

    ocr_analytics: list[st.OCRAnalytic] = []
    # Find all the json files associated with the images.
    for image_obj in image_objects:
        check_abortion()
        json_file_path = cache_dir / f"{image_obj.uuid}_{image_obj.path.stem}#raw.json"
        ocr_analytic = pp.prep_json_file(
            json_file_path,
            preprocessor_conf=profile.preprocessor,
            cache_masks=False,
            mocr=ocr_processor if profile.preprocessor.ocr_enabled else None,
            cache_masks_ocr=True,
            performing_ocr=True,
        )

        if ocr_analytic is not None:
            ocr_analytics.append(ocr_analytic)

        progress_callback.emit(
            imf.ProgressData(
                len(image_objects),
                target_outputs,
                imf.Step.preprocessor,
                imf.ProgressType.incremental,
            )
        )

    # Update only the raw boxes, the rest are tainted by the forced profile changes.
    for image_obj in image_objects:
        update_output(image_obj, imf.Output.initial_boxes, "_boxes.png")

    logger.info(f"Finished processing {len(image_objects)} images.")

    # ============================================== Final Output ==============================================

    check_abortion()

    # Output the OCRed text from the analytics.
    # Format of the analytics:
    # number of boxes | sizes of all boxes | sizes of boxes that were OCRed | path to image, text, box coordinates
    # We do not need to show the first three columns, so we simplify the data structure.
    path_texts_coords: list[tuple[Path, str, st.Box]] = list(
        itertools.chain.from_iterable(a.removed_box_data for a in ocr_analytics)
    )
    if path_texts_coords:
        paths, texts, boxes = zip(*path_texts_coords)
        paths = hp.trim_prefix_from_paths(paths)
        path_texts_coords = list(zip(paths, texts, boxes))
        # Sort by path.
        path_texts_coords = natsorted(path_texts_coords, key=lambda x: x[0])

    buffer = StringIO()
    if csv_output:
        writer = csv.writer(buffer, quoting=csv.QUOTE_MINIMAL)
        writer.writerow(
            [tr("filename"), tr("startx"), tr("starty"), tr("endx"), tr("endy"), tr("text")]
        )

        for path, bubble, box in path_texts_coords:
            if "\n" in bubble:
                logger.warning(f"Detected newline in bubble: {path} {bubble} {box}")
                bubble = bubble.replace("\n", "\\n")
            writer.writerow([path, *box.as_tuple, bubble])

        text_out = buffer.getvalue()
    else:
        # Place the file path on it's own line, and only if it's different from the previous one.
        current_path = ""
        for path, bubble, _ in path_texts_coords:
            if path != current_path:
                buffer.write(f"\n\n{path}: ")
                current_path = path
            buffer.write(f"\n{bubble}")
            if "\n" in bubble:
                logger.warning(f"Detected newline in bubble: {path} {bubble}")

        text_out = buffer.getvalue()

    text_out = text_out.strip("\n \t")

    if output_file is not None:
        try:
            output_file.parent.mkdir(parents=True, exist_ok=True)
            output_file.write_text(text_out, encoding="utf-8")
            buffer.write(
                "\n\n" + tr("Saved detected text to {output_file}").format(output_file=output_file)
            )
        except OSError:
            # buffer.write(f"\n\nFailed to write detected text to {output_file}")
            buffer.write(
                "\n\n"
                + tr("Failed to write detected text to {output_file}").format(
                    output_file=output_file
                )
            )
            gu.show_exception(None, tr("Save Failed"), tr("Failed to write detected text to file."))

    progress_callback.emit(
        imf.ProgressData(
            0,
            [],
            imf.Step.preprocessor,
            imf.ProgressType.outputOCR,
            buffer.getvalue(),
        )
    )

    progress_callback.emit(
        imf.ProgressData(
            0,
            [],
            imf.Step.output,
            imf.ProgressType.end,
        )
    )
