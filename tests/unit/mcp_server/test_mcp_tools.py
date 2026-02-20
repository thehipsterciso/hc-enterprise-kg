"""Tests for MCP server tool functions.

These tests call the underlying tool functions directly rather than going
through the MCP transport layer.
"""

from __future__ import annotations

import json
import tempfile
import time
from pathlib import Path

import pytest

mcp_available = pytest.importorskip("mcp", reason="mcp package not installed")
import mcp_server.state as state  # noqa: E402
from export.json_export import JSONExporter  # noqa: E402
from graph.knowledge_graph import KnowledgeGraph  # noqa: E402
from mcp_server.server import mcp  # noqa: E402
from synthetic.orchestrator import SyntheticOrchestrator  # noqa: E402
from synthetic.profiles.tech_company import mid_size_tech_company  # noqa: E402


def _call_tool(name: str, **kwargs):
    """Call an MCP tool by name via the FastMCP registry."""
    # FastMCP stores tools in _tool_manager; access them directly for testing
    for tool in mcp._tool_manager._tools.values():
        if tool.name == name:
            return tool.fn(**kwargs)
    raise ValueError(f"Tool '{name}' not found")


@pytest.fixture(scope="module")
def graph_json_path() -> str:
    """Generate a small synthetic KG, export to a temp JSON file, return the path."""
    kg = KnowledgeGraph()
    profile = mid_size_tech_company(20)
    SyntheticOrchestrator(kg, profile, seed=42).generate()

    exporter = JSONExporter()
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as tmp:
        tmp_path = tmp.name
    exporter.export(kg.engine, Path(tmp_path))
    return tmp_path


@pytest.fixture(autouse=True)
def _reset_server_state():
    """Ensure each test starts with a clean server state."""
    state._kg = None
    state._loaded_path = None
    state._loaded_mtime = 0.0
    yield
    state._kg = None
    state._loaded_path = None
    state._loaded_mtime = 0.0


# ---------------------------------------------------------------
# load_graph
# ---------------------------------------------------------------


class TestLoadGraph:
    def test_load_graph_returns_stats(self, graph_json_path: str):
        result = state.load_graph(graph_json_path)
        assert result["status"] == "ok"
        assert result["entity_count"] > 0
        assert result["relationship_count"] > 0
        assert isinstance(result["entity_types"], dict)
        assert "person" in result["entity_types"]

    def test_load_graph_nonexistent_file(self):
        result = state.load_graph("/tmp/does_not_exist_hckg.json")
        assert "error" in result


# ---------------------------------------------------------------
# get_statistics
# ---------------------------------------------------------------


class TestGetStatistics:
    def test_get_statistics_without_load(self):
        result = _call_tool("get_statistics")
        assert "error" in result
        assert "load_graph" in result["error"].lower()

    def test_get_statistics_after_load(self, graph_json_path: str):
        state.load_graph(graph_json_path)
        result = _call_tool("get_statistics")
        assert "entity_count" in result
        assert result["entity_count"] > 0


# ---------------------------------------------------------------
# list_entities
# ---------------------------------------------------------------


class TestListEntities:
    def test_list_entities_all(self, graph_json_path: str):
        state.load_graph(graph_json_path)
        result = _call_tool("list_entities")
        assert isinstance(result, list)
        assert len(result) > 0
        assert "id" in result[0]
        assert "name" in result[0]
        assert "entity_type" in result[0]

    def test_list_entities_by_type(self, graph_json_path: str):
        state.load_graph(graph_json_path)
        result = _call_tool("list_entities", entity_type="person")
        assert isinstance(result, list)
        assert len(result) > 0
        assert all(e["entity_type"] == "person" for e in result)

    def test_list_entities_respects_limit(self, graph_json_path: str):
        state.load_graph(graph_json_path)
        result = _call_tool("list_entities", limit=3)
        assert len(result) <= 3

    def test_list_entities_invalid_type(self, graph_json_path: str):
        state.load_graph(graph_json_path)
        result = _call_tool("list_entities", entity_type="unicorn")
        assert isinstance(result, list)
        assert "error" in result[0]


# ---------------------------------------------------------------
# get_entity
# ---------------------------------------------------------------


class TestGetEntity:
    def test_get_entity_found(self, graph_json_path: str):
        state.load_graph(graph_json_path)
        entities = _call_tool("list_entities", entity_type="person", limit=1)
        entity_id = entities[0]["id"]

        result = _call_tool("get_entity", entity_id=entity_id)
        assert result["id"] == entity_id
        assert "name" in result

    def test_get_entity_not_found(self, graph_json_path: str):
        state.load_graph(graph_json_path)
        result = _call_tool("get_entity", entity_id="nonexistent-id-12345")
        assert "error" in result


# ---------------------------------------------------------------
# get_neighbors
# ---------------------------------------------------------------


class TestGetNeighbors:
    def test_get_neighbors(self, graph_json_path: str):
        state.load_graph(graph_json_path)
        entities = _call_tool("list_entities", entity_type="person", limit=1)
        entity_id = entities[0]["id"]

        result = _call_tool("get_neighbors", entity_id=entity_id)
        assert isinstance(result, list)
        if len(result) > 0:
            assert "entity" in result[0]
            assert "relationships" in result[0]


