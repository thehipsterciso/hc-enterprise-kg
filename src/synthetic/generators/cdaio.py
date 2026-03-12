"""Generators for CDAIO entity types: AI Models, Data Products, Data Pipelines.

Each generator follows the coordinated template dict pattern (ADR-006):
no faker.sentence() or faker.bs() — all names and descriptions are
domain-specific and semantically coherent.
"""

from __future__ import annotations

import random

from domain.base import EntityType
from domain.entities.ai_model import (
    AIModel,
    BaselineComparison,
    FairnessMetric,
    NISTAIRMFProfile,
    PerformanceMetric,
    ServingInfrastructure,
    TrainingCompute,
)
from domain.entities.data_pipeline import (
    ComputeResource,
    DataPipeline,
    ExecutionFrequency,
    RetryPolicy,
)
from domain.entities.data_product import (
    DataProduct,
    DataProductSLA,
    QualityDimensions,
)
from domain.shared import ProvenanceAndConfidence, TemporalAndVersioning
from synthetic.base import AbstractGenerator, GenerationContext, GeneratorRegistry

# ---------------------------------------------------------------------------
# AI Model templates
# ---------------------------------------------------------------------------

# (name, model_type, framework, status, is_generative, eu_risk, functional_domain)
AI_MODEL_TEMPLATES: list[tuple[str, str, str, str, bool, str, str]] = [
    (
        "Customer Churn Predictor",
        "classification",
        "scikit_learn",
        "production",
        False,
        "limited",
        "Sales & Marketing",
    ),
    (
        "Revenue Forecasting Model",
        "regression",
        "xgboost",
        "production",
        False,
        "minimal",
        "Finance",
    ),
    (
        "Document Classification Engine",
        "NLP",
        "pytorch",
        "production",
        False,
        "limited",
        "Operations",
    ),
    (
        "Fraud Detection System",
        "classification",
        "tensorflow",
        "production",
        False,
        "high",
        "Finance",
    ),
    (
        "Customer Segmentation",
        "clustering",
        "scikit_learn",
        "production",
        False,
        "minimal",
        "Sales & Marketing",
    ),
    (
        "Sentiment Analysis Pipeline",
        "NLP",
        "huggingface",
        "staging",
        False,
        "limited",
        "Sales & Marketing",
    ),
    (
        "Demand Forecasting",
        "regression",
        "pytorch",
        "production",
        False,
        "minimal",
        "Operations",
    ),
    (
        "Image Quality Inspector",
        "computer_vision",
        "pytorch",
        "staging",
        False,
        "minimal",
        "Operations",
    ),
    (
        "Recommendation Engine",
        "recommendation",
        "tensorflow",
        "production",
        False,
        "limited",
        "Sales & Marketing",
    ),
    (
        "Enterprise ChatBot",
        "generative",
        "anthropic",
        "production",
        True,
        "limited",
        "Operations",
    ),
    (
        "Code Review Assistant",
        "generative",
        "openai",
        "staging",
        True,
        "minimal",
        "Technology",
    ),
    (
        "Risk Scoring Model",
        "classification",
        "xgboost",
        "production",
        False,
        "high",
        "Finance",
    ),
]

# Overflow name fragments for generating beyond template count
_AI_MODEL_OVERFLOW_PREFIXES = [
    "Anomaly Detection",
    "Propensity Scoring",
    "Price Optimization",
    "Inventory Prediction",
    "Compliance Screening",
    "Workforce Planning",
    "Supply Chain Forecast",
    "Credit Risk Assessment",
    "Patient Readmission",
    "Claims Adjudication",
]

_AI_MODEL_OVERFLOW_SUFFIXES = ["Model", "Engine", "Classifier", "Predictor", "System"]

# Framework → category mapping
_FRAMEWORK_CATEGORY: dict[str, str] = {
    "scikit_learn": "traditional_ml",
    "xgboost": "traditional_ml",
    "pytorch": "deep_learning",
    "tensorflow": "deep_learning",
    "huggingface": "foundation_model",
    "openai": "llm",
    "anthropic": "llm",
    "custom": "traditional_ml",
}

# Framework → serving platform mapping
_FRAMEWORK_SERVING: dict[str, list[str]] = {
    "scikit_learn": ["SageMaker", "Vertex AI", "MLflow"],
    "xgboost": ["SageMaker", "Vertex AI", "MLflow"],
    "pytorch": ["TorchServe", "SageMaker", "Vertex AI"],
    "tensorflow": ["TensorFlow Serving", "SageMaker", "Vertex AI"],
    "huggingface": ["vLLM", "SageMaker", "Vertex AI"],
    "openai": ["Azure OpenAI", "OpenAI API"],
    "anthropic": ["Amazon Bedrock", "Anthropic API"],
    "custom": ["SageMaker", "Kubernetes"],
}

