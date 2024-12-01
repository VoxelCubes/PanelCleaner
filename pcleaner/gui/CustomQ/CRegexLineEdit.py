import re
import PySide6.QtGui as Qg
import PySide6.QtWidgets as Qw
from PySide6.QtCore import Signal


class RegexLineEdit(Qw.QWidget):
    """
    A little line edit combined with an indicator icon to show if the regex is valid or not.
    """

    def __init__(self):
        super().__init__()

        main_layout = Qw.QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)

        line_edit_layout = Qw.QHBoxLayout()
        self.line_edit = Qw.QLineEdit()
        self.line_edit.textChanged.connect(self.validate_regex)
        line_edit_layout.addWidget(self.line_edit)

        self.error_icon = Qw.QLabel()
        success_icon = Qg.QIcon.fromTheme("data-success")
        if not success_icon.isNull():
            self.error_icon.setPixmap(success_icon.pixmap(20, 20))  # Initially success icon
        self.error_icon.setToolTip("Regex is valid")
        line_edit_layout.addWidget(self.error_icon)
        line_edit_layout.setStretch(0, 1)  # Make the line edit stretchable
        line_edit_layout.setStretch(1, 0)  # Error icon should not stretch

        main_layout.addLayout(line_edit_layout)

        self.setLayout(main_layout)

    def validate_regex(self, text):
        try:
            re.compile(text)
            # Set success icon and tooltip
            success_icon = Qg.QIcon.fromTheme("data-success")
            if not success_icon.isNull():
                self.error_icon.setPixmap(success_icon.pixmap(20, 20))
            self.error_icon.setToolTip(self.tr("Regex is valid"))
        except re.error as e:
            # Set error icon from the theme and tooltip
            error_icon = Qg.QIcon.fromTheme("data-error")
            if not error_icon.isNull():
                self.error_icon.setPixmap(error_icon.pixmap(20, 20))
            self.error_icon.setToolTip(f"Regex Error: {e.msg}")

    def setRegex(self, text):
        self.line_edit.setText(text)

    def regex(self):
        return self.line_edit.text()

    @property
    def textChanged(self) -> Signal:
        return self.line_edit.textChanged

    def setClearButtonEnabled(self, enabled: bool):
        self.line_edit.setClearButtonEnabled(enabled)

    def setPlaceholderText(self, text: str):
        self.line_edit.setPlaceholderText(text)

    @property
    def textEdited(self):
        return self.line_edit.textEdited

    def text(self):
        return self.line_edit.text()

    def setText(self, text: str):
        self.line_edit.setText(text)

    def setRegexEnabled(self, enabled: bool):
        self.error_icon.setVisible(enabled)
