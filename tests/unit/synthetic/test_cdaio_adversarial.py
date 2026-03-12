"""Adversarial tests for CDAIO entity types, generators, weavers, and integration points.

Tests probe failure modes:
1. Sub-model serialization round-trip (JSON → Pydantic → JSON)
2. Extra field leakage via extra="allow"
3. Generator overflow logic at scale
4. Weaver empty-list edge cases
5. Relationship schema validation for all 8 new types
6. Discriminated union dispatch for AnyEntity
7. Generator field correctness — no extras leaking
8. Edge cases in template selection and overflow naming
"""

from __future__ import annotations

import json
import random

import pytest

from domain.base import BaseEntity, EntityType, RelationshipType
from domain.entities import AnyEntity
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
from domain.registry import EntityRegistry
from domain.relationship_schema import validate_relationship
from domain.shared import ProvenanceAndConfidence, TemporalAndVersioning

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_ai_model(**overrides) -> AIModel:
    """Create a minimal valid AIModel with optional overrides."""
    defaults = dict(
        name="Test Model",
        description="Test AI model",
        ai_model_id="AIM-00001",
        model_type="classification",
        model_category="traditional_ml",
        model_framework="scikit_learn",
        model_status="production",
    )
    defaults.update(overrides)
    return AIModel(**defaults)


def _make_data_product(**overrides) -> DataProduct:
    """Create a minimal valid DataProduct with optional overrides."""
    defaults = dict(
        name="Test Product",
        description="Test data product",
        data_product_id="DPR-00001",
        data_product_type="dataset",
        maturity="ga",
        data_product_tier="gold",
    )
    defaults.update(overrides)
    return DataProduct(**defaults)


def _make_data_pipeline(**overrides) -> DataPipeline:
    """Create a minimal valid DataPipeline with optional overrides."""
    defaults = dict(
        name="Test Pipeline",
        description="Test data pipeline",
        pipeline_id="DPL-00001",
        pipeline_type="etl",
        pipeline_pattern="medallion",
        orchestration_platform="airflow",
        pipeline_status="active",
    )
    defaults.update(overrides)
    return DataPipeline(**defaults)


# ===========================================================================
# 1. Sub-model serialization round-trip
# ===========================================================================


class TestAIModelSerializationRoundTrip:
    """AIModel with all sub-models must survive JSON round-trip."""

    def test_full_submodel_round_trip(self):
        """Create AIModel with every sub-model populated, serialize, deserialize."""
        model = _make_ai_model(
            training_compute=TrainingCompute(
                gpu_type="A100",
                gpu_hours=42.5,
                cloud_provider="AWS",
                estimated_cost=15000.00,
                carbon_footprint_kg=123.4,
            ),
            performance_metrics=[
                PerformanceMetric(
                    metric_name="F1",
                    value=0.92,
                    dataset_split="test",
                    threshold=0.80,
                ),
                PerformanceMetric(
                    metric_name="accuracy",
                    value=0.95,
                    dataset_split="validation",
                ),
            ],
            baseline_comparison=BaselineComparison(
                baseline_model="v1.0",
                baseline_value=0.85,
                improvement_pct=8.2,
            ),
            serving_infrastructure=ServingInfrastructure(
                serving_platform="SageMaker",
                endpoint_url="https://model.example.com",
                latency_p50_ms=25.5,
                latency_p99_ms=150.0,
                throughput_rps=1000.0,
                auto_scaling=True,
            ),
            fairness_metrics=[
                FairnessMetric(
                    metric_name="demographic_parity",
                    protected_attribute="gender",
                    value=0.95,
                    threshold=0.80,
                    passes=True,
                ),
            ],
            nist_ai_rmf_profile=NISTAIRMFProfile(
                govern_maturity="Managed",
                map_maturity="Measured",
                measure_maturity="Optimized",
                manage_maturity="Partial",
            ),
            taxonomy_lineage=[],
            hyperparameters={"learning_rate": "0.001", "max_depth": "10"},
            guardrail_types=["content_filter", "pii_detection"],
        )

        # Serialize to JSON
        json_str = json.dumps(model.model_dump(mode="json"), default=str)
        data = json.loads(json_str)

        # Deserialize back
        restored = AIModel.model_validate(data)

        # Verify sub-models survived
        assert restored.training_compute is not None
        assert restored.training_compute.gpu_type == "A100"
        assert restored.training_compute.gpu_hours == 42.5
        assert restored.training_compute.carbon_footprint_kg == 123.4
        assert len(restored.performance_metrics) == 2
        assert restored.performance_metrics[0].metric_name == "F1"
        assert restored.performance_metrics[0].value == 0.92
        assert restored.baseline_comparison is not None
        assert restored.baseline_comparison.improvement_pct == 8.2
        assert restored.serving_infrastructure is not None
        assert restored.serving_infrastructure.auto_scaling is True
        assert len(restored.fairness_metrics) == 1
        assert restored.fairness_metrics[0].passes is True
        assert restored.nist_ai_rmf_profile is not None
        assert restored.nist_ai_rmf_profile.govern_maturity == "Managed"
        assert restored.hyperparameters == {"learning_rate": "0.001", "max_depth": "10"}
        assert restored.guardrail_types == ["content_filter", "pii_detection"]

    def test_none_submodels_round_trip(self):
        """AIModel with None sub-models must serialize/deserialize cleanly."""
        model = _make_ai_model(
            training_compute=None,
            baseline_comparison=None,
            serving_infrastructure=None,
            nist_ai_rmf_profile=None,
        )
        json_str = json.dumps(model.model_dump(mode="json"), default=str)
        data = json.loads(json_str)
        restored = AIModel.model_validate(data)
        assert restored.training_compute is None
        assert restored.baseline_comparison is None
        assert restored.serving_infrastructure is None
        assert restored.nist_ai_rmf_profile is None

    def test_empty_list_submodels(self):
        """AIModel with empty list sub-models round-trips correctly."""
        model = _make_ai_model(
            performance_metrics=[],
            fairness_metrics=[],
            taxonomy_lineage=[],
            guardrail_types=[],
            trained_on_data_assets=[],
        )
        json_str = json.dumps(model.model_dump(mode="json"), default=str)
        data = json.loads(json_str)
        restored = AIModel.model_validate(data)
        assert restored.performance_metrics == []
        assert restored.fairness_metrics == []
        assert restored.taxonomy_lineage == []
        assert restored.guardrail_types == []


