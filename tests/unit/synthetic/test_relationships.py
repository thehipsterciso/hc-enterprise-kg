"""Tests for RelationshipWeaver."""

import random

from domain.base import EntityType, RelationshipType
from domain.entities.department import Department
from domain.entities.location import Location
from domain.entities.network import Network
from domain.entities.person import Person
from domain.entities.system import System
from domain.entities.vulnerability import Vulnerability
from synthetic.base import GenerationContext
from synthetic.profiles.tech_company import mid_size_tech_company
from synthetic.relationships import RelationshipWeaver


def _build_context(num_people: int = 10, seed: int = 42) -> GenerationContext:
    profile = mid_size_tech_company(num_people)
    ctx = GenerationContext(profile=profile, seed=seed)

    # Generate minimal entities
    people = [
        Person(id=f"p{i}", first_name=f"Person{i}", last_name="Test", name=f"Person{i} Test", email=f"p{i}@t.com")
        for i in range(num_people)
    ]
    departments = [
        Department(id=f"d{i}", name=spec.name)
        for i, spec in enumerate(profile.department_specs)
    ]
    systems = [
        System(id=f"s{i}", name=f"System{i}", system_type="application")
        for i in range(5)
    ]
    networks = [
        Network(id=f"n{i}", name=f"Network{i}", network_type="lan", cidr="10.0.0.0/24")
        for i in range(3)
    ]
    locations = [
        Location(id=f"l{i}", name=f"Location{i}", city=f"City{i}", country="US")
        for i in range(2)
    ]
    vulns = [
        Vulnerability(id=f"v{i}", name=f"CVE-2024-000{i}", severity="high")
        for i in range(2)
    ]

    ctx.store(EntityType.PERSON, people)
    ctx.store(EntityType.DEPARTMENT, departments)
    ctx.store(EntityType.SYSTEM, systems)
    ctx.store(EntityType.NETWORK, networks)
    ctx.store(EntityType.LOCATION, locations)
    ctx.store(EntityType.VULNERABILITY, vulns)

    return ctx


class TestRelationshipWeaver:
    def test_weave_all_produces_relationships(self):
        ctx = _build_context()
        weaver = RelationshipWeaver(ctx)
        rels = weaver.weave_all()
        assert len(rels) > 0

    def test_people_assigned_to_departments(self):
        ctx = _build_context()
        weaver = RelationshipWeaver(ctx)
        rels = weaver.weave_all()
        works_in = [r for r in rels if r.relationship_type == RelationshipType.WORKS_IN]
        assert len(works_in) > 0

    def test_systems_assigned_to_networks(self):
        ctx = _build_context()
        weaver = RelationshipWeaver(ctx)
        rels = weaver.weave_all()
        connects = [r for r in rels if r.relationship_type == RelationshipType.CONNECTS_TO]
        assert len(connects) > 0

    def test_locations_assigned(self):
        ctx = _build_context()
        weaver = RelationshipWeaver(ctx)
        rels = weaver.weave_all()
        located = [r for r in rels if r.relationship_type == RelationshipType.LOCATED_AT]
        assert len(located) > 0

    def test_management_chains_created(self):
        ctx = _build_context(num_people=20)
        weaver = RelationshipWeaver(ctx)
        rels = weaver.weave_all()
        reports_to = [r for r in rels if r.relationship_type == RelationshipType.REPORTS_TO]
        manages = [r for r in rels if r.relationship_type == RelationshipType.MANAGES]
        assert len(reports_to) > 0
        assert len(manages) > 0

    def test_vulns_assigned_to_systems(self):
        ctx = _build_context()
        weaver = RelationshipWeaver(ctx)
        rels = weaver.weave_all()
        affects = [r for r in rels if r.relationship_type == RelationshipType.AFFECTS]
        assert len(affects) > 0

    def test_empty_entity_lists_produce_no_relationships(self):
        profile = mid_size_tech_company(10)
        ctx = GenerationContext(profile=profile, seed=42)
        # Don't store any entities
        weaver = RelationshipWeaver(ctx)
        rels = weaver.weave_all()
        assert len(rels) == 0

    def test_seed_reproducibility(self):
        ctx1 = _build_context(seed=99)
        rels1 = RelationshipWeaver(ctx1).weave_all()

        ctx2 = _build_context(seed=99)
        rels2 = RelationshipWeaver(ctx2).weave_all()

        assert len(rels1) == len(rels2)
