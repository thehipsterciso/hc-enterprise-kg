"""AutoKGPipeline: orchestrates extract → link → resolve → score pipeline."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from auto.base import PipelineResult
from auto.extractors.csv_extractor import CSVExtractor
from auto.extractors.llm_extractor import LLMExtractor
from auto.extractors.rule_based import RuleBasedExtractor
from auto.linkers.embedding_linker import EmbeddingLinker
from auto.linkers.heuristic_linker import HeuristicLinker
from auto.resolvers.dedup_resolver import DedupResolver
from domain.base import BaseEntity, BaseRelationship

if TYPE_CHECKING:
    from auto.extractors.base import AbstractExtractor
    from auto.linkers.base import AbstractLinker
    from auto.resolvers.base import AbstractResolver
    from graph.knowledge_graph import KnowledgeGraph


class AutoKGPipeline:
    """Orchestrates the automatic KG construction pipeline.

    Configurable pipeline that chains:
    1. Extraction: Convert raw data into entities and relationships
    2. Linking: Discover additional relationships between extracted entities
    3. Resolution: Merge/deduplicate overlapping entities
    4. Load: Insert the final entities and relationships into the KG

    Usage:
        kg = KnowledgeGraph()
        pipeline = AutoKGPipeline(kg)
        result = pipeline.run("path/to/data.csv")

        # Or with custom configuration:
        pipeline = AutoKGPipeline(
            kg,
            extractors=[RuleBasedExtractor(), CSVExtractor()],
            linkers=[HeuristicLinker()],
            resolver=DedupResolver(),
            use_llm=False,
            use_embeddings=False,
        )
    """

    def __init__(
        self,
        knowledge_graph: KnowledgeGraph,
        extractors: list[AbstractExtractor] | None = None,
        linkers: list[AbstractLinker] | None = None,
        resolver: AbstractResolver | None = None,
        use_llm: bool = True,
        use_embeddings: bool = True,
        llm_model: str = "gpt-4o-mini",
    ) -> None:
        self._kg = knowledge_graph

        # Configure extractors
        if extractors is not None:
            self._extractors = extractors
        else:
            self._extractors: list[AbstractExtractor] = [
                RuleBasedExtractor(),
                CSVExtractor(),
            ]
            if use_llm:
                self._extractors.append(LLMExtractor(model=llm_model))

        # Configure linkers
        if linkers is not None:
            self._linkers = linkers
        else:
            self._linkers: list[AbstractLinker] = [HeuristicLinker()]
            if use_embeddings:
                self._linkers.append(EmbeddingLinker())

        # Configure resolver
        self._resolver = resolver or DedupResolver()

    def run(self, data: Any, **kwargs: Any) -> PipelineResult:
        """Run the full auto-KG pipeline on the given data.

        Args:
            data: Input data (file path, string text, or CSV content).
            **kwargs: Extra arguments passed to extractors.

        Returns:
            PipelineResult with all extracted entities, relationships, and stats.
        """
        result = PipelineResult()
        all_entities: list[BaseEntity] = []
        all_relationships: list[BaseRelationship] = []

        # Stage 1: Extraction
        for extractor in self._extractors:
            if extractor.can_handle(data):
                extraction = extractor.extract(data, **kwargs)
                result.extraction_results.append(extraction)
                all_entities.extend(extraction.entities)
                all_relationships.extend(extraction.relationships)

        if not all_entities:
            result.stats["status"] = "no_entities_extracted"
            return result

        # Stage 2: Linking
        for linker in self._linkers:
            try:
                linking = linker.link(all_entities)
                result.linking_results.append(linking)
                all_relationships.extend(linking.relationships)
            except Exception as e:
                result.linking_results.append(
                    type(linking)(link_method="error", errors=[str(e)])  # type: ignore[name-defined]
                )

        # Stage 3: Resolution
        resolution = self._resolver.resolve(all_entities)
        result.resolution_result = resolution

        # Use resolved entities (deduplicated)
        final_entities = resolution.entities if resolution.entities else all_entities

        # Update relationships to point to merged entity IDs
        id_remap = {removed: kept for kept, removed in resolution.merged_entity_ids}
        final_relationships: list[BaseRelationship] = []
        for rel in all_relationships:
            src = id_remap.get(rel.source_id, rel.source_id)
            tgt = id_remap.get(rel.target_id, rel.target_id)
            if src != rel.source_id or tgt != rel.target_id:
                rel = BaseRelationship(
                    relationship_type=rel.relationship_type,
                    source_id=src,
                    target_id=tgt,
                    confidence=rel.confidence,
                    properties=rel.properties,
                )
            final_relationships.append(rel)

        # Stage 4: Load into KG
        entity_ids_in_kg = set()
        for entity in final_entities:
            try:
                self._kg.add_entity(entity)
                entity_ids_in_kg.add(entity.id)
            except Exception:
                pass  # Skip entities that fail validation

        loaded_rels = 0
        for rel in final_relationships:
            if rel.source_id in entity_ids_in_kg and rel.target_id in entity_ids_in_kg:
                try:
                    self._kg.add_relationship(rel)
                    loaded_rels += 1
                except Exception:
                    pass

        result.entities = final_entities
        result.relationships = final_relationships
        result.stats = {
            "entities_extracted": len(all_entities),
            "entities_after_dedup": len(final_entities),
            "duplicates_merged": len(resolution.merged_entity_ids),
            "relationships_discovered": len(all_relationships),
            "relationships_after_remap": len(final_relationships),
            "entities_loaded": len(entity_ids_in_kg),
            "relationships_loaded": loaded_rels,
            "status": "complete",
        }

        return result
