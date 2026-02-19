"""Generator for Vendor entities."""

from __future__ import annotations

import random

from hc_enterprise_kg.domain.base import EntityType
from hc_enterprise_kg.domain.entities.vendor import Vendor
from hc_enterprise_kg.synthetic.base import AbstractGenerator, GenerationContext, GeneratorRegistry

VENDOR_TYPES = ["saas", "iaas", "consulting", "hardware", "managed_service", "software_license"]
CERTIFICATIONS = ["SOC2", "ISO27001", "HIPAA", "PCI-DSS", "FedRAMP", "CSA-STAR"]
RISK_TIERS = ["low", "medium", "high", "critical"]


@GeneratorRegistry.register
class VendorGenerator(AbstractGenerator):
    """Generates Vendor entities."""

    GENERATES = EntityType.VENDOR

    def generate(self, count: int, context: GenerationContext) -> list[Vendor]:
        faker = context.faker
        vendors: list[Vendor] = []

        for _ in range(count):
            vendor_type = random.choice(VENDOR_TYPES)
            has_data = random.random() < 0.4

            vendor = Vendor(
                name=faker.company(),
                description=f"{vendor_type.replace('_', ' ').title()} provider",
                vendor_type=vendor_type,
                contract_value=round(random.uniform(5000, 2000000), 2),
                risk_tier=random.choice(RISK_TIERS),
                has_data_access=has_data,
                data_classification_access=(
                    random.sample(["public", "internal", "confidential", "restricted"], k=random.randint(1, 2))
                    if has_data
                    else []
                ),
                compliance_certifications=random.sample(
                    CERTIFICATIONS, k=random.randint(0, 3)
                ),
                contract_expiry=str(faker.date_between(start_date="today", end_date="+3y")),
                primary_contact=faker.name(),
                sla_uptime=round(random.uniform(99.0, 99.99), 2),
                tags=[vendor_type],
            )
            vendors.append(vendor)

        context.store(EntityType.VENDOR, vendors)
        return vendors
