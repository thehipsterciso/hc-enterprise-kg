"""Quick start example: generate a synthetic enterprise KG and explore it."""

from hc_enterprise_kg.domain.base import EntityType, RelationshipType
from hc_enterprise_kg.graph.knowledge_graph import KnowledgeGraph
from hc_enterprise_kg.synthetic.orchestrator import SyntheticOrchestrator
from hc_enterprise_kg.synthetic.profiles.tech_company import mid_size_tech_company


def main() -> None:
    # Step 1: Create a knowledge graph
    kg = KnowledgeGraph(backend="networkx", track_events=True)

    # Step 2: Generate synthetic data from a tech company profile
    profile = mid_size_tech_company(employee_count=100)
    orchestrator = SyntheticOrchestrator(kg, profile, seed=42)
    counts = orchestrator.generate()

    print("=== Generation Complete ===")
    for entity_type, count in sorted(counts.items()):
        print(f"  {entity_type}: {count}")

    # Step 3: Explore the graph
    stats = kg.statistics
    print(f"\n=== Graph Statistics ===")
    print(f"  Entities: {stats['entity_count']}")
    print(f"  Relationships: {stats['relationship_count']}")
    print(f"  Entity types: {stats['entity_types']}")

    # Step 4: Query the graph
    people = kg.query().entities(EntityType.PERSON).execute()
    print(f"\n=== People ({len(people)}) ===")
    for p in people[:5]:
        print(f"  {p.name} ({p.email})")
    if len(people) > 5:
        print(f"  ... and {len(people) - 5} more")

    departments = kg.query().entities(EntityType.DEPARTMENT).execute()
    print(f"\n=== Departments ({len(departments)}) ===")
    for d in departments:
        print(f"  {d.name}")

    systems = kg.query().entities(EntityType.SYSTEM).execute()
    print(f"\n=== Systems ({len(systems)}) ===")
    for s in systems[:5]:
        print(f"  {s.name} ({s.system_type})")
    if len(systems) > 5:
        print(f"  ... and {len(systems) - 5} more")

    # Step 5: Traverse relationships
    if people:
        first_person = people[0]
        neighbors = kg.neighbors(first_person.id)
        print(f"\n=== Neighbors of {first_person.name} ===")
        for n in neighbors:
            print(f"  {n.entity_type.value}: {n.name}")

    # Step 6: Export to JSON
    from hc_enterprise_kg.export.json_export import JSONExporter

    exporter = JSONExporter()
    json_str = exporter.export_string(kg.engine)
    print(f"\n=== JSON Export ===")
    print(f"  Output size: {len(json_str):,} characters")

    # Step 7: Check event log
    print(f"\n=== Event Log ===")
    print(f"  Total events: {len(kg.event_log)}")
    if kg.event_log:
        type_counts: dict[str, int] = {}
        for event in kg.event_log:
            t = event.mutation_type.value
            type_counts[t] = type_counts.get(t, 0) + 1
        for t, c in sorted(type_counts.items()):
            print(f"  {t}: {c}")

    print("\nDone!")


if __name__ == "__main__":
    main()
