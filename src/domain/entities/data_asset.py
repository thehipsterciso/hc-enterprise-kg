"""Data asset entity — datasets, databases, data stores, and data products.

Extended from the v0.1 minimal data asset (~9 fields) to the full enterprise
ontology (~85 attributes across 8 groups). Part of L03: Data Assets layer.
Derived from L5 schema, aligned with DCAM 2.2, DMBOK2, ISO 8000, GDPR/CCPA.
"""

from __future__ import annotations

from typing import ClassVar, Literal

from pydantic import BaseModel, Field

from domain.base import BaseEntity, EntityType
from domain.shared import (
    AuditFinding,
    BackupStatus,
    ProvenanceAndConfidence,
    RegulatoryApplicability,
    TemporalAndVersioning,
)

# ---------------------------------------------------------------------------
# Sub-models — Group 1: Identity & Classification
# ---------------------------------------------------------------------------


class AcquisitionSource(BaseModel):
    """Source details for externally acquired data."""

    source_name: str = ""
    acquisition_date: str | None = None
    license_terms: str = ""
    usage_restrictions: str = ""
    renewal_date: str | None = None


# ---------------------------------------------------------------------------
# Sub-models — Group 2: Data Architecture
# ---------------------------------------------------------------------------


class StorageTechnology(BaseModel):
    """Where the data physically/logically resides."""

    system_id: str = ""  # Reference to L4 System
    system_name: str = ""
    storage_service: str = ""


class StorageFormat(BaseModel):
    """How data is stored on disk/object store."""

    format_type: str = ""  # Relational Tables, Parquet, Avro, JSON, CSV, etc.
    schema_definition_exists: bool = False
    schema_reference: str = ""
    schema_evolution_strategy: str = ""  # Strict, Backward/Forward/Full Compat, No Strategy


class DataVolume(BaseModel):
    """Size metrics for a data asset."""

    current_size: float | None = None
    size_unit: str = ""  # MB, GB, TB, PB
    growth_rate_monthly_pct: float | None = None
    projected_size_12m: float | None = None
    projected_size_unit: str = ""


class RecordCount(BaseModel):
    """Row/document count metrics."""

    current_count: int | None = None
    growth_rate_monthly_pct: float | None = None
    count_as_of_date: str | None = None


class DataVelocity(BaseModel):
    """Rate of data change."""

    creation_rate: str = ""
    update_rate: str = ""
    deletion_rate: str = ""


class PartitioningStrategy(BaseModel):
    """How data is partitioned for performance."""

    partition_key: str = ""
    partition_type: str = ""  # Date/Time, Geography, Business Unit, Hash, Range, List, None


class ArchivalStrategy(BaseModel):
    """Tiered storage and archival configuration."""

    hot_tier_retention: str = ""
    warm_tier_retention: str = ""
    cold_tier_retention: str = ""
    archive_technology: str = ""


class ReplicationConfig(BaseModel):
    """Data replication settings."""

    is_replicated: bool = False
    replication_type: str = ""  # Synchronous, Asynchronous, Near-Real-Time, Scheduled, None
    replica_locations: list[str] = Field(default_factory=list)
    replication_lag: str = ""


class EncryptionAtRest(BaseModel):
    """Encryption profile for data at rest."""

    encrypted: bool = False
    algorithm: str = ""
    key_management: str = ""  # HSM, Cloud KMS, Software Key Store, Application Managed


class DataMaskingConfig(BaseModel):
    """Data masking and de-identification configuration."""

    masking_applied: bool = False
    masking_type: str = ""  # Static/Dynamic Masking, Tokenization, Pseudonymization, FPE
    masked_fields: list[str] = Field(default_factory=list)
    non_production_masking: bool = False


# ---------------------------------------------------------------------------
# Sub-models — Group 3: Data Quality
# ---------------------------------------------------------------------------


class QualityScoreComposite(BaseModel):
    """Aggregate quality score."""

    score: float | None = None  # 1.0-5.0
    scale: str = "1-5"
    assessed_date: str | None = None


class QualityDimension(BaseModel):
    """Individual quality dimension measurement (ISO 8000/DCAM)."""

    dimension: str = ""  # Completeness, Accuracy, Timeliness, Consistency, etc.
    score: float | None = None  # 0-100
    measurement_method: str = ""
    threshold: float | None = None
    meets_threshold: bool | None = None
    last_measured: str | None = None


