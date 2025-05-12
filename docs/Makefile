#!/usr/bin/env make
# Minimal Makefile for building Sphinx documentation

# You can set these variables from the command line.
SPHINXOPTS    =
SPHINXBUILD   = sphinx-build
SOURCEDIR     = source
BUILDDIR      = _build

.PHONY: help html clean

help:
	@echo "Please use 'make <target>' where <target> is one of"
	@echo "  html    to build the HTML documentation"
	@echo "  clean   to clean all generated files"

html:
	$(SPHINXBUILD) -b html $(SPHINXOPTS) $(SOURCEDIR) $(BUILDDIR)/html
	@echo "\nBuild finished. The HTML pages are in $(BUILDDIR)/html."

clean:
	rm -rf $(BUILDDIR)

.PHONY: openapi
openapi:
	@echo "Fetching OpenAPI schema..."
	@curl -s http://localhost:8000/api/v1/openapi.json -o $(SOURCEDIR)/openapi.json
	@echo "OpenAPI schema saved to $(SOURCEDIR)/openapi.json"