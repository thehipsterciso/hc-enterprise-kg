# ADR-001: Custom Synthetic Data Pipeline over External Libraries

**Status:** Accepted
**Date:** 2026-02-21
**Context:** Synthetic data generation for enterprise knowledge graphs

---

## Summary

The synthetic data pipeline in hc-enterprise-kg is a custom implementation. This document records the architectural decision to build and maintain that pipeline rather than adopt an external synthetic data library, and the evaluation that supports it.

---

## Problem Statement

Generating structurally accurate enterprise organizational models requires producing 30 entity types, 52 relationship types, and domain-specific field values that are internally consistent across industry profiles, scaling tiers, and organizational structures. The question is whether an existing open-source Python library can handle this, or whether the problem demands a purpose-built pipeline.

---

## Evaluation Criteria

Five properties define what the pipeline must deliver:

1. **Graph-native generation** -- Output is a connected knowledge graph with typed, weighted, directional relationships, not tabular rows
2. **Domain-constrained coherence** -- Coordinated template dicts across 30 generators producing internally consistent field values (risk math, encryption-classification alignment, tech stack coherence)
3. **Research-backed scaling** -- Entity counts derived from `scaled_range()` with industry-specific `ScalingCoefficients` and size-tier multipliers calibrated against Gartner, MuleSoft, NIST, Hackett Group, and McKinsey benchmarks
4. **Profile-driven variation** -- Three industry profiles (tech, financial, healthcare) producing structurally different graphs that reflect real-world sector patterns
5. **Structural validation** -- Automated quality scoring across five dimensions with a 0.70 floor

Any candidate library must satisfy all five, or clearly identify which it can offload.

---

## Libraries Evaluated

### Tier 1: Multi-Table / Relational Synthesis

| Library | Version | License | Approach | Active |
|---------|---------|---------|----------|--------|
| **SDV (Synthetic Data Vault)** | 1.32.1 | Business Source License | Gaussian Copula + HMA for multi-table relational data | Yes |

SDV is the most capable general-purpose synthetic data library available. Its `HMASynthesizer` models parent-child relationships using hierarchical recursive algorithms, and its `DayZSynthesizer` can generate multi-table data from metadata alone without training data.

**Where it falls short:**

- **Table limit** -- `HMASynthesizer` is optimized for ~5 tables at 1 level of depth. Modelling 30 entity types with 52 relationship types would require flattening the graph into dozens of interrelated tables, losing the graph semantics that make the output useful for blast radius, centrality, and path analysis
- **Tabular paradigm** -- SDV operates on foreign-key parent-child relationships. Enterprise knowledge graphs have many-to-many, directional, weighted relationships with typed properties (`depends_on` with dependency strength, `mitigates` with effectiveness metadata). This is not a tabular problem
- **Requires training data** -- SDV learns statistical distributions from existing datasets. Our pipeline generates from domain rules and scaling coefficients, not from real organizational data. `DayZSynthesizer` can generate from metadata, but without the domain constraints that make the output structurally accurate
- **License incompatibility** -- BSL restricts commercial use. hc-enterprise-kg is MIT-licensed

### Tier 2: Field-Level Data Providers

| Library | Version | License | Approach | Active |
|---------|---------|---------|----------|--------|
| **Faker** | 40.4.0 | MIT | Provider-based fake data (names, addresses, dates, text) | Yes |
| **Mimesis** | 19.1.0 | MIT | Schema-based fake data, zero dependencies, typed | Yes |

Both libraries generate realistic atomic field values -- names, company names, addresses, IP addresses, phone numbers, dates. Neither provides relational modelling, constraint enforcement, or domain-specific generation logic.

**Current usage:** Faker is already a dependency for leaf-level field values (person names, email addresses, network CIDRs). This is the correct scope for a field-level provider. The generators layer domain-specific coordinated templates on top of these atomic values.

**Mimesis as alternative:** Mimesis offers ~2x performance over Faker, zero external dependencies, full type annotations, and schema-based generation. It is a viable drop-in for leaf-level values if Faker performance becomes a bottleneck. It does not change the architectural picture.

### Tier 3: Privacy-Preserving Synthesis (Wrong Paradigm)

| Library | Version | License | Approach | Active |
|---------|---------|---------|----------|--------|
| **Gretel Synthetics** | 0.22.20 | Source Available | LSTM/GAN-based, differential privacy | Slow cadence |
| **ydata-synthetic** | 1.4.0 | GPL-3.0 | GAN-based (CTGAN, WGAN) | Deprecated |
| **DataSynthesizer** | 0.1.13 | MIT | Bayesian networks, differential privacy | Inactive |
| **Synthcity** | 0.2.12 | Apache-2.0 | Plugin-based, 20+ generative models | Yes |

These libraries solve a fundamentally different problem: learning statistical distributions from sensitive real-world data and producing privacy-safe copies. Our pipeline generates organizational models from scratch using domain rules and scaling coefficients. There is no source dataset to learn from, no privacy constraint to satisfy, and no statistical distribution to preserve. Wrong tool for the job.

### Tier 4: Knowledge Graph / RDF Generators

| Library | Version | License | Approach | Active |
|---------|---------|---------|----------|--------|
| **PyGraft** | Academic | MIT | Schema + KG generation with OWL reasoning | Academic |
| **RDFGraphGen** | PyPI | -- | RDF graphs from SHACL shape constraints | Academic |

