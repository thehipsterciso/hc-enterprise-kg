# ADR-005: Layered Generation Order for Referential Integrity

**Status:** Accepted
**Date:** 2026-02-21
**Context:** Synthetic data generation pipeline ordering strategy

---

## Summary

Synthetic entities are generated in a hardcoded 12-layer dependency order defined by the `GENERATION_ORDER` list in the orchestrator. Each layer can reference entities from previous layers. Relationships are woven in a separate phase after all entities exist. This is a sequential, topological build — not parallel, not declarative, not two-pass.

---

## Decision

Generate entities in a fixed, explicit dependency order. Wire relationships after all entities exist.

---

## The Ordering

```
L00  Foundation    → Location
L04  Organization  → Department, Role
L05  People        → Person
L02  Technology    → Network, System
L03  Data          → DataAsset
L01  Compliance    → Policy, Vulnerability, ThreatActor, Incident
L01  Governance    → Regulation, Control, Risk, Threat
L02  Technology    → Integration
L03  Data          → DataDomain, DataFlow
L04  Organization  → OrganizationalUnit
L06  Capabilities  → BusinessCapability
L07  Locations     → Site, Geography, Jurisdiction
L08  Products      → ProductPortfolio, Product
L09  Customers     → MarketSegment, Customer
L10  Vendors       → Contract
L11  Initiatives   → Initiative
```

The orchestrator iterates this list sequentially. Each generator receives a `GenerationContext` containing all previously generated entities.

---

## Alternatives Considered

| Alternative | Assessment |
|-------------|------------|
| **Topological sort at runtime** | Generators declare dependencies explicitly; a DAG sort computes the order. More flexible but adds complexity. The dependency graph between 30 types is stable — it has not changed in 15+ releases. Runtime sorting solves a problem that does not exist |
| **Two-pass generation** | First pass creates all entities without references. Second pass populates cross-references. Avoids ordering entirely but means entities are incomplete after the first pass and generators cannot use inter-entity context during creation |
| **No ordering (parallel generation)** | Generate all types concurrently, resolve dangling references after. Requires post-hoc validation and repair. Fragile for a domain where a Person's department assignment affects their data sensitivity, which affects the systems they access |
| **Graph-of-generators with explicit dependency edges** | Each generator registers which entity types it requires. A framework resolves and schedules execution. Framework overhead for a linear pipeline. The current `GENERATION_ORDER` list is 42 lines and immediately readable |

---

## Rationale

1. **Referential integrity by construction** -- L05 People generators reference L04 Department entities that already exist. L10 Contract generators reference L10 Vendor entities. No dangling references, no post-hoc repair
2. **Context accumulation** -- `GenerationContext.get_entities(EntityType.DEPARTMENT)` returns all departments when the Person generator runs. The generator uses department headcount fractions to distribute people proportionally. This cross-entity reasoning is only possible because departments exist first
3. **Explicit and auditable** -- Anyone reading `GENERATION_ORDER` sees the full dependency chain in 42 lines. No framework magic, no implicit resolution, no debugging "why did this type generate before that type"
4. **Relationship weaving as final phase** -- `RelationshipWeaver.weave_all()` runs after all 30 entity types exist. The 33 weaver methods can reference any entity type without ordering constraints

---

## Where This Diverges from Best Practice

### No Parallelism

Types within the same layer (e.g., Site, Geography, Jurisdiction are all L07) could theoretically generate in parallel. The orchestrator does not exploit this. Generation is purely sequential.

At the current scale (100-20,000 employees), the total generation time is 0.3-8.0 seconds. Parallelism would add threading complexity for marginal speedup. If generation time becomes a bottleneck at larger scales, layer-internal parallelism is the first optimization to consider.

### Hardcoded, Not Declarative

The ordering is a Python list, not a configuration file or a declarative dependency graph. Adding a new entity type requires editing `GENERATION_ORDER` in the orchestrator module and placing it in the correct position. There is no validation that the ordering is topologically correct — the correctness depends on the developer placing it correctly.

This is a deliberate trade-off. The ordering has been stable across 20+ releases. The overhead of a declarative dependency framework is not justified by a list that changes once or twice per minor version.

---

## Trade-Offs

| Benefit | Cost |
|---------|------|
| Referential integrity guaranteed by construction | No parallelism in generation |
| Cross-entity reasoning available in generators | New types require careful placement in the ordering |
| Immediately readable ordering (42 lines) | No runtime validation of ordering correctness |
| Relationship weaving has full entity access | Sequential execution is slower than theoretical parallel |

---

## Risks

1. **Ordering errors** -- A new entity type placed too early in the list may reference types that do not yet exist. Mitigated by integration tests that run the full pipeline and validate entity/relationship counts
2. **Circular dependencies** -- The current ontology has no circular dependencies between generation layers. If the ontology evolves to require them (e.g., type A references type B and type B references type A), the linear ordering model breaks. Would require a two-pass approach for those specific types

---

## Re-Evaluation Triggers

- Generation time exceeding 30 seconds at target scales (20k employees)
- Circular dependency between entity types in the ontology
- Frequent reordering of `GENERATION_ORDER` indicating the static list is a maintenance burden
- A contributor proposes a declarative dependency framework with clear benefits over the current approach

---

## References

- `src/synthetic/orchestrator.py` -- `GENERATION_ORDER` list and `SyntheticOrchestrator.generate()`
- `src/synthetic/base.py` -- `GenerationContext` with `get_entities()` for cross-type access
- `src/synthetic/relationships.py` -- `RelationshipWeaver.weave_all()` (post-generation phase)
