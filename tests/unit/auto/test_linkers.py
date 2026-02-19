"""Tests for entity linkers."""

from unittest.mock import MagicMock, patch

from hc_enterprise_kg.auto.linkers.heuristic_linker import HeuristicLinker
from hc_enterprise_kg.domain.base import EntityType, RelationshipType
from hc_enterprise_kg.domain.entities.department import Department
from hc_enterprise_kg.domain.entities.person import Person
from hc_enterprise_kg.domain.entities.system import System


class TestHeuristicLinker:
    def test_fk_detection_links_person_to_department(self):
        dept = Department(id="d1", name="Engineering")
        person = Person(
            id="p1",
            first_name="Alice",
            last_name="Smith",
            name="Alice Smith",
            email="a@b.com",
            department_id="d1",
        )
        linker = HeuristicLinker()
        result = linker.link([person, dept])
        assert len(result.relationships) >= 1
        fk_rels = [r for r in result.relationships if r.properties.get("_link_method") == "fk_detection"]
        assert len(fk_rels) == 1
        assert fk_rels[0].source_id == "p1"
        assert fk_rels[0].target_id == "d1"

    def test_no_links_for_unrelated_entities(self):
        dept = Department(id="d1", name="Engineering")
        sys = System(id="s1", name="WebApp", system_type="application")
        linker = HeuristicLinker(name_match_threshold=99.0)
        result = linker.link([dept, sys])
        # No FK attrs linking these, names don't match
        assert len(result.relationships) == 0

    def test_name_matching_links_similar_names(self):
        # Person named "Engineering" should fuzzy-match Department "Engineering"
        person = Person(
            id="p1", first_name="Engineering", last_name="Team",
            name="Engineering Team", email="eng@test.com",
        )
        dept = Department(id="d1", name="Engineering Team")
        linker = HeuristicLinker(name_match_threshold=80.0)
        result = linker.link([person, dept])
        name_rels = [r for r in result.relationships if r.properties.get("_link_method") == "name_matching"]
        assert len(name_rels) >= 1

    def test_high_threshold_prevents_links(self):
        person = Person(
            id="p1", first_name="Alice", last_name="Smith",
            name="Alice Smith", email="a@b.com",
        )
        dept = Department(id="d1", name="Engineering")
        linker = HeuristicLinker(name_match_threshold=99.0)
        result = linker.link([person, dept])
        name_rels = [r for r in result.relationships if r.properties.get("_link_method") == "name_matching"]
        assert len(name_rels) == 0

    def test_linking_result_has_method(self):
        linker = HeuristicLinker()
        result = linker.link([])
        assert result.link_method == "heuristic"

    def test_relationships_have_confidence(self):
        dept = Department(id="d1", name="Engineering")
        person = Person(
            id="p1", first_name="Alice", last_name="Smith",
            name="Alice Smith", email="a@b.com",
            department_id="d1",
        )
        linker = HeuristicLinker()
        result = linker.link([person, dept])
        for rel in result.relationships:
            assert 0.0 <= rel.confidence <= 1.0


class TestEmbeddingLinker:
    def test_embedding_linker_returns_result_with_few_entities(self):
        from hc_enterprise_kg.auto.linkers.embedding_linker import EmbeddingLinker

        linker = EmbeddingLinker(similarity_threshold=0.7)
        # Less than 2 entities => no linking
        person = Person(id="p1", first_name="A", last_name="B", name="A B", email="a@b.com")
        result = linker.link([person])
        assert result.link_method == "embedding"
        assert len(result.relationships) == 0

    def test_embedding_linker_missing_library(self):
        from hc_enterprise_kg.auto.linkers.embedding_linker import EmbeddingLinker

        linker = EmbeddingLinker()
        linker._model = None  # Reset

        person = Person(id="p1", first_name="A", last_name="B", name="A B", email="a@b.com")
        dept = Department(id="d1", name="Engineering")

        # Mock the import to fail
        with patch.object(linker, "_load_model", side_effect=ImportError("no module")):
            result = linker.link([person, dept])
            assert len(result.errors) >= 1
