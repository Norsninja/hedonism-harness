"""Tests for ``core/actions.py`` — action enum, validity, apply_action, delta commit."""

from __future__ import annotations

import dataclasses

import numpy as np
import pytest

from hedonism_harness.core.actions import (
    EMPTY_DELTA,
    MOVE_DIRECTIONS,
    Action,
    CellMutation,
    WorldDelta,
    apply_action,
    commit_delta,
    get_valid_actions,
)
from hedonism_harness.core.body import AgentBody, make_body
from hedonism_harness.core.config import ActionConfig, BodyConfig, WorldConfig
from hedonism_harness.core.events import (
    AgentMoved,
    AgentStayed,
    AteFood,
    HazardEntered,
    ReproductionRequested,
)
from hedonism_harness.core.traits import TraitConfig, random_traits
from hedonism_harness.core.world import CellKind, World, build_world

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def rng() -> np.random.Generator:
    return np.random.default_rng(0)


@pytest.fixture
def body_config() -> BodyConfig:
    return BodyConfig()


@pytest.fixture
def action_config() -> ActionConfig:
    return ActionConfig()


@pytest.fixture
def traits():
    return random_traits(TraitConfig(), np.random.default_rng(0))


def _empty_world(width: int = 5, height: int = 5) -> World:
    """Build a world with no food and no hazards for predictable tests."""
    return build_world(
        WorldConfig(seed=1, width=width, height=height, food_density=0.0, hazard_density=0.0)
    )


def _body_at(x: int, y: int, traits, body_config: BodyConfig) -> AgentBody:
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
# get_valid_actions
# ---------------------------------------------------------------------------


def test_stay_is_always_valid(traits, body_config) -> None:
    world = _empty_world()
    body = _body_at(2, 2, traits, body_config)
    assert Action.STAY in get_valid_actions(world, body)


def test_movement_filtered_at_corners(traits, body_config) -> None:
    world = _empty_world(width=4, height=4)
    nw_corner = _body_at(0, 3, traits, body_config)
    valid = get_valid_actions(world, nw_corner)
    assert Action.MOVE_NORTH not in valid  # off the top
    assert Action.MOVE_WEST not in valid  # off the left
    assert Action.MOVE_SOUTH in valid
    assert Action.MOVE_EAST in valid


def test_walls_block_movement(traits, body_config) -> None:
    world = _empty_world()
    world.kind_layer[3, 2] = CellKind.WALL  # east of (2, 2)
    body = _body_at(2, 2, traits, body_config)
    valid = get_valid_actions(world, body)
    assert Action.MOVE_EAST not in valid
    assert Action.MOVE_WEST in valid


def test_eat_only_valid_on_food_cell(traits, body_config) -> None:
    world = _empty_world()
    body = _body_at(2, 2, traits, body_config)
    assert Action.EAT not in get_valid_actions(world, body)

    world.kind_layer[2, 2] = CellKind.FOOD
    world.food_value[2, 2] = 10.0
    assert Action.EAT in get_valid_actions(world, body)


def test_reproduce_filtered_in_v01_step_6(traits, body_config) -> None:
    """REPRODUCE wiring lands in step 9 — get_valid_actions must filter it out for now."""
    world = _empty_world()
    body = _body_at(2, 2, traits, body_config)
    assert Action.REPRODUCE not in get_valid_actions(world, body)


def test_occupied_blocks_movement(traits, body_config) -> None:
    """Mesa wrapper passes ``occupied``; movement into an occupied cell must be filtered."""
    world = _empty_world()
    body = _body_at(2, 2, traits, body_config)
    occupied = frozenset({(2, 3), (3, 2)})  # block N and E
    valid = get_valid_actions(world, body, occupied=occupied)
    assert Action.MOVE_NORTH not in valid
    assert Action.MOVE_EAST not in valid
    assert Action.MOVE_SOUTH in valid
    assert Action.MOVE_WEST in valid
    assert Action.STAY in valid


