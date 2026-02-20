# Python API Guide

The Python API provides programmatic access to graph generation, querying, analysis, and export. All imports resolve from the `src/` package root.

---

## Generating a Knowledge Graph

Create a `KnowledgeGraph`, choose an organization profile, and run the orchestrator. The `seed` parameter makes output deterministic.

```python
from graph.knowledge_graph import KnowledgeGraph
from synthetic.orchestrator import SyntheticOrchestrator
from synthetic.profiles.tech_company import mid_size_tech_company

kg = KnowledgeGraph()
profile = mid_size_tech_company(employee_count=100)
orchestrator = SyntheticOrchestrator(kg, profile, seed=42)
counts = orchestrator.generate()  # dict[str, int] — entity type → count

print(kg.statistics)
# {'entity_count': 277, 'relationship_count': 543, ...}
```

### Available Profiles

```python
from synthetic.profiles.tech_company import mid_size_tech_company
from synthetic.profiles.financial_org import financial_org
from synthetic.profiles.healthcare_org import healthcare_org

# Each accepts employee_count as parameter
tech_profile = mid_size_tech_company(employee_count=500)
fin_profile = financial_org(employee_count=1000)
health_profile = healthcare_org(employee_count=2000)
```

### Quality Reports

After generation, the orchestrator runs automated quality checks. Access the report directly:

```python
report = orchestrator.quality_report
print(report.summary())
# Overall: 0.89
# Risk math consistency: 0.95
# Description quality: 1.00
# Tech stack coherence: 0.85
# Field correlation: 0.90
# Encryption/classification: 0.75
```

The orchestrator warns if `overall_score < 0.7`.

---

## Querying the Graph

### Entity Access

```python
from domain.base import EntityType, RelationshipType

# List all entities of a type
people = kg.list_entities(entity_type=EntityType.PERSON)
systems = kg.list_entities(entity_type=EntityType.SYSTEM, limit=10)

# Get a single entity by ID
entity = kg.get_entity(entity_id)

# Add, update, remove
new_id = kg.add_entity(entity)
updated = kg.update_entity(entity_id, name="New Name")
removed = kg.remove_entity(entity_id)
```

### Query Builder

The query builder provides a fluent interface for filtered entity retrieval.

```python
# Find all people
people = kg.query().entities(EntityType.PERSON).execute()

# Filter by attributes
active_engineers = (
    kg.query()
    .entities(EntityType.PERSON)
    .where(is_active=True, title="Software Engineer")
    .execute()
)

# Find entities connected to a specific entity via a relationship type
dept_members = (
    kg.query()
    .entities(EntityType.PERSON)
    .connected_to(department_id, via=RelationshipType.WORKS_IN)
    .execute()
)
```

### Relationships

```python
# Get relationships for an entity
rels = kg.get_relationships(entity_id)
rels_out = kg.get_relationships(entity_id, direction="out")
rels_typed = kg.get_relationships(
    entity_id,
    relationship_type=RelationshipType.DEPENDS_ON
)

# Add a relationship
from domain.base import BaseRelationship
rel = BaseRelationship(
    relationship_type=RelationshipType.DEPENDS_ON,
    source_id=system_a_id,
    target_id=system_b_id,
    weight=0.8,
    confidence=0.9,
    properties={"dependency_type": "runtime"},
)
kg.add_relationship(rel)
```

### Graph Traversal

```python
# Immediate neighbors
neighbors = kg.neighbors(entity_id)
neighbors_out = kg.neighbors(entity_id, direction="out")
neighbors_typed = kg.neighbors(
    entity_id,
    relationship_type=RelationshipType.DEPENDS_ON,
    entity_type=EntityType.SYSTEM,
)

# Shortest path (returns list of entity IDs, or None)
path = kg.shortest_path(source_id, target_id)

# Blast radius (entities reachable within N hops)
affected = kg.blast_radius(entity_id, max_depth=3)
# Returns dict[int, list[BaseEntity]] — hop distance → affected entities
```

### Bulk Operations

```python
ids = kg.add_entities_bulk(entity_list)
rel_ids = kg.add_relationships_bulk(relationship_list)
```

### Graph Statistics

```python
stats = kg.statistics
# {
#     'entity_count': 277,
#     'relationship_count': 543,
#     'entity_types': {'person': 100, 'system': 45, ...},
#     'relationship_types': {'works_in': 100, 'depends_on': 87, ...},
#     'density': 0.014,
#     'is_weakly_connected': True,
# }
```

---

## Analysis

