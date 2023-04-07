# define variables
PYTHON = python
BUILD_DIR = dist/

# default target
all: clean build install

# build target
build:
	$(PYTHON) -m build --outdir $(BUILD_DIR)

# install target
install:
	$(PYTHON) -m pip install $(BUILD_DIR)*.whl

# clean target
clean:
	rm -rf $(BUILD_DIR)

release:
	twine upload $(BUILD_DIR)*


.PHONY: clean build install