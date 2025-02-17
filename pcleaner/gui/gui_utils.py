import io
import re
import sys
from types import TracebackType
from typing import Literal
from io import StringIO
from pathlib import Path
from importlib import resources

import PySide6.QtCore as Qc
import PySide6.QtGui as Qg
import PySide6.QtWidgets as Qw
from loguru import logger

from pcleaner.gui.error_dialog_driver import ErrorDialog
import pcleaner.gui.worker_thread as wt
import pcleaner.ocr.parsers as op
import pcleaner.gui.image_file as imf
import pcleaner.structures as st
from pcleaner.helpers import tr
import pcleaner.helpers as hp
from pcleaner.data import custom_icons
from pcleaner.data import color_themes


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
            label.setTextInteractionFlags(
                Qc.Qt.TextSelectableByMouse
                | Qc.Qt.LinksAccessibleByMouse
                | Qc.Qt.LinksAccessibleByKeyboard
            )


def show_exception(
    parent,
    title: str,
    msg: str,
    error_bundle: None | wt.WorkerError | tuple[type, BaseException, TracebackType] = None,
    collect_exception: bool = True,
) -> None:
    """
    Show an exception in a dialog along with logs.
    This automatically gathers the exception information from the current context
    or a given worker error object.

    You can also skip collecting the exception if you have already logged this separately and
    merely wish to open the Issue Reporter dialog for the user.

    :param parent: The parent widget.
    :param title: The title of the dialog.
    :param msg: The message to show.
    :param error_bundle: [Optional] A worker error or a tuple of exception information.
    :param collect_exception: [Optional] Whether to add exception information to the log.
    """

    if collect_exception:
        exception_type: type[BaseException]
        exception_value: BaseException
        exception_traceback: TracebackType

        if error_bundle is not None:
            if isinstance(error_bundle, tuple):
                exception_type, exception_value, exception_traceback = error_bundle
            elif isinstance(error_bundle, wt.WorkerError):
                exception_type = error_bundle.exception_type
                exception_value = error_bundle.value
                exception_traceback = error_bundle.traceback
            else:
                logger.error(f"Invalid error bundle: {error_bundle}")
                exception_type, exception_value, exception_traceback = sys.exc_info()
        else:
            exception_type, exception_value, exception_traceback = sys.exc_info()

        # Ignore the exception if it's a KeyboardInterrupt.
        if exception_type is KeyboardInterrupt:
            logger.warning("User interrupted the process.")
            return

        logger.opt(
            depth=1, exception=(exception_type, exception_value, exception_traceback)
        ).critical(msg)

    box = ErrorDialog(parent, title, msg)
    box.exec()


def show_critical(parent, title: str, msg: str, **kwargs) -> int:
    msg = msg.ljust(MIN_MSG_LENGTH)
    buttons = Qw.QMessageBox.Yes | Qw.QMessageBox.Abort
    if "buttons" in kwargs:
        buttons = kwargs.pop("buttons")
    box = SelectableMessageBox(
        Qw.QMessageBox.Critical,
        title,
        msg,
        buttons,
        parent,
        **kwargs,
    )
    return box.exec()


def show_warning(parent, title: str, msg: str, **kwargs) -> None:
    msg = msg.ljust(MIN_MSG_LENGTH)
    box = SelectableMessageBox(
        Qw.QMessageBox.Warning, title, msg, Qw.QMessageBox.Ok, parent, **kwargs
    )
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
    logger.debug(f"Opening file {path}")
    try:
        # Use Qt to open the file, so that it works on all platforms.
        Qg.QDesktopServices.openUrl(Qc.QUrl.fromLocalFile(str(path)))
    except Exception:
        show_exception(None, tr("File Error"), tr("Failed to open file."))


def get_available_themes() -> list[tuple[str, str]]:
    """
    Check the data/color_themes directory for available themes.
    The theme name is the plain file name. The display name is either defined in the
    theme file under section General, key name.
    If not defined, the display name is the theme name but capitalized and
    with spaces instead of underscores.

    Note: The implicit system theme is not included in the list.

    :return: A list of available theme names with their display names.
    """
    # Simply discover all files in the themes folder.
    themes = []
    with resources.path(color_themes, "") as theme_dir:
        theme_dir = Path(theme_dir)
    for theme_file in theme_dir.iterdir():
        # Skip dirs and empty files.
        if theme_file.is_dir() or theme_file.stat().st_size == 0:
            continue
        theme_name = theme_file.stem
        content = theme_file.read_text()
        display_name = theme_name.replace("_", " ").capitalize()
        in_general_section = False
        for line in content.split("\n"):
            line = line.strip()
            if line.startswith("[General]"):
                in_general_section = True
            elif line.startswith("[") and line.endswith("]"):
                if in_general_section:
                    # We found general, but came across the next section now.
                    break
                in_general_section = False
            elif "=" in line:
                key, value = map(str.strip, line.split("=", 1))
                if key == "Name":
                    display_name = value
                    break
        themes.append((theme_name, display_name))

    return themes


