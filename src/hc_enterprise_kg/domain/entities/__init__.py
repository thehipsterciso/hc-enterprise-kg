"""Entity type definitions for the knowledge graph."""

from __future__ import annotations

from typing import Annotated, Union

from pydantic import Field

from hc_enterprise_kg.domain.entities.data_asset import DataAsset
from hc_enterprise_kg.domain.entities.department import Department
from hc_enterprise_kg.domain.entities.incident import Incident
from hc_enterprise_kg.domain.entities.location import Location
from hc_enterprise_kg.domain.entities.network import Network
from hc_enterprise_kg.domain.entities.person import Person
from hc_enterprise_kg.domain.entities.policy import Policy
from hc_enterprise_kg.domain.entities.role import Role
from hc_enterprise_kg.domain.entities.system import System
from hc_enterprise_kg.domain.entities.threat_actor import ThreatActor
from hc_enterprise_kg.domain.entities.vendor import Vendor
from hc_enterprise_kg.domain.entities.vulnerability import Vulnerability

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
