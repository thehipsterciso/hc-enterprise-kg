# ADR-008: Relationship Weaving as Post-Generation Phase

**Status:** Accepted
**Date:** 2026-02-21
**Context:** Relationship creation strategy in the synthetic pipeline

---

## Summary

Relationships are created in a separate `RelationshipWeaver` phase after all 30 entity types have been generated, not inline during entity generation. The weaver contains 33 methods producing 52 relationship types with contextual weight, confidence scores, and typed properties. Mirror fields on entities are populated from woven relationships as a final step.

---

## Decision

Separate relationship creation from entity generation. All relationships are woven in a single phase after all entities exist.

---

## The Two-Phase Architecture

```
Phase 1: Entity Generation (sequential, 30 types in GENERATION_ORDER)
    → Each generator produces entities for one type
    → Entities are added to the KnowledgeGraph via add_entities_bulk()
    → GenerationContext accumulates all entities for cross-type access

Phase 2: Relationship Weaving (single pass, 33 methods)
    → RelationshipWeaver.weave_all() runs after all entities exist
    → 33 weaver methods produce relationships across all type pairs
    → _make_rel() enforces consistent metadata on every relationship
    → _populate_mirror_fields() denormalizes key relationships onto entities
    → All relationships added via add_relationships_bulk()
```

---

## Alternatives Considered

| Alternative | Assessment |
|-------------|------------|
| **Generators create their own relationships** | Each generator emits entities AND relationships. PersonGenerator creates `WORKS_IN` relationships when creating people. Rejected because cross-layer relationships (Control → Regulation, Initiative → System) would require generators to reach into other generators' output, creating tight coupling. The 33 weaver methods would fragment across 30 generator files |
| **Declarative relationship rules** | Relationships auto-generated from type-matching rules ("every Person gets a WORKS_IN to a Department"). Too rigid for the contextual logic needed (headcount-proportional assignment, severity-based weights, type-filtered hosting) |
| **Interleaved generation** | Generate Layer 1 entities, then Layer 1 relationships, then Layer 2 entities, then Layer 2 relationships. Avoids holding all entities in memory simultaneously. But cross-layer relationships (L11 Initiative → L02 System) would require backfilling, making this effectively a multi-pass approach with more complexity |
| **Two-pass entity generation** | First pass creates all entities without references. Second pass populates cross-references on entities. Does not address relationships — only entity-to-entity field references. Still needs a relationship phase |

---

## What the Weaver Provides

### Contextual Relationship Metadata

Every relationship carries `weight`, `confidence`, and `properties` — not just source/target/type:

- **`_make_rel()`** enforces `round(weight, 2)` and `round(confidence, 2)` on every relationship
- **`SEVERITY_WEIGHT`** maps severity levels to edge weights: low=0.3, medium=0.5, high=0.8, critical=1.0
- **Confidence values** are semantically grounded: 0.95 for organizational facts (person works in department), 0.70 for uncertain attribution (threat actor exploits vulnerability)
- **Properties** carry typed context: `dependency_type` (runtime/build/data/authentication/monitoring), `exploit_maturity` (weaponized/proof_of_concept/theoretical), `supply_type` (license/service/hardware/subscription/support)

### Domain Logic in the Weaver Methods

The 33 methods encode organizational structure logic:

- **`_assign_people_to_departments()`** -- Distributes people proportionally based on department headcount fractions. Not random — a department with 30% headcount fraction gets ~30% of people
- **`_create_management_chains()`** -- Creates `MANAGES` and `REPORTS_TO` relationships reflecting organizational hierarchy
- **`_assign_systems_hosting()`** -- Infrastructure systems `HOSTS` application systems. Type-filtered: only infrastructure can host
- **`_link_controls_to_regulations()`** -- Controls `IMPLEMENTS` regulations with enforcement metadata
- **`_link_risks_to_controls()`** -- Controls `MITIGATES` risks with effectiveness metadata

### Mirror Field Denormalization

