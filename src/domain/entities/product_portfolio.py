"""ProductPortfolio entity — strategic grouping of products.

A product portfolio is a strategic grouping of related products managed as a
unit for investment, go-to-market, and P&L purposes. Portfolios are
hierarchical (Enterprise Portfolio → Business Unit Portfolio → Product Line →
Sub-Line).

Attribute groups
----------------
1. Identity & Classification
2. Hierarchy
3. Ownership & Organization
4. Strategy
5. Financial Summary
6. Market Position
7. Dependencies & Relationships
8. Temporal & Provenance
"""

from __future__ import annotations

from typing import ClassVar, Literal

from pydantic import BaseModel, Field

from domain.base import BaseEntity, EntityType
from domain.shared import (
    MarketPosition,
    ProvenanceAndConfidence,
    StrategicAlignment,
    TemporalAndVersioning,
)

# ---------------------------------------------------------------------------
# Sub-models — Financial
# ---------------------------------------------------------------------------


class PortfolioFinancialSummary(BaseModel):
    """Aggregated financial summary for the portfolio."""

    annual_revenue: float | None = None
    annual_cost: float | None = None
    gross_margin_pct: float | None = None
    contribution_margin_pct: float | None = None
    currency: str = "USD"
    fiscal_year: str = ""
    yoy_growth_pct: float | None = None
    revenue_pct_of_enterprise: float | None = None


# ---------------------------------------------------------------------------
# ProductPortfolio entity
# ---------------------------------------------------------------------------


class ProductPortfolio(BaseEntity):
    """Strategic grouping of related products/services.

    Managed as a unit for investment, go-to-market, and P&L purposes.
    Hierarchical: Enterprise Portfolio → Business Unit Portfolio → Product
    Line → Sub-Line.
    """

    ENTITY_TYPE: ClassVar[EntityType] = EntityType.PRODUCT_PORTFOLIO
    entity_type: Literal[EntityType.PRODUCT_PORTFOLIO] = EntityType.PRODUCT_PORTFOLIO

    # --- Group 1: Identity & Classification ---
    portfolio_id: str = ""
    portfolio_type: str = ""
    portfolio_level: str = ""

    # --- Group 2: Hierarchy ---
    parent_portfolio: str = ""
    child_portfolios: list[str] = Field(default_factory=list)

    # --- Group 3: Ownership & Organization ---
    portfolio_owner: str = ""
    managing_org_unit: str = ""

    # --- Group 4: Strategy ---
    strategic_role: str = ""
    lifecycle_stage: str = ""
    investment_priority: str = ""
    strategic_alignment: StrategicAlignment | None = None

    # --- Group 5: Financial Summary ---
    financial_summary: PortfolioFinancialSummary | None = None

    # --- Group 6: Market Position ---
    market_position: MarketPosition | None = None

    # --- Group 7: Dependencies & Relationships ---
    contains_products: list[str] = Field(default_factory=list)
    managed_by_org_unit: str = ""

    # --- Group 8: Temporal & Provenance ---
    temporal_and_versioning: TemporalAndVersioning = Field(default_factory=TemporalAndVersioning)
    provenance_and_confidence: ProvenanceAndConfidence = Field(
        default_factory=ProvenanceAndConfidence
    )
