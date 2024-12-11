from enum import IntEnum
from pathlib import Path

import PySide6.QtCore as Qc
import PySide6.QtGui as Qg
import PySide6.QtWidgets as Qw
from loguru import logger
from natsort import natsorted

import pcleaner.gui.gui_utils as gu
import pcleaner.gui.image_file as imf
import pcleaner.gui.worker_thread as wt
import pcleaner.helpers as hp
import pcleaner.structures as st
from pcleaner.gui.file_table import GUI_PADDING
from pcleaner.gui.ui_generated_files.ui_ImageMatchOverview import Ui_ImageMatchOverview
from pcleaner.helpers import f_plural


class Column(IntEnum):
    IMAGE_INDEX = 0
    SHORT_IMAGE_PATH = 1
    ANALYTICS_PATH = 2


class ImageMatchOverview(Qw.QDialog, Ui_ImageMatchOverview):
    """
    A window to let the user fix a broken image to ocr analytic mapping.
    This happens when loading an old set of OCR results with a different
    set of images.
    """

    images: list[imf.ImageFile]
    mapping: dict[imf.ImageFile, st.OCRAnalytic]
    unmatched_images: list[imf.ImageFile]
    unmatched_analytics: [st.OCRAnalytic]

    def __init__(
        self,
        parent=None,
        mapping: dict[imf.ImageFile, st.OCRAnalytic] = None,
        unmatched_images: list[imf.ImageFile] = None,
        unmatched_analytics: list[st.OCRAnalytic] = None,
    ):
        """
        Init the widget.

        :param parent: The parent widget.
        :param mapping: The mapping of images to OCR analytics.
        :param unmatched_images: The images that don't have a match.
        :param unmatched_analytics: The OCR analytics that don't have a match.
        """
        logger.info(f"Opening the ImageMatchOverview window.")
        Qw.QDialog.__init__(self, parent)
        self.setupUi(self)

        self.images = list(mapping.keys()) + unmatched_images
        self.images = natsorted(self.images, key=lambda x: x.path)
        self.mapping = mapping
        self.unmatched_images = unmatched_images
        self.unmatched_analytics = natsorted(unmatched_analytics, key=lambda x: x.path)

        self.threadpool = Qc.QThreadPool.globalInstance()

        # Make icons larger so the thumbnails are more visible.
        self.file_table.setIconSize(Qc.QSize(imf.THUMBNAIL_SIZE, imf.THUMBNAIL_SIZE))
        self.file_table.verticalHeader().setDefaultSectionSize(imf.THUMBNAIL_SIZE + GUI_PADDING)

        self.file_table.horizontalHeader().setSectionResizeMode(
            Column.SHORT_IMAGE_PATH, Qw.QHeaderView.Stretch
        )
        self.file_table.horizontalHeader().setSectionResizeMode(
            Column.ANALYTICS_PATH, Qw.QHeaderView.Stretch
        )
        # Hide the index column.
        self.file_table.horizontalHeader().setSectionHidden(Column.IMAGE_INDEX, True)

        self.populate_table()

        self.show_statistics()
        self.init_orphan_warning()

        # Connect the buttons.
        self.pushButton_select_all.clicked.connect(self.select_all)
        self.pushButton_deselect_all.clicked.connect(self.deselect_all)
        self.pushButton_deselect_new.clicked.connect(self.deselect_new)

        self.select_all()
        self.file_table.itemSelectionChanged.connect(self.update_button_states)
        # If there are no images lacking a match, hide the button that removes them.
        if not self.unmatched_images:
            self.pushButton_deselect_new.hide()

        self.buttonBox.button(Qw.QDialogButtonBox.Ok).setText(self.tr("Proceed With Selection"))

    def populate_table(self):

        def make_strikeout_cell(_row: int, _column: int) -> None:
            cell_item = self.file_table.item(_row, _column)
            cell_font = cell_item.font()
            cell_font.setStrikeOut(True)
            cell_item.setFont(cell_font)
            cell_item.setTextAlignment(Qc.Qt.AlignCenter)
            cell_item.setText(" " * 20)

        # First insert the unmatched analytics, since these will be lost.
        for row, analytic in enumerate(self.unmatched_analytics):
            analytic_str = (
                f"{analytic.path} ({len(analytic.removed_box_data)} "
                f"{f_plural(len(analytic.removed_box_data), self.tr('box'), self.tr('boxes'))})"
            )
            self.file_table.appendRow("-1", " " * 20, analytic_str)
            make_strikeout_cell(row, Column.SHORT_IMAGE_PATH)
            # These rows must not be selectable.
            self.file_table.item(row, Column.SHORT_IMAGE_PATH).setFlags(
                self.file_table.item(row, Column.SHORT_IMAGE_PATH).flags() & ~Qc.Qt.ItemIsSelectable
            )
            self.file_table.item(row, Column.ANALYTICS_PATH).setFlags(
                self.file_table.item(row, Column.SHORT_IMAGE_PATH).flags() & ~Qc.Qt.ItemIsSelectable
            )

        # Collect the file paths and map them to their shortened version.
        shortened_paths = hp.trim_prefix_from_paths(list(image.path for image in self.images))

        for row, ((image_index, image_file), short_image_path) in enumerate(
            zip(enumerate(self.images), shortened_paths), start=len(self.unmatched_analytics)
        ):

            analytic_str = ""
            if image_file in self.mapping:
                analytic = self.mapping[image_file]
                analytic_str = (
                    f"{analytic.path} ({len(analytic.removed_box_data)} "
                    f"{f_plural(len(analytic.removed_box_data), self.tr('box'), self.tr('boxes'))})"
                )

            self.file_table.appendRow(f"{image_index}", str(short_image_path), analytic_str)

            if not analytic_str:
                make_strikeout_cell(row, Column.ANALYTICS_PATH)

            self.file_table.item(row, Column.SHORT_IMAGE_PATH).setToolTip(str(image_file.path))

            # Check if the image has loaded yet. If not, use a placeholder icon.
            if not image_file.data_loaded():
                self.file_table.item(row, Column.SHORT_IMAGE_PATH).setIcon(image_file.icon)
            else:
                self.update_row_icon(row, image_file)

        # Begin loading the images in a bit to let the gui update.
        worker = wt.Worker(self.lazy_load_images, no_progress_callback=True)
        worker.signals.error.connect(self.image_dispatch_worker_error)
        self.threadpool.start(worker)

    def update_row_icon(self, row: int, file_obj: imf.ImageFile) -> None:
        """
        Load the image's real thumbnail.

        :param row: The row to update.
        :param file_obj: The file object to use.
        """
        self.file_table.item(row, Column.SHORT_IMAGE_PATH).setIcon(file_obj.thumbnail)

    def show_statistics(self) -> None:
        """
        Compile simple stats and display them above the table.
        """
        plural_images = f_plural(len(self.images), self.tr("image"), self.tr("images"))
        plural_img_unassigned = f_plural(
            len(self.unmatched_images), self.tr("new image"), self.tr("new images")
        )
        stats = self.tr(
            "Matched {num_images} {plural_images} to OCR results. "
            "{num_images_unassigned} {plural_img_unassigned}."
        ).format(
            num_images=len(self.mapping),
            plural_images=plural_images,
            num_images_unassigned=len(self.unmatched_images),
            plural_img_unassigned=plural_img_unassigned,
        )
        self.label_stats.setText(stats)

    def init_orphan_warning(self) -> None:
        """
        If we're dropping analytics, warn the user.
        """
        if not self.unmatched_analytics:
            self.label_warning.hide()
            self.label_warning_icon.hide()
            return

        plural_result = f_plural(
            len(self.unmatched_analytics), self.tr("result"), self.tr("results")
        )
        warning = self.tr(
            "{num_analytics_unassigned} orphaned OCR {plural_result} will be lost."
        ).format(
            num_analytics_unassigned=len(self.unmatched_analytics), plural_result=plural_result
        )
        self.label_warning.setText(warning)

        self.label_warning_icon.setPixmap(Qg.QIcon.fromTheme("dialog-warning").pixmap(16, 16))

    def expand_matched_analytic_paths(self) -> None:
        """
        Expand the paths of the matched analytics to match the full path of the assigned
        image, since the paths from the loaded file are truncated.
        """
        for image, analytic in list(self.mapping.items()):
            analytic_with_expanded_path = st.OCRAnalytic(
                image.path,
                analytic.num_boxes,
                analytic.box_sizes_ocr,
                analytic.box_sizes_removed,
                analytic.removed_box_data,
            )
            self.mapping[image] = analytic_with_expanded_path

    def update_mapping_to_selection(self) -> None:
        """
        When we have finalized a selection, we must provide a blank analytic for each
        new image that didn't have a match.
        Also, unselected images that had a mapping need to be purged.
        """
        selected_indices = self.selected_image_indexes()
        for index, image in enumerate(self.images):
            if index in selected_indices:
                if image in self.mapping:
                    continue
                else:
                    self.mapping[image] = st.OCRAnalytic(image.path, 0, [], [], [])
            else:
                # Remove the mapping.
                self.mapping.pop(image, None)

    def export_final_mapping(self) -> dict[imf.ImageFile, st.OCRAnalytic]:
        """
        Export the final mapping after the user has made their selection.

        :return: The final mapping.
        """
        self.update_mapping_to_selection()
        self.expand_matched_analytic_paths()
        return self.mapping

    def selected_image_indexes(self) -> list[int]:
        """
        Get the indexes of the selected images.

        :return: The indexes of the selected images.
        """
        selected_indexes = []
        for model_index in self.file_table.selectedIndexes():
            if model_index.column() == Column.SHORT_IMAGE_PATH:
                # Read the index from the id column.
                index: int = self.image_index_of_row(model_index.row())
                selected_indexes.append(index)
        return selected_indexes

    def image_index_of_row(self, row: int) -> int | None:
        # Grab the index, but return None if it's -1, since that's the placeholder
        # for analytics without a matching image.
        index = int(self.file_table.item(row, Column.IMAGE_INDEX).text())
        return index if index != -1 else None

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
        for image in self.images:
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
        for row in range(self.file_table.rowCount()):
            index = int(self.file_table.item(row, Column.IMAGE_INDEX).text())
            if index == -1:
                # Skip the unmatched analytics.
                continue
            image_obj = self.images[index]
            if str(image_obj.path) == str(file_path):
                # Update the table with the thumbnail and image size.
                self.update_row_icon(row, image_obj)
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

    # ============================ Button Slots ============================

    def select_all(self) -> None:
        # We need to exclude the unmatched analytics.
        first_image = self.file_table.model().index(
            len(self.unmatched_analytics), Column.IMAGE_INDEX
        )
        last_image = self.file_table.model().index(
            self.file_table.rowCount() - 1, Column.ANALYTICS_PATH
        )
        self.file_table.selectionModel().select(
            Qc.QItemSelection(first_image, last_image), Qc.QItemSelectionModel.Select
        )
        self.update_button_states()

    def deselect_all(self) -> None:
        self.file_table.clearSelection()
        self.update_button_states()

    def deselect_new(self) -> None:
        """
        Deselect all images that don't have a match.
        """
        for row in range(len(self.unmatched_analytics), self.file_table.rowCount()):
            image_index = self.image_index_of_row(row)
            if self.mapping.get(self.images[image_index]):
                continue
            # Unselect this row.
            model_index = self.file_table.model().index(row, Column.SHORT_IMAGE_PATH)
            self.file_table.selectionModel().select(
                model_index, Qc.QItemSelectionModel.Deselect | Qc.QItemSelectionModel.Rows
            )

        self.update_button_states()

    def update_button_states(self) -> None:
        """
        We only get to show one of the select-/deselect-all buttons at a time.
        We can't let the user click OK if there are no images selected.
        """
        selection = self.selected_image_indexes()
        all_selected = len(selection) == len(self.images)
        any_selected = bool(selection)

        self.pushButton_select_all.setVisible(not all_selected)
        self.pushButton_deselect_all.setVisible(all_selected)

        self.buttonBox.button(Qw.QDialogButtonBox.Ok).setEnabled(any_selected)
