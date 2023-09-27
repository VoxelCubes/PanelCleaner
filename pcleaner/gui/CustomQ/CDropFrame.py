import PySide6.QtGui as Qg
import PySide6.QtWidgets as Qw
from PySide6.QtCore import Signal


# noinspection PyPep8Naming
class CDropFrame(Qw.QFrame):
    """
    Extends the functionality with custom helpers
    And includes a secondary array for data linked to each item
    """

    drop_signal = Signal(Qg.QDropEvent)

    def __init__(self, parent=None) -> None:
        Qw.QFrame.__init__(self, parent)
        self.setAcceptDrops(True)

    def dragEnterEvent(self, event: Qg.QDragEnterEvent) -> None:
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event: Qg.QDropEvent) -> None:
        self.drop_signal.emit(event)
