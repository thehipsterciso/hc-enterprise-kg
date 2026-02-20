"""Performance benchmarking suite for the enterprise knowledge graph.

Measures 9 performance dimensions across profiles and scales:
generation, loading, writes, reads, traversal, analysis, export, search, memory.
"""

from __future__ import annotations

import json
import os
import platform
import tempfile
import time
import tracemalloc
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


@dataclass
class BenchmarkResult:
    """Single benchmark measurement."""

    operation: str
    scale: int
    profile: str
    elapsed_sec: float
    peak_memory_mb: float = 0.0
    entity_count: int = 0
    relationship_count: int = 0
    extra: dict[str, Any] = field(default_factory=dict)


@dataclass
class BenchmarkReport:
    """Collection of benchmark results with system info."""

    results: list[BenchmarkResult] = field(default_factory=list)
    system_info: dict[str, str] = field(default_factory=dict)
    timestamp: str = ""

    def to_markdown(self) -> str:
        """Render report as markdown tables."""
        lines = [
            "# Performance Benchmark Report",
            "",
            f"**Generated:** {self.timestamp}",
            "",
            "## System Information",
            "",
        ]
        for k, v in self.system_info.items():
            lines.append(f"- **{k}:** {v}")
        lines.append("")

        # Group results by operation category
        categories: dict[str, list[BenchmarkResult]] = {}
        for r in self.results:
            cat = r.operation.split(":")[0] if ":" in r.operation else r.operation
            categories.setdefault(cat, []).append(r)

        # Generation summary table
        gen_results = [r for r in self.results if r.operation == "generation"]
        if gen_results:
            lines.extend(
                [
                    "## Synthetic Generation",
                    "",
                    "| Profile | Employees | Time (s) | Entities | Relationships | "
                    "Peak Memory (MB) | Quality Score |",
                    "|---|---|---|---|---|---|---|",
                ]
            )
            for r in sorted(gen_results, key=lambda x: (x.profile, x.scale)):
                quality = r.extra.get("quality_score", "N/A")
                lines.append(
                    f"| {r.profile} | {r.scale:,} | {r.elapsed_sec:.2f} | "
                    f"{r.entity_count:,} | {r.relationship_count:,} | "
                    f"{r.peak_memory_mb:.1f} | {quality} |"
                )
            lines.append("")

        # Operation latency table
        ops = [r for r in self.results if r.operation != "generation"]
        if ops:
            # Group by scale+profile for a per-scale table
            by_scale: dict[tuple[str, int], list[BenchmarkResult]] = {}
            for r in ops:
                by_scale.setdefault((r.profile, r.scale), []).append(r)

            lines.extend(
                [
                    "## Operation Latency",
                    "",
                    "| Profile | Scale | Operation | Time (s) | Details |",
                    "|---|---|---|---|---|",
                ]
            )
            for (prof, scale), results in sorted(by_scale.items()):
                for r in sorted(results, key=lambda x: x.operation):
                    details = ", ".join(f"{k}={v}" for k, v in r.extra.items()) if r.extra else ""
                    lines.append(
                        f"| {prof} | {scale:,} | {r.operation} | {r.elapsed_sec:.4f} | {details} |"
                    )
            lines.append("")

        return "\n".join(lines)

    def to_json(self) -> str:
        """Render report as structured JSON."""
        data = {
            "timestamp": self.timestamp,
            "system_info": self.system_info,
            "results": [
                {
                    "operation": r.operation,
                    "scale": r.scale,
                    "profile": r.profile,
                    "elapsed_sec": round(r.elapsed_sec, 4),
                    "peak_memory_mb": round(r.peak_memory_mb, 2),
                    "entity_count": r.entity_count,
                    "relationship_count": r.relationship_count,
                    "extra": r.extra,
                }
                for r in self.results
            ],
        }
        return json.dumps(data, indent=2)


