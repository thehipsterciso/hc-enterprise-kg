"""Base classes and data structures for the Knowledge Graph Enrichment Agency.

This module provides the foundational infrastructure for enriching entities
in the knowledge graph with additional attributes, relationships, and provenance
tracking. All 30 entity enrichers inherit from AbstractEnricher and are
registered in EnricherRegistry (following the same pattern as GeneratorRegistry).

Architectural invariant: every enrichment result passes through the
AdversarialValidator BEFORE being applied to the graph. The validator
rejects updates that fail Pydantic model validation, violate confidence
rubric criteria, contain stale source data, or break cross-entity coherence.
No enrichment bypasses this gate.
"""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import StrEnum
from typing import Any, ClassVar

# UTC timezone (Python 3.11+) or fallback for compatibility
try:
    from datetime import UTC
except ImportError:
    UTC = timezone.utc

from domain.base import BaseEntity, BaseRelationship, EntityType, RelationshipType
from domain.shared import DataGap, ProvenanceAndConfidence

logger = logging.getLogger(__name__)


class EnrichmentTier(StrEnum):
    """Enrichment tiers corresponding to OSINT depth and resource investment.

    - BASIC: Local graph analysis, no external APIs.
    - STANDARD: Local graph + cached OSINT data.
    - DEEP: Full OSINT, relationship inference, scenario analysis.
    """

    BASIC = "basic"
    STANDARD = "standard"
    DEEP = "deep"


class ConfidenceLevel(StrEnum):
    """Confidence scale for enriched values.

    Each level has testable criteria defined in CONFIDENCE_RUBRIC.
    Enrichers MUST use the rubric to determine confidence — not guesswork.
    """

    VERIFIED = "verified"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    UNVERIFIED = "unverified"


# Testable rubric: maps each confidence level to its required source evidence.
# The adversarial validator enforces these criteria before any enrichment is applied.
CONFIDENCE_RUBRIC: dict[ConfidenceLevel, dict[str, Any]] = {
    ConfidenceLevel.VERIFIED: {
        "description": "Government source, certified audit report, or published standard body",
        "required_source_types": ["government", "certified_audit", "standard_body"],
        "min_sources": 1,
        "max_staleness_days": 365,
        "examples": [
            "NIST SP 800-53 Rev 5",
            "ISO 27001:2022 certified audit",
            "SEC EDGAR filing",
            "MITRE ATT&CK v14 (published framework)",
        ],
    },
    ConfidenceLevel.HIGH: {
        "description": "Authoritative industry source with audit trail within validity window",
        "required_source_types": ["sec_filing", "soc2_report", "regulatory_text", "vendor_attestation"],
        "min_sources": 1,
        "max_staleness_days": 548,  # 18 months for SOC 2; 12 months for SEC filings
        "examples": [
            "SEC 10-K annual filing (within 12 months)",
            "SOC 2 Type II report (within 18 months)",
            "GDPR Article text (EU Regulation 2016/679)",
        ],
    },
    ConfidenceLevel.MEDIUM: {
        "description": "OSINT corroborated by 2+ independent sources within 6 months",
        "required_source_types": ["osint", "industry_benchmark", "web_search", "press_release"],
        "min_sources": 2,
        "max_staleness_days": 180,
        "examples": [
            "Gartner Magic Quadrant 2025 + vendor press release",
            "Industry salary survey + BLS data",
            "Two independent news sources confirming the same fact",
        ],
    },
    ConfidenceLevel.LOW: {
        "description": "Single unverified source, graph inference, or template-derived value",
        "required_source_types": ["single_source", "graph_inference", "template", "synthetic"],
        "min_sources": 0,
        "max_staleness_days": 90,
        "examples": [
            "Inferred from graph neighborhood",
            "Template-derived default value",
            "Single web search result without corroboration",
        ],
    },
    ConfidenceLevel.UNVERIFIED: {
        "description": "No source attribution or placeholder value",
        "required_source_types": ["none", "placeholder"],
        "min_sources": 0,
        "max_staleness_days": 30,
        "examples": [
            "Default/placeholder value pending enrichment",
            "Field populated without source tracking",
        ],
    },
}


