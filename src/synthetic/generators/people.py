"""Generator for Person entities."""

from __future__ import annotations

import random

from domain.base import EntityType
from domain.entities.person import Person
from synthetic.base import AbstractGenerator, GenerationContext, GeneratorRegistry

# Department → realistic job titles pool
DEPARTMENT_TITLES: dict[str, list[str]] = {
    "Engineering": [
        "Software Engineer", "Senior Software Engineer", "Staff Engineer",
        "Principal Engineer", "Engineering Manager", "DevOps Engineer",
        "Site Reliability Engineer", "QA Engineer", "Frontend Developer",
        "Backend Developer", "Platform Engineer", "Data Engineer",
    ],
    "Product": [
        "Product Manager", "Senior Product Manager", "Product Analyst",
        "UX Designer", "UI Designer", "Product Director",
    ],
    "Sales": [
        "Account Executive", "Sales Manager", "Sales Director",
        "Business Development Rep", "SDR", "VP Sales",
    ],
    "Marketing": [
        "Marketing Manager", "Content Strategist", "Growth Analyst",
        "Digital Marketing Specialist", "Brand Manager", "Marketing Director",
    ],
    "HR": [
        "HR Generalist", "Recruiter", "HR Manager", "HR Director",
        "Talent Acquisition Specialist", "Compensation Analyst",
    ],
    "Finance & Billing": [
        "Financial Analyst", "Controller", "Accountant", "Billing Specialist",
        "Revenue Analyst", "Finance Manager", "Accounts Payable Specialist",
    ],
    "Finance & Accounting": [
        "Financial Analyst", "Controller", "Accountant", "Treasury Analyst",
        "Senior Accountant", "Finance Director", "AP Specialist",
    ],
    "Legal": [
        "General Counsel", "Legal Counsel", "Paralegal", "Contract Manager",
        "Compliance Analyst", "Legal Director",
    ],
    "IT": [
        "System Administrator", "Network Engineer", "Help Desk Analyst",
        "DBA", "IT Manager", "Cloud Engineer", "IT Director",
    ],
    "IT Operations": [
        "System Administrator", "Network Engineer", "Help Desk Analyst",
        "DBA", "IT Manager", "Cloud Engineer", "IT Director",
    ],
    "Technology": [
        "Software Engineer", "DevOps Engineer", "Cloud Architect",
        "Data Engineer", "Tech Lead", "Engineering Manager", "CTO",
    ],
    "Security": [
        "Security Analyst", "Security Engineer", "SOC Analyst",
        "Penetration Tester", "Security Architect", "CISO",
    ],
    "Information Security": [
        "Security Analyst", "Security Engineer", "SOC Analyst",
        "Penetration Tester", "Threat Hunter", "Security Architect", "CISO",
    ],
    "Executive": [
        "CEO", "CTO", "CFO", "COO", "CIO", "CISO", "Chief of Staff",
    ],
    "Clinical Operations": [
        "Physician", "Nurse Practitioner", "Clinical Director",
        "Medical Officer", "Clinical Analyst", "Care Coordinator",
    ],
    "Nursing": [
        "Registered Nurse", "Charge Nurse", "Nurse Manager",
        "Clinical Nurse Specialist", "Nurse Educator",
    ],
    "Administration": [
        "Office Manager", "Executive Assistant", "Administrative Coordinator",
        "Facilities Coordinator", "Administrative Director",
    ],
    "Pharmacy": [
        "Pharmacist", "Pharmacy Technician", "Pharmacy Director",
        "Clinical Pharmacist", "Pharmacy Manager",
    ],
    "Research": [
        "Research Scientist", "Lab Technician", "Research Director",
        "Clinical Research Coordinator", "Principal Investigator",
    ],
    "Compliance": [
        "Compliance Officer", "Compliance Analyst", "Compliance Director",
        "Regulatory Affairs Specialist", "Privacy Officer",
    ],
    "Compliance & Legal": [
        "Compliance Officer", "Compliance Analyst", "Legal Counsel",
        "Regulatory Affairs Specialist", "Privacy Officer", "Compliance Director",
    ],
    "Facilities": [
        "Facilities Manager", "Maintenance Technician", "Safety Officer",
        "Building Engineer", "Facilities Director",
    ],
    "Trading": [
        "Trader", "Quantitative Analyst", "Trading Desk Manager",
        "Algorithmic Developer", "Market Maker",
    ],
    "Risk Management": [
        "Risk Analyst", "Senior Risk Analyst", "Risk Manager",
        "Credit Risk Officer", "Operational Risk Analyst",
    ],
    "Operations": [
        "Operations Analyst", "Operations Manager", "Operations Director",
        "Process Engineer", "Supply Chain Analyst",
    ],
    "Client Services": [
        "Client Manager", "Account Manager", "Client Service Director",
        "Relationship Manager", "Client Success Manager",
    ],
    "Internal Audit": [
        "Internal Auditor", "Senior Auditor", "Audit Manager",
        "IT Auditor", "Audit Director",
    ],
}

