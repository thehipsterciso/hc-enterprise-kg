"""Generators for enterprise ontology entity types (L01-L11).

Each generator follows the same pattern as the v0.1 generators: extends
AbstractGenerator, declares GENERATES, and is registered via decorator.
Entities are created with realistic enterprise attributes populated.
"""

from __future__ import annotations

import random

from domain.base import EntityType
from domain.entities.business_capability import BusinessCapability
from domain.entities.contract import Contract
from domain.entities.control import Control
from domain.entities.customer import Customer
from domain.entities.data_domain import DataDomain
from domain.entities.data_flow import DataFlow
from domain.entities.geography import Geography
from domain.entities.initiative import (
    ActiveRisk,
    BudgetBreakdown,
    BusinessCaseSummary,
    FundingSource,
    ImpactsSystem,
    Initiative,
    InitiativeRiskProfile,
    KeyMilestone,
    ResourceRequirements,
    SuccessCriterion,
    TotalBudget,
)
from domain.entities.integration import Integration
from domain.entities.jurisdiction import Jurisdiction
from domain.entities.market_segment import MarketSegment
from domain.entities.organizational_unit import OrganizationalUnit
from domain.entities.product import Product
from domain.entities.product_portfolio import ProductPortfolio
from domain.entities.regulation import Regulation
from domain.entities.risk import Risk
from domain.entities.site import CurrentOccupancy, Site, SiteAddress
from domain.entities.threat import Threat
from domain.shared import ProvenanceAndConfidence, TemporalAndVersioning
from synthetic.base import AbstractGenerator, GenerationContext, GeneratorRegistry

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

REGULATION_NAMES = [
    ("GDPR", "General Data Protection Regulation", "EU", "Data Privacy"),
    ("CCPA", "California Consumer Privacy Act", "US-CA", "Data Privacy"),
    ("HIPAA", "Health Insurance Portability and Accountability Act", "US", "Healthcare"),
    ("SOX", "Sarbanes-Oxley Act", "US", "Financial Reporting"),
    ("PCI-DSS", "Payment Card Industry Data Security Standard", "Global", "Payment Security"),
    ("DORA", "Digital Operational Resilience Act", "EU", "Financial Services"),
    ("NIS2", "Network and Information Security Directive 2", "EU", "Cybersecurity"),
    ("SOC2", "Service Organization Control Type 2", "US", "Trust Services"),
    ("ISO27001", "Information Security Management System", "Global", "Information Security"),
    ("GLBA", "Gramm-Leach-Bliley Act", "US", "Financial Privacy"),
    ("FERPA", "Family Educational Rights and Privacy Act", "US", "Education"),
    ("NIST-CSF", "NIST Cybersecurity Framework", "US", "Cybersecurity"),
    ("Basel III", "Basel III Capital Adequacy", "Global", "Banking"),
    ("MiFID II", "Markets in Financial Instruments Directive II", "EU", "Financial Markets"),
    ("FISMA", "Federal Information Security Modernization Act", "US", "Government IT"),
]

CONTROL_FRAMEWORKS = ["NIST 800-53", "ISO 27001", "CIS Controls", "COBIT", "SOC2 TSC"]
CONTROL_TYPES = ["Preventive", "Detective", "Corrective", "Compensating"]
CONTROL_DOMAINS = [
    "Access Control",
    "Asset Management",
    "Audit & Accountability",
    "Configuration Management",
    "Incident Response",
    "Media Protection",
    "Physical Security",
    "Risk Assessment",
    "System & Communications Protection",
    "Vulnerability Management",
    "Change Management",
    "Data Protection",
]

RISK_CATEGORIES = [
    "Operational",
    "Cybersecurity",
    "Compliance",
    "Financial",
    "Strategic",
    "Reputational",
    "Third-Party",
    "Technology",
]
RISK_LEVELS = ["Critical", "High", "Medium", "Low"]

THREAT_CATEGORIES = [
    "Cyber",
    "Physical",
    "Insider",
    "Supply Chain",
    "Natural Disaster",
    "Geopolitical",
    "Regulatory Change",
]
THREAT_LIKELIHOOD = ["Very High", "High", "Medium", "Low", "Very Low"]

INTEGRATION_TYPES = [
    "API",
    "ETL",
    "File Transfer",
    "Message Queue",
    "Database Link",
    "Webhook",
    "CDC",
    "ESB",
]
INTEGRATION_PROTOCOLS = ["REST", "SOAP", "gRPC", "SFTP", "Kafka", "AMQP", "JDBC"]

DATA_DOMAIN_NAMES = [
    "Customer Data",
    "Financial Data",
    "Employee Data",
    "Product Data",
    "Operational Data",
    "Marketing Data",
    "Compliance Data",
    "Clinical Data",
    "Trading Data",
    "Risk Data",
    "Supply Chain Data",
    "Research Data",
]

