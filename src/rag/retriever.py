"""GraphRAG retrieval pipeline: question -> entities + relationships -> formatted context."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from domain.base import BaseEntity, BaseRelationship, EntityType
from rag.context_builder import ContextBuilder
from rag.search import GraphSearch

if TYPE_CHECKING:
    from graph.knowledge_graph import KnowledgeGraph

# Common English stopwords to filter out of keyword extraction
_STOPWORDS = frozenset(
    {
        "a",
        "an",
        "the",
        "is",
        "are",
        "was",
        "were",
        "be",
        "been",
        "being",
        "have",
        "has",
        "had",
        "do",
        "does",
        "did",
        "will",
        "would",
        "could",
        "should",
        "may",
        "might",
        "shall",
        "can",
        "need",
        "dare",
        "ought",
        "used",
        "to",
        "of",
        "in",
        "for",
        "on",
        "with",
        "at",
        "by",
        "from",
        "as",
        "into",
        "through",
        "during",
        "before",
        "after",
        "above",
        "below",
        "between",
        "out",
        "off",
        "over",
        "under",
        "again",
        "further",
        "then",
        "once",
        "here",
        "there",
        "when",
        "where",
        "why",
        "how",
        "all",
        "both",
        "each",
        "few",
        "more",
        "most",
        "other",
        "some",
        "such",
        "no",
        "nor",
        "not",
        "only",
        "own",
        "same",
        "so",
        "than",
        "too",
        "very",
        "just",
        "because",
        "but",
        "and",
        "or",
        "if",
        "while",
        "about",
        "what",
        "which",
        "who",
        "whom",
        "this",
        "that",
        "these",
        "those",
        "am",
        "it",
        "its",
        "i",
        "me",
        "my",
        "we",
        "our",
        "you",
        "your",
        "he",
        "him",
        "his",
        "she",
        "her",
        "they",
        "them",
        "their",
    }
)

# Mapping of common plural forms to entity types
_PLURAL_MAP = {
    "people": EntityType.PERSON,
    "persons": EntityType.PERSON,
    "departments": EntityType.DEPARTMENT,
    "roles": EntityType.ROLE,
    "systems": EntityType.SYSTEM,
    "networks": EntityType.NETWORK,
    "policies": EntityType.POLICY,
    "vendors": EntityType.VENDOR,
    "locations": EntityType.LOCATION,
    "vulnerabilities": EntityType.VULNERABILITY,
    "incidents": EntityType.INCIDENT,
}


@dataclass
class RetrievalResult:
    """Result of a GraphRAG retrieval operation."""

    entities: list[BaseEntity] = field(default_factory=list)
    relationships: list[BaseRelationship] = field(default_factory=list)
    context: str = ""
    stats: dict = field(default_factory=dict)


class GraphRAGRetriever:
    """Main retrieval pipeline that searches the knowledge graph and formats context for LLMs."""

    def __init__(
        self,
        fuzzy_threshold: float = 50.0,
        neighbor_depth: int = 1,
    ) -> None:
        self._fuzzy_threshold = fuzzy_threshold
        self._neighbor_depth = neighbor_depth
        self._search = GraphSearch()
        self._context_builder = ContextBuilder()

    def retrieve(
        self,
        question: str,
        kg: KnowledgeGraph,
        top_k: int = 20,
    ) -> RetrievalResult:
        """Retrieve relevant entities and relationships from the KG for a question.

        Steps:
            1. Extract keywords from the question
            2. Fuzzy search entity names for each keyword
            3. Pull entities of any mentioned entity types
            4. Deduplicate matched entities
            5. Expand context with immediate neighbors
            6. Collect relationships between result entities
            7. Score and rank entities
            8. Trim to top_k
            9. Build formatted context string
            10. Return RetrievalResult

        Args:
            question: The natural language question.
            kg: The knowledge graph to search.
            top_k: Maximum number of entities to include.

        Returns:
            A RetrievalResult with entities, relationships, context, and stats.
        """
        # Step 1: Extract keywords
        keywords, type_matches = self._extract_keywords(question)

        # Step 2: Fuzzy search for each keyword
        entity_scores: dict[str, tuple[BaseEntity, float]] = {}
        for keyword in keywords:
            matches = self._search.search_by_name(kg, keyword, top_k=top_k)
            for entity, score in matches:
                if score < self._fuzzy_threshold:
                    continue
                existing = entity_scores.get(entity.id)
                if existing is None or score > existing[1]:
                    entity_scores[entity.id] = (entity, score)

        # Step 3: Pull entities by type for any mentioned entity types
        for entity_type in type_matches:
            type_entities = self._search.search_by_type(kg, entity_type, limit=top_k)
            for entity in type_entities:
                if entity.id not in entity_scores:
                    # Give type-matched entities a baseline score
                    entity_scores[entity.id] = (entity, 60.0)

        # Step 4: Deduplicate is handled by the dict keying above

        # Step 5: Expand context with immediate neighbors
        seed_ids = list(entity_scores.keys())
        for entity_id in seed_ids:
            neighbors = kg.neighbors(entity_id, direction="both")
            for neighbor in neighbors:
                if neighbor.id not in entity_scores:
                    # Neighbors get a reduced score (centrality bonus for being connected)
                    entity_scores[neighbor.id] = (neighbor, 40.0)
                else:
                    # Boost score for entities connected to multiple seed entities
                    existing_entity, existing_score = entity_scores[neighbor.id]
                    entity_scores[neighbor.id] = (existing_entity, existing_score + 5.0)

        # Step 6: Collect relationships between all result entities
        result_entity_ids = set(entity_scores.keys())
        relationships: list[BaseRelationship] = []
        seen_rel_ids: set[str] = set()
        for entity_id in result_entity_ids:
            rels = kg.get_relationships(entity_id, direction="both")
            for rel in rels:
                if rel.id in seen_rel_ids:
                    continue
                if rel.source_id in result_entity_ids and rel.target_id in result_entity_ids:
                    relationships.append(rel)
                    seen_rel_ids.add(rel.id)

        # Step 7: Score entities (fuzzy match score + centrality bonus)
        # Add a centrality bonus based on how many relationships connect to each entity
        rel_counts: dict[str, int] = {}
        for rel in relationships:
            rel_counts[rel.source_id] = rel_counts.get(rel.source_id, 0) + 1
            rel_counts[rel.target_id] = rel_counts.get(rel.target_id, 0) + 1

        scored: list[tuple[BaseEntity, float]] = []
        for entity_id, (entity, base_score) in entity_scores.items():
            centrality_bonus = rel_counts.get(entity_id, 0) * 2.0
            final_score = base_score + centrality_bonus
            scored.append((entity, final_score))

        # Step 8: Sort and trim to top_k
        scored.sort(key=lambda x: x[1], reverse=True)
        top_entities = [entity for entity, _score in scored[:top_k]]
        top_entity_ids = {e.id for e in top_entities}

        # Filter relationships to only include those between top entities
        top_relationships = [
            rel
            for rel in relationships
            if rel.source_id in top_entity_ids and rel.target_id in top_entity_ids
        ]

        # Step 9: Build context string
        context = self._context_builder.build_context(top_entities, top_relationships, kg)

        # Step 10: Return result
        return RetrievalResult(
            entities=top_entities,
            relationships=top_relationships,
            context=context,
            stats={
                "keywords_extracted": list(keywords),
                "type_matches": [t.value for t in type_matches],
                "total_candidates": len(entity_scores),
                "entities_returned": len(top_entities),
                "relationships_returned": len(top_relationships),
            },
        )

    @staticmethod
    def _extract_keywords(question: str) -> tuple[list[str], list[EntityType]]:
        """Extract search keywords and entity type references from a question.

        Args:
            question: The natural language question.

        Returns:
            A tuple of (keywords, entity_types_mentioned).
        """
        # Tokenize and filter stopwords
        tokens = question.lower().split()
        # Remove punctuation from tokens
        cleaned = []
        for token in tokens:
            cleaned_token = token.strip("?.,!;:'\"()[]{}").strip()
            if cleaned_token and cleaned_token not in _STOPWORDS:
                cleaned.append(cleaned_token)

        # Check for entity type names in the question
        type_matches: list[EntityType] = []
        question_lower = question.lower()
        for entity_type in EntityType:
            # Check both the enum value and a human-friendly form
            type_name = entity_type.value.replace("_", " ")
            if type_name in question_lower or entity_type.value in question_lower:
                type_matches.append(entity_type)

        # Also check plural forms (simple heuristic)
        for plural, etype in _PLURAL_MAP.items():
            if plural in question_lower and etype not in type_matches:
                type_matches.append(etype)

        return cleaned, type_matches
