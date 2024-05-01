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

## It won't start on Windows, something about "Magic"?

You can try swapping out the python magic package (image manipulation library) with the following command:

```bash
pip uninstall python-magic
pip install python-magic-bin
```

## Will profiles I set up with the CLI work with the GUI?

Yes, they will. The GUI is just a wrapper around the CLI, so it will use the same profiles.


## This specific image causes an error, what do I do?

Please open an issue on Github and attach the image in question as well as your log file. You can find it by clicking
the "Open Log" button in the gui, or going to the folder `~/.cache/pcleaner` on Linux/MacOS or `%APPDATA%\pcleaner\cache` on Windows.

Without both of those I cannot help you.


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
