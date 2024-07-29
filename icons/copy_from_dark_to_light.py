#!/usr/bin/python

import os


def simple_replace_color_in_svg(input_folder, output_folder, old_color, new_color) -> None:
    # Ensure the output folder exists
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    # Loop through all the SVG files in the input folder
    for svg_file in os.listdir(input_folder):
        if svg_file.endswith(".svg"):
            # Construct the full path to the SVG file
            input_path = os.path.join(input_folder, svg_file)

            # Read the SVG file as a text
            with open(input_path, "r") as f:
                file_content = f.read()

            # Replace the color
            modified_content = file_content.replace(old_color, new_color)

            # Construct the full path to the output SVG file
            output_path = os.path.join(output_folder, svg_file)

            # Write the modified SVG back to a new file
            with open(output_path, "w") as f:
                f.write(modified_content)


# Define parameters
input_folder = "pcleaner/data/custom_icons/dark"
output_folder = "pcleaner/data/custom_icons/light"
old_color = "#fcfcfc"
new_color = "#232629"

# Run the function
simple_replace_color_in_svg(input_folder, output_folder, old_color, new_color)
