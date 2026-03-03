"""KARMA Multi-Agent Pipeline for Knowledge Graph Enrichment.

Implements the KARMA framework (Lu et al., NeurIPS 2025) adapted for
enterprise knowledge graph enrichment. Nine specialized agents form a
sequential pipeline where each agent handles a distinct phase of the
enrichment lifecycle.

Pipeline flow:
    ControllerAgent → IngestionAgent → ReaderAgent → SummarizerAgent
    → EntityExtractorAgent → RelExtractorAgent → SchemaAlignerAgent
    → ConflictResolverAgent → EvaluatorAgent

Each agent wraps existing enrichment infrastructure (enrichers, graph
context engine, OSINT agent, provenance reconciler) rather than
reimplementing it. The KARMA layer provides coordination, state
management, and a formal agent communication protocol.

See ADR-014 for architectural rationale.
"""

from __future__ import annotations

from enrichment.karma.base_agent import (
    AbstractKarmaAgent,
    AgentMessage,
    AgentRole,
    MessageType,
    PipelineState,
    PipelineStatus,
)

__all__ = [
    "AbstractKarmaAgent",
    "AgentMessage",
    "AgentRole",
    "MessageType",
    "PipelineState",
    "PipelineStatus",
]
