"""MarketSegment entity — strategic market grouping.

A market segment is a defined portion of the addressable market, grouped
by industry vertical, geography, size, behavior, or regulatory
characteristics. Segments are hierarchical (Market → Segment →
Sub-Segment).

Attribute groups
----------------
1. Identity & Hierarchy (~7 attrs)
2. Ownership (~2 attrs)
3. Market Sizing & Performance (~8 attrs)
4. Dependencies & Relationships (~3 attrs)
5. Temporal & Provenance
"""

from __future__ import annotations

from typing import ClassVar, Literal

from pydantic import BaseModel, Field

from domain.base import BaseEntity, EntityType
from domain.shared import (
    ProvenanceAndConfidence,
    TemporalAndVersioning,
)

# ---------------------------------------------------------------------------
# Sub-models
# ---------------------------------------------------------------------------


class SegmentCriterion(BaseModel):
    """Explicit membership rule for the segment."""

    criterion_type: str = ""
    criterion_value: str = ""
    criterion_description: str = ""


class MarketSizing(BaseModel):
    """TAM / SAM / SOM sizing for the segment."""

    tam: float | None = None
    sam: float | None = None
    som: float | None = None
    currency: str = "USD"
    methodology: str = ""
    as_of_date: str = ""


class GrowthRate(BaseModel):
    """Segment growth metrics."""

    current_yoy_pct: float | None = None
    projected_3yr_cagr: float | None = None
    growth_driver: str = ""


class WinRate(BaseModel):
    """Win rate metrics for the segment."""

    current_pct: float | None = None
    trend: str = ""
    measurement_period: str = ""


class SegmentFinancialSummary(BaseModel):
    """Aggregate financial summary for the segment."""

    annual_revenue: float | None = None
    customer_count: int | None = None
    average_deal_size: float | None = None
    currency: str = "USD"
    fiscal_year: str = ""
    revenue_pct_of_enterprise: float | None = None


class SegmentRegulatoryEnvironment(BaseModel):
    """Regulatory landscape for the segment."""

    primary_regulations: list[str] = Field(default_factory=list)
    compliance_complexity: str = ""
    description: str = ""


class EntryBarrier(BaseModel):
    """Barrier to entry in the segment."""

    barrier_type: str = ""
    barrier_description: str = ""
    severity: str = ""


class ServedByProduct(BaseModel):
    """Product serving this segment with revenue attribution."""

    product_id: str = ""
    product_name: str = ""
    revenue_in_segment: float | None = None
    currency: str = "USD"


# ---------------------------------------------------------------------------
# MarketSegment entity
# ---------------------------------------------------------------------------


class MarketSegment(BaseEntity):
    """Strategic market grouping for go-to-market and investment purposes.

    Hierarchical: Market → Segment → Sub-Segment. Membership defined by
    explicit criteria (industry code, revenue range, geography, etc.).
    """

    ENTITY_TYPE: ClassVar[EntityType] = EntityType.MARKET_SEGMENT
    entity_type: Literal[EntityType.MARKET_SEGMENT] = EntityType.MARKET_SEGMENT

    # --- Group 1: Identity & Hierarchy ---
    segment_id: str = ""
    segment_type: str = ""
    segment_level: str = ""
    parent_segment: str = ""
    child_segments: list[str] = Field(default_factory=list)
    segment_criteria: list[SegmentCriterion] = Field(default_factory=list)

    # --- Group 2: Ownership ---
    segment_owner: str = ""
    managing_org_unit: str = ""

    # --- Group 3: Market Sizing & Performance ---
    market_sizing: MarketSizing | None = None
    growth_rate: GrowthRate | None = None
    competitive_intensity: str = ""
    win_rate: WinRate | None = None
    strategic_priority: str = ""
    segment_financial_summary: SegmentFinancialSummary | None = None
    regulatory_environment: SegmentRegulatoryEnvironment | None = None
    entry_barriers: list[EntryBarrier] = Field(default_factory=list)

    # --- Group 4: Dependencies & Relationships ---
    contains_customers: list[str] = Field(default_factory=list)
    served_by_products: list[ServedByProduct] = Field(default_factory=list)
    managed_by_org_unit: str = ""

    # --- Group 5: Temporal & Provenance ---
    temporal_and_versioning: TemporalAndVersioning = Field(
        default_factory=TemporalAndVersioning
    )
    provenance_and_confidence: ProvenanceAndConfidence = Field(
        default_factory=ProvenanceAndConfidence
    )
