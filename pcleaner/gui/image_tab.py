from pathlib import Path
import PySide6.QtGui as Qg
import PySide6.QtWidgets as Qw
from PySide6.QtCore import Signal, Slot

import pcleaner.gui.image_file as st
import pcleaner.gui.image_details_driver as idd

from logzero import logger


# noinspection PyPep8Naming
class ImageTab(Qw.QTabWidget):
    """
    Manage the static tab for the file table and the dynamic tabs showing the image
    previews/outputs.
    """

    # Currently open dynamic tabs: path -> (image structure, tab's widget)
    open_images: dict[Path, tuple[st.ImageFile, Qw.QWidget]]

    def __init__(self, parent=None):
        Qw.QTabWidget.__init__(self, parent)
        self.setAcceptDrops(True)

        self.open_images = {}

        self.tabCloseRequested.connect(self.tab_close)

    def open_image(self, image_obj: st.ImageFile):
        """
        Check if the image is already open, in which case show it.
        Otherwise create a new tab.

        :param image_obj: Image object to open.
        """
        if image_obj.path in self.open_images:
            self.setCurrentWidget(self.open_images[image_obj.path][1])
            return

        # Create the tab.
        tab = idd.ImageDetailsWidget(image_obj=image_obj)
        self.addTab(tab, image_obj.path.name)
        self.open_images[image_obj.path] = (image_obj, tab)
        self.setCurrentWidget(tab)

    @Slot(int)
    def tab_close(self, index: int):
        """
        Close the image details tab.

        :param index: The index of the tab to close.
        """
        # Make sure the index is not the primary tab.
        if index == 0:
            logger.warning("Attempted to close the primary tab.")
            return
        logger.debug(f"Closing tab at index {index}.")
        # The tab we're closing must be an image details tab.
        # noinspection PyTypeChecker
        widget_to_close: idd.ImageDetailsWidget = self.widget(index)
        path = widget_to_close.image_obj.path
        self.open_images.pop(path)
        self.removeTab(index)
