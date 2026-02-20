"""Shared fixtures for performance tests."""

from __future__ import annotations

import tracemalloc
from typing import Any

import pytest

from graph.knowledge_graph import KnowledgeGraph
from synthetic.orchestrator import SyntheticOrchestrator
from synthetic.profiles.tech_company import mid_size_tech_company

SEED = 42

# Cache generated graphs across tests in the same session
_graph_cache: dict[int, tuple[KnowledgeGraph, dict[str, Any]]] = {}


def _get_graph(scale: int) -> tuple[KnowledgeGraph, dict[str, Any]]:
    """Generate or retrieve a cached tech profile graph at the given scale."""
    if scale not in _graph_cache:
        kg = KnowledgeGraph()
        profile = mid_size_tech_company(employee_count=scale)
        orchestrator = SyntheticOrchestrator(kg, profile, seed=SEED)
        orchestrator.generate()
        stats = kg.statistics
        _graph_cache[scale] = (kg, stats)
    return _graph_cache[scale]


@pytest.fixture(scope="session")
def graph_100() -> tuple[KnowledgeGraph, dict[str, Any]]:
    """Tech profile graph at 100 employees."""
    return _get_graph(100)


@pytest.fixture(scope="session")
def graph_500() -> tuple[KnowledgeGraph, dict[str, Any]]:
    """Tech profile graph at 500 employees."""
    return _get_graph(500)


@pytest.fixture(scope="session")
def graph_1000() -> tuple[KnowledgeGraph, dict[str, Any]]:
    """Tech profile graph at 1000 employees."""
    return _get_graph(1000)


@pytest.fixture
def memory_tracker():
    """Context manager fixture for tracking peak memory."""

    class Tracker:
        def __init__(self):
            self.peak_mb = 0.0

        def __enter__(self):
            tracemalloc.start()
            return self

        def __exit__(self, *args):
            _, peak = tracemalloc.get_traced_memory()
            tracemalloc.stop()
            self.peak_mb = peak / (1024 * 1024)

    return Tracker
