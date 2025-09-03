PYTHON ?= python3
PIP ?= $(PYTHON) -m pip

.PHONY: help install dev test lint type-check format run clean qa test-coverage install-dev security docs

help:
	@echo "Targets: install, install-dev, dev, test, test-coverage, lint, type-check, format, qa, security, docs, run, clean"

install:
	$(PIP) install -e .


install-dev:
	$(PIP) install -e .[dev]

dev:
	$(PIP) install -e .[dev]

test:
	pytest -q

lint:
	ruff check .
	black --check openworld_methane tests

type-check:
	mypy openworld_methane

format:
	black openworld_methane tests
	ruff format .

run:
	$(PYTHON) -m openworld_methane --help || true

clean:
	rm -rf .pytest_cache .mypy_cache **/__pycache__

qa: lint type-check test

test-coverage:
	pytest --cov=openworld_methane --cov-report=term-missing

security:
	@echo "Run security scanning (placeholder)"

docs:
	mkdocs build

