"""Tests for ``core/valence.py`` — Hedonism Harness invariants.

Covers SPEC §18.4 plus property tests for NaN-freedom and total = sum of
components.
"""

from __future__ import annotations

import dataclasses
import math

import numpy as np
import pytest
from hypothesis import given
from hypothesis import strategies as st

from hedonism_harness.core.actions import Action, action_energy_cost
from hedonism_harness.core.body import make_body
from hedonism_harness.core.config import ActionConfig, BodyConfig, WorldConfig
from hedonism_harness.core.sensors import Observation, observe
from hedonism_harness.core.traits import TraitConfig, Traits, random_traits
from hedonism_harness.core.valence import ValenceBreakdown, evaluate
from hedonism_harness.core.world import CellKind, World, build_world

# ---------------------------------------------------------------------------
# Fixtures and helpers
# ---------------------------------------------------------------------------


@pytest.fixture
def body_config() -> BodyConfig:
    return BodyConfig()


@pytest.fixture
def action_config() -> ActionConfig:
    return ActionConfig()


@pytest.fixture
def traits() -> Traits:
    return random_traits(TraitConfig(), np.random.default_rng(0))


def _empty_world(width: int = 11, height: int = 11) -> World:
    return build_world(
        WorldConfig(seed=1, width=width, height=height, food_density=0.0, hazard_density=0.0)
    )


def _body(x: int, y: int, traits: Traits, body_config: BodyConfig, **overrides):
    body = make_body(
        body_id=1, lineage_id=1, parent_id=None, x=x, y=y, traits=traits, config=body_config
    )
    if overrides:
        body = dataclasses.replace(body, **overrides)
    return body


def _zero_obs(**overrides) -> Observation:
    base: dict[str, float | int | bool] = {
        "energy_ratio": 1.0,
        "health_ratio": 1.0,
        "hunger_level": 0.0,
        "injury_level": 0.0,
        "age": 0,
        "food_signal_north": 0.0,
        "food_signal_south": 0.0,
        "food_signal_east": 0.0,
        "food_signal_west": 0.0,
        "hazard_signal_north": 0.0,
        "hazard_signal_south": 0.0,
        "hazard_signal_east": 0.0,
        "hazard_signal_west": 0.0,
        "on_food": False,
        "on_hazard": False,
        "on_safe": False,
        "current_food_value": 0.0,
        "current_hazard_damage": 0.0,
        "current_safe_value": 0.0,
    }
    base.update(overrides)
    return Observation(**base)  # type: ignore[arg-type]


# ---------------------------------------------------------------------------
# SPEC §18.4: required invariants
# ---------------------------------------------------------------------------


def test_total_equals_pleasure_minus_pain_minus_fear_minus_uncertainty_minus_effort(
    traits, body_config
) -> None:
    body_b = _body(5, 5, traits, body_config, energy=30.0, health=80.0)
    body_a = _body(5, 5, traits, body_config, energy=29.9, health=80.0)
    obs = _zero_obs(hunger_level=0.7, injury_level=0.2)
    bd = evaluate(obs, obs, body_b, body_a, Action.STAY, 0.1, traits)
    assert bd.total == pytest.approx(bd.pleasure - bd.pain - bd.fear - bd.uncertainty - bd.effort)


def test_no_component_is_nan_or_inf_under_default_traits(traits, body_config) -> None:
    body_b = _body(5, 5, traits, body_config, energy=50.0, health=50.0)
    body_a = _body(5, 5, traits, body_config, energy=49.0, health=50.0)
    obs = _zero_obs(hunger_level=0.5, injury_level=0.5)
    bd = evaluate(obs, obs, body_b, body_a, Action.STAY, 1.0, traits)
    for value in (bd.total, bd.pleasure, bd.pain, bd.fear, bd.uncertainty, bd.effort):
        assert math.isfinite(value)


