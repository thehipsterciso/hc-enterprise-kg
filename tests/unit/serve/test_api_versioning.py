"""Tests for API versioning with /v1/ prefix."""

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


class TestV1Routes:
    """Versioned routes under /v1/ prefix work correctly."""

    def test_v1_statistics(self, client):
        resp = client.get("/v1/statistics")
        assert resp.status_code == 200
        data = json.loads(resp.data)
        assert "entity_count" in data

    def test_v1_entities(self, client):
        resp = client.get("/v1/entities")
        assert resp.status_code == 200

    def test_v1_search(self, client):
        resp = client.get("/v1/search?q=test")
        assert resp.status_code == 200

    def test_v1_centrality(self, client):
        resp = client.get("/v1/centrality")
        assert resp.status_code == 200

    def test_v1_has_api_version_header(self, client):
        resp = client.get("/v1/statistics")
        assert resp.headers.get("X-API-Version") == "1"

    def test_root_routes_still_work(self, client):
        resp = client.get("/statistics")
        assert resp.status_code == 200


class TestDeprecationHeaders:
    """Deprecated root routes include deprecation headers."""

    def test_deprecation_header_on_root_statistics(self, client):
        resp = client.get("/statistics")
        assert resp.headers.get("Deprecation") == "true"

    def test_sunset_header(self, client):
        resp = client.get("/statistics")
        assert "Sunset" in resp.headers

    def test_link_header_points_to_v1(self, client):
        resp = client.get("/statistics")
        link = resp.headers.get("Link", "")
        assert "/v1/statistics" in link

    def test_no_deprecation_on_v1(self, client):
        resp = client.get("/v1/statistics")
        assert resp.headers.get("Deprecation") is None

    def test_index_not_deprecated(self, client):
        resp = client.get("/")
        assert resp.headers.get("Deprecation") is None

    def test_health_not_deprecated(self, client):
        resp = client.get("/health")
        assert resp.headers.get("Deprecation") is None


class TestIndexEndpoints:
    """Index lists v1 endpoints."""

    def test_index_shows_v1_prefix(self, client):
        resp = client.get("/")
        data = json.loads(resp.data)
        endpoints = data["endpoints"]
        v1_endpoints = [e for e in endpoints if "/v1/" in e]
        assert len(v1_endpoints) > 0

    def test_deprecation_notice_in_index(self, client):
        resp = client.get("/")
        data = json.loads(resp.data)
        assert "deprecation_notice" in data
