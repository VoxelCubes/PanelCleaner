from pathlib import Path
from importlib import resources

import PySide6.QtCore as Qc
from PySide6.QtCore import Qt
import PySide6.QtGui as Qg
import PySide6.QtWidgets as Qw
from PySide6.QtCore import Signal, Slot
from loguru import logger

import pcleaner.data
import pcleaner.gui.structures as gst
import pcleaner.helpers as hp

ZOOM_TICK_FACTOR = 1.25


class ImageViewer(Qw.QGraphicsView):
    mouseMoved = Qc.Signal(int, int)
    image_dimensions: tuple[int, int] | None
    image_item: Qw.QGraphicsPixmapItem | None
    # Share the pixmap within the image item to optimize multiple viewers
    # of the same image (as with the diff viewers).
    shared_pixmap: gst.Shared[Qg.QPixmap | None] | None

    loaded_image_path: Path | None

    # We want to emit when the zoom factor changes,
    # and also receive them.
    zoom_factor_changed = Signal(float)
    # Slot: set_zoom_factor = Slot(float)

    def __init__(self, parent=None) -> None:
        super(ImageViewer, self).__init__(parent)
        self.setRenderHint(Qg.QPainter.Antialiasing)

        # Scene for QGraphicsView
        self.scene = Qw.QGraphicsScene(self)
        self.setScene(self.scene)

        self.image_item = None
        self.image_dimensions = None
        self.loaded_image_path = None
        self.shared_pixmap = None
        # Disable the allocation limit for high resolution images.
        Qg.QImageReader.setAllocationLimit(0)

        self.zoom_factor = 1.0
        self.setAlignment(Qt.AlignCenter)

        # I'm confused as to what this is supposed to do.
        # Docs say this will prevent it from receiving mouse move events when no button
        # is pressed, but it somehow still does. Is it overridden somewhere??
        self.setMouseTracking(False)

        # Make zooming focus on mouse.
        self.setTransformationAnchor(Qw.QGraphicsView.ViewportAnchor.AnchorUnderMouse)

    def share_pixmap_container(self, container: gst.Shared) -> None:
        """
        Accept a shared container to deduplicate pixmap loads in memory.

        :param container: A sharable container.
        """
        self.shared_pixmap = container

    @Slot(float)
    def set_zoom_factor(self, factor: float) -> None:
        self.zoom_factor = factor
        self.zoom(1, suppress_signals=True)

    def pixmap_invalid(self) -> bool:
        return self.image_item is None or (
            self.image_item is not None and self.image_item.pixmap().isNull()
        )

    def load_cache_aware(self, image_path: Path) -> Qg.QPixmap:
        # If a container is provided, use that, or fill it if it's empty.
        if (
            self.shared_pixmap is None
            or self.shared_pixmap.is_none()
            or self.shared_pixmap.get().isNull()
        ):
            image = load_image_with_orientation(image_path)
            pixmap = Qg.QPixmap.fromImage(image)
            if self.shared_pixmap is not None:
                self.shared_pixmap.set(pixmap)
        else:
            pixmap = self.shared_pixmap.get()
        return pixmap

    def set_image(self, image_path: Path = None) -> None:
        self.loaded_image_path = image_path

        if image_path:
            self.scene.clear()
            self.image_item = Qw.QGraphicsPixmapItem()
            self.scene.addItem(self.image_item)
            # Move the image item by -0.5, -0.5 to make it align with the scene's
            self.image_item.setOffset(-0.5, -0.5)

            pixmap = self.load_cache_aware(image_path)
            self.image_item.setPixmap(pixmap)
            self.reset_scene_rect()
            dim = self.image_item.pixmap().size()
            self.image_dimensions = (dim.width(), dim.height())
            self.update_smoothing()
        else:
            # Display "nothing" message when no image is set
            self.scene.clear()
            self.image_dimensions = None
            self.image_item = None

    def reset_scene_rect(self) -> None:
        self.setSceneRect(self.image_item.pixmap().rect())

    def update_smoothing(self) -> None:
        # Do no smoothing if zooming is, so when a pixel covers more than 1 pixel.
        if self.zoom_factor > 1:
            self.setRenderHint(Qg.QPainter.SmoothPixmapTransform, False)
            self.set_transformation_mode(Qt.FastTransformation)
        else:
            self.setRenderHint(Qg.QPainter.SmoothPixmapTransform, True)
            self.set_transformation_mode(Qt.SmoothTransformation)

    def wheelEvent(self, event: Qg.QWheelEvent) -> None:
        if Qt.ControlModifier & event.modifiers():
            # Zoom in/out with Ctrl + mouse wheel
            if event.angleDelta().y() > 0:
                self.zoom_in(wheel=True)
            else:
                self.zoom_out(wheel=True)
        elif Qt.ShiftModifier & event.modifiers():
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
        if self.pixmap_invalid():
            return
        # Call base class implementation for standard behavior
        super().mouseMoveEvent(event)
        # Emit the mouse position always
        image_pos = self.image_position(event.pos())
        self.mouseMoved.emit(image_pos.x(), image_pos.y())
        self.viewport().update()  # Request redraw for the pixel highlight

    def drawForeground(self, painter, rect) -> None:
        if not self.pixmap_invalid() and self.zoom_factor > 5:
            view_pos = self.mapFromGlobal(Qg.QCursor.pos())
            image_pos = self.mapToScene(view_pos).toPoint()

            # Check if the cursor is inside the pixmap area
            if self.image_item.pixmap().rect().contains(image_pos):
                # Decide the color for the square
                pixel_color = self.image_item.pixmap().toImage().pixelColor(image_pos)
                avg = (pixel_color.red() + pixel_color.green() + pixel_color.blue()) / 3
                square_color = Qt.white if avg < 128 else Qt.black

                painter.setPen(Qg.QPen(square_color, 1 / self.zoom_factor))
                rect = Qc.QRectF(image_pos.x() - 0.5, image_pos.y() - 0.5, 1, 1)
                scaled_rect = rect.adjusted(
                    -0.5 / self.zoom_factor,
                    -0.5 / self.zoom_factor,
                    0.5 / self.zoom_factor,
                    0.5 / self.zoom_factor,
                )
                painter.drawRect(scaled_rect)

    def drawBackground(self, painter, rect) -> None:
        super().drawBackground(painter, rect)  # Call the base class implementation
        if not self.pixmap_invalid():
            image_rect = self.image_item.boundingRect()
            bg_color = self.palette().highlight().color()
            # If the color is really dark, use a lighter color for the background and vice versa.
            if bg_color.lightness() < 40:
                bg_color = bg_color.lighter(110)
            else:
                bg_color = bg_color.darker(110)
            painter.setBrush(bg_color)
            painter.drawRect(image_rect)

    def zoom(self, factor: float, *, suppress_signals: bool = False) -> None:
        """
        Zoom the image by the given factor.
        The image may not exceed a scale of 100x or have both width and height be smaller
        than half of the viewport's width and height.

        In the even that this was called as a callback, we can suppress the signal.

        :param factor: The factor to multiply the current zoom factor by.
        :param suppress_signals: Whether to suppress the zoom factor changed signal.
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

        self.update_smoothing()
        self.setTransform(Qg.QTransform().scale(self.zoom_factor, self.zoom_factor))

        if not suppress_signals:
            self.zoom_factor_changed.emit(self.zoom_factor)

    def reset_zoom(self) -> None:
        self.zoom_factor = 1
        self.setTransform(Qg.QTransform().scale(self.zoom_factor, self.zoom_factor))
        self.zoom_factor_changed.emit(self.zoom_factor)

    def set_transformation_mode(self, mode: Qt.TransformationMode) -> None:
        """
        This function is broken out to allow subclasses with 2 images to
        apply the transformation mode to both images.

        :param mode: The transformation mode to apply.
        """

        self.image_item.setTransformationMode(mode)


class BubbleImageViewer(ImageViewer):
    """
    An ImageViewer that can draw (rectangular) bubbles on the image.
    """

    # These lists must all have the same length.
    bubbles: list[Qc.QRect]
    bubble_colors: list[Qg.QColor]
    bubble_labels: list[str]
    bubble_stroke: list[Qt.PenStyle]  # DashLine or SolidLine etc.

    allow_drawing_bubble: bool
    new_bubble_color: Qg.QColor

    _new_bubble_start: Qc.QPoint | None
    _new_bubble_end: Qc.QPoint | None
    new_bubble: Signal = Signal(Qc.QRect)
    bubble_clicked: Signal = Signal(int)  # The index of the bubble clicked.

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.bubbles = []
        self.bubble_colors = []
        self.bubble_labels = []
        self.bubble_stroke = []
        self.allow_drawing_bubble = False
        # Default new bubble color to palette highlight color.
        self.new_bubble_color = self.palette().highlight().color()

        self._new_bubble_start = None
        self._new_bubble_end = None

        # Load included font.
        font_path = hp.resource_path(pcleaner.data, "LiberationSans-Regular.ttf")
        font_id = Qg.QFontDatabase.addApplicationFont(str(font_path))
        if font_id == -1:
            logger.error("Failed to load font.")
            self.font_name = None
        else:
            self.font_name = Qg.QFontDatabase.applicationFontFamilies(font_id)[0]

    def set_allow_drawing_bubble(self, allow: bool) -> None:
        self.allow_drawing_bubble = allow

    def set_new_bubble_color(self, color: Qg.QColor) -> None:
        self.new_bubble_color = color

    def clear_bubbles(self) -> None:
        self.bubbles.clear()
        self.bubble_colors.clear()
        self.bubble_labels.clear()
        self.bubble_stroke.clear()
        self.viewport().update()

    def set_bubbles(
        self,
        rects: list[Qc.QRect],
        colors: list[Qg.QColor],
        labels: list[str],
        strokes: list[Qt.PenStyle],
    ) -> None:
        self.bubbles = rects
        self.bubble_colors = colors
        self.bubble_labels = labels
        self.bubble_stroke = strokes
        self.viewport().update()

    def point_in_image(self, point: Qc.QPoint) -> bool:
        if self.image_item is None:
            return False
        return self.image_item.pixmap().rect().contains(point)

    def point_in_a_bubble(self, point: Qc.QPoint) -> int:
        """
        Figure out if any of the bubbles contain this point.

        :param point: The point to check.
        :return: The index of the bubble that contains the point, or -1 if none do.
        """
        for i, bubble in enumerate(self.bubbles):
            if bubble.contains(point):
                return i
        return -1

    def mousePressEvent(self, event: Qg.QMouseEvent) -> None:
        # Begin drawing a new bubble, if allowed.
        if self.allow_drawing_bubble:
            # Discard boxes that are started outside the image.
            if self.point_in_image(self.image_position(event.pos())):
                self._new_bubble_start = self.image_position(event.pos())
                self.setCursor(Qt.CrossCursor)
        else:
            # Check if a bubble was clicked.
            bubble_index = self.point_in_a_bubble(self.image_position(event.pos()))
            self.bubble_clicked.emit(bubble_index)
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event: Qg.QMouseEvent) -> None:
        if self.allow_drawing_bubble and self._new_bubble_start is not None:
            self._new_bubble_end = self.image_position(event.pos())
            self.viewport().update()
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: Qg.QMouseEvent) -> None:
        # Finish drawing the bubble and emit the new bubble signal.
        if self.allow_drawing_bubble and self._new_bubble_start is not None:
            self._new_bubble_end = self.image_position(event.pos())
            if self.point_in_image(self._new_bubble_end):
                # Construct a positively sized QRect.
                # Qc.QRect(self._new_bubble_start, self._new_bubble_end)
                rect = Qc.QRect(
                    min(self._new_bubble_start.x(), self._new_bubble_end.x()),
                    min(self._new_bubble_start.y(), self._new_bubble_end.y()),
                    abs(self._new_bubble_end.x() - self._new_bubble_start.x()),
                    abs(self._new_bubble_end.y() - self._new_bubble_start.y()),
                )
                self.new_bubble.emit(rect)
                logger.debug(
                    f"New bubble drawn: {Qc.QRect(self._new_bubble_start, self._new_bubble_end)}"
                )
            self._new_bubble_start = None
            self._new_bubble_end = None
            self.viewport().update()
            self.setCursor(Qt.ArrowCursor)
        super().mouseReleaseEvent(event)

    def drawForeground(self, painter, rect) -> None:
        if self.image_item is None:
            return
        # Don't call super's function, we don't want the pixel highlight.

        # Use the included font for drawing bubble labels.
        font_size = int(self.image_dimensions[0] / 55) + 5  # Adjusted for scuffed Qt drawing.
        if self.font_name is not None:
            paint_font = Qg.QFont(self.font_name, font_size)
        else:
            paint_font = Qg.QFont("Arial", font_size)
        painter.setFont(paint_font)

        for bubble, color, label, stroke in zip(
            self.bubbles, self.bubble_colors, self.bubble_labels, self.bubble_stroke
        ):
            # Skip bubbles that have -1 for all coordinates. These are created when importing
            # plain text OCR data, which doesn't have box data.
            if (
                bubble.x() == -1
                and bubble.y() == -1
                and bubble.width() == 0
                and bubble.height() == 0
            ):
                continue
            # Draw the bubble with a solid outline and a fill at 48/255 opacity.
            painter.setPen(Qg.QPen(color, 1, stroke, j=Qt.PenJoinStyle.MiterJoin))
            painter.setBrush(Qg.QColor(color.red(), color.green(), color.blue(), 48))
            painter.drawRect(bubble)

            # Draw the label with a white outline.
            path = Qg.QPainterPath()
            path.addText(
                bubble.topLeft() - Qc.QPoint(int(-font_size * 0.1), int(font_size * 0.2)),
                paint_font,
                label,
            )

            outline_pen = Qg.QPen(Qt.white, 5, j=Qt.PenJoinStyle.RoundJoin)
            painter.setPen(outline_pen)
            painter.drawPath(path)

            text_pen = Qg.QPen(color)
            painter.setPen(text_pen)
            painter.fillPath(path, text_pen.color())

        if self._new_bubble_start is not None and self._new_bubble_end is not None:
            # Use double the opacity for the new bubble to make it more visible.
            painter.setPen(Qg.QPen(self.new_bubble_color, 1, Qt.DashLine))
            painter.setBrush(
                Qg.QColor(
                    self.new_bubble_color.red(),
                    self.new_bubble_color.green(),
                    self.new_bubble_color.blue(),
                    48 * 2,
                )
            )
            painter.drawRect(Qc.QRect(self._new_bubble_start, self._new_bubble_end))


def load_image_with_orientation(image_path: Path | str) -> Qg.QImage:
    """
    This exists to accommodate images with embedded rotation tags.

    :param image_path: The image path.
    :return: A QImage object.
    """
    reader = Qg.QImageReader(str(image_path))
    image = reader.read()

    if not image.isNull():
        transformation = reader.transformation()
        # Create the appropriate QTransform
        if transformation == Qg.QImageIOHandler.TransformationMirror:
            transform = Qg.QTransform().scale(-1, 1)
        elif transformation == Qg.QImageIOHandler.TransformationFlip:
            transform = Qg.QTransform().scale(1, -1)
        elif transformation == Qg.QImageIOHandler.TransformationRotate180:
            transform = Qg.QTransform().rotate(180)
        elif transformation == Qg.QImageIOHandler.TransformationRotate90:
            transform = Qg.QTransform().rotate(90)
        elif transformation == Qg.QImageIOHandler.TransformationRotate270:
            transform = Qg.QTransform().rotate(270)
        else:
            transform = Qg.QTransform()

        # Apply the transformation if needed
        if not transform.isIdentity():
            image = image.transformed(transform, Qt.SmoothTransformation)

    return image
