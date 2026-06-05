:: Webtoon Translate & Cleaner - open the GUI (workspace browser + glossary editor).
:: Run from the PROJECT ROOT:
::    ".\Windows scripts\webtoon-gui.bat"             (browse all workspaces)
::    ".\Windows scripts\webtoon-gui.bat" myseries    (jump to a workspace's glossary)
@echo off
setlocal

if not exist "venv\Scripts\python.exe" (
    echo [ERROR] venv not found. Run ".\Windows scripts\webtoon-install.bat" first.
    exit /b 1
)

".\venv\Scripts\python.exe" pcleaner\main.py workspace gui %*
endlocal
