# ADR-011: rapidfuzz over Embedding-Based Search

**Status:** Accepted
**Date:** 2026-02-21
**Context:** Entity search strategy across MCP, REST, and RAG pipelines

---

## Summary

Entity search uses rapidfuzz's `WRatio` scorer for fuzzy string matching against entity names. The same approach is used in the MCP server, REST API, and RAG retrieval pipeline. No embeddings, no vector database, no external API calls. Search completes in sub-millisecond time with zero infrastructure.

This prioritizes simplicity and zero-dependency operation over semantic understanding.

---

## Decision

Use rapidfuzz fuzzy string matching for all entity search. Do not use embedding-based semantic search.

---

## How It Works

```python
# GraphSearch.search_by_name()
matches = process.extract(
    query,                    # User's search string
    names,                    # All entity names in the graph
    scorer=fuzz.WRatio,       # Weighted ratio scorer
    limit=top_k,              # Max results
)
# Filter results below 50.0 score threshold
```

`WRatio` (Weighted Ratio) combines multiple string similarity algorithms (ratio, partial ratio, token sort ratio, token set ratio) and returns the best score. It handles partial matches, out-of-order tokens, and abbreviations.

---

## Alternatives Considered

| Alternative | Assessment |
|-------------|------------|
| **OpenAI/Sentence-Transformers embeddings with vector similarity** | Semantic understanding: "authentication system" finds "SSO Gateway." Requires embedding model (local or API), vector store (FAISS/Chroma), embedding computation on graph load, and either an API key or a multi-GB model download. Adds seconds of latency per search and a significant dependency chain. For a graph with <5,000 entities, the complexity is not justified |
| **Elasticsearch / OpenSearch** | Full-text search with BM25 ranking, fuzzy matching, analyzers. Requires a running search server (Java, Docker). Contradicts the zero-infrastructure positioning. Would be appropriate for 100,000+ entity graphs |
| **SQLite FTS5** | Embedded full-text search. No external server. Good for structured text search. Requires building and maintaining an FTS index alongside the graph. Adds a second data store. The graph already supports linear scan in sub-millisecond time |
| **Simple substring matching** | `if query.lower() in entity.name.lower()`. Simplest possible approach. No fuzzy matching — "Jenkin" would not find "Jenkins CI." Too brittle for real-world queries |
| **No search (ID-based lookups only)** | Force users to know entity IDs. Unusable for exploratory analysis, which is the primary use case |

---

## Rationale

1. **Zero infrastructure** -- rapidfuzz is a compiled Python/C library. `pip install rapidfuzz`. No server, no API key, no model download, no vector store
2. **Sub-millisecond execution** -- Linear scan of all entity names with `WRatio` scoring completes in <1ms for graphs with <5,000 entities. The computation is CPU-bound string comparison, not network I/O
3. **Consistent implementation** -- The same `GraphSearch.search_by_name()` method is used in MCP tools (`search_entities`), REST API (`handle_search`), and RAG retrieval (`GraphRAGRetriever`). One implementation, one behavior
4. **Good-enough matching** -- `WRatio` handles the common search patterns: partial names ("Jenkins" matches "Jenkins CI"), out-of-order tokens ("CI Jenkins" matches "Jenkins CI"), abbreviations, and typos

---

## Where This Diverges from Best Practice

### No Semantic Understanding

Fuzzy string matching operates on character sequences, not meaning. Searching "authentication system" will not find "SSO Gateway" because the strings share zero characters. Searching "vulnerable servers" will not find "Compromised Production Web Server" unless the query happens to contain overlapping substrings.

For the synthetic knowledge graph, this limitation is partially mitigated by the coordinated template system (ADR-006): entity names are descriptive and domain-specific ("Jenkins CI Server," "PCI DSS Compliance," "Customer Data Lake"), so keyword-based queries produce reasonable results. For a graph with cryptic entity names, fuzzy matching would be significantly less useful.

### Linear Scan, No Index

Every search scans all entity names in the graph. At 5,000 entities, this is sub-millisecond. At 500,000 entities, it would be seconds. There is no inverted index, no pre-computed similarity matrix, no spatial data structure for approximate nearest neighbors.

The project's target range (100-20,000 employees, producing <5,000 entities) makes this acceptable. Scaling beyond that range would require an index.

### Fixed Score Threshold

The 50.0 score threshold is hardcoded. It filters noise but may exclude valid low-confidence matches for short entity names. "HR" searching against "Human Resources Department" scores lower than "Jenkins CI" searching against "Jenkins." The threshold is not tunable by the caller.

### No Query Understanding

The search has no concept of query intent. "What systems are vulnerable?" is treated as a name search for entities containing those words. The RAG pipeline adds keyword extraction and entity type detection on top, but the core search is pure string matching.

---

## Trade-Offs

| Benefit | Cost |
|---------|------|
| Zero infrastructure, sub-millisecond | No semantic understanding |
| One implementation across MCP, REST, RAG | Linear scan, no index |
| Handles typos, partial matches, token reordering | Fixed score threshold, not tunable |
| No external API calls or model dependencies | Cannot find conceptually related but differently named entities |
| Deterministic — same query always returns same results | No learning or personalization |

---

## Risks

1. **False positives for short names** -- `WRatio` can produce high scores for very short entity names that coincidentally match query substrings. Mitigated by the 50.0 threshold, but short names (2-3 characters) remain noisy
2. **Entity name dependency** -- Search quality depends entirely on entity names being descriptive. Cryptic names (codes, abbreviations, internal identifiers) produce poor search results. Mitigated by the coordinated template system generating descriptive names
3. **Scale ceiling** -- Linear scan breaks down at 100,000+ entities. Currently well within safe range, but the project has no index-based fallback

---

## Re-Evaluation Triggers

- Graph sizes exceeding 50,000 entities where linear scan latency becomes noticeable
- User reports of search failing to find conceptually related entities (semantic gap)
- Embedding models becoming lightweight enough (<100MB, sub-100ms inference) to justify as a dependency
- A requirement for similarity-based entity recommendation (not just name search)

---

## References

- `src/rag/search.py` -- `GraphSearch` with `search_by_name()`, `search_by_type()`, `search_by_attribute()`
- `src/mcp_server/tools.py` -- `search_entities` tool using fuzzy matching
- `src/serve/app.py` -- REST API search endpoint
- [rapidfuzz Documentation](https://rapidfuzz.github.io/RapidFuzz/) -- `WRatio` scorer reference
