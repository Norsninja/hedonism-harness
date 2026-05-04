"""Typed event dataclasses (SPEC §27.8).

Core/ emits events. Metrics/ interprets them. Io/ persists them.

Blinker signal wiring lives in ``metrics/`` so this module stays a pure data
layer with no subscriber knowledge — modules that *emit* events depend only
on the dataclasses defined here.

All events carry the simulation tick implicitly via the emission site or the
subscriber's clock; we only attach a ``tick`` field where the event is decoupled
from per-tick emission (births, deaths, lineage events).
"""

from __future__ import annotations

from dataclasses import dataclass

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
