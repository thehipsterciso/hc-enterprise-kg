# CDAIO-Informed Roadmap: hc-enterprise-kg

**Date:** 2026-02-28
**Author:** Thomas Jones, CDAIO Candidate
**Companion:** [docs/cdaio-evaluation.md](cdaio-evaluation.md)

---

## North Star

hc-enterprise-kg is a rapid-evaluation platform. It helps people understand an enterprise fast — its structure, dependencies, risks, and governance posture — without requiring months of discovery or six-figure consulting engagements.

It is **not** intended to be a production-grade enterprise architecture tool, a compliance management system, or a replacement for purpose-built governance platforms. Anyone needing that level of rigor should invest the time and money in proper enterprise architecture, governance frameworks, and organizational change management.

The roadmap below adds capabilities that make the rapid-evaluation use case more complete. Each item is scoped to what a lightweight knowledge graph can reasonably represent — enough to surface understanding and inform strategy, not enough to run operations.

Every item on this roadmap traces to a specific teaching from the CMU Heinz CDAIO program. Attribution is given to the advisor whose instruction surfaced the gap. Where cohort discussion or team analysis contributed to the insight, that is noted.

---

## Phasing

| Phase | Theme | Timeline | Scope |
|-------|-------|----------|-------|
| **1** | Strategic Value Layer | Near-term | Value measurement, initiative lifecycle — the gaps every module hit |
| **2** | Data Architecture Depth | Near-term | Semantic layer, data product concepts, AI-readiness — Module 3 gaps |
| **3** | Organizational Readiness | Medium-term | Fluency, decision traceability, culture indicators — Module 4–5 gaps |
| **4** | Emerging Concerns | Future | AI model governance, non-human identity, data ethics — forward-looking |

---

## Phase 1: Strategic Value Layer

These are the highest-impact gaps. Every module — Steyer, Cheriath, Craig — emphasized that a CDAIO who cannot articulate value in financial terms does not survive. The platform models the enterprise but cannot answer "is this investment working?" or "what should we do next?"

### 1.1 Value Measurement on Initiative

**Gap:** No financial structure on Initiative entity. Cannot represent ROI, investment ask, benefit realization, or value category.

**Attribution:** Dr. David Steyer (Module 1) — "It either has to make me money, save me money, or keep me out of jail." Craig (Module 5) — value measurement framework with four categories (operational, customer, economic, strategic) and the principle that finance must be the referee for value claims. Krishna Cheriath (Module 2) — the distinction between "CFO-certifiable value" and "bullshit value."

**Change:** Add fields to Initiative entity:

```
value_category: str          # operational | customer | economic | strategic
investment_ask: float        # total funding requested
investment_currency: str     # USD default
projected_annual_value: float
value_confidence: str        # demonstrated | modeled | estimated | aspirational
financial_validated: bool    # has finance reviewed and certified?
payback_months: int | None   # estimated time to breakeven
```

**Scope:** Field additions to an existing entity. No new entity type. Enough to classify and filter initiatives by value category and confidence level during rapid evaluation. Not a replacement for a proper financial model.

**What this enables:** "Show me all initiatives with demonstrated value over $1M" or "Which initiatives have not been financially validated?" — questions that every board asks and that the platform currently cannot answer.

### 1.2 Initiative Lifecycle Stage

**Gap:** No way to track where an initiative stands in its lifecycle. Cannot differentiate a napkin idea from a funded pilot from a scaled production deployment.

**Attribution:** Craig (Module 5) — Four Ps framework (Problem → POC → Pilot → Production) with explicit stage-gate criteria. Cheriath (Module 2) — the Ferrari vs. Cargo Ship distinction between quick wins and structural programs.

**Change:** Add fields to Initiative entity:

```
lifecycle_stage: str         # problem | poc | pilot | production | retired
initiative_type: str         # quick_win | structural | foundational
stage_gate_criteria: str     # what must be true to advance
time_to_value: str           # < 3 months | 3-12 months | 12+ months
```

