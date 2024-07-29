import datetime

import PySide6
import PySide6.QtGui as Qg
import PySide6.QtWidgets as Qw
from PySide6.QtCore import Qt

import pcleaner.gui.license_driver as ld
import pcleaner.gui.gui_utils as gu
from pcleaner import __version__
from pcleaner.gui.ui_generated_files.ui_About import Ui_About


class AboutWidget(Qw.QWidget, Ui_About):
    """
    Displays the about information.
    """

    def __init__(
        self,
        parent: Qw.QWidget | None = None,
    ):
        """
        Initialize the widget.

        :param parent: The parent widget.
        """
        Qw.QWidget.__init__(self, parent)
        self.setupUi(self)
        self.setWindowFlag(Qt.Window)
        self.setWindowIcon(gu.load_custom_icon("logo-tiny"))

        self.label_license.linkActivated.connect(self.open_license)

        copyright_str = f"© 2023"
        if (until := datetime.datetime.now().year) > 2023:
            copyright_str += f"–{until}"

        self.label_copyright.setText(copyright_str)

        self.label_version.setText(__version__)
        self.label_toolkit.setText(f"PySide (Qt) {PySide6.__version__}")

        self.label_logo.setPixmap(
            Qg.QPixmap(gu.custom_icon_path("logo")).scaledToWidth(200, mode=Qt.SmoothTransformation)
        )

    def open_license(self) -> None:
        """
        Open the license dialog.
        """
        license_widget = ld.LicenseDialog(self)
        license_widget.show()
