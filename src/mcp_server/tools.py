"""MCP tool definitions for the Enterprise Knowledge Graph.

Each function is registered as an MCP tool via the ``mcp`` FastMCP instance
imported from :mod:`mcp_server.server`.
"""

from __future__ import annotations

from typing import Any

from rapidfuzz import fuzz, process

from domain.base import BaseEntity, BaseRelationship, EntityType, RelationshipType
from domain.registry import EntityRegistry
from mcp_server.helpers import compact_entity, compact_relationship
from mcp_server.state import NoGraphError, load_graph, persist_graph, require_graph
from mcp_server.validation import validate_entity_input, validate_relationship_input


def register_tools(mcp):  # noqa: ANN001
    """Register all MCP tools on the given FastMCP instance."""

    @mcp.tool()
    def load_graph_tool(path: str) -> dict:
        """Load a JSON knowledge-graph file into the server.

        The file must follow the standard hc-enterprise-kg JSON export format
        (keys: entities, relationships).  Call this before using any other tool.

        Args:
            path: Absolute or relative path to the JSON graph file.

        Returns:
            Statistics about the loaded graph (entity count, relationship count,
            entity types, etc.) or an error message.
        """
        return load_graph(path)

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
            kg = require_graph()
        except NoGraphError:
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
            kg = require_graph()
        except NoGraphError:
            return [{"error": "No graph loaded. Call load_graph first."}]

        et: EntityType | None = None
        if entity_type:
            try:
                et = EntityType(entity_type)
            except ValueError:
                valid = [e.value for e in EntityType]
                return [{"error": f"Unknown entity_type '{entity_type}'. Valid types: {valid}"}]

        entities = kg.list_entities(entity_type=et, limit=limit)
        return [compact_entity(e) for e in entities]

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
            kg = require_graph()
        except NoGraphError:
            return {"error": "No graph loaded. Call load_graph first."}

        entity = kg.get_entity(entity_id)
        if entity is None:
            return {"error": f"Entity '{entity_id}' not found."}
        return compact_entity(entity)

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
            kg = require_graph()
        except NoGraphError:
            return [{"error": "No graph loaded. Call load_graph first."}]

        if direction not in ("in", "out", "both"):
            return [{"error": f"Invalid direction '{direction}'. Must be 'in', 'out', or 'both'."}]

        rt: RelationshipType | None = None
        if relationship_type:
            try:
                rt = RelationshipType(relationship_type)
            except ValueError:
                valid = [r.value for r in RelationshipType]
                return [
                    {"error": f"Unknown relationship_type '{relationship_type}'. Valid: {valid}"}
                ]

        neighbors = kg.neighbors(entity_id, direction=direction, relationship_type=rt)
        rels = kg.get_relationships(entity_id, direction=direction, relationship_type=rt)

        rel_lookup: dict[str, list[dict]] = {}
        for rel in rels:
            other_id = rel.target_id if rel.source_id == entity_id else rel.source_id
            rel_lookup.setdefault(other_id, []).append(compact_relationship(rel))

        results = []
        for neighbor in neighbors:
            entry: dict[str, Any] = {
                "entity": compact_entity(neighbor),
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
            kg = require_graph()
        except NoGraphError:
            return {"error": "No graph loaded. Call load_graph first."}

        path_ids = kg.shortest_path(source_id, target_id)
        if path_ids is None:
            return {"error": f"No path found between '{source_id}' and '{target_id}'."}

        path_entities = []
        for eid in path_ids:
            entity = kg.get_entity(eid)
            if entity:
                path_entities.append(compact_entity(entity))
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
            kg = require_graph()
        except NoGraphError:
            return {"error": "No graph loaded. Call load_graph first."}

        if kg.get_entity(entity_id) is None:
            return {"error": f"Entity '{entity_id}' not found."}

        by_depth = kg.blast_radius(entity_id, max_depth)
        serialised: dict[str, list[dict]] = {}
        total = 0
        for depth in sorted(by_depth):
            serialised[str(depth)] = [compact_entity(e) for e in by_depth[depth]]
            total += len(by_depth[depth])

        return {
            "entity_id": entity_id,
            "max_depth": max_depth,
            "total_affected": total,
            "by_depth": serialised,
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
            kg = require_graph()
        except NoGraphError:
            return [{"error": "No graph loaded. Call load_graph first."}]

        engine = kg.engine

        if metric == "degree":
            ranked = engine.degree_centrality(top_n=20)
        elif metric == "betweenness":
            ranked = engine.betweenness_centrality(top_n=20)
        elif metric == "pagerank":
            ranked = engine.pagerank(top_n=20)
        else:
            return [
                {"error": f"Unknown metric '{metric}'. Choose degree, betweenness, or pagerank."}
            ]

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
            kg = require_graph()
        except NoGraphError:
            return [{"error": "No graph loaded. Call load_graph first."}]

        ranked = kg.engine.most_connected(top_n=top_n)

        results = []
        for eid, degree in ranked:
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
            kg = require_graph()
        except NoGraphError:
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
                entry = compact_entity(entity)
                entry["match_score"] = round(score, 1)
                results.append(entry)

        results.sort(key=lambda x: x["match_score"], reverse=True)
        return results[:limit]

    # ------------------------------------------------------------------ #
    #  Write tools                                                        #
    # ------------------------------------------------------------------ #

    @mcp.tool()
    def add_relationship_tool(
        relationship_type: str,
        source_id: str,
        target_id: str,
        weight: float = 1.0,
        confidence: float = 1.0,
        properties: dict | None = None,
    ) -> dict:
        """Add a validated relationship between two existing entities.

        Enforces the RELATIONSHIP_SCHEMA domain/range constraints so only
        semantically valid edges can be created.  The graph is automatically
        persisted to disk after a successful write.

        Args:
            relationship_type: One of the 55 valid relationship types
                (e.g. "depends_on", "supports", "subject_to").
            source_id: ID of the source entity (must already exist).
            target_id: ID of the target entity (must already exist).
            weight: Edge weight 0.0-1.0 (default 1.0).
            confidence: Confidence score 0.0-1.0 (default 1.0).
            properties: Optional dict of additional properties.

        Returns:
            The created relationship summary, or an error dict.
        """
        try:
            kg = require_graph()
        except NoGraphError:
            return {"error": "No graph loaded. Call load_graph first."}

        # Validate inputs
        ok, reason = validate_relationship_input(
            kg,
            relationship_type,
            source_id,
            target_id,
        )
        if not ok:
            return {"error": reason}

        # Clamp weight/confidence to valid range
        weight = max(0.0, min(1.0, weight))
        confidence = max(0.0, min(1.0, confidence))

        # Create and add
        rel = BaseRelationship(
            relationship_type=RelationshipType(relationship_type),
            source_id=source_id,
            target_id=target_id,
            weight=weight,
            confidence=confidence,
            properties=properties or {},
        )
        rel_id = kg.add_relationship(rel)

        # Persist to disk
        err = persist_graph()
        if err:
            return err

        return {
            "status": "ok",
            "relationship_id": rel_id,
            "relationship": compact_relationship(rel),
        }

    @mcp.tool()
    def add_relationships_batch(relationships: list[dict]) -> dict:
        """Add multiple validated relationships in one call.

        Validates ALL inputs before committing ANY — if any item fails
        validation, nothing is written.  A single persist happens at the end.

        Each dict in the list must contain:
            relationship_type (str), source_id (str), target_id (str)
        Optional per-item keys:
            weight (float, default 1.0), confidence (float, default 1.0),
            properties (dict)

        Args:
            relationships: List of relationship dicts to create.

        Returns:
            Summary with created count and relationship IDs, or
            per-item validation errors.
        """
        try:
            kg = require_graph()
        except NoGraphError:
            return {"error": "No graph loaded. Call load_graph first."}

        if not relationships:
            return {"error": "Empty relationships list."}

        if len(relationships) > 500:
            count = len(relationships)
            return {"error": f"Too many relationships ({count}). Maximum is 500 per batch."}

        # Phase 1: validate all
        errors: list[dict] = []
        for i, item in enumerate(relationships):
            rel_type = item.get("relationship_type", "")
            src = item.get("source_id", "")
            tgt = item.get("target_id", "")

            if not rel_type or not src or not tgt:
                errors.append(
                    {
                        "index": i,
                        "error": "Missing required field"
                        " (relationship_type, source_id, or target_id).",
                    }
                )
                continue

            ok, reason = validate_relationship_input(kg, rel_type, src, tgt)
            if not ok:
                errors.append({"index": i, "error": reason})

        if errors:
            return {"status": "error", "errors": errors, "committed": 0}

        # Phase 2: commit all
        created: list[dict] = []
        for item in relationships:
            weight = max(0.0, min(1.0, float(item.get("weight", 1.0))))
            confidence = max(0.0, min(1.0, float(item.get("confidence", 1.0))))
            rel = BaseRelationship(
                relationship_type=RelationshipType(item["relationship_type"]),
                source_id=item["source_id"],
                target_id=item["target_id"],
                weight=weight,
                confidence=confidence,
                properties=item.get("properties") or {},
            )
            rel_id = kg.add_relationship(rel)
            created.append({"relationship_id": rel_id, "relationship": compact_relationship(rel)})

        # Phase 3: single persist
        err = persist_graph()
        if err:
            return err

        return {"status": "ok", "committed": len(created), "relationships": created}

    @mcp.tool()
    def remove_relationship_tool(relationship_id: str) -> dict:
        """Remove a relationship by its ID.

        The graph is automatically persisted to disk after removal.

        Args:
            relationship_id: The ID of the relationship to remove.

        Returns:
            The removed relationship info, or an error dict.
        """
        try:
            kg = require_graph()
        except NoGraphError:
            return {"error": "No graph loaded. Call load_graph first."}

        rel = kg.get_relationship(relationship_id)
        if rel is None:
            return {"error": f"Relationship '{relationship_id}' not found."}

        info = compact_relationship(rel)
        success = kg.remove_relationship(relationship_id)
        if not success:
            return {"error": f"Failed to remove relationship '{relationship_id}'."}

        err = persist_graph()
        if err:
            return err

        return {"status": "ok", "removed": info}

    # ------------------------------------------------------------------ #
    #  Entity CRUD tools                                                  #
    # ------------------------------------------------------------------ #

    @mcp.tool()
    def add_entity_tool(
        entity_type: str,
        name: str,
        description: str = "",
        properties: dict | None = None,
    ) -> dict:
        """Add a new entity to the knowledge graph.

        Creates a concrete Pydantic entity of the given type using the
        EntityRegistry.  An ID is auto-generated (UUID).

        Args:
            entity_type: One of the 30 valid entity types
                (e.g. "system", "person", "vendor").
            name: Display name for the entity.
            description: Optional description.
            properties: Optional dict of type-specific fields
                (e.g. {"status": "active"} for a System).

        Returns:
            The created entity summary, or an error dict.
        """
        try:
            kg = require_graph()
        except NoGraphError:
            return {"error": "No graph loaded. Call load_graph first."}

        ok, reason = validate_entity_input(entity_type, name, description)
        if not ok:
            return {"error": reason}

        et = EntityType(entity_type)
        try:
            entity_cls = EntityRegistry.get(et)
        except KeyError:
            return {"error": f"No entity class registered for '{entity_type}'."}

        # Build kwargs — name + description + any extra properties
        kwargs: dict[str, Any] = {"name": name}
        if description:
            kwargs["description"] = description
        if properties:
            kwargs.update(properties)

        try:
            entity = entity_cls(**kwargs)
        except Exception as exc:
            return {"error": f"Failed to create entity: {exc}"}

        entity_id = kg.add_entity(entity)

        err = persist_graph()
        if err:
            return err

        return {
            "status": "ok",
            "entity_id": entity_id,
            "entity": compact_entity(entity),
        }

    @mcp.tool()
    def update_entity_tool(
        entity_id: str,
        updates: dict,
    ) -> dict:
        """Update fields on an existing entity.

        Applies the given key-value updates to the entity. The engine
        validates the result via copy-validate-write.

        Args:
            entity_id: ID of the entity to update.
            updates: Dict of field names to new values.

        Returns:
            The updated entity summary, or an error dict.
        """
        try:
            kg = require_graph()
        except NoGraphError:
            return {"error": "No graph loaded. Call load_graph first."}

        if not updates:
            return {"error": "No updates provided."}

        existing = kg.get_entity(entity_id)
        if existing is None:
            return {"error": f"Entity '{entity_id}' not found."}

        try:
            updated = kg.update_entity(entity_id, **updates)
        except (KeyError, ValueError, TypeError) as exc:
            return {"error": f"Update failed: {exc}"}

        err = persist_graph()
        if err:
            return err

        return {
            "status": "ok",
            "entity_id": entity_id,
            "entity": compact_entity(updated),
        }

    @mcp.tool()
    def remove_entity_tool(entity_id: str) -> dict:
        """Remove an entity and all its relationships from the graph.

        The engine automatically removes all edges connected to the
        entity.  The graph is persisted to disk after removal.

        Args:
            entity_id: ID of the entity to remove.

        Returns:
            The removed entity summary, or an error dict.
        """
        try:
            kg = require_graph()
        except NoGraphError:
            return {"error": "No graph loaded. Call load_graph first."}

        entity = kg.get_entity(entity_id)
        if entity is None:
            return {"error": f"Entity '{entity_id}' not found."}

        info = compact_entity(entity)
        success = kg.remove_entity(entity_id)
        if not success:
            return {"error": f"Failed to remove entity '{entity_id}'."}

        err = persist_graph()
        if err:
            return err

        return {"status": "ok", "removed": info}
