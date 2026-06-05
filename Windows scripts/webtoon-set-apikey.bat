:: Webtoon Translate & Cleaner - persist your OpenRouter API key.
:: Stores OPENROUTER_API_KEY as a user environment variable (remembered across reboots).
:: Run from the PROJECT ROOT:
::    ".\Windows scripts\webtoon-set-apikey.bat" sk-or-xxxxxxxxxxxxxxxx
::
:: NOTE: open a NEW terminal afterwards so the variable takes effect.
@echo off
setlocal

if "%~1"=="" (
    echo Usage: webtoon-set-apikey.bat ^<your-openrouter-api-key^>
    echo Get a key at https://openrouter.ai/keys
    exit /b 1
)

setx OPENROUTER_API_KEY "%~1" >nul
if errorlevel 1 (
    echo [ERROR] Failed to set the environment variable.
    exit /b 1
)

echo OpenRouter API key saved.
echo Open a NEW terminal window for it to take effect.
endlocal
