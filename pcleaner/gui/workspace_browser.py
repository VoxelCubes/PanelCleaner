"""
Workspace browser dialog (PySide6).

Lists the registered Webtoon Translate & Cleaner workspaces, shows each one's languages
and per-page progress, and provides quick actions: edit the glossary (via
``GlossaryEditor``) and open the manifest in the system editor. Self-contained and built
manually (no generated ``Ui_`` class).
"""

from pathlib import Path

import PySide6.QtCore as Qc
import PySide6.QtWidgets as Qw
from PySide6.QtCore import Qt

from pcleaner.helpers import tr
import pcleaner.config as cfg
import pcleaner.cli_utils as cli
from pcleaner.workspace import Workspace, PageState
from pcleaner.gui.glossary_editor import GlossaryEditor

COL_NAME = 0
COL_LANGS = 1
COL_PROGRESS = 2
COL_PATH = 3
COLUMN_COUNT = 4


def _progress_text(ws: Workspace) -> str:
    counts = ws.progress_summary()
    total = sum(counts.values())
    done = counts[PageState.rendered]
    return tr("{done}/{total} rendered").format(done=done, total=total)


class WorkspaceBrowser(Qw.QDialog):
    """A read-only browser over the saved workspaces, with glossary/manifest actions."""

    def __init__(self, config: cfg.Config, parent: Qw.QWidget | None = None) -> None:
        Qw.QDialog.__init__(self, parent)
        self.config = config
        self._rows: list[Path] = []

        self.setWindowTitle(tr("Workspaces"))
        self.resize(760, 460)
        self._build_ui()
        self.refresh()

    def _build_ui(self) -> None:
        layout = Qw.QVBoxLayout(self)

        self.table = Qw.QTableWidget(0, COLUMN_COUNT, self)
        self.table.setHorizontalHeaderLabels(
            [tr("Workspace"), tr("Languages"), tr("Progress"), tr("Path")]
        )
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.setColumnWidth(COL_NAME, 180)
        self.table.setColumnWidth(COL_LANGS, 120)
        self.table.setColumnWidth(COL_PROGRESS, 140)
        self.table.setSelectionBehavior(Qw.QAbstractItemView.SelectRows)
        self.table.setSelectionMode(Qw.QAbstractItemView.SingleSelection)
        self.table.setEditTriggers(Qw.QAbstractItemView.NoEditTriggers)
        self.table.itemSelectionChanged.connect(self._update_buttons)
        self.table.itemDoubleClicked.connect(lambda _item: self.edit_glossary())
        layout.addWidget(self.table)

        buttons = Qw.QHBoxLayout()
        self.button_glossary = Qw.QPushButton(tr("Edit Glossary"), self)
        self.button_manifest = Qw.QPushButton(tr("Open Manifest"), self)
        self.button_refresh = Qw.QPushButton(tr("Refresh"), self)
        buttons.addWidget(self.button_glossary)
        buttons.addWidget(self.button_manifest)
        buttons.addWidget(self.button_refresh)
        buttons.addStretch(1)
        layout.addLayout(buttons)

        self.button_glossary.clicked.connect(self.edit_glossary)
        self.button_manifest.clicked.connect(self.open_manifest)
        self.button_refresh.clicked.connect(self.refresh)

        self.button_box = Qw.QDialogButtonBox(Qw.QDialogButtonBox.Close, self)
        self.button_box.rejected.connect(self.reject)
        self.button_box.accepted.connect(self.accept)
        layout.addWidget(self.button_box)

        self._update_buttons()

    def refresh(self) -> None:
        """Reload the list of saved workspaces from the config."""
        self.table.setRowCount(0)
        self._rows = []
        for name, path in self.config.saved_workspaces.items():
            row = self.table.rowCount()
            self.table.insertRow(row)
            langs = "?"
            progress = tr("(manifest missing)")
            try:
                if Workspace.exists(path):
                    ws = Workspace.load(path)
                    langs = f"{ws.source_lang or '?'} -> {ws.target_lang or '?'}"
                    progress = _progress_text(ws)
            except Exception:
                progress = tr("(error reading)")
            self.table.setItem(row, COL_NAME, Qw.QTableWidgetItem(name))
            self.table.setItem(row, COL_LANGS, Qw.QTableWidgetItem(langs))
            self.table.setItem(row, COL_PROGRESS, Qw.QTableWidgetItem(progress))
            self.table.setItem(row, COL_PATH, Qw.QTableWidgetItem(str(path)))
            self._rows.append(Path(path))
        self._update_buttons()

    def _selected_root(self) -> Path | None:
        rows = {index.row() for index in self.table.selectedIndexes()}
        if not rows:
            return None
        return self._rows[min(rows)]

    def _update_buttons(self) -> None:
        has_selection = self._selected_root() is not None
        self.button_glossary.setEnabled(has_selection)
        self.button_manifest.setEnabled(has_selection)

    def edit_glossary(self) -> None:
        root = self._selected_root()
        if root is None:
            return
        try:
            ws = Workspace.load(root)
        except FileNotFoundError:
            Qw.QMessageBox.warning(self, tr("Workspace"), tr("Manifest missing."))
            return
        editor = GlossaryEditor.edit_path(ws.resolve_glossary_path(), self)
        editor.exec()

    def open_manifest(self) -> None:
        root = self._selected_root()
        if root is None:
            return
        cli.open_file_with_editor(Workspace.manifest_path(root), self.config.profile_editor)
