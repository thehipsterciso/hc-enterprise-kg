"""Pre-built profile for a mid-size technology company."""

from __future__ import annotations

from synthetic.profiles.base_profile import (
    INDUSTRY_COEFFICIENTS,
    DepartmentSpec,
    NetworkSpec,
    OrgProfile,
    scaled_range,
)


def mid_size_tech_company(employee_count: int = 500) -> OrgProfile:
    """Create an org profile for a mid-size technology company."""
    c = INDUSTRY_COEFFICIENTS["technology"]
    s = lambda coeff, floor, ceiling: scaled_range(employee_count, coeff, floor, ceiling)  # noqa: E731

    return OrgProfile(
        name="Acme Technologies",
        industry="technology",
        employee_count=employee_count,
        department_specs=[
            DepartmentSpec(
                name="Engineering",
                headcount_fraction=0.35,
                systems_count_range=(10, 30),
                data_sensitivity="high",
            ),
            DepartmentSpec(
                name="Product",
                headcount_fraction=0.10,
                systems_count_range=(3, 8),
            ),
            DepartmentSpec(
                name="Sales",
                headcount_fraction=0.15,
                systems_count_range=(5, 12),
            ),
            DepartmentSpec(
                name="Marketing",
                headcount_fraction=0.08,
                systems_count_range=(4, 10),
            ),
            DepartmentSpec(
                name="HR",
                headcount_fraction=0.05,
                data_sensitivity="critical",
            ),
            DepartmentSpec(
                name="Finance",
                headcount_fraction=0.05,
                data_sensitivity="critical",
            ),
            DepartmentSpec(
                name="Legal",
                headcount_fraction=0.03,
                data_sensitivity="high",
            ),
            DepartmentSpec(
                name="IT Operations",
                headcount_fraction=0.10,
                systems_count_range=(15, 40),
                data_sensitivity="high",
            ),
            DepartmentSpec(
                name="Security",
                headcount_fraction=0.05,
                systems_count_range=(5, 15),
                data_sensitivity="critical",
            ),
            DepartmentSpec(
                name="Executive",
                headcount_fraction=0.04,
                data_sensitivity="critical",
            ),
        ],
        location_count=max(1, min(30, employee_count // 800 + 1)),
        system_count_range=s(c.systems, 20, 2000),
        network_specs=[
            NetworkSpec(name="Corporate", cidr="10.0.0.0/16", zone="internal"),
            NetworkSpec(name="DMZ", cidr="172.16.0.0/24", zone="dmz"),
            NetworkSpec(name="Dev/Staging", cidr="10.1.0.0/16", zone="internal"),
            NetworkSpec(name="Guest WiFi", cidr="192.168.0.0/24", zone="guest"),
        ],
        vendor_count_range=s(c.vendors, 5, 500),
        data_asset_count_range=s(c.data_assets, 10, 1500),
        policy_count_range=s(c.policies, 5, 200),
        vulnerability_probability=0.20,
        threat_actor_count_range=s(c.threat_actors, 2, 50),
        incident_count_range=s(c.incidents, 1, 100),
        # Enterprise ontology
        regulation_count_range=s(100, 3, 30),
        control_count_range=s(c.controls, 5, 400),
        risk_count_range=s(c.risks, 3, 150),
        threat_count_range=s(c.threats, 2, 40),
        integration_count_range=s(c.integrations, 3, 300),
        data_domain_count_range=s(c.data_domains, 3, 20),
        data_flow_count_range=s(c.data_flows, 4, 500),
        org_unit_count_range=s(c.org_units, 3, 80),
        capability_count_range=s(c.capabilities, 5, 50),
        site_count_range=s(c.sites, 2, 30),
        geography_count_range=s(c.geographies, 2, 15),
        jurisdiction_count_range=s(c.jurisdictions, 2, 15),
        product_portfolio_count_range=s(c.product_portfolios, 1, 10),
        product_count_range=s(c.products, 3, 80),
        market_segment_count_range=s(c.market_segments, 2, 15),
        customer_count_range=s(c.customers, 5, 200),
        contract_count_range=s(c.contracts, 5, 250),
        initiative_count_range=s(c.initiatives, 3, 60),
    )
