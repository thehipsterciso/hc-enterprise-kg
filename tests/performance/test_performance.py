"""Performance regression tests with explicit thresholds.

Run with: make benchmark
Or: poetry run pytest tests/performance/ -v
"""

from __future__ import annotations

import tempfile
import time
from pathlib import Path
from typing import Any

import pytest

from domain.base import EntityType
from graph.knowledge_graph import KnowledgeGraph

# Thresholds per scale (generous to avoid flaky failures on CI).
# These represent "never exceed" ceilings, not expected times.
THRESHOLDS = {
    100: {
        "generation_sec": 5,
        "load_sec": 2,
        "blast_radius_sec": 1,
        "centrality_sec": 1,
        "peak_memory_mb": 200,
    },
    500: {
        "generation_sec": 20,
        "load_sec": 5,
        "blast_radius_sec": 2,
        "centrality_sec": 5,
        "peak_memory_mb": 500,
    },
    1000: {
        "generation_sec": 60,
        "load_sec": 10,
        "blast_radius_sec": 5,
        "centrality_sec": 10,
        "peak_memory_mb": 1000,
    },
}


# --- Generation ---


@pytest.mark.performance
def test_generation_100(graph_100: tuple[KnowledgeGraph, dict[str, Any]]) -> None:
    """Generation at 100 employees should produce entities and relationships."""
    kg, stats = graph_100
    assert stats["entity_count"] > 0
    assert stats["relationship_count"] > 0


@pytest.mark.performance
def test_generation_time_100(memory_tracker) -> None:
    """Generation at 100 employees completes within threshold."""
    from synthetic.orchestrator import SyntheticOrchestrator
    from synthetic.profiles.tech_company import mid_size_tech_company

    tracker = memory_tracker()
    with tracker:
        kg = KnowledgeGraph()
        profile = mid_size_tech_company(employee_count=100)
        orch = SyntheticOrchestrator(kg, profile, seed=99)
        start = time.perf_counter()
        orch.generate()
        elapsed = time.perf_counter() - start

    assert elapsed < THRESHOLDS[100]["generation_sec"], (
        f"Generation took {elapsed:.2f}s, threshold is {THRESHOLDS[100]['generation_sec']}s"
    )
    assert tracker.peak_mb < THRESHOLDS[100]["peak_memory_mb"], (
        f"Peak memory {tracker.peak_mb:.1f}MB exceeds {THRESHOLDS[100]['peak_memory_mb']}MB"
    )


@pytest.mark.performance
def test_generation_time_500(memory_tracker) -> None:
    """Generation at 500 employees completes within threshold."""
    from synthetic.orchestrator import SyntheticOrchestrator
    from synthetic.profiles.tech_company import mid_size_tech_company

    tracker = memory_tracker()
    with tracker:
        kg = KnowledgeGraph()
        profile = mid_size_tech_company(employee_count=500)
        orch = SyntheticOrchestrator(kg, profile, seed=99)
        start = time.perf_counter()
        orch.generate()
        elapsed = time.perf_counter() - start

    assert elapsed < THRESHOLDS[500]["generation_sec"], (
        f"Generation took {elapsed:.2f}s, threshold is {THRESHOLDS[500]['generation_sec']}s"
    )
    assert tracker.peak_mb < THRESHOLDS[500]["peak_memory_mb"], (
        f"Peak memory {tracker.peak_mb:.1f}MB exceeds {THRESHOLDS[500]['peak_memory_mb']}MB"
    )


# --- Load & Export ---


@pytest.mark.performance
def test_load_roundtrip_100(graph_100: tuple[KnowledgeGraph, dict[str, Any]]) -> None:
    """Export + re-import at 100 employees completes within threshold."""
    from export.json_export import JSONExporter
    from ingest.json_ingestor import JSONIngestor

    kg, stats = graph_100

    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
        tmp_path = Path(f.name)

    try:
        JSONExporter().export(kg.engine, tmp_path)

        start = time.perf_counter()
        result = JSONIngestor().ingest(str(tmp_path))
        kg2 = KnowledgeGraph()
        kg2.add_entities_bulk(result.entities)
        kg2.add_relationships_bulk(result.relationships)
        elapsed = time.perf_counter() - start

        assert elapsed < THRESHOLDS[100]["load_sec"], (
            f"Load took {elapsed:.2f}s, threshold is {THRESHOLDS[100]['load_sec']}s"
        )
        assert len(result.entities) == stats["entity_count"]
    finally:
        tmp_path.unlink(missing_ok=True)