**Scope:** Field additions. Enables filtering and prioritization during rapid evaluation. Not a project management system.

**What this enables:** "Which initiatives are stuck in POC?" or "Show me quick wins that could demonstrate value in under 3 months" — the prioritization questions Cheriath and Craig both said define the first 180 days.

### 1.3 Relationship: `creates_value_for`

**Gap:** No relationship connecting Initiative to the business outcomes it targets. Cannot traverse from a strategic investment to the capabilities, systems, or data domains it improves.

**Attribution:** Cheriath (Module 2) — the digital blueprint must connect investments to the parts of the enterprise they affect. Craig (Module 5) — value attribution requires traceability from initiative to outcome.

**Change:** Add relationship type `creates_value_for` with domain Initiative and range BusinessCapability, DataDomain, System, Department.

**Scope:** One new relationship type. Enables traversal from initiative to impact area and vice versa.

---

## Phase 2: Data Architecture Depth

Module 3 exposed gaps in how the platform represents modern data architecture concepts — particularly the data mesh paradigm and the semantic layer that makes data self-describing.

### 2.1 Data Product Fields on DataAsset

**Gap:** DataAsset models individual data artifacts but not the data-as-a-product concept from data mesh — published APIs, consumer contracts, producer accountability, SLAs.

**Attribution:** Module 3 Instructor — Zhamak Dehghani's four data mesh principles, particularly domain ownership and data as a product. Dr. Steyer (Module 1) — the Sears catalog analogy for how producers publish data with agreed protocols.

**Change:** Add fields to DataAsset:

```
is_data_product: bool        # explicitly published for consumption?
product_owner_role: str      # reference to Role entity
consumer_count: int | None   # how many downstream consumers
access_protocol: str         # API | file_share | streaming | query
sla_freshness: str           # real-time | hourly | daily | weekly
```

**Scope:** Field additions to existing entity. Distinguishes raw data assets from intentionally published data products. Enough for rapid evaluation of data mesh readiness.

**What this enables:** "How many data assets are published as products vs. sitting in silos?" and "Which data products have no defined SLA?" — direct inputs to the data strategy deliverable.

### 2.2 Semantic Layer Representation

**Gap:** No entity type for business glossaries, shared definitions, or semantic models. DataDomain.business_glossary_reference is a URL pointer, not a structural model.

**Attribution:** Module 3 Instructor — the semantic layer as the bridge between technical data and business meaning. Dr. Steyer (Module 1) — the "turnover" example (US vs. UK meaning) demonstrating why metadata and shared definitions are non-negotiable.

**Change:** Add optional fields to DataDomain:

```
glossary_term_count: int | None
has_semantic_model: bool
semantic_coverage: str       # full | partial | none
definition_conflicts: int    # known cross-domain definition disagreements
```

**Scope:** Field additions. Not a glossary management system. Enough to flag whether semantic governance exists and where it breaks down.

### 2.3 AI-Readiness Metadata on DataAsset

**Gap:** No representation of whether data is suitable for AI/ML consumption — bias, representativeness, labeling quality, or training suitability.

**Attribution:** Module 3 Instructor — AI-ready data criteria. Karan DeWal (Module 4) — new data types from AI and the governance implications of training data.

**Change:** Add fields to DataAsset:

```
ai_ready: bool | None        # assessed for ML suitability?
bias_assessed: bool          # has bias evaluation been performed?
labeling_quality: str        # high | medium | low | unlabeled | na
training_eligible: bool      # licensing and compliance allow ML training?
```

**Scope:** Four boolean/string fields. Enough to answer "what percentage of our data assets have been assessed for AI readiness?" during rapid evaluation. Not a model governance platform.

**What this enables:** The question every CDAIO gets asked: "Are we AI-ready?" This gives a structural answer instead of hand-waving.

---

## Phase 3: Organizational Readiness

Modules 4 and 5 converged on a consistent message: technical capability is 30% of the problem. The other 70% is people, culture, fluency, and organizational readiness. The platform models the 30% well. These additions give it lightweight hooks into the 70%.

