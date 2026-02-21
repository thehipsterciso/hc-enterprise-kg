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
make test          # Run all tests (~756)
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
- `refactor/description` for refactoring
- `docs/description` for documentation changes
- `test/description` for test additions
- `chore/description` for maintenance

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

### Pitfalls to watch for

- **`extra="allow"` on BaseEntity** ([ADR-002](docs/adr/002-pydantic-v2-extra-allow.md)) — Wrong field names silently go to `__pydantic_extra__` instead of raising validation errors. This is the most common bug source in the project. Always double-check field names against the entity class. Use `HCKG_STRICT=1` to catch extras during development.
- **Sub-model fields** — Many enterprise entity fields that look like scalars are actually Pydantic sub-models (e.g., `Site.address` is `SiteAddress`, not `str`). Always verify against the entity class before writing generators.
- **Temporal/provenance naming** — Most entities use `temporal`/`provenance` fields. But Initiative, Vendor, Contract, Customer, MarketSegment, ProductPortfolio, and Product use `temporal_and_versioning`/`provenance_and_confidence`. Geography and Jurisdiction use inline scalars instead.
- **Layer ordering** ([ADR-005](docs/adr/005-layered-generation-order.md)) — New entity types must be placed correctly in `GENERATION_ORDER` so they can reference entities from earlier layers.

## Adding a New Organization Profile

1. Create a profile function in `src/synthetic/profiles/`
2. Return an `OrgProfile` with department specs, network specs, and count ranges
3. Wire it into the CLI in `src/cli/generate.py` and `src/cli/demo_cmd.py`
4. Add tests

## MCP Server Development

The MCP server lives in `src/mcp_server/` with four modules:
- `state.py` — Graph state management with mtime-based auto-reload
- `helpers.py` — Entity/relationship serialization helpers
- `tools.py` — All 10 `@mcp.tool()` definitions via `register_tools()`
- `server.py` — Slim entry point

To test MCP tools directly:
```python
from mcp_server.server import mcp
for tool in mcp._tool_manager._tools.values():
    if tool.name == "list_entities":
        result = tool.fn(entity_type="person")
```

## Reporting Bugs

Use the [bug report template](https://github.com/thehipsterciso/hc-enterprise-kg/issues/new?template=bug_report.yml) on GitHub Issues.

## Documentation

Detailed reference documentation lives in `docs/`:

| Document | Description |
|---|---|
| [Entity Model Reference](docs/entity-model.md) | All 30 entity types, 52 relationship types, generation layers |
| [CLI Reference](docs/cli.md) | All commands with options, defaults, examples |
| [Python API Guide](docs/python-api.md) | Generation, querying, analysis, exporting |
| [Organization Profiles](docs/profiles.md) | Industry profiles, scaling model, quality scoring |
| [Performance & Benchmarking](docs/performance.md) | Benchmark results, scaling, memory, system requirements |
| [Troubleshooting](docs/troubleshooting.md) | Common issues, setup, examples |
| [Architecture Decision Records](docs/adr/) | Design rationale for all major architectural choices |

## Architecture Decision Records

Every significant design choice is documented as an ADR in `docs/adr/`. If your contribution changes or challenges an existing architectural decision, update the relevant ADR or propose a new one.

### When to Write an ADR

- You are introducing a new library, framework, or backend
- You are changing a data model, serialization format, or API contract
- You are replacing or significantly modifying an existing pattern (e.g., switching search strategies, changing the graph backend)
- You are making a trade-off that future contributors will need to understand

### ADR Structure

Follow the existing format in `docs/adr/`:

1. **Title and status** — One-line decision statement, date, status (Accepted / Superseded / Deprecated)
2. **Context** — What problem or requirement prompted this decision
3. **Decision** — What was chosen and why
4. **Alternatives Considered** — What was evaluated and rejected, with specific reasons
5. **Where This Diverges from Best Practice** — Honest assessment of trade-offs and known limitations
6. **Consequences** — What follows from the decision (positive and negative)
7. **Re-evaluation Triggers** — Concrete conditions that would warrant revisiting this decision

ADRs are living documents. If the project outgrows a decision, the ADR gets updated with a superseding record — it does not get deleted. The historical record matters.

## Questions

Open a [Discussion](https://github.com/thehipsterciso/hc-enterprise-kg/discussions) for questions, ideas, or general feedback.
