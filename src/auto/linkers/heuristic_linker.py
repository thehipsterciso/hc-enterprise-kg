"""Heuristic-based entity linker using fuzzy name matching and FK detection."""

from __future__ import annotations

from rapidfuzz import fuzz

from auto.base import LinkingResult
from auto.confidence import ConfidenceSource, compute_confidence
from auto.linkers.base import AbstractLinker
from domain.base import BaseEntity, BaseRelationship, EntityType, RelationshipType

# Heuristic rules for which entity types can be linked
LINKABLE_PAIRS: list[tuple[EntityType, EntityType, RelationshipType]] = [
    (EntityType.PERSON, EntityType.DEPARTMENT, RelationshipType.WORKS_IN),
    (EntityType.SYSTEM, EntityType.NETWORK, RelationshipType.CONNECTS_TO),
    (EntityType.SYSTEM, EntityType.VENDOR, RelationshipType.SUPPLIED_BY),
    (EntityType.DATA_ASSET, EntityType.SYSTEM, RelationshipType.STORES),
    (EntityType.POLICY, EntityType.SYSTEM, RelationshipType.GOVERNS),
    (EntityType.VULNERABILITY, EntityType.SYSTEM, RelationshipType.AFFECTS),
    (EntityType.DEPARTMENT, EntityType.LOCATION, RelationshipType.LOCATED_AT),
]

# Attribute pairs that indicate FK-like relationships
FK_ATTRIBUTES: list[tuple[str, EntityType]] = [
    ("department_id", EntityType.DEPARTMENT),
    ("system_id", EntityType.SYSTEM),
    ("network_id", EntityType.NETWORK),
    ("vendor_id", EntityType.VENDOR),
    ("location_id", EntityType.LOCATION),
    ("owner_id", EntityType.PERSON),
    ("head_id", EntityType.PERSON),
    ("threat_actor_id", EntityType.THREAT_ACTOR),
]


class HeuristicLinker(AbstractLinker):
    """Links entities using fuzzy name matching and FK attribute detection.

    Two strategies:
    1. FK detection: If entity A has a `department_id` attribute matching
       entity B's id, create a relationship.
    2. Name matching: If entity names match above a threshold using fuzzy
       string matching, propose a relationship.
    """

    def __init__(self, name_match_threshold: float = 85.0) -> None:
        self._threshold = name_match_threshold

    def link(self, entities: list[BaseEntity]) -> LinkingResult:
        relationships: list[BaseRelationship] = []
        errors: list[str] = []

        # Index entities by type and by id
        by_type: dict[EntityType, list[BaseEntity]] = {}
        by_id: dict[str, BaseEntity] = {}
        for entity in entities:
            by_type.setdefault(entity.entity_type, []).append(entity)
            by_id[entity.id] = entity

        # Strategy 1: FK attribute detection
        for entity in entities:
            for attr_name, target_type in FK_ATTRIBUTES:
                fk_value = getattr(entity, attr_name, None)
                if fk_value and fk_value in by_id:
                    target = by_id[fk_value]
                    rel_type = self._infer_relationship_type(entity.entity_type, target.entity_type)
                    if rel_type:
                        confidence = compute_confidence(ConfidenceSource.HEURISTIC_LINK)
                        relationships.append(
                            BaseRelationship(
                                relationship_type=rel_type,
                                source_id=entity.id,
                                target_id=target.id,
                                confidence=confidence,
                                properties={"_link_method": "fk_detection"},
                            )
                        )

        # Strategy 2: Name-based matching for linkable pairs
        for src_type, tgt_type, rel_type in LINKABLE_PAIRS:
            sources = by_type.get(src_type, [])
            targets = by_type.get(tgt_type, [])

            if not sources or not targets:
                continue

            for src in sources:
                for tgt in targets:
                    score = fuzz.token_sort_ratio(src.name, tgt.name)
                    if score >= self._threshold:
                        confidence = compute_confidence(
                            ConfidenceSource.HEURISTIC_LINK,
                            similarity_score=score / 100.0,
                        )
                        relationships.append(
                            BaseRelationship(
                                relationship_type=rel_type,
                                source_id=src.id,
                                target_id=tgt.id,
                                confidence=confidence,
                                properties={
                                    "_link_method": "name_matching",
                                    "_match_score": score,
                                },
                            )
                        )

        return LinkingResult(
            relationships=relationships,
            link_method="heuristic",
            errors=errors,
        )

    def _infer_relationship_type(
        self, source_type: EntityType, target_type: EntityType
    ) -> RelationshipType | None:
        for src_t, tgt_t, rel_t in LINKABLE_PAIRS:
            if source_type == src_t and target_type == tgt_t:
                return rel_t
        # Fallback generic mappings
        fk_rel_map: dict[tuple[EntityType, EntityType], RelationshipType] = {
            (EntityType.PERSON, EntityType.DEPARTMENT): RelationshipType.WORKS_IN,
            (EntityType.PERSON, EntityType.PERSON): RelationshipType.REPORTS_TO,
            (EntityType.DEPARTMENT, EntityType.PERSON): RelationshipType.MANAGES,
            (EntityType.DEPARTMENT, EntityType.LOCATION): RelationshipType.LOCATED_AT,
        }
        return fk_rel_map.get((source_type, target_type))
