from pathlib import Path

import prettytable as pt

import pcleaner.cli_utils as cli
import pcleaner.config as cfg


def list_profiles(config: cfg.Config):
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

    def check_path(path: Path):
        if path.exists():
            return "OK"
        else:
            return "File not found"

    def check_default(profile: str | None):
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
            cfg.RESERVED_PROFILE_NAMES[0],
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


def new_profile(config: cfg.Config, profile_name: str, profile_path: str | None):
    """
    Create a new profile with the given name and path.

    :param config: The config object.
    :param profile_name: The name of the profile.
    :param profile_path: The path to the profile.
    """
    if not is_valid_profile_name(config, profile_name):
        return

    # If no path is given, use the default path.
    if profile_path is None:
        profile_path = cli.get_config_path().parent / "profiles" / f"{profile_name}.conf"
    else:
        profile_path = Path(profile_path)
        # If the path is a directory, append a default filename.
        if profile_path.is_dir():
            profile_path = profile_path / f"{profile_name}.conf"

    # Check if overwriting an existing file.
    if profile_path.exists():
        if not cli.get_confirmation(f"Overwrite existing file {profile_path}?"):
            print("Aborting.")
            return

    profile_path.parent.mkdir(parents=True, exist_ok=True)
    # Create the profile file from the built-in default.
    profile = cfg.Profile()
    profile.write(profile_path)
    print(f"Profile {profile_name} created at {profile_path}.")

    # Add the profile to the config.
    config.add_profile(profile_name, profile_path)
    config.save()

    open_profile(config, profile_name)


def add_profile(config: cfg.Config, profile_name: str, profile_path: str):
    """
    Add a profile to the config.

    :param config: The config object.
    :param profile_name: The name of the profile.
    :param profile_path: The path to the profile file.
    """
    if not is_valid_profile_name(config, profile_name):
        return

    # Verify the profile path exists.
    profile_path = Path(profile_path)
    if not profile_path.is_file():
        print("Profile file not found.")
        return

    # Add the profile to the config.
    config.add_profile(profile_name, profile_path)
    config.save()

    print(f"Profile {profile_name} added.")


def open_profile(config: cfg.Config, profile_name: str):
    """
    Open the profile in the default editor, unless specified in the config.

    :param config: The config object.
    :param profile_name: The name of the profile.
    :return:
    """
    profile_path = config.saved_profiles[profile_name]
    cli.open_file_with_editor(profile_path, config.profile_editor)


def delete_profile(config: cfg.Config, profile_name: str):
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


def set_default_profile(config: cfg.Config, profile_name: str):
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


def repair_profile(config: cfg.Config, profile_name: str):
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

    # If it wasn't salvageable, ask before overwriting.
    if not_salvageable:
        if not cli.get_confirmation(
            f"Reset profile {closest_match} to defaults? This will overwrite the file."
        ):
            print("Aborting.")
            return

    profile.write(profile_path)
    print(f"Profile {closest_match} repaired.")


def is_valid_profile_name(
    config: cfg.Config, profile_name: str, allow_reserved: bool = False
) -> bool:
    """
    Verify the profile name isn't empty or already in use.
    Normally reject reserved names, but allow them if specified.

    :param config: The config object.
    :param profile_name: The name of the profile.
    :param allow_reserved: Allow reserved names.
    :return: True if valid, False otherwise.
    """
    if not profile_name:
        print("Profile name cannot be empty.")
        return False
    if profile_name in config.saved_profiles.keys():
        print("Profile name already in use.")
        return False
    if profile_name.lower() in cfg.RESERVED_PROFILE_NAMES and not allow_reserved:
        print("Profile name is reserved.")
        return False
    return True


def purge_missing_profiles(config: cfg.Config):
    """
    Remove profiles from the config that no longer exist.

    :param config: The config object.
    """
    purged = False
    for profile_name, profile_path in list(config.saved_profiles.items()):
        if not profile_path.is_file():
            config.remove_profile(profile_name)
            purged = True
    if purged:
        config.save()
        print("Purged missing profiles.")
