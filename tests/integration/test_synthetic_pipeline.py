"""Integration tests for the synthetic generation pipeline."""

from hc_enterprise_kg.domain.base import EntityType, RelationshipType
from hc_enterprise_kg.graph.knowledge_graph import KnowledgeGraph
from hc_enterprise_kg.synthetic.orchestrator import SyntheticOrchestrator
from hc_enterprise_kg.synthetic.profiles.tech_company import mid_size_tech_company
from hc_enterprise_kg.synthetic.profiles.healthcare_org import healthcare_org
from hc_enterprise_kg.synthetic.profiles.financial_org import financial_org


class TestSyntheticPipeline:
    def test_tech_company_generation(self):
        kg = KnowledgeGraph()
        profile = mid_size_tech_company(50)
        orchestrator = SyntheticOrchestrator(kg, profile, seed=42)
        counts = orchestrator.generate()

        assert counts["person"] == 50
        assert counts.get("department", 0) > 0
        assert counts.get("system", 0) > 0
        assert counts.get("_relationships", 0) > 0

        stats = kg.statistics
        assert stats["entity_count"] > 50  # People + other entities

    def test_healthcare_org_generation(self):
        kg = KnowledgeGraph()
        profile = healthcare_org(30)
        orchestrator = SyntheticOrchestrator(kg, profile, seed=42)
        counts = orchestrator.generate()

        assert counts["person"] == 30
        assert counts.get("_relationships", 0) > 0

    def test_financial_org_generation(self):
        kg = KnowledgeGraph()
        profile = financial_org(30)
        orchestrator = SyntheticOrchestrator(kg, profile, seed=42)
        counts = orchestrator.generate()

        assert counts["person"] == 30
        assert counts.get("_relationships", 0) > 0

    def test_generation_with_query(self):
        kg = KnowledgeGraph()
        profile = mid_size_tech_company(20)
        orchestrator = SyntheticOrchestrator(kg, profile, seed=42)
        orchestrator.generate()

        people = kg.query().entities(EntityType.PERSON).execute()
        assert len(people) == 20

        departments = kg.query().entities(EntityType.DEPARTMENT).execute()
        assert len(departments) > 0

    def test_generation_with_export(self):
        import json

        kg = KnowledgeGraph()
        profile = mid_size_tech_company(15)
        orchestrator = SyntheticOrchestrator(kg, profile, seed=42)
        orchestrator.generate()

        from hc_enterprise_kg.export.json_export import JSONExporter
        exporter = JSONExporter()
        result = exporter.export_string(kg.engine)
        data = json.loads(result)

        assert len(data["entities"]) > 15
        assert len(data["relationships"]) > 0
        assert data["statistics"]["entity_count"] == len(data["entities"])

    def test_event_log_recorded(self):
        kg = KnowledgeGraph(track_events=True)
        profile = mid_size_tech_company(10)
        orchestrator = SyntheticOrchestrator(kg, profile, seed=42)
        orchestrator.generate()

        assert len(kg.event_log) > 0

    def test_seed_reproducibility(self):
        kg1 = KnowledgeGraph()
        profile1 = mid_size_tech_company(20)
        orch1 = SyntheticOrchestrator(kg1, profile1, seed=123)
        counts1 = orch1.generate()

        kg2 = KnowledgeGraph()
        profile2 = mid_size_tech_company(20)
        orch2 = SyntheticOrchestrator(kg2, profile2, seed=123)
        counts2 = orch2.generate()

        assert counts1 == counts2
        assert kg1.statistics["entity_count"] == kg2.statistics["entity_count"]
