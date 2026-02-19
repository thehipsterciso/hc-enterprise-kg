"""Event bus for graph mutation events."""

from __future__ import annotations

from collections import defaultdict
from typing import Callable

from domain.temporal import GraphEvent, MutationType

EventHandler = Callable[[GraphEvent], None]


class EventBus:
    """Simple in-process event bus for graph mutation events.

    Subscribers register callbacks for specific mutation types (or all).
    Events are dispatched synchronously.
    """

    def __init__(self) -> None:
        self._handlers: dict[MutationType | None, list[EventHandler]] = defaultdict(list)

    def subscribe(
        self,
        handler: EventHandler,
        mutation_type: MutationType | None = None,
    ) -> None:
        """Subscribe to events. None means subscribe to all mutation types."""
        self._handlers[mutation_type].append(handler)

    def unsubscribe(
        self,
        handler: EventHandler,
        mutation_type: MutationType | None = None,
    ) -> None:
        """Remove a handler subscription."""
        handlers = self._handlers.get(mutation_type, [])
        if handler in handlers:
            handlers.remove(handler)

    def emit(self, event: GraphEvent) -> None:
        """Dispatch an event to all matching handlers."""
        for handler in self._handlers.get(event.mutation_type, []):
            handler(event)
        for handler in self._handlers.get(None, []):
            handler(event)

    @property
    def handler_count(self) -> int:
        return sum(len(h) for h in self._handlers.values())
