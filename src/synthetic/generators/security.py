"""Generators for Vulnerability and ThreatActor entities."""

from __future__ import annotations

import random

from domain.base import EntityType
from domain.entities.threat_actor import ThreatActor
from domain.entities.vulnerability import Vulnerability
from synthetic.base import AbstractGenerator, GenerationContext, GeneratorRegistry

VULN_TYPES = [
    "SQL Injection", "Cross-Site Scripting", "Buffer Overflow",
    "Remote Code Execution", "Privilege Escalation", "Authentication Bypass",
    "Information Disclosure", "Denial of Service", "Path Traversal",
    "Insecure Deserialization", "SSRF", "Broken Access Control",
]

SEVERITIES = ["low", "medium", "high", "critical"]
CVSS_RANGES = {"low": (0.1, 3.9), "medium": (4.0, 6.9), "high": (7.0, 8.9), "critical": (9.0, 10.0)}

THREAT_ACTOR_TYPES = ["nation_state", "cybercriminal", "hacktivist", "insider", "apt"]
MOTIVATIONS = ["financial", "espionage", "disruption", "ideological", "retaliation"]
SOPHISTICATION = ["low", "medium", "high", "advanced"]

APT_NAMES = [
    "Midnight Blizzard", "Cozy Bear", "Fancy Bear", "Lazarus Group",
    "Equation Group", "Shadow Brokers", "DarkSide", "REvil",
    "Sandworm", "Turla", "Kimsuky", "Charming Kitten",
]

TTPS = [
    "T1566-Phishing", "T1059-Command Scripting", "T1078-Valid Accounts",
    "T1021-Remote Services", "T1071-Application Layer Protocol",
    "T1486-Data Encrypted for Impact", "T1053-Scheduled Task",
    "T1027-Obfuscated Files", "T1105-Ingress Tool Transfer",
    "T1070-Indicator Removal", "T1218-System Binary Proxy Execution",
]


@GeneratorRegistry.register
class VulnerabilityGenerator(AbstractGenerator):
    """Generates Vulnerability entities."""

    GENERATES = EntityType.VULNERABILITY

    def generate(self, count: int, context: GenerationContext) -> list[Vulnerability]:
        faker = context.faker
        vulns: list[Vulnerability] = []

        for _ in range(count):
            severity = random.choice(SEVERITIES)
            cvss_min, cvss_max = CVSS_RANGES[severity]

            vuln = Vulnerability(
                name=random.choice(VULN_TYPES),
                description=faker.sentence(nb_words=12),
                cve_id=f"CVE-{random.randint(2020, 2025)}-{random.randint(10000, 99999)}",
                cvss_score=round(random.uniform(cvss_min, cvss_max), 1),
                severity=severity,
                status=random.choice(["open", "mitigated", "accepted", "resolved"]),
                exploit_available=random.random() < 0.3,
                patch_available=random.random() < 0.6,
                affected_component=faker.word(),
                discovery_date=str(faker.date_between(start_date="-2y", end_date="today")),
                tags=[severity],
            )
            vulns.append(vuln)

        context.store(EntityType.VULNERABILITY, vulns)
        return vulns


@GeneratorRegistry.register
class ThreatActorGenerator(AbstractGenerator):
    """Generates ThreatActor entities."""

    GENERATES = EntityType.THREAT_ACTOR

    def generate(self, count: int, context: GenerationContext) -> list[ThreatActor]:
        faker = context.faker
        actors: list[ThreatActor] = []

        for i in range(count):
            actor_name = APT_NAMES[i] if i < len(APT_NAMES) else f"APT-{faker.word().title()}"

            actor = ThreatActor(
                name=actor_name,
                description=faker.sentence(nb_words=10),
                actor_type=random.choice(THREAT_ACTOR_TYPES),
                sophistication=random.choice(SOPHISTICATION),
                motivation=random.choice(MOTIVATIONS),
                origin_country=faker.country_code(),
                first_seen=str(faker.date_between(start_date="-5y", end_date="-1y")),
                last_seen=str(faker.date_between(start_date="-1y", end_date="today")),
                aliases=[faker.word().title() for _ in range(random.randint(1, 3))],
                ttps=random.sample(TTPS, k=random.randint(2, 5)),
                target_industries=random.sample(
                    ["technology", "healthcare", "finance", "government", "energy", "defense"],
                    k=random.randint(1, 3),
                ),
                tags=[random.choice(THREAT_ACTOR_TYPES)],
            )
            actors.append(actor)

        context.store(EntityType.THREAT_ACTOR, actors)
        return actors
