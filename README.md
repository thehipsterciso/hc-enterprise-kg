# hc-enterprise-kg

[![CI](https://github.com/thehipsterciso/hc-enterprise-kg/actions/workflows/ci.yml/badge.svg)](https://github.com/thehipsterciso/hc-enterprise-kg/actions/workflows/ci.yml)
[![Python 3.11+](https://img.shields.io/badge/python-3.11%2B-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)
[![Code style: ruff](https://img.shields.io/badge/code%20style-ruff-000000.svg)](https://docs.astral.sh/ruff/)

**An open-source enterprise knowledge graph platform for rapid organizational modelling, scenario analysis, and data & AI leadership.**

Build a structurally accurate "digital twin" of an organization — people, departments, systems, vendors, data assets, and the relationships between them — in seconds, not months. Designed for leaders who need directionally correct insights fast.

---

## Vision & Objectives

### The Problem

Data and AI leaders are expected to make high-stakes decisions about organizational structure, technology investment, risk exposure, and operational efficiency — often with incomplete information, fragmented tooling, and no way to model the consequences before committing resources. Full-scale enterprise analysis takes months. By the time it delivers, the landscape has already shifted.

### The Approach

**hc-enterprise-kg** is built for speed-to-insight. It generates realistic enterprise models that let you stress-test scenarios, surface hidden dependencies, and identify low-hanging fruit — without standing up a production data platform or waiting on a six-month consulting engagement.

This is not a replacement for enterprise-grade analysis. It is the tool you reach for *before* that — to rapidly validate hypotheses, pressure-test assumptions, and build the directional confidence needed to prioritize where deeper investment will actually pay off.

### Enabling Data & AI Leadership

The [Chief Data and AI Officer (CDAIO)](https://www.heinz.cmu.edu/programs/executive-education/chief-data-ai-officer-certificate) role — and the broader movement toward unified data, AI, and technology governance — demands a new class of tooling. Leaders in these functions need the ability to model organizational complexity, quantify interdependencies, and communicate findings to boards and stakeholders with structural evidence, not slide decks and intuition.

**hc-enterprise-kg** provides that foundation:

- **Scenario modelling** — Spin up realistic organizational graphs and stress-test structural changes: What happens if this vendor relationship is severed? What's the downstream impact of consolidating two departments? Where are the single points of failure?
- **Rapid discovery** — Surface the insights that are hardest to see in flat data: which systems are over-connected, which teams are under-resourced relative to their data footprint, where do critical dependencies cluster
- **Data governance mapping** — Visualize data asset ownership, classification, and lineage across departments, systems, and third-party relationships in a single connected model
- **AI-readiness assessment** — Model the infrastructure, talent distribution, and process maturity required to operationalize machine learning and generative AI across the enterprise
- **Stakeholder communication** — Produce graph-backed evidence for board-level conversations, investment justification, and strategic planning — grounded in structural analysis rather than subjective assessment

### Why Knowledge Graphs

Spreadsheets model entities. Knowledge graphs model *relationships* — and in enterprise decision-making, the relationships are where the insight lives.

A knowledge graph reveals what flat data cannot: how a change in one part of the organization cascades through dependencies, where risk concentrates at structural chokepoints, and which connections between people, systems, and data create the leverage points that drive disproportionate impact.

Graph-based modelling enables:

- **Dependency analysis** — Trace how entities connect across organizational boundaries to identify hidden fragility and upstream/downstream impact
- **Impact estimation** — Quantify the scope of effect from any structural change, outage, or disruption
- **Centrality and criticality scoring** — Identify the people, systems, and relationships that carry disproportionate organizational weight
- **Scenario comparison** — Generate multiple organizational models and compare structural properties side by side

---

## Prerequisites

- **Python 3.11+** (3.12 recommended; 3.14 is not yet supported by all dependencies)
- **Poetry** for dependency management

If you don't have Poetry installed:

```bash
# macOS
brew install poetry

# Or via pipx (any platform)
pipx install poetry
```

## Install

```bash
git clone https://github.com/thehipsterciso/hc-enterprise-kg.git
cd hc-enterprise-kg
poetry install
```

This creates a virtual environment and installs all dependencies. The CLI tool `hckg` is available through Poetry.

> **Why `poetry run`?** Poetry installs the tool inside its own virtual environment, not system-wide. Every `hckg` command needs the `poetry run` prefix unless you set up an alias (see [Shell Alias](#shell-alias) below).

## Quick Start

One command — generates a full enterprise knowledge graph, exports it to a file, and prints a summary:

```bash
poetry run hckg demo
```

This produces `graph.json` in your current directory containing a complete knowledge graph with ~277 entities and ~543 relationships. The output tells you exactly what was created and what to do next.

You can customize the generated organization:

```bash
# Healthcare org with 500 employees
poetry run hckg demo --profile healthcare --employees 500 --output hospital.json

# Financial services org exported as GraphML
poetry run hckg demo --profile financial --employees 200 --format graphml --output bank.graphml
```

## Shell Alias

To avoid typing `poetry run` every time, add this to your shell config:

```bash
# For zsh (default on macOS)
echo 'alias hckg="poetry run hckg"' >> ~/.zshrc && source ~/.zshrc

# For bash
echo 'alias hckg="poetry run hckg"' >> ~/.bashrc && source ~/.bashrc
```

After that, all examples below work without the `poetry run` prefix. The rest of this README assumes the alias is set up.

## What Gets Generated

Each knowledge graph contains interconnected entities that model a real organization:

| Entity Type | Description | Example Fields |
|---|---|---|
| **Person** | Employees, contractors | name, email, title, department, clearance level |
| **Department** | Organizational units | name, headcount, budget, data sensitivity |
| **System** | Servers, applications, SaaS | hostname, IP, OS, criticality, internet-facing |
| **Network** | Network segments | CIDR, zone (internal/DMZ/guest) |
| **Data Asset** | Databases, file stores | classification (public/internal/confidential/restricted) |
| **Vendor** | Third-party suppliers | contract value, risk tier |
| **Policy** | Governance documents | compliance framework, enforcement status |
| **Vulnerability** | Security weaknesses | CVE ID, CVSS score, severity, patch status |
| **Threat Actor** | Adversaries | motivation, sophistication, target sectors |
| **Incident** | Security events | severity, status, affected systems |
| **Location** | Physical sites | city, country, building type |

These entities are connected by 19 relationship types: `works_in`, `reports_to`, `manages`, `connects_to`, `depends_on`, `stores`, `governs`, `exploits`, `affects`, `supplied_by`, and more.

## CLI Reference

### `hckg demo` — Zero-config demo

Generates a complete org, exports it, and prints a summary. No arguments needed.

```bash
hckg demo
hckg demo --profile healthcare --employees 500 --output hospital.json
hckg demo --format graphml --output graph.graphml
```

| Option | Default | Description |
|---|---|---|
| `--profile` | `tech` | Organization type: `tech`, `healthcare`, `financial` |
| `--employees` | `100` | Number of employees to generate |
| `--seed` | `42` | Random seed for reproducible output |
| `--output` | `graph.json` | Output file path |
| `--format` | `json` | Output format: `json` or `graphml` |

### `hckg generate org` — Synthetic generation

Same generation engine as `demo`, with more granular output. Always exports to a file (defaults to `graph.json`).

```bash
hckg generate org
hckg generate org --profile tech --employees 100 --seed 42
hckg generate org --profile healthcare --employees 500 --output hospital.json
```

### `hckg inspect` — Inspect a knowledge graph file

Loads an exported JSON file and prints entity/relationship breakdowns, graph density, and connectivity.

```bash
# First, generate a graph (this creates graph.json)
hckg demo

# Then inspect it
hckg inspect graph.json
```

### `hckg auto build` — Build KG from your own data

Construct a knowledge graph from a CSV file. The pipeline automatically infers entity types from column names, extracts entities, links relationships, and deduplicates.

```bash
# From your own CSV file
hckg auto build employees.csv --output result.json

# Try it without a file — generates sample data dynamically using Faker
hckg auto build --demo --output result.json
```

Your CSV should have column headers. The pipeline recognizes columns like `name`, `first_name`, `last_name`, `email`, `department`, `title`, `hostname`, `ip_address`, etc. to infer the entity type (Person, System, etc.).

| Option | Default | Description |
|---|---|---|
| `--demo` | off | Run with dynamically generated sample data (no file needed) |
| `--output` | none | Export result to JSON file |
| `--use-llm` / `--no-llm` | `--no-llm` | Enable LLM-based extraction (requires API key) |
| `--use-embeddings` / `--no-embeddings` | `--no-embeddings` | Enable embedding-based linking (requires sentence-transformers) |
| `--llm-model` | `gpt-4o-mini` | LLM model for extraction |

### `hckg auto extract` — Extract entities from text

Quick entity extraction from a text string using rule-based pattern matching. Recognizes emails, IP addresses, hostnames, and CVE IDs.

```bash
hckg auto extract "Contact alice@acme.com at 10.0.1.50 about CVE-2024-1234"
```

### `hckg visualize` — Interactive graph visualization

Renders a knowledge graph as an interactive, color-coded network diagram in your browser. Each entity type gets a distinct color and size. Hover over nodes for details. Includes a floating legend and summary.

```bash
# Generate and visualize in two commands
hckg demo
hckg visualize graph.json

# Customize output
hckg visualize graph.json --output my_viz.html --no-physics
hckg visualize graph.json --height 1200px --no-open
```

| Option | Default | Description |
|---|---|---|
| `--output` | `<source>_viz.html` | Output HTML file path |
| `--height` | `900px` | Visualization height |
| `--width` | `100%` | Visualization width |
| `--physics / --no-physics` | `--physics` | Enable force-directed layout simulation |
| `--open / --no-open` | `--open` | Automatically open in browser |

> Requires the viz extras: `poetry install --extras viz`

### `hckg serve` — Knowledge graph server

Start a server that exposes the knowledge graph to any LLM client, agent framework, or HTTP consumer. REST API by default; use `--stdio` for Claude Desktop's MCP pipe.

```bash
# REST API (default) — works with ChatGPT, OpenAI, LangChain, curl, etc.
hckg serve graph.json
hckg serve graph.json --port 9000 --host 0.0.0.0

# MCP stdio mode — used by Claude Desktop
hckg serve graph.json --stdio
```

| Option | Default | Description |
|---|---|---|
| `--host` | `127.0.0.1` | Bind address |
| `--port` | `8420` | Port to listen on |
| `--stdio` | off | Run as MCP server over stdio (for Claude Desktop) |
| `--reload` | off | Enable auto-reload for development |

**REST endpoints:**

| Endpoint | Description |
|---|---|
| `GET /statistics` | Graph stats (entity/relationship counts by type) |
| `GET /entities` | List entities (`?type=person&limit=50`) |
| `GET /entities/<id>` | Entity details |
| `GET /search?q=alice` | Fuzzy entity search |
| `POST /ask` | GraphRAG question answering (send `{"question": "..."}`) |
| `GET /openai/tools` | OpenAI function-calling tool definitions |
| `POST /openai/call` | Execute a tool by name (for agent frameworks) |
| `GET /health` | Health check |

> REST mode requires `poetry install --extras api`. Stdio mode requires `poetry install --extras mcp`.

### `hckg install` — Register with LLM clients

Register hc-enterprise-kg with LLM desktop clients. Currently supports Claude Desktop; extensible to other clients.

```bash
# Register with Claude Desktop
hckg install claude
hckg install claude --graph graph.json

# Check what's registered
hckg install status

# Remove from a client
hckg install remove claude
```

### `hckg export` — Convert between formats

Re-export an existing JSON knowledge graph to a different format.

```bash
hckg export --source graph.json --format graphml --output graph.graphml
```

## Organization Profiles

Three industry profiles are included, each with realistic department structures, system counts, network segments, and security postures:

| Profile | Default Org Name | Departments | Focus |
|---|---|---|---|
| `tech` | Acme Technologies | Engineering, Product, Sales, Marketing, IT Ops, Security | Software company with DevOps, multiple dev environments |
| `healthcare` | MedCare Health Systems | Clinical Ops, Nursing, Pharmacy, Research, Compliance | HIPAA-sensitive, medical device networks, restricted zones |
| `financial` | Atlas Financial Group | Trading, Risk Mgmt, Compliance, Internal Audit | SOX/PCI focus, trading floor network, high contractor ratio |

Profiles control department distribution, system counts, network architecture, vulnerability probability, and threat actor characteristics. You can create custom profiles by defining an `OrgProfile` object (see `src/synthetic/profiles/base_profile.py`).

## Python API

### Synthetic generation

```python
from graph.knowledge_graph import KnowledgeGraph
from synthetic.orchestrator import SyntheticOrchestrator
from synthetic.profiles.tech_company import mid_size_tech_company

# Create a knowledge graph and generate a tech company with 100 employees.
# The seed parameter makes output reproducible — same seed = same graph.
kg = KnowledgeGraph()
profile = mid_size_tech_company(employee_count=100)
orchestrator = SyntheticOrchestrator(kg, profile, seed=42)
counts = orchestrator.generate()

print(kg.statistics)
# {'entity_count': 277, 'relationship_count': 543, ...}
```

### Querying the graph

```python
from domain.base import EntityType, RelationshipType

# Find all people in the graph
people = kg.query().entities(EntityType.PERSON).execute()

# Filter by attributes — .where() matches on entity fields
active_engineers = (
    kg.query()
    .entities(EntityType.PERSON)
    .where(is_active=True, title="Software Engineer")
    .execute()
)

# Find entities connected to a specific entity via a relationship type
dept_members = (
    kg.query()
    .entities(EntityType.PERSON)
    .connected_to(department_id, via=RelationshipType.WORKS_IN)
    .execute()
)

# Traverse the graph — get immediate neighbors or find shortest paths
neighbors = kg.neighbors(entity_id)
path = kg.shortest_path(source_id, target_id)
```

### Analysis and security queries

```python
from analysis.metrics import (
    compute_centrality,
    compute_risk_score,
    find_most_connected,
)
from analysis.queries import (
    find_attack_paths,
    get_blast_radius,
    find_critical_systems,
    find_unpatched_vulnerabilities,
    find_internet_facing_systems,
)

# Find the most connected entities (potential single points of failure)
top_entities = find_most_connected(kg, top_n=10)

# Compute risk score for a system based on connected vulns, exposure, degree
risk = compute_risk_score(kg, system_id)
# {'entity_name': 'web-server-01', 'risk_score': 65.0, 'factors': {...}}

# Find shortest attack path between two entities
path = find_attack_paths(kg, internet_system_id, database_id)

# Blast radius: what's reachable within 3 hops of a compromised system?
affected = get_blast_radius(kg, compromised_system_id, max_depth=3)

# Security posture queries
critical = find_critical_systems(kg)
unpatched = find_unpatched_vulnerabilities(kg)
exposed = find_internet_facing_systems(kg)
```

### Auto-construction from CSV

```python
from auto.pipeline import AutoKGPipeline
from graph.knowledge_graph import KnowledgeGraph

# The pipeline reads your CSV, infers entity types from column headers,
# extracts entities, links them by shared attributes, and deduplicates.
kg = KnowledgeGraph()
pipeline = AutoKGPipeline(kg, use_llm=False, use_embeddings=False)
result = pipeline.run("employees.csv")

print(result.stats)
# {'entities_extracted': 25, 'entities_after_dedup': 23, ...}
```

### Exporting

```python
from pathlib import Path
from export.json_export import JSONExporter
from export.graphml_export import GraphMLExporter

# Export to JSON — includes entities, relationships, and statistics
JSONExporter().export(kg.engine, Path("output.json"))

# Export to GraphML — compatible with Gephi, yEd, Cytoscape
GraphMLExporter().export(kg.engine, Path("output.graphml"))

# Or get a string (useful for APIs, streaming, etc.)
json_string = JSONExporter().export_string(kg.engine)
```

## Project Structure

```
src/
  cli/          # Click-based CLI (demo, generate, auto, inspect, export, serve, mcp, visualize)
  domain/       # Pydantic v2 entity models (Person, System, Vulnerability, etc.)
  engine/       # Graph backend abstraction (NetworkX; swappable to Neo4j)
  graph/        # KnowledgeGraph facade, event bus, query builder
  synthetic/    # Profile-driven synthetic data generation + relationship weaving
  auto/         # Auto KG construction (rule-based, CSV, LLM extraction + linking)
  ingest/       # Data ingestion (JSON)
  export/       # Export (JSON, GraphML)
  analysis/     # Graph metrics (centrality, PageRank) + security queries
  rag/          # GraphRAG retrieval pipeline (search, context builder, retriever)
  serve/        # REST API server (Flask, OpenAI-compatible endpoints)
  mcp_server/   # MCP server for Claude Desktop integration
tests/          # 217 tests (unit + integration)
examples/       # Runnable example scripts
```

## Optional Dependencies

The base install covers synthetic generation, CSV-based auto-construction, and all CLI commands. Optional extras enable additional capabilities:

```bash
# Embedding-based entity linking (requires ~500MB model download)
poetry install --extras embeddings

# Neo4j graph backend
poetry install --extras neo4j

# Visualization (matplotlib, pyvis)
poetry install --extras viz

# REST API server (Flask)
poetry install --extras api

# MCP server for Claude Desktop
poetry install --extras mcp

# Development tools (pytest, mypy, ruff)
poetry install --extras dev
```

## Development

```bash
make install    # Install with dev dependencies
make test       # Run 217 tests
make test-cov   # Run tests with coverage report
make lint       # Lint with ruff
make format     # Auto-format with ruff
make typecheck  # Type check with mypy
make clean      # Remove caches and build artifacts
make all        # Lint + typecheck + test
```

## Examples

Runnable example scripts that demonstrate the Python API:

```bash
# Synthetic generation with graph exploration
poetry run python examples/quick_start.py

# Auto KG construction from CSV data
poetry run python examples/auto_kg_from_csv.py
```

## Troubleshooting

**`command not found: hckg`**
You need the `poetry run` prefix, or set up a [shell alias](#shell-alias). Poetry installs tools inside a virtual environment, not system-wide.

**`command not found: poetry`**
Install Poetry: `brew install poetry` (macOS) or `pipx install poetry` (any platform).

**`poetry shell` doesn't work**
Poetry 2.0 removed the `shell` command. Use `poetry run hckg ...` instead, or activate the virtualenv manually: `source $(poetry env info -p)/bin/activate`.

**Python 3.14 errors with torch/sentence-transformers**
Some dependencies don't support 3.14 yet. Use Python 3.12: `poetry env use python3.12` then `poetry install`.

**`Path 'graph.json' does not exist`**
You need to generate a graph first. Run `hckg demo` — it creates `graph.json` by default.

**`Provide a SOURCE file, or use --demo`**
The `auto build` command needs either a CSV file or the `--demo` flag. Try: `hckg auto build --demo --output result.json`.

**Tests failing after a fresh clone**
Run `poetry install --extras dev` to get test dependencies, then `make test`.