class QualityRule(BaseModel):
    """Automated quality check rule."""

    rule_id: str = ""
    rule_description: str = ""
    rule_type: str = ""  # Completeness Check, Format Validation, Range Check, etc.
    pass_rate_pct: float | None = None
    last_execution_date: str | None = None
    automated: bool = False


class QualityIssue(BaseModel):
    """Open data quality issue."""

    issue_id: str = ""
    description: str = ""
    severity: str = ""  # Critical, High, Medium, Low
    affected_records_pct: float | None = None
    remediation_status: str = ""  # Open, In Progress, Remediated, Accepted, Deferred


class QualityMonitoring(BaseModel):
    """Automated quality monitoring configuration."""

    automated_monitoring: bool = False
    monitoring_tool: str = ""
    monitoring_frequency: str = ""
    alerting_configured: bool = False


class ProfilingStatus(BaseModel):
    """Data profiling status."""

    last_profiled_date: str | None = None
    profiling_tool: str = ""
    profile_reference: str = ""


class GoldenRecordStatus(BaseModel):
    """Master data golden record tracking."""

    is_golden_source: bool = False
    golden_source_reference: str = ""
    conflict_resolution_method: str = ""  # Most Recent Wins, Most Complete, Source Priority, etc.


class CleansingHistoryEntry(BaseModel):
    """Data cleansing event."""

    cleansing_date: str | None = None
    scope: str = ""
    method: str = ""
    records_affected: int | None = None


class FitnessForPurpose(BaseModel):
    """Fitness assessment for a specific use case."""

    use_case: str = ""
    fitness_rating: str = ""  # Fit, Fit with Caveats, Unfit, Not Assessed
    fitness_evidence: str = ""


# ---------------------------------------------------------------------------
# Sub-models — Group 4: Governance & Lineage
# ---------------------------------------------------------------------------


class AccessGovernance(BaseModel):
    """Access governance configuration."""

    access_request_process: str = ""
    approval_authority: str = ""
    access_review_frequency: str = ""
    last_review_date: str | None = None


class CurrentAccessGrants(BaseModel):
    """Access grant summary."""

    total_users_with_access: int | None = None
    roles_with_access: list[str] = Field(default_factory=list)
    last_access_audit_date: str | None = None


class ConsentManagement(BaseModel):
    """Consent tracking for personal data."""

    requires_consent: bool = False
    consent_type: str = ""  # Explicit Opt-In, Implied, Contractual, Legitimate Interest, etc.
    consent_tracking_system: str = ""
    consent_withdrawal_process: str = ""


class LineageEntry(BaseModel):
    """Upstream or downstream lineage reference."""

    asset_id: str = ""  # Reference to DataAsset
    asset_name: str = ""
    description: str = ""
    transformation_type: str = ""  # Direct Copy, Mapping, Aggregation, Enrichment, etc.
    refresh_frequency: str = ""
    dependency_strength: str = ""  # Strong, Moderate, Weak


class CatalogStatus(BaseModel):
    """Data catalog registration status."""

    cataloged: bool = False
    catalog_platform: str = ""
    catalog_url: str = ""
    metadata_completeness_pct: float | None = None


class RetentionCompliance(BaseModel):
    """Retention policy compliance tracking."""

    policy_reference: str = ""
    required_retention: str = ""
    actual_retention: str = ""
    compliant: bool | None = None
    disposal_method: str = ""
    legal_hold_flag: bool = False


# ---------------------------------------------------------------------------
# Sub-models — Group 5: Regulatory & Compliance
# ---------------------------------------------------------------------------


class CrossBorderTransferStatus(BaseModel):
    """Cross-border data transfer compliance."""

    data_crosses_borders: bool = False
    source_jurisdictions: list[str] = Field(default_factory=list)
    destination_jurisdictions: list[str] = Field(default_factory=list)
    transfer_mechanisms: list[str] = Field(default_factory=list)  # SCCs, BCRs, etc.
    compliant: bool | None = None


class PrivacyImpactAssessment(BaseModel):
    """PIA/DPIA tracking."""

    pia_required: bool = False
    pia_completed: bool = False
    pia_date: str | None = None
    pia_findings_summary: str = ""
    pia_reference: str = ""


class BreachNotificationObligation(BaseModel):
    """Breach notification requirements."""

    applicable: bool = False
    notification_timeframe_hours: int | None = None
    authority_notification: bool = False
    individual_notification: bool = False
    jurisdiction: str = ""


