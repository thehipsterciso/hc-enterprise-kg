"""DataPipeline entity — data movement and transformation workflow.

Covers CDAIO Modules 4 (Data Engineering) and 6 (DataOps). Models the
end-to-end lifecycle of data pipelines: ingestion, transformation,
quality checking, orchestration, CI/CD, cost, and governance.

Attribute groups
----------------
1. Identity & Classification (~10 attrs)
2. Source & Target (~8 attrs)
3. Execution Profile (~8 attrs)
4. Quality & Observability (~8 attrs) -- DataOps standards
5. CI/CD & Version Control (~6 attrs) -- DataOps Manifesto
6. Cost & Performance (~5 attrs)
7. Governance & Ownership (~6 attrs)
8. Dependencies & Relationships
9. Temporal & Provenance

Framework provenance: dbt, Great Expectations, DataOps Manifesto,
Apache Airflow, Prefect, Dagster, Soda, medallion architecture.
"""

from __future__ import annotations

from typing import ClassVar, Literal

from pydantic import BaseModel, Field

from domain.base import BaseEntity, EntityType
from domain.shared import (
    ProvenanceAndConfidence,
    TemporalAndVersioning,
)

# ===========================================================================
# Group 3: Execution Profile — sub-models
# ===========================================================================


class ExecutionFrequency(BaseModel):
    """Scheduling and last-run tracking for a pipeline."""

    schedule: str = ""  # cron expression or descriptor (e.g. "0 */2 * * *")
    typical_duration_minutes: float | None = None
    last_run_start: str | None = None
    last_run_end: str | None = None
    last_run_status: str = ""  # success, failed, partial, skipped, running


class ComputeResource(BaseModel):
    """Compute resources allocated to a pipeline run."""

    compute_type: str = ""  # spark, kubernetes, ecs, lambda, local, databricks
    instance_type: str = ""  # e.g. "m5.xlarge", "Standard_D4s_v3"
    parallelism: int | None = None
    auto_scaling: bool = False


class RetryPolicy(BaseModel):
    """Retry and dead-letter configuration for pipeline failures."""

    max_retries: int | None = None
    backoff_strategy: str = ""  # fixed, exponential, linear
    dead_letter_queue: str = ""  # queue/topic name or ARN


# ===========================================================================
# Group 7: Governance & Ownership — sub-models
# ===========================================================================


class PipelineChangeLogEntry(BaseModel):
    """Audit trail entry for pipeline changes."""

    date: str = ""
    change_description: str = ""
    changed_by: str = ""


# ===========================================================================
# DataPipeline entity
# ===========================================================================


class DataPipeline(BaseEntity):
    """A data movement and transformation workflow.

    Models ETL/ELT pipelines, streaming jobs, CDC replication,
    reverse-ETL flows, and ML training/inference pipelines. Captures
    identity, source/target lineage, execution profile, data quality
    checks (Great Expectations / Soda / dbt tests), CI/CD posture
    per the DataOps Manifesto, cost metrics, and governance.
    """

    ENTITY_TYPE: ClassVar[EntityType] = EntityType.DATA_PIPELINE
    entity_type: Literal[EntityType.DATA_PIPELINE] = EntityType.DATA_PIPELINE

    # --- Group 1: Identity & Classification ---
    pipeline_id: str = ""  # Format: DP-XXXXX
    # etl, elt, streaming, batch, micro_batch, cdc,
    # reverse_etl, ml_training, ml_inference, data_quality
    pipeline_type: str = ""
    pipeline_pattern: str = ""  # medallion, lambda, kappa, hub_spoke, fan_out, fan_in
    # airflow, prefect, dagster, mage, dbt_cloud, step_functions, custom
    orchestration_platform: str = ""
    pipeline_status: str = ""  # active, paused, failed, deprecated, development, testing
    functional_domain: str = ""
    pipeline_tier: str = ""  # bronze, silver, gold
    cron_schedule: str = ""  # cron expression for scheduled runs
    trigger_type: str = ""  # scheduled, event_driven, on_demand, dependency

    # --- Group 2: Source & Target ---
    source_systems: list[str] = Field(default_factory=list)  # system IDs
    source_data_assets: list[str] = Field(default_factory=list)  # data asset IDs
    target_systems: list[str] = Field(default_factory=list)  # system IDs
    target_data_assets: list[str] = Field(default_factory=list)  # data asset IDs
    target_data_products: list[str] = Field(default_factory=list)  # data product IDs
    transformation_count: int | None = None
    transformation_language: str = ""  # sql, python, spark, dbt, custom
    transformation_complexity: str = ""  # simple, moderate, complex

    # --- Group 3: Execution Profile ---
    execution_frequency: ExecutionFrequency | None = None
    average_runtime_minutes: float | None = None
    p95_runtime_minutes: float | None = None
    compute_resource: ComputeResource | None = None
    data_volume_per_run_gb: float | None = None
    rows_processed_per_run: int | None = None
    retry_policy: RetryPolicy | None = None
    idempotent: bool = False

    # --- Group 4: Quality & Observability (DataOps standards) ---
    quality_checks_enabled: bool = False
    quality_framework: str = ""  # great_expectations, soda, dbt_tests, custom
    quality_check_count: int | None = None
    quality_pass_rate_pct: float | None = None
    observability_enabled: bool = False
    alerting_channels: list[str] = Field(default_factory=list)  # slack, pagerduty, email, webhook
    sla_target_minutes: int | None = None
    sla_breach_count_30d: int | None = None
    data_lineage_tracked: bool = False

    # --- Group 5: CI/CD & Version Control (DataOps Manifesto) ---
    version_controlled: bool = False
    repository_url: str = ""
    ci_cd_enabled: bool = False
    ci_cd_platform: str = ""  # github_actions, gitlab_ci, jenkins, custom
    test_coverage_pct: float | None = None
    deployment_strategy: str = ""  # blue_green, canary, rolling, direct

    # --- Group 6: Cost & Performance ---
    monthly_compute_cost: float | None = None
    currency: str = "USD"
    cost_per_gb_processed: float | None = None
    cost_trend: str = ""  # increasing, stable, decreasing
    optimization_opportunities: list[str] = Field(default_factory=list)

    # --- Group 7: Governance & Ownership ---
    pipeline_owner: str = ""
    technical_owner: str = ""
    data_steward: str = ""
    approval_required_for_changes: bool = False
    change_log: list[PipelineChangeLogEntry] = Field(default_factory=list)
    documentation_url: str = ""

    # --- Group 8: Dependencies & Relationships ---
    depends_on_pipelines: list[str] = Field(default_factory=list)
    upstream_systems: list[str] = Field(default_factory=list)
    downstream_consumers: list[str] = Field(default_factory=list)
    orchestrated_by_system: str = ""

    # --- Group 9: Temporal & Provenance ---
    temporal_and_versioning: TemporalAndVersioning = Field(default_factory=TemporalAndVersioning)
    provenance_and_confidence: ProvenanceAndConfidence = Field(
        default_factory=ProvenanceAndConfidence
    )
