"""EntityExtractorAgent — dispatches to the 30 entity-type enrichers.

Wraps the EnricherRegistry to dispatch enrichment to the appropriate
entity-type enricher. Takes ENTITY_SUMMARY messages and produces
ENRICHMENT_RESULT messages containing field updates and provenance.

KARMA mapping: Entity Extraction Agent — identifies and extracts
structured entity information from the summarized source material.
In our adaptation, this means running the domain-specific enricher
for each entity type.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from domain.base import EntityType
from enrichment.base import (
    EnricherRegistry,
    EnrichmentProfile,
    EnrichmentTier,
)
from enrichment.karma.base_agent import (
    AbstractKarmaAgent,
    AgentMessage,
    AgentRole,
    MessageType,
    PipelineState,
)

logger = logging.getLogger(__name__)

# Mapping of tier levels to EnrichmentTier enums
TIER_LEVEL_MAP = {
    1: EnrichmentTier.BASIC,
    2: EnrichmentTier.BASIC,
    3: EnrichmentTier.STANDARD,
    4: EnrichmentTier.DEEP,
    5: EnrichmentTier.DEEP,
}


class EntityExtractorAgent(AbstractKarmaAgent):
    """Dispatches enrichment to the 30 entity-type enrichers.

    For each entity, looks up the registered enricher via EnricherRegistry
    and invokes its enrich() method with the full graph context and OSINT
    results from upstream agents.

    No enricher logic is modified — this agent is purely a dispatcher.
    """

    @property
    def role(self) -> AgentRole:
        return AgentRole.ENTITY_EXTRACTOR

    def process(
        self,
        message: AgentMessage,
        state: PipelineState,
    ) -> list[AgentMessage]:
        """Run the entity-type enricher and forward results.

        Responds to ENTITY_SUMMARY messages by invoking the registered
        enricher and producing ENRICHMENT_RESULT messages.

        Args:
            message: ENTITY_SUMMARY with entity + context + osint + profile.
            state: Current pipeline state.

        Returns:
            List containing one ENRICHMENT_RESULT message (or empty on error).
        """
        if message.message_type != MessageType.ENTITY_SUMMARY:
            return []

        entity = message.payload.get("entity")
        context = message.payload.get("context")
        osint = message.payload.get("osint")
        entity_type_str = message.payload.get("entity_type", "")
        tier = message.metadata.get("tier", state.current_tier)

        if entity is None or context is None:
            logger.warning("EntityExtractorAgent: missing entity or context")
            return []

        # Look up the enricher
        try:
            entity_type = EntityType(entity_type_str)
        except ValueError:
            logger.warning(f"Unknown entity type: {entity_type_str}")
            return []

        if not EnricherRegistry.is_registered(entity_type):
            logger.debug(f"No enricher registered for {entity_type_str}")
            return []

        enricher_class = EnricherRegistry.get(entity_type)
        enricher = enricher_class()
        tier_enum = TIER_LEVEL_MAP.get(tier, EnrichmentTier.BASIC)

        try:
            result = enricher.enrich(
                entity,
                context,
                osint=osint,
                tier=tier_enum,
            )

            if not result.has_updates():
                state.entities_processed += 1
                return []

            return [
                self.create_message(
                    recipient=AgentRole.RELATIONSHIP_EXTRACTOR,
                    message_type=MessageType.ENRICHMENT_RESULT,
                    payload={
                        "entity_id": entity.id,
                        "entity_type": entity_type_str,
                        "entity": entity,
                        "result": result,
                    },
                    correlation_id=message.correlation_id,
                    metadata=message.metadata,
                )
            ]

        except Exception as e:
            logger.error(
                f"EntityExtractorAgent error for {entity_type_str} "
                f"{entity.id}: {e}",
                exc_info=True,
            )
            state.entities_failed += 1
            return []
