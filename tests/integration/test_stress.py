"""Stress tests — scaled generation, performance gates, and roundtrip validation."""

from __future__ import annotations

import json
import time

import pytest

from domain.base import EntityType
from export.json_export import JSONExporter
from graph.knowledge_graph import KnowledgeGraph
from ingest.json_ingestor import JSONIngestor
from synthetic.orchestrator import SyntheticOrchestrator
from synthetic.profiles.financial_org import financial_org
from synthetic.profiles.healthcare_org import healthcare_org
from synthetic.profiles.tech_company import mid_size_tech_company

# All 30 entity types expected in a full generation
ALL_ENTITY_TYPES = {
    "person",
    "department",
    "role",
    "system",
    "network",
    "data_asset",
    "policy",
    "vendor",
    "location",
    "vulnerability",
    "threat_actor",
    "incident",
    "regulation",
    "control",
    "risk",
    "threat",
    "integration",
    "data_domain",
    "data_flow",
    "organizational_unit",
    "business_capability",
    "site",
    "geography",
    "jurisdiction",
    "product_portfolio",
    "product",
    "market_segment",
    "customer",
    "contract",
    "initiative",
}


# ---------------------------------------------------------------------------
# Parametrized scale tests — 100 to 20,000 employees
# ---------------------------------------------------------------------------


@pytest.mark.slow
class TestScaledGeneration:
    """Verify generation scales correctly from startup to large enterprise."""

    @pytest.mark.parametrize(
        "emp,max_sec",
        [
            (100, 10),
            (500, 30),
            (1000, 60),
            (5000, 180),
            (10000, 300),
            (20000, 600),
        ],
    )
    def test_generation_at_scale(self, emp: int, max_sec: int):
        """Generate a tech company at various employee counts within time gates."""
        kg = KnowledgeGraph()
        profile = mid_size_tech_company(emp)

        start = time.time()
        counts = SyntheticOrchestrator(kg, profile, seed=42).generate()
        elapsed = time.time() - start

        assert counts["person"] == emp
        assert elapsed < max_sec, (
            f"{emp}-employee generation took {elapsed:.1f}s (limit {max_sec}s)"
        )

        stats = kg.statistics
        assert stats["entity_count"] > emp
        assert stats["relationship_count"] > 0

        # All 30 entity types should be present
        generated_types = set(stats["entity_types"].keys())
        missing = ALL_ENTITY_TYPES - generated_types
        assert not missing, f"Missing types at {emp} employees: {missing}"

    def test_scaling_ratios(self):
        """A 20k org must have >10x the non-person entities of a 100-person org."""
        kg_small = KnowledgeGraph()
        SyntheticOrchestrator(kg_small, mid_size_tech_company(100), seed=1).generate()
        small_entities = kg_small.statistics["entity_count"]
        small_non_person = small_entities - 100

        kg_large = KnowledgeGraph()
        SyntheticOrchestrator(kg_large, mid_size_tech_company(20000), seed=1).generate()
        large_entities = kg_large.statistics["entity_count"]
        large_non_person = large_entities - 20000

        ratio = large_non_person / max(1, small_non_person)
        assert ratio > 10, (
            f"20k org has only {ratio:.1f}x non-person entities vs 100 org "
            f"({large_non_person} vs {small_non_person}). Scaling is broken."
        )


# ---------------------------------------------------------------------------
# Multi-industry profile tests
# ---------------------------------------------------------------------------


