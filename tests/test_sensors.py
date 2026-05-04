"""Tests for ``core/sensors.py`` — internal, external, and memory sensors."""

from __future__ import annotations

import dataclasses

import numpy as np
import pytest

from hedonism_harness.core.body import make_body
from hedonism_harness.core.config import BodyConfig, WorldConfig
from hedonism_harness.core.sensors import Observation, observe
from hedonism_harness.core.traits import TraitConfig, random_traits
from hedonism_harness.core.world import CellKind, World, build_world


@pytest.fixture
def body_config() -> BodyConfig:
    return BodyConfig()


def _empty_world(width: int = 11, height: int = 11) -> World:
    return build_world(
        WorldConfig(seed=1, width=width, height=height, food_density=0.0, hazard_density=0.0)
    )


def _body_with_radius(x: int, y: int, radius: int, body_config: BodyConfig):
    base = random_traits(TraitConfig(), np.random.default_rng(0))
    traits = dataclasses.replace(base, sensor_radius=radius)
    return make_body(
        body_id=1,
        lineage_id=1,
        parent_id=None,
        x=x,
        y=y,
        traits=traits,
        config=body_config,
    )


# ---------------------------------------------------------------------------
# Internal sensors
# ---------------------------------------------------------------------------


def test_internal_sensors_at_full_health(body_config) -> None:
    world = _empty_world()
    body = _body_with_radius(5, 5, 3, body_config)
    obs = observe(world, body, body_config)
    assert obs.energy_ratio == pytest.approx(body_config.starting_energy / body_config.max_energy)
    assert obs.health_ratio == pytest.approx(1.0)
    assert obs.hunger_level == pytest.approx(1.0 - obs.energy_ratio)
    assert obs.injury_level == pytest.approx(0.0)
    assert obs.age == 0


def test_internal_sensors_when_starving(body_config) -> None:
    world = _empty_world()
    body = dataclasses.replace(_body_with_radius(5, 5, 3, body_config), energy=10.0, health=20.0)
    obs = observe(world, body, body_config)
    assert obs.energy_ratio == pytest.approx(10.0 / body_config.max_energy)
    assert obs.health_ratio == pytest.approx(20.0 / body_config.max_health)
    assert obs.hunger_level == pytest.approx(1.0 - obs.energy_ratio)
    assert obs.injury_level == pytest.approx(1.0 - obs.health_ratio)


# ---------------------------------------------------------------------------
# External sensors — food
# ---------------------------------------------------------------------------


def test_food_directly_north_contributes_to_north_signal(body_config) -> None:
    world = _empty_world()
    world.kind_layer[5, 7] = CellKind.FOOD  # 2 cells north of (5, 5)
    world.food_value[5, 7] = 10.0
    body = _body_with_radius(5, 5, 3, body_config)
    obs = observe(world, body, body_config)
    assert obs.food_signal_north == pytest.approx(10.0 / 2)
    assert obs.food_signal_south == 0.0
    assert obs.food_signal_east == 0.0
    assert obs.food_signal_west == 0.0


def test_food_signal_decays_with_distance(body_config) -> None:
    """Two FOOD cells at distance 1 and 3 along the same axis: 1/1 + value/3."""
    world = _empty_world()
    world.kind_layer[5, 6] = CellKind.FOOD  # distance 1 north
    world.food_value[5, 6] = 6.0
    world.kind_layer[5, 8] = CellKind.FOOD  # distance 3 north
    world.food_value[5, 8] = 9.0
    body = _body_with_radius(5, 5, 5, body_config)
    obs = observe(world, body, body_config)
    assert obs.food_signal_north == pytest.approx(6.0 / 1 + 9.0 / 3)


def test_food_beyond_sensor_radius_is_invisible(body_config) -> None:
    world = _empty_world()
    world.kind_layer[5, 9] = CellKind.FOOD  # distance 4
    world.food_value[5, 9] = 100.0
    body = _body_with_radius(5, 5, 2, body_config)  # radius 2 — too short
    obs = observe(world, body, body_config)
    assert obs.food_signal_north == 0.0


def test_axis_scan_stops_at_world_edge(body_config) -> None:
    """A body near the edge with radius extending past it should not raise."""
    world = _empty_world(width=4, height=4)
    body = _body_with_radius(3, 3, 5, body_config)  # NE corner, radius bigger than world
    obs = observe(world, body, body_config)
    assert obs.food_signal_north == 0.0
    assert obs.food_signal_east == 0.0


# ---------------------------------------------------------------------------
# External sensors — hazard
# ---------------------------------------------------------------------------


