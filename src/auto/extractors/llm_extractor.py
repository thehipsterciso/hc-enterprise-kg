"""LLM-based entity and relationship extraction."""

from __future__ import annotations

import json
import uuid
from typing import Any

from auto.base import ExtractionResult
from auto.confidence import ConfidenceSource, compute_confidence
from auto.extractors.base import AbstractExtractor
from domain.base import (
    BaseEntity,
    BaseRelationship,
    EntityType,
    RelationshipType,
)
from domain.registry import EntityRegistry

EXTRACTION_PROMPT = """You are an entity and relationship extractor for an enterprise knowledge graph.

Given the following text, extract all entities and relationships you can find.

Entity types: person, department, role, system, network, data_asset, policy, vendor, location, vulnerability, threat_actor, incident

Relationship types: works_in, manages, reports_to, has_role, member_of, hosts, connects_to, depends_on, stores, runs_on, governs, exploits, targets, mitigates, affects, provides_service, located_at, supplied_by, responsible_for

Return a JSON object with this exact structure:
{
  "entities": [
    {"entity_type": "person", "name": "John Doe", "attributes": {"email": "john@example.com", "title": "Engineer"}},
    ...
  ],
  "relationships": [
    {"type": "works_in", "source_name": "John Doe", "target_name": "Engineering"},
    ...
  ]
}

Only include entities and relationships you are confident about. Do not hallucinate.

TEXT:
"""


class LLMExtractor(AbstractExtractor):
    """Extracts entities and relationships from unstructured text using an LLM.

    Uses litellm for provider-agnostic API calls (supports OpenAI, Anthropic, local models).
    """

    def __init__(self, model: str = "gpt-4o-mini", temperature: float = 0.0) -> None:
        self._model = model
        self._temperature = temperature

    def can_handle(self, data: Any) -> bool:
        return isinstance(data, str) and len(data) > 50

    def extract(self, data: Any, **kwargs: Any) -> ExtractionResult:
        if not isinstance(data, str):
            return ExtractionResult(source="llm", errors=["Data must be a string"])

        try:
            from litellm import completion
        except ImportError:
            return ExtractionResult(
                source="llm",
                errors=["litellm is required for LLM extraction. Install with: pip install litellm"],
            )

        EntityRegistry.auto_discover()

        try:
            response = completion(
                model=self._model,
                messages=[
                    {"role": "system", "content": "You extract structured entities from text. Always respond with valid JSON."},
                    {"role": "user", "content": EXTRACTION_PROMPT + data},
                ],
                temperature=self._temperature,
                response_format={"type": "json_object"},
            )

            content = response.choices[0].message.content
            if not content:
                return ExtractionResult(source="llm", errors=["Empty LLM response"])

            parsed = json.loads(content)
            return self._parse_llm_response(parsed)

        except Exception as e:
            return ExtractionResult(source="llm", errors=[f"LLM extraction failed: {e}"])

    def _parse_llm_response(self, parsed: dict[str, Any]) -> ExtractionResult:
        """Parse LLM JSON response into domain entities and relationships."""
        entities: list[BaseEntity] = []
        relationships: list[BaseRelationship] = []
        errors: list[str] = []
        confidence = compute_confidence(ConfidenceSource.LLM_EXTRACTION)
        name_to_id: dict[str, str] = {}

        for raw_entity in parsed.get("entities", []):
            try:
                entity_type_str = raw_entity.get("entity_type", "")
                entity_type = EntityType(entity_type_str)
                name = raw_entity.get("name", "Unknown")
                attrs = raw_entity.get("attributes", {})

                entity_id = str(uuid.uuid4())
                name_to_id[name] = entity_id

                entity_data = {
                    "id": entity_id,
                    "entity_type": entity_type.value,
                    "name": name,
                    "metadata": {"_confidence": confidence, "_source": "llm"},
                    **attrs,
                }

                entity_class = EntityRegistry.get(entity_type)
                entity = entity_class.model_validate(entity_data)
                entities.append(entity)
            except Exception as e:
                errors.append(f"Entity parse error: {e}")

        for raw_rel in parsed.get("relationships", []):
            try:
                rel_type = RelationshipType(raw_rel.get("type", ""))
                source_name = raw_rel.get("source_name", "")
                target_name = raw_rel.get("target_name", "")

                source_id = name_to_id.get(source_name)
                target_id = name_to_id.get(target_name)

                if source_id and target_id:
                    relationships.append(
                        BaseRelationship(
                            relationship_type=rel_type,
                            source_id=source_id,
                            target_id=target_id,
                            confidence=confidence,
                        )
                    )
            except Exception as e:
                errors.append(f"Relationship parse error: {e}")

        return ExtractionResult(
            entities=entities,
            relationships=relationships,
            source="llm",
            errors=errors,
        )
