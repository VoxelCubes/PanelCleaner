import os
import shutil
from hashlib import sha256
from pathlib import Path

import requests
import torch
import tqdm
from loguru import logger
from manga_ocr import MangaOcr
from transformers import file_utils
import pcleaner.cli_utils as cu


MODEL_URL = "https://github.com/zyddnys/manga-image-translator/releases/download/beta-0.3/"
TORCH_MODEL_NAME = "comictextdetector.pt"
TORCH_SHA256 = "1f90fa60aeeb1eb82e2ac1167a66bf139a8a61b8780acd351ead55268540cccb"
CV2_MODEL_NAME = "comictextdetector.pt.onnx"
CV2_SHA256 = "1a86ace74961413cbd650002e7bb4dcec4980ffa21b2f19b86933372071d718f"
OCR_DIR_NAME = "models--kha-white--manga-ocr-base"
INPAINTING_URL = "https://github.com/Sanster/models/releases/download/AnimeMangaInpainting/anime-manga-big-lama.pt"
INPAINTING_SHA256 = "479d3afdcb7ed2fd944ed4ebcc39ca45b33491f0f2e43eb1000bd623cfb41823"


def check_hash(file_path: Path, sha_hash: str) -> bool:
    """
    Check if the file has the expected sha256 hash.

    :param file_path: The path to the file.
    :param sha_hash: The expected sha256 hash.
    :return: True if the file has the expected hash.
    """
    return sha256(file_path.read_bytes()).hexdigest() == sha_hash


def download_file(url: str, save_dir: Path, sha_hash: str = None) -> Path | None:
    """
    Download a file from a url and return the path to the downloaded file.

    :param url: The url to download the file from.
    :param save_dir: The directory where the file will be saved.
    :param sha_hash: The sha256 hash of the file. If it doesn't match, the download will be aborted.
    :return: The path to the downloaded file.
    """
    response = requests.get(url, stream=True)
    try:
        response.raise_for_status()
    except requests.exceptions.HTTPError as e:
        print(f"Error downloading file from url: {url}\n{e}")
        print("Manually download the file and save the path to it in a profile's settings.")
        return None

    file_name = os.path.basename(url)
    save_path = save_dir / file_name

    # Ensure the file is not already downloaded, and the folder exists.
    save_dir.mkdir(parents=True, exist_ok=True)
    if save_path.is_file():
        save_path.unlink()
    elif save_path.is_dir():
        save_path.rmdir()

    file_size = int(response.headers.get("Content-Length", 0))
    chunk_size = 8192  # 8KB

    with open(save_path, "wb") as f, tqdm.tqdm(total=file_size, unit="B", unit_scale=True) as pbar:
        for chunk in response.iter_content(chunk_size=chunk_size):
            if chunk:
                f.write(chunk)
                pbar.update(len(chunk))

    if not save_path.exists():
        print(f"Error downloading file from url: {url}\nFailed to save the file to {save_path}")
    if sha_hash is not None:
        if not check_hash(save_path, sha_hash):
            print(
                f"Error downloading file from url: {url}\nThe file content is different from expected."
            )
            save_path.unlink()
            return None

    return save_path


def download_torch_model(cache_dir: Path) -> Path | None:
    """
    Download the torch model and return the path to the downloaded file.

    :param cache_dir: The directory where the file will be saved.
    :return: The path to the downloaded file. Or None if the download failed.
    """
    print("Downloading Torch model for CUDA...")
    return download_file(MODEL_URL + TORCH_MODEL_NAME, cache_dir, sha_hash=TORCH_SHA256)


def download_cv2_model(cache_dir: Path) -> Path | None:
    """
    Download the cv2 model and return the path to the downloaded file.

    :param cache_dir: The directory where the file will be saved.
    :return: The path to the downloaded file. Or None if the download failed.
    """
    print("Downloading OpenCV model for CPU...")
    return download_file(MODEL_URL + CV2_MODEL_NAME, cache_dir, sha_hash=CV2_SHA256)


def get_old_inpainting_model_path(config) -> Path:
    """
    Get the path to the inpainting model.

    :return: The path to the inpainting model.
    """
    return config.get_model_cache_dir() / "big-lama.pt"


