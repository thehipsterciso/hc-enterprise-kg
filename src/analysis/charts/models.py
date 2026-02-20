"""Data models for the analytics charts module."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class ScaleSnapshot:
    """Statistics captured for one (profile, scale) generation run."""

    profile: str
    scale: int  # employee_count
    entity_count: int = 0
    relationship_count: int = 0
    entity_types: dict[str, int] = field(default_factory=dict)
    relationship_types: dict[str, int] = field(default_factory=dict)
    density: float = 0.0
    generation_time_sec: float = 0.0
    peak_memory_mb: float = 0.0
    quality_scores: dict[str, float] = field(default_factory=dict)
    centrality_top_n: list[tuple[str, str, float]] = field(default_factory=list)
    most_connected: list[tuple[str, str, int]] = field(default_factory=list)


@dataclass
class ChartDataSet:
    """All collected data for chart generation."""

    snapshots: list[ScaleSnapshot] = field(default_factory=list)
    profiles: list[str] = field(default_factory=list)
    scales: list[int] = field(default_factory=list)

    def by_profile(self, profile: str) -> list[ScaleSnapshot]:
        """Get snapshots for a specific profile, sorted by scale."""
        return sorted(
            [s for s in self.snapshots if s.profile == profile],
            key=lambda s: s.scale,
        )

    def at_scale(self, scale: int) -> list[ScaleSnapshot]:
        """Get snapshots across all profiles at a given scale."""
        return [s for s in self.snapshots if s.scale == scale]


@dataclass
class ChartConfig:
    """Configuration for chart generation."""

    output_dir: str = "./charts"
    format: str = "png"
    scales: list[int] = field(default_factory=lambda: [100, 500, 1000, 5000])
    profiles: list[str] = field(default_factory=lambda: ["tech"])
    seed: int = 42
    dpi: int = 150
    # Individual chart toggles
    render_scaling: bool = True
    render_relationships: bool = True
    render_entities: bool = True
    render_performance: bool = True
    render_centrality: bool = True
    render_quality: bool = True
    render_density: bool = True
    render_profile_comparison: bool = True
