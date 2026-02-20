"""Property-based tests for entity model invariants using Hypothesis."""

from __future__ import annotations

import pytest
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

from domain.base import BaseRelationship, EntityType, RelationshipType
from domain.registry import EntityRegistry

# Ensure registry is populated
EntityRegistry.auto_discover()

# Per-entity-type required fields beyond name/entity_type
REQUIRED_EXTRAS: dict[EntityType, dict] = {
    EntityType.PERSON: {
        "first_name": "Test",
        "last_name": "User",
        "email": "test@example.com",
    },
}

# All concrete entity classes
ENTITY_CLASSES = [(et, EntityRegistry.get(et)) for et in EntityType]


def _make_entity(entity_class, entity_type: EntityType, **kwargs):
    """Create an entity with required fields filled in."""
    extras = REQUIRED_EXTRAS.get(entity_type, {})
    return entity_class(**{**extras, **kwargs})


# Strategies
entity_names = st.text(
    min_size=1,
    max_size=50,
    alphabet=st.characters(
        whitelist_categories=("L", "N", "Zs"),
        min_codepoint=32,
        max_codepoint=126,
    ),
).filter(lambda s: s.strip())

entity_descriptions = st.text(max_size=200)
tag_lists = st.lists(st.text(min_size=1, max_size=20), max_size=5)


class TestEntityRoundtrip:
    """model_dump() → model_validate() should be a bijection for all entity types."""

    @pytest.mark.parametrize(
        "entity_type,entity_class",
        ENTITY_CLASSES,
        ids=[et.value for et in EntityType],
    )
    def test_minimal_roundtrip(self, entity_type, entity_class):
        """Minimal construction → dump → validate preserves identity."""
        entity = _make_entity(entity_class, entity_type, name="Test Entity")
        dumped = entity.model_dump(mode="json")
        restored = entity_class.model_validate(dumped)

        assert restored.id == entity.id
        assert restored.name == entity.name
        assert restored.entity_type == entity.entity_type

    @pytest.mark.parametrize(
        "entity_type,entity_class",
        ENTITY_CLASSES,
        ids=[et.value for et in EntityType],
    )
    @given(data=st.data())
    @settings(max_examples=10, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_roundtrip_with_random_base_fields(self, entity_type, entity_class, data):
        """Random base field values survive roundtrip for all 30 entity types."""
        name = data.draw(entity_names)
        desc = data.draw(entity_descriptions)
        tags = data.draw(tag_lists)

        entity = _make_entity(
            entity_class,
            entity_type,
            name=name,
            description=desc,
            tags=tags,
        )

        dumped = entity.model_dump(mode="json")
        restored = entity_class.model_validate(dumped)

        assert restored.id == entity.id
        assert restored.name == name
        assert restored.description == desc
        assert restored.tags == tags
        assert restored.entity_type == entity_type


class TestRelationshipRoundtrip:
    """BaseRelationship serialization roundtrip."""

    @given(
        weight=st.floats(min_value=0.0, max_value=100.0, allow_nan=False),
        confidence=st.floats(min_value=0.0, max_value=1.0, allow_nan=False),
    )
    @settings(max_examples=20)
    def test_relationship_roundtrip(self, weight, confidence):
        """Relationship with random weight/confidence survives roundtrip."""
        rel = BaseRelationship(
            relationship_type=RelationshipType.WORKS_IN,
            source_id="src-1",
            target_id="tgt-1",
            weight=weight,
            confidence=confidence,
        )

        dumped = rel.model_dump(mode="json")
        restored = BaseRelationship.model_validate(dumped)

        assert restored.id == rel.id
        assert restored.weight == pytest.approx(weight)
        assert restored.confidence == pytest.approx(confidence)
        assert restored.source_id == "src-1"
        assert restored.target_id == "tgt-1"


class TestExtraFieldDetection:
    """Verify that extra="allow" behavior is detectable."""

    @pytest.mark.parametrize(
        "entity_type,entity_class",
        ENTITY_CLASSES,
        ids=[et.value for et in EntityType],
    )
    def test_misspelled_field_goes_to_extras(self, entity_type, entity_class):
        """Demonstrate that misspelled fields land in __pydantic_extra__."""
        entity = _make_entity(
            entity_class,
            entity_type,
            name="Test",
            this_field_does_not_exist_xyz="should be in extras",
        )
        extras = entity.__pydantic_extra__ or {}
        assert "this_field_does_not_exist_xyz" in extras, (
            f"{entity_class.__name__} did not capture extra field — "
            "extra='allow' may have been changed"
        )

    @pytest.mark.parametrize(
        "entity_type,entity_class",
        ENTITY_CLASSES,
        ids=[et.value for et in EntityType],
    )
    def test_correct_field_not_in_extras(self, entity_type, entity_class):
        """Known fields should NOT appear in __pydantic_extra__."""
        entity = _make_entity(entity_class, entity_type, name="Test", description="A real field")
        extras = entity.__pydantic_extra__ or {}
        assert "name" not in extras
        assert "description" not in extras


class TestEntityTypeEnumStability:
    """Entity type enum values must remain stable across versions."""

    ORIGINAL_V01_TYPES = {
        "person",
        "department",
        "role",
        "system",
        "network",
        "data_asset",
        "policy",
        "vendor",
        "location",
        "vulnerability",
        "threat_actor",
        "incident",
    }

    ENTERPRISE_TYPES = {
        "regulation",
        "control",
        "risk",
        "threat",
        "integration",
        "data_domain",
        "data_flow",
        "organizational_unit",
        "business_capability",
        "site",
        "geography",
        "jurisdiction",
        "product_portfolio",
        "product",
        "market_segment",
        "customer",
        "contract",
        "initiative",
    }

    def test_v01_types_preserved(self):
        """Original v0.1 entity types must still exist."""
        current = {et.value for et in EntityType}
        missing = self.ORIGINAL_V01_TYPES - current
        assert not missing, f"v0.1 entity types removed: {missing}"

    def test_enterprise_types_preserved(self):
        """Enterprise entity types must still exist."""
        current = {et.value for et in EntityType}
        missing = self.ENTERPRISE_TYPES - current
        assert not missing, f"Enterprise entity types removed: {missing}"

    def test_total_entity_type_count(self):
        """We should have exactly 30 entity types."""
        assert len(EntityType) == 30, f"Expected 30, got {len(EntityType)}: {list(EntityType)}"


class TestRelationshipTypeEnumStability:
    """Relationship type enum values must remain stable."""

    def test_minimum_relationship_types(self):
        """We should have at least 50 relationship types."""
        assert len(RelationshipType) >= 50, (
            f"Expected >=50 relationship types, got {len(RelationshipType)}"
        )

    def test_core_relationship_types_exist(self):
        """Core organizational relationship types must exist."""
        core = {"works_in", "manages", "reports_to", "has_role", "depends_on"}
        current = {rt.value for rt in RelationshipType}
        missing = core - current
        assert not missing, f"Core relationship types removed: {missing}"
