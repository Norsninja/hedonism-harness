"""Tests for policies/ — Random, Reflex, Hedonism (no memory yet)."""

from __future__ import annotations

import dataclasses

import numpy as np
import pytest

from hedonism_harness.core.actions import Action, get_valid_actions
from hedonism_harness.core.body import make_body
from hedonism_harness.core.config import ActionConfig, BodyConfig, WorldConfig
from hedonism_harness.core.sensors import observe
from hedonism_harness.core.traits import TraitConfig, random_traits
from hedonism_harness.core.world import CellKind, World, build_world
from hedonism_harness.policies import (
    DecisionContext,
    HedonismPolicy,
    RandomPolicy,
    ReflexPolicy,
)

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def body_config() -> BodyConfig:
    return BodyConfig()


@pytest.fixture
def action_config() -> ActionConfig:
    return ActionConfig()


@pytest.fixture
def traits():
    return random_traits(TraitConfig(), np.random.default_rng(0))


def _empty_world(width: int = 11, height: int = 11) -> World:
    return build_world(
        WorldConfig(seed=1, width=width, height=height, food_density=0.0, hazard_density=0.0)
    )


def _ctx(
    world: World,
    body,
    body_config: BodyConfig,
    action_config: ActionConfig,
    seed: int = 0,
) -> DecisionContext:
    return DecisionContext(
        world=world,
        body=body,
        observation=observe(world, body, body_config),
        rng=np.random.default_rng(seed),
        body_config=body_config,
        action_config=action_config,
        memory=None,
    )


def _body(x, y, traits, body_config, **overrides):
    body = make_body(
        body_id=1,
        lineage_id=1,
        parent_id=None,
        x=x,
        y=y,
        traits=traits,
        config=body_config,
    )
    if overrides:
        body = dataclasses.replace(body, **overrides)
    return body


# ---------------------------------------------------------------------------
# RandomPolicy
# ---------------------------------------------------------------------------


def test_random_policy_picks_only_valid_actions(traits, body_config, action_config) -> None:
    world = _empty_world()
    body = _body(2, 2, traits, body_config)
    valid = set(get_valid_actions(world, body))
    policy = RandomPolicy()
    for seed in range(20):
        ctx = _ctx(world, body, body_config, action_config, seed=seed)
        decision = policy.decide(ctx)
        assert decision.action in valid
        assert decision.breakdown is None


def test_random_policy_is_deterministic_under_seed(traits, body_config, action_config) -> None:
    world = _empty_world()
    body = _body(2, 2, traits, body_config)
    policy = RandomPolicy()
    a = policy.decide(_ctx(world, body, body_config, action_config, seed=42))
    b = policy.decide(_ctx(world, body, body_config, action_config, seed=42))
    assert a.action == b.action


# ---------------------------------------------------------------------------
# ReflexPolicy
# ---------------------------------------------------------------------------


def test_reflex_eats_when_on_food_and_hungry(traits, body_config, action_config) -> None:
    world = _empty_world()
    world.kind_layer[5, 5] = CellKind.FOOD
    world.food_value[5, 5] = 20.0
    body = _body(5, 5, traits, body_config, energy=10.0)  # very hungry
    decision = ReflexPolicy().decide(_ctx(world, body, body_config, action_config))
    assert decision.action == Action.EAT


def test_reflex_does_not_eat_when_full(traits, body_config, action_config) -> None:
    world = _empty_world()
    world.kind_layer[5, 5] = CellKind.FOOD
    world.food_value[5, 5] = 20.0
    full_energy = body_config.max_energy
    body = _body(5, 5, traits, body_config, energy=full_energy)
    decision = ReflexPolicy().decide(_ctx(world, body, body_config, action_config))
    assert decision.action != Action.EAT


def test_reflex_flees_from_hazard(traits, body_config, action_config) -> None:
    world = _empty_world()
    # Hazard to the north -> reflex should move SOUTH.
    world.kind_layer[5, 7] = CellKind.HAZARD
    world.hazard_damage[5, 7] = 10.0
    body = _body(5, 5, traits, body_config)
    decision = ReflexPolicy().decide(_ctx(world, body, body_config, action_config))
    assert decision.action == Action.MOVE_SOUTH


def test_reflex_seeks_food_signal(traits, body_config, action_config) -> None:
    world = _empty_world()
    world.kind_layer[7, 5] = CellKind.FOOD  # food to the east
    world.food_value[7, 5] = 10.0
    body = _body(5, 5, traits, body_config)
    decision = ReflexPolicy().decide(_ctx(world, body, body_config, action_config))
    assert decision.action == Action.MOVE_EAST


