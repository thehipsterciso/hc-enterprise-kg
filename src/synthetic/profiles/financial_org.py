"""Pre-built profile for a financial services organization."""

from __future__ import annotations

from synthetic.profiles.base_profile import (
    INDUSTRY_COEFFICIENTS,
    DepartmentSpec,
    NetworkSpec,
    OrgProfile,
    scaled_range,
)


def financial_org(employee_count: int = 1000) -> OrgProfile:
    """Create an org profile for a financial services organization."""
    c = INDUSTRY_COEFFICIENTS["financial_services"]
    s = lambda coeff, floor, ceiling: scaled_range(employee_count, coeff, floor, ceiling)  # noqa: E731

    return OrgProfile(
        name="Atlas Financial Group",
        industry="financial_services",
        employee_count=employee_count,
        department_specs=[
            DepartmentSpec(
                name="Trading",
                headcount_fraction=0.15,
                systems_count_range=(10, 30),
                data_sensitivity="critical",
            ),
            DepartmentSpec(
                name="Risk Management",
                headcount_fraction=0.10,
                systems_count_range=(8, 20),
                data_sensitivity="critical",
            ),
            DepartmentSpec(
                name="Technology",
                headcount_fraction=0.20,
                systems_count_range=(20, 50),
                data_sensitivity="high",
            ),
            DepartmentSpec(
                name="Compliance & Legal",
                headcount_fraction=0.08,
                systems_count_range=(5, 15),
                data_sensitivity="critical",
            ),
            DepartmentSpec(
                name="Operations",
                headcount_fraction=0.12,
                systems_count_range=(10, 25),
                data_sensitivity="high",
            ),
            DepartmentSpec(
                name="Client Services",
                headcount_fraction=0.10,
                systems_count_range=(5, 15),
                data_sensitivity="high",
            ),
            DepartmentSpec(
                name="Finance & Accounting",
                headcount_fraction=0.06,
                systems_count_range=(5, 12),
                data_sensitivity="critical",
            ),
            DepartmentSpec(
                name="HR",
                headcount_fraction=0.04,
                data_sensitivity="high",
            ),
            DepartmentSpec(
                name="Information Security",
                headcount_fraction=0.08,
                systems_count_range=(10, 25),
                data_sensitivity="critical",
            ),
            DepartmentSpec(
                name="Executive",
                headcount_fraction=0.03,
                data_sensitivity="critical",
            ),
            DepartmentSpec(
                name="Internal Audit",
                headcount_fraction=0.04,
                systems_count_range=(3, 8),
                data_sensitivity="critical",
            ),
        ],
        location_count=max(1, min(100, employee_count // 300 + 1)),
        system_count_range=s(c.systems, 30, 3500),
        network_specs=[
            NetworkSpec(name="Trading Floor", cidr="10.0.0.0/24", zone="restricted"),
            NetworkSpec(name="Corporate", cidr="10.1.0.0/16", zone="internal"),
            NetworkSpec(name="DMZ", cidr="172.16.0.0/24", zone="dmz"),
            NetworkSpec(name="DR Site", cidr="10.2.0.0/16", zone="internal"),
            NetworkSpec(name="Guest", cidr="192.168.0.0/24", zone="guest"),
        ],
        vendor_count_range=s(c.vendors, 10, 2500),
        data_asset_count_range=s(c.data_assets, 15, 4000),
        policy_count_range=s(c.policies, 10, 500),
        vulnerability_probability=0.12,
        threat_actor_count_range=s(c.threat_actors, 3, 50),
        incident_count_range=s(c.incidents, 1, 100),
        contractor_fraction=0.20,
        remote_fraction=0.25,
        # Enterprise ontology — financial-heavy compliance & risk
        regulation_count_range=s(80, 5, 60),
        control_count_range=s(c.controls, 8, 1000),
        risk_count_range=s(c.risks, 5, 500),
        threat_count_range=s(c.threats, 3, 100),
        integration_count_range=s(c.integrations, 5, 800),
        data_domain_count_range=s(c.data_domains, 3, 50),
        data_flow_count_range=s(c.data_flows, 5, 2000),
        org_unit_count_range=s(c.org_units, 4, 250),
        capability_count_range=s(c.capabilities, 5, 150),
        site_count_range=s(c.sites, 2, 100),
        geography_count_range=s(c.geographies, 2, 25),
        jurisdiction_count_range=s(c.jurisdictions, 3, 30),
        product_portfolio_count_range=s(c.product_portfolios, 1, 15),
        product_count_range=s(c.products, 4, 200),
        market_segment_count_range=s(c.market_segments, 2, 25),
        customer_count_range=s(c.customers, 10, 8000),
        contract_count_range=s(c.contracts, 8, 8000),
        initiative_count_range=s(c.initiatives, 4, 200),
    )
