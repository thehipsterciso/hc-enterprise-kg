"""Organizational profiles for synthetic data generation."""

from synthetic.profiles.base_profile import DepartmentSpec, NetworkSpec, OrgProfile
from synthetic.profiles.financial_org import financial_org
from synthetic.profiles.healthcare_org import healthcare_org
from synthetic.profiles.tech_company import mid_size_tech_company

__all__ = [
    "DepartmentSpec",
    "NetworkSpec",
    "OrgProfile",
    "financial_org",
    "healthcare_org",
    "mid_size_tech_company",
]
