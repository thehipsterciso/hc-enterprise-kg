"""Tests for MCP write tools (relationships + entities)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

mcp_available = pytest.importorskip("mcp", reason="mcp package not installed")

import mcp_server.state as state  # noqa: E402
from domain.base import EntityType  # noqa: E402
from domain.registry import EntityRegistry  # noqa: E402
from export.json_export import JSONExporter  # noqa: E402
from graph.knowledge_graph import KnowledgeGraph  # noqa: E402
from mcp_server.server import mcp  # noqa: E402

EntityRegistry.auto_discover()


def _call_tool(tool_name: str, **kwargs):
    """Call an MCP tool by name via the FastMCP registry."""
    for tool in mcp._tool_manager._tools.values():
        if tool.name == tool_name:
            return tool.fn(**kwargs)
    raise ValueError(f"Tool '{tool_name}' not found")


def _build_test_kg(tmp_path: Path) -> str:
    """Create a minimal KG with Person + Department + System, export, load into state."""
    person_cls = EntityRegistry.get(EntityType.PERSON)
    dept_cls = EntityRegistry.get(EntityType.DEPARTMENT)
    system_cls = EntityRegistry.get(EntityType.SYSTEM)

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
    kg.add_entity(system_cls(id="sys-001", name="Auth Service"))
    kg.add_entity(system_cls(id="sys-002", name="DB Service"))

    json_path = tmp_path / "test_graph.json"
    JSONExporter().export(kg.engine, json_path)
    state._kg = kg
    state._loaded_path = str(json_path)
    state._loaded_mtime = json_path.stat().st_mtime
    return str(json_path)


@pytest.fixture(autouse=True)
def _reset_state():
    """Clean server state before and after each test."""
    state._kg = None
    state._loaded_path = None
    state._loaded_mtime = 0.0
    yield
    state._kg = None
    state._loaded_path = None
    state._loaded_mtime = 0.0


# -- add_relationship_tool --


class TestAddRelationshipTool:
    def test_valid_relationship(self, tmp_path):
        _build_test_kg(tmp_path)
        result = _call_tool(
            "add_relationship_tool",
            relationship_type="works_in",
            source_id="per-001",
            target_id="dept-001",
        )
        assert result["status"] == "ok"
        assert "relationship_id" in result
        assert result["relationship"]["relationship_type"] == "works_in"
        assert result["relationship"]["source_id"] == "per-001"
        assert result["relationship"]["target_id"] == "dept-001"

    def test_system_depends_on_system(self, tmp_path):
        _build_test_kg(tmp_path)
        result = _call_tool(
            "add_relationship_tool",
            relationship_type="depends_on",
            source_id="sys-001",
            target_id="sys-002",
        )
        assert result["status"] == "ok"

    def test_invalid_relationship_type(self, tmp_path):
        _build_test_kg(tmp_path)
        result = _call_tool(
            "add_relationship_tool",
            relationship_type="not_a_real_type",
            source_id="per-001",
            target_id="dept-001",
        )
        assert "error" in result
        assert "Unknown relationship_type" in result["error"]

    def test_missing_source_entity(self, tmp_path):
        _build_test_kg(tmp_path)
        result = _call_tool(
            "add_relationship_tool",
            relationship_type="works_in",
            source_id="per-999",
            target_id="dept-001",
        )
        assert "error" in result
        assert "not found" in result["error"].lower()

    def test_missing_target_entity(self, tmp_path):
        _build_test_kg(tmp_path)
        result = _call_tool(
            "add_relationship_tool",
            relationship_type="works_in",
            source_id="per-001",
            target_id="dept-999",
        )
        assert "error" in result
        assert "not found" in result["error"].lower()

    def test_schema_violation(self, tmp_path):
        """works_in requires Person -> Department, not System -> System."""
        _build_test_kg(tmp_path)
        result = _call_tool(
            "add_relationship_tool",
            relationship_type="works_in",
            source_id="sys-001",
            target_id="sys-002",
        )
        assert "error" in result

    def test_persists_to_disk(self, tmp_path):
        json_path = _build_test_kg(tmp_path)
        _call_tool(
            "add_relationship_tool",
            relationship_type="works_in",
            source_id="per-001",
            target_id="dept-001",
        )
        # Re-read from disk and verify relationship is there
        data = json.loads(Path(json_path).read_text())
        rel_types = [r["relationship_type"] for r in data["relationships"]]
        assert "works_in" in rel_types

    def test_with_properties(self, tmp_path):
        _build_test_kg(tmp_path)
        result = _call_tool(
            "add_relationship_tool",
            relationship_type="depends_on",
            source_id="sys-001",
            target_id="sys-002",
            properties={"context": "authentication"},
        )
        assert result["status"] == "ok"
        assert result["relationship"]["properties"]["context"] == "authentication"

    def test_default_weight_and_confidence(self, tmp_path):
        _build_test_kg(tmp_path)
        result = _call_tool(
            "add_relationship_tool",
            relationship_type="works_in",
            source_id="per-001",
            target_id="dept-001",
        )
        assert result["relationship"]["weight"] == 1.0
        assert result["relationship"]["confidence"] == 1.0

    def test_custom_weight_and_confidence(self, tmp_path):
        _build_test_kg(tmp_path)
        result = _call_tool(
            "add_relationship_tool",
            relationship_type="works_in",
            source_id="per-001",
            target_id="dept-001",
            weight=0.5,
            confidence=0.8,
        )
        assert result["relationship"]["weight"] == 0.5
        assert result["relationship"]["confidence"] == 0.8

    def test_weight_clamped(self, tmp_path):
        _build_test_kg(tmp_path)
        result = _call_tool(
            "add_relationship_tool",
            relationship_type="works_in",
            source_id="per-001",
            target_id="dept-001",
            weight=5.0,
            confidence=-1.0,
        )
        assert result["status"] == "ok"
        assert result["relationship"]["weight"] == 1.0
        assert result["relationship"]["confidence"] == 0.0

    def test_no_graph_loaded(self):
        result = _call_tool(
            "add_relationship_tool",
            relationship_type="works_in",
            source_id="per-001",
            target_id="dept-001",
        )
        assert "error" in result
        assert "No graph loaded" in result["error"]

    def test_relationship_count_increases(self, tmp_path):
        _build_test_kg(tmp_path)
        stats_before = state._kg.statistics["relationship_count"]
        _call_tool(
            "add_relationship_tool",
            relationship_type="works_in",
            source_id="per-001",
            target_id="dept-001",
        )
        stats_after = state._kg.statistics["relationship_count"]
        assert stats_after == stats_before + 1


# -- add_relationships_batch --


class TestAddRelationshipsBatch:
    def test_valid_batch(self, tmp_path):
        _build_test_kg(tmp_path)
        result = _call_tool(
            "add_relationships_batch",
            relationships=[
                {"relationship_type": "works_in", "source_id": "per-001", "target_id": "dept-001"},
                {"relationship_type": "depends_on", "source_id": "sys-001", "target_id": "sys-002"},
            ],
        )
        assert result["status"] == "ok"
        assert result["committed"] == 2
        assert len(result["relationships"]) == 2

    def test_single_item_batch(self, tmp_path):
        _build_test_kg(tmp_path)
        result = _call_tool(
            "add_relationships_batch",
            relationships=[
                {"relationship_type": "works_in", "source_id": "per-001", "target_id": "dept-001"},
            ],
        )
        assert result["status"] == "ok"
        assert result["committed"] == 1

    def test_validation_failure_rejects_all(self, tmp_path):
        """If any item fails validation, nothing is committed."""
        _build_test_kg(tmp_path)
        count_before = state._kg.statistics["relationship_count"]
        result = _call_tool(
            "add_relationships_batch",
            relationships=[
                {"relationship_type": "works_in", "source_id": "per-001", "target_id": "dept-001"},
                {
                    "relationship_type": "not_a_real_type",
                    "source_id": "per-001",
                    "target_id": "dept-001",
                },
            ],
        )
        assert result["status"] == "error"
        assert result["committed"] == 0
        assert len(result["errors"]) == 1
        assert result["errors"][0]["index"] == 1
        # Verify nothing was committed
        count_after = state._kg.statistics["relationship_count"]
        assert count_after == count_before

    def test_missing_required_field(self, tmp_path):
        _build_test_kg(tmp_path)
        result = _call_tool(
            "add_relationships_batch",
            relationships=[
                {"relationship_type": "works_in", "source_id": "per-001"},
            ],
        )
        assert result["status"] == "error"
        assert "Missing required field" in result["errors"][0]["error"]

    def test_empty_list(self, tmp_path):
        _build_test_kg(tmp_path)
        result = _call_tool("add_relationships_batch", relationships=[])
        assert "error" in result
        assert "Empty" in result["error"]

    def test_batch_limit_exceeded(self, tmp_path):
        _build_test_kg(tmp_path)
        item = {"relationship_type": "works_in", "source_id": "per-001", "target_id": "dept-001"}
        big_list = [item] * 501
        result = _call_tool("add_relationships_batch", relationships=big_list)
        assert "error" in result
        assert "500" in result["error"]

    def test_batch_persists_to_disk(self, tmp_path):
        json_path = _build_test_kg(tmp_path)
        _call_tool(
            "add_relationships_batch",
            relationships=[
                {"relationship_type": "works_in", "source_id": "per-001", "target_id": "dept-001"},
                {"relationship_type": "depends_on", "source_id": "sys-001", "target_id": "sys-002"},
            ],
        )
        data = json.loads(Path(json_path).read_text())
        rel_types = [r["relationship_type"] for r in data["relationships"]]
        assert "works_in" in rel_types
        assert "depends_on" in rel_types

    def test_batch_with_weight_and_properties(self, tmp_path):
        _build_test_kg(tmp_path)
        result = _call_tool(
            "add_relationships_batch",
            relationships=[
                {
                    "relationship_type": "depends_on",
                    "source_id": "sys-001",
                    "target_id": "sys-002",
                    "weight": 0.7,
                    "confidence": 0.9,
                    "properties": {"context": "auth"},
                },
            ],
        )
        assert result["status"] == "ok"
        rel = result["relationships"][0]["relationship"]
        assert rel["weight"] == 0.7
        assert rel["confidence"] == 0.9
        assert rel["properties"]["context"] == "auth"

    def test_no_graph_loaded(self):
        result = _call_tool(
            "add_relationships_batch",
            relationships=[
                {"relationship_type": "works_in", "source_id": "per-001", "target_id": "dept-001"},
            ],
        )
        assert "error" in result
        assert "No graph loaded" in result["error"]

    def test_multiple_validation_errors(self, tmp_path):
        _build_test_kg(tmp_path)
        result = _call_tool(
            "add_relationships_batch",
            relationships=[
                {
                    "relationship_type": "not_a_real_type",
                    "source_id": "per-001",
                    "target_id": "dept-001",
                },
                {
                    "relationship_type": "works_in",
                    "source_id": "per-999",
                    "target_id": "dept-001",
                },
            ],
        )
        assert result["status"] == "error"
        assert len(result["errors"]) == 2
        assert result["committed"] == 0


# -- remove_relationship_tool --


class TestRemoveRelationshipTool:
    def test_remove_valid(self, tmp_path):
        _build_test_kg(tmp_path)
        # First add a relationship
        add_result = _call_tool(
            "add_relationship_tool",
            relationship_type="works_in",
            source_id="per-001",
            target_id="dept-001",
        )
        rel_id = add_result["relationship_id"]
        count_after_add = state._kg.statistics["relationship_count"]

        # Now remove it
        result = _call_tool("remove_relationship_tool", relationship_id=rel_id)
        assert result["status"] == "ok"
        assert result["removed"]["relationship_type"] == "works_in"
        assert state._kg.statistics["relationship_count"] == count_after_add - 1

    def test_remove_not_found(self, tmp_path):
        _build_test_kg(tmp_path)
        result = _call_tool("remove_relationship_tool", relationship_id="nonexistent-id")
        assert "error" in result
        assert "not found" in result["error"].lower()

    def test_remove_persists_to_disk(self, tmp_path):
        json_path = _build_test_kg(tmp_path)
        # Add then remove
        add_result = _call_tool(
            "add_relationship_tool",
            relationship_type="works_in",
            source_id="per-001",
            target_id="dept-001",
        )
        rel_id = add_result["relationship_id"]

        _call_tool("remove_relationship_tool", relationship_id=rel_id)

        # Verify on disk
        data = json.loads(Path(json_path).read_text())
        rel_ids = [r.get("id", "") for r in data["relationships"]]
        assert rel_id not in rel_ids

    def test_remove_no_graph_loaded(self):
        result = _call_tool("remove_relationship_tool", relationship_id="some-id")
        assert "error" in result
        assert "No graph loaded" in result["error"]


# -- add_entity_tool --


class TestAddEntityTool:
    def test_add_system(self, tmp_path):
        _build_test_kg(tmp_path)
        result = _call_tool(
            "add_entity_tool",
            entity_type="system",
            name="New API Gateway",
            description="Edge proxy for all services",
        )
        assert result["status"] == "ok"
        assert "entity_id" in result
        assert result["entity"]["name"] == "New API Gateway"
        assert result["entity"]["entity_type"] == "system"

    def test_add_person(self, tmp_path):
        _build_test_kg(tmp_path)
        result = _call_tool(
            "add_entity_tool",
            entity_type="person",
            name="Bob Jones",
            properties={
                "first_name": "Bob",
                "last_name": "Jones",
                "email": "bob@test.com",
            },
        )
        assert result["status"] == "ok"
        assert result["entity"]["name"] == "Bob Jones"

    def test_add_department(self, tmp_path):
        _build_test_kg(tmp_path)
        result = _call_tool(
            "add_entity_tool",
            entity_type="department",
            name="Security Operations",
        )
        assert result["status"] == "ok"
        assert result["entity"]["entity_type"] == "department"

    def test_invalid_entity_type(self, tmp_path):
        _build_test_kg(tmp_path)
        result = _call_tool(
            "add_entity_tool",
            entity_type="spaceship",
            name="USS Enterprise",
        )
        assert "error" in result
        assert "Unknown entity_type" in result["error"]

    def test_empty_name(self, tmp_path):
        _build_test_kg(tmp_path)
        result = _call_tool(
            "add_entity_tool",
            entity_type="system",
            name="",
        )
        assert "error" in result
        assert "name" in result["error"].lower()

    def test_entity_count_increases(self, tmp_path):
        _build_test_kg(tmp_path)
        before = state._kg.statistics["entity_count"]
        _call_tool(
            "add_entity_tool",
            entity_type="system",
            name="Test System",
        )
        after = state._kg.statistics["entity_count"]
        assert after == before + 1

    def test_persists_to_disk(self, tmp_path):
        json_path = _build_test_kg(tmp_path)
        _call_tool(
            "add_entity_tool",
            entity_type="system",
            name="Persisted System",
        )
        data = json.loads(Path(json_path).read_text())
        names = [e["name"] for e in data["entities"]]
        assert "Persisted System" in names

    def test_no_graph_loaded(self):
        result = _call_tool(
            "add_entity_tool",
            entity_type="system",
            name="Ghost",
        )
        assert "error" in result
        assert "No graph loaded" in result["error"]


# -- update_entity_tool --


class TestUpdateEntityTool:
    def test_update_name(self, tmp_path):
        _build_test_kg(tmp_path)
        result = _call_tool(
            "update_entity_tool",
            entity_id="sys-001",
            updates={"name": "Auth Service v2"},
        )
        assert result["status"] == "ok"
        assert result["entity"]["name"] == "Auth Service v2"

    def test_update_description(self, tmp_path):
        _build_test_kg(tmp_path)
        result = _call_tool(
            "update_entity_tool",
            entity_id="dept-001",
            updates={"description": "Software Engineering"},
        )
        assert result["status"] == "ok"

    def test_update_not_found(self, tmp_path):
        _build_test_kg(tmp_path)
        result = _call_tool(
            "update_entity_tool",
            entity_id="nonexistent-id",
            updates={"name": "Foo"},
        )
        assert "error" in result
        assert "not found" in result["error"].lower()

    def test_empty_updates(self, tmp_path):
        _build_test_kg(tmp_path)
        result = _call_tool(
            "update_entity_tool",
            entity_id="sys-001",
            updates={},
        )
        assert "error" in result
        assert "No updates" in result["error"]

    def test_persists_to_disk(self, tmp_path):
        json_path = _build_test_kg(tmp_path)
        _call_tool(
            "update_entity_tool",
            entity_id="sys-001",
            updates={"name": "Updated Auth"},
        )
        data = json.loads(Path(json_path).read_text())
        names = [e["name"] for e in data["entities"]]
        assert "Updated Auth" in names

    def test_no_graph_loaded(self):
        result = _call_tool(
            "update_entity_tool",
            entity_id="sys-001",
            updates={"name": "X"},
        )
        assert "error" in result
        assert "No graph loaded" in result["error"]


# -- remove_entity_tool --


class TestRemoveEntityTool:
    def test_remove_valid(self, tmp_path):
        _build_test_kg(tmp_path)
        before = state._kg.statistics["entity_count"]
        result = _call_tool(
            "remove_entity_tool",
            entity_id="sys-002",
        )
        assert result["status"] == "ok"
        assert result["removed"]["name"] == "DB Service"
        assert state._kg.statistics["entity_count"] == before - 1

    def test_remove_not_found(self, tmp_path):
        _build_test_kg(tmp_path)
        result = _call_tool(
            "remove_entity_tool",
            entity_id="nonexistent",
        )
        assert "error" in result
        assert "not found" in result["error"].lower()

    def test_remove_cascades_relationships(self, tmp_path):
        _build_test_kg(tmp_path)
        # Add a relationship to sys-002
        _call_tool(
            "add_relationship_tool",
            relationship_type="depends_on",
            source_id="sys-001",
            target_id="sys-002",
        )
        rel_count_before = state._kg.statistics["relationship_count"]
        # Remove sys-002 — should also remove the relationship
        _call_tool("remove_entity_tool", entity_id="sys-002")
        rel_count_after = state._kg.statistics["relationship_count"]
        assert rel_count_after < rel_count_before

    def test_remove_persists_to_disk(self, tmp_path):
        json_path = _build_test_kg(tmp_path)
        _call_tool("remove_entity_tool", entity_id="sys-002")
        data = json.loads(Path(json_path).read_text())
        ids = [e["id"] for e in data["entities"]]
        assert "sys-002" not in ids

    def test_no_graph_loaded(self):
        result = _call_tool(
            "remove_entity_tool",
            entity_id="sys-001",
        )
        assert "error" in result
        assert "No graph loaded" in result["error"]
