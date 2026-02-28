# CDAIO Program Evaluation: hc-enterprise-kg Platform

**Date:** 2026-02-28
**Evaluator:** Thomas Jones, CDAIO Candidate
**Program:** Carnegie Mellon University Heinz College, Chief Data & AI Officer Program
**Platform Version:** v0.30.3

---

## Purpose

This document evaluates hc-enterprise-kg against the curriculum delivered across Modules 1–5 of the CMU Heinz College CDAIO program. The goal is to identify where the platform structurally represents the concepts taught by program advisors, where it falls short, and what incremental changes would close those gaps.

hc-enterprise-kg is a rapid-evaluation tool — not a production-grade enterprise architecture platform. It is designed to facilitate quick wins, surface understanding, and support strategic positioning. Anyone requiring full enterprise-grade implementation should invest in proper architecture, governance, and change management. This evaluation holds the platform to what it claims to be, not what it doesn't.

---

## Methodology

Five module transcripts were analyzed for substantive teaching concepts, frameworks, and principles. Each was mapped against the platform's 30 entity types, 58 relationship types, and analysis capabilities. Alignment was scored as:

- **Strong** — the platform structurally represents the concept and supports practical use
- **Partial** — the concept is representable but requires workarounds or is underspecified
- **Gap** — the concept has no structural representation in the platform

---

## Module-by-Module Alignment

### Module 1: Enterprise Data Management Foundations
**Instructor:** Dr. David Steyer

| Concept | Alignment | Platform Representation |
|---------|-----------|----------------------|
| Data lifecycle (5 stages) | **Strong** | DataAsset carries retention, classification, encryption, quality. DataDomain adds retention_policy with destruction_method and legal_hold_status. DataFlow tracks movement. |
| Data governance — 3 mechanisms | **Strong** | Structural: Department, OrgUnit, Role, Person with `manages`, `reports_to`. Procedural: Policy, Regulation, Control with `enforces`, `implements`, `subject_to`. Relational: `governs`, `responsible_for`, `managed_by` make accountability chains traversable. |
| Data quality — 7 dimensions | **Strong** | QualityReport scores semantic coherence, field completeness, relationship coverage, temporal validity, constraint satisfaction. Quality gate warns below 0.7. DataAsset has quality sub-model. DataDomain has quality_targets with completeness/accuracy/timeliness/consistency. |
| Data architecture (fabric, mesh, lake house) | **Partial** | System entity has system_type and Integration models source/target with SLA. But there is no explicit representation of data fabric vs. mesh topology, no catalog/metadata platform concept. |
| Metadata management | **Partial** | Every entity carries provenance metadata. But metadata-as-connective-tissue — the cross-cutting layer Steyer described running vertically through all architecture layers — is implicit in the graph structure rather than explicitly modeled. |
| Master data / reference data management | **Partial** | DataAsset has data_type and classification. DataDomain scopes governance. But there is no explicit MDM concept — no distinction between master data, reference data, and transactional data as first-class concerns. |
| Data maturity models (DCAM, DAMA CMM) | **Strong** | DataDomain.maturity_dimensions carries DCAM 2.2 dimension scores (1.0–5.0). BusinessCapability has maturity and strategic alignment. Maturity is structurally representable. |
| DIKW hierarchy | **Partial** | The platform operates at the Data and Information layers. Knowledge and Wisdom are implicit in relationship traversal and analysis output, not structurally represented. |
| Business case construction (BLUF, ROI) | **Gap** | No entity type for investment proposals, financial projections, benefit realization, or ROI tracking. Initiative has `benefits` and `funding` fields but nothing approaching the rigor Steyer described — no NPV, IRR, payback period. |
| Cost of poor data quality | **Partial** | Quality scoring exists. Risk entity can model financial_impact. But there is no direct link between data quality scores and business cost — the causal chain Steyer demonstrated (data error → budget overrun → failed school) is not traversable. |
| Data lifecycle ownership | **Strong** | DataDomain has domain_owner and domain_steward references. GoverningPolicy links to Policy entities. The custodianship model Steyer described is structurally present. |

**Module 1 summary:** Strong on governance, lifecycle, quality, and maturity. Gaps in business case/ROI modeling and the cost-of-quality causal chain.

---

### Module 2: Data & AI Strategy
**Instructor:** Krishna Cheriath

