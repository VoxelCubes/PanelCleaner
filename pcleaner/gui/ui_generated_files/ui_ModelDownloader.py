# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'ModelDownloader.ui'
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
from PySide6.QtWidgets import (QApplication, QDialog, QHBoxLayout, QLabel,
    QProgressBar, QSizePolicy, QSpacerItem, QVBoxLayout,
    QWidget)

class Ui_ModelDownloader(object):
    def setupUi(self, ModelDownloader):
        if not ModelDownloader.objectName():
            ModelDownloader.setObjectName(u"ModelDownloader")
        ModelDownloader.resize(720, 306)
        ModelDownloader.setModal(True)
        self.verticalLayout = QVBoxLayout(ModelDownloader)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.label = QLabel(ModelDownloader)
        self.label.setObjectName(u"label")

        self.verticalLayout.addWidget(self.label)

        self.verticalSpacer_2 = QSpacerItem(20, 10, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed)

        self.verticalLayout.addItem(self.verticalSpacer_2)

        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setSpacing(12)
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.label_model_name = QLabel(ModelDownloader)
        self.label_model_name.setObjectName(u"label_model_name")
        self.label_model_name.setText(u"<model name>")

        self.horizontalLayout.addWidget(self.label_model_name)

        self.horizontalSpacer = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout.addItem(self.horizontalSpacer)

        self.label_model_speed = QLabel(ModelDownloader)
        self.label_model_speed.setObjectName(u"label_model_speed")
        self.label_model_speed.setText(u"<download speed>")

        self.horizontalLayout.addWidget(self.label_model_speed)

        self.label_model_size = QLabel(ModelDownloader)
        self.label_model_size.setObjectName(u"label_model_size")
        self.label_model_size.setText(u"<download size/total>")

        self.horizontalLayout.addWidget(self.label_model_size)


        self.verticalLayout.addLayout(self.horizontalLayout)

        self.progressBar_model = QProgressBar(ModelDownloader)
        self.progressBar_model.setObjectName(u"progressBar_model")
        self.progressBar_model.setValue(0)

        self.verticalLayout.addWidget(self.progressBar_model)

        self.verticalSpacer = QSpacerItem(20, 20, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed)

        self.verticalLayout.addItem(self.verticalSpacer)

        self.horizontalLayout_2 = QHBoxLayout()
        self.horizontalLayout_2.setSpacing(12)
        self.horizontalLayout_2.setObjectName(u"horizontalLayout_2")
        self.label_2 = QLabel(ModelDownloader)
        self.label_2.setObjectName(u"label_2")

        self.horizontalLayout_2.addWidget(self.label_2)

        self.label_ocr_file_name = QLabel(ModelDownloader)
        self.label_ocr_file_name.setObjectName(u"label_ocr_file_name")
        self.label_ocr_file_name.setText(u"<file name>")

        self.horizontalLayout_2.addWidget(self.label_ocr_file_name)

        self.horizontalSpacer_2 = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_2.addItem(self.horizontalSpacer_2)

        self.label_ocr_speed = QLabel(ModelDownloader)
        self.label_ocr_speed.setObjectName(u"label_ocr_speed")
        self.label_ocr_speed.setText(u"<download speed>")

        self.horizontalLayout_2.addWidget(self.label_ocr_speed)

        self.label_ocr_size = QLabel(ModelDownloader)
        self.label_ocr_size.setObjectName(u"label_ocr_size")
        self.label_ocr_size.setText(u"<download size/total>")

        self.horizontalLayout_2.addWidget(self.label_ocr_size)


        self.verticalLayout.addLayout(self.horizontalLayout_2)

        self.progressBar_ocr = QProgressBar(ModelDownloader)
        self.progressBar_ocr.setObjectName(u"progressBar_ocr")
        self.progressBar_ocr.setValue(0)

        self.verticalLayout.addWidget(self.progressBar_ocr)

        self.verticalSpacer_4 = QSpacerItem(20, 20, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed)

        self.verticalLayout.addItem(self.verticalSpacer_4)

        self.horizontalLayout_3 = QHBoxLayout()
        self.horizontalLayout_3.setSpacing(12)
        self.horizontalLayout_3.setObjectName(u"horizontalLayout_3")
        self.label_3 = QLabel(ModelDownloader)
        self.label_3.setObjectName(u"label_3")

        self.horizontalLayout_3.addWidget(self.label_3)

        self.horizontalSpacer_3 = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_3.addItem(self.horizontalSpacer_3)

        self.label_inpaint_speed = QLabel(ModelDownloader)
        self.label_inpaint_speed.setObjectName(u"label_inpaint_speed")
        self.label_inpaint_speed.setText(u"<download speed>")

        self.horizontalLayout_3.addWidget(self.label_inpaint_speed)

        self.label_inpaint_size = QLabel(ModelDownloader)
        self.label_inpaint_size.setObjectName(u"label_inpaint_size")
        self.label_inpaint_size.setText(u"<download size/total>")

        self.horizontalLayout_3.addWidget(self.label_inpaint_size)


        self.verticalLayout.addLayout(self.horizontalLayout_3)

        self.progressBar_inpaint = QProgressBar(ModelDownloader)
        self.progressBar_inpaint.setObjectName(u"progressBar_inpaint")
        self.progressBar_inpaint.setValue(0)

        self.verticalLayout.addWidget(self.progressBar_inpaint)

        self.verticalSpacer_3 = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.verticalLayout.addItem(self.verticalSpacer_3)


        self.retranslateUi(ModelDownloader)

        QMetaObject.connectSlotsByName(ModelDownloader)
    # setupUi

    def retranslateUi(self, ModelDownloader):
        ModelDownloader.setWindowTitle(QCoreApplication.translate("ModelDownloader", u"Downloading Machine Learning Models", None))
        self.label.setText(QCoreApplication.translate("ModelDownloader", u"Model data required to run Panel Cleaner:", None))
        self.label_2.setText(QCoreApplication.translate("ModelDownloader", u"OCR model:", None))
        self.label_3.setText(QCoreApplication.translate("ModelDownloader", u"Inpainting model", None))
    # retranslateUi

