# Enterprise Architecture Blueprint

**Version:** 1.0.0
**Date:** 2026-03-10
**Pattern:** Modular Monorepo with Extractable Services
**Standard:** Hexagonal Architecture (Ports & Adapters), Domain-Driven Design

---

## Design Philosophy

This platform is a **knowledge graph for CDAIO insight** — not a technology execution platform. It models what a Chief Data & AI Officer needs to understand: organizational structure, data assets, AI models, data pipelines, governance posture, risk exposure, and strategic initiatives. The entities and their relationships ARE the product. Every module in the CMU CDAIO program is addressed by making the graph queryable for the questions a data leader asks.

---

## System Topology

```
┌─────────────────────────────────────────────────────────────┐
│                     hc-platform (workspace)                  │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌──────────────────────┐    ┌──────────────────────┐       │
│  │  hc-enterprise-kg    │    │  hc-enterprise-kg-gateway       │       │
│  │  (Core Domain)       │◄───│  (API Gateway)       │       │
│  │                      │    │  FastAPI + GraphQL    │       │
│  │  33 entity types     │    │  OpenAPI 3.1          │       │
│  │  66 relationship     │    └──────────────────────┘       │
│  │  types               │                                    │
│  │  Pluggable engine    │    ┌──────────────────────┐       │
│  │  MCP server          │    │  hc-enterprise-kg-web           │       │
│  └──────────┬───────────┘    │  (Dashboard)         │       │
│             │                │  React + D3.js       │       │
│             │                │  Next.js             │       │
│             ▼                └──────────────────────┘       │
│  ┌──────────────────────┐                                    │
│  │  hc-enterprise-kg-infra         │    Industry Standards:             │
│  │  (Infrastructure)    │    ● Docker / Kubernetes           │
│  │  Docker Compose      │    ● Terraform / OpenTofu          │
│  │  K8s manifests       │    ● Prometheus / Grafana          │
│  │  Terraform           │    ● OpenTelemetry                 │
│  │  Monitoring          │    ● OWASP / NIST CSF 2.0         │
│  └──────────────────────┘                                    │
└─────────────────────────────────────────────────────────────┘
```

---

## Pluggable Capability Matrix

Every major capability is behind an abstract interface. Swap implementations without changing consuming code.

| Capability | Interface | Primary | Alternatives | Standard |
|-----------|-----------|---------|-------------|----------|
| **Graph Backend** | `AbstractGraphEngine` | NetworkX | Neo4j, Amazon Neptune, TigerGraph | IEEE Graph DB |
| **Entity Validation** | `BaseEntity` (Pydantic v2) | Pydantic | attrs, marshmallow | JSON Schema |
| **Serialization** | `AbstractExporter` | JSON | GraphML, RDF/OWL, Parquet | JSON-LD, W3C |
| **Fuzzy Search** | `search_entities()` | rapidfuzz | Elasticsearch, pgvector | BM25, ANN |
| **AI Interface** | MCP Server | Claude Desktop | Any MCP client | Model Context Protocol |
| **REST API** | FastAPI Router | FastAPI | Flask, Litestar | OpenAPI 3.1 |
| **GraphQL** | Strawberry Schema | Strawberry | Ariadne, Graphene | GraphQL Spec |
| **Visualization** | D3.js Components | D3.js | Cytoscape.js, Sigma.js | SVG/Canvas |
| **Auth** | Middleware | OAuth 2.0/OIDC | JWT, API Keys, mTLS | RFC 6749 |
| **Monitoring** | OpenTelemetry | Prometheus | Datadog, New Relic | OTLP |
| **IaC** | Terraform | Terraform | Pulumi, OpenTofu, CDK | HCL |
| **Container** | Dockerfile | Docker | Podman, containerd | OCI |
| **Orchestration** | K8s manifests | Kubernetes | Docker Swarm, ECS | CNCF |
| **Data Quality** | `QualityReport` | Custom scoring | Great Expectations, Soda | DCAM 2.2 |

---

## Repository Structure

### hc-enterprise-kg (Core Domain) — This repo

The knowledge graph engine, entity models, synthetic generation, analysis, and MCP server.

