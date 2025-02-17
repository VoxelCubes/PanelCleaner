import yaml
from pathlib import Path, PosixPath
from importlib import resources

import pcleaner.gui.gui_utils as gu
import pcleaner.gui.ui_generated_files
import pcleaner.data.theme_icons as theme_icons_module
import pcleaner.helpers as hp


def test_get_available_themes():
    """
    Test the get_available_themes function.
    """
    themes = gu.get_available_themes()

    assert themes
    assert set(themes) == {("breeze-dark", "Breeze Dark"), ("breeze", "Breeze Light")}


def test_theme_icon_presence():
    """
    Test that all icons are present in the resources.
    """
    # Read the icon list from the yaml file located at DeepQt/icons/theme_list.yaml
    yaml_path = Path(__file__).parent.parent / "icons" / "theme_list.yaml"
    theme_icons_root = hp.resource_path(theme_icons_module)

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


def test_theme_icon_app_presence():
    # Load the source code and inspect it for xdg icon names.
    with resources.as_file(resources.files(pcleaner.gui.ui_generated_files)) as f:
        source_dir = f

    # This only works for the generated code from ui files.
    # General python code would be undecidable.
    expected_icons: set[str] = set()
    for source_file in source_dir.rglob("*.py"):
        with source_file.open() as file:
            for line in file:
                if 'iconThemeName = u"' in line:
                    theme_name = line.split('iconThemeName = u"')[1].split('"')[0]
                    expected_icons.add(theme_name)

    # Ensure they are listed in the yaml icon list file.
    yaml_path = Path(__file__).parent.parent / "icons" / "theme_list.yaml"
    with yaml_path.open() as file:
        data = yaml.safe_load(file)

    theme_icons = data["Files"]
    icon_set = set()
    for category, sizes in theme_icons.items():
        for size, icons in sizes.items():
            for icon in icons:
                icon_set.add(icon)

    missing = expected_icons - icon_set
    assert not missing
