# CLAUDE.md — Project Guide for AI Assistants

## Project Overview

**hc-enterprise-kg** is an open-source enterprise knowledge graph platform. It generates structurally accurate organizational models ("digital twins") with 30 entity types and 50 relationship types, enabling scenario analysis, risk modeling, and dependency mapping. Every major design choice is documented as an [Architecture Decision Record](docs/adr/).

## Quick Commands

```bash
poetry run pytest tests/ -v          # Run all tests (~1012)
poetry run pytest tests/performance/ -v  # Performance regression tests
poetry run ruff check src/ tests/    # Lint
poetry run hckg demo --clean         # Generate fresh graph.json
poetry run hckg demo --employees 200 # Larger org
poetry run hckg import data.json     # Import real org data
poetry run hckg import people.csv -t person  # Import CSV
poetry run hckg charts               # Generate analytics charts (default: tech, 100-5000)
poetry run hckg charts --full        # All 3 profiles, 6 scales
```

## Architecture

```
src/
  domain/       # Pydantic v2 entity models (30 types), BaseEntity (ADR-002), EntityType/RelationshipType enums
  engine/       # AbstractGraphEngine → NetworkXGraphEngine (ADR-003, pluggable backend)
  graph/        # KnowledgeGraph facade (ADR-004), event bus, QueryBuilder
  synthetic/    # Profile-driven generators (ADR-001, ADR-006) + relationship weaving (ADR-008) + quality scoring
  auto/         # Auto KG from CSV/text (rule-based + optional LLM)
  ingest/       # CSVIngestor, JSONIngestor, validator, mapping_loader
  export/       # JSONExporter (ADR-012), GraphMLExporter
  analysis/     # Centrality, risk scoring, attack paths, blast radius, benchmarking, charts
  rag/          # GraphRAG retrieval pipeline
  cli/          # Click CLI (demo, generate, inspect, auto, serve, install, visualize, export, benchmark, charts)
  mcp_server/   # MCP server for Claude Desktop (ADR-009, ADR-010: state.py, helpers.py, tools.py, server.py)
  serve/        # REST API server (Flask)
```

## Layer Build Order (Synthetic Generation) — [ADR-005](docs/adr/005-layered-generation-order.md)

L00 Foundation → L01 Compliance → L02 Technology → L03 Data → L04 Organization → L05 People → L06 Capabilities → L07 Locations → L08 Products → L09 Customers → L10 Vendors → L11 Initiatives

## Entity Types (30)

**v0.1 (12):** Person, Department, Role, System, Network, DataAsset, Policy, Vendor, Location, Vulnerability, ThreatActor, Incident

**Enterprise (18):** Regulation, Control, Risk, Threat, Integration, DataDomain, DataFlow, OrganizationalUnit, BusinessCapability, Site, Geography, Jurisdiction, ProductPortfolio, Product, MarketSegment, Customer, Contract, Initiative

## Synthetic Data Pipeline

**Scaling** ([ADR-007](docs/adr/007-research-backed-scaling.md)): Entity counts use `scaled_range(employee_count, coefficient, floor, ceiling)` with industry-specific `ScalingCoefficients` and size-tier multipliers (0.7x startup, 1.0x mid, 1.2x enterprise, 1.4x large). Three profiles: tech, financial, healthcare. Departments exceeding 500 headcount are subdivided into sub-departments via `SUB_DEPARTMENT_TEMPLATES` (30+ sets). Roles expand with seniority variants (Junior/Senior/Staff) based on sub-department headcount. At 14k emp (tech): 42 depts, 301 roles.

**Count Overrides**: `SyntheticOrchestrator(kg, profile, count_overrides={"system": 500})` pins exact counts. CLI: `--systems 500 --vendors 100` (25 flags via `entity_overrides.py` decorator). `OVERRIDABLE_ENTITIES` dict in `orchestrator.py` maps CLI names → EntityType.

**Generators** ([ADR-006](docs/adr/006-coordinated-template-dicts.md)): All 30 generators use coordinated template dicts (not independent random). No faker.sentence()/faker.bs() — all descriptions are domain-specific. Risk levels derived from RISK_MATRIX[likelihood][impact].

**Relationships** ([ADR-008](docs/adr/008-relationship-weaving.md)): 33 weaver methods produce 30+ relationship types with contextual weight/confidence/properties via `_make_rel()`. Mirror fields populated post-weave.

**Quality**: `assess_quality(context) → QualityReport` checks risk math, descriptions, tech coherence, field correlations, encryption↔classification. Orchestrator warns if < 0.7.

## Key Pitfalls

1. **`extra="allow"` on BaseEntity** ([ADR-002](docs/adr/002-pydantic-v2-extra-allow.md)) — Wrong field names silently go to `__pydantic_extra__`, no validation error. Always verify field names against the entity class. Use `HCKG_STRICT=1` to catch extras during development.

2. **Sub-model fields** — Many enterprise entity fields that look like scalars are Pydantic sub-models (e.g., `Site.address` is `SiteAddress`, not `str`). Always check the entity class before writing generators.

3. **Temporal/provenance naming inconsistency** — Most entities use `temporal`/`provenance`. But Initiative, Vendor, Contract, Customer, MarketSegment, ProductPortfolio, Product use `temporal_and_versioning`/`provenance_and_confidence`. Geography/Jurisdiction use inline scalars.

