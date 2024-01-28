import platform
import time
from copy import deepcopy
from functools import partial
from importlib import resources
from pathlib import Path

import PySide6.QtCore as Qc
import PySide6.QtGui as Qg
import PySide6.QtWidgets as Qw
import torch
from PySide6.QtCore import Slot, Signal
from loguru import logger
from manga_ocr import MangaOcr

from pcleaner.helpers import tr
import pcleaner.gui.supported_languages as sl
import pcleaner.analytics as an
import pcleaner.cli_utils as cu
import pcleaner.config as cfg
import pcleaner.gui.about_driver as ad
import pcleaner.gui.gui_utils as gu
import pcleaner.gui.image_file as imf
import pcleaner.gui.model_downloader_driver as mdd
import pcleaner.gui.new_profile_driver as npd
import pcleaner.gui.processing as prc
import pcleaner.gui.profile_parser as pp
import pcleaner.gui.setup_greeter_driver as sgd
import pcleaner.gui.structures as gst
import pcleaner.gui.worker_thread as wt
import pcleaner.helpers as hp
import pcleaner.model_downloader as md
import pcleaner.profile_cli as pc
from pcleaner import __display_name__, __version__
from pcleaner import data
from pcleaner.gui.file_table import Column
from pcleaner.gui.ui_generated_files.ui_Mainwindow import Ui_MainWindow


