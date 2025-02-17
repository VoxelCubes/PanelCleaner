# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'Mainwindow.ui'
##
## Created by: Qt User Interface Compiler version 6.8.2
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide6.QtCore import (QCoreApplication, QDate, QDateTime, QLocale,
    QMetaObject, QObject, QPoint, QRect,
    QSize, QTime, QUrl, Qt)
from PySide6.QtGui import (QAction, QBrush, QColor, QConicalGradient,
    QCursor, QFont, QFontDatabase, QGradient,
    QIcon, QImage, QKeySequence, QLinearGradient,
    QPainter, QPalette, QPixmap, QRadialGradient,
    QTransform)
from PySide6.QtWidgets import (QAbstractItemView, QApplication, QCheckBox, QFrame,
    QGroupBox, QHBoxLayout, QHeaderView, QLabel,
    QLineEdit, QMainWindow, QMenu, QMenuBar,
    QProgressBar, QPushButton, QRadioButton, QSizePolicy,
    QSpacerItem, QSplitter, QStackedWidget, QStatusBar,
    QTableWidgetItem, QTextEdit, QVBoxLayout, QWidget)

from pcleaner.gui.CustomQ.CComboBox import CComboBox
from pcleaner.gui.CustomQ.CDropFrame import CDropFrame
from pcleaner.gui.CustomQ.CTextEdit import CTextEdit
from pcleaner.gui.CustomQ.CTooltipLabel import CTooltipLabel
from pcleaner.gui.file_table import FileTable
from pcleaner.gui.image_tab import ImageTab