| Concept | Alignment | Platform Representation |
|---------|-----------|----------------------|
| The Digital Blueprint | **Strong** | The entire platform is a digital blueprint engine. 30 entity types across 11 layers with typed relationships. The MCP server makes it queryable in natural language. This is the artifact Cheriath said 80% of organizations lack. |
| Four-dimension strategy (tech foundation, data mgmt, unlocking value, fluency) | **Partial** | Dimensions 1–2 (tech foundation, data management) are well-represented through System, Integration, DataAsset, DataDomain, Control. Dimension 3 (unlocking value) is partially represented through BusinessCapability and Initiative. Dimension 4 (fluency) has no representation. |
| Ferrari vs. Cargo Ship (quick wins vs. structural programs) | **Gap** | No way to classify initiatives as quick-win vs. structural. Initiative entity has no lifecycle stage, effort estimate, or time-to-value classification. |
| CFO-certifiable value vs. "bullshit value" | **Gap** | No financial validation structure. No way to distinguish demonstrated value from projected value from aspirational value. |
| 70/30 rule (70% business process, 30% tech) | **N/A** | This is a principle, not a structural concept. Noted for roadmap framing — the platform is the 30%, not the 70%. |
| Minimum Viable Bureaucracy for governance | **Strong** | The platform's governance layer (Policy, Regulation, Control, Risk) is designed for rapid evaluation, not exhaustive compliance. This aligns with Cheriath's principle of right-sizing governance to organizational maturity. |
| Data custodianship (position, not person) | **Strong** | DataDomain.domain_owner and domain_steward reference Role entities, not Person entities. The abstraction is correct — custodianship belongs to the position. |
| DAI Decision Framework | **Gap** | No structured representation of Decision owner, Advice givers, Informed. Person and Role exist but lack decision-rights assignment. |
| Systems of Record / Insight / Enablement | **Partial** | System has system_type but no explicit classification into Cheriath's three-system taxonomy. Representable through system_type values but not enforced or guided. |
| Risk of under-innovation | **Strong** | blast_radius(), find_vendor_dependencies(), and centrality analysis directly enable the dependency risk analysis Cheriath described. If a platform is untouchable due to technical debt, the blast radius shows what else stays frozen. |
| Partnership model (CDAIO owns 30%) | **Partial** | Vendor and Contract entities model external partnerships. But the internal partnership model — which systems/capabilities are owned by CDAIO vs. IT vs. business units — is not explicitly represented. |

**Module 2 summary:** Strong as a digital blueprint and dependency analysis tool. Gaps in value measurement, initiative classification, and the strategic/financial layer that separates a CDAIO from a CDO.

---

### Module 3: Data Platform Architecture
**Instructor:** [Module 3 Instructor]

