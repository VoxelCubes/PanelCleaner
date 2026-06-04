"""Tests for translator config and result structures."""

import pytest

from pcleaner.translator.config import TranslatorConfig, GlossaryMode, to_glossary_mode
from pcleaner.translator.structures import (
    TranslationResult,
    PageTranslation,
    CostAccounting,
)


def test_to_glossary_mode_unknown_defaults():
    assert to_glossary_mode("prompt") == GlossaryMode.PROMPT
    assert to_glossary_mode("replace") == GlossaryMode.REPLACE
    assert to_glossary_mode("prompt+replace") == GlossaryMode.PROMPT_REPLACE
    assert to_glossary_mode("???") == GlossaryMode.PROMPT_REPLACE


def test_translator_config_roundtrip_and_fix():
    config = TranslatorConfig.from_dict(
        {
            "model": "openai/gpt-4o",
            "batch_size": 0,  # invalid -> clamped to 1
            "context_window": -3,  # invalid -> clamped to 0
            "temperature": 5.0,  # invalid -> clamped to 2.0
            "max_retries": -1,  # invalid -> clamped to 0
            "glossary_mode": "replace",
        }
    )
    assert config.model == "openai/gpt-4o"
    assert config.batch_size == 1
    assert config.context_window == 0
    assert config.temperature == 2.0
    assert config.max_retries == 0
    assert config.glossary_mode == GlossaryMode.REPLACE

    data = config.to_dict()
    again = TranslatorConfig.from_dict(data)
    assert again.to_dict() == data


def test_translator_config_defaults_on_empty_dict():
    config = TranslatorConfig.from_dict({})
    assert config.model
    assert config.batch_size >= 1
    assert config.glossary_mode == GlossaryMode.PROMPT_REPLACE


def test_translation_result_box_obj():
    # box_obj imports structures.Box, which pulls the full (heavy) dependency chain.
    # Skip gracefully if those optional deps are not installed in the test environment.
    pytest.importorskip("pcleaner.structures")
    result = TranslationResult(box=(1, 2, 3, 4), source_text="a", target_text="b")
    box = result.box_obj
    assert (box.x1, box.y1, box.x2, box.y2) == (1, 2, 3, 4)


def test_page_translation_json_roundtrip():
    page = PageTranslation(
        image_path="/img/001.png",
        source_lang="ja",
        target_lang="th",
        results=[
            TranslationResult(
                box=(0, 0, 10, 10),
                source_text="こんにちは",
                target_text="สวัสดี",
                model="m",
                glossary_applied=True,
                prompt_tokens=5,
                completion_tokens=7,
                cost_usd=0.001,
            )
        ],
    )
    restored = PageTranslation.from_json(page.to_json())
    assert restored.image_path == "/img/001.png"
    assert restored.source_lang == "ja"
    assert restored.target_lang == "th"
    assert len(restored.results) == 1
    r = restored.results[0]
    assert r.box == (0, 0, 10, 10)
    assert r.source_text == "こんにちは"
    assert r.target_text == "สวัสดี"
    assert r.prompt_tokens == 5
    assert restored.total_cost_usd == 0.001
    assert restored.total_tokens == 12


def test_page_translation_save_load(tmp_path):
    page = PageTranslation("/i.png", "ja", "th", [TranslationResult((0, 0, 1, 1), "x", "y")])
    path = tmp_path / "#translated.json"
    page.save(path)
    loaded = PageTranslation.load(path)
    assert loaded.results[0].target_text == "y"


def test_cost_accounting():
    acc = CostAccounting()
    acc.add(10, 20, 0.5)
    acc.add_result(TranslationResult((0, 0, 1, 1), "a", "b", prompt_tokens=5, completion_tokens=5, cost_usd=0.25))
    assert acc.prompt_tokens == 15
    assert acc.completion_tokens == 25
    assert acc.total_tokens == 40
    assert abs(acc.cost_usd - 0.75) < 1e-9
    assert acc.requests == 1
    assert "request" in acc.summary()
