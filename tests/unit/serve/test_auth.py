"""Tests for REST API bearer-token authentication."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

import pytest

flask = pytest.importorskip("flask", reason="flask not installed")

import serve.app as serve_module  # noqa: E402
from export.json_export import JSONExporter  # noqa: E402
from serve.app import create_app  # noqa: E402

TEST_API_KEY = "test-secret-key-12345"


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
def authed_client(graph_file):
    """Client with API key authentication enabled."""
    app = create_app(graph_path=graph_file, api_key=TEST_API_KEY)
    app.config["TESTING"] = True
    with app.test_client() as c:
        yield c


@pytest.fixture()
def open_client(graph_file):
    """Client without API key (open access)."""
    app = create_app(graph_path=graph_file)
    app.config["TESTING"] = True
    with app.test_client() as c:
        yield c


class TestAuthEnabled:
    """When HCKG_API_KEY is set, protected routes require a valid token."""

    def test_health_exempt(self, authed_client):
        resp = authed_client.get("/health")
        assert resp.status_code == 200

    def test_index_exempt(self, authed_client):
        resp = authed_client.get("/")
        assert resp.status_code == 200

    def test_statistics_requires_auth(self, authed_client):
        resp = authed_client.get("/statistics")
        assert resp.status_code == 401
        data = json.loads(resp.data)
        assert "error" in data

    def test_valid_token_passes(self, authed_client):
        resp = authed_client.get(
            "/statistics",
            headers={"Authorization": f"Bearer {TEST_API_KEY}"},
        )
        assert resp.status_code == 200

    def test_invalid_token_rejected(self, authed_client):
        resp = authed_client.get(
            "/statistics",
            headers={"Authorization": "Bearer wrong-key"},
        )
        assert resp.status_code == 403
        data = json.loads(resp.data)
        assert "error" in data

    def test_missing_bearer_prefix(self, authed_client):
        resp = authed_client.get(
            "/statistics",
            headers={"Authorization": TEST_API_KEY},
        )
        assert resp.status_code == 401

    def test_entities_requires_auth(self, authed_client):
        resp = authed_client.get("/entities")
        assert resp.status_code == 401

    def test_entities_with_auth(self, authed_client):
        resp = authed_client.get(
            "/entities",
            headers={"Authorization": f"Bearer {TEST_API_KEY}"},
        )
        assert resp.status_code == 200


class TestAuthDisabled:
    """When no API key is configured, all routes are open."""

    def test_statistics_open(self, open_client):
        resp = open_client.get("/statistics")
        assert resp.status_code == 200

    def test_entities_open(self, open_client):
        resp = open_client.get("/entities")
        assert resp.status_code == 200


class TestAuthViaEnvVar:
    """API key can be set via HCKG_API_KEY environment variable."""

    def test_env_var_enables_auth(self, graph_file, monkeypatch):
        monkeypatch.setenv("HCKG_API_KEY", "env-key-xyz")
        app = create_app(graph_path=graph_file)
        app.config["TESTING"] = True
        with app.test_client() as c:
            resp = c.get("/statistics")
            assert resp.status_code == 401

            resp = c.get(
                "/statistics",
                headers={"Authorization": "Bearer env-key-xyz"},
            )
            assert resp.status_code == 200
