"""Entity type definitions for the knowledge graph."""

from __future__ import annotations

from typing import Annotated

from pydantic import Field

from domain.entities.business_capability import BusinessCapability
from domain.entities.control import Control
from domain.entities.customer import Customer
from domain.entities.data_asset import DataAsset
from domain.entities.data_domain import DataDomain
from domain.entities.data_flow import DataFlow
from domain.entities.department import Department
from domain.entities.geography import Geography
from domain.entities.incident import Incident
from domain.entities.integration import Integration
from domain.entities.jurisdiction import Jurisdiction
from domain.entities.location import Location
from domain.entities.market_segment import MarketSegment
from domain.entities.network import Network
from domain.entities.organizational_unit import OrganizationalUnit
from domain.entities.person import Person
from domain.entities.policy import Policy
from domain.entities.product import Product
from domain.entities.product_portfolio import ProductPortfolio
from domain.entities.regulation import Regulation
from domain.entities.risk import Risk
from domain.entities.role import Role
from domain.entities.site import Site
from domain.entities.stubs import (
    Contract,
    Initiative,
)
from domain.entities.system import System
from domain.entities.threat import Threat
from domain.entities.threat_actor import ThreatActor
from domain.entities.vendor import Vendor
from domain.entities.vulnerability import Vulnerability

AnyEntity = Annotated[
    # v0.1 original types
    Person
    | Department
    | Role
    | System
    | Network
    | DataAsset
    | Policy
    | Vendor
    | Location
    | Vulnerability
    | ThreatActor
    | Incident
    # L01: Compliance & Governance (full implementations)
    | Regulation
    | Control
    | Risk
    | Threat
    # L02: Technology & Systems (full implementations)
    | Integration
    # L03: Data Assets (full implementations)
    | DataDomain
    | DataFlow
    # L04: Organization (full implementations)
    | OrganizationalUnit
    # L06: Business Capabilities (full implementations)
    | BusinessCapability
    # L07: Locations & Facilities (full implementations)
    | Site
    | Geography
    | Jurisdiction
    # L08: Products & Services (full implementations)
    | ProductPortfolio
    | Product
    # L09: Customers & Markets (full implementations)
    | MarketSegment
    | Customer
    | Contract
    | Initiative,
    Field(discriminator="entity_type"),
]

__all__ = [
    "AnyEntity",
    "BusinessCapability",
    "Contract",
    "Control",
    "Customer",
    "DataAsset",
    "DataDomain",
    "DataFlow",
    "Department",
    "Geography",
    "Incident",
    "Initiative",
    "Integration",
    "Jurisdiction",
    "Location",
    "MarketSegment",
    "Network",
    "OrganizationalUnit",
    "Person",
    "Policy",
    "Product",
    "ProductPortfolio",
    "Regulation",
    "Risk",
    "Role",
    "Site",
    "System",
    "Threat",
    "ThreatActor",
    "Vendor",
    "Vulnerability",
]
