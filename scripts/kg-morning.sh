#!/usr/bin/env bash
# kg-morning.sh — Morning refresh: pull main → rebuild graph.json → MCP auto-reloads.
#
# Called at 8 am by LaunchAgent (macOS) or systemd timer (Linux).
# Also callable manually.
#
# Usage:
#   bash kg-morning.sh [--skip-pull]
#
# Environment:
#   HCKG_DATA_DIR   — path to hc-cdaio-kg clone  (default: ~/hc-cdaio-kg)
#   HCKG_GRAPH_OUT  — where to write graph.json   (default: ~/hc-cdaio-kg/graph.json)

set -euo pipefail
IFS=$'\n\t'

# ── Config ───────────────────────────────────────────────────────────────────
DATA_DIR="${HCKG_DATA_DIR:-${HOME}/hc-cdaio-kg}"
GRAPH_OUT="${HCKG_GRAPH_OUT:-${DATA_DIR}/graph.json}"
LIB_DIR="$(cd "$(dirname "$0")/lib" && pwd)"
PYTHON_CMD="${PYTHON_CMD:-python3}"
LOG_FILE="${DATA_DIR}/.kg-morning.log"
SKIP_PULL=0

# ── Args ─────────────────────────────────────────────────────────────────────
while [[ $# -gt 0 ]]; do
  case "$1" in
    --skip-pull) SKIP_PULL=1; shift ;;
    *) echo "Unknown argument: $1" >&2; exit 1 ;;
  esac
done

# ── Logging ──────────────────────────────────────────────────────────────────
_ts() { date '+%Y-%m-%d %H:%M:%S'; }
log() { printf '[%s] %s\n' "$(_ts)" "$*" | tee -a "${LOG_FILE}" >&2; }

if [[ -f "${LOG_FILE}" ]] && [[ $(wc -c < "${LOG_FILE}") -gt 1048576 ]]; then
  mv "${LOG_FILE}" "${LOG_FILE}.1"
fi

log "kg-morning: start"

# ── Sanity checks ────────────────────────────────────────────────────────────
[[ -d "${DATA_DIR}/.git" ]] || { log "ERROR: ${DATA_DIR} is not a git repo. Run cmu-cdaio-install.sh first."; exit 1; }
[[ -f "${LIB_DIR}/kg-build.py" ]] || { log "ERROR: missing ${LIB_DIR}/kg-build.py"; exit 1; }

# ── 1. Save current branch, switch to main ───────────────────────────────────
ORIG_BRANCH="$(git -C "${DATA_DIR}" rev-parse --abbrev-ref HEAD 2>/dev/null || echo "main")"
log "Current branch: ${ORIG_BRANCH}"

if [[ "${ORIG_BRANCH}" != "main" ]]; then
  git -C "${DATA_DIR}" stash --quiet 2>>"${LOG_FILE}" || true
  git -C "${DATA_DIR}" checkout main --quiet 2>>"${LOG_FILE}"
fi

# ── 2. Pull latest main ───────────────────────────────────────────────────────
if [[ $SKIP_PULL -eq 0 ]]; then
  log "Pulling latest main from origin"
  if git -C "${DATA_DIR}" pull --ff-only origin main --quiet 2>>"${LOG_FILE}"; then
    log "Pull succeeded"
  else
    log "WARN: fast-forward pull failed — local main may have diverged"
    git -C "${DATA_DIR}" fetch origin main --quiet 2>>"${LOG_FILE}" || true
  fi
else
  log "Skipping pull (--skip-pull)"
fi

# ── 3. Rebuild graph.json ────────────────────────────────────────────────────
log "Building ${GRAPH_OUT}"
"${PYTHON_CMD}" "${LIB_DIR}/kg-build.py" "${DATA_DIR}" "${GRAPH_OUT}" 2>>"${LOG_FILE}"
log "graph.json rebuilt: ${GRAPH_OUT}"

# ── 4. Restore original branch ───────────────────────────────────────────────
if [[ "${ORIG_BRANCH}" != "main" ]]; then
  git -C "${DATA_DIR}" checkout "${ORIG_BRANCH}" --quiet 2>>"${LOG_FILE}"
  git -C "${DATA_DIR}" stash pop --quiet 2>>"${LOG_FILE}" || true
  log "Restored branch: ${ORIG_BRANCH}"
fi

# ── 5. Update HCKG_DEFAULT_GRAPH symlink if needed ───────────────────────────
# If the install pointed HCKG_DEFAULT_GRAPH at graph.json in the data repo,
# the MCP server will detect the new mtime and auto-reload — no restart needed.
CLAUDE_CFG="${HOME}/Library/Application Support/Claude/claude_desktop_config.json"
if [[ -f "${CLAUDE_CFG}" ]]; then
  REGISTERED="$(python3 -c "
import json, sys
try:
    cfg = json.load(open('${CLAUDE_CFG}'))
    env = cfg.get('mcpServers',{}).get('hc-enterprise-kg',{}).get('env',{})
    print(env.get('HCKG_DEFAULT_GRAPH',''))
except: pass
" 2>/dev/null || echo "")"
  if [[ "${REGISTERED}" == "${GRAPH_OUT}" ]]; then
    log "MCP server will auto-reload from: ${GRAPH_OUT}"
  elif [[ -n "${REGISTERED}" ]]; then
    log "Note: HCKG_DEFAULT_GRAPH=${REGISTERED} (differs from ${GRAPH_OUT})"
    log "      Copy graph.json there if you want MCP to pick up today's data:"
    log "      cp ${GRAPH_OUT} ${REGISTERED}"
  fi
fi

# ── 6. Optional macOS notification ──────────────────────────────────────────
if command -v osascript &>/dev/null; then
  ENTITY_COUNT="$(python3 -c "
import json
try:
    g = json.load(open('${GRAPH_OUT}'))
    print(len(g.get('entities',[])))
except: print('?')
" 2>/dev/null || echo '?')"
  osascript -e "display notification \"Morning refresh done — ${ENTITY_COUNT} entities\" with title \"hc-cdaio-kg\"" \
    2>/dev/null || true
fi

log "kg-morning: done"
