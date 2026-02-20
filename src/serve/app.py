"""Lightweight REST API that exposes the knowledge graph to any HTTP client.

Designed to be LLM-agnostic: Claude Desktop (via MCP), ChatGPT custom GPTs,
OpenAI function calling, LangChain agents, or plain curl can all consume it.

Run via CLI:
    hckg serve graph.json
    hckg serve graph.json --port 8420 --host 0.0.0.0
"""

from __future__ import annotations

import json
import re
from collections import deque
from pathlib import Path
from typing import Any

import networkx as nx
from rapidfuzz import fuzz, process

from domain.base import BaseEntity, EntityType, RelationshipType
from graph.knowledge_graph import KnowledgeGraph
from ingest.json_ingestor import JSONIngestor
from rag.retriever import GraphRAGRetriever

# ---------------------------------------------------------------------------
# Module-level state
# ---------------------------------------------------------------------------

_kg: KnowledgeGraph | None = None
_retriever = GraphRAGRetriever()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _require_graph() -> KnowledgeGraph:
    if _kg is None:
        raise _NoGraphError
    return _kg


class _NoGraphError(Exception):
    pass


def _compact_entity(entity: BaseEntity) -> dict[str, Any]:
    raw = entity.model_dump(mode="json")
    skip = {"created_at", "updated_at", "metadata", "valid_from", "valid_until", "version"}
    return {k: v for k, v in raw.items() if k not in skip and v is not None and v != "" and v != []}


def _compact_relationship(rel: Any) -> dict[str, Any]:
    raw = rel.model_dump(mode="json")
    skip = {"created_at", "updated_at", "valid_from", "valid_until", "version"}
    return {k: v for k, v in raw.items() if k not in skip and v is not None and v != "" and v != {}}


def _json_response(data: Any, status: int = 200) -> tuple[str, int, dict]:
    """Return a JSON response tuple compatible with Flask."""
    body = json.dumps(data, default=str, indent=2)
    return body, status, {"Content-Type": "application/json"}


def _error(msg: str, status: int = 400) -> tuple[str, int, dict]:
    return _json_response({"error": msg}, status)


_SAFE_ID_RE = re.compile(r"^[a-zA-Z0-9\-_\.]+$")


def _is_safe_id(value: str) -> bool:
    """Return True if *value* contains only safe characters for an entity ID."""
    return bool(value) and bool(_SAFE_ID_RE.match(value))


# ---------------------------------------------------------------------------
# Load graph into memory
# ---------------------------------------------------------------------------


def load_graph_from_path(path: str) -> dict:
    """Load a JSON graph file and return stats."""
    global _kg  # noqa: PLW0603

    p = Path(path)
    if not p.exists():
        return {"error": f"File not found: {path}"}

    ingestor = JSONIngestor()
    result = ingestor.ingest(str(p))

    if result.errors:
        return {"error": f"Failed to load: {'; '.join(result.errors)}"}

    kg = KnowledgeGraph()
    if result.entities:
        kg.add_entities_bulk(result.entities)
    if result.relationships:
        kg.add_relationships_bulk(result.relationships)

    _kg = kg
    stats = kg.statistics
    return {
        "status": "ok",
        "entity_count": stats["entity_count"],
        "relationship_count": stats["relationship_count"],
        "entity_types": stats.get("entity_types", {}),
        "relationship_types": stats.get("relationship_types", {}),
    }


# ---------------------------------------------------------------------------
# API endpoint handlers (framework-agnostic — return dicts)
# ---------------------------------------------------------------------------


def handle_statistics() -> dict:
    kg = _require_graph()
    return kg.statistics


def handle_list_entities(entity_type: str = "", limit: int = 50) -> list[dict]:
    kg = _require_graph()
    et: EntityType | None = None
    if entity_type:
        try:
            et = EntityType(entity_type)
        except ValueError:
            valid = [e.value for e in EntityType]
            return [{"error": f"Unknown entity_type '{entity_type}'. Valid: {valid}"}]
    entities = kg.list_entities(entity_type=et, limit=limit)
    return [_compact_entity(e) for e in entities]


def handle_get_entity(entity_id: str) -> dict:
    kg = _require_graph()
    entity = kg.get_entity(entity_id)
    if entity is None:
        return {"error": f"Entity '{entity_id}' not found."}
    return _compact_entity(entity)


