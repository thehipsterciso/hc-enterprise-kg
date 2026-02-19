"""Embedding-based entity linker using sentence-transformers for similarity."""

from __future__ import annotations

from typing import Any

from hc_enterprise_kg.auto.base import LinkingResult
from hc_enterprise_kg.auto.confidence import ConfidenceSource, compute_confidence
from hc_enterprise_kg.auto.linkers.base import AbstractLinker
from hc_enterprise_kg.domain.base import BaseEntity, BaseRelationship, RelationshipType


class EmbeddingLinker(AbstractLinker):
    """Links entities by computing embedding similarity on their descriptions.

    Uses sentence-transformers to embed entity name + description, then
    finds pairs above a cosine similarity threshold and proposes relationships.
    """

    def __init__(
        self,
        model_name: str = "all-MiniLM-L6-v2",
        similarity_threshold: float = 0.7,
        relationship_type: RelationshipType = RelationshipType.DEPENDS_ON,
    ) -> None:
        self._model_name = model_name
        self._threshold = similarity_threshold
        self._rel_type = relationship_type
        self._model: Any = None

    def _load_model(self) -> Any:
        if self._model is None:
            try:
                from sentence_transformers import SentenceTransformer
                self._model = SentenceTransformer(self._model_name)
            except ImportError:
                raise ImportError(
                    "sentence-transformers is required for embedding linking. "
                    "Install with: pip install sentence-transformers"
                )
        return self._model

    def link(self, entities: list[BaseEntity]) -> LinkingResult:
        if len(entities) < 2:
            return LinkingResult(link_method="embedding")

        try:
            model = self._load_model()
        except ImportError as e:
            return LinkingResult(link_method="embedding", errors=[str(e)])

        # Build text representations
        texts = [f"{e.name}: {e.description}" for e in entities]

        try:
            import numpy as np

            # Encode all entities
            embeddings = model.encode(texts, convert_to_numpy=True, show_progress_bar=False)

            # Normalize for cosine similarity
            norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
            norms = np.where(norms == 0, 1, norms)
            normalized = embeddings / norms

            # Compute pairwise cosine similarity
            similarity_matrix = normalized @ normalized.T

            relationships: list[BaseRelationship] = []

            for i in range(len(entities)):
                for j in range(i + 1, len(entities)):
                    sim = float(similarity_matrix[i, j])
                    if sim >= self._threshold:
                        # Don't link entities of the same type by default
                        if entities[i].entity_type == entities[j].entity_type:
                            continue

                        confidence = compute_confidence(
                            ConfidenceSource.EMBEDDING_LINK,
                            similarity_score=sim,
                        )
                        relationships.append(
                            BaseRelationship(
                                relationship_type=self._rel_type,
                                source_id=entities[i].id,
                                target_id=entities[j].id,
                                confidence=confidence,
                                properties={
                                    "_link_method": "embedding_similarity",
                                    "_similarity_score": round(sim, 4),
                                },
                            )
                        )

            return LinkingResult(relationships=relationships, link_method="embedding")

        except Exception as e:
            return LinkingResult(link_method="embedding", errors=[f"Embedding linking failed: {e}"])