class TestDataProductSerializationRoundTrip:
    """DataProduct with sub-models must survive JSON round-trip."""

    def test_full_submodel_round_trip(self):
        product = _make_data_product(
            data_product_sla=DataProductSLA(
                availability_pct=99.9,
                freshness_target="< 15 minutes",
                latency_target_ms=500,
                support_hours="24x7",
            ),
            quality_dimensions=QualityDimensions(
                completeness_pct=98.5,
                accuracy_pct=99.1,
                timeliness_score=0.95,
                consistency_score=0.88,
                uniqueness_pct=99.7,
            ),
        )
        json_str = json.dumps(product.model_dump(mode="json"), default=str)
        data = json.loads(json_str)
        restored = DataProduct.model_validate(data)

        assert restored.data_product_sla is not None
        assert restored.data_product_sla.availability_pct == 99.9
        assert restored.data_product_sla.support_hours == "24x7"
        assert restored.quality_dimensions is not None
        assert restored.quality_dimensions.completeness_pct == 98.5
        assert restored.quality_dimensions.uniqueness_pct == 99.7


class TestDataPipelineSerializationRoundTrip:
    """DataPipeline with sub-models must survive JSON round-trip."""

    def test_full_submodel_round_trip(self):
        pipeline = _make_data_pipeline(
            execution_frequency=ExecutionFrequency(
                schedule="0 2 * * *",
                typical_duration_minutes=45.5,
                last_run_status="success",
            ),
            compute_resource=ComputeResource(
                compute_type="spark",
                instance_type="m5.xlarge",
                parallelism=4,
                auto_scaling=True,
            ),
            retry_policy=RetryPolicy(
                max_retries=3,
                backoff_strategy="exponential",
                dead_letter_queue="arn:aws:sqs:us-east-1:123456789012:dlq",
            ),
        )
        json_str = json.dumps(pipeline.model_dump(mode="json"), default=str)
        data = json.loads(json_str)
        restored = DataPipeline.model_validate(data)

        assert restored.execution_frequency is not None
        assert restored.execution_frequency.schedule == "0 2 * * *"
        assert restored.execution_frequency.typical_duration_minutes == 45.5
        assert restored.compute_resource is not None
        assert restored.compute_resource.parallelism == 4
        assert restored.retry_policy is not None
        assert restored.retry_policy.max_retries == 3
        assert restored.retry_policy.backoff_strategy == "exponential"


# ===========================================================================
# 2. Extra field leakage detection (extra="allow" pitfall)
# ===========================================================================


class TestExtraFieldLeakage:
    """Detect fields silently going to __pydantic_extra__ instead of model fields."""

    def test_ai_model_no_extras_on_valid_construction(self):
        """A properly constructed AIModel must have no extras."""
        model = _make_ai_model()
        extras = model.__pydantic_extra__ or {}
        assert extras == {}, f"AIModel has unexpected extras: {sorted(extras.keys())}"

    def test_data_product_no_extras_on_valid_construction(self):
        product = _make_data_product()
        extras = product.__pydantic_extra__ or {}
        assert extras == {}, f"DataProduct has unexpected extras: {sorted(extras.keys())}"

    def test_data_pipeline_no_extras_on_valid_construction(self):
        pipeline = _make_data_pipeline()
        extras = pipeline.__pydantic_extra__ or {}
        assert extras == {}, f"DataPipeline has unexpected extras: {sorted(extras.keys())}"

    def test_ai_model_typo_goes_to_extras(self):
        """Verify that a typo in a field name goes to extras (demonstrates the pitfall)."""
        model = AIModel(
            name="Typo Test",
            model_typ="classification",  # typo: model_typ instead of model_type
        )
        extras = model.__pydantic_extra__ or {}
        assert "model_typ" in extras, "Typo should end up in extras (extra='allow')"
        assert model.model_type == "", "Real field should have default value"

    def test_data_product_typo_goes_to_extras(self):
        product = DataProduct(
            name="Typo Test",
            data_prodct_type="dataset",  # typo
        )
        extras = product.__pydantic_extra__ or {}
        assert "data_prodct_type" in extras
        assert product.data_product_type == ""

    def test_data_pipeline_typo_goes_to_extras(self):
        pipeline = DataPipeline(
            name="Typo Test",
            pipline_type="etl",  # typo
        )
        extras = pipeline.__pydantic_extra__ or {}
        assert "pipline_type" in extras
        assert pipeline.pipeline_type == ""


# ===========================================================================
# 3. Generator output validation — no extras leaking
# ===========================================================================


