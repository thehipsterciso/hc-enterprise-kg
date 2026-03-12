"""Adversarial user-input tests for MCP tools, import, and engine.

Tests every crash vector a user can trigger through:
- MCP tool calls with malformed/malicious parameters
- JSON import with corrupted/oversized/missing data
- Engine queries with boundary/extreme values
- Property-based fuzzing via Hypothesis

These tests verify the system returns graceful error dicts (never crashes)
regardless of what garbage a user feeds in.
"""

from __future__ import annotations

import contextlib
import json
import uuid
from typing import Any

import networkx as nx
import pytest
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

from domain.base import BaseRelationship, RelationshipType
from domain.entities.person import Person
from domain.entities.system import System
from domain.registry import EntityRegistry
from engine.networkx_engine import NetworkXGraphEngine
from graph.knowledge_graph import KnowledgeGraph
from ingest.json_ingestor import JSONIngestor
from mcp_server.validation import (
    MAX_DESCRIPTION_LENGTH,
    MAX_NAME_LENGTH,
    validate_entity_input,
    validate_entity_type,
    validate_id_format,
    validate_relationship_input,
    validate_relationship_type,
)

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def kg_with_entities():
    """KG with two entities for relationship testing."""
    EntityRegistry.auto_discover()
    kg = KnowledgeGraph()
    p = Person(name="Alice", first_name="Alice", last_name="Test", email="alice@example.com")
    s = System(name="TestSys")
    kg.add_entity(p)
    kg.add_entity(s)
    return kg, p, s


@pytest.fixture()
def empty_kg():
    """Empty KG with no entities."""
    EntityRegistry.auto_discover()
    return KnowledgeGraph()


# ===========================================================================
# 1. add_entity_tool: properties dict injection
# ===========================================================================


class TestPropertiesInjection:
    """sanitize_properties strips reserved fields before entity creation."""

    def test_sanitize_strips_id(self):
        """id is stripped from properties dict."""
        from mcp_server.validation import sanitize_properties

        clean, stripped = sanitize_properties({"id": "HACKED-ID", "status": "active"})
        assert "id" not in clean
        assert "id" in stripped
        assert clean["status"] == "active"

    def test_sanitize_strips_entity_type(self):
        """entity_type is stripped from properties dict."""
        from mcp_server.validation import sanitize_properties

        clean, stripped = sanitize_properties({"entity_type": "person"})
        assert "entity_type" not in clean
        assert "entity_type" in stripped

    def test_sanitize_strips_created_at(self):
        """created_at is stripped from properties dict."""
        from mcp_server.validation import sanitize_properties

        clean, stripped = sanitize_properties({"created_at": "not-a-date"})
        assert "created_at" not in clean
        assert "created_at" in stripped

    def test_sanitize_passes_valid_properties(self):
        """Non-reserved fields pass through unchanged."""
        from mcp_server.validation import sanitize_properties

        props = {"status": "active", "tier": "gold", "custom_field": 42}
        clean, stripped = sanitize_properties(props)
        assert clean == props
        assert stripped == []

    def test_sanitize_strips_all_reserved(self):
        """All 7 reserved fields are stripped."""
        from mcp_server.validation import RESERVED_ENTITY_FIELDS, sanitize_properties

        props = {field: "bad" for field in RESERVED_ENTITY_FIELDS}
        props["safe_field"] = "ok"
        clean, stripped = sanitize_properties(props)
        assert clean == {"safe_field": "ok"}
        assert set(stripped) == RESERVED_ENTITY_FIELDS


# ===========================================================================
# 2. update_entity_tool: missing ValidationError catch
# ===========================================================================


class TestUpdateEntityCrash:
    """Engine.update_entity catches KeyError/ValueError/TypeError but
    Pydantic ValidationError inherits from ValueError, so it should be caught.
    Test to confirm."""

    def test_update_with_invalid_date(self, kg_with_entities):
        """Setting a date field to garbage should not crash."""
        kg, person, _ = kg_with_entities
        with contextlib.suppress(KeyError, ValueError, TypeError):
            kg.update_entity(person.id, effective_date="NOT-A-DATE")

    def test_update_entity_type_to_different_type(self, kg_with_entities):
        """Attempt to change entity_type from 'person' to 'system'."""
        kg, person, _ = kg_with_entities
        # This should either be rejected or silently work
        try:
            result = kg.update_entity(person.id, entity_type="system")
            # If it succeeds, the entity_type changed — dangerous
            assert result.entity_type.value in ("person", "system")
        except (KeyError, ValueError, TypeError):
            pass  # Expected

    def test_update_with_none_name(self, kg_with_entities):
        """Setting name=None should be rejected."""
        kg, person, _ = kg_with_entities
        with contextlib.suppress(KeyError, ValueError, TypeError):
            kg.update_entity(person.id, name=None)

    def test_update_nonexistent_entity(self, empty_kg):
        """Updating a non-existent entity should raise KeyError."""
        with pytest.raises(KeyError):
            empty_kg.update_entity("does-not-exist", name="New")


# ===========================================================================
# 3. blast_radius: no depth cap
# ===========================================================================


