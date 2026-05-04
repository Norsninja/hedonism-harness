"""Typed event dataclasses + named blinker signals (SPEC §27.8).

Core/ emits events. Metrics/ subscribes to interpret. Io/ persists what
metrics produces.

The signal table at the bottom of this module gives every event type a
process-wide ``blinker.NamedSignal``. Emitters do not subscribe; subscribers
live in ``metrics/aggregators.py``. Tests can connect ad-hoc via
``signal_for(EventType).connect(callback)``. Per SPEC §27.11, ``core/`` may
import blinker — it is the one cross-cutting communication primitive allowed
in the scientific layer.

All events carry the simulation tick implicitly via the emission site or the
subscriber's clock; we only attach a ``tick`` field where the event is
decoupled from per-tick emission (births, deaths, lineage events).
"""

from __future__ import annotations

from dataclasses import dataclass

import blinker

from hedonism_harness.core.body import DeathCause


@dataclass(frozen=True)
class AgentMoved:
    agent_id: int
    from_x: int
    from_y: int
    to_x: int
    to_y: int


@dataclass(frozen=True)
class AgentStayed:
    agent_id: int
    x: int
    y: int


@dataclass(frozen=True)
class AteFood:
    agent_id: int
    x: int
    y: int
    food_gained: float


@dataclass(frozen=True)
class HazardEntered:
    """Emitted when an agent moves into a HAZARD cell. Damage event is separate."""

    agent_id: int
    x: int
    y: int


@dataclass(frozen=True)
class HazardDamageApplied:
    """Emitted by the simulation loop after per-tick hazard residency damage."""

    agent_id: int
    x: int
    y: int
    damage: float


@dataclass(frozen=True)
class ReproductionRequested:
    """Emitted when an agent takes the REPRODUCE action.

    The simulation loop's birth queue consumes this and produces ``AgentBorn``.
    """

    agent_id: int
    x: int
    y: int


@dataclass(frozen=True)
class AgentBorn:
    agent_id: int
    parent_id: int
    lineage_id: int
    x: int
    y: int
    tick: int


@dataclass(frozen=True)
class AgentDied:
    agent_id: int
    cause: DeathCause
    tick: int


AnyEvent = (
    AgentMoved
    | AgentStayed
    | AteFood
    | HazardEntered
    | HazardDamageApplied
    | ReproductionRequested
    | AgentBorn
    | AgentDied
)


# ---------------------------------------------------------------------------
# Named blinker signals — one per event type
# ---------------------------------------------------------------------------
#
# Subscribers connect via ``signal_for(EventType).connect(handler)``. Senders
# call ``signal_for(type(event)).send(model, event=event)``. The ``model``
# sender lets subscribers filter by simulation instance during batch runs.
#
# Signals are NamedSignals (process-wide singletons keyed by name); creating a
# second signal with the same name returns the same object. Tests can
# disconnect handlers in teardown via ``.disconnect(handler)``.

_SIGNAL_NAMES: dict[type, str] = {
    AgentMoved: "hh.agent_moved",
    AgentStayed: "hh.agent_stayed",
    AteFood: "hh.ate_food",
    HazardEntered: "hh.hazard_entered",
    HazardDamageApplied: "hh.hazard_damage_applied",
    ReproductionRequested: "hh.reproduction_requested",
    AgentBorn: "hh.agent_born",
    AgentDied: "hh.agent_died",
}


def signal_for(event_type: type) -> blinker.NamedSignal:
    """Return the blinker signal corresponding to an event class."""
    name = _SIGNAL_NAMES.get(event_type)
    if name is None:
        msg = f"No signal registered for event type {event_type!r}"
        raise KeyError(msg)
    return blinker.signal(name)


def emit(sender: object, event: AnyEvent) -> None:
    """Send ``event`` on its named signal. ``sender`` is conventionally the model."""
    signal_for(type(event)).send(sender, event=event)
