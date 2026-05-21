# define configurable variables. May need to be adapted for your environment.
CurrentDir := $(shell pwd)
UV := uv
VENV_GUI_CPU := .venv-gui-cpu
VENV_GUI_CUDA := .venv-gui-cuda
VENV_CLI_CUDA := .venv-cli-cuda
PYINSTALLER_VENV := $(VENV_GUI_CPU)
PYTHON := $(VENV_GUI_CPU)/bin/python
PYINSTALLER := $(PYINSTALLER_VENV)/bin/pyinstaller
BUILD_DIR := dist/
DIR_ICONS := icons
UI_DIR := ui_files/
PACKED_TRANSLATION_DATA := pcleaner/data/translation_generated_files
RC_OUTPUT_DIR := pcleaner/gui/rc_generated_files/
UI_OUTPUT_DIR := pcleaner/gui/ui_generated_files/
UIC_COMPILER := $(VENV_GUI_CPU)/bin/pyside6-uic
I18N_LUPDATE := $(VENV_GUI_CPU)/bin/pyside6-lupdate
I18N_COMPILER := $(VENV_GUI_CPU)/bin/pyside6-lrelease
BLACK_LINE_LENGTH := 100
BLACK_TARGET_DIR := pcleaner/
BLACK_EXCLUDE_PATTERN := "^$(UI_OUTPUT_DIR).*|^pcleaner/comic_text_detector/.*"

LANGUAGES := $(shell python -c "import sys; sys.path.append('.'); from pcleaner.gui.supported_languages import supported_languages; lang_codes = list(supported_languages().keys()); lang_codes.remove('en_US'); print(' '.join(lang_codes))")
PYTHON_VERSION = $(shell $(PYTHON) -c "import sys; print('{}.{}'.format(sys.version_info[0], sys.version_info[1]))")
PYINSTALLER_SITE = $(PYINSTALLER_VENV)/lib/python$(PYTHON_VERSION)/site-packages

EXCLUDE_NEWER_DATE := $(shell date -u -d '7 days ago' +%Y-%m-%d)
export UV_EXCLUDE_NEWER := $(EXCLUDE_NEWER_DATE)

run-gui:
	$(PYTHON) -m pcleaner.gui.launcher

# print supported languages
print-translated-languages:
	@echo $(LANGUAGES)

fresh-install: clean-build build install

refresh-assets: build-icon-cache compile-ui refresh-i18n compile-i18n

build-both: build build-cli

uv-sync-gui-cpu:
	$(UV) venv $(VENV_GUI_CPU)
	. $(VENV_GUI_CPU)/bin/activate && $(UV) pip install --reinstall torch torchvision --index-url https://download.pytorch.org/whl/cpu
	. $(VENV_GUI_CPU)/bin/activate && $(UV) sync --active --group runtime-base --group runtime-gui --group runtime-dbus --group dev-tools --no-install-package torch --no-install-package torchvision

uv-sync-gui-cuda:
	$(UV) venv $(VENV_GUI_CUDA)
	. $(VENV_GUI_CUDA)/bin/activate && $(UV) sync --active --group runtime-base --group runtime-gui --group runtime-dbus --group dev-tools

uv-sync-cli-cuda:
	$(UV) venv $(VENV_CLI_CUDA)
	. $(VENV_CLI_CUDA)/bin/activate && $(UV) sync --active --group runtime-base --group runtime-gui --group runtime-dbus --group dev-tools

sync-setup-cfg:
	$(PYTHON) tools/sync_setup_cfg.py

# Normal build target. Use the setup-cli-gui.cfg configuration.
build: compile-ui sync-setup-cfg
	cp setup-cli-gui.cfg setup.cfg
	$(UV) build --outdir $(BUILD_DIR)
	rm setup.cfg

# CLI-only build target. Use the setup-cli.cfg configuration.
build-cli: sync-setup-cfg
	cp setup-cli.cfg setup.cfg
	$(UV) build --outdir $(BUILD_DIR)
	rm setup.cfg

# clean-build target
clean-build: 
	rm -rf $(BUILD_DIR)


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
	$(foreach lang, $(LANGUAGES), $(I18N_COMPILER) translations/PanelCleaner_$(lang).ts -qm $(PACKED_TRANSLATION_DATA)/PanelCleaner_$(lang).qm;)

# compile .ui files
compile-ui:
	for file in $(UI_DIR)*.ui; do \
		basename=`basename $$file .ui`; \
		$(UIC_COMPILER) $$file -o $(UI_OUTPUT_DIR)ui_$$basename.py; \
	done

# run build_icon_cache.py
build-icon-cache:
	$(PYTHON) $(DIR_ICONS)/build_icon_cache.py
	$(PYTHON) $(DIR_ICONS)/copy_from_dark_to_light.py

# install target
install:
	$(UV) pip install --python $(PYTHON) $(BUILD_DIR)*.whl

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

release: confirm
	$(UV) publish $(BUILD_DIR)*

build-elf:
	$(PYINSTALLER) pcleaner/main.py \
		--paths "${PYINSTALLER_SITE}" \
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
		--add-data "${PYINSTALLER_SITE}/manga_ocr/assets/example.jpg:assets/" \
		--collect-data pcleaner
	
	# This stupid thing refuses to collect data, so do it manually:
	@echo "Copying data files..."
	mkdir -p dist-elf/PanelCleaner/_internal/pcleaner
	cp -r pcleaner/data dist-elf/PanelCleaner/_internal/pcleaner/
	@echo "Purging __pycache__ directories..."
	@find dist-elf/PanelCleaner/_internal/pcleaner -type d -name "__pycache__"
	@find dist-elf/PanelCleaner/_internal/pcleaner -type d -name "__pycache__" -exec rm -rf {} \; || true

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
	$(UV) pip uninstall --python $(PYTHON) torch torchvision -y
	$(UV) pip install --python $(PYTHON) torch torchvision --index-url https://download.pytorch.org/whl/cpu

requirements-tested:
	$(UV) lock
	$(UV) export --format requirements-txt --group runtime-base --group runtime-gui --group runtime-dbus > requirements_tested.txt

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

confirm:
	@read -p "Are you sure you want to proceed? (yes/no): " CONFIRM; \
	if [ "$$CONFIRM" = "yes" ]; then \
		echo "Proceeding..."; \
	else \
		echo "Aborted by user."; \
		exit 1; \
	fi


.PHONY: confirm clean build build-cli build-both install fresh-install release refresh-i18n compile-i18n compile-ui build-icon-cache refresh-assets black-format pip-install-torch-no-cuda build-elf build-app-image uv-sync-gui-cpu uv-sync-gui-cuda uv-sync-cli-cuda sync-setup-cfg requirements-tested