4. **Relationship types are lowercase** — Stats show `"implements"` not `"IMPLEMENTS"`. The `RelationshipType` enum values are lowercase strings.

5. **EntityRegistry.auto_discover()** — Must be called before using `EntityRegistry.get()` in ingestion contexts.

## Analytics Charts

The charts module (`src/analysis/charts/`) auto-generates 8 chart types from synthetic data:

1. **Scaling Curves** — entity/relationship count vs employee count (demonstrates linearity)
2. **Entity Distribution** — stacked bar of 30 entity types across scales
3. **Relationship Distribution** — horizontal bar of top-20 relationship types
4. **Profile Comparison** — grouped bar comparing tech/financial/healthcare (requires 2+ profiles)
5. **Performance Scaling** — dual-axis: generation time + peak memory vs employee count
6. **Density vs Scale** — graph density trend as org grows
7. **Centrality Distribution** — top-15 entities by degree centrality
8. **Quality Radar** — 5-axis spider chart from QualityReport dimensions

**CLI:** `hckg charts --profiles tech,financial --scales 100,500,1000,5000 --output ./charts`
**API:** `from analysis.charts import generate_all_charts, ChartConfig`

## MCP Server

The MCP server (`src/mcp_server/`) provides 13 tools for Claude Desktop:
- **Read:** `load_graph`, `get_statistics`, `list_entities`, `get_entity`, `get_neighbors`, `find_shortest_path`, `get_blast_radius`, `compute_centrality`, `find_most_connected`, `search_entities`
- **Write:** `add_relationship_tool`, `add_relationships_batch` (atomic, max 500), `remove_relationship_tool`

**Auto-reload** ([ADR-009](docs/adr/009-mcp-mtime-auto-reload.md))**:** The server detects graph file changes via mtime checking on every tool call. After `hckg demo --clean`, Claude Desktop tools automatically pick up the new graph.

**Write tool validation** (`src/mcp_server/validation.py`)**:** All write tools validate inputs (enum membership, entity existence, domain/range schema) before mutation. `persist_graph()` in `state.py` auto-saves to disk and syncs mtime to prevent reload races.

## Architecture Decision Records

All major design choices are formally documented in `docs/adr/`. Before proposing changes to any of these areas, read the relevant ADR for context, trade-offs, and re-evaluation triggers.

| ADR | Decision |
|-----|----------|
| [001](docs/adr/001-custom-synthetic-data-pipeline.md) | Custom synthetic data pipeline over external libraries |
| [002](docs/adr/002-pydantic-v2-extra-allow.md) | Pydantic v2 with `extra="allow"` for entity models |
| [003](docs/adr/003-networkx-multidigraph.md) | NetworkX MultiDiGraph as pluggable graph backend |
| [004](docs/adr/004-knowledge-graph-facade.md) | KnowledgeGraph facade with synchronous event bus |
| [005](docs/adr/005-layered-generation-order.md) | Layered generation order for referential integrity |
| [006](docs/adr/006-coordinated-template-dicts.md) | Coordinated template dicts over random generation |
| [007](docs/adr/007-research-backed-scaling.md) | Research-backed scaling with industry coefficients |
| [008](docs/adr/008-relationship-weaving.md) | Relationship weaving as post-generation phase |
| [009](docs/adr/009-mcp-mtime-auto-reload.md) | MCP server with mtime-based auto-reload |
| [010](docs/adr/010-compact-entity-serialization.md) | Compact entity serialization for LLM context windows |
| [011](docs/adr/011-rapidfuzz-search.md) | rapidfuzz over embedding-based search |
| [012](docs/adr/012-json-primary-export.md) | JSON as primary export format |

## Engineering Discipline (non-negotiable)

### Versioning: Major.Minor.Patch
- **Every discrete change gets its own patch bump** — never batch multiple changes into one version
- Minor bump: new feature area or capability grouping
- Patch bump: each individual enhancement, bug fix, or doc change

### Execution Order for ANY Change
1. Create GitHub issue (one per discrete change)
2. Create branch from `main`, push to remote
3. Implement the single change
4. Tests pass, lint clean
5. Commit, push, create PR referencing issue
6. Merge → bump version (patch) → tag → `gh release create`
7. Close issue
8. Update CHANGELOG, README, ARCHITECTURE, CLAUDE.md

## Testing Patterns

- Engine contract tests in `tests/unit/engine/test_contract.py`
- MCP tool tests call tools via `mcp._tool_manager._tools` registry
- Synthetic pipeline integration tests in `tests/integration/test_synthetic_pipeline.py`
- Stress tests (100-20k employees) in `tests/integration/test_stress.py`
- Quality scoring tests in `tests/unit/synthetic/test_quality.py`
- Relationship enrichment tests in `tests/unit/synthetic/test_relationship_enrichment.py`
- Performance regression tests in `tests/performance/` (run with `make benchmark`)
- Ingestor tests in `tests/unit/ingest/`
- Import CLI tests in `tests/unit/cli/test_import_cmd.py`
- Import template integration tests in `tests/integration/test_import_templates.py`
- Schema inference tests in `tests/unit/auto/test_schema_inference.py`
- MCP validation tests in `tests/unit/mcp_server/test_mcp_validation.py`
- MCP write tool tests in `tests/unit/mcp_server/test_write_tools.py`
