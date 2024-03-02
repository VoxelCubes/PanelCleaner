import os
import re
import time
from pathlib import Path

import PySide6.QtCore as Qc
import PySide6.QtWidgets as Qw
import humanfriendly as hf
import requests
import torch
from PySide6.QtCore import Signal, QObject, Slot
from attr import frozen
from humanfriendly import format_timespan, parse_size
from loguru import logger
from manga_ocr import MangaOcr

from pcleaner.helpers import tr
import pcleaner.config as cfg
import pcleaner.gui.gui_utils as gu
import pcleaner.gui.worker_thread as wt
import pcleaner.model_downloader as md
from pcleaner.gui.ui_generated_files.ui_ModelDownloader import Ui_ModelDownloader


PROGRESS_UPDATE_INTERVAL = 0.5


def format_size(size: int | float) -> str:
    """
    Format a size in bytes to a human readable string.

    :param size: The size in bytes.
    :return: The size as a human readable string.
    """
    return hf.format_size(size, binary=True)


@frozen
class ProgressData:
    """
    A data class for holding the progress data of a download.

    - percentage: The percentage of the download, from 0 to 100.
    - downloaded_size: The number of bytes downloaded so far.
    - file_size: The total size of the file in bytes.
    - speed: The download speed in bytes per second.
    - eta: The estimated time until the download is finished, in seconds.
        When no accurate estimate can be given yet, it will be -1.
    - file_name: [Optional] The name of the file being downloaded. Only used for the ocr model.
    """

    percentage: int
    downloaded_size: int
    file_size: int
    speed: float
    eta: int
    file_name: str | None = None


class DownloadSignals(QObject):
    progress_signal = Signal(ProgressData)


