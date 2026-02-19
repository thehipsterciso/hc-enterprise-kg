"""Generator for Person entities."""

from __future__ import annotations

from domain.base import EntityType
from domain.entities.person import Person
from synthetic.base import AbstractGenerator, GenerationContext, GeneratorRegistry


@GeneratorRegistry.register
class PeopleGenerator(AbstractGenerator):
    """Generates Person entities based on the org profile."""

    GENERATES = EntityType.PERSON

    def generate(self, count: int, context: GenerationContext) -> list[Person]:
        faker = context.faker
        profile = context.profile
        people: list[Person] = []
        domain = profile.name.lower().replace(" ", "") + ".com"

        clearance_levels = ["none", "basic", "elevated", "privileged", "admin"]

        for i in range(count):
            first = faker.first_name()
            last = faker.last_name()
            is_contractor = (i / max(count, 1)) > (1 - profile.contractor_fraction)

            person = Person(
                first_name=first,
                last_name=last,
                name=f"{first} {last}",
                email=f"{first.lower()}.{last.lower()}@{domain}",
                title=faker.job(),
                employee_id=f"EMP-{faker.unique.random_number(digits=6):06d}",
                clearance_level=faker.random_element(clearance_levels),
                is_active=faker.boolean(chance_of_getting_true=95),
                hire_date=str(faker.date_between(start_date="-10y", end_date="today")),
                phone=faker.phone_number(),
                tags=["contractor"] if is_contractor else ["employee"],
            )
            people.append(person)

        context.store(EntityType.PERSON, people)
        return people
