"""Backward compatibility tests for the enterprise ontology migration.

Verifies that JSON payloads from v0.1 (the original 12 entity types)
still parse correctly after enum expansion and stub entity additions.
This test file runs on every layer branch to guard against regressions.
"""

from pydantic import TypeAdapter

from domain.base import EntityType, RelationshipType
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
from domain.registry import EntityRegistry

# TypeAdapter for AnyEntity discriminated union parsing
_any_entity_adapter = TypeAdapter(AnyEntity)


class TestLegacyEntityJsonRoundtrip:
    """Verify v0.1 JSON payloads still deserialize after ontology expansion."""

    def test_person_legacy_json(self):
        data = {
            "entity_type": "person",
            "name": "Alice Smith",
            "first_name": "Alice",
            "last_name": "Smith",
            "email": "alice@acme.com",
        }
        entity = _any_entity_adapter.validate_python(data)
        assert isinstance(entity, Person)
        assert entity.first_name == "Alice"

    def test_department_legacy_json(self):
        data = {"entity_type": "department", "name": "Engineering", "code": "ENG"}
        entity = _any_entity_adapter.validate_python(data)
        assert isinstance(entity, Department)
        assert entity.code == "ENG"

    def test_role_legacy_json(self):
        data = {"entity_type": "role", "name": "DBA", "is_privileged": True}
        entity = _any_entity_adapter.validate_python(data)
        assert isinstance(entity, Role)
        assert entity.is_privileged is True

    def test_system_legacy_json(self):
        data = {
            "entity_type": "system",
            "name": "WebApp",
            "hostname": "web01",
            "criticality": "high",
        }
        entity = _any_entity_adapter.validate_python(data)
        assert isinstance(entity, System)
        assert entity.hostname == "web01"

    def test_network_legacy_json(self):
        data = {"entity_type": "network", "name": "Corp LAN", "cidr": "10.0.0.0/8"}
        entity = _any_entity_adapter.validate_python(data)
        assert isinstance(entity, Network)
        assert entity.cidr == "10.0.0.0/8"

    def test_data_asset_legacy_json(self):
        data = {
            "entity_type": "data_asset",
            "name": "Customer DB",
            "classification": "confidential",
        }
        entity = _any_entity_adapter.validate_python(data)
        assert isinstance(entity, DataAsset)
        assert entity.classification == "confidential"

    def test_policy_legacy_json(self):
        data = {"entity_type": "policy", "name": "Access Control", "is_enforced": True}
        entity = _any_entity_adapter.validate_python(data)
        assert isinstance(entity, Policy)
        assert entity.is_enforced is True

    def test_vendor_legacy_json(self):
        data = {"entity_type": "vendor", "name": "Acme Corp", "risk_tier": "high"}
        entity = _any_entity_adapter.validate_python(data)
        assert isinstance(entity, Vendor)
        assert entity.risk_tier == "high"

    def test_location_legacy_json(self):
        data = {"entity_type": "location", "name": "HQ", "city": "NYC", "country": "US"}
        entity = _any_entity_adapter.validate_python(data)
        assert isinstance(entity, Location)
        assert entity.city == "NYC"

    def test_vulnerability_legacy_json(self):
        data = {
            "entity_type": "vulnerability",
            "name": "CVE-2024-1234",
            "cvss_score": 9.8,
        }
        entity = _any_entity_adapter.validate_python(data)
        assert isinstance(entity, Vulnerability)
        assert entity.cvss_score == 9.8

    def test_threat_actor_legacy_json(self):
        data = {
            "entity_type": "threat_actor",
            "name": "APT29",
            "actor_type": "nation-state",
        }
        entity = _any_entity_adapter.validate_python(data)
        assert isinstance(entity, ThreatActor)
        assert entity.actor_type == "nation-state"

    def test_incident_legacy_json(self):
        data = {"entity_type": "incident", "name": "Phishing Campaign", "severity": "high"}
        entity = _any_entity_adapter.validate_python(data)
        assert isinstance(entity, Incident)
        assert entity.severity == "high"


class TestOriginalEnumValuesPreserved:
    """Verify all v0.1 enum values still exist and have the same string values."""

    def test_original_entity_types(self):
        original_values = {
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
        current_values = {e.value for e in EntityType}
        assert original_values.issubset(current_values)

    def test_original_relationship_types(self):
        original_values = {
            "works_in",
            "manages",
            "reports_to",
            "has_role",
            "member_of",
            "hosts",
            "connects_to",
            "depends_on",
            "stores",
            "runs_on",
            "governs",
            "exploits",
            "targets",
            "mitigates",
            "affects",
            "provides_service",
            "located_at",
            "supplied_by",
            "responsible_for",
        }
        current_values = {r.value for r in RelationshipType}
        assert original_values.issubset(current_values)


class TestNewStubEntitiesCreateable:
    """Verify all 18 stub entity types can be instantiated."""

    def test_all_new_entity_types_have_classes(self):
        new_types = [
            EntityType.REGULATION,
            EntityType.CONTROL,
            EntityType.RISK,
            EntityType.THREAT,
            EntityType.INTEGRATION,
            EntityType.DATA_DOMAIN,
            EntityType.DATA_FLOW,
            EntityType.ORGANIZATIONAL_UNIT,
            EntityType.BUSINESS_CAPABILITY,
            EntityType.SITE,
            EntityType.GEOGRAPHY,
            EntityType.JURISDICTION,
            EntityType.PRODUCT_PORTFOLIO,
            EntityType.PRODUCT,
            EntityType.MARKET_SEGMENT,
            EntityType.CUSTOMER,
            EntityType.CONTRACT,
            EntityType.INITIATIVE,
        ]
        for et in new_types:
            assert EntityRegistry.is_registered(et), f"{et} not registered"
            cls = EntityRegistry.get(et)
            entity = cls(name=f"Test {et.value}")
            assert entity.entity_type == et
            assert entity.name == f"Test {et.value}"

    def test_entity_accepts_extra_fields(self):
        """Entities should accept arbitrary fields via extra='allow'."""
        from domain.entities.regulation import Regulation

        reg = Regulation(
            name="GDPR",
            enforcement_body="EDPB",
            penalties_max_usd=22_000_000,
        )
        assert reg.name == "GDPR"
        # Extra fields accessible via model_dump
        dump = reg.model_dump()
        assert dump["enforcement_body"] == "EDPB"
        assert dump["penalties_max_usd"] == 22_000_000

    def test_stub_roundtrip_via_any_entity(self):
        """Stubs should parse through the AnyEntity discriminated union."""
        data = {"entity_type": "regulation", "name": "SOX"}
        entity = _any_entity_adapter.validate_python(data)
        assert entity.entity_type == EntityType.REGULATION
        assert entity.name == "SOX"

    def test_registry_count(self):
        """Registry should have 30 types: 12 original + 18 stubs."""
        all_types = EntityRegistry.all_types()
        assert len(all_types) == 30, f"Expected 30 types, got {len(all_types)}: {all_types}"
