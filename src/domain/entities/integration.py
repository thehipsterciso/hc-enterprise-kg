"""Integration entity — connection between systems enabling data or process flow.

Integrations are first-class nodes (not edges) because at enterprise scale
they carry their own technology stack, SLA, owner, cost, risk profile, and
lifecycle state. Part of L02: Technology & Systems layer. Derived from L4 schema.
"""

from __future__ import annotations

from typing import ClassVar, Literal

from pydantic import BaseModel, Field

from domain.base import BaseEntity, EntityType
from domain.shared import DataQualityScore, ProvenanceAndConfidence, TemporalAndVersioning

# ---------------------------------------------------------------------------
# Sub-models
# ---------------------------------------------------------------------------


class SystemRef(BaseModel):
    """Reference to a system participating in an integration."""

    system_id: str = ""
    system_name: str = ""


class MiddlewarePlatform(BaseModel):
    """Middleware/iPaaS platform used by an integration."""

    platform_name: str = ""
    platform_system_id: str = ""  # Reference to L4 System
    managed_by: str = ""


class DataExchanged(BaseModel):
    """Data exchanged through an integration."""

    data_description: str = ""
    data_classification: str = ""  # Public, Internal, Confidential, Restricted
    data_domains: list[str] = Field(default_factory=list)
    volume_per_day: str = ""
    record_count_per_day: int | None = None


class LatencyRequirement(BaseModel):
    """Latency requirements and actuals for an integration."""

    max_acceptable_ms: int | None = None
    actual_p95_ms: int | None = None
    meets_requirement: bool | None = None


class ErrorHandling(BaseModel):
    """Error handling configuration for an integration."""

    retry_mechanism: str = ""  # Exponential Backoff, Fixed Interval, None
    dead_letter_queue: bool = False
    alerting: bool = False
    manual_intervention_required: bool = False
    error_rate_pct: float | None = None


class IntegrationAvailabilitySLA(BaseModel):
    """Availability SLA for an integration."""

    target_uptime_pct: float | None = None
    actual_uptime_pct: float | None = None
    measurement_period: str = ""


class IntegrationSecurityProfile(BaseModel):
    """Security posture of an integration."""

    authentication: str = ""  # OAuth 2.0, API Key, mTLS, Basic Auth, None
    encryption_in_transit: bool = False
    encryption_protocol: str = ""  # TLS 1.3, TLS 1.2, etc.
    data_masking: bool = False
    api_key_rotation: bool = False
    ip_whitelisting: bool = False
    rate_limiting: bool = False


class CrossesBoundary(BaseModel):
    """Boundary crossing analysis for an integration."""

    crosses_network_boundary: bool = False
    boundary_type: str = ""  # IT/OT, DMZ/Internal, Cloud/On-Prem, etc.
    crosses_jurisdiction: bool = False
    source_jurisdiction: str = ""
    target_jurisdiction: str = ""
    cross_border_transfer_mechanism: str = ""  # SCCs, BCRs, Adequacy Decision, etc.


class IntegrationCost(BaseModel):
    """Cost profile for an integration."""

    amount: float | None = None
    currency: str = "USD"
    cost_components: list[str] = Field(default_factory=list)


class IntegrationTechDebt(BaseModel):
    """Technical debt indicator for an integration."""

    indicator_type: str = ""
    severity: str = ""  # Critical, High, Medium, Low
    description: str = ""


class IntegrationChange(BaseModel):
    """Change history entry for an integration."""

    change_date: str | None = None
    change_description: str = ""
    changed_by: str = ""


class LastMajorChange(BaseModel):
    """Last significant change to an integration."""

    change_date: str | None = None
    change_description: str = ""
    change_driver: str = ""


# ---------------------------------------------------------------------------
# Integration entity
# ---------------------------------------------------------------------------


class Integration(BaseEntity):
    """A connection between systems enabling data or process flow.

    First-class node (not an edge) because integrations carry their own
    technology stack, SLA, owner, cost, risk profile, and lifecycle.
    Graph pattern: System -> CONNECTS_TO -> Integration -> CONNECTS_TO -> System.
    """

    ENTITY_TYPE: ClassVar[EntityType] = EntityType.INTEGRATION
    entity_type: Literal[EntityType.INTEGRATION] = EntityType.INTEGRATION

    # --- Identity ---
    integration_id: str = ""  # Format: IN-XXXXX
    integration_type: str = ""  # API, File Transfer, Database Link, etc.
    integration_pattern: str = ""  # Request-Reply, Pub-Sub, Batch, etc.

    # --- Connected systems ---
    source_systems: list[SystemRef] = Field(default_factory=list)
    target_systems: list[SystemRef] = Field(default_factory=list)
    direction: str = ""  # Unidirectional, Bidirectional

    # --- Middleware ---
    middleware_platform: MiddlewarePlatform = Field(
        default_factory=MiddlewarePlatform
    )

    # --- Data profile ---
    data_exchanged: DataExchanged = Field(default_factory=DataExchanged)
    frequency: str = ""  # Real-Time, Near Real-Time, Hourly, Daily, etc.

    # --- Performance ---
    latency_requirement: LatencyRequirement = Field(
        default_factory=LatencyRequirement
    )
    error_handling: ErrorHandling = Field(default_factory=ErrorHandling)
    availability_sla: IntegrationAvailabilitySLA = Field(
        default_factory=IntegrationAvailabilitySLA
    )

    # --- Status ---
    operational_status: str = ""  # Active, Degraded, Maintenance, Failed, etc.

    # --- Security ---
    security_profile: IntegrationSecurityProfile = Field(
        default_factory=IntegrationSecurityProfile
    )
    crosses_boundary: CrossesBoundary = Field(default_factory=CrossesBoundary)

    # --- Ownership ---
    owner: str = ""  # Reference to L2 Role
    integration_support_team: str = ""  # Reference to L1 Org Unit
    vendor: str = ""  # Reference to L8 Vendor

    # --- Financial ---
    annual_cost: IntegrationCost = Field(default_factory=IntegrationCost)

    # --- Technical debt ---
    technical_debt_indicators: list[IntegrationTechDebt] = Field(
        default_factory=list
    )

    # --- Monitoring ---
    monitoring_status: str = ""  # Fully Monitored, Partially, Not Monitored

    # --- Lifecycle ---
    effective_date: str | None = None
    retirement_date: str | None = None
    last_major_change: LastMajorChange = Field(default_factory=LastMajorChange)
    change_history: list[IntegrationChange] = Field(default_factory=list)

    # --- Provenance ---
    confidence_level: str = ""  # Verified, Assessed, Estimated, Assumed, Unknown
    data_quality_score: DataQualityScore = Field(
        default_factory=DataQualityScore
    )

    # --- Temporal & Provenance ---
    temporal: TemporalAndVersioning = Field(
        default_factory=TemporalAndVersioning
    )
    provenance: ProvenanceAndConfidence = Field(
        default_factory=ProvenanceAndConfidence
    )
