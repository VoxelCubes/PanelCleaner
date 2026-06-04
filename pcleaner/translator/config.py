"""
Translator configuration.

``TranslatorConfig`` is owned by a workspace and serialized into the ``[translator]``
table of ``workspace.toml``. It holds the settings for LLM-based translation via
OpenRouter: model, batching, context, glossary application mode and retry behaviour.

The OpenRouter API key is deliberately NOT stored here. It lives in the global
``Config`` or the ``OPENROUTER_API_KEY`` environment variable, so a workspace manifest
is safe to share and commit.
"""

import sys

from attrs import define
from loguru import logger

# If using Python 3.10 or older, use the 3rd party StrEnum.
if sys.version_info < (3, 11):
    from strenum import StrEnum
else:
    from enum import StrEnum


class GlossaryMode(StrEnum):
    """How the glossary is applied during translation."""

    PROMPT = "prompt"
    REPLACE = "replace"
    PROMPT_REPLACE = "prompt+replace"


def to_glossary_mode(value: str) -> GlossaryMode:
    """Parse a string into a GlossaryMode, defaulting to ``prompt+replace``."""
    try:
        return GlossaryMode(str(value).strip().lower())
    except ValueError:
        logger.warning(f"Unknown glossary mode '{value}', defaulting to 'prompt+replace'.")
        return GlossaryMode.PROMPT_REPLACE


# A sensible default model available on OpenRouter.
DEFAULT_MODEL = "anthropic/claude-3.5-sonnet"


@define
class TranslatorConfig:
    """Settings for the translation step, stored per workspace."""

    model: str = DEFAULT_MODEL
    batch_size: int = 12
    include_context: bool = True
    context_window: int = 2
    glossary_mode: GlossaryMode = GlossaryMode.PROMPT_REPLACE
    temperature: float = 0.3
    max_retries: int = 4

    def fix(self) -> None:
        """Clamp values into valid ranges, following the convention used by Profile configs."""
        if not str(self.model).strip():
            self.model = DEFAULT_MODEL
        self.batch_size = max(1, int(self.batch_size))
        self.context_window = max(0, int(self.context_window))
        self.temperature = min(2.0, max(0.0, float(self.temperature)))
        self.max_retries = max(0, int(self.max_retries))
        if not isinstance(self.glossary_mode, GlossaryMode):
            self.glossary_mode = to_glossary_mode(self.glossary_mode)

    def to_dict(self) -> dict:
        """Serialize to a TOML-compatible dictionary."""
        return {
            "model": self.model,
            "batch_size": self.batch_size,
            "include_context": self.include_context,
            "context_window": self.context_window,
            "glossary_mode": str(self.glossary_mode),
            "temperature": self.temperature,
            "max_retries": self.max_retries,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "TranslatorConfig":
        """Build a TranslatorConfig from a (possibly partial) dictionary."""
        config = cls()
        if "model" in data:
            config.model = str(data["model"])
        if "batch_size" in data:
            config.batch_size = int(data["batch_size"])
        if "include_context" in data:
            config.include_context = bool(data["include_context"])
        if "context_window" in data:
            config.context_window = int(data["context_window"])
        if "glossary_mode" in data:
            config.glossary_mode = to_glossary_mode(data["glossary_mode"])
        if "temperature" in data:
            config.temperature = float(data["temperature"])
        if "max_retries" in data:
            config.max_retries = int(data["max_retries"])
        config.fix()
        return config
