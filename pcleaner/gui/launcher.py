import os
import platform
import sys
from io import StringIO

import PySide6
import PySide6.QtGui as Qg
import PySide6.QtWidgets as Qw
import logzero
from logzero import logger
import torch

import pcleaner.cli_utils as cu
from pcleaner import __display_name__, __version__
from pcleaner.gui.mainwindow_driver import MainWindow


# This import is needed to load the icons.
import pcleaner.gui.rc_generated_files.rc_icons
import pcleaner.gui.rc_generated_files.rc_theme_icons
import pcleaner.gui.rc_generated_files.rc_themes


def launch() -> None:
    """
    Launch the GUI.
    """

    cu.get_log_path().parent.mkdir(parents=True, exist_ok=True)
    # Log up to 1MB to the log file.
    logzero.logfile(str(cu.get_log_path()), maxBytes=2**30, backupCount=1, loglevel=logzero.DEBUG)
    logger.info("\n---- Starting up ----")
    buffer = StringIO()
    buffer.write("\n- Program Information -\n")
    buffer.write(f"Program: {__display_name__} {__version__}\n")
    buffer.write(f"Log file is {cu.get_log_path()}\n")
    buffer.write(f"Config file is {cu.get_config_path()}\n")
    buffer.write(f"Cache directory is {cu.get_cache_path()}\n")
    buffer.write("- System Information -\n")
    buffer.write(f"Operating System: {platform.system()} {platform.release()}\n")
    buffer.write(f"Machine: {platform.machine()}\n")
    buffer.write(f"Python Version: {sys.version}\n")
    buffer.write(f"PySide (Qt) Version: {PySide6.__version__}\n")
    buffer.write(f"Available Qt Themes: {', '.join(Qw.QStyleFactory.keys())}\n")
    buffer.write(f"CPU Cores: {os.cpu_count()}\n")
    if torch.cuda.is_available():
        buffer.write(f"GPU: {torch.cuda.get_device_name(0)} (CUDA enabled)\n")
    else:
        buffer.write("GPU: None (CUDA not available)\n")

    logger.info(buffer.getvalue())

    # Start the main window.
    app = Qw.QApplication(sys.argv)

    Qg.QIcon.setFallbackSearchPaths([":/icons", ":/icon-themes"])
    # We need to set an initial theme on Windows, otherwise the icons will fail to load
    # later on, even when switching the theme again.
    if platform.system() == "Windows":
        Qg.QIcon.setThemeName("breeze")
        Qg.QIcon.setThemeSearchPaths([":/icons", ":/icon-themes"])

    try:
        window = MainWindow()
        window.show()
        sys.exit(app.exec())
    except Exception as e:
        logger.exception(
            e,
        )
    finally:
        logger.info("---- Shutting down ----\n")


if __name__ == "__main__":
    launch()
