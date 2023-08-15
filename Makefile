# define variables
PYTHON = python
BUILD_DIR = dist/
QRC_DIR = icons/
UI_DIR = ui_files/
RC_OUTPUT_DIR = pcleaner/gui/rc_generated_files/
UI_OUTPUT_DIR = pcleaner/gui/ui_generated_files/
RCC_COMPILER = venv/bin/pyside6-rcc
UIC_COMPILER = venv/bin/pyside6-uic

# default target
fresh-install: clean build install

# build target
build: compile-qrc compile-ui
	$(PYTHON) -m build --outdir $(BUILD_DIR)

# compile .qrc files
compile-qrc:
	for file in $(QRC_DIR)*.qrc; do \
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
	cd $(QRC_DIR) && $(PYTHON) build_icon_cache.py

# install target
install:
	$(PYTHON) -m pip install $(BUILD_DIR)*.whl

# clean target
clean:
	rm -rf $(BUILD_DIR)

release:
	twine upload $(BUILD_DIR)*

.PHONY: clean build install fresh-install release compile-qrc compile-ui build-icon-cache
