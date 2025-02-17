# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'OutputReview.ui'
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
from PySide6.QtWidgets import (QAbstractItemView, QApplication, QComboBox, QFrame,
    QHBoxLayout, QLabel, QListView, QListWidget,
    QListWidgetItem, QPushButton, QSizePolicy, QSlider,
    QSpacerItem, QSplitter, QStackedWidget, QVBoxLayout,
    QWidget)

from pcleaner.gui.CustomQ.CElidedLabel import CElidedLabel
from pcleaner.gui.image_diff_viewers import (DifferenceViewer, OnionViewer, OverlayViewer, SwipeViewer)
from pcleaner.gui.image_viewer import ImageViewer

class Ui_OutputReview(object):
    def setupUi(self, OutputReview):
        if not OutputReview.objectName():
            OutputReview.setObjectName(u"OutputReview")
        OutputReview.resize(1400, 800)
        self.verticalLayout_7 = QVBoxLayout(OutputReview)
        self.verticalLayout_7.setObjectName(u"verticalLayout_7")
        self.verticalLayout_7.setContentsMargins(1, 1, 1, 1)
        self.splitter = QSplitter(OutputReview)
        self.splitter.setObjectName(u"splitter")
        self.splitter.setOrientation(Qt.Horizontal)
        self.layoutWidget = QWidget(self.splitter)
        self.layoutWidget.setObjectName(u"layoutWidget")
        self.verticalLayout_3 = QVBoxLayout(self.layoutWidget)
        self.verticalLayout_3.setObjectName(u"verticalLayout_3")
        self.verticalLayout_3.setContentsMargins(0, 0, 0, 0)
        self.horizontalLayout_2 = QHBoxLayout()
        self.horizontalLayout_2.setObjectName(u"horizontalLayout_2")
        self.horizontalLayout_2.setContentsMargins(6, 6, 6, 7)
        self.label_image_count = QLabel(self.layoutWidget)
        self.label_image_count.setObjectName(u"label_image_count")
        self.label_image_count.setText(u"<image count>")

        self.horizontalLayout_2.addWidget(self.label_image_count)

        self.horizontalSpacer = QSpacerItem(0, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_2.addItem(self.horizontalSpacer)

        self.label = QLabel(self.layoutWidget)
        self.label.setObjectName(u"label")

        self.horizontalLayout_2.addWidget(self.label)

        self.horizontalSlider_icon_size = QSlider(self.layoutWidget)
        self.horizontalSlider_icon_size.setObjectName(u"horizontalSlider_icon_size")
        self.horizontalSlider_icon_size.setMinimum(1)
        self.horizontalSlider_icon_size.setMaximum(1000)
        self.horizontalSlider_icon_size.setOrientation(Qt.Horizontal)

        self.horizontalLayout_2.addWidget(self.horizontalSlider_icon_size)

        self.pushButton_prev = QPushButton(self.layoutWidget)
        self.pushButton_prev.setObjectName(u"pushButton_prev")
        self.pushButton_prev.setText(u"")
        icon = QIcon()
        iconThemeName = u"arrow-left"
        if QIcon.hasThemeIcon(iconThemeName):
            icon = QIcon.fromTheme(iconThemeName)
        else:
            icon.addFile(u".", QSize(), QIcon.Mode.Normal, QIcon.State.Off)

        self.pushButton_prev.setIcon(icon)
        self.pushButton_prev.setFlat(True)

        self.horizontalLayout_2.addWidget(self.pushButton_prev)

        self.pushButton_next = QPushButton(self.layoutWidget)
        self.pushButton_next.setObjectName(u"pushButton_next")
        self.pushButton_next.setText(u"")
        icon1 = QIcon()
        iconThemeName = u"arrow-right"
        if QIcon.hasThemeIcon(iconThemeName):
            icon1 = QIcon.fromTheme(iconThemeName)
        else:
            icon1.addFile(u".", QSize(), QIcon.Mode.Normal, QIcon.State.Off)

        self.pushButton_next.setIcon(icon1)
        self.pushButton_next.setFlat(True)

        self.horizontalLayout_2.addWidget(self.pushButton_next)

        self.horizontalLayout_2.setStretch(1, 1)
        self.horizontalLayout_2.setStretch(3, 3)

        self.verticalLayout_3.addLayout(self.horizontalLayout_2)

        self.image_list = QListWidget(self.layoutWidget)
        self.image_list.setObjectName(u"image_list")
        self.image_list.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        self.image_list.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.image_list.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.image_list.setProperty(u"showDropIndicator", False)
        self.image_list.setDragDropMode(QAbstractItemView.NoDragDrop)
        self.image_list.setTextElideMode(Qt.ElideLeft)
        self.image_list.setVerticalScrollMode(QAbstractItemView.ScrollPerPixel)
        self.image_list.setHorizontalScrollMode(QAbstractItemView.ScrollPerPixel)
        self.image_list.setMovement(QListView.Static)
        self.image_list.setFlow(QListView.LeftToRight)
        self.image_list.setProperty(u"isWrapping", True)
        self.image_list.setResizeMode(QListView.Adjust)
        self.image_list.setLayoutMode(QListView.Batched)
        self.image_list.setViewMode(QListView.IconMode)
        self.image_list.setUniformItemSizes(False)
        self.image_list.setBatchSize(50)
        self.image_list.setWordWrap(False)
        self.image_list.setSelectionRectVisible(True)

        self.verticalLayout_3.addWidget(self.image_list)

        self.splitter.addWidget(self.layoutWidget)
        self.layoutWidget1 = QWidget(self.splitter)
        self.layoutWidget1.setObjectName(u"layoutWidget1")
        self.verticalLayout = QVBoxLayout(self.layoutWidget1)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.verticalLayout.setContentsMargins(0, 0, 0, 0)
        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setSpacing(6)
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.horizontalLayout.setContentsMargins(6, 6, 6, 6)
        self.label_file_name = CElidedLabel(self.layoutWidget1)
        self.label_file_name.setObjectName(u"label_file_name")
        sizePolicy = QSizePolicy(QSizePolicy.Policy.MinimumExpanding, QSizePolicy.Policy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.label_file_name.sizePolicy().hasHeightForWidth())
        self.label_file_name.setSizePolicy(sizePolicy)
        self.label_file_name.setFrameShape(QFrame.NoFrame)
        self.label_file_name.setFrameShadow(QFrame.Raised)

        self.horizontalLayout.addWidget(self.label_file_name)

        self.pushButton_zoom_in = QPushButton(self.layoutWidget1)
        self.pushButton_zoom_in.setObjectName(u"pushButton_zoom_in")
        icon2 = QIcon()
        iconThemeName = u"zoom-in"
        if QIcon.hasThemeIcon(iconThemeName):
            icon2 = QIcon.fromTheme(iconThemeName)
        else:
            icon2.addFile(u".", QSize(), QIcon.Mode.Normal, QIcon.State.Off)

        self.pushButton_zoom_in.setIcon(icon2)
        self.pushButton_zoom_in.setFlat(True)

        self.horizontalLayout.addWidget(self.pushButton_zoom_in)

        self.pushButton_zoom_out = QPushButton(self.layoutWidget1)
        self.pushButton_zoom_out.setObjectName(u"pushButton_zoom_out")
        icon3 = QIcon()
        iconThemeName = u"zoom-out"
        if QIcon.hasThemeIcon(iconThemeName):
            icon3 = QIcon.fromTheme(iconThemeName)
        else:
            icon3.addFile(u".", QSize(), QIcon.Mode.Normal, QIcon.State.Off)

        self.pushButton_zoom_out.setIcon(icon3)
        self.pushButton_zoom_out.setFlat(True)

        self.horizontalLayout.addWidget(self.pushButton_zoom_out)

        self.pushButton_zoom_reset = QPushButton(self.layoutWidget1)
        self.pushButton_zoom_reset.setObjectName(u"pushButton_zoom_reset")
        icon4 = QIcon()
        iconThemeName = u"zoom-original"
        if QIcon.hasThemeIcon(iconThemeName):
            icon4 = QIcon.fromTheme(iconThemeName)
        else:
            icon4.addFile(u".", QSize(), QIcon.Mode.Normal, QIcon.State.Off)

        self.pushButton_zoom_reset.setIcon(icon4)
        self.pushButton_zoom_reset.setFlat(True)

        self.horizontalLayout.addWidget(self.pushButton_zoom_reset)

        self.pushButton_zoom_fit = QPushButton(self.layoutWidget1)
        self.pushButton_zoom_fit.setObjectName(u"pushButton_zoom_fit")
        icon5 = QIcon()
        iconThemeName = u"zoom-fit-best"
        if QIcon.hasThemeIcon(iconThemeName):
            icon5 = QIcon.fromTheme(iconThemeName)
        else:
            icon5.addFile(u".", QSize(), QIcon.Mode.Normal, QIcon.State.Off)

        self.pushButton_zoom_fit.setIcon(icon5)
        self.pushButton_zoom_fit.setFlat(True)

        self.horizontalLayout.addWidget(self.pushButton_zoom_fit)

        self.label_2 = QLabel(self.layoutWidget1)
        self.label_2.setObjectName(u"label_2")

        self.horizontalLayout.addWidget(self.label_2)

        self.comboBox_view_mode = QComboBox(self.layoutWidget1)
        self.comboBox_view_mode.addItem("")
        self.comboBox_view_mode.addItem("")
        self.comboBox_view_mode.addItem("")
        self.comboBox_view_mode.addItem("")
        self.comboBox_view_mode.addItem("")
        self.comboBox_view_mode.setObjectName(u"comboBox_view_mode")

        self.horizontalLayout.addWidget(self.comboBox_view_mode)

        self.pushButton_done = QPushButton(self.layoutWidget1)
        self.pushButton_done.setObjectName(u"pushButton_done")

        self.horizontalLayout.addWidget(self.pushButton_done)


        self.verticalLayout.addLayout(self.horizontalLayout)

        self.stackedWidget = QStackedWidget(self.layoutWidget1)
        self.stackedWidget.setObjectName(u"stackedWidget")
        self.page_side_by_side = QWidget()
        self.page_side_by_side.setObjectName(u"page_side_by_side")
        self.horizontalLayout_3 = QHBoxLayout(self.page_side_by_side)
        self.horizontalLayout_3.setSpacing(4)
        self.horizontalLayout_3.setObjectName(u"horizontalLayout_3")
        self.horizontalLayout_3.setContentsMargins(0, 0, 0, 0)
        self.image_viewer_sbs_master = ImageViewer(self.page_side_by_side)
        self.image_viewer_sbs_master.setObjectName(u"image_viewer_sbs_master")

        self.horizontalLayout_3.addWidget(self.image_viewer_sbs_master)

        self.image_viewer_sbs_slave = ImageViewer(self.page_side_by_side)
        self.image_viewer_sbs_slave.setObjectName(u"image_viewer_sbs_slave")
        self.image_viewer_sbs_slave.setEnabled(False)
        self.image_viewer_sbs_slave.setInteractive(False)

        self.horizontalLayout_3.addWidget(self.image_viewer_sbs_slave)

        self.horizontalLayout_3.setStretch(0, 1)
        self.horizontalLayout_3.setStretch(1, 1)
        self.stackedWidget.addWidget(self.page_side_by_side)
        self.page_swipe = QWidget()
        self.page_swipe.setObjectName(u"page_swipe")
        self.verticalLayout_4 = QVBoxLayout(self.page_swipe)
        self.verticalLayout_4.setSpacing(0)
        self.verticalLayout_4.setObjectName(u"verticalLayout_4")
        self.verticalLayout_4.setContentsMargins(0, 0, 0, 0)
        self.image_viewer_swipe = SwipeViewer(self.page_swipe)
        self.image_viewer_swipe.setObjectName(u"image_viewer_swipe")

        self.verticalLayout_4.addWidget(self.image_viewer_swipe)

        self.horizontalLayout_5 = QHBoxLayout()
        self.horizontalLayout_5.setObjectName(u"horizontalLayout_5")
        self.horizontalLayout_5.setContentsMargins(0, 6, 0, 6)
        self.horizontalSpacer_2 = QSpacerItem(0, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_5.addItem(self.horizontalSpacer_2)

        self.horizontalSlider_swipe = QSlider(self.page_swipe)
        self.horizontalSlider_swipe.setObjectName(u"horizontalSlider_swipe")
        sizePolicy1 = QSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        sizePolicy1.setHorizontalStretch(0)
        sizePolicy1.setVerticalStretch(0)
        sizePolicy1.setHeightForWidth(self.horizontalSlider_swipe.sizePolicy().hasHeightForWidth())
        self.horizontalSlider_swipe.setSizePolicy(sizePolicy1)
        self.horizontalSlider_swipe.setOrientation(Qt.Horizontal)

        self.horizontalLayout_5.addWidget(self.horizontalSlider_swipe)

        self.horizontalSpacer_3 = QSpacerItem(0, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_5.addItem(self.horizontalSpacer_3)

        self.horizontalLayout_5.setStretch(0, 1)
        self.horizontalLayout_5.setStretch(1, 3)
        self.horizontalLayout_5.setStretch(2, 1)

        self.verticalLayout_4.addLayout(self.horizontalLayout_5)

        self.stackedWidget.addWidget(self.page_swipe)
        self.page_onion = QWidget()
        self.page_onion.setObjectName(u"page_onion")
        self.verticalLayout_5 = QVBoxLayout(self.page_onion)
        self.verticalLayout_5.setSpacing(0)
        self.verticalLayout_5.setObjectName(u"verticalLayout_5")
        self.verticalLayout_5.setContentsMargins(0, 0, 0, 0)
        self.image_viewer_onion = OnionViewer(self.page_onion)
        self.image_viewer_onion.setObjectName(u"image_viewer_onion")

        self.verticalLayout_5.addWidget(self.image_viewer_onion)

        self.horizontalLayout_6 = QHBoxLayout()
        self.horizontalLayout_6.setObjectName(u"horizontalLayout_6")
        self.horizontalLayout_6.setContentsMargins(0, 6, 0, 6)
        self.horizontalSpacer_6 = QSpacerItem(0, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_6.addItem(self.horizontalSpacer_6)

        self.horizontalSlider_onion = QSlider(self.page_onion)
        self.horizontalSlider_onion.setObjectName(u"horizontalSlider_onion")
        sizePolicy1.setHeightForWidth(self.horizontalSlider_onion.sizePolicy().hasHeightForWidth())
        self.horizontalSlider_onion.setSizePolicy(sizePolicy1)
        self.horizontalSlider_onion.setOrientation(Qt.Horizontal)

        self.horizontalLayout_6.addWidget(self.horizontalSlider_onion)

        self.horizontalSpacer_7 = QSpacerItem(0, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_6.addItem(self.horizontalSpacer_7)

        self.horizontalLayout_6.setStretch(0, 1)
        self.horizontalLayout_6.setStretch(1, 3)
        self.horizontalLayout_6.setStretch(2, 1)

        self.verticalLayout_5.addLayout(self.horizontalLayout_6)

        self.stackedWidget.addWidget(self.page_onion)
        self.page_difference = QWidget()
        self.page_difference.setObjectName(u"page_difference")
        self.verticalLayout_6 = QVBoxLayout(self.page_difference)
        self.verticalLayout_6.setSpacing(0)
        self.verticalLayout_6.setObjectName(u"verticalLayout_6")
        self.verticalLayout_6.setContentsMargins(0, 0, 0, 0)
        self.image_viewer_difference = DifferenceViewer(self.page_difference)
        self.image_viewer_difference.setObjectName(u"image_viewer_difference")

        self.verticalLayout_6.addWidget(self.image_viewer_difference)

        self.horizontalLayout_7 = QHBoxLayout()
        self.horizontalLayout_7.setSpacing(0)
        self.horizontalLayout_7.setObjectName(u"horizontalLayout_7")
        self.horizontalLayout_7.setContentsMargins(0, 6, 0, 6)
        self.horizontalSpacer_8 = QSpacerItem(0, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_7.addItem(self.horizontalSpacer_8)

        self.horizontalSlider_difference = QSlider(self.page_difference)
        self.horizontalSlider_difference.setObjectName(u"horizontalSlider_difference")
        sizePolicy1.setHeightForWidth(self.horizontalSlider_difference.sizePolicy().hasHeightForWidth())
        self.horizontalSlider_difference.setSizePolicy(sizePolicy1)
        self.horizontalSlider_difference.setOrientation(Qt.Horizontal)

        self.horizontalLayout_7.addWidget(self.horizontalSlider_difference)

        self.horizontalSpacer_9 = QSpacerItem(0, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_7.addItem(self.horizontalSpacer_9)

        self.horizontalLayout_7.setStretch(0, 1)
        self.horizontalLayout_7.setStretch(1, 3)
        self.horizontalLayout_7.setStretch(2, 1)

        self.verticalLayout_6.addLayout(self.horizontalLayout_7)

        self.stackedWidget.addWidget(self.page_difference)
        self.page_overlay = QWidget()
        self.page_overlay.setObjectName(u"page_overlay")
        self.verticalLayout_2 = QVBoxLayout(self.page_overlay)
        self.verticalLayout_2.setSpacing(0)
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.verticalLayout_2.setContentsMargins(0, 0, 0, 0)
        self.image_viewer_overlay = OverlayViewer(self.page_overlay)
        self.image_viewer_overlay.setObjectName(u"image_viewer_overlay")

        self.verticalLayout_2.addWidget(self.image_viewer_overlay)

        self.horizontalLayout_8 = QHBoxLayout()
        self.horizontalLayout_8.setSpacing(0)
        self.horizontalLayout_8.setObjectName(u"horizontalLayout_8")
        self.horizontalLayout_8.setContentsMargins(0, 6, 0, 6)
        self.horizontalSpacer_10 = QSpacerItem(0, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_8.addItem(self.horizontalSpacer_10)

        self.horizontalSlider_overlay = QSlider(self.page_overlay)
        self.horizontalSlider_overlay.setObjectName(u"horizontalSlider_overlay")
        sizePolicy1.setHeightForWidth(self.horizontalSlider_overlay.sizePolicy().hasHeightForWidth())
        self.horizontalSlider_overlay.setSizePolicy(sizePolicy1)
        self.horizontalSlider_overlay.setOrientation(Qt.Horizontal)

        self.horizontalLayout_8.addWidget(self.horizontalSlider_overlay)

        self.horizontalSpacer_11 = QSpacerItem(0, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_8.addItem(self.horizontalSpacer_11)

        self.horizontalLayout_8.setStretch(0, 1)
        self.horizontalLayout_8.setStretch(1, 3)
        self.horizontalLayout_8.setStretch(2, 1)

        self.verticalLayout_2.addLayout(self.horizontalLayout_8)

        self.stackedWidget.addWidget(self.page_overlay)

        self.verticalLayout.addWidget(self.stackedWidget)

        self.splitter.addWidget(self.layoutWidget1)

        self.verticalLayout_7.addWidget(self.splitter)


        self.retranslateUi(OutputReview)

        self.stackedWidget.setCurrentIndex(0)


        QMetaObject.connectSlotsByName(OutputReview)
    # setupUi

    def retranslateUi(self, OutputReview):
        OutputReview.setWindowTitle(QCoreApplication.translate("OutputReview", u"Review", None))
        self.label.setText(QCoreApplication.translate("OutputReview", u"Icon Size:", None))
#if QT_CONFIG(tooltip)
        self.pushButton_prev.setToolTip(QCoreApplication.translate("OutputReview", u"Previous image", None))
#endif // QT_CONFIG(tooltip)
#if QT_CONFIG(tooltip)
        self.pushButton_next.setToolTip(QCoreApplication.translate("OutputReview", u"Next image", None))
#endif // QT_CONFIG(tooltip)
#if QT_CONFIG(tooltip)
        self.pushButton_zoom_in.setToolTip(QCoreApplication.translate("OutputReview", u"Zoom in", None))
#endif // QT_CONFIG(tooltip)
        self.pushButton_zoom_in.setText("")
#if QT_CONFIG(tooltip)
        self.pushButton_zoom_out.setToolTip(QCoreApplication.translate("OutputReview", u"Zoom out", None))
#endif // QT_CONFIG(tooltip)
        self.pushButton_zoom_out.setText("")
#if QT_CONFIG(tooltip)
        self.pushButton_zoom_reset.setToolTip(QCoreApplication.translate("OutputReview", u"Reset zoom", None))
#endif // QT_CONFIG(tooltip)
        self.pushButton_zoom_reset.setText("")
#if QT_CONFIG(tooltip)
        self.pushButton_zoom_fit.setToolTip(QCoreApplication.translate("OutputReview", u"Zoom to fit", None))
#endif // QT_CONFIG(tooltip)
        self.pushButton_zoom_fit.setText("")
        self.label_2.setText(QCoreApplication.translate("OutputReview", u"View Mode:", None))
        self.comboBox_view_mode.setItemText(0, QCoreApplication.translate("OutputReview", u"Side-by-Side", None))
        self.comboBox_view_mode.setItemText(1, QCoreApplication.translate("OutputReview", u"Swipe", None))
        self.comboBox_view_mode.setItemText(2, QCoreApplication.translate("OutputReview", u"Onion", None))
        self.comboBox_view_mode.setItemText(3, QCoreApplication.translate("OutputReview", u"Difference", None))
        self.comboBox_view_mode.setItemText(4, QCoreApplication.translate("OutputReview", u"Overlay", None))

        self.pushButton_done.setText(QCoreApplication.translate("OutputReview", u"Done", None))
    # retranslateUi

