"""
Small helpers for reading and writing TOML files.

The new Webtoon Translate & Cleaner systems (workspace, glossary, translator and
render config) store their data as TOML, since it is friendlier than INI for
nested keys and lists of entries, while remaining easy to hand-edit and diff.

Reading uses the standard library ``tomllib`` on Python 3.11+ and falls back to
the ``tomli`` backport on 3.10. Writing uses ``tomli_w``. These are only imported
by the translation/rendering features, so a clean-only install never needs them.
"""

import shutil
from pathlib import Path
from typing import Any

from loguru import logger

# Reading: tomllib is stdlib on 3.11+, tomli is the backport for 3.10.
try:
    import tomllib as _toml_read
except ModuleNotFoundError:  # pragma: no cover - only on Python 3.10
    import tomli as _toml_read  # type: ignore


def load_toml(path: Path) -> dict[str, Any]:
    """
    Load a TOML file into a dictionary.

    :param path: The path to the TOML file.
    :return: The parsed contents as a dictionary.
    :raises OSError: If the file cannot be read.
    :raises ValueError: If the file is not valid TOML.
    """
    with open(path, "rb") as file:
        try:
            return _toml_read.load(file)
        except Exception as e:
            raise ValueError(f"Failed to parse TOML file {path}: {e}") from e


def dumps_toml(data: dict[str, Any]) -> str:
    """
    Serialize a dictionary to a TOML string.

    :param data: The data to serialize. Must be TOML-compatible.
    :return: The TOML string.
    """
    import tomli_w

    return tomli_w.dumps(data)


def safe_write_toml(data: dict[str, Any], path: Path) -> bool:
    """
    Write a dictionary to a TOML file atomically.

    Writes to a temporary file first and then moves it into place, mirroring
    ``config.Profile.safe_write`` so a failed write never corrupts an existing file.

    :param data: The data to serialize.
    :param path: The destination path.
    :return: True if the file was written successfully, False otherwise.
    """
    path = Path(path)
    temp_path = path.with_suffix(path.suffix + ".tmp")
    try:
        with open(temp_path, "w", encoding="utf-8") as file:
            file.write(dumps_toml(data))
    except Exception:
        logger.exception(f"Failed to write TOML to {temp_path}")
        try:
            if temp_path.exists():
                temp_path.unlink()
        except Exception:
            logger.exception(f"Failed to delete {temp_path}")
        return False

    try:
        shutil.move(temp_path, path)
    except Exception:
        logger.exception(f"Failed to rename {temp_path} to {path}")
        try:
            if temp_path.exists():
                temp_path.unlink()
        except Exception:
            logger.exception(f"Failed to delete {temp_path}")
        return False

    return True
