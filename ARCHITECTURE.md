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
- `weight`, `properties`

50 relationship types connect entities across layers (e.g., `works_in`, `implements`, `mitigates`, `regulates`).

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
                                   → RelationshipWeaver → relationships
```

1. `OrgProfile` defines department specs, counts, and configuration
2. `SyntheticOrchestrator` resolves counts and runs generators in layer order
3. Each generator (e.g., `PersonGenerator`, `RegulationGenerator`) produces entities
4. `RelationshipWeaver` creates edges between generated entities
5. Enterprise generators add cross-layer relationships (e.g., controls → regulations)

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
