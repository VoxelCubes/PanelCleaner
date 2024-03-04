import os
import platform
import sys
from io import StringIO

import PySide6
import PySide6.QtGui as Qg
import PySide6.QtWidgets as Qw
import PySide6.QtCore as Qc
from loguru import logger
import torch

import pcleaner.cli_utils as cu
import pcleaner.config as cfg
from pcleaner import __display_name__, __version__
from pcleaner.gui.mainwindow_driver import MainWindow


# This import is needed to load the icons.
import pcleaner.gui.rc_generated_files.rc_icons
import pcleaner.gui.rc_generated_files.rc_theme_icons
import pcleaner.gui.rc_generated_files.rc_themes
import pcleaner.gui.rc_generated_files.rc_translations


def launch(debug: bool = False) -> None:
    """
    Launch the GUI.
    """

    cu.get_log_path().parent.mkdir(parents=True, exist_ok=True)
    # Log up to 1MB to the log file.
    # loguru.logfile(str(cu.get_log_path()), maxBytes=2**30, backupCount=1, loglevel=loguru.DEBUG)

    # Set up file logging.
    logger.add(str(cu.get_log_path()), rotation="10 MB", retention="1 week", level="DEBUG")

    logger.info("\n" + cfg.STARTUP_MESSAGE)
    buffer = StringIO()
    buffer.write("\n- Program Information -\n")
    buffer.write(f"Program: {__display_name__} {__version__}\n")
    buffer.write(f"Executing from: {__file__}\n")
    buffer.write(f"Log file: {cu.get_log_path()}\n")
    buffer.write(f"Config file: {cu.get_config_path()}\n")
    buffer.write(f"Cache directory: {cu.get_cache_path()}\n")
    buffer.write("- System Information -\n")
    buffer.write(f"Operating System: {platform.system()} {platform.release()}\n")
    if platform.system() == "Linux":
        buffer.write(f"Desktop Environment: {os.getenv('XDG_CURRENT_DESKTOP', 'unknown')}\n")
    buffer.write(f"Machine: {platform.machine()}\n")
    buffer.write(f"Python Version: {sys.version}\n")
    buffer.write(f"PySide (Qt) Version: {PySide6.__version__}\n")
    buffer.write(f"Available Qt Themes: {', '.join(Qw.QStyleFactory.keys())}\n")
    buffer.write(f"System locale: {Qc.QLocale.system().name()}\n")
    buffer.write(f"CPU Cores: {os.cpu_count()}\n")
    if torch.cuda.is_available():
        buffer.write(f"GPU: {torch.cuda.get_device_name(0)} (CUDA enabled)\n")
    else:
        buffer.write("GPU: None (CUDA not available)\n")

    logger.info(buffer.getvalue())

    # Start the main window.
    app = Qw.QApplication(sys.argv)

    # Load the config.
    config = cfg.load_config()

    # Apply the locale from the config.
    if config.locale:
        locale = Qc.QLocale(config.locale)
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

    path = ":/translations"
    if translator.load(locale, "PanelCleaner", "_", path):
        app.installTranslator(translator)
        logger.debug(f"Loaded App translations for {locale.name()}.")

    Qg.QIcon.setFallbackSearchPaths([":/icons", ":/icon-themes"])
    # We need to set an initial theme on Windows, otherwise the icons will fail to load
    # later on, even when switching the theme again.
    if platform.system() == "Windows":
        Qg.QIcon.setThemeName("breeze")
        Qg.QIcon.setThemeSearchPaths([":/icons", ":/icon-themes"])

    try:
        window = MainWindow(config, debug)
        window.show()
        sys.exit(app.exec())
    except Exception:
        logger.opt(exception=True).critical("Failed to initialize the main window.")
    finally:
        logger.info(cfg.SHUTDOWN_MESSAGE + "\n")


if __name__ == "__main__":
    launch()
