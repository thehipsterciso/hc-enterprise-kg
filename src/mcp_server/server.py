"""MCP server for Claude Desktop integration with the Enterprise Knowledge Graph.

Exposes knowledge graph operations as MCP tools so Claude Desktop can
query, search, and analyse an enterprise KG interactively.
"""

from __future__ import annotations

from collections import deque
from typing import Any

import networkx as nx
from mcp.server.fastmcp import FastMCP
from rapidfuzz import fuzz, process

from domain.base import BaseEntity, EntityType, RelationshipType
from graph.knowledge_graph import KnowledgeGraph
from ingest.json_ingestor import JSONIngestor

mcp = FastMCP("hc-enterprise-kg")

# Module-level KG instance shared across all tool invocations.
_kg: KnowledgeGraph | None = None


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _require_graph() -> KnowledgeGraph:
    """Return the loaded KG or raise a helpful message."""
    if _kg is None:
        raise _NoGraphError
    return _kg


class _NoGraphError(Exception):
    """Sentinel – caught at the tool boundary and turned into a dict."""


def _compact_entity(entity: BaseEntity) -> dict[str, Any]:
    """Serialise an entity to a compact JSON-safe dict.

    Strips None/empty values and internal temporal/metadata fields to keep
    MCP responses small and LLM-friendly.
    """
    raw = entity.model_dump(mode="json")
    skip = {"created_at", "updated_at", "metadata", "valid_from", "valid_until", "version"}
    return {k: v for k, v in raw.items() if k not in skip and v is not None and v != "" and v != []}


def _compact_relationship(rel: Any) -> dict[str, Any]:
    raw = rel.model_dump(mode="json")
    skip = {"created_at", "updated_at", "valid_from", "valid_until", "version"}
    return {k: v for k, v in raw.items() if k not in skip and v is not None and v != "" and v != {}}


# ---------------------------------------------------------------------------
# Tools
# ---------------------------------------------------------------------------


@mcp.tool()
def load_graph(path: str) -> dict:
    """Load a JSON knowledge-graph file into the server.

    The file must follow the standard hc-enterprise-kg JSON export format
    (keys: entities, relationships).  Call this before using any other tool.

    Args:
        path: Absolute or relative path to the JSON graph file.

    Returns:
        Statistics about the loaded graph (entity count, relationship count,
        entity types, etc.) or an error message.
    """
    global _kg  # noqa: PLW0603

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
    stats = kg.statistics
    return {
        "status": "ok",
        "entity_count": stats["entity_count"],
        "relationship_count": stats["relationship_count"],
        "entity_types": stats.get("entity_types", {}),
        "relationship_types": stats.get("relationship_types", {}),
    }


@mcp.tool()
def get_statistics() -> dict:
    """Return high-level statistics about the currently loaded knowledge graph.

    Includes entity and relationship counts broken down by type, graph
    density, and weak-connectivity status.

    Returns:
        A dict with keys: entity_count, relationship_count, entity_types,
        relationship_types, density, is_weakly_connected.
    """
    try:
        kg = _require_graph()
    except _NoGraphError:
        return {"error": "No graph loaded. Call load_graph first."}
    return kg.statistics


@mcp.tool()
def list_entities(entity_type: str = "", limit: int = 50) -> list[dict]:
    """List entities in the knowledge graph, optionally filtered by type.

    Args:
        entity_type: Filter to a specific entity type (e.g. "person",
            "system", "department"). Leave empty to list all types.
        limit: Maximum number of entities to return (default 50).

    Returns:
        A list of compact entity dicts with key fields (id, name,
        entity_type, plus type-specific attributes).
    """
    try:
        kg = _require_graph()
    except _NoGraphError:
        return [{"error": "No graph loaded. Call load_graph first."}]

    et: EntityType | None = None
    if entity_type:
        try:
            et = EntityType(entity_type)
        except ValueError:
            valid = [e.value for e in EntityType]
            return [{"error": f"Unknown entity_type '{entity_type}'. Valid types: {valid}"}]

    entities = kg.list_entities(entity_type=et, limit=limit)
    return [_compact_entity(e) for e in entities]


@mcp.tool()
def get_entity(entity_id: str) -> dict:
    """Get full details for a single entity by its ID.

    Args:
        entity_id: The UUID of the entity to retrieve.

    Returns:
        A compact dict with all non-empty fields of the entity, or an
        error if not found.
    """
    try:
        kg = _require_graph()
    except _NoGraphError:
        return {"error": "No graph loaded. Call load_graph first."}

    entity = kg.get_entity(entity_id)
    if entity is None:
        return {"error": f"Entity '{entity_id}' not found."}
    return _compact_entity(entity)