def handle_get_neighbors(
    entity_id: str,
    direction: str = "both",
    relationship_type: str = "",
) -> list[dict]:
    kg = _require_graph()
    if direction not in ("in", "out", "both"):
        return [{"error": f"Invalid direction '{direction}'."}]

    rt: RelationshipType | None = None
    if relationship_type:
        try:
            rt = RelationshipType(relationship_type)
        except ValueError:
            valid = [r.value for r in RelationshipType]
            return [{"error": f"Unknown relationship_type '{relationship_type}'. Valid: {valid}"}]

    neighbors = kg.neighbors(entity_id, direction=direction, relationship_type=rt)
    rels = kg.get_relationships(entity_id, direction=direction, relationship_type=rt)

    rel_lookup: dict[str, list[dict]] = {}
    for rel in rels:
        other_id = rel.target_id if rel.source_id == entity_id else rel.source_id
        rel_lookup.setdefault(other_id, []).append(_compact_relationship(rel))

    results = []
    for neighbor in neighbors:
        results.append(
            {
                "entity": _compact_entity(neighbor),
                "relationships": rel_lookup.get(neighbor.id, []),
            }
        )
    return results


def handle_shortest_path(source_id: str, target_id: str) -> dict:
    kg = _require_graph()
    path_ids = kg.shortest_path(source_id, target_id)
    if path_ids is None:
        return {"error": f"No path between '{source_id}' and '{target_id}'."}

    path_entities = []
    for eid in path_ids:
        entity = kg.get_entity(eid)
        if entity:
            path_entities.append(_compact_entity(entity))
        else:
            path_entities.append({"id": eid, "error": "entity not found"})

    return {"path_length": len(path_ids) - 1, "path": path_entities}


def handle_blast_radius(entity_id: str, max_depth: int = 3) -> dict:
    kg = _require_graph()
    if kg.get_entity(entity_id) is None:
        return {"error": f"Entity '{entity_id}' not found."}

    visited: set[str] = set()
    queue: deque[tuple[str, int]] = deque([(entity_id, 0)])
    by_depth: dict[int, list[dict]] = {}

    while queue:
        current_id, depth = queue.popleft()
        if current_id in visited or depth > max_depth:
            continue
        visited.add(current_id)

        if current_id != entity_id:
            entity = kg.get_entity(current_id)
            if entity:
                by_depth.setdefault(depth, []).append(_compact_entity(entity))

        if depth < max_depth:
            for neighbor in kg.neighbors(current_id):
                if neighbor.id not in visited:
                    queue.append((neighbor.id, depth + 1))

    total = sum(len(v) for v in by_depth.values())
    return {
        "entity_id": entity_id,
        "max_depth": max_depth,
        "total_affected": total,
        "by_depth": {str(k): v for k, v in sorted(by_depth.items())},
    }


def handle_centrality(metric: str = "degree", top_n: int = 20) -> list[dict]:
    kg = _require_graph()
    g = kg.engine.get_native_graph()

    if metric == "degree":
        scores = nx.degree_centrality(g)
    elif metric == "betweenness":
        scores = nx.betweenness_centrality(g)
    elif metric == "pagerank":
        scores = nx.pagerank(g)
    else:
        return [{"error": f"Unknown metric '{metric}'. Choose degree, betweenness, or pagerank."}]

    ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)[:top_n]

    results = []
    for eid, score in ranked:
        entity = kg.get_entity(eid)
        if entity:
            results.append(
                {
                    "id": eid,
                    "name": entity.name,
                    "entity_type": entity.entity_type.value,
                    "score": round(score, 6),
                }
            )
    return results


def handle_search(query: str, entity_type: str = "", limit: int = 20) -> list[dict]:
    kg = _require_graph()
    et: EntityType | None = None
    if entity_type:
        try:
            et = EntityType(entity_type)
        except ValueError:
            valid = [e.value for e in EntityType]
            return [{"error": f"Unknown entity_type '{entity_type}'. Valid: {valid}"}]

    all_entities = kg.list_entities(entity_type=et)
    if not all_entities:
        return []

    name_to_entities: dict[str, list[BaseEntity]] = {}
    for entity in all_entities:
        name_to_entities.setdefault(entity.name, []).append(entity)

    names = list(name_to_entities.keys())
    matches = process.extract(query, names, scorer=fuzz.WRatio, limit=limit)

    results: list[dict] = []
    for name, score, _idx in matches:
        if score < 50.0:
            continue
        for entity in name_to_entities[name]:
            entry = _compact_entity(entity)
            entry["match_score"] = round(score, 1)
            results.append(entry)

    results.sort(key=lambda x: x["match_score"], reverse=True)
    return results[:limit]