class TestGeneratorOutputCorrectness:
    """Verify generators produce entities with NO extras leaking."""

    @pytest.fixture(autouse=True)
    def _setup_context(self):
        """Create a GenerationContext with prerequisite entities."""
        from synthetic.base import GenerationContext
        from synthetic.profiles.tech_company import mid_size_tech_company

        self.profile = mid_size_tech_company(200)
        self.context = GenerationContext(profile=self.profile, seed=42)

        # Generate prerequisite entities
        from synthetic.generators import (
            DataAssetGenerator,
            DataDomainGenerator,
            DepartmentGenerator,
            SystemGenerator,
        )

        DepartmentGenerator().generate(len(self.profile.department_specs), self.context)
        SystemGenerator().generate(20, self.context)
        DataAssetGenerator().generate(15, self.context)
        DataDomainGenerator().generate(5, self.context)

    def test_ai_model_generator_no_extras(self):
        """Every AIModel from the generator must have no extras."""
        from synthetic.generators.cdaio import AIModelGenerator

        models = AIModelGenerator().generate(12, self.context)
        for model in models:
            extras = model.__pydantic_extra__ or {}
            assert extras == {}, f"AIModel '{model.name}' has extras: {sorted(extras.keys())}"

    def test_data_product_generator_no_extras(self):
        """Every DataProduct from the generator must have no extras."""
        from synthetic.generators.cdaio import DataProductGenerator

        products = DataProductGenerator().generate(8, self.context)
        for product in products:
            extras = product.__pydantic_extra__ or {}
            assert extras == {}, f"DataProduct '{product.name}' has extras: {sorted(extras.keys())}"

    def test_data_pipeline_generator_no_extras(self):
        """Every DataPipeline from the generator must have no extras."""
        from synthetic.generators.cdaio import DataPipelineGenerator

        pipelines = DataPipelineGenerator().generate(8, self.context)
        for pipeline in pipelines:
            extras = pipeline.__pydantic_extra__ or {}
            assert extras == {}, (
                f"DataPipeline '{pipeline.name}' has extras: {sorted(extras.keys())}"
            )

    def test_ai_model_generator_overflow(self):
        """Generate more AIModels than templates (12). Overflow must produce valid entities."""
        from synthetic.generators.cdaio import AIModelGenerator

        models = AIModelGenerator().generate(20, self.context)
        assert len(models) == 20
        for model in models:
            extras = model.__pydantic_extra__ or {}
            assert extras == {}, (
                f"Overflow AIModel '{model.name}' has extras: {sorted(extras.keys())}"
            )
            assert model.entity_type == EntityType.AI_MODEL
            assert model.model_type != ""
            assert model.model_framework != ""

    def test_data_product_generator_overflow(self):
        """Generate more DataProducts than templates (8). Overflow must work."""
        from synthetic.generators.cdaio import DataProductGenerator

        products = DataProductGenerator().generate(25, self.context)
        assert len(products) == 25
        for product in products:
            extras = product.__pydantic_extra__ or {}
            assert extras == {}, (
                f"Overflow DataProduct '{product.name}' has extras: {sorted(extras.keys())}"
            )
            assert product.data_product_type != ""
            assert product.data_product_tier != ""

    def test_data_pipeline_generator_overflow(self):
        """Generate more DataPipelines than templates (8). Overflow must work."""
        from synthetic.generators.cdaio import DataPipelineGenerator

        pipelines = DataPipelineGenerator().generate(25, self.context)
        assert len(pipelines) == 25
        for pipeline in pipelines:
            extras = pipeline.__pydantic_extra__ or {}
            assert extras == {}, (
                f"Overflow DataPipeline '{pipeline.name}' has extras: {sorted(extras.keys())}"
            )
            assert pipeline.pipeline_type != ""
            assert pipeline.orchestration_platform != ""

    def test_ai_model_generator_zero_count(self):
        """Generator with count=0 should produce empty list, not crash."""
        from synthetic.generators.cdaio import AIModelGenerator

        models = AIModelGenerator().generate(0, self.context)
        assert models == []

    def test_data_product_generator_zero_count(self):
        from synthetic.generators.cdaio import DataProductGenerator

        products = DataProductGenerator().generate(0, self.context)
        assert products == []

    def test_data_pipeline_generator_zero_count(self):
        from synthetic.generators.cdaio import DataPipelineGenerator

        pipelines = DataPipelineGenerator().generate(0, self.context)
        assert pipelines == []

    def test_ai_model_generator_count_one(self):
        """Single entity generation must work."""
        from synthetic.generators.cdaio import AIModelGenerator

        models = AIModelGenerator().generate(1, self.context)
        assert len(models) == 1
        assert models[0].entity_type == EntityType.AI_MODEL

    def test_generator_stores_entities_in_context(self):
        """Generators must store entities in context for weavers to find."""
        from synthetic.generators.cdaio import (
            AIModelGenerator,
            DataPipelineGenerator,
            DataProductGenerator,
        )

        AIModelGenerator().generate(5, self.context)
        DataProductGenerator().generate(5, self.context)
        DataPipelineGenerator().generate(5, self.context)

        assert len(self.context.get_entities(EntityType.AI_MODEL)) == 5
        assert len(self.context.get_entities(EntityType.DATA_PRODUCT)) == 5
        assert len(self.context.get_entities(EntityType.DATA_PIPELINE)) == 5


# ===========================================================================
# 4. Weaver empty-list edge cases
# ===========================================================================


class TestWeaverEmptyListEdgeCases:
    """Weavers must not crash when entity lists are empty."""

    @pytest.fixture()
    def empty_context(self):
        from synthetic.base import GenerationContext
        from synthetic.profiles.tech_company import mid_size_tech_company

        profile = mid_size_tech_company(100)
        return GenerationContext(profile=profile, seed=42)

    def test_ai_models_to_data_assets_empty(self, empty_context):
        """No AI models → no relationships, no crash."""
        from synthetic.relationships import RelationshipWeaver

        weaver = RelationshipWeaver(empty_context)
        rels = weaver._link_ai_models_to_data_assets()
        assert rels == []

    def test_ai_models_to_systems_empty(self, empty_context):
        from synthetic.relationships import RelationshipWeaver

        weaver = RelationshipWeaver(empty_context)
        rels = weaver._link_ai_models_to_systems()
        assert rels == []

    def test_data_pipelines_to_sources_empty(self, empty_context):
        from synthetic.relationships import RelationshipWeaver

        weaver = RelationshipWeaver(empty_context)
        rels = weaver._link_data_pipelines_to_sources()
        assert rels == []

    def test_data_pipelines_to_targets_empty(self, empty_context):
        from synthetic.relationships import RelationshipWeaver

        weaver = RelationshipWeaver(empty_context)
        rels = weaver._link_data_pipelines_to_targets()
        assert rels == []

    def test_data_products_to_domains_empty(self, empty_context):
        from synthetic.relationships import RelationshipWeaver

        weaver = RelationshipWeaver(empty_context)
        rels = weaver._link_data_products_to_domains()
        assert rels == []

    def test_data_pipelines_to_orchestrators_empty(self, empty_context):
        from synthetic.relationships import RelationshipWeaver

        weaver = RelationshipWeaver(empty_context)
        rels = weaver._link_data_pipelines_to_orchestrators()
        assert rels == []

    def test_ai_models_to_products_empty(self, empty_context):
        from synthetic.relationships import RelationshipWeaver

        weaver = RelationshipWeaver(empty_context)
        rels = weaver._link_ai_models_to_products()
        assert rels == []

    def test_data_pipelines_to_data_products_empty(self, empty_context):
        from synthetic.relationships import RelationshipWeaver

        weaver = RelationshipWeaver(empty_context)
        rels = weaver._link_data_pipelines_to_data_products()
        assert rels == []

    def test_initiatives_to_value_empty(self, empty_context):
        from synthetic.relationships import RelationshipWeaver

        weaver = RelationshipWeaver(empty_context)
        rels = weaver._link_initiatives_to_value()
        assert rels == []


