from pathlib import Path
from typing import Callable

import PySide6.QtCore as Qc
import PySide6.QtWidgets as Qw
from PySide6.QtCore import Slot
from loguru import logger

import pcleaner.config as cfg
import pcleaner.gui.image_details_driver as idd
import pcleaner.gui.image_file as imf
import pcleaner.output_structures as ost
import pcleaner.gui.structures as st
import pcleaner.ocr.ocr as ocr


# noinspection PyPep8Naming
class ImageTab(Qw.QTabWidget):
    """
    Manage the static tab for the file table and the dynamic tabs showing the image
    previews/outputs.
    """

    # Currently open dynamic tabs: path -> (image structure, tab's widget)
    open_images: dict[Path, tuple[imf.ImageFile, Qw.QWidget]]

    def __init__(self, parent=None) -> None:
        Qw.QTabWidget.__init__(self, parent)
        self.setAcceptDrops(True)

        self.open_images = {}

        self.tabCloseRequested.connect(self.tab_close)
        self.currentChanged.connect(lambda _: self.update_tabs())

    @Slot(imf.ImageFile)
    def open_image(
        self,
        image_obj: imf.ImageFile,
        config: cfg.Config,
        shared_ocr_model: st.Shared[ocr.OCREngineFactory],
        thread_queue: Qc.QThreadPool,
        progress_callback: Callable[[ost.ProgressData], None],
        profile_changed_signal: Qc.Signal,
        abort_signal: Qc.Signal,
    ):
        """
        Check if the image is already open, in which case show it.
        Otherwise create a new tab.

        :param image_obj: Image object to open.
        :param config: The config object.
        :param shared_ocr_model: The shared OCR model.
        :param thread_queue: The thread queue for processing steps.
        :param progress_callback: The callback to call when a step is done.
        :param profile_changed_signal: The signal that is broadcast when the profile is changed.
        :param abort_signal: The signal that is broadcast when the user aborts the process.
        """
        if image_obj.path in self.open_images:
            self.setCurrentWidget(self.open_images[image_obj.path][1])
            return

        # Create the tab.
        tab = idd.ImageDetailsWidget(
            parent=self,
            image_obj=image_obj,
            config=config,
            shared_ocr_model=shared_ocr_model,
            thread_queue=thread_queue,
            progress_callback=progress_callback,
            profile_changed_signal=profile_changed_signal,
            abort_signal=abort_signal,
        )
        self.addTab(tab, image_obj.path.name)
        self.open_images[image_obj.path] = (image_obj, tab)
        self.setCurrentWidget(tab)

    @Slot(int)
    def tab_close(self, index: int) -> None:
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

    def clear_files(self) -> None:
        """
        Clear all files from the table, removing all tabs except the primary tab.
        """
        self.open_images.clear()
        for i in range(self.count() - 1, 0, -1):
            self.removeTab(i)

    def remove_file(self, path: Path) -> None:
        """
        Remove the file from the table, removing the tab if it exists.

        :param path: The path of the file to remove.
        """
        if path in self.open_images:
            logger.info(f"Removing file {path} from the table.")
            index = self.indexOf(self.open_images[path][1])
            self.open_images.pop(path)
            self.removeTab(index)

    @Slot(ost.Step)
    def update_tabs(self, step: ost.Step = None) -> None:
        """
        Update the thumbnails in the currently active image details tab, if any.

        :param step: The step to update the thumbnails for.
        """
        current_tab = self.currentWidget()
        if isinstance(current_tab, idd.ImageDetailsWidget):
            current_tab.load_image_thumbnails(step)
