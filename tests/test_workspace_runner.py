"""Tests for the workspace orchestration core (discovery, state machine, translate/render)."""

import json

from PIL import Image

from pcleaner import workspace_runner as wr
from pcleaner.workspace import Workspace, PageState, ChapterEntry, PageEntry
from pcleaner.glossary import Glossary
from pcleaner.translator.batching import Bubble
from pcleaner.translator.openrouter import ChatResponse, ChatUsage


class FakeClient:
    def __init__(self, responses):
        self.responses = list(responses)
        self.calls = []

    def chat(self, model, messages, temperature=0.3):
        self.calls.append((model, messages, temperature))
        return self.responses.pop(0)


def resp(arr):
    return ChatResponse(
        content=json.dumps(arr, ensure_ascii=False),
        usage=ChatUsage(prompt_tokens=4, completion_tokens=2, cost_usd=0.001, model="m"),
    )


def make_ws(tmp_path, chapter="ch001", pages=("001.png", "002.png")):
    ws = Workspace.create(tmp_path / "series", "Series", "ja", "th")
    ws.init_dirs()
    raw_dir = wr.chapter_subdir(ws, chapter, "raw")
    raw_dir.mkdir(parents=True, exist_ok=True)
    for name in pages:
        Image.new("RGB", (200, 100), "white").save(raw_dir / name)
    return ws


def test_stage_rank_and_at_least():
    assert wr.stage_rank(PageState.raw) == 0
    assert wr.stage_rank(PageState.rendered) == 3
    assert wr.at_least(PageState.translated, PageState.cleaned) is True
    assert wr.at_least(PageState.cleaned, PageState.translated) is False


def test_sync_manifest_adds_chapters_and_pages(tmp_path):
    ws = make_ws(tmp_path)
    added = wr.sync_manifest(ws)
    assert added == 2
    chapter = ws.get_chapter("ch001")
    assert chapter is not None
    assert {p.file for p in chapter.pages} == {"001.png", "002.png"}
    assert all(p.uuid for p in chapter.pages)
    # Idempotent: a second sync adds nothing and preserves state.
    chapter.pages[0].state = PageState.translated
    assert wr.sync_manifest(ws) == 0
    assert ws.get_chapter("ch001").pages[0].state == PageState.translated


def test_build_jobs_paths(tmp_path):
    ws = make_ws(tmp_path, pages=("001.png",))
    wr.sync_manifest(ws)
    jobs = wr.build_jobs(ws)
    assert len(jobs) == 1
    job = jobs[0]
    assert job.chapter_id == "ch001"
    assert job.file == "001.png"
    assert job.raw_path == wr.chapter_subdir(ws, "ch001", "raw") / "001.png"
    assert job.cleaned_path == wr.chapter_subdir(ws, "ch001", "cleaned") / "001.png"
    assert job.rendered_path == wr.chapter_subdir(ws, "ch001", "rendered") / "001.png"


def test_build_jobs_filter_chapter(tmp_path):
    ws = make_ws(tmp_path)
    # Add a second chapter on disk.
    raw2 = wr.chapter_subdir(ws, "ch002", "raw")
    raw2.mkdir(parents=True, exist_ok=True)
    Image.new("RGB", (10, 10), "white").save(raw2 / "001.png")
    wr.sync_manifest(ws)
    assert {j.chapter_id for j in wr.build_jobs(ws)} == {"ch001", "ch002"}
    assert {j.chapter_id for j in wr.build_jobs(ws, "ch002")} == {"ch002"}


def test_read_scale_from_clean_json(tmp_path):
    cache = tmp_path / "cache"
    cache.mkdir()
    (cache / "abcd_001#clean.json").write_text(json.dumps({"scale": 2.5}), encoding="utf-8")
    assert wr.read_scale_from_clean_json(cache, tmp_path / "001.png") == 2.5
    # Missing -> default 1.0.
    assert wr.read_scale_from_clean_json(cache, tmp_path / "999.png") == 1.0
    assert wr.read_scale_from_clean_json(tmp_path / "nope", tmp_path / "001.png") == 1.0


def test_translate_and_render_job(tmp_path):
    ws = make_ws(tmp_path, pages=("001.png",))
    wr.sync_manifest(ws)
    job = wr.build_jobs(ws)[0]

    client = FakeClient([resp(["สวัสดี"])])
    runner = wr.WorkspaceTranslateRender(
        ws=ws, glossary=Glossary(), fonts=wr.build_font_registry(ws), client=client
    )

    bubbles = [Bubble(0, (10, 10, 190, 90), "こんにちは")]
    assert runner.translate_job(job, bubbles) is True
    # Sidecar written and state advanced.
    sidecar = ws.cache_dir() / "001#translated.json"
    assert sidecar.is_file()
    assert ws.get_chapter("ch001").pages[0].state == PageState.translated

    # Render falls back to the raw image (no cleaned image present) and writes a PNG.
    assert runner.render_job(job, scale=1.0) is True
    assert job.rendered_path.is_file()
    assert ws.get_chapter("ch001").pages[0].state == PageState.rendered


def test_render_job_without_translation_returns_false(tmp_path):
    ws = make_ws(tmp_path, pages=("001.png",))
    wr.sync_manifest(ws)
    job = wr.build_jobs(ws)[0]
    runner = wr.WorkspaceTranslateRender(
        ws=ws, glossary=Glossary(), fonts=wr.build_font_registry(ws)
    )
    assert runner.render_job(job) is False


def test_translate_job_uses_cache(tmp_path):
    ws = make_ws(tmp_path, pages=("001.png",))
    wr.sync_manifest(ws)
    job = wr.build_jobs(ws)[0]
    bubbles = [Bubble(0, (0, 0, 10, 10), "A"), Bubble(1, (20, 20, 30, 30), "B")]

    runner1 = wr.WorkspaceTranslateRender(
        ws=ws, glossary=Glossary(), fonts=wr.build_font_registry(ws),
        client=FakeClient([resp(["a", "b"])]),
    )
    runner1.translate_job(job, bubbles)

    # Second run: only the first bubble's box changes text source -> the cached ones are
    # reused, so a single-bubble response suffices for the one new box.
    new_bubbles = [Bubble(0, (0, 0, 10, 10), "A"), Bubble(1, (20, 20, 30, 30), "B"),
                   Bubble(2, (40, 40, 50, 50), "C")]
    client2 = FakeClient([resp(["c"])])
    runner2 = wr.WorkspaceTranslateRender(
        ws=ws, glossary=Glossary(), fonts=wr.build_font_registry(ws), client=client2
    )
    runner2.translate_job(job, new_bubbles)
    # Only the new bubble "C" was sent to the client.
    assert len(client2.calls) == 1
    from pcleaner.translator.structures import PageTranslation
    page = PageTranslation.load(ws.cache_dir() / "001#translated.json")
    assert {r.target_text for r in page.results} == {"a", "b", "c"}
