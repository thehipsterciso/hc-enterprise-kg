"""Entity type definitions for the knowledge graph."""

from __future__ import annotations

from typing import Annotated, Union

from pydantic import Field

from domain.entities.data_asset import DataAsset
from domain.entities.department import Department
from domain.entities.incident import Incident
from domain.entities.location import Location
from domain.entities.network import Network
from domain.entities.person import Person
from domain.entities.policy import Policy
from domain.entities.role import Role
from domain.entities.system import System
from domain.entities.threat_actor import ThreatActor
from domain.entities.vendor import Vendor
from domain.entities.vulnerability import Vulnerability

AnyEntity = Annotated[
    Union[
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
    ],
    Field(discriminator="entity_type"),
]

__all__ = [
    "AnyEntity",
    "DataAsset",
    "Department",
    "Incident",
    "Location",
    "Network",
    "Person",
    "Policy",
    "Role",
    "System",
    "ThreatActor",
    "Vendor",
    "Vulnerability",
]
