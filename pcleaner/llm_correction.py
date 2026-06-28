"""Smart OCR post-correction using a large language model via airllm.

airllm performs layer-wise disk offloading so very large models (e.g. Llama-3-70B)
can run on a few GB of RAM, at the cost of slow token generation. Because generation
is slow, the OCR text from many bubbles is batched into a single prompt and the model
is asked to return a JSON list of corrected snippets in one pass.

This is an optional feature. Install the extra with::

    pip install pcleaner[llm]

and enable it with the ``--use-llm`` flag on the ``pcleaner ocr`` command (or by setting
``llm_enabled = True`` in the profile's ``[LLM]`` section).
"""

import json
import re
from typing import Sequence

from loguru import logger
from tqdm import tqdm

import pcleaner.structures as st

# Marker the model is told to place around the JSON list so we can locate it
# reliably even when the model adds chatter around it.
_JSON_FENCE = "```"
_SYSTEM_PROMPT = (
    "You are an OCR post-correction engine for manga and comic speech bubbles. "
    "You receive a JSON array of raw OCR strings, in reading order. Fix obvious OCR "
    "errors: misread characters, broken/garbled text, stray punctuation, and missing or "
    "duplicate characters, while preserving the original language, meaning, numbers, and "
    "spacing. Do not translate. Do not add commentary. If a string is already correct or "
    "unintelligible, return it unchanged. Output ONLY a JSON array of the same length and "
    "order as the input."
)


def _import_airllm():
    """Lazily import airllm so the rest of the program works without the [llm] extra."""
    try:
        from airllm import AutoModel  # type: ignore
    except ImportError as exc:
        raise ImportError(
            "airllm is not installed. Install the optional LLM extra with: "
            "pip install pcleaner[llm]"
        ) from exc
    return AutoModel