# Model type → primary metric mapping
_MODEL_TYPE_METRICS: dict[str, tuple[str, float, float]] = {
    "classification": ("F1", 0.70, 0.98),
    "regression": ("RMSE", 0.01, 0.15),
    "clustering": ("silhouette_score", 0.40, 0.85),
    "NLP": ("F1", 0.75, 0.95),
    "computer_vision": ("mAP", 0.65, 0.95),
    "recommendation": ("NDCG@10", 0.30, 0.80),
    "generative": ("perplexity", 3.0, 25.0),
    "reinforcement_learning": ("cumulative_reward", 50.0, 500.0),
    "ensemble": ("accuracy", 0.80, 0.99),
}

# NIST AI RMF maturity choices
_NIST_MATURITY = ["Not Started", "Partial", "Managed", "Measured", "Optimized"]

# ---------------------------------------------------------------------------
# Data Product templates
# ---------------------------------------------------------------------------

# (name, dp_type, tier, maturity, functional_area)
DATA_PRODUCT_TEMPLATES: list[tuple[str, str, str, str, str]] = [
    (
        "Customer 360 Dataset",
        "dataset",
        "gold",
        "ga",
        "Sales & Marketing",
    ),
    (
        "Real-Time Revenue Dashboard",
        "dashboard",
        "gold",
        "ga",
        "Finance",
    ),
    (
        "Employee Skills API",
        "api",
        "silver",
        "ga",
        "HR",
    ),
    (
        "Vendor Risk Score Feed",
        "stream",
        "gold",
        "ga",
        "Risk & Compliance",
    ),
    (
        "Product Analytics Dataset",
        "dataset",
        "silver",
        "ga",
        "Product",
    ),
    (
        "Regulatory Compliance Report",
        "report",
        "gold",
        "ga",
        "Risk & Compliance",
    ),
    (
        "ML Feature Store — Customer",
        "feature_store",
        "gold",
        "beta",
        "Technology",
    ),
    (
        "Market Intelligence Feed",
        "stream",
        "silver",
        "ga",
        "Sales & Marketing",
    ),
]

# Overflow fragments
_DP_OVERFLOW_NAMES: list[tuple[str, str, str]] = [
    ("Supply Chain Metrics", "dataset", "silver"),
    ("Financial Close Package", "report", "gold"),
    ("Customer Lifetime Value", "dataset", "gold"),
    ("Operational KPI Dashboard", "dashboard", "silver"),
    ("Identity Resolution API", "api", "gold"),
    ("Patient Cohort Dataset", "dataset", "gold"),
    ("Claims Analytics Report", "report", "silver"),
    ("IoT Telemetry Feed", "stream", "bronze"),
    ("Fraud Signals Feature Store", "feature_store", "gold"),
    ("Campaign Attribution Dataset", "dataset", "silver"),
]

# Data product type → access protocol mapping
_DP_TYPE_PROTOCOL: dict[str, list[str]] = {
    "dataset": ["file_share", "query", "sdk"],
    "api": ["api"],
    "stream": ["streaming", "webhook"],
    "report": ["file_share", "query"],
    "dashboard": ["query"],
    "feature_store": ["api", "sdk"],
    "ml_feature": ["api", "sdk"],
    "derived_metric": ["api", "query"],
}

# Data product type → data format mapping
_DP_TYPE_FORMAT: dict[str, list[str]] = {
    "dataset": ["parquet", "avro", "csv"],
    "api": ["json", "protobuf", "graphql"],
    "stream": ["json", "avro", "protobuf"],
    "report": ["csv", "json"],
    "dashboard": ["json"],
    "feature_store": ["parquet", "json"],
    "ml_feature": ["parquet", "json"],
    "derived_metric": ["json"],
}

# Data product type → update frequency mapping
_DP_TYPE_FREQUENCY: dict[str, list[str]] = {
    "dataset": ["daily", "weekly", "monthly"],
    "api": ["real_time", "near_real_time"],
    "stream": ["real_time", "near_real_time"],
    "report": ["daily", "weekly", "monthly"],
    "dashboard": ["near_real_time", "hourly"],
    "feature_store": ["hourly", "daily"],
    "ml_feature": ["hourly", "daily"],
    "derived_metric": ["hourly", "daily"],
}

# ---------------------------------------------------------------------------
# Data Pipeline templates
# ---------------------------------------------------------------------------