`_populate_mirror_fields()` runs after all relationships are woven and sets convenience fields on entities:

- `Person.holds_roles` -- List of role IDs from `HAS_ROLE` relationships
- `Role.filled_by_persons` -- List of person IDs (inverse)
- `Role.headcount_filled` -- Count of people holding this role
- `Person.located_at` -- Location ID from `LOCATED_AT` relationship
- `Person.participates_in_initiatives` -- Initiative IDs from `MEMBER_OF` relationships

These mirror fields enable O(1) access to common traversals in exported JSON without requiring the graph engine.

---

## Where This Diverges from Best Practice

### All-or-Nothing Weaving

`weave_all()` creates every relationship type in one call. There is no way to weave a subset of relationship types or re-weave a single type after modification. If you want to regenerate only vendor relationships, you must re-run the entire weaver.

### No Relationship Validation During Weaving

The `RELATIONSHIP_SCHEMA` dict in `src/domain/relationship_schema.py` defines valid source/target types for each relationship type. The weaver does not call `validate_relationship()` during generation. It relies on each weaver method being correctly implemented. Validation is available for external consumers but is not enforced internally.

This is a deliberate trade-off: the weaver methods are tested, and adding validation on every relationship creation would slow generation. But it means a bug in a weaver method can produce relationships that violate the schema without detection at generation time.

### Mirror Fields via `extra="allow"`

Mirror fields like `Person.holds_roles` are not declared on the `Person` model. They land in `__pydantic_extra__` via the `extra="allow"` config (ADR-002). This means they are not type-checked, not documented in the schema, and discoverable only by reading the weaver code or the exported JSON.

### In-Place Entity Mutation

`_populate_mirror_fields()` modifies entity objects that already exist in the knowledge graph by setting attributes directly. This is a side effect that happens after `add_entities_bulk()` has already stored the entities. The mirror fields exist on the Python objects in the `GenerationContext` and in the exported JSON, but not necessarily on the entity as stored in the engine (which stores a snapshot at `add_entity()` time).

---

## Trade-Offs

| Benefit | Cost |
|---------|------|
| All entities available when weaving — no ordering constraints within relationships | Must hold all entities in memory simultaneously |
| 33 methods centralized in one file — auditable relationship topology | Adding a new entity type may require modifying multiple weaver methods |
| Consistent metadata via `_make_rel()` | No schema validation during weaving |
| Mirror fields for O(1) access in exported JSON | Mirror fields are undeclared extras, not schema-enforced |
| Proportional, type-filtered, context-aware relationship logic | All-or-nothing weaving, no incremental updates |

---

## Risks

1. **Weaver method bugs** -- A method creating `DEPENDS_ON` between two wrong entity types would produce invalid relationships undetected. Mitigated by integration tests that validate relationship type distributions
2. **Mirror field staleness** -- If relationships are modified after `_populate_mirror_fields()` runs, mirror fields become stale. Currently not an issue because the pipeline is generate-once, but would be a problem in a mutable graph
3. **Memory footprint** -- All entities from all 30 types are held in `GenerationContext` during weaving. At 20k employees this is tens of megabytes — acceptable but worth monitoring

---

## Re-Evaluation Triggers

- Need for incremental relationship re-weaving (modify vendors without re-weaving everything)
- Mirror field inconsistencies discovered in exported graphs
- Weaver method count exceeding 50, suggesting the single-file approach needs decomposition
- A mutable graph use case where mirror fields must stay synchronized with relationship changes

---

## References

- `src/synthetic/relationships.py` -- `RelationshipWeaver` with 33 methods, `_make_rel()`, `_populate_mirror_fields()`
- `src/synthetic/orchestrator.py` -- Two-phase pipeline: `generate()` then `weave_all()`
- `src/domain/relationship_schema.py` -- `RELATIONSHIP_SCHEMA` (not enforced during weaving)
- `docs/adr/005-layered-generation-order.md` -- Related: why entity generation is ordered
