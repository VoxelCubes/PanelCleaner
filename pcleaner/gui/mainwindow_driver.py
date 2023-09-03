from copy import deepcopy
from functools import partial
from importlib import resources
from typing import Sequence
from pathlib import Path
import time

import PySide6.QtCore as Qc
import PySide6.QtGui as Qg
import PySide6.QtWidgets as Qw
from PySide6.QtCore import Slot, Signal
from logzero import logger
from manga_ocr import MangaOcr

import pcleaner.cli_utils as cu
import pcleaner.config as cfg
import pcleaner.analytics as an
import pcleaner.gui.gui_utils as gu
import pcleaner.gui.image_file as imf
import pcleaner.gui.new_profile_driver as npd
import pcleaner.gui.processing as prc
import pcleaner.gui.profile_parser as pp
import pcleaner.gui.structures as gst
import pcleaner.structures as st
import pcleaner.gui.worker_thread as wt
import pcleaner.helpers as hp
import pcleaner.profile_cli as pc
from pcleaner import __display_name__, __version__
from pcleaner import data
from pcleaner.gui.file_table import Column
from pcleaner.gui.ui_generated_files.ui_Mainwindow import Ui_MainWindow


ANALYTICS_COLUMNS = 72


# noinspection PyUnresolvedReferences
class MainWindow(Qw.QMainWindow, Ui_MainWindow):
    config: cfg.Config = None

    label_stats: Qw.QLabel

    toolBox_profile: pp.ProfileToolBox
    # Optional shared instance of the OCR model to save time due to its slow loading.
    shared_ocr_model: gst.Shared[gst.OCRModel]

    threadpool: Qc.QThreadPool  # Used for loading images and other gui tasks.
    thread_queue: Qc.QThreadPool  # Used for tasks that need to run sequentially, without blocking the gui.

    progress_current: int
    progress_step_start: imf.Step | None  # When None, no processing is running.

    profile_values_changed = Signal()

    # Save a copy of the last applied profile to prevent multiple profile change calls
    # by the user when the profile didn't actually change.
    last_applied_profile: cfg.Profile | None

    def __init__(self):
        Qw.QMainWindow.__init__(self)
        self.setupUi(self)
        self.setWindowTitle(f"{__display_name__} {__version__}")
        self.setWindowIcon(Qg.QIcon(":/logo-tiny.png"))

        self.progress_current: int = 0
        self.progress_step_start: imf.Step | None = None

        self.config = cfg.load_config()
        self.shared_ocr_model = gst.Shared[gst.OCRModel]()

        self.last_applied_profile = None

        # TODO eventually check for the existence of the text detector models on startup.

        # This threadpool is used for parallelizing tasks the gui relies on, such as loading images.
        # This isn't used for processing, since that is handled by the multiprocessing module
        # for true parallelism.
        self.threadpool = Qc.QThreadPool.globalInstance()
        logger.info(f"Multithreading with maximum {self.threadpool.maxThreadCount()} threads")

        # This threadpool acts as a queue for processing runs, therefore only allowing one thread at a time.
        # This is because they must share the same cache directory, which isn't thread safe if operating on the same image.
        # Additionally, this allows each requested output to check if it was already fulfilled
        # in a previous run, and if so, skip it.
        self.thread_queue = Qc.QThreadPool()
        self.thread_queue.setMaxThreadCount(1)

        # Share core objects with the file table.
        # Since the file table is created by the ui loader, we can't pass them to the constructor.
        self.file_table.set_config(self.config)
        self.file_table.set_shared_ocr_model(self.shared_ocr_model)
        self.file_table.set_thread_queue(self.thread_queue)

        self.start_initialization_worker()

        self.initialize_ui()

        Qc.QTimer.singleShot(0, self.post_init)

    def initialize_ui(self):
        self.hide_progress_drawer()
        self.set_up_statusbar()
        self.initialize_profiles()
        self.initialize_analytics_view()
        self.disable_running_cleaner()

        # Allow the table to accept file drops and hide the PATH column.
        self.file_table.setAcceptDrops(True)
        self.file_table.setColumnHidden(Column.PATH, True)
        self.file_table.setColumnWidth(Column.FILENAME, 200)
        self.file_table.setColumnWidth(Column.SIZE, 100)
        self.frame_greeter.drop_signal.connect(self.file_table.dropEvent)
        self.file_table.table_is_empty.connect(lambda: self.stackedWidget_images.setCurrentIndex(0))
        self.file_table.table_not_empty.connect(
            lambda: self.stackedWidget_images.setCurrentIndex(1)
        )
        # Hide the close button for the file table tab.
        self.image_tab.tabBar().setTabButton(0, Qw.QTabBar.RightSide, None)
        # Display a theme icon on the left side of the tab.
        self.image_tab.tabBar().setTabIcon(0, Qg.QIcon.fromTheme("view-form-symbolic"))

        # Set up the drop panel.
        label_font = self.label_drop.font()
        label_font.setPointSize(round(label_font.pointSize() * 1.5))
        self.label_drop.setFont(label_font)
        icon_size = round(imf.THUMBNAIL_SIZE * 1.5)
        self.label_drop_icon.setPixmap(Qg.QIcon.fromTheme("download").pixmap(icon_size, icon_size))

        # Connect signals.
        self.comboBox_current_profile.hookedCurrentIndexChanged.connect(self.change_current_profile)
        self.action_add_files.triggered.connect(self.file_table.browse_add_files)
        self.action_add_folders.triggered.connect(self.file_table.browse_add_folders)
        self.action_clear_files.triggered.connect(self.file_table.clear_files)
        self.action_clear_files.triggered.connect(self.image_tab.clear_files)
        self.file_table.requesting_image_preview.connect(
            partial(
                self.image_tab.open_image,
                config=self.config,
                shared_ocr_model=self.shared_ocr_model,
                thread_queue=self.thread_queue,
                progress_callback=self.show_current_progress,
                profile_changed_signal=self.profile_values_changed,
            )
        )
        self.pushButton_start.clicked.connect(self.start_processing)

        # Connect profile changes to file table refreshes, due to the processing size being profile-dependent.
        self.profile_values_changed.connect(self.file_table.update_all_rows)

        # Set the current palette to use the inactive color for placeholder text.
        palette = self.palette()
        placeholder_color = palette.color(Qg.QPalette.Inactive, Qg.QPalette.Text)
        palette.setColor(Qg.QPalette.PlaceholderText, placeholder_color)
        self.setPalette(palette)
        # Make the progress drawer use the alternate background color.
        alternate_color = palette.color(Qg.QPalette.AlternateBase)
        self.widget_progress_drawer.setStyleSheet(
            f"background-color: {alternate_color.name()};"
            + self.widget_progress_drawer.styleSheet()
        )

    def post_init(self):
        """
        Handle any initialization that must be done after the window is shown.
        """
        # Make the profile groupbox the width of 5 save buttons as a good enough heuristic.
        header_button_width = self.pushButton_save_profile.width()
        profile_width, table_width, output_width = self.splitter.sizes()
        # Add the difference to the table width.
        self.splitter.setSizes(
            [
                header_button_width * 5,
                table_width + profile_width - 5 * header_button_width,
                output_width,
            ]
        )

    # ========================================== UI Toggles ==========================================

    def hide_progress_drawer(self):
        self.widget_progress_drawer.hide()

    def show_progress_drawer(self):
        self.widget_progress_drawer.show()

    def enable_running_cleaner(self):
        logger.info("Enabling running cleaner")
        self.pushButton_start.setEnabled(True)

    def disable_running_cleaner(self):
        logger.info("Disabling running cleaner")
        self.pushButton_start.setEnabled(False)

    # ========================================== Initialization Workers ==========================================

    def start_initialization_worker(self):
        """
        Perform various slow startup procedures in a thread that would otherwise make the gui lag.

        In particular:
        - Clean the cache.
        - Load the text detection model.
        - Load the OCR model.
        """
        logger.debug(f"Worker Thread cleaning cache")
        cache_worker = wt.Worker(self.clean_cache, no_progress_callback=True)
        cache_worker.signals.error.connect(
            partial(self.generic_worker_error, context="Failed to clean cache.")
        )
        self.threadpool.start(cache_worker)

        logger.debug(f"Worker Thread loading OCR model.")
        ocr_worker = wt.Worker(self.load_ocr_model, no_progress_callback=True)
        ocr_worker.signals.error.connect(
            partial(
                self.generic_worker_error,
                context="Failed to load OCR model. OCR impossible, moderate cleaning impact.",
            )
        )
        # Add it to the queue, to make sure it finishes before any processing starts.
        self.thread_queue.start(ocr_worker)

    def load_ocr_model(self):
        t_start = time.time()
        self.statusbar.showMessage(f"Loading OCR model...")
        self.shared_ocr_model.set(MangaOcr())
        logger.info(f"Loaded OCR model ({time.time()-t_start:.2f}s)")
        self.statusbar.showMessage(f"Loaded OCR model.")
        self.enable_running_cleaner()

    def generic_worker_error(self, error: wt.WorkerError, context: str = ""):
        """
        Simply show the user the error.

        :param error: The worker error object.
        :param context: A string to add to the error message.
        """
        logger.error(f"Worker error: {error}")
        if not context:
            gu.show_warning(self, "Error", f"Encountered error: {error}")
        else:
            gu.show_warning(self, "Error", f"{context}\n\nEncountered error: {error}")

    def closeEvent(self, event: Qg.QCloseEvent):
        """
        Notify config on close.
        """
        logger.info("Closing window.")
        # self.abort_translation_worker.emit()
        # if self.threadpool.activeThreadCount():
        #     self.statusbar.showMessage("Waiting for threads to finish...")
        #     # Process Qt events so that the message shows up.
        #     Qc.QCoreApplication.processEvents()
        #     self.threadpool.waitForDone()
        #
        # nuke_epub_cache()
        # event.accept()

    def clean_cache(self):
        cache_dir = self.config.get_cleaner_cache_dir()
        if len(list(cache_dir.glob("*"))) > 0:
            cu.empty_cache_dir(cache_dir)

    def initialize_analytics_view(self):
        """
        Set up the text edit for analytics.
        """
        # Set the font to monospace, using the included font.
        # The font is stored in the data module. Noto Mono is a free font.
        # Load it from file to be cross platform.
        self.textEdit_analytics.clear()
        with resources.files(data) as data_path:
            font_path = data_path / "NotoMono-Regular.ttf"
        font_id = Qg.QFontDatabase.addApplicationFont(str(font_path))
        if font_id != -1:
            logger.info("Loaded included font")
        else:
            logger.error(
                f"Failed to load included font from '{str(font_path)}'. Using backup monospace font"
            )
        self.textEdit_analytics.setReadOnly(True)
        self.textEdit_analytics.setLineWrapMode(Qw.QTextEdit.NoWrap)

        font_metrics = Qg.QFontMetrics(self.textEdit_analytics.font())
        char_width = font_metrics.averageCharWidth()
        columns = ANALYTICS_COLUMNS
        required_width = char_width * columns

        logger.debug(
            f"Char width: {char_width}, columns: {columns}, required width: {required_width}"
        )

        # Adjust for margins, scroll bar, and borders
        text_margins = self.textEdit_analytics.contentsMargins()
        frame_margins = self.frame_output.contentsMargins()
        scrollbar_width = Qw.QApplication.style().pixelMetric(Qw.QStyle.PM_ScrollBarExtent)
        total_width = (
            required_width
            + text_margins.left()
            + text_margins.right()
            + scrollbar_width
            + frame_margins.left()
            + frame_margins.right()
        )

        self.frame_output.setMaximumWidth(total_width)

        logger.debug(f"Set text edit width to {total_width}")

    # ========================================== Profiles ==========================================

    def initialize_profiles(self):
        """
        Load the available profiles and display the default profile.
        """
        all_profiles: list[tuple[str, Path | None]] = [(cfg.DEFAULT_PROFILE_NAME, None)]
        for profile_name, profile_path in self.config.saved_profiles.items():
            all_profiles.append((profile_name, profile_path))

        logger.debug(f"Found profiles: {all_profiles}")

        self.comboBox_current_profile.clear()
        for profile_name, profile_path in all_profiles:
            self.comboBox_current_profile.addTextItemLinkedData(profile_name, profile_path)

        # Set the current profile to the default profile.
        # If this is the default profile, then staying on the 0th index is fine.
        if self.config.default_profile:
            self.comboBox_current_profile.setCurrentIndexByText(self.config.default_profile)

        # Populate default profile list.
        self.menu_set_default_profile.clear()
        for profile_name, profile_path in all_profiles:
            action = Qg.QAction(profile_name, self)
            action.setCheckable(True)
            action.triggered.connect(partial(self.handle_set_default_profile, profile_name))
            self.menu_set_default_profile.addAction(action)
            action.setChecked(
                profile_name
                == (
                    self.config.default_profile
                    if self.config.default_profile
                    else cfg.DEFAULT_PROFILE_NAME
                )
            )

        # Load the ProfileToolBox widget.
        self.toolBox_profile = pp.ProfileToolBox(self)
        inner_layout = Qw.QVBoxLayout()
        inner_layout.setContentsMargins(0, 0, 0, 0)
        inner_layout.addWidget(self.toolBox_profile)
        self.toolBox_profile_frame.setLayout(inner_layout)
        self.config.load_profile(self.config.default_profile)

        # Load the structure.
        structure = pp.parse_profile_structure(self.config.current_profile)
        self.toolBox_profile.load_profile_structure(structure)

        self.load_current_profile()
        self.comboBox_current_profile.set_pre_change_hook(self.profile_change_check)

        # Connect signals.
        self.toolBox_profile.values_changed.connect(self.handle_profile_values_changed)
        self.pushButton_reset_profile.clicked.connect(self.reset_profile)
        self.pushButton_save_profile.clicked.connect(self.save_profile)
        self.pushButton_apply_profile.clicked.connect(self.apply_profile)
        self.action_save_profile.triggered.connect(self.save_profile)
        self.action_save_profile_as.triggered.connect(partial(self.save_profile, save_as=True))
        self.action_import_profile.triggered.connect(self.import_profile)
        self.action_new_profile.triggered.connect(partial(self.save_profile, make_new=True))
        self.action_delete_profile.triggered.connect(self.delete_profile)

    def handle_set_default_profile(self, profile_name: str):
        """
        Set the default profile in the config.
        """
        logger.debug(f"Setting default profile to {profile_name}")
        self.config.default_profile = (
            profile_name if profile_name != cfg.DEFAULT_PROFILE_NAME else None
        )
        self.config.save()
        # Update the menu.
        for action in self.menu_set_default_profile.actions():
            action.setChecked(action.text() == profile_name)

    def import_profile(self):
        """
        Open a file picker and add the profile to the profile list.
        """
        logger.debug("Importing profile.")
        file_path = Qw.QFileDialog.getOpenFileName(
            self,
            "Import Profile",
            "",
            "Profile Files (*.conf)",
        )[0]
        if file_path:
            logger.debug(f"Importing profile from {file_path}")
            profile_name = Path(file_path).stem
            success, msg = pc.add_profile(self.config, profile_name, file_path)
            if success:
                gu.show_info(self, "Profile Imported", msg)
            else:
                gu.show_warning(self, "Import Error", msg)
                return

            self.add_new_profile_to_gui(profile_name, Path(file_path))

    def delete_profile(self):
        """
        Ask and then delete the current profile.
        Of course, the default profile cannot be deleted.
        :return:
        """
        # if not self.profile_change_check():
        #     return
        logger.debug("Deleting profile.")
        profile_name = self.comboBox_current_profile.currentText()

        if self.comboBox_current_profile.currentText() == cfg.DEFAULT_PROFILE_NAME:
            gu.show_warning(self, "Failed to Delete", "The default profile cannot be deleted.")
            return
        response = gu.show_question(
            self, "Delete Profile", f"Are you sure you want to delete the profile {profile_name}?"
        )
        if response == Qw.QMessageBox.Yes:
            profile_file = self.config.saved_profiles[profile_name]
            self.config.remove_profile(profile_name)
            self.config.save()
            if profile_file.is_file():
                try:
                    profile_file.unlink()
                except OSError as e:
                    gu.show_warning(
                        self, "Delete Error", "Failed to delete the profile\n" + e.what()
                    )

            # To suppress the change check since we don't care about discarding the current changes.
            self.toolBox_profile.reset_all()
            self.comboBox_current_profile.removeItem(self.comboBox_current_profile.currentIndex())
            for action in self.menu_set_default_profile.actions():
                if action.text() == profile_name:
                    self.menu_set_default_profile.removeAction(action)
                    break

    def check_profile_difference_sice_last_apply(self) -> bool:
        """
        Compare the current profile to the last applied profile.

        :return: True if the profiles are different, False otherwise.
        """
        if self.last_applied_profile is None:
            return True

        # Read the current profile and then compare.
        profile_in_gui = cfg.Profile()
        self.toolBox_profile.get_profile_values(profile_in_gui)
        return profile_in_gui != self.last_applied_profile

    def set_last_applied_profile(self):
        """
        Set the last applied profile to the current profile.
        """
        self.last_applied_profile = deepcopy(self.config.current_profile)

    def load_current_profile(self):
        """
        Load the current profile.
        """
        logger.debug("Loading current profile.")
        self.toolBox_profile.set_profile_values(self.config.current_profile)
        self.set_last_applied_profile()
        self.profile_values_changed.emit()

    def profile_change_check(self) -> bool:
        """
        Check if the current profile has unsaved changes.

        :return: True if the profile is ready to be changed, False otherwise.
        """
        logger.warning("Profile change check")
        # Check if the profile is still in the list.
        if self.comboBox_current_profile.currentText() not in list(
            self.config.saved_profiles.keys()
        ) + [cfg.DEFAULT_PROFILE_NAME]:
            logger.debug("Profile not in list.")
            # The profile is not in the list, so it must have been deleted.
            return True

        if self.toolBox_profile.is_modified():
            logger.debug(
                f"Previous profile {self.comboBox_current_profile.currentText()} has unsaved changes."
            )
            # Warn the user that he will lose unsaved changes.
            message = (
                f"The profile '{self.comboBox_current_profile.currentText()}' has unsaved changes.\n"
                f"Switching profiles will discard changes to the current profile."
            )
            response = gu.show_question(
                self,
                "Unsaved changes",
                message,
                Qw.QMessageBox.Cancel | Qw.QMessageBox.Save | Qw.QMessageBox.Discard,
            )
            if response == Qw.QMessageBox.Cancel:
                logger.debug("Profile change aborted.")
                # Abort the profile change.
                return False
            elif response == Qw.QMessageBox.Save:
                logger.debug("Saving previous profile.")
                # Save the current profile.
                self.save_profile()
            elif response == Qw.QMessageBox.Discard:
                # Continue as normal.
                logger.debug("Discarding previous profile changes.")
            else:
                raise ValueError(f"Invalid response: {response}")

        return True

    @Slot()
    def change_current_profile(self):
        """
        Set the config option to match the current profile selector, then load it.
        """
        profile_name = self.comboBox_current_profile.currentText()
        self.config.load_profile(profile_name)
        self.load_current_profile()

    @Slot()
    def handle_profile_values_changed(self):
        """
        Handle the profile values changing.
        """
        dirty = self.toolBox_profile.is_modified()
        self.pushButton_apply_profile.setEnabled(self.check_profile_difference_sice_last_apply())
        self.pushButton_save_profile.setEnabled(dirty)
        self.pushButton_reset_profile.setEnabled(dirty)
        self.action_save_profile.setEnabled(dirty)

    def reset_profile(self):
        """
        Reset the current profile.
        """
        self.toolBox_profile.reset_all()
        self.handle_profile_values_changed()

    def apply_profile(self):
        """
        Apply the current profile.
        Read the current settings and broadcast profile changes.
        """
        logger.info("Applying profile.")
        self.toolBox_profile.get_profile_values(self.config.current_profile)
        self.handle_profile_values_changed()
        self.set_last_applied_profile()
        self.profile_values_changed.emit()
        self.pushButton_apply_profile.setEnabled(False)

    def save_profile(self, save_as: bool = False, make_new: bool = False):
        """
        Save the current profile.

        :param save_as: Whether to save as a new profile.
        :param make_new: Whether to make a new profile.
        """
        # Grab the path from the combobox's linked data. If it is none, this is the
        # default profile, so we need to save it as a new profile.
        profile_path = self.comboBox_current_profile.currentLinkedData()
        profile_name = self.comboBox_current_profile.currentText()
        if profile_path is None or make_new:
            save_as = True

        if profile_path is None and not make_new:
            # Trying to save over the default profile.
            profile_path, profile_name = self.get_new_profile_path(show_protection_hint=True)
        elif save_as:
            profile_path, profile_name = self.get_new_profile_path()

        # If the path is still none, the dialog was canceled.
        if profile_path is None:
            logger.info("User canceled profile save.")
            return

        if make_new:
            success, msg = pc.new_profile(self.config, profile_name, profile_path)
            if success:
                gu.show_info(self, "Profile Created", msg)
                self.add_new_profile_to_gui(profile_name, profile_path)
            else:
                gu.show_warning(self, "Create Error", msg)
                return
        else:
            # Proceed to write the profile.
            logger.info(f"Saving profile to {profile_path}")
            self.toolBox_profile.get_profile_values(self.config.current_profile)
            success = self.config.current_profile.write(profile_path)
            if not success:
                logger.error("Failed to save profile.")
                self.statusbar.showMessage(f"Failed to save profile to {profile_path}")
                gu.show_critical(self, "Save Error", "Failed to save profile.")
                return

            logger.info("Profile saved successfully.")
            self.statusbar.showMessage(f"Profile saved to {profile_path}")
            if save_as:
                self.config.add_profile(profile_name, profile_path)
                if not self.config.save():
                    logger.error("Failed to save config.")
                    self.statusbar.showMessage("Failed to save config.")
                    gu.show_critical(
                        self,
                        "Save Error",
                        "Failed to save the new profile to the configuration file.",
                    )
                    return
                # To suppress the change check since we don't care about discarding the current changes.
                self.toolBox_profile.reset_all()

                # Add the new profile to the combobox.
                self.add_new_profile_to_gui(profile_name, profile_path)

        self.config.load_profile(profile_name)
        self.load_current_profile()
        self.handle_profile_values_changed()

    def add_new_profile_to_gui(self, profile_name: str, profile_path: Path):
        self.comboBox_current_profile.addTextItemLinkedData(profile_name, profile_path)
        self.comboBox_current_profile.setCurrentIndexByLinkedData(profile_path)
        self.menu_set_default_profile.addAction(profile_name)
        self.menu_set_default_profile.actions()[-1].triggered.connect(
            partial(self.handle_set_default_profile, profile_name)
        )
        self.menu_set_default_profile.actions()[-1].setCheckable(True)

    @staticmethod
    def get_new_profile_path(
        show_protection_hint: bool = False,
    ) -> tuple[Path, str] | tuple[None, None]:
        """
        Open a save dialog to save the current profile.

        :param show_protection_hint: Whether to show a hint about protecting the default profile.
        """
        default_path = cu.get_default_profile_path()
        new_profile_dialog = npd.NewProfileDialog(
            default_path, show_protection_hint, cfg.RESERVED_PROFILE_NAMES
        )
        response = new_profile_dialog.exec()
        if response == Qw.QDialog.Accepted:
            return new_profile_dialog.get_save_path(), new_profile_dialog.get_name()

        return None, None

    # ========================================== Processing ==========================================

    def start_processing(self):
        """
        Start processing all files in the table.
        """
        self.disable_running_cleaner()
        # Figure out what outputs are requested, depending on the checkboxes and the profile.
        request_cleaned = self.checkBox_save_clean.isChecked()
        request_mask = self.checkBox_save_mask.isChecked()
        request_text = self.checkBox_save_text.isChecked()

        requested_outputs = []

        if self.config.current_profile.denoiser.denoising_enabled:
            if request_cleaned:
                requested_outputs.append(imf.Output.denoised_image)
            if request_mask:
                requested_outputs.append(imf.Output.denoiser_mask)
        else:
            if request_cleaned:
                requested_outputs.append(imf.Output.masked_image)
            if request_mask:
                requested_outputs.append(imf.Output.final_mask)

        if request_text:
            requested_outputs.append(imf.Output.isolated_text)

        requested_outputs.append(imf.Output.write_output)

        logger.info(f"Requested outputs: {requested_outputs}")

        output_str = self.lineEdit_out_directory.text()
        output_directory = Path(output_str if output_str else "cleaned")
        image_files = self.file_table.get_image_files()
        config = deepcopy(self.config)

        worker = wt.Worker(
            self.generate_output, requested_outputs, output_directory, image_files, config
        )
        worker.signals.progress.connect(self.show_current_progress)
        worker.signals.result.connect(self.output_worker_result)
        worker.signals.error.connect(self.output_worker_error)
        worker.signals.finished.connect(self.output_worker_finished)
        self.thread_queue.start(worker)

    def generate_output(
        self,
        outputs: list[imf.Output],
        output_directory: Path,
        image_files: list[imf.ImageFile],
        config: cfg.Config,
        progress_callback: imf.ProgressSignal,
    ) -> None:
        """
        Generate the given output, if there doesn't yet exist a valid output for it.
        Then output it to the given directory.

        :param outputs: The outputs to generate.
        :param output_directory: The directory to output to.
        :param image_files: The image files to process.
        :param config: The config to use.
        :param progress_callback: The callback given by the worker thread wrapper.
        """

        # Start the processor.
        prc.generate_output(
            image_objects=image_files,
            target_outputs=outputs,
            output_dir=output_directory,
            config=config,
            ocr_model=self.shared_ocr_model.get(),
            progress_callback=progress_callback,
        )

    def output_worker_result(self):
        gu.show_info(self, "Processing Finished", "Finished processing all files.")
        logger.info("Output worker finished.")

    def output_worker_finished(self):
        self.hide_progress_drawer()
        self.progress_step_start = None
        self.progress_current = 0
        self.enable_running_cleaner()

    @Slot(wt.WorkerError)
    def output_worker_error(self, e):
        gu.show_warning(
            self, "Processing Error", f"Encountered an error while processing files.\n\n{e}"
        )
        logger.error(f"Output worker encountered an error:\n{e}")

    """
    Log file
    """

    def set_up_statusbar(self):
        """
        Add a label to show the current char total and time estimate.
        Add a flat button to the statusbar to offer opening the config file.
        Add a flat button to the statusbar to offer opening the log file.
        """
        self.statusbar.setSizeGripEnabled(False)
        self.statusbar.setContentsMargins(0, 0, 6, 0)

        self.label_stats = Qw.QLabel("")
        self.statusbar.addPermanentWidget(self.label_stats)

        button_config = Qw.QPushButton("Open Config")
        button_config.clicked.connect(partial(hp.open_file, cu.get_config_path()))
        button_config.setFlat(True)
        self.statusbar.addPermanentWidget(button_config)

        button_log = Qw.QPushButton("Open Log")
        button_log.clicked.connect(partial(hp.open_file, cu.get_log_path()))
        button_log.setFlat(True)
        self.statusbar.addPermanentWidget(button_log)

    """
    Simple UI manipulation functions
    """

    @Slot(imf.ProgressData)
    def show_current_progress(self, progress_data: imf.ProgressData):
        if progress_data.progress_type == imf.ProgressType.start:
            # Processing begins, initialize what needs to be.
            # Specifically, clear the analytics panel.
            self.textEdit_analytics.clear()
            return

        elif progress_data.progress_type == imf.ProgressType.begin_step:
            logger.info(f"Progress beginning step: {progress_data}")
            # This marks the beginning of a new processing step.
            self.show_progress_drawer()
            self.progress_current = 0

            if self.progress_step_start is None:
                # This is the first step.
                self.progress_step_start = progress_data.current_step
                # Set the target label, we don't need to update this multiple times.
                self.label_target_outputs.setText(
                    ", ".join(
                        pp.to_display_name(o.name).replace("Ai ", "AI ")
                        for o in progress_data.target_outputs
                    )
                )

        elif progress_data.progress_type == imf.ProgressType.incremental:
            self.progress_current += progress_data.value

        elif progress_data.progress_type == imf.ProgressType.absolute:
            self.progress_current = progress_data.value

        elif progress_data.progress_type == imf.ProgressType.analyticsOCR:
            logger.info(f"Showing ocr analytics... {progress_data.value}")
            # Append the formatted analytics to the text edit.
            ocr_analytics, ocr_max_size = progress_data.value
            analytics_str = an.show_ocr_analytics(ocr_analytics, ocr_max_size, ANALYTICS_COLUMNS)
            self.textEdit_analytics.append(gu.ansi_to_html(analytics_str))
            self.file_table.show_ocr_mini_analytics(ocr_analytics)

        elif progress_data.progress_type == imf.ProgressType.analyticsMasker:
            # Show analytics.
            logger.info(f"Showing masker analytics... {progress_data.value}")
            masker_analytics_raw = progress_data.value
            analytics_str = an.show_masker_analytics(masker_analytics_raw, ANALYTICS_COLUMNS)
            self.textEdit_analytics.append(gu.ansi_to_html(analytics_str))
            self.file_table.show_masker_mini_analytics(masker_analytics_raw)

        elif progress_data.progress_type == imf.ProgressType.analyticsDenoiser:
            # Show analytics.
            logger.info(f"Showing analytics... {progress_data.value}")
            denoise_analytics_raw, min_deviation, max_deviation = progress_data.value
            analytics_str = an.show_denoise_analytics(
                denoise_analytics_raw,
                min_deviation,
                max_deviation,
                ANALYTICS_COLUMNS,
            )
            self.textEdit_analytics.append(gu.ansi_to_html(analytics_str))
            self.file_table.show_denoise_mini_analytics(denoise_analytics_raw, min_deviation)

        elif progress_data.progress_type == imf.ProgressType.end:
            # This marks the end of a processing step.
            self.output_worker_finished()
            return
        else:
            # Sanity check.
            raise ValueError(f"Invalid progress type: {progress_data.progress_type}")

        # Update the progress bars.
        self.progressBar_individual.setValue(self.progress_current)
        self.progressBar_individual.setMaximum(progress_data.total_images)
        self.progressBar_total.setValue(progress_data.current_step.value)
        self.progressBar_total.setMaximum(
            imf.output_to_step[max(progress_data.target_outputs)].value
        )
        # Update the label.
        self.label_progress_total.setText(
            f"Current step: {pp.to_display_name(progress_data.current_step.name)}"
        )

    #
    # def show_glossary_help(self):
    #     """
    #     Show the glossary documentation in a web browser.
    #     Open the github page for this.
    #     """
    #     show_info(
    #         self,
    #         "Glossary info",
    #         # language=HTML
    #         """<html>
    #                 <head/>
    #                 <body>
    #                     <p> DeepQt uses glossary files to pre-process files before sending them to the API;
    #                         this is not the same as DeepL's glossary functions. Therefore, they can be used
    #                         with any language and offer special features, which DeepL's glossaries cannot
    #                         offer.
    #                     </p>
    #                     <p>
    #                        The format of these glossaries is outlined in the
    #                         <a href="https://github.com/VoxelCubes/DeepQt/blob/master/docs/glossary_help.md">
    #                             online documentation
    #                         </a>
    #                         .
    #                     </p>
    #                 </body>
    #             </html>""",
    #     )
