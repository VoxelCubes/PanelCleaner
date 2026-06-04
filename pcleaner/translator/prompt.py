"""
Prompt construction and response parsing for LLM translation.

The model is asked to translate a numbered list of speech bubbles and to reply with a
JSON array of strings, one per bubble, preserving order. Surrounding bubbles can be
supplied as read-only context so dialogue stays coherent across a batch.

All functions here are pure and side-effect free, so they are easy to unit-test.
"""

import json

# Default system prompt template. ``{source}``, ``{target}`` and ``{glossary}`` are filled in.
DEFAULT_SYSTEM_TEMPLATE = """\
You are a professional comic/manga/webtoon translator.
Translate the numbered speech bubbles from {source} into {target}.

Rules:
- Translate naturally and fluently for {target} readers; do not translate word-for-word.
- Preserve the meaning, tone and any emphasis of each bubble.
- Keep each translation as a single bubble; do not merge or split bubbles.
- Do not add notes, explanations or romanization.
- Reply ONLY with a JSON array of strings, one entry per numbered bubble, in order.
{glossary}"""


def build_system_prompt(
    source_lang: str,
    target_lang: str,
    glossary_block: str = "",
    template: str | None = None,
) -> str:
    """
    Build the system prompt for a translation request.

    :param source_lang: The source language (code or name).
    :param target_lang: The target language (code or name).
    :param glossary_block: An optional glossary block to inject (may be empty).
    :param template: An optional override template. Must contain ``{source}``,
        ``{target}`` and ``{glossary}`` placeholders.
    :return: The formatted system prompt.
    """
    tmpl = template if template is not None else DEFAULT_SYSTEM_TEMPLATE
    glossary_section = f"\n{glossary_block}" if glossary_block.strip() else ""
    return tmpl.format(source=source_lang, target=target_lang, glossary=glossary_section)


def build_user_message(
    batch_texts: list[str],
    context_before: list[str] | None = None,
    context_after: list[str] | None = None,
) -> str:
    """
    Build the user message listing the bubbles to translate, with optional context.

    :param batch_texts: The source texts of the bubbles to translate, in order.
    :param context_before: Optional preceding bubbles (read-only context).
    :param context_after: Optional following bubbles (read-only context).
    :return: The formatted user message.
    """
    parts: list[str] = []
    if context_before:
        preceding = "\n".join(f"- {text}" for text in context_before)
        parts.append("Preceding context (do NOT translate, for reference only):\n" + preceding)
    if context_after:
        following = "\n".join(f"- {text}" for text in context_after)
        parts.append("Following context (do NOT translate, for reference only):\n" + following)

    numbered = "\n".join(f"{i}. {text}" for i, text in enumerate(batch_texts, start=1))
    parts.append("Translate these bubbles:\n" + numbered)
    parts.append(
        f"Reply with a JSON array of exactly {len(batch_texts)} string(s), in the same order."
    )
    return "\n\n".join(parts)


def parse_translation_response(content: str, expected: int) -> list[str]:
    """
    Parse the model's reply into a list of translated strings.

    Tries to parse a JSON array first (tolerating Markdown code fences). Falls back to
    splitting numbered or plain lines if the model did not return valid JSON. The result
    is always padded or truncated to ``expected`` length so it lines up with the batch.

    :param content: The raw assistant content.
    :param expected: The number of bubbles that were requested.
    :return: A list of exactly ``expected`` strings.
    """
    parsed = _try_parse_json_array(content)
    if parsed is None:
        parsed = _parse_lines(content)

    # Normalize length so results align with the batch indices.
    if len(parsed) < expected:
        parsed = parsed + [""] * (expected - len(parsed))
    elif len(parsed) > expected:
        parsed = parsed[:expected]
    return [str(item) for item in parsed]


def _strip_code_fences(content: str) -> str:
    text = content.strip()
    if text.startswith("```"):
        # Drop the opening fence line (``` or ```json) and the trailing fence.
        lines = text.splitlines()
        if lines and lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip().startswith("```"):
            lines = lines[:-1]
        text = "\n".join(lines).strip()
    return text


def _try_parse_json_array(content: str) -> list | None:
    text = _strip_code_fences(content)
    # Narrow to the outermost array if there is surrounding prose.
    start = text.find("[")
    end = text.rfind("]")
    if start != -1 and end != -1 and end > start:
        candidate = text[start : end + 1]
    else:
        candidate = text
    try:
        data = json.loads(candidate)
    except (json.JSONDecodeError, ValueError):
        return None
    if isinstance(data, list):
        return data
    return None


def _parse_lines(content: str) -> list[str]:
    """Fallback: split into non-empty lines, stripping common numbering like ``1.`` / ``-``."""
    import re

    results: list[str] = []
    for raw in content.splitlines():
        line = raw.strip()
        if not line or line.startswith("```"):
            continue
        line = re.sub(r"^\s*\d+[.)]\s*", "", line)
        line = re.sub(r"^\s*[-*]\s*", "", line)
        results.append(line)
    return results
