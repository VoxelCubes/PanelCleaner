import PySide6.QtWidgets as Qw
from PySide6.QtCore import Qt
import PySide6.QtGui as Qg


# noinspection PyPep8Naming
class CTextEdit(Qw.QTextEdit):
    """
    A QTextEdit with a few extra features.
    - A context menu option to clear the text.
    """

    def __init__(self, parent=None) -> None:
        Qw.QTextEdit.__init__(self, parent)

        # Create a custom action for clearing the text
        self.clear_action = Qg.QAction(self.tr("Clear"), self)
        self.clear_action.setShortcut(Qg.QKeySequence("Ctrl+L"))
        self.clear_action.setIcon(Qg.QIcon.fromTheme("edit-clear-history"))
        self.clear_action.triggered.connect(self.clear)

        # Create a shortcut for the clear action
        self.clear_shortcut = Qg.QShortcut(Qg.QKeySequence("Ctrl+L"), self)
        self.clear_shortcut.setContext(Qt.WidgetWithChildrenShortcut)
        self.clear_shortcut.activated.connect(self.clear)

    def contextMenuEvent(self, event):
        menu = self.createStandardContextMenu()

        menu.addAction(self.clear_action)

        # If the text is empty, disable the clear action.
        self.clear_action.setEnabled(bool(self.toPlainText()))

        menu.exec_(event.globalPos())