class ThirdPartySharing(BaseModel):
    """Third-party data sharing arrangement."""

    third_party_name: str = ""
    sharing_purpose: str = ""
    legal_basis: str = ""
    data_processing_agreement_reference: str = ""
    data_types_shared: list[str] = Field(default_factory=list)


class AITrainingUsage(BaseModel):
    """AI/ML training usage tracking (EU AI Act / NIST AI RMF)."""

    used_for_ai_training: bool = False
    model_references: list[str] = Field(default_factory=list)
    consent_basis: str = ""
    bias_assessment_completed: bool = False
    eu_ai_act_risk_category: str = ""  # Unacceptable, High, Limited, Minimal, Not Applicable


class AnonymizationStatus(BaseModel):
    """Anonymization/de-identification status."""

    anonymized: bool = False
    anonymization_method: str = ""  # k-Anonymity, l-Diversity, Differential Privacy, etc.
    re_identification_risk_level: str = ""  # Negligible, Low, Medium, High


# ---------------------------------------------------------------------------
# Sub-models — Group 6: Financial Profile
# ---------------------------------------------------------------------------


class DataCostItem(BaseModel):
    """Cost line item for a data asset."""

    annual_cost: float | None = None
    currency: str = "USD"
    cost_driver: str = ""


class DataAcquisitionCost(BaseModel):
    """Purchase/license cost for acquired data."""

    cost: float | None = None
    currency: str = "USD"
    renewal_date: str | None = None


class DataValueAssessment(BaseModel):
    """Estimated business value of a data asset."""

    estimated_value: float | None = None
    valuation_method: str = ""  # Revenue Attribution, Cost Avoidance, Replacement Cost, etc.
    confidence: str = ""  # High, Medium, Low


class DataCostOptimization(BaseModel):
    """Cost optimization opportunity for data assets."""

    opportunity_description: str = ""
    estimated_annual_savings: float | None = None
    effort_level: str = ""  # Quick Win, Moderate Effort, Significant Effort, Major Initiative
    status: str = ""  # Identified, Under Evaluation, Approved, In Progress, Realized, Rejected


class TotalDataCost(BaseModel):
    """Aggregate annual data cost."""

    annual_total: float | None = None
    currency: str = "USD"


# ---------------------------------------------------------------------------
# DataAsset entity
# ---------------------------------------------------------------------------