CAPABILITY_NAMES = [
    "Customer Relationship Management",
    "Financial Planning & Analysis",
    "Human Capital Management",
    "Product Development",
    "Supply Chain Management",
    "Risk Management",
    "Compliance Management",
    "IT Service Management",
    "Data Analytics",
    "Digital Marketing",
    "Order Management",
    "Procurement",
    "Quality Assurance",
    "Strategic Planning",
    "Cybersecurity Operations",
    "Business Intelligence",
    "Enterprise Architecture",
    "Innovation Management",
]

SITE_TYPES = [
    "Headquarters",
    "Regional Office",
    "Data Center",
    "Branch Office",
    "Operations Center",
    "R&D Facility",
]

PRODUCT_NAMES = [
    "Enterprise Platform",
    "Analytics Suite",
    "Mobile App",
    "Customer Portal",
    "Risk Dashboard",
    "Compliance Manager",
    "Trading Platform",
    "Claims Processor",
    "EHR System",
    "Payment Gateway",
    "API Marketplace",
    "Data Lake Platform",
    "Security Operations Center",
    "Cloud Infrastructure",
    "Identity Management",
    "Document Management",
]

INITIATIVE_TYPES = [
    "Digital Transformation",
    "Technology Migration / Modernization",
    "Process Improvement",
    "Regulatory Compliance",
    "Security Remediation",
    "AI / ML Initiative",
    "Cost Optimization",
    "Customer Experience",
    "Data Governance",
    "Infrastructure",
]

INITIATIVE_STATUSES = [
    "Proposed",
    "Approved",
    "Planning",
    "In Progress",
    "On Hold",
    "At Risk",
    "Completed",
]


# ---------------------------------------------------------------------------
# L01: Compliance & Governance
# ---------------------------------------------------------------------------


@GeneratorRegistry.register
class RegulationGenerator(AbstractGenerator):
    """Generates Regulation entities with compliance attributes."""

    GENERATES = EntityType.REGULATION

    def generate(self, count: int, context: GenerationContext) -> list[Regulation]:
        faker = context.faker
        regs: list[Regulation] = []
        selected = random.sample(REGULATION_NAMES, k=min(count, len(REGULATION_NAMES)))
        for i in range(count):
            if i < len(selected):
                short, full, jur, domain = selected[i]
            else:
                short = f"REG-{faker.bothify('??###').upper()}"
                full = f"{faker.bs().title()} Regulation"
                jur = random.choice(["US", "EU", "Global", "UK", "APAC"])
                domain = random.choice(
                    ["Data Privacy", "Financial", "Cybersecurity", "Operational"]
                )

            reg = Regulation(
                name=full,
                description=f"{short} — {domain} regulation in {jur}",
                regulation_id=f"REG-{i + 1:05d}",
                short_name=short,
                regulation_category=domain,
                applicability_status="Applicable",
                effective_date=str(faker.date_between(start_date="-5y", end_date="today")),
                temporal=TemporalAndVersioning(schema_version="1.0.0"),
                provenance=ProvenanceAndConfidence(
                    primary_data_source="Compliance Team",
                    confidence_level=random.choice(["Verified", "High"]),
                ),
                tags=[domain.lower().replace(" ", "-"), jur.lower()],
            )
            regs.append(reg)

        context.store(EntityType.REGULATION, regs)
        return regs


@GeneratorRegistry.register
class ControlGenerator(AbstractGenerator):
    """Generates Control entities with testing and effectiveness attributes."""

    GENERATES = EntityType.CONTROL

    def generate(self, count: int, context: GenerationContext) -> list[Control]:
        faker = context.faker
        controls: list[Control] = []
        for i in range(count):
            framework = random.choice(CONTROL_FRAMEWORKS)
            domain = random.choice(CONTROL_DOMAINS)
            control = Control(
                name=f"{domain} — {framework} Control",
                description=f"{random.choice(CONTROL_TYPES)} control for {domain.lower()}",
                control_id=f"CTL-{i + 1:05d}",
                control_type=random.choice(CONTROL_TYPES),
                control_domain=domain,
                control_framework=framework,
                control_objective=f"Ensure {domain.lower()} requirements are met",
                implementation_status=random.choice(
                    ["Implemented", "Partially Implemented", "Planned"]
                ),
                automation_level=random.choice(["Fully Automated", "Semi-Automated", "Manual"]),
                control_owner=faker.name(),
                temporal=TemporalAndVersioning(schema_version="1.0.0"),
                provenance=ProvenanceAndConfidence(
                    primary_data_source="GRC Platform",
                    confidence_level="High",
                ),
                tags=[framework.lower().replace(" ", "-"), domain.lower().replace(" ", "-")],
            )
            controls.append(control)

        context.store(EntityType.CONTROL, controls)
        return controls