class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        if not MainWindow.objectName():
            MainWindow.setObjectName(u"MainWindow")
        MainWindow.resize(1850, 800)
        self.action_add_files = QAction(MainWindow)
        self.action_add_files.setObjectName(u"action_add_files")
        icon = QIcon()
        iconThemeName = u"document-open"
        if QIcon.hasThemeIcon(iconThemeName):
            icon = QIcon.fromTheme(iconThemeName)
        else:
            icon.addFile(u".", QSize(), QIcon.Mode.Normal, QIcon.State.Off)

        self.action_add_files.setIcon(icon)
        self.action_remove_all_files = QAction(MainWindow)
        self.action_remove_all_files.setObjectName(u"action_remove_all_files")
        icon1 = QIcon()
        iconThemeName = u"edit-clear-history"
        if QIcon.hasThemeIcon(iconThemeName):
            icon1 = QIcon.fromTheme(iconThemeName)
        else:
            icon1.addFile(u".", QSize(), QIcon.Mode.Normal, QIcon.State.Off)

        self.action_remove_all_files.setIcon(icon1)
        self.action_new_profile = QAction(MainWindow)
        self.action_new_profile.setObjectName(u"action_new_profile")
        icon2 = QIcon()
        iconThemeName = u"document-new"
        if QIcon.hasThemeIcon(iconThemeName):
            icon2 = QIcon.fromTheme(iconThemeName)
        else:
            icon2.addFile(u".", QSize(), QIcon.Mode.Normal, QIcon.State.Off)

        self.action_new_profile.setIcon(icon2)
        self.action_delete_profile = QAction(MainWindow)
        self.action_delete_profile.setObjectName(u"action_delete_profile")
        icon3 = QIcon()
        iconThemeName = u"edit-delete"
        if QIcon.hasThemeIcon(iconThemeName):
            icon3 = QIcon.fromTheme(iconThemeName)
        else:
            icon3.addFile(u".", QSize(), QIcon.Mode.Normal, QIcon.State.Off)

        self.action_delete_profile.setIcon(icon3)
        self.action_import_profile = QAction(MainWindow)
        self.action_import_profile.setObjectName(u"action_import_profile")
        icon4 = QIcon()
        iconThemeName = u"document-import"
        if QIcon.hasThemeIcon(iconThemeName):
            icon4 = QIcon.fromTheme(iconThemeName)
        else:
            icon4.addFile(u".", QSize(), QIcon.Mode.Normal, QIcon.State.Off)

        self.action_import_profile.setIcon(icon4)
        self.action_online_documentation = QAction(MainWindow)
        self.action_online_documentation.setObjectName(u"action_online_documentation")
        icon5 = QIcon()
        iconThemeName = u"internet-services"
        if QIcon.hasThemeIcon(iconThemeName):
            icon5 = QIcon.fromTheme(iconThemeName)
        else:
            icon5.addFile(u".", QSize(), QIcon.Mode.Normal, QIcon.State.Off)

        self.action_online_documentation.setIcon(icon5)
        self.action_about = QAction(MainWindow)
        self.action_about.setObjectName(u"action_about")
        icon6 = QIcon()
        iconThemeName = u"help-about"
        if QIcon.hasThemeIcon(iconThemeName):
            icon6 = QIcon.fromTheme(iconThemeName)
        else:
            icon6.addFile(u".", QSize(), QIcon.Mode.Normal, QIcon.State.Off)

        self.action_about.setIcon(icon6)
        self.actionView_License = QAction(MainWindow)
        self.actionView_License.setObjectName(u"actionView_License")
        self.action_save_profile = QAction(MainWindow)
        self.action_save_profile.setObjectName(u"action_save_profile")
        icon7 = QIcon()
        iconThemeName = u"document-save"
        if QIcon.hasThemeIcon(iconThemeName):
            icon7 = QIcon.fromTheme(iconThemeName)
        else:
            icon7.addFile(u".", QSize(), QIcon.Mode.Normal, QIcon.State.Off)

        self.action_save_profile.setIcon(icon7)
        self.action_save_profile_as = QAction(MainWindow)
        self.action_save_profile_as.setObjectName(u"action_save_profile_as")
        icon8 = QIcon()
        iconThemeName = u"document-save-as"
        if QIcon.hasThemeIcon(iconThemeName):
            icon8 = QIcon.fromTheme(iconThemeName)
        else:
            icon8.addFile(u".", QSize(), QIcon.Mode.Normal, QIcon.State.Off)

        self.action_save_profile_as.setIcon(icon8)
        self.action_system_theme = QAction(MainWindow)
        self.action_system_theme.setObjectName(u"action_system_theme")
        self.action_system_theme.setCheckable(True)
        self.action_dark = QAction(MainWindow)
        self.action_dark.setObjectName(u"action_dark")
        self.action_dark.setCheckable(True)
        self.action_light = QAction(MainWindow)
        self.action_light.setObjectName(u"action_light")
        self.action_light.setCheckable(True)
        self.action_temp_2 = QAction(MainWindow)
        self.action_temp_2.setObjectName(u"action_temp_2")
        self.action_temp_2.setText(u"<temp>")
        self.action_add_folders = QAction(MainWindow)
        self.action_add_folders.setObjectName(u"action_add_folders")
        icon9 = QIcon()
        iconThemeName = u"document-open-folder"
        if QIcon.hasThemeIcon(iconThemeName):
            icon9 = QIcon.fromTheme(iconThemeName)
        else:
            icon9.addFile(u".", QSize(), QIcon.Mode.Normal, QIcon.State.Off)

        self.action_add_folders.setIcon(icon9)
        self.action_delete_models = QAction(MainWindow)
        self.action_delete_models.setObjectName(u"action_delete_models")
        self.action_delete_models.setIcon(icon3)
        self.action_download_models = QAction(MainWindow)
        self.action_download_models.setObjectName(u"action_download_models")
        icon10 = QIcon()
        iconThemeName = u"download"
        if QIcon.hasThemeIcon(iconThemeName):
            icon10 = QIcon.fromTheme(iconThemeName)
        else:
            icon10.addFile(u".", QSize(), QIcon.Mode.Normal, QIcon.State.Off)

        self.action_download_models.setIcon(icon10)
        self.action_donate = QAction(MainWindow)
        self.action_donate.setObjectName(u"action_donate")
        self.action_temp_3 = QAction(MainWindow)
        self.action_temp_3.setObjectName(u"action_temp_3")
        self.action_temp_3.setText(u"<temp>")
        self.action_remove_file = QAction(MainWindow)
        self.action_remove_file.setObjectName(u"action_remove_file")
        self.action_remove_file.setEnabled(False)
        icon11 = QIcon()
        iconThemeName = u"edit-delete-remove"
        if QIcon.hasThemeIcon(iconThemeName):
            icon11 = QIcon.fromTheme(iconThemeName)
        else:
            icon11.addFile(u".", QSize(), QIcon.Mode.Normal, QIcon.State.Off)

        self.action_remove_file.setIcon(icon11)
        self.action_help_translation = QAction(MainWindow)
        self.action_help_translation.setObjectName(u"action_help_translation")
        icon12 = QIcon()
        iconThemeName = u"languages"
        if QIcon.hasThemeIcon(iconThemeName):
            icon12 = QIcon.fromTheme(iconThemeName)
        else:
            icon12.addFile(u".", QSize(), QIcon.Mode.Normal, QIcon.State.Off)

        self.action_help_translation.setIcon(icon12)
        self.action_report_issue = QAction(MainWindow)
        self.action_report_issue.setObjectName(u"action_report_issue")
        icon13 = QIcon()
        iconThemeName = u"tools-report-bug"
        if QIcon.hasThemeIcon(iconThemeName):
            icon13 = QIcon.fromTheme(iconThemeName)
        else:
            icon13.addFile(u".", QSize(), QIcon.Mode.Normal, QIcon.State.Off)

        self.action_report_issue.setIcon(icon13)
        self.action_simulate_exception = QAction(MainWindow)
        self.action_simulate_exception.setObjectName(u"action_simulate_exception")
        self.action_file_manager_extension = QAction(MainWindow)
        self.action_file_manager_extension.setObjectName(u"action_file_manager_extension")
        icon14 = QIcon()
        iconThemeName = u"application-menu"
        if QIcon.hasThemeIcon(iconThemeName):
            icon14 = QIcon.fromTheme(iconThemeName)
        else:
            icon14.addFile(u".", QSize(), QIcon.Mode.Normal, QIcon.State.Off)

        self.action_file_manager_extension.setIcon(icon14)
        self.action_show_ocr_language_support = QAction(MainWindow)
        self.action_show_ocr_language_support.setObjectName(u"action_show_ocr_language_support")
        icon15 = QIcon()
        iconThemeName = u"code-block"
        if QIcon.hasThemeIcon(iconThemeName):
            icon15 = QIcon.fromTheme(iconThemeName)
        else:
            icon15.addFile(u".", QSize(), QIcon.Mode.Normal, QIcon.State.Off)

        self.action_show_ocr_language_support.setIcon(icon15)
        self.actionReset_Window_Layout_Preferences = QAction(MainWindow)
        self.actionReset_Window_Layout_Preferences.setObjectName(u"actionReset_Window_Layout_Preferences")
        self.action_delete_window_state = QAction(MainWindow)
        self.action_delete_window_state.setObjectName(u"action_delete_window_state")
        icon16 = QIcon()
        iconThemeName = u"edit-reset"
        if QIcon.hasThemeIcon(iconThemeName):
            icon16 = QIcon.fromTheme(iconThemeName)
        else:
            icon16.addFile(u".", QSize(), QIcon.Mode.Normal, QIcon.State.Off)

        self.action_delete_window_state.setIcon(icon16)
        self.action_show_oom = QAction(MainWindow)
        self.action_show_oom.setObjectName(u"action_show_oom")
        self.action_show_oom.setCheckable(True)
        self.action_show_oom.setChecked(True)
        self.action_post_action_settings = QAction(MainWindow)
        self.action_post_action_settings.setObjectName(u"action_post_action_settings")
        icon17 = QIcon()
        iconThemeName = u"configure"
        if QIcon.hasThemeIcon(iconThemeName):
            icon17 = QIcon.fromTheme(iconThemeName)
        else:
            icon17.addFile(u".", QSize(), QIcon.Mode.Normal, QIcon.State.Off)

        self.action_post_action_settings.setIcon(icon17)
        self.action_TEMP = QAction(MainWindow)
        self.action_TEMP.setObjectName(u"action_TEMP")
        self.action_TEMP.setEnabled(False)
        self.action_TEMP.setText(u"<TEMP>")
        self.centralwidget = QWidget(MainWindow)
        self.centralwidget.setObjectName(u"centralwidget")
        self.verticalLayout_6 = QVBoxLayout(self.centralwidget)
        self.verticalLayout_6.setObjectName(u"verticalLayout_6")
        self.verticalLayout_6.setContentsMargins(1, 4, 1, 1)
        self.splitter = QSplitter(self.centralwidget)
        self.splitter.setObjectName(u"splitter")
        self.splitter.setOrientation(Qt.Horizontal)
        self.groupBox_profile = QGroupBox(self.splitter)
        self.groupBox_profile.setObjectName(u"groupBox_profile")
        self.verticalLayout_2 = QVBoxLayout(self.groupBox_profile)
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.horizontalLayout_profile_header = QHBoxLayout()
        self.horizontalLayout_profile_header.setObjectName(u"horizontalLayout_profile_header")
        self.comboBox_current_profile = CComboBox(self.groupBox_profile)
        self.comboBox_current_profile.addItem("")
        self.comboBox_current_profile.setObjectName(u"comboBox_current_profile")
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.comboBox_current_profile.sizePolicy().hasHeightForWidth())
        self.comboBox_current_profile.setSizePolicy(sizePolicy)
        self.comboBox_current_profile.setMinimumSize(QSize(48, 0))

        self.horizontalLayout_profile_header.addWidget(self.comboBox_current_profile)

        self.pushButton_apply_profile = QPushButton(self.groupBox_profile)
        self.pushButton_apply_profile.setObjectName(u"pushButton_apply_profile")
        self.pushButton_apply_profile.setEnabled(False)
        icon18 = QIcon()
        iconThemeName = u"dialog-ok-apply"
        if QIcon.hasThemeIcon(iconThemeName):
            icon18 = QIcon.fromTheme(iconThemeName)
        else:
            icon18.addFile(u".", QSize(), QIcon.Mode.Normal, QIcon.State.Off)

        self.pushButton_apply_profile.setIcon(icon18)

        self.horizontalLayout_profile_header.addWidget(self.pushButton_apply_profile)

        self.pushButton_save_profile = QPushButton(self.groupBox_profile)
        self.pushButton_save_profile.setObjectName(u"pushButton_save_profile")
        self.pushButton_save_profile.setEnabled(False)
        self.pushButton_save_profile.setIcon(icon7)

        self.horizontalLayout_profile_header.addWidget(self.pushButton_save_profile)

        self.pushButton_reset_profile = QPushButton(self.groupBox_profile)
        self.pushButton_reset_profile.setObjectName(u"pushButton_reset_profile")
        self.pushButton_reset_profile.setEnabled(False)
        icon19 = QIcon()
        iconThemeName = u"document-revert"
        if QIcon.hasThemeIcon(iconThemeName):
            icon19 = QIcon.fromTheme(iconThemeName)
        else:
            icon19.addFile(u".", QSize(), QIcon.Mode.Normal, QIcon.State.Off)

        self.pushButton_reset_profile.setIcon(icon19)

        self.horizontalLayout_profile_header.addWidget(self.pushButton_reset_profile)


        self.verticalLayout_2.addLayout(self.horizontalLayout_profile_header)

        self.toolBox_profile_frame = QWidget(self.groupBox_profile)
        self.toolBox_profile_frame.setObjectName(u"toolBox_profile_frame")
        sizePolicy1 = QSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Expanding)
        sizePolicy1.setHorizontalStretch(0)
        sizePolicy1.setVerticalStretch(0)
        sizePolicy1.setHeightForWidth(self.toolBox_profile_frame.sizePolicy().hasHeightForWidth())
        self.toolBox_profile_frame.setSizePolicy(sizePolicy1)

        self.verticalLayout_2.addWidget(self.toolBox_profile_frame)

        self.splitter.addWidget(self.groupBox_profile)
        self.stackedWidget_images = QStackedWidget(self.splitter)
        self.stackedWidget_images.setObjectName(u"stackedWidget_images")
        self.page_greeter = QWidget()
        self.page_greeter.setObjectName(u"page_greeter")
        self.verticalLayout_8 = QVBoxLayout(self.page_greeter)
        self.verticalLayout_8.setObjectName(u"verticalLayout_8")
        self.verticalLayout_8.setContentsMargins(0, 0, 0, 0)
        self.frame_greeter = CDropFrame(self.page_greeter)
        self.frame_greeter.setObjectName(u"frame_greeter")
        self.frame_greeter.setFrameShape(QFrame.StyledPanel)
        self.frame_greeter.setFrameShadow(QFrame.Raised)
        self.frame_greeter.setLineWidth(4)
        self.horizontalLayout_4 = QHBoxLayout(self.frame_greeter)
        self.horizontalLayout_4.setObjectName(u"horizontalLayout_4")
        self.verticalLayout_10 = QVBoxLayout()
        self.verticalLayout_10.setSpacing(30)
        self.verticalLayout_10.setObjectName(u"verticalLayout_10")
        self.verticalSpacer_3 = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.verticalLayout_10.addItem(self.verticalSpacer_3)

        self.label_drop = QLabel(self.frame_greeter)
        self.label_drop.setObjectName(u"label_drop")
        self.label_drop.setAlignment(Qt.AlignCenter)

        self.verticalLayout_10.addWidget(self.label_drop)

        self.label_drop_icon = QLabel(self.frame_greeter)
        self.label_drop_icon.setObjectName(u"label_drop_icon")
        self.label_drop_icon.setText(u"<drop icon>")
        self.label_drop_icon.setAlignment(Qt.AlignCenter)

        self.verticalLayout_10.addWidget(self.label_drop_icon)

        self.verticalSpacer_4 = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.verticalLayout_10.addItem(self.verticalSpacer_4)


        self.horizontalLayout_4.addLayout(self.verticalLayout_10)


        self.verticalLayout_8.addWidget(self.frame_greeter)

        self.stackedWidget_images.addWidget(self.page_greeter)
        self.page_table = QWidget()
        self.page_table.setObjectName(u"page_table")
        self.verticalLayout = QVBoxLayout(self.page_table)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.verticalLayout.setContentsMargins(0, 0, 0, 0)
        self.image_tab = ImageTab(self.page_table)
        self.image_tab.setObjectName(u"image_tab")
        self.image_tab.setTabsClosable(True)
        self.tabWidget_table_page = QWidget()
        self.tabWidget_table_page.setObjectName(u"tabWidget_table_page")
        self.verticalLayout_3 = QVBoxLayout(self.tabWidget_table_page)
        self.verticalLayout_3.setSpacing(0)
        self.verticalLayout_3.setObjectName(u"verticalLayout_3")
        self.verticalLayout_3.setContentsMargins(0, 0, 0, 0)
        self.file_table = FileTable(self.tabWidget_table_page)
        if (self.file_table.columnCount() < 7):
            self.file_table.setColumnCount(7)
        __qtablewidgetitem = QTableWidgetItem()
        __qtablewidgetitem.setText(u"id");
        self.file_table.setHorizontalHeaderItem(0, __qtablewidgetitem)
        __qtablewidgetitem1 = QTableWidgetItem()
        self.file_table.setHorizontalHeaderItem(1, __qtablewidgetitem1)
        __qtablewidgetitem2 = QTableWidgetItem()
        self.file_table.setHorizontalHeaderItem(2, __qtablewidgetitem2)
        __qtablewidgetitem3 = QTableWidgetItem()
        self.file_table.setHorizontalHeaderItem(3, __qtablewidgetitem3)
        __qtablewidgetitem4 = QTableWidgetItem()
        self.file_table.setHorizontalHeaderItem(4, __qtablewidgetitem4)
        __qtablewidgetitem5 = QTableWidgetItem()
        self.file_table.setHorizontalHeaderItem(5, __qtablewidgetitem5)
        __qtablewidgetitem6 = QTableWidgetItem()
        self.file_table.setHorizontalHeaderItem(6, __qtablewidgetitem6)
        self.file_table.setObjectName(u"file_table")
        self.file_table.setFrameShape(QFrame.NoFrame)
        self.file_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.file_table.setDragDropOverwriteMode(False)
        self.file_table.setDragDropMode(QAbstractItemView.NoDragDrop)
        self.file_table.setAlternatingRowColors(True)
        self.file_table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.file_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.file_table.setSortingEnabled(False)
        self.file_table.setCornerButtonEnabled(False)
        self.file_table.horizontalHeader().setHighlightSections(False)
        self.file_table.verticalHeader().setHighlightSections(False)

        self.verticalLayout_3.addWidget(self.file_table)

        self.image_tab.addTab(self.tabWidget_table_page, "")

        self.verticalLayout.addWidget(self.image_tab)

        self.stackedWidget_images.addWidget(self.page_table)
        self.splitter.addWidget(self.stackedWidget_images)
        self.frame_output = QFrame(self.splitter)
        self.frame_output.setObjectName(u"frame_output")
        self.frame_output.setFrameShape(QFrame.NoFrame)
        self.frame_output.setFrameShadow(QFrame.Raised)
        self.verticalLayout_4 = QVBoxLayout(self.frame_output)
        self.verticalLayout_4.setObjectName(u"verticalLayout_4")
        self.verticalLayout_4.setContentsMargins(0, 0, 0, 0)
        self.horizontalLayout_3 = QHBoxLayout()
        self.horizontalLayout_3.setObjectName(u"horizontalLayout_3")
        self.groupBox_process = QGroupBox(self.frame_output)
        self.groupBox_process.setObjectName(u"groupBox_process")
        self.verticalLayout_9 = QVBoxLayout(self.groupBox_process)
        self.verticalLayout_9.setObjectName(u"verticalLayout_9")
        self.radioButton_cleaning = QRadioButton(self.groupBox_process)
        self.radioButton_cleaning.setObjectName(u"radioButton_cleaning")
        self.radioButton_cleaning.setChecked(True)

        self.verticalLayout_9.addWidget(self.radioButton_cleaning)

        self.radioButton_ocr = QRadioButton(self.groupBox_process)
        self.radioButton_ocr.setObjectName(u"radioButton_ocr")

        self.verticalLayout_9.addWidget(self.radioButton_ocr)

        self.verticalSpacer = QSpacerItem(20, 0, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.verticalLayout_9.addItem(self.verticalSpacer)

        self.verticalLayout_7 = QVBoxLayout()
        self.verticalLayout_7.setObjectName(u"verticalLayout_7")
        self.pushButton_edit_ocr = QPushButton(self.groupBox_process)
        self.pushButton_edit_ocr.setObjectName(u"pushButton_edit_ocr")
        self.pushButton_edit_ocr.setIcon(icon)

        self.verticalLayout_7.addWidget(self.pushButton_edit_ocr)

        self.pushButton_abort = QPushButton(self.groupBox_process)
        self.pushButton_abort.setObjectName(u"pushButton_abort")
        icon20 = QIcon()
        iconThemeName = u"process-stop"
        if QIcon.hasThemeIcon(iconThemeName):
            icon20 = QIcon.fromTheme(iconThemeName)
        else:
            icon20.addFile(u".", QSize(), QIcon.Mode.Normal, QIcon.State.Off)

        self.pushButton_abort.setIcon(icon20)

        self.verticalLayout_7.addWidget(self.pushButton_abort)

        self.pushButton_start = QPushButton(self.groupBox_process)
        self.pushButton_start.setObjectName(u"pushButton_start")
        icon21 = QIcon()
        iconThemeName = u"media-playback-start"
        if QIcon.hasThemeIcon(iconThemeName):
            icon21 = QIcon.fromTheme(iconThemeName)
        else:
            icon21.addFile(u".", QSize(), QIcon.Mode.Normal, QIcon.State.Off)

        self.pushButton_start.setIcon(icon21)

        self.verticalLayout_7.addWidget(self.pushButton_start)


        self.verticalLayout_9.addLayout(self.verticalLayout_7)


        self.horizontalLayout_3.addWidget(self.groupBox_process)

        self.groupBox_output_options = QGroupBox(self.frame_output)
        self.groupBox_output_options.setObjectName(u"groupBox_output_options")
        self.verticalLayout_5 = QVBoxLayout(self.groupBox_output_options)
        self.verticalLayout_5.setObjectName(u"verticalLayout_5")
        self.stackedWidget_output = QStackedWidget(self.groupBox_output_options)
        self.stackedWidget_output.setObjectName(u"stackedWidget_output")
        self.page_cleaning = QWidget()
        self.page_cleaning.setObjectName(u"page_cleaning")
        self.verticalLayout_14 = QVBoxLayout(self.page_cleaning)
        self.verticalLayout_14.setObjectName(u"verticalLayout_14")
        self.verticalLayout_14.setContentsMargins(0, 0, 0, 0)
        self.horizontalLayout_7 = QHBoxLayout()
        self.horizontalLayout_7.setObjectName(u"horizontalLayout_7")
        self.verticalLayout_11 = QVBoxLayout()
        self.verticalLayout_11.setSpacing(6)
        self.verticalLayout_11.setObjectName(u"verticalLayout_11")
        self.checkBox_save_clean = QCheckBox(self.page_cleaning)
        self.checkBox_save_clean.setObjectName(u"checkBox_save_clean")
        self.checkBox_save_clean.setChecked(True)

        self.verticalLayout_11.addWidget(self.checkBox_save_clean)

        self.checkBox_save_mask = QCheckBox(self.page_cleaning)
        self.checkBox_save_mask.setObjectName(u"checkBox_save_mask")
        self.checkBox_save_mask.setChecked(True)

        self.verticalLayout_11.addWidget(self.checkBox_save_mask)

        self.checkBox_save_text = QCheckBox(self.page_cleaning)
        self.checkBox_save_text.setObjectName(u"checkBox_save_text")

        self.verticalLayout_11.addWidget(self.checkBox_save_text)


        self.horizontalLayout_7.addLayout(self.verticalLayout_11)

        self.horizontalSpacer_6 = QSpacerItem(0, 0, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_7.addItem(self.horizontalSpacer_6)

        self.verticalLayout_13 = QVBoxLayout()
        self.verticalLayout_13.setSpacing(6)
        self.verticalLayout_13.setObjectName(u"verticalLayout_13")
        self.horizontalLayout_10 = QHBoxLayout()
        self.horizontalLayout_10.setObjectName(u"horizontalLayout_10")
        self.checkBox_review_output = QCheckBox(self.page_cleaning)
        self.checkBox_review_output.setObjectName(u"checkBox_review_output")
        self.checkBox_review_output.setChecked(True)

        self.horizontalLayout_10.addWidget(self.checkBox_review_output)

        self.label_review_output_help = CTooltipLabel(self.page_cleaning)
        self.label_review_output_help.setObjectName(u"label_review_output_help")
        self.label_review_output_help.setToolTipDuration(-1)
        self.label_review_output_help.setText(u"<helper>")

        self.horizontalLayout_10.addWidget(self.label_review_output_help)

        self.horizontalSpacer_7 = QSpacerItem(0, 0, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_10.addItem(self.horizontalSpacer_7)


        self.verticalLayout_13.addLayout(self.horizontalLayout_10)

        self.horizontalLayout_6 = QHBoxLayout()
        self.horizontalLayout_6.setObjectName(u"horizontalLayout_6")
        self.checkBox_write_output = QCheckBox(self.page_cleaning)
        self.checkBox_write_output.setObjectName(u"checkBox_write_output")
        self.checkBox_write_output.setChecked(True)

        self.horizontalLayout_6.addWidget(self.checkBox_write_output)

        self.label_write_output_help = CTooltipLabel(self.page_cleaning)
        self.label_write_output_help.setObjectName(u"label_write_output_help")
        self.label_write_output_help.setToolTipDuration(-1)
        self.label_write_output_help.setText(u"<helper>")

        self.horizontalLayout_6.addWidget(self.label_write_output_help)

        self.horizontalSpacer_4 = QSpacerItem(0, 0, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_6.addItem(self.horizontalSpacer_4)


        self.verticalLayout_13.addLayout(self.horizontalLayout_6)

        self.verticalSpacer_6 = QSpacerItem(20, 0, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.verticalLayout_13.addItem(self.verticalSpacer_6)


        self.horizontalLayout_7.addLayout(self.verticalLayout_13)


        self.verticalLayout_14.addLayout(self.horizontalLayout_7)

        self.verticalSpacer_2 = QSpacerItem(20, 1, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.verticalLayout_14.addItem(self.verticalSpacer_2)

        self.horizontalLayout_5 = QHBoxLayout()
        self.horizontalLayout_5.setObjectName(u"horizontalLayout_5")
        self.label_4 = QLabel(self.page_cleaning)
        self.label_4.setObjectName(u"label_4")
        self.label_4.setTextInteractionFlags(Qt.LinksAccessibleByMouse)

        self.horizontalLayout_5.addWidget(self.label_4)

        self.label_cleaning_outdir_help = CTooltipLabel(self.page_cleaning)
        self.label_cleaning_outdir_help.setObjectName(u"label_cleaning_outdir_help")
        self.label_cleaning_outdir_help.setToolTipDuration(-1)
        self.label_cleaning_outdir_help.setText(u"<helper>")

        self.horizontalLayout_5.addWidget(self.label_cleaning_outdir_help)

        self.horizontalSpacer_3 = QSpacerItem(0, 0, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_5.addItem(self.horizontalSpacer_3)


        self.verticalLayout_14.addLayout(self.horizontalLayout_5)

        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.lineEdit_out_directory = QLineEdit(self.page_cleaning)
        self.lineEdit_out_directory.setObjectName(u"lineEdit_out_directory")
        self.lineEdit_out_directory.setClearButtonEnabled(True)

        self.horizontalLayout.addWidget(self.lineEdit_out_directory)

        self.pushButton_browse_out_dir = QPushButton(self.page_cleaning)
        self.pushButton_browse_out_dir.setObjectName(u"pushButton_browse_out_dir")
        self.pushButton_browse_out_dir.setIcon(icon9)

        self.horizontalLayout.addWidget(self.pushButton_browse_out_dir)


        self.verticalLayout_14.addLayout(self.horizontalLayout)

        self.stackedWidget_output.addWidget(self.page_cleaning)
        self.page_ocr = QWidget()
        self.page_ocr.setObjectName(u"page_ocr")
        self.verticalLayout_12 = QVBoxLayout(self.page_ocr)
        self.verticalLayout_12.setObjectName(u"verticalLayout_12")
        self.verticalLayout_12.setContentsMargins(0, 0, 0, 0)
        self.horizontalLayout_11 = QHBoxLayout()
        self.horizontalLayout_11.setObjectName(u"horizontalLayout_11")
        self.verticalLayout_15 = QVBoxLayout()
        self.verticalLayout_15.setObjectName(u"verticalLayout_15")
        self.radioButton_ocr_text = QRadioButton(self.page_ocr)
        self.radioButton_ocr_text.setObjectName(u"radioButton_ocr_text")
        self.radioButton_ocr_text.setChecked(False)

        self.verticalLayout_15.addWidget(self.radioButton_ocr_text)

        self.radioButton_ocr_csv = QRadioButton(self.page_ocr)
        self.radioButton_ocr_csv.setObjectName(u"radioButton_ocr_csv")
        self.radioButton_ocr_csv.setChecked(True)

        self.verticalLayout_15.addWidget(self.radioButton_ocr_csv)


        self.horizontalLayout_11.addLayout(self.verticalLayout_15)

        self.horizontalSpacer_8 = QSpacerItem(0, 0, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_11.addItem(self.horizontalSpacer_8)

        self.verticalLayout_17 = QVBoxLayout()
        self.verticalLayout_17.setObjectName(u"verticalLayout_17")
        self.horizontalLayout_12 = QHBoxLayout()
        self.horizontalLayout_12.setObjectName(u"horizontalLayout_12")
        self.checkBox_review_ocr = QCheckBox(self.page_ocr)
        self.checkBox_review_ocr.setObjectName(u"checkBox_review_ocr")
        self.checkBox_review_ocr.setChecked(True)

        self.horizontalLayout_12.addWidget(self.checkBox_review_ocr)

        self.label_review_ocr_help = CTooltipLabel(self.page_ocr)
        self.label_review_ocr_help.setObjectName(u"label_review_ocr_help")
        self.label_review_ocr_help.setText(u"<helper>")

        self.horizontalLayout_12.addWidget(self.label_review_ocr_help)


        self.verticalLayout_17.addLayout(self.horizontalLayout_12)

        self.verticalSpacer_7 = QSpacerItem(0, 0, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.verticalLayout_17.addItem(self.verticalSpacer_7)


        self.horizontalLayout_11.addLayout(self.verticalLayout_17)


        self.verticalLayout_12.addLayout(self.horizontalLayout_11)

        self.verticalSpacer_5 = QSpacerItem(10, 0, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.verticalLayout_12.addItem(self.verticalSpacer_5)

        self.horizontalLayout_9 = QHBoxLayout()
        self.horizontalLayout_9.setObjectName(u"horizontalLayout_9")
        self.label_6 = QLabel(self.page_ocr)
        self.label_6.setObjectName(u"label_6")
        self.label_6.setTextInteractionFlags(Qt.LinksAccessibleByMouse)

        self.horizontalLayout_9.addWidget(self.label_6)

        self.label_ocr_outdir_help = CTooltipLabel(self.page_ocr)
        self.label_ocr_outdir_help.setObjectName(u"label_ocr_outdir_help")
        self.label_ocr_outdir_help.setToolTipDuration(-1)
        self.label_ocr_outdir_help.setText(u"<helper>")

        self.horizontalLayout_9.addWidget(self.label_ocr_outdir_help)

        self.horizontalSpacer_5 = QSpacerItem(0, 0, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_9.addItem(self.horizontalSpacer_5)


        self.verticalLayout_12.addLayout(self.horizontalLayout_9)

        self.horizontalLayout_8 = QHBoxLayout()
        self.horizontalLayout_8.setObjectName(u"horizontalLayout_8")
        self.lineEdit_out_file = QLineEdit(self.page_ocr)
        self.lineEdit_out_file.setObjectName(u"lineEdit_out_file")
        self.lineEdit_out_file.setClearButtonEnabled(True)

        self.horizontalLayout_8.addWidget(self.lineEdit_out_file)

        self.pushButton_browse_out_file = QPushButton(self.page_ocr)
        self.pushButton_browse_out_file.setObjectName(u"pushButton_browse_out_file")
        self.pushButton_browse_out_file.setIcon(icon)

        self.horizontalLayout_8.addWidget(self.pushButton_browse_out_file)


        self.verticalLayout_12.addLayout(self.horizontalLayout_8)

        self.stackedWidget_output.addWidget(self.page_ocr)

        self.verticalLayout_5.addWidget(self.stackedWidget_output)


        self.horizontalLayout_3.addWidget(self.groupBox_output_options)

        self.horizontalLayout_3.setStretch(0, 1)
        self.horizontalLayout_3.setStretch(1, 3)

        self.verticalLayout_4.addLayout(self.horizontalLayout_3)

        self.textEdit_analytics = CTextEdit(self.frame_output)
        self.textEdit_analytics.setObjectName(u"textEdit_analytics")
        self.textEdit_analytics.setDocumentTitle(u"")
        self.textEdit_analytics.setUndoRedoEnabled(False)
        self.textEdit_analytics.setLineWrapMode(QTextEdit.NoWrap)
        self.textEdit_analytics.setReadOnly(False)
        self.textEdit_analytics.setHtml(u"<!DOCTYPE HTML PUBLIC \"-//W3C//DTD HTML 4.0//EN\" \"http://www.w3.org/TR/REC-html40/strict.dtd\">\n"
"<html><head><meta name=\"qrichtext\" content=\"1\" /><style type=\"text/css\">\n"
"p, li { white-space: pre-wrap; }\n"
"</style></head><body style=\" font-family:'Noto Sans'; font-size:10pt; font-weight:400; font-style:normal;\">\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" font-family:'Noto Mono','Monospace';\">Mask Fitment Analytics <br />---------------------- <br />Total boxes: 5 | Masks succeeded: 5 (100%) | Masks failed: </span><span style=\" font-family:'Noto Mono','Monospace'; color:#b21818;\">0</span><span style=\" font-family:'Noto Mono','Monospace';\"> <br />Perfect masks: </span><span style=\" font-family:'Noto Mono','Monospace'; color:#18b2b2;\">5</span><span style=\" font-family:'Noto Mono','Monospace';\"> (100%) | Average border deviation: 0.00 <br /><br />Mask usage by mask size (smallest to largest)"
                        ": <br />Mask 0  :  </span><span style=\" font-family:'Noto Mono','Monospace'; color:#18b2b2;\">0</span><span style=\" font-family:'Noto Mono','Monospace';\"> / 0 <br />Mask 1  :  </span><span style=\" font-family:'Noto Mono','Monospace'; color:#18b2b2;\">0</span><span style=\" font-family:'Noto Mono','Monospace';\"> / 0 <br />Mask 2  :  </span><span style=\" font-family:'Noto Mono','Monospace'; color:#18b2b2;\">0</span><span style=\" font-family:'Noto Mono','Monospace';\"> / 0 <br />Mask 3  :  </span><span style=\" font-family:'Noto Mono','Monospace'; color:#18b2b2;\">0</span><span style=\" font-family:'Noto Mono','Monospace';\"> / 0 <br />Mask 4  :  </span><span style=\" font-family:'Noto Mono','Monospace'; color:#18b2b2;\">0</span><span style=\" font-family:'Noto Mono','Monospace';\"> / 0 <br />Mask 5  :  </span><span style=\" font-family:'Noto Mono','Monospace'; color:#18b2b2;\">0</span><span style=\" font-family:'Noto Mono','Monospace';\"> / 0 <br />Mask 6  : </span><span style=\" font-family:'Noto Mono','"
                        "Monospace'; color:#18b2b2;\">\u2588\u2588\u2588\u2588\u2588\u2588\u2588\u2588\u2588\u2588\u2588\u2588\u2588\u2588\u2588\u2588\u2588\u2588\u2588\u2588\u2588\u2588\u2588\u2588\u2588\u2588\u2588\u2588\u2588\u2588\u2588\u2588\u2588\u2588\u2588\u2588\u2588\u2588\u2588\u2588</span><span style=\" font-family:'Noto Mono','Monospace';\"> </span><span style=\" font-family:'Noto Mono','Monospace'; color:#18b2b2;\">1</span><span style=\" font-family:'Noto Mono','Monospace';\"> / 1 <br />Mask 7  :  </span><span style=\" font-family:'Noto Mono','Monospace'; color:#18b2b2;\">0</span><span style=\" font-family:'Noto Mono','Monospace';\"> / 0 <br />Mask 8  :  </span><span style=\" font-family:'Noto Mono','Monospace'; color:#18b2b2;\">0</span><span style=\" font-family:'Noto Mono','Monospace';\"> / 0 <br />Mask 9  :  </span><span style=\" font-family:'Noto Mono','Monospace'; color:#18b2b2;\">0</span><span style=\" font-family:'Noto Mono','Monospace';\"> / 0 <br />Mask 10 :  </span><span style=\" font-family:'Noto Mono','Monospa"
                        "ce'; color:#18b2b2;\">0</span><span style=\" font-family:'Noto Mono','Monospace';\"> / 0 <br />Box mask: </span><span style=\" font-family:'Noto Mono','Monospace'; color:#18b2b2;\">\u2588\u2588\u2588\u2588\u2588\u2588\u2588\u2588\u2588\u2588\u2588\u2588\u2588\u2588\u2588\u2588\u2588\u2588\u2588\u2588\u2588\u2588\u2588\u2588\u2588\u2588\u2588\u2588\u2588\u2588\u2588\u2588\u2588\u2588\u2588\u2588\u2588\u2588\u2588\u2588</span><span style=\" font-family:'Noto Mono','Monospace';\"> </span><span style=\" font-family:'Noto Mono','Monospace'; color:#18b2b2;\">4</span><span style=\" font-family:'Noto Mono','Monospace';\"> / 4 <br /><br /></span><span style=\" font-family:'Noto Mono','Monospace'; color:#18b2b2;\">\u2588 Perfect</span><span style=\" font-family:'Noto Mono','Monospace';\"> | \u2588 Total<br /><br /></span></p></body></html>")

        self.verticalLayout_4.addWidget(self.textEdit_analytics)

        self.verticalLayout_4.setStretch(1, 1)
        self.splitter.addWidget(self.frame_output)

        self.verticalLayout_6.addWidget(self.splitter)

        self.widget_oom_banner = QWidget(self.centralwidget)
        self.widget_oom_banner.setObjectName(u"widget_oom_banner")
        self.horizontalLayout_13 = QHBoxLayout(self.widget_oom_banner)
        self.horizontalLayout_13.setObjectName(u"horizontalLayout_13")
        self.horizontalSpacer_9 = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_13.addItem(self.horizontalSpacer_9)

        self.horizontalLayout_14 = QHBoxLayout()
        self.horizontalLayout_14.setObjectName(u"horizontalLayout_14")
        self.label_oom_icon = QLabel(self.widget_oom_banner)
        self.label_oom_icon.setObjectName(u"label_oom_icon")
        self.label_oom_icon.setText(u"<warning icon>")

        self.horizontalLayout_14.addWidget(self.label_oom_icon)

        self.label_oom_message = QLabel(self.widget_oom_banner)
        self.label_oom_message.setObjectName(u"label_oom_message")
        self.label_oom_message.setText(u"<warning msg>")

        self.horizontalLayout_14.addWidget(self.label_oom_message)


        self.horizontalLayout_13.addLayout(self.horizontalLayout_14)

        self.horizontalSpacer_10 = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_13.addItem(self.horizontalSpacer_10)


        self.verticalLayout_6.addWidget(self.widget_oom_banner)

        self.widget_post_process_banner = QWidget(self.centralwidget)
        self.widget_post_process_banner.setObjectName(u"widget_post_process_banner")
        self.horizontalLayout_17 = QHBoxLayout(self.widget_post_process_banner)
        self.horizontalLayout_17.setObjectName(u"horizontalLayout_17")
        self.horizontalSpacer_13 = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_17.addItem(self.horizontalSpacer_13)

        self.horizontalLayout_18 = QHBoxLayout()
        self.horizontalLayout_18.setObjectName(u"horizontalLayout_18")
        self.label_post_process_icon = QLabel(self.widget_post_process_banner)
        self.label_post_process_icon.setObjectName(u"label_post_process_icon")
        self.label_post_process_icon.setText(u"<post-process icon>")

        self.horizontalLayout_18.addWidget(self.label_post_process_icon)

        self.label_post_process = QLabel(self.widget_post_process_banner)
        self.label_post_process.setObjectName(u"label_post_process")
        self.label_post_process.setText(u"<what will happen after processing>")

        self.horizontalLayout_18.addWidget(self.label_post_process)


        self.horizontalLayout_17.addLayout(self.horizontalLayout_18)

        self.horizontalSpacer_14 = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_17.addItem(self.horizontalSpacer_14)

        self.label_post_action_conflict_icon = QLabel(self.widget_post_process_banner)
        self.label_post_action_conflict_icon.setObjectName(u"label_post_action_conflict_icon")
        self.label_post_action_conflict_icon.setText(u"<warning icon>")

        self.horizontalLayout_17.addWidget(self.label_post_action_conflict_icon)

        self.label_post_action_conflict = QLabel(self.widget_post_process_banner)
        self.label_post_action_conflict.setObjectName(u"label_post_action_conflict")
        font = QFont()
        font.setItalic(True)
        self.label_post_action_conflict.setFont(font)
        self.label_post_action_conflict.setText(u"<warning note>")

        self.horizontalLayout_17.addWidget(self.label_post_action_conflict)

        self.horizontalSpacer_11 = QSpacerItem(24, 0, QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_17.addItem(self.horizontalSpacer_11)

        self.pushButton_post_action_cancel = QPushButton(self.widget_post_process_banner)
        self.pushButton_post_action_cancel.setObjectName(u"pushButton_post_action_cancel")
        icon22 = QIcon()
        iconThemeName = u"dialog-cancel"
        if QIcon.hasThemeIcon(iconThemeName):
            icon22 = QIcon.fromTheme(iconThemeName)
        else:
            icon22.addFile(u".", QSize(), QIcon.Mode.Normal, QIcon.State.Off)

        self.pushButton_post_action_cancel.setIcon(icon22)
        self.pushButton_post_action_cancel.setFlat(False)

        self.horizontalLayout_17.addWidget(self.pushButton_post_action_cancel)

        self.pushButton_post_action_close = QPushButton(self.widget_post_process_banner)
        self.pushButton_post_action_close.setObjectName(u"pushButton_post_action_close")
        self.pushButton_post_action_close.setIcon(icon18)
        self.pushButton_post_action_close.setFlat(False)

        self.horizontalLayout_17.addWidget(self.pushButton_post_action_close)


        self.verticalLayout_6.addWidget(self.widget_post_process_banner)

        self.widget_progress_drawer = QWidget(self.centralwidget)
        self.widget_progress_drawer.setObjectName(u"widget_progress_drawer")
        self.horizontalLayout_2 = QHBoxLayout(self.widget_progress_drawer)
        self.horizontalLayout_2.setObjectName(u"horizontalLayout_2")
        self.label_generating_what = QLabel(self.widget_progress_drawer)
        self.label_generating_what.setObjectName(u"label_generating_what")

        self.horizontalLayout_2.addWidget(self.label_generating_what)

        self.label_target_outputs = QLabel(self.widget_progress_drawer)
        self.label_target_outputs.setObjectName(u"label_target_outputs")
        self.label_target_outputs.setText(u"<targeted output(s)>")

        self.horizontalLayout_2.addWidget(self.label_target_outputs)

        self.horizontalSpacer = QSpacerItem(40, 20, QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_2.addItem(self.horizontalSpacer)

        self.label_current_step_label = QLabel(self.widget_progress_drawer)
        self.label_current_step_label.setObjectName(u"label_current_step_label")

        self.horizontalLayout_2.addWidget(self.label_current_step_label)

        self.label_current_step = QLabel(self.widget_progress_drawer)
        self.label_current_step.setObjectName(u"label_current_step")
        self.label_current_step.setText(u"<step>")

        self.horizontalLayout_2.addWidget(self.label_current_step)

        self.progressBar_total = QProgressBar(self.widget_progress_drawer)
        self.progressBar_total.setObjectName(u"progressBar_total")
        sizePolicy2 = QSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        sizePolicy2.setHorizontalStretch(0)
        sizePolicy2.setVerticalStretch(0)
        sizePolicy2.setHeightForWidth(self.progressBar_total.sizePolicy().hasHeightForWidth())
        self.progressBar_total.setSizePolicy(sizePolicy2)
        self.progressBar_total.setMinimum(0)
        self.progressBar_total.setValue(24)
        self.progressBar_total.setTextVisible(True)

        self.horizontalLayout_2.addWidget(self.progressBar_total)

        self.horizontalSpacer_2 = QSpacerItem(40, 20, QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_2.addItem(self.horizontalSpacer_2)

        self.label_progress_step = QLabel(self.widget_progress_drawer)
        self.label_progress_step.setObjectName(u"label_progress_step")

        self.horizontalLayout_2.addWidget(self.label_progress_step)

        self.progressBar_individual = QProgressBar(self.widget_progress_drawer)
        self.progressBar_individual.setObjectName(u"progressBar_individual")
        self.progressBar_individual.setValue(24)

        self.horizontalLayout_2.addWidget(self.progressBar_individual)

        self.horizontalLayout_2.setStretch(5, 1)
        self.horizontalLayout_2.setStretch(8, 5)

        self.verticalLayout_6.addWidget(self.widget_progress_drawer)

        self.verticalLayout_6.setStretch(0, 1)
        MainWindow.setCentralWidget(self.centralwidget)
        self.menubar = QMenuBar(MainWindow)
        self.menubar.setObjectName(u"menubar")
        self.menubar.setGeometry(QRect(0, 0, 1850, 34))
        self.menu_File = QMenu(self.menubar)
        self.menu_File.setObjectName(u"menu_File")
        self.menu_Profile = QMenu(self.menubar)
        self.menu_Profile.setObjectName(u"menu_Profile")
        self.menu_set_default_profile = QMenu(self.menu_Profile)
        self.menu_set_default_profile.setObjectName(u"menu_set_default_profile")
        self.menu_settings = QMenu(self.menubar)
        self.menu_settings.setObjectName(u"menu_settings")
        self.menu_theme = QMenu(self.menu_settings)
        self.menu_theme.setObjectName(u"menu_theme")
        self.menu_language = QMenu(self.menu_settings)
        self.menu_language.setObjectName(u"menu_language")
        self.menu_language.setIcon(icon12)
        self.menu_post_actions = QMenu(self.menu_settings)
        self.menu_post_actions.setObjectName(u"menu_post_actions")
        self.menu_Help = QMenu(self.menubar)
        self.menu_Help.setObjectName(u"menu_Help")
        MainWindow.setMenuBar(self.menubar)
        self.statusbar = QStatusBar(MainWindow)
        self.statusbar.setObjectName(u"statusbar")
        MainWindow.setStatusBar(self.statusbar)
#if QT_CONFIG(shortcut)
        self.label_4.setBuddy(self.lineEdit_out_directory)
        self.label_6.setBuddy(self.lineEdit_out_directory)
#endif // QT_CONFIG(shortcut)

        self.menubar.addAction(self.menu_File.menuAction())
        self.menubar.addAction(self.menu_Profile.menuAction())
        self.menubar.addAction(self.menu_settings.menuAction())
        self.menubar.addAction(self.menu_Help.menuAction())
        self.menu_File.addAction(self.action_add_files)
        self.menu_File.addAction(self.action_add_folders)
        self.menu_File.addSeparator()
        self.menu_File.addAction(self.action_remove_file)
        self.menu_File.addAction(self.action_remove_all_files)
        self.menu_Profile.addAction(self.action_new_profile)
        self.menu_Profile.addAction(self.action_import_profile)
        self.menu_Profile.addSeparator()
        self.menu_Profile.addAction(self.action_save_profile)
        self.menu_Profile.addAction(self.action_save_profile_as)
        self.menu_Profile.addSeparator()
        self.menu_Profile.addAction(self.action_delete_profile)
        self.menu_Profile.addSeparator()
        self.menu_Profile.addAction(self.menu_set_default_profile.menuAction())
        self.menu_set_default_profile.addAction(self.action_temp_2)
        self.menu_settings.addAction(self.menu_theme.menuAction())
        self.menu_settings.addAction(self.menu_language.menuAction())
        self.menu_settings.addAction(self.action_file_manager_extension)
        self.menu_settings.addAction(self.action_delete_window_state)
        self.menu_settings.addAction(self.action_show_oom)
        self.menu_settings.addSeparator()
        self.menu_settings.addAction(self.action_post_action_settings)
        self.menu_settings.addAction(self.menu_post_actions.menuAction())
        self.menu_theme.addAction(self.action_system_theme)
        self.menu_theme.addSeparator()
        self.menu_theme.addAction(self.action_dark)
        self.menu_theme.addAction(self.action_light)
        self.menu_language.addAction(self.action_temp_3)
        self.menu_post_actions.addAction(self.action_TEMP)
        self.menu_Help.addAction(self.action_online_documentation)
        self.menu_Help.addAction(self.action_about)
        self.menu_Help.addAction(self.action_show_ocr_language_support)
        self.menu_Help.addAction(self.action_donate)
        self.menu_Help.addAction(self.action_help_translation)
        self.menu_Help.addAction(self.action_report_issue)
        self.menu_Help.addSeparator()
        self.menu_Help.addAction(self.action_delete_models)
        self.menu_Help.addAction(self.action_simulate_exception)

        self.retranslateUi(MainWindow)

        self.stackedWidget_images.setCurrentIndex(0)
        self.stackedWidget_output.setCurrentIndex(0)


        QMetaObject.connectSlotsByName(MainWindow)
    # setupUi

    def retranslateUi(self, MainWindow):
        MainWindow.setWindowTitle(QCoreApplication.translate("MainWindow", u"Panel Cleaner", None))
        self.action_add_files.setText(QCoreApplication.translate("MainWindow", u"Add Files...", None))
        self.action_remove_all_files.setText(QCoreApplication.translate("MainWindow", u"Remove All Files", None))
        self.action_new_profile.setText(QCoreApplication.translate("MainWindow", u"New", None))
        self.action_delete_profile.setText(QCoreApplication.translate("MainWindow", u"Delete", None))
        self.action_import_profile.setText(QCoreApplication.translate("MainWindow", u"Import...", None))
        self.action_online_documentation.setText(QCoreApplication.translate("MainWindow", u"Online Documentation", None))
        self.action_about.setText(QCoreApplication.translate("MainWindow", u"About Panel Cleaner", None))
        self.actionView_License.setText(QCoreApplication.translate("MainWindow", u"View License", None))
        self.action_save_profile.setText(QCoreApplication.translate("MainWindow", u"Save", None))
        self.action_save_profile_as.setText(QCoreApplication.translate("MainWindow", u"Save as...", None))
        self.action_system_theme.setText(QCoreApplication.translate("MainWindow", u"System", None))
        self.action_dark.setText(QCoreApplication.translate("MainWindow", u"Dark", None))
        self.action_light.setText(QCoreApplication.translate("MainWindow", u"Light", None))
        self.action_add_folders.setText(QCoreApplication.translate("MainWindow", u"Add Folder...", None))
        self.action_delete_models.setText(QCoreApplication.translate("MainWindow", u"Delete Machine Learning Models", None))
        self.action_download_models.setText(QCoreApplication.translate("MainWindow", u"Download Machine Learning Models", None))
        self.action_donate.setText(QCoreApplication.translate("MainWindow", u"Donate", None))
        self.action_remove_file.setText(QCoreApplication.translate("MainWindow", u"Remove File", None))
        self.action_help_translation.setText(QCoreApplication.translate("MainWindow", u"Help Translate Panel Cleaner", None))
        self.action_report_issue.setText(QCoreApplication.translate("MainWindow", u"Report an Issue...", None))
        self.action_simulate_exception.setText(QCoreApplication.translate("MainWindow", u"Simulate Exception", None))
        self.action_file_manager_extension.setText(QCoreApplication.translate("MainWindow", u"Add File Browser Extension...", None))
        self.action_show_ocr_language_support.setText(QCoreApplication.translate("MainWindow", u"Show Supported OCR Languages", None))
        self.actionReset_Window_Layout_Preferences.setText(QCoreApplication.translate("MainWindow", u"Reset Window Layout Preferences", None))
        self.action_delete_window_state.setText(QCoreApplication.translate("MainWindow", u"Reset Window Layout Preferences", None))
        self.action_show_oom.setText(QCoreApplication.translate("MainWindow", u"Show Out Of Memory Warnings", None))
        self.action_post_action_settings.setText(QCoreApplication.translate("MainWindow", u"Configure Post-Run Actions...", None))
        self.groupBox_profile.setTitle(QCoreApplication.translate("MainWindow", u"Profile", None))
        self.comboBox_current_profile.setItemText(0, QCoreApplication.translate("MainWindow", u"Default", None))

        self.pushButton_apply_profile.setText(QCoreApplication.translate("MainWindow", u"Apply", None))
        self.pushButton_save_profile.setText(QCoreApplication.translate("MainWindow", u"Save", None))
        self.pushButton_reset_profile.setText(QCoreApplication.translate("MainWindow", u"Reset All", None))
        self.label_drop.setText(QCoreApplication.translate("MainWindow", u"Drag and Drop Images or Folders Here", None))
        ___qtablewidgetitem = self.file_table.horizontalHeaderItem(1)
        ___qtablewidgetitem.setText(QCoreApplication.translate("MainWindow", u"File", None));
        ___qtablewidgetitem1 = self.file_table.horizontalHeaderItem(2)
        ___qtablewidgetitem1.setText(QCoreApplication.translate("MainWindow", u"Size", None));
        ___qtablewidgetitem2 = self.file_table.horizontalHeaderItem(3)
        ___qtablewidgetitem2.setText(QCoreApplication.translate("MainWindow", u"Processing Size", u"The size that the picture is shrunk down to for processing."));
        ___qtablewidgetitem3 = self.file_table.horizontalHeaderItem(4)
        ___qtablewidgetitem3.setText(QCoreApplication.translate("MainWindow", u"File Size", None));
        ___qtablewidgetitem4 = self.file_table.horizontalHeaderItem(5)
        ___qtablewidgetitem4.setText(QCoreApplication.translate("MainWindow", u"Color Mode", u"Like RGB, grayscale etc."));
        ___qtablewidgetitem5 = self.file_table.horizontalHeaderItem(6)
        ___qtablewidgetitem5.setText(QCoreApplication.translate("MainWindow", u"Analytics", u"Can also call this statistics."));
        self.image_tab.setTabText(self.image_tab.indexOf(self.tabWidget_table_page), QCoreApplication.translate("MainWindow", u"Images", None))
        self.groupBox_process.setTitle(QCoreApplication.translate("MainWindow", u"Process", None))
        self.radioButton_cleaning.setText(QCoreApplication.translate("MainWindow", u"Cleaning", None))
        self.radioButton_ocr.setText(QCoreApplication.translate("MainWindow", u"OCR", None))
        self.pushButton_edit_ocr.setText(QCoreApplication.translate("MainWindow", u"Edit Existing Output", None))
        self.pushButton_abort.setText(QCoreApplication.translate("MainWindow", u"Abort", None))
        self.pushButton_start.setText(QCoreApplication.translate("MainWindow", u"Start", None))
        self.groupBox_output_options.setTitle(QCoreApplication.translate("MainWindow", u"Output", None))
        self.checkBox_save_clean.setText(QCoreApplication.translate("MainWindow", u"Cleaned Image", None))
        self.checkBox_save_mask.setText(QCoreApplication.translate("MainWindow", u"Mask", None))
        self.checkBox_save_text.setText(QCoreApplication.translate("MainWindow", u"Isolated Text", None))
        self.checkBox_review_output.setText(QCoreApplication.translate("MainWindow", u"Review Output", None))
#if QT_CONFIG(tooltip)
        self.label_review_output_help.setToolTip(QCoreApplication.translate("MainWindow", u"<html><head/><body><p>When checked, a review window will open upon process completion. The results are also pre-viewable in each image's details view, before proceeding with saving them to disk.</p></body></html>", None))
#endif // QT_CONFIG(tooltip)
        self.checkBox_write_output.setText(QCoreApplication.translate("MainWindow", u"Save Output", None))
#if QT_CONFIG(tooltip)
        self.label_write_output_help.setToolTip(QCoreApplication.translate("MainWindow", u"<html><head/><body><p>When checked, the outputs are saved on disk. Otherwise, you can only preview them in the image details view or the Output Review, if enabled. </p><p>If the profile remains unchanged after cleaning without this option enabled, you can quickly export them by running the cleaner again with this option enabled.</p></body></html>", None))
#endif // QT_CONFIG(tooltip)
        self.label_4.setText(QCoreApplication.translate("MainWindow", u"Output Directory:", None))
#if QT_CONFIG(tooltip)
        self.label_cleaning_outdir_help.setToolTip(QCoreApplication.translate("MainWindow", u"You can use a relative path to create a subfolder at the image's original location, or use an absolute path.", None))
#endif // QT_CONFIG(tooltip)
        self.lineEdit_out_directory.setPlaceholderText(QCoreApplication.translate("MainWindow", u"cleaned", None))
        self.pushButton_browse_out_dir.setText("")
        self.radioButton_ocr_text.setText(QCoreApplication.translate("MainWindow", u"Plain Text", None))
        self.radioButton_ocr_csv.setText(QCoreApplication.translate("MainWindow", u"CSV Spreadsheet", None))
        self.checkBox_review_ocr.setText(QCoreApplication.translate("MainWindow", u"Review Output", None))
#if QT_CONFIG(tooltip)
        self.label_review_ocr_help.setToolTip(QCoreApplication.translate("MainWindow", u"When checked, a review window will open upon process completion.", None))
#endif // QT_CONFIG(tooltip)
        self.label_6.setText(QCoreApplication.translate("MainWindow", u"Output File:", None))
#if QT_CONFIG(tooltip)
        self.label_ocr_outdir_help.setToolTip(QCoreApplication.translate("MainWindow", u"<html><head/><body><p>Either enter an absolute or relative path with a file name. The output of all images is written to the same file.</p></body></html>", None))
#endif // QT_CONFIG(tooltip)
        self.lineEdit_out_file.setPlaceholderText(QCoreApplication.translate("MainWindow", u"detected_text.txt", None))
        self.pushButton_browse_out_file.setText("")
        self.pushButton_post_action_cancel.setText(QCoreApplication.translate("MainWindow", u"Cancel Action", None))
        self.pushButton_post_action_close.setText(QCoreApplication.translate("MainWindow", u"Close", None))
        self.label_generating_what.setText(QCoreApplication.translate("MainWindow", u"Generating:", u"This is present progressive, as in \"[currently] Generating:\""))
        self.label_current_step_label.setText(QCoreApplication.translate("MainWindow", u"Current Step:", None))
        self.progressBar_total.setFormat(QCoreApplication.translate("MainWindow", u"%v / %m", None))
        self.label_progress_step.setText(QCoreApplication.translate("MainWindow", u"Images Processed:", u"As in \"images processed: 42\" with progress bar."))
        self.progressBar_individual.setFormat(QCoreApplication.translate("MainWindow", u"%v / %m", None))
        self.menu_File.setTitle(QCoreApplication.translate("MainWindow", u"File", None))
        self.menu_Profile.setTitle(QCoreApplication.translate("MainWindow", u"Profile", None))
        self.menu_set_default_profile.setTitle(QCoreApplication.translate("MainWindow", u"Set Default", None))
        self.menu_settings.setTitle(QCoreApplication.translate("MainWindow", u"Settings", None))
        self.menu_theme.setTitle(QCoreApplication.translate("MainWindow", u"Theme", u"As in color theme"))
        self.menu_language.setTitle(QCoreApplication.translate("MainWindow", u"Language", None))
        self.menu_post_actions.setTitle(QCoreApplication.translate("MainWindow", u"Post-Run Actions", None))
        self.menu_Help.setTitle(QCoreApplication.translate("MainWindow", u"Help", None))
    # retranslateUi

