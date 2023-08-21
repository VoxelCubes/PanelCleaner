##############################################################################################
#
#  Worker Threads loosely based on QRunnable by Martin Fitzpatrick
#  https://www.pythonguis.com/tutorials/multithreading-pyside6-applications-qthreadpool/
#  License: MIT
#
##############################################################################################

import sys
import traceback
from dataclasses import dataclass
from typing import Callable

from PySide6.QtCore import QRunnable, Slot, Signal, QObject


@dataclass(frozen=True, slots=True)
class WorkerError:
    exception_type: type
    value: Exception
    traceback: str
    args: tuple | None = None
    kwargs: dict | None = None

    def __str__(self):
        return f"{self.exception_type}: {self.traceback}\n{self.value}"


class WorkerSignals(QObject):
    """
    Defines the signals available from a running worker thread.

    Supported signals are:

    finished
        The initial parameters passed to the worker when it was started, args and kwargs.

    error
        an instance of WorkerError.

    result
        object data returned from processing, if anything.

    progress
        anything to indicate the current state.

    """

    finished = Signal(tuple)
    error = Signal(WorkerError)
    result = Signal(object)
    progress = Signal(object)


class Worker(QRunnable):
    """
    Worker thread

    Inherits from QRunnable to handler worker thread setup, signals and wrap-up.

    DO NO. I REPEAT. DO NOT PUT @Slot() DECORATORS ON THE FUNCTIONS THAT YOU
    CONNECT TO THE SIGNALS. YOU WILL ONLY BE REWARDED WITH SEGFAULTS.

    :param callback: The function callback to run on this worker thread. Supplied args and
                     kwargs will be passed through to the runner.
    :param args: Arguments to pass to the callback function.
    :param no_progress_callback: If present (true or false), don't send progress signals.
    :param kwargs: Keywords to pass to the callback function.
    """

    def __init__(self, fn: Callable, *args, no_progress_callback: bool = False, **kwargs):
        QRunnable.__init__(self)

        # Store constructor arguments (re-used for processing).
        self.fn = fn
        self.args = args
        self.kwargs = kwargs
        self.signals = WorkerSignals()

        # Add the callback to our kwargs.
        if not no_progress_callback:
            self.kwargs["progress_callback"] = self.signals.progress

    @Slot()
    def run(self):
        """
        Initialise the runner function with passed args, kwargs.
        """

        # Retrieve args/kwargs here; and fire processing using them.
        try:
            result = self.fn(*self.args, **self.kwargs)
        except:
            traceback.print_exc()
            exception_type, value = sys.exc_info()[:2]
            self.signals.error.emit(
                WorkerError(exception_type, value, traceback.format_exc(), self.args, self.kwargs)
            )
        else:
            self.signals.result.emit(result)  # Return the result of the processing
        finally:
            self.signals.finished.emit((self.args, self.kwargs))  # Done
