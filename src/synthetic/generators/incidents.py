"""Generator for Incident entities."""

from __future__ import annotations

import random

from domain.base import EntityType
from domain.entities.incident import Incident
from synthetic.base import AbstractGenerator, GenerationContext, GeneratorRegistry

# Incident type → coordinated description, impact, root_cause, detection templates
INCIDENT_TEMPLATES: dict[str, dict] = {
    "data_breach": {
        "descriptions": [
            "Unauthorized access to sensitive data detected in production environment",
            "Exfiltration of customer PII from database via compromised credentials",
            "Data exposure through misconfigured cloud storage bucket",
        ],
        "impacts": [
            "Potential exposure of customer PII affecting regulatory compliance",
            "Data loss impacting customer trust and triggering breach notification",
            "Regulatory liability and potential fines under data protection laws",
        ],
        "root_causes": [
            "Compromised service account with excessive permissions",
            "Misconfigured access controls on cloud storage",
            "Stolen credentials via phishing campaign",
        ],
        "detections": ["siem", "audit", "threat_intel"],
    },
    "malware": {
        "descriptions": [
            "Malware infection detected on multiple endpoints via EDR alert",
            "Trojan horse identified communicating with known C2 infrastructure",
            "Worm propagation across internal network segment",
        ],
        "impacts": [
            "System availability degraded across affected endpoints",
            "Potential lateral movement and data exfiltration risk",
            "Operational disruption requiring endpoint isolation",
        ],
        "root_causes": [
            "Drive-by download from compromised website",
            "Malicious email attachment opened by user",
            "Infected USB device connected to corporate endpoint",
        ],
        "detections": ["edr", "ids", "siem"],
    },
    "phishing": {
        "descriptions": [
            "Targeted phishing campaign impersonating executive leadership",
            "Credential harvesting via spoofed SSO login page",
            "Spear phishing emails delivering malicious payloads to finance team",
        ],
        "impacts": [
            "Multiple accounts compromised requiring password resets",
            "Potential unauthorized access to financial systems",
            "Employee credential exposure and downstream access risk",
        ],
        "root_causes": [
            "Sophisticated social engineering bypassing email filters",
            "Lookalike domain not caught by email gateway",
            "Lack of MFA on targeted accounts",
        ],
        "detections": ["user_report", "siem", "threat_intel"],
    },
    "dos": {
        "descriptions": [
            "Distributed denial of service attack targeting public-facing services",
            "Application-layer DDoS overwhelming API endpoints",
            "Volumetric attack exceeding CDN capacity thresholds",
        ],
        "impacts": [
            "Customer-facing services unavailable for extended period",
            "Revenue loss from service disruption during peak hours",
            "SLA violations affecting customer contracts",
        ],
        "root_causes": [
            "Botnet targeting public IP ranges with UDP flood",
            "Application vulnerability enabling amplification attack",
            "Insufficient DDoS mitigation capacity at edge",
        ],
        "detections": ["ids", "siem", "soar"],
    },
    "insider_threat": {
        "descriptions": [
            "Anomalous data access pattern detected for privileged user",
            "Unauthorized bulk data download by departing employee",
            "Privileged account used to access restricted systems outside business hours",
        ],
        "impacts": [
            "Potential intellectual property theft and competitive harm",
            "Confidential data at risk of unauthorized disclosure",
            "Trust boundary violation requiring investigation",
        ],
        "root_causes": [
            "Disgruntled employee with elevated access privileges",
            "Inadequate access revocation during offboarding",
            "Excessive standing privileges for user role",
        ],
        "detections": ["siem", "audit", "user_report"],
    },
    "ransomware": {
        "descriptions": [
            "Ransomware encryption detected on file servers and network shares",
            "Critical systems encrypted with ransom demand for cryptocurrency",
            "Ransomware deployment following lateral movement from initial foothold",
        ],
        "impacts": [
            "Critical business operations halted pending recovery",
            "Data availability compromised across multiple departments",
            "Potential permanent data loss for unprotected systems",
        ],
        "root_causes": [
            "Initial access via exploited VPN vulnerability",
            "Ransomware-as-a-Service deployed through phishing vector",
            "Unpatched critical vulnerability exploited for initial access",
        ],
        "detections": ["edr", "siem", "user_report"],
    },
    "account_compromise": {
        "descriptions": [
            "Privileged account compromise detected via impossible travel alert",
            "Service account credentials used from unauthorized location",
            "Admin account showing signs of unauthorized access and privilege use",
        ],
        "impacts": [
            "Attacker gained access to administrative controls",
            "Potential for lateral movement and privilege escalation",
            "Sensitive system configurations potentially modified",
        ],
        "root_causes": [
            "Credential stuffing attack using leaked credentials",
            "Brute force attack on exposed authentication endpoint",
            "Session hijacking through XSS vulnerability",
        ],
        "detections": ["siem", "ids", "soar"],
    },
    "supply_chain": {
        "descriptions": [
            "Compromised third-party library detected in production dependencies",
            "Vendor software update containing embedded backdoor",
            "Supply chain compromise via trojanized development tool",
        ],
        "impacts": [
            "Production systems potentially compromised via trusted channel",
            "Widespread exposure through trusted vendor relationship",
            "Integrity of build pipeline and deployed artifacts uncertain",
        ],
        "root_causes": [
            "Compromised vendor build pipeline injecting malicious code",
            "Typosquatted package installed via dependency confusion",
            "Vendor credentials compromised enabling software tampering",
        ],
        "detections": ["threat_intel", "siem", "audit"],
    },
    "misconfiguration": {
        "descriptions": [
            "Security misconfiguration exposing internal services to internet",
            "Cloud resource misconfiguration allowing unauthorized public access",
            "Firewall rule change inadvertently opening restricted network segment",
        ],
        "impacts": [
            "Internal services exposed to unauthorized access",
            "Data potentially accessible to external parties",
            "Compliance violation requiring immediate remediation",
        ],
        "root_causes": [
            "Infrastructure-as-code change deployed without security review",
            "Manual configuration change bypassing change management",
            "Default credentials left on newly provisioned resource",
        ],
        "detections": ["audit", "siem", "ids"],
    },
}

