# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'ImageMatchOverview.ui'
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
from PySide6.QtWidgets import (QAbstractButton, QAbstractItemView, QApplication, QDialog,
    QDialogButtonBox, QFrame, QHBoxLayout, QHeaderView,
    QLabel, QPushButton, QSizePolicy, QSpacerItem,
    QTableWidgetItem, QVBoxLayout, QWidget)

from pcleaner.gui.CustomQ.CTableWidget import CTableWidget

class Ui_ImageMatchOverview(object):
    def setupUi(self, ImageMatchOverview):
        if not ImageMatchOverview.objectName():
            ImageMatchOverview.setObjectName(u"ImageMatchOverview")
        ImageMatchOverview.resize(785, 620)
        self.verticalLayout = QVBoxLayout(ImageMatchOverview)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.verticalLayout.setContentsMargins(1, -1, 1, -1)
        self.verticalLayout_2 = QVBoxLayout()
        self.verticalLayout_2.setSpacing(12)
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.verticalLayout_2.setContentsMargins(6, 4, 6, 4)
        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.label_stats = QLabel(ImageMatchOverview)
        self.label_stats.setObjectName(u"label_stats")
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.label_stats.sizePolicy().hasHeightForWidth())
        self.label_stats.setSizePolicy(sizePolicy)
        self.label_stats.setText(u"<statistics>")

        self.horizontalLayout.addWidget(self.label_stats)

        self.label_warning_icon = QLabel(ImageMatchOverview)
        self.label_warning_icon.setObjectName(u"label_warning_icon")
        self.label_warning_icon.setText(u"<warning icon>")

        self.horizontalLayout.addWidget(self.label_warning_icon)

        self.label_warning = QLabel(ImageMatchOverview)
        self.label_warning.setObjectName(u"label_warning")
        self.label_warning.setText(u"<x pages of OCR data will be lost>")

        self.horizontalLayout.addWidget(self.label_warning)


        self.verticalLayout_2.addLayout(self.horizontalLayout)

        self.horizontalLayout_3 = QHBoxLayout()
        self.horizontalLayout_3.setObjectName(u"horizontalLayout_3")
        self.pushButton_deselect_all = QPushButton(ImageMatchOverview)
        self.pushButton_deselect_all.setObjectName(u"pushButton_deselect_all")

        self.horizontalLayout_3.addWidget(self.pushButton_deselect_all)

        self.pushButton_select_all = QPushButton(ImageMatchOverview)
        self.pushButton_select_all.setObjectName(u"pushButton_select_all")

        self.horizontalLayout_3.addWidget(self.pushButton_select_all)

        self.pushButton_deselect_new = QPushButton(ImageMatchOverview)
        self.pushButton_deselect_new.setObjectName(u"pushButton_deselect_new")
        sizePolicy1 = QSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        sizePolicy1.setHorizontalStretch(0)
        sizePolicy1.setVerticalStretch(0)
        sizePolicy1.setHeightForWidth(self.pushButton_deselect_new.sizePolicy().hasHeightForWidth())
        self.pushButton_deselect_new.setSizePolicy(sizePolicy1)

        self.horizontalLayout_3.addWidget(self.pushButton_deselect_new)

        self.horizontalSpacer = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_3.addItem(self.horizontalSpacer)


        self.verticalLayout_2.addLayout(self.horizontalLayout_3)


        self.verticalLayout.addLayout(self.verticalLayout_2)

        self.file_table = CTableWidget(ImageMatchOverview)
        if (self.file_table.columnCount() < 3):
            self.file_table.setColumnCount(3)
        __qtablewidgetitem = QTableWidgetItem()
        __qtablewidgetitem.setText(u"image_index");
        self.file_table.setHorizontalHeaderItem(0, __qtablewidgetitem)
        __qtablewidgetitem1 = QTableWidgetItem()
        self.file_table.setHorizontalHeaderItem(1, __qtablewidgetitem1)
        __qtablewidgetitem2 = QTableWidgetItem()
        self.file_table.setHorizontalHeaderItem(2, __qtablewidgetitem2)
        self.file_table.setObjectName(u"file_table")
        self.file_table.setFocusPolicy(Qt.NoFocus)
        self.file_table.setFrameShape(QFrame.NoFrame)
        self.file_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.file_table.setProperty(u"showDropIndicator", False)
        self.file_table.setDragDropOverwriteMode(False)
        self.file_table.setDragDropMode(QAbstractItemView.NoDragDrop)
        self.file_table.setAlternatingRowColors(True)
        self.file_table.setSelectionMode(QAbstractItemView.MultiSelection)
        self.file_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.file_table.setSortingEnabled(False)
        self.file_table.setCornerButtonEnabled(False)
        self.file_table.horizontalHeader().setVisible(True)
        self.file_table.horizontalHeader().setHighlightSections(False)
        self.file_table.verticalHeader().setVisible(False)
        self.file_table.verticalHeader().setHighlightSections(False)

        self.verticalLayout.addWidget(self.file_table)

        self.horizontalLayout_2 = QHBoxLayout()
        self.horizontalLayout_2.setObjectName(u"horizontalLayout_2")
        self.horizontalLayout_2.setContentsMargins(6, -1, 6, -1)
        self.buttonBox = QDialogButtonBox(ImageMatchOverview)
        self.buttonBox.setObjectName(u"buttonBox")
        self.buttonBox.setOrientation(Qt.Horizontal)
        self.buttonBox.setStandardButtons(QDialogButtonBox.Cancel|QDialogButtonBox.Ok)

        self.horizontalLayout_2.addWidget(self.buttonBox)


        self.verticalLayout.addLayout(self.horizontalLayout_2)


        self.retranslateUi(ImageMatchOverview)
        self.buttonBox.accepted.connect(ImageMatchOverview.accept)
        self.buttonBox.rejected.connect(ImageMatchOverview.reject)

        QMetaObject.connectSlotsByName(ImageMatchOverview)
    # setupUi

    def retranslateUi(self, ImageMatchOverview):
        ImageMatchOverview.setWindowTitle(QCoreApplication.translate("ImageMatchOverview", u"Image Selection", None))
        self.pushButton_deselect_all.setText(QCoreApplication.translate("ImageMatchOverview", u"Deselect All", None))
        self.pushButton_select_all.setText(QCoreApplication.translate("ImageMatchOverview", u"Select All", None))
        self.pushButton_deselect_new.setText(QCoreApplication.translate("ImageMatchOverview", u"Unselect images without matching OCR data", None))
        ___qtablewidgetitem = self.file_table.horizontalHeaderItem(1)
        ___qtablewidgetitem.setText(QCoreApplication.translate("ImageMatchOverview", u"Image File", None));
        ___qtablewidgetitem1 = self.file_table.horizontalHeaderItem(2)
        ___qtablewidgetitem1.setText(QCoreApplication.translate("ImageMatchOverview", u"OCR Data", u"Can also call this statistics."));
    # retranslateUi

