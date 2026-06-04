"""Tests for translate_page orchestration with a fake client (no network)."""

import json

from pcleaner.glossary import Glossary, GlossaryEntry, TermType
from pcleaner.translator.config import TranslatorConfig, GlossaryMode
from pcleaner.translator.openrouter import ChatResponse, ChatUsage
from pcleaner.translator.batching import Bubble
from pcleaner.translator.structures import PageTranslation, TranslationResult, CostAccounting
from pcleaner.translator.translate import (
    TranslatePageData,
    translate_page,
    estimate_request_count,
    estimate_source_chars,
)


def resp(arr, prompt=8, completion=4, cost=0.004, model="m"):
    return ChatResponse(
        content=json.dumps(arr, ensure_ascii=False),
        usage=ChatUsage(prompt_tokens=prompt, completion_tokens=completion, cost_usd=cost, model=model),
    )


class FakeClient:
    """Returns queued ChatResponses and records the messages it was called with."""

    def __init__(self, responses):
        self.responses = list(responses)
        self.calls = []

    def chat(self, model, messages, temperature=0.3):
        self.calls.append((model, messages, temperature))
        return self.responses.pop(0)


def page(*texts):
    bubbles = [Bubble(i, (i, i, i + 1, i + 1), t) for i, t in enumerate(texts)]
    return TranslatePageData(image_path="/img/001.png", bubbles=bubbles)


def base_config(**kw):
    cfg = TranslatorConfig()
    cfg.batch_size = kw.get("batch_size", 100)
    cfg.include_context = kw.get("include_context", False)
    cfg.context_window = kw.get("context_window", 2)
    cfg.glossary_mode = kw.get("glossary_mode", GlossaryMode.PROMPT_REPLACE)
    return cfg


def test_basic_translation_single_batch():
    client = FakeClient([resp(["สวัสดี", "ลาก่อน"])])
    result = translate_page(
        page("こんにちは", "さようなら"),
        client=client,
        glossary=Glossary(),
        config=base_config(),
        source_lang="ja",
        target_lang="th",
    )
    assert isinstance(result, PageTranslation)
    assert result.source_lang == "ja" and result.target_lang == "th"
    assert [r.target_text for r in result.results] == ["สวัสดี", "ลาก่อน"]
    assert [r.source_text for r in result.results] == ["こんにちは", "さようなら"]
    assert len(client.calls) == 1


def test_batching_makes_multiple_calls():
    client = FakeClient([resp(["a", "b"]), resp(["c"])])
    result = translate_page(
        page("1", "2", "3"),
        client=client,
        glossary=Glossary(),
        config=base_config(batch_size=2),
        source_lang="ja",
        target_lang="th",
    )
    assert len(client.calls) == 2
    assert [r.target_text for r in result.results] == ["a", "b", "c"]


def test_cache_skips_translated_bubbles():
    existing = PageTranslation(
        "/img/001.png",
        "ja",
        "th",
        results=[TranslationResult(box=(0, 0, 1, 1), source_text="1", target_text="cached")],
    )
    client = FakeClient([resp(["new"])])
    result = translate_page(
        page("1", "2"),
        client=client,
        glossary=Glossary(),
        config=base_config(batch_size=10),
        source_lang="ja",
        target_lang="th",
        existing=existing,
    )
    # Only the uncached bubble (index 1) is sent.
    assert len(client.calls) == 1
    # Order preserved; cached result reused.
    assert [r.target_text for r in result.results] == ["cached", "new"]


def test_force_ignores_cache():
    existing = PageTranslation(
        "/img/001.png",
        "ja",
        "th",
        results=[TranslationResult(box=(0, 0, 1, 1), source_text="1", target_text="cached")],
    )
    client = FakeClient([resp(["fresh"])])
    result = translate_page(
        page("1"),
        client=client,
        glossary=Glossary(),
        config=base_config(),
        source_lang="ja",
        target_lang="th",
        existing=existing,
        force=True,
    )
    assert result.results[0].target_text == "fresh"


def test_glossary_prompt_mode_injects_block_no_replace():
    glossary = Glossary(entries=[GlossaryEntry("神", "เทพเจ้า", TermType.term)])
    client = FakeClient([resp(["神 อยู่ที่นี่"])])
    result = translate_page(
        page("x"),
        client=client,
        glossary=glossary,
        config=base_config(glossary_mode=GlossaryMode.PROMPT),
        source_lang="ja",
        target_lang="th",
    )
    system_msg = client.calls[0][1][0]["content"]
    assert "神 -> เทพเจ้า" in system_msg
    # prompt-only mode does NOT post-replace.
    assert result.results[0].target_text == "神 อยู่ที่นี่"


def test_glossary_replace_mode_applies_postprocess():
    glossary = Glossary(entries=[GlossaryEntry("神", "เทพเจ้า", TermType.term)])
    client = FakeClient([resp(["神 ปรากฏ"])])
    result = translate_page(
        page("x"),
        client=client,
        glossary=glossary,
        config=base_config(glossary_mode=GlossaryMode.REPLACE),
        source_lang="ja",
        target_lang="th",
    )
    # replace mode does not inject the glossary into the prompt...
    system_msg = client.calls[0][1][0]["content"]
    assert "神 -> เทพเจ้า" not in system_msg
    # ...but does post-replace the term in the output.
    assert result.results[0].target_text == "เทพเจ้า ปรากฏ"


def test_context_included_when_enabled():
    client = FakeClient([resp(["A"]), resp(["B"]), resp(["C"])])
    translate_page(
        page("first", "second", "third"),
        client=client,
        glossary=Glossary(),
        config=base_config(batch_size=1, include_context=True, context_window=1),
        source_lang="ja",
        target_lang="th",
    )
    # First batch is bubble 0; its following-context should include "second".
    user_msg = client.calls[0][1][1]["content"]
    assert "Following context" in user_msg
    assert "second" in user_msg


def test_accounting_accumulates_and_splits_usage():
    accounting = CostAccounting()
    client = FakeClient([resp(["a", "b"], prompt=10, completion=4, cost=0.01)])
    result = translate_page(
        page("1", "2"),
        client=client,
        glossary=Glossary(),
        config=base_config(),
        source_lang="ja",
        target_lang="th",
        accounting=accounting,
    )
    assert accounting.prompt_tokens == 10
    assert accounting.completion_tokens == 4
    assert abs(accounting.cost_usd - 0.01) < 1e-9
    assert accounting.requests == 1
    # Usage is split across the two bubbles (10 -> 5+5, 4 -> 2+2).
    assert [r.prompt_tokens for r in result.results] == [5, 5]
    assert [r.completion_tokens for r in result.results] == [2, 2]


def test_no_bubbles_no_calls():
    client = FakeClient([])
    result = translate_page(
        TranslatePageData("/img/001.png", []),
        client=client,
        glossary=Glossary(),
        config=base_config(),
        source_lang="ja",
        target_lang="th",
    )
    assert result.results == []
    assert client.calls == []


def test_estimators():
    data = page("aa", "bbb", "c")
    assert estimate_request_count(data, base_config(batch_size=2)) == 2
    assert estimate_source_chars(data) == 6
