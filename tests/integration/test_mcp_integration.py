"""MCP integration tests — full lifecycle including auto-reload."""

from __future__ import annotations

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
    for tool in mcp._tool_manager._tools.values():
        if tool.name == name:
            return tool.fn(**kwargs)
    raise ValueError(f"Tool '{name}' not found")


def _generate_graph(employees: int = 20, seed: int = 42) -> tuple[KnowledgeGraph, str]:
    """Generate a graph and export to a temp file. Returns (kg, path)."""
    kg = KnowledgeGraph()
    profile = mid_size_tech_company(employees)
    SyntheticOrchestrator(kg, profile, seed=seed).generate()

    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as tmp:
        tmp_path = tmp.name
    JSONExporter().export(kg.engine, Path(tmp_path))
    return kg, tmp_path


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


class TestMCPFullLifecycle:
    """End-to-end MCP server lifecycle tests."""

    def test_load_query_all_tools(self):
        """Load a graph, then exercise every query tool."""
        _, path = _generate_graph(employees=30)
        result = state.load_graph(path)
        assert result["status"] == "ok"

        # get_statistics
        stats = _call_tool("get_statistics")
        assert stats["entity_count"] > 30

        # list_entities
        entities = _call_tool("list_entities", limit=5)
        assert len(entities) <= 5

        # list_entities by type
        people = _call_tool("list_entities", entity_type="person")
        assert len(people) == 30
        assert all(p["entity_type"] == "person" for p in people)

        # get_entity
        entity_id = people[0]["id"]
        entity = _call_tool("get_entity", entity_id=entity_id)
        assert entity["id"] == entity_id

        # get_neighbors
        neighbors = _call_tool("get_neighbors", entity_id=entity_id)
        assert isinstance(neighbors, list)

        # search_entities
        search = _call_tool("search_entities", query="Engineering")
        assert isinstance(search, list)

        # find_most_connected
        connected = _call_tool("find_most_connected", top_n=3)
        assert len(connected) <= 3

        # compute_centrality
        centrality = _call_tool("compute_centrality", metric="degree")
        assert isinstance(centrality, list)
        if centrality:
            assert "score" in centrality[0]

        # get_blast_radius
        blast = _call_tool("get_blast_radius", entity_id=entity_id, max_depth=2)
        assert "total_affected" in blast

        # find_shortest_path (self to self)
        path_result = _call_tool("find_shortest_path", source_id=entity_id, target_id=entity_id)
        assert path_result["path_length"] == 0

    def test_auto_reload_after_regeneration(self):
        """Simulate hckg demo → MCP detects change and reloads."""
        _, path = _generate_graph(employees=10, seed=1)
        state.load_graph(path)

        initial_count = _call_tool("get_statistics")["entity_count"]

        # Simulate regeneration — write a new graph to the same file
        time.sleep(0.05)
        kg2 = KnowledgeGraph()
        profile2 = mid_size_tech_company(50)
        SyntheticOrchestrator(kg2, profile2, seed=2).generate()
        JSONExporter().export(kg2.engine, Path(path))

        # Next tool call should detect the change and reload
        new_stats = _call_tool("get_statistics")
        assert new_stats["entity_count"] != initial_count, (
            "Graph should have reloaded with different data"
        )

    def test_entity_type_coverage(self):
        """All 30 entity types should be present after loading a full graph."""
        _, path = _generate_graph(employees=50, seed=42)
        state.load_graph(path)

        stats = _call_tool("get_statistics")
        entity_types = set(stats["entity_types"].keys())

        expected_types = {
            "person",
            "department",
            "role",
            "system",
            "network",
            "data_asset",
            "policy",
            "vendor",
            "location",
            "vulnerability",
            "threat_actor",
            "incident",
            "regulation",
            "control",
            "risk",
            "threat",
            "integration",
            "data_domain",
            "data_flow",
            "organizational_unit",
            "business_capability",
            "site",
            "geography",
            "jurisdiction",
            "product_portfolio",
            "product",
            "market_segment",
            "customer",
            "contract",
            "initiative",
        }
        missing = expected_types - entity_types
        assert not missing, f"Missing entity types: {missing}"

    def test_relationship_types_present(self):
        """Generated graph should have multiple relationship types."""
        _, path = _generate_graph(employees=30)
        state.load_graph(path)

        stats = _call_tool("get_statistics")
        rel_types = set(stats.get("relationship_types", {}).keys())
        assert len(rel_types) >= 5, f"Only {len(rel_types)} relationship types found"

    def test_search_and_navigate(self):
        """Search for an entity, then navigate its relationships."""
        _, path = _generate_graph(employees=30)
        state.load_graph(path)

        # Search for departments
        depts = _call_tool("search_entities", query="Engineering")
        assert len(depts) > 0

        # Get full entity details
        dept = _call_tool("get_entity", entity_id=depts[0]["id"])
        assert dept["name"]

        # Get neighbors
        neighbors = _call_tool("get_neighbors", entity_id=dept["id"])
        assert isinstance(neighbors, list)

    def test_centrality_metrics(self):
        """All three centrality metrics should work."""
        _, path = _generate_graph(employees=20)
        state.load_graph(path)

        for metric in ("degree", "betweenness"):
            result = _call_tool("compute_centrality", metric=metric)
            assert isinstance(result, list)
            assert len(result) > 0
            assert "score" in result[0]

        # pagerank requires scipy — test gracefully if not installed
        try:
            result = _call_tool("compute_centrality", metric="pagerank")
            assert isinstance(result, list)
        except ModuleNotFoundError:
            pytest.skip("scipy not installed — pagerank unavailable")
