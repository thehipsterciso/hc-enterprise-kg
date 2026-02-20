"""Analytics charts for the enterprise knowledge graph.

Auto-generates charts showcasing scaling behavior, entity/relationship
distributions, quality metrics, and performance characteristics.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from analysis.charts.models import ChartConfig, ChartDataSet, ScaleSnapshot

if TYPE_CHECKING:
    from collections.abc import Callable

__all__ = [
    "ChartConfig",
    "ChartDataSet",
    "ScaleSnapshot",
    "generate_all_charts",
]


def generate_all_charts(
    config: ChartConfig | None = None,
    progress_callback: Callable[[str, int], None] | None = None,
) -> list[str]:
    """One-call API: collect data at multiple scales and render all charts.

    Args:
        config: Chart generation configuration. Uses defaults if None.
        progress_callback: Called with (profile, scale) before each generation.

    Returns:
        List of output file paths.
    """
    from analysis.charts.data_collector import ScaleDataCollector
    from analysis.charts.renderer import ChartRenderer

    config = config or ChartConfig()
    collector = ScaleDataCollector(config)
    dataset = collector.collect(progress_callback=progress_callback)
    renderer = ChartRenderer(dataset, config)
    return renderer.render_all()
