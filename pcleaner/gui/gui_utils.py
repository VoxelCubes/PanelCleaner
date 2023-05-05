import platform
import subprocess
import zipfile as zf
from pathlib import Path

import PySide6.QtWidgets as Qw
from logzero import logger


# For all show functions, pad the dialog message, so that the dialog is not too narrow for the window title.
MIN_MSG_LENGTH = 50


def show_critical(parent, title: str, msg: str):
    msg = msg.ljust(MIN_MSG_LENGTH)
    return Qw.QMessageBox.critical(parent, title, msg, Qw.QMessageBox.Yes, Qw.QMessageBox.Abort)


def show_warning(parent, title: str, msg: str):
    msg = msg.ljust(MIN_MSG_LENGTH)
    Qw.QMessageBox.warning(parent, title, msg, Qw.QMessageBox.Ok)


def show_info(parent, title: str, msg: str):
    msg = msg.ljust(MIN_MSG_LENGTH)
    Qw.QMessageBox.information(parent, title, msg, Qw.QMessageBox.Ok)


def show_question(
    parent, title: str, msg: str, buttons=Qw.QMessageBox.Yes | Qw.QMessageBox.Cancel
) -> int:
    msg = msg.ljust(MIN_MSG_LENGTH)
    dlg = Qw.QMessageBox(parent)
    dlg.setWindowTitle(title)
    dlg.setText(msg)
    dlg.setStandardButtons(buttons)
    dlg.setIcon(Qw.QMessageBox.Question)
    return dlg.exec()