class AssessmentMethodology(StrEnum):
    """How the enrichment was performed. Each methodology has a precise definition.

    - AUTOMATED: Programmatic lookup against a published standard or reference database.
      No human judgment involved. Source is deterministic (same input → same output).
      Examples: NIST control ID lookup, MITRE technique matching, CVE database query.

    - HYBRID: Combines automated lookup with heuristic or rule-based inference.
      Source data is real, but the mapping/interpretation involves algorithmic judgment.
      Examples: Salary range from benchmark + role level adjustment, risk score from
      FAIR model with graph-derived inputs, control effectiveness from framework + gap analysis.

    - MANUAL: Requires human subject matter expert review to validate.
      Cannot be fully automated. Enrichment may suggest a value, but it is explicitly
      flagged as requiring human confirmation before confidence can exceed MEDIUM.
      Examples: Vendor due diligence findings, incident root cause analysis,
      strategic initiative alignment assessment.

    - IMPORT: Bulk import from an authoritative external system.
      Data is ingested as-is from a trusted source (HRIS, CMDB, GRC platform).
      Confidence is inherited from the source system's own quality rating.
      Examples: Employee records from Workday, asset inventory from ServiceNow,
      vulnerability scan results from Qualys.
    """

    AUTOMATED = "automated"
    HYBRID = "hybrid"
    MANUAL = "manual"
    IMPORT = "import"


class FieldCategory(StrEnum):
    """Categorization of entity fields for weighted completeness scoring.

    - CRITICAL: Load-bearing fields for risk, compliance, and operational decisions.
      Missing critical fields degrade entity confidence to LOW regardless of other scores.
      Weight: 3x in completeness calculation.

    - OPERATIONAL: Day-to-day operational fields that inform business decisions.
      Missing operational fields reduce completeness but don't force confidence ceiling.
      Weight: 2x in completeness calculation.

    - METADATA: Process tracking, audit trail, and provenance fields.
      Missing metadata fields are tracked but don't materially affect confidence.
      Weight: 1x in completeness calculation.
    """

    CRITICAL = "critical"
    OPERATIONAL = "operational"
    METADATA = "metadata"


# Source validity windows: how long a source remains authoritative before
# it is considered stale and requires re-verification.
SOURCE_VALIDITY_WINDOWS: dict[str, int] = {
    # Government / standard body sources
    "nist": 730,            # 2 years — NIST revisions are infrequent
    "iso": 1095,            # 3 years — ISO standards have long cycles
    "mitre": 365,           # 1 year — ATT&CK updates annually
    "cis": 365,             # 1 year — CIS Controls update annually
    # Regulatory / compliance sources
    "sec_filing": 365,      # 1 year — annual filings
    "soc2_report": 548,     # 18 months — SOC 2 Type II validity
    "regulatory_text": 1095,  # 3 years — regulation text is stable
    "certified_audit": 365,  # 1 year — audit reports annual
    # Industry / OSINT sources
    "industry_benchmark": 365,  # 1 year — annual surveys
    "press_release": 180,   # 6 months — news decays fast
    "web_search": 90,       # 3 months — web content is volatile
    "vendor_attestation": 365,  # 1 year — vendor self-reports
    # Graph-derived sources
    "graph_inference": 30,  # 30 days — graph changes invalidate inferences
    "template": 0,          # Immediately stale — templates are defaults only
    "synthetic": 0,         # Immediately stale — synthetic is placeholder
}


@dataclass
class ValidationFailure:
    """A single failure from the adversarial validation gate.

    Records what failed, why, and what the enricher attempted.
    """

    field_name: str
    failure_type: str  # "pydantic_validation", "confidence_inflation", "stale_source", "coherence_violation"
    message: str
    attempted_value: Any = None
    enricher_source: str = ""


@dataclass
class EnrichmentAction:
    """Audit trail record for a single enrichment action on an entity.

    Records what was enriched, how, when, and with what confidence
    for provenance and audit purposes.
    """

    entity_id: str
    entity_type: EntityType
    fields_enriched: list[str]
    source: str
    methodology: AssessmentMethodology | str
    confidence: ConfidenceLevel
    source_date: str | None = None  # ISO date when the source data was published/retrieved
    validity_window_days: int | None = None  # How long this source remains authoritative
    timestamp: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass
class EnrichmentStats:
    """Aggregate statistics for an enrichment run across all entities."""

    total_entities_enriched: int = 0
    total_fields_enriched: int = 0
    total_relationships_suggested: int = 0
    total_gaps_identified: int = 0
    total_validation_failures: int = 0  # Fields rejected by adversarial validator
    total_fields_attempted: int = 0  # Fields the enricher tried to set
    validation_failures: list[ValidationFailure] = field(default_factory=list)
    actions: list[EnrichmentAction] = field(default_factory=list)
    start_time: datetime = field(default_factory=lambda: datetime.now(UTC))
    end_time: datetime | None = None

    def duration_seconds(self) -> float:
        """Return enrichment run duration in seconds."""
        end = self.end_time or datetime.now(UTC)
        return (end - self.start_time).total_seconds()

    def rejection_rate(self) -> float:
        """Percentage of attempted field updates that were rejected."""
        if self.total_fields_attempted == 0:
            return 0.0
        return self.total_validation_failures / self.total_fields_attempted


@dataclass
class EnrichmentResult:
    """Result of enriching a single entity.

    Contains field updates, relationship suggestions, provenance updates,
    and identified data gaps for the entity.
    """

    entity_id: str
    entity_type: EntityType
    field_updates: dict[str, Any] = field(default_factory=dict)
    provenance_update: ProvenanceAndConfidence | None = None
    relationship_suggestions: list[tuple[RelationshipType, str, float, str]] = field(
        default_factory=list
    )
    known_gaps: list[DataGap] = field(default_factory=list)
    actions: list[EnrichmentAction] = field(default_factory=list)

    def has_updates(self) -> bool:
        """Return True if this result contains any updates."""
        return bool(
            self.field_updates
            or self.relationship_suggestions
            or self.known_gaps
            or self.provenance_update
        )


@dataclass
class EntityContext:
    """Full graph neighborhood for an entity being enriched.

    Contains the entity itself, its direct neighbors grouped by relationship
    type, and relationship metadata for each edge. This context is passed
    to enrichers to enable graph-aware enrichment.
    """

    entity: BaseEntity
    neighbors_by_type: dict[RelationshipType, list[BaseEntity]] = field(
        default_factory=dict
    )
    relationships: list[BaseRelationship] = field(default_factory=list)

    def get_neighbors(self, rel_type: RelationshipType) -> list[BaseEntity]:
        """Get neighbors connected via a specific relationship type."""
        return self.neighbors_by_type.get(rel_type, [])

    def get_all_neighbors(self) -> list[BaseEntity]:
        """Get all neighboring entities regardless of relationship type."""
        seen = set()
        neighbors = []
        for neighbor_list in self.neighbors_by_type.values():
            for neighbor in neighbor_list:
                if neighbor.id not in seen:
                    seen.add(neighbor.id)
                    neighbors.append(neighbor)
        return neighbors

    def get_relationships_to(self, neighbor_id: str) -> list[BaseRelationship]:
        """Get all relationships connecting to a specific neighbor."""
        return [r for r in self.relationships if r.target_id == neighbor_id]


@dataclass
class CrossEntityProfile:
    """Holistic profile built from graph traversal across related entities.

    Aggregates patterns, statistics, and inferred properties across an entity
    and its neighborhood to inform enrichment decisions.
    """

    entity_id: str
    entity_type: EntityType
    neighbors_by_type: dict[EntityType, int] = field(default_factory=dict)
    relationship_patterns: dict[str, int] = field(default_factory=dict)
    inferred_properties: dict[str, Any] = field(default_factory=dict)
    aggregated_tags: list[str] = field(default_factory=list)
    risk_signals: list[str] = field(default_factory=list)

    def neighbor_count(self) -> int:
        """Total number of neighbors across all types."""
        return sum(self.neighbors_by_type.values())

    def unique_relationship_types(self) -> int:
        """Number of distinct relationship types."""
        return len(self.relationship_patterns)


