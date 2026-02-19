"""Tests for MCP server tool functions.

These tests call the underlying tool functions directly rather than going
through the MCP transport layer.
"""

from __future__ import annotations

import tempfile
from pathlib import Path

import pytest

mcp_available = pytest.importorskip("mcp", reason="mcp package not installed")
import mcp_server.server as srv  # noqa: E402
from export.json_export import JSONExporter  # noqa: E402
from graph.knowledge_graph import KnowledgeGraph  # noqa: E402
from synthetic.orchestrator import SyntheticOrchestrator  # noqa: E402
from synthetic.profiles.tech_company import mid_size_tech_company  # noqa: E402


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
    srv._kg = None
    yield
    srv._kg = None


# ---------------------------------------------------------------
# load_graph
# ---------------------------------------------------------------


class TestLoadGraph:
    def test_load_graph_returns_stats(self, graph_json_path: str):
        result = srv.load_graph(graph_json_path)
        assert result["status"] == "ok"
        assert result["entity_count"] > 0
        assert result["relationship_count"] > 0
        assert isinstance(result["entity_types"], dict)
        assert "person" in result["entity_types"]

    def test_load_graph_nonexistent_file(self):
        result = srv.load_graph("/tmp/does_not_exist_hckg.json")
        assert "error" in result


# ---------------------------------------------------------------
# get_statistics
# ---------------------------------------------------------------


class TestGetStatistics:
    def test_get_statistics_without_load(self):
        result = srv.get_statistics()
        assert "error" in result
        assert "load_graph" in result["error"].lower()

    def test_get_statistics_after_load(self, graph_json_path: str):
        srv.load_graph(graph_json_path)
        result = srv.get_statistics()
        assert "entity_count" in result
        assert result["entity_count"] > 0


# ---------------------------------------------------------------
# list_entities
# ---------------------------------------------------------------


class TestListEntities:
    def test_list_entities_all(self, graph_json_path: str):
        srv.load_graph(graph_json_path)
        result = srv.list_entities()
        assert isinstance(result, list)
        assert len(result) > 0
        # Each entry should have id, name, entity_type
        assert "id" in result[0]
        assert "name" in result[0]
        assert "entity_type" in result[0]

    def test_list_entities_by_type(self, graph_json_path: str):
        srv.load_graph(graph_json_path)
        result = srv.list_entities(entity_type="person")
        assert isinstance(result, list)
        assert len(result) > 0
        assert all(e["entity_type"] == "person" for e in result)

    def test_list_entities_respects_limit(self, graph_json_path: str):
        srv.load_graph(graph_json_path)
        result = srv.list_entities(limit=3)
        assert len(result) <= 3

    def test_list_entities_invalid_type(self, graph_json_path: str):
        srv.load_graph(graph_json_path)
        result = srv.list_entities(entity_type="unicorn")
        assert isinstance(result, list)
        assert "error" in result[0]


# ---------------------------------------------------------------
# get_entity
# ---------------------------------------------------------------


class TestGetEntity:
    def test_get_entity_found(self, graph_json_path: str):
        srv.load_graph(graph_json_path)
        # Grab the first person entity to get a valid ID
        entities = srv.list_entities(entity_type="person", limit=1)
        entity_id = entities[0]["id"]

        result = srv.get_entity(entity_id)
        assert result["id"] == entity_id
        assert "name" in result

    def test_get_entity_not_found(self, graph_json_path: str):
        srv.load_graph(graph_json_path)
        result = srv.get_entity("nonexistent-id-12345")
        assert "error" in result


# ---------------------------------------------------------------
# get_neighbors
# ---------------------------------------------------------------


class TestGetNeighbors:
    def test_get_neighbors(self, graph_json_path: str):
        srv.load_graph(graph_json_path)
        # Get a person who likely has connections
        entities = srv.list_entities(entity_type="person", limit=1)
        entity_id = entities[0]["id"]

        result = srv.get_neighbors(entity_id)
        assert isinstance(result, list)
        # Persons typically have at least a department or role connection
        if len(result) > 0:
            assert "entity" in result[0]
            assert "relationships" in result[0]


# ---------------------------------------------------------------
# search_entities
# ---------------------------------------------------------------


class TestSearchEntities:
    def test_search_entities_finds_match(self, graph_json_path: str):
        srv.load_graph(graph_json_path)
        # Search for a department name that we know exists
        result = srv.search_entities(query="Engineering")
        assert isinstance(result, list)
        assert len(result) > 0
        assert "match_score" in result[0]

    def test_search_entities_no_match(self, graph_json_path: str):
        srv.load_graph(graph_json_path)
        result = srv.search_entities(query="zzzzxqnonexistent9999")
        assert isinstance(result, list)
        # Should return empty or very low-scoring results (filtered by threshold)
        # All results should have score >= 50 or be empty
        for entry in result:
            if "match_score" in entry:
                assert entry["match_score"] >= 50.0


# ---------------------------------------------------------------
# Additional tools (smoke tests)
# ---------------------------------------------------------------


class TestAdditionalTools:
    def test_find_most_connected(self, graph_json_path: str):
        srv.load_graph(graph_json_path)
        result = srv.find_most_connected(top_n=5)
        assert isinstance(result, list)
        assert len(result) <= 5
        if result:
            assert "degree" in result[0]

    def test_compute_centrality_degree(self, graph_json_path: str):
        srv.load_graph(graph_json_path)
        result = srv.compute_centrality(metric="degree")
        assert isinstance(result, list)
        assert len(result) <= 20
        if result:
            assert "score" in result[0]

    def test_compute_centrality_invalid(self, graph_json_path: str):
        srv.load_graph(graph_json_path)
        result = srv.compute_centrality(metric="invalid_metric")
        assert isinstance(result, list)
        assert "error" in result[0]

    def test_get_blast_radius(self, graph_json_path: str):
        srv.load_graph(graph_json_path)
        entities = srv.list_entities(limit=1)
        entity_id = entities[0]["id"]

        result = srv.get_blast_radius(entity_id, max_depth=2)
        assert "total_affected" in result
        assert "by_depth" in result

    def test_find_shortest_path_no_graph(self):
        result = srv.find_shortest_path("a", "b")
        assert "error" in result
