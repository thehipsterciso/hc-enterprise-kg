"""Tests for enhanced /health endpoint."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

import pytest

flask = pytest.importorskip("flask", reason="flask not installed")

import serve.app as serve_module  # noqa: E402
from export.json_export import JSONExporter  # noqa: E402
from serve.app import create_app  # noqa: E402


@pytest.fixture(autouse=True)
def _reset_serve_state():
    serve_module._kg = None
    yield
    serve_module._kg = None


@pytest.fixture()
def graph_file(populated_kg):
    with tempfile.TemporaryDirectory() as tmpdir:
        path = Path(tmpdir) / "test_graph.json"
        JSONExporter().export(populated_kg.engine, path)
        yield str(path)


@pytest.fixture()
def client(graph_file):
    app = create_app(graph_path=graph_file)
    app.config["TESTING"] = True
    with app.test_client() as c:
        yield c


class TestEnhancedHealth:
    def test_returns_version(self, client):
        resp = client.get("/health")
        data = json.loads(resp.data)
        assert "version" in data
        assert isinstance(data["version"], str)

    def test_returns_uptime(self, client):
        resp = client.get("/health")
        data = json.loads(resp.data)
        assert "uptime_seconds" in data
        assert data["uptime_seconds"] >= 0

    def test_returns_entity_types_when_loaded(self, client):
        resp = client.get("/health")
        data = json.loads(resp.data)
        assert data["graph_loaded"] is True
        assert "entity_types" in data
        assert isinstance(data["entity_types"], dict)

    def test_returns_relationship_types_when_loaded(self, client):
        resp = client.get("/health")
        data = json.loads(resp.data)
        assert "relationship_types" in data
        assert isinstance(data["relationship_types"], dict)

    def test_no_type_breakdowns_without_graph(self):
        app = create_app()
        app.config["TESTING"] = True
        with app.test_client() as c:
            resp = c.get("/health")
            data = json.loads(resp.data)
            assert data["graph_loaded"] is False
            assert "entity_types" not in data
            assert "relationship_types" not in data
            assert data["entity_count"] == 0

    def test_graph_file_metadata(self, graph_file, monkeypatch):
        monkeypatch.setenv("HCKG_DEFAULT_GRAPH", graph_file)
        app = create_app(graph_path=graph_file)
        app.config["TESTING"] = True
        with app.test_client() as c:
            resp = c.get("/health")
            data = json.loads(resp.data)
            assert "graph_file" in data
            assert data["graph_file"]["path"] == graph_file
            assert data["graph_file"]["size_bytes"] > 0
            assert "modified" in data["graph_file"]

    def test_no_graph_file_without_env_var(self, client):
        resp = client.get("/health")
        data = json.loads(resp.data)
        assert "graph_file" not in data