# (name, pipeline_type, pattern, orchestration, status, functional_domain)
DATA_PIPELINE_TEMPLATES: list[tuple[str, str, str, str, str, str]] = [
    (
        "Customer Data Ingestion",
        "etl",
        "batch",
        "airflow",
        "active",
        "Sales & Marketing",
    ),
    (
        "Real-Time Transaction Stream",
        "streaming",
        "kappa",
        "custom",
        "active",
        "Finance",
    ),
    (
        "Data Warehouse Refresh",
        "elt",
        "medallion",
        "dbt_cloud",
        "active",
        "Technology",
    ),
    (
        "ML Feature Engineering",
        "etl",
        "hub_spoke",
        "prefect",
        "active",
        "Technology",
    ),
    (
        "Regulatory Report Builder",
        "batch",
        "fan_out",
        "airflow",
        "active",
        "Risk & Compliance",
    ),
    (
        "Data Quality Monitor",
        "data_quality",
        "fan_in",
        "great_expectations",
        "active",
        "Technology",
    ),
    (
        "Vendor Data Sync",
        "cdc",
        "hub_spoke",
        "dagster",
        "active",
        "Operations",
    ),
    (
        "Analytics Mart Refresh",
        "elt",
        "medallion",
        "dbt_cloud",
        "active",
        "Technology",
    ),
]

# Overflow fragments
_PIPELINE_OVERFLOW_NAMES: list[tuple[str, str, str, str]] = [
    ("Patient Record ETL", "etl", "batch", "airflow"),
    ("Clickstream Ingestor", "streaming", "kappa", "custom"),
    ("Financial Close Pipeline", "elt", "medallion", "dbt_cloud"),
    ("Claims Processing Pipeline", "batch", "fan_out", "airflow"),
    ("IoT Sensor Collector", "streaming", "lambda", "custom"),
    ("HR Data Synchronization", "cdc", "hub_spoke", "dagster"),
    ("Compliance Evidence Collector", "batch", "fan_in", "airflow"),
    ("Product Catalog Sync", "cdc", "hub_spoke", "prefect"),
    ("Marketing Attribution Pipeline", "etl", "batch", "prefect"),
    ("Risk Score Calculator", "etl", "hub_spoke", "airflow"),
]

# Pipeline type → transformation language mapping
_PIPELINE_TYPE_LANGUAGE: dict[str, list[str]] = {
    "etl": ["python", "spark", "sql"],
    "elt": ["sql", "dbt"],
    "streaming": ["python", "spark", "custom"],
    "batch": ["python", "sql", "spark"],
    "micro_batch": ["spark", "python"],
    "cdc": ["sql", "custom"],
    "reverse_etl": ["sql", "python"],
    "ml_training": ["python", "spark"],
    "ml_inference": ["python"],
    "data_quality": ["python", "sql"],
}

# Pipeline type → quality framework mapping
_PIPELINE_QUALITY_FRAMEWORK: dict[str, list[str]] = {
    "etl": ["great_expectations", "dbt_tests", "custom"],
    "elt": ["dbt_tests", "soda", "great_expectations"],
    "streaming": ["custom", "soda"],
    "batch": ["great_expectations", "custom"],
    "micro_batch": ["custom", "soda"],
    "cdc": ["custom"],
    "reverse_etl": ["custom", "dbt_tests"],
    "ml_training": ["custom"],
    "ml_inference": ["custom"],
    "data_quality": ["great_expectations", "soda"],
}

# Orchestration → CI/CD platform mapping
_ORCH_CICD: dict[str, list[str]] = {
    "airflow": ["github_actions", "gitlab_ci"],
    "prefect": ["github_actions"],
    "dagster": ["github_actions", "gitlab_ci"],
    "dbt_cloud": ["github_actions"],
    "great_expectations": ["github_actions"],
    "custom": ["github_actions", "jenkins", "gitlab_ci"],
    "step_functions": ["github_actions"],
    "mage": ["github_actions"],
}

# Cron schedule templates for different pipeline patterns
_CRON_SCHEDULES: dict[str, list[str]] = {
    "batch": ["0 2 * * *", "0 6 * * *", "0 0 * * 0", "0 0 1 * *"],
    "medallion": ["0 3 * * *", "0 */4 * * *"],
    "hub_spoke": ["0 1 * * *", "0 */6 * * *"],
    "fan_out": ["0 5 * * *", "0 4 * * 1"],
    "fan_in": ["30 6 * * *", "0 7 * * *"],
    "kappa": [],  # streaming — no cron
    "lambda": [],  # streaming — no cron
}


# ---------------------------------------------------------------------------
# CDAIO Generators
# ---------------------------------------------------------------------------


