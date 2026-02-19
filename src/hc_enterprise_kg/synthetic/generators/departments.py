"""Generator for Department entities."""

from __future__ import annotations

from hc_enterprise_kg.domain.base import EntityType
from hc_enterprise_kg.domain.entities.department import Department
from hc_enterprise_kg.synthetic.base import AbstractGenerator, GenerationContext, GeneratorRegistry


@GeneratorRegistry.register
class DepartmentGenerator(AbstractGenerator):
    """Generates Department entities from the org profile department specs."""

    GENERATES = EntityType.DEPARTMENT

    def generate(self, count: int, context: GenerationContext) -> list[Department]:
        faker = context.faker
        profile = context.profile
        departments: list[Department] = []

        for spec in profile.department_specs:
            dept = Department(
                name=spec.name,
                description=f"{spec.name} department at {profile.name}",
                code=spec.name.upper().replace(" ", "_")[:8],
                headcount=int(profile.employee_count * spec.headcount_fraction),
                tags=[spec.data_sensitivity],
                metadata={"data_sensitivity": spec.data_sensitivity},
                budget=round(faker.pyfloat(min_value=100000, max_value=10000000), 2),
            )
            departments.append(dept)

        context.store(EntityType.DEPARTMENT, departments)
        return departments
