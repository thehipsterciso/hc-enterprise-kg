# Import Guide

Import real organizational data into the knowledge graph using `hckg import`. Supports JSON (multi-type, with relationships) and CSV (single entity type per file).

## Quick Start

```bash
# Import a JSON file with entities and relationships
hckg import organization.json

# Import a CSV of people
hckg import people.csv -t person

# Import with a vendor column mapping
hckg import workday-export.csv --mapping workday-hr.mapping.json

# Validate without writing output
hckg import data.json --dry-run

# Merge into an existing graph
hckg import new-systems.json --merge existing-graph.json
```

## CLI Options

| Option | Default | Description |
|---|---|---|
| `SOURCE` (required) | — | Path to JSON or CSV file |
| `-o`, `--output` | `graph.json` | Output graph file path |
| `-t`, `--entity-type` | auto-detect | Entity type for CSV import |
| `-m`, `--merge` | — | Merge into existing graph file |
| `--mapping` | — | Column mapping file for CSV (`.mapping.json`) |
| `--dry-run` | off | Validate only, do not write output |
| `--strict` | off | Treat warnings as errors |

**Constraints:** `--mapping` and `--entity-type` are mutually exclusive. `--mapping` is CSV-only.

## JSON Format

The canonical JSON format contains `entities` and `relationships` arrays:

```json
{
  "entities": [
    {
      "id": "person-001",
      "entity_type": "person",
      "name": "Jane Doe",
      "first_name": "Jane",
      "last_name": "Doe",
      "email": "jane.doe@example.com",
      "title": "Senior Software Engineer"
    },
    {
      "id": "dept-eng",
      "entity_type": "department",
      "name": "Engineering",
      "code": "ENG",
      "headcount": 45
    }
  ],
  "relationships": [
    {
      "relationship_type": "works_in",
      "source_id": "person-001",
      "target_id": "dept-eng"
    }
  ]
}
```

**Required fields** for every entity: `id`, `entity_type`, `name`.

See `examples/import-templates/organization.json` for a complete template covering all 30 entity types with 31 relationships.

### Entity Types (30)

The `entity_type` field must be one of:

| Category | Types |
|---|---|
| People & Org | `person`, `department`, `role`, `organizational_unit` |
| Technology | `system`, `network`, `integration` |
| Data | `data_asset`, `data_domain`, `data_flow` |
| Security | `vulnerability`, `threat_actor`, `incident`, `threat` |
| Governance | `policy`, `regulation`, `control`, `risk` |
| Locations | `location`, `site`, `geography`, `jurisdiction` |
| Commercial | `vendor`, `contract`, `customer`, `market_segment`, `product`, `product_portfolio`, `initiative`, `business_capability` |

### Relationship Types

Use lowercase relationship type values. Common types:

| Type | Meaning |
|---|---|
| `works_in` | Person → Department |
| `has_role` | Person → Role |
| `manages` | Person → Person |
| `responsible_for` | Department → System |
| `connects_to` | System → Network |
| `stores` | System → DataAsset |
| `affects` | Vulnerability → System |
| `mitigates` | Control → Risk |
| `implements` | Control → Policy/Regulation |
| `subject_to` | Entity → Regulation |
| `supplies` | Vendor → System |
| `contracts_with` | Contract → Vendor |
| `supports` | System → BusinessCapability |
| `located_at` | Entity → Location/Site/Geography |
| `contains` | OrgUnit → Department |
| `buys` | Customer → Product |
| `impacts` | Initiative → System |

See `src/domain/base.py` `RelationshipType` for the full list of 50+ types.

## CSV Format

Each CSV file imports one entity type. The first row must be column headers.

```bash
# Explicit entity type
hckg import people.csv -t person

# Auto-detection (infers type from column names)
hckg import people.csv
```

Auto-detection works for all 30 entity types based on column name patterns. Use `-t` when auto-detection picks the wrong type.

### CSV Templates

Ready-to-use templates are in `examples/import-templates/`:

| File | Entity Type | Key Columns |
|---|---|---|
| `people.csv` | person | name, first_name, last_name, email, title, employee_id, hire_date |
| `departments.csv` | department | name, description, code, headcount |
| `systems.csv` | system | name, system_type, hostname, ip_address, os, criticality, environment |
| `vendors.csv` | vendor | name, vendor_type, risk_tier, has_data_access, primary_contact |
| `vulnerabilities.csv` | vulnerability | name, cve_id, cvss_score, severity, status, exploit_available |
| `risks.csv` | risk | name, risk_id, risk_category, inherent_risk_level, residual_risk_level |
| `controls.csv` | control | name, control_id, control_type, control_domain, control_status |
| `incidents.csv` | incident | name, incident_type, severity, status, detection_method |

## Column Mappings

When your CSV has vendor-specific column names (e.g., Workday, ServiceNow), use a `.mapping.json` file to translate columns to canonical field names.

