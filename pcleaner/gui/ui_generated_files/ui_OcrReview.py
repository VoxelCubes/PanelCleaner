# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'OcrReview.ui'
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
from PySide6.QtWidgets import (QAbstractItemView, QApplication, QComboBox, QDialog,
    QFrame, QHBoxLayout, QHeaderView, QLabel,
    QListView, QListWidget, QListWidgetItem, QPushButton,
    QSizePolicy, QSlider, QSpacerItem, QSplitter,
    QTableWidgetItem, QVBoxLayout, QWidget)

from pcleaner.gui.CustomQ.CComboBox import CComboBox
from pcleaner.gui.CustomQ.CElidedLabel import CElidedLabel
from pcleaner.gui.CustomQ.CTableWidget import CTableWidget
from pcleaner.gui.image_viewer import BubbleImageViewer

class Ui_OcrReview(object):
    def setupUi(self, OcrReview):
        if not OcrReview.objectName():
            OcrReview.setObjectName(u"OcrReview")
        OcrReview.resize(1400, 800)
        OcrReview.setWindowTitle(u"Review")
        OcrReview.setModal(True)
        self.verticalLayout_2 = QVBoxLayout(OcrReview)
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.verticalLayout_2.setContentsMargins(1, 1, 1, 1)
        self.splitter = QSplitter(OcrReview)
        self.splitter.setObjectName(u"splitter")
        self.splitter.setOrientation(Qt.Horizontal)
        self.layoutWidget1 = QWidget(self.splitter)
        self.layoutWidget1.setObjectName(u"layoutWidget1")
        self.verticalLayout_3 = QVBoxLayout(self.layoutWidget1)
        self.verticalLayout_3.setSpacing(6)
        self.verticalLayout_3.setObjectName(u"verticalLayout_3")
        self.verticalLayout_3.setContentsMargins(0, 0, 0, 0)
        self.horizontalLayout_2 = QHBoxLayout()
        self.horizontalLayout_2.setObjectName(u"horizontalLayout_2")
        self.horizontalLayout_2.setContentsMargins(6, 6, 6, 7)
        self.label_image_count = QLabel(self.layoutWidget1)
        self.label_image_count.setObjectName(u"label_image_count")
        self.label_image_count.setText(u"<image count>")

        self.horizontalLayout_2.addWidget(self.label_image_count)

        self.horizontalSpacer = QSpacerItem(0, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_2.addItem(self.horizontalSpacer)

        self.label = QLabel(self.layoutWidget1)
        self.label.setObjectName(u"label")

        self.horizontalLayout_2.addWidget(self.label)

        self.horizontalSlider_icon_size = QSlider(self.layoutWidget1)
        self.horizontalSlider_icon_size.setObjectName(u"horizontalSlider_icon_size")
        self.horizontalSlider_icon_size.setMinimum(1)
        self.horizontalSlider_icon_size.setMaximum(1000)
        self.horizontalSlider_icon_size.setOrientation(Qt.Horizontal)

        self.horizontalLayout_2.addWidget(self.horizontalSlider_icon_size)

        self.pushButton_prev = QPushButton(self.layoutWidget1)
        self.pushButton_prev.setObjectName(u"pushButton_prev")
        self.pushButton_prev.setText(u"")
        icon = QIcon()
        iconThemeName = u"arrow-left"
        if QIcon.hasThemeIcon(iconThemeName):
            icon = QIcon.fromTheme(iconThemeName)
        else:
            icon.addFile(u".", QSize(), QIcon.Mode.Normal, QIcon.State.Off)

        self.pushButton_prev.setIcon(icon)
        self.pushButton_prev.setFlat(True)

        self.horizontalLayout_2.addWidget(self.pushButton_prev)

        self.pushButton_next = QPushButton(self.layoutWidget1)
        self.pushButton_next.setObjectName(u"pushButton_next")
        self.pushButton_next.setText(u"")
        icon1 = QIcon()
        iconThemeName = u"arrow-right"
        if QIcon.hasThemeIcon(iconThemeName):
            icon1 = QIcon.fromTheme(iconThemeName)
        else:
            icon1.addFile(u".", QSize(), QIcon.Mode.Normal, QIcon.State.Off)

        self.pushButton_next.setIcon(icon1)
        self.pushButton_next.setFlat(True)

        self.horizontalLayout_2.addWidget(self.pushButton_next)

        self.horizontalLayout_2.setStretch(1, 1)
        self.horizontalLayout_2.setStretch(3, 3)

        self.verticalLayout_3.addLayout(self.horizontalLayout_2)

        self.image_list = QListWidget(self.layoutWidget1)
        self.image_list.setObjectName(u"image_list")
        self.image_list.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        self.image_list.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.image_list.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.image_list.setProperty(u"showDropIndicator", False)
        self.image_list.setDragDropMode(QAbstractItemView.NoDragDrop)
        self.image_list.setTextElideMode(Qt.ElideLeft)
        self.image_list.setVerticalScrollMode(QAbstractItemView.ScrollPerPixel)
        self.image_list.setHorizontalScrollMode(QAbstractItemView.ScrollPerPixel)
        self.image_list.setMovement(QListView.Static)
        self.image_list.setFlow(QListView.LeftToRight)
        self.image_list.setProperty(u"isWrapping", True)
        self.image_list.setResizeMode(QListView.Adjust)
        self.image_list.setLayoutMode(QListView.Batched)
        self.image_list.setViewMode(QListView.IconMode)
        self.image_list.setUniformItemSizes(False)
        self.image_list.setBatchSize(50)
        self.image_list.setWordWrap(False)
        self.image_list.setSelectionRectVisible(True)

        self.verticalLayout_3.addWidget(self.image_list)

        self.splitter.addWidget(self.layoutWidget1)
        self.layoutWidget = QWidget(self.splitter)
        self.layoutWidget.setObjectName(u"layoutWidget")
        self.verticalLayout = QVBoxLayout(self.layoutWidget)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.verticalLayout.setContentsMargins(0, 0, 0, 0)
        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setSpacing(6)
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.horizontalLayout.setContentsMargins(6, 6, 6, 6)
        self.label_file_name = CElidedLabel(self.layoutWidget)
        self.label_file_name.setObjectName(u"label_file_name")
        sizePolicy = QSizePolicy(QSizePolicy.Policy.MinimumExpanding, QSizePolicy.Policy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.label_file_name.sizePolicy().hasHeightForWidth())
        self.label_file_name.setSizePolicy(sizePolicy)
        self.label_file_name.setFrameShape(QFrame.NoFrame)
        self.label_file_name.setFrameShadow(QFrame.Raised)

        self.horizontalLayout.addWidget(self.label_file_name)

        self.pushButton_zoom_in = QPushButton(self.layoutWidget)
        self.pushButton_zoom_in.setObjectName(u"pushButton_zoom_in")
        icon2 = QIcon()
        iconThemeName = u"zoom-in"
        if QIcon.hasThemeIcon(iconThemeName):
            icon2 = QIcon.fromTheme(iconThemeName)
        else:
            icon2.addFile(u".", QSize(), QIcon.Mode.Normal, QIcon.State.Off)

        self.pushButton_zoom_in.setIcon(icon2)
        self.pushButton_zoom_in.setFlat(True)

        self.horizontalLayout.addWidget(self.pushButton_zoom_in)

        self.pushButton_zoom_out = QPushButton(self.layoutWidget)
        self.pushButton_zoom_out.setObjectName(u"pushButton_zoom_out")
        icon3 = QIcon()
        iconThemeName = u"zoom-out"
        if QIcon.hasThemeIcon(iconThemeName):
            icon3 = QIcon.fromTheme(iconThemeName)
        else:
            icon3.addFile(u".", QSize(), QIcon.Mode.Normal, QIcon.State.Off)

        self.pushButton_zoom_out.setIcon(icon3)
        self.pushButton_zoom_out.setFlat(True)

        self.horizontalLayout.addWidget(self.pushButton_zoom_out)

        self.pushButton_zoom_reset = QPushButton(self.layoutWidget)
        self.pushButton_zoom_reset.setObjectName(u"pushButton_zoom_reset")
        icon4 = QIcon()
        iconThemeName = u"zoom-original"
        if QIcon.hasThemeIcon(iconThemeName):
            icon4 = QIcon.fromTheme(iconThemeName)
        else:
            icon4.addFile(u".", QSize(), QIcon.Mode.Normal, QIcon.State.Off)

        self.pushButton_zoom_reset.setIcon(icon4)
        self.pushButton_zoom_reset.setFlat(True)

        self.horizontalLayout.addWidget(self.pushButton_zoom_reset)

        self.pushButton_zoom_fit = QPushButton(self.layoutWidget)
        self.pushButton_zoom_fit.setObjectName(u"pushButton_zoom_fit")
        icon5 = QIcon()
        iconThemeName = u"zoom-fit-best"
        if QIcon.hasThemeIcon(iconThemeName):
            icon5 = QIcon.fromTheme(iconThemeName)
        else:
            icon5.addFile(u".", QSize(), QIcon.Mode.Normal, QIcon.State.Off)

        self.pushButton_zoom_fit.setIcon(icon5)
        self.pushButton_zoom_fit.setFlat(True)

        self.horizontalLayout.addWidget(self.pushButton_zoom_fit)

        self.comboBox_view_mode = QComboBox(self.layoutWidget)
        self.comboBox_view_mode.addItem("")
        self.comboBox_view_mode.addItem("")
        self.comboBox_view_mode.setObjectName(u"comboBox_view_mode")

        self.horizontalLayout.addWidget(self.comboBox_view_mode)

        self.line = QFrame(self.layoutWidget)
        self.line.setObjectName(u"line")
        self.line.setFrameShape(QFrame.Shape.VLine)
        self.line.setFrameShadow(QFrame.Shadow.Sunken)

        self.horizontalLayout.addWidget(self.line)

        self.pushButton_row_up = QPushButton(self.layoutWidget)
        self.pushButton_row_up.setObjectName(u"pushButton_row_up")
        self.pushButton_row_up.setText(u"")
        icon6 = QIcon()
        iconThemeName = u"arrow-up"
        if QIcon.hasThemeIcon(iconThemeName):
            icon6 = QIcon.fromTheme(iconThemeName)
        else:
            icon6.addFile(u".", QSize(), QIcon.Mode.Normal, QIcon.State.Off)

        self.pushButton_row_up.setIcon(icon6)
        self.pushButton_row_up.setFlat(True)

        self.horizontalLayout.addWidget(self.pushButton_row_up)

        self.pushButton_row_down = QPushButton(self.layoutWidget)
        self.pushButton_row_down.setObjectName(u"pushButton_row_down")
        self.pushButton_row_down.setText(u"")
        icon7 = QIcon()
        iconThemeName = u"arrow-down"
        if QIcon.hasThemeIcon(iconThemeName):
            icon7 = QIcon.fromTheme(iconThemeName)
        else:
            icon7.addFile(u".", QSize(), QIcon.Mode.Normal, QIcon.State.Off)

        self.pushButton_row_down.setIcon(icon7)
        self.pushButton_row_down.setFlat(True)

        self.horizontalLayout.addWidget(self.pushButton_row_down)

        self.pushButton_new = QPushButton(self.layoutWidget)
        self.pushButton_new.setObjectName(u"pushButton_new")
        self.pushButton_new.setText(u"<new>")
        self.pushButton_new.setCheckable(True)
        self.pushButton_new.setFlat(True)

        self.horizontalLayout.addWidget(self.pushButton_new)

        self.pushButton_delete = QPushButton(self.layoutWidget)
        self.pushButton_delete.setObjectName(u"pushButton_delete")
        self.pushButton_delete.setText(u"")
        icon8 = QIcon()
        iconThemeName = u"edit-delete"
        if QIcon.hasThemeIcon(iconThemeName):
            icon8 = QIcon.fromTheme(iconThemeName)
        else:
            icon8.addFile(u".", QSize(), QIcon.Mode.Normal, QIcon.State.Off)

        self.pushButton_delete.setIcon(icon8)
        self.pushButton_delete.setFlat(True)

        self.horizontalLayout.addWidget(self.pushButton_delete)

        self.pushButton_undelete = QPushButton(self.layoutWidget)
        self.pushButton_undelete.setObjectName(u"pushButton_undelete")
        self.pushButton_undelete.setText(u"<undelete>")
        self.pushButton_undelete.setFlat(True)

        self.horizontalLayout.addWidget(self.pushButton_undelete)

        self.pushButton_reset = QPushButton(self.layoutWidget)
        self.pushButton_reset.setObjectName(u"pushButton_reset")
        icon9 = QIcon()
        iconThemeName = u"edit-reset"
        if QIcon.hasThemeIcon(iconThemeName):
            icon9 = QIcon.fromTheme(iconThemeName)
        else:
            icon9.addFile(u".", QSize(), QIcon.Mode.Normal, QIcon.State.Off)

        self.pushButton_reset.setIcon(icon9)
        self.pushButton_reset.setFlat(True)

        self.horizontalLayout.addWidget(self.pushButton_reset)

        self.pushButton_reset_all = QPushButton(self.layoutWidget)
        self.pushButton_reset_all.setObjectName(u"pushButton_reset_all")
        icon10 = QIcon()
        iconThemeName = u"document-revert"
        if QIcon.hasThemeIcon(iconThemeName):
            icon10 = QIcon.fromTheme(iconThemeName)
        else:
            icon10.addFile(u".", QSize(), QIcon.Mode.Normal, QIcon.State.Off)

        self.pushButton_reset_all.setIcon(icon10)
        self.pushButton_reset_all.setFlat(True)

        self.horizontalLayout.addWidget(self.pushButton_reset_all)

        self.line_2 = QFrame(self.layoutWidget)
        self.line_2.setObjectName(u"line_2")
        self.line_2.setFrameShape(QFrame.Shape.VLine)
        self.line_2.setFrameShadow(QFrame.Shadow.Sunken)

        self.horizontalLayout.addWidget(self.line_2)

        self.label_2 = QLabel(self.layoutWidget)
        self.label_2.setObjectName(u"label_2")

        self.horizontalLayout.addWidget(self.label_2)

        self.comboBox_ocr_language = CComboBox(self.layoutWidget)
        self.comboBox_ocr_language.setObjectName(u"comboBox_ocr_language")

        self.horizontalLayout.addWidget(self.comboBox_ocr_language)

        self.pushButton_done = QPushButton(self.layoutWidget)
        self.pushButton_done.setObjectName(u"pushButton_done")

        self.horizontalLayout.addWidget(self.pushButton_done)

        self.horizontalLayout.setStretch(0, 1)

        self.verticalLayout.addLayout(self.horizontalLayout)

        self.splitter_side = QSplitter(self.layoutWidget)
        self.splitter_side.setObjectName(u"splitter_side")
        self.splitter_side.setOrientation(Qt.Horizontal)
        self.image_viewer = BubbleImageViewer(self.splitter_side)
        self.image_viewer.setObjectName(u"image_viewer")
        self.splitter_side.addWidget(self.image_viewer)
        self.tableWidget_ocr = CTableWidget(self.splitter_side)
        if (self.tableWidget_ocr.columnCount() < 2):
            self.tableWidget_ocr.setColumnCount(2)
        __qtablewidgetitem = QTableWidgetItem()
        self.tableWidget_ocr.setHorizontalHeaderItem(0, __qtablewidgetitem)
        __qtablewidgetitem1 = QTableWidgetItem()
        self.tableWidget_ocr.setHorizontalHeaderItem(1, __qtablewidgetitem1)
        self.tableWidget_ocr.setObjectName(u"tableWidget_ocr")
        self.tableWidget_ocr.setAcceptDrops(True)
        self.tableWidget_ocr.setEditTriggers(QAbstractItemView.AllEditTriggers)
        self.tableWidget_ocr.setTabKeyNavigation(False)
        self.tableWidget_ocr.setProperty(u"showDropIndicator", True)
        self.tableWidget_ocr.setDragEnabled(True)
        self.tableWidget_ocr.setDragDropOverwriteMode(False)
        self.tableWidget_ocr.setDragDropMode(QAbstractItemView.NoDragDrop)
        self.tableWidget_ocr.setDefaultDropAction(Qt.MoveAction)
        self.tableWidget_ocr.setAlternatingRowColors(True)
        self.tableWidget_ocr.setSelectionMode(QAbstractItemView.SingleSelection)
        self.tableWidget_ocr.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.splitter_side.addWidget(self.tableWidget_ocr)
        self.tableWidget_ocr.horizontalHeader().setDefaultSectionSize(80)
        self.tableWidget_ocr.horizontalHeader().setStretchLastSection(True)
        self.tableWidget_ocr.verticalHeader().setVisible(False)

        self.verticalLayout.addWidget(self.splitter_side)

        self.verticalLayout.setStretch(1, 1)
        self.splitter.addWidget(self.layoutWidget)

        self.verticalLayout_2.addWidget(self.splitter)


        self.retranslateUi(OcrReview)

        QMetaObject.connectSlotsByName(OcrReview)
    # setupUi

    def retranslateUi(self, OcrReview):
        self.label.setText(QCoreApplication.translate("OcrReview", u"Icon Size:", None))
#if QT_CONFIG(tooltip)
        self.pushButton_prev.setToolTip(QCoreApplication.translate("OcrReview", u"Previous image", None))
#endif // QT_CONFIG(tooltip)
#if QT_CONFIG(tooltip)
        self.pushButton_next.setToolTip(QCoreApplication.translate("OcrReview", u"Next image", None))
#endif // QT_CONFIG(tooltip)
#if QT_CONFIG(tooltip)
        self.pushButton_zoom_in.setToolTip(QCoreApplication.translate("OcrReview", u"Zoom in", None))
#endif // QT_CONFIG(tooltip)
        self.pushButton_zoom_in.setText("")
#if QT_CONFIG(tooltip)
        self.pushButton_zoom_out.setToolTip(QCoreApplication.translate("OcrReview", u"Zoom out", None))
#endif // QT_CONFIG(tooltip)
        self.pushButton_zoom_out.setText("")
#if QT_CONFIG(tooltip)
        self.pushButton_zoom_reset.setToolTip(QCoreApplication.translate("OcrReview", u"Reset zoom", None))
#endif // QT_CONFIG(tooltip)
        self.pushButton_zoom_reset.setText("")
#if QT_CONFIG(tooltip)
        self.pushButton_zoom_fit.setToolTip(QCoreApplication.translate("OcrReview", u"Zoom to fit", None))
#endif // QT_CONFIG(tooltip)
        self.pushButton_zoom_fit.setText("")
        self.comboBox_view_mode.setItemText(0, QCoreApplication.translate("OcrReview", u"With Boxes", None))
        self.comboBox_view_mode.setItemText(1, QCoreApplication.translate("OcrReview", u"Original", None))

#if QT_CONFIG(tooltip)
        self.pushButton_row_up.setToolTip(QCoreApplication.translate("OcrReview", u"Move box order up", None))
#endif // QT_CONFIG(tooltip)
#if QT_CONFIG(tooltip)
        self.pushButton_row_down.setToolTip(QCoreApplication.translate("OcrReview", u"Move box order down", None))
#endif // QT_CONFIG(tooltip)
#if QT_CONFIG(tooltip)
        self.pushButton_new.setToolTip(QCoreApplication.translate("OcrReview", u"Add a new box", None))
#endif // QT_CONFIG(tooltip)
#if QT_CONFIG(tooltip)
        self.pushButton_delete.setToolTip(QCoreApplication.translate("OcrReview", u"Delete current box", None))
#endif // QT_CONFIG(tooltip)
#if QT_CONFIG(tooltip)
        self.pushButton_undelete.setToolTip(QCoreApplication.translate("OcrReview", u"Recover this deleted box", None))
#endif // QT_CONFIG(tooltip)
#if QT_CONFIG(tooltip)
        self.pushButton_reset.setToolTip(QCoreApplication.translate("OcrReview", u"Reset changes to this image", None))
#endif // QT_CONFIG(tooltip)
        self.pushButton_reset.setText("")
        self.pushButton_reset_all.setText(QCoreApplication.translate("OcrReview", u"Reset All", None))
        self.label_2.setText(QCoreApplication.translate("OcrReview", u"OCR new boxes:", None))
        self.pushButton_done.setText(QCoreApplication.translate("OcrReview", u"Done", None))
        ___qtablewidgetitem = self.tableWidget_ocr.horizontalHeaderItem(0)
        ___qtablewidgetitem.setText(QCoreApplication.translate("OcrReview", u"Box", None));
        ___qtablewidgetitem1 = self.tableWidget_ocr.horizontalHeaderItem(1)
        ___qtablewidgetitem1.setText(QCoreApplication.translate("OcrReview", u"Text", None));
        pass
    # retranslateUi

