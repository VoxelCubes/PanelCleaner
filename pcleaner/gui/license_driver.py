import PySide6.QtGui as Qg
import PySide6.QtWidgets as Qw

from pcleaner.gui.ui_generated_files.ui_License import Ui_License


class LicenseDialog(Qw.QDialog, Ui_License):
    """
    Displays the license.
    """

    def __init__(
        self,
        parent: Qw.QWidget | None = None,
    ):
        """
        Initialize the widget.

        :param parent: The parent widget.
        """
        Qw.QDialog.__init__(self, parent)
        self.setupUi(self)
        self.setWindowIcon(Qg.QIcon(":/logo-tiny.png"))
