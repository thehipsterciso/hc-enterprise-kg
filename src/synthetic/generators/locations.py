"""Generator for Location entities."""

from __future__ import annotations

import random

from domain.base import EntityType
from domain.entities.location import Location
from synthetic.base import AbstractGenerator, GenerationContext, GeneratorRegistry

LOCATION_TYPES = ["headquarters", "office", "data_center", "warehouse", "remote_hub"]
SECURITY_LEVELS = ["standard", "enhanced", "restricted"]


@GeneratorRegistry.register
class LocationGenerator(AbstractGenerator):
    """Generates Location entities."""

    GENERATES = EntityType.LOCATION

    def generate(self, count: int, context: GenerationContext) -> list[Location]:
        faker = context.faker
        locations: list[Location] = []

        for i in range(count):
            loc_type = (
                LOCATION_TYPES[i] if i < len(LOCATION_TYPES) else random.choice(LOCATION_TYPES)
            )

            location = Location(
                name=f"{faker.city()} {loc_type.replace('_', ' ').title()}",
                description=f"{loc_type.replace('_', ' ').title()} facility",
                address=faker.street_address(),
                city=faker.city(),
                state=faker.state_abbr(),
                country=faker.country_code(),
                zip_code=faker.zipcode(),
                location_type=loc_type,
                capacity=random.randint(50, 5000),
                is_primary=i == 0,
                security_level=random.choice(SECURITY_LEVELS),
                has_physical_security=loc_type != "remote_hub",
                tags=[loc_type],
            )
            locations.append(location)

        context.store(EntityType.LOCATION, locations)
        return locations
