REM This emulates the functionality of the Makefile's refresh-assets target.
@echo off
setlocal enabledelayedexpansion
REM Define variables
set CurrentDir=%cd%
set PYTHON=venv\Scripts\python.exe
set QRC_DIR_ICONS=icons\
set QRC_DIR_THEMES=themes\
set UI_DIR=ui_files\
set RC_OUTPUT_DIR=pcleaner\gui\rc_generated_files\
set UI_OUTPUT_DIR=pcleaner\gui\ui_generated_files\
set RCC_COMPILER=venv\Scripts\pyside6-rcc.exe
set UIC_COMPILER=venv\Scripts\pyside6-uic.exe
set I18N_LUPDATE=venv\Scripts\pyside6-lupdate.exe
set I18N_COMPILER=venv\Scripts\pyside6-lrelease.exe

REM Get supported languages
set TEMP_FILE=temp.txt
%PYTHON% -c "import sys; sys.path.append('.'); from pcleaner.gui.supported_languages import supported_languages; print(' '.join(supported_languages().keys()))" > %TEMP_FILE%

REM Read supported languages from temp file
set /p LANGUAGES=<%TEMP_FILE%
del %TEMP_FILE%

echo %LANGUAGES%

REM Create translations directory
mkdir translations

REM Extract strings for translation
set PYTHONPATH=%CurrentDir%
call %PYTHON% translations\profile_extractor.py
call %PYTHON% translations\process_steps_extractor.py
call %I18N_LUPDATE% -extensions .py,.ui -no-recursive pcleaner pcleaner\gui pcleaner\gui\CustomQ ui_files ^
    translations\profile_strings.py translations\process_strings.py -source-language en_US -target-language en_US -ts translations\PanelCleaner_source.ts

REM Compile translations for each language
for %%l in (%LANGUAGES%) do (
    %I18N_COMPILER% translations\PanelCleaner_%%l.ts -qm translations\packed\PanelCleaner_%%l.qm
)

REM Update QRC file for translations
echo ^<RCC^>^<qresource prefix="/translations"^> > translations\packed\linguist.qrc
for %%l in (%LANGUAGES%) do (
    echo     ^<file^>PanelCleaner_%%l.qm^</file^> >> translations\packed\linguist.qrc
)
echo ^</qresource^>^</RCC^> >> translations\packed\linguist.qrc
%RCC_COMPILER% translations\packed\linguist.qrc -o %RC_OUTPUT_DIR%rc_windows_translations.py

REM Compile .ui files
:: for %%f in (%UI_DIR%*.ui) do (
::     set basename=%%~nf
::     %UIC_COMPILER% %%f -o %UI_OUTPUT_DIR%ui_!basename!.py
:: )

REM Compile .qrc files in QRC_DIR_ICONS
for %%f in (%QRC_DIR_ICONS%*.qrc) do (
    set "basename=%%~nf"
    %RCC_COMPILER% %%f -o !RC_OUTPUT_DIR!rc_windows_!basename!.py
)

REM Compile .qrc files in QRC_DIR_THEMES
for %%f in (%QRC_DIR_THEMES%*.qrc) do (
    set "basename=%%~nf"
    %RCC_COMPILER% %%f -o !RC_OUTPUT_DIR!rc_windows_!basename!.py
)

REM End of batch file
