# ADR-006: Coordinated Template Dicts over Random Generation

**Status:** Accepted
**Date:** 2026-02-21
**Context:** Field-level data generation strategy for entity attributes

---

## Summary

All 30 generators use pre-coordinated template dictionaries where related fields are bundled together (system name, OS, tech stack, and ports are a coherent unit), rather than selecting each field independently from separate random pools. Risk levels are computed deterministically from `RISK_MATRIX[likelihood][impact]`. No generator uses `faker.sentence()` or `faker.bs()` for descriptions.

This produces entities that are structurally accurate rather than statistically plausible.

---

## Decision

Use coordinated template dictionaries for all domain-specific field generation. Reserve Faker for leaf-level atomic values only (names, addresses, dates, IPs).

---

## Alternatives Considered

| Alternative | Assessment |
|-------------|------------|
| **Faker for everything** | `faker.sentence()` for descriptions, `faker.bs()` for business context, `faker.company()` for vendor names. Fast to implement, zero domain knowledge. Produces lorem ipsum that is immediately recognizable as fake and carries no analytical value |
| **Independent random selection per field** | System type from one list, OS from another, tech stack from a third. Fields are uncorrelated. A "Jenkins CI" system with "Windows Server" OS and "SAP HANA" technology stack undermines the structural accuracy claim |
| **Markov chain / probabilistic models** | Learn field correlations from training data. Produces statistically plausible output. Requires training data that does not exist (we are generating from domain rules, not copying real organizations). Adds ML complexity for a rule-based problem |
| **Real-world data sampling with anonymization** | Sample from actual organizational data, anonymize PII. Produces the most realistic output. Requires access to real organizational data, raises privacy concerns, and contradicts the project's purpose (generating synthetic models, not anonymizing real ones) |

---

## How Coordinated Templates Work

A system generator template bundles related fields:

```
"Jenkins CI" → type=application, os=linux, technologies=[java, groovy],
               ports=[8080], criticality=high
```

When the generator selects "Jenkins CI," all correlated fields come with it. The system is coherent because the template was designed as a unit by someone who knows what Jenkins is.

This pattern applies across all 30 entity types:

- **Systems** -- Name, type, OS, technologies, ports, criticality are bundled
- **Risks** -- `RISK_MATRIX[likelihood][impact] → risk_level` is deterministic, not random
- **Threat actors** -- 12 named profiles with correlated TTPs, motivation, and sophistication
- **Sites** -- Data centers always have "Restricted" physical security tier
- **Data flows** -- Restricted/Confidential classification correlates with encryption-in-transit
- **Vulnerabilities** -- CVSS score correlates with severity, patch availability correlates with status

---

## Where This Diverges from Best Practice

### Finite Variety

Template dictionaries have finite entries. At very large scales (10,000+ entities of a given type), templates repeat. A 5,000-employee org with 400 systems will have system names and configurations that appear multiple times.

This is acceptable because the graph's value is in the structure and relationships, not in the uniqueness of every system name. But it is a known limitation. Faker supplements templates with randomized names, descriptions, and identifiers to add surface-level variety.

### Manual Maintenance

Every coordinated template was hand-written with domain expertise. Adding a new system type means adding a new template entry with correct field correlations. There is no automated way to generate or validate these templates — correctness depends on the author's domain knowledge.

The quality scoring module (`assess_quality()`) partially compensates by checking tech stack coherence, risk math consistency, and encryption-classification alignment. But it only catches categories of errors, not individual template mistakes.

### Opinionated Domain Assumptions

Templates encode assumptions about what constitutes a coherent technology stack, a reasonable risk profile, or a realistic vendor configuration. These assumptions reflect the authors' experience in technology, financial services, and healthcare organizations. They may not match every organization.

The `count_overrides` mechanism does not extend to template content — you can override how many systems are generated, but not which system templates are used.

---

## What Quality Scoring Validates

The quality module (`assess_quality()`) runs five checks that are only meaningful because templates enforce correlations:

1. **Risk math consistency** -- `risk_level == RISK_MATRIX[likelihood][impact]` for every Risk entity
2. **Description quality** -- No lorem ipsum patterns (regex detection of `faker.sentence()` output)
3. **Tech stack coherence** -- Appliance-type systems do not have web frameworks
4. **Field correlations** -- Residual risk ≤ inherent risk. Data center sites have restricted security
5. **Encryption-classification consistency** -- Restricted/Confidential data flows use encryption in transit

These checks would be meaningless with random generation because there would be no expected correlations to validate.

---

## Trade-Offs

| Benefit | Cost |
|---------|------|
| Entities are internally consistent and domain-plausible | Templates require manual authoring and maintenance |
| Quality scoring can validate structural correctness | Finite variety at large scale |
| Output is useful for scenario analysis, not just load testing | Adding new entity archetypes requires domain expertise |
| No lorem ipsum in any field | More code complexity than random selection |
| Risk math is deterministic and verifiable | Templates encode opinionated domain assumptions |

---

## Risks

1. **Template staleness** -- Technology templates reference specific products (Jenkins, Splunk, SAP HANA). These become dated as products evolve. Mitigated by periodic updates, but no automated detection
2. **Domain bias** -- Templates reflect the authors' experience in US/UK enterprise environments. Organizations in other regions or industries may find the templates unrealistic. Mitigated partially by the three-profile system (tech, financial, healthcare)
3. **Correlation gaps** -- Not all field correlations are enforced by templates. Some entities have fields that should correlate but are selected independently. Quality scoring catches some of these, but coverage is incomplete

---

## Re-Evaluation Triggers

- Template variety becomes visibly insufficient at target scales (repeated system names in a single generation)
- Quality scoring identifies correlation gaps that templates should enforce but do not
- A new industry profile (e.g., government, manufacturing) requires templates that do not exist
- LLM-based entity generation becomes viable and can produce domain-coherent entities without hand-authored templates

---

## References

- `src/synthetic/generators/enterprise.py` -- `RISK_MATRIX` and enterprise entity templates
- `src/synthetic/generators/systems.py` -- System templates with correlated fields
- `src/synthetic/quality.py` -- `assess_quality()` with five validation checks
- `docs/adr/001-custom-synthetic-data-pipeline.md` -- Related: why we build our own pipeline
