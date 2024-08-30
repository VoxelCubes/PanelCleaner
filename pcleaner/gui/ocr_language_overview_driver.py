from enum import IntEnum

import PySide6.QtCore as Qc
import PySide6.QtGui as Qg
import PySide6.QtWidgets as Qw
from loguru import logger

import pcleaner.gui.state_saver as ss
import pcleaner.ocr.supported_languages as osl
from pcleaner.gui.ui_generated_files.ui_OCRLanguageSupport import Ui_OCRLanguageSupport
from pcleaner.helpers import tr
from pcleaner.ocr import ocr


class Column(IntEnum):
    CODE = 0
    LANGUAGE = 1
    MANGAOCR = 2
    TESSERACT = 3


class OCRLanguageSupport(Qw.QDialog, Ui_OCRLanguageSupport):
    """
    Display the current state of OCR language support.
    """

    state_saver: ss.StateSaver  # The state saver for the window.

    def __init__(
        self,
        parent=None,
    ):
        """
        Init the widget.

        :param parent: The parent widget.
        """
        logger.info(f"Opening the OCR Language Support dialog.")
        Qw.QDialog.__init__(self, parent)
        self.setupUi(self)

        self.populate_table()

        # Connect the buttons.
        self.pushButton_install_tesseract.clicked.connect(self.open_tesseract_installation)
        self.pushButton_install_tesseract_language_packs.clicked.connect(
            self.open_tesseract_langs_installation
        )

        self.state_saver = ss.StateSaver("ocr_language_support")
        self.init_state_saver()
        self.state_saver.restore()

    def closeEvent(self, event: Qg.QCloseEvent) -> None:
        """
        Called when the window is closed.
        """
        self.state_saver.save()
        event.accept()

    def init_state_saver(self) -> None:
        """
        Load the state from the state saver.
        """
        self.state_saver.register(
            self,
            self.lang_table,
        )

    def populate_table(self):
        # I tried to make the columns sortable, so that you could figure out what all
        # the languages are, that something like tesseract currently supports,
        # but item delegates were not only a pain in the ass, but didn't work either.
        # Trying to use a label with text and making said text invisible also wouldn't
        # work with the icons.

        manga_ocr_langs = ocr.MangaOcr.langs()
        tesseract_langs = ocr.TesseractOcr.langs()

        if tesseract_langs:
            self.pushButton_install_tesseract.hide()

        for code, lang in osl.language_code_name_sorted(
            include_detect=False, pin_important=True, translate=tr
        ):
            if code in (osl.LanguageCode.detect_box, osl.LanguageCode.detect_page):
                continue
            self.lang_table.appendRow(str(code), tr(lang))

            row = self.lang_table.rowCount() - 1
            if code in manga_ocr_langs:
                self.lang_table.setCellWidget(
                    row, Column.MANGAOCR, IconWidget(Qg.QIcon.fromTheme("dialog-ok"))
                )

            if code in tesseract_langs:
                self.lang_table.setCellWidget(
                    row, Column.TESSERACT, IconWidget(Qg.QIcon.fromTheme("dialog-ok"))
                )

        self.lang_table.resizeColumnsToContents()

    @staticmethod
    def open_tesseract_installation():
        """
        Open the online documentation in the default browser.
        """
        logger.debug("Opening online documentation for Tesseract installation.")
        Qg.QDesktopServices.openUrl(
            Qc.QUrl("https://github.com/VoxelCubes/PanelCleaner?tab=readme-ov-file#ocr")
        )

    @staticmethod
    def open_tesseract_langs_installation():
        """
        Open the online documentation in the default browser.
        """
        logger.debug("Opening online documentation for Tesseract language pack installation.")
        Qg.QDesktopServices.openUrl(
            Qc.QUrl("https://ocrmypdf.readthedocs.io/en/latest/languages.html")
        )


class IconWidget(Qw.QWidget):
    def __init__(self, icon, parent=None):
        super().__init__(parent)
        layout = Qw.QHBoxLayout()
        label = Qw.QLabel()
        label.setPixmap(icon.pixmap(22, 22))  # Adjust size as necessary
        layout.addWidget(label)
        layout.setAlignment(label, Qc.Qt.AlignCenter)  # Center the QLabel
        layout.setContentsMargins(0, 0, 0, 0)  # Remove margins
        self.setLayout(layout)
