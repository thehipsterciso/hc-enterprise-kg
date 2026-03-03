"""RelExtractorAgent — processes relationship suggestions from enrichment results.

Wraps the relationship enricher logic. Takes ENRICHMENT_RESULT messages and
extracts relationship suggestions (new edges, updated weights), forwarding
them alongside the field updates to the SchemaAlignerAgent.

KARMA mapping: Relationship Extraction Agent — identifies and extracts
relationships between entities from the enrichment results.
"""

from __future__ import annotations

import logging

from enrichment.karma.base_agent import (
    AbstractKarmaAgent,
    AgentMessage,
    AgentRole,
    MessageType,
    PipelineState,
)

logger = logging.getLogger(__name__)


class RelExtractorAgent(AbstractKarmaAgent):
    """Processes relationship suggestions from enrichment results.

    For each ENRICHMENT_RESULT, extracts any relationship_suggestions
    and forwards them alongside the field updates. The relationship
    suggestions include new edges, updated weights, and confidence scores.

    This agent doesn't modify enrichment results — it annotates them
    with relationship metadata for downstream processing.
    """

    @property
    def role(self) -> AgentRole:
        return AgentRole.RELATIONSHIP_EXTRACTOR

    def process(
        self,
        message: AgentMessage,
        state: PipelineState,
    ) -> list[AgentMessage]:
        """Extract relationship suggestions and forward to SchemaAligner.

        Args:
            message: ENRICHMENT_RESULT with entity + result.
            state: Current pipeline state.

        Returns:
            List containing one message forwarded to SchemaAligner.
        """
        if message.message_type != MessageType.ENRICHMENT_RESULT:
            return []

        result = message.payload.get("result")
        if result is None:
            return []

        # Extract relationship suggestions from the result
        rel_suggestions = result.relationship_suggestions or []

        if rel_suggestions:
            logger.debug(
                f"RelExtractorAgent: {len(rel_suggestions)} relationship "
                f"suggestions for {message.payload.get('entity_id', '')}"
            )

        # Forward everything to SchemaAligner (field updates + relationships)
        return [
            self.create_message(
                recipient=AgentRole.SCHEMA_ALIGNER,
                message_type=MessageType.ENRICHMENT_RESULT,
                payload={
                    **message.payload,
                    "relationship_suggestions": rel_suggestions,
                },
                correlation_id=message.correlation_id,
                metadata=message.metadata,
            )
        ]