| Concept | Alignment | Platform Representation |
|---------|-----------|----------------------|
| Medallion Architecture (Bronze/Silver/Gold) | **Partial** | DataAsset has classification and data_type but no explicit tier/zone concept for processing stages. Representable through naming conventions but not structurally enforced. |
| Data Mesh (Dehghani's 4 principles) | **Partial** | DataDomain models domain ownership. DataAsset models individual assets. But the data-as-a-product concept — published APIs, consumer contracts, SLAs — is not structurally present. |
| Data Fabric | **Partial** | Integration entity tracks system-to-system data movement. But the unified metadata layer that defines a fabric is implicit, not explicit. |
| Semantic layer | **Gap** | No entity type for semantic models, business glossaries, or shared definitions. DataDomain has business_glossary_reference but it is a URL pointer, not a structural model. |
| Data lineage | **Strong** | DataFlow tracks source_system, target_system, transformations, frequency, sensitivity, and jurisdiction crossing. The lineage chain is traversable. |
| Knowledge graphs | **Strong** | The platform is a knowledge graph. This is direct alignment. |
| AI-ready data criteria | **Gap** | No representation of data readiness for AI/ML consumption — no bias assessment, representativeness score, labeling quality, or training/validation split metadata. |
| Data observability (5 pillars) | **Partial** | Quality scoring covers some pillars (freshness via temporal, volume via entity counts). But no dedicated observability model for schema change detection, distribution drift, or lineage breakage alerts. |
| Federated governance | **Strong** | The layered entity model with per-domain ownership (DataDomain.domain_owner, DataDomain.domain_steward) and per-type governance (Policy.applies_to_entity_types) supports federated governance by design. |

**Module 3 summary:** Strong on lineage, federated governance, and knowledge graph structure. Gaps in semantic layer modeling, data product concepts, and AI-readiness metadata.

---

### Module 4: Maturity Assessment & Data Culture
**Instructors:** Doug Laney and Karan DeWal

| Concept | Alignment | Platform Representation |
|---------|-----------|----------------------|
| 8-dimension maturity model | **Strong** | DataDomain.maturity_dimensions + BusinessCapability.maturity provide structural representation. Radar/spider chart output is supported via the quality radar chart type. |
| DCAM as industry standard | **Strong** | DataDomain.maturity_dimensions explicitly reference DCAM 2.2 dimensions with scored assessments. |
| Data as enterprise asset (Infonomics) | **Partial** | DataAsset exists as an entity type. But the Infonomics properties Laney described — non-rivalrous, non-depleting, self-generative — are not represented. No economic valuation model for data assets. |
| VECTOR framework (culture assessment) | **Gap** | No entity type for culture metrics, survey results, or organizational readiness scores. The 5 pillars and 320 questions have no structural representation. |
| Decision traceability | **Gap** | Entity provenance tracks who assessed what and when. But decision chains — why a particular classification was chosen, what alternatives were considered, who approved — are not modeled. |
| New data types from AI | **Gap** | Decision traces, vector embeddings, synthetic data, agent interaction logs — none have entity types. The platform models traditional enterprise data but not AI-generated data artifacts. |
| Non-human identity management | **Gap** | No entity type for AI agents, service accounts, or automated actors as first-class identities. Person is human-only. |
| Governance as enablement | **Strong** | The platform's governance layer exists to make risk and compliance traversable, not to enforce bureaucracy. Policy → Control → Risk chains enable understanding, not obstruction. Aligned with Laney's framing. |
| Hub-and-spoke / franchise / federated org models | **Partial** | OrganizationalUnit and Department support hierarchical and matrix structures. But the three governance operating models Laney described are not explicitly classified or selectable. |

**Module 4 summary:** Strong on maturity assessment infrastructure. Significant gaps in culture measurement, decision traceability, AI-era data types, and data valuation.

---

### Module 5: Analytics & AI in Practice
**Instructor:** Craig [Last Name]

| Concept | Alignment | Platform Representation |
|---------|-----------|----------------------|
| Analytics continuum (descriptive → prescriptive) | **Partial** | The analysis module provides descriptive (centrality, statistics) and diagnostic (blast radius, attack paths) capabilities. Predictive and prescriptive analytics are not built in — the platform provides data for them, not the analytics themselves. |
| Decision intelligence (3 stages) | **Gap** | No representation of human-machine decision interaction stages. The platform models the enterprise, not the decision-making process applied to it. |
| Four Ps (Problem → POC → Pilot → Production) | **Gap** | Initiative entity has no lifecycle stage field. No stage-gate concept, no success criteria per stage, no funding gates. Cannot model "this initiative is in POC and awaiting pilot approval." |
| Value measurement (operational, customer, economic, strategic) | **Gap** | No value taxonomy. No entity type for measured outcomes, benefit realization, or value attribution. This is the single most-emphasized gap across all modules. |
| Data/AI literacy (5 levels) | **Gap** | No entity type for organizational fluency assessment, training programs, or competency tracking. |
| Go-and-see / Gemba observation | **N/A** | Operational practice, not a structural concept. |
| POC vs. Pilot differentiation | **Gap** | Subsumed by the Four Ps gap above. |
| Finance as referee for value claims | **Gap** | No validation layer for distinguishing demonstrated vs. projected vs. aspirational value. Subsumed by the value measurement gap. |
| Adoption-first strategy | **N/A** | Design principle, not a structural concept. Noted for roadmap prioritization. |
| Data ethics as trust currency | **Gap** | No entity type for ethical review records, appropriate use policies, or trust metrics. |

**Module 5 summary:** The platform provides the enterprise model that analytics operates on, but does not model the analytics/AI lifecycle itself. Gaps in value measurement, initiative lifecycle, fluency, and ethics are consistent and significant.

---

## Gap Summary

Ranked by frequency of emphasis across modules and practical impact on rapid evaluation use cases:

| Gap | Modules | Impact on Rapid Evaluation |
|-----|---------|---------------------------|
| **Value measurement / ROI tracking** | 1, 2, 5 | High — cannot answer "is this worth doing?" without financial structure |
| **Initiative lifecycle (POC → Production)** | 2, 5 | High — cannot track whether strategic actions are progressing |
| **Data/AI fluency and readiness** | 2, 4, 5 | Medium — important for strategy but not for structural modeling |
| **Decision traceability** | 4 | Medium — important for governance maturity but can be deferred |
| **Semantic layer / data products** | 3 | Medium — important for data mesh orgs, less so for rapid evaluation |
| **AI model governance** | 3, 4 | Medium — increasingly important but tangential to enterprise structure |
| **Data valuation (Infonomics)** | 4 | Low-Medium — strategic concept, hard to operationalize in rapid eval |
| **Culture / VECTOR metrics** | 4, 5 | Low — inherently hard to model; indicators are more practical |
| **Non-human identity** | 4 | Low — emerging concern, not yet standard |
| **Data ethics records** | 5 | Low — important but better served by policy tooling than graph modeling |

---

## What the Platform Gets Right

This section exists because it matters. The platform was not designed against the CDAIO curriculum, yet it structurally represents the majority of Module 1–3 concepts — governance mechanisms, data lifecycle, quality dimensions, maturity modeling, dependency mapping, compliance traceability, and the digital blueprint concept that Cheriath identified as the single most neglected artifact in enterprise data leadership.

The blast radius and attack path analysis capabilities directly enable the kind of "what breaks if this changes" thinking that every module emphasized. The MCP server integration — making the graph queryable from Claude Desktop in natural language — converts a static model into an interactive analytical tool. That is closer to the "system of insight" concept (Module 2) than most purpose-built analytics platforms achieve.

The provenance model (source, assessed_by, confidence, last_assessed_date) on every entity implements the evidence chain discipline that Dr. Steyer taught in Module 1 and that underpins the entire CDAIO program's emphasis on epistemic rigor.

The platform's rapid-evaluation design philosophy aligns naturally with Cheriath's "minimum viable bureaucracy" principle and Craig's "adoption-first" approach. It does not try to be all things. It tries to surface understanding fast enough to inform strategy.

---

## Recommendations

See [docs/cdaio-roadmap.md](cdaio-roadmap.md) for the incremental implementation plan addressing these gaps.
