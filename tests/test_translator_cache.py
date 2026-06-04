"""Tests for the translation cache helpers."""

from pathlib import Path

from pcleaner.translator import cache as tcache
from pcleaner.translator.structures import PageTranslation, TranslationResult


def test_sidecar_path_uses_stem():
    path = tcache.sidecar_path(Path("/out"), Path("/imgs/0001_page.png"))
    assert path == Path("/out/0001_page#translated.json")


def test_load_if_exists_missing_returns_none(tmp_path):
    assert tcache.load_if_exists(tmp_path / "nope.json") is None


def test_load_if_exists_roundtrip(tmp_path):
    page = PageTranslation(
        "/i.png", "ja", "th", [TranslationResult((0, 0, 1, 1), "src", "tgt")]
    )
    path = tmp_path / "001#translated.json"
    page.save(path)
    loaded = tcache.load_if_exists(path)
    assert loaded is not None
    assert loaded.results[0].target_text == "tgt"


def test_load_if_exists_corrupt_returns_none(tmp_path):
    path = tmp_path / "bad#translated.json"
    path.write_text("not valid json", encoding="utf-8")
    assert tcache.load_if_exists(path) is None
