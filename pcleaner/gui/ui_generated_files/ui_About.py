# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'About.ui'
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
from PySide6.QtWidgets import (QApplication, QFormLayout, QHBoxLayout, QLabel,
    QSizePolicy, QSpacerItem, QVBoxLayout, QWidget)

class Ui_About(object):
    def setupUi(self, About):
        if not About.objectName():
            About.setObjectName(u"About")
        About.resize(620, 265)
        self.horizontalLayout_2 = QHBoxLayout(About)
        self.horizontalLayout_2.setSpacing(6)
        self.horizontalLayout_2.setObjectName(u"horizontalLayout_2")
        self.horizontalLayout_2.setContentsMargins(20, 20, 20, 20)
        self.label_logo = QLabel(About)
        self.label_logo.setObjectName(u"label_logo")
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.label_logo.sizePolicy().hasHeightForWidth())
        self.label_logo.setSizePolicy(sizePolicy)
        self.label_logo.setMinimumSize(QSize(200, 200))
        self.label_logo.setMaximumSize(QSize(200, 200))
        self.label_logo.setScaledContents(True)

        self.horizontalLayout_2.addWidget(self.label_logo)

        self.horizontalSpacer_2 = QSpacerItem(40, 20, QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_2.addItem(self.horizontalSpacer_2)

        self.verticalLayout = QVBoxLayout()
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.label_2 = QLabel(About)
        self.label_2.setObjectName(u"label_2")
        self.label_2.setTextFormat(Qt.MarkdownText)

        self.verticalLayout.addWidget(self.label_2)

        self.formLayout = QFormLayout()
        self.formLayout.setObjectName(u"formLayout")
        self.formLayout.setContentsMargins(-1, 10, -1, -1)
        self.label_3 = QLabel(About)
        self.label_3.setObjectName(u"label_3")

        self.formLayout.setWidget(0, QFormLayout.LabelRole, self.label_3)

        self.label_version = QLabel(About)
        self.label_version.setObjectName(u"label_version")
        self.label_version.setText(u"<version>")

        self.formLayout.setWidget(0, QFormLayout.FieldRole, self.label_version)

        self.label_11 = QLabel(About)
        self.label_11.setObjectName(u"label_11")

        self.formLayout.setWidget(1, QFormLayout.LabelRole, self.label_11)

        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.label_copyright = QLabel(About)
        self.label_copyright.setObjectName(u"label_copyright")
        self.label_copyright.setText(u"<copyright>")

        self.horizontalLayout.addWidget(self.label_copyright)

        self.label_13 = QLabel(About)
        self.label_13.setObjectName(u"label_13")
        self.label_13.setText(u"Voxel")

        self.horizontalLayout.addWidget(self.label_13)

        self.horizontalSpacer = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout.addItem(self.horizontalSpacer)


        self.formLayout.setLayout(1, QFormLayout.FieldRole, self.horizontalLayout)

        self.label_5 = QLabel(About)
        self.label_5.setObjectName(u"label_5")

        self.formLayout.setWidget(2, QFormLayout.LabelRole, self.label_5)

        self.label_toolkit = QLabel(About)
        self.label_toolkit.setObjectName(u"label_toolkit")
        self.label_toolkit.setText(u"<toolkit>")

        self.formLayout.setWidget(2, QFormLayout.FieldRole, self.label_toolkit)

        self.label_7 = QLabel(About)
        self.label_7.setObjectName(u"label_7")

        self.formLayout.setWidget(3, QFormLayout.LabelRole, self.label_7)

        self.label_license = QLabel(About)
        self.label_license.setObjectName(u"label_license")
        self.label_license.setText(u"<html><head/><body><p><a href=\"open_license\"><span style=\" text-decoration: underline; color:#8419ff;\">GNU General Public License v3.0</span></a></p></body></html>")
        self.label_license.setTextInteractionFlags(Qt.LinksAccessibleByKeyboard|Qt.LinksAccessibleByMouse)

        self.formLayout.setWidget(3, QFormLayout.FieldRole, self.label_license)

        self.label_9 = QLabel(About)
        self.label_9.setObjectName(u"label_9")

        self.formLayout.setWidget(4, QFormLayout.LabelRole, self.label_9)

        self.label_10 = QLabel(About)
        self.label_10.setObjectName(u"label_10")
        self.label_10.setText(u"<html><head/><body><p><a href=\"https://github.com/VoxelCubes/PanelCleaner\"><span style=\" text-decoration: underline; color:#8419ff;\">GitHub</span></a></p></body></html>")
        self.label_10.setOpenExternalLinks(True)
        self.label_10.setTextInteractionFlags(Qt.LinksAccessibleByKeyboard|Qt.LinksAccessibleByMouse)

        self.formLayout.setWidget(4, QFormLayout.FieldRole, self.label_10)


        self.verticalLayout.addLayout(self.formLayout)


        self.horizontalLayout_2.addLayout(self.verticalLayout)


        self.retranslateUi(About)

        QMetaObject.connectSlotsByName(About)
    # setupUi

    def retranslateUi(self, About):
        About.setWindowTitle(QCoreApplication.translate("About", u"About Panel Cleaner", None))
        self.label_logo.setText("")
        self.label_2.setText(QCoreApplication.translate("About", u"# Panel Cleaner\n"
"\n"
"An AI-powered tool to clean manga panels.", None))
        self.label_3.setText(QCoreApplication.translate("About", u"Version:", None))
        self.label_11.setText(QCoreApplication.translate("About", u"Author:", None))
        self.label_5.setText(QCoreApplication.translate("About", u"Toolkit:", None))
        self.label_7.setText(QCoreApplication.translate("About", u"License:", None))
        self.label_9.setText(QCoreApplication.translate("About", u"Source code:", None))
    # retranslateUi

