import math
from enum import IntEnum
from pathlib import Path

import PySide6.QtCore as Qc
import PySide6.QtGui as Qg
import PySide6.QtWidgets as Qw
from PySide6.QtCore import Slot
from loguru import logger
from natsort import natsorted

import pcleaner.config as cfg
import pcleaner.gui.gui_utils as gu
import pcleaner.gui.image_file as imf
import pcleaner.gui.image_viewer as iv
from pcleaner.helpers import f_plural
from pcleaner.gui.ui_generated_files.ui_OutputReview import Ui_OutputReview

# The maximum size, will be smaller on one side if the image is not square.
THUMBNAIL_SIZE = 180


class ViewMode(IntEnum):
    SideBySide = 0
    Swipe = 1
    Onion = 2
    Difference = 3
    Overlay = 4


class OutputReviewWindow(Qw.QDialog, Ui_OutputReview):
    """
    A window to display the process results.
    """

    images: list[imf.ImageFile]
    target_output: imf.Output | None
    mask_outputs: list[imf.Output] | None
    show_isolated_text: bool
    config: cfg.Config
    confirm_closing: bool

    first_slot_connection: bool
    first_sbs_slot_connection: bool

    # Used so that the view will zoom to fit on the first load only.
    # This action needs to be delayed since the image dimensions are not known until the image is loaded,
    # since the size may change depending on the scale value.
    viewers_initialized: set

    min_thumbnail_size: int
    max_thumbnail_size: int

    def __init__(
        self,
        parent=None,
        images: list[imf.ImageFile] = None,
        target_output: imf.Output | None = None,
        mask_outputs: list[imf.Output] | None = None,
        show_isolated_text: bool = False,
        config: cfg.Config = None,
        confirm_closing: bool = False,
    ):
        """
        Init the widget.

        :param parent: The parent widget.
        :param images: The images to display.
        :param target_output: The main output to display.
        :param mask_outputs: The mask outputs to display.
        :param show_isolated_text: Whether to show the isolated text instead of the output in
            certain view modes (side-by-side).
        :param config: The configuration object.
        :param confirm_closing: Whether to ask for confirmation before closing.
        """
        logger.info(f"Opening Review Window for {len(images)} outputs.")
        Qw.QDialog.__init__(self, parent)
        self.setupUi(self)

        self.images = images
        self.target_output = target_output
        self.mask_outputs = mask_outputs
        self.show_isolated_text = show_isolated_text
        self.config = config
        self.confirm_closing = confirm_closing

        self.sort_images_by_path()

        self.first_load = set()
        self.first_slot_connection = True
        self.first_sbs_slot_connection = True

        self.calculate_thumbnail_size()
        self.init_arrow_buttons()
        self.init_image_list()
        self.init_image_viewers()
        self.image_list.currentItemChanged.connect(self.handle_image_change)
        self.comboBox_view_mode.currentIndexChanged.connect(self.handle_image_change)
        # Select the first image to start with.
        self.image_list.setCurrentRow(0)
        # Override Qt's dynamic scroll speed with a fixed, standard value.
        self.image_list.verticalScrollBar().setSingleStep(120)

        self.pushButton_done.clicked.connect(self.close)

    def closeEvent(self, event: Qg.QCloseEvent) -> None:
        if self.confirm_closing:
            if (
                gu.show_question(
                    self,
                    self.tr("Finish Review"),
                    self.tr("Are you sure you want to finish the review?"),
                )
                == Qw.QMessageBox.Cancel
            ):
                event.ignore()
                return
        event.accept()

    def sort_images_by_path(self) -> None:
        """
        Sort the images by their file path using natsort.
        This is necessary because the parallel batch processing will not preserve the order when
        many pictures are processed at once.
        """
        self.images = natsorted(self.images, key=lambda x: x.path)

    def calculate_thumbnail_size(self) -> None:
        """
        Use the current monitor's resolution to calculate the thumbnail size.
        The min value is 1% of the screen width, the max value is 100%.
        """
        screen = Qw.QApplication.primaryScreen()
        screen_size = screen.size()
        screen_width = screen_size.width()
        self.min_thumbnail_size = int(screen_width * 0.01)
        self.max_thumbnail_size = screen_width

    def to_log_scale(self, value: int) -> int:
        """
        Convert a linear value to a logarithmic scale.
        """
        min_log = math.log(self.min_thumbnail_size)
        max_log = math.log(self.max_thumbnail_size)
        scale = (max_log - min_log) / (
            self.horizontalSlider_icon_size.maximum() - self.horizontalSlider_icon_size.minimum()
        )
        log_value = min_log + (value - self.horizontalSlider_icon_size.minimum()) * scale
        return int(math.exp(log_value))

    def from_log_scale(self, value: int) -> int:
        """
        Convert a logarithmic value to a linear scale.
        """
        min_log = math.log(self.min_thumbnail_size)
        max_log = math.log(self.max_thumbnail_size)
        scale = (max_log - min_log) / (
            self.horizontalSlider_icon_size.maximum() - self.horizontalSlider_icon_size.minimum()
        )
        linear_value = (
            math.log(value) - min_log
        ) / scale + self.horizontalSlider_icon_size.minimum()
        return int(linear_value)

    def init_image_list(self) -> None:
        """
        Populate the image list with the images.
        """
        # Reduce the size of the list. Make it a 1/3 split.
        window_width = self.width()
        self.splitter.setSizes([window_width // 3, 2 * window_width // 3])

        self.image_list.setIconSize(Qc.QSize(THUMBNAIL_SIZE, THUMBNAIL_SIZE))
        # Use a logarithmic scale to distribute the values.
        self.horizontalSlider_icon_size.setValue(self.from_log_scale(THUMBNAIL_SIZE))
        self.horizontalSlider_icon_size.valueChanged.connect(self.update_icon_size)

        label_text = f_plural(len(self.images), self.tr("image"), self.tr("images"))
        self.label_image_count.setText(f"{len(self.images)} {label_text}")

        for image in self.images:

            original_path = image.path
            output_path = image.outputs[self.target_output].path

            if output_path is None:
                logger.error(f"Output path for {image.path} is None.")

            try:
                self.image_list.addItem(
                    Qw.QListWidgetItem(Qg.QIcon(str(output_path)), str(original_path.stem))
                )
            except OSError:
                gu.show_exception(
                    self,
                    self.tr("Loading Error"),
                    self.tr("Failed to load image '{path}'").format(path=output_path),
                )

        # Sanity check.
        if len(self.images) != self.image_list.count():
            logger.error("Failed to populate the image list correctly.")

    def init_arrow_buttons(self) -> None:
        """
        Connect the arrow buttons to the image list.
        """
        self.pushButton_next.clicked.connect(
            lambda: self.image_list.setCurrentRow(self.image_list.currentRow() + 1)
        )
        self.pushButton_prev.clicked.connect(
            lambda: self.image_list.setCurrentRow(self.image_list.currentRow() - 1)
        )

        # Disable the buttons if there is no next or previous image.
        self.image_list.currentRowChanged.connect(self.check_arrow_buttons)

    def check_arrow_buttons(self) -> None:
        """
        Check if the arrow buttons should be enabled or disabled.
        """
        current_row = self.image_list.currentRow()
        self.pushButton_prev.setEnabled(current_row > 0)
        self.pushButton_next.setEnabled(current_row < self.image_list.count() - 1)

    @Slot(int)
    def update_icon_size(self, size: int) -> None:
        """
        Update the icon size in the image list.

        :param size: The new size.
        """
        size = self.to_log_scale(size)
        self.image_list.setIconSize(Qc.QSize(size, size))

    def init_image_viewers(self) -> None:
        # Each one gets its own slider to manage the size of it themselves.
        self.image_viewer_swipe.connect_slider(self.horizontalSlider_swipe)
        self.image_viewer_onion.connect_slider(self.horizontalSlider_onion)
        self.image_viewer_difference.connect_slider(self.horizontalSlider_difference)
        self.image_viewer_overlay.connect_slider(self.horizontalSlider_overlay)

    @Slot(Qw.QListWidgetItem, Qw.QListWidgetItem)
    @Slot(Qw.QListWidgetItem)
    def handle_image_change(
        self, current: Qw.QListWidgetItem, previous: Qw.QListWidgetItem = None
    ) -> None:
        """
        Figure out what the new image is and display it.
        """
        # We don't need the previous image, so we ignore it.
        if current is None:
            return
        index = self.image_list.currentRow()
        image = self.images[index]
        self.switch_to_image(image)

    def current_view_mode(self) -> ViewMode:
        """
        Read the state of the combobox to determine the current view mode.

        :return: The current view mode.
        """
        return ViewMode(self.comboBox_view_mode.currentIndex())

    def switch_to_image(self, image: imf.ImageFile) -> None:
        """
        Show the image in the button in the image view.

        :param image: The image to show.
        """
        original_path = image.path
        output_path = image.outputs[self.target_output].path
        mask_paths = [image.outputs[mask].path for mask in self.mask_outputs]
        isolated_text_path = image.outputs[imf.Output.isolated_text].path

        self.label_file_name.setText(str(original_path))
        self.label_file_name.setToolTip(str(original_path))
        self.label_file_name.setElideMode(Qc.Qt.ElideLeft)

        view_mode = self.current_view_mode()
        self.stackedWidget.setCurrentIndex(view_mode)

        viewer_to_zoom: iv.ImageViewer | None = None

        match view_mode:
            case ViewMode.SideBySide:
                if not self.show_isolated_text:
                    self.load_side_by_side(original_path, output_path)
                else:
                    self.load_side_by_side(original_path, isolated_text_path)
                viewer_to_zoom = self.image_viewer_sbs_master
            case ViewMode.Swipe:
                self.load_swipe(original_path, output_path)
                viewer_to_zoom = self.image_viewer_swipe
            case ViewMode.Onion:
                self.load_onion(original_path, output_path)
                viewer_to_zoom = self.image_viewer_onion
            case ViewMode.Difference:
                self.load_difference(original_path, output_path)
                viewer_to_zoom = self.image_viewer_difference
            case ViewMode.Overlay:
                mask_color = self.config.current_profile.masker.debug_mask_color
                self.load_overlay(original_path, mask_paths, mask_color)
                viewer_to_zoom = self.image_viewer_overlay
            case _:
                logger.error("Invalid view mode.")

        # Disconnect prior slots if necessary.
        if not self.first_slot_connection:
            self.pushButton_zoom_in.clicked.disconnect()
            self.pushButton_zoom_out.clicked.disconnect()
            self.pushButton_zoom_fit.clicked.disconnect()
            self.pushButton_zoom_reset.clicked.disconnect()
        # Connect the zoom buttons to the image viewer.
        self.pushButton_zoom_in.clicked.connect(viewer_to_zoom.zoom_in)
        self.pushButton_zoom_out.clicked.connect(viewer_to_zoom.zoom_out)
        self.pushButton_zoom_fit.clicked.connect(viewer_to_zoom.zoom_fit)
        self.pushButton_zoom_reset.clicked.connect(viewer_to_zoom.zoom_reset)
        self.first_slot_connection = False

        # Set a delayed zoom to fit.
        if viewer_to_zoom not in self.first_load:
            Qc.QTimer.singleShot(0, viewer_to_zoom.zoom_fit)
            self.first_load.add(viewer_to_zoom)

    def load_side_by_side(self, original_path: Path, output_path: Path) -> None:
        """
        Load the images in the side-by-side view.
        This mode has 2 image viewers side by side.
        The master (left) shows the original image, the slave (right) shows the output image.
        Zoom events from the buttons are sent to the master, then the slave updates
        its zoom level to match the master.
        """
        # # Disconnect prior slots.
        # if not self.first_sbs_slot_connection:
        #     self.image_viewer_sbs_master.zoom_factor_changed.disconnect()
        #     self.image_viewer_sbs_slave.zoom_factor_changed_wheel.disconnect()
        #     self.image_viewer_sbs_master.horizontalScrollBar().valueChanged.disconnect()
        #     self.image_viewer_sbs_slave.horizontalScrollBar().valueChanged.disconnect()
        #     self.image_viewer_sbs_master.verticalScrollBar().valueChanged.disconnect()
        #     self.image_viewer_sbs_slave.verticalScrollBar().valueChanged.disconnect()

        # Load the images.
        self.image_viewer_sbs_master.set_image(original_path)
        self.image_viewer_sbs_slave.set_image(output_path)

        if not self.first_sbs_slot_connection:
            return
        # The slave copies the master's zoom level.
        self.image_viewer_sbs_master.zoom_factor_changed.connect(
            self.image_viewer_sbs_slave.set_zoom_factor
        )
        # Unless the slave receives direct orders from the scroll wheel.
        self.image_viewer_sbs_slave.zoom_factor_changed_wheel.connect(
            self.image_viewer_sbs_master.set_zoom_factor
        )
        # The slave copies the master's scroll position and vice versa.
        self.image_viewer_sbs_master.horizontalScrollBar().valueChanged.connect(
            self.image_viewer_sbs_slave.horizontalScrollBar().setValue
        )
        self.image_viewer_sbs_slave.horizontalScrollBar().valueChanged.connect(
            self.image_viewer_sbs_master.horizontalScrollBar().setValue
        )
        self.image_viewer_sbs_master.verticalScrollBar().valueChanged.connect(
            self.image_viewer_sbs_slave.verticalScrollBar().setValue
        )
        self.image_viewer_sbs_slave.verticalScrollBar().valueChanged.connect(
            self.image_viewer_sbs_master.verticalScrollBar().setValue
        )
        self.first_sbs_slot_connection = False

    def load_swipe(self, original_path: Path, output_path: Path) -> None:
        """
        Load the images in the swipe view.
        This mode has 1 image viewer.
        The original image is shown on the left, the output image is shown on the right.
        The user can swipe the images horizontally to compare them.
        """
        self.image_viewer_swipe.set_images(original_path, output_path)

    def load_onion(self, original_path: Path, output_path: Path) -> None:
        """
        Load the images in the onion view.
        This mode has 1 image viewer.
        The output image is shown on top of the original image.
        The user can adjust the onion level to see more or less of the output image.
        """
        self.image_viewer_onion.set_images(original_path, output_path)

    def load_difference(self, original_path: Path, output_path: Path) -> None:
        """
        Load the images in the difference view.
        This mode has 1 image viewer.
        The difference between the original and output images is shown.
        """
        self.image_viewer_difference.set_images(original_path, output_path)

    def load_overlay(
        self, original_path: Path, mask_paths: list[Path], mask_color: tuple[int, int, int, int]
    ) -> None:
        """
        Load the images in the overlay view.
        This mode has 1 image viewer.
        The mask is shown on top of the original image.
        """
        self.image_viewer_overlay.set_images(original_path, mask_paths, mask_color)
