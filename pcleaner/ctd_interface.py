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
import string
from pathlib import Path
import multiprocessing as mp

from tqdm import tqdm
import torch

import pcleaner.config as cfg
from .comic_text_detector.inference import TextDetector
from .comic_text_detector.utils.io_utils import imread, imwrite, find_all_imgs, NumpyEncoder
from .comic_text_detector.utils.textmask import REFINEMASK_ANNOTATION


def model2annotations(
    config: cfg.TextDetectorConfig,
    model_path: Path,
    img_paths: str | Path | list[str | Path],
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

    :param config: Text detector configuration, part of the profile.
    :param model_path: Path to the model file. This ends either in .pt or .onnx (torch or cv2 format).
    :param img_paths: Path or a list of paths to an image or directory of images.
    :param save_dir: Path to the directory where the results will be saved.
    :return:
    """
    # Scan for images, shallow search in given directories.
    if isinstance(img_paths, str | Path):
        img_paths = [img_paths]

    img_list = []

    for img_dir in img_paths:
        if Path(img_dir).is_dir():
            img_list.extend(find_all_imgs(img_dir, abs_path=True))
        elif Path(img_dir).is_file():
            img_list.append(img_dir)
        else:
            raise FileNotFoundError(f"Image path {img_dir} does not exist.")

    if not img_list:
        print("No images found.")
        return

    device = "cuda" if model_path.suffix == ".pt" else "cpu"
    print(f"Using device for text detection model: {device}")
    # Determine the number of processes to use
    num_processes = min(config.concurrent_models, len(img_list))
    print(f"Using {num_processes} processes for text detection.")

    if num_processes > 1:

        mp.freeze_support()
        mp.set_start_method("spawn")

        with mp.Pool(num_processes) as pool:

            # Distribute the images evenly among the processes.
            batches = [list() for _ in range(num_processes)]
            for i, img_path in enumerate(img_list):
                batches[i % num_processes].append(img_path)

            args = [(batch, model_path, device, save_dir) for batch in batches]

            for _ in tqdm(pool.imap_unordered(process_image_batch, args), total=len(args)):
                pass  # do nothing, just iterate through the results

    else:
        model = TextDetector(model_path=str(model_path), input_size=1024, device=device)

        for index, img_path in enumerate(tqdm(img_list)):
            process_image(img_path, model, save_dir)


def process_image_batch(args):
    img_batch, model_path, device, save_dir = args
    model = TextDetector(model_path=str(model_path), input_size=1024, device=device)
    for img_path in img_batch:
        process_image(img_path, model, save_dir)

    del model

    if device == "cuda":
        # Release CUDA resources.
        torch.cuda.ipc_collect()
        torch.cuda.empty_cache()


def process_image(img_path: str | Path, model: TextDetector, save_dir: Path):

    img = imread(img_path)
    img_path = Path(img_path).absolute()

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
        "blk_list": blk_dict_list,
    }

    with open(Path(img_name).with_suffix(".json"), "w", encoding="utf8") as f:
        json.dump(data, f, ensure_ascii=False, cls=NumpyEncoder, indent=4)
    imwrite(img_name, img)
    imwrite(maskname, mask_refined)


def get_random_uppercase_string(length: int = 4) -> str:
    """
    Return a random string of uppercase letters of the given length.

    :param length: The length of the string to return.
    :return: A random string of uppercase letters of the given length.
    """
    letters = string.ascii_uppercase
    random_indices = random.sample(range(len(letters)), length)
    return "".join(map(lambda i: letters[i], random_indices))
