from pathlib import Path

import PySide6.QtCore as Qc
import PySide6.QtGui as Qg
import PySide6.QtWidgets as Qw
from PySide6.QtCore import Signal, Slot
from loguru import logger
import cv2
import numpy as np

import pcleaner.gui.image_viewer as iv


class SwipeViewer(iv.ImageViewer):
    """
    Display 2 images overlayed on top of each other, with a percentage to control the
    point horizontally at which the other image is shown instead.
    """

    image_left: Qw.QGraphicsPixmapItem | None
    image_right: Qw.QGraphicsPixmapItem | None
    raw_image_left: Qg.QImage | None
    raw_image_right: Qg.QImage | None
    swipe_position: int
    slider: Qw.QSlider | None

    def __init__(self, parent=None) -> None:
        super(SwipeViewer, self).__init__(parent)
        self.image_left = None
        self.image_right = None
        self.swipe_position = 0
        self.slider = None

        self.raw_image_left = None
        self.raw_image_right = None

    def set_images(self, left: Path, right: Path) -> None:
        """
        Accept 2 image paths and load them into the viewer.
        """
        self.scene.clear()

        self.image_left = Qw.QGraphicsPixmapItem()
        self.image_right = Qw.QGraphicsPixmapItem()
        self.scene.addItem(self.image_left)
        self.scene.addItem(self.image_right)
        # Set the parent's image item for zoom purposes.
        self.image_item = self.image_left

        self.image_left.setOffset(0, 0)
        self.image_right.setOffset(0, 0)
        # self.image_left.setOffset(-0.5, -0.5)
        # self.image_right.setOffset(-0.5, -0.5)

        self.raw_image_left = Qg.QImage(str(left))
        pixmap = Qg.QPixmap.fromImage(self.raw_image_left)
        self.image_left.setPixmap(pixmap)

        self.raw_image_right = Qg.QImage(str(right))
        pixmap = Qg.QPixmap.fromImage(self.raw_image_right)
        self.image_right.setPixmap(pixmap)

        self.image_dimensions = (
            self.image_item.pixmap().size().width(),
            self.image_item.pixmap().size().height(),
        )

        # Load the pixel dimensions into the slider.
        # The slider holds the exact number of pixels to show on the left side.
        if not self.slider:
            logger.error("Slider not connected to swipe view!")
        else:
            self.slider.setMaximum(self.raw_image_left.width())
            # Start the slider in the middle.
            self.slider.setValue(self.raw_image_left.width() // 2)

        self.update_mask()

    def update_mask(self) -> None:
        """
        Update the mask position based on the percentage.
        """
        if not self.image_left or not self.image_right:
            return

        width = self.raw_image_left.width()
        height = self.raw_image_left.height()

        # Create a new QPixmap for the first image.
        img1_part = self.raw_image_left.copy(0, 0, self.swipe_position, height)
        self.image_left.setPixmap(Qg.QPixmap.fromImage(img1_part))

        # Create a new QPixmap for the second image.
        img2_part = self.raw_image_right.copy(
            self.swipe_position,
            0,
            width - self.swipe_position,
            height,
        )
        self.image_right.setPixmap(Qg.QPixmap.fromImage(img2_part))
        self.image_right.setPos(self.swipe_position, 0)

    def connect_slider(self, slider: Qw.QSlider) -> None:
        self.slider = slider
        slider.valueChanged.connect(self.handle_slider_change)

    @Slot(int)
    def handle_slider_change(self, value: int) -> None:
        """
        Handle the slider value change.
        """
        self.swipe_position = value
        self.update_mask()

    def drawBackground(self, painter, rect) -> None:
        """
        Ignore the direct parent's background drawing,
        going straight to the graphicsview's function.
        """
        super(iv.ImageViewer, self).drawBackground(painter, rect)

    def set_transformation_mode(self, mode: Qc.Qt.TransformationMode) -> None:
        self.image_left.setTransformationMode(mode)
        self.image_right.setTransformationMode(mode)

    def drawForeground(self, painter, rect) -> None:
        # Draw a vertical line at the swipe position
        if self.image_left and self.image_right:
            # Get highlight color from the palette.
            highlight_color = self.palette().highlight().color()
            painter.setPen(Qg.QPen(highlight_color, 2))
            painter.drawLine(
                self.swipe_position, 0, self.swipe_position, self.raw_image_left.height()
            )


class OnionViewer(iv.ImageViewer):
    """
    Display 2 images overlayed on top of each other, with a percentage to control the
    transparency of the top image.
    """

    lower_image: Qw.QGraphicsPixmapItem | None
    upper_image: Qw.QGraphicsPixmapItem | None
    alpha: float
    slider: Qw.QSlider | None

    def __init__(self, parent=None) -> None:
        super(OnionViewer, self).__init__(parent)
        self.lower_image = None
        self.upper_image = None
        self.alpha = 0.5
        self.slider = None

    def set_images(self, lower: Path, upper: Path) -> None:
        """
        Accept 2 image paths and load them into the viewer.
        """
        self.scene.clear()

        self.lower_image = Qw.QGraphicsPixmapItem()
        self.upper_image = Qw.QGraphicsPixmapItem()
        self.scene.addItem(self.lower_image)
        self.scene.addItem(self.upper_image)
        # Set the parent's image item for zoom purposes.
        self.image_item = self.lower_image

        self.lower_image.setOffset(-0.5, -0.5)
        self.upper_image.setOffset(-0.5, -0.5)

        lower_image = Qg.QImage(str(lower))
        pixmap = Qg.QPixmap.fromImage(lower_image)
        self.lower_image.setPixmap(pixmap)

        upper_image = Qg.QImage(str(upper))
        pixmap = Qg.QPixmap.fromImage(upper_image)
        self.upper_image.setPixmap(pixmap)

        self.image_dimensions = (
            self.image_item.pixmap().size().width(),
            self.image_item.pixmap().size().height(),
        )

        self.update_alpha()

    def update_alpha(self) -> None:
        if self.lower_image and self.upper_image:
            self.upper_image.setOpacity(self.alpha)

    def connect_slider(self, slider: Qw.QSlider) -> None:
        # Make the slider a percentage and start it at 50%.
        self.slider = slider
        slider.setMaximum(100)
        slider.valueChanged.connect(self.handle_slider_change)
        slider.setValue(50)

    @Slot(int)
    def handle_slider_change(self, value: int) -> None:
        self.alpha = value / 100
        self.update_alpha()


class DifferenceViewer(iv.ImageViewer):
    """
    Display 2 images overlaid on top of each other with the difference filter applied.
    An additional slider controls the opacity of the overlay.
    """

    lower_image: Qw.QGraphicsPixmapItem | None
    upper_image: Qw.QGraphicsPixmapItem | None
    alpha: float
    slider: Qw.QSlider | None

    def __init__(self, parent=None) -> None:
        super(DifferenceViewer, self).__init__(parent)
        self.lower_image = None
        self.upper_image = None
        self.alpha = 0.0
        self.slider = None

    def set_images(self, lower: Path, upper: Path) -> None:
        """
        Accept 2 image paths and load them into the viewer, applying the difference filter.
        """
        self.scene.clear()

        self.lower_image = Qw.QGraphicsPixmapItem()
        self.upper_image = Qw.QGraphicsPixmapItem()
        self.scene.addItem(self.lower_image)
        self.scene.addItem(self.upper_image)
        # Set the parent's image item for zoom purposes.
        self.image_item = self.lower_image

        self.lower_image.setOffset(-0.5, -0.5)
        self.upper_image.setOffset(-0.5, -0.5)

        lower_image = cv2.imread(str(lower))
        upper_image = cv2.imread(str(upper))

        # Apply the difference filter using OpenCV
        difference_image = cv2.absdiff(lower_image, upper_image)

        # Convert back to QPixmap for display
        lower_pixmap = self.cv2_to_pixmap(lower_image)
        upper_pixmap = self.cv2_to_pixmap(difference_image)

        self.lower_image.setPixmap(lower_pixmap)
        self.upper_image.setPixmap(upper_pixmap)

        self.image_dimensions = (
            self.image_item.pixmap().size().width(),
            self.image_item.pixmap().size().height(),
        )

        self.update_alpha()

    def cv2_to_pixmap(self, cv2_img) -> Qg.QPixmap:
        """
        Convert an OpenCV image to QPixmap.
        """
        height, width, channel = cv2_img.shape
        bytes_per_line = 3 * width
        q_img = Qg.QImage(
            cv2_img.data, width, height, bytes_per_line, Qg.QImage.Format_RGB888
        ).rgbSwapped()
        return Qg.QPixmap.fromImage(q_img)

    def update_alpha(self) -> None:
        if self.lower_image and self.upper_image:
            self.upper_image.setOpacity(self.alpha)

    def connect_slider(self, slider: Qw.QSlider) -> None:
        # Make the slider a percentage and start it at 85%.
        self.slider = slider
        slider.setMaximum(100)
        slider.valueChanged.connect(self.handle_slider_change)
        slider.setValue(85)

    @Slot(int)
    def handle_slider_change(self, value: int) -> None:
        self.alpha = value / 100
        self.update_alpha()


class OverlayViewer(iv.ImageViewer):
    """
    Display 2 images overlaid on top of each other where the upper image is recolored to a solid color and the opacity is controlled by a slider.
    """

    lower_image: Qw.QGraphicsPixmapItem | None
    upper_image: Qw.QGraphicsPixmapItem | None
    alpha: float
    slider: Qw.QSlider | None
    recolor: tuple[int, int, int, int]

    def __init__(self, parent=None) -> None:
        super(OverlayViewer, self).__init__(parent)
        self.lower_image = None
        self.upper_image = None
        self.alpha = 0.5
        self.slider = None
        self.recolor = (255, 0, 0, 0)  # Default recolor to red

    def set_images(
        self, lower: Path, masks: list[Path], mask_color: tuple[int, int, int, int]
    ) -> None:
        """
        Accept 2 image paths and load them into the viewer.
        """
        self.scene.clear()

        self.lower_image = Qw.QGraphicsPixmapItem()
        self.upper_image = Qw.QGraphicsPixmapItem()
        self.scene.addItem(self.lower_image)
        self.scene.addItem(self.upper_image)
        self.recolor = mask_color
        # Set the parent's image item for zoom purposes.
        self.image_item = self.lower_image

        self.lower_image.setOffset(-0.5, -0.5)
        self.upper_image.setOffset(-0.5, -0.5)

        # lower_image = cv2.imread(str(lower))
        lower_image = Qg.QImage(str(lower))
        lower_pixmap = Qg.QPixmap.fromImage(lower_image)
        self.lower_image.setPixmap(lower_pixmap)

        # Merge masks
        merged_mask = self.merge_masks(masks)

        # Apply recolor to the merged mask while preserving the alpha channel
        recolored_image = self.recolor_image(merged_mask, self.recolor)

        # Convert OpenCV images to QPixmap
        upper_pixmap = self.cv2_to_pixmap(recolored_image)
        self.upper_image.setPixmap(upper_pixmap)

        self.image_dimensions = (
            self.image_item.pixmap().size().width(),
            self.image_item.pixmap().size().height(),
        )

        self.update_alpha()

    @staticmethod
    def merge_masks(masks: list[Path]) -> np.ndarray:
        """
        Merge multiple mask images into one by adding them together.
        """
        merged_mask = None

        for mask_path in masks:
            mask_image = cv2.imread(
                str(mask_path), cv2.IMREAD_UNCHANGED
            )  # Ensure alpha channel is loaded
            if merged_mask is None:
                merged_mask = np.zeros_like(mask_image, dtype=np.uint8)

            # Add the current mask to the merged mask
            merged_mask = cv2.add(merged_mask, mask_image)

        return merged_mask

    @staticmethod
    def recolor_image(image: np.ndarray, color: tuple) -> np.ndarray:
        """
        Recolor the given image to the specified solid color while preserving the alpha channel.
        """
        # OpenCV uses BGR instead of RGB.
        b, g, r, a = cv2.split(image)
        recolored_image = np.zeros_like(image)
        recolored_image[:, :, 0] = color[2]  # B channel
        recolored_image[:, :, 1] = color[1]  # G channel
        recolored_image[:, :, 2] = color[0]  # R channel
        recolored_image[:, :, 3] = a  # Alpha channel
        return recolored_image

    @staticmethod
    def cv2_to_pixmap(cv2_img: np.ndarray) -> Qg.QPixmap:
        """
        Convert an OpenCV image to QPixmap.
        """
        height, width, channel = cv2_img.shape
        bytes_per_line = channel * width
        q_img = Qg.QImage(
            cv2_img.data,
            width,
            height,
            bytes_per_line,
            Qg.QImage.Format_ARGB32 if channel == 4 else Qg.QImage.Format_RGB888,
        )
        return Qg.QPixmap.fromImage(q_img)

    def update_alpha(self) -> None:
        if self.lower_image and self.upper_image:
            self.upper_image.setOpacity(self.alpha)

    def connect_slider(self, slider: Qw.QSlider) -> None:
        # Make the slider a percentage and start it at 50%.
        self.slider = slider
        slider.setMaximum(100)
        slider.valueChanged.connect(self.handle_slider_change)
        slider.setValue(50)

    @Slot(int)
    def handle_slider_change(self, value: int) -> None:
        self.alpha = value / 100
        self.update_alpha()