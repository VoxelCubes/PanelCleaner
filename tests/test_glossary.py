"""Tests for the glossary data model (pcleaner/glossary.py)."""

from pcleaner.glossary import Glossary, GlossaryEntry, TermType, to_term_type


def make_glossary() -> Glossary:
    return Glossary(
        name="Test",
        source_lang="ja",
        target_lang="th",
        entries=[
            GlossaryEntry("ハルカ", "ฮารุกะ", TermType.name, notes="hero"),
            GlossaryEntry("先輩", "รุ่นพี่", TermType.honorific),
            GlossaryEntry("SFX", "SFX", TermType.do_not_translate, do_not_translate=True),
        ],
    )


def test_to_term_type_unknown_defaults_to_term():
    assert to_term_type("name") == TermType.name
    assert to_term_type("nonsense") == TermType.term


def test_save_load_roundtrip(tmp_path):
    glossary = make_glossary()
    path = tmp_path / "glossary.toml"
    assert glossary.save(path)

    loaded = Glossary.load(path)
    assert loaded.name == "Test"
    assert loaded.source_lang == "ja"
    assert loaded.target_lang == "th"
    assert len(loaded.entries) == 3
    haruka = loaded.entries[0]
    assert haruka.source == "ハルカ"
    assert haruka.target == "ฮารุกะ"
    assert haruka.type == TermType.name
    assert haruka.notes == "hero"
    # The do-not-translate type implies the flag on load.
    assert loaded.entries[2].do_not_translate is True


def test_add_replaces_existing_source():
    glossary = Glossary()
    glossary.add(GlossaryEntry("a", "b"))
    glossary.add(GlossaryEntry("a", "c"))
    assert len(glossary.entries) == 1
    assert glossary.entries[0].target == "c"


def test_remove():
    glossary = make_glossary()
    assert glossary.remove("先輩") is True
    assert glossary.remove("missing") is False
    assert all(e.source != "先輩" for e in glossary.entries)


def test_validate_detects_duplicates_and_empty():
    glossary = Glossary(
        entries=[
            GlossaryEntry("dup", "x"),
            GlossaryEntry("dup", "y"),
            GlossaryEntry("", "z"),
            GlossaryEntry("noempty", ""),
        ]
    )
    warnings = glossary.validate()
    assert any("Duplicate" in w for w in warnings)
    assert any("empty source" in w for w in warnings)
    assert any("empty target" in w for w in warnings)


def test_validate_allows_empty_target_for_do_not_translate():
    glossary = Glossary(
        entries=[GlossaryEntry("X", "", TermType.do_not_translate, do_not_translate=True)]
    )
    assert glossary.validate() == []


def test_to_prompt_block():
    block = make_glossary().to_prompt_block()
    assert "ハルカ -> ฮารุกะ" in block
    assert "character name" in block
    assert "honorific" in block
    assert "Do NOT translate" in block
    assert "SFX" in block


def test_to_prompt_block_empty():
    assert Glossary().to_prompt_block() == ""


def test_apply_postprocess_replaces_terms_not_dnt():
    glossary = make_glossary()
    result = glossary.apply_postprocess("ฉันเจอ ハルカ กับ 先輩 และ SFX")
    assert "ฮารุกะ" in result
    assert "รุ่นพี่" in result
    # Do-not-translate terms are left verbatim by post-processing.
    assert "SFX" in result


def test_apply_postprocess_longer_first():
    glossary = Glossary(entries=[GlossaryEntry("ab", "X"), GlossaryEntry("abc", "Y")])
    # "abc" must be replaced before "ab" to avoid partial clobbering.
    assert glossary.apply_postprocess("abc") == "Y"


def test_case_sensitivity():
    sensitive = Glossary(entries=[GlossaryEntry("Cat", "X", case_sensitive=True)])
    assert sensitive.apply_postprocess("cat Cat") == "cat X"
    insensitive = Glossary(entries=[GlossaryEntry("Cat", "X", case_sensitive=False)])
    assert insensitive.apply_postprocess("cat Cat") == "X X"
