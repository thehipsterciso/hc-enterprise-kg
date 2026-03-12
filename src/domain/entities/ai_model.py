"""AIModel entity — AI/ML model lifecycle, governance, and operations.

Covers CDAIO Modules 9-16: Data Science, AI Foundations, AI Strategy,
AI Factory, MLOps, Responsible AI, and Generative AI. Models the full
lifecycle from training through deployment, monitoring, and retirement.

Attribute groups
----------------
1. Identity & Classification (~12 attrs)
2. Training & Data Lineage (~10 attrs)
3. Performance Metrics (~8 attrs)
4. Deployment & Operations (~10 attrs)
5. Fairness & Responsible AI (~10 attrs) — EU AI Act, NIST AI RMF
6. Governance & Ownership (~8 attrs)
7. GenAI-Specific Fields (~8 attrs) — Module 16
8. Financial Profile (~5 attrs)
9. Dependencies & Relationships — Typed Edges (~6 attrs)
10. Temporal & Provenance

Framework provenance: NIST AI RMF 1.0, EU AI Act, ISO/IEC 42001,
MLflow, CRISP-DM, Google Model Cards, OECD AI Principles.
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
# Group 1: Identity & Classification — sub-models
# ===========================================================================


class TaxonomyLineageAIModel(BaseModel):
    """Taxonomy lineage mapping for AI model classification."""

    framework: str = ""  # NIST AI RMF, ISO/IEC 42001, CRISP-DM, etc.
    framework_element_id: str = ""
    mapping_confidence: str = ""  # Exact Match, Strong, Moderate, Weak


# ===========================================================================
# Group 2: Training & Data Lineage — sub-models
# ===========================================================================


class TrainingCompute(BaseModel):
    """Compute resources consumed during model training."""

    gpu_type: str = ""  # A100, H100, V100, TPU v4, etc.
    gpu_hours: float | None = None
    cloud_provider: str = ""  # AWS, GCP, Azure, On-Prem, etc.
    estimated_cost: float | None = None
    currency: str = "USD"
    carbon_footprint_kg: float | None = None


# ===========================================================================
# Group 3: Performance Metrics — sub-models
# ===========================================================================


class PerformanceMetric(BaseModel):
    """Single performance metric measurement."""

    metric_name: str = ""  # accuracy, F1, AUROC, RMSE, BLEU, perplexity, etc.
    value: float | None = None
    dataset_split: str = ""  # train, validation, test, holdout
    threshold: float | None = None


class BaselineComparison(BaseModel):
    """Comparison against a baseline model."""

    baseline_model: str = ""
    baseline_value: float | None = None
    improvement_pct: float | None = None


# ===========================================================================
# Group 4: Deployment & Operations — sub-models
# ===========================================================================


class ServingInfrastructure(BaseModel):
    """Model serving infrastructure details."""

    serving_platform: str = ""  # SageMaker, Vertex AI, TorchServe, vLLM, etc.
    endpoint_url: str = ""
    latency_p50_ms: float | None = None
    latency_p99_ms: float | None = None
    throughput_rps: float | None = None
    auto_scaling: bool = False


# ===========================================================================
# Group 5: Fairness & Responsible AI — sub-models
# ===========================================================================


class FairnessMetric(BaseModel):
    """Fairness metric measurement for a protected attribute."""

    metric_name: str = ""  # demographic_parity, equalized_odds, calibration, etc.
    protected_attribute: str = ""  # gender, race, age, disability, etc.
    value: float | None = None
    threshold: float | None = None
    passes: bool | None = None


class NISTAIRMFProfile(BaseModel):
    """NIST AI RMF 1.0 maturity profile across four functions."""

    govern_maturity: str = ""  # Not Started, Partial, Managed, Measured, Optimized
    map_maturity: str = ""
    measure_maturity: str = ""
    manage_maturity: str = ""


# ===========================================================================
# AIModel entity
# ===========================================================================


class AIModel(BaseEntity):
    """An AI or machine learning model across its full lifecycle.

    Covers traditional ML, deep learning, foundation models, fine-tuned
    models, and agentic systems. Tracks training lineage, performance,
    deployment, fairness, governance, and GenAI-specific attributes.

    Aligns with NIST AI RMF 1.0 (GOVERN/MAP/MEASURE/MANAGE), EU AI Act
    risk categories, ISO/IEC 42001 AI management system, MLflow lifecycle
    stages, and CRISP-DM methodology phases.
    """

    ENTITY_TYPE: ClassVar[EntityType] = EntityType.AI_MODEL
    entity_type: Literal[EntityType.AI_MODEL] = EntityType.AI_MODEL

    # --- Group 1: Identity & Classification ---
    ai_model_id: str = ""  # Format: AIM-XXXXX
    # model_name inherits from BaseEntity.name
    model_type: str = ""  # classification, regression, clustering, NLP,
    # computer_vision, recommendation, generative, reinforcement_learning,
    # ensemble, other
    model_category: str = ""  # traditional_ml, deep_learning, llm,
    # foundation_model, fine_tuned, agent
    model_framework: str = ""  # pytorch, tensorflow, scikit_learn,
    # xgboost, huggingface, openai, anthropic, custom
    model_version: str = ""
    model_status: str = ""  # development, staging, production, retired, archived
    model_description_extended: str = ""
    functional_domain: str = ""  # Finance, Healthcare, Security, Operations, etc.
    taxonomy_lineage: list[TaxonomyLineageAIModel] = Field(default_factory=list)

    # --- Group 2: Training & Data Lineage ---
    training_data_refs: list[str] = Field(default_factory=list)  # list of data asset IDs
    training_data_description: str = ""
    feature_count: int | None = None
    training_sample_count: int | None = None
    training_compute: TrainingCompute | None = None
    training_started: str = ""
    training_completed: str = ""
    training_duration_hours: float | None = None
    hyperparameters: dict[str, str] = Field(default_factory=dict)
    preprocessing_pipeline: str = ""

    # --- Group 3: Performance Metrics ---
    primary_metric_name: str = ""  # accuracy, F1, AUROC, RMSE, BLEU, perplexity, etc.
    primary_metric_value: float | None = None
    performance_metrics: list[PerformanceMetric] = Field(default_factory=list)
    baseline_comparison: BaselineComparison | None = None
    validation_methodology: str = ""  # cross_validation, holdout, temporal, A/B_test
    last_evaluated_date: str = ""

    # --- Group 4: Deployment & Operations ---
    deployment_status: str = ""  # not_deployed, canary, shadow, blue_green, full_production
    deployment_target_system_id: str = ""  # ref to System entity
    serving_infrastructure: ServingInfrastructure | None = None
    inference_cost_per_1k: float | None = None
    monitoring_enabled: bool = False
    drift_detection_enabled: bool = False
    drift_status: str = ""  # no_drift, data_drift, concept_drift, both, not_monitored
    last_drift_check: str = ""
    model_health: str = ""  # healthy, degraded, critical, unknown
    rollback_version: str = ""

    # --- Group 5: Fairness & Responsible AI (EU AI Act + NIST AI RMF) ---
    eu_ai_act_risk_category: str = ""  # unacceptable, high, limited, minimal, not_classified
    nist_ai_rmf_profile: NISTAIRMFProfile | None = None
    bias_assessment_completed: bool = False
    fairness_metrics: list[FairnessMetric] = Field(default_factory=list)
    explainability_method: str = ""  # SHAP, LIME, attention_weights,
    # feature_importance, counterfactual, none
    explainability_documentation_url: str = ""
    human_oversight_required: bool = False
    human_in_the_loop: bool = False
    ethics_review_status: str = ""  # not_required, pending, approved, conditional, rejected
    ethics_review_date: str = ""
    ethics_reviewer: str = ""

    # --- Group 6: Governance & Ownership ---
    model_owner: str = ""
    technical_owner: str = ""
    business_owner: str = ""
    approval_status: str = ""  # draft, review, approved, deprecated
    approved_by: str = ""
    approval_date: str = ""
    model_card_url: str = ""  # per Google Model Cards standard
    documentation_completeness: str = ""  # full, partial, minimal, none

    # --- Group 7: GenAI-Specific Fields (Module 16) ---
    is_generative: bool = False
    base_model_provider: str = ""  # openai, anthropic, google, meta, mistral, custom
    base_model_name: str = ""
    context_window_tokens: int | None = None
    fine_tuning_method: str = ""  # full, LoRA, QLoRA, RLHF, DPO, none
    guardrails_enabled: bool = False
    guardrail_types: list[str] = Field(default_factory=list)
    # content_filter, pii_detection, prompt_injection, toxicity,
    # hallucination_check
    prompt_template_version: str = ""

    # --- Group 8: Financial Profile ---
    total_development_cost: float | None = None
    currency: str = "USD"
    annual_operating_cost: float | None = None
    projected_annual_value: float | None = None
    value_confidence: str = ""  # demonstrated, modeled, estimated, aspirational

    # --- Group 9: Dependencies & Relationships — typed edges ---
    trained_on_data_assets: list[str] = Field(default_factory=list)
    deployed_in_systems: list[str] = Field(default_factory=list)
    consumes_pipelines: list[str] = Field(default_factory=list)
    monitored_by_systems: list[str] = Field(default_factory=list)
    related_models: list[str] = Field(default_factory=list)
    serves_products: list[str] = Field(default_factory=list)

    # --- Group 10: Temporal & Provenance ---
    temporal_and_versioning: TemporalAndVersioning = Field(default_factory=TemporalAndVersioning)
    provenance_and_confidence: ProvenanceAndConfidence = Field(
        default_factory=ProvenanceAndConfidence
    )
