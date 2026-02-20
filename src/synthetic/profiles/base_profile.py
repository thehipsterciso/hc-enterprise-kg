"""Organizational profile definitions for synthetic data generation."""

from __future__ import annotations

from dataclasses import dataclass

from pydantic import BaseModel, Field


class DepartmentSpec(BaseModel):
    """Specification for a department in the org profile."""

    name: str
    headcount_fraction: float
    systems_count_range: tuple[int, int] = (2, 10)
    data_sensitivity: str = "medium"


class NetworkSpec(BaseModel):
    """Specification for network segments."""

    name: str
    cidr: str
    zone: str  # dmz, internal, restricted, guest


class OrgProfile(BaseModel):
    """Parameterized description of an organization.

    This drives the synthetic data generation. Different profiles
    produce different organizational structures.
    """

    name: str
    industry: str
    employee_count: int
    department_specs: list[DepartmentSpec]
    location_count: int = 1
    system_count_range: tuple[int, int] = (20, 100)
    network_specs: list[NetworkSpec] = Field(default_factory=list)
    vendor_count_range: tuple[int, int] = (5, 30)
    data_asset_count_range: tuple[int, int] = (10, 50)
    policy_count_range: tuple[int, int] = (5, 20)
    vulnerability_probability: float = 0.15
    threat_actor_count_range: tuple[int, int] = (2, 8)
    incident_count_range: tuple[int, int] = (0, 10)
    contractor_fraction: float = 0.1
    remote_fraction: float = 0.3
    simulation_days: int = 365
    daily_event_probability: float = 0.3

    # --- Enterprise ontology entity counts (L01-L11) ---
    regulation_count_range: tuple[int, int] = (3, 10)
    control_count_range: tuple[int, int] = (5, 20)
    risk_count_range: tuple[int, int] = (3, 12)
    threat_count_range: tuple[int, int] = (2, 8)
    integration_count_range: tuple[int, int] = (3, 15)
    data_domain_count_range: tuple[int, int] = (3, 8)
    data_flow_count_range: tuple[int, int] = (4, 15)
    org_unit_count_range: tuple[int, int] = (3, 10)
    capability_count_range: tuple[int, int] = (5, 15)
    site_count_range: tuple[int, int] = (2, 8)
    geography_count_range: tuple[int, int] = (2, 6)
    jurisdiction_count_range: tuple[int, int] = (2, 6)
    product_portfolio_count_range: tuple[int, int] = (1, 4)
    product_count_range: tuple[int, int] = (3, 12)
    market_segment_count_range: tuple[int, int] = (2, 6)
    customer_count_range: tuple[int, int] = (5, 20)
    contract_count_range: tuple[int, int] = (5, 20)
    initiative_count_range: tuple[int, int] = (3, 10)


# ---------------------------------------------------------------------------
# Industry-aware scaling
# ---------------------------------------------------------------------------


@dataclass
class ScalingCoefficients:
    """Industry-specific ratios: employees-per-entity.

    Lower coefficient = more entities per employee (denser infrastructure).
    """

    systems: float = 12
    vendors: float = 50
    data_assets: float = 20
    policies: float = 80
    controls: float = 50
    risks: float = 80
    threats: float = 200
    integrations: float = 40
    data_domains: float = 500
    data_flows: float = 30
    org_units: float = 150
    capabilities: float = 100
    sites: float = 500
    geographies: float = 1000
    jurisdictions: float = 1000
    product_portfolios: float = 2000
    products: float = 200
    market_segments: float = 1000
    customers: float = 100
    contracts: float = 80
    initiatives: float = 200
    threat_actors: float = 250
    incidents: float = 200


INDUSTRY_COEFFICIENTS: dict[str, ScalingCoefficients] = {
    "technology": ScalingCoefficients(
        systems=8,
        vendors=40,
        data_assets=15,
        policies=100,
        controls=50,
        risks=80,
        threats=200,
        integrations=30,
        data_domains=400,
        data_flows=25,
        org_units=150,
        capabilities=100,
        sites=500,
        geographies=1000,
        jurisdictions=1000,
        product_portfolios=2000,
        products=200,
        market_segments=1000,
        customers=100,
        contracts=60,
        initiatives=200,
        threat_actors=250,
        incidents=200,
    ),
    "financial_services": ScalingCoefficients(
        systems=12,
        vendors=35,
        data_assets=10,
        policies=40,
        controls=20,
        risks=30,
        threats=150,
        integrations=40,
        data_domains=300,
        data_flows=20,
        org_units=100,
        capabilities=80,
        sites=400,
        geographies=800,
        jurisdictions=600,
        product_portfolios=1500,
        products=150,
        market_segments=800,
        customers=50,
        contracts=40,
        initiatives=150,
        threat_actors=200,
        incidents=150,
    ),
    "healthcare": ScalingCoefficients(
        systems=15,
        vendors=50,
        data_assets=5,
        policies=50,
        controls=25,
        risks=40,
        threats=200,
        integrations=35,
        data_domains=200,
        data_flows=15,
        org_units=120,
        capabilities=100,
        sites=300,
        geographies=800,
        jurisdictions=600,
        product_portfolios=2000,
        products=200,
        market_segments=1000,
        customers=80,
        contracts=50,
        initiatives=200,
        threat_actors=300,
        incidents=100,
    ),
}


def _size_tier_multiplier(employee_count: int) -> float:
    """Organizational maturity multiplier based on size tier.

    Startups share systems and have informal controls.
    Large enterprises have complex hierarchies and regulatory burden.
    """
    if employee_count < 250:
        return 0.7
    if employee_count < 2000:
        return 1.0
    if employee_count < 10000:
        return 1.2
    return 1.4


def scaled_range(
    employee_count: int,
    coefficient: float,
    floor: int,
    ceiling: int,
) -> tuple[int, int]:
    """Compute (low, high) entity count range scaled by industry and size.

    Args:
        employee_count: Number of employees in the org.
        coefficient: Employees-per-entity ratio from ScalingCoefficients.
        floor: Minimum count regardless of org size.
        ceiling: Maximum count (hard cap).
    """
    tier = _size_tier_multiplier(employee_count)
    base = max(floor, int((employee_count / coefficient) * tier))
    low = min(ceiling - 1, max(floor, int(base * 0.8)))
    high = min(ceiling, max(low + 1, int(base * 1.2)))
    return (low, high)
