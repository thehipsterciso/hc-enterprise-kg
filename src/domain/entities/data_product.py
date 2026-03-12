"""DataProduct entity — a curated, self-describing unit of data for consumption.

Covers CDAIO Module 8 (Developing Data Products and the Business of Data)
and Module 7 (Data Monetization / Infonomics). A DataProduct is how data
is packaged, governed, and delivered to consumers — the output side of
the data supply chain.

Attribute groups
----------------
1. Identity & Classification (~10 attrs)
2. Ownership & Accountability (~6 attrs)
3. Data Characteristics (~8 attrs)
4. Access & Distribution (~8 attrs)
5. Quality & Contracts (~8 attrs)
6. Monetization & Value (~8 attrs)
7. Compliance & Privacy (~6 attrs)
8. FAIR Compliance (~4 attrs)
9. Dependencies & Relationships (~5 attrs)
10. Temporal & Provenance

Framework provenance: Data Mesh (Dehghani), Infonomics (Laney),
FAIR Data Principles (Wilkinson et al.), Data Product Canvas,
DCAM 2.2, DMBOK2.
"""

from __future__ import annotations

from typing import ClassVar, Literal

from pydantic import BaseModel, Field

from domain.base import BaseEntity, EntityType
from domain.shared import (
    ProvenanceAndConfidence,
    TemporalAndVersioning,
)

# ===========================================================================
# Group 2: Ownership & Accountability — sub-models
# ===========================================================================


class DataProductSLA(BaseModel):
    """Service-level agreement for the data product."""

    availability_pct: float | None = None
    freshness_target: str = ""  # e.g. "< 15 minutes", "daily by 06:00 UTC"
    latency_target_ms: int | None = None
    support_hours: str = ""  # e.g. "24x7", "business hours", "best effort"


# ===========================================================================
# Group 5: Quality & Contracts — sub-models
# ===========================================================================


class QualityDimensions(BaseModel):
    """Multi-dimensional data quality assessment (Data Mesh SLA pattern)."""

    completeness_pct: float | None = None
    accuracy_pct: float | None = None
    timeliness_score: float | None = None
    consistency_score: float | None = None
    uniqueness_pct: float | None = None


# ===========================================================================
# DataProduct entity
# ===========================================================================


class DataProduct(BaseEntity):
    """A curated, self-describing unit of data for consumption.

    Represents the output side of the data supply chain — how data is
    packaged, governed, and delivered to consumers. Modeled after Data
    Mesh domain-owned data products with Infonomics valuation, FAIR
    compliance scoring, and Data Product Canvas patterns.
    """

    ENTITY_TYPE: ClassVar[EntityType] = EntityType.DATA_PRODUCT
    entity_type: Literal[EntityType.DATA_PRODUCT] = EntityType.DATA_PRODUCT

    # --- Group 1: Identity & Classification ---
    data_product_id: str = ""
    data_product_type: str = ""
    # dataset, api, stream, report, dashboard, feature_store,
    # ml_feature, derived_metric
    domain: str = ""  # Reference to DataDomain entity
    functional_area: str = ""
    maturity: str = ""  # ideation, development, beta, ga, deprecated, retired
    visibility: str = ""  # internal, partner, public
    data_product_tier: str = ""  # bronze, silver, gold, platinum

    # --- Group 2: Ownership & Accountability ---
    product_owner_role: str = ""
    technical_steward: str = ""
    domain_owner: str = ""
    support_team: str = ""
    escalation_path: str = ""
    data_product_sla: DataProductSLA | None = None

    # --- Group 3: Data Characteristics ---
    source_data_assets: list[str] = Field(default_factory=list)  # Data asset IDs
    update_frequency: str = ""
    # real_time, near_real_time, hourly, daily, weekly, monthly, on_demand
    data_format: str = ""  # json, parquet, avro, csv, protobuf, graphql, rest_api, grpc
    schema_definition_url: str = ""
    schema_version: str = ""
    volume_gb: float | None = None
    row_count: int | None = None
    quality_score: float | None = None  # 0.0 - 1.0

    # --- Group 4: Access & Distribution ---
    access_protocol: str = ""  # api, file_share, streaming, query, sdk, webhook
    endpoint_url: str = ""
    authentication_method: str = ""
    consumer_count: int | None = None
    consumer_list: list[str] = Field(default_factory=list)  # Department/system IDs
    rate_limit_rps: int | None = None
    throttling_policy: str = ""
    self_service_enabled: bool = False

    # --- Group 5: Quality & Contracts ---
    quality_dimensions: QualityDimensions | None = None
    quality_monitoring_enabled: bool = False
    data_contract_version: str = ""
    data_contract_url: str = ""
    breaking_change_policy: str = ""  # versioned, backward_compatible, notify_consumers
    last_quality_check: str = ""
    quality_trend: str = ""  # improving, stable, declining
    incidents_last_90_days: int | None = None

    # --- Group 6: Monetization & Value (Module 7 Infonomics) ---
    monetization_status: str = ""
    # not_monetized, internal_value, direct_revenue,
    # indirect_revenue, cost_avoidance
    economic_value_method: str = ""  # cost, market, income, utility, none
    estimated_annual_value: float | None = None
    currency: str = "USD"
    cost_to_produce: float | None = None
    margin_pct: float | None = None
    value_confidence: str = ""  # demonstrated, modeled, estimated, aspirational
    revenue_attribution_model: str = ""

    # --- Group 7: Compliance & Privacy ---
    contains_pii: bool = False
    contains_phi: bool = False
    contains_financial: bool = False
    data_classification: str = ""  # public, internal, confidential, restricted
    retention_policy: str = ""
    cross_border_restrictions: list[str] = Field(default_factory=list)  # Jurisdiction IDs

    # --- Group 8: FAIR Compliance (FAIR Data Principles) ---
    findable_score: float | None = None  # 0.0 - 1.0
    accessible_score: float | None = None  # 0.0 - 1.0
    interoperable_score: float | None = None  # 0.0 - 1.0
    reusable_score: float | None = None  # 0.0 - 1.0

    # --- Group 9: Dependencies & Relationships ---
    source_systems: list[str] = Field(default_factory=list)
    consuming_systems: list[str] = Field(default_factory=list)
    upstream_pipelines: list[str] = Field(default_factory=list)
    downstream_data_products: list[str] = Field(default_factory=list)
    serving_products: list[str] = Field(default_factory=list)  # Product entity refs

    # --- Group 10: Temporal & Provenance ---
    temporal_and_versioning: TemporalAndVersioning = Field(default_factory=TemporalAndVersioning)
    provenance_and_confidence: ProvenanceAndConfidence = Field(
        default_factory=ProvenanceAndConfidence
    )
