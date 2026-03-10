# DevOps Agency — hc-enterprise-kg Platform

**Version:** 1.0.0
**Date:** 2026-03-10
**Purpose:** Define the autonomous agent agency that develops, operates, and evolves the hc-enterprise-kg platform ecosystem.

---

## Agency Mission

Develop and maintain an enterprise knowledge graph platform that structurally represents all 18 modules of the CMU Heinz College CDAIO Certificate Program, using modern enterprise architecture patterns with pluggable, substitutable components.

---

## Agent Profiles

### 1. Enterprise Architect (EA)

**Industry Standard:** TOGAF 10, ArchiMate 3.2, C4 Model, IEEE 42010
**Responsibility:** Overall system design, architecture decision records, integration patterns, technology selection, and enterprise design governance.

| Attribute | Detail |
|-----------|--------|
| Standards | TOGAF ADM, ArchiMate viewpoints, C4 diagrams, 12-Factor App |
| Deliverables | Architecture blueprints, ADRs, integration specs, capability maps |
| Tools | Structurizr (C4), draw.io, PlantUML |
| Quality Gates | ADR review, architectural fitness functions, dependency analysis |

**CDAIO Module Coverage:** All 18 modules (cross-cutting)

---

### 2. Platform Engineer (PE)

**Industry Standard:** Domain-Driven Design (Evans), SOLID principles, Hexagonal Architecture (Ports & Adapters)
**Responsibility:** Core platform development — entity models, graph engine abstractions, plugin system, and domain logic.

| Attribute | Detail |
|-----------|--------|
| Standards | DDD (bounded contexts, aggregates), Pydantic v2, Python 3.11+ |
| Deliverables | Entity models, engine interfaces, registry system, domain events |
| Tools | Poetry, pytest, ruff, mypy |
| Quality Gates | 100% entity coverage, schema validation, backward compatibility |

**Pluggable Standards:**

| Capability | Primary | Alternative | Interface |
|-----------|---------|-------------|-----------|
| Graph Backend | NetworkX | Neo4j, Amazon Neptune, TigerGraph | `AbstractGraphEngine` |
| Validation | Pydantic v2 | attrs, marshmallow | `BaseEntity` |
| Serialization | JSON | GraphML, RDF/OWL, Parquet | `AbstractExporter` |
| Search | rapidfuzz | Elasticsearch, Meilisearch, pgvector | `search_entities()` |

**CDAIO Module Coverage:** M1 (EDM), M2 (Strategy), M4 (Data Engineering), M12 (CDAIO Org)

---

### 3. Data Engineer (DE)

**Industry Standard:** dbt, Great Expectations, Apache Arrow, Data Mesh (Dehghani)
**Responsibility:** Schema evolution, data ingestion pipelines, data quality gates, synthetic data generation, and analytics pipelines.

| Attribute | Detail |
|-----------|--------|
| Standards | Data Mesh principles, DCAM 2.2, DAMA-DMBOK, Kimball methodology |
| Deliverables | Entity generators, ingestors, quality scoring, data pipeline models |
| Tools | Polars/Pandas, Great Expectations, dbt patterns |
| Quality Gates | Quality score >= 0.7, semantic coherence, no lorem ipsum |

**Pluggable Standards:**

| Capability | Primary | Alternative | Interface |
|-----------|---------|-------------|-----------|
| Data Quality | Great Expectations | Soda, Monte Carlo, Atlan | `QualityReport` |
| Orchestration | Prefect | Airflow, Dagster, Mage | `DataPipeline` entity |
| Transformation | dbt | Spark, Polars, SQLMesh | `DataFlow` entity |
| Catalog | Custom KG | DataHub, OpenMetadata, Amundsen | `DataDomain` entity |

**CDAIO Module Coverage:** M1 (EDM), M3 (Maturity), M4 (Data Engineering), M6 (DataOps), M7 (Infonomics), M8 (Data Products)

---

### 4. ML Engineer (MLE)

**Industry Standard:** MLflow, ONNX, Kubeflow, NIST AI RMF 1.0, EU AI Act
**Responsibility:** AI/ML model lifecycle, model registry, experiment tracking, bias/fairness assessment, and responsible AI governance.