@GeneratorRegistry.register
class RiskGenerator(AbstractGenerator):
    """Generates Risk entities with impact and likelihood assessment."""

    GENERATES = EntityType.RISK

    def generate(self, count: int, context: GenerationContext) -> list[Risk]:
        faker = context.faker
        risks: list[Risk] = []
        for i in range(count):
            category = random.choice(RISK_CATEGORIES)
            risk = Risk(
                name=f"{category} Risk — {faker.bs().title()}",
                description=f"Risk in {category.lower()} domain",
                risk_id=f"RSK-{i + 1:05d}",
                risk_category=category,
                inherent_likelihood=random.choice(THREAT_LIKELIHOOD),
                inherent_impact=random.choice(RISK_LEVELS),
                inherent_risk_level=random.choice(RISK_LEVELS),
                residual_likelihood=random.choice(THREAT_LIKELIHOOD),
                residual_impact=random.choice(RISK_LEVELS),
                residual_risk_level=random.choice(RISK_LEVELS),
                risk_owner=faker.name(),
                risk_status=random.choice(["Open", "Mitigated", "Accepted", "Transferred"]),
                risk_response_strategy=random.choice(["Mitigate", "Accept", "Transfer", "Avoid"]),
                last_assessment_date=str(faker.date_between(start_date="-6m", end_date="today")),
                temporal=TemporalAndVersioning(schema_version="1.0.0"),
                provenance=ProvenanceAndConfidence(
                    primary_data_source="ERM Platform",
                    confidence_level=random.choice(["Verified", "High", "Medium"]),
                ),
                tags=[category.lower().replace(" ", "-")],
            )
            risks.append(risk)

        context.store(EntityType.RISK, risks)
        return risks


@GeneratorRegistry.register
class ThreatGenerator(AbstractGenerator):
    """Generates Threat entities (distinct from ThreatActor)."""

    GENERATES = EntityType.THREAT

    def generate(self, count: int, context: GenerationContext) -> list[Threat]:
        faker = context.faker
        threats: list[Threat] = []
        for i in range(count):
            category = random.choice(THREAT_CATEGORIES)
            threat = Threat(
                name=f"{category} Threat — {faker.bs().title()}",
                description=f"Threat in {category.lower()} domain",
                threat_id=f"THR-{i + 1:05d}",
                threat_category=category,
                threat_type=random.choice(
                    ["Targeted", "Opportunistic", "Environmental", "Systemic"]
                ),
                likelihood=random.choice(THREAT_LIKELIHOOD),
                impact_if_realized=random.choice(RISK_LEVELS),
                threat_level=random.choice(RISK_LEVELS),
                threat_source=random.choice(["External", "Internal", "Environmental", "Partner"]),
                threat_status=random.choice(["Active", "Emerging", "Historical", "Mitigated"]),
                temporal=TemporalAndVersioning(schema_version="1.0.0"),
                provenance=ProvenanceAndConfidence(
                    primary_data_source="Threat Intelligence",
                    confidence_level=random.choice(["High", "Medium"]),
                ),
                tags=[category.lower().replace(" ", "-")],
            )
            threats.append(threat)

        context.store(EntityType.THREAT, threats)
        return threats


# ---------------------------------------------------------------------------
# L02: Technology & Systems
# ---------------------------------------------------------------------------


@GeneratorRegistry.register
class IntegrationGenerator(AbstractGenerator):
    """Generates Integration entities between systems."""

    GENERATES = EntityType.INTEGRATION

    def generate(self, count: int, context: GenerationContext) -> list[Integration]:
        integrations: list[Integration] = []

        for i in range(count):
            int_type = random.choice(INTEGRATION_TYPES)
            protocol = random.choice(INTEGRATION_PROTOCOLS)

            integration = Integration(
                name=f"{int_type} Integration — {protocol}",
                description=f"{int_type} integration using {protocol}",
                integration_id=f"INT-{i + 1:05d}",
                integration_type=int_type,
                protocol=protocol,
                data_format=random.choice(["JSON", "XML", "CSV", "Avro", "Parquet", "Binary"]),
                frequency=random.choice(
                    ["Real-time", "Near Real-time", "Hourly", "Daily", "Weekly"]
                ),
                direction=random.choice(["Unidirectional", "Bidirectional"]),
                status=random.choice(["Active", "Inactive", "Deprecated", "Under Development"]),
                criticality=random.choice(["Critical", "High", "Medium", "Low"]),
                temporal=TemporalAndVersioning(schema_version="1.0.0"),
                provenance=ProvenanceAndConfidence(
                    primary_data_source="Integration Platform",
                    confidence_level="High",
                ),
                tags=[int_type.lower().replace(" ", "-")],
            )
            integrations.append(integration)

        context.store(EntityType.INTEGRATION, integrations)
        return integrations


# ---------------------------------------------------------------------------
# L03: Data Assets
# ---------------------------------------------------------------------------


