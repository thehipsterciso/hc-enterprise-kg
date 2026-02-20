"""Tests for SyntheticOrchestrator."""

from graph.knowledge_graph import KnowledgeGraph
from synthetic.orchestrator import SyntheticOrchestrator
from synthetic.profiles.tech_company import mid_size_tech_company


class TestSyntheticOrchestrator:
    def test_generate_small_org(self):
        kg = KnowledgeGraph()
        profile = mid_size_tech_company(50)
        orchestrator = SyntheticOrchestrator(kg, profile, seed=42)
        counts = orchestrator.generate()

        assert counts["person"] == 50
        assert counts["department"] == 10
        assert counts["_relationships"] > 0
        assert kg.statistics["entity_count"] > 50
        assert kg.statistics["relationship_count"] > 0

    def test_generate_with_seed_reproducible(self):
        kg1 = KnowledgeGraph()
        kg2 = KnowledgeGraph()
        profile = mid_size_tech_company(20)

        SyntheticOrchestrator(kg1, profile, seed=42).generate()
        SyntheticOrchestrator(kg2, profile, seed=42).generate()

        assert kg1.statistics["entity_count"] == kg2.statistics["entity_count"]
        assert kg1.statistics["relationship_count"] == kg2.statistics["relationship_count"]

    def test_roles_generated(self):
        """RoleGenerator runs and produces Role entities for each department."""
        kg = KnowledgeGraph()
        profile = mid_size_tech_company(20)
        counts = SyntheticOrchestrator(kg, profile, seed=42).generate()

        assert "role" in counts
        assert counts["role"] > 0
        # Should have at least one role per department
        assert counts["role"] >= counts["department"]

    def test_event_log_populated(self):
        kg = KnowledgeGraph(track_events=True)
        profile = mid_size_tech_company(10)
        SyntheticOrchestrator(kg, profile, seed=42).generate()

        assert len(kg.event_log) > 0

    def test_count_overrides_apply(self):
        """Entity count overrides should produce exact counts."""
        kg = KnowledgeGraph()
        profile = mid_size_tech_company(500)
        overrides = {"system": 25, "vendor": 5, "control": 3}
        counts = SyntheticOrchestrator(kg, profile, seed=42, count_overrides=overrides).generate()

        assert counts["system"] == 25
        assert counts["vendor"] == 5
        assert counts["control"] == 3
        # Non-overridden types should still be present and > 0
        assert counts["person"] == 500
        assert counts["department"] > 0
        assert counts["risk"] > 0

    def test_count_overrides_empty_dict_is_noop(self):
        """Empty overrides dict should not change behavior."""
        kg1 = KnowledgeGraph()
        kg2 = KnowledgeGraph()
        profile = mid_size_tech_company(50)

        counts_no_override = SyntheticOrchestrator(kg1, profile, seed=42).generate()
        counts_empty_override = SyntheticOrchestrator(
            kg2, profile, seed=42, count_overrides={}
        ).generate()

        assert counts_no_override["system"] == counts_empty_override["system"]
        assert counts_no_override["vendor"] == counts_empty_override["vendor"]

    def test_count_overrides_zero_suppresses_entity(self):
        """Override of 0 should suppress generation of that entity type."""
        kg = KnowledgeGraph()
        profile = mid_size_tech_company(50)
        overrides = {"threat_actor": 0}
        counts = SyntheticOrchestrator(kg, profile, seed=42, count_overrides=overrides).generate()

        assert "threat_actor" not in counts or counts.get("threat_actor", 0) == 0
