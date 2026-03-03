"""SummarizerAgent — builds holistic entity profiles from graph context.

Wraps the existing GraphContextEngine.get_holistic_profile() method.
Takes ENTITY_CONTEXT messages and produces ENTITY_SUMMARY messages
that combine the graph neighborhood with OSINT findings into a
coherent profile for the entity enricher.

KARMA mapping: Summarizer Agent — condenses and organizes extracted
information into structured summaries for enrichment.
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
    from enrichment.graph_context import GraphContextEngine

logger = logging.getLogger(__name__)


class SummarizerAgent(AbstractKarmaAgent):
    """Builds holistic entity profiles from graph context and OSINT data.

    Combines the entity's graph neighborhood (from ReaderAgent) with
    any OSINT findings to produce a comprehensive profile that enrichers
    can use for context-aware enrichment decisions.

    Implements simple caching: if the same entity_id is summarized
    multiple times in a pipeline run, the cached profile is reused.

    Args:
        graph_context_engine: GraphContextEngine for profile building.
    """

    def __init__(self, graph_context_engine: GraphContextEngine) -> None:
        self._graph_context = graph_context_engine
        self._cache: dict[str, dict] = {}

    @property
    def role(self) -> AgentRole:
        return AgentRole.SUMMARIZER

    def on_pipeline_start(self, state: PipelineState) -> None:
        """Clear the profile cache at pipeline start."""
        self._cache.clear()

    def process(
        self,
        message: AgentMessage,
        state: PipelineState,
    ) -> list[AgentMessage]:
        """Build a holistic profile for the entity.

        Responds to ENTITY_CONTEXT messages by building a cross-entity
        profile and forwarding to the EntityExtractorAgent.

        Args:
            message: ENTITY_CONTEXT with entity + context + osint.
            state: Current pipeline state.

        Returns:
            List containing one ENTITY_SUMMARY message.
        """
        if message.message_type != MessageType.ENTITY_CONTEXT:
            return []

        entity_id = message.payload.get("entity_id", "")
        entity = message.payload.get("entity")
        context = message.payload.get("context")
        osint = message.payload.get("osint")

        # Check cache
        if entity_id in self._cache:
            profile = self._cache[entity_id]
        else:
            # Build holistic profile from graph traversal
            try:
                profile = self._graph_context.get_holistic_profile(entity_id)
            except Exception:
                profile = None

            # Cache the profile
            self._cache[entity_id] = profile

        return [
            self.create_message(
                recipient=AgentRole.ENTITY_EXTRACTOR,
                message_type=MessageType.ENTITY_SUMMARY,
                payload={
                    "entity_id": entity_id,
                    "entity_type": message.payload.get("entity_type", ""),
                    "entity": entity,
                    "context": context,
                    "osint": osint,
                    "holistic_profile": profile,
                },
                correlation_id=message.correlation_id,
                metadata=message.metadata,
            )
        ]