```bash
hckg import workday-export.csv --mapping workday-hr.mapping.json
```

### Mapping File Format

```json
{
  "name": "Workday People Export",
  "description": "Maps Workday HR export columns to Person entity fields",
  "entity_type": "person",
  "name_field": "Legal_First_Name",
  "columns": {
    "Worker_ID": "employee_id",
    "Legal_First_Name": "first_name",
    "Legal_Last_Name": "last_name",
    "Work_Email": "email",
    "Business_Title": "title",
    "Hire_Date": "hire_date",
    "Active_Status": "is_active"
  }
}
```

**Fields:**
- `entity_type` — target entity type (required)
- `name_field` — source column to use as entity `name` (required)
- `columns` — mapping of `source_column` → `target_field` (required)
- `name`, `description` — human labels (optional)

Example mapping files are in `examples/import-mappings/`:
- `workday-hr.mapping.json` — Workday People → Person
- `servicenow-cmdb.mapping.json` — ServiceNow CI → System
- `qualys-vulns.mapping.json` — Qualys Scan → Vulnerability

## Validation

`hckg import` validates data before writing:

- **Entity type validity** — rejects unknown `entity_type` values
- **Required fields** — checks `name` is present on all entities
- **Unknown fields** — warns when field names don't match entity schema (catches typos that would silently go to `__pydantic_extra__`)
- **Relationship validity** — verifies `relationship_type` is a known type
- **Referential integrity** — checks `source_id`/`target_id` reference existing entities

### Validation Modes

```bash
# Normal: errors abort, warnings are displayed
hckg import data.json

# Strict: warnings also abort
hckg import data.json --strict

# Dry-run: validate without writing output
hckg import data.json --dry-run
```

## Common Workflows

### Import from scratch

```bash
# Start with the JSON template, edit it with your data
cp examples/import-templates/organization.json my-org.json
# Edit my-org.json with real data...
hckg import my-org.json -o graph.json
```

### Build incrementally with CSV files

```bash
# Import people first
hckg import people.csv -t person -o graph.json

# Add systems, merging into existing graph
hckg import systems.csv -t system --merge graph.json -o graph.json

# Add vendors
hckg import vendors.csv -t vendor --merge graph.json -o graph.json
```

### Import vendor exports with mappings

```bash
# Export from Workday, then import with mapping
hckg import workday-people-2024.csv --mapping examples/import-mappings/workday-hr.mapping.json

# ServiceNow CMDB export
hckg import cmdb-ci-export.csv --mapping examples/import-mappings/servicenow-cmdb.mapping.json
```

### Validate before import

```bash
# Check for issues without writing
hckg import my-data.json --dry-run --strict

# Fix issues, then import for real
hckg import my-data.json -o graph.json
```

## Entity Field Reference

### Person
| Field | Type | Description |
|---|---|---|
| `first_name` | str | First name |
| `last_name` | str | Last name |
| `email` | str | Email address |
| `title` | str | Job title |
| `employee_id` | str | Employee identifier |
| `is_active` | bool | Employment status |
| `hire_date` | str | Date hired (YYYY-MM-DD) |
| `department_id` | str | Department entity ID |

### System
| Field | Type | Description |
|---|---|---|
| `system_type` | str | application, database, infrastructure |
| `hostname` | str | Server hostname |
| `ip_address` | str | IP address |
| `os` | str | Operating system |
| `criticality` | str | low, medium, high, critical |
| `environment` | str | production, staging, development |
| `is_internet_facing` | bool | Externally accessible |

### Vulnerability
| Field | Type | Description |
|---|---|---|
| `cve_id` | str | CVE identifier |
| `cvss_score` | float | CVSS score (0.0-10.0) |
| `severity` | str | low, medium, high, critical |
| `status` | str | open, remediated, accepted |
| `exploit_available` | bool | Known exploit exists |
| `patch_available` | bool | Patch is available |

### Risk
| Field | Type | Description |
|---|---|---|
| `risk_id` | str | Risk identifier |
| `risk_category` | str | Cybersecurity, Compliance, Operational, etc. |
| `inherent_risk_level` | str | Low, Medium, High, Critical |
| `residual_risk_level` | str | Low, Medium, High, Critical |
| `risk_status` | str | Open, Closed, Monitoring |
| `risk_owner` | str | Responsible person/role |
| `risk_treatment` | str | Mitigate, Accept, Transfer, Avoid |

### Control
| Field | Type | Description |
|---|---|---|
| `control_id` | str | Control identifier |
| `control_type` | str | Preventive, Detective, Corrective |
| `control_domain` | str | Access Control, Network Security, etc. |
| `control_status` | str | Implemented, Partially Implemented, Planned |
| `control_owner` | str | Responsible team/person |

For the complete field reference for all 30 entity types, see [Entity Model](entity-model.md).