def test_hunger_pain_increases_as_hunger_increases(traits, body_config) -> None:
    body_b = _body(5, 5, traits, body_config)
    body_a = _body(5, 5, traits, body_config)
    obs_low = _zero_obs(hunger_level=0.1)
    obs_high = _zero_obs(hunger_level=0.9)
    low = evaluate(obs_low, obs_low, body_b, body_a, Action.STAY, 0.0, traits)
    high = evaluate(obs_high, obs_high, body_b, body_a, Action.STAY, 0.0, traits)
    assert high.details["hunger_pain"] > low.details["hunger_pain"]


def test_eating_pleasure_higher_when_hungry_than_full(traits, body_config) -> None:
    body_b = _body(5, 5, traits, body_config)
    body_a = _body(5, 5, traits, body_config, energy=body_config.starting_energy + 10.0)
    obs_full = _zero_obs(hunger_level=0.0, current_food_value=10.0, on_food=True)
    obs_hungry = _zero_obs(hunger_level=0.9, current_food_value=10.0, on_food=True)
    obs_after = _zero_obs()  # post-eat: cell empty
    full = evaluate(obs_full, obs_after, body_b, body_a, Action.EAT, 0.0, traits)
    hungry = evaluate(obs_hungry, obs_after, body_b, body_a, Action.EAT, 0.0, traits)
    assert hungry.details["eating_pleasure"] > full.details["eating_pleasure"]


def test_eating_pleasure_zero_when_action_is_not_eat(traits, body_config) -> None:
    body = _body(5, 5, traits, body_config)
    obs = _zero_obs(hunger_level=0.9, current_food_value=10.0, on_food=True)
    bd = evaluate(obs, obs, body, body, Action.STAY, 0.1, traits)
    assert bd.details["eating_pleasure"] == 0.0


def test_fear_increases_with_predicted_hazard_risk(traits, body_config) -> None:
    body = _body(5, 5, traits, body_config)
    obs_zero = _zero_obs()
    obs_low_haz = _zero_obs(hazard_signal_north=0.5)
    obs_high_haz = _zero_obs(hazard_signal_north=5.0)
    low = evaluate(obs_zero, obs_low_haz, body, body, Action.STAY, 0.0, traits)
    high = evaluate(obs_zero, obs_high_haz, body, body, Action.STAY, 0.0, traits)
    assert high.fear > low.fear


def test_pain_tolerance_reduces_felt_pain(body_config) -> None:
    config = TraitConfig()
    base = random_traits(config, np.random.default_rng(0))
    sensitive = dataclasses.replace(base, pain_tolerance=0.0, hunger_pain_sensitivity=1.0)
    tolerant = dataclasses.replace(base, pain_tolerance=0.9, hunger_pain_sensitivity=1.0)
    body_s = _body(5, 5, sensitive, body_config)
    body_t = _body(5, 5, tolerant, body_config)
    obs = _zero_obs(hunger_level=0.8)
    s = evaluate(obs, obs, body_s, body_s, Action.STAY, 0.0, sensitive)
    t = evaluate(obs, obs, body_t, body_t, Action.STAY, 0.0, tolerant)
    assert t.details["hunger_pain"] < s.details["hunger_pain"]


def test_risk_tolerance_reduces_fear(body_config) -> None:
    config = TraitConfig()
    base = random_traits(config, np.random.default_rng(0))
    cautious = dataclasses.replace(base, risk_tolerance=0.0, fear_sensitivity=1.0)
    bold = dataclasses.replace(base, risk_tolerance=0.9, fear_sensitivity=1.0)
    body_c = _body(5, 5, cautious, body_config)
    body_b = _body(5, 5, bold, body_config)
    obs = _zero_obs(hazard_signal_north=2.0)
    c = evaluate(obs, obs, body_c, body_c, Action.STAY, 0.0, cautious)
    b = evaluate(obs, obs, body_b, body_b, Action.STAY, 0.0, bold)
    assert b.fear < c.fear


