# ADR-003: NetworkX MultiDiGraph as Graph Backend

**Status:** Accepted
**Date:** 2026-02-21
**Context:** Graph storage engine selection and abstraction strategy

---

## Summary

The graph storage backend is NetworkX's `MultiDiGraph`, an in-memory directed multigraph. It runs behind a 20-method `AbstractGraphEngine` interface that makes the backend pluggable. This decision trades scalability and persistence for zero operational overhead and deployment simplicity.

---

## Decision

Use `nx.MultiDiGraph` as the default (and currently only) graph backend, accessed exclusively through the `AbstractGraphEngine` abstraction.

---

## Why MultiDiGraph Specifically

The choice of `MultiDiGraph` over other NetworkX graph types is deliberate:

| Graph Type | Directed | Multi-Edge | Fit |
|------------|----------|------------|-----|
| `Graph` | No | No | Cannot model directional relationships (`manages`, `depends_on`) |
| `DiGraph` | Yes | No | Cannot model multiple relationships between the same pair of entities |
| `MultiGraph` | No | Yes | Directionality is essential for organizational modelling |
| **`MultiDiGraph`** | **Yes** | **Yes** | **Correct model for enterprise knowledge graphs** |

Enterprise graphs routinely have multiple directed edges between the same nodes. A person can both `WORKS_IN` and `MANAGES` a department. Two systems can have both `DEPENDS_ON` and `CONNECTS_TO` relationships with different properties. `MultiDiGraph` is the only NetworkX type that models this correctly.

---

## Alternatives Considered

| Alternative | Assessment |
|-------------|------------|
| **Neo4j** | The industry standard for graph databases. Native Cypher queries, ACID transactions, horizontal scaling, persistence. Rejected because it requires a running database server, Java runtime, operational management, and network configuration. For a tool positioned as "run in seconds without standing up a production data platform," an external database contradicts the value proposition |
| **igraph (python-igraph)** | Faster than NetworkX for large-scale analytics (C core). Less Pythonic API, weaker attribute support on nodes/edges, smaller ecosystem. Would require significant adapter code for rich entity/relationship attribute storage |
| **graph-tool** | Fastest Python graph library (C++/Boost core). Excellent for analytics but heavy dependency (compiled C++), GPL license, harder to install. Overkill for the scale this project targets |
| **RDFLib / triple stores** | Native semantic web support, SPARQL queries, ontology reasoning. Wrong data model — we use a property graph (typed nodes with rich attributes and typed, weighted, directional edges), not RDF triples |
| **Dict-of-dicts adjacency structure** | Zero dependencies, complete control. Too low-level — would require reimplementing shortest_path, centrality, PageRank, BFS, and every graph algorithm from scratch |
| **SQLAlchemy / relational** | Mature, persistent, ACID. Graph traversal queries are complex and slow in SQL (recursive CTEs, multiple joins). Poor fit for blast radius, centrality, and path analysis |

---

## Rationale

1. **Zero infrastructure** -- `pip install networkx`. No server, no configuration, no connection strings. The graph exists in the Python process
2. **Rich node/edge attributes** -- Entities are stored as node attributes via `model_dump()`. Relationships are stored as edge attributes with weight, confidence, and typed properties. NetworkX supports arbitrary Python dicts on every node and edge
3. **Built-in algorithms** -- `nx.shortest_path()`, `nx.degree_centrality()`, `nx.betweenness_centrality()`, `nx.pagerank()`, `nx.density()`, `nx.is_weakly_connected()` are all single function calls. No algorithm reimplementation required
4. **Pluggable backend** -- The `AbstractGraphEngine` ABC defines 20 abstract methods spanning CRUD, traversal, analytics, bulk operations, and introspection. `GraphEngineFactory` provides `register()` and `auto_discover()`. Swapping to Neo4j means implementing one class, not rewriting the application

---

## Where This Diverges from Best Practice

For a "knowledge graph platform," the conventional choice would be Neo4j, Amazon Neptune, or a similar graph database. We chose an in-memory library instead.

### The Scalability Ceiling

NetworkX stores the entire graph in Python memory. At 20,000 employees (~2,500 entities, ~5,000 relationships), memory usage is tens of megabytes and all operations complete in seconds. This is adequate for the project's stated target range (100-20,000 employees).

It will not scale to millions of nodes. If the project needs to model an organization with 100,000+ employees or ingest production data at enterprise scale, NetworkX is the bottleneck. The `AbstractGraphEngine` abstraction exists specifically for this eventuality — but the second backend has not been built.

### No Persistence

The graph lives in memory. Export to JSON. Re-import from JSON. There is no incremental persistence, no transactions, no crash recovery. The generation pipeline runs in seconds, so regeneration is cheap, but this model does not support a live, evolving graph that persists between sessions.

### Single-Process Model

No concurrent access. The MCP server, REST API, and CLI all assume a single-process model with a single graph instance. This is acceptable for a scenario-analysis tool but would not support multi-user access.

---

## The Pluggable Backend Abstraction

The `AbstractGraphEngine` interface is the insurance policy:

- **20 abstract methods** cover entity CRUD (5), relationship CRUD (4), traversal (3), analytics (4 as `NotImplementedError`), bulk operations (2), and introspection (3)
- **`blast_radius()`** has a default BFS implementation in the abstract class, overridable for backend-specific optimization
- **Analytics methods** (`degree_centrality`, `betweenness_centrality`, `pagerank`, `most_connected`) raise `NotImplementedError` in the base class — each backend must provide its own implementation
- **`GraphEngineFactory.register(name, cls)`** and **`auto_discover()`** provide the registration mechanism

No consumer of the graph (KnowledgeGraph facade, synthetic pipeline, MCP server, REST API, analysis module) imports `NetworkXGraphEngine` directly. Everything goes through `AbstractGraphEngine`. This means a Neo4j backend, when built, requires zero changes to any other module.

---

## Trade-Offs

| Benefit | Cost |
|---------|------|
| Zero operational overhead | Cannot scale beyond ~20k employees in memory |
| Single `pip install` deployment | No persistence between sessions |
| Built-in graph algorithms | Single-process, no concurrent access |
| Pluggable backend for future migration | Second backend not yet implemented |
| Complete control over data model | No native query language (no Cypher, no SPARQL) |

---

## Risks

1. **Backend lock-in despite abstraction** -- The abstraction exists but has only one implementation. Untested abstractions rot. Mitigated by engine contract tests in `tests/unit/engine/test_contract.py`
2. **Memory pressure at scale** -- Large organizations with many entities may approach memory limits. Mitigated by stress tests validating 20k employees and the performance benchmarking suite
3. **Algorithm performance** -- `betweenness_centrality` scales super-linearly with graph size. At 5,000+ employees it becomes the slowest operation. Mitigated by recommending `degree_centrality` or `pagerank` for large graphs

---

## Re-Evaluation Triggers

- User demand for persistent, evolving graphs (not regenerated each session)
- Need to model organizations with 100,000+ employees
- Multi-user access requirements (concurrent reads/writes)
- A contributor submits a Neo4j backend implementation

---

## References

- `src/engine/abstract.py` -- `AbstractGraphEngine` (20 abstract methods + 4 analytics + BFS)
- `src/engine/networkx_engine.py` -- `NetworkXGraphEngine` implementation
- `src/engine/factory.py` -- `GraphEngineFactory` with registration and auto-discovery
- [NetworkX Documentation](https://networkx.org/documentation/stable/) -- MultiDiGraph reference
