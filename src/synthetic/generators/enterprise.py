"""Generators for enterprise ontology entity types (L01-L11).

Each generator follows the same pattern as the v0.1 generators: extends
AbstractGenerator, declares GENERATES, and is registered via decorator.
Entities are created with semantically coherent attributes.
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
# Risk matrix: likelihood × impact → risk level
# ---------------------------------------------------------------------------

RISK_MATRIX: dict[str, dict[str, str]] = {
    "Very High": {"Critical": "Critical", "High": "Critical", "Medium": "High", "Low": "Medium"},
    "High": {"Critical": "Critical", "High": "High", "Medium": "High", "Low": "Medium"},
    "Medium": {"Critical": "High", "High": "High", "Medium": "Medium", "Low": "Low"},
    "Low": {"Critical": "High", "High": "Medium", "Medium": "Low", "Low": "Low"},
    "Very Low": {"Critical": "Medium", "High": "Low", "Medium": "Low", "Low": "Low"},
}

RISK_LEVEL_ORDER = {"Low": 0, "Medium": 1, "High": 2, "Critical": 3}
LIKELIHOOD_CHOICES = ["Very High", "High", "Medium", "Low", "Very Low"]
IMPACT_CHOICES = ["Critical", "High", "Medium", "Low"]

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

# Control templates: (framework, domain, type) tuples
CONTROL_TEMPLATES = [
    (
        "NIST 800-53",
        "Access Control",
        "Preventive",
        "Enforce least-privilege access to systems and data",
    ),
    (
        "NIST 800-53",
        "Audit & Accountability",
        "Detective",
        "Monitor and log all access to sensitive resources",
    ),
    (
        "NIST 800-53",
        "Incident Response",
        "Corrective",
        "Contain and remediate security incidents within SLA",
    ),
    (
        "NIST 800-53",
        "Configuration Management",
        "Preventive",
        "Maintain secure baseline configurations for all systems",
    ),
    (
        "NIST 800-53",
        "Risk Assessment",
        "Detective",
        "Conduct periodic risk assessments and vulnerability scans",
    ),
    (
        "ISO 27001",
        "Asset Management",
        "Preventive",
        "Maintain accurate inventory of information assets",
    ),
    ("ISO 27001", "Data Protection", "Preventive", "Encrypt sensitive data at rest and in transit"),
    (
        "ISO 27001",
        "Physical Security",
        "Preventive",
        "Control physical access to facilities and server rooms",
    ),
    (
        "ISO 27001",
        "System & Communications Protection",
        "Preventive",
        "Segment networks and enforce boundary controls",
    ),
    (
        "CIS Controls",
        "Vulnerability Management",
        "Detective",
        "Scan for and remediate vulnerabilities per severity SLA",
    ),
    (
        "CIS Controls",
        "Access Control",
        "Preventive",
        "Implement multi-factor authentication for privileged access",
    ),
    (
        "CIS Controls",
        "Change Management",
        "Preventive",
        "Require approval workflow for production changes",
    ),
    (
        "COBIT",
        "Audit & Accountability",
        "Detective",
        "Maintain audit trails for all critical transactions",
    ),
    (
        "COBIT",
        "Risk Assessment",
        "Detective",
        "Assess IT-related risks and report to governance board",
    ),
    (
        "SOC2 TSC",
        "Data Protection",
        "Preventive",
        "Protect confidentiality of customer data per trust criteria",
    ),
    (
        "SOC2 TSC",
        "Access Control",
        "Preventive",
        "Validate access controls per SOC2 trust service criteria",
    ),
]

# Risk category → name suffixes (replaces faker.bs())
RISK_NAME_TEMPLATES: dict[str, list[str]] = {
    "Operational": [
        "Process Failure",
        "Service Disruption",
        "Capacity Overrun",
        "Key Personnel Loss",
        "Vendor Dependency Failure",
    ],
    "Cybersecurity": [
        "Unpatched Critical Systems",
        "Credential Compromise",
        "Ransomware Exposure",
        "Data Exfiltration",
        "Zero-Day Exploitation",
    ],
    "Compliance": [
        "Regulatory Non-Compliance",
        "Audit Finding Backlog",
        "Policy Violation",
        "Licensing Gap",
        "Data Retention Breach",
    ],
    "Financial": [
        "Revenue Shortfall",
        "Budget Overrun",
        "Fraud Exposure",
        "Currency Fluctuation",
        "Credit Default",
    ],
    "Strategic": [
        "Market Position Erosion",
        "Technology Obsolescence",
        "Competitive Disruption",
        "M&A Integration Failure",
    ],
    "Reputational": [
        "Public Data Breach",
        "Customer Trust Erosion",
        "Media Negative Coverage",
        "Social Media Crisis",
    ],
    "Third-Party": [
        "Vendor Data Breach",
        "Supply Chain Disruption",
        "Contractor Misconduct",
        "SLA Violation",
    ],
    "Technology": [
        "Legacy System Failure",
        "Cloud Outage",
        "Data Center Failure",
        "Integration Breakdown",
    ],
}

# Threat category → pre-mapped type and source
THREAT_CATEGORY_MAP: dict[str, dict] = {
    "Cyber": {
        "types": ["Targeted", "Opportunistic"],
        "sources": ["External", "Partner"],
        "names": [
            "Advanced Persistent Threat",
            "Ransomware Campaign",
            "Phishing Operation",
            "DDoS Attack",
            "Credential Stuffing",
        ],
    },
    "Physical": {
        "types": ["Environmental", "Opportunistic"],
        "sources": ["External", "Environmental"],
        "names": [
            "Facility Intrusion",
            "Equipment Theft",
            "Sabotage Attempt",
            "Unauthorized Physical Access",
        ],
    },
    "Insider": {
        "types": ["Targeted"],
        "sources": ["Internal"],
        "names": [
            "Data Theft by Employee",
            "Privilege Abuse",
            "Intellectual Property Theft",
            "Unauthorized Access Escalation",
        ],
    },
    "Supply Chain": {
        "types": ["Targeted", "Systemic"],
        "sources": ["Partner", "External"],
        "names": [
            "Compromised Dependency",
            "Vendor Software Backdoor",
            "Third-Party Data Breach",
            "Supply Chain Interruption",
        ],
    },
    "Natural Disaster": {
        "types": ["Environmental"],
        "sources": ["Environmental"],
        "names": [
            "Severe Weather Event",
            "Earthquake Risk",
            "Flooding",
            "Power Grid Failure",
        ],
    },
    "Geopolitical": {
        "types": ["Systemic"],
        "sources": ["External"],
        "names": [
            "Sanctions Impact",
            "Trade Restriction",
            "Political Instability",
            "Cross-Border Data Transfer Block",
        ],
    },
    "Regulatory Change": {
        "types": ["Systemic"],
        "sources": ["External"],
        "names": [
            "New Privacy Regulation",
            "Compliance Framework Update",
            "Licensing Requirement Change",
            "Reporting Mandate",
        ],
    },
}

# Integration type → protocol mapping
INTEGRATION_TYPE_PROTOCOLS: dict[str, list[str]] = {
    "API": ["REST", "gRPC", "SOAP"],
    "ETL": ["JDBC", "SFTP"],
    "File Transfer": ["SFTP", "REST"],
    "Message Queue": ["Kafka", "AMQP"],
    "Database Link": ["JDBC"],
    "Webhook": ["REST"],
    "CDC": ["Kafka", "JDBC"],
    "ESB": ["SOAP", "AMQP"],
}

# Integration type → data format mapping
INTEGRATION_TYPE_FORMATS: dict[str, list[str]] = {
    "API": ["JSON", "XML"],
    "ETL": ["CSV", "Parquet", "Avro"],
    "File Transfer": ["CSV", "XML", "Binary"],
    "Message Queue": ["JSON", "Avro"],
    "Database Link": ["Binary"],
    "Webhook": ["JSON"],
    "CDC": ["JSON", "Avro"],
    "ESB": ["XML", "JSON"],
}

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

DATA_DOMAIN_DESCRIPTIONS: dict[str, str] = {
    "Customer Data": "Customer demographics, preferences, interactions, and account information",
    "Financial Data": "Financial transactions, ledger entries, and accounting records",
    "Employee Data": "Employee records, compensation, performance, and benefits data",
    "Product Data": "Product specifications, pricing, inventory, and lifecycle data",
    "Operational Data": "Operational metrics, process logs, and workflow data",
    "Marketing Data": "Campaign analytics, lead scoring, and market research data",
    "Compliance Data": "Regulatory filings, audit reports, and compliance evidence",
    "Clinical Data": "Patient health records, lab results, and clinical trial data",
    "Trading Data": "Trade execution records, market data, and position tracking",
    "Risk Data": "Risk assessments, loss events, and risk indicator metrics",
    "Supply Chain Data": "Supplier records, procurement data, and logistics tracking",
    "Research Data": "Research outputs, experimental data, and intellectual property",
}

# Capability name → functional domain mapping
CAPABILITY_DOMAIN_MAP: dict[str, str] = {
    "Customer Relationship Management": "Sales & Marketing",
    "Financial Planning & Analysis": "Finance",
    "Human Capital Management": "HR",
    "Product Development": "Technology",
    "Supply Chain Management": "Operations",
    "Risk Management": "Risk & Compliance",
    "Compliance Management": "Risk & Compliance",
    "IT Service Management": "Technology",
    "Data Analytics": "Technology",
    "Digital Marketing": "Sales & Marketing",
    "Order Management": "Operations",
    "Procurement": "Operations",
    "Quality Assurance": "Operations",
    "Strategic Planning": "Finance",
    "Cybersecurity Operations": "Technology",
    "Business Intelligence": "Technology",
    "Enterprise Architecture": "Technology",
    "Innovation Management": "Technology",
}

CAPABILITY_NAMES = list(CAPABILITY_DOMAIN_MAP.keys())

# Importance → investment priority correlation
IMPORTANCE_INVESTMENT: dict[str, list[str]] = {
    "Differentiating": ["Invest"],
    "Essential": ["Invest", "Maintain"],
    "Commodity": ["Maintain", "Tolerate"],
}

SITE_TYPES = [
    "Headquarters",
    "Regional Office",
    "Data Center",
    "Branch Office",
    "Operations Center",
    "R&D Facility",
]

# Site type → security tier correlation
SITE_SECURITY_MAP: dict[str, list[str]] = {
    "Headquarters": ["Enhanced", "Restricted"],
    "Regional Office": ["Standard", "Enhanced"],
    "Data Center": ["Restricted"],
    "Branch Office": ["Standard"],
    "Operations Center": ["Enhanced", "Restricted"],
    "R&D Facility": ["Enhanced"],
}

# Product templates: name → {type, criticality}
PRODUCT_TEMPLATES: dict[str, dict] = {
    "Enterprise Platform": {"type": "Platform", "criticality": "Critical"},
    "Analytics Suite": {"type": "Software", "criticality": "High"},
    "Mobile App": {"type": "Software", "criticality": "Medium"},
    "Customer Portal": {"type": "SaaS", "criticality": "High"},
    "Risk Dashboard": {"type": "Software", "criticality": "High"},
    "Compliance Manager": {"type": "SaaS", "criticality": "Critical"},
    "Trading Platform": {"type": "Platform", "criticality": "Critical"},
    "Claims Processor": {"type": "Software", "criticality": "High"},
    "EHR System": {"type": "Software", "criticality": "Critical"},
    "Payment Gateway": {"type": "SaaS", "criticality": "Critical"},
    "API Marketplace": {"type": "Platform", "criticality": "Medium"},
    "Data Lake Platform": {"type": "Platform", "criticality": "High"},
    "Security Operations Center": {"type": "Software", "criticality": "Critical"},
    "Cloud Infrastructure": {"type": "Platform", "criticality": "Critical"},
    "Identity Management": {"type": "SaaS", "criticality": "Critical"},
    "Document Management": {"type": "SaaS", "criticality": "Medium"},
}

PRODUCT_NAMES = list(PRODUCT_TEMPLATES.keys())

# Market segment name → segment_type
SEGMENT_TYPE_MAP: dict[str, str] = {
    "Enterprise": "Company Size",
    "Mid-Market": "Company Size",
    "SMB": "Company Size",
    "Government": "Industry Vertical",
    "Healthcare": "Industry Vertical",
    "Financial Services": "Industry Vertical",
    "Technology": "Industry Vertical",
    "Education": "Industry Vertical",
}

# OrgUnit name templates by type (replaces faker.company_suffix())
OU_NAME_TEMPLATES: dict[str, list[str]] = {
    "Business Unit": [
        "North America",
        "EMEA",
        "APAC",
        "Latin America",
        "Enterprise",
        "Consumer",
        "Government",
    ],
    "Division": [
        "Technology",
        "Operations",
        "Commercial",
        "Financial Services",
        "Healthcare",
        "Corporate Services",
    ],
    "Department": [
        "Engineering",
        "Product",
        "Sales",
        "Marketing",
        "Finance",
        "Compliance",
        "Security",
    ],
    "Team": [
        "Platform",
        "Infrastructure",
        "Data",
        "Customer Success",
        "Incident Response",
        "DevOps",
    ],
    "Shared Service Center": [
        "Global IT Services",
        "HR Shared Services",
        "Finance Operations",
        "Procurement Center",
    ],
    "Center of Excellence": [
        "Cloud CoE",
        "Data & AI CoE",
        "Security CoE",
        "Agile CoE",
        "Automation CoE",
    ],
}

OU_TYPES = list(OU_NAME_TEMPLATES.keys())

# Initiative type → name suffixes (replaces faker.bs())
INITIATIVE_NAME_TEMPLATES: dict[str, list[str]] = {
    "Digital Transformation": [
        "Cloud Migration Program",
        "Digital Workplace Modernization",
        "Customer Experience Digitization",
        "Process Automation Initiative",
    ],
    "Technology Migration / Modernization": [
        "Legacy System Replacement",
        "Platform Consolidation",
        "Infrastructure Modernization",
        "Database Migration",
    ],
    "Process Improvement": [
        "Operational Excellence Program",
        "Lean Process Optimization",
        "Workflow Automation",
        "Service Delivery Enhancement",
    ],
    "Regulatory Compliance": [
        "GDPR Compliance Program",
        "SOX Remediation",
        "Privacy Framework Implementation",
        "Regulatory Reporting Upgrade",
    ],
    "Security Remediation": [
        "Zero Trust Architecture",
        "Vulnerability Remediation Sprint",
        "Identity Governance Overhaul",
        "SOC Modernization",
    ],
    "AI / ML Initiative": [
        "AI-Powered Analytics",
        "Machine Learning Platform",
        "Intelligent Automation",
        "Predictive Risk Modeling",
    ],
    "Cost Optimization": [
        "Cloud Cost Optimization",
        "License Rationalization",
        "Vendor Consolidation",
        "Infrastructure Right-Sizing",
    ],
    "Customer Experience": [
        "Omnichannel Engagement",
        "Self-Service Portal",
        "Customer Journey Optimization",
        "Personalization Engine",
    ],
    "Data Governance": [
        "Enterprise Data Catalog",
        "Data Quality Program",
        "Master Data Management",
        "Data Lineage Implementation",
    ],
    "Infrastructure": [
        "Network Refresh",
        "Data Center Consolidation",
        "Edge Computing Deployment",
        "Hybrid Cloud Implementation",
    ],
}

INITIATIVE_TYPES = list(INITIATIVE_NAME_TEMPLATES.keys())

INITIATIVE_STATUSES = [
    "Proposed",
    "Approved",
    "Planning",
    "In Progress",
    "On Hold",
    "At Risk",
    "Completed",
]

# Contract type → description
CONTRACT_DESCRIPTIONS: dict[str, str] = {
    "Master Services Agreement": (
        "Master services agreement governing professional services engagement"
    ),
    "Statement of Work": "Statement of work defining specific deliverables and timelines",
    "License Agreement": "Software license agreement with usage terms and restrictions",
    "Support Agreement": "Technical support and maintenance agreement with SLA terms",
    "NDA": "Non-disclosure agreement protecting confidential information exchange",
    "Data Processing Agreement": "Data processing agreement governing personal data handling",
}

PORTFOLIO_TEMPLATES = [
    ("Enterprise Solutions", "Product", "Mature", "Core"),
    ("Consumer Products", "Product", "Growth", "Adjacent"),
    ("Digital Services", "Service", "Growth", "Core"),
    ("Platform Services", "Platform", "Mature", "Core"),
    ("Professional Services", "Service", "Mature", "Adjacent"),
    ("Data Products", "Product", "Emerging", "Transformational"),
    ("Cloud Services", "Platform", "Growth", "Core"),
    ("Security Solutions", "Product", "Growth", "Adjacent"),
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
                # Generate overflow regulations with contextual names
                domain = random.choice(
                    ["Data Privacy", "Financial", "Cybersecurity", "Operational"]
                )
                jur = random.choice(["US", "EU", "Global", "UK", "APAC"])
                short = f"{jur}-{domain.replace(' ', '').upper()[:4]}-{i + 1:03d}"
                full = f"{jur} {domain} Regulation {i + 1}"

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
    """Generates Control entities with coherent framework/domain/type."""

    GENERATES = EntityType.CONTROL

    def generate(self, count: int, context: GenerationContext) -> list[Control]:
        faker = context.faker
        controls: list[Control] = []
        for i in range(count):
            if i < len(CONTROL_TEMPLATES):
                framework, domain, ctrl_type, objective = CONTROL_TEMPLATES[i]
            else:
                t = CONTROL_TEMPLATES[i % len(CONTROL_TEMPLATES)]
                framework, domain, ctrl_type, objective = t

            control = Control(
                name=f"{domain} — {framework} Control",
                description=f"{ctrl_type} control for {domain.lower()}",
                control_id=f"CTL-{i + 1:05d}",
                control_type=ctrl_type,
                control_domain=domain,
                control_framework=framework,
                control_objective=objective,
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
    """Generates Risk entities with matrix-derived risk levels."""

    GENERATES = EntityType.RISK

    def generate(self, count: int, context: GenerationContext) -> list[Risk]:
        faker = context.faker
        risks: list[Risk] = []
        for i in range(count):
            category = random.choice(list(RISK_NAME_TEMPLATES.keys()))
            name_suffix = random.choice(RISK_NAME_TEMPLATES[category])

            # Inherent risk: derive level from likelihood × impact
            inh_likelihood = random.choice(LIKELIHOOD_CHOICES)
            inh_impact = random.choice(IMPACT_CHOICES)
            inh_level = RISK_MATRIX[inh_likelihood][inh_impact]

            # Residual risk: must be ≤ inherent (controls reduce risk)
            res_likelihood = random.choice(LIKELIHOOD_CHOICES)
            res_impact = random.choice(IMPACT_CHOICES)
            res_level_raw = RISK_MATRIX[res_likelihood][res_impact]
            # Clamp residual to not exceed inherent
            if RISK_LEVEL_ORDER[res_level_raw] > RISK_LEVEL_ORDER[inh_level]:
                res_level = inh_level
            else:
                res_level = res_level_raw

            risk = Risk(
                name=f"{category} Risk — {name_suffix}",
                description=f"{category} risk: {name_suffix.lower()}",
                risk_id=f"RSK-{i + 1:05d}",
                risk_category=category,
                inherent_likelihood=inh_likelihood,
                inherent_impact=inh_impact,
                inherent_risk_level=inh_level,
                residual_likelihood=res_likelihood,
                residual_impact=res_impact,
                residual_risk_level=res_level,
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
    """Generates Threat entities with category-correlated type/source."""

    GENERATES = EntityType.THREAT

    def generate(self, count: int, context: GenerationContext) -> list[Threat]:
        threats: list[Threat] = []
        categories = list(THREAT_CATEGORY_MAP.keys())

        for i in range(count):
            category = random.choice(categories)
            cat_map = THREAT_CATEGORY_MAP[category]
            name_suffix = random.choice(cat_map["names"])

            likelihood = random.choice(LIKELIHOOD_CHOICES)
            impact = random.choice(IMPACT_CHOICES)
            threat_level = RISK_MATRIX[likelihood][impact]

            threat = Threat(
                name=f"{category} Threat — {name_suffix}",
                description=f"{category} threat: {name_suffix.lower()}",
                threat_id=f"THR-{i + 1:05d}",
                threat_category=category,
                threat_type=random.choice(cat_map["types"]),
                likelihood=likelihood,
                impact_if_realized=impact,
                threat_level=threat_level,
                threat_source=random.choice(cat_map["sources"]),
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
    """Generates Integration entities with type-correlated protocol/format."""

    GENERATES = EntityType.INTEGRATION

    def generate(self, count: int, context: GenerationContext) -> list[Integration]:
        integrations: list[Integration] = []
        int_types = list(INTEGRATION_TYPE_PROTOCOLS.keys())

        for i in range(count):
            int_type = random.choice(int_types)
            protocol = random.choice(INTEGRATION_TYPE_PROTOCOLS[int_type])
            data_format = random.choice(INTEGRATION_TYPE_FORMATS[int_type])

            integration = Integration(
                name=f"{int_type} Integration — {protocol}",
                description=f"{int_type} integration using {protocol} with {data_format} payloads",
                integration_id=f"INT-{i + 1:05d}",
                integration_type=int_type,
                protocol=protocol,
                data_format=data_format,
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
    """Generates DataDomain entities with contextual descriptions."""

    GENERATES = EntityType.DATA_DOMAIN

    def generate(self, count: int, context: GenerationContext) -> list[DataDomain]:
        faker = context.faker
        domains: list[DataDomain] = []
        selected = random.sample(DATA_DOMAIN_NAMES, k=min(count, len(DATA_DOMAIN_NAMES)))

        for i in range(count):
            if i < len(selected):
                name = selected[i]
                desc = DATA_DOMAIN_DESCRIPTIONS.get(name, f"Enterprise data domain: {name}")
            else:
                name = random.choice(DATA_DOMAIN_NAMES)
                desc = DATA_DOMAIN_DESCRIPTIONS.get(name, f"Enterprise data domain: {name}")

            domain = DataDomain(
                name=name,
                description=desc,
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
    """Generates DataFlow entities with correlation fixes."""

    GENERATES = EntityType.DATA_FLOW

    def generate(self, count: int, context: GenerationContext) -> list[DataFlow]:
        systems = context.get_entities(EntityType.SYSTEM)
        flows: list[DataFlow] = []

        for i in range(count):
            if systems and len(systems) >= 2:
                src_sys, tgt_sys = random.sample(systems, 2)
                src = src_sys.name
                tgt = tgt_sys.name
            elif systems:
                src = systems[0].name
                tgt = "External Target"
            else:
                src = "External Source"
                tgt = "External Target"

            classification = random.choice(["Public", "Internal", "Confidential", "Restricted"])
            method = random.choice(["API", "ETL", "File Transfer", "Streaming", "Replication"])
            # Encryption required for sensitive classifications
            encrypted = classification in ("Restricted", "Confidential") or random.random() < 0.3

            flow = DataFlow(
                name=f"Flow: {src} → {tgt}",
                description=(
                    f"{method} transfer of {classification.lower()} data from {src} to {tgt}"
                ),
                flow_id=f"DF-{i + 1:05d}",
                data_classification=classification,
                transfer_method=method,
                frequency=random.choice(["Real-time", "Hourly", "Daily", "Weekly", "On Demand"]),
                encryption_in_transit=encrypted,
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


@GeneratorRegistry.register
class OrgUnitGenerator(AbstractGenerator):
    """Generates OrganizationalUnit entities with realistic names."""

    GENERATES = EntityType.ORGANIZATIONAL_UNIT

    def generate(self, count: int, context: GenerationContext) -> list[OrganizationalUnit]:
        faker = context.faker
        units: list[OrganizationalUnit] = []

        for i in range(count):
            unit_type = random.choice(OU_TYPES)
            name_pool = OU_NAME_TEMPLATES[unit_type]
            base_name = random.choice(name_pool)

            # Map functional domain from name
            domain_map = {
                "Technology": "Technology",
                "Engineering": "Technology",
                "Platform": "Technology",
                "Infrastructure": "Technology",
                "Data": "Technology",
                "DevOps": "Technology",
                "Cloud CoE": "Technology",
                "Data & AI CoE": "Technology",
                "Security CoE": "Technology",
                "Agile CoE": "Technology",
                "Automation CoE": "Technology",
                "Incident Response": "Technology",
                "Sales": "Sales",
                "Commercial": "Sales",
                "Customer Success": "Sales",
                "Marketing": "Marketing",
                "Finance": "Finance",
                "Finance Operations": "Finance",
                "HR Shared Services": "HR",
                "Compliance": "Compliance",
                "Legal": "Legal",
                "Operations": "Operations",
                "Procurement Center": "Operations",
                "Global IT Services": "Technology",
            }
            func_domain = domain_map.get(
                base_name, random.choice(["Technology", "Finance", "Operations", "Sales"])
            )

            unit = OrganizationalUnit(
                name=f"{base_name} {unit_type}",
                description=f"{unit_type}: {base_name}",
                unit_id=f"OU-{i + 1:05d}",
                unit_type=unit_type,
                operational_status=random.choice(
                    ["Active", "Planned", "Under Restructuring", "Dissolved"]
                ),
                geographic_scope=random.choice(["Global", "Regional", "National", "Local"]),
                functional_domain_primary=func_domain,
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
    """Generates BusinessCapability entities with correlated domain/investment."""

    GENERATES = EntityType.BUSINESS_CAPABILITY

    def generate(self, count: int, context: GenerationContext) -> list[BusinessCapability]:
        caps: list[BusinessCapability] = []
        selected = random.sample(CAPABILITY_NAMES, k=min(count, len(CAPABILITY_NAMES)))

        for i in range(count):
            name = selected[i] if i < len(selected) else random.choice(CAPABILITY_NAMES)
            func_domain = CAPABILITY_DOMAIN_MAP.get(name, "Operations")
            importance = random.choice(["Differentiating", "Essential", "Commodity"])
            investment = random.choice(IMPORTANCE_INVESTMENT[importance])

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
                strategic_importance=importance,
                business_criticality=random.choice(["Critical", "High", "Medium", "Low"]),
                investment_priority=investment,
                functional_domain=func_domain,
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
    """Generates Site entities with type-correlated security tier."""

    GENERATES = EntityType.SITE

    def generate(self, count: int, context: GenerationContext) -> list[Site]:
        faker = context.faker
        sites: list[Site] = []
        for i in range(count):
            site_type = random.choice(SITE_TYPES)
            city = faker.city()
            security_tier = random.choice(SITE_SECURITY_MAP.get(site_type, ["Standard"]))

            site = Site(
                name=f"{city} {site_type}",
                description=f"{site_type} facility in {city}",
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
                physical_security_tier=security_tier,
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
    """Generates ProductPortfolio entities with coordinated attributes."""

    GENERATES = EntityType.PRODUCT_PORTFOLIO

    def generate(self, count: int, context: GenerationContext) -> list[ProductPortfolio]:
        faker = context.faker
        portfolios: list[ProductPortfolio] = []
        for i in range(count):
            if i < len(PORTFOLIO_TEMPLATES):
                name, ptype, lifecycle, role = PORTFOLIO_TEMPLATES[i]
            else:
                t = PORTFOLIO_TEMPLATES[i % len(PORTFOLIO_TEMPLATES)]
                name = f"{t[0]} v{(i // len(PORTFOLIO_TEMPLATES)) + 1}"
                ptype, lifecycle, role = t[1], t[2], t[3]

            portfolio = ProductPortfolio(
                name=name,
                description=f"Product portfolio: {name}",
                portfolio_id=f"PF-{i + 1:05d}",
                portfolio_type=ptype,
                lifecycle_stage=lifecycle,
                strategic_role=role,
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
    """Generates Product entities with name-correlated type/criticality."""

    GENERATES = EntityType.PRODUCT

    def generate(self, count: int, context: GenerationContext) -> list[Product]:
        faker = context.faker
        products: list[Product] = []
        selected = random.sample(PRODUCT_NAMES, k=min(count, len(PRODUCT_NAMES)))

        for i in range(count):
            if i < len(selected):
                name = selected[i]
                tmpl = PRODUCT_TEMPLATES[name]
                prod_type = tmpl["type"]
                criticality = tmpl["criticality"]
            else:
                name = random.choice(PRODUCT_NAMES)
                tmpl = PRODUCT_TEMPLATES[name]
                prod_type = tmpl["type"]
                criticality = tmpl["criticality"]

            product = Product(
                name=name,
                description=f"{prod_type} product: {name}",
                product_id=f"PRD-{i + 1:05d}",
                product_type=prod_type,
                lifecycle_stage=random.choice(
                    ["Development", "Launch", "Growth", "Mature", "Decline", "Retired"]
                ),
                product_owner=faker.name(),
                product_manager=faker.name(),
                business_criticality=criticality,
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
    """Generates MarketSegment entities with name-correlated type."""

    GENERATES = EntityType.MARKET_SEGMENT

    def generate(self, count: int, context: GenerationContext) -> list[MarketSegment]:
        faker = context.faker
        segments: list[MarketSegment] = []
        segment_names = list(SEGMENT_TYPE_MAP.keys())

        for i in range(count):
            name = segment_names[i] if i < len(segment_names) else random.choice(segment_names)
            seg_type = SEGMENT_TYPE_MAP.get(name, "Use Case")

            segment = MarketSegment(
                name=name,
                description=f"{seg_type} market segment: {name}",
                segment_id=f"SEG-{i + 1:05d}",
                segment_type=seg_type,
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
    """Generates Customer entities with contextual descriptions."""

    GENERATES = EntityType.CUSTOMER

    def generate(self, count: int, context: GenerationContext) -> list[Customer]:
        faker = context.faker
        customers: list[Customer] = []
        for i in range(count):
            customer_type = random.choice(
                ["Enterprise", "Mid-Market", "SMB", "Government", "Non-Profit"]
            )
            industry = random.choice(
                ["Technology", "Healthcare", "Financial Services", "Manufacturing", "Retail"]
            )
            customer = Customer(
                name=faker.company(),
                description=f"{customer_type} customer in {industry}",
                customer_id=f"CUST-{i + 1:05d}",
                customer_type=customer_type,
                relationship_status=random.choice(["Active", "Prospect", "Churned", "Dormant"]),
                account_tier=random.choice(["Strategic", "Key", "Standard", "Growth"]),
                industry=industry,
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
    """Generates Contract entities with type-contextual descriptions."""

    GENERATES = EntityType.CONTRACT

    def generate(self, count: int, context: GenerationContext) -> list[Contract]:
        faker = context.faker
        vendors = context.get_entities(EntityType.VENDOR)
        contracts: list[Contract] = []
        contract_types = list(CONTRACT_DESCRIPTIONS.keys())

        for i in range(count):
            vendor = random.choice(vendors) if vendors else None
            contract_type = random.choice(contract_types)
            desc = CONTRACT_DESCRIPTIONS[contract_type]

            contract = Contract(
                name=f"Contract — {vendor.name if vendor else faker.company()}",
                description=desc,
                contract_id=f"CTR-{i + 1:05d}",
                contract_type=contract_type,
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
    """Generates Initiative entities with contextual names."""

    GENERATES = EntityType.INITIATIVE

    def generate(self, count: int, context: GenerationContext) -> list[Initiative]:
        faker = context.faker
        systems = context.get_entities(EntityType.SYSTEM)
        initiatives: list[Initiative] = []

        for i in range(count):
            init_type = random.choice(INITIATIVE_TYPES)
            name_suffix = random.choice(INITIATIVE_NAME_TEMPLATES[init_type])
            budget = round(random.uniform(100_000, 20_000_000), 2)
            status = random.choice(INITIATIVE_STATUSES)

            initiative = Initiative(
                name=f"{init_type} — {name_suffix}",
                description=f"Strategic initiative: {name_suffix}",
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
                    [
                        "Initiation",
                        "Planning",
                        "Execution",
                        "Monitoring & Control",
                        "Closing",
                    ]
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
                        category="Technology / Licensing",
                        amount=round(budget * 0.4, 2),
                    ),
                    BudgetBreakdown(
                        category="Professional Services",
                        amount=round(budget * 0.3, 2),
                    ),
                    BudgetBreakdown(
                        category="Personnel / Labor",
                        amount=round(budget * 0.25, 2),
                    ),
                    BudgetBreakdown(
                        category="Contingency",
                        amount=round(budget * 0.05, 2),
                    ),
                ],
                funding_source=FundingSource(
                    source_type=random.choice(
                        [
                            "Operating Budget",
                            "Capital Budget",
                            "Innovation Fund",
                        ]
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
                    overall_risk=random.choice(IMPACT_CHOICES),
                    schedule_risk=random.choice(IMPACT_CHOICES),
                    budget_risk=random.choice(IMPACT_CHOICES),
                ),
                active_risks=[
                    ActiveRisk(
                        risk_id=f"IR-{i + 1:03d}-001",
                        description=f"Key risk for {name_suffix}",
                        probability=random.choice(LIKELIHOOD_CHOICES),
                        impact=random.choice(IMPACT_CHOICES),
                        risk_level=random.choice(IMPACT_CHOICES),
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
                            [
                                "Implements New",
                                "Migrates",
                                "Upgrades",
                                "Decommissions",
                            ]
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
