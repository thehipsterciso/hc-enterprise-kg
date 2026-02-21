# ADR-010: Compact Entity Serialization for LLM Context Windows

**Status:** Accepted
**Date:** 2026-02-21
**Context:** Response formatting for MCP and REST API consumers

---

## Summary

MCP and REST API responses use a `compact_entity()` function that strips `None`, empty strings, empty lists, and internal temporal/metadata fields from entity dicts before returning them. This reduces response size for LLM context window efficiency. The same approach is applied to relationships via `compact_relationship()`.

This is a lossy serialization — information is deliberately discarded to optimize for the primary consumer (language models with token budgets).

---

## Decision

Strip empty values and internal fields from all API responses. Optimize for LLM token efficiency over information completeness.

---

## What Gets Stripped

**Null/empty fields:**
- `None` values
- Empty strings (`""`)
- Empty lists (`[]`)
- Empty dicts (`{}`) (relationships only)

**Internal temporal fields:**
- `created_at`
- `updated_at`
- `valid_from`
- `valid_until`
- `version`

**Internal metadata:**
- `metadata` dict (which may contain `_confidence`, `_source` from auto-extraction)

---

## Alternatives Considered

| Alternative | Assessment |
|-------------|------------|
| **Full `model_dump()` output** | Return every field on every entity, including nulls, empty lists, and timestamps. For a System entity with 40+ fields, roughly half are None or empty. Full output doubles token cost for zero analytical value. LLMs process tokens linearly — padding with empty fields reduces the useful-content-to-context-window ratio |
| **Custom DTOs per entity type** | Type-specific response schemas for each of the 30 entity types. Maximum control over what each type returns. 30 DTO classes to maintain in parallel with 30 entity classes. Schema drift between entities and DTOs is guaranteed |
| **GraphQL-style field selection** | Caller specifies which fields to return. Maximum flexibility, no wasted tokens. Requires a query language, schema introspection, and field-level access control. Overengineered for the current consumer set (Claude Desktop, REST clients) |
| **Binary/protobuf serialization** | Minimal wire size, type-safe deserialization. LLMs consume text, not binary. MCP protocol is JSON-based. Binary is not an option for the primary consumer |

---

## Rationale

1. **Token efficiency** -- A raw `model_dump()` of a System entity is ~2,000 characters. After compact serialization, it is ~800 characters. For a `list_entities` call returning 50 systems, that is 60,000 characters saved — roughly 15,000 tokens
2. **Signal-to-noise ratio** -- LLMs perform better when context contains relevant information, not padding. `created_at: "2026-02-21T14:30:00Z"` on every entity adds nothing to analytical queries like "which systems have critical vulnerabilities"
3. **Uniform application** -- One `compact_entity()` function handles all 30 entity types. One `compact_relationship()` handles all relationship types. No per-type logic required

---

## Where This Diverges from Best Practice

### Information Loss Is Deliberate

This is a lossy serialization. The `metadata` dict may contain provenance information (`_confidence`, `_source`) from the auto-KG pipeline. Stripping it means API consumers cannot see where auto-extracted entities came from or how confident the extraction was.

Temporal fields (`created_at`, `version`) carry audit trail information. Stripping them means consumers cannot track when entities were created or how many times they have been modified.

This is a conscious trade-off: the primary consumer (Claude Desktop via MCP) does not need provenance or temporal data for scenario analysis. If a consumer needs full fidelity, they should use the JSON export directly, not the API.

### No Opt-In for Full Detail

There is no `compact=false` parameter. Every API response is always compact. A consumer that needs temporal metadata, provenance information, or the `metadata` dict has no way to request it through the API.

This is a simplicity trade-off. Adding a verbosity parameter means testing two output paths, documenting two modes, and handling edge cases where one consumer expects compact and another expects full. The JSON export file contains full-fidelity data for consumers that need it.

### Duplicated Implementation

`compact_entity()` exists in both `mcp_server/helpers.py` and `serve/app.py` with identical logic but separate implementations. A change to the skip list must be made in both places. This is a known DRY violation.

---

## Trade-Offs

| Benefit | Cost |
|---------|------|
| ~60% reduction in response size | Provenance and temporal information lost |
| Better LLM analytical performance | No opt-in for full detail |
| Single function handles all 30 entity types | Duplicated across MCP and REST modules |
| Cleaner output for human readers too | Consumers cannot distinguish "field is empty" from "field was stripped" |

---

## Risks

1. **Lost provenance** -- Auto-extracted entities lose their `_confidence` and `_source` metadata. If an LLM-based consumer needs to reason about extraction confidence, this information is unavailable through the API
2. **Duplication drift** -- The two `compact_entity()` implementations may diverge over time. Mitigated by extracting to a shared utility (currently not done)
3. **Assumption about consumers** -- The optimization assumes LLMs are the primary consumer. If the REST API gains non-LLM consumers (dashboards, integrations), the stripped fields may be needed

---

## Re-Evaluation Triggers

- A consumer needs temporal or provenance data through the API (not via JSON export)
- The duplication between MCP and REST causes a bug (different skip lists)
- Response size optimization becomes less critical (larger context windows, cheaper tokens)
- Non-LLM consumers of the REST API need full-fidelity responses

---

## References

- `src/mcp_server/helpers.py` -- `compact_entity()`, `compact_relationship()`
- `src/serve/app.py` -- `_compact_entity()`, `_compact_relationship()` (duplicate)
- `src/export/json_export.py` -- Full-fidelity export (no stripping)
