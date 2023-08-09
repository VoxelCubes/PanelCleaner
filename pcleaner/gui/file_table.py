from enum import IntEnum, auto
from functools import partial
from pathlib import Path
from uuid import uuid4, UUID

import PySide6.QtCore as Qc
from PySide6.QtCore import Qt
import PySide6.QtGui as Qg
import PySide6.QtWidgets as Qw
from PySide6.QtCore import Slot
from logzero import logger
from natsort import natsorted

import pcleaner.config as cfg
from .CustomQ.CTableWidget import CTableWidget
import pcleaner.gui.image_file as st
import pcleaner.helpers as hp
import pcleaner.gui.gui_utils as gu
import pcleaner.gui.worker_thread as wt

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

    # config: cfg.Config  # Reference to the MainWindow's config.
    # files: dict[str, st.TextFile | st.EpubFile]

    # request_text_param_update = Qc.Signal()
    # ready_for_translation = Qc.Signal()
    # not_ready_for_translation = Qc.Signal()
    # statusbar_message = Qc.Signal(str, int)
    # recalculate_char_total = Qc.Signal()
    table_is_empty = Qc.Signal()
    table_not_empty = Qc.Signal()

    requesting_image_preview = Qc.Signal(st.ImageFile)

    def __init__(self, parent=None):
        CTableWidget.__init__(self, parent)

        # Store a map of resolved file paths to file objects.
        self.files: dict[Path, st.ImageFile] = {}
        self.threadpool = Qc.QThreadPool.globalInstance()
        # self.finished_drop.connect(lambda: self.request_text_param_update.emit())

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

    # def set_config(self, config: cfg.Config):
    #     self.config = config

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

        self.files[path] = st.ImageFile(path=path)

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
            file_obj: st.ImageFile = self.files[long_path]

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
    def image_loading_task(image: st.ImageFile) -> Path:
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

    #     @staticmethod
    #     def initialize_file(path: Path) -> st.TextFile | st.EpubFile:
    #         """
    #         Read and populate the basic information of the file.
    #         Text files (utf8) and epub files are supported.
    #
    #         :param path: The path to the file.
    #         """
    #         logger.debug(f"Initializing file {path}")
    #         if path.suffix.lower() == ".epub":
    #             return st.EpubFile(path=path, cache_dir=cfg.epub_cache_path())
    #         else:
    #             return st.TextFile(path=path)
    #
    #     @Slot()
    #     def update_all_output_filenames(self):
    #         """
    #         Update all output filenames in the table.
    #         The file names need to match the output directory preference and target language.
    #         Don't update locked files.
    #         """
    #         for row in range(self.rowCount()):
    #             file_id = self.item(row, Column.PATH).text()
    #             file = self.files[file_id]
    #             if file.locked:
    #                 continue
    #             new_output_filename = make_output_filename(file, self.config)
    #             self.item(row, Column.OUTPUT).setText(str(new_output_filename))
    #
    #         logger.debug("All output filenames updated.")
    #
    #     """
    #     Text Processing
    #     """
    #
    #     @Slot(st.Glossary)
    #     def update_all_text_params(self, glossary: st.Glossary):
    #         """
    #         Update all text file parameters.
    #         This means processing the glossary and quote protection, if so configured.
    #         Also apply the glossary to epub files.
    #         """
    #         # Abort if no text files.
    #         if self.rowCount() == 0:
    #             return
    #
    #         # Try again in 0.5 seconds if the threadpool is busy.
    #         if self.threadpool.activeThreadCount() > 0:
    #             self.statusbar_message.emit("Waiting for previous threads to finish...", 1000)
    #             Qc.QTimer.singleShot(500, partial(self.update_all_text_params, glossary))
    #             return
    #
    #         self.statusbar_message.emit("Processing...", 5000)
    #
    #         # Show a progress message for all files.
    #         for row in range(self.rowCount()):
    #             # If the file is locked, skip it.
    #             if not self.files[self.item(row, Column.PATH).text()].locked:
    #                 self.item(row, Column.STATUS).setText("Processing...")
    #
    #         logger.debug("Updating all text params")
    #         for row in range(self.rowCount()):
    #             self.update_file_params(row, glossary)
    #
    #     def update_file_params(self, row: int, glossary: st.Glossary):
    #         """
    #         Update the text file parameters for the given row.
    #         This means processing the glossary and quote protection, if so configured.
    #
    #         :param row: The row in the table to update.
    #         :param glossary: The glossary to apply.
    #         """
    #         logger.debug(f"Updating text parameters for {row}")
    #         file_id = self.item(row, Column.PATH).text()
    #         file = self.files[file_id]
    #         file_is_epub = isinstance(file, st.EpubFile)
    #         file_needs_preprocessing = file_is_epub and not file.initialized
    #
    #         # If not processing, check if the label should be updated to say that changes were reverted.
    #         if (
    #             not file_needs_preprocessing
    #             and not (self.config.use_glossary and glossary.is_valid())
    #             and (not self.config.use_quote_protection or file_is_epub)
    #         ):
    #             if file.process_level != st.ProcessLevel.RAW:
    #                 file.process_level = st.ProcessLevel.RAW
    #                 self.item(row, Column.STATUS).setText("Reset to original")
    #                 self.recalculate_char_count(file_id)
    #                 return
    #
    #         if self.config.use_glossary and glossary.is_valid() and glossary.hash != file.glossary_hash:
    #             glossary_to_pass = glossary
    #         else:
    #             glossary_to_pass = None
    #
    #         # Test and set lock.
    #         if file.locked:
    #             logger.warning(f"File {file.path} is locked, access denied.")
    #             return
    #         file.locked = True
    #
    #         # Crunch time begins for the worker. Bless his soul.
    #         # (Move this to another thread because it's CPU intensive.)
    #         if not file_is_epub:
    #             # Start the text file worker.
    #             worker = wt.Worker(
    #                 self.text_process_work,
    #                 file_id=file_id,
    #                 text_file=file,
    #                 glossary=glossary_to_pass,
    #                 apply_glossary=self.config.use_glossary and glossary.is_valid(),
    #                 apply_protection=self.config.use_quote_protection,
    #             )
    #             logger.debug(
    #                 f"Worker Thread processing text file {file.path}: "
    #                 f"Glossary: {glossary_to_pass is not None} | Protection: {self.config.use_quote_protection}"
    #             )
    #         else:
    #             # Start the epub file worker.
    #             worker = wt.Worker(
    #                 self.epub_process_work,
    #                 file_id=file_id,
    #                 epub_file=file,
    #                 glossary=glossary_to_pass,
    #                 apply_glossary=self.config.use_glossary and glossary.is_valid(),
    #             )
    #             logger.debug(
    #                 f"Worker Thread processing epub file {file.path}: "
    #                 f"Glossary: {glossary_to_pass is not None}"
    #             )
    #
    #         worker.signals.result.connect(self.file_process_worker_result)
    #         worker.signals.progress.connect(self.file_process_worker_progress)
    #         worker.signals.error.connect(self.file_process_worker_error)
    #         worker.signals.finished.connect(self.file_process_worker_finished)
    #         # Execute.
    #         logger.info(f"Executing worker thread {file.path}")
    #         self.threadpool.start(worker)
    #
    #     """
    #     Workers
    #     """
    #
    #     @staticmethod
    #     def text_process_work(
    #         file_id: str,
    #         text_file: st.TextFile,
    #         glossary: st.Glossary,
    #         apply_glossary: bool,
    #         apply_protection: bool,
    #         progress_callback: Qc.Signal,
    #     ):
    #         """
    #         Apply the glossary to the given text file.
    #
    #         :param file_id: The ID of the file to process.
    #         :param text_file: The text file to apply the glossary to.
    #         :param glossary: The glossary to apply. None if no glossary is to be applied.
    #         :param apply_glossary: True if the glossary is to be applied.
    #         :param apply_protection: Whether to apply quote protection.
    #         :param progress_callback: A callback to call with the progress of the processing.
    #         """
    #
    #         if apply_glossary:
    #             progress_callback.emit((file_id, "Applying glossary..."))
    #             if (
    #                 glossary is not None
    #             ):  # In this case, the glossary was already applied and still cached.
    #                 text_file.text_glossary = gls.process_text(text_file.text, glossary)
    #                 text_file.glossary_hash = glossary.hash
    #             # Set it either way, so that the file knows it's been processed.
    #             text_file.process_level = st.ProcessLevel.GLOSSARY
    #
    #             if apply_protection:
    #                 progress_callback.emit((file_id, "Applying EQP next..."))
    #                 text_file.text_glossary_protected = qp.protect_text(text_file.text_glossary)
    #                 text_file.process_level = st.ProcessLevel.GLOSSARY_PROTECTED
    #         elif apply_protection:
    #             progress_callback.emit((file_id, "Applying EQP..."))
    #             text_file.text_protected = qp.protect_text(text_file.text)
    #             text_file.process_level = st.ProcessLevel.PROTECTED
    #
    #         progress_callback.emit((file_id, "Ready"))
    #
    #         # Return the file id to update the table.
    #         logger.info(f"Text file {text_file.path} processed.")
    #         return file_id
    #
    #     def epub_process_work(
    #         self,
    #         file_id: str,
    #         epub_file: st.EpubFile,
    #         glossary: st.Glossary,
    #         apply_glossary: bool,
    #         progress_callback: Qc.Signal,
    #     ):
    #         """
    #         Apply the glossary to the given epub file.
    #
    #         :param file_id: The ID of the file to process.
    #         :param epub_file: The epub file to apply the glossary to.
    #         :param glossary: The glossary to apply. None if no glossary is to be applied.
    #         :param apply_glossary: True if the glossary is to be applied.
    #         :param progress_callback: A callback to call with the progress of the processing.
    #         """
    #
    #         # Pre-process the epub file.
    #         progress_callback.emit((file_id, "Loading epub..."))
    #         epub_file.initialize_files(
    #             nuke_ruby=self.config.epub_nuke_ruby,
    #             nuke_kobo=self.config.epub_nuke_kobo,
    #             nuke_indents=self.config.epub_nuke_indents,
    #             crush_html=self.config.epub_crush,
    #             make_text_horizontal=self.config.epub_make_text_horizontal,
    #             ignore_empty=self.config.epub_ignore_empty_html,
    #         )
    #
    #         if apply_glossary:
    #             progress_callback.emit((file_id, "Applying glossary..."))
    #             if (
    #                 glossary is not None
    #             ):  # In this case, the glossary was already applied and still cached.
    #                 gls.process_epub_file(epub_file, glossary)
    #             # Set it either way, so that the file knows it's been processed.
    #             epub_file.process_level = st.ProcessLevel.GLOSSARY
    #
    #         progress_callback.emit((file_id, "Ready"))
    #
    #         # Return the file id to update the table.
    #         logger.info(f"Epub file {epub_file.path} processed.")
    #         return file_id
    #
    #     """
    #     Worker Callbacks
    #     """
    #
    #     def file_process_worker_result(self, file_id: str):
    #         """
    #         Update the table with the result of the glossary processing.
    #         """
    #         logger.debug(f"Worker thread {file_id} finished.")
    #         # Ignore if the file no longer exists.
    #         if file_id not in self.files:
    #             logger.info(f"File {file_id} no longer exists, ignoring result.")
    #             return
    #
    #         self.recalculate_char_count(file_id)
    #         # Try to add the cover as the icon, if this was an epub.
    #         file = self.files[file_id]
    #         if isinstance(file, st.EpubFile) and file.cover_image is not None:
    #             absolute_path = file.cache_dir / file.cover_image
    #             try:
    #                 row = self.findItems(file_id, Qc.Qt.MatchExactly)[0].row()
    #                 self.item(row, Column.FILENAME).setIcon(Qg.QIcon(str(absolute_path)))
    #                 logger.info(f"Set cover image for {file_id} to {absolute_path}")
    #                 file.cover_image = None  # Clear the cover image so it's not loaded again.
    #             except OSError as e:
    #                 logger.error(f"Could not load cover image {absolute_path}")
    #                 logger.exception(e)
    #
    #     def file_process_worker_progress(self, progress: tuple[str, str]):
    #         """
    #         Update the progress bar in the table.
    #         Unwrap the tuple. This is just because worker signals only transmit 1 object.
    #
    #         :param progress: The progress tuple: (file_id, message)
    #         """
    #         file_id, message = progress
    #         # If the file_id no longer exists, ignore.
    #         if file_id not in self.files:
    #             logger.info(f"Worker progress for file {file_id} ignored, as it no longer exists.")
    #             return
    #         self.show_file_progress(file_id, message)
    #
    #     def file_process_worker_error(self, error: wt.WorkerError):
    #         """
    #         Display an error message in the table.
    #         """
    #         # Extract the row from the WorkerError's kwargs.
    #         file_id = error.kwargs["file_id"]
    #         file = self.files[file_id]
    #         logger.error(f"Failed to process {file.path.name}\n{error}")
    #         self.update_table_cell(file_id, Column.STATUS, "Failed to process.")
    #
    #     def file_process_worker_finished(self, initial_args: tuple[list, dict]):
    #         """
    #         Unlock the file after processing is finished.
    #         """
    #         args, kwargs = initial_args
    #         file_id = kwargs["file_id"]
    #         try:
    #             text_file = self.files[file_id]
    #         except KeyError:
    #             # The file was removed from the table before processing finished.
    #             logger.info(
    #                 f"File {file_id} was removed from the table before processing finished. Ignoring worker results."
    #             )
    #             return
    #
    #         text_file.locked = False
    #         logger.debug(f"Worker thread {text_file.path} finished.")
    #         if self.all_files_ready():
    #             self.ready_for_translation.emit()
    #
    #     """
    #     Misc.
    #     """
    #
    #     def update_table_cell(self, file_id: str, column: int, message: str):
    #         """
    #         Show the translation progress in the table.
    #         """
    #         self.item(self.findItems(file_id, Qc.Qt.MatchExactly)[0].row(), column).setText(message)
    #
    #     def show_file_progress(self, file_id: str, message: str):
    #         """
    #         Show the translation progress in the table.
    #         """
    #         self.update_table_cell(file_id, Column.STATUS, message)
    #
    #     def all_files_ready(self) -> bool:
    #         """
    #         Check if all files' process level matches the expected value and are not locked.
    #         If no files exist, return False.
    #         Note: Epub files don't use quote protection, so ignore that option.
    #
    #         :return: True if all files are ready.
    #         """
    #         expected_process_level_text = st.ProcessLevel.RAW
    #         expected_process_level_epub = st.ProcessLevel.RAW
    #         if self.config.use_glossary:
    #             expected_process_level_text |= st.ProcessLevel.GLOSSARY
    #             expected_process_level_epub |= st.ProcessLevel.GLOSSARY
    #         if self.config.use_quote_protection:
    #             expected_process_level_text |= st.ProcessLevel.PROTECTED
    #
    #         if self.rowCount() == 0:
    #             return False
    #
    #         for row in range(self.rowCount()):
    #             file = self.files[self.item(row, Column.PATH).text()]
    #
    #             if file.locked:
    #                 return False
    #
    #             if isinstance(file, st.TextFile):
    #                 if (
    #                     self.files[self.item(row, Column.PATH).text()].process_level
    #                     != expected_process_level_text
    #                 ):
    #                     return False
    #             else:
    #                 if (
    #                     self.files[self.item(row, Column.PATH).text()].process_level
    #                     != expected_process_level_epub
    #                 ):
    #                     return False
    #         return True
    #
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


