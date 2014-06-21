all: clean build

clean:
	rm -rf static

build: clean
	mkdir static
	mkdir -p static/js static/css static/fonts
	make -C scripts build
	make -C scripts install
