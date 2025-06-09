"""
The whole point of this file is to extract the process step strings from the image file,
such that Qt Linguist can properly parse them with adequate context.

The generated code will not run, it's just a helper to generate the .ts files.

This is done because integrating this into the actual source code would degrade the readability
tremendously, and also provide far worse context for the translators.

This file needs to be run before the Makefile action that refreshes the source .ts file.
"""

from io import StringIO
from datetime import datetime
from pathlib import Path

from attrs import define

import pcleaner.gui.image_file as imf
import pcleaner.output_structures as ost
import pcleaner.gui.profile_parser as pp


@define
class ProcessString:
    """
    Strings extracted from the process pipeline.
    description, step name, output name
    """

    description: str
    step_name: str | None
    output_name: str | None


def extract_step_strings(outputs: dict[ost.Output, imf.ProcessOutput]) -> list[ProcessString]:
    """
    Extracts all the strings from the process pipeline.
    """
    process_strings: list[ProcessString] = []
    for output, process_output in outputs.items():
        if process_output.description == "Not visible":
            continue
        process_strings.append(
            ProcessString(
                process_output.description.replace("\n", "\\n"),
                process_output.step_name,
                (
                    process_output.output_name
                    if process_output.output_name is not None
                    else pp.to_display_name(output.name)
                ),
            )
        )
    return process_strings


def bogus_codegen(process_strings: list[ProcessString]) -> str:
    """
    Construct a fake Python file that contains translation function calls for all the process strings.
    This way Qt Linguist can add them to its .ts file with additional context.

    :param process_strings: The process strings to generate code for.
    :return: Generated code.
    """
    buffer = StringIO()

    buffer.write(
        f"""\
# -*- coding: utf-8 -*-
#########################################################################################
# Strings gathered from the image file outputs in pcleaner/gui/image_file.py.
# This file is not meant to be run, it's just a helper to generate the .ts files.
#
# Created by pcleaner/translations/process_step_extractor.py on {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
#
# WARNING! All changes made in this file will be lost when the .ts files are refreshed!
#########################################################################################

from PySide6.QtCore import QCoreApplication
\n\n"""
    )

    # deduplicate process steps.
    step_names_seen: set[str] = set()
    # deduplicate output names.
    output_names_seen: set[str] = set()

    for process_string in process_strings:
        buffer.write(
            f"QCoreApplication.translate('Process Steps', '{process_string.description}',"
            f" 'Step description in the image details view, step: {process_string.step_name},"
            f" output: {process_string.output_name}')\n"
        )
        if process_string.step_name is not None and process_string.step_name not in step_names_seen:
            step_names_seen.add(process_string.step_name)
            buffer.write(
                f"QCoreApplication.translate('Process Steps', '{process_string.step_name}',"
                f" 'Step name in the image details view')\n"
            )
        if (
            process_string.output_name is not None
            and process_string.output_name not in output_names_seen
        ):
            output_names_seen.add(process_string.output_name)
            buffer.write(
                f"QCoreApplication.translate('Process Steps', '{process_string.output_name}',"
                f" 'Output name in the image details view')\n"
            )
        buffer.write("\n")

    return buffer.getvalue()


def main() -> None:
    """
    Extracts all the strings from the default profile.
    """
    image_file = imf.ImageFile(Path("nothing.png"))
    process_outputs = image_file.outputs
    # This step name is used only in the progress bar and is not included in "pcleaner/gui/image_file.py",
    # but since it still needs to be translated, we need to manually squeeze it in here.
    process_outputs[ost.Output.write_output] = imf.ProcessOutput(
        "<This is just a placeholder, translating this string is not necessary>",
        None,
        "Write Output",
    )

    process_strings = extract_step_strings(process_outputs)
    code = bogus_codegen(process_strings)
    # Write the file right next to this one, no matter the current working directory.
    output_file = Path(__file__).parent / "process_strings.py"
    output_file.write_text(code, encoding="utf-8")


if __name__ == "__main__":
    main()
