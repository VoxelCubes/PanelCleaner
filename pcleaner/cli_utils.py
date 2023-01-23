import difflib
import os
import platform
import shutil
import subprocess
from pathlib import Path

from xdg import XDG_CONFIG_HOME, XDG_CACHE_HOME

from pcleaner import __program__


def get_config_path() -> Path:
    """
    Get the path to the configuration file for both Linux and Windows.
    """
    if platform.system() == "Linux":
        path = Path(XDG_CONFIG_HOME, __program__, __program__ + "rc")
    elif platform.system() == "Windows":
        path = Path(os.getenv("APPDATA"), __program__, __program__ + "config.ini")
    elif platform.system() == "Darwin":
        path = Path(
            os.getenv("HOME"),
            "Library",
            "Application Support",
            __program__,
            __program__ + "config.ini",
        )
    else:  # ???
        raise NotImplementedError("Your OS is currently not supported.")

    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def get_cache_path() -> Path:
    """
    Get the default suggested path to the cache directory for both Linux and Windows.
    """
    if platform.system() == "Linux":
        path = Path(XDG_CACHE_HOME, __program__)
    elif platform.system() == "Windows":
        path = Path(os.getenv("APPDATA"), __program__, "cache")
    elif platform.system() == "Darwin":
        path = Path(
            os.getenv("HOME"),
            "Library",
            "Caches",
            __program__,
        )
    else:  # ???
        raise NotImplementedError("Your OS is currently not supported.")

    path.mkdir(parents=True, exist_ok=True)
    return path


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
        # Run and detatch the process, so this one can exit.
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
        os.system(f"{opener} {path}")

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
