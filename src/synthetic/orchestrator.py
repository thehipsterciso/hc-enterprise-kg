"""SyntheticOrchestrator: coordinates full synthetic KG generation from an OrgProfile."""

from __future__ import annotations

import random

from domain.base import EntityType
from graph.knowledge_graph import KnowledgeGraph
from synthetic.base import GenerationContext, GeneratorRegistry

# Import generators to trigger registration
import synthetic.generators  # noqa: F401
from synthetic.profiles.base_profile import OrgProfile
from synthetic.relationships import RelationshipWeaver

# Generation order matters: some entities reference others
GENERATION_ORDER: list[tuple[EntityType, str]] = [
    (EntityType.LOCATION, "location_count"),
    (EntityType.DEPARTMENT, "_department_count"),
    (EntityType.ROLE, "_role_count"),
    (EntityType.PERSON, "employee_count"),
    (EntityType.NETWORK, "_network_count"),
    (EntityType.SYSTEM, "system_count_range"),
    (EntityType.DATA_ASSET, "data_asset_count_range"),
    (EntityType.POLICY, "policy_count_range"),
    (EntityType.VENDOR, "vendor_count_range"),
    (EntityType.VULNERABILITY, "_vuln_count"),
    (EntityType.THREAT_ACTOR, "threat_actor_count_range"),
    (EntityType.INCIDENT, "incident_count_range"),
]


class SyntheticOrchestrator:
    """Coordinates full synthetic KG generation from an OrgProfile.

    Usage:
        profile = mid_size_tech_company(500)
        kg = KnowledgeGraph()
        orchestrator = SyntheticOrchestrator(kg, profile, seed=42)
        orchestrator.generate()
    """

    def __init__(
        self,
        knowledge_graph: KnowledgeGraph,
        profile: OrgProfile,
        seed: int | None = None,
    ) -> None:
        self._kg = knowledge_graph
        self._profile = profile
        self._context = GenerationContext(profile=profile, seed=seed)

    def generate(self) -> dict[str, int]:
        """Run the full generation pipeline. Returns counts by entity type."""
        counts: dict[str, int] = {}

        # Phase 1: Generate all entities in dependency order
        for entity_type, count_key in GENERATION_ORDER:
            if not GeneratorRegistry.is_registered(entity_type):
                continue

            count = self._resolve_count(entity_type, count_key)
            if count <= 0:
                continue

            generator_class = GeneratorRegistry.get(entity_type)
            generator = generator_class()
            entities = generator.generate(count, self._context)

            self._kg.add_entities_bulk(entities)
            counts[entity_type.value] = len(entities)

        # Phase 2: Weave relationships
        weaver = RelationshipWeaver(self._context)
        relationships = weaver.weave_all()
        self._kg.add_relationships_bulk(relationships)
        counts["_relationships"] = len(relationships)

        return counts

    def _resolve_count(self, entity_type: EntityType, count_key: str) -> int:
        """Resolve the count for an entity type from the profile."""
        profile = self._profile

        if count_key.startswith("_"):
            if entity_type == EntityType.DEPARTMENT:
                return len(profile.department_specs)
            elif entity_type == EntityType.NETWORK:
                return len(profile.network_specs) if profile.network_specs else 0
            elif entity_type == EntityType.ROLE:
                return 0  # RoleGenerator derives count from departments
            elif entity_type == EntityType.VULNERABILITY:
                system_count = len(self._context.get_entities(EntityType.SYSTEM))
                return max(1, int(system_count * profile.vulnerability_probability))
            return 0

        value = getattr(profile, count_key, None)
        if isinstance(value, int):
            return value
        if isinstance(value, tuple) and len(value) == 2:
            return random.randint(value[0], value[1])
        return 0

    @property
    def context(self) -> GenerationContext:
        return self._context
