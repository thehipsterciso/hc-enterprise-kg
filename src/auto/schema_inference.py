"""Schema inference: automatically detect entity types and relationships from raw data."""

from __future__ import annotations

import re

from domain.base import EntityType

# Patterns that hint at entity types based on column names or values
COLUMN_PATTERNS: dict[EntityType, list[str]] = {
    EntityType.PERSON: [
        r"(?i)(first.?name|last.?name|employee|email|hire.?date|title|staff)",
    ],
    EntityType.DEPARTMENT: [
        r"(?i)(department|dept|division|business.?unit|team)",
    ],
    EntityType.SYSTEM: [
        r"(?i)(hostname|ip.?address|server|system|application|service|os|port)",
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
        r"(?i)(policy|control|framework|compliance|regulation)",
    ],
    EntityType.LOCATION: [
        r"(?i)(location|address|city|state|country|zip|facility|site)",
    ],
    EntityType.THREAT_ACTOR: [
        r"(?i)(threat.?actor|apt|adversary|attacker|campaign)",
    ],
    EntityType.INCIDENT: [
        r"(?i)(incident|breach|alert|detection|response|forensic)",
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
