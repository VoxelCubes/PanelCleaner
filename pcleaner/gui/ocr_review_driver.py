import math
from enum import IntEnum
from functools import wraps, partial

import PySide6.QtCore as Qc
import PySide6.QtGui as Qg
import PySide6.QtWidgets as Qw
from PIL import Image
from PySide6.QtCore import Slot
from loguru import logger
from natsort import natsorted

import pcleaner.gui.gui_utils as gu
import pcleaner.gui.image_file as imf
import pcleaner.gui.state_saver as ss
import pcleaner.gui.structures as gst
import pcleaner.gui.worker_thread as wt
import pcleaner.ocr.ocr as ocr
import pcleaner.ocr.supported_languages as osl
import pcleaner.output_structures as ost
import pcleaner.structures as st
from pcleaner.gui.ui_generated_files.ui_OcrReview import Ui_OcrReview
from pcleaner.helpers import tr, f_plural


# The maximum size, will be smaller on one side if the image is not square.
THUMBNAIL_SIZE = 180


# The way the cellUpdate signal works, which we need to know when a cell was manually edited,
# is that it also triggers on all other changes too... But we need to ignore those
# due to inconsistent intermediate states causing exception.
def suppress_cell_update_handling(method):
    @wraps(method)
    def wrapper(self, *args, **kwargs):
        self.awaiting_user_input = False
        result = method(self, *args, **kwargs)
        self.awaiting_user_input = True
        return result

    return wrapper


class ViewMode(IntEnum):
    WithBoxes = 0
    Original = 1


BUBBLE_STATUS_COLORS = {
    st.OCRStatus.Normal: Qg.QColor(0, 128, 0, 255),
    st.OCRStatus.Removed: Qg.QColor(128, 0, 0, 255),
    st.OCRStatus.EditedRemoved: Qg.QColor(128, 0, 0, 255),
    st.OCRStatus.Edited: Qg.QColor(0, 0, 128, 255),
    st.OCRStatus.New: Qg.QColor(128, 64, 0, 255),
}


