<#
.SYNOPSIS
    Zero-touch hc-enterprise-kg setup for CMU CDAIO (Windows)

.DESCRIPTION
    Installs prerequisites, clones the repo, loads your org knowledge graph,
    and registers the MCP server with Claude Desktop — all in one shot.

    Requires: Windows 10 1709+ or Windows 11, PowerShell 5.1+
    Recommended: Run in a PowerShell terminal (not CMD)

.PARAMETER GraphSource
    Path to a pre-built graph.json snapshot OR a directory of JSON source files.

.PARAMETER InstallDir
    Override the default install location. Default: $HOME\hc-enterprise-kg

.PARAMETER SkipPull
    Skip 'git pull' if the repo is already cloned.

.EXAMPLE
    .\cmu-cdaio-install.ps1 C:\Users\you\rackspace\graph.json
    .\cmu-cdaio-install.ps1 C:\Users\you\rackspace-jsons\
    .\cmu-cdaio-install.ps1 graph.json -InstallDir D:\tools\hckg
#>

[CmdletBinding()]
param(
    [Parameter(Mandatory = $true, Position = 0)]
    [string]$GraphSource,

    [string]$InstallDir = "$HOME\hc-enterprise-kg",

    [switch]$SkipPull
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

# ---------------------------------------------------------------------------
# Color helpers
# ---------------------------------------------------------------------------
function Step  { param([string]$msg) Write-Host "`n==> $msg" -ForegroundColor Cyan }
function Ok    { param([string]$msg) Write-Host "    v  $msg" -ForegroundColor Green }
function Warn  { param([string]$msg) Write-Host "    !  $msg" -ForegroundColor Yellow }
function Info  { param([string]$msg) Write-Host "    $msg" }
function Fail  { param([string]$msg) Write-Host "`n    X  ERROR: $msg`n" -ForegroundColor Red; exit 1 }

# ---------------------------------------------------------------------------
# Resolve GraphSource to absolute path now (before we cd away)
# ---------------------------------------------------------------------------
$GraphSource = Resolve-Path -LiteralPath $GraphSource -ErrorAction SilentlyContinue
if (-not $GraphSource) {
    Fail "Path does not exist: $($args[0])"
}
$GraphSource = $GraphSource.Path

# ---------------------------------------------------------------------------
# Banner
# ---------------------------------------------------------------------------
Write-Host ""
Write-Host "╔══════════════════════════════════════════════════════╗" -ForegroundColor White
Write-Host "║   CMU CDAIO — hc-enterprise-kg installer (Windows)   ║" -ForegroundColor White
Write-Host "╚══════════════════════════════════════════════════════╝" -ForegroundColor White
Write-Host ""
Info "Graph source : $GraphSource"
Info "Install dir  : $InstallDir"

# ---------------------------------------------------------------------------
# Step 1 — OS / PowerShell version check
# ---------------------------------------------------------------------------
Step "Checking environment"

$psMajor = $PSVersionTable.PSVersion.Major
if ($psMajor -lt 5) {
    Fail "PowerShell 5.1 or later is required (you have $($PSVersionTable.PSVersion)). Update via Windows Update."
}
Ok "PowerShell $($PSVersionTable.PSVersion) on $([System.Environment]::OSVersion.VersionString)"

# Check execution policy — must allow script execution
$policy = Get-ExecutionPolicy -Scope CurrentUser
if ($policy -in @('Restricted', 'AllSigned')) {
    Warn "Execution policy '$policy' may block this script."
    Warn "To fix, run in an elevated PowerShell: Set-ExecutionPolicy -Scope CurrentUser RemoteSigned"
    Fail "Execution policy too restrictive. See warning above."
}

# ---------------------------------------------------------------------------
# Helper — run a command and fail on non-zero exit
# ---------------------------------------------------------------------------
function Invoke-Required {
    param([string]$Exe, [string[]]$Arguments, [string]$FailMsg)
    $result = & $Exe @Arguments 2>&1
    if ($LASTEXITCODE -ne 0) {
        Write-Host ($result -join "`n") -ForegroundColor Red
        Fail $FailMsg
    }
    return $result
}

# ---------------------------------------------------------------------------
# Helper — check if a command exists
# ---------------------------------------------------------------------------
function Test-Command { param([string]$Name) return [bool](Get-Command $Name -ErrorAction SilentlyContinue) }

# ---------------------------------------------------------------------------
# Step 2 — winget availability
# ---------------------------------------------------------------------------
Step "Checking package manager (winget)"

$HaveWinget = Test-Command 'winget'
if ($HaveWinget) {
    Ok "winget available — will use for auto-installs"
} else {
    Warn "winget not found. Auto-installs disabled."
    Warn "Install winget from the Microsoft Store (App Installer) then re-run,"
    Warn "or install Python/Git manually from python.org and git-scm.com."
}

# ---------------------------------------------------------------------------
# Step 3 — Python >= 3.11
# ---------------------------------------------------------------------------
Step "Checking Python >= 3.11"

$PythonCmd = $null
foreach ($candidate in @('python3.13','python3.12','python3.11','python3','python')) {
    if (Test-Command $candidate) {
        $ver = & $candidate -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')" 2>$null
        if ($ver -match '^(\d+)\.(\d+)$') {
            $maj = [int]$Matches[1]; $min = [int]$Matches[2]
            if ($maj -gt 3 -or ($maj -eq 3 -and $min -ge 11)) {
                $PythonCmd = $candidate
                Ok "Found: $($PythonCmd) -> $(& $PythonCmd --version)"
                break
            }
        }
    }
}

if (-not $PythonCmd) {
    Warn "No Python >= 3.11 found."
    if ($HaveWinget) {
        Info "Installing Python 3.12 via winget..."
        winget install --id Python.Python.3.12 --silent --accept-package-agreements --accept-source-agreements
        # Refresh PATH
        $env:Path = [System.Environment]::GetEnvironmentVariable('Path','Machine') + ';' +
                    [System.Environment]::GetEnvironmentVariable('Path','User')
        $PythonCmd = 'python'
        Ok "Installed: $(& python --version)"
    } else {
        Fail "Python 3.11+ is required. Download from https://www.python.org/downloads/ then re-run."
    }
}

# ---------------------------------------------------------------------------
# Step 4 — Git
# ---------------------------------------------------------------------------
Step "Checking Git"

if (-not (Test-Command 'git')) {
    Warn "Git not found."
    if ($HaveWinget) {
        Info "Installing Git via winget..."
        winget install --id Git.Git --silent --accept-package-agreements --accept-source-agreements
        $env:Path = [System.Environment]::GetEnvironmentVariable('Path','Machine') + ';' +
                    [System.Environment]::GetEnvironmentVariable('Path','User')
    } else {
        Fail "Git is required. Download from https://git-scm.com/download/win then re-run."
    }
}
Ok "$(git --version)"

# ---------------------------------------------------------------------------
# Step 5 — Clone or update the repository
# ---------------------------------------------------------------------------
Step "Setting up repository"

$RepoUrl = 'https://github.com/thehipsterciso/hc-enterprise-kg'

if (Test-Path "$InstallDir\.git") {
    Ok "Repository found at $InstallDir"
    if ($SkipPull) {
        Info "SkipPull specified — skipping git pull"
    } else {
        Info "Pulling latest changes..."
        Push-Location $InstallDir
        try {
            $pullOut = git pull --ff-only 2>&1
            Write-Host ($pullOut | ForEach-Object { "    $_" })
        } catch {
            Warn "Could not fast-forward. If you have local changes, re-run with -SkipPull."
        } finally {
            Pop-Location
        }
        Ok "Repository up to date"
    }
} else {
    Info "Cloning $RepoUrl -> $InstallDir ..."
    Invoke-Required 'git' @('clone', $RepoUrl, $InstallDir) "git clone failed"
    Ok "Cloned successfully"
}

Set-Location $InstallDir

# ---------------------------------------------------------------------------
# Step 6 — Poetry
# ---------------------------------------------------------------------------
Step "Checking Poetry"

$PoetryCmd = $null
foreach ($candidate in @('poetry', "$HOME\.local\bin\poetry.exe", "$env:APPDATA\Python\Scripts\poetry.exe")) {
    if (Test-Command $candidate) { $PoetryCmd = $candidate; break }
}

if (-not $PoetryCmd) {
    Warn "Poetry not found. Installing via pip..."
    # pipx is the cleanest approach on Windows
    & $PythonCmd -m pip install --user --quiet pipx 2>&1 | Out-Null
    & $PythonCmd -m pipx ensurepath 2>&1 | Out-Null
    # Refresh PATH so pipx-installed tools are visible
    $env:Path = [System.Environment]::GetEnvironmentVariable('Path','User') + ';' + $env:Path
    pipx install poetry
    $PoetryCmd = 'poetry'
}
Ok "$(& $PoetryCmd --version)"

Step "Installing Python dependencies"
& $PoetryCmd install --extras 'mcp' --no-interaction 2>&1 |
    Where-Object { $_ -match '^(Installing|Updating|No dependencies|Resolving|Writing)' } |
    ForEach-Object { "    $_" } | Write-Host
Ok "Dependencies installed (mcp extras included)"

# ---------------------------------------------------------------------------
# Step 7 — Load the knowledge graph
# ---------------------------------------------------------------------------
$GraphDest = Join-Path $InstallDir 'graph.json'

Step "Loading knowledge graph"
Info "Source: $GraphSource"
Info "Dest  : $GraphDest"

if (Test-Path $GraphSource -PathType Leaf) {
    # Single graph.json snapshot
    Info "Single JSON file — validating..."
    $validateScript = @"
import json, sys
try:
    with open(r'$GraphSource') as f:
        data = json.load(f)
except json.JSONDecodeError as e:
    print(f'    X  Not valid JSON: {e}', file=sys.stderr); sys.exit(1)
if not isinstance(data, dict):
    print('    X  graph.json root must be a JSON object.', file=sys.stderr); sys.exit(1)
ec = len(data.get('entities', []))
rc = len(data.get('relationships', []))
print(f'    v  Valid graph.json - {ec} entities, {rc} relationships')
"@
    & $PythonCmd -c $validateScript
    if ($LASTEXITCODE -ne 0) { Fail "graph.json validation failed" }

    Copy-Item $GraphSource $GraphDest -Force
    Ok "graph.json installed"

} elseif (Test-Path $GraphSource -PathType Container) {
    # Directory of JSON source files
    $jsonFiles = Get-ChildItem -Path $GraphSource -Filter '*.json' | Sort-Object Name
    if ($jsonFiles.Count -eq 0) { Fail "No .json files found in: $GraphSource" }

    Info "Directory mode — found $($jsonFiles.Count) JSON file(s):"
    foreach ($f in $jsonFiles) { Info "    -> $($f.Name)" }

    foreach ($f in $jsonFiles) {
        Info "Importing $($f.Name)..."
        & $PoetryCmd run hckg import $f.FullName 2>&1 | ForEach-Object { "    $_" } | Write-Host
    }
    Ok "All files imported -> graph.json"

} else {
    Fail "GraphSource is neither a file nor a directory: $GraphSource"
}

# ---------------------------------------------------------------------------
# Step 8 — Register with Claude Desktop
# ---------------------------------------------------------------------------
Step "Registering MCP server with Claude Desktop"

# What this step does:
#   Writes an entry into claude_desktop_config.json under "mcpServers".
#   The entry bakes in: the Python interpreter path, [-m, mcp_server.server],
#   and HCKG_DEFAULT_GRAPH=<absolute Windows path to graph.json>.
#   On restart, Claude Desktop spawns the MCP server process with that env var.
#   The server calls auto_load_default_graph() -> JSONIngestor.ingest(path).
#   On every tool call, the server checks the file's mtime and auto-reloads
#   if graph.json changed on disk (no Claude restart needed).

Info "Graph that will be registered: $GraphDest"
Info "Writing to Claude Desktop config..."

& $PoetryCmd run hckg install claude --auto-install --graph $GraphDest 2>&1 |
    ForEach-Object { "    $_" } | Write-Host

if ($LASTEXITCODE -ne 0) {
    Fail "hckg install claude failed. Run: poetry run hckg install doctor"
}

# Show what was actually registered so the user can verify
$ClaudeConfig = Join-Path $env:APPDATA 'Claude\claude_desktop_config.json'
if (Test-Path $ClaudeConfig) {
    Write-Host ""
    Info "Registered config (from $ClaudeConfig):"
    $showScript = @"
import json, sys
with open(r'$ClaudeConfig') as f:
    cfg = json.load(f)
entry = cfg.get('mcpServers', {}).get('hc-enterprise-kg', {})
if not entry:
    print('    ! hc-enterprise-kg entry not found', file=sys.stderr); sys.exit(1)
print(f"    command : {entry.get('command', '?')}")
for a in entry.get('args', []):
    print(f"    arg     : {a}")
if entry.get('cwd'):
    print(f"    cwd     : {entry['cwd']}")
graph = entry.get('env', {}).get('HCKG_DEFAULT_GRAPH', '(none)')
print(f"    graph   : {graph}")
print()
print('    Graph loading chain:')
print('    1. Claude Desktop starts  -> spawns MCP server with HCKG_DEFAULT_GRAPH set')
print(f"    2. Server startup         -> auto_load_default_graph() -> JSONIngestor.ingest('{graph}')")
print('    3. Running                -> mtime-checked on every tool call (auto-reloads if changed)')
"@
    & $PythonCmd -c $showScript
}

Ok "MCP server registered"

# ---------------------------------------------------------------------------
# Done
# ---------------------------------------------------------------------------
Write-Host ""
Write-Host "╔══════════════════════════════════════════════════════╗" -ForegroundColor Green
Write-Host "║   Installation complete!                             ║" -ForegroundColor Green
Write-Host "╚══════════════════════════════════════════════════════╝" -ForegroundColor Green
Write-Host ""
Write-Host "Next steps:" -ForegroundColor White
Write-Host "  1. Close Claude Desktop completely (right-click tray icon -> Quit)"
Write-Host "  2. Reopen Claude Desktop"
Write-Host "  3. In a new chat, try:"
Write-Host "       `"Load my knowledge graph and show the top 10 most connected entities`""
Write-Host ""
Write-Host "Useful commands:" -ForegroundColor White
Write-Host "  Diagnose:        cd $InstallDir; poetry run hckg install doctor"
Write-Host "  Update graph:    Copy-Item C:\new\graph.json $GraphDest"
Write-Host "                   (no restart needed -- server auto-reloads on next tool call)"
Write-Host "  Run demo graph:  cd $InstallDir; poetry run hckg demo --clean"
Write-Host ""
