"""Confidence scoring for auto-extracted entities and relationships."""

from __future__ import annotations

from enum import Enum


class ConfidenceSource(str, Enum):
    """Source of extraction that determines base confidence."""

    RULE_BASED = "rule_based"
    CSV_STRUCTURED = "csv_structured"
    LLM_EXTRACTION = "llm_extraction"
    HEURISTIC_LINK = "heuristic_link"
    EMBEDDING_LINK = "embedding_link"
    USER_PROVIDED = "user_provided"


# Base confidence scores by source type
BASE_CONFIDENCE: dict[ConfidenceSource, float] = {
    ConfidenceSource.USER_PROVIDED: 1.0,
    ConfidenceSource.RULE_BASED: 0.95,
    ConfidenceSource.CSV_STRUCTURED: 0.90,
    ConfidenceSource.LLM_EXTRACTION: 0.70,
    ConfidenceSource.HEURISTIC_LINK: 0.75,
    ConfidenceSource.EMBEDDING_LINK: 0.60,
}


def compute_confidence(
    source: ConfidenceSource,
    similarity_score: float | None = None,
    field_completeness: float = 1.0,
) -> float:
    """Compute a confidence score for an extracted entity or relationship.

    Args:
        source: The extraction method used.
        similarity_score: Optional similarity score (0-1) from embedding/fuzzy matching.
        field_completeness: Fraction of expected fields that are populated (0-1).

    Returns:
        Confidence score between 0.0 and 1.0.
    """
    base = BASE_CONFIDENCE.get(source, 0.5)

    if similarity_score is not None:
        # Blend base confidence with similarity score
        score = 0.5 * base + 0.5 * similarity_score
    else:
        score = base

    # Penalize incomplete entities
    score *= max(0.5, field_completeness)

    return round(min(1.0, max(0.0, score)), 3)
