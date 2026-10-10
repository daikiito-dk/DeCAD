VENV ?= .venv
BIN := $(VENV)/bin

.PHONY: setup test lint fmt check clean

setup:
	uv venv
	uv pip install -e ".[dev]"

test:
	$(BIN)/pytest -q

lint:
	$(BIN)/ruff check .
	$(BIN)/ruff format --check .

fmt:
	$(BIN)/ruff format .
	$(BIN)/ruff check --fix .

check: lint test

clean:
	rm -rf $(VENV) dist build *.egg-info .pytest_cache .ruff_cache