STATUSES = ["open", "investigating", "contained", "resolved", "closed"]


@GeneratorRegistry.register
class IncidentGenerator(AbstractGenerator):
    """Generates Incident entities with type-coherent descriptions."""

    GENERATES = EntityType.INCIDENT

    def generate(self, count: int, context: GenerationContext) -> list[Incident]:
        faker = context.faker
        incidents: list[Incident] = []

        system_ids = context.get_ids(EntityType.SYSTEM)
        actor_ids = context.get_ids(EntityType.THREAT_ACTOR)

        for _ in range(count):
            inc_type = random.choice(list(INCIDENT_TEMPLATES.keys()))
            tmpl = INCIDENT_TEMPLATES[inc_type]
            occurred = faker.date_time_between(start_date="-1y", end_date="now")
            detected = faker.date_time_between(start_date=occurred, end_date="now")

            incident = Incident(
                name=f"{inc_type.replace('_', ' ').title()} — {faker.date()}",
                description=random.choice(tmpl["descriptions"]),
                incident_type=inc_type,
                severity=random.choice(["low", "medium", "high", "critical"]),
                status=random.choice(STATUSES),
                detection_method=random.choice(tmpl["detections"]),
                occurred_at=str(occurred),
                detected_at=str(detected),
                impact_description=random.choice(tmpl["impacts"]),
                root_cause=random.choice(tmpl["root_causes"]),
                affected_system_ids=(
                    random.sample(system_ids, k=min(random.randint(1, 3), len(system_ids)))
                    if system_ids
                    else []
                ),
                threat_actor_id=(
                    random.choice(actor_ids) if actor_ids and random.random() < 0.5 else None
                ),
                tags=[inc_type],
            )
            incidents.append(incident)

        context.store(EntityType.INCIDENT, incidents)
        return incidents
