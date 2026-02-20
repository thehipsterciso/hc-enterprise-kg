"""Unit tests for analysis.charts data models and theme."""

from __future__ import annotations

from pathlib import Path

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


# ---------------------------------------------------------------------------
# ScaleDataCollector
# ---------------------------------------------------------------------------


class TestScaleDataCollector:
    def test_collect_single_snapshot(self):
        """Collector should produce one snapshot for one (profile, scale)."""
        from analysis.charts.data_collector import ScaleDataCollector

        cfg = ChartConfig(profiles=["tech"], scales=[100], seed=42)
        collector = ScaleDataCollector(cfg)
        dataset = collector.collect()

        assert len(dataset.snapshots) == 1
        snap = dataset.snapshots[0]
        assert snap.profile == "tech"
        assert snap.scale == 100

    def test_snapshot_populates_entity_types(self):
        """Snapshot should have multiple entity types with non-zero counts."""
        from analysis.charts.data_collector import ScaleDataCollector

        cfg = ChartConfig(profiles=["tech"], scales=[100], seed=42)
        collector = ScaleDataCollector(cfg)
        dataset = collector.collect()

        snap = dataset.snapshots[0]
        assert snap.entity_count > 0
        assert snap.relationship_count > 0
        assert len(snap.entity_types) > 0
        assert len(snap.relationship_types) > 0
        assert snap.density > 0

    def test_snapshot_populates_quality_scores(self):
        """Snapshot should have all 5 quality dimensions plus overall."""
        from analysis.charts.data_collector import ScaleDataCollector

        cfg = ChartConfig(profiles=["tech"], scales=[100], seed=42)
        collector = ScaleDataCollector(cfg)
        dataset = collector.collect()

        snap = dataset.snapshots[0]
        assert "overall_score" in snap.quality_scores
        assert "risk_math_consistency" in snap.quality_scores
        assert "description_quality" in snap.quality_scores
        assert "tech_stack_coherence" in snap.quality_scores
        assert "field_correlation_score" in snap.quality_scores
        assert "encryption_classification_consistency" in snap.quality_scores

    def test_snapshot_populates_centrality(self):
        """Snapshot should have centrality data."""
        from analysis.charts.data_collector import ScaleDataCollector

        cfg = ChartConfig(profiles=["tech"], scales=[100], seed=42)
        collector = ScaleDataCollector(cfg)
        dataset = collector.collect()

        snap = dataset.snapshots[0]
        assert len(snap.centrality_top_n) > 0
        # Each entry is (id, name, score)
        eid, name, score = snap.centrality_top_n[0]
        assert isinstance(eid, str)
        assert isinstance(name, str)
        assert isinstance(score, float)

    def test_snapshot_populates_most_connected(self):
        """Snapshot should have most-connected data."""
        from analysis.charts.data_collector import ScaleDataCollector

        cfg = ChartConfig(profiles=["tech"], scales=[100], seed=42)
        collector = ScaleDataCollector(cfg)
        dataset = collector.collect()

        snap = dataset.snapshots[0]
        assert len(snap.most_connected) > 0
        eid, name, degree = snap.most_connected[0]
        assert isinstance(degree, int)
        assert degree > 0

    def test_snapshot_populates_timing(self):
        """Snapshot should have non-zero generation time and memory."""
        from analysis.charts.data_collector import ScaleDataCollector

        cfg = ChartConfig(profiles=["tech"], scales=[100], seed=42)
        collector = ScaleDataCollector(cfg)
        dataset = collector.collect()

        snap = dataset.snapshots[0]
        assert snap.generation_time_sec > 0
        assert snap.peak_memory_mb > 0

    def test_collect_multiple_scales(self):
        """Collector should produce snapshots for each scale."""
        from analysis.charts.data_collector import ScaleDataCollector

        cfg = ChartConfig(profiles=["tech"], scales=[100, 200], seed=42)
        collector = ScaleDataCollector(cfg)
        dataset = collector.collect()

        assert len(dataset.snapshots) == 2
        assert dataset.snapshots[0].scale == 100
        assert dataset.snapshots[1].scale == 200

    def test_progress_callback_called(self):
        """Progress callback should be called for each (profile, scale)."""
        from analysis.charts.data_collector import ScaleDataCollector

        cfg = ChartConfig(profiles=["tech"], scales=[100], seed=42)
        collector = ScaleDataCollector(cfg)
        calls: list[tuple[str, int]] = []
        dataset = collector.collect(progress_callback=lambda p, s: calls.append((p, s)))

        assert len(calls) == 1
        assert calls[0] == ("tech", 100)
        assert len(dataset.snapshots) == 1

    def test_dataset_metadata(self):
        """Dataset should carry profiles and scales metadata."""
        from analysis.charts.data_collector import ScaleDataCollector

        cfg = ChartConfig(profiles=["tech", "financial"], scales=[100], seed=42)
        collector = ScaleDataCollector(cfg)
        dataset = collector.collect()

        assert dataset.profiles == ["tech", "financial"]
        assert dataset.scales == [100]
        assert len(dataset.snapshots) == 2


