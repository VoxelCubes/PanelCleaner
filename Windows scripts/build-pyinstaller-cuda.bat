@echo off
setlocal

:: Perform a Windows build with CUDA.
set "VENV_GUI_CUDA=.venv-gui-cuda"

if not exist "%VENV_GUI_CUDA%\Scripts\pyinstaller.exe" (
    echo Virtual environment not found or missing PyInstaller. Please run "Windows scripts\install_cuda_windows.bat" first.
    exit /b 1
)

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
