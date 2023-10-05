import io
import re
import sys
from io import StringIO
from pathlib import Path

import PySide6.QtCore as Qc
import PySide6.QtGui as Qg
import PySide6.QtWidgets as Qw
from logzero import logger


# For all show functions, pad the dialog message, so that the dialog is not too narrow for the window title.
MIN_MSG_LENGTH = 50


class SelectableMessageBox(Qw.QMessageBox):
    """
    Subclass the QMessageBox to make the text selectable.
    """

    def __init__(self, *args, **kwargs):
        super(SelectableMessageBox, self).__init__(*args, **kwargs)
        self.setTextInteractionFlags(Qc.Qt.TextSelectableByMouse)

        labels = self.findChildren(Qw.QLabel)
        for label in labels:
            label.setTextInteractionFlags(Qc.Qt.TextSelectableByMouse)


def show_critical(parent, title: str, msg: str) -> int:
    msg = msg.ljust(MIN_MSG_LENGTH)
    box = SelectableMessageBox(
        Qw.QMessageBox.Critical, title, msg, Qw.QMessageBox.Yes | Qw.QMessageBox.Abort, parent
    )
    return box.exec()


def show_warning(parent, title: str, msg: str) -> None:
    msg = msg.ljust(MIN_MSG_LENGTH)
    box = SelectableMessageBox(Qw.QMessageBox.Warning, title, msg, Qw.QMessageBox.Ok, parent)
    box.exec()


def show_info(parent, title: str, msg: str) -> None:
    msg = msg.ljust(MIN_MSG_LENGTH)
    box = SelectableMessageBox(Qw.QMessageBox.Information, title, msg, Qw.QMessageBox.Ok, parent)
    box.exec()


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


def open_file(path: Path) -> None:
    """
    Open any given file with the default application.
    """
    logger.info(f"Opening file {path}")
    try:
        # Use Qt to open the file, so that it works on all platforms.
        Qg.QDesktopServices.openUrl(Qc.QUrl.fromLocalFile(str(path)))
    except Exception as e:
        logger.exception(e)


class CaptureOutput(Qc.QObject):
    text_written = Qc.Signal(str, str)

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self._io_stdout = io.StringIO()
        self._io_stderr = io.StringIO()

    def __enter__(self) -> "CaptureOutput":
        self._original_stdout = sys.stdout
        self._original_stderr = sys.stderr
        sys.stdout = self
        sys.stderr = self
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        sys.stdout = self._original_stdout
        sys.stderr = self._original_stderr

    def write(self, string, stream="stdout") -> None:
        if stream == "stdout":
            self._io_stdout.write(string)
        elif stream == "stderr":
            self._io_stderr.write(string)
        self.text_written.emit(string, stream)

    def getvalue(self, stream="stdout") -> str:
        if stream == "stdout":
            return self._io_stdout.getvalue()
        elif stream == "stderr":
            return self._io_stderr.getvalue()

    def flush(self) -> None:
        self._io_stdout.flush()
        self._io_stderr.flush()


# Mapping between KDE color keys and QPalette roles
section_role_mapping = {
    "Colors:Button": {
        "BackgroundNormal": Qg.QPalette.Button,
        "ForegroundNormal": Qg.QPalette.ButtonText,
        "ForegroundActive": Qg.QPalette.BrightText,
    },
    "Colors:View": {
        "BackgroundNormal": Qg.QPalette.Base,
        "BackgroundAlternate": Qg.QPalette.AlternateBase,
        "ForegroundNormal": Qg.QPalette.Text,
        "ForegroundLink": Qg.QPalette.Link,
        "ForegroundVisited": Qg.QPalette.LinkVisited,
        "ForegroundInactive": Qg.QPalette.PlaceholderText,
    },
    "Colors:Selection": {
        "BackgroundNormal": Qg.QPalette.Highlight,
        "ForegroundNormal": Qg.QPalette.HighlightedText,
    },
    "Colors:Tooltip": {
        "BackgroundNormal": Qg.QPalette.ToolTipBase,
        "ForegroundNormal": Qg.QPalette.ToolTipText,
    },
    "Colors:Window": {
        "BackgroundNormal": Qg.QPalette.Window,
        "ForegroundNormal": Qg.QPalette.WindowText,
    },
    # Add more mappings as needed
}


