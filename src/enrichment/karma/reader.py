"""ReaderAgent — retrieves graph context and OSINT data for entities.

Wraps the existing GraphContextEngine and OSINTResearchAgent. For each
entity in an ENTITY_BATCH, retrieves the full graph neighborhood and
optionally runs OSINT research, producing ENTITY_CONTEXT messages.

KARMA mapping: Reader Agent — reads and interprets source material,
extracting relevant information for downstream processing.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from enrichment.karma.base_agent import (
    AbstractKarmaAgent,
    AgentMessage,
    AgentRole,
    MessageType,
    PipelineState,
)

if TYPE_CHECKING:
    from enrichment.base import OSINTResults
    from enrichment.graph_context import GraphContextEngine
    from enrichment.osint_agent import OSINTResearchAgent
    from graph.knowledge_graph import KnowledgeGraph

logger = logging.getLogger(__name__)


class ReaderAgent(AbstractKarmaAgent):
    """Retrieves graph context and OSINT data for entities being enriched.

    Wraps GraphContextEngine.get_entity_context() and optionally invokes
    the OSINTResearchAgent for external grounding.

    Args:
        knowledge_graph: The KnowledgeGraph instance.
        graph_context_engine: GraphContextEngine for neighborhood retrieval.
        osint_agent: Optional OSINTResearchAgent for external research.
    """

    def __init__(
        self,
        knowledge_graph: KnowledgeGraph,
        graph_context_engine: GraphContextEngine,
        osint_agent: OSINTResearchAgent | None = None,
    ) -> None:
        self._kg = knowledge_graph
        self._graph_context = graph_context_engine
        self._osint_agent = osint_agent

    @property
    def role(self) -> AgentRole:
        return AgentRole.READER

    def process(
        self,
        message: AgentMessage,
        state: PipelineState,
    ) -> list[AgentMessage]:
        """Retrieve context for each entity in the batch.

        Responds to ENTITY_BATCH messages by looking up each entity's
        graph neighborhood and producing ENTITY_CONTEXT messages.

        Args:
            message: ENTITY_BATCH with entity_ids payload.
            state: Current pipeline state.

        Returns:
            List of ENTITY_CONTEXT messages, one per entity.
        """
        if message.message_type != MessageType.ENTITY_BATCH:
            return []

        entity_ids: list[str] = message.payload.get("entity_ids", [])
        entity_type: str = message.payload.get("entity_type", "")
        tier: int = message.metadata.get("tier", state.current_tier)
        messages: list[AgentMessage] = []

        for entity_id in entity_ids:
            try:
                entity = self._kg.get_entity(entity_id)
                if entity is None:
                    logger.warning(f"ReaderAgent: entity {entity_id} not found")
                    continue

                # Get graph context
                context = self._graph_context.get_entity_context(entity_id)

                # Optional OSINT research
                osint: OSINTResults | None = None
                if self._osint_agent:
                    try:
                        osint = self._osint_agent.research(entity)
                    except Exception as e:
                        logger.debug(f"OSINT research failed for {entity_id}: {e}")

                messages.append(
                    self.create_message(
                        recipient=AgentRole.SUMMARIZER,
                        message_type=MessageType.ENTITY_CONTEXT,
                        payload={
                            "entity_id": entity_id,
                            "entity_type": entity_type,
                            "context": context,
                            "osint": osint,
                            "entity": entity,
                        },
                        correlation_id=message.correlation_id,
                        metadata={"tier": tier},
                    )
                )

            except Exception as e:
                logger.error(f"ReaderAgent error for {entity_id}: {e}")
                state.entities_failed += 1

        return messages
