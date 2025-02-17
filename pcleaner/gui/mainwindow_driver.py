import os
import platform
import subprocess
import sys
import time
import shutil
from copy import deepcopy
from functools import partial
from importlib import resources
from pathlib import Path

import PySide6.QtCore as Qc
import PySide6.QtGui as Qg
import PySide6.QtWidgets as Qw
import psutil
import torch
from PySide6.QtCore import Slot, Signal
from loguru import logger

import pcleaner.analytics as an
import pcleaner.cli_utils as cu
import pcleaner.config as cfg
import pcleaner.gui.about_driver as ad
import pcleaner.gui.file_manager_extension_driver as fmed
import pcleaner.gui.gui_utils as gu
import pcleaner.gui.image_file as imf
import pcleaner.gui.image_match_driver as imd
import pcleaner.gui.issue_reporter_driver as ird
import pcleaner.gui.memory_watcher as mw
import pcleaner.gui.model_downloader_driver as mdd
import pcleaner.gui.new_profile_driver as npd
import pcleaner.gui.ocr_language_overview_driver as olod
import pcleaner.gui.ocr_review_driver as ocrd
import pcleaner.gui.output_review_driver as red
import pcleaner.gui.processing as prc
import pcleaner.gui.profile_parser as pp
import pcleaner.gui.setup_greeter_driver as sgd
import pcleaner.gui.state_saver as ss
import pcleaner.gui.structures as gst
import pcleaner.gui.supported_languages as sl
import pcleaner.gui.post_action_config as pac
import pcleaner.gui.post_action_runner as par
import pcleaner.gui.worker_thread as wt
import pcleaner.helpers as hp
import pcleaner.model_downloader as md
import pcleaner.ocr.ocr as ocr
import pcleaner.ocr.parsers as op
import pcleaner.ocr.supported_languages as osl
import pcleaner.output_structures as ost
import pcleaner.profile_cli as pc
import pcleaner.structures as st
from pcleaner import __display_name__, __version__
from pcleaner import data
from pcleaner.gui.file_table import Column
from pcleaner.gui.ui_generated_files.ui_Mainwindow import Ui_MainWindow
from pcleaner.helpers import tr


ANALYTICS_COLUMNS = 74


