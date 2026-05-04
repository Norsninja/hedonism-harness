"""World state: NumPy-backed terrain layers + read-only Cell view helper.

Per SPEC §27.1, terrain is stored as parallel NumPy arrays (one per attribute)
that map directly onto Mesa 3.x ``PropertyLayer`` instances at the model layer.
Per SPEC §27.11, this module imports stdlib + numpy + pydantic only — no Mesa,
no IO. The Mesa wrapping happens in ``hedonism_harness/model.py``.

``World`` is intentionally mutable: ``apply_action`` mutates layers in place
(food consumption, hazard application). One-step prediction uses a cheap
``WorldDelta`` overlay rather than copying the layers — see ``actions.py``
when it lands.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import IntEnum

import numpy as np

from hedonism_harness.core.config import WorldConfig
from hedonism_harness.core.rng import make_streams


class CellKind(IntEnum):
    """Primary terrain kind for a cell.

    Stored as ``uint8`` in ``World.kind_layer``.
    """

    EMPTY = 0
    FOOD = 1
    HAZARD = 2
    WALL = 3
    SAFE = 4


@dataclass
class World:
    """NumPy-backed world state.

    Layer shapes are ``(width, height)`` and indexed as ``layer[x, y]``.
    """

    kind_layer: np.ndarray  # uint8, values from CellKind
    food_value: np.ndarray  # float32
    hazard_damage: np.ndarray  # float32
    safe_value: np.ndarray  # float32
    width: int
    height: int


@dataclass(frozen=True)
class Cell:
    """Read-only view of a single cell. Returned by ``cell_at``."""

    x: int
    y: int
    kind: CellKind
    food_value: float
    hazard_damage: float
    safe_value: float


def build_world(config: WorldConfig) -> World:
    """Generate a deterministic world from a ``WorldConfig``.

    Uses the ``world_gen`` RNG stream. Calling this twice with the same config
    yields byte-identical layer arrays (the v0.1 determinism north star).
    """
    rng = make_streams(config.seed).world_gen
    shape = (config.width, config.height)

    kind_layer = np.full(shape, CellKind.EMPTY, dtype=np.uint8)
    food_value = np.zeros(shape, dtype=np.float32)
    hazard_damage = np.zeros(shape, dtype=np.float32)
    safe_value = np.zeros(shape, dtype=np.float32)

    # Single uniform draw, then partition into FOOD / HAZARD / EMPTY by threshold.
    # This keeps the consumed RNG sequence stable when densities change at the margin.
    roll = rng.random(shape)
    food_mask = roll < config.food_density
    hazard_mask = (roll >= config.food_density) & (
        roll < config.food_density + config.hazard_density
    )

    kind_layer[food_mask] = CellKind.FOOD
    kind_layer[hazard_mask] = CellKind.HAZARD
    food_value[food_mask] = config.food_value_default
    hazard_damage[hazard_mask] = config.hazard_damage_default

    return World(
        kind_layer=kind_layer,
        food_value=food_value,
        hazard_damage=hazard_damage,
        safe_value=safe_value,
        width=config.width,
        height=config.height,
    )


def in_bounds(world: World, x: int, y: int) -> bool:
    """True iff ``(x, y)`` is a valid cell coordinate."""
    return 0 <= x < world.width and 0 <= y < world.height


def cell_at(world: World, x: int, y: int) -> Cell:
    """Return a read-only ``Cell`` view at ``(x, y)``. Raises ``IndexError`` out of bounds."""
    if not in_bounds(world, x, y):
        msg = f"cell ({x}, {y}) out of bounds for world {world.width}x{world.height}"
        raise IndexError(msg)
    return Cell(
        x=x,
        y=y,
        kind=CellKind(int(world.kind_layer[x, y])),
        food_value=float(world.food_value[x, y]),
        hazard_damage=float(world.hazard_damage[x, y]),
        safe_value=float(world.safe_value[x, y]),
    )
