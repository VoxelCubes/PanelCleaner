:: Perform a Windows build.
:: Be sure to switch venv first!
:: This is for the helper script that sets up the windows explorer integration through regedit,
:: which means it needs to be run separately as a subprocess so it can gain admin privileges to edit the registry.
:: When bundling as an exe though, we can't rely on the existing python interpreter, since the bundled one
:: can no longer be used to run the helper script.
.\venv\Scripts\pip install pyinstaller
.\venv\Scripts\pyinstaller.exe pcleaner/data/windows_explorer_integration_regedit.py --paths 'venv/Lib/site-packages' ^
    --onefile --noconfirm --clean --workpath=build --distpath=dist_exe --uac-admin --console ^
    --name="WindowsExplorerIntegrationRegedit.exe" --icon=icons\logo.ico
