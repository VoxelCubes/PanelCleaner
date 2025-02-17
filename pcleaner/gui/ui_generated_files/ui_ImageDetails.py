# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'ImageDetails.ui'
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
from PySide6.QtWidgets import (QApplication, QFrame, QGraphicsView, QHBoxLayout,
    QLabel, QLayout, QPushButton, QScrollArea,
    QSizePolicy, QStackedWidget, QVBoxLayout, QWidget)

from pcleaner.gui.CustomQ.CElidedLabel import CElidedLabel
from pcleaner.gui.image_viewer import ImageViewer

class Ui_ImageDetails(object):
    def setupUi(self, ImageDetails):
        if not ImageDetails.objectName():
            ImageDetails.setObjectName(u"ImageDetails")
        ImageDetails.resize(900, 800)
        ImageDetails.setWindowTitle(u"Form")
        self.horizontalLayout_3 = QHBoxLayout(ImageDetails)
        self.horizontalLayout_3.setSpacing(0)
        self.horizontalLayout_3.setObjectName(u"horizontalLayout_3")
        self.horizontalLayout_3.setContentsMargins(0, 0, 0, 0)
        self.scrollArea = QScrollArea(ImageDetails)
        self.scrollArea.setObjectName(u"scrollArea")
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)
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
        sizePolicy1 = QSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Preferred)
        sizePolicy1.setHorizontalStretch(0)
        sizePolicy1.setVerticalStretch(0)
        sizePolicy1.setHeightForWidth(self.widget.sizePolicy().hasHeightForWidth())
        self.widget.setSizePolicy(sizePolicy1)
        self.sidebar_layout = QVBoxLayout(self.widget)
        self.sidebar_layout.setObjectName(u"sidebar_layout")
        self.sidebar_layout.setContentsMargins(4, 4, 4, 4)

        self.horizontalLayout_2.addWidget(self.widget)

        self.scrollArea.setWidget(self.scrollAreaWidgetContents)

        self.horizontalLayout_3.addWidget(self.scrollArea)

        self.verticalLayout = QVBoxLayout()
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setSpacing(6)
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.horizontalLayout.setContentsMargins(6, 4, 4, 4)
        self.label_file_name = CElidedLabel(ImageDetails)
        self.label_file_name.setObjectName(u"label_file_name")
        sizePolicy2 = QSizePolicy(QSizePolicy.Policy.MinimumExpanding, QSizePolicy.Policy.Preferred)
        sizePolicy2.setHorizontalStretch(0)
        sizePolicy2.setVerticalStretch(0)
        sizePolicy2.setHeightForWidth(self.label_file_name.sizePolicy().hasHeightForWidth())
        self.label_file_name.setSizePolicy(sizePolicy2)
        self.label_file_name.setFrameShape(QFrame.NoFrame)
        self.label_file_name.setFrameShadow(QFrame.Raised)

        self.horizontalLayout.addWidget(self.label_file_name)

        self.pushButton_zoom_in = QPushButton(ImageDetails)
        self.pushButton_zoom_in.setObjectName(u"pushButton_zoom_in")
        icon = QIcon()
        iconThemeName = u"zoom-in"
        if QIcon.hasThemeIcon(iconThemeName):
            icon = QIcon.fromTheme(iconThemeName)
        else:
            icon.addFile(u".", QSize(), QIcon.Mode.Normal, QIcon.State.Off)

        self.pushButton_zoom_in.setIcon(icon)
        self.pushButton_zoom_in.setFlat(True)

        self.horizontalLayout.addWidget(self.pushButton_zoom_in)

        self.pushButton_zoom_out = QPushButton(ImageDetails)
        self.pushButton_zoom_out.setObjectName(u"pushButton_zoom_out")
        icon1 = QIcon()
        iconThemeName = u"zoom-out"
        if QIcon.hasThemeIcon(iconThemeName):
            icon1 = QIcon.fromTheme(iconThemeName)
        else:
            icon1.addFile(u".", QSize(), QIcon.Mode.Normal, QIcon.State.Off)

        self.pushButton_zoom_out.setIcon(icon1)
        self.pushButton_zoom_out.setFlat(True)

        self.horizontalLayout.addWidget(self.pushButton_zoom_out)

        self.pushButton_zoom_reset = QPushButton(ImageDetails)
        self.pushButton_zoom_reset.setObjectName(u"pushButton_zoom_reset")
        icon2 = QIcon()
        iconThemeName = u"zoom-original"
        if QIcon.hasThemeIcon(iconThemeName):
            icon2 = QIcon.fromTheme(iconThemeName)
        else:
            icon2.addFile(u".", QSize(), QIcon.Mode.Normal, QIcon.State.Off)

        self.pushButton_zoom_reset.setIcon(icon2)
        self.pushButton_zoom_reset.setFlat(True)

        self.horizontalLayout.addWidget(self.pushButton_zoom_reset)

        self.pushButton_zoom_fit = QPushButton(ImageDetails)
        self.pushButton_zoom_fit.setObjectName(u"pushButton_zoom_fit")
        icon3 = QIcon()
        iconThemeName = u"zoom-fit-best"
        if QIcon.hasThemeIcon(iconThemeName):
            icon3 = QIcon.fromTheme(iconThemeName)
        else:
            icon3.addFile(u".", QSize(), QIcon.Mode.Normal, QIcon.State.Off)

        self.pushButton_zoom_fit.setIcon(icon3)
        self.pushButton_zoom_fit.setFlat(True)

        self.horizontalLayout.addWidget(self.pushButton_zoom_fit)

        self.pushButton_refresh = QPushButton(ImageDetails)
        self.pushButton_refresh.setObjectName(u"pushButton_refresh")
        self.pushButton_refresh.setEnabled(False)
        icon4 = QIcon()
        iconThemeName = u"view-refresh"
        if QIcon.hasThemeIcon(iconThemeName):
            icon4 = QIcon.fromTheme(iconThemeName)
        else:
            icon4.addFile(u".", QSize(), QIcon.Mode.Normal, QIcon.State.Off)

        self.pushButton_refresh.setIcon(icon4)

        self.horizontalLayout.addWidget(self.pushButton_refresh)

        self.pushButton_menu = QPushButton(ImageDetails)
        self.pushButton_menu.setObjectName(u"pushButton_menu")
        sizePolicy3 = QSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        sizePolicy3.setHorizontalStretch(0)
        sizePolicy3.setVerticalStretch(0)
        sizePolicy3.setHeightForWidth(self.pushButton_menu.sizePolicy().hasHeightForWidth())
        self.pushButton_menu.setSizePolicy(sizePolicy3)
        self.pushButton_menu.setMinimumSize(QSize(16, 16))
        self.pushButton_menu.setContextMenuPolicy(Qt.ActionsContextMenu)
        icon5 = QIcon()
        iconThemeName = u"overflow-menu"
        if QIcon.hasThemeIcon(iconThemeName):
            icon5 = QIcon.fromTheme(iconThemeName)
        else:
            icon5.addFile(u".", QSize(), QIcon.Mode.Normal, QIcon.State.Off)

        self.pushButton_menu.setIcon(icon5)

        self.horizontalLayout.addWidget(self.pushButton_menu)


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
        sizePolicy4 = QSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        sizePolicy4.setHorizontalStretch(0)
        sizePolicy4.setVerticalStretch(0)
        sizePolicy4.setHeightForWidth(self.image_viewer.sizePolicy().hasHeightForWidth())
        self.image_viewer.setSizePolicy(sizePolicy4)
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
        self.horizontalLayout_4.setSpacing(12)
        self.horizontalLayout_4.setObjectName(u"horizontalLayout_4")
        self.horizontalLayout_4.setContentsMargins(6, 4, 4, 4)
        self.label_step = QLabel(ImageDetails)
        self.label_step.setObjectName(u"label_step")
        sizePolicy5 = QSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        sizePolicy5.setHorizontalStretch(0)
        sizePolicy5.setVerticalStretch(0)
        sizePolicy5.setHeightForWidth(self.label_step.sizePolicy().hasHeightForWidth())
        self.label_step.setSizePolicy(sizePolicy5)
        self.label_step.setText(u"<Current Step>")
        self.label_step.setWordWrap(True)

        self.horizontalLayout_4.addWidget(self.label_step)

        self.horizontalLayout_6 = QHBoxLayout()
        self.horizontalLayout_6.setSpacing(4)
        self.horizontalLayout_6.setObjectName(u"horizontalLayout_6")
        self.label_position_label = QLabel(ImageDetails)
        self.label_position_label.setObjectName(u"label_position_label")

        self.horizontalLayout_6.addWidget(self.label_position_label)

        self.label_position = QLabel(ImageDetails)
        self.label_position.setObjectName(u"label_position")
        self.label_position.setText(u"<x,y>")

        self.horizontalLayout_6.addWidget(self.label_position)


        self.horizontalLayout_4.addLayout(self.horizontalLayout_6)

        self.horizontalLayout_7 = QHBoxLayout()
        self.horizontalLayout_7.setSpacing(4)
        self.horizontalLayout_7.setObjectName(u"horizontalLayout_7")
        self.label_size_label = QLabel(ImageDetails)
        self.label_size_label.setObjectName(u"label_size_label")

        self.horizontalLayout_7.addWidget(self.label_size_label)

        self.label_size = QLabel(ImageDetails)
        self.label_size.setObjectName(u"label_size")
        self.label_size.setText(u"<w x h>")

        self.horizontalLayout_7.addWidget(self.label_size)


        self.horizontalLayout_4.addLayout(self.horizontalLayout_7)

        self.widget_footer_info = QWidget(ImageDetails)
        self.widget_footer_info.setObjectName(u"widget_footer_info")
        self.horizontalLayout_5 = QHBoxLayout(self.widget_footer_info)
        self.horizontalLayout_5.setObjectName(u"horizontalLayout_5")
        self.horizontalLayout_5.setContentsMargins(0, 0, 0, 0)

        self.horizontalLayout_4.addWidget(self.widget_footer_info)


        self.verticalLayout.addLayout(self.horizontalLayout_4)


        self.horizontalLayout_3.addLayout(self.verticalLayout)


        self.retranslateUi(ImageDetails)

        self.stackedWidget.setCurrentIndex(1)


        QMetaObject.connectSlotsByName(ImageDetails)
    # setupUi

    def retranslateUi(self, ImageDetails):
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
#if QT_CONFIG(tooltip)
        self.pushButton_zoom_fit.setToolTip(QCoreApplication.translate("ImageDetails", u"Zoom to fit", None))
#endif // QT_CONFIG(tooltip)
        self.pushButton_zoom_fit.setText("")
        self.pushButton_refresh.setText(QCoreApplication.translate("ImageDetails", u"Refresh", None))
        self.pushButton_menu.setText("")
        self.label_17.setText(QCoreApplication.translate("ImageDetails", u"Generating...", None))
        self.label_position_label.setText(QCoreApplication.translate("ImageDetails", u"Position:", None))
        self.label_size_label.setText(QCoreApplication.translate("ImageDetails", u"Size:", None))
        pass
    # retranslateUi

