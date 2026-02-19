"""Integration tests for the automatic KG construction pipeline."""

import tempfile
from pathlib import Path

from hc_enterprise_kg.auto.extractors.csv_extractor import CSVExtractor
from hc_enterprise_kg.auto.extractors.rule_based import RuleBasedExtractor
from hc_enterprise_kg.auto.linkers.heuristic_linker import HeuristicLinker
from hc_enterprise_kg.auto.pipeline import AutoKGPipeline
from hc_enterprise_kg.auto.resolvers.dedup_resolver import DedupResolver
from hc_enterprise_kg.domain.base import EntityType
from hc_enterprise_kg.graph.knowledge_graph import KnowledgeGraph

SAMPLE_CSV = """name,email,department,title
Alice Smith,alice@acme.com,Engineering,Software Engineer
Bob Jones,bob@acme.com,Marketing,Marketing Manager
Carol White,carol@acme.com,Engineering,Senior Engineer
"""


class TestAutoPipelineIntegration:
    def test_csv_to_kg_pipeline(self):
        kg = KnowledgeGraph()

        # Write CSV to temp file
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            f.write(SAMPLE_CSV)
            csv_path = f.name

        pipeline = AutoKGPipeline(
            kg,
            extractors=[CSVExtractor()],
            linkers=[HeuristicLinker()],
            resolver=DedupResolver(),
            use_llm=False,
            use_embeddings=False,
        )
        result = pipeline.run(csv_path)

        assert result.stats["status"] == "complete"
        assert result.stats["entities_extracted"] >= 3
        assert result.stats["entities_loaded"] >= 3

        # Clean up
        Path(csv_path).unlink()

    def test_csv_string_pipeline(self):
        kg = KnowledgeGraph()
        pipeline = AutoKGPipeline(
            kg,
            extractors=[CSVExtractor()],
            linkers=[],
            resolver=DedupResolver(),
            use_llm=False,
            use_embeddings=False,
        )
        result = pipeline.run(SAMPLE_CSV)

        assert result.stats["status"] == "complete"
        assert result.stats["entities_loaded"] >= 3

    def test_rule_based_extraction_from_text(self):
        kg = KnowledgeGraph()
        text = """
        Contact alice@acme.com or bob@test.org for help.
        Server 10.0.1.50 has vulnerability CVE-2024-1234.
        """
        pipeline = AutoKGPipeline(
            kg,
            extractors=[RuleBasedExtractor()],
            linkers=[],
            resolver=DedupResolver(),
            use_llm=False,
            use_embeddings=False,
        )
        result = pipeline.run(text)

        assert result.stats["status"] == "complete"
        assert result.stats["entities_extracted"] >= 2

    def test_dedup_in_pipeline(self):
        kg = KnowledgeGraph()
        csv_content = """name,email,department,title
Alice Smith,alice@acme.com,Engineering,Engineer
Alice Smith,,Engineering,Senior Engineer
"""
        pipeline = AutoKGPipeline(
            kg,
            extractors=[CSVExtractor()],
            linkers=[],
            resolver=DedupResolver(name_threshold=90.0),
            use_llm=False,
            use_embeddings=False,
        )
        result = pipeline.run(csv_content)

        assert result.stats["status"] == "complete"
        # Two rows extracted, but should merge into one
        assert result.stats["entities_extracted"] == 2
        assert result.stats["duplicates_merged"] >= 1

    def test_pipeline_loads_into_queryable_kg(self):
        kg = KnowledgeGraph()
        pipeline = AutoKGPipeline(
            kg,
            extractors=[CSVExtractor()],
            linkers=[HeuristicLinker()],
            resolver=DedupResolver(),
            use_llm=False,
            use_embeddings=False,
        )
        pipeline.run(SAMPLE_CSV)

        # Should be able to query entities after pipeline
        people = kg.query().entities(EntityType.PERSON).execute()
        assert len(people) >= 3
