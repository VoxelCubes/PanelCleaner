# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'FileManagerIntegration.ui'
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
from PySide6.QtWidgets import (QAbstractButton, QApplication, QCommandLinkButton, QDialog,
    QDialogButtonBox, QLabel, QSizePolicy, QSpacerItem,
    QVBoxLayout, QWidget)

class Ui_FileManagerExtension(object):
    def setupUi(self, FileManagerExtension):
        if not FileManagerExtension.objectName():
            FileManagerExtension.setObjectName(u"FileManagerExtension")
        FileManagerExtension.resize(650, 420)
        self.verticalLayout = QVBoxLayout(FileManagerExtension)
        self.verticalLayout.setSpacing(6)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.verticalLayout.setContentsMargins(12, 12, 12, -1)
        self.label = QLabel(FileManagerExtension)
        self.label.setObjectName(u"label")
        self.label.setTextFormat(Qt.MarkdownText)
        self.label.setWordWrap(True)

        self.verticalLayout.addWidget(self.label)

        self.verticalSpacer = QSpacerItem(20, 12, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.verticalLayout.addItem(self.verticalSpacer)

        self.commandLinkButton_install = QCommandLinkButton(FileManagerExtension)
        self.commandLinkButton_install.setObjectName(u"commandLinkButton_install")
        self.commandLinkButton_install.setText(u"<add shell extension>")
        self.commandLinkButton_install.setDescription(u"<adding to what program>")

        self.verticalLayout.addWidget(self.commandLinkButton_install)

        self.verticalSpacer_3 = QSpacerItem(20, 12, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed)

        self.verticalLayout.addItem(self.verticalSpacer_3)

        self.commandLinkButton_uninstall = QCommandLinkButton(FileManagerExtension)
        self.commandLinkButton_uninstall.setObjectName(u"commandLinkButton_uninstall")
        self.commandLinkButton_uninstall.setText(u"<remove shell extension>")
        icon = QIcon()
        iconThemeName = u"edit-delete"
        if QIcon.hasThemeIcon(iconThemeName):
            icon = QIcon.fromTheme(iconThemeName)
        else:
            icon.addFile(u".", QSize(), QIcon.Mode.Normal, QIcon.State.Off)

        self.commandLinkButton_uninstall.setIcon(icon)
        self.commandLinkButton_uninstall.setDescription(u"<removing from what program>")

        self.verticalLayout.addWidget(self.commandLinkButton_uninstall)

        self.verticalSpacer_2 = QSpacerItem(20, 12, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.verticalLayout.addItem(self.verticalSpacer_2)

        self.buttonBox = QDialogButtonBox(FileManagerExtension)
        self.buttonBox.setObjectName(u"buttonBox")
        self.buttonBox.setStandardButtons(QDialogButtonBox.Close)

        self.verticalLayout.addWidget(self.buttonBox)


        self.retranslateUi(FileManagerExtension)
        self.buttonBox.rejected.connect(FileManagerExtension.reject)

        QMetaObject.connectSlotsByName(FileManagerExtension)
    # setupUi

    def retranslateUi(self, FileManagerExtension):
        FileManagerExtension.setWindowTitle(QCoreApplication.translate("FileManagerExtension", u"File Manager Extension", None))
        self.label.setText(QCoreApplication.translate("FileManagerExtension", u"### Add or Remove Integration with your File Browser\n"
"\n"
"This feature adds a menu option to your file browser's context menu (which appears when you right-click) for folders or image files.\n"
"\n"
"It allows you to use Panel Cleaner directly from the file browser, eliminating the need to open the application separately.\n"
"\n"
"By default, this uses the built-in profile. However, you can change this default setting by choosing **Profile** and then **Set Default** from the application's menu bar.", None))
    # retranslateUi

