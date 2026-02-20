"""Generator for System entities."""

from __future__ import annotations

import random

from domain.base import EntityType
from domain.entities.system import System
from synthetic.base import AbstractGenerator, GenerationContext, GeneratorRegistry

# Coordinated system templates: name → {type, os_choices, tech_stacks, ports}
SYSTEM_TEMPLATES = [
    {
        "name": "ERP System",
        "type": "application",
        "os": ["Linux", "Windows Server 2022"],
        "stacks": [["java", "spring", "oracle"], ["java", "spring", "postgresql"]],
        "ports": [443, 8080],
        "criticality": "critical",
    },
    {
        "name": "CRM Platform",
        "type": "saas",
        "os": ["Linux"],
        "stacks": [["python", "django", "postgresql"], ["java", "spring", "mysql"]],
        "ports": [443],
        "criticality": "high",
    },
    {
        "name": "HR Portal",
        "type": "application",
        "os": ["Linux", "Windows Server 2022"],
        "stacks": [[".net", "sql-server", "iis"], ["python", "django", "postgresql"]],
        "ports": [443, 8443],
        "criticality": "high",
    },
    {
        "name": "Email Server",
        "type": "server",
        "os": ["Windows Server 2022", "Linux"],
        "stacks": [["exchange", "active-directory"], ["postfix", "dovecot", "linux"]],
        "ports": [25, 443, 993],
        "criticality": "critical",
    },
    {
        "name": "File Server",
        "type": "server",
        "os": ["Windows Server 2022", "Linux"],
        "stacks": [["smb", "ntfs", "windows"], ["nfs", "zfs", "linux"]],
        "ports": [445, 139],
        "criticality": "medium",
    },
    {
        "name": "Database Server",
        "type": "database",
        "os": ["Linux", "RHEL 9"],
        "stacks": [["postgresql", "pgbouncer"], ["mysql", "percona"], ["oracle", "asm"]],
        "ports": [5432, 3306],
        "criticality": "critical",
    },
    {
        "name": "Web Application",
        "type": "application",
        "os": ["Linux", "Ubuntu 22.04"],
        "stacks": [["node", "react", "mongodb"], ["python", "django", "postgresql"]],
        "ports": [80, 443],
        "criticality": "high",
    },
    {
        "name": "API Gateway",
        "type": "appliance",
        "os": ["Linux"],
        "stacks": [["kong", "nginx", "lua"], ["envoy", "grpc", "go"]],
        "ports": [443, 8443],
        "criticality": "critical",
    },
    {
        "name": "Load Balancer",
        "type": "appliance",
        "os": ["Linux"],
        "stacks": [["haproxy", "keepalived"], ["nginx", "lua"]],
        "ports": [80, 443],
        "criticality": "critical",
    },
    {
        "name": "DNS Server",
        "type": "server",
        "os": ["Linux", "RHEL 9"],
        "stacks": [["bind9", "dnssec"], ["unbound", "nsd"]],
        "ports": [53],
        "criticality": "critical",
    },
    {
        "name": "LDAP/AD Server",
        "type": "server",
        "os": ["Windows Server 2022"],
        "stacks": [["active-directory", "kerberos", "ldap"]],
        "ports": [389, 636, 88],
        "criticality": "critical",
    },
    {
        "name": "Monitoring System",
        "type": "application",
        "os": ["Linux", "Ubuntu 22.04"],
        "stacks": [["prometheus", "grafana", "alertmanager"], ["datadog", "agent"]],
        "ports": [9090, 3000],
        "criticality": "high",
    },
    {
        "name": "Log Aggregator",
        "type": "application",
        "os": ["Linux"],
        "stacks": [["elasticsearch", "kibana", "logstash"], ["splunk", "forwarder"]],
        "ports": [9200, 5601],
        "criticality": "high",
    },
    {
        "name": "CI/CD Pipeline",
        "type": "application",
        "os": ["Linux"],
        "stacks": [["jenkins", "groovy", "docker"], ["gitlab-ci", "docker", "kubernetes"]],
        "ports": [8080, 443],
        "criticality": "high",
    },
    {
        "name": "Code Repository",
        "type": "saas",
        "os": ["Linux"],
        "stacks": [["git", "gitlab", "ruby"], ["git", "github", "go"]],
        "ports": [443, 22],
        "criticality": "high",
    },
    {
        "name": "Wiki/Docs",
        "type": "saas",
        "os": ["Linux"],
        "stacks": [["confluence", "java"], ["notion", "node"]],
        "ports": [443],
        "criticality": "low",
    },
    {
        "name": "Chat Platform",
        "type": "saas",
        "os": ["Linux"],
        "stacks": [["slack", "electron"], ["teams", "azure"]],
        "ports": [443],
        "criticality": "medium",
    },
    {
        "name": "VPN Gateway",
        "type": "appliance",
        "os": ["Linux"],
        "stacks": [["openvpn", "pki"], ["wireguard", "ipsec"]],
        "ports": [443, 1194],
        "criticality": "critical",
    },
    {
        "name": "Firewall",
        "type": "appliance",
        "os": ["Linux"],
        "stacks": [["palo-alto", "pan-os"], ["fortinet", "fortigate"]],
        "ports": [443],
        "criticality": "critical",
    },
    {
        "name": "IDS/IPS",
        "type": "appliance",
        "os": ["Linux"],
        "stacks": [["suricata", "zeek"], ["snort", "barnyard"]],
        "ports": [443],
        "criticality": "high",
    },
    {
        "name": "SIEM",
        "type": "application",
        "os": ["Linux", "RHEL 9"],
        "stacks": [["splunk", "enterprise-security"], ["elastic", "security", "kibana"]],
        "ports": [8089, 443],
        "criticality": "critical",
    },
    {
        "name": "Backup Server",
        "type": "server",
        "os": ["Linux", "Windows Server 2022"],
        "stacks": [["veeam", "sql-server"], ["bacula", "postgresql"]],
        "ports": [9392, 443],
        "criticality": "high",
    },
    {
        "name": "Data Warehouse",
        "type": "database",
        "os": ["Linux"],
        "stacks": [["snowflake", "sql"], ["redshift", "postgresql"], ["bigquery", "sql"]],
        "ports": [443, 5439],
        "criticality": "high",
    },
    {
        "name": "Analytics Platform",
        "type": "application",
        "os": ["Linux"],
        "stacks": [["tableau", "python"], ["powerbi", "azure"], ["looker", "sql"]],
        "ports": [443, 8088],
        "criticality": "medium",
    },
    {
        "name": "SSO Provider",
        "type": "saas",
        "os": ["Linux"],
        "stacks": [["okta", "saml", "oidc"], ["azure-ad", "oauth2"]],
        "ports": [443],
        "criticality": "critical",
    },
]

