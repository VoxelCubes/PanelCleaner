from enum import IntEnum, auto
from pathlib import Path

import PySide6.QtCore as Qc
import PySide6.QtWidgets as Qw
from logzero import logger
from natsort import natsorted

import pcleaner.config as cfg
import pcleaner.gui.gui_utils as gu
import pcleaner.gui.image_file as imf
import pcleaner.gui.structures as st
import pcleaner.gui.worker_thread as wt
import pcleaner.helpers as hp
from .CustomQ.CTableWidget import CTableWidget


# The size used for the little thumbnails on each row.
ICON_SIZE = 44


class Column(IntEnum):
    PATH = 0
    FILENAME = auto()
    SIZE = auto()
    CHARS = auto()
    OUTPUT = auto()


# noinspection PyUnresolvedReferences
class FileTable(CTableWidget):
    """
    Extends the functionality with custom helpers
    """

    config: cfg.Config  # Reference to the MainWindow's config.
    shared_ocr_model: st.Shared[st.OCRModel]  # Must be handed over by the mainwindow.

    table_is_empty = Qc.Signal()
    table_not_empty = Qc.Signal()

    files: dict[Path, imf.ImageFile]

    requesting_image_preview = Qc.Signal(imf.ImageFile)

    def __init__(self, parent=None):
        CTableWidget.__init__(self, parent)

        # Store a map of resolved file paths to file objects.
        self.files: dict[Path, imf.ImageFile] = {}
        self.threadpool = Qc.QThreadPool.globalInstance()

        # Make icons larger so the thumbnails are more visible.
        self.setIconSize(Qc.QSize(ICON_SIZE, ICON_SIZE))
        self.verticalHeader().setDefaultSectionSize(ICON_SIZE + 4)

        self.itemDoubleClicked.connect(self.on_double_click)

    def check_empty(self):
        logger.debug(f"Checking if table is empty")
        if self.rowCount() == 0:
            self.table_is_empty.emit()
        else:
            self.table_not_empty.emit()

    def set_config(self, config: cfg.Config):
        self.config = config

    def set_shared_ocr_model(self, shared_ocr_model: st.Shared[st.OCRModel]):
        self.shared_ocr_model = shared_ocr_model

    def get_image_files(self) -> list[imf.ImageFile]:
        """
        Get a list of all the image files in the table.
        """
        return list(self.files.values())

    def handleDrop(self, path: str):
        logger.debug(f"Dropped {path}")
        image_paths, rejected_tiffs = hp.discover_all_images(path, cfg.SUPPORTED_IMG_TYPES)
        logger.info(f"Discovered {len(image_paths)} images")
        if rejected_tiffs:
            rejected_tiff_str = "\n".join([str(p) for p in rejected_tiffs])
            hp.show_warning(
                self,
                "Unsupported TIFF files",
                f"The following 5-channel TIFF files are not supported\n: " f"{rejected_tiff_str}",
            )
        for image_path in image_paths:
            self.add_file(image_path)
        self.repopulate_table()

        # Check for images that haven't loaded their data yet.
        # They will need to have a worker thread scheduled, so the gui doesn't freeze.
        for image in self.files.values():
            if not image.data_loaded():
                # Start the text file worker.
                worker = wt.Worker(self.image_loading_task, image=image, no_progress_callback=True)
                logger.debug(f"Worker Thread loading image {image.path}")

                worker.signals.result.connect(self.image_loading_worker_result)
                worker.signals.error.connect(self.image_loading_worker_error)
                # Execute.
                logger.info(f"Executing worker thread {image.path}")
                self.threadpool.start(worker)

    def add_file(self, path: Path):
        """
        Attempt to add a new image to the table.
        All paths are expected to be resolved, absolute paths that point to existing files with a valid extension.

        :param path: Path to the image file.
        """
        logger.info(f'Requesting to add "{path}"')
        # Make sure the file is not already in the table.
        if path in self.files:
            logger.warning(f'File "{path}" already in table.')
            gu.show_warning(self, "Duplicate file", f'File "{path}" is already in the table.')
            return

        self.files[path] = imf.ImageFile(path=path)

    def repopulate_table(self):
        """
        Repopulate the table with the current files.
        """
        self.clearAll()

        # Collect the file paths and map them to their shortened version.
        # Then update the table accordingly.
        shortened_paths = hp.trim_prefix_from_paths(list(self.files.keys()))
        long_and_short_paths: list[tuple[Path, Path]] = list(
            natsorted(zip(self.files.keys(), shortened_paths), key=lambda x: x[1])
        )

        # Fill in the sorted rows.
        for row, (long_path, short_path) in enumerate(long_and_short_paths):
            file_obj: imf.ImageFile = self.files[long_path]

            self.appendRow(str(long_path), str(short_path), "", "", "")

            self.item(row, Column.FILENAME).setToolTip(str(long_path))

            # Check if the image has loaded yet. If not, use a placeholder icon.
            if not file_obj.data_loaded():
                self.item(row, Column.FILENAME).setIcon(file_obj.icon)
            else:
                self.item(row, Column.FILENAME).setIcon(file_obj.thumbnail)
                self.item(row, Column.SIZE).setText(file_obj.size_str)

        self.check_empty()

    def on_double_click(self, item):
        """
        Request to open the image in a new tab to generate previews.

        emits: requesting_image_preview

        :param item: The clicked item.
        """
        # Get the file object.
        try:
            file_obj = self.files[Path(self.item(item.row(), Column.PATH).text())]
            self.requesting_image_preview.emit(file_obj)
        except KeyError:
            logger.warning(f"Could not find file object for item at row {item.row()}")
            return

    # =========================== Worker Tasks ===========================

    @staticmethod
    def image_loading_task(image: imf.ImageFile) -> Path:
        """
        Thin wrapper to ensure the image object will be returned in the event of an error.

        :param image: The image to load.
        :return: The path to the image for callbacks.
        """
        return image.load_image()

    # ========================= Worker Callbacks =========================

    def image_loading_worker_result(self, file_path: Path):
        """
        Update the table with the thumbnail.
        """
        logger.debug(f"Worker thread {file_path} finished.")

        # Search for the file in the table.
        for row in range(self.rowCount()):
            if self.item(row, Column.PATH).text() == str(file_path):
                # Update the table with the thumbnail and image size.
                self.item(row, Column.FILENAME).setIcon(self.files[file_path].thumbnail)
                self.item(row, Column.SIZE).setText(self.files[file_path].size_str)
                break
        else:
            logger.warning(f"Worker done. Could not find {file_path} in the table. ignoring.")

    def image_loading_worker_error(self, error: wt.WorkerError):
        """
        Display an error message in the table.
        """
        # Extract the file object from the WorkerError's *args, being the self argument.
        try:
            file_path = error.kwargs["image"].path
        except (IndexError, AttributeError):
            logger.error(f"Failed to process {error}")
            return
        # Save the error in the file object.
        self.files[file_path].error = error.value
        logger.error(f"Worker thread {file_path} failed with {error.value}")
        gu.show_warning(
            self, "Failed to load image", f"Failed to load image {file_path}:\n\n{error.value}"
        )

    def browse_add_files(self):
        """
        Browse for one or more files to add to the table.
        """
        file_dialog = Qw.QFileDialog(self, "Select files")
        file_dialog.setNameFilter(f"Images (*{' *'.join(cfg.SUPPORTED_IMG_TYPES)})")

        # To select multiple files, you can use QFileDialog.getOpenFileNames().
        # To also include directories in the selection, we set the option QFileDialog.ShowDirsOnly to False.
        file_dialog.setOption(Qw.QFileDialog.ShowDirsOnly, False)
        file_dialog.setFileMode(Qw.QFileDialog.ExistingFiles)

        if file_dialog.exec() == Qw.QFileDialog.Accepted:
            selected_files = file_dialog.selectedFiles()
            print(selected_files)
            for file in selected_files:
                self.handleDrop(file)
            # self.request_text_param_update.emit()

    def browse_add_folders(self):
        """
        Browse for one or more folders to add to the table.
        """
        folder = Qw.QFileDialog.getExistingDirectory(self, "Select directory")
        if folder:
            self.handleDrop(folder)
