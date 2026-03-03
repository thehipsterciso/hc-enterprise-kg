"""EnrichmentProfile ABC — base class for industry profiles.

Each profile defines which entity types and fields to prioritize during enrichment,
focusing on industry-specific concerns and providing OSINT sources for that profile.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from domain.base import EntityType


class EnrichmentProfile(ABC):
    """Abstract base class for enrichment profiles.

    A profile defines priority enrichment strategies for an industry:
    - which entity types to prioritize
    - which fields to populate based on tier
    - which OSINT sources to consult
    - focus areas (e.g., tech stack coherence, risk coverage, data classification)

    Subclasses implement tech, financial, healthcare profiles.
    """

    name: str = "Base Profile"

    @abstractmethod
    def should_populate_field(self, entity_type: EntityType, field: str, tier: int) -> bool:
        """Determine if a field should be populated for an entity at this tier.

        Args:
            entity_type: The entity type being enriched.
            field: The field name to check.
            tier: The enrichment tier (1-5).

        Returns:
            True if this profile should populate the field at this tier.
        """
        ...

    @abstractmethod
    def get_focus_areas(self) -> list[str]:
        """Get the focus areas (e.g., 'technology_stack', 'risk_coverage', 'data_classification').

        Returns:
            List of focus area names for this profile.
        """
        ...

    @abstractmethod
    def get_enrichment_priority(self) -> list[EntityType]:
        """Get entity types in priority order for this profile.

        Earlier in the list = higher priority.

        Returns:
            List of EntityType in priority order.
        """
        ...

    @abstractmethod
    def get_osint_sources(self) -> list[str]:
        """Get OSINT sources to consult for this profile.

        Used when osint_enabled=True in enrichment CLI.

        Returns:
            List of OSINT source names (e.g., 'shodan', 'censys', 'cve_feeds').
        """
        ...