class ModelDownloader(Qw.QDialog, Ui_ModelDownloader):
    """
    A widget showing the current download progress of the model.
    """

    model_name: str = ""
    model_path: Path | None = None

    text_detector_downloaded: bool = False
    ocr_downloaded: bool = False
    inpainting_downloaded: bool = False
    encountered_error: bool = False

    def __init__(
        self,
        parent: Qw.QWidget | None = None,
        config: cfg.Config = None,
        need_text_detector: bool = True,
        need_ocr: bool = True,
        need_inpainting: bool = True,
    ):
        """
        Initialize the widget.

        :param parent: The parent widget.
        :param config: The config to use.
        :param need_text_detector: If True, download the text detector model.
        :param need_ocr: If True, download the ocr model.
        :param need_inpainting: If True, download the inpainting model.
        """
        Qw.QDialog.__init__(self, parent)
        self.setupUi(self)

        self.text_detector_downloaded = not need_text_detector
        self.ocr_downloaded = not need_ocr
        self.inpainting_downloaded = not need_inpainting

        self.buffer = []

        if need_text_detector:
            self.download_text_detector(config)
        else:
            temp_progress_data = ProgressData(100, 0, 0, 0, -1)
            self.model_name = self.tr("Already downloaded")
            self.show_text_detection_progress(temp_progress_data)

        if need_ocr:
            self.download_ocr()
        else:
            temp_progress_data = ProgressData(100, 0, 0, 0, -1, self.tr("Already downloaded"))
            self.show_ocr_progress(temp_progress_data)

        if need_inpainting:
            self.download_inpainting(config)
        else:
            temp_progress_data = ProgressData(100, 0, 0, 0, -1, self.tr("Already downloaded"))
            self.show_inpainting_progress(temp_progress_data)

    def check_finished(self) -> None:
        if self.text_detector_downloaded and self.ocr_downloaded:
            if not self.encountered_error:
                logger.info("Finished downloading all models.")
                self.accept()
            else:
                logger.error("Failed to download all models.")
                self.reject()

    # ============================= Text Detector =============================

    def download_text_detector(self, config: cfg.Config) -> None:
        # Check if we need the cuda or cpu model.
        if torch.cuda.is_available():
            model_url = md.MODEL_URL + md.TORCH_MODEL_NAME
            sha_hash = md.TORCH_SHA256
            self.model_name = self.tr("Text Detector model (CUDA)")
        else:
            model_url = md.MODEL_URL + md.CV2_MODEL_NAME
            sha_hash = md.CV2_SHA256
            self.model_name = self.tr("Text Detector model (CPU)")

        # Init the ui.
        temp_progress_data = ProgressData(0, 0, 0, 0, -1)
        self.show_text_detection_progress(temp_progress_data)

        # Start the download in a separate thread.
        threadpool = Qc.QThreadPool.globalInstance()
        signals = DownloadSignals()
        signals.progress_signal.connect(self.show_text_detection_progress)

        worker = wt.Worker(
            download_file,
            model_url,
            config.get_model_cache_dir(),
            signals,
            sha_hash,
            no_progress_callback=True,
        )
        worker.signals.finished.connect(self.text_detection_finished)
        worker.signals.result.connect(self.text_detection_result)
        worker.signals.error.connect(self.text_detection_error)
        threadpool.start(worker)

    @Slot(ProgressData)
    def show_text_detection_progress(self, progress_data: ProgressData) -> None:
        """
        Update the progress bar.

        :param progress_data: The progress data.
        """
        self.label_model_name.setText(self.model_name)
        self.label_model_size.setText(
            f"{format_size(progress_data.downloaded_size)} / {format_size(progress_data.file_size)}"
        )
        self.label_model_speed.setText(
            f"{format_size(progress_data.speed)}/s, {self.tr('ETA', 'estimated time of completion')}: "
            f"{format_timespan(progress_data.eta, ) if progress_data.eta >= 0 else '—'}"
        )
        self.progressBar_model.setValue(progress_data.percentage)

    @Slot(wt.WorkerError)
    def text_detection_error(self, worker_error: wt.WorkerError) -> None:
        """
        Show an error message.

        :param worker_error: The error message.
        """
        self.label_model_speed.setText("—")
        self.label_model_size.setText("")
        self.encountered_error = True
        gu.show_exception(self, self.tr("Download Failed"), str(worker_error.value), worker_error)

    @Slot(Path)
    def text_detection_result(self, model_path: Path | None) -> None:
        """
        Save the path to the downloaded model.

        :param model_path: The path to the downloaded model.
        """
        if model_path is None:
            return
        self.model_path = model_path

    def text_detection_finished(self) -> None:
        """
        Close the dialog if all models have been downloaded.
        """
        self.text_detector_downloaded = True
        self.check_finished()

    # ============================= OCR =============================

    def download_ocr(self) -> None:
        """
        Download the ocr model.
        """
        # Start the download in a separate thread.
        threadpool = Qc.QThreadPool.globalInstance()

        custom_stdout = gu.CaptureOutput()
        custom_stdout.text_written.connect(self.ocr_output_log)

        worker = wt.Worker(
            ocr_download_worker,
            custom_stdout,
            no_progress_callback=True,
        )
        worker.signals.finished.connect(self.ocr_finished)
        worker.signals.error.connect(self.ocr_error)
        threadpool.start(worker)

    def ocr_finished(self) -> None:
        """
        Close the dialog if all models have been downloaded.
        """
        self.ocr_downloaded = True
        if self.buffer:
            logger.info("\n".join(self.buffer))
            gu.show_warning(self, self.tr("OCR download errors"), "\n".join(self.buffer))
        self.check_finished()

    @Slot(wt.WorkerError)
    def ocr_error(self, worker_error: wt.WorkerError) -> None:
        """
        Show an error message.

        :param worker_error: The error message.
        """
        self.label_ocr_speed.setText("—")
        self.label_ocr_size.setText("")
        self.encountered_error = True
        gu.show_exception(self, self.tr("Download Failed"), str(worker_error.value), worker_error)

    @Slot(str, str)
    def ocr_output_log(self, text: str, stream: str) -> None:
        """
        Append the text to the output log.

        :param text: The text to append.
        :param stream: The stream the text was written to, stdout or stderr.
        """
        progress_data = parse_ocr_progress(text)
        if progress_data is None:
            return
        if isinstance(progress_data, str):
            self.buffer.append(progress_data)
            return
        # Update the ui with the progress data.
        self.show_ocr_progress(progress_data)

    def show_ocr_progress(self, progress_data: ProgressData) -> None:
        self.label_ocr_file_name.setText(progress_data.file_name)
        self.label_ocr_size.setText(
            f"{format_size(progress_data.downloaded_size)} / {format_size(progress_data.file_size)}"
        )
        self.label_ocr_speed.setText(
            f"{format_size(progress_data.speed)}/s, "
            + self.tr("ETA", "estimated time of completion")
            + f": {format_timespan(progress_data.eta, ) if progress_data.eta >= 0 else '—'}"
        )
        self.progressBar_ocr.setValue(progress_data.percentage)

    # ============================= Text Detector =============================

    def download_inpainting(self, config: cfg.Config) -> None:
        model_url = md.INPAINTING_URL
        sha_hash = md.INPAINTING_SHA256

        # Init the ui.
        temp_progress_data = ProgressData(0, 0, 0, 0, -1, self.tr("Inpainting model"))
        self.show_inpainting_progress(temp_progress_data)

        # Start the download in a separate thread.
        threadpool = Qc.QThreadPool.globalInstance()
        signals = DownloadSignals()
        signals.progress_signal.connect(self.show_inpainting_progress)

        worker = wt.Worker(
            download_file,
            model_url,
            config.get_model_cache_dir(),
            signals,
            sha_hash,
            no_progress_callback=True,
        )
        worker.signals.finished.connect(self.inpainting_finished)
        worker.signals.error.connect(self.inpainting_error)
        threadpool.start(worker)

    @Slot(ProgressData)
    def show_inpainting_progress(self, progress_data: ProgressData) -> None:
        """
        Update the progress bar.

        :param progress_data: The progress data.
        """
        self.label_inpaint_size.setText(
            f"{format_size(progress_data.downloaded_size)} / {format_size(progress_data.file_size)}"
        )
        self.label_inpaint_speed.setText(
            f"{format_size(progress_data.speed)}/s, {self.tr('ETA', 'estimated time of completion')}: "
            f"{format_timespan(progress_data.eta, ) if progress_data.eta >= 0 else '—'}"
        )
        self.progressBar_inpaint.setValue(progress_data.percentage)

    @Slot(wt.WorkerError)
    def inpainting_error(self, worker_error: wt.WorkerError) -> None:
        """
        Show an error message.

        :param worker_error: The error message.
        """
        self.label_inpaint_speed.setText("—")
        self.label_inpaint_size.setText("")
        self.encountered_error = True
        gu.show_exception(self, self.tr("Download Failed"), str(worker_error.value), worker_error)

    def inpainting_finished(self) -> None:
        """
        Close the dialog if all models have been downloaded.
        """
        self.inpainting_downloaded = True
        self.check_finished()


