"""Generator for Policy entities."""

from __future__ import annotations

import random

from domain.base import EntityType
from domain.entities.policy import Policy
from synthetic.base import AbstractGenerator, GenerationContext, GeneratorRegistry

POLICY_TEMPLATES = [
    (
        "Access Control Policy",
        "access_control",
        "NIST",
        "AC-1",
        "Defines access control requirements for systems and data",
    ),
    (
        "Data Classification Policy",
        "data_protection",
        "ISO27001",
        "A.8.2",
        "Establishes data classification levels and handling requirements",
    ),
    (
        "Incident Response Plan",
        "incident_response",
        "NIST",
        "IR-1",
        "Outlines procedures for detecting, responding to, and recovering from incidents",
    ),
    (
        "Acceptable Use Policy",
        "acceptable_use",
        "CIS",
        "CIS-1.1",
        "Defines acceptable use of organizational IT resources",
    ),
    (
        "Password Policy",
        "authentication",
        "NIST",
        "IA-5",
        "Sets password complexity, rotation, and management requirements",
    ),
    (
        "Network Security Policy",
        "network_security",
        "ISO27001",
        "A.13.1",
        "Governs network segmentation, monitoring, and access controls",
    ),
    (
        "Encryption Policy",
        "encryption",
        "PCI-DSS",
        "3.4",
        "Mandates encryption standards for data at rest and in transit",
    ),
    (
        "Remote Access Policy",
        "remote_access",
        "NIST",
        "AC-17",
        "Controls remote access methods and authentication requirements",
    ),
    (
        "Change Management Policy",
        "change_management",
        "ITIL",
        "CHG-1",
        "Establishes change approval workflows and rollback procedures",
    ),
    (
        "Backup and Recovery Policy",
        "backup",
        "ISO27001",
        "A.12.3",
        "Defines backup frequency, retention, and recovery testing",
    ),
    (
        "Third-Party Risk Policy",
        "vendor_management",
        "SOC2",
        "CC9.2",
        "Governs vendor assessment, onboarding, and ongoing risk monitoring",
    ),
    (
        "Data Retention Policy",
        "data_retention",
        "GDPR",
        "Art-5",
        "Specifies data retention periods and secure disposal requirements",
    ),
    (
        "Physical Security Policy",
        "physical_security",
        "ISO27001",
        "A.11.1",
        "Controls physical access to facilities and secure areas",
    ),
    (
        "Security Awareness Training",
        "training",
        "NIST",
        "AT-2",
        "Mandates security awareness training frequency and content",
    ),
    (
        "Vulnerability Management Policy",
        "vulnerability_management",
        "NIST",
        "RA-5",
        "Defines vulnerability scanning, prioritization, and remediation SLAs",
    ),
    (
        "Business Continuity Plan",
        "business_continuity",
        "ISO22301",
        "BC-1",
        "Outlines business continuity and disaster recovery procedures",
    ),
    (
        "Privacy Policy",
        "privacy",
        "GDPR",
        "Art-13",
        "Governs personal data collection, processing, and subject rights",
    ),
    (
        "Mobile Device Policy",
        "mobile_security",
        "CIS",
        "CIS-5.1",
        "Controls mobile device enrollment, configuration, and remote wipe",
    ),
    (
        "Cloud Security Policy",
        "cloud_security",
        "CSA",
        "CCM-1",
        "Establishes security requirements for cloud service adoption",
    ),
    (
        "Logging and Monitoring Policy",
        "monitoring",
        "NIST",
        "AU-2",
        "Defines logging requirements and security monitoring standards",
    ),
]

# Overflow policy types with contextual names
OVERFLOW_POLICIES = [
    (
        "API Security Policy",
        "api_security",
        "OWASP",
        "API-1",
        "Governs API authentication, rate limiting, and input validation",
    ),
    (
        "Patch Management Policy",
        "patch_management",
        "CIS",
        "CIS-3.4",
        "Defines patching timelines based on vulnerability severity",
    ),
    (
        "Identity Lifecycle Policy",
        "identity_management",
        "NIST",
        "IA-4",
        "Controls account provisioning, review, and deprovisioning",
    ),
    (
        "Secure Development Policy",
        "sdlc",
        "OWASP",
        "SDLC-1",
        "Mandates secure coding practices and code review requirements",
    ),
    (
        "Asset Management Policy",
        "asset_management",
        "ISO27001",
        "A.8.1",
        "Establishes asset inventory, ownership, and lifecycle tracking",
    ),
    (
        "Wireless Security Policy",
        "wireless_security",
        "CIS",
        "CIS-15.1",
        "Controls wireless network configuration and access",
    ),
    (
        "Email Security Policy",
        "email_security",
        "NIST",
        "SC-7",
        "Defines email filtering, authentication, and anti-phishing controls",
    ),
    (
        "Database Security Policy",
        "database_security",
        "CIS",
        "CIS-6.1",
        "Governs database access, encryption, and audit logging",
    ),
    (
        "Endpoint Protection Policy",
        "endpoint_security",
        "CIS",
        "CIS-10.1",
        "Mandates endpoint detection, response, and hardening standards",
    ),
    (
        "Supply Chain Security Policy",
        "supply_chain",
        "NIST",
        "SR-1",
        "Controls software supply chain integrity and provenance verification",
    ),
]


@GeneratorRegistry.register
class PolicyGenerator(AbstractGenerator):
    """Generates Policy entities with contextual descriptions."""

    GENERATES = EntityType.POLICY

    def generate(self, count: int, context: GenerationContext) -> list[Policy]:
        policies: list[Policy] = []
        all_templates = list(POLICY_TEMPLATES) + list(OVERFLOW_POLICIES)

        for i in range(count):
            if i < len(all_templates):
                name, ptype, framework, control_id, desc = all_templates[i]
            else:
                # Cycle through templates for very large counts
                base = all_templates[i % len(all_templates)]
                rev = (i // len(all_templates)) + 1
                name = f"{base[0]} v{rev}"
                ptype = base[1]
                framework = base[2]
                control_id = f"{base[3]}-r{rev}"
                desc = base[4]

            policy = Policy(
                name=name,
                description=desc,
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
