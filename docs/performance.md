# Performance & Benchmarking

---

## Running Benchmarks

```bash
# Quick benchmark (tech profile, 100 + 500 employees)
hckg benchmark

# Full benchmark (all profiles, all scales)
hckg benchmark --full

# Custom profiles and scales
hckg benchmark --profiles tech,financial --scales 100,1000,5000

# Save report
hckg benchmark --output report.md
hckg benchmark --format json --output report.json
```

Run performance regression tests:

```bash
make benchmark
# or
poetry run pytest tests/performance/ -v
```

---

## Synthetic Generation

Generation time scales linearly with employee count. Memory follows the same pattern. Quality scores remain above 0.96 at all scales.

| Profile | Employees | Time (s) | Entities | Relationships | Peak Memory (MB) | Quality |
|---|---|---|---|---|---|---|
| tech | 100 | 0.20 | 269 | 652 | 8.8 | 0.99 |
| tech | 500 | 0.64 | 795 | 2,525 | 28.9 | 0.99 |
| tech | 1,000 | 1.33 | 1,488 | 4,907 | 54.6 | 0.96 |
| tech | 5,000 | 6.74 | 7,423 | 24,832 | 277.7 | 0.97 |
| financial | 100 | 0.21 | 324 | 785 | 10.9 | 0.98 |
| financial | 500 | 0.65 | 831 | 2,595 | 29.5 | 0.98 |
| financial | 1,000 | 1.45 | 1,574 | 5,106 | 56.6 | 0.99 |
| financial | 5,000 | 7.44 | 8,228 | 26,672 | 303.8 | 0.98 |
| healthcare | 100 | 0.20 | 307 | 757 | 10.3 | 1.00 |
| healthcare | 500 | 1.00 | 847 | 2,652 | 30.9 | 0.98 |
| healthcare | 1,000 | 1.35 | 1,648 | 5,226 | 61.1 | 0.99 |
| healthcare | 5,000 | 7.59 | 8,699 | 27,432 | 332.9 | 0.98 |

Financial and healthcare profiles generate denser graphs than tech at the same employee count due to higher compliance and data asset scaling coefficients.

---

## Operation Latency

Times in seconds for the tech profile. Most operations stay under 100ms at 5,000 employees.

| Operation | 100 | 500 | 1,000 | 5,000 |
|---|---|---|---|---|
| Single entity lookup | <0.001 | <0.001 | <0.001 | <0.001 |
| Filtered list (by type) | 0.002 | 0.008 | 0.017 | 0.083 |
| Query builder | 0.001 | 0.004 | 0.006 | 0.033 |
| Neighbors | <0.001 | <0.001 | <0.001 | <0.001 |
| Shortest path | <0.001 | <0.001 | <0.001 | <0.001 |
| Blast radius (depth 3) | 0.009 | 0.036 | 0.038 | 0.108 |
| Degree centrality | <0.001 | <0.001 | 0.001 | 0.005 |
| Betweenness centrality | 0.009 | 0.081 | 0.777 | 52.0 |
| Risk score | <0.001 | <0.001 | <0.001 | <0.001 |
| Fuzzy search | 0.007 | 0.017 | 0.033 | 0.716 |

**Betweenness centrality** is the one operation that scales super-linearly. It runs in O(VE) time, which means it jumps from under a second at 1,000 employees to nearly a minute at 5,000. For graphs above 1,000 employees, consider using degree centrality or PageRank instead, both of which remain sub-second at all tested scales.

---

## Export & Load

| Profile | Employees | Export (s) | File Size (MB) | Load (s) |
|---|---|---|---|---|
| tech | 100 | 0.04 | 1.4 | 0.03 |
| tech | 500 | 0.65 | 4.4 | 0.09 |
| tech | 1,000 | 0.20 | 8.3 | 0.18 |
| tech | 5,000 | 1.74 | 42.4 | 2.65 |
| financial | 5,000 | 1.99 | 46.3 | 1.58 |
| healthcare | 5,000 | 1.94 | 50.5 | 2.40 |

