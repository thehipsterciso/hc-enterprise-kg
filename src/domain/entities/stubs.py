"""Stub entity classes for enterprise ontology types not yet fully implemented.

Each stub is a minimal BaseEntity subclass with the correct ENTITY_TYPE.
As each layer branch is built, the stub is replaced by a full implementation
in its own file (e.g., regulation.py, control.py, etc.) and removed from
this file.

Stubs accept arbitrary extra fields via BaseEntity's extra="allow" config,
so JSON data with full attribute sets can be ingested even before the
detailed entity class is built.
"""

from __future__ import annotations

from typing import ClassVar, Literal

from domain.base import BaseEntity, EntityType

# --- L01: Compliance & Governance ---


class Regulation(BaseEntity):
    """Stub: external regulatory requirement. Full implementation in L01."""

    ENTITY_TYPE: ClassVar[EntityType] = EntityType.REGULATION
    entity_type: Literal[EntityType.REGULATION] = EntityType.REGULATION


class Control(BaseEntity):
    """Stub: security or compliance control. Full implementation in L01."""

    ENTITY_TYPE: ClassVar[EntityType] = EntityType.CONTROL
    entity_type: Literal[EntityType.CONTROL] = EntityType.CONTROL


class Risk(BaseEntity):
    """Stub: identified risk. Full implementation in L01."""

    ENTITY_TYPE: ClassVar[EntityType] = EntityType.RISK
    entity_type: Literal[EntityType.RISK] = EntityType.RISK


class Threat(BaseEntity):
    """Stub: threat to the enterprise. Full implementation in L01."""

    ENTITY_TYPE: ClassVar[EntityType] = EntityType.THREAT
    entity_type: Literal[EntityType.THREAT] = EntityType.THREAT


# --- L02: Technology & Systems ---


class Integration(BaseEntity):
    """Stub: system-to-system integration. Full implementation in L02."""

    ENTITY_TYPE: ClassVar[EntityType] = EntityType.INTEGRATION
    entity_type: Literal[EntityType.INTEGRATION] = EntityType.INTEGRATION


# --- L03: Data Assets ---


class DataDomain(BaseEntity):
    """Stub: data governance domain. Full implementation in L03."""

    ENTITY_TYPE: ClassVar[EntityType] = EntityType.DATA_DOMAIN
    entity_type: Literal[EntityType.DATA_DOMAIN] = EntityType.DATA_DOMAIN


class DataFlow(BaseEntity):
    """Stub: data movement between systems. Full implementation in L03."""

    ENTITY_TYPE: ClassVar[EntityType] = EntityType.DATA_FLOW
    entity_type: Literal[EntityType.DATA_FLOW] = EntityType.DATA_FLOW


# --- L04: Organization ---


class OrganizationalUnit(BaseEntity):
    """Stub: organizational unit. Full implementation in L04."""

    ENTITY_TYPE: ClassVar[EntityType] = EntityType.ORGANIZATIONAL_UNIT
    entity_type: Literal[EntityType.ORGANIZATIONAL_UNIT] = EntityType.ORGANIZATIONAL_UNIT


# --- L06: Business Capabilities ---


class BusinessCapability(BaseEntity):
    """Stub: business capability. Full implementation in L06."""

    ENTITY_TYPE: ClassVar[EntityType] = EntityType.BUSINESS_CAPABILITY
    entity_type: Literal[EntityType.BUSINESS_CAPABILITY] = EntityType.BUSINESS_CAPABILITY


# --- L07: Locations & Facilities ---


class Site(BaseEntity):
    """Stub: physical site. Full implementation in L07."""

    ENTITY_TYPE: ClassVar[EntityType] = EntityType.SITE
    entity_type: Literal[EntityType.SITE] = EntityType.SITE


class Geography(BaseEntity):
    """Stub: geographic region. Full implementation in L07."""

    ENTITY_TYPE: ClassVar[EntityType] = EntityType.GEOGRAPHY
    entity_type: Literal[EntityType.GEOGRAPHY] = EntityType.GEOGRAPHY


class Jurisdiction(BaseEntity):
    """Stub: legal/regulatory jurisdiction. Full implementation in L07."""

    ENTITY_TYPE: ClassVar[EntityType] = EntityType.JURISDICTION
    entity_type: Literal[EntityType.JURISDICTION] = EntityType.JURISDICTION


# --- L08: Products & Services ---


class ProductPortfolio(BaseEntity):
    """Stub: product portfolio. Full implementation in L08."""

    ENTITY_TYPE: ClassVar[EntityType] = EntityType.PRODUCT_PORTFOLIO
    entity_type: Literal[EntityType.PRODUCT_PORTFOLIO] = EntityType.PRODUCT_PORTFOLIO


class Product(BaseEntity):
    """Stub: product or service offering. Full implementation in L08."""

    ENTITY_TYPE: ClassVar[EntityType] = EntityType.PRODUCT
    entity_type: Literal[EntityType.PRODUCT] = EntityType.PRODUCT


# --- L09: Customers & Markets ---


class MarketSegment(BaseEntity):
    """Stub: market segment. Full implementation in L09."""

    ENTITY_TYPE: ClassVar[EntityType] = EntityType.MARKET_SEGMENT
    entity_type: Literal[EntityType.MARKET_SEGMENT] = EntityType.MARKET_SEGMENT


class Customer(BaseEntity):
    """Stub: customer account. Full implementation in L09."""

    ENTITY_TYPE: ClassVar[EntityType] = EntityType.CUSTOMER
    entity_type: Literal[EntityType.CUSTOMER] = EntityType.CUSTOMER


# --- L10: Vendors & Partners ---


class Contract(BaseEntity):
    """Stub: vendor/partner contract. Full implementation in L10."""

    ENTITY_TYPE: ClassVar[EntityType] = EntityType.CONTRACT
    entity_type: Literal[EntityType.CONTRACT] = EntityType.CONTRACT


# --- L11: Strategic Initiatives ---


class Initiative(BaseEntity):
    """Stub: strategic initiative. Full implementation in L11."""

    ENTITY_TYPE: ClassVar[EntityType] = EntityType.INITIATIVE
    entity_type: Literal[EntityType.INITIATIVE] = EntityType.INITIATIVE
