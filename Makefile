.PHONY: setup format lint guards test check

PYTHON ?= python
PYTHON_BOOTSTRAP ?= python3.14
RUFF ?= ruff
PYTEST ?= pytest
PYTHON_FILES := $(shell git ls-files --cached --others --exclude-standard '*.py')
MARKDOWN_FILES := $(shell git ls-files --cached --others --exclude-standard '*.md')
PROJECT_FILES := $(shell git ls-files --cached --others --exclude-standard)

setup:
	$(PYTHON_BOOTSTRAP) -m venv .venv
	.venv/bin/python -m pip install --require-hashes -r requirements.lock
	.venv/bin/python -m pip install -e . --no-deps

format:
	$(PYTHON) scripts/quality.py --fix --skip-tests

lint:
	$(RUFF) check .
	$(RUFF) format --check .

guards:
	$(PYTHON) scripts/check_lookahead.py $(PYTHON_FILES)
	$(PYTHON) scripts/check_secrets.py $(PROJECT_FILES)
	$(PYTHON) scripts/check_docs.py $(MARKDOWN_FILES)

test:
	$(PYTEST)

check:
	$(PYTHON) scripts/quality.py