class TestWeaverSingleEntityEdgeCases:
    """Weavers must handle single-entity lists without index errors."""

    @pytest.fixture()
    def single_entity_context(self):
        from synthetic.base import GenerationContext
        from synthetic.profiles.tech_company import mid_size_tech_company

        profile = mid_size_tech_company(100)
        ctx = GenerationContext(profile=profile, seed=42)
        # Add exactly 1 of each entity type
        ctx.store(EntityType.AI_MODEL, [_make_ai_model(name="Solo Model")])
        ctx.store(
            EntityType.DATA_ASSET,
            [BaseEntity(entity_type=EntityType.DATA_ASSET, name="Solo Asset")],
        )
        ctx.store(
            EntityType.SYSTEM, [BaseEntity(entity_type=EntityType.SYSTEM, name="Solo System")]
        )
        ctx.store(EntityType.DATA_PIPELINE, [_make_data_pipeline(name="Solo Pipeline")])
        ctx.store(EntityType.DATA_PRODUCT, [_make_data_product(name="Solo Product")])
        ctx.store(
            EntityType.DATA_DOMAIN,
            [BaseEntity(entity_type=EntityType.DATA_DOMAIN, name="Solo Domain")],
        )
        ctx.store(
            EntityType.PRODUCT, [BaseEntity(entity_type=EntityType.PRODUCT, name="Solo Product")]
        )
        ctx.store(
            EntityType.INITIATIVE,
            [BaseEntity(entity_type=EntityType.INITIATIVE, name="Solo Initiative")],
        )
        ctx.store(
            EntityType.BUSINESS_CAPABILITY,
            [BaseEntity(entity_type=EntityType.BUSINESS_CAPABILITY, name="Solo Cap")],
        )
        return ctx

    def test_ai_models_to_data_assets_single(self, single_entity_context):
        """1 AI model + 1 data asset → should produce 1 TRAINED_ON relationship."""
        from synthetic.relationships import RelationshipWeaver

        weaver = RelationshipWeaver(single_entity_context)
        rels = weaver._link_ai_models_to_data_assets()
        assert len(rels) >= 1
        assert all(r.relationship_type == RelationshipType.TRAINED_ON for r in rels)

    def test_data_pipelines_to_sources_single(self, single_entity_context):
        from synthetic.relationships import RelationshipWeaver

        weaver = RelationshipWeaver(single_entity_context)
        rels = weaver._link_data_pipelines_to_sources()
        assert len(rels) >= 1
        assert all(r.relationship_type == RelationshipType.CONSUMES for r in rels)

    def test_data_products_to_domains_single(self, single_entity_context):
        from synthetic.relationships import RelationshipWeaver

        weaver = RelationshipWeaver(single_entity_context)
        rels = weaver._link_data_products_to_domains()
        assert len(rels) == 1
        assert rels[0].relationship_type == RelationshipType.BELONGS_TO

    def test_initiatives_to_value_single(self, single_entity_context):
        from synthetic.relationships import RelationshipWeaver

        weaver = RelationshipWeaver(single_entity_context)
        rels = weaver._link_initiatives_to_value()
        assert len(rels) >= 1
        assert all(r.relationship_type == RelationshipType.CREATES_VALUE_FOR for r in rels)


# ===========================================================================
# 5. Relationship schema validation — all 8 new types
# ===========================================================================


