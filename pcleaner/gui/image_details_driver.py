from functools import partial
from pathlib import Path
import PySide6.QtWidgets as Qw
import PySide6.QtGui as Qg
import PySide6.QtCore as Qc
from PySide6.QtCore import Signal, Slot
from logzero import logger
import shutil

from pcleaner.gui.ui_generated_files.ui_ImageDetails import Ui_ImageDetails
import pcleaner.gui.image_file as imf
import pcleaner.gui.gui_utils as gu

# TODO slap a bunch of right aligned labels next to the step names to indicate that thez need to be refreshed.
# when the last checksum is none, ignore, as they were never even generated.
# Or maybe as a badge, drawing a square with the accent color underneath???

THUMBNAIL_SIZE = 180, 180
PUSHBUTTON_THUMBNAIL_MARGIN = 16


class ImageDetailsWidget(Qw.QWidget, Ui_ImageDetails):
    """
    A widget that shows the details of an image object.
    """

    image_obj: imf.ImageFile  # The image object to show.
    current_image_path: Path | None  # The path of the image currently shown.

    button_map: dict[Qw.QPushButton, imf.Step]

    def __init__(self, parent=None, image_obj: imf.ImageFile = None):
        """
        Init the widget.

        :param image_obj: The image object to show.
        """
        logger.info(f"Opening details tab for {image_obj.path}")
        Qw.QWidget.__init__(self, parent)
        self.setupUi(self)

        self.image_obj = image_obj
        self.button_map = self.init_button_map()

        # Clear sample text from labels that only update on user interaction.
        self.label_size.setText("")
        self.label_position.setText("")
        self.label_step.setText("")

        self.init_sidebar()
        self.load_all_image_thumbnails()
        self.pushButton_input.click()

    def init_button_map(self) -> dict[Qw.QPushButton, imf.Step]:
        return {
            self.pushButton_input: imf.Step.input,
            self.pushButton_text_detection: imf.Step.ai_mask,
            self.pushButton_initial_boxes: imf.Step.initial_boxes,
            self.pushButton_final_boxes: imf.Step.final_boxes,
            self.pushButton_box_mask: imf.Step.box_mask,
            self.pushButton_cut_mask: imf.Step.cut_mask,
            self.pushButton_mask_layers: imf.Step.mask_layers,
            self.pushButton_final_mask: imf.Step.final_mask,
            self.pushButton_output_overlay: imf.Step.mask_overlay,
            self.pushButton_output_masked: imf.Step.masked_image,
            self.pushButton_denoise_mask: imf.Step.denoiser_mask,
            self.pushButton_denoised_output: imf.Step.denoised_image,
        }

    def init_sidebar(self):
        """
        Set up the buttons in the sidebar.
        """
        self.label_file_name.setText(self.image_obj.path.name)
        self.label_file_name.setToolTip(str(self.image_obj.path))
        self.label_file_name.setElideMode(Qc.Qt.ElideLeft)

        self.pushButton_zoom_in.clicked.connect(self.image_viewer.zoom_in)
        self.pushButton_zoom_out.clicked.connect(self.image_viewer.zoom_out)
        self.pushButton_zoom_reset.clicked.connect(self.image_viewer.zoom_reset)

        self.pushButton_export.clicked.connect(self.export_image)

        # Figure out the optimal button size.
        # It should fit within the thumbnail size while maintaining the aspect ratio.
        # The button size is the minimum of the thumbnail size and the image size.
        image_width, image_height = self.image_obj.size
        ratio = image_width / image_height
        if image_width > image_height:
            button_width = THUMBNAIL_SIZE[0]
            button_height = int(button_width / ratio)
        else:
            button_height = THUMBNAIL_SIZE[1]
            button_width = int(button_height * ratio)

        # Adjust the width of the scroll area to fit the buttons.
        scrollbar_width = Qw.QApplication.style().pixelMetric(Qw.QStyle.PM_ScrollBarExtent)
        margins_left, _, margins_right, _ = self.sidebar_layout.getContentsMargins()
        self.scrollArea.setFixedWidth(
            button_width
            + PUSHBUTTON_THUMBNAIL_MARGIN
            + scrollbar_width
            + margins_left
            + margins_right
            + 2,  # Arbitrary extra margin to make it look "right".
        )
        logger.debug(f"Setting scroll area width to {self.scrollArea.width()}")

        # Resize all the buttons.
        # self.scrollArea.setFixedWidth()
        for button in self.button_map:
            button.setFixedSize(
                button_width + PUSHBUTTON_THUMBNAIL_MARGIN,
                button_height + PUSHBUTTON_THUMBNAIL_MARGIN,
            )
            button.setIconSize(Qc.QSize(button_width, button_height))
            button.clicked.connect(partial(self.switch_to_image, button))

    def load_all_image_thumbnails(self):
        """
        Load all the images into the buttons.
        """
        for button, step_type in self.button_map.items():
            step = self.image_obj.steps[step_type]
            if step.path is not None:
                try:
                    button.setIcon(Qg.QIcon(str(step.path)))
                except OSError as e:
                    logger.error(f"Failed to load image {step.path}: {e}")
            else:
                button.setText("Generate Me")

    def switch_to_image(self, button: Qw.QPushButton):
        """
        Show the image in the button in the image view.

        :param button: The button that was clicked.
        """
        step: imf.ProcessStep = self.image_obj.steps[self.button_map[button]]
        self.label_step.setText(step.description)
        self.current_image_path = step.path
        if not step.has_path():
            # Clear whatever image is currently shown.
            self.image_viewer.set_image(None)
            self.label_position.setText("")
            self.widget_footer_info.hide()
            self.stackedWidget.setCurrentWidget(self.page_no_image)
            self.pushButton_export.setEnabled(False)
            self.pushButton_refresh.setEnabled(False)
        else:
            try:
                self.image_viewer.set_image(step.path)
                self.label_size.setText(
                    f"{self.image_viewer.image_dimensions[0]} × {self.image_viewer.image_dimensions[1]}"
                )
                self.image_viewer.mouseMoved.connect(self.update_position_label)
                self.widget_footer_info.show()
                self.stackedWidget.setCurrentWidget(self.page_viewer)
                self.pushButton_export.setEnabled(True)
                self.pushButton_refresh.setEnabled(True)
            except OSError as e:
                logger.error(f"Image at {step.path} does not exist. {e}")
                gu.show_warning(
                    self, "Image not found.", f"Image at {step.path} does not exist: {e}"
                )
                return

    @Slot(int, int)
    def update_position_label(self, x: int, y: int):
        """
        Update the position label with the current mouse position.

        :param x: The x coordinate of the mouse.
        :param y: The y coordinate of the mouse.
        """
        self.label_position.setText(f"{x}, {y}")

    def export_image(self):
        """
        If the image exists, open a save dialog to copy it to a new location.
        """
        if self.current_image_path is None:
            return
        if not self.current_image_path.is_file():
            return

        save_path, _ = Qw.QFileDialog.getSaveFileName(self, "Export Image")
        if save_path:
            try:
                shutil.copy(self.current_image_path, save_path)
                logger.info(f"Exported image to {save_path}")
            except OSError as e:
                logger.error(f"Failed to export image to {save_path}: {e}")
                gu.show_warning(self, "Export failed", f"Failed to export image:\n\n{e}")
