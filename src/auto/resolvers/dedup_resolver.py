"""Deduplication resolver: merges overlapping entities."""

from __future__ import annotations

from rapidfuzz import fuzz

from auto.base import ResolutionResult
from auto.resolvers.base import AbstractResolver
from domain.base import BaseEntity


class DedupResolver(AbstractResolver):
    """Identifies and merges duplicate entities based on name similarity.

    When duplicates are found, the entity with higher confidence (from metadata)
    is kept and the other is merged into it. If confidence is equal, the
    entity with more populated fields wins.
    """

    def __init__(self, name_threshold: float = 90.0) -> None:
        self._threshold = name_threshold

    def resolve(self, entities: list[BaseEntity]) -> ResolutionResult:
        if len(entities) < 2:
            return ResolutionResult(entities=list(entities))

        # Group entities by type for comparison
        by_type: dict[str, list[BaseEntity]] = {}
        for entity in entities:
            by_type.setdefault(entity.entity_type.value, []).append(entity)

        merged_ids: list[tuple[str, str]] = []
        final_entities: list[BaseEntity] = []
        removed_ids: set[str] = set()

        for entity_type, group in by_type.items():
            # Compare all pairs within the same type
            keep: dict[str, BaseEntity] = {}
            for entity in group:
                if entity.id in removed_ids:
                    continue

                # Check against already-kept entities
                found_match = False
                for kept_id, kept_entity in list(keep.items()):
                    score = fuzz.token_sort_ratio(entity.name, kept_entity.name)
                    if score >= self._threshold:
                        # Merge: keep the higher-confidence one
                        winner, loser = self._pick_winner(kept_entity, entity)
                        merged = self._merge_entities(winner, loser)
                        keep[winner.id] = merged
                        merged_ids.append((winner.id, loser.id))
                        removed_ids.add(loser.id)
                        found_match = True
                        break

                if not found_match:
                    keep[entity.id] = entity

            final_entities.extend(keep.values())

        return ResolutionResult(
            merged_entity_ids=merged_ids,
            entities=final_entities,
        )

    def _pick_winner(
        self, a: BaseEntity, b: BaseEntity
    ) -> tuple[BaseEntity, BaseEntity]:
        """Pick the entity with higher confidence or more fields populated."""
        conf_a = a.metadata.get("_confidence", 0.5)
        conf_b = b.metadata.get("_confidence", 0.5)
        if conf_a >= conf_b:
            return a, b
        return b, a

    def _merge_entities(self, winner: BaseEntity, loser: BaseEntity) -> BaseEntity:
        """Merge loser's fields into winner where winner has empty/default values."""
        winner_data = winner.model_dump()
        loser_data = loser.model_dump()

        for key, loser_val in loser_data.items():
            if key in ("id", "entity_type", "created_at", "updated_at", "version"):
                continue
            winner_val = winner_data.get(key)
            # Fill empty fields from loser
            if self._is_empty(winner_val) and not self._is_empty(loser_val):
                winner_data[key] = loser_val

        # Merge tags
        winner_tags = set(winner_data.get("tags", []))
        loser_tags = set(loser_data.get("tags", []))
        winner_data["tags"] = list(winner_tags | loser_tags)

        # Merge metadata
        winner_meta = winner_data.get("metadata", {})
        loser_meta = loser_data.get("metadata", {})
        for k, v in loser_meta.items():
            if k not in winner_meta:
                winner_meta[k] = v
        winner_data["metadata"] = winner_meta
        winner_data["metadata"]["_merged_from"] = loser.id

        from domain.registry import EntityRegistry

        EntityRegistry.auto_discover()
        entity_class = EntityRegistry.get(winner.entity_type)
        return entity_class.model_validate(winner_data)

    def _is_empty(self, value: object) -> bool:
        if value is None:
            return True
        if isinstance(value, str) and value == "":
            return True
        if isinstance(value, list) and len(value) == 0:
            return True
        if isinstance(value, dict) and len(value) == 0:
            return True
        return False