# --- Read Operations ---


@pytest.mark.performance
def test_single_lookup_latency(graph_100: tuple[KnowledgeGraph, dict[str, Any]]) -> None:
    """Single entity lookup should be sub-millisecond."""
    kg, _ = graph_100
    entities = kg.list_entities(limit=1)
    entity_id = entities[0].id

    start = time.perf_counter()
    for _ in range(1000):
        kg.get_entity(entity_id)
    elapsed = (time.perf_counter() - start) / 1000

    assert elapsed < 0.001, f"Single lookup took {elapsed*1000:.3f}ms, expected < 1ms"


# --- Traversal ---


@pytest.mark.performance
def test_blast_radius_100(graph_100: tuple[KnowledgeGraph, dict[str, Any]]) -> None:
    """Blast radius at depth 3 for 100 employees within threshold."""
    kg, _ = graph_100
    systems = kg.list_entities(entity_type=EntityType.SYSTEM, limit=1)
    assert systems, "No systems found"

    start = time.perf_counter()
    kg.blast_radius(systems[0].id, max_depth=3)
    elapsed = time.perf_counter() - start

    assert elapsed < THRESHOLDS[100]["blast_radius_sec"], (
        f"Blast radius took {elapsed:.2f}s, threshold is "
        f"{THRESHOLDS[100]['blast_radius_sec']}s"
    )


@pytest.mark.performance
def test_shortest_path_100(graph_100: tuple[KnowledgeGraph, dict[str, Any]]) -> None:
    """Shortest path between two systems should be fast."""
    kg, _ = graph_100
    systems = kg.list_entities(entity_type=EntityType.SYSTEM, limit=2)
    if len(systems) < 2:
        pytest.skip("Not enough systems for shortest path test")

    start = time.perf_counter()
    kg.shortest_path(systems[0].id, systems[1].id)
    elapsed = time.perf_counter() - start

    assert elapsed < 1.0, f"Shortest path took {elapsed:.2f}s, expected < 1s"


# --- Analysis ---


@pytest.mark.performance
def test_degree_centrality_100(graph_100: tuple[KnowledgeGraph, dict[str, Any]]) -> None:
    """Degree centrality at 100 employees within threshold."""
    from analysis.metrics import compute_centrality

    kg, _ = graph_100

    start = time.perf_counter()
    compute_centrality(kg)
    elapsed = time.perf_counter() - start

    assert elapsed < THRESHOLDS[100]["centrality_sec"], (
        f"Centrality took {elapsed:.2f}s, threshold is "
        f"{THRESHOLDS[100]['centrality_sec']}s"
    )


@pytest.mark.performance
def test_betweenness_centrality_500(graph_500: tuple[KnowledgeGraph, dict[str, Any]]) -> None:
    """Betweenness centrality (O(VE)) at 500 employees within threshold."""
    from analysis.metrics import compute_betweenness_centrality

    kg, _ = graph_500

    start = time.perf_counter()
    compute_betweenness_centrality(kg)
    elapsed = time.perf_counter() - start

    assert elapsed < THRESHOLDS[500]["centrality_sec"], (
        f"Betweenness took {elapsed:.2f}s, threshold is "
        f"{THRESHOLDS[500]['centrality_sec']}s"
    )


# --- Scaling ---


@pytest.mark.performance
def test_entity_count_scales(
    graph_100: tuple[KnowledgeGraph, dict[str, Any]],
    graph_500: tuple[KnowledgeGraph, dict[str, Any]],
) -> None:
    """Entity count should scale with employee count."""
    _, stats_100 = graph_100
    _, stats_500 = graph_500

    # 500 employees should produce more entities than 100
    assert stats_500["entity_count"] > stats_100["entity_count"], (
        f"500-employee graph ({stats_500['entity_count']} entities) should have more "
        f"than 100-employee graph ({stats_100['entity_count']} entities)"
    )

    # Ratio should be reasonable (not 1:1, not 1:25)
    ratio = stats_500["entity_count"] / stats_100["entity_count"]
    assert 1.5 < ratio < 10, f"Entity scaling ratio {ratio:.1f} outside expected range"