@pytest.mark.slow
class TestIndustryProfiles:
    """Verify all industry profiles generate valid graphs at scale."""

    @pytest.mark.parametrize(
        "profile_fn,emp",
        [
            (mid_size_tech_company, 1000),
            (financial_org, 1000),
            (healthcare_org, 1000),
        ],
    )
    def test_industry_generation(self, profile_fn, emp: int):
        """Each industry profile generates all 30 types with valid counts."""
        kg = KnowledgeGraph()
        profile = profile_fn(emp)

        start = time.time()
        counts = SyntheticOrchestrator(kg, profile, seed=42).generate()
        elapsed = time.time() - start

        assert counts["person"] == emp
        assert elapsed < 60, f"{profile.industry} generation took {elapsed:.1f}s"

        stats = kg.statistics
        generated_types = set(stats["entity_types"].keys())
        missing = ALL_ENTITY_TYPES - generated_types
        assert not missing, f"{profile.industry} missing types: {missing}"

    def test_financial_has_more_controls_than_tech(self):
        """Financial services should generate denser controls than tech."""
        emp = 2000

        kg_tech = KnowledgeGraph()
        SyntheticOrchestrator(kg_tech, mid_size_tech_company(emp), seed=42).generate()
        tech_controls = kg_tech.statistics["entity_types"].get("control", 0)

        kg_fin = KnowledgeGraph()
        SyntheticOrchestrator(kg_fin, financial_org(emp), seed=42).generate()
        fin_controls = kg_fin.statistics["entity_types"].get("control", 0)

        assert fin_controls > tech_controls, (
            f"Financial ({fin_controls}) should have more controls than tech ({tech_controls})"
        )

    def test_healthcare_has_more_data_assets_than_tech(self):
        """Healthcare should generate denser data assets than tech."""
        emp = 2000

        kg_tech = KnowledgeGraph()
        SyntheticOrchestrator(kg_tech, mid_size_tech_company(emp), seed=42).generate()
        tech_data = kg_tech.statistics["entity_types"].get("data_asset", 0)

        kg_hc = KnowledgeGraph()
        SyntheticOrchestrator(kg_hc, healthcare_org(emp), seed=42).generate()
        hc_data = kg_hc.statistics["entity_types"].get("data_asset", 0)

        assert hc_data > tech_data, (
            f"Healthcare ({hc_data}) should have more data assets than tech ({tech_data})"
        )


# ---------------------------------------------------------------------------
# Export/Import roundtrip
# ---------------------------------------------------------------------------


class TestExportImportRoundtrip:
    """Verify export -> import preserves graph fidelity."""

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
        """All entity types survive export -> import."""
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


# ---------------------------------------------------------------------------
# Performance gates
# ---------------------------------------------------------------------------


class TestPerformanceGates:
    """Query and analytics operations within time bounds."""

    def test_blast_radius_timing(self):
        """Blast radius on a 200-employee graph should complete in <2s."""
        kg = KnowledgeGraph()
        profile = mid_size_tech_company(200)
        SyntheticOrchestrator(kg, profile, seed=42).generate()

        systems = kg.query().entities(EntityType.SYSTEM).execute()
        assert len(systems) > 0
        system_id = systems[0].id

        start = time.time()
        result = kg.blast_radius(system_id, max_depth=3)
        elapsed = time.time() - start

        assert elapsed < 2.0, f"Blast radius took {elapsed:.2f}s"
        total = sum(len(entities) for entities in result.values())
        assert total > 0, "Blast radius returned no affected entities"

    def test_list_entities_with_type_filter(self):
        """Listing entities by type should be fast on a 300-employee graph."""
        kg = KnowledgeGraph()
        profile = mid_size_tech_company(300)
        SyntheticOrchestrator(kg, profile, seed=42).generate()

        start = time.time()
        people = kg.query().entities(EntityType.PERSON).execute()
        elapsed = time.time() - start

        assert len(people) == 300
        assert elapsed < 1.0, f"Query took {elapsed:.2f}s"

    def test_statistics_performance(self):
        """Computing statistics should be fast."""
        kg = KnowledgeGraph()
        profile = mid_size_tech_company(300)
        SyntheticOrchestrator(kg, profile, seed=42).generate()

        start = time.time()
        stats = kg.statistics
        elapsed = time.time() - start

        assert elapsed < 1.0, f"Statistics took {elapsed:.2f}s"
        assert stats["entity_count"] > 300

    @pytest.mark.slow
    def test_analytics_at_5k_employees(self):
        """Analytics operations on a 5k graph stay within bounds."""
        kg = KnowledgeGraph()
        profile = mid_size_tech_company(5000)
        SyntheticOrchestrator(kg, profile, seed=42).generate()

        # Statistics
        start = time.time()
        stats = kg.statistics
        elapsed = time.time() - start
        assert elapsed < 5.0, f"Statistics at 5k took {elapsed:.2f}s"
        assert stats["entity_count"] > 5000

        # Blast radius
        systems = kg.query().entities(EntityType.SYSTEM).execute()
        start = time.time()
        kg.blast_radius(systems[0].id, max_depth=2)
        elapsed = time.time() - start
        assert elapsed < 10.0, f"Blast radius at 5k took {elapsed:.2f}s"
