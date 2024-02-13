import re
import os
from datetime import datetime
from typing import Sequence

import pcleaner.config as cfg
import pcleaner.cli_utils as cu

MAX_SESSIONS = 30


def get_username() -> str:
    """
    Get the username of the current user.
    We want to censor this in the log files for privacy.

    :return: The username of the current user.
    """
    return os.getlogin()


def censor(text: str) -> str:
    """
    Censor the username from the log file.
    We want to censor this in the log files for privacy.

    :param text: The text to censor.
    :return: The censored text.
    """
    return text.replace(get_username(), "<username>")


class LogSession:
    text: str
    date_time: datetime
    errors: int
    criticals: int
    corrupted: bool

    def __init__(self, text: str) -> None:
        self.text = text
        self.date_time = datetime.now()
        self.errors = 0
        self.criticals = 0
        self.corrupted = False
        self.parse()
        self.censor()

    def parse(self) -> None:
        self.errors = self.text.count("ERROR")
        self.criticals = self.text.count("CRITICAL")
        # Find the first parsable date in the log session.
        # Example: 2024-01-27 22:51:03.778
        first_date = re.search(r"\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}", self.text)
        if first_date:
            self.date_time = datetime.strptime(first_date.group(), "%Y-%m-%d %H:%M:%S")
        else:
            # If no date is found, we assume the log session is corrupted, since every
            # log session should start with a date.
            self.corrupted = True

    def censor(self) -> None:
        self.text = censor(self.text)


def load_log_file() -> str | None:
    """
    Load the log file. If none exists, return None.
    None existing is a bit odd, but it is possible that the log file was deleted.
    Not a big deal, but it is something to consider.

    :return: The log file contents.
    """
    contents = None
    try:
        with open(cu.get_log_path(), "r", encoding="utf-8") as file:
            contents = file.read()
    except FileNotFoundError:
        pass
    return contents


def parse_log_file(contents: str, max_sessions: int = MAX_SESSIONS) -> Sequence[LogSession]:
    """
    Parse the log file contents.

    :param contents: The log file contents.
    :param max_sessions: The maximum number of sessions to parse.
    :return: A list of log sessions, sorted by date, newest first.
    """

    sessions = []
    # Split the log file into sections based on start and shutdown messages
    raw_sessions = re.split(rf"({cfg.STARTUP_MESSAGE})", contents)

    # Pairing each startup message with its corresponding log session
    for i in range(len(raw_sessions) - 2, 0, -2):
        if raw_sessions[i] == cfg.STARTUP_MESSAGE and i + 1 < len(raw_sessions):
            session_text = raw_sessions[i + 1]
            # If there is a shutdown message, find it and truncate the session text
            shutdown_index = session_text.find(cfg.SHUTDOWN_MESSAGE, -500)
            if shutdown_index != -1:
                shutdown_index = session_text.find("\n", shutdown_index)
                if shutdown_index != -1:
                    session_text = session_text[:shutdown_index]

            session_text = session_text.strip()

            # Append sessions in reverse order
            sessions.append(LogSession(session_text))

            # Stop if the maximum number of sessions is reached
            if len(sessions) >= max_sessions:
                break

    return sessions
