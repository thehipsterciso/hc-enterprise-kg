"""Generator for Vendor entities."""

from __future__ import annotations

import random

from domain.base import EntityType
from domain.entities.vendor import Vendor
from synthetic.base import AbstractGenerator, GenerationContext, GeneratorRegistry

# Vendor type profiles: type → {name_suffixes, risk_range, data_access_pct, cert_pool}
VENDOR_PROFILES: dict[str, dict] = {
    "saas": {
        "suffixes": ["Cloud", "Online", "Platform", "Hub", "Suite"],
        "risk_range": ["medium", "high"],
        "data_access_pct": 0.7,
        "cert_pool": ["SOC2", "ISO27001", "CSA-STAR"],
    },
    "iaas": {
        "suffixes": ["Cloud Services", "Infrastructure", "Hosting", "Data Centers"],
        "risk_range": ["high", "critical"],
        "data_access_pct": 0.9,
        "cert_pool": ["SOC2", "ISO27001", "FedRAMP", "CSA-STAR"],
    },
    "consulting": {
        "suffixes": ["Consulting", "Advisory", "Partners", "Group"],
        "risk_range": ["low", "medium"],
        "data_access_pct": 0.3,
        "cert_pool": ["ISO27001"],
    },
    "hardware": {
        "suffixes": ["Technologies", "Systems", "Hardware", "Electronics"],
        "risk_range": ["low", "medium"],
        "data_access_pct": 0.1,
        "cert_pool": ["ISO27001"],
    },
    "managed_service": {
        "suffixes": ["Managed Services", "MSP", "IT Solutions", "Operations"],
        "risk_range": ["high", "critical"],
        "data_access_pct": 0.8,
        "cert_pool": ["SOC2", "ISO27001", "HIPAA"],
    },
    "software_license": {
        "suffixes": ["Software", "Labs", "Digital", "Tech"],
        "risk_range": ["low", "medium"],
        "data_access_pct": 0.2,
        "cert_pool": ["SOC2", "ISO27001"],
    },
}

VENDOR_PREFIXES = [
    "Apex",
    "Summit",
    "Crest",
    "Vertex",
    "Pinnacle",
    "Horizon",
    "Nexus",
    "Vanguard",
    "Catalyst",
    "Meridian",
    "Prism",
    "Atlas",
    "Aegis",
    "Forge",
    "Onyx",
    "Nova",
    "Zenith",
    "Stratos",
    "Citadel",
    "Quantum",
]


@GeneratorRegistry.register
class VendorGenerator(AbstractGenerator):
    """Generates Vendor entities with type-correlated attributes."""

    GENERATES = EntityType.VENDOR

    def generate(self, count: int, context: GenerationContext) -> list[Vendor]:
        faker = context.faker
        vendors: list[Vendor] = []

        for _ in range(count):
            vendor_type = random.choice(list(VENDOR_PROFILES.keys()))
            vp = VENDOR_PROFILES[vendor_type]
            suffix = random.choice(vp["suffixes"])
            prefix = random.choice(VENDOR_PREFIXES)
            name = f"{prefix} {suffix}"

            has_data = random.random() < vp["data_access_pct"]
            risk_tier = random.choice(vp["risk_range"])
            certs = random.sample(
                vp["cert_pool"], k=min(random.randint(0, 2), len(vp["cert_pool"]))
            )
            # Higher risk vendors with data access should have certifications
            if has_data and risk_tier in ("high", "critical") and not certs:
                certs = [random.choice(vp["cert_pool"])]

            vendor = Vendor(
                name=name,
                description=f"{vendor_type.replace('_', ' ').title()} provider — {name}",
                vendor_type=vendor_type,
                contract_value=round(random.uniform(5000, 2000000), 2),
                risk_tier=risk_tier,
                has_data_access=has_data,
                data_classification_access=(
                    random.sample(
                        ["public", "internal", "confidential", "restricted"],
                        k=random.randint(1, 2),
                    )
                    if has_data
                    else []
                ),
                compliance_certifications=certs,
                contract_expiry=str(faker.date_between(start_date="today", end_date="+3y")),
                primary_contact=faker.name(),
                sla_uptime=round(random.uniform(99.0, 99.99), 2),
                tags=[vendor_type],
            )
            vendors.append(vendor)

        context.store(EntityType.VENDOR, vendors)
        return vendors
