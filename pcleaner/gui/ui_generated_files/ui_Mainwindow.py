# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'Mainwindow.ui'
##
## Created by: Qt User Interface Compiler version 6.4.0
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
from PySide6.QtWidgets import (QAbstractItemView, QApplication, QCheckBox, QFormLayout,
    QFrame, QGroupBox, QHBoxLayout, QHeaderView,
    QLabel, QLineEdit, QMainWindow, QMenu,
    QMenuBar, QProgressBar, QPushButton, QRadioButton,
    QSizePolicy, QSpacerItem, QSplitter, QStatusBar,
    QTabWidget, QTableWidgetItem, QTextEdit, QVBoxLayout,
    QWidget)

from pcleaner.gui.CustomQ.CComboBox import CComboBox
from pcleaner.gui.file_table import FileTable

class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        if not MainWindow.objectName():
            MainWindow.setObjectName(u"MainWindow")
        MainWindow.resize(1701, 720)
        self.action_Open_Files = QAction(MainWindow)
        self.action_Open_Files.setObjectName(u"action_Open_Files")
        self.action_Clear_Files = QAction(MainWindow)
        self.action_Clear_Files.setObjectName(u"action_Clear_Files")
        self.action_New_Profile_2 = QAction(MainWindow)
        self.action_New_Profile_2.setObjectName(u"action_New_Profile_2")
        self.action_Delete_Profile = QAction(MainWindow)
        self.action_Delete_Profile.setObjectName(u"action_Delete_Profile")
        self.action_Import_Profile = QAction(MainWindow)
        self.action_Import_Profile.setObjectName(u"action_Import_Profile")
        self.action_Open_Log = QAction(MainWindow)
        self.action_Open_Log.setObjectName(u"action_Open_Log")
        self.action_Panel_Cleaner_Documentation = QAction(MainWindow)
        self.action_Panel_Cleaner_Documentation.setObjectName(u"action_Panel_Cleaner_Documentation")
        self.action_Source_Code = QAction(MainWindow)
        self.action_Source_Code.setObjectName(u"action_Source_Code")
        self.actionView_License = QAction(MainWindow)
        self.actionView_License.setObjectName(u"actionView_License")
        self.action_Save = QAction(MainWindow)
        self.action_Save.setObjectName(u"action_Save")
        self.action_Save_as = QAction(MainWindow)
        self.action_Save_as.setObjectName(u"action_Save_as")
        self.action_Apply_Denoising = QAction(MainWindow)
        self.action_Apply_Denoising.setObjectName(u"action_Apply_Denoising")
        self.action_Apply_Denoising.setCheckable(True)
        self.action_Apply_Denoising.setChecked(True)
        self.actionShow_Terminal_Command = QAction(MainWindow)
        self.actionShow_Terminal_Command.setObjectName(u"actionShow_Terminal_Command")
        self.action_System_Theme = QAction(MainWindow)
        self.action_System_Theme.setObjectName(u"action_System_Theme")
        self.action_Dark = QAction(MainWindow)
        self.action_Dark.setObjectName(u"action_Dark")
        self.action_Light = QAction(MainWindow)
        self.action_Light.setObjectName(u"action_Light")
        self.action_temp = QAction(MainWindow)
        self.action_temp.setObjectName(u"action_temp")
        self.action_temp_2 = QAction(MainWindow)
        self.action_temp_2.setObjectName(u"action_temp_2")
        self.centralwidget = QWidget(MainWindow)
        self.centralwidget.setObjectName(u"centralwidget")
        self.verticalLayout = QVBoxLayout(self.centralwidget)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.verticalLayout.setContentsMargins(1, 4, 1, 1)
        self.splitter = QSplitter(self.centralwidget)
        self.splitter.setObjectName(u"splitter")
        self.splitter.setOrientation(Qt.Horizontal)
        self.splitter.setHandleWidth(10)
        self.groupBox = QGroupBox(self.splitter)
        self.groupBox.setObjectName(u"groupBox")
        self.verticalLayout_2 = QVBoxLayout(self.groupBox)
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.horizontalLayout_2 = QHBoxLayout()
        self.horizontalLayout_2.setObjectName(u"horizontalLayout_2")
        self.comboBox_current_profile = CComboBox(self.groupBox)
        self.comboBox_current_profile.addItem("")
        self.comboBox_current_profile.setObjectName(u"comboBox_current_profile")
        sizePolicy = QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.comboBox_current_profile.sizePolicy().hasHeightForWidth())
        self.comboBox_current_profile.setSizePolicy(sizePolicy)
        self.comboBox_current_profile.setMinimumSize(QSize(48, 0))

        self.horizontalLayout_2.addWidget(self.comboBox_current_profile)

        self.pushButton_save_profile = QPushButton(self.groupBox)
        self.pushButton_save_profile.setObjectName(u"pushButton_save_profile")
        self.pushButton_save_profile.setEnabled(False)
        icon = QIcon()
        iconThemeName = u"document-save"
        if QIcon.hasThemeIcon(iconThemeName):
            icon = QIcon.fromTheme(iconThemeName)
        else:
            icon.addFile(u".", QSize(), QIcon.Normal, QIcon.Off)
        
        self.pushButton_save_profile.setIcon(icon)

        self.horizontalLayout_2.addWidget(self.pushButton_save_profile)

        self.pushButton_reset_profile = QPushButton(self.groupBox)
        self.pushButton_reset_profile.setObjectName(u"pushButton_reset_profile")
        self.pushButton_reset_profile.setEnabled(False)
        icon1 = QIcon()
        iconThemeName = u"document-revert"
        if QIcon.hasThemeIcon(iconThemeName):
            icon1 = QIcon.fromTheme(iconThemeName)
        else:
            icon1.addFile(u".", QSize(), QIcon.Normal, QIcon.Off)
        
        self.pushButton_reset_profile.setIcon(icon1)

        self.horizontalLayout_2.addWidget(self.pushButton_reset_profile)

        self.pushButton_apply_profile = QPushButton(self.groupBox)
        self.pushButton_apply_profile.setObjectName(u"pushButton_apply_profile")
        self.pushButton_apply_profile.setEnabled(False)
        icon2 = QIcon()
        iconThemeName = u"dialog-ok-apply"
        if QIcon.hasThemeIcon(iconThemeName):
            icon2 = QIcon.fromTheme(iconThemeName)
        else:
            icon2.addFile(u".", QSize(), QIcon.Normal, QIcon.Off)
        
        self.pushButton_apply_profile.setIcon(icon2)

        self.horizontalLayout_2.addWidget(self.pushButton_apply_profile)


        self.verticalLayout_2.addLayout(self.horizontalLayout_2)

        self.toolBox_profile_frame = QWidget(self.groupBox)
        self.toolBox_profile_frame.setObjectName(u"toolBox_profile_frame")
        sizePolicy1 = QSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)
        sizePolicy1.setHorizontalStretch(0)
        sizePolicy1.setVerticalStretch(0)
        sizePolicy1.setHeightForWidth(self.toolBox_profile_frame.sizePolicy().hasHeightForWidth())
        self.toolBox_profile_frame.setSizePolicy(sizePolicy1)

        self.verticalLayout_2.addWidget(self.toolBox_profile_frame)

        self.splitter.addWidget(self.groupBox)
        self.tabWidget_files = QTabWidget(self.splitter)
        self.tabWidget_files.setObjectName(u"tabWidget_files")
        self.tabWidget_table_page = QWidget()
        self.tabWidget_table_page.setObjectName(u"tabWidget_table_page")
        self.verticalLayout_3 = QVBoxLayout(self.tabWidget_table_page)
        self.verticalLayout_3.setSpacing(0)
        self.verticalLayout_3.setObjectName(u"verticalLayout_3")
        self.verticalLayout_3.setContentsMargins(0, 0, 0, 0)
        self.file_table = FileTable(self.tabWidget_table_page)
        if (self.file_table.columnCount() < 5):
            self.file_table.setColumnCount(5)
        __qtablewidgetitem = QTableWidgetItem()
        self.file_table.setHorizontalHeaderItem(0, __qtablewidgetitem)
        __qtablewidgetitem1 = QTableWidgetItem()
        self.file_table.setHorizontalHeaderItem(1, __qtablewidgetitem1)
        __qtablewidgetitem2 = QTableWidgetItem()
        self.file_table.setHorizontalHeaderItem(2, __qtablewidgetitem2)
        __qtablewidgetitem3 = QTableWidgetItem()
        self.file_table.setHorizontalHeaderItem(3, __qtablewidgetitem3)
        __qtablewidgetitem4 = QTableWidgetItem()
        self.file_table.setHorizontalHeaderItem(4, __qtablewidgetitem4)
        self.file_table.setObjectName(u"file_table")
        self.file_table.setFrameShape(QFrame.NoFrame)
        self.file_table.setFrameShadow(QFrame.Plain)
        self.file_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.file_table.setDragDropOverwriteMode(False)
        self.file_table.setDragDropMode(QAbstractItemView.NoDragDrop)
        self.file_table.setAlternatingRowColors(True)
        self.file_table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.file_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.file_table.setSortingEnabled(True)
        self.file_table.setCornerButtonEnabled(False)

        self.verticalLayout_3.addWidget(self.file_table)

        self.tabWidget_files.addTab(self.tabWidget_table_page, "")
        self.splitter.addWidget(self.tabWidget_files)
        self.frame_3 = QFrame(self.splitter)
        self.frame_3.setObjectName(u"frame_3")
        self.frame_3.setFrameShape(QFrame.StyledPanel)
        self.frame_3.setFrameShadow(QFrame.Raised)
        self.verticalLayout_4 = QVBoxLayout(self.frame_3)
        self.verticalLayout_4.setObjectName(u"verticalLayout_4")
        self.horizontalLayout_3 = QHBoxLayout()
        self.horizontalLayout_3.setObjectName(u"horizontalLayout_3")
        self.groupBox_4 = QGroupBox(self.frame_3)
        self.groupBox_4.setObjectName(u"groupBox_4")
        self.verticalLayout_9 = QVBoxLayout(self.groupBox_4)
        self.verticalLayout_9.setObjectName(u"verticalLayout_9")
        self.radioButton_cleaning = QRadioButton(self.groupBox_4)
        self.radioButton_cleaning.setObjectName(u"radioButton_cleaning")
        self.radioButton_cleaning.setChecked(True)

        self.verticalLayout_9.addWidget(self.radioButton_cleaning)

        self.radioButton_ocr = QRadioButton(self.groupBox_4)
        self.radioButton_ocr.setObjectName(u"radioButton_ocr")

        self.verticalLayout_9.addWidget(self.radioButton_ocr)

        self.verticalSpacer = QSpacerItem(20, 0, QSizePolicy.Minimum, QSizePolicy.Expanding)

        self.verticalLayout_9.addItem(self.verticalSpacer)

        self.verticalLayout_7 = QVBoxLayout()
        self.verticalLayout_7.setObjectName(u"verticalLayout_7")
        self.label_warning = QLabel(self.groupBox_4)
        self.label_warning.setObjectName(u"label_warning")
        sizePolicy2 = QSizePolicy(QSizePolicy.Minimum, QSizePolicy.Minimum)
        sizePolicy2.setHorizontalStretch(0)
        sizePolicy2.setVerticalStretch(0)
        sizePolicy2.setHeightForWidth(self.label_warning.sizePolicy().hasHeightForWidth())
        self.label_warning.setSizePolicy(sizePolicy2)

        self.verticalLayout_7.addWidget(self.label_warning)

        self.pushButton_start = QPushButton(self.groupBox_4)
        self.pushButton_start.setObjectName(u"pushButton_start")
        icon3 = QIcon()
        iconThemeName = u"media-playback-start"
        if QIcon.hasThemeIcon(iconThemeName):
            icon3 = QIcon.fromTheme(iconThemeName)
        else:
            icon3.addFile(u".", QSize(), QIcon.Normal, QIcon.Off)
        
        self.pushButton_start.setIcon(icon3)

        self.verticalLayout_7.addWidget(self.pushButton_start)

        self.pushButton_abort = QPushButton(self.groupBox_4)
        self.pushButton_abort.setObjectName(u"pushButton_abort")
        icon4 = QIcon()
        iconThemeName = u"process-stop"
        if QIcon.hasThemeIcon(iconThemeName):
            icon4 = QIcon.fromTheme(iconThemeName)
        else:
            icon4.addFile(u".", QSize(), QIcon.Normal, QIcon.Off)
        
        self.pushButton_abort.setIcon(icon4)

        self.verticalLayout_7.addWidget(self.pushButton_abort)


        self.verticalLayout_9.addLayout(self.verticalLayout_7)


        self.horizontalLayout_3.addWidget(self.groupBox_4)

        self.groupBox_3 = QGroupBox(self.frame_3)
        self.groupBox_3.setObjectName(u"groupBox_3")
        self.verticalLayout_5 = QVBoxLayout(self.groupBox_3)
        self.verticalLayout_5.setObjectName(u"verticalLayout_5")
        self.checkBox_save_clean = QCheckBox(self.groupBox_3)
        self.checkBox_save_clean.setObjectName(u"checkBox_save_clean")
        self.checkBox_save_clean.setChecked(True)

        self.verticalLayout_5.addWidget(self.checkBox_save_clean)

        self.checkBox_save_mask = QCheckBox(self.groupBox_3)
        self.checkBox_save_mask.setObjectName(u"checkBox_save_mask")
        self.checkBox_save_mask.setChecked(True)

        self.verticalLayout_5.addWidget(self.checkBox_save_mask)

        self.checkBox_save_text = QCheckBox(self.groupBox_3)
        self.checkBox_save_text.setObjectName(u"checkBox_save_text")

        self.verticalLayout_5.addWidget(self.checkBox_save_text)

        self.verticalSpacer_2 = QSpacerItem(20, 1, QSizePolicy.Minimum, QSizePolicy.Expanding)

        self.verticalLayout_5.addItem(self.verticalSpacer_2)

        self.label_4 = QLabel(self.groupBox_3)
        self.label_4.setObjectName(u"label_4")
        self.label_4.setTextInteractionFlags(Qt.LinksAccessibleByMouse)

        self.verticalLayout_5.addWidget(self.label_4)

        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.lineEdit_out_directory = QLineEdit(self.groupBox_3)
        self.lineEdit_out_directory.setObjectName(u"lineEdit_out_directory")

        self.horizontalLayout.addWidget(self.lineEdit_out_directory)

        self.pushButton_browse_out_dir = QPushButton(self.groupBox_3)
        self.pushButton_browse_out_dir.setObjectName(u"pushButton_browse_out_dir")
        icon5 = QIcon()
        iconThemeName = u"document-open-folder"
        if QIcon.hasThemeIcon(iconThemeName):
            icon5 = QIcon.fromTheme(iconThemeName)
        else:
            icon5.addFile(u".", QSize(), QIcon.Normal, QIcon.Off)
        
        self.pushButton_browse_out_dir.setIcon(icon5)

        self.horizontalLayout.addWidget(self.pushButton_browse_out_dir)


        self.verticalLayout_5.addLayout(self.horizontalLayout)


        self.horizontalLayout_3.addWidget(self.groupBox_3)

        self.horizontalLayout_3.setStretch(0, 1)
        self.horizontalLayout_3.setStretch(1, 3)

        self.verticalLayout_4.addLayout(self.horizontalLayout_3)

        self.textEdit_analytics = QTextEdit(self.frame_3)
        self.textEdit_analytics.setObjectName(u"textEdit_analytics")
        self.textEdit_analytics.setUndoRedoEnabled(False)
        self.textEdit_analytics.setLineWrapMode(QTextEdit.NoWrap)
        self.textEdit_analytics.setLineWrapColumnOrWidth(100)
        self.textEdit_analytics.setReadOnly(True)

        self.verticalLayout_4.addWidget(self.textEdit_analytics)

        self.verticalLayout_4.setStretch(1, 1)
        self.splitter.addWidget(self.frame_3)

        self.verticalLayout.addWidget(self.splitter)

        self.widget_progress_drawer = QWidget(self.centralwidget)
        self.widget_progress_drawer.setObjectName(u"widget_progress_drawer")
        self.formLayout = QFormLayout(self.widget_progress_drawer)
        self.formLayout.setObjectName(u"formLayout")
        self.formLayout.setVerticalSpacing(4)
        self.label_progress_step = QLabel(self.widget_progress_drawer)
        self.label_progress_step.setObjectName(u"label_progress_step")

        self.formLayout.setWidget(0, QFormLayout.LabelRole, self.label_progress_step)

        self.progressBar_individual = QProgressBar(self.widget_progress_drawer)
        self.progressBar_individual.setObjectName(u"progressBar_individual")
        self.progressBar_individual.setValue(24)

        self.formLayout.setWidget(0, QFormLayout.FieldRole, self.progressBar_individual)

        self.label_2 = QLabel(self.widget_progress_drawer)
        self.label_2.setObjectName(u"label_2")

        self.formLayout.setWidget(1, QFormLayout.LabelRole, self.label_2)

        self.progressBar_total = QProgressBar(self.widget_progress_drawer)
        self.progressBar_total.setObjectName(u"progressBar_total")
        self.progressBar_total.setValue(24)
        self.progressBar_total.setTextVisible(True)

        self.formLayout.setWidget(1, QFormLayout.FieldRole, self.progressBar_total)


        self.verticalLayout.addWidget(self.widget_progress_drawer)

        self.verticalLayout.setStretch(0, 1)
        MainWindow.setCentralWidget(self.centralwidget)
        self.menubar = QMenuBar(MainWindow)
        self.menubar.setObjectName(u"menubar")
        self.menubar.setGeometry(QRect(0, 0, 1701, 34))
        self.menu_File = QMenu(self.menubar)
        self.menu_File.setObjectName(u"menu_File")
        self.menu_Profile = QMenu(self.menubar)
        self.menu_Profile.setObjectName(u"menu_Profile")
        self.menuCurrent_Profile = QMenu(self.menu_Profile)
        self.menuCurrent_Profile.setObjectName(u"menuCurrent_Profile")
        self.menuSet_Default = QMenu(self.menu_Profile)
        self.menuSet_Default.setObjectName(u"menuSet_Default")
        self.menu_Settings = QMenu(self.menubar)
        self.menu_Settings.setObjectName(u"menu_Settings")
        self.menu_Theme = QMenu(self.menu_Settings)
        self.menu_Theme.setObjectName(u"menu_Theme")
        self.menu_Help = QMenu(self.menubar)
        self.menu_Help.setObjectName(u"menu_Help")
        MainWindow.setMenuBar(self.menubar)
        self.statusbar = QStatusBar(MainWindow)
        self.statusbar.setObjectName(u"statusbar")
        MainWindow.setStatusBar(self.statusbar)
