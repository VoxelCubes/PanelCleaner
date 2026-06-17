@echo off
setlocal

:: Perform a Windows build with CUDA.
if not defined PY_UV set "PY_UV=python3.14"
if not defined GPU_BACKEND set "GPU_BACKEND=auto"
set "VENV_GUI_CUDA=.venv-gui-cuda"
set "UV_EXCLUDE_NEWER=10 days"

if exist "%VENV_GUI_CUDA%" rmdir /s /q "%VENV_GUI_CUDA%"
uv venv --python "%PY_UV%" "%VENV_GUI_CUDA%" || exit /b 1
uv pip install --python "%VENV_GUI_CUDA%\Scripts\python.exe" ^
    --torch-backend "%GPU_BACKEND%" ^
    --group runtime-base ^
    --group runtime-gui ^
    --group runtime-dbus ^
    --group dev-tools ^
    --group runtime-torch || exit /b 1

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