class TestRelationshipSchemaValidation:
    """Verify domain/range constraints for all 8 new relationship types."""

    # --- TRAINED_ON: AIModel → DataAsset | DataProduct ---
    def test_trained_on_valid(self):
        ok, _ = validate_relationship(
            RelationshipType.TRAINED_ON, EntityType.AI_MODEL, EntityType.DATA_ASSET
        )
        assert ok

    def test_trained_on_valid_data_product(self):
        ok, _ = validate_relationship(
            RelationshipType.TRAINED_ON, EntityType.AI_MODEL, EntityType.DATA_PRODUCT
        )
        assert ok

    def test_trained_on_invalid_source(self):
        ok, reason = validate_relationship(
            RelationshipType.TRAINED_ON, EntityType.SYSTEM, EntityType.DATA_ASSET
        )
        assert not ok
        assert "source type" in reason

    def test_trained_on_invalid_target(self):
        ok, reason = validate_relationship(
            RelationshipType.TRAINED_ON, EntityType.AI_MODEL, EntityType.SYSTEM
        )
        assert not ok
        assert "target type" in reason

    # --- DEPLOYED_IN: AIModel → System ---
    def test_deployed_in_valid(self):
        ok, _ = validate_relationship(
            RelationshipType.DEPLOYED_IN, EntityType.AI_MODEL, EntityType.SYSTEM
        )
        assert ok

    def test_deployed_in_invalid_source(self):
        ok, _ = validate_relationship(
            RelationshipType.DEPLOYED_IN, EntityType.DATA_PIPELINE, EntityType.SYSTEM
        )
        assert not ok

    def test_deployed_in_invalid_target(self):
        ok, _ = validate_relationship(
            RelationshipType.DEPLOYED_IN, EntityType.AI_MODEL, EntityType.DEPARTMENT
        )
        assert not ok

    # --- PRODUCES: DataPipeline | AIModel → DataAsset | DataProduct ---
    def test_produces_pipeline_valid(self):
        ok, _ = validate_relationship(
            RelationshipType.PRODUCES, EntityType.DATA_PIPELINE, EntityType.DATA_ASSET
        )
        assert ok

    def test_produces_ai_model_valid(self):
        ok, _ = validate_relationship(
            RelationshipType.PRODUCES, EntityType.AI_MODEL, EntityType.DATA_PRODUCT
        )
        assert ok

    def test_produces_invalid_source(self):
        ok, _ = validate_relationship(
            RelationshipType.PRODUCES, EntityType.SYSTEM, EntityType.DATA_ASSET
        )
        assert not ok

    # --- CONSUMES: DataPipeline | AIModel | DataProduct → DataAsset | DataProduct ---
    def test_consumes_pipeline_valid(self):
        ok, _ = validate_relationship(
            RelationshipType.CONSUMES, EntityType.DATA_PIPELINE, EntityType.DATA_ASSET
        )
        assert ok

    def test_consumes_data_product_source_valid(self):
        ok, _ = validate_relationship(
            RelationshipType.CONSUMES, EntityType.DATA_PRODUCT, EntityType.DATA_ASSET
        )
        assert ok

    def test_consumes_invalid_target(self):
        ok, _ = validate_relationship(
            RelationshipType.CONSUMES, EntityType.DATA_PIPELINE, EntityType.SYSTEM
        )
        assert not ok

    # --- CREATES_VALUE_FOR: Initiative|DataProduct|AIModel → BizCap|Domain|Dept ---
    def test_creates_value_for_initiative(self):
        ok, _ = validate_relationship(
            RelationshipType.CREATES_VALUE_FOR,
            EntityType.INITIATIVE,
            EntityType.BUSINESS_CAPABILITY,
        )
        assert ok

    def test_creates_value_for_ai_model(self):
        ok, _ = validate_relationship(
            RelationshipType.CREATES_VALUE_FOR,
            EntityType.AI_MODEL,
            EntityType.DEPARTMENT,
        )
        assert ok

    def test_creates_value_for_data_product(self):
        ok, _ = validate_relationship(
            RelationshipType.CREATES_VALUE_FOR,
            EntityType.DATA_PRODUCT,
            EntityType.DATA_DOMAIN,
        )
        assert ok

    def test_creates_value_for_invalid_source(self):
        ok, _ = validate_relationship(
            RelationshipType.CREATES_VALUE_FOR,
            EntityType.SYSTEM,
            EntityType.BUSINESS_CAPABILITY,
        )
        assert not ok

    def test_creates_value_for_invalid_target(self):
        ok, _ = validate_relationship(
            RelationshipType.CREATES_VALUE_FOR,
            EntityType.INITIATIVE,
            EntityType.SYSTEM,
        )
        assert not ok

    # --- MONITORS: System | DataPipeline → AIModel | DataPipeline | System ---
    def test_monitors_system_valid(self):
        ok, _ = validate_relationship(
            RelationshipType.MONITORS, EntityType.SYSTEM, EntityType.AI_MODEL
        )
        assert ok

    def test_monitors_pipeline_valid(self):
        ok, _ = validate_relationship(
            RelationshipType.MONITORS, EntityType.DATA_PIPELINE, EntityType.SYSTEM
        )
        assert ok

    def test_monitors_invalid_source(self):
        ok, _ = validate_relationship(
            RelationshipType.MONITORS, EntityType.PERSON, EntityType.AI_MODEL
        )
        assert not ok

    # --- PUBLISHES: DataPipeline | System → DataProduct ---
    def test_publishes_pipeline_valid(self):
        ok, _ = validate_relationship(
            RelationshipType.PUBLISHES, EntityType.DATA_PIPELINE, EntityType.DATA_PRODUCT
        )
        assert ok

    def test_publishes_system_valid(self):
        ok, _ = validate_relationship(
            RelationshipType.PUBLISHES, EntityType.SYSTEM, EntityType.DATA_PRODUCT
        )
        assert ok

    def test_publishes_invalid_target(self):
        ok, _ = validate_relationship(
            RelationshipType.PUBLISHES, EntityType.DATA_PIPELINE, EntityType.DATA_ASSET
        )
        assert not ok

    # --- ORCHESTRATES: System → DataPipeline ---
    def test_orchestrates_valid(self):
        ok, _ = validate_relationship(
            RelationshipType.ORCHESTRATES, EntityType.SYSTEM, EntityType.DATA_PIPELINE
        )
        assert ok

    def test_orchestrates_invalid_source(self):
        ok, _ = validate_relationship(
            RelationshipType.ORCHESTRATES, EntityType.PERSON, EntityType.DATA_PIPELINE
        )
        assert not ok

    def test_orchestrates_invalid_target(self):
        ok, _ = validate_relationship(
            RelationshipType.ORCHESTRATES, EntityType.SYSTEM, EntityType.SYSTEM
        )
        assert not ok

    # --- Expanded schemas: SUPPORTS includes AI_MODEL, BELONGS_TO includes DATA_PRODUCT ---
    def test_supports_ai_model_source(self):
        ok, _ = validate_relationship(
            RelationshipType.SUPPORTS, EntityType.AI_MODEL, EntityType.PRODUCT
        )
        assert ok

    def test_belongs_to_data_product_source(self):
        ok, _ = validate_relationship(
            RelationshipType.BELONGS_TO,
            EntityType.DATA_PRODUCT,
            EntityType.DATA_DOMAIN,
        )
        assert ok