@dataclass
class OSINTResults:
    """Container for OSINT research results on an entity.

    Aggregates external research findings from various sources: public records,
    news, web search results, regulatory databases, threat intelligence feeds, etc.
    """

    entity_id: str
    entity_type: EntityType
    web_results: list[dict[str, Any]] = field(default_factory=list)
    news_items: list[dict[str, Any]] = field(default_factory=list)
    regulatory_findings: list[dict[str, Any]] = field(default_factory=list)
    threat_intel: list[dict[str, Any]] = field(default_factory=list)
    social_media_profiles: list[dict[str, Any]] = field(default_factory=list)
    raw_data: dict[str, Any] = field(default_factory=dict)
    research_timestamp: datetime = field(default_factory=lambda: datetime.now(UTC))
    research_sources: list[str] = field(default_factory=list)

    def has_findings(self) -> bool:
        """Return True if any research findings were collected."""
        return bool(
            self.web_results
            or self.news_items
            or self.regulatory_findings
            or self.threat_intel
            or self.social_media_profiles
            or self.raw_data
        )


@dataclass
class EnrichmentContext:
    """Shared context for all enrichers during an enrichment run.

    Analogous to GenerationContext in synthetic/base.py. Holds configuration,
    entity collections, and statistics for a coordinated enrichment campaign.
    """

    profile: EnrichmentProfile
    tier: EnrichmentTier
    seed: int | None = None
    graph_entities: dict[EntityType, list[BaseEntity]] = field(default_factory=dict)
    graph_relationships: list[BaseRelationship] = field(default_factory=list)
    entity_contexts: dict[str, EntityContext] = field(default_factory=dict)
    cross_profiles: dict[str, CrossEntityProfile] = field(default_factory=dict)
    osint_results: dict[str, OSINTResults] = field(default_factory=dict)
    stats: EnrichmentStats = field(default_factory=EnrichmentStats)

    def get_entities(self, entity_type: EntityType) -> list[BaseEntity]:
        """Retrieve all entities of a given type."""
        return self.graph_entities.get(entity_type, [])

    def get_entity_context(self, entity_id: str) -> EntityContext | None:
        """Retrieve EntityContext for an entity by ID."""
        return self.entity_contexts.get(entity_id)

    def get_osint_results(self, entity_id: str) -> OSINTResults | None:
        """Retrieve OSINT results for an entity by ID."""
        return self.osint_results.get(entity_id)

    def get_cross_profile(self, entity_id: str) -> CrossEntityProfile | None:
        """Retrieve CrossEntityProfile for an entity by ID."""
        return self.cross_profiles.get(entity_id)


class AbstractEnricher(ABC):
    """Base class for all entity enrichers.

    Each enricher is responsible for enriching entities of a specific type
    by analyzing the entity's graph context, optionally consulting OSINT results,
    and generating field updates, relationship suggestions, and gap identification.

    Subclasses must set ENRICHES to the EntityType they handle and implement
    the enrich() method.
    """

    ENRICHES: ClassVar[EntityType]

    @abstractmethod
    def enrich(
        self,
        entity: BaseEntity,
        context: EntityContext,
        osint: OSINTResults | None = None,
        tier: EnrichmentTier = EnrichmentTier.BASIC,
        profile: EnrichmentProfile = EnrichmentProfile.STANDARD,
        enrichment_context: EnrichmentContext | None = None,
    ) -> EnrichmentResult:
        """Enrich a single entity based on its context and OSINT data.

        Args:
            entity: The entity to enrich.
            context: EntityContext containing the entity's graph neighborhood.
            osint: Optional OSINTResults from external research.
            tier: Enrichment tier (BASIC, STANDARD, DEEP).
            profile: Enrichment profile (MINIMAL, STANDARD, COMPREHENSIVE).
            enrichment_context: Shared context for the entire enrichment run.

        Returns:
            EnrichmentResult containing field updates, relationship suggestions,
            provenance updates, and identified gaps.
        """
        ...