```
src/
  domain/           33 Pydantic v2 entity models, 66 relationship types
    entities/        ai_model.py, data_product.py, data_pipeline.py (new)
    base.py          EntityType + RelationshipType enums
    registry.py      EntityRegistry (plugin discovery)
    relationship_schema.py  Domain/range constraints
    shared.py        Reusable sub-models
  engine/           Pluggable graph backend
    abstract.py      AbstractGraphEngine (swap NetworkX for Neo4j)
    networkx_engine.py
    factory.py       GraphEngineFactory.register("neo4j", Neo4jEngine)
  graph/            KnowledgeGraph facade, event bus, QueryBuilder
  synthetic/        Profile-driven generation (tech, financial, healthcare)
    generators/      30 v0.1 + 3 CDAIO generators
    profiles/        Industry-specific scaling coefficients
    relationships.py 33+ weaver methods including CDAIO relationships
  analysis/         Centrality, risk scoring, blast radius, charts
  mcp_server/       16 tools for Claude Desktop (read + write + provenance)
  ingest/           CSV/JSON ingestion with schema mapping
  export/           JSON + GraphML export
  rag/              GraphRAG retrieval pipeline
  cli/              Click CLI (demo, generate, inspect, auto, serve, install)
  serve/            REST API (Flask)
```

### hc-enterprise-kg-gateway (API Gateway)

FastAPI + Strawberry GraphQL gateway exposing the knowledge graph via REST and GraphQL.

```
hc-enterprise-kg-gateway/
  src/
    main.py           FastAPI app, CORS, router mounting
    config.py          pydantic-settings configuration
    routes/            REST endpoints (entities, relationships, analysis, health)
    graphql/           Strawberry schema + resolvers
    middleware/         OAuth 2.0 auth middleware
  Dockerfile
```

### hc-enterprise-kg-web (Dashboard)

React + Next.js + D3.js interactive dashboard for CDAIO insight.

```
hc-enterprise-kg-web/
  src/
    app/               Next.js App Router pages
      entities/         Entity explorer
      graph/            Force-directed graph visualization
      maturity/         Maturity radar chart
      ai-models/        AI model registry view
    components/         GraphExplorer, EntityTable, MaturityRadar, Sidebar
    lib/                API client, TypeScript types
```

### hc-enterprise-kg-infra (Infrastructure)

Docker Compose, Kubernetes, Terraform, and monitoring configuration.

```
hc-enterprise-kg-infra/
  docker/              docker-compose.yml (6 services), Dockerfiles
  k8s/                 Namespace, deployments, services
  terraform/           Provider config, variables, modules
  monitoring/          Prometheus scrape config, Grafana dashboards
  .github/workflows/   CI pipeline
```

---

## CDAIO Module Coverage — 18/18

| # | CDAIO Module | How the KG Addresses It |
|---|-------------|------------------------|
| 1 | **EDM Foundations** | `DataAsset`, `DataDomain`, `DataFlow` + governance chains (`Policy` → `Control` → `Risk`). Quality dimensions, lifecycle, classification, retention. |
| 2 | **Data Strategy & Governance** | `Initiative` with `value_category`, `lifecycle_stage`, `value_confidence`. Decision rights on `Role`. Governance traversal via `governs`, `implements`, `subject_to`. |
| 3 | **Maturity Assessment** | `DataDomain.maturity_dimensions` (DCAM 2.2). `BusinessCapability.maturity`. `Department.data_fluency_level`. Quality radar charts. |
| 4 | **Data Engineering** | `DataPipeline` entity — pipeline type, orchestration platform, medallion/lambda/kappa patterns, source/target lineage, execution profiles. `ORCHESTRATES`, `CONSUMES`, `PRODUCES` relationships. |
| 5 | **Analytics/BI** | Analysis module (centrality, PageRank, blast radius). Charts module (8 chart types). Dashboard scaffold (hc-enterprise-kg-web) with D3.js. |
| 6 | **DataOps** | `DataPipeline` with CI/CD fields (`version_controlled`, `ci_cd_enabled`, `test_coverage_pct`), quality framework integration, SLA tracking, observability flags. |
| 7 | **Infonomics** | `DataAsset` with `economic_value_method` (cost/market/income/utility), `estimated_economic_value`, `monetization_status`. `DataProduct` with `estimated_annual_value`, `cost_to_produce`, `margin_pct`. |
| 8 | **Data Products** | `DataProduct` entity — ownership, SLA, FAIR compliance scores, quality contracts, consumer tracking, monetization status, access protocols. `PUBLISHES`, `BELONGS_TO` relationships. |
| 9 | **Data Science/ML** | `AIModel` entity — training data lineage (`TRAINED_ON`), performance metrics, validation methodology, hyperparameters. |
| 10 | **AI Foundations** | `AIModel` with model type taxonomy (classification, regression, NLP, generative, etc.), framework tracking (pytorch, tensorflow, huggingface), deployment status. |
| 11 | **AI Strategy** | `Initiative` with `data_ai_alignment`. `AIModel` with `projected_annual_value`, `value_confidence`. `CREATES_VALUE_FOR` relationship linking initiatives to business capabilities. |
| 12 | **CDAIO Organization** | `Department` and `OrgUnit` with `data_fluency_level`, `data_culture_score`, `ai_readiness_tier`. `Role` with `cdaio_function`, `decision_domains`, `decision_authority`. |
| 13 | **AI Factory** | `AIModel` + `DataPipeline` together model the AI factory — training pipelines (`CONSUMES` data, `PRODUCES` models), serving infrastructure, compute profiles. |
| 14 | **MLOps** | `AIModel` with `deployment_status`, `drift_detection_enabled`, `drift_status`, `model_health`, `monitoring_enabled`, `rollback_version`. `DEPLOYED_IN` relationship to systems. |
| 15 | **Responsible AI** | `AIModel` with `eu_ai_act_risk_category`, `nist_ai_rmf_profile`, `fairness_metrics`, `bias_assessment_completed`, `ethics_review_status`, `human_oversight_required`, `explainability_method`. |
| 16 | **GenAI/LLM** | `AIModel` with `is_generative`, `base_model_provider` (openai, anthropic, etc.), `context_window_tokens`, `fine_tuning_method`, `guardrails_enabled`, `guardrail_types`. MCP server for Claude Desktop. |
| 17 | **Cybersecurity** | `Vulnerability`, `ThreatActor`, `Incident`, `Risk`, `Threat`. Blast radius analysis, attack path finding, centrality scoring. `EXPLOITS`, `TARGETS`, `MITIGATES`, `AFFECTS` relationships. |
| 18 | **Leadership/Comms** | Dashboard (hc-enterprise-kg-web), interactive visualization (`hckg visualize`), quality radar charts, MCP natural-language querying. The graph IS the communication artifact. |

