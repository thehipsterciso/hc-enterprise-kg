# ADR-012: JSON as Primary Export Format

**Status:** Accepted
**Date:** 2026-02-21
**Context:** Graph export and interchange format selection

---

## Summary

The primary export format is a flat JSON file with `{"entities": [...], "relationships": [...], "statistics": {...}}`. GraphML is supported as a secondary format for graph visualization tools (Gephi, yEd). No other export formats are implemented.

This choice optimizes for human readability, universal parseability, and round-trip fidelity with Pydantic models. It explicitly does not optimize for graph database import, semantic web interchange, or large-scale data processing.

---

## Decision

Use flat JSON as the primary export and interchange format. Support GraphML as a secondary format for visualization.

---

## The JSON Structure

```json
{
  "entities": [
    {
      "id": "uuid",
      "entity_type": "system",
      "name": "Jenkins CI",
      "description": "Continuous integration server",
      "system_type": "application",
      "technologies": ["java", "groovy"],
      ...
    }
  ],
  "relationships": [
    {
      "id": "uuid",
      "relationship_type": "depends_on",
      "source_id": "uuid",
      "target_id": "uuid",
      "weight": 0.85,
      "confidence": 0.92,
      "properties": {"dependency_type": "runtime"}
    }
  ],
  "statistics": {
    "entity_count": 277,
    "relationship_count": 543,
    ...
  }
}
```

Entities and relationships are stored as Pydantic `model_dump(mode="json")` output. The format round-trips perfectly: export via `JSONExporter`, re-import via `JSONIngestor`, `model_validate()` reconstructs the original Pydantic objects.

---

## Alternatives Considered

| Alternative | Assessment |
|-------------|------------|
| **Neo4j CSV import format** | `nodes.csv` + `relationships.csv` with Neo4j-specific headers. Couples the export to a specific database. Complex attributes (lists, nested dicts) require custom encoding. The project does not assume Neo4j as the target |
| **RDF / Turtle / N-Triples** | Native semantic web interchange. Triple-based model (subject-predicate-object) is fundamentally different from the project's property graph model (typed nodes with rich attributes, typed edges with weight/confidence/properties). Converting to RDF would lose the property graph semantics or require reification |
| **JSON-LD** | JSON format with linked data semantics. Adds `@context`, `@id`, `@type` overhead. Designed for web-scale data linking, not local graph interchange. The project does not participate in the linked data ecosystem |
| **Pickle / binary serialization** | Fastest serialization, smallest file size. Not human-readable, not portable across Python versions, security risk on deserialization (arbitrary code execution). Unacceptable for a format that users inspect and share |
| **SQLite database file** | Persistent, queryable, single-file. Adds SQLite dependency for consumers. Not human-readable. Overkill for a read-once export that gets loaded into memory |
| **Parquet / Arrow columnar format** | Excellent for large-scale data processing. Not human-readable. Designed for tabular data, not graph data with variable-schema entities. Complex attributes require encoding |

---

## Why GraphML as Secondary

GraphML is an XML-based graph format supported natively by NetworkX (`nx.write_graphml()`), Gephi, yEd, Cytoscape, and other graph visualization tools. It is the simplest path from "generated graph" to "visual exploration."

GraphML limitations are accepted:
- Complex attributes (lists, dicts, booleans, None) are converted to strings. Type fidelity is lost
- The exported GraphML cannot be re-imported to reconstruct Pydantic entities. It is a one-way format for visualization
- XML verbose compared to JSON

---

## Where This Diverges from Best Practice

### No Graph Database Export

The most common request for a "knowledge graph platform" would be export to Neo4j, Amazon Neptune, or TigerGraph. The project does not support any graph database import format. Users who want to load the graph into Neo4j must write their own importer.

This is deliberate. The project positions itself as a pre-engagement analysis tool, not a production data platform. The graph is consumed in-memory via MCP, REST API, or Python API. If users need persistent graph database storage, they are past the "scenario analysis" stage and into production data management.

### No Incremental Export

The entire graph is exported every time. There is no diff-based export, no changelog export, no streaming export. A change to one entity requires re-exporting the complete graph.

For generation-and-analysis workflows (generate graph, export, analyze, regenerate), this is acceptable. For an evolving graph with continuous mutations, incremental export would be necessary.

### File Size at Scale

A 5,000-employee graph with ~1,500 entities and ~3,000 relationships produces a ~5 MB JSON file. A 20,000-employee graph approaches 20 MB. JSON is verbose — every field name is repeated for every entity.

This is within acceptable limits for the project's purpose. The file is generated once, loaded once, and discarded when a new graph is generated. It is not a streaming data format or a wire protocol.

---

## Trade-Offs

| Benefit | Cost |
|---------|------|
| Human-readable, inspectable in any text editor | Verbose — field names repeated per entity |
| Universal parseability (every language has a JSON parser) | No graph database import support |
| Perfect round-trip with Pydantic `model_dump()` / `model_validate()` | No incremental export |
| Git-friendly (text diffs show exactly what changed) | Multi-megabyte files at scale |
| GraphML secondary for visualization tools | GraphML loses type fidelity (everything becomes strings) |

---

## Risks

1. **User expectation mismatch** -- Users expecting Neo4j/Neptune import support will be disappointed. Mitigated by clear documentation of what the project is (scenario analysis tool, not ETL pipeline)
2. **File size growth** -- At 50,000+ entities, JSON files become unwieldy. Mitigated by the current scale ceiling (~20,000 employees, ~5,000 entities)
3. **GraphML fidelity loss** -- Users who export to GraphML and expect to round-trip back to the original model will lose data. Mitigated by documenting GraphML as a visualization-only format

---

## Re-Evaluation Triggers

- Demand for Neo4j or Neptune import format from users who need persistent graph storage
- File sizes exceeding 50 MB where JSON verbosity becomes a practical problem
- Need for incremental or streaming export in an evolving-graph use case
- A standard graph interchange format (like GEXF 2.0 or a future standard) gaining enough adoption to justify implementation

---

## References

- `src/export/json_export.py` -- `JSONExporter` with `export()` and `export_string()`
- `src/export/graphml_export.py` -- `GraphMLExporter` with string attribute conversion
- `src/export/base.py` -- `AbstractExporter` interface
- `src/ingest/json_ingestor.py` -- `JSONIngestor` for round-trip import
