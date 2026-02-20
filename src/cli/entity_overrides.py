"""Shared CLI options for entity count overrides.

Provides a Click decorator that adds --systems, --vendors, --controls, etc.
flags to any CLI command. The decorator collects all provided overrides into
a dict[str, int] mapping EntityType.value → count.
"""

from __future__ import annotations

import functools
from typing import TYPE_CHECKING, Any

import click

if TYPE_CHECKING:
    from collections.abc import Callable

from synthetic.orchestrator import OVERRIDABLE_ENTITIES

# Build the list of Click options from OVERRIDABLE_ENTITIES.
# Each option is --{name} with type=int and default=None.
_OVERRIDE_OPTIONS: list[tuple[str, str]] = [
    (cli_name, entity_type.value) for cli_name, entity_type in OVERRIDABLE_ENTITIES.items()
]


def _build_help(cli_name: str) -> str:
    """Build help text for an entity count override flag."""
    label = cli_name.replace("_", " ")
    return f"Override {label} count (bypasses scaling)."


def entity_count_overrides(func: Callable[..., Any]) -> Callable[..., Any]:
    """Click decorator that adds --systems, --vendors, etc. override flags.

    Injects a `count_overrides` keyword argument (dict[str, int]) into the
    decorated function containing all entity count overrides that were provided.

    Usage:
        @click.command()
        @entity_count_overrides
        def my_command(count_overrides, **kwargs):
            orchestrator = SyntheticOrchestrator(kg, profile, count_overrides=count_overrides)
    """

    @functools.wraps(func)
    def wrapper(**kwargs: Any) -> Any:
        # Collect all provided overrides into a dict
        overrides: dict[str, int] = {}
        for cli_name, entity_value in _OVERRIDE_OPTIONS:
            value = kwargs.pop(cli_name, None)
            if value is not None:
                overrides[entity_value] = value
        kwargs["count_overrides"] = overrides
        return func(**kwargs)

    # Apply Click options in reverse order so they appear in declaration order
    for cli_name, _entity_value in reversed(_OVERRIDE_OPTIONS):
        wrapper = click.option(
            f"--{cli_name.replace('_', '-')}",
            cli_name,
            type=int,
            default=None,
            help=_build_help(cli_name),
        )(wrapper)

    return wrapper
