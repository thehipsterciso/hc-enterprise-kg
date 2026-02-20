# Entity Model Reference

The knowledge graph models an enterprise organization as a network of typed entities connected by typed relationships. Thirty entity types span twelve generation layers, from compliance frameworks and technology infrastructure through people, products, customers, and strategic initiatives. Fifty-two relationship types encode how those entities depend on, govern, contain, and affect each other.

Every entity extends `BaseEntity` (Pydantic v2) and carries a UUID, name, description, tags, metadata, and temporal fields. Every relationship carries a type, source/target IDs, contextual weight, confidence score, and a properties dict. The model is designed for structural analysis: dependency mapping, blast radius computation, centrality scoring, and risk quantification all operate directly on this graph.

---

## Core Entities (12)

These entity types form the foundational organizational model: people, structure, technology, security, and third-party relationships.

| Entity Type | Description | Key Attributes |
|---|---|---|
| **Person** | Employees and contractors | title, email, clearance_level, is_active, holds_roles, located_at |
| **Department** | Organizational units | headcount, budget, data_sensitivity |
| **Role** | Job roles with permissions | title, level, permissions, is_privileged, filled_by_persons |
| **System** | Servers, applications, SaaS platforms | hostname, ip_address, os, criticality, tech_stack, is_internet_facing |
| **Network** | Network segments | cidr, zone (dmz, internal, restricted, guest) |
| **Data Asset** | Databases, file stores, data repositories | classification, data_type, format, encryption |
| **Policy** | Governance and compliance documents | framework, status, severity, enforcement |
| **Vendor** | Third-party suppliers and service providers | risk_tier, has_data_access, certifications |
| **Location** | Physical locations | city, country, region |
| **Vulnerability** | Security weaknesses | cve_id, cvss_score, severity, patch_available, status |
| **Threat Actor** | Adversaries and threat sources | motivation, sophistication, origin_country, actor_type |
| **Incident** | Security events and breaches | severity, status, affected_systems, detection_method |

---

## Enterprise Entities (18)

These entity types extend the model to cover compliance, data governance, business capabilities, products, customers, and strategy. Each is assigned to a generation layer (L01-L11) that determines build order.

| Entity Type | Layer | Description | Key Attributes |
|---|---|---|---|
| **Regulation** | L01 Compliance | Laws, standards, and regulatory frameworks (GDPR, SOX, HIPAA) | jurisdiction, authority, effective_date |
| **Control** | L01 Compliance | Security and compliance controls (SCF-aligned) | framework, domain, control_type, effectiveness |
| **Risk** | L01 Compliance | Enterprise risks with quantified scoring | inherent_likelihood, inherent_impact, inherent_risk_level, residual_risk_level, treatment |
| **Threat** | L01 Compliance | Threat catalog entries (MITRE ATT&CK-aligned) | category, threat_type, source, threat_level |
| **Integration** | L02 Technology | System-to-system integrations | integration_type, protocol, data_format, direction |
| **Data Domain** | L03 Data | Logical data groupings with stewardship | owner, steward, classification |
| **Data Flow** | L03 Data | Data movement between systems | source_system, target_system, method, data_classification, encryption_in_transit |
| **Organizational Unit** | L04 Organization | Business units, divisions, subsidiaries | unit_type, parent_unit, headcount |
| **Business Capability** | L06 Capabilities | Capability map (L1/L2/L3 hierarchy) | level, functional_domain, maturity, strategic_importance |
| **Site** | L07 Locations | Physical facilities | address, site_type, capacity, physical_security_tier |
| **Geography** | L07 Locations | Geographic regions and territories | region_type, countries |
| **Jurisdiction** | L07 Locations | Regulatory jurisdictions | jurisdiction_type, governing_body |
| **Product Portfolio** | L08 Products | Product groupings and strategy | portfolio_type, lifecycle_stage, strategy |
| **Product** | L08 Products | Individual products and services | product_type, criticality, revenue, compliance_requirements |
| **Market Segment** | L09 Customers | Target markets and segments | segment_type, size, demographics |
| **Customer** | L09 Customers | Customer accounts and relationships | customer_type, industry, revenue, satisfaction |
| **Contract** | L10 Vendors | Vendor contracts with SLAs and terms | contract_type, value, sla_terms, renewal_date |
| **Initiative** | L11 Initiatives | Strategic programs and projects | initiative_type, status, budget, timeline, sponsors |