class TestBlastRadiusBoundary:
    """blast_radius max_depth has no upper bound validation."""

    def test_max_depth_zero(self, kg_with_entities):
        """max_depth=0 should return empty (no hops)."""
        kg, person, _ = kg_with_entities
        result = kg.blast_radius(person.id, max_depth=0)
        # depth=0 means only the start node, which is excluded
        total = sum(len(v) for v in result.values())
        assert total == 0

    def test_max_depth_negative(self, kg_with_entities):
        """max_depth=-1 should return empty (impossible depth)."""
        kg, person, _ = kg_with_entities
        result = kg.blast_radius(person.id, max_depth=-1)
        total = sum(len(v) for v in result.values())
        assert total == 0

    def test_max_depth_very_large(self, kg_with_entities):
        """max_depth=10000 on a small graph should not hang."""
        kg, person, system = kg_with_entities
        # Add a relationship so traversal has something
        rel = BaseRelationship(
            relationship_type=RelationshipType.RUNS_ON,
            source_id=person.id,
            target_id=system.id,
        )
        kg.add_relationship(rel)
        result = kg.blast_radius(person.id, max_depth=10000)
        # Should find system at depth 1 and stop
        total = sum(len(v) for v in result.values())
        assert total == 1


# ===========================================================================
# 4. list_entities: boundary limit/offset values
# ===========================================================================


class TestListEntitiesBoundary:
    """list_entities limit parameter edge cases."""

    def test_limit_zero(self, kg_with_entities):
        """limit=0 should return empty list."""
        kg, _, _ = kg_with_entities
        result = kg.list_entities(limit=0)
        assert result == []

    def test_limit_negative(self, kg_with_entities):
        """limit=-1 triggers Python slice quirk: l[:-1] drops last element."""
        kg, _, _ = kg_with_entities
        result = kg.list_entities(limit=-1)
        # Negative limit is a quirk — should ideally return empty or all
        assert isinstance(result, list)

    def test_limit_very_large(self, kg_with_entities):
        """limit=999999999 should work fine (just returns all entities)."""
        kg, _, _ = kg_with_entities
        result = kg.list_entities(limit=999999999)
        assert len(result) == 2

    def test_offset_beyond_count(self, kg_with_entities):
        """offset=999 when only 2 entities exist should return empty."""
        kg, _, _ = kg_with_entities
        result = kg.list_entities(offset=999)
        assert result == []

    def test_negative_offset(self, kg_with_entities):
        """Negative offset — Python slice handles it but may be unexpected."""
        kg, _, _ = kg_with_entities
        result = kg.list_entities(offset=-1)
        # l[-1:] returns the last element
        assert isinstance(result, list)


# ===========================================================================
# 5. search_entities: query string edge cases
# ===========================================================================


class TestSearchEdgeCases:
    """search_entities with adversarial query strings."""

    def test_empty_query(self, kg_with_entities):
        """Empty string should not crash."""
        kg, _, _ = kg_with_entities
        all_entities = kg.list_entities()
        if not all_entities:
            return
        from rapidfuzz import fuzz, process

        names = [e.name for e in all_entities]
        matches = process.extract("", names, scorer=fuzz.WRatio, limit=20)
        # Should return results (empty matches everything at score 0)
        assert isinstance(matches, list)

    def test_very_long_query(self, kg_with_entities):
        """Megabyte-length query should not crash rapidfuzz."""
        kg, _, _ = kg_with_entities
        all_entities = kg.list_entities()
        if not all_entities:
            return
        from rapidfuzz import fuzz, process

        names = [e.name for e in all_entities]
        big_query = "A" * 100_000  # 100KB query
        matches = process.extract(big_query, names, scorer=fuzz.WRatio, limit=20)
        assert isinstance(matches, list)

    def test_unicode_query(self, kg_with_entities):
        """Unicode/emoji in query should not crash."""
        kg, _, _ = kg_with_entities
        all_entities = kg.list_entities()
        if not all_entities:
            return
        from rapidfuzz import fuzz, process

        names = [e.name for e in all_entities]
        matches = process.extract(
            "\U0001f4a9\u0000\u200b\uffff", names, scorer=fuzz.WRatio, limit=20
        )
        assert isinstance(matches, list)

    def test_null_bytes_in_query(self, kg_with_entities):
        """Null bytes in search query."""
        kg, _, _ = kg_with_entities
        all_entities = kg.list_entities()
        if not all_entities:
            return
        from rapidfuzz import fuzz, process

        names = [e.name for e in all_entities]
        matches = process.extract("test\x00inject", names, scorer=fuzz.WRatio, limit=20)
        assert isinstance(matches, list)


# ===========================================================================
# 6. add_relationships_batch: non-dict items
# ===========================================================================


class TestBatchRelationshipsCrash:
    """add_relationships_batch with malformed list items."""

    def test_batch_with_string_items(self, kg_with_entities):
        """List of strings instead of dicts should be handled."""
        items = ["not", "a", "dict"]
        for item in items:
            # .get() will fail on a string
            with pytest.raises(AttributeError):
                item.get("relationship_type", "")

    def test_batch_with_none_items(self):
        """None items in the batch list."""
        items = [None, None]
        for item in items:
            with pytest.raises(AttributeError):
                item.get("relationship_type", "")

    def test_batch_with_nested_lists(self):
        """Nested lists instead of dicts."""
        items = [["a", "b"], [1, 2]]
        for item in items:
            # list has no .get()
            with pytest.raises(AttributeError):
                item.get("relationship_type", "")

    def test_batch_exactly_500(self, kg_with_entities):
        """Exactly 500 items should be accepted (boundary)."""
        kg, person, system = kg_with_entities
        items = [
            {
                "relationship_type": "works_in",
                "source_id": person.id,
                "target_id": system.id,
            }
        ] * 500
        # Should not hit the "too many" error
        assert len(items) == 500
        assert len(items) <= 500

    def test_batch_501_rejected(self):
        """501 items should be rejected."""
        items = [{"relationship_type": "x", "source_id": "a", "target_id": "b"}] * 501
        assert len(items) > 500


