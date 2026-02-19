"""Pre-built query library for common enterprise KG analysis."""

from __future__ import annotations

from hc_enterprise_kg.domain.base import BaseEntity, EntityType, RelationshipType
from hc_enterprise_kg.graph.knowledge_graph import KnowledgeGraph


def find_attack_paths(
    kg: KnowledgeGraph,
    source_entity_id: str,
    target_entity_id: str,
) -> list[str] | None:
    """Find the shortest attack path between two entities."""
    return kg.shortest_path(source_entity_id, target_entity_id)


def get_blast_radius(
    kg: KnowledgeGraph,
    entity_id: str,
    max_depth: int = 3,
) -> list[BaseEntity]:
    """Get all entities reachable from the given entity within max_depth hops."""
    visited: set[str] = set()
    queue: list[tuple[str, int]] = [(entity_id, 0)]
    result: list[BaseEntity] = []

    while queue:
        current_id, depth = queue.pop(0)
        if current_id in visited or depth > max_depth:
            continue
        visited.add(current_id)

        entity = kg.get_entity(current_id)
        if entity and current_id != entity_id:
            result.append(entity)

        if depth < max_depth:
            neighbors = kg.neighbors(current_id)
            for neighbor in neighbors:
                if neighbor.id not in visited:
                    queue.append((neighbor.id, depth + 1))

    return result


def find_critical_systems(kg: KnowledgeGraph) -> list[BaseEntity]:
    """Find all systems marked as critical."""
    return kg.query().entities(EntityType.SYSTEM).where(criticality="critical").execute()


def find_unpatched_vulnerabilities(kg: KnowledgeGraph) -> list[BaseEntity]:
    """Find open vulnerabilities without patches."""
    vulns = kg.list_entities(entity_type=EntityType.VULNERABILITY)
    return [
        v for v in vulns
        if getattr(v, "status", "") == "open" and not getattr(v, "patch_available", True)
    ]


def find_internet_facing_systems(kg: KnowledgeGraph) -> list[BaseEntity]:
    """Find all internet-facing systems."""
    return kg.query().entities(EntityType.SYSTEM).where(is_internet_facing=True).execute()


def find_privileged_users(kg: KnowledgeGraph) -> list[BaseEntity]:
    """Find people with privileged roles."""
    privileged_roles = kg.query().entities(EntityType.ROLE).where(is_privileged=True).execute()
    privileged_people: list[BaseEntity] = []
    seen: set[str] = set()

    for role in privileged_roles:
        people = kg.neighbors(
            role.id,
            direction="in",
            relationship_type=RelationshipType.HAS_ROLE,
            entity_type=EntityType.PERSON,
        )
        for person in people:
            if person.id not in seen:
                seen.add(person.id)
                privileged_people.append(person)

    return privileged_people


def find_vendor_dependencies(kg: KnowledgeGraph, vendor_id: str) -> list[BaseEntity]:
    """Find all systems that depend on a specific vendor."""
    return kg.neighbors(
        vendor_id,
        direction="in",
        relationship_type=RelationshipType.SUPPLIED_BY,
        entity_type=EntityType.SYSTEM,
    )


def find_high_risk_data_assets(kg: KnowledgeGraph) -> list[BaseEntity]:
    """Find data assets with restricted or confidential classification."""
    assets = kg.list_entities(entity_type=EntityType.DATA_ASSET)
    return [
        a for a in assets
        if getattr(a, "classification", "") in ("restricted", "confidential")
    ]
