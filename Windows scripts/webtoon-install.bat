:: Webtoon Translate & Cleaner - one-shot installer for Windows.
:: Run this from the PROJECT ROOT (not from inside the "Windows scripts" folder):
::    ".\Windows scripts\webtoon-install.bat"
::
:: Creates a local virtual environment in .\venv and installs all dependencies
:: (including torch, PySide6, tomli_w). Requires Python 3.10+ on PATH.
@echo off
setlocal

where python >nul 2>nul
if errorlevel 1 (
    echo [ERROR] Python was not found on PATH. Install Python 3.10+ and try again.
    exit /b 1
)

if not exist "venv" (
    echo Creating virtual environment in .\venv ...
    python -m venv venv
    if errorlevel 1 (
        echo [ERROR] Failed to create the virtual environment.
        exit /b 1
    )
)

echo Upgrading pip ...
".\venv\Scripts\python.exe" -m pip install --upgrade pip

echo Installing dependencies (this can take a while, torch is large) ...
".\venv\Scripts\pip.exe" install -r requirements.txt
if errorlevel 1 (
    echo [ERROR] Dependency installation failed.
    exit /b 1
)

echo.
echo Done. Next steps:
echo   1) Set your OpenRouter API key:
echo        ".\Windows scripts\webtoon-set-apikey.bat" sk-or-xxxxxxxx
echo   2) Open the GUI:
echo        ".\Windows scripts\webtoon-gui.bat"
echo   or run any command:
echo        ".\Windows scripts\webtoon.bat" workspace new myseries --source=ja --target=th
endlocal
