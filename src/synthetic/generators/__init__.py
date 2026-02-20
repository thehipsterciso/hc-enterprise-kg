"""Synthetic data generators for all entity types.

Importing this module registers all generators with the GeneratorRegistry.
"""

from synthetic.generators.data_assets import DataAssetGenerator
from synthetic.generators.departments import DepartmentGenerator
from synthetic.generators.enterprise import (
    CapabilityGenerator,
    ContractGenerator,
    ControlGenerator,
    CustomerGenerator,
    DataDomainGenerator,
    DataFlowGenerator,
    GeographyGenerator,
    InitiativeGenerator,
    IntegrationGenerator,
    JurisdictionGenerator,
    MarketSegmentGenerator,
    OrgUnitGenerator,
    ProductGenerator,
    ProductPortfolioGenerator,
    RegulationGenerator,
    RiskGenerator,
    SiteGenerator,
    ThreatGenerator,
)
from synthetic.generators.incidents import IncidentGenerator
from synthetic.generators.locations import LocationGenerator
from synthetic.generators.networks import NetworkGenerator
from synthetic.generators.people import PeopleGenerator
from synthetic.generators.policies import PolicyGenerator
from synthetic.generators.roles import RoleGenerator
from synthetic.generators.security import ThreatActorGenerator, VulnerabilityGenerator
from synthetic.generators.systems import SystemGenerator
from synthetic.generators.vendors import VendorGenerator

__all__ = [
    # v0.1 generators
    "DataAssetGenerator",
    "DepartmentGenerator",
    "IncidentGenerator",
    "LocationGenerator",
    "NetworkGenerator",
    "PeopleGenerator",
    "PolicyGenerator",
    "RoleGenerator",
    "SystemGenerator",
    "ThreatActorGenerator",
    "VendorGenerator",
    "VulnerabilityGenerator",
    # Enterprise generators (L01-L11)
    "CapabilityGenerator",
    "ContractGenerator",
    "ControlGenerator",
    "CustomerGenerator",
    "DataDomainGenerator",
    "DataFlowGenerator",
    "GeographyGenerator",
    "InitiativeGenerator",
    "IntegrationGenerator",
    "JurisdictionGenerator",
    "MarketSegmentGenerator",
    "OrgUnitGenerator",
    "ProductGenerator",
    "ProductPortfolioGenerator",
    "RegulationGenerator",
    "RiskGenerator",
    "SiteGenerator",
    "ThreatGenerator",
]