@GeneratorRegistry.register
class AIModelGenerator(AbstractGenerator):
    """Generates AIModel entities with coherent lifecycle and governance attributes.

    Templates cover classification, regression, NLP, computer vision,
    recommendation, and generative models. Includes EU AI Act risk
    categories, NIST AI RMF maturity, fairness metrics, and deployment status.
    """

    GENERATES = EntityType.AI_MODEL

    def generate(self, count: int, context: GenerationContext) -> list[AIModel]:
        faker = context.faker
        data_assets = context.get_entities(EntityType.DATA_ASSET)
        systems = context.get_entities(EntityType.SYSTEM)
        departments = context.get_entities(EntityType.DEPARTMENT)
        models: list[AIModel] = []

        selected = random.sample(AI_MODEL_TEMPLATES, k=min(count, len(AI_MODEL_TEMPLATES)))

        for i in range(count):
            if i < len(selected):
                name, model_type, framework, status, is_gen, eu_risk, func_domain = selected[i]
            else:
                # Overflow: generate coherent names from fragments
                prefix = random.choice(_AI_MODEL_OVERFLOW_PREFIXES)
                suffix = random.choice(_AI_MODEL_OVERFLOW_SUFFIXES)
                name = f"{prefix} {suffix}"
                model_type = random.choice(["classification", "regression", "NLP", "clustering"])
                framework = random.choice(["scikit_learn", "xgboost", "pytorch", "tensorflow"])
                status = random.choice(["production", "staging", "development"])
                is_gen = False
                eu_risk = random.choice(["minimal", "limited", "high"])
                func_domain = random.choice(
                    ["Finance", "Operations", "Technology", "Sales & Marketing"]
                )

            category = _FRAMEWORK_CATEGORY.get(framework, "traditional_ml")

            # Primary metric from model type
            metric_name, metric_low, metric_high = _MODEL_TYPE_METRICS.get(
                model_type, ("accuracy", 0.70, 0.99)
            )
            primary_metric_value = round(random.uniform(metric_low, metric_high), 4)

            # Training data references
            training_refs: list[str] = []
            if data_assets:
                ref_count = min(random.randint(1, 3), len(data_assets))
                training_refs = [da.id for da in random.sample(data_assets, ref_count)]

            # Deployment target
            deploy_system_id = ""
            if systems and status in ("production", "staging"):
                deploy_system_id = random.choice(systems).id

            # Model owner from departments
            model_owner = ""
            if departments:
                owner_dept = random.choice(departments)
                model_owner = f"{owner_dept.name} Data Science"

            # Serving infrastructure
            serving_platform = random.choice(_FRAMEWORK_SERVING.get(framework, ["SageMaker"]))
            serving = ServingInfrastructure(
                serving_platform=serving_platform,
                latency_p50_ms=round(random.uniform(5, 200), 1),
                latency_p99_ms=round(random.uniform(50, 2000), 1),
                throughput_rps=round(random.uniform(10, 5000), 0),
                auto_scaling=status == "production",
            )

            # Training compute
            gpu_type = random.choice(["A100", "H100", "V100", "T4"])
            training_compute = TrainingCompute(
                gpu_type=gpu_type,
                gpu_hours=round(random.uniform(1, 500), 1),
                cloud_provider=random.choice(["AWS", "GCP", "Azure"]),
                estimated_cost=round(random.uniform(100, 50000), 2),
            )

            # Fairness metrics (for high-risk models)
            fairness_metrics: list[FairnessMetric] = []
            if eu_risk in ("high",):
                for attr in ["gender", "age"]:
                    fairness_metrics.append(
                        FairnessMetric(
                            metric_name="demographic_parity",
                            protected_attribute=attr,
                            value=round(random.uniform(0.80, 1.0), 3),
                            threshold=0.80,
                            passes=True,
                        )
                    )

            # GenAI-specific fields
            base_provider = ""
            base_model_name = ""
            context_window = None
            guardrails = False
            guardrail_types: list[str] = []
            if is_gen:
                base_provider = framework  # openai or anthropic
                base_model_name = {
                    "openai": "gpt-4",
                    "anthropic": "claude-3-opus",
                }.get(framework, "custom")
                context_window = random.choice([4096, 8192, 32768, 128000, 200000])
                guardrails = True
                guardrail_types = random.sample(
                    [
                        "content_filter",
                        "pii_detection",
                        "prompt_injection",
                        "toxicity",
                        "hallucination_check",
                    ],
                    k=random.randint(2, 4),
                )

            model = AIModel(
                name=name,
                description=f"{model_type.replace('_', ' ').title()} model: {name}",
                ai_model_id=f"AIM-{i + 1:05d}",
                model_type=model_type,
                model_category=category,
                model_framework=framework,
                model_version=(
                    f"{random.randint(1, 5)}.{random.randint(0, 9)}.{random.randint(0, 9)}"
                ),
                model_status=status,
                functional_domain=func_domain,
                # Training & data lineage
                training_data_refs=training_refs,
                training_data_description=f"Training dataset for {name}",
                feature_count=random.randint(10, 500) if not is_gen else None,
                training_sample_count=random.randint(10000, 5000000) if not is_gen else None,
                training_compute=training_compute,
                training_duration_hours=round(random.uniform(0.5, 200), 1),
                # Performance
                primary_metric_name=metric_name,
                primary_metric_value=primary_metric_value,
                performance_metrics=[
                    PerformanceMetric(
                        metric_name=metric_name,
                        value=primary_metric_value,
                        dataset_split="test",
                    ),
                ],
                baseline_comparison=BaselineComparison(
                    baseline_model="Previous Version",
                    improvement_pct=round(random.uniform(1, 15), 1),
                ),
                validation_methodology=random.choice(
                    ["cross_validation", "holdout", "temporal", "A/B_test"]
                ),
                # Deployment & operations
                deployment_status="full_production"
                if status == "production"
                else ("canary" if status == "staging" else "not_deployed"),
                deployment_target_system_id=deploy_system_id,
                serving_infrastructure=serving,
                inference_cost_per_1k=round(random.uniform(0.01, 5.0), 3),
                monitoring_enabled=status == "production",
                drift_detection_enabled=status == "production",
                drift_status="no_drift" if status == "production" else "not_monitored",
                model_health="healthy" if status == "production" else "unknown",
                # Fairness & responsible AI
                eu_ai_act_risk_category=eu_risk,
                nist_ai_rmf_profile=NISTAIRMFProfile(
                    govern_maturity=random.choice(_NIST_MATURITY),
                    map_maturity=random.choice(_NIST_MATURITY),
                    measure_maturity=random.choice(_NIST_MATURITY),
                    manage_maturity=random.choice(_NIST_MATURITY),
                ),
                bias_assessment_completed=eu_risk in ("high", "limited"),
                fairness_metrics=fairness_metrics,
                explainability_method=random.choice(
                    ["SHAP", "LIME", "feature_importance", "attention_weights"]
                )
                if not is_gen
                else "attention_weights",
                human_oversight_required=eu_risk == "high",
                ethics_review_status=random.choice(["approved", "pending", "not_required"]),
                # Governance & ownership
                model_owner=model_owner or faker.name(),
                technical_owner=faker.name(),
                business_owner=faker.name(),
                approval_status="approved" if status == "production" else "review",
                documentation_completeness=random.choice(["full", "partial", "minimal"]),
                # GenAI fields
                is_generative=is_gen,
                base_model_provider=base_provider,
                base_model_name=base_model_name,
                context_window_tokens=context_window,
                guardrails_enabled=guardrails,
                guardrail_types=guardrail_types,
                # Financial profile
                total_development_cost=round(random.uniform(10000, 500000), 2),
                annual_operating_cost=round(random.uniform(5000, 200000), 2),
                projected_annual_value=round(random.uniform(50000, 5000000), 2),
                value_confidence=random.choice(
                    ["demonstrated", "modeled", "estimated", "aspirational"]
                ),
                # Relationship refs
                trained_on_data_assets=training_refs,
                deployed_in_systems=[deploy_system_id] if deploy_system_id else [],
                # Temporal & provenance
                temporal_and_versioning=TemporalAndVersioning(schema_version="1.0.0"),
                provenance_and_confidence=ProvenanceAndConfidence(
                    primary_data_source="ML Platform",
                    confidence_level=random.choice(["Verified", "High"]),
                ),
                tags=[
                    model_type.lower().replace(" ", "-"),
                    framework.lower(),
                    eu_risk,
                ],
            )
            models.append(model)

        context.store(EntityType.AI_MODEL, models)
        return models