def test_occupied_none_ignores_occupancy(traits, body_config) -> None:
    """Default ``occupied=None`` is the existing terrain-only behavior."""
    world = _empty_world()
    body = _body_at(2, 2, traits, body_config)
    valid = get_valid_actions(world, body, occupied=None)
    assert Action.MOVE_NORTH in valid
    assert Action.MOVE_SOUTH in valid
    assert Action.MOVE_EAST in valid
    assert Action.MOVE_WEST in valid


def test_occupied_empty_set_matches_none(traits, body_config) -> None:
    """An empty frozenset is equivalent to None for movement purposes."""
    world = _empty_world()
    body = _body_at(2, 2, traits, body_config)
    valid = get_valid_actions(world, body, occupied=frozenset())
    assert Action.MOVE_NORTH in valid
    assert Action.MOVE_SOUTH in valid
    assert Action.MOVE_EAST in valid
    assert Action.MOVE_WEST in valid


# ---------------------------------------------------------------------------
# apply_action — STAY
# ---------------------------------------------------------------------------


def test_stay_charges_stay_cost(traits, body_config, action_config, rng) -> None:
    world = _empty_world()
    body = _body_at(2, 2, traits, body_config)
    result = apply_action(world, body, Action.STAY, body_config, action_config, rng)
    assert result.body.x == 2
    assert result.body.y == 2
    assert result.body.energy == pytest.approx(body.energy - action_config.stay_cost)
    assert result.delta is EMPTY_DELTA
    assert isinstance(result.events[0], AgentStayed)


# ---------------------------------------------------------------------------
# apply_action — MOVE
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("action", list(MOVE_DIRECTIONS.keys()))
def test_movement_updates_position_and_charges_move_cost(
    action: Action, traits, body_config, action_config, rng
) -> None:
    world = _empty_world()
    body = _body_at(2, 2, traits, body_config)
    result = apply_action(world, body, action, body_config, action_config, rng)
    dx, dy = MOVE_DIRECTIONS[action]
    assert result.body.x == 2 + dx
    assert result.body.y == 2 + dy
    assert result.body.energy == pytest.approx(body.energy - action_config.move_cost)
    assert isinstance(result.events[0], AgentMoved)


def test_moving_into_hazard_emits_hazard_entered(traits, body_config, action_config, rng) -> None:
    world = _empty_world()
    world.kind_layer[3, 2] = CellKind.HAZARD
    world.hazard_damage[3, 2] = 5.0
    body = _body_at(2, 2, traits, body_config)
    result = apply_action(world, body, Action.MOVE_EAST, body_config, action_config, rng)
    event_types = {type(e) for e in result.events}
    assert AgentMoved in event_types
    assert HazardEntered in event_types


def test_apply_action_does_not_mutate_input_body(traits, body_config, action_config, rng) -> None:
    world = _empty_world()
    body = _body_at(2, 2, traits, body_config)
    before = dataclasses.replace(body)
    apply_action(world, body, Action.MOVE_NORTH, body_config, action_config, rng)
    assert body == before


# ---------------------------------------------------------------------------
# apply_action — EAT
# ---------------------------------------------------------------------------


def test_eat_increases_energy_and_clears_cell(traits, body_config, action_config, rng) -> None:
    world = _empty_world()
    world.kind_layer[2, 2] = CellKind.FOOD
    world.food_value[2, 2] = 25.0
    body = _body_at(2, 2, traits, body_config)
    result = apply_action(world, body, Action.EAT, body_config, action_config, rng)

    expected_energy = min(body_config.max_energy, body.energy + 25.0 - action_config.eat_cost)
    assert result.body.energy == pytest.approx(expected_energy)
    assert (2, 2) in result.delta.cells
    mutation = result.delta.cells[(2, 2)]
    assert mutation.kind == CellKind.EMPTY
    assert mutation.food_value == 0.0
    assert isinstance(result.events[0], AteFood)
    assert result.events[0].food_gained == 25.0


