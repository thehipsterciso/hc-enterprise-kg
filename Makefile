.PHONY: install test test-fast test-cov lint format typecheck security generate clean all benchmark

install:
	poetry install --extras "dev mcp viz api"

test:
	poetry run pytest tests/ -v --tb=short

test-fast:
	poetry run pytest tests/ -v --tb=short -m "not slow"

test-cov:
	poetry run pytest tests/ --cov=src --cov-report=term-missing --cov-report=html

lint:
	poetry run ruff check src/ tests/

format:
	poetry run ruff format src/ tests/

format-check:
	poetry run ruff format --check src/ tests/

typecheck:
	poetry run mypy src/ --ignore-missing-imports

security:
	poetry run pip-audit

generate:
	poetry run hckg generate org --profile tech --employees 100 --seed 42

clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .pytest_cache -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .mypy_cache -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name '*.egg-info' -exec rm -rf {} + 2>/dev/null || true
	rm -rf dist/ build/ htmlcov/ .coverage

benchmark:
	poetry run pytest tests/performance/ -v --tb=short

all: lint format-check typecheck test