def custom_icon_path(icon_name: str, theme: Literal["dark", "light"] | str = "") -> Path:
    """
    Loads the given icon from the dark, light, or color-agnostic set of custom icons.
    File names may omit the extension, in which case .svg and .png are checked.

    :param icon_name: The icon's filename, with or without extension.
    :param theme: Indicate if the icon should be pulled from the light or dark theme,
        if applicable, otherwise leave blank.
    :return: A full path to the file.
    """
    custom_icon_dir = hp.resource_path(custom_icons)

    if theme:
        custom_icon_dir = custom_icon_dir / theme

    for extension in ("", ".svg", ".png"):
        icon_path = custom_icon_dir / (icon_name + extension)
        if icon_path.is_file():
            return icon_path

    raise FileNotFoundError(f"Failed to load '{custom_icon_dir / icon_name}'")


def load_custom_icon(icon_name: str, theme: Literal["dark", "light"] | str = "") -> Qg.QIcon:
    """
    Loads the given icon from the dark, light, or color-agnostic set of custom icons.
    File names may omit the extension, in which case .svg and .png are checked.
    If the file could not be found, a QIcon with a null pixmap is returned.

    :param icon_name: The icon's filename, with or without extension.
    :param theme: Indicate if the icon should be pulled from the light or dark theme,
        if applicable, otherwise leave blank.
    :return: A QIcon that may have a null pixmap.
    """
    try:
        icon_path = custom_icon_path(icon_name, theme)
        return Qg.QIcon(str(icon_path))
    except FileNotFoundError as e:
        logger.error(e)
        return Qg.QIcon()


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


def clamp_8bit(value: int) -> int:
    """
    Clamp a value to the 0-255 range.
    """
    return max(0, min(value, 255))


def apply_color_effect(
    source: Qg.QColor, effect_base: Qg.QColor, contrast_amount: float
) -> Qg.QColor:
    """
    Apply a color effect to a source color.

    :param source: The source color.
    :param effect_base: The base color for the effect.
    :param contrast_amount: The amount of contrast to apply.
    :return: The modified color.
    """
    # Essentially alpha blend, with the effect having the contrast amount as the alpha pasted on top.
    r = clamp_8bit(int(source.red() * (1 - contrast_amount) + effect_base.red() * contrast_amount))
    g = clamp_8bit(
        int(source.green() * (1 - contrast_amount) + effect_base.green() * contrast_amount)
    )
    b = clamp_8bit(
        int(source.blue() * (1 - contrast_amount) + effect_base.blue() * contrast_amount)
    )
    return Qg.QColor(r, g, b)


def load_color_palette(theme: str) -> Qg.QPalette:
    """
    Provide a theme name and get a QPalette object.
    The name should match one of the files in the themes folder.

    :param theme: The name of the theme.
    :return: A QPalette object.
    """
    palette = Qg.QPalette()

    file_path = hp.resource_path(color_themes, theme)

    file = Qc.QFile(file_path)
    if file.open(Qc.QFile.ReadOnly | Qc.QFile.Text):
        stream = Qc.QTextStream(file)
        content = stream.readAll()

        # Find the disabled color parameters.
        disabled_color = Qg.QColor.fromRgb(128, 128, 128)  # Default to gray.
        disabled_contrast_amount = 0.0
        in_disabled_section = False
        for line in content.split("\n"):
            line = line.strip()
            if line == "[ColorEffects:Disabled]":
                in_disabled_section = True
                continue
            if not in_disabled_section:
                continue
            if line.startswith("["):
                in_disabled_section = False
                break
            if "=" not in line:
                continue

            # Ok, now we're in the disabled section.
            key, value = map(str.strip, line.split("=", 1))
            if key == "Color":
                r, g, b = map(int, value.split(","))
                disabled_color.setRgb(r, g, b)
            elif key == "ContrastAmount":
                disabled_contrast_amount = float(value)

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
                    palette.setColor(Qg.QPalette.Normal, qt_color_role, Qg.QColor(r, g, b))
                    palette.setColor(Qg.QPalette.Inactive, qt_color_role, Qg.QColor(r, g, b))
                    # Calculate the disabled color.
                    disabled_color = apply_color_effect(
                        Qg.QColor(r, g, b), disabled_color, disabled_contrast_amount
                    )
                    palette.setColor(Qg.QPalette.Disabled, qt_color_role, disabled_color)
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
        "92": "color:#22ff22;",
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


