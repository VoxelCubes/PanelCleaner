# AUTOGENERATED! DO NOT EDIT! File to edit: ../nbs/ocr_paligemma.ipynb.

# %% ../nbs/ocr_paligemma.ipynb 1
from __future__ import annotations


# %% auto 0
__all__ = ['PaliGemmaOCR']

# %% ../nbs/ocr_paligemma.ipynb 5
import subprocess
from pathlib import Path
from typing import Any
from typing import Literal
from typing import TypeAlias

import torch
import transformers.image_utils as image_utils
from PIL import Image
from rich.console import Console
from transformers import AutoProcessor
from transformers import BitsAndBytesConfig
from transformers import PaliGemmaForConditionalGeneration


# %% ../nbs/ocr_paligemma.ipynb 12
console = Console(width=104, tab_size=4, force_jupyter=True)
cprint = console.print


# %% ../nbs/ocr_paligemma.ipynb 15
from .experiments import *
from .helpers import RenderJSON
from .helpers import IN_MAC
from .helpers import IN_LINUX
from .helpers import default_device
from .ocr_metric import *
from .web_server import setup_ngrok
from .web_server import WebServerBottle


# %% ../nbs/ocr_paligemma.ipynb 16
if IN_MAC:
    import mlx.core as mx
    from mlx_vlm import load, generate


# %% ../nbs/ocr_paligemma.ipynb 17
def load_image(img_ref: str | Path | Image.Image) -> Image.Image:
    return image_utils.load_image(str(img_ref) if isinstance(img_ref, Path) else img_ref)


# %% ../nbs/ocr_paligemma.ipynb 18
def get_gpu_vram(total=True):
    if total:
        if IN_MAC:
            return mx.metal.device_info()['memory_size']//1024//1024
        else:
            command = "nvidia-smi --query-gpu=memory.total --format=csv,noheader,nounits"
    else:
        if IN_MAC:
            return mx.metal.get_active_memory()//1024//1024
        else:
            command = "nvidia-smi --query-gpu=memory.used --format=csv,noheader,nounits"
    try:
        vram = subprocess.check_output(command, shell=True).decode('utf-8').strip()
        return vram
    except subprocess.CalledProcessError:
        return "Failed to get VRAM"


# %% ../nbs/ocr_paligemma.ipynb 66
SizeT = Literal['224', '448']
QuantT: TypeAlias = Literal['bfloat16'] | Literal['8bit'] | Literal['4bit']


def _setup_processor(model_id: str='google/paligemma-3b-mix-224', **kwargs):
    size: SizeT = kwargs.pop('size', '224')
    quant: QuantT = kwargs.pop('quant', '8bit')
    if IN_MAC and quant != 'bfloat16':
        from mlx_vlm.utils import get_model_path, load_processor
        model_id = f'mlx-community/paligemma-3b-mix-{size}-8bit'
        processor_config = kwargs.pop('processor_config', None)
        model_path = get_model_path(model_id)
        if processor_config is None:
            processor = load_processor(model_path)
        else:
            processor = load_processor(model_path, processor_config=processor_config)
    else:
        processor = AutoProcessor.from_pretrained(model_id)
    return processor


# %% ../nbs/ocr_paligemma.ipynb 68
def _setup_model(device:str | None, size: SizeT, quant: QuantT, lazy: bool = False):
    if IN_MAC and quant != 'bfloat16':
        from mlx_vlm.utils import load_model, get_model_path
        model_id = f"mlx-community/paligemma-3b-mix-{size}-8bit"
        model_path = get_model_path(model_id)
        model = load_model(model_path, lazy=lazy)
    else:
        model_id = f"google/paligemma-3b-mix-{size}"
        generation_args: dict =  {
        }
        if quant == '8bit':
            generation_args['quantization_config'] = BitsAndBytesConfig(load_in_8bit=True)
        elif quant =='4bit':
            generation_args['quantization_config'] = BitsAndBytesConfig(load_in_4bit=True)
        else:
            generation_args['device_map'] = device or default_device()
            generation_args['torch_dtype'] = torch.bfloat16
            generation_args['revision'] = 'bfloat16'
        model = PaliGemmaForConditionalGeneration.from_pretrained(model_id, **generation_args,).eval()

    return model

# %% ../nbs/ocr_paligemma.ipynb 70
prompt_text_tmpl = (
        "Perform optical character recognition OCR on this image, which contains speech "
        "balloons from a comic book. The text is in {}."
)

prompt_text_tmpl = (
        "Do perform optical character recognition OCR on the image, which contains speech "
        "balloons from a comic book. The text is in {}. Carefully extract the text exactly "
        "as it appears, ensuring that you preserve the original capitalization, punctuation, and "
        "formatting."
)

prompt_text_tmpl = 'What does the text say?'
prompt_text_tmpl = 'OCR the text in the image'


default_prompt_text_tmpl = prompt_text_tmpl

