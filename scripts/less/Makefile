LESS_SCRIPTS = theme.css container.css

LESSC = lessc
LESSCFLAGS = -x
STATIC = static

.SUFFIXES:
.SUFFIXES: .less .css

all: build

build: $(LESS_SCRIPTS)

.less.css:
	$(LESSC) $(LESSCFLAGS) $< > $@

install: $(LESS_SCRIPTS)
	cp -v $(LESS_SCRIPTS) $(OUTPUT)/css/

.PHONY: build
