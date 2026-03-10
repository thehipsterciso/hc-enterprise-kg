"""Persistent JSONL audit logger for knowledge graph mutations."""

from __future__ import annotations

import json
import logging
from typing import TYPE_CHECKING

from export.file_lock import GraphFileLock

if TYPE_CHECKING:
    from pathlib import Path

    from domain.temporal import GraphEvent

logger = logging.getLogger(__name__)


def derive_audit_path(graph_path: Path) -> Path:
    """Derive audit log path from graph file path.

    ``graph.json`` → ``graph.audit.jsonl``
    """
    return graph_path.with_suffix(".audit.jsonl")


class AuditLogger:
    """Appends GraphEvent records as JSONL to an audit log file.

    Each event is serialized as a single JSON line and appended
    atomically with an exclusive file lock.

    Usage::

        audit = AuditLogger(Path("graph.audit.jsonl"))
        kg.subscribe(audit)
    """

    def __init__(self, path: Path) -> None:
        self._path = path

    @property
    def path(self) -> Path:
        return self._path

    def __call__(self, event: GraphEvent) -> None:
        """Write a single event to the audit log (EventBus handler)."""
        line = event.model_dump_json() + "\n"
        try:
            with GraphFileLock(self._path, exclusive=True, timeout=5.0), open(self._path, "a") as f:
                f.write(line)
        except Exception:
            logger.exception("Failed to write audit event %s", event.id)

    def read_events(self) -> list[dict]:
        """Read all events from the audit log (for diagnostics)."""
        if not self._path.exists():
            return []
        events = []
        with GraphFileLock(self._path, exclusive=False, timeout=5.0), open(self._path) as f:
            for line in f:
                stripped = line.strip()
                if stripped:
                    events.append(json.loads(stripped))
        return events

    def event_count(self) -> int:
        """Return the number of events in the audit log."""
        if not self._path.exists():
            return 0
        count = 0
        with open(self._path) as f:
            for line in f:
                if line.strip():
                    count += 1
        return count
