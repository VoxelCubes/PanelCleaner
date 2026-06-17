@echo off
setlocal

:: Perform a Windows build (CPU-only).
set "VENV_GUI_CPU=.venv-gui-cpu"

if not exist "%VENV_GUI_CPU%\Scripts\pyinstaller.exe" (
    echo Virtual environment not found or missing PyInstaller. Please run "Windows scripts\install_cpu_windows.bat" first.
    exit /b 1
)

call "Windows scripts\build-integration-helper-pyinstaller.bat" || exit /b 1

.\.venv-gui-cpu\Scripts\pyinstaller.exe pcleaner/main.py --paths '.venv-gui-cpu/Lib/site-packages' ^
    --onedir --noconfirm --clean --workpath=build --distpath=dist_exe --windowed ^
    --name="PanelCleaner" --icon=pcleaner/data/custom_icons/logo.ico ^
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
    --add-data "dist_exe/WindowsExplorerIntegrationRegedit.exe;pcleaner/data/" ^
    --add-data ".venv-gui-cpu/Lib/site-packages/manga_ocr/assets/example.jpg;assets/" ^
    --collect-datas pcleaner

Copy "docs\What is _internal.txt" "dist_exe/PanelCleaner\What is _internal.txt"
xcopy "pcleaner\data" "dist_exe\PanelCleaner\_internal\pcleaner\data" /E /I /Y
cd "dist_exe\PanelCleaner\_internal\pcleaner\data"
for /d /r . %%d in (__pycache__) do @rmdir /s /q "%%d"
