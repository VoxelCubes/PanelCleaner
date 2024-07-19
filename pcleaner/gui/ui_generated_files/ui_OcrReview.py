# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'OcrReview.ui'
##
## Created by: Qt User Interface Compiler version 6.7.0
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
    QFrame, QHBoxLayout, QLabel, QListView,
    QListWidget, QListWidgetItem, QPushButton, QSizePolicy,
    QSlider, QSpacerItem, QSplitter, QVBoxLayout,
    QWidget)

from pcleaner.gui.CustomQ.CElidedLabel import CElidedLabel
from pcleaner.gui.CustomQ.CTextEdit import CTextEdit
from pcleaner.gui.image_viewer import ImageViewer

class Ui_OcrReview(object):
    def setupUi(self, OcrReview):
        if not OcrReview.objectName():
            OcrReview.setObjectName(u"OcrReview")
        OcrReview.resize(1400, 800)
        OcrReview.setWindowTitle(u"Review")
        OcrReview.setSizeGripEnabled(True)
        OcrReview.setModal(True)
        self.verticalLayout_2 = QVBoxLayout(OcrReview)
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.splitter = QSplitter(OcrReview)
        self.splitter.setObjectName(u"splitter")
        self.splitter.setOrientation(Qt.Horizontal)
        self.layoutWidget = QWidget(self.splitter)
        self.layoutWidget.setObjectName(u"layoutWidget")
        self.verticalLayout_3 = QVBoxLayout(self.layoutWidget)
        self.verticalLayout_3.setObjectName(u"verticalLayout_3")
        self.verticalLayout_3.setContentsMargins(0, 0, 0, 0)
        self.horizontalLayout_2 = QHBoxLayout()
        self.horizontalLayout_2.setObjectName(u"horizontalLayout_2")
        self.horizontalLayout_2.setContentsMargins(6, 6, 6, 6)
        self.label_image_count = QLabel(self.layoutWidget)
        self.label_image_count.setObjectName(u"label_image_count")

        self.horizontalLayout_2.addWidget(self.label_image_count)

        self.horizontalSpacer = QSpacerItem(0, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_2.addItem(self.horizontalSpacer)

        self.label = QLabel(self.layoutWidget)
        self.label.setObjectName(u"label")

        self.horizontalLayout_2.addWidget(self.label)

        self.horizontalSlider_icon_size = QSlider(self.layoutWidget)
        self.horizontalSlider_icon_size.setObjectName(u"horizontalSlider_icon_size")
        self.horizontalSlider_icon_size.setMinimum(1)
        self.horizontalSlider_icon_size.setMaximum(1000)
        self.horizontalSlider_icon_size.setOrientation(Qt.Horizontal)

        self.horizontalLayout_2.addWidget(self.horizontalSlider_icon_size)

        self.pushButton_prev = QPushButton(self.layoutWidget)
        self.pushButton_prev.setObjectName(u"pushButton_prev")
        self.pushButton_prev.setText(u"")
        icon = QIcon()
        iconThemeName = u"arrow-left"
        if QIcon.hasThemeIcon(iconThemeName):
            icon = QIcon.fromTheme(iconThemeName)
        else:
            icon.addFile(u".", QSize(), QIcon.Normal, QIcon.Off)

        self.pushButton_prev.setIcon(icon)
        self.pushButton_prev.setFlat(True)

        self.horizontalLayout_2.addWidget(self.pushButton_prev)

        self.pushButton_next = QPushButton(self.layoutWidget)
        self.pushButton_next.setObjectName(u"pushButton_next")
        self.pushButton_next.setText(u"")
        icon1 = QIcon()
        iconThemeName = u"arrow-right"
        if QIcon.hasThemeIcon(iconThemeName):
            icon1 = QIcon.fromTheme(iconThemeName)
        else:
            icon1.addFile(u".", QSize(), QIcon.Normal, QIcon.Off)

        self.pushButton_next.setIcon(icon1)
        self.pushButton_next.setFlat(True)

        self.horizontalLayout_2.addWidget(self.pushButton_next)

        self.horizontalLayout_2.setStretch(1, 1)
        self.horizontalLayout_2.setStretch(3, 3)

        self.verticalLayout_3.addLayout(self.horizontalLayout_2)

        self.image_list = QListWidget(self.layoutWidget)
        self.image_list.setObjectName(u"image_list")
        self.image_list.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        self.image_list.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.image_list.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.image_list.setProperty("showDropIndicator", False)
        self.image_list.setDragDropMode(QAbstractItemView.NoDragDrop)
        self.image_list.setVerticalScrollMode(QAbstractItemView.ScrollPerPixel)
        self.image_list.setHorizontalScrollMode(QAbstractItemView.ScrollPerPixel)
        self.image_list.setMovement(QListView.Static)
        self.image_list.setFlow(QListView.LeftToRight)
        self.image_list.setProperty("isWrapping", True)
        self.image_list.setResizeMode(QListView.Adjust)
        self.image_list.setLayoutMode(QListView.Batched)
        self.image_list.setViewMode(QListView.IconMode)
        self.image_list.setUniformItemSizes(False)
        self.image_list.setBatchSize(50)
        self.image_list.setWordWrap(False)
        self.image_list.setSelectionRectVisible(True)

        self.verticalLayout_3.addWidget(self.image_list)

        self.splitter.addWidget(self.layoutWidget)
        self.widget = QWidget(self.splitter)
        self.widget.setObjectName(u"widget")
        self.verticalLayout = QVBoxLayout(self.widget)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.verticalLayout.setContentsMargins(0, 0, 0, 0)
        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setSpacing(6)
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.horizontalLayout.setContentsMargins(6, 4, 4, 4)
        self.label_file_name = CElidedLabel(self.widget)
        self.label_file_name.setObjectName(u"label_file_name")
        sizePolicy = QSizePolicy(QSizePolicy.Policy.MinimumExpanding, QSizePolicy.Policy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.label_file_name.sizePolicy().hasHeightForWidth())
        self.label_file_name.setSizePolicy(sizePolicy)
        self.label_file_name.setFrameShape(QFrame.NoFrame)
        self.label_file_name.setFrameShadow(QFrame.Raised)

        self.horizontalLayout.addWidget(self.label_file_name)

        self.pushButton_zoom_in = QPushButton(self.widget)
        self.pushButton_zoom_in.setObjectName(u"pushButton_zoom_in")
        icon2 = QIcon()
        iconThemeName = u"zoom-in"
        if QIcon.hasThemeIcon(iconThemeName):
            icon2 = QIcon.fromTheme(iconThemeName)
        else:
            icon2.addFile(u".", QSize(), QIcon.Normal, QIcon.Off)

        self.pushButton_zoom_in.setIcon(icon2)
        self.pushButton_zoom_in.setFlat(True)

        self.horizontalLayout.addWidget(self.pushButton_zoom_in)

        self.pushButton_zoom_out = QPushButton(self.widget)
        self.pushButton_zoom_out.setObjectName(u"pushButton_zoom_out")
        icon3 = QIcon()
        iconThemeName = u"zoom-out"
        if QIcon.hasThemeIcon(iconThemeName):
            icon3 = QIcon.fromTheme(iconThemeName)
        else:
            icon3.addFile(u".", QSize(), QIcon.Normal, QIcon.Off)

        self.pushButton_zoom_out.setIcon(icon3)
        self.pushButton_zoom_out.setFlat(True)

        self.horizontalLayout.addWidget(self.pushButton_zoom_out)

        self.pushButton_zoom_reset = QPushButton(self.widget)
        self.pushButton_zoom_reset.setObjectName(u"pushButton_zoom_reset")
        icon4 = QIcon()
        iconThemeName = u"zoom-original"
        if QIcon.hasThemeIcon(iconThemeName):
            icon4 = QIcon.fromTheme(iconThemeName)
        else:
            icon4.addFile(u".", QSize(), QIcon.Normal, QIcon.Off)

        self.pushButton_zoom_reset.setIcon(icon4)
        self.pushButton_zoom_reset.setFlat(True)

        self.horizontalLayout.addWidget(self.pushButton_zoom_reset)

        self.pushButton_zoom_fit = QPushButton(self.widget)
        self.pushButton_zoom_fit.setObjectName(u"pushButton_zoom_fit")
        icon5 = QIcon()
        iconThemeName = u"zoom-fit-best"
        if QIcon.hasThemeIcon(iconThemeName):
            icon5 = QIcon.fromTheme(iconThemeName)
        else:
            icon5.addFile(u".", QSize(), QIcon.Normal, QIcon.Off)

        self.pushButton_zoom_fit.setIcon(icon5)
        self.pushButton_zoom_fit.setFlat(True)

        self.horizontalLayout.addWidget(self.pushButton_zoom_fit)

        self.comboBox_view_mode = QComboBox(self.widget)
        self.comboBox_view_mode.addItem("")
        self.comboBox_view_mode.addItem("")
        self.comboBox_view_mode.setObjectName(u"comboBox_view_mode")

        self.horizontalLayout.addWidget(self.comboBox_view_mode)

        self.pushButton_done = QPushButton(self.widget)
        self.pushButton_done.setObjectName(u"pushButton_done")

        self.horizontalLayout.addWidget(self.pushButton_done)


        self.verticalLayout.addLayout(self.horizontalLayout)

        self.splitter_side = QSplitter(self.widget)
        self.splitter_side.setObjectName(u"splitter_side")
        self.splitter_side.setOrientation(Qt.Horizontal)
        self.image_viewer = ImageViewer(self.splitter_side)
        self.image_viewer.setObjectName(u"image_viewer")
        self.splitter_side.addWidget(self.image_viewer)
        self.textEdit_ocr = CTextEdit(self.splitter_side)
        self.textEdit_ocr.setObjectName(u"textEdit_ocr")
        self.textEdit_ocr.setReadOnly(True)
        self.textEdit_ocr.setHtml(u"<!DOCTYPE HTML PUBLIC \"-//W3C//DTD HTML 4.0//EN\" \"http://www.w3.org/TR/REC-html40/strict.dtd\">\n"
"<html><head><meta name=\"qrichtext\" content=\"1\" /><style type=\"text/css\">\n"
"p, li { white-space: pre-wrap; }\n"
"</style></head><body style=\" font-family:'Noto Sans'; font-size:10pt; font-weight:400; font-style:normal;\">\n"
"<p style=\"-qt-paragraph-type:empty; margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><br /></p></body></html>")
        self.textEdit_ocr.setTabStopDistance(40.000000000000000)
        self.splitter_side.addWidget(self.textEdit_ocr)

        self.verticalLayout.addWidget(self.splitter_side)

        self.verticalLayout.setStretch(1, 1)
        self.splitter.addWidget(self.widget)

        self.verticalLayout_2.addWidget(self.splitter)


        self.retranslateUi(OcrReview)

        QMetaObject.connectSlotsByName(OcrReview)
    # setupUi

    def retranslateUi(self, OcrReview):
        self.label_image_count.setText(QCoreApplication.translate("OcrReview", u"<image count>", None))
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

        self.pushButton_done.setText(QCoreApplication.translate("OcrReview", u"Finish Review", None))
        pass
    # retranslateUi

