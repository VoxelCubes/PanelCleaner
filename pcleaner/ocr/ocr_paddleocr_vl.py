"""
PaddleOCR-VL OCR engine.

This wraps the PaddleOCR-VL-1.5 vision-language model hosted on Hugging Face
(https://huggingface.co/PaddlePaddle/PaddleOCR-VL-1.5) as a regular OCR engine,
following the same singleton/lazy-loading pattern as the manga-ocr and tesseract
engines.

The model is heavy (~0.9B parameters) and requires ``transformers>=5.0.0``,
which is NOT part of Panel Cleaner's base dependencies. To avoid forcing that
major upgrade onto every install (it can conflict with the manga-ocr engine),
the transformers/torch imports are deferred into ``initialize_model`` and the
engine advertises its availability through :func:`is_available`. Install the
optional extra to use it::

    pip install "pcleaner[paddleocr-vl]"
"""

from pathlib import Path

from loguru import logger
from PIL import Image

import pcleaner.ocr.supported_languages as osl


# The Hugging Face repository id for the model.
MODEL_ID = "PaddlePaddle/PaddleOCR-VL-1.5"

# The minimum transformers version that ships the PaddleOCR-VL model classes.
_MIN_TRANSFORMERS_VERSION = (5, 0, 0)

# The prompt used to put the model into plain text-recognition (OCR) mode.
_OCR_PROMPT = "OCR:"


def is_available() -> bool:
    """
    Check whether the optional dependencies for PaddleOCR-VL are installed.

    This requires ``transformers>=5.0.0``, which is only pulled in by the
    ``paddleocr-vl`` extra. Importing this module never fails on its own; callers
    should gate usage of the engine behind this check.

    :return: True if PaddleOCR-VL can be loaded.
    """
    try:
        import transformers
    except ImportError:
        return False

    version_str = getattr(transformers, "__version__", "0")
    try:
        parts = tuple(int(p) for p in version_str.split(".")[:3])
        # Pad to length 3 so the comparison is well-defined.
        parts = parts + (0,) * (3 - len(parts))
        return parts >= _MIN_TRANSFORMERS_VERSION
    except (ValueError, TypeError):
        logger.warning(f"Could not parse transformers version: {version_str!r}")
        return False


class PaddleOcrVL:
    _instance = None
    _model = None
    _processor = None
    _device = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            logger.info("Creating the PaddleOcrVL instance")
            cls._instance = super(PaddleOcrVL, cls).__new__(cls)
            cls._instance._model = None
            cls._instance._processor = None
            cls._instance._device = None
        return cls._instance

    def __init__(self, *args, **kwargs):
        # Initialization logic is deferred to initialize_model.
        pass

    @staticmethod
    def langs() -> set[osl.LanguageCode]:
        """
        The languages PaddleOCR-VL handles well. The model is broadly
        multilingual; this is a conservative curated subset of the language
        codes Panel Cleaner knows about.
        """
        return {
            osl.LanguageCode.jpn,
            osl.LanguageCode.eng,
            osl.LanguageCode.kor,
            osl.LanguageCode.chi_sim,
            osl.LanguageCode.chi_tra,
            osl.LanguageCode.fra,
            osl.LanguageCode.deu,
            osl.LanguageCode.spa,
            osl.LanguageCode.ita,
            osl.LanguageCode.por,
            osl.LanguageCode.rus,
            osl.LanguageCode.nld,
            osl.LanguageCode.ara,
        }

    def initialize_model(self) -> None:
        if self._model is not None:
            return

        if not is_available():
            raise RuntimeError(
                "PaddleOCR-VL requires the optional dependency 'transformers>=5.0.0'.\n"
                "Install it with: pip install 'pcleaner[paddleocr-vl]'"
            )

        import torch
        from transformers import AutoModelForImageTextToText, AutoProcessor

        # Reuse the same device-selection logic as the text detector.
        if torch.cuda.is_available():
            device = "cuda"
        elif torch.backends.mps.is_available():
            device = "mps"
        else:
            device = "cpu"
        dtype = torch.float32 if device == "cpu" else torch.float16

        logger.info(f"Loading PaddleOCR-VL model on device: {device}")
        self._processor = AutoProcessor.from_pretrained(MODEL_ID, trust_remote_code=True)
        self._model = (
            AutoModelForImageTextToText.from_pretrained(
                MODEL_ID, dtype=dtype, trust_remote_code=True
            )
            .to(device)
            .eval()
        )
        self._device = device

    @staticmethod
    def _load_image(img_or_path: Image.Image | Path | str) -> Image.Image:
        if isinstance(img_or_path, (str, Path)):
            return Image.open(img_or_path).convert("RGB")
        elif isinstance(img_or_path, Image.Image):
            return img_or_path.convert("RGB")
        raise ValueError(f"img_or_path must be a path or PIL.Image, got: {type(img_or_path)}")

    def __call__(self, img_or_path: Image.Image | Path | str, **kwargs) -> str:
        self.initialize_model()

        import torch

        image = self._load_image(img_or_path)
        messages = [
            {
                "role": "user",
                "content": [
                    {"type": "image", "image": image},
                    {"type": "text", "text": _OCR_PROMPT},
                ],
            }
        ]
        inputs = self._processor.apply_chat_template(
            messages,
            tokenize=True,
            add_generation_prompt=True,
            return_dict=True,
            return_tensors="pt",
        ).to(self._device)

        with torch.no_grad():
            generated = self._model.generate(**inputs, max_new_tokens=1024)

        # Strip the prompt tokens, keeping only the newly generated answer.
        trimmed = generated[:, inputs["input_ids"].shape[1] :]
        text = self._processor.batch_decode(trimmed, skip_special_tokens=True)[0]
        return text.strip()