def test_reproduction_pleasure_scales_with_reproduction_drive(body_config) -> None:
    config = TraitConfig()
    base = random_traits(config, np.random.default_rng(0))
    low_drive = dataclasses.replace(base, reproduction_drive=0.0, pleasure_sensitivity=1.0)
    high_drive = dataclasses.replace(base, reproduction_drive=2.5, pleasure_sensitivity=1.0)
    body_l = _body(5, 5, low_drive, body_config)
    body_h = _body(5, 5, high_drive, body_config)
    obs = _zero_obs()
    low = evaluate(obs, obs, body_l, body_l, Action.REPRODUCE, 0.0, low_drive)
    high = evaluate(obs, obs, body_h, body_h, Action.REPRODUCE, 0.0, high_drive)
    assert high.details["reproduction_pleasure"] > low.details["reproduction_pleasure"]


# ---------------------------------------------------------------------------
# Hazard pain (residency)
# ---------------------------------------------------------------------------


def test_standing_on_hazard_produces_hazard_pain(traits, body_config) -> None:
    body = _body(5, 5, traits, body_config)
    safe_obs = _zero_obs()
    haz_obs = _zero_obs(on_hazard=True, current_hazard_damage=10.0)
    safe = evaluate(safe_obs, safe_obs, body, body, Action.STAY, 0.0, traits)
    danger = evaluate(haz_obs, haz_obs, body, body, Action.STAY, 0.0, traits)
    assert danger.details["hazard_pain"] > safe.details["hazard_pain"]


# ---------------------------------------------------------------------------
# Safety pleasure — escape from a hazard
# ---------------------------------------------------------------------------


def test_moving_away_from_hazard_produces_safety_pleasure(traits, body_config) -> None:
    body = _body(5, 5, traits, body_config)
    obs_before = _zero_obs(hazard_signal_north=3.0)
    obs_after = _zero_obs()  # moved away, hazard no longer near
    bd = evaluate(obs_before, obs_after, body, body, Action.MOVE_SOUTH, 1.0, traits)
    assert bd.details["safety_pleasure"] > 0.0


def test_safety_pleasure_zero_when_hazard_unchanged(traits, body_config) -> None:
    body = _body(5, 5, traits, body_config)
    obs = _zero_obs(hazard_signal_north=3.0)
    bd = evaluate(obs, obs, body, body, Action.STAY, 0.0, traits)
    assert bd.details["safety_pleasure"] == 0.0


# ---------------------------------------------------------------------------
# v0.1 placeholders
# ---------------------------------------------------------------------------


def test_novelty_pleasure_zero_without_memory(traits, body_config) -> None:
    body = _body(5, 5, traits, body_config)
    obs = _zero_obs()  # all memory fields default to 0
    bd = evaluate(obs, obs, body, body, Action.STAY, 0.0, traits)
    assert bd.details["novelty_pleasure"] == 0.0
    assert bd.details["novelty_score"] == 0.0


def test_uncertainty_zero_without_memory(traits, body_config) -> None:
    body = _body(5, 5, traits, body_config)
    obs = _zero_obs()
    bd = evaluate(obs, obs, body, body, Action.STAY, 0.0, traits)
    assert bd.uncertainty == 0.0


def test_recovery_pleasure_zero_when_no_health_gain(traits, body_config) -> None:
    body = _body(5, 5, traits, body_config)
    obs = _zero_obs()
    bd = evaluate(obs, obs, body, body, Action.STAY, 0.0, traits)
    assert bd.details["recovery_pleasure"] == 0.0


# ---------------------------------------------------------------------------
# Integration: harness against real observe() output
# ---------------------------------------------------------------------------