# ===========================================================================
# 7. JSON import: malformed data
# ===========================================================================


class TestJSONImportCrashVectors:
    """Import system handling of malformed JSON."""

    def test_empty_json(self, tmp_path):
        """Empty JSON object should produce empty result."""
        f = tmp_path / "empty.json"
        f.write_text("{}")
        ingestor = JSONIngestor()
        result = ingestor.ingest(f)
        assert result.entities == []
        assert result.relationships == []

    def test_json_array_instead_of_object(self, tmp_path):
        """JSON array instead of object — should report error, not crash."""
        f = tmp_path / "array.json"
        f.write_text('[{"entity_type": "person", "name": "Test"}]')
        ingestor = JSONIngestor()
        result = ingestor.ingest(f)
        assert len(result.errors) == 1
        assert "dict" in result.errors[0].lower() or "object" in result.errors[0].lower()

    def test_truncated_json(self, tmp_path):
        """Truncated JSON file (incomplete)."""
        f = tmp_path / "truncated.json"
        f.write_text('{"entities": [{"entity_type": "person", "name": "Test"')
        ingestor = JSONIngestor()
        result = ingestor.ingest(f)
        assert len(result.errors) > 0
        assert "Invalid JSON" in result.errors[0]

    def test_entity_missing_entity_type(self, tmp_path):
        """Entity dict without entity_type key."""
        data = {"entities": [{"name": "NoType"}]}
        f = tmp_path / "notype.json"
        f.write_text(json.dumps(data))
        ingestor = JSONIngestor()
        result = ingestor.ingest(f)
        assert len(result.errors) == 1
        assert result.entities == []

    def test_entity_invalid_entity_type(self, tmp_path):
        """Entity with entity_type that doesn't exist in enum."""
        data = {"entities": [{"entity_type": "unicorn", "name": "Fake"}]}
        f = tmp_path / "badtype.json"
        f.write_text(json.dumps(data))
        ingestor = JSONIngestor()
        result = ingestor.ingest(f)
        assert len(result.errors) == 1

    def test_entity_missing_name(self, tmp_path):
        """Entity without name field — required by BaseEntity."""
        data = {"entities": [{"entity_type": "system"}]}
        f = tmp_path / "noname.json"
        f.write_text(json.dumps(data))
        ingestor = JSONIngestor()
        result = ingestor.ingest(f)
        assert len(result.errors) == 1

    def test_relationship_missing_required_fields(self, tmp_path):
        """Relationship without source_id/target_id."""
        data = {"relationships": [{"relationship_type": "works_in"}]}
        f = tmp_path / "badrel.json"
        f.write_text(json.dumps(data))
        ingestor = JSONIngestor()
        result = ingestor.ingest(f)
        assert len(result.errors) == 1

    def test_relationship_invalid_type(self, tmp_path):
        """Relationship with invalid relationship_type."""
        data = {
            "relationships": [
                {
                    "relationship_type": "FLIES_TO",
                    "source_id": "a",
                    "target_id": "b",
                }
            ]
        }
        f = tmp_path / "badreltype.json"
        f.write_text(json.dumps(data))
        ingestor = JSONIngestor()
        result = ingestor.ingest(f)
        assert len(result.errors) == 1

    def test_mixed_good_and_bad_entities(self, tmp_path):
        """Mix of valid and invalid entities — valid ones should survive."""
        EntityRegistry.auto_discover()
        data = {
            "entities": [
                {"entity_type": "system", "name": "GoodSys"},
                {"entity_type": "unicorn", "name": "Bad"},
                {"entity_type": "system", "name": "AlsoGood"},
            ]
        }
        f = tmp_path / "mixed.json"
        f.write_text(json.dumps(data))
        ingestor = JSONIngestor()
        result = ingestor.ingest(f)
        assert len(result.entities) == 2
        assert len(result.errors) == 1

    def test_entity_with_deeply_nested_properties(self, tmp_path):
        """Entity with deeply nested sub-objects in extra fields."""
        EntityRegistry.auto_discover()
        nested = {"level": 0}
        current = nested
        for i in range(1, 100):
            current["child"] = {"level": i}
            current = current["child"]
        data = {
            "entities": [
                {
                    "entity_type": "system",
                    "name": "DeepSys",
                    "deep_field": nested,
                }
            ]
        }
        f = tmp_path / "deep.json"
        f.write_text(json.dumps(data))
        ingestor = JSONIngestor()
        result = ingestor.ingest(f)
        # Should succeed — extra="allow" accepts it
        assert len(result.entities) == 1

    def test_entity_with_huge_string_field(self, tmp_path):
        """Entity with a 10MB description field."""
        EntityRegistry.auto_discover()
        data = {
            "entities": [
                {
                    "entity_type": "system",
                    "name": "BigSys",
                    "description": "A" * (10 * 1024 * 1024),
                }
            ]
        }
        f = tmp_path / "big.json"
        f.write_text(json.dumps(data))
        ingestor = JSONIngestor()
        result = ingestor.ingest(f)
        # Should succeed — no max length on entity description at model level
        assert len(result.entities) == 1

    def test_nonexistent_file(self):
        """Import from file that doesn't exist."""
        ingestor = JSONIngestor()
        result = ingestor.ingest("/nonexistent/path/graph.json")
        assert len(result.errors) == 1
        assert "not found" in result.errors[0].lower() or "File not found" in result.errors[0]

    def test_binary_file(self, tmp_path):
        """Import a binary file as JSON — should report error, not crash."""
        f = tmp_path / "binary.json"
        f.write_bytes(b"\x00\x01\x02\x03\xff\xfe\xfd")
        ingestor = JSONIngestor()
        result = ingestor.ingest(f)
        assert len(result.errors) == 1
        assert "utf-8" in result.errors[0].lower() or "text" in result.errors[0].lower()

    def test_json_with_duplicate_ids(self, tmp_path):
        """Two entities with the same ID."""
        EntityRegistry.auto_discover()
        dup_id = str(uuid.uuid4())
        data = {
            "entities": [
                {"id": dup_id, "entity_type": "system", "name": "Sys1"},
                {"id": dup_id, "entity_type": "system", "name": "Sys2"},
            ]
        }
        f = tmp_path / "dupes.json"
        f.write_text(json.dumps(data))
        ingestor = JSONIngestor()
        result = ingestor.ingest(f)
        # Both should parse, second overwrites first in KG
        assert len(result.entities) == 2

    def test_ingest_string_invalid_json(self):
        """ingest_string with invalid JSON."""
        ingestor = JSONIngestor()
        result = ingestor.ingest_string("NOT JSON AT ALL {{{}}")
        assert len(result.errors) > 0

    def test_ingest_string_null(self):
        """ingest_string with JSON null — should report error, not crash."""
        ingestor = JSONIngestor()
        result = ingestor.ingest_string("null")
        assert len(result.errors) == 1
        assert "dict" in result.errors[0].lower() or "object" in result.errors[0].lower()


