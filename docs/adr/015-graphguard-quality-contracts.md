# ADR-015: GraphGuard Quality Contract Framework for Enrichment Validation

**Status:** Accepted
**Date:** 2026-03-03
**Context:** Enrichment data quality validation architecture

---

## Summary

The v2 enrichment pipeline used a monolithic `AdversarialValidator` class (~300 LOC) that combined four validation gates into a single `validate()` method. This ADR decomposes the validator into 5 formal QualityContracts and 3 Guardian agents following the GraphGuard pattern (Fraunhofer IAIS, 2023). Each contract is declarative, independently testable, and produces queryable audit reports.

---

## Problem Statement

The AdversarialValidator was effective but had structural limitations:

1. **Monolithic validate()** — All four validation gates (Pydantic validation, plausibility bounds, confidence rubric enforcement, source staleness) were baked into one method. Adding a new validation criterion required modifying the core class.
2. **No audit trail** — Validation results were returned as a flat list of `ValidationFailure` objects with no structured querying (e.g., "show me all plausibility violations for vendors").
3. **No configurability** — All contracts ran at the same severity. There was no way to run plausibility as ERROR (blocking) but staleness as WARNING (informational) without modifying the class.
4. **No graph-level validation** — The validator operated per-entity. Cross-entity coherence ran as a separate phase with a different interface.

---

## Evaluation Criteria

1. **Declarative** — Each quality rule must be expressed as a self-contained contract with a unique ID, severity, and evaluate() method.
2. **Composable** — Contracts must be assembled into Guardians that run at specific pipeline checkpoints.
3. **Queryable** — Validation results must be structured in a QualityValidationReport that supports filtering by entity, contract, severity, and field.
4. **Backward compatible** — The `AdversarialValidator` class must remain importable and functional for existing tests.
5. **Independent** — Each contract must be unit-testable without the others.

---

## Decision

Decompose the AdversarialValidator into the GraphGuard three-layer architecture:

### Layer 1: QualityContracts (5 contracts)

| Contract ID | Contract | Extracted From | Severity |
|---|---|---|---|
| GG-PLAUS-001 | PlausibilityContract | `_check_plausibility()` | ERROR |
| GG-STALE-001 | StalenessContract | `_downgrade_for_staleness()` | WARNING |
| GG-CONF-001 | ConfidenceRubricContract | `_enforce_confidence_rubric()` | WARNING |
| GG-COHER-001 | CoherenceContract | `coherence_rules.py` | WARNING |
| GG-COMPL-001 | CompletenessContract | `quality.py` | WARNING |

### Layer 2: Guardians (3 guardians)

| Guardian | Phase | Contracts |
|---|---|---|
| PreEnrichmentGuardian | Before enricher.enrich() | (Tier eligibility — future) |
| PostEnrichmentGuardian | After enricher, before graph update | Plausibility, Staleness, ConfidenceRubric |
| CoherenceGuardian | After full enrichment pass | Coherence |

### Layer 3: QualityValidationReport

Structured audit record with queryable methods:
- `get_violations_for_entity(entity_id)`
- `get_violations_by_contract(contract_id)`
- `get_violations_by_severity(severity)`
- `pass_rate()`
- `entity_ids_with_violations()`

### Integration

The `EvaluatorAgent` (KARMA pipeline, ADR-014) instantiates the `PostEnrichmentGuardian` and runs its contracts on each enrichment result. The existing `AdversarialValidator` remains as a backward-compatible facade.

---

## Consequences

**Positive:**
- Each contract is independently testable (~20 LOC per contract test).
- New validation rules require one contract class, not monolith modification.
- QualityValidationReport enables structured quality analytics.
- Severity is configurable per contract (ERROR blocks, WARNING logs).
- Coherence validation shares the same contract interface as per-entity validation.

**Negative:**
- More files to maintain (5 contracts + guardian + reports vs 1 validator).
- Indirect validation path (Guardian → Contract → Report) vs direct validate().
- Two validation paths during transition (AdversarialValidator + GraphGuard).

---

## Risks

- **Contract proliferation** — Adding too many fine-grained contracts could make the validation pipeline slow. Mitigated by bundling related checks into single contracts.
- **Report size** — QualityValidationReport could grow large for graphs with thousands of entities. Mitigated by the head_limit on violation storage.

---

## Re-Evaluation Triggers

- When DAMA-DMBOK data quality dimensions are integrated platform-wide.
- When real-time streaming enrichment requires async contract evaluation.
- When the AdversarialValidator facade is fully deprecated.

---

## References

- Fraunhofer IAIS, "GraphGuard: A Quality Contract Framework for Knowledge Graphs", 2023
- `src/enrichment/guard/` — Implementation
- ADR-013 — Original enrichment agency design
- ADR-014 — KARMA agent pipeline (companion ADR)