class OcrReviewWindow(Qw.QDialog, Ui_OcrReview):
    """
    A window to display the process results.
    """

    images: list[imf.ImageFile]
    # These are the in the raw analytic format.
    ocr_analytics: list[st.OCRAnalytic]
    # These use the mutable format.
    ocr_results: list[list[st.OCRResult]]
    # When editing old data, we shouldn't try to use the generated box images,
    # as they might not exist or be wrong.
    editing_old_data: bool

    min_thumbnail_size: int
    max_thumbnail_size: int

    first_load: bool

    ocr_engine_factory: gst.Shared[ocr.OCREngineFactory]
    theme_is_dark: gst.Shared[bool]

    # When True, handle changes to cells as user input.
    awaiting_user_input: bool

    state_saver: ss.StateSaver  # The state saver for the window.

    def __init__(
        self,
        parent=None,
        images: list[imf.ImageFile] = None,
        ocr_analytics: list[st.OCRAnalytic] = None,
        editing_old_data: bool = False,
        ocr_engine_factory: gst.Shared[ocr.OCREngineFactory] = None,
        theme_is_dark: gst.Shared[bool] = None,
    ):
        """
        Init the widget.

        :param ocr_engine_factory:
        :param parent: The parent widget.
        :param images: The images to display.
        :param ocr_analytics: The OCR results to display.
        :param editing_old_data: When true, don't attempt to load generated box outputs.
        :param theme_is_dark: The shared theme state.
        """
        logger.info(f"Opening OCR Review Window for {len(images)} outputs.")
        Qw.QDialog.__init__(self, parent)
        self.setupUi(self)

        # Special OutputReview overrides.
        self.target_output = ost.Output.initial_boxes
        self.confirm_closing = True

        self.images = images
        self.ocr_analytics = ocr_analytics
        self.editing_old_data = editing_old_data
        self.ocr_engine_factory = ocr_engine_factory
        self.theme_is_dark = theme_is_dark

        self.sort_images_by_path()

        self.awaiting_user_input = False

        if len(self.images) != len(self.ocr_analytics):
            logger.error("The number of images and OCR results don't match.")

        self.ocr_results = st.convert_ocr_analytics_to_results(self.ocr_analytics)

        self.first_load = True

        # Set the table to only allow editing in the text column.
        self.tableWidget_ocr.setEditableColumns([1])
        self.tableWidget_ocr.setItemDelegate(WrapTextDelegate())
        self.tableWidget_ocr.resized.connect(self.adjust_row_heights)

        self.calculate_thumbnail_size()
        self.init_arrow_buttons()
        self.init_image_list()
        self.image_list.currentItemChanged.connect(self.handle_image_change)
        # Select the first image to start with.
        self.comboBox_view_mode.currentIndexChanged.connect(self.update_image_boxes)
        self.tableWidget_ocr.currentRowChanged.connect(self.update_image_boxes)
        Qc.QTimer.singleShot(0, partial(self.image_list.setCurrentRow, 0))
        # Override Qt's dynamic scroll speed with a fixed, standard value.
        self.image_list.verticalScrollBar().setSingleStep(120)

        # Let the user select the bubble by clicking it too.
        self.image_viewer.bubble_clicked.connect(self.handle_bubble_clicked)

        self.pushButton_done.clicked.connect(self.close)

        # Connect the zoom buttons to the image viewer.
        self.pushButton_zoom_in.clicked.connect(self.image_viewer.zoom_in)
        self.pushButton_zoom_out.clicked.connect(self.image_viewer.zoom_out)
        self.pushButton_zoom_fit.clicked.connect(self.image_viewer.zoom_fit)
        self.pushButton_zoom_reset.clicked.connect(self.image_viewer.zoom_reset)

        # Connect the table buttons.
        self.pushButton_new.toggled.connect(self.new_bubble)
        self.pushButton_delete.clicked.connect(self.delete_bubble)
        self.pushButton_reset.clicked.connect(self.reset_single_bubble)
        self.pushButton_reset_all.clicked.connect(self.reset_all_bubbles)
        self.pushButton_row_up.clicked.connect(self.move_row_up)
        self.pushButton_row_down.clicked.connect(self.move_row_down)
        self.pushButton_undelete.clicked.connect(self.delete_bubble)
        self.tableWidget_ocr.currentRowChanged.connect(self.update_button_availability)
        self.tableWidget_ocr.cellChanged.connect(self.handle_table_edited)

        # Callback for new bubble creation.
        self.image_viewer.new_bubble.connect(self.add_new_bubble)

        # Make side splitter 50/50.
        side_splitter_width = self.splitter_side.width()
        self.splitter_side.setSizes([side_splitter_width // 2, side_splitter_width // 2])

        self.load_custom_icons()
        self.update_button_availability()

        # Set the new button color to match what would be assigned to new buttons.
        self.image_viewer.set_new_bubble_color(BUBBLE_STATUS_COLORS[st.OCRStatus.New])

        self.init_shortcuts()

        self.load_ocr_options()

        self.state_saver = ss.StateSaver("ocr_review")
        self.init_state_saver()
        self.state_saver.restore()

    def init_shortcuts(self) -> None:
        def set_button_shortcut(button: Qw.QPushButton, key_sequence: Qg.QKeySequence) -> None:
            button.setShortcut(key_sequence)
            button.setToolTip(button.toolTip() + f" ({button.shortcut().toString()})")

        set_button_shortcut(self.pushButton_new, Qg.QKeySequence(Qc.Qt.CTRL + Qc.Qt.Key_N))
        set_button_shortcut(self.pushButton_delete, Qg.QKeySequence(Qc.Qt.CTRL + Qc.Qt.Key_D))
        set_button_shortcut(
            self.pushButton_undelete, Qg.QKeySequence(Qc.Qt.CTRL + Qc.Qt.SHIFT + Qc.Qt.Key_D)
        )
        set_button_shortcut(self.pushButton_reset, Qg.QKeySequence(Qc.Qt.CTRL + Qc.Qt.Key_R))
        set_button_shortcut(self.pushButton_prev, Qg.QKeySequence(Qc.Qt.CTRL + Qc.Qt.Key_Left))
        set_button_shortcut(self.pushButton_next, Qg.QKeySequence(Qc.Qt.CTRL + Qc.Qt.Key_Right))
        set_button_shortcut(self.pushButton_row_up, Qg.QKeySequence(Qc.Qt.CTRL + Qc.Qt.Key_Up))
        set_button_shortcut(self.pushButton_row_down, Qg.QKeySequence(Qc.Qt.CTRL + Qc.Qt.Key_Down))

    def get_final_ocr_analytics(self) -> list[st.OCRAnalytic]:
        """
        Convert the mutable OCR results back to the original format.

        :return: The OCR analytics.
        """
        return st.convert_ocr_results_to_analytics(self.ocr_results)

    def load_custom_icons(self) -> None:
        # Load the custom new_bubble icon.
        theme = "dark" if self.theme_is_dark.get() else "light"

        icon_new = gu.load_custom_icon("new_bubble", theme)
        icon_undelete = gu.load_custom_icon("trash_restore", theme)

        # Check if it loaded correctly.
        if icon_new.isNull():
            logger.error("Failed to load icon new_bubble.")
            return
        if icon_undelete.isNull():
            logger.error("Failed to load icon trash_restore.")
            return

        self.pushButton_new.setIcon(icon_new)
        self.pushButton_new.setText("")
        self.pushButton_undelete.setIcon(icon_undelete)
        self.pushButton_undelete.setText("")

    def switch_to_image(self, image: imf.ImageFile) -> None:
        """
        Show the image in the button in the image view.

        :param image: The image to show.
        """
        original_path = image.path

        self.label_file_name.setText(str(original_path))
        self.label_file_name.setToolTip(str(original_path))
        self.label_file_name.setElideMode(Qc.Qt.ElideLeft)

        self.image_viewer.set_image(original_path)

        self.load_ocr_results(self.ocr_results[self.images.index(image)])

        # Select the first row (if any) to allow for easy keyboard navigation.
        if self.tableWidget_ocr.rowCount() > 0:
            self.tableWidget_ocr.setCurrentCell(0, 1)
            self.tableWidget_ocr.focusWidget()

        # Set a delayed zoom to fit.
        if self.first_load:
            Qc.QTimer.singleShot(0, self.image_viewer.zoom_fit)
            self.first_load = False

    @suppress_cell_update_handling
    def load_ocr_results(self, ocr_results: list[st.OCRResult]) -> None:
        """
        Load the OCR results into the text fields.

        :param ocr_results: The OCR results to load for this image.
        """
        self.tableWidget_ocr.clearAll()

        # This index is for the table to keep track of the index into the specific OCR result list.
        # It isn't the original index of the box as shown in the image.
        for index, ocr_result in enumerate(ocr_results):
            self.tableWidget_ocr.appendRow(
                str(ocr_result.label),
                ocr_result.text,
            )
            # If the status is edited, make it italic, removed is strikeout, and
            # editedremoved is both.
            cell_font = self.tableWidget_ocr.item(index, 1).font()
            if ocr_result.status == st.OCRStatus.Edited:
                cell_font.setItalic(True)
            elif ocr_result.status == st.OCRStatus.Removed:
                cell_font.setStrikeOut(True)
            elif ocr_result.status == st.OCRStatus.EditedRemoved:
                cell_font.setItalic(True)
                cell_font.setStrikeOut(True)
            self.tableWidget_ocr.item(index, 1).setFont(cell_font)

        self.update_image_boxes()
        self.adjust_row_heights()

    def adjust_row_heights(self):
        for row in range(self.tableWidget_ocr.rowCount()):
            self.tableWidget_ocr.resizeRowToContents(row)

    def update_image_boxes(self) -> None:
        """
        Update the image viewer with the current OCR results.
        """
        if self.view_mode() == ViewMode.Original or not self.ocr_results:
            self.image_viewer.clear_bubbles()
            return

        ocr_results = self.current_image_ocr_results()

        rects: list[Qc.QRect] = [
            Qc.QRect(*ocr_result.box.as_tuple_xywh) for ocr_result in ocr_results
        ]
        colors: list[Qg.QColor] = [
            BUBBLE_STATUS_COLORS[ocr_result.status] for ocr_result in ocr_results
        ]
        labels: list[str] = [str(ocr_result.label) for ocr_result in ocr_results]
        strokes: list[Qc.Qt.PenStyle] = list(
            map(
                lambda r: (
                    Qc.Qt.SolidLine
                    if r.status not in (st.OCRStatus.Removed, st.OCRStatus.EditedRemoved)
                    else Qc.Qt.DashLine
                ),
                ocr_results,
            )
        )
        # assert self.tableWidget_ocr.rowCount() == len(ocr_results)
        # assert self.tableWidget_ocr.rowCount() == len(rects)
        # assert self.tableWidget_ocr.rowCount() == len(colors)
        # assert self.tableWidget_ocr.rowCount() == len(labels)
        # assert self.tableWidget_ocr.rowCount() == len(strokes)

        # Set the selected bubble to have the highlight color.
        selected_row = self.tableWidget_ocr.currentRow()
        if selected_row != -1:
            colors[selected_row] = self.palette().highlight().color()
        self.image_viewer.set_bubbles(rects, colors, labels, strokes)

    def view_mode(self) -> ViewMode:
        """
        Get the current view mode.

        :return: The current view mode.
        """
        return ViewMode(self.comboBox_view_mode.currentIndex())

    def current_image_ocr_results(self) -> list[st.OCRResult]:
        """
        Get the OCR results for the currently selected image.

        :return: The OCR results.
        """
        return self.ocr_results[self.image_list.currentRow()]

    @Slot(int)
    def handle_bubble_clicked(self, index: int) -> None:
        self.tableWidget_ocr.setCurrentCell(index, 1)

    # OCR Engine stuff =============================================================================

    def load_ocr_options(self) -> None:
        """
        We can either disable auto OCR or choose what language we want it to detect.
        """
        self.comboBox_ocr_language.addTextItemLinkedData(self.tr("No OCR"), None)
        code_and_name = osl.language_code_name_sorted(
            include_detect=False, pin_important=True, translate=tr
        )
        # Filter out the languages we can't use anyway.
        available_lang_codes = ocr.get_all_available_langs()
        for code, lang in filter(lambda x: x[0] in available_lang_codes, code_and_name):
            self.comboBox_ocr_language.addTextItemLinkedData(lang, code)
        # Start at the second item, ie. the first actual language.
        self.comboBox_ocr_language.setCurrentIndex(1)

    def get_ocr_engine(self) -> ocr.OCRModel | None:
        """
        Get the current OCR model to use.

        :return: The OCR model to use, or None if no OCR should be done.
        """
        selected_index = self.comboBox_ocr_language.currentIndex()
        if selected_index == 0:
            return None
        return self.ocr_engine_factory.get()(self.comboBox_ocr_language.currentLinkedData())

    def start_ocr(self, box: st.Box, row: int) -> None:
        """
        Start a worker thread to perform OCR on the given box.
        It's typically fast enough to not be noticeable if it were blocking,
        then again I don't know what kind of potato you're running this on.

        :param box: The box to perform OCR on.
        :param row: The row it was added on.
        """
        current_image_index = self.image_list.currentRow()
        ocr_worker = wt.Worker(
            self.perform_ocr, box, current_image_index, row, no_progress_callback=True
        )
        ocr_worker.signals.error.connect(self.ocr_worker_error)
        ocr_worker.signals.result.connect(self.ocr_worker_result)
        ocr_worker.signals.finished.connect(self.ocr_worker_finished)
        Qc.QThreadPool.globalInstance().start(ocr_worker)

        Qw.QApplication.setOverrideCursor(Qc.Qt.WaitCursor)

    def perform_ocr(self, box: st.Box, image_index: int, row: int) -> tuple[str, int, int]:
        """
        Grab the image file directly and crop that.

        :param box: The box to crop.
        :param image_index: The index of the image this is for.
            Important to know if the user has switched images.
        :param row: The row in the table to update.
        :return: The OCR result.
        """
        model = self.get_ocr_engine()
        original_image = self.image_viewer.image_item.pixmap()
        # Crop the image to the bubble.
        bubble_image = original_image.copy(*box.as_tuple_xywh)
        bubble_pil_image = Image.fromqpixmap(bubble_image)
        return model(bubble_pil_image), image_index, row

    def ocr_worker_error(self, error: wt.WorkerError) -> None:
        logger.error(f"OCR worker thread error: {error}")
        gu.show_exception(self, self.tr("OCR Error"), self.tr("Encountered error:"), error)

    @suppress_cell_update_handling
    def ocr_worker_result(self, result: tuple[str, int, int]) -> None:
        text, image_index, row = result

        ocr_results = self.ocr_results[image_index]
        try:
            ocr_results[row].text = text
        except IndexError:
            logger.error("OCR result index out of range. User likely deleted the bubble.")

        self.load_ocr_results(ocr_results)

        # Focus the newly created bubble, if still on this image.
        if image_index == self.image_list.currentRow():
            self.tableWidget_ocr.setCurrentCell(row, 1)
            self.tableWidget_ocr.focusWidget()

    def ocr_worker_finished(self) -> None:
        # Reset the cursor and enable the window.
        Qw.QApplication.restoreOverrideCursor()

    # Table manipulation functions =================================================================

    def update_button_availability(self) -> None:
        """
        Check which buttons should be enabled.
        """
        selected_row = self.tableWidget_ocr.currentRow()
        self.pushButton_row_up.setEnabled(selected_row > 0)
        self.pushButton_row_down.setEnabled(
            selected_row != -1 and selected_row < self.tableWidget_ocr.rowCount() - 1
        )
        # For resetting a single bubble, both the index needs to
        # be valid and the bubble must be edited.
        if selected_row == -1:
            self.pushButton_reset.setEnabled(False)
        else:
            ocr_results = self.current_image_ocr_results()
            self.pushButton_reset.setEnabled(
                ocr_results[selected_row].status
                in (st.OCRStatus.Edited, st.OCRStatus.EditedRemoved, st.OCRStatus.Removed)
            )
        # For delete there must be a selection and it can't be deleted already.
        self.pushButton_undelete.hide()
        if selected_row == -1:
            self.pushButton_delete.setEnabled(False)
            self.pushButton_delete.show()
            self.pushButton_undelete.hide()
        else:
            ocr_results = self.current_image_ocr_results()
            self.pushButton_delete.setEnabled(True)
            if ocr_results[selected_row].status in (
                st.OCRStatus.Removed,
                st.OCRStatus.EditedRemoved,
            ):
                self.pushButton_delete.hide()
                self.pushButton_undelete.show()
            else:
                self.pushButton_delete.show()
                self.pushButton_undelete.hide()

    @suppress_cell_update_handling
    def delete_bubble(self) -> None:
        """
        Remove the currently selected bubble.
        If it was a new bubble, remove it entirely.
        Otherwise, mark it as removed.
        But if already removed, undelete it.
        """
        selected_row = self.tableWidget_ocr.currentRow()
        if selected_row == -1:
            return

        ocr_results = self.current_image_ocr_results()
        ocr_result = ocr_results[selected_row]

        if ocr_result.status == st.OCRStatus.New:
            ocr_results.pop(selected_row)
        elif ocr_result.status == st.OCRStatus.Removed:
            ocr_result.status = st.OCRStatus.Normal
        elif ocr_result.status == st.OCRStatus.EditedRemoved:
            ocr_result.status = st.OCRStatus.Edited
        elif ocr_result.status == st.OCRStatus.Edited:
            ocr_result.status = st.OCRStatus.EditedRemoved
        else:
            ocr_result.status = st.OCRStatus.Removed

        self.load_ocr_results(ocr_results)

    @suppress_cell_update_handling
    def reset_single_bubble(self) -> None:
        """
        Reset only the currently selected bubble.
        Go by the original label to find the correct bubble.
        """
        selected_row = self.tableWidget_ocr.currentRow()
        if selected_row == -1:
            return
        # Check that this is an edited bubble.
        ocr_results = self.current_image_ocr_results()
        if ocr_results[selected_row].status not in (
            st.OCRStatus.Edited,
            st.OCRStatus.EditedRemoved,
            st.OCRStatus.Removed,
        ):
            logger.error("Tried to reset a non-edited bubble.")
            return

        image_index = self.image_list.currentRow()
        original_analytic = self.ocr_analytics[image_index]
        # Wrap it in a list due to the way the helper is written, then unpack the result.
        original_results = st.convert_ocr_analytics_to_results([original_analytic])[0]

        ocr_results = self.ocr_results[image_index]
        # Figure out what the original row was by matching the label.
        original_row = next(
            i
            for i, ocr_result in enumerate(original_results)
            if ocr_result.label == ocr_results[selected_row].label
        )
        ocr_results[selected_row] = original_results[original_row]

        self.load_ocr_results(ocr_results)

    @suppress_cell_update_handling
    def reset_all_bubbles(self) -> None:
        """
        Reset all bubbles to their original state.
        """
        # Confirm first.
        if (
            gu.show_question(
                self,
                self.tr("Reset Bubbles"),
                self.tr("Are you sure you want to reset all boxes for this image?"),
            )
            == Qw.QMessageBox.Cancel
        ):
            return
        # Pull the original OCR results from the analytics.
        image_index = self.image_list.currentRow()
        original_analytic = self.ocr_analytics[image_index]
        # Wrap it in a list due to the way the helper is written, then unpack the result.
        original_results = st.convert_ocr_analytics_to_results([original_analytic])[0]

        self.ocr_results[image_index] = original_results
        self.load_ocr_results(original_results)

    @suppress_cell_update_handling
    def move_row_up(self) -> None:
        """
        Move the currently selected row up.
        """
        selected_row = self.tableWidget_ocr.currentRow()
        if selected_row == -1 or selected_row == 0:
            return

        ocr_results = self.current_image_ocr_results()
        ocr_results.insert(selected_row - 1, ocr_results.pop(selected_row))

        self.load_ocr_results(ocr_results)
        self.tableWidget_ocr.setCurrentCell(selected_row - 1, 1)

    @suppress_cell_update_handling
    def move_row_down(self) -> None:
        """
        Move the currently selected row down.
        """
        selected_row = self.tableWidget_ocr.currentRow()
        if selected_row == -1 or selected_row == self.tableWidget_ocr.rowCount() - 1:
            return

        ocr_results = self.current_image_ocr_results()
        ocr_results.insert(selected_row + 1, ocr_results.pop(selected_row))

        self.load_ocr_results(ocr_results)
        self.tableWidget_ocr.setCurrentCell(selected_row + 1, 1)

    def new_bubble(self) -> None:
        """
        Switch the image viewer to bubble mode.
        The actual bubble creation is done once the callback comes in on
        BubbleImageViewer.new_bubble.
        """
        self.image_viewer.set_allow_drawing_bubble(self.pushButton_new.isChecked())

    @suppress_cell_update_handling
    def add_new_bubble(self, rect: Qc.QRect) -> None:
        # Disable new bubble mode.
        self.pushButton_new.setChecked(False)
        self.new_bubble()

        # Create regular xyxy coordinates for a box.
        box = st.Box(*rect.getCoords())

        # Discard if the bubble is too small.
        MIN_BUBBLE_SIZE = 400
        if box.area < MIN_BUBBLE_SIZE:
            logger.debug("Discarding bubble due to size.")
            return

        # Find the lowest free bubble index.
        first_free_index = 1
        used_indices = [
            int(ocr_result.label.split()[-1])
            for ocr_result in self.current_image_ocr_results()
            if ocr_result.status == st.OCRStatus.New
        ]
        while first_free_index in used_indices:
            first_free_index += 1

        new_bubble_label = self.tr("New") + f" {first_free_index}"

        # Add the new bubble to the current image.
        ocr_results = self.current_image_ocr_results()
        image_path = self.image_viewer.loaded_image_path
        # Insert it after the currently selected box, if any, otherwise at the end.
        selected_row = self.tableWidget_ocr.currentRow()
        if selected_row == -1:
            new_row = self.tableWidget_ocr.rowCount()
            ocr_results.append(
                st.OCRResult(image_path, "", box, new_bubble_label, st.OCRStatus.New)
            )
        else:
            new_row = selected_row + 1
            ocr_results.insert(
                new_row,
                st.OCRResult(image_path, "", box, new_bubble_label, st.OCRStatus.New),
            )

        self.load_ocr_results(ocr_results)

        if self.get_ocr_engine() is not None:
            # Quick sanity check. We might not want to OCR more than 20% of the image.
            # This is a rough estimate, but it should be good enough.
            image_area = (
                self.image_viewer.image_dimensions[0] * self.image_viewer.image_dimensions[1]
            )
            bubble_area = box.area
            if bubble_area > 0.2 * image_area:
                if (
                    gu.show_question(
                        self,
                        self.tr("OCR Warning"),
                        self.tr("The bubble is very large. Are you sure you want to OCR it?"),
                    )
                    == Qw.QMessageBox.Cancel
                ):
                    return
            self.start_ocr(box, new_row)
        else:
            # Focus the newly created bubble.
            self.tableWidget_ocr.setCurrentCell(new_row, 1)
            self.tableWidget_ocr.focusWidget()

    @Slot(int, int)
    def handle_table_edited(self, row: int, col: int) -> None:
        """
        Store the edited text in the OCR results.

        :param row: The row of the edited cell.
        :param col: The column of the edited cell, must be 1, the label may not be changed.
        """
        if not self.awaiting_user_input:
            return

        if col != 1:
            logger.error("Only the text column should be editable.")
            return

        ocr_results = self.current_image_ocr_results()
        ocr_results[row].text = self.tableWidget_ocr.currentText(1)
        # If the cell was normal, mark it as edited.
        if ocr_results[row].status == st.OCRStatus.Normal:
            ocr_results[row].status = st.OCRStatus.Edited
        if ocr_results[row].status == st.OCRStatus.Removed:
            ocr_results[row].status = st.OCRStatus.EditedRemoved

        current_row = self.tableWidget_ocr.currentRow()
        self.load_ocr_results(ocr_results)
        self.tableWidget_ocr.selectRow(current_row)

    # Copied shit from OutputReview ================================================================

    def sort_images_by_path(self) -> None:
        """
        Sort the images by their file path using natsort.
        This is necessary because the parallel batch processing will not preserve the order when
        many pictures are processed at once.
        """
        # self.images = natsorted(self.images, key=lambda x: x.path)
        combined = list(zip(self.images, self.ocr_analytics))
        sorted_combined = natsorted(combined, key=lambda x: x[0].path)
        images, ocr_analytics = zip(*sorted_combined)
        self.images = list(images)
        self.ocr_analytics = list(ocr_analytics)

    def closeEvent(self, event: Qg.QCloseEvent) -> None:
        if self.confirm_closing:
            if (
                gu.show_question(
                    self,
                    self.tr("Finish Review"),
                    self.tr("Are you sure you want to finish the review?"),
                )
                == Qw.QMessageBox.Cancel
            ):
                event.ignore()
                return

        self.state_saver.save()
        event.accept()

    def calculate_thumbnail_size(self) -> None:
        """
        Use the current monitor's resolution to calculate the thumbnail size.
        The min value is 1% of the screen width, the max value is 100%.
        """
        screen = Qw.QApplication.primaryScreen()
        screen_size = screen.size()
        screen_width = screen_size.width()
        self.min_thumbnail_size = int(screen_width * 0.01)
        self.max_thumbnail_size = screen_width

    def to_log_scale(self, value: int) -> int:
        """
        Convert a linear value to a logarithmic scale.
        """
        min_log = math.log(self.min_thumbnail_size)
        max_log = math.log(self.max_thumbnail_size)
        scale = (max_log - min_log) / (
            self.horizontalSlider_icon_size.maximum() - self.horizontalSlider_icon_size.minimum()
        )
        log_value = min_log + (value - self.horizontalSlider_icon_size.minimum()) * scale
        return int(math.exp(log_value))

    def from_log_scale(self, value: int) -> int:
        """
        Convert a logarithmic value to a linear scale.
        """
        min_log = math.log(self.min_thumbnail_size)
        max_log = math.log(self.max_thumbnail_size)
        scale = (max_log - min_log) / (
            self.horizontalSlider_icon_size.maximum() - self.horizontalSlider_icon_size.minimum()
        )
        linear_value = (
            math.log(value) - min_log
        ) / scale + self.horizontalSlider_icon_size.minimum()
        return int(linear_value)

    def init_image_list(self) -> None:
        """
        Populate the image list with the images.
        """
        # Reduce the size of the list. Make it a 1/3 split.
        window_width = self.width()
        self.splitter.setSizes([window_width // 3, 2 * window_width // 3])

        label_text = f_plural(len(self.images), self.tr("image"), self.tr("images"))
        self.label_image_count.setText(f"{len(self.images)} {label_text}")

        for image in self.images:

            original_path = image.path
            if self.editing_old_data:
                output_path = original_path
            else:
                output_path = image.outputs[self.target_output].path

            if output_path is None:
                logger.error(f"Output path for {image.path} is None.")

            try:
                self.image_list.addItem(
                    Qw.QListWidgetItem(Qg.QIcon(str(output_path)), str(original_path.stem))
                )
            except OSError:
                gu.show_exception(
                    self,
                    self.tr("Loading Error"),
                    self.tr("Failed to load image '{path}'").format(path=output_path),
                )

        # Use a logarithmic scale to distribute the values.
        self.horizontalSlider_icon_size.valueChanged.connect(self.update_icon_size)
        self.horizontalSlider_icon_size.setValue(self.from_log_scale(THUMBNAIL_SIZE))

        # Sanity check.
        if len(self.images) != self.image_list.count():
            logger.error("Failed to populate the image list correctly.")

    def init_arrow_buttons(self) -> None:
        """
        Connect the arrow buttons to the image list.
        """
        self.pushButton_next.clicked.connect(
            lambda: self.image_list.setCurrentRow(self.image_list.currentRow() + 1)
        )
        self.pushButton_prev.clicked.connect(
            lambda: self.image_list.setCurrentRow(self.image_list.currentRow() - 1)
        )

        # Disable the buttons if there is no next or previous image.
        self.image_list.currentRowChanged.connect(self.check_arrow_buttons)

    def check_arrow_buttons(self) -> None:
        """
        Check if the arrow buttons should be enabled or disabled.
        """
        current_row = self.image_list.currentRow()
        self.pushButton_prev.setEnabled(current_row > 0)
        self.pushButton_next.setEnabled(current_row < self.image_list.count() - 1)

    @Slot(int)
    def update_icon_size(self, size: int) -> None:
        """
        Update the icon size in the image list.

        :param size: The new size.
        """
        size = self.to_log_scale(size)
        self.image_list.setIconSize(Qc.QSize(size, size))
        for index, image in enumerate(self.images):
            item = self.image_list.item(index)
            text = image.path.name
            self.elide_text(item, text, int(size * 0.9))

    def elide_text(self, item, text, width):
        font_metrics = Qg.QFontMetrics(self.font())
        elided_text = font_metrics.elidedText(text, Qc.Qt.ElideLeft, width)
        item.setText(elided_text)

    @Slot(Qw.QListWidgetItem, Qw.QListWidgetItem)
    @Slot(Qw.QListWidgetItem)
    def handle_image_change(
        self, current: Qw.QListWidgetItem = None, previous: Qw.QListWidgetItem = None
    ) -> None:
        """
        Figure out what the new image is and display it.
        """
        # We don't need the previous image, so we ignore it.
        index = self.image_list.currentRow()
        image = self.images[index]
        self.switch_to_image(image)

    def init_state_saver(self) -> None:
        """
        Load the state from the state saver.
        """
        self.state_saver.register(
            self,
            self.splitter,
            self.horizontalSlider_icon_size,
        )


class WrapTextDelegate(Qw.QStyledItemDelegate):
    """
    Let table widget rows expand vertically to prevent line wrapping.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self._table_widget = parent

    def paint(self, painter, option, index):
        # Set text wrapping for the cell
        option.textElideMode = Qc.Qt.ElideNone
        option.displayAlignment = Qc.Qt.AlignLeft | Qc.Qt.AlignVCenter
        option.widget.setWordWrap(True)
        super().paint(painter, option, index)

    def sizeHint(self, option, index):
        # Get the text from the index
        text = index.data(Qc.Qt.DisplayRole)
        if not text:
            return super().sizeHint(option, index)

        # Create a Qg.QFontMetrics object to calculate the size of the text
        font_metrics = Qg.QFontMetrics(option.font)

        # Calculate the width available for the text
        text_width = option.rect.width()

        # Calculate the height needed for the text to wrap within the given width
        text_height = font_metrics.boundingRect(
            0, 0, text_width, 0, Qc.Qt.TextWordWrap, text
        ).height()

        # Add an extra half line height.
        text_height += font_metrics.height()

        # Calculate the default size and add text height if necessary
        size = super().sizeHint(option, index)
        return Qc.QSize(size.width(), max(size.height(), text_height))