def test_harness_runs_against_observe_output(traits, body_config, action_config) -> None:
    """End-to-end smoke: observe() output flows into evaluate() without type errors."""
    world = _empty_world()
    world.kind_layer[5, 7] = CellKind.FOOD
    world.food_value[5, 7] = 25.0
    world.kind_layer[7, 5] = CellKind.HAZARD
    world.hazard_damage[7, 5] = 10.0

    body = _body(5, 5, traits, body_config)
    obs_before = observe(world, body, body_config)
    body_after = dataclasses.replace(
        body, energy=body.energy - action_config.move_cost, y=body.y + 1
    )
    obs_after = observe(world, body_after, body_config)
    cost = action_energy_cost(Action.MOVE_NORTH, action_config)
    bd = evaluate(obs_before, obs_after, body, body_after, Action.MOVE_NORTH, cost, traits)
    assert isinstance(bd, ValenceBreakdown)
    assert math.isfinite(bd.total)


# ---------------------------------------------------------------------------
# Property: NaN-freedom over the full trait/observation space
# ---------------------------------------------------------------------------


@given(seed=st.integers(min_value=0, max_value=2**32 - 1))
def test_evaluate_property_no_nans_under_random_traits(seed: int) -> None:
    """Property: any random traits + arbitrary in-range observation -> finite total."""
    config = TraitConfig()
    rng = np.random.default_rng(seed)
    traits = random_traits(config, rng)
    body_config = BodyConfig()
    body_b = make_body(
        body_id=1, lineage_id=1, parent_id=None, x=0, y=0, traits=traits, config=body_config
    )
    body_a = dataclasses.replace(body_b, energy=max(0.0, body_b.energy - 1.0))
    obs = _zero_obs(
        hunger_level=float(rng.uniform(0.0, 1.0)),
        injury_level=float(rng.uniform(0.0, 1.0)),
        hazard_signal_north=float(rng.uniform(0.0, 5.0)),
        current_food_value=float(rng.uniform(0.0, 30.0)),
        current_hazard_damage=float(rng.uniform(0.0, 20.0)),
    )
    bd = evaluate(obs, obs, body_b, body_a, Action.STAY, 0.1, traits)
    for value in (bd.total, bd.pleasure, bd.pain, bd.fear, bd.uncertainty, bd.effort):
        assert math.isfinite(value)


# ---------------------------------------------------------------------------
# action_energy_cost helper
# ---------------------------------------------------------------------------


def test_action_energy_cost_returns_configured_costs(action_config) -> None:
    assert action_energy_cost(Action.STAY, action_config) == action_config.stay_cost
    assert action_energy_cost(Action.MOVE_NORTH, action_config) == action_config.move_cost
    assert action_energy_cost(Action.MOVE_EAST, action_config) == action_config.move_cost
    assert action_energy_cost(Action.EAT, action_config) == action_config.eat_cost
    assert action_energy_cost(Action.REPRODUCE, action_config) == 0.0


# ---------------------------------------------------------------------------
# Anticipated food pleasure (v0.4) — added in response to the v0.3 null result.
#
# v0.3 evidence: in `tight_gradient` (food + hazard both in sensor range from
# spawn x=1), agents never moved east toward food. Reading valence.py revealed
# the directional ``food_signal_*`` sensor fields existed on Observation but
# were never read — fear/safety drove avoidance, but no symmetric anticipation
# pulled toward food. These tests pin the contract for the missing term.
#
# Formula (per v0.4 design):
#
#     food_signal_gain = max(0, sum(food_signal_*_after) - sum(food_signal_*_before))
#     anticipated_food_pleasure = (
#         food_signal_gain * obs_before.hunger_level * traits.pleasure_sensitivity
#     )
#
# Gating by ``hunger_level`` is load-bearing: full agents must not be pulled.
# ---------------------------------------------------------------------------


