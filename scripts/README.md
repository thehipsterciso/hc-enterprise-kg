# scripts/ — Admin Tools (hc-enterprise-kg)

> **CMU CDAIO team member?**  The installer and workflow scripts now live in the
> **[hc-cdaio-kg](https://github.com/thehipsterciso/hc-cdaio-kg)** data repo.
> Set up your environment with just two commands:
>
> ```bash
> git clone https://github.com/thehipsterciso/hc-cdaio-kg
> bash hc-cdaio-kg/scripts/install.sh
> ```

---

This folder contains **admin-only tools** for maintaining the hc-cdaio-kg
GitHub repository.  You only need these if you are the org admin.

## Admin tools

### `kg-setup-repo.sh` — Initial repo scaffold

Run once to create the hc-cdaio-kg GitHub repo, default labels, branch
protections, and initial per-type file structure.

```bash
bash scripts/kg-setup-repo.sh [<seed-graph.json>]
```

### `kg-add-member.sh` — Grant collaborator access

Run when a team member files a collaborator-request GitHub issue.

```bash
bash scripts/kg-add-member.sh <github-username>
```

## `lib/` — Python helpers (used by admin tools)

| File | Purpose |
|------|---------|
| `kg-build.py` | Assemble per-type JSON files → `graph.json` |
| `kg-split.py` | Split `graph.json` → per-type entity/relationship files |
| `kg-merge.py` | Merge helper used during PR review |

## Workflow scripts

The day-to-day workflow scripts (`kg-sync.sh`, `kg-eod.sh`, `kg-morning.sh`)
and the team member installer (`install.sh`) now live in
**hc-cdaio-kg/scripts/**.  Do not add them back here.
