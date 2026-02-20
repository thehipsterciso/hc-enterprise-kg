"""Pre-built profile for a financial services organization."""

from __future__ import annotations

from synthetic.profiles.base_profile import (
    DepartmentSpec,
    NetworkSpec,
    OrgProfile,
)


def financial_org(employee_count: int = 1000) -> OrgProfile:
    """Create an org profile for a financial services organization."""
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
        location_count=4,
        system_count_range=(60, 200),
        network_specs=[
            NetworkSpec(name="Trading Floor", cidr="10.0.0.0/24", zone="restricted"),
            NetworkSpec(name="Corporate", cidr="10.1.0.0/16", zone="internal"),
            NetworkSpec(name="DMZ", cidr="172.16.0.0/24", zone="dmz"),
            NetworkSpec(name="DR Site", cidr="10.2.0.0/16", zone="internal"),
            NetworkSpec(name="Guest", cidr="192.168.0.0/24", zone="guest"),
        ],
        vendor_count_range=(15, 50),
        data_asset_count_range=(25, 80),
        policy_count_range=(20, 50),
        vulnerability_probability=0.12,
        threat_actor_count_range=(5, 15),
        incident_count_range=(1, 12),
        contractor_fraction=0.20,
        remote_fraction=0.25,
        # Enterprise ontology — financial-heavy compliance & risk
        regulation_count_range=(6, 18),
        control_count_range=(12, 40),
        risk_count_range=(6, 20),
        threat_count_range=(4, 12),
        integration_count_range=(6, 22),
        data_domain_count_range=(4, 10),
        data_flow_count_range=(6, 22),
        org_unit_count_range=(5, 15),
        capability_count_range=(8, 22),
        site_count_range=(3, 8),
        geography_count_range=(3, 8),
        jurisdiction_count_range=(4, 10),
        product_portfolio_count_range=(2, 6),
        product_count_range=(6, 25),
        market_segment_count_range=(3, 8),
        customer_count_range=(15, 50),
        contract_count_range=(12, 40),
        initiative_count_range=(5, 15),
    )