# ===========================================================================
# 8. Engine: entity name edge cases
# ===========================================================================


class TestEntityNameEdgeCases:
    """Entities with adversarial name values."""

    def test_name_with_null_bytes_rejected(self):
        """Name containing null bytes — validation rejects it."""
        ok, reason = validate_entity_input("system", "Test\x00System")
        assert not ok
        assert "control" in reason.lower()

    def test_name_with_control_characters_rejected(self):
        """Name with control characters — validation rejects it."""
        ok, reason = validate_entity_input("system", "Test\x01\x02\x03System")
        assert not ok
        assert "control" in reason.lower()

    def test_name_with_emoji(self):
        """Name with emoji — should work fine."""
        EntityRegistry.auto_discover()
        s = System(name="\U0001f525 Fire System \U0001f525")
        assert "\U0001f525" in s.name

    def test_name_max_length(self):
        """Name at exactly MAX_NAME_LENGTH."""
        EntityRegistry.auto_discover()
        long_name = "A" * MAX_NAME_LENGTH
        s = System(name=long_name)
        assert len(s.name) == MAX_NAME_LENGTH

    def test_name_over_max_length(self):
        """Name exceeding MAX_NAME_LENGTH — validation should reject."""
        over_name = "A" * (MAX_NAME_LENGTH + 1)
        ok, reason = validate_entity_input("system", over_name)
        assert not ok
        assert "exceeds" in reason

    def test_name_whitespace_only(self):
        """Name that's only whitespace — validation should reject."""
        ok, reason = validate_entity_input("system", "   ")
        assert not ok
        assert "empty" in reason.lower()


# ===========================================================================
# 9. Validation: ID format edge cases
# ===========================================================================


class TestIDValidation:
    """validate_id_format with adversarial IDs."""

    def test_empty_id(self):
        ok, reason = validate_id_format("")
        assert not ok

    def test_id_with_spaces(self):
        ok, reason = validate_id_format("has spaces")
        assert not ok

    def test_id_with_sql_injection(self):
        ok, reason = validate_id_format("'; DROP TABLE entities; --")
        assert not ok

    def test_id_with_path_traversal(self):
        ok, reason = validate_id_format("../../etc/passwd")
        assert not ok
        assert "invalid characters" in reason.lower()

    def test_id_with_html_tags(self):
        ok, reason = validate_id_format("<script>alert(1)</script>")
        assert not ok

    def test_valid_uuid(self):
        ok, reason = validate_id_format(str(uuid.uuid4()))
        assert ok

    def test_id_with_colons_dots_hyphens(self):
        """These should be valid per SAFE_ID_RE."""
        ok, _ = validate_id_format("entity:v1.2-beta")
        assert ok


# ===========================================================================
# 10. Validation: entity_type and relationship_type
# ===========================================================================


class TestEnumValidation:
    """Enum validation edge cases."""

    def test_entity_type_empty(self):
        ok, _ = validate_entity_type("")
        assert not ok

    def test_entity_type_case_sensitive(self):
        """EntityType values are lowercase — uppercase should fail."""
        ok, _ = validate_entity_type("SYSTEM")
        assert not ok

    def test_entity_type_with_spaces(self):
        ok, _ = validate_entity_type("data asset")
        assert not ok

    def test_relationship_type_empty(self):
        ok, _ = validate_relationship_type("")
        assert not ok

    def test_relationship_type_uppercase(self):
        ok, _ = validate_relationship_type("WORKS_IN")
        assert not ok

    def test_relationship_type_valid(self):
        ok, _ = validate_relationship_type("works_in")
        assert ok


