"""
Glossary system for the Webtoon Translate & Cleaner.

A glossary is a per-series dictionary of terms (character names, recurring terms,
honorifics, and do-not-translate entries). It is stored as a standalone TOML file
that a workspace references, and is consumed solely by the translator. It is
applied either by injecting it into the LLM prompt, by deterministic
post-translation replacement, or both (see ``TranslatorConfig.glossary_mode``).

The glossary never leaks into the cleaning ``Profile`` or the global ``Config``;
it is owned entirely by the workspace that points at it.
"""

import re
import sys
from pathlib import Path

from attrs import define, field
from loguru import logger

from pcleaner import toml_utils as tu

# If using Python 3.10 or older, use the 3rd party StrEnum.
if sys.version_info < (3, 11):
    from strenum import StrEnum
else:
    from enum import StrEnum


SCHEMA_VERSION = 1


class TermType(StrEnum):
    """The role a glossary entry plays, which affects how it is presented to the model."""

    name = "name"
    term = "term"
    honorific = "honorific"
    do_not_translate = "do_not_translate"


def to_term_type(value: str) -> TermType:
    """
    Parse a string into a TermType, defaulting to ``term`` for unknown values.
    """
    try:
        return TermType(str(value).strip().lower())
    except ValueError:
        logger.warning(f"Unknown glossary term type '{value}', defaulting to 'term'.")
        return TermType.term


@define
class GlossaryEntry:
    """A single glossary term mapping a source term to a preferred target rendering."""

    source: str
    target: str
    type: TermType = TermType.term
    notes: str = ""
    case_sensitive: bool = False
    do_not_translate: bool = False

    def to_dict(self) -> dict:
        return {
            "source": self.source,
            "target": self.target,
            "type": str(self.type),
            "notes": self.notes,
            "case_sensitive": self.case_sensitive,
            "do_not_translate": self.do_not_translate,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "GlossaryEntry":
        term_type = to_term_type(data.get("type", "term"))
        # An explicit do_not_translate flag, or the dedicated type, both mark a term verbatim.
        do_not_translate = bool(data.get("do_not_translate", False)) or (
            term_type == TermType.do_not_translate
        )
        return cls(
            source=str(data.get("source", "")),
            target=str(data.get("target", "")),
            type=term_type,
            notes=str(data.get("notes", "")),
            case_sensitive=bool(data.get("case_sensitive", False)),
            do_not_translate=do_not_translate,
        )


@define
class Glossary:
    """
    A collection of glossary entries for a single series.

    Stored as a TOML file with a ``[meta]`` table and an array of ``[[terms]]``.
    """

    name: str = ""
    source_lang: str | None = None
    target_lang: str | None = None
    entries: list[GlossaryEntry] = field(factory=list)

    @classmethod
    def load(cls, path: Path) -> "Glossary":
        """
        Load a glossary from a TOML file. On failure, returns an empty glossary.
        """
        path = Path(path)
        try:
            data = tu.load_toml(path)
        except (OSError, ValueError):
            logger.exception(f"Failed to load glossary from {path}")
            return cls()

        meta = data.get("meta", {})
        entries = [GlossaryEntry.from_dict(entry) for entry in data.get("terms", [])]
        return cls(
            name=str(meta.get("name", "")),
            source_lang=meta.get("source_lang"),
            target_lang=meta.get("target_lang"),
            entries=entries,
        )

    def to_dict(self) -> dict:
        """Serialize to a TOML-compatible dictionary."""
        meta: dict = {"name": self.name, "version": SCHEMA_VERSION}
        if self.source_lang is not None:
            meta["source_lang"] = self.source_lang
        if self.target_lang is not None:
            meta["target_lang"] = self.target_lang
        return {
            "meta": meta,
            "terms": [entry.to_dict() for entry in self.entries],
        }

    def save(self, path: Path) -> bool:
        """
        Write the glossary to a TOML file atomically.

        :param path: The destination path.
        :return: True if written successfully.
        """
        return tu.safe_write_toml(self.to_dict(), Path(path))

    def add(self, entry: GlossaryEntry) -> None:
        """Add or replace an entry, keyed by its source term."""
        for index, existing in enumerate(self.entries):
            if existing.source == entry.source:
                self.entries[index] = entry
                return
        self.entries.append(entry)

    def remove(self, source: str) -> bool:
        """Remove the entry with the given source term. Returns True if one was removed."""
        for index, existing in enumerate(self.entries):
            if existing.source == source:
                del self.entries[index]
                return True
        return False

    def validate(self) -> list[str]:
        """
        Validate the glossary, returning a list of human-readable warnings.
        An empty list means the glossary is valid.
        """
        warnings: list[str] = []
        seen: set[str] = set()
        for entry in self.entries:
            if not entry.source.strip():
                warnings.append("An entry has an empty source term.")
                continue
            if entry.source in seen:
                warnings.append(f"Duplicate source term: '{entry.source}'.")
            seen.add(entry.source)
            # do-not-translate entries are allowed to have target == source (or empty).
            if not entry.do_not_translate and not entry.target.strip():
                warnings.append(f"Entry '{entry.source}' has an empty target translation.")
        return warnings

    def to_prompt_block(self, max_entries: int | None = None) -> str:
        """
        Render the glossary as a block of text to inject into the LLM system prompt.

        :param max_entries: Optionally cap the number of translatable entries listed,
            to keep the prompt within a reasonable size. Do-not-translate terms are
            always listed in full.
        :return: A formatted prompt block, or an empty string if there is nothing to add.
        """
        translatable = [e for e in self.entries if not e.do_not_translate and e.target.strip()]
        verbatim = [e for e in self.entries if e.do_not_translate]

        if max_entries is not None:
            translatable = translatable[:max_entries]

        lines: list[str] = []
        if translatable:
            lines.append("Glossary (use these exact translations):")
            for entry in translatable:
                note = ""
                if entry.type == TermType.name:
                    note = " (character name; keep consistent)"
                elif entry.type == TermType.honorific:
                    note = " (honorific)"
                elif entry.notes:
                    note = f" ({entry.notes})"
                lines.append(f"- {entry.source} -> {entry.target}{note}")

        if verbatim:
            terms = ", ".join(e.source for e in verbatim)
            lines.append(f"Do NOT translate (keep verbatim): {terms}")

        return "\n".join(lines)

    def apply_postprocess(self, text: str) -> str:
        """
        Apply deterministic post-translation replacement to a translated string.

        Replaces source terms with their target rendering. Do-not-translate terms are
        left untouched (they are forced verbatim via the prompt instead). Longer source
        terms are replaced first to avoid partial-overlap clobbering.

        :param text: The translated text to post-process.
        :return: The text with glossary replacements applied.
        """
        result = text
        replaceable = [
            e for e in self.entries if not e.do_not_translate and e.source.strip() and e.target
        ]
        for entry in sorted(replaceable, key=lambda e: len(e.source), reverse=True):
            flags = 0 if entry.case_sensitive else re.IGNORECASE
            result = re.sub(re.escape(entry.source), entry.target, result, flags=flags)
        return result
