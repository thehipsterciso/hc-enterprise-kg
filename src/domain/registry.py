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
        from domain.entities.business_capability import BusinessCapability
        from domain.entities.contract import Contract
        from domain.entities.control import Control
        from domain.entities.customer import Customer
        from domain.entities.data_domain import DataDomain
        from domain.entities.data_flow import DataFlow
        from domain.entities.geography import Geography
        from domain.entities.integration import Integration
        from domain.entities.jurisdiction import Jurisdiction
        from domain.entities.market_segment import MarketSegment
        from domain.entities.organizational_unit import OrganizationalUnit
        from domain.entities.product import Product
        from domain.entities.product_portfolio import ProductPortfolio
        from domain.entities.regulation import Regulation
        from domain.entities.risk import Risk
        from domain.entities.site import Site
        from domain.entities.stubs import (
            Initiative,
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
            # L04: Organization (full implementations)
            OrganizationalUnit,
            # L06: Business Capabilities (full implementations)
            BusinessCapability,
            # L07: Locations & Facilities (full implementations)
            Site,
            Geography,
            Jurisdiction,
            # L08: Products & Services (full implementations)
            ProductPortfolio,
            Product,
            # L09: Customers & Markets (full implementations)
            MarketSegment,
            Customer,
            # L10: Vendors & Partners (full implementations)
            Contract,
            Initiative,
        ]:
            cls.register(entity_class.ENTITY_TYPE, entity_class)
