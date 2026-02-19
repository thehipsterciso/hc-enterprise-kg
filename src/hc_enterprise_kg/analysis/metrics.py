"""Graph metrics and analysis for the enterprise knowledge graph."""

from __future__ import annotations

from typing import Any

import networkx as nx

from hc_enterprise_kg.graph.knowledge_graph import KnowledgeGraph


def compute_centrality(kg: KnowledgeGraph) -> dict[str, float]:
    """Compute degree centrality for all entities."""
    g = kg.engine.get_native_graph()
    return nx.degree_centrality(g)


def compute_betweenness_centrality(kg: KnowledgeGraph) -> dict[str, float]:
    """Compute betweenness centrality for all entities."""
    g = kg.engine.get_native_graph()
    return nx.betweenness_centrality(g)


def compute_pagerank(kg: KnowledgeGraph) -> dict[str, float]:
    """Compute PageRank for all entities."""
    g = kg.engine.get_native_graph()
    return nx.pagerank(g)


def find_most_connected(kg: KnowledgeGraph, top_n: int = 10) -> list[tuple[str, int]]:
    """Find the top N most connected entities by degree."""
    g = kg.engine.get_native_graph()
    degrees = sorted(g.degree(), key=lambda x: x[1], reverse=True)
    return degrees[:top_n]


def compute_clustering_coefficient(kg: KnowledgeGraph) -> float:
    """Compute average clustering coefficient (undirected projection)."""
    g = kg.engine.get_native_graph()
    undirected = g.to_undirected()
    return nx.average_clustering(undirected)


def get_connected_components(kg: KnowledgeGraph) -> list[set[str]]:
    """Get weakly connected components."""
    g = kg.engine.get_native_graph()
    return [c for c in nx.weakly_connected_components(g)]


def compute_risk_score(kg: KnowledgeGraph, entity_id: str) -> dict[str, Any]:
    """Compute a risk score for an entity based on graph topology.

    Factors:
    - Number of vulnerabilities affecting connected systems
    - Criticality of connected systems
    - Number of hops from internet-facing systems
    - Data sensitivity of connected assets
    """
    from hc_enterprise_kg.domain.base import EntityType

    entity = kg.get_entity(entity_id)
    if not entity:
        return {"entity_id": entity_id, "risk_score": 0.0, "error": "Entity not found"}

    score = 0.0
    factors: dict[str, Any] = {}

    # Factor 1: Connected vulnerabilities
    vuln_neighbors = kg.neighbors(entity_id, entity_type=EntityType.VULNERABILITY)
    vuln_count = len(vuln_neighbors)
    critical_vulns = sum(1 for v in vuln_neighbors if getattr(v, "severity", "") == "critical")
    score += vuln_count * 10 + critical_vulns * 25
    factors["vulnerabilities"] = vuln_count
    factors["critical_vulnerabilities"] = critical_vulns

    # Factor 2: Degree centrality (more connections = higher exposure)
    g = kg.engine.get_native_graph()
    if entity_id in g:
        degree = g.degree(entity_id)
        score += degree * 2
        factors["degree"] = degree

    # Factor 3: Internet exposure
    system_neighbors = kg.neighbors(entity_id, entity_type=EntityType.SYSTEM)
    internet_facing = sum(1 for s in system_neighbors if getattr(s, "is_internet_facing", False))
    score += internet_facing * 20
    factors["internet_facing_connections"] = internet_facing

    # Normalize to 0-100
    risk_score = min(100.0, score)

    return {
        "entity_id": entity_id,
        "entity_name": entity.name,
        "risk_score": round(risk_score, 1),
        "factors": factors,
    }
