import shutil
from functools import partial
from pathlib import Path
from typing import Callable

import PySide6.QtCore as Qc
import PySide6.QtGui as Qg
import PySide6.QtWidgets as Qw
from PySide6.QtCore import Slot
from logzero import logger

import pcleaner.config as cfg
import pcleaner.gui.gui_utils as gu
import pcleaner.gui.image_file as imf
import pcleaner.gui.processing as prc
import pcleaner.gui.structures as st
import pcleaner.gui.worker_thread as wt
from pcleaner.gui.ui_generated_files.ui_ImageDetails import Ui_ImageDetails


# TODO slap a bunch of right aligned labels next to the step names to indicate that they need to be refreshed.
# when the last checksum is none, ignore, as they were never even generated.
# Or maybe as a badge, drawing a square with the accent color underneath???

THUMBNAIL_SIZE = 180, 180
PUSHBUTTON_THUMBNAIL_MARGIN = 8
PUSHBUTTON_THUMBNAIL_SEPARATION = 8
SIDEBAR_COLUMNS = 2


class ImageDetailsWidget(Qw.QWidget, Ui_ImageDetails):
    """
    A widget that shows the details of an image object.
    """

    image_obj: imf.ImageFile  # The image object to show.
    current_image_path: Path | None  # The path of the image currently shown.

    button_map: dict[Qw.QPushButton, imf.Output]

    config: cfg.Config
    shared_ocr_model: st.Shared[st.OCRModel]  # Must be handed over by the file table.
    thread_queue: Qc.QThreadPool
    progress_callback: Callable[[imf.ProgressData], None]

    # Used so that the view will zoom to fit on the first load only.
    # This action needs to be delayed since the image dimensions are not known until the image is loaded,
    # since the size may change depending on the scale value.
    first_load: bool

    def __init__(
        self,
        parent=None,
        image_obj: imf.ImageFile = None,
        config: cfg.Config = None,
        shared_ocr_model: st.Shared[st.OCRModel] = None,
        thread_queue: Qc.QThreadPool = None,
        progress_callback: Callable[[imf.ProgressData], None] = None,
    ):
        """
        Init the widget.

        :param image_obj: The image object to show.
        """
        logger.info(f"Opening details tab for {image_obj.path}")
        Qw.QWidget.__init__(self, parent)
        self.setupUi(self)

        self.image_obj = image_obj
        self.config = config
        self.shared_ocr_model = shared_ocr_model
        self.button_map = self.create_sidebar_buttons()

        self.first_load = True
        self.thread_queue = thread_queue
        self.progress_callback = progress_callback

        # Clear sample text from labels that only update on user interaction.
        self.label_size.setText("")
        self.label_position.setText("")
        self.label_step.setText("")

        self.init_sidebar()
        self.load_all_image_thumbnails()
        # Click on the first button to show the input image.
        input_button = list(self.button_map.keys())[0]
        input_button.click()

    def create_sidebar_buttons(self) -> dict[Qw.QPushButton, imf.Output]:
        """
        Parse the image object's outputs to create a list of buttons in the side panel.

        Returns: A map of buttons to outputs.
        """

        current_button_layout: Qw.QGridLayout
        current_button_index: int = 0
        last_step_name: str | None = None

        def add_button(title: str | None) -> Qw.QPushButton | Qw.QVBoxLayout:
            # Insert a new button into the current step's layout.
            button = Qw.QPushButton()
            button.setCheckable(True)
            button.clicked.connect(partial(self.uncheck_all_other_buttons, button))
            # Ensure the button's style sheet dictates that when checked, it is highlighted
            # with the accent color from the current system theme.
            # Fetch the accent color from the current palette
            accent_color = self.palette().color(Qg.QPalette.ColorRole.Highlight)

            # Update button's stylesheet to use the accent color as background
            button.setStyleSheet(
                f"QPushButton:checked {{background-color: {accent_color.name()};}}"
            )
            button_widget = button

            # Create a title as a separate label widget and stack them vertically.
            if title is not None:
                layout = Qw.QVBoxLayout()
                layout.setContentsMargins(0, 0, 0, 0)
                layout.setSpacing(4)  # The small spacing between the label and the image.
                label = Qw.QLabel(title)
                layout.addWidget(label)
                layout.addWidget(button)
                # Wrap the layout in a widget so it can be added to the grid layout.
                button_widget = Qw.QWidget()
                button_widget.setLayout(layout)

            # Add it to the current button grid layout, wrapping to the next row if necessary.
            nonlocal current_button_layout, current_button_index
            current_button_layout.addWidget(
                button_widget,
                current_button_index // SIDEBAR_COLUMNS,
                current_button_index % SIDEBAR_COLUMNS,
            )
            logger.debug(
                f"Adding button {title} at index {current_button_index}, row {current_button_index // SIDEBAR_COLUMNS}, column {current_button_index % SIDEBAR_COLUMNS}"
            )
            current_button_index += 1
            return button

        def add_step_label(title: str):
            # Add a step name label with a spacer above it if needed.
            nonlocal last_step_name
            if last_step_name is not None:
                spacer = Qw.QSpacerItem(0, 16, Qw.QSizePolicy.Minimum, Qw.QSizePolicy.Minimum)
                self.sidebar_layout.addItem(spacer)

            label = Qw.QLabel(title)
            font = label.font()
            font.setBold(True)
            label.setFont(font)
            self.sidebar_layout.addWidget(label)
            # Add a fresh grid layout for the buttons.
            nonlocal current_button_layout, current_button_index
            current_button_layout = Qw.QGridLayout()
            current_button_layout.setContentsMargins(0, 0, 0, 0)
            current_button_layout.setSpacing(PUSHBUTTON_THUMBNAIL_SEPARATION)
            current_button_index = 0
            self.sidebar_layout.addLayout(current_button_layout)

        buttons = {}
        for output, proc_output in self.image_obj.outputs.items():
            # Add a step name label if it has changed and is not None.
            # Outputs with a none step name are not shown.
            if proc_output.step_name is None:
                continue
            elif proc_output.step_name != last_step_name:
                add_step_label(proc_output.step_name)
                last_step_name = proc_output.step_name

            button_title = proc_output.output_name
            new_button = add_button(button_title)
            buttons[new_button] = output

        return buttons

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
        self.pushButton_zoom_fit.clicked.connect(self.image_viewer.zoom_fit)

        self.pushButton_export.clicked.connect(self.export_image)

        # Figure out the optimal button size.
        # It should fit within the thumbnail size while maintaining the aspect ratio.
        # The button size is the minimum of the thumbnail size and the image size.
        image_width, image_height = self.image_obj.size
        ratio = image_width / image_height
        if image_width > image_height:
            thumbnail_width = THUMBNAIL_SIZE[0]
            thumbnail_height = int(thumbnail_width / ratio)
        else:
            thumbnail_height = THUMBNAIL_SIZE[1]
            thumbnail_width = int(thumbnail_height * ratio)

        # Adjust the width of the scroll area to fit the buttons.
        scrollbar_width = Qw.QApplication.style().pixelMetric(Qw.QStyle.PM_ScrollBarExtent)
        margins_left, _, margins_right, _ = self.sidebar_layout.getContentsMargins()
        self.scrollArea.setFixedWidth(
            thumbnail_width * SIDEBAR_COLUMNS
            + PUSHBUTTON_THUMBNAIL_MARGIN * SIDEBAR_COLUMNS
            + PUSHBUTTON_THUMBNAIL_SEPARATION * (SIDEBAR_COLUMNS - 1)
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
                thumbnail_width + PUSHBUTTON_THUMBNAIL_MARGIN,
                thumbnail_height + PUSHBUTTON_THUMBNAIL_MARGIN,
            )
            button.setIconSize(Qc.QSize(thumbnail_width, thumbnail_height))
            button.clicked.connect(partial(self.switch_to_image, button))

    def load_all_image_thumbnails(self):
        """
        Load all the images into the buttons.
        """
        for button, output in self.button_map.items():
            proc_output = self.image_obj.outputs[output]
            if proc_output.path is not None:
                try:
                    button.setIcon(Qg.QIcon(str(proc_output.path)))
                    button.setText("")
                except OSError as e:
                    logger.error(f"Failed to load image {proc_output.path}: {e}")
            else:
                button.setText("Generate Me")

    def switch_to_image(self, button: Qw.QPushButton):
        """
        Show the image in the button in the image view.

        :param button: The button that was clicked.
        """
        output = self.button_map[button]
        proc_output: imf.ProcessOutput = self.image_obj.outputs[output]
        self.label_step.setText(proc_output.description)
        self.current_image_path = proc_output.path
        if not proc_output.has_path():
            # Clear whatever image is currently shown.
            self.image_viewer.set_image(None)
            self.label_position.setText("")
            self.widget_footer_info.hide()
            self.stackedWidget.setCurrentWidget(self.page_no_image)
            self.pushButton_export.setEnabled(False)
            self.pushButton_refresh.setEnabled(False)
            self.start_output_worker(output)
        else:
            try:
                self.image_viewer.set_image(proc_output.path)
                self.label_size.setText(
                    f"{self.image_viewer.image_dimensions[0]} × {self.image_viewer.image_dimensions[1]}"
                )
                self.image_viewer.mouseMoved.connect(self.update_position_label)
                self.widget_footer_info.show()
                self.stackedWidget.setCurrentWidget(self.page_viewer)
                self.pushButton_export.setEnabled(True)
                self.pushButton_refresh.setEnabled(True)
            except OSError as e:
                logger.error(f"Image at {proc_output.path} does not exist. {e}")
                gu.show_warning(
                    self, "Image not found.", f"Image at {proc_output.path} does not exist: {e}"
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

    def reload_current_image(self):
        """
        Reload the current image.
        The current image is the one belonging to the currently selected pushbutton.
        """
        # Check all the buttons to see which one is currently clicked.
        for button in self.button_map:
            if button.isChecked():
                self.switch_to_image(button)
                break

    @Slot()
    def uncheck_all_other_buttons(self, checked_button: Qw.QPushButton):
        """
        Uncheck all buttons except the one that was checked.

        :param checked_button: The button that was checked.
        """
        for button in self.button_map:
            if button is not checked_button:
                button.setChecked(False)

    # ========================================== Worker Functions ==========================================

    def start_output_worker(self, output: imf.Output):
        """
        Start the worker thread for the given output.

        :param output: The output to generate.
        """
        worker = wt.Worker(self.generate_output, output)
        worker.signals.progress.connect(self.progress_callback)
        worker.signals.result.connect(self.output_worker_result)
        worker.signals.error.connect(self.output_worker_error)
        self.thread_queue.start(worker)

    def generate_output(self, output: imf.Output, progress_callback: imf.ProgressSignal) -> None:
        """
        Generate the given output, if there doesn't yet exist a valid output for it.

        :param output: The output to generate.
        :param progress_callback: The callback given by the worker thread wrapper.
        """
        # Check if the output is already valid.
        proc_output: imf.ProcessOutput = self.image_obj.outputs[output]
        if proc_output.is_unchanged(self.config.current_profile):
            logger.debug(f"Output {output} is unchanged. Worker will not run.")
            return

        # Start the processor.
        prc.generate_output(
            image_objects=[self.image_obj],
            target_outputs=[output],
            output_dir=None,
            config=self.config,
            ocr_model=self.shared_ocr_model.get(),
            progress_callback=progress_callback,
        )

    def output_worker_result(self):
        self.load_all_image_thumbnails()
        self.reload_current_image()
        if self.first_load:
            self.first_load = False
            self.image_viewer.zoom_fit()
        logger.info("Output worker finished.")

    def output_worker_error(self):
        logger.error("Output worker encountered an error.")
