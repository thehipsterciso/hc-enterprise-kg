"""Generators for Vulnerability and ThreatActor entities."""

from __future__ import annotations

import random

from domain.base import EntityType
from domain.entities.threat_actor import ThreatActor
from domain.entities.vulnerability import Vulnerability
from synthetic.base import AbstractGenerator, GenerationContext, GeneratorRegistry

# Vulnerability type → {descriptions, components}
VULN_TEMPLATES: dict[str, dict] = {
    "SQL Injection": {
        "descriptions": [
            "SQL injection vulnerability in user input handling",
            "Unsanitized query parameters allow SQL injection",
            "Database query construction vulnerable to injection via form fields",
        ],
        "components": [
            "login form", "search API", "user profile endpoint",
            "reporting module", "admin dashboard query",
        ],
    },
    "Cross-Site Scripting": {
        "descriptions": [
            "Reflected XSS in URL parameter processing",
            "Stored XSS vulnerability in user-generated content",
            "DOM-based XSS through unescaped template rendering",
        ],
        "components": [
            "comment system", "user profile page", "search results",
            "notification display", "message rendering",
        ],
    },
    "Buffer Overflow": {
        "descriptions": [
            "Heap buffer overflow in input parsing routine",
            "Stack-based buffer overflow in network protocol handler",
            "Integer overflow leading to buffer overwrite",
        ],
        "components": [
            "packet parser", "file upload handler", "image processing library",
            "protocol decoder", "memory allocator",
        ],
    },
    "Remote Code Execution": {
        "descriptions": [
            "Remote code execution via deserialization of untrusted data",
            "Command injection enabling arbitrary code execution",
            "Template injection allowing server-side code execution",
        ],
        "components": [
            "API endpoint", "file processing service", "template engine",
            "deserialization handler", "webhook processor",
        ],
    },
    "Privilege Escalation": {
        "descriptions": [
            "Local privilege escalation through SUID binary exploitation",
            "Vertical privilege escalation via insecure role check",
            "Privilege escalation through misconfigured sudo rules",
        ],
        "components": [
            "authentication module", "role-based access control",
            "sudo configuration", "service account handler",
        ],
    },
    "Authentication Bypass": {
        "descriptions": [
            "Authentication bypass through token manipulation",
            "Session fixation allowing authentication bypass",
            "Missing authentication check on administrative endpoint",
        ],
        "components": [
            "SSO integration", "API authentication middleware",
            "session management", "JWT validation",
        ],
    },
    "Information Disclosure": {
        "descriptions": [
            "Sensitive information disclosed in error messages",
            "Debug endpoint exposing internal system details",
            "Directory listing enabled on web server",
        ],
        "components": [
            "error handler", "debug endpoint", "HTTP headers",
            "API response serializer", "log output",
        ],
    },
    "Denial of Service": {
        "descriptions": [
            "Resource exhaustion through malformed request flood",
            "Algorithmic complexity DoS in parsing function",
            "Memory leak triggered by specific input pattern",
        ],
        "components": [
            "request parser", "rate limiter", "connection handler",
            "XML parser", "regex engine",
        ],
    },
    "Path Traversal": {
        "descriptions": [
            "Path traversal allowing access to files outside web root",
            "Directory traversal in file download functionality",
            "Zip slip vulnerability in archive extraction",
        ],
        "components": [
            "file download endpoint", "archive extractor",
            "static file server", "document viewer",
        ],
    },
    "Insecure Deserialization": {
        "descriptions": [
            "Insecure deserialization of user-controlled data",
            "Object injection through untrusted deserialization",
            "Unsafe unmarshaling of serialized objects",
        ],
        "components": [
            "session handler", "message queue consumer",
            "cache layer", "RPC framework",
        ],
    },
    "SSRF": {
        "descriptions": [
            "Server-side request forgery via URL parameter manipulation",
            "SSRF enabling access to internal metadata services",
            "Blind SSRF through webhook URL processing",
        ],
        "components": [
            "webhook handler", "URL preview feature",
            "PDF generator", "image fetcher",
        ],
    },
    "Broken Access Control": {
        "descriptions": [
            "Horizontal access control bypass via IDOR",
            "Missing function-level access control on admin API",
            "Insecure direct object reference in resource endpoint",
        ],
        "components": [
            "REST API endpoint", "file access handler",
            "user management interface", "resource controller",
        ],
    },
}

SEVERITIES = ["low", "medium", "high", "critical"]
CVSS_RANGES = {"low": (0.1, 3.9), "medium": (4.0, 6.9), "high": (7.0, 8.9), "critical": (9.0, 10.0)}

