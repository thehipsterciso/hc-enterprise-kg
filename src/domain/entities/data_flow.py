"""DataFlow entity — logical data movement between systems and data assets.

Distinct from L4 Integration (the technical pipe). A single DataFlow may
traverse multiple L4 Integrations. Part of L03: Data Assets layer.
Derived from L5 schema.
"""

from __future__ import annotations

from typing import ClassVar, Literal

from pydantic import BaseModel, Field

from domain.base import BaseEntity, EntityType
from domain.shared import ProvenanceAndConfidence, TemporalAndVersioning

# ---------------------------------------------------------------------------
# Sub-models
# ---------------------------------------------------------------------------


class FlowEndpoint(BaseModel):
    """Source or target endpoint in a data flow."""

    asset_id: str = ""  # Reference to DataAsset
    system_id: str = ""  # Reference to L4 System


class TransformationLogic(BaseModel):
    """Transformation applied within a data flow."""

    description: str = ""
    complexity: str = ""  # Simple, Moderate, Complex, Very Complex
    transformation_type: str = ""  # Pass-Through, Mapping, Aggregation, etc.
    transformation_documentation: str = ""


class FlowVolume(BaseModel):
    """Volume metrics per execution of a data flow."""

    records: int | None = None
    size: float | None = None
    size_unit: str = ""  # KB, MB, GB, TB


class FlowLatency(BaseModel):
    """Latency requirements and actuals for a data flow."""

    target_ms: int | None = None
    actual_p95_ms: int | None = None
    meets_target: bool | None = None


class QualityGate(BaseModel):
    """Quality gate applied during data flow execution."""

    gate_type: str = ""  # Completeness Check, Schema Validation, Business Rule, etc.
    rule_description: str = ""
    pass_rate_pct: float | None = None
    action_on_failure: str = ""  # Reject Record, Quarantine, Alert and Continue, Halt Flow


class LineagePosition(BaseModel):
    """Position of this flow in the overall lineage chain."""

    hops_from_source: int | None = None
    hops_to_consumer: int | None = None
    lineage_chain_id: str = ""


class FlowJurisdictionCrossing(BaseModel):
    """Cross-border jurisdiction analysis for a data flow."""

    crosses_border: bool = False
    source_jurisdiction_id: str = ""  # Reference to L3 Jurisdiction
    target_jurisdiction_id: str = ""  # Reference to L3 Jurisdiction
    transfer_mechanism: str = ""  # SCCs, BCRs, Adequacy Decision, etc.
    compliant: bool | None = None


class FlowErrorRate(BaseModel):
    """Error rate tracking for a data flow."""

    current_pct: float | None = None  # 0-100
    threshold_pct: float | None = None
    trend: str = ""  # Improving, Stable, Worsening


class FlowSLA(BaseModel):
    """Service level agreement for a data flow."""

    freshness_target: str = ""
    completeness_target_pct: float | None = None
    actual_freshness: str = ""
    actual_completeness_pct: float | None = None
    meets_sla: bool | None = None


class FlowCost(BaseModel):
    """Cost profile for a data flow."""

    amount: float | None = None
    currency: str = "USD"
    cost_components: list[str] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# DataFlow entity
# ---------------------------------------------------------------------------


class DataFlow(BaseEntity):
    """A logical data movement between systems and data assets.

    Distinct from L4 Integration (the technical pipe). A single DataFlow
    may traverse multiple Integrations. Tracks data lineage, quality gates,
    jurisdiction crossings, and SLAs.
    """

    ENTITY_TYPE: ClassVar[EntityType] = EntityType.DATA_FLOW
    entity_type: Literal[EntityType.DATA_FLOW] = EntityType.DATA_FLOW

    # --- Identity ---
    flow_id: str = ""  # Format: DF-XXXXX
    flow_type: str = ""  # Ingestion, Transformation, Distribution, Replication, etc.

    # --- Endpoints ---
    source_assets: list[FlowEndpoint] = Field(default_factory=list)
    target_assets: list[FlowEndpoint] = Field(default_factory=list)

    # --- Transformation ---
    transformation_logic: TransformationLogic = Field(
        default_factory=TransformationLogic
    )
    data_classification_in_flow: str = ""  # Highest classification level in this flow

    # --- Volume & Frequency ---
    volume_per_execution: FlowVolume = Field(default_factory=FlowVolume)
    frequency: str = ""  # Real-Time, Near-Real-Time, Hourly, Daily, Weekly, etc.

    # --- Performance ---
    latency: FlowLatency = Field(default_factory=FlowLatency)
    quality_gates: list[QualityGate] = Field(default_factory=list)

    # --- Lineage ---
    lineage_position: LineagePosition = Field(default_factory=LineagePosition)

    # --- Jurisdiction ---
    crosses_jurisdiction: FlowJurisdictionCrossing = Field(
        default_factory=FlowJurisdictionCrossing
    )

    # --- Integration bridge (L5-to-L4) ---
    integration_references: list[str] = Field(default_factory=list)  # L4 Integration IDs

    # --- Ownership ---
    owner: str = ""  # Reference to L2 Role
    support_team: str = ""  # Reference to L1 Org Unit

    # --- Operations ---
    operational_status: str = ""  # Active, Degraded, Maintenance, Failed, etc.
    error_rate: FlowErrorRate = Field(default_factory=FlowErrorRate)
    monitoring_status: str = ""  # Fully Monitored, Partially, Not Monitored

    # --- SLA ---
    sla: FlowSLA = Field(default_factory=FlowSLA)

    # --- Financial ---
    annual_cost: FlowCost = Field(default_factory=FlowCost)

    # --- Temporal & Provenance ---
    temporal: TemporalAndVersioning = Field(default_factory=TemporalAndVersioning)
    provenance: ProvenanceAndConfidence = Field(
        default_factory=ProvenanceAndConfidence
    )
