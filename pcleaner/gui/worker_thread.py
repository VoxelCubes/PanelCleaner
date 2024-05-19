##############################################################################################
#
#  Worker Threads loosely based on QRunnable by Martin Fitzpatrick
#  https://www.pythonguis.com/tutorials/multithreading-pyside6-applications-qthreadpool/
#  License: MIT
#
##############################################################################################

import sys
from types import TracebackType
from dataclasses import dataclass
from typing import Callable

from PySide6.QtCore import QRunnable, Slot, Signal, QObject


@dataclass(frozen=True, slots=True)
class WorkerError:
    exception_type: type[BaseException]
    value: BaseException
    traceback: TracebackType
    args: tuple | None = None
    kwargs: dict | None = None

    def __str__(self) -> str:
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

    aborted
        The initial parameters passed to the worker when it was started, args and kwargs.

    """

    finished = Signal(tuple)
    error = Signal(WorkerError)
    result = Signal(object)
    progress = Signal(object)
    aborted = Signal(tuple)


class SharableFlag:
    def __init__(self, initial_value: bool = False) -> None:
        self._flag = initial_value

    def get(self) -> bool:
        return self._flag

    def set(self, value: bool) -> None:
        self._flag = value


class Abort(Exception):
    """
    Exception to abort the worker.
    """

    pass


class Worker(QRunnable):
    """
    Worker thread

    Inherits from QRunnable to handler worker thread setup, signals and wrap-up.

    DO NO. I REPEAT. DO NOT PUT @Slot() DECORATORS ON THE FUNCTIONS THAT YOU
    CONNECT TO THE SIGNALS. YOU WILL ONLY BE REWARDED WITH SEGFAULTS.

    :param callback: The function callback to run on this worker thread. Supplied args and
                     kwargs will be passed through to the runner.
    :param args: Arguments to pass to the callback function.
    :param no_progress_callback: [Optional] If True, the progress_callback will not be added to the kwargs.
    :param abort_signal: [Optional] A signal that will be emitted when the thread should abort.
    :param kwargs: Keywords to pass to the callback function.
    """

    aborted: SharableFlag

    def __init__(
        self,
        fn: Callable,
        *args,
        no_progress_callback: bool = False,
        abort_signal: Signal | None = None,
        **kwargs,
    ):
        QRunnable.__init__(self)

        # Store constructor arguments (re-used for processing).
        self.fn = fn
        self.args = args
        self.kwargs = kwargs
        self.signals = WorkerSignals()

        # If the abort signal is received, the abort flag is set to true.
        # The worker process must abort itself when the flag is true.
        self.aborted = SharableFlag(False)

        # Add the callback to our kwargs.
        if not no_progress_callback:
            self.kwargs["progress_callback"] = self.signals.progress

        # If an abort signal is provided, provide the sharable flag to the worker.
        if abort_signal is not None:
            self.kwargs["abort_flag"] = self.aborted
            abort_signal.connect(self.abort)

    @Slot()
    def run(self) -> None:
        """
        Initialise the runner function with passed args, kwargs.
        """

        # Retrieve args/kwargs here; and fire processing using them.
        # The function should expect the keyword arguments:
        # progress_callback and abort_flag unless disabled in the constructor.

        # After running, we need to check if the signals still exist. They may have been deleted in
        # the instance that the program was closed while the worker was running.
        # Otherwise the Python runtime crashes, which is ok in this state, but it just isn't very nice.
        try:
            try:
                result = self.fn(*self.args, **self.kwargs)
            except Abort:
                self.signals.aborted.emit((self.args, self.kwargs))
            except Exception:
                # traceback.print_exc()  # Disabled because we handle showing the error in whatever
                # called the worker. This also prevents the runtime errors from getting printed, which
                # are caught in an outer try block.
                # Use traceback.format_exc() to get the traceback as a string.
                # Using the raw traceback instead and letting the logger format that instead though.
                exception_type, value, traceback = sys.exc_info()
                self.signals.error.emit(
                    WorkerError(exception_type, value, traceback, self.args, self.kwargs)
                )
            else:
                self.signals.result.emit(result)  # Return the result of the processing.
            finally:
                self.signals.finished.emit((self.args, self.kwargs))  # Done
        except RuntimeError:
            # The signals were deleted, so we can't emit them.
            # This is fine, we just don't need to emit anything.
            pass

    @Slot()
    def abort(self) -> None:
        self.aborted.set(True)
