import PySide6.QtWidgets as Qw
import PySide6.QtGui as Qg
import PySide6.QtCore as Qc
from PySide6.QtCore import Qt


class CTooltipLabel(Qw.QLabel):
    """
    A label that displays a help-hint icon and shows a tooltip when clicked.
    This is to make little helper icons more consistent.
    """

    icon_name: str

    def __init__(self, parent=None, tooltip: str = "", icon_name: str = "help-hint") -> None:
        super(CTooltipLabel, self).__init__(parent)

        # Display the help-hint icon and no text.
        self.icon_name = icon_name
        self.load_icon()
        self.setText("")
        if tooltip:
            self.setToolTip(tooltip)

        # Make the label focusable to receive keyboard events
        self.setFocusPolicy(Qt.StrongFocus)

    def load_icon(self) -> None:
        """
        Load the display icon.
        """
        self.setPixmap(Qg.QIcon.fromTheme(self.icon_name).pixmap(16, 16))

    def setText(self, text: str) -> None:
        """
        Ignore all attempts to set the text.
        """
        pass

    def keyPressEvent(self, event) -> None:
        """
        Show tooltip when the Enter or Space key is pressed.
        """
        if event.key() in (Qt.Key_Return, Qt.Key_Space):
            # Showing tooltip at the center of the label when triggered by keyboard.
            self.showTooltipAtPosition(self.rect().center())

    def showTooltipAtPosition(self, pos: Qc.QPoint) -> None:
        """
        Show the tooltip at the given local position.
        """
        global_pos = self.mapToGlobal(pos)
        Qw.QToolTip.showText(global_pos, self.toolTip())
