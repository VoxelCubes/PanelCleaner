# define configurable variables. May need to be adapted for your environment.
CurrentDir := $(shell pwd)
PYINSTALLER_VENV := venv_clean
PYTHON := venv/bin/python
PYINSTALLER := $(PYINSTALLER_VENV)/bin/pyinstaller
BUILD_DIR := dist/
QRC_DIR_ICONS := icons/
QRC_DIR_THEMES := themes/
UI_DIR := ui_files/
RC_OUTPUT_DIR := pcleaner/gui/rc_generated_files/
UI_OUTPUT_DIR := pcleaner/gui/ui_generated_files/
RCC_COMPILER := venv/bin/pyside6-rcc
UIC_COMPILER := venv/bin/pyside6-uic
I18N_LUPDATE := venv/bin/pyside6-lupdate
I18N_COMPILER := venv/bin/pyside6-lrelease
BLACK_LINE_LENGTH := 100
BLACK_TARGET_DIR := pcleaner/
BLACK_EXCLUDE_PATTERN := "^$(RC_OUTPUT_DIR).*|^$(UI_OUTPUT_DIR).*|^pcleaner/comic_text_detector/.*"

LANGUAGES := $(shell python -c "import sys; sys.path.append('.'); from pcleaner.gui.supported_languages import supported_languages; print(' '.join(supported_languages().keys()))")

# print supported languages
print-supported-languages:
	@echo $(LANGUAGES)

fresh-install: clean-build build install

refresh-assets: build-icon-cache compile-qrc compile-ui refresh-i18n compile-i18n

build-both: build build-cli

# Normal build target. Use the setup-cli-gui.cfg configuration.
build: compile-qrc compile-ui
	cp setup-cli-gui.cfg setup.cfg
	$(PYTHON) -m build --outdir $(BUILD_DIR)
	rm setup.cfg

# CLI-only build target. Use the setup-cli.cfg configuration.
build-cli:
	cp setup-cli.cfg setup.cfg
	$(PYTHON) -m build --outdir $(BUILD_DIR)
	rm setup.cfg

# clean-build target
clean-build: 
	rm -rf $(BUILD_DIR)

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


# Refresh localization files for the source language, en_US only.
# For some of the i18n, getting Linguist to recognize the strings with enough context added was too
# big of a pain in the ass, so here are python functions that extract the data structures and parse
# out the relevant strings, then create fake code for Linguist to ingest.
refresh-i18n:
	mkdir -p translations
	PYTHONPATH=/home/corbin/Repos/PanelCleaner $(PYTHON) translations/profile_extractor.py
	PYTHONPATH=/home/corbin/Repos/PanelCleaner $(PYTHON) translations/process_steps_extractor.py
	$(I18N_LUPDATE) -extensions .py,.ui -no-recursive pcleaner pcleaner/gui pcleaner/gui/CustomQ ui_files \
		translations/profile_strings.py translations/process_strings.py -source-language en_US -target-language en_US -ts translations/PanelCleaner_source.ts

# Generate .ts files for each language if they don't already exist
generate-ts:
	$(foreach lang, $(LANGUAGES), \
		if [ ! -f translations/PanelCleaner_$(lang).ts ]; then \
			echo "Generating TS file for: $(lang)"; \
			$(I18N_LUPDATE) -extensions .py,.ui -no-recursive pcleaner pcleaner/gui pcleaner/gui/CustomQ ui_files \
			translations/profile_strings.py translations/process_strings.py -source-language en_US -target-language $(lang) -ts translations/PanelCleaner_$(lang).ts; \
		fi;)

# Compile localization files for each language, then update the QRC file and compile it.
compile-i18n: generate-ts
	$(foreach lang, $(LANGUAGES), $(I18N_COMPILER) translations/PanelCleaner_$(lang).ts -qm translations/packed/PanelCleaner_$(lang).qm;)

	echo '<RCC><qresource prefix="/translations">' > translations/packed/linguist.qrc
	$(foreach lang, $(LANGUAGES), echo '    <file>PanelCleaner_$(lang).qm</file>' >> translations/packed/linguist.qrc;)
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
	$(PYTHON) -m pip install $(BUILD_DIR)*.whl 

