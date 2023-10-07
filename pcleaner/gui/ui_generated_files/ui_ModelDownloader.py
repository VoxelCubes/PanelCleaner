# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'ModelDownloader.ui'
##
## Created by: Qt User Interface Compiler version 6.5.3
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
from PySide6.QtWidgets import (QApplication, QDialog, QHBoxLayout, QLabel,
    QProgressBar, QSizePolicy, QSpacerItem, QVBoxLayout,
    QWidget)

class Ui_ModelDownloader(object):
    def setupUi(self, ModelDownloader):
        if not ModelDownloader.objectName():
            ModelDownloader.setObjectName(u"ModelDownloader")
        ModelDownloader.resize(720, 209)
        ModelDownloader.setModal(True)
        self.verticalLayout = QVBoxLayout(ModelDownloader)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.label = QLabel(ModelDownloader)
        self.label.setObjectName(u"label")

        self.verticalLayout.addWidget(self.label)

        self.verticalSpacer_2 = QSpacerItem(20, 10, QSizePolicy.Minimum, QSizePolicy.Fixed)

        self.verticalLayout.addItem(self.verticalSpacer_2)

        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setSpacing(12)
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.label_model_name = QLabel(ModelDownloader)
        self.label_model_name.setObjectName(u"label_model_name")

        self.horizontalLayout.addWidget(self.label_model_name)

        self.horizontalSpacer = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.horizontalLayout.addItem(self.horizontalSpacer)

        self.label_model_speed = QLabel(ModelDownloader)
        self.label_model_speed.setObjectName(u"label_model_speed")

        self.horizontalLayout.addWidget(self.label_model_speed)

        self.label_model_size = QLabel(ModelDownloader)
        self.label_model_size.setObjectName(u"label_model_size")

        self.horizontalLayout.addWidget(self.label_model_size)


        self.verticalLayout.addLayout(self.horizontalLayout)

        self.progressBar_model = QProgressBar(ModelDownloader)
        self.progressBar_model.setObjectName(u"progressBar_model")
        self.progressBar_model.setValue(0)

        self.verticalLayout.addWidget(self.progressBar_model)

        self.verticalSpacer = QSpacerItem(20, 20, QSizePolicy.Minimum, QSizePolicy.Fixed)

        self.verticalLayout.addItem(self.verticalSpacer)

        self.horizontalLayout_2 = QHBoxLayout()
        self.horizontalLayout_2.setSpacing(12)
        self.horizontalLayout_2.setObjectName(u"horizontalLayout_2")
        self.label_2 = QLabel(ModelDownloader)
        self.label_2.setObjectName(u"label_2")

        self.horizontalLayout_2.addWidget(self.label_2)

        self.label_ocr_file_name = QLabel(ModelDownloader)
        self.label_ocr_file_name.setObjectName(u"label_ocr_file_name")

        self.horizontalLayout_2.addWidget(self.label_ocr_file_name)

        self.horizontalSpacer_2 = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.horizontalLayout_2.addItem(self.horizontalSpacer_2)

        self.label_ocr_speed = QLabel(ModelDownloader)
        self.label_ocr_speed.setObjectName(u"label_ocr_speed")

        self.horizontalLayout_2.addWidget(self.label_ocr_speed)

        self.label_ocr_size = QLabel(ModelDownloader)
        self.label_ocr_size.setObjectName(u"label_ocr_size")

        self.horizontalLayout_2.addWidget(self.label_ocr_size)


        self.verticalLayout.addLayout(self.horizontalLayout_2)

        self.progressBar_ocr = QProgressBar(ModelDownloader)
        self.progressBar_ocr.setObjectName(u"progressBar_ocr")
        self.progressBar_ocr.setValue(0)

        self.verticalLayout.addWidget(self.progressBar_ocr)

        self.verticalSpacer_3 = QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)

        self.verticalLayout.addItem(self.verticalSpacer_3)


        self.retranslateUi(ModelDownloader)

        QMetaObject.connectSlotsByName(ModelDownloader)
    # setupUi

    def retranslateUi(self, ModelDownloader):
        ModelDownloader.setWindowTitle(QCoreApplication.translate("ModelDownloader", u"Downloading Machine Learning Models", None))
        self.label.setText(QCoreApplication.translate("ModelDownloader", u"Model data required to run Panel Cleaner:", None))
        self.label_model_name.setText(QCoreApplication.translate("ModelDownloader", u"<model name>", None))
        self.label_model_speed.setText(QCoreApplication.translate("ModelDownloader", u"<download speed>", None))
        self.label_model_size.setText(QCoreApplication.translate("ModelDownloader", u"<download size/total>", None))
        self.label_2.setText(QCoreApplication.translate("ModelDownloader", u"OCR model:", None))
        self.label_ocr_file_name.setText(QCoreApplication.translate("ModelDownloader", u"<file name>", None))
        self.label_ocr_speed.setText(QCoreApplication.translate("ModelDownloader", u"<download speed>", None))
        self.label_ocr_size.setText(QCoreApplication.translate("ModelDownloader", u"<download size/total>", None))
    # retranslateUi

