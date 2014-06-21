COFFEE_SCRIPTS = test.min.js

.SUFFIXES:
.SUFFIXES: .coffee .js .min.js


all: build


build: $(COFFEE_SCRIPTS)

.coffee.js:
	coffee -c $<

.js.min.js:
	uglifyjs --no-copyright --output $@ $<

install: $(COFFEE_SCRIPTS)
	cp -v $(COFFEE_SCRIPTS) $(OUTPUT)/js/

.PHONY: build
