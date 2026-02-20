"""Generator for Department entities."""

from __future__ import annotations

import random

from domain.base import EntityType
from domain.entities.department import Department
from synthetic.base import AbstractGenerator, GenerationContext, GeneratorRegistry


@GeneratorRegistry.register
class DepartmentGenerator(AbstractGenerator):
    """Generates Department entities from the org profile department specs."""

    GENERATES = EntityType.DEPARTMENT

    def generate(self, count: int, context: GenerationContext) -> list[Department]:
        profile = context.profile
        departments: list[Department] = []

        for spec in profile.department_specs:
            headcount = int(profile.employee_count * spec.headcount_fraction)
            # Budget correlated with headcount: ~$80k-$150k per head
            budget = round(headcount * random.uniform(80_000, 150_000), 2)

            dept = Department(
                name=spec.name,
                description=f"{spec.name} department at {profile.name}",
                code=spec.name.upper().replace(" ", "_")[:8],
                headcount=headcount,
                tags=[spec.data_sensitivity],
                metadata={"data_sensitivity": spec.data_sensitivity},
                budget=budget,
            )
            departments.append(dept)

        context.store(EntityType.DEPARTMENT, departments)
        return departments