def get_inpainting_model_path(config) -> Path:
    """
    Get the path to the inpainting model.

    :return: The path to the inpainting model.
    """
    return config.get_model_cache_dir() / "anime-manga-big-lama.pt"


def download_inpainting_model(cache_dir: Path) -> Path | None:
    """
    Download the inpainting model and return the path to the downloaded file.

    :param cache_dir: The directory where the file will be saved.
    :return: The path to the downloaded file. Or None if the download failed.
    """
    print("Downloading inpainting model...")
    return download_file(INPAINTING_URL, cache_dir, sha_hash=INPAINTING_SHA256)


def is_inpainting_downloaded(config) -> bool:
    """
    Check if the inpainting model is downloaded.

    :return: True if the inpainting model is downloaded.
    """
    return get_inpainting_model_path(config).is_file()


def has_old_inpainting_model(config) -> bool:
    """
    Check if the old inpainting model is downloaded.

    :return: True if the old inpainting model is downloaded.
    """
    return get_old_inpainting_model_path(config).is_file()


def check_upgrade_inpainting_model(config) -> None:
    # Check if we have the old version sitting around and offer to
    # delete or keep it.
    if has_old_inpainting_model(config):
        if cu.get_confirmation(
            "A new version of the inpainting model is available.\n"
            "You can delete the model later if you don't want to upgrade yet.\n"
            "Switch to the new model?",
            default=True,
        ):
            get_old_inpainting_model_path(config).unlink()
            download_inpainting_model(config.get_model_cache_dir())
        else:
            print("Old model kept.")
            shutil.move(get_old_inpainting_model_path(config), get_inpainting_model_path(config))
    else:
        download_inpainting_model(config.get_model_cache_dir())


def ensure_inpainting_available(config) -> None:
    """
    Check if it is downloaded, and download it if it isn't.

    :param config: The config to get the cache path from.
    """
    if not is_inpainting_downloaded(config):
        check_upgrade_inpainting_model(config)


def download_models(config, force: bool, cuda: bool, cpu: bool) -> None:
    """
    Download the models and save the paths to them in the config.
    If neither cuda nor cpu is set, use cuda if available.

    :param config: The config to save the paths in.
    :param force: If True, overwrite the paths in the config.
    :param cuda: If True, only download the cuda model.
    :param cpu: If True, only download the cpu model.
    :return:
    """
    if not cuda and not cpu:
        cuda = torch.cuda.is_available()
        cpu = not cuda

    cache_dir = config.get_model_cache_dir()
    # Check if they aren't set already.
    if cuda:
        if force or config.default_torch_model_path is None:
            config.default_torch_model_path = download_torch_model(cache_dir)
        else:
            print(
                f"Skipping Torch model download, path already set to: {config.default_torch_model_path}"
            )
    if cpu:
        if force or config.default_cv2_model_path is None:
            config.default_cv2_model_path = download_cv2_model(cache_dir)
        else:
            print(
                f"Skipping OpenCV model download, path already set to: {config.default_cv2_model_path}"
            )

    config.save()

    # Download the inpainting model.
    ensure_inpainting_available(config)

    # Also load the OCR model, but there is only one option and can't be forced.
    MangaOcr()


def get_ocr_model_directory() -> Path:
    """
    Get the path to the OCR model directory.

    :return: The path to the OCR model directory.
    """
    cache_dir = Path(file_utils.default_cache_path)
    ocr_dir = cache_dir / OCR_DIR_NAME
    return ocr_dir


def is_ocr_downloaded() -> bool:
    """
    Check if the OCR model is downloaded.

    :return: True if the OCR model is downloaded.
    """
    return get_ocr_model_directory().is_dir()


def delete_models(text_detector_cache_dir: Path) -> None:
    """
    Delete the downloaded models.

    :param text_detector_cache_dir: The path to the text detector cache directory.
    """
    ocr_dir = get_ocr_model_directory()
    if ocr_dir.is_dir():
        logger.info(f"Deleting OCR model directory: {ocr_dir}")
        shutil.rmtree(ocr_dir)
    else:
        logger.warning(f"OCR model directory does not exist and cannot be deleted: {ocr_dir}")

    if text_detector_cache_dir.is_dir():
        logger.info(f"Deleting text detector cache directory: {text_detector_cache_dir}")
        shutil.rmtree(text_detector_cache_dir)
