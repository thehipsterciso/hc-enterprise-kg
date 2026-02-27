#!/usr/bin/env python3
"""
test-kg-pipeline.py — Scientific regression tests for kg-split / kg-build / kg-merge.

Usage:
    python3 scripts/test-kg-pipeline.py [path/to/graph.json]

Defaults to ~/hc-cdaio-kg/entities + relationships dirs (already-split data),
or accepts a raw graph.json to derive everything from.

Exit code: 0 = all pass, 1 = one or more failures.
"""

import copy
import json
import shutil
import sys
import tempfile
import traceback
from pathlib import Path

# ---------------------------------------------------------------------------
# Locate the lib scripts next to this file
# ---------------------------------------------------------------------------
LIB = Path(__file__).parent / "lib"
sys.path.insert(0, str(LIB))

# Import the three modules directly (no subprocess overhead, no PATH games)
import importlib.util

def _load(name: str):
    spec = importlib.util.spec_from_file_location(name, LIB / f"{name}.py")
    mod  = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod

split_mod = _load("kg-split")
build_mod = _load("kg-build")
merge_mod = _load("kg-merge")

# ---------------------------------------------------------------------------
# Tiny test harness
# ---------------------------------------------------------------------------
PASS = "\033[32m  PASS\033[0m"
FAIL = "\033[31m  FAIL\033[0m"
INFO = "\033[34m  INFO\033[0m"

_results: list[tuple[str, bool, str]] = []   # (name, passed, detail)

def check(name: str, condition: bool, detail: str = "") -> bool:
    tag = PASS if condition else FAIL
    print(f"{tag}  {name}")
    if detail:
        prefix = "        "
        for line in detail.splitlines():
            print(f"{prefix}{line}")
    _results.append((name, condition, detail))
    return condition

def section(title: str):
    print(f"\n\033[1m{'─'*60}\033[0m")
    print(f"\033[1m  {title}\033[0m")
    print(f"\033[1m{'─'*60}\033[0m")

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def load_split_dir(d: Path) -> tuple[dict[str, dict], dict[tuple, dict]]:
    """Load per-type files → {id: entity}, {(src,tgt,type): rel}"""
    entities: dict[str, dict] = {}
    rels: dict[tuple, dict]   = {}

    for f in sorted((d / "entities").glob("*.json")):
        for e in json.loads(f.read_text()):
            entities[e["id"]] = e

    for f in sorted((d / "relationships").glob("*.json")):
        for r in json.loads(f.read_text()):
            key = (r["source_id"], r["target_id"], r["relationship_type"])
            rels[key] = r

    return entities, rels


def write_split_dir(entities: list[dict], rels: list[dict], d: Path):
    """Write per-type files exactly as kg-split does."""
    from collections import defaultdict
    by_e: dict[str, list] = defaultdict(list)
    for e in entities:
        by_e[e["entity_type"]].append(e)
    (d / "entities").mkdir(parents=True, exist_ok=True)
    for t, lst in sorted(by_e.items()):
        (d / "entities" / f"{t}.json").write_text(json.dumps(lst, indent=2) + "\n")

    by_r: dict[str, list] = defaultdict(list)
    for r in rels:
        by_r[r["relationship_type"]].append(r)
    (d / "relationships").mkdir(parents=True, exist_ok=True)
    for t, lst in sorted(by_r.items()):
        (d / "relationships" / f"{t}.json").write_text(json.dumps(lst, indent=2) + "\n")


# ---------------------------------------------------------------------------
# Load source graph
# ---------------------------------------------------------------------------

def load_source(arg: str | None) -> tuple[list[dict], list[dict]]:
    """Return (entities, relationships) from graph.json or hc-cdaio-kg dir."""
    if arg:
        p = Path(arg)
        if p.is_file():
            g = json.loads(p.read_text())
            return g["entities"], g["relationships"]
        if p.is_dir() and (p / "entities").exists():
            ents, rels_idx = load_split_dir(p)
            return list(ents.values()), list(rels_idx.values())
        sys.exit(f"ERROR: {arg} is not a graph.json or split directory")

    # Default: ~/hc-cdaio-kg
    default = Path.home() / "hc-cdaio-kg"
    if default.exists():
        ents, rels_idx = load_split_dir(default)
        return list(ents.values()), list(rels_idx.values())

    sys.exit("ERROR: no graph source found. Pass a graph.json path.")


