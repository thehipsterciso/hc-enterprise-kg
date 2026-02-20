"""Data collector that generates graphs at multiple scales and captures statistics."""

from __future__ import annotations

import time
import tracemalloc
from typing import TYPE_CHECKING, Any

from analysis.charts.models import ChartConfig, ChartDataSet, ScaleSnapshot

if TYPE_CHECKING:
    from collections.abc import Callable


def _get_profile(name: str, employee_count: int) -> Any:
    """Get an organization profile by name."""
    from synthetic.profiles.financial_org import financial_org
    from synthetic.profiles.healthcare_org import healthcare_org
    from synthetic.profiles.tech_company import mid_size_tech_company

    factories: dict[str, Callable[..., Any]] = {
        "tech": mid_size_tech_company,
        "financial": financial_org,
        "healthcare": healthcare_org,
    }
    return factories[name](employee_count=employee_count)


class ScaleDataCollector:
    """Generates graphs at multiple scales and collects comprehensive statistics."""

    def __init__(self, config: ChartConfig) -> None:
        self._config = config

    def collect(self, progress_callback: Callable[[str, int], None] | None = None) -> ChartDataSet:
        """Run generation at all (profile, scale) combinations and collect data."""
        dataset = ChartDataSet(
            profiles=list(self._config.profiles),
            scales=list(self._config.scales),
        )
        for profile_name in self._config.profiles:
            for scale in self._config.scales:
                if progress_callback:
                    progress_callback(profile_name, scale)
                snapshot = self._collect_snapshot(profile_name, scale)
                dataset.snapshots.append(snapshot)
        return dataset

    def _collect_snapshot(self, profile_name: str, scale: int) -> ScaleSnapshot:
        """Generate one graph and capture all statistics."""
        from analysis.metrics import compute_centrality, find_most_connected
        from graph.knowledge_graph import KnowledgeGraph
        from synthetic.orchestrator import SyntheticOrchestrator

        kg = KnowledgeGraph()
        profile = _get_profile(profile_name, scale)
        orchestrator = SyntheticOrchestrator(kg, profile, seed=self._config.seed)

        tracemalloc.start()
        start = time.perf_counter()
        orchestrator.generate()
        elapsed = time.perf_counter() - start
        _, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()

        stats = kg.statistics

        # Quality scores
        quality_scores: dict[str, float] = {}
        qr = orchestrator.quality_report
        if qr:
            quality_scores = {
                "overall_score": qr.overall_score,
                "risk_math_consistency": qr.risk_math_consistency,
                "description_quality": qr.description_quality,
                "tech_stack_coherence": qr.tech_stack_coherence,
                "field_correlation_score": qr.field_correlation_score,
                "encryption_classification_consistency": qr.encryption_classification_consistency,
            }

        # Centrality — top 15 by degree
        centrality_top_n: list[tuple[str, str, float]] = []
        try:
            centrality = compute_centrality(kg)
            top_ids = sorted(centrality.items(), key=lambda x: x[1], reverse=True)[:15]
            for eid, score in top_ids:
                entity = kg.get_entity(eid)
                name = entity.name if entity else eid
                centrality_top_n.append((eid, name, score))
        except Exception:  # noqa: S110
            pass  # centrality may fail on very small or disconnected graphs

        # Most connected — top 15 by raw degree
        most_connected: list[tuple[str, str, int]] = []
        try:
            mc_raw = find_most_connected(kg, top_n=15)
            for eid, degree in mc_raw:
                entity = kg.get_entity(eid)
                name = entity.name if entity else eid
                most_connected.append((eid, name, degree))
        except Exception:  # noqa: S110
            pass

        return ScaleSnapshot(
            profile=profile_name,
            scale=scale,
            entity_count=stats.get("entity_count", 0),
            relationship_count=stats.get("relationship_count", 0),
            entity_types=dict(stats.get("entity_types", {})),
            relationship_types=dict(stats.get("relationship_types", {})),
            density=stats.get("density", 0.0),
            generation_time_sec=elapsed,
            peak_memory_mb=peak / (1024 * 1024),
            quality_scores=quality_scores,
            centrality_top_n=centrality_top_n,
            most_connected=most_connected,
        )
