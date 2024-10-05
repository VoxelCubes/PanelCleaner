import yaml
from pathlib import Path, PosixPath
from importlib import resources

import pcleaner.gui.gui_utils as gu
import pcleaner.data.theme_icons as theme_icons_module


def test_get_available_themes():
    """
    Test the get_available_themes function.
    """
    themes = gu.get_available_themes()

    assert themes
    assert themes == [("breeze", "Breeze Light"), ("breeze-dark", "Breeze Dark")]


def test_theme_icon_presence():
    """
    Test that all icons are present in the resources.
    """
    # Read the icon list from the yaml file located at DeepQt/icons/theme_list.yaml
    yaml_path = Path(__file__).parent.parent / "icons" / "theme_list.yaml"
    with resources.files(theme_icons_module) as theme_icons_path:
        theme_icons_root = Path(theme_icons_path)

    with yaml_path.open() as file:
        data = yaml.safe_load(file)

    theme_directories = data["Theme directories"]
    theme_icons = data["Files"]

    # Perform a depth-first search for each icon in a theme, which means
    # checking for leaf nodes, which are the icon file names.
    # When coming across a directory, the name of that directory is added to the path,
    # then scanned recursively.
    for theme_path in theme_directories:
        # Only use the last directory name of the theme path.
        theme_directory_name = PosixPath(theme_path).name
        for category, sizes in theme_icons.items():
            for size, icons in sizes.items():
                for icon in icons:
                    expected_relative_path = (
                        PosixPath(theme_directory_name) / category / str(size) / icon
                    )

                    for suffix in ["svg", "png"]:
                        full_path = (
                            theme_icons_root
                            / expected_relative_path.with_suffix(f".{suffix}").as_posix()
                        )
                        if full_path.exists():
                            break
                    else:
                        assert (
                            False
                        ), f"Icon {expected_relative_path} not found among the theme_icons data files."
