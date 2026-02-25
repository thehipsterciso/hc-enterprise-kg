"""Relationship domain/range constraints — declares valid (source, rel, target) triples."""

from __future__ import annotations

from domain.base import EntityType, RelationshipType

# Map: RelationshipType → (valid_source_types, valid_target_types)
# Both sets can contain multiple entity types.
RELATIONSHIP_SCHEMA: dict[RelationshipType, tuple[set[EntityType], set[EntityType]]] = {
    # --- Organizational ---
    RelationshipType.WORKS_IN: (
        {EntityType.PERSON},
        {EntityType.DEPARTMENT},
    ),
    RelationshipType.MANAGES: (
        {EntityType.PERSON},
        {EntityType.PERSON, EntityType.DEPARTMENT},
    ),
    RelationshipType.REPORTS_TO: (
        {EntityType.PERSON},
        {EntityType.PERSON},
    ),
    RelationshipType.HAS_ROLE: (
        {EntityType.PERSON},
        {EntityType.ROLE},
    ),
    RelationshipType.MEMBER_OF: (
        {EntityType.PERSON},
        {EntityType.DEPARTMENT, EntityType.ORGANIZATIONAL_UNIT},
    ),
    # --- Technical ---
    RelationshipType.HOSTS: (
        {EntityType.SYSTEM, EntityType.NETWORK},
        {EntityType.SYSTEM, EntityType.DATA_ASSET},
    ),
    RelationshipType.CONNECTS_TO: (
        {EntityType.SYSTEM},
        {EntityType.NETWORK},
    ),
    RelationshipType.DEPENDS_ON: (
        {
            EntityType.SYSTEM,
            EntityType.BUSINESS_CAPABILITY,
            EntityType.INTEGRATION,
            EntityType.ROLE,
        },
        {EntityType.SYSTEM, EntityType.INTEGRATION, EntityType.BUSINESS_CAPABILITY},
    ),
    RelationshipType.STORES: (
        {EntityType.SYSTEM},
        {EntityType.DATA_ASSET},
    ),
    RelationshipType.RUNS_ON: (
        {EntityType.SYSTEM},
        {EntityType.SYSTEM},
    ),
    # --- Security ---
    RelationshipType.GOVERNS: (
        {EntityType.POLICY},
        {EntityType.SYSTEM, EntityType.DATA_ASSET, EntityType.DEPARTMENT},
    ),
    RelationshipType.EXPLOITS: (
        {EntityType.THREAT_ACTOR},
        {EntityType.VULNERABILITY},
    ),
    RelationshipType.TARGETS: (
        {EntityType.THREAT_ACTOR, EntityType.THREAT},
        {EntityType.SYSTEM, EntityType.PERSON, EntityType.DATA_ASSET},
    ),
    RelationshipType.MITIGATES: (
        {EntityType.CONTROL},
        {EntityType.RISK, EntityType.VULNERABILITY, EntityType.THREAT},
    ),
    RelationshipType.AFFECTS: (
        {EntityType.VULNERABILITY, EntityType.INCIDENT},
        {EntityType.SYSTEM, EntityType.DATA_ASSET},
    ),
    # --- Operational ---
    RelationshipType.PROVIDES_SERVICE: (
        {EntityType.SYSTEM, EntityType.VENDOR},
        {EntityType.DEPARTMENT, EntityType.ORGANIZATIONAL_UNIT},
    ),
    RelationshipType.LOCATED_AT: (
        {EntityType.PERSON, EntityType.SYSTEM, EntityType.DEPARTMENT, EntityType.SITE},
        {EntityType.LOCATION, EntityType.SITE, EntityType.GEOGRAPHY},
    ),
    RelationshipType.SUPPLIED_BY: (
        {EntityType.SYSTEM},
        {EntityType.VENDOR},
    ),
    RelationshipType.RESPONSIBLE_FOR: (
        {EntityType.DEPARTMENT, EntityType.PERSON},
        {EntityType.SYSTEM, EntityType.DATA_ASSET},
    ),
    # --- L00: Geography ---
    RelationshipType.LOCATED_IN: (
        {
            EntityType.GEOGRAPHY,
            EntityType.SITE,
            EntityType.LOCATION,
            EntityType.NETWORK,
        },
        {EntityType.GEOGRAPHY},
    ),
    RelationshipType.ISOLATED_FROM: (
        {EntityType.GEOGRAPHY},
        {EntityType.GEOGRAPHY},
    ),
    RelationshipType.ACQUIRED_FROM: (
        {EntityType.GEOGRAPHY, EntityType.SITE},
        {EntityType.GEOGRAPHY},
    ),
    # --- Cross-layer (L00 edge templates) ---
    RelationshipType.SUPPORTS: (
        {
            EntityType.SYSTEM,
            EntityType.BUSINESS_CAPABILITY,
            EntityType.DEPARTMENT,
            EntityType.INTEGRATION,
        },
        {
            EntityType.BUSINESS_CAPABILITY,
            EntityType.PRODUCT,
            EntityType.INITIATIVE,
            EntityType.PRODUCT_PORTFOLIO,
        },
    ),
    RelationshipType.BELONGS_TO: (
        {EntityType.DATA_FLOW, EntityType.PRODUCT, EntityType.SYSTEM},
        {EntityType.DATA_DOMAIN, EntityType.PRODUCT_PORTFOLIO, EntityType.ORGANIZATIONAL_UNIT},
    ),
    RelationshipType.STAFFED_BY: (
        {EntityType.DEPARTMENT, EntityType.ORGANIZATIONAL_UNIT},
        {EntityType.PERSON},
    ),
    RelationshipType.HOSTED_ON: (
        {EntityType.SYSTEM, EntityType.DATA_ASSET, EntityType.NETWORK},
        {EntityType.SYSTEM, EntityType.SITE},
    ),
    RelationshipType.PROCESSES: (
        {EntityType.SYSTEM},
        {EntityType.DATA_ASSET, EntityType.DATA_FLOW},
    ),
    RelationshipType.DELIVERS: (
        {EntityType.SYSTEM, EntityType.VENDOR},
        {EntityType.PRODUCT, EntityType.DATA_ASSET},
    ),
    RelationshipType.SERVES: (
        {
            EntityType.PRODUCT,
            EntityType.SYSTEM,
            EntityType.DEPARTMENT,
            EntityType.ORGANIZATIONAL_UNIT,
        },
        {EntityType.CUSTOMER, EntityType.MARKET_SEGMENT},
    ),
    RelationshipType.MANAGED_BY: (
        {
            EntityType.SYSTEM,
            EntityType.PRODUCT,
            EntityType.CONTRACT,
            EntityType.INTEGRATION,
            EntityType.DATA_ASSET,
            EntityType.NETWORK,
            EntityType.DATA_DOMAIN,
        },
        {EntityType.PERSON, EntityType.DEPARTMENT},
    ),
    RelationshipType.GOVERNED_BY: (
        {
            EntityType.SYSTEM,
            EntityType.DATA_ASSET,
            EntityType.PRODUCT,
            EntityType.NETWORK,
            EntityType.INTEGRATION,
        },
        {EntityType.POLICY, EntityType.REGULATION, EntityType.CONTROL},
    ),
    RelationshipType.IMPACTED_BY: (
        {EntityType.SYSTEM, EntityType.PRODUCT, EntityType.BUSINESS_CAPABILITY},
        {EntityType.INCIDENT, EntityType.RISK, EntityType.THREAT},
    ),
    # --- L01: Compliance & Governance ---
    RelationshipType.REGULATES: (
        {EntityType.REGULATION, EntityType.JURISDICTION},
        {
            EntityType.SYSTEM,
            EntityType.DATA_ASSET,
            EntityType.PRODUCT,
            EntityType.VENDOR,
            EntityType.GEOGRAPHY,
        },
    ),
    RelationshipType.IMPLEMENTS: (
        {EntityType.CONTROL, EntityType.POLICY},
        {EntityType.REGULATION, EntityType.POLICY},
    ),
    RelationshipType.ENFORCES: (
        {EntityType.CONTROL, EntityType.POLICY},
        {EntityType.REGULATION, EntityType.RISK, EntityType.POLICY},
    ),
    RelationshipType.CREATES_RISK: (
        {EntityType.THREAT, EntityType.VULNERABILITY, EntityType.VENDOR},
        {EntityType.RISK},
    ),
    RelationshipType.ADDRESSES: (
        {EntityType.CONTROL, EntityType.INITIATIVE},
        {EntityType.RISK, EntityType.THREAT},
    ),
    RelationshipType.AUDITED_BY: (
        {EntityType.SYSTEM, EntityType.VENDOR, EntityType.CONTROL},
        {EntityType.PERSON, EntityType.DEPARTMENT},
    ),
    RelationshipType.SUBJECT_TO: (
        {
            EntityType.SYSTEM,
            EntityType.VENDOR,
            EntityType.DATA_ASSET,
            EntityType.PRODUCT,
            EntityType.JURISDICTION,
            EntityType.SITE,
            EntityType.REGULATION,
            EntityType.POLICY,
            EntityType.NETWORK,
            EntityType.INTEGRATION,
            EntityType.DATA_DOMAIN,
            EntityType.CUSTOMER,
            EntityType.DEPARTMENT,
        },
        {EntityType.REGULATION, EntityType.JURISDICTION, EntityType.POLICY, EntityType.CONTROL},
    ),
    # --- L02: Technology & Systems ---
    RelationshipType.INTEGRATES_WITH: (
        {EntityType.SYSTEM, EntityType.INTEGRATION},
        {EntityType.SYSTEM},
    ),
    RelationshipType.AUTHENTICATES_VIA: (
        {EntityType.SYSTEM, EntityType.PERSON},
        {EntityType.SYSTEM, EntityType.INTEGRATION},
    ),
    RelationshipType.FEEDS_DATA_TO: (
        {EntityType.SYSTEM, EntityType.DATA_ASSET},
        {EntityType.SYSTEM, EntityType.DATA_ASSET},
    ),
    # --- L03: Data Assets ---
    RelationshipType.CONTAINS: (
        {
            EntityType.DATA_DOMAIN,
            EntityType.SYSTEM,
            EntityType.MARKET_SEGMENT,
            EntityType.PRODUCT_PORTFOLIO,
        },
        {EntityType.DATA_ASSET, EntityType.DATA_FLOW, EntityType.CUSTOMER, EntityType.PRODUCT},
    ),
    RelationshipType.FLOWS_TO: (
        {EntityType.DATA_FLOW, EntityType.DATA_ASSET},
        {EntityType.SYSTEM, EntityType.DATA_ASSET},
    ),
    RelationshipType.ORIGINATES_FROM: (
        {EntityType.DATA_FLOW, EntityType.DATA_ASSET},
        {EntityType.SYSTEM, EntityType.VENDOR},
    ),
    RelationshipType.CLASSIFIED_AS: (
        {EntityType.DATA_ASSET},
        {EntityType.DATA_DOMAIN},
    ),
    # --- L04-L05: Organization & People ---
    RelationshipType.APPLIES_TO: (
        {EntityType.CONTROL, EntityType.POLICY, EntityType.REGULATION},
        {EntityType.SYSTEM, EntityType.DATA_ASSET, EntityType.DEPARTMENT, EntityType.VENDOR},
    ),
    # --- L06: Business Capabilities ---
    RelationshipType.ENABLES: (
        {EntityType.SYSTEM, EntityType.PRODUCT},
        {EntityType.BUSINESS_CAPABILITY},
    ),
    RelationshipType.REALIZED_BY: (
        {EntityType.BUSINESS_CAPABILITY},
        {EntityType.SYSTEM, EntityType.PRODUCT, EntityType.PERSON},
    ),
    # --- L08-L10: Commercial ---
    RelationshipType.BUYS: (
        {EntityType.CUSTOMER},
        {EntityType.PRODUCT, EntityType.PRODUCT_PORTFOLIO},
    ),
    RelationshipType.CONTRACTS_WITH: (
        {EntityType.CONTRACT},
        {EntityType.VENDOR},
    ),
    RelationshipType.HOLDS: (
        {EntityType.CUSTOMER, EntityType.VENDOR},
        {EntityType.CONTRACT},
    ),
    RelationshipType.PROVIDES: (
        {EntityType.VENDOR},
        {EntityType.SYSTEM, EntityType.PRODUCT, EntityType.DATA_ASSET},
    ),
    RelationshipType.SUPPLIES: (
        {EntityType.VENDOR},
        {EntityType.SYSTEM, EntityType.PRODUCT},
    ),
    # --- L11: Strategic Initiatives ---
    RelationshipType.IMPACTS: (
        {EntityType.INITIATIVE},
        {EntityType.SYSTEM, EntityType.PRODUCT, EntityType.BUSINESS_CAPABILITY, EntityType.RISK},
    ),
    RelationshipType.DRIVES: (
        {EntityType.INITIATIVE},
        {EntityType.PRODUCT, EntityType.BUSINESS_CAPABILITY, EntityType.CONTROL},
    ),
    RelationshipType.FUNDED_BY: (
        {EntityType.INITIATIVE},
        {EntityType.DEPARTMENT, EntityType.ORGANIZATIONAL_UNIT},
    ),
}


def validate_relationship(
    relationship_type: RelationshipType,
    source_type: EntityType,
    target_type: EntityType,
) -> tuple[bool, str]:
    """Check if a relationship is valid per the schema.

    Returns (True, "") if valid, or (False, reason) if not.
    """
    schema = RELATIONSHIP_SCHEMA.get(relationship_type)
    if schema is None:
        return True, ""  # No constraint defined — allow by default

    valid_sources, valid_targets = schema
    if source_type not in valid_sources:
        return False, (
            f"{relationship_type.value}: source type '{source_type.value}' not in "
            f"allowed sources {sorted(s.value for s in valid_sources)}"
        )
    if target_type not in valid_targets:
        return False, (
            f"{relationship_type.value}: target type '{target_type.value}' not in "
            f"allowed targets {sorted(t.value for t in valid_targets)}"
        )
    return True, ""
