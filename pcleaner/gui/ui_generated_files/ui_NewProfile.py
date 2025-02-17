# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'NewProfile.ui'
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
from PySide6.QtWidgets import (QAbstractButton, QApplication, QDialog, QDialogButtonBox,
    QFormLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QRadioButton, QSizePolicy, QSpacerItem,
    QVBoxLayout, QWidget)

class Ui_NewProfile(object):
    def setupUi(self, NewProfile):
        if not NewProfile.objectName():
            NewProfile.setObjectName(u"NewProfile")
        NewProfile.resize(556, 258)
        self.verticalLayout = QVBoxLayout(NewProfile)
        self.verticalLayout.setSpacing(12)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.label_default_protection_hint = QLabel(NewProfile)
        self.label_default_protection_hint.setObjectName(u"label_default_protection_hint")
        self.label_default_protection_hint.setWordWrap(True)

        self.verticalLayout.addWidget(self.label_default_protection_hint)

        self.formLayout = QFormLayout()
        self.formLayout.setObjectName(u"formLayout")
        self.radioButton_default_location = QRadioButton(NewProfile)
        self.radioButton_default_location.setObjectName(u"radioButton_default_location")
        self.radioButton_default_location.setChecked(True)

        self.formLayout.setWidget(1, QFormLayout.LabelRole, self.radioButton_default_location)

        self.radioButton_custom_location = QRadioButton(NewProfile)
        self.radioButton_custom_location.setObjectName(u"radioButton_custom_location")

        self.formLayout.setWidget(2, QFormLayout.LabelRole, self.radioButton_custom_location)

        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.lineEdit_location = QLineEdit(NewProfile)
        self.lineEdit_location.setObjectName(u"lineEdit_location")
        self.lineEdit_location.setEnabled(False)

        self.horizontalLayout.addWidget(self.lineEdit_location)

        self.pushButton_browse_location = QPushButton(NewProfile)
        self.pushButton_browse_location.setObjectName(u"pushButton_browse_location")
        self.pushButton_browse_location.setEnabled(False)
        icon = QIcon()
        iconThemeName = u"document-open-folder"
        if QIcon.hasThemeIcon(iconThemeName):
            icon = QIcon.fromTheme(iconThemeName)
        else:
            icon.addFile(u".", QSize(), QIcon.Mode.Normal, QIcon.State.Off)

        self.pushButton_browse_location.setIcon(icon)

        self.horizontalLayout.addWidget(self.pushButton_browse_location)


        self.formLayout.setLayout(2, QFormLayout.FieldRole, self.horizontalLayout)

        self.label = QLabel(NewProfile)
        self.label.setObjectName(u"label")

        self.formLayout.setWidget(0, QFormLayout.LabelRole, self.label)

        self.lineEdit_name = QLineEdit(NewProfile)
        self.lineEdit_name.setObjectName(u"lineEdit_name")

        self.formLayout.setWidget(0, QFormLayout.FieldRole, self.lineEdit_name)

        self.label_default_path = QLabel(NewProfile)
        self.label_default_path.setObjectName(u"label_default_path")
        self.label_default_path.setText(u"<default path>")
        self.label_default_path.setTextInteractionFlags(Qt.LinksAccessibleByMouse|Qt.TextSelectableByKeyboard|Qt.TextSelectableByMouse)

        self.formLayout.setWidget(1, QFormLayout.FieldRole, self.label_default_path)


        self.verticalLayout.addLayout(self.formLayout)

        self.verticalSpacer = QSpacerItem(20, 5, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.verticalLayout.addItem(self.verticalSpacer)

        self.horizontalLayout_2 = QHBoxLayout()
        self.horizontalLayout_2.setSpacing(2)
        self.horizontalLayout_2.setObjectName(u"horizontalLayout_2")
        self.label_warning_icon = QLabel(NewProfile)
        self.label_warning_icon.setObjectName(u"label_warning_icon")
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.label_warning_icon.sizePolicy().hasHeightForWidth())
        self.label_warning_icon.setSizePolicy(sizePolicy)
        self.label_warning_icon.setText(u"")

        self.horizontalLayout_2.addWidget(self.label_warning_icon)

        self.label_warning_message = QLabel(NewProfile)
        self.label_warning_message.setObjectName(u"label_warning_message")
        font = QFont()
        font.setItalic(True)
        self.label_warning_message.setFont(font)
        self.label_warning_message.setText(u"<some warning>")

        self.horizontalLayout_2.addWidget(self.label_warning_message)

        self.horizontalSpacer = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_2.addItem(self.horizontalSpacer)


        self.verticalLayout.addLayout(self.horizontalLayout_2)

        self.buttonBox = QDialogButtonBox(NewProfile)
        self.buttonBox.setObjectName(u"buttonBox")
        self.buttonBox.setOrientation(Qt.Horizontal)
        self.buttonBox.setStandardButtons(QDialogButtonBox.Cancel|QDialogButtonBox.Save)

        self.verticalLayout.addWidget(self.buttonBox)

        QWidget.setTabOrder(self.lineEdit_name, self.radioButton_default_location)
        QWidget.setTabOrder(self.radioButton_default_location, self.radioButton_custom_location)
        QWidget.setTabOrder(self.radioButton_custom_location, self.lineEdit_location)
        QWidget.setTabOrder(self.lineEdit_location, self.pushButton_browse_location)

        self.retranslateUi(NewProfile)
        self.buttonBox.accepted.connect(NewProfile.accept)
        self.buttonBox.rejected.connect(NewProfile.reject)
        self.radioButton_custom_location.toggled.connect(self.lineEdit_location.setEnabled)
        self.radioButton_custom_location.toggled.connect(self.pushButton_browse_location.setEnabled)

        QMetaObject.connectSlotsByName(NewProfile)
    # setupUi

    def retranslateUi(self, NewProfile):
        NewProfile.setWindowTitle(QCoreApplication.translate("NewProfile", u"New Profile", None))
        self.label_default_protection_hint.setText(QCoreApplication.translate("NewProfile", u"The default profile cannot be overwritten. Save a new profile with your changes:", None))
        self.radioButton_default_location.setText(QCoreApplication.translate("NewProfile", u"Use the default location", None))
        self.radioButton_custom_location.setText(QCoreApplication.translate("NewProfile", u"Use a different location:", None))
        self.pushButton_browse_location.setText("")
        self.label.setText(QCoreApplication.translate("NewProfile", u"Profile Name:", None))
    # retranslateUi

