import PySide6.QtWidgets as Qw
import PySide6.QtGui as Qg
import PySide6.QtCore as Qc


class CTableWidget(Qw.QTableWidget):
    """
    Extends the functionality with custom helpers
    """

    finished_drop = Qc.Signal()

    def __init__(self, parent=None):
        Qw.QTableWidget.__init__(self, parent)

    def clearAll(self):
        self.clearContents()
        self.setRowCount(0)
        self.itemSelectionChanged.emit()

    def currentText(self, col: int):
        return self.item(self.currentRow(), col).text()

    def setCurrentText(self, col: int, text: str):
        return self.item(self.currentRow(), col).setText(text)

    def appendRow(self, *args: str, select_new: bool = False):
        """
        Adds a new row to the bottom and fills each column with one of the args
        :param args: list(str)
        :param select_new: bool - highlight the new row
        """
        rows = self.rowCount()
        self.setRowCount(rows + 1)
        for i, arg in enumerate(args):
            self.setItem(rows, i, Qw.QTableWidgetItem(arg))
        if select_new:
            self.setCurrentCell(rows, 0)

    def moveRowUp(self, row: int):
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

    def moveRowDown(self, row: int):
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

    def columnValues(self, col: int):
        values = []
        for row in range(self.rowCount()):
            values.append(self.item(row, col).text())
        return values

    def resizeHeightToContents(self):
        # Add 1 per row to compensate for grid lines. Subtract 1 at the end since only inner grid lines count.
        height = 0
        for i in range(self.rowCount()):
            height += self.rowHeight(i) + 1
        self.setMinimumHeight(height - 1)

    def hasSelected(self):
        return self.selectedIndexes() != []

    def dragEnterEvent(self, event: Qg.QDragEnterEvent):
        if event.mimeData().hasUrls():
            event.accept()
        else:
            event.ignore()

    def dragMoveEvent(self, event: Qg.QDragMoveEvent):
        if event.mimeData().hasUrls():
            event.accept()
        else:
            event.ignore()

    def dropEvent(self, event: Qg.QDropEvent):
        if event.mimeData().hasUrls():
            for url in event.mimeData().urls():
                self.handleDrop(url.toLocalFile())
            event.accept()
        else:
            event.ignore()
        self.finished_drop.emit()

    def handleDrop(self, path: str):
        pass
