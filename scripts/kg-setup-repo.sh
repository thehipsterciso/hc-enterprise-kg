#!/usr/bin/env bash
# kg-setup-repo.sh — One-time admin setup: create hc-cdaio-kg on GitHub.
#
# Usage:
#   bash kg-setup-repo.sh <graph.json-or-dir>
#
# What it does:
#   1. Verifies gh CLI is authenticated
#   2. Creates thehipsterciso/hc-cdaio-kg (private) on GitHub
#   3. Clones it locally to ~/hc-cdaio-kg
#   4. Splits the seed graph into per-type files
#   5. Adds .gitignore + .gitattributes
#   6. Commits and pushes to main
#   7. Enables branch protection on main (PRs required)
#
# Run this ONCE as the admin before any team members run their install scripts.

set -euo pipefail
IFS=$'\n\t'

# ── Constants ────────────────────────────────────────────────────────────────
REPO_NAME="hc-cdaio-kg"
REPO_OWNER="thehipsterciso"
REPO_FULL="${REPO_OWNER}/${REPO_NAME}"
DATA_DIR="${HOME}/${REPO_NAME}"
LIB_DIR="$(cd "$(dirname "$0")/lib" && pwd)"
PYTHON_CMD="${PYTHON_CMD:-python3}"

# ── Colours ──────────────────────────────────────────────────────────────────
if [[ -t 1 ]]; then
  GRN='\033[0;32m'; YLW='\033[0;33m'; RED='\033[0;31m'; BLD='\033[1m'; RST='\033[0m'
else
  GRN=''; YLW=''; RED=''; BLD=''; RST=''
fi

ok()   { printf "${GRN}  ✓${RST}  %s\n" "$*"; }
warn() { printf "${YLW}  !${RST}  %s\n" "$*"; }
die()  { printf "${RED}  ✗  %s${RST}\n" "$*" >&2; exit 1; }
hdr()  { printf "\n${BLD}[%s] %s${RST}\n" "$1" "$2"; }

