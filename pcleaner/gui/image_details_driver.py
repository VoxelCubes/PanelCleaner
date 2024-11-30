import shutil
from functools import partial
from pathlib import Path
from typing import Callable
from typing import Sequence

import PySide6.QtCore as Qc
import PySide6.QtGui as Qg
import PySide6.QtWidgets as Qw
from PySide6.QtCore import Slot, Signal
from loguru import logger

from pcleaner.helpers import tr
import pcleaner.config as cfg
import pcleaner.gui.gui_utils as gu
import pcleaner.gui.image_file as imf
import pcleaner.output_structures as ost
import pcleaner.gui.processing as prc
import pcleaner.gui.structures as gst
import pcleaner.gui.worker_thread as wt
from pcleaner.gui.CustomQ.CBadgeButton import BadgeButton
from pcleaner.gui.ui_generated_files.ui_ImageDetails import Ui_ImageDetails
import pcleaner.ocr.ocr as ocr

# The maximum size, will be smaller on one side if the image is not square.
THUMBNAIL_SIZE = (180, 180)
PUSHBUTTON_THUMBNAIL_MARGIN = 8
PUSHBUTTON_THUMBNAIL_SEPARATION = 8
SIDEBAR_COLUMNS = 2
BADGE_SIZE = 24


class FileFreshnessTracker:
    """
    Keep track of the last time a file was modified to determine if it has changed
    since the last time it was read.
    """

    _last_modified: dict[Path, float]

    def __init__(self):
        self._last_modified = {}

    def has_changed(self, path: Path) -> bool:
        """
        Check if the file has changed since the last time it was checked.

        :param path: The path to the file.
        :return: True if the file has changed, False otherwise.
        """
        try:
            last_modified = path.stat().st_mtime
        except OSError:
            logger.error(f"Failed to get last modified time for {path}")
            return True
        if last_modified != self._last_modified.get(path, None):
            self._last_modified[path] = last_modified
            return True
        return False

    def invalidate(self, path: Path | None = None) -> None:
        """
        Invalidate the last modified time for the given path.

        :param path: [Optional] The path to the file.
        """
        if path is not None:
            self._last_modified.pop(path, None)
        else:
            self._last_modified.clear()