@GeneratorRegistry.register
class DataProductGenerator(AbstractGenerator):
    """Generates DataProduct entities with coherent ownership and quality attributes.

    Templates cover datasets, APIs, streams, dashboards, reports,
    and feature stores. Includes FAIR scores, monetization status,
    SLA targets, and quality dimensions.
    """

    GENERATES = EntityType.DATA_PRODUCT

    def generate(self, count: int, context: GenerationContext) -> list[DataProduct]:
        faker = context.faker
        data_assets = context.get_entities(EntityType.DATA_ASSET)
        systems = context.get_entities(EntityType.SYSTEM)
        data_domains = context.get_entities(EntityType.DATA_DOMAIN)
        products: list[DataProduct] = []

        selected = random.sample(DATA_PRODUCT_TEMPLATES, k=min(count, len(DATA_PRODUCT_TEMPLATES)))

        for i in range(count):
            if i < len(selected):
                name, dp_type, tier, maturity, func_area = selected[i]
            else:
                # Overflow: pick from overflow pool or recombine
                overflow_idx = (i - len(selected)) % len(_DP_OVERFLOW_NAMES)
                overflow = _DP_OVERFLOW_NAMES[overflow_idx]
                name = overflow[0]
                dp_type = overflow[1]
                tier = overflow[2]
                maturity = random.choice(["ga", "beta", "development"])
                func_area = random.choice(
                    [
                        "Finance",
                        "Operations",
                        "Technology",
                        "Sales & Marketing",
                        "HR",
                    ]
                )

            # Source data asset references
            source_refs: list[str] = []
            if data_assets:
                ref_count = min(random.randint(1, 4), len(data_assets))
                source_refs = [da.id for da in random.sample(data_assets, ref_count)]

            # Source system references
            source_sys: list[str] = []
            if systems:
                sys_count = min(random.randint(1, 3), len(systems))
                source_sys = [s.id for s in random.sample(systems, sys_count)]

            # Domain reference
            domain_name = ""
            if data_domains:
                domain_name = random.choice(data_domains).name

            # Access protocol and format from type
            access_protocol = random.choice(_DP_TYPE_PROTOCOL.get(dp_type, ["api"]))
            data_format = random.choice(_DP_TYPE_FORMAT.get(dp_type, ["json"]))
            update_frequency = random.choice(_DP_TYPE_FREQUENCY.get(dp_type, ["daily"]))

            # Quality scores
            completeness = round(random.uniform(0.85, 1.0), 2)
            accuracy = round(random.uniform(0.90, 1.0), 2)
            quality_score = round((completeness + accuracy) / 2, 2)

            # Consumer count — gold tier products have more consumers
            consumer_base = {"gold": (5, 50), "silver": (2, 20), "bronze": (1, 10)}
            c_low, c_high = consumer_base.get(tier, (1, 15))
            consumer_count = random.randint(c_low, c_high)

            # SLA targets — gold tier has stricter SLAs
            sla_availability = {"gold": 99.9, "silver": 99.5, "bronze": 99.0}
            freshness_map = {
                "real_time": "< 1 minute",
                "near_real_time": "< 15 minutes",
                "hourly": "< 1 hour",
                "daily": "daily by 06:00 UTC",
                "weekly": "weekly by Monday 06:00 UTC",
                "monthly": "by 2nd business day",
                "on_demand": "< 30 minutes",
            }
            sla = DataProductSLA(
                availability_pct=sla_availability.get(tier, 99.0),
                freshness_target=freshness_map.get(update_frequency, "daily by 06:00 UTC"),
                support_hours="24x7" if tier == "gold" else "business hours",
            )

            # FAIR scores — ga products tend to score higher
            fair_base = 0.7 if maturity == "ga" else 0.4
            findable = round(random.uniform(fair_base, min(1.0, fair_base + 0.25)), 2)
            accessible = round(random.uniform(fair_base, min(1.0, fair_base + 0.25)), 2)
            interoperable = round(random.uniform(fair_base, min(1.0, fair_base + 0.25)), 2)
            reusable = round(random.uniform(fair_base, min(1.0, fair_base + 0.25)), 2)

            # Data classification from tier
            classification = {
                "gold": random.choice(["confidential", "internal"]),
                "silver": random.choice(["internal", "confidential"]),
                "bronze": random.choice(["internal", "public"]),
            }.get(tier, "internal")

            product = DataProduct(
                name=name,
                description=f"{dp_type.replace('_', ' ').title()} data product: {name}",
                data_product_id=f"DPR-{i + 1:05d}",
                data_product_type=dp_type,
                domain=domain_name,
                functional_area=func_area,
                maturity=maturity,
                visibility="internal" if classification != "public" else "public",
                data_product_tier=tier,
                # Ownership
                product_owner_role=f"{func_area} Data Product Owner",
                technical_steward=faker.name(),
                domain_owner=faker.name(),
                support_team=f"{func_area} Data Engineering",
                data_product_sla=sla,
                # Data characteristics
                source_data_assets=source_refs,
                update_frequency=update_frequency,
                data_format=data_format,
                schema_version="1.0.0",
                volume_gb=round(random.uniform(0.1, 500), 1),
                row_count=random.randint(1000, 50000000),
                quality_score=quality_score,
                # Access & distribution
                access_protocol=access_protocol,
                authentication_method=random.choice(["oauth2", "api_key", "iam_role"]),
                consumer_count=consumer_count,
                self_service_enabled=maturity == "ga",
                # Quality & contracts
                quality_dimensions=QualityDimensions(
                    completeness_pct=completeness * 100,
                    accuracy_pct=accuracy * 100,
                    timeliness_score=round(random.uniform(0.8, 1.0), 2),
                    consistency_score=round(random.uniform(0.85, 1.0), 2),
                    uniqueness_pct=round(random.uniform(95, 100), 1),
                ),
                quality_monitoring_enabled=maturity == "ga",
                data_contract_version="1.0" if maturity == "ga" else "",
                breaking_change_policy="versioned" if tier == "gold" else "backward_compatible",
                quality_trend=random.choice(["improving", "stable", "declining"]),
                incidents_last_90_days=random.randint(0, 5),
                # Monetization & value
                monetization_status=random.choice(
                    [
                        "not_monetized",
                        "internal_value",
                        "cost_avoidance",
                        "indirect_revenue",
                    ]
                ),
                estimated_annual_value=round(random.uniform(10000, 2000000), 2),
                cost_to_produce=round(random.uniform(5000, 200000), 2),
                value_confidence=random.choice(["demonstrated", "modeled", "estimated"]),
                # Compliance
                contains_pii=classification in ("confidential", "restricted"),
                data_classification=classification,
                # FAIR scores
                findable_score=findable,
                accessible_score=accessible,
                interoperable_score=interoperable,
                reusable_score=reusable,
                # Relationship refs
                source_systems=source_sys,
                # Temporal & provenance
                temporal_and_versioning=TemporalAndVersioning(schema_version="1.0.0"),
                provenance_and_confidence=ProvenanceAndConfidence(
                    primary_data_source="Data Product Catalog",
                    confidence_level=random.choice(["Verified", "High"]),
                ),
                tags=[
                    dp_type.lower().replace(" ", "-"),
                    tier,
                    func_area.lower().replace(" & ", "-").replace(" ", "-"),
                ],
            )
            products.append(product)

        context.store(EntityType.DATA_PRODUCT, products)
        return products


