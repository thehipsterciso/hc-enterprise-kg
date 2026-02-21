"""Tests for the hckg visualize CLI command."""

from __future__ import annotations

import tempfile
from pathlib import Path

import pytest
from click.testing import CliRunner

from cli.main import cli
from cli.visualize_cmd import (
    ENTITY_COLORS,
    ENTITY_SIZES,
    _build_tooltip,
    _get_node_label,
    _inject_legend,
)


@pytest.fixture()
def sample_graph_json(populated_kg):
    """Export the populated_kg fixture to a temp JSON file."""
    from export.json_export import JSONExporter

    with tempfile.TemporaryDirectory() as tmpdir:
        path = Path(tmpdir) / "test_graph.json"
        JSONExporter().export(populated_kg.engine, path)
        yield str(path)


class TestNodeLabel:
    def test_uses_name_field(self):
        assert _get_node_label({"name": "Alice", "entity_type": "person"}) == "Alice"

    def test_uses_hostname_when_no_name(self):
        assert _get_node_label({"hostname": "web-01", "entity_type": "system"}) == "web-01"

    def test_uses_cve_id(self):
        data = {"cve_id": "CVE-2024-1234", "entity_type": "vulnerability"}
        assert _get_node_label(data) == "CVE-2024-1234"

    def test_fallback_to_entity_type(self):
        assert _get_node_label({"entity_type": "network"}) == "network"

    def test_fallback_to_question_mark(self):
        assert _get_node_label({}) == "?"

    def test_skips_empty_name(self):
        result = _get_node_label({"name": "", "hostname": "srv-1", "entity_type": "system"})
        assert result == "srv-1"


class TestBuildTooltip:
    def test_includes_entity_type(self):
        tooltip = _build_tooltip({"entity_type": "person", "name": "Alice"})
        assert "Entity Type" in tooltip
        assert "person" in tooltip

    def test_skips_internal_fields(self):
        tooltip = _build_tooltip({"id": "abc", "created_at": "now", "name": "Alice"})
        assert "Id" not in tooltip.split("<br>")[0] if "<br>" in tooltip else True

    def test_skips_none_and_empty(self):
        tooltip = _build_tooltip({"name": "Alice", "email": None, "tags": []})
        assert "Email" not in tooltip
        assert "Tags" not in tooltip


class TestEntityMappings:
    def test_all_entity_types_have_colors(self):
        from domain.base import EntityType

        for etype in EntityType:
            assert etype.value in ENTITY_COLORS, f"Missing color for {etype.value}"

    def test_all_entity_types_have_sizes(self):
        from domain.base import EntityType

        for etype in EntityType:
            assert etype.value in ENTITY_SIZES, f"Missing size for {etype.value}"


class TestInjectLegend:
    def test_injects_legend_html(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            html_path = Path(tmpdir) / "test.html"
            html_path.write_text("<html><body></body></html>")
            stats = {
                "entity_count": 10,
                "relationship_count": 5,
                "entity_types": {"person": 7, "department": 3},
            }
            _inject_legend(html_path, stats)
            content = html_path.read_text()
            assert "kg-legend" in content
            assert "hc-enterprise-kg" in content
            assert "Person (7)" in content
            assert "Department (3)" in content
            assert "10 entities" in content

    def test_missing_body_tag_warns(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            html_path = Path(tmpdir) / "test.html"
            html_path.write_text("<html><div>no body tag</div></html>")
            stats = {
                "entity_count": 5,
                "relationship_count": 2,
                "entity_types": {"person": 5},
            }
            _inject_legend(html_path, stats)
            content = html_path.read_text()
            # Legend should NOT be injected — original content unchanged
            assert "kg-legend" not in content

    def test_only_shows_present_types(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            html_path = Path(tmpdir) / "test.html"
            html_path.write_text("<html><body></body></html>")
            stats = {
                "entity_count": 5,
                "relationship_count": 2,
                "entity_types": {"person": 5},
            }
            _inject_legend(html_path, stats)
            content = html_path.read_text()
            assert "Person (5)" in content
            assert "Department" not in content


_pyvis_available = True
try:
    import pyvis  # noqa: F401
except ImportError:
    _pyvis_available = False


@pytest.mark.skipif(not _pyvis_available, reason="pyvis not installed")
class TestVisualizeCLI:
    def test_visualize_produces_html(self, sample_graph_json):
        runner = CliRunner()
        with tempfile.TemporaryDirectory() as tmpdir:
            out = Path(tmpdir) / "viz.html"
            result = runner.invoke(
                cli, ["visualize", sample_graph_json, "--output", str(out), "--no-open"]
            )
            assert result.exit_code == 0, result.output
            assert out.exists()
            content = out.read_text()
            assert "<html>" in content.lower()
            assert "kg-legend" in content

    def test_visualize_default_output_name(self, sample_graph_json):
        runner = CliRunner()
        result = runner.invoke(cli, ["visualize", sample_graph_json, "--no-open"])
        assert result.exit_code == 0, result.output
        # Default name is <stem>_viz.html
        expected = Path("test_graph_viz.html")
        assert expected.exists() or "Visualization saved" in result.output

    def test_visualize_no_physics(self, sample_graph_json):
        runner = CliRunner()
        with tempfile.TemporaryDirectory() as tmpdir:
            out = Path(tmpdir) / "viz.html"
            result = runner.invoke(
                cli,
                ["visualize", sample_graph_json, "--output", str(out), "--no-open", "--no-physics"],
            )
            assert result.exit_code == 0, result.output
            content = out.read_text()
            assert "<html>" in content.lower()

    def test_visualize_malformed_json(self, tmp_path):
        bad = tmp_path / "bad.json"
        bad.write_text("not json {{{")
        runner = CliRunner()
        result = runner.invoke(cli, ["visualize", str(bad), "--no-open"])
        assert result.exit_code != 0

    def test_visualize_output_creates_dirs(self, sample_graph_json, tmp_path):
        nested = tmp_path / "a" / "b" / "viz.html"
        runner = CliRunner()
        result = runner.invoke(
            cli,
            ["visualize", sample_graph_json, "--output", str(nested), "--no-open"],
        )
        assert result.exit_code == 0, result.output
        assert nested.exists()

    def test_visualize_nonexistent_file(self):
        runner = CliRunner()
        result = runner.invoke(cli, ["visualize", "/tmp/nonexistent_xyz.json", "--no-open"])
        assert result.exit_code != 0

    def test_visualize_contains_entity_data(self, sample_graph_json):
        runner = CliRunner()
        with tempfile.TemporaryDirectory() as tmpdir:
            out = Path(tmpdir) / "viz.html"
            result = runner.invoke(
                cli, ["visualize", sample_graph_json, "--output", str(out), "--no-open"]
            )
            assert result.exit_code == 0, result.output
            content = out.read_text()
            # Should contain node data from our fixtures
            assert "Alice Smith" in content or "Engineering" in content
