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

Please open an issue on Github and attach the image in question as well as your log file. You can find it by clicking the "Open Log" button in the gui, or going to the folder `~/.cache/pcleaner` on Linux/MacOS or `%APPDATA%\pcleaner\cache` on Windows.

Without both of those I cannot help you.