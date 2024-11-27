import os
import subprocess

import PySide6.QtCore as Qc
import PySide6.QtGui as Qg
import PySide6.QtWidgets as Qw
from loguru import logger

import pcleaner.gui.post_action_config as pac
import pcleaner.gui.state_saver as ss
from pcleaner.gui.ui_generated_files.ui_PostActionRunner import Ui_PostActionRunner


class PostActionRunner(Qw.QDialog, Ui_PostActionRunner):
    """
    The post action execution dialog.
    """

    time_to_wait: int
    paused: bool
    dont_shut_down: bool
    state_saver: ss.StateSaver  # The state saver for the window.

    def __init__(
        self,
        parent=None,
        time_to_wait: int = 1,
        action_name: str = "",
        command: str = "",
        debug: bool = False,
        error: bool = False,
    ) -> None:
        """
        Init the widget.

        :param parent: The parent widget.
        """
        Qw.QDialog.__init__(self, parent)
        self.setupUi(self)

        self.paused = False
        self.time_to_wait = time_to_wait

        font = self.plainTextEdit_command.font()
        font.setFamily("Noto Mono")
        self.plainTextEdit_command.setFont(font)
        self.plainTextEdit_command.setPlainText(command)
        # Move the cursor to the end of the text.
        cursor = self.plainTextEdit_command.textCursor()
        cursor.movePosition(Qg.QTextCursor.End)
        self.plainTextEdit_command.setTextCursor(cursor)

        background_color = self.palette().color(Qg.QPalette.Window)
        theme_is_dark = background_color.lightness() < 128

        self.highlighter = ShellSyntaxHighlighter(
            self.plainTextEdit_command.document(), theme_is_dark
        )

        font = self.label_what.font()
        font.setPointSize(round(font.pointSize() * 1.5))
        self.label_what.setFont(font)

        if not error:
            self.label_error.hide()
            self.label_error_icon.hide()
        else:
            self.label_error_icon.setPixmap(Qg.QIcon.fromTheme("data-warning").pixmap(16, 16))

        self.dont_shut_down = action_name == pac.SHUTDOWN_COMMAND_NAME and debug

        if action_name == pac.SHUTDOWN_COMMAND_NAME:
            self.label_remaining_time.hide()
            self.pushButton_cancel_action.hide()
            self.label_action_icon.setPixmap(Qg.QIcon.fromTheme("system-shutdown").pixmap(64, 64))
            self.label_what.setText(self.tr("Shutting down the system"))
            self.lcdNumber_shutdown.setDigitCount(len(str(time_to_wait)))
            # I counted 18 pixels per digit.
            self.lcdNumber_shutdown.setFixedWidth(18 * len(str(time_to_wait)))
        else:
            self.lcdNumber_shutdown.hide()
            self.pushButton_cancel_shutdown.hide()
            self.label_action_icon.setPixmap(Qg.QIcon.fromTheme("dialog-scripts").pixmap(64, 64))
            self.label_what.setText(
                self.tr('Running the action "{action_name}"').format(action_name=action_name)
            )

        self.pushButton_again.hide()
        self.pushButton_again.clicked.connect(self.run_command)
        self.pushButton_close.hide()
        self.pushButton_close.clicked.connect(self.close)

        self.pushButton_pause.clicked.connect(self.pause)
        self.pushButton_resume.clicked.connect(self.resume)
        self.pushButton_resume.hide()
        self.pushButton_skip_countdown.clicked.connect(self.skip_countdown)

        self.pushButton_cancel_action.clicked.connect(self.cancel)
        self.pushButton_cancel_shutdown.clicked.connect(self.cancel)

        self.plainTextEdit_command.setTabStopDistance(40)

        if time_to_wait == 0:
            self.pushButton_again.show()
            self.pushButton_skip_countdown.hide()
            # Give the window a little time to appear.
            Qc.QTimer.singleShot(10, self.run_command)
        else:
            self.set_time_remaining(time_to_wait)
            self.count_down()

        self.state_saver = ss.StateSaver("post_action_runner")
        self.init_state_saver()
        self.state_saver.restore()

    def count_down(self) -> None:
        """
        Count down the time to wait.
        """
        if self.paused:
            return
        if self.time_to_wait > 0:
            if not self.paused:
                self.time_to_wait -= 1
                self.set_time_remaining(self.time_to_wait)
                Qc.QTimer.singleShot(1000, self.count_down)
        else:
            self.run_command()

    def run_command(self) -> None:
        if self.paused:
            # Last second cancellation.
            return
        if self.dont_shut_down:
            self.pushButton_again.show()
            self.pushButton_close.show()
            self.hide_countdown_stuff()
            logger.warning("Psyche! Not really shutting down, we're in debug mode.")
            return
        command = self.plainTextEdit_command.toPlainText()
        logger.info(f"Running command: {command}")
        subprocess.Popen(command, shell=True, start_new_session=True, env=os.environ)
        self.pushButton_again.show()
        self.pushButton_close.show()
        self.hide_countdown_stuff()

    def set_time_remaining(self, time: int) -> None:
        self.lcdNumber_shutdown.display(time)
        if time <= 3:
            # Make the number red.
            self.lcdNumber_shutdown.setStyleSheet("color: red")
        if time != 1:
            self.label_remaining_time.setText(
                self.tr("Remaining time: {time} seconds").format(time=time)
            )
        else:
            self.label_remaining_time.setText(self.tr("Remaining time: 1 second"))

    def init_state_saver(self) -> None:
        """
        Load the state from the state saver.
        """
        self.state_saver.register(self)

    def closeEvent(self, event: Qg.QCloseEvent) -> None:
        self.state_saver.save()
        self.paused = True
        event.accept()

    def pause(self) -> None:
        self.paused = True
        self.pushButton_pause.hide()
        self.pushButton_resume.show()

    def resume(self) -> None:
        self.paused = False
        self.pushButton_pause.show()
        self.pushButton_resume.hide()
        Qc.QTimer.singleShot(1000, self.count_down)

    def skip_countdown(self) -> None:
        self.time_to_wait = 0
        self.paused = False
        self.run_command()

    def cancel(self) -> None:
        self.paused = True
        self.pushButton_close.show()
        self.hide_countdown_stuff()

    def hide_countdown_stuff(self) -> None:
        self.pushButton_cancel_action.hide()
        self.pushButton_cancel_shutdown.hide()
        self.pushButton_pause.hide()
        self.pushButton_resume.hide()
        self.pushButton_skip_countdown.hide()
        self.label_remaining_time.hide()
        self.lcdNumber_shutdown.hide()

    def changeEvent(self, event) -> None:
        """
        Listen for palette change events to notify all widgets.
        """
        if event.type() == Qc.QEvent.PaletteChange:
            logger.debug("Palette changed, updating syntax highlighter.")
            background_color = self.palette().color(Qg.QPalette.Window)
            theme_is_dark = background_color.lightness() < 128
            self.highlighter.toggle_dark_mode(theme_is_dark)


