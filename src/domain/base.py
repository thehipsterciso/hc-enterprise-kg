"""Core domain model: base types, enums, and mixins for the knowledge graph."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from enum import StrEnum
from typing import Any, ClassVar

from pydantic import BaseModel, ConfigDict, Field


class EntityType(StrEnum):
    """Enumeration of all entity types in the knowledge graph.

    Original v0.1 types are listed first for backward compatibility.
    Enterprise ontology types (L00-L11) follow, grouped by build layer.
    """

    # --- v0.1 original types ---
    PERSON = "person"
    DEPARTMENT = "department"
    ROLE = "role"
    SYSTEM = "system"
    NETWORK = "network"
    DATA_ASSET = "data_asset"
    POLICY = "policy"
    VENDOR = "vendor"
    LOCATION = "location"
    VULNERABILITY = "vulnerability"
    THREAT_ACTOR = "threat_actor"
    INCIDENT = "incident"

    # --- L01: Compliance & Governance (from schema L9) ---
    REGULATION = "regulation"
    CONTROL = "control"
    RISK = "risk"
    THREAT = "threat"

    # --- L02: Technology & Systems (from schema L4) ---
    INTEGRATION = "integration"

    # --- L03: Data Assets (from schema L5) ---
    DATA_DOMAIN = "data_domain"
    DATA_FLOW = "data_flow"

    # --- L04: Organization (from schema L1) ---
    ORGANIZATIONAL_UNIT = "organizational_unit"

    # --- L06: Business Capabilities (from schema L0) ---
    BUSINESS_CAPABILITY = "business_capability"

    # --- L07: Locations & Facilities (from schema L3) ---
    SITE = "site"
    GEOGRAPHY = "geography"
    JURISDICTION = "jurisdiction"

    # --- L08: Products & Services (from schema L6) ---
    PRODUCT_PORTFOLIO = "product_portfolio"
    PRODUCT = "product"

    # --- L09: Customers & Markets (from schema L7) ---
    MARKET_SEGMENT = "market_segment"
    CUSTOMER = "customer"

    # --- L10: Vendors & Partners (from schema L8) ---
    CONTRACT = "contract"

    # --- L11: Strategic Initiatives (from schema L10) ---
    INITIATIVE = "initiative"


class RelationshipType(StrEnum):
    """Enumeration of all relationship types in the knowledge graph.

    Original v0.1 types are listed first. Enterprise ontology cross-layer
    edge types follow, derived from L00 edge templates and per-layer schemas.
    """

    # --- v0.1 original types ---
    # Organizational
    WORKS_IN = "works_in"
    MANAGES = "manages"
    REPORTS_TO = "reports_to"
    HAS_ROLE = "has_role"
    MEMBER_OF = "member_of"
    # Technical
    HOSTS = "hosts"
    CONNECTS_TO = "connects_to"
    DEPENDS_ON = "depends_on"
    STORES = "stores"
    RUNS_ON = "runs_on"
    # Security
    GOVERNS = "governs"
    EXPLOITS = "exploits"
    TARGETS = "targets"
    MITIGATES = "mitigates"
    AFFECTS = "affects"
    # Operational
    PROVIDES_SERVICE = "provides_service"
    LOCATED_AT = "located_at"
    SUPPLIED_BY = "supplied_by"
    RESPONSIBLE_FOR = "responsible_for"

    # --- Cross-layer edge types (from L00 edge templates) ---
    SUPPORTS = "supports"
    BELONGS_TO = "belongs_to"
    STAFFED_BY = "staffed_by"
    HOSTED_ON = "hosted_on"
    PROCESSES = "processes"
    DELIVERS = "delivers"
    SERVES = "serves"
    MANAGED_BY = "managed_by"
    GOVERNED_BY = "governed_by"
    IMPACTED_BY = "impacted_by"

    # --- L01: Compliance & Governance ---
    REGULATES = "regulates"
    IMPLEMENTS = "implements"
    ENFORCES = "enforces"
    CREATES_RISK = "creates_risk"
    ADDRESSES = "addresses"
    AUDITED_BY = "audited_by"
    SUBJECT_TO = "subject_to"

    # --- L02: Technology & Systems ---
    INTEGRATES_WITH = "integrates_with"
    AUTHENTICATES_VIA = "authenticates_via"
    FEEDS_DATA_TO = "feeds_data_to"

    # --- L03: Data Assets ---
    CONTAINS = "contains"
    FLOWS_TO = "flows_to"
    ORIGINATES_FROM = "originates_from"
    CLASSIFIED_AS = "classified_as"

    # --- L06: Business Capabilities ---
    ENABLES = "enables"
    REALIZED_BY = "realized_by"

    # --- L08-L10: Commercial layer ---
    BUYS = "buys"
    CONTRACTS_WITH = "contracts_with"
    HOLDS = "holds"
    PROVIDES = "provides"
    SUPPLIES = "supplies"

    # --- L11: Strategic Initiatives ---
    IMPACTS = "impacts"
    DRIVES = "drives"
    FUNDED_BY = "funded_by"

    # --- L00: Geography ---
    LOCATED_IN = "located_in"
    ISOLATED_FROM = "isolated_from"
    ACQUIRED_FROM = "acquired_from"


class TemporalMixin(BaseModel):
    """Mixin that adds temporal tracking to any entity or relationship."""

    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    valid_from: datetime | None = None
    valid_until: datetime | None = None
    version: int = 1


class BaseEntity(TemporalMixin):
    """Abstract base for all knowledge graph entities."""

    model_config = ConfigDict(extra="allow")

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    entity_type: EntityType
    name: str
    description: str = ""
    tags: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)

    ENTITY_TYPE: ClassVar[EntityType]


class BaseRelationship(TemporalMixin):
    """Abstract base for all knowledge graph relationships."""

    model_config = ConfigDict(extra="allow")

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    relationship_type: RelationshipType
    source_id: str
    target_id: str
    weight: float = 1.0
    confidence: float = 1.0
    properties: dict[str, Any] = Field(default_factory=dict)
