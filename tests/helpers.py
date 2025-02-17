from pathlib import Path
from importlib import resources
from tests import mock_files


def read_mock_file(file_name: str, module=mock_files) -> str:
    with resources.as_file(resources.files(module).joinpath(file_name)) as f:
        file_contents = f.read_text()
    return file_contents


def mock_file_path(file_name: str, module=mock_files) -> Path:
    with resources.as_file(resources.files(module).joinpath(file_name)) as f:
        path = f
    return path
