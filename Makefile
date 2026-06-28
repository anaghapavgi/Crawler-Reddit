.PHONY: install install-dev format lint typecheck test verify smoke

install:
	python -m pip install -e .

install-dev:
	python -m pip install -e ".[dev]"

format:
	ruff format .

lint:
	ruff check .

typecheck:
	mypy src

test:
	pytest

verify:
	ruff format --check .
	ruff check .
	mypy src
	pytest --cov=src/reddit_intelligence --cov-report=term-missing

smoke:
	python scripts/smoke_test.py
