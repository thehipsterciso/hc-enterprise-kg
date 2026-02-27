#!/usr/bin/env bash
# =============================================================================
# cmu-cdaio-install.sh — Zero-touch hc-enterprise-kg setup for CMU CDAIO
#
# Usage (new team member — no local files needed):
#   git clone https://github.com/thehipsterciso/hc-enterprise-kg
#   bash hc-enterprise-kg/scripts/cmu-cdaio-install.sh
#
# Usage (optional — supply a local graph snapshot to seed step 7):
#   bash cmu-cdaio-install.sh /path/to/graph.json
#   bash cmu-cdaio-install.sh /path/to/json-source-directory/
#
# Supports: macOS (Intel + Apple Silicon), Linux (apt/dnf)
# Windows:  Use scripts/cmu-cdaio-install.ps1 instead (native PowerShell)
#
# What this does (all idempotent — safe to re-run):
#   [1/9] OS detection
#   [2/9] Python ≥3.11
#   [3/9] Git
#   [4/9] Repository clone / pull
#   [5/9] Poetry
#   [6/9] Python dependencies (mcp extras)
#   [7/9] Knowledge graph load (skipped if no local source — step 9 handles it)
#   [8/9] Claude Desktop MCP registration
#   [9/9] GitHub data repo (hc-cdaio-kg) + sync daemons
#   [+]   Claude Desktop restart (with your approval, if it's running)
# =============================================================================

set -euo pipefail
IFS=$'\n\t'

# ---------------------------------------------------------------------------
# Hard-coded configuration
# ---------------------------------------------------------------------------
readonly REPO_URL="https://github.com/thehipsterciso/hc-enterprise-kg"
readonly REPO_NAME="hc-enterprise-kg"
readonly DEFAULT_INSTALL_DIR="${HOME}/${REPO_NAME}"
readonly MIN_PYTHON_MAJOR=3
readonly MIN_PYTHON_MINOR=11
readonly TOTAL_STEPS=9

# ---------------------------------------------------------------------------
# Colors — suppressed when stdout is not a TTY
# ---------------------------------------------------------------------------
if [ -t 1 ]; then
  RED='\033[0;31m' GREEN='\033[0;32m' YELLOW='\033[1;33m'
  BLUE='\033[0;34m' BOLD='\033[1m'    DIM='\033[2m' RESET='\033[0m'
  _IS_TTY=1
else
  RED='' GREEN='' YELLOW='' BLUE='' BOLD='' DIM='' RESET=''
  _IS_TTY=0
fi

# ---------------------------------------------------------------------------
# Progress state
# ---------------------------------------------------------------------------
CURRENT_STEP=0
SCRIPT_START=$(date +%s)
_STEP_START=0
_SPINNER_PID=""

# ---------------------------------------------------------------------------
# Spinner
#
# Uses ASCII frames as the safe default; switches to braille only when the
# terminal reports UTF-8 encoding.  Frames are stored in an array (no cut/
# subshell per frame — avoids the 12-forks/s overhead and the byte-vs-char
# ambiguity of `cut -c` in C/POSIX locales).
# ---------------------------------------------------------------------------
_LOCALE="${LC_ALL:-${LC_CTYPE:-${LANG:-}}}"
if [[ "$_LOCALE" == *"UTF-8"* || "$_LOCALE" == *"utf-8"* || "$_LOCALE" == *"utf8"* ]]; then
  _FRAMES=('⠋' '⠙' '⠹' '⠸' '⠼' '⠴' '⠦' '⠧' '⠇' '⠏')