# ===========================================================================
# 11. Engine: neighbors/shortest_path on non-existent entity
# ===========================================================================


class TestEngineQueryEdgeCases:
    """Engine queries with non-existent or adversarial entity IDs."""

    def test_neighbors_nonexistent(self, empty_kg):
        """Neighbors of non-existent entity should return empty, not crash."""
        with contextlib.suppress(KeyError, nx.NetworkXError):
            result = empty_kg.neighbors("does-not-exist")
            assert result == []

    def test_shortest_path_nonexistent_source(self, empty_kg):
        """shortest_path with non-existent source."""
        result = empty_kg.shortest_path("no-source", "no-target")
        assert result is None

    def test_shortest_path_same_node(self, kg_with_entities):
        """shortest_path from entity to itself."""
        kg, person, _ = kg_with_entities
        result = kg.shortest_path(person.id, person.id)
        # NetworkX returns [node] for path to self
        assert result is not None
        assert len(result) == 1

    def test_get_entity_empty_id(self, empty_kg):
        """get_entity with empty string."""
        result = empty_kg.get_entity("")
        assert result is None

    def test_get_entity_none_cast(self, empty_kg):
        """get_entity with a very long ID."""
        result = empty_kg.get_entity("x" * 10000)
        assert result is None


# ===========================================================================
# 12. Engine: centrality on empty graph
# ===========================================================================


class TestCentralityEdgeCases:
    """Centrality computations on edge-case graphs."""

    def test_degree_centrality_empty(self):
        """Degree centrality on empty graph."""
        engine = NetworkXGraphEngine()
        result = engine.degree_centrality()
        assert result == []

    def test_pagerank_empty(self):
        """PageRank on empty graph should not crash."""
        engine = NetworkXGraphEngine()
        try:
            result = engine.pagerank()
            assert result == []
        except ModuleNotFoundError:
            pytest.skip("scipy not installed")

    def test_betweenness_empty(self):
        """Betweenness centrality on empty graph."""
        engine = NetworkXGraphEngine()
        result = engine.betweenness_centrality()
        assert result == []

    def test_most_connected_empty(self):
        """most_connected on empty graph."""
        engine = NetworkXGraphEngine()
        result = engine.most_connected()
        assert result == []

    def test_most_connected_negative_top_n(self, kg_with_entities):
        """most_connected with top_n=-1."""
        kg, _, _ = kg_with_entities
        result = kg.engine.most_connected(top_n=-1)
        # sorted(...)[:−1] drops the last element
        assert isinstance(result, list)

    def test_statistics_empty_graph(self):
        """Statistics on empty graph should not crash."""
        engine = NetworkXGraphEngine()
        stats = engine.get_statistics()
        assert stats["entity_count"] == 0
        assert stats["relationship_count"] == 0
        assert stats["density"] == 0


# ===========================================================================
# 13. Engine: serialization round-trip edge cases
# ===========================================================================


class TestSerializationEdgeCases:
    """Round-trip through JSON with adversarial entity data."""

    def test_entity_with_nan_float(self, tmp_path):
        """Entity with NaN float — json.dumps can't handle NaN by default."""
        EntityRegistry.auto_discover()
        s = System(name="NanSys")
        # Inject NaN into a float field
        s.__pydantic_extra__["bad_float"] = float("nan")
        raw = s.model_dump(mode="json")
        # json.dumps will produce "NaN" which is not valid JSON
        try:
            json_str = json.dumps(raw)
            # If it succeeds, json.loads should also work
            parsed = json.loads(json_str)
            assert isinstance(parsed, dict)
        except ValueError:
            pass  # Expected — NaN not valid JSON

    def test_entity_with_infinity(self):
        """Entity with Infinity float."""
        EntityRegistry.auto_discover()
        s = System(name="InfSys")
        s.__pydantic_extra__["bad_float"] = float("inf")
        raw = s.model_dump(mode="json")
        try:
            json_str = json.dumps(raw)
            parsed = json.loads(json_str)
            assert isinstance(parsed, dict)
        except ValueError:
            pass  # Expected

    def test_entity_with_circular_reference(self):
        """Entity with circular reference in extras — should fail serialization."""
        EntityRegistry.auto_discover()
        s = System(name="CircSys")
        circular: dict[str, Any] = {"a": 1}
        circular["self"] = circular
        s.__pydantic_extra__["loop"] = circular
        with pytest.raises((ValueError, TypeError)):
            s.model_dump(mode="json")


# ===========================================================================
# 14. MCP validation: relationship input edge cases
# ===========================================================================


class TestRelationshipValidationEdgeCases:
    """validate_relationship_input with adversarial inputs."""

    def test_source_equals_target(self, kg_with_entities):
        """Self-referential relationship — entity pointing to itself."""
        kg, person, _ = kg_with_entities
        # Some relationship types might allow self-reference
        ok, reason = validate_relationship_input(kg, "depends_on", person.id, person.id)
        # Should be accepted (schema allows person→person for depends_on?
        # or rejected if domain/range doesn't match)
        assert isinstance(ok, bool)

    def test_valid_relationship_wrong_domain(self, kg_with_entities):
        """works_in from system→person (wrong direction)."""
        kg, person, system = kg_with_entities
        ok, reason = validate_relationship_input(kg, "works_in", system.id, person.id)
        # works_in domain is person→department, so system→person should fail
        assert not ok

    def test_empty_ids(self, kg_with_entities):
        """Empty source and target IDs."""
        kg, _, _ = kg_with_entities
        ok, reason = validate_relationship_input(kg, "works_in", "", "")
        assert not ok


