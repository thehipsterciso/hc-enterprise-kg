"""Graph structural integrity tests — validate graph invariants after generation."""

from __future__ import annotations

import pytest

from domain.base import EntityType, RelationshipType
from graph.knowledge_graph import KnowledgeGraph
from synthetic.orchestrator import SyntheticOrchestrator
from synthetic.profiles.tech_company import mid_size_tech_company


@pytest.fixture(scope="module")
def generated_kg() -> KnowledgeGraph:
    """Generate a 100-employee graph once for all integrity tests."""
    kg = KnowledgeGraph()
    profile = mid_size_tech_company(100)
    SyntheticOrchestrator(kg, profile, seed=42).generate()
    return kg


class TestReferentialIntegrity:
    """Every relationship must point to entities that exist in the graph."""

    def test_no_dangling_source_ids(self, generated_kg: KnowledgeGraph):
        """All relationship source_ids must reference existing entities."""
        engine = generated_kg.engine
        all_entity_ids = {e.id for e in engine.list_entities()}
        dangling = []

        for entity in engine.list_entities():
            for rel in engine.get_relationships(entity.id, direction="out"):
                if rel.source_id not in all_entity_ids:
                    dangling.append(f"{rel.relationship_type}: source {rel.source_id} missing")

        assert not dangling, f"Found {len(dangling)} dangling source refs:\n" + "\n".join(
            dangling[:10]
        )

    def test_no_dangling_target_ids(self, generated_kg: KnowledgeGraph):
        """All relationship target_ids must reference existing entities."""
        engine = generated_kg.engine
        all_entity_ids = {e.id for e in engine.list_entities()}
        dangling = []

        for entity in engine.list_entities():
            for rel in engine.get_relationships(entity.id, direction="out"):
                if rel.target_id not in all_entity_ids:
                    dangling.append(f"{rel.relationship_type}: target {rel.target_id} missing")

        assert not dangling, f"Found {len(dangling)} dangling target refs:\n" + "\n".join(
            dangling[:10]
        )


class TestSelfLoops:
    """No entity should have a relationship to itself."""

    def test_no_self_loops(self, generated_kg: KnowledgeGraph):
        """No relationship should have source_id == target_id."""
        engine = generated_kg.engine
        self_loops = []

        for entity in engine.list_entities():
            for rel in engine.get_relationships(entity.id, direction="out"):
                if rel.source_id == rel.target_id:
                    self_loops.append(f"{rel.relationship_type}: {entity.name} ({entity.id})")

        assert not self_loops, f"Found {len(self_loops)} self-loops:\n" + "\n".join(self_loops[:10])


class TestReportsToDAG:
    """REPORTS_TO relationships must form a DAG (no circular reporting chains)."""

    def test_reports_to_is_acyclic(self, generated_kg: KnowledgeGraph):
        """Detect cycles in the REPORTS_TO subgraph via DFS."""
        engine = generated_kg.engine
        people = engine.list_entities(entity_type=EntityType.PERSON)

        # Build adjacency: person_id → list of person_ids they report to
        reports_to: dict[str, list[str]] = {}
        for person in people:
            rels = engine.get_relationships(
                person.id,
                direction="out",
                relationship_type=RelationshipType.REPORTS_TO,
            )
            targets = [r.target_id for r in rels]
            if targets:
                reports_to[person.id] = targets

        # DFS cycle detection (0=unvisited, 1=in-progress, 2=done)
        in_progress, done = 1, 2
        color: dict[str, int] = {pid: 0 for pid in reports_to}
        cycles: list[str] = []

        def dfs(node: str, path: list[str]) -> None:
            color[node] = in_progress
            for neighbor in reports_to.get(node, []):
                if neighbor in color:
                    if color[neighbor] == in_progress:
                        cycles.append(f"Cycle: {' → '.join(path + [neighbor])}")
                        return
                    if color[neighbor] == 0:
                        dfs(neighbor, path + [neighbor])
            color[node] = done

        for node_id in reports_to:
            if color[node_id] == 0:
                dfs(node_id, [node_id])

        assert not cycles, "Found cycles in REPORTS_TO:\n" + "\n".join(cycles[:5])


class TestDegreeDistribution:
    """Generated graphs should have realistic degree distributions."""

    def test_no_isolated_people(self, generated_kg: KnowledgeGraph):
        """Every person should have at least one relationship (works_in, has_role, etc.)."""
        engine = generated_kg.engine
        people = engine.list_entities(entity_type=EntityType.PERSON)
        isolated = []

        for person in people:
            rels = engine.get_relationships(person.id, direction="both")
            if len(rels) == 0:
                isolated.append(f"{person.name} ({person.id})")

        assert not isolated, (
            f"Found {len(isolated)} isolated people (no relationships):\n"
            + "\n".join(isolated[:10])
        )

    def test_no_isolated_departments(self, generated_kg: KnowledgeGraph):
        """Every department should have at least one person."""
        engine = generated_kg.engine
        departments = engine.list_entities(entity_type=EntityType.DEPARTMENT)
        empty_depts = []

        for dept in departments:
            members = engine.neighbors(
                dept.id,
                direction="in",
                relationship_type=RelationshipType.WORKS_IN,
            )
            if len(members) == 0:
                empty_depts.append(f"{dept.name} ({dept.id})")

        assert not empty_depts, (
            f"Found {len(empty_depts)} departments with no members:\n" + "\n".join(empty_depts[:10])
        )

    def test_systems_not_over_connected(self, generated_kg: KnowledgeGraph):
        """No system should have more than 50% of all relationships."""
        engine = generated_kg.engine
        stats = engine.get_statistics()
        total_rels = stats["relationship_count"]
        systems = engine.list_entities(entity_type=EntityType.SYSTEM)

        for system in systems:
            rels = engine.get_relationships(system.id, direction="both")
            ratio = len(rels) / total_rels if total_rels > 0 else 0
            assert ratio < 0.5, (
                f"System '{system.name}' has {len(rels)}/{total_rels} relationships"
                f" ({ratio:.1%}) — likely a wiring bug"
            )