---

## CDAIO Insight Queries Enabled

The relationship graph enables these CDAIO questions through traversal:

**Strategy & Value:**
- "Which initiatives have demonstrated value over $1M?" → Initiative.value_confidence + expected_outcomes
- "What's stuck in POC?" → Initiative.lifecycle_stage == "poc"
- "Which quick wins can show value in 3 months?" → Initiative.initiative_nature + time_to_value

**Data Architecture:**
- "How many data assets are published as products?" → DataProduct count vs DataAsset count
- "Which data products lack SLAs?" → DataProduct.data_product_sla == None
- "What's our FAIR compliance?" → DataProduct.findable_score, accessible_score, etc.

**AI/ML Governance:**
- "Which AI models are high-risk under EU AI Act?" → AIModel.eu_ai_act_risk_category == "high"
- "Which models lack bias assessment?" → AIModel.bias_assessment_completed == False
- "What data feeds our fraud detection model?" → TRAINED_ON traversal
- "Which systems host production AI models?" → DEPLOYED_IN traversal

**DataOps Health:**
- "Which pipelines are failing SLAs?" → DataPipeline.sla_breach_count_30d > 0
- "What's our CI/CD coverage for data pipelines?" → DataPipeline.ci_cd_enabled
- "Which pipelines feed our data products?" → PUBLISHES traversal

**Organizational Readiness:**
- "Which departments have low data fluency?" → Department.data_fluency_level < 3
- "Who has decision authority over data classification?" → Role.decision_domains + decision_authority
- "What's the blast radius if this vendor fails?" → blast_radius(vendor_id)

---

## Domain Model Summary

**33 Entity Types** across 12+ generation layers:
- v0.1 (12): Person, Department, Role, System, Network, DataAsset, Policy, Vendor, Location, Vulnerability, ThreatActor, Incident
- Enterprise (18): Regulation, Control, Risk, Threat, Integration, DataDomain, DataFlow, OrganizationalUnit, BusinessCapability, Site, Geography, Jurisdiction, ProductPortfolio, Product, MarketSegment, Customer, Contract, Initiative
- CDAIO (3): **AIModel**, **DataProduct**, **DataPipeline**

**66 Relationship Types** including 8 new CDAIO types:
- `trained_on` — AIModel → DataAsset/DataProduct
- `deployed_in` — AIModel → System
- `produces` — DataPipeline/AIModel → DataAsset/DataProduct
- `consumes` — DataPipeline/AIModel/DataProduct → DataAsset/DataProduct
- `creates_value_for` — Initiative/DataProduct/AIModel → BusinessCapability/DataDomain/Department
- `monitors` — System/DataPipeline → AIModel/DataPipeline/System
- `publishes` — DataPipeline/System → DataProduct
- `orchestrates` — System → DataPipeline
