:: On Windows, pip is too retarded to install the CUDA variants of pytorch correctly, so here is
:: the manual way, using CUDA 11 for compatibility.
:: See https://pytorch.org/get-started/locally/#windows-pip for more info.
:: First ensure the regular torch is uninstalled.
.\venv-cuda\Scripts\pip uninstall torch torchvision -y
.\venv-cuda\Scripts\pip install torch torchvision --index-url https://download.pytorch.org/whl/cu118