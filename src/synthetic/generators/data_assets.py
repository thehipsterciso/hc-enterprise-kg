"""Generator for DataAsset entities."""

from __future__ import annotations

import random

from domain.base import EntityType
from domain.entities.data_asset import DataAsset
from synthetic.base import AbstractGenerator, GenerationContext, GeneratorRegistry

# Coordinated templates: name → {data_type, classification, format, description}
ASSET_TEMPLATES = [
    {
        "name": "Customer Database",
        "data_type": "pii",
        "classification": "confidential",
        "format": "sql",
        "desc": "Primary customer records including contact details and account history",
    },
    {
        "name": "Employee Records",
        "data_type": "pii",
        "classification": "restricted",
        "format": "sql",
        "desc": "HR employee records with personal data, compensation, and benefits",
    },
    {
        "name": "Financial Ledger",
        "data_type": "financial",
        "classification": "restricted",
        "format": "sql",
        "desc": "General ledger with transaction records and account balances",
    },
    {
        "name": "Product Catalog",
        "data_type": "operational",
        "classification": "internal",
        "format": "sql",
        "desc": "Product and service catalog with pricing and availability",
    },
    {
        "name": "Audit Logs",
        "data_type": "operational",
        "classification": "confidential",
        "format": "data_lake",
        "desc": "System audit logs for security monitoring and compliance",
    },
    {
        "name": "Email Archive",
        "data_type": "pii",
        "classification": "confidential",
        "format": "file",
        "desc": "Corporate email archive for legal hold and compliance",
    },
    {
        "name": "Source Code Repository",
        "data_type": "intellectual_property",
        "classification": "restricted",
        "format": "file",
        "desc": "Application source code and build artifacts",
    },
    {
        "name": "Marketing Analytics",
        "data_type": "operational",
        "classification": "internal",
        "format": "data_lake",
        "desc": "Campaign performance metrics and customer engagement data",
    },
    {
        "name": "Sales Pipeline Data",
        "data_type": "financial",
        "classification": "confidential",
        "format": "sql",
        "desc": "CRM pipeline data with deal values and sales forecasts",
    },
    {
        "name": "Support Tickets",
        "data_type": "operational",
        "classification": "internal",
        "format": "nosql",
        "desc": "Customer support tickets with resolution tracking",
    },
    {
        "name": "Compliance Reports",
        "data_type": "operational",
        "classification": "confidential",
        "format": "file",
        "desc": "Regulatory compliance reports and audit findings",
    },
    {
        "name": "Network Logs",
        "data_type": "operational",
        "classification": "internal",
        "format": "stream",
        "desc": "Network traffic logs for security monitoring and forensics",
    },
    {
        "name": "Backup Archives",
        "data_type": "operational",
        "classification": "confidential",
        "format": "file",
        "desc": "System backup archives for disaster recovery",
    },
    {
        "name": "Research Data",
        "data_type": "intellectual_property",
        "classification": "restricted",
        "format": "data_lake",
        "desc": "R&D research data including experimental results and analyses",
    },
    {
        "name": "Client Contracts",
        "data_type": "financial",
        "classification": "restricted",
        "format": "file",
        "desc": "Signed client contracts and service agreements",
    },
    {
        "name": "Vendor Records",
        "data_type": "financial",
        "classification": "confidential",
        "format": "sql",
        "desc": "Third-party vendor information and risk assessments",
    },
    {
        "name": "Payroll Data",
        "data_type": "pii",
        "classification": "restricted",
        "format": "sql",
        "desc": "Employee payroll records including salary and tax information",
    },
    {
        "name": "Health Records",
        "data_type": "phi",
        "classification": "restricted",
        "format": "sql",
        "desc": "Protected health information subject to HIPAA requirements",
    },
    {
        "name": "Transaction History",
        "data_type": "financial",
        "classification": "confidential",
        "format": "data_lake",
        "desc": "Historical transaction records for reporting and analytics",
    },
    {
        "name": "User Activity Logs",
        "data_type": "operational",
        "classification": "internal",
        "format": "stream",
        "desc": "Application user activity logs for behavior analytics",
    },
    {
        "name": "API Keys Vault",
        "data_type": "operational",
        "classification": "restricted",
        "format": "nosql",
        "desc": "Secrets management vault storing API keys and credentials",
    },
    {
        "name": "Configuration Store",
        "data_type": "operational",
        "classification": "internal",
        "format": "nosql",
        "desc": "Centralized configuration management for infrastructure and applications",
    },
]

# Overflow names by data type
OVERFLOW_NAMES: dict[str, list[str]] = {
    "pii": ["Contact Directory", "User Profiles", "Identity Store", "Benefits Records"],
    "phi": ["Lab Results Store", "Imaging Archive", "Patient Demographics"],
    "financial": ["Budget Tracker", "Invoice Archive", "Revenue Reports", "Tax Records"],
    "intellectual_property": ["Patent Filings", "Trade Secrets Vault", "Design Documents"],
    "operational": ["Metrics Store", "Event Queue", "Cache Layer", "Job Scheduler Data"],
    "public": ["Public API Docs", "Marketing Content", "Press Releases"],
}

REGULATIONS = ["GDPR", "HIPAA", "PCI-DSS", "SOX", "CCPA", "FERPA"]


@GeneratorRegistry.register
class DataAssetGenerator(AbstractGenerator):
    """Generates DataAsset entities with coordinated type/classification/format."""

    GENERATES = EntityType.DATA_ASSET

    def generate(self, count: int, context: GenerationContext) -> list[DataAsset]:
        assets: list[DataAsset] = []

        for i in range(count):
            if i < len(ASSET_TEMPLATES):
                tmpl = ASSET_TEMPLATES[i]
                name = tmpl["name"]
                data_type = tmpl["data_type"]
                classification = tmpl["classification"]
                fmt = tmpl["format"]
                desc = tmpl["desc"]
            else:
                data_type = random.choice(
                    ["pii", "phi", "financial", "intellectual_property", "operational"]
                )
                overflow = OVERFLOW_NAMES.get(data_type, ["Data Store"])
                name = random.choice(overflow)
                if data_type in ("pii", "phi", "intellectual_property"):
                    classification = random.choice(["restricted", "confidential"])
                elif data_type == "financial":
                    classification = random.choice(["confidential", "restricted"])
                else:
                    classification = random.choice(["internal", "confidential"])
                fmt = random.choice(["sql", "nosql", "file", "data_lake", "stream"])
                desc = f"{data_type.replace('_', ' ').title()} data store: {name}"

            asset = DataAsset(
                name=name,
                description=desc,
                data_type=data_type,
                classification=classification,
                format=fmt,
                retention_days=random.choice([30, 90, 365, 730, 2555]),
                is_encrypted=(
                    classification in ("restricted", "confidential") or random.random() < 0.3
                ),
                record_count=random.randint(1000, 10000000),
                regulations=(
                    random.sample(REGULATIONS, k=random.randint(1, 3))
                    if classification in ("confidential", "restricted")
                    else []
                ),
                tags=[classification, data_type],
            )
            assets.append(asset)

        context.store(EntityType.DATA_ASSET, assets)
        return assets
