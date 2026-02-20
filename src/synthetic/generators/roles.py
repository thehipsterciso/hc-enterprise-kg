"""Generator for Role entities."""

from __future__ import annotations

import random

from domain.base import EntityType
from domain.entities.role import Role
from synthetic.base import AbstractGenerator, GenerationContext, GeneratorRegistry

ROLE_TEMPLATES = {
    "Engineering": [
        "Software Engineer",
        "Senior Engineer",
        "Tech Lead",
        "DevOps Engineer",
        "QA Engineer",
    ],
    "Product": ["Product Manager", "Product Analyst", "UX Designer"],
    "Sales": ["Account Executive", "Sales Manager", "SDR"],
    "Marketing": ["Marketing Manager", "Content Strategist", "Growth Analyst"],
    "HR": ["HR Generalist", "Recruiter", "HR Manager"],
    "Finance": ["Financial Analyst", "Controller", "Accountant"],
    "Finance & Billing": ["Financial Analyst", "Billing Specialist", "Revenue Analyst"],
    "Finance & Accounting": ["Financial Analyst", "Controller", "Senior Accountant"],
    "Legal": ["Legal Counsel", "Paralegal", "Compliance Analyst"],
    "Compliance & Legal": ["Compliance Officer", "Legal Counsel", "Regulatory Analyst"],
    "IT Operations": ["System Administrator", "Network Engineer", "Help Desk Analyst", "DBA"],
    "IT": [
        "System Administrator", "Network Engineer", "Help Desk Analyst", "DBA", "Cloud Engineer",
    ],
    "Technology": ["Software Engineer", "DevOps Engineer", "Cloud Architect", "Data Engineer"],
    "Security": ["Security Analyst", "Security Engineer", "SOC Analyst", "CISO"],
    "Information Security": [
        "Security Analyst", "Security Engineer", "SOC Analyst", "Threat Hunter", "CISO",
    ],
    "Executive": ["CEO", "CTO", "CFO", "COO"],
    "Clinical Operations": ["Clinical Director", "Care Coordinator", "Medical Officer"],
    "Nursing": ["Charge Nurse", "Nurse Manager", "Clinical Nurse Specialist"],
    "Administration": ["Office Manager", "Administrative Director"],
    "Pharmacy": ["Pharmacist", "Pharmacy Manager"],
    "Research": ["Research Scientist", "Principal Investigator"],
    "Compliance": ["Compliance Officer", "Privacy Officer", "Regulatory Analyst"],
    "Facilities": ["Facilities Manager", "Safety Officer"],
    "Trading": ["Trader", "Trading Desk Manager", "Quantitative Analyst"],
    "Risk Management": ["Risk Analyst", "Risk Manager", "Credit Risk Officer"],
    "Operations": ["Operations Analyst", "Operations Manager"],
    "Client Services": ["Client Manager", "Relationship Manager"],
    "Internal Audit": ["Internal Auditor", "Audit Manager"],
}

ACCESS_LEVELS = ["standard", "elevated", "privileged", "admin"]

# Role-name → correlated permissions
ROLE_PERMISSIONS: dict[str, list[str]] = {
    # Engineering / Tech
    "Software Engineer": ["read:internal", "write:internal", "deploy:production", "access:vpn"],
    "Senior Engineer": ["read:internal", "write:internal", "deploy:production", "access:vpn"],
    "Tech Lead": ["read:internal", "write:internal", "deploy:production", "approve:changes"],
    "DevOps Engineer": ["admin:systems", "deploy:production", "read:internal", "write:internal"],
    "QA Engineer": ["read:internal", "write:internal", "access:vpn"],
    "Cloud Engineer": ["admin:systems", "deploy:production", "read:internal"],
    "Cloud Architect": ["admin:systems", "deploy:production", "approve:changes"],
    "Data Engineer": ["read:internal", "read:confidential", "write:internal"],
    # Security
    "Security Analyst": ["read:internal", "read:confidential", "access:vpn"],
    "Security Engineer": ["admin:systems", "read:confidential", "read:internal"],
    "SOC Analyst": ["read:internal", "read:confidential", "access:vpn"],
    "Threat Hunter": ["read:confidential", "read:internal", "access:vpn"],
    "Penetration Tester": ["admin:systems", "read:confidential", "access:vpn"],
    "CISO": ["admin:systems", "admin:users", "read:confidential", "write:confidential",
             "approve:changes", "manage:budgets"],
    # Executive
    "CEO": ["admin:users", "manage:budgets", "approve:changes", "read:confidential"],
    "CTO": ["admin:systems", "admin:users", "deploy:production", "approve:changes"],
    "CFO": ["manage:budgets", "read:confidential", "write:confidential", "approve:changes"],
    "COO": ["manage:budgets", "approve:changes", "read:confidential"],
    "CIO": ["admin:systems", "manage:budgets", "approve:changes"],
    # Management
    "HR Manager": ["admin:users", "read:confidential", "write:confidential"],
    "Sales Manager": ["read:internal", "manage:budgets"],
    "Marketing Manager": ["read:internal", "write:internal"],
    # Admin/IT
    "System Administrator": ["admin:systems", "read:internal", "deploy:production"],
    "Network Engineer": ["admin:systems", "read:internal"],
    "DBA": ["admin:systems", "read:confidential", "write:confidential"],
    "Help Desk Analyst": ["read:internal", "admin:users"],
}

DEFAULT_PERMISSIONS = ["read:internal", "access:vpn"]


@GeneratorRegistry.register
class RoleGenerator(AbstractGenerator):
    """Generates Role entities with name-correlated permissions."""

    GENERATES = EntityType.ROLE

    def generate(self, count: int, context: GenerationContext) -> list[Role]:
        departments = context.get_entities(EntityType.DEPARTMENT)
        roles: list[Role] = []

        for dept in departments:
            dept_roles = ROLE_TEMPLATES.get(dept.name, ["Analyst", "Manager", "Director"])
            for role_name in dept_roles:
                is_privileged = any(
                    kw in role_name.lower()
                    for kw in [
                        "admin", "lead", "manager", "director",
                        "ciso", "cto", "ceo", "cfo", "coo", "cio",
                    ]
                )
                access = "privileged" if is_privileged else random.choice(ACCESS_LEVELS[:2])

                # Use role-specific permissions when available
                permissions = ROLE_PERMISSIONS.get(role_name, DEFAULT_PERMISSIONS)

                role = Role(
                    name=role_name,
                    description=f"{role_name} role in {dept.name}",
                    department_id=dept.id,
                    access_level=access,
                    is_privileged=is_privileged,
                    permissions=list(permissions),
                    tags=[dept.name.lower().replace(" ", "_")],
                )
                roles.append(role)

        context.store(EntityType.ROLE, roles)
        return roles
