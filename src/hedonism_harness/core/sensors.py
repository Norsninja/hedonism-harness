"""Partial-information sensors (SPEC §10).

``observe(world, body, memory=None) -> Observation`` is a pure function. It is
called once per agent per tick before action selection, and once per candidate
action during predict-one-step.

Three sensor groups (all assembled into a single ``Observation``):

  - Internal: derived from ``body`` only (energy/health ratios, hunger, etc.).
  - External: directional food/hazard signals computed by orthogonal axial scans
    out to ``traits.sensor_radius`` cells. Per §10.2: ``signal += value / distance``.
  - Memory: directional remembered-good / remembered-bad signals. Read from
    ``ValenceMemory`` when present; zero when memory is ``None``.

Memory fields are always present in ``Observation`` so the harness has a
uniform interface across ``HedonismPolicy`` (no memory) and
``MemoryHedonismPolicy`` (with memory). When memory is disabled, those fields
score neutrally in the harness.

Memory module wiring lands with SPEC §26.12 step 12 (memory.py); for now this
module accepts a ``memory`` argument typed as ``object | None`` so memory.py
can land without changing this signature.
"""

from __future__ import annotations

from dataclasses import dataclass

from hedonism_harness.core.body import AgentBody
from hedonism_harness.core.config import BodyConfig
from hedonism_harness.core.world import CellKind, World, in_bounds


@dataclass(frozen=True)
class Observation:
    """Everything an agent's policy is allowed to read at decision time."""

    # Internal
    energy_ratio: float
    health_ratio: float
    hunger_level: float
    injury_level: float
    age: int

    # External — directional food signal (sum of value / distance along axis).
    food_signal_north: float
    food_signal_south: float
    food_signal_east: float
    food_signal_west: float

    # External — directional hazard signal.
    hazard_signal_north: float
    hazard_signal_south: float
    hazard_signal_east: float
    hazard_signal_west: float

    # Cell-local readouts at the body's current position.
    on_food: bool
    on_hazard: bool
    on_safe: bool
    current_food_value: float
    current_hazard_damage: float
    current_safe_value: float

    # Memory — directional remembered good/bad. Zero when memory disabled.
    remembered_good_north: float = 0.0
    remembered_good_south: float = 0.0
    remembered_good_east: float = 0.0
    remembered_good_west: float = 0.0
    remembered_bad_north: float = 0.0
    remembered_bad_south: float = 0.0
    remembered_bad_east: float = 0.0
    remembered_bad_west: float = 0.0


# Step (dx, dy) for each direction, used by both external and memory scans.
_DIRECTION_STEPS: dict[str, tuple[int, int]] = {
    "north": (0, 1),
    "south": (0, -1),
    "east": (1, 0),
    "west": (-1, 0),
}


def _scan_axial(
    layer,
    origin_x: int,
    origin_y: int,
    width: int,
    height: int,
    dx: int,
    dy: int,
    radius: int,
) -> float:
    """Sum ``layer[x, y] / distance`` along an axial ray of length ``radius``."""
    total = 0.0
    for d in range(1, radius + 1):
        x, y = origin_x + dx * d, origin_y + dy * d
        if not (0 <= x < width and 0 <= y < height):
            break
        value = float(layer[x, y])
        if value != 0.0:
            total += value / d
    return total


def observe(
    world: World,
    body: AgentBody,
    body_config: BodyConfig,
    memory: object | None = None,
) -> Observation:
    """Build an ``Observation`` from world + body (+ optional memory).

    Pure: does not mutate any input.
    """
    radius = int(body.traits.sensor_radius)
    energy_ratio = body.energy / body_config.max_energy
    health_ratio = body.health / body_config.max_health

    # External signals: four axial scans.
    food_signals: dict[str, float] = {}
    hazard_signals: dict[str, float] = {}
    for name, (dx, dy) in _DIRECTION_STEPS.items():
        food_signals[name] = _scan_axial(
            world.food_value, body.x, body.y, world.width, world.height, dx, dy, radius
        )
        hazard_signals[name] = _scan_axial(
            world.hazard_damage, body.x, body.y, world.width, world.height, dx, dy, radius
        )

    cur_kind = (
        CellKind(int(world.kind_layer[body.x, body.y]))
        if in_bounds(world, body.x, body.y)
        else CellKind.EMPTY
    )

    memory_signals = _read_memory_directional(memory, body, world)

    return Observation(
        energy_ratio=energy_ratio,
        health_ratio=health_ratio,
        hunger_level=1.0 - energy_ratio,
        injury_level=1.0 - health_ratio,
        age=body.age,
        food_signal_north=food_signals["north"],
        food_signal_south=food_signals["south"],
        food_signal_east=food_signals["east"],
        food_signal_west=food_signals["west"],
        hazard_signal_north=hazard_signals["north"],
        hazard_signal_south=hazard_signals["south"],
        hazard_signal_east=hazard_signals["east"],
        hazard_signal_west=hazard_signals["west"],
        on_food=cur_kind == CellKind.FOOD,
        on_hazard=cur_kind == CellKind.HAZARD,
        on_safe=cur_kind == CellKind.SAFE,
        current_food_value=float(world.food_value[body.x, body.y]),
        current_hazard_damage=float(world.hazard_damage[body.x, body.y]),
        current_safe_value=float(world.safe_value[body.x, body.y]),
        **memory_signals,
    )


def _read_memory_directional(
    memory: object | None, body: AgentBody, world: World
) -> dict[str, float]:
    """Return the eight memory-direction fields as a dict.

    Returns all zeros when ``memory`` is ``None``. The non-None branch is a
    placeholder that lands properly with memory.py (SPEC §26.12 step 12).
    """
    keys = (
        "remembered_good_north",
        "remembered_good_south",
        "remembered_good_east",
        "remembered_good_west",
        "remembered_bad_north",
        "remembered_bad_south",
        "remembered_bad_east",
        "remembered_bad_west",
    )
    if memory is None:
        return dict.fromkeys(keys, 0.0)

    # memory.py is not implemented yet (SPEC §26.12 step 12). When it lands,
    # this branch reads remembered pleasure/pain along each axis.
    _ = body, world  # silence unused warnings until wired up
    return dict.fromkeys(keys, 0.0)