# ===========================================================================
# 6. Discriminated union dispatch for AnyEntity
# ===========================================================================


class TestAnyEntityDiscriminator:
    """AnyEntity discriminated union must correctly dispatch to CDAIO types."""

    def test_ai_model_dispatch(self):
        """JSON with entity_type='ai_model' must dispatch to AIModel class."""
        from pydantic import TypeAdapter

        adapter = TypeAdapter(AnyEntity)
        data = {
            "entity_type": "ai_model",
            "name": "Test Model",
            "model_type": "classification",
        }
        entity = adapter.validate_python(data)
        assert isinstance(entity, AIModel)
        assert entity.model_type == "classification"

    def test_data_product_dispatch(self):
        from pydantic import TypeAdapter

        adapter = TypeAdapter(AnyEntity)
        data = {
            "entity_type": "data_product",
            "name": "Test Product",
            "data_product_type": "dataset",
        }
        entity = adapter.validate_python(data)
        assert isinstance(entity, DataProduct)
        assert entity.data_product_type == "dataset"

    def test_data_pipeline_dispatch(self):
        from pydantic import TypeAdapter

        adapter = TypeAdapter(AnyEntity)
        data = {
            "entity_type": "data_pipeline",
            "name": "Test Pipeline",
            "pipeline_type": "etl",
        }
        entity = adapter.validate_python(data)
        assert isinstance(entity, DataPipeline)
        assert entity.pipeline_type == "etl"


# ===========================================================================
# 7. EntityRegistry knows new types
# ===========================================================================


class TestEntityRegistryNewTypes:
    """EntityRegistry must have all 3 new types after auto_discover."""

    @pytest.fixture(autouse=True)
    def _setup_registry(self):
        EntityRegistry.auto_discover()

    def test_ai_model_registered(self):
        cls = EntityRegistry.get(EntityType.AI_MODEL)
        assert cls is AIModel

    def test_data_product_registered(self):
        cls = EntityRegistry.get(EntityType.DATA_PRODUCT)
        assert cls is DataProduct

    def test_data_pipeline_registered(self):
        cls = EntityRegistry.get(EntityType.DATA_PIPELINE)
        assert cls is DataPipeline

    def test_total_registered_types(self):
        """Should have 33 types registered (30 original + 3 CDAIO)."""
        all_types = EntityRegistry.all_types()
        assert len(all_types) == 33, f"Expected 33 registered types, got {len(all_types)}"


# ===========================================================================
# 8. Temporal/provenance naming convention
# ===========================================================================


class TestTemporalProvenanceNaming:
    """New CDAIO types must use temporal_and_versioning / provenance_and_confidence."""

    def test_ai_model_naming(self):
        model = _make_ai_model()
        assert hasattr(model, "temporal_and_versioning")
        assert hasattr(model, "provenance_and_confidence")
        assert isinstance(model.temporal_and_versioning, TemporalAndVersioning)
        assert isinstance(model.provenance_and_confidence, ProvenanceAndConfidence)

    def test_data_product_naming(self):
        product = _make_data_product()
        assert hasattr(product, "temporal_and_versioning")
        assert hasattr(product, "provenance_and_confidence")

    def test_data_pipeline_naming(self):
        pipeline = _make_data_pipeline()
        assert hasattr(pipeline, "temporal_and_versioning")
        assert hasattr(pipeline, "provenance_and_confidence")


# ===========================================================================
# 9. Generator coherence — field value constraints
# ===========================================================================


class TestGeneratorCoherence:
    """Generator output must follow documented value constraints."""

    @pytest.fixture(autouse=True)
    def _setup_context(self):
        from synthetic.base import GenerationContext
        from synthetic.profiles.tech_company import mid_size_tech_company

        self.profile = mid_size_tech_company(200)
        self.context = GenerationContext(profile=self.profile, seed=42)

        from synthetic.generators import (
            DataAssetGenerator,
            DataDomainGenerator,
            DepartmentGenerator,
            ProductGenerator,
            SystemGenerator,
        )

        DepartmentGenerator().generate(len(self.profile.department_specs), self.context)
        SystemGenerator().generate(20, self.context)
        DataAssetGenerator().generate(15, self.context)
        DataDomainGenerator().generate(5, self.context)
        ProductGenerator().generate(5, self.context)

    def test_ai_model_genai_fields_coherent(self):
        """Generative models must have base_model_provider; non-generative must not."""
        from synthetic.generators.cdaio import AIModelGenerator

        random.seed(42)
        models = AIModelGenerator().generate(12, self.context)
        for model in models:
            if model.is_generative:
                assert model.base_model_provider != "", (
                    f"Generative model '{model.name}' missing base_model_provider"
                )
                assert model.guardrails_enabled is True
                assert len(model.guardrail_types) >= 2
            else:
                assert model.base_model_provider == ""

    def test_ai_model_metric_types_match(self):
        """Primary metric name should be appropriate for the model type."""
        from synthetic.generators.cdaio import _MODEL_TYPE_METRICS, AIModelGenerator

        random.seed(42)
        models = AIModelGenerator().generate(12, self.context)
        for model in models:
            if model.model_type in _MODEL_TYPE_METRICS:
                expected_metric = _MODEL_TYPE_METRICS[model.model_type][0]
                assert model.primary_metric_name == expected_metric, (
                    f"Model '{model.name}' type={model.model_type} "
                    f"has metric '{model.primary_metric_name}' "
                    f"expected '{expected_metric}'"
                )

    def test_ai_model_deployment_status_coherent(self):
        """Production models should be full_production; non-production should not."""
        from synthetic.generators.cdaio import AIModelGenerator

        random.seed(42)
        models = AIModelGenerator().generate(12, self.context)
        for model in models:
            if model.model_status == "production":
                assert model.deployment_status == "full_production"
                assert model.monitoring_enabled is True
                assert model.drift_detection_enabled is True
            elif model.model_status == "staging":
                assert model.deployment_status == "canary"
            elif model.model_status == "development":
                assert model.deployment_status == "not_deployed"

    def test_data_product_fair_scores_bounded(self):
        """FAIR scores must be between 0.0 and 1.0."""
        from synthetic.generators.cdaio import DataProductGenerator

        random.seed(42)
        products = DataProductGenerator().generate(15, self.context)
        for product in products:
            for field in [
                "findable_score",
                "accessible_score",
                "interoperable_score",
                "reusable_score",
            ]:
                value = getattr(product, field)
                if value is not None:
                    assert 0.0 <= value <= 1.0, (
                        f"DataProduct '{product.name}' {field}={value} out of bounds"
                    )

    def test_data_pipeline_streaming_no_cron(self):
        """Streaming pipelines (kappa/lambda) should have empty cron schedule."""
        from synthetic.generators.cdaio import DataPipelineGenerator

        random.seed(42)
        pipelines = DataPipelineGenerator().generate(20, self.context)
        for pipeline in pipelines:
            if pipeline.pipeline_type in ("streaming", "cdc"):
                assert pipeline.trigger_type == "event_driven", (
                    f"Streaming pipeline '{pipeline.name}' should be event_driven"
                )

    def test_data_pipeline_quality_pass_rate_bounded(self):
        """Quality pass rate must be between 0 and 100."""
        from synthetic.generators.cdaio import DataPipelineGenerator

        random.seed(42)
        pipelines = DataPipelineGenerator().generate(20, self.context)
        for pipeline in pipelines:
            if pipeline.quality_pass_rate_pct is not None:
                assert 0 <= pipeline.quality_pass_rate_pct <= 100