# clean target
clean:
	rm -rf build
	rm -rf dist
	rm -rf dist-elf/PanelCleaner
	rm -rf AppImage
	rm -rf .pytest_cache
	rm -rf pcleaner.egg-info
	rm -rf AUR/panelcleaner/pkg
	rm -rf AUR/panelcleaner/src
	rm -rf AUR/panelcleaner/*.tar.gz
	rm -rf AUR/panelcleaner/*.tar.zst

# format the code
black-format:
	find $(BLACK_TARGET_DIR) -type f -name '*.py' | grep -Ev $(BLACK_EXCLUDE_PATTERN) | xargs black --line-length $(BLACK_LINE_LENGTH)

release:
	$(PYTHON) -m twine upload $(BUILD_DIR)*

build-elf:
	$(PYINSTALLER) pcleaner/main.py \
		--paths "${PYINSTALLER_VENV}/lib/python3.11/site-packages" \
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
		--add-data "${PYINSTALLER_VENV}/lib/python3.11/site-packages/manga_ocr/assets/example.jpg:assets/" \
		--add-data "pcleaner/data/LiberationSans-Regular.ttf:pcleaner/data/" \
		--add-data "pcleaner/data/NotoMono-Regular.ttf:pcleaner/data/"
	
	@echo "Purging CUDA related files from _internal directory..."
	@find dist-elf/PanelCleaner/_internal -type f \( \
		-name 'libtorch_cuda.so' -o \
		-name 'libc10_cuda.so' -o \
		-name 'libcusparse.so*' -o \
		-name 'libcurand.so*' -o \
		-name 'libcudnn.so*' -o \
		-name 'libcublasLt.so*' -o \
		-name 'libcublas.so*' -o \
		-name 'libcupti.so*' -o \
		-name 'libcufft.so*' -o \
		-name 'libcudart.so*' -o \
		-name 'libnv*' -o \
		-name 'libnccl.so*' \
		\) -exec rm -rf {} \;


pip-install-torch-no-cuda:
	$(PYTHON) -m pip uninstall torch torchvision -y
	$(PYTHON) -m pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu

# build AppImage from ELF
build-app-image: 
	# appimagetool Error: Desktop file not found, aborting
	# No idea how to fix, oh well...
	@echo "Building AppImage..."
	# Create AppDir structure
	mkdir -p AppImage/PanelCleaner.AppDir/usr/bin
	mkdir -p AppImage/PanelCleaner.AppDir/usr/lib
	mkdir -p AppImage/PanelCleaner.AppDir/usr/share/applications
	mkdir -p AppImage/PanelCleaner.AppDir/usr/share/icons/hicolor/256x256/apps
	mkdir -p AppImage/PanelCleaner.AppDir/usr/share/metainfo

	# Copy the ELF file and its dependencies
	cp -r dist-elf/PanelCleaner/PanelCleaner AppImage/PanelCleaner.AppDir/usr/bin/
	cp -r dist-elf/PanelCleaner/_internal/* AppImage/PanelCleaner.AppDir/usr/lib/
	
	# Copy desktop file and icon
	cp PanelCleaner.desktop AppImage/PanelCleaner.AppDir/usr/share/applications/
	cp icons/logo-big.png AppImage/PanelCleaner.AppDir/usr/share/icons/hicolor/256x256/apps/PanelCleaner.png

	# Copy AppStream metadata
	cp flatpak/io.github.voxelcubes.panelcleaner.appdata.xml AppImage/PanelCleaner.AppDir/usr/share/metainfo/


	# Create AppRun script
	echo -e "#!/bin/bash\nexec \$${APPDIR}/usr/bin/PanelCleaner" > AppImage/PanelCleaner.AppDir/AppRun
	chmod +x AppImage/PanelCleaner.AppDir/AppRun

	# Use appimagetool to create the AppImage
	appimagetool -v AppImage/PanelCleaner.AppDir -n -u "gh-releases-zsync|VoxelCubes|PanelCleaner|latest" PanelCleaner-x86_64.AppImage

	@echo "AppImage built successfully."


.PHONY: clean build build-cli build-both install fresh-install release refresh-i18n compile-i18n compile-qrc compile-ui build-icon-cache refresh-assets black-format pip-install-torch-no-cuda, build-elf, build-app-image
