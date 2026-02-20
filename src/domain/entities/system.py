"""System entity — discrete technology component delivering functionality.

Encompasses enterprise applications, business applications, infrastructure
platforms, data platforms, security tools, OT/ICS systems, and end-user
computing. The primary node connecting technology to all other layers.
Part of L02: Technology & Systems layer. Derived from L4 schema.
Extends original v0.1 System with full enterprise ontology attributes.
"""

from __future__ import annotations

from typing import ClassVar, Literal

from pydantic import BaseModel, Field

from domain.base import BaseEntity, EntityType
from domain.shared import (
    AuditFinding,
    BackupStatus,
    CostBenchmark,
    CyberExposure,
    ProvenanceAndConfidence,
    RegulatoryApplicability,
    StrategicAlignment,
    TemporalAndVersioning,
)

# ---------------------------------------------------------------------------
# Group 1: Identity & Classification sub-models
# ---------------------------------------------------------------------------


class FormerName(BaseModel):
    """Historical name for a system that has been migrated or rebranded."""

    former_name: str = ""
    from_date: str | None = None
    to_date: str | None = None
    change_reason: str = ""


class AcquisitionSource(BaseModel):
    """M&A acquisition origin for an acquired system."""

    source_entity_name: str = ""
    acquisition_date: str | None = None
    integration_status: str = ""  # Pre-Integration, Assessment Complete, etc.


class TaxonomyLineage(BaseModel):
    """Framework cross-reference for a system."""

    framework: str = ""  # TOGAF, ArchiMate, NIST CSF, CIS Controls, etc.
    framework_element_id: str = ""
    mapping_confidence: str = ""  # Exact Match, Strong, Moderate, Weak


# ---------------------------------------------------------------------------
# Group 2: Technical Profile sub-models
# ---------------------------------------------------------------------------


class TechStackEntry(BaseModel):
    """Single layer in a system's technology stack."""

    layer: str = ""  # Operating System, Runtime, Framework, etc.
    technology: str = ""
    version: str = ""
    vendor: str = ""
    end_of_support_date: str | None = None


class ProgrammingLanguage(BaseModel):
    """Programming language used by a system."""

    language: str = ""
    version: str = ""
    usage_type: str = ""  # Primary, Secondary, Scripting, Test, Build


class DataStore(BaseModel):
    """Data store used by a system."""

    store_type: str = ""  # RDBMS, NoSQL, Object Store, etc.
    technology: str = ""
    version: str = ""
    capacity: str = ""


class ApiSurface(BaseModel):
    """API exposure profile for a system."""

    api_count: int | None = None
    api_types: list[str] = Field(default_factory=list)
    api_documentation_status: str = ""
    api_versioning_strategy: str = ""
    api_gateway: str = ""


class AuthenticationMechanism(BaseModel):
    """Authentication mechanism supported by a system."""

    mechanism: str = ""  # SSO, LDAP, SAML, OAuth, etc.
    protocol: str = ""
    mfa_supported: bool = False
    mfa_enforced: bool = False


class EncryptionProfile(BaseModel):
    """Encryption posture for a system."""

    data_at_rest: str = ""  # AES-256, TDE, None, etc.
    data_in_transit: str = ""  # TLS 1.3, TLS 1.2, etc.
    key_management: str = ""  # KMS, HSM, Application-Managed, etc.


class ScalabilityProfile(BaseModel):
    """Scalability characteristics of a system."""

    horizontal_scaling: bool = False
    vertical_scaling: bool = False
    auto_scaling: bool = False
    max_concurrent_users: int | None = None
    max_throughput: str = ""


class AvailabilityDesign(BaseModel):
    """High-availability architecture design."""

    architecture_pattern: str = ""  # Active-Active, Active-Passive, etc.
    redundancy_level: str = ""
    failover_type: str = ""  # Automatic, Manual, None
    designed_uptime_pct: float | None = None


class VersionInfo(BaseModel):
    """Current version details for a system."""

    version: str = ""
    release_date: str | None = None
    patch_level: str = ""
    last_update_date: str | None = None


