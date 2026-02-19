# hc-enterprise-kg

Enterprise Knowledge Graph for cybersecurity, data, and AI research. Build a "digital twin" of an organization with synthetic data generation, automatic KG construction from CSV/text, and graph analysis.

## Install

```bash
poetry install
```

## Quick Start

```python
from graph.knowledge_graph import KnowledgeGraph
from synthetic.orchestrator import SyntheticOrchestrator
from synthetic.profiles.tech_company import mid_size_tech_company

kg = KnowledgeGraph()
profile = mid_size_tech_company(employee_count=100)
SyntheticOrchestrator(kg, profile, seed=42).generate()

print(kg.statistics)
```

## CLI

All CLI commands run through Poetry:

```bash
# Generate a synthetic org KG
poetry run hckg generate org --profile tech --employees 100 --seed 42

# Generate and export to JSON
poetry run hckg generate org --profile healthcare --employees 200 --output graph.json

# Inspect an exported KG
poetry run hckg inspect graph.json

# Export to different formats
poetry run hckg export --source graph.json --format graphml --output graph.graphml

# Auto-construct KG from a CSV file
poetry run hckg auto build data.csv --output result.json

# Extract entities from text
poetry run hckg auto extract "Contact alice@acme.com at 10.0.1.50"
```

Available profiles: `tech`, `healthcare`, `financial`

## Project Structure

```
src/
  domain/       # Pydantic v2 entity models (Person, System, Vulnerability, etc.)
  engine/       # Graph backend abstraction (NetworkX, swappable to Neo4j)
  graph/        # KnowledgeGraph facade + event bus
  synthetic/    # Profile-driven synthetic data generation
  auto/         # Automatic KG construction (rule-based, CSV, LLM extraction)
  ingest/       # Data ingestion (CSV, JSON)
  export/       # Export (JSON, GraphML)
  analysis/     # Pre-built queries and graph metrics
  cli/          # Click-based CLI
tests/          # 124 tests (unit + integration)
examples/       # quick_start.py, auto_kg_from_csv.py
```

## Development

```bash
make install    # Install with dev dependencies
make test       # Run tests
make lint       # Lint with ruff
make typecheck  # Type check with mypy
make all        # All of the above
```

## Examples

```bash
poetry run python examples/quick_start.py
poetry run python examples/auto_kg_from_csv.py
```
