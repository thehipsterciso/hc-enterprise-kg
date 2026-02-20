# Architecture

This document describes the high-level architecture of hc-enterprise-kg.

## System Overview

```
┌─────────────────────────────────────────────────────────────┐
│                        CLI (Click)                          │
│  demo | generate | inspect | auto | serve | install | viz   │
└─────────────┬───────────────┬───────────────┬───────────────┘
              │               │               │
    ┌─────────▼──────┐  ┌────▼────┐  ┌───────▼───────┐
    │   Synthetic    │  │  Auto   │  │    Ingest     │
    │  Orchestrator  │  │ Pipeline│  │ CSV/JSON      │
    └─────────┬──────┘  └────┬────┘  └───────┬───────┘
              │               │               │
              └───────────────┼───────────────┘
                              │
              ┌───────────────▼───────────────┐
              │      KnowledgeGraph Facade    │
              │  query() | neighbors() | ...  │
              └───────────────┬───────────────┘
                              │
              ┌───────────────▼───────────────┐
              │     AbstractGraphEngine       │
              │      (NetworkX backend)       │
              └───────────────────────────────┘
                              │
         ┌────────────────────┼────────────────────┐
         │                    │                    │
    ┌────▼─────┐      ┌──────▼──────┐     ┌──────▼──────┐
    │  Export  │      │  Analysis  │     │  MCP/REST  │
    │ JSON/GML│      │  Metrics   │     │  Servers   │
    └──────────┘      └─────────────┘     └─────────────┘
```

## Layer Model

The synthetic generator builds entities in a specific order to ensure referential integrity. Each layer can reference entities from previous layers.

| Layer | Name | Entity Types |
|---|---|---|
| L00 | Foundation | Shared sub-models, enums, base classes |
| L01 | Compliance | Regulation, Control, Risk, Threat |
| L02 | Technology | System (extended), Integration |
| L03 | Data | DataAsset (extended), DataDomain, DataFlow |
| L04 | Organization | OrganizationalUnit |
| L05 | People | Person (extended), Role (extended) |
| L06 | Capabilities | BusinessCapability |
| L07 | Locations | Site, Geography, Jurisdiction |
| L08 | Products | ProductPortfolio, Product |
| L09 | Customers | MarketSegment, Customer |
| L10 | Vendors | Vendor (extended), Contract |
| L11 | Initiatives | Initiative |

## Domain Model

### Entity Hierarchy

All entities extend `BaseEntity` which provides:
- `id` (UUID, auto-generated)
- `entity_type` (EntityType enum)
- `name` (string)
- `description`, `tags`, `metadata`
- `created_at`, `updated_at`, `valid_from`, `valid_until`, `version`

Entity types are registered in `EntityRegistry` and resolved via `EntityType` enum values.

### Relationship Model

All relationships use `BaseRelationship`:
- `id` (UUID, auto-generated)
- `relationship_type` (RelationshipType enum)
- `source_id`, `target_id`
- `weight` (contextual: severity-based, variance, or fixed — not all 1.0)
- `confidence` (0.70 for uncertain attribution to 0.95 for organizational fact)
- `properties` (contextual key-value pairs: dependency_type, exploit_maturity, severity, enforcement, etc.)

50 relationship types defined, 30+ actively woven by `RelationshipWeaver`. Domain/range constraints enforced via `RELATIONSHIP_SCHEMA` in `relationship_schema.py`.

## Engine Abstraction

`AbstractGraphEngine` defines the graph operations contract:
- Entity CRUD: `add_entity`, `get_entity`, `update_entity`, `remove_entity`
- Relationship CRUD: `add_relationship`, `get_relationship`, `remove_relationship`
- Traversal: `neighbors`, `shortest_path`, `blast_radius`
- Introspection: `get_statistics`, `entity_count`, `relationship_count`

`NetworkXGraphEngine` is the default implementation backed by `nx.MultiDiGraph`. Entities are nodes (attrs = model dict), relationships are edges keyed by relationship ID.

