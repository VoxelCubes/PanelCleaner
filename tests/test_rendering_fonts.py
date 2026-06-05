"""Tests for the font registry (resolution + loading)."""

from pcleaner.rendering.fonts import FontRegistry, BUNDLED_FALLBACK


def test_fallback_path_is_bundled():
    fr = FontRegistry()
    assert fr.fallback_path().name == BUNDLED_FALLBACK


def test_resolve_defaults_to_fallback_when_unknown():
    fr = FontRegistry(default_font="DefinitelyNotInstalledFont")
    assert fr.resolve("th").name == BUNDLED_FALLBACK


def test_resolve_matches_bundled_by_stem_prefix():
    # "LiberationSans" should match "LiberationSans-Regular.ttf".
    fr = FontRegistry(default_font="LiberationSans")
    assert fr.resolve(None).name == BUNDLED_FALLBACK


def test_resolve_matches_other_bundled_font():
    fr = FontRegistry(default_font="NotoMono")
    assert "NotoMono" in fr.resolve(None).name


def test_per_language_override_takes_precedence():
    fr = FontRegistry(default_font="LiberationSans", per_language={"ja": "NotoMono"})
    assert "NotoMono" in fr.resolve("ja").name
    # Other languages still use the default.
    assert fr.resolve("th").name == BUNDLED_FALLBACK


def test_resolve_explicit_path(tmp_path):
    fr = FontRegistry()
    # An existing file path is used directly.
    real = fr.fallback_path()
    fr2 = FontRegistry(default_font=str(real))
    assert fr2.resolve("en") == real


def test_load_returns_font_of_size():
    fr = FontRegistry()
    font = fr.load("th", 30)
    assert font.size == 30
    # Size is clamped to at least 1.
    assert fr.load("th", 0).size == 1


def test_resolve_is_cached():
    fr = FontRegistry(default_font="LiberationSans")
    first = fr.resolve("th")
    assert fr.resolve("th") is first
