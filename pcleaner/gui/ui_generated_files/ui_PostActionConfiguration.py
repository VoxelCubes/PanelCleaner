# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'PostActionConfiguration.ui'
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
from PySide6.QtWidgets import (QAbstractButton, QAbstractItemView, QAbstractSpinBox, QApplication,
    QCheckBox, QDialog, QDialogButtonBox, QFormLayout,
    QHBoxLayout, QHeaderView, QLabel, QLineEdit,
    QPushButton, QSizePolicy, QSpacerItem, QSpinBox,
    QTableWidgetItem, QVBoxLayout, QWidget)

from pcleaner.gui.CustomQ.CTableWidget import CTableWidget
from pcleaner.gui.CustomQ.CTooltipLabel import CTooltipLabel

class Ui_PostActionConfiguration(object):
    def setupUi(self, PostActionConfiguration):
        if not PostActionConfiguration.objectName():
            PostActionConfiguration.setObjectName(u"PostActionConfiguration")
        PostActionConfiguration.resize(800, 640)
        self.verticalLayout = QVBoxLayout(PostActionConfiguration)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.checkBox_remember_action = QCheckBox(PostActionConfiguration)
        self.checkBox_remember_action.setObjectName(u"checkBox_remember_action")

        self.verticalLayout.addWidget(self.checkBox_remember_action)

        self.horizontalLayout_8 = QHBoxLayout()
        self.horizontalLayout_8.setObjectName(u"horizontalLayout_8")
        self.label_13 = QLabel(PostActionConfiguration)
        self.label_13.setObjectName(u"label_13")

        self.horizontalLayout_8.addWidget(self.label_13)

        self.spinBox_wait_time = QSpinBox(PostActionConfiguration)
        self.spinBox_wait_time.setObjectName(u"spinBox_wait_time")
        self.spinBox_wait_time.setMaximum(86400)
        self.spinBox_wait_time.setStepType(QAbstractSpinBox.AdaptiveDecimalStepType)

        self.horizontalLayout_8.addWidget(self.spinBox_wait_time)

        self.label_review_output_help_7 = CTooltipLabel(PostActionConfiguration)
        self.label_review_output_help_7.setObjectName(u"label_review_output_help_7")
        self.label_review_output_help_7.setToolTipDuration(-1)
        self.label_review_output_help_7.setText(u"<helper>")

        self.horizontalLayout_8.addWidget(self.label_review_output_help_7)

        self.horizontalSpacer_2 = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_8.addItem(self.horizontalSpacer_2)


        self.verticalLayout.addLayout(self.horizontalLayout_8)

        self.verticalSpacer_2 = QSpacerItem(20, 18, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed)

        self.verticalLayout.addItem(self.verticalSpacer_2)

        self.formLayout = QFormLayout()
        self.formLayout.setObjectName(u"formLayout")
        self.formLayout.setContentsMargins(-1, 0, -1, 6)
        self.label = QLabel(PostActionConfiguration)
        self.label.setObjectName(u"label")

        self.formLayout.setWidget(0, QFormLayout.LabelRole, self.label)

        self.lineEdit_shutdown = QLineEdit(PostActionConfiguration)
        self.lineEdit_shutdown.setObjectName(u"lineEdit_shutdown")

        self.formLayout.setWidget(0, QFormLayout.FieldRole, self.lineEdit_shutdown)


        self.verticalLayout.addLayout(self.formLayout)

        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.label_2 = QLabel(PostActionConfiguration)
        self.label_2.setObjectName(u"label_2")

        self.horizontalLayout.addWidget(self.label_2)

        self.horizontalSpacer = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout.addItem(self.horizontalSpacer)

        self.pushButton_row_up = QPushButton(PostActionConfiguration)
        self.pushButton_row_up.setObjectName(u"pushButton_row_up")
        self.pushButton_row_up.setText(u"")
        icon = QIcon()
        iconThemeName = u"arrow-up"
        if QIcon.hasThemeIcon(iconThemeName):
            icon = QIcon.fromTheme(iconThemeName)
        else:
            icon.addFile(u".", QSize(), QIcon.Mode.Normal, QIcon.State.Off)

        self.pushButton_row_up.setIcon(icon)
        self.pushButton_row_up.setFlat(True)

        self.horizontalLayout.addWidget(self.pushButton_row_up)

        self.pushButton_row_down = QPushButton(PostActionConfiguration)
        self.pushButton_row_down.setObjectName(u"pushButton_row_down")
        self.pushButton_row_down.setText(u"")
        icon1 = QIcon()
        iconThemeName = u"arrow-down"
        if QIcon.hasThemeIcon(iconThemeName):
            icon1 = QIcon.fromTheme(iconThemeName)
        else:
            icon1.addFile(u".", QSize(), QIcon.Mode.Normal, QIcon.State.Off)

        self.pushButton_row_down.setIcon(icon1)
        self.pushButton_row_down.setFlat(True)

        self.horizontalLayout.addWidget(self.pushButton_row_down)

        self.pushButton_new = QPushButton(PostActionConfiguration)
        self.pushButton_new.setObjectName(u"pushButton_new")
        icon2 = QIcon()
        iconThemeName = u"list-add"
        if QIcon.hasThemeIcon(iconThemeName):
            icon2 = QIcon.fromTheme(iconThemeName)
        else:
            icon2.addFile(u".", QSize(), QIcon.Mode.Normal, QIcon.State.Off)

        self.pushButton_new.setIcon(icon2)
        self.pushButton_new.setFlat(True)

        self.horizontalLayout.addWidget(self.pushButton_new)

        self.pushButton_delete = QPushButton(PostActionConfiguration)
        self.pushButton_delete.setObjectName(u"pushButton_delete")
        icon3 = QIcon()
        iconThemeName = u"edit-delete"
        if QIcon.hasThemeIcon(iconThemeName):
            icon3 = QIcon.fromTheme(iconThemeName)
        else:
            icon3.addFile(u".", QSize(), QIcon.Mode.Normal, QIcon.State.Off)

        self.pushButton_delete.setIcon(icon3)
        self.pushButton_delete.setFlat(True)

        self.horizontalLayout.addWidget(self.pushButton_delete)


        self.verticalLayout.addLayout(self.horizontalLayout)

        self.tableWidget_commands = CTableWidget(PostActionConfiguration)
        if (self.tableWidget_commands.columnCount() < 2):
            self.tableWidget_commands.setColumnCount(2)
        __qtablewidgetitem = QTableWidgetItem()
        self.tableWidget_commands.setHorizontalHeaderItem(0, __qtablewidgetitem)
        __qtablewidgetitem1 = QTableWidgetItem()
        self.tableWidget_commands.setHorizontalHeaderItem(1, __qtablewidgetitem1)
        self.tableWidget_commands.setObjectName(u"tableWidget_commands")
        self.tableWidget_commands.setEditTriggers(QAbstractItemView.AllEditTriggers)
        self.tableWidget_commands.setProperty(u"showDropIndicator", False)
        self.tableWidget_commands.setDragDropOverwriteMode(False)
        self.tableWidget_commands.setAlternatingRowColors(True)
        self.tableWidget_commands.setSelectionMode(QAbstractItemView.SingleSelection)
        self.tableWidget_commands.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.tableWidget_commands.horizontalHeader().setDefaultSectionSize(200)
        self.tableWidget_commands.horizontalHeader().setStretchLastSection(True)

        self.verticalLayout.addWidget(self.tableWidget_commands)

        self.horizontalLayout_10 = QHBoxLayout()
        self.horizontalLayout_10.setObjectName(u"horizontalLayout_10")
        self.checkBox_cancel_on_error = QCheckBox(PostActionConfiguration)
        self.checkBox_cancel_on_error.setObjectName(u"checkBox_cancel_on_error")
        self.checkBox_cancel_on_error.setChecked(False)

        self.horizontalLayout_10.addWidget(self.checkBox_cancel_on_error)

        self.label_review_output_help_6 = CTooltipLabel(PostActionConfiguration)
        self.label_review_output_help_6.setObjectName(u"label_review_output_help_6")
        self.label_review_output_help_6.setToolTipDuration(-1)
        self.label_review_output_help_6.setText(u"<helper>")

        self.horizontalLayout_10.addWidget(self.label_review_output_help_6)

        self.horizontalSpacer_9 = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_10.addItem(self.horizontalSpacer_9)


        self.verticalLayout.addLayout(self.horizontalLayout_10)

        self.verticalSpacer = QSpacerItem(20, 18, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed)

        self.verticalLayout.addItem(self.verticalSpacer)

        self.label_3 = QLabel(PostActionConfiguration)
        self.label_3.setObjectName(u"label_3")
        font = QFont()
        font.setBold(True)
        self.label_3.setFont(font)

        self.verticalLayout.addWidget(self.label_3)

        self.horizontalLayout_7 = QHBoxLayout()
        self.horizontalLayout_7.setSpacing(24)
        self.horizontalLayout_7.setObjectName(u"horizontalLayout_7")
        self.horizontalLayout_7.setContentsMargins(-1, 6, -1, 6)
        self.formLayout_2 = QFormLayout()
        self.formLayout_2.setObjectName(u"formLayout_2")
        self.label_4 = QLabel(PostActionConfiguration)
        self.label_4.setObjectName(u"label_4")

        self.formLayout_2.setWidget(0, QFormLayout.LabelRole, self.label_4)

        self.horizontalLayout_2 = QHBoxLayout()
        self.horizontalLayout_2.setObjectName(u"horizontalLayout_2")
        self.label_5 = QLabel(PostActionConfiguration)
        self.label_5.setObjectName(u"label_5")
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.label_5.sizePolicy().hasHeightForWidth())
        self.label_5.setSizePolicy(sizePolicy)

        self.horizontalLayout_2.addWidget(self.label_5)

        self.label_review_output_help = CTooltipLabel(PostActionConfiguration)
        self.label_review_output_help.setObjectName(u"label_review_output_help")
        self.label_review_output_help.setToolTipDuration(-1)
        self.label_review_output_help.setText(u"<helper>")

        self.horizontalLayout_2.addWidget(self.label_review_output_help)

        self.horizontalSpacer_3 = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_2.addItem(self.horizontalSpacer_3)


        self.formLayout_2.setLayout(0, QFormLayout.FieldRole, self.horizontalLayout_2)

        self.inputDirectoryIesLabel = QLabel(PostActionConfiguration)
        self.inputDirectoryIesLabel.setObjectName(u"inputDirectoryIesLabel")

        self.formLayout_2.setWidget(1, QFormLayout.LabelRole, self.inputDirectoryIesLabel)

        self.horizontalLayout_3 = QHBoxLayout()
        self.horizontalLayout_3.setObjectName(u"horizontalLayout_3")
        self.label_12 = QLabel(PostActionConfiguration)
        self.label_12.setObjectName(u"label_12")
        sizePolicy.setHeightForWidth(self.label_12.sizePolicy().hasHeightForWidth())
        self.label_12.setSizePolicy(sizePolicy)

        self.horizontalLayout_3.addWidget(self.label_12)

        self.label_review_output_help_2 = CTooltipLabel(PostActionConfiguration)
        self.label_review_output_help_2.setObjectName(u"label_review_output_help_2")
        self.label_review_output_help_2.setToolTipDuration(-1)
        self.label_review_output_help_2.setText(u"<helper>")

        self.horizontalLayout_3.addWidget(self.label_review_output_help_2)

        self.horizontalSpacer_4 = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_3.addItem(self.horizontalSpacer_4)


        self.formLayout_2.setLayout(1, QFormLayout.FieldRole, self.horizontalLayout_3)


        self.horizontalLayout_7.addLayout(self.formLayout_2)

        self.formLayout_3 = QFormLayout()
        self.formLayout_3.setObjectName(u"formLayout_3")
        self.label_6 = QLabel(PostActionConfiguration)
        self.label_6.setObjectName(u"label_6")

        self.formLayout_3.setWidget(0, QFormLayout.LabelRole, self.label_6)

        self.horizontalLayout_4 = QHBoxLayout()
        self.horizontalLayout_4.setObjectName(u"horizontalLayout_4")
        self.label_9 = QLabel(PostActionConfiguration)
        self.label_9.setObjectName(u"label_9")
        sizePolicy.setHeightForWidth(self.label_9.sizePolicy().hasHeightForWidth())
        self.label_9.setSizePolicy(sizePolicy)

        self.horizontalLayout_4.addWidget(self.label_9)

        self.label_review_output_help_4 = CTooltipLabel(PostActionConfiguration)
        self.label_review_output_help_4.setObjectName(u"label_review_output_help_4")
        self.label_review_output_help_4.setToolTipDuration(-1)
        self.label_review_output_help_4.setText(u"<helper>")

        self.horizontalLayout_4.addWidget(self.label_review_output_help_4)

        self.horizontalSpacer_5 = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_4.addItem(self.horizontalSpacer_5)


        self.formLayout_3.setLayout(0, QFormLayout.FieldRole, self.horizontalLayout_4)

        self.label_10 = QLabel(PostActionConfiguration)
        self.label_10.setObjectName(u"label_10")

        self.formLayout_3.setWidget(1, QFormLayout.LabelRole, self.label_10)

        self.horizontalLayout_5 = QHBoxLayout()
        self.horizontalLayout_5.setObjectName(u"horizontalLayout_5")
        self.label_11 = QLabel(PostActionConfiguration)
        self.label_11.setObjectName(u"label_11")
        sizePolicy.setHeightForWidth(self.label_11.sizePolicy().hasHeightForWidth())
        self.label_11.setSizePolicy(sizePolicy)

        self.horizontalLayout_5.addWidget(self.label_11)

        self.label_review_output_help_5 = CTooltipLabel(PostActionConfiguration)
        self.label_review_output_help_5.setObjectName(u"label_review_output_help_5")
        self.label_review_output_help_5.setToolTipDuration(-1)
        self.label_review_output_help_5.setText(u"<helper>")

        self.horizontalLayout_5.addWidget(self.label_review_output_help_5)

        self.horizontalSpacer_6 = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_5.addItem(self.horizontalSpacer_6)


        self.formLayout_3.setLayout(1, QFormLayout.FieldRole, self.horizontalLayout_5)


        self.horizontalLayout_7.addLayout(self.formLayout_3)

        self.formLayout_4 = QFormLayout()
        self.formLayout_4.setObjectName(u"formLayout_4")
        self.label_8 = QLabel(PostActionConfiguration)
        self.label_8.setObjectName(u"label_8")

        self.formLayout_4.setWidget(0, QFormLayout.LabelRole, self.label_8)

        self.horizontalLayout_6 = QHBoxLayout()
        self.horizontalLayout_6.setObjectName(u"horizontalLayout_6")
        self.label_7 = QLabel(PostActionConfiguration)
        self.label_7.setObjectName(u"label_7")
        sizePolicy.setHeightForWidth(self.label_7.sizePolicy().hasHeightForWidth())
        self.label_7.setSizePolicy(sizePolicy)

        self.horizontalLayout_6.addWidget(self.label_7)

        self.label_review_output_help_3 = CTooltipLabel(PostActionConfiguration)
        self.label_review_output_help_3.setObjectName(u"label_review_output_help_3")
        self.label_review_output_help_3.setToolTipDuration(-1)
        self.label_review_output_help_3.setText(u"<helper>")

        self.horizontalLayout_6.addWidget(self.label_review_output_help_3)

        self.horizontalSpacer_7 = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_6.addItem(self.horizontalSpacer_7)


        self.formLayout_4.setLayout(0, QFormLayout.FieldRole, self.horizontalLayout_6)


        self.horizontalLayout_7.addLayout(self.formLayout_4)


        self.verticalLayout.addLayout(self.horizontalLayout_7)

        self.horizontalLayout_9 = QHBoxLayout()
        self.horizontalLayout_9.setObjectName(u"horizontalLayout_9")
        self.label_warning_icon = QLabel(PostActionConfiguration)
        self.label_warning_icon.setObjectName(u"label_warning_icon")
        self.label_warning_icon.setText(u"<warning icon>")

        self.horizontalLayout_9.addWidget(self.label_warning_icon)

        self.label_warning = QLabel(PostActionConfiguration)
        self.label_warning.setObjectName(u"label_warning")
        font1 = QFont()
        font1.setItalic(True)
        self.label_warning.setFont(font1)
        self.label_warning.setText(u"<warning>")

        self.horizontalLayout_9.addWidget(self.label_warning)

        self.horizontalSpacer_8 = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_9.addItem(self.horizontalSpacer_8)

        self.buttonBox = QDialogButtonBox(PostActionConfiguration)
        self.buttonBox.setObjectName(u"buttonBox")
        self.buttonBox.setOrientation(Qt.Horizontal)
        self.buttonBox.setStandardButtons(QDialogButtonBox.Cancel|QDialogButtonBox.Ok)

        self.horizontalLayout_9.addWidget(self.buttonBox)

        self.horizontalLayout_9.setStretch(2, 1)

        self.verticalLayout.addLayout(self.horizontalLayout_9)


        self.retranslateUi(PostActionConfiguration)
        self.buttonBox.accepted.connect(PostActionConfiguration.accept)
        self.buttonBox.rejected.connect(PostActionConfiguration.reject)

        QMetaObject.connectSlotsByName(PostActionConfiguration)
    # setupUi

    def retranslateUi(self, PostActionConfiguration):
        PostActionConfiguration.setWindowTitle(QCoreApplication.translate("PostActionConfiguration", u"Configure Post-Run Actions", None))
        self.checkBox_remember_action.setText(QCoreApplication.translate("PostActionConfiguration", u"Always perform the action after processing", None))
        self.label_13.setText(QCoreApplication.translate("PostActionConfiguration", u"Wait before performing an action:", None))
        self.spinBox_wait_time.setSuffix(QCoreApplication.translate("PostActionConfiguration", u" s", None))
