# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/), and this project adheres to [Semantic Versioning](https://semver.org/).

## [0.20.11] - 2026-02-21

### Added
- **Install pre-flight validation** — `hckg install claude` now runs 3 checks before writing config: Python version, server module existence, MCP SDK importability. Fails with actionable fix commands instead of silently writing a broken config (#191)
- **`hckg install doctor`** — new subcommand that diagnoses an existing Claude Desktop registration without modifying anything
- **`--skip-checks` flag** — bypass pre-flight validation for advanced users
- 16 new tests for install validation (756 total)

## [0.20.10] - 2026-02-21

### Added
- **Architecture Decision Records** — 12 formal ADRs (001-012) documenting every major design choice, each with context, decision, alternatives, honest divergence analysis, and re-evaluation triggers (#187)

### Changed
- **ADR cross-references across documentation** — Added ADR links at decision-point context throughout ARCHITECTURE.md, README.md, CONTRIBUTING.md, CLAUDE.md, entity-model.md, profiles.md, performance.md, python-api.md, cli.md (#188)
- **CONTRIBUTING.md** — Added ADR authoring guidance section for contributors, updated test count (689→740), added ADR directory to documentation table
- **GitHub repo description** — Updated to mention formally documented architectural decisions

## [0.20.7] - 2026-02-20

### Added
- **Analytics charts module** (`src/analysis/charts/`) — auto-generates 8 chart types showcasing scaling, distributions, performance, and quality (#126, #128, #130, #132, #134, #136, #138, #140)
- **`hckg charts` CLI command** — generate charts from synthetic data at multiple scales and profiles
- **`generate_all_charts()` API** — one-call function for programmatic chart generation
- **8 chart types**: scaling curves, entity distribution, relationship distribution, profile comparison, performance scaling, density vs scale, centrality distribution, quality radar
- **ScaleDataCollector** — generates graphs at multiple (profile, scale) combinations and captures comprehensive statistics
- **ChartRenderer** — matplotlib-based rendering with Agg backend, PNG/SVG output, configurable DPI
- **Visual theme** — consistent entity colors, profile colors, type groupings, quality dimension labels
- 48 tests covering models, collector, renderer, CLI, public API, and integration pipeline

## [0.19.7] - 2026-02-20

### Security
- **Fix stack trace exposure in REST API** — Replace exception details with generic error messages in `/openai/call` endpoint (CWE-209, CWE-497) (#123)

## [0.19.6] - 2026-02-20

### Security
- **Fix reflected XSS in REST API** — Validate entity ID path parameters against safe character pattern; replace user-echoed error messages with generic text in 4 routes (CWE-79, CWE-116) (#121)

## [0.19.5] - 2026-02-20

### Security
- **Add explicit permissions to CI workflow** — Lock down `GITHUB_TOKEN` to `contents: read` (least privilege) (CWE-275) (#119)

## [0.19.4] - 2026-02-20

### Changed
- **Update README, ARCHITECTURE, CLAUDE.md** — Document department subdivision, role seniority scaling, entity count override flags, research-backed coefficients, update test count to 692 (#117)

## [0.19.3] - 2026-02-20

### Added
- **Entity count override flags** — 25 individual CLI flags (`--systems`, `--vendors`, `--controls`, etc.) for `hckg demo` and `hckg generate org` to pin exact entity counts, bypassing `scaled_range()` (#115)
- `count_overrides` parameter on `SyntheticOrchestrator` for programmatic use
- 3 new tests for override mechanism (apply, noop, zero-suppression)

## [0.19.2] - 2026-02-20

### Changed
- **Update docs for entity scaling** — Update `docs/profiles.md` with dynamic department scaling section, revised coefficients table, role seniority expansion docs, and scaling results table (#113)
- CHANGELOG entries for v0.19.0 and v0.19.1

## [0.19.1] - 2026-02-20

### Added
- **Dynamic department and role scaling** — Departments exceeding 500 headcount are subdivided into sub-departments using 30+ industry-specific templates. Roles expanded with seniority variants (Junior/Senior/Staff) based on headcount (#111)
- At 14,512 employees (tech): departments 10→42, roles 35→301
- People distributed to leaf departments using headcount-proportional assignment
- Sub-departments linked via `parent_department_id`

## [0.19.0] - 2026-02-20

### Changed
- **Proportional entity scaling** — Raise entity count ceilings and adjust scaling coefficients across all three industry profiles (tech, financial, healthcare) based on Gartner, MuleSoft, NIST, Hackett Group, and McKinsey research (#109)
- Adjusted `ScalingCoefficients` for org_units, vendors, contracts, customers to match industry benchmarks
- Raised ceilings on 16+ entity types to research-backed maximums for orgs up to 20,000 employees
- Dynamic location formula replaces fixed caps (tech: emp÷400, financial: emp÷300, healthcare: emp÷200)

## [0.18.5] - 2026-02-20

### Fixed
- **Fix CI** — Run `ruff format` on 15 unformatted files, resolve mypy duplicate module error with `mypy_path`/`explicit_package_bases`, disable 7 pre-existing mypy error codes that were never enforced (#107)

## [0.18.4] - 2026-02-20

### Changed
- **Add `hckg benchmark` to CLI reference** (`docs/cli.md`) — Document all options, defaults, and examples for the benchmark command (#105)

## [0.18.3] - 2026-02-20

### Added
- **Performance documentation** (`docs/performance.md`) — Benchmark results, scaling characteristics, memory profile, recommended system requirements, architecture guidance (#103)

### Changed
- Update README and CONTRIBUTING with performance docs link, benchmark CLI entry, test count (679 → 689)

## [0.18.2] - 2026-02-20

### Added
- **Performance regression test suite** (`tests/performance/`) — 10 tests with explicit thresholds per scale tier, `@pytest.mark.performance` marker, `make benchmark` target (#101)

## [0.18.1] - 2026-02-20

### Added
- **`hckg benchmark` CLI command** — Wraps BenchmarkSuite with `--profiles`, `--scales`, `--full`, `--output`, `--format`, `--seed` options (#99)

## [0.18.0] - 2026-02-20

### Added
- **Performance benchmarking module** (`src/analysis/benchmark.py`) — `BenchmarkSuite` class measuring 9 performance dimensions: generation, loading, reads, traversal, analysis, export, search, and memory across profiles and scales (#97)
- `BenchmarkResult` and `BenchmarkReport` dataclasses with markdown and JSON output

## [0.17.8] - 2026-02-20

### Changed
- **Update CONTRIBUTING.md** — Fix stale test count (488 → 679), add documentation table linking to new docs/ (#95)

## [0.17.7] - 2026-02-20

### Changed
- **Complete README rewrite** — Slimmed from 549 to ~200 lines with brand voice (Executive Brief mode), links to new docs/ reference materials (#93)

## [0.17.6] - 2026-02-20

### Added
- **Troubleshooting guide** (`docs/troubleshooting.md`) — Common setup issues, Poetry configuration, runnable examples (#91)

## [0.17.5] - 2026-02-20

### Added
- **Profiles & scaling guide** (`docs/profiles.md`) — Industry profile comparison, scaling coefficients, quality scoring, custom profiles (#89)

## [0.17.4] - 2026-02-20

### Added
- **Python API guide** (`docs/python-api.md`) — Generation, querying, analysis, auto-construction, exporting with working examples (#87)

## [0.17.3] - 2026-02-20

### Added
- **CLI reference** (`docs/cli.md`) — All commands with options, defaults, examples, REST endpoints, MCP tools (#85)

## [0.17.2] - 2026-02-20

### Added
- **Entity model reference** (`docs/entity-model.md`) — All 30 entity types, 52 relationship types, generation layers, base model fields (#83)

## [0.17.1] - 2026-02-20

### Changed
- **Codify versioning discipline** — every discrete change gets its own patch bump; documented execution order in CLAUDE.md (#81)

## [0.17.0] - 2026-02-20

### Added
- **12 new relationship types** — CREATES_RISK, SUBJECT_TO, ADDRESSES, HOSTS, FLOWS_TO, CLASSIFIED_AS, REALIZED_BY, CONTAINS, DELIVERS, SERVES, IMPACTS (initiative→risk), MEMBER_OF (person→orgunit) (#77)
- **Entity mirror field population** — Person.holds_roles, Person.located_at, Person.participates_in_initiatives, Role.filled_by_persons, Role.headcount_filled populated from woven relationships (#78)
- **20 relationship enrichment tests** — metadata validation, new type coverage, mirror field assertions

### Changed
- **Relationship metadata enrichment** — All 33 weaver methods now produce contextual weight (severity-based, variance), confidence (0.70-0.95), and properties (dependency_type, exploit_maturity, enforcement, etc.) instead of default 1.0/1.0/{} (#76)
- **`_make_rel()` helper** — Consistent relationship construction with explicit metadata across all weaver methods
- Total woven relationship types: >=30 (up from 22)

## [0.16.0] - 2026-02-20

### Added
- **Quality scoring module** (`src/synthetic/quality.py`) — Automated post-generation assessment with 5 metrics: risk math consistency, description quality, tech stack coherence, field correlation, encryption↔classification (#72)
- **QualityReport dataclass** — Scores, warnings, human-readable summary
- **Post-generation quality check** in orchestrator — warns if overall score < 0.7
- **8 quality tests** — threshold assertions for all metrics

### Changed
- **Semantic coherence overhaul for all 30 generators** (#71):
  - Coordinated template dicts replace independent random selection (system name ↔ OS ↔ stack ↔ ports)
  - Domain-specific descriptions replace faker.sentence()/faker.bs()/faker.paragraph() (#73)
  - RISK_MATRIX[likelihood][impact] → deterministic risk_level; residual ≤ inherent (#74)
  - APT attribution hardcoded for 12 named threat actors
  - Field correlations enforced: encryption↔classification, patch↔status, site security↔type (#75)
  - Budget correlated with headcount, clearance weighted distribution, role permissions mapped

### Fixed
- **Location double-city bug** — name and city field now use same faker.city() call
- **Policy overflow truncation** — generates valid overflow policies for count > template count

## [0.15.0] - 2026-02-20

**Version reset from v1.1.0 → 0.15.0** — Pre-production semver (0.x) to reflect that synthetic data quality, scaling, and relationship completeness are not yet production-grade. (#65)

### Added
- **Industry-aware profile scaling** — `ScalingCoefficients` per industry (tech, financial, healthcare) with size-tier maturity multipliers (startup 0.7x, mid-market 1.0x, enterprise 1.2x, large 1.4x) (#66)
- **`scaled_range()` function** — Entity counts derived from `(employee_count / coefficient) * tier_mult` with floor/ceiling clamping
- **Financial services profile** (`financial_org.py`) — SOX/PCI-dense, 2x controls vs tech
- **Healthcare profile** (`healthcare_org.py`) — HIPAA-driven, 3x data assets vs tech
- **Parametrized stress tests** for 100, 500, 1k, 5k, 10k, 20k employees with time gates (#67)
- **Scaling ratio test** — 20k org must have >10x non-person entities vs 100
- **Industry comparison tests** — financial has denser controls, healthcare has denser data assets

### Changed
- **DEPENDS_ON cap scales with system count** — `max(5, len(systems) // 3)` replaces hardcoded `min(len(systems) // 3, 20)`

### Fixed
- **`scaled_range()` ceiling clamping** — low no longer exceeds high at large employee counts

## [0.14.0] - 2026-02-19

### Added
- **Enterprise synthetic generators** for all 18 L01-L11 entity types
- **10 cross-layer relationship weaving methods** connecting entities across layers
- **Enterprise integration tests** for full 30-type synthetic pipeline
- **Extended sample_entities.json** with all enterprise entity types

## [0.13.0] - 2026-02-19

### Added
- **Initiative entity** — Full implementation replacing last stub (~80 attributes)
- **Initiative test suite** — 14 tests

## [0.12.0] - 2026-02-19

### Added
- **Extended Vendor entity** with contract, compliance, and risk attributes
- **Contract entity** — Vendor contracts with SLAs, financial terms, compliance
- **Test suite** for extended Vendor and Contract entities

## [0.11.0] - 2026-02-19

### Added
- **MarketSegment entity** — Target markets with demographics and sizing
- **Customer entity** — Customer accounts with revenue, satisfaction, lifecycle
- **Test suite** for MarketSegment and Customer entities

## [0.10.0] - 2026-02-19

### Added
- **ProductPortfolio entity** — Product groupings with strategy and lifecycle
- **Product entity** — Individual products with pricing, compliance, and metrics
- **Test suite** for ProductPortfolio and Product entities

## [0.9.0] - 2026-02-19

### Added
- **Site entity** (~91 attributes) — Physical facilities with address, capacity, compliance
- **Geography entity** (~20 attributes) — Geographic regions and territories
- **Jurisdiction entity** (~18 attributes) — Regulatory jurisdictions
- **Locations test suite** — 18 tests

## [0.8.0] - 2026-02-19

### Added
- **BusinessCapability entity** (~90 attributes) — L1/L2/L3 capability hierarchy with maturity assessment
- **Business capabilities test suite** — 12 tests

## [0.7.0] - 2026-02-19

### Added
- **Extended Person entity** (~64 attributes) — Security clearance, emergency contact, career progression
- **Extended Role entity** (~65 attributes) — Permissions, compliance requirements, succession planning
- **People & roles test suite** — 20 tests

## [0.6.0] - 2026-02-19

### Added
- **OrganizationalUnit entity** (~100 attributes) — Business units, divisions, subsidiaries
- **Organization test suite**

## [0.5.0] - 2026-02-19

### Added
- **Extended DataAsset entity** — Expanded with governance, lineage, and quality attributes
- **DataDomain entity** — Logical data groupings with ownership
- **DataFlow entity** — Data movement between systems
- **Data assets test suite**

## [0.4.0] - 2026-02-19

### Added
- **Extended System entity** (~119 attributes) — Full enterprise system modeling
- **Integration entity** (~30 attributes) — System-to-system integrations
- **Technology test suite**

## [0.3.0] - 2026-02-19

### Added
- **Regulation entity** — Laws and standards with compliance tracking
- **Control entity** — Security/compliance controls (SCF-aligned)
- **Risk entity** — Enterprise risks with scoring and treatment
- **Threat entity** — Threat catalog entries (MITRE ATT&CK-aligned)
- **Extended Policy entity** — Added compliance mapping and enforcement
- **Compliance test suite**

## [0.2.0] - 2026-02-19

### Added
- **Enterprise ontology foundation** — Expanded EntityType and RelationshipType enums (30 types, 50 relationships)
- **Shared sub-models** — TemporalAndVersioning, ProvenanceAndConfidence, and other reusable Pydantic models
- **Stub entity classes** for all 18 new enterprise types
- **Backward compatibility tests** and shared sub-model tests

## [0.1.0] - 2025-02-19

### Added
- **Core knowledge graph** with KnowledgeGraph facade, event bus, and query builder
- **12 entity types**: Person, Department, Role, System, Network, Data Asset, Policy, Vendor, Location, Vulnerability, Threat Actor, Incident
- **19 relationship types**: works_in, reports_to, manages, connects_to, depends_on, stores, governs, exploits, affects, supplied_by, and more
- **Synthetic data generation** with profile-driven orchestrator and Faker-based generators
- **3 organization profiles**: tech company, healthcare org, financial services
- **Auto KG construction** from CSV and text with rule-based extraction
- **CLI tool (`hckg`)** with demo, generate, inspect, auto, export commands
- **Export formats**: JSON and GraphML
- **Analysis module** with centrality metrics, risk scoring, attack paths, blast radius
- **NetworkX graph backend** with pluggable engine abstraction
- **MCP server** — 10 tools for Claude Desktop integration
- **REST API server** — Flask-based with OpenAI-compatible endpoints
- **GraphRAG retrieval pipeline**
- **Interactive visualization** via pyvis
- **`hckg serve`** — Unified server with REST and MCP stdio modes
- **`hckg install`** — Register with Claude Desktop
- **124 tests** (unit + integration)
