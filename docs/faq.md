# Frequently Asked Questions

## Is CUDA worth it?

If you have a CUDA-capable GPU, then yes, it is worth it. The speedup is significant, approximately
2–3x faster than the CPU version. However, the CPU version is still rather quick, needing less than a minute
for 40 pages, depending on hardware. 

If you plan to use OCR primarily, CUDA is highly recommended though, here you will see a speedup of 4–5x.

### If CUDA is so good, why don't you offer a prebuilt binary?

The problem with CUDA is that the required libraries are very large, especially if you want to support
multiple CUDA versions. This would place the final executable at 5+ Gigabytes, which Github will not allow me
to upload under their 2 Gigabyte limit.

Feel free to download the source code and build your own CUDA version, I have left the necessary build files for it. 

You will need to have a python virtual environment set up (e.g. using Pycharm or done manually), install the requirements and then run the following command:

On Linux (pytorch installs with cuda support by default):
```bash
make build-elf
```

On Windows (after ensuring you have the CUDA enabled version of pytorch installed, and your virtual environment is a folder named venv-cuda):
```bash
.\build-pyinstaller-cuda.bat
```

You will find the output in the dist_elf or dist_exe_cuda folders respectively.

Please do not ask for more help with this, that is all I can provide.

## CUDA isn't working, what do I do?

First, make sure you have a CUDA-capable GPU installed and that you have CUDA support
in your installation on pytorch. You can check this by running the following python script:

```python
import torch
print(torch.cuda.is_available())
```

If this returns `False`, then you can try reinstalling pytorch with the correct CUDA version
for your system. First, uninstall pytorch:

```bash
pip uninstall torch torchvision
```

Then, follow the instructions on the [pytorch website](https://pytorch.org/get-started/locally/)
to find the right command, typically something like:

```bash
pip3 install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
```
(`torchaudio` may be omitted)
This should download around 2 Gigabytes of data, so be patient, then try running `pcleaner` again.


## Will profiles I set up with the CLI work with the GUI?

Yes, they will. The GUI is just a wrapper around the CLI, so it will use the same profiles.


## This specific image causes an error, what do I do?

Please open an issue on Github and attach the image in question as well as your log file. You can find it by clicking
the "Open Log" button in the gui, or going to the folder `~/.cache/pcleaner` on Linux/MacOS or `%APPDATA%\pcleaner\cache` on Windows.

Without both of those I cannot help you.


## The cleaner is getting rid of things that are in my OCR blacklist!

The cleaner has the option to skip bubbles that contain text that doesn't need cleaning.
It checks two different things: the text itself, and the bounding box of the text.
Both are configurable in the profile:
- OCR Max Size: The maximum size of a bubble that will be skipped.
- OCR Blacklist Pattern: A regex pattern that must match the text if it is to be skipped.

You can check if this is working as intended by running OCR in csv mode.
This will output, for example, the following for one of the bubbles:
```
test.png,380,1700,480,1750,．．．！！
```
As a table, this data means the following:

|filename|startx|starty|endx|endy|text
|---|---|---|---|---|---|
test.png|380|1700|480|1750|．．．！！

Note: If the text it claims to have found makes no sense, for example, it just reads "．．．", for something
entirely different, check what OCR language is set. The default MangaOCR model might return something like that
for English text, resulting in it getting ignored, if the bubble was small enough.

### Checking bubble size

If the text was removed during cleaning, when you think it shouldn't, check if the OCR Max Size is set too low.
To calculate the box size, you first need to check the scale being used to process the image.
This is visible in the main table of the GUI, seen here:

![Processing size](https://raw.githubusercontent.com/VoxelCubes/PanelCleaner/master/media/screenshots/processing_size.png) 

This is influenced by the profile settings in General: Input Height Lower Target and Input Height Upper Target.
The scaled image size is what is used to calculate the box size, so you need to multiply the box size by the scale to get the actual size.

To calculate the size of the box, use this formula:

$$
\text{box size} = (\text{endx} - \text{startx}) \times (\text{endy} - \text{starty})
$$

Then to correct for the scale factor, if it isn't 100%:

$$
\text{actual box size} = \text{box size} \times \left(\frac{\text{processing size percentage}}{100}\right)^2
$$

For example, we would calculate the box size as: $(480 - 380) \times (1750 - 1700) = 100 \times 50 = 5000$.
The default OCR Max Size is 3000, so this bubble will be cleaned.

If we had a scale factor of 50%, we would adjust the size: $5000 \times \left(\frac{50}{100}\right)^2 = 5000 \times 0.25 = 1250$.
If this image was actually scaled down to 50%, then the bubble size would qualify for skipping.

### Checking blacklist pattern

To check the second condition, the blacklist pattern, you can use a website such as [regex101](https://regex101.com/)
(You may need to select the "Python" flavor of regex, once there.)

Then copy your OCR Blacklist Pattern into the "Regular Expression" field, and the text of your bubble into the "Test String" field.
By default, the pattern is `[～．ー！？０-９~.!?0-9-]*`, and in our case, the text is `．．．！！`.

If the text gets fully highlighted, then it works! If not, you may need to adjust the pattern.
But remember that the size condition must also be met for the bubble to be skipped.

In the example case, the text was being cleaned because the size was too large, if processing at 100% scale.
Therefore, adjusting the OCR Max Size to 5001 would allow the bubble to be skipped. But a larger margin is recommended,
such as 10000, or even larger like 999999999 to effectively disable the check. **But be warned that doing so will perform
OCR on all bubbles, which will slow down cleaning times significantly.**

## dbus cannot be installed in WSL2, what do I do?

There is a simple workaround for this: simply downgrading the package.

First ensure it isn't installed:
```bash
pip uninstall dbus-python
```

Then install the older version:
```bash
dbus-python==1.2.18
```

Now you can attempt to install `pcleaner` again.

## How can I install the OCR model manually?

First off, don't do this unless you have a good reason to. It's a little more work than simply downloading a file,
the way it works for the text detection and inpainting models.

To begin, download only these model files from the [huggingface website](https://huggingface.co/kha-white/manga-ocr-base/tree/main):
```
config.json
preprocessor_config.json
pytorch_model.bin
special_tokens_map.json
tokenizer_config.json
vocab.txt
```

Next, figure out where your huggingface cache is located. This is typically `~/.cache/huggingface` on Linux/MacOS and `%APPDATA%\.cache/huggingface` on Windows.

You can also use the environment variable `XDG_CACHE_HOME` to change the exact location of the `.cache` directory. \
Note: Changing this will affect where the other model data and logs, as well as intermediate files, are stored.

Once you have the files, create a directory structure like this:
```
huggingface
└── hub
   ├── models--kha-white--manga-ocr-base
   │  ├── refs
   │  │  └── main
   │  └── snapshots
   │     └── aa6573bd10b0d446cbf622e29c3e084914df9741
   │        ├── config.json
   │        ├── preprocessor_config.json
   │        ├── pytorch_model.bin
   │        ├── special_tokens_map.json
   │        ├── tokenizer_config.json
   │        └── vocab.txt
   └── version.txt
```
The `version.txt` contains this:
```
1
```
And the `main` file contains this:
```
aa6573bd10b0d446cbf622e29c3e084914df9741
```

Note: The `aa6573bd10b0d446cbf622e29c3e084914df9741` is the git commit hash of the model, basically, it marks the current version.