The engine is pluggable — `AbstractGraphEngine` can be implemented with Neo4j or any other graph backend without changing the rest of the stack.

## Synthetic Pipeline

```
OrgProfile → SyntheticOrchestrator → [Generator per type] → KnowledgeGraph
                                   → RelationshipWeaver  → relationships (enriched)
                                   → QualityAssessment   → QualityReport
```

1. `OrgProfile` defines department specs and industry-specific `ScalingCoefficients`
2. `SyntheticOrchestrator` resolves counts via `scaled_range()` (industry coefficient × size-tier multiplier) and runs generators in layer order
3. Each generator uses **coordinated template dicts** — related fields are pre-mapped (e.g., system name ↔ OS ↔ tech stack ↔ ports), not independently random
4. `RelationshipWeaver` creates 30+ relationship types with contextual weight, confidence, and properties via `_make_rel()` helper
5. `_populate_mirror_fields()` denormalizes relationship edges into entity fields (Person.holds_roles, Role.filled_by_persons, etc.)
6. `assess_quality()` runs 5 automated checks (risk math, description quality, tech coherence, field correlation, encryption↔classification) and produces a `QualityReport`

### Industry-Aware Scaling

Entity counts scale with employee count using `ScalingCoefficients` per industry:

| Industry | Systems (coeff) | Controls (coeff) | Data Assets (coeff) |
|---|---|---|---|
| Technology | 1:8 employees | 1:50 | 1:15 |
| Financial Services | 1:12 | 1:20 (2.5x tech) | 1:10 |
| Healthcare | 1:15 | 1:25 | 1:5 (3x tech) |

Size-tier multipliers: startup 0.7x (<250), mid-market 1.0x, enterprise 1.2x (2k-10k), large 1.4x (>10k).

### Quality Scoring

`src/synthetic/quality.py` provides `assess_quality(context) → QualityReport`:
- **Risk math consistency**: level = RISK_MATRIX[likelihood][impact]
- **Description quality**: regex detection of lorem ipsum / faker patterns
- **Tech stack coherence**: appliance types shouldn't have web frameworks
- **Field correlation**: residual ≤ inherent, patch ↔ status, site security ↔ type
- **Encryption ↔ classification**: restricted/confidential data encrypted in transit

## MCP Server

The MCP server (`src/mcp_server/`) exposes 10 tools to Claude Desktop:

| Module | Purpose |
|---|---|
| `server.py` | FastMCP instance creation and entry point |
| `state.py` | Graph loading, mtime-based auto-reload, `require_graph()` |
| `helpers.py` | Entity/relationship serialization to compact JSON |
| `tools.py` | All 10 tool definitions via `register_tools()` |

**Auto-reload**: Before every tool call, `require_graph()` checks the graph file's mtime. If changed, it transparently reloads. This means `hckg demo --clean` is immediately reflected in Claude Desktop without restart.

## Data Flow

### Generation
```
Profile → Orchestrator → Generators → KnowledgeGraph → JSONExporter → graph.json
```

### MCP Query
```
Claude Desktop → MCP tool call → require_graph() (auto-reload) → KnowledgeGraph → compact response
```

### Ingestion
```
CSV/JSON file → Ingestor (with schema mapping + transforms) → IngestResult (entities + relationships)
```

## Key Design Decisions

1. **Pydantic v2 for entities** — Runtime validation, JSON serialization, and IDE support. `extra="allow"` enables forward compatibility but requires careful field naming.

2. **NetworkX MultiDiGraph** — Supports multiple edges between same nodes (common in enterprise graphs), directed relationships, and rich node/edge attributes. In-memory, no external dependencies.

3. **mtime-based reload** — Zero-dependency file change detection. Checked on every tool call (microsecond cost) rather than file watching (which requires extra threads/dependencies).

4. **Profile-driven generation** — Industry profiles (tech, healthcare, financial) control generation parameters. Easy to add new profiles without changing generators.

5. **Layer-ordered generation** — Ensures referential integrity. L01 entities exist before L02 entities reference them.