def test_anticipated_food_pleasure_pulls_east_when_food_visible_east_and_hungry(
    traits, body_config
) -> None:
    """The candidate that increases the food signal must score higher pleasure.

    Setup: hungry agent, no food visible from current cell. Predicted MOVE_EAST
    increases ``food_signal_east``; predicted MOVE_WEST decreases it. East
    must win on the new ``anticipated_food_pleasure`` field.
    """
    body = _body(5, 5, traits, body_config)
    obs_before = _zero_obs(hunger_level=0.8, food_signal_east=2.0)
    obs_after_east = _zero_obs(hunger_level=0.8, food_signal_east=10.0)  # closer
    obs_after_west = _zero_obs(hunger_level=0.8, food_signal_east=0.5)  # farther

    east = evaluate(obs_before, obs_after_east, body, body, Action.MOVE_EAST, 1.0, traits)
    west = evaluate(obs_before, obs_after_west, body, body, Action.MOVE_WEST, 1.0, traits)

    assert east.details["anticipated_food_pleasure"] > 0.0
    assert west.details["anticipated_food_pleasure"] == 0.0  # clipped at 0
    assert east.pleasure > west.pleasure


def test_anticipated_food_pleasure_is_zero_when_full(traits, body_config) -> None:
    """Full agents (hunger_level == 0) get no pull from food signal gain.

    Without this gate, satiated agents would chase food forever; food
    anticipation must scale with felt hunger to be biologically reasonable.
    """
    body = _body(5, 5, traits, body_config)
    obs_before = _zero_obs(hunger_level=0.0, food_signal_east=2.0)
    obs_after = _zero_obs(hunger_level=0.0, food_signal_east=10.0)
    bd = evaluate(obs_before, obs_after, body, body, Action.MOVE_EAST, 1.0, traits)
    assert bd.details["anticipated_food_pleasure"] == 0.0


def test_anticipated_food_pleasure_scales_monotonically_with_hunger_level(
    traits, body_config
) -> None:
    body = _body(5, 5, traits, body_config)
    food_after = _zero_obs(hunger_level=0.0, food_signal_east=10.0)  # placeholder

    def _score(hunger: float) -> float:
        obs_before = _zero_obs(hunger_level=hunger, food_signal_east=2.0)
        obs_after = dataclasses.replace(food_after, hunger_level=hunger)
        bd = evaluate(obs_before, obs_after, body, body, Action.MOVE_EAST, 1.0, traits)
        return bd.details["anticipated_food_pleasure"]

    low = _score(0.2)
    mid = _score(0.5)
    high = _score(0.9)
    assert low < mid < high


def test_anticipated_food_pleasure_uses_sum_across_directions(traits, body_config) -> None:
    """Gain must be computed on the SUM of all four directional food signals,
    not a single axis. Otherwise an agent at a 4-way symmetric food junction
    (gain on multiple axes) would only feel one direction's pull."""
    body = _body(5, 5, traits, body_config)
    obs_before = _zero_obs(hunger_level=0.7)
    # Two axes light up after the move — the sum gain is 12, not 6.
    obs_after = _zero_obs(hunger_level=0.7, food_signal_east=6.0, food_signal_north=6.0)
    bd = evaluate(obs_before, obs_after, body, body, Action.MOVE_EAST, 1.0, traits)
    expected = 12.0 * 0.7 * traits.pleasure_sensitivity
    assert bd.details["anticipated_food_pleasure"] == pytest.approx(expected)


# ---------------------------------------------------------------------------
# Effort double-channel pin (v0.8 hygiene)
# ---------------------------------------------------------------------------
#
# ``valence.evaluate`` currently routes ``action_energy_cost`` through TWO
# channels:
#
#   1. ``energy_cost_pain = action_energy_cost * traits.hunger_pain_sensitivity``
#      — folded into ``pain``, trait-filtered by hunger sensitivity.
#   2. ``effort = action_energy_cost`` — subtracted at the top level as a
#      raw quantity.
#
# Net subtraction from ``total`` for an action of cost ``c`` and an agent
# with ``hunger_pain_sensitivity = s``: ``c * (1 + s)``.
#
# The valence module's docstring explicitly notes this is intentional ("the
# spec's '- effort_cost' subtraction at the top level is the identical
# quantity weighted differently"), but the double-channel structure is
# easy to miss when reading the breakdown's separate ``effort`` and
# ``pain`` fields. v0.8 pins this behavior so any future
# effort-accounting ablation (consolidating to one channel) fails this
# test loudly instead of silently changing every experiment's net total.
# Effort-accounting ablation itself is deferred — see
# ``docs/experiments/fear_hunger_v0.8.md`` (Deferred work).