def test_apply_action_does_not_mutate_input_world_for_eat(
    traits, body_config, action_config, rng
) -> None:
    """Predict-one-step relies on this: scoring EAT must not consume the food."""
    world = _empty_world()
    world.kind_layer[2, 2] = CellKind.FOOD
    world.food_value[2, 2] = 25.0
    before_kind = world.kind_layer.copy()
    before_food = world.food_value.copy()
    body = _body_at(2, 2, traits, body_config)
    apply_action(world, body, Action.EAT, body_config, action_config, rng)
    np.testing.assert_array_equal(world.kind_layer, before_kind)
    np.testing.assert_array_equal(world.food_value, before_food)


# ---------------------------------------------------------------------------
# apply_action — REPRODUCE (stub for step 9)
# ---------------------------------------------------------------------------


def test_reproduce_emits_request_event(traits, body_config, action_config, rng) -> None:
    world = _empty_world()
    body = _body_at(2, 2, traits, body_config)
    result = apply_action(world, body, Action.REPRODUCE, body_config, action_config, rng)
    assert isinstance(result.events[0], ReproductionRequested)
    # Body is unchanged in the stub — energy cost lands with step 9.
    assert result.body == body


# ---------------------------------------------------------------------------
# apply_action — unknown action
# ---------------------------------------------------------------------------


def test_apply_action_rejects_unknown_action(traits, body_config, action_config, rng) -> None:
    world = _empty_world()
    body = _body_at(2, 2, traits, body_config)
    with pytest.raises(ValueError, match="Unknown action"):
        apply_action(world, body, 999, body_config, action_config, rng)  # type: ignore[arg-type]


# ---------------------------------------------------------------------------
# commit_delta
# ---------------------------------------------------------------------------


def test_commit_delta_mutates_world_layers() -> None:
    world = _empty_world()
    world.kind_layer[2, 2] = CellKind.FOOD
    world.food_value[2, 2] = 25.0
    delta = WorldDelta(cells={(2, 2): CellMutation(kind=CellKind.EMPTY, food_value=0.0)})
    commit_delta(world, delta)
    assert world.kind_layer[2, 2] == CellKind.EMPTY
    assert world.food_value[2, 2] == 0.0


def test_commit_delta_only_touches_specified_attributes() -> None:
    world = _empty_world()
    world.kind_layer[2, 2] = CellKind.FOOD
    world.food_value[2, 2] = 25.0
    world.hazard_damage[2, 2] = 7.0  # nonsensical combo, but tests selectivity
    delta = WorldDelta(cells={(2, 2): CellMutation(kind=CellKind.EMPTY)})
    commit_delta(world, delta)
    assert world.kind_layer[2, 2] == CellKind.EMPTY
    assert world.food_value[2, 2] == 25.0  # untouched
    assert world.hazard_damage[2, 2] == 7.0  # untouched


def test_commit_empty_delta_is_noop() -> None:
    world = _empty_world()
    before_kind = world.kind_layer.copy()
    commit_delta(world, EMPTY_DELTA)
    np.testing.assert_array_equal(world.kind_layer, before_kind)


# ---------------------------------------------------------------------------
# Predict-one-step contract (SPEC §27.5)
# ---------------------------------------------------------------------------


def test_predict_one_step_can_score_all_valid_actions_without_drift(
    traits, body_config, action_config, rng
) -> None:
    """Scoring all valid actions against a body copy must leave world+body intact."""
    world = _empty_world()
    world.kind_layer[2, 2] = CellKind.FOOD
    world.food_value[2, 2] = 25.0
    world.kind_layer[3, 2] = CellKind.HAZARD
    world.hazard_damage[3, 2] = 5.0

    body = _body_at(2, 2, traits, body_config)
    before_body = dataclasses.replace(body)
    before_kind = world.kind_layer.copy()
    before_food = world.food_value.copy()

    for action in get_valid_actions(world, body):
        # In real predict, the policy passes a body copy; here we pass the
        # original since apply_action is pure either way.
        apply_action(world, body, action, body_config, action_config, rng)

    assert body == before_body
    np.testing.assert_array_equal(world.kind_layer, before_kind)
    np.testing.assert_array_equal(world.food_value, before_food)