def test_hazard_signals_match_food_geometry(body_config) -> None:
    """The hazard scan uses the same geometry as the food scan."""
    world = _empty_world()
    world.kind_layer[3, 5] = CellKind.HAZARD  # 2 west
    world.hazard_damage[3, 5] = 8.0
    body = _body_with_radius(5, 5, 3, body_config)
    obs = observe(world, body, body_config)
    assert obs.hazard_signal_west == pytest.approx(8.0 / 2)
    assert obs.hazard_signal_north == 0.0
    assert obs.hazard_signal_south == 0.0
    assert obs.hazard_signal_east == 0.0


# ---------------------------------------------------------------------------
# Cell-local readouts
# ---------------------------------------------------------------------------


def test_on_food_flag_when_standing_on_food(body_config) -> None:
    world = _empty_world()
    world.kind_layer[5, 5] = CellKind.FOOD
    world.food_value[5, 5] = 12.0
    body = _body_with_radius(5, 5, 1, body_config)
    obs = observe(world, body, body_config)
    assert obs.on_food is True
    assert obs.on_hazard is False
    assert obs.current_food_value == pytest.approx(12.0)


def test_on_hazard_flag_and_value(body_config) -> None:
    world = _empty_world()
    world.kind_layer[5, 5] = CellKind.HAZARD
    world.hazard_damage[5, 5] = 7.0
    body = _body_with_radius(5, 5, 1, body_config)
    obs = observe(world, body, body_config)
    assert obs.on_hazard is True
    assert obs.current_hazard_damage == pytest.approx(7.0)


def test_on_safe_flag(body_config) -> None:
    world = _empty_world()
    world.kind_layer[5, 5] = CellKind.SAFE
    world.safe_value[5, 5] = 1.0
    body = _body_with_radius(5, 5, 1, body_config)
    obs = observe(world, body, body_config)
    assert obs.on_safe is True


# ---------------------------------------------------------------------------
# Memory sensors (placeholder until step 12)
# ---------------------------------------------------------------------------


def test_memory_signals_zero_when_memory_is_none(body_config) -> None:
    world = _empty_world()
    body = _body_with_radius(5, 5, 3, body_config)
    obs = observe(world, body, body_config, memory=None)
    assert obs.remembered_good_north == 0.0
    assert obs.remembered_good_south == 0.0
    assert obs.remembered_good_east == 0.0
    assert obs.remembered_good_west == 0.0
    assert obs.remembered_bad_north == 0.0
    assert obs.remembered_bad_south == 0.0
    assert obs.remembered_bad_east == 0.0
    assert obs.remembered_bad_west == 0.0


# ---------------------------------------------------------------------------
# Purity contract
# ---------------------------------------------------------------------------


def test_observe_does_not_mutate_world_or_body(body_config) -> None:
    world = _empty_world()
    world.kind_layer[5, 7] = CellKind.FOOD
    world.food_value[5, 7] = 10.0
    body = _body_with_radius(5, 5, 3, body_config)
    before_kind = world.kind_layer.copy()
    before_food = world.food_value.copy()
    before_body = dataclasses.replace(body)
    observe(world, body, body_config)
    np.testing.assert_array_equal(world.kind_layer, before_kind)
    np.testing.assert_array_equal(world.food_value, before_food)
    assert body == before_body


def test_observation_is_frozen(body_config) -> None:
    world = _empty_world()
    body = _body_with_radius(5, 5, 1, body_config)
    obs = observe(world, body, body_config)
    with pytest.raises(dataclasses.FrozenInstanceError):
        obs.energy_ratio = 0.0  # type: ignore[misc]


def test_observe_is_idempotent(body_config) -> None:
    world = _empty_world()
    world.kind_layer[5, 7] = CellKind.FOOD
    world.food_value[5, 7] = 10.0
    body = _body_with_radius(5, 5, 3, body_config)
    a = observe(world, body, body_config)
    b = observe(world, body, body_config)
    assert a == b


def test_observation_carries_all_thirteen_internal_external_fields(body_config) -> None:
    """Sanity: Observation has every field SPEC §10 lists."""
    world = _empty_world()
    body = _body_with_radius(5, 5, 1, body_config)
    obs = observe(world, body, body_config)
    field_names = {f.name for f in dataclasses.fields(Observation)}
    expected = {
        "energy_ratio",
        "health_ratio",
        "hunger_level",
        "injury_level",
        "age",
        "food_signal_north",
        "food_signal_south",
        "food_signal_east",
        "food_signal_west",
        "hazard_signal_north",
        "hazard_signal_south",
        "hazard_signal_east",
        "hazard_signal_west",
    }
    assert expected.issubset(field_names)
    _ = obs  # ensure observe() ran
