"""Graph state management for the MCP server.

Manages the module-level KnowledgeGraph instance and mtime-based
auto-reload so the server detects when graph.json changes on disk.
"""

from __future__ import annotations

import logging
import os
from pathlib import Path

from graph.knowledge_graph import KnowledgeGraph
from ingest.json_ingestor import JSONIngestor

logger = logging.getLogger(__name__)

# Module-level KG instance shared across all tool invocations.
_kg: KnowledgeGraph | None = None
_loaded_path: str | None = None
_loaded_mtime: float = 0.0


class NoGraphError(Exception):
    """Sentinel — caught at the tool boundary and turned into a dict."""


def load_graph(path: str) -> dict:
    """Load a JSON knowledge-graph file, replacing the current graph.

    Returns statistics about the loaded graph or an error dict.
    """
    global _kg, _loaded_path, _loaded_mtime  # noqa: PLW0603

    ingestor = JSONIngestor()
    result = ingestor.ingest(path)

    if result.errors:
        return {"error": f"Failed to load graph: {'; '.join(result.errors)}"}

    kg = KnowledgeGraph()
    if result.entities:
        kg.add_entities_bulk(result.entities)
    if result.relationships:
        kg.add_relationships_bulk(result.relationships)

    _kg = kg
    resolved = str(Path(path).resolve())
    _loaded_path = resolved
    try:
        _loaded_mtime = os.path.getmtime(resolved)
    except OSError:
        _loaded_mtime = 0.0

    stats = kg.statistics
    return {
        "status": "ok",
        "entity_count": stats["entity_count"],
        "relationship_count": stats["relationship_count"],
        "entity_types": stats.get("entity_types", {}),
        "relationship_types": stats.get("relationship_types", {}),
    }


def _maybe_reload() -> None:
    """Re-load the graph file if its mtime has changed since last load."""
    global _loaded_mtime  # noqa: PLW0603
    if _loaded_path is None:
        return
    try:
        current_mtime = os.path.getmtime(_loaded_path)
    except OSError:
        return
    if current_mtime != _loaded_mtime:
        logger.info("Graph file changed on disk — reloading %s", _loaded_path)
        load_graph(_loaded_path)


def require_graph() -> KnowledgeGraph:
    """Return the loaded KG or raise NoGraphError."""
    _maybe_reload()
    if _kg is None:
        raise NoGraphError
    return _kg


def auto_load_default_graph() -> None:
    """Load the graph from HCKG_DEFAULT_GRAPH env var if set."""
    path = os.environ.get("HCKG_DEFAULT_GRAPH")
    if path and Path(path).exists():
        load_graph(path)
