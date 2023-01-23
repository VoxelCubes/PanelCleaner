# Panel Cleaner

This tool uses machine learning to find text and then generates masks to cover it up with the highest accuracy possible. It is designed to clean easy bubbles, no in-painting or out-of-bubble text removal is done. This is intended to save a lot of monotonous work for people who have to clean a lot of panels, while making sure it doesn't paint over anything that it wasn't supposed to.

![Example](https://raw.githubusercontent.com/VoxelCubes/PanelCleaner/master/media/spread.png)

Visualized in the middle panel: 

- Various boxes are drawn where the AI found text. 

- (Green) The AI also generates a precise mask where it detected text. 

- (Purple) These masks are expanded to cover any nearby text that wasn't detected, as well as jpeg artifacts.

- (Blue) For masks that are a tight fit, the border around the edge of the mask is denoised for final clean-up, without affecting the rest of the image.

## Features

- Cleans text bubbles without leaving artifacts.

- Avoids painting over parts of the image that aren't text.

- Ignores bubbles containing only symbols or numbers, as those don't need translation.

- Works for many languages.

- Offers a plethora of options to customize the cleaning process and the ability to save multiple presets as profiles.

- Provides detailed analytics on the cleaning process, to see how your settings affect the results.

- Supports CUDA acceleration, if your hardware supports it.

- Supports batch processing of images and directories.

- Can handle bubbles on any solid grayscale background color.

## Shortcomings

- The program relies on AI for the initial text detection, which by nature is imperfect. Sometimes it will miss little bits of text or think part of the bubble belongs to the text, which will prevent that bubble from being cleaned. From testing, this typically affects between 2–8% of bubbles, depending on your settings.

- Due to the conservative approach taken in the selection of masks, if the program can't clean the bubble to a satisfying degree, it will skip that bubble outright. This does, however, also prevent false positives.

- For masks, only grayscale is currently supported. This means it can cover up text in white, black, or gray bubbles, but not colored ones.

## Why Use This Program Instead of Other Tools?

This program is designed to precisely and fully clean text bubbles, without leaving any artifacts. 
The [AI](https://github.com/dmMaze/comic-text-detector) used to detect text and generate the initial mask was *not* created as part of this project, this project merely uses it as a starting point and improves upon the output.

| Original                             | AI Output                           | Panel Cleaner                          |
|:------------------------------------:|:-----------------------------------:|:--------------------------------------:|
| ![Original](https://raw.githubusercontent.com/VoxelCubes/PanelCleaner/master/media/demo_original.png) | ![AI Output](https://raw.githubusercontent.com/VoxelCubes/PanelCleaner/master/media/demo_ai_raw.png) | ![Panel Cleaner](https://raw.githubusercontent.com/VoxelCubes/PanelCleaner/master/media/demo_clean.png) |

As you can see, with a bit of extra cleanup applied to the AI output, some leftover text and jpeg compression artifacts are removed, and the bubble is fully cleaned.

## Installation

The program requires **Python 3.10** or newer.

Install the program with pip from PyPI:

```
pip install pcleaner
```

Note: The program has only been tested on Linux and on Windows with WSL, but should work on Windows (natively) and Mac as well.

## Usage

The program is run from the command line, and, in the most common use, takes any number of images or directories as input. The program will create a new directory called `cleaned` in the same directory as the input files, and place the cleaned images and/or masks there.

Examples:

```
pcleaner clean image1.png image2.png image3.png

pcleaner clean folder1 image1.png
```

Demonstration with 46 images, real time, with CUDA acceleration.
![Demonstration](https://raw.githubusercontent.com/VoxelCubes/PanelCleaner/master/media/pcleaner_demo_compressed.gif)

There are many more options, which can be seen by running

```
pcleaner --help
```

## Profiles

The program exposes every setting possible in a configuration profile, which are saved as simple text files. Each configuration option is explained inside the file itself, allowing you to optimize each parameter of the cleaning process for your specific needs. \
Just generate a new profile with

```
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

Note: The default profile is optimized for images roughly 1100x1600 pixels in size.
Adjust size parameters accordingly in a profile if you are using images with a significantly
lower or higher resolution.

## Acknowledgements

- [Comic Text Detector](https://github.com/dmMaze/comic-text-detector) for finding text bubbles and generating the initial mask.

- [Manga OCR](https://github.com/kha-white/manga-ocr) for detecting which bubbles only contain symbols or numbers.

## License

This project is licensed under the GNU General Public License v3.0 – see the [LICENSE](LICENSE) file for details.

## Roadmap

Maybe make a GUI for it.
