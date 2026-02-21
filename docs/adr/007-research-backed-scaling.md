# ADR-007: Research-Backed Scaling with Industry Coefficients

**Status:** Accepted
**Date:** 2026-02-21
**Context:** Entity count scaling model for synthetic organizations

---

## Summary

Entity counts scale with employee count using `ScalingCoefficients` dataclasses per industry, a `scaled_range()` function, and four size-tier multipliers (startup 0.7x, mid-market 1.0x, enterprise 1.2x, large 1.4x). Coefficients are calibrated against Gartner, MuleSoft, NIST, Hackett Group, and McKinsey benchmarks. This is the model that makes a 200-employee tech startup structurally different from a 10,000-employee financial institution.

---

## Decision

Scale entity counts dynamically based on employee count, industry profile, and organizational size tier, using research-calibrated coefficients.

---

## The Scaling Model

### `scaled_range(employee_count, coefficient, floor, ceiling)`

1. Determine the size-tier multiplier: startup (<250) = 0.7x, mid-market (250-2000) = 1.0x, enterprise (2000-10000) = 1.2x, large (10000+) = 1.4x
2. Compute `base = max(floor, int((employee_count / coefficient) * tier))`
3. Return `(low, high)` where `low = 0.8 × base` and `high = 1.2 × base`, both clamped to `[floor, ceiling]`
4. The orchestrator calls `random.randint(low, high)` for natural variance

### Industry Coefficients

`ScalingCoefficients` defines the employees-per-entity ratio for each entity type. Lower coefficient = more entities per employee = denser infrastructure.

Example differentials across industries:

| Entity Type | Technology | Financial Services | Healthcare |
|-------------|-----------|-------------------|------------|
| Systems | 1:8 | 1:12 | 1:15 |
| Controls | 1:50 | 1:20 | 1:25 |
| Data Assets | 1:15 | 1:10 | 1:5 |
| Customers | 1:50 | 1:25 | 1:40 |
| Contracts | 1:15 | 1:8 | 1:12 |

Financial services has 2.5x the controls of tech (regulatory burden). Healthcare has 3x the data assets of tech (patient records, clinical data, imaging).

---

## Alternatives Considered

| Alternative | Assessment |
|-------------|------------|
| **Fixed ranges per entity type** | Simple, predictable. A 100-person startup and a 10,000-person enterprise get the same 20-100 systems. This is obviously wrong — organizational infrastructure scales with headcount |
| **Linear scaling with a single universal ratio** | Every industry, every size tier, same ratio. Ignores the reality that financial services orgs have dramatically more compliance infrastructure than tech startups. The single ratio would be wrong for everyone |
| **User-specified exact counts for everything** | Maximum flexibility, zero automation. Users must decide how many systems, vendors, controls, etc. an organization should have. Most users do not know the answer. Exists as `count_overrides` escape hatch |
| **Logarithmic or power-law scaling** | Some entity types may scale sub-linearly (departments do not double when headcount doubles). Currently not modeled — `scaled_range()` is approximately linear with a tier multiplier. A power-law model could be more accurate but adds complexity |
| **ML from real organizational data** | Train a model on real-world organizational structures. Would produce the most accurate scaling. Requires a training dataset of real organizational models that does not exist and would be highly sensitive data |

---

## Research Basis

The coefficients are calibrated against published research, not invented:

- **Gartner** -- IT spending ratios, system-to-employee benchmarks by industry
- **MuleSoft** -- Enterprise integration density research
- **NIST** -- Control framework density per regulatory regime
- **Hackett Group** -- Shared services and organizational structure benchmarks
- **McKinsey** -- Operating model research, department sizing

These are directional calibrations, not exact replication. A coefficient of `systems=8` for technology does not mean "every real tech company has exactly 1 system per 8 employees." It means "at this ratio, the generated graph produces a system landscape that is structurally plausible for a tech company of this size."

---

