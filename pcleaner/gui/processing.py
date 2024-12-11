import os
from copy import deepcopy, copy
from functools import partial
from multiprocessing import Pool
from pathlib import Path
from typing import Callable

import torch
from loguru import logger

import pcleaner.config as cfg
import pcleaner.denoiser as dn
import pcleaner.gui.ctd_interface_gui as ctm
import pcleaner.gui.gui_utils as gu
import pcleaner.gui.image_file as imf
import pcleaner.gui.worker_thread as wt
import pcleaner.gui.structures as gst
import pcleaner.image_export as ie
import pcleaner.inpainting as ip
import pcleaner.masker as ma
import pcleaner.ocr.ocr as ocr
import pcleaner.output_structures as ost
import pcleaner.preprocessor as pp
import pcleaner.structures as st
import pcleaner.helpers as hp
from pcleaner import model_downloader as md
from pcleaner.config import LayeredExport
from pcleaner.helpers import tr


def generate_output(
    image_objects: list[imf.ImageFile | imf.MergedImageFile],
    split_files: dict[Path, list[imf.ImageFile]],
    target_outputs: list[ost.Output],
    output_dir: Path | None,
    config: cfg.Config,
    ocr_processor: ocr.OCREngineFactory | None,
    progress_callback: ost.ProgressSignal,
    batch_metadata: gst.BatchMetadata,
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
    :param split_files: The split files information.
    :param target_outputs: The target outputs to reach, eg. the clean mask and image.
        Multiple outputs are only supported for those within the same step, as it's meant to accommodate
        the full run parameters.
    :param output_dir: The directory to save the outputs to. If None, the output remains in the cache directory.
    :param config: The config to use.
    :param ocr_processor: The ocr models to use.
    :param progress_callback: A callback to report progress to the gui.
    :param batch_metadata: The metadata for the batch, used for the post action arguments.
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
                ost.ProgressData(
                    0,
                    [],
                    ost.Step.output,
                    ost.ProgressType.aborted,
                )
            )
            raise wt.Abort()

    progress_callback.emit(
        ost.ProgressData(
            0,
            [],
            ost.Step.text_detection,
            ost.ProgressType.start,
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

    def step_needs_to_be_rerun_closure(current_step: ost.Step) -> Callable[[imf.ImageFile], bool]:
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

            target_outputs_in_the_current_step: tuple[ost.Output] = tuple(
                filter(lambda o: o in ost.step_to_output[current_step], reversed(target_outputs))
            )

            if target_outputs_in_the_current_step:
                # We need to check each output we care about to know if we gotta rerun the step.
                return any(
                    image_object.outputs[o].is_changed(profile)
                    for o in target_outputs_in_the_current_step
                )
            else:
                # In this case we just need to know if the step's representative is complete.
                representative: ost.Output = ost.get_output_representing_step(current_step)
                return image_object.outputs[representative].is_changed(profile)

        return step_changed

    def update_output(image_object: imf.ImageFile, current_output: ost.Output) -> None:
        """
        Update the output of the given image object.
        Check if the file actually exists, and if it does, update the output path.

        :param image_object: The image object to update.
        :param current_output: The output to update.
        """
        nonlocal profile, cache_dir

        _path_gen = ost.OutputPathGenerator(image_object.path, cache_dir, image_object.uuid)
        path = _path_gen.for_output(current_output)

        if path.is_file():
            image_object.outputs[current_output].update(path, profile)

    # ============================================== Text Detection ==============================================

    check_abortion()

    step_text_detector_images = tuple(
        filter(step_needs_to_be_rerun_closure(ost.Step.text_detection), image_objects)
    )

    if step_text_detector_images:
        logger.info(
            f"Running text detection AI model for {len(step_text_detector_images)} images..."
        )

        visualize_raw_boxes = ost.Output.raw_boxes in target_outputs

        try:
            ctm.model2annotations_gui(
                profile.general,
                profile.text_detector,
                text_detector_model_path,
                step_text_detector_images,
                cache_dir,
                no_text_detection=target_output == ost.Output.input,
                visualize_raw_boxes=visualize_raw_boxes,
                partial_progress_data=partial(
                    ost.ProgressData,
                    len(step_text_detector_images),
                    target_outputs,
                    ost.Step.text_detection,
                ),
                progress_callback=progress_callback if target_output != ost.Output.input else None,
                abort_flag=abort_flag,
            )
        except wt.Abort:
            # Send the progress callback a signal that the process was aborted,
            # and then raise the exception again to stop the processing.
            check_abortion()

        for image_obj in step_text_detector_images:
            for output in ost.step_to_output[ost.Step.text_detection]:
                update_output(image_obj, output)

        progress_callback.emit(
            ost.ProgressData(
                len(step_text_detector_images),
                target_outputs,
                ost.Step.text_detection,
                ost.ProgressType.textDetection_done,
            )
        )

    # ============================================== Preprocessing ==============================================

    check_abortion()

    if target_output > ost.get_output_representing_step(ost.Step.text_detection):
        step_preprocessor_images = tuple(
            filter(step_needs_to_be_rerun_closure(ost.Step.preprocessor), image_objects)
        )

        if step_preprocessor_images:
            logger.info(f"Running preprocessing for {len(step_preprocessor_images)} images...")

            progress_callback.emit(
                ost.ProgressData(
                    len(step_preprocessor_images),
                    target_outputs,
                    ost.Step.preprocessor,
                    ost.ProgressType.begin_step,
                )
            )

            ocr_analytics: list[st.OCRAnalytic] = []
            # Find all the json files associated with the images.
            for image_obj in step_preprocessor_images:
                check_abortion()
                path_gen = ost.OutputPathGenerator(image_obj.path, cache_dir, image_obj.uuid)
                ocr_analytic = pp.prep_json_file(
                    path_gen.raw_json,
                    preprocessor_conf=profile.preprocessor,
                    cache_masks=target_output in ost.step_to_output[ost.Step.preprocessor]
                    or output_dir is None,
                    ocr_engine_factory=ocr_processor if profile.preprocessor.ocr_enabled else None,
                )

                if ocr_analytic is not None:
                    ocr_analytics.append(ocr_analytic)

                progress_callback.emit(
                    ost.ProgressData(
                        len(step_preprocessor_images),
                        target_outputs,
                        ost.Step.preprocessor,
                        ost.ProgressType.incremental,
                    )
                )

            # Update the outputs of the image objects, skipping Output.ocr.
            for image_obj in step_preprocessor_images:
                update_output(image_obj, ost.Output.initial_boxes)
                update_output(image_obj, ost.Output.final_boxes)
                update_output(image_obj, ost.Output.clean_json)

            progress_callback.emit(
                ost.ProgressData(
                    len(step_preprocessor_images),
                    target_outputs,
                    ost.Step.preprocessor,
                    ost.ProgressType.analyticsOCR,
                    (ocr_analytics, profile.preprocessor.ocr_max_size),
                )
            )

    # ============================================== Masker ==============================================

    check_abortion()

    if target_output > ost.get_output_representing_step(ost.Step.preprocessor):
        step_masker_images = tuple(
            filter(step_needs_to_be_rerun_closure(ost.Step.masker), image_objects)
        )

        if step_masker_images:
            logger.info(f"Running masker for {len(step_masker_images)} images...")

            progress_callback.emit(
                ost.ProgressData(
                    len(step_masker_images),
                    target_outputs,
                    ost.Step.masker,
                    ost.ProgressType.begin_step,
                )
            )

            # Find all the json files associated with the images.
            json_files = []
            for image_obj in step_masker_images:
                path_gen = ost.OutputPathGenerator(image_obj.path, cache_dir, image_obj.uuid)
                json_files.append(path_gen.clean_json)

            # Pack all the arguments into a dataclass.
            outputs_that_need_masks = (
                ost.Output.box_mask,
                ost.Output.cut_mask,
                ost.Output.mask_layers,
                ost.Output.mask_overlay,
            )
            # If any of out targeted outputs need to have intermediate masks generated,
            # we need to show the masks. Or if we explicitly want to show the masks.
            need_to_show_masks = output_dir is None or any(
                output in outputs_that_need_masks for output in target_outputs
            )

            data = [
                st.MaskerData(
                    json_file,
                    cache_dir,
                    profile.masker,
                    extract_text=ost.Output.isolated_text in target_outputs,
                    show_masks=need_to_show_masks,
                    debug=debug,
                )
                for json_file in json_files
            ]

            masker_analytics_raw = []

            # Check the size of the required pool, run sequentially if the size is 1.
            core_limit = profile.masker.max_threads
            if core_limit == 0:
                core_limit = os.cpu_count()
            pool_size = min(core_limit, len(data))

            if pool_size > 1:
                with Pool(processes=pool_size) as pool:
                    for analytic in pool.imap(ma.mask_page, data):
                        check_abortion()
                        masker_analytics_raw.extend(analytic)

                        progress_callback.emit(
                            ost.ProgressData(
                                len(step_masker_images),
                                target_outputs,
                                ost.Step.masker,
                                ost.ProgressType.incremental,
                            )
                        )
            else:
                for data_obj in data:
                    check_abortion()
                    analytic = ma.mask_page(data_obj)
                    masker_analytics_raw.extend(analytic)

                    progress_callback.emit(
                        ost.ProgressData(
                            len(step_masker_images),
                            target_outputs,
                            ost.Step.masker,
                            ost.ProgressType.incremental,
                        )
                    )

            for image_obj in step_masker_images:
                for output in ost.step_to_output[ost.Step.masker]:
                    update_output(image_obj, output)

            progress_callback.emit(
                ost.ProgressData(
                    len(step_masker_images),
                    target_outputs,
                    ost.Step.masker,
                    ost.ProgressType.analyticsMasker,
                    (masker_analytics_raw, copy(profile.masker)),  # Make a copy to avoid a mutex.
                )
            )

    # ============================================== Denoiser ==============================================

    check_abortion()

    if (
        target_output > ost.get_output_representing_step(ost.Step.masker)
        and profile.denoiser.denoising_enabled
    ):
        step_denoiser_images = tuple(
            filter(step_needs_to_be_rerun_closure(ost.Step.denoiser), image_objects)
        )

        if step_denoiser_images:
            logger.info(f"Running denoiser for {len(step_denoiser_images)} images...")

            progress_callback.emit(
                ost.ProgressData(
                    len(step_denoiser_images),
                    target_outputs,
                    ost.Step.denoiser,
                    ost.ProgressType.begin_step,
                )
            )

            # Find all the json files associated with the images.
            json_files = []
            for image_obj in step_denoiser_images:
                path_gen = ost.OutputPathGenerator(image_obj.path, cache_dir, image_obj.uuid)
                json_files.append(path_gen.mask_data_json)

            # Pack all the arguments into a dataclass.
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
                core_limit = os.cpu_count()
            pool_size = min(core_limit, len(data))

            if pool_size > 1:
                with Pool() as pool:
                    for analytic in pool.imap(dn.denoise_page, data):
                        check_abortion()
                        denoise_analytics_raw.append(analytic)

                        progress_callback.emit(
                            ost.ProgressData(
                                len(step_denoiser_images),
                                target_outputs,
                                ost.Step.denoiser,
                                ost.ProgressType.incremental,
                            )
                        )
            else:
                for data_obj in data:
                    check_abortion()
                    analytic = dn.denoise_page(data_obj)
                    denoise_analytics_raw.append(analytic)

                    progress_callback.emit(
                        ost.ProgressData(
                            len(step_denoiser_images),
                            target_outputs,
                            ost.Step.denoiser,
                            ost.ProgressType.incremental,
                        )
                    )

            for image_obj in step_denoiser_images:
                for output in ost.step_to_output[ost.Step.denoiser]:
                    update_output(image_obj, output)

            progress_callback.emit(
                ost.ProgressData(
                    len(step_denoiser_images),
                    target_outputs,
                    ost.Step.denoiser,
                    ost.ProgressType.analyticsDenoiser,
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
        target_output > ost.get_output_representing_step(ost.Step.denoiser)
        and profile.inpainter.inpainting_enabled
    ):
        step_inpainting_images = tuple(
            filter(step_needs_to_be_rerun_closure(ost.Step.inpainter), image_objects)
        )

        if step_inpainting_images:
            logger.info(f"Running inpainting for {len(step_inpainting_images)} images...")

            progress_callback.emit(
                ost.ProgressData(
                    len(step_inpainting_images),
                    target_outputs,
                    ost.Step.inpainter,
                    ost.ProgressType.begin_step,
                )
            )

            # Find all the json files associated with the images.
            json_files = []
            for image_obj in step_inpainting_images:
                path_gen = ost.OutputPathGenerator(image_obj.path, cache_dir, image_obj.uuid)
                json_files.append((path_gen.clean_json, path_gen.mask_data_json))

            # Check the inpainting model is available.
            if not md.is_inpainting_downloaded(config):
                raise FileNotFoundError(tr("Inpainting model not found."))

            inpainter_model = ip.InpaintingModel(config)

            # Pack all the arguments into a dataclass.
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
                for page_json_file, mask_json_file in json_files
            ]

            # Single threaded due to model loading overhead.
            inpaint_analytics_raw = []
            for data_obj in data:
                check_abortion()
                analytic = ip.inpaint_page(data_obj, inpainter_model)
                inpaint_analytics_raw.append(analytic)

                progress_callback.emit(
                    ost.ProgressData(
                        len(step_inpainting_images),
                        target_outputs,
                        ost.Step.inpainter,
                        ost.ProgressType.incremental,
                    )
                )

            for image_obj in step_inpainting_images:
                for output in ost.step_to_output[ost.Step.inpainter]:
                    update_output(image_obj, output)

            progress_callback.emit(
                ost.ProgressData(
                    len(step_inpainting_images),
                    target_outputs,
                    ost.Step.inpainter,
                    ost.ProgressType.analyticsInpainter,
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

    if target_output == ost.Output.write_output:

        handle_merging_splits(image_objects, split_files, profile, cache_dir)
        batch_metadata.set_input_paths_from_files(image_objects)

        progress_callback.emit(
            ost.ProgressData(
                len(image_objects),
                target_outputs,
                ost.Step.output,
                ost.ProgressType.begin_step,
            )
        )

        # Pack all the arguments in batches.
        data = [
            (
                image_obj.path,
                image_obj.export_path,
                cache_dir,
                image_obj.uuid,
                target_outputs,
                output_dir,
                profile.general.preferred_file_type,
                profile.general.preferred_mask_file_type,
                profile.denoiser.denoising_enabled,
                profile.general.layered_export,
            )
            for image_obj in image_objects
        ]

        # Check the size of the required pool, run sequentially if the size is 1.
        core_limit = profile.general.max_threads_export
        if core_limit == 0:
            core_limit = os.cpu_count()
        pool_size = min(core_limit, len(data))

        if pool_size > 1:
            with Pool(processes=pool_size) as pool:
                for output_files in pool.imap_unordered(ie.copy_to_output_batched, data):
                    check_abortion()
                    batch_metadata.output_files.extend(output_files)

                    progress_callback.emit(
                        ost.ProgressData(
                            len(image_objects),
                            target_outputs,
                            ost.Step.output,
                            ost.ProgressType.incremental,
                        )
                    )
        else:
            for args in data:
                check_abortion()
                output_files = ie.copy_to_output(*args)
                batch_metadata.output_files.extend(output_files)

                progress_callback.emit(
                    ost.ProgressData(
                        len(image_objects),
                        target_outputs,
                        ost.Step.output,
                        ost.ProgressType.incremental,
                    )
                )

        # For bulk exports, we need a common parent directory.
        if not output_dir.is_absolute():
            common_parent = hp.common_path_parent(
                [image_object.export_path for image_object in image_objects],
            )
            output_dir = common_parent / output_dir

        if profile.general.layered_export == LayeredExport.PSD_BULK:
            file_path = ie.bundle_psd(
                output_dir,
                cache_dir,
                [image_object.path for image_object in image_objects],
                [image_object.uuid for image_object in image_objects],
            )
            if file_path is not None:
                batch_metadata.output_files = [file_path]

        # Clean up merged files to prevent a storage leak
        if split_files:
            # These files start with merged_
            for file in cache_dir.glob("merger_*"):
                file.unlink()

    else:
        # We aren't writing output, but we may still need to update the metadata at least.
        # For that, we will need the input files, so we'd prefer to use the re-merged files.

        # If we need to merge files, we do it by replacing the split objects with the merged objects.
        # But we don't actually want to delete the image objects, so we create a shallow copy of the list.
        # Otherwise the review options, which share the image objects list, would have messed up
        # image objects as a side effect, then pass those on to the next run of the cleaner, resulting
        # in the poor thing being unable to handle the merged files.
        # We don't want the merged image objects to leak beyond the scope of this function.
        image_objects_export = image_objects.copy()
        handle_merging_splits(image_objects_export, split_files, profile, cache_dir)
        batch_metadata.set_input_paths_from_files(image_objects_export)

    batch_metadata.calculate_output_parents()

    progress_callback.emit(
        ost.ProgressData(
            0,
            [],
            ost.Step.output,
            ost.ProgressType.end,
        )
    )


def perform_ocr(
    image_objects: list[imf.ImageFile],
    split_files: dict[Path, list[imf.ImageFile]],
    output_file: Path | None,
    csv_output: bool,
    config: cfg.Config,
    ocr_engine_factory: ocr.OCREngineFactory | None,
    progress_callback: ost.ProgressSignal,
    batch_metadata: gst.BatchMetadata,
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
    :param split_files: The split files information.
    :param output_file: The directory to save the outputs to. If None, nothing is written.
    :param csv_output: If True, the output is written as a csv file.
    :param config: The config to use.
    :param ocr_engine_factory: The ocr processors to use.
    :param progress_callback: A callback to report progress to the gui.
    :param batch_metadata: The metadata for the batch, used for the post action arguments.
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
                ost.ProgressData(
                    0,
                    [],
                    ost.Step.output,
                    ost.ProgressType.aborted,
                )
            )
            raise wt.Abort()

    target_outputs = [ost.Output.ocr]

    progress_callback.emit(
        ost.ProgressData(
            0,
            [],
            ost.Step.text_detection,
            ost.ProgressType.start,
        )
    )

    # Create an independent copy of the profile, since this instance is shared and mutated across threads.
    # Due to the checksum only being generated at the end, we don't want to erroneously claim this output
    # matches a profile that was changed in the meantime.
    # Also, we will be editing this profile to get OCR working.
    profile = deepcopy(config.current_profile)

    # Make sure OCR is enabled.
    profile.preprocessor.ocr_enabled = True
    # Make sure the max size is infinite, so no boxes are skipped in the OCR process.
    profile.preprocessor.ocr_max_size = 10**10
    # Set the OCR blacklist pattern to match everything, so all text gets reported in the analytics.
    profile.preprocessor.ocr_blacklist_pattern = ".*"

    cache_dir = config.get_cleaner_cache_dir()

    # Get the text detector model path from the config.
    cuda = torch.cuda.is_available()
    text_detector_model_path = config.get_model_path(cuda)

    def step_needs_to_be_rerun_closure(current_step: ost.Step) -> Callable[[imf.ImageFile], bool]:
        """
        Check if any of the outputs for the given image object need to be rerun.

        :return: A function that takes an image object and returns True if the step needs to be rerun for it.
        """

        def step_changed(image_object: imf.ImageFile) -> bool:
            nonlocal profile
            nonlocal target_outputs
            nonlocal current_step

            target_outputs_in_the_current_step: tuple[ost.Output] = tuple(
                filter(lambda o: o in ost.step_to_output[current_step], reversed(target_outputs))
            )

            if target_outputs_in_the_current_step:
                # We need to check each output we care about to know if we gotta rerun the step.
                return any(
                    image_object.outputs[o].is_changed(profile)
                    for o in target_outputs_in_the_current_step
                )
            else:
                # In this case we just need to know if the step's representative is complete.
                representative: ost.Output = ost.get_output_representing_step(current_step)
                return image_object.outputs[representative].is_changed(profile)

        return step_changed

    def update_output(image_object: imf.ImageFile, current_output: ost.Output) -> None:
        """
        Update the output of the given image object.
        Check if the file actually exists, and if it does, update the output path.

        :param image_object: The image object to update.
        :param current_output: The output to update.
        """
        nonlocal profile, cache_dir

        _path_gen = ost.OutputPathGenerator(image_object.path, cache_dir, image_object.uuid)
        path = _path_gen.for_output(current_output)

        if path.is_file():
            image_object.outputs[current_output].update(path, profile)

    # ============================================== Text Detection ==============================================

    check_abortion()

    step_text_detector_images = tuple(
        filter(step_needs_to_be_rerun_closure(ost.Step.text_detection), image_objects)
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
                    ost.ProgressData,
                    len(step_text_detector_images),
                    target_outputs,
                    ost.Step.text_detection,
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
            for output in ost.step_to_output[ost.Step.text_detection]:
                update_output(image_obj, output)

    # ============================================== Preprocessing ==============================================

    check_abortion()

    logger.info(f"Running preprocessing for {len(image_objects)} images...")

    progress_callback.emit(
        ost.ProgressData(
            len(image_objects),
            target_outputs,
            ost.Step.preprocessor,
            ost.ProgressType.begin_step,
        )
    )

    ocr_analytics: list[st.OCRAnalytic] = []
    # Find all the json files associated with the images.
    for image_obj in image_objects:
        check_abortion()
        path_gen = ost.OutputPathGenerator(image_obj.path, cache_dir, image_obj.uuid)
        ocr_analytic = pp.prep_json_file(
            path_gen.raw_json,
            preprocessor_conf=profile.preprocessor,
            cache_masks=False,
            ocr_engine_factory=ocr_engine_factory,
            cache_masks_ocr=True,
            performing_ocr=True,
        )

        if ocr_analytic is not None:
            ocr_analytics.append(ocr_analytic)

        progress_callback.emit(
            ost.ProgressData(
                len(image_objects),
                target_outputs,
                ost.Step.preprocessor,
                ost.ProgressType.incremental,
            )
        )

    # Update only the raw boxes, the rest are tainted by the forced profile changes.
    for image_obj in image_objects:
        update_output(image_obj, ost.Output.initial_boxes)

    logger.info(f"Finished processing {len(image_objects)} images.")

    # ============================================== Final Output ==============================================

    check_abortion()

    # In the cleaning process we want to avoid messing with the image_objects list if we aren't exporting,
    # since we share it with the review options object, which will then reuse it later in turn for export.
    # With OCR however, we don't use the image objects list for export (just the analytics),
    # but we do use it when showing the image in the OCR editor/reviewer, in which case this
    # cross-contamination is explicitly necessary to have the reviewer show the merged image for
    # OCR editing, as is expected with the merged analytics containing the text.
    handle_merging_splits(image_objects, split_files, profile, cache_dir, for_ocr=True)
    handle_merging_ocr_splits(split_files, profile, ocr_analytics)

    check_abortion()

    # Output the OCRed text from the analytics.
    text_out = ocr.format_output(
        ocr_analytics,
        csv_output,
        (tr("filename"), tr("startx"), tr("starty"), tr("endx"), tr("endy"), tr("text")),
    )

    text_out = text_out.strip("\n \t")

    if output_file is not None:
        try:
            output_file.parent.mkdir(parents=True, exist_ok=True)
            output_file.write_text(text_out, encoding="utf-8")
            text_out += "\n\n" + tr("Saved detected text to {output_file}").format(
                output_file=output_file
            )
        except OSError:
            text_out += "\n\n" + tr("Failed to write detected text to {output_file}").format(
                output_file=output_file
            )
            gu.show_exception(None, tr("Save Failed"), tr("Failed to write detected text to file."))

    progress_callback.emit(
        ost.ProgressData(
            0,
            [],
            ost.Step.preprocessor,
            ost.ProgressType.outputOCR,
            (text_out, ocr_analytics),
        )
    )

    progress_callback.emit(
        ost.ProgressData(
            0,
            [],
            ost.Step.output,
            ost.ProgressType.end,
        )
    )


def handle_merging_splits(
    image_objects: list[imf.ImageFile | imf.MergedImageFile],
    split_files: dict[Path, list[imf.ImageFile]],
    profile: cfg.Profile,
    cache_dir: Path,
    for_ocr: bool = False,
):
    """
    If merging the splits, merge them into a new image object and remove the split objects.

    :param image_objects: The image objects to process.
    :param split_files: The split files information.
    :param profile: The profile to use.
    :param cache_dir: The cache directory to use.
    :param for_ocr: If True, the merge is for OCR, and we forge some output data as well.
    """
    if not split_files:
        return

    if profile.general.merge_after_split:
        logger.info("Merging split files...")

        for split_file in split_files:
            split_objects = split_files[split_file]

            if not split_objects:
                logger.error(f"Split file {split_file} has no split objects.")
                continue

            # Create a new image object with the split objects.
            merged_object = imf.MergedImageFile(split_objects, cache_dir, for_ocr)

            # Add the new object to the list of image objects.
            image_objects.append(merged_object)

            # Remove the split objects from the list of image objects.
            for split_object in split_objects:
                image_objects.remove(split_object)


def handle_merging_ocr_splits(
    split_files: dict[Path, list[imf.ImageFile]],
    profile: cfg.Profile,
    ocr_analytics: list[st.OCRAnalytic],
):
    """
    If merging the splits, merge them into a new image object and remove the split objects.

    :param split_files: The split files information.
    :param profile: The profile to use.
    :param ocr_analytics: The OCR analytics to merge.
    """
    if not split_files:
        return

    if profile.general.merge_after_split:
        logger.info("Merging split ocr...")

        for split_file in split_files:
            split_objects = split_files[split_file]

            if not split_objects:
                logger.error(f"Split file {split_file} has no split objects.")
                continue

            segment_paths = [split_object.path for split_object in split_objects]
            split_from = split_objects[0].split_from
            st.merge_ocr_analytics(split_from, segment_paths, ocr_analytics)
