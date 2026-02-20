"""RelationshipWeaver: creates realistic relationships between generated entities."""

from __future__ import annotations

import random
from typing import TYPE_CHECKING

from domain.base import BaseRelationship, EntityType, RelationshipType

if TYPE_CHECKING:
    from synthetic.base import GenerationContext


class RelationshipWeaver:
    """Creates realistic relationships between generated entities.

    This is where the organizational structure comes together: assigning
    people to departments, systems to networks, policies to data assets, etc.
    """

    def __init__(self, context: GenerationContext) -> None:
        self._ctx = context

    def weave_all(self) -> list[BaseRelationship]:
        """Generate all relationship types. Returns flat list."""
        rels: list[BaseRelationship] = []
        # v0.1 relationships
        rels.extend(self._assign_people_to_departments())
        rels.extend(self._create_management_chains())
        rels.extend(self._assign_people_to_roles())
        rels.extend(self._assign_systems_to_networks())
        rels.extend(self._assign_systems_to_departments())
        rels.extend(self._assign_data_to_systems())
        rels.extend(self._assign_policies_to_assets())
        rels.extend(self._assign_vulns_to_systems())
        rels.extend(self._assign_threats_to_vulns())
        rels.extend(self._assign_vendors_to_systems())
        rels.extend(self._assign_locations())
        # Enterprise cross-layer relationships (L01-L11)
        rels.extend(self._link_controls_to_regulations())
        rels.extend(self._link_risks_to_controls())
        rels.extend(self._link_integrations_to_systems())
        rels.extend(self._link_data_flows_to_domains())
        rels.extend(self._link_capabilities_to_systems())
        rels.extend(self._link_products_to_portfolios())
        rels.extend(self._link_customers_to_products())
        rels.extend(self._link_contracts_to_vendors())
        rels.extend(self._link_initiatives_to_entities())
        rels.extend(self._link_sites_to_geographies())
        return rels

    def _assign_people_to_departments(self) -> list[BaseRelationship]:
        people = self._ctx.get_entities(EntityType.PERSON)
        departments = self._ctx.get_entities(EntityType.DEPARTMENT)
        profile = self._ctx.profile
        rels: list[BaseRelationship] = []

        if not departments or not people:
            return rels

        idx = 0
        for spec, dept in zip(profile.department_specs, departments, strict=False):
            count = max(1, int(len(people) * spec.headcount_fraction))
            for person in people[idx : idx + count]:
                rels.append(
                    BaseRelationship(
                        relationship_type=RelationshipType.WORKS_IN,
                        source_id=person.id,
                        target_id=dept.id,
                    )
                )
                person.department_id = dept.id
            idx += count

        # Assign any remaining people to random departments
        for person in people[idx:]:
            dept = random.choice(departments)
            rels.append(
                BaseRelationship(
                    relationship_type=RelationshipType.WORKS_IN,
                    source_id=person.id,
                    target_id=dept.id,
                )
            )
            person.department_id = dept.id

        return rels

    def _create_management_chains(self) -> list[BaseRelationship]:
        people = self._ctx.get_entities(EntityType.PERSON)
        departments = self._ctx.get_entities(EntityType.DEPARTMENT)
        rels: list[BaseRelationship] = []

        if not departments or len(people) < 2:
            return rels

        # For each department, pick a manager from its people
        dept_people: dict[str, list] = {}
        for person in people:
            did = getattr(person, "department_id", None)
            if did:
                dept_people.setdefault(did, []).append(person)

        for dept in departments:
            members = dept_people.get(dept.id, [])
            if len(members) < 2:
                continue
            manager = members[0]
            dept.head_id = manager.id
            rels.append(
                BaseRelationship(
                    relationship_type=RelationshipType.MANAGES,
                    source_id=manager.id,
                    target_id=dept.id,
                )
            )
            for report in members[1:]:
                rels.append(
                    BaseRelationship(
                        relationship_type=RelationshipType.REPORTS_TO,
                        source_id=report.id,
                        target_id=manager.id,
                    )
                )

        return rels

    def _assign_people_to_roles(self) -> list[BaseRelationship]:
        people = self._ctx.get_entities(EntityType.PERSON)
        roles = self._ctx.get_entities(EntityType.ROLE)
        rels: list[BaseRelationship] = []

        if not roles or not people:
            return rels

        # Group roles by department
        dept_roles: dict[str | None, list] = {}
        for role in roles:
            did = getattr(role, "department_id", None)
            dept_roles.setdefault(did, []).append(role)

        for person in people:
            did = getattr(person, "department_id", None)
            available = dept_roles.get(did, dept_roles.get(None, []))
            if available:
                role = random.choice(available)
                rels.append(
                    BaseRelationship(
                        relationship_type=RelationshipType.HAS_ROLE,
                        source_id=person.id,
                        target_id=role.id,
                    )
                )

        return rels

    def _assign_systems_to_networks(self) -> list[BaseRelationship]:
        systems = self._ctx.get_entities(EntityType.SYSTEM)
        networks = self._ctx.get_entities(EntityType.NETWORK)
        rels: list[BaseRelationship] = []

        if not networks or not systems:
            return rels

        for system in systems:
            network = random.choice(networks)
            system.network_id = network.id
            rels.append(
                BaseRelationship(
                    relationship_type=RelationshipType.CONNECTS_TO,
                    source_id=system.id,
                    target_id=network.id,
                )
            )

        # Add some inter-system dependencies
        for _i in range(min(len(systems) // 3, 20)):
            src, tgt = random.sample(systems, 2)
            rels.append(
                BaseRelationship(
                    relationship_type=RelationshipType.DEPENDS_ON,
                    source_id=src.id,
                    target_id=tgt.id,
                )
            )

        return rels

    def _assign_systems_to_departments(self) -> list[BaseRelationship]:
        systems = self._ctx.get_entities(EntityType.SYSTEM)
        departments = self._ctx.get_entities(EntityType.DEPARTMENT)
        rels: list[BaseRelationship] = []

        if not departments or not systems:
            return rels

        for system in systems:
            dept = random.choice(departments)
            system.department_id = dept.id
            rels.append(
                BaseRelationship(
                    relationship_type=RelationshipType.RESPONSIBLE_FOR,
                    source_id=dept.id,
                    target_id=system.id,
                )
            )

        return rels

    def _assign_data_to_systems(self) -> list[BaseRelationship]:
        data_assets = self._ctx.get_entities(EntityType.DATA_ASSET)
        systems = self._ctx.get_entities(EntityType.SYSTEM)
        rels: list[BaseRelationship] = []

        if not systems or not data_assets:
            return rels

        for asset in data_assets:
            system = random.choice(systems)
            asset.system_id = system.id
            rels.append(
                BaseRelationship(
                    relationship_type=RelationshipType.STORES,
                    source_id=system.id,
                    target_id=asset.id,
                )
            )

        return rels

    def _assign_policies_to_assets(self) -> list[BaseRelationship]:
        policies = self._ctx.get_entities(EntityType.POLICY)
        data_assets = self._ctx.get_entities(EntityType.DATA_ASSET)
        systems = self._ctx.get_entities(EntityType.SYSTEM)
        rels: list[BaseRelationship] = []

        targets = data_assets + systems
        if not policies or not targets:
            return rels

        for policy in policies:
            governed = random.sample(targets, k=min(random.randint(2, 6), len(targets)))
            for target in governed:
                rels.append(
                    BaseRelationship(
                        relationship_type=RelationshipType.GOVERNS,
                        source_id=policy.id,
                        target_id=target.id,
                    )
                )

        return rels

    def _assign_vulns_to_systems(self) -> list[BaseRelationship]:
        vulns = self._ctx.get_entities(EntityType.VULNERABILITY)
        systems = self._ctx.get_entities(EntityType.SYSTEM)
        rels: list[BaseRelationship] = []

        if not systems or not vulns:
            return rels

        for vuln in vulns:
            affected = random.sample(systems, k=min(random.randint(1, 3), len(systems)))
            vuln.affected_system_ids = [s.id for s in affected]
            for system in affected:
                rels.append(
                    BaseRelationship(
                        relationship_type=RelationshipType.AFFECTS,
                        source_id=vuln.id,
                        target_id=system.id,
                    )
                )

        return rels

    def _assign_threats_to_vulns(self) -> list[BaseRelationship]:
        actors = self._ctx.get_entities(EntityType.THREAT_ACTOR)
        vulns = self._ctx.get_entities(EntityType.VULNERABILITY)
        rels: list[BaseRelationship] = []

        if not actors or not vulns:
            return rels

        for actor in actors:
            targeted_vulns = random.sample(vulns, k=min(random.randint(1, 4), len(vulns)))
            for vuln in targeted_vulns:
                rels.append(
                    BaseRelationship(
                        relationship_type=RelationshipType.EXPLOITS,
                        source_id=actor.id,
                        target_id=vuln.id,
                    )
                )

        return rels

    def _assign_vendors_to_systems(self) -> list[BaseRelationship]:
        vendors = self._ctx.get_entities(EntityType.VENDOR)
        systems = self._ctx.get_entities(EntityType.SYSTEM)
        rels: list[BaseRelationship] = []

        if not vendors or not systems:
            return rels

        for vendor in vendors:
            supplied = random.sample(systems, k=min(random.randint(1, 3), len(systems)))
            for system in supplied:
                rels.append(
                    BaseRelationship(
                        relationship_type=RelationshipType.SUPPLIED_BY,
                        source_id=system.id,
                        target_id=vendor.id,
                    )
                )

        return rels

    def _assign_locations(self) -> list[BaseRelationship]:
        locations = self._ctx.get_entities(EntityType.LOCATION)
        departments = self._ctx.get_entities(EntityType.DEPARTMENT)
        networks = self._ctx.get_entities(EntityType.NETWORK)
        rels: list[BaseRelationship] = []

        if not locations:
            return rels

        for dept in departments:
            loc = random.choice(locations)
            dept.location_id = loc.id
            rels.append(
                BaseRelationship(
                    relationship_type=RelationshipType.LOCATED_AT,
                    source_id=dept.id,
                    target_id=loc.id,
                )
            )

        for network in networks:
            loc = random.choice(locations)
            network.location_id = loc.id
            rels.append(
                BaseRelationship(
                    relationship_type=RelationshipType.LOCATED_AT,
                    source_id=network.id,
                    target_id=loc.id,
                )
            )

        return rels

    # ------------------------------------------------------------------
    # Enterprise cross-layer relationships (L01-L11)
    # ------------------------------------------------------------------

    def _link_controls_to_regulations(self) -> list[BaseRelationship]:
        """Controls IMPLEMENTS Regulations."""
        controls = self._ctx.get_entities(EntityType.CONTROL)
        regulations = self._ctx.get_entities(EntityType.REGULATION)
        rels: list[BaseRelationship] = []
        if not controls or not regulations:
            return rels
        for control in controls:
            reg = random.choice(regulations)
            rels.append(
                BaseRelationship(
                    relationship_type=RelationshipType.IMPLEMENTS,
                    source_id=control.id,
                    target_id=reg.id,
                )
            )
        return rels

    def _link_risks_to_controls(self) -> list[BaseRelationship]:
        """Controls MITIGATES Risks."""
        controls = self._ctx.get_entities(EntityType.CONTROL)
        risks = self._ctx.get_entities(EntityType.RISK)
        rels: list[BaseRelationship] = []
        if not controls or not risks:
            return rels
        for risk in risks:
            mitigating = random.sample(controls, k=min(random.randint(1, 3), len(controls)))
            for control in mitigating:
                rels.append(
                    BaseRelationship(
                        relationship_type=RelationshipType.MITIGATES,
                        source_id=control.id,
                        target_id=risk.id,
                    )
                )
        return rels

    def _link_integrations_to_systems(self) -> list[BaseRelationship]:
        """Integrations INTEGRATES_WITH Systems."""
        integrations = self._ctx.get_entities(EntityType.INTEGRATION)
        systems = self._ctx.get_entities(EntityType.SYSTEM)
        rels: list[BaseRelationship] = []
        if not integrations or not systems:
            return rels
        for integration in integrations:
            target_sys = random.choice(systems)
            rels.append(
                BaseRelationship(
                    relationship_type=RelationshipType.INTEGRATES_WITH,
                    source_id=integration.id,
                    target_id=target_sys.id,
                )
            )
        return rels

    def _link_data_flows_to_domains(self) -> list[BaseRelationship]:
        """DataFlows BELONGS_TO DataDomains."""
        flows = self._ctx.get_entities(EntityType.DATA_FLOW)
        domains = self._ctx.get_entities(EntityType.DATA_DOMAIN)
        rels: list[BaseRelationship] = []
        if not flows or not domains:
            return rels
        for flow in flows:
            domain = random.choice(domains)
            rels.append(
                BaseRelationship(
                    relationship_type=RelationshipType.BELONGS_TO,
                    source_id=flow.id,
                    target_id=domain.id,
                )
            )
        return rels

    def _link_capabilities_to_systems(self) -> list[BaseRelationship]:
        """Systems SUPPORTS BusinessCapabilities."""
        capabilities = self._ctx.get_entities(EntityType.BUSINESS_CAPABILITY)
        systems = self._ctx.get_entities(EntityType.SYSTEM)
        rels: list[BaseRelationship] = []
        if not capabilities or not systems:
            return rels
        for cap in capabilities:
            supporting = random.sample(systems, k=min(random.randint(1, 3), len(systems)))
            for sys in supporting:
                rels.append(
                    BaseRelationship(
                        relationship_type=RelationshipType.SUPPORTS,
                        source_id=sys.id,
                        target_id=cap.id,
                    )
                )
        return rels

    def _link_products_to_portfolios(self) -> list[BaseRelationship]:
        """Products BELONGS_TO ProductPortfolios."""
        products = self._ctx.get_entities(EntityType.PRODUCT)
        portfolios = self._ctx.get_entities(EntityType.PRODUCT_PORTFOLIO)
        rels: list[BaseRelationship] = []
        if not products or not portfolios:
            return rels
        for product in products:
            portfolio = random.choice(portfolios)
            rels.append(
                BaseRelationship(
                    relationship_type=RelationshipType.BELONGS_TO,
                    source_id=product.id,
                    target_id=portfolio.id,
                )
            )
        return rels

    def _link_customers_to_products(self) -> list[BaseRelationship]:
        """Customers BUYS Products."""
        customers = self._ctx.get_entities(EntityType.CUSTOMER)
        products = self._ctx.get_entities(EntityType.PRODUCT)
        rels: list[BaseRelationship] = []
        if not customers or not products:
            return rels
        for customer in customers:
            bought = random.sample(products, k=min(random.randint(1, 3), len(products)))
            for product in bought:
                rels.append(
                    BaseRelationship(
                        relationship_type=RelationshipType.BUYS,
                        source_id=customer.id,
                        target_id=product.id,
                    )
                )
        return rels

    def _link_contracts_to_vendors(self) -> list[BaseRelationship]:
        """Contracts CONTRACTS_WITH Vendors."""
        contracts = self._ctx.get_entities(EntityType.CONTRACT)
        vendors = self._ctx.get_entities(EntityType.VENDOR)
        rels: list[BaseRelationship] = []
        if not contracts or not vendors:
            return rels
        for contract in contracts:
            vendor = random.choice(vendors)
            rels.append(
                BaseRelationship(
                    relationship_type=RelationshipType.CONTRACTS_WITH,
                    source_id=contract.id,
                    target_id=vendor.id,
                )
            )
        return rels

    def _link_initiatives_to_entities(self) -> list[BaseRelationship]:
        """Initiatives IMPACTS various entity types."""
        initiatives = self._ctx.get_entities(EntityType.INITIATIVE)
        systems = self._ctx.get_entities(EntityType.SYSTEM)
        capabilities = self._ctx.get_entities(EntityType.BUSINESS_CAPABILITY)
        rels: list[BaseRelationship] = []
        if not initiatives:
            return rels
        for initiative in initiatives:
            if systems:
                target = random.choice(systems)
                rels.append(
                    BaseRelationship(
                        relationship_type=RelationshipType.IMPACTS,
                        source_id=initiative.id,
                        target_id=target.id,
                    )
                )
            if capabilities:
                target = random.choice(capabilities)
                rels.append(
                    BaseRelationship(
                        relationship_type=RelationshipType.IMPACTS,
                        source_id=initiative.id,
                        target_id=target.id,
                    )
                )
        return rels

    def _link_sites_to_geographies(self) -> list[BaseRelationship]:
        """Sites LOCATED_AT Geographies."""
        sites = self._ctx.get_entities(EntityType.SITE)
        geos = self._ctx.get_entities(EntityType.GEOGRAPHY)
        rels: list[BaseRelationship] = []
        if not sites or not geos:
            return rels
        for site in sites:
            geo = random.choice(geos)
            rels.append(
                BaseRelationship(
                    relationship_type=RelationshipType.LOCATED_AT,
                    source_id=site.id,
                    target_id=geo.id,
                )
            )
        return rels
