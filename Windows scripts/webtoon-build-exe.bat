:: Webtoon Translate & Cleaner - build a standalone Windows .exe with PyInstaller.
:: Run from the PROJECT ROOT (after webtoon-install.bat):
::    ".\Windows scripts\webtoon-build-exe.bat"
::
:: Produces dist_exe\PanelCleaner\PanelCleaner.exe, which includes ALL commands
:: (clean, ocr, workspace, glossary, translate, render, gui) since they live under
:: pcleaner\ and are collected automatically.
::
:: This is a self-contained variant of build-pyinstaller.bat that skips the optional
:: Windows Explorer integration helper. For the full official build (with Explorer
:: integration), use build-pyinstaller.bat instead.
@echo off
setlocal

if not exist "venv\Scripts\python.exe" (
    echo [ERROR] venv not found. Run ".\Windows scripts\webtoon-install.bat" first.
    exit /b 1
)

echo Installing PyInstaller into the venv ...
".\venv\Scripts\pip.exe" install pyinstaller
if errorlevel 1 (
    echo [ERROR] Failed to install PyInstaller.
    exit /b 1
)

echo Building PanelCleaner.exe (this takes several minutes) ...
".\venv\Scripts\pyinstaller.exe" pcleaner/main.py --paths "venv/Lib/site-packages" ^
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
    --copy-metadata transformers ^
    --collect-data torch ^
    --collect-data unidic_lite ^
    --hidden-import=scipy.signal ^
    --collect-datas pcleaner
if errorlevel 1 (
    echo [ERROR] PyInstaller build failed.
    exit /b 1
)

echo Copying bundled data ...
Copy "docs\What is _internal.txt" "dist_exe\PanelCleaner\What is _internal.txt"
xcopy "pcleaner\data" "dist_exe\PanelCleaner\_internal\pcleaner\data" /E /I /Y
for /d /r "dist_exe\PanelCleaner\_internal\pcleaner\data" %%d in (__pycache__) do @if exist "%%d" rmdir /s /q "%%d"

echo.
echo Done. Run it with:
echo    dist_exe\PanelCleaner\PanelCleaner.exe workspace gui
echo    dist_exe\PanelCleaner\PanelCleaner.exe workspace run myseries --ocr=detected.csv --clean
endlocal