## Where This Diverges from Best Practice

### Coefficients Are Estimates

The research sources provide ranges, not point estimates. The project collapses ranges into single coefficients per industry. A technology company's system density could realistically be anywhere from 1:5 to 1:15. We chose 1:8 and applied a ±20% variance band via `scaled_range()`. The variance is narrower than reality.

### Size-Tier Breakpoints Are Discrete

The four size tiers (250, 2000, 10000) create discontinuities. A 249-employee org gets 0.7x multiplier; a 250-employee org gets 1.0x. In reality, organizational maturity scales continuously. The discrete tiers are a simplification — accurate enough for the project's purpose (scenario analysis, not actuarial modelling) but not smooth.

### Three Profiles for Every Industry

Technology, financial services, and healthcare. Every other industry (government, manufacturing, retail, energy, education) must pick the closest match. This is a known gap. Adding a profile requires authoring a full `ScalingCoefficients` instance with 22 coefficients and a set of `DepartmentSpec` entries, which requires industry-specific domain knowledge.

### The Dynamic Department Subdivision

Departments exceeding 500 headcount subdivide into sub-departments via 30+ industry-specific `SUB_DEPARTMENT_TEMPLATES`. Roles expand with seniority variants (Junior/Senior/Staff). At 14,512 employees (tech profile): 42 departments (was 10), 301 roles (was 35).

The 500-headcount threshold is hardcoded, not configurable per profile. It models a common span-of-control inflection point, but different organizations subdivide at different thresholds. The sub-department templates are industry-specific but may not match every organization's actual hierarchy.

---

## The Count Override Escape Hatch

`count_overrides` bypasses scaling entirely: `SyntheticOrchestrator(kg, profile, count_overrides={"system": 500})` pins systems at exactly 500 regardless of employee count or profile. The CLI exposes 25 flags (`--systems 500 --vendors 100`).

Five entity types are excluded from overrides because they are derived: department (from `DepartmentSpec`), role (from departments), network (from `NetworkSpec`), vulnerability (from system count × probability), and person (from `employee_count`).

---

## Trade-Offs

| Benefit | Cost |
|---------|------|
| Structurally different graphs per industry and scale | Coefficients are estimates, not measurements |
| Research-backed credibility | Only three industry profiles |
| Natural variance via randomized range | Discrete size-tier breakpoints create discontinuities |
| Count overrides as escape hatch | Five entity types cannot be overridden |
| Dynamic dept/role expansion at scale | 500-headcount subdivision threshold is hardcoded |

---

## Risks

1. **Coefficient drift** -- Industry benchmarks evolve. Coefficients calibrated to 2024-era research may not reflect 2028-era organizational structures. Mitigated by periodic recalibration, but no automated detection
2. **Edge case math** -- At large employee counts, `low` can exceed `ceiling` in `scaled_range()`. This is a documented bug pattern, mitigated by explicit clamping: `low = min(ceiling - 1, max(floor, ...))`
3. **Profile gap** -- Organizations in industries without a profile (government, manufacturing) get a best-guess approximation. No way to know how wrong it is without domain-specific validation

---

## Re-Evaluation Triggers

- New industry benchmark data that significantly changes known ratios
- User reports that generated graphs are structurally implausible for their organization size/industry
- Demand for additional industry profiles (government, manufacturing, retail)
- Evidence that continuous scaling (power-law) would produce meaningfully better graphs than the current tier model

---

## References

- `src/synthetic/profiles/base_profile.py` -- `ScalingCoefficients`, `INDUSTRY_COEFFICIENTS`, `scaled_range()`, `_size_tier_multiplier()`
- `src/synthetic/profiles/tech_company.py` -- Technology profile
- `src/synthetic/profiles/financial_org.py` -- Financial services profile
- `src/synthetic/profiles/healthcare_org.py` -- Healthcare profile
- `docs/profiles.md` -- User-facing profile documentation
