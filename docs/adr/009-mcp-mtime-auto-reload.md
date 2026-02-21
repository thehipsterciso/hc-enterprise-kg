# ADR-009: MCP Server with mtime-Based Auto-Reload

**Status:** Accepted
**Date:** 2026-02-21
**Context:** MCP server state management and graph file change detection

---

## Summary

The MCP server uses a module-level singleton `KnowledgeGraph` instance with file modification time (mtime) polling on every tool call to detect when graph.json changes on disk. After `hckg demo --clean`, the next Claude Desktop tool call automatically picks up the new graph without server restart or manual reload.

Zero dependencies. Zero threads. One `os.path.getmtime()` call per tool invocation.

---

## Decision

Poll file mtime on every tool call. Reload the graph if the file has changed since last load.

---

## How It Works

```
_kg: KnowledgeGraph | None = None    # Module-level singleton
_loaded_path: str | None = None       # Last loaded file path
_loaded_mtime: float = 0.0            # Last known modification time

require_graph() → KnowledgeGraph:
    1. Call _maybe_reload()
    2. _maybe_reload() checks os.path.getmtime(_loaded_path)
    3. If mtime differs from _loaded_mtime, re-ingest the file
    4. Return _kg (newly loaded or existing)
```

Every MCP tool calls `require_graph()` before accessing the graph. The mtime check adds microseconds — one `stat()` syscall.

---

## Alternatives Considered

| Alternative | Assessment |
|-------------|------------|
| **File system watcher (watchdog, inotify)** | Background thread monitors file changes, triggers reload. Requires the `watchdog` dependency or platform-specific `inotify`/`FSEvents`. Adds threading complexity (the MCP stdio transport is single-threaded). A daemon thread for a file that changes once per session |
| **Manual reload** | User must call `load_graph` tool in Claude Desktop after every `hckg demo --clean`. Friction for the most common workflow. Users will forget, get stale data, and file bugs |
| **Timer-based polling** | Check mtime every N seconds on a background timer. Uses CPU when idle. Still requires threading. Adds latency between file change and detection. The per-call check is both simpler and more responsive |
| **Database backend with live queries** | No file to watch — queries hit a live database. Requires a running database (contradicts the zero-infrastructure decision in ADR-003). Adds operational complexity for a solved problem |
| **IPC signal from CLI to server** | `hckg demo` sends a signal (Unix socket, named pipe) to the MCP server when generation completes. Requires inter-process communication infrastructure. Platform-specific. Tight coupling between CLI and server |

---

## Rationale

1. **Zero dependencies** -- `os.path.getmtime()` is stdlib. No watchdog, no threading, no platform-specific file watching
2. **Zero threads** -- The MCP stdio transport is single-threaded by design. Adding a watcher thread introduces concurrency concerns (thread safety of module-level globals, GIL contention) for no benefit
3. **Responsive** -- The reload happens on the next tool call after the file changes. For the Claude Desktop workflow (regenerate graph, then query it), the very first query after regeneration gets the new data
4. **Microsecond cost** -- One `stat()` syscall per tool call. On modern filesystems this is <1μs. Negligible compared to the graph query itself

---

## Where This Diverges from Best Practice

### Module-Level Globals

`_kg`, `_loaded_path`, and `_loaded_mtime` are module-level mutable state. In a multi-threaded or multi-process context, this is unsafe — two concurrent tool calls could race on `_maybe_reload()`, both detecting a changed mtime, both triggering a reload, and one getting a partially loaded graph.

This is acceptable because the MCP stdio transport is single-threaded. Tool calls are sequential, not concurrent. But the code is not thread-safe by design, and adapting it to a multi-connection transport would require locks or a different state management pattern.

### No File Locking

If a tool call arrives while `hckg demo --clean` is writing graph.json, the server may load a partial file. The `JSONIngestor` would either parse incomplete JSON (and fail with an error dict) or parse a complete but outdated version (if the OS buffer has not flushed).

In practice, graph generation completes in under 8 seconds and writes atomically via `Path.write_text()`. The window for this race is small. But there is no file locking, no write-then-rename atomic swap, and no retry logic.

### No Proactive Notification

The server cannot tell Claude Desktop "new data is available." It waits passively for the next tool call. If a user regenerates the graph but does not make another query, the old data persists silently. This is a pull model, not push.

For the Claude Desktop workflow this is fine — users regenerate because they intend to query. For a hypothetical multi-client scenario, proactive notification would be necessary.

---

## Trade-Offs

| Benefit | Cost |
|---------|------|
| Zero dependencies, zero threads | Module-level globals are not thread-safe |
| Microsecond detection cost | No file locking during reload |
| Transparent to the user — just works | No proactive notification to clients |
| Simpler than every alternative considered | Race condition window during file write |

---

## Risks

1. **Partial file load** -- If reload happens during file write, the graph may be corrupt. Mitigated by the small write window and `JSONIngestor` error handling
2. **State management** -- Module-level globals are the simplest possible state management. Any evolution toward multi-connection support requires rethinking this. Mitigated by the single-threaded MCP transport assumption
3. **Silent stale data** -- If `os.path.getmtime()` fails (file deleted, permission error), `_maybe_reload()` silently returns. The server continues with the old graph without alerting the user

---

## Re-Evaluation Triggers

- MCP transport changes to support concurrent connections
- Users report stale data after graph regeneration (race condition evidence)
- Need for proactive push notification to Claude Desktop
- File write atomicity becomes a reliability issue

---

## References

- `src/mcp_server/state.py` -- `_maybe_reload()`, `require_graph()`, module-level globals
- `src/mcp_server/server.py` -- MCP tool registrations calling `require_graph()`
- `docs/adr/003-networkx-multidigraph.md` -- Related: zero-infrastructure backend choice