@GeneratorRegistry.register
class DataDomainGenerator(AbstractGenerator):
    """Generates DataDomain entities."""

    GENERATES = EntityType.DATA_DOMAIN

    def generate(self, count: int, context: GenerationContext) -> list[DataDomain]:
        faker = context.faker
        domains: list[DataDomain] = []
        selected = random.sample(DATA_DOMAIN_NAMES, k=min(count, len(DATA_DOMAIN_NAMES)))

        for i in range(count):
            name = selected[i] if i < len(selected) else f"{faker.word().title()} Data Domain"
            domain = DataDomain(
                name=name,
                description=f"Enterprise data domain: {name}",
                domain_id=f"DD-{i + 1:05d}",
                domain_owner=faker.name(),
                data_steward=faker.name(),
                classification_level=random.choice(
                    ["Public", "Internal", "Confidential", "Restricted"]
                ),
                governance_status=random.choice(["Governed", "Partially Governed", "Ungoverned"]),
                temporal=TemporalAndVersioning(schema_version="1.0.0"),
                provenance=ProvenanceAndConfidence(
                    primary_data_source="Data Governance Platform",
                    confidence_level="High",
                ),
                tags=["data-domain"],
            )
            domains.append(domain)

        context.store(EntityType.DATA_DOMAIN, domains)
        return domains


@GeneratorRegistry.register
class DataFlowGenerator(AbstractGenerator):
    """Generates DataFlow entities between systems/domains."""

    GENERATES = EntityType.DATA_FLOW

    def generate(self, count: int, context: GenerationContext) -> list[DataFlow]:
        systems = context.get_entities(EntityType.SYSTEM)
        flows: list[DataFlow] = []

        for i in range(count):
            src = random.choice(systems).name if systems else "External Source"
            tgt = random.choice(systems).name if systems else "External Target"
            flow = DataFlow(
                name=f"Flow: {src} → {tgt}",
                description=f"Data flow from {src} to {tgt}",
                flow_id=f"DF-{i + 1:05d}",
                data_classification=random.choice(
                    ["Public", "Internal", "Confidential", "Restricted"]
                ),
                transfer_method=random.choice(
                    ["API", "ETL", "File Transfer", "Streaming", "Replication"]
                ),
                frequency=random.choice(["Real-time", "Hourly", "Daily", "Weekly", "On Demand"]),
                encryption_in_transit=random.choice([True, False]),
                status=random.choice(["Active", "Inactive", "Under Review"]),
                temporal=TemporalAndVersioning(schema_version="1.0.0"),
                provenance=ProvenanceAndConfidence(
                    primary_data_source="Data Lineage Tool",
                    confidence_level=random.choice(["High", "Medium"]),
                ),
                tags=["data-flow"],
            )
            flows.append(flow)

        context.store(EntityType.DATA_FLOW, flows)
        return flows


# ---------------------------------------------------------------------------
# L04: Organization
# ---------------------------------------------------------------------------


OU_TYPES = [
    "Business Unit",
    "Division",
    "Department",
    "Team",
    "Shared Service Center",
    "Center of Excellence",
]


@GeneratorRegistry.register
class OrgUnitGenerator(AbstractGenerator):
    """Generates OrganizationalUnit entities."""

    GENERATES = EntityType.ORGANIZATIONAL_UNIT

    def generate(self, count: int, context: GenerationContext) -> list[OrganizationalUnit]:
        faker = context.faker
        units: list[OrganizationalUnit] = []

        for i in range(count):
            unit_type = random.choice(OU_TYPES)
            unit = OrganizationalUnit(
                name=f"{faker.company_suffix()} {unit_type}",
                description=f"{unit_type} organizational unit",
                unit_id=f"OU-{i + 1:05d}",
                unit_type=unit_type,
                operational_status=random.choice(
                    ["Active", "Planned", "Under Restructuring", "Dissolved"]
                ),
                geographic_scope=random.choice(["Global", "Regional", "National", "Local"]),
                functional_domain_primary=random.choice(
                    [
                        "Technology",
                        "Finance",
                        "Operations",
                        "Sales",
                        "Marketing",
                        "HR",
                        "Legal",
                        "Compliance",
                    ]
                ),
                unit_leader=faker.name(),
                unit_leader_title=random.choice(
                    ["VP", "SVP", "Director", "Managing Director", "Head"]
                ),
                business_criticality=random.choice(["Critical", "High", "Medium", "Low"]),
                temporal=TemporalAndVersioning(schema_version="1.0.0"),
                provenance=ProvenanceAndConfidence(
                    primary_data_source="HR System",
                    confidence_level="High",
                ),
                tags=[unit_type.lower().replace(" ", "-")],
            )
            units.append(unit)

        context.store(EntityType.ORGANIZATIONAL_UNIT, units)
        return units


