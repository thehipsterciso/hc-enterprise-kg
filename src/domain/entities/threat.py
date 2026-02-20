"""Threat entity — source of potential harm independent of the enterprise.

Threats are inputs to risk assessment. An earthquake (threat) combined
with a single-location data center (vulnerability) creates a business
interruption risk. Part of L01: Compliance & Governance layer.
Derived from L9 schema.
"""

from __future__ import annotations

from typing import ClassVar, Literal

from pydantic import BaseModel, Field

from domain.base import BaseEntity, EntityType
from domain.shared import MaterialityAssessment, ProvenanceAndConfidence, TemporalAndVersioning


# ---------------------------------------------------------------------------
# Sub-models
# ---------------------------------------------------------------------------


class ThreatTaxonomyRef(BaseModel):
    """Cross-reference to an external threat taxonomy."""

    taxonomy: str = ""  # SCF, MITRE ATT&CK, STRIDE, NIST SP 800-30, etc.
    taxonomy_id: str = ""  # e.g., NT-2, MT-2, TA0001
    taxonomy_name: str = ""
    mapping_confidence: str = ""  # Exact Match, Strong, Moderate, Weak, Partial


class GeographicApplicability(BaseModel):
    """Location-specific applicability for a threat."""

    location_id: str = ""  # Reference to L3 Geography or Site
    location_name: str = ""
    applicability_level: str = ""  # High, Medium, Low


class IndustryApplicability(BaseModel):
    """Industry-specific applicability for a threat."""

    industry: str = ""
    applicability_level: str = ""  # High, Medium, Low


class SeasonalPattern(BaseModel):
    """Seasonal variation in threat likelihood."""

    is_seasonal: bool = False
    peak_period: str = ""
    pattern_description: str = ""


class HistoricalFrequency(BaseModel):
    """Historical frequency data for a threat."""

    events_per_year_industry: float | None = None
    events_per_year_enterprise: float | None = None
    last_occurrence_enterprise: str | None = None
    data_source: str = ""


class ThreatRiskLink(BaseModel):
    """Link from threat to a risk it creates."""

    risk_id: str = ""
    causal_description: str = ""


class ThreatControlLink(BaseModel):
    """Link from threat to a control that addresses it."""

    control_id: str = ""
    effectiveness_against_threat: str = ""  # Fully, Substantially, Partially, Minimally


class RelatedThreat(BaseModel):
    """Relationship between threats."""

    threat_id: str = ""
    relationship_type: str = ""  # Enables, Enabled By, Amplifies, etc.


# ---------------------------------------------------------------------------
# Threat entity
# ---------------------------------------------------------------------------


class Threat(BaseEntity):
    """A source of potential harm that exists independent of the enterprise.

    Threats are inputs to risk assessment. SCF's 37 threats (14 natural,
    23 man-made) populate the security and physical baseline. Enterprise
    extends with competitive, market, technology disruption, and talent
    threats using the same structure.
    """

    ENTITY_TYPE: ClassVar[EntityType] = EntityType.THREAT
    entity_type: Literal[EntityType.THREAT] = EntityType.THREAT

    # --- Identity & classification ---
    threat_id: str = ""  # Format: TH-XXXXX
    threat_group: str = ""  # Natural Threat, Man-Made Intentional/Unintentional/Systemic, etc.
    threat_category: str = ""  # Environmental/Weather, Cyber — External Actor, etc.
    threat_source_type: str = ""  # Nation State, Organized Criminal, Hacktivist, etc.
    threat_taxonomy_references: list[ThreatTaxonomyRef] = Field(default_factory=list)
    origin: str = ""  # SCF Threat Catalog, MITRE ATT&CK, Threat Intelligence, etc.

    # --- Relevance & applicability ---
    relevance_to_enterprise: str = ""  # Critical, High, Medium, Low, Not Applicable
    relevance_rationale: str = ""
    geographic_applicability: list[GeographicApplicability] = Field(
        default_factory=list
    )
    industry_applicability: list[IndustryApplicability] = Field(default_factory=list)
    seasonal_pattern: SeasonalPattern = Field(default_factory=SeasonalPattern)
    historical_frequency: HistoricalFrequency = Field(
        default_factory=HistoricalFrequency
    )

    # --- Materiality & impact ---
    materiality_assessment: MaterialityAssessment = Field(
        default_factory=MaterialityAssessment
    )
    potential_impact_description: str = ""

    # --- Assessment & monitoring ---
    threat_trend: str = ""  # Increasing, Stable, Decreasing
    threat_velocity: str = ""  # Instant, Hours, Days, Weeks, Months
    last_assessed: str | None = None
    assessment_cadence: str = ""  # Annual, Semi-Annual, Quarterly, etc.
    next_assessment: str | None = None

    # --- Relationships ---
    creates_risks: list[ThreatRiskLink] = Field(default_factory=list)
    addressed_by_controls: list[ThreatControlLink] = Field(default_factory=list)
    related_threats: list[RelatedThreat] = Field(default_factory=list)

    # --- Temporal & provenance ---
    temporal: TemporalAndVersioning = Field(default_factory=TemporalAndVersioning)
    provenance: ProvenanceAndConfidence = Field(
        default_factory=ProvenanceAndConfidence
    )