class TechnicalDebtIndicator(BaseModel):
    """Technical debt indicator for a system or integration."""

    indicator_type: str = ""  # EOL Component, Unsupported OS, etc.
    severity: str = ""  # Critical, High, Medium, Low
    description: str = ""
    estimated_remediation_effort: str = ""


class OpenSourceProfile(BaseModel):
    """Open source component profile."""

    component_count: int | None = None
    license_types: list[str] = Field(default_factory=list)
    sbom_available: bool = False
    sbom_format: str = ""
    vulnerability_scanning_enabled: bool = False
    last_scan_date: str | None = None


class ContainerProfile(BaseModel):
    """Containerization status."""

    is_containerized: bool = False
    container_platform: str = ""
    orchestration_platform: str = ""


class IaCProfile(BaseModel):
    """Infrastructure as Code status."""

    iac_enabled: bool = False
    iac_tool: str = ""
    coverage_pct: float | None = None


class ObservabilityStack(BaseModel):
    """Observability tool coverage."""

    logging_tool: str = ""
    logging_coverage: str = ""
    monitoring_tool: str = ""
    monitoring_coverage: str = ""
    tracing_tool: str = ""
    tracing_coverage: str = ""
    alerting_tool: str = ""
    alerting_coverage: str = ""


# ---------------------------------------------------------------------------
# Group 3: Operational Profile sub-models
# ---------------------------------------------------------------------------


class AvailabilitySLA(BaseModel):
    """Availability SLA and actuals."""

    target_uptime_pct: float | None = None
    measurement_window: str = ""
    actual_uptime_pct: float | None = None
    actual_measurement_period: str = ""
    sla_source: str = ""
    sla_breach_count_12m: int | None = None


class PerformanceSLA(BaseModel):
    """Performance SLA and actuals."""

    response_time_target_ms: int | None = None
    throughput_target: str = ""
    actual_response_time_p95_ms: int | None = None
    actual_throughput: str = ""


class CurrentUsers(BaseModel):
    """User count profile for a system."""

    total_licensed_users: int | None = None
    total_provisioned_users: int | None = None
    active_users_monthly: int | None = None
    peak_concurrent: int | None = None
    user_growth_trend: str = ""  # Growing, Stable, Declining


class UsersByGeography(BaseModel):
    """User count by geographic region."""

    geography_id: str = ""
    geography_name: str = ""
    user_count: int | None = None


class SupportModel(BaseModel):
    """Support model for a system."""

    support_provider: str = ""  # Internal, Vendor, MSP, Hybrid
    support_tier: str = ""
    support_hours: str = ""  # 24x7, Business Hours, etc.
    escalation_path: str = ""
    support_contract_reference: str = ""


class IncidentHistory(BaseModel):
    """Incident history for a system."""

    p1_count_12m: int | None = None
    p2_count_12m: int | None = None
    mttr_hours: float | None = None
    last_major_incident_date: str | None = None
    last_major_incident_description: str = ""


class ChangeVelocity(BaseModel):
    """DORA-style change velocity metrics."""

    releases_per_month: float | None = None
    deployment_frequency: str = ""
    change_failure_rate_pct: float | None = None
    lead_time_for_changes: str = ""


class MaintenanceWindow(BaseModel):
    """Scheduled maintenance window."""

    schedule: str = ""
    duration_hours: float | None = None
    impact_scope: str = ""
    last_maintenance_date: str | None = None


class CapacityCurrent(BaseModel):
    """Current capacity utilization."""

    cpu_utilization_pct: float | None = None
    memory_utilization_pct: float | None = None
    storage_utilization_pct: float | None = None
    network_utilization_pct: float | None = None
    measurement_date: str | None = None


class CapacityHeadroom(BaseModel):
    """Remaining capacity and scaling plan."""

    months_to_capacity: int | None = None
    scaling_plan: str = ""
    scaling_cost_estimate: float | None = None


# ---------------------------------------------------------------------------
# Group 4: Financial Profile sub-models
# ---------------------------------------------------------------------------


