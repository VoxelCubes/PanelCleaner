import os
import os.path as osp
import glob
from pathlib import Path
import cv2
import numpy as np
import json
from loguru import logger

IMG_EXT = [".jpeg", ".jpg", ".png", ".bmp", ".tiff", ".tif", ".jp2", ".dib", ".webp", ".ppm"]

# Guard for numpy version compatibility
from packaging import version

np_version = version.parse(np.__version__)

if np_version >= version.parse("2.0.0"):
    NP_BOOL_TYPES = (np.bool_,)
    NP_FLOAT_TYPES = (np.float16, np.float32, np.float64)
else:
    NP_BOOL_TYPES = (np.bool_, np.bool8)
    NP_FLOAT_TYPES = (np.float_, np.float16, np.float32, np.float64)
    logger.info("Using numpy <2.0.0 compatible types for boolean and float.")

NP_INT_TYPES = (
    np.int_,
    np.int8,
    np.int16,
    np.int32,
    np.int64,
    np.uint,
    np.uint8,
    np.uint16,
    np.uint32,
    np.uint64,
)


# https://stackoverflow.com/questions/26646362/numpy-array-is-not-json-serializable
class NumpyEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        elif isinstance(obj, np.ScalarType):
            if isinstance(obj, NP_BOOL_TYPES):
                return bool(obj)
            elif isinstance(obj, NP_FLOAT_TYPES):
                return float(obj)
            elif isinstance(obj, NP_INT_TYPES):
                return int(obj)
        return json.JSONEncoder.default(self, obj)


def find_all_imgs(img_dir, abs_path=False):
    imglist = list()
    for filep in glob.glob(osp.join(img_dir, "*")):
        filename = osp.basename(filep)
        file_suffix = Path(filename).suffix
        if file_suffix.lower() not in IMG_EXT:
            continue
        if abs_path:
            imglist.append(filep)
        else:
            imglist.append(filename)
    return imglist


imread = lambda imgpath, read_type=cv2.IMREAD_COLOR: cv2.imdecode(
    np.fromfile(imgpath, dtype=np.uint8), read_type
)
# def imread(imgpath, read_type=cv2.IMREAD_COLOR):
#     img = cv2.imdecode(np.fromfile(imgpath, dtype=np.uint8), read_type)
#     return img


def imwrite(img_path, img, ext=".png"):
    suffix = Path(img_path).suffix
    if suffix != "":
        img_path = img_path.replace(suffix, ext)
    else:
        img_path += ext
    cv2.imencode(ext, img)[1].tofile(img_path)
