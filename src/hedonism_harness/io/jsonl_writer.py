"""Per-tick events as JSON Lines (SPEC §17, §27.8).

Each event becomes one JSON object per line, in the order it was emitted.
Schema is the dataclass field set plus an ``event`` discriminator and an
``emitted_tick`` field (when known — only ``AgentBorn``/``AgentDied`` carry
their own tick).

Per SPEC §27.11, this layer may import ``core/events`` and stdlib only.
"""

from __future__ import annotations

import json
from dataclasses import asdict
from typing import TYPE_CHECKING

from hedonism_harness.core.body import DeathCause
from hedonism_harness.core.events import AgentBorn, AgentDied

if TYPE_CHECKING:
    from collections.abc import Iterable
    from pathlib import Path

    from hedonism_harness.core.events import AnyEvent


def _serialize(event: AnyEvent) -> dict[str, object]:
    """Return a JSON-friendly dict for one event (enums -> name strings)."""
    payload = asdict(event)
    if isinstance(event, AgentDied):
        cause = payload.get("cause")
        if isinstance(cause, DeathCause):
            payload["cause"] = cause.name
    payload["event"] = type(event).__name__
    if isinstance(event, (AgentBorn, AgentDied)):
        payload["emitted_tick"] = event.tick
    return payload


def write_events_jsonl(path: Path, events: Iterable[AnyEvent]) -> None:
    """Write events to ``path`` one JSON object per line, preserving order."""
    with path.open("w") as f:
        for event in events:
            f.write(json.dumps(_serialize(event), sort_keys=True))
            f.write("\n")


def append_events_jsonl(path: Path, events: Iterable[AnyEvent]) -> None:
    """Append events without truncating — used for streaming during long runs."""
    with path.open("a") as f:
        for event in events:
            f.write(json.dumps(_serialize(event), sort_keys=True))
            f.write("\n")
