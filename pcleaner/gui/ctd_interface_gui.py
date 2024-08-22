import multiprocessing as mp
from functools import partial
from pathlib import Path
from typing import Sequence

import torch

import pcleaner.config as cfg
import pcleaner.gui.image_file as imf
import pcleaner.output_structures as ost
import pcleaner.gui.worker_thread as wt
from pcleaner.comic_text_detector.inference import TextDetector
from pcleaner.ctd_interface import process_image


# It's simply slower for anything less than this many images.
MIN_IMAGES_FOR_MULTIPROCESSING = 20


def model2annotations_gui(
    config_general: cfg.GeneralConfig,
    config_detector: cfg.TextDetectorConfig,
    text_detector_model_path: Path,
    img_list: Sequence[imf.ImageFile],
    save_dir: Path,
    no_text_detection: bool,
    visualize_raw_boxes: bool,
    partial_progress_data: partial,
    progress_callback: ost.ProgressSignal | None,
    abort_flag: wt.SharableFlag,
):
    """
    Run the model on a directory of images and produce the following
    for each image inside the save_dir directory:
    - A copy of the original image as a .png file.
    - A .png file containing the text mask, filename: <image_name>_mask.png.
    - A .json file containing each box of text, as well as other metadata,
      filename: <image_name>.json.

    For this modified version, include the image name and mask name in the
    json file.

    The partial progress data must have the following arguments pre-filled:
    - The total number of images to process.
    - The target output to reach.
    - The current step.

    Note on Aborting:
    The sharable flag is passed to this function because it is what iterates over the images.
    It must not interrupt the process for a single image, but should prevent the next image
    from being processed.
    All this function needs to do is raise the Abort exception, the calling function will send
    the appropriate progress update to the rest of the gui.

    :param config_general: General configuration, part of the profile.
    :param config_detector: Text detector configuration, part of the profile.
    :param text_detector_model_path: Path to the model file. This ends either in .pt or .onnx (torch or cv2 format).
    :param img_list: Path or a list of paths to an image or directory of images.
    :param save_dir: Path to the directory where the results will be saved.
    :param no_text_detection: If True, the text detection step is skipped. This is to only get the "input" output.
    :param visualize_raw_boxes: If True, the raw box data is drawn as an extra output.
    :param partial_progress_data: A partial function to create a ProgressData object.
        You must only add the current iteration to the partial function to construct a valid
        ProgressData object.
    :param progress_callback: A callback to report progress to the gui.
    :param abort_flag: A flag to indicate if the process should abort.
    """

    if progress_callback is not None:
        progress_callback.emit(partial_progress_data(ost.ProgressType.begin_step))

    def inc_progress() -> None:
        if progress_callback is not None:
            progress_callback.emit(partial_progress_data(ost.ProgressType.incremental))

    num_processes = min(config_detector.concurrent_models, len(img_list))

    if (
        num_processes > 1
        and not no_text_detection
        and len(img_list) > MIN_IMAGES_FOR_MULTIPROCESSING
    ):
        mp.freeze_support()
        mp.set_start_method("spawn")

        with mp.Pool(num_processes) as pool:
            # Distribute the images evenly among the processes.
            # The batches is a list of lists of tuples, where each tuple contains the image path and uuid.
            batches: list[list[tuple[Path, str]]] = [list() for _ in range(num_processes)]
            for i, img_obj in enumerate(img_list):
                batches[i % num_processes].append((img_obj.path, img_obj.uuid))

            device = "cuda" if text_detector_model_path.suffix == ".pt" else "cpu"
            args = [
                (
                    batch,
                    text_detector_model_path,
                    device,
                    save_dir,
                    config_general.input_height_lower_target,
                    config_general.input_height_upper_target,
                    inc_progress,
                    visualize_raw_boxes,
                )
                for batch in batches
            ]

            for _ in pool.imap_unordered(process_image_batch, args):
                if abort_flag.get():
                    raise wt.Abort()

    else:
        # Load the model.
        cuda = torch.cuda.is_available()
        device = "cuda" if cuda else "cpu"
        model = TextDetector(
            model_path=str(text_detector_model_path), input_size=1024, device=device
        )

        for img_obj in img_list:
            if abort_flag.get():
                raise wt.Abort()

            process_image(
                img_obj.path,
                model,
                save_dir,
                config_general.input_height_lower_target,
                config_general.input_height_upper_target,
                no_text_detection,
                img_obj.uuid,
                visualize_raw_boxes,
            )
            inc_progress()


def process_image_batch(args) -> None:
    (
        img_batch,
        model_path,
        device,
        save_dir,
        lower_target,
        upper_target,
        inc_progress,
        visualize_raw_boxes,
    ) = args
    model = TextDetector(model_path=str(model_path), input_size=1024, device=device)
    for img_path, img_uuid in img_batch:
        process_image(
            img_path,
            model,
            save_dir,
            lower_target,
            upper_target,
            uuid=img_uuid,
            visualize_raw_data=visualize_raw_boxes,
        )
        inc_progress()

    del model

    if device == "cuda":
        # Release CUDA resources.
        torch.cuda.ipc_collect()
        torch.cuda.empty_cache()
