#!/usr/bin/env python3
"""
test-mcp-integration.py — End-to-end test: hc-cdaio-kg graph consumed by hc-enterprise-kg MCP server.

Builds graph.json from ~/hc-cdaio-kg per-type files, loads it through the MCP
server's own load_graph tool, then exercises all 16 tools including write
operations (add/update/remove entity and relationship).

Usage:
    poetry run python3 scripts/test-mcp-integration.py

Exit code: 0 = all pass, 1 = one or more failures.
"""

import json
import os
import sys
import tempfile
import traceback
from pathlib import Path

# ---------------------------------------------------------------------------
# Ensure src/ is on the path
# ---------------------------------------------------------------------------
REPO_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(REPO_ROOT / "src"))
LIB = REPO_ROOT / "scripts" / "lib"
sys.path.insert(0, str(LIB))

# ---------------------------------------------------------------------------
# Tiny harness (same style as test-kg-pipeline.py)
# ---------------------------------------------------------------------------
PASS = "\033[32m  PASS\033[0m"
FAIL = "\033[31m  FAIL\033[0m"
SKIP = "\033[33m  SKIP\033[0m"

_results: list[tuple[str, bool, str]] = []

def check(name: str, condition: bool, detail: str = "") -> bool:
    tag = PASS if condition else FAIL
    print(f"{tag}  {name}")
    if detail:
        for line in detail.splitlines():
            print(f"        {line}")
    _results.append((name, condition, detail))
    return condition

def section(title: str):
    print(f"\n\033[1m{'─'*62}\033[0m")
    print(f"\033[1m  {title}\033[0m")
    print(f"\033[1m{'─'*62}\033[0m")

def no_error(name: str, result) -> bool:
    if isinstance(result, dict) and "error" in result:
        return check(name, False, f"error={result['error']}")
    if isinstance(result, list) and len(result) == 1 and isinstance(result[0], dict) and "error" in result[0]:
        return check(name, False, f"error={result[0]['error']}")
    return check(name, True)

# ---------------------------------------------------------------------------
# Step 1 — Build graph.json from ~/hc-cdaio-kg
# ---------------------------------------------------------------------------

def build_graph(tmp_dir: Path) -> Path:
    import importlib.util
    spec = importlib.util.spec_from_file_location("kg_build", LIB / "kg-build.py")
    build_mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(build_mod)

    data_dir = Path.home() / "hc-cdaio-kg"
    if not data_dir.exists():
        sys.exit(f"ERROR: {data_dir} does not exist — run kg-setup-repo.sh first")

    graph_path = tmp_dir / "cdaio-graph.json"
    build_mod.build(data_dir, graph_path)
    return graph_path

# ---------------------------------------------------------------------------
# Step 2 — Set up MCP server
# ---------------------------------------------------------------------------

def setup_mcp():
    from domain.registry import EntityRegistry
    EntityRegistry.auto_discover()
    from mcp_server.server import mcp
    import mcp_server.state as state
    return mcp, state

def call_tool(mcp, tool_name: str, **kwargs):
    for tool in mcp._tool_manager._tools.values():
        if tool.name == tool_name:
            return tool.fn(**kwargs)
    raise ValueError(f"Tool '{tool_name}' not found in MCP registry")

# ===========================================================================
# TESTS
# ===========================================================================

