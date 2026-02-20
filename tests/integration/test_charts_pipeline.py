"""Integration tests for the analytics charts pipeline."""

from __future__ import annotations

from pathlib import Path

import pytest
from click.testing import CliRunner


@pytest.mark.integration
class TestChartsPipeline:
    def test_full_pipeline_single_profile(self, tmp_path):
        """End-to-end: collect data at 100 employees, render all charts."""
        from analysis.charts import ChartConfig, generate_all_charts

        config = ChartConfig(
            output_dir=str(tmp_path),
            format="png",
            scales=[100],
            profiles=["tech"],
            seed=42,
        )
        paths = generate_all_charts(config)

        # Should produce 7 charts (no profile_comparison for single profile)
        assert len(paths) == 7
        for p in paths:
            fp = Path(p)
            assert fp.exists()
            assert fp.stat().st_size > 0
            assert fp.suffix == ".png"

        # Verify expected filenames
        filenames = {Path(p).name for p in paths}
        assert "scaling_curves.png" in filenames
        assert "entity_distribution_tech.png" in filenames
        assert "relationship_distribution_tech.png" in filenames
        assert "performance_scaling.png" in filenames
        assert "density_vs_scale.png" in filenames
        assert "centrality_tech.png" in filenames
        assert "quality_radar.png" in filenames

    def test_full_pipeline_multi_profile(self, tmp_path):
        """Multi-profile pipeline should include profile comparison chart."""
        from analysis.charts import ChartConfig, generate_all_charts

        config = ChartConfig(
            output_dir=str(tmp_path),
            format="png",
            scales=[100],
            profiles=["tech", "financial"],
            seed=42,
        )
        paths = generate_all_charts(config)

        # Should produce 8 charts (includes profile_comparison)
        assert len(paths) == 8
        filenames = {Path(p).name for p in paths}
        assert "profile_comparison.png" in filenames

    def test_cli_end_to_end(self, tmp_path):
        """hckg charts CLI produces output files."""
        from cli.charts_cmd import charts

        runner = CliRunner()
        result = runner.invoke(
            charts,
            [
                "--scales",
                "100",
                "--profiles",
                "tech",
                "--output",
                str(tmp_path),
                "--format",
                "png",
            ],
        )
        assert result.exit_code == 0, f"CLI failed: {result.output}"
        assert "Generated" in result.output

        png_files = list(tmp_path.glob("*.png"))
        assert len(png_files) == 7

    def test_svg_output(self, tmp_path):
        """SVG format should produce .svg files."""
        from analysis.charts import ChartConfig, generate_all_charts

        config = ChartConfig(
            output_dir=str(tmp_path),
            format="svg",
            scales=[100],
            profiles=["tech"],
            seed=42,
        )
        paths = generate_all_charts(config)

        for p in paths:
            assert Path(p).suffix == ".svg"