#if QT_CONFIG(tooltip)
        self.label_review_output_help_7.setToolTip(QCoreApplication.translate("PostActionConfiguration", u"<html><head/><body><p>If you set a wait time greater than 0, a window will open upon process completion. This window will show a countdown and allow you to preview as well as edit the command.</p></body></html>", None))
#endif // QT_CONFIG(tooltip)
        self.label.setText(QCoreApplication.translate("PostActionConfiguration", u"Power Off Command:", None))
        self.lineEdit_shutdown.setPlaceholderText(QCoreApplication.translate("PostActionConfiguration", u"shutdown", None))
        self.label_2.setText(QCoreApplication.translate("PostActionConfiguration", u"Custom Commands:", None))
#if QT_CONFIG(tooltip)
        self.pushButton_row_up.setToolTip(QCoreApplication.translate("PostActionConfiguration", u"Move command up", None))
#endif // QT_CONFIG(tooltip)
#if QT_CONFIG(tooltip)
        self.pushButton_row_down.setToolTip(QCoreApplication.translate("PostActionConfiguration", u"Move command down", None))
#endif // QT_CONFIG(tooltip)
        self.pushButton_new.setText(QCoreApplication.translate("PostActionConfiguration", u"New", None))
        self.pushButton_delete.setText(QCoreApplication.translate("PostActionConfiguration", u"Delete", None))
        ___qtablewidgetitem = self.tableWidget_commands.horizontalHeaderItem(0)
        ___qtablewidgetitem.setText(QCoreApplication.translate("PostActionConfiguration", u"Action Name", None));
        ___qtablewidgetitem1 = self.tableWidget_commands.horizontalHeaderItem(1)
        ___qtablewidgetitem1.setText(QCoreApplication.translate("PostActionConfiguration", u"Command or Script File Path", None));
        self.checkBox_cancel_on_error.setText(QCoreApplication.translate("PostActionConfiguration", u"Cancel the custom action if processing failed", None))
