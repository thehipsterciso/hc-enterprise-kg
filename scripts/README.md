# CMU CDAIO Install Scripts

Zero-touch setup for CMU CDAIO team members. One command installs everything
and wires up Claude Desktop.

## macOS / Linux

```bash
bash cmu-cdaio-install.sh /path/to/graph.json
# or a directory of JSON source files:
bash cmu-cdaio-install.sh /path/to/rackspace-jsons/
```

## Windows (PowerShell)

Right-click PowerShell → "Run as Administrator" (first time only, to set execution policy):

```powershell
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
```

Then run:

```powershell
.\cmu-cdaio-install.ps1 C:\path\to\graph.json
# or a directory:
.\cmu-cdaio-install.ps1 C:\path\to\rackspace-jsons\
```

## What the scripts do

| Step | macOS/Linux | Windows |
|------|-------------|---------|
| Prereqs | brew / apt / dnf | winget |
| Python ≥ 3.11 | auto-install if missing | auto-install if missing |
| Git | auto-install if missing | auto-install if missing |
| Repo | `git clone` or `git pull` | `git clone` or `git pull` |
| Dependencies | `poetry install --extras mcp` | `poetry install --extras mcp` |
| Graph (single file) | validates JSON, copies to repo root | validates JSON, copies to repo root |
| Graph (directory) | `hckg import` each `.json` in order | `hckg import` each `.json` in order |
| Claude Desktop | `hckg install claude --auto-install` | `hckg install claude --auto-install` |
| Verify | prints registered config + loading chain | prints registered config + loading chain |

## How the graph is loaded

```
graph.json on disk
  └─ path registered as HCKG_DEFAULT_GRAPH in claude_desktop_config.json
       └─ Claude Desktop restart spawns MCP server with that env var
            └─ auto_load_default_graph() → JSONIngestor.ingest(path) → in memory
                 └─ every tool call: mtime check → auto-reload if file changed
```

**Updating the graph** (no Claude restart required):

```bash
# macOS/Linux
cp /new/graph.json ~/hc-enterprise-kg/graph.json

# Windows
Copy-Item C:\new\graph.json $HOME\hc-enterprise-kg\graph.json
```

The server detects the changed mtime on the next tool call and reloads automatically.

## Environment variable overrides

| Variable | Default | Purpose |
|----------|---------|---------|
| `HCKG_INSTALL_DIR` | `~/hc-enterprise-kg` | Override clone location (bash) |
| `HCKG_SKIP_PULL` | `0` | Set to `1` to skip git pull |
| `-InstallDir` | `$HOME\hc-enterprise-kg` | Override clone location (PowerShell) |
| `-SkipPull` | (off) | Skip git pull (PowerShell) |

## Troubleshooting

```bash
# macOS/Linux
cd ~/hc-enterprise-kg && poetry run hckg install doctor

# Windows
cd $HOME\hc-enterprise-kg; poetry run hckg install doctor
```
