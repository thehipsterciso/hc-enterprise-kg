"""Pre-built profile for a mid-size technology company."""

from __future__ import annotations

from synthetic.profiles.base_profile import (
    DepartmentSpec,
    NetworkSpec,
    OrgProfile,
)


def mid_size_tech_company(employee_count: int = 500) -> OrgProfile:
    """Create an org profile for a mid-size technology company."""
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
        location_count=3,
        system_count_range=(40, 120),
        network_specs=[
            NetworkSpec(name="Corporate", cidr="10.0.0.0/16", zone="internal"),
            NetworkSpec(name="DMZ", cidr="172.16.0.0/24", zone="dmz"),
            NetworkSpec(name="Dev/Staging", cidr="10.1.0.0/16", zone="internal"),
            NetworkSpec(name="Guest WiFi", cidr="192.168.0.0/24", zone="guest"),
        ],
        vendor_count_range=(10, 40),
        data_asset_count_range=(15, 60),
        policy_count_range=(8, 25),
        vulnerability_probability=0.20,
        threat_actor_count_range=(3, 10),
        incident_count_range=(1, 8),
        # Enterprise ontology
        regulation_count_range=(3, 8),
        control_count_range=(8, 25),
        risk_count_range=(4, 12),
        threat_count_range=(3, 8),
        integration_count_range=(5, 20),
        data_domain_count_range=(3, 8),
        data_flow_count_range=(5, 18),
        org_unit_count_range=(4, 12),
        capability_count_range=(6, 18),
        site_count_range=(2, 6),
        geography_count_range=(2, 5),
        jurisdiction_count_range=(2, 5),
        product_portfolio_count_range=(1, 3),
        product_count_range=(4, 15),
        market_segment_count_range=(2, 6),
        customer_count_range=(8, 30),
        contract_count_range=(8, 30),
        initiative_count_range=(4, 12),
    )
