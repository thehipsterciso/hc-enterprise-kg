"""Synthetic data generators for all entity types.

Importing this module registers all generators with the GeneratorRegistry.
"""

from hc_enterprise_kg.synthetic.generators.data_assets import DataAssetGenerator
from hc_enterprise_kg.synthetic.generators.departments import DepartmentGenerator
from hc_enterprise_kg.synthetic.generators.incidents import IncidentGenerator
from hc_enterprise_kg.synthetic.generators.locations import LocationGenerator
from hc_enterprise_kg.synthetic.generators.networks import NetworkGenerator
from hc_enterprise_kg.synthetic.generators.people import PeopleGenerator
from hc_enterprise_kg.synthetic.generators.policies import PolicyGenerator
from hc_enterprise_kg.synthetic.generators.roles import RoleGenerator
from hc_enterprise_kg.synthetic.generators.security import ThreatActorGenerator, VulnerabilityGenerator
from hc_enterprise_kg.synthetic.generators.systems import SystemGenerator
from hc_enterprise_kg.synthetic.generators.vendors import VendorGenerator

__all__ = [
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
]
