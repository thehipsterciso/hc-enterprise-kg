"""Generator for System entities."""

from __future__ import annotations

import random

from domain.base import EntityType
from domain.entities.system import System
from synthetic.base import AbstractGenerator, GenerationContext, GeneratorRegistry

SYSTEM_TYPES = ["server", "application", "database", "saas", "workstation", "appliance", "vm"]
OS_CHOICES = ["Linux", "Windows Server 2022", "Ubuntu 22.04", "RHEL 9", "Windows 11", "macOS"]
ENVIRONMENTS = ["production", "staging", "development", "test", "dr"]
CRITICALITY = ["low", "medium", "high", "critical"]
TECH_STACKS = [
    ["python", "django", "postgresql"],
    ["java", "spring", "mysql"],
    ["node", "react", "mongodb"],
    ["go", "grpc", "redis"],
    [".net", "sql-server", "iis"],
    ["ruby", "rails", "postgresql"],
]
APP_NAMES = [
    "ERP System", "CRM Platform", "HR Portal", "Email Server", "File Server",
    "Database Server", "Web Application", "API Gateway", "Load Balancer",
    "DNS Server", "LDAP/AD Server", "Monitoring System", "Log Aggregator",
    "CI/CD Pipeline", "Code Repository", "Wiki/Docs", "Chat Platform",
    "VPN Gateway", "Firewall", "IDS/IPS", "SIEM", "Backup Server",
    "Data Warehouse", "Analytics Platform", "SSO Provider",
]


@GeneratorRegistry.register
class SystemGenerator(AbstractGenerator):
    """Generates System entities."""

    GENERATES = EntityType.SYSTEM

    def generate(self, count: int, context: GenerationContext) -> list[System]:
        faker = context.faker
        systems: list[System] = []

        for i in range(count):
            sys_type = random.choice(SYSTEM_TYPES)
            hostname = f"{faker.word()}-{sys_type[:3]}-{i:03d}"
            app_name = random.choice(APP_NAMES) if i < len(APP_NAMES) else f"{faker.word().title()} Service"

            system = System(
                name=app_name,
                description=f"{app_name} ({sys_type})",
                system_type=sys_type,
                hostname=hostname,
                ip_address=faker.ipv4_private(),
                os=random.choice(OS_CHOICES),
                version=f"{random.randint(1, 12)}.{random.randint(0, 9)}.{random.randint(0, 20)}",
                environment=random.choice(ENVIRONMENTS),
                criticality=random.choice(CRITICALITY),
                is_internet_facing=random.random() < 0.2,
                ports=random.sample([22, 80, 443, 3306, 5432, 8080, 8443, 6379, 27017], k=random.randint(1, 4)),
                technologies=random.choice(TECH_STACKS),
                tags=[sys_type],
            )
            systems.append(system)

        context.store(EntityType.SYSTEM, systems)
        return systems
