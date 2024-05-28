# PanelCleaner Testbed

## Overview
The **PanelCleaner** testbed serves as a dedicated area for experimenting and testing new ideas with *PanelCleaner* using Jupyter Notebooks. Currently, it focuses on **OCR** technologies, primarily using **Tesseract** and **IDefics** models. The testbed also begins the development of an evaluation framework to support future experiments. This project utilizes the `nbdev` literate programming environment.

## Installation
To get started with the notebooks, you'll need Jupyter Lab/Notebook or any Python IDE that supports Jupyter notebooks like *VSCode* or *Google Colab*. 
The setup mostly shares the same requirements as PanelCleaner and its CLI, with a few additional dependencies.  
Here’s how to set up your environment:
1. Activate a virtual environment.
2. Navigate to the `_testbed` directory:
   ```bash
   cd _testbed
   ```
3. Install the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```
Note: Each notebook may require the installation of additional dependencies.

## Google Colab Support
The notebooks are ready to use on Google Colab, allowing you to run them directly on the platform without any extra setup or local GPU rigs.
Instructions to use Google Colab are included in the notebooks.

## Install Test Images
The test images are not included in the repository but can be downloaded from the following link:
- [Test images PCISet](https://drive.google.com/file/d/18TSXLCYAPxAlUsdHmgAe6FZM5d8K6gcT/view?usp=drive_link). The notebooks also have instructions and code to download the set directly 

After downloading, place the test images in the [source](source) directory. If you want to use your own, each image should have a corresponding text file with the same name, but with the extension `.txt`, which contains the ground truth data, one line per box (as calculated by PanelCleaner). Optionally, you can also include a `.json` file with the same name, specifying the language of the page:
```json
{
  "lang": "Spanish"
}
```
If no language file is found, English will be used by default. In the near future, language detection will be automated.

## Introduction to nbdev
[nbdev](https://nbdev.fast.ai/) is a **literate programming** environment that allows you to develop a Python library in Jupyter Notebooks, integrating exploratory programming, code, tests, and documentation into a single cohesive workflow. Inspired by **Donald Knuth**'s concept of literate programming, this approach not only makes the development process more intuitive but also eases the maintenance and understanding of the codebase.

## Library Notebooks (WIP)

#### [helpers.ipynb](helpers.ipynb)
This notebook includes utility functions and helpers that support the experiments in other notebooks, streamlining repetitive tasks and data manipulation.

#### [ocr_metric.ipynb](ocr_metric.ipynb)
This notebook focuses on defining and implementing metrics to evaluate the performance and accuracy of OCR engines, crucial for assessing the effectiveness of OCR technologies in various scenarios. It currently develops a basic metric for evaluating OCR models. In the near future, additional metrics will be added, such as precision and recall using Levenshtein distance (edit distance). More importantly, it will introduce a metric tailored to the unique characteristics of Comics/Manga OCR, a topic currently unexplored in technical literature.

#### [experiments.ipynb](experiments.ipynb)
This notebook details the development of the evaluation framework used in other notebooks, with Tesseract as a case study to illustrate the evaluation process. It's a work in progress, and will be updated continuously. If you're only interested in visualizing the results of the experiments, go directly to `Test_tesseract.ipynb` or `Test_idefics.ipynb`, which are much shorter and more to the point.

#### [visor.ipynb](visor.ipynb)
Base infrastructure of experiments visualization. Simple composition of Jupyter widgets.


## Test Notebooks (WIP)

#### [test_tesseract.ipynb](test_tesseract.ipynb)
This notebook is dedicated to testing the Tesseract OCR engine, offering insights into its capabilities and limitations through hands-on experiments.

#### [test_idefics.ipynb](test_idefics.ipynb)
Similar to `test_tesseract.ipynb`, this notebook focuses on the IDefics LVM model, evaluating its performance and accuracy under different conditions. Here you can compare the results of the Tesseract OCR engine with the IDefics LVM model to see how the two stand in terms of accuracy and performance.