def load_color_palette(theme: str) -> Qg.QPalette:
    """
    Provide a theme name and get a QPalette object.
    The name should match one of the files in the themes folder.

    :param theme: The name of the theme.
    :return: A QPalette object.
    """
    palette = Qg.QPalette()

    file = Qc.QFile(f":/themes/{theme}")
    if file.open(Qc.QFile.ReadOnly | Qc.QFile.Text):
        stream = Qc.QTextStream(file)
        content = stream.readAll()

        section = None
        for line in content.split("\n"):
            line = line.strip()
            if line.startswith("[") and line.endswith("]"):
                section = line[1:-1]
            elif "=" in line:
                key, value = map(str.strip, line.split("=", 1))
                role_mapping = section_role_mapping.get(section, {})
                qt_color_role = role_mapping.get(key, None)
                if qt_color_role is not None:
                    r, g, b = map(int, value.split(","))
                    palette.setColor(qt_color_role, Qg.QColor(r, g, b))
    else:
        raise ValueError(f"Could not open theme file: {theme}")

    # Fallback calculations
    if not palette.color(Qg.QPalette.Light).isValid():
        base = palette.color(Qg.QPalette.Button)
        palette.setColor(Qg.QPalette.Light, base.lighter(150))

    if not palette.color(Qg.QPalette.Dark).isValid():
        base = palette.color(Qg.QPalette.Window)
        palette.setColor(Qg.QPalette.Dark, base.darker(150))

    if not palette.color(Qg.QPalette.Midlight).isValid():
        light = palette.color(Qg.QPalette.Light)
        button = palette.color(Qg.QPalette.Button)
        midlight = Qg.QColor(
            (light.red() + button.red()) // 2,
            (light.green() + button.green()) // 2,
            (light.blue() + button.blue()) // 2,
        )
        palette.setColor(Qg.QPalette.Midlight, midlight)

    if not palette.color(Qg.QPalette.Mid).isValid():
        dark = palette.color(Qg.QPalette.Dark)
        button = palette.color(Qg.QPalette.Button)
        mid = Qg.QColor(
            (dark.red() + button.red()) // 2,
            (dark.green() + button.green()) // 2,
            (dark.blue() + button.blue()) // 2,
        )
        palette.setColor(Qg.QPalette.Mid, mid)

    if not palette.color(Qg.QPalette.Shadow).isValid():
        palette.setColor(Qg.QPalette.Shadow, Qg.QColor(0, 0, 0))

    return palette


def ansi_to_html(input_text: str) -> str:
    """
    Convert ansi escape sequences to html.

    Analytics HTML template
    <html><head><meta name="qrichtext" content="1" /><style type="text/css">
    p, li { white-space: pre-wrap; font-family: Noto Mono, Monospace; size: 12pt}
    </style></head><body>
    <p style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px;
     -qt-block-indent:0; text-indent:0px;"><span style=" ">Mask Fitment Analytics
     <br />---------------------- <br />Total boxes: 5 | Masks succeeded: 5 (100%)
     | Masks failed: </span><span style="color:#b21818;">0</span><span style=" ">
     <br />Perfect masks: </span><span style="color:#18b2b2;">5</span><span style=" ">
     (100%) | Average border deviation: 0.00 <br /><br />Mask usage by mask size
     (smallest to largest): <br />Mask 0  :  </span><span style="color:#18b2b2;">0</span>
     <span style=" "> / 0 <br />Mask 1  :  </span><span style="color:#18b2b2;">0</span>
     <span style=" "> / 0 <br />Mask 2  :  </span><span style="color:#18b2b2;">0</span>
     <span style=" "> / 0 <br />Mask 3  :  </span><span style="color:#18b2b2;">0</span>
     <span style=" "> / 0 <br />Mask 4  :  </span><span style="color:#18b2b2;">0</span>
     <span style=" "> / 0 <br />Mask 5  :  </span><span style="color:#18b2b2;">0</span>
     <span style=" "> / 0 <br />Mask 6  : </span><span style="color:#18b2b2;">
     ████████████████████████████████████████</span><span style=" "> </span>
     <span style="color:#18b2b2;">1</span><span style=" "> / 1 <br />Mask 7  :  </span>
     <span style="color:#18b2b2;">0</span><span style=" "> / 0 <br />Mask 8  :  </span>
     <span style="color:#18b2b2;">0</span><span style=" "> / 0 <br />Mask 9  :  </span>
     <span style="color:#18b2b2;">0</span><span style=" "> / 0 <br />Mask 10 :  </span>
     <span style="color:#18b2b2;">0</span><span style=" "> / 0 <br />Box mask: </span>
     <span style="color:#18b2b2;">████████████████████████████████████████</span>
     <span style=" "> </span><span style="color:#18b2b2;">4</span><span style=" ">
     / 4 <br /><br /></span><span style="color:#18b2b2;">█ Perfect</span><span style=" ">
     | █ Total<br /><br /></span></p></body></html>
    """
    # Define ANSI escape sequences and corresponding Qt HTML color codes
    ansi_to_html_lut = {
        "31": "color:#eb514f;",
        "32": "color:#00ff00;",
        "33": "color:#ffff00;",
        "34": "color:#0000ff;",
        "35": "color:#a771bf;",
        "36": "color:#00a3a3;",
        "37": "color:#ffffff;",
        "39": " ",  # Default color
    }

    # Initialize HTML header and footer
    html_header = """<html><head><meta name="qrichtext" content="1" /><style type="text/css">
        p, li { white-space: pre-wrap; font-family: Noto Mono, Monospace; size: 12pt}
        </style></head><body>
        <p style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;">"""
    html_footer = "</p></body></html>"

    # Initialize output HTML with header
    buffer = StringIO()
    buffer.write(html_header)

    # Initialize current_style
    current_style = ""

    # Strip leading and trailing whitespace.
    input_text = input_text.strip()

    # Use regex to find all ANSI sequences and split text
    for plain_text, ansi_code in re.findall(r"(.*?)(?:\x1b\[(\d+)m|$)", input_text, re.DOTALL):
        # Add plain text
        newline = "\n"
        buffer.write(
            f'<span style="{current_style}">{plain_text.replace(newline, "<br />")}</span>'
        )

        # Update the style for the next span based on ANSI code
        if ansi_code:
            current_style = ansi_to_html_lut.get(ansi_code, "")

    # Add HTML footer
    buffer.write(html_footer)

    return buffer.getvalue()
