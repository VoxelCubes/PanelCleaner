"""Tests for prompt construction and response parsing."""

from pcleaner.translator import prompt as pr


def test_build_system_prompt_includes_langs_and_glossary():
    out = pr.build_system_prompt("ja", "th", "Glossary:\n- A -> B")
    assert "ja" in out and "th" in out
    assert "Glossary:" in out
    assert "A -> B" in out


def test_build_system_prompt_without_glossary():
    out = pr.build_system_prompt("ja", "th", "")
    assert "ja" in out and "th" in out
    # No dangling glossary section.
    assert "Glossary" not in out


def test_build_system_prompt_custom_template():
    out = pr.build_system_prompt("ja", "th", "G", template="{source}->{target}{glossary}")
    assert out == "ja->th\nG"


def test_build_user_message_numbers_bubbles():
    msg = pr.build_user_message(["hello", "world"])
    assert "1. hello" in msg
    assert "2. world" in msg
    assert "exactly 2" in msg


def test_build_user_message_with_context():
    msg = pr.build_user_message(["mid"], context_before=["prev"], context_after=["next"])
    assert "Preceding context" in msg and "prev" in msg
    assert "Following context" in msg and "next" in msg
    assert "1. mid" in msg


def test_parse_plain_json_array():
    assert pr.parse_translation_response('["a", "b"]', 2) == ["a", "b"]


def test_parse_json_with_code_fence():
    content = "```json\n[\"x\", \"y\"]\n```"
    assert pr.parse_translation_response(content, 2) == ["x", "y"]


def test_parse_json_with_surrounding_prose():
    content = 'Sure! Here you go: ["one", "two"] Hope this helps.'
    assert pr.parse_translation_response(content, 2) == ["one", "two"]


def test_parse_pads_when_too_few():
    assert pr.parse_translation_response('["only"]', 3) == ["only", "", ""]


def test_parse_truncates_when_too_many():
    assert pr.parse_translation_response('["a","b","c"]', 2) == ["a", "b"]


def test_parse_fallback_numbered_lines():
    content = "1. first\n2. second\n3. third"
    assert pr.parse_translation_response(content, 3) == ["first", "second", "third"]


def test_parse_fallback_bullet_lines():
    content = "- alpha\n- beta"
    assert pr.parse_translation_response(content, 2) == ["alpha", "beta"]


def test_parse_handles_unicode():
    assert pr.parse_translation_response('["สวัสดี", "ลาก่อน"]', 2) == ["สวัสดี", "ลาก่อน"]
