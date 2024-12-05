import difflib
import os
import platform
import shutil
import subprocess
import sys
from io import StringIO
from pathlib import Path

import prettytable as pt
import torch
from loguru import logger
from xdg import XDG_CONFIG_HOME, XDG_CACHE_HOME

import pcleaner.config as cfg
import pcleaner.helpers as hp
import pcleaner.ocr.supported_languages as osl
from pcleaner import __display_name__, __version__
from pcleaner import __program__


def get_config_path() -> Path:
    """
    Get the path to the configuration file for both Linux and Windows.
    """
    xdg_path = os.getenv("XDG_CONFIG_HOME") or Path.home() / ".config"

    if platform.system() == "Linux":
        path = Path(XDG_CONFIG_HOME, __program__, __program__ + "rc")
    elif platform.system() == "Windows":
        path = Path(
            xdg_path if "XDG_CONFIG_HOME" in os.environ else os.getenv("APPDATA"),
            __program__,
            __program__ + "config.ini",
        )
    elif platform.system() == "Darwin":
        path = Path(
            (
                xdg_path
                if "XDG_CONFIG_HOME" in os.environ
                else (Path.home() / "Library" / "Application Support")
            ),
            __program__,
            __program__ + "config.ini",
        )
    else:  # ???
        raise NotImplementedError("Your OS is currently not supported.")

    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def get_default_profile_path(profile_name: str | None = None) -> Path:
    if profile_name is None:
        return get_config_path().parent / "profiles"
    return get_config_path().parent / "profiles" / f"{profile_name}.conf"


def get_cache_path() -> Path:
    """
    Get the default suggested path to the cache directory for both Linux and Windows.
    """
    xdg_path = os.getenv("XDG_CACHE_HOME") or Path.home() / ".cache"

    if platform.system() == "Linux":
        path = Path(XDG_CACHE_HOME, __program__)
    elif platform.system() == "Windows":
        path = Path(
            xdg_path if "XDG_CACHE_HOME" in os.environ else os.getenv("APPDATA"),
            __program__,
            "cache",
        )
    elif platform.system() == "Darwin":
        path = Path(
            xdg_path if "XDG_CACHE_HOME" in os.environ else (Path.home() / "Library" / "Caches"),
            __program__,
        )
    else:  # ???
        raise NotImplementedError("Your OS is currently not supported.")

    path.mkdir(parents=True, exist_ok=True)
    return path


def get_log_path() -> Path:
    """
    Get the path to the log file.
    Use the cache directory for this.
    """
    return get_cache_path() / f"{__program__}.log"


def get_lock_file_path() -> Path:
    """
    Get the path to the lock file.
    Use the cache directory for this.
    """
    return get_cache_path() / f"{__program__}.lock"


def open_file_with_editor(path: Path, configured_opener: str | None) -> None:
    """
    Open the given file with the given editor.
    If no editor is given, use the default editor for the current OS.

    :param path: The path to the file to open.
    :param configured_opener: The configured editor to use.
    """
    if platform.system() == "Linux":
        opener = "xdg-open" if configured_opener is None else configured_opener
        print(f"Opening {path} with {opener}.")
        # Test if the configured editor exists. Even xdg-open may be missing, like in a docker container.
        if shutil.which(opener) is None:
            print(
                f"Configured editor '{opener}' not found. "
                f"Please open the file manually or configure another program."
            )
            return
        # Run and detach the process, so this one can exit.
        subprocess.Popen([opener, path], start_new_session=True)

        print("If nothing happens, try setting the profile_editor option in the config.")

    elif platform.system() == "Windows":
        opener = "start" if configured_opener is None else configured_opener
        print(f"Opening {path} with {opener}.")
        os.system(f"{opener} {path}")

        print("\nIf nothing happens, try setting the 'profile_editor' option in the config.")
    elif platform.system() == "Darwin":
        opener = "open" if configured_opener is None else configured_opener
        print(f"Opening {path} with {opener}.")
        os.system(f'{opener} "{path}"')

        print("\nIf nothing happens, try setting the 'profile_editor' option in the config.")
    else:
        print(
            f"Your OS ({platform.system()}) is not supported, but you can open the path manually:\n"
            f"Profile path: {path}"
        )


def ask_then_delete(target_dir) -> bool:
    """
    Ask to delete a directory.
    On Linux, check if trash-cli is installed and offer to trash the item instead.
    If that fails, ask to delete it.

    :param target_dir:
    :return: True if the directory was deleted.
    """

    if shutil.which("trash"):
        if get_confirmation(f"{target_dir} already exists. Move to trash?", default=True):
            if subprocess.run(["trash-put", str(target_dir)]).returncode == 0:
                return True
            else:
                print("Failed to move to trash.")
        else:
            return False

    if get_confirmation(f"{target_dir} already exists. Do you want to delete it?", default=False):
        shutil.rmtree(target_dir)

    # Perform a final check to see if the directory was deleted.
    return not target_dir.exists()


