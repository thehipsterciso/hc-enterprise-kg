# Contributing to hc-enterprise-kg

Thanks for your interest in contributing! This document explains how to get started.

## Development Setup

```bash
git clone https://github.com/thehipsterciso/hc-enterprise-kg.git
cd hc-enterprise-kg
poetry install --extras dev
```

## Running Tests

```bash
make test          # Run all 124 tests
make test-cov      # Run with coverage report
make lint          # Lint with ruff
make typecheck     # Type check with mypy
make all           # Lint + typecheck + test
```

All tests must pass before submitting a PR.

## Making Changes

1. Fork the repo and create a branch from `main`
2. Make your changes
3. Add or update tests for any new functionality
4. Run `make all` to verify lint, types, and tests pass
5. Submit a pull request

## Branch Naming

- `feature/description` for new features
- `fix/description` for bug fixes
- `docs/description` for documentation changes

## Code Style

- We use [ruff](https://docs.astral.sh/ruff/) for linting and formatting (line length: 100)
- Type annotations are required — we run mypy in strict mode
- Entity models use Pydantic v2
- CLI commands use Click

Run `make format` to auto-format your code before committing.

## Adding a New Entity Type

1. Create a model in `src/domain/entities/` (extend `BaseEntity`)
2. Add the type to `EntityType` enum in `src/domain/base.py`
3. Register it in `src/domain/entities/__init__.py`
4. Add a generator in `src/synthetic/generators/` if it should be synthetically generated
5. Add relationship rules in `src/synthetic/relationships.py`
6. Add tests

## Adding a New Organization Profile

1. Create a profile function in `src/synthetic/profiles/`
2. Return an `OrgProfile` with department specs, network specs, and count ranges
3. Wire it into the CLI in `src/cli/generate.py` and `src/cli/demo_cmd.py`
4. Add tests

## Reporting Bugs

Use the [bug report template](https://github.com/thehipsterciso/hc-enterprise-kg/issues/new?template=bug_report.yml) on GitHub Issues.

## Questions

Open a [Discussion](https://github.com/thehipsterciso/hc-enterprise-kg/discussions) for questions, ideas, or general feedback.
