"""Organizational profile definitions for synthetic data generation."""

from __future__ import annotations

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
