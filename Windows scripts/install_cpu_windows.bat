@echo off
setlocal

:: Create a CPU-only Windows uv environment, matching the Makefile uv-sync-gui-cpu target.
if not defined PY_UV set "PY_UV=python3.14"
set "VENV_GUI_CPU=.venv-gui-cpu"
set "UV_EXCLUDE_NEWER=10 days"

if exist "%VENV_GUI_CPU%" rmdir /s /q "%VENV_GUI_CPU%"
uv venv --python "%PY_UV%" "%VENV_GUI_CPU%" || exit /b 1
uv pip install --python "%VENV_GUI_CPU%\Scripts\python.exe" ^
    --torch-backend cpu ^
    --group runtime-base ^
    --group runtime-gui ^
    --group runtime-dbus ^
    --group dev-tools ^
    --group runtime-torch || exit /b 1
