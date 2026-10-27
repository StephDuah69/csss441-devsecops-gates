.PHONY: help setup test lint format run docker-build docker-run clean

PYTHON := python
VENV_DIR := .venv
VENV_BIN := $(VENV_DIR)/bin
ifeq ($(OS),Windows_NT)
    VENV_BIN := $(VENV_DIR)/Scripts
endif

help:
	@echo "CSSS 441 DevSecOps Pipeline - Makefile Commands:"
	@echo "  make setup        - Install dependencies and setup virtual environment"
	@echo "  make test         - Run automated unit and integration tests"
	@echo "  make lint         - Run Ruff security and style linter"
	@echo "  make format       - Format code using Ruff"
	@echo "  make run          - Run FastAPI application locally on port 8000"
	@echo "  make docker-build - Build hardened Docker container image"
	@echo "  make docker-run   - Launch container via Docker Compose"
	@echo "  make clean        - Remove caches and build artifacts"

setup:
	$(PYTHON) -m venv $(VENV_DIR)
	$(VENV_BIN)/python -m pip install --upgrade pip
	$(VENV_BIN)/pip-compile requirements.in
	$(VENV_BIN)/pip-compile requirements-dev.in
	$(VENV_BIN)/pip install -r requirements-dev.txt

test:
	$(VENV_BIN)/pytest -v

lint:
	$(VENV_BIN)/ruff check .
	$(VENV_BIN)/ruff format --check .

format:
	$(VENV_BIN)/ruff check --fix .
	$(VENV_BIN)/ruff format .

run:
	$(VENV_BIN)/uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

docker-build:
	docker build -t csss441-book-catalog:local .

docker-run:
	docker compose up -d

clean:
	rm -rf __pycache__ .pytest_cache .ruff_cache htmlcov .coverage