# Named APT profiles with hardcoded attribution
APT_PROFILES: dict[str, dict] = {
    "Midnight Blizzard": {
        "origin": "RU", "type": "nation_state", "motivation": "espionage",
        "sophistication": "advanced",
        "targets": ["technology", "government", "defense"],
    },
    "Cozy Bear": {
        "origin": "RU", "type": "apt", "motivation": "espionage",
        "sophistication": "advanced",
        "targets": ["government", "defense", "healthcare"],
    },
    "Fancy Bear": {
        "origin": "RU", "type": "nation_state", "motivation": "espionage",
        "sophistication": "advanced",
        "targets": ["government", "defense", "energy"],
    },
    "Lazarus Group": {
        "origin": "KP", "type": "nation_state", "motivation": "financial",
        "sophistication": "advanced",
        "targets": ["finance", "technology", "defense"],
    },
    "Equation Group": {
        "origin": "US", "type": "nation_state", "motivation": "espionage",
        "sophistication": "advanced",
        "targets": ["government", "technology", "energy"],
    },
    "Shadow Brokers": {
        "origin": "Unknown", "type": "hacktivist", "motivation": "disruption",
        "sophistication": "high",
        "targets": ["government", "technology"],
    },
    "DarkSide": {
        "origin": "RU", "type": "cybercriminal", "motivation": "financial",
        "sophistication": "high",
        "targets": ["energy", "healthcare", "finance"],
    },
    "REvil": {
        "origin": "RU", "type": "cybercriminal", "motivation": "financial",
        "sophistication": "high",
        "targets": ["technology", "healthcare", "finance"],
    },
    "Sandworm": {
        "origin": "RU", "type": "nation_state", "motivation": "disruption",
        "sophistication": "advanced",
        "targets": ["energy", "government", "technology"],
    },
    "Turla": {
        "origin": "RU", "type": "apt", "motivation": "espionage",
        "sophistication": "advanced",
        "targets": ["government", "defense"],
    },
    "Kimsuky": {
        "origin": "KP", "type": "nation_state", "motivation": "espionage",
        "sophistication": "high",
        "targets": ["government", "defense", "technology"],
    },
    "Charming Kitten": {
        "origin": "IR", "type": "nation_state", "motivation": "espionage",
        "sophistication": "high",
        "targets": ["government", "defense", "technology"],
    },
}

TTPS = [
    "T1566-Phishing",
    "T1059-Command Scripting",
    "T1078-Valid Accounts",
    "T1021-Remote Services",
    "T1071-Application Layer Protocol",
    "T1486-Data Encrypted for Impact",
    "T1053-Scheduled Task",
    "T1027-Obfuscated Files",
    "T1105-Ingress Tool Transfer",
    "T1070-Indicator Removal",
    "T1218-System Binary Proxy Execution",
]


@GeneratorRegistry.register
class VulnerabilityGenerator(AbstractGenerator):
    """Generates Vulnerability entities with type-coherent descriptions and components."""

    GENERATES = EntityType.VULNERABILITY

    def generate(self, count: int, context: GenerationContext) -> list[Vulnerability]:
        faker = context.faker
        vulns: list[Vulnerability] = []

        vuln_types = list(VULN_TEMPLATES.keys())

        for _ in range(count):
            severity = random.choice(SEVERITIES)
            cvss_min, cvss_max = CVSS_RANGES[severity]
            vuln_type = random.choice(vuln_types)
            tmpl = VULN_TEMPLATES[vuln_type]

            patch_available = random.random() < 0.6
            # Correlate status with patch availability
            if patch_available:
                status = random.choice(["mitigated", "resolved", "open"])
            else:
                status = random.choice(["open", "accepted", "open"])

            vuln = Vulnerability(
                name=vuln_type,
                description=random.choice(tmpl["descriptions"]),
                cve_id=f"CVE-{random.randint(2020, 2025)}-{random.randint(10000, 99999)}",
                cvss_score=round(random.uniform(cvss_min, cvss_max), 1),
                severity=severity,
                status=status,
                exploit_available=random.random() < 0.3,
                patch_available=patch_available,
                affected_component=random.choice(tmpl["components"]),
                discovery_date=str(faker.date_between(start_date="-2y", end_date="today")),
                tags=[severity],
            )
            vulns.append(vuln)

        context.store(EntityType.VULNERABILITY, vulns)
        return vulns


@GeneratorRegistry.register
class ThreatActorGenerator(AbstractGenerator):
    """Generates ThreatActor entities with hardcoded attribution for named APTs."""

    GENERATES = EntityType.THREAT_ACTOR

    def generate(self, count: int, context: GenerationContext) -> list[ThreatActor]:
        faker = context.faker
        actors: list[ThreatActor] = []
        apt_names = list(APT_PROFILES.keys())

        for i in range(count):
            if i < len(apt_names):
                actor_name = apt_names[i]
                profile = APT_PROFILES[actor_name]
                origin = profile["origin"]
                actor_type = profile["type"]
                motivation = profile["motivation"]
                sophistication = profile["sophistication"]
                targets = profile["targets"]
                desc = (
                    f"{actor_type.replace('_', ' ').title()} threat actor attributed to "
                    f"{origin}, motivated by {motivation}"
                )
            else:
                actor_name = f"APT-{faker.lexify('????').upper()}"
                actor_type = random.choice(["cybercriminal", "hacktivist", "insider"])
                motivation = random.choice(
                    ["financial", "disruption", "ideological", "retaliation"]
                )
                sophistication = random.choice(["low", "medium", "high"])
                origin = random.choice(["Unknown", "RU", "CN", "IR", "KP"])
                targets = random.sample(
                    ["technology", "healthcare", "finance", "government", "energy", "defense"],
                    k=random.randint(1, 3),
                )
                desc = (
                    f"{actor_type.replace('_', ' ').title()} group with "
                    f"{sophistication} sophistication"
                )

            actor = ThreatActor(
                name=actor_name,
                description=desc,
                actor_type=actor_type,
                sophistication=sophistication,
                motivation=motivation,
                origin_country=origin,
                first_seen=str(faker.date_between(start_date="-5y", end_date="-1y")),
                last_seen=str(faker.date_between(start_date="-1y", end_date="today")),
                aliases=[faker.lexify("???-####").upper() for _ in range(random.randint(1, 3))],
                ttps=random.sample(TTPS, k=random.randint(2, 5)),
                target_industries=targets,
                tags=[actor_type],
            )
            actors.append(actor)

        context.store(EntityType.THREAT_ACTOR, actors)
        return actors
