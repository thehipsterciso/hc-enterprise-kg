"""Bearer token authentication for the hckg REST API.

If ``HCKG_API_KEY`` is set (env var or passed to ``create_app``), all
routes except ``/`` and ``/health`` require a valid ``Authorization:
Bearer <token>`` header.  If unset, the API runs open (backward
compatible).
"""

from __future__ import annotations

import hmac
import logging
import os
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import flask.typing as ft
    from flask import Flask

logger = logging.getLogger(__name__)

# Routes that are always accessible without authentication
EXEMPT_PATHS = frozenset({"/", "/health"})


def init_auth(app: Flask, api_key: str | None = None) -> None:
    """Register a ``before_request`` hook that enforces bearer-token auth.

    Parameters
    ----------
    app:
        The Flask application instance.
    api_key:
        The expected API key.  Falls back to the ``HCKG_API_KEY``
        environment variable.  If neither is set, authentication is
        disabled and all requests are allowed through.
    """
    resolved_key = api_key or os.environ.get("HCKG_API_KEY")

    if not resolved_key:
        logger.info("HCKG_API_KEY not set — API authentication disabled")
        return

    logger.info("API authentication enabled")

    @app.before_request
    def _check_auth() -> ft.ResponseReturnValue | None:
        from flask import request as flask_request

        if flask_request.path in EXEMPT_PATHS:
            return None

        auth_header = flask_request.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            from flask import Response

            return Response(
                '{"error": "Missing or invalid Authorization header. '
                'Use: Authorization: Bearer <token>"}',
                status=401,
                content_type="application/json",
            )

        token = auth_header[7:]  # Strip "Bearer " prefix
        if not hmac.compare_digest(token, resolved_key):
            from flask import Response

            return Response(
                '{"error": "Invalid API key"}',
                status=403,
                content_type="application/json",
            )

        return None
