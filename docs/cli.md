# CLI Reference

The `hckg` command-line tool provides synthetic graph generation, inspection, auto-construction from data, visualization, and server modes for both REST and MCP clients. All commands run through Poetry's virtual environment.

```bash
# Direct invocation
poetry run hckg <command> [options]

# Or set up an alias (recommended)
alias hckg="poetry run hckg"
```

**Global options:**

| Option | Default | Description |
|---|---|---|
| `--backend` | `networkx` | Graph backend to use |
| `--version` | — | Show version and exit |

---

## `hckg demo`

Zero-config demo. Generates a complete enterprise knowledge graph, exports it to a file, and prints a summary.

```bash
hckg demo
hckg demo --profile healthcare --employees 500 --output hospital.json
hckg demo --format graphml --output graph.graphml
hckg demo --clean  # removes previous output files before generating
hckg demo --employees 5000 --systems 500 --vendors 100  # override entity counts
```

| Option | Default | Description |
|---|---|---|
| `--profile` | `tech` | Organization type: `tech`, `healthcare`, `financial` |
| `--employees` | `100` | Number of employees to generate |
| `--seed` | `42` | Random seed for reproducible output |
| `--output` | `graph.json` | Output file path |
| `--format` | `json` | Output format: `json` or `graphml` |
| `--clean` | off | Remove previous output files before generating (`graph.json`, `graph.graphml`, `result.json`, `*_viz.html`) |
| `--systems`, `--vendors`, etc. | None | Override specific entity counts (see [Entity Count Overrides](#entity-count-overrides)) |

---

## `hckg generate org`

Synthetic generation with the same engine as `demo`, using different defaults. Always exports to a file.

```bash
hckg generate org
hckg generate org --profile financial --employees 1000 --seed 99
hckg generate org --output large_org.json
hckg generate org --employees 14512 --systems 500 --vendors 100 --controls 200
```

| Option | Default | Description |
|---|---|---|
| `--profile` | `tech` | Organization type: `tech`, `healthcare`, `financial` |
| `--employees` | `500` | Number of employees to generate |
| `--seed` | None | Random seed for reproducibility (omit for random) |
| `--output` | `graph.json` | Export file path |
| `--systems`, `--vendors`, etc. | None | Override specific entity counts (see [Entity Count Overrides](#entity-count-overrides)) |

---

## `hckg inspect`

Load and inspect an exported knowledge graph file. Prints entity/relationship breakdowns, graph density, and connectivity status.

```bash
hckg demo                 # generates graph.json
hckg inspect graph.json   # inspect it
```

**Arguments:**

| Argument | Required | Description |
|---|---|---|
| `SOURCE` | Yes | Path to a knowledge graph JSON file (must exist) |

**Output includes:** entity count, relationship count, graph density, weak connectivity, entity types breakdown, relationship types breakdown.

---

## `hckg import`

Import real organizational data from JSON or CSV files into the knowledge graph. Validates data before writing and supports column mapping files for vendor exports.

```bash
hckg import organization.json                          # JSON import
hckg import people.csv -t person                       # CSV with explicit type
hckg import workday.csv --mapping workday-hr.mapping.json  # CSV with column mapping
hckg import data.json --dry-run --strict               # validate only
hckg import new-data.json --merge existing.json        # merge into existing graph
```

**Arguments:**

| Argument | Required | Description |
|---|---|---|
| `SOURCE` | Yes | Path to JSON or CSV file |

**Options:**

| Option | Default | Description |
|---|---|---|
| `-o`, `--output` | `graph.json` | Output graph file path |
| `-t`, `--entity-type` | auto-detect | Entity type for CSV import |
| `-m`, `--merge` | — | Merge into existing graph file |
| `--mapping` | — | Column mapping file for CSV (`.mapping.json`) |
| `--dry-run` | off | Validate only, do not write output |
| `--strict` | off | Treat warnings as errors |

**Notes:** `--mapping` and `--entity-type` are mutually exclusive. `--mapping` is CSV-only. See [Import Guide](import-guide.md) for full documentation.

---

## `hckg auto build`

Construct a knowledge graph from a CSV file. The pipeline infers entity types from column headers, extracts entities, links relationships by shared attributes, and deduplicates.

```bash
# From your own CSV
hckg auto build employees.csv --output result.json

# Demo mode — generates sample data, no file needed
hckg auto build --demo --output result.json
```

**Arguments:**

| Argument | Required | Description |
|---|---|---|
| `SOURCE` | No (if `--demo`) | Path to CSV data source |

**Options:**

| Option | Default | Description |
|---|---|---|
| `--demo` | off | Run with dynamically generated sample data |
| `--use-llm` / `--no-llm` | `--no-llm` | Enable LLM-based extraction (requires API key) |
| `--use-embeddings` / `--no-embeddings` | `--no-embeddings` | Enable embedding-based linking (requires sentence-transformers) |
| `--llm-model` | `gpt-4o-mini` | LLM model for extraction |
| `--output` | None | Export result to JSON file |

**Recognized CSV columns:** `name`, `first_name`, `last_name`, `email`, `department`, `title`, `location`, `hostname`, `ip_address`, and others. Column names are used to infer entity types (Person, System, etc.).

---

## `hckg auto extract`

Extract entities from a text string using rule-based pattern matching. Recognizes emails, IP addresses, hostnames, and CVE IDs.

```bash
hckg auto extract "Contact alice@acme.com at 10.0.1.50 about CVE-2024-1234"
```

**Arguments:**

| Argument | Required | Description |
|---|---|---|
| `TEXT` | Yes | Text string to extract entities from |

---

## `hckg visualize`

Render a knowledge graph as an interactive, color-coded network diagram in the browser. Each entity type gets a distinct color and size. Hover for details.

```bash
hckg visualize graph.json
hckg visualize graph.json --output custom_viz.html --no-physics
hckg visualize graph.json --height 1200px --no-open
```

**Arguments:**

| Argument | Required | Description |
|---|---|---|
| `SOURCE` | Yes | Path to knowledge graph JSON file (must exist) |

**Options:**

| Option | Default | Description |
|---|---|---|
| `--output` | `<source>_viz.html` | Output HTML file path |
| `--height` | `900px` | Visualization height |
| `--width` | `100%` | Visualization width |
| `--physics` / `--no-physics` | `--physics` | Enable force-directed layout simulation |
| `--open` / `--no-open` | `--open` | Automatically open in browser |

> Requires: `poetry install --extras viz`

---

## `hckg serve`

Start a knowledge graph server. REST API by default for HTTP consumers; `--stdio` for Claude Desktop's MCP pipe.

```bash
# REST API — works with curl, ChatGPT, LangChain, any HTTP client
hckg serve graph.json
hckg serve graph.json --port 9000 --host 0.0.0.0

# MCP stdio — for Claude Desktop
hckg serve graph.json --stdio
```

**Arguments:**

| Argument | Required | Description |
|---|---|---|
| `SOURCE` | Yes | Path to knowledge graph JSON file (must exist) |

**Options:**

| Option | Default | Description |
|---|---|---|
| `--host` | `127.0.0.1` | Bind address |
| `--port` | `8420` | Port to listen on |
| `--stdio` | off | Run as MCP server over stdio (for Claude Desktop) |
| `--reload` | off | Enable auto-reload for development |

> REST mode requires: `poetry install --extras api`
> MCP stdio requires: `poetry install --extras mcp`

### REST API Endpoints

Base URL: `http://127.0.0.1:8420` (default)

| Method | Endpoint | Description |
|---|---|---|
| GET | `/` | API index — lists all endpoints |
| GET | `/health` | Health check |
| GET | `/statistics` | Graph statistics (entity/relationship counts by type, density, connectivity) |
| GET | `/entities` | List entities. Params: `?type=<entity_type>`, `?limit=<int>` (default 50) |
| GET | `/entities/<id>` | Get entity by ID |
| GET | `/entities/<id>/neighbors` | Get neighbors. Params: `?direction=in|out|both`, `?relationship_type=<str>` |
| GET | `/path/<src>/<tgt>` | Shortest path between two entities |
| GET | `/blast-radius/<id>` | Blast radius. Params: `?max_depth=<int>` (default 3) |
| GET | `/centrality` | Centrality scores. Params: `?metric=degree|betweenness|pagerank`, `?top_n=<int>` (default 20) |
| GET | `/search` | Fuzzy name search. Params: `?q=<query>` (required), `?type=<entity_type>`, `?limit=<int>` |
| POST | `/ask` | GraphRAG Q&A. Body: `{"question": "...", "top_k": 20}` |
| POST | `/load` | Load a graph file. Body: `{"path": "/abs/path/to/graph.json"}` |
| GET | `/openai/tools` | OpenAI function-calling tool definitions |
| POST | `/openai/call` | Execute a tool by name. Body: `{"name": "<tool>", "arguments": {...}}` |

### OpenAI-Compatible Tool Names

For use with `/openai/call`: `get_statistics`, `list_entities`, `get_entity`, `get_neighbors`, `find_shortest_path`, `get_blast_radius`, `compute_centrality`, `search_entities`, `ask_graph`

### MCP Tools

When running in `--stdio` mode, the server exposes 10 tools to Claude Desktop:

`load_graph`, `get_statistics`, `list_entities`, `get_entity`, `get_neighbors`, `find_shortest_path`, `get_blast_radius`, `compute_centrality`, `find_most_connected`, `search_entities`

The MCP server auto-reloads when the graph file changes (mtime-based detection on every tool call — see [ADR-009](adr/009-mcp-mtime-auto-reload.md)).

---

## `hckg install`

Register hc-enterprise-kg with LLM desktop clients. Currently supports Claude Desktop.

```bash
# Register with Claude Desktop
hckg install claude
hckg install claude --graph graph.json

# Check registration status
hckg install status

# Remove registration
hckg install remove claude
```

### `hckg install claude`

| Option | Default | Description |
|---|---|---|
| `--config` | Auto-detected | Path to `claude_desktop_config.json` |
| `--graph` | None | Default graph file to auto-load on startup |

Config auto-detection paths:
- **macOS:** `~/Library/Application Support/Claude/claude_desktop_config.json`
- **Windows:** `%APPDATA%/Claude/claude_desktop_config.json`
- **Linux:** `$XDG_CONFIG_HOME/claude/claude_desktop_config.json`

### `hckg install status`

Reports whether `hc-enterprise-kg` is registered in Claude Desktop config. Shows command, working directory, and graph path if registered.

### `hckg install remove claude`

Removes the `hc-enterprise-kg` entry from Claude Desktop config.

---

## `hckg export`

Re-export an existing JSON knowledge graph to a different format.

```bash
hckg export --source graph.json --format graphml --output graph.graphml
```

| Option | Default | Description |
|---|---|---|
| `--source` | — | Source JSON knowledge graph file (required) |
| `--format` | `json` | Output format: `json` or `graphml` |
| `--output` | — | Output file path (required) |

---

## Entity Count Overrides

Both `hckg demo` and `hckg generate org` accept individual flags to override specific entity counts. When provided, these bypass the `scaled_range()` scaling formula ([ADR-007](adr/007-research-backed-scaling.md)) and produce exactly the specified number of entities.

```bash
# Pin systems to 500 and vendors to 100, let everything else scale normally
hckg generate org --employees 14512 --systems 500 --vendors 100

# Override controls and risks for a compliance-focused scenario
hckg demo --employees 5000 --controls 200 --risks 50 --customers 1000
```

### Available Override Flags

| Flag | Entity Type |
|---|---|
| `--systems` | System |
| `--data-assets` | DataAsset |
| `--policies` | Policy |
| `--vendors` | Vendor |
| `--locations` | Location |
| `--threat-actors` | ThreatActor |
| `--incidents` | Incident |
| `--regulations` | Regulation |
| `--controls` | Control |
| `--risks` | Risk |
| `--threats` | Threat |
| `--integrations` | Integration |
| `--data-domains` | DataDomain |
| `--data-flows` | DataFlow |
| `--org-units` | OrganizationalUnit |
| `--capabilities` | BusinessCapability |
| `--sites` | Site |
| `--geographies` | Geography |
| `--jurisdictions` | Jurisdiction |
| `--product-portfolios` | ProductPortfolio |
| `--products` | Product |
| `--market-segments` | MarketSegment |
| `--customers` | Customer |
| `--contracts` | Contract |
| `--initiatives` | Initiative |

**Not overridable** (derived from other state): departments, roles, networks, vulnerabilities, persons (use `--employees`).

---

## `hckg benchmark`

Run performance benchmarks across organization profiles and employee scales. Measures generation time, memory, load/export, read latency, traversal, analysis, and search.

```bash
# Quick benchmark (tech profile, 100 + 500 employees)
hckg benchmark

# Full benchmark (all 3 profiles, 6 scales: 100-20,000)
hckg benchmark --full

# Custom profiles and scales
hckg benchmark --profiles tech,financial --scales 100,1000,5000

# Save report to file
hckg benchmark --output report.md
hckg benchmark --full --format json --output report.json
```

| Option | Default | Description |
|---|---|---|
| `--profiles` | `tech` | Comma-separated profile names: `tech`, `financial`, `healthcare` |
| `--scales` | `100,500` | Comma-separated employee counts |
| `--full` | off | Run all 3 profiles at 100, 500, 1,000, 5,000, 10,000, 20,000 employees |
| `--output` | None | Save report to file (prints to stdout if omitted) |
| `--format` | `markdown` | Report format: `markdown` or `json` |
| `--seed` | `42` | Random seed for reproducible generation |

**Output:** A markdown table (or JSON document) with per-profile, per-scale measurements including generation time, entity/relationship counts, peak memory, quality scores, and per-operation latency.

> See [Performance & Benchmarking](performance.md) for detailed results and scaling characteristics.
