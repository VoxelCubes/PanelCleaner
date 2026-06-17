@echo off
setlocal

:: Create a CUDA-capable Windows uv environment, matching the Makefile uv-sync-gui-cuda target.
:: Set GPU_BACKEND=cu128, cu130, etc. to force a CUDA version.
if not defined PY_UV set "PY_UV=python3.14"
if not defined GPU_BACKEND set "GPU_BACKEND=auto"
set "VENV_GUI_CUDA=.venv-gui-cuda"
set "UV_EXCLUDE_NEWER=10 days"

if exist "%VENV_GUI_CUDA%" rmdir /s /q "%VENV_GUI_CUDA%"
uv venv --python "%PY_UV%" "%VENV_GUI_CUDA%" || exit /b 1
uv pip install --python "%VENV_GUI_CUDA%\Scripts\python.exe" ^
    --torch-backend "%GPU_BACKEND%" ^
    --group runtime-base ^
    --group runtime-gui ^
    --group runtime-dbus ^
    --group dev-tools ^
    --group runtime-torch || exit /b 1
