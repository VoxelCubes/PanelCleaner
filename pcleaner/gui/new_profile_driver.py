from pathlib import Path

import PySide6.QtGui as Qg
import PySide6.QtWidgets as Qw

import pcleaner.gui.gui_utils as gu
from pcleaner.gui.ui_generated_files.ui_NewProfile import Ui_NewProfile


class NewProfileDialog(Qw.QDialog, Ui_NewProfile):
    """
    The dialog for creating a new profile.
    It takes care of assigning a new file path.
    """

    default_path: Path
    protected_names: list[str]

    def __init__(
        self,
        default_path: Path,
        show_protection_hint: bool,
        protected_names: list[str],
    ) -> None:
        """
        Initialize the dialog.

        :param default_path: The default path to display.
        :param show_protection_hint: When true, show a hint about not being able to overwrite the default profile.
        :param protected_names: A list of names that are protected and cannot be used,
            as they are used for builtin profiles.
        """
        # For some reason, it doesn't want parent.
        Qw.QDialog.__init__(self)
        self.setupUi(self)

        self.default_path = default_path
        self.label_default_path.setText(str(self.default_path))
        self.protected_names = protected_names

        self.setWindowIcon(gu.load_custom_icon("logo-tiny"))

        # Ensure that the default path exists.
        self.default_path.mkdir(parents=True, exist_ok=True)

        self.label_warning_icon.setPixmap(Qg.QIcon.fromTheme("data-error").pixmap(16, 16))
        self.label_default_protection_hint.setVisible(show_protection_hint)

        self.validate()
        self.lineEdit_name.textChanged.connect(self.validate)
        self.lineEdit_location.textChanged.connect(self.validate)

        self.pushButton_browse_location.clicked.connect(self.browse_location)

        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)

    def get_name(self) -> str:
        """
        Return the name of the new profile.

        :return: The name of the new profile.
        """
        return self.lineEdit_name.text().strip()

    def get_directory(self) -> Path:
        """
        Return the directory of the new profile.

        :return: The directory of the new profile.
        """
        return (
            self.default_path
            if self.radioButton_default_location.isChecked()
            else Path(self.lineEdit_location.text())
        )

    def get_save_path(self) -> Path:
        """
        Return the path where the new profile should be saved.

        :return: The path where the new profile should be saved.
        """
        return (self.get_directory() / self.get_name()).with_suffix(".conf")

    def browse_location(self) -> None:
        """
        Let the user choose a custom location. Only directories are allowed.
        """
        dialog = Qw.QFileDialog(self)
        dialog.setFileMode(Qw.QFileDialog.Directory)
        dialog.setOption(Qw.QFileDialog.ShowDirsOnly, True)
        dialog.setDirectory(str(self.default_path))

        if dialog.exec():
            self.lineEdit_location.setText(dialog.selectedFiles()[0])

    def validate(self) -> None:
        """
        Check if the current input is acceptable, and show warnings if not.
        """
        name = self.get_name()
        prospective_dir = self.get_directory()

        if not name:
            self.label_warning_message.setText("Please enter a name.")
            self.label_warning_message.show()
            self.label_warning_icon.hide()
            self.buttonBox.button(Qw.QDialogButtonBox.Save).setEnabled(False)
        elif name.lower() in self.protected_names:
            self.label_warning_message.setText("This name is used by a builtin profile.")
            self.label_warning_message.show()
            self.label_warning_icon.show()
            self.buttonBox.button(Qw.QDialogButtonBox.Save).setEnabled(False)
        elif (prospective_dir / name).with_suffix(".conf").exists():
            self.label_warning_message.setText("A profile with this name already exists.")
            self.label_warning_message.show()
            self.label_warning_icon.show()
            self.buttonBox.button(Qw.QDialogButtonBox.Save).setEnabled(False)
        else:
            self.label_warning_message.hide()
            self.label_warning_icon.hide()
            self.buttonBox.button(Qw.QDialogButtonBox.Save).setEnabled(True)

        if not prospective_dir.is_dir():
            self.label_warning_message.setText("The selected directory does not exist.")
            self.label_warning_message.show()
            self.label_warning_icon.show()
            self.buttonBox.button(Qw.QDialogButtonBox.Save).setEnabled(False)
