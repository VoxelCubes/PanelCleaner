# Contributing

Certain command line tools used here are specific to Linux/MacOS or require special setup on Windows.

## uv-based workflow

This project uses uv dependency groups in `pyproject.toml` as the source of truth. The Makefile drives the sync and build steps.
uv is configured (via environment variables in the Makefile and scripts) to only resolve packages uploaded at least a week ago,
to guard against the rising threat of supply chain attacks. Maintainers should be especially aware of this threat,
since if one of us gets compromised, our own packages could be used to attack our very own users.

### Sync environments

- CPU GUI environment (used for PyInstaller and tooling):
  `make uv-sync-gui-cpu`
- CUDA GUI environment (optional):
  `make uv-sync-gui-cuda`
- CUDA CLI environment (optional):
  `make uv-sync-cli-cuda`

### Running pcleaner from source

Make sure your current working directory is the root of the repo.
Then activate the appropriate environment (e.g. `source .venv-gui-cpu/bin/activate`), then:
- `python -m pcleaner.gui.launcher` to run the GUI
- `python -m pcleaner.main` to run the CLI

### Build wheels

The setup templates are updated from uv groups via `tools/sync_setup_cfg.py`.

- GUI wheel: `make build`
- CLI-only wheel: `make build-cli`

To test the most recently built wheel:
- run: `make test-whl-install`
- Activate this new environment (make sure no other venv is currently active, deactivate them with `deactivate` if needed), then run:
`source .venv-test-whl/bin/activate`
- Change your directory to outside the repo (otherwise it will run the local source files), then run:
`pcleaner-gui` or `pcleaner-cli` as you normally would to test the gui/cli respectively.
Check that the log file includes such a line: 
`Executing from: <your repo path>/PanelCleaner/.venv-test-whl/lib/python3.14/site-packages/pcleaner/gui/launcher.py`
It's important that venv-test-whl is part of the path, otherwise you aren't testing the wheel you just built.

### PyInstaller builds

- Linux ELF (CPU GUI environment): `make build-elf`
- Windows CPU build: `scripts/build-pyinstaller.bat`
- Windows CUDA build: `scripts/build-pyinstaller-cuda.bat`

### Export tested requirements

Generate a locked `requirements_tested.txt` (used for Flatpak builds):
`make requirements-tested`

## Pip fallback

A plain `requirements.txt` remains available for users who prefer pip, note that it is derived from pyproject.toml for gui builds.