File size grows proportionally with entity and relationship count. Healthcare produces the largest files at a given scale due to denser data asset and compliance entity graphs.

---

## Memory Profile

Peak memory during generation, measured via `tracemalloc`:

| Employees | Tech (MB) | Financial (MB) | Healthcare (MB) |
|---|---|---|---|
| 100 | 8.8 | 10.9 | 10.3 |
| 500 | 28.9 | 29.5 | 30.9 |
| 1,000 | 54.6 | 56.6 | 61.1 |
| 5,000 | 277.7 | 303.8 | 332.9 |

Memory scales linearly at roughly 55-65 MB per 1,000 employees. The loaded graph (after export/import roundtrip) uses slightly less memory than the generation peak because transient generation state is released.

---

## Scaling Characteristics

| Metric | Scaling Behavior | Notes |
|---|---|---|
| Generation time | Linear | ~1.3s per 1,000 employees |
| Entity count | Linear | ~1,500 entities per 1,000 employees (tech) |
| Relationship count | Linear | ~5,000 relationships per 1,000 employees |
| Peak memory | Linear | ~55 MB per 1,000 employees |
| File size | Linear | ~8 MB per 1,000 employees |
| Single lookup | Constant | Hash-based, sub-millisecond at any scale |
| Neighbors | Constant | Adjacency list lookup |
| Blast radius | Sub-linear | Bounded by depth parameter |
| Degree centrality | Linear | O(V + E) |
| Betweenness centrality | Super-linear | O(VE), avoid above 1,000 employees |
| Fuzzy search | Linear | Scales with unique entity name count |

---

## Recommended System Requirements

| Scale | Employees | RAM | CPU | Generation Time | Disk (JSON) |
|---|---|---|---|---|---|
| Small | 100 | 256 MB | Any | <1s | 2 MB |
| Medium | 500 | 512 MB | Any | <1s | 5 MB |
| Large | 1,000 | 1 GB | Any | ~1.5s | 10 MB |
| Enterprise | 5,000 | 2 GB | 2+ cores | ~7s | 50 MB |
| Large Enterprise | 10,000 | 4 GB | 4+ cores | ~15s | 100 MB |
| Maximum | 20,000 | 8 GB | 4+ cores | ~30s | 200 MB |

These recommendations include headroom for analysis operations after generation. Betweenness centrality at 5,000+ employees will benefit from faster CPUs.

---

## Architecture Guidance

The default **NetworkX backend** is sufficient for most use cases up to 20,000 employees. It runs in-process with no external dependencies, making it ideal for development, testing, CI/CD pipelines, and single-user analysis.

Consider a **Neo4j backend** (via the pluggable engine abstraction) when:

- You need persistent storage across sessions
- Multiple users need concurrent read/write access
- Graph size exceeds available RAM
- You need Cypher query capabilities beyond the built-in query builder
- Betweenness centrality or other expensive algorithms need to run on large graphs (Neo4j's GDS library has optimized parallel implementations)

The engine abstraction (`AbstractGraphEngine`) means switching backends requires no changes to application code, only configuration.

---

## Performance Regression Tests

The test suite in `tests/performance/` defines explicit thresholds:

| Scale | Generation | Load | Blast Radius | Centrality | Memory |
|---|---|---|---|---|---|
| 100 | <5s | <2s | <1s | <1s | <200 MB |
| 500 | <20s | <5s | <2s | <5s | <500 MB |
| 1,000 | <60s | <10s | <5s | <10s | <1,000 MB |

Thresholds are set conservatively to avoid false failures on CI while still catching significant regressions. Run `make benchmark` to execute these tests.

---

## Benchmark Environment

Results in this document were collected on:

- **Platform:** macOS 15.5 (arm64)
- **Processor:** Apple Silicon (arm)
- **Python:** 3.12.12
- **NetworkX backend** with in-memory graph storage
- **Seed:** 42 (deterministic generation)

Your results will vary based on hardware. Use `hckg benchmark` to generate results specific to your environment.

---

For full CLI usage, see [CLI Reference](cli.md). For the Python API, see [Python API Guide](python-api.md).
