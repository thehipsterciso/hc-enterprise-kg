#!/usr/bin/env bash
# kg-sync.sh — Daemon: split graph.json → per-type files → commit → push branch.
#
# Called every 30 minutes by LaunchAgent (macOS) or systemd timer (Linux).
# Also callable manually at any time.
#
# Usage:
#   bash kg-sync.sh [--message "custom commit message"]
#
# Environment:
#   HCKG_DATA_DIR   — path to hc-cdaio-kg clone  (default: ~/hc-cdaio-kg)
#   HCKG_GRAPH_SRC  — path to live graph.json     (default: ~/hc-enterprise-kg/graph.json)
#   HCKG_BRANCH     — branch to commit to         (default: auto-detected from git)

set -euo pipefail
IFS=$'\n\t'

# ── Config ───────────────────────────────────────────────────────────────────
DATA_DIR="${HCKG_DATA_DIR:-${HOME}/hc-cdaio-kg}"
GRAPH_SRC="${HCKG_GRAPH_SRC:-${HOME}/hc-enterprise-kg/graph.json}"
LIB_DIR="$(cd "$(dirname "$0")/lib" && pwd)"
PYTHON_CMD="${PYTHON_CMD:-python3}"
LOG_FILE="${DATA_DIR}/.kg-sync.log"
COMMIT_MSG=""

# ── Args ─────────────────────────────────────────────────────────────────────
while [[ $# -gt 0 ]]; do
  case "$1" in
    --message|-m) COMMIT_MSG="$2"; shift 2 ;;
    *) echo "Unknown argument: $1" >&2; exit 1 ;;
  esac
done

# ── Logging (to file + stderr) ────────────────────────────────────────────────
_ts() { date '+%Y-%m-%d %H:%M:%S'; }
log() { printf '[%s] %s\n' "$(_ts)" "$*" | tee -a "${LOG_FILE}" >&2; }

# Rotate log if > 1 MB
if [[ -f "${LOG_FILE}" ]] && [[ $(wc -c < "${LOG_FILE}") -gt 1048576 ]]; then
  mv "${LOG_FILE}" "${LOG_FILE}.1"
fi

log "kg-sync: start"

# ── Sanity checks ────────────────────────────────────────────────────────────
[[ -d "${DATA_DIR}/.git" ]] || { log "ERROR: ${DATA_DIR} is not a git repo"; exit 1; }
[[ -f "${GRAPH_SRC}" ]]     || { log "SKIP: graph source not found: ${GRAPH_SRC}"; exit 0; }
[[ -f "${LIB_DIR}/kg-split.py" ]] || { log "ERROR: missing ${LIB_DIR}/kg-split.py"; exit 1; }

# ── Detect branch ────────────────────────────────────────────────────────────
if [[ -n "${HCKG_BRANCH:-}" ]]; then
  BRANCH="${HCKG_BRANCH}"
else
  BRANCH="$(git -C "${DATA_DIR}" rev-parse --abbrev-ref HEAD 2>/dev/null || echo "")"
  if [[ -z "${BRANCH}" || "${BRANCH}" == "main" || "${BRANCH}" == "HEAD" ]]; then
    # Try to derive from git config user or system username
    GIT_USER="$(git -C "${DATA_DIR}" config user.name 2>/dev/null \
      | tr '[:upper:]' '[:lower:]' | tr ' ' '-' || echo "")"
    GH_USER="$(gh api user --jq .login 2>/dev/null || echo "")"
    MEMBER="${GH_USER:-${GIT_USER:-$(whoami)}}"
    BRANCH="${MEMBER}/data"
    log "Auto-detected branch: ${BRANCH}"
    # Switch to the member branch if it exists
    if git -C "${DATA_DIR}" ls-remote --exit-code --heads origin "${BRANCH}" &>/dev/null; then
      git -C "${DATA_DIR}" fetch origin "${BRANCH}" --quiet
      git -C "${DATA_DIR}" checkout "${BRANCH}" --quiet 2>/dev/null \
        || git -C "${DATA_DIR}" checkout -b "${BRANCH}" "origin/${BRANCH}" --quiet
    else
      log "WARN: branch ${BRANCH} not found on origin — committing to current branch"
      BRANCH="$(git -C "${DATA_DIR}" rev-parse --abbrev-ref HEAD)"
    fi
  fi
fi
log "Branch: ${BRANCH}"

# ── Split graph.json → per-type files ────────────────────────────────────────
log "Splitting ${GRAPH_SRC} into per-type files"
"${PYTHON_CMD}" "${LIB_DIR}/kg-split.py" "${GRAPH_SRC}" "${DATA_DIR}" 2>>"${LOG_FILE}"

# ── Check for changes ────────────────────────────────────────────────────────
git -C "${DATA_DIR}" add entities/ relationships/ 2>/dev/null || true

if git -C "${DATA_DIR}" diff --cached --quiet; then
  log "No changes since last sync — nothing to commit"
  exit 0
fi

# Count changed files
CHANGED=$(git -C "${DATA_DIR}" diff --cached --name-only | wc -l | tr -d ' ')

# ── Commit ───────────────────────────────────────────────────────────────────
if [[ -z "${COMMIT_MSG}" ]]; then
  COMMIT_MSG="sync: auto-commit ${CHANGED} file(s) at $(_ts)"
fi

git -C "${DATA_DIR}" commit -m "${COMMIT_MSG}" --quiet
log "Committed: ${COMMIT_MSG}"

# ── Push ─────────────────────────────────────────────────────────────────────
git -C "${DATA_DIR}" push origin "${BRANCH}" --quiet 2>>"${LOG_FILE}" \
  || git -C "${DATA_DIR}" push origin "${BRANCH}" --set-upstream --quiet 2>>"${LOG_FILE}"
log "Pushed to origin/${BRANCH}"

log "kg-sync: done (${CHANGED} files)"
