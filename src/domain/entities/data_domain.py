"""DataDomain entity — strategic governance aggregation for data.

A DataDomain is how business leaders think about data and how policies are
scoped. It contains DataAssets and maps to business capabilities. Part of
L03: Data Assets layer. Derived from L5 schema, aligned with DCAM 2.2/DMBOK2.
"""

from __future__ import annotations

from typing import ClassVar, Literal

from pydantic import BaseModel, Field

from domain.base import BaseEntity, EntityType
from domain.shared import ProvenanceAndConfidence, TemporalAndVersioning

# ---------------------------------------------------------------------------
# Sub-models
# ---------------------------------------------------------------------------


class SubDomain(BaseModel):
    """A sub-domain within a data domain."""

    sub_domain_name: str = ""
    sub_domain_description: str = ""


class BusinessGlossaryReference(BaseModel):
    """Link to the business glossary for this domain."""

    glossary_platform: str = ""
    glossary_url: str = ""
    term_count: int | None = None
    last_updated: str | None = None


class GoverningPolicy(BaseModel):
    """Policy governing a data domain."""

    policy_id: str = ""  # Reference to L01 Policy
    policy_name: str = ""
    policy_type: str = ""  # Data Classification, Retention, Quality, Access, Privacy, etc.


class SensitivityFlags(BaseModel):
    """Data sensitivity indicators for a domain."""

    pii_flag: bool = False
    phi_flag: bool = False
    pci_flag: bool = False
    children_data_flag: bool = False
    biometric_flag: bool = False
    financial_data_flag: bool = False
    trade_secret_flag: bool = False


class RegulatorySensitivity(BaseModel):
    """Regulatory sensitivity entry for a data domain."""

    regulation: str = ""
    sensitivity_description: str = ""
    handling_requirements: str = ""
    jurisdiction_id: str = ""  # Reference to L3 Jurisdiction


class DataResidencyRequirement(BaseModel):
    """Data residency/localization requirement."""

    jurisdiction_id: str = ""  # Reference to L3 Jurisdiction
    jurisdiction_name: str = ""
    requirement_description: str = ""
    localization_required: bool = False
    compliant: bool | None = None
    compliance_evidence: str = ""


class RetentionPolicy(BaseModel):
    """Data retention policy for a domain."""

    minimum_retention: str = ""
    minimum_retention_basis: str = ""
    maximum_retention: str = ""
    maximum_retention_basis: str = ""
    destruction_method: str = ""  # Secure Deletion, Cryptographic Erasure, etc.
    legal_hold_status: str = ""  # No Active Hold, Active Hold — Litigation, etc.


class QualityTargets(BaseModel):
    """Domain-level data quality targets (ISO 8000/DCAM)."""

    completeness_target_pct: float | None = None  # 0-100
    accuracy_target_pct: float | None = None  # 0-100
    timeliness_target: str = ""
    consistency_target: str = ""
    current_composite_score: float | None = None  # 1.0-5.0
    meets_targets: bool | None = None


class MaturityDimension(BaseModel):
    """DCAM 2.2 maturity dimension assessment."""

    dimension: str = ""  # Data Governance, Quality Mgmt, Operations, Architecture, etc.
    score: float | None = None  # 1.0-5.0
    assessed_date: str | None = None


class MonetizationPotential(BaseModel):
    """Data monetization potential assessment."""

    potential_type: str = ""  # Direct Data Product, Process Optimization, Risk Reduction, etc.
    estimated_annual_value: float | None = None
    currency: str = "USD"
    confidence: str = ""  # High — Demonstrated, Medium — Modeled, Low — Estimated, Speculative


# ---------------------------------------------------------------------------
# DataDomain entity
# ---------------------------------------------------------------------------


class DataDomain(BaseEntity):
    """A strategic data governance domain.

    DataDomains are how business leaders think about data — they contain
    DataAssets, map to business capabilities, and scope governance policies.
    Derived from DCAM 2.2 and DMBOK2 frameworks.
    """

    ENTITY_TYPE: ClassVar[EntityType] = EntityType.DATA_DOMAIN
    entity_type: Literal[EntityType.DATA_DOMAIN] = EntityType.DATA_DOMAIN

    # --- Identity ---
    domain_id: str = ""  # Format: DD-XXXXX
    domain_type: str = ""  # Master Data, Reference Data, Transactional, Analytical, etc.
    domain_scope: str = ""  # Enterprise-Wide, Business Unit, Function, Regional
    sub_domains: list[SubDomain] = Field(default_factory=list)
    business_glossary_reference: BusinessGlossaryReference = Field(
        default_factory=BusinessGlossaryReference
    )

    # --- Ownership ---
    domain_owner: str = ""  # Reference to L2 Role (senior business leader)
    domain_steward: str = ""  # Reference to L2 Role (day-to-day stewardship)
    governing_policies: list[GoverningPolicy] = Field(default_factory=list)

    # --- Classification & Sensitivity ---
    data_classification: str = ""  # Highest classification in this domain
    sensitivity_flags: SensitivityFlags = Field(default_factory=SensitivityFlags)
    regulatory_sensitivity: list[RegulatorySensitivity] = Field(default_factory=list)
    data_residency_requirements: list[DataResidencyRequirement] = Field(default_factory=list)

    # --- Retention ---
    retention_policy: RetentionPolicy = Field(default_factory=RetentionPolicy)

    # --- Quality & Maturity ---
    quality_targets: QualityTargets = Field(default_factory=QualityTargets)
    maturity_level: str = ""  # L00 maturity scale
    maturity_dimensions: list[MaturityDimension] = Field(default_factory=list)

    # --- Strategic Value ---
    strategic_value: str = ""  # Revenue Generating, Decision Enabling, Compliance Required, etc.
    monetization_potential: MonetizationPotential = Field(default_factory=MonetizationPotential)

    # --- Temporal & Provenance ---
    temporal: TemporalAndVersioning = Field(default_factory=TemporalAndVersioning)
    provenance: ProvenanceAndConfidence = Field(default_factory=ProvenanceAndConfidence)
