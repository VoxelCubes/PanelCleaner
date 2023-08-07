# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'ImageDetails.ui'
##
## Created by: Qt User Interface Compiler version 6.5.1
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
from PySide6.QtWidgets import (QApplication, QFrame, QGraphicsView, QHBoxLayout,
    QLabel, QLayout, QPushButton, QScrollArea,
    QSizePolicy, QSpacerItem, QStackedWidget, QVBoxLayout,
    QWidget)

from pcleaner.gui.image_viewer import ImageViewer

class Ui_ImageDetails(object):
    def setupUi(self, ImageDetails):
        if not ImageDetails.objectName():
            ImageDetails.setObjectName(u"ImageDetails")
        ImageDetails.resize(900, 800)
        self.horizontalLayout_3 = QHBoxLayout(ImageDetails)
        self.horizontalLayout_3.setSpacing(0)
        self.horizontalLayout_3.setObjectName(u"horizontalLayout_3")
        self.horizontalLayout_3.setContentsMargins(0, 0, 0, 0)
        self.scrollArea = QScrollArea(ImageDetails)
        self.scrollArea.setObjectName(u"scrollArea")
        sizePolicy = QSizePolicy(QSizePolicy.Minimum, QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.scrollArea.sizePolicy().hasHeightForWidth())
        self.scrollArea.setSizePolicy(sizePolicy)
        self.scrollArea.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scrollAreaWidgetContents = QWidget()
        self.scrollAreaWidgetContents.setObjectName(u"scrollAreaWidgetContents")
        self.scrollAreaWidgetContents.setGeometry(QRect(0, 0, 138, 943))
        self.horizontalLayout_2 = QHBoxLayout(self.scrollAreaWidgetContents)
        self.horizontalLayout_2.setObjectName(u"horizontalLayout_2")
        self.horizontalLayout_2.setSizeConstraint(QLayout.SetMinimumSize)
        self.horizontalLayout_2.setContentsMargins(0, 0, 0, 0)
        self.widget = QWidget(self.scrollAreaWidgetContents)
        self.widget.setObjectName(u"widget")
        sizePolicy1 = QSizePolicy(QSizePolicy.Minimum, QSizePolicy.Preferred)
        sizePolicy1.setHorizontalStretch(0)
        sizePolicy1.setVerticalStretch(0)
        sizePolicy1.setHeightForWidth(self.widget.sizePolicy().hasHeightForWidth())
        self.widget.setSizePolicy(sizePolicy1)
        self.sidebar_layout = QVBoxLayout(self.widget)
        self.sidebar_layout.setObjectName(u"sidebar_layout")
        self.sidebar_layout.setContentsMargins(4, 4, 4, 4)
        self.label_2 = QLabel(self.widget)
        self.label_2.setObjectName(u"label_2")
        font = QFont()
        font.setBold(True)
        self.label_2.setFont(font)

        self.sidebar_layout.addWidget(self.label_2)

        self.pushButton_input = QPushButton(self.widget)
        self.pushButton_input.setObjectName(u"pushButton_input")
        self.pushButton_input.setCheckable(True)
        self.pushButton_input.setAutoExclusive(True)

        self.sidebar_layout.addWidget(self.pushButton_input)

        self.verticalSpacer = QSpacerItem(20, 16, QSizePolicy.Minimum, QSizePolicy.Minimum)

        self.sidebar_layout.addItem(self.verticalSpacer)

        self.label_3 = QLabel(self.widget)
        self.label_3.setObjectName(u"label_3")
        self.label_3.setFont(font)

        self.sidebar_layout.addWidget(self.label_3)

        self.pushButton_text_detection = QPushButton(self.widget)
        self.pushButton_text_detection.setObjectName(u"pushButton_text_detection")
        self.pushButton_text_detection.setCheckable(True)
        self.pushButton_text_detection.setAutoExclusive(True)

        self.sidebar_layout.addWidget(self.pushButton_text_detection)

        self.verticalSpacer_2 = QSpacerItem(20, 16, QSizePolicy.Minimum, QSizePolicy.Minimum)

        self.sidebar_layout.addItem(self.verticalSpacer_2)

        self.label_4 = QLabel(self.widget)
        self.label_4.setObjectName(u"label_4")
        self.label_4.setFont(font)

        self.sidebar_layout.addWidget(self.label_4)

        self.label_5 = QLabel(self.widget)
        self.label_5.setObjectName(u"label_5")

        self.sidebar_layout.addWidget(self.label_5)

        self.pushButton_initial_boxes = QPushButton(self.widget)
        self.pushButton_initial_boxes.setObjectName(u"pushButton_initial_boxes")
        self.pushButton_initial_boxes.setCheckable(True)
        self.pushButton_initial_boxes.setAutoExclusive(True)

        self.sidebar_layout.addWidget(self.pushButton_initial_boxes)

        self.label_6 = QLabel(self.widget)
        self.label_6.setObjectName(u"label_6")

        self.sidebar_layout.addWidget(self.label_6)

        self.pushButton_final_boxes = QPushButton(self.widget)
        self.pushButton_final_boxes.setObjectName(u"pushButton_final_boxes")
        self.pushButton_final_boxes.setCheckable(True)
        self.pushButton_final_boxes.setAutoExclusive(True)

        self.sidebar_layout.addWidget(self.pushButton_final_boxes)

        self.verticalSpacer_3 = QSpacerItem(20, 16, QSizePolicy.Minimum, QSizePolicy.Minimum)

        self.sidebar_layout.addItem(self.verticalSpacer_3)

        self.label_7 = QLabel(self.widget)
        self.label_7.setObjectName(u"label_7")
        self.label_7.setFont(font)

        self.sidebar_layout.addWidget(self.label_7)

        self.label_8 = QLabel(self.widget)
        self.label_8.setObjectName(u"label_8")

        self.sidebar_layout.addWidget(self.label_8)

        self.pushButton_box_mask = QPushButton(self.widget)
        self.pushButton_box_mask.setObjectName(u"pushButton_box_mask")
        self.pushButton_box_mask.setCheckable(True)
        self.pushButton_box_mask.setAutoExclusive(True)

        self.sidebar_layout.addWidget(self.pushButton_box_mask)

        self.label_9 = QLabel(self.widget)
        self.label_9.setObjectName(u"label_9")

        self.sidebar_layout.addWidget(self.label_9)

        self.pushButton_cut_mask = QPushButton(self.widget)
        self.pushButton_cut_mask.setObjectName(u"pushButton_cut_mask")
        self.pushButton_cut_mask.setCheckable(True)
        self.pushButton_cut_mask.setAutoExclusive(True)

        self.sidebar_layout.addWidget(self.pushButton_cut_mask)

        self.label_13 = QLabel(self.widget)
        self.label_13.setObjectName(u"label_13")

        self.sidebar_layout.addWidget(self.label_13)

        self.pushButton_mask_layers = QPushButton(self.widget)
        self.pushButton_mask_layers.setObjectName(u"pushButton_mask_layers")
        self.pushButton_mask_layers.setCheckable(True)
        self.pushButton_mask_layers.setAutoExclusive(True)

        self.sidebar_layout.addWidget(self.pushButton_mask_layers)

        self.label_10 = QLabel(self.widget)
        self.label_10.setObjectName(u"label_10")

        self.sidebar_layout.addWidget(self.label_10)

        self.pushButton_final_mask = QPushButton(self.widget)
        self.pushButton_final_mask.setObjectName(u"pushButton_final_mask")
        self.pushButton_final_mask.setCheckable(True)
        self.pushButton_final_mask.setAutoExclusive(True)

        self.sidebar_layout.addWidget(self.pushButton_final_mask)

        self.label_11 = QLabel(self.widget)
        self.label_11.setObjectName(u"label_11")

        self.sidebar_layout.addWidget(self.label_11)

        self.pushButton_output_masked = QPushButton(self.widget)
        self.pushButton_output_masked.setObjectName(u"pushButton_output_masked")
        self.pushButton_output_masked.setCheckable(True)
        self.pushButton_output_masked.setAutoExclusive(True)

        self.sidebar_layout.addWidget(self.pushButton_output_masked)

        self.verticalSpacer_4 = QSpacerItem(20, 16, QSizePolicy.Minimum, QSizePolicy.Minimum)

        self.sidebar_layout.addItem(self.verticalSpacer_4)

        self.label_12 = QLabel(self.widget)
        self.label_12.setObjectName(u"label_12")
        self.label_12.setFont(font)

        self.sidebar_layout.addWidget(self.label_12)

        self.label_15 = QLabel(self.widget)
        self.label_15.setObjectName(u"label_15")

        self.sidebar_layout.addWidget(self.label_15)

        self.pushButton_denoise_mask = QPushButton(self.widget)
        self.pushButton_denoise_mask.setObjectName(u"pushButton_denoise_mask")
        self.pushButton_denoise_mask.setCheckable(True)
        self.pushButton_denoise_mask.setAutoExclusive(True)

        self.sidebar_layout.addWidget(self.pushButton_denoise_mask)

        self.label_14 = QLabel(self.widget)
        self.label_14.setObjectName(u"label_14")

        self.sidebar_layout.addWidget(self.label_14)

        self.pushButton_denoised_output = QPushButton(self.widget)
        self.pushButton_denoised_output.setObjectName(u"pushButton_denoised_output")
        self.pushButton_denoised_output.setCheckable(True)
        self.pushButton_denoised_output.setAutoExclusive(True)

        self.sidebar_layout.addWidget(self.pushButton_denoised_output)


        self.horizontalLayout_2.addWidget(self.widget)

        self.scrollArea.setWidget(self.scrollAreaWidgetContents)

        self.horizontalLayout_3.addWidget(self.scrollArea)

        self.verticalLayout = QVBoxLayout()
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setSpacing(6)
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.horizontalLayout.setContentsMargins(6, 4, 4, 4)
        self.label_file_name = QLabel(ImageDetails)
        self.label_file_name.setObjectName(u"label_file_name")

        self.horizontalLayout.addWidget(self.label_file_name)

        self.horizontalSpacer = QSpacerItem(0, 0, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.horizontalLayout.addItem(self.horizontalSpacer)

        self.pushButton_export = QPushButton(ImageDetails)
        self.pushButton_export.setObjectName(u"pushButton_export")
        icon = QIcon()
        iconThemeName = u"document-save"
        if QIcon.hasThemeIcon(iconThemeName):
            icon = QIcon.fromTheme(iconThemeName)
        else:
            icon.addFile(u"../../../.designer/backup", QSize(), QIcon.Normal, QIcon.Off)

        self.pushButton_export.setIcon(icon)

        self.horizontalLayout.addWidget(self.pushButton_export)

        self.pushButton_refresh = QPushButton(ImageDetails)
        self.pushButton_refresh.setObjectName(u"pushButton_refresh")
        icon1 = QIcon()
        iconThemeName = u"view-refresh"
        if QIcon.hasThemeIcon(iconThemeName):
            icon1 = QIcon.fromTheme(iconThemeName)
        else:
            icon1.addFile(u"../../../.designer/backup", QSize(), QIcon.Normal, QIcon.Off)

        self.pushButton_refresh.setIcon(icon1)

        self.horizontalLayout.addWidget(self.pushButton_refresh)

        self.pushButton_zoom_in = QPushButton(ImageDetails)
        self.pushButton_zoom_in.setObjectName(u"pushButton_zoom_in")
        icon2 = QIcon()
        iconThemeName = u"zoom-in"
        if QIcon.hasThemeIcon(iconThemeName):
            icon2 = QIcon.fromTheme(iconThemeName)
        else:
            icon2.addFile(u"../../../.designer/backup", QSize(), QIcon.Normal, QIcon.Off)

        self.pushButton_zoom_in.setIcon(icon2)
        self.pushButton_zoom_in.setFlat(True)

        self.horizontalLayout.addWidget(self.pushButton_zoom_in)

        self.pushButton_zoom_out = QPushButton(ImageDetails)
        self.pushButton_zoom_out.setObjectName(u"pushButton_zoom_out")
        icon3 = QIcon()
        iconThemeName = u"zoom-out"
        if QIcon.hasThemeIcon(iconThemeName):
            icon3 = QIcon.fromTheme(iconThemeName)
        else:
            icon3.addFile(u"../../../.designer/backup", QSize(), QIcon.Normal, QIcon.Off)

        self.pushButton_zoom_out.setIcon(icon3)
        self.pushButton_zoom_out.setFlat(True)

        self.horizontalLayout.addWidget(self.pushButton_zoom_out)

        self.pushButton_zoom_reset = QPushButton(ImageDetails)
        self.pushButton_zoom_reset.setObjectName(u"pushButton_zoom_reset")
        icon4 = QIcon()
        iconThemeName = u"zoom-original"
        if QIcon.hasThemeIcon(iconThemeName):
            icon4 = QIcon.fromTheme(iconThemeName)
        else:
            icon4.addFile(u"../../../.designer/backup", QSize(), QIcon.Normal, QIcon.Off)

        self.pushButton_zoom_reset.setIcon(icon4)
        self.pushButton_zoom_reset.setFlat(True)

        self.horizontalLayout.addWidget(self.pushButton_zoom_reset)


        self.verticalLayout.addLayout(self.horizontalLayout)

        self.stackedWidget = QStackedWidget(ImageDetails)
        self.stackedWidget.setObjectName(u"stackedWidget")
        self.page_viewer = QWidget()
        self.page_viewer.setObjectName(u"page_viewer")
        self.verticalLayout_3 = QVBoxLayout(self.page_viewer)
        self.verticalLayout_3.setSpacing(0)
        self.verticalLayout_3.setObjectName(u"verticalLayout_3")
        self.verticalLayout_3.setContentsMargins(0, 0, 0, 0)
        self.image_viewer = ImageViewer(self.page_viewer)
        self.image_viewer.setObjectName(u"image_viewer")
        sizePolicy2 = QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        sizePolicy2.setHorizontalStretch(0)
        sizePolicy2.setVerticalStretch(0)
        sizePolicy2.setHeightForWidth(self.image_viewer.sizePolicy().hasHeightForWidth())
        self.image_viewer.setSizePolicy(sizePolicy2)
        self.image_viewer.setFrameShape(QFrame.NoFrame)
        self.image_viewer.setFrameShadow(QFrame.Plain)
        self.image_viewer.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)

        self.verticalLayout_3.addWidget(self.image_viewer)

        self.stackedWidget.addWidget(self.page_viewer)
        self.page_no_image = QWidget()
        self.page_no_image.setObjectName(u"page_no_image")
        self.verticalLayout_4 = QVBoxLayout(self.page_no_image)
        self.verticalLayout_4.setObjectName(u"verticalLayout_4")
        self.label_17 = QLabel(self.page_no_image)
        self.label_17.setObjectName(u"label_17")

        self.verticalLayout_4.addWidget(self.label_17, 0, Qt.AlignHCenter)

        self.stackedWidget.addWidget(self.page_no_image)

        self.verticalLayout.addWidget(self.stackedWidget)

        self.horizontalLayout_4 = QHBoxLayout()
        self.horizontalLayout_4.setSpacing(6)
        self.horizontalLayout_4.setObjectName(u"horizontalLayout_4")
        self.horizontalLayout_4.setContentsMargins(6, 4, 4, 4)
        self.label_step = QLabel(ImageDetails)
        self.label_step.setObjectName(u"label_step")

        self.horizontalLayout_4.addWidget(self.label_step)

        self.horizontalSpacer_2 = QSpacerItem(20, 0, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.horizontalLayout_4.addItem(self.horizontalSpacer_2)

        self.label_position_label = QLabel(ImageDetails)
        self.label_position_label.setObjectName(u"label_position_label")

        self.horizontalLayout_4.addWidget(self.label_position_label)

        self.label_position = QLabel(ImageDetails)
        self.label_position.setObjectName(u"label_position")

        self.horizontalLayout_4.addWidget(self.label_position)

        self.horizontalSpacer_3 = QSpacerItem(10, 10, QSizePolicy.Minimum, QSizePolicy.Minimum)

        self.horizontalLayout_4.addItem(self.horizontalSpacer_3)

        self.label_size_label = QLabel(ImageDetails)
        self.label_size_label.setObjectName(u"label_size_label")

        self.horizontalLayout_4.addWidget(self.label_size_label)

        self.label_size = QLabel(ImageDetails)
        self.label_size.setObjectName(u"label_size")

        self.horizontalLayout_4.addWidget(self.label_size)


        self.verticalLayout.addLayout(self.horizontalLayout_4)


        self.horizontalLayout_3.addLayout(self.verticalLayout)


        self.retranslateUi(ImageDetails)

        self.stackedWidget.setCurrentIndex(1)


        QMetaObject.connectSlotsByName(ImageDetails)
    # setupUi

    def retranslateUi(self, ImageDetails):
        ImageDetails.setWindowTitle(QCoreApplication.translate("ImageDetails", u"Form", None))
        self.label_2.setText(QCoreApplication.translate("ImageDetails", u"Input", None))
        self.pushButton_input.setText("")
        self.label_3.setText(QCoreApplication.translate("ImageDetails", u"Text Detection", None))
        self.pushButton_text_detection.setText("")
        self.label_4.setText(QCoreApplication.translate("ImageDetails", u"Preprocessor", None))
        self.label_5.setText(QCoreApplication.translate("ImageDetails", u"Initial Boxes", None))
        self.pushButton_initial_boxes.setText("")
        self.label_6.setText(QCoreApplication.translate("ImageDetails", u"Final Boxes", None))
        self.pushButton_final_boxes.setText("")
        self.label_7.setText(QCoreApplication.translate("ImageDetails", u"Masker", None))
        self.label_8.setText(QCoreApplication.translate("ImageDetails", u"Box Mask", None))
        self.pushButton_box_mask.setText("")
        self.label_9.setText(QCoreApplication.translate("ImageDetails", u"Cut Mask", None))
        self.pushButton_cut_mask.setText("")
        self.label_13.setText(QCoreApplication.translate("ImageDetails", u"Mask Layers", None))
        self.pushButton_mask_layers.setText("")
        self.label_10.setText(QCoreApplication.translate("ImageDetails", u"Final Mask", None))
        self.pushButton_final_mask.setText("")
        self.label_11.setText(QCoreApplication.translate("ImageDetails", u"Masked Output", None))
        self.pushButton_output_masked.setText("")
        self.label_12.setText(QCoreApplication.translate("ImageDetails", u"Denoiser", None))
        self.label_15.setText(QCoreApplication.translate("ImageDetails", u"Denoise Mask", None))
        self.pushButton_denoise_mask.setText("")
        self.label_14.setText(QCoreApplication.translate("ImageDetails", u"Denoised Output", None))
        self.pushButton_denoised_output.setText("")
        self.label_file_name.setText(QCoreApplication.translate("ImageDetails", u"<File name>", None))
        self.pushButton_export.setText(QCoreApplication.translate("ImageDetails", u"Export", None))
        self.pushButton_refresh.setText(QCoreApplication.translate("ImageDetails", u"Refresh", None))
#if QT_CONFIG(tooltip)
        self.pushButton_zoom_in.setToolTip(QCoreApplication.translate("ImageDetails", u"Zoom in", None))
#endif // QT_CONFIG(tooltip)
        self.pushButton_zoom_in.setText("")
#if QT_CONFIG(tooltip)
        self.pushButton_zoom_out.setToolTip(QCoreApplication.translate("ImageDetails", u"Zoom out", None))
#endif // QT_CONFIG(tooltip)
        self.pushButton_zoom_out.setText("")
#if QT_CONFIG(tooltip)
        self.pushButton_zoom_reset.setToolTip(QCoreApplication.translate("ImageDetails", u"Reset zoom", None))
#endif // QT_CONFIG(tooltip)
        self.pushButton_zoom_reset.setText("")
        self.label_17.setText(QCoreApplication.translate("ImageDetails", u"Generating...", None))
        self.label_step.setText(QCoreApplication.translate("ImageDetails", u"<Current Step>", None))
        self.label_position_label.setText(QCoreApplication.translate("ImageDetails", u"Position:", None))
        self.label_position.setText(QCoreApplication.translate("ImageDetails", u"<x,y>", None))
        self.label_size_label.setText(QCoreApplication.translate("ImageDetails", u"Size:", None))
        self.label_size.setText(QCoreApplication.translate("ImageDetails", u"<w x h>", None))
    # retranslateUi

