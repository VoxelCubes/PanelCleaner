"""
Translation orchestration.

``translate_page`` ties together the OpenRouter client, prompt construction, batching,
the glossary and the translation cache to translate one page's worth of bubbles. It
mirrors the shape of ``masker.mask_page`` / ``denoiser.denoise_page``: a data struct in,
a ``PageTranslation`` sidecar out.

The client is injected as a small Protocol so the orchestration is fully testable with a
fake client (no network).
"""

from typing import Protocol

from attrs import define, field
from loguru import logger

from pcleaner.glossary import Glossary
from pcleaner.translator import prompt as pr
from pcleaner.translator.batching import Bubble, make_batches, context_for_batch
from pcleaner.translator.config import TranslatorConfig, GlossaryMode
from pcleaner.translator.openrouter import ChatResponse
from pcleaner.translator.structures import (
    TranslationResult,
    PageTranslation,
    CostAccounting,
)


class TranslatorClient(Protocol):
    """The minimal client interface needed for translation (see OpenRouterClient)."""

    def chat(
        self, model: str, messages: list[dict[str, str]], temperature: float = 0.3
    ) -> ChatResponse: ...


@define
class TranslatePageData:
    """The input for translating one page: the source bubbles in reading order."""

    image_path: str
    bubbles: list[Bubble] = field(factory=list)


def _uses_prompt(mode: GlossaryMode) -> bool:
    return mode in (GlossaryMode.PROMPT, GlossaryMode.PROMPT_REPLACE)


def _uses_replace(mode: GlossaryMode) -> bool:
    return mode in (GlossaryMode.REPLACE, GlossaryMode.PROMPT_REPLACE)


def _split_usage(total: int, parts: int) -> list[int]:
    """Distribute an integer token count as evenly as possible across ``parts`` items."""
    if parts <= 0:
        return []
    base, remainder = divmod(total, parts)
    return [base + (1 if i < remainder else 0) for i in range(parts)]


def estimate_request_count(data: TranslatePageData, config: TranslatorConfig) -> int:
    """Estimate the number of API requests a page would take (for ``--dry-run``)."""
    return len(make_batches(data.bubbles, config.batch_size))


def estimate_source_chars(data: TranslatePageData) -> int:
    """Total number of source characters on a page (a rough cost proxy for ``--dry-run``)."""
    return sum(len(b.text) for b in data.bubbles)


def translate_page(
    data: TranslatePageData,
    *,
    client: TranslatorClient,
    glossary: Glossary,
    config: TranslatorConfig,
    source_lang: str,
    target_lang: str,
    model: str | None = None,
    existing: PageTranslation | None = None,
    force: bool = False,
    accounting: CostAccounting | None = None,
    system_template: str | None = None,
) -> PageTranslation:
    """
    Translate all bubbles on a page, reusing cached translations where possible.

    :param data: The page's source bubbles in reading order.
    :param client: The translation client (injected; e.g. OpenRouterClient).
    :param glossary: The glossary to apply (prompt and/or post-replacement).
    :param config: The translator configuration.
    :param source_lang: Source language code/name.
    :param target_lang: Target language code/name.
    :param model: Optional model override (defaults to ``config.model``).
    :param existing: A previously cached PageTranslation, to skip already-done bubbles.
    :param force: When True, ignore the cache and retranslate everything.
    :param accounting: Optional cost accumulator updated in place.
    :param system_template: Optional system-prompt template override.
    :return: The full PageTranslation for the page.
    """
    used_model = model or config.model

    # Build the cache map of already-translated bubbles, keyed by box geometry.
    cached: dict[tuple, TranslationResult] = {}
    if existing is not None and not force:
        cached = {r.box: r for r in existing.results}

    to_translate = [b for b in data.bubbles if b.box not in cached]

    glossary_block = ""
    if _uses_prompt(config.glossary_mode):
        glossary_block = glossary.to_prompt_block()
    system_prompt = pr.build_system_prompt(
        source_lang, target_lang, glossary_block, system_template
    )

    results_by_box: dict[tuple, TranslationResult] = dict(cached)

    for batch in make_batches(to_translate, config.batch_size):
        before, after = ([], [])
        if config.include_context:
            before, after = context_for_batch(data.bubbles, batch, config.context_window)
        user_message = pr.build_user_message([b.text for b in batch], before, after)
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message},
        ]

        response = client.chat(used_model, messages, config.temperature)
        targets = pr.parse_translation_response(response.content, len(batch))

        # Distribute the batch's usage across its bubbles for per-result accounting.
        prompt_split = _split_usage(response.usage.prompt_tokens, len(batch))
        completion_split = _split_usage(response.usage.completion_tokens, len(batch))
        cost_split = response.usage.cost_usd / len(batch) if batch else 0.0

        for i, (bubble, target) in enumerate(zip(batch, targets)):
            glossary_applied = False
            if _uses_replace(config.glossary_mode):
                replaced = glossary.apply_postprocess(target)
                glossary_applied = replaced != target or _uses_prompt(config.glossary_mode)
                target = replaced
            elif _uses_prompt(config.glossary_mode) and glossary_block:
                glossary_applied = True

            results_by_box[bubble.box] = TranslationResult(
                box=bubble.box,
                source_text=bubble.text,
                target_text=target,
                model=response.usage.model or used_model,
                glossary_applied=glossary_applied,
                prompt_tokens=prompt_split[i],
                completion_tokens=completion_split[i],
                cost_usd=cost_split,
            )

        if accounting is not None:
            accounting.add(
                response.usage.prompt_tokens,
                response.usage.completion_tokens,
                response.usage.cost_usd,
            )

    # Emit results in the original reading order.
    ordered = [results_by_box[b.box] for b in data.bubbles if b.box in results_by_box]
    logger.debug(
        f"Translated page {data.image_path}: {len(to_translate)} new, "
        f"{len(cached)} cached, {len(ordered)} total."
    )
    return PageTranslation(
        image_path=data.image_path,
        source_lang=source_lang,
        target_lang=target_lang,
        results=ordered,
    )
