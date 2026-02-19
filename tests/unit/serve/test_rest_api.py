"""Tests for the hckg serve REST API."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

import pytest

flask = pytest.importorskip("flask", reason="flask not installed")

import serve.app as serve_module  # noqa: E402
from export.json_export import JSONExporter  # noqa: E402
from serve.app import OPENAI_TOOLS, create_app  # noqa: E402


@pytest.fixture(autouse=True)
def _reset_serve_state():
    """Reset module-level _kg between tests to avoid cross-test contamination."""
    serve_module._kg = None
    yield
    serve_module._kg = None


@pytest.fixture()
def graph_file(populated_kg):
    """Export the populated_kg fixture to a temp JSON file."""
    with tempfile.TemporaryDirectory() as tmpdir:
        path = Path(tmpdir) / "test_graph.json"
        JSONExporter().export(populated_kg.engine, path)
        yield str(path)


@pytest.fixture()
def client(graph_file):
    """Create a Flask test client with a loaded graph."""
    app = create_app(graph_path=graph_file)
    app.config["TESTING"] = True
    with app.test_client() as c:
        yield c


class TestHealthAndIndex:
    def test_index_returns_endpoints(self, client):
        resp = client.get("/")
        data = json.loads(resp.data)
        assert resp.status_code == 200
        assert data["service"] == "hc-enterprise-kg"
        assert "endpoints" in data

    def test_health_shows_graph_loaded(self, client):
        resp = client.get("/health")
        data = json.loads(resp.data)
        assert data["status"] == "ok"
        assert data["graph_loaded"] is True
        assert data["entity_count"] > 0


class TestStatistics:
    def test_statistics_returns_counts(self, client):
        resp = client.get("/statistics")
        data = json.loads(resp.data)
        assert resp.status_code == 200
        assert "entity_count" in data
        assert "relationship_count" in data

    def test_statistics_without_graph(self):
        app = create_app()
        app.config["TESTING"] = True
        with app.test_client() as c:
            resp = c.get("/statistics")
            assert resp.status_code == 409


class TestEntities:
    def test_list_all_entities(self, client):
        resp = client.get("/entities")
        data = json.loads(resp.data)
        assert resp.status_code == 200
        assert isinstance(data, list)
        assert len(data) >= 3  # person, dept, system

    def test_list_filtered_by_type(self, client):
        resp = client.get("/entities?type=person")
        data = json.loads(resp.data)
        assert resp.status_code == 200
        assert all(e["entity_type"] == "person" for e in data)

    def test_list_with_limit(self, client):
        resp = client.get("/entities?limit=1")
        data = json.loads(resp.data)
        assert len(data) == 1

    def test_get_entity_by_id(self, client):
        entities = json.loads(client.get("/entities").data)
        eid = entities[0]["id"]
        resp = client.get(f"/entities/{eid}")
        data = json.loads(resp.data)
        assert resp.status_code == 200
        assert data["id"] == eid

    def test_get_nonexistent_entity(self, client):
        resp = client.get("/entities/nonexistent-id-xyz")
        assert resp.status_code == 404

    def test_invalid_entity_type(self, client):
        resp = client.get("/entities?type=bogus")
        data = json.loads(resp.data)
        assert any("error" in item for item in data)


class TestNeighbors:
    def test_get_neighbors(self, client):
        resp = client.get("/entities/person-1/neighbors")
        data = json.loads(resp.data)
        assert resp.status_code == 200
        assert isinstance(data, list)
        assert len(data) >= 1

    def test_get_neighbors_with_direction(self, client):
        resp = client.get("/entities/person-1/neighbors?direction=out")
        assert resp.status_code == 200


class TestPaths:
    def test_shortest_path(self, client):
        resp = client.get("/path/person-1/sys-1")
        data = json.loads(resp.data)
        assert resp.status_code == 200
        assert "path" in data
        assert data["path_length"] >= 1

    def test_no_path(self, client):
        resp = client.get("/path/person-1/nonexistent")
        assert resp.status_code == 404


class TestBlastRadius:
    def test_blast_radius(self, client):
        resp = client.get("/blast-radius/person-1")
        data = json.loads(resp.data)
        assert resp.status_code == 200
        assert "total_affected" in data
        assert data["total_affected"] >= 1

    def test_blast_radius_nonexistent(self, client):
        resp = client.get("/blast-radius/nonexistent-id")
        assert resp.status_code == 404


class TestCentrality:
    def test_degree_centrality(self, client):
        resp = client.get("/centrality")
        data = json.loads(resp.data)
        assert resp.status_code == 200
        assert isinstance(data, list)
        assert len(data) >= 1
        assert "score" in data[0]

    def test_betweenness(self, client):
        resp = client.get("/centrality?metric=betweenness")
        data = json.loads(resp.data)
        assert resp.status_code == 200
        assert isinstance(data, list)

    def test_invalid_metric(self, client):
        resp = client.get("/centrality?metric=bogus")
        data = json.loads(resp.data)
        assert any("error" in item for item in data)


class TestSearch:
    def test_fuzzy_search(self, client):
        resp = client.get("/search?q=alice")
        data = json.loads(resp.data)
        assert resp.status_code == 200
        assert isinstance(data, list)
        assert len(data) >= 1
        assert "match_score" in data[0]

    def test_search_missing_query(self, client):
        resp = client.get("/search")
        assert resp.status_code == 400


class TestAsk:
    def test_ask_returns_context(self, client):
        resp = client.post("/ask", json={"question": "Who works in Engineering?"})
        data = json.loads(resp.data)
        assert resp.status_code == 200
        assert "context" in data
        assert "entities" in data

    def test_ask_missing_question(self, client):
        resp = client.post("/ask", json={})
        assert resp.status_code == 400


class TestOpenAIEndpoints:
    def test_openai_tools_returns_definitions(self, client):
        resp = client.get("/openai/tools")
        data = json.loads(resp.data)
        assert resp.status_code == 200
        assert isinstance(data, list)
        assert len(data) >= 8
        for tool in data:
            assert tool["type"] == "function"
            assert "name" in tool["function"]
            assert "description" in tool["function"]
            assert "parameters" in tool["function"]

    def test_openai_call_get_statistics(self, client):
        resp = client.post("/openai/call", json={
            "name": "get_statistics",
            "arguments": {},
        })
        data = json.loads(resp.data)
        assert resp.status_code == 200
        assert "result" in data
        assert "entity_count" in data["result"]

    def test_openai_call_search(self, client):
        resp = client.post("/openai/call", json={
            "name": "search_entities",
            "arguments": {"query": "alice"},
        })
        data = json.loads(resp.data)
        assert resp.status_code == 200
        assert "result" in data

    def test_openai_call_ask_graph(self, client):
        resp = client.post("/openai/call", json={
            "name": "ask_graph",
            "arguments": {"question": "What systems exist?"},
        })
        data = json.loads(resp.data)
        assert resp.status_code == 200
        assert "result" in data
        assert "context" in data["result"]

    def test_openai_call_unknown_tool(self, client):
        resp = client.post("/openai/call", json={
            "name": "nonexistent_tool",
            "arguments": {},
        })
        assert resp.status_code == 400


class TestLoadEndpoint:
    def test_load_graph_via_api(self, graph_file):
        app = create_app()
        app.config["TESTING"] = True
        with app.test_client() as c:
            # No graph yet (state was reset by autouse fixture)
            resp = c.get("/health")
            data = json.loads(resp.data)
            assert data["graph_loaded"] is False

            # Load via POST
            resp = c.post("/load", json={"path": graph_file})
            data = json.loads(resp.data)
            assert resp.status_code == 200
            assert data["status"] == "ok"

            # Now graph is loaded
            resp = c.get("/health")
            data = json.loads(resp.data)
            assert data["graph_loaded"] is True

    def test_load_missing_path(self):
        app = create_app()
        app.config["TESTING"] = True
        with app.test_client() as c:
            resp = c.post("/load", json={})
            assert resp.status_code == 400


class TestOpenAIToolsCompleteness:
    def test_all_tools_have_required_schema(self):
        for tool in OPENAI_TOOLS:
            func = tool["function"]
            assert isinstance(func["name"], str)
            assert len(func["name"]) > 0
            assert isinstance(func["description"], str)
            assert "properties" in func["parameters"]

    def test_ask_graph_tool_exists(self):
        names = [t["function"]["name"] for t in OPENAI_TOOLS]
        assert "ask_graph" in names
