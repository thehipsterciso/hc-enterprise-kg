"""Generator for Network entities."""

from __future__ import annotations

from domain.base import EntityType
from domain.entities.network import Network
from synthetic.base import AbstractGenerator, GenerationContext, GeneratorRegistry


@GeneratorRegistry.register
class NetworkGenerator(AbstractGenerator):
    """Generates Network entities from the org profile network specs."""

    GENERATES = EntityType.NETWORK

    def generate(self, count: int, context: GenerationContext) -> list[Network]:
        faker = context.faker
        profile = context.profile
        networks: list[Network] = []

        for spec in profile.network_specs:
            cidr_parts = spec.cidr.split("/")
            base_ip = cidr_parts[0]
            gateway = base_ip.rsplit(".", 1)[0] + ".1"

            network = Network(
                name=spec.name,
                description=f"{spec.name} network ({spec.zone} zone)",
                cidr=spec.cidr,
                zone=spec.zone,
                vlan_id=faker.random_int(min=10, max=4094),
                gateway=gateway,
                dns_servers=[faker.ipv4_private(), faker.ipv4_private()],
                is_monitored=spec.zone != "guest",
                tags=[spec.zone],
            )
            networks.append(network)

        context.store(EntityType.NETWORK, networks)
        return networks
