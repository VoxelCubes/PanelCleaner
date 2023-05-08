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
    # glossary: st.Glossary = None
    processing: bool = False

    # text_params_changed = Signal(st.Glossary)
    # text_output_changed = Signal()
    # abort_translation_worker = Signal()

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
        #
        # self.threadpool = Qc.QThreadPool.globalInstance()
        # logger.info(f"Multithreading with maximum {self.threadpool.maxThreadCount()} threads")
        #
        # self.config = cfg.Config.load()
        # # Set debug flag.
        # self.config.tl_mock = mock
        #
        # logger.debug(f"Loaded config: {self.config.safe_dump()}")
        # self.load_config_to_ui()
        # # Share config with the file table.
        # self.file_table.set_config(self.config)
        #
        # self.load_glossary()

    def initialize_ui(self):
        self.hide_progress()
        self.start_button_enabled(False)
        self.show_button_start()
        # self.update_input_buttons()
        self.set_up_statusbar()
        self.initialize_profiles()
        self.initialize_analytics_view()

        # Allow the table to accept file drops and hide the ID column.
        self.file_table.setAcceptDrops(True)
        self.file_table.setColumnHidden(Column.ID, True)
        self.file_table.setColumnWidth(Column.FILENAME, 200)
        self.file_table.setColumnWidth(Column.STATUS, 200)

        # Connect signals.
        self.connect_combobox_slots()
        self.comboBox_current_profile.hookedCurrentIndexChanged.connect(self.change_current_profile)

        return

        self.checkBox_file_fixed_dir.toggled.connect(self.fixed_output_dir_toggled)
        self.checkBox_use_glossary.toggled.connect(self.use_glossary_toggled)
        self.checkBox_extra_quote_protection.toggled.connect(self.extra_quote_protection_toggled)
        self.pushButton_file_dir_browse.clicked.connect(self.browse_file_out_dir)
        self.lineEdit_file_out_dir.textEdited.connect(partial(self.fixed_file_out_updated, False))
        self.lineEdit_file_out_dir.editingFinished.connect(
            partial(self.fixed_file_out_updated, True)
        )

        self.pushButton_glossary_file_browse.clicked.connect(self.browse_glossary_file)
        self.lineEdit_glossary_file.textEdited.connect(
            partial(self.glossary_file_updated, self, False)
        )
        self.lineEdit_glossary_file.editingFinished.connect(
            partial(self.glossary_file_updated, self, True)
        )
        self.pushButton_glossary_help.clicked.connect(self.show_glossary_help)

        self.pushButton_api_config.clicked.connect(self.configure_api)
        self.pushButton_refresh.clicked.connect(self.load_config_to_ui)

        self.text_output_changed.connect(self.file_table.update_all_output_filenames)
        self.text_params_changed.connect(self.file_table.update_all_text_params)

        self.file_table.itemSelectionChanged.connect(self.update_input_buttons)
        self.pushButton_file_add.clicked.connect(self.file_table.browse_add_file)
        self.pushButton_file_preview.clicked.connect(self.file_table.preview_selected_file)
        self.pushButton_file_remove.clicked.connect(self.file_table.remove_selected_file)
        self.pushButton_file_remove_all.clicked.connect(self.file_table.remove_all_files)

        self.pushButton_start.clicked.connect(self.start_translating)
        self.pushButton_abort.clicked.connect(self.abort_translating)

        self.file_table.request_text_param_update.connect(self.update_file_table_params)
        self.file_table.ready_for_translation.connect(self.ready_to_translate)
        self.file_table.not_ready_for_translation.connect(self.not_ready_to_translate)
        self.file_table.statusbar_message.connect(self.statusbar.showMessage)
        self.file_table.recalculate_char_total.connect(self.recalculate_char_total)

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

    def connect_combobox_slots(self):
        """
        Connect the combobox slots.
        """
        # self.comboBox_lang_from.currentIndexChanged.connect(self.lang_from_updated)
        # self.comboBox_lang_to.currentIndexChanged.connect(self.lang_to_updated)
        pass

    def disconnect_combobox_slots(self):
        """
        Disconnect the combobox slots. This prevents erroneous signals from being sent during
        setup of new language options.
        """
        # self.comboBox_lang_from.currentIndexChanged.disconnect()
        # self.comboBox_lang_to.currentIndexChanged.disconnect()
        pass

    # """
    # Config interactions
    # """
    #
    # def load_config_to_ui(self):
    #     """
    #     Apply data from config to ui widgets.
    #     """
    #     logger.debug("Loading config to UI.")
    #
    #     self.checkBox_file_fixed_dir.setChecked(self.config.use_fixed_output_path)
    #     self.lineEdit_file_out_dir.setText(self.config.fixed_output_path)
    #
    #     self.lineEdit_glossary_file.setText(self.config.glossary_path)
    #     self.checkBox_use_glossary.setChecked(self.config.use_glossary)
    #     self.checkBox_extra_quote_protection.setChecked(self.config.use_quote_protection)
    #
    #     self.fixed_output_dir_enabled(self.config.use_fixed_output_path)
    #     self.glossary_enabled(self.config.use_glossary)
    #
    #     # Ignore the mock because it cannot give language options. It is only to be used for translation.
    #     translator = self.open_translator(use_mock=False)
    #
    #     self.show_api_status(translator is not None)
    #     self.update_current_usage(translator)
    #
    #     if translator is not None:
    #         # Disconnect the slots to prevent signals from being sent during setup of new language options.
    #         self.disconnect_combobox_slots()  # vvv
    #         # Load language options from API.
    #         self.comboBox_lang_from.clear()
    #         self.comboBox_lang_to.clear()
    #
    #         # Add automatic option.
    #         self.comboBox_lang_from.addTextItemLinkedData("Detect", "")
    #
    #         for lang in translator.get_source_languages():
    #             self.comboBox_lang_from.addTextItemLinkedData(lang.name, lang.code)
    #
    #         for lang in translator.get_target_languages():
    #             self.comboBox_lang_to.addTextItemLinkedData(lang.name, lang.code)
    #
    #         self.connect_combobox_slots()  # ^^^
    #
    #         # Try to select the configured languages.
    #         try:
    #             self.comboBox_lang_from.setCurrentIndexByLinkedData(self.config.lang_from)
    #         except ValueError:
    #             logger.debug(f"Configured lang_from '{self.config.lang_from}' not found")
    #
    #         try:
    #             self.comboBox_lang_to.setCurrentIndexByLinkedData(self.config.lang_to)
    #         except ValueError:
    #             logger.debug(f"Configured lang_to '{self.config.lang_to}' not found")
    #     else:
    #         self.statusbar.showMessage("Error connecting to the API.")
    #
    # def lang_from_updated(self):
    #     """
    #     Copy lang_from from the combobox into the config and save it.
    #     """
    #     self.config.lang_from = self.comboBox_lang_from.currentLinkedData()
    #     logger.debug(f"Saving lang_from: {self.config.lang_from}")
    #     self.config.save()
    #
    # def lang_to_updated(self):
    #     """
    #     Copy lang_to from the combobox into the config and save it.
    #     """
    #     self.config.lang_to = self.comboBox_lang_to.currentLinkedData()
    #     logger.debug(f"Saving lang_to: {self.config.lang_to}")
    #     self.text_output_changed.emit()
    #     self.config.save()
    #
    # def fixed_output_dir_toggled(self):
    #     """
    #     Enable or disable the fixed output directory checkbox and save it to the config.
    #     """
    #     self.config.use_fixed_output_path = self.checkBox_file_fixed_dir.isChecked()
    #     self.fixed_output_dir_enabled(self.config.use_fixed_output_path)
    #     self.text_output_changed.emit()
    #     self.config.save()
    #
    # def browse_file_out_dir(self):
    #     """
    #     Browse for a directory to save files to.
    #     """
    #     dir_path = Qw.QFileDialog.getExistingDirectory(
    #         self, "Select output directory", self.config.fixed_output_path
    #     )
    #     if dir_path:
    #         self.lineEdit_file_out_dir.setText(dir_path)
    #         self.config.fixed_output_path = dir_path
    #         self.text_output_changed.emit()
    #         self.config.save()
    #
    # def fixed_file_out_updated(self, save: bool, *_):
    #     """
    #     Copy fixed_file_out from the lineedit into the config and save it.
    #     Don't save until the line edit signals the end of editing.
    #     Throw away the text in the line edit that the signal passes along by using *_.
    #     This is because the signal for editing finished does not pass along the text,
    #     making it unreliable.
    #
    #     :param save: Whether to save the config.
    #     """
    #     self.config.fixed_output_path = self.lineEdit_file_out_dir.text()
    #     if save:
    #         self.config.save()
    #     self.text_output_changed.emit()
    #
    # def use_glossary_toggled(self):
    #     """
    #     Enable or disable the glossary checkbox and save it to the config.
    #     """
    #     self.config.use_glossary = self.checkBox_use_glossary.isChecked()
    #     self.glossary_enabled(self.config.use_glossary)
    #     self.config.save()
    #     if self.config.use_glossary:
    #         self.load_glossary()
    #     self.text_params_changed.emit(self.glossary)
    #
    # def browse_glossary_file(self):
    #     """
    #     Browse for a glossary file.
    #     Accepts whatever pyexcel can handle.
    #     """
    #     file_path = Qw.QFileDialog.getOpenFileName(
    #         self, "Select glossary file", self.config.glossary_path
    #     )
    #     if file_path:
    #         self.lineEdit_glossary_file.setText(file_path[0])
    #         self.config.glossary_path = file_path[0]
    #         self.config.save()
    #         self.load_glossary()
    #
    # def glossary_file_updated(self, save: bool, *_):
    #     """
    #     Copy glossary_file from the lineedit into the config and save it.
    #     Don't save until the line edit signals the end of editing.
    #     Throw away the text in the line edit that the signal passes along by using *_.
    #     This is because the signal for editing finished does not pass along the text,
    #     making it unreliable.
    #
    #     :param save: Whether to save the config.
    #     """
    #     self.config.glossary_path = self.lineEdit_glossary_file.text()
    #     if save:
    #         self.config.save()
    #         self.load_glossary()
    #
    # def extra_quote_protection_toggled(self):
    #     """
    #     Enable or disable the extra quote protection checkbox and save it to the config.
    #     """
    #     self.config.use_quote_protection = self.checkBox_extra_quote_protection.isChecked()
    #     self.config.save()
    #     self.text_params_changed.emit(self.glossary)
    #
    # """
    # Dialogs
    # """
    #
    # def configure_api(self):
    #     """
    #     Configure the DeepL API.
    #     """
    #     api_conf_dialog = ConfigureAccount(self, self.config)
    #     response = api_conf_dialog.exec()
    #     if response == Qw.QDialog.Accepted:
    #         # Adopt changes from the dialog.
    #         self.config.api_key = api_conf_dialog.lineEdit_api_key.text()
    #         self.config.save()
    #         self.load_config_to_ui()
    #
    # """
    # Misc helpers
    # """
    #
    # # def open_translator(self, use_mock: bool = True) -> deepl.Translator | None:
    # #     """
    # #     Open a translator instance.
    # #
    # #     :return: translator instance and whether it was successful
    # #     """
    # #
    # #     if self.config.api_key == "":
    # #         # Fail silently if no API key is set, since this is the default value.
    # #         logger.warning("No API key set")
    # #         return None
    # #     try:
    # #         if self.config.tl_mock and use_mock:
    # #             logger.info("Opening mock translator.")
    # #             return deepl.Translator(
    # #                 auth_key="1234567890",
    # #                 server_url="http://localhost:3000",
    # #             )
    # #         else:
    # #             logger.info("Opening translator.")
    # #             translator = deepl.Translator(auth_key=self.config.api_key)
    # #             # Test the api, since initialization doesn't mean success.
    # #             translator.get_source_languages()
    # #             return translator
    # #     except Exception as e:
    # #         show_warning(self, "API Error", f"Failed connect to DeepL API\n\n{e}")
    # #         return None
    #
    # def update_file_table_params(self):
    #     """
    #     Update the file table with the current parameters.
    #     """
    #     self.text_params_changed.emit(self.glossary)
    #
    def initialize_analytics_view(self):
        """
        Set up the text edit for analytics.
        """
        # Set the font to monospace, using the included font.
        # The font is stored in the data module. Noto Mono is a free font.
        # Load it from file to be cross platform.
        font_path = resources.path(data, "NotoMono-Regular.ttf")
        font_id = Qg.QFontDatabase.addApplicationFont(str(font_path))
        if font_id != -1:
            logger.info("Loaded included font")
        else:
            logger.error(f"Failed to load included font. Using backup monospace font")
        self.textEdit_analytics.setReadOnly(True)
        self.textEdit_analytics.setLineWrapMode(Qw.QTextEdit.NoWrap)

    """
    Profiles
    """

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

            self.add_new_profile_to_gui(profile_name, file_path)

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
        self.pushButton_apply_profile.setEnabled(dirty)
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
    Glossary
    """

    def load_glossary(self):
        """
        Open a glossary file and parse it.
        Afterwards, notify any files to apply it.
        """
        path = Path(self.config.glossary_path)

        if not path.is_file():
            logger.warning(f"Glossary file not found: {path}")
            self.statusbar.showMessage(f"Glossary file not found.", 10_000)
            return

        # Check if we haven't loaded the file before.
        if self.glossary.is_same_glossary(path):
            logger.info("Glossary file unchanged")
            return
        # Start the worker.
        self.glossary_worker_start(path)

    def glossary_worker_start(self, path: Path):
        """
        Initialize generic QRunner worker to load a glossary file.

        :param path: Path to the glossary file.
        """
        self.statusbar.showMessage("Loading glossary...")
        worker = wt.Worker(gl.parse_glossary, path=path, no_progress_callback=True)
        worker.signals.result.connect(self.glossary_worker_result)
        worker.signals.error.connect(self.glossary_worker_error)
        logger.debug(f"Loading glossary from {path}")
        # Execute.
        self.threadpool.start(worker)

    # def glossary_worker_result(self, glossary: st.Glossary):
    #     """
    #     Notify any files to apply the glossary.
    #
    #     :param glossary: The glossary received from the worker.
    #     """
    #     self.glossary = glossary
    #     terms_found = len(glossary)
    #     self.statusbar.showMessage(
    #         f"Loaded {terms_found} {hp.f_plural(terms_found, 'term')} from glossary."
    #     )
    #     logger.info(f"Glossary loaded, {terms_found} {hp.f_plural(terms_found, 'term')} found.")
    #     logger.debug(f"Glossary dump: \n{glossary}")
    #     self.text_params_changed.emit(self.glossary)
    #
    # def glossary_worker_error(self, error: wt.WorkerError):
    #     """
    #     Notify the user of an error.
    #     """
    #     self.statusbar.showMessage(f"Error loading glossary.", 10_000)
    #     show_warning(self, "Glossary Error", f"Failed to open glossary file\n\n{error.value}")
    #     logger.error(f"Failed to open glossary file.\n{error}")
    #
    # """
    # Translation
    # """
    #
    # def start_translating(self):
    #     logger.info("Starting translation.")
    #     # Check if the API is ready.
    #     translator = self.open_translator()
    #     if translator is None:
    #         show_warning(
    #             self, "API Error", "Failed to open DeepL translator. Please check account settings."
    #         )
    #     if self.config.tl_mock:
    #         show_warning(
    #             self,
    #             "Mock Mode",
    #             "Translations are being performed with the mock translator.\nDo not expect accurate results.",
    #         )
    #     else:
    #         # Skip the char count warning when mocking because then we can't load usage stats and it doesn't matter.
    #         if not self.char_count_warning(translator):
    #             return
    #
    #     # Restrict user interaction.
    #     self.processing = True
    #     self.update_input_buttons()
    #     self.set_translation_parameters_enabled(False)
    #     self.abort_button_enabled(True)
    #     self.show_button_abort()
    #     self.progressBar.setValue(0)
    #     self.show_progress()
    #     self.label_progress.setText("Preparing...")
    #     self.statusbar.showMessage("Translating...")
    #
    #     # Send the data off to the worker.
    #     worker = ai.DeeplWorker(
    #         translator=translator, input_files=self.file_table.files, config=self.config
    #     )
    #     worker.signals.result.connect(self.translation_worker_result)
    #     worker.signals.progress.connect(self.translation_worker_progress)
    #     worker.signals.error.connect(self.translation_worker_error)
    #     self.abort_translation_worker.connect(worker.abort)
    #     self.threadpool.start(worker)
    #
    # def char_count_warning(self, translator: deepl.Translator) -> bool:
    #     # Make sure the user is aware of how many characters will be translated.
    #     # Check if the allotted character count won't exceed the quota.
    #     total_chars = sum(file.char_count for file in self.file_table.files.values())
    #     api_usage = translator.get_usage()
    #     allowed_chars = api_usage.character.limit - api_usage.character.count
    #     remaining_chars = allowed_chars - total_chars
    #     warning_msg = (
    #         f"You are about to translate {hp.format_char_count(total_chars)} "
    #         f"{hp.f_plural(total_chars, 'character')},\n"
    #         f"leaving you with {hp.format_char_count(remaining_chars)} "
    #         f"{hp.f_plural(remaining_chars, 'character')}."
    #         f"\nProceed?"
    #     )
    #     if api_usage.character.limit_reached:
    #         warning_msg = "You have reached your character limit.\nProceed anyway?"
    #     elif total_chars > allowed_chars:
    #         warning_msg = (
    #             f"You are about to translate {hp.format_char_count(total_chars)} "
    #             f"{hp.f_plural(total_chars, 'character')}, "
    #             f"which exceeds your remaining character limit of {hp.format_char_count(allowed_chars)}.\nProceed anyway?"
    #         )
    #     # Ask the user if he wants to proceed, just in case.
    #     logger.info(f"Character limit warning: {warning_msg}")
    #     affirmation = show_question(self, "API Limit", warning_msg)
    #     if not affirmation:
    #         logger.info("Translation cancelled.")
    #         return False
    #     return True
    #
    # def translation_worker_result(self, exit_code: ai.State):
    #     """
    #     If we made it here, the translation was either successful or aborted.
    #     Notify the user, write the output, and reset the ui.
    #
    #     :param exit_code: The exit code of the translation.
    #     """
    #
    #     logger.info(f"Translation finished with exit code {exit_code}")
    #     self.text_output_changed.emit()
    #
    #     if exit_code == ai.State.DONE:
    #         self.statusbar.showMessage("Translation finished.")
    #         show_info(self, "Finished", "Translations successfully completed.")
    #         for file_id in self.file_table.files:
    #             self.write_output_file(file_id)
    #
    #     elif exit_code == ai.State.ABORTED:
    #         self.statusbar.showMessage("Translation aborted.")
    #         show_info(self, "Aborted", "Translation aborted.")
    #         if self.config.dump_on_abort:
    #             for file_id in self.file_table.files:
    #                 self.write_output_file(file_id)
    #
    #     elif exit_code == ai.State.QUOTA_EXCEEDED:
    #         self.statusbar.showMessage("API quota exceeded.")
    #         show_warning(
    #             self,
    #             "API Quota Exceeded",
    #             "The DeepL API quota has been exceeded.\nDumping output files.",
    #         )
    #         for file_id in self.file_table.files:
    #             self.write_output_file(file_id)
    #
    #     self.translation_worker_finished()
    #
    # def translation_worker_progress(
    #     self, key: str, message: str, processed_chars: int | None, total_chars: int | None
    # ):
    #     """
    #     Update the file with the key in the file table to display this message.
    #
    #     :param key: InputFile ID.
    #     :param message: Progress status.
    #     :param processed_chars: Number of characters processed.
    #     :param total_chars: Total number of characters to process.
    #     """
    #     logger.debug(f"Translation progress: {key} {message} {processed_chars} {total_chars}")
    #     self.file_table.show_file_progress(key, message)
    #     if processed_chars is not None and total_chars is not None:
    #         self.update_translation_status(processed_chars, total_chars)
    #
    # def translation_worker_error(self, error: wt.WorkerError):
    #     logger.error(f"Translation failed.\n{error}")
    #     self.statusbar.showMessage(f"Translation failed.")
    #     show_warning(self, "Translation Error", f"Translation failed.\n\n{error.value}")
    #     self.translation_worker_finished()
    #
    # def translation_worker_finished(self):
    #     """
    #     Update the UI to reflect the finished state.
    #     """
    #     self.processing = False
    #     self.update_input_buttons()
    #     self.set_translation_parameters_enabled(True)
    #     self.abort_button_enabled(False)
    #     self.show_button_start()
    #     self.hide_progress()
    #     self.config.save()  # Save the last average time/1000 characters.
    #     self.load_config_to_ui()
    #
    # def abort_translating(self):
    #     logger.info("Aborting translation.")
    #     self.abort_translation_worker.emit()
    #     self.statusbar.showMessage("Aborting translation...")
    #
    # def write_output_file(self, file_id: str):
    #     """
    #     Write the output file to disk.
    #     Check the type of the file (text or epub) and run the appropriate function.
    #
    #     :param file_id: InputFile ID.
    #     """
    #
    #     file = self.file_table.files[file_id]
    #     try:
    #         if isinstance(file, st.TextFile):
    #             self.write_output_text_file(file_id)
    #         elif isinstance(file, st.EpubFile):
    #             self.write_output_epub_file(file_id)
    #         else:
    #             raise TypeError(f"Unknown file type: {file}")
    #
    #     except OSError as e:
    #         path_out = make_output_filename(file, self.config)
    #         logger.error(f"Failed to write translation to {path_out}.\n{e}\n\n")
    #         show_warning(
    #             self,
    #             "Output Error",
    #             f"Failed to write translation to {path_out}.\n\n{e}\n\n"
    #             f"Please make sure you have write permissions to the output directory.\n"
    #             f"To save the translation in another location without needing to re-translate, "
    #             f'select your file, then click the "preview" button.\n'
    #             f'There, select the translated version and press the "Save Preview to File" button.',
    #         )
    #         self.file_table.show_file_progress(file_id, "Could not write output!")
    #
    # def write_output_text_file(self, file_id: str):
    #     """
    #     Write the translation of a file to the assigned output path.
    #
    #     Check the status of the file. We decide 3 cases:
    #     1. File is not translated.
    #        - Skip this file.
    #     2. File is translated.
    #        - Write the translation to the output path.
    #     3. File is partially translated.
    #        - Dump the translation to the output path, if so configured.
    #
    #     :param file_id: InputFile ID.
    #     """
    #     file = self.file_table.files[file_id]
    #     text_out = file.get_translated_text()
    #     path_out = make_output_filename(file, self.config)
    #
    #     if text_out is None:  # Case 1.
    #         logger.info(f"Skipping file {file_id} because it has not been translated.")
    #         self.file_table.show_file_progress(file_id, "Not translated.")
    #         return
    #     else:
    #         # Ensure the output directory exists.
    #         path_out.parent.mkdir(parents=True, exist_ok=True)
    #
    #         with open(path_out, "w", encoding="utf-8") as f:
    #             f.write(text_out)
    #             logger.info(f"Wrote translation to {path_out}")
    #             if file.translation_incomplete():
    #                 self.file_table.show_file_progress(file_id, "Incomplete output written.")
    #             else:
    #                 self.file_table.show_file_progress(file_id, "Translation written.")
    #
    # def write_output_epub_file(self, file_id: str):
    #     """
    #     Write the translation of a file to the assigned output path.
    #
    #     Check the status of the file. We decide 3 cases:
    #     1. File is not translated.
    #        - Skip this file.
    #     2. File is translated.
    #        - Write the translation to the output path.
    #     3. File is partially translated.
    #        - Dump the translation to the output path, if so configured.
    #
    #     :param file_id: InputFile ID.
    #     """
    #     file: st.EpubFile = self.file_table.files[file_id]
    #     path_out = make_output_filename(file, self.config)
    #
    #     if not file.translation_incomplete() and not file.is_translated():
    #         # Skip this because we have nothing to dump.
    #         logger.info(f"Skipping file {file_id} because nothing has been translated.")
    #         self.file_table.show_file_progress(file_id, "Not translated.")
    #         return
    #
    #     file.write(st.ProcessLevel.TRANSLATED, path_out)

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

    def fixed_output_dir_enabled(self, enabled: bool):
        self.lineEdit_file_out_dir.setEnabled(enabled)
        self.pushButton_file_dir_browse.setEnabled(enabled)

    def glossary_enabled(self, enabled: bool):
        self.lineEdit_glossary_file.setEnabled(enabled)
        self.pushButton_glossary_file_browse.setEnabled(enabled)

    def start_button_enabled(self, enabled: bool):
        self.pushButton_start.setEnabled(enabled)

    def abort_button_enabled(self, enabled: bool):
        self.pushButton_abort.setEnabled(enabled)

    def show_button_start(self):
        self.pushButton_start.show()
        self.pushButton_abort.hide()

    def show_button_abort(self):
        self.pushButton_start.hide()
        self.pushButton_abort.show()

    def show_api_status(self, good: bool):
        self.label_api_status_good.setVisible(good)
        self.label_api_status_good_icon.setVisible(good)
        self.label_api_status_bad.setVisible(not good)
        self.label_api_status_bad_icon.setVisible(not good)

    # def update_input_buttons(self):
    #     logger.debug("Updating input buttons")
    #
    #     if self.processing:
    #         self.action_Open_Files.setEnabled(False)
    #         self.action_Clear_Files.setEnabled(False)
    #     else:
    #         self.action_Open_Files.setEnabled(True)
    #         self.action_Clear_Files.setEnabled(self.file_table.rowCount() > 0)
    #
    # def update_current_usage(self, translator: deepl.Translator | None):
    #     if translator is None:
    #         self.label_api_usage.setText("—")
    #         self.label_api_usage_warn_icon.hide()
    #         self.label_api_usage_error_icon.hide()
    #         return
    #
    #     usage = translator.get_usage()
    #     count = usage.character.count
    #     limit = usage.character.limit
    #     percentage = count / limit * 100  # Output with 2 decimals.
    #
    #     count_str = hp.format_char_count(count)
    #     limit_str = hp.format_char_count(limit)
    #
    #     self.label_api_usage.setText(f"{percentage:.2f}%  {count_str} / {limit_str} characters")
    #
    #     if percentage < 90:
    #         self.label_api_usage_warn_icon.hide()
    #         self.label_api_usage_error_icon.hide()
    #     elif percentage < 100:
    #         self.label_api_usage_warn_icon.show()
    #         self.label_api_usage_error_icon.hide()
    #     else:
    #         self.label_api_usage_warn_icon.hide()
    #         self.label_api_usage_error_icon.show()
    #
    # def ready_to_translate(self):
    #     logger.info("Ready to translate.")
    #     if self.threadpool.activeThreadCount() > 0:
    #         logger.error("Threadpool still has active threads.")
    #     self.start_button_enabled(True)
    #     self.show_button_start()
    #     self.statusbar.showMessage("Ready to translate.")
    #
    # def not_ready_to_translate(self):
    #     logger.info("Not ready to translate.")
    #     self.start_button_enabled(False)
    #     self.show_button_start()
    #
    # def set_translation_parameters_enabled(self, enabled: bool):
    #     """
    #     When processing, language, output, glossary, and account settings must all be locked.
    #
    #     :param enabled: Sets the enabled flag for all relevant widgets accordingly.
    #     """
    #     self.groupBox_language.setEnabled(enabled)
    #     self.groupBox_glossary.setEnabled(enabled)
    #     self.groupBox_api.setEnabled(enabled)
    #     self.checkBox_file_fixed_dir.setEnabled(enabled)
    #     self.lineEdit_file_out_dir.setEnabled(enabled)
    #     self.pushButton_file_dir_browse.setEnabled(enabled)
    #
    # def recalculate_char_total(self):
    #     """
    #     Calculate a new total of characters to translate and display it in the status bar.
    #     """
    #     char_total = sum(file.char_count for file in self.file_table.files.values())
    #     if char_total == 0:
    #         self.label_stats.setText("")
    #         return
    #
    #     time_total = ceil(self.config.avg_time_per_mille * char_total / 1000)
    #     char_text = hp.format_char_count(char_total) + hp.f_plural(char_total, " character")
    #     time_text = f"Approx. {hp.f_time(time_total)}"
    #     self.label_stats.setText(char_text + "   " + time_text)
    #
    # def update_translation_status(self, processed_chars: int, char_total: int):
    #     """
    #     Update the translation status label.
    #     """
    #     if char_total == 0:
    #         logger.info("Total character count is 0. Nothing to do.")
    #         return
    #     char_text = hp.format_char_count(processed_chars) + " / " + hp.format_char_count(char_total)
    #     time_total = ceil(self.config.avg_time_per_mille * (char_total - processed_chars) / 1000)
    #     self.label_progress.setText(
    #         f"Translated {char_text} {hp.f_plural(char_total, 'character')}\n"
    #         f"Approximately {hp.f_time(time_total)} remaining"
    #     )
    #     self.progressBar.setValue(processed_chars / char_total * 100)
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
