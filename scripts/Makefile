all: build install

build:
	make -C coffee clean
	make -C less clean
	make -C coffee build
	make -C less build

install:
	make -C coffee install OUTPUT=../../static
	make -C less install OUTPUT=../../static
	make -C bootstrap install OUTPUT=../../static
	make -C vendor install OUTPUT=../../static

.PHONY: all build install
