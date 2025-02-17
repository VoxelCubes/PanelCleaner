# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'PostActionRunner.ui'
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
from PySide6.QtWidgets import (QApplication, QDialog, QFrame, QHBoxLayout,
    QLCDNumber, QLabel, QPlainTextEdit, QPushButton,
    QSizePolicy, QSpacerItem, QVBoxLayout, QWidget)

class Ui_PostActionRunner(object):
    def setupUi(self, PostActionRunner):
        if not PostActionRunner.objectName():
            PostActionRunner.setObjectName(u"PostActionRunner")
        PostActionRunner.resize(600, 400)
        self.verticalLayout_3 = QVBoxLayout(PostActionRunner)
        self.verticalLayout_3.setSpacing(12)
        self.verticalLayout_3.setObjectName(u"verticalLayout_3")
        self.horizontalLayout_2 = QHBoxLayout()
        self.horizontalLayout_2.setObjectName(u"horizontalLayout_2")
        self.label_action_icon = QLabel(PostActionRunner)
        self.label_action_icon.setObjectName(u"label_action_icon")
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.label_action_icon.sizePolicy().hasHeightForWidth())
        self.label_action_icon.setSizePolicy(sizePolicy)
        self.label_action_icon.setMinimumSize(QSize(64, 64))
        self.label_action_icon.setText(u"<icon>")

        self.horizontalLayout_2.addWidget(self.label_action_icon)

        self.verticalLayout_4 = QVBoxLayout()
        self.verticalLayout_4.setSpacing(4)
        self.verticalLayout_4.setObjectName(u"verticalLayout_4")
        self.verticalLayout_4.setContentsMargins(-1, -1, 18, -1)
        self.verticalSpacer_2 = QSpacerItem(20, 0, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.verticalLayout_4.addItem(self.verticalSpacer_2)

        self.label_what = QLabel(PostActionRunner)
        self.label_what.setObjectName(u"label_what")
        self.label_what.setText(u"<doing what>")

        self.verticalLayout_4.addWidget(self.label_what)

        self.label_remaining_time = QLabel(PostActionRunner)
        self.label_remaining_time.setObjectName(u"label_remaining_time")
        self.label_remaining_time.setText(u"<remaining time>")

        self.verticalLayout_4.addWidget(self.label_remaining_time)

        self.verticalSpacer_3 = QSpacerItem(20, 0, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.verticalLayout_4.addItem(self.verticalSpacer_3)


        self.horizontalLayout_2.addLayout(self.verticalLayout_4)

        self.lcdNumber_shutdown = QLCDNumber(PostActionRunner)
        self.lcdNumber_shutdown.setObjectName(u"lcdNumber_shutdown")
        sizePolicy1 = QSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        sizePolicy1.setHorizontalStretch(0)
        sizePolicy1.setVerticalStretch(0)
        sizePolicy1.setHeightForWidth(self.lcdNumber_shutdown.sizePolicy().hasHeightForWidth())
        self.lcdNumber_shutdown.setSizePolicy(sizePolicy1)
        self.lcdNumber_shutdown.setMinimumSize(QSize(0, 48))
        self.lcdNumber_shutdown.setFrameShape(QFrame.NoFrame)
        self.lcdNumber_shutdown.setDigitCount(5)
        self.lcdNumber_shutdown.setSegmentStyle(QLCDNumber.Flat)

        self.horizontalLayout_2.addWidget(self.lcdNumber_shutdown)

        self.horizontalSpacer = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_2.addItem(self.horizontalSpacer)

        self.horizontalLayout_2.setStretch(3, 6)

        self.verticalLayout_3.addLayout(self.horizontalLayout_2)

        self.horizontalLayout_4 = QHBoxLayout()
        self.horizontalLayout_4.setSpacing(4)
        self.horizontalLayout_4.setObjectName(u"horizontalLayout_4")
        self.label_error_icon = QLabel(PostActionRunner)
        self.label_error_icon.setObjectName(u"label_error_icon")
        sizePolicy.setHeightForWidth(self.label_error_icon.sizePolicy().hasHeightForWidth())
        self.label_error_icon.setSizePolicy(sizePolicy)
        self.label_error_icon.setMinimumSize(QSize(16, 16))
        self.label_error_icon.setText(u"<icon>")

        self.horizontalLayout_4.addWidget(self.label_error_icon)

        self.label_error = QLabel(PostActionRunner)
        self.label_error.setObjectName(u"label_error")
        font = QFont()
        font.setItalic(True)
        self.label_error.setFont(font)

        self.horizontalLayout_4.addWidget(self.label_error)


        self.verticalLayout_3.addLayout(self.horizontalLayout_4)

        self.verticalSpacer = QSpacerItem(20, 6, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed)

        self.verticalLayout_3.addItem(self.verticalSpacer)

        self.label_2 = QLabel(PostActionRunner)
        self.label_2.setObjectName(u"label_2")
        font1 = QFont()
        font1.setBold(True)
        self.label_2.setFont(font1)

        self.verticalLayout_3.addWidget(self.label_2)

        self.plainTextEdit_command = QPlainTextEdit(PostActionRunner)
        self.plainTextEdit_command.setObjectName(u"plainTextEdit_command")
        self.plainTextEdit_command.setPlainText(u"")
        self.plainTextEdit_command.setTextInteractionFlags(Qt.TextEditorInteraction)

        self.verticalLayout_3.addWidget(self.plainTextEdit_command)

        self.horizontalLayout_3 = QHBoxLayout()
        self.horizontalLayout_3.setSpacing(6)
        self.horizontalLayout_3.setObjectName(u"horizontalLayout_3")
        self.horizontalSpacer_3 = QSpacerItem(0, 0, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_3.addItem(self.horizontalSpacer_3)

        self.verticalLayout_5 = QVBoxLayout()
        self.verticalLayout_5.setObjectName(u"verticalLayout_5")
        self.pushButton_again = QPushButton(PostActionRunner)
        self.pushButton_again.setObjectName(u"pushButton_again")
        icon = QIcon(QIcon.fromTheme(u"debug-run"))
        self.pushButton_again.setIcon(icon)

        self.verticalLayout_5.addWidget(self.pushButton_again)

        self.pushButton_skip_countdown = QPushButton(PostActionRunner)
        self.pushButton_skip_countdown.setObjectName(u"pushButton_skip_countdown")
        icon1 = QIcon(QIcon.fromTheme(u"media-skip-forward"))
        self.pushButton_skip_countdown.setIcon(icon1)

        self.verticalLayout_5.addWidget(self.pushButton_skip_countdown)


        self.horizontalLayout_3.addLayout(self.verticalLayout_5)

        self.verticalLayout = QVBoxLayout()
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.pushButton_resume = QPushButton(PostActionRunner)
        self.pushButton_resume.setObjectName(u"pushButton_resume")
        sizePolicy2 = QSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed)
        sizePolicy2.setHorizontalStretch(0)
        sizePolicy2.setVerticalStretch(0)
        sizePolicy2.setHeightForWidth(self.pushButton_resume.sizePolicy().hasHeightForWidth())
        self.pushButton_resume.setSizePolicy(sizePolicy2)
        icon2 = QIcon(QIcon.fromTheme(u"media-playback-start"))
        self.pushButton_resume.setIcon(icon2)

        self.verticalLayout.addWidget(self.pushButton_resume)

        self.pushButton_pause = QPushButton(PostActionRunner)
        self.pushButton_pause.setObjectName(u"pushButton_pause")
        icon3 = QIcon(QIcon.fromTheme(u"media-playback-pause"))
        self.pushButton_pause.setIcon(icon3)

        self.verticalLayout.addWidget(self.pushButton_pause)


        self.horizontalLayout_3.addLayout(self.verticalLayout)

        self.pushButton_close = QPushButton(PostActionRunner)
        self.pushButton_close.setObjectName(u"pushButton_close")
        icon4 = QIcon(QIcon.fromTheme(u"window-close"))
        self.pushButton_close.setIcon(icon4)

        self.horizontalLayout_3.addWidget(self.pushButton_close)

        self.verticalLayout_2 = QVBoxLayout()
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.pushButton_cancel_action = QPushButton(PostActionRunner)
        self.pushButton_cancel_action.setObjectName(u"pushButton_cancel_action")
        icon5 = QIcon(QIcon.fromTheme(u"dialog-cancel"))
        self.pushButton_cancel_action.setIcon(icon5)

        self.verticalLayout_2.addWidget(self.pushButton_cancel_action)

        self.pushButton_cancel_shutdown = QPushButton(PostActionRunner)
        self.pushButton_cancel_shutdown.setObjectName(u"pushButton_cancel_shutdown")
        icon6 = QIcon()
        iconThemeName = u"dialog-cancel"
        if QIcon.hasThemeIcon(iconThemeName):
            icon6 = QIcon.fromTheme(iconThemeName)
        else:
            icon6.addFile(u".", QSize(), QIcon.Mode.Normal, QIcon.State.Off)

        self.pushButton_cancel_shutdown.setIcon(icon6)

        self.verticalLayout_2.addWidget(self.pushButton_cancel_shutdown)


        self.horizontalLayout_3.addLayout(self.verticalLayout_2)


        self.verticalLayout_3.addLayout(self.horizontalLayout_3)

        self.verticalLayout_3.setStretch(4, 1)

        self.retranslateUi(PostActionRunner)

        QMetaObject.connectSlotsByName(PostActionRunner)
    # setupUi

    def retranslateUi(self, PostActionRunner):
        PostActionRunner.setWindowTitle(QCoreApplication.translate("PostActionRunner", u"Post-Action Runner", None))
        self.label_error.setText(QCoreApplication.translate("PostActionRunner", u"An error occurred during the process.", None))
        self.label_2.setText(QCoreApplication.translate("PostActionRunner", u"Full Command:", None))
        self.pushButton_again.setText(QCoreApplication.translate("PostActionRunner", u"Run Again", None))
        self.pushButton_skip_countdown.setText(QCoreApplication.translate("PostActionRunner", u"Skip Countdown", None))
        self.pushButton_resume.setText(QCoreApplication.translate("PostActionRunner", u"Resume Countdown", None))
        self.pushButton_pause.setText(QCoreApplication.translate("PostActionRunner", u"Pause Countdown", None))
        self.pushButton_close.setText(QCoreApplication.translate("PostActionRunner", u"Close", None))
        self.pushButton_cancel_action.setText(QCoreApplication.translate("PostActionRunner", u"Cancel Action", None))
        self.pushButton_cancel_shutdown.setText(QCoreApplication.translate("PostActionRunner", u"Cancel Shutdown", None))
    # retranslateUi