class TotalCostOfOwnership(BaseModel):
    """Annual TCO for a system."""

    annual_tco: float | None = None
    currency: str = "USD"
    fiscal_year: str = ""
    tco_methodology: str = ""


class CostBreakdownItem(BaseModel):
    """Single cost category in a TCO breakdown."""

    category: str = ""  # License, Hosting, Support, Development, etc.
    amount: float | None = None
    percentage_of_total: float | None = None


class LicenseDetails(BaseModel):
    """Software license details."""

    license_type: str = ""
    license_count: int | None = None
    licenses_in_use: int | None = None
    license_utilization_pct: float | None = None
    true_up_date: str | None = None
    contract_reference: str = ""


class ContractDetails(BaseModel):
    """Vendor contract details for a system."""

    vendor: str = ""
    contract_id: str = ""
    contract_start: str | None = None
    contract_end: str | None = None
    annual_value: float | None = None
    total_contract_value: float | None = None
    currency: str = "USD"
    auto_renewal: bool = False
    notice_period_days: int | None = None


class CostPerUnit(BaseModel):
    """Per-user or per-transaction cost."""

    amount: float | None = None
    currency: str = "USD"
    basis: str = ""


class CostOptimizationOpportunity(BaseModel):
    """Identified cost optimization opportunity."""

    opportunity_description: str = ""
    estimated_annual_savings: float | None = None
    currency: str = "USD"
    effort_level: str = ""  # Low, Medium, High
    status: str = ""  # Identified, In Progress, Implemented, Deferred


class CapexRemaining(BaseModel):
    """Remaining capitalized expenditure."""

    remaining_book_value: float | None = None
    currency: str = "USD"
    amortization_end_date: str | None = None


# ---------------------------------------------------------------------------
# Group 5: Strategic Importance sub-models
# ---------------------------------------------------------------------------


class BusinessImpactIfUnavailable(BaseModel):
    """Impact assessment if system becomes unavailable."""

    impact_description: str = ""
    estimated_financial_impact_per_hour: float | None = None
    currency: str = "USD"
    affected_capabilities: list[str] = Field(default_factory=list)
    affected_users: int | None = None
    affected_customers: int | None = None


class ReplacementCandidate(BaseModel):
    """Replacement/migration plan for a system."""

    has_replacement_planned: bool = False
    replacement_system_id: str = ""
    replacement_system_name: str = ""
    migration_timeline: str = ""
    migration_status: str = ""
    migration_complexity: str = ""  # Low, Medium, High, Very High


class FitnessScore(BaseModel):
    """Technical or business fitness assessment."""

    composite_score: float | None = None  # 1-5
    dimensions: list[str] = Field(default_factory=list)
    assessed_date: str | None = None


# ---------------------------------------------------------------------------
# Group 6: Security & Compliance sub-models
# ---------------------------------------------------------------------------


class VulnerabilityProfile(BaseModel):
    """Vulnerability scan profile."""

    last_scan_date: str | None = None
    critical_count: int | None = None
    high_count: int | None = None
    medium_count: int | None = None
    low_count: int | None = None
    scan_tool: str = ""
    scan_coverage_pct: float | None = None
    trend: str = ""  # Improving, Stable, Worsening


class PenetrationTestStatus(BaseModel):
    """Penetration test results."""

    last_test_date: str | None = None
    test_type: str = ""  # External, Internal, Application, Social Engineering
    findings_critical: int | None = None
    findings_high: int | None = None
    findings_open: int | None = None
    next_scheduled_date: str | None = None


class PatchCompliance(BaseModel):
    """Patch compliance status."""

    patch_policy: str = ""
    compliance_pct: float | None = None
    days_to_patch_critical: int | None = None
    days_to_patch_high: int | None = None
    last_assessed_date: str | None = None


class AccessReviewStatus(BaseModel):
    """Access review status for a system."""

    last_review_date: str | None = None
    next_review_date: str | None = None
    review_frequency: str = ""
    last_review_findings: str = ""


