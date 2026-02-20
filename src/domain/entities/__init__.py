"""Entity type definitions for the knowledge graph."""

from __future__ import annotations

from typing import Annotated

from pydantic import Field

from domain.entities.control import Control
from domain.entities.data_asset import DataAsset
from domain.entities.department import Department
from domain.entities.incident import Incident
from domain.entities.integration import Integration
from domain.entities.location import Location
from domain.entities.network import Network
from domain.entities.person import Person
from domain.entities.policy import Policy
from domain.entities.regulation import Regulation
from domain.entities.risk import Risk
from domain.entities.role import Role
from domain.entities.data_domain import DataDomain
from domain.entities.data_flow import DataFlow
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
    | OrganizationalUnit
    | BusinessCapability
    | Site
    | Geography
    | Jurisdiction
    | ProductPortfolio
    | Product
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
