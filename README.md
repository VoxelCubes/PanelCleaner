# Panel Cleaner

[![License: GPL v3](https://img.shields.io/badge/License-GPL%20v3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)
[![PyPI version](https://img.shields.io/pypi/v/pcleaner)](https://pypi.org/project/pcleaner/)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

This tool uses machine learning to find text and then generates masks to cover it up with the highest accuracy possible. It is designed to clean easy bubbles, no in-painting or out-of-bubble text removal is done. This is intended to save a lot of monotonous work for people who have to clean a lot of panels, while making sure it doesn't paint over anything that it wasn't supposed to.

![Example](https://raw.githubusercontent.com/VoxelCubes/PanelCleaner/master/media/spread.png)

Visualized in the top right page: 

- Various boxes are drawn where the AI found text. 

- (Green) The AI also generates a precise mask where it detected text. 

- (Purple) These masks are expanded to cover any nearby text that wasn't detected, as well as jpeg artifacts.

- (Blue) For masks that are a tight fit, the border around the edge of the mask is denoised for final clean-up, without affecting the rest of the image.

The two bottom pages are what the program can output: either just the transparent mask layer and/or the mask applied to the original image, cleaning it.

## Contents
> [Features](#features) \
> [Limitations](#limitations) \
> [Why Use This Program?](#why-use-this-program) \
> [Installation](#installation) \
> [Usage](#usage) \
> [Profiles](#profiles) \
> [OCR](#ocr) \
> [Examples](#examples-of-tricky-bubbles) \
> [Acknowledgements](#acknowledgements) \
> [License](#license) \
> [Roadmap](#roadmap)


## Features

- Cleans text bubbles without leaving artifacts.

- Avoids painting over parts of the image that aren't text.

- Ignores bubbles containing only symbols or numbers, as those don't need translation.

- Offers a plethora of options to customize the cleaning process and the ability to save multiple presets as profiles.
  See the [default profile](https://github.com/VoxelCubes/PanelCleaner/blob/master/media/default.conf) for a list of all options.

- Provides detailed analytics on the cleaning process, to see how your settings affect the results.

- Supports CUDA acceleration, if your hardware supports it.

- Supports batch processing of images and directories.

- Can handle bubbles on any solid grayscale background color.

- Can also run OCR on the pages and output the text to a file.


## Limitations

- It only supports Japanese and English text.

- The program relies on AI for the initial text detection, which by nature is imperfect. Sometimes it will miss little bits of text or think part of the bubble belongs to the text, which will prevent that bubble from being cleaned. From testing, this typically affects between 2–8% of bubbles, depending on your settings.

- Due to the conservative approach taken in the selection of masks, if the program can't clean the bubble to a satisfying degree, it will skip that bubble outright. This does, however, also prevent false positives.

- For masks, only grayscale is currently supported. This means it can cover up text in white, black, or gray bubbles, but not colored ones.


## Why Use This Program?

This program is designed to precisely and fully clean text bubbles, without leaving any artifacts.
Its aim is to save a cleaner's time, by taking care of monotonous work.
The [AI](https://github.com/dmMaze/comic-text-detector) used to detect text and generate the initial mask was *not* created as part of this project, this project merely uses it as a starting point and improves upon the output.

| Original                             | AI Output                           | Panel Cleaner                          |
|:------------------------------------:|:-----------------------------------:|:--------------------------------------:|
| ![Original](https://raw.githubusercontent.com/VoxelCubes/PanelCleaner/master/media/demo_original.png) | ![AI Output](https://raw.githubusercontent.com/VoxelCubes/PanelCleaner/master/media/demo_ai_raw.png) | ![Panel Cleaner](https://raw.githubusercontent.com/VoxelCubes/PanelCleaner/master/media/demo_clean.png) |

As you can see, with a bit of extra cleanup applied to the AI output, some leftover text and jpeg compression artifacts are removed, and the bubble is fully cleaned. \
When fully cleaning it isn't possible, Panel Cleaner will instead skip the bubble so as not to waste your time with a poorly cleaned bit of text. The exact cleaning behavior is highly configurable, see [Profiles](#profiles) for more details.


## Installation

The program requires **Python 3.10** or newer.

Install the program with pip from [PyPI](https://pypi.org/project/pcleaner/):
```bash
pip install pcleaner
```

Note: The program has only been tested on Linux and on Windows with WSL, but should work on Windows (natively) and Mac as well.


## Usage

The program is run from the command line, and, in the most common use, takes any number of images or directories as input. The program will create a new directory called `cleaned` in the same directory as the input files, and place the cleaned images and/or masks there. Often, it's more useful to only export the mask layer, and you can do so by adding the `--save-only-mask`, or `-m` for short, option.

Examples:
```bash
pcleaner clean image1.png image2.png image3.png

pcleaner clean -m folder1 image1.png
```

Demonstration with 46 images, real time, with CUDA acceleration.
![Demonstration](https://raw.githubusercontent.com/VoxelCubes/PanelCleaner/master/media/pcleaner_demo.gif)

There are many more options, which can be seen by running
```bash
pcleaner --help
```


## Profiles

The program exposes every setting possible in a configuration profile, which are saved as simple text files. Each configuration option is explained inside the file itself, allowing you to optimize each parameter of the cleaning process for your specific needs. \
Just generate a new profile with
```bash
pcleaner profile new my_profile_name_here
```

and it will open your new profile for you in a text editor. \
Here is a tiny snippet from the default profile, for example:
```ini
# Number of pixels to grow the mask by each step. 
# This bulks up the outline of the mask, so smaller values will be more accurate but slower.
mask_growth_step_pixels = 2

# Number of steps to grow the mask by.
# A higher number will make more and larger masks, ultimately limited by the reference box size.
mask_growth_steps = 11
```

Run the cleaner with your specified profile by adding `--profile=my_profile_name_here` or
`-p my_profile_name_here` to the command.

If you are having trouble seeing how the settings affect the results, you can use the 
`--cache-masks` option to save visualizations of intermediate steps to the cache directory.

| Default Profile                                | Custom Profile                              |
| ---------------------------------------------- | ------------------------------------------- |
| ![Default Profile](https://raw.githubusercontent.com/VoxelCubes/PanelCleaner/master/media/profile_original.png) | ![Custom Profile](https://raw.githubusercontent.com/VoxelCubes/PanelCleaner/master/media/profile_modded.png) |
| mask_growth_step_pixels = 2                    | mask_growth_step_pixels = 4                 |
| mask_growth_steps = 11                         | mask_growth_steps = 4                       |

Additionally, analytics are provided for each processing step in the terminal, so you can see how your settings affect the results on a whole.

See the [default profile](https://github.com/VoxelCubes/PanelCleaner/blob/master/media/default.conf) for a list of all options.

Note: The default profile is optimized for images roughly 1100x1600 pixels in size.
Adjust size parameters accordingly in a profile if you are using images with a significantly
lower or higher resolution.


## OCR

You can also use Panel Cleaner to perform Optical Character Recognition (OCR) on the pages,
and output the text to a file. This could be useful to assist in translation, or to extract
text for analytical purposes. \
You can run OCR with:
```bash
pcleaner ocr myfolder --output-path=output.txt
```


## Examples of Tricky Bubbles

| Original | Cleaned |
|:--------:|:-------:|
| ![Square bubble raw](https://raw.githubusercontent.com/VoxelCubes/PanelCleaner/master/media/demo_bubbles/square_bubble_raw.png) | ![Square bubble clean](https://raw.githubusercontent.com/VoxelCubes/PanelCleaner/master/media/demo_bubbles/square_bubble_clean.png) |
| ![Handwritten bubble raw](https://raw.githubusercontent.com/VoxelCubes/PanelCleaner/master/media/demo_bubbles/handwritten_bubble_raw.png) | ![Handwritten bubble clean](https://raw.githubusercontent.com/VoxelCubes/PanelCleaner/master/media/demo_bubbles/handwritten_bubble_clean.png) |
| ![Black bubble raw](https://raw.githubusercontent.com/VoxelCubes/PanelCleaner/master/media/demo_bubbles/black_bubble_raw.png) | ![Black bubble clean](https://raw.githubusercontent.com/VoxelCubes/PanelCleaner/master/media/demo_bubbles/black_bubble_clean.png) |
| ![Ray bubble raw](https://raw.githubusercontent.com/VoxelCubes/PanelCleaner/master/media/demo_bubbles/ray_bubble_raw.png) | ![Ray bubble clean](https://raw.githubusercontent.com/VoxelCubes/PanelCleaner/master/media/demo_bubbles/ray_bubble_clean.png) |
| ![Nightmare bubble raw](https://raw.githubusercontent.com/VoxelCubes/PanelCleaner/master/media/demo_bubbles/nightmare_bubble_raw.png) | ![Nightmare bubble clean](https://raw.githubusercontent.com/VoxelCubes/PanelCleaner/master/media/demo_bubbles/nightmare_bubble_clean.png) |
| ![Spikey bubble raw](https://raw.githubusercontent.com/VoxelCubes/PanelCleaner/master/media/demo_bubbles/spikey_bubble_raw.png) | ![Spikey bubble clean](https://raw.githubusercontent.com/VoxelCubes/PanelCleaner/master/media/demo_bubbles/spikey_bubble_clean.png) |
| ![Darkrays bubble raw](https://raw.githubusercontent.com/VoxelCubes/PanelCleaner/master/media/demo_bubbles/darkrays_bubble_raw.png) | ![Darkrays bubble clean](https://raw.githubusercontent.com/VoxelCubes/PanelCleaner/master/media/demo_bubbles/darkrays_bubble_clean.png) |



## Acknowledgements

- [Comic Text Detector](https://github.com/dmMaze/comic-text-detector) for finding text bubbles and generating the initial mask.

- [Manga OCR](https://github.com/kha-white/manga-ocr) for detecting which bubbles only contain symbols or numbers,
  and performing the dedicated OCR command.


## License

This project is licensed under the GNU General Public License v3.0 – see
the [LICENSE](https://raw.githubusercontent.com/VoxelCubes/PanelCleaner/master/LICENSE) file for details.


## Roadmap

Maybe make a GUI for it.
