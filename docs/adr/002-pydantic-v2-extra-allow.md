# ADR-002: Pydantic v2 with `extra="allow"` for Entity Models

**Status:** Accepted
**Date:** 2026-02-21
**Context:** Entity model framework and validation strategy

---

## Summary

All 30 entity types extend `BaseEntity`, a Pydantic v2 `BaseModel` with `model_config = ConfigDict(extra="allow")`. This decision prioritizes forward compatibility and schema flexibility over strict validation. It is the single most consequential design choice in the project and the most common source of bugs.

---

## Decision

Use Pydantic v2 as the entity model framework with `extra="allow"` on the base class.

---

## Context

An enterprise knowledge graph with 30 entity types, 52 relationship types, and hundreds of fields needs a model layer that provides runtime validation, JSON serialization, type safety, and IDE support. The ontology grew from 12 types (v0.1) to 30 types over 20+ releases, and will continue to evolve.

---

## Alternatives Considered

| Alternative | Assessment |
|-------------|------------|
| **Pydantic v2 with `extra="forbid"`** | Strict validation catches typos at construction. Rejected because serialized graphs from older versions fail to load when new fields are added, and mirror fields (`Person.holds_roles`) set by the relationship weaver would require schema changes for every new denormalized field |
| **Pydantic v2 with `extra="ignore"`** | Silently drops unknown fields. Loses data on round-trip, which is worse than storing it in extras |
| **Python dataclasses** | Lighter weight, stdlib. No built-in JSON serialization, no runtime validation beyond type hints, no `model_dump(mode="json")` for export |
| **attrs** | Strong validation via converters, fast. No native JSON serialization, less IDE support than Pydantic, smaller ecosystem |
| **Marshmallow** | Mature serialization library. Separate schema classes from data classes creates duplication. No runtime validation on the data objects themselves |

---

## Rationale

Pydantic v2 provides the best combination of capabilities for this use case:

1. **Runtime validation** -- Field types are enforced at construction. A `System` with `criticality="high"` validates; `criticality=42` fails. This catches a class of bugs that dataclasses miss entirely
2. **JSON serialization** -- `model_dump(mode="json")` produces export-ready dicts. `model_validate()` reconstructs from JSON. The export/ingest pipeline is three lines of code
3. **IDE support** -- Full autocomplete, type checking, and inline documentation for all 30 entity classes. This matters for a 200+ field ontology
4. **`TemporalMixin`** -- `BaseEntity` inherits `created_at`, `updated_at`, `valid_from`, `valid_until`, `version` from `TemporalMixin` via Pydantic's model inheritance. Every entity gets temporal tracking for free

The `extra="allow"` choice specifically enables:

- **Forward compatibility** -- Older graph.json files load in newer code. Newer files with unknown fields load in older code. Neither case raises `ValidationError`
- **Mirror field injection** -- The relationship weaver's `_populate_mirror_fields()` sets fields like `Person.holds_roles` and `Role.filled_by_persons` post-construction. With `extra="forbid"`, every mirror field would need a schema declaration
- **Metadata passthrough** -- The auto-KG pipeline attaches `_confidence` and `_source` keys via the metadata dict pattern. Third-party consumers can attach arbitrary metadata without forking the model

---

## Where This Diverges from Best Practice

The conventional recommendation is `extra="forbid"` for domain models. The Pydantic documentation recommends it. Most Pydantic guides recommend it. We chose differently, and the cost is real.

### The Silent Failure Problem

With `extra="allow"`, a misspelled field name does not raise an error. It lands in `__pydantic_extra__` as if nothing happened:

```python
# This silently succeeds. 'descritpion' goes to extras.
System(entity_type="system", name="Jenkins", descritpion="CI server")
```

This is the single most common bug pattern in the project. Generator authors write `descritpion` instead of `description`, the entity validates, the tests pass, and the field is missing in the output. The bug is invisible until someone reads the exported JSON carefully.

### Mitigations Built to Compensate

The project maintains a validation module (`src/domain/validation.py`) specifically to address this:

- **`check_extra_fields(entity)`** -- Returns any keys in `__pydantic_extra__`. A non-empty result is almost always a bug
- **`warn_extra_fields(entity)`** -- Logs a warning. In strict mode (`HCKG_STRICT=1`), raises `ValueError`
- **`validate_entity_strict(entity)`** -- Full strict validation check suite

These exist because `extra="allow"` creates a problem that needs compensating controls. With `extra="forbid"`, none of this code would be necessary.

---

## Trade-Offs

| Benefit | Cost |
|---------|------|
| Forward/backward graph compatibility | Misspelled fields silently succeed |
| Mirror field injection without schema changes | Entities can accumulate undiscovered garbage fields |
| Metadata passthrough for third-party consumers | Required building a separate validation module |
| Simpler ontology evolution (add fields without breaking old graphs) | Generator authors must be more careful with field names |

---

## Risks

1. **Silent data corruption** -- Misspelled fields produce entities that look correct but are missing data. Mitigated by `HCKG_STRICT=1` in CI and quality scoring checks
2. **Schema drift** -- Over time, extras accumulate. No enforcement that extras are intentional vs. accidental. Mitigated by `check_extra_fields()` in tests
3. **Type safety erosion** -- Extras bypass Pydantic's type system entirely. A datetime in an extra field is a string. An int is an int. No validation

---

## Re-Evaluation Triggers

- If the ontology stabilizes at 30 types with no new additions for 3+ releases, `extra="forbid"` becomes more attractive (less forward-compatibility pressure)
- If a bug audit shows that extra-field typos account for a significant fraction of defects, the cost/benefit balance may have shifted
- If Pydantic adds a mode like `extra="warn"` that allows extras but logs them, that would be the ideal middle ground

---

## References

- `src/domain/base.py` -- `BaseEntity` with `model_config = ConfigDict(extra="allow")`
- `src/domain/validation.py` -- Compensating validation controls
- [Pydantic v2 Model Config](https://docs.pydantic.dev/latest/api/config/) -- `extra` field documentation