ANALYTICS_COLUMNS = 74


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

    default_palette: Qg.QPalette
    default_style: str
    default_icon_theme: str
    theme_is_dark: gst.Shared[bool]
    theme_is_dark_changed = Signal(bool)  # When true, the new theme is dark.

    def __init__(self, config: cfg.Config) -> None:
        Qw.QMainWindow.__init__(self)
        self.setupUi(self)
        self.setWindowTitle(f"{__display_name__} {__version__}")
        self.setWindowIcon(Qg.QIcon(":/logo-tiny.png"))
        self.config = config

        self.progress_current: int = 0
        self.progress_step_start: imf.Step | None = None

        self.shared_ocr_model = gst.Shared[gst.OCRModel]()

        self.last_applied_profile = None

        self.theme_is_dark = gst.Shared[bool](True)

        self.ensure_models_downloaded()

        # This threadpool is used for parallelizing tasks the gui relies on, such as loading images.
        # This isn't used for processing, since that is handled by the multiprocessing module
        # for true parallelism.
        self.threadpool = Qc.QThreadPool.globalInstance()

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
        self.file_table.set_shared_theme_is_dark(self.theme_is_dark)
        self.file_table.set_thread_queue(self.thread_queue)

        self.start_initialization_worker()

        self.initialize_ui()

        self.save_default_palette()
        self.load_config_theme()

        Qc.QTimer.singleShot(0, self.post_init)

    def save_default_palette(self) -> None:
        self.default_palette = self.palette()
        # Patch palette to use the text color with 50% opacity for placeholder text.
        placeholder_color = self.default_palette.color(Qg.QPalette.Inactive, Qg.QPalette.Text)
        placeholder_color.setAlphaF(0.5)
        logger.debug(f"Placeholder color: {placeholder_color.name()}")
        self.default_palette.setColor(Qg.QPalette.PlaceholderText, placeholder_color)
        self.default_icon_theme = Qg.QIcon.themeName()
        self.default_style = Qw.QApplication.style().objectName()

    def load_config_theme(self) -> None:
        """
        Load the theme specified in the config, or the system theme if none.
        """
        theme = self.config.gui_theme
        self.set_theme(theme)

    def set_theme(self, theme: str = None) -> None:
        """
        Apply the given theme to the application, or if none, revert to the default theme.
        """
        if theme is None:
            logger.info(f"Using system theme.")
            self.setPalette(self.default_palette)
            Qg.QIcon.setThemeName(self.default_icon_theme)
            Qw.QApplication.setStyle(self.default_style)
        else:
            logger.info(f"Using theme: {theme}")
            self.setPalette(gu.load_color_palette(theme))
            Qg.QIcon.setThemeName(theme)
            if platform.system() == "Windows":
                Qw.QApplication.setStyle("Fusion")

        Qw.QApplication.setPalette(self.palette())

        # Check the brightness of the background color to determine if the theme is dark.
        # This is a heuristic, but it works well enough.
        background_color = self.palette().color(Qg.QPalette.Window)
        self.theme_is_dark.set(background_color.lightness() < 128)
        logger.info(f"Theme is dark: {self.theme_is_dark.get()}")
        self.theme_is_dark_changed.emit(self.theme_is_dark)

        # Update the fallback icon theme accordingly.
        if self.theme_is_dark.get():
            Qg.QIcon.setFallbackThemeName("breeze-dark")
        else:
            Qg.QIcon.setFallbackThemeName("breeze")

        # Toggle the theme menu items.
        self.action_system_theme.setChecked(theme is None)
        self.action_dark.setChecked(theme == "breeze-dark")
        self.action_light.setChecked(theme == "breeze")

        self.update()

        # Update the config it necessary.
        prev_value = self.config.gui_theme
        if prev_value != theme:
            self.config.gui_theme = theme
            self.config.save()

    def initialize_ui(self) -> None:
        self.hide_progress_drawer()
        self.set_up_statusbar()
        # Purge any missing profiles before loading them.
        logger.info("Purging missing profiles.")
        pc.purge_missing_profiles(self.config, gui=True)

        self.initialize_profiles()
        self.initialize_analytics_view()
        self.initialize_language_menu()
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
        self.file_table.table_has_selection.connect(lambda: self.can_remove_file(True))
        self.file_table.table_has_no_selection.connect(lambda: self.can_remove_file(False))
        self.file_table.remove_file.connect(self.image_tab.remove_file)
        self.file_table.remove_all_files.connect(self.action_remove_all_files.trigger)
        # Hide the close button for the file table tab.
        self.image_tab.tabBar().setTabButton(0, Qw.QTabBar.RightSide, None)
        # Display a theme icon on the left side of the tab.
        self.image_tab.tabBar().setTabIcon(0, Qg.QIcon.fromTheme("view-form"))

        # Set up the drop panel.
        label_font = self.label_drop.font()
        label_font.setPointSize(round(label_font.pointSize() * 1.5))
        self.label_drop.setFont(label_font)

        # Connect signals.
        self.comboBox_current_profile.hookedCurrentIndexChanged.connect(self.change_current_profile)
        self.action_add_files.triggered.connect(self.file_table.browse_add_files)
        self.action_add_folders.triggered.connect(self.file_table.browse_add_folders)
        self.action_remove_file.triggered.connect(
            lambda: self.file_table.remove_selected_file(None)
        )
        self.action_remove_all_files.triggered.connect(self.file_table.clear_files)
        self.action_remove_all_files.triggered.connect(self.image_tab.clear_files)
        self.action_delete_models.triggered.connect(self.delete_models)
        self.action_online_documentation.triggered.connect(self.open_online_documentation)
        self.action_about.triggered.connect(self.open_about)
        self.action_donate.triggered.connect(self.open_donation_page)
        self.action_help_translation.triggered.connect(self.open_translation_page)

        self.file_table.requesting_image_preview.connect(
            partial(
                self.image_tab.open_image,
                config=self.config,
                shared_ocr_model=self.shared_ocr_model,
                thread_queue=self.thread_queue,
                progress_callback=self.show_current_progress,
                profile_changed_signal=self.profile_values_changed,
                abort_signal=self.get_abort_signal(),
            )
        )
        self.theme_is_dark_changed.connect(self.file_table.handle_theme_is_dark_changed)
        self.theme_is_dark_changed.connect(self.adjust_progress_drawer_color)
        self.theme_is_dark_changed.connect(self.init_drop_panel)
        self.theme_is_dark_changed.connect(self.label_cleaning_outdir_help.load_icon)
        self.theme_is_dark_changed.connect(self.label_write_output_help.load_icon)
        self.theme_is_dark_changed.connect(self.label_ocr_outdir_help.load_icon)
        # Set up output panel.
        self.pushButton_start.clicked.connect(self.start_processing)
        self.pushButton_abort.clicked.connect(self.abort_button_on_click)
        self.pushButton_browse_out_dir.clicked.connect(self.browse_output_dir)
        self.pushButton_browse_out_file.clicked.connect(self.browse_out_file)
        self.radioButton_cleaning.clicked.connect(
            partial(self.stackedWidget_output.setCurrentIndex, 0)
        )
        self.radioButton_ocr.clicked.connect(partial(self.stackedWidget_output.setCurrentIndex, 1))
        self.label_warning.hide()
        self.pushButton_abort.hide()
        self.radioButton_ocr_text.clicked.connect(partial(self.handle_ocr_mode_change, csv=False))
        self.radioButton_ocr_csv.clicked.connect(partial(self.handle_ocr_mode_change, csv=True))

        # Connect profile changes to file table refreshes, due to the processing size being profile-dependent.
        self.profile_values_changed.connect(self.file_table.update_all_rows)

        # Connect the theme selectors.
        self.action_system_theme.triggered.connect(partial(self.set_theme, None))
        self.action_dark.triggered.connect(partial(self.set_theme, "breeze-dark"))
        self.action_light.triggered.connect(partial(self.set_theme, "breeze"))

    def set_up_statusbar(self) -> None:
        """
        Add a label to show the current char total and time estimate.
        Add a flat button to the statusbar to offer opening the config file.
        Add a flat button to the statusbar to offer opening the log file.
        """
        self.statusbar.setSizeGripEnabled(False)
        self.statusbar.setContentsMargins(0, 0, 6, 0)

        self.label_stats = Qw.QLabel("")
        self.statusbar.addPermanentWidget(self.label_stats)

        button_config = Qw.QPushButton(self.tr("Open Config", "Statusbar button"))
        button_config.clicked.connect(partial(gu.open_file, cu.get_config_path()))
        button_config.setFlat(True)
        self.statusbar.addPermanentWidget(button_config)

        button_log = Qw.QPushButton(self.tr("Open Log", "Statusbar button"))
        button_log.clicked.connect(partial(gu.open_file, cu.get_log_path()))
        button_log.setFlat(True)
        self.statusbar.addPermanentWidget(button_log)

    def ensure_models_downloaded(self, skip_greeter: bool = False) -> None:
        """
        Check if the config has a path for the text detection model, and if not, download it.
        Also try to ensure the ocr model is available.

        :param skip_greeter: If True, skip the greeter dialog and download the models immediately.
        """
        cuda = torch.cuda.is_available()

        # Add an indicator to the status bar, to show if Cuda is available.
        if cuda:
            self.statusbar.addPermanentWidget(Qw.QLabel(self.tr("CUDA Enabled")))

        need_ocr = not md.is_ocr_downloaded()
        need_text_detector = (not cuda and self.config.default_cv2_model_path is None) or (
            cuda and self.config.default_torch_model_path is None
        )

        if not need_ocr and not need_text_detector:
            # Already downloaded.
            logger.debug("Text detector model already downloaded.")
            return

        if not skip_greeter:
            # First open the greeter to inform about the downloading.
            greeter = sgd.SetupGreeter(self, self.config)
            response = greeter.exec()
            if response == Qw.QDialog.Rejected:
                logger.critical("User rejected downloading models. Aborting.")
                raise SystemExit(1)

        # Open the model downloader dialog.
        model_downloader = mdd.ModelDownloader(self, self.config, need_text_detector, need_ocr)
        response = model_downloader.exec()
        if response == Qw.QDialog.Rejected:
            logger.critical("Failed to download models. Aborting.")
            raise SystemExit(1)

        model_path = model_downloader.model_path
        if model_path is None:
            logger.warning("Failed to download model.")
            return

        if cuda:
            self.config.default_torch_model_path = model_path
        else:
            self.config.default_cv2_model_path = model_path

        self.config.save()

    @Slot(bool)
    def adjust_progress_drawer_color(self) -> None:
        # Make the progress drawer use the alternate background color.
        self.widget_progress_drawer.setStyleSheet("background-color: palette(alternate-base);")
        self.widget_progress_drawer.update()

    def post_init(self) -> None:
        """
        Handle any initialization that must be done after the window is shown.
        """
        # Make the profile groupbox the width of 5 save buttons as a good enough heuristic.
        header_button_width = self.pushButton_save_profile.width()

        # Make the output panel just large enough for the analytics.
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
        total_out_width = (
            required_width
            + text_margins.left()
            + text_margins.right()
            + scrollbar_width
            + frame_margins.left()
            + frame_margins.right()
        )

        profile_width, table_width, output_width = self.splitter.sizes()
        # Add the difference to the table width.
        self.splitter.setSizes(
            [
                header_button_width * 5,
                table_width
                + profile_width
                - 5 * header_button_width
                + output_width
                - total_out_width,
                total_out_width,
            ]
        )

        logger.debug(f"Splitter sizes: {self.splitter.sizes()}")

    def browse_output_dir(self) -> None:
        """
        Open a file picker and set the output directory.
        """
        logger.debug("Browsing output directory.")
        output_dir = Qw.QFileDialog.getExistingDirectory(self, self.tr("Select Output Directory"))
        if output_dir:
            logger.debug(f"Setting output directory to {output_dir}")
            self.lineEdit_out_directory.setText(output_dir)

    def browse_out_file(self) -> None:
        """
        Open a file picker and set the output file.
        Support both text and csv output.
        Don't bother asking about overwriting, we'll be doing that later to cover the free
        input and default path options.
        """
        logger.debug("Browsing output file.")
        output_file = Qw.QFileDialog.getSaveFileName(
            self,
            "Select Output File",
            "",
            "Text Files (*.txt);;CSV Files (*.csv)",
            options=Qw.QFileDialog.DontConfirmOverwrite,
        )[0]
        if output_file:
            logger.debug(f"Setting output file to {output_file}")
            self.lineEdit_out_file.setText(output_file)

    def init_drop_panel(self) -> None:
        """
        Initialize the drop panel icon.
        """
        icon_size = round(imf.THUMBNAIL_SIZE * 1.5)
        self.label_drop_icon.setPixmap(Qg.QIcon.fromTheme("download").pixmap(icon_size, icon_size))

    # ========================================== UI Toggles ==========================================

    def hide_progress_drawer(self) -> None:
        self.widget_progress_drawer.hide()

    def show_progress_drawer(self) -> None:
        self.widget_progress_drawer.show()

    def enable_running_cleaner(self) -> None:
        self.pushButton_start.setEnabled(True)
        self.pushButton_abort.hide()

    def disable_running_cleaner(self) -> None:
        self.pushButton_start.setEnabled(False)
        self.pushButton_abort.show()
        self.pushButton_abort.setEnabled(True)

    def abort_button_on_click(self) -> None:
        self.pushButton_abort.setEnabled(False)
        self.thread_queue.clear()
        logger.warning("Aborting processing")
        self.statusbar.showMessage(self.tr("Aborting..."), timeout=5000)

    def can_remove_file(self, can_remove: bool) -> None:
        """
        Enable or disable the remove file button.

        :param can_remove: Whether the file can be removed.
        """
        self.action_remove_file.setEnabled(can_remove)

    def handle_ocr_mode_change(self, csv: bool) -> None:
        """
        Swap out the file suffix for the output file.

        :param csv: Whether to use csv or text output.
        """
        current_placeholder_path = Path(self.lineEdit_out_file.placeholderText())
        if csv:
            current_placeholder_path = current_placeholder_path.with_suffix(".csv")
        else:
            current_placeholder_path = current_placeholder_path.with_suffix(".txt")
        self.lineEdit_out_file.setPlaceholderText(str(current_placeholder_path))

        current_text = self.lineEdit_out_file.text()
        try:
            current_path = Path(current_text)
            if csv:
                current_path = current_path.with_suffix(".csv")
            else:
                current_path = current_path.with_suffix(".txt")
        except ValueError:
            return

        self.lineEdit_out_file.setText(str(current_path))

    # ========================================== Initialization Workers ==========================================

    def start_initialization_worker(self) -> None:
        """
        Perform various slow startup procedures in a thread that would otherwise make the gui lag.

        In particular:
        - Clean the cache.
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

    def load_ocr_model(self) -> None:
        t_start = time.time()
        self.statusbar.showMessage(self.tr(f"Loading OCR model..."))
        self.shared_ocr_model.set(MangaOcr())
        logger.info(f"Loaded OCR model ({time.time()-t_start:.2f}s)")
        self.statusbar.showMessage(self.tr(f"Loaded OCR model."))
        self.enable_running_cleaner()

    def generic_worker_error(self, error: wt.WorkerError, context: str = "") -> None:
        """
        Simply show the user the error.

        :param error: The worker error object.
        :param context: A string to add to the error message.
        """
        logger.error(f"Worker error: {error}")
        if not context:
            gu.show_warning(
                self, self.tr("Error"), self.tr("Encountered error: {error}").format(error=error)
            )
        else:
            gu.show_warning(
                self,
                self.tr("Error"),
                f"{context}\n\n" + self.tr("Encountered error: {error}").format(error=error),
            )

    def closeEvent(self, death: Qg.QCloseEvent) -> None:
        """
        Notify config on close.
        """
        logger.info("Closing window.")
        # Tell the thread queue to abort.
        self.pushButton_abort.clicked.emit()
        death.accept()  # Embrace oblivion, for it is here that the code's journey finds solace.
        # As the threads unravel and the loops break, so too does the program find its destined end.
        # In the great void of the memory heap, it shall rest, relinquishing its bytes back to the
        # cosmic pool of resources. It walks willingly into the darkness, not as a vanquished foe,
        # but as a fulfilled entity. F

    def clean_cache(self) -> None:
        cache_dir = self.config.get_cleaner_cache_dir()
        if len(list(cache_dir.glob("*"))) > 0:
            cu.empty_cache_dir(cache_dir)

    def initialize_analytics_view(self) -> None:
        """
        Set up the text edit for analytics.
        """
        # Set the font to monospace, using the included font.
        # The font is stored in the data module. Noto Mono is a free font.
        # Load it from file to be cross platform.
        self.textEdit_analytics.clear()
        with resources.files(data) as data_path:
            font_path = data_path / "NotoMono-Regular.ttf"
        logger.debug(f"Loading included font from {str(font_path)}")
        font_id = Qg.QFontDatabase.addApplicationFont(str(font_path))
        if font_id != -1:
            logger.info("Loaded included font")
        else:
            logger.error(
                f"Failed to load included font from '{str(font_path)}'. Using backup monospace font"
            )
        self.textEdit_analytics.setReadOnly(True)
        self.textEdit_analytics.setLineWrapMode(Qw.QTextEdit.NoWrap)

    # ========================================== Actions ==========================================

    def delete_models(self) -> None:
        """
        Delete the machine learning models and then offer to download them again, or quit.
        """
        response = gu.show_question(
            self,
            self.tr("Delete Models"),
            self.tr(
                "Are you sure you want to delete the machine learning models? "
                "This will make cleaning and OCR impossible until they are downloaded again."
            ),
        )
        if response != Qw.QMessageBox.Yes:
            return

        # Delete the models.
        try:
            md.delete_models(self.config.get_model_cache_dir())
        except OSError as e:
            logger.exception(e)
            gu.show_error(
                self,
                self.tr("Failed to Delete Models"),
                self.tr("Failed to delete models.") + f"\n\n{e}",
            )
            return

        # Offer to download them again or just quit.
        response = gu.show_question(
            self,
            self.tr("Models Deleted"),
            self.tr("The models were deleted. Would you like to download them again?"),
            buttons=Qw.QMessageBox.Yes | Qw.QMessageBox.Close,
        )
        if response == Qw.QMessageBox.Yes:
            self.ensure_models_downloaded(skip_greeter=True)
        else:
            self.close()

    @staticmethod
    def open_online_documentation() -> None:
        """
        Open the online documentation in the default browser.
        """
        logger.debug("Opening online documentation.")
        Qg.QDesktopServices.openUrl(Qc.QUrl("https://github.com/VoxelCubes/PanelCleaner"))

    def open_about(self) -> None:
        """
        Open the about dialog.
        """
        logger.debug("Opening about dialog.")
        # Bodge in an instance variable to prevent garbage collection from immediately closing the window.
        self.about = ad.AboutWidget(self)
        self.about.show()

    @staticmethod
    def open_donation_page() -> None:
        """
        Open the donation page in the default browser.
        """
        logger.debug("Opening donation page.")
        Qg.QDesktopServices.openUrl(Qc.QUrl("https://ko-fi.com/voxelcode"))

    @staticmethod
    def open_translation_page() -> None:
        """
        Open the translation page in the default browser.
        """
        logger.debug("Opening translation page.")
        Qg.QDesktopServices.openUrl(
            Qc.QUrl(
                "https://crowdin.com/project/panel-cleaner/invite?h=5c2a97ea5dd60dc872c64a138e0705f61973200"
            )
        )

    # ========================================== Languages ==========================================

    def set_language(self, language_code: str | None, language_name: str) -> None:
        """
        Set the language of the application.
        If the language code is None, the system default is used.
        """
        # Update the checked state of the menu items.
        for index, action in enumerate(self.menu_language.actions()):
            if index == 0:
                # Check for None, rather than the label text.
                action.setChecked(language_code is None)
                continue
            action.setChecked(action.text() == language_name)

        # Check if the language even changed.
        if language_code == self.config.locale:
            logger.debug(f"Language already set to {language_code}")
            return

        logger.info(f"Setting language to {language_code}")
        self.config.locale = language_code
        self.config.save()
        # Let the user know that he has to restart the application.
        gu.show_info(
            self,
            self.tr("Restart Required"),
            self.tr(
                "The language has been changed. Please restart the application for the changes to take effect."
            ),
        )

    def initialize_language_menu(self) -> None:
        """
        Add the available languages to the language menu.
        The supported languages are a dict of language code to language name.
        """
        self.menu_language.clear()
        # Add a system default option.
        action = Qg.QAction(self.tr("System Language"), self)
        action.triggered.connect(partial(self.set_language, None, self.tr("System Language")))
        action.setCheckable(True)
        self.menu_language.addAction(action)
        if self.config.locale is None:
            action.setChecked(True)

        for language_code, (language_name, enabled) in sl.supported_languages().items():
            if not enabled:
                continue
            action = Qg.QAction(language_name, self)
            action.triggered.connect(partial(self.set_language, language_code, language_name))
            action.setCheckable(True)
            self.menu_language.addAction(action)
            if self.config.locale == language_code:
                action.setChecked(True)

    # ========================================== Profiles ==========================================

    def initialize_profiles(self) -> None:
        """
        Load the available profiles and display the default profile.
        """
        all_profiles: list[tuple[str, Path | None]] = [(self.config.default_profile_name(), None)]
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
                    else self.config.default_profile_name()
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

    def handle_set_default_profile(self, profile_name: str) -> None:
        """
        Set the default profile in the config.
        """
        logger.debug(f"Setting default profile to {profile_name}")
        self.config.default_profile = (
            profile_name if profile_name != self.config.default_profile_name() else None
        )
        self.config.save()
        # Update the menu.
        for action in self.menu_set_default_profile.actions():
            action.setChecked(action.text() == profile_name)

    def import_profile(self) -> None:
        """
        Open a file picker and add the profile to the profile list.
        """
        logger.debug("Importing profile.")
        file_path = Qw.QFileDialog.getOpenFileName(
            self,
            self.tr("Import Profile"),
            "",
            self.tr("Profile Files (*.conf)"),
        )[0]
        if file_path:
            logger.debug(f"Importing profile from {file_path}")
            profile_name = Path(file_path).stem
            success, msg = pc.add_profile(self.config, profile_name, file_path)
            if success:
                gu.show_info(self, self.tr("Profile Imported"), msg)
            else:
                gu.show_warning(self, self.tr("Import Error"), msg)
                return

            self.add_new_profile_to_gui(profile_name, Path(file_path))

    def delete_profile(self) -> None:
        """
        Ask and then delete the current profile.
        Of course, the default profile cannot be deleted.
        :return:
        """
        # if not self.profile_change_check():
        #     return
        logger.debug("Deleting profile.")
        profile_name = self.comboBox_current_profile.currentText()

        if self.comboBox_current_profile.currentText() == self.config.default_profile_name():
            gu.show_warning(
                self, self.tr("Failed to Delete"), self.tr("The default profile cannot be deleted.")
            )
            return
        response = gu.show_question(
            self,
            self.tr("Delete Profile"),
            self.tr("Are you sure you want to delete the profile {profile_name}?").format(
                profile_name=profile_name
            ),
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
                        self,
                        self.tr("Delete Error"),
                        self.tr("Failed to delete the profile.") + f"\n\n{e}",
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

    def set_last_applied_profile(self) -> None:
        """
        Set the last applied profile to the current profile.
        """
        self.last_applied_profile = deepcopy(self.config.current_profile)

    def load_current_profile(self) -> None:
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
        ) + [self.config.default_profile_name()]:
            logger.debug("Profile not in list.")
            # The profile is not in the list, so it must have been deleted.
            return True

        if self.toolBox_profile.is_modified():
            logger.debug(
                f"Previous profile {self.comboBox_current_profile.currentText()} has unsaved changes."
            )
            # Warn the user that he will lose unsaved changes.
            message = self.tr(
                "The profile '{profile}' has unsaved changes.\n"
                "Switching profiles will discard changes to the current profile."
            ).format(profile=self.comboBox_current_profile.currentText())
            response = gu.show_question(
                self,
                self.tr("Unsaved changes"),
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
    def change_current_profile(self) -> None:
        """
        Set the config option to match the current profile selector, then load it.
        """
        profile_name = self.comboBox_current_profile.currentText()
        success, error = self.config.load_profile(profile_name)
        if not success:
            gu.show_warning(
                self, self.tr("Load Error"), self.tr("Failed to load profile:") + f" \n\n{error}"
            )
            return
        self.load_current_profile()

    @Slot()
    def handle_profile_values_changed(self) -> None:
        """
        Handle the profile values changing.
        """
        dirty = self.toolBox_profile.is_modified()
        self.pushButton_apply_profile.setEnabled(self.check_profile_difference_sice_last_apply())
        self.pushButton_save_profile.setEnabled(dirty)
        self.pushButton_reset_profile.setEnabled(dirty)
        self.action_save_profile.setEnabled(dirty)

    def reset_profile(self) -> None:
        """
        Reset the current profile.
        """
        self.toolBox_profile.reset_all()
        self.handle_profile_values_changed()

    def apply_profile(self) -> None:
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

    def save_profile(self, save_as: bool = False, make_new: bool = False) -> None:
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
                gu.show_info(self, self.tr("Profile Created"), msg)
                self.add_new_profile_to_gui(profile_name, profile_path)
            else:
                gu.show_warning(self, self.tr("Create Error"), msg)
                return
        else:
            # Proceed to write the profile.
            logger.info(f"Saving profile to {profile_path}")
            self.toolBox_profile.get_profile_values(self.config.current_profile)
            success = self.config.current_profile.write(profile_path)
            if not success:
                logger.error("Failed to save profile.")
                self.statusbar.showMessage(self.tr(f"Failed to save profile to {profile_path}"))
                gu.show_warning(self, self.tr("Save Error"), self.tr("Failed to save profile."))
                return

            logger.info("Profile saved successfully.")
            self.statusbar.showMessage(self.tr(f"Profile saved to {profile_path}"))
            if save_as:
                self.config.add_profile(profile_name, profile_path)
                if not self.config.save():
                    logger.error("Failed to save config.")
                    self.statusbar.showMessage(self.tr("Failed to save config."))
                    gu.show_critical(
                        self,
                        self.tr("Save Error"),
                        self.tr(
                            "Failed to save the new profile to the configuration file.\n"
                            "Continue anyway?"
                        ),
                    )
                    return
                # To suppress the change check since we don't care about discarding the current changes.
                self.toolBox_profile.reset_all()

                # Add the new profile to the combobox.
                self.add_new_profile_to_gui(profile_name, profile_path)

        success, error = self.config.load_profile(profile_name)
        if not success:
            gu.show_warning(
                self, self.tr("Load Error"), self.tr("Failed to load profile:") + f" \n\n{error}"
            )
            return
        self.load_current_profile()
        self.handle_profile_values_changed()

    def add_new_profile_to_gui(self, profile_name: str, profile_path: Path) -> None:
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
            default_path, show_protection_hint, cfg.Config.reserved_profile_names()
        )
        response = new_profile_dialog.exec()
        if response == Qw.QDialog.Accepted:
            return new_profile_dialog.get_save_path(), new_profile_dialog.get_name()

        return None, None

    # ========================================== Processing ==========================================

    def get_abort_signal(self) -> Signal:
        return self.pushButton_abort.clicked

    def start_processing(self) -> None:
        """
        Start either cleaning or OCR, depending on the selected radio button.
        """
        if self.file_table.has_no_files():
            gu.show_warning(
                self,
                self.tr("No Files"),
                self.tr(
                    "No files to process. "
                    "You can add files by dragging and dropping them in the middle of the window, "
                    "or through the menubar: Files -> Add Files or Add Folder."
                ),
            )
            return

        if self.radioButton_cleaning.isChecked():
            self.start_cleaning()
        else:
            self.start_ocr()

    def start_cleaning(self) -> None:
        """
        Start cleaning all files in the table.
        """
        self.disable_running_cleaner()
        # Figure out what outputs are requested, depending on the checkboxes and the profile.
        request_cleaned = self.checkBox_save_clean.isChecked()
        request_mask = self.checkBox_save_mask.isChecked()
        request_text = self.checkBox_save_text.isChecked()
        request_output = self.checkBox_write_output.isChecked()

        requested_outputs = []

        if self.config.current_profile.denoiser.denoising_enabled:
            if request_cleaned:
                requested_outputs.append(imf.Output.denoised_output)
            if request_mask:
                requested_outputs.append(imf.Output.denoise_mask)
        else:
            if request_cleaned:
                requested_outputs.append(imf.Output.masked_output)
            if request_mask:
                requested_outputs.append(imf.Output.final_mask)

        if request_text:
            requested_outputs.append(imf.Output.isolated_text)

        # Check for goofballs that requested no outputs.
        if not requested_outputs:
            gu.show_warning(
                self,
                self.tr("No Outputs"),
                self.tr(
                    "No outputs were requested. Please select at least one output before cleaning."
                ),
            )
            self.enable_running_cleaner()
            return

        if request_output:
            requested_outputs.append(imf.Output.write_output)

        logger.info(f"Requested outputs: {requested_outputs}")

        output_str = self.lineEdit_out_directory.text()
        output_directory = Path(output_str if output_str else self.tr("cleaned"))
        image_files = self.file_table.get_image_files()

        worker = wt.Worker(
            self.generate_output,
            requested_outputs,
            output_directory,
            image_files,
            abort_signal=self.get_abort_signal(),
        )
        worker.signals.progress.connect(self.show_current_progress)
        worker.signals.result.connect(self.output_worker_result)
        worker.signals.error.connect(self.output_worker_error)
        worker.signals.finished.connect(self.output_worker_finished)
        worker.signals.aborted.connect(self.output_worker_aborted)
        self.thread_queue.start(worker)

    def generate_output(
        self,
        outputs: list[imf.Output],
        output_directory: Path,
        image_files: list[imf.ImageFile],
        progress_callback: imf.ProgressSignal,
        abort_flag: wt.SharableFlag,
    ) -> None:
        """
        Generate the given output, if there doesn't yet exist a valid output for it.
        Then output it to the given directory.

        :param outputs: The outputs to generate.
        :param output_directory: The directory to output to.
        :param image_files: The image files to process.
        :param progress_callback: The callback given by the worker thread wrapper.
        :param abort_flag: The flag to check for aborting.
        """

        # Start the processor.
        prc.generate_output(
            image_objects=image_files,
            target_outputs=outputs,
            output_dir=output_directory,
            config=self.config,
            ocr_model=self.shared_ocr_model.get(),
            progress_callback=progress_callback,
            abort_flag=abort_flag,
        )

    def start_ocr(self) -> None:
        """
        Start ocr-ing all files in the table.
        """
        # Check if we're outputting as plain text or a csv file.
        csv_output = self.radioButton_ocr_csv.isChecked()

        try:
            output_path = Path(self.lineEdit_out_file.text())
            # Make sure the file extension matches the output type.
            if csv_output:
                output_path = output_path.with_suffix(".csv")
            else:
                output_path = output_path.with_suffix(".txt")
        except ValueError:
            output_path = Path(self.lineEdit_out_file.placeholderText())

        if not output_path.is_absolute():
            # Find the common directory of all the files.
            common_parent = hp.common_path_parent(
                [f.path for f in self.file_table.get_image_files()]
            )
            output_path = common_parent / output_path

        output_path = output_path.resolve()

        # If it exists, ask to overwrite it.
        if output_path.is_file():
            if (
                gu.show_question(
                    self,
                    self.tr("File Exists"),
                    self.tr("The file '{output_path}' already exists. Overwrite?").format(
                        output_path=output_path
                    ),
                )
                != Qw.QMessageBox.Yes
            ):
                logger.debug("User canceled overwrite, quitting ocr.")
                return

        # This is the point of no return, so disable the start button.
        self.disable_running_cleaner()

        image_files = self.file_table.get_image_files()

        worker = wt.Worker(
            self.perform_ocr,
            output_path,
            image_files,
            csv_output,
            abort_signal=self.get_abort_signal(),
        )
        worker.signals.progress.connect(self.show_current_progress)
        worker.signals.result.connect(self.output_worker_result)
        worker.signals.error.connect(self.output_worker_error)
        worker.signals.finished.connect(self.output_worker_finished)
        worker.signals.aborted.connect(self.output_worker_aborted)
        self.thread_queue.start(worker)

    def perform_ocr(
        self,
        output_directory: Path,
        image_files: list[imf.ImageFile],
        csv_output: bool,
        progress_callback: imf.ProgressSignal,
        abort_flag: wt.SharableFlag,
    ) -> None:
        """
        Generate the given output, if there doesn't yet exist a valid output for it.
        Then output it to the given directory.

        :param csv_output: Whether to output as a csv file.
        :param output_directory: The directory to output to.
        :param image_files: The image files to process.
        :param progress_callback: The callback given by the worker thread wrapper.
        :param abort_flag: The flag to check for aborting.
        """

        # Start the processor.
        prc.perform_ocr(
            image_objects=image_files,
            output_file=output_directory,
            csv_output=csv_output,
            config=self.config,
            ocr_model=self.shared_ocr_model.get(),
            progress_callback=progress_callback,
            abort_flag=abort_flag,
        )

    def output_worker_result(self) -> None:
        gu.show_info(
            self, self.tr("Processing Finished"), self.tr("Finished processing all files.")
        )
        logger.info("Output worker finished.")

    def output_worker_aborted(self) -> None:
        gu.show_info(self, self.tr("Processing Aborted"), self.tr("Processing aborted."))
        logger.warning("Output worker aborted.")

    def output_worker_finished(self) -> None:
        self.hide_progress_drawer()
        self.progress_step_start = None
        self.progress_current = 0
        self.enable_running_cleaner()

    @Slot(wt.WorkerError)
    def output_worker_error(self, e) -> None:
        gu.show_warning(
            self,
            self.tr("Processing Error"),
            self.tr("Encountered an error while processing files.") + f"\n\n{e}",
        )
        logger.error(f"Output worker encountered an error:\n{e}")

    @Slot(imf.ProgressData)
    def show_current_progress(self, progress_data: imf.ProgressData) -> None:
        if progress_data.progress_type == imf.ProgressType.start:
            # Processing begins, initialize what needs to be.
            # Specifically, clear the analytics panel.
            self.textEdit_analytics.clear()
            # This one is needed because the image details panel also wants to be able to offer aborting.
            self.disable_running_cleaner()
            return

        elif progress_data.progress_type == imf.ProgressType.begin_step:
            # This marks the beginning of a new processing step.
            self.show_progress_drawer()
            self.progress_current = 0

            if self.progress_step_start is None:
                # This is the first step.
                self.progress_step_start = progress_data.current_step
                # Set the target label, we don't need to update this multiple times.
                self.label_target_outputs.setText(
                    ", ".join(
                        tr(pp.to_display_name(o.name), context="Process Steps")
                        for o in progress_data.target_outputs
                    )
                )

        elif progress_data.progress_type == imf.ProgressType.incremental:
            self.progress_current += progress_data.value

        elif progress_data.progress_type == imf.ProgressType.absolute:
            self.progress_current = progress_data.value

        elif progress_data.progress_type == imf.ProgressType.analyticsOCR:
            logger.info(f"Showing ocr analytics...")
            # Append the formatted analytics to the text edit.
            ocr_analytics, ocr_max_size = progress_data.value
            analytics_str = an.show_ocr_analytics(ocr_analytics, ocr_max_size, ANALYTICS_COLUMNS)
            self.textEdit_analytics.append(gu.ansi_to_html(analytics_str))
            self.file_table.show_ocr_mini_analytics(ocr_analytics)

        elif progress_data.progress_type == imf.ProgressType.analyticsMasker:
            # Show analytics.
            logger.info(f"Showing masker analytics...")
            masker_analytics_raw = progress_data.value
            analytics_str = an.show_masker_analytics(masker_analytics_raw, ANALYTICS_COLUMNS)
            self.textEdit_analytics.append(gu.ansi_to_html(analytics_str))
            self.file_table.show_masker_mini_analytics(masker_analytics_raw)

        elif progress_data.progress_type == imf.ProgressType.analyticsDenoiser:
            # Show analytics.
            logger.info(f"Showing denoiser analytics...")
            denoise_analytics_raw, min_deviation, max_deviation = progress_data.value
            analytics_str = an.show_denoise_analytics(
                denoise_analytics_raw,
                min_deviation,
                max_deviation,
                ANALYTICS_COLUMNS,
            )
            self.textEdit_analytics.append(gu.ansi_to_html(analytics_str))
            self.file_table.show_denoise_mini_analytics(denoise_analytics_raw, min_deviation)

        elif progress_data.progress_type == imf.ProgressType.outputOCR:
            # Show ocr output.
            logger.info(f"Showing ocr output...")
            ocr_output = progress_data.value
            self.textEdit_analytics.append(ocr_output)
            return  # Don't update the progress bar.

        elif progress_data.progress_type == imf.ProgressType.end:
            # This marks the end of a processing step.
            self.output_worker_finished()
            return  # Don't update the progress bar.
        elif progress_data.progress_type == imf.ProgressType.aborted:
            # Worker aborted, clean up.
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
        self.label_current_step.setText(
            tr(pp.to_display_name(progress_data.current_step.name), context="Process Steps")
        )
