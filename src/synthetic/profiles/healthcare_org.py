"""Pre-built profile for a healthcare organization."""

from __future__ import annotations

from synthetic.profiles.base_profile import (
    DepartmentSpec,
    NetworkSpec,
    OrgProfile,
)


def healthcare_org(employee_count: int = 2000) -> OrgProfile:
    """Create an org profile for a healthcare organization."""
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
        location_count=5,
        system_count_range=(80, 250),
        network_specs=[
            NetworkSpec(name="Clinical Network", cidr="10.0.0.0/16", zone="restricted"),
            NetworkSpec(name="Administrative", cidr="10.1.0.0/16", zone="internal"),
            NetworkSpec(name="Medical Devices", cidr="10.2.0.0/24", zone="restricted"),
            NetworkSpec(name="Guest WiFi", cidr="192.168.0.0/24", zone="guest"),
            NetworkSpec(name="DMZ", cidr="172.16.0.0/24", zone="dmz"),
        ],
        vendor_count_range=(20, 60),
        data_asset_count_range=(30, 100),
        policy_count_range=(15, 40),
        vulnerability_probability=0.18,
        threat_actor_count_range=(3, 12),
        incident_count_range=(2, 15),
        contractor_fraction=0.15,
        remote_fraction=0.10,
    )
