import platform
import subprocess
from math import ceil
from pathlib import Path

from logzero import logger


def f_plural(value, singular: str, plural: str):
    """
    Selects which form to use based on the value.
    """
    return singular if value == 1 else plural


def scale_length_rounded(size: int, scale: float) -> int:
    """
    Scale the given size by the given scale.
    Round up to prevent nulling small values.

    :param size: Size to scale.
    :param scale: Scale factor.
    :return: Scaled size.
    """
    return ceil(size * scale)


def scale_area_rounded(area: int, scale: float) -> int:
    """
    Scale the given area by the given scale.
    Round up to prevent nulling small values.

    :param area: Area to scale.
    :param scale: Scale factor.
    :return: Scaled area.
    """
    return ceil(area * scale * scale)


def open_file(path: Path):
    """
    Open any given file with the default application.
    """
    logger.info(f"Opening file {path}")
    try:
        if platform.system() == "Linux":
            subprocess.run(["xdg-open", path])
        elif platform.system() == "Windows":
            subprocess.run(["start", path])
        elif platform.system() == "Darwin":
            subprocess.run(["open", path])
    except Exception as e:
        logger.exception(e)
