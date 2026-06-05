:: Webtoon Translate & Cleaner - generic launcher.
:: Forwards all arguments to Panel Cleaner using the local venv.
:: Run from the PROJECT ROOT, e.g.:
::    ".\Windows scripts\webtoon.bat" workspace run myseries --ocr=detected.csv --clean
::    ".\Windows scripts\webtoon.bat" glossary list --workspace=myseries
@echo off
setlocal

if not exist "venv\Scripts\python.exe" (
    echo [ERROR] venv not found. Run ".\Windows scripts\webtoon-install.bat" first.
    exit /b 1
)

".\venv\Scripts\python.exe" pcleaner\main.py %*
endlocal
