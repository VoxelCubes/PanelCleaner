:: Perform a Windows build with CUDA.
uv venv .venv-gui-cuda
call .venv-gui-cuda\Scripts\activate
for /f %%i in ('powershell -NoProfile -Command "(Get-Date).AddDays(-7).ToString('yyyy-MM-dd')"') do set UV_EXCLUDE_NEWER=%%i
uv sync --active --group runtime-base --group runtime-gui --group dev-tools

.\.venv-gui-cuda\Scripts\pyinstaller.exe pcleaner/main.py --paths '.venv-gui-cuda/Lib/site-packages' ^
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
    --add-data ".venv-gui-cuda/Lib/site-packages/manga_ocr/assets/example.jpg;assets/" ^
    --collect-data pcleaner
