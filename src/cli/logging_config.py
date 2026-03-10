"""Centralised logging configuration for hckg.

Provides ``configure_logging()`` which sets up the root logger with
either a human-readable text formatter (for CLI use) or a structured
JSON formatter (for MCP/REST production use).

Environment variables
---------------------
HCKG_LOG_LEVEL
    Logging level name (default ``INFO``).
HCKG_LOG_FORMAT
    ``json`` or ``text`` (default ``text``).
HCKG_LOG_FILE
    Optional path — if set, logs are *also* written to this file.
"""

from __future__ import annotations

import json
import logging
import os
import sys
from datetime import UTC, datetime


class JsonFormatter(logging.Formatter):
    """Emit each log record as a single JSON line."""

    def format(self, record: logging.LogRecord) -> str:
        entry = {
            "timestamp": datetime.fromtimestamp(record.created, tz=UTC).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        if record.exc_info and record.exc_info[1] is not None:
            entry["exception"] = self.formatException(record.exc_info)
        # Propagate any extra keys the caller attached
        for key in ("method", "path", "status", "duration_ms", "caller"):
            value = getattr(record, key, None)
            if value is not None:
                entry[key] = value
        return json.dumps(entry, default=str)


_TEXT_FORMAT = "%(asctime)s %(levelname)-8s %(name)s  %(message)s"
_TEXT_DATEFMT = "%Y-%m-%d %H:%M:%S"


def configure_logging(
    *,
    level: str | None = None,
    json_format: bool | None = None,
    log_file: str | None = None,
) -> None:
    """Configure the root logger for hckg.

    Parameters
    ----------
    level:
        Logging level name.  Defaults to ``HCKG_LOG_LEVEL`` env var,
        then ``INFO``.
    json_format:
        If ``True``, use JSON formatter.  Defaults to ``HCKG_LOG_FORMAT``
        env var (``json`` → True, anything else → False), then ``False``.
    log_file:
        Optional file path.  Defaults to ``HCKG_LOG_FILE`` env var.
    """
    resolved_level = (level or os.environ.get("HCKG_LOG_LEVEL", "INFO")).upper()
    if json_format is None:
        json_format = os.environ.get("HCKG_LOG_FORMAT", "text").lower() == "json"
    resolved_file = log_file or os.environ.get("HCKG_LOG_FILE")

    root = logging.getLogger()
    root.setLevel(resolved_level)

    # Remove any existing handlers to avoid duplicates on re-configure
    for handler in root.handlers[:]:
        root.removeHandler(handler)

    # Console handler (stderr)
    console = logging.StreamHandler(sys.stderr)
    if json_format:
        console.setFormatter(JsonFormatter())
    else:
        console.setFormatter(logging.Formatter(_TEXT_FORMAT, datefmt=_TEXT_DATEFMT))
    root.addHandler(console)

    # Optional file handler
    if resolved_file:
        file_handler = logging.FileHandler(resolved_file)
        if json_format:
            file_handler.setFormatter(JsonFormatter())
        else:
            file_handler.setFormatter(logging.Formatter(_TEXT_FORMAT, datefmt=_TEXT_DATEFMT))
        root.addHandler(file_handler)
