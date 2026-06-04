"""Tests for the workspace data model (pcleaner/workspace.py)."""

from pcleaner.workspace import (
    Workspace,
    ProfileRef,
    PageEntry,
    ChapterEntry,
    PageState,
    to_page_state,
)
from pcleaner.translator.config import GlossaryMode
from pcleaner.rendering.config import Alignment


def test_to_page_state_unknown_defaults_to_raw():
    assert to_page_state("rendered") == PageState.rendered
    assert to_page_state("nonsense") == PageState.raw


def test_create_and_save_load_roundtrip(tmp_path):
    ws = Workspace.create(
        tmp_path / "series",
        name="Series XYZ",
        source_lang="ja",
        target_lang="th",
        profile_ref=ProfileRef(name="myprofile"),
    )
    ws.translator.model = "openai/gpt-4o"
    ws.render.alignment = Alignment.LEFT
    ws.fonts = {"ja": "NotoSansJP"}
    ws.chapters = [
        ChapterEntry(
            "ch001",
            "Chapter 1",
            pages=[PageEntry("001.png", PageState.rendered, "uuid-1")],
        )
    ]
    ws.init_dirs()
    assert ws.save()

    loaded = Workspace.load(tmp_path / "series")
    assert loaded.name == "Series XYZ"
    assert loaded.source_lang == "ja"
    assert loaded.target_lang == "th"
    assert loaded.profile_ref.name == "myprofile"
    assert loaded.translator.model == "openai/gpt-4o"
    assert loaded.translator.glossary_mode == GlossaryMode.PROMPT_REPLACE
    assert loaded.render.alignment == Alignment.LEFT
    assert loaded.fonts == {"ja": "NotoSansJP"}
    assert len(loaded.chapters) == 1
    page = loaded.chapters[0].pages[0]
    assert page.file == "001.png"
    assert page.state == PageState.rendered
    assert page.uuid == "uuid-1"


def test_init_dirs_creates_skeleton_and_glossary(tmp_path):
    ws = Workspace.create(tmp_path / "s", "S", "ja", "th")
    ws.init_dirs()
    assert (tmp_path / "s" / "chapters").is_dir()
    assert ws.cache_dir().is_dir()
    assert ws.resolve_glossary_path().is_file()
    glossary = ws.resolve_glossary()
    assert glossary.source_lang == "ja"
    assert glossary.target_lang == "th"


def test_exists_and_load_missing(tmp_path):
    assert Workspace.exists(tmp_path) is False
    try:
        Workspace.load(tmp_path)
        assert False, "expected FileNotFoundError"
    except FileNotFoundError:
        pass


def test_set_page_state(tmp_path):
    ws = Workspace.create(tmp_path / "s", "S", "ja", "th")
    ws.chapters = [ChapterEntry("ch001", pages=[PageEntry("001.png")])]
    assert ws.set_page_state("ch001", "001.png", PageState.cleaned, "u1") is True
    page = ws.chapters[0].pages[0]
    assert page.state == PageState.cleaned
    assert page.uuid == "u1"
    # Unknown chapter / page returns False.
    assert ws.set_page_state("nope", "001.png", PageState.cleaned) is False
    assert ws.set_page_state("ch001", "nope.png", PageState.cleaned) is False


def test_progress_summary(tmp_path):
    ws = Workspace.create(tmp_path / "s", "S", "ja", "th")
    ws.chapters = [
        ChapterEntry(
            "ch001",
            pages=[
                PageEntry("1.png", PageState.raw),
                PageEntry("2.png", PageState.cleaned),
                PageEntry("3.png", PageState.rendered),
            ],
        )
    ]
    counts = ws.progress_summary()
    assert counts[PageState.raw] == 1
    assert counts[PageState.cleaned] == 1
    assert counts[PageState.rendered] == 1
    assert counts[PageState.translated] == 0


def test_resolve_glossary_path_relative_and_absolute(tmp_path):
    ws = Workspace.create(tmp_path / "s", "S", "ja", "th")
    assert ws.resolve_glossary_path() == tmp_path / "s" / "glossary.toml"
    ws.glossary_path = str(tmp_path / "abs" / "g.toml")
    assert ws.resolve_glossary_path() == tmp_path / "abs" / "g.toml"