# ---------------------------------------------------------------------------
# L06: Business Capabilities
# ---------------------------------------------------------------------------


@GeneratorRegistry.register
class CapabilityGenerator(AbstractGenerator):
    """Generates BusinessCapability entities."""

    GENERATES = EntityType.BUSINESS_CAPABILITY

    def generate(self, count: int, context: GenerationContext) -> list[BusinessCapability]:
        faker = context.faker
        caps: list[BusinessCapability] = []
        selected = random.sample(CAPABILITY_NAMES, k=min(count, len(CAPABILITY_NAMES)))

        for i in range(count):
            name = selected[i] if i < len(selected) else f"{faker.bs().title()} Capability"
            cap = BusinessCapability(
                name=name,
                description=f"Enterprise capability: {name}",
                capability_id=f"BC-{i + 1:05d}",
                capability_level=random.choice(
                    ["L0 — Enterprise", "L1 — Domain", "L2 — Sub-domain", "L3 — Function"]
                ),
                maturity_level=random.choice(
                    ["Initial", "Developing", "Defined", "Managed", "Optimized"]
                ),
                strategic_importance=random.choice(["Differentiating", "Essential", "Commodity"]),
                business_criticality=random.choice(["Critical", "High", "Medium", "Low"]),
                investment_priority=random.choice(["Invest", "Maintain", "Divest", "Tolerate"]),
                functional_domain=random.choice(
                    [
                        "Sales & Marketing",
                        "Finance",
                        "Operations",
                        "Technology",
                        "HR",
                        "Risk & Compliance",
                        "Customer Service",
                    ]
                ),
                temporal=TemporalAndVersioning(schema_version="1.0.0"),
                provenance=ProvenanceAndConfidence(
                    primary_data_source="Enterprise Architecture",
                    confidence_level="High",
                ),
                tags=["capability"],
            )
            caps.append(cap)

        context.store(EntityType.BUSINESS_CAPABILITY, caps)
        return caps


# ---------------------------------------------------------------------------
# L07: Locations & Facilities
# ---------------------------------------------------------------------------


@GeneratorRegistry.register
class SiteGenerator(AbstractGenerator):
    """Generates Site entities with facility attributes."""

    GENERATES = EntityType.SITE

    def generate(self, count: int, context: GenerationContext) -> list[Site]:
        faker = context.faker
        sites: list[Site] = []
        for i in range(count):
            site_type = random.choice(SITE_TYPES)
            city = faker.city()
            site = Site(
                name=f"{city} {site_type}",
                description=f"{site_type} facility",
                site_id=f"SITE-{i + 1:05d}",
                site_type=site_type,
                site_status=random.choice(
                    ["Active", "Under Construction", "Planned", "Decommissioned"]
                ),
                ownership_type=random.choice(["Owned", "Leased", "Co-located", "Shared"]),
                address=SiteAddress(
                    street_line_1=faker.street_address(),
                    city=city,
                    state_province=faker.state_abbr(),
                    postal_code=faker.zipcode(),
                    country_code=faker.country_code(),
                ),
                current_occupancy=CurrentOccupancy(
                    headcount=random.randint(20, 4000),
                ),
                physical_security_tier=random.choice(["Standard", "Enhanced", "Restricted"]),
                business_continuity_tier=random.choice(["Tier 1", "Tier 2", "Tier 3", "Tier 4"]),
                temporal=TemporalAndVersioning(schema_version="1.0.0"),
                provenance=ProvenanceAndConfidence(
                    primary_data_source="Facilities Management",
                    confidence_level="High",
                ),
                tags=[site_type.lower().replace(" ", "-")],
            )
            sites.append(site)

        context.store(EntityType.SITE, sites)
        return sites


@GeneratorRegistry.register
class GeographyGenerator(AbstractGenerator):
    """Generates Geography entities."""

    GENERATES = EntityType.GEOGRAPHY

    def generate(self, count: int, context: GenerationContext) -> list[Geography]:
        faker = context.faker
        geos: list[Geography] = []
        regions = [
            ("North America", "Region"),
            ("EMEA", "Region"),
            ("APAC", "Region"),
            ("Latin America", "Region"),
            ("United States", "Country"),
            ("United Kingdom", "Country"),
            ("Germany", "Country"),
            ("Japan", "Country"),
            ("Australia", "Country"),
            ("India", "Country"),
        ]
        for i in range(count):
            if i < len(regions):
                name, geo_type = regions[i]
            else:
                name = faker.country()
                geo_type = "Country"
            geo = Geography(
                name=name,
                description=f"{geo_type}: {name}",
                geography_id=f"GEO-{i + 1:05d}",
                geography_type=geo_type,
                schema_version="1.0.0",
                confidence_level="Verified",
                tags=[geo_type.lower()],
            )
            geos.append(geo)

        context.store(EntityType.GEOGRAPHY, geos)
        return geos


