"""RelationshipWeaver: creates realistic relationships between generated entities."""

from __future__ import annotations

import random
from typing import TYPE_CHECKING

from domain.base import BaseRelationship, EntityType, RelationshipType

if TYPE_CHECKING:
    from synthetic.base import GenerationContext

# Severity → weight mapping for security relationships
SEVERITY_WEIGHT = {"low": 0.3, "medium": 0.5, "high": 0.8, "critical": 1.0}

DEPENDENCY_TYPES = ["runtime", "build", "data", "authentication", "monitoring"]

SUPPLY_TYPES = ["license", "service", "hardware", "subscription", "support"]

EXPLOIT_MATURITY = ["weaponized", "proof_of_concept", "theoretical"]


class RelationshipWeaver:
    """Creates realistic relationships between generated entities.

    This is where the organizational structure comes together: assigning
    people to departments, systems to networks, policies to data assets, etc.
    """

    def __init__(self, context: GenerationContext) -> None:
        self._ctx = context

    def _make_rel(
        self,
        rel_type: RelationshipType,
        source_id: str,
        target_id: str,
        weight: float = 1.0,
        confidence: float = 1.0,
        properties: dict | None = None,
    ) -> BaseRelationship:
        """Create a relationship with explicit metadata."""
        return BaseRelationship(
            relationship_type=rel_type,
            source_id=source_id,
            target_id=target_id,
            weight=round(weight, 2),
            confidence=round(confidence, 2),
            properties=properties or {},
        )

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
        # New relationship types (PR3)
        rels.extend(self._link_threats_to_risks())
        rels.extend(self._link_regulations_to_jurisdictions())
        rels.extend(self._link_controls_to_threats())
        rels.extend(self._link_systems_hosting())
        rels.extend(self._link_data_flows_to_systems())
        rels.extend(self._link_data_assets_to_domains())
        rels.extend(self._link_capabilities_to_roles())
        rels.extend(self._link_org_units_to_departments())
        rels.extend(self._link_products_to_systems())
        rels.extend(self._link_products_to_segments())
        rels.extend(self._link_initiatives_to_risks())
        rels.extend(self._link_persons_to_org_units())
        # Populate entity mirror fields from woven relationships
        self._populate_mirror_fields(rels)
        return rels

    # ------------------------------------------------------------------
    # v0.1 relationships (enriched with metadata)
    # ------------------------------------------------------------------

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
                    self._make_rel(
                        RelationshipType.WORKS_IN,
                        person.id,
                        dept.id,
                        weight=1.0,
                        confidence=0.95,
                        properties={"assignment_type": "primary"},
                    )
                )
                person.department_id = dept.id
            idx += count

        # Assign any remaining people to random departments
        for person in people[idx:]:
            dept = random.choice(departments)
            rels.append(
                self._make_rel(
                    RelationshipType.WORKS_IN,
                    person.id,
                    dept.id,
                    weight=1.0,
                    confidence=0.95,
                    properties={"assignment_type": "primary"},
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
                self._make_rel(
                    RelationshipType.MANAGES,
                    manager.id,
                    dept.id,
                    weight=1.0,
                    confidence=0.90,
                    properties={"management_type": "direct"},
                )
            )
            for report in members[1:]:
                rels.append(
                    self._make_rel(
                        RelationshipType.REPORTS_TO,
                        report.id,
                        manager.id,
                        weight=1.0,
                        confidence=0.90,
                        properties={"reporting_type": "solid_line"},
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
                    self._make_rel(
                        RelationshipType.HAS_ROLE,
                        person.id,
                        role.id,
                        weight=0.9,
                        confidence=0.85,
                        properties={"assignment_type": "primary"},
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
                self._make_rel(
                    RelationshipType.CONNECTS_TO,
                    system.id,
                    network.id,
                    weight=1.0,
                    confidence=0.90,
                    properties={"connection_type": "network"},
                )
            )

        # Add inter-system dependencies — scale cap with system count
        dep_cap = max(5, len(systems) // 3)
        for _ in range(dep_cap):
            src, tgt = random.sample(systems, 2)
            dep_type = random.choice(DEPENDENCY_TYPES)
            rels.append(
                self._make_rel(
                    RelationshipType.DEPENDS_ON,
                    src.id,
                    tgt.id,
                    weight=round(random.uniform(0.4, 1.0), 2),
                    confidence=0.75,
                    properties={"dependency_type": dep_type},
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
                self._make_rel(
                    RelationshipType.RESPONSIBLE_FOR,
                    dept.id,
                    system.id,
                    weight=0.8,
                    confidence=0.85,
                    properties={"ownership_type": "primary"},
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
                self._make_rel(
                    RelationshipType.STORES,
                    system.id,
                    asset.id,
                    weight=1.0,
                    confidence=0.90,
                    properties={"storage_type": "primary"},
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
            enforced = getattr(policy, "is_enforced", True)
            for target in governed:
                rels.append(
                    self._make_rel(
                        RelationshipType.GOVERNS,
                        policy.id,
                        target.id,
                        weight=round(random.uniform(0.7, 1.0), 2),
                        confidence=0.80,
                        properties={
                            "enforcement": "active" if enforced else "monitoring",
                        },
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
            severity = getattr(vuln, "severity", "medium")
            for system in affected:
                rels.append(
                    self._make_rel(
                        RelationshipType.AFFECTS,
                        vuln.id,
                        system.id,
                        weight=SEVERITY_WEIGHT.get(severity, 0.5),
                        confidence=0.80,
                        properties={"severity": severity},
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
            sophistication = getattr(actor, "sophistication", "medium")
            for vuln in targeted_vulns:
                maturity = random.choice(EXPLOIT_MATURITY)
                rels.append(
                    self._make_rel(
                        RelationshipType.EXPLOITS,
                        actor.id,
                        vuln.id,
                        weight=round(random.uniform(0.5, 1.0), 2),
                        confidence=0.70,
                        properties={
                            "exploit_maturity": maturity,
                            "actor_sophistication": sophistication,
                        },
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
            vendor_type = getattr(vendor, "vendor_type", "software_license")
            for system in supplied:
                rels.append(
                    self._make_rel(
                        RelationshipType.SUPPLIED_BY,
                        system.id,
                        vendor.id,
                        weight=0.8,
                        confidence=0.85,
                        properties={"supply_type": random.choice(SUPPLY_TYPES)},
                    )
                )
            # Tag vendor with supply context
            if vendor_type in ("saas", "iaas", "managed_service"):
                vendor.has_data_access = getattr(vendor, "has_data_access", True)

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
                self._make_rel(
                    RelationshipType.LOCATED_AT,
                    dept.id,
                    loc.id,
                    weight=1.0,
                    confidence=0.95,
                    properties={"location_type": "primary"},
                )
            )

        for network in networks:
            loc = random.choice(locations)
            network.location_id = loc.id
            rels.append(
                self._make_rel(
                    RelationshipType.LOCATED_AT,
                    network.id,
                    loc.id,
                    weight=1.0,
                    confidence=0.95,
                    properties={"location_type": "primary"},
                )
            )

        return rels

    # ------------------------------------------------------------------
    # Enterprise cross-layer relationships (L01-L11) — enriched
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
                self._make_rel(
                    RelationshipType.IMPLEMENTS,
                    control.id,
                    reg.id,
                    weight=0.85,
                    confidence=0.80,
                    properties={"implementation_status": "implemented"},
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
            risk_level = getattr(risk, "inherent_risk_level", "Medium")
            for control in mitigating:
                effectiveness = (
                    "High" if random.random() < 0.6 else "Medium"
                )
                rels.append(
                    self._make_rel(
                        RelationshipType.MITIGATES,
                        control.id,
                        risk.id,
                        weight=0.8,
                        confidence=0.80,
                        properties={
                            "effectiveness": effectiveness,
                            "risk_level": risk_level,
                        },
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
            protocol = getattr(integration, "protocol", "REST")
            rels.append(
                self._make_rel(
                    RelationshipType.INTEGRATES_WITH,
                    integration.id,
                    target_sys.id,
                    weight=0.85,
                    confidence=0.80,
                    properties={"protocol": protocol},
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
            classification = getattr(flow, "data_classification", "Internal")
            rels.append(
                self._make_rel(
                    RelationshipType.BELONGS_TO,
                    flow.id,
                    domain.id,
                    weight=0.75,
                    confidence=0.80,
                    properties={"data_classification": classification},
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
            importance = getattr(cap, "strategic_importance", "Medium")
            for sys in supporting:
                rels.append(
                    self._make_rel(
                        RelationshipType.SUPPORTS,
                        sys.id,
                        cap.id,
                        weight=round(random.uniform(0.6, 1.0), 2),
                        confidence=0.75,
                        properties={"strategic_importance": importance},
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
                self._make_rel(
                    RelationshipType.BELONGS_TO,
                    product.id,
                    portfolio.id,
                    weight=0.9,
                    confidence=0.90,
                    properties={"portfolio_assignment": "primary"},
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
            tier = getattr(customer, "customer_tier", "standard")
            for product in bought:
                rels.append(
                    self._make_rel(
                        RelationshipType.BUYS,
                        customer.id,
                        product.id,
                        weight=round(random.uniform(0.6, 1.0), 2),
                        confidence=0.85,
                        properties={"customer_tier": tier},
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
            contract_type = getattr(contract, "contract_type", "master_agreement")
            rels.append(
                self._make_rel(
                    RelationshipType.CONTRACTS_WITH,
                    contract.id,
                    vendor.id,
                    weight=0.9,
                    confidence=0.90,
                    properties={"contract_type": contract_type},
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
            init_type = getattr(initiative, "initiative_type", "strategic")
            if systems:
                target = random.choice(systems)
                rels.append(
                    self._make_rel(
                        RelationshipType.IMPACTS,
                        initiative.id,
                        target.id,
                        weight=round(random.uniform(0.5, 1.0), 2),
                        confidence=0.75,
                        properties={"initiative_type": init_type, "impact_area": "technology"},
                    )
                )
            if capabilities:
                target = random.choice(capabilities)
                rels.append(
                    self._make_rel(
                        RelationshipType.IMPACTS,
                        initiative.id,
                        target.id,
                        weight=round(random.uniform(0.5, 1.0), 2),
                        confidence=0.75,
                        properties={"initiative_type": init_type, "impact_area": "capability"},
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
            site_type = getattr(site, "site_type", "Office")
            rels.append(
                self._make_rel(
                    RelationshipType.LOCATED_AT,
                    site.id,
                    geo.id,
                    weight=1.0,
                    confidence=0.95,
                    properties={"site_type": site_type},
                )
            )
        return rels

    # ------------------------------------------------------------------
    # New relationship types (12 new weaver methods)
    # ------------------------------------------------------------------

    def _link_threats_to_risks(self) -> list[BaseRelationship]:
        """Threats CREATES_RISK Risks."""
        threats = self._ctx.get_entities(EntityType.THREAT)
        risks = self._ctx.get_entities(EntityType.RISK)
        rels: list[BaseRelationship] = []
        if not threats or not risks:
            return rels
        for threat in threats:
            target_risks = random.sample(risks, k=min(random.randint(1, 2), len(risks)))
            threat_level = getattr(threat, "threat_level", "Medium")
            for risk in target_risks:
                rels.append(
                    self._make_rel(
                        RelationshipType.CREATES_RISK,
                        threat.id,
                        risk.id,
                        weight=SEVERITY_WEIGHT.get(threat_level.lower(), 0.5),
                        confidence=0.75,
                        properties={"threat_level": threat_level},
                    )
                )
        return rels

    def _link_regulations_to_jurisdictions(self) -> list[BaseRelationship]:
        """Regulations SUBJECT_TO Jurisdictions."""
        regulations = self._ctx.get_entities(EntityType.REGULATION)
        jurisdictions = self._ctx.get_entities(EntityType.JURISDICTION)
        rels: list[BaseRelationship] = []
        if not regulations or not jurisdictions:
            return rels
        for regulation in regulations:
            jurisdiction = random.choice(jurisdictions)
            rels.append(
                self._make_rel(
                    RelationshipType.SUBJECT_TO,
                    regulation.id,
                    jurisdiction.id,
                    weight=1.0,
                    confidence=0.90,
                    properties={"regulatory_scope": "mandatory"},
                )
            )
        return rels

    def _link_controls_to_threats(self) -> list[BaseRelationship]:
        """Controls ADDRESSES Threats."""
        controls = self._ctx.get_entities(EntityType.CONTROL)
        threats = self._ctx.get_entities(EntityType.THREAT)
        rels: list[BaseRelationship] = []
        if not controls or not threats:
            return rels
        for control in controls:
            addressed = random.sample(threats, k=min(random.randint(1, 2), len(threats)))
            control_type = getattr(control, "control_type", "preventive")
            for threat in addressed:
                rels.append(
                    self._make_rel(
                        RelationshipType.ADDRESSES,
                        control.id,
                        threat.id,
                        weight=round(random.uniform(0.6, 1.0), 2),
                        confidence=0.75,
                        properties={"control_type": control_type},
                    )
                )
        return rels

    def _link_systems_hosting(self) -> list[BaseRelationship]:
        """Infrastructure systems HOSTS application systems."""
        systems = self._ctx.get_entities(EntityType.SYSTEM)
        rels: list[BaseRelationship] = []
        if len(systems) < 2:
            return rels

        infra_types = {"server", "infrastructure", "virtual_machine", "container"}
        app_types = {"application", "web_application", "microservice"}

        infra = [s for s in systems if getattr(s, "system_type", "") in infra_types]
        apps = [s for s in systems if getattr(s, "system_type", "") in app_types]

        if not infra or not apps:
            return rels

        for app in apps:
            host = random.choice(infra)
            rels.append(
                self._make_rel(
                    RelationshipType.HOSTS,
                    host.id,
                    app.id,
                    weight=1.0,
                    confidence=0.85,
                    properties={"hosting_type": "primary"},
                )
            )
        return rels

    def _link_data_flows_to_systems(self) -> list[BaseRelationship]:
        """DataFlows FLOWS_TO destination Systems."""
        flows = self._ctx.get_entities(EntityType.DATA_FLOW)
        systems = self._ctx.get_entities(EntityType.SYSTEM)
        rels: list[BaseRelationship] = []
        if not flows or not systems:
            return rels
        for flow in flows:
            target_sys = random.choice(systems)
            encrypted = getattr(flow, "encryption_in_transit", False)
            rels.append(
                self._make_rel(
                    RelationshipType.FLOWS_TO,
                    flow.id,
                    target_sys.id,
                    weight=0.85,
                    confidence=0.80,
                    properties={"encrypted": encrypted},
                )
            )
        return rels

    def _link_data_assets_to_domains(self) -> list[BaseRelationship]:
        """DataAssets CLASSIFIED_AS DataDomains."""
        assets = self._ctx.get_entities(EntityType.DATA_ASSET)
        domains = self._ctx.get_entities(EntityType.DATA_DOMAIN)
        rels: list[BaseRelationship] = []
        if not assets or not domains:
            return rels
        for asset in assets:
            domain = random.choice(domains)
            classification = getattr(asset, "classification", "Internal")
            rels.append(
                self._make_rel(
                    RelationshipType.CLASSIFIED_AS,
                    asset.id,
                    domain.id,
                    weight=0.8,
                    confidence=0.80,
                    properties={"data_classification": classification},
                )
            )
        return rels

    def _link_capabilities_to_roles(self) -> list[BaseRelationship]:
        """BusinessCapabilities REALIZED_BY Roles."""
        capabilities = self._ctx.get_entities(EntityType.BUSINESS_CAPABILITY)
        roles = self._ctx.get_entities(EntityType.ROLE)
        rels: list[BaseRelationship] = []
        if not capabilities or not roles:
            return rels
        for cap in capabilities:
            realizers = random.sample(roles, k=min(random.randint(1, 2), len(roles)))
            for role in realizers:
                rels.append(
                    self._make_rel(
                        RelationshipType.REALIZED_BY,
                        cap.id,
                        role.id,
                        weight=round(random.uniform(0.6, 1.0), 2),
                        confidence=0.75,
                        properties={"realization_type": "primary"},
                    )
                )
        return rels

    def _link_org_units_to_departments(self) -> list[BaseRelationship]:
        """OrganizationalUnits CONTAINS Departments."""
        org_units = self._ctx.get_entities(EntityType.ORGANIZATIONAL_UNIT)
        departments = self._ctx.get_entities(EntityType.DEPARTMENT)
        rels: list[BaseRelationship] = []
        if not org_units or not departments:
            return rels
        for dept in departments:
            ou = random.choice(org_units)
            rels.append(
                self._make_rel(
                    RelationshipType.CONTAINS,
                    ou.id,
                    dept.id,
                    weight=1.0,
                    confidence=0.90,
                    properties={"containment_type": "organizational"},
                )
            )
        return rels

    def _link_products_to_systems(self) -> list[BaseRelationship]:
        """Systems DELIVERS Products."""
        products = self._ctx.get_entities(EntityType.PRODUCT)
        systems = self._ctx.get_entities(EntityType.SYSTEM)
        rels: list[BaseRelationship] = []
        if not products or not systems:
            return rels
        for product in products:
            delivering = random.sample(systems, k=min(random.randint(1, 2), len(systems)))
            criticality = getattr(product, "criticality", "medium")
            for sys in delivering:
                rels.append(
                    self._make_rel(
                        RelationshipType.DELIVERS,
                        sys.id,
                        product.id,
                        weight=SEVERITY_WEIGHT.get(criticality, 0.5),
                        confidence=0.80,
                        properties={"criticality": criticality},
                    )
                )
        return rels

    def _link_products_to_segments(self) -> list[BaseRelationship]:
        """Products SERVES MarketSegments."""
        products = self._ctx.get_entities(EntityType.PRODUCT)
        segments = self._ctx.get_entities(EntityType.MARKET_SEGMENT)
        rels: list[BaseRelationship] = []
        if not products or not segments:
            return rels
        for product in products:
            served = random.sample(segments, k=min(random.randint(1, 2), len(segments)))
            for segment in served:
                rels.append(
                    self._make_rel(
                        RelationshipType.SERVES,
                        product.id,
                        segment.id,
                        weight=round(random.uniform(0.6, 1.0), 2),
                        confidence=0.80,
                        properties={"market_fit": "primary"},
                    )
                )
        return rels

    def _link_initiatives_to_risks(self) -> list[BaseRelationship]:
        """Initiatives IMPACTS Risks (risk-driven initiatives)."""
        initiatives = self._ctx.get_entities(EntityType.INITIATIVE)
        risks = self._ctx.get_entities(EntityType.RISK)
        rels: list[BaseRelationship] = []
        if not initiatives or not risks:
            return rels
        for initiative in initiatives:
            target_risks = random.sample(risks, k=min(random.randint(1, 2), len(risks)))
            for risk in target_risks:
                risk_level = getattr(risk, "inherent_risk_level", "Medium")
                rels.append(
                    self._make_rel(
                        RelationshipType.IMPACTS,
                        initiative.id,
                        risk.id,
                        weight=SEVERITY_WEIGHT.get(risk_level.lower(), 0.5),
                        confidence=0.70,
                        properties={"impact_area": "risk_reduction"},
                    )
                )
        return rels

    def _link_persons_to_org_units(self) -> list[BaseRelationship]:
        """Persons MEMBER_OF OrganizationalUnits."""
        people = self._ctx.get_entities(EntityType.PERSON)
        org_units = self._ctx.get_entities(EntityType.ORGANIZATIONAL_UNIT)
        rels: list[BaseRelationship] = []
        if not people or not org_units:
            return rels
        for person in people:
            ou = random.choice(org_units)
            rels.append(
                self._make_rel(
                    RelationshipType.MEMBER_OF,
                    person.id,
                    ou.id,
                    weight=1.0,
                    confidence=0.85,
                    properties={"membership_type": "primary"},
                )
            )
        return rels

    # ------------------------------------------------------------------
    # Mirror field population
    # ------------------------------------------------------------------

    def _populate_mirror_fields(self, rels: list[BaseRelationship]) -> None:
        """Populate denormalized mirror fields on entities from woven relationships."""
        # Build lookup indexes: entity_id → entity
        entity_index: dict[str, object] = {}
        for etype in EntityType:
            for entity in self._ctx.get_entities(etype):
                entity_index[entity.id] = entity

        # Collect relationship edges by type
        edges_by_type: dict[RelationshipType, list[BaseRelationship]] = {}
        for rel in rels:
            edges_by_type.setdefault(rel.relationship_type, []).append(rel)

        # Person.holds_roles ← HAS_ROLE (person → role)
        for rel in edges_by_type.get(RelationshipType.HAS_ROLE, []):
            person = entity_index.get(rel.source_id)
            if person and hasattr(person, "holds_roles"):
                if not isinstance(person.holds_roles, list):
                    person.holds_roles = []
                person.holds_roles.append(rel.target_id)

        # Person.located_at ← LOCATED_AT where source is a department
        # We derive person location from their department's location
        dept_location: dict[str, str] = {}
        for rel in edges_by_type.get(RelationshipType.LOCATED_AT, []):
            source = entity_index.get(rel.source_id)
            if source and getattr(source, "entity_type", None) == EntityType.DEPARTMENT:
                dept_location[rel.source_id] = rel.target_id

        for rel in edges_by_type.get(RelationshipType.WORKS_IN, []):
            person = entity_index.get(rel.source_id)
            loc_id = dept_location.get(rel.target_id)
            if person and loc_id and hasattr(person, "located_at"):
                if not isinstance(person.located_at, list):
                    person.located_at = []
                if loc_id not in person.located_at:
                    person.located_at.append(loc_id)

        # Role.filled_by_persons ← HAS_ROLE reverse (role ← person)
        for rel in edges_by_type.get(RelationshipType.HAS_ROLE, []):
            role = entity_index.get(rel.target_id)
            if role and hasattr(role, "filled_by_persons"):
                if not isinstance(role.filled_by_persons, list):
                    role.filled_by_persons = []
                role.filled_by_persons.append(rel.source_id)

        # Role.headcount_filled ← count of filled_by_persons
        roles = self._ctx.get_entities(EntityType.ROLE)
        for role in roles:
            filled = getattr(role, "filled_by_persons", [])
            if isinstance(filled, list):
                role.headcount_filled = len(filled)

        # Person.participates_in_initiatives ← IMPACTS where person's dept
        # is target (simplified: assign initiative awareness to subset of people)
        people = self._ctx.get_entities(EntityType.PERSON)
        initiatives = self._ctx.get_entities(EntityType.INITIATIVE)
        if people and initiatives:
            # ~20% of people are aware of initiatives
            aware_count = max(1, len(people) // 5)
            aware_people = random.sample(people, k=min(aware_count, len(people)))
            for person in aware_people:
                if hasattr(person, "participates_in_initiatives"):
                    if not isinstance(person.participates_in_initiatives, list):
                        person.participates_in_initiatives = []
                    init = random.choice(initiatives)
                    person.participates_in_initiatives.append(init.id)
