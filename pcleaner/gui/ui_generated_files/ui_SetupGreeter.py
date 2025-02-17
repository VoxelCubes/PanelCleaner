# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'SetupGreeter.ui'
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
from PySide6.QtWidgets import (QApplication, QDialog, QFormLayout, QHBoxLayout,
    QLabel, QPushButton, QSizePolicy, QSpacerItem,
    QVBoxLayout, QWidget)

class Ui_SetupGreeter(object):
    def setupUi(self, SetupGreeter):
        if not SetupGreeter.objectName():
            SetupGreeter.setObjectName(u"SetupGreeter")
        SetupGreeter.resize(720, 490)
        SetupGreeter.setMinimumSize(QSize(600, 0))
        SetupGreeter.setModal(True)
        self.verticalLayout = QVBoxLayout(SetupGreeter)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.verticalLayout.setContentsMargins(-1, 20, -1, -1)
        self.label_2 = QLabel(SetupGreeter)
        self.label_2.setObjectName(u"label_2")
        self.label_2.setTextFormat(Qt.MarkdownText)

        self.verticalLayout.addWidget(self.label_2, 0, Qt.AlignHCenter)

        self.verticalSpacer_4 = QSpacerItem(20, 14, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed)

        self.verticalLayout.addItem(self.verticalSpacer_4)

        self.label = QLabel(SetupGreeter)
        self.label.setObjectName(u"label")
        self.label.setTextFormat(Qt.MarkdownText)
        self.label.setWordWrap(True)
        self.label.setOpenExternalLinks(True)
        self.label.setTextInteractionFlags(Qt.NoTextInteraction)

        self.verticalLayout.addWidget(self.label)

        self.verticalSpacer_5 = QSpacerItem(20, 14, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed)

        self.verticalLayout.addItem(self.verticalSpacer_5)

        self.formLayout = QFormLayout()
        self.formLayout.setObjectName(u"formLayout")
        self.formLayout.setFieldGrowthPolicy(QFormLayout.ExpandingFieldsGrow)
        self.formLayout.setRowWrapPolicy(QFormLayout.WrapLongRows)
        self.formLayout.setHorizontalSpacing(6)
        self.formLayout.setVerticalSpacing(6)
        self.label_9 = QLabel(SetupGreeter)
        self.label_9.setObjectName(u"label_9")

        self.formLayout.setWidget(0, QFormLayout.LabelRole, self.label_9)

        self.verticalLayout_2 = QVBoxLayout()
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.label_6 = QLabel(SetupGreeter)
        self.label_6.setObjectName(u"label_6")
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.label_6.sizePolicy().hasHeightForWidth())
        self.label_6.setSizePolicy(sizePolicy)
        self.label_6.setText(u"[https://github.com/zyddnys/manga-image-translator/releases](https://github.com/zyddnys/manga-image-translator/releases)")
        self.label_6.setTextFormat(Qt.MarkdownText)
        self.label_6.setWordWrap(True)
        self.label_6.setOpenExternalLinks(True)
        self.label_6.setTextInteractionFlags(Qt.TextBrowserInteraction)

        self.verticalLayout_2.addWidget(self.label_6)

        self.label_11 = QLabel(SetupGreeter)
        self.label_11.setObjectName(u"label_11")
        sizePolicy.setHeightForWidth(self.label_11.sizePolicy().hasHeightForWidth())
        self.label_11.setSizePolicy(sizePolicy)
        self.label_11.setTextFormat(Qt.MarkdownText)
        self.label_11.setWordWrap(True)
        self.label_11.setOpenExternalLinks(True)
        self.label_11.setTextInteractionFlags(Qt.TextBrowserInteraction)

        self.verticalLayout_2.addWidget(self.label_11)


        self.formLayout.setLayout(0, QFormLayout.FieldRole, self.verticalLayout_2)

        self.label_4 = QLabel(SetupGreeter)
        self.label_4.setObjectName(u"label_4")
        self.label_4.setTextFormat(Qt.PlainText)
        self.label_4.setWordWrap(True)
        self.label_4.setOpenExternalLinks(True)
        self.label_4.setTextInteractionFlags(Qt.NoTextInteraction)

        self.formLayout.setWidget(1, QFormLayout.LabelRole, self.label_4)

        self.label_text_detector_path = QLabel(SetupGreeter)
        self.label_text_detector_path.setObjectName(u"label_text_detector_path")
        sizePolicy1 = QSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        sizePolicy1.setHorizontalStretch(0)
        sizePolicy1.setVerticalStretch(0)
        sizePolicy1.setHeightForWidth(self.label_text_detector_path.sizePolicy().hasHeightForWidth())
        self.label_text_detector_path.setSizePolicy(sizePolicy1)
        self.label_text_detector_path.setText(u"<text detection path>")
        self.label_text_detector_path.setWordWrap(True)
        self.label_text_detector_path.setTextInteractionFlags(Qt.TextSelectableByKeyboard|Qt.TextSelectableByMouse)

        self.formLayout.setWidget(1, QFormLayout.FieldRole, self.label_text_detector_path)

        self.verticalSpacer_2 = QSpacerItem(20, 10, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Maximum)

        self.formLayout.setItem(2, QFormLayout.LabelRole, self.verticalSpacer_2)

        self.label_10 = QLabel(SetupGreeter)
        self.label_10.setObjectName(u"label_10")
        self.label_10.setWordWrap(True)

        self.formLayout.setWidget(3, QFormLayout.LabelRole, self.label_10)

        self.label_5 = QLabel(SetupGreeter)
        self.label_5.setObjectName(u"label_5")
        sizePolicy1.setHeightForWidth(self.label_5.sizePolicy().hasHeightForWidth())
        self.label_5.setSizePolicy(sizePolicy1)
        self.label_5.setText(u"[https://huggingface.co/kha-white/manga-ocr-base/tree/main](https://huggingface.co/kha-white/manga-ocr-base/tree/main)")
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
        sizePolicy1.setHeightForWidth(self.label_ocr_path.sizePolicy().hasHeightForWidth())
        self.label_ocr_path.setSizePolicy(sizePolicy1)
        self.label_ocr_path.setText(u"<ocr path>")
        self.label_ocr_path.setWordWrap(True)
        self.label_ocr_path.setTextInteractionFlags(Qt.TextSelectableByKeyboard|Qt.TextSelectableByMouse)

        self.formLayout.setWidget(4, QFormLayout.FieldRole, self.label_ocr_path)

        self.label_12 = QLabel(SetupGreeter)
        self.label_12.setObjectName(u"label_12")
        self.label_12.setWordWrap(True)

        self.formLayout.setWidget(6, QFormLayout.LabelRole, self.label_12)

        self.label_13 = QLabel(SetupGreeter)
        self.label_13.setObjectName(u"label_13")
        sizePolicy1.setHeightForWidth(self.label_13.sizePolicy().hasHeightForWidth())
        self.label_13.setSizePolicy(sizePolicy1)
        self.label_13.setText(u"[https://github.com/Sanster/models/releases/download/AnimeMangaInpainting/anime-manga-big-lama.pt](https://github.com/Sanster/models/releases/download/AnimeMangaInpainting/anime-manga-big-lama.pt)")
        self.label_13.setTextFormat(Qt.MarkdownText)
        self.label_13.setWordWrap(True)
        self.label_13.setOpenExternalLinks(True)
        self.label_13.setTextInteractionFlags(Qt.TextBrowserInteraction)

        self.formLayout.setWidget(6, QFormLayout.FieldRole, self.label_13)

        self.label_8 = QLabel(SetupGreeter)
        self.label_8.setObjectName(u"label_8")
        self.label_8.setTextFormat(Qt.PlainText)
        self.label_8.setWordWrap(True)
        self.label_8.setOpenExternalLinks(True)
        self.label_8.setTextInteractionFlags(Qt.NoTextInteraction)

        self.formLayout.setWidget(7, QFormLayout.LabelRole, self.label_8)

        self.label_inpainting_path = QLabel(SetupGreeter)
        self.label_inpainting_path.setObjectName(u"label_inpainting_path")
        sizePolicy1.setHeightForWidth(self.label_inpainting_path.sizePolicy().hasHeightForWidth())
        self.label_inpainting_path.setSizePolicy(sizePolicy1)
        self.label_inpainting_path.setText(u"<inpainting path>")
        self.label_inpainting_path.setWordWrap(True)
        self.label_inpainting_path.setTextInteractionFlags(Qt.TextSelectableByKeyboard|Qt.TextSelectableByMouse)

        self.formLayout.setWidget(7, QFormLayout.FieldRole, self.label_inpainting_path)

        self.verticalSpacer_3 = QSpacerItem(20, 10, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Maximum)

        self.formLayout.setItem(5, QFormLayout.LabelRole, self.verticalSpacer_3)


        self.verticalLayout.addLayout(self.formLayout)

        self.verticalSpacer = QSpacerItem(0, 0, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.verticalLayout.addItem(self.verticalSpacer)

        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setSpacing(6)
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.horizontalSpacer = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout.addItem(self.horizontalSpacer)

        self.pushButton_ok = QPushButton(SetupGreeter)
        self.pushButton_ok.setObjectName(u"pushButton_ok")
        icon = QIcon()
        iconThemeName = u"download"
        if QIcon.hasThemeIcon(iconThemeName):
            icon = QIcon.fromTheme(iconThemeName)
        else:
            icon.addFile(u".", QSize(), QIcon.Mode.Normal, QIcon.State.Off)

        self.pushButton_ok.setIcon(icon)
        self.pushButton_ok.setAutoDefault(False)

        self.horizontalLayout.addWidget(self.pushButton_ok)

        self.pushButton_abort = QPushButton(SetupGreeter)
        self.pushButton_abort.setObjectName(u"pushButton_abort")
        icon1 = QIcon()
        iconThemeName = u"dialog-cancel"
        if QIcon.hasThemeIcon(iconThemeName):
            icon1 = QIcon.fromTheme(iconThemeName)
        else:
            icon1.addFile(u".", QSize(), QIcon.Mode.Normal, QIcon.State.Off)

        self.pushButton_abort.setIcon(icon1)

        self.horizontalLayout.addWidget(self.pushButton_abort)


        self.verticalLayout.addLayout(self.horizontalLayout)


        self.retranslateUi(SetupGreeter)
        self.pushButton_ok.clicked.connect(SetupGreeter.accept)
        self.pushButton_abort.clicked.connect(SetupGreeter.reject)

        self.pushButton_ok.setDefault(False)


        QMetaObject.connectSlotsByName(SetupGreeter)
    # setupUi

    def retranslateUi(self, SetupGreeter):
        SetupGreeter.setWindowTitle(QCoreApplication.translate("SetupGreeter", u"Downloading Machine Learning Models", None))
        self.label_2.setText(QCoreApplication.translate("SetupGreeter", u"## Setting up Panel Cleaner", None))
        self.label.setText(QCoreApplication.translate("SetupGreeter", u"Before Panel Cleaner can begin, it requires the following machine learning models. Press **Automatically Download** to allow Panel Cleaner to download these files to get started (Internet connection required, total space approx. 700 MiB)", None))
        self.label_9.setText(QCoreApplication.translate("SetupGreeter", u"Text Detection:", None))
        self.label_11.setText(QCoreApplication.translate("SetupGreeter", u"(only the comictextdetector file is needed)", None))
        self.label_4.setText(QCoreApplication.translate("SetupGreeter", u"Saved in:", None))
        self.label_10.setText(QCoreApplication.translate("SetupGreeter", u"Optical Character Recognition (OCR):", None))
        self.label_7.setText(QCoreApplication.translate("SetupGreeter", u"Saved in:", None))
        self.label_12.setText(QCoreApplication.translate("SetupGreeter", u"Inpainting:", None))
        self.label_8.setText(QCoreApplication.translate("SetupGreeter", u"Saved in:", None))
        self.pushButton_ok.setText(QCoreApplication.translate("SetupGreeter", u"Automatically Download", None))
        self.pushButton_abort.setText(QCoreApplication.translate("SetupGreeter", u"Abort", None))
    # retranslateUi

