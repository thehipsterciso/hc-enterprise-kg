# ADR-014: KARMA Multi-Agent Pipeline for Enrichment Orchestration

**Status:** Superseded — Moved to hc-enterprise-kg-enrich
**Date:** 2026-03-03
**Superseded:** 2026-03-10 (v0.32.0)
**Context:** Enrichment pipeline architecture refactor

> **NOTICE (v0.32.0):** The KARMA pipeline documented in this ADR has been removed from `hc-enterprise-kg` and relocated to [`hc-enterprise-kg-enrich`](https://github.com/thehipsterciso/hc-enterprise-kg-enrich). `hc-enterprise-kg-enrich` implements a 7-agent variant of this architecture (PrioritizationAgent, ContextAgent, SearchAgent, ReasoningAgent, ConfidenceAgent, CoherenceAgent, CommitAgent). The decisions below are preserved for historical reference.

---

## Summary

The enrichment orchestrator (v2) used a monolithic loop that combined entity iteration, context retrieval, enrichment execution, validation, and graph mutation into a single `_enrich_tier()` method. This ADR adopts the KARMA framework (Lu et al., NeurIPS 2025) to decompose enrichment into 9 specialized agents, each responsible for a single pipeline phase. The decomposition improves testability, enables concurrent processing, and provides formal inter-agent communication tracing.

---

## Problem Statement

The v2 EnrichmentOrchestrator handled all pipeline phases in a single method:

1. Entity loading and ordering (ingestion)
2. Graph context retrieval (reading)
3. Profile building (summarization)
4. Field enrichment (entity extraction)
5. Relationship suggestion (relationship extraction)
6. Pydantic validation (schema alignment)
7. Adversarial validation (evaluation)
8. Provenance recording (conflict resolution / provenance)
9. Graph mutation (application)

This monolith had three consequences: (a) individual phases could not be unit tested in isolation, (b) adding a new validation step required modifying the core loop, and (c) pipeline tracing was limited to log messages with no formal message protocol.

---

## Evaluation Criteria

1. **Agent isolation** — Each pipeline phase must be testable with mock inputs and outputs, without requiring a full knowledge graph.
2. **Backward compatibility** — The existing `EnrichmentOrchestrator.enrich_to_tier()` API must continue to work unchanged.
3. **Traceability** — Every inter-agent communication must be captured in a typed message with sender, recipient, correlation ID, and timestamp.
4. **Extensibility** — Adding a new pipeline phase (e.g., LLM-based enrichment) should require adding one agent class, not modifying the core loop.
5. **Performance** — Agent dispatch overhead must be < 10% of total pipeline time.

---

## Decision

Adopt the KARMA 9-agent pipeline architecture. Each agent inherits from `AbstractKarmaAgent` and communicates via typed `AgentMessage` objects. The `ControllerAgent` dispatches messages through the pipeline in sequence.

### Agent Mapping

| KARMA Agent | Role | Wraps |
|---|---|---|
| ControllerAgent | Pipeline orchestration | EnrichmentOrchestrator loop |
| IngestionAgent | Entity loading + batching | GENERATION_ORDER iteration |
| ReaderAgent | Graph context retrieval | GraphContextEngine |
| SummarizerAgent | Holistic profile building | HolisticEntityProfile |
| EntityExtractorAgent | Enricher dispatch | EnricherRegistry + 30 enrichers |
| RelExtractorAgent | Relationship processing | relationship_enricher |
| SchemaAlignerAgent | Pydantic validation | AdversarialValidator._validate_pydantic_field() |
| EvaluatorAgent | Quality contract evaluation | AdversarialValidator + GraphGuard (ADR-015) |
| ConflictResolverAgent | Multi-source merge + provenance | ProvenanceReconciler |

### Pipeline Selection

The `EnrichmentOrchestrator` accepts a `pipeline` parameter:
- `pipeline="legacy"` (default) — Uses the original monolithic loop.
- `pipeline="karma"` — Delegates to the KARMA ControllerAgent.

---

## Consequences

**Positive:**
- Each agent is independently unit-testable with mock messages.
- Pipeline tracing via AgentMessage provides full audit trail.
- New phases can be added by implementing one agent class.
- Existing enricher code (30 enrichers, templates, OSINT) is unchanged.

**Negative:**
- Additional abstraction layer adds ~5% dispatch overhead.
- Message passing requires serializable payloads (currently using direct object references).
- Two code paths (legacy + KARMA) must be maintained during transition.

---

## Risks

- **Performance regression** — Agent dispatch overhead could accumulate for large graphs. Mitigated by profiling during integration testing.
- **Message protocol drift** — Adding new message types without updating all agents. Mitigated by the MessageType enum.

---

## Re-Evaluation Triggers

- If the legacy pipeline is fully deprecated and removed.
- If async/concurrent agent execution is needed (current pipeline is synchronous).
- If LLM-based agents are added that require different communication patterns.

---

## References

- Lu et al., "KARMA: Augmenting Embodied AI Agents with Long-and-Short Term Memory for Multi-Agent Knowledge Graph Enrichment", NeurIPS 2025
- `src/enrichment/karma/` — Implementation
- ADR-013 — Original enrichment agency design
- ADR-015 — GraphGuard quality contracts (companion ADR)
