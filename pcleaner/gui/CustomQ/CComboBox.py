from enum import Enum, auto
from typing import Callable

import PySide6.QtWidgets as Qw
from PySide6.QtCore import Slot, Signal
from loguru import logger


class HookState(Enum):
    Start = auto()
    CheckHook = auto()
    End = auto()


# noinspection PyPep8Naming
class CComboBox(Qw.QComboBox):
    """
    Extends the functionality with custom helpers
    And includes a secondary array for data linked to each item.

    The pre_change_hook is called before the current index is changed,
    and can interrupt the index change.
    """

    _pre_change_hook: Callable[[], bool] | None = None
    _prev_index: int = -1
    _next_index: int = -1
    _hook_state: HookState = HookState.Start
    hookedCurrentIndexChanged: Signal = Signal(int)

    def __init__(self, parent=None) -> None:
        Qw.QComboBox.__init__(self, parent)
        self._linked_data = []
        # self.installEventFilter(self)
        self.currentIndexChanged.connect(self.forward_current_index_changed_hooked)

    def set_pre_change_hook(self, hook: Callable[[], bool]) -> None:
        self._pre_change_hook = hook

    def emit_hooked_change(self, index: int) -> None:
        """
        Emit the hooked change signal, but only if the index has changed.
        Remember the previous index.
        :param index: The new index.
        """
        if self._prev_index != index:
            self._prev_index = index
        self.hookedCurrentIndexChanged.emit(index)

    @Slot(int)
    def forward_current_index_changed_hooked(self, new_index: int) -> None:
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
                # Recursively call this function again with the previous index.
                self.setCurrentIndex(
                    self._prev_index if self._prev_index != -1 else self.currentIndex()
                )
            case HookState.CheckHook:
                if self._pre_change_hook():
                    self._hook_state = HookState.End
                    # Recursively call this function again with the next index,
                    # but ignore the hook this time due to the end state.
                    self.setCurrentIndex(self._next_index)
                    self.emit_hooked_change(self._next_index)
                else:
                    self._hook_state = HookState.Start
            case HookState.End:
                self._hook_state = HookState.Start

    def clear(self) -> None:
        Qw.QComboBox.clear(self)
        self._linked_data.clear()

    def addTextItemLinkedData(self, text: str, data: any) -> None:
        self.addItem(text)
        self._linked_data.append(data)

    def setCurrentIndexByText(self, text: str) -> None:
        self.setCurrentIndex(self.findText(text))

    def setCurrentIndexByLinkedData(self, data: any) -> None:
        self.setCurrentIndex(self._linked_data.index(data))

    def indexLinkedData(self, data: any) -> int:
        return self._linked_data.index(data)

    @Slot(int)
    def setCurrentIndex(self, index: int) -> None:
        """
        Ensure the index is valid.
        :param index:
        """
        Qw.QComboBox.setCurrentIndex(self, min(max(index, 0), self.count() - 1))

    def currentLinkedData(self) -> None:
        try:
            return self._linked_data[self.currentIndex()]
        except IndexError:
            logger.error("No linked data found for current index")
            logger.error("Current index:", self.currentIndex())
            logger.error("Linked data:", self._linked_data)

    def removeItem(self, index: int) -> None:
        """
        Remove an item from the combo box, and its linked data.

        :param index: The index to remove.
        """
        if index < 0 or index >= self.count():
            logger.warning(f"Invalid index {index} for removal.")
            return

        # Remove the item and its linked data
        Qw.QComboBox.removeItem(self, index)
        self._linked_data.pop(index)

        # Reset hook state and prev index.
        self._prev_index = self.currentIndex()
        self._hook_state = HookState.Start
        # We need to emit the change manually since we're side-stepping the hook routine.
        self.hookedCurrentIndexChanged.emit(self.currentIndex())
