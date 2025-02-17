import locale as pylocale
import os
import platform
import sys
from importlib import resources
from io import StringIO
import logging

import PySide6
import PySide6.QtCore as Qc
import PySide6.QtGui as Qg
import PySide6.QtWidgets as Qw
import torch
from PIL import Image
from docopt import docopt
from loguru import logger

import pcleaner.cli_utils as cu
import pcleaner.config as cfg
import pcleaner.data.theme_icons as theme_icons_data
import pcleaner.data.translation_generated_files as translation_data
import pcleaner.gui.gui_utils as gu
import pcleaner.helpers as hp
from pcleaner import __display_name__, __version__
from pcleaner.gui.mainwindow_driver import MainWindow


# Allow loading of large images.
Image.MAX_IMAGE_PIXELS = 2**32


def launch(files_to_open: list[str], debug: bool = False) -> None:
    """
    Launch the GUI.

    :param files_to_open: A list of files to open.
    :param debug: Whether to enable debug mode.
    """

    cu.get_log_path().parent.mkdir(parents=True, exist_ok=True)

    logging.getLogger("transformers").setLevel(logging.ERROR)

    # Set up file logging.
    logger.add(str(cu.get_log_path()), rotation="10 MB", retention="1 week", level="DEBUG")

    # Set up a preliminary exception handler so that this still shows up in the log.
    # Once the gui is up and running it'll be replaced with a call to the gui's error dialog.
    def exception_handler(exctype, value, traceback) -> None:
        logger.opt(depth=1, exception=(exctype, value, traceback)).critical(
            "An uncaught exception was raised before the GUI was initialized."
        )

    sys.excepthook = exception_handler

    cu.dump_system_info(__file__, gui=True)

    # Start the main window.
    app = Qw.QApplication(sys.argv)

    # Load the config.
    config = cfg.load_config()

    # Apply the locale from the config.
    if config.locale:
        locale = Qc.QLocale(config.locale)
        # Apply it to python as well.
        pylocale.setlocale(pylocale.LC_ALL, locale.name())

    else:
        locale = Qc.QLocale.system()

    logger.info(f"Using locale {locale.name()}.")

    translator = Qc.QTranslator(app)

    # Load translations.
    path = Qc.QLibraryInfo.location(Qc.QLibraryInfo.TranslationsPath)
    if translator.load(locale, "qt", "_", path):
        logger.debug(f"Loaded built-in Qt translations for {locale.name()}.")
        app.installTranslator(translator)
    else:
        logger.warning(f"Failed to load Qt translations from {path}.")

    translator = Qc.QTranslator(app)

    if translator.load(locale, "qtbase", "_", path):
        logger.debug(f"Loaded built-in Qt base translations for {locale.name()}.")
        app.installTranslator(translator)
    else:
        logger.warning(f"Failed to load Qt base translations from {path}.")

    translator = Qc.QTranslator(app)

    path = str(hp.resource_path(translation_data))

    if translator.load(locale, "PanelCleaner", "_", path):
        app.installTranslator(translator)
        logger.debug(f"Loaded App translations for {locale.name()}.")

    # with hp.resource_path(theme_icons_data) as data_path:
    #     theme_icons = str(data_path)
    theme_icons = str(hp.resource_path(theme_icons_data))

    default_theme_search_paths = Qg.QIcon.themeSearchPaths()
    Qg.QIcon.setThemeSearchPaths([default_theme_search_paths, theme_icons, ":/icons"])

    Qg.QIcon.setFallbackSearchPaths([":/icons", theme_icons])
    # We need to set an initial theme on Windows, otherwise the icons will fail to load
    # later on, even when switching the theme again.
    if platform.system() == "Windows":
        Qg.QIcon.setThemeName("breeze")

    if files_to_open:
        input_paths = ", ".join(map(str, files_to_open))
        logger.info(f"Files to open: {input_paths}")

    try:
        window = MainWindow(config, files_to_open, debug)
        window.show()
        sys.exit(app.exec())
    except Exception:
        gu.show_exception(None, "Failed to launch", "Failed to initialize the main window.")
    finally:
        logger.info(cfg.SHUTDOWN_MESSAGE + "\n")


def main():
    docopt_doc = """Panel Cleaner

    Usage:
        pcleaner-gui [<image_path> ...] [--debug]

    Options:
        <image_path>          One or multiple files or directories to load on startup.
        --debug               Enable debug mode.
    """
    args = docopt(docopt_doc, version=f"Panel Cleaner {__version__}")
    launch(args.image_path, args.debug)


if __name__ == "__main__":
    main()
