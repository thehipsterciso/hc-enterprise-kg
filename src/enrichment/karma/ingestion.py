"""IngestionAgent — loads and batches entities for the KARMA pipeline.

Extracts the entity iteration and batching logic from the original
EnrichmentOrchestrator. Loads entities from the KnowledgeGraph in
GENERATION_ORDER and produces ENTITY_BATCH messages for downstream agents.

KARMA mapping: Ingestion Agent — responsible for sourcing raw data
(in our case, entities from the knowledge graph) and preparing it
for the enrichment pipeline.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from domain.base import EntityType
from enrichment.base import EnricherRegistry
from enrichment.karma.base_agent import (
    AbstractKarmaAgent,
    AgentMessage,
    AgentRole,
    MessageType,
    PipelineState,
)
from synthetic.orchestrator import GENERATION_ORDER

if TYPE_CHECKING:
    from graph.knowledge_graph import KnowledgeGraph

logger = logging.getLogger(__name__)


class IngestionAgent(AbstractKarmaAgent):
    """Loads entities from the knowledge graph and batches them for enrichment.

    Iterates entity types in GENERATION_ORDER, skipping types without
    registered enrichers. Produces one ENTITY_BATCH message per entity type
    containing the list of entities to enrich.

    Args:
        knowledge_graph: The KnowledgeGraph to load entities from.
    """

    def __init__(self, knowledge_graph: KnowledgeGraph) -> None:
        self._kg = knowledge_graph

    @property
    def role(self) -> AgentRole:
        return AgentRole.INGESTION

    def process(
        self,
        message: AgentMessage,
        state: PipelineState,
    ) -> list[AgentMessage]:
        """Load entities from the graph and produce batched messages.

        Responds to PIPELINE_START messages by loading all entities in
        generation order and producing ENTITY_BATCH messages.

        Args:
            message: Expected to be PIPELINE_START with tier info.
            state: Current pipeline state.

        Returns:
            List of ENTITY_BATCH messages, one per entity type.
        """
        if message.message_type != MessageType.PIPELINE_START:
            return []

        messages: list[AgentMessage] = []
        total_entities = 0

        for entity_type, _ in GENERATION_ORDER:
            if not EnricherRegistry.is_registered(entity_type):
                continue

            entities = self._kg.list_entities(entity_type)
            if not entities:
                continue

            total_entities += len(entities)

            messages.append(
                self.create_message(
                    recipient=AgentRole.READER,
                    message_type=MessageType.ENTITY_BATCH,
                    payload={
                        "entity_type": entity_type.value,
                        "entity_ids": [e.id for e in entities],
                        "count": len(entities),
                    },
                    correlation_id=f"tier-{state.current_tier}-{entity_type.value}",
                    metadata={"tier": state.current_tier},
                )
            )

        logger.info(
            f"IngestionAgent: loaded {total_entities} entities across "
            f"{len(messages)} entity types"
        )

        state.entities_queued = total_entities
        return messages
