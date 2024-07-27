import PySide6.QtWidgets as Qw
import PySide6.QtGui as Qg
import PySide6.QtCore as Qc


# noinspection PyPep8Naming
class CTableWidget(Qw.QTableWidget):
    """
    Extends the functionality with custom helpers
    """

    finished_drop = Qc.Signal()
    currentRowChanged = Qc.Signal(int)
    resized = Qc.Signal()

    # Populate a list to make select columns editable.
    editable_columns: list[int] | None = None

    def __init__(self, parent=None) -> None:
        Qw.QTableWidget.__init__(self, parent)
        self.editable_columns = None
        self.currentCellChanged.connect(self.handleCurrentCellChanged)

    def setEditableColumns(self, columns: list[int]) -> None:
        self.editable_columns = columns

    def clearAll(self) -> None:
        self.clearContents()
        self.setRowCount(0)
        self.itemSelectionChanged.emit()

    def currentText(self, col: int) -> str:
        return self.item(self.currentRow(), col).text()

    def currentInt(self, col: int) -> int:
        return int(self.currentText(col))

    def setCurrentText(self, col: int, text: str) -> None:
        return self.item(self.currentRow(), col).setText(text)

    def appendRow(self, *args: str, select_new: bool = False) -> None:
        """
        Adds a new row to the bottom and fills each column with one of the args
        :param args: list(str)
        :param select_new: bool - highlight the new row
        """
        rows = self.rowCount()
        self.setRowCount(rows + 1)
        for i, arg in enumerate(args):
            if self.editable_columns is None:
                self.setItem(rows, i, Qw.QTableWidgetItem(arg))
            else:
                item = Qw.QTableWidgetItem(arg)
                if i in self.editable_columns:
                    item.setFlags(item.flags() | Qc.Qt.ItemIsEditable)
                else:
                    item.setFlags(item.flags() & ~Qc.Qt.ItemIsEditable)
                self.setItem(rows, i, item)
        if select_new:
            self.setCurrentCell(rows, 0)

    def moveRowUp(self, row: int) -> None:
        """
        Inserts a new row above row, then moves all items into it.
        Then deletes old row and selects new row.
        :param row: int
        """
        self.insertRow(row - 1)
        for i in range(self.columnCount()):
            item = self.takeItem(row + 1, i)
            self.setItem(row - 1, i, item)
        self.removeRow(row + 1)
        self.setCurrentCell(row - 1, 0)

    def moveRowDown(self, row: int) -> None:
        """
        Inserts a new row below row, then moves all items into it.
        Then deletes old row and selects new row.
        :param row: int
        """
        self.insertRow(row + 2)
        for i in range(self.columnCount()):
            item = self.takeItem(row, i)
            self.setItem(row + 2, i, item)
        self.removeRow(row)
        self.setCurrentCell(row + 1, 0)

    def columnValues(self, col: int) -> list:
        values = []
        for row in range(self.rowCount()):
            values.append(self.item(row, col).text())
        return values

    def resizeEvent(self, event):
        # Simple hook to catch resize events.
        super().resizeEvent(event)
        self.resized.emit()

    def resizeHeightToContents(self) -> None:
        # Add 1 per row to compensate for grid lines. Subtract 1 at the end since only inner grid lines count.
        height = 0
        for i in range(self.rowCount()):
            height += self.rowHeight(i) + 1
        self.setMinimumHeight(height - 1)

    def hasSelected(self) -> bool:
        return self.selectedIndexes() != []

    def dragEnterEvent(self, event: Qg.QDragEnterEvent) -> None:
        if event.mimeData().hasUrls():
            event.accept()
        else:
            event.ignore()

    def dragMoveEvent(self, event: Qg.QDragMoveEvent) -> None:
        if event.mimeData().hasUrls():
            event.accept()
        else:
            event.ignore()

    def dropEvent(self, event: Qg.QDropEvent) -> None:
        if event.mimeData().hasUrls():
            for url in event.mimeData().urls():
                self.handleDrop(url.toLocalFile())
            event.accept()
        else:
            event.ignore()
        self.finished_drop.emit()

    def handleDrop(self, path: str) -> None:
        pass

    def handleCurrentCellChanged(self, currentRow, currentColumn, previousRow, previousColumn):
        if currentRow != previousRow:
            self.currentRowChanged.emit(currentRow)