@mcp.tool()
def get_neighbors(
    entity_id: str,
    direction: str = "both",
    relationship_type: str = "",
) -> list[dict]:
    """Get entities directly connected to a given entity.

    Args:
        entity_id: The UUID of the entity whose neighbors to retrieve.
        direction: "in", "out", or "both" (default "both").
        relationship_type: Optional filter by relationship type (e.g.
            "works_in", "depends_on"). Leave empty for all types.

    Returns:
        A list of dicts, each containing the neighbor entity summary and
        the connecting relationship info.
    """
    try:
        kg = _require_graph()
    except _NoGraphError:
        return [{"error": "No graph loaded. Call load_graph first."}]

    if direction not in ("in", "out", "both"):
        return [{"error": f"Invalid direction '{direction}'. Must be 'in', 'out', or 'both'."}]

    rt: RelationshipType | None = None
    if relationship_type:
        try:
            rt = RelationshipType(relationship_type)
        except ValueError:
            valid = [r.value for r in RelationshipType]
            return [{"error": f"Unknown relationship_type '{relationship_type}'. Valid: {valid}"}]

    neighbors = kg.neighbors(entity_id, direction=direction, relationship_type=rt)
    rels = kg.get_relationships(entity_id, direction=direction, relationship_type=rt)

    # Build a lookup of relationships keyed by the *other* entity id
    rel_lookup: dict[str, list[dict]] = {}
    for rel in rels:
        other_id = rel.target_id if rel.source_id == entity_id else rel.source_id
        rel_lookup.setdefault(other_id, []).append(_compact_relationship(rel))

    results = []
    for neighbor in neighbors:
        entry: dict[str, Any] = {
            "entity": _compact_entity(neighbor),
            "relationships": rel_lookup.get(neighbor.id, []),
        }
        results.append(entry)

    return results


@mcp.tool()
def find_shortest_path(source_id: str, target_id: str) -> dict:
    """Find the shortest path between two entities in the graph.

    Args:
        source_id: UUID of the starting entity.
        target_id: UUID of the destination entity.

    Returns:
        A dict with the ordered list of entity summaries along the path,
        or an error if no path exists.
    """
    try:
        kg = _require_graph()
    except _NoGraphError:
        return {"error": "No graph loaded. Call load_graph first."}

    path_ids = kg.shortest_path(source_id, target_id)
    if path_ids is None:
        return {"error": f"No path found between '{source_id}' and '{target_id}'."}

    path_entities = []
    for eid in path_ids:
        entity = kg.get_entity(eid)
        if entity:
            path_entities.append(_compact_entity(entity))
        else:
            path_entities.append({"id": eid, "error": "entity not found"})

    return {
        "path_length": len(path_ids) - 1,
        "path": path_entities,
    }


@mcp.tool()
def get_blast_radius(entity_id: str, max_depth: int = 3) -> dict:
    """Compute the blast radius of an entity — all entities reachable within N hops.

    Uses breadth-first traversal to find every entity that could be
    affected if the given entity is compromised or fails.

    Args:
        entity_id: UUID of the starting entity.
        max_depth: Maximum number of hops to traverse (default 3).

    Returns:
        A dict mapping hop distance (1, 2, ...) to lists of affected
        entity summaries, plus a total count.
    """
    try:
        kg = _require_graph()
    except _NoGraphError:
        return {"error": "No graph loaded. Call load_graph first."}

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


@mcp.tool()
def compute_centrality(metric: str = "degree") -> list[dict]:
    """Compute centrality scores and return the top 20 entities.

    Args:
        metric: Centrality algorithm — one of "degree", "betweenness",
            or "pagerank" (default "degree").

    Returns:
        A list of the top 20 entities by the chosen metric, each with
        id, name, entity_type, and score.
    """
    try:
        kg = _require_graph()
    except _NoGraphError:
        return [{"error": "No graph loaded. Call load_graph first."}]

    g = kg.engine.get_native_graph()

    if metric == "degree":
        scores = nx.degree_centrality(g)
    elif metric == "betweenness":
        scores = nx.betweenness_centrality(g)
    elif metric == "pagerank":
        scores = nx.pagerank(g)
    else:
        return [{"error": f"Unknown metric '{metric}'. Choose degree, betweenness, or pagerank."}]

    ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)[:20]

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


@mcp.tool()
def find_most_connected(top_n: int = 10) -> list[dict]:
    """Find the most connected entities by raw connection count.

    Args:
        top_n: Number of top entities to return (default 10).

    Returns:
        A list of entities sorted by degree (number of connections),
        each with id, name, entity_type, and degree.
    """
    try:
        kg = _require_graph()
    except _NoGraphError:
        return [{"error": "No graph loaded. Call load_graph first."}]

    g = kg.engine.get_native_graph()
    degrees = sorted(g.degree(), key=lambda x: x[1], reverse=True)[:top_n]

    results = []
    for eid, degree in degrees:
        entity = kg.get_entity(eid)
        if entity:
            results.append(
                {
                    "id": eid,
                    "name": entity.name,
                    "entity_type": entity.entity_type.value,
                    "degree": degree,
                }
            )
    return results


@mcp.tool()
def search_entities(
    query: str,
    entity_type: str = "",
    limit: int = 20,
) -> list[dict]:
    """Fuzzy text search across entity names.

    Uses rapidfuzz to find entities whose names best match the query
    string.  Optionally filter by entity type.

    Args:
        query: Search text to match against entity names.
        entity_type: Optional entity type filter (e.g. "person").
        limit: Maximum results to return (default 20).

    Returns:
        A list of matching entities with their match score (0-100).
    """
    try:
        kg = _require_graph()
    except _NoGraphError:
        return [{"error": "No graph loaded. Call load_graph first."}]

    et: EntityType | None = None
    if entity_type:
        try:
            et = EntityType(entity_type)
        except ValueError:
            valid = [e.value for e in EntityType]
            return [{"error": f"Unknown entity_type '{entity_type}'. Valid types: {valid}"}]

    all_entities = kg.list_entities(entity_type=et)
    if not all_entities:
        return []

    # Build name -> entities mapping
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


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


def main() -> None:
    """Run the MCP server over stdio transport."""
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