# Fallback titles when department name doesn't match
DEFAULT_TITLES = [
    "Analyst", "Senior Analyst", "Manager", "Director",
    "Coordinator", "Specialist", "Administrator", "Consultant",
]

# Weighted clearance distribution: 60% none/basic, 25% elevated, 10% privileged, 5% admin
CLEARANCE_WEIGHTS = {
    "none": 30,
    "basic": 30,
    "elevated": 25,
    "privileged": 10,
    "admin": 5,
}
CLEARANCE_POOL = [level for level, w in CLEARANCE_WEIGHTS.items() for _ in range(w)]


@GeneratorRegistry.register
class PeopleGenerator(AbstractGenerator):
    """Generates Person entities based on the org profile."""

    GENERATES = EntityType.PERSON

    def generate(self, count: int, context: GenerationContext) -> list[Person]:
        faker = context.faker
        profile = context.profile
        people: list[Person] = []
        domain = profile.name.lower().replace(" ", "") + ".com"

        # Build department-batched title assignments from profile
        dept_batches: list[tuple[str, int]] = []
        for spec in profile.department_specs:
            dept_batches.append((spec.name, max(1, int(count * spec.headcount_fraction))))

        # Generate people in department-aware batches for title coherence
        idx = 0
        for dept_name, batch_size in dept_batches:
            titles = DEPARTMENT_TITLES.get(dept_name, DEFAULT_TITLES)
            for _ in range(batch_size):
                if idx >= count:
                    break
                first = faker.first_name()
                last = faker.last_name()
                is_contractor = (idx / max(count, 1)) > (1 - profile.contractor_fraction)

                person = Person(
                    first_name=first,
                    last_name=last,
                    name=f"{first} {last}",
                    email=f"{first.lower()}.{last.lower()}@{domain}",
                    title=random.choice(titles),
                    employee_id=f"EMP-{faker.unique.random_number(digits=6):06d}",
                    clearance_level=random.choice(CLEARANCE_POOL),
                    is_active=faker.boolean(chance_of_getting_true=95),
                    hire_date=str(faker.date_between(start_date="-10y", end_date="today")),
                    phone=faker.phone_number(),
                    tags=["contractor"] if is_contractor else ["employee"],
                )
                people.append(person)
                idx += 1

        # Fill any remaining people
        while idx < count:
            first = faker.first_name()
            last = faker.last_name()
            person = Person(
                first_name=first,
                last_name=last,
                name=f"{first} {last}",
                email=f"{first.lower()}.{last.lower()}@{domain}",
                title=random.choice(DEFAULT_TITLES),
                employee_id=f"EMP-{faker.unique.random_number(digits=6):06d}",
                clearance_level=random.choice(CLEARANCE_POOL),
                is_active=faker.boolean(chance_of_getting_true=95),
                hire_date=str(faker.date_between(start_date="-10y", end_date="today")),
                phone=faker.phone_number(),
                tags=["employee"],
            )
            people.append(person)
            idx += 1

        context.store(EntityType.PERSON, people)
        return people
