from enum import Enum, auto

import PySide6.QtWidgets as Qw
from PySide6.QtCore import Slot, Signal, QEvent

from typing import Callable, Any
from logzero import logger


class HookState(Enum):
    Start = auto()
    CheckHook = auto()
    End = auto()


# noinspection PyPep8Naming
class CComboBox(Qw.QComboBox):
    """
    Extends the functionality with custom helpers
    And includes a secondary array for data linked to each item
    """

    _pre_change_hook: Callable[[], bool] | None = None
    _prev_index: int = -1
    _next_index: int = -1
    _hook_state: HookState = HookState.Start
    hookedCurrentIndexChanged: Signal = Signal(int)

    def __init__(self, parent=None):
        Qw.QComboBox.__init__(self, parent)
        self._linked_data = []
        # self.installEventFilter(self)
        self.currentIndexChanged.connect(self.forward_current_index_changed_hooked)

    def set_pre_change_hook(self, hook: Callable[[], bool]):
        self._pre_change_hook = hook

    def emit_hooked_change(self, index: int):
        """
        Emit the hooked change signal, but only if the index has changed.
        Remember the previous index.
        :param index: The new index.
        """
        if self._prev_index != index:
            self._prev_index = index
        self.hookedCurrentIndexChanged.emit(index)

    @Slot(int)
    def forward_current_index_changed_hooked(self, new_index: int):
        """
        Forward the current index changed signal, but only if the hook returns True.

        :param new_index: The new index
        """
        if self._pre_change_hook is None:
            self.hookedCurrentIndexChanged.emit(new_index)
            if self._prev_index != new_index:
                self._prev_index = new_index
            return

        match self._hook_state:
            case HookState.Start:
                # Go back to the previous index temporarily, to check the hook.
                self._next_index = new_index
                self._hook_state = HookState.CheckHook
                self.setCurrentIndex(
                    self._prev_index if self._prev_index != -1 else self.currentIndex()
                )
            case HookState.CheckHook:
                if self._pre_change_hook():
                    self._hook_state = HookState.End
                    self.setCurrentIndex(self._next_index)
                    self.emit_hooked_change(self._next_index)
                else:
                    self._hook_state = HookState.Start
            case HookState.End:
                self._hook_state = HookState.Start

    def clear(self):
        Qw.QComboBox.clear(self)
        self._linked_data.clear()

    def addTextItemLinkedData(self, text: str, data: any):
        self.addItem(text)
        self._linked_data.append(data)

    def setCurrentIndexByText(self, text: str):
        self.setCurrentIndex(self.findText(text))

    def setCurrentIndexByLinkedData(self, data: any):
        self.setCurrentIndex(self._linked_data.index(data))

    def indexLinkedData(self, data: any):
        return self._linked_data.index(data)

    @Slot(int)
    def setCurrentIndex(self, index: int) -> None:
        """
        Ensure the index is valid.
        :param index:
        """
        Qw.QComboBox.setCurrentIndex(self, min(max(index, 0), self.count() - 1))

    def currentLinkedData(self):
        try:
            return self._linked_data[self.currentIndex()]
        except IndexError:
            logger.error("No linked data found for current index")
            logger.error("Current index:", self.currentIndex())
            logger.error("Linked data:", self._linked_data)