def test_action_energy_cost_is_double_channelled_via_pain_and_effort(traits, body_config) -> None:
    """Pin the current double-channel behavior: a unit increase in
    ``action_energy_cost`` reduces ``total`` by ``1 + hunger_pain_sensitivity``,
    not just by 1 (effort alone) or just by ``hunger_pain_sensitivity``
    (energy_cost_pain alone).
    """
    body = _body(5, 5, traits, body_config)
    obs = _zero_obs()
    s = traits.hunger_pain_sensitivity

    # Two evaluations identical except for action_energy_cost.
    bd_zero = evaluate(obs, obs, body, body, Action.STAY, 0.0, traits)
    bd_one = evaluate(obs, obs, body, body, Action.STAY, 1.0, traits)

    # Channel 1: energy_cost_pain (trait-filtered, in `pain`).
    assert bd_zero.details["energy_cost_pain"] == pytest.approx(0.0)
    assert bd_one.details["energy_cost_pain"] == pytest.approx(s)

    # Channel 2: effort (raw, top-level subtraction).
    assert bd_zero.effort == pytest.approx(0.0)
    assert bd_one.effort == pytest.approx(1.0)

    # Combined: total drops by (1 + s) for one unit of cost.
    expected_drop = 1.0 + s
    actual_drop = bd_zero.total - bd_one.total
    assert actual_drop == pytest.approx(expected_drop)


def test_existing_fear_still_pushes_west_when_hazard_visible_east(body_config) -> None:
    """Regression guard: the v0.3 fix must NOT change avoidance behavior.

    Fearful agent, hazard visible east, food invisible. Predicted MOVE_EAST
    increases hazard_signal_east; MOVE_WEST decreases it. West must still
    win on net total (fear up east, safety_pleasure up west).
    """
    cfg = TraitConfig()
    fearful = Traits(
        hunger_pain_sensitivity=cfg.hunger_pain_sensitivity.min,
        injury_pain_sensitivity=cfg.injury_pain_sensitivity.max,
        fear_sensitivity=cfg.fear_sensitivity.max,
        pleasure_sensitivity=(cfg.pleasure_sensitivity.min + cfg.pleasure_sensitivity.max) / 2,
        reproduction_drive=(cfg.reproduction_drive.min + cfg.reproduction_drive.max) / 2,
        novelty_drive=(cfg.novelty_drive.min + cfg.novelty_drive.max) / 2,
        uncertainty_aversion=(cfg.uncertainty_aversion.min + cfg.uncertainty_aversion.max) / 2,
        pain_tolerance=cfg.pain_tolerance.min,
        risk_tolerance=cfg.risk_tolerance.min,
        memory_strength=(cfg.memory_strength.min + cfg.memory_strength.max) / 2,
        memory_decay_rate=(cfg.memory_decay_rate.min + cfg.memory_decay_rate.max) / 2,
        sensor_radius=4,
        metabolic_rate=(cfg.metabolic_rate.min + cfg.metabolic_rate.max) / 2,
    )
    body = _body(5, 5, fearful, body_config)
    obs_before = _zero_obs(hunger_level=0.3, hazard_signal_east=6.0)
    obs_east = _zero_obs(hunger_level=0.3, hazard_signal_east=12.0)  # closer to hazard
    obs_west = _zero_obs(hunger_level=0.3, hazard_signal_east=4.0)  # farther
    east = evaluate(obs_before, obs_east, body, body, Action.MOVE_EAST, 1.0, fearful)
    west = evaluate(obs_before, obs_west, body, body, Action.MOVE_WEST, 1.0, fearful)
    assert west.total > east.total, "Fearful's existing avoidance is broken: west should beat east."
