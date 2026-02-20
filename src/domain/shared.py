"""Shared sub-models for the enterprise knowledge graph ontology.

Reusable Pydantic models derived from L00 shared definitions. These are
used across multiple entity types to avoid structural duplication and
ensure consistency across layers.
"""

from __future__ import annotations

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Temporal & Versioning (L00 reusable block)
# ---------------------------------------------------------------------------


class TemporalAndVersioning(BaseModel):
    """Temporal tracking for enterprise ontology entities.

    Extends the base TemporalMixin with schema-level versioning
    and effective dating for enterprise governance.
    """

    effective_date: str | None = None
    expiration_date: str | None = None
    last_review_date: str | None = None
    next_review_date: str | None = None
    change_reason: str = ""
    schema_version: str = "1.0.0"


# ---------------------------------------------------------------------------
# Provenance & Confidence (L00 reusable block)
# ---------------------------------------------------------------------------


class DataQualityScore(BaseModel):
    """Data quality assessment for provenance tracking."""

    completeness_pct: float | None = None
    accuracy_confidence: str = ""  # High, Medium, Low, Unknown
    timeliness_score: str = ""  # Current, Recent, Stale, Outdated
    consistency_score: str = ""  # Consistent, Minor/Major Inconsistencies, Not Assessed


class AttestationStatus(BaseModel):
    """Attestation tracking for provenance."""

    attested_by: str = ""
    attestation_date: str | None = None
    next_attestation_date: str | None = None


class DataGap(BaseModel):
    """Known data gap in an entity's attribute set."""

    attribute_name: str = ""
    gap_description: str = ""
    remediation_plan: str = ""
    priority: str = ""  # Critical, High, Medium, Low


class ProvenanceAndConfidence(BaseModel):
    """Data provenance and confidence tracking.

    Tracks where entity data came from, how confident we are in it,
    and what gaps exist. Used across all major entity types.
    """

    data_quality_score: DataQualityScore = Field(default_factory=DataQualityScore)
    primary_data_source: str = ""
    last_assessed_date: str | None = None
    assessed_by: str = ""
    assessment_methodology: str = ""  # Manual, Automated, Hybrid, Import, Self-Reported
    confidence_level: str = ""  # Verified, High, Medium, Low, Unverified
    attestation_status: AttestationStatus | None = None
    known_data_gaps: list[DataGap] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Audit Finding (L00 reusable block)
# ---------------------------------------------------------------------------


class AuditFinding(BaseModel):
    """Standard audit finding. Used in L0, L1, L3, L4, L5, L9."""

    finding_id: str = ""
    finding_severity: str = ""  # Critical, High, Medium, Low, Informational
    finding_source: str = ""  # Internal/External Audit, Pen Test, Vuln Scan, etc.
    finding_date: str | None = None
    finding_description: str = ""
    remediation_status: str = ""  # Open, In Progress, Remediated, Accepted, Deferred
    remediation_target_date: str | None = None
    remediation_owner: str = ""


# ---------------------------------------------------------------------------
# Single Point of Failure (L00 reusable block)
# ---------------------------------------------------------------------------


class SinglePointOfFailure(BaseModel):
    """SPOF identification and tracking. Used in L0, L3, L4."""

    spof_id: str = ""
    spof_description: str = ""
    spof_type: str = ""  # Layer-specific enum
    mitigation_status: str = ""  # Mitigated, Partially Mitigated, Unmitigated, Accepted
    mitigation_plan: str = ""


# ---------------------------------------------------------------------------
# Strategic Alignment (L00 reusable block)
# ---------------------------------------------------------------------------


class StrategicAlignment(BaseModel):
    """Strategic objective alignment. Used in L0, L1, L3, L4, L5, L6."""

    strategic_objective_id: str = ""
    strategic_objective_name: str = ""
    alignment_strength: str = ""  # Primary Enabler, Contributing, Tangential
    alignment_evidence: str = ""


# ---------------------------------------------------------------------------
# Cost Benchmark (L00 reusable block)
# ---------------------------------------------------------------------------


