"""In-memory token-bucket rate limiter for the hckg REST API.

Configuration via environment variables:
    HCKG_RATE_LIMIT  — requests per second (default 10, 0 = disabled)
    HCKG_RATE_BURST  — max burst size (default 20)
"""

from __future__ import annotations

import logging
import os
import time
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from flask import Flask

logger = logging.getLogger(__name__)


class TokenBucket:
    """Token bucket for rate limiting a single client."""

    __slots__ = ("_rate", "_burst", "_tokens", "_last_refill")

    def __init__(self, rate: float, burst: int) -> None:
        self._rate = rate
        self._burst = burst
        self._tokens = float(burst)
        self._last_refill = time.monotonic()

    def consume(self) -> bool:
        """Try to consume one token.  Returns True if allowed."""
        now = time.monotonic()
        elapsed = now - self._last_refill
        self._tokens = min(self._burst, self._tokens + elapsed * self._rate)
        self._last_refill = now

        if self._tokens >= 1.0:
            self._tokens -= 1.0
            return True
        return False

    @property
    def retry_after(self) -> float:
        """Seconds until the next token is available."""
        if self._tokens >= 1.0:
            return 0.0
        return (1.0 - self._tokens) / self._rate


class RateLimiter:
    """Per-IP rate limiter using token buckets."""

    def __init__(self, rate: float, burst: int) -> None:
        self._rate = rate
        self._burst = burst
        self._buckets: dict[str, TokenBucket] = {}

    def allow(self, client_ip: str) -> tuple[bool, float]:
        """Check if a request from *client_ip* is allowed.

        Returns ``(allowed, retry_after_seconds)``.
        """
        if client_ip not in self._buckets:
            self._buckets[client_ip] = TokenBucket(self._rate, self._burst)
        bucket = self._buckets[client_ip]
        allowed = bucket.consume()
        return allowed, bucket.retry_after


def init_rate_limit(app: Flask, rate: float | None = None, burst: int | None = None) -> None:
    """Register a ``before_request`` hook that enforces per-IP rate limiting.

    Parameters
    ----------
    app:
        Flask application instance.
    rate:
        Requests per second.  Falls back to ``HCKG_RATE_LIMIT`` env var,
        then 10.  Set to 0 to disable.
    burst:
        Maximum burst size.  Falls back to ``HCKG_RATE_BURST`` env var,
        then 20.
    """
    if rate is None:
        rate = float(os.environ.get("HCKG_RATE_LIMIT", "10"))
    if burst is None:
        burst = int(os.environ.get("HCKG_RATE_BURST", "20"))

    if rate <= 0:
        logger.info("Rate limiting disabled (HCKG_RATE_LIMIT=0)")
        return

    logger.info("Rate limiting enabled: %.1f req/s, burst %d", rate, burst)
    limiter = RateLimiter(rate, burst)

    @app.before_request
    def _check_rate_limit() -> object | None:
        from flask import Response
        from flask import request as flask_request

        client_ip = flask_request.remote_addr or "unknown"
        allowed, retry_after = limiter.allow(client_ip)

        if not allowed:
            return Response(
                '{"error": "Rate limit exceeded"}',
                status=429,
                content_type="application/json",
                headers={"Retry-After": str(int(retry_after) + 1)},
            )
        return None
