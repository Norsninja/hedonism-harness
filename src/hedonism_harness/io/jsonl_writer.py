"""Per-tick events as JSON Lines (SPEC §17, §27.8).

Each entry on the wire is a tick-stamped envelope::

    {"tick": 12, "type": "AgentMoved", "event": {...}}

The model stores ``LoggedEvent`` envelopes in ``HHModel.event_log``. The
writer takes any iterable of ``LoggedEvent`` and serializes one envelope per
line, preserving emission order. Enums are serialized as name strings so the
output is fully JSON-decodable without custom handlers.

Per SPEC §27.11, this layer may import ``core/events`` and stdlib only.
"""

from __future__ import annotations

import json
from dataclasses import asdict
from typing import TYPE_CHECKING

from hedonism_harness.core.body import DeathCause
from hedonism_harness.core.events import AgentDied

if TYPE_CHECKING:
    from collections.abc import Iterable
    from pathlib import Path

    from hedonism_harness.core.events import AnyEvent, LoggedEvent


def _event_payload(event: AnyEvent) -> dict[str, object]:
    """Return a JSON-friendly dict for one event (enums -> name strings)."""
    payload = asdict(event)
    if isinstance(event, AgentDied):
        cause = payload.get("cause")
        if isinstance(cause, DeathCause):
            payload["cause"] = cause.name
    return payload


def _serialize(logged: LoggedEvent) -> dict[str, object]:
    """Wrap a ``LoggedEvent`` as the on-wire envelope."""
    return {
        "tick": logged.tick,
        "type": type(logged.event).__name__,
        "event": _event_payload(logged.event),
    }


def write_events_jsonl(path: Path, logged_events: Iterable[LoggedEvent]) -> None:
    """Write tick-stamped envelopes to ``path`` one per line, preserving order."""
    with path.open("w") as f:
        for logged in logged_events:
            f.write(json.dumps(_serialize(logged), sort_keys=True))
            f.write("\n")


def append_events_jsonl(path: Path, logged_events: Iterable[LoggedEvent]) -> None:
    """Append envelopes without truncating — used for streaming during long runs."""
    with path.open("a") as f:
        for logged in logged_events:
            f.write(json.dumps(_serialize(logged), sort_keys=True))
            f.write("\n")
