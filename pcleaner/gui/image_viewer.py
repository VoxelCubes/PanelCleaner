from pathlib import Path

import PySide6.QtCore as Qc
import PySide6.QtGui as Qg
import PySide6.QtWidgets as Qw
from loguru import logger


ZOOM_TICK_FACTOR = 1.25


class ImageViewer(Qw.QGraphicsView):
    mouseMoved = Qc.Signal(int, int)
    image_dimensions: tuple[int, int] | None
    image_item: Qw.QGraphicsPixmapItem | None

    def __init__(self, parent=None) -> None:
        super(ImageViewer, self).__init__(parent)
        self.setRenderHint(Qg.QPainter.Antialiasing)

        # Scene for QGraphicsView
        self.scene = Qw.QGraphicsScene(self)
        self.setScene(self.scene)

        self.image_item = None
        # Disable the allocation limit for high resolution images.
        Qg.QImageReader.setAllocationLimit(0)

        self.zoom_factor = 1.0
        self.setAlignment(Qc.Qt.AlignCenter)

        self.setMouseTracking(True)

    def pixmap_valid(self) -> bool:
        return self.image_item is not None and self.image_item.pixmap().isNull()

    def set_image(self, image_path: Path = None) -> None:
        if image_path:
            self.scene.clear()
            self.image_item = Qw.QGraphicsPixmapItem()
            self.scene.addItem(self.image_item)
            # Move the image item by -0.5, -0.5 to make it align with the scene's
            # origin (0, 0).
            self.image_item.setOffset(-0.5, -0.5)

            image = Qg.QImage(str(image_path))
            pixmap = Qg.QPixmap.fromImage(image)
            self.image_item.setPixmap(pixmap)
            self.setSceneRect(pixmap.rect())
            dim = self.image_item.pixmap().size()
            self.image_dimensions = (dim.width(), dim.height())
            self.zoom(1)

        else:
            # Display "nothing" message when no image is set
            self.scene.clear()
            self.image_dimensions = None
            self.image_item = None

    def wheelEvent(self, event: Qg.QWheelEvent) -> None:
        if Qc.Qt.ControlModifier & event.modifiers():
            # Zoom in/out with Ctrl + mouse wheel
            if event.angleDelta().y() > 0:
                self.zoom_in(wheel=True)
            else:
                self.zoom_out(wheel=True)
        elif Qc.Qt.ShiftModifier & event.modifiers():
            # Horizontal scrolling with Shift + mouse wheel
            self.horizontalScrollBar().setValue(
                self.horizontalScrollBar().value() - event.angleDelta().y()
            )
        else:
            # Default behavior for panning
            super().wheelEvent(event)

    # For the mouse wheel events, we want to zoom slower.
    # Since zooming applies a factor, we can use a root of the factor to
    # achieve half of a zoom step.
    def zoom_in(self, wheel=False) -> None:
        if wheel:
            self.zoom(ZOOM_TICK_FACTOR**0.5)
        else:
            self.zoom(ZOOM_TICK_FACTOR)

    def zoom_out(self, wheel=False) -> None:
        if wheel:
            self.zoom(1 / (ZOOM_TICK_FACTOR**0.5))
        else:
            self.zoom(1 / ZOOM_TICK_FACTOR)

    def zoom_reset(self) -> None:
        self.zoom_factor = 1.0
        self.zoom(1)

    def zoom_fit(self) -> None:
        if self.image_dimensions is None:
            return
        width, height = self.image_dimensions
        view_width, view_height = self.viewport().width(), self.viewport().height()
        width_factor = view_width / width
        height_factor = view_height / height
        self.zoom_factor = min(width_factor, height_factor)
        # logger.debug(
        #     f"Zoom to fit with factor: {self.zoom_factor:.2%} for view size {view_width}x{view_height} and image size {width}x{height}"
        # )
        self.zoom(1)

    def image_position(self, pos) -> Qc.QPoint:
        return self.mapToScene(pos).toPoint()

    def mouseMoveEvent(self, event) -> None:
        if self.pixmap_valid():
            return
        # Call base class implementation for standard behavior
        super().mouseMoveEvent(event)
        # Emit the mouse position always
        image_pos = self.image_position(event.pos())
        self.mouseMoved.emit(image_pos.x(), image_pos.y())
        self.viewport().update()  # Request redraw for the pixel highlight

    def drawForeground(self, painter, rect) -> None:
        if not self.pixmap_valid() and self.zoom_factor > 5:
            view_pos = self.mapFromGlobal(Qg.QCursor.pos())
            image_pos = self.mapToScene(view_pos).toPoint()

            # Check if the cursor is inside the pixmap area
            if self.image_item.pixmap().rect().contains(image_pos):
                # Decide the color for the square
                pixel_color = self.image_item.pixmap().toImage().pixelColor(image_pos)
                avg = (pixel_color.red() + pixel_color.green() + pixel_color.blue()) / 3
                square_color = Qc.Qt.white if avg < 128 else Qc.Qt.black

                painter.setPen(Qg.QPen(square_color, 1 / self.zoom_factor))
                rect = Qc.QRectF(image_pos.x() - 0.5, image_pos.y() - 0.5, 1, 1)
                scaled_rect = rect.adjusted(
                    -0.5 / self.zoom_factor,
                    -0.5 / self.zoom_factor,
                    0.5 / self.zoom_factor,
                    0.5 / self.zoom_factor,
                )
                painter.drawRect(scaled_rect)

    def zoom(self, factor) -> None:
        """
        Zoom the image by the given factor.
        The image may not exceed a scale of 100x or have both width and height be smaller
        than half of the viewport's width and height.

        :param factor: The factor to multiply the current zoom factor by.
        """
        proposed_zoom_factor = self.zoom_factor * factor
        proposed_zoom_factor = min(proposed_zoom_factor, 100)

        current_width, current_height = (
            self.image_item.pixmap().width(),
            self.image_item.pixmap().height(),
        )
        proposed_width, proposed_height = (
            current_width * proposed_zoom_factor,
            current_height * proposed_zoom_factor,
        )
        view_width, view_height = self.viewport().width(), self.viewport().height()

        # Don't zoom out further if it's getting too smol.
        if proposed_width < view_width / 2 and proposed_height < view_height / 2 and factor < 1:
            return

        self.zoom_factor = proposed_zoom_factor

        if self.zoom_factor >= 2:
            self.setRenderHint(Qg.QPainter.SmoothPixmapTransform, False)
            self.image_item.setTransformationMode(Qc.Qt.FastTransformation)
        else:
            self.setRenderHint(Qg.QPainter.SmoothPixmapTransform, True)
            self.image_item.setTransformationMode(Qc.Qt.SmoothTransformation)
        self.setTransform(Qg.QTransform().scale(self.zoom_factor, self.zoom_factor))

    def reset_zoom(self) -> None:
        self.zoom_factor = 1
        self.setTransform(Qg.QTransform().scale(self.zoom_factor, self.zoom_factor))
