"""Generator for Role entities with seniority-level scaling."""

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
        "System Administrator",
        "Network Engineer",
        "Help Desk Analyst",
        "DBA",
        "Cloud Engineer",
    ],
    "Technology": ["Software Engineer", "DevOps Engineer", "Cloud Architect", "Data Engineer"],
    "Security": ["Security Analyst", "Security Engineer", "SOC Analyst", "CISO"],
    "Information Security": [
        "Security Analyst",
        "Security Engineer",
        "SOC Analyst",
        "Threat Hunter",
        "CISO",
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
    "CISO": [
        "admin:systems",
        "admin:users",
        "read:confidential",
        "write:confidential",
        "approve:changes",
        "manage:budgets",
    ],
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

# Keywords indicating a role should NOT get seniority-level expansion
_SENIORITY_EXEMPT_KEYWORDS = frozenset(
    [
        "manager",
        "director",
        "vp",
        "chief",
        "ceo",
        "cto",
        "cfo",
        "coo",
        "cio",
        "ciso",
        "lead",
        "head",
        "principal",
        "senior",
        "junior",
        "staff",
        "recruiter",
        "paralegal",
        "officer",
    ]
)


def _should_expand_seniority(role_name: str) -> bool:
    """Check if a role name is eligible for seniority-level expansion."""
    return not any(kw in role_name.lower() for kw in _SENIORITY_EXEMPT_KEYWORDS)


def _seniority_variants(role_name: str, headcount: int) -> list[tuple[str, str | None]]:
    """Generate (variant_name, base_name) tuples for seniority expansion.

    Returns the base role plus seniority variants based on department headcount.
    base_name is None for the original role, or the original name for variants
    (used for permission lookup).
    """
    if not _should_expand_seniority(role_name):
        return [(role_name, None)]

    variants: list[tuple[str, str | None]] = [(role_name, None)]
    if headcount >= 100:
        variants.append((f"Senior {role_name}", role_name))
    if headcount >= 300:
        variants.insert(0, (f"Junior {role_name}", role_name))
    if headcount >= 500:
        variants.append((f"Staff {role_name}", role_name))
    return variants


def _get_parent_department_name(dept_name: str) -> str:
    """Extract parent department name for sub-departments.

    'Engineering - Platform Engineering' → 'Engineering'
    'Engineering' → 'Engineering'
    """
    if " - " in dept_name:
        return dept_name.split(" - ", 1)[0]
    return dept_name


@GeneratorRegistry.register
class RoleGenerator(AbstractGenerator):
    """Generates Role entities with name-correlated permissions.

    For sub-departments (name contains ' - '), looks up role templates
    by the parent department name. Expands roles with seniority variants
    when department headcount is large enough.
    """

    GENERATES = EntityType.ROLE

    def generate(self, count: int, context: GenerationContext) -> list[Role]:
        departments = context.get_entities(EntityType.DEPARTMENT)
        roles: list[Role] = []

        for dept in departments:
            # Skip parent departments that have sub-departments
            has_children = any(
                getattr(d, "parent_department_id", None) == dept.id for d in departments
            )
            if has_children:
                continue

            parent_name = _get_parent_department_name(dept.name)
            dept_roles = ROLE_TEMPLATES.get(parent_name, ["Analyst", "Manager", "Director"])
            dept_headcount = getattr(dept, "headcount", 0)

            for role_name in dept_roles:
                for variant_name, base_name in _seniority_variants(role_name, dept_headcount):
                    is_privileged = any(
                        kw in variant_name.lower()
                        for kw in [
                            "admin",
                            "lead",
                            "manager",
                            "director",
                            "ciso",
                            "cto",
                            "ceo",
                            "cfo",
                            "coo",
                            "cio",
                            "staff",
                            "senior",
                        ]
                    )
                    access = "privileged" if is_privileged else random.choice(ACCESS_LEVELS[:2])

                    # Look up permissions by exact name, then base name, then default
                    permissions = ROLE_PERMISSIONS.get(variant_name)
                    if not permissions and base_name:
                        permissions = ROLE_PERMISSIONS.get(base_name)
                    if not permissions:
                        permissions = DEFAULT_PERMISSIONS

                    role = Role(
                        name=variant_name,
                        description=f"{variant_name} role in {dept.name}",
                        department_id=dept.id,
                        access_level=access,
                        is_privileged=is_privileged,
                        permissions=list(permissions),
                        tags=[dept.name.lower().replace(" ", "_")],
                    )
                    roles.append(role)

        context.store(EntityType.ROLE, roles)
        return roles
