# Organization Profiles & Scaling

Synthetic generation is driven by organization profiles that define industry characteristics, department structures, and entity density. Three profiles are included out of the box: technology, financial services, and healthcare. Each produces structurally different graphs that reflect real-world industry patterns.

---

## Profile Comparison

| | Technology | Financial Services | Healthcare |
|---|---|---|---|
| **Default Name** | Acme Technologies | Atlas Financial Group | MedCare Health Systems |
| **Default Employees** | 500 | 1,000 | 2,000 |
| **Key Departments** | Engineering (35%), Product (10%), Sales (15%), IT Ops (10%), Security (5%) | Trading (15%), Risk Mgmt (10%), Technology (20%), Compliance (8%), Info Security (8%) | Clinical Ops (40%), Nursing (15%), Administration (8%), IT (6%), Compliance (4%) |
| **Network Architecture** | Corporate, DMZ, Dev/Staging, Guest WiFi | Trading Floor (restricted), Corporate, DMZ, DR Site, Guest | Clinical (restricted), Administrative, Medical Devices (restricted), Guest, DMZ |
| **Vulnerability Probability** | 0.20 | 0.12 | 0.18 |
| **Contractor Fraction** | 0.10 | 0.20 | 0.15 |
| **Remote Fraction** | 0.30 | 0.25 | 0.10 |
| **Scaling Focus** | Dense systems (1:8), heavy integrations | 2.5x controls, 2.7x risks, dense compliance | 3x data assets, 2x data flows, heavy regulated data |

---

## Industry Scaling Coefficients

Entity counts are derived from employee count using industry-specific coefficients. The coefficient represents employees per entity: a systems coefficient of 8 means one system per 8 employees.

| Entity Type | Technology | Financial | Healthcare |
|---|---|---|---|
| Systems | 8 | 12 | 15 |
| Vendors | **25** | **20** | **30** |
| Data Assets | 15 | 10 | **5** |
| Policies | 100 | 40 | 50 |
| Controls | 50 | **20** | 25 |
| Risks | 80 | **30** | 40 |
| Threats | 200 | 150 | 200 |
| Integrations | 30 | 40 | 35 |
| Data Domains | 400 | 300 | 200 |
| Data Flows | 25 | 20 | **15** |
| Org Units | **80** | **60** | **70** |
| Capabilities | 100 | 80 | 100 |
| Sites | 500 | 400 | 300 |
| Geographies | 1000 | 800 | 800 |
| Jurisdictions | 1000 | **600** | 600 |
| Product Portfolios | 2000 | 1500 | 2000 |
| Products | 200 | 150 | 200 |
| Market Segments | 1000 | 800 | 1000 |
| Customers | **50** | **25** | **40** |
| Contracts | **15** | **8** | **12** |
| Initiatives | 200 | 150 | 200 |
| Threat Actors | 250 | 200 | 300 |
| Incidents | 200 | 150 | 100 |

Bold values highlight where an industry differs most from the default. Coefficients for vendors, org units, customers, and contracts were adjusted in v0.19.0 based on Gartner, MuleSoft, NIST, Hackett Group, and McKinsey research benchmarks.

---

## Dynamic Department & Role Scaling

For organizations above ~500 employees per department, departments are automatically subdivided into sub-departments for realistic scaling. Sub-departments are linked to their parent via `parent_department_id`.

### How It Works

1. Each department's headcount is computed from `employee_count * headcount_fraction`
2. If headcount exceeds 500 and a sub-department template exists, the department is subdivided
3. The parent department retains ~3% headcount (leadership positions)
4. Sub-departments split the remaining headcount evenly
5. Number of sub-departments: `min(template_count, max(2, headcount // 300))`

### Sub-Department Templates

30+ template sets cover all departments across the three profiles:

| Department | Sub-department Examples |
|---|---|
| Engineering | Platform, Product, Infrastructure, Data, Mobile, Frontend, Backend, QA, SRE, Security Engineering |
| Sales | Enterprise, Mid-Market, Inside Sales, Solutions Engineering, Sales Operations |
| Clinical Operations | Emergency Medicine, Surgical Services, Outpatient, Inpatient, Diagnostics, Rehabilitation, Pediatrics, Cardiology |
| Trading | Equities, Fixed Income, Derivatives, FX, Commodities |

### Role Seniority Expansion

Roles in sub-departments are expanded with seniority variants based on headcount:

| Headcount Threshold | Seniority Variants Added |
|---|---|
| >= 100 | Senior {Role} |
| >= 300 | Junior {Role} + Senior {Role} |
| >= 500 | Junior {Role} + Senior {Role} + Staff {Role} |

Roles containing management/leadership keywords (Manager, Director, VP, C-suite) are exempt from seniority expansion.

### Scaling Results (Technology Profile)

| Employees | Departments | Roles |
|---|---|---|
| 100 | 10 | 35 |
| 500 | 10 | 38 |
| 2,000 | 12 | 71 |
| 5,000 | 17 | 127 |
| 14,512 | 42 | 301 |
| 20,000 | 49 | 382 |