#if QT_CONFIG(tooltip)
        self.label_review_output_help_6.setToolTip(QCoreApplication.translate("PostActionConfiguration", u"<html><head/><body><p>The Power Off action will run regardless of this setting.</p></body></html>", None))
#endif // QT_CONFIG(tooltip)
        self.label_3.setText(QCoreApplication.translate("PostActionConfiguration", u"Placeholder Tokens:", None))
        self.label_4.setText(QCoreApplication.translate("PostActionConfiguration", u"Input Files", None))
        self.label_5.setText(QCoreApplication.translate("PostActionConfiguration", u"%i", None))
#if QT_CONFIG(tooltip)
        self.label_review_output_help.setToolTip(QCoreApplication.translate("PostActionConfiguration", u"<html><head/><body><p>The individual file paths of each file processed, as a space separated list, with quotation marks where necessary.</p></body></html>", None))
#endif // QT_CONFIG(tooltip)
        self.inputDirectoryIesLabel.setText(QCoreApplication.translate("PostActionConfiguration", u"Input Directory", None))
        self.label_12.setText(QCoreApplication.translate("PostActionConfiguration", u"%id", None))
#if QT_CONFIG(tooltip)
        self.label_review_output_help_2.setToolTip(QCoreApplication.translate("PostActionConfiguration", u"<html><head/><body><p>Group files by parent directory and list these, as a space separated list, with quotation marks where necessary.</p></body></html>", None))
