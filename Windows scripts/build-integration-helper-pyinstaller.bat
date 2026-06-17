@echo off
setlocal

:: Perform a Windows build.
:: This is for the helper script that sets up the windows explorer integration through regedit,
:: which means it needs to be run separately as a subprocess so it can gain admin privileges to edit the registry.
:: When bundling as an exe though, we can't rely on the existing python interpreter, since the bundled one
:: can no longer be used to run the helper script.
if not defined PYINSTALLER_VENV set "PYINSTALLER_VENV=.venv-gui-cpu"

if not exist "%PYINSTALLER_VENV%\Scripts\pyinstaller.exe" (
    echo Virtual environment not found or missing PyInstaller. Please run the matching install script first.
    exit /b 1
)

"%PYINSTALLER_VENV%\Scripts\pyinstaller.exe" pcleaner/data/windows_explorer_integration_regedit.py --paths "%PYINSTALLER_VENV%/Lib/site-packages" ^
    --onefile --noconfirm --clean --workpath=build --distpath=dist_exe --uac-admin --console ^
    --name="WindowsExplorerIntegrationRegedit.exe" --icon=icons\logo.ico