### 3.1 Fluency Indicators on Department / OrganizationalUnit

**Gap:** No way to represent organizational data literacy or readiness at the department or unit level.

**Attribution:** Craig (Module 5) — 5-level fluency framework (aware → literate → proficient → advanced → expert). Cheriath (Module 2) — fluency as the fourth strategic dimension that most organizations ignore. Doug Laney (Module 4) — culture assessment as a prerequisite for maturity advancement.

**Change:** Add optional fields to Department and OrganizationalUnit:

```
data_fluency_level: int | None   # 1-5 scale per Craig's framework
fluency_assessed_date: str | None
training_program_active: bool
```

**Scope:** Three fields on two existing entities. Not a learning management system. Enough to color-code an org chart by data fluency during rapid evaluation and identify which departments are ready for data initiatives and which need investment first.

### 3.2 Decision Rights on Role

**Gap:** No structured representation of who decides what. Cannot model the DAI framework or RACI assignments.

**Attribution:** Cheriath (Module 2) — DAI Decision Framework (Decision owner, Advice givers, Informed) as a practical alternative to full RACI. Craig (Module 5) — decision intelligence and the three stages of human-machine interaction.

**Change:** Add optional fields to Role:

```
decision_domains: list[str]      # what this role decides (e.g., "data classification", "vendor selection")
decision_authority: str          # decides | advises | informed
```

**Scope:** Two fields. Enables "who has decision authority over data classification?" queries. Not a full RACI matrix — that belongs in a governance tool, not a knowledge graph.

### 3.3 Culture Indicator Fields on OrganizationalUnit

**Gap:** Culture is inherently hard to model in a graph. But its indicators — governance cadence, quality trends, engagement with data tools — are measurable.

**Attribution:** Doug Laney and Karan DeWal (Module 4) — VECTOR framework for culture assessment. Craig (Module 5) — adoption-first strategy and go-and-see observation.

**Change:** Add optional fields to OrganizationalUnit:

```
governance_cadence: str          # weekly | monthly | quarterly | none
data_quality_trend: str          # improving | stable | declining | unknown
dashboard_adoption_pct: float | None  # % of unit actively using analytics
```

**Scope:** Three fields. Indicators, not measurements. Enough to identify which parts of the organization have data culture momentum and which don't. A CDAIO walking into a new role can color-code the org by these indicators within a week.

---

## Phase 4: Emerging Concerns

These gaps were raised in Modules 3–5 as forward-looking concerns. They are real but less urgent for rapid evaluation today. Documented here for future reference.

### 4.1 AI Model Governance

**Gap:** No entity type for ML models, their training data, deployment status, bias metrics, or drift monitoring.

**Attribution:** Karan DeWal (Module 4) — model validation, fairness monitoring, and bias governance. Module 3 Instructor — AI-ready data criteria and the governance chain from training data to deployed model.

**Future direction:** A lightweight `AIModel` entity type with fields for model_type, training_data_refs, deployment_status, last_validated, fairness_assessed, and drift_status. Relationship `trained_on` to DataAsset and `deployed_in` to System.

**Why deferred:** Rapid evaluation typically assesses an organization's AI readiness, not its deployed model inventory. The Phase 2 AI-readiness fields on DataAsset are the higher-priority enabler.

### 4.2 Non-Human Identity Management

**Gap:** No entity type for AI agents, service accounts, or automated actors. Person is human-only.

**Attribution:** Karan DeWal (Module 4) — non-human identities as an emerging governance challenge. As AI agents proliferate, "who did this" increasingly means "which system or agent did this."

**Future direction:** Either extend Person with an `is_human` flag or create a lightweight `ServiceIdentity` entity. Relationship `acts_as` to Role.

**Why deferred:** Few organizations have formalized non-human identity governance. Important to track but premature for rapid evaluation.

### 4.3 Data Ethics Records

**Gap:** No entity type for ethical review records, appropriate use policies, or trust metrics.

**Attribution:** Craig (Module 5) — data ethics as trust currency. The principle that organizations which treat ethics as a checkbox rather than a discipline eventually pay the price in customer trust and regulatory exposure.

