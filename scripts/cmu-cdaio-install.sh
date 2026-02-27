#!/usr/bin/env bash
# =============================================================================
# cmu-cdaio-install.sh — Zero-touch hc-enterprise-kg setup for CMU CDAIO
#
# Usage:
#   bash cmu-cdaio-install.sh /path/to/graph.json
#   bash cmu-cdaio-install.sh /path/to/json-source-directory/
#
# Supports: macOS (Intel + Apple Silicon), Linux (apt/dnf)
# Windows:  Use scripts/cmu-cdaio-install.ps1 instead (native PowerShell)
#
# What this does (all idempotent — safe to re-run):
#   [1/8] OS detection
#   [2/8] Python ≥3.11
#   [3/8] Git
#   [4/8] Repository clone / pull
#   [5/8] Poetry
#   [6/8] Python dependencies (mcp extras)
#   [7/8] Knowledge graph load
#   [8/8] Claude Desktop MCP registration
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
readonly TOTAL_STEPS=8

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
  echo "  Usage:  bash $0 <graph-source>"
  echo ""
  echo "  <graph-source> is one of:"
  echo "    /path/to/graph.json          Pre-built KG snapshot → copied in directly"
  echo "    /path/to/json-source-dir/    Directory of JSON files → imported in order"
  echo ""
  echo "  Optional environment variables:"
  echo "    HCKG_INSTALL_DIR    Override default install location (~/${REPO_NAME})"
  echo "    HCKG_SKIP_PULL      Set to '1' to skip git pull on an existing clone"
  echo ""
  exit 1
}

[[ $# -lt 1 || "$1" == "-h" || "$1" == "--help" ]] && usage

GRAPH_SOURCE="$1"
INSTALL_DIR="${HCKG_INSTALL_DIR:-${DEFAULT_INSTALL_DIR}}"
SKIP_PULL="${HCKG_SKIP_PULL:-0}"

# Resolve GRAPH_SOURCE to absolute path now (before we cd away)
if [[ -e "$GRAPH_SOURCE" ]]; then
  GRAPH_SOURCE="$(cd "$(dirname "$GRAPH_SOURCE")" && pwd)/$(basename "$GRAPH_SOURCE")"
else
  die "Path does not exist: $GRAPH_SOURCE"
fi

# ---------------------------------------------------------------------------
# Banner
# ---------------------------------------------------------------------------
echo ""
echo -e "${BOLD}╔══════════════════════════════════════════════════════╗${RESET}"
echo -e "${BOLD}║   CMU CDAIO — hc-enterprise-kg installer             ║${RESET}"
echo -e "${BOLD}╚══════════════════════════════════════════════════════╝${RESET}"
echo ""
info "Graph source : ${GRAPH_SOURCE}"
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
# [7/8] Knowledge graph
# ---------------------------------------------------------------------------
GRAPH_DEST="${INSTALL_DIR}/graph.json"

step "Knowledge graph"
info "Source : ${GRAPH_SOURCE}"
info "Dest   : ${GRAPH_DEST}"

if [[ -f "$GRAPH_SOURCE" ]]; then
  # ── Single graph.json snapshot ─────────────────────────────────────────
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
echo "  Update graph:  cp /new/graph.json ${GRAPH_DEST}"
echo "                 (server auto-reloads on next tool call — no restart needed)"
echo "  Fresh demo:    cd ${INSTALL_DIR} && poetry run hckg demo --clean"
echo ""
