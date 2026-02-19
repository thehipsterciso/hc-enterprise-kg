# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/), and this project adheres to [Semantic Versioning](https://semver.org/).

## [Unreleased]

### Added

- **`hckg serve` command** — Unified server with two modes: REST API (default, Flask) for any HTTP client, and `--stdio` for Claude Desktop's MCP pipe. Works with ChatGPT, OpenAI, LangChain, curl, or any LLM client
- **OpenAI-compatible endpoints** — `GET /openai/tools` returns function-calling tool definitions; `POST /openai/call` dispatches tool invocations for agent frameworks
- **GraphRAG endpoint** — `POST /ask` accepts natural-language questions and returns relevant graph context via the retrieval pipeline
- **`hckg install` command** — Register hc-enterprise-kg with LLM clients: `hckg install claude`, `hckg install status`, `hckg install remove claude`. Auto-detects config paths on macOS/Windows/Linux
- **GraphRAG retrieval pipeline** — Keyword extraction, fuzzy entity matching, type detection, neighbor expansion, relevance scoring, and LLM-ready context formatting (`src/rag/`)
- **MCP server** — 10 tools for Claude Desktop integration (`src/mcp_server/`)
- **`hckg visualize` command** — Interactive HTML graph visualization powered by pyvis
- **`--clean` flag on `hckg demo`** — Remove previous output files before regenerating
- **94 new tests** — REST API (32), install CLI (8), serve CLI (3), MCP server tools (17), GraphRAG (16), visualize (18)

### Changed

- **Refined project vision and objectives** — Focused on rapid organizational modelling, scenario analysis, and enabling data & AI leadership (CDAIO). Positioned as a speed-to-insight tool for directionally correct analysis and low-hanging fruit identification
- **Updated README** with Vision & Objectives section covering the problem space, approach, CDAIO enablement, and the rationale for knowledge graph-based modelling
- **Updated project metadata** — Refined description, keywords, and GitHub topics to reflect organizational modelling, data & AI governance, and scenario analysis focus
- **Updated `hckg demo` output** to include `hckg visualize` in next steps

## [0.1.0] - 2025-02-19

### Added

- **Core knowledge graph** with KnowledgeGraph facade, event bus, and query builder
- **12 entity types**: Person, Department, Role, System, Network, Data Asset, Policy, Vendor, Location, Vulnerability, Threat Actor, Incident
- **19 relationship types**: works_in, reports_to, manages, connects_to, depends_on, stores, governs, exploits, affects, supplied_by, and more
- **Synthetic data generation** with profile-driven orchestrator and Faker-based generators
- **3 organization profiles**: tech company, healthcare org, financial services
- **Auto KG construction** from CSV and text with rule-based extraction, heuristic linking, and deduplication
- **CLI tool (`hckg`)** with commands: demo, generate, inspect, auto build, auto extract, export
- **Export formats**: JSON and GraphML
- **Analysis module** with centrality metrics, risk scoring, attack path finding, and blast radius queries
- **NetworkX graph backend** with pluggable engine abstraction
- **124 tests** (unit + integration)
- **Full documentation** in README with CLI reference, Python API examples, and troubleshooting