@GeneratorRegistry.register
class JurisdictionGenerator(AbstractGenerator):
    """Generates Jurisdiction entities."""

    GENERATES = EntityType.JURISDICTION

    def generate(self, count: int, context: GenerationContext) -> list[Jurisdiction]:
        faker = context.faker
        jurisdictions: list[Jurisdiction] = []
        jur_templates = [
            ("US Federal", "Federal", "US"),
            ("EU General", "Supranational", "EU"),
            ("UK", "National", "GB"),
            ("California", "State/Province", "US-CA"),
            ("New York", "State/Province", "US-NY"),
            ("Germany", "National", "DE"),
            ("Singapore", "National", "SG"),
            ("Australia", "National", "AU"),
        ]
        for i in range(count):
            if i < len(jur_templates):
                name, jur_type, code = jur_templates[i]
            else:
                name = faker.country()
                jur_type = "National"
                code = faker.country_code()
            jur = Jurisdiction(
                name=f"{name} Jurisdiction",
                description=f"{jur_type} jurisdiction: {name}",
                jurisdiction_id=f"JUR-{i + 1:05d}",
                jurisdiction_type=jur_type,
                jurisdiction_code=code,
                schema_version="1.0.0",
                confidence_level="Verified",
                tags=[jur_type.lower().replace("/", "-")],
            )
            jurisdictions.append(jur)

        context.store(EntityType.JURISDICTION, jurisdictions)
        return jurisdictions


# ---------------------------------------------------------------------------
# L08: Products & Services
# ---------------------------------------------------------------------------


@GeneratorRegistry.register
class ProductPortfolioGenerator(AbstractGenerator):
    """Generates ProductPortfolio entities."""

    GENERATES = EntityType.PRODUCT_PORTFOLIO

    def generate(self, count: int, context: GenerationContext) -> list[ProductPortfolio]:
        faker = context.faker
        portfolios: list[ProductPortfolio] = []
        portfolio_names = [
            "Enterprise Solutions",
            "Consumer Products",
            "Digital Services",
            "Platform Services",
            "Professional Services",
            "Data Products",
        ]
        for i in range(count):
            name = (
                portfolio_names[i]
                if i < len(portfolio_names)
                else f"{faker.bs().title()} Portfolio"
            )
            portfolio = ProductPortfolio(
                name=name,
                description=f"Product portfolio: {name}",
                portfolio_id=f"PF-{i + 1:05d}",
                portfolio_type=random.choice(["Product", "Service", "Platform", "Hybrid"]),
                lifecycle_stage=random.choice(["Growth", "Mature", "Harvest", "Emerging"]),
                strategic_role=random.choice(["Core", "Adjacent", "Transformational"]),
                portfolio_owner=faker.name(),
                product_count=random.randint(2, 20),
                temporal_and_versioning=TemporalAndVersioning(schema_version="1.0.0"),
                provenance_and_confidence=ProvenanceAndConfidence(
                    primary_data_source="Product Management",
                    confidence_level="High",
                ),
                tags=["portfolio"],
            )
            portfolios.append(portfolio)

        context.store(EntityType.PRODUCT_PORTFOLIO, portfolios)
        return portfolios


@GeneratorRegistry.register
class ProductGenerator(AbstractGenerator):
    """Generates Product entities with enterprise attributes."""

    GENERATES = EntityType.PRODUCT

    def generate(self, count: int, context: GenerationContext) -> list[Product]:
        faker = context.faker
        products: list[Product] = []
        selected = random.sample(PRODUCT_NAMES, k=min(count, len(PRODUCT_NAMES)))

        for i in range(count):
            name = selected[i] if i < len(selected) else f"{faker.word().title()} Product"
            product = Product(
                name=name,
                description=f"Enterprise product: {name}",
                product_id=f"PRD-{i + 1:05d}",
                product_type=random.choice(["Software", "Service", "Platform", "Hardware", "SaaS"]),
                lifecycle_stage=random.choice(
                    ["Development", "Launch", "Growth", "Mature", "Decline", "Retired"]
                ),
                product_owner=faker.name(),
                product_manager=faker.name(),
                business_criticality=random.choice(["Critical", "High", "Medium", "Low"]),
                temporal_and_versioning=TemporalAndVersioning(schema_version="1.0.0"),
                provenance_and_confidence=ProvenanceAndConfidence(
                    primary_data_source="Product Management",
                    confidence_level="High",
                ),
                tags=["product"],
            )
            products.append(product)

        context.store(EntityType.PRODUCT, products)
        return products


# ---------------------------------------------------------------------------
# L09: Customers & Markets
# ---------------------------------------------------------------------------


