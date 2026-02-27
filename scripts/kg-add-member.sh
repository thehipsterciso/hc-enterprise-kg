#!/usr/bin/env bash
# kg-add-member.sh — Add a GitHub collaborator to hc-cdaio-kg and create their branch.
#
# Usage:
#   bash kg-add-member.sh <github-username>
#
# What it does:
#   1. Invites <github-username> as a collaborator (write access)
#   2. Creates a personal branch <github-username>/data off main
#   3. Pushes the branch to origin so the team member can clone it
#
# Run this once per team member BEFORE they run cmu-cdaio-install.sh.

set -euo pipefail
IFS=$'\n\t'

REPO_OWNER="thehipsterciso"
REPO_NAME="hc-cdaio-kg"
REPO_FULL="${REPO_OWNER}/${REPO_NAME}"
DATA_DIR="${HOME}/${REPO_NAME}"

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
[[ $# -ne 1 ]] && die "Usage: kg-add-member.sh <github-username>"
MEMBER="$1"
BRANCH="${MEMBER}/data"

# ── Sanity checks ────────────────────────────────────────────────────────────
command -v gh &>/dev/null || die "gh CLI not found"
gh auth status &>/dev/null || die "gh CLI not authenticated — run: gh auth login"
gh repo view "${REPO_FULL}" &>/dev/null || die "Repo ${REPO_FULL} not found. Run kg-setup-repo.sh first."

# ── Step 1 — Invite collaborator ─────────────────────────────────────────────
hdr "1/3" "Invite ${MEMBER} as collaborator"
# gh api returns 204 if already a collaborator — idempotent
if gh api \
  --method PUT \
  "repos/${REPO_FULL}/collaborators/${MEMBER}" \
  --field permission=push \
  &>/dev/null; then
  ok "Invited ${MEMBER} (push access) — they will receive a GitHub email to accept"
else
  warn "Could not invite ${MEMBER} — they may already be a collaborator or username may be wrong"
fi

# ── Step 2 — Ensure local repo is current ───────────────────────────────────
hdr "2/3" "Sync local repo"
if [[ ! -d "${DATA_DIR}/.git" ]]; then
  gh repo clone "${REPO_FULL}" "${DATA_DIR}"
  ok "Cloned ${REPO_FULL} to ${DATA_DIR}"
else
  git -C "${DATA_DIR}" fetch --quiet origin
  git -C "${DATA_DIR}" checkout main --quiet
  git -C "${DATA_DIR}" merge --ff-only origin/main --quiet 2>/dev/null \
    || warn "Could not fast-forward local main — continuing anyway"
  ok "Local repo up to date"
fi

# ── Step 3 — Create and push branch ─────────────────────────────────────────
hdr "3/3" "Create branch ${BRANCH}"
# Check if branch already exists on remote
if git -C "${DATA_DIR}" ls-remote --exit-code --heads origin "${BRANCH}" &>/dev/null; then
  warn "Branch ${BRANCH} already exists on origin — skipping"
else
  git -C "${DATA_DIR}" checkout -b "${BRANCH}" origin/main --quiet
  git -C "${DATA_DIR}" push origin "${BRANCH}" --quiet
  git -C "${DATA_DIR}" checkout main --quiet
  ok "Branch ${BRANCH} created and pushed to ${REPO_FULL}"
fi

# ── Done ────────────────────────────────────────────────────────────────────
printf "\n${GRN}${BLD}Member added!${RST}\n"
printf "  User   : %s\n" "${MEMBER}"
printf "  Branch : %s\n" "${BRANCH}"
printf "  Repo   : https://github.com/${REPO_FULL}/tree/%s\n" "${BRANCH}"
printf "\n%s can now run:\n" "${MEMBER}"
printf "  bash cmu-cdaio-install.sh <graph.json>\n"