People are distributed to leaf departments (sub-departments where they exist, parent departments where they don't) using headcount-proportional assignment.

---

## Size Tier Scaling

Organizations scale differently depending on their size. A startup shares systems across teams and has informal controls. A large enterprise has departmentalized infrastructure, formal compliance programs, and regulatory burden that multiplies entity density.

| Tier | Employee Range | Multiplier | Characteristics |
|---|---|---|---|
| Startup | < 250 | 0.7x | Shared systems, informal controls |
| Mid-market | 250 - 1,999 | 1.0x | Baseline |
| Enterprise | 2,000 - 9,999 | 1.2x | Departmentalized, formal compliance |
| Large Enterprise | 10,000+ | 1.4x | Complex hierarchy, regulatory burden |

### How `scaled_range()` Works

```python
def scaled_range(employee_count, coefficient, floor, ceiling):
    tier = _size_tier_multiplier(employee_count)  # 0.7 / 1.0 / 1.2 / 1.4
    base = max(floor, int((employee_count / coefficient) * tier))
    low  = min(ceiling - 1, max(floor, int(base * 0.8)))
    high = min(ceiling, max(low + 1, int(base * 1.2)))
    return (low, high)
```

The function returns a `(low, high)` tuple. The orchestrator picks a random value within this range. Floor and ceiling prevent degenerate counts.

### Example: Systems at Different Scales (Technology Profile)

| Employees | Tier | Raw Base | Range |
|---|---|---|---|
| 100 | Startup (0.7x) | 8 | 7 - 10 |
| 500 | Mid-market (1.0x) | 62 | 50 - 75 |
| 5,000 | Enterprise (1.2x) | 750 | 600 - 900 |
| 20,000 | Large (1.4x) | 3,500 | 2,800 - capped |

Location counts also scale dynamically: `max(1, min(100, employee_count // N + 1))` where N varies by industry (400 for tech, 300 for financial, 200 for healthcare).

---

## Quality Scoring

After generation, the orchestrator runs an automated quality assessment that checks five dimensions:

| Metric | What It Checks | How |
|---|---|---|
| **Risk Math Consistency** | `inherent_risk_level == RISK_MATRIX[likelihood][impact]` | Verifies deterministic derivation for all Risk entities |
| **Description Quality** | No lorem ipsum or faker-generated text | Regex scan for `lorem`, `ipsum`, `dolor`, `sit amet`, `consectetur` |
| **Tech Stack Coherence** | Appliance-type systems should not have web frameworks | Flags appliances with django, rails, react, express, spring, flask |
| **Field Correlation** | Dependent fields agree | Residual risk <= inherent risk. Patch available correlates with vuln status. Data center sites have restricted security tier. |
| **Encryption/Classification** | Sensitive data is encrypted | Data flows with restricted/confidential classification must have `encryption_in_transit=True` |

Each metric scores 0.0 to 1.0. The overall score is the arithmetic mean. The orchestrator warns if the overall score falls below 0.7.

### Accessing Quality Reports

```python
report = orchestrator.quality_report
print(report.overall_score)       # 0.89
print(report.risk_math_consistency)  # 0.95
print(report.warnings)            # list of specific issues found
print(report.summary())           # human-readable multi-line output
```

---

## Custom Profiles

Create your own profile by defining an `OrgProfile` with department specs and optional scaling coefficients.

```python
from synthetic.profiles.base_profile import OrgProfile, DepartmentSpec, NetworkSpec, ScalingCoefficients

profile = OrgProfile(
    name="My Company",
    industry="technology",
    employee_count=300,
    department_specs=[
        DepartmentSpec(name="Engineering", headcount_fraction=0.40, data_sensitivity="high"),
        DepartmentSpec(name="Product", headcount_fraction=0.15),
        DepartmentSpec(name="Sales", headcount_fraction=0.20),
        DepartmentSpec(name="Operations", headcount_fraction=0.15),
        DepartmentSpec(name="Executive", headcount_fraction=0.10),
    ],
    network_specs=[
        NetworkSpec(name="Corporate", cidr="10.0.0.0/16", zone="internal"),
        NetworkSpec(name="DMZ", cidr="172.16.0.0/24", zone="dmz"),
    ],
    vulnerability_probability=0.15,
    contractor_fraction=0.1,
    remote_fraction=0.3,
)
```

The `industry` field determines which `ScalingCoefficients` are used. Set it to `"technology"`, `"financial_services"`, or `"healthcare"` to use built-in coefficients. For custom scaling, you can override individual count ranges directly on the profile:

```python
profile.system_count_range = (50, 100)
profile.control_count_range = (20, 40)
profile.customer_count_range = (10, 30)
```

Wire it into the CLI by adding a factory function in `src/synthetic/profiles/` and registering the profile name in `src/cli/demo_cmd.py` and `src/cli/generate.py`.

---

For the full entity model reference, see [Entity Model](entity-model.md). For architecture details, see [ARCHITECTURE.md](../ARCHITECTURE.md).