#if QT_CONFIG(shortcut)
        self.label_4.setBuddy(self.lineEdit_out_directory)
#endif // QT_CONFIG(shortcut)

        self.menubar.addAction(self.menu_File.menuAction())
        self.menubar.addAction(self.menu_Profile.menuAction())
        self.menubar.addAction(self.menu_Settings.menuAction())
        self.menubar.addAction(self.menu_Help.menuAction())
        self.menu_File.addAction(self.action_Open_Files)
        self.menu_File.addAction(self.action_Clear_Files)
        self.menu_Profile.addAction(self.menuCurrent_Profile.menuAction())
        self.menu_Profile.addSeparator()
        self.menu_Profile.addAction(self.action_New_Profile_2)
        self.menu_Profile.addAction(self.action_Import_Profile)
        self.menu_Profile.addSeparator()
        self.menu_Profile.addAction(self.action_Save)
        self.menu_Profile.addAction(self.action_Save_as)
        self.menu_Profile.addSeparator()
        self.menu_Profile.addAction(self.action_Delete_Profile)
        self.menu_Profile.addSeparator()
        self.menu_Profile.addAction(self.menuSet_Default.menuAction())
        self.menuCurrent_Profile.addAction(self.action_temp)
        self.menuSet_Default.addAction(self.action_temp_2)
        self.menu_Settings.addAction(self.menu_Theme.menuAction())
        self.menu_Settings.addAction(self.action_Open_Log)
        self.menu_Theme.addAction(self.action_System_Theme)
        self.menu_Theme.addSeparator()
        self.menu_Theme.addAction(self.action_Dark)
        self.menu_Theme.addAction(self.action_Light)
        self.menu_Help.addAction(self.action_Panel_Cleaner_Documentation)
        self.menu_Help.addAction(self.action_Source_Code)
        self.menu_Help.addSeparator()
        self.menu_Help.addAction(self.actionShow_Terminal_Command)

        self.retranslateUi(MainWindow)

        QMetaObject.connectSlotsByName(MainWindow)
    # setupUi

    def retranslateUi(self, MainWindow):
        MainWindow.setWindowTitle(QCoreApplication.translate("MainWindow", u"Panel Cleaner", None))
        self.action_Open_Files.setText(QCoreApplication.translate("MainWindow", u"Open Files", None))
        self.action_Clear_Files.setText(QCoreApplication.translate("MainWindow", u"Clear Files", None))
        self.action_New_Profile_2.setText(QCoreApplication.translate("MainWindow", u"New", None))
        self.action_Delete_Profile.setText(QCoreApplication.translate("MainWindow", u"Delete", None))
        self.action_Import_Profile.setText(QCoreApplication.translate("MainWindow", u"Import...", None))
        self.action_Open_Log.setText(QCoreApplication.translate("MainWindow", u"Open Log", None))
        self.action_Panel_Cleaner_Documentation.setText(QCoreApplication.translate("MainWindow", u"Online Documentation", None))
        self.action_Source_Code.setText(QCoreApplication.translate("MainWindow", u"About Panel Cleaner", None))
        self.actionView_License.setText(QCoreApplication.translate("MainWindow", u"View License", None))
        self.action_Save.setText(QCoreApplication.translate("MainWindow", u"Save", None))
        self.action_Save_as.setText(QCoreApplication.translate("MainWindow", u"Save as...", None))
        self.action_Apply_Denoising.setText(QCoreApplication.translate("MainWindow", u"Apply Denoising", None))
        self.actionShow_Terminal_Command.setText(QCoreApplication.translate("MainWindow", u"Show Terminal Command", None))
        self.action_System_Theme.setText(QCoreApplication.translate("MainWindow", u"System", None))
        self.action_Dark.setText(QCoreApplication.translate("MainWindow", u"Dark", None))
        self.action_Light.setText(QCoreApplication.translate("MainWindow", u"Light", None))
        self.action_temp.setText(QCoreApplication.translate("MainWindow", u"<temp>", None))
        self.action_temp_2.setText(QCoreApplication.translate("MainWindow", u"<temp>", None))
        self.groupBox.setTitle(QCoreApplication.translate("MainWindow", u"Profile", None))
        self.comboBox_current_profile.setItemText(0, QCoreApplication.translate("MainWindow", u"Default", None))

        self.pushButton_save_profile.setText(QCoreApplication.translate("MainWindow", u"Save", None))
        self.pushButton_reset_profile.setText(QCoreApplication.translate("MainWindow", u"Reset All", None))
        self.pushButton_apply_profile.setText(QCoreApplication.translate("MainWindow", u"Apply", None))
        ___qtablewidgetitem = self.file_table.horizontalHeaderItem(0)
        ___qtablewidgetitem.setText(QCoreApplication.translate("MainWindow", u"id", None));
        ___qtablewidgetitem1 = self.file_table.horizontalHeaderItem(1)
        ___qtablewidgetitem1.setText(QCoreApplication.translate("MainWindow", u"File", None));
        ___qtablewidgetitem2 = self.file_table.horizontalHeaderItem(2)
        ___qtablewidgetitem2.setText(QCoreApplication.translate("MainWindow", u"Size", None));
        ___qtablewidgetitem3 = self.file_table.horizontalHeaderItem(3)
        ___qtablewidgetitem3.setText(QCoreApplication.translate("MainWindow", u"Status", None));
        ___qtablewidgetitem4 = self.file_table.horizontalHeaderItem(4)
        ___qtablewidgetitem4.setText(QCoreApplication.translate("MainWindow", u"Output", None));
        self.tabWidget_files.setTabText(self.tabWidget_files.indexOf(self.tabWidget_table_page), QCoreApplication.translate("MainWindow", u"Images", None))
        self.groupBox_4.setTitle(QCoreApplication.translate("MainWindow", u"Process", None))
        self.radioButton_cleaning.setText(QCoreApplication.translate("MainWindow", u"Cleaning", None))
        self.radioButton_ocr.setText(QCoreApplication.translate("MainWindow", u"OCR", None))
        self.label_warning.setText(QCoreApplication.translate("MainWindow", u"Warning", None))
        self.pushButton_start.setText(QCoreApplication.translate("MainWindow", u"Start", None))
        self.pushButton_abort.setText(QCoreApplication.translate("MainWindow", u"Abort", None))
        self.groupBox_3.setTitle(QCoreApplication.translate("MainWindow", u"Output", None))
        self.checkBox_save_clean.setText(QCoreApplication.translate("MainWindow", u"Cleaned Image", None))
        self.checkBox_save_mask.setText(QCoreApplication.translate("MainWindow", u"Mask", None))
        self.checkBox_save_text.setText(QCoreApplication.translate("MainWindow", u"Extracted Text", None))
        self.label_4.setText(QCoreApplication.translate("MainWindow", u"Output Directory:", None))
        self.pushButton_browse_out_dir.setText("")
        self.textEdit_analytics.setHtml(QCoreApplication.translate("MainWindow", u"<!DOCTYPE HTML PUBLIC \"-//W3C//DTD HTML 4.0//EN\" \"http://www.w3.org/TR/REC-html40/strict.dtd\">\n"
"<html><head><meta name=\"qrichtext\" content=\"1\" /><style type=\"text/css\">\n"
"p, li { white-space: pre-wrap; }\n"
"</style></head><body style=\" font-family:'Noto Sans'; font-size:10pt; font-weight:400; font-style:normal;\">\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" font-family:'Noto Mono','Monospace';\">Mask Fitment Analytics <br />---------------------- <br />Total boxes: 5 | Masks succeeded: 5 (100%) | Masks failed: </span><span style=\" font-family:'Noto Mono','Monospace'; color:#b21818;\">0</span><span style=\" font-family:'Noto Mono','Monospace';\"> <br />Perfect masks: </span><span style=\" font-family:'Noto Mono','Monospace'; color:#18b2b2;\">5</span><span style=\" font-family:'Noto Mono','Monospace';\"> (100%) | Average border deviation: 0.00 <br /><br />Mask usage by mask size (smallest to largest)"
                        ": <br />Mask 0  :  </span><span style=\" font-family:'Noto Mono','Monospace'; color:#18b2b2;\">0</span><span style=\" font-family:'Noto Mono','Monospace';\"> / 0 <br />Mask 1  :  </span><span style=\" font-family:'Noto Mono','Monospace'; color:#18b2b2;\">0</span><span style=\" font-family:'Noto Mono','Monospace';\"> / 0 <br />Mask 2  :  </span><span style=\" font-family:'Noto Mono','Monospace'; color:#18b2b2;\">0</span><span style=\" font-family:'Noto Mono','Monospace';\"> / 0 <br />Mask 3  :  </span><span style=\" font-family:'Noto Mono','Monospace'; color:#18b2b2;\">0</span><span style=\" font-family:'Noto Mono','Monospace';\"> / 0 <br />Mask 4  :  </span><span style=\" font-family:'Noto Mono','Monospace'; color:#18b2b2;\">0</span><span style=\" font-family:'Noto Mono','Monospace';\"> / 0 <br />Mask 5  :  </span><span style=\" font-family:'Noto Mono','Monospace'; color:#18b2b2;\">0</span><span style=\" font-family:'Noto Mono','Monospace';\"> / 0 <br />Mask 6  : </span><span style=\" font-family:'Noto Mono','"
                        "Monospace'; color:#18b2b2;\">\u2588\u2588\u2588\u2588\u2588\u2588\u2588\u2588\u2588\u2588\u2588\u2588\u2588\u2588\u2588\u2588\u2588\u2588\u2588\u2588\u2588\u2588\u2588\u2588\u2588\u2588\u2588\u2588\u2588\u2588\u2588\u2588\u2588\u2588\u2588\u2588\u2588\u2588\u2588\u2588</span><span style=\" font-family:'Noto Mono','Monospace';\"> </span><span style=\" font-family:'Noto Mono','Monospace'; color:#18b2b2;\">1</span><span style=\" font-family:'Noto Mono','Monospace';\"> / 1 <br />Mask 7  :  </span><span style=\" font-family:'Noto Mono','Monospace'; color:#18b2b2;\">0</span><span style=\" font-family:'Noto Mono','Monospace';\"> / 0 <br />Mask 8  :  </span><span style=\" font-family:'Noto Mono','Monospace'; color:#18b2b2;\">0</span><span style=\" font-family:'Noto Mono','Monospace';\"> / 0 <br />Mask 9  :  </span><span style=\" font-family:'Noto Mono','Monospace'; color:#18b2b2;\">0</span><span style=\" font-family:'Noto Mono','Monospace';\"> / 0 <br />Mask 10 :  </span><span style=\" font-family:'Noto Mono','Monospa"
                        "ce'; color:#18b2b2;\">0</span><span style=\" font-family:'Noto Mono','Monospace';\"> / 0 <br />Box mask: </span><span style=\" font-family:'Noto Mono','Monospace'; color:#18b2b2;\">\u2588\u2588\u2588\u2588\u2588\u2588\u2588\u2588\u2588\u2588\u2588\u2588\u2588\u2588\u2588\u2588\u2588\u2588\u2588\u2588\u2588\u2588\u2588\u2588\u2588\u2588\u2588\u2588\u2588\u2588\u2588\u2588\u2588\u2588\u2588\u2588\u2588\u2588\u2588\u2588</span><span style=\" font-family:'Noto Mono','Monospace';\"> </span><span style=\" font-family:'Noto Mono','Monospace'; color:#18b2b2;\">4</span><span style=\" font-family:'Noto Mono','Monospace';\"> / 4 <br /><br /></span><span style=\" font-family:'Noto Mono','Monospace'; color:#18b2b2;\">\u2588 Perfect</span><span style=\" font-family:'Noto Mono','Monospace';\"> | \u2588 Total<br /><br /></span></p></body></html>", None))
        self.label_progress_step.setText(QCoreApplication.translate("MainWindow", u"Current Step:", None))
        self.label_2.setText(QCoreApplication.translate("MainWindow", u"Total Progress:", None))
        self.menu_File.setTitle(QCoreApplication.translate("MainWindow", u"File", None))
        self.menu_Profile.setTitle(QCoreApplication.translate("MainWindow", u"Profile", None))
        self.menuCurrent_Profile.setTitle(QCoreApplication.translate("MainWindow", u"Current Profile", None))
        self.menuSet_Default.setTitle(QCoreApplication.translate("MainWindow", u"Set Default", None))
        self.menu_Settings.setTitle(QCoreApplication.translate("MainWindow", u"Settings", None))
        self.menu_Theme.setTitle(QCoreApplication.translate("MainWindow", u"Theme", None))
        self.menu_Help.setTitle(QCoreApplication.translate("MainWindow", u"Help", None))
    # retranslateUi

