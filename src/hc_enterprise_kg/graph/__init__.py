"""High-level knowledge graph facade."""

from hc_enterprise_kg.graph.events import EventBus
from hc_enterprise_kg.graph.knowledge_graph import KnowledgeGraph

__all__ = ["EventBus", "KnowledgeGraph"]
