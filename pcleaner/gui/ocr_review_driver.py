import math
from enum import IntEnum

import PySide6.QtCore as Qc
import PySide6.QtGui as Qg
import PySide6.QtWidgets as Qw
from PySide6.QtCore import Slot
from loguru import logger

import pcleaner.gui.gui_utils as gu
import pcleaner.gui.image_file as imf
import pcleaner.structures as st
from pcleaner.gui.ui_generated_files.ui_OcrReview import Ui_OcrReview

# The maximum size, will be smaller on one side if the image is not square.
THUMBNAIL_SIZE = 180


class ViewMode(IntEnum):
    WithBoxes = 0
    Original = 1


class OcrReviewWindow(Qw.QDialog, Ui_OcrReview):
    """
    A window to display the process results.
    """

    images: list[imf.ImageFile]
    ocr_results: list[st.OCRAnalytic]

    min_thumbnail_size: int
    max_thumbnail_size: int

    first_load: bool

    def __init__(
        self,
        parent=None,
        images: list[imf.ImageFile] = None,
        ocr_results: list[st.OCRAnalytic] = None,
    ):
        """
        Init the widget.

        :param parent: The parent widget.
        :param images: The images to display.
        :param ocr_results: The OCR results to display.
        """
        logger.debug(f"Opening OCR Review Window for {len(images)} outputs.")
        Qw.QDialog.__init__(self, parent)
        self.setupUi(self)

        # Special OutputReview overrides.
        self.target_output = imf.Output.initial_boxes
        self.confirm_closing = True

        self.images = images
        self.ocr_results = ocr_results

        if len(self.images) != len(self.ocr_results):
            logger.error("The number of images and OCR results don't match.")

        self.first_load = True

        self.calculate_thumbnail_size()
        self.init_arrow_buttons()
        self.init_image_list()
        self.image_list.currentItemChanged.connect(self.handle_image_change)
        # Select the first image to start with.
        self.image_list.setCurrentRow(0)
        self.comboBox_view_mode.currentIndexChanged.connect(self.handle_image_change)

        self.pushButton_done.clicked.connect(self.close)

        # Connect the zoom buttons to the image viewer.
        self.pushButton_zoom_in.clicked.connect(self.image_viewer.zoom_in)
        self.pushButton_zoom_out.clicked.connect(self.image_viewer.zoom_out)
        self.pushButton_zoom_fit.clicked.connect(self.image_viewer.zoom_fit)
        self.pushButton_zoom_reset.clicked.connect(self.image_viewer.zoom_reset)

        # Make side splitter 50/50.
        side_splitter_width = self.splitter_side.width()
        self.splitter_side.setSizes([side_splitter_width // 2, side_splitter_width // 2])

    def switch_to_image(self, image: imf.ImageFile) -> None:
        """
        Show the image in the button in the image view.

        :param image: The image to show.
        """
        original_path = image.path
        output_path = image.outputs[self.target_output].path

        self.label_file_name.setText(str(original_path))
        self.label_file_name.setToolTip(str(original_path))
        self.label_file_name.setElideMode(Qc.Qt.ElideLeft)

        if self.view_mode() == ViewMode.WithBoxes:
            self.image_viewer.set_image(output_path)
        else:
            self.image_viewer.set_image(original_path)

        self.load_ocr_results(self.ocr_results[self.images.index(image)])

        # Set a delayed zoom to fit.
        if self.first_load:
            Qc.QTimer.singleShot(0, self.image_viewer.zoom_fit)
            self.first_load = False

    def load_ocr_results(self, ocr_result: st.OCRAnalytic) -> None:
        """
        Load the OCR results into the text fields.

        :param ocr_result: The OCR results to load.
        """
        # Format OCR results.
        self.textEdit_ocr.clear()
        text = ""
        for index, (_, ocr_text, _) in enumerate(ocr_result.removed_box_data):
            text += f"{index + 1}\t {ocr_text}\n\n"

        if not text:
            text = f'<i>{self.tr("No text found in the image.")}</i>'

        self.textEdit_ocr.setPlainText(text)

    def view_mode(self) -> ViewMode:
        """
        Get the current view mode.

        :return: The current view mode.
        """
        return ViewMode(self.comboBox_view_mode.currentIndex())

    # Copied shit from OutputReview ================================================================

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

        self.label_image_count.setText(self.tr("%n image(s)", "", len(self.images)))

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

    @Slot(Qw.QListWidgetItem, Qw.QListWidgetItem)
    @Slot(Qw.QListWidgetItem)
    def handle_image_change(
        self, current: Qw.QListWidgetItem = None, previous: Qw.QListWidgetItem = None
    ) -> None:
        """
        Figure out what the new image is and display it.
        """
        # We don't need the previous image, so we ignore it.
        index = self.image_list.currentRow()
        image = self.images[index]
        self.switch_to_image(image)