def test_reflex_falls_back_to_valid_random_when_no_signals(
    traits, body_config, action_config
) -> None:
    world = _empty_world()
    body = _body(5, 5, traits, body_config)
    valid = set(get_valid_actions(world, body))
    decision = ReflexPolicy().decide(_ctx(world, body, body_config, action_config))
    assert decision.action in valid


# ---------------------------------------------------------------------------
# HedonismPolicy
# ---------------------------------------------------------------------------


def test_hedonism_picks_eat_when_on_food_and_hungry(traits, body_config, action_config) -> None:
    world = _empty_world()
    world.kind_layer[5, 5] = CellKind.FOOD
    world.food_value[5, 5] = 30.0
    # Make agent very hungry; eating should dominate scoring.
    body = _body(5, 5, traits, body_config, energy=5.0)
    policy = HedonismPolicy(exploration_noise=0.0)
    decision = policy.decide(_ctx(world, body, body_config, action_config))
    assert decision.action == Action.EAT
    assert decision.breakdown is not None
    assert decision.breakdown.details["eating_pleasure"] > 0


def test_hedonism_avoids_stepping_into_hazard(body_config, action_config) -> None:
    """A fearful, intact agent with hazards adjacent should not walk into them."""
    config = TraitConfig()
    base = random_traits(config, np.random.default_rng(0))
    fearful = dataclasses.replace(
        base,
        fear_sensitivity=3.0,
        risk_tolerance=0.0,
        injury_pain_sensitivity=2.5,
        pain_tolerance=0.0,
    )
    world = _empty_world()
    # Hazard immediately east. Other directions are clear.
    world.kind_layer[6, 5] = CellKind.HAZARD
    world.hazard_damage[6, 5] = 30.0
    body = _body(5, 5, fearful, body_config)
    policy = HedonismPolicy(exploration_noise=0.0)
    decision = policy.decide(_ctx(world, body, body_config, action_config))
    assert decision.action != Action.MOVE_EAST


def test_hedonism_returns_breakdown_for_scored_choices(traits, body_config, action_config) -> None:
    world = _empty_world()
    body = _body(5, 5, traits, body_config)
    policy = HedonismPolicy(exploration_noise=0.0)
    decision = policy.decide(_ctx(world, body, body_config, action_config))
    assert decision.breakdown is not None


def test_hedonism_exploration_noise_returns_no_breakdown(
    traits, body_config, action_config
) -> None:
    world = _empty_world()
    body = _body(5, 5, traits, body_config)
    # noise=1.0 forces the random branch on every call.
    policy = HedonismPolicy(exploration_noise=1.0)
    decision = policy.decide(_ctx(world, body, body_config, action_config))
    assert decision.breakdown is None
    assert decision.action in set(get_valid_actions(world, body))


def test_hedonism_rejects_out_of_range_exploration_noise() -> None:
    with pytest.raises(ValueError, match="exploration_noise"):
        HedonismPolicy(exploration_noise=-0.1)
    with pytest.raises(ValueError, match="exploration_noise"):
        HedonismPolicy(exploration_noise=1.1)


def test_hedonism_is_deterministic_under_seed(traits, body_config, action_config) -> None:
    world = _empty_world()
    world.kind_layer[5, 5] = CellKind.FOOD
    world.food_value[5, 5] = 20.0
    body = _body(5, 5, traits, body_config)
    policy = HedonismPolicy(exploration_noise=0.5)  # exercise the noise branch too
    a = policy.decide(_ctx(world, body, body_config, action_config, seed=99))
    b = policy.decide(_ctx(world, body, body_config, action_config, seed=99))
    assert a.action == b.action


def test_hedonism_does_not_mutate_world_or_body(traits, body_config, action_config) -> None:
    """Predict-one-step purity: scoring must not commit any deltas."""
    world = _empty_world()
    world.kind_layer[5, 5] = CellKind.FOOD
    world.food_value[5, 5] = 25.0
    before_kind = world.kind_layer.copy()
    before_food = world.food_value.copy()
    body = _body(5, 5, traits, body_config)
    before_body = dataclasses.replace(body)
    HedonismPolicy(exploration_noise=0.0).decide(_ctx(world, body, body_config, action_config))
    np.testing.assert_array_equal(world.kind_layer, before_kind)
    np.testing.assert_array_equal(world.food_value, before_food)
    assert body == before_body
