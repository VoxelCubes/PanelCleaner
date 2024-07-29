:: Perform a Windows build with CUDA.
:: Be sure to switch venv first!
.\venv-cuda\Scripts\pip install pyinstaller
.\venv-cuda\Scripts\pyinstaller.exe pcleaner/main.py --paths 'venv-cuda/Lib/site-packages' ^
    --onefile --noconfirm --clean --workpath=build --distpath=dist_exe_cuda --windowed ^
    --name="PanelCleaner.exe" --icon=icons\logo.ico ^
    --copy-metadata filelock ^
    --copy-metadata huggingface-hub ^
    --copy-metadata numpy ^
    --copy-metadata packaging ^
    --copy-metadata pyyaml ^
    --copy-metadata regex ^
    --copy-metadata requests ^
    --copy-metadata safetensors ^
    --copy-metadata tokenizers ^
    --copy-metadata tqdm ^
    --copy-metadata torch ^
    --collect-data torch ^
    --collect-data unidic_lite ^
    --hidden-import=scipy.signal ^
    --add-data "venv/Lib/site-packages/manga_ocr/assets/example.jpg;assets/" ^
    --collect-data pcleaner
