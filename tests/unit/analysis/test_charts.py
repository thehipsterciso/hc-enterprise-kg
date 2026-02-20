"""Unit tests for analysis.charts data models and theme."""

from __future__ import annotations

from analysis.charts.models import ChartConfig, ChartDataSet, ScaleSnapshot
from analysis.charts.theme import (
    ENTITY_COLORS,
    ENTITY_TYPE_GROUPS,
    GROUP_COLORS,
    PROFILE_COLORS,
    QUALITY_DIMENSION_LABELS,
)

# ---------------------------------------------------------------------------
# ScaleSnapshot
# ---------------------------------------------------------------------------


class TestScaleSnapshot:
    def test_construction_minimal(self):
        snap = ScaleSnapshot(profile="tech", scale=100)
        assert snap.profile == "tech"
        assert snap.scale == 100
        assert snap.entity_count == 0
        assert snap.entity_types == {}

    def test_construction_full(self):
        snap = ScaleSnapshot(
            profile="financial",
            scale=5000,
            entity_count=1200,
            relationship_count=2400,
            entity_types={"person": 500, "system": 200},
            relationship_types={"works_in": 500},
            density=0.004,
            generation_time_sec=12.5,
            peak_memory_mb=256.0,
            quality_scores={"overall_score": 0.85, "risk_math_consistency": 1.0},
            centrality_top_n=[("id1", "CEO", 0.45)],
            most_connected=[("id2", "ERP System", 42)],
        )
        assert snap.entity_count == 1200
        assert snap.relationship_count == 2400
        assert snap.density == 0.004
        assert snap.quality_scores["overall_score"] == 0.85
        assert len(snap.centrality_top_n) == 1
        assert snap.most_connected[0][2] == 42

    def test_defaults_are_independent(self):
        """Mutable defaults should not be shared across instances."""
        a = ScaleSnapshot(profile="tech", scale=100)
        b = ScaleSnapshot(profile="tech", scale=200)
        a.entity_types["person"] = 50
        assert "person" not in b.entity_types


# ---------------------------------------------------------------------------
# ChartDataSet
# ---------------------------------------------------------------------------


def _make_dataset() -> ChartDataSet:
    """Helper: create a dataset with 2 profiles x 3 scales."""
    snapshots = []
    for profile in ["tech", "financial"]:
        for scale in [100, 500, 1000]:
            snapshots.append(
                ScaleSnapshot(
                    profile=profile,
                    scale=scale,
                    entity_count=scale * 4,
                    relationship_count=scale * 7,
                )
            )
    return ChartDataSet(
        snapshots=snapshots,
        profiles=["tech", "financial"],
        scales=[100, 500, 1000],
    )


class TestChartDataSet:
    def test_by_profile_filters_correctly(self):
        ds = _make_dataset()
        tech = ds.by_profile("tech")
        assert len(tech) == 3
        assert all(s.profile == "tech" for s in tech)

    def test_by_profile_sorted_by_scale(self):
        ds = _make_dataset()
        tech = ds.by_profile("tech")
        scales = [s.scale for s in tech]
        assert scales == sorted(scales)

    def test_by_profile_empty_for_unknown(self):
        ds = _make_dataset()
        assert ds.by_profile("healthcare") == []

    def test_at_scale_filters_correctly(self):
        ds = _make_dataset()
        at_500 = ds.at_scale(500)
        assert len(at_500) == 2
        assert all(s.scale == 500 for s in at_500)
        profiles = {s.profile for s in at_500}
        assert profiles == {"tech", "financial"}

    def test_at_scale_empty_for_unknown(self):
        ds = _make_dataset()
        assert ds.at_scale(9999) == []

    def test_empty_dataset(self):
        ds = ChartDataSet()
        assert ds.snapshots == []
        assert ds.by_profile("tech") == []
        assert ds.at_scale(100) == []


# ---------------------------------------------------------------------------
# ChartConfig
# ---------------------------------------------------------------------------


class TestChartConfig:
    def test_defaults(self):
        cfg = ChartConfig()
        assert cfg.output_dir == "./charts"
        assert cfg.format == "png"
        assert cfg.scales == [100, 500, 1000, 5000]
        assert cfg.profiles == ["tech"]
        assert cfg.seed == 42
        assert cfg.dpi == 150

    def test_all_chart_toggles_default_true(self):
        cfg = ChartConfig()
        assert cfg.render_scaling is True
        assert cfg.render_relationships is True
        assert cfg.render_entities is True
        assert cfg.render_performance is True
        assert cfg.render_centrality is True
        assert cfg.render_quality is True
        assert cfg.render_density is True
        assert cfg.render_profile_comparison is True

    def test_custom_config(self):
        cfg = ChartConfig(
            output_dir="/tmp/out",
            format="svg",
            scales=[100, 200],
            profiles=["tech", "healthcare"],
            render_quality=False,
        )
        assert cfg.output_dir == "/tmp/out"
        assert cfg.format == "svg"
        assert cfg.scales == [100, 200]
        assert cfg.profiles == ["tech", "healthcare"]
        assert cfg.render_quality is False

    def test_defaults_are_independent(self):
        a = ChartConfig()
        b = ChartConfig()
        a.scales.append(99999)
        assert 99999 not in b.scales


# ---------------------------------------------------------------------------
# Theme
# ---------------------------------------------------------------------------


class TestTheme:
    def test_entity_colors_has_30_types(self):
        assert len(ENTITY_COLORS) == 30

    def test_profile_colors_has_3_profiles(self):
        assert set(PROFILE_COLORS.keys()) == {"tech", "financial", "healthcare"}

    def test_entity_type_groups_cover_all_30_types(self):
        all_types = set()
        for types in ENTITY_TYPE_GROUPS.values():
            all_types.update(types)
        assert len(all_types) == 30
        # Every type should have a color
        for t in all_types:
            assert t in ENTITY_COLORS, f"{t} missing from ENTITY_COLORS"

    def test_group_colors_match_groups(self):
        assert set(GROUP_COLORS.keys()) == set(ENTITY_TYPE_GROUPS.keys())

    def test_quality_dimension_labels_has_5(self):
        assert len(QUALITY_DIMENSION_LABELS) == 5
