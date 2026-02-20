"""Entity and relationship type registry for plugin discovery."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from domain.base import BaseEntity, EntityType


class EntityRegistry:
    """Registry for entity type classes.

    Supports dynamic registration so users can add custom entity types
    without modifying core code.
    """

    _registry: dict[EntityType, type[BaseEntity]] = {}

    @classmethod
    def register(cls, entity_type: EntityType, entity_class: type[BaseEntity]) -> None:
        cls._registry[entity_type] = entity_class

    @classmethod
    def get(cls, entity_type: EntityType) -> type[BaseEntity]:
        if entity_type not in cls._registry:
            raise KeyError(f"No entity class registered for type: {entity_type}")
        return cls._registry[entity_type]

    @classmethod
    def all_types(cls) -> list[EntityType]:
        return list(cls._registry.keys())

    @classmethod
    def is_registered(cls, entity_type: EntityType) -> bool:
        return entity_type in cls._registry

    @classmethod
    def clear(cls) -> None:
        cls._registry.clear()

    @classmethod
    def auto_discover(cls) -> None:
        """Auto-register all built-in entity classes.

        Registers v0.1 original types first, then enterprise ontology
        stubs for types not yet fully implemented. As each layer branch
        replaces a stub with a full implementation, the import moves
        from stubs.py to the dedicated module.
        """
        from domain.entities import (
            DataAsset,
            Department,
            Incident,
            Location,
            Network,
            Person,
            Policy,
            Role,
            System,
            ThreatActor,
            Vendor,
            Vulnerability,
        )
        from domain.entities.control import Control
        from domain.entities.data_domain import DataDomain
        from domain.entities.data_flow import DataFlow
        from domain.entities.integration import Integration
        from domain.entities.regulation import Regulation
        from domain.entities.risk import Risk
        from domain.entities.stubs import (
            BusinessCapability,
            Contract,
            Customer,
            Geography,
            Initiative,
            Jurisdiction,
            MarketSegment,
            OrganizationalUnit,
            Product,
            ProductPortfolio,
            Site,
        )
        from domain.entities.threat import Threat

        for entity_class in [
            # v0.1 original types
            Person,
            Department,
            Role,
            System,
            Network,
            DataAsset,
            Policy,
            Vendor,
            Location,
            Vulnerability,
            ThreatActor,
            Incident,
            # L01: Compliance & Governance (full implementations)
            Regulation,
            Control,
            Risk,
            Threat,
            # L02: Technology & Systems (full implementations)
            Integration,
            # L03: Data Assets (full implementations)
            DataDomain,
            DataFlow,
            OrganizationalUnit,
            BusinessCapability,
            Site,
            Geography,
            Jurisdiction,
            ProductPortfolio,
            Product,
            MarketSegment,
            Customer,
            Contract,
            Initiative,
        ]:
            cls.register(entity_class.ENTITY_TYPE, entity_class)
