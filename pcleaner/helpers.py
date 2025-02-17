import difflib
import platform
import subprocess
from importlib import resources
from enum import Enum
from itertools import takewhile, groupby
from pathlib import Path

import psutil
import tifffile
from loguru import logger

try:
    import PySide6.QtCore as Qc
except ImportError:
    Qc = None


def tr(
    text: str,
    disambiguation: str | None = None,
    context: str = "",
    count: int = -1,
) -> str:
    """
    Translate a string to the current locale.
    """
    if Qc is None:
        return text
    return Qc.QCoreApplication.translate(context, text, disambiguation, count)


def f_plural(value, singular: str, plural: str) -> str:
    """
    Selects which form to use based on the value.
    """
    return singular if value == 1 else plural


def resource_path(module, resource="") -> Path:
    with resources.as_file(resources.files(module).joinpath(resource)) as f:
        path = f
    return path


def open_file(path: Path) -> None:
    """
    Open any given file with the default application.
    """
    logger.debug(f"Opening file {path}")
    try:
        if platform.system() == "Linux":
            subprocess.run(["xdg-open", path])
        elif platform.system() == "Windows":
            subprocess.run(["notepad", path])
        elif platform.system() == "Darwin":
            subprocess.run(["open", path])
    except Exception as e:
        logger.exception(e)


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


# Make custom exception for unsupported img suffixes.
class UnsupportedImageType(Exception):
    pass


def discover_all_images(
    img_paths: str | Path | list[str | Path], supported_extensions: list[str]
) -> tuple[list[Path], list[Path]]:
    """
    Discover all images in the given paths.
    Perform a shallow search in directories, not recursing into subdirectories.

    :param img_paths: A path to a single image, directory, or multiple of either.
    :param supported_extensions: A list of supported image extensions. e.g. [".png", ".jpg"]
    :return: A list of all accepted images found by path only, and a list of rejected tiff files,
        if they have an unsupported format.
    """
    img_list: list[Path] = []

    # Wrap single paths in a list.
    if isinstance(img_paths, str):
        img_paths = [Path(img_paths)]
    elif isinstance(img_paths, Path):
        img_paths = [img_paths]
    elif isinstance(img_paths, list):
        # Convert all strings to paths.
        img_paths = [Path(path) for path in img_paths]
    else:
        raise TypeError(tr("Invalid type for img_paths: {paths}".format(paths=type(img_paths))))

    for img_path in img_paths:
        if img_path.is_dir():
            img_list.extend(find_all_images_shallow(img_path, supported_extensions))
        elif img_path.is_file() and (img_path.suffix.lower() in supported_extensions):
            img_list.append(img_path)
        elif img_path.is_file():
            raise UnsupportedImageType(
                tr("Unsupported image format: {suffix} for {path}").format(
                    suffix=img_path.suffix, path=img_path
                )
            )
        else:
            raise FileNotFoundError(
                tr("Image path {img_path} does not exist.").format(img_path=img_path)
            )

    # Ensure all paths are absolute.
    img_list = [path.resolve() for path in img_list]

    # Filter out 5 channel TIFFs, as they are not supported.
    rejected_tiffs = [path for path in img_list if is_5_channel_tiff(path)]
    img_list = [path for path in img_list if not is_5_channel_tiff(path)]

    return img_list, rejected_tiffs


def find_all_images_shallow(img_dir: Path, supported_extensions: list[str]) -> list[Path]:
    """
    Non-recursive search for all images in the given directory.

    :param img_dir: The directory to search.
    :param supported_extensions: A list of supported image extensions. e.g. [".png", ".jpg"]
    :return: A list of all images found in the given directory.
    """
    image_list: list[Path] = []
    for file_path in img_dir.glob("*"):
        file_suffix = file_path.suffix
        if file_suffix.lower() not in supported_extensions:
            continue
        else:
            image_list.append(file_path)
    return image_list


def is_5_channel_tiff(path: Path) -> bool:
    """
    Returns True if the given file is a TIFF image with a 5.1 channel, False otherwise.
    """
    # Check suffix first.
    if path.suffix not in [".tif", ".tiff"]:
        return False
    # Try opening the file as a TIFF image
    with tifffile.TiffFile(path) as tif:
        logger.debug("Tiff data:\n" + str(tif.pages[0].tags))
        # Check if the TIFF image has 5 channels.
        try:
            if tif.pages[0].tags["SamplesPerPixel"].value == 5:
                logger.warning(
                    f"Found a 5 channel TIFF image: {path}. These are not supported, the image will be skipped."
                )
                return True
        except KeyError:
            pass

    return False


