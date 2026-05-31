"""
This file contains a slightly modified version of the original function,
and serves as the only link to the comic_text_detector project:
https://github.com/dmMaze/comic-text-detector
(License: GNU General Public License v3.0)

Should a newer version of the comic_text_detector project be released,
replacing the files in the pcleaner/comic_text_detector folder with the
newer version should be sufficient to update the code, provided that the
coupling between this function and the rest of the code is not broken.

The code present in the pcleaner/comic_text_detector folder is a
slimmed-down version of the original project, containing only the
necessary files to run the model and the function below.
"""

import json
import multiprocessing as mp
from math import floor, ceil
from pathlib import Path

import cv2
import numpy as np
import torch
from loguru import logger
from tqdm import tqdm

import pcleaner.config as cfg
import pcleaner.image_ops as ops
import pcleaner.output_structures as ost
from pcleaner.comic_text_detector.inference import TextDetector
from pcleaner.comic_text_detector.utils.io_utils import imwrite, NumpyEncoder
from pcleaner.comic_text_detector.utils.textmask import REFINEMASK_ANNOTATION


def model2annotations(
    config_general: cfg.GeneralConfig,
    config_detector: cfg.TextDetectorConfig,
    model_path: Path,
    img_list: list[Path],
    save_dir: Path,
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

    :param config_general: General configuration, part of the profile.
    :param config_detector: Text detector configuration, part of the profile.
    :param model_path: Path to the model file. This ends either in .pt or .onnx (torch or cv2 format).
    :param img_list: Path or a list of paths to an image or directory of images.
    :param save_dir: Path to the directory where the results will be saved.
    :return:
    """


    # For non-MPS systems, use the original multiprocessing approach
    device = "cuda" if torch.cuda.is_available() else "cpu"
    num_processes = min(config_detector.concurrent_models, len(img_list))
    if torch.backends.mps.is_available():
        device = "mps"
        num_processes = 1  # Multiprocessing breaks the mps backend.
    print(f"Using device for text detection model: {device}")
    print(f"Using {num_processes} processes for text detection.")

    if num_processes > 1:
        mp.freeze_support()
        mp.set_start_method("spawn")

        with mp.Pool(num_processes) as pool:
            # Distribute the images evenly among the processes.
            batches = [list() for _ in range(num_processes)]
            for i, img_path in enumerate(img_list):
                batches[i % num_processes].append(img_path)

            args = [
                (
                    batch,
                    model_path,
                    device,
                    save_dir,
                    config_general.input_height_lower_target,
                    config_general.input_height_upper_target,
                    config_detector.bubble_detection_enabled,
                    config_detector.bubble_detector_model_path,
                )
                for batch in batches
            ]

            for _ in tqdm(pool.imap_unordered(process_image_batch, args), total=len(args)):
                pass  # do nothing, just iterate through the results

    else:
        model = TextDetector(model_path=str(model_path), input_size=1024, device=device)

        for index, img_path in enumerate(tqdm(img_list)):
            process_image(
                img_path,
                model,
                save_dir,
                config_general.input_height_lower_target,
                config_general.input_height_upper_target,
                bubble_detection_enabled=config_detector.bubble_detection_enabled,
                bubble_detector_model_path=config_detector.bubble_detector_model_path,
            )


def process_image_batch(args) -> None:
    (
        img_batch,
        model_path,
        device,
        save_dir,
        height_target_lower,
        height_target_upper,
        bubble_detection_enabled,
        bubble_detector_model_path,
    ) = args
    model = TextDetector(model_path=str(model_path), input_size=1024, device=device)
    for img_path in img_batch:
        process_image(
            img_path,
            model,
            save_dir,
            height_target_lower,
            height_target_upper,
            bubble_detection_enabled=bubble_detection_enabled,
            bubble_detector_model_path=bubble_detector_model_path,
        )

    del model

    if device == "cuda":
        # Release CUDA resources.
        torch.cuda.ipc_collect()
        torch.cuda.empty_cache()


def process_image(
    img_path: Path,
    model: TextDetector,
    save_dir: Path,
    height_target_lower: int,
    height_target_upper: int,
    skip_text_detection: bool = False,
    uuid: str = None,
    visualize_raw_data: bool = False,
    bubble_detection_enabled: bool = False,
    bubble_detector_model_path: str | None = None,
):
    """
    Process a single image using the TextDetector model.
    This generates a mask and a json file containing the text boxes.
    These both belong in the cache directory.

    :param img_path: The path to the image to process.
    :param model: The TextDetector model.
    :param save_dir: The directory where the results will be saved.
    :param height_target_lower: The lower target height of the input image.
    :param height_target_upper: The upper target height of the input image.
    :param skip_text_detection: If True, skip the text detection step and only
        save the scaled input image as a png.
    :param uuid: The uuid to use for the image. If None, a new uuid will be generated.
    :param visualize_raw_data: If True, visualize the raw box data.
    """

    img: np.ndarray = read_image(img_path)
    img, image_scale = resize_to_target(img, height_target_lower, height_target_upper)

    path_gen = ost.OutputPathGenerator(img_path, save_dir, uuid)

    # Save a scaled copy of the image.
    imwrite(str(path_gen.base_png), img)
    if skip_text_detection:
        # If we're only saving the scaled image, we're done.
        return

    mask, mask_refined, blk_list = model(
        img, refine_mode=REFINEMASK_ANNOTATION, keep_undetected_mask=True
    )

    # Optionally augment the detected boxes using the comic text and bubble detector.
    if bubble_detection_enabled:
        augment_blk_list_with_bubble_detector(img, blk_list, bubble_detector_model_path)

    blk_xyxy = []
    blk_dict_list = []
    for blk in blk_list:
        blk_xyxy.append(blk.xyxy)
        blk_dict_list.append(blk.to_dict())

    # Inject the img_name.png and mask name and original path into the json.
    data = {
        "image_path": str(path_gen.base_png),
        "mask_path": str(path_gen.raw_mask),
        "original_path": str(img_path),
        "scale": image_scale,
        "blk_list": blk_dict_list,
    }
    json_path = path_gen.raw_json
    logger.debug(f"Saving json file to {json_path}")
    with open(json_path, "w", encoding="utf8") as f:
        json.dump(data, f, ensure_ascii=False, cls=NumpyEncoder, indent=4)
    imwrite(str(path_gen.raw_mask), mask_refined)

    if visualize_raw_data:
        ops.visualize_raw_boxes(img, blk_dict_list, path_gen.raw_boxes)


def _boxes_overlap(box_a, box_b, threshold: float = 0.3) -> bool:
    """
    Check whether two xyxy boxes overlap by more than ``threshold`` of the
    smaller box's area.
    """
    ax1, ay1, ax2, ay2 = box_a
    bx1, by1, bx2, by2 = box_b
    x_overlap = max(0, min(ax2, bx2) - max(ax1, bx1))
    y_overlap = max(0, min(ay2, by2) - max(ay1, by1))
    intersection = x_overlap * y_overlap
    if intersection == 0:
        return False
    area_a = max(1, (ax2 - ax1) * (ay2 - ay1))
    area_b = max(1, (bx2 - bx1) * (by2 - by1))
    return intersection / min(area_a, area_b) > threshold


def augment_blk_list_with_bubble_detector(
    img: np.ndarray,
    blk_list: list,
    bubble_detector_model_path: str | None = None,
) -> None:
    """
    Augment the detected text blocks in place using the comic text and bubble
    detector (RT-DETR). New text regions (classes text_bubble / text_free) that
    aren't already covered by an existing block are appended, and every block is
    tagged with an ``in_bubble`` flag based on the detected bubble regions.

    The segmentation mask from the built-in detector is left untouched; this only
    improves the box data. Failures are logged and ignored so that an unavailable
    or failing optional model never breaks the main pipeline.

    :param img: The (already resized) image as a cv2 BGR ndarray.
    :param blk_list: The list of TextBlock objects to augment in place.
    :param bubble_detector_model_path: Optional model path/repo override.
    """
    try:
        from pcleaner.comic_text_detector.bubble_detector import (
            BubbleDetector,
            CLASS_BUBBLE,
            CLASS_TEXT_BUBBLE,
            CLASS_TEXT_FREE,
        )
        from pcleaner.comic_text_detector.utils.textblock import TextBlock
    except ImportError as e:
        logger.warning(f"Could not import the bubble detector, skipping augmentation: {e}")
        return

    try:
        detections = BubbleDetector().detect(img, model_path=bubble_detector_model_path)
    except Exception as e:
        logger.error(f"Comic text and bubble detection failed, skipping augmentation: {e}")
        return

    bubble_boxes = [box for box, cls, _ in detections if cls == CLASS_BUBBLE]
    text_boxes = [box for box, cls, _ in detections if cls in (CLASS_TEXT_BUBBLE, CLASS_TEXT_FREE)]

    # Append detected text regions that aren't already represented by a block.
    existing_boxes = [blk.xyxy for blk in blk_list]
    for box in text_boxes:
        if not any(_boxes_overlap(box, existing) for existing in existing_boxes):
            blk_list.append(TextBlock(xyxy=list(box), language="unknown"))
            existing_boxes.append(box)

    # Tag every block with whether it sits inside a detected speech bubble.
    for blk in blk_list:
        blk.in_bubble = any(_boxes_overlap(blk.xyxy, bubble) for bubble in bubble_boxes)


def read_image(path: Path | str) -> np.ndarray:
    """
    Read image from path, scaling it if necessary.
    Then return an array of the image.

    :param path: Image path
    :return: Image array
    """

    return cv2.imdecode(np.fromfile(str(path), dtype=np.uint8), cv2.IMREAD_COLOR)


def calculate_new_size_and_scale(
    width: int, height: int, height_target_lower: int, height_target_upper: int
) -> tuple[int, int, float]:
    """
    Calculate the new dimensions and scale factor for resizing an image.
    Prefer the largest whole integer scale factor to scale down by.
    Never scales up and skips scaling if one of the dimensions is <= 0.

    :param width: The current width of the image.
    :param height: The current height of the image.
    :param height_target_lower: The lower target height of the input image.
    :param height_target_upper: The upper target height of the input image.
    :return: Tuple containing new width, new height, and scale factor.
    """
    if height_target_lower <= 0 or height_target_upper <= 0 or height <= height_target_upper:
        return width, height, 1.0

    # Check if both targets are the same, or the lower one is greater, requiring an exact size.
    if height_target_lower >= height_target_upper:
        scale = height_target_upper / height
        new_width = round(width * scale)
        new_height = height_target_lower
    else:
        # Otherwise, check bounds and choose the largest whole integer scale factor, if possible.
        # Using the inverse scale factor to determine denominators like 1/2, 1/3, etc.
        inv_scale_lower = height / height_target_lower
        inv_scale_upper = height / height_target_upper
        inv_scale_upper_nearest = ceil(inv_scale_upper)
        # Check if the nearest upper bound is within the range.
        if inv_scale_upper_nearest <= inv_scale_lower:
            scale = 1 / inv_scale_upper_nearest
            new_width = round(width * scale)
            new_height = round(height * scale)
        else:
            # Otherwise just try to choose the largest size that results in a height that is a multiple of 4.
            max_height = round(height / inv_scale_upper)
            min_height = round(height / inv_scale_lower)
            # Find the largest multiple of 4 that is within the range.
            new_height = floor(max_height / 4) * 4
            if new_height < min_height:
                # If the largest multiple of 4 is still too small, just use the upper bound.
                new_height = max_height
            scale = new_height / height
            new_width = round(width * scale)

    return new_width, new_height, scale


def resize_to_target(
    image: np.ndarray, height_target_lower: int, height_target_upper: int
) -> tuple[np.ndarray, float]:
    """
    Resize the image to fall within the target height range.
    Prefer the largest whole integer scale factor to scale down by.
    Never scales up and skips scaling if one of the dimensions is <= 0.

    :param image: The image to resize as a numpy array, loaded by cv2.
    :param height_target_lower: The lower target height of the input image.
    :param height_target_upper: The upper target height of the input image.
    :return: The resized image and the scale factor.
    """
    height, width, _ = image.shape  # As a matrix, it returns the height (columns) first.
    new_width, new_height, scale = calculate_new_size_and_scale(
        width, height, height_target_lower, height_target_upper
    )

    return cv2.resize(image, (new_width, new_height), interpolation=cv2.INTER_AREA), scale