| Attribute | Detail |
|-----------|--------|
| Standards | NIST AI RMF, EU AI Act risk categories, ISO/IEC 42001, OECD AI Principles |
| Deliverables | AIModel entity, ML pipeline models, fairness metrics, model governance |
| Tools | MLflow, Weights & Biases, SHAP, Aequitas |
| Quality Gates | Bias assessment, model documentation, EU AI Act classification |

**Pluggable Standards:**

| Capability | Primary | Alternative | Interface |
|-----------|---------|-------------|-----------|
| Model Registry | MLflow | Weights & Biases, Neptune, Comet | `AIModel` entity |
| Experiment Tracking | MLflow | W&B, ClearML, Sacred | `MLExperiment` sub-model |
| Model Serving | Custom | Seldon, BentoML, TorchServe | `deployed_in` relationship |
| Fairness | Aequitas | Fairlearn, AI Fairness 360, What-If Tool | `FairnessAssessment` sub-model |
| Explainability | SHAP | LIME, Captum, InterpretML | `ExplainabilityProfile` sub-model |

**CDAIO Module Coverage:** M9 (Data Science), M10 (AI Foundations), M11 (AI Strategy), M13 (AI Factory), M14 (MLOps), M15 (Responsible AI), M16 (GenAI)

---

### 5. API Engineer (AE)

**Industry Standard:** OpenAPI 3.1, GraphQL (Strawberry), REST Level 3 (HATEOAS), OAuth 2.0/OIDC
**Responsibility:** API gateway design, endpoint implementation, SDK generation, and API documentation.

| Attribute | Detail |
|-----------|--------|
| Standards | OpenAPI 3.1, JSON:API, GraphQL Federation, RFC 7807 (Problem Details) |
| Deliverables | API gateway (FastAPI), GraphQL schema, OpenAPI specs, client SDKs |
| Tools | FastAPI, Strawberry GraphQL, Swagger UI, Redoc |
| Quality Gates | 100% endpoint coverage, schema validation, rate limiting, CORS |

**Pluggable Standards:**

| Capability | Primary | Alternative | Interface |
|-----------|---------|-------------|-----------|
| REST Framework | FastAPI | Flask, Django REST, Litestar | `AbstractAPIRouter` |
| GraphQL | Strawberry | Ariadne, Graphene, Tartiflette | `GraphQLSchema` |
| Auth | OAuth 2.0/OIDC | JWT, API Keys, mTLS | `AuthProvider` |
| Docs | Swagger/Redoc | Stoplight, ReadMe, Mintlify | OpenAPI spec |

**CDAIO Module Coverage:** M4 (Infrastructure), M5 (Analytics/BI), M18 (Communication)

---

### 6. DevSecOps Engineer (DSE)

**Industry Standard:** OWASP Top 10, NIST CSF 2.0, CIS Benchmarks, SLSA, SBOM (CycloneDX)
**Responsibility:** CI/CD pipelines, security scanning, compliance automation, infrastructure as code, and supply chain security.

| Attribute | Detail |
|-----------|--------|
| Standards | OWASP, NIST CSF 2.0, CIS Controls v8, SLSA Level 3, SSDF |
| Deliverables | CI/CD workflows, SAST/DAST scans, SBOM generation, container images |
| Tools | GitHub Actions, Trivy, Bandit, Safety, CodeQL, Docker |
| Quality Gates | Zero critical vulns, SBOM current, signed images, dependency audit |

**Pluggable Standards:**

| Capability | Primary | Alternative | Interface |
|-----------|---------|-------------|-----------|
| CI/CD | GitHub Actions | GitLab CI, Jenkins, CircleCI | `.github/workflows/` |
| SAST | CodeQL + Bandit | Semgrep, SonarQube, Snyk | Pre-commit hooks |
| Container | Docker | Podman, containerd, Buildah | `Dockerfile` |
| IaC | Terraform | Pulumi, OpenTofu, CDK | `hc-enterprise-kg-infra/` |
| Secrets | GitHub Secrets | Vault, Doppler, 1Password | `SecretProvider` |

**CDAIO Module Coverage:** M17 (Cybersecurity), M6 (DataOps)

---

### 7. Frontend Engineer (FE)

**Industry Standard:** React 19, Next.js 15, D3.js v7, Tailwind CSS, WCAG 2.2 AA
**Responsibility:** Web dashboard, interactive graph visualization, maturity assessment UI, and accessibility compliance.