---

## Generation Layers (L00-L11)

Entities are generated in layer order to ensure referential integrity. Each layer can reference entities from all previous layers but not from subsequent ones.

| Layer | Name | Entity Types | Purpose |
|---|---|---|---|
| L00 | Foundation | Shared sub-models, enums, base classes | Infrastructure for all other layers |
| L01 | Compliance | Regulation, Control, Risk, Threat | Governance and risk framework |
| L02 | Technology | System (extended), Integration | Technology infrastructure and interconnections |
| L03 | Data | DataAsset (extended), DataDomain, DataFlow | Data landscape and movement |
| L04 | Organization | OrganizationalUnit | Business structure above departments |
| L05 | People | Person (extended), Role (extended) | Workforce and job functions |
| L06 | Capabilities | BusinessCapability | What the organization can do |
| L07 | Locations | Site, Geography, Jurisdiction | Where the organization operates |
| L08 | Products | ProductPortfolio, Product | What the organization delivers |
| L09 | Customers | MarketSegment, Customer | Who the organization serves |
| L10 | Vendors | Vendor (extended), Contract | Third-party relationships |
| L11 | Initiatives | Initiative | Strategic programs driving change |

Department, Network, Policy, Location, Vulnerability, Threat Actor, and Incident are generated as part of the core pipeline alongside the layer system.

---

## Relationship Types (52)

Every relationship has a defined source type and target type (see schema below). Relationships carry three metadata fields beyond the type:

- **weight** (float, 0.0-1.0): Contextual strength. Severity-based for security relationships (critical vuln = 1.0, low = 0.3), variance-based for dependencies (random 0.5-1.0), fixed for organizational facts (WORKS_IN = 1.0).
- **confidence** (float, 0.0-1.0): How certain the relationship is. Organizational facts are 0.90-0.95. Threat attribution is 0.70-0.75. Automated inferences fall in between.
- **properties** (dict): Contextual key-value pairs. Examples: `{"dependency_type": "runtime"}`, `{"severity": "critical"}`, `{"enforcement": "mandatory"}`, `{"assignment_type": "primary"}`.

### Organizational

| Type | Source | Target | Description |
|---|---|---|---|
| `works_in` | Person | Department | Employment assignment |
| `manages` | Person | Person, Department | Management relationship |
| `reports_to` | Person | Person | Reporting chain |
| `has_role` | Person | Role | Role assignment |
| `member_of` | Person | Department, Organizational Unit | Membership |

### Technical

| Type | Source | Target | Description |
|---|---|---|---|
| `hosts` | System, Network | System, Data Asset | Hosting relationship |
| `connects_to` | System | Network | Network connectivity |
| `depends_on` | System | System | System dependency |
| `stores` | System | Data Asset | Data storage |
| `runs_on` | System | System | Runtime platform |

### Security

| Type | Source | Target | Description |
|---|---|---|---|
| `governs` | Policy | System, Data Asset, Department | Policy governance |
| `exploits` | Threat Actor | Vulnerability | Exploitation |
| `targets` | Threat Actor, Threat | System, Person, Data Asset | Targeting |
| `mitigates` | Control | Risk, Vulnerability, Threat | Risk mitigation |
| `affects` | Vulnerability, Incident | System, Data Asset | Impact |

### Operational

| Type | Source | Target | Description |
|---|---|---|---|
| `provides_service` | System, Vendor | Department, Organizational Unit | Service delivery |
| `located_at` | Person, System, Department, Site | Location, Site, Geography | Physical location |
| `supplied_by` | System | Vendor | Vendor supply |
| `responsible_for` | Department, Person | System, Data Asset | Ownership |

### Cross-Layer

| Type | Source | Target | Description |
|---|---|---|---|
| `supports` | System, Business Capability | Business Capability, Product, Initiative | Capability support |
| `belongs_to` | Data Flow, Product, System | Data Domain, Product Portfolio, Organizational Unit | Containment |
| `staffed_by` | Department, Organizational Unit | Person | Staffing |
| `hosted_on` | System, Data Asset | System, Site | Hosting platform |
| `processes` | System | Data Asset, Data Flow | Data processing |
| `delivers` | System, Vendor | Product, Data Asset | Delivery |
| `serves` | Product, System | Customer, Market Segment | Service |
| `managed_by` | System, Product, Contract | Person, Department | Management |
| `governed_by` | System, Data Asset, Product | Policy, Regulation, Control | Governance |
| `impacted_by` | System, Product, Business Capability | Incident, Risk, Threat | Impact exposure |