#     def preview_selected_file(self):
#         """
#         Open the preview window for the selected file.
#         """
#         selected_row = self.selectedItems()[0].row()
#         file_id = self.item(selected_row, Column.PATH).text()
#         file = self.files[file_id]
#         if isinstance(file, st.TextFile):
#             dtp.TextPreview(self, file, self.config).exec()
#         else:
#             dep.EpubPreview(self, file, self.config).exec()
#
#     def remove_selected_file(self):
#         """
#         Remove the selected file from the table.
#         """
#         selected_row = self.selectedItems()[0].row()
#         file_id = self.item(selected_row, Column.PATH).text()
#         self.removeRow(selected_row)
#         # This isn't automatically emitted when removing a row, but is necessary to update the buttons.
#         self.itemSelectionChanged.emit()
#
#         del self.files[file_id]
#         if self.all_files_ready():
#             self.ready_for_translation.emit()
#         else:
#             self.not_ready_for_translation.emit()
#         self.recalculate_char_total.emit()
#
#     def remove_all_files(self):
#         """
#         Remove all files from the table.
#         """
#         self.clearAll()
#         self.files.clear()
#         self.not_ready_for_translation.emit()
#         self.recalculate_char_total.emit()
#
#     def recalculate_char_count(self, file_id: str):
#         """
#         Update the table after a file has been processed.
#
#         :param file_id: The ID of the file to update.
#         """
#         file = self.files[file_id]
#         char_count = file.char_count
#         logger.debug(f"Recalculating char count for {file.path.name} ({char_count} chars).")
#         self.update_table_cell(file_id, Column.CHARS, hp.format_char_count(char_count))
#         self.recalculate_char_total.emit()
#
#
# def make_output_filename(input_file: st.InputFile, config: cfg.Config) -> Path:
#     # Append the language code to the file stem.
#     path = input_file.path
#     # Add lang extension.
#     path = path.with_stem(f"{path.stem}_{config.lang_to.lower()}")
#     # Add dump extension if translation failed.
#     if input_file.translation_incomplete():
#         path = path.with_suffix(".DUMP")
#
#     if config.use_fixed_output_path:
#         # Make the fixed output path absolute, meaning it isn't relative to the
#         # current working directory.
#         path = Path("/") / config.fixed_output_path / path.name
#         path = path.resolve()
#
#     path = hp.ensure_unique_file_path(path)
#
#     return path
