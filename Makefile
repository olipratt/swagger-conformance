# Makefile for building releases of swagger-conformance.

# Source directories.
PKGSOURCEDIR = swaggerconformance

# General documentation directories.
DOCSSOURCEDIR = docs/source
SPHINXAPIOUT = $(DOCSSOURCEDIR)/modules
DOCSBUILDDIR = docs/build
DOCSHTMLDIR = $(DOCSBUILDDIR)/html
# Sphinx documentation commands.
SPHINXBUILDOPTS = -E -W
SPHINXBUILD = sphinx-build
SPHINXBUILDTARGET = html

# Python commands.
PYTHONCMD = python3
PYTHONUTDIR = tests
PYTHONUTOPTS = -v -s $(PYTHONUTDIR) -t . -p "test_*.py"
PYCOVERAGECMD = coverage

# Package building values.
DISTSDIR = dist

# Put it first so that "make" without argument is like "make help".
help:
	@echo "Available targets:"
	@echo "    help"
	@echo "        Print this message."
	@echo "    lint"
	@echo "        Run pylint over the package's source code."
	@echo "    test"
	@echo "        Run all tests."
	@echo "    test_coverage"
	@echo "        Run all tests with code coverage enabled."
	@echo "    docs"
	@echo "        Generate all documentation."
	@echo "    package"
	@echo "        Package up ready for upload to PyPI."
	@echo "    all"
	@echo "        Run all tests and builds, but don't upload the results."
	@echo "    docs_upload"
	@echo "        Generate and upload documentation to PyPI."
	@echo "    package_upload"
	@echo "        Build and upload the current code to PyPI."
	@echo "    publish"
	@echo "        Build and publish docs and packages to PyPI."

lint:
	$(PYTHONCMD) -m pylint $(PKGSOURCEDIR)

test: lint
	$(PYTHONCMD) -m unittest discover $(PYTHONUTOPTS)

test_coverage: test
	$(PYCOVERAGECMD) run -m unittest discover $(PYTHONUTOPTS)
	$(PYCOVERAGECMD) report

docs_clean:
	rm -rf "$(DOCSBUILDDIR)"

docs_sphinx: docs_clean
	@$(SPHINXBUILD) -M "$(SPHINXBUILDTARGET)" "$(DOCSSOURCEDIR)" \
		"$(DOCSBUILDDIR)" $(SPHINXBUILDOPTS)

docs: docs_sphinx

package: test
	rm -rf "$(DISTSDIR)"
	$(PYTHONCMD) setup.py sdist bdist_wheel

package_upload: package
	twine upload dist/*

publish: package_upload

all: docs test_coverage package

.PHONY: help lint test test_coverage docs_clean docs_sphinx docs package \
	package_upload publish all
