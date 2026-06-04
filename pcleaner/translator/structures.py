"""
Data models for translation results, cached as the ``#translated.json`` sidecar.

These mirror the JSON serialization style of ``structures.PageData``: boxes are stored
as ``(x1, y1, x2, y2)`` tuples. The geometry in ``#clean.json`` (PageData) remains the
canonical source of truth; the box stored here is a redundant convenience so the
renderer can match a translation to its bubble without re-deriving geometry.

To keep this module lightweight (importable without PIL/torch), the box is stored as a
plain tuple. Use :meth:`TranslationResult.box_obj` to get a ``structures.Box`` when needed.
"""

import json
from pathlib import Path

from attrs import define, field, frozen

BoxTuple = tuple[int, int, int, int]


@frozen
class TranslationResult:
    """The translation of a single bubble, plus its model/usage accounting."""

    box: BoxTuple
    source_text: str
    target_text: str
    model: str = ""
    glossary_applied: bool = False
    prompt_tokens: int = 0
    completion_tokens: int = 0
    cost_usd: float = 0.0

    @property
    def box_obj(self):
        """Return the box as a ``structures.Box`` (imported lazily to stay lightweight)."""
        from pcleaner.structures import Box

        return Box(*self.box)

    def to_dict(self) -> dict:
        return {
            "box": list(self.box),
            "source_text": self.source_text,
            "target_text": self.target_text,
            "model": self.model,
            "glossary_applied": self.glossary_applied,
            "prompt_tokens": self.prompt_tokens,
            "completion_tokens": self.completion_tokens,
            "cost_usd": self.cost_usd,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "TranslationResult":
        return cls(
            box=tuple(data["box"]),  # type: ignore[arg-type]
            source_text=data.get("source_text", ""),
            target_text=data.get("target_text", ""),
            model=data.get("model", ""),
            glossary_applied=bool(data.get("glossary_applied", False)),
            prompt_tokens=int(data.get("prompt_tokens", 0)),
            completion_tokens=int(data.get("completion_tokens", 0)),
            cost_usd=float(data.get("cost_usd", 0.0)),
        )


@define
class PageTranslation:
    """All translations for a single page, serialized to ``#translated.json``."""

    image_path: str
    source_lang: str
    target_lang: str
    results: list[TranslationResult] = field(factory=list)

    @property
    def total_cost_usd(self) -> float:
        return sum(r.cost_usd for r in self.results)

    @property
    def total_tokens(self) -> int:
        return sum(r.prompt_tokens + r.completion_tokens for r in self.results)

    def to_json(self) -> str:
        data = {
            "image_path": self.image_path,
            "source_lang": self.source_lang,
            "target_lang": self.target_lang,
            "total_cost_usd": self.total_cost_usd,
            "results": [r.to_dict() for r in self.results],
        }
        return json.dumps(data, indent=4, ensure_ascii=False)

    @classmethod
    def from_json(cls, json_str: str) -> "PageTranslation":
        data = json.loads(json_str)
        return cls(
            image_path=data["image_path"],
            source_lang=data["source_lang"],
            target_lang=data["target_lang"],
            results=[TranslationResult.from_dict(r) for r in data.get("results", [])],
        )

    @classmethod
    def load(cls, path: Path) -> "PageTranslation":
        return cls.from_json(Path(path).read_text(encoding="utf-8"))

    def save(self, path: Path) -> None:
        Path(path).write_text(self.to_json(), encoding="utf-8")


@define
class CostAccounting:
    """Accumulates token usage and cost across a translation run."""

    prompt_tokens: int = 0
    completion_tokens: int = 0
    cost_usd: float = 0.0
    requests: int = 0

    def add(self, prompt_tokens: int, completion_tokens: int, cost_usd: float) -> None:
        self.prompt_tokens += prompt_tokens
        self.completion_tokens += completion_tokens
        self.cost_usd += cost_usd
        self.requests += 1

    def add_result(self, result: TranslationResult) -> None:
        self.prompt_tokens += result.prompt_tokens
        self.completion_tokens += result.completion_tokens
        self.cost_usd += result.cost_usd

    @property
    def total_tokens(self) -> int:
        return self.prompt_tokens + self.completion_tokens

    def summary(self) -> str:
        return (
            f"Translation usage: {self.requests} request(s), "
            f"{self.prompt_tokens} prompt + {self.completion_tokens} completion tokens "
            f"({self.total_tokens} total), estimated cost ${self.cost_usd:.4f}"
        )