def ocr_download_worker(custom_stdout) -> None:
    with custom_stdout:
        MangaOcr()


# ============================= Utilities =============================


def download_file(url: str, save_dir: Path, signals: DownloadSignals, sha_hash: str = None) -> Path:
    """
    Download a file from a url.

    If something goes wrong, it will raise an exception.

    :param url: The url to download the file from.
    :param save_dir: The directory where the file will be saved.
    :param signals: The signals to emit progress and error messages.
    :param sha_hash: The sha256 hash of the file. If it doesn't match, the download will be aborted.
    :return: The path to the downloaded file.
    """
    response = requests.get(url, stream=True, timeout=10)
    try:
        response.raise_for_status()
    except requests.exceptions.HTTPError as e:
        raise ConnectionError(
            tr("Error downloading file from url: {url}").format(url=url) + "\n{e}"
        )

    file_name = os.path.basename(url)
    save_path = save_dir / file_name

    save_dir.mkdir(parents=True, exist_ok=True)
    if save_path.is_file():
        save_path.unlink()
    elif save_path.is_dir():
        save_path.rmdir()

    file_size = int(response.headers.get("Content-Length", 0))
    chunk_size = 8192  # 8KB
    downloaded_size = 0
    start_time = time.time()

    # Since we don't want to update the infos as often as the progress bar, only update it every few seconds.
    last_progress_time = start_time
    last_downloaded_size = 0
    last_speed = 0
    last_eta = -1

    with open(save_path, "wb") as f:
        for chunk in response.iter_content(chunk_size=chunk_size):
            if chunk:
                f.write(chunk)
                downloaded_size += len(chunk)

                elapsed_time = time.time() - start_time

                percentage = int((downloaded_size / file_size) * 100)

                # Only update the the rest of the infos if the time difference exceeds the update interval.
                if time.time() - last_progress_time > PROGRESS_UPDATE_INTERVAL or percentage == 100:
                    last_progress_time = time.time()
                    last_downloaded_size = downloaded_size
                    last_speed = downloaded_size / elapsed_time  # Bytes per second
                    remaining_bytes = file_size - downloaded_size
                    last_eta = round(remaining_bytes / last_speed)  # in seconds

                progress_data = ProgressData(
                    percentage=percentage,
                    downloaded_size=last_downloaded_size,
                    file_size=file_size,
                    speed=last_speed,
                    eta=last_eta,
                )
                signals.progress_signal.emit(progress_data)

    if not save_path.exists():
        raise OSError(
            tr(
                "Error downloading file from url: {url}\nFailed to save the file to {save_path}"
            ).format(url=url, save_path=save_path)
        )

    if sha_hash is not None:
        if not md.check_hash(save_path, sha_hash):
            save_path.unlink()
            raise OSError(
                tr(
                    "Error downloading file from url: {url}\nThe file content is different from expected."
                ).format(url=url)
            )

    return save_path


