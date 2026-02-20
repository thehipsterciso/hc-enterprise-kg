"""Stress tests — large graph generation, performance, and roundtrip validation."""

from __future__ import annotations

import json
import time

from domain.base import EntityType
from export.json_export import JSONExporter
from graph.knowledge_graph import KnowledgeGraph
from ingest.json_ingestor import JSONIngestor
from synthetic.orchestrator import SyntheticOrchestrator
from synthetic.profiles.tech_company import mid_size_tech_company

# All 30 entity types expected in a full generation
ALL_ENTITY_TYPES = {
    "person", "department", "role", "system", "network",
    "data_asset", "policy", "vendor", "location",
    "vulnerability", "threat_actor", "incident",
    "regulation", "control", "risk", "threat",
    "integration", "data_domain", "data_flow",
    "organizational_unit", "business_capability",
    "site", "geography", "jurisdiction",
    "product_portfolio", "product",
    "market_segment", "customer",
    "contract", "initiative",
}


class TestLargeGraphGeneration:
    """Tests with 500+ employee graphs."""

    def test_500_employee_generation(self):
        """Generate a 500-employee org — all types present, reasonable timing."""
        kg = KnowledgeGraph()
        profile = mid_size_tech_company(500)

        start = time.time()
        counts = SyntheticOrchestrator(kg, profile, seed=42).generate()
        elapsed = time.time() - start

        assert counts["person"] == 500
        assert elapsed < 30, f"Generation took {elapsed:.1f}s — expected <30s"

        stats = kg.statistics
        assert stats["entity_count"] > 500
        assert stats["relationship_count"] > 0

        # All 30 types should be present
        generated_types = set(stats["entity_types"].keys())
        missing = ALL_ENTITY_TYPES - generated_types
        assert not missing, f"Missing types in 500-employee graph: {missing}"

    def test_1000_employee_generation(self):
        """Generate a 1000-employee org."""
        kg = KnowledgeGraph()
        profile = mid_size_tech_company(1000)

        start = time.time()
        counts = SyntheticOrchestrator(kg, profile, seed=99).generate()
        elapsed = time.time() - start

        assert counts["person"] == 1000
        assert elapsed < 60, f"Generation took {elapsed:.1f}s — expected <60s"

        stats = kg.statistics
        assert stats["entity_count"] > 1000
        assert stats["relationship_count"] > stats["entity_count"]


class TestExportImportRoundtrip:
    """Verify export → import preserves graph fidelity."""

    def test_roundtrip_preserves_counts(self):
        """Export to JSON, reimport, verify entity/relationship counts match."""
        kg = KnowledgeGraph()
        profile = mid_size_tech_company(100)
        SyntheticOrchestrator(kg, profile, seed=42).generate()

        original_stats = kg.statistics

        # Export
        json_str = JSONExporter().export_string(kg.engine)
        data = json.loads(json_str)

        assert len(data["entities"]) == original_stats["entity_count"]
        assert len(data["relationships"]) == original_stats["relationship_count"]

        # Reimport
        ingestor = JSONIngestor()
        result = ingestor.ingest_string(json_str)

        assert not result.errors, f"Import errors: {result.errors}"
        assert len(result.entities) == original_stats["entity_count"]
        assert len(result.relationships) == original_stats["relationship_count"]

    def test_roundtrip_preserves_all_types(self):
        """All entity types survive export → import."""
        kg = KnowledgeGraph()
        profile = mid_size_tech_company(50)
        SyntheticOrchestrator(kg, profile, seed=42).generate()

        json_str = JSONExporter().export_string(kg.engine)
        data = json.loads(json_str)

        exported_types = {e["entity_type"] for e in data["entities"]}
        missing = ALL_ENTITY_TYPES - exported_types
        assert not missing, f"Export missing types: {missing}"

        result = JSONIngestor().ingest_string(json_str)
        imported_types = {e.entity_type.value for e in result.entities}
        missing_after = ALL_ENTITY_TYPES - imported_types
        assert not missing_after, f"Import missing types: {missing_after}"


class TestBlastRadiusPerformance:
    """Blast radius should complete in reasonable time even on large graphs."""

    def test_blast_radius_timing(self):
        """Blast radius on a 200-employee graph should complete in <2s."""
        kg = KnowledgeGraph()
        profile = mid_size_tech_company(200)
        SyntheticOrchestrator(kg, profile, seed=42).generate()

        # Pick a well-connected entity
        systems = kg.query().entities(EntityType.SYSTEM).execute()
        assert len(systems) > 0
        system_id = systems[0].id

        start = time.time()
        result = kg.blast_radius(system_id, max_depth=3)
        elapsed = time.time() - start

        assert elapsed < 2.0, f"Blast radius took {elapsed:.2f}s — expected <2s"
        total = sum(len(entities) for entities in result.values())
        assert total > 0, "Blast radius returned no affected entities"


class TestQueryPerformance:
    """Query operations should be efficient on medium-large graphs."""

    def test_list_entities_with_type_filter(self):
        """Listing entities by type should be fast on a 300-employee graph."""
        kg = KnowledgeGraph()
        profile = mid_size_tech_company(300)
        SyntheticOrchestrator(kg, profile, seed=42).generate()

        start = time.time()
        people = kg.query().entities(EntityType.PERSON).execute()
        elapsed = time.time() - start

        assert len(people) == 300
        assert elapsed < 1.0, f"Query took {elapsed:.2f}s — expected <1s"

    def test_statistics_performance(self):
        """Computing statistics should be fast."""
        kg = KnowledgeGraph()
        profile = mid_size_tech_company(300)
        SyntheticOrchestrator(kg, profile, seed=42).generate()

        start = time.time()
        stats = kg.statistics
        elapsed = time.time() - start

        assert elapsed < 1.0, f"Statistics took {elapsed:.2f}s — expected <1s"
        assert stats["entity_count"] > 300