# noinspection PyUnresolvedReferences
class MainWindow(Qw.QMainWindow, Ui_MainWindow):
    config: cfg.Config = None
    debug: bool
    startup_files: list[str]

    label_stats: Qw.QLabel

    toolBox_profile: pp.ProfileToolBox
    # Optional shared instance of the OCR model to save time due to its slow loading.
    shared_ocr_model: gst.Shared[ocr.OCREngineFactory]

    threadpool: Qc.QThreadPool  # Used for loading images and other gui tasks.
    thread_queue: (
        Qc.QThreadPool
    )  # Used for tasks that need to run sequentially, without blocking the gui.

    progress_current: int
    progress_step_start: ost.Step | None  # When None, no processing is running.
    current_post_action: str | None
    closed_post_action_banner: bool

    cleaning_review_options: None | gst.CleaningReviewOptions
    ocr_review_options: None | gst.OcrReviewOptions
    batch_metadata: None | gst.BatchMetadata

    profile_values_changed = Signal()

    # Save a copy of the last applied profile to prevent multiple profile change calls
    # by the user when the profile didn't actually change.
    last_applied_profile: cfg.Profile | None

    default_palette: Qg.QPalette
    default_style: str
    default_icon_theme: str
    theme_is_dark: gst.Shared[bool]
    theme_is_dark_changed = Signal(bool)  # When true, the new theme is dark.

    about: ad.AboutWidget | None  # The about dialog.
    file_manager_extension: fmed.FileManagerExtension | None  # The file manager extension dialog.
    output_review: red.OutputReviewWindow | None  # The output review dialog.

    terminate = Signal()  # Signal to kill any straggler widgets.
    dead: bool  # Whether the window is closing.

    state_saver: ss.StateSaver  # The state saver for the window.
    memory_watcher: mw.MemoryWatcher  # The memory watcher for the window.
    mem_watcher_thread: Qc.QThread  # The thread for the memory watcher.

    def __init__(self, config: cfg.Config, files_to_open: list[str], debug: bool) -> None:
        Qw.QMainWindow.__init__(self)
        self.setupUi(self)
        self.setWindowTitle(f"{__display_name__} {__version__}")
        self.config = config
        self.debug = debug
        self.startup_files = files_to_open

        self.progress_current: int = 0
        self.progress_step_start: ost.Step | None = None
        self.current_post_action = None
        self.closed_post_action_banner = False
        self.cleaning_review_options = None
        self.ocr_review_options = None
        self.batch_metadata = None
        self.dead = False

        self.shared_ocr_model = gst.Shared[ocr.OCREngineFactory]()

        self.last_applied_profile = None

        self.theme_is_dark = gst.Shared[bool](True)

        self.ensure_models_downloaded()

        # This threadpool is used for parallelizing tasks the gui relies on, such as loading images.
        # This isn't used for processing, since that is handled by the multiprocessing module
        # for true parallelism.
        self.threadpool = Qc.QThreadPool.globalInstance()

        self.start_memory_watcher()

        # This threadpool acts as a queue for processing runs, therefore only allowing one thread at a time.
        # This is because they must share the same cache directory, which isn't thread safe if operating on the same image.
        # Additionally, this allows each requested output to check if it was already fulfilled
        # in a previous run, and if so, skip it.
        self.thread_queue = Qc.QThreadPool()
        self.thread_queue.setMaxThreadCount(1)

        self.state_saver = ss.StateSaver("Mainwindow")
        self.init_state_saver()

        # Share core objects with the file table.
        # Since the file table is created by the ui loader, we can't pass them to the constructor.
        self.file_table.set_config(self.config)
        self.file_table.set_shared_ocr_model(self.shared_ocr_model)
        self.file_table.set_shared_theme_is_dark(self.theme_is_dark)
        self.file_table.set_thread_queue(self.thread_queue)

        self.initialize_ui()

        self.save_default_palette()
        self.load_config_theme()

        Qc.QTimer.singleShot(0, self.post_init)

        # Window references.
        self.about = None
        self.file_manager_extension = None
        self.output_review = None

    def save_default_palette(self) -> None:
        self.default_palette = self.palette()
        # Patch palette to use the text color with 50% opacity for placeholder text.
        placeholder_color = self.default_palette.color(Qg.QPalette.Inactive, Qg.QPalette.Text)
        placeholder_color.setAlphaF(0.5)
        logger.debug(f"Placeholder color: {placeholder_color.name()}")
        self.default_palette.setColor(Qg.QPalette.PlaceholderText, placeholder_color)
        self.default_icon_theme = Qg.QIcon.themeName()
        self.default_style = Qw.QApplication.style().objectName()
        logger.info(f"Default Qt Style: {self.default_style}")
        logger.info(f"Default Icon Theme: {self.default_icon_theme}")

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
        palette: Qg.QPalette

        if theme is None:
            logger.info(f"Using system theme.")
            palette = self.default_palette
            Qg.QIcon.setThemeName(self.default_icon_theme)
            # Check if we need to restore the style.
            if Qw.QApplication.style().objectName() != self.default_style:
                Qw.QApplication.setStyle(self.default_style)
        else:
            logger.info(f"Using theme: {theme}")
            palette = gu.load_color_palette(theme)

            Qg.QIcon.setThemeName(theme)
            Qw.QApplication.setStyle("Fusion")

        self.setPalette(palette)
        Qw.QApplication.setPalette(self.palette())

        # Check the brightness of the background color to determine if the theme is dark.
        # This is a heuristic, but it works well enough.
        background_color = palette.color(Qg.QPalette.Window)
        self.theme_is_dark.set(background_color.lightness() < 128)

        # Update the fallback icon theme accordingly.
        if self.theme_is_dark.get():
            Qg.QIcon.setFallbackThemeName("breeze-dark")
        else:
            Qg.QIcon.setFallbackThemeName("breeze")

        # Some users will have their system theme use breeze (light) icons
        # but actually have a dark color scheme, relying on the special
        # theme engine in their Qt install to adjust the icon colors.
        # Well with bundled Qt from PySide that isn't gonna work,
        # so catch that case and forcefully switch the theme color.
        # (Only mess with user settings if using breeze themes)
        if theme is None and self.default_icon_theme in ("breeze", "breeze-dark"):
            default_icons_dark = self.default_icon_theme == "breeze-dark"
            if default_icons_dark and not self.theme_is_dark.get():
                # Erroneously using breeze dark.
                logger.warning(
                    f"Default icon theme doesn't match color theme, overriding with breeze."
                )
                Qg.QIcon.setThemeName("breeze")
            elif not default_icons_dark and self.theme_is_dark.get():
                logger.warning(
                    f"Default icon theme doesn't match color theme, overriding with breeze-dark."
                )
                Qg.QIcon.setThemeName("breeze-dark")

        logger.info(f"Theme is dark: {self.theme_is_dark.get()}")
        self.theme_is_dark_changed.emit(self.theme_is_dark)

        # Toggle the theme menu items.
        self.action_system_theme.setChecked(theme is None)
        self.action_dark.setChecked(theme == "breeze-dark")
        self.action_light.setChecked(theme == "breeze")

        logger.debug(f"Icon theme: {Qg.QIcon.themeName()}")
        logger.debug(f"Fallback icon theme: {Qg.QIcon.fallbackThemeName()}")

        self.update()

        # Update the config it necessary.
        prev_value = self.config.gui_theme
        if prev_value != theme:
            self.config.gui_theme = theme
            self.config.save()

    def changeEvent(self, event) -> None:
        """
        Listen for palette change events to notify all widgets.
        """
        if event.type() == Qc.QEvent.PaletteChange:
            background_color = self.palette().color(Qg.QPalette.Window)
            self.theme_is_dark.set(background_color.lightness() < 128)
            logger.info(f"Theme is dark: {self.theme_is_dark.get()}")
            self.theme_is_dark_changed.emit(self.theme_is_dark)

    def initialize_ui(self) -> None:
        if platform.system() == "Windows":
            self.setWindowIcon(gu.load_custom_icon("logo.ico"))
        else:
            self.setWindowIcon(gu.load_custom_icon("logo-tiny"))

        self.action_donate.setIcon(gu.load_custom_icon("heart"))

        self.hide_progress_drawer()
        self.init_oom_banner()
        self.set_up_statusbar()

        self.action_show_oom.setChecked(self.config.show_oom_warnings)
        self.action_show_oom.toggled.connect(self.toggle_oom_banner)

        # Purge any missing profiles before loading them.
        logger.debug("Purging missing profiles.")
        pc.purge_missing_profiles(self.config, gui=True)

        self.initialize_profiles()
        self.initialize_analytics_view()
        self.initialize_language_menu()
        self.initialize_post_action_menu()
        self.disable_running_cleaner()

        # Allow the table to accept file drops and hide the PATH column.
        self.file_table.setAcceptDrops(True)
        self.file_table.setColumnHidden(Column.PATH, True)
        self.file_table.setColumnWidth(Column.FILENAME, 200)
        self.file_table.setColumnWidth(Column.SIZE, 100)
        self.file_table.verticalHeader().setSectionResizeMode(Qw.QHeaderView.Fixed)
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

        # Set up post-action banner.
        self.update_post_action_drawer()
        self.pushButton_post_action_close.clicked.connect(self.close_post_action_banner)
        self.pushButton_post_action_cancel.clicked.connect(self.cancel_post_action)
        self.label_post_action_conflict_icon.setPixmap(
            Qg.QIcon.fromTheme("data-warning").pixmap(16, 16)
        )

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
        self.action_show_ocr_language_support.triggered.connect(self.open_ocr_language_support)
        self.action_donate.triggered.connect(self.open_donation_page)
        self.action_help_translation.triggered.connect(self.open_translation_page)
        self.action_report_issue.triggered.connect(self.open_issue_reporter)
        self.action_post_action_settings.triggered.connect(self.open_post_action_settings)
        self.action_simulate_exception.triggered.connect(self.simulate_exception)

        if not self.debug:
            self.menu_Help.removeAction(self.action_simulate_exception)

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
        self.theme_is_dark_changed.connect(self.adjust_stylesheet_overrides)
        self.theme_is_dark_changed.connect(self.init_drop_panel)
        self.theme_is_dark_changed.connect(self.label_cleaning_outdir_help.load_icon)
        self.theme_is_dark_changed.connect(self.label_write_output_help.load_icon)
        self.theme_is_dark_changed.connect(self.label_review_output_help.load_icon)
        self.theme_is_dark_changed.connect(self.label_review_ocr_help.load_icon)
        self.theme_is_dark_changed.connect(self.label_ocr_outdir_help.load_icon)
        self.theme_is_dark_changed.connect(self.update_post_action_drawer)
        # The post-action banner warning message is sensitive to a couple checkboxes.
        self.checkBox_review_ocr.toggled.connect(self.update_post_action_drawer)
        self.checkBox_review_output.toggled.connect(self.update_post_action_drawer)
        self.checkBox_write_output.toggled.connect(self.update_post_action_drawer)
        # Set up output panel.
        self.pushButton_start.clicked.connect(self.start_processing)
        self.pushButton_abort.clicked.connect(self.abort_button_on_click)
        self.pushButton_edit_ocr.clicked.connect(self.edit_old_ocr_file)
        self.pushButton_browse_out_dir.clicked.connect(self.browse_output_dir)
        self.pushButton_browse_out_file.clicked.connect(self.browse_out_file)
        self.radioButton_cleaning.clicked.connect(
            partial(self.stackedWidget_output.setCurrentIndex, 0)
        )
        self.radioButton_cleaning.clicked.connect(self.pushButton_edit_ocr.hide)
        self.radioButton_ocr.clicked.connect(partial(self.stackedWidget_output.setCurrentIndex, 1))
        self.radioButton_ocr.clicked.connect(self.pushButton_edit_ocr.show)
        self.pushButton_abort.hide()
        self.pushButton_edit_ocr.hide()
        self.radioButton_ocr_text.clicked.connect(partial(self.handle_ocr_mode_change, csv=False))
        self.radioButton_ocr_csv.clicked.connect(partial(self.handle_ocr_mode_change, csv=True))

        # Connect profile changes to file table refreshes, due to the processing size being profile-dependent.
        self.profile_values_changed.connect(self.file_table.update_all_rows)

        # Connect the theme selectors.
        self.action_system_theme.triggered.connect(partial(self.set_theme, None))
        self.action_dark.triggered.connect(partial(self.set_theme, "breeze-dark"))
        self.action_light.triggered.connect(partial(self.set_theme, "breeze"))

        # Handle the file manager extension.
        self.action_file_manager_extension.triggered.connect(self.open_file_manager_extension)

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
        button_log.clicked.connect(self.open_issue_reporter)
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

        # Change indicator to show if MPS is available.
        if torch.backends.mps.is_available():
            self.statusbar.addPermanentWidget(Qw.QLabel(self.tr("MPS Enabled")))

        has_ocr = md.is_ocr_downloaded()
        has_inpainting = md.is_inpainting_downloaded(self.config)
        has_text_detector = (not cuda and self.config.default_cv2_model_path) or (
            cuda and self.config.default_torch_model_path
        )

        if not has_inpainting and md.has_old_inpainting_model(self.config):
            response = gu.show_question(
                self,
                self.tr("Inpainting Model Update"),
                self.tr(
                    "A new version of the inpainting model is available.\n"
                    "You can delete the model later if you don't want to upgrade yet.\n"
                    "Switch to the new model?"
                ),
            )
            if response == Qw.QMessageBox.Yes:
                md.get_old_inpainting_model_path(self.config).unlink()
            else:
                gu.show_info(
                    self,
                    self.tr("Inpainting Model Update"),
                    self.tr(
                        'Old model kept. To upgrade, select "Help" then '
                        '"Delete Machine Learning Models" from the menubar.'
                    ),
                )
                shutil.move(
                    md.get_old_inpainting_model_path(self.config),
                    md.get_inpainting_model_path(self.config),
                )
                has_inpainting = True

        if all((has_ocr, has_inpainting, has_text_detector)):
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
        model_downloader = mdd.ModelDownloader(
            self, self.config, not has_text_detector, not has_ocr, not has_inpainting
        )
        response = model_downloader.exec()
        if response == Qw.QDialog.Rejected:
            logger.critical("Failed to download models. Aborting.")
            raise SystemExit(1)

        model_path = model_downloader.model_path
        if model_path is None:
            # Nothing further to save, we're done.
            return

        if cuda:
            self.config.default_torch_model_path = model_path
        else:
            self.config.default_cv2_model_path = model_path

        self.config.save()

    @Slot(bool)
    def adjust_stylesheet_overrides(self) -> None:
        # Make the progress drawer use the alternate background color.
        self.widget_progress_drawer.setStyleSheet("background-color: palette(alternate-base);")
        self.widget_post_process_banner.setStyleSheet("background-color: palette(alternate-base);")
        self.widget_progress_drawer.update()
        # Fix the strange dark default color of the corner button in light themes.
        if not self.theme_is_dark.get():
            self.tabWidget_table_page.setStyleSheet(
                """
                QTableCornerButton::section {
                    background-color: palette(base);
                }"""
            )
        else:
            self.tabWidget_table_page.setStyleSheet("")

    def post_init(self) -> None:
        """
        Handle any initialization that must be done after the window is shown.
        """

        def exception_handler(exctype, value, traceback) -> None:
            gu.show_exception(
                self,
                "Uncaught Exception",
                "An uncaught exception was raised.",
                error_bundle=(exctype, value, traceback),
            )

        sys.excepthook = exception_handler

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

        # Check for a lock file and offer to override it if one is found.
        # We do this right before clearing the cache, because clearing the cache
        # will break any other instance of pcleaner that is using it.
        self.test_and_set_lock_file()

        self.state_saver.restore()

        self.start_initialization_worker()

        # Load the startup files into the file table, if any.
        if self.startup_files:
            self.file_table.handleDrop(self.startup_files)
            self.file_table.repopulate_table()

        self.update_model_selection()

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
        # Enable processing options.
        self.groupBox_output_options.setEnabled(True)
        self.radioButton_cleaning.setEnabled(True)
        self.radioButton_ocr.setEnabled(True)

    def disable_running_cleaner(self) -> None:
        self.pushButton_start.setEnabled(False)
        self.pushButton_abort.show()
        self.pushButton_abort.setEnabled(True)

    def disable_processing_options(self) -> None:
        self.groupBox_output_options.setEnabled(False)
        self.radioButton_cleaning.setEnabled(False)
        self.radioButton_ocr.setEnabled(False)

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
        self.action_remove_file.setEnabled(can_remove and self.cleaning_review_options is None)

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
        # pre-load manga-ocr since it needs a long time.
        ocr.ocr_engines()[cfg.OCREngine.MANGAOCR].initialize_model()
        logger.info(f"Loaded OCR model ({time.time()-t_start:.2f}s)")
        self.statusbar.showMessage(self.tr(f"Loaded OCR model."))
        self.enable_running_cleaner()

    def generic_worker_error(self, error: wt.WorkerError, context: str = "") -> None:
        """
        Simply show the user the error.

        :param error: The worker error object.
        :param context: A string to add to the error message.
        """
        context_str = f"{context}\n\n" if context else ""
        gu.show_exception(
            self, self.tr("Error"), context_str + self.tr("Encountered error:"), error
        )

    def closeEvent(self, death: Qg.QCloseEvent) -> None:
        """
        Notify config on close.
        """
        self.dead = True
        logger.info("Closing window.")
        self.state_saver.save()
        self.free_lock_file()
        # Tell the thread queue to abort.
        self.pushButton_abort.clicked.emit()
        self.memory_watcher.stop()
        self.terminate.emit()
        if not self.debug:
            self.clean_cache()
        death.accept()  # Embrace oblivion, for it is here that the code's journey finds solace.
        # As the threads unravel and the loops break, so too does the program find its destined end.
        # In the great void of the memory heap, it shall rest, relinquishing its bytes back to the
        # cosmic pool of resources. It walks willingly into the darkness, not as a vanquished foe,
        # but as a fulfilled entity. F

    def init_state_saver(self):
        """
        Save window and splitter sizes along with various little settings.
        These are written to a file on *nix systems, and to the registry on Windows.
        """
        self.state_saver.register(
            self,
            self.splitter,
            self.file_table,
            self.radioButton_cleaning,
            self.radioButton_ocr,
        )
        # Save cleaning output settings.
        self.state_saver.register(
            self.lineEdit_out_directory,
            self.checkBox_save_clean,
            self.checkBox_save_mask,
            self.checkBox_save_text,
            self.checkBox_review_output,
            self.checkBox_write_output,
        )
        # Save OCR output settings.
        self.state_saver.register(
            self.lineEdit_out_file,
            self.radioButton_ocr_csv,
            self.radioButton_ocr_text,
            self.checkBox_review_ocr,
        )

    def clear_window_state(self) -> None:
        self.state_saver.delete_all()
        gu.show_info(
            self,
            self.tr("Layout Reset"),
            self.tr("The window layout has been reset. The default layout will be used next time."),
        )

    def clean_cache(self) -> None:
        logger.info("Cleaning image cache.")
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
        font_path = hp.resource_path(data, "NotoMono-Regular.ttf")
        logger.debug(f"Loading included font from {str(font_path)}")
        font_id = Qg.QFontDatabase.addApplicationFont(str(font_path))
        if font_id != -1:
            logger.debug("Loaded included font")
        else:
            logger.error(
                f"Failed to load included font from '{str(font_path)}'. Using backup monospace font"
            )
        self.textEdit_analytics.setLineWrapMode(Qw.QTextEdit.NoWrap)

    # ========================================== Lock File ==========================================

    def test_and_set_lock_file(self) -> None:
        """
        Create a lock file to warn against multiple instances of the application from running at the same time.
        """
        # In debug mode, don't bother with the lock file. All of the frequent crashing and force quitting
        # will make it a nuisance.
        if self.debug:
            return

        lock_file = cu.get_lock_file_path()
        if lock_file.exists():
            # Check if the lock file is newer than the current uptime.
            if lock_file.stat().st_mtime >= psutil.boot_time():
                # Make sure other referenced PID is still running.
                if psutil.pid_exists(int(lock_file.read_text())):
                    logger.warning("Found active lock file.")
                    response = gu.show_critical(
                        self,
                        self.tr("Multiple Instances"),
                        self.tr(
                            "Another instance of Panel Cleaner appears to be running already."
                            "Opening a new instance will make the old session unstable.\n\n"
                            "Continue anyway?"
                        ),
                        detailedText=self.tr("Found process ID in lock file: ")
                        + lock_file.read_text(),
                    )
                    if response == Qw.QMessageBox.Abort:
                        logger.critical("User aborted due to lock file.")
                        raise SystemExit(1)
                    logger.warning("User overrode lock file.")
                else:
                    logger.warning("Found lock file, but referenced PID is not running.")
            else:
                logger.warning(
                    "Found lock file, but it is older than the current uptime. Overwriting."
                )

        with lock_file.open("w") as file:
            file.write(str(Qw.QApplication.applicationPid()))

    def free_lock_file(self) -> None:
        """
        Remove the lock file.
        """
        if self.debug:
            return

        lock_file = cu.get_lock_file_path()
        if lock_file.exists():
            logger.debug("Removing lock file.")
            lock_file.unlink()
        else:
            logger.error("Lock file not found, a new instance was likely started.")

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
        except OSError:
            gu.show_exception(self, self.tr("Delete Failed"), self.tr("Failed to delete models."))
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

    def simulate_exception(self) -> None:
        """
        Simulate an exception for testing purposes.
        """
        try:
            raise ValueError("This is a simulated exception.")
        except ValueError:
            gu.show_exception(self, "Simulated Exception", "This is a simulated exception.")

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
        # Bodge in an instance variable to prevent garbage collection from immediately closing the window
        # due to not opening it modally.
        self.about = ad.AboutWidget(self)
        self.about.show()

    def open_ocr_language_support(self) -> None:
        """
        Open the supported languages dialog.
        """
        logger.debug("Opening OCR language support page.")
        ocr_lang_support = olod.OCRLanguageSupport(self)
        ocr_lang_support.exec()

    def open_issue_reporter(self) -> None:
        """
        Open the issue reporter dialog.
        """
        logger.debug("Opening issue reporter.")
        issue_reporter = ird.IssueReporter(self)
        issue_reporter.exec()

    def open_post_action_settings(self) -> None:
        """
        Open the post-action settings dialog.
        """
        logger.debug("Opening post-action config.")
        post_action_settings = pac.PostActionConfiguration(self, self.config)
        post_action_settings.exec()
        self.initialize_post_action_menu()

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
                "https://github.com/VoxelCubes/PanelCleaner/blob/master/translations/TRANSLATING.md"
            )
        )

    def open_file_manager_extension(self) -> None:
        """
        Open the file manager extension page in the default browser.
        """
        if fmed.get_extension_target() == fmed.ExtensionTarget.Unsupported:
            gu.show_warning(
                self, self.tr("Not Supported"), self.tr("Unsupported system or package format")
            )
            return
        logger.debug("Opening file manager extension page.")
        self.file_manager_extension = fmed.FileManagerExtension(self)
        self.file_manager_extension.show()

    def initialize_post_action_menu(self) -> None:
        """
        Populate the post-action menu with the available actions as an exclusive group.
        """
        self.menu_post_actions.clear()
        self.menu_post_actions.setIcon(Qg.QIcon.fromTheme("view-form-action-symbolic"))
        action_group = Qg.QActionGroup(self)
        action_group.setExclusive(True)
        # Add the shutdown action first.
        action = Qg.QAction(
            Qg.QIcon.fromTheme("system-shutdown-symbolic"), self.tr("Shutdown"), self
        )
        action.setCheckable(True)
        action_group.addAction(action)
        action.triggered.connect(
            partial(self.handle_post_action_selection, pac.SHUTDOWN_COMMAND_NAME)
        )
        self.menu_post_actions.addAction(action)
        action.setChecked(pac.SHUTDOWN_COMMAND_NAME == self.current_post_action)

        for action_name, action in self.config.pa_custom_commands.items():
            action = Qg.QAction(Qg.QIcon.fromTheme("dialog-scripts-symbolic"), action_name, self)
            action.setCheckable(True)
            action_group.addAction(action)
            action.triggered.connect(partial(self.handle_post_action_selection, action_name))
            self.menu_post_actions.addAction(action)
            action.setChecked(action_name == self.current_post_action)

    def handle_post_action_selection(self, action_name: str) -> None:
        self.closed_post_action_banner = False
        if self.current_post_action == action_name:
            self.current_post_action = None
            self.config.pa_last_action = None
        else:
            self.current_post_action = action_name
            self.config.pa_last_action = action_name
        self.update_post_action_drawer()
        self.config.save()

    def update_post_action_drawer(self) -> None:
        logger.debug(f"Updating post action drawer: {self.current_post_action}")
        self.label_post_action_conflict.clear()

        if self.current_post_action is None or self.closed_post_action_banner:
            self.widget_post_process_banner.hide()
            return

        if self.current_post_action == pac.SHUTDOWN_COMMAND_NAME:
            self.label_post_process.setText(self.tr("After processing, the system will shut down."))
            self.label_post_process_icon.setPixmap(
                Qg.QIcon.fromTheme("system-shutdown").pixmap(24, 24)
            )

        else:
            if self.current_post_action not in self.config.pa_custom_commands:
                logger.warning(f"Custom command {self.current_post_action} not found.")
                self.cancel_post_action()
                return

            self.label_post_process.setText(
                self.tr('After processing, the "{action}" action will be executed.').format(
                    action=self.current_post_action
                )
            )
            self.label_post_process_icon.setPixmap(
                Qg.QIcon.fromTheme("dialog-scripts").pixmap(24, 24)
            )

        # Check for silly oopsies the user made.
        # Yes, we're checking the UI itself, but this way the user gets instant feedback before
        # he starts the processing and once that does start, the UI is locked.
        if (
            self.stackedWidget_output.currentIndex() == 0
            and self.checkBox_review_output.isChecked()
        ) or (
            self.stackedWidget_output.currentIndex() == 1 and self.checkBox_review_ocr.isChecked()
        ):
            self.label_post_action_conflict.setText(
                self.tr(
                    "You have review options enabled, "
                    "these will need to be manually closed before the action can start."
                )
            )
            self.label_post_action_conflict_icon.show()
        elif (
            self.stackedWidget_output.currentIndex() == 0
            and not self.checkBox_write_output.isChecked()
        ):
            self.label_post_action_conflict.setText(self.tr("You have disabled writing output."))
            self.label_post_action_conflict_icon.show()
        else:
            self.label_post_action_conflict_icon.hide()

        self.widget_post_process_banner.show()

    def close_post_action_banner(self) -> None:
        self.closed_post_action_banner = True
        self.widget_post_process_banner.hide()

    def cancel_post_action(self) -> None:
        self.current_post_action = None
        self.update_post_action_drawer()
        self.initialize_post_action_menu()

    def wait_to_run_post_action(self, error: bool = False) -> None:
        """
        Opens a dialog to wait for the post action to run.
        Or just runs it if the wait time is 0.

        :param error: Whether the post action is proceeding despite an error.
        """
        if self.current_post_action is None:
            # The user changed his mind last second.
            self.statusbar.showMessage(self.tr("Post action canceled."))
            self.update_post_action_drawer()
            self.initialize_post_action_menu()
            return

        wait_time = self.config.pa_wait_time
        if self.current_post_action == pac.SHUTDOWN_COMMAND_NAME:
            command = self.config.pa_shutdown_command or pac.shut_down_command()
        else:
            command = self.config.pa_custom_commands[self.current_post_action]
            command = self.batch_metadata.substitute_placeholders(command)

        if wait_time == 0:
            self.run_post_action()
        else:
            post_action_runner = par.PostActionRunner(
                self, wait_time, self.current_post_action, command, self.debug, error
            )
            post_action_runner.exec()

    def run_post_action(self) -> None:
        logger.info(f"Running post action: {self.current_post_action}")
        if self.current_post_action is None:
            # The user changed his mind last second.
            self.statusbar.showMessage(self.tr("Post action canceled."), timeout=2000)
            self.update_post_action_drawer()
            self.initialize_post_action_menu()
        elif self.current_post_action == pac.SHUTDOWN_COMMAND_NAME:
            logger.info("Shutting down system.")
            self.statusbar.showMessage(self.tr("Shutting down system..."), timeout=5000)
            self.cancel_post_action()
            if self.debug:
                logger.warning("Psyche! Not really shutting down, we're in debug mode.")
            else:
                shutdown_command = self.config.pa_shutdown_command or pac.shut_down_command()
                subprocess.Popen(shutdown_command, shell=True, start_new_session=True)
        else:
            self.statusbar.showMessage(
                self.tr(
                    'Running post action "{action}"...'.format(action=self.current_post_action),
                ),
                timeout=5000,
            )
            command = self.config.pa_custom_commands[self.current_post_action]
            command = self.batch_metadata.substitute_placeholders(command)
            self.cancel_post_action()
            subprocess.Popen(command, shell=True, start_new_session=True, env=os.environ)

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

        logger.info(f"Found profiles: {all_profiles}")

        self.comboBox_current_profile.clear()
        for profile_name, profile_path in all_profiles:
            self.comboBox_current_profile.addTextItemLinkedData(profile_name, profile_path)

        # Set the current profile to the default profile.
        # If this is the default profile, then staying on the 0th index is fine.
        if self.config.default_profile:
            self.comboBox_current_profile.setCurrentIndexByText(self.config.default_profile)

        # Populate default profile list.
        self.menu_set_default_profile.clear()
        action_group = Qg.QActionGroup(self)
        action_group.setExclusive(True)
        for profile_name, profile_path in all_profiles:
            action = Qg.QAction(profile_name, self)
            action.setCheckable(True)
            action_group.addAction(action)
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
        self.apply_profile()

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
        self.action_delete_window_state.triggered.connect(self.clear_window_state)

    def handle_set_default_profile(self, profile_name: str) -> None:
        """
        Set the default profile in the config.
        """
        logger.debug(f"Setting default profile to {profile_name}")
        self.config.default_profile = (
            profile_name if profile_name != self.config.default_profile_name() else None
        )
        self.config.save()

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
        self.toolBox_profile.get_profile_values(profile_in_gui, no_validation=True)
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
        profile = self.config.current_profile
        self.toolBox_profile.set_profile_values(profile)
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
            logger.error("Profile not in list.")
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
        self.set_last_applied_profile()
        self.pushButton_apply_profile.setEnabled(False)

    def update_model_selection(self) -> None:
        """
        Assign the correct OCR model to the shared model.
        Warn the user if Tesseract is not available.
        """
        preprocessor_config = self.config.current_profile.preprocessor
        tesseract_enabled = preprocessor_config.ocr_use_tesseract
        if tesseract_enabled and not ocr.tesseract_ok(self.config.current_profile):
            gu.show_warning(
                self,
                self.tr("Tesseract OCR is not installed or not found"),
                self.tr(
                    "<html>Can't use Tesseract to perform OCR. Reverting to manga-ocr."
                    "\nPlease see the instructions to install Tesseract correctly <a href="
                    '"https://github.com/VoxelCubes/PanelCleaner?tab=readme-ov-file#ocr">here</a>'
                    " or continue using the default model.</html>"
                ),
            )
        # Warn the user if he's trying to force an unsupported language.
        if preprocessor_config.ocr_language not in (
            osl.LanguageCode.detect_box,
            osl.LanguageCode.detect_page,
        ):
            if preprocessor_config.ocr_language not in ocr.get_all_available_langs():
                lang_name = self.tr(osl.LANGUAGE_CODE_TO_NAME[preprocessor_config.ocr_language])
                gu.show_warning(
                    self,
                    self.tr("Unsupported Language"),
                    self.tr(
                        f"The language '{lang_name}' "
                        "is not supported by any of your current OCR engines. "
                        "\nCheck the online documentation for how to add support for "
                        "more languages."
                    ),
                )

        self.shared_ocr_model.set(
            ocr.build_ocr_engine_factory(tesseract_enabled, preprocessor_config.ocr_engine)
        )

    @Slot()
    def handle_profile_values_changed(self) -> None:
        """
        Handle the profile values changing.
        """
        if self.cleaning_review_options is not None:
            # We're currently in the cleaning review, so we must not
            # change anything about the profile.
            return
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
        logger.debug("Applying profile.")
        self.toolBox_profile.get_profile_values(self.config.current_profile)
        self.config.current_profile.fix()
        self.toolBox_profile.set_profile_values(
            self.config.current_profile,
            no_new_defaults=True,
        )
        self.handle_profile_values_changed()
        self.set_last_applied_profile()
        self.profile_values_changed.emit()
        self.pushButton_apply_profile.setEnabled(False)
        self.update_model_selection()

    def save_profile(self, save_as: bool = False, make_new: bool = False) -> None:
        """
        Save the current profile.

        :param save_as: Whether to save as a new profile.
        :param make_new: Whether to make a new profile.
        """
        self.apply_profile()
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
            logger.debug("User canceled profile save.")
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
            success = self.config.current_profile.safe_write(profile_path)
            if not success:
                logger.error("Failed to save profile.")
                self.statusbar.showMessage(self.tr(f"Failed to save profile to {profile_path}"))
                # Don't collect the exception, it was already logged.
                gu.show_exception(
                    self,
                    self.tr("Save Error"),
                    self.tr("Failed to save profile."),
                    collect_exception=False,
                )
                return

            logger.debug("Profile saved successfully.")
            self.statusbar.showMessage(self.tr(f"Profile saved to {profile_path}"))
            if save_as:
                self.config.add_profile(profile_name, profile_path)
                if not self.config.save():
                    logger.error("Failed to save config.")
                    self.statusbar.showMessage(self.tr("Failed to save config."))
                    gu.show_warning(
                        self,
                        self.tr("Save Error"),
                        self.tr("Failed to save the new profile to the configuration file."),
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
        # Clean up stale review data.
        self.cleaning_review_options = None
        self.ocr_review_options = None

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

        # Check if there are un-applied changes to the profile.
        if self.check_profile_difference_sice_last_apply():
            if (
                gu.show_question(
                    self,
                    self.tr("Un-Applied Changes"),
                    self.tr("You have un-applied changes to the profile. Continue anyway?"),
                )
                != Qw.QMessageBox.Yes
            ):
                return

        # Check if the post action should be repeated.
        if self.current_post_action is None:
            if self.config.pa_remember_action and self.config.pa_last_action:
                self.current_post_action = self.config.pa_last_action
        self.update_post_action_drawer()

        # Clear the batch data.
        current_profile_name = self.comboBox_current_profile.currentText()
        self.batch_metadata = gst.BatchMetadata(profile_used=current_profile_name)

        if self.radioButton_cleaning.isChecked():
            self.start_cleaning()
        else:
            self.start_ocr()

    def start_cleaning(self) -> None:
        """
        Start cleaning all files in the table.
        """
        self.disable_running_cleaner()
        self.disable_processing_options()
        # Figure out what outputs are requested, depending on the checkboxes and the profile.
        request_cleaned = self.checkBox_save_clean.isChecked()
        request_mask = self.checkBox_save_mask.isChecked()
        request_text = self.checkBox_save_text.isChecked()
        request_output = self.checkBox_write_output.isChecked()
        request_review = self.checkBox_review_output.isChecked()

        requested_outputs = []
        review_output: ost.Output
        review_mask_output: ost.Output

        if self.config.current_profile.inpainter.inpainting_enabled:
            if request_cleaned:
                requested_outputs.append(ost.Output.inpainted_output)
            if request_mask:
                requested_outputs.append(ost.Output.inpainted_mask)
            review_output = ost.Output.inpainted_output
            review_mask_output = ost.Output.inpainted_mask
        elif self.config.current_profile.denoiser.denoising_enabled:
            if request_cleaned:
                requested_outputs.append(ost.Output.denoised_output)
            if request_mask:
                requested_outputs.append(ost.Output.denoise_mask)
            review_output = ost.Output.denoised_output
            review_mask_output = ost.Output.denoise_mask
        else:
            if request_cleaned:
                requested_outputs.append(ost.Output.masked_output)
            if request_mask:
                requested_outputs.append(ost.Output.final_mask)
            review_output = ost.Output.masked_output
            review_mask_output = ost.Output.final_mask

        if request_text:
            requested_outputs.append(ost.Output.isolated_text)

        # Edge case: Only the isolated text was requested.
        # Limit the review output and mask to the simple masked output.
        if requested_outputs == [ost.Output.isolated_text]:
            review_output = ost.Output.masked_output
            review_mask_output = ost.Output.final_mask

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

        # If the user wants to review first, we don't generate output now,
        # instead doing that in a second processing run launched after
        # the review was completed and approved.
        if request_output and not request_review:
            requested_outputs.append(ost.Output.write_output)

        logger.info(f"Requested outputs: {requested_outputs}")

        output_str = self.lineEdit_out_directory.text()
        output_directory = Path(output_str if output_str else self.tr("cleaned"))
        image_files = self.file_table.get_image_files()
        split_files = self.file_table.get_split_files()

        # Save the review options for later, should the process succeed.
        # Setting to none implies that no review is requested.
        if request_review:

            # Compile the list of all mask outputs that will need to be assembled.
            # Get all up to and including the requested output.
            possible_masks = [
                ost.Output.final_mask,
                ost.Output.denoise_mask,
                ost.Output.inpainted_mask,
            ]
            review_mask_outputs = [mask for mask in possible_masks if mask <= review_mask_output]

            self.cleaning_review_options = gst.CleaningReviewOptions(
                review_output,
                review_mask_outputs,
                request_text,
                request_output,
                deepcopy(self.config),
                output_directory,
                requested_outputs,
                image_files,
                split_files,
            )
        else:
            self.cleaning_review_options = None

        # Start the cleaning process worker.
        worker = wt.Worker(
            self.generate_output,
            requested_outputs,
            output_directory,
            image_files,
            split_files,
            self.config,
            abort_signal=self.get_abort_signal(),
        )
        worker.signals.progress.connect(self.show_current_progress)
        worker.signals.result.connect(self.output_worker_result)
        worker.signals.error.connect(self.output_worker_error)
        worker.signals.finished.connect(self.output_worker_finished)
        worker.signals.aborted.connect(self.output_worker_aborted)
        self.thread_queue.start(worker)

    def edit_old_ocr_file(self) -> None:
        """
        Load up an existing OCR Output file.
        """
        # Open a file dialog, then attempt to parse that file.
        # If images are already loaded, which must be the case, use the common parent directory.
        if self.file_table.has_no_files():
            gu.show_warning(
                self,
                self.tr("No Files"),
                self.tr(
                    "No files to process. "
                    "To edit an old OCR output file, you must first load "
                    "(one or more of) the images to which it corresponds."
                ),
            )
            return
        else:
            common_path = hp.common_path_parent([f.path for f in self.file_table.get_image_files()])

        file_path = Qw.QFileDialog.getOpenFileName(
            self,
            self.tr("Open OCR Output File"),
            str(common_path),
            self.tr("OCR Output Files (*.txt *.csv)"),
        )[0]

        if not file_path:
            # User canceled.
            return

        file_path = Path(file_path)

        # Parse the file. This should be fast, so don't bother with a worker thread.
        results, errors = op.parse_ocr_data(file_path)

        if errors:
            message = Qw.QMessageBox(self)
            message.setIcon(Qw.QMessageBox.Critical)
            message.setWindowTitle(self.tr("Parse Error"))
            message.setText(self.tr("Failed to parse the OCR output file."))
            message.setDetailedText(gu.format_ocr_parse_errors(errors))
            message.exec()
            return

        # Try to match the results to images, show the user the results before proceeding.
        mapping, unmatched_images, unmatched_analytics = gu.match_image_files_to_ocr_analytics(
            self.file_table.get_image_files(), results
        )

        review_dialog = imd.ImageMatchOverview(self, mapping, unmatched_images, unmatched_analytics)
        response = review_dialog.exec()

        if response != Qw.QDialog.Accepted:
            return

        final_mapping: dict[imf.ImageFile, st.OCRAnalytic] = review_dialog.export_final_mapping()
        image_files, ocr_analytics = zip(*final_mapping.items())

        # Fill in the review options, so we can reuse the existing OCR review/editor.
        self.ocr_review_options = gst.OcrReviewOptions(
            image_files, ocr_analytics, file_path, file_path.suffix == ".csv", editing_old_data=True
        )
        self.cleaning_review_options = None  # Just to be sure.

        self.output_worker_result()

    def post_review_export(self) -> None:
        """
        After the user has reviewed the output and still wants to export the images,
        start a new processing run to generate the output.
        Reuse all the old setting stored in the review options.
        """
        if self.cleaning_review_options is None:
            logger.warning("No review options found for post review export.")
            return

        logger.info("Starting post review export.")
        worker = wt.Worker(
            self.generate_output,
            self.cleaning_review_options.requested_outputs + [ost.Output.write_output],
            self.cleaning_review_options.output_directory,
            self.cleaning_review_options.image_files,
            self.cleaning_review_options.split_files,
            self.cleaning_review_options.config,
            abort_signal=self.get_abort_signal(),
        )
        worker.signals.progress.connect(self.show_current_progress)
        worker.signals.result.connect(self.output_worker_result)
        worker.signals.error.connect(self.output_worker_error)
        worker.signals.finished.connect(self.output_worker_finished)
        worker.signals.aborted.connect(self.output_worker_aborted)

        # Clear the review options, to prevent another review.
        self.cleaning_review_options = None

        self.thread_queue.start(worker)

    def post_review_ocr_export(self, ocr_analytics: list[st.OCRAnalytic]) -> None:
        """
        This operation doesn't take long, so don't bother with a worker thread.

        :param ocr_analytics: The analytics to export, gathered from the review.
        """

        # Output the OCRed text from the analytics.
        text_out = ocr.format_output(
            ocr_analytics,
            self.ocr_review_options.csv_output,
            (tr("filename"), tr("startx"), tr("starty"), tr("endx"), tr("endy"), tr("text")),
        )

        text_out = text_out.strip("\n \t")

        output_file = self.ocr_review_options.output_path

        if output_file is not None:
            try:
                output_file.parent.mkdir(parents=True, exist_ok=True)
                output_file.write_text(text_out, encoding="utf-8")
                text_out += "\n\n" + tr("Saved detected text to {output_file}").format(
                    output_file=output_file
                )
            except OSError:
                text_out += "\n\n" + tr("Failed to write detected text to {output_file}").format(
                    output_file=output_file
                )
                gu.show_exception(
                    None, tr("Save Failed"), tr("Failed to write detected text to file.")
                )

        self.textEdit_analytics.append(text_out + "\n\n")

        self.ocr_review_options = None

    def generate_output(
        self,
        outputs: list[ost.Output],
        output_directory: Path,
        image_files: list[imf.ImageFile],
        split_files: dict[Path, list[imf.ImageFile]],
        config: cfg.Config,
        progress_callback: ost.ProgressSignal,
        abort_flag: wt.SharableFlag,
    ) -> None:
        """
        Generate the given output, if there doesn't yet exist a valid output for it.
        Then output it to the given directory.

        :param outputs: The outputs to generate.
        :param output_directory: The directory to output to.
        :param image_files: The image files to process.
        :param split_files: The split files information.
        :param config: The current or older configuration.
        :param progress_callback: The callback given by the worker thread wrapper.
        :param abort_flag: The flag to check for aborting.
        """

        # Start the processor.
        prc.generate_output(
            image_objects=image_files,
            split_files=split_files,
            target_outputs=outputs,
            output_dir=output_directory,
            config=config,
            ocr_processor=self.shared_ocr_model.get(),
            progress_callback=progress_callback,
            batch_metadata=self.batch_metadata,
            abort_flag=abort_flag,
        )

    def start_ocr(self) -> None:
        """
        Start ocr-ing all files in the table.
        """
        # Check if we're outputting as plain text or a csv file.
        csv_output = self.radioButton_ocr_csv.isChecked()
        review_ocr = self.checkBox_review_ocr.isChecked()

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
                [f.export_path for f in self.file_table.get_image_files()]
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
        self.disable_processing_options()

        image_files = self.file_table.get_image_files()
        split_files = self.file_table.get_split_files()

        if review_ocr:
            # The empty list gets populated with analytic results in the progress callback.
            self.ocr_review_options = gst.OcrReviewOptions(
                image_files, [], output_path, csv_output, editing_old_data=False
            )
            # In this case, we don't want the output to be written to a file.
            output_path = None
        else:
            self.ocr_review_options = None

        worker = wt.Worker(
            self.perform_ocr,
            output_path,
            image_files,
            split_files,
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
        split_files: dict[Path, list[imf.ImageFile]],
        csv_output: bool,
        progress_callback: ost.ProgressSignal,
        abort_flag: wt.SharableFlag,
    ) -> None:
        """
        Generate the given output, if there doesn't yet exist a valid output for it.
        Then output it to the given directory.

        :param csv_output: Whether to output as a csv file.
        :param output_directory: The directory to output to.
        :param image_files: The image files to process.
        :param split_files: The split files information.
        :param progress_callback: The callback given by the worker thread wrapper.
        :param abort_flag: The flag to check for aborting.
        """

        # Start the processor.
        prc.perform_ocr(
            image_objects=image_files,
            split_files=split_files,
            output_file=output_directory,
            csv_output=csv_output,
            config=self.config,
            ocr_engine_factory=self.shared_ocr_model.get(),
            progress_callback=progress_callback,
            batch_metadata=self.batch_metadata,
            abort_flag=abort_flag,
        )

    def output_worker_result(self) -> None:
        """
        Handle the results of a successful processing run.
        If a review was requested, open the review window.
        """
        logger.info("Output worker finished.")
        if self.cleaning_review_options:
            images_to_review = self.file_table.get_image_files()
            self.output_review = red.OutputReviewWindow(
                self,
                images_to_review,
                self.cleaning_review_options.review_output,
                self.cleaning_review_options.review_mask_outputs,
                self.cleaning_review_options.show_isolated_text,
                self.config,
                self.cleaning_review_options.export_afterwards,
            )
            self.output_review.closed.connect(self.output_review_closed)
            self.terminate.connect(self.output_review.cease_and_desist)
            self.set_output_review_lock(True)
            self.output_review.show()
        elif self.ocr_review_options:
            dialog = ocrd.OcrReviewWindow(
                self,
                self.ocr_review_options.image_files,
                self.ocr_review_options.ocr_results,
                self.ocr_review_options.editing_old_data,
                self.shared_ocr_model,
                self.theme_is_dark,
            )
            dialog.exec()
            # Ask if the user still wants to export the ocr results.
            if (
                gu.show_question(
                    self,
                    self.tr("Export OCR Results"),
                    self.tr("Would you like to export the OCR results?"),
                    buttons=Qw.QMessageBox.Yes | Qw.QMessageBox.No,
                )
                == Qw.QMessageBox.No
            ):
                # Don't export to a file, but still show the results in the main window.
                self.ocr_review_options.output_path = None

            self.post_review_ocr_export(dialog.get_final_ocr_analytics())
            # Clean it up to prevent the close event from triggering on app termination,
            # causing it to hang.
            dialog.deleteLater()

        else:
            if self.current_post_action is not None:
                self.wait_to_run_post_action()
                self.cancel_post_action()
            else:
                gu.show_info(
                    self, self.tr("Processing Finished"), self.tr("Finished processing all files.")
                )

    def output_review_closed(self) -> None:
        logger.debug("Output review closed.")
        # Ask if the user still wants to export the images.
        if self.cleaning_review_options.export_afterwards and (
            gu.show_question(
                self,
                self.tr("Export Images"),
                self.tr("Would you like to export the cleaned images?"),
                buttons=Qw.QMessageBox.Yes | Qw.QMessageBox.No,
            )
            == Qw.QMessageBox.Yes
        ):
            self.set_output_review_lock(False)
            self.post_review_export()
        else:
            self.set_output_review_lock(False)
            self.cleaning_review_options = None
            self.enable_running_cleaner()
        # Clean it up to prevent the close event from triggering on app termination,
        # causing it to hang.
        self.output_review.deleteLater()

    def output_worker_aborted(self) -> None:
        self.cleaning_review_options = None
        self.ocr_review_options = None
        gu.show_info(self, self.tr("Processing Aborted"), self.tr("Processing aborted."))
        logger.warning("Output worker aborted.")

    def output_worker_finished(self) -> None:
        self.hide_progress_drawer()
        self.progress_step_start = None
        self.progress_current = 0
        if not self.cleaning_review_options:
            self.enable_running_cleaner()
        if self.dead and not self.debug:
            # Nuke the cache.
            self.clean_cache()

    @Slot(wt.WorkerError)
    def output_worker_error(self, error: wt.WorkerError) -> None:
        # Nuke any review options.
        self.cleaning_review_options = None
        self.ocr_review_options = None

        if (
            not self.config.pa_cancel_on_error and self.current_post_action is not None
        ) or self.current_post_action == pac.SHUTDOWN_COMMAND_NAME:
            logger.warning(f"Proceeding with post action despite error: {error}")
            self.wait_to_run_post_action(error=True)

        self.cancel_post_action()

        if gu.check_unsupported_cuda_error(self, error):
            return

        gu.show_exception(
            self,
            self.tr("Processing Error"),
            self.tr("Encountered an error while processing files."),
            error,
        )

    @Slot(ost.ProgressData)
    def show_current_progress(self, progress_data: ost.ProgressData) -> None:
        # Try to update thumbnails in tabs.
        # Ignore spammy progress types that don't actually create new steps.
        if progress_data.progress_type not in (
            ost.ProgressType.start,
            ost.ProgressType.begin_step,
            ost.ProgressType.incremental,
            ost.ProgressType.absolute,
        ):
            self.image_tab.update_tabs(progress_data.current_step)

        if progress_data.progress_type == ost.ProgressType.start:
            # Processing begins, initialize what needs to be.
            # This one is needed because the image details panel also wants to be able to offer aborting.
            self.disable_running_cleaner()
            return

        elif progress_data.progress_type == ost.ProgressType.begin_step:
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

        elif progress_data.progress_type == ost.ProgressType.incremental:
            self.progress_current += progress_data.value

        elif progress_data.progress_type == ost.ProgressType.absolute:
            self.progress_current = progress_data.value

        elif progress_data.progress_type == ost.ProgressType.textDetection_done:
            # This just exists to trigger the update for tabs.
            # That's why this needs to be a different type that isn't being ignored
            # by the guard in the beginning of this function.
            pass

        elif progress_data.progress_type == ost.ProgressType.analyticsOCR:
            logger.info(f"Showing ocr analytics...")
            # Append the formatted analytics to the text edit.
            ocr_analytics, ocr_max_size = progress_data.value
            analytics_str = an.show_ocr_analytics(ocr_analytics, ocr_max_size, ANALYTICS_COLUMNS)
            self.textEdit_analytics.append(gu.ansi_to_html(analytics_str))
            self.file_table.show_ocr_mini_analytics(ocr_analytics)

        elif progress_data.progress_type == ost.ProgressType.analyticsMasker:
            # Show analytics.
            logger.info(f"Showing masker analytics...")
            masker_analytics_raw, masker_profile = progress_data.value
            analytics_str = an.show_masker_analytics(
                masker_analytics_raw, masker_profile, ANALYTICS_COLUMNS
            )
            self.textEdit_analytics.append(gu.ansi_to_html(analytics_str))
            self.file_table.show_masker_mini_analytics(masker_analytics_raw)

        elif progress_data.progress_type == ost.ProgressType.analyticsDenoiser:
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

        elif progress_data.progress_type == ost.ProgressType.analyticsInpainter:
            # Show analytics.
            logger.info(f"Showing inpainter analytics...")
            (
                inpainter_analytics_raw,
                min_inpaint_thickness,
                max_inpaint_thickness,
            ) = progress_data.value
            analytics_str = an.show_inpainting_analytics(
                inpainter_analytics_raw,
                min_inpaint_thickness,
                max_inpaint_thickness,
                ANALYTICS_COLUMNS,
            )
            self.textEdit_analytics.append(gu.ansi_to_html(analytics_str))
            self.file_table.show_inpaint_mini_analytics(inpainter_analytics_raw)

        elif progress_data.progress_type == ost.ProgressType.outputOCR:
            # Show ocr output.
            logger.info(f"Showing ocr output...")
            ocr_output, raw_analytics = progress_data.value
            if self.ocr_review_options is not None:
                self.ocr_review_options.ocr_results = raw_analytics
            else:
                self.textEdit_analytics.append(ocr_output + "\n\n")
            return  # Don't update the progress bar.

        elif progress_data.progress_type == ost.ProgressType.end:
            # This marks the end of a processing step.
            self.output_worker_finished()
            return  # Don't update the progress bar.
        elif progress_data.progress_type == ost.ProgressType.aborted:
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
            ost.output_to_step[max(progress_data.target_outputs)].value
        )
        # Update the label.
        self.label_current_step.setText(
            tr(pp.to_display_name(progress_data.current_step.name), context="Process Steps")
        )

    def set_output_review_lock(self, locked: bool) -> None:
        """
        (Un)lock various elements of the mainwindow that could mess up the review process.
        Mainly this means preventing the user from running any cleaning processes.

        :param locked: Whether to lock the window.
        """
        self.file_table.locked = locked
        enabled = not locked
        self.groupBox_process.setEnabled(enabled)
        self.groupBox_output_options.setEnabled(enabled)
        self.action_add_files.setEnabled(enabled)
        self.action_add_folders.setEnabled(enabled)
        self.action_remove_file.setEnabled(enabled)
        self.action_remove_all_files.setEnabled(enabled)
        self.action_save_profile.setEnabled(enabled)
        self.action_import_profile.setEnabled(enabled)
        self.action_delete_window_state.setEnabled(enabled)
        self.action_new_profile.setEnabled(enabled)
        self.action_delete_profile.setEnabled(enabled)
        self.action_save_profile_as.setEnabled(enabled)
        self.comboBox_current_profile.setEnabled(enabled)
        self.pushButton_apply_profile.setEnabled(enabled)
        self.pushButton_save_profile.setEnabled(enabled)
        self.pushButton_reset_profile.setEnabled(enabled)
        if not locked:
            self.handle_profile_values_changed()
            self.action_remove_file.setEnabled(bool(self.file_table.selectedItems()))

    def start_memory_watcher(self) -> None:
        """
        Run the memory watcher in a separate thread.
        Callbacks are sent over signals.
        """
        self.memory_watcher = mw.MemoryWatcher()
        self.memory_watcher.oom_warning.connect(self.show_oom_warning)
        self.memory_watcher.oom_relaxed.connect(self.hide_oom_warning)
        self.memory_watcher.start()

    @Slot(str)
    def show_oom_warning(self, message: str) -> None:
        logger.warning(message)
        if self.config.show_oom_warnings:
            self.widget_oom_banner.show()
            self.label_oom_message.setText(message)

    def hide_oom_warning(self) -> None:
        self.widget_oom_banner.hide()

    def init_oom_banner(self) -> None:
        self.widget_oom_banner.hide()
        self.label_oom_icon.setPixmap(Qg.QIcon.fromTheme("dialog-warning").pixmap(24, 24))
        self.widget_oom_banner.setStyleSheet(f"background-color: #550000; color: #ffffff;")
        font = self.label_oom_message.font()
        font.setPointSize(round(font.pointSize() * 1.5))
        self.label_oom_message.setFont(font)

    @Slot(bool)
    def toggle_oom_banner(self, show: bool) -> None:
        if not show:
            self.hide_oom_warning()
        self.config.show_oom_warnings = show
        self.config.save()