### Compliance & Governance (L01)

| Type | Source | Target | Description |
|---|---|---|---|
| `regulates` | Regulation, Jurisdiction | System, Data Asset, Product, Vendor | Regulatory scope |
| `implements` | Control | Regulation, Policy | Control implementation |
| `enforces` | Control, Policy | Regulation, Risk | Enforcement |
| `creates_risk` | Threat, Vulnerability, Vendor | Risk | Risk creation |
| `addresses` | Control, Initiative | Risk, Threat | Risk treatment |
| `audited_by` | System, Vendor, Control | Person, Department | Audit assignment |
| `subject_to` | System, Vendor, Data Asset, Product | Regulation, Jurisdiction | Regulatory subjection |

### Technology & Systems (L02)

| Type | Source | Target | Description |
|---|---|---|---|
| `integrates_with` | System, Integration | System | System integration |
| `authenticates_via` | System, Person | System, Integration | Authentication |
| `feeds_data_to` | System, Data Asset | System, Data Asset | Data feed |

### Data Assets (L03)

| Type | Source | Target | Description |
|---|---|---|---|
| `contains` | Data Domain, System | Data Asset, Data Flow | Containment |
| `flows_to` | Data Flow, Data Asset | System, Data Asset | Data movement |
| `originates_from` | Data Flow, Data Asset | System, Vendor | Data origin |
| `classified_as` | Data Asset | Data Domain | Classification |

### Business Capabilities (L06)

| Type | Source | Target | Description |
|---|---|---|---|
| `enables` | System, Product | Business Capability | Capability enablement |
| `realized_by` | Business Capability | System, Product, Person | Capability realization |

### Commercial (L08-L10)

| Type | Source | Target | Description |
|---|---|---|---|
| `buys` | Customer | Product | Purchase |
| `contracts_with` | Contract | Vendor | Contractual relationship |
| `holds` | Customer, Vendor | Contract | Contract holding |
| `provides` | Vendor | System, Product, Data Asset | Vendor provision |
| `supplies` | Vendor | System, Product | Supply |

### Strategic Initiatives (L11)

| Type | Source | Target | Description |
|---|---|---|---|
| `impacts` | Initiative | System, Product, Business Capability, Risk | Initiative impact |
| `drives` | Initiative | Product, Business Capability, Control | Initiative driver |
| `funded_by` | Initiative | Department, Organizational Unit | Funding source |

---

## Base Model Fields

### BaseEntity

All entities inherit these fields:

| Field | Type | Default | Description |
|---|---|---|---|
| `id` | str | uuid4() | Unique identifier |
| `entity_type` | EntityType | — | Discriminator |
| `name` | str | — | Display name |
| `description` | str | `""` | Human-readable description |
| `tags` | list[str] | `[]` | Classification tags |
| `metadata` | dict[str, Any] | `{}` | Extensible metadata |
| `created_at` | datetime | now(UTC) | Creation timestamp |
| `updated_at` | datetime | now(UTC) | Last update timestamp |
| `valid_from` | datetime \| None | `None` | Temporal validity start |
| `valid_until` | datetime \| None | `None` | Temporal validity end |
| `version` | int | `1` | Entity version |

### BaseRelationship

All relationships inherit these fields:

| Field | Type | Default | Description |
|---|---|---|---|
| `id` | str | uuid4() | Unique identifier |
| `relationship_type` | RelationshipType | — | Discriminator |
| `source_id` | str | — | Source entity ID |
| `target_id` | str | — | Target entity ID |
| `weight` | float | `1.0` | Contextual strength (0.0-1.0) |
| `confidence` | float | `1.0` | Attribution confidence (0.0-1.0) |
| `properties` | dict[str, Any] | `{}` | Contextual key-value pairs |
| `created_at` | datetime | now(UTC) | Creation timestamp |
| `updated_at` | datetime | now(UTC) | Last update timestamp |

---

For the full architecture, layer pipeline, and engine abstraction details, see [ARCHITECTURE.md](../ARCHITECTURE.md).
