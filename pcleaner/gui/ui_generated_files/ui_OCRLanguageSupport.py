# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'OCRLanguageSupport.ui'
##
## Created by: Qt User Interface Compiler version 6.8.2
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide6.QtCore import (QCoreApplication, QDate, QDateTime, QLocale,
    QMetaObject, QObject, QPoint, QRect,
    QSize, QTime, QUrl, Qt)
from PySide6.QtGui import (QBrush, QColor, QConicalGradient, QCursor,
    QFont, QFontDatabase, QGradient, QIcon,
    QImage, QKeySequence, QLinearGradient, QPainter,
    QPalette, QPixmap, QRadialGradient, QTransform)
from PySide6.QtWidgets import (QAbstractItemView, QApplication, QDialog, QFrame,
    QHBoxLayout, QHeaderView, QPushButton, QSizePolicy,
    QSpacerItem, QTableWidgetItem, QVBoxLayout, QWidget)

from pcleaner.gui.CustomQ.CTableWidget import CTableWidget

class Ui_OCRLanguageSupport(object):
    def setupUi(self, OCRLanguageSupport):
        if not OCRLanguageSupport.objectName():
            OCRLanguageSupport.setObjectName(u"OCRLanguageSupport")
        OCRLanguageSupport.resize(500, 720)
        self.verticalLayout = QVBoxLayout(OCRLanguageSupport)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.verticalLayout.setContentsMargins(1, 0, 1, -1)
        self.lang_table = CTableWidget(OCRLanguageSupport)
        if (self.lang_table.columnCount() < 4):
            self.lang_table.setColumnCount(4)
        __qtablewidgetitem = QTableWidgetItem()
        self.lang_table.setHorizontalHeaderItem(0, __qtablewidgetitem)
        __qtablewidgetitem1 = QTableWidgetItem()
        self.lang_table.setHorizontalHeaderItem(1, __qtablewidgetitem1)
        __qtablewidgetitem2 = QTableWidgetItem()
        self.lang_table.setHorizontalHeaderItem(2, __qtablewidgetitem2)
        __qtablewidgetitem3 = QTableWidgetItem()
        self.lang_table.setHorizontalHeaderItem(3, __qtablewidgetitem3)
        self.lang_table.setObjectName(u"lang_table")
        self.lang_table.setFocusPolicy(Qt.NoFocus)
        self.lang_table.setFrameShape(QFrame.NoFrame)
        self.lang_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.lang_table.setProperty(u"showDropIndicator", False)
        self.lang_table.setDragDropOverwriteMode(False)
        self.lang_table.setDragDropMode(QAbstractItemView.NoDragDrop)
        self.lang_table.setAlternatingRowColors(True)
        self.lang_table.setSelectionMode(QAbstractItemView.MultiSelection)
        self.lang_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.lang_table.setSortingEnabled(False)
        self.lang_table.setCornerButtonEnabled(False)
        self.lang_table.horizontalHeader().setVisible(True)
        self.lang_table.horizontalHeader().setMinimumSectionSize(80)
        self.lang_table.horizontalHeader().setHighlightSections(False)
        self.lang_table.verticalHeader().setVisible(False)
        self.lang_table.verticalHeader().setHighlightSections(False)

        self.verticalLayout.addWidget(self.lang_table)

        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.horizontalLayout.setContentsMargins(6, 6, -1, -1)
        self.pushButton_install_tesseract = QPushButton(OCRLanguageSupport)
        self.pushButton_install_tesseract.setObjectName(u"pushButton_install_tesseract")
        icon = QIcon()
        iconThemeName = u"internet-services"
        if QIcon.hasThemeIcon(iconThemeName):
            icon = QIcon.fromTheme(iconThemeName)
        else:
            icon.addFile(u".", QSize(), QIcon.Mode.Normal, QIcon.State.Off)

        self.pushButton_install_tesseract.setIcon(icon)

        self.horizontalLayout.addWidget(self.pushButton_install_tesseract)

        self.pushButton_install_tesseract_language_packs = QPushButton(OCRLanguageSupport)
        self.pushButton_install_tesseract_language_packs.setObjectName(u"pushButton_install_tesseract_language_packs")
        self.pushButton_install_tesseract_language_packs.setIcon(icon)

        self.horizontalLayout.addWidget(self.pushButton_install_tesseract_language_packs)

        self.horizontalSpacer = QSpacerItem(0, 0, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout.addItem(self.horizontalSpacer)


        self.verticalLayout.addLayout(self.horizontalLayout)


        self.retranslateUi(OCRLanguageSupport)

        QMetaObject.connectSlotsByName(OCRLanguageSupport)
    # setupUi

    def retranslateUi(self, OCRLanguageSupport):
        OCRLanguageSupport.setWindowTitle(QCoreApplication.translate("OCRLanguageSupport", u"OCR Language Support", None))
        ___qtablewidgetitem = self.lang_table.horizontalHeaderItem(0)
        ___qtablewidgetitem.setText(QCoreApplication.translate("OCRLanguageSupport", u"Code", None));
        ___qtablewidgetitem1 = self.lang_table.horizontalHeaderItem(1)
        ___qtablewidgetitem1.setText(QCoreApplication.translate("OCRLanguageSupport", u"Language", u"Can also call this statistics."));
        ___qtablewidgetitem2 = self.lang_table.horizontalHeaderItem(2)
        ___qtablewidgetitem2.setText(QCoreApplication.translate("OCRLanguageSupport", u"MangaOCR", None));
        ___qtablewidgetitem3 = self.lang_table.horizontalHeaderItem(3)
        ___qtablewidgetitem3.setText(QCoreApplication.translate("OCRLanguageSupport", u"Tesseract", None));
        self.pushButton_install_tesseract.setText(QCoreApplication.translate("OCRLanguageSupport", u"How to install Tesseract", None))
        self.pushButton_install_tesseract_language_packs.setText(QCoreApplication.translate("OCRLanguageSupport", u"How to install Tesseract language packs", None))
    # retranslateUi