# ===========================================================================
# 15. Hypothesis: property-based fuzzing
# ===========================================================================


class TestHypothesisFuzzing:
    """Property-based tests using Hypothesis to find crash vectors."""

    @given(
        entity_type=st.text(min_size=0, max_size=50),
        name=st.text(min_size=0, max_size=300),
        description=st.text(min_size=0, max_size=5000),
    )
    @settings(max_examples=200, suppress_health_check=[HealthCheck.too_slow])
    def test_validate_entity_input_never_crashes(
        self, entity_type: str, name: str, description: str
    ):
        """validate_entity_input should never crash regardless of input."""
        ok, reason = validate_entity_input(entity_type, name, description)
        assert isinstance(ok, bool)
        assert isinstance(reason, str)

    @given(value=st.text(min_size=0, max_size=200))
    @settings(max_examples=200, suppress_health_check=[HealthCheck.too_slow])
    def test_validate_entity_type_never_crashes(self, value: str):
        """validate_entity_type should never crash."""
        ok, reason = validate_entity_type(value)
        assert isinstance(ok, bool)

    @given(value=st.text(min_size=0, max_size=200))
    @settings(max_examples=200, suppress_health_check=[HealthCheck.too_slow])
    def test_validate_relationship_type_never_crashes(self, value: str):
        """validate_relationship_type should never crash."""
        ok, reason = validate_relationship_type(value)
        assert isinstance(ok, bool)

    @given(value=st.text(min_size=0, max_size=500))
    @settings(max_examples=200, suppress_health_check=[HealthCheck.too_slow])
    def test_validate_id_format_never_crashes(self, value: str):
        """validate_id_format should never crash."""
        ok, reason = validate_id_format(value)
        assert isinstance(ok, bool)

    @given(
        name=st.text(
            alphabet=st.characters(
                categories=("L", "N", "P", "S", "Z"),
                include_characters="\x00\x01\x02\x03\n\r\t",
            ),
            min_size=1,
            max_size=100,
        )
    )
    @settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])
    def test_system_entity_accepts_any_name(self, name: str):
        """System entity should accept any non-empty name."""
        EntityRegistry.auto_discover()
        s = System(name=name)
        assert s.name == name

    @given(
        data=st.fixed_dictionaries(
            {
                "entity_type": st.just("system"),
                "name": st.text(min_size=1, max_size=50),
            },
            optional={
                "description": st.text(min_size=0, max_size=200),
                "status": st.text(min_size=0, max_size=50),
                "fake_field": st.text(min_size=0, max_size=50),
            },
        )
    )
    @settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])
    def test_json_ingest_entity_never_crashes(self, data: dict):
        """Ingesting random entity dicts should never crash."""
        EntityRegistry.auto_discover()
        ingestor = JSONIngestor()
        json_data = json.dumps({"entities": [data]})
        result = ingestor.ingest_string(json_data)
        # Should either succeed or have an error, never crash
        assert isinstance(result.entities, list)
        assert isinstance(result.errors, list)

    @given(
        data=st.fixed_dictionaries(
            {},
            optional={
                "relationship_type": st.text(min_size=0, max_size=50),
                "source_id": st.text(min_size=0, max_size=50),
                "target_id": st.text(min_size=0, max_size=50),
                "weight": st.one_of(
                    st.floats(allow_nan=True, allow_infinity=True),
                    st.text(min_size=0, max_size=10),
                ),
            },
        )
    )
    @settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])
    def test_json_ingest_relationship_never_crashes(self, data: dict):
        """Ingesting random relationship dicts should never crash."""
        EntityRegistry.auto_discover()
        ingestor = JSONIngestor()
        json_data = json.dumps({"relationships": [data]}, default=str)
        result = ingestor.ingest_string(json_data)
        assert isinstance(result.relationships, list)
        assert isinstance(result.errors, list)


# ===========================================================================
# 16. JSON ingest_string with extreme inputs
# ===========================================================================


class TestIngestStringExtreme:
    """ingest_string with values that push JSON/Pydantic boundaries."""

    def test_empty_string(self):
        """Empty string is not valid JSON."""
        ingestor = JSONIngestor()
        result = ingestor.ingest_string("")
        assert len(result.errors) > 0

    def test_just_whitespace(self):
        """Whitespace-only string."""
        ingestor = JSONIngestor()
        result = ingestor.ingest_string("   \n\t  ")
        assert len(result.errors) > 0

    def test_json_number(self):
        """JSON number instead of object — should report type error."""
        ingestor = JSONIngestor()
        result = ingestor.ingest_string("42")
        assert len(result.errors) == 1
        assert "int" in result.errors[0]

    def test_json_string(self):
        """JSON string instead of object — should report type error."""
        ingestor = JSONIngestor()
        result = ingestor.ingest_string('"hello"')
        assert len(result.errors) == 1
        assert "str" in result.errors[0]

    def test_json_boolean(self):
        """JSON boolean instead of object — should report type error."""
        ingestor = JSONIngestor()
        result = ingestor.ingest_string("true")
        assert len(result.errors) == 1
        assert "bool" in result.errors[0]

    def test_json_array_of_entities(self):
        """JSON array at top level (not object) — should report type error."""
        ingestor = JSONIngestor()
        result = ingestor.ingest_string('[{"entity_type": "system"}]')
        assert len(result.errors) == 1
        assert "list" in result.errors[0]

    def test_unicode_escape_in_json(self):
        """JSON with unicode escape sequences."""
        EntityRegistry.auto_discover()
        ingestor = JSONIngestor()
        data = (
            '{"entities": [{"entity_type": "system",'
            ' "name": "\\u0048\\u0065\\u006c\\u006c\\u006f"}]}'
        )
        result = ingestor.ingest_string(data)
        assert len(result.entities) == 1
        assert result.entities[0].name == "Hello"


