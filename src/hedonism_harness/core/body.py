"""Pure agent body: dataclass + lifecycle helpers (SPEC §27.9).

``AgentBody`` is intentionally separate from the Mesa agent wrapper. It carries
all per-agent state that the science cares about — position, energy, health,
age, traits — but knows nothing about Mesa, scheduling, policies, or events.

Per SPEC §27.5 (predict-one-step), the body is frozen and updated via
``dataclasses.replace`` so a cheap copy can be passed through ``apply_action``
during action scoring without disturbing the live body.

Naming: ``AgentBody`` (not ``Agent``) avoids collision with Mesa's ``Agent``.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from enum import IntEnum

from hedonism_harness.core.config import BodyConfig
from hedonism_harness.core.traits import Traits


class DeathCause(IntEnum):
    """Why an agent died. Set on ``AgentBody.death_cause`` when ``alive`` flips."""

    STARVATION = 1
    INJURY = 2
    INTERVENTION = 3  # v0.42: experimental intervention killed this agent.


@dataclass(frozen=True)
class AgentBody:
    """All per-agent state that domain logic reads from or writes to."""

    id: int
    lineage_id: int
    parent_id: int | None
    x: int
    y: int
    energy: float
    health: float
    age: int
    traits: Traits
    alive: bool = True
    death_cause: DeathCause | None = None


def make_body(
    *,
    body_id: int,
    lineage_id: int,
    parent_id: int | None,
    x: int,
    y: int,
    traits: Traits,
    config: BodyConfig,
) -> AgentBody:
    """Construct a fresh body at full starting state."""
    return AgentBody(
        id=body_id,
        lineage_id=lineage_id,
        parent_id=parent_id,
        x=x,
        y=y,
        energy=config.starting_energy,
        health=config.starting_health,
        age=0,
        traits=traits,
    )


def apply_metabolism(body: AgentBody, config: BodyConfig) -> AgentBody:
    """Apply per-tick energy decay and increment age.

    Cost = ``base_metabolic_cost * traits.metabolic_rate +
    sensor_radius_metabolic_cost * traits.sensor_radius``.
    Energy floor is 0; death is determined by ``is_dead`` after this call.
    """
    cost = (
        config.base_metabolic_cost * body.traits.metabolic_rate
        + config.sensor_radius_metabolic_cost * body.traits.sensor_radius
    )
    new_energy = max(0.0, body.energy - cost)
    return replace(body, energy=new_energy, age=body.age + 1)


def apply_damage(body: AgentBody, amount: float) -> AgentBody:
    """Reduce health by ``amount``, flooring at 0. ``amount`` must be non-negative."""
    if amount < 0:
        msg = f"apply_damage requires non-negative amount, got {amount}"
        raise ValueError(msg)
    return replace(body, health=max(0.0, body.health - amount))


def apply_energy_delta(body: AgentBody, delta: float, config: BodyConfig) -> AgentBody:
    """Add ``delta`` to energy, clamped to ``[0, max_energy]``.

    Used for eating (positive delta) and action costs (negative delta).
    """
    new_energy = max(0.0, min(config.max_energy, body.energy + delta))
    return replace(body, energy=new_energy)


def is_dead(body: AgentBody) -> bool:
    """True iff energy or health has hit zero. Death cause is not set here."""
    return body.energy <= 0.0 or body.health <= 0.0


def infer_death_cause(body: AgentBody) -> DeathCause | None:
    """Return the ``DeathCause`` implied by current vitals, or ``None`` if alive.

    If both vitals are at zero simultaneously, ``INJURY`` wins (zero health
    is a more acute proximate cause than zero energy).
    """
    if body.health <= 0.0:
        return DeathCause.INJURY
    if body.energy <= 0.0:
        return DeathCause.STARVATION
    return None


def mark_dead(body: AgentBody, cause: DeathCause) -> AgentBody:
    """Flip ``alive`` to False and record ``death_cause``. Idempotent on repeats."""
    return replace(body, alive=False, death_cause=cause)