# ── Args ─────────────────────────────────────────────────────────────────────
[[ $# -ne 1 ]] && die "Usage: kg-setup-repo.sh <graph.json or directory>"
SEED_SOURCE="$1"

# ── Step 1 — Verify gh CLI ───────────────────────────────────────────────────
hdr "1/7" "Verify GitHub CLI"
command -v gh &>/dev/null || die "gh CLI not found. Install from https://cli.github.com"
gh auth status &>/dev/null       || die "gh CLI not authenticated. Run: gh auth login"
GH_USER="$(gh api user --jq .login 2>/dev/null)" || die "Cannot fetch GitHub username"
ok "Authenticated as ${GH_USER}"

# ── Step 2 — Create repo ────────────────────────────────────────────────────
hdr "2/7" "Create ${REPO_FULL} on GitHub"
if gh repo view "${REPO_FULL}" &>/dev/null; then
  warn "Repo ${REPO_FULL} already exists — skipping creation"
else
  gh repo create "${REPO_FULL}" \
    --public \
    --description "hc-enterprise-kg data — CMU CDAIO team graph (per-type JSON)" \
    --clone=false
  ok "Created ${REPO_FULL} (public)"
fi

# ── Step 3 — Clone ──────────────────────────────────────────────────────────
hdr "3/7" "Clone to ${DATA_DIR}"
if [[ -d "${DATA_DIR}/.git" ]]; then
  warn "${DATA_DIR} already a git repo — skipping clone"
else
  [[ -e "${DATA_DIR}" ]] && die "${DATA_DIR} exists but is not a git repo. Remove it first."
  gh repo clone "${REPO_FULL}" "${DATA_DIR}"
  ok "Cloned to ${DATA_DIR}"
fi
cd "${DATA_DIR}" || die "Cannot enter ${DATA_DIR}"

# ── Step 4 — Split seed graph ────────────────────────────────────────────────
hdr "4/7" "Split seed graph into per-type files"
[[ -f "${LIB_DIR}/kg-split.py" ]]  || die "Missing ${LIB_DIR}/kg-split.py"
[[ -f "${LIB_DIR}/kg-build.py" ]]  || die "Missing ${LIB_DIR}/kg-build.py"

# Accept a single graph.json OR a directory of JSON files
if [[ -d "${SEED_SOURCE}" ]]; then
  # Directory of JSON files — import each one and merge
  _TMP_COMBINED="$(mktemp /tmp/kg-combined-XXXXXX.json)" \
    || die "Cannot create temp file"
  printf '{"entities":[],"relationships":[]}\n' > "${_TMP_COMBINED}"

  _count=0
  while IFS= read -r -d '' _jf; do
    "${PYTHON_CMD}" - <<PYMERGE
import json, sys
combined = json.loads(open("${_TMP_COMBINED}").read())
src      = json.loads(open("${_jf}").read())
if isinstance(src, dict):
    combined["entities"]      += src.get("entities", [])
    combined["relationships"] += src.get("relationships", [])
elif isinstance(src, list):
    # bare array — treat as entities
    combined["entities"] += src
open("${_TMP_COMBINED}", "w").write(json.dumps(combined, indent=2) + "\n")
PYMERGE
    (( _count++ )) || true
  done < <(find "${SEED_SOURCE}" -maxdepth 1 -name '*.json' -print0 | sort -z)

  ok "Merged ${_count} JSON file(s) from directory"
  SEED_JSON="${_TMP_COMBINED}"
else
  SEED_JSON="${SEED_SOURCE}"
  [[ -f "${SEED_JSON}" ]] || die "Seed file not found: ${SEED_JSON}"
fi

# Run the splitter
"${PYTHON_CMD}" "${LIB_DIR}/kg-split.py" "${SEED_JSON}" "${DATA_DIR}"
ok "Per-type files written to ${DATA_DIR}/entities/ and ${DATA_DIR}/relationships/"

# Cleanup temp file if used
[[ -n "${_TMP_COMBINED:-}" ]] && rm -f "${_TMP_COMBINED}"

# ── Step 5 — Scaffold repo files ─────────────────────────────────────────────
hdr "5/7" "Add .gitignore and .gitattributes"

cat > "${DATA_DIR}/.gitignore" <<'EOF'
# Assembled graph file — built locally by kg-morning.sh / kg-sync.sh
graph.json

# Editor / OS
.DS_Store
*.swp
*~
Thumbs.db
EOF

cat > "${DATA_DIR}/.gitattributes" <<'EOF'
# Treat all JSON files as text to get clean LF diffs
*.json  text eol=lf
EOF

cat > "${DATA_DIR}/README.md" <<EOF
# hc-cdaio-kg — CMU CDAIO Knowledge Graph Data

Per-entity-type and per-relationship-type JSON files for the
[hc-enterprise-kg](https://github.com/${REPO_OWNER}/hc-enterprise-kg) MCP server.

## Structure

\`\`\`
entities/
    person.json
    system.json
    department.json
    ...
relationships/
    works_in.json
    depends_on.json
    ...
\`\`\`

Each file is a JSON array of objects of that type.

## Workflow

| Time | Action |
|------|--------|
| 8 am | \`kg-morning.sh\` pulls main → rebuilds \`graph.json\` |
| every 30 min | \`kg-sync.sh\` splits graph → commits → pushes to your branch |
| 5 pm | \`kg-eod.sh\` final sync + opens PR to main |

## Admin

- **Add a new member:** \`bash kg-add-member.sh <github-username>\`
- **Merge branches:** review and merge PRs in GitHub

## graph.json

\`graph.json\` is **gitignored** and assembled locally.  To rebuild it:

\`\`\`bash
python3 ~/hc-cdaio-kg/scripts/lib/kg-build.py ~/hc-cdaio-kg ~/hc-cdaio-kg/graph.json
\`\`\`
EOF

ok "Repo scaffold files written"

# ── Step 6 — Initial commit ──────────────────────────────────────────────────
hdr "6/7" "Commit and push to main"
git -C "${DATA_DIR}" add .gitignore .gitattributes README.md entities/ relationships/ 2>/dev/null || true

if git -C "${DATA_DIR}" diff --cached --quiet; then
  warn "Nothing new to commit — repo already up to date"
else
  git -C "${DATA_DIR}" commit -m "feat: initial graph split — per-type entity and relationship files"
  git -C "${DATA_DIR}" push origin main
  ok "Pushed initial data to ${REPO_FULL} main"
fi

# ── Step 7 — Branch protection ───────────────────────────────────────────────
hdr "7/7" "Enable branch protection on main"
# Requires admin access; silently skip if gh API call fails (e.g. free-plan private repo)
if gh api \
  --method PUT \
  "repos/${REPO_FULL}/branches/main/protection" \
  --field required_status_checks=null \
  --field enforce_admins=false \
  --field 'required_pull_request_reviews={"required_approving_review_count":1}' \
  --field restrictions=null \
  &>/dev/null; then
  ok "Branch protection enabled — PRs required to merge to main"
else
  warn "Could not set branch protection (may require GitHub Pro for private repos)"
  warn "You can set it manually: https://github.com/${REPO_FULL}/settings/branches"
fi

# ── Ensure collaborator-request label exists on hc-cdaio-kg ──────────────────
# Team member installers file issues here when requesting access.
gh label create "collaborator-request" \
  --repo "${REPO_FULL}" \
  --description "New team member requesting hc-cdaio-kg access" \
  --color "0075ca" \
  &>/dev/null || true  # idempotent
ok "collaborator-request label ready on ${REPO_FULL}"

# ── Done ────────────────────────────────────────────────────────────────────
printf "\n${GRN}${BLD}Setup complete!${RST}\n"
printf "  Repo  : https://github.com/${REPO_FULL}\n"
printf "  Local : %s\n" "${DATA_DIR}"
printf "\nNext steps:\n"
printf "  Add team members : bash %s/kg-add-member.sh <github-username>\n" "$(dirname "$0")"
printf "  Team member install : bash %s/cmu-cdaio-install.sh <graph-source>\n" "$(dirname "$0")"
