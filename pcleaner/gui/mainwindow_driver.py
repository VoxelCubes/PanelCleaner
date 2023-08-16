import shutil
from functools import partial
from pathlib import Path
from importlib import resources

import PySide6.QtCore as Qc
import PySide6.QtGui as Qg
import PySide6.QtWidgets as Qw
from PySide6.QtCore import Signal, Slot
from logzero import logger

import pcleaner.cli_utils as cu
import pcleaner.helpers as hp
import pcleaner.config as cfg
import pcleaner.gui.profile_parser as pp
import pcleaner.gui.gui_utils as gu
import pcleaner.profile_cli as pc
from pcleaner.gui.ui_generated_files.ui_Mainwindow import Ui_MainWindow
from pcleaner.gui.file_table import Column
from pcleaner import __display_name__, __version__
from pcleaner import data
import pcleaner.gui.new_profile_driver as npd


# noinspection PyUnresolvedReferences
class MainWindow(Qw.QMainWindow, Ui_MainWindow):
    config: cfg.Config = None
    processing: bool = False

    label_stats: Qw.QLabel

    toolBox_profile: pp.ProfileToolBox

    def __init__(self):
        Qw.QMainWindow.__init__(self)
        self.setupUi(self)
        self.setWindowTitle(f"{__display_name__} {__version__}")
        self.setWindowIcon(Qg.QIcon(":/logo-tiny.png"))
        self.processing = False

        self.config = cfg.load_config()

        self.initialize_ui()

    def initialize_ui(self):
        self.hide_progress()
        self.set_up_statusbar()
        self.initialize_profiles()
        self.initialize_analytics_view()

        # Allow the table to accept file drops and hide the PATH column.
        self.file_table.setAcceptDrops(True)
        self.file_table.setColumnHidden(Column.PATH, True)
        self.file_table.setColumnWidth(Column.FILENAME, 200)
        self.file_table.setColumnWidth(Column.SIZE, 100)
        self.frame_greeter.drop_signal.connect(self.file_table.dropEvent)
        self.file_table.table_is_empty.connect(lambda: self.stackedWidget.setCurrentIndex(0))
        self.file_table.table_not_empty.connect(lambda: self.stackedWidget.setCurrentIndex(1))
        # Hide the close button for the file table tab.
        self.image_tab.tabBar().setTabButton(0, Qw.QTabBar.RightSide, None)
        # Display a theme icon on the left side of the tab.
        self.image_tab.tabBar().setTabIcon(0, Qg.QIcon.fromTheme("view-form"))

        # Connect signals.
        self.comboBox_current_profile.hookedCurrentIndexChanged.connect(self.change_current_profile)
        self.action_add_files.triggered.connect(self.file_table.browse_add_files)
        self.action_add_folders.triggered.connect(self.file_table.browse_add_folders)



        )
        )




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


    def initialize_analytics_view(self):
        """
        Set up the text edit for analytics.
        """
        # Set the font to monospace, using the included font.
        # The font is stored in the data module. Noto Mono is a free font.
        # Load it from file to be cross platform.
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

            self.toolBox_profile.reset_all()  # To suppress the change check.
            self.comboBox_current_profile.removeItem(self.comboBox_current_profile.currentIndex())
            for action in self.menu_set_default_profile.actions():
                if action.text() == profile_name:
                    self.menu_set_default_profile.removeAction(action)
                    break

    def load_current_profile(self):
        """
        Load the current profile.
        """
        logger.debug("Loading current profile.")
        self.toolBox_profile.set_profile_values(self.config.current_profile)

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
        self.pushButton_save_profile.setEnabled(dirty)
        self.pushButton_reset_profile.setEnabled(dirty)
        self.action_save_profile.setEnabled(dirty)

    def reset_profile(self):
        """
        Reset the current profile.
        """
        self.toolBox_profile.reset_all()
        self.handle_profile_values_changed()

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

    def get_new_profile_path(
        self, show_protection_hint: bool = False
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

    def hide_progress(self):
        self.widget_progress_drawer.hide()

    def show_progress(self):
        self.widget_progress_drawer.show()


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
