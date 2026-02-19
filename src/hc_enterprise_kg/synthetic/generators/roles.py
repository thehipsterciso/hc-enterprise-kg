"""Generator for Role entities."""

from __future__ import annotations

import random

from hc_enterprise_kg.domain.base import EntityType
from hc_enterprise_kg.domain.entities.role import Role
from hc_enterprise_kg.synthetic.base import AbstractGenerator, GenerationContext, GeneratorRegistry

ROLE_TEMPLATES = {
    "Engineering": ["Software Engineer", "Senior Engineer", "Tech Lead", "DevOps Engineer", "QA Engineer"],
    "Product": ["Product Manager", "Product Analyst", "UX Designer"],
    "Sales": ["Account Executive", "Sales Manager", "SDR"],
    "Marketing": ["Marketing Manager", "Content Strategist", "Growth Analyst"],
    "HR": ["HR Generalist", "Recruiter", "HR Manager"],
    "Finance": ["Financial Analyst", "Controller", "Accountant"],
    "Legal": ["Legal Counsel", "Paralegal", "Compliance Analyst"],
    "IT Operations": ["System Administrator", "Network Engineer", "Help Desk Analyst", "DBA"],
    "Security": ["Security Analyst", "Security Engineer", "SOC Analyst", "CISO"],
    "Executive": ["CEO", "CTO", "CFO", "COO"],
}

ACCESS_LEVELS = ["standard", "elevated", "privileged", "admin"]
PERMISSIONS = [
    "read:internal", "write:internal", "read:confidential", "write:confidential",
    "admin:systems", "admin:users", "deploy:production", "access:vpn",
    "manage:budgets", "approve:changes",
]


@GeneratorRegistry.register
class RoleGenerator(AbstractGenerator):
    """Generates Role entities based on department specs."""

    GENERATES = EntityType.ROLE

    def generate(self, count: int, context: GenerationContext) -> list[Role]:
        departments = context.get_entities(EntityType.DEPARTMENT)
        roles: list[Role] = []

        for dept in departments:
            dept_roles = ROLE_TEMPLATES.get(dept.name, ["Analyst", "Manager", "Director"])
            for role_name in dept_roles:
                is_privileged = any(
                    kw in role_name.lower()
                    for kw in ["admin", "lead", "manager", "director", "ciso", "cto", "ceo", "cfo", "coo"]
                )
                access = "privileged" if is_privileged else random.choice(ACCESS_LEVELS[:2])

                role = Role(
                    name=role_name,
                    description=f"{role_name} role in {dept.name}",
                    department_id=dept.id,
                    access_level=access,
                    is_privileged=is_privileged,
                    permissions=random.sample(PERMISSIONS, k=random.randint(2, 5)),
                    tags=[dept.name.lower().replace(" ", "_")],
                )
                roles.append(role)

        context.store(EntityType.ROLE, roles)
        return roles