class TestEntityTypeCoverage:
    """All 30 entity types should be generated."""

    def test_all_entity_types_present(self, generated_kg: KnowledgeGraph):
        """Every EntityType enum member should have at least one instance."""
        stats = generated_kg.statistics
        generated_types = set(stats["entity_types"].keys())
        all_types = {et.value for et in EntityType}
        missing = all_types - generated_types
        assert not missing, f"Missing entity types: {missing}"


class TestRelationshipTypeCoverage:
    """Audit which relationship types are actually woven."""

    def test_minimum_relationship_types(self, generated_kg: KnowledgeGraph):
        """At least 15 relationship types should be present in a generated graph."""
        stats = generated_kg.statistics
        rel_types = set(stats.get("relationship_types", {}).keys())
        assert len(rel_types) >= 15, (
            f"Only {len(rel_types)} relationship types woven "
            f"(out of {len(RelationshipType)}): {sorted(rel_types)}"
        )

    def test_report_unwoven_relationship_types(self, generated_kg: KnowledgeGraph):
        """Document which relationship types have zero instances (informational)."""
        stats = generated_kg.statistics
        woven_types = set(stats.get("relationship_types", {}).keys())
        all_types = {rt.value for rt in RelationshipType}
        unwoven = all_types - woven_types
        # This is informational — we track progress on wiring all 52 types
        # Currently ~33 are unwoven. As the number drops, tighten this threshold.
        assert len(unwoven) <= 35, (
            f"Too many unwoven relationship types ({len(unwoven)}/{len(all_types)}): "
            f"{sorted(unwoven)[:10]}..."
        )


class TestGraphConsistency:
    """Cross-entity consistency checks."""

    def test_person_department_consistency(self, generated_kg: KnowledgeGraph):
        """Every person's WORKS_IN target should be a Department entity."""
        engine = generated_kg.engine
        people = engine.list_entities(entity_type=EntityType.PERSON)
        invalid = []

        for person in people:
            rels = engine.get_relationships(
                person.id,
                direction="out",
                relationship_type=RelationshipType.WORKS_IN,
            )
            for rel in rels:
                target = engine.get_entity(rel.target_id)
                if target and target.entity_type != EntityType.DEPARTMENT:
                    invalid.append(
                        f"{person.name} WORKS_IN {target.name} "
                        f"(type: {target.entity_type}, expected: department)"
                    )

        assert not invalid, f"Found {len(invalid)} invalid WORKS_IN targets:\n" + "\n".join(
            invalid[:10]
        )

    def test_reports_to_type_consistency(self, generated_kg: KnowledgeGraph):
        """REPORTS_TO should only connect Person to Person."""
        engine = generated_kg.engine
        people = engine.list_entities(entity_type=EntityType.PERSON)
        invalid = []

        for person in people:
            rels = engine.get_relationships(
                person.id, direction="out", relationship_type=RelationshipType.REPORTS_TO
            )
            for rel in rels:
                target = engine.get_entity(rel.target_id)
                if target and target.entity_type != EntityType.PERSON:
                    invalid.append(
                        f"{person.name} REPORTS_TO {target.name} (type: {target.entity_type})"
                    )

        assert not invalid, f"Found {len(invalid)} non-person REPORTS_TO targets:\n" + "\n".join(
            invalid[:10]
        )

    def test_manages_type_consistency(self, generated_kg: KnowledgeGraph):
        """MANAGES should connect Person to Person or Person to Department."""
        engine = generated_kg.engine
        people = engine.list_entities(entity_type=EntityType.PERSON)
        valid_target_types = {EntityType.PERSON, EntityType.DEPARTMENT}
        invalid = []

        for person in people:
            rels = engine.get_relationships(
                person.id, direction="out", relationship_type=RelationshipType.MANAGES
            )
            for rel in rels:
                target = engine.get_entity(rel.target_id)
                if target and target.entity_type not in valid_target_types:
                    invalid.append(
                        f"{person.name} MANAGES {target.name} (type: {target.entity_type})"
                    )

        assert not invalid, f"Found {len(invalid)} invalid MANAGES targets:\n" + "\n".join(
            invalid[:10]
        )

    def test_vendor_relationship_type_consistency(self, generated_kg: KnowledgeGraph):
        """SUPPLIED_BY should point from System to Vendor."""
        engine = generated_kg.engine
        systems = engine.list_entities(entity_type=EntityType.SYSTEM)
        invalid = []

        for system in systems:
            rels = engine.get_relationships(
                system.id,
                direction="out",
                relationship_type=RelationshipType.SUPPLIED_BY,
            )
            for rel in rels:
                target = engine.get_entity(rel.target_id)
                if target and target.entity_type != EntityType.VENDOR:
                    invalid.append(
                        f"{system.name} SUPPLIED_BY {target.name} (type: {target.entity_type})"
                    )

        assert not invalid, f"Found {len(invalid)} invalid SUPPLIED_BY targets:\n" + "\n".join(
            invalid[:10]
        )
