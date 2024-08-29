"""
The whole point of this file is to extract the profile strings from the default profile,
such that Qt Linguist can properly parse them with adequate context.

The generated code will not run, it's just a helper to generate the .ts files.

This is done because integrating this into the actual source code would degrade the readability
tremendously, and also provide far worse context for the translators.

This way, we hook into the same parser that the GUI uses, and extract the strings from there,
such that they are already in the correct format the GUI will display them in.
That avoids making translators deal with the # characters and wrapping lines in any way.
Then we can simply intercept the strings on the GUI layer to translate them.

This file needs to be run before the Makefile action that refreshes the source .ts file.
"""

from io import StringIO
from datetime import datetime
from pathlib import Path

from attrs import define

import pcleaner.config as cfg
import pcleaner.gui.profile_parser as pp
import pcleaner.ocr.supported_languages as osl


@define
class ProfileString:
    """
    A comment/section/entry inside the profile that will be opened up to i18n.
    For that, we need the text, the section, and the type.
    """

    text: str
    type: str
    section: str


def extract_profile_strings(profile_structure: list[pp.ProfileSection]) -> list[ProfileString]:
    """
    Extracts all the strings from the default profile.
    """
    profile_strings: list[ProfileString] = []
    for section in profile_structure:
        """
        These consist of a name and a list of comments and entries. We ignore the entries.
        """
        current_section = pp.to_display_name(section.name)

        profile_strings.append(ProfileString(current_section, "Profile section title", ""))
        for item in section.items:
            if isinstance(item, pp.ProfileComment):
                profile_strings.append(
                    ProfileString(
                        item.comment.replace("'", "\\'"), "Profile comment in ", current_section
                    )
                )
            elif isinstance(item, pp.ProfileEntry):
                profile_strings.append(
                    ProfileString(
                        pp.to_display_name(item.key), "Profile entry in ", current_section
                    )
                )
            # The remaining case is a space, which we ignore.

    return profile_strings


def extract_language_names() -> list[str]:
    """
    Grab the language names from ocr/supported_languages.py.

    :return: List of language names.
    """
    return list(osl.LANGUAGE_CODE_TO_NAME.values())


def bogus_codegen(profile_strings: list[ProfileString], language_names: list[str]) -> str:
    """
    Construct a fake Python file that contains translation function calls for all the profile strings.
    This way Qt Linguist can add them to its .ts file with additional context.

    :param profile_strings: List of profile strings to generate code for.
    :param language_names: List of language names to generate code for.
    :return: Generated code.
    """
    buffer = StringIO()

    buffer.write(
        f"""\
# -*- coding: utf-8 -*-
#########################################################################################
# Strings gathered from the default profile in pcleaner/config.py
# This file is not meant to be run, it's just a helper to generate the .ts files.
#
# Created by pcleaner/translations/profile_extractor.py on {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
#
# WARNING! All changes made in this file will be lost when the .ts files are refreshed!
#########################################################################################

from PySide6.QtCore import QCoreApplication
\n\n"""
    )

    for profile_string in profile_strings:
        buffer.write(
            f"QCoreApplication.translate('Profile', '{profile_string.text}', '{profile_string.type}{profile_string.section}')\n\n"
        )

    for language_name in language_names:
        buffer.write(
            f"QCoreApplication.translate('Profile', '{language_name}', 'Language option for OCR')\n\n"
        )

    return buffer.getvalue()


def main() -> None:
    """
    Extracts all the strings from the default profile.
    """
    profile = cfg.Profile()
    profile_structure = pp.parse_profile_structure(profile)
    profile_strings = extract_profile_strings(profile_structure)
    language_names = extract_language_names()
    code = bogus_codegen(profile_strings, language_names)
    # Write the file right next to this one, no matter the current working directory.
    output_file = Path(__file__).parent / "profile_strings.py"
    output_file.write_text(code, encoding="utf-8")


if __name__ == "__main__":
    main()
