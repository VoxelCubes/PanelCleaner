from collections import defaultdict
from enum import IntEnum, auto
from pathlib import Path
from typing import Sequence

import PySide6.QtCore as Qc
import PySide6.QtGui as Qg
import PySide6.QtWidgets as Qw
from PySide6.QtCore import Slot
from logzero import logger
from natsort import natsorted

import pcleaner.config as cfg
import pcleaner.ctd_interface as ctd
import pcleaner.gui.gui_utils as gu
import pcleaner.gui.image_file as imf
import pcleaner.gui.structures as gst
import pcleaner.gui.worker_thread as wt
import pcleaner.helpers as hp
import pcleaner.structures as st
from .CustomQ.CTableWidget import CTableWidget


# Add some space between the icon of each row.
GUI_PADDING = 4


class Column(IntEnum):
    PATH = 0
    FILENAME = auto()
    SIZE = auto()
    PROCESSING_SIZE = auto()
    FILE_SIZE = auto()
    COLOR_MODE = auto()
    ANALYTICS = auto()


# noinspection PyUnresolvedReferences
class FileTable(CTableWidget):
    """
    Extends the functionality with custom helpers
    """

    config: cfg.Config  # Reference to the MainWindow's config.
    shared_ocr_model: gst.Shared[gst.OCRModel]  # Must be handed over by the mainwindow.
    thread_queue: Qc.QThreadPool  # Must be handed over by the mainwindow.

    table_is_empty = Qc.Signal()
    table_not_empty = Qc.Signal()

    files: dict[Path, imf.ImageFile]

    requesting_image_preview = Qc.Signal(imf.ImageFile)

    step_icons_dark: dict[imf.ImageAnalyticCategory, Qg.QIcon]
    step_icons_light: dict[imf.ImageAnalyticCategory, Qg.QIcon]
    shared_theme_is_dark: gst.Shared[bool]

    def __init__(self, parent=None) -> None:
        CTableWidget.__init__(self, parent)

        # Store a map of resolved file paths to file objects.
        self.files: dict[Path, imf.ImageFile] = {}
        self.threadpool = Qc.QThreadPool.globalInstance()

        # Make icons larger so the thumbnails are more visible.
        self.setIconSize(Qc.QSize(imf.THUMBNAIL_SIZE, imf.THUMBNAIL_SIZE))
        self.verticalHeader().setDefaultSectionSize(imf.THUMBNAIL_SIZE + GUI_PADDING)

        self.itemClicked.connect(self.on_click)
        self.finished_drop.connect(self.repopulate_table)

        Qc.QTimer.singleShot(0, self.post_init)

        # Load the icons once to share them between all image files.
        for dark_or_light in ["dark", "light"]:
            icons = {}
            for icon_name, analytic_category in [
                ("ocr_box_removed.svg", imf.ImageAnalyticCategory.ocr_removed),
                ("mask_failed.svg", imf.ImageAnalyticCategory.mask_failed),
                ("mask_perfect.svg", imf.ImageAnalyticCategory.mask_perfect),
                ("mask_denoised.svg", imf.ImageAnalyticCategory.denoised),
            ]:
                icons[analytic_category] = Qg.QIcon(f":/custom_icons/{dark_or_light}/{icon_name}")

            if dark_or_light == "dark":
                self.step_icons_dark = icons
            else:
                self.step_icons_light = icons

    def post_init(self) -> None:
        # Make enough room for the 4 analytic icons.
        self.setColumnWidth(
            Column.ANALYTICS, round(4 * (imf.THUMBNAIL_SIZE * 0.75) + 2 * GUI_PADDING)
        )

        # Add tooltips to column headers.
        self.horizontalHeaderItem(Column.SIZE).setToolTip(
            "Original size in pixels (width × height)"
        )
        self.horizontalHeaderItem(Column.PROCESSING_SIZE).setToolTip(
            "Processing size in pixels (width × height), scale factor"
        )

    def set_thread_queue(self, thread_queue: Qc.QThreadPool) -> None:
        self.thread_queue = thread_queue

    def check_empty(self) -> None:
        if self.rowCount() == 0:
            self.table_is_empty.emit()
        else:
            self.table_not_empty.emit()

    # Setters passed through from the mainwindow.
    def set_config(self, config: cfg.Config) -> None:
        self.config = config

    def set_shared_ocr_model(self, shared_ocr_model: gst.Shared[gst.OCRModel]) -> None:
        self.shared_ocr_model = shared_ocr_model

    def set_shared_theme_is_dark(self, shared_theme_is_dark: gst.Shared[bool]) -> None:
        self.shared_theme_is_dark = shared_theme_is_dark

    def get_image_files(self) -> list[imf.ImageFile]:
        """
        Get a list of all the image files in the table.
        """
        return list(self.files.values())

    def has_no_files(self) -> bool:
        """
        Check if the table is empty.
        """
        return len(self.files) == 0

    def handleDrop(self, path: str) -> None:
        logger.debug(f"Dropped {path}")
        image_paths, rejected_tiffs = hp.discover_all_images(path, cfg.SUPPORTED_IMG_TYPES)
        if rejected_tiffs:
            rejected_tiff_str = "\n".join([str(p) for p in rejected_tiffs])
            hp.show_warning(
                self,
                "Unsupported TIFF files",
                f"The following 5-channel TIFF files are not supported\n: " f"{rejected_tiff_str}",
            )
        for image_path in image_paths:
            self.add_file(image_path)

    def update_all_rows(self) -> None:
        """
        Called when the profile has changed.
        All we need to do is to go through all the rows and call update on them.
        We don't need to repopulate the table, since the files and their names
        have not changed.
        """
        for row in range(self.rowCount()):
            self.update_row(row, self.files[Path(self.item(row, Column.PATH).text())])

    def add_file(self, path: Path) -> None:
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

    def clear_files(self) -> None:
        """
        Delete all files from the table.
        """
        logger.info(f"Clearing table")
        self.files.clear()
        self.clearAll()
        self.check_empty()

    def repopulate_table(self) -> None:
        """
        Repopulate the table with the current files.
        """
        logger.debug(f"Repopulating table")
        # Remember it to scroll back after repopulating.
        v_scroll_pos = self.verticalScrollBar().value()
        h_scroll_pos = self.horizontalScrollBar().value()

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

            self.appendRow(str(long_path), str(short_path), "", "", "", "", "", "")

            self.item(row, Column.FILENAME).setToolTip(str(long_path))
            # Center all columns after the filename.
            for col in range(Column.SIZE, self.columnCount()):
                self.item(row, col).setTextAlignment(Qc.Qt.AlignCenter)

            # Check if the image has loaded yet. If not, use a placeholder icon.
            if not file_obj.data_loaded():
                self.item(row, Column.FILENAME).setIcon(file_obj.icon)
            else:
                self.update_row(row, file_obj)

        self.check_empty()

        # Begin loading the images in a bit to let the gui update.
        worker = wt.Worker(self.lazy_load_images, no_progress_callback=True)
        worker.signals.error.connect(self.image_dispatch_worker_error)
        self.threadpool.start(worker)

        self.verticalScrollBar().setValue(v_scroll_pos)
        self.horizontalScrollBar().setValue(h_scroll_pos)

    def update_row(self, row: int, file_obj: imf.ImageFile) -> None:
        """
        Update the table with the file object's data.

        :param row: The row to update.
        :param file_obj: The file object to use.
        """
        self.item(row, Column.FILENAME).setIcon(file_obj.thumbnail)
        self.item(row, Column.SIZE).setText(file_obj.size_str)
        proc_width, proc_height, proc_scale = ctd.calculate_new_size_and_scale(
            *file_obj.size,
            self.config.current_profile.general.input_height_lower_target,
            self.config.current_profile.general.input_height_upper_target,
        )
        if proc_scale != 1:
            self.item(row, Column.PROCESSING_SIZE).setText(
                f"{proc_width} × {proc_height} ({proc_scale:.0%})"
            )
        else:
            self.item(row, Column.PROCESSING_SIZE).setText(f"100%")
        self.item(row, Column.FILE_SIZE).setText(file_obj.file_size_str)
        self.item(row, Column.COLOR_MODE).setText(file_obj.color_mode_str)

        # Create the analytic icons. They are arranged horizontally in a container widget.
        # The icon ist stacked on top of a label with the "number / total".
        container = Qw.QWidget()
        grid_layout = Qw.QGridLayout(container)
        grid_layout.setContentsMargins(0, 0, 0, 0)
        grid_layout.setSpacing(0)

        icons = self.step_icons_dark if self.shared_theme_is_dark.get() else self.step_icons_light
        grid_col = 0

        for analytic, icon in icons.items():
            # Check if the analytic isn't blank, otherwise just insert a spacer of the same size.
            analytic_value = file_obj.analytics_data.get_category(analytic)
            icon_size = int(imf.THUMBNAIL_SIZE * 0.75)  # Increased size, adjust as necessary

            if not analytic_value:
                empty_label = Qw.QLabel()  # Empty QLabel as spacer
                empty_label.setFixedSize(icon_size, icon_size)
                grid_layout.addWidget(empty_label, 0, grid_col)
            else:
                icon_label = Qw.QLabel()
                icon_label.setPixmap(icon.pixmap(icon_size, icon_size))
                icon_label.setAlignment(Qc.Qt.AlignCenter)
                grid_layout.addWidget(icon_label, 0, grid_col)

                num_label = Qw.QLabel(analytic_value)
                num_label.setAlignment(Qc.Qt.AlignCenter)
                grid_layout.addWidget(num_label, 1, grid_col)

                # Add a helpful tooltip to both the icon and the label.
                if analytic == imf.ImageAnalyticCategory.ocr_removed:
                    tooltip = "Number of boxes removed by the OCR model / total boxes"
                elif analytic == imf.ImageAnalyticCategory.mask_failed:
                    tooltip = "Number of boxes that failed to generate a mask / total boxes"
                elif analytic == imf.ImageAnalyticCategory.mask_perfect:
                    tooltip = "Number of boxes that were perfectly masked / total boxes"
                elif analytic == imf.ImageAnalyticCategory.denoised:
                    tooltip = "Number of boxes that were denoised / total boxes"
                else:
                    raise ValueError(f"Unknown analytic {analytic}")

                icon_label.setToolTip(tooltip)
                num_label.setToolTip(tooltip)

            grid_col += 1  # Move to next column for next icon

        # Set the container as the cell widget
        self.setCellWidget(row, Column.ANALYTICS, container)

    def mousePressEvent(self, event) -> None:
        """
        When clicking in blank space, clear the selection.

        :param event: The mouse event.
        """
        item = self.itemAt(event.pos())
        if item is None:
            self.clearSelection()
        else:
            super().mousePressEvent(event)

    def on_click(self, item) -> None:
        """
        Request to open the image in a new tab to generate previews.

        emits: requesting_image_preview

        :param item: The clicked item.
        """
        # Get the file object.
        try:
            file_obj = self.files[Path(self.item(item.row(), Column.PATH).text())]
            # Check if it has loaded yet.
            if not file_obj.data_loaded():
                logger.debug(f"Image {file_obj.path} has not loaded yet.")
                gu.show_info(self, "Image not loaded", "Please wait until the image has loaded.")
                return
            self.requesting_image_preview.emit(file_obj)
        except KeyError:
            logger.warning(f"Could not find file object for item at row {item.row()}")
            return

    def show_ocr_mini_analytics(self, ocr_analytics: Sequence[st.OCRAnalytic]) -> None:
        """
        Update the image files with the mini analytics data.

        :param ocr_analytics: The analytics to show.
        """
        # Create a default dict to store path -> (num_boxes_removed, total_boxes)
        analytics_dict: dict[Path, Sequence[int, int]] = defaultdict(lambda: [0, 0])

        for analytic in ocr_analytics:
            for removed_data in analytic.removed_box_data:
                path, _, _ = removed_data

                # Update the number of boxes removed for this path.
                analytics_dict[path][0] += 1

                # Update the total number of boxes for this path.
                analytics_dict[path][1] = analytic.num_boxes

        # Update the image files with the analytics data.
        for path, (num_removed, total) in analytics_dict.items():
            img_file = self.files[path]
            img_file.analytics_data.set_category(
                imf.ImageAnalyticCategory.ocr_removed, num_removed, total
            )
        self.update_all_rows()

    def show_masker_mini_analytics(
        self, masker_analytics: Sequence[st.MaskFittingAnalytic]
    ) -> None:
        """
        Update the image files with the mini analytics data.

        :param masker_analytics: The analytics to show.
        """
        # Create a default dict to store image_path -> (no fit found, perfect fit, total boxes)
        analytics_dict: dict[Path, Sequence[int, int, int]] = defaultdict(lambda: [0, 0, 0])

        for analytic in masker_analytics:
            path = analytic.image_path

            # Update the number of boxes where no fit was found.
            if not analytic.fit_was_found:
                analytics_dict[path][0] += 1

            # Update the number of boxes that were perfectly masked.
            if analytic.mask_std_deviation == 0:
                analytics_dict[path][1] += 1

            # Update the total number of boxes for this path.
            analytics_dict[path][2] += 1

        # Update the image files with the analytics data.
        for path, (num_failed, num_perfect, total) in analytics_dict.items():
            img_file = self.files[path]
            img_file.analytics_data.set_category(
                imf.ImageAnalyticCategory.mask_failed, num_failed, total
            )
            img_file.analytics_data.set_category(
                imf.ImageAnalyticCategory.mask_perfect, num_perfect, total
            )

        self.update_all_rows()

    def show_denoise_mini_analytics(
        self, denoise_analytics: Sequence[st.DenoiseAnalytic], min_deviation: float
    ) -> None:
        """
        Update the image files with the mini analytics data.

        :param denoise_analytics: The analytics to show.
        :param min_deviation: The minimum deviation to consider for denoising.
        """
        # Check how many of the deviation values fall below the threshold for a path.
        for analytic in denoise_analytics:
            path = analytic.path

            # Update the total number of boxes for this path.
            total = len(analytic.std_deviations)
            denoised = len([dev for dev in analytic.std_deviations if dev > min_deviation])

            # Update the number of boxes that were denoised directly.
            self.files[path].analytics_data.set_category(
                imf.ImageAnalyticCategory.denoised, denoised, total
            )

        self.update_all_rows()

    @Slot(bool)
    def handle_theme_is_dark_changed(self, is_dark: bool) -> None:
        """
        When the theme changes, we need to update the icons.

        :param is_dark:
        """
        self.update_all_rows()

    # =========================== Worker Tasks ===========================

    @staticmethod
    def image_loading_task(image: imf.ImageFile) -> Path:
        """
        Thin wrapper to ensure the image object will be returned in the event of an error.

        :param image: The image to load.
        :return: The path to the image for callbacks.
        """
        return image.load_image()

    def lazy_load_images(self) -> None:
        logger.info(f"Dispatching image loading workers")
        # Check for images that haven't loaded their data yet.
        # They will need to have a worker thread scheduled, so the gui doesn't freeze.
        for image in self.files.values():
            if not (image.loading_queued or image.data_loaded()):
                image.loading_queued = True
                logger.debug(f"Worker Thread loading image {image.path}")
                worker = wt.Worker(self.image_loading_task, image=image, no_progress_callback=True)
                worker.signals.result.connect(self.image_loading_worker_result)
                worker.signals.error.connect(self.image_loading_worker_error)
                self.threadpool.start(worker)

    # ========================= Worker Callbacks =========================

    def image_loading_worker_result(self, file_path: Path) -> None:
        """
        Update the table with the thumbnail.
        """
        # Search for the file in the table.
        for row in range(self.rowCount()):
            if self.item(row, Column.PATH).text() == str(file_path):
                # Update the table with the thumbnail and image size.
                self.update_row(row, self.files[file_path])
                break
        else:
            logger.warning(f"Worker done. Could not find {file_path} in the table. ignoring.")

    def image_loading_worker_error(self, error: wt.WorkerError) -> None:
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

    def image_dispatch_worker_error(self, error: wt.WorkerError) -> None:
        """
        Display an error message in the table.
        """
        gu.show_warning(
            self, "Failed to dispatch image", f"Failed to dispatch image:\n\n{error.value}"
        )

    # =========================== File Adding ===========================

    def browse_add_files(self) -> None:
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
        self.repopulate_table()

    def browse_add_folders(self) -> None:
        """
        Browse for one or more folders to add to the table.
        """
        folder = Qw.QFileDialog.getExistingDirectory(self, "Select directory")
        if folder:
            self.handleDrop(folder)

        self.repopulate_table()
