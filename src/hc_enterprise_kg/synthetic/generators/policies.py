"""Generator for Policy entities."""

from __future__ import annotations

import random

from hc_enterprise_kg.domain.base import EntityType
from hc_enterprise_kg.domain.entities.policy import Policy
from hc_enterprise_kg.synthetic.base import AbstractGenerator, GenerationContext, GeneratorRegistry

POLICY_TEMPLATES = [
    ("Access Control Policy", "access_control", "NIST", "AC-1"),
    ("Data Classification Policy", "data_protection", "ISO27001", "A.8.2"),
    ("Incident Response Plan", "incident_response", "NIST", "IR-1"),
    ("Acceptable Use Policy", "acceptable_use", "CIS", "CIS-1.1"),
    ("Password Policy", "authentication", "NIST", "IA-5"),
    ("Network Security Policy", "network_security", "ISO27001", "A.13.1"),
    ("Encryption Policy", "encryption", "PCI-DSS", "3.4"),
    ("Remote Access Policy", "remote_access", "NIST", "AC-17"),
    ("Change Management Policy", "change_management", "ITIL", "CHG-1"),
    ("Backup and Recovery Policy", "backup", "ISO27001", "A.12.3"),
    ("Third-Party Risk Policy", "vendor_management", "SOC2", "CC9.2"),
    ("Data Retention Policy", "data_retention", "GDPR", "Art-5"),
    ("Physical Security Policy", "physical_security", "ISO27001", "A.11.1"),
    ("Security Awareness Training", "training", "NIST", "AT-2"),
    ("Vulnerability Management Policy", "vulnerability_management", "NIST", "RA-5"),
    ("Business Continuity Plan", "business_continuity", "ISO22301", "BC-1"),
    ("Privacy Policy", "privacy", "GDPR", "Art-13"),
    ("Mobile Device Policy", "mobile_security", "CIS", "CIS-5.1"),
    ("Cloud Security Policy", "cloud_security", "CSA", "CCM-1"),
    ("Logging and Monitoring Policy", "monitoring", "NIST", "AU-2"),
]


@GeneratorRegistry.register
class PolicyGenerator(AbstractGenerator):
    """Generates Policy entities."""

    GENERATES = EntityType.POLICY

    def generate(self, count: int, context: GenerationContext) -> list[Policy]:
        faker = context.faker
        policies: list[Policy] = []

        templates = POLICY_TEMPLATES[:count] if count <= len(POLICY_TEMPLATES) else POLICY_TEMPLATES
        for name, ptype, framework, control_id in templates:
            policy = Policy(
                name=name,
                description=faker.sentence(nb_words=15),
                policy_type=ptype,
                framework=framework,
                control_id=control_id,
                severity=random.choice(["low", "medium", "high", "critical"]),
                is_enforced=random.random() < 0.85,
                review_frequency_days=random.choice([90, 180, 365]),
                tags=[framework.lower()],
            )
            policies.append(policy)

        context.store(EntityType.POLICY, policies)
        return policies