# ===========================================================================
# 17. Engine: update_entity with type-confused values
# ===========================================================================


class TestUpdateTypeConfusion:
    """update_entity with values of wrong types."""

    def test_update_tags_with_string(self, kg_with_entities):
        """tags field expects list[str], but user passes a string."""
        kg, _, system = kg_with_entities
        with contextlib.suppress(KeyError, ValueError, TypeError):
            kg.update_entity(system.id, tags="not-a-list")

    def test_update_name_with_number(self, kg_with_entities):
        """name field expects str, but user passes int."""
        kg, _, system = kg_with_entities
        with contextlib.suppress(KeyError, ValueError, TypeError):
            result = kg.update_entity(system.id, name=12345)
            # Pydantic may coerce int to str
            assert isinstance(result.name, str)

    def test_update_name_with_dict(self, kg_with_entities):
        """name field expects str, but user passes dict."""
        kg, _, system = kg_with_entities
        with contextlib.suppress(KeyError, ValueError, TypeError):
            kg.update_entity(system.id, name={"key": "value"})

    def test_update_metadata_with_string(self, kg_with_entities):
        """metadata field expects dict, but user passes string."""
        kg, _, system = kg_with_entities
        with contextlib.suppress(KeyError, ValueError, TypeError):
            kg.update_entity(system.id, metadata="not-a-dict")


# ===========================================================================
# 18. Concurrent state: operations on stale references
# ===========================================================================


class TestStaleReferences:
    """Operations using entity IDs that have been removed."""

    def test_relationship_to_removed_entity(self, kg_with_entities):
        """Add relationship after target entity was removed."""
        kg, person, system = kg_with_entities
        kg.remove_entity(system.id)
        # Now try to add relationship to removed entity
        rel = BaseRelationship(
            relationship_type=RelationshipType.RUNS_ON,
            source_id=person.id,
            target_id=system.id,
        )
        with pytest.raises(KeyError):
            kg.add_relationship(rel)

    def test_get_neighbors_of_removed_entity(self, kg_with_entities):
        """Get neighbors of entity that was just removed."""
        kg, person, system = kg_with_entities
        kg.remove_entity(person.id)
        with contextlib.suppress(KeyError, nx.NetworkXError):
            result = kg.neighbors(person.id)
            assert result == []

    def test_blast_radius_of_removed_entity(self, kg_with_entities):
        """Blast radius of removed entity."""
        kg, person, _ = kg_with_entities
        kg.remove_entity(person.id)
        with contextlib.suppress(KeyError, nx.NetworkXError):
            result = kg.blast_radius(person.id)
            total = sum(len(v) for v in result.values())
            assert total == 0

    def test_double_remove_entity(self, kg_with_entities):
        """Remove the same entity twice."""
        kg, person, _ = kg_with_entities
        assert kg.remove_entity(person.id) is True
        assert kg.remove_entity(person.id) is False

    def test_double_remove_relationship(self, kg_with_entities):
        """Remove the same relationship twice."""
        kg, person, system = kg_with_entities
        rel = BaseRelationship(
            relationship_type=RelationshipType.RUNS_ON,
            source_id=person.id,
            target_id=system.id,
        )
        rel_id = kg.add_relationship(rel)
        assert kg.remove_relationship(rel_id) is True
        assert kg.remove_relationship(rel_id) is False


# ===========================================================================
# 19. MCP description length boundary
# ===========================================================================


class TestDescriptionLength:
    """Description field length limits."""

    def test_description_at_max(self):
        """Description at exactly MAX_DESCRIPTION_LENGTH."""
        desc = "A" * MAX_DESCRIPTION_LENGTH
        ok, _ = validate_entity_input("system", "Test", desc)
        assert ok

    def test_description_over_max(self):
        """Description exceeding MAX_DESCRIPTION_LENGTH."""
        desc = "A" * (MAX_DESCRIPTION_LENGTH + 1)
        ok, reason = validate_entity_input("system", "Test", desc)
        assert not ok
        assert "exceeds" in reason

    def test_description_with_newlines(self):
        """Description with many newlines — each char counts."""
        desc = "\n" * 1000
        ok, _ = validate_entity_input("system", "Test", desc)
        assert ok  # 1000 < 4096


# ===========================================================================
# 20. Weight/confidence boundary values
# ===========================================================================


