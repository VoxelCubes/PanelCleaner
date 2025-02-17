# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'ErrorDialog.ui'
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
    QPushButton, QSizePolicy, QSpacerItem, QVBoxLayout,
    QWidget)

from pcleaner.gui.log_viewer import LogViewer

class Ui_ErrorDialog(object):
    def setupUi(self, ErrorDialog):
        if not ErrorDialog.objectName():
            ErrorDialog.setObjectName(u"ErrorDialog")
        ErrorDialog.resize(1200, 700)
        ErrorDialog.setWindowTitle(u"Dialog")
        self.horizontalLayout_2 = QHBoxLayout(ErrorDialog)
        self.horizontalLayout_2.setSpacing(12)
        self.horizontalLayout_2.setObjectName(u"horizontalLayout_2")
        self.horizontalLayout_2.setContentsMargins(-1, 12, -1, -1)
        self.verticalLayout_2 = QVBoxLayout()
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.label_error_icon = QLabel(ErrorDialog)
        self.label_error_icon.setObjectName(u"label_error_icon")
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.label_error_icon.sizePolicy().hasHeightForWidth())
        self.label_error_icon.setSizePolicy(sizePolicy)
        self.label_error_icon.setMinimumSize(QSize(64, 64))
        self.label_error_icon.setMaximumSize(QSize(64, 64))
        self.label_error_icon.setText(u"<error icon>")

        self.verticalLayout_2.addWidget(self.label_error_icon)

        self.verticalSpacer = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.verticalLayout_2.addItem(self.verticalSpacer)


        self.horizontalLayout_2.addLayout(self.verticalLayout_2)

        self.verticalLayout = QVBoxLayout()
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.label_message = QLabel(ErrorDialog)
        self.label_message.setObjectName(u"label_message")
        self.label_message.setText(u"<error message>")

        self.verticalLayout.addWidget(self.label_message)

        self.log_viewer = LogViewer(ErrorDialog)
        self.log_viewer.setObjectName(u"log_viewer")

        self.verticalLayout.addWidget(self.log_viewer)

        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.label_name_hidden = QLabel(ErrorDialog)
        self.label_name_hidden.setObjectName(u"label_name_hidden")
        self.label_name_hidden.setText(u"<name was hidden>")

        self.horizontalLayout.addWidget(self.label_name_hidden)

        self.horizontalSpacer = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout.addItem(self.horizontalSpacer)

        self.pushButton_clipboard = QPushButton(ErrorDialog)
        self.pushButton_clipboard.setObjectName(u"pushButton_clipboard")
        icon = QIcon()
        iconThemeName = u"edit-copy"
        if QIcon.hasThemeIcon(iconThemeName):
            icon = QIcon.fromTheme(iconThemeName)
        else:
            icon.addFile(u".", QSize(), QIcon.Mode.Normal, QIcon.State.Off)

        self.pushButton_clipboard.setIcon(icon)

        self.horizontalLayout.addWidget(self.pushButton_clipboard)

        self.pushButton_open_issues = QPushButton(ErrorDialog)
        self.pushButton_open_issues.setObjectName(u"pushButton_open_issues")
        icon1 = QIcon()
        iconThemeName = u"internet-services"
        if QIcon.hasThemeIcon(iconThemeName):
            icon1 = QIcon.fromTheme(iconThemeName)
        else:
            icon1.addFile(u".", QSize(), QIcon.Mode.Normal, QIcon.State.Off)

        self.pushButton_open_issues.setIcon(icon1)

        self.horizontalLayout.addWidget(self.pushButton_open_issues)

        self.pushButton_kill = QPushButton(ErrorDialog)
        self.pushButton_kill.setObjectName(u"pushButton_kill")
        icon2 = QIcon(QIcon.fromTheme(u"process-stop"))
        self.pushButton_kill.setIcon(icon2)

        self.horizontalLayout.addWidget(self.pushButton_kill)

        self.pushButton_close = QPushButton(ErrorDialog)
        self.pushButton_close.setObjectName(u"pushButton_close")
        icon3 = QIcon()
        iconThemeName = u"window-close"
        if QIcon.hasThemeIcon(iconThemeName):
            icon3 = QIcon.fromTheme(iconThemeName)
        else:
            icon3.addFile(u".", QSize(), QIcon.Mode.Normal, QIcon.State.Off)

        self.pushButton_close.setIcon(icon3)

        self.horizontalLayout.addWidget(self.pushButton_close)


        self.verticalLayout.addLayout(self.horizontalLayout)


        self.horizontalLayout_2.addLayout(self.verticalLayout)


        self.retranslateUi(ErrorDialog)

        QMetaObject.connectSlotsByName(ErrorDialog)
    # setupUi

    def retranslateUi(self, ErrorDialog):
        self.pushButton_clipboard.setText(QCoreApplication.translate("ErrorDialog", u"Copy to Clipboard", None))
        self.pushButton_open_issues.setText(QCoreApplication.translate("ErrorDialog", u"Open Issue Tracker", None))
        self.pushButton_kill.setText(QCoreApplication.translate("ErrorDialog", u"Terminate Panel Cleaner", None))
        self.pushButton_close.setText(QCoreApplication.translate("ErrorDialog", u"Close", None))
        pass
    # retranslateUi

