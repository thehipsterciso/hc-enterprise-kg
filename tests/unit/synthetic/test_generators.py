"""Tests for entity generators."""

# Import to trigger registration
import synthetic.generators  # noqa: F401
from domain.base import EntityType
from synthetic.base import GenerationContext, GeneratorRegistry
from synthetic.profiles.tech_company import mid_size_tech_company


class TestGenerators:
    def _make_context(self, employees=50):
        profile = mid_size_tech_company(employees)
        return GenerationContext(profile=profile, seed=42)

    def test_people_generator(self):
        ctx = self._make_context()
        gen = GeneratorRegistry.get(EntityType.PERSON)()
        people = gen.generate(50, ctx)
        assert len(people) == 50
        assert all(p.entity_type == EntityType.PERSON for p in people)
        assert all(p.email for p in people)

    def test_department_generator(self):
        ctx = self._make_context()
        gen = GeneratorRegistry.get(EntityType.DEPARTMENT)()
        depts = gen.generate(len(ctx.profile.department_specs), ctx)
        assert len(depts) == len(ctx.profile.department_specs)

    def test_system_generator(self):
        ctx = self._make_context()
        gen = GeneratorRegistry.get(EntityType.SYSTEM)()
        systems = gen.generate(20, ctx)
        assert len(systems) == 20
        assert all(s.entity_type == EntityType.SYSTEM for s in systems)

    def test_vulnerability_generator(self):
        ctx = self._make_context()
        gen = GeneratorRegistry.get(EntityType.VULNERABILITY)()
        vulns = gen.generate(5, ctx)
        assert len(vulns) == 5
        assert all(v.cve_id for v in vulns)

    def test_seed_reproducibility(self):
        # Each context re-seeds Faker globally, so we need fresh generators
        ctx1 = GenerationContext(profile=mid_size_tech_company(50), seed=42)
        people1 = GeneratorRegistry.get(EntityType.PERSON)().generate(10, ctx1)

        ctx2 = GenerationContext(profile=mid_size_tech_company(50), seed=42)
        people2 = GeneratorRegistry.get(EntityType.PERSON)().generate(10, ctx2)

        assert [p.name for p in people1] == [p.name for p in people2]

    def test_all_generators_registered(self):
        expected = {
            EntityType.PERSON,
            EntityType.DEPARTMENT,
            EntityType.ROLE,
            EntityType.SYSTEM,
            EntityType.NETWORK,
            EntityType.DATA_ASSET,
            EntityType.POLICY,
            EntityType.VENDOR,
            EntityType.LOCATION,
            EntityType.VULNERABILITY,
            EntityType.THREAT_ACTOR,
            EntityType.INCIDENT,
        }
        registered = set(GeneratorRegistry.all().keys())
        assert expected.issubset(registered)