#endif // QT_CONFIG(tooltip)
        self.label_6.setText(QCoreApplication.translate("PostActionConfiguration", u"Output Files", None))
        self.label_9.setText(QCoreApplication.translate("PostActionConfiguration", u"%o", None))
#if QT_CONFIG(tooltip)
        self.label_review_output_help_4.setToolTip(QCoreApplication.translate("PostActionConfiguration", u"<html><head/><body><p>The individual file paths of each file created as an output, as a space separated list, with quotation marks where necessary.</p></body></html>", None))
#endif // QT_CONFIG(tooltip)
        self.label_10.setText(QCoreApplication.translate("PostActionConfiguration", u"Output Directory", None))
        self.label_11.setText(QCoreApplication.translate("PostActionConfiguration", u"%od", None))
#if QT_CONFIG(tooltip)
        self.label_review_output_help_5.setToolTip(QCoreApplication.translate("PostActionConfiguration", u"<html><head/><body><p>Group output files by parent directory and list these, as a space separated list, with quotation marks where necessary.</p></body></html>", None))
#endif // QT_CONFIG(tooltip)
        self.label_8.setText(QCoreApplication.translate("PostActionConfiguration", u"Profile Used", None))
        self.label_7.setText(QCoreApplication.translate("PostActionConfiguration", u"%p", None))
#if QT_CONFIG(tooltip)
        self.label_review_output_help_3.setToolTip(QCoreApplication.translate("PostActionConfiguration", u"<html><head/><body><p>The name of the profile used, with quotation marks if necessary.</p></body></html>", None))
#endif // QT_CONFIG(tooltip)
    # retranslateUi

