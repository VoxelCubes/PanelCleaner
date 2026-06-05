"""
Smoke tests for the glossary editor dialog.

These require PySide6 and run headless via the Qt "offscreen" platform. They are skipped
automatically where PySide6 is not installed (e.g. a CLI-only environment).
"""

import os

import pytest

# Skip the whole module if PySide6 is unavailable.
pytest.importorskip("PySide6")
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import PySide6.QtWidgets as Qw  # noqa: E402
from PySide6.QtCore import Qt  # noqa: E402

from pcleaner.glossary import Glossary, GlossaryEntry, TermType  # noqa: E402
from pcleaner.gui.glossary_editor import (  # noqa: E402
    GlossaryEditor,
    COL_SOURCE,
    COL_TARGET,
    COL_NOTES,
    COL_DNT,
)


@pytest.fixture(scope="module")
def app():
    application = Qw.QApplication.instance() or Qw.QApplication([])
    yield application


def make_glossary():
    return Glossary(
        name="T",
        source_lang="ja",
        target_lang="th",
        entries=[
            GlossaryEntry("ハルカ", "ฮารุกะ", TermType.name),
            GlossaryEntry("先輩", "รุ่นพี่", TermType.honorific),
        ],
    )


def test_populates_table_from_glossary(app, tmp_path):
    editor = GlossaryEditor(make_glossary(), tmp_path / "g.toml")
    assert editor.table.rowCount() == 2
    assert editor.table.item(0, COL_SOURCE).text() == "ハルカ"
    assert editor.table.item(1, COL_TARGET).text() == "รุ่นพี่"


def test_add_and_collect(app, tmp_path):
    editor = GlossaryEditor(Glossary(), tmp_path / "g.toml")
    editor.add_row()
    editor.table.item(0, COL_SOURCE).setText("神")
    editor.table.item(0, COL_TARGET).setText("เทพ")
    editor.table.item(0, COL_NOTES).setText("god")
    entries = editor.collect_entries()
    assert len(entries) == 1
    assert entries[0].source == "神"
    assert entries[0].target == "เทพ"
    assert entries[0].notes == "god"


def test_blank_rows_are_skipped(app, tmp_path):
    editor = GlossaryEditor(Glossary(), tmp_path / "g.toml")
    editor.add_row()  # left blank
    assert editor.collect_entries() == []


def test_save_roundtrip(app, tmp_path):
    path = tmp_path / "g.toml"
    editor = GlossaryEditor(make_glossary(), path)
    editor.save_and_accept()
    assert path.is_file()
    reloaded = Glossary.load(path)
    assert {e.source for e in reloaded.entries} == {"ハルカ", "先輩"}


def test_dnt_checkbox_reflected(app, tmp_path):
    editor = GlossaryEditor(Glossary(), tmp_path / "g.toml")
    editor.add_row()
    editor.table.item(0, COL_SOURCE).setText("SFX")
    editor.table.item(0, COL_TARGET).setText("SFX")
    editor.table.item(0, COL_DNT).setCheckState(Qt.Checked)
    entries = editor.collect_entries()
    assert entries[0].do_not_translate is True