def parse_ocr_progress(line: str) -> ProgressData | str | None:
    """
    Parse a line of the download progress. The huggingface transformer library ostensibly uses
    tqdm to show the download progress.
    Example: '\rDownloading pytorch_model.bin:  12%|#1        | 31.5M/444M [00:04<00:59, 6.95MB/s]'
    Example: 'pytorch_model.bin:  19%|#8        | 83.9M/444M [00:02<00:12, 29.0MB/s]'

    Note: The specific application I'm tracking, Huggingface's transformer library, uses decimal size prefixes for data.

    :param line:
    :return:
    """
    line = line.strip()
    if not line:
        return None

    # Try matching known file names in the line
    known_filenames = [
        "preprocessor_config.json",
        "tokenizer_config.json",
        "config.json",
        "special_tokens_map.json",
        "vocab.txt",
        "pytorch_model.bin",
    ]

    # Fallback values.
    percentage: int = 0
    downloaded: int = 0
    total: int = 0
    speed: float = 0
    eta: int = 0
    filename: str = "?"

    # Using regex to capture relevant data.
    regex_pattern = r".*?(Downloading )?(?P<path>.*?): *(?P<percentage>\d+)%\|.*?\| (?P<downloaded>[\d.]+[kMGT]?B?)/(?P<total>[\d.]+[kMGT]?B?)(?: \[.*?<(?P<eta>.*), (?P<speed>[\d.]+[kMGT]?B/s)\])?"

    if match := re.search(regex_pattern, line, flags=re.IGNORECASE):
        # Figure out the file name. If it was not elided, use the file name from the line.
        # Otherwise, check if there is a directory delimiter in the path and use the last part
        # of the path as the file name.
        # If all else fails, try and match it to a known file name.
        filename = match.group("path")
        if filename.startswith("(…)"):
            filename = filename[3:]
            if "/" in filename:
                filename = filename.split("/")[-1]
            else:
                for known_filename in known_filenames:
                    if known_filename in filename:
                        filename = known_filename
                        break

        else:
            filename = filename.split("/")[-1]

        percentage = int(match.group("percentage"))

        downloaded = parse_size(match.group("downloaded"))
        total = parse_size(match.group("total"))

        speed = parse_size(match.group("speed")) if match.group("speed") else 0

        eta = parse_simple_time(match.group("eta")) if match.group("eta") else -1

    else:
        # If all that failed, attempt to salvage some information at the very least.
        logger.error(f'Could not parse ocr download progress data: "{line}"')

        regex_pattern_backup_percentage = r".*? *(?P<percentage>\d+)%"
        regex_pattern_backup_data = r" (?P<downloaded>[\d.]+[kMGT]?B?)/(?P<total>[\d.]+[kMGT]?B?)"

        match_percentage = re.search(regex_pattern_backup_percentage, line, flags=re.IGNORECASE)
        match_data = re.search(regex_pattern_backup_data, line, flags=re.IGNORECASE)

        if match_percentage:
            percentage = int(match_percentage.group("percentage"))

        if match_data:
            downloaded = parse_size(match_data.group("downloaded"))
            total = parse_size(match_data.group("total"))

        if not match_percentage or not match_data:
            # It's FUBAR.
            return "Could not parse ocr download progress data at all: " + line

    return ProgressData(percentage, downloaded, total, speed, eta, filename)


def parse_simple_time(time_str: str) -> int:
    """
    Parse time formatted by tqdm to total seconds.
    The expected format: "00:00" or "00:00:00"

    :param time_str: Time string formatted by tqdm (e.g., "240:25:35").
    :return: Total seconds.
    :raises ValueError: If the time format is invalid.
    """
    # Split the time string by colons
    parts = time_str.split(":")

    if len(parts) == 2:
        # Minutes and seconds are provided.
        return int(parts[0]) * 60 + int(parts[1])
    elif len(parts) == 3:
        # Hours, minutes, and seconds are provided.
        return int(parts[0]) * 60 * 60 + int(parts[1]) * 60 + int(parts[2])
    else:
        raise ValueError("Invalid time format")
