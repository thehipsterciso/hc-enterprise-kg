"""Geography entity — geographic region in the enterprise footprint.

Flat entity (~20 attributes) for hierarchical geographic decomposition
(Global → Super-Region → Region → Country → State/Province → Metro).
Part of L07: Locations & Facilities layer. Derived from L3 schema.
"""

from __future__ import annotations

from typing import ClassVar, Literal

from pydantic import BaseModel, Field

from domain.base import BaseEntity, EntityType

# ---------------------------------------------------------------------------
# Sub-models
# ---------------------------------------------------------------------------


class CountryEntry(BaseModel):
    """Country within a geography."""

    country_code: str = ""  # ISO 3166-1 alpha-2
    country_name: str = ""


class RegionalLeadership(BaseModel):
    """Regional leadership assignment."""

    org_unit_id: str = ""  # Reference to L1
    leader_role_id: str = ""  # Reference to L2 Role
    leader_person_id: str = ""  # Reference to L2 Person


class MarketCharacteristics(BaseModel):
    """Economic and market characteristics of a geography."""

    total_gdp: float | None = None
    population: float | None = None
    gdp_growth_rate: float | None = None
    economic_classification: str = ""  # Developed, Emerging, Frontier, Mixed
    currency_primary: str = ""  # ISO 4217
    as_of_date: str | None = None


class GeographicStrategicImportance(BaseModel):
    """Strategic importance of a geography."""

    importance_level: str = ""
    # Enum: Primary Growth Market, Core Established Market,
    # Emerging Opportunity, Maintenance Market, Exit Candidate
    revenue_contribution_pct: float | None = None  # 0-100
    employee_count: int | None = None
    site_count: int | None = None


# ---------------------------------------------------------------------------
# Main entity
# ---------------------------------------------------------------------------


class Geography(BaseEntity):
    """Represents a geographic region in the enterprise footprint.

    Hierarchical decomposition from Global down to Metro Area.
    Links to Sites (containment) and Jurisdictions (overlap).
    """

    ENTITY_TYPE: ClassVar[EntityType] = EntityType.GEOGRAPHY
    entity_type: Literal[EntityType.GEOGRAPHY] = EntityType.GEOGRAPHY

    # --- Identity ---
    geography_id: str = ""  # GEO-XXXXX
    geography_name_short: str = ""
    geography_type: str = ""
    # Enum: Global, Super-Region, Region, Sub-Region, Country,
    # State / Province, Metro Area, Custom
    geography_description: str = ""

    # --- Hierarchy ---
    parent_geography: str = ""  # Reference to parent Geography
    child_geographies: list[str] = Field(default_factory=list)

    # --- Content ---
    countries_included: list[CountryEntry] = Field(default_factory=list)
    regional_leadership: RegionalLeadership | None = None
    time_zones: list[str] = Field(default_factory=list)  # IANA timezone
    primary_languages: list[str] = Field(default_factory=list)  # ISO 639-1
    market_characteristics: MarketCharacteristics | None = None
    strategic_importance: GeographicStrategicImportance | None = None

    # --- Edge ports ---
    sites_in_geography: list[str] = Field(default_factory=list)  # Site IDs
    overlaps_with_jurisdictions: list[str] = Field(default_factory=list)  # Jurisdiction IDs

    # --- Temporal (inline, not shared block for flat entity) ---
    effective_date: str | None = None
    retirement_date: str | None = None
    last_updated: str | None = None
    schema_version: str = "1.0.0"
    confidence_level: str = ""  # Verified, Assessed, Estimated, Assumed, Unknown