class CostBenchmark(BaseModel):
    """Cost benchmarking structure. Used in L0, L1, L3, L4, L5."""

    benchmark_source: str = ""
    benchmark_value: float | None = None
    percentile_position: float | None = None  # 1-100
    benchmark_date: str | None = None


# ---------------------------------------------------------------------------
# Regulatory Applicability (L00 reusable block)
# ---------------------------------------------------------------------------


class RegulatoryApplicability(BaseModel):
    """Regulatory compliance tracking. Used in L0, L1, L4, L5, L9."""

    regulation_id: str = ""
    regulation_name: str = ""
    jurisdiction: str = ""
    applicability_type: str = ""  # Directly Regulated, Indirectly Affected, Voluntary Adoption
    compliance_status: str = ""  # Compliant, Partially Compliant, Non-Compliant, Not Assessed
    last_assessment_date: str | None = None
    next_assessment_date: str | None = None


# ---------------------------------------------------------------------------
# Cyber Exposure (L00 reusable block)
# ---------------------------------------------------------------------------


class CyberExposure(BaseModel):
    """Cyber risk exposure profile. Used in L0, L4."""

    attack_surface_type: str = ""  # Internet Facing, Internal, Air Gapped, Hybrid, Cloud, OT/ICS
    threat_profile: str = ""  # Nation State, Organized Crime, Hacktivist, Insider, Opportunistic, Low
    last_assessment_date: str | None = None
    assessment_methodology: str = ""


# ---------------------------------------------------------------------------
# Backup Status (L00 reusable block)
# ---------------------------------------------------------------------------


class BackupStatus(BaseModel):
    """Backup assessment structure. Used in L4, L5."""

    backup_frequency: str = ""  # Continuous, Hourly, Daily, Weekly, Monthly, None
    backup_type: str = ""  # Full, Incremental, Differential, Snapshot, Replication, None
    last_successful_backup: str | None = None
    backup_tested_date: str | None = None
    retention_period: str = ""
    meets_rpo: bool | None = None


# ---------------------------------------------------------------------------
# Sanctions Screening (cross-layer: L7 Customer, L8 Vendor)
# ---------------------------------------------------------------------------


class SanctionsScreening(BaseModel):
    """Sanctions and watchlist screening. Used in L7, L8."""

    screening_status: str = ""  # Clear, Match Found, Pending Review, Not Screened
    last_screening_date: str | None = None
    screening_provider: str = ""
    lists_checked: list[str] = Field(default_factory=list)  # OFAC SDN, EU, UN, etc.
    match_details: str = ""


# ---------------------------------------------------------------------------
# Industry Classification (cross-layer: L7 Customer, L8 Vendor)
# ---------------------------------------------------------------------------


class IndustryClassification(BaseModel):
    """Industry taxonomy classification. Used in L7, L8."""

    naics_code: str = ""
    naics_description: str = ""
    sic_code: str = ""
    sic_description: str = ""
    gics_code: str = ""
    gics_description: str = ""


# ---------------------------------------------------------------------------
# Materiality Assessment (cross-layer: L9 Risk, L9 Threat)
# ---------------------------------------------------------------------------


class MaterialityAssessment(BaseModel):
    """SEC/PCAOB materiality thresholds. Used in L9 Risk and Threat."""

    pct_of_pretax_income: float | None = None
    pct_of_total_assets: float | None = None
    pct_of_total_equity: float | None = None
    pct_of_total_revenue: float | None = None
    materiality_conclusion: str = ""  # Material, Potentially Material, Not Material, Not Assessed


# ---------------------------------------------------------------------------
# Market Position (cross-layer: L6 Portfolio, L6 Product, L7 Segment)
# ---------------------------------------------------------------------------


class MarketPosition(BaseModel):
    """Total addressable / serviceable / obtainable market. Used in L6, L7."""

    market_size_tam: float | None = None  # Total Addressable Market
    market_size_sam: float | None = None  # Serviceable Addressable Market
    market_size_som: float | None = None  # Serviceable Obtainable Market
    market_share_pct: float | None = None
    market_share_rank: int | None = None
    currency: str = "USD"
    as_of_date: str | None = None
