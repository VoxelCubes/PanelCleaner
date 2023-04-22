import sys
import argparse
import platform

import PySide6.QtWidgets as Qw
import PySide6.QtGui as Qg
import logzero
from logzero import logger

from pcleaner.gui.mainwindow_driver import MainWindow
import pcleaner.config as cfg
import pcleaner.cli_utils as cu
from pcleaner import __display_name__, __version__


# This import is needed to load the icons.
import pcleaner.gui.rc_generated_files.icons_rc
import pcleaner.gui.rc_generated_files.theme_icons_rc


def launch(input_paths: list[str]) -> None:
    """
    Launch the GUI.

    :param input_paths: List of paths to open on startup, may be empty.
    """

    cu.get_log_path().parent.mkdir(parents=True, exist_ok=True)
    # Log up to 1MB to the log file.
    logzero.logfile(str(cu.get_log_path()), maxBytes=2**30, backupCount=1, loglevel=logzero.DEBUG)
    logger.info("\n---- Starting up ----")
    logger.info(f"Program: {__display_name__} {__version__}")
    logger.info(f"Log file is {cu.get_log_path()}")

    # # Set up icon theme.
    # if args.icon_theme:
    #     if args.icon_theme == "Breeze":
    #         logger.info("Using Breeze icon theme.")
    #         Qg.QIcon.setThemeName("Breeze")
    #     elif args.icon_theme == "BreezeDark":
    #         logger.info("Using BreezeDark icon theme.")
    #         Qg.QIcon.setThemeName("BreezeDark")
    #     else:
    #         raise ValueError(f"Unknown icon theme: {args.icon_theme}")
    # elif platform.system() == "Windows" or platform.system() == "Darwin":
    #     # Default to Breeze on Windows.
    #     logger.info("Using Breeze icon theme.")
    #     Qg.QIcon.setThemeName("Breeze")

    # Start the main window.
    app = Qw.QApplication(sys.argv)

    try:
        window = MainWindow()
        window.show()
        # TODO load the initial paths
        sys.exit(app.exec())
    except Exception as e:
        logger.exception(
            e,
        )
    finally:
        logger.info("---- Shutting down ----\n")
