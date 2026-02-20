"""Tests for relationship enrichment: metadata, new types, and mirror fields."""

import random

from domain.base import EntityType, RelationshipType
from graph.knowledge_graph import KnowledgeGraph
from synthetic.orchestrator import SyntheticOrchestrator
from synthetic.profiles.tech_company import mid_size_tech_company


def _make_graph(emp: int = 100, seed: int = 42):
    """Generate a full graph and return (kg, orchestrator)."""
    random.seed(seed)
    profile = mid_size_tech_company(emp)
    kg = KnowledgeGraph()
    orch = SyntheticOrchestrator(kg, profile, seed=seed)
    orch.generate()
    return kg, orch


class TestRelationshipMetadata:
    """All relationships should have enriched weight/confidence/properties."""

    def setup_method(self):
        self.kg, self.orch = _make_graph(100)
        self.rels = list(self.kg._engine._graph.edges(data=True))

    def test_relationships_have_varied_weights(self):
        """Not all weights should be 1.0 — at least 20% should differ."""
        edges = self.kg._engine._graph.edges(data=True)
        weights = [data.get("weight", 1.0) for _, _, data in edges]
        non_default = sum(1 for w in weights if w != 1.0)
        assert len(weights) > 0
        ratio = non_default / len(weights)
        assert ratio >= 0.15, f"Only {ratio:.0%} of relationships have non-default weights"

    def test_relationships_have_varied_confidence(self):
        """Not all confidence values should be 1.0."""
        edges = self.kg._engine._graph.edges(data=True)
        confidences = [data.get("confidence", 1.0) for _, _, data in edges]
        non_default = sum(1 for c in confidences if c != 1.0)
        assert len(confidences) > 0
        ratio = non_default / len(confidences)
        assert ratio >= 0.15, f"Only {ratio:.0%} have non-default confidence"

    def test_relationships_have_properties(self):
        """At least 50% of relationships should have non-empty properties."""
        edges = self.kg._engine._graph.edges(data=True)
        props = [data.get("properties", {}) for _, _, data in edges]
        non_empty = sum(1 for p in props if p)
        assert len(props) > 0
        ratio = non_empty / len(props)
        assert ratio >= 0.40, f"Only {ratio:.0%} have non-empty properties"


class TestNewRelationshipTypes:
    """12 new relationship types should be woven."""

    def setup_method(self):
        self.kg, self.orch = _make_graph(100)

    def _count_rel_type(self, rel_type: RelationshipType) -> int:
        """Count relationships of a given type in the graph."""
        count = 0
        for _, _, data in self.kg._engine._graph.edges(data=True):
            if data.get("relationship_type") == rel_type.value:
                count += 1
        return count

    def _get_rel_types(self) -> set[str]:
        """Get all unique relationship types in the graph."""
        return {
            data.get("relationship_type")
            for _, _, data in self.kg._engine._graph.edges(data=True)
            if data.get("relationship_type")
        }

    def test_at_least_30_relationship_types(self):
        """Should have >= 30 distinct relationship types (was 22 before)."""
        types = self._get_rel_types()
        assert len(types) >= 30, f"Only {len(types)} relationship types: {sorted(types)}"

    def test_creates_risk_woven(self):
        assert self._count_rel_type(RelationshipType.CREATES_RISK) > 0

    def test_subject_to_woven(self):
        assert self._count_rel_type(RelationshipType.SUBJECT_TO) > 0

    def test_addresses_woven(self):
        assert self._count_rel_type(RelationshipType.ADDRESSES) > 0

    def test_flows_to_woven(self):
        assert self._count_rel_type(RelationshipType.FLOWS_TO) > 0

    def test_classified_as_woven(self):
        assert self._count_rel_type(RelationshipType.CLASSIFIED_AS) > 0

    def test_realized_by_woven(self):
        assert self._count_rel_type(RelationshipType.REALIZED_BY) > 0

    def test_contains_woven(self):
        assert self._count_rel_type(RelationshipType.CONTAINS) > 0

    def test_delivers_woven(self):
        assert self._count_rel_type(RelationshipType.DELIVERS) > 0

    def test_serves_woven(self):
        assert self._count_rel_type(RelationshipType.SERVES) > 0

    def test_member_of_woven(self):
        assert self._count_rel_type(RelationshipType.MEMBER_OF) > 0

    def test_initiatives_impact_risks(self):
        """Initiatives should IMPACTS Risks (new link)."""
        count = 0
        for _, _, data in self.kg._engine._graph.edges(data=True):
            if (
                data.get("relationship_type") == RelationshipType.IMPACTS.value
                and data.get("properties", {}).get("impact_area") == "risk_reduction"
            ):
                count += 1
        assert count > 0


class TestMirrorFields:
    """Entity mirror fields should be populated from relationships."""

    def setup_method(self):
        self.kg, self.orch = _make_graph(100)
        self.ctx = self.orch.context

    def test_person_holds_roles_populated(self):
        """At least some persons should have holds_roles populated."""
        people = self.ctx.get_entities(EntityType.PERSON)
        with_roles = [
            p for p in people if getattr(p, "holds_roles", None) and len(p.holds_roles) > 0
        ]
        assert len(with_roles) > 0, "No persons have holds_roles populated"

    def test_role_filled_by_persons_populated(self):
        """At least some roles should have filled_by_persons populated."""
        roles = self.ctx.get_entities(EntityType.ROLE)
        with_persons = [
            r
            for r in roles
            if getattr(r, "filled_by_persons", None) and len(r.filled_by_persons) > 0
        ]
        assert len(with_persons) > 0, "No roles have filled_by_persons populated"

    def test_role_headcount_filled_matches(self):
        """Role.headcount_filled should match len(filled_by_persons)."""
        roles = self.ctx.get_entities(EntityType.ROLE)
        for role in roles:
            filled = getattr(role, "filled_by_persons", [])
            hc = getattr(role, "headcount_filled", 0)
            if isinstance(filled, list) and len(filled) > 0:
                assert hc == len(filled), (
                    f"Role '{role.name}': headcount_filled={hc} "
                    f"but filled_by_persons has {len(filled)}"
                )

    def test_person_located_at_populated(self):
        """At least some persons should have located_at populated."""
        people = self.ctx.get_entities(EntityType.PERSON)
        with_location = [
            p for p in people if getattr(p, "located_at", None) and len(p.located_at) > 0
        ]
        assert len(with_location) > 0, "No persons have located_at populated"

    def test_person_participates_in_initiatives(self):
        """~20% of people should have initiative participation."""
        people = self.ctx.get_entities(EntityType.PERSON)
        participating = [
            p
            for p in people
            if getattr(p, "participates_in_initiatives", None)
            and len(p.participates_in_initiatives) > 0
        ]
        assert len(participating) > 0, "No persons participate in initiatives"
        ratio = len(participating) / len(people)
        assert ratio >= 0.10, f"Only {ratio:.0%} participate in initiatives"
