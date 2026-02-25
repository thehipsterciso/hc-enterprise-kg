# hc-enterprise-kg

[![CI](https://github.com/thehipsterciso/hc-enterprise-kg/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/thehipsterciso/hc-enterprise-kg/actions/workflows/ci.yml)
[![Python 3.11+](https://img.shields.io/badge/python-3.11%2B-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)
[![Code style: ruff](https://img.shields.io/badge/code%20style-ruff-000000.svg)](https://docs.astral.sh/ruff/)

Rapid enterprise organizational modeling for data, AI, and cybersecurity leaders — stress-test scenarios, surface dependencies, and find quick wins before committing resources.

---

## Why This Exists

Data and AI leaders are expected to make high-stakes decisions about organizational structure, technology investment, and risk exposure with incomplete information and fragmented tooling. The conventional path takes months of discovery, integration, and analysis before delivering a model that is already outdated by the time it arrives.

**hc-enterprise-kg** takes a different approach. It generates a realistic "digital twin" of an enterprise organization, complete with people, departments, systems, vendors, data assets, compliance frameworks, and the relationships between them, so you can stress-test scenarios, surface hidden dependencies, and identify structural chokepoints before committing resources to deeper analysis. The output is a connected graph, not a spreadsheet, because in enterprise decision-making the relationships between entities are where the insight lives.

This is the tool you reach for *before* a full-scale engagement, to validate hypotheses and build the directional confidence needed to prioritize where deeper investment will actually pay off.

---

## Quick Start

```bash
git clone https://github.com/thehipsterciso/hc-enterprise-kg.git
cd hc-enterprise-kg
poetry install
poetry run hckg demo
```

That generates a complete enterprise knowledge graph with ~277 entities and ~543 relationships, exports it to `graph.json`, and prints a summary. Inspect what was created:

```bash
poetry run hckg inspect graph.json
```

Customize the organization:

```bash
# Healthcare org with 500 employees
poetry run hckg demo --profile healthcare --employees 500 --output hospital.json

# Financial services, exported as GraphML for Gephi
poetry run hckg demo --profile financial --employees 200 --format graphml

# Override specific entity counts
poetry run hckg demo --employees 5000 --systems 500 --vendors 100 --controls 200
```

---

## What Gets Generated

Each graph contains **30 interconnected entity types** modelling a complete organization across 12 generation layers: compliance and governance (regulations, controls, risks, threats), technology infrastructure (systems, integrations, networks), data landscape (assets, domains, flows), organizational structure (departments, business units, capabilities), people and roles, physical locations and jurisdictions, products and portfolios, customers and market segments, vendor contracts, and strategic initiatives.

These entities are connected by **52 relationship types**, each carrying contextual weight, confidence scores, and typed properties. A `depends_on` relationship between two systems includes a dependency type and strength. A `mitigates` relationship between a control and a risk carries effectiveness metadata. Three industry profiles (technology, financial services, healthcare) produce structurally different graphs that reflect real-world sector patterns, with entity counts scaled to research-backed benchmarks (Gartner, MuleSoft, NIST, Hackett Group, McKinsey) from 100-employee startups to 20,000-employee enterprises.

Departments exceeding 500 headcount are automatically subdivided into sub-departments (30+ industry-specific templates), and roles expand with seniority variants (Junior/Senior/Staff) based on headcount. At 14,512 employees, a tech org generates 42 departments and 301 roles instead of the fixed 10/35. Individual entity counts can be pinned via CLI flags (`--systems 500 --vendors 100`) to bypass scaling.

Generated data is validated by an automated quality scoring module that checks risk math consistency, description quality, tech stack coherence, field correlations, and encryption-classification alignment.

> See [Entity Model Reference](docs/entity-model.md) and [Organization Profiles](docs/profiles.md) for full details.

---

## What You Can Do With It

- **Scenario modelling** -- Spin up organizational graphs and stress-test structural changes. What happens if a vendor relationship is severed? What is the downstream impact of consolidating two departments?
- **Blast radius analysis** -- Quantify what is reachable within N hops of a compromised system, a failing vendor, or a departing key person
- **Dependency mapping** -- Trace how entities connect across organizational boundaries to identify hidden fragility and single points of failure
- **Centrality and criticality scoring** -- Find the people, systems, and relationships that carry disproportionate organizational weight
- **Risk quantification** -- Score entities based on connected vulnerabilities, exposure, and structural position rather than qualitative heat maps
- **Attack path analysis** -- Find shortest paths between threat entry points and critical assets
- **Data governance mapping** -- Visualize data asset ownership, classification, and lineage across departments, systems, and third parties

---

## Project Structure

```
src/
  cli/          Click-based CLI (demo, generate, inspect, auto, serve, install, visualize, export, benchmark)
  domain/       Pydantic v2 entity models (30 types), enums, entity registry
  engine/       Graph backend abstraction (NetworkX; swappable to Neo4j)
  graph/        KnowledgeGraph facade, event bus, query builder
  synthetic/    Profile-driven generation, relationship weaving, quality scoring
  auto/         Auto KG construction from CSV/text (rule-based + optional LLM)
  ingest/       Data ingestion (JSON, CSV with schema mappings and transforms)
  export/       Export (JSON, GraphML)
  analysis/     Graph metrics (centrality, PageRank), risk scoring, benchmarking
  rag/          GraphRAG retrieval pipeline
  serve/        REST API server (Flask, OpenAI-compatible endpoints)
  mcp_server/   MCP server for Claude Desktop (10 tools, auto-reload)
tests/          740+ tests (unit, integration, stress, performance)
```

> See [Architecture](ARCHITECTURE.md) for the full system design.

---

## CLI Quick Reference

| Command | Description |
|---|---|
| `hckg demo` | Generate a complete org graph, export, and print summary |
| `hckg generate org` | Synthetic generation with configurable profile and scale |
| `hckg inspect <file>` | Load and inspect a graph file (entity/relationship breakdown) |
| `hckg auto build <csv>` | Build a knowledge graph from CSV data |
| `hckg auto extract <text>` | Extract entities from text (emails, IPs, CVEs) |
| `hckg visualize <file>` | Interactive graph visualization in the browser |
| `hckg serve <file>` | REST API server or MCP stdio for Claude Desktop |
| `hckg install claude` | Register with Claude Desktop |
| `hckg export` | Convert between JSON and GraphML formats |
| `hckg benchmark` | Run performance benchmarks across profiles and scales |

> See [CLI Reference](docs/cli.md) for full options and examples.

---

## Documentation

| Document | Description |
|---|---|
| [Entity Model Reference](docs/entity-model.md) | All 30 entity types, 52 relationship types, generation layers, base model fields |
| [CLI Reference](docs/cli.md) | All commands with options, defaults, examples, REST endpoints |
| [Python API Guide](docs/python-api.md) | Generation, querying, analysis, auto-construction, exporting |
| [Organization Profiles](docs/profiles.md) | Industry profiles, scaling model, quality scoring, custom profiles |
| [Performance & Benchmarking](docs/performance.md) | Benchmark results, scaling characteristics, memory profile, system requirements |
| [Architecture](ARCHITECTURE.md) | System design, layer pipeline, engine abstraction, data flow |
| [Troubleshooting](docs/troubleshooting.md) | Common issues, setup, runnable examples |
| [Architecture Decision Records](docs/adr/) | Design rationale for all major architectural choices (12 ADRs) |
| [Contributing](CONTRIBUTING.md) | Development setup, code style, adding entity types |
| [Changelog](CHANGELOG.md) | Release history |

---

## Shell Alias

To avoid typing `poetry run` every time:

```bash
# zsh (default on macOS)
echo 'alias hckg="poetry run hckg"' >> ~/.zshrc && source ~/.zshrc

# bash
echo 'alias hckg="poetry run hckg"' >> ~/.bashrc && source ~/.bashrc
```

---

## Optional Dependencies

```bash
poetry install --extras viz         # Visualization (pyvis)
poetry install --extras api         # REST API server (Flask)
poetry install --extras mcp         # MCP server for Claude Desktop
poetry install --extras embeddings  # Embedding-based entity linking
poetry install --extras neo4j       # Neo4j graph backend
poetry install --extras dev         # Development tools (pytest, mypy, ruff)
```

---

## Development

```bash
make install    # Install with dev dependencies
make test       # Run all tests (~740)
make test-cov   # Tests with coverage report
make lint       # Lint with ruff
make format     # Auto-format with ruff
make typecheck  # Type check with mypy
make clean      # Remove caches and build artifacts
make all        # Lint + typecheck + test
```

---

## License

MIT
