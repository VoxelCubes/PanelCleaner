"""
Comic text and bubble detector.

This wraps the RT-DETR-v2 model from
https://huggingface.co/ogkalu/comic-text-and-bubble-detector as an optional,
auxiliary object detector. It is NOT a replacement for the built-in
comic_text_detector (which also produces the segmentation mask the cleaning
pipeline relies on); instead it is used to *augment* box detection and to
classify boxes as being inside a speech bubble or free-floating.

The model detects three classes:
    0 -> bubble      (the speech bubble shape itself)
    1 -> text_bubble (text located inside a bubble)
    2 -> text_free   (text located outside any bubble)

It requires ``transformers`` with RT-DETRv2 support, which is only pulled in by
the optional ``paddleocr-vl`` extra. The heavy imports are therefore deferred
into ``initialize_model`` and availability is reported through
:func:`is_available`.
"""

from pathlib import Path

import numpy as np
from loguru import logger
from PIL import Image


# The Hugging Face repository id for the model.
MODEL_ID = "ogkalu/comic-text-and-bubble-detector"

# Class id -> human readable label, as trained by the model author.
CLASS_BUBBLE = 0
CLASS_TEXT_BUBBLE = 1
CLASS_TEXT_FREE = 2
CLASS_MAP = {
    CLASS_BUBBLE: "bubble",
    CLASS_TEXT_BUBBLE: "text_bubble",
    CLASS_TEXT_FREE: "text_free",
}

# Detection = (xyxy box, class id, confidence score).
Detection = tuple[tuple[int, int, int, int], int, float]


def is_available() -> bool:
    """
    Check whether the optional dependencies for the bubble detector are present.

    :return: True if the RT-DETR object detection model can be loaded.
    """
    try:
        from transformers import AutoModelForObjectDetection  # noqa: F401
    except ImportError:
        return False
    return True


class BubbleDetector:
    _instance = None
    _model = None
    _processor = None
    _device = None
    _source = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            logger.info("Creating the BubbleDetector instance")
            cls._instance = super(BubbleDetector, cls).__new__(cls)
            cls._instance._model = None
            cls._instance._processor = None
            cls._instance._device = None
            cls._instance._source = None
        return cls._instance

    def __init__(self, *args, **kwargs):
        # Initialization logic is deferred to initialize_model.
        pass

    def initialize_model(self, model_path: str | None = None) -> None:
        source = model_path or MODEL_ID
        # Reload if the requested source changed (e.g. a custom override path).
        if self._model is not None and self._source == source:
            return

        if not is_available():
            raise RuntimeError(
                "The comic text and bubble detector requires the optional dependency "
                "'transformers' with RT-DETRv2 support (transformers>=4.45).\n"
                "Install it with: pip install 'pcleaner[paddleocr-vl]'"
            )

        import torch
        from transformers import AutoImageProcessor, AutoModelForObjectDetection

        if torch.cuda.is_available():
            device = "cuda"
        elif torch.backends.mps.is_available():
            device = "mps"
        else:
            device = "cpu"

        logger.info(f"Loading comic text and bubble detector on device: {device}")
        self._processor = AutoImageProcessor.from_pretrained(source)
        self._model = AutoModelForObjectDetection.from_pretrained(source).to(device).eval()
        self._device = device
        self._source = source

    @staticmethod
    def _to_pil(image: "np.ndarray | Image.Image") -> Image.Image:
        if isinstance(image, Image.Image):
            return image.convert("RGB")
        # cv2 images are BGR ndarrays; convert to RGB for the model.
        if isinstance(image, np.ndarray):
            return Image.fromarray(image[..., ::-1]).convert("RGB")
        raise ValueError(f"image must be a numpy array or PIL.Image, got: {type(image)}")

    def detect(
        self,
        image: "np.ndarray | Image.Image",
        conf_thresh: float = 0.3,
        model_path: str | None = None,
    ) -> list[Detection]:
        """
        Run object detection on an image.

        :param image: The image as a cv2 BGR ndarray or a PIL image.
        :param conf_thresh: Minimum confidence score to keep a detection.
        :param model_path: Optional path/repo override for the model weights.
        :return: A list of (xyxy box, class id, score) detections.
        """
        self.initialize_model(model_path)

        import torch

        pil_image = self._to_pil(image)
        inputs = self._processor(images=pil_image, return_tensors="pt").to(self._device)
        with torch.no_grad():
            outputs = self._model(**inputs)

        # (height, width) as expected by post_process_object_detection.
        target_sizes = torch.tensor([pil_image.size[::-1]], device=self._device)
        results = self._processor.post_process_object_detection(
            outputs, threshold=conf_thresh, target_sizes=target_sizes
        )[0]

        detections: list[Detection] = []
        for box, label, score in zip(
            results["boxes"], results["labels"], results["scores"]
        ):
            x1, y1, x2, y2 = (int(round(v)) for v in box.tolist())
            detections.append(((x1, y1, x2, y2), int(label), float(score)))
        return detections
