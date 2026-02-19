"""Generator for DataAsset entities."""

from __future__ import annotations

import random

from domain.base import EntityType
from domain.entities.data_asset import DataAsset
from synthetic.base import AbstractGenerator, GenerationContext, GeneratorRegistry

DATA_TYPES = ["pii", "phi", "financial", "intellectual_property", "operational", "public"]
CLASSIFICATIONS = ["public", "internal", "confidential", "restricted"]
FORMATS = ["sql", "nosql", "file", "api", "stream", "data_lake"]
REGULATIONS = ["GDPR", "HIPAA", "PCI-DSS", "SOX", "CCPA", "FERPA"]

ASSET_NAMES = [
    "Customer Database",
    "Employee Records",
    "Financial Ledger",
    "Product Catalog",
    "Audit Logs",
    "Email Archive",
    "Source Code Repository",
    "Marketing Analytics",
    "Sales Pipeline Data",
    "Support Tickets",
    "Compliance Reports",
    "Network Logs",
    "Backup Archives",
    "Research Data",
    "Client Contracts",
    "Vendor Records",
    "Payroll Data",
    "Health Records",
    "Transaction History",
    "User Activity Logs",
    "API Keys Vault",
    "Configuration Store",
]


@GeneratorRegistry.register
class DataAssetGenerator(AbstractGenerator):
    """Generates DataAsset entities."""

    GENERATES = EntityType.DATA_ASSET

    def generate(self, count: int, context: GenerationContext) -> list[DataAsset]:
        faker = context.faker
        assets: list[DataAsset] = []

        for i in range(count):
            name = ASSET_NAMES[i] if i < len(ASSET_NAMES) else f"{faker.word().title()} Data Store"
            data_type = random.choice(DATA_TYPES)
            classification = random.choice(CLASSIFICATIONS)

            asset = DataAsset(
                name=name,
                description=faker.sentence(nb_words=10),
                data_type=data_type,
                classification=classification,
                format=random.choice(FORMATS),
                retention_days=random.choice([30, 90, 365, 730, 2555]),
                is_encrypted=random.random() < 0.6,
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
