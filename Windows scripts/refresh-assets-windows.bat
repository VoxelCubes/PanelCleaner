REM This simply generates the packed .qm translation files
@echo off
setlocal enabledelayedexpansion
REM Define variables
set CurrentDir=%cd%
set PYTHON=venv\Scripts\python.exe
set I18N_COMPILER=venv\Scripts\pyside6-lrelease.exe

REM Get supported languages
set TEMP_FILE=temp.txt
%PYTHON% -c "import sys; sys.path.append('.'); from pcleaner.gui.supported_languages import supported_languages; lang_codes = list(supported_languages().keys()); lang_codes.remove('en_US'); print(' '.join(lang_codes))" > %TEMP_FILE%

REM Read supported languages from temp file
set /p LANGUAGES=<%TEMP_FILE%
del %TEMP_FILE%

echo %LANGUAGES%

REM Compile translations for each language
for %%l in (%LANGUAGES%) do (
    %I18N_COMPILER% translations\PanelCleaner_%%l.ts -qm pcleaner\data\translation_generated_files\PanelCleaner_%%l.qm
)

REM End of batch file
