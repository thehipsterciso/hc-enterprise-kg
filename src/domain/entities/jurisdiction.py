"""Jurisdiction entity — legal/regulatory jurisdiction.

Flat entity (~18 attributes) for regulatory environment modeling.
Covers legal systems, data residency, labor law, tax, privacy, sanctions,
and cross-border transfer rules. Part of L07: Locations & Facilities layer.
Derived from L3 schema.
"""

from __future__ import annotations

from typing import ClassVar, Literal

from pydantic import BaseModel, Field

from domain.base import BaseEntity, EntityType

# ---------------------------------------------------------------------------
# Sub-models
# ---------------------------------------------------------------------------


class JurisdictionLocalName(BaseModel):
    """Local-language name for a jurisdiction."""

    language_code: str = ""  # ISO 639-1
    name: str = ""


class RegulatoryAgency(BaseModel):
    """Regulatory agency within a jurisdiction."""

    agency_name: str = ""
    regulatory_domain: str = ""


class GoverningBody(BaseModel):
    """Governing body of a jurisdiction."""

    name: str = ""
    regulatory_agencies: list[RegulatoryAgency] = Field(default_factory=list)


class RegulatoryFrameworkSummary(BaseModel):
    """Summary of the regulatory framework."""

    legal_system_type: str = ""
    # Enum: Common Law, Civil Law, Mixed, Religious Law, Customary Law
    regulatory_intensity: str = ""  # Heavy, Moderate, Light, Evolving
    key_characteristics: str = ""


class DataResidencyRequirements(BaseModel):
    """Data residency/localization requirements."""

    has_requirements: bool = False
    requirement_description: str = ""
    applicable_data_types: list[str] = Field(default_factory=list)
    localization_required: bool = False
    transfer_mechanisms_available: list[str] = Field(default_factory=list)


class LaborLawSummary(BaseModel):
    """Summary of labor law requirements."""

    employment_at_will: bool | None = None
    notice_period_statutory: str = ""
    severance_requirements: str = ""
    works_council_required: bool = False
    works_council_threshold: str = ""
    maximum_working_hours: str = ""
    mandatory_benefits: list[str] = Field(default_factory=list)
    union_prevalence: str = ""  # High, Moderate, Low, Rare


class WithholdingTaxRates(BaseModel):
    """Withholding tax rates."""

    dividends: float | None = None
    interest: float | None = None
    royalties: float | None = None


class TransferPricingRules(BaseModel):
    """Transfer pricing regulatory requirements."""

    documentation_required: bool = False
    country_by_country_reporting: bool = False
    arm_length_standard: bool = False
    advance_pricing_agreements: bool = False


class TaxRegime(BaseModel):
    """Tax environment summary."""

    corporate_tax_rate: float | None = None  # 0-100
    effective_tax_rate: float | None = None  # 0-100
    vat_gst_rate: float | None = None  # 0-100
    withholding_tax_rates: WithholdingTaxRates = Field(default_factory=WithholdingTaxRates)
    transfer_pricing_rules: TransferPricingRules = Field(default_factory=TransferPricingRules)
    tax_incentives: list[str] = Field(default_factory=list)


class BreachNotificationRequirement(BaseModel):
    """Data breach notification requirements."""

    required: bool = False
    timeframe_hours: float | None = None
    authority_notification: bool = False
    individual_notification: bool = False


class PrivacyRegulation(BaseModel):
    """Privacy regulation summary."""

    primary_regulation: str = ""
    regulation_reference: str = ""  # Reference to L9
    supervisory_authority: str = ""
    breach_notification_requirement: BreachNotificationRequirement = Field(
        default_factory=BreachNotificationRequirement
    )
    consent_requirements: str = ""
    cross_border_transfer_restrictions: str = ""


class CrossBorderTransferRules(BaseModel):
    """Cross-border transfer restrictions."""

    data_transfer_restricted: bool = False
    goods_transfer_restricted: bool = False
    export_controls: list[str] = Field(default_factory=list)  # EAR, ITAR, Wassenaar, etc.
    import_restrictions: str = ""
    currency_controls: bool = False


class SanctionsStatus(BaseModel):
    """Sanctions status of a jurisdiction."""

    sanctioned: bool = False
    sanctioning_bodies: list[str] = Field(default_factory=list)  # OFAC, EU, UN
    sanction_type: str = ""  # Comprehensive, Targeted / Sectoral, None
    last_reviewed: str | None = None


# ---------------------------------------------------------------------------
# Main entity
# ---------------------------------------------------------------------------


class Jurisdiction(BaseEntity):
    """Represents a legal/regulatory jurisdiction.

    Models the regulatory environment including legal systems, tax regimes,
    data residency, labor law, privacy regulations, sanctions, and
    cross-border transfer rules.
    """

    ENTITY_TYPE: ClassVar[EntityType] = EntityType.JURISDICTION
    entity_type: Literal[EntityType.JURISDICTION] = EntityType.JURISDICTION

    # --- Identity ---
    jurisdiction_id: str = ""  # JR-XXXXX
    jurisdiction_name_local: JurisdictionLocalName | None = None
    jurisdiction_type: str = ""
    # Enum: Supranational, Federal / National, State / Provincial,
    # Local / Municipal, Economic Zone, Industry-Specific
    jurisdiction_code: str = ""  # ISO 3166-1 or ISO 3166-2

    # --- Hierarchy ---
    parent_jurisdiction: str = ""  # Reference to parent Jurisdiction
    child_jurisdictions: list[str] = Field(default_factory=list)

    # --- Regulatory environment ---
    governing_body: GoverningBody | None = None
    regulatory_framework_summary: RegulatoryFrameworkSummary | None = None
    data_residency_requirements: DataResidencyRequirements | None = None
    labor_law_summary: LaborLawSummary | None = None
    tax_regime: TaxRegime | None = None
    privacy_regulation: PrivacyRegulation | None = None
    cross_border_transfer_rules: CrossBorderTransferRules | None = None
    sanctions_status: SanctionsStatus | None = None

    # --- Edge ports ---
    sites_in_jurisdiction: list[str] = Field(default_factory=list)  # Site IDs
    applicable_to_entities: list[str] = Field(default_factory=list)  # L1 IDs
    governs_capabilities: list[str] = Field(default_factory=list)  # L0 IDs
    links_to_compliance: list[str] = Field(default_factory=list)  # L9 IDs

    # --- Temporal (inline) ---
    effective_date: str | None = None
    last_updated: str | None = None
    update_trigger: str = ""
    # Enum: Regulatory Change, Tax Law Change, Political Change,
    # Sanctions Update, Scheduled Review, New Data Requirement
    schema_version: str = "1.0.0"
    confidence_level: str = ""  # Verified, Assessed, Estimated, Assumed, Unknown
    data_source: list[str] = Field(default_factory=list)
