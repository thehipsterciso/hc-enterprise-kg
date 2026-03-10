"""Tests for in-memory rate limiting."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

import pytest

flask = pytest.importorskip("flask", reason="flask not installed")

import serve.app as serve_module  # noqa: E402
from export.json_export import JSONExporter  # noqa: E402
from serve.app import create_app  # noqa: E402
from serve.rate_limit import RateLimiter, TokenBucket  # noqa: E402


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


class TestTokenBucket:
    def test_allows_burst(self):
        bucket = TokenBucket(rate=1.0, burst=3)
        assert bucket.consume() is True
        assert bucket.consume() is True
        assert bucket.consume() is True

    def test_rejects_after_burst(self):
        bucket = TokenBucket(rate=1.0, burst=2)
        bucket.consume()
        bucket.consume()
        assert bucket.consume() is False

    def test_retry_after_positive(self):
        bucket = TokenBucket(rate=1.0, burst=1)
        bucket.consume()
        bucket.consume()  # exhausted
        assert bucket.retry_after > 0

    def test_refills_over_time(self, monkeypatch):
        import time

        bucket = TokenBucket(rate=10.0, burst=1)
        bucket.consume()  # exhaust
        assert bucket.consume() is False

        # Simulate time passing
        original_monotonic = time.monotonic
        offset = 0.2  # 200ms at 10/s = 2 tokens refilled
        monkeypatch.setattr(time, "monotonic", lambda: original_monotonic() + offset)

        assert bucket.consume() is True


class TestRateLimiter:
    def test_per_ip_isolation(self):
        limiter = RateLimiter(rate=1.0, burst=1)
        allowed_a, _ = limiter.allow("1.1.1.1")
        allowed_b, _ = limiter.allow("2.2.2.2")
        assert allowed_a is True
        assert allowed_b is True

    def test_same_ip_limited(self):
        limiter = RateLimiter(rate=1.0, burst=1)
        limiter.allow("1.1.1.1")
        allowed, retry_after = limiter.allow("1.1.1.1")
        assert allowed is False
        assert retry_after > 0


class TestRateLimitIntegration:
    def test_returns_429_when_exceeded(self, graph_file, monkeypatch):
        monkeypatch.setenv("HCKG_RATE_LIMIT", "1")
        monkeypatch.setenv("HCKG_RATE_BURST", "1")
        app = create_app(graph_path=graph_file)
        app.config["TESTING"] = True
        with app.test_client() as c:
            resp1 = c.get("/health")
            assert resp1.status_code == 200

            resp2 = c.get("/health")
            assert resp2.status_code == 429
            data = json.loads(resp2.data)
            assert "error" in data
            assert "Retry-After" in resp2.headers

    def test_disabled_with_zero(self, graph_file, monkeypatch):
        monkeypatch.setenv("HCKG_RATE_LIMIT", "0")
        app = create_app(graph_path=graph_file)
        app.config["TESTING"] = True
        with app.test_client() as c:
            for _ in range(10):
                resp = c.get("/health")
                assert resp.status_code == 200
