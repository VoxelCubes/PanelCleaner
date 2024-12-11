from collections import defaultdict
import uuid
from enum import IntEnum, auto
from pathlib import Path
from typing import Sequence

import PySide6.QtCore as Qc
import PySide6.QtGui as Qg
import PySide6.QtWidgets as Qw
from PySide6.QtCore import Slot
from loguru import logger
from natsort import natsorted

import pcleaner.config as cfg
import pcleaner.ctd_interface as ctd
import pcleaner.gui.gui_utils as gu
import pcleaner.gui.image_file as imf
import pcleaner.output_structures as ost
import pcleaner.image_ops as ops
import pcleaner.gui.structures as gst
import pcleaner.gui.worker_thread as wt
import pcleaner.helpers as hp
import pcleaner.structures as st
from .CustomQ.CTableWidget import CTableWidget
import pcleaner.ocr.ocr as ocr


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
    shared_ocr_model: gst.Shared[ocr.OCREngineFactory]  # Must be handed over by the mainwindow.
    thread_queue: Qc.QThreadPool  # Must be handed over by the mainwindow.

    # Prevent interactions that delete files. This preserves the integrity of review mode.
    locked: bool

    table_is_empty = Qc.Signal()
    table_not_empty = Qc.Signal()

    table_has_selection = Qc.Signal()
    table_has_no_selection = Qc.Signal()

    remove_file = Qc.Signal(Path)
    remove_all_files = Qc.Signal()

    files: dict[Path, imf.ImageFile]
    split_files: dict[Path, list[imf.ImageFile]]

    notify_on_duplicate: bool

    requesting_image_preview = Qc.Signal(imf.ImageFile)

    step_icons_dark: dict[ost.ImageAnalyticCategory, Qg.QIcon]
    step_icons_light: dict[ost.ImageAnalyticCategory, Qg.QIcon]
    shared_theme_is_dark: gst.Shared[bool]

    last_header_widths: list[int]

    def __init__(self, parent=None) -> None:
        CTableWidget.__init__(self, parent)

        # Store a map of resolved file paths to file objects.
        self.files: dict[Path, imf.ImageFile] = {}
        self.split_files: dict[Path, list[imf.ImageFile]] = {}
        self.threadpool = Qc.QThreadPool.globalInstance()

        self.notify_on_duplicate = True

        self.locked = False

        # Make icons larger so the thumbnails are more visible.
        self.setIconSize(Qc.QSize(imf.THUMBNAIL_SIZE, imf.THUMBNAIL_SIZE))
        self.verticalHeader().setDefaultSectionSize(imf.THUMBNAIL_SIZE + GUI_PADDING)

        self.itemClicked.connect(self.on_click)
        self.finished_drop.connect(self.repopulate_table)

        # Upon style change events, we need to remember the last known good header widths, otherwise they are reset.
        self.last_header_widths = [self.columnWidth(col) for col in range(self.columnCount())]

        Qc.QTimer.singleShot(0, self.post_init)

        self.selectionModel().selectionChanged.connect(self.check_selected)
        self.check_selected()

        self.setContextMenuPolicy(Qc.Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.show_context_menu)

        # Load the icons once to share them between all image files.
        for dark_or_light in ["dark", "light"]:
            icons = {}
            for icon_name, analytic_category in [
                ("ocr_box_removed.svg", ost.ImageAnalyticCategory.ocr_removed),
                ("mask_failed.svg", ost.ImageAnalyticCategory.mask_failed),
                ("mask_perfect.svg", ost.ImageAnalyticCategory.mask_perfect),
                ("mask_denoised.svg", ost.ImageAnalyticCategory.denoised),
                ("mask_inpainting.svg", ost.ImageAnalyticCategory.inpainted),
            ]:
                icons[analytic_category] = gu.load_custom_icon(icon_name, dark_or_light)

            if dark_or_light == "dark":
                self.step_icons_dark = icons
            else:
                self.step_icons_light = icons

    def post_init(self) -> None:
        # Make enough room for the analytic icons.
        icon_count = len(self.step_icons_dark)
        self.setColumnWidth(
            Column.ANALYTICS, round(icon_count * (imf.THUMBNAIL_SIZE * 0.75) + 2 * GUI_PADDING)
        )
        # make the filename column wider.
        self.setColumnWidth(Column.FILENAME, 220)

        # Add tooltips to column headers.
        self.horizontalHeaderItem(Column.SIZE).setToolTip(
            self.tr("Original size in pixels (width × height)")
        )
        self.horizontalHeaderItem(Column.PROCESSING_SIZE).setToolTip(
            self.tr("Processing size in pixels (width × height), scale factor")
        )

    def changeEvent(self, arg__1: Qc.QEvent) -> None:
        """
        Style change and some other events screw up the header widths, so check if they were
        reset and then restore the last known good header widths.

        :param arg__1: Qt event.
        """

        current_widths = [self.columnWidth(col) for col in range(self.columnCount())]
        # Check if the widths are all 0 or 100.
        if all(w in (0, 100) for w in current_widths) and self.last_header_widths:
            # Restore the last known good header widths.
            logger.debug(f"Restoring last known good header widths: {self.last_header_widths}")
            for col, width in enumerate(self.last_header_widths):
                self.setColumnWidth(col, width)
        else:
            self.last_header_widths = current_widths

        super().changeEvent(arg__1)

    def set_thread_queue(self, thread_queue: Qc.QThreadPool) -> None:
        self.thread_queue = thread_queue

    def check_empty(self) -> None:
        if self.rowCount() == 0:
            self.table_is_empty.emit()
        else:
            self.table_not_empty.emit()

    def check_selected(self) -> None:
        # Must have a selected row and focus.
        if self.currentRow() != -1 and self.hasFocus():
            self.table_has_selection.emit()
        else:
            self.table_has_no_selection.emit()

    def focusInEvent(self, event):
        super().focusInEvent(event)
        self.check_selected()

    def focusOutEvent(self, event):
        super().focusOutEvent(event)
        self.check_selected()

    # Setters passed through from the mainwindow.
    def set_config(self, config: cfg.Config) -> None:
        self.config = config

    def set_shared_ocr_model(self, shared_ocr_model: gst.Shared[ocr.OCREngineFactory]) -> None:
        self.shared_ocr_model = shared_ocr_model

    def set_shared_theme_is_dark(self, shared_theme_is_dark: gst.Shared[bool]) -> None:
        self.shared_theme_is_dark = shared_theme_is_dark

    def get_image_files(self) -> list[imf.ImageFile]:
        """
        Get a list of all the image files in the table.
        """
        return list(self.files.values())

    def get_split_files(self) -> dict[Path, list[imf.ImageFile]]:
        return self.split_files

    def has_no_files(self) -> bool:
        """
        Check if the table is empty.
        """
        return len(self.files) == 0

    def dropEvent(self, event: Qg.QDropEvent) -> None:
        """
        We need to reset the notification flag, since this doesn't count as
        a browse drop.
        """
        self.notify_on_duplicate = True
        super().dropEvent(event)

    def handleDrop(self, path: str | list[str]) -> None:
        logger.debug(f"Dropped {path}")
        try:
            image_paths, rejected_tiffs = hp.discover_all_images(path, cfg.SUPPORTED_IMG_TYPES)
        except (FileNotFoundError, hp.UnsupportedImageType) as e:
            logger.error(f"Failed to discover images: {e}")
            path_str = path if isinstance(path, str) else ", ".join(path)
            gu.show_warning(
                self,
                self.tr("Loading Failed"),
                self.tr("Failed to discover images: {path}").format(path=path_str) + f"\n\n{e}",
            )
            return
        except Exception:
            path_str = path if isinstance(path, str) else ", ".join(path)
            gu.show_exception(
                self,
                self.tr("Loading Failed"),
                self.tr("Failed to load images: {path}").format(path=path_str),
            )
            return

        if rejected_tiffs:
            rejected_tiff_str = "\n".join([str(p) for p in rejected_tiffs])
            hp.show_warning(
                self,
                self.tr("Unsupported TIFF files"),
                self.tr("The following 5-channel TIFF files are not supported: \n")
                + str(rejected_tiff_str),
            )

        for image_path in image_paths:
            self.notify_on_duplicate &= self.add_file(image_path, self.notify_on_duplicate)

    def update_all_rows(self) -> None:
        """
        Called when the profile has changed.
        All we need to do is to go through all the rows and call update on them.
        We don't need to repopulate the table, since the files and their names
        have not changed.
        """
        for row in range(self.rowCount()):
            self.update_row(row, self.files[Path(self.item(row, Column.PATH).text())])

    def add_file(self, path: Path, notify_on_duplicate: bool) -> bool:
        """
        Attempt to add a new image to the table.
        All paths are expected to be resolved, absolute paths that point to existing files with a valid extension.

        :param path: Path to the image file.
        :param notify_on_duplicate: When True, will notify the user when a duplicate shows up.
        :return: Whether to notify the next time a duplicate shows up.
        """
        logger.debug(f'Requesting to add "{path}"')
        # Make sure the file is not already in the table.
        if path in self.files or path in self.split_files:
            logger.warning(f'File "{path}" already in table.')
            if not notify_on_duplicate:
                return False

            dialog = Qw.QMessageBox(self)
            dialog.setWindowTitle(self.tr("Duplicate file"))
            dialog.setText(self.tr('File "{path}" is already in the table.').format(path=path))
            dialog.setStandardButtons(Qw.QMessageBox.Ok)
            dialog.setIcon(Qw.QMessageBox.Warning)
            ok_to_all_button = dialog.addButton(self.tr("Ignore All"), Qw.QMessageBox.ActionRole)

            dialog.exec()
            logger.warning(dialog.clickedButton() is ok_to_all_button)

            return dialog.clickedButton() is not ok_to_all_button

        # Check if the image needs splitting due to excessive length.
        general_profile = self.config.current_profile.general
        splits = ops.calculate_best_splits(
            path,
            general_profile.preferred_split_height,
            general_profile.split_tolerance_margin,
            general_profile.split_long_strips,
            general_profile.long_strip_aspect_ratio,
        )
        if not splits:
            # Nothing to do.
            self.files[path] = imf.ImageFile(path=path)
        else:
            segments = ops.split_image(path, splits)
            # Save these dummy files in the cache.
            cache_dir = self.config.get_cleaner_cache_dir() / f"splits_{uuid.uuid4().hex}"
            cache_dir.mkdir(parents=True, exist_ok=True)
            self.split_files[path] = []
            for index, segment in enumerate(segments, 1):
                segment_name = path.stem + "_" + self.tr("split") + f"_{index}" + path.suffix
                segment_path = cache_dir / segment_name
                segment.save(segment_path)
                fake_path = path.with_name(segment_name)
                self.files[segment_path] = imf.ImageFile(
                    path=segment_path, split_from=path, export_path=fake_path
                )
                self.split_files[path].append(self.files[segment_path])
        return notify_on_duplicate

    def clear_files(self) -> None:
        """
        Delete all files from the table.
        """
        logger.debug(f"Clearing table")
        self.files.clear()
        self.split_files.clear()
        self.clearAll()
        self.check_empty()

    def keyPressEvent(self, event) -> None:
        """
        Allow deleting an item with the delete key.
        :param event: Qt event.
        """
        if event.key() == Qc.Qt.Key_Delete:
            if self.selectedItems():
                self.remove_selected_file()
        else:
            super().keyPressEvent(event)

    def remove_selected_file(self, selected_row: int | None = None) -> None:
        """
        Remove the selected file from the table.

        :param selected_row: If not None, remove the file at this row instead of the selected row.
        """
        logger.debug(f"Removing selected file. Auto-selected row: {selected_row is None}")
        if selected_row is None:
            selected_row = self.currentRow()
            if selected_row == -1:
                logger.warning(f"No row selected")
                return

        path = Path(self.item(selected_row, Column.PATH).text())
        self.remove_file.emit(path)
        # Check if the file was split.
        removed_image_file = self.files[path]
        split_from = removed_image_file.split_from
        if split_from is not None:
            # Remove this part of the split.
            self.split_files[split_from].remove(removed_image_file)
            if not self.split_files[split_from]:
                # Remove the split from the table.
                del self.split_files[split_from]
        del self.files[path]
        self.removeRow(selected_row)
        self.check_empty()
        self.check_selected()

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
        file_paths = [img_file.export_path for img_file in self.files.values()]
        shortened_paths = hp.trim_prefix_from_paths(file_paths)
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
                if analytic == ost.ImageAnalyticCategory.ocr_removed:
                    tooltip = self.tr("Number of boxes removed by the OCR model / total boxes")
                elif analytic == ost.ImageAnalyticCategory.mask_failed:
                    tooltip = self.tr(
                        "Number of boxes that failed to generate a mask / total boxes"
                    )
                elif analytic == ost.ImageAnalyticCategory.mask_perfect:
                    tooltip = self.tr("Number of boxes that were perfectly masked / total boxes")
                elif analytic == ost.ImageAnalyticCategory.denoised:
                    tooltip = self.tr("Number of boxes that were denoised / total boxes")
                elif analytic == ost.ImageAnalyticCategory.inpainted:
                    tooltip = self.tr("Number of boxes that were inpainted")
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

    def on_click(self, item: Qw.QTableWidgetItem) -> None:
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
                gu.show_info(
                    self,
                    self.tr("Image not loaded"),
                    self.tr("Please wait until the image has loaded."),
                )
                return
            self.requesting_image_preview.emit(file_obj)
        except KeyError:
            logger.warning(f"Could not find file object for item at row {item.row()}")
            return

    def show_context_menu(self, position):
        # Get the item at the clicked position
        item = self.itemAt(position)
        if not item:
            return  # No item at this position

        context_menu = Qw.QMenu(self)

        # Add "Open" action
        open_action = Qg.QAction(
            Qg.QIcon.fromTheme("view-list-details"), self.tr("Open individual cleaning"), self
        )
        context_menu.addAction(open_action)
        open_action.triggered.connect(lambda: self.on_click(item))

        # Add "Delete" action
        item = self.itemAt(position)
        if item:
            # Figure out the row.
            row = item.row()
            delete_action = Qg.QAction(
                Qg.QIcon.fromTheme("edit-delete-remove"), self.tr("Remove from list"), self
            )
            context_menu.addAction(delete_action)
            delete_action.setEnabled(not self.locked)
            delete_action.triggered.connect(lambda: self.remove_selected_file(row))

        # Add "Delete All" action
        delete_all_action = Qg.QAction(
            Qg.QIcon.fromTheme("edit-clear-history"), self.tr("Remove all files from list"), self
        )
        context_menu.addAction(delete_all_action)
        delete_all_action.setEnabled(not self.locked)
        delete_all_action.triggered.connect(self.remove_all_files)

        # Show the context menu at the cursor position
        context_menu.exec(self.viewport().mapToGlobal(position))

    def show_ocr_mini_analytics(self, ocr_analytics: Sequence[st.OCRAnalytic]) -> None:
        """
        Update the image files with the mini analytics data.

        :param ocr_analytics: The analytics to show.
        """
        # Create a default dict to store path -> (num_boxes_removed, total_boxes)
        analytics_dict: dict[Path, Sequence[int, int]] = defaultdict(lambda: [0, 0])

        for analytic in ocr_analytics:
            # Update the number of boxes removed for this path.
            analytics_dict[analytic.path][0] = len(analytic.removed_box_data)

            # Update the total number of boxes for this path.
            analytics_dict[analytic.path][1] = analytic.num_boxes

        # Update the image files with the analytics data.
        for path, (num_removed, total) in analytics_dict.items():
            img_file = self.files[path]
            img_file.analytics_data.set_category(
                ost.ImageAnalyticCategory.ocr_removed, num_removed, total
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
                ost.ImageAnalyticCategory.mask_failed, num_failed, total
            )
            img_file.analytics_data.set_category(
                ost.ImageAnalyticCategory.mask_perfect, num_perfect, total
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
                ost.ImageAnalyticCategory.denoised, denoised, total
            )

        self.update_all_rows()

    def show_inpaint_mini_analytics(
        self, inpaint_analytics: Sequence[st.InpaintingAnalytic]
    ) -> None:
        """
        Update the image files with the mini analytics data.

        :param inpaint_analytics: The analytics to show.
        """
        for analytic in inpaint_analytics:
            path = analytic.path
            self.files[path].analytics_data.set_category(
                ost.ImageAnalyticCategory.inpainted, len(analytic.thicknesses), None
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
        gu.show_exception(
            self,
            self.tr("Failed to load image"),
            self.tr("Failed to load image {file_path}.").format(file_path=file_path),
            error,
        )

    def image_dispatch_worker_error(self, error: wt.WorkerError) -> None:
        """
        Display an error message in the table.
        """
        gu.show_exception(
            self, self.tr("Dispatch Failed"), self.tr("Failed to dispatch image."), error
        )

    # =========================== File Adding ===========================

    def browse_add_files(self) -> None:
        """
        Browse for one or more files to add to the table.
        """
        file_dialog = Qw.QFileDialog(self, self.tr("Select files"))
        file_dialog.setNameFilter(self.tr("Images") + f" (*{' *'.join(cfg.SUPPORTED_IMG_TYPES)})")

        # To select multiple files, you can use QFileDialog.getOpenFileNames().
        # To also include directories in the selection, we set the option QFileDialog.ShowDirsOnly to False.
        file_dialog.setOption(Qw.QFileDialog.ShowDirsOnly, False)
        file_dialog.setFileMode(Qw.QFileDialog.ExistingFiles)

        self.notify_on_duplicate = True

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
        folder = Qw.QFileDialog.getExistingDirectory(self, self.tr("Select directory"))

        self.notify_on_duplicate = True

        if folder:
            self.handleDrop(folder)

        self.repopulate_table()
