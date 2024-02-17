from pathlib import Path

import prettytable as pt

from pcleaner.helpers import tr
import pcleaner.cli_utils as cli
import pcleaner.config as cfg


def list_profiles(config: cfg.Config) -> None:
    """
    Display the dict of profiles in the config in a pretty table.

    :param config: The config object.
    """
    if not config.saved_profiles:
        print(
            "No profiles saved.\n\n"
            "Make a new profile with: (providing a path is optional)\n"
            "   pcleaner profile new <profile name> [<profile path>]\n"
            "or import a profile file with:\n"
            "   pcleaner profile add <profile name> <profile path>"
        )
        return

    def check_path(path: Path) -> str:
        if path.exists():
            return "OK"
        else:
            return "File not found"

    def check_default(profile: str | None) -> str:
        if profile == config.default_profile:
            return "Yes"
        else:
            return ""

    table = pt.PrettyTable()
    table.set_style(pt.SINGLE_BORDER)
    table.field_names = ["Profile Name", "Path", "Status", "Default"]
    # Align the path column to the left, but not the header.
    table.align["Path"] = "l"
    # Insert the builtin first.
    table.add_row(
        [
            config.reserved_profile_names()[0],
            "",
            "OK",
            check_default(None),
        ]
    )
    for profile_name, profile_path in config.saved_profiles.items():
        table.add_row(
            [profile_name, profile_path, check_path(profile_path), check_default(profile_name)]
        )
    print(table)


def new_profile(
    config: cfg.Config, profile_name: str, profile_path: str | None, cli_mode: bool = False
) -> tuple[bool, str]:
    """
    Create a new profile with the given name and path.

    :param config: The config object.
    :param profile_name: The name of the profile.
    :param profile_path: The path to the profile.
    :param cli_mode: Whether to ask to overwrite an existing file. Only applicable in CLI mode.
    """
    valid, msg = is_valid_profile_name(config, profile_name)
    if not valid:
        return False, msg

    # If no path is given, use the default path.
    if profile_path is None:
        profile_path = cli.get_default_profile_path(profile_name)
    else:
        profile_path = Path(profile_path)
        # If the path is a directory, append a default filename.
        if profile_path.is_dir():
            profile_path = profile_path / f"{profile_name}.conf"

    # Check if overwriting an existing file.
    if profile_path.exists():
        if not cli_mode:
            return False, tr("Profile file {profile_path} already exists.").format(
                profile_path=profile_path
            )
        if not cli.get_confirmation(f"Overwrite existing file {profile_path}?"):
            return False, "Aborted."

    profile_path.parent.mkdir(parents=True, exist_ok=True)
    # Create the profile file from the built-in default.
    profile = cfg.Profile()
    profile.safe_write(profile_path)

    # Add the profile to the config.
    config.add_profile(profile_name, profile_path)
    config.save()

    if cli_mode:
        print(f"Profile {profile_name} created at {profile_path}.")
        open_profile(config, profile_name)
        return True, ""

    return True, tr("Profile {profile_name} created.").format(profile_name=profile_name)


def add_profile(config: cfg.Config, profile_name: str, profile_path: str) -> tuple[bool, str]:
    """
    Add a profile to the config.

    :param config: The config object.
    :param profile_name: The name of the profile.
    :param profile_path: The path to the profile file.
    """
    valid, msg = is_valid_profile_name(config, profile_name)
    if not valid:
        return False, msg

    # Verify the profile path exists.
    profile_path = Path(profile_path)
    if not profile_path.is_file():
        return False, "Profile file not found."

    # Add the profile to the config.
    config.add_profile(profile_name, profile_path)
    config.save()

    return True, f"Profile {profile_name} added."


def open_profile(config: cfg.Config, profile_name: str) -> None:
    """
    Open the profile in the default editor, unless specified in the config.

    :param config: The config object.
    :param profile_name: The name of the profile.
    :return:
    """
    profile_path = config.saved_profiles[profile_name]
    cli.open_file_with_editor(profile_path, config.profile_editor)


def delete_profile(config: cfg.Config, profile_name: str) -> None:
    """
    Remove a profile from the config.
    Also offer to delete the profile file.

    :param config: The config object.
    :param profile_name: The name of the profile.
    """
    closest_match = cli.closest_match(profile_name, list(config.saved_profiles.keys()))

    if closest_match is None:
        print(f"Profile {profile_name} not found.")
        return

    profile_file = config.saved_profiles[closest_match]
    config.remove_profile(closest_match)
    config.save()
    print(f"Profile {closest_match} removed.\n")
    if not profile_file.is_file():
        # Already done.
        return
    if cli.get_confirmation(f"Delete profile file {profile_file}?"):
        profile_file.unlink()
        print("File deleted.")


def set_default_profile(config: cfg.Config, profile_name: str) -> None:
    """
    Set the default profile.

    :param config: The config object.
    :param profile_name: The name of the profile.
    """
    closest_match = cli.closest_match(profile_name, list(config.saved_profiles.keys()))
    if closest_match is None:
        print(f"Profile {profile_name} not found.")
        return

    config.default_profile = closest_match
    config.save()


def repair_profile(config: cfg.Config, profile_name: str) -> None:
    """
    Read as much of the profile as possible and then re-export the profile to the same path.

    :param config: The config object.
    :param profile_name: The name of the profile.
    """
    closest_match = cli.closest_match(profile_name, list(config.saved_profiles.keys()))
    if closest_match is None:
        print(f"Profile {profile_name} not found.")
        return

    profile_path = config.saved_profiles[closest_match]
    profile = cfg.Profile()
    not_salvageable = False
    try:
        profile.load(profile_path)
    except Exception as e:
        print(f"Unfixable error loading profile: {e}")
        profile = cfg.Profile()
        not_salvageable = True

    # Verify the values in the profile.
    profile.fix()

    # If it wasn't salvageable, ask before overwriting.
    if not_salvageable:
        if not cli.get_confirmation(
            f"Reset profile {closest_match} to defaults? This will overwrite the file."
        ):
            print("Aborting.")
            return

    profile.safe_write(profile_path)
    print(f"Profile {closest_match} repaired.")


def is_valid_profile_name(
    config: cfg.Config, profile_name: str, allow_reserved: bool = False
) -> tuple[bool, str]:
    """
    Verify the profile name isn't empty or already in use.
    Normally reject reserved names, but allow them if specified.

    :param config: The config object.
    :param profile_name: The name of the profile.
    :param allow_reserved: Allow reserved names.
    :return: True if valid, False otherwise, and a message.
    """
    if not profile_name:
        return False, tr("Profile name cannot be empty.")
    if profile_name in config.saved_profiles.keys():
        return False, tr("Profile name already in use.")
    if profile_name.lower() in config.reserved_profile_names() and not allow_reserved:
        return False, tr("Profile name is reserved.")
    return True, ""


def purge_missing_profiles(config: cfg.Config, gui: bool = False) -> None:
    """
    Remove profiles from the config that no longer exist.

    :param config: The config object.
    :param gui: When True, don't print anything.
    """
    purged = False
    for profile_name, profile_path in list(config.saved_profiles.items()):
        if not profile_path.is_file():
            config.remove_profile(profile_name)
            purged = True
    if purged:
        config.save()
        if not gui:
            print("Purged missing profiles.")
