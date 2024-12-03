import platform
from pathlib import Path
from functools import wraps

import PySide6.QtGui as Qg
import PySide6.QtWidgets as Qw
from loguru import logger

import pcleaner.config as cfg
import pcleaner.gui.state_saver as ss
from pcleaner.gui.ui_generated_files.ui_PostActionConfiguration import Ui_PostActionConfiguration

SHUTDOWN_COMMAND_NAME = "SHUTDOWN"


def defer_button_update(method):
    @wraps(method)
    def wrapper(self, *args, **kwargs):
        self.disable_button_check = True
        result = method(self, *args, **kwargs)
        self.disable_button_check = False
        self.update_button_enabled()
        return result

    return wrapper


class PostActionConfiguration(Qw.QDialog, Ui_PostActionConfiguration):
    """
    The post action configuration dialog.
    """

    config: cfg.Config
    disable_button_check: bool

    state_saver: ss.StateSaver  # The state saver for the window.

    def __init__(
        self,
        parent=None,
        config: cfg.Config = None,
    ) -> None:
        """
        Init the widget.

        :param parent: The parent widget.
        """
        Qw.QDialog.__init__(self, parent)
        self.setupUi(self)

        self.config = config
        self.disable_button_check = False

        self.checkBox_remember_action.setChecked(config.pa_remember_action)
        self.checkBox_cancel_on_error.setChecked(config.pa_cancel_on_error)
        self.spinBox_wait_time.setValue(config.pa_wait_time)
        self.lineEdit_shutdown.setText(config.pa_shutdown_command or "")
        self.lineEdit_shutdown.setPlaceholderText(shut_down_command())

        for name, command in config.pa_custom_commands.items():
            self.tableWidget_commands.appendRow(name, command)

        self.pushButton_new.clicked.connect(
            lambda: self.tableWidget_commands.appendRow("", "", select_new=True)
        )
        self.pushButton_delete.clicked.connect(self.delete_command)
        self.pushButton_row_up.clicked.connect(self.move_row_up)
        self.pushButton_row_down.clicked.connect(self.move_row_down)
        self.tableWidget_commands.currentRowChanged.connect(self.update_button_enabled)
        self.tableWidget_commands.cellChanged.connect(self.update_button_enabled)

        self.label_warning.hide()
        self.label_warning_icon.hide()
        self.label_warning_icon.setPixmap(Qg.QIcon.fromTheme("data-warning").pixmap(16, 16))

        self.update_button_enabled()

        self.state_saver = ss.StateSaver("post_action_config")
        self.init_state_saver()
        self.state_saver.restore()

    def init_state_saver(self) -> None:
        """
        Load the state from the state saver.
        """
        self.state_saver.register(
            self,
            self.tableWidget_commands,
        )

    def closeEvent(self, event: Qg.QCloseEvent) -> None:
        self.state_saver.save()
        event.accept()

    def delete_command(self) -> None:
        """
        Delete the selected command.
        """
        row = self.tableWidget_commands.currentRow()
        if row == -1:
            return
        self.tableWidget_commands.removeRow(row)
        self.update_button_enabled()

    @defer_button_update
    def move_row_up(self) -> None:
        row = self.tableWidget_commands.currentRow()
        if row == -1:
            return
        self.tableWidget_commands.moveRowUp(row)

    @defer_button_update
    def move_row_down(self) -> None:
        row = self.tableWidget_commands.currentRow()
        if row == -1:
            return
        self.tableWidget_commands.moveRowDown(row)

    def update_button_enabled(self) -> None:
        """
        Update the enabled state of the buttons.
        """
        if self.disable_button_check:
            return
        row = self.tableWidget_commands.currentRow()
        self.pushButton_delete.setEnabled(row != -1)
        self.pushButton_row_up.setEnabled(row > 0)
        self.pushButton_row_down.setEnabled(
            row != -1 and row < self.tableWidget_commands.rowCount() - 1
        )
        self.buttonBox.button(Qw.QDialogButtonBox.Ok).setEnabled(self.commands_valid())

    def commands_valid(self) -> bool:
        """
        Check if the commands are valid. All we care about is that the names are not empty
        and unique.
        """
        names = set()
        for row in range(self.tableWidget_commands.rowCount()):
            name = self.tableWidget_commands.item(row, 0).text()
            if not name:
                self.label_warning.setText(self.tr("Action names cannot be empty."))
                self.label_warning.show()
                self.label_warning_icon.show()
                return False
            if name in names:
                self.label_warning.setText(self.tr("Action names must be unique."))
                self.label_warning.show()
                self.label_warning_icon.show()
                return False
            if name == SHUTDOWN_COMMAND_NAME:
                self.label_warning.setText(
                    self.tr('The name "{shutdown_command}" is reserved.').format(
                        shutdown_command=SHUTDOWN_COMMAND_NAME
                    )
                )
                self.label_warning.show()
                self.label_warning_icon.show()
                return False
            # Make sure this isn't the flatpak version:
            if Path("/.flatpak-info").exists():
                self.label_warning.setText(
                    self.tr("The Flatpak sandbox will likely prevent actions from working.")
                )
                self.label_warning.show()
                self.label_warning_icon.show()
                return False

            names.add(name)
        self.label_warning.setText("")
        self.label_warning.hide()
        self.label_warning_icon.hide()
        return True

    def accept(self):
        """
        Accept the dialog.
        """
        if not self.commands_valid():  # Just to be sure.
            return
        self.config.pa_remember_action = self.checkBox_remember_action.isChecked()
        self.config.pa_cancel_on_error = self.checkBox_cancel_on_error.isChecked()
        self.config.pa_wait_time = self.spinBox_wait_time.value()
        self.config.pa_shutdown_command = self.lineEdit_shutdown.text()

        self.config.pa_custom_commands = {
            self.tableWidget_commands.item(row, 0)
            .text(): self.tableWidget_commands.item(row, 1)
            .text()
            for row in range(self.tableWidget_commands.rowCount())
        }

        self.config.save()

        super().accept()


def shut_down_command() -> str:
    if platform.system() == "Windows":
        return "shutdown /s /t 0"
    else:  # Works on all Unix-like systems.
        return "shutdown -h now"
