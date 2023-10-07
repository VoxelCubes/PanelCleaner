# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'SetupGreeter.ui'
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
from PySide6.QtWidgets import (QAbstractButton, QApplication, QDialog, QDialogButtonBox,
    QFormLayout, QLabel, QSizePolicy, QSpacerItem,
    QVBoxLayout, QWidget)

class Ui_SetupGreeter(object):
    def setupUi(self, SetupGreeter):
        if not SetupGreeter.objectName():
            SetupGreeter.setObjectName(u"SetupGreeter")
        SetupGreeter.resize(720, 382)
        SetupGreeter.setMinimumSize(QSize(600, 0))
        SetupGreeter.setModal(True)
        self.verticalLayout = QVBoxLayout(SetupGreeter)
        self.verticalLayout.setSpacing(20)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.verticalLayout.setContentsMargins(-1, 20, -1, -1)
        self.label_2 = QLabel(SetupGreeter)
        self.label_2.setObjectName(u"label_2")
        self.label_2.setTextFormat(Qt.MarkdownText)

        self.verticalLayout.addWidget(self.label_2, 0, Qt.AlignHCenter)

        self.label = QLabel(SetupGreeter)
        self.label.setObjectName(u"label")
        self.label.setTextFormat(Qt.PlainText)
        self.label.setWordWrap(True)
        self.label.setOpenExternalLinks(True)
        self.label.setTextInteractionFlags(Qt.NoTextInteraction)

        self.verticalLayout.addWidget(self.label)

        self.formLayout = QFormLayout()
        self.formLayout.setObjectName(u"formLayout")
        self.formLayout.setFieldGrowthPolicy(QFormLayout.ExpandingFieldsGrow)
        self.formLayout.setRowWrapPolicy(QFormLayout.WrapLongRows)
        self.label_9 = QLabel(SetupGreeter)
        self.label_9.setObjectName(u"label_9")

        self.formLayout.setWidget(0, QFormLayout.LabelRole, self.label_9)

        self.label_3 = QLabel(SetupGreeter)
        self.label_3.setObjectName(u"label_3")
        sizePolicy = QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.label_3.sizePolicy().hasHeightForWidth())
        self.label_3.setSizePolicy(sizePolicy)
        self.label_3.setTextFormat(Qt.MarkdownText)
        self.label_3.setWordWrap(True)
        self.label_3.setOpenExternalLinks(True)
        self.label_3.setTextInteractionFlags(Qt.TextBrowserInteraction)

        self.formLayout.setWidget(0, QFormLayout.FieldRole, self.label_3)

        self.label_4 = QLabel(SetupGreeter)
        self.label_4.setObjectName(u"label_4")
        self.label_4.setTextFormat(Qt.PlainText)
        self.label_4.setWordWrap(True)
        self.label_4.setOpenExternalLinks(True)
        self.label_4.setTextInteractionFlags(Qt.NoTextInteraction)

        self.formLayout.setWidget(1, QFormLayout.LabelRole, self.label_4)

        self.label_text_detector_path = QLabel(SetupGreeter)
        self.label_text_detector_path.setObjectName(u"label_text_detector_path")
        self.label_text_detector_path.setTextInteractionFlags(Qt.TextSelectableByKeyboard|Qt.TextSelectableByMouse)

        self.formLayout.setWidget(1, QFormLayout.FieldRole, self.label_text_detector_path)

        self.label_10 = QLabel(SetupGreeter)
        self.label_10.setObjectName(u"label_10")
        self.label_10.setWordWrap(True)

        self.formLayout.setWidget(3, QFormLayout.LabelRole, self.label_10)

        self.label_5 = QLabel(SetupGreeter)
        self.label_5.setObjectName(u"label_5")
        sizePolicy1 = QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        sizePolicy1.setHorizontalStretch(0)
        sizePolicy1.setVerticalStretch(0)
        sizePolicy1.setHeightForWidth(self.label_5.sizePolicy().hasHeightForWidth())
        self.label_5.setSizePolicy(sizePolicy1)
        self.label_5.setTextFormat(Qt.MarkdownText)
        self.label_5.setWordWrap(True)
        self.label_5.setOpenExternalLinks(True)
        self.label_5.setTextInteractionFlags(Qt.TextBrowserInteraction)

        self.formLayout.setWidget(3, QFormLayout.FieldRole, self.label_5)

        self.label_7 = QLabel(SetupGreeter)
        self.label_7.setObjectName(u"label_7")
        self.label_7.setTextFormat(Qt.PlainText)
        self.label_7.setWordWrap(True)
        self.label_7.setOpenExternalLinks(True)
        self.label_7.setTextInteractionFlags(Qt.NoTextInteraction)

        self.formLayout.setWidget(4, QFormLayout.LabelRole, self.label_7)

        self.label_ocr_path = QLabel(SetupGreeter)
        self.label_ocr_path.setObjectName(u"label_ocr_path")
        self.label_ocr_path.setTextInteractionFlags(Qt.TextSelectableByKeyboard|Qt.TextSelectableByMouse)

        self.formLayout.setWidget(4, QFormLayout.FieldRole, self.label_ocr_path)

        self.verticalSpacer_2 = QSpacerItem(20, 20, QSizePolicy.Minimum, QSizePolicy.Fixed)

        self.formLayout.setItem(2, QFormLayout.LabelRole, self.verticalSpacer_2)


        self.verticalLayout.addLayout(self.formLayout)

        self.verticalSpacer = QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)

        self.verticalLayout.addItem(self.verticalSpacer)

        self.buttonBox = QDialogButtonBox(SetupGreeter)
        self.buttonBox.setObjectName(u"buttonBox")
        self.buttonBox.setOrientation(Qt.Horizontal)
        self.buttonBox.setStandardButtons(QDialogButtonBox.Abort|QDialogButtonBox.Ok)

        self.verticalLayout.addWidget(self.buttonBox)


        self.retranslateUi(SetupGreeter)
        self.buttonBox.accepted.connect(SetupGreeter.accept)
        self.buttonBox.rejected.connect(SetupGreeter.reject)

        QMetaObject.connectSlotsByName(SetupGreeter)
    # setupUi

    def retranslateUi(self, SetupGreeter):
        SetupGreeter.setWindowTitle(QCoreApplication.translate("SetupGreeter", u"Downloading Machine Learning Models", None))
        self.label_2.setText(QCoreApplication.translate("SetupGreeter", u"## Setting up Panel Cleaner", None))
        self.label.setText(QCoreApplication.translate("SetupGreeter", u"Before Panel Cleaner can begin, it requires the following machine learning models. Press OK to allow Panel Cleaner to automatically download these files to get started (Internet connection required, total space approx. 524 MiB)", None))
        self.label_9.setText(QCoreApplication.translate("SetupGreeter", u"Text Detection:", None))
        self.label_3.setText(QCoreApplication.translate("SetupGreeter", u"[https://github.com/zyddnys/manga-image-translator/releases](https://github.com/zyddnys/manga-image-translator/releases) \\\n"
"(only the comictextdetector file is needed)", None))
        self.label_4.setText(QCoreApplication.translate("SetupGreeter", u"Saved in:", None))
        self.label_text_detector_path.setText(QCoreApplication.translate("SetupGreeter", u"<text detection path>", None))
        self.label_10.setText(QCoreApplication.translate("SetupGreeter", u"Optical Character Recognition (OCR):", None))
        self.label_5.setText(QCoreApplication.translate("SetupGreeter", u"[https://huggingface.co/kha-white/manga-ocr-base/tree/main](https://huggingface.co/kha-white/manga-ocr-base/tree/main)", None))
        self.label_7.setText(QCoreApplication.translate("SetupGreeter", u"Saved in:", None))
        self.label_ocr_path.setText(QCoreApplication.translate("SetupGreeter", u"<ocr path>", None))
    # retranslateUi