# ===========================================================================
# 10. Scaling at large employee counts
# ===========================================================================


class TestScalingAtLargeCounts:
    """Verify entity count ranges stay within bounds at 5k, 10k, 20k employees."""

    @pytest.mark.parametrize("employee_count", [5000, 10000, 20000])
    def test_tech_profile_scaling_bounds(self, employee_count):
        from synthetic.profiles.tech_company import mid_size_tech_company

        profile = mid_size_tech_company(employee_count)

        # CDAIO ranges
        for field_name, ceiling in [
            ("ai_model_count_range", 300),
            ("data_product_count_range", 500),
            ("data_pipeline_count_range", 800),
        ]:
            low, high = getattr(profile, field_name)
            assert low >= 1, f"{field_name} low={low} at {employee_count} emp"
            assert high <= ceiling, (
                f"{field_name} high={high} exceeds ceiling {ceiling} at {employee_count} emp"
            )
            assert low < high, f"{field_name} low={low} >= high={high} at {employee_count} emp"

    @pytest.mark.parametrize("employee_count", [5000, 10000, 20000])
    def test_financial_profile_scaling_bounds(self, employee_count):
        from synthetic.profiles.financial_org import financial_org

        profile = financial_org(employee_count)
        for field_name in [
            "ai_model_count_range",
            "data_product_count_range",
            "data_pipeline_count_range",
        ]:
            low, high = getattr(profile, field_name)
            assert low >= 1, f"{field_name} low={low}"
            assert low < high, f"{field_name} low={low} >= high={high}"

    @pytest.mark.parametrize("employee_count", [5000, 10000, 20000])
    def test_healthcare_profile_scaling_bounds(self, employee_count):
        from synthetic.profiles.healthcare_org import healthcare_org

        profile = healthcare_org(employee_count)
        for field_name in [
            "ai_model_count_range",
            "data_product_count_range",
            "data_pipeline_count_range",
        ]:
            low, high = getattr(profile, field_name)
            assert low >= 1, f"{field_name} low={low}"
            assert low < high, f"{field_name} low={low} >= high={high}"


# ===========================================================================
# 11. Engine round-trip: add entity → serialize → deserialize
# ===========================================================================


class TestEngineRoundTrip:
    """Verify entities survive engine add → retrieve cycle."""

    @pytest.fixture(autouse=True)
    def _setup_engine(self):
        from engine.networkx_engine import NetworkXGraphEngine

        EntityRegistry.auto_discover()
        self.engine = NetworkXGraphEngine()

    def test_ai_model_engine_round_trip(self):
        model = _make_ai_model(
            training_compute=TrainingCompute(gpu_type="H100", gpu_hours=10.0),
            nist_ai_rmf_profile=NISTAIRMFProfile(govern_maturity="Managed"),
        )
        self.engine.add_entity(model)
        retrieved = self.engine.get_entity(model.id)
        assert isinstance(retrieved, AIModel)
        assert retrieved.name == "Test Model"
        assert retrieved.training_compute is not None
        assert retrieved.training_compute.gpu_type == "H100"
        assert retrieved.nist_ai_rmf_profile is not None
        assert retrieved.nist_ai_rmf_profile.govern_maturity == "Managed"

    def test_data_product_engine_round_trip(self):
        product = _make_data_product(
            data_product_sla=DataProductSLA(availability_pct=99.9),
            quality_dimensions=QualityDimensions(completeness_pct=98.0),
        )
        self.engine.add_entity(product)
        retrieved = self.engine.get_entity(product.id)
        assert isinstance(retrieved, DataProduct)
        assert retrieved.data_product_sla is not None
        assert retrieved.data_product_sla.availability_pct == 99.9
        assert retrieved.quality_dimensions is not None

    def test_data_pipeline_engine_round_trip(self):
        pipeline = _make_data_pipeline(
            execution_frequency=ExecutionFrequency(schedule="0 2 * * *"),
            compute_resource=ComputeResource(compute_type="spark", parallelism=4),
        )
        self.engine.add_entity(pipeline)
        retrieved = self.engine.get_entity(pipeline.id)
        assert isinstance(retrieved, DataPipeline)
        assert retrieved.execution_frequency is not None
        assert retrieved.execution_frequency.schedule == "0 2 * * *"
        assert retrieved.compute_resource is not None
        assert retrieved.compute_resource.parallelism == 4

    def test_engine_entity_count_by_type(self):
        """Engine must correctly count entities by new types."""
        self.engine.add_entity(_make_ai_model(name="M1"))
        self.engine.add_entity(_make_ai_model(name="M2"))
        self.engine.add_entity(_make_data_product(name="P1"))
        self.engine.add_entity(_make_data_pipeline(name="PL1"))

        assert self.engine.entity_count(EntityType.AI_MODEL) == 2
        assert self.engine.entity_count(EntityType.DATA_PRODUCT) == 1
        assert self.engine.entity_count(EntityType.DATA_PIPELINE) == 1

    def test_engine_update_cdaio_entity(self):
        """Engine update must work for new types."""
        model = _make_ai_model(model_status="development")
        self.engine.add_entity(model)
        updated = self.engine.update_entity(model.id, {"model_status": "production"})
        assert updated.model_status == "production"

    def test_engine_remove_cdaio_entity(self):
        """Engine remove must work for new types."""
        model = _make_ai_model()
        self.engine.add_entity(model)
        assert self.engine.entity_count(EntityType.AI_MODEL) == 1
        self.engine.remove_entity(model.id)
        assert self.engine.entity_count(EntityType.AI_MODEL) == 0


