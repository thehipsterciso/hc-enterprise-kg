"""Tests for all entity types."""

from domain.base import EntityType
from domain.entities import (
    AnyEntity,
    DataAsset,
    Department,
    Incident,
    Location,
    Network,
    Person,
    Policy,
    Role,
    System,
    ThreatActor,
    Vendor,
    Vulnerability,
)


class TestAllEntityTypes:
    """Verify each entity type can be created with minimal fields."""

    def test_person(self):
        e = Person(first_name="A", last_name="B", name="A B", email="a@b.com")
        assert e.entity_type == EntityType.PERSON

    def test_department(self):
        e = Department(name="Engineering")
        assert e.entity_type == EntityType.DEPARTMENT

    def test_role(self):
        e = Role(name="Engineer")
        assert e.entity_type == EntityType.ROLE

    def test_system(self):
        e = System(name="Web Server")
        assert e.entity_type == EntityType.SYSTEM

    def test_network(self):
        e = Network(name="Corporate LAN")
        assert e.entity_type == EntityType.NETWORK

    def test_data_asset(self):
        e = DataAsset(name="Customer DB")
        assert e.entity_type == EntityType.DATA_ASSET

    def test_policy(self):
        e = Policy(name="Access Control")
        assert e.entity_type == EntityType.POLICY

    def test_vendor(self):
        e = Vendor(name="Acme Corp")
        assert e.entity_type == EntityType.VENDOR

    def test_location(self):
        e = Location(name="HQ")
        assert e.entity_type == EntityType.LOCATION

    def test_vulnerability(self):
        e = Vulnerability(name="CVE-2024-12345")
        assert e.entity_type == EntityType.VULNERABILITY

    def test_threat_actor(self):
        e = ThreatActor(name="APT-1")
        assert e.entity_type == EntityType.THREAT_ACTOR

    def test_incident(self):
        e = Incident(name="Data Breach 2024")
        assert e.entity_type == EntityType.INCIDENT


class TestDiscriminatedUnion:
    def test_person_roundtrip(self):
        person = Person(first_name="A", last_name="B", name="A B", email="a@b.com")
        data = person.model_dump()
        data["entity_type"] = "person"
        from pydantic import TypeAdapter

        adapter = TypeAdapter(AnyEntity)
        restored = adapter.validate_python(data)
        assert isinstance(restored, Person)
        assert restored.first_name == "A"

    def test_system_roundtrip(self):
        system = System(name="Server", hostname="srv-01")
        data = system.model_dump()
        data["entity_type"] = "system"
        from pydantic import TypeAdapter

        adapter = TypeAdapter(AnyEntity)
        restored = adapter.validate_python(data)
        assert isinstance(restored, System)
        assert restored.hostname == "srv-01"
