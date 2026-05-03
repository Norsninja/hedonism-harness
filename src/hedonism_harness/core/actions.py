"""Action enum + apply_action — single source of truth for state transitions.

Per SPEC §27.5, ``apply_action`` is the only function that knows how an action
mutates body and world. Predict-one-step calls the same function against a
copied body and consults the returned ``WorldDelta`` for staged cell changes,
so predicted valence cannot drift from realized valence.

Per SPEC §27.4, hazard residency damage and metabolism are applied separately
by the simulation loop after all actions have been applied.

Coordinate convention: ``x`` is the column index, ``y`` is the row index.
North = ``+y``. Layers are indexed ``layer[x, y]``.
"""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from enum import IntEnum

import numpy as np

from hedonism_harness.core.body import AgentBody, apply_energy_delta
from hedonism_harness.core.config import ActionConfig, BodyConfig
from hedonism_harness.core.events import (
    AgentMoved,
    AgentStayed,
    AnyEvent,
    AteFood,
    HazardEntered,
    ReproductionRequested,
)
from hedonism_harness.core.world import CellKind, World, in_bounds


class Action(IntEnum):
    MOVE_NORTH = 0
    MOVE_SOUTH = 1
    MOVE_EAST = 2
    MOVE_WEST = 3
    STAY = 4
    EAT = 5
    REPRODUCE = 6


MOVE_DIRECTIONS: dict[Action, tuple[int, int]] = {
    Action.MOVE_NORTH: (0, 1),
    Action.MOVE_SOUTH: (0, -1),
    Action.MOVE_EAST: (1, 0),
    Action.MOVE_WEST: (-1, 0),
}


@dataclass(frozen=True)
class CellMutation:
    """Per-attribute changes to apply to a single cell. ``None`` = no change."""

    kind: CellKind | None = None
    food_value: float | None = None
    hazard_damage: float | None = None
    safe_value: float | None = None


@dataclass(frozen=True)
class WorldDelta:
    """Sparse set of cell mutations.

    Empty deltas are common (movement, stay) — we use ``EMPTY_DELTA`` as a
    shared sentinel in those cases to avoid per-call dict allocation.
    """

    cells: dict[tuple[int, int], CellMutation] = field(default_factory=dict)


EMPTY_DELTA = WorldDelta()


@dataclass(frozen=True)
class ActionResult:
    """Outcome of applying one action.

    Caller commits ``delta`` via ``commit_delta`` to mutate the live world,
    and dispatches ``events`` to subscribers.
    """

    body: AgentBody
    delta: WorldDelta
    events: tuple[AnyEvent, ...]


def get_valid_actions(world: World, body: AgentBody) -> tuple[Action, ...]:
    """Return the actions ``body`` may legally take from its current state.

    - ``STAY`` is always valid.
    - Movement is invalid when destination is out of bounds or a WALL cell.
    - ``EAT`` is valid only when the current cell is FOOD.
    - ``REPRODUCE`` is filtered out at this layer in v0.1 step 6; reproduction
      validity (energy threshold, age, adjacent space) lands with step 9.
    """
    valid: list[Action] = [Action.STAY]

    for action, (dx, dy) in MOVE_DIRECTIONS.items():
        nx, ny = body.x + dx, body.y + dy
        if not in_bounds(world, nx, ny):
            continue
        if CellKind(int(world.kind_layer[nx, ny])) == CellKind.WALL:
            continue
        valid.append(action)

    if CellKind(int(world.kind_layer[body.x, body.y])) == CellKind.FOOD:
        valid.append(Action.EAT)

    return tuple(valid)


def apply_action(
    world: World,
    body: AgentBody,
    action: Action,
    body_config: BodyConfig,
    action_config: ActionConfig,
    rng: np.random.Generator,  # reserved for stochastic actions in later versions
) -> ActionResult:
    """Apply ``action`` to ``body`` in ``world`` and return the result.

    Pure with respect to inputs: does not mutate ``world`` or ``body``. The
    caller is responsible for committing ``result.delta`` via ``commit_delta``
    and dispatching ``result.events``.

    ``rng`` is reserved in the signature for stochastic actions in later
    versions (e.g. probabilistic hazards); v0.1 actions are deterministic.
    """
    if action == Action.STAY:
        new_body = apply_energy_delta(body, -action_config.stay_cost, body_config)
        return ActionResult(
            body=new_body,
            delta=EMPTY_DELTA,
            events=(AgentStayed(agent_id=body.id, x=body.x, y=body.y),),
        )

    if action in MOVE_DIRECTIONS:
        dx, dy = MOVE_DIRECTIONS[action]
        nx, ny = body.x + dx, body.y + dy
        moved = replace(
            apply_energy_delta(body, -action_config.move_cost, body_config),
            x=nx,
            y=ny,
        )
        events: list[AnyEvent] = [
            AgentMoved(
                agent_id=body.id,
                from_x=body.x,
                from_y=body.y,
                to_x=nx,
                to_y=ny,
            )
        ]
        if CellKind(int(world.kind_layer[nx, ny])) == CellKind.HAZARD:
            events.append(HazardEntered(agent_id=body.id, x=nx, y=ny))
        return ActionResult(body=moved, delta=EMPTY_DELTA, events=tuple(events))

    if action == Action.EAT:
        food_gain = float(world.food_value[body.x, body.y])
        fed = apply_energy_delta(body, food_gain, body_config)
        if action_config.eat_cost > 0:
            fed = apply_energy_delta(fed, -action_config.eat_cost, body_config)
        delta = WorldDelta(
            cells={(body.x, body.y): CellMutation(kind=CellKind.EMPTY, food_value=0.0)}
        )
        return ActionResult(
            body=fed,
            delta=delta,
            events=(AteFood(agent_id=body.id, x=body.x, y=body.y, food_gained=food_gain),),
        )

    if action == Action.REPRODUCE:
        # Validity + child construction are wired up in SPEC §26.12 step 9.
        # apply_action emits the request; the simulation's birth queue handles
        # actual child creation on the following tick.
        return ActionResult(
            body=body,
            delta=EMPTY_DELTA,
            events=(ReproductionRequested(agent_id=body.id, x=body.x, y=body.y),),
        )

    msg = f"Unknown action: {action!r}"
    raise ValueError(msg)


def action_energy_cost(action: Action, action_config: ActionConfig) -> float:
    """Return the energy cost the body pays for taking ``action``.

    Used by the Hedonism Harness to compute ``effort_cost`` independent of body
    energy clamping (which would otherwise hide costs when energy hits the cap
    after eating).

    REPRODUCE returns 0 in v0.1 step 6; the reproduction energy cost lands
    with step 9.
    """
    if action == Action.STAY:
        return action_config.stay_cost
    if action in MOVE_DIRECTIONS:
        return action_config.move_cost
    if action == Action.EAT:
        return action_config.eat_cost
    if action == Action.REPRODUCE:
        return 0.0
    msg = f"Unknown action: {action!r}"
    raise ValueError(msg)


def commit_delta(world: World, delta: WorldDelta) -> None:
    """Apply a ``WorldDelta`` to the live world's NumPy layers in place."""
    for (x, y), mutation in delta.cells.items():
        if mutation.kind is not None:
            world.kind_layer[x, y] = mutation.kind
        if mutation.food_value is not None:
            world.food_value[x, y] = mutation.food_value
        if mutation.hazard_damage is not None:
            world.hazard_damage[x, y] = mutation.hazard_damage
        if mutation.safe_value is not None:
            world.safe_value[x, y] = mutation.safe_value
