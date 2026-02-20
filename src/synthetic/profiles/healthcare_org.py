"""Pre-built profile for a healthcare organization."""

from __future__ import annotations

from synthetic.profiles.base_profile import (
    INDUSTRY_COEFFICIENTS,
    DepartmentSpec,
    NetworkSpec,
    OrgProfile,
    scaled_range,
)


def healthcare_org(employee_count: int = 2000) -> OrgProfile:
    """Create an org profile for a healthcare organization."""
    c = INDUSTRY_COEFFICIENTS["healthcare"]
    s = lambda coeff, floor, ceiling: scaled_range(employee_count, coeff, floor, ceiling)  # noqa: E731

    return OrgProfile(
        name="MedCare Health Systems",
        industry="healthcare",
        employee_count=employee_count,
        department_specs=[
            DepartmentSpec(
                name="Clinical Operations",
                headcount_fraction=0.40,
                systems_count_range=(20, 50),
                data_sensitivity="critical",
            ),
            DepartmentSpec(
                name="Nursing",
                headcount_fraction=0.15,
                systems_count_range=(5, 15),
                data_sensitivity="critical",
            ),
            DepartmentSpec(
                name="Administration",
                headcount_fraction=0.08,
                systems_count_range=(5, 10),
            ),
            DepartmentSpec(
                name="IT",
                headcount_fraction=0.06,
                systems_count_range=(15, 40),
                data_sensitivity="high",
            ),
            DepartmentSpec(
                name="Finance & Billing",
                headcount_fraction=0.07,
                systems_count_range=(8, 20),
                data_sensitivity="critical",
            ),
            DepartmentSpec(
                name="Pharmacy",
                headcount_fraction=0.05,
                systems_count_range=(5, 12),
                data_sensitivity="critical",
            ),
            DepartmentSpec(
                name="Research",
                headcount_fraction=0.06,
                systems_count_range=(8, 20),
                data_sensitivity="high",
            ),
            DepartmentSpec(
                name="Compliance",
                headcount_fraction=0.04,
                systems_count_range=(3, 8),
                data_sensitivity="critical",
            ),
            DepartmentSpec(
                name="HR",
                headcount_fraction=0.04,
                data_sensitivity="high",
            ),
            DepartmentSpec(
                name="Facilities",
                headcount_fraction=0.05,
                systems_count_range=(3, 8),
            ),
        ],
        location_count=max(1, min(30, employee_count // 500 + 1)),
        system_count_range=s(c.systems, 30, 2000),
        network_specs=[
            NetworkSpec(name="Clinical Network", cidr="10.0.0.0/16", zone="restricted"),
            NetworkSpec(name="Administrative", cidr="10.1.0.0/16", zone="internal"),
            NetworkSpec(name="Medical Devices", cidr="10.2.0.0/24", zone="restricted"),
            NetworkSpec(name="Guest WiFi", cidr="192.168.0.0/24", zone="guest"),
            NetworkSpec(name="DMZ", cidr="172.16.0.0/24", zone="dmz"),
        ],
        vendor_count_range=s(c.vendors, 10, 500),
        data_asset_count_range=s(c.data_assets, 20, 3000),
        policy_count_range=s(c.policies, 8, 250),
        vulnerability_probability=0.18,
        threat_actor_count_range=s(c.threat_actors, 2, 40),
        incident_count_range=s(c.incidents, 1, 120),
        contractor_fraction=0.15,
        remote_fraction=0.10,
        # Enterprise ontology — healthcare-heavy compliance
        regulation_count_range=s(80, 4, 35),
        control_count_range=s(c.controls, 8, 400),
        risk_count_range=s(c.risks, 4, 180),
        threat_count_range=s(c.threats, 2, 45),
        integration_count_range=s(c.integrations, 5, 300),
        data_domain_count_range=s(c.data_domains, 3, 25),
        data_flow_count_range=s(c.data_flows, 5, 700),
        org_unit_count_range=s(c.org_units, 4, 100),
        capability_count_range=s(c.capabilities, 5, 55),
        site_count_range=s(c.sites, 2, 35),
        geography_count_range=s(c.geographies, 2, 15),
        jurisdiction_count_range=s(c.jurisdictions, 2, 15),
        product_portfolio_count_range=s(c.product_portfolios, 1, 10),
        product_count_range=s(c.products, 4, 90),
        market_segment_count_range=s(c.market_segments, 2, 15),
        customer_count_range=s(c.customers, 8, 250),
        contract_count_range=s(c.contracts, 8, 300),
        initiative_count_range=s(c.initiatives, 4, 70),
    )