# ---------------------------------------------------------------------------
# ChartRenderer
# ---------------------------------------------------------------------------


def _make_renderer_dataset() -> ChartDataSet:
    """Create a small dataset suitable for renderer tests."""
    snapshots = []
    for scale in [100, 500]:
        snapshots.append(
            ScaleSnapshot(
                profile="tech",
                scale=scale,
                entity_count=scale * 4,
                relationship_count=scale * 7,
                entity_types={
                    "person": scale,
                    "department": max(3, scale // 30),
                    "role": max(5, scale // 10),
                    "system": max(10, scale // 5),
                    "network": 3,
                    "data_asset": max(5, scale // 8),
                    "policy": 5,
                    "vendor": max(3, scale // 20),
                    "location": 3,
                    "vulnerability": max(5, scale // 10),
                    "threat_actor": 3,
                    "incident": 2,
                    "regulation": 5,
                    "control": 8,
                    "risk": 6,
                    "threat": 4,
                    "integration": max(3, scale // 15),
                    "data_domain": 4,
                    "data_flow": max(3, scale // 20),
                    "organizational_unit": 3,
                    "business_capability": 5,
                    "site": 3,
                    "geography": 3,
                    "jurisdiction": 3,
                    "product_portfolio": 2,
                    "product": 5,
                    "market_segment": 3,
                    "customer": max(3, scale // 15),
                    "contract": max(3, scale // 20),
                    "initiative": 3,
                },
                relationship_types={"works_in": scale, "manages": scale // 10},
                density=0.005 - (scale * 0.000001),
                generation_time_sec=scale * 0.01,
                peak_memory_mb=scale * 0.1,
                quality_scores={
                    "overall_score": 0.85,
                    "risk_math_consistency": 1.0,
                    "description_quality": 0.9,
                    "tech_stack_coherence": 0.8,
                    "field_correlation_score": 0.75,
                    "encryption_classification_consistency": 0.7,
                },
                centrality_top_n=[("id1", "CEO", 0.45), ("id2", "CTO", 0.38)],
                most_connected=[("id3", "ERP", 42), ("id4", "AD", 35)],
            )
        )
    return ChartDataSet(snapshots=snapshots, profiles=["tech"], scales=[100, 500])


class TestChartRenderer:
    def test_render_scaling_curves_creates_file(self, tmp_path):
        """render_scaling_curves() should produce a PNG file."""
        from analysis.charts.renderer import ChartRenderer

        dataset = _make_renderer_dataset()
        cfg = ChartConfig(output_dir=str(tmp_path), format="png")
        renderer = ChartRenderer(dataset, cfg)
        path = renderer.render_scaling_curves()

        assert Path(path).exists()
        assert path.endswith(".png")
        assert Path(path).stat().st_size > 0

    def test_render_entity_distribution_creates_file(self, tmp_path):
        """render_entity_distribution() should produce a PNG file."""
        from analysis.charts.renderer import ChartRenderer

        dataset = _make_renderer_dataset()
        cfg = ChartConfig(output_dir=str(tmp_path), format="png")
        renderer = ChartRenderer(dataset, cfg)
        path = renderer.render_entity_distribution()

        assert Path(path).exists()
        assert path.endswith(".png")

    def test_render_with_svg_format(self, tmp_path):
        """SVG format should produce .svg files."""
        from analysis.charts.renderer import ChartRenderer

        dataset = _make_renderer_dataset()
        cfg = ChartConfig(output_dir=str(tmp_path), format="svg")
        renderer = ChartRenderer(dataset, cfg)
        path = renderer.render_scaling_curves()

        assert path.endswith(".svg")
        assert Path(path).exists()

    def test_render_all_returns_file_list(self, tmp_path):
        """render_all() should return list of created file paths."""
        from analysis.charts.renderer import ChartRenderer

        dataset = _make_renderer_dataset()
        cfg = ChartConfig(output_dir=str(tmp_path), format="png")
        renderer = ChartRenderer(dataset, cfg)
        paths = renderer.render_all()

        assert len(paths) == 5  # scaling + entity + relationship + performance + density
        for p in paths:
            assert Path(p).exists()

    def test_render_creates_output_directory(self, tmp_path):
        """render_all() should create the output directory if needed."""
        from analysis.charts.renderer import ChartRenderer

        out_dir = tmp_path / "nested" / "output"
        dataset = _make_renderer_dataset()
        cfg = ChartConfig(output_dir=str(out_dir), format="png")
        renderer = ChartRenderer(dataset, cfg)
        paths = renderer.render_all()

        assert out_dir.exists()
        assert len(paths) > 0

    def test_render_respects_chart_toggles(self, tmp_path):
        """Disabled charts should not be rendered."""
        from analysis.charts.renderer import ChartRenderer

        dataset = _make_renderer_dataset()
        cfg = ChartConfig(
            output_dir=str(tmp_path),
            format="png",
            render_scaling=False,
            render_entities=True,
        )
        renderer = ChartRenderer(dataset, cfg)
        paths = renderer.render_all()

        assert len(paths) == 4  # entity + relationship + performance + density
        assert "entity_distribution" in paths[0]

    def test_render_relationship_distribution_creates_file(self, tmp_path):
        """render_relationship_distribution() should produce a PNG file."""
        from analysis.charts.renderer import ChartRenderer

        dataset = _make_renderer_dataset()
        cfg = ChartConfig(output_dir=str(tmp_path), format="png")
        renderer = ChartRenderer(dataset, cfg)
        path = renderer.render_relationship_distribution()

        assert Path(path).exists()
        assert "relationship_distribution" in path

    def test_render_profile_comparison_creates_file(self, tmp_path):
        """render_profile_comparison() should produce a PNG with 2+ profiles."""
        from analysis.charts.renderer import ChartRenderer

        # Need multi-profile dataset
        snapshots = []
        for profile in ["tech", "financial"]:
            snapshots.append(
                ScaleSnapshot(
                    profile=profile,
                    scale=500,
                    entity_count=2000 if profile == "tech" else 1800,
                    relationship_count=3500 if profile == "tech" else 3200,
                    entity_types={"person": 500},
                    relationship_types={"works_in": 500},
                    density=0.004,
                )
            )
        dataset = ChartDataSet(
            snapshots=snapshots, profiles=["tech", "financial"], scales=[500]
        )
        cfg = ChartConfig(output_dir=str(tmp_path), format="png")
        renderer = ChartRenderer(dataset, cfg)
        path = renderer.render_profile_comparison()

        assert Path(path).exists()
        assert "profile_comparison" in path

    def test_render_profile_comparison_skipped_single_profile(self, tmp_path):
        """Profile comparison should not appear in render_all() with single profile."""
        from analysis.charts.renderer import ChartRenderer

        dataset = _make_renderer_dataset()  # single profile
        cfg = ChartConfig(output_dir=str(tmp_path), format="png")
        renderer = ChartRenderer(dataset, cfg)
        paths = renderer.render_all()

        filenames = [Path(p).name for p in paths]
        assert not any("profile_comparison" in f for f in filenames)

    def test_render_performance_scaling_creates_file(self, tmp_path):
        """render_performance_scaling() should produce a PNG file."""
        from analysis.charts.renderer import ChartRenderer

        dataset = _make_renderer_dataset()
        cfg = ChartConfig(output_dir=str(tmp_path), format="png")
        renderer = ChartRenderer(dataset, cfg)
        path = renderer.render_performance_scaling()

        assert Path(path).exists()
        assert "performance_scaling" in Path(path).name

    def test_render_density_vs_scale_creates_file(self, tmp_path):
        """render_density_vs_scale() should produce a PNG file."""
        from analysis.charts.renderer import ChartRenderer

        dataset = _make_renderer_dataset()
        cfg = ChartConfig(output_dir=str(tmp_path), format="png")
        renderer = ChartRenderer(dataset, cfg)
        path = renderer.render_density_vs_scale()

        assert Path(path).exists()
        assert "density_vs_scale" in Path(path).name
