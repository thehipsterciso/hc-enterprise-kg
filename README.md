# hc-enterprise-kg

Enterprise Knowledge Graph for cybersecurity, data, and AI research.

## Install

```bash
poetry install
```

## Usage

```bash
# Generate a synthetic org KG
hckg generate org --profile tech --employees 100 --seed 42

# Inspect the graph
hckg inspect

# Export
hckg export --format json --output graph.json
```

## Development

```bash
make test       # Run tests
make lint       # Lint
make typecheck  # Type check
make all        # All of the above
```
