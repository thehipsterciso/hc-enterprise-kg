# CLAUDE.md — Project Guide for AI Assistants

## Project Overview

**hc-enterprise-kg** is an open-source enterprise knowledge graph platform. It generates structurally accurate organizational models ("digital twins") with 30 entity types and 50 relationship types, enabling scenario analysis, risk modeling, and dependency mapping.

## Quick Commands

```bash
poetry run pytest tests/ -v          # Run all tests (~689)
poetry run pytest tests/performance/ -v  # Performance regression tests
poetry run ruff check src/ tests/    # Lint
poetry run hckg demo --clean         # Generate fresh graph.json
poetry run hckg demo --employees 200 # Larger org
```

## Architecture

```
src/
  domain/       # Pydantic v2 entity models (30 types), BaseEntity, EntityType/RelationshipType enums
  engine/       # AbstractGraphEngine → NetworkXGraphEngine (pluggable backend)
  graph/        # KnowledgeGraph facade, event bus, QueryBuilder
  synthetic/    # Profile-driven generators + relationship weaving + quality scoring (SyntheticOrchestrator)
  auto/         # Auto KG from CSV/text (rule-based + optional LLM)
  ingest/       # CSVIngestor, JSONIngestor with schema mappings
  export/       # JSONExporter, GraphMLExporter
  analysis/     # Centrality, risk scoring, attack paths, blast radius, benchmarking
  rag/          # GraphRAG retrieval pipeline
  cli/          # Click CLI (demo, generate, inspect, auto, serve, install, visualize, export, benchmark)
  mcp_server/   # MCP server for Claude Desktop (state.py, helpers.py, tools.py, server.py)
  serve/        # REST API server (Flask)
```

## Layer Build Order (Synthetic Generation)

L00 Foundation → L01 Compliance → L02 Technology → L03 Data → L04 Organization → L05 People → L06 Capabilities → L07 Locations → L08 Products → L09 Customers → L10 Vendors → L11 Initiatives

## Entity Types (30)

**v0.1 (12):** Person, Department, Role, System, Network, DataAsset, Policy, Vendor, Location, Vulnerability, ThreatActor, Incident

**Enterprise (18):** Regulation, Control, Risk, Threat, Integration, DataDomain, DataFlow, OrganizationalUnit, BusinessCapability, Site, Geography, Jurisdiction, ProductPortfolio, Product, MarketSegment, Customer, Contract, Initiative

## Synthetic Data Pipeline

**Scaling**: Entity counts use `scaled_range(employee_count, coefficient, floor, ceiling)` with industry-specific `ScalingCoefficients` and size-tier multipliers (0.7x startup, 1.0x mid, 1.2x enterprise, 1.4x large). Three profiles: tech, financial, healthcare.

**Generators**: All 30 generators use coordinated template dicts (not independent random). No faker.sentence()/faker.bs() — all descriptions are domain-specific. Risk levels derived from RISK_MATRIX[likelihood][impact].

**Relationships**: 33 weaver methods produce 30+ relationship types with contextual weight/confidence/properties via `_make_rel()`. Mirror fields populated post-weave.

**Quality**: `assess_quality(context) → QualityReport` checks risk math, descriptions, tech coherence, field correlations, encryption↔classification. Orchestrator warns if < 0.7.

## Key Pitfalls

1. **`extra="allow"` on BaseEntity** — Wrong field names silently go to `__pydantic_extra__`, no validation error. Always verify field names against the entity class.

2. **Sub-model fields** — Many enterprise entity fields that look like scalars are Pydantic sub-models (e.g., `Site.address` is `SiteAddress`, not `str`). Always check the entity class before writing generators.

3. **Temporal/provenance naming inconsistency** — Most entities use `temporal`/`provenance`. But Initiative, Vendor, Contract, Customer, MarketSegment, ProductPortfolio, Product use `temporal_and_versioning`/`provenance_and_confidence`. Geography/Jurisdiction use inline scalars.

4. **Relationship types are lowercase** — Stats show `"implements"` not `"IMPLEMENTS"`. The `RelationshipType` enum values are lowercase strings.

5. **EntityRegistry.auto_discover()** — Must be called before using `EntityRegistry.get()` in ingestion contexts.

## MCP Server

The MCP server (`src/mcp_server/`) provides 10 tools for Claude Desktop:
- `load_graph`, `get_statistics`, `list_entities`, `get_entity`, `get_neighbors`
- `find_shortest_path`, `get_blast_radius`, `compute_centrality`, `find_most_connected`, `search_entities`

**Auto-reload:** The server detects graph file changes via mtime checking on every tool call. After `hckg demo --clean`, Claude Desktop tools automatically pick up the new graph.

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
