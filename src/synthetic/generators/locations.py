"""Generator for Location entities."""

from __future__ import annotations

import random

from domain.base import EntityType
from domain.entities.location import Location
from synthetic.base import AbstractGenerator, GenerationContext, GeneratorRegistry

LOCATION_TYPES = ["headquarters", "office", "data_center", "warehouse", "remote_hub"]

# Type → correlated security level and capacity range
LOCATION_PROFILES: dict[str, dict] = {
    "headquarters": {
        "security": ["enhanced", "restricted"],
        "capacity": (200, 5000),
    },
    "office": {
        "security": ["standard", "enhanced"],
        "capacity": (50, 1500),
    },
    "data_center": {
        "security": ["restricted"],
        "capacity": (20, 200),
    },
    "warehouse": {
        "security": ["standard", "enhanced"],
        "capacity": (30, 500),
    },
    "remote_hub": {
        "security": ["standard"],
        "capacity": (10, 100),
    },
}


@GeneratorRegistry.register
class LocationGenerator(AbstractGenerator):
    """Generates Location entities with type-correlated attributes."""

    GENERATES = EntityType.LOCATION

    def generate(self, count: int, context: GenerationContext) -> list[Location]:
        faker = context.faker
        locations: list[Location] = []

        for i in range(count):
            loc_type = (
                LOCATION_TYPES[i] if i < len(LOCATION_TYPES) else random.choice(LOCATION_TYPES)
            )
            lp = LOCATION_PROFILES[loc_type]

            # Use same city for name and city field
            city = faker.city()

            location = Location(
                name=f"{city} {loc_type.replace('_', ' ').title()}",
                description=f"{loc_type.replace('_', ' ').title()} facility in {city}",
                address=faker.street_address(),
                city=city,
                state=faker.state_abbr(),
                country=faker.country_code(),
                zip_code=faker.zipcode(),
                location_type=loc_type,
                capacity=random.randint(*lp["capacity"]),
                is_primary=i == 0,
                security_level=random.choice(lp["security"]),
                has_physical_security=loc_type != "remote_hub",
                tags=[loc_type],
            )
            locations.append(location)

        context.store(EntityType.LOCATION, locations)
        return locations
