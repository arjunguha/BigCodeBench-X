all:
	@echo "Use 'make stdio_bcb.sif' to build the container image."

build: stdio_bcb.sif

stdio_bcb.sif: stdio_bcb.def requirements.txt driver.py entrypoint.py post_install.sh
	apptainer build stdio_bcb.sif stdio_bcb.def
