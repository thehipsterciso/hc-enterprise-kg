"""Tests for MCP write-tool input validation."""

from __future__ import annotations

import pytest

mcp_available = pytest.importorskip("mcp", reason="mcp package not installed")

from domain.base import EntityType  # noqa: E402
from domain.registry import EntityRegistry  # noqa: E402
from graph.knowledge_graph import KnowledgeGraph  # noqa: E402
from mcp_server.validation import (  # noqa: E402
    MAX_DESCRIPTION_LENGTH,
    MAX_NAME_LENGTH,
    validate_entity_input,
    validate_entity_type,
    validate_id_format,
    validate_relationship_input,
    validate_relationship_type,
)

EntityRegistry.auto_discover()


# -- helpers --


def _kg_with_person_and_dept() -> KnowledgeGraph:
    """Build a minimal KG with one Person and one Department."""
    person_cls = EntityRegistry.get(EntityType.PERSON)
    dept_cls = EntityRegistry.get(EntityType.DEPARTMENT)

    kg = KnowledgeGraph()
    kg.add_entity(
        person_cls(
            id="per-001",
            name="Alice",
            first_name="Alice",
            last_name="Smith",
            email="alice@test.com",
        )
    )
    kg.add_entity(dept_cls(id="dept-001", name="Engineering"))
    return kg


# -- validate_id_format --


class TestValidateIdFormat:
    def test_valid_ids(self):
        for val in ["abc-123", "sys_001", "geo:north-america", "v1.2.3"]:
            ok, _ = validate_id_format(val)
            assert ok, f"Expected '{val}' to be valid"

    def test_empty_id(self):
        ok, reason = validate_id_format("")
        assert not ok
        assert "empty" in reason.lower()

    def test_invalid_chars(self):
        ok, reason = validate_id_format("id with spaces")
        assert not ok
        assert "invalid characters" in reason.lower()

    def test_injection_attempt(self):
        ok, _ = validate_id_format("<script>alert(1)</script>")
        assert not ok


# -- validate_relationship_type --


class TestValidateRelationshipType:
    def test_valid(self):
        ok, _ = validate_relationship_type("depends_on")
        assert ok

    def test_invalid(self):
        ok, reason = validate_relationship_type("applies_to")
        assert not ok
        assert "Unknown relationship_type" in reason

    def test_empty(self):
        ok, _ = validate_relationship_type("")
        assert not ok


# -- validate_entity_type --


class TestValidateEntityType:
    def test_valid(self):
        ok, _ = validate_entity_type("system")
        assert ok

    def test_invalid(self):
        ok, reason = validate_entity_type("spaceship")
        assert not ok
        assert "Unknown entity_type" in reason


# -- validate_relationship_input --


class TestValidateRelationshipInput:
    def test_valid(self):
        kg = _kg_with_person_and_dept()
        ok, _ = validate_relationship_input(kg, "works_in", "per-001", "dept-001")
        assert ok

    def test_bad_enum(self):
        kg = _kg_with_person_and_dept()
        ok, reason = validate_relationship_input(kg, "applies_to", "per-001", "dept-001")
        assert not ok
        assert "Unknown relationship_type" in reason

    def test_missing_source(self):
        kg = _kg_with_person_and_dept()
        ok, reason = validate_relationship_input(kg, "works_in", "per-999", "dept-001")
        assert not ok
        assert "per-999" in reason
        assert "not found" in reason.lower()

    def test_missing_target(self):
        kg = _kg_with_person_and_dept()
        ok, reason = validate_relationship_input(kg, "works_in", "per-001", "dept-999")
        assert not ok
        assert "dept-999" in reason

    def test_schema_violation(self):
        """works_in requires Person->Department, not Department->Person."""
        kg = _kg_with_person_and_dept()
        ok, reason = validate_relationship_input(kg, "works_in", "dept-001", "per-001")
        assert not ok
        assert "department" in reason.lower() or "person" in reason.lower()


# -- validate_entity_input --


class TestValidateEntityInput:
    def test_valid(self):
        ok, _ = validate_entity_input("system", "My System", "A test system")
        assert ok

    def test_bad_type(self):
        ok, reason = validate_entity_input("spaceship", "USS Enterprise")
        assert not ok
        assert "Unknown entity_type" in reason

    def test_empty_name(self):
        ok, reason = validate_entity_input("system", "")
        assert not ok
        assert "empty" in reason.lower()

    def test_whitespace_name(self):
        ok, reason = validate_entity_input("system", "   ")
        assert not ok
        assert "empty" in reason.lower()

    def test_name_too_long(self):
        ok, reason = validate_entity_input("system", "x" * (MAX_NAME_LENGTH + 1))
        assert not ok
        assert str(MAX_NAME_LENGTH) in reason

    def test_description_too_long(self):
        ok, reason = validate_entity_input(
            "system",
            "Ok Name",
            "x" * (MAX_DESCRIPTION_LENGTH + 1),
        )
        assert not ok
        assert str(MAX_DESCRIPTION_LENGTH) in reason
