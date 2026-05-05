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


@dataclass(frozen=True)
class FoodRespawned:
    """Emitted by ``HHModel._apply_food_respawn`` (v0.18) when a previously-
    consumed FOOD cell refills under the cooldown mechanism.

    No agent_id — this is an environmental event. Carries its own ``tick``
    so subscribers (and the events.jsonl writer) can disambiguate ordering
    when multiple cells refill on the same tick.
    """

    x: int
    y: int
    tick: int


@dataclass(frozen=True)
class PoolRespawnDenied:
    """v0.19: a scheduled food respawn was denied because the ambient
    energy pool could not fund the refill (pool < food_value_default).

    Emitted from ``HHModel._apply_food_respawn`` instead of a
    ``FoodRespawned`` for the affected cell. The cell stays EMPTY and
    its respawn schedule is cleared (sentinel reset to 0 — see v0.19
    pre-reg §"Respawn failure semantics", option (i)).
    """

    x: int
    y: int
    tick: int


@dataclass(frozen=True)
class PoolBirthDenied:
    """v0.19: a queued birth was denied because the ambient energy pool
    could not fund the child's startup energy (pool < offspring_start_energy).

    Emitted from ``HHModel._process_birth_queue`` instead of an
    ``AgentBorn`` for the affected parent. The parent's reproduction
    cost is NOT debited; the parent stays alive and re-enters the
    eligibility pool next tick (mirrors the existing
    ``find_adjacent_empty_cell`` rejection contract in
    ``core/reproduction.process_reproduction``).

    Under v0.20 ``PARENT_TRANSFER_POOL_GAP`` mode, this is emitted when
    the pool cannot fund the gap (``offspring_start_energy -
    energy_cost``) rather than the full ``offspring_start_energy``; the
    contract (parent retains energy, no child created) is unchanged.
    """

    parent_id: int
    x: int
    y: int
    tick: int


@dataclass(frozen=True)
class BirthDeniedParentEnergy:
    """v0.20: a queued birth was denied because the parent's body energy
    fell below ``reproduction_cost`` between queueing and birth processing.

    Only emitted under ``PARENT_TRANSFER_POOL_GAP`` mode. Under the v0.7..v0.19
    ``POOL_FULL`` path, ``charge_parent`` debits unconditionally (energy floors
    at 0); v0.20 transfer mode adds an explicit pre-check because routing a
    sub-cost parent contribution into the child would underfund the child's
    startup. On denial, no state changes: parent retains its full energy, pool
    is untouched, no child is created. Parent re-enters the eligibility pool
    next tick.
    """

    parent_id: int
    x: int
    y: int
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
    | FoodRespawned
    | PoolRespawnDenied
    | PoolBirthDenied
    | BirthDeniedParentEnergy
)


@dataclass(frozen=True)
class LoggedEvent:
    """Tick-stamped envelope for an event in ``HHModel.event_log``.

    Most events do not carry their own ``tick`` field (movements, eats,
    hazard damage). Instead of bloating every event dataclass with a tick
    field, the model wraps each event with the current ``tick_count`` at
    emission time. ``io/jsonl_writer.py`` reads the envelope to produce
    ``{"tick": T, "type": ..., "event": {...}}`` JSONL lines.
    """

    tick: int
    event: AnyEvent


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
    FoodRespawned: "hh.food_respawned",
    PoolRespawnDenied: "hh.pool_respawn_denied",
    PoolBirthDenied: "hh.pool_birth_denied",
    BirthDeniedParentEnergy: "hh.birth_denied_parent_energy",
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