@GeneratorRegistry.register
class MarketSegmentGenerator(AbstractGenerator):
    """Generates MarketSegment entities."""

    GENERATES = EntityType.MARKET_SEGMENT

    def generate(self, count: int, context: GenerationContext) -> list[MarketSegment]:
        faker = context.faker
        segments: list[MarketSegment] = []
        segment_names = [
            "Enterprise",
            "Mid-Market",
            "SMB",
            "Government",
            "Healthcare",
            "Financial Services",
            "Technology",
            "Education",
        ]
        for i in range(count):
            name = segment_names[i] if i < len(segment_names) else f"{faker.bs().title()} Segment"
            segment = MarketSegment(
                name=name,
                description=f"Market segment: {name}",
                segment_id=f"SEG-{i + 1:05d}",
                segment_type=random.choice(
                    ["Industry Vertical", "Company Size", "Geography", "Use Case"]
                ),
                segment_owner=faker.name(),
                strategic_priority=random.choice(["Primary", "Secondary", "Emerging", "Declining"]),
                temporal_and_versioning=TemporalAndVersioning(schema_version="1.0.0"),
                provenance_and_confidence=ProvenanceAndConfidence(
                    primary_data_source="Strategy Team",
                    confidence_level="High",
                ),
                tags=["market-segment"],
            )
            segments.append(segment)

        context.store(EntityType.MARKET_SEGMENT, segments)
        return segments


@GeneratorRegistry.register
class CustomerGenerator(AbstractGenerator):
    """Generates Customer entities with enterprise attributes."""

    GENERATES = EntityType.CUSTOMER

    def generate(self, count: int, context: GenerationContext) -> list[Customer]:
        faker = context.faker
        customers: list[Customer] = []
        for i in range(count):
            customer = Customer(
                name=faker.company(),
                description="Enterprise customer",
                customer_id=f"CUST-{i + 1:05d}",
                customer_type=random.choice(
                    ["Enterprise", "Mid-Market", "SMB", "Government", "Non-Profit"]
                ),
                relationship_status=random.choice(["Active", "Prospect", "Churned", "Dormant"]),
                account_tier=random.choice(["Strategic", "Key", "Standard", "Growth"]),
                industry=random.choice(
                    ["Technology", "Healthcare", "Financial Services", "Manufacturing", "Retail"]
                ),
                account_manager=faker.name(),
                relationship_start_date=str(
                    faker.date_between(start_date="-10y", end_date="today")
                ),
                temporal_and_versioning=TemporalAndVersioning(schema_version="1.0.0"),
                provenance_and_confidence=ProvenanceAndConfidence(
                    primary_data_source="CRM System",
                    confidence_level="High",
                ),
                tags=["customer"],
            )
            customers.append(customer)

        context.store(EntityType.CUSTOMER, customers)
        return customers


# ---------------------------------------------------------------------------
# L10: Vendors & Partners (Contract — Vendor already has a v0.1 generator)
# ---------------------------------------------------------------------------


@GeneratorRegistry.register
class ContractGenerator(AbstractGenerator):
    """Generates Contract entities linked to vendors."""

    GENERATES = EntityType.CONTRACT

    def generate(self, count: int, context: GenerationContext) -> list[Contract]:
        faker = context.faker
        vendors = context.get_entities(EntityType.VENDOR)
        contracts: list[Contract] = []
        for i in range(count):
            vendor = random.choice(vendors) if vendors else None
            contract = Contract(
                name=f"Contract — {vendor.name if vendor else faker.company()}",
                description="Master agreement",
                contract_id=f"CTR-{i + 1:05d}",
                contract_type=random.choice(
                    [
                        "Master Services Agreement",
                        "Statement of Work",
                        "License Agreement",
                        "Support Agreement",
                        "NDA",
                        "Data Processing Agreement",
                    ]
                ),
                contract_status=random.choice(
                    ["Active", "Expired", "Under Negotiation", "Terminated"]
                ),
                vendor_id=vendor.id if vendor else "",
                vendor_name=vendor.name if vendor else "",
                total_value=round(random.uniform(50_000, 10_000_000), 2),
                currency="USD",
                start_date=str(faker.date_between(start_date="-3y", end_date="today")),
                end_date=str(faker.date_between(start_date="today", end_date="+3y")),
                auto_renewal=random.choice([True, False]),
                payment_terms=random.choice(["Net 30", "Net 45", "Net 60", "Net 90"]),
                temporal_and_versioning=TemporalAndVersioning(schema_version="1.0.0"),
                provenance_and_confidence=ProvenanceAndConfidence(
                    primary_data_source="Contract Management System",
                    confidence_level="Verified",
                ),
                tags=["contract"],
            )
            contracts.append(contract)

        context.store(EntityType.CONTRACT, contracts)
        return contracts


# ---------------------------------------------------------------------------
# L11: Strategic Initiatives
# ---------------------------------------------------------------------------