def _get_system_info() -> dict[str, str]:
    """Collect system information for benchmark context."""
    import sys

    info = {
        "Python": sys.version.split()[0],
        "Platform": platform.platform(),
        "Processor": platform.processor() or "unknown",
        "Machine": platform.machine(),
    }
    try:
        import psutil

        mem = psutil.virtual_memory()
        info["Total RAM"] = f"{mem.total / (1024**3):.1f} GB"
    except ImportError:
        info["Total RAM"] = "unknown (install psutil for detection)"
    return info


def _get_profile(name: str, employee_count: int) -> Any:
    """Get an organization profile by name."""
    from synthetic.profiles.financial_org import financial_org
    from synthetic.profiles.healthcare_org import healthcare_org
    from synthetic.profiles.tech_company import mid_size_tech_company

    factories = {
        "tech": mid_size_tech_company,
        "financial": financial_org,
        "healthcare": healthcare_org,
    }
    return factories[name](employee_count=employee_count)


class BenchmarkSuite:
    """Run comprehensive performance benchmarks across profiles and scales."""

    def __init__(
        self,
        profiles: list[str] | None = None,
        scales: list[int] | None = None,
        seed: int = 42,
    ) -> None:
        self.profiles = profiles or ["tech"]
        self.scales = scales or [100, 500]
        self.seed = seed
        self._results: list[BenchmarkResult] = []
        # Cache of (profile, scale) -> (kg, stats) for reuse across benchmarks
        self._graphs: dict[tuple[str, int], Any] = {}

    def _generate_graph(self, profile_name: str, scale: int) -> Any:
        """Generate a graph and cache it. Returns (kg, stats_dict)."""
        key = (profile_name, scale)
        if key in self._graphs:
            return self._graphs[key]

        from graph.knowledge_graph import KnowledgeGraph
        from synthetic.orchestrator import SyntheticOrchestrator

        kg = KnowledgeGraph()
        profile = _get_profile(profile_name, scale)
        orchestrator = SyntheticOrchestrator(kg, profile, seed=self.seed)

        tracemalloc.start()
        start = time.perf_counter()
        counts = orchestrator.generate()
        elapsed = time.perf_counter() - start
        _, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()

        stats = kg.statistics
        quality_score = "N/A"
        if orchestrator.quality_report:
            quality_score = f"{orchestrator.quality_report.overall_score:.2f}"

        self._results.append(
            BenchmarkResult(
                operation="generation",
                scale=scale,
                profile=profile_name,
                elapsed_sec=elapsed,
                peak_memory_mb=peak / (1024 * 1024),
                entity_count=stats.get("entity_count", 0),
                relationship_count=stats.get("relationship_count", 0),
                extra={
                    "quality_score": quality_score,
                    "entity_types": len(stats.get("entity_types", {})),
                    "relationship_types": len(stats.get("relationship_types", {})),
                    "entities_per_sec": int(stats.get("entity_count", 0) / max(elapsed, 0.001)),
                },
            )
        )

        self._graphs[key] = (kg, stats, counts)
        return kg, stats, counts

    def run_generation(self) -> list[BenchmarkResult]:
        """Benchmark synthetic generation across all profiles and scales."""
        start_len = len(self._results)
        for profile_name in self.profiles:
            for scale in self.scales:
                self._generate_graph(profile_name, scale)
        return self._results[start_len:]

    def run_load(self) -> list[BenchmarkResult]:
        """Benchmark graph export + load roundtrip."""
        from export.json_export import JSONExporter
        from graph.knowledge_graph import KnowledgeGraph
        from ingest.json_ingestor import JSONIngestor

        results = []
        for profile_name in self.profiles:
            for scale in self.scales:
                kg, stats, _ = self._generate_graph(profile_name, scale)

                with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
                    tmp_path = Path(f.name)

                try:
                    # Export
                    start = time.perf_counter()
                    JSONExporter().export(kg.engine, tmp_path)
                    export_time = time.perf_counter() - start
                    file_size_mb = os.path.getsize(tmp_path) / (1024 * 1024)

                    results.append(
                        BenchmarkResult(
                            operation="export:json",
                            scale=scale,
                            profile=profile_name,
                            elapsed_sec=export_time,
                            entity_count=stats.get("entity_count", 0),
                            relationship_count=stats.get("relationship_count", 0),
                            extra={"file_size_mb": round(file_size_mb, 2)},
                        )
                    )

                    # Load (parse + ingest)
                    ingestor = JSONIngestor()
                    start = time.perf_counter()
                    result = ingestor.ingest(str(tmp_path))
                    parse_time = time.perf_counter() - start

                    # Bulk add
                    kg2 = KnowledgeGraph()
                    start = time.perf_counter()
                    kg2.add_entities_bulk(result.entities)
                    entity_add_time = time.perf_counter() - start

                    start = time.perf_counter()
                    kg2.add_relationships_bulk(result.relationships)
                    rel_add_time = time.perf_counter() - start

                    total_load = parse_time + entity_add_time + rel_add_time
                    results.append(
                        BenchmarkResult(
                            operation="load:total",
                            scale=scale,
                            profile=profile_name,
                            elapsed_sec=total_load,
                            entity_count=len(result.entities),
                            relationship_count=len(result.relationships),
                            extra={
                                "parse_sec": round(parse_time, 4),
                                "entity_add_sec": round(entity_add_time, 4),
                                "rel_add_sec": round(rel_add_time, 4),
                            },
                        )
                    )
                finally:
                    tmp_path.unlink(missing_ok=True)

        self._results.extend(results)
        return results

    def run_reads(self) -> list[BenchmarkResult]:
        """Benchmark read operations."""
        from domain.base import EntityType

        results = []
        for profile_name in self.profiles:
            for scale in self.scales:
                kg, stats, _ = self._generate_graph(profile_name, scale)
                entities = kg.list_entities(limit=1)
                if not entities:
                    continue
                entity_id = entities[0].id

                # Single entity lookup
                start = time.perf_counter()
                for _ in range(100):
                    kg.get_entity(entity_id)
                elapsed = (time.perf_counter() - start) / 100
                results.append(
                    BenchmarkResult(
                        operation="read:single_lookup",
                        scale=scale,
                        profile=profile_name,
                        elapsed_sec=elapsed,
                        extra={"iterations": 100, "per_call_ms": round(elapsed * 1000, 3)},
                    )
                )

                # Filtered list
                start = time.perf_counter()
                kg.list_entities(entity_type=EntityType.PERSON)
                elapsed = time.perf_counter() - start
                results.append(
                    BenchmarkResult(
                        operation="read:list_filtered",
                        scale=scale,
                        profile=profile_name,
                        elapsed_sec=elapsed,
                    )
                )

                # Query builder
                start = time.perf_counter()
                kg.query().entities(EntityType.SYSTEM).execute()
                elapsed = time.perf_counter() - start
                results.append(
                    BenchmarkResult(
                        operation="read:query_builder",
                        scale=scale,
                        profile=profile_name,
                        elapsed_sec=elapsed,
                    )
                )

        self._results.extend(results)
        return results

    def run_traversal(self) -> list[BenchmarkResult]:
        """Benchmark graph traversal operations."""
        from domain.base import EntityType

        results = []
        for profile_name in self.profiles:
            for scale in self.scales:
                kg, _, _ = self._generate_graph(profile_name, scale)
                systems = kg.list_entities(entity_type=EntityType.SYSTEM, limit=2)
                if not systems:
                    continue

                # Neighbors
                start = time.perf_counter()
                kg.neighbors(systems[0].id)
                elapsed = time.perf_counter() - start
                results.append(
                    BenchmarkResult(
                        operation="traversal:neighbors",
                        scale=scale,
                        profile=profile_name,
                        elapsed_sec=elapsed,
                    )
                )

                # Shortest path
                if len(systems) >= 2:
                    start = time.perf_counter()
                    kg.shortest_path(systems[0].id, systems[1].id)
                    elapsed = time.perf_counter() - start
                    results.append(
                        BenchmarkResult(
                            operation="traversal:shortest_path",
                            scale=scale,
                            profile=profile_name,
                            elapsed_sec=elapsed,
                        )
                    )

                # Blast radius
                start = time.perf_counter()
                kg.blast_radius(systems[0].id, max_depth=3)
                elapsed = time.perf_counter() - start
                results.append(
                    BenchmarkResult(
                        operation="traversal:blast_radius",
                        scale=scale,
                        profile=profile_name,
                        elapsed_sec=elapsed,
                        extra={"max_depth": 3},
                    )
                )

        self._results.extend(results)
        return results

    def run_analysis(self) -> list[BenchmarkResult]:
        """Benchmark analysis functions."""
        from analysis.metrics import (
            compute_betweenness_centrality,
            compute_centrality,
            compute_pagerank,
            compute_risk_score,
            find_most_connected,
        )
        from domain.base import EntityType

        results = []
        for profile_name in self.profiles:
            for scale in self.scales:
                kg, _, _ = self._generate_graph(profile_name, scale)

                for name, fn in [
                    ("analysis:degree_centrality", lambda _kg=kg: compute_centrality(_kg)),
                    ("analysis:betweenness", lambda _kg=kg: compute_betweenness_centrality(_kg)),
                    ("analysis:pagerank", lambda _kg=kg: compute_pagerank(_kg)),
                    ("analysis:most_connected", lambda _kg=kg: find_most_connected(_kg, top_n=10)),
                ]:
                    start = time.perf_counter()
                    try:
                        fn()
                    except (ImportError, ModuleNotFoundError):
                        # Some analysis functions need optional deps (e.g. scipy)
                        results.append(
                            BenchmarkResult(
                                operation=name,
                                scale=scale,
                                profile=profile_name,
                                elapsed_sec=0.0,
                                extra={"skipped": "missing optional dependency"},
                            )
                        )
                        continue
                    elapsed = time.perf_counter() - start
                    results.append(
                        BenchmarkResult(
                            operation=name,
                            scale=scale,
                            profile=profile_name,
                            elapsed_sec=elapsed,
                        )
                    )

                # Risk score (needs a system entity)
                systems = kg.list_entities(entity_type=EntityType.SYSTEM, limit=1)
                if systems:
                    start = time.perf_counter()
                    compute_risk_score(kg, systems[0].id)
                    elapsed = time.perf_counter() - start
                    results.append(
                        BenchmarkResult(
                            operation="analysis:risk_score",
                            scale=scale,
                            profile=profile_name,
                            elapsed_sec=elapsed,
                        )
                    )

        self._results.extend(results)
        return results

    def run_search(self) -> list[BenchmarkResult]:
        """Benchmark fuzzy name search (mirrors MCP search_entities tool)."""
        try:
            from rapidfuzz import fuzz, process
        except ImportError:
            return []

        results = []
        for profile_name in self.profiles:
            for scale in self.scales:
                kg, _, _ = self._generate_graph(profile_name, scale)

                start = time.perf_counter()
                all_entities = kg.list_entities()
                names = list({e.name for e in all_entities})
                process.extract("server", names, scorer=fuzz.WRatio, limit=20)
                elapsed = time.perf_counter() - start
                results.append(
                    BenchmarkResult(
                        operation="search:fuzzy",
                        scale=scale,
                        profile=profile_name,
                        elapsed_sec=elapsed,
                        extra={"candidate_names": len(names)},
                    )
                )

        self._results.extend(results)
        return results

    def run_all(self, progress_callback: Any = None) -> BenchmarkReport:
        """Run all benchmarks and produce a complete report."""
        self._results = []
        self._graphs = {}

        phases = [
            ("Generation", self.run_generation),
            ("Load & Export", self.run_load),
            ("Reads", self.run_reads),
            ("Traversal", self.run_traversal),
            ("Analysis", self.run_analysis),
            ("Search", self.run_search),
        ]

        for phase_name, phase_fn in phases:
            if progress_callback:
                progress_callback(phase_name)
            phase_fn()

        return BenchmarkReport(
            results=self._results,
            system_info=_get_system_info(),
            timestamp=datetime.now(UTC).strftime("%Y-%m-%d %H:%M:%S UTC"),
        )
