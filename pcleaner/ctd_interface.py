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
import uuid
from pathlib import Path
import multiprocessing as mp

from tqdm import tqdm
from PIL import Image
import torch
import numpy as np
import cv2
from logzero import logger

import pcleaner.config as cfg
from .comic_text_detector.inference import TextDetector
from .comic_text_detector.utils.io_utils import imwrite, NumpyEncoder
from .comic_text_detector.utils.textmask import REFINEMASK_ANNOTATION


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

    device = "cuda" if model_path.suffix == ".pt" else "cpu"
    print(f"Using device for text detection model: {device}")
    # Determine the number of processes to use
    num_processes = min(config_detector.concurrent_models, len(img_list))
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
                (batch, model_path, device, save_dir, config_general.input_size_scale)
                for batch in batches
            ]

            for _ in tqdm(pool.imap_unordered(process_image_batch, args), total=len(args)):
                pass  # do nothing, just iterate through the results

    else:
        model = TextDetector(model_path=str(model_path), input_size=1024, device=device)

        for index, img_path in enumerate(tqdm(img_list)):
            process_image(img_path, model, save_dir, config_general.input_size_scale)


def process_image_batch(args):
    img_batch, model_path, device, save_dir, image_scale = args
    model = TextDetector(model_path=str(model_path), input_size=1024, device=device)
    for img_path in img_batch:
        process_image(img_path, model, save_dir, image_scale)

    del model

    if device == "cuda":
        # Release CUDA resources.
        torch.cuda.ipc_collect()
        torch.cuda.empty_cache()


def process_image(img_path: Path, model: TextDetector, save_dir: Path, image_scale: float):
    """
    Process a single image using the TextDetector model.
    This generates a mask and a json file containing the text boxes.
    These both belong in the cache directory.

    :param img_path: The path to the image to process.
    :param model: The TextDetector model.
    :param save_dir: The directory where the results will be saved.
    :param image_scale: The scale to use when resizing the image (float > 0).
    """

    img = read_image(img_path, image_scale)

    # Prepend an index to prevent name clobbering between different files.
    prefix = f"{uuid.uuid4()}_"

    img_name = prefix + img_path.stem
    maskname = img_name + "_mask.png"

    # Make names absolute paths.
    img_name = str((save_dir / (img_name + ".png")).absolute())
    maskname = str((save_dir / maskname).absolute())

    mask, mask_refined, blk_list = model(
        img, refine_mode=REFINEMASK_ANNOTATION, keep_undetected_mask=True
    )
    blk_xyxy = []
    blk_dict_list = []
    for blk in blk_list:
        blk_xyxy.append(blk.xyxy)
        blk_dict_list.append(blk.to_dict())

    # Inject the img_name.png and mask name and original path into the json.
    data = {
        "image_path": img_name,
        "mask_path": maskname,
        "original_path": str(img_path),
        "scale": image_scale,
        "blk_list": blk_dict_list,
    }
    # Remove the suffix and add _raw.json
    json_path = Path(img_name).with_suffix(".json")
    json_path = json_path.with_stem(json_path.stem + "#raw")
    logger.debug(f"Saving json file to {json_path}")
    with open(json_path, "w", encoding="utf8") as f:
        json.dump(data, f, ensure_ascii=False, cls=NumpyEncoder, indent=4)
    imwrite(img_name, img)
    imwrite(maskname, mask_refined)


def read_image(path: Path | str, scale=1.0) -> np.ndarray:
    """
    Read image from path, scaling it if necessary.
    Then return an array of the image.

    :param path: Image path
    :param scale: Scale factor
    :return: Image array
    """

    img = Image.open(str(path))

    if img.mode == "CMYK":
        logger.warning(f"Image {path} is in CMYK mode. Converting to RGB.")
        img = img.convert("RGB")

    if scale != 1.0:
        new_width = int(img.width * scale)
        new_height = int(img.height * scale)
        img = img.resize((new_width, new_height), Image.ANTIALIAS)

    return np.array(img)
