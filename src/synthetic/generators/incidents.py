"""Generator for Incident entities."""

from __future__ import annotations

import random

from domain.base import EntityType
from domain.entities.incident import Incident
from synthetic.base import AbstractGenerator, GenerationContext, GeneratorRegistry

INCIDENT_TYPES = [
    "data_breach", "malware", "phishing", "dos", "insider_threat",
    "ransomware", "account_compromise", "supply_chain", "misconfiguration",
]
DETECTION_METHODS = ["siem", "ids", "user_report", "threat_intel", "audit", "edr", "soar"]
STATUSES = ["open", "investigating", "contained", "resolved", "closed"]


@GeneratorRegistry.register
class IncidentGenerator(AbstractGenerator):
    """Generates Incident entities."""

    GENERATES = EntityType.INCIDENT

    def generate(self, count: int, context: GenerationContext) -> list[Incident]:
        faker = context.faker
        incidents: list[Incident] = []

        system_ids = context.get_ids(EntityType.SYSTEM)
        actor_ids = context.get_ids(EntityType.THREAT_ACTOR)

        for _ in range(count):
            inc_type = random.choice(INCIDENT_TYPES)
            occurred = faker.date_time_between(start_date="-1y", end_date="now")
            detected = faker.date_time_between(start_date=occurred, end_date="now")

            incident = Incident(
                name=f"{inc_type.replace('_', ' ').title()} Incident - {faker.date()}",
                description=faker.paragraph(nb_sentences=2),
                incident_type=inc_type,
                severity=random.choice(["low", "medium", "high", "critical"]),
                status=random.choice(STATUSES),
                detection_method=random.choice(DETECTION_METHODS),
                occurred_at=str(occurred),
                detected_at=str(detected),
                impact_description=faker.sentence(nb_words=10),
                root_cause=faker.sentence(nb_words=8),
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
