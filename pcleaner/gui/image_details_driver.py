import shutil
from functools import partial
from pathlib import Path
from typing import Callable
from typing import Sequence

import PySide6.QtCore as Qc
import PySide6.QtGui as Qg
import PySide6.QtWidgets as Qw
from PySide6.QtCore import Slot, Signal
from logzero import logger

import pcleaner.config as cfg
import pcleaner.gui.gui_utils as gu
import pcleaner.gui.image_file as imf
import pcleaner.gui.processing as prc
import pcleaner.gui.structures as st
import pcleaner.gui.worker_thread as wt
from pcleaner.gui.CustomQ.CBadgeButton import BadgeButton
from pcleaner.gui.ui_generated_files.ui_ImageDetails import Ui_ImageDetails


THUMBNAIL_SIZE = 180, 180
PUSHBUTTON_THUMBNAIL_MARGIN = 8
PUSHBUTTON_THUMBNAIL_SEPARATION = 8
SIDEBAR_COLUMNS = 2
BADGE_SIZE = 24


class ImageDetailsWidget(Qw.QWidget, Ui_ImageDetails):
    """
    A widget that shows the details of an image object.
    """

    image_obj: imf.ImageFile  # The image object to show.
    current_image_path: Path | None  # The path of the image currently shown.

    button_map: dict[BadgeButton, imf.Output]

    config: cfg.Config
    shared_ocr_model: st.Shared[st.OCRModel]  # Must be handed over by the file table.
    thread_queue: Qc.QThreadPool
    progress_callback: Callable[[imf.ProgressData], None]
    abort_signal: Signal

    menu: Qw.QMenu  # The overflow menu for the export and ocr buttons.
    export_action: Qg.QAction
    ocr_action: Qg.QAction

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
        profile_changed_signal: Signal = None,
        abort_signal: Signal = None,
    ):
        """
        Init the widget.

        :param image_obj: The image object to show.
        :param config: The config object.
        :param shared_ocr_model: The shared OCR model.
        :param thread_queue: The thread queue to use for the workers.
        :param progress_callback: The callback to use for the progress signals.
        :param profile_changed_signal: The signal that is emitted when the profile changes.
        :param abort_signal: The signal that is emitted when the worker should abort.
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
        self.abort_signal = abort_signal

        # Clear sample text from labels that only update on user interaction.
        self.label_size.setText("")
        self.label_position.setText("0, 0")
        self.label_step.setText("")

        self.init_sidebar()
        self.load_all_image_thumbnails()
        self.pushButton_refresh.clicked.connect(self.regenerate_current_output)
        self.init_menu()
        profile_changed_signal.connect(self.start_profile_checker)
        # Click on the first button to show the input image.
        input_button = list(self.button_map.keys())[0]
        input_button.click()

    def init_menu(self) -> None:
        """
        Initialize the overflow menu housing the export and ocr button for the image details widget.
        """
        self.menu = Qw.QMenu(self)
        self.export_action = Qg.QAction(Qg.QIcon.fromTheme("document-save"), "Export Image", self)
        self.export_action.triggered.connect(self.export_image)
        self.menu.addAction(self.export_action)

        self.ocr_action = Qg.QAction(Qg.QIcon.fromTheme("document-scan"), "OCR Image", self)
        self.ocr_action.triggered.connect(self.start_ocr_worker)
        self.menu.addAction(self.ocr_action)

        self.pushButton_menu.setMenu(self.menu)

    def create_sidebar_buttons(self) -> dict[BadgeButton, imf.Output]:
        """
        Parse the image object's outputs to create a list of buttons in the side panel.

        Returns: A map of buttons to outputs.
        """

        current_button_layout: Qw.QGridLayout
        current_button_index: int = 0
        last_step_name: str | None = None

        def add_button(title: str | None) -> BadgeButton | Qw.QVBoxLayout:
            # Insert a new button into the current step's layout.
            button = BadgeButton()
            button.setCheckable(True)
            button.set_badge_size(BADGE_SIZE, PUSHBUTTON_THUMBNAIL_MARGIN)
            button.clicked.connect(partial(self.uncheck_all_other_buttons, button))
            button_widget = button

            # Create a title as a separate label widget and stack them vertically.
            if title is not None:
                layout = Qw.QVBoxLayout()
                layout.setContentsMargins(0, 0, 0, 0)
                layout.setSpacing(2)  # The small spacing between the label and the image.
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
            current_button_index += 1
            return button

        def add_step_label(title: str) -> None:
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

    def changeEvent(self, event: Qc.QEvent) -> None:
        """
        Due to the buttons using a fixed stylesheet to apply the colored border as a background,
        they do not react to changes in the palette. Therefore we need to nuke all buttons and
        re-create them when the palette changes.
        :param event:
        :return:
        """
        Qw.QWidget.changeEvent(self, event)
        if event.type() == Qc.QEvent.PaletteChange:
            logger.warning("Palette changed. Re-creating buttons.")

            # Remember what output was last selected.
            current_output = self.button_map.get(self.current_button(), None)

            # Empty out the sidebar layout.
            self._clear_all_from_layout(self.sidebar_layout)
            # Re-create the buttons.
            self.button_map = self.create_sidebar_buttons()
            self.init_sidebar()
            self.load_all_image_thumbnails()

            # Select the button that was selected before.
            for button, output in self.button_map.items():
                if output == current_output:
                    button.click()
                    break

            self.update()

    def _clear_all_from_layout(self, layout: Qw.QLayout) -> None:
        for i in reversed(
            range(layout.count())
        ):  # Loop backwards to avoid disrupting the remaining indices
            item = layout.itemAt(i)
            if item.widget() is not None:
                widget = item.widget()
                widget.deleteLater()  # Mark the widget for deletion
            elif item.layout() is not None:
                # Recursively clear this sub-layout
                self._clear_all_from_layout(item.layout())
            layout.removeItem(item)  # Remove the item from layout

    def init_sidebar(self) -> None:
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

    def load_all_image_thumbnails(self) -> None:
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
        # Update the badges on the buttons.
        self.start_profile_checker()

    def switch_to_image(self, button: BadgeButton) -> None:
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
            self.label_position.setText("0, 0")
            self.widget_footer_info.hide()
            self.stackedWidget.setCurrentWidget(self.page_no_image)
            self.export_action.setEnabled(False)
            self.pushButton_refresh.setEnabled(False)
            self.start_output_worker(output)
        else:
            try:
                # Draw a background using the accent color to provide contrast.
                self.image_viewer.setBackgroundBrush(
                    Qg.QBrush(self.palette().color(Qg.QPalette.Highlight))
                )
                self.image_viewer.set_image(proc_output.path)
                self.label_size.setText(
                    f"{self.image_viewer.image_dimensions[0]} × {self.image_viewer.image_dimensions[1]}"
                )
                self.image_viewer.mouseMoved.connect(self.update_position_label)
                self.widget_footer_info.show()
                self.stackedWidget.setCurrentWidget(self.page_viewer)
                self.export_action.setEnabled(True)
                self.pushButton_refresh.setEnabled(True)
                if self.first_load:
                    self.first_load = False
                    # Call the zoom fit function after the event loop has finished.
                    # This is necessary because the viewport dimensions are not known until the image is loaded.
                    Qc.QTimer.singleShot(0, self.image_viewer.zoom_fit)
            except OSError as e:
                logger.error(f"Image at {proc_output.path} does not exist. {e}")
                gu.show_warning(
                    self, "Image not found.", f"Image at {proc_output.path} does not exist: {e}"
                )
                return

    @Slot(int, int)
    def update_position_label(self, x: int, y: int) -> None:
        """
        Update the position label with the current mouse position.

        :param x: The x coordinate of the mouse.
        :param y: The y coordinate of the mouse.
        """
        self.label_position.setText(f"{x}, {y}")
        self.label_position.setMinimumWidth(self.label_position.width())

    def export_image(self) -> None:
        """
        If the image exists, open a save dialog to copy it to a new location.
        """
        if self.current_image_path is None:
            return
        if not self.current_image_path.is_file():
            return

        save_path, _ = Qw.QFileDialog.getSaveFileName(self, "Export Image", filter="PNG (*.png)")
        if save_path:
            save_path = Path(save_path).with_suffix(".png")
            try:
                shutil.copy(self.current_image_path, save_path)
                logger.info(f"Exported image to {save_path}")
            except OSError as e:
                logger.error(f"Failed to export image to {save_path}: {e}")
                gu.show_warning(self, "Export failed", f"Failed to export image:\n\n{e}")

    def current_button(self) -> BadgeButton | None:
        """
        Get the currently selected button.

        Returns: The button that is currently selected, or None if no button is selected.
        """
        for button in self.button_map:
            if button.isChecked():
                return button
        return None

    def reload_current_image(self) -> None:
        """
        Reload the current image.
        The current image is the one belonging to the currently selected pushbutton.
        """
        if button := self.current_button():
            self.switch_to_image(button)

    @Slot()
    def uncheck_all_other_buttons(self, checked_button: BadgeButton) -> None:
        """
        Uncheck all buttons except the one that was checked.

        :param checked_button: The button that was checked.
        """
        for button in self.button_map:
            if button is not checked_button:
                button.setChecked(False)

    def regenerate_current_output(self) -> None:
        """
        Delete the current output and regenerate it.
        """
        if button := self.current_button():
            self.image_obj.outputs[self.button_map[button]].reset()
            self.switch_to_image(button)

    def clear_change_flairs(self) -> None:
        """
        Clear the change flairs from all buttons.
        """
        for button in self.button_map:
            button.hide_badge()

    @staticmethod
    def set_change_flair(button: BadgeButton) -> None:
        """
        Set the change flair on the given button.

        :param button: The button to set the flair on.
        """
        button.show_badge()

    # ========================================== Worker Functions ==========================================

    def start_output_worker(self, output: imf.Output) -> None:
        """
        Start the worker thread for the given output.

        :param output: The output to generate.
        """
        worker = wt.Worker(self.generate_output, output, abort_signal=self.abort_signal)
        worker.signals.progress.connect(self.progress_callback)
        worker.signals.result.connect(self.output_worker_result)
        worker.signals.error.connect(self.output_worker_error)
        worker.signals.aborted.connect(self.output_worker_aborted)
        self.thread_queue.start(worker)

    def generate_output(
        self, output: imf.Output, progress_callback: imf.ProgressSignal, abort_flag: wt.SharableFlag
    ) -> None:
        """
        Generate the given output, if there doesn't yet exist a valid output for it.

        :param output: The output to generate.
        :param progress_callback: The callback given by the worker thread wrapper.
        :param abort_flag: The flag that is set when the worker should abort.
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
            abort_flag=abort_flag,
        )

    def output_worker_result(self) -> None:
        self.load_all_image_thumbnails()
        self.reload_current_image()
        logger.info("Output worker finished.")

    @Slot(wt.WorkerError)
    def output_worker_error(self, error: wt.WorkerError) -> None:
        logger.error("Output worker encountered an error.")
        gu.show_warning(self, "Output failed", f"Output generation failed:\n\n{error}")

    def output_worker_aborted(self) -> None:
        self.load_all_image_thumbnails()
        self.reload_current_image()
        self.thread_queue.clear()
        self.pushButton_refresh.setEnabled(True)
        logger.warning("Output worker aborted.")

    def start_profile_checker(self) -> None:
        """
        Start the profile checker thread.
        The process isn't very intensive, usually taking between 1 and 10 ms, but when run on the
        queue it prevents race conditions with the output worker.
        """
        worker = wt.Worker(self.check_profile_changes, no_progress_callback=True)
        worker.signals.error.connect(self.profile_checker_error)
        worker.signals.result.connect(self.profile_checker_result)
        self.thread_queue.start(worker)

    def check_profile_changes(self) -> Sequence[BadgeButton]:
        """
        Check if the current profile has changed for the outputs that exist.
        The regular ordered outputs progressively get more sensitive, so we can
        figure out when the first change happens and know that everything after
        that has changed as well, and vise versa, if something near the end is
        unchanged, we know that everything before it is unchanged as well.

        This doesn't work for the individually sensitive outputs, so we just check
        each of them.
        """

        logger.info("Profile changed. Checking for changes.")

        changed_buttons: list[BadgeButton] = []

        # Create lists of the buttons that have an output to check.
        independent_buttons: list[tuple[BadgeButton, imf.ProcessOutput]] = []
        ordered_buttons: list[tuple[BadgeButton, imf.ProcessOutput]] = []

        for button, output in self.button_map.items():
            # Check if the output is individually sensitive or has no path.
            proc_output: imf.ProcessOutput = self.image_obj.outputs[output]

            if proc_output.path is None:
                continue

            if output in imf.OUTPUTS_WITH_INDEPENDENT_PROFILE_SENSITIVITY:
                independent_buttons.append((button, proc_output))
            else:
                ordered_buttons.append((button, proc_output))

        # Handle the independent buttons first.
        for button, proc_output in independent_buttons:
            if not proc_output.is_unchanged(self.config.current_profile):
                changed_buttons.append(button)

        # Sanity check, do we even have any ordered buttons?
        if len(ordered_buttons) == 0:
            return changed_buttons

        # Perform a binary search on the ordered buttons, to find the first changed output.
        # But first check the bounds, first and last.
        # Cache the check results in a tri-state list. We can't use a typical cache because
        # the profile will change between runs.
        ordered_buttons_changed: list[bool | None] = [None] * len(ordered_buttons)

        # Keep track of the number of cache misses for the check function.
        change_check_calls = 0
        change_check_cache_misses = 0

        def check_changed(index: int) -> bool:
            nonlocal ordered_buttons_changed, ordered_buttons, self
            nonlocal change_check_cache_misses, change_check_calls
            change_check_calls += 1
            # logger.debug(
            #     f"Checking button {index}, with output {self.button_map[ordered_buttons[index][0]].name}"
            # )
            if (changed := ordered_buttons_changed[index]) is not None:
                return changed
            changed = ordered_buttons[index][1].is_changed(self.config.current_profile)
            change_check_cache_misses += 1
            ordered_buttons_changed[index] = changed
            return changed

        # Check the first and last buttons.
        if not check_changed(-1):
            # logger.debug(
            #     f"Determined that none of the ordered buttons changed in {change_check_calls} calls"
            #     f" ({1-change_check_cache_misses/change_check_calls:.0%} cache hits)."
            # )
            # Nothing is changed.
            return changed_buttons
        elif check_changed(0):
            # Everything is changed.
            ordered_buttons_changed = [True] * len(ordered_buttons)
        else:
            # Now we do the binary search, knowing that a change
            # happened somewhere between the first and last.
            low, high = 0, len(ordered_buttons) - 1
            current: int = (low + high) // 2

            # The logic of the search is as follows:
            # If the current button has changed but the previous one hasn't, then
            # current points to the first changed button.
            # Otherwise, if the current button has not changed, move low to current + 1.
            # If the current button has changed, move high to current - 1.
            while low <= high:
                # Already handled the boundary cases, so we know that the current button's
                # previous button exists and is the last unchanged one.
                if check_changed(current) and not check_changed(current - 1):
                    break
                elif not check_changed(current):
                    low = current + 1
                else:
                    high = current - 1
                current = (low + high) // 2

            # At this point, current points to the first changed button.
            # Everything from this point onwards is also changed,
            # and everything before it is unchanged.
            for idx in range(len(ordered_buttons_changed)):
                ordered_buttons_changed[idx] = idx >= current

            # logger.debug(
            #     f"Determined that none of the ordered buttons changed in {change_check_calls} calls"
            #     f" ({1-change_check_cache_misses/change_check_calls:.0%} cache hits)."
            # )

        # Update the flair for the buttons that have changed.
        for idx, (button, _) in enumerate(ordered_buttons):
            if ordered_buttons_changed[idx]:
                changed_buttons.append(button)

        return changed_buttons

    def profile_checker_result(self, changed_buttons: Sequence[BadgeButton]) -> None:
        """
        Update the flair on the buttons that have changed.

        :param changed_buttons: The buttons that have changed.
        """
        self.clear_change_flairs()
        # logger.debug(
        #     f"Setting change badge for "
        #     f"{len(changed_buttons)} buttons: {','.join(self.button_map[output].name for output in changed_buttons)}"
        # )
        for button in changed_buttons:
            self.set_change_flair(button)

    def profile_checker_error(self, error: wt.WorkerError) -> None:
        logger.error("Profile checker encountered an error.")
        gu.show_warning(self, "Profile check failed", f"Profile change check failed:\n\n{error}")

    def start_ocr_worker(self) -> None:
        """
        Start a worker to perform the OCR process on this image.
        """
        self.ocr_action.setEnabled(False)
        worker = wt.Worker(self.generate_ocr, abort_signal=self.abort_signal)
        worker.signals.progress.connect(self.progress_callback)
        worker.signals.finished.connect(self.ocr_worker_finished)
        worker.signals.result.connect(self.output_worker_result)
        worker.signals.error.connect(self.output_worker_error)
        self.thread_queue.start(worker)

    def generate_ocr(
        self, progress_callback: imf.ProgressSignal, abort_flag: wt.SharableFlag
    ) -> None:
        """
        Run OCR for the image.

        :param progress_callback: The callback given by the worker thread wrapper.
        :param abort_flag: The flag that is set when the worker should abort.
        """
        prc.perform_ocr(
            image_objects=[self.image_obj],
            output_file=None,
            csv_output=False,
            config=self.config,
            ocr_model=self.shared_ocr_model.get(),
            progress_callback=progress_callback,
            abort_flag=abort_flag,
        )

    def ocr_worker_finished(self) -> None:
        self.ocr_action.setEnabled(True)
        logger.info("OCR worker finished.")
