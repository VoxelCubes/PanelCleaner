# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'IssueReporter.ui'
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

from pcleaner.gui.CustomQ.CComboBox import CComboBox
from pcleaner.gui.log_viewer import LogViewer

class Ui_IssueReporter(object):
    def setupUi(self, IssueReporter):
        if not IssueReporter.objectName():
            IssueReporter.setObjectName(u"IssueReporter")
        IssueReporter.resize(1200, 700)
        self.verticalLayout = QVBoxLayout(IssueReporter)
        self.verticalLayout.setSpacing(6)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.label = QLabel(IssueReporter)
        self.label.setObjectName(u"label")

        self.verticalLayout.addWidget(self.label)

        self.horizontalLayout_2 = QHBoxLayout()
        self.horizontalLayout_2.setObjectName(u"horizontalLayout_2")
        self.label_logs_view = QLabel(IssueReporter)
        self.label_logs_view.setObjectName(u"label_logs_view")

        self.horizontalLayout_2.addWidget(self.label_logs_view)

        self.comboBox_sessions = CComboBox(IssueReporter)
        self.comboBox_sessions.setObjectName(u"comboBox_sessions")

        self.horizontalLayout_2.addWidget(self.comboBox_sessions)


        self.verticalLayout.addLayout(self.horizontalLayout_2)

        self.log_viewer = LogViewer(IssueReporter)
        self.log_viewer.setObjectName(u"log_viewer")
        self.log_viewer.setPlainText(u"")

        self.verticalLayout.addWidget(self.log_viewer)

        self.horizontalLayout_3 = QHBoxLayout()
        self.horizontalLayout_3.setSpacing(12)
        self.horizontalLayout_3.setObjectName(u"horizontalLayout_3")
        self.label_2 = QLabel(IssueReporter)
        self.label_2.setObjectName(u"label_2")
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.label_2.sizePolicy().hasHeightForWidth())
        self.label_2.setSizePolicy(sizePolicy)

        self.horizontalLayout_3.addWidget(self.label_2)

        self.label_log_path = QLabel(IssueReporter)
        self.label_log_path.setObjectName(u"label_log_path")
        self.label_log_path.setText(u"<log file path>")
        self.label_log_path.setTextInteractionFlags(Qt.LinksAccessibleByMouse|Qt.TextSelectableByKeyboard|Qt.TextSelectableByMouse)

        self.horizontalLayout_3.addWidget(self.label_log_path)


        self.verticalLayout.addLayout(self.horizontalLayout_3)

        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.label_name_hidden = QLabel(IssueReporter)
        self.label_name_hidden.setObjectName(u"label_name_hidden")
        self.label_name_hidden.setText(u"<name was hidden>")

        self.horizontalLayout.addWidget(self.label_name_hidden)

        self.horizontalSpacer = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout.addItem(self.horizontalSpacer)

        self.pushButton_clipboard = QPushButton(IssueReporter)
        self.pushButton_clipboard.setObjectName(u"pushButton_clipboard")
        icon = QIcon()
        iconThemeName = u"edit-copy"
        if QIcon.hasThemeIcon(iconThemeName):
            icon = QIcon.fromTheme(iconThemeName)
        else:
            icon.addFile(u".", QSize(), QIcon.Mode.Normal, QIcon.State.Off)

        self.pushButton_clipboard.setIcon(icon)

        self.horizontalLayout.addWidget(self.pushButton_clipboard)

        self.pushButton_open_issues = QPushButton(IssueReporter)
        self.pushButton_open_issues.setObjectName(u"pushButton_open_issues")
        icon1 = QIcon()
        iconThemeName = u"internet-services"
        if QIcon.hasThemeIcon(iconThemeName):
            icon1 = QIcon.fromTheme(iconThemeName)
        else:
            icon1.addFile(u".", QSize(), QIcon.Mode.Normal, QIcon.State.Off)

        self.pushButton_open_issues.setIcon(icon1)

        self.horizontalLayout.addWidget(self.pushButton_open_issues)

        self.pushButton_close = QPushButton(IssueReporter)
        self.pushButton_close.setObjectName(u"pushButton_close")
        icon2 = QIcon()
        iconThemeName = u"window-close"
        if QIcon.hasThemeIcon(iconThemeName):
            icon2 = QIcon.fromTheme(iconThemeName)
        else:
            icon2.addFile(u".", QSize(), QIcon.Mode.Normal, QIcon.State.Off)

        self.pushButton_close.setIcon(icon2)

        self.horizontalLayout.addWidget(self.pushButton_close)


        self.verticalLayout.addLayout(self.horizontalLayout)


        self.retranslateUi(IssueReporter)

        QMetaObject.connectSlotsByName(IssueReporter)
    # setupUi

    def retranslateUi(self, IssueReporter):
        IssueReporter.setWindowTitle(QCoreApplication.translate("IssueReporter", u"Report an Issue", None))
        self.label.setText(QCoreApplication.translate("IssueReporter", u"Consider including the log for the session that had an issue, if applicable.", None))
        self.label_logs_view.setText(QCoreApplication.translate("IssueReporter", u"View Logs:", None))
        self.label_2.setText(QCoreApplication.translate("IssueReporter", u"Log file is at:", None))
        self.pushButton_clipboard.setText(QCoreApplication.translate("IssueReporter", u"Copy to Clipboard", None))
        self.pushButton_open_issues.setText(QCoreApplication.translate("IssueReporter", u"Open Issue Tracker", None))
        self.pushButton_close.setText(QCoreApplication.translate("IssueReporter", u"Close", None))
    # retranslateUi

