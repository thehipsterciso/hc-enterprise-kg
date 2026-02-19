"""Example: automatically construct a knowledge graph from CSV data."""

import tempfile
from pathlib import Path

from hc_enterprise_kg.auto.extractors.csv_extractor import CSVExtractor
from hc_enterprise_kg.auto.linkers.heuristic_linker import HeuristicLinker
from hc_enterprise_kg.auto.pipeline import AutoKGPipeline
from hc_enterprise_kg.auto.resolvers.dedup_resolver import DedupResolver
from hc_enterprise_kg.domain.base import EntityType
from hc_enterprise_kg.graph.knowledge_graph import KnowledgeGraph

# Sample organizational data
SAMPLE_DATA = """name,first_name,last_name,email,department,title,location
Alice Smith,Alice,Smith,alice@acme.com,Engineering,Software Engineer,New York
Bob Jones,Bob,Jones,bob@acme.com,Marketing,Marketing Manager,San Francisco
Carol White,Carol,White,carol@acme.com,Engineering,Senior Engineer,New York
Dave Brown,Dave,Brown,dave@acme.com,Finance,Financial Analyst,Chicago
Eve Wilson,Eve,Wilson,eve@acme.com,Human Resources,HR Director,San Francisco
Frank Miller,Frank,Miller,frank@acme.com,Engineering,DevOps Engineer,New York
Grace Lee,Grace,Lee,grace@acme.com,Sales,Account Executive,Chicago
Alice Smith,Alice,Smith,alice.s@acme.com,Engineering,Lead Engineer,New York
"""


def main() -> None:
    # Step 1: Create a knowledge graph
    kg = KnowledgeGraph(backend="networkx", track_events=True)

    # Step 2: Write sample CSV to a temp file
    with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
        f.write(SAMPLE_DATA)
        csv_path = f.name

    print(f"CSV file: {csv_path}")

    # Step 3: Configure and run the auto-KG pipeline
    # Disable LLM and embeddings for this example (no API keys needed)
    pipeline = AutoKGPipeline(
        kg,
        extractors=[CSVExtractor()],
        linkers=[HeuristicLinker(name_match_threshold=85.0)],
        resolver=DedupResolver(name_threshold=90.0),
        use_llm=False,
        use_embeddings=False,
    )

    print("\n=== Running Auto-KG Pipeline ===")
    result = pipeline.run(csv_path)

    # Step 4: Show pipeline results
    print(f"\n=== Pipeline Results ===")
    for key, value in sorted(result.stats.items()):
        print(f"  {key}: {value}")

    # Step 5: Explore the resulting graph
    print(f"\n=== Graph Contents ===")
    stats = kg.statistics
    print(f"  Total entities: {stats['entity_count']}")
    print(f"  Total relationships: {stats['relationship_count']}")

    people = kg.query().entities(EntityType.PERSON).execute()
    print(f"\n=== Extracted People ({len(people)}) ===")
    for p in people:
        email = getattr(p, "email", "N/A")
        title = getattr(p, "title", "N/A")
        print(f"  {p.name} - {title} ({email})")

    # Step 6: Check if deduplication worked
    # Alice Smith appears twice in the CSV — should be merged
    alice_count = sum(1 for p in people if "Alice" in p.name)
    print(f"\n=== Deduplication ===")
    print(f"  Alice entries in CSV: 2")
    print(f"  Alice entities in KG: {alice_count}")
    if alice_count == 1:
        print("  Deduplication successful!")

    # Step 7: Export results
    from hc_enterprise_kg.export.json_export import JSONExporter

    exporter = JSONExporter()
    json_str = exporter.export_string(kg.engine)
    print(f"\n=== JSON Export ===")
    print(f"  Output size: {len(json_str):,} characters")

    # Clean up temp file
    Path(csv_path).unlink()
    print("\nDone!")


if __name__ == "__main__":
    main()
