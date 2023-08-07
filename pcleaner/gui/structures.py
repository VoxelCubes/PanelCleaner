from pathlib import Path
import io

import PySide6.QtCore as Qc
import PySide6.QtGui as Qg
import PySide6.QtWidgets as Qw
from PySide6.QtCore import Slot
from logzero import logger
from PIL import Image

import pcleaner.config as cfg
from .CustomQ.CTableWidget import CTableWidget
import pcleaner.helpers as hp
from attrs import define


# The max size used for the icon and large thumbnail.
THUMBNAIL_SIZE = 44, 44


class ImageFile:
    """
    This class represents an image file.
    """

    path: Path  # Path to the image file.
    icon: Qg.QIcon  # Placeholder icon for the image type.
    # The following attributes are lazy-loaded.
    image: Image = None  # Image object. (Image doesn't like the union operator)
    thumbnail: Qg.QPixmap | None = None  # Thumbnail of the image, used as the icon.
    size: tuple[int, int] | None = None  # Size of the image.

    path_ai_mask: Path | None = None
    path_initial_boxes: Path | None = None
    path_final_boxes: Path | None = None
    path_box_mask: Path | None = None
    path_cut_mask: Path | None = None
    path_mask_layers: Path | None = None
    path_final_mask: Path | None = None
    path_masked_image: Path | None = None
    path_denoiser_mask: Path | None = None
    path_denoised_image: Path | None = None

    error: Exception | None = None  # Error that occurred during any process.

    def __init__(self, path: Path):
        """
        Init the image file.

        :param path: Path to the image file.
        """
        self.path = path
        self.icon = Qg.QIcon.fromTheme(cfg.SUFFIX_TO_ICON[path.suffix.lower()])

    @property
    def size_str(self) -> str:
        """
        Returns the size of the image as a string.
        """
        if self.size is None:
            return "Unknown"
        return f"{self.size[0]:n} × {self.size[1]:n}"

    def data_loaded(self) -> bool:
        """
        Returns whether the lazily-loaded image data is ready.
        """
        return self.image is not None and self.thumbnail is not None and self.size is not None

    def load_image(self) -> Path:
        """
        Loads the image data.

        :return: Path to the image file so that the callback knows which image was loaded.
        """
        self.image = Image.open(self.path)
        self.size = self.image.size
        # Shrink the image down to a thumbnail size to reduce memory usage.
        # Then it converts it to a QPixmap for use as an icon.
        thumbnail = self.image.copy()
        thumbnail.thumbnail(THUMBNAIL_SIZE)
        if thumbnail.mode == "CMYK":
            thumbnail = thumbnail.convert("RGB")
        byte_data = io.BytesIO()
        thumbnail.save(byte_data, format="PNG")
        byte_data.seek(0)
        qimage = Qg.QPixmap()
        # noinspection PyTypeChecker
        qimage.loadFromData(byte_data.read(), "PNG")
        self.thumbnail = qimage

        return self.path
