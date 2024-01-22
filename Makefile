# define variables
CurrentDir := $(shell pwd)
PYTHON = venv/bin/python
PYINSTALLER = venv/bin/pyinstaller
BUILD_DIR = dist/
QRC_DIR_ICONS = icons/
QRC_DIR_THEMES = themes/
UI_DIR = ui_files/
RC_OUTPUT_DIR = pcleaner/gui/rc_generated_files/
UI_OUTPUT_DIR = pcleaner/gui/ui_generated_files/
RCC_COMPILER = venv/bin/pyside6-rcc
UIC_COMPILER = venv/bin/pyside6-uic
I18N_LUPDATE = venv/bin/pyside6-lupdate
I18N_COMPILER = venv/bin/pyside6-lrelease
BLACK_LINE_LENGTH = 100
BLACK_TARGET_DIR = pcleaner/
BLACK_EXCLUDE_PATTERN = "^$(RC_OUTPUT_DIR).*|^$(UI_OUTPUT_DIR).*|^pcleaner/comic_text_detector/.*"

LANGUAGES := $(shell python -c "import sys; sys.path.append('.'); from pcleaner.data.supported_languages import supported_languages; print(' '.join(supported_languages().keys()))")

# print supported languages
print-supported-languages:
	@echo $(LANGUAGES)

fresh-install: clean build install

refresh-assets: build-icon-cache compile-qrc compile-ui refresh-i18n compile-i18n


# build target
build: compile-qrc compile-ui
	$(PYTHON) -m build --outdir $(BUILD_DIR)

# compile .qrc files
compile-qrc:
	for file in $(QRC_DIR_ICONS)*.qrc; do \
		basename=`basename $$file .qrc`; \
		$(RCC_COMPILER) $$file -o $(RC_OUTPUT_DIR)rc_$$basename.py; \
	done
	for file in $(QRC_DIR_THEMES)*.qrc; do \
		basename=`basename $$file .qrc`; \
		$(RCC_COMPILER) $$file -o $(RC_OUTPUT_DIR)rc_$$basename.py; \
	done


# Refresh localization files for each language.
refresh-i18n:
	$(foreach lang, $(LANGUAGES), mkdir -p translations && $(I18N_LUPDATE) pcleaner/*.py pcleaner/gui/*.py pcleaner/gui/CustomQ/*.py ui_files -ts translations/$(lang).ts;)

# Compile localization files for each language, then update the QRC file and compile it.
compile-i18n:
	$(foreach lang, $(LANGUAGES), $(I18N_COMPILER) translations/$(lang).ts -qm translations/packed/$(lang).qm;)

	echo '<!DOCTYPE RCC><RCC version="1.0"><qresource prefix="/translations">' > translations/packed/linguist.qrc
	$(foreach lang, $(LANGUAGES), echo '    <file>$(lang).qm</file>' >> translations/packed/linguist.qrc;)
	echo '</qresource></RCC>' >> translations/packed/linguist.qrc

	$(RCC_COMPILER) translations/packed/linguist.qrc -o $(RC_OUTPUT_DIR)rc_translations.py


# compile .ui files
compile-ui:
	for file in $(UI_DIR)*.ui; do \
		basename=`basename $$file .ui`; \
		$(UIC_COMPILER) $$file -o $(UI_OUTPUT_DIR)ui_$$basename.py; \
	done

# run build_icon_cache.py
build-icon-cache:
	cd $(QRC_DIR_ICONS) && ${CurrentDir}/$(PYTHON) build_icon_cache.py
	cd $(QRC_DIR_ICONS)/custom_icons && ${CurrentDir}/$(PYTHON) copy_from_dark_to_light.py

# install target
install:
	python -m pip install $(BUILD_DIR)*.whl --break-system-packages

# clean target
clean:
	rm -rf $(BUILD_DIR)

# format the code
black-format:
	find $(BLACK_TARGET_DIR) -type f -name '*.py' | grep -Ev $(BLACK_EXCLUDE_PATTERN) | xargs black --line-length $(BLACK_LINE_LENGTH)

release:
	twine upload $(BUILD_DIR)*

build-elf:
	$(PYINSTALLER) pcleaner/main.py \
		--paths 'venv/lib/python3.11/site-packages' \
		--onedir --noconfirm --clean --workpath=build --distpath=dist-elf --windowed \
		--name="PanelCleaner" \
		--copy-metadata=filelock \
		--copy-metadata=huggingface-hub \
		--copy-metadata=numpy \
		--copy-metadata=packaging \
		--copy-metadata=pyyaml \
		--copy-metadata=pillow \
		--copy-metadata=regex \
		--copy-metadata=requests \
		--copy-metadata=safetensors \
		--copy-metadata=tokenizers \
		--copy-metadata=tqdm \
		--copy-metadata=torch \
		--collect-data=torch \
		--collect-data=unidic_lite \
		--hidden-import=scipy.signal \
		--add-data "venv/lib/python3.11/site-packages/manga_ocr/assets/example.jpg:assets/" \
		--add-data "pcleaner/data/LiberationSans-Regular.ttf:pcleaner/data/" \
		--add-data "pcleaner/data/NotoMono-Regular.ttf:pcleaner/data/"

pip-install-torch-no-cuda:
	$(PYTHON) -m pip uninstall torch torchvision -y
	$(PYTHON) -m pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu


.PHONY: clean build install fresh-install release refresh-i18n compile-i18n compile-qrc compile-ui build-icon-cache refresh-assets black-format pip-install-torch-no-cuda
