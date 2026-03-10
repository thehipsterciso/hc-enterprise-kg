# ADR-013: Intelligence-Driven Knowledge Graph Enrichment Agency

**Status:** Superseded — Moved to hc-enterprise-kg-enrich
**Date:** 2026-03-03
**Superseded:** 2026-03-10 (v0.32.0)
**Context:** Enterprise knowledge graph entity enrichment and data maturity

> **NOTICE (v0.32.0):** The enrichment module documented in this ADR has been removed from `hc-enterprise-kg` and relocated to [`hc-enterprise-kg-enrich`](https://github.com/thehipsterciso/hc-enterprise-kg-enrich). The `hckg enrich` command now redirects to that package. The architecture decisions below are preserved for historical reference; the canonical implementation lives in `hc-enterprise-kg-enrich`.

---

## Summary

The hc-enterprise-kg schema defines 30 entity types with extremely rich Pydantic models (Person ~65 fields, System ~119, Vendor ~95, OrgUnit ~100, Initiative ~95), but synthetic generators populate only 10-15% of available fields. An Enrichment Agency — a coordinated group of context-aware agents — progressively deepens entity attributes and relationship metadata across five maturity tiers aligned to CMMI/DCAM standards. This document records the decision to implement enrichment as a post-generation phase, driven by graph context and OSINT intelligence, with provenance and confidence as first-class concerns.

---

## Problem Statement

Current generators produce structurally valid but sparsely populated entities. Temporal fields, assessment histories, financial profiles, framework mappings, skills inventories, performance scorecards, and provenance metadata are all structurally defined in Pydantic models but left empty after generation. This gap prevents meaningful scenario analysis, risk modeling, data maturity assessment, and graph-driven intelligence workflows.

The enrichment problem has three dimensions:

1. **Isolation** -- Generators operate per-entity-type. A PersonGenerator knows nothing about the person's Role, Department, Systems, Risks, Controls, or Location. Field-filling is siloed and incoherent
2. **Grounding** -- Synthetic values lack semantic grounding in real-world frameworks. Controls reference invented IDs; threats do not map to MITRE ATT&CK; compliance mappings are hand-waved
3. **Provenance** -- When fields are enriched, there is no record of data source, methodology, confidence, or known gaps. Graph consumers cannot assess data quality or understand what they are looking at

---

## Evaluation Criteria

An enrichment system must satisfy six properties:

1. **Context-aware** -- Every enricher receives the entity's full neighborhood (Person → Role, Department, Systems, Risks, Controls, Locations, Jurisdictions; System → Vendors, Networks, DataAssets, Controls, Threats)
2. **Non-breaking** -- Enrichment is additive. Existing generators remain unchanged. A graph enriched to Tier 3 has all Tier 1 fields intact
3. **OSINT-grounded** -- Framework mappings, threat IDs, and control IDs reference real-world standards (NIST SP 800-53, ISO 27001, CIS Controls v8, MITRE ATT&CK). No invented identifiers
4. **Provenance-aware** -- Every enrichment updates ProvenanceAndConfidence, recording source, methodology, confidence, and gaps
5. **Maturity-tiered** -- Enrichment advances through CMMI/DCAM-aligned tiers, allowing clients to choose desired data fidelity
6. **Profile-aware** -- Tech, Financial, and Healthcare profiles customize which fields are populated and what OSINT sources are consulted

---

## Libraries and Approaches Evaluated

### Monolithic LLM Enrichment (Rejected)

**Approach:** Use Claude or GPT-4 to enrich all fields at once via prompt engineering.

**Why rejected:**
- Non-deterministic with seed control
- Expensive at scale (100k+ entities)
- Difficult to reproduce in testing
- Hard to validate framework mappings against canonical sources
- Does not meet "grounding" criterion for critical fields
- Confidence cascading undefined

**Reconsideration trigger:** If LLM costs drop below $0.0001 per entity and streaming inference is available, revisit for Tier 4-5

### Single-Pass Enrichment (Rejected)

**Approach:** One enrichment pass fills all empty fields per entity type.

**Why rejected:**
- No progressive maturity model
- All-or-nothing approach
- Difficult to control data quality by tier
- No ability to "enrich to Tier 2" for cost optimization
- Cross-entity coherence validation must run at end anyway

### Enrichment Embedded in Generators (Rejected)

**Approach:** Generators produce rich output directly.

**Why rejected:**
- Violates separation of concerns
- Generators become complex and hard to maintain
- Breaks unit testability (generator tests would require full graph context)
- No way to adjust enrichment level independently of generation
- Makes profile customization harder

### Coordinated Agent-Based Enrichment (Selected)

**Approach:** 30 dedicated enrichers, one per entity type, operating on EntityContext (neighborhood via GraphContextEngine), driven by OSINT intelligence and coordinated through EnricherRegistry.

**Why selected:**
- Agents operate in context, not isolation
- Clear separation: generation → enrichment
- Testable per-agent
- Profile customization via enricher registry
- Maturity tiers are implementable as enricher composition
- Provenance tracking is natural (agents record their source and confidence)

---

## Decision

**Implement an Enrichment Agency as a post-generation phase, driven by context-aware agents, OSINT-grounded intelligence, and provenance-aware field mutation.**

### Architecture

**1. GraphContextEngine**

Computes an EntityContext for any entity. Given a Person with ID P:

```python
class EntityContext:
    entity: Entity
    neighbors_by_type: dict[EntityType, list[Entity]]  # Role, Department, Systems, etc.
    incoming_relationships: list[Relationship]
    outgoing_relationships: list[Relationship]
    paths_to_critical_assets: list[Path]  # Optional, for risk analysis
```

Used by enrichers to make context-aware decisions. No agent queries the graph directly; all access is through EntityContext.

**2. EnricherRegistry**

Parallel to GeneratorRegistry. Each of 30 entity types has one registered enricher:

```python
class BaseEnricher(ABC):
    entity_type: EntityType
    min_confidence: float = 0.8

    def enrich(self, entity: Entity, context: EntityContext) -> Entity:
        """Mutate entity in-place, update provenance, return mutated entity."""
        pass

class PersonEnricher(BaseEnricher):
    entity_type = EntityType.PERSON

    def enrich(self, person: Person, context: EntityContext) -> Person:
        # Access person.role, person.department, systems assigned, risks, etc.
        # from context.neighbors_by_type
        # Populate skills, certifications, performance scores, temporal fields
        # Update person.provenance_and_confidence
        pass
```

All enrichers registered in a module-level registry:

```python
ENRICHER_REGISTRY = EnricherRegistry()
ENRICHER_REGISTRY.register(PersonEnricher)
ENRICHER_REGISTRY.register(SystemEnricher)
# ... 28 more
```

**3. OSINTResearchAgent**

Provides real-world framework reference data:

```python
class OSINTResearchAgent:
    # Built-in canonical sources
    nist_sp_800_53 = {
        "AC-2": {"title": "Account Management", "family": "Access Control"},
        # ... 800+ controls
    }

    iso_27001 = {
        "A.5.1": {"title": "Policies for IS", "domain": "Organization"},
        # ... 100+ controls
    }

    cis_controls_v8 = { ... }  # 18 controls, mapped

    mitre_attack = {
        "T1021": {"name": "Remote Service Session Initiation", "tactics": ["lateral-movement"]},
        # ... 200+ techniques
    }

    def resolve_control(self, framework: str, control_id: str) -> ControlDefinition:
        """Return canonical control metadata."""
        pass

    def resolve_threat(self, threat_name: str) -> ThreatDefinition:
        """Map threat name to MITRE ATT&CK technique."""
        pass

    def search_external(self, query: str) -> list[SearchResult]:
        """Optional external search (web, CVE databases, etc.)."""
        # Behind a feature flag; default off
        pass
```

**4. Five-Tier Maturity Model**

Aligned to CMMI capability levels and DCAM data maturity:

| Tier | Name | Coverage | Focus | Cost | Example |
|------|------|----------|-------|------|---------|
| 1 | Initial | ~15% | Generator output as-is | Low | Synthetic graph ready to use |
| 2 | Managed | ~35% | Operational fields (statuses, owner links, basic temporal) | Low | Personnel profiles, system statuses |
| 3 | Defined | ~60% | Cross-entity coherence, framework mappings, skill-role alignment | Medium | Controls mapped to NIST, risks mapped to MITRE ATT&CK |
| 4 | Measured | ~80% | Quantitative metrics, performance data, cost allocation, effectiveness scores | Medium-High | System costs, control effectiveness, risk scores |
| 5 | Optimized | ~95% | Full fidelity, scenario analysis data, predictive fields, comprehensive provenance | High | Historical trends, prediction vectors for ML |

Enricher implementations support tier-specific logic:

```python
class PersonEnricher(BaseEnricher):
    def enrich(self, person: Person, context: EntityContext, tier: int) -> Person:
        if tier >= 2:
            person.status = "ACTIVE"
            person.assigned_on = datetime(...)

        if tier >= 3:
            person.skills = self._infer_skills_from_role_and_systems(context)
            person.certifications = self._resolve_cert_requirements(context)

        if tier >= 4:
            person.performance_score = self._compute_from_incident_history(context)
            person.total_cost = self._allocate_from_department(context)

        if tier >= 5:
            person.career_trajectory = self._build_from_org_patterns(context)
            person.risk_exposure = self._compute_blast_radius_score(context)

        return person
```

**5. Confidence Cascading**

When enriching a relationship, confidence propagates from source and target:

```python
relationship.confidence = min(source_entity.provenance.confidence,
                              target_entity.provenance.confidence)
```

If a Person's skills come from a Tier 3 enrichment (confidence 0.8) and a System's criticality is a user-provided value (confidence 1.0), a `has_skill_for` relationship gets confidence 0.8.

**6. One Enricher Per Entity Type — No Exceptions**

All 30 types have dedicated enrichers. No catch-all `generic_enricher()`. This enforces domain knowledge embedding.

**7. Industry-Specific Enrichment Profiles**

Profiles customize which enrichers run, which fields are prioritized, and which OSINT sources are consulted:

```python
class EnrichmentProfile:
    name: str  # "tech", "financial", "healthcare"
    enabled_enrichers: set[EntityType]
    osint_sources: list[str]  # Which frameworks to use
    tier_defaults: dict[EntityType, int]  # Default maturity tier per type
    coherence_rules: list[CoherenceRule]

TECH_PROFILE = EnrichmentProfile(
    name="tech",
    enabled_enrichers={Person, System, Role, ...},
    osint_sources=["mitre_attack", "cis_v8", "nist_800_53"],
    tier_defaults={Person: 3, System: 4, Control: 4},
    coherence_rules=[
        PersonSkillRoleAlignmentRule(),
        SystemCostCriticalityCorrelationRule(),
        ...
    ]
)
```

**8. Post-Enrichment Coherence Validation**

A CrossEntityEnricher validates cross-graph consistency:

```python
class CrossEntityEnricher(BaseEnricher):
    """Runs after all per-entity enrichment."""

    def enrich(self, ignored: Entity, context: EntityContext) -> Entity:
        """Actually validates and mutates entire graph."""

        # Person skills align with Role requirements
        # System costs correlate with criticality
        # Control effectiveness correlates with Risk residual levels
        # Temporal fields are chronologically consistent
        # Framework mappings reference canonical sources
        pass
```

---

## Consequences

**Positive:**

1. Enrichment is additive and non-breaking — existing generators unchanged
2. Graph fidelity tunable to desired maturity level via tier selection
3. Provenance tracking enables data quality assessment at any point
4. Context-aware agents produce coherent field values
5. OSINT grounding makes framework mappings verifiable
6. Profile system allows vertical (industry) customization
7. Per-agent testing is straightforward; no monolithic enrichment black box
8. Confidence cascading provides quantified data quality signals to consumers

**Negative:**

1. Implementation scale: ~12K LOC for enrichers + ~4K LOC for tests
2. Maintenance burden: 30 enrichers must be updated when schema changes
3. Framework reference data must be manually curated and versioned
4. External OSINT search (if enabled) adds latency and cost

---

## Implementation Plan

**Phase 1 (MVP):**
- GraphContextEngine implementation
- EnricherRegistry and BaseEnricher abstraction
- PersonEnricher, SystemEnricher, RoleEnricher (3 types, Tier 2-3 only)
- OSINTResearchAgent with built-in NIST/ISO/CIS/ATT&CK data
- Basic orchestration: `hckg enrich --tier 2` on demo graph
- Tests: 200+ test cases covering agent context access and provenance mutation

**Phase 2:**
- Remaining 27 enrichers (all entity types, Tier 2-3)
- Coherence validation rules (10+ rules, e.g., skill-role alignment)
- Profile system (tech, financial, healthcare)
- CLI: `--profile tech`, `--tier 4`

**Phase 3:**
- Tier 4-5 quantitative metrics
- Scenario analysis field preparation
- Optional external OSINT search (feature-flagged)
- Performance benchmarks (enrichment time vs. entity count)

---

## Alternatives Considered and Rejected

| Alternative | Rejection Reason |
|-------------|------------------|
| LLM-driven enrichment (all fields at once) | Non-deterministic, expensive, hard to ground in canonical frameworks, confidence undefined |
| Single-pass enrichment (all tiers at once) | No progressive maturity, all-or-nothing fidelity, cross-entity coherence validation still needed |
| Enrichment in generators | Breaks separation of concerns, generators become complex, untestable without full graph context |
| Embedding OSINT in enrichers (no centralized agent) | Duplicates framework reference data, hard to keep consistent, no single source of truth |

---

## Risks of This Decision

1. **Maintenance complexity** -- 30 enrichers and cross-entity coherence rules must be maintained and tested. Mitigated by per-enricher unit tests and integration test suites
2. **Schema coupling** -- If entity schemas change significantly, enrichers must be updated. Mitigated by centralized schema definitions and validation
3. **OSINT data staleness** -- Built-in framework data (NIST, ISO, CIS, ATT&CK) must be refreshed. Mitigated by versioning framework data and documenting update cadence
4. **Context explosion** -- EntityContext could be large for highly connected entities. Mitigated by lazy loading and optional path traversal depth limits

---

## Re-Evaluation Triggers

Revisit this decision if any of the following occur:

- **LLM costs drop significantly** (< $0.0001 per entity) and streaming inference is available. Reconsider LLM-driven enrichment for Tier 4-5, with OSINT grounding validated in post-processing
- **Entity schema changes substantially** (>5 new fields per type or restructuring). Reassess whether enrichers can be generalized or whether a schema-driven enrichment approach is needed
- **Real data import (CSV/JSON ingest) matures** substantially. Enrichment should complement, not duplicate, imported data. Establish clear precedence rules (imported > Tier 5 enriched > Tier 3 enriched)
- **Cross-entity coherence rules exceed 50** in number or become difficult to maintain. Consider a domain-specific language or rule engine (e.g., Drools, Nools)
- **Enrichment latency exceeds 10ms per entity** at scale (100k entities). Consider parallelization or caching strategies

---

## References

- [CMMI Capability Levels](https://cmmiinstitute.com/) -- Maturity model baseline
- [DCAM Data Capability Assessment Model](https://www.dataversity.net/) -- Data maturity framework
- [NIST SP 800-53](https://csrc.nist.gov/publications/detail/sp/800-53/rev-5/final) -- Security controls reference
- [ISO 27001](https://www.iso.org/isoiec-27001-information-security-management.html) -- Information security standards
- [CIS Controls v8](https://www.cisecurity.org/cis-controls/) -- Cybersecurity controls
- [MITRE ATT&CK Framework](https://attack.mitre.org/) -- Threat modeling and tactics
- ADR-001: Custom Synthetic Data Pipeline -- Generation layer (predecessor to enrichment)
- ADR-006: Coordinated Template Dicts -- Field value coherence principles
- ADR-008: Relationship Weaving -- Relationship graph construction patterns
