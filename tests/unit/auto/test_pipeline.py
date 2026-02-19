"""Tests for the AutoKGPipeline."""

from unittest.mock import MagicMock

from auto.base import ExtractionResult, LinkingResult, ResolutionResult
from auto.pipeline import AutoKGPipeline
from domain.base import BaseRelationship, RelationshipType
from domain.entities.department import Department
from domain.entities.person import Person
from graph.knowledge_graph import KnowledgeGraph


class TestAutoKGPipeline:
    def test_pipeline_with_no_entities_extracted(self, kg: KnowledgeGraph):
        mock_extractor = MagicMock()
        mock_extractor.can_handle.return_value = True
        mock_extractor.extract.return_value = ExtractionResult(source="test")

        pipeline = AutoKGPipeline(
            kg,
            extractors=[mock_extractor],
            linkers=[],
            use_llm=False,
            use_embeddings=False,
        )
        result = pipeline.run("test data")
        assert result.stats.get("status") == "no_entities_extracted"

    def test_pipeline_extracts_and_loads_entities(self, kg: KnowledgeGraph):
        person = Person(
            id="p1",
            first_name="Alice",
            last_name="Smith",
            name="Alice Smith",
            email="a@b.com",
        )

        mock_extractor = MagicMock()
        mock_extractor.can_handle.return_value = True
        mock_extractor.extract.return_value = ExtractionResult(entities=[person], source="test")

        mock_linker = MagicMock()
        mock_linker.link.return_value = LinkingResult(link_method="mock")

        mock_resolver = MagicMock()
        mock_resolver.resolve.return_value = ResolutionResult(entities=[person])

        pipeline = AutoKGPipeline(
            kg,
            extractors=[mock_extractor],
            linkers=[mock_linker],
            resolver=mock_resolver,
            use_llm=False,
            use_embeddings=False,
        )
        result = pipeline.run("test data")

        assert result.stats["status"] == "complete"
        assert result.stats["entities_extracted"] == 1
        assert result.stats["entities_loaded"] == 1
        assert kg.get_entity("p1") is not None

    def test_pipeline_links_relationships(self, kg: KnowledgeGraph):
        person = Person(
            id="p1",
            first_name="Alice",
            last_name="Smith",
            name="Alice Smith",
            email="a@b.com",
        )
        dept = Department(id="d1", name="Engineering")

        mock_extractor = MagicMock()
        mock_extractor.can_handle.return_value = True
        mock_extractor.extract.return_value = ExtractionResult(
            entities=[person, dept], source="test"
        )

        rel = BaseRelationship(
            relationship_type=RelationshipType.WORKS_IN,
            source_id="p1",
            target_id="d1",
        )
        mock_linker = MagicMock()
        mock_linker.link.return_value = LinkingResult(relationships=[rel], link_method="mock")

        mock_resolver = MagicMock()
        mock_resolver.resolve.return_value = ResolutionResult(entities=[person, dept])

        pipeline = AutoKGPipeline(
            kg,
            extractors=[mock_extractor],
            linkers=[mock_linker],
            resolver=mock_resolver,
        )
        result = pipeline.run("test")

        assert result.stats["relationships_loaded"] >= 1

    def test_pipeline_dedup_merges_entities(self, kg: KnowledgeGraph):
        p1 = Person(
            id="p1", first_name="Alice", last_name="Smith", name="Alice Smith", email="a@b.com"
        )
        p2 = Person(id="p2", first_name="Alice", last_name="Smith", name="Alice Smith", email="")

        mock_extractor = MagicMock()
        mock_extractor.can_handle.return_value = True
        mock_extractor.extract.return_value = ExtractionResult(entities=[p1, p2], source="test")

        mock_linker = MagicMock()
        mock_linker.link.return_value = LinkingResult(link_method="mock")

        mock_resolver = MagicMock()
        mock_resolver.resolve.return_value = ResolutionResult(
            entities=[p1],
            merged_entity_ids=[("p1", "p2")],
        )

        pipeline = AutoKGPipeline(
            kg,
            extractors=[mock_extractor],
            linkers=[mock_linker],
            resolver=mock_resolver,
        )
        result = pipeline.run("test")

        assert result.stats["duplicates_merged"] == 1
        assert result.stats["entities_after_dedup"] == 1

    def test_pipeline_skips_extractor_that_cannot_handle(self, kg: KnowledgeGraph):
        mock_extractor = MagicMock()
        mock_extractor.can_handle.return_value = False

        pipeline = AutoKGPipeline(
            kg,
            extractors=[mock_extractor],
            linkers=[],
            use_llm=False,
            use_embeddings=False,
        )
        result = pipeline.run("test")
        mock_extractor.extract.assert_not_called()
        assert result.stats.get("status") == "no_entities_extracted"