The analysis module provides graph metrics and security-specific queries.

### Centrality and Connectivity

```python
from analysis.metrics import (
    compute_centrality,
    compute_betweenness_centrality,
    compute_pagerank,
    find_most_connected,
    compute_clustering_coefficient,
    get_connected_components,
)

# Degree centrality (dict: entity_id → score)
centrality = compute_centrality(kg)

# Betweenness centrality
betweenness = compute_betweenness_centrality(kg)

# PageRank
pagerank = compute_pagerank(kg)

# Most connected entities (list of (entity_id, degree) tuples)
top_10 = find_most_connected(kg, top_n=10)

# Clustering coefficient (float)
clustering = compute_clustering_coefficient(kg)

# Connected components (list of sets of entity IDs)
components = get_connected_components(kg)
```

### Risk Scoring

```python
from analysis.metrics import compute_risk_score

risk = compute_risk_score(kg, system_id)
# {
#     'entity_id': '...',
#     'entity_name': 'web-server-01',
#     'risk_score': 65.0,
#     'factors': {
#         'vulnerabilities': 3,
#         'critical_vulnerabilities': 1,
#         'degree': 12,
#         'internet_facing_connections': 2,
#     }
# }
```

Risk score (0-100) factors: connected vulnerabilities (+10 each, +25 for critical), degree centrality (+2 per connection), internet-facing system connections (+20 each).

### Security Queries

```python
from analysis.queries import (
    find_attack_paths,
    get_blast_radius,
    find_critical_systems,
    find_unpatched_vulnerabilities,
    find_internet_facing_systems,
    find_privileged_users,
    find_vendor_dependencies,
    find_high_risk_data_assets,
)

# Shortest attack path (list of entity IDs, or None)
path = find_attack_paths(kg, source_id, target_id)

# Blast radius (all entities reachable within N hops)
affected = get_blast_radius(kg, compromised_system_id, max_depth=3)

# Security posture queries
critical = find_critical_systems(kg)              # systems where criticality="critical"
unpatched = find_unpatched_vulnerabilities(kg)     # vulns: status="open", patch_available=False
exposed = find_internet_facing_systems(kg)         # systems where is_internet_facing=True
privileged = find_privileged_users(kg)             # people with privileged roles
vendor_deps = find_vendor_dependencies(kg, vendor_id)  # systems supplied by a vendor
high_risk = find_high_risk_data_assets(kg)         # data assets: classification in (restricted, confidential)
```

---

## Auto-Construction from CSV

Build a knowledge graph from your own data. The pipeline infers entity types from column headers, extracts entities, links them by shared attributes, and deduplicates.

```python
from auto.pipeline import AutoKGPipeline
from graph.knowledge_graph import KnowledgeGraph

kg = KnowledgeGraph()
pipeline = AutoKGPipeline(kg, use_llm=False, use_embeddings=False)
result = pipeline.run("employees.csv")

print(result.stats)
# {'entities_extracted': 25, 'entities_after_dedup': 23, ...}
```

### With Optional Extractors

```python
from auto.pipeline import AutoKGPipeline
from auto.extractors.csv_extractor import CSVExtractor
from auto.linkers.heuristic_linker import HeuristicLinker
from auto.resolvers.dedup_resolver import DedupResolver

pipeline = AutoKGPipeline(
    kg,
    extractors=[CSVExtractor()],
    linkers=[HeuristicLinker(name_match_threshold=85.0)],
    resolver=DedupResolver(name_threshold=90.0),
    use_llm=False,
    use_embeddings=False,
)
result = pipeline.run("employees.csv")
```

---

## Exporting

Export to JSON (entities, relationships, and statistics) or GraphML (compatible with Gephi, yEd, Cytoscape).

```python
from pathlib import Path
from export.json_export import JSONExporter
from export.graphml_export import GraphMLExporter

# Export to file
JSONExporter().export(kg.engine, Path("output.json"))
GraphMLExporter().export(kg.engine, Path("output.graphml"))

# Export to string
json_string = JSONExporter().export_string(kg.engine)
```

---

## Event Bus

Track mutations to the graph in real time.

```python
from graph.knowledge_graph import KnowledgeGraph, MutationType

kg = KnowledgeGraph(track_events=True)

def on_add(event):
    print(f"Added: {event}")

kg.subscribe(on_add, mutation_type=MutationType.ADD)

# Events are logged
print(kg.event_log)
```

---

For the full entity model reference, see [Entity Model](entity-model.md). For CLI usage, see [CLI Reference](cli.md).
