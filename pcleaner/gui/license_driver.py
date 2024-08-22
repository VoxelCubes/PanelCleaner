import PySide6.QtWidgets as Qw

from pcleaner.gui.ui_generated_files.ui_License import Ui_License
import pcleaner.gui.gui_utils as gu


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
        self.setWindowIcon(gu.load_custom_icon("logo-tiny"))