def all_equal(iterable) -> bool:
    """
    Checks if all items in a list are the same using itertools.groupby.
    It works because groupby will produce a single group if and only if all items are the same.
    This groupby function is highly performant.

    :param iterable: An iterable.
    :return: True if all items are the same, False otherwise.
    """
    g = groupby(iterable)
    return next(g, True) and not next(g, False)


def trim_prefix_from_paths(paths: list[Path]) -> list[Path]:
    """
    For a given list of Path objects, shorten them by removing the longest common prefix.
    This will only split along directory boundaries, so the paths will remain valid, but no
    longer relative to the original directory.
    It will not trim the actual file name.

    :param paths: A list of paths to shorten.
    :return: A list of shortened paths as Path objects.
    """
    if not paths:
        return []

    # Split all Path objects into their constituent parts.
    parts = [list(p.parts[:-1]) for p in paths]

    # Calculate how many of the first parts are the same for all paths.
    prefix_len = sum(1 for _ in takewhile(all_equal, zip(*parts)))

    # Shorten paths by removing the common prefix
    short_paths = [Path(*p.parts[prefix_len:]) for p in paths]

    return short_paths


def common_path_parent(paths: list[Path]) -> Path:
    """
    For a given list of Path objects, shorten them by removing the longest common prefix.
    This will only split along directory boundaries, so the paths will remain valid, but no
    longer relative to the original directory.
    It will not trim the actual file name.

    :param paths: A list of paths to shorten.
    :return: A list of shortened paths as Path objects.
    """
    if not paths:
        return Path()

    # Special case: if any path is root (its parent is itself), return root
    root_path = next((p for p in paths if p.parent == p), None)
    if root_path is not None:
        return root_path

    # Split all Path objects into their constituent parts.
    parts = [list(p.parts[:-1]) for p in paths]

    # Calculate how many of the first parts are the same for all paths.
    prefix_len = sum(1 for _ in takewhile(all_equal, zip(*parts)))

    prefix = Path(*paths[0].parts[:prefix_len])

    return prefix


class Urgency(Enum):
    LOW = 0
    NORMAL = 1
    CRITICAL = 2


def send_desktop_notification(
    title: str, message: str = "", duration_s: int = 10, urgency: Urgency = Urgency.NORMAL
) -> None:
    """
    Send a desktop notification using the `notify-send` command on Linux.
    On other platforms, do nothing.

    :param title: The title of the notification.
    :param message: [Optional] The message to display.
    :param duration_s: [Optional] The duration of the notification in seconds.
    :param urgency: [Optional] The urgency level of the notification.
    """
    if platform.system() == "Linux":
        try:
            import dbus
        except ImportError:
            logger.error(
                "dbus-python not installed. Please install it to have desktop notifications."
            )
            return

        item = "org.freedesktop.Notifications"
        notfy_intf = dbus.Interface(
            dbus.SessionBus().get_object(item, "/" + item.replace(".", "/")), item
        )
        notfy_intf.Notify(
            "Panel Cleaner",
            0,
            "panelcleaner",
            title,
            message,
            [],
            {"urgency": urgency.value},
            duration_s * 1000,
        )

    elif platform.system() == "Windows":
        import win10toast

        toaster = win10toast.ToastNotifier()
        toaster.show_toast(title, message, duration=duration_s, threaded=True)

    else:
        logger.debug(f"Desktop notifications are not supported on {platform.system()}")


def sys_virtual_memory_total() -> int:
    """
    Get the total amount of RAM in the system in bytes.
    """
    try:
        return psutil.virtual_memory().total
    except Exception as e:
        logger.exception(e)
        return 0


def sys_virtual_memory_used_percent() -> float:
    """
    Get the percentage of RAM used in the system.
    """
    try:
        return psutil.virtual_memory().percent
    except Exception as e:
        logger.exception(e)
        return 0


def sys_swap_memory_total() -> int:
    """
    Get the total amount of swap memory in the system in bytes.
    """
    try:
        return psutil.swap_memory().total
    except Exception as e:
        logger.exception(e)
        return 0


def sys_swap_memory_used() -> int:
    """
    Get the used amount of swap memory in the system in bytes.
    """
    try:
        return psutil.swap_memory().used
    except Exception as e:
        logger.exception(e)
        return 0
