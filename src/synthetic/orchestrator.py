"""SyntheticOrchestrator: coordinates full synthetic KG generation from an OrgProfile."""

from __future__ import annotations

import random
from typing import TYPE_CHECKING

# Import generators to trigger registration
import synthetic.generators  # noqa: F401
from domain.base import EntityType
from synthetic.base import GenerationContext, GeneratorRegistry
from synthetic.relationships import RelationshipWeaver

if TYPE_CHECKING:
    from graph.knowledge_graph import KnowledgeGraph
    from synthetic.profiles.base_profile import OrgProfile

# Generation order matters: some entities reference others.
# v0.1 types first, then enterprise types in layer dependency order.
GENERATION_ORDER: list[tuple[EntityType, str]] = [
    # --- v0.1 original types ---
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
    # --- L01: Compliance & Governance ---
    (EntityType.REGULATION, "regulation_count_range"),
    (EntityType.CONTROL, "control_count_range"),
    (EntityType.RISK, "risk_count_range"),
    (EntityType.THREAT, "threat_count_range"),
    # --- L02: Technology & Systems ---
    (EntityType.INTEGRATION, "integration_count_range"),
    # --- L03: Data Assets ---
    (EntityType.DATA_DOMAIN, "data_domain_count_range"),
    (EntityType.DATA_FLOW, "data_flow_count_range"),
    # --- L04: Organization ---
    (EntityType.ORGANIZATIONAL_UNIT, "org_unit_count_range"),
    # --- L06: Business Capabilities ---
    (EntityType.BUSINESS_CAPABILITY, "capability_count_range"),
    # --- L07: Locations & Facilities ---
    (EntityType.SITE, "site_count_range"),
    (EntityType.GEOGRAPHY, "geography_count_range"),
    (EntityType.JURISDICTION, "jurisdiction_count_range"),
    # --- L08: Products & Services ---
    (EntityType.PRODUCT_PORTFOLIO, "product_portfolio_count_range"),
    (EntityType.PRODUCT, "product_count_range"),
    # --- L09: Customers & Markets ---
    (EntityType.MARKET_SEGMENT, "market_segment_count_range"),
    (EntityType.CUSTOMER, "customer_count_range"),
    # --- L10: Vendors & Partners ---
    (EntityType.CONTRACT, "contract_count_range"),
    # --- L11: Strategic Initiatives ---
    (EntityType.INITIATIVE, "initiative_count_range"),
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
                # RoleGenerator derives roles from departments, not from count.
                # Return department count so the orchestrator doesn't skip it.
                return len(profile.department_specs)
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