class EnricherRegistry:
    """Registry for entity enrichers. Supports dynamic registration.

    Follows the same pattern as GeneratorRegistry in synthetic/base.py.
    All enrichers are registered by their ENRICHES entity type.
    """

    _registry: dict[EntityType, type[AbstractEnricher]] = {}

    @classmethod
    def register(
        cls, enricher_class: type[AbstractEnricher]
    ) -> type[AbstractEnricher]:
        """Register an enricher class. Can be used as a decorator.

        Example:
            @EnricherRegistry.register
            class PersonEnricher(AbstractEnricher):
                ENRICHES = EntityType.PERSON
                ...
        """
        cls._registry[enricher_class.ENRICHES] = enricher_class
        return enricher_class

    @classmethod
    def get(cls, entity_type: EntityType) -> type[AbstractEnricher]:
        """Get the enricher class for a given entity type.

        Raises:
            KeyError: If no enricher is registered for the entity type.
        """
        if entity_type not in cls._registry:
            raise KeyError(f"No enricher registered for type: {entity_type}")
        return cls._registry[entity_type]

    @classmethod
    def all(cls) -> dict[EntityType, type[AbstractEnricher]]:
        """Return all registered enrichers as a dict mapping EntityType to class."""
        return dict(cls._registry)

    @classmethod
    def is_registered(cls, entity_type: EntityType) -> bool:
        """Check if an enricher is registered for a given entity type."""
        return entity_type in cls._registry

    @classmethod
    def clear(cls) -> None:
        """Clear all registered enrichers (primarily for testing)."""
        cls._registry.clear()


