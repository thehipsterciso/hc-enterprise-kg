"""Tests for MCP write tools (add_relationship_tool)."""

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


def _call_tool(name: str, **kwargs):
    """Call an MCP tool by name via the FastMCP registry."""
    for tool in mcp._tool_manager._tools.values():
        if tool.name == name:
            return tool.fn(**kwargs)
    raise ValueError(f"Tool '{name}' not found")


def _build_test_kg(tmp_path: Path) -> str:
    """Create a minimal KG with Person + Department + System, export, load into state."""
    person_cls = EntityRegistry.get(EntityType.PERSON)
    dept_cls = EntityRegistry.get(EntityType.DEPARTMENT)
    system_cls = EntityRegistry.get(EntityType.SYSTEM)

    kg = KnowledgeGraph()
    kg.add_entity(person_cls(
        id="per-001", name="Alice", first_name="Alice",
        last_name="Smith", email="alice@test.com",
    ))
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
            relationship_type="applies_to",
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
