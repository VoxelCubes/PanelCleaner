"""
Glossary editor dialog (PySide6).

A self-contained, manually-built ``QDialog`` for editing a workspace's glossary as a
table. It loads/saves via the ``pcleaner.glossary.Glossary`` model used by the CLI and
translator, so the GUI and CLI stay in sync. Built without a generated ``Ui_`` class so it
has no extra build-step dependency.
"""

from pathlib import Path

import PySide6.QtCore as Qc
import PySide6.QtWidgets as Qw
from PySide6.QtCore import Qt

from pcleaner.helpers import tr
from pcleaner.glossary import Glossary, GlossaryEntry, TermType, to_term_type

# Table columns.
COL_SOURCE = 0
COL_TARGET = 1
COL_TYPE = 2
COL_DNT = 3
COL_NOTES = 4
COLUMN_COUNT = 5

TERM_TYPE_VALUES = [str(t) for t in TermType]


class GlossaryEditor(Qw.QDialog):
    """A table editor for a workspace glossary, saved back to its TOML file."""

    def __init__(
        self,
        glossary: Glossary,
        path: Path,
        parent: Qw.QWidget | None = None,
    ) -> None:
        Qw.QDialog.__init__(self, parent)
        self._glossary = glossary
        self._path = Path(path)

        self.setWindowTitle(tr("Glossary Editor"))
        self.resize(720, 480)
        self._build_ui()
        self._populate()

    # -- UI construction -----------------------------------------------------------

    def _build_ui(self) -> None:
        layout = Qw.QVBoxLayout(self)

        info = Qw.QLabel(
            tr("Editing glossary: {path}").format(path=str(self._path)), self
        )
        info.setWordWrap(True)
        layout.addWidget(info)

        self.table = Qw.QTableWidget(0, COLUMN_COUNT, self)
        self.table.setHorizontalHeaderLabels(
            [tr("Source"), tr("Target"), tr("Type"), tr("Do not translate"), tr("Notes")]
        )
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.setColumnWidth(COL_SOURCE, 160)
        self.table.setColumnWidth(COL_TARGET, 160)
        self.table.setColumnWidth(COL_TYPE, 130)
        self.table.setColumnWidth(COL_DNT, 120)
        self.table.setSelectionBehavior(Qw.QAbstractItemView.SelectRows)
        layout.addWidget(self.table)

        # Row action buttons.
        row_buttons = Qw.QHBoxLayout()
        self.button_add = Qw.QPushButton(tr("Add"), self)
        self.button_remove = Qw.QPushButton(tr("Remove"), self)
        self.button_validate = Qw.QPushButton(tr("Validate"), self)
        row_buttons.addWidget(self.button_add)
        row_buttons.addWidget(self.button_remove)
        row_buttons.addWidget(self.button_validate)
        row_buttons.addStretch(1)
        layout.addLayout(row_buttons)

        self.button_add.clicked.connect(self.add_row)
        self.button_remove.clicked.connect(self.remove_selected_rows)
        self.button_validate.clicked.connect(self.validate)

        # Dialog buttons (Save / Cancel).
        self.button_box = Qw.QDialogButtonBox(
            Qw.QDialogButtonBox.Save | Qw.QDialogButtonBox.Cancel, self
        )
        self.button_box.accepted.connect(self.save_and_accept)
        self.button_box.rejected.connect(self.reject)
        layout.addWidget(self.button_box)

    def _make_type_combo(self, value: TermType) -> Qw.QComboBox:
        combo = Qw.QComboBox(self.table)
        combo.addItems(TERM_TYPE_VALUES)
        combo.setCurrentText(str(value))
        return combo

    def _append_entry_row(self, entry: GlossaryEntry) -> None:
        row = self.table.rowCount()
        self.table.insertRow(row)
        self.table.setItem(row, COL_SOURCE, Qw.QTableWidgetItem(entry.source))
        self.table.setItem(row, COL_TARGET, Qw.QTableWidgetItem(entry.target))
        self.table.setCellWidget(row, COL_TYPE, self._make_type_combo(entry.type))

        dnt_item = Qw.QTableWidgetItem()
        dnt_item.setFlags(Qt.ItemIsUserCheckable | Qt.ItemIsEnabled | Qt.ItemIsSelectable)
        dnt_item.setCheckState(Qt.Checked if entry.do_not_translate else Qt.Unchecked)
        dnt_item.setTextAlignment(Qt.AlignCenter)
        self.table.setItem(row, COL_DNT, dnt_item)

        self.table.setItem(row, COL_NOTES, Qw.QTableWidgetItem(entry.notes))

    def _populate(self) -> None:
        self.table.setRowCount(0)
        for entry in self._glossary.entries:
            self._append_entry_row(entry)

    # -- Slots ---------------------------------------------------------------------

    def add_row(self) -> None:
        self._append_entry_row(GlossaryEntry(source="", target=""))
        self.table.scrollToBottom()

    def remove_selected_rows(self) -> None:
        rows = sorted({index.row() for index in self.table.selectedIndexes()}, reverse=True)
        for row in rows:
            self.table.removeRow(row)

    def collect_entries(self) -> list[GlossaryEntry]:
        """Read the table back into a list of glossary entries."""
        entries: list[GlossaryEntry] = []
        for row in range(self.table.rowCount()):
            source = self._cell_text(row, COL_SOURCE)
            target = self._cell_text(row, COL_TARGET)
            if not source and not target:
                continue
            combo = self.table.cellWidget(row, COL_TYPE)
            term_type = to_term_type(combo.currentText()) if combo else TermType.term
            dnt_item = self.table.item(row, COL_DNT)
            do_not_translate = bool(dnt_item and dnt_item.checkState() == Qt.Checked)
            do_not_translate = do_not_translate or term_type == TermType.do_not_translate
            entries.append(
                GlossaryEntry(
                    source=source,
                    target=target,
                    type=term_type,
                    notes=self._cell_text(row, COL_NOTES),
                    do_not_translate=do_not_translate,
                )
            )
        return entries

    def _cell_text(self, row: int, col: int) -> str:
        item = self.table.item(row, col)
        return item.text().strip() if item is not None else ""

    def validate(self) -> bool:
        """Validate the current table contents, showing any warnings."""
        candidate = Glossary(
            name=self._glossary.name,
            source_lang=self._glossary.source_lang,
            target_lang=self._glossary.target_lang,
            entries=self.collect_entries(),
        )
        warnings = candidate.validate()
        if warnings:
            Qw.QMessageBox.warning(
                self, tr("Glossary issues"), "\n".join(f"- {w}" for w in warnings)
            )
            return False
        Qw.QMessageBox.information(self, tr("Glossary valid"), tr("No issues found."))
        return True

    def save_and_accept(self) -> None:
        """Save the glossary to disk and close the dialog."""
        self._glossary.entries = self.collect_entries()
        if self._glossary.save(self._path):
            self.accept()
        else:
            Qw.QMessageBox.warning(
                self,
                tr("Save failed"),
                tr("Could not write the glossary to {path}.").format(path=str(self._path)),
            )

    @classmethod
    def edit_path(cls, path: Path, parent: Qw.QWidget | None = None) -> "GlossaryEditor":
        """Convenience constructor that loads the glossary from a path."""
        path = Path(path)
        glossary = Glossary.load(path) if path.is_file() else Glossary()
        return cls(glossary, path, parent)
