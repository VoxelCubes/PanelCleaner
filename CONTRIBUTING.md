# Contributing

## uv-based workflow

This project uses uv dependency groups in `pyproject.toml` as the source of truth. The Makefile drives the sync and build steps.
uv is configured (via environment variables in the Makefile and scripts) to only resolve packages uploaded at least a week ago,
to guard against the rising threat of supply chain attacks.

### Sync environments

- CPU GUI environment (used for PyInstaller and tooling):
  - `make uv-sync-gui-cpu`
- CUDA GUI environment (optional):
  - `make uv-sync-gui-cuda`
- CUDA CLI environment (optional):
  - `make uv-sync-cli-cuda`

### Build wheels

The setup templates are updated from uv groups via `tools/sync_setup_cfg.py`.

- GUI + CLI wheel:
  - `make build`
- CLI-only wheel:
  - `make build-cli`

### Publish wheels

- `make release`

### PyInstaller builds

- Linux ELF (CPU GUI environment):
  - `make build-elf`
- Windows CPU build:
  - `Windows scripts/build-pyinstaller.bat`
- Windows CUDA build:
  - `Windows scripts/build-pyinstaller-cuda.bat`

### Export tested requirements

Generate a locked `requirements_tested.txt` (used for Flatpak builds):

- `make requirements-tested`

## Pip fallback

A plain `requirements.txt` remains available for users who prefer pip, note that it is derived from pyproject.toml for gui builds.