class ImageDetailsWidget(Qw.QWidget, Ui_ImageDetails):
    """
    A widget that shows the details of an image object.
    """

    image_obj: imf.ImageFile  # The image object to show.
    current_image_path: Path | None  # The path of the image currently shown.

    button_map: dict[BadgeButton, ost.Output]

    # This set is just to figure out what labels might need extra horizontal space
    # in the case of long translations. Apparently the actual parent widget is
    # too retarded to keep track of its children, so we need to do it ourselves.
    output_labels: set[Qw.QLabel]

    freshness_tracker: FileFreshnessTracker

    config: cfg.Config
    shared_ocr_model: (
        gst.Shared[ocr.OCREngineFactory] | None
    )  # Must be handed over by the file table.
    thread_queue: Qc.QThreadPool
    progress_callback: Callable[[ost.ProgressData], None]
    abort_signal: Signal

    menu: Qw.QMenu  # The overflow menu for the export and ocr buttons.
    to_clipboard_action: Qg.QAction
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
        shared_ocr_model: gst.Shared[ocr.OCREngineFactory] | None = None,
        thread_queue: Qc.QThreadPool = None,
        progress_callback: Callable[[ost.ProgressData], None] = None,
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
        logger.debug(f"Opening details tab for {image_obj.path}")
        Qw.QWidget.__init__(self, parent)
        self.setupUi(self)

        self.freshness_tracker = FileFreshnessTracker()

        self.image_obj = image_obj
        self.config = config
        self.shared_ocr_model = shared_ocr_model
        self.button_map, self.output_labels = self.create_sidebar_buttons()

        self.first_load = True
        self.thread_queue = thread_queue
        self.progress_callback = progress_callback
        self.abort_signal = abort_signal

        # Clear sample text from labels that only update on user interaction.
        self.label_size.setText("")
        self.label_position.setText("0, 0")
        self.label_step.setText("")

        self.init_sidebar()
        self.load_image_thumbnails()
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

        self.to_clipboard_action = Qg.QAction(
            Qg.QIcon.fromTheme("edit-copy"), self.tr("Copy Image to Clipboard"), self
        )
        self.to_clipboard_action.triggered.connect(self.copy_image_to_clipboard)
        self.menu.addAction(self.to_clipboard_action)

        self.export_action = Qg.QAction(
            Qg.QIcon.fromTheme("document-save"), self.tr("Export Image"), self
        )
        self.export_action.triggered.connect(self.export_image)
        self.menu.addAction(self.export_action)

        self.ocr_action = Qg.QAction(
            Qg.QIcon.fromTheme("document-scan"), self.tr("OCR Image"), self
        )
        self.ocr_action.triggered.connect(self.start_ocr_worker)
        self.menu.addAction(self.ocr_action)

        self.pushButton_menu.setMenu(self.menu)

    def create_sidebar_buttons(self) -> tuple[dict[BadgeButton, ost.Output], set[Qw.QLabel]]:
        """
        Parse the image object's outputs to create a list of buttons in the side panel.

        Returns: A map of buttons to outputs and the labels that were created.
        """

        current_button_layout: Qw.QGridLayout
        current_button_index: int = 0
        last_step_name: str | None = None
        # Nuke the cache, if it exists.
        self.freshness_tracker.invalidate()

        def add_button(title: str | None) -> BadgeButton | Qw.QVBoxLayout:
            # Insert a new button into the current step's layout.
            button = BadgeButton()
            button.setCheckable(True)
            button.set_badge_size(BADGE_SIZE, PUSHBUTTON_THUMBNAIL_MARGIN)
            button.clicked.connect(partial(self.uncheck_all_other_buttons, button))
            button_widget = button

            # Create a title as a separate label widget and stack them vertically.
            if title is not None:
                nonlocal labels
                layout = Qw.QVBoxLayout()
                layout.setContentsMargins(0, 0, 0, 0)
                layout.setSpacing(2)  # The small spacing between the label and the image.
                label = Qw.QLabel(title)
                label.setObjectName("output_label")
                layout.addWidget(label)
                layout.addWidget(button)
                labels.add(label)
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
            current_button_layout.setObjectName(f"gridLayout_{title}")
            current_button_layout.setContentsMargins(0, 0, 0, 0)
            current_button_layout.setSpacing(PUSHBUTTON_THUMBNAIL_SEPARATION)
            current_button_index = 0
            self.sidebar_layout.addLayout(current_button_layout)

        buttons = {}
        labels = set()
        for output, proc_output in self.image_obj.outputs.items():
            # Add a step name label if it has changed and is not None.
            # Outputs with a none step name are not shown.
            if proc_output.step_name is None:
                continue
            elif proc_output.step_name != last_step_name:
                add_step_label(tr(proc_output.step_name, context="Process Steps"))
                last_step_name = proc_output.step_name

            button_title = (
                tr(proc_output.output_name, context="Process Steps")
                if proc_output.output_name is not None
                else None
            )
            new_button = add_button(button_title)
            buttons[new_button] = output

        return buttons, labels

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
            self.button_map, self.output_labels = self.create_sidebar_buttons()
            self.init_sidebar()
            self.load_image_thumbnails()

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

        # To account for long translation strings, check what the widest label is.
        # Ignoring the step name labels though, since they have double the width, they
        # are unlikely to be cut off.
        max_label_width = 0
        for label in self.output_labels:
            max_label_width = max(max_label_width, label.sizeHint().width())

        column_width = max(thumbnail_width, max_label_width)

        # Adjust the width of the scroll area to fit the buttons.
        scrollbar_width = Qw.QApplication.style().pixelMetric(Qw.QStyle.PM_ScrollBarExtent)
        margins_left, _, margins_right, _ = self.sidebar_layout.getContentsMargins()
        self.scrollArea.setFixedWidth(
            column_width * SIDEBAR_COLUMNS
            + PUSHBUTTON_THUMBNAIL_MARGIN * SIDEBAR_COLUMNS
            + PUSHBUTTON_THUMBNAIL_SEPARATION * (SIDEBAR_COLUMNS - 1)
            + scrollbar_width
            + margins_left
            + margins_right
            + 2,  # Arbitrary extra margin to make it look "right".
        )
        logger.debug(f"Setting scroll area width to {self.scrollArea.width()}")

        # Make each grid layout column take up the same column width.
        for grid_laypout in self.sidebar_layout.findChildren(Qw.QGridLayout):
            for i in range(grid_laypout.columnCount()):
                grid_laypout.setColumnMinimumWidth(i, column_width)

        # Resize all the buttons.
        # self.scrollArea.setFixedWidth()
        for button in self.button_map:
            button.setFixedSize(
                thumbnail_width + PUSHBUTTON_THUMBNAIL_MARGIN,
                thumbnail_height + PUSHBUTTON_THUMBNAIL_MARGIN,
            )
            button.setIconSize(Qc.QSize(thumbnail_width, thumbnail_height))
            button.clicked.connect(partial(self.switch_to_image, button))

    def load_image_thumbnails(self, only_step: ost.Step | None = None) -> None:
        """
        Load all the images into the buttons.

        :param only_step: [Optional] Only load the images for this step.
        """

        def check_output(current_output: ost.Output) -> bool:
            return only_step is None or ost.output_to_step[current_output] == only_step

        current_button = self.current_button()

        for button, output in self.button_map.items():
            if not check_output(output):
                continue

            proc_output = self.image_obj.outputs[output]
            if proc_output.path is not None:
                # Check if the file has even changed since last time.
                if not self.freshness_tracker.has_changed(proc_output.path):
                    continue

                try:
                    button.setIcon(Qg.QIcon(str(proc_output.path)))
                    button.setText("")

                    if button is current_button:
                        self.switch_to_image(button)
                except OSError:
                    gu.show_exception(
                        self,
                        self.tr("Loading Error"),
                        self.tr("Failed to load image '{path}'").format(path=proc_output.path),
                    )
            else:
                # Clear any pixmaps that might be there.
                button.setIcon(Qg.QIcon())
                button.setText(self.tr("Generate Me"))
        # Update the badges on the buttons.
        self.start_profile_checker()

    def request_has_conflict(self, proc_output: imf.ProcessOutput) -> bool:
        """
        Check if the user made a silly request, like asking for an inpainted output when
        inpainting was disabled in the profile.
        Alternatively, pcleaner could silently override that setting this one time, but that
        would be confusing to a user who doesn't know that this needs to be enabled first,
        and would otherwise wonder why he isn't getting inpainted outputs when running the
        batch cleaning.

        :param proc_output: The requested output.
        :return: True is this output can't be generated.
        """
        if (
            proc_output.step_name == "Denoiser"
            and not self.config.current_profile.denoiser.denoising_enabled
        ):
            logger.warning("Tried denoising when it was disabled in the profile.")
            gu.show_warning(
                self,
                self.tr("Impossible Request"),
                self.tr(
                    "Denoising is disabled in the current profile, this output can't be generated.\n"
                    "Please enable denoising in the profile settings and try again."
                ),
            )
            return True

        if (
            proc_output.step_name == "Inpainter"
            and not self.config.current_profile.inpainter.inpainting_enabled
        ):
            logger.warning("Tried inpainting when it was disabled in the profile.")
            gu.show_warning(
                self,
                self.tr("Impossible Request"),
                self.tr(
                    "Inpainting is disabled in the current profile, this output can't be generated.\n"
                    "Please enable inpainting in the profile settings and try again."
                ),
            )
            return True

        return False

    def switch_to_image(self, button: BadgeButton) -> None:
        """
        Show the image in the button in the image view.

        :param button: The button that was clicked.
        """
        output = self.button_map[button]
        proc_output: imf.ProcessOutput = self.image_obj.outputs[output]
        self.label_step.setText(tr(proc_output.description, context="Process Steps"))
        self.current_image_path = proc_output.path
        if not proc_output.has_path():
            # Clear whatever image is currently shown.
            self.image_viewer.set_image(None)
            self.label_position.setText("0, 0")
            self.widget_footer_info.hide()
            self.stackedWidget.setCurrentWidget(self.page_no_image)
            self.export_action.setEnabled(False)
            self.pushButton_refresh.setEnabled(False)
            if self.request_has_conflict(proc_output):
                self.uncheck_all_other_buttons(None)
                return
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
            except OSError:
                gu.show_exception(
                    self,
                    self.tr("Image not found."),
                    self.tr("Image at {path} does not exist:").format(path=proc_output.path),
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

    def copy_image_to_clipboard(self) -> None:
        """
        If the image exists, open a save dialog to copy it to a new location.
        """
        if self.current_image_path is None:
            return
        if not self.current_image_path.is_file():
            return

        mime_data = Qc.QMimeData()
        mime_data.setUrls([Qc.QUrl.fromLocalFile(str(self.current_image_path))])
        clipboard = Qw.QApplication.clipboard()
        clipboard.setMimeData(mime_data)

    def export_image(self) -> None:
        """
        If the image exists, open a save dialog to copy it to a new location.
        """
        if self.current_image_path is None:
            return
        if not self.current_image_path.is_file():
            return

        save_path, _ = Qw.QFileDialog.getSaveFileName(
            self, self.tr("Export Image"), filter="PNG (*.png)"
        )
        if save_path:
            save_path = Path(save_path).with_suffix(".png")
            try:
                shutil.copy(self.current_image_path, save_path)
                logger.info(f"Exported image to {save_path}")
            except OSError:
                gu.show_exception(
                    self, self.tr("Export failed"), self.tr("Failed to export image:")
                )

    def current_button(self) -> BadgeButton | None:
        """
        Get the currently selected button.

        Returns: The button that is currently selected, or None if no button is selected.
        """
        for button in self.button_map:
            if button.isChecked():
                return button
        return None

    @Slot()
    def uncheck_all_other_buttons(self, checked_button: BadgeButton | None) -> None:
        """
        Uncheck all buttons except the one that was checked.

        :param checked_button: The button that was checked.
        """
        for button in self.button_map:
            if checked_button is None or button is not checked_button:
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

    def start_output_worker(self, output: ost.Output) -> None:
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
        self, output: ost.Output, progress_callback: ost.ProgressSignal, abort_flag: wt.SharableFlag
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
            split_files={},
            target_outputs=[output],
            output_dir=None,
            config=self.config,
            ocr_processor=self.shared_ocr_model.get(),
            progress_callback=progress_callback,
            batch_metadata=gst.BatchMetadata(),
            abort_flag=abort_flag,
        )

    def output_worker_result(self) -> None:
        self.load_image_thumbnails()
        logger.info("Output worker finished.")

    @Slot(wt.WorkerError)
    def output_worker_error(self, error: wt.WorkerError) -> None:

        if gu.check_unsupported_cuda_error(self, error):
            return

        gu.show_exception(
            self, self.tr("Output Failed"), self.tr("Output generation failed:"), error
        )

    def output_worker_aborted(self) -> None:
        self.load_image_thumbnails()
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

        changed_buttons: list[BadgeButton] = []

        # Create lists of the buttons that have an output to check.
        independent_buttons: list[tuple[BadgeButton, imf.ProcessOutput]] = []
        ordered_buttons: list[tuple[BadgeButton, imf.ProcessOutput]] = []

        for button, output in self.button_map.items():
            # Check if the output is individually sensitive or has no path.
            proc_output: imf.ProcessOutput = self.image_obj.outputs[output]

            if proc_output.path is None:
                continue

            if output in ost.OUTPUTS_WITH_INDEPENDENT_PROFILE_SENSITIVITY:
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
        gu.show_exception(
            self, self.tr("Profile check failed"), self.tr("Profile change check failed:"), error
        )

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
        self, progress_callback: ost.ProgressSignal, abort_flag: wt.SharableFlag
    ) -> None:
        """
        Run OCR for the image.

        :param progress_callback: The callback given by the worker thread wrapper.
        :param abort_flag: The flag that is set when the worker should abort.
        """
        prc.perform_ocr(
            image_objects=[self.image_obj],
            split_files={},
            output_file=None,
            csv_output=False,
            config=self.config,
            ocr_engine_factory=self.shared_ocr_model.get(),
            progress_callback=progress_callback,
            batch_metadata=gst.BatchMetadata(),
            abort_flag=abort_flag,
        )

    def ocr_worker_finished(self) -> None:
        self.ocr_action.setEnabled(True)
        logger.debug("OCR worker finished.")