def run(mcp, state, graph_path: Path):
    graph_str = str(graph_path)

    # -----------------------------------------------------------------------
    section("load_graph — load hc-cdaio-kg graph into MCP server")
    # -----------------------------------------------------------------------
    result = call_tool(mcp, "load_graph_tool", path=graph_str)
    no_error("load_graph returns no error", result)
    check("load_graph entity_count == 2908",
          result.get("entity_count") == 2908,
          f"got: {result.get('entity_count')}")
    check("load_graph relationship_count == 6023",
          result.get("relationship_count") == 6023,
          f"got: {result.get('relationship_count')}")
    check("load_graph reports 26 entity types",
          len(result.get("entity_types", {})) == 26,
          f"got: {len(result.get('entity_types', {}))}")

    # -----------------------------------------------------------------------
    section("get_statistics — basic graph stats")
    # -----------------------------------------------------------------------
    stats = call_tool(mcp, "get_statistics")
    no_error("get_statistics returns no error", stats)
    check("statistics entity_count correct",
          stats.get("entity_count") == 2908,
          f"got: {stats.get('entity_count')}")
    check("statistics relationship_count correct",
          stats.get("relationship_count") == 6023,
          f"got: {stats.get('relationship_count')}")
    check("statistics has density field",
          "density" in stats)
    check("statistics has is_weakly_connected field",
          "is_weakly_connected" in stats)

    # -----------------------------------------------------------------------
    section("list_entities — paging and type filtering")
    # -----------------------------------------------------------------------
    all_ents = call_tool(mcp, "list_entities", entity_type="", limit=50)
    no_error("list_entities (all types) returns no error", all_ents)
    check("list_entities returns up to 50 results",
          isinstance(all_ents, list) and 1 <= len(all_ents) <= 50,
          f"got: {len(all_ents)}")

    persons = call_tool(mcp, "list_entities", entity_type="person", limit=200)
    no_error("list_entities(person) returns no error", persons)
    check("list_entities(person) returns 100 persons",
          len(persons) == 100,
          f"got: {len(persons)}")
    check("list_entities(person) entities have entity_type=person",
          all(e.get("entity_type") == "person" for e in persons))

    systems = call_tool(mcp, "list_entities", entity_type="system", limit=200)
    no_error("list_entities(system) returns no error", systems)
    check("list_entities(system) returns 164 systems",
          len(systems) == 164,
          f"got: {len(systems)}")

    # Invalid type should return error (validation rejects unknown types)
    bad_type = call_tool(mcp, "list_entities", entity_type="nonexistent_type_xyz", limit=10)
    check("list_entities(invalid_type) returns error for unknown type",
          (isinstance(bad_type, list) and bad_type and "error" in bad_type[0])
          or (isinstance(bad_type, dict) and "error" in bad_type),
          f"got: {bad_type!r}")

    # -----------------------------------------------------------------------
    section("get_entity — retrieve specific entities")
    # -----------------------------------------------------------------------
    # Pick a known ID from the persons list
    known_person = persons[0]
    person_id = known_person["id"]

    entity = call_tool(mcp, "get_entity", entity_id=person_id)
    no_error("get_entity(known id) returns no error", entity)
    check("get_entity returns correct entity",
          entity.get("id") == person_id,
          f"expected {person_id}, got {entity.get('id')}")

    # Unknown ID should return error dict
    unknown = call_tool(mcp, "get_entity", entity_id="does-not-exist-xyz")
    check("get_entity(unknown id) returns error dict",
          isinstance(unknown, dict) and "error" in unknown,
          f"got: {unknown!r}")

    # -----------------------------------------------------------------------
    section("search_entities — fuzzy name search")
    # -----------------------------------------------------------------------
    # Use part of a known entity name
    known_name = known_person.get("name", "")
    if known_name:
        search_q = known_name[:6]   # first 6 chars of name
        results = call_tool(mcp, "search_entities", query=search_q, entity_type="", limit=5)
        no_error("search_entities returns no error", results)
        check("search_entities returns at least 1 result",
              isinstance(results, list) and len(results) >= 1,
              f"query={search_q!r}, got {len(results)} results")
        check("search_entities top result has match_score",
              "match_score" in results[0] if results else False)

    # Type-filtered search
    sys_results = call_tool(mcp, "search_entities", query="service", entity_type="system", limit=10)
    no_error("search_entities(type=system) returns no error", sys_results)
    check("search_entities with entity_type filter returns only systems",
          all(r.get("entity_type") == "system" for r in sys_results),
          f"types found: {set(r.get('entity_type') for r in sys_results)}")

    # -----------------------------------------------------------------------
    section("get_neighbors — entity connectivity")
    # -----------------------------------------------------------------------
    neighbors = call_tool(mcp, "get_neighbors", entity_id=person_id, direction="both")
    no_error("get_neighbors(both) returns no error", neighbors)
    check("get_neighbors returns a list",
          isinstance(neighbors, list))
    if neighbors:
        check("get_neighbors each item has entity and relationships",
              all("entity" in n and "relationships" in n for n in neighbors),
              f"first item keys: {list(neighbors[0].keys()) if neighbors else []}")

    out_nbrs = call_tool(mcp, "get_neighbors", entity_id=person_id, direction="out")
    no_error("get_neighbors(out) returns no error", out_nbrs)
    in_nbrs = call_tool(mcp, "get_neighbors", entity_id=person_id, direction="in")
    no_error("get_neighbors(in) returns no error", in_nbrs)

    # Unknown entity
    bad_nbrs = call_tool(mcp, "get_neighbors", entity_id="ghost-id-xyz", direction="both")
    check("get_neighbors(unknown id) returns error or empty list",
          (isinstance(bad_nbrs, dict) and "error" in bad_nbrs) or bad_nbrs == [],
          f"got: {bad_nbrs!r}")

    # -----------------------------------------------------------------------
    section("find_shortest_path — graph traversal")
    # -----------------------------------------------------------------------
    # Pick two different entities
    src_id = persons[0]["id"]
    tgt_id = systems[0]["id"]

    path_result = call_tool(mcp, "find_shortest_path", source_id=src_id, target_id=tgt_id)
    check("find_shortest_path returns a dict (path or no-path-found)",
          isinstance(path_result, dict),
          f"got: {type(path_result)}")
    check("find_shortest_path result has 'path' key or error key",
          "path" in path_result or "error" in path_result,
          f"keys: {list(path_result.keys()) if isinstance(path_result, dict) else type(path_result)}")

    # Same → same: path of length 1
    self_path = call_tool(mcp, "find_shortest_path", source_id=src_id, target_id=src_id)
    no_error("find_shortest_path(self→self) no error", self_path)

    # -----------------------------------------------------------------------
    section("get_blast_radius — impact analysis")
    # -----------------------------------------------------------------------
    blast = call_tool(mcp, "get_blast_radius", entity_id=systems[0]["id"], max_depth=2)
    no_error("get_blast_radius returns no error", blast)
    check("get_blast_radius has 'total_affected' key",
          "total_affected" in blast,
          f"keys: {list(blast.keys()) if isinstance(blast, dict) else type(blast)}")
    check("get_blast_radius total_affected >= 0",
          isinstance(blast.get("total_affected"), int) and blast["total_affected"] >= 0,
          f"total_affected={blast.get('total_affected')}")

    # -----------------------------------------------------------------------
    section("compute_centrality — degree, betweenness, pagerank")
    # -----------------------------------------------------------------------
    for metric in ("degree", "betweenness", "pagerank"):
        cent = call_tool(mcp, "compute_centrality", metric=metric)
        no_error(f"compute_centrality({metric}) no error", cent)
        check(f"compute_centrality({metric}) returns up to 20 entities",
              isinstance(cent, list) and 0 < len(cent) <= 20,
              f"got: {len(cent)}")
        check(f"compute_centrality({metric}) each item has score",
              all("score" in e for e in cent),
              f"first: {cent[0] if cent else {}}")

    # Invalid metric
    bad_cent = call_tool(mcp, "compute_centrality", metric="invalid_metric_xyz")
    check("compute_centrality(invalid metric) returns error",
          (isinstance(bad_cent, dict) and "error" in bad_cent)
          or (isinstance(bad_cent, list) and bad_cent and "error" in bad_cent[0]),
          f"got: {bad_cent!r}")

    # -----------------------------------------------------------------------
    section("find_most_connected — hub detection")
    # -----------------------------------------------------------------------
    hubs = call_tool(mcp, "find_most_connected", top_n=10)
    no_error("find_most_connected(top_n=10) no error", hubs)
    check("find_most_connected returns 10 entities",
          isinstance(hubs, list) and len(hubs) == 10,
          f"got: {len(hubs)}")
    check("find_most_connected entities have degree field",
          all("degree" in e for e in hubs))
    check("find_most_connected is sorted descending by degree",
          all(hubs[i]["degree"] >= hubs[i+1]["degree"] for i in range(len(hubs)-1)))

    # -----------------------------------------------------------------------
    section("add_entity_tool — write: create new entity")
    # -----------------------------------------------------------------------
    new_ent = call_tool(mcp, "add_entity_tool",
                        entity_type="vendor",
                        name="Acme Test Vendor",
                        description="Auto-generated by integration test")
    no_error("add_entity_tool returns no error", new_ent)
    new_id = new_ent.get("entity_id", "")
    check("add_entity_tool returns entity with id",
          bool(new_id),
          f"got: {new_ent!r}")
    check("add_entity_tool entity is retrievable via get_entity",
          call_tool(mcp, "get_entity", entity_id=new_id).get("id") == new_id)

    # Invalid type
    bad_ent = call_tool(mcp, "add_entity_tool",
                        entity_type="not_a_real_type_xyz",
                        name="Bad Entity")
    check("add_entity_tool(invalid type) returns error",
          isinstance(bad_ent, dict) and "error" in bad_ent,
          f"got: {bad_ent!r}")

    # -----------------------------------------------------------------------
    section("update_entity_tool — write: modify existing entity")
    # -----------------------------------------------------------------------
    updated = call_tool(mcp, "update_entity_tool",
                        entity_id=new_id,
                        updates={"name": "Acme Test Vendor UPDATED", "description": "Updated by test"})
    no_error("update_entity_tool returns no error", updated)
    check("update_entity_tool name change reflected",
          call_tool(mcp, "get_entity", entity_id=new_id).get("name") == "Acme Test Vendor UPDATED")

    # Update unknown entity
    bad_upd = call_tool(mcp, "update_entity_tool",
                        entity_id="ghost-id-for-update",
                        updates={"name": "Ghost"})
    check("update_entity_tool(unknown id) returns error",
          isinstance(bad_upd, dict) and "error" in bad_upd,
          f"got: {bad_upd!r}")

    # -----------------------------------------------------------------------
    section("add_relationship_tool — write: create relationship")
    # -----------------------------------------------------------------------
    anchor_id = systems[0]["id"]
    rel = call_tool(mcp, "add_relationship_tool",
                    relationship_type="supplied_by",
                    source_id=anchor_id,
                    target_id=new_id,
                    weight=0.9,
                    confidence=0.95)
    no_error("add_relationship_tool returns no error", rel)
    rel_id = rel.get("relationship_id", "")
    check("add_relationship_tool returns relationship with id",
          bool(rel_id),
          f"got: {rel!r}")
    check("add_relationship_tool relationship appears in get_neighbors",
          any(r.get("id") == rel_id
              for n in call_tool(mcp, "get_neighbors", entity_id=anchor_id, direction="out")
              if isinstance(n, dict) and "relationships" in n
              for r in n["relationships"]))

    # Invalid relationship type
    bad_rel = call_tool(mcp, "add_relationship_tool",
                        relationship_type="not_a_valid_rel_type",
                        source_id=anchor_id,
                        target_id=new_id)
    check("add_relationship_tool(invalid type) returns error",
          isinstance(bad_rel, dict) and "error" in bad_rel,
          f"got: {bad_rel!r}")

    # Non-existent source
    bad_src_rel = call_tool(mcp, "add_relationship_tool",
                            relationship_type="supplied_by",
                            source_id="ghost-src-id",
                            target_id=new_id)
    check("add_relationship_tool(unknown source) returns error",
          isinstance(bad_src_rel, dict) and "error" in bad_src_rel,
          f"got: {bad_src_rel!r}")

    # -----------------------------------------------------------------------
    section("add_relationships_batch — write: atomic batch")
    # -----------------------------------------------------------------------
    anchor2_id = systems[1]["id"]
    batch = call_tool(mcp, "add_relationships_batch", relationships=[
        {"relationship_type": "supplied_by", "source_id": anchor2_id, "target_id": new_id,
         "weight": 0.8},
        {"relationship_type": "depends_on",  "source_id": anchor_id,  "target_id": anchor2_id,
         "weight": 0.7},
    ])
    no_error("add_relationships_batch(valid) returns no error", batch)
    check("add_relationships_batch committed == 2",
          batch.get("committed") == 2,
          f"got: {batch!r}")

    # Batch with one invalid item — nothing should be written
    stats_before = call_tool(mcp, "get_statistics")
    rc_before = stats_before.get("relationship_count", 0)
    bad_batch = call_tool(mcp, "add_relationships_batch", relationships=[
        {"relationship_type": "depends_on", "source_id": anchor_id, "target_id": anchor2_id},
        {"relationship_type": "NOT_VALID",  "source_id": anchor_id, "target_id": anchor2_id},
    ])
    check("add_relationships_batch(one invalid) returns error",
          isinstance(bad_batch, dict) and (
              "error" in bad_batch or "errors" in bad_batch or bad_batch.get("status") == "error"
          ),
          f"got: {bad_batch!r}")
    rc_after = call_tool(mcp, "get_statistics").get("relationship_count", 0)
    check("add_relationships_batch(one invalid) is atomic — no partial write",
          rc_after == rc_before,
          f"before={rc_before}, after={rc_after}")

    # -----------------------------------------------------------------------
    section("remove_relationship_tool — write: delete relationship")
    # -----------------------------------------------------------------------
    removed_rel = call_tool(mcp, "remove_relationship_tool", relationship_id=rel_id)
    no_error("remove_relationship_tool returns no error", removed_rel)
    check("remove_relationship_tool removed_id matches",
          removed_rel.get("removed", {}).get("id") == rel_id,
          f"got: {removed_rel!r}")
    check("remove_relationship_tool relationship gone from get_neighbors",
          not any(r.get("id") == rel_id
                  for n in call_tool(mcp, "get_neighbors", entity_id=anchor_id, direction="out")
                  if isinstance(n, dict) and "relationships" in n
                  for r in n["relationships"]))

    # Remove unknown relationship
    bad_rem = call_tool(mcp, "remove_relationship_tool", relationship_id="ghost-rel-id")
    check("remove_relationship_tool(unknown id) returns error",
          isinstance(bad_rem, dict) and "error" in bad_rem,
          f"got: {bad_rem!r}")

    # -----------------------------------------------------------------------
    section("remove_entity_tool — write: delete entity")
    # -----------------------------------------------------------------------
    removed_ent = call_tool(mcp, "remove_entity_tool", entity_id=new_id)
    no_error("remove_entity_tool returns no error", removed_ent)
    check("remove_entity_tool removed entity is no longer retrievable",
          "error" in call_tool(mcp, "get_entity", entity_id=new_id))

    # Confirm entity count is back to original
    final_stats = call_tool(mcp, "get_statistics")
    check("entity count restored after add+remove cycle",
          final_stats.get("entity_count") == 2908,
          f"got: {final_stats.get('entity_count')}")

    # Remove unknown entity
    bad_re = call_tool(mcp, "remove_entity_tool", entity_id="ghost-ent-id")
    check("remove_entity_tool(unknown id) returns error",
          isinstance(bad_re, dict) and "error" in bad_re,
          f"got: {bad_re!r}")

    # -----------------------------------------------------------------------
    section("Summary")
    # -----------------------------------------------------------------------
    passed = sum(1 for _, ok, _ in _results if ok)
    failed = sum(1 for _, ok, _ in _results if not ok)
    total  = len(_results)
    print(f"\n  \033[1mTotal: {total}   Passed: \033[32m{passed}\033[0m\033[1m   Failed: \033[31m{failed}\033[0m")
    if failed:
        print("\n  \033[31mFailed tests:\033[0m")
        for name, ok, detail in _results:
            if not ok:
                print(f"    • {name}")
                if detail:
                    print(f"      {detail}")
    print()
    return failed


# ---------------------------------------------------------------------------
if __name__ == "__main__":
    print("\033[1mhc-cdaio-kg → hc-enterprise-kg MCP integration test\033[0m")

    with tempfile.TemporaryDirectory(prefix="kg-mcp-test-") as tmp:
        tmp_path = Path(tmp)

        print("\n  Building graph.json from ~/hc-cdaio-kg...")
        try:
            graph_path = build_graph(tmp_path)
        except Exception as e:
            sys.exit(f"ERROR building graph: {e}")

        g = json.loads(graph_path.read_text())
        print(f"  Built: {len(g['entities'])} entities, {len(g['relationships'])} relationships")

        print("  Loading MCP server...")
        try:
            mcp, state = setup_mcp()
        except Exception as e:
            traceback.print_exc()
            sys.exit(f"ERROR loading MCP server: {e}")

        failures = run(mcp, state, graph_path)

    sys.exit(1 if failures else 0)
