"""Tests for domain base types."""

from domain.base import (
    BaseEntity,
    BaseRelationship,
    EntityType,
    RelationshipType,
)
from domain.entities.person import Person


class TestBaseEntity:
    def test_person_creation(self, sample_person):
        assert sample_person.name == "Alice Smith"
        assert sample_person.entity_type == EntityType.PERSON
        assert sample_person.first_name == "Alice"

    def test_entity_has_id(self):
        person = Person(first_name="Bob", last_name="Jones", name="Bob Jones", email="bob@test.com")
        assert person.id is not None
        assert len(person.id) > 0

    def test_entity_has_timestamps(self):
        person = Person(first_name="Bob", last_name="Jones", name="Bob Jones", email="bob@test.com")
        assert person.created_at is not None
        assert person.updated_at is not None
        assert person.version == 1

    def test_entity_serialization(self, sample_person):
        data = sample_person.model_dump()
        assert data["first_name"] == "Alice"
        assert data["entity_type"] == EntityType.PERSON

    def test_entity_deserialization(self, sample_person):
        data = sample_person.model_dump()
        restored = Person.model_validate(data)
        assert restored.name == sample_person.name
        assert restored.id == sample_person.id

    def test_entity_extra_fields(self):
        person = Person(
            first_name="Bob",
            last_name="Jones",
            name="Bob Jones",
            email="bob@test.com",
            custom_field="custom_value",
        )
        assert person.custom_field == "custom_value"


class TestBaseRelationship:
    def test_relationship_creation(self, sample_relationship):
        assert sample_relationship.relationship_type == RelationshipType.WORKS_IN
        assert sample_relationship.source_id == "person-1"
        assert sample_relationship.target_id == "dept-1"

    def test_relationship_defaults(self, sample_relationship):
        assert sample_relationship.weight == 1.0
        assert sample_relationship.confidence == 1.0

    def test_relationship_serialization(self, sample_relationship):
        data = sample_relationship.model_dump()
        restored = BaseRelationship.model_validate(data)
        assert restored.source_id == sample_relationship.source_id