@GeneratorRegistry.register
class InitiativeGenerator(AbstractGenerator):
    """Generates Initiative entities with strategic attributes."""

    GENERATES = EntityType.INITIATIVE

    def generate(self, count: int, context: GenerationContext) -> list[Initiative]:
        faker = context.faker
        systems = context.get_entities(EntityType.SYSTEM)
        initiatives: list[Initiative] = []

        for i in range(count):
            init_type = random.choice(INITIATIVE_TYPES)
            budget = round(random.uniform(100_000, 20_000_000), 2)
            status = random.choice(INITIATIVE_STATUSES)

            initiative = Initiative(
                name=f"{init_type} — {faker.bs().title()}",
                description=f"Strategic initiative: {init_type}",
                initiative_id=f"SI-{i + 1:05d}",
                initiative_tier=random.choice(["Portfolio", "Program", "Project", "Workstream"]),
                initiative_type=init_type,
                initiative_category=random.choice(
                    ["Strategic", "Operational", "Regulatory", "Remediation"]
                ),
                strategic_priority=random.choice(["Must Do", "Should Do", "Could Do"]),
                origin=random.choice(
                    [
                        "Strategic Planning",
                        "Board Directive",
                        "Regulatory Requirement",
                        "Audit Finding",
                        "Competitive Response",
                        "Technology End-of-Life",
                    ]
                ),
                current_status=status,
                phase=random.choice(
                    ["Initiation", "Planning", "Execution", "Monitoring & Control", "Closing"]
                ),
                planned_start_date=str(faker.date_between(start_date="-1y", end_date="today")),
                planned_end_date=str(faker.date_between(start_date="today", end_date="+2y")),
                total_budget=TotalBudget(
                    approved_budget=budget,
                    currency="USD",
                    budget_type=random.choice(["Capital", "Operating", "Mixed"]),
                ),
                budget_breakdown=[
                    BudgetBreakdown(
                        category="Technology / Licensing", amount=round(budget * 0.4, 2)
                    ),
                    BudgetBreakdown(
                        category="Professional Services", amount=round(budget * 0.3, 2)
                    ),
                    BudgetBreakdown(category="Personnel / Labor", amount=round(budget * 0.25, 2)),
                    BudgetBreakdown(category="Contingency", amount=round(budget * 0.05, 2)),
                ],
                funding_source=FundingSource(
                    source_type=random.choice(
                        ["Operating Budget", "Capital Budget", "Innovation Fund"]
                    ),
                ),
                business_case_summary=BusinessCaseSummary(
                    expected_costs=budget,
                    roi_estimate_pct=round(random.uniform(50, 300), 1),
                    payback_period_months=random.randint(6, 48),
                ),
                success_criteria=[
                    SuccessCriterion(
                        criterion="On-time delivery",
                        metric="Schedule adherence",
                        target="Within 10% of planned",
                        measurement_method="PMO tracking",
                    ),
                ],
                executive_sponsor=faker.name(),
                initiative_lead=faker.name(),
                owning_org_unit="",
                initiative_risk_profile=InitiativeRiskProfile(
                    overall_risk=random.choice(RISK_LEVELS),
                    schedule_risk=random.choice(RISK_LEVELS),
                    budget_risk=random.choice(RISK_LEVELS),
                ),
                active_risks=[
                    ActiveRisk(
                        risk_id=f"IR-{i + 1:03d}-001",
                        description=f"Key risk for {init_type}",
                        probability=random.choice(THREAT_LIKELIHOOD),
                        impact=random.choice(RISK_LEVELS),
                        risk_level=random.choice(RISK_LEVELS),
                        owner=faker.name(),
                    ),
                ],
                resource_requirements=ResourceRequirements(
                    total_fte=round(random.uniform(5, 100), 1),
                    internal_fte=round(random.uniform(3, 70), 1),
                    external_fte=round(random.uniform(2, 30), 1),
                ),
                key_milestones=[
                    KeyMilestone(
                        milestone_name="Go-Live",
                        planned_date=str(faker.date_between(start_date="today", end_date="+2y")),
                        status=random.choice(["Not Started", "On Track", "At Risk"]),
                        milestone_type="Go-Live",
                    ),
                ],
                impacts_systems=[
                    ImpactsSystem(
                        system_id=random.choice(systems).id if systems else "",
                        impact_type=random.choice(
                            ["Implements New", "Migrates", "Upgrades", "Decommissions"]
                        ),
                    ),
                ]
                if systems
                else [],
                temporal_and_versioning=TemporalAndVersioning(schema_version="1.0.0"),
                provenance_and_confidence=ProvenanceAndConfidence(
                    primary_data_source="PPM Tool",
                    confidence_level=random.choice(["High", "Medium"]),
                ),
                tags=[init_type.lower().replace(" ", "-").replace("/", "-")],
            )
            initiatives.append(initiative)

        context.store(EntityType.INITIATIVE, initiatives)
        return initiatives
