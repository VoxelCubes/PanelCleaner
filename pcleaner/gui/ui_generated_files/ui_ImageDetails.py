# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'ImageDetails.ui'
##
## Created by: Qt User Interface Compiler version 6.4.0
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
from PySide6.QtWidgets import (QAbstractItemView, QApplication, QHBoxLayout, QLabel,
    QListView, QListWidget, QListWidgetItem, QPushButton,
    QSizePolicy, QSpacerItem, QVBoxLayout, QWidget)

class Ui_ImageDetails(object):
    def setupUi(self, ImageDetails):
        if not ImageDetails.objectName():
            ImageDetails.setObjectName(u"ImageDetails")
        ImageDetails.resize(800, 600)
        self.verticalLayout = QVBoxLayout(ImageDetails)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.verticalLayout.setContentsMargins(0, 0, 0, 0)
        self.listWidget = QListWidget(ImageDetails)
        self.listWidget.setObjectName(u"listWidget")
        sizePolicy = QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.listWidget.sizePolicy().hasHeightForWidth())
        self.listWidget.setSizePolicy(sizePolicy)
        self.listWidget.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.listWidget.setProperty("showDropIndicator", False)
        self.listWidget.setFlow(QListView.LeftToRight)
        self.listWidget.setLayoutMode(QListView.SinglePass)
        self.listWidget.setViewMode(QListView.IconMode)
        self.listWidget.setUniformItemSizes(True)
        self.listWidget.setItemAlignment(Qt.AlignLeading|Qt.AlignLeft|Qt.AlignVCenter)

        self.verticalLayout.addWidget(self.listWidget)

        self.widget_image = QWidget(ImageDetails)
        self.widget_image.setObjectName(u"widget_image")
        sizePolicy1 = QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        sizePolicy1.setHorizontalStretch(0)
        sizePolicy1.setVerticalStretch(0)
        sizePolicy1.setHeightForWidth(self.widget_image.sizePolicy().hasHeightForWidth())
        self.widget_image.setSizePolicy(sizePolicy1)

        self.verticalLayout.addWidget(self.widget_image)

        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.label_step = QLabel(ImageDetails)
        self.label_step.setObjectName(u"label_step")

        self.horizontalLayout.addWidget(self.label_step)

        self.horizontalSpacer_2 = QSpacerItem(20, 0, QSizePolicy.Maximum, QSizePolicy.Minimum)

        self.horizontalLayout.addItem(self.horizontalSpacer_2)

        self.label = QLabel(ImageDetails)
        self.label.setObjectName(u"label")

        self.horizontalLayout.addWidget(self.label)

        self.label_size = QLabel(ImageDetails)
        self.label_size.setObjectName(u"label_size")

        self.horizontalLayout.addWidget(self.label_size)

        self.horizontalSpacer_3 = QSpacerItem(20, 0, QSizePolicy.Maximum, QSizePolicy.Minimum)

        self.horizontalLayout.addItem(self.horizontalSpacer_3)

        self.label_fil_name = QLabel(ImageDetails)
        self.label_fil_name.setObjectName(u"label_fil_name")

        self.horizontalLayout.addWidget(self.label_fil_name)

        self.horizontalSpacer = QSpacerItem(40, 0, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.horizontalLayout.addItem(self.horizontalSpacer)

        self.pushButton_zoom_in = QPushButton(ImageDetails)
        self.pushButton_zoom_in.setObjectName(u"pushButton_zoom_in")
        icon = QIcon(QIcon.fromTheme(u"zoom-in"))
        self.pushButton_zoom_in.setIcon(icon)
        self.pushButton_zoom_in.setFlat(True)

        self.horizontalLayout.addWidget(self.pushButton_zoom_in)

        self.pushButton_zoom_out = QPushButton(ImageDetails)
        self.pushButton_zoom_out.setObjectName(u"pushButton_zoom_out")
        icon1 = QIcon(QIcon.fromTheme(u"zoom-out"))
        self.pushButton_zoom_out.setIcon(icon1)
        self.pushButton_zoom_out.setFlat(True)

        self.horizontalLayout.addWidget(self.pushButton_zoom_out)

        self.pushButton_zoom_reset = QPushButton(ImageDetails)
        self.pushButton_zoom_reset.setObjectName(u"pushButton_zoom_reset")
        icon2 = QIcon(QIcon.fromTheme(u"zoom-original"))
        self.pushButton_zoom_reset.setIcon(icon2)
        self.pushButton_zoom_reset.setFlat(True)

        self.horizontalLayout.addWidget(self.pushButton_zoom_reset)


        self.verticalLayout.addLayout(self.horizontalLayout)


        self.retranslateUi(ImageDetails)

        QMetaObject.connectSlotsByName(ImageDetails)
    # setupUi

    def retranslateUi(self, ImageDetails):
        ImageDetails.setWindowTitle(QCoreApplication.translate("ImageDetails", u"Form", None))
        self.label_step.setText(QCoreApplication.translate("ImageDetails", u"<Current Step>", None))
        self.label.setText(QCoreApplication.translate("ImageDetails", u"Size:", None))
        self.label_size.setText(QCoreApplication.translate("ImageDetails", u"TextLabel", None))
        self.label_fil_name.setText(QCoreApplication.translate("ImageDetails", u"<File name>", None))
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
    # retranslateUi

