# PyInstaller spec for a Windows build that bundles transformers 5, so the
# PaddleOCR-VL OCR engine (and the comic text/bubble detector) work inside the
# packaged exe.
#
# The key difference from a plain --onedir CLI build is module_collection_mode:
# transformers 5 reads each model's own .py source file at load time
# (PreTrainedModel._can_set_experts_implementation -> open(inspect.getfile(cls))).
# PyInstaller normally ships only byte-compiled modules, so that open() fails
# with FileNotFoundError and every model (manga-ocr, RT-DETR, PaddleOCR-VL)
# crashes. Collecting these packages as source ('pyz+py') places the real .py
# files in the bundle so inspect/open succeed.

from PyInstaller.utils.hooks import copy_metadata, collect_data_files, collect_submodules

datas = []
datas += collect_data_files("torch")
datas += collect_data_files("unidic_lite")
datas += collect_data_files("pcleaner")
datas += [("venv/Lib/site-packages/manga_ocr/assets/example.jpg", "assets")]

for dist in (
    "filelock",
    "huggingface-hub",
    "numpy",
    "packaging",
    "pyyaml",
    "regex",
    "requests",
    "safetensors",
    "tokenizers",
    "tqdm",
    "torch",
    "transformers",
    "accelerate",
):
    datas += copy_metadata(dist)

hiddenimports = ["scipy.signal"]
hiddenimports += collect_submodules("transformers")

a = Analysis(
    ["pcleaner/main.py"],
    pathex=["venv/Lib/site-packages"],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    # This is the crucial part: ship real .py source for packages whose model
    # classes get inspected/opened at runtime by transformers 5.
    module_collection_mode={
        "transformers": "pyz+py",
        "manga_ocr": "pyz+py",
    },
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="PanelCleaner",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    icon="pcleaner/data/custom_icons/logo.ico",
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    name="PanelCleaner",
)