**Future direction:** Optional `ethics_reviewed` and `appropriate_use_policy_id` fields on DataAsset and Initiative. Lightweight — not an ethics review board management system.

**Why deferred:** Ethics governance is better served by policy tooling and organizational process than by knowledge graph structure. The Policy entity can already reference ethics policies; the gap is in linking them to specific data assets and initiatives.

### 4.4 Data Valuation (Infonomics)

**Gap:** No economic valuation model for data assets. DataAsset has no representation of the properties Doug Laney described — non-rivalrous, non-depleting, self-generative.

**Attribution:** Doug Laney (Module 4) — *Infonomics* framework. Data as an asset that appreciates with use rather than depreciating.

**Future direction:** Optional `estimated_economic_value`, `value_basis` (cost, market, income, utility), and `monetization_status` fields on DataAsset.

**Why deferred:** Data valuation is methodologically contentious. Most organizations cannot produce defensible valuations. Including it in rapid evaluation risks false precision. Better to add after the organization has mature data governance (Phase 1–3 capabilities).

---

## Implementation Notes

**Versioning:** Each phase item gets its own patch bump per project engineering discipline. No batching.

**Testing:** Each field addition requires updated synthetic generators, schema tests, and MCP serialization tests.

**Backward compatibility:** All new fields must default to `None`, `False`, `""`, or `Field(default_factory=list)` to avoid breaking existing graphs. Existing data loads without modification.

**Documentation:** Each change updates entity-model.md and CHANGELOG.

**What this roadmap is not:** A project plan with dates. The CDAIO program runs through mid-2026. Items will be implemented as they become relevant to practicum deliverables and as the platform's user base validates the need. The roadmap is a backlog, not a commitment.

---

## Advisor and Program Attribution

| Advisor | Modules | Primary Contributions to This Roadmap |
|---------|---------|--------------------------------------|
| Dr. David Steyer | 1 | Data lifecycle, governance mechanisms, data quality dimensions, business case construction, cost of poor quality |
| Krishna Cheriath | 2 | Digital blueprint concept, four-dimension strategy, CFO-certifiable value, DAI framework, minimum viable bureaucracy, partnership model |
| [Module 3 Instructor] | 3 | Data mesh/fabric architecture, semantic layer, AI-ready data criteria, data observability, medallion architecture |
| Doug Laney | 4 | 8-dimension maturity model, DCAM framework, data valuation, Infonomics properties, governance operating models |
| Karan DeWal | 4 | VECTOR culture framework, decision traceability, AI-era data types, non-human identity management |
| Craig [Last Name] | 5 | Four Ps lifecycle, value measurement framework, fluency levels, decision intelligence, finance as referee, adoption-first strategy, data ethics |

### Program

**Carnegie Mellon University, Heinz College of Information Systems and Public Policy** — Chief Data & AI Officer Program. The analytical frameworks, rigor standards, and practitioner perspective that shaped both this evaluation and roadmap.

### Cohort Contributions

*[Placeholder for specific cohort member contributions — team analysis, discussion insights, or peer review that influenced roadmap priorities.]*

| Cohort Member | Contribution |
|--------------|-------------|
| *[Name]* | *[Specific insight or analysis]* |
| *[Name]* | *[Specific insight or analysis]* |
| *[Name]* | *[Specific insight or analysis]* |

---

## Relationship to hc-cdaio-kg

The hc-cdaio-kg repository contains the Rackspace Technology rapid evaluation — the first real-world application of hc-enterprise-kg. Gaps identified in that evaluation directly informed this roadmap. As roadmap items are implemented in the platform, they become available for use in future rapid evaluations.

The two repositories are complementary:
- **hc-enterprise-kg** — the platform (schema, engine, generators, analysis, MCP server)
- **hc-cdaio-kg** — a specific evaluation (entities, relationships, due diligence analysis)

Changes to the platform improve all evaluations. Changes to a specific evaluation inform what the platform should support next.