# Overflow system name patterns by type
OVERFLOW_NAMES: dict[str, list[str]] = {
    "server": [
        "File Archive Server",
        "Print Server",
        "FTP Server",
        "NTP Server",
        "Build Server",
        "License Server",
        "Proxy Server",
    ],
    "application": [
        "Inventory Management",
        "Workflow Engine",
        "Notification Service",
        "Reporting Engine",
        "Scheduling System",
        "Document Management",
        "Asset Tracker",
        "Audit Platform",
    ],
    "database": [
        "Reporting Database",
        "Analytics DB",
        "Archive Database",
        "Staging Database",
        "Replica Database",
    ],
    "saas": [
        "Project Management SaaS",
        "Design Tool",
        "Survey Platform",
        "Expense Management",
        "Travel Booking",
        "E-Signature Platform",
    ],
    "workstation": [
        "Developer Workstation",
        "Admin Workstation",
        "Kiosk Terminal",
        "Lab Workstation",
        "Trading Terminal",
    ],
    "appliance": [
        "WAF Appliance",
        "DDoS Mitigation",
        "Email Gateway",
        "Web Proxy",
        "Network TAP",
    ],
    "vm": [
        "Test VM",
        "Dev VM",
        "Sandbox VM",
        "Build VM",
        "Staging VM",
    ],
}

ENVIRONMENTS = ["production", "staging", "development", "test", "dr"]
SYSTEM_TYPES = ["server", "application", "database", "saas", "workstation", "appliance", "vm"]


@GeneratorRegistry.register
class SystemGenerator(AbstractGenerator):
    """Generates System entities with coherent type/OS/stack/port coordination."""

    GENERATES = EntityType.SYSTEM

    def generate(self, count: int, context: GenerationContext) -> list[System]:
        faker = context.faker
        systems: list[System] = []

        for i in range(count):
            if i < len(SYSTEM_TEMPLATES):
                tmpl = SYSTEM_TEMPLATES[i]
                name = tmpl["name"]
                sys_type = tmpl["type"]
                os_choice = random.choice(tmpl["os"])
                stack = random.choice(tmpl["stacks"])
                ports = tmpl["ports"]
                criticality = tmpl["criticality"]
            else:
                sys_type = random.choice(SYSTEM_TYPES)
                overflow = OVERFLOW_NAMES.get(sys_type, ["Service"])
                name = random.choice(overflow)
                # Assign coherent OS based on type
                if sys_type in ("appliance", "vm"):
                    os_choice = random.choice(["Linux", "Ubuntu 22.04", "RHEL 9"])
                elif sys_type == "workstation":
                    os_choice = random.choice(["Windows 11", "macOS"])
                elif sys_type == "saas":
                    os_choice = "Linux"
                else:
                    os_choice = random.choice(
                        ["Linux", "Ubuntu 22.04", "RHEL 9", "Windows Server 2022"]
                    )
                stack = random.choice(
                    [
                        ["python", "flask", "postgresql"],
                        ["java", "spring", "mysql"],
                        ["node", "express", "mongodb"],
                        ["go", "grpc", "redis"],
                        [".net", "sql-server", "iis"],
                    ]
                )
                ports = random.sample([22, 80, 443, 3306, 5432, 8080, 8443], k=random.randint(1, 3))
                criticality = random.choice(["low", "medium", "high", "critical"])

            hostname = f"{name.lower().replace(' ', '-').replace('/', '-')[:20]}-{i:03d}"

            system = System(
                name=name,
                description=f"{name} — {sys_type} running {os_choice}",
                system_type=sys_type,
                hostname=hostname,
                ip_address=faker.ipv4_private(),
                os=os_choice,
                version=f"{random.randint(1, 12)}.{random.randint(0, 9)}.{random.randint(0, 20)}",
                environment=random.choice(ENVIRONMENTS),
                criticality=criticality,
                is_internet_facing=random.random() < 0.2,
                ports=ports,
                technologies=stack,
                tags=[sys_type],
            )
            systems.append(system)

        context.store(EntityType.SYSTEM, systems)
        return systems
