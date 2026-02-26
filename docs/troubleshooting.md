# Troubleshooting & Examples

---

## Common Issues

### `command not found: hckg`

Poetry installs tools inside a virtual environment, not system-wide. Use the `poetry run` prefix:

```bash
poetry run hckg demo
```

Or set up an alias to avoid typing it every time:

```bash
# zsh (default on macOS)
echo 'alias hckg="poetry run hckg"' >> ~/.zshrc && source ~/.zshrc

# bash
echo 'alias hckg="poetry run hckg"' >> ~/.bashrc && source ~/.bashrc
```

### `command not found: poetry`

Install Poetry:

```bash
# macOS (recommended)
brew install poetry

# Any platform
pipx install poetry
```

### Poetry curl installer fails: "This build of python cannot create venvs without using symlinks"

You are using Apple's Command Line Tools Python (`/Library/Developer/CommandLineTools/`), which is intentionally restricted and cannot create virtualenvs without symlinks. The `curl | python3 -` installer path does not work with this Python.

**Fix — use Homebrew instead:**

```bash
brew install poetry
```

Homebrew's poetry brings a compatible Python (3.14+) and sets up the virtualenv correctly. After installation, add poetry to your PATH if prompted:

```bash
export PATH="/opt/homebrew/bin:$PATH"
```

Then proceed with:

```bash
poetry install
poetry run hckg demo
```

### `poetry shell` doesn't work

Poetry 2.0 removed the `shell` command. Use `poetry run hckg ...` instead, or activate the virtualenv manually:

```bash
source $(poetry env info -p)/bin/activate
```

### Python 3.14 errors with torch / sentence-transformers

Some dependencies do not support Python 3.14 yet. Use Python 3.12:

```bash
poetry env use python3.12
poetry install
```

### `Path 'graph.json' does not exist`

You need to generate a graph first:

```bash
hckg demo          # creates graph.json
hckg inspect graph.json
```

### `Provide a SOURCE file, or use --demo`

The `auto build` command needs either a CSV file or the `--demo` flag:

```bash
hckg auto build --demo --output result.json
hckg auto build employees.csv --output result.json
```

### Tests failing after a fresh clone

Install dev dependencies first:

```bash
poetry install --extras dev
make test
```

### Visualization extras not found

The `visualize` command requires the viz extras:

```bash
poetry install --extras viz
hckg visualize graph.json
```

### REST server won't start

The `serve` command requires the api extras:

```bash
poetry install --extras api
hckg serve graph.json
```

For MCP stdio mode, install the mcp extras instead:

```bash
poetry install --extras mcp
hckg serve graph.json --stdio
```

---

## Runnable Examples

Two example scripts demonstrate the Python API end-to-end.

### Synthetic Generation

Generates a tech company graph, explores entities and relationships, and exports to JSON.

```bash
poetry run python examples/quick_start.py
```

### Auto-Construction from CSV

Builds a knowledge graph from CSV data using the auto-construction pipeline with heuristic linking and deduplication.

```bash
poetry run python examples/auto_kg_from_csv.py
```

---

For full CLI usage, see [CLI Reference](cli.md). For the Python API, see [Python API Guide](python-api.md).