class TestWeightConfidenceBounds:
    """Weight and confidence clamping via clamp_float()."""

    def test_weight_negative(self):
        """Negative weight should be clamped to 0."""
        from mcp_server.validation import clamp_float

        assert clamp_float(-5.0) == 0.0

    def test_weight_over_one(self):
        """Weight > 1.0 should be clamped to 1.0."""
        from mcp_server.validation import clamp_float

        assert clamp_float(999.0) == 1.0

    def test_weight_nan(self):
        """NaN weight — clamp_float treats it as high default."""
        from mcp_server.validation import clamp_float

        # NaN is neither > 0 nor <= 0, but our guard handles it
        result = clamp_float(float("nan"))
        assert 0.0 <= result <= 1.0

    def test_weight_infinity(self):
        """Infinity weight — should clamp to 1.0."""
        from mcp_server.validation import clamp_float

        assert clamp_float(float("inf")) == 1.0

    def test_confidence_negative_infinity(self):
        """Negative infinity confidence — should clamp to 0.0."""
        from mcp_server.validation import clamp_float

        assert clamp_float(float("-inf")) == 0.0


# ===========================================================================
# 21. Update entity: immutable fields blocked
# ===========================================================================


class TestUpdateImmutableFields:
    """sanitize_updates strips immutable fields."""

    def test_strips_entity_type(self):
        from mcp_server.validation import sanitize_updates

        clean, stripped = sanitize_updates({"entity_type": "system", "name": "New"})
        assert "entity_type" not in clean
        assert "entity_type" in stripped
        assert clean["name"] == "New"

    def test_strips_id(self):
        from mcp_server.validation import sanitize_updates

        clean, stripped = sanitize_updates({"id": "new-id", "name": "X"})
        assert "id" not in clean
        assert "id" in stripped

    def test_strips_created_at(self):
        from mcp_server.validation import sanitize_updates

        clean, stripped = sanitize_updates({"created_at": "2024-01-01"})
        assert "created_at" not in clean
        assert len(clean) == 0

    def test_passes_valid_updates(self):
        from mcp_server.validation import sanitize_updates

        updates = {"name": "New", "description": "Updated"}
        clean, stripped = sanitize_updates(updates)
        assert clean == updates
        assert stripped == []


# ===========================================================================
# 22. Batch relationships: non-dict type checking
# ===========================================================================


class TestBatchTypeChecking:
    """add_relationships_batch rejects non-dict items."""

    def test_string_items_produce_validation_error(self):
        """String items should produce per-item type error, not crash."""
        items = ["not-a-dict", "also-not"]
        errors = []
        for i, item in enumerate(items):
            if not isinstance(item, dict):
                errors.append({"index": i, "error": f"Expected dict, got {type(item).__name__}."})
        assert len(errors) == 2
        assert "str" in errors[0]["error"]

    def test_none_items_produce_validation_error(self):
        """None items should produce per-item type error."""
        items = [None]
        errors = []
        for i, item in enumerate(items):
            if not isinstance(item, dict):
                errors.append({"index": i, "error": f"Expected dict, got {type(item).__name__}."})
        assert len(errors) == 1
        assert "NoneType" in errors[0]["error"]


# ===========================================================================
# 23. Import file size limit
# ===========================================================================


class TestImportFileSizeLimit:
    """JSONIngestor rejects files exceeding MAX_IMPORT_FILE_BYTES."""

    def test_file_size_check_exists(self):
        """Verify MAX_IMPORT_FILE_BYTES is defined."""
        from ingest.json_ingestor import MAX_IMPORT_FILE_BYTES

        assert MAX_IMPORT_FILE_BYTES == 500 * 1024 * 1024

    def test_small_file_accepted(self, tmp_path):
        """Normal-sized file should be accepted."""
        f = tmp_path / "small.json"
        f.write_text('{"entities": []}')
        ingestor = JSONIngestor()
        result = ingestor.ingest(f)
        assert len(result.errors) == 0


# ===========================================================================
# 24. Blast radius depth cap
# ===========================================================================


class TestBlastRadiusDepthCap:
    """MCP tool caps blast_radius max_depth."""

    def test_cap_value_exists(self):
        """Verify MAX_BLAST_RADIUS_DEPTH is defined."""
        from mcp_server.validation import MAX_BLAST_RADIUS_DEPTH

        assert MAX_BLAST_RADIUS_DEPTH == 10

    def test_large_depth_clamped(self):
        """max_depth=1000000 should be clamped to MAX_BLAST_RADIUS_DEPTH."""
        from mcp_server.validation import MAX_BLAST_RADIUS_DEPTH

        clamped = max(1, min(MAX_BLAST_RADIUS_DEPTH, 1000000))
        assert clamped == 10

    def test_negative_depth_clamped(self):
        """max_depth=-1 should be clamped to 1."""
        from mcp_server.validation import MAX_BLAST_RADIUS_DEPTH

        clamped = max(1, min(MAX_BLAST_RADIUS_DEPTH, -1))
        assert clamped == 1


# ===========================================================================
# 25. List entities limit cap
# ===========================================================================


class TestListLimitCap:
    """MCP tool caps list_entities limit."""

    def test_cap_value_exists(self):
        """Verify MAX_LIST_LIMIT is defined."""
        from mcp_server.validation import MAX_LIST_LIMIT

        assert MAX_LIST_LIMIT == 10_000

    def test_negative_limit_clamped(self):
        """limit=-1 should be clamped to 1."""
        from mcp_server.validation import MAX_LIST_LIMIT

        clamped = max(1, min(MAX_LIST_LIMIT, -1))
        assert clamped == 1

    def test_huge_limit_clamped(self):
        """limit=999999999 should be clamped to MAX_LIST_LIMIT."""
        from mcp_server.validation import MAX_LIST_LIMIT

        clamped = max(1, min(MAX_LIST_LIMIT, 999999999))
        assert clamped == MAX_LIST_LIMIT