# ---------------------------------------------------------------
# search_entities
# ---------------------------------------------------------------


class TestSearchEntities:
    def test_search_entities_finds_match(self, graph_json_path: str):
        state.load_graph(graph_json_path)
        result = _call_tool("search_entities", query="Engineering")
        assert isinstance(result, list)
        assert len(result) > 0
        assert "match_score" in result[0]

    def test_search_entities_no_match(self, graph_json_path: str):
        state.load_graph(graph_json_path)
        result = _call_tool("search_entities", query="zzzzxqnonexistent9999")
        assert isinstance(result, list)
        for entry in result:
            if "match_score" in entry:
                assert entry["match_score"] >= 50.0


# ---------------------------------------------------------------
# Additional tools (smoke tests)
# ---------------------------------------------------------------


class TestAdditionalTools:
    def test_find_most_connected(self, graph_json_path: str):
        state.load_graph(graph_json_path)
        result = _call_tool("find_most_connected", top_n=5)
        assert isinstance(result, list)
        assert len(result) <= 5
        if result:
            assert "degree" in result[0]

    def test_compute_centrality_degree(self, graph_json_path: str):
        state.load_graph(graph_json_path)
        result = _call_tool("compute_centrality", metric="degree")
        assert isinstance(result, list)
        assert len(result) <= 20
        if result:
            assert "score" in result[0]

    def test_compute_centrality_invalid(self, graph_json_path: str):
        state.load_graph(graph_json_path)
        result = _call_tool("compute_centrality", metric="invalid_metric")
        assert isinstance(result, list)
        assert "error" in result[0]

    def test_get_blast_radius(self, graph_json_path: str):
        state.load_graph(graph_json_path)
        entities = _call_tool("list_entities", limit=1)
        entity_id = entities[0]["id"]

        result = _call_tool("get_blast_radius", entity_id=entity_id, max_depth=2)
        assert "total_affected" in result
        assert "by_depth" in result

    def test_find_shortest_path_no_graph(self):
        result = _call_tool("find_shortest_path", source_id="a", target_id="b")
        assert "error" in result


# ---------------------------------------------------------------
# auto_load_default_graph
# ---------------------------------------------------------------


class TestAutoLoadDefaultGraph:
    def test_auto_load_from_env(self, graph_json_path: str, monkeypatch):
        monkeypatch.setenv("HCKG_DEFAULT_GRAPH", graph_json_path)
        state.auto_load_default_graph()
        assert state._kg is not None
        assert state._kg.statistics["entity_count"] > 0

    def test_auto_load_skipped_when_no_env(self, monkeypatch):
        monkeypatch.delenv("HCKG_DEFAULT_GRAPH", raising=False)
        state.auto_load_default_graph()
        assert state._kg is None

    def test_auto_load_skipped_when_path_missing(self, monkeypatch):
        monkeypatch.setenv("HCKG_DEFAULT_GRAPH", "/tmp/nonexistent_hckg.json")
        state.auto_load_default_graph()
        assert state._kg is None


# ---------------------------------------------------------------
# Auto-reload on file change
# ---------------------------------------------------------------


class TestAutoReload:
    """Verify mtime-based auto-reload of the graph file."""

    def test_reload_detects_file_change(self, graph_json_path: str):
        """After loading a graph, modifying the file triggers a reload."""
        state.load_graph(graph_json_path)
        original_count = state._kg.statistics["entity_count"]
        original_mtime = state._loaded_mtime

        time.sleep(0.05)

        with open(graph_json_path) as f:
            data = json.load(f)
        data["entities"] = data["entities"][:5]
        data["relationships"] = []
        with open(graph_json_path, "w") as f:
            json.dump(data, f)

        kg = state.require_graph()
        assert kg.statistics["entity_count"] == 5
        assert kg.statistics["entity_count"] != original_count
        assert state._loaded_mtime != original_mtime

    def test_no_reload_when_file_unchanged(self, graph_json_path: str):
        """When the file hasn't changed, require_graph returns the same instance."""
        state.load_graph(graph_json_path)
        kg_before = state._kg
        mtime_before = state._loaded_mtime

        kg_after = state.require_graph()
        assert kg_after is kg_before
        assert state._loaded_mtime == mtime_before

    def test_reload_graceful_when_file_deleted(self, graph_json_path: str):
        """If the graph file is deleted, the server keeps the last loaded graph."""
        state.load_graph(graph_json_path)

        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as tmp:
            tmp.write(Path(graph_json_path).read_bytes())
            tmp_path = tmp.name

        state.load_graph(tmp_path)
        Path(tmp_path).unlink()

        kg = state.require_graph()
        assert kg is not None

    def test_loaded_path_set_after_load(self, graph_json_path: str):
        """load_graph sets _loaded_path and _loaded_mtime."""
        assert state._loaded_path is None
        assert state._loaded_mtime == 0.0

        state.load_graph(graph_json_path)
        assert state._loaded_path == str(Path(graph_json_path).resolve())
        assert state._loaded_mtime > 0
