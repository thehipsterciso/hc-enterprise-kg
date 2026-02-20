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