class LLMCorrector:
    """Loads an airllm model once and corrects batches of OCR text.

    airllm generation is slow (layer-wise disk offloading), so callers should batch
    many bubbles into one :meth:`correct_texts` call rather than one per bubble.
    """

    def __init__(
        self,
        model_name: str,
        *,
        max_new_tokens: int = 1024,
        max_bubbles_per_prompt: int = 40,
        compression: str | None = None,
        hf_token: str | None = None,
    ) -> None:
        self.model_name = model_name
        self.max_new_tokens = max_new_tokens
        self.max_bubbles_per_prompt = max(1, max_bubbles_per_prompt)
        self.compression = compression
        self.hf_token = hf_token

        AutoModel = _import_airllm()
        logger.info(f"Loading airllm model '{model_name}' (this may take a while)...")
        kwargs = {}
        if compression:
            kwargs["compression"] = compression
        if hf_token:
            kwargs["hf_token"] = hf_token
        self.model = AutoModel.from_pretrained(model_name, **kwargs)
        logger.info("airllm model loaded.")

    def correct_texts(self, texts: Sequence[str]) -> list[str]:
        """Correct a list of OCR strings, returning a list of the same length.

        Bubbles are processed in chunks of ``max_bubbles_per_prompt``. On any error
        for a chunk, the original strings are returned unchanged for that chunk,
        so a single bad batch never aborts the whole run.
        """
        results: list[str] = list(texts)
        for start in range(0, len(texts), self.max_bubbles_per_prompt):
            chunk = list(texts[start : start + self.max_bubbles_per_prompt])
            if not any(text.strip() for text in chunk):
                # Skip purely-empty batches; nothing to correct.
                continue
            try:
                corrected = self._correct_chunk(chunk)
            except Exception:
                logger.exception(
                    f"LLM correction failed for bubbles {start}-{start + len(chunk)}; "
                    "keeping original OCR output."
                )
                continue
            # Guard against the model returning the wrong number of items.
            if len(corrected) == len(chunk):
                results[start : start + len(chunk)] = corrected
            else:
                logger.warning(
                    f"LLM returned {len(corrected)} corrections for {len(chunk)} bubbles; "
                    "keeping original OCR output for this batch."
                )
        return results

    def _correct_chunk(self, chunk: list[str]) -> list[str]:
        prompt = self._build_prompt(chunk)
        raw_output = self._generate(prompt)
        return self._parse(raw_output, chunk)

    def _build_prompt(self, chunk: list[str]) -> str:
        payload = json.dumps(chunk, ensure_ascii=False)
        return (
            f"{_SYSTEM_PROMPT}\n\n"
            f"Input JSON array:\n{payload}\n\n"
            f"Output the corrected JSON array wrapped in {_JSON_FENCE} fences."
        )

    def _generate(self, prompt: str) -> str:
        tokenizer = self.model.tokenizer

        # Prefer the model's chat template for instruct models (e.g. Llama-3-Instruct).
        input_text = self._apply_chat_template(prompt)

        input_tokens = tokenizer(
            [input_text],
            return_tensors="pt",
            return_attention_mask=False,
            truncation=True,
            padding=False,
        )
        input_ids = input_tokens["input_ids"]
        if hasattr(input_ids, "cuda"):
            input_ids = input_ids.cuda()

        generation_output = self.model.generate(
            input_ids,
            max_new_tokens=self.max_new_tokens,
            use_cache=True,
            return_dict_in_generate=True,
        )
        # Strip the prompt tokens, then decode only the newly generated part.
        prompt_len = input_ids.shape[-1]
        new_tokens = generation_output.sequences[0][prompt_len:]
        return tokenizer.decode(new_tokens, skip_special_tokens=True)

    def _apply_chat_template(self, prompt: str) -> str:
        tokenizer = self.model.tokenizer
        apply = getattr(tokenizer, "apply_chat_template", None)
        if callable(apply):
            try:
                messages = [
                    {"role": "system", "content": _SYSTEM_PROMPT},
                    {"role": "user", "content": prompt[len(_SYSTEM_PROMPT) :].lstrip()},
                ]
                templated = apply(messages, tokenize=False, add_generation_prompt=True)
                if isinstance(templated, str) and templated.strip():
                    return templated
            except Exception:
                logger.debug("Chat template not applicable; falling back to raw prompt.")
        return prompt

    @staticmethod
    def _parse(raw_output: str, original: list[str]) -> list[str]:
        """Extract the JSON array of corrections from the model output.

        Tolerates code fences and surrounding chatter. Always returns a list
        whose length matches ``original`` on success; mismatches bubble up to
        the caller (which keeps the originals).
        """
        text = raw_output.strip()

        # Strip ```json ... ``` or ``` ... ``` fences if present.
        fence_match = re.search(r"```(?:json)?\s*(.*?)```", text, re.DOTALL)
        if fence_match:
            text = fence_match.group(1).strip()

        # Find the outermost JSON array if there's chatter around it.
        array_match = re.search(r"\[.*\]", text, re.DOTALL)
        if array_match:
            text = array_match.group(0)

        parsed = json.loads(text)
        if not isinstance(parsed, list):
            raise ValueError("LLM did not return a JSON array.")
        # Coerce every item to a string (in case the model emitted bare numbers/bools).
        return ["" if item is None else str(item) for item in parsed]


def correct_ocr_analytics(
    ocr_analytics: list[st.OCRAnalytic],
    corrector: LLMCorrector,
) -> list[st.OCRAnalytic]:
    """Run LLM correction over the OCR analytics, returning new analytics.

    The box coordinates and other analytics are preserved; only the OCR text in
    ``removed_box_data`` is replaced with the corrected version. The input list
    is not modified (``OCRAnalytic`` is frozen).
    """
    corrected_analytics: list[st.OCRAnalytic] = []
    for analytic in tqdm(ocr_analytics, desc="LLM correcting OCR"):
        texts = [text for text, _ in analytic.removed_box_data]
        boxes = [box for _, box in analytic.removed_box_data]
        if not texts:
            corrected_analytics.append(analytic)
            continue
        corrected_texts = corrector.correct_texts(texts)
        corrected_box_data = list(zip(corrected_texts, boxes))
        corrected_analytics.append(
            st.OCRAnalytic(
                path=analytic.path,
                num_boxes=analytic.num_boxes,
                box_sizes_ocr=analytic.box_sizes_ocr,
                box_sizes_removed=analytic.box_sizes_removed,
                removed_box_data=corrected_box_data,
            )
        )
    return corrected_analytics
