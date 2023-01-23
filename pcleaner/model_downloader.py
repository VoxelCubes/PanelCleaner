import os
from pathlib import Path
from hashlib import sha256

import requests
import tqdm
import torch


MODEL_URL = "https://github.com/zyddnys/manga-image-translator/releases/download/beta-0.3/"
TORCH_MODEL_NAME = "comictextdetector.pt"
TORCH_SHA256 = "1f90fa60aeeb1eb82e2ac1167a66bf139a8a61b8780acd351ead55268540cccb"
CV2_MODEL_NAME = "comictextdetector.pt.onnx"
CV2_SHA256 = "1a86ace74961413cbd650002e7bb4dcec4980ffa21b2f19b86933372071d718f"


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


def download_models(config, force: bool, cuda: bool, cpu: bool):
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
