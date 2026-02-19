"""Tests for SyntheticOrchestrator."""

from hc_enterprise_kg.graph.knowledge_graph import KnowledgeGraph
from hc_enterprise_kg.synthetic.orchestrator import SyntheticOrchestrator
from hc_enterprise_kg.synthetic.profiles.tech_company import mid_size_tech_company


class TestSyntheticOrchestrator:
    def test_generate_small_org(self):
        kg = KnowledgeGraph()
        profile = mid_size_tech_company(50)
        orchestrator = SyntheticOrchestrator(kg, profile, seed=42)
        counts = orchestrator.generate()

        assert counts["person"] == 50
        assert counts["department"] == 10
        assert counts["_relationships"] > 0
        assert kg.statistics["total_entities"] > 50
        assert kg.statistics["total_relationships"] > 0

    def test_generate_with_seed_reproducible(self):
        kg1 = KnowledgeGraph()
        kg2 = KnowledgeGraph()
        profile = mid_size_tech_company(20)

        SyntheticOrchestrator(kg1, profile, seed=42).generate()
        SyntheticOrchestrator(kg2, profile, seed=42).generate()

        assert kg1.statistics["total_entities"] == kg2.statistics["total_entities"]
        assert kg1.statistics["total_relationships"] == kg2.statistics["total_relationships"]

    def test_event_log_populated(self):
        kg = KnowledgeGraph(track_events=True)
        profile = mid_size_tech_company(10)
        SyntheticOrchestrator(kg, profile, seed=42).generate()

        assert len(kg.event_log) > 0
