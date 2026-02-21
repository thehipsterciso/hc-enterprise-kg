# ADR-004: KnowledgeGraph Facade with Event Bus

**Status:** Accepted
**Date:** 2026-02-21
**Context:** Application-level graph interface and mutation tracking

---

## Summary

A `KnowledgeGraph` class serves as the single entry point for all graph operations. It wraps the engine backend with an in-process synchronous event bus and a fluent query builder. Every consumer (synthetic pipeline, MCP server, REST API, analysis module) interacts with this facade, never with the engine directly.

---

## Decision

Implement a facade pattern with synchronous event dispatch on every graph mutation.

---

## Alternatives Considered

| Alternative | Assessment |
|-------------|------------|
| **Direct engine access** | Callers use `NetworkXGraphEngine` directly. Simpler, fewer layers. No cross-cutting concerns (events, query abstraction). Every consumer must handle engine setup and entity registry initialization independently |
| **Repository pattern per entity type** | `PersonRepository`, `SystemRepository`, etc. Type-safe but creates 30 repository classes with significant duplication. Fragmented interface — callers must know which repository to use |
| **CQRS (Command Query Responsibility Segregation)** | Separate read/write models. Appropriate for distributed systems with eventual consistency. Overengineered for a single-process, in-memory graph |
| **No abstraction** | Use NetworkX `MultiDiGraph` directly throughout the codebase. Eliminates indirection but couples every module to NetworkX and makes backend migration impossible |

---

## What the Facade Provides

### 1. Initialization Coordination

On construction, `KnowledgeGraph` calls `EntityRegistry.auto_discover()` and `GraphEngineFactory.auto_discover()`. This ensures all 30 entity types and the engine backend are registered before any operation. Without the facade, every consumer would need to remember this initialization sequence.

### 2. Synchronous Event Bus

Every mutating operation (CREATE, UPDATE, DELETE, LINK, UNLINK) emits a `GraphEvent` through the `EventBus`:

- `EventBus.subscribe(handler, mutation_type)` -- Register a callback for specific mutations or all mutations (mutation_type=None)
- `EventBus.emit(event)` -- Synchronous dispatch to all matching handlers
- `GraphEvent` captures `mutation_type`, `entity_type`, `entity_id`, `relationship_id`, `before_snapshot`, `after_snapshot`

The event log is also stored as an unbounded in-memory list (`_event_log`) for audit trail access.

### 3. Fluent Query Builder

`kg.query()` returns a `QueryBuilder` that chains `.entities()`, `.where()`, `.connected_to()`, `.limit()`, `.offset()`, `.execute()`. This provides a readable API for filtered traversals without requiring callers to understand engine internals.

---

## Where This Diverges from Best Practice

### The Event Bus is Synchronous and In-Process

Modern event-driven architectures use asynchronous message brokers (Kafka, RabbitMQ, Redis Streams) for event dispatch. Our event bus is a `defaultdict(list)` of handler functions called inline during mutation. There is no queue, no retry, no ordering guarantee beyond call order, no persistence.

This is intentional. The graph is in-memory. The process is single-threaded. The consumers are local. An async message broker would add operational complexity without solving a problem that exists at this scale.

The cost: if a handler throws an exception, it propagates into the mutation call. If a handler is slow, it blocks the mutation. If the process crashes, the event log is lost.

### The Event Log is Unbounded

`_event_log` is a `list[GraphEvent]` that grows with every mutation. For a generation run producing ~800 entities and ~1,500 relationships, that is ~2,300 events. At ~500 bytes per event, this is ~1.1 MB — negligible. For an application that performs millions of mutations over time, this would be a memory leak.

The project does not perform millions of mutations. Generation runs once, the graph is used for analysis, and the process exits. But if the graph were used in a long-running service with continuous mutations, the unbounded log would need rotation or persistence.

---

## Trade-Offs

| Benefit | Cost |
|---------|------|
| Single initialization point for registry and engine | One layer of indirection on every call |
| Audit trail on every mutation | Unbounded event log in memory |
| Subscriber pattern for reactive logic | Synchronous handlers block mutations |
| Fluent query API | QueryBuilder loads all entities then filters in Python (no query pushdown) |
| Engine isolation (consumers never import the backend) | Facade must proxy every engine method |

---

## Risks

1. **Event log memory growth** -- Unbounded list grows with mutations. Acceptable for batch generation, problematic for long-running services. Mitigated by the current usage pattern (generate, analyze, exit)
2. **Handler exceptions** -- A failing subscriber handler crashes the mutation operation. Mitigated by the current absence of error-prone handlers (no subscribers are registered by default)
3. **Query performance** -- `QueryBuilder.execute()` calls `list_entities()` to load all matching entities, then applies traversal filters in Python. No query pushdown to the engine. Acceptable for sub-20k entity graphs

---

## Re-Evaluation Triggers

- Long-running service usage pattern requiring event log rotation
- Performance profiling showing facade overhead is significant
- Need for asynchronous event processing or external subscribers
- Query patterns requiring engine-level optimization (index-backed filtering)

---

## References

- `src/graph/knowledge_graph.py` -- `KnowledgeGraph` facade
- `src/graph/events.py` -- `EventBus` with synchronous dispatch
- `src/engine/query.py` -- `QueryBuilder` fluent API
- `src/domain/temporal.py` -- `GraphEvent`, `MutationType` definitions