class AdversarialValidator:
    """Adversarial validation gate for enrichment results.

    Every EnrichmentResult passes through this validator BEFORE being applied
    to the knowledge graph. The validator enforces four classes of checks:

    1. Pydantic Model Validation — Proposed field updates are validated against
       the entity's Pydantic model. Dict values that should be sub-models are
       coerced. Fields that fail validation are rejected, not silently dropped.

    2. Confidence Rubric Enforcement — Each EnrichmentAction's claimed confidence
       level is checked against CONFIDENCE_RUBRIC criteria. An enricher claiming
       VERIFIED confidence from a web search result gets downgraded to MEDIUM.

    3. Source Staleness Check — Source dates are compared against
       SOURCE_VALIDITY_WINDOWS. A SOC 2 report older than 18 months triggers
       a confidence downgrade.

    4. Value Plausibility — Domain-specific bounds checks. A salary of $50M,
       a CVSS score of 15, or a negative headcount are caught here.

    Rejected fields are logged with full context (what was attempted, why it
    failed, what the enricher claimed as its source) so the enricher can be
    debugged without running the entire pipeline again.

    Usage:
        validator = AdversarialValidator()
        validated_result, failures = validator.validate(entity, result)
        # validated_result.field_updates contains ONLY safe updates
        # failures contains rejected fields with reasons
    """

    # Domain-specific bounds for plausibility checks
    PLAUSIBILITY_BOUNDS: ClassVar[dict[str, dict[str, tuple[float, float]]]] = {
        "person": {
            "annual_compensation": (15_000, 15_000_000),
            "years_experience": (0, 60),
            "direct_reports_count": (0, 500),
        },
        "system": {
            "annual_cost": (0, 500_000_000),
            "availability_target": (0, 100),
        },
        "risk": {
            "probability": (0.0, 1.0),
            "impact_score": (0, 100),
            "cvss_score": (0.0, 10.0),
        },
        "vulnerability": {
            "cvss_score": (0.0, 10.0),
        },
        "department": {
            "head_count": (0, 100_000),
            "budget": (0, 50_000_000_000),
        },
        "vendor": {
            "annual_spend": (0, 10_000_000_000),
        },
    }

    def validate(
        self,
        entity: BaseEntity,
        result: EnrichmentResult,
    ) -> tuple[EnrichmentResult, list[ValidationFailure]]:
        """Validate an enrichment result before it is applied to the graph.

        Returns a new EnrichmentResult with only the validated field_updates,
        plus a list of ValidationFailure records for anything rejected.

        Args:
            entity: The entity that would receive the updates.
            result: The enrichment result to validate.

        Returns:
            Tuple of (validated_result, list_of_failures).
        """
        failures: list[ValidationFailure] = []
        validated_fields: dict[str, Any] = {}

        entity_type_str = (
            entity.entity_type.lower()
            if isinstance(entity.entity_type, str)
            else entity.entity_type.value.lower()
            if hasattr(entity.entity_type, "value")
            else str(entity.entity_type).lower()
        )

        for field_name, value in result.field_updates.items():
            # --- Check 1: Pydantic model validation + sub-model coercion ---
            coerced_value, pydantic_failure = self._validate_pydantic_field(
                entity, field_name, value
            )
            if pydantic_failure:
                failures.append(pydantic_failure)
                continue

            # --- Check 2: Value plausibility ---
            plausibility_failure = self._check_plausibility(
                entity_type_str, field_name, coerced_value
            )
            if plausibility_failure:
                failures.append(plausibility_failure)
                continue

            validated_fields[field_name] = coerced_value

        # --- Check 3: Confidence rubric enforcement on actions ---
        validated_actions = []
        for action in result.actions:
            validated_action = self._enforce_confidence_rubric(action)
            validated_actions.append(validated_action)

        # Build validated result
        validated_result = EnrichmentResult(
            entity_id=result.entity_id,
            entity_type=result.entity_type,
            field_updates=validated_fields,
            provenance_update=result.provenance_update,
            relationship_suggestions=result.relationship_suggestions,
            known_gaps=result.known_gaps,
            actions=validated_actions,
        )

        if failures:
            logger.warning(
                f"AdversarialValidator rejected {len(failures)} field(s) for "
                f"{entity_type_str} {entity.id}: "
                f"{[f.field_name for f in failures]}"
            )

        return validated_result, failures

    def _validate_pydantic_field(
        self,
        entity: BaseEntity,
        field_name: str,
        value: Any,
    ) -> tuple[Any, ValidationFailure | None]:
        """Validate a field update against the entity's Pydantic model.

        Handles sub-model coercion: if a field expects a Pydantic model but
        receives a dict, attempts to construct the model from the dict.

        Returns:
            Tuple of (coerced_value, failure_or_none).
        """
        # Get the entity's model class
        entity_class = type(entity)

        # Check if this field exists on the model
        model_fields = entity_class.model_fields if hasattr(entity_class, "model_fields") else {}

        if field_name not in model_fields:
            # Field not in model — will go to __pydantic_extra__ due to extra="allow"
            # This is a valid pattern per ADR-002, but we log it
            logger.debug(
                f"Field '{field_name}' not in {entity_class.__name__} model_fields — "
                f"will be stored in __pydantic_extra__"
            )
            return value, None

        field_info = model_fields[field_name]
        field_annotation = field_info.annotation

        # Attempt sub-model coercion for dict values
        if isinstance(value, dict) and field_annotation is not None:
            coerced_value = self._coerce_to_submodel(
                field_name, value, field_annotation, entity_class.__name__
            )
            if coerced_value is not None:
                return coerced_value, None
            # If coercion failed, report it
            return value, ValidationFailure(
                field_name=field_name,
                failure_type="pydantic_validation",
                message=(
                    f"Dict value for '{field_name}' could not be coerced to "
                    f"expected type {field_annotation}. This is a sub-model "
                    f"validation failure — the enricher must construct the "
                    f"sub-model instance, not pass a raw dict."
                ),
                attempted_value=value,
            )

        # For list of dicts that should be list of sub-models
        if isinstance(value, list) and value and isinstance(value[0], dict):
            coerced_list = self._coerce_list_to_submodels(
                field_name, value, field_annotation, entity_class.__name__
            )
            if coerced_list is not None:
                return coerced_list, None
            # Lists of dicts that can't be coerced — report but allow
            # (some fields legitimately accept list[dict])
            logger.debug(
                f"List[dict] for '{field_name}' on {entity_class.__name__} — "
                f"could not coerce to sub-models, passing as-is"
            )

        return value, None

    def _coerce_to_submodel(
        self,
        field_name: str,
        value: dict,
        annotation: Any,
        entity_class_name: str,
    ) -> Any | None:
        """Attempt to construct a Pydantic sub-model from a dict.

        Returns the constructed model instance, or None if coercion fails.
        """
        import typing
        from pydantic import BaseModel

        # Unwrap Optional, Union types
        origin = getattr(annotation, "__origin__", None)
        args = getattr(annotation, "__args__", ())

        target_type = annotation

        # Handle Optional[X] → X
        if origin is typing.Union:
            non_none_args = [a for a in args if a is not type(None)]
            if len(non_none_args) == 1:
                target_type = non_none_args[0]

        # Check if target is a Pydantic BaseModel subclass
        if isinstance(target_type, type) and issubclass(target_type, BaseModel):
            try:
                return target_type.model_validate(value)
            except Exception as e:
                logger.debug(
                    f"Sub-model coercion failed for {entity_class_name}.{field_name}: {e}"
                )
                return None

        return value  # Not a sub-model field — return as-is

    def _coerce_list_to_submodels(
        self,
        field_name: str,
        value: list[dict],
        annotation: Any,
        entity_class_name: str,
    ) -> list | None:
        """Attempt to coerce a list of dicts to a list of Pydantic sub-models."""
        import typing
        from pydantic import BaseModel

        origin = getattr(annotation, "__origin__", None)
        args = getattr(annotation, "__args__", ())

        # Handle list[X]
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

        return None  # Could not determine sub-model type

    def _check_plausibility(
        self,
        entity_type_str: str,
        field_name: str,
        value: Any,
    ) -> ValidationFailure | None:
        """Check if a numeric value falls within plausible domain bounds."""
        bounds = self.PLAUSIBILITY_BOUNDS.get(entity_type_str, {})
        if field_name not in bounds:
            return None

        if not isinstance(value, (int, float)):
            return None

        low, high = bounds[field_name]
        if value < low or value > high:
            return ValidationFailure(
                field_name=field_name,
                failure_type="plausibility",
                message=(
                    f"Value {value} for '{field_name}' on {entity_type_str} "
                    f"outside plausible range [{low}, {high}]"
                ),
                attempted_value=value,
            )
        return None

    def _enforce_confidence_rubric(
        self, action: EnrichmentAction
    ) -> EnrichmentAction:
        """Enforce confidence rubric: downgrade inflated confidence claims.

        Checks that the claimed confidence level is supported by the source type
        and staleness window. Downgrades confidence if the claim is unsupported.
        """
        claimed = action.confidence
        if isinstance(claimed, str):
            try:
                claimed = ConfidenceLevel(claimed.lower())
            except ValueError:
                claimed = ConfidenceLevel.UNVERIFIED

        rubric = CONFIDENCE_RUBRIC.get(claimed, {})
        max_staleness = rubric.get("max_staleness_days", 0)

        # Check source staleness if source_date is provided
        if action.source_date:
            try:
                source_dt = datetime.fromisoformat(
                    action.source_date.replace("Z", "+00:00")
                )
                days_old = (datetime.now(UTC) - source_dt).days
                if days_old > max_staleness and max_staleness > 0:
                    # Downgrade: find the appropriate lower level
                    downgraded = self._downgrade_for_staleness(claimed, days_old)
                    if downgraded != claimed:
                        logger.info(
                            f"Confidence downgrade: {claimed.value} → {downgraded.value} "
                            f"for {action.entity_id} (source {days_old} days old, "
                            f"max {max_staleness} for {claimed.value})"
                        )
                        action = EnrichmentAction(
                            entity_id=action.entity_id,
                            entity_type=action.entity_type,
                            fields_enriched=action.fields_enriched,
                            source=action.source,
                            methodology=action.methodology,
                            confidence=downgraded,
                            source_date=action.source_date,
                            validity_window_days=action.validity_window_days,
                            timestamp=action.timestamp,
                        )
            except (ValueError, TypeError):
                pass  # Can't parse date — leave confidence as-is

        return action

    def _downgrade_for_staleness(
        self, current: ConfidenceLevel, days_old: int
    ) -> ConfidenceLevel:
        """Determine the appropriate confidence level given source age.

        Walks down the confidence ladder until finding a level whose
        staleness window accommodates the source age.
        """
        levels = [
            ConfidenceLevel.VERIFIED,
            ConfidenceLevel.HIGH,
            ConfidenceLevel.MEDIUM,
            ConfidenceLevel.LOW,
            ConfidenceLevel.UNVERIFIED,
        ]

        # Start from the current level and work downward
        start_idx = levels.index(current)
        for level in levels[start_idx:]:
            max_days = CONFIDENCE_RUBRIC[level].get("max_staleness_days", 0)
            if max_days == 0 or days_old <= max_days:
                return level

        return ConfidenceLevel.UNVERIFIED
