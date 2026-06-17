@echo off
setlocal

:: These are the packages that are tested on Windows and used for the Windows exe build.
set "VENV_GUI_CPU=.venv-gui-cpu"

if not exist "%VENV_GUI_CPU%\Scripts\python.exe" (
    echo Virtual environment not found. Please run "Windows scripts\build-pyinstaller.bat" first.
    exit /b 1
)

uv pip freeze --no-cache --python "%VENV_GUI_CPU%\Scripts\python.exe" > requirements_tested_windows.txt