else
  _FRAMES=('-' '\' '|' '/')
fi
readonly _FRAME_COUNT=${#_FRAMES[@]}

_start_spinner() {
  [[ "$_IS_TTY" == "0" ]] && return
  local msg="$1"
  (
    local i=0
    while true; do
      printf "\r    ${BLUE}%s${RESET}  %s " "${_FRAMES[i % _FRAME_COUNT]}" "$msg"
      i=$((i + 1))
      sleep 0.08
    done
  ) &
  _SPINNER_PID=$!
  # Suppress "[N] Done" job-completion noise when we kill it later
  disown "$_SPINNER_PID" 2>/dev/null || true
}

_stop_spinner() {
  if [[ -n "$_SPINNER_PID" ]] && kill -0 "$_SPINNER_PID" 2>/dev/null; then
    kill "$_SPINNER_PID" 2>/dev/null || true
    # Don't `wait` on a disowned PID — behaviour is undefined across bash versions
    _SPINNER_PID=""
  fi
  [[ "$_IS_TTY" == "1" ]] && printf "\r\033[2K"
}

# ---------------------------------------------------------------------------
# Trap — runs on EXIT, and explicitly exits on INT/TERM so Ctrl-C aborts.
# Bug fix: guard rm against empty path; separate EXIT from INT/TERM so
# INT/TERM call exit (which then fires EXIT), avoiding double cleanup.
# ---------------------------------------------------------------------------
_POETRY_TMPOUT=""
_cleanup() {
  _stop_spinner
  [[ -n "$_POETRY_TMPOUT" ]] && rm -f "$_POETRY_TMPOUT"
}
trap '_cleanup' EXIT
trap '_cleanup; exit 130' INT   # 128 + SIGINT(2)
trap '_cleanup; exit 143' TERM  # 128 + SIGTERM(15)

# ---------------------------------------------------------------------------
# Output helpers
# ---------------------------------------------------------------------------

step() {
  _stop_spinner
  CURRENT_STEP=$((CURRENT_STEP + 1))
  _STEP_START=$(date +%s)
  echo -e "\n${BLUE}${BOLD}[${CURRENT_STEP}/${TOTAL_STEPS}] ${*}${RESET}"
}

ok() {
  _stop_spinner
  local suf=""
  if [[ "$_STEP_START" -gt 0 ]]; then
    local _now; _now=$(date +%s)
    local _secs=$(( _now - _STEP_START ))
    [[ $_secs -ge 2 ]] && suf="  ${DIM}(${_secs}s)${RESET}"
    _STEP_START=0
  fi
  echo -e "    ${GREEN}✓${RESET}  ${*}${suf}"
}

warn() { _stop_spinner; echo -e "    ${YELLOW}!${RESET}  ${*}"; }
info() { echo -e "    ${*}"; }
die()  { _stop_spinner; echo -e "\n    ${RED}✗  ERROR: ${*}${RESET}\n" >&2; exit 1; }

# ---------------------------------------------------------------------------
# Usage / argument parsing
# ---------------------------------------------------------------------------
usage() {
  echo ""
  echo -e "${BOLD}CMU CDAIO — hc-enterprise-kg zero-touch installer${RESET}"
  echo ""
  echo "  Usage:  bash $0 [graph-source]"
  echo ""
  echo "  [graph-source] is OPTIONAL.  If omitted (recommended for new team members),"
  echo "  graph data is pulled automatically from hc-cdaio-kg — no local file needed."
  echo ""
  echo "  If provided, <graph-source> is one of:"
  echo "    /path/to/graph.json          Pre-built KG snapshot → copied in directly"
  echo "    /path/to/json-source-dir/    Directory of JSON files → imported in order"
  echo ""
  echo "  Optional environment variables:"
  echo "    HCKG_INSTALL_DIR    Override default install location (~/${REPO_NAME})"
  echo "    HCKG_SKIP_PULL      Set to '1' to skip git pull on an existing clone"
  echo ""
  exit 1
}

[[ "$1" == "-h" || "$1" == "--help" ]] && usage

GRAPH_SOURCE="${1:-}"
INSTALL_DIR="${HCKG_INSTALL_DIR:-${DEFAULT_INSTALL_DIR}}"
SKIP_PULL="${HCKG_SKIP_PULL:-0}"

# Resolve GRAPH_SOURCE to absolute path now (before we cd away)
if [[ -n "$GRAPH_SOURCE" ]]; then
  if [[ -e "$GRAPH_SOURCE" ]]; then
    GRAPH_SOURCE="$(cd "$(dirname "$GRAPH_SOURCE")" && pwd)/$(basename "$GRAPH_SOURCE")"
  else
    die "Path does not exist: $GRAPH_SOURCE"
  fi
fi

# ---------------------------------------------------------------------------
# Banner
# ---------------------------------------------------------------------------
echo ""
echo -e "${BOLD}╔══════════════════════════════════════════════════════╗${RESET}"
echo -e "${BOLD}║   CMU CDAIO — hc-enterprise-kg installer             ║${RESET}"
echo -e "${BOLD}╚══════════════════════════════════════════════════════╝${RESET}"
echo ""
info "Graph source : ${GRAPH_SOURCE:-(none — will build from hc-cdaio-kg)}"
info "Install dir  : ${INSTALL_DIR}"
info "Steps        : ${TOTAL_STEPS} (+ optional Claude restart)"

# ---------------------------------------------------------------------------
# [1/8] OS detection
# ---------------------------------------------------------------------------
step "OS detection"

OS="$(uname -s 2>/dev/null || true)"
ARCH="$(uname -m 2>/dev/null || true)"

case "$OS" in
  Darwin)
    PLATFORM="macos"
    ok "macOS (${ARCH})"
    PYPATH="$(command -v python3 2>/dev/null || true)"
    if [[ "$PYPATH" == /Library/Developer/CommandLineTools/* ]]; then
      warn "Apple Command-Line Tools Python detected — this can break Poetry."
      warn "If Poetry install fails, run:  brew install poetry"
    fi
    ;;
  Linux)
    PLATFORM="linux"
    ok "Linux (${ARCH})"
    ;;
  CYGWIN*|MINGW*|MSYS*)
    die "Windows detected. Use the PowerShell script instead:\n  .\\cmu-cdaio-install.ps1 <graph-source>"
    ;;
  *)
    die "Unsupported OS: ${OS}. This script supports macOS and Linux.\nOn Windows, use cmu-cdaio-install.ps1."
    ;;
esac

# ---------------------------------------------------------------------------
# Package manager helper — array-based, no eval
# ---------------------------------------------------------------------------
PKG_INSTALL_CMD=()
_APT=0
_DNF=0

if [[ "$PLATFORM" == "macos" ]]; then
  command -v brew &>/dev/null || die \
    "Homebrew is required on macOS.\nInstall it from https://brew.sh then re-run this script."
  PKG_INSTALL_CMD=(brew install)
elif [[ "$PLATFORM" == "linux" ]]; then
  if command -v apt-get &>/dev/null; then
    PKG_INSTALL_CMD=(sudo apt-get install -y)
    _APT=1
  elif command -v dnf &>/dev/null; then
    PKG_INSTALL_CMD=(sudo dnf install -y)
    _DNF=1
  else
    warn "Unknown Linux package manager — some auto-installs may fail."
  fi
fi

_pkg_install() {
  [[ ${#PKG_INSTALL_CMD[@]} -eq 0 ]] && \
    die "No package manager configured. Install the package manually and re-run."
  "${PKG_INSTALL_CMD[@]}" "$@"
}

# ---------------------------------------------------------------------------
# [2/8] Python ≥3.11
# ---------------------------------------------------------------------------
step "Python ≥${MIN_PYTHON_MAJOR}.${MIN_PYTHON_MINOR}"

PYTHON_CMD=""
for _cmd in python3.13 python3.12 python3.11 python3 python; do
  if command -v "$_cmd" &>/dev/null; then
    _ver="$("$_cmd" -c \
      'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")' \
      2>/dev/null || true)"
    _maj="${_ver%%.*}"
    _min="${_ver#*.}"
    if [[ -n "$_ver" && "$_maj" -ge "$MIN_PYTHON_MAJOR" && "$_min" -ge "$MIN_PYTHON_MINOR" ]]; then
      PYTHON_CMD="$_cmd"
      ok "Found: $("$_cmd" --version 2>&1)"
      break
    fi
  fi
done

if [[ -z "$PYTHON_CMD" ]]; then
  warn "No Python ≥${MIN_PYTHON_MAJOR}.${MIN_PYTHON_MINOR} found — installing Python 3.12..."
  if [[ "$PLATFORM" == "macos" ]]; then
    brew install python@3.12
    PYTHON_CMD="python3.12"
  elif [[ "$_APT" == "1" ]]; then
    # On Ubuntu 24.04+, Python 3.12 is in the standard repos; only add deadsnakes
    # on older releases that don't have it natively.
    _start_spinner "Updating package lists..."
    sudo apt-get update -q
    _stop_spinner
    if ! apt-cache show python3.12 &>/dev/null; then
      info "Python 3.12 not in standard repos — adding deadsnakes PPA..."
      sudo apt-get install -y software-properties-common
      sudo add-apt-repository -y ppa:deadsnakes/ppa
      _start_spinner "Updating package lists..."
      sudo apt-get update -q
      _stop_spinner
    fi
    # Note: python3.12-distutils was removed in Python 3.12; omit it
    sudo apt-get install -y python3.12 python3.12-venv python3.12-dev
    PYTHON_CMD="python3.12"
  elif [[ "$_DNF" == "1" ]]; then
    sudo dnf install -y python3.12
    PYTHON_CMD="python3.12"
  else
    die "Cannot auto-install Python on this platform.\nInstall Python 3.11+ from https://python.org and re-run."
  fi
  ok "Installed: $($PYTHON_CMD --version 2>&1)"
fi

# ---------------------------------------------------------------------------
# [3/8] Git
# ---------------------------------------------------------------------------
step "Git"

if ! command -v git &>/dev/null; then
  warn "Git not found — installing..."
  if [[ "$PLATFORM" == "macos" ]]; then
    brew install git
  elif [[ "$_APT" == "1" ]]; then
    _start_spinner "Updating package lists..."
    sudo apt-get update -q
    _stop_spinner
    _pkg_install git
  else
    _pkg_install git
  fi
fi
ok "$(git --version)"

# ---------------------------------------------------------------------------
# [4/8] Repository
# ---------------------------------------------------------------------------
step "Repository"

if [[ -d "${INSTALL_DIR}/.git" ]]; then
  ok "Repo found at ${INSTALL_DIR}"
  if [[ "$SKIP_PULL" == "1" ]]; then
    info "HCKG_SKIP_PULL=1 — skipping git pull"
  else
    info "Pulling latest..."
    # Capture pull result explicitly so ok/warn reflect actual outcome
    if git -C "$INSTALL_DIR" pull --ff-only 2>&1 | sed 's/^/    /'; then
      ok "Repository up to date"
    else
      warn "Could not fast-forward — repo is at its current version."
      warn "Set HCKG_SKIP_PULL=1 if you have local changes."
    fi
  fi
else
  info "Cloning ${REPO_URL}"
  info "→ ${INSTALL_DIR}"
  git clone "$REPO_URL" "$INSTALL_DIR"
  ok "Cloned"
fi

# All remaining commands run from inside the repo
cd "$INSTALL_DIR" || die "Cannot enter ${INSTALL_DIR} — check permissions and re-run."

# ---------------------------------------------------------------------------
# [5/8] Poetry
# ---------------------------------------------------------------------------
step "Poetry"

POETRY_CMD=""
for _p in poetry "${HOME}/.local/bin/poetry" "${HOME}/.poetry/bin/poetry"; do
  if command -v "$_p" &>/dev/null 2>/dev/null; then
    POETRY_CMD="$_p"
    break
  fi
done

if [[ -z "$POETRY_CMD" ]]; then
  warn "Poetry not found — installing..."
  if [[ "$PLATFORM" == "macos" ]]; then
    brew install poetry
    POETRY_CMD="poetry"
  else
    # Ensure pip is available before attempting pipx install
    if ! "$PYTHON_CMD" -m pip --version &>/dev/null 2>&1; then
      info "pip not found — bootstrapping via ensurepip..."
      "$PYTHON_CMD" -m ensurepip --upgrade || \
        die "Cannot bootstrap pip. Install python3-pip manually and re-run."
    fi
    if ! command -v pipx &>/dev/null; then
      _start_spinner "Installing pipx..."
      "$PYTHON_CMD" -m pip install --user --quiet pipx
      _stop_spinner
      export PATH="${HOME}/.local/bin:${PATH}"
      "$PYTHON_CMD" -m pipx ensurepath --force 2>/dev/null || true
    fi
    _start_spinner "Installing Poetry via pipx..."
    pipx install poetry
    _stop_spinner
    # Use command -v after PATH update rather than a hardcoded path
    export PATH="${HOME}/.local/bin:${PATH}"
    POETRY_CMD="$(command -v poetry)" || \
      die "Poetry installed but not found in PATH. Open a new terminal and re-run."
  fi
fi
ok "$($POETRY_CMD --version)"

# ---------------------------------------------------------------------------
# [6/8] Python dependencies
# ---------------------------------------------------------------------------
step "Python dependencies (mcp extras)"

_POETRY_TMPOUT="$(mktemp)" || die "Cannot create temp file — is /tmp full or read-only?"
_start_spinner "Resolving dependencies..."

if ! "$POETRY_CMD" install --extras "mcp" --no-interaction \
     > "$_POETRY_TMPOUT" 2>&1; then
  _stop_spinner
  warn "poetry install failed. Full output:"
  sed 's/^/    /' "$_POETRY_TMPOUT"
  die "Dependency install failed. Fix the errors above and re-run."
fi

_stop_spinner
grep -E "(Resolving|Installing|Updating|•|Lock)" "$_POETRY_TMPOUT" 2>/dev/null \
  | head -20 | sed 's/^/    /' || true
# _cleanup (via EXIT trap) will rm _POETRY_TMPOUT; also clear it now
rm -f "$_POETRY_TMPOUT"; _POETRY_TMPOUT=""

ok "Dependencies installed"

# ---------------------------------------------------------------------------
# [7/9] Knowledge graph (optional — skipped when no local source provided)
# ---------------------------------------------------------------------------
GRAPH_DEST="${INSTALL_DIR}/graph.json"

step "Knowledge graph"

if [[ -z "$GRAPH_SOURCE" ]]; then
  info "No local graph source provided — skipping."
  info "Step 9 will pull from hc-cdaio-kg and build graph.json automatically."
  ok "Skipped — graph will come from hc-cdaio-kg"

elif [[ -f "$GRAPH_SOURCE" ]]; then
  # ── Single graph.json snapshot ─────────────────────────────────────────
  info "Source : ${GRAPH_SOURCE}"
  info "Dest   : ${GRAPH_DEST}"
  info "Single file — validating..."

  # Export path for the quoted heredoc (no bash expansion inside <<'PYCHECK')
  export _HCKG_GRAPH_SRC="$GRAPH_SOURCE"
  _start_spinner "Parsing JSON..."
  # stdout captured (keeps terminal clean while spinner runs);
  # stderr still reaches the terminal so error messages are visible
  _GRAPH_INFO="$("$PYTHON_CMD" - <<'PYCHECK'
import json, os, sys
src = os.environ.get("_HCKG_GRAPH_SRC", "")
try:
    with open(src) as f:
        data = json.load(f)
except Exception as e:
    print(f"Cannot read graph: {e}", file=sys.stderr)
    sys.exit(1)
if not isinstance(data, dict):
    print("graph.json root must be a JSON object (not array/scalar).", file=sys.stderr)
    sys.exit(1)
ec = len(data.get("entities", []))
rc = len(data.get("relationships", []))
print(f"{ec} entities, {rc} relationships")
PYCHECK
  )"
  _stop_spinner
  info "Valid — ${_GRAPH_INFO}"

  cp "$GRAPH_SOURCE" "$GRAPH_DEST"
  ok "graph.json installed"

elif [[ -d "$GRAPH_SOURCE" ]]; then
  # ── Directory of JSON source files ─────────────────────────────────────
  info "Source : ${GRAPH_SOURCE}"
  info "Dest   : ${GRAPH_DEST}"
  # while-read loop for bash 3.2 compat (mapfile requires bash 4+)
  JSON_FILES=()
  while IFS= read -r _f; do
    JSON_FILES+=("$_f")
  done < <(find "$GRAPH_SOURCE" -maxdepth 1 -name "*.json" | sort)

  [[ ${#JSON_FILES[@]} -eq 0 ]] && die "No .json files found in: $GRAPH_SOURCE"

  info "Directory mode — ${#JSON_FILES[@]} JSON file(s):"
  for _f in "${JSON_FILES[@]}"; do
    info "    → $(basename "$_f")"
  done

  _i=0
  for _f in "${JSON_FILES[@]}"; do
    _i=$((_i + 1))
    info "[${_i}/${#JSON_FILES[@]}] Importing $(basename "$_f")..."
    if ! "$POETRY_CMD" run hckg import "$_f" 2>&1 | sed 's/^/    /'; then
      die "Import failed on $(basename "$_f"). See output above."
    fi
  done
  ok "All files imported → graph.json"

else
  die "GRAPH_SOURCE is neither a file nor a directory: $GRAPH_SOURCE"
fi

# ---------------------------------------------------------------------------
# [8/8] Claude Desktop MCP registration
# ---------------------------------------------------------------------------
step "Claude Desktop MCP registration"
#
# What happens here:
#   • Writes to claude_desktop_config.json under "mcpServers"
#   • Entry stores: Python path, [-m, mcp_server.server], HCKG_DEFAULT_GRAPH=<path>
#   • On Claude Desktop restart → server process spawned with env var set
#   • Server startup: auto_load_default_graph() → JSONIngestor.ingest(path)
#   • Each tool call: mtime-checked → auto-reload if graph.json changed on disk
#
info "Graph to register : ${GRAPH_DEST}"
info "Writing config..."

"$POETRY_CMD" run hckg install claude \
  --auto-install \
  --graph "$GRAPH_DEST" \
  2>&1 | sed 's/^/    /'
# set -o pipefail: pipeline fails (and script exits) if hckg returns non-zero

# Read back what was registered so the user can verify — non-fatal if it fails
CLAUDE_CONFIG=""
case "$PLATFORM" in
  macos) CLAUDE_CONFIG="${HOME}/Library/Application Support/Claude/claude_desktop_config.json" ;;
  linux) CLAUDE_CONFIG="${XDG_CONFIG_HOME:-${HOME}/.config}/Claude/claude_desktop_config.json" ;;
esac

if [[ -n "$CLAUDE_CONFIG" && -f "$CLAUDE_CONFIG" ]]; then
  echo ""
  info "Registered entry (from $(basename "$CLAUDE_CONFIG")):"
  export _HCKG_CONFIG="$CLAUDE_CONFIG"
  # Non-fatal: verification failure doesn't undo a successful registration
  "$PYTHON_CMD" - <<'PYSHOW' || warn "Could not read back config — run 'hckg install doctor' to verify."
import json, os, sys
cfg_path = os.environ.get("_HCKG_CONFIG", "")
try:
    with open(cfg_path) as f:
        cfg = json.load(f)
except Exception as e:
    print(f"    Could not open config: {e}", file=sys.stderr)
    sys.exit(1)
entry = cfg.get("mcpServers", {}).get("hc-enterprise-kg", {})
if not entry:
    print("    hc-enterprise-kg entry not found in config", file=sys.stderr)
    sys.exit(1)
print(f"    command : {entry.get('command', '?')}")
for a in entry.get("args", []):
    print(f"    arg     : {a}")
if entry.get("cwd"):
    print(f"    cwd     : {entry['cwd']}")
graph = entry.get("env", {}).get("HCKG_DEFAULT_GRAPH", "(none)")
print(f"    graph   : {graph}")
print()
print("    Loading chain:")
print("    1. Claude restarts   → MCP server spawned with HCKG_DEFAULT_GRAPH set")
print("    2. Server startup    → auto_load_default_graph() → JSONIngestor.ingest()")
print("    3. Each tool call    → mtime check → auto-reload if graph.json changed")
PYSHOW
fi

ok "MCP server registered"

# ---------------------------------------------------------------------------
# [9/9] GitHub data repo (hc-cdaio-kg) + sync daemons
#
# Two-phase design:
#   Phase 1 — Read (no GitHub account needed):
#     Clone hc-cdaio-kg via public HTTPS, build graph.json, register MCP.
#     Claude works immediately even before push access is set up.
#   Phase 2 — Write (needs GitHub account + collaborator access):
#     Guide user through account creation if needed, authenticate with gh,
#     discover username, create personal branch, push initial split,
#     install sync daemons.  If access not yet granted, prints username
#     so the user can share it with the admin and re-run later.
# ---------------------------------------------------------------------------
step "GitHub data repo + sync daemons"

_DATA_REPO_NAME="hc-cdaio-kg"
_DATA_REPO_OWNER="thehipsterciso"
_DATA_REPO_FULL="${_DATA_REPO_OWNER}/${_DATA_REPO_NAME}"
_DATA_REPO_URL="https://github.com/${_DATA_REPO_OWNER}/${_DATA_REPO_NAME}.git"
_DATA_DIR="${HOME}/${_DATA_REPO_NAME}"
_SCRIPTS_DIR="$(cd "$(dirname "$0")" && pwd)"
_SYNC_GRAPH="${_DATA_DIR}/graph.json"
_GH_USER=""
_MEMBER_BRANCH=""
_CLONE_OK=0
_PUSH_READY=0

# ══════════════════════════════════════════════════════════════════════════
# Phase 1 — Read: clone or pull, build graph.json, wire MCP
# HTTPS clone works on any public repo without a GitHub account.
# ══════════════════════════════════════════════════════════════════════════
info "Phase 1: fetching shared graph data from ${_DATA_REPO_FULL}"

if [[ -d "${_DATA_DIR}/.git" ]]; then
  _start_spinner "Pulling latest main..."
  git -C "${_DATA_DIR}" fetch origin --quiet 2>/dev/null || true
  git -C "${_DATA_DIR}" checkout main --quiet 2>/dev/null || true
  git -C "${_DATA_DIR}" merge --ff-only origin/main --quiet 2>/dev/null || true
  _stop_spinner
  ok "Data repo updated"
  _CLONE_OK=1
else
  _start_spinner "Cloning ${_DATA_REPO_FULL}..."
  if git clone --quiet "${_DATA_REPO_URL}" "${_DATA_DIR}" 2>/dev/null; then
    _stop_spinner
    ok "Cloned ${_DATA_REPO_FULL}"
    _CLONE_OK=1
  else
    _stop_spinner
    warn "Could not clone ${_DATA_REPO_FULL}"
    warn "Admin may not have created the data repo yet — run kg-setup-repo.sh first."
  fi
fi

# Build graph.json from cloned per-type files, then register MCP
if [[ "$_CLONE_OK" == "1" ]]; then
  _BUILD_PY="${_SCRIPTS_DIR}/lib/kg-build.py"
  if [[ -f "${_BUILD_PY}" ]] \
       && [[ -d "${_DATA_DIR}/entities" || -d "${_DATA_DIR}/relationships" ]]; then
    info "Building graph.json from per-type files..."
    "$PYTHON_CMD" "${_BUILD_PY}" "${_DATA_DIR}" "${_SYNC_GRAPH}"
  elif [[ ! -f "${_SYNC_GRAPH}" ]]; then
    cp "${GRAPH_DEST}" "${_SYNC_GRAPH}" 2>/dev/null \
      || warn "Could not seed ${_SYNC_GRAPH}"
  fi

  if [[ -f "${_SYNC_GRAPH}" ]]; then
    info "Updating HCKG_DEFAULT_GRAPH → ${_SYNC_GRAPH}"
    "$POETRY_CMD" run hckg install claude \
      --auto-install \
      --graph "${_SYNC_GRAPH}" \
      2>&1 | sed 's/^/    /'
    ok "MCP now loading from ${_SYNC_GRAPH}  ← Claude is ready"
  fi
fi

# ══════════════════════════════════════════════════════════════════════════
# Phase 2 — Write: gh auth → username → branch → daemons
# ══════════════════════════════════════════════════════════════════════════
echo ""
info "Phase 2: setting up your personal sync branch (requires GitHub account)"

# ── Install gh CLI if missing ─────────────────────────────────────────────
if ! command -v gh &>/dev/null; then
  if [[ "$PLATFORM" == "macos" ]]; then
    _start_spinner "Installing gh CLI..."
    brew install gh; _stop_spinner
  elif [[ "$_APT" == "1" ]]; then
    if apt-cache show gh &>/dev/null 2>&1; then
      _pkg_install gh
    else
      info "Adding GitHub CLI apt repo..."
      sudo mkdir -p -m 755 /etc/apt/keyrings
      wget -qO- https://cli.github.com/packages/githubcli-archive-keyring.gpg \
        | sudo tee /etc/apt/keyrings/githubcli-archive-keyring.gpg > /dev/null
      sudo chmod go+r /etc/apt/keyrings/githubcli-archive-keyring.gpg
      echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/githubcli-archive-keyring.gpg] https://cli.github.com/packages stable main" \
        | sudo tee /etc/apt/sources.list.d/github-cli.list > /dev/null
      _start_spinner "Installing gh..."
      sudo apt-get update -q && _pkg_install gh; _stop_spinner
    fi
  elif [[ "$_DNF" == "1" ]]; then
    _start_spinner "Installing gh..."; sudo dnf install -y gh; _stop_spinner
  else
    warn "Cannot auto-install gh — install from https://cli.github.com then re-run."
  fi
fi

# ── Authenticate ──────────────────────────────────────────────────────────
if command -v gh &>/dev/null && ! gh auth status &>/dev/null 2>&1; then
  echo ""
  echo -e "    ${BOLD}GitHub account needed to push your changes${RESET}"
  echo ""
  echo "    hc-cdaio-kg is publicly readable, but pushing your edits back"
  echo "    requires a free GitHub account and collaborator access."
  echo ""
  if [[ -t 0 ]]; then
    printf "    Do you already have a GitHub account? [y/N] "
    read -r _HAS_ACCOUNT; echo ""
    if [[ ! "$_HAS_ACCOUNT" =~ ^[Yy]([Ee][Ss])?$ ]]; then
      echo "    ┌─────────────────────────────────────────────────────┐"
      echo "    │  Create your free GitHub account:                   │"
      echo "    │  https://github.com/signup                          │"
      echo "    │  • Use your work email • Verify before continuing   │"
      echo "    └─────────────────────────────────────────────────────┘"
      echo ""
      [[ "$PLATFORM" == "macos" ]] && open "https://github.com/signup" 2>/dev/null || true
      command -v xdg-open &>/dev/null \
        && xdg-open "https://github.com/signup" 2>/dev/null || true
      printf "    Press Enter once your account is verified: "
      read -r _; echo ""
    fi
    echo "    Launching GitHub authentication (a browser window will open)..."
    echo "    Choose HTTPS when prompted for protocol."
    echo ""
    gh auth login --web --git-protocol https \
      || warn "Authentication failed — sync daemons will not be installed"
  else
    warn "stdin is not a terminal — run: gh auth login  then re-run installer"
  fi
fi

# ── Discover username ────────────────────────────────────────────────────
if command -v gh &>/dev/null && gh auth status &>/dev/null 2>&1; then
  _GH_USER="$(gh api user --jq .login 2>/dev/null || echo "")"
fi

if [[ -n "${_GH_USER}" ]]; then
  ok "Authenticated as: ${_GH_USER}"
  _MEMBER_BRANCH="${_GH_USER}/data"

  # ── Check collaborator / push access ─────────────────────────────────
  _VIEWER_PERM="$(gh repo view "${_DATA_REPO_FULL}" --json viewerPermission \
    --jq '.viewerPermission' 2>/dev/null || echo "NONE")"

  if [[ "${_VIEWER_PERM}" =~ ^(WRITE|MAINTAIN|ADMIN)$ ]]; then
    _PUSH_READY=1
  else
    # No push access yet — file a GitHub issue on hc-cdaio-kg
    # so the admin gets an automatic notification and knows exactly what to run.
    echo ""
    info "Requesting collaborator access from admin..."
    _ISSUE_TITLE="Add collaborator: ${_GH_USER} to hc-cdaio-kg"
    _ISSUE_BODY="$(cat <<ISSUEBODY
## New team member install request

**GitHub username:** \`${_GH_USER}\`

**Action required (admin):**
\`\`\`bash
bash scripts/kg-add-member.sh ${_GH_USER}
\`\`\`

Once the invitation is accepted, \`${_GH_USER}\` can re-run the installer to complete sync setup.

> Auto-generated by \`cmu-cdaio-install.sh\`
ISSUEBODY
)"
    if gh issue create \
         --repo "${_DATA_REPO_FULL}" \
         --title "${_ISSUE_TITLE}" \
         --body "${_ISSUE_BODY}" \
         --label "collaborator-request" \
         2>/dev/null \
       || gh issue create \
         --repo "${_DATA_REPO_FULL}" \
         --title "${_ISSUE_TITLE}" \
         --body "${_ISSUE_BODY}" \
         2>/dev/null; then
      ok "Access request filed — admin will receive a GitHub notification"
    else
      warn "Could not file GitHub issue (label may not exist — that's OK)"
      warn "Your username is: ${_GH_USER}"
      warn "Ask admin to run: bash scripts/kg-add-member.sh ${_GH_USER}"
    fi
    echo ""
    info "Once the admin grants access and you accept the GitHub invitation email:"
    info "  Re-run: bash $(basename "$0")"
    warn "Sync daemons NOT installed yet — Claude reads from main branch for now."
  fi
fi

# ── Create branch + initial commit + push ───────────────────────────────
if [[ "$_PUSH_READY" == "1" && "$_CLONE_OK" == "1" ]]; then
  if git -C "${_DATA_DIR}" ls-remote --exit-code --heads origin "${_MEMBER_BRANCH}" &>/dev/null; then
    git -C "${_DATA_DIR}" checkout "${_MEMBER_BRANCH}" --quiet 2>/dev/null \
      || git -C "${_DATA_DIR}" checkout -b "${_MEMBER_BRANCH}" "origin/${_MEMBER_BRANCH}" --quiet
  else
    git -C "${_DATA_DIR}" checkout -b "${_MEMBER_BRANCH}" origin/main --quiet 2>/dev/null \
      || git -C "${_DATA_DIR}" checkout -b "${_MEMBER_BRANCH}" --quiet
    git -C "${_DATA_DIR}" push origin "${_MEMBER_BRANCH}" --quiet 2>/dev/null \
      || warn "Branch push failed — will retry on first kg-sync.sh run"
  fi
  info "Branch: ${_MEMBER_BRANCH}"

  # Split seed graph onto the member branch.
  # Prefer local GRAPH_DEST (if Step 7 ran); fall back to _SYNC_GRAPH from hc-cdaio-kg.
  _SPLIT_SRC="${GRAPH_DEST}"
  [[ ! -f "${_SPLIT_SRC}" ]] && _SPLIT_SRC="${_SYNC_GRAPH}"
  if [[ -f "${_SCRIPTS_DIR}/lib/kg-split.py" && -f "${_SPLIT_SRC}" ]]; then
    "$PYTHON_CMD" "${_SCRIPTS_DIR}/lib/kg-split.py" "${_SPLIT_SRC}" "${_DATA_DIR}" 2>/dev/null || true
    git -C "${_DATA_DIR}" add entities/ relationships/ 2>/dev/null || true
    if ! git -C "${_DATA_DIR}" diff --cached --quiet; then
      git -C "${_DATA_DIR}" commit -m "feat: initial graph split from installer" --quiet
      git -C "${_DATA_DIR}" push origin "${_MEMBER_BRANCH}" --quiet 2>/dev/null \
        || warn "Push failed — will retry on first kg-sync.sh run"
      ok "Initial graph split pushed to ${_MEMBER_BRANCH}"
    else
      info "Branch already up to date"
    fi
  fi
fi

# ── Install daemons ──────────────────────────────────────────────────────
if [[ "$_PUSH_READY" == "1" && -n "${_MEMBER_BRANCH}" ]]; then
  if [[ "$PLATFORM" == "macos" ]]; then
    _LA_DIR="${HOME}/Library/LaunchAgents"
    mkdir -p "${_LA_DIR}"

    # ── kg-sync every 30 minutes ──────────────────────────────────────────
    _SYNC_PLIST="${_LA_DIR}/com.hccdaio.kg-sync.plist"
    cat > "${_SYNC_PLIST}" <<PLIST
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN"
  "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>              <string>com.hccdaio.kg-sync</string>
    <key>ProgramArguments</key>
    <array>
        <string>/bin/bash</string>
        <string>${_SCRIPTS_DIR}/kg-sync.sh</string>
    </array>
    <key>EnvironmentVariables</key>
    <dict>
        <key>HCKG_DATA_DIR</key>   <string>${_DATA_DIR}</string>
        <key>HCKG_GRAPH_SRC</key>  <string>${GRAPH_DEST}</string>
        <key>HCKG_BRANCH</key>     <string>${_MEMBER_BRANCH}</string>
        <key>HOME</key>            <string>${HOME}</string>
        <key>PATH</key>            <string>/usr/local/bin:/opt/homebrew/bin:/usr/bin:/bin</string>
    </dict>
    <key>StartInterval</key>      <integer>1800</integer>
    <key>RunAtLoad</key>          <false/>
    <key>StandardOutPath</key>    <string>${_DATA_DIR}/.kg-sync-launchd.log</string>
    <key>StandardErrorPath</key>  <string>${_DATA_DIR}/.kg-sync-launchd.log</string>
</dict>
</plist>
PLIST

    # ── EOD PR at 17:00 daily ─────────────────────────────────────────────
    _EOD_PLIST="${_LA_DIR}/com.hccdaio.kg-eod.plist"
    cat > "${_EOD_PLIST}" <<PLIST
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN"
  "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>              <string>com.hccdaio.kg-eod</string>
    <key>ProgramArguments</key>
    <array>
        <string>/bin/bash</string>
        <string>${_SCRIPTS_DIR}/kg-eod.sh</string>
    </array>
    <key>EnvironmentVariables</key>
    <dict>
        <key>HCKG_DATA_DIR</key>   <string>${_DATA_DIR}</string>
        <key>HCKG_GRAPH_SRC</key>  <string>${GRAPH_DEST}</string>
        <key>HCKG_BRANCH</key>     <string>${_MEMBER_BRANCH}</string>
        <key>HOME</key>            <string>${HOME}</string>
        <key>PATH</key>            <string>/usr/local/bin:/opt/homebrew/bin:/usr/bin:/bin</string>
    </dict>
    <key>StartCalendarInterval</key>
    <dict>
        <key>Hour</key>    <integer>17</integer>
        <key>Minute</key>  <integer>0</integer>
    </dict>
    <key>StandardOutPath</key>    <string>${_DATA_DIR}/.kg-eod-launchd.log</string>
    <key>StandardErrorPath</key>  <string>${_DATA_DIR}/.kg-eod-launchd.log</string>
</dict>
</plist>
PLIST

    # ── Morning pull at 08:00 daily ───────────────────────────────────────
    _MORNING_PLIST="${_LA_DIR}/com.hccdaio.kg-morning.plist"
    cat > "${_MORNING_PLIST}" <<PLIST
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN"
  "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>              <string>com.hccdaio.kg-morning</string>
    <key>ProgramArguments</key>
    <array>
        <string>/bin/bash</string>
        <string>${_SCRIPTS_DIR}/kg-morning.sh</string>
    </array>
    <key>EnvironmentVariables</key>
    <dict>
        <key>HCKG_DATA_DIR</key>  <string>${_DATA_DIR}</string>
        <key>HCKG_GRAPH_OUT</key> <string>${_SYNC_GRAPH}</string>
        <key>HOME</key>           <string>${HOME}</string>
        <key>PATH</key>           <string>/usr/local/bin:/opt/homebrew/bin:/usr/bin:/bin</string>
    </dict>
    <key>StartCalendarInterval</key>
    <dict>
        <key>Hour</key>    <integer>8</integer>
        <key>Minute</key>  <integer>0</integer>
    </dict>
    <key>StandardOutPath</key>    <string>${_DATA_DIR}/.kg-morning-launchd.log</string>
    <key>StandardErrorPath</key>  <string>${_DATA_DIR}/.kg-morning-launchd.log</string>
</dict>
</plist>
PLIST

    # Load/reload all three agents
    for _plist in "${_SYNC_PLIST}" "${_EOD_PLIST}" "${_MORNING_PLIST}"; do
      _label="$(basename "${_plist}" .plist)"
      launchctl unload "${_plist}" 2>/dev/null || true
      launchctl load "${_plist}" 2>/dev/null \
        && info "  LaunchAgent loaded: ${_label}" \
        || warn "  Could not load ${_label} — check ${_plist}"
    done
    ok "LaunchAgents installed (sync every 30 min, EOD at 5pm, morning pull at 8am)"

  elif [[ "$PLATFORM" == "linux" ]]; then
    _SYSTEMD_DIR="${HOME}/.config/systemd/user"
    mkdir -p "${_SYSTEMD_DIR}"

    # ── kg-sync.service ────────────────────────────────────────────────────
    cat > "${_SYSTEMD_DIR}/kg-sync.service" <<UNIT
[Unit]
Description=hc-cdaio-kg sync — split graph.json and push to branch

[Service]
Type=oneshot
ExecStart=/bin/bash ${_SCRIPTS_DIR}/kg-sync.sh
Environment=HCKG_DATA_DIR=${_DATA_DIR}
Environment=HCKG_GRAPH_SRC=${GRAPH_DEST}
Environment=HCKG_BRANCH=${_MEMBER_BRANCH}
StandardOutput=append:${_DATA_DIR}/.kg-sync-systemd.log
StandardError=append:${_DATA_DIR}/.kg-sync-systemd.log
UNIT

    cat > "${_SYSTEMD_DIR}/kg-sync.timer" <<UNIT
[Unit]
Description=hc-cdaio-kg sync every 30 minutes

[Timer]
OnBootSec=5min
OnUnitActiveSec=30min
Persistent=true

[Install]
WantedBy=timers.target
UNIT

    # ── kg-eod.service ─────────────────────────────────────────────────────
    cat > "${_SYSTEMD_DIR}/kg-eod.service" <<UNIT
[Unit]
Description=hc-cdaio-kg EOD — final sync + PR to main

[Service]
Type=oneshot
ExecStart=/bin/bash ${_SCRIPTS_DIR}/kg-eod.sh
Environment=HCKG_DATA_DIR=${_DATA_DIR}
Environment=HCKG_GRAPH_SRC=${GRAPH_DEST}
Environment=HCKG_BRANCH=${_MEMBER_BRANCH}
StandardOutput=append:${_DATA_DIR}/.kg-eod-systemd.log
StandardError=append:${_DATA_DIR}/.kg-eod-systemd.log
UNIT

    cat > "${_SYSTEMD_DIR}/kg-eod.timer" <<UNIT
[Unit]
Description=hc-cdaio-kg EOD at 17:00 daily

[Timer]
OnCalendar=*-*-* 17:00:00
Persistent=true

[Install]
WantedBy=timers.target
UNIT

    # ── kg-morning.service ─────────────────────────────────────────────────
    cat > "${_SYSTEMD_DIR}/kg-morning.service" <<UNIT
[Unit]
Description=hc-cdaio-kg morning pull — rebuild graph.json from main

[Service]
Type=oneshot
ExecStart=/bin/bash ${_SCRIPTS_DIR}/kg-morning.sh
Environment=HCKG_DATA_DIR=${_DATA_DIR}
Environment=HCKG_GRAPH_OUT=${_SYNC_GRAPH}
StandardOutput=append:${_DATA_DIR}/.kg-morning-systemd.log
StandardError=append:${_DATA_DIR}/.kg-morning-systemd.log
UNIT

    cat > "${_SYSTEMD_DIR}/kg-morning.timer" <<UNIT
[Unit]
Description=hc-cdaio-kg morning pull at 08:00

[Timer]
OnCalendar=*-*-* 08:00:00
Persistent=true

[Install]
WantedBy=timers.target
UNIT

    # Reload and enable
    systemctl --user daemon-reload 2>/dev/null \
      || warn "systemctl daemon-reload failed — may need: loginctl enable-linger ${USER}"
    for _svc in kg-sync kg-eod kg-morning; do
      systemctl --user enable --now "${_svc}.timer" 2>/dev/null \
        && info "  systemd timer enabled: ${_svc}.timer" \
        || warn "  Could not enable ${_svc}.timer — check ~/.config/systemd/user/"
    done
    ok "systemd timers installed (sync every 30 min, EOD at 5pm, morning pull at 8am)"
  fi

  # ── Daemon summary ────────────────────────────────────────────────────────
  echo ""
  info "Sync daemons active:"
  info "  8 am         : kg-morning.sh  — pull main → rebuild graph.json"
  info "  every 30 min : kg-sync.sh     — commit + push your changes"
  info "  5 pm         : kg-eod.sh      — open PR to main"
  info "  Logs : ${_DATA_DIR}/.kg-*.log"

fi  # end daemon install (_PUSH_READY)

# ---------------------------------------------------------------------------
# [+] Claude Desktop process management (with user approval)
# ---------------------------------------------------------------------------
echo ""
echo -e "${BLUE}${BOLD}[+] Claude Desktop restart${RESET}"

_find_claude_pids() {
  if [[ "$PLATFORM" == "macos" ]]; then
    pgrep -x "Claude" 2>/dev/null || true
  else
    # Try progressively broader searches; || true ensures no set-e trigger
    pgrep -f "[Cc]laude.?[Dd]esktop" 2>/dev/null \
      || pgrep -x "claude" 2>/dev/null \
      || pgrep -x "Claude" 2>/dev/null \
      || true
  fi
}

CLAUDE_PIDS="$(_find_claude_pids)"
CLAUDE_PIDS_DISPLAY="$(printf '%s' "$CLAUDE_PIDS" | tr '\n' ' ' | sed 's/ $//')"

if [[ -z "$CLAUDE_PIDS" ]]; then
  info "Claude Desktop is not running — open it manually after this script finishes."
else
  echo ""
  warn "Claude Desktop is running  (PID: ${CLAUDE_PIDS_DISPLAY})"
  warn "It must be restarted to load the new MCP server registration."
  echo ""

  if [[ ! -t 0 ]]; then
    warn "stdin is not a terminal — cannot prompt."
    warn "Restart Claude Desktop manually to activate the MCP server."
  else
    printf "    Restart Claude Desktop now? [y/N] "
    read -r _REPLY
    echo ""

    if [[ "$_REPLY" =~ ^[Yy]([Ee][Ss])?$ ]]; then

      # ── Graceful stop ─────────────────────────────────────────────────
      info "Stopping Claude Desktop..."
      if [[ "$PLATFORM" == "macos" ]]; then
        osascript -e 'quit app "Claude"' 2>/dev/null \
          || kill -TERM $CLAUDE_PIDS 2>/dev/null || true  # SC2086: word-split on PIDs intentional
      else
        kill -TERM $CLAUDE_PIDS 2>/dev/null || true       # SC2086: word-split on PIDs intentional
      fi

      # Wait up to 5 s for graceful shutdown — spinner runs continuously outside the loop
      _waited=0
      _start_spinner "Waiting for Claude Desktop to exit..."
      while [[ $_waited -lt 5 ]] && [[ -n "$(_find_claude_pids)" ]]; do
        sleep 1
        _waited=$((_waited + 1))
      done
      _stop_spinner

      # Force-kill if still alive — re-query PIDs to avoid PID-reuse race
      _LIVE_PIDS="$(_find_claude_pids)"
      if [[ -n "$_LIVE_PIDS" ]]; then
        warn "Still running after ${_waited}s — force stopping..."
        # SC2086: word-split intentional
        kill -KILL $_LIVE_PIDS 2>/dev/null || true
        sleep 1
      fi
      ok "Claude Desktop stopped"

      # ── Relaunch ──────────────────────────────────────────────────────
      info "Relaunching Claude Desktop..."
      if [[ "$PLATFORM" == "macos" ]]; then
        open -a "Claude" 2>/dev/null \
          && ok "Claude Desktop relaunched" \
          || warn "Could not relaunch — open Claude Desktop manually."
      else
        _CLAUDE_BIN=""
        for _b in claude-desktop claude /usr/bin/claude-desktop \
                   /opt/Claude/claude /usr/local/bin/claude-desktop \
                   /snap/bin/claude-desktop; do
          if command -v "$_b" &>/dev/null 2>/dev/null; then
            _CLAUDE_BIN="$_b"
            break
          fi
        done
        if [[ -n "$_CLAUDE_BIN" ]]; then
          nohup "$_CLAUDE_BIN" &>/dev/null &
          disown
          ok "Claude Desktop relaunching (${_CLAUDE_BIN})"
        else
          warn "Could not find the Claude Desktop binary — open it manually."
        fi
      fi

    else
      warn "Skipped — open Claude Desktop manually to activate the MCP server."
    fi
  fi
fi

# ---------------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------------
SCRIPT_END=$(date +%s)
ELAPSED=$(( SCRIPT_END - SCRIPT_START ))
ELAPSED_FMT="$(printf '%dm %ds' $(( ELAPSED / 60 )) $(( ELAPSED % 60 )))"

echo ""
echo -e "${GREEN}${BOLD}╔══════════════════════════════════════════════════════╗${RESET}"
echo -e "${GREEN}${BOLD}║   Installation complete!                             ║${RESET}"
echo -e "${GREEN}${BOLD}╚══════════════════════════════════════════════════════╝${RESET}"
echo ""
echo -e "  ${DIM}Total time: ${ELAPSED_FMT}${RESET}"
echo ""
echo -e "${BOLD}In Claude Desktop, try:${RESET}"
echo "  \"Load my knowledge graph and show the top 10 most connected entities\""
echo ""
echo -e "${BOLD}Useful commands:${RESET}"
echo "  Diagnose:      cd ${INSTALL_DIR} && poetry run hckg install doctor"
echo "  Morning pull:  bash ${_SCRIPTS_DIR:-$(dirname "$0")}/kg-morning.sh"
echo "                 (rebuilds graph.json from hc-cdaio-kg main — auto-reloads in Claude)"
echo "  Manual sync:   bash ${_SCRIPTS_DIR:-$(dirname "$0")}/kg-sync.sh"
echo "  Manual EOD:    bash ${_SCRIPTS_DIR:-$(dirname "$0")}/kg-eod.sh"
echo "  Fresh demo:    cd ${INSTALL_DIR} && poetry run hckg demo --clean"
echo ""
