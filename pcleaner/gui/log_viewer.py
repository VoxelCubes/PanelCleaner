import re
from importlib import resources

import PySide6.QtCore as Qc
import PySide6.QtGui as Qg
import PySide6.QtWidgets as Qw

from pcleaner import data
from pcleaner import helpers as hp

colors_dark_theme = {
    "debug": Qg.QColor(41, 128, 185),
    "info": Qg.QColor(39, 174, 96),
    "warning": Qg.QColor(196, 91, 0),
    "error": Qg.QColor(218, 68, 83),
    "critical": Qg.QColor(149, 218, 76),
    "critical_bg": Qg.QColor(77, 31, 36),
    "traceback_values": Qg.QColor(40, 160, 160),
}
colors_light_theme = {
    "debug": Qg.QColor(0, 87, 174),
    "info": Qg.QColor(0, 110, 40),
    "warning": Qg.QColor(176, 128, 0),
    "error": Qg.QColor(191, 3, 3),
    "critical": Qg.QColor(191, 82, 3),
    "critical_bg": Qg.QColor(247, 230, 230),
    "traceback_values": Qg.QColor(0, 128, 128),
}


class Highlighter(Qg.QSyntaxHighlighter):
    def __init__(self, parent=None):
        Qg.QSyntaxHighlighter.__init__(self, parent)

        self._mappings = {}

    def add_mapping(self, pattern, format_):
        self._mappings[pattern] = format_

    def highlightBlock(self, text):
        for pattern, format_ in self._mappings.items():
            for match in re.finditer(pattern, text):
                start, end = match.span()
                self.setFormat(start, end - start, format_)


class LogSyntaxManager(Qc.QObject):
    def __init__(self, parent, widget: Qw.QPlainTextEdit, palette: Qg.QPalette):
        Qc.QObject.__init__(self, parent)

        self._highlighter = Highlighter()

        self.setup_editor(widget, palette)

    def setup_editor(self, widget: Qw.QPlainTextEdit, palette: Qg.QPalette):
        background_color = palette.color(Qg.QPalette.Window)
        theme_is_dark = background_color.lightness() < 128

        if theme_is_dark:
            colors = colors_dark_theme
        else:
            colors = colors_light_theme

        debug_format = Qg.QTextCharFormat()
        debug_format.setForeground(Qg.QBrush(colors["debug"]))

        info_format = Qg.QTextCharFormat()
        info_format.setForeground(Qg.QBrush(colors["info"]))

        warning_format = Qg.QTextCharFormat()
        warning_format.setForeground(Qg.QBrush(colors["warning"]))

        error_format = Qg.QTextCharFormat()
        error_format.setForeground(Qg.QBrush(colors["error"]))
        error_format.setFontWeight(Qg.QFont.Bold)

        critical_format = Qg.QTextCharFormat()
        critical_format.setForeground(Qg.QBrush(colors["critical"]))
        critical_format.setBackground(Qg.QBrush(colors["critical_bg"]))
        critical_format.setFontWeight(Qg.QFont.Bold)

        traceback_values_format = Qg.QTextCharFormat()
        traceback_values_format.setForeground(Qg.QBrush(colors["traceback_values"]))

        traceback_file_format = Qg.QTextCharFormat()
        traceback_file_format.setForeground(Qg.QBrush(colors["error"]))

        template = r"^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\.\d{3} \| LEVEL +\| [\w\.]+:[\w]+:\d+ -"

        self._highlighter.add_mapping(template.replace("LEVEL", "DEBUG"), debug_format)
        self._highlighter.add_mapping(template.replace("LEVEL", "INFO"), info_format)
        self._highlighter.add_mapping(template.replace("LEVEL", "WARNING"), warning_format)
        self._highlighter.add_mapping(template.replace("LEVEL", "ERROR"), error_format)
        self._highlighter.add_mapping(template.replace("LEVEL", "CRITICAL"), critical_format)
        self._highlighter.add_mapping(r"^\W*[└│].*$", traceback_values_format)
        self._highlighter.add_mapping(r'^>?\s*File ".*?", line \d+, in .+$', traceback_file_format)

        self._highlighter.setDocument(widget.document())


class LogViewer(Qw.QPlainTextEdit):
    """
    Show logs of individual sessions.
    Visualize them with syntax highlighting and stuff.
    """

    syntax_highlighter: LogSyntaxManager

    def __init__(
        self,
        parent=None,
    ) -> None:
        """
        Init the widget.

        :param parent: The parent widget.
        """
        Qw.QPlainTextEdit.__init__(self, parent)

        font_path = hp.resource_path(data, "NotoMono-Regular.ttf")
        font_id = Qg.QFontDatabase.addApplicationFont(str(font_path))
        self.setFont(Qg.QFont(Qg.QFontDatabase.applicationFontFamilies(font_id)[0]))
        self.syntax_highlighter = LogSyntaxManager(self, self, self.palette())

    def show_log(self, log_text: str) -> None:
        """
        Show the log in the text edit.

        :param log_text: The log text.
        """
        self.setPlainText(log_text)

    def get_log(self) -> str:
        """
        Get the log text.

        :return: The log text.
        """
        return self.toPlainText()

    def scroll_to_bottom(self) -> None:
        """
        Scroll to the bottom of the log.
        """
        self.verticalScrollBar().setValue(self.verticalScrollBar().maximum())
