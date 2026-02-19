"""Context builder that formats knowledge graph data as structured text for LLMs."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from domain.base import BaseEntity, BaseRelationship
    from graph.knowledge_graph import KnowledgeGraph

# Fields to skip when rendering entity attributes
_INTERNAL_FIELDS = frozenset({
    "id",
    "created_at",
    "updated_at",
    "valid_from",
    "valid_until",
    "version",
    "metadata",
})


class ContextBuilder:
    """Formats knowledge graph entities and relationships as structured context for LLMs."""

    @staticmethod
    def build_context(
        entities: list[BaseEntity],
        relationships: list[BaseRelationship],
        kg: KnowledgeGraph,
        max_tokens: int = 4000,
    ) -> str:
        """Build a formatted context string with entity summaries and relationships.

        Approximates token count as chars / 4 and truncates entities if needed
        to stay within the token budget.

        Args:
            entities: The entities to include in the context.
            relationships: The relationships to include in the context.
            kg: The knowledge graph (used to resolve entity names for relationships).
            max_tokens: Approximate maximum token budget.

        Returns:
            A formatted context string ready for LLM consumption.
        """
        if not entities and not relationships:
            return "No relevant context found in the knowledge graph."

        max_chars = max_tokens * 4
        sections: list[str] = []

        # --- Summary header ---
        entity_types_present = sorted({e.entity_type.value for e in entities})
        header = (
            f"=== Knowledge Graph Context ===\n"
            f"Entities: {len(entities)} | "
            f"Types: {', '.join(entity_types_present) if entity_types_present else 'none'} | "
            f"Relationships: {len(relationships)}"
        )
        sections.append(header)

        # --- Entity details ---
        entity_section_parts: list[str] = []
        entity_section_parts.append("\n--- Entities ---")

        for entity in entities:
            entity_block = ContextBuilder._format_entity(entity)
            entity_section_parts.append(entity_block)

            # Check if we're approaching the budget (leave room for relationships)
            current_chars = sum(len(s) for s in sections) + sum(
                len(p) for p in entity_section_parts
            )
            # Reserve roughly 1/3 of budget for relationships
            if current_chars > max_chars * 2 // 3:
                remaining = len(entities) - len(entity_section_parts) + 1
                entity_section_parts.append(
                    f"  ... ({remaining} more entities truncated)"
                )
                break

        sections.append("\n".join(entity_section_parts))

        # --- Relationships ---
        if relationships:
            rel_parts: list[str] = ["\n--- Relationships ---"]
            entity_map = {e.id: e.name for e in entities}

            for rel in relationships:
                source_name = entity_map.get(rel.source_id) or _resolve_name(kg, rel.source_id)
                target_name = entity_map.get(rel.target_id) or _resolve_name(kg, rel.target_id)
                rel_label = rel.relationship_type.value.replace("_", " ")
                rel_parts.append(f"  {source_name} {rel_label} {target_name}")

                # Check budget
                current_chars = sum(len(s) for s in sections) + sum(len(p) for p in rel_parts)
                if current_chars > max_chars:
                    rel_parts.append("  ... (more relationships truncated)")
                    break

            sections.append("\n".join(rel_parts))

        result = "\n\n".join(sections)

        # Final trim if still over budget
        if len(result) > max_chars:
            result = result[: max_chars - 3] + "..."

        return result

    @staticmethod
    def _format_entity(entity: BaseEntity) -> str:
        """Format a single entity as a text block."""
        data = entity.model_dump()
        lines = [f"  [{entity.entity_type.value.upper()}] {entity.name}"]

        for key, value in data.items():
            if key in _INTERNAL_FIELDS:
                continue
            if key in ("entity_type", "name"):
                continue
            if value is None or value == "" or value == [] or value == {}:
                continue
            if isinstance(value, list):
                value = ", ".join(str(v) for v in value)
            lines.append(f"    {key}: {value}")

        return "\n".join(lines)


def _resolve_name(kg: KnowledgeGraph, entity_id: str) -> str:
    """Look up an entity name from the KG, falling back to the ID."""
    entity = kg.get_entity(entity_id)
    if entity:
        return entity.name
    return entity_id