# Map the OCR parse error codes to i18n-able strings.
OCR_PARSE_ERROR_CODES = {
    op.ParseErrorCode.OS_ERROR: tr("Failed to access the file."),
    op.ParseErrorCode.OTHER_ERROR: tr("An error occurred."),
    op.ParseErrorCode.NOT_6_COLUMNS: tr("The CSV file format requires exactly 6 columns."),
    op.ParseErrorCode.NOT_AN_INT: tr("The coordinates must be integers."),
    op.ParseErrorCode.INT_TOO_BIG: tr("The box coordinates may not exceed 2 billion."),
    op.ParseErrorCode.INVALID_FORMAT: tr("The file format was not recognized."),
    op.ParseErrorCode.INVALID_CSV_HEADER: tr(
        "The CSV file must start with a header row, followed by data rows."
    ),
    op.ParseErrorCode.NO_FILE_PATH: tr("The file path is missing."),
    op.ParseErrorCode.INVALID_PATH: tr("The file path is invalid."),
}


def format_ocr_parse_errors(errors: list[op.ParseError]) -> str:
    """
    Format the OCR parse errors into a human-readable, i18n-able string.

    ParseErrors contain the following:
    - line: int
    - error_code: ParseErrorCode
    - context: str

    :param errors: The list of OCR parse errors.
    :return: A formatted string.
    """

    buffer = StringIO()
    buffer.write(tr("OCR Parse Errors"))
    buffer.write("\n\n")

    for error in errors:
        buffer.write(f"- Line {error.line}: ")
        buffer.write(OCR_PARSE_ERROR_CODES[error.error_code])
        buffer.write("\n")
        buffer.write(f"  {error.context}\n\n")

    return buffer.getvalue()


class AmbiguousPath(Exception):
    pass


def match_image_files_to_ocr_analytics(
    images: list[imf.ImageFile], analytics: list[st.OCRAnalytic]
) -> tuple[dict[imf.ImageFile, st.OCRAnalytic], list[imf.ImageFile], list[st.OCRAnalytic]]:
    """
    Attempt to match all the currently loaded images to the OCR analytics.
    If an image couldn't find a partner, it gets added to the unmatched list of Images.
    Likewise, unmatched analytics are added to the unmatched list of Paths.

    If an analytic could be assigned to multiple images, raise an AmbiguousPath exception.

    :param images: The list of ImageFiles.
    :param analytics: The list of OCRAnalytics.
    :return: A dictionary of matched ImageFiles and OCRAnalytics, and two lists of unmatched items.
    """
    matched = {}
    unmatched_images = images.copy()
    unmatched_analytics = analytics.copy()

    # Attempt to match the file names in the analytics to the image paths
    # by making sure the file path is a suffix of the image path.
    for analytic in analytics:
        # Assumption: all removed box data elements report the same path,
        # so choose the first one.
        file_path_fragment = analytic.path

        for image in images:
            if str(image.path).endswith(str(file_path_fragment)):
                # Guard against double assignments.
                if image in matched:
                    raise AmbiguousPath(
                        tr("Multiple analytics match the image: {path}").format(path=image.path)
                    )
                if analytic not in unmatched_analytics:
                    raise AmbiguousPath(
                        tr("Multiple images match the file path: {path}").format(
                            path=file_path_fragment
                        )
                    )
                matched[image] = analytic
                unmatched_images.remove(image)
                unmatched_analytics.remove(analytic)

    return matched, unmatched_images, unmatched_analytics


def check_unsupported_cuda_error(caller, error: wt.WorkerError) -> bool:
    """
    Check if the error is related to an unsupported CUDA operation and show a message to the user.

    :param caller: The calling object.
    :param error: The WorkerError object.
    :return: True if the error was handled, False otherwise.
    """
    if error.exception_type == NotImplementedError and "CUDA" in str(error.value):
        # Get the current CUDA version.
        cuda_version = tr("Error, no version found.")
        try:
            import torch

            version = torch.version.cuda
            if version is not None:
                cuda_version = version
        except Exception:
            pass
        logger.opt(
            depth=1, exception=(error.exception_type, error.value, error.traceback)
        ).critical(error.value)
        show_critical(
            caller,
            tr("CUDA Error"),
            tr(
                "<html>"
                "Your GPU does not support the required CUDA operations.<br><br>"
                "Try uninstalling the current versions of torch and torchvision"
                " and installing the CPU version (or a different CUDA version) instead.<br>"
                "You can find further instructions here: <br><a href='https://pytorch.org/get-started/locally/'>"
                "https://pytorch.org/get-started/locally/</a><br>"
                'Check the "Compute Platform" section to see the available versions.<br><br>'
                f"Your current CUDA version is: {cuda_version}<br>"
                "</html>"
            ),
            buttons=Qw.QMessageBox.Ok,
            detailedText=str(error.value),
        )
        return True
    return False