class ShellSyntaxHighlighter(Qg.QSyntaxHighlighter):
    def __init__(self, document, dark_mode=False):
        super().__init__(document)

        self.dark_mode = dark_mode
        self.highlighting_rules = []

        self.color_map_light = {
            "comment": Qg.QColor(106, 153, 85),  # Greenish, subdued for comments
            "keyword": Qg.QColor(0, 81, 255),  # Bright blue for keywords
            "variable": Qg.QColor(75, 0, 130),  # Indigo for variables
            "string": Qg.QColor(163, 21, 21),  # Deep red for strings
            "number": Qg.QColor(60, 103, 64),  # Pastel green for numbers
            "operator": Qg.QColor(0, 122, 204),  # Soft blue for operators
            "path": Qg.QColor(36, 162, 36),  # Green for paths
        }

        self.color_map_dark = {
            "comment": Qg.QColor(106, 153, 85),  # Same greenish tone for comments
            "keyword": Qg.QColor(86, 156, 214),  # Soft cyan for keywords
            "variable": Qg.QColor(156, 220, 254),  # Bright cyan for variables
            "string": Qg.QColor(214, 157, 133),  # Soft coral for strings
            "number": Qg.QColor(181, 206, 168),  # Same pastel green for numbers
            "operator": Qg.QColor(212, 212, 212),  # Light gray for operators
            "path": Qg.QColor(255, 198, 109),  # Golden yellow for paths
        }
        self.setup_highlighting_rules()

    def setup_highlighting_rules(self):
        """Set up the highlighting rules based on the current color map."""
        color_map = self.color_map_dark if self.dark_mode else self.color_map_light
        self.highlighting_rules.clear()

        # Format for comments
        comment_format = Qg.QTextCharFormat()
        comment_format.setForeground(color_map["comment"])
        self.highlighting_rules.append((Qc.QRegularExpression(r"#.*"), comment_format))

        # Format for keywords
        keyword_format = Qg.QTextCharFormat()
        keyword_format.setForeground(color_map["keyword"])
        keywords = r"\b(if|then|else|fi|for|while|do|done|case|esac|in|function|elif|return|break|continue|export|unset|readonly)\b"
        self.highlighting_rules.append((Qc.QRegularExpression(keywords), keyword_format))

        # Format for variables
        variable_format = Qg.QTextCharFormat()
        variable_format.setForeground(color_map["variable"])
        self.highlighting_rules.append(
            (Qc.QRegularExpression(r"\$\w+|\$\{[^}]+\}"), variable_format)
        )

        # Format for strings
        string_format = Qg.QTextCharFormat()
        string_format.setForeground(color_map["string"])
        self.highlighting_rules.append(
            (Qc.QRegularExpression(r"'[^']*'|\"[^\"]*\""), string_format)
        )

        # Format for numbers
        number_format = Qg.QTextCharFormat()
        number_format.setForeground(color_map["number"])
        self.highlighting_rules.append((Qc.QRegularExpression(r"\b\d+\b"), number_format))

        # Format for operators and symbols
        operator_format = Qg.QTextCharFormat()
        operator_format.setForeground(color_map["operator"])
        self.highlighting_rules.append((Qc.QRegularExpression(r"[=|!<>;&]+"), operator_format))

        # File Paths (Linux/Mac)
        path_format = Qg.QTextCharFormat()
        path_format.setForeground(color_map["path"])
        self.highlighting_rules.append((Qc.QRegularExpression(r"(/[^ ]*|~[^ ]*)"), path_format))

        # Windows Absolute Paths
        win_path_format = Qg.QTextCharFormat()
        win_path_format.setForeground(color_map["path"])
        win_absolute = r"[A-Z]:\\(?:[^\\:*?\"<>|\r\n]+\\)*[^\\:*?\"<>|\r\n]*"
        self.highlighting_rules.append((Qc.QRegularExpression(win_absolute), win_path_format))

        # Windows Network Paths
        win_network = r"\\\\(?:[^\\:*?\"<>|\r\n]+\\)+[^\\:*?\"<>|\r\n]*"
        self.highlighting_rules.append((Qc.QRegularExpression(win_network), win_path_format))

        # Windows Escaped Paths
        win_escaped = r"[A-Z]:\\\\(?:[^\\:*?\"<>|\r\n]+\\\\)*[^\\:*?\"<>|\r\n]*"
        self.highlighting_rules.append((Qc.QRegularExpression(win_escaped), win_path_format))

    def toggle_dark_mode(self, dark_mode):
        """Toggle between light and dark mode and reapply highlighting rules."""
        self.dark_mode = dark_mode
        self.setup_highlighting_rules()
        self.rehighlight()

    def highlightBlock(self, text):
        """Apply syntax highlighting to a block of text."""
        for pattern, fmt in self.highlighting_rules:
            expression = pattern
            matches = expression.globalMatch(text)
            while matches.hasNext():
                match = matches.next()
                self.setFormat(match.capturedStart(), match.capturedLength(), fmt)
