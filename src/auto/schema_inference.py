"""Schema inference: automatically detect entity types and relationships from raw data."""

from __future__ import annotations

import re

from domain.base import EntityType

# Patterns that hint at entity types based on column names or values
COLUMN_PATTERNS: dict[EntityType, list[str]] = {
    # --- v0.1 original types ---
    EntityType.PERSON: [
        r"(?i)(first.?name|last.?name|employee|email|hire.?date|title|staff)",
    ],
    EntityType.DEPARTMENT: [
        r"(?i)(department|dept|division|business.?unit|team)",
    ],
    EntityType.ROLE: [
        r"(?i)(role.?type|role.?family|access.?level|is.?privileged|role.?id|permissions)",
    ],
    EntityType.SYSTEM: [
        r"(?i)(hostname|ip.?address|server|system|application|service|\bos\b|\bport\b)",
    ],
    EntityType.NETWORK: [
        r"(?i)(cidr|subnet|vlan|network|gateway|dns)",
    ],
    EntityType.VULNERABILITY: [
        r"(?i)(cve|cvss|vulnerability|vuln|exploit|severity)",
    ],
    EntityType.VENDOR: [
        r"(?i)(vendor|supplier|provider|contractor|sla)",
    ],
    EntityType.DATA_ASSET: [
        r"(?i)(data.?asset|database|dataset|classification|retention|encryption)",
    ],
    EntityType.POLICY: [
        r"(?i)(policy|policy.?id|policy.?type|policy.?status|policy.?owner|framework)",
    ],
    EntityType.LOCATION: [
        r"(?i)(location|address|city|state|country|zip|facility)",
    ],
    EntityType.THREAT_ACTOR: [
        r"(?i)(threat.?actor|apt|adversary|attacker|campaign)",
    ],
    EntityType.INCIDENT: [
        r"(?i)(incident|breach|alert|detection|response|forensic)",
    ],
    # --- Enterprise types ---
    EntityType.REGULATION: [
        r"(?i)(regulation.?id|regulation.?category|issuing.?body|regulation.?type"
        r"|compliance.?status|regulatory)",
    ],
    EntityType.CONTROL: [
        r"(?i)(control.?id|control.?type|control.?domain|control.?category"
        r"|control.?status|control.?owner)",
    ],
    EntityType.RISK: [
        r"(?i)(risk.?id|risk.?category|risk.?level|risk.?owner|risk.?status"
        r"|risk.?treatment|inherent.?risk|residual.?risk)",
    ],
    EntityType.THREAT: [
        r"(?i)(threat.?id|threat.?category|threat.?group|threat.?source|threat.?trend)",
    ],
    EntityType.INTEGRATION: [
        r"(?i)(integration.?id|integration.?type|protocol|middleware"
        r"|source.?system|target.?system)",
    ],
    EntityType.DATA_DOMAIN: [
        r"(?i)(domain.?id|domain.?type|domain.?owner|domain.?steward"
        r"|data.?domain|governance.?status)",
    ],
    EntityType.DATA_FLOW: [
        r"(?i)(flow.?id|flow.?type|transfer.?method|data.?flow"
        r"|source.?asset|target.?asset)",
    ],
    EntityType.ORGANIZATIONAL_UNIT: [
        r"(?i)(unit.?id|unit.?type|operating.?model|org.?unit"
        r"|organizational.?unit|unit.?leader)",
    ],
    EntityType.BUSINESS_CAPABILITY: [
        r"(?i)(capability.?id|capability.?level|maturity.?level"
        r"|business.?capability|strategic.?importance)",
    ],
    EntityType.SITE: [
        r"(?i)(site.?id|site.?type|site.?status|building|campus|facility.?type)",
    ],
    EntityType.GEOGRAPHY: [
        r"(?i)(geography.?id|geography.?type|geography|region.?code)",
    ],
    EntityType.JURISDICTION: [
        r"(?i)(jurisdiction.?id|jurisdiction.?type|jurisdiction.?code|governing.?body)",
    ],
    EntityType.PRODUCT_PORTFOLIO: [
        r"(?i)(portfolio.?id|portfolio.?type|product.?portfolio)",
    ],
    EntityType.PRODUCT: [
        r"(?i)(product.?id|product.?type|offering.?type|lifecycle.?stage|product.?name)",
    ],
    EntityType.MARKET_SEGMENT: [
        r"(?i)(segment.?id|segment.?type|market.?segment|segment.?criteria)",
    ],
    EntityType.CUSTOMER: [
        r"(?i)(customer.?id|customer.?type|account.?tier|customer.?name"
        r"|relationship.?status)",
    ],
    EntityType.CONTRACT: [
        r"(?i)(contract.?id|contract.?type|contract.?status|contract.?value"
        r"|contract.?owner)",
    ],
    EntityType.INITIATIVE: [
        r"(?i)(initiative.?id|initiative.?type|initiative.?tier"
        r"|initiative.?category|executive.?sponsor)",
    ],
}

# Patterns for detecting relationships from column names
RELATIONSHIP_COLUMN_PATTERNS = [
    (r"(?i)(department.?id|dept.?id)", "entity_to_department"),
    (r"(?i)(manager.?id|reports.?to|supervisor)", "person_to_manager"),
    (r"(?i)(system.?id|host.?id|server.?id)", "entity_to_system"),
    (r"(?i)(network.?id|subnet.?id|vlan.?id)", "entity_to_network"),
    (r"(?i)(vendor.?id|supplier.?id)", "entity_to_vendor"),
    (r"(?i)(location.?id|site.?id)", "entity_to_location"),
    (r"(?i)(owner.?id|assigned.?to)", "entity_to_person"),
    (r"(?i)(regulation.?id)", "entity_to_regulation"),
    (r"(?i)(control.?id)", "entity_to_control"),
    (r"(?i)(risk.?id)", "entity_to_risk"),
    (r"(?i)(contract.?id)", "entity_to_contract"),
    (r"(?i)(initiative.?id)", "entity_to_initiative"),
    (r"(?i)(product.?id)", "entity_to_product"),
    (r"(?i)(customer.?id)", "entity_to_customer"),
    (r"(?i)(capability.?id)", "entity_to_capability"),
    (r"(?i)(portfolio.?id)", "entity_to_portfolio"),
]


def infer_entity_type(columns: list[str]) -> EntityType | None:
    """Infer the most likely entity type from a list of column names.

    Returns the entity type with the most pattern matches, or None if
    no strong match is found.
    """
    scores: dict[EntityType, int] = {}
    for entity_type, patterns in COLUMN_PATTERNS.items():
        score = 0
        for pattern in patterns:
            for col in columns:
                if re.search(pattern, col):
                    score += 1
        if score > 0:
            scores[entity_type] = score

    if not scores:
        return None
    return max(scores, key=scores.get)  # type: ignore[arg-type]


def infer_relationships(columns: list[str]) -> list[tuple[str, str]]:
    """Detect potential relationship columns from column names.

    Returns list of (column_name, relationship_hint) tuples.
    """
    results: list[tuple[str, str]] = []
    for pattern, hint in RELATIONSHIP_COLUMN_PATTERNS:
        for col in columns:
            if re.search(pattern, col):
                results.append((col, hint))
    return results


def infer_name_field(columns: list[str]) -> str | None:
    """Guess which column is the entity name field."""
    name_patterns = [
        r"(?i)^name$",
        r"(?i)(full.?name|display.?name)",
        r"(?i)(title|label|hostname)",
    ]
    for pattern in name_patterns:
        for col in columns:
            if re.search(pattern, col):
                return col
    return columns[0] if columns else None