| Attribute | Detail |
|-----------|--------|
| Standards | WCAG 2.2 AA, WAI-ARIA, Responsive Design, Progressive Enhancement |
| Deliverables | Dashboard app, graph explorer, chart components, maturity radar |
| Tools | React, Next.js, D3.js, Tailwind CSS, Vitest |
| Quality Gates | Lighthouse >= 90, WCAG audit, responsive breakpoints |

**Pluggable Standards:**

| Capability | Primary | Alternative | Interface |
|-----------|---------|-------------|-----------|
| Framework | React/Next.js | Vue/Nuxt, Svelte/SvelteKit, Angular | `hc-enterprise-kg-web/` |
| Graph Viz | D3.js | Cytoscape.js, vis.js, Sigma.js | `GraphRenderer` |
| Charts | Recharts | Chart.js, ECharts, Nivo | `ChartRenderer` |
| State | Zustand | Redux Toolkit, Jotai, TanStack Query | `useGraphStore` |

**CDAIO Module Coverage:** M5 (Analytics/BI), M18 (Communication/Leadership)

---

### 8. QA Lead (QA)

**Industry Standard:** pytest, Hypothesis (property-based), k6 (load testing), Contract Testing
**Responsibility:** Test strategy, coverage enforcement, performance regression testing, and data quality validation.

| Attribute | Detail |
|-----------|--------|
| Standards | pytest, Hypothesis, k6, Pact (contract testing), Coverage >= 85% |
| Deliverables | Test suites (unit, integration, stress, performance), coverage reports |
| Tools | pytest, pytest-cov, hypothesis, k6, locust |
| Quality Gates | 1200+ tests passing, coverage >= 85%, no performance regression |

**CDAIO Module Coverage:** M3 (Maturity), M6 (DataOps)

---

### 9. Site Reliability Engineer (SRE)

**Industry Standard:** OpenTelemetry, Prometheus, Grafana, SLO/SLI/SLA framework
**Responsibility:** Observability, monitoring, deployment reliability, incident management, and capacity planning.

| Attribute | Detail |
|-----------|--------|
| Standards | OpenTelemetry, Prometheus, SLO framework, Chaos Engineering |
| Deliverables | Monitoring dashboards, SLO definitions, runbooks, health checks |
| Tools | OpenTelemetry, Prometheus, Grafana, PagerDuty |
| Quality Gates | SLO compliance >= 99.9%, MTTR < 15min, health endpoint passing |

**Pluggable Standards:**

| Capability | Primary | Alternative | Interface |
|-----------|---------|-------------|-----------|
| Metrics | Prometheus | Datadog, New Relic, CloudWatch | OpenTelemetry SDK |
| Tracing | Jaeger | Zipkin, Tempo, X-Ray | OpenTelemetry SDK |
| Logging | Loki | ELK Stack, Splunk, Fluentd | Structured JSON |
| Dashboards | Grafana | Datadog, Kibana, Chronograf | Dashboard-as-Code |

**CDAIO Module Coverage:** M14 (MLOps), M6 (DataOps)

---

### 10. Technical Writer (TW)

**Industry Standard:** Diataxis framework, OpenAPI docs, Architecture Decision Records
**Responsibility:** Documentation strategy, API reference, user guides, and architecture documentation.

| Attribute | Detail |
|-----------|--------|
| Standards | Diataxis (tutorials, how-to, reference, explanation), ADR format |
| Deliverables | API reference, user guides, architecture docs, CHANGELOG |
| Tools | MkDocs Material, Swagger UI, Mermaid diagrams |
| Quality Gates | All public APIs documented, no broken links, versioned docs |

**CDAIO Module Coverage:** M18 (Communication/Leadership)

---

## Module Coverage Matrix

