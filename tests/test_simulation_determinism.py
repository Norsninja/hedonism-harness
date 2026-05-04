"""Determinism north star: same seed -> same world -> same first N events -> same metrics.

Per docs/SPEC.md §26.12, this is the first proof point for v0.1.
"""

from __future__ import annotations

import numpy as np
import pytest
from hypothesis import given
from hypothesis import strategies as st

from hedonism_harness.core.config import WorldConfig
from hedonism_harness.core.world import build_world


@pytest.mark.determinism
def test_same_seed_produces_identical_kind_layer() -> None:
    """Two worlds built with the same seed and config must have identical terrain."""
    config = WorldConfig(seed=12345, width=16, height=16)
    world_a = build_world(config)
    world_b = build_world(config)

    np.testing.assert_array_equal(world_a.kind_layer, world_b.kind_layer)


@pytest.mark.determinism
def test_different_seeds_produce_different_kind_layers() -> None:
    """Sanity: changing the seed must change generated terrain."""
    world_a = build_world(WorldConfig(seed=1, width=16, height=16))
    world_b = build_world(WorldConfig(seed=2, width=16, height=16))

    assert not np.array_equal(world_a.kind_layer, world_b.kind_layer)


@pytest.mark.determinism
@given(seed=st.integers(min_value=0, max_value=2**32 - 1))
def test_world_generation_is_deterministic_under_any_seed(seed: int) -> None:
    """Property: for any seed, repeated generation yields byte-identical layers."""
    config = WorldConfig(seed=seed, width=8, height=8)
    world_a = build_world(config)
    world_b = build_world(config)

    np.testing.assert_array_equal(world_a.kind_layer, world_b.kind_layer)
    np.testing.assert_array_equal(world_a.food_value, world_b.food_value)
    np.testing.assert_array_equal(world_a.hazard_damage, world_b.hazard_damage)
    np.testing.assert_array_equal(world_a.safe_value, world_b.safe_value)
