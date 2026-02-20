"""Generator for Department entities with dynamic sub-department scaling."""

from __future__ import annotations

import random

from domain.base import EntityType
from domain.entities.department import Department
from synthetic.base import AbstractGenerator, GenerationContext, GeneratorRegistry

# Minimum headcount for a department to be subdivided into sub-departments.
SUBDIVISION_THRESHOLD = 500

# Sub-department templates by parent department name.
# Covers all department names across tech, financial, and healthcare profiles.
SUB_DEPARTMENT_TEMPLATES: dict[str, list[str]] = {
    # --- Technology profiles ---
    "Engineering": [
        "Platform Engineering",
        "Product Engineering",
        "Infrastructure",
        "Data Engineering",
        "Mobile Engineering",
        "Frontend Engineering",
        "Backend Engineering",
        "QA & Testing",
        "SRE & Reliability",
        "Security Engineering",
    ],
    "Product": [
        "Product Management",
        "UX & Design",
        "Product Analytics",
        "Technical Writing",
    ],
    "Sales": [
        "Enterprise Sales",
        "Mid-Market Sales",
        "Inside Sales",
        "Solutions Engineering",
        "Sales Operations",
    ],
    "Marketing": [
        "Digital Marketing",
        "Brand & Communications",
        "Product Marketing",
        "Events & Field Marketing",
        "Demand Generation",
    ],
    "IT Operations": [
        "Cloud Infrastructure",
        "Service Desk",
        "Network Operations",
        "Database Administration",
    ],
    "Security": [
        "Security Operations",
        "GRC",
        "Threat Intelligence",
        "Application Security",
        "Identity & Access Management",
    ],
    "HR": [
        "Talent Acquisition",
        "Compensation & Benefits",
        "Learning & Development",
        "Employee Relations",
    ],
    "Finance": [
        "Financial Planning & Analysis",
        "Treasury",
        "Tax",
        "Accounts Payable & Receivable",
    ],
    "Legal": [
        "Corporate Legal",
        "Intellectual Property",
        "Employment Law",
    ],
    # --- Financial services profiles ---
    "Trading": [
        "Equities Trading",
        "Fixed Income",
        "Derivatives",
        "FX Trading",
        "Commodities",
    ],
    "Technology": [
        "Platform Engineering",
        "Application Development",
        "Infrastructure & Cloud",
        "Data Engineering",
        "DevOps & SRE",
        "QA & Testing",
    ],
    "Risk Management": [
        "Market Risk",
        "Credit Risk",
        "Operational Risk",
        "Model Risk",
    ],
    "Compliance & Legal": [
        "Regulatory Compliance",
        "Legal Affairs",
        "Privacy & Data Protection",
        "Anti-Money Laundering",
    ],
    "Operations": [
        "Settlement & Clearing",
        "Reconciliation",
        "Client Onboarding",
        "Middle Office",
    ],
    "Client Services": [
        "Private Banking",
        "Institutional Services",
        "Retail Banking",
        "Wealth Management",
    ],
    "Finance & Accounting": [
        "Financial Planning & Analysis",
        "Treasury Operations",
        "Tax & Compliance",
        "Accounts & Reporting",
    ],
    "Information Security": [
        "Security Operations Center",
        "GRC",
        "Threat Intelligence",
        "Application Security",
        "Identity & Access Management",
    ],
    "Internal Audit": [
        "IT Audit",
        "Financial Audit",
        "Operational Audit",
    ],
    # --- Healthcare profiles ---
    "Clinical Operations": [
        "Emergency Medicine",
        "Surgical Services",
        "Outpatient Services",
        "Inpatient Care",
        "Diagnostics & Imaging",
        "Rehabilitation",
        "Pediatrics",
        "Cardiology",
    ],
    "Nursing": [
        "Medical-Surgical Nursing",
        "ICU & Critical Care",
        "Emergency Nursing",
        "Pediatric Nursing",
        "Obstetrics & Gynecology",
    ],
    "Administration": [
        "Hospital Administration",
        "Patient Access",
        "Health Information Management",
        "Quality Improvement",
    ],
    "IT": [
        "Clinical Systems",
        "Infrastructure",
        "Service Desk",
        "Data & Analytics",
        "Cybersecurity",
    ],
    "Finance & Billing": [
        "Revenue Cycle Management",
        "Claims Processing",
        "Patient Accounts",
        "Financial Planning",
    ],
    "Pharmacy": [
        "Inpatient Pharmacy",
        "Outpatient Pharmacy",
        "Clinical Pharmacy",
    ],
    "Research": [
        "Clinical Trials",
        "Basic Research",
        "Translational Research",
        "Biostatistics",
    ],
    "Compliance": [
        "Regulatory Compliance",
        "Privacy (HIPAA)",
        "Accreditation",
    ],
    "Facilities": [
        "Maintenance & Engineering",
        "Environmental Services",
        "Safety & Security",
    ],
}


def _subdivide_department(
    parent: Department,
    profile_name: str,
) -> list[Department]:
    """Split a large department into sub-departments.

    Returns the parent (with reduced headcount for leadership) plus
    the sub-department entities linked via parent_department_id.
    """
    templates = SUB_DEPARTMENT_TEMPLATES.get(parent.name, [])
    if not templates:
        return [parent]

    # Number of sub-departments scales with headcount
    n_subs = min(len(templates), max(2, parent.headcount // 300))
    chosen = templates[:n_subs]

    # Reserve ~3% of headcount for parent (leadership)
    leadership_headcount = max(3, int(parent.headcount * 0.03))
    remaining = parent.headcount - leadership_headcount
    parent.headcount = leadership_headcount

    result: list[Department] = [parent]

    # Distribute remaining headcount across sub-departments
    base_per_sub = remaining // n_subs
    leftover = remaining - base_per_sub * n_subs

    for i, sub_name in enumerate(chosen):
        sub_headcount = base_per_sub + (1 if i < leftover else 0)
        budget = round(sub_headcount * random.uniform(80_000, 150_000), 2)

        sub_dept = Department(
            name=f"{parent.name} - {sub_name}",
            description=f"{sub_name} division within {parent.name} at {profile_name}",
            code=f"{parent.code}_{i + 1:02d}"[:8],
            headcount=sub_headcount,
            parent_department_id=parent.id,
            tags=list(parent.tags),
            metadata=dict(parent.metadata),
            budget=budget,
        )
        result.append(sub_dept)

    return result


@GeneratorRegistry.register
class DepartmentGenerator(AbstractGenerator):
    """Generates Department entities from the org profile department specs.

    For large organizations, departments exceeding SUBDIVISION_THRESHOLD
    employees are subdivided into sub-departments for realistic scaling.
    """

    GENERATES = EntityType.DEPARTMENT

    def generate(self, count: int, context: GenerationContext) -> list[Department]:
        profile = context.profile
        departments: list[Department] = []

        for spec in profile.department_specs:
            headcount = int(profile.employee_count * spec.headcount_fraction)
            budget = round(headcount * random.uniform(80_000, 150_000), 2)

            dept = Department(
                name=spec.name,
                description=f"{spec.name} department at {profile.name}",
                code=spec.name.upper().replace(" ", "_")[:8],
                headcount=headcount,
                tags=[spec.data_sensitivity],
                metadata={"data_sensitivity": spec.data_sensitivity},
                budget=budget,
            )

            if headcount > SUBDIVISION_THRESHOLD and spec.name in SUB_DEPARTMENT_TEMPLATES:
                departments.extend(_subdivide_department(dept, profile.name))
            else:
                departments.append(dept)

        context.store(EntityType.DEPARTMENT, departments)
        return departments