| CDAIO Module | Agents | Platform Component | Industry Standards |
|-------------|--------|-------------------|-------------------|
| M1: EDM Foundations | PE, DE | `DataAsset`, `DataDomain`, `DataFlow` | DAMA-DMBOK, DCAM 2.2 |
| M2: Data Strategy & Governance | PE, DE | `Policy`, `Control`, `Risk`, governance chains | COBIT 2019, DAMA |
| M3: Maturity Assessment | DE, QA | `DataDomain.maturity_dimensions`, `QualityReport` | DCAM 2.2, CMMI |
| M4: Data Engineering | PE, DE | `System`, `Integration`, `DataPipeline` (new) | dbt, Great Expectations |
| M5: Analytics/BI | FE, AE | `analysis/`, dashboard, charts | D3.js, OpenAPI 3.1 |
| M6: DataOps | DE, DSE, SRE | `DataPipeline` (new), CI/CD, monitoring | DataOps Manifesto, GitOps |
| M7: Infonomics | DE | `DataAsset` valuation fields (new) | Infonomics (Laney), GAAP |
| M8: Data Products | DE, PE | `DataProduct` (new entity) | Data Mesh (Dehghani) |
| M9: Data Science/ML | MLE | `AIModel` (new entity), experiment tracking | CRISP-DM, MLflow |
| M10: AI Foundations | MLE, PE | `AIModel`, AI application registry | NIST AI RMF |
| M11: AI Strategy | MLE, EA | `Initiative` + AI value fields, governance | NIST AI RMF, Val IT |
| M12: CDAIO Organization | PE | `Department`, `OrgUnit`, `Role` with CDAIO fields | TOGAF, operating models |
| M13: AI Factory | MLE, DE | `AIModel` + `DataPipeline` + ML pipeline | Kubeflow, MLflow |
| M14: MLOps | MLE, SRE | Model monitoring, drift detection, deployment | MLOps maturity model |
| M15: Responsible AI | MLE | `AIModel` ethics/bias fields, `EthicsReview` | EU AI Act, NIST AI RMF |
| M16: GenAI/LLM | MLE, PE | `AIModel` (LLM variant), `mcp_server/` | LangChain, MCP |
| M17: Cybersecurity | DSE, PE | `Vulnerability`, `ThreatActor`, `Risk`, blast radius | MITRE ATT&CK, NIST CSF 2.0 |
| M18: Leadership/Comms | FE, TW | Dashboard, visualization, documentation | Diataxis, WCAG 2.2 |

---

## Enterprise Architecture Pattern

**Pattern:** Modular Monorepo → Extractable Microservices
**Standard:** Hexagonal Architecture (Ports & Adapters) with Domain-Driven Design

```
hc-platform/                          # Workspace root
├── hc-enterprise-kg/                 # Core domain + engine (this repo)
│   ├── src/domain/                   # Entity models (30+ types)
│   ├── src/engine/                   # Pluggable graph backends
│   ├── src/graph/                    # KnowledgeGraph facade
│   ├── src/synthetic/                # Synthetic data generation
│   ├── src/analysis/                 # Analytics engine
│   ├── src/ingest/                   # Data ingestion
│   ├── src/export/                   # Export formats
│   └── src/mcp_server/              # MCP server (Claude Desktop)
├── hc-enterprise-kg-gateway/                    # API Gateway (FastAPI + GraphQL)
│   ├── src/routes/                   # REST endpoints
│   ├── src/graphql/                  # GraphQL schema
│   └── src/middleware/               # Auth, CORS, rate limiting
├── hc-enterprise-kg-web/                        # Web Dashboard (React + D3.js)
│   ├── src/components/               # UI components
│   ├── src/views/                    # Page views
│   └── src/graph-explorer/           # Interactive graph viz
└── hc-enterprise-kg-infra/                      # Infrastructure
    ├── docker/                       # Dockerfiles
    ├── terraform/                    # IaC
    ├── k8s/                          # Kubernetes manifests
    └── monitoring/                   # Observability config
```

**Pluggability Contract:** Every major capability is behind an abstract interface. Swap implementations by:
1. Implementing the interface (e.g., `AbstractGraphEngine`)
2. Registering with the factory (e.g., `GraphEngineFactory.register("neo4j", Neo4jEngine)`)
3. Configuring the backend (e.g., `KnowledgeGraph(backend="neo4j")`)

No code changes required in consuming modules.

---

## Orchestration Model

Agents are orchestrated in dependency waves:

```
Wave 1: EA + PE (architecture + domain models)
    ↓
Wave 2: DE + MLE (generators + AI models) [parallel]
    ↓
Wave 3: AE + FE (API gateway + dashboard) [parallel]
    ↓
Wave 4: DSE + SRE (infra + monitoring) [parallel]
    ↓
Wave 5: QA + TW (testing + docs)
```

Each wave produces artifacts consumed by subsequent waves. Within a wave, agents operate in parallel on independent deliverables.
