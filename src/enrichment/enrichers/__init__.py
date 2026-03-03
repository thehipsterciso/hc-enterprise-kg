"""Entity enrichers — one per entity type, no exceptions.

Importing this package auto-discovers and registers all enrichers
with the EnricherRegistry, similar to how synthetic/generators works.
"""

from __future__ import annotations

# ── Business & Commercial ──
from enrichment.enrichers.business_capability_enricher import BusinessCapabilityEnricher
from enrichment.enrichers.coherence_enricher import CoherenceEnricher
from enrichment.enrichers.contract_enricher import ContractEnricher
from enrichment.enrichers.control_enricher import ControlEnricher
from enrichment.enrichers.customer_enricher import CustomerEnricher

# ── Data ──
from enrichment.enrichers.data_asset_enricher import DataAssetEnricher
from enrichment.enrichers.data_domain_enricher import DataDomainEnricher
from enrichment.enrichers.data_flow_enricher import DataFlowEnricher
from enrichment.enrichers.geography_enricher import GeographyEnricher
from enrichment.enrichers.incident_enricher import IncidentEnricher
from enrichment.enrichers.initiative_enricher import InitiativeEnricher
from enrichment.enrichers.integration_enricher import IntegrationEnricher
from enrichment.enrichers.jurisdiction_enricher import JurisdictionEnricher

# ── Geography & Locations ──
from enrichment.enrichers.location_enricher import LocationEnricher
from enrichment.enrichers.market_segment_enricher import MarketSegmentEnricher
from enrichment.enrichers.network_enricher import NetworkEnricher
from enrichment.enrichers.organizational_unit_enricher import OrganizationalUnitEnricher

# Import all enricher modules to trigger @EnricherRegistry.register decorators.
# Each module registers its enricher class on import.
# ── People & Organization ──
from enrichment.enrichers.person_enricher import PersonEnricher
from enrichment.enrichers.policy_enricher import PolicyEnricher
from enrichment.enrichers.product_enricher import ProductEnricher
from enrichment.enrichers.product_portfolio_enricher import ProductPortfolioEnricher
from enrichment.enrichers.regulation_enricher import RegulationEnricher

# ── Cross-Cutting ──
from enrichment.enrichers.relationship_enricher import RelationshipEnricher

# ── Risk & Compliance ──
from enrichment.enrichers.risk_enricher import RiskEnricher
from enrichment.enrichers.role_enricher import RoleEnricher
from enrichment.enrichers.site_enricher import SiteEnricher

# ── Technology & Systems ──
from enrichment.enrichers.system_enricher import SystemEnricher
from enrichment.enrichers.threat_actor_enricher import ThreatActorEnricher
from enrichment.enrichers.threat_enricher import ThreatEnricher

# ── Vendor ──
from enrichment.enrichers.vendor_enricher import VendorEnricher
from enrichment.enrichers.vulnerability_enricher import VulnerabilityEnricher

__all__ = [
    # People & Organization
    "PersonEnricher",
    "RoleEnricher",
    "OrganizationalUnitEnricher",
    # Technology & Systems
    "SystemEnricher",
    "NetworkEnricher",
    "IntegrationEnricher",
    # Data
    "DataAssetEnricher",
    "DataDomainEnricher",
    "DataFlowEnricher",
    # Risk & Compliance
    "RiskEnricher",
    "ThreatEnricher",
    "VulnerabilityEnricher",
    "ThreatActorEnricher",
    "IncidentEnricher",
    "ControlEnricher",
    "PolicyEnricher",
    "RegulationEnricher",
    # Geography & Locations
    "LocationEnricher",
    "SiteEnricher",
    "GeographyEnricher",
    "JurisdictionEnricher",
    # Business & Commercial
    "BusinessCapabilityEnricher",
    "ProductPortfolioEnricher",
    "ProductEnricher",
    "MarketSegmentEnricher",
    "CustomerEnricher",
    "ContractEnricher",
    "InitiativeEnricher",
    # Vendor
    "VendorEnricher",
    # Cross-Cutting
    "RelationshipEnricher",
    "CoherenceEnricher",
]