# ===========================================================================
# 12. Backward compatibility — pre-CDAIO graph loads
# ===========================================================================


class TestBackwardCompatibility:
    """Graphs without CDAIO entity types must still load and work."""

    @pytest.fixture()
    def pre_cdaio_graph_json(self, tmp_path):
        """Create a minimal graph.json without CDAIO types."""
        data = {
            "entities": [
                {
                    "id": "person-1",
                    "entity_type": "person",
                    "name": "Alice Smith",
                    "first_name": "Alice",
                    "last_name": "Smith",
                    "email": "alice@example.com",
                },
                {
                    "id": "dept-1",
                    "entity_type": "department",
                    "name": "Engineering",
                },
                {
                    "id": "system-1",
                    "entity_type": "system",
                    "name": "API Gateway",
                },
            ],
            "relationships": [
                {
                    "id": "rel-1",
                    "relationship_type": "works_in",
                    "source_id": "person-1",
                    "target_id": "dept-1",
                    "weight": 1.0,
                    "confidence": 1.0,
                    "properties": {},
                },
            ],
            "statistics": {},
        }
        path = tmp_path / "pre_cdaio_graph.json"
        path.write_text(json.dumps(data, indent=2))
        return path

    def test_pre_cdaio_graph_loads(self, pre_cdaio_graph_json):
        """Graph without CDAIO types must load without errors."""
        from ingest.json_ingestor import JSONIngestor

        EntityRegistry.auto_discover()
        result = JSONIngestor().ingest(pre_cdaio_graph_json)
        assert len(result.entities) == 3
        assert len(result.errors) == 0

    def test_pre_cdaio_graph_with_new_types_mixed(self, tmp_path):
        """Graph with old + new types must load both correctly."""
        data = {
            "entities": [
                {
                    "id": "person-1",
                    "entity_type": "person",
                    "name": "Bob Jones",
                    "first_name": "Bob",
                    "last_name": "Jones",
                    "email": "bob@example.com",
                },
                {
                    "id": "aim-1",
                    "entity_type": "ai_model",
                    "name": "Fraud Detector",
                    "model_type": "classification",
                },
            ],
            "relationships": [],
            "statistics": {},
        }
        path = tmp_path / "mixed_graph.json"
        path.write_text(json.dumps(data, indent=2))

        from ingest.json_ingestor import JSONIngestor

        EntityRegistry.auto_discover()
        result = JSONIngestor().ingest(path)
        assert len(result.entities) == 2


# ===========================================================================
# 13. Full pipeline integration — generate + export + re-import
# ===========================================================================


class TestFullPipelineRoundTrip:
    """End-to-end: generate CDAIO entities → export JSON → re-import → verify."""

    def test_generate_export_reimport(self, tmp_path):
        from graph.knowledge_graph import KnowledgeGraph
        from synthetic.orchestrator import SyntheticOrchestrator
        from synthetic.profiles.tech_company import mid_size_tech_company

        EntityRegistry.auto_discover()

        # Generate
        kg = KnowledgeGraph()
        profile = mid_size_tech_company(100)
        orchestrator = SyntheticOrchestrator(kg, profile, seed=42)
        counts = orchestrator.generate()

        assert counts.get("ai_model", 0) > 0
        assert counts.get("data_product", 0) > 0
        assert counts.get("data_pipeline", 0) > 0

        # Export
        from export.json_export import JSONExporter

        export_path = tmp_path / "test_graph.json"
        JSONExporter().export(kg._engine, export_path)

        # Re-import
        from ingest.json_ingestor import JSONIngestor

        result = JSONIngestor().ingest(export_path)
        assert len(result.errors) == 0, f"Re-import errors: {result.errors}"

        # Verify CDAIO entities survived
        ai_models = [e for e in result.entities if e.entity_type == EntityType.AI_MODEL]
        data_products = [e for e in result.entities if e.entity_type == EntityType.DATA_PRODUCT]
        data_pipelines = [e for e in result.entities if e.entity_type == EntityType.DATA_PIPELINE]

        assert len(ai_models) == counts["ai_model"]
        assert len(data_products) == counts["data_product"]
        assert len(data_pipelines) == counts["data_pipeline"]

        # Verify sub-models survived round-trip
        for model in ai_models:
            assert isinstance(model, AIModel)
            # Generator always sets training_compute
            assert model.training_compute is not None
            assert model.nist_ai_rmf_profile is not None

        for product in data_products:
            assert isinstance(product, DataProduct)
            assert product.data_product_sla is not None
            assert product.quality_dimensions is not None

        for pipeline in data_pipelines:
            assert isinstance(pipeline, DataPipeline)
            assert pipeline.execution_frequency is not None
            assert pipeline.compute_resource is not None
            assert pipeline.retry_policy is not None