def get_confirmation(prompt: str, default: bool | None = None) -> bool:
    """
    Get confirmation from the user.
    Repeat if the input wasn't valid.

    :param prompt: The prompt to display to the user.
    :param default: The default value to return if the user doesn't input anything.
    :return: The user's confirmation.
    """
    match default:
        case None:
            prompt += " [y/n]"
        case True:
            prompt += " [Y/n]"
        case False:
            prompt += " [y/N]"

    prompt += " > "

    while True:
        user_input = input(prompt)
        if user_input.lower().strip().startswith("y"):
            return True
        elif user_input.lower().strip().startswith("n"):
            return False
        elif user_input == "" and default is not None:
            return default
        else:
            print("Invalid input. Please try again.")


def empty_cache_dir(cache_dir: Path) -> None:
    """
    Empty the cache directory.
    Only attempt to delete .png images and .json files.
    Or .pt and .onnx files for PyTorch and ONNX models.
    This limits the damage if this points to the wrong directory.
    """
    for item in cache_dir.iterdir():
        if item.suffix in [".png", ".json", ".pt", ".onnx"]:
            item.unlink()
    # Remove all folders starting with "splits".
    for folder in cache_dir.glob("splits*"):
        shutil.rmtree(folder)


def closest_match(word: str, choices: list[str]) -> str | None:
    """
    Return the closest match for the given word in the list of choices.
    If no good match is found, return None.
    """
    if word in choices:
        return word
    else:
        # Find the closest match using difflib:
        closest = difflib.get_close_matches(word, choices, 1, 0.5)  # 0.6 is the default threshold
        if closest:
            return str(closest[0])
        else:
            return None


def list_all_languages() -> None:
    """
    List all supported language codes.
    """
    print("Language detection options:")
    table = pt.PrettyTable()
    table.set_style(pt.SINGLE_BORDER)
    table.field_names = ["Language", "Code"]
    table.align = "l"
    for code, name in osl.LANGUAGE_CODE_TO_NAME.items():
        table.add_row([name, code])
    print(table)


def dump_system_info(executing_from: str, gui: bool = False) -> None:
    logger.info("\n" + cfg.STARTUP_MESSAGE)
    buffer = StringIO()
    buffer.write("\n- Program Information -\n")
    buffer.write(f"Program: {__display_name__} {__version__}\n")
    buffer.write(f"Executing from: {executing_from}\n")
    buffer.write(f"Log file: {get_log_path()}\n")
    buffer.write(f"Config file: {get_config_path()}\n")
    buffer.write(f"Cache directory: {get_cache_path()}\n")
    buffer.write("- System Information -\n")
    buffer.write(f"Operating System: {platform.system()} {platform.release()}\n")
    if platform.system() == "Linux":
        buffer.write(f"Desktop Environment: {os.getenv('XDG_CURRENT_DESKTOP', 'unknown')}\n")
    buffer.write(f"Python Version: {sys.version}\n")
    if gui:
        import PySide6
        import PySide6.QtCore as Qc
        import PySide6.QtGui as Qg
        import PySide6.QtWidgets as Qw

        buffer.write(f"PySide (Qt) Version: {PySide6.__version__}\n")
        buffer.write(f"Available Qt Themes: {', '.join(Qw.QStyleFactory.keys())}\n")
        current_app_theme = Qw.QApplication.style()
        current_app_theme_name = (
            current_app_theme.objectName() if current_app_theme else "System Default"
        )
        buffer.write(f"Current Qt Theme: {current_app_theme_name}\n")
        icon_theme_name = Qg.QIcon.themeName()
        icon_theme_name = icon_theme_name if icon_theme_name else "System Default"
        buffer.write(f"Current Icon Theme: {icon_theme_name}\n")
        buffer.write(f"System locale: {Qc.QLocale.system().name()}\n")
    buffer.write(f"Architecture: {platform.machine()}\n")
    buffer.write(f"CPU Cores: {os.cpu_count()}\n")
    buffer.write(f"Memory: {hp.sys_virtual_memory_total() / 1024 ** 3:.2f} GiB\n")
    buffer.write(f"Swap: {hp.sys_swap_memory_total() / 1024 ** 3:.2f} GiB\n")
    if torch.cuda.is_available():
        buffer.write(f"GPU: {torch.cuda.get_device_name(0)} (CUDA enabled)\n")
        buffer.write(f"    CUDA Version: {torch.version.cuda}\n")
        buffer.write(
            f"    CUDA Cores: {torch.cuda.get_device_properties(0).multi_processor_count}\n"
        )
        buffer.write(
            f"    VRAM: {torch.cuda.get_device_properties(0).total_memory / 1024 ** 3:.2f} GiB\n"
        )
    else:
        buffer.write("GPU: None (CUDA not available)\n")

    logger.info(buffer.getvalue())
