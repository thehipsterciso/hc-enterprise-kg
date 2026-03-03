"""SchemaAlignerAgent — validates field updates against Pydantic entity models.

Extracts the Pydantic validation and sub-model coercion logic from the
AdversarialValidator. Ensures that proposed field updates are type-safe
and sub-models are properly constructed before reaching the graph.

KARMA mapping: Schema Alignment Agent — ensures extracted entities and
relationships conform to the target knowledge graph schema.
"""

from __future__ import annotations

import logging
import typing
from typing import Any

from pydantic import BaseModel

from domain.base import BaseEntity
from enrichment.base import EnrichmentResult, ValidationFailure
from enrichment.karma.base_agent import (
    AbstractKarmaAgent,
    AgentMessage,
    AgentRole,
    MessageType,
    PipelineState,
)

logger = logging.getLogger(__name__)


class SchemaAlignerAgent(AbstractKarmaAgent):
    """Validates and coerces field updates against Pydantic entity models.

    For each proposed field update:
    1. Checks if the field exists on the entity's Pydantic model
    2. If the value is a dict and the field expects a sub-model,
       attempts to construct the sub-model from the dict
    3. If the value is a list of dicts and the field expects a list
       of sub-models, coerces each item

    Fields that fail validation are removed from the updates and
    recorded as ValidationFailure objects.
    """

    @property
    def role(self) -> AgentRole:
        return AgentRole.SCHEMA_ALIGNER

    def process(
        self,
        message: AgentMessage,
        state: PipelineState,
    ) -> list[AgentMessage]:
        """Validate field updates against entity schema.

        Responds to ENRICHMENT_RESULT messages by validating each field
        update and forwarding the validated result to the EvaluatorAgent.

        Args:
            message: ENRICHMENT_RESULT with entity + result.
            state: Current pipeline state.

        Returns:
            List containing one SCHEMA_VALIDATION message.
        """
        if message.message_type != MessageType.ENRICHMENT_RESULT:
            return []

        entity = message.payload.get("entity")
        result: EnrichmentResult | None = message.payload.get("result")

        if entity is None or result is None:
            return []

        # Validate each field update
        validated_fields: dict[str, Any] = {}
        failures: list[ValidationFailure] = []

        for field_name, value in result.field_updates.items():
            coerced, failure = self._validate_field(entity, field_name, value)
            if failure:
                failures.append(failure)
            else:
                validated_fields[field_name] = coerced

        # Build validated result
        validated_result = EnrichmentResult(
            entity_id=result.entity_id,
            entity_type=result.entity_type,
            field_updates=validated_fields,
            provenance_update=result.provenance_update,
            relationship_suggestions=result.relationship_suggestions,
            known_gaps=result.known_gaps,
            actions=result.actions,
        )

        return [
            self.create_message(
                recipient=AgentRole.EVALUATOR,
                message_type=MessageType.SCHEMA_VALIDATION,
                payload={
                    **message.payload,
                    "result": validated_result,
                    "schema_failures": failures,
                    "fields_attempted": len(result.field_updates),
                },
                correlation_id=message.correlation_id,
                metadata=message.metadata,
            )
        ]

    def _validate_field(
        self,
        entity: BaseEntity,
        field_name: str,
        value: Any,
    ) -> tuple[Any, ValidationFailure | None]:
        """Validate a single field update against the entity's Pydantic model."""
        entity_class = type(entity)
        model_fields = (
            entity_class.model_fields
            if hasattr(entity_class, "model_fields")
            else {}
        )

        if field_name not in model_fields:
            # Will go to __pydantic_extra__ (per ADR-002)
            return value, None

        field_info = model_fields[field_name]
        field_annotation = field_info.annotation

        # Sub-model coercion for dict values
        if isinstance(value, dict) and field_annotation is not None:
            coerced = self._coerce_to_submodel(
                field_name, value, field_annotation, entity_class.__name__
            )
            if coerced is not None:
                return coerced, None
            return value, ValidationFailure(
                field_name=field_name,
                failure_type="pydantic_validation",
                message=(
                    f"Dict value for '{field_name}' could not be coerced to "
                    f"expected type {field_annotation}"
                ),
                attempted_value=value,
            )

        # List of sub-models coercion
        if isinstance(value, list) and value and isinstance(value[0], dict):
            coerced_list = self._coerce_list_to_submodels(
                field_name, value, field_annotation, entity_class.__name__
            )
            if coerced_list is not None:
                return coerced_list, None

        return value, None

    @staticmethod
    def _coerce_to_submodel(
        field_name: str,
        value: dict,
        annotation: Any,
        entity_class_name: str,
    ) -> Any | None:
        """Attempt to construct a Pydantic sub-model from a dict."""
        origin = getattr(annotation, "__origin__", None)
        args = getattr(annotation, "__args__", ())

        target_type = annotation

        # Handle Optional[X] → X
        if origin is typing.Union:
            non_none_args = [a for a in args if a is not type(None)]
            if len(non_none_args) == 1:
                target_type = non_none_args[0]

        if isinstance(target_type, type) and issubclass(target_type, BaseModel):
            try:
                return target_type.model_validate(value)
            except Exception as e:
                logger.debug(
                    f"Sub-model coercion failed for "
                    f"{entity_class_name}.{field_name}: {e}"
                )
                return None

        return value  # Not a sub-model — return as-is

    @staticmethod
    def _coerce_list_to_submodels(
        field_name: str,
        value: list[dict],
        annotation: Any,
        entity_class_name: str,
    ) -> list | None:
        """Attempt to coerce a list of dicts to a list of sub-models."""
        origin = getattr(annotation, "__origin__", None)
        args = getattr(annotation, "__args__", ())

        if origin is list and args:
            item_type = args[0]

            # Unwrap Optional
            item_origin = getattr(item_type, "__origin__", None)
            item_args = getattr(item_type, "__args__", ())
            if item_origin is typing.Union:
                non_none = [a for a in item_args if a is not type(None)]
                if len(non_none) == 1:
                    item_type = non_none[0]

            if isinstance(item_type, type) and issubclass(item_type, BaseModel):
                try:
                    return [item_type.model_validate(item) for item in value]
                except Exception as e:
                    logger.debug(
                        f"List sub-model coercion failed for "
                        f"{entity_class_name}.{field_name}: {e}"
                    )
                    return None

        return None
