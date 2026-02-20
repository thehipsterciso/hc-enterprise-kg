# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/), and this project adheres to [Semantic Versioning](https://semver.org/).

## [0.17.0] - 2026-02-20

### Added
- **CSVIngestor transforms** — `FieldMapping.transform` now applied during ingestion (lowercase, uppercase, strip, int, float, bool)
- **CSVIngestor relationship mappings** — `SchemaMapping.relationship_mappings` processed after entity ingestion
- **JSONIngestor.ingest_string()** — In-memory JSON ingestion with shared core logic
- **25 new ingestor tests**

## [0.16.0] - 2026-02-20

### Changed
- **MCP server modularization** — Split monolithic server.py into `state.py`, `helpers.py`, `tools.py`, `server.py`
- **Blast radius to engine layer** — Moved BFS from MCP tool to `AbstractGraphEngine.blast_radius()`
- **Safe update_entity** — Copy-validate-write pattern prevents in-place corruption; invalid updates raise `ValueError`
- **ID prefix comments** — Aligned schema comments with generator output (REG-/CTL-/RSK-/THR-)

### Fixed
- `datetime.utcnow()` deprecation in `update_entity` (now uses `datetime.now(UTC)`)

## [0.15.0] - 2026-02-20

### Fixed
- **MCP auto-reload** — Server detects graph file changes via mtime checking, transparently reloads on every tool call
- **RoleGenerator** — Now executes; roles generated for all departments (was returning count 0)
- **Version sync** — `__version__` uses `importlib.metadata` for single-source truth
- **Deserialization logging** — `_deserialize_entity/relationship` now logs errors instead of silently swallowing them

### Removed
- **stubs.py** — Empty file removed; all entity stubs replaced by full implementations

## [0.14.0] - 2026-02-19

### Added
- **Enterprise synthetic generators** for all 18 L01-L11 entity types
- **10 cross-layer relationship weaving methods** connecting entities across layers
- **Enterprise integration tests** for full 30-type synthetic pipeline
- **Extended sample_entities.json** with all enterprise entity types

## [0.13.0] - 2026-02-19

### Added
- **Initiative entity** — Full implementation replacing last stub (~80 attributes)
- **Initiative test suite** — 14 tests

## [0.12.0] - 2026-02-19

### Added
- **Extended Vendor entity** with contract, compliance, and risk attributes
- **Contract entity** — Vendor contracts with SLAs, financial terms, compliance
- **Test suite** for extended Vendor and Contract entities

## [0.11.0] - 2026-02-19

### Added
- **MarketSegment entity** — Target markets with demographics and sizing
- **Customer entity** — Customer accounts with revenue, satisfaction, lifecycle
- **Test suite** for MarketSegment and Customer entities

## [0.10.0] - 2026-02-19

### Added
- **ProductPortfolio entity** — Product groupings with strategy and lifecycle
- **Product entity** — Individual products with pricing, compliance, and metrics
- **Test suite** for ProductPortfolio and Product entities

## [0.9.0] - 2026-02-19

### Added
- **Site entity** (~91 attributes) — Physical facilities with address, capacity, compliance
- **Geography entity** (~20 attributes) — Geographic regions and territories
- **Jurisdiction entity** (~18 attributes) — Regulatory jurisdictions
- **Locations test suite** — 18 tests

## [0.8.0] - 2026-02-19

### Added
- **BusinessCapability entity** (~90 attributes) — L1/L2/L3 capability hierarchy with maturity assessment
- **Business capabilities test suite** — 12 tests

## [0.7.0] - 2026-02-19

### Added
- **Extended Person entity** (~64 attributes) — Security clearance, emergency contact, career progression
- **Extended Role entity** (~65 attributes) — Permissions, compliance requirements, succession planning
- **People & roles test suite** — 20 tests

## [0.6.0] - 2026-02-19

### Added
- **OrganizationalUnit entity** (~100 attributes) — Business units, divisions, subsidiaries
- **Organization test suite**

## [0.5.0] - 2026-02-19

### Added
- **Extended DataAsset entity** — Expanded with governance, lineage, and quality attributes
- **DataDomain entity** — Logical data groupings with ownership
- **DataFlow entity** — Data movement between systems
- **Data assets test suite**

## [0.4.0] - 2026-02-19

### Added
- **Extended System entity** (~119 attributes) — Full enterprise system modeling
- **Integration entity** (~30 attributes) — System-to-system integrations
- **Technology test suite**

## [0.3.0] - 2026-02-19

### Added
- **Regulation entity** — Laws and standards with compliance tracking
- **Control entity** — Security/compliance controls (SCF-aligned)
- **Risk entity** — Enterprise risks with scoring and treatment
- **Threat entity** — Threat catalog entries (MITRE ATT&CK-aligned)
- **Extended Policy entity** — Added compliance mapping and enforcement
- **Compliance test suite**

## [0.2.0] - 2026-02-19

### Added
- **Enterprise ontology foundation** — Expanded EntityType and RelationshipType enums (30 types, 50 relationships)
- **Shared sub-models** — TemporalAndVersioning, ProvenanceAndConfidence, and other reusable Pydantic models
- **Stub entity classes** for all 18 new enterprise types
- **Backward compatibility tests** and shared sub-model tests

## [0.1.0] - 2025-02-19

### Added
- **Core knowledge graph** with KnowledgeGraph facade, event bus, and query builder
- **12 entity types**: Person, Department, Role, System, Network, Data Asset, Policy, Vendor, Location, Vulnerability, Threat Actor, Incident
- **19 relationship types**: works_in, reports_to, manages, connects_to, depends_on, stores, governs, exploits, affects, supplied_by, and more
- **Synthetic data generation** with profile-driven orchestrator and Faker-based generators
- **3 organization profiles**: tech company, healthcare org, financial services
- **Auto KG construction** from CSV and text with rule-based extraction
- **CLI tool (`hckg`)** with demo, generate, inspect, auto, export commands
- **Export formats**: JSON and GraphML
- **Analysis module** with centrality metrics, risk scoring, attack paths, blast radius
- **NetworkX graph backend** with pluggable engine abstraction
- **MCP server** — 10 tools for Claude Desktop integration
- **REST API server** — Flask-based with OpenAI-compatible endpoints
- **GraphRAG retrieval pipeline**
- **Interactive visualization** via pyvis
- **`hckg serve`** — Unified server with REST and MCP stdio modes
- **`hckg install`** — Register with Claude Desktop
- **124 tests** (unit + integration)
