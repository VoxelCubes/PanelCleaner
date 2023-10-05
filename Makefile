# define variables
PYTHON = python
BUILD_DIR = dist/
QRC_DIR_ICONS = icons/
QRC_DIR_THEMES = themes/
UI_DIR = ui_files/
RC_OUTPUT_DIR = pcleaner/gui/rc_generated_files/
UI_OUTPUT_DIR = pcleaner/gui/ui_generated_files/
RCC_COMPILER = venv/bin/pyside6-rcc
UIC_COMPILER = venv/bin/pyside6-uic
BLACK_LINE_LENGTH = 100
BLACK_TARGET_DIR = pcleaner/
BLACK_EXCLUDE_PATTERN = "^$(RC_OUTPUT_DIR).*|^$(UI_OUTPUT_DIR).*|^pcleaner/comic_text_detector/.*"


fresh-install: clean build install

refresh-assets: build-icon-cache compile-qrc compile-ui


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


# compile .ui files
compile-ui:
	for file in $(UI_DIR)*.ui; do \
		basename=`basename $$file .ui`; \
		$(UIC_COMPILER) $$file -o $(UI_OUTPUT_DIR)ui_$$basename.py; \
	done

# run build_icon_cache.py
build-icon-cache:
	cd $(QRC_DIR_ICONS) && $(PYTHON) build_icon_cache.py
	cd $(QRC_DIR_ICONS)/custom_icons && $(PYTHON) copy_from_dark_to_light.py

# install target
install:
	$(PYTHON) -m pip install $(BUILD_DIR)*.whl --break-system-packages

# clean target
clean:
	rm -rf $(BUILD_DIR)

# format the code
black-format:
	find $(BLACK_TARGET_DIR) -type f -name '*.py' | grep -Ev $(BLACK_EXCLUDE_PATTERN) | xargs black --line-length $(BLACK_LINE_LENGTH)

release:
	twine upload $(BUILD_DIR)*

.PHONY: clean build install fresh-install release compile-qrc compile-ui build-icon-cache refresh-assets