class SecurityArchitectureReview(BaseModel):
    """Security architecture review status."""

    last_review_date: str | None = None
    review_outcome: str = ""
    open_findings_count: int | None = None
    next_review_date: str | None = None


class ComplianceCertification(BaseModel):
    """Compliance certification held by a system."""

    certification: str = ""  # SOC 2 Type II, ISO 27001, PCI DSS, etc.
    scope: str = ""
    status: str = ""  # Certified, In Progress, Expired, Not Applicable
    last_audit_date: str | None = None
    next_audit_date: str | None = None


class DataResidencyConstraint(BaseModel):
    """Data residency requirement for a system."""

    jurisdiction_id: str = ""
    data_types: list[str] = Field(default_factory=list)
    residency_requirement: str = ""


# ---------------------------------------------------------------------------
# System entity
# ---------------------------------------------------------------------------


class System(BaseEntity):
    """A discrete technology component delivering functionality.

    The richest entity in the knowledge graph (~119 attributes).
    Encompasses enterprise applications, business applications,
    infrastructure platforms, data platforms, security tools, OT/ICS
    systems, and end-user computing. Connects technology to capabilities,
    organizations, people, locations, data, and vendors.
    """

    ENTITY_TYPE: ClassVar[EntityType] = EntityType.SYSTEM
    entity_type: Literal[EntityType.SYSTEM] = EntityType.SYSTEM

    # --- v0.1 fields (preserved for backward compatibility) ---
    system_type: str = ""
    hostname: str = ""
    ip_address: str = ""
    os: str = ""
    version: str = ""
    vendor_id: str | None = None
    environment: str = "production"
    criticality: str = "medium"
    is_internet_facing: bool = False
    owner_id: str | None = None
    department_id: str | None = None
    network_id: str | None = None
    ports: list[int] = Field(default_factory=list)
    technologies: list[str] = Field(default_factory=list)

    # === Group 1: Identity & Classification ===
    system_id: str = ""  # Format: SY-XXXXX
    system_name_common: str = ""
    system_name_former: list[FormerName] = Field(default_factory=list)
    system_description_extended: str = ""
    system_category: str = ""
    system_subcategory: str = ""
    deployment_model: str = ""
    hosting_model: str = ""
    architecture_type: str = ""
    system_tier: str = ""
    origin: str = ""
    acquisition_source: AcquisitionSource = Field(default_factory=AcquisitionSource)
    procurement_type: str = ""
    functional_domain_primary: str = ""
    functional_domain_secondary: list[str] = Field(default_factory=list)
    taxonomy_lineage: list[TaxonomyLineage] = Field(default_factory=list)

    # === Group 2: Technical Profile ===
    technology_stack: list[TechStackEntry] = Field(default_factory=list)
    programming_languages: list[ProgrammingLanguage] = Field(default_factory=list)
    data_stores: list[DataStore] = Field(default_factory=list)
    api_surface: ApiSurface = Field(default_factory=ApiSurface)
    authentication_mechanisms: list[AuthenticationMechanism] = Field(default_factory=list)
    encryption_profile: EncryptionProfile = Field(default_factory=EncryptionProfile)
    scalability_profile: ScalabilityProfile = Field(default_factory=ScalabilityProfile)
    availability_design: AvailabilityDesign = Field(default_factory=AvailabilityDesign)
    current_version_info: VersionInfo = Field(default_factory=VersionInfo)
    version_currency: str = ""
    technical_debt_indicators: list[TechnicalDebtIndicator] = Field(default_factory=list)
    open_source_components: OpenSourceProfile = Field(default_factory=OpenSourceProfile)
    cloud_native_score: str = ""
    containerized: ContainerProfile = Field(default_factory=ContainerProfile)
    infrastructure_as_code: IaCProfile = Field(default_factory=IaCProfile)
    observability_stack: ObservabilityStack = Field(default_factory=ObservabilityStack)

    # === Group 3: Operational Profile ===
    operational_status: str = ""
    operational_status_rationale: str = ""
    availability_sla: AvailabilitySLA = Field(default_factory=AvailabilitySLA)
    performance_sla: PerformanceSLA = Field(default_factory=PerformanceSLA)
    current_users: CurrentUsers = Field(default_factory=CurrentUsers)
    user_base_by_geography: list[UsersByGeography] = Field(default_factory=list)
    support_model: SupportModel = Field(default_factory=SupportModel)
    incident_history: IncidentHistory = Field(default_factory=IncidentHistory)
    change_velocity: ChangeVelocity = Field(default_factory=ChangeVelocity)
    maintenance_windows: MaintenanceWindow = Field(default_factory=MaintenanceWindow)
    capacity_current: CapacityCurrent = Field(default_factory=CapacityCurrent)
    capacity_headroom: CapacityHeadroom = Field(default_factory=CapacityHeadroom)
    monitoring_coverage: str = ""

    # === Group 4: Financial Profile ===
    total_cost_of_ownership: TotalCostOfOwnership = Field(default_factory=TotalCostOfOwnership)
    cost_breakdown: list[CostBreakdownItem] = Field(default_factory=list)
    license_details: LicenseDetails = Field(default_factory=LicenseDetails)
    contract_details: ContractDetails = Field(default_factory=ContractDetails)
    cost_per_user: CostPerUnit = Field(default_factory=CostPerUnit)
    cost_per_transaction: CostPerUnit = Field(default_factory=CostPerUnit)
    cost_trend: str = ""
    cost_optimization_opportunities: list[CostOptimizationOpportunity] = Field(default_factory=list)
    capex_remaining: CapexRemaining = Field(default_factory=CapexRemaining)
    system_cost_benchmark: CostBenchmark = Field(default_factory=CostBenchmark)

    # === Group 5: Strategic Importance ===
    strategic_alignment: list[StrategicAlignment] = Field(default_factory=list)
    business_criticality: str = ""
    criticality_justification: str = ""
    business_impact_if_unavailable: BusinessImpactIfUnavailable = Field(
        default_factory=BusinessImpactIfUnavailable
    )
    strategic_classification: str = ""
    strategic_classification_rationale: str = ""
    replacement_candidate: ReplacementCandidate = Field(default_factory=ReplacementCandidate)
    innovation_potential: str = ""
    technical_fitness: FitnessScore = Field(default_factory=FitnessScore)
    business_fitness: FitnessScore = Field(default_factory=FitnessScore)

    # === Group 6: Security & Compliance ===
    risk_exposure_inherent: str = ""
    risk_exposure_residual: str = ""
    data_classification_handled: list[str] = Field(default_factory=list)
    vulnerability_profile: VulnerabilityProfile = Field(default_factory=VulnerabilityProfile)
    penetration_test_status: PenetrationTestStatus = Field(default_factory=PenetrationTestStatus)
    patch_compliance: PatchCompliance = Field(default_factory=PatchCompliance)
    access_control_model: str = ""
    access_review_status: AccessReviewStatus = Field(default_factory=AccessReviewStatus)
    security_architecture_review: SecurityArchitectureReview = Field(
        default_factory=SecurityArchitectureReview
    )
    compliance_certifications: list[ComplianceCertification] = Field(default_factory=list)
    regulatory_applicability: list[RegulatoryApplicability] = Field(default_factory=list)
    network_zone: str = ""
    data_residency_constraints: list[DataResidencyConstraint] = Field(default_factory=list)
    audit_findings: list[AuditFinding] = Field(default_factory=list)
    cyber_exposure: CyberExposure = Field(default_factory=CyberExposure)

    # === Group 7: Ownership & Accountability ===
    system_owner: str = ""
    technical_owner: str = ""
    data_steward: str = ""
    security_owner: str = ""
    support_team: str = ""
    development_team: str = ""
    governance_body: str = ""
    vendor_account_manager: str = ""

    # === Operational backup ===
    backup_status: BackupStatus = Field(default_factory=BackupStatus)

    # === Temporal & Provenance ===
    temporal: TemporalAndVersioning = Field(default_factory=TemporalAndVersioning)
    provenance: ProvenanceAndConfidence = Field(default_factory=ProvenanceAndConfidence)