Both operate in the Semantic Web / RDF ontology space. They generate abstract ontological graphs with RDFS/OWL constructs, not structured enterprise organizational models with Pydantic entities, industry profiles, and domain-specific field values. Closer in spirit to the graph generation problem, but targeting a different domain and data model entirely.

---

## What the Custom Pipeline Does That No Library Can

The gap between available libraries and the requirements is not incremental -- it is structural. The pipeline's value is in the domain logic, not the data generation mechanics.

### 1. Layered Generation with Referential Integrity

Twelve generation layers (L00 Foundation through L11 Initiatives) execute in dependency order. L01 Compliance entities exist before L02 Technology entities reference them. L05 People are assigned to L04 Departments. This is a topological build, not independent table generation.

### 2. Research-Backed Scaling

`scaled_range(employee_count, coefficient, floor, ceiling)` with industry-specific `ScalingCoefficients` and four size-tier multipliers (startup 0.7x, mid-market 1.0x, enterprise 1.2x, large 1.4x) produces entity counts calibrated to published research. At 14,512 employees, a tech profile generates 42 departments and 301 roles. No library encodes this domain knowledge.

### 3. Dynamic Structural Adaptation

Departments exceeding 500 headcount subdivide into sub-departments via 30+ industry-specific `SUB_DEPARTMENT_TEMPLATES`. Roles expand with seniority variants (Junior/Senior/Staff) based on sub-department headcount. The organizational structure reshapes itself as the graph scales.

### 4. Coordinated Template Dicts

All 30 generators use domain-specific template dictionaries that produce internally consistent field values. A system's technology stack, vendor associations, data classifications, and compliance mappings are correlated, not independently randomized. This is what makes the graph structurally accurate rather than statistically plausible.

### 5. Relationship Weaving

33 weaver methods produce 52 relationship types with contextual weight, confidence scores, and typed properties via `_make_rel()`. Mirror fields are populated post-weave. A `depends_on` between two systems carries dependency type and strength. A `mitigates` between a control and a risk carries effectiveness metadata. This is domain modelling, not foreign-key generation.

### 6. Quality Scoring

`assess_quality()` validates five dimensions: risk math consistency (RISK_MATRIX determinism), description quality (no lorem ipsum), tech stack coherence, field correlations, and encryption-classification alignment. The orchestrator warns if the composite score falls below 0.70. No external library provides enterprise-domain quality validation.

---

## Decision

**Build and maintain the custom synthetic data pipeline.**

The external library ecosystem addresses two adjacent problems (privacy-preserving copies of real data, and realistic atomic field values) but does not address the core problem: generating structurally accurate, domain-constrained, scaling-aware enterprise organizational models as connected knowledge graphs.

The architecture is:

- **Custom code** (~85%) -- Orchestrator, 30 generators, 33 relationship weavers, quality scoring, scaling logic, profile system, layer ordering
- **Faker** (~15%) -- Leaf-level field values (names, addresses, dates, IPs, CIDRs) where domain-specific templates are not required

This is the correct boundary. The domain logic is the product.

---

## Alternatives Considered and Rejected

| Alternative | Rejection Reason |
|-------------|------------------|
| SDV as orchestrator | Tabular paradigm, ~5 table limit, BSL license, requires training data |
| Mimesis replacing Faker | Valid micro-optimization, not an architectural change. Evaluate if Faker becomes a performance bottleneck |
| PyGraft for graph structure | RDF/OWL domain, no enterprise organizational modelling, no Pydantic integration |
| Hybrid (SDV for entities, custom for relationships) | Adds complexity without reducing it. SDV cannot encode scaling coefficients or coordinated templates. The orchestrator already handles entity generation cleanly |

---

## Risks of This Decision

1. **Maintenance burden** -- 30 generators and 33 weavers are custom code that must be maintained, tested, and extended. Mitigated by 740+ tests, quality scoring, and the performance benchmarking suite
2. **Knowledge concentration** -- The domain logic encodes specific scaling research and industry patterns. Mitigated by CLAUDE.md, ARCHITECTURE.md, and comprehensive inline documentation
3. **No free lunch from upstream improvements** -- If SDV or a future library develops graph-native generation with constraint support, we do not benefit automatically. Mitigated by periodic re-evaluation (see below)

---

## Re-Evaluation Triggers

Revisit this decision if any of the following occur:

- A Python library with MIT/Apache-2.0 license ships graph-native synthetic data generation with typed, weighted, directional relationships
- SDV or equivalent adds support for 30+ table schemas without requiring training data, under a permissive license
- The maintenance cost of custom generators exceeds the cost of adapting an external library (measured by test failures, bug frequency, or time-to-add-entity-type)
- A domain-specific enterprise modelling library emerges that encodes organizational scaling research

---

## References

- [SDV Documentation](https://docs.sdv.dev/sdv) -- Multi-table relational synthesis
- [Faker Documentation](https://faker.readthedocs.io/) -- Field-level fake data
- [Mimesis Documentation](https://mimesis.name/) -- High-performance fake data
- [PyGraft](https://github.com/nicolas-hbt/pygraft) -- Synthetic knowledge graph generation (RDF/OWL)
- Gartner, MuleSoft, NIST, Hackett Group, McKinsey -- Scaling coefficient sources (see `docs/profiles.md`)
