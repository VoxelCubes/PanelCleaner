# PanelCleaner Testbed

## Overview

The **PanelCleaner** testbed is a specialized environment designed for experimenting with and testing enhancements to the **PanelCleaner** software, particularly through the use of Jupyter Notebooks. Currently, the focus of this testbed is on OCR technologies, with a special emphasis on evaluating and comparing the performance of **Tesseract** and **IDefics** and other recent so-called AI models, multimodal generative language models with visual capabilities.

This is not only a platform for practical application testing, also serves as a development space for an evolving evaluation framework. This framework is intended to rigorously check the effectiveness of OCR and other technologies in various scenarios and aim to support the continuous improvement of **PanelCleaner**.

Additionally, the testbed leverages the `nbdev` literate programming environment.


## Installation

To begin using the **PanelCleaner** testbed, you will need an environment capable of running Jupyter Notebooks, such as Jupyter Lab or Notebook, VSCode, or Google Colab. The setup shares common requirements with the main **PanelCleaner** software, along with a few additional dependencies specific to the testbed.

### Setting up your local environment

Follow these steps to set up your environment from scratch:

1. **Clone the repo and switch to the testbed branch:**
   ```bash
   gh repo clone civvic/PanelCleaner
   cd PanelCleaner
   git pull origin testbed
   git switch testbed
   ```

2. **Create and activate a virtual environment:**
   ```bash
   virtualenv -p python3.10 venv
   . venv/bin/activate
   ```

3. **Install the PanelCleaner package and testbed requirements:**
   ```bash
   pip install -e .
   cd pcleaner/_testbed
   pip install -r requirements.txt
   pip install -r requirements-idefics.txt
   ```

4. **Download and unzip the experiment images:**
   ```bash
   gdown --id 1MCqUImwFS5iQ271CD9_t2FSugJXdYj0a -O experiment.zip
   unzip -qn experiment.zip -d .
   ```

5. **Launch Jupyter Lab/Notebook** with the provided local URLs
   ```bash
   jupyter lab --no-browser
   ```

6.  or **Open directly the notebooks in VSCode**.


### Note:
- Each notebook may require the installation of additional dependencies not covered in the initial setup. Ensure to check the specific requirements within each notebook.  

- Jupyter (or VSCode) set the current working directory to the one that contains the launched notebook. Most of the links contained inside each notebook are relative to this working directory.


## Google Colab support

The notebooks are (or should be) fully compatible with Google Colab, enabling you to run them directly on the platform without requiring any local computational resources. This is particularly beneficial for us GPU-poor who do not have access to local GPU capabilities.


### Getting started with Google Colab

1. **Accessing the notebooks:**
   - Upload the notebook files to your Google Drive.
   - Open Google Colab and use the `File` menu to locate and open the notebooks from your Google Drive.
   - Or better yet, install a local dev of PanelCleaner in your Google Drive and open the notebooks from there.

2. **Setting up the environment:**
   - Most dependencies should be pre-installed on Google Colab, but you may need to install specific packages relevant to the **PanelCleaner** testbed. This can be done directly within the notebook using `!pip install` commands.

3. **Running the notebooks:**
   - Execute the cells sequentially by pressing `Shift + Enter`. Adjust settings and parameters as necessary based on the experiment requirements.

### Tips for using Google Colab

- **Persistent sessions:** Be aware that Google Colab sessions can time out after a period of inactivity. To prevent data loss, ensure to save your work frequently.
- **GPU acceleration:** For intensive computations, take advantage of Google Colab’s GPU by changing the runtime type to GPU through the `Runtime` > `Change runtime type` menu.

Instructions for specific configurations and additional setup details are provided within each notebook to ensure smooth operation on Google Colab.



## Install test images

The test images are crucial for conducting OCR experiments but are not included in the repository until we clear out licence issues. They can be easily downloaded and set up with the following instructions:

### Downloading test images

You can download a pre-selected set of comic book images, which are ideal for testing OCR capabilities:

- [Download Test Images PCISet](https://drive.google.com/file/d/1MCqUImwFS5iQ271CD9_t2FSugJXdYj0a/view?usp=sharing)

After downloading, unzip the files and place them in the `source` directory within your testbed environment.

You can also make this directly within each notebook.


### Preparing your own images

If you prefer to use your own images:

1. **Place your images:** Ensure that each image file is placed in the `source` directory.
2. **Prepare ground truth data:** Accompany each image with a `.json` file containing the ground truth data. This file should have the same name as the image with the suffix `_gt` and include one line per text box as detected by PanelCleaner in two versions, `all_caps`, and `capitalized`, with the following format:
```JSON
{
  "all-caps": [
    "SUDDENLY...",
    "GASP! EVERYTHING'S W-WHIRLING AROUND ME! I CAN'T STAND UP...",
    "CLARK! I'M FALLING! HELP! HELP!",
    ...
  ],
  "capitalized": [
    "Suddenly...",
    "Gasp! Everything's W-whirling around me! I can't stand up...",
    "Clark! I'm falling! Help! Help!",
    ...
  ]
}
```
3. **Language specification (optional):**
   - 
   - Include a `.json` file for each image specifying the language of the text. 
   If no language file is provided, English will be assumed by default. 
   Here is an example format:

```json
{
  "lang": "Spanish"
}
```


### Future Enhancements

In the near future, we plan to automate language detection to streamline the setup process further.



## Introduction to nbdev
[nbdev](https://nbdev.fast.ai/) is a **literate programming** environment that allows you to develop a Python library in Jupyter Notebooks. It integrates non-sequential asynchronous exploratory coding, documentation, and testing into a seamless workflow. Inspired by **Donald Knuth**'s concept of literate programming, this approach not only makes the development process more intuitive but also eases the maintenance and understanding of the codebase.



## Library Notebooks (WIP)

The various Jupyter notebooks that form the core of the **PanelCleaner** testbed library. Each notebook is currently under active development. Below is an overview of some of the key notebooks:

#### [helpers.ipynb](helpers.ipynb)
This notebook includes utility functions and helpers that support the experiments in other notebooks, streamlining repetitive tasks and data manipulation.

#### [ocr_metric.ipynb](ocr_metric.ipynb)
This notebook focuses on defining and implementing metrics to evaluate the performance and accuracy of OCR engines, crucial for assessing the effectiveness of OCR technologies in various scenarios. It currently develops a basic metric for evaluating OCR models. In the near future, additional metrics will be added, such as precision and recall using Levenshtein distance (edit distance). More importantly, it will introduce a metric tailored to the unique characteristics of Comics/Manga OCR, a topic currently unexplored in technical literature.

**Note**: this is currently a very simple notebook and could be a good starting point to understand how we use a very simplified `nbdev` workflow. Open it and look at the first cell where we setup the name of the module. The last cell contains the command to create the `helpers.py` module inside `_testbed/testbed`. The in-between cells code, test and document the module. Only the cells tagged with `#| export` will be exported to the `helpers.py` file. In a full blown `nbdev` env, you could also use this same notebook to generate documentation and tests, all integrated with CIs and fully automated.

#### [experiments.ipynb](experiments.ipynb)
This notebook details the minutiae of the evaluation framework used in other notebooks, with Tesseract as a case study to illustrate the evaluation process. It's a work in progress, and will be updated continuously. 

#### [visor.ipynb](visor.ipynb)
Base infrastructure of experiments visualization. Simple composition of Jupyter widgets.


### [ocr_idefics.ipynb](ocr_idefics.ipynb)
### [ocr_paligemma.ipynb](ocr_paligemma.ipynb)
These notebooks chronicle the testing and development of the VLM Idefics and Paligemma model adapters. They serve functions analogous to the main PanelCleaner modules `ocr_mangaocr.py` and `ocr_tesseract.py` found in `pcleaner/ocr`, adhering to the previously developed API. Should the decision-makers opt to integrate Idefics or Paligemma into the main build, the modules generated in `_testbed/testbed` can be seamlessly transferred to `pcleaner/ocr`.



## Test Notebooks (WIP)

If you're only interested in visualizing the results of the experiments, go directly to `Test_tesseract.ipynb` or `Test_idefics.ipynb`, which are are more concise and focused.

#### [test_tesseract.ipynb](test_tesseract.ipynb)
This notebook is dedicated to testing the Tesseract OCR engine, offering insights into its capabilities and limitations through hands-on experiments. We mostly consider Tesseract as a baseline to compare the performance of the other models. Its performance 80-85% with handwritten all-caps is not the good--was not trained for that at all-- but it's a good starting point.

#### [test_idefics.ipynb](test_idefics.ipynb)
Similar to `test_tesseract.ipynb`, this notebook focuses on Meta's Idefics VLM model, evaluating its performance and accuracy under different conditions. Here you can compare the results of the Tesseract OCR engine with the Idefics VLM model to see how the two stand in terms of accuracy and performance.

#### [test_paligemma.ipynb](test_paligemma.ipynb)
This notebook evaluates the OCR performance of the very recent Google Paligemma model, providing a detailed analysis of its effectiveness in processing comic book images.
