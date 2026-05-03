"""Tests for ``core/world.py`` — terrain generation, bounds, cell views."""

from __future__ import annotations

import numpy as np
import pytest
from hypothesis import given
from hypothesis import strategies as st

from hedonism_harness.core.config import WorldConfig
from hedonism_harness.core.world import (
    Cell,
    CellKind,
    build_world,
    cell_at,
    in_bounds,
)


def test_world_layers_have_expected_shape_and_dtype() -> None:
    config = WorldConfig(seed=1, width=24, height=12)
    world = build_world(config)

    assert world.kind_layer.shape == (24, 12)
    assert world.kind_layer.dtype == np.uint8
    assert world.food_value.dtype == np.float32
    assert world.hazard_damage.dtype == np.float32
    assert world.safe_value.dtype == np.float32


def test_zero_density_world_has_no_food_or_hazards() -> None:
    config = WorldConfig(seed=1, width=16, height=16, food_density=0.0, hazard_density=0.0)
    world = build_world(config)

    assert int((world.kind_layer == CellKind.FOOD).sum()) == 0
    assert int((world.kind_layer == CellKind.HAZARD).sum()) == 0
    assert float(world.food_value.sum()) == 0.0
    assert float(world.hazard_damage.sum()) == 0.0


def test_food_value_is_set_only_on_food_cells() -> None:
    config = WorldConfig(seed=42, width=32, height=32, food_density=0.2, hazard_density=0.0)
    world = build_world(config)
    food_mask = world.kind_layer == CellKind.FOOD

    assert np.all(world.food_value[food_mask] == config.food_value_default)
    assert np.all(world.food_value[~food_mask] == 0.0)


def test_hazard_damage_is_set_only_on_hazard_cells() -> None:
    config = WorldConfig(seed=42, width=32, height=32, food_density=0.0, hazard_density=0.2)
    world = build_world(config)
    hazard_mask = world.kind_layer == CellKind.HAZARD

    assert np.all(world.hazard_damage[hazard_mask] == config.hazard_damage_default)
    assert np.all(world.hazard_damage[~hazard_mask] == 0.0)


def test_in_bounds_checks_corners_and_outside() -> None:
    world = build_world(WorldConfig(seed=1, width=10, height=8))

    assert in_bounds(world, 0, 0)
    assert in_bounds(world, 9, 7)
    assert not in_bounds(world, -1, 0)
    assert not in_bounds(world, 0, -1)
    assert not in_bounds(world, 10, 0)
    assert not in_bounds(world, 0, 8)


def test_cell_at_returns_view_consistent_with_layers() -> None:
    world = build_world(WorldConfig(seed=7, width=20, height=20, food_density=0.3))
    for x in range(world.width):
        for y in range(world.height):
            cell = cell_at(world, x, y)
            assert isinstance(cell, Cell)
            assert cell.kind == CellKind(int(world.kind_layer[x, y]))
            assert cell.food_value == float(world.food_value[x, y])
            assert cell.hazard_damage == float(world.hazard_damage[x, y])


def test_cell_at_raises_on_out_of_bounds() -> None:
    world = build_world(WorldConfig(seed=1, width=4, height=4))
    with pytest.raises(IndexError):
        cell_at(world, 4, 0)


@given(
    seed=st.integers(min_value=0, max_value=2**32 - 1),
    food_density=st.floats(min_value=0.0, max_value=1.0, allow_nan=False),
    hazard_density=st.floats(min_value=0.0, max_value=1.0, allow_nan=False),
)
def test_food_and_hazard_masks_never_overlap(
    seed: int, food_density: float, hazard_density: float
) -> None:
    """Property: the threshold partition assigns each cell to at most one kind."""
    # Densities must sum to <= 1.0 for the partition to be valid.
    if food_density + hazard_density > 1.0:
        return
    config = WorldConfig(
        seed=seed,
        width=8,
        height=8,
        food_density=food_density,
        hazard_density=hazard_density,
    )
    world = build_world(config)
    food = world.kind_layer == CellKind.FOOD
    hazard = world.kind_layer == CellKind.HAZARD
    assert int((food & hazard).sum()) == 0