# ===========================================================================
# TEST SUITE
# ===========================================================================

def run_tests(src_entities: list[dict], src_rels: list[dict]):
    tmp = Path(tempfile.mkdtemp(prefix="kg-test-"))
    try:
        _run(tmp, src_entities, src_rels)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def _run(tmp: Path, src_entities: list[dict], src_rels: list[dict]):
    n_e = len(src_entities)
    n_r = len(src_rels)
    print(f"\n{INFO}  Source: {n_e} entities, {n_r} relationships")

    # -----------------------------------------------------------------------
    # SECTION 1 — Round-trip: split then build
    # -----------------------------------------------------------------------
    section("Round-trip: split → build")

    graph_in  = tmp / "source.json"
    split_out = tmp / "split"
    graph_out = tmp / "rebuilt.json"

    graph_in.write_text(json.dumps({"entities": src_entities, "relationships": src_rels}, indent=2))

    # Run split
    try:
        split_mod.split(graph_in, split_out)
        split_ok = True
    except SystemExit as e:
        split_ok = False
    check("split completes without error", split_ok)

    # Correct number of per-type files
    e_files = list((split_out / "entities").glob("*.json"))
    r_files = list((split_out / "relationships").glob("*.json"))
    e_types  = {e["entity_type"] for e in src_entities}
    r_types  = {r["relationship_type"] for r in src_rels}
    check("entity file count == distinct entity_types",
          len(e_files) == len(e_types),
          f"files={len(e_files)}, types={len(e_types)}")
    check("relationship file count == distinct relationship_types",
          len(r_files) == len(r_types),
          f"files={len(r_files)}, types={len(r_types)}")

    # Run build
    try:
        build_mod.build(split_out, graph_out)
        build_ok = True
    except Exception:
        build_ok = False
    check("build completes without error", build_ok)

    rebuilt = json.loads(graph_out.read_text())
    rebuilt_e = rebuilt["entities"]
    rebuilt_r = rebuilt["relationships"]

    # Count fidelity
    check("entity count preserved after round-trip",
          len(rebuilt_e) == n_e,
          f"original={n_e}, rebuilt={len(rebuilt_e)}")
    check("relationship count preserved after round-trip",
          len(rebuilt_r) == n_r,
          f"original={n_r}, rebuilt={len(rebuilt_r)}")

    # ID set fidelity
    orig_eids     = {e["id"] for e in src_entities}
    rebuilt_eids  = {e["id"] for e in rebuilt_e}
    missing_eids  = orig_eids - rebuilt_eids
    extra_eids    = rebuilt_eids - orig_eids
    check("no entity IDs lost after round-trip",
          not missing_eids,
          f"missing={len(missing_eids)}: {list(missing_eids)[:5]}" if missing_eids else "")
    check("no phantom entity IDs added after round-trip",
          not extra_eids,
          f"extra={len(extra_eids)}: {list(extra_eids)[:5]}" if extra_eids else "")

    # Relationship key-set fidelity
    orig_rkeys    = {(r["source_id"], r["target_id"], r["relationship_type"]) for r in src_rels}
    rebuilt_rkeys = {(r["source_id"], r["target_id"], r["relationship_type"]) for r in rebuilt_r}
    missing_rkeys = orig_rkeys - rebuilt_rkeys
    extra_rkeys   = rebuilt_rkeys - orig_rkeys
    check("no relationship keys lost after round-trip",
          not missing_rkeys,
          f"missing={len(missing_rkeys)}" if missing_rkeys else "")
    check("no phantom relationship keys added after round-trip",
          not extra_rkeys,
          f"extra={len(extra_rkeys)}" if extra_rkeys else "")

    # Deep field fidelity — every entity record is byte-for-byte identical
    orig_by_id    = {e["id"]: e for e in src_entities}
    rebuilt_by_id = {e["id"]: e for e in rebuilt_e}
    field_diffs = [
        eid for eid in (orig_eids & rebuilt_eids)
        if orig_by_id[eid] != rebuilt_by_id[eid]
    ]
    check("all entity field data preserved (deep equality)",
          not field_diffs,
          f"{len(field_diffs)} entities differ: {field_diffs[:3]}" if field_diffs else "")

    orig_rkey_to_rel    = {(r["source_id"], r["target_id"], r["relationship_type"]): r for r in src_rels}
    rebuilt_rkey_to_rel = {(r["source_id"], r["target_id"], r["relationship_type"]): r for r in rebuilt_r}
    rel_diffs = [
        k for k in (orig_rkeys & rebuilt_rkeys)
        if orig_rkey_to_rel[k] != rebuilt_rkey_to_rel[k]
    ]
    check("all relationship field data preserved (deep equality)",
          not rel_diffs,
          f"{len(rel_diffs)} relationships differ: {list(rel_diffs)[:3]}" if rel_diffs else "")

    # -----------------------------------------------------------------------
    # SECTION 2 — Merge: additive (branch adds new entities)
    # -----------------------------------------------------------------------
    section("Merge: additive — branch-only entities and relationships")

    base_dir   = tmp / "merge_base"
    branch_dir = tmp / "merge_branch"
    merged_dir = tmp / "merge_out_additive"

    # Base = first half; branch = second half (completely disjoint IDs)
    half = n_e // 2
    half_r = n_r // 2
    base_e   = src_entities[:half]
    branch_e = src_entities[half:]
    base_r   = src_rels[:half_r]
    branch_r = src_rels[half_r:]

    write_split_dir(base_e, base_r, base_dir)
    write_split_dir(branch_e, branch_r, branch_dir)

    try:
        merge_mod.merge(base_dir, branch_dir, merged_dir)
        merge_ok = True
    except Exception:
        merge_ok = False
    check("merge (additive) completes without error", merge_ok)

    if merge_ok:
        m_ents, m_rels = load_split_dir(merged_dir)

        base_ids   = {e["id"] for e in base_e}
        branch_ids = {e["id"] for e in branch_e}

        check("merged entity count == base + branch (no duplicates)",
              len(m_ents) == n_e,
              f"expected={n_e}, got={len(m_ents)}")
        check("all base entity IDs present in merge",
              base_ids <= set(m_ents.keys()),
              f"missing from base: {base_ids - set(m_ents.keys())}")
        check("all branch entity IDs present in merge",
              branch_ids <= set(m_ents.keys()),
              f"missing from branch: {branch_ids - set(m_ents.keys())}")

        base_rkeys   = {(r["source_id"], r["target_id"], r["relationship_type"]) for r in base_r}
        branch_rkeys = {(r["source_id"], r["target_id"], r["relationship_type"]) for r in branch_r}
        all_rkeys    = base_rkeys | branch_rkeys
        check("merged relationship count == union of base + branch",
              len(m_rels) == len(all_rkeys),
              f"expected={len(all_rkeys)}, got={len(m_rels)}")

    # -----------------------------------------------------------------------
    # SECTION 3 — Merge: conflict resolution (branch wins)
    # -----------------------------------------------------------------------
    section("Merge: conflict — same entity ID modified in branch wins")

    conflict_base_dir   = tmp / "conflict_base"
    conflict_branch_dir = tmp / "conflict_branch"
    conflict_out_dir    = tmp / "conflict_out"

    # Use 20 entities; modify 5 of them in branch
    sample = src_entities[:20]
    sample_r = src_rels[:10]
    CONFLICT_COUNT = 5
    modified = copy.deepcopy(sample[:CONFLICT_COUNT])
    for e in modified:
        e["name"] = e["name"] + " [BRANCH EDIT]"

    base_sample   = sample                         # original
    branch_sample = modified + sample[CONFLICT_COUNT:]  # 5 modified + rest same

    write_split_dir(base_sample, sample_r, conflict_base_dir)
    write_split_dir(branch_sample, sample_r, conflict_branch_dir)

    try:
        merge_mod.merge(conflict_base_dir, conflict_branch_dir, conflict_out_dir)
        conflict_ok = True
    except Exception:
        conflict_ok = False
    check("merge (conflict) completes without error", conflict_ok)

    if conflict_ok:
        c_ents, _ = load_split_dir(conflict_out_dir)

        # Branch-modified entities must be the winners
        branch_wins = all(
            c_ents[e["id"]]["name"].endswith("[BRANCH EDIT]")
            for e in modified
            if e["id"] in c_ents
        )
        check("branch version wins on conflicting entity IDs",
              branch_wins)

        # Unmodified entities should be byte-for-bit identical to originals
        orig_unchanged = {e["id"]: e for e in sample[CONFLICT_COUNT:]}
        unchanged_ok = all(
            c_ents.get(eid) == orig_unchanged[eid]
            for eid in orig_unchanged
        )
        check("non-conflicting entities unchanged after merge",
              unchanged_ok)

        check("total entity count correct after conflict merge",
              len(c_ents) == len(sample),
              f"expected={len(sample)}, got={len(c_ents)}")

    # -----------------------------------------------------------------------
    # SECTION 4 — Merge: relationship deduplication
    # -----------------------------------------------------------------------
    section("Merge: relationship deduplication — same key in both → exactly once")

    dedup_base_dir   = tmp / "dedup_base"
    dedup_branch_dir = tmp / "dedup_branch"
    dedup_out_dir    = tmp / "dedup_out"

    sample_r10 = src_rels[:10]
    # Branch has identical relationships PLUS 5 extra with a modified weight
    branch_r_modified = copy.deepcopy(sample_r10)
    for r in branch_r_modified[:5]:
        r["weight"] = 0.99   # mutate so they're "different" but same key

    write_split_dir(src_entities[:5], sample_r10, dedup_base_dir)
    write_split_dir(src_entities[:5], branch_r_modified, dedup_branch_dir)

    try:
        merge_mod.merge(dedup_base_dir, dedup_branch_dir, dedup_out_dir)
        dedup_ok = True
    except Exception:
        dedup_ok = False
    check("merge (dedup) completes without error", dedup_ok)

    if dedup_ok:
        _, d_rels = load_split_dir(dedup_out_dir)
        expected_count = len({
            (r["source_id"], r["target_id"], r["relationship_type"])
            for r in sample_r10
        })
        check("duplicate relationship keys appear exactly once",
              len(d_rels) == expected_count,
              f"expected={expected_count}, got={len(d_rels)}")

        # Branch-modified rels should be the winners (weight=0.99)
        branch_key_to_rel = {
            (r["source_id"], r["target_id"], r["relationship_type"]): r
            for r in branch_r_modified
        }
        branch_rel_wins = all(
            d_rels[k].get("weight") == branch_key_to_rel[k].get("weight")
            for k in list(branch_key_to_rel.keys())[:5]
            if k in d_rels
        )
        check("branch relationship version wins on duplicate keys",
              branch_rel_wins)

    # -----------------------------------------------------------------------
    # SECTION 5 — Merge: identity (merge with self == self)
    # -----------------------------------------------------------------------
    section("Merge: identity — merge(X, X) == X")

    self_dir = tmp / "self_merge_base"
    self_out = tmp / "self_merge_out"

    write_split_dir(src_entities[:50], src_rels[:50], self_dir)
    merge_mod.merge(self_dir, self_dir, self_out)

    s_ents, s_rels = load_split_dir(self_out)
    orig_s_ents, orig_s_rels = load_split_dir(self_dir)

    check("merge(X, X) entity count == |X|",
          len(s_ents) == len(orig_s_ents),
          f"expected={len(orig_s_ents)}, got={len(s_ents)}")
    check("merge(X, X) relationship count == |X|",
          len(s_rels) == len(orig_s_rels),
          f"expected={len(orig_s_rels)}, got={len(s_rels)}")
    check("merge(X, X) all entity IDs preserved",
          set(s_ents.keys()) == set(orig_s_ents.keys()))

    # -----------------------------------------------------------------------
    # SECTION 6 — ADVERSARIAL: edge cases designed to break things
    # -----------------------------------------------------------------------
    section("ADVERSARIAL: empty graph → split and build")

    empty_graph = tmp / "empty.json"
    empty_split = tmp / "empty_split"
    empty_built = tmp / "empty_built.json"
    empty_graph.write_text(json.dumps({"entities": [], "relationships": []}, indent=2))
    try:
        split_mod.split(empty_graph, empty_split)
        build_mod.build(empty_split, empty_built)
        adv_empty_ok = True
        rebuilt_empty = json.loads(empty_built.read_text())
    except Exception as e:
        adv_empty_ok = False
        rebuilt_empty = {}
    check("ADVERSARIAL: empty graph round-trips without error", adv_empty_ok)
    check("ADVERSARIAL: empty graph produces zero entities",
          rebuilt_empty.get("entities", []) == [],
          f"got: {rebuilt_empty.get('entities', [])[:3]}")
    check("ADVERSARIAL: empty graph produces zero relationships",
          rebuilt_empty.get("relationships", []) == [],
          f"got: {rebuilt_empty.get('relationships', [])[:3]}")

    section("ADVERSARIAL: entity with missing entity_type field")

    bad_e = [
        {"id": "bad-001", "name": "No Type Entity"},          # missing entity_type
        {"id": "bad-002", "entity_type": "person", "name": "Good"},
    ]
    bad_graph = tmp / "bad_type.json"
    bad_split = tmp / "bad_split"
    bad_built = tmp / "bad_built.json"
    bad_graph.write_text(json.dumps({"entities": bad_e, "relationships": []}, indent=2))
    try:
        split_mod.split(bad_graph, bad_split)
        build_mod.build(bad_split, bad_built)
        adv_type_ok = True
        rebuilt_bad = json.loads(bad_built.read_text())
    except Exception:
        adv_type_ok = False
        rebuilt_bad = {}
    check("ADVERSARIAL: missing entity_type doesn't crash split/build", adv_type_ok)
    if adv_type_ok:
        rebuilt_ids = {e["id"] for e in rebuilt_bad.get("entities", [])}
        check("ADVERSARIAL: entity with missing entity_type survives round-trip",
              "bad-001" in rebuilt_ids,
              f"ids present: {rebuilt_ids}")

    section("ADVERSARIAL: duplicate entity IDs in source graph")

    dup_e = [
        {"id": "dup-001", "entity_type": "person", "name": "First"},
        {"id": "dup-001", "entity_type": "person", "name": "Second"},  # same ID
        {"id": "dup-002", "entity_type": "person", "name": "Unique"},
    ]
    dup_graph = tmp / "dup.json"
    dup_split = tmp / "dup_split"
    dup_built = tmp / "dup_built.json"
    dup_graph.write_text(json.dumps({"entities": dup_e, "relationships": []}, indent=2))
    try:
        split_mod.split(dup_graph, dup_split)
        build_mod.build(dup_split, dup_built)
        adv_dup_ok = True
        rebuilt_dup = json.loads(dup_built.read_text())
    except Exception:
        adv_dup_ok = False
        rebuilt_dup = {}
    check("ADVERSARIAL: duplicate IDs don't crash split/build", adv_dup_ok)
    if adv_dup_ok:
        # Both copies should be preserved by split (it doesn't deduplicate)
        dup_ids = [e["id"] for e in rebuilt_dup.get("entities", [])]
        check("ADVERSARIAL: duplicate ID entries preserved in split/build (no silent dedup)",
              dup_ids.count("dup-001") == 2,
              f"count of dup-001: {dup_ids.count('dup-001')} (expected 2 — split is not a deduplicator)")

    section("ADVERSARIAL: merge with empty branch → result equals base")

    nonempty_base = tmp / "nonempty_base"
    empty_branch  = tmp / "empty_branch"
    base_vs_empty = tmp / "base_vs_empty_out"

    sample10 = src_entities[:10]
    sample_r5 = src_rels[:5]
    write_split_dir(sample10, sample_r5, nonempty_base)
    # empty branch: create dirs but no files
    (empty_branch / "entities").mkdir(parents=True, exist_ok=True)
    (empty_branch / "relationships").mkdir(parents=True, exist_ok=True)

    try:
        merge_mod.merge(nonempty_base, empty_branch, base_vs_empty)
        adv_empty_branch_ok = True
    except Exception:
        adv_empty_branch_ok = False
    check("ADVERSARIAL: merge(base, empty_branch) completes without error", adv_empty_branch_ok)
    if adv_empty_branch_ok:
        bve_ents, bve_rels = load_split_dir(base_vs_empty)
        orig_ents, orig_rels = load_split_dir(nonempty_base)
        check("ADVERSARIAL: merge(base, empty) entity count == base",
              len(bve_ents) == len(orig_ents),
              f"expected={len(orig_ents)}, got={len(bve_ents)}")
        check("ADVERSARIAL: merge(base, empty) all base entity IDs present",
              set(bve_ents.keys()) == set(orig_ents.keys()))

    section("ADVERSARIAL: merge with empty base → result equals branch")

    empty_base2  = tmp / "empty_base2"
    full_branch2 = tmp / "full_branch2"
    empty_vs_full = tmp / "empty_vs_full_out"

    (empty_base2 / "entities").mkdir(parents=True, exist_ok=True)
    (empty_base2 / "relationships").mkdir(parents=True, exist_ok=True)
    write_split_dir(sample10, sample_r5, full_branch2)

    try:
        merge_mod.merge(empty_base2, full_branch2, empty_vs_full)
        adv_empty_base_ok = True
    except Exception:
        adv_empty_base_ok = False
    check("ADVERSARIAL: merge(empty_base, branch) completes without error", adv_empty_base_ok)
    if adv_empty_base_ok:
        evf_ents, evf_rels = load_split_dir(empty_vs_full)
        check("ADVERSARIAL: merge(empty, branch) entity count == branch",
              len(evf_ents) == len(sample10),
              f"expected={len(sample10)}, got={len(evf_ents)}")

    section("ADVERSARIAL: unicode, nulls, and deep nesting survive round-trip")

    nasty_e = [
        {"id": "unicode-001", "entity_type": "person", "name": "日本語テスト 🔥 <>&\"'"},
        {"id": "null-001",    "entity_type": "system", "name": None, "description": None},
        {"id": "nested-001",  "entity_type": "policy", "name": "Deep",
         "meta": {"a": {"b": {"c": {"d": [1, 2, 3]}}}}},
    ]
    nasty_r = [
        {"id": "r-nasty-001", "source_id": "unicode-001", "target_id": "nested-001",
         "relationship_type": "governs", "weight": 1.0,
         "properties": {"note": "emoji 🎯 and <special> chars"}},
    ]
    nasty_graph = tmp / "nasty.json"
    nasty_split = tmp / "nasty_split"
    nasty_built = tmp / "nasty_built.json"
    nasty_graph.write_text(json.dumps({"entities": nasty_e, "relationships": nasty_r},
                                      indent=2, ensure_ascii=False))
    try:
        split_mod.split(nasty_graph, nasty_split)
        build_mod.build(nasty_split, nasty_built)
        adv_nasty_ok = True
        rebuilt_nasty = json.loads(nasty_built.read_text())
    except Exception as exc:
        adv_nasty_ok = False
        rebuilt_nasty = {}
    check("ADVERSARIAL: unicode/null/nested graph round-trips without error", adv_nasty_ok)
    if adv_nasty_ok:
        rebuilt_n_by_id = {e["id"]: e for e in rebuilt_nasty.get("entities", [])}
        check("ADVERSARIAL: unicode entity preserved exactly",
              rebuilt_n_by_id.get("unicode-001", {}).get("name") == "日本語テスト 🔥 <>&\"'")
        check("ADVERSARIAL: null field entity preserved exactly",
              rebuilt_n_by_id.get("null-001", {}).get("name") is None)
        check("ADVERSARIAL: deeply nested entity preserved exactly",
              rebuilt_n_by_id.get("nested-001", {}).get("meta") ==
              {"a": {"b": {"c": {"d": [1, 2, 3]}}}})

    section("ADVERSARIAL: corrupt JSON in one per-type file — build continues")

    corrupt_dir = tmp / "corrupt_split"
    (corrupt_dir / "entities").mkdir(parents=True, exist_ok=True)
    (corrupt_dir / "relationships").mkdir(parents=True, exist_ok=True)
    good_e = [{"id": "g-001", "entity_type": "person", "name": "Good"}]
    (corrupt_dir / "entities" / "person.json").write_text(json.dumps(good_e, indent=2))
    (corrupt_dir / "entities" / "system.json").write_text("THIS IS NOT JSON {{{")  # corrupt
    corrupt_built = tmp / "corrupt_built.json"
    try:
        import io, contextlib
        buf = io.StringIO()
        with contextlib.redirect_stderr(buf):
            build_mod.build(corrupt_dir, corrupt_built)
        adv_corrupt_ok = True
        rebuilt_corrupt = json.loads(corrupt_built.read_text())
        corrupt_warnings = buf.getvalue()
    except Exception:
        adv_corrupt_ok = False
        rebuilt_corrupt = {}
        corrupt_warnings = ""
    check("ADVERSARIAL: corrupt per-type file doesn't crash build (skips with warning)",
          adv_corrupt_ok)
    if adv_corrupt_ok:
        ids_in_corrupt = {e["id"] for e in rebuilt_corrupt.get("entities", [])}
        check("ADVERSARIAL: good entities still present when one file is corrupt",
              "g-001" in ids_in_corrupt)
        check("ADVERSARIAL: build emits a warning about corrupt file",
              "invalid JSON" in corrupt_warnings or "WARNING" in corrupt_warnings,
              f"stderr was: {corrupt_warnings!r}")

    section("ADVERSARIAL: relationship with missing keys survives split/build")

    stub_r = [
        {"id": "r-stub-001", "source_id": "x", "target_id": "y"},          # no relationship_type
        {"id": "r-stub-002", "relationship_type": "depends_on"},             # no source/target
        {"id": "r-stub-003", "source_id": "a", "target_id": "b",
         "relationship_type": "supports"},                                    # good
    ]
    stub_graph = tmp / "stub_r.json"
    stub_split = tmp / "stub_r_split"
    stub_built = tmp / "stub_r_built.json"
    stub_graph.write_text(json.dumps({"entities": [], "relationships": stub_r}, indent=2))
    try:
        split_mod.split(stub_graph, stub_split)
        build_mod.build(stub_split, stub_built)
        adv_stub_ok = True
        rebuilt_stub = json.loads(stub_built.read_text())
    except Exception:
        adv_stub_ok = False
        rebuilt_stub = {}
    check("ADVERSARIAL: relationships with missing keys don't crash split/build", adv_stub_ok)
    if adv_stub_ok:
        rebuilt_r_ids = {r.get("id") for r in rebuilt_stub.get("relationships", [])}
        check("ADVERSARIAL: all stub relationships (even malformed) preserved",
              {"r-stub-001", "r-stub-002", "r-stub-003"} <= rebuilt_r_ids,
              f"present: {rebuilt_r_ids}")

    section("ADVERSARIAL: single entity, single relationship — minimum viable graph")

    one_e = [{"id": "solo-001", "entity_type": "person", "name": "Solo"}]
    one_r = [{"id": "r-solo-001", "source_id": "solo-001", "target_id": "solo-001",
              "relationship_type": "reports_to"}]   # self-loop
    one_graph = tmp / "one.json"
    one_split = tmp / "one_split"
    one_built = tmp / "one_built.json"
    one_graph.write_text(json.dumps({"entities": one_e, "relationships": one_r}, indent=2))
    try:
        split_mod.split(one_graph, one_split)
        build_mod.build(one_split, one_built)
        adv_one_ok = True
        rebuilt_one = json.loads(one_built.read_text())
    except Exception:
        adv_one_ok = False
        rebuilt_one = {}
    check("ADVERSARIAL: single entity + self-loop relationship round-trips", adv_one_ok)
    if adv_one_ok:
        check("ADVERSARIAL: self-loop relationship preserved",
              len(rebuilt_one.get("relationships", [])) == 1)
        check("ADVERSARIAL: self-loop source_id == target_id preserved",
              rebuilt_one["relationships"][0]["source_id"] ==
              rebuilt_one["relationships"][0]["target_id"])

    section("ADVERSARIAL: merge — branch adds rel referencing base-only entity ID")

    cross_base   = tmp / "cross_base"
    cross_branch = tmp / "cross_branch"
    cross_out    = tmp / "cross_out"

    base_entity  = [{"id": "base-only-001", "entity_type": "system", "name": "Base System"}]
    branch_entity = [{"id": "branch-only-001", "entity_type": "vendor", "name": "Branch Vendor"}]
    cross_rel = [{"id": "r-cross-001", "source_id": "branch-only-001",
                  "target_id": "base-only-001", "relationship_type": "supplies"}]

    write_split_dir(base_entity, [], cross_base)
    write_split_dir(branch_entity, cross_rel, cross_branch)

    try:
        merge_mod.merge(cross_base, cross_branch, cross_out)
        adv_cross_ok = True
    except Exception:
        adv_cross_ok = False
    check("ADVERSARIAL: branch rel referencing base-only entity doesn't crash merge", adv_cross_ok)
    if adv_cross_ok:
        cx_ents, cx_rels = load_split_dir(cross_out)
        check("ADVERSARIAL: both base entity and branch entity present after cross-ref merge",
              "base-only-001" in cx_ents and "branch-only-001" in cx_ents,
              f"present: {set(cx_ents.keys())}")
        check("ADVERSARIAL: cross-ref relationship preserved in merge output",
              len(cx_rels) == 1)

    # -----------------------------------------------------------------------
    # Summary
    # -----------------------------------------------------------------------
    section("Summary")
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
    arg = sys.argv[1] if len(sys.argv) > 1 else None
    print("\033[1mkg-pipeline test suite\033[0m")
    src_e, src_r = load_source(arg)
    failures = run_tests(src_e, src_r)
    sys.exit(1 if failures else 0)