def handle_ask(question: str, top_k: int = 20) -> dict:
    """GraphRAG-powered question answering: pass a question, get graph context back."""
    kg = _require_graph()
    result = _retriever.retrieve(question, kg, top_k=top_k)
    return {
        "context": result.context,
        "entities": [_compact_entity(e) for e in result.entities],
        "relationships": [_compact_relationship(r) for r in result.relationships],
        "stats": result.stats,
    }


# ---------------------------------------------------------------------------
# OpenAI-compatible tool definitions
# ---------------------------------------------------------------------------


_STAT_DESC = (
    "Return high-level statistics about the knowledge graph: "
    "entity and relationship counts by type, density, connectivity."
)
_ETYPE_DESC = "Filter by entity type (person, department, system, etc.). Leave empty for all."
_BLAST_DESC = "Compute all entities reachable within N hops of a given entity (blast radius)."
_SEARCH_DESC = "Fuzzy search entities by name. Returns matching entities with match scores."
_ASK_DESC = (
    "Ask a natural-language question and get relevant graph "
    "context via GraphRAG. Returns entities, relationships, "
    "and a formatted context string."
)
_QUESTION_DESC = "Natural language question about the organization."

OPENAI_TOOLS: list[dict] = [
    {
        "type": "function",
        "function": {
            "name": "get_statistics",
            "description": _STAT_DESC,
            "parameters": {
                "type": "object",
                "properties": {},
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "list_entities",
            "description": ("List entities in the knowledge graph, optionally filtered by type."),
            "parameters": {
                "type": "object",
                "properties": {
                    "entity_type": {
                        "type": "string",
                        "description": _ETYPE_DESC,
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Max entities (default 50).",
                        "default": 50,
                    },
                },
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_entity",
            "description": "Get full details for an entity by ID.",
            "parameters": {
                "type": "object",
                "properties": {
                    "entity_id": {
                        "type": "string",
                        "description": "UUID of the entity.",
                    },
                },
                "required": ["entity_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_neighbors",
            "description": "Get entities directly connected to an entity.",
            "parameters": {
                "type": "object",
                "properties": {
                    "entity_id": {
                        "type": "string",
                        "description": "UUID of the entity.",
                    },
                    "direction": {
                        "type": "string",
                        "enum": ["in", "out", "both"],
                        "description": "Direction (default: both).",
                        "default": "both",
                    },
                    "relationship_type": {
                        "type": "string",
                        "description": (
                            "Filter by relationship type (works_in, depends_on, etc.)."
                        ),
                    },
                },
                "required": ["entity_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "find_shortest_path",
            "description": "Find the shortest path between two entities.",
            "parameters": {
                "type": "object",
                "properties": {
                    "source_id": {
                        "type": "string",
                        "description": "UUID of the start entity.",
                    },
                    "target_id": {
                        "type": "string",
                        "description": "UUID of the end entity.",
                    },
                },
                "required": ["source_id", "target_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_blast_radius",
            "description": _BLAST_DESC,
            "parameters": {
                "type": "object",
                "properties": {
                    "entity_id": {
                        "type": "string",
                        "description": "UUID of the starting entity.",
                    },
                    "max_depth": {
                        "type": "integer",
                        "description": "Maximum hops (default 3).",
                        "default": 3,
                    },
                },
                "required": ["entity_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "compute_centrality",
            "description": "Compute centrality scores for top entities.",
            "parameters": {
                "type": "object",
                "properties": {
                    "metric": {
                        "type": "string",
                        "enum": ["degree", "betweenness", "pagerank"],
                        "description": "Algorithm (default: degree).",
                        "default": "degree",
                    },
                    "top_n": {
                        "type": "integer",
                        "description": "Top entities (default 20).",
                        "default": 20,
                    },
                },
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "search_entities",
            "description": _SEARCH_DESC,
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search text to match.",
                    },
                    "entity_type": {
                        "type": "string",
                        "description": "Optional entity type filter.",
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Max results (default 20).",
                        "default": 20,
                    },
                },
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "ask_graph",
            "description": _ASK_DESC,
            "parameters": {
                "type": "object",
                "properties": {
                    "question": {
                        "type": "string",
                        "description": _QUESTION_DESC,
                    },
                    "top_k": {
                        "type": "integer",
                        "description": "Max entities (default 20).",
                        "default": 20,
                    },
                },
                "required": ["question"],
            },
        },
    },
]


# ---------------------------------------------------------------------------
# Flask app factory
# ---------------------------------------------------------------------------


def create_app(graph_path: str | None = None) -> Any:
    """Create and configure the Flask application.

    Args:
        graph_path: Optional path to a JSON graph file to load on startup.

    Returns:
        A Flask app instance.
    """
    try:
        from flask import Flask
        from flask import request as flask_request
    except ImportError as exc:
        raise ImportError(
            "Flask is required for the REST API server. Install it with:\n"
            "  poetry install --extras api\n"
            "  # or: pip install flask"
        ) from exc

    app = Flask(__name__)

    if graph_path:
        with app.app_context():
            result = load_graph_from_path(graph_path)
            if "error" in result:
                raise RuntimeError(f"Failed to load graph: {result['error']}")

    # --- Routes ---

    @app.route("/", methods=["GET"])
    def index():  # type: ignore[no-untyped-def]
        return _json_response(
            {
                "service": "hc-enterprise-kg",
                "version": "0.1.0",
                "endpoints": [
                    "GET  /               — This index",
                    "GET  /health         — Health check",
                    "GET  /statistics     — Graph statistics",
                    "GET  /entities       — List entities",
                    "GET  /entities/<id>  — Entity by ID",
                    "GET  /entities/<id>/neighbors — Neighbors",
                    "GET  /path/<src>/<tgt> — Shortest path",
                    "GET  /blast-radius/<id> — Blast radius",
                    "GET  /centrality     — Centrality scores",
                    "GET  /search         — Fuzzy search",
                    "POST /ask            — GraphRAG Q&A",
                    "GET  /openai/tools   — OpenAI tool defs",
                    "POST /openai/call    — Execute a tool",
                    "POST /load           — Load a graph file",
                ],
            }
        )

    @app.route("/health", methods=["GET"])
    def health():  # type: ignore[no-untyped-def]
        has_graph = _kg is not None
        stats = _kg.statistics if _kg else {}
        return _json_response(
            {
                "status": "ok",
                "graph_loaded": has_graph,
                "entity_count": stats.get("entity_count", 0),
                "relationship_count": stats.get("relationship_count", 0),
            }
        )

    @app.route("/statistics", methods=["GET"])
    def statistics():  # type: ignore[no-untyped-def]
        try:
            return _json_response(handle_statistics())
        except _NoGraphError:
            return _error("No graph loaded. POST to /load first.", 409)

    @app.route("/entities", methods=["GET"])
    def list_entities_route():  # type: ignore[no-untyped-def]
        try:
            entity_type = flask_request.args.get("type", "")
            limit = int(flask_request.args.get("limit", "50"))
            return _json_response(handle_list_entities(entity_type, limit))
        except _NoGraphError:
            return _error("No graph loaded.", 409)

    @app.route("/entities/<entity_id>", methods=["GET"])
    def get_entity_route(entity_id: str):  # type: ignore[no-untyped-def]
        if not _is_safe_id(entity_id):
            return _error("Invalid entity ID format.", 400)
        try:
            result = handle_get_entity(entity_id)
            if "error" in result:
                return _error("Entity not found.", 404)
            return _json_response(result)
        except _NoGraphError:
            return _error("No graph loaded.", 409)

    @app.route("/entities/<entity_id>/neighbors", methods=["GET"])
    def get_neighbors_route(entity_id: str):  # type: ignore[no-untyped-def]
        if not _is_safe_id(entity_id):
            return _error("Invalid entity ID format.", 400)
        try:
            direction = flask_request.args.get("direction", "both")
            rel_type = flask_request.args.get("relationship_type", "")
            return _json_response(handle_get_neighbors(entity_id, direction, rel_type))
        except _NoGraphError:
            return _error("No graph loaded.", 409)

    @app.route("/path/<source_id>/<target_id>", methods=["GET"])
    def shortest_path_route(source_id: str, target_id: str):  # type: ignore[no-untyped-def]
        if not _is_safe_id(source_id) or not _is_safe_id(target_id):
            return _error("Invalid entity ID format.", 400)
        try:
            result = handle_shortest_path(source_id, target_id)
            if "error" in result:
                return _error("No path found between the specified entities.", 404)
            return _json_response(result)
        except _NoGraphError:
            return _error("No graph loaded.", 409)

    @app.route("/blast-radius/<entity_id>", methods=["GET"])
    def blast_radius_route(entity_id: str):  # type: ignore[no-untyped-def]
        if not _is_safe_id(entity_id):
            return _error("Invalid entity ID format.", 400)
        try:
            max_depth = int(flask_request.args.get("max_depth", "3"))
            result = handle_blast_radius(entity_id, max_depth)
            if "error" in result:
                return _error("Entity not found.", 404)
            return _json_response(result)
        except _NoGraphError:
            return _error("No graph loaded.", 409)

    @app.route("/centrality", methods=["GET"])
    def centrality_route():  # type: ignore[no-untyped-def]
        try:
            metric = flask_request.args.get("metric", "degree")
            top_n = int(flask_request.args.get("top_n", "20"))
            return _json_response(handle_centrality(metric, top_n))
        except _NoGraphError:
            return _error("No graph loaded.", 409)

    @app.route("/search", methods=["GET"])
    def search_route():  # type: ignore[no-untyped-def]
        try:
            q = flask_request.args.get("q", "")
            if not q:
                return _error("Missing required query parameter 'q'.")
            entity_type = flask_request.args.get("type", "")
            limit = int(flask_request.args.get("limit", "20"))
            return _json_response(handle_search(q, entity_type, limit))
        except _NoGraphError:
            return _error("No graph loaded.", 409)

    @app.route("/ask", methods=["POST"])
    def ask_route():  # type: ignore[no-untyped-def]
        try:
            data = flask_request.get_json(silent=True) or {}
            question = data.get("question", "")
            if not question:
                return _error("Missing 'question' in request body.")
            top_k = int(data.get("top_k", 20))
            return _json_response(handle_ask(question, top_k))
        except _NoGraphError:
            return _error("No graph loaded.", 409)

    @app.route("/load", methods=["POST"])
    def load_route():  # type: ignore[no-untyped-def]
        data = flask_request.get_json(silent=True) or {}
        path = data.get("path", "")
        if not path:
            return _error("Missing 'path' in request body.")
        result = load_graph_from_path(path)
        if "error" in result:
            return _error(result["error"])
        return _json_response(result)

    # --- OpenAI-compatible endpoints ---

    @app.route("/openai/tools", methods=["GET"])
    def openai_tools():  # type: ignore[no-untyped-def]
        return _json_response(OPENAI_TOOLS)

    @app.route("/openai/call", methods=["POST"])
    def openai_call():  # type: ignore[no-untyped-def]
        """Execute a tool by name with arguments — for function-calling agents."""
        try:
            data = flask_request.get_json(silent=True) or {}
            name = data.get("name", "")
            arguments = data.get("arguments", {})

            dispatch: dict[str, Any] = {
                "get_statistics": lambda args: handle_statistics(),
                "list_entities": lambda args: handle_list_entities(
                    args.get("entity_type", ""), args.get("limit", 50)
                ),
                "get_entity": lambda args: handle_get_entity(args["entity_id"]),
                "get_neighbors": lambda args: handle_get_neighbors(
                    args["entity_id"],
                    args.get("direction", "both"),
                    args.get("relationship_type", ""),
                ),
                "find_shortest_path": lambda args: handle_shortest_path(
                    args["source_id"], args["target_id"]
                ),
                "get_blast_radius": lambda args: handle_blast_radius(
                    args["entity_id"], args.get("max_depth", 3)
                ),
                "compute_centrality": lambda args: handle_centrality(
                    args.get("metric", "degree"), args.get("top_n", 20)
                ),
                "search_entities": lambda args: handle_search(
                    args["query"], args.get("entity_type", ""), args.get("limit", 20)
                ),
                "ask_graph": lambda args: handle_ask(args["question"], args.get("top_k", 20)),
            }

            handler = dispatch.get(name)
            if handler is None:
                return _error(f"Unknown tool. Available: {list(dispatch.keys())}")

            result = handler(arguments)
            return _json_response({"result": result})

        except _NoGraphError:
            return _error("No graph loaded. POST to /load first.", 409)
        except KeyError:
            return _error("Missing required argument in tool call.")

    return app