@GeneratorRegistry.register
class DataPipelineGenerator(AbstractGenerator):
    """Generates DataPipeline entities with coherent orchestration and quality attributes.

    Templates cover ETL, ELT, streaming, CDC, batch, and data quality
    pipelines. Includes SLA targets, quality check counts, CI/CD status,
    and compute cost estimates.
    """

    GENERATES = EntityType.DATA_PIPELINE

    def generate(self, count: int, context: GenerationContext) -> list[DataPipeline]:
        faker = context.faker
        systems = context.get_entities(EntityType.SYSTEM)
        data_assets = context.get_entities(EntityType.DATA_ASSET)
        pipelines: list[DataPipeline] = []

        selected = random.sample(
            DATA_PIPELINE_TEMPLATES, k=min(count, len(DATA_PIPELINE_TEMPLATES))
        )

        for i in range(count):
            if i < len(selected):
                name, p_type, pattern, orch, status, func_domain = selected[i]
            else:
                # Overflow: pick from overflow pool
                overflow_idx = (i - len(selected)) % len(_PIPELINE_OVERFLOW_NAMES)
                overflow = _PIPELINE_OVERFLOW_NAMES[overflow_idx]
                name = overflow[0]
                p_type = overflow[1]
                pattern = overflow[2]
                orch = overflow[3]
                status = random.choice(["active", "paused", "development"])
                func_domain = random.choice(
                    ["Finance", "Operations", "Technology", "Sales & Marketing"]
                )

            # Source and target system references
            source_sys: list[str] = []
            target_sys: list[str] = []
            if systems and len(systems) >= 2:
                sampled = random.sample(systems, min(4, len(systems)))
                mid = len(sampled) // 2
                source_sys = [s.id for s in sampled[:mid]]
                target_sys = [s.id for s in sampled[mid:]]
            elif systems:
                source_sys = [systems[0].id]

            # Source data asset references
            source_da: list[str] = []
            target_da: list[str] = []
            if data_assets and len(data_assets) >= 2:
                sampled_da = random.sample(data_assets, min(4, len(data_assets)))
                mid_da = len(sampled_da) // 2
                source_da = [da.id for da in sampled_da[:mid_da]]
                target_da = [da.id for da in sampled_da[mid_da:]]

            # Transformation language from pipeline type
            transform_lang = random.choice(_PIPELINE_TYPE_LANGUAGE.get(p_type, ["python"]))

            # Quality framework from pipeline type
            quality_fw = random.choice(_PIPELINE_QUALITY_FRAMEWORK.get(p_type, ["custom"]))
            quality_check_count = random.randint(5, 50)
            quality_pass_rate = round(random.uniform(90, 100), 1)

            # Trigger type — streaming pipelines are event-driven
            is_streaming = p_type in ("streaming", "cdc")
            trigger_type = (
                "event_driven"
                if is_streaming
                else random.choice(["scheduled", "dependency", "on_demand"])
            )

            # Cron schedule — only for non-streaming
            cron = ""
            if not is_streaming:
                cron_pool = _CRON_SCHEDULES.get(pattern, ["0 2 * * *"])
                cron = random.choice(cron_pool) if cron_pool else ""

            # Pipeline tier from pattern
            tier = {
                "medallion": random.choice(["bronze", "silver", "gold"]),
                "kappa": "silver",
                "lambda": "silver",
                "hub_spoke": "silver",
                "fan_out": random.choice(["silver", "gold"]),
                "fan_in": random.choice(["silver", "gold"]),
                "batch": "bronze",
            }.get(pattern, "bronze")

            # Runtime — streaming pipelines run continuously
            avg_runtime = round(random.uniform(5, 120), 1) if not is_streaming else None
            p95_runtime = round(avg_runtime * random.uniform(1.5, 3.0), 1) if avg_runtime else None

            # Execution frequency
            exec_freq = ExecutionFrequency(
                schedule=cron,
                typical_duration_minutes=avg_runtime,
                last_run_status=random.choice(
                    ["success", "success", "success", "failed", "partial"]
                )
                if not is_streaming
                else "running",
            )

            # Compute resources
            compute = ComputeResource(
                compute_type=random.choice(["spark", "kubernetes", "ecs", "lambda"])
                if not is_streaming
                else random.choice(["spark", "kubernetes"]),
                auto_scaling=status == "active",
            )

            # Retry policy
            retry = RetryPolicy(
                max_retries=random.choice([3, 5]),
                backoff_strategy=random.choice(["exponential", "fixed"]),
            )

            # SLA target — lower for streaming (measured in minutes)
            sla_minutes = (
                random.choice([5, 10, 15]) if is_streaming else random.choice([60, 120, 240, 480])
            )

            # Monthly compute cost
            monthly_cost = round(random.uniform(50, 15000), 2)

            # CI/CD
            ci_cd_platform = random.choice(_ORCH_CICD.get(orch, ["github_actions"]))
            ci_cd_enabled = status in ("active", "testing")

            pipeline = DataPipeline(
                name=name,
                description=f"{p_type.upper()} pipeline: {name}",
                pipeline_id=f"DPL-{i + 1:05d}",
                pipeline_type=p_type,
                pipeline_pattern=pattern,
                orchestration_platform=orch,
                pipeline_status=status,
                functional_domain=func_domain,
                pipeline_tier=tier,
                cron_schedule=cron,
                trigger_type=trigger_type,
                # Source & target
                source_systems=source_sys,
                source_data_assets=source_da,
                target_systems=target_sys,
                target_data_assets=target_da,
                transformation_count=random.randint(3, 30),
                transformation_language=transform_lang,
                transformation_complexity=random.choice(["simple", "moderate", "complex"]),
                # Execution profile
                execution_frequency=exec_freq,
                average_runtime_minutes=avg_runtime,
                p95_runtime_minutes=p95_runtime,
                compute_resource=compute,
                data_volume_per_run_gb=round(random.uniform(0.01, 100), 2),
                rows_processed_per_run=random.randint(1000, 10000000),
                retry_policy=retry,
                idempotent=random.choice([True, True, False]),
                # Quality & observability
                quality_checks_enabled=True,
                quality_framework=quality_fw,
                quality_check_count=quality_check_count,
                quality_pass_rate_pct=quality_pass_rate,
                observability_enabled=status == "active",
                alerting_channels=random.sample(
                    ["slack", "pagerduty", "email"], k=random.randint(1, 3)
                ),
                sla_target_minutes=sla_minutes,
                sla_breach_count_30d=random.choice([0, 0, 0, 1, 2]),
                data_lineage_tracked=True,
                # CI/CD & version control
                version_controlled=True,
                ci_cd_enabled=ci_cd_enabled,
                ci_cd_platform=ci_cd_platform,
                test_coverage_pct=round(random.uniform(40, 95), 1),
                deployment_strategy=random.choice(["blue_green", "canary", "rolling", "direct"]),
                # Cost & performance
                monthly_compute_cost=monthly_cost,
                cost_per_gb_processed=round(monthly_cost / max(1, random.uniform(10, 500)), 3),
                cost_trend=random.choice(["increasing", "stable", "decreasing"]),
                # Governance & ownership
                pipeline_owner=faker.name(),
                technical_owner=faker.name(),
                data_steward=faker.name(),
                approval_required_for_changes=tier in ("silver", "gold"),
                # Temporal & provenance
                temporal_and_versioning=TemporalAndVersioning(schema_version="1.0.0"),
                provenance_and_confidence=ProvenanceAndConfidence(
                    primary_data_source="DataOps Platform",
                    confidence_level=random.choice(["Verified", "High"]),
                ),
                tags=[
                    p_type.lower(),
                    orch.lower().replace("_", "-"),
                    func_domain.lower().replace(" & ", "-").replace(" ", "-"),
                ],
            )
            pipelines.append(pipeline)

        context.store(EntityType.DATA_PIPELINE, pipelines)
        return pipelines