# %% ../nbs/ocr_paligemma.ipynb 71
class PaliGemmaOCR:
    prompt_text_tmpl: str = default_prompt_text_tmpl
    PROCESSOR: Any = None
    MODEL: Any = None


    @classmethod
    def setup_processor(cls, 
            model_id: str='google/paligemma-3b-mix-224', 
            size: SizeT = '224',
            quant: QuantT = '8bit',
            ):
        cls.PROCESSOR = _setup_processor(model_id, size=size, quant=quant)
        return cls.PROCESSOR
    
    @classmethod
    def setup_model(cls, device: str | None = None, size: SizeT='224', quant: QuantT='bfloat16'):
        cls.MODEL = _setup_model(device, size, quant)
        return cls.MODEL
    
    @staticmethod
    def is_paligemma_available() -> bool:
        return PaliGemmaOCR.PROCESSOR is not None and PaliGemmaOCR.MODEL is not None
    is_model_ready = is_paligemma_available

    def setup_paligemma(self):
        if self.PROCESSOR is None:
            type(self).setup_processor(size=self.size, quant=self.quant)
        if self.MODEL is None:
            type(self).setup_model(self.device, self.size, self.quant)
    setup = setup_paligemma
    
    def cleanup(self):
        try: del self.PROCESSOR
        except Exception: pass
        try: del self.MODEL
        except Exception: pass
        if IN_MAC:
            mx.metal.clear_cache()
        else:
            torch.cuda.empty_cache()
        import gc
        gc.collect()
        self.MODEL = self.PROCESSOR = None

    def _generation_args_mac(self, image: Image.Image, prompt_text: str):
        prompt = prompt_text
        max_new_tokens = 100
        temperature = 0.0
        top_p = 1.0
        # repetition_penalty = 1.2
        # repetition_context_size = 20
        generation_args: dict = {
            'model': self.MODEL,
            'processor': self.PROCESSOR,
            "image": image,
            'prompt': prompt,
            "max_tokens": max_new_tokens,
            'temp': temperature,
            'top_p': top_p,
            # 'repetition_penalty': repetition_penalty,
            # 'repetition_context_size': repetition_context_size,
        }
        return prompt, generation_args

    def _generation_args(self, image: Image.Image, prompt: str):
        model_inputs = self.PROCESSOR(text=prompt, images=image, return_tensors="pt").to(self.MODEL.device)
        max_new_tokens=100
        do_sample = False
        generation_args: dict = {
            'max_new_tokens': max_new_tokens,
            'do_sample': do_sample,
        }
        return prompt, model_inputs, generation_args

    def _generate_mac(self, image: Image.Image, prompt_text: str):
        prompt, generation_args = self._generation_args_mac(image, prompt_text)
        output = generate(
            **generation_args, 
            verbose=False#True
        )
        return prompt, output.strip('<end_of_utterance>').strip(' ')

    def _generate(self, image: Image.Image, prompt: str):
        prompt, model_inputs, generation_args = self._generation_args(image, prompt)
        input_len = model_inputs["input_ids"].shape[-1]
        with torch.inference_mode():
            generation = self.MODEL.generate(**model_inputs, **generation_args)
            generation = generation[0][input_len:]
            decoded = self.PROCESSOR.decode(generation, skip_special_tokens=True)
        return prompt, decoded

    def postprocess_ocr(self, text):
        return ' '.join(remove_multiple_whitespaces(text).splitlines())
    
    def show_info(self):
        quant = self.quant
        size = self.size
        cfg = PaliGemmaOCR.MODEL.config if PaliGemmaOCR.MODEL is not None else None
        if cfg is not None:
            if hasattr(cfg, 'quantization_config'):
                qcfg = cfg.quantization_config
                quant = '4bit' if qcfg.load_in_4bit else '8bit'
        cprint(
            f"{'Size':>17}: {size!r}\n"
            f"{'Quantization':>17}: {quant!r}\n"
            f"{'Device':>17}: {self.device!r}\n"
            f"{'VRAM':>17}: {get_gpu_vram(False)}/{get_gpu_vram()} MiB\n"
        )


    def __call__(
        self,
        img_or_path: Image.Image | Path | str,
        lang: str | None = None,
        prompt_text: str | None = None,
        config: str | None = None,
        show_prompt: bool = False,
        **kwargs,
    ) -> str:
        self.setup_paligemma()
        if not self.is_paligemma_available():
            raise RuntimeError("PaliGemma is not installed or not found.")
        prompt_text = prompt_text or self.prompt_text_tmpl.format(lang or self.lang)
        image = load_image(img_or_path)
        gen_func = self._generate_mac if IN_MAC and self.quant != 'bfloat16' else self._generate
        prompt, generated_text = gen_func(image, prompt_text)
        if show_prompt:
            cprint("INPUT:", prompt, "\nOUTPUT:", generated_text)
        return generated_text#.strip('"')


    def __init__(self, 
            lang: str | None = None, 
            size: SizeT | None = None,
            quant: QuantT | None = None,
            device: str | None = None, 
            *, 
            prompt_text_tmpl: str | None = None, 
            lazy: bool | None = False,
            **_
        ):
        self.lang = lang
        self.prompt_text_tmpl = prompt_text_tmpl or self.prompt_text_tmpl
        self.size: SizeT = size or '224'
        self.quant: QuantT = quant or 'bfloat16'#'8bits'
        self.device = device or default_device()
        if not lazy and not self.is_paligemma_available():
            self.setup_paligemma()


OCRExperimentContext.register_model('PaliGemma', PaliGemmaOCR, {
            "size": '224',
            "quant": 'bfloat16',
        })

