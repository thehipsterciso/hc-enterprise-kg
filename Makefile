.PHONY: install test test-cov lint format typecheck generate clean all

install:
	poetry install --extras dev

test:
	poetry run pytest tests/ -v --tb=short

test-cov:
	poetry run pytest tests/ --cov=src --cov-report=term-missing

lint:
	poetry run ruff check src/ tests/

format:
	poetry run ruff format src/ tests/

typecheck:
	poetry run mypy src/

generate:
	poetry run hckg generate org --profile tech --employees 100 --seed 42

clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .pytest_cache -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .mypy_cache -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name '*.egg-info' -exec rm -rf {} + 2>/dev/null || true
	rm -rf dist/ build/ htmlcov/ .coverage

all: lint typecheck test
