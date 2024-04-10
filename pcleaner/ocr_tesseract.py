from pathlib import Path

import pytesseract
from PIL import Image

class TesseractOcr:
    def __init__(self, lang='eng'):
        self.lang = lang

    def __call__(self, img_or_path):
        if isinstance(img_or_path, str) or isinstance(img_or_path, Path):
            img = Image.open(img_or_path)
        elif isinstance(img_or_path, Image.Image):
            img = img_or_path
        else:
            raise ValueError(f'img_or_path must be a path or PIL.Image, instead got: {img_or_path}')

        text = pytesseract.image_to_string(img, lang=self.lang)
        return text#half_to_full_width(text)