class DataAsset(BaseEntity):
    """A data asset: database, dataset, file store, data product, etc.

    Extended from v0.1 (~9 fields) to full enterprise ontology (~85 attributes
    across 8 groups). All v0.1 fields preserved for backward compatibility.
    """

    ENTITY_TYPE: ClassVar[EntityType] = EntityType.DATA_ASSET
    entity_type: Literal[EntityType.DATA_ASSET] = EntityType.DATA_ASSET

    # --- v0.1 fields (preserved) ---
    data_type: str = ""  # pii, phi, financial, intellectual_property, public
    classification: str = "internal"  # public, internal, confidential, restricted
    format: str = ""  # sql, nosql, file, api, stream
    retention_days: int | None = None
    is_encrypted: bool = False
    owner_id: str | None = None
    system_id: str | None = None
    record_count: int | None = None
    regulations: list[str] = Field(default_factory=list)

    # === Group 1: Identity & Classification ===
    asset_id: str = ""  # Format: DA-XXXXX
    asset_name_common: str = ""
    asset_description_extended: str = ""
    asset_type: str = ""  # Database, Data Warehouse, Data Lake Zone, etc.
    asset_subtype: str = ""  # Further refinement within type
    data_domain_primary: str = ""  # Reference to DataDomain
    data_domain_secondary: list[str] = Field(default_factory=list)
    data_classification: str = ""  # L00 classification enum
    pii_categories: list[str] = Field(default_factory=list)
    data_format: str = ""  # Structured, Semi-Structured, Unstructured, Mixed
    origin: str = ""  # Organic, Acquired (M&A), Third-Party, etc.
    acquisition_source: AcquisitionSource = Field(default_factory=AcquisitionSource)
    functional_domain_primary: str = ""
    functional_domain_secondary: list[str] = Field(default_factory=list)

    # === Group 2: Data Architecture ===
    storage_technology: StorageTechnology = Field(default_factory=StorageTechnology)
    storage_format: StorageFormat = Field(default_factory=StorageFormat)
    volume: DataVolume = Field(default_factory=DataVolume)
    record_count_detail: RecordCount = Field(default_factory=RecordCount)
    velocity: DataVelocity = Field(default_factory=DataVelocity)
    partitioning_strategy: PartitioningStrategy = Field(default_factory=PartitioningStrategy)
    indexing_strategy: str = ""
    archival_strategy: ArchivalStrategy = Field(default_factory=ArchivalStrategy)
    replication: ReplicationConfig = Field(default_factory=ReplicationConfig)
    backup_status: BackupStatus = Field(default_factory=BackupStatus)
    encryption_at_rest: EncryptionAtRest = Field(default_factory=EncryptionAtRest)
    data_masking: DataMaskingConfig = Field(default_factory=DataMaskingConfig)

    # === Group 3: Data Quality ===
    quality_score_composite: QualityScoreComposite = Field(default_factory=QualityScoreComposite)
    quality_dimensions: list[QualityDimension] = Field(default_factory=list)
    quality_rules: list[QualityRule] = Field(default_factory=list)
    quality_trend: str = ""  # Improving, Stable, Declining, Unknown
    quality_issues_open: list[QualityIssue] = Field(default_factory=list)
    quality_monitoring: QualityMonitoring = Field(default_factory=QualityMonitoring)
    profiling_status: ProfilingStatus = Field(default_factory=ProfilingStatus)
    golden_record_status: GoldenRecordStatus = Field(default_factory=GoldenRecordStatus)
    data_cleansing_history: list[CleansingHistoryEntry] = Field(default_factory=list)
    fitness_for_purpose: list[FitnessForPurpose] = Field(default_factory=list)

    # === Group 4: Governance & Lineage ===
    data_owner: str = ""  # Reference to L2 Role
    data_steward: str = ""  # Reference to L2 Role
    data_custodian: str = ""  # Reference to L2 Role (technical)
    access_governance: AccessGovernance = Field(default_factory=AccessGovernance)
    access_control_model: str = ""  # RBAC, ABAC, MAC, DAC, Custom, None
    current_access_grants: CurrentAccessGrants = Field(default_factory=CurrentAccessGrants)
    consent_management: ConsentManagement = Field(default_factory=ConsentManagement)
    lineage_upstream: list[LineageEntry] = Field(default_factory=list)
    lineage_downstream: list[LineageEntry] = Field(default_factory=list)
    lineage_completeness: str = ""  # Fully/Substantially/Partially Documented, Undocumented
    catalog_status: CatalogStatus = Field(default_factory=CatalogStatus)
    retention_compliance: RetentionCompliance = Field(default_factory=RetentionCompliance)

    # === Group 5: Regulatory & Compliance ===
    regulatory_applicability: list[RegulatoryApplicability] = Field(default_factory=list)
    cross_border_transfer_status: CrossBorderTransferStatus = Field(
        default_factory=CrossBorderTransferStatus
    )
    data_subject_rights_applicable: bool = False
    dsar_process_reference: str = ""
    privacy_impact_assessment: PrivacyImpactAssessment = Field(
        default_factory=PrivacyImpactAssessment
    )
    breach_notification_obligation: BreachNotificationObligation = Field(
        default_factory=BreachNotificationObligation
    )
    audit_findings: list[AuditFinding] = Field(default_factory=list)
    third_party_sharing: list[ThirdPartySharing] = Field(default_factory=list)
    ai_training_usage: AITrainingUsage = Field(default_factory=AITrainingUsage)
    anonymization_status: AnonymizationStatus = Field(default_factory=AnonymizationStatus)

    # === Group 6: Financial Profile ===
    storage_cost: DataCostItem = Field(default_factory=DataCostItem)
    processing_cost: DataCostItem = Field(default_factory=DataCostItem)
    acquisition_cost: DataAcquisitionCost = Field(default_factory=DataAcquisitionCost)
    value_assessment: DataValueAssessment = Field(default_factory=DataValueAssessment)
    cost_optimization_opportunities: list[DataCostOptimization] = Field(default_factory=list)
    total_data_cost: TotalDataCost = Field(default_factory=TotalDataCost)

    # === Temporal & Provenance ===
    temporal: TemporalAndVersioning = Field(default_factory=TemporalAndVersioning)
    provenance: ProvenanceAndConfidence = Field(default_factory=ProvenanceAndConfidence)
