"""Tests for GradientPolicy — the v0.2 reflex-cell decision rule.

Three layers:
  - Pure decision tests on hand-built Observation / DecisionContext: gradient
    response per direction, auto-EAT on food, STAY when all gradients zero,
    hunger amplification, never-REPRODUCE invariant, tie-break via rng.
  - Trait-coefficient tests: pleasure_sensitivity scales pleasure pull;
    fear_sensitivity * (1 - risk_tolerance) scales pain pull.
  - Integration via HHModel: a GradientPolicy founder steps without raising
    and updates body position consistent with the gradient rule.
"""

from __future__ import annotations

import dataclasses

import numpy as np

from hedonism_harness.core.actions import Action
from hedonism_harness.core.body import make_body
from hedonism_harness.core.config import (
    ActionConfig,
    BodyConfig,
    ReproductionConfig,
    WorldConfig,
)
from hedonism_harness.core.sensors import Observation, observe
from hedonism_harness.core.traits import TraitConfig, random_traits
from hedonism_harness.core.world import CellKind, build_world
from hedonism_harness.mesa_agents import HHAgent
from hedonism_harness.model import FounderSpec, HHModel
from hedonism_harness.policies.base import DecisionContext
from hedonism_harness.policies.gradient_policy import GradientPolicy


def _traits():
    return random_traits(TraitConfig(), np.random.default_rng(0))


def _zero_obs(**overrides) -> Observation:
    base: dict[str, float | int | bool] = {
        "energy_ratio": 0.5,
        "health_ratio": 1.0,
        "hunger_level": 0.5,
        "injury_level": 0.0,
        "age": 5,
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


def _ctx(*, observation: Observation, body=None, occupied=None, seed: int = 0) -> DecisionContext:
    world_cfg = WorldConfig(seed=1, width=8, height=8, food_density=0.0, hazard_density=0.0)
    world = build_world(world_cfg)
    body = body or make_body(
        body_id=1,
        lineage_id=0,
        parent_id=None,
        x=4,
        y=4,
        traits=_traits(),
        config=BodyConfig(),
    )
    return DecisionContext(
        world=world,
        body=body,
        observation=observation,
        rng=np.random.default_rng(seed),
        body_config=BodyConfig(),
        action_config=ActionConfig(),
        memory=None,
        reproduction_config=ReproductionConfig(min_age=10),
        occupied=occupied or frozenset(),
    )


# ---------------------------------------------------------------------------
# Reflex: auto-EAT
# ---------------------------------------------------------------------------


def test_returns_eat_when_on_food() -> None:
    """The on-food cell triggers EAT regardless of gradients elsewhere."""
    policy = GradientPolicy()
    # Place body on a FOOD cell to satisfy get_valid_actions.
    world_cfg = WorldConfig(seed=1, width=8, height=8, food_density=0.0, hazard_density=0.0)
    world = build_world(world_cfg)
    world.kind_layer[4, 4] = CellKind.FOOD
    world.food_value[4, 4] = 5.0
    body = make_body(
        body_id=1,
        lineage_id=0,
        parent_id=None,
        x=4,
        y=4,
        traits=_traits(),
        config=BodyConfig(),
    )
    obs = observe(world, body, BodyConfig(), memory=None)
    ctx = DecisionContext(
        world=world,
        body=body,
        observation=obs,
        rng=np.random.default_rng(0),
        body_config=BodyConfig(),
        action_config=ActionConfig(),
        memory=None,
        reproduction_config=ReproductionConfig(min_age=10),
        occupied=frozenset(),
    )
    decision = policy.decide(ctx)
    assert decision.action == Action.EAT


def test_does_not_eat_when_food_value_zero() -> None:
    """If on_food but current_food_value is 0 (consumed last tick), no EAT."""
    policy = GradientPolicy()
    obs = _zero_obs(on_food=True, current_food_value=0.0)
    decision = policy.decide(ctx=_ctx(observation=obs))
    assert decision.action != Action.EAT


# ---------------------------------------------------------------------------
# Gradient pull
# ---------------------------------------------------------------------------


def test_picks_move_along_strongest_food_gradient() -> None:
    policy = GradientPolicy()
    obs = _zero_obs(
        food_signal_east=5.0, food_signal_west=1.0, food_signal_north=0.0, food_signal_south=0.0
    )
    decision = policy.decide(ctx=_ctx(observation=obs))
    assert decision.action == Action.MOVE_EAST


def test_picks_move_away_from_hazard_when_pleasure_zero() -> None:
    """No food, hazard east; the cell should NOT move east. Net is the
    inverse pull — it picks STAY since all gradients sum to negative or zero."""
    policy = GradientPolicy()
    obs = _zero_obs(hazard_signal_east=5.0)
    decision = policy.decide(ctx=_ctx(observation=obs))
    # Net pull: MOVE_EAST = 0 - pain_w * 5 = negative; STAY = 0; others = 0.
    # STAY wins.
    assert decision.action == Action.STAY


def test_balances_pleasure_against_pain() -> None:
    """Strong food east + strong hazard east -> the cell still goes east only
    if pleasure pull exceeds pain pull. Use traits where it does."""
    policy = GradientPolicy()
    traits = dataclasses.replace(
        _traits(),
        pleasure_sensitivity=2.0,
        fear_sensitivity=0.5,
        risk_tolerance=0.5,
    )
    body = make_body(
        body_id=1,
        lineage_id=0,
        parent_id=None,
        x=4,
        y=4,
        traits=traits,
        config=BodyConfig(),
    )
    obs = _zero_obs(food_signal_east=10.0, hazard_signal_east=2.0)
    decision = policy.decide(ctx=_ctx(observation=obs, body=body))
    # pleasure_w = 2.0 * 1.5 = 3.0 (hunger_amp=1.5); pain_w = 0.5 * 0.5 = 0.25
    # net_east = 3.0 * 10 - 0.25 * 2 = 30 - 0.5 = 29.5 >> 0; MOVE_EAST wins.
    assert decision.action == Action.MOVE_EAST


def test_stays_when_all_gradients_zero() -> None:
    """Featureless cell -> no movement (STAY pull = 0 beats negative; ties
    among other zero-pull moves are broken by rng but STAY wins because it's
    the only zero-pull action explicitly seeded to best_net=0)."""
    policy = GradientPolicy()
    obs = _zero_obs()  # all signals zero
    decision = policy.decide(ctx=_ctx(observation=obs))
    assert decision.action == Action.STAY


# ---------------------------------------------------------------------------
# Hunger amplification
# ---------------------------------------------------------------------------


def test_hunger_amplifies_pleasure_pull() -> None:
    """A hungry cell should respond to pleasure gradients more strongly than
    a sated cell. We compare net pulls indirectly via decision: if hunger
    flips a sated-cell STAY into a hungry-cell MOVE, the amplification
    applies."""
    policy = GradientPolicy()
    traits = dataclasses.replace(
        _traits(),
        pleasure_sensitivity=1.0,
        fear_sensitivity=2.0,
        risk_tolerance=0.0,  # full fear weight
    )
    body = make_body(
        body_id=1,
        lineage_id=0,
        parent_id=None,
        x=4,
        y=4,
        traits=traits,
        config=BodyConfig(),
    )
    # Choose signals where:
    # - sated (hunger=0): pleasure_w = 1.0 * 1.0 = 1.0; pain_w = 2.0 * 1.0 = 2.0;
    #   net_east = 1.0 * 3.0 - 2.0 * 2.0 = 3.0 - 4.0 = -1.0 -> STAY wins.
    # - hungry (hunger=1): pleasure_w = 1.0 * 2.0 = 2.0;
    #   net_east = 2.0 * 3.0 - 2.0 * 2.0 = 6.0 - 4.0 = 2.0 -> MOVE_EAST wins.
    obs_sated = _zero_obs(hunger_level=0.0, food_signal_east=3.0, hazard_signal_east=2.0)
    obs_hungry = _zero_obs(hunger_level=1.0, food_signal_east=3.0, hazard_signal_east=2.0)
    sated = policy.decide(ctx=_ctx(observation=obs_sated, body=body))
    hungry = policy.decide(ctx=_ctx(observation=obs_hungry, body=body))
    assert sated.action == Action.STAY
    assert hungry.action == Action.MOVE_EAST


# ---------------------------------------------------------------------------
# REPRODUCE invariant
# ---------------------------------------------------------------------------


def test_never_returns_reproduce_even_when_eligible() -> None:
    """REPRODUCE remains in the action enum and may be in the valid set
    when the agent is eligible. GradientPolicy must never select it —
    auto-reproduction is a substrate phase, not a behavior."""
    policy = GradientPolicy()
    # Build a body that satisfies can_reproduce: full energy, old enough,
    # adjacent open cells. The policy should still pick STAY/MOVE/EAT.
    body = make_body(
        body_id=1,
        lineage_id=0,
        parent_id=None,
        x=4,
        y=4,
        traits=_traits(),
        config=BodyConfig(),
    )
    body = dataclasses.replace(body, energy=100.0, age=30)
    obs = _zero_obs(hunger_level=0.0)  # sated, no gradients
    decision = policy.decide(ctx=_ctx(observation=obs, body=body))
    assert decision.action != Action.REPRODUCE


# ---------------------------------------------------------------------------
# Integration — GradientPolicy in HHModel
# ---------------------------------------------------------------------------


# ---------------------------------------------------------------------------
# v0.26: hazard_avoidance_weight seam (perception-vs-damage decoupling)
# ---------------------------------------------------------------------------


def test_default_hazard_avoidance_weight_is_one() -> None:
    """The seam default is 1.0; constructing without the kwarg matches."""
    a = GradientPolicy()
    b = GradientPolicy(hazard_avoidance_weight=1.0)
    assert a.hazard_avoidance_weight == 1.0
    assert b.hazard_avoidance_weight == 1.0


def test_hazard_avoidance_weight_zero_disables_pain_pull() -> None:
    """At weight=0, hazard pull contributes zero — a strong-pleasure /
    strong-hazard cell that STAYed under default coupling now MOVEs toward
    the hazard because pleasure pull goes unopposed."""
    traits = dataclasses.replace(
        _traits(),
        pleasure_sensitivity=1.0,
        fear_sensitivity=2.0,
        risk_tolerance=0.0,
    )
    body = make_body(
        body_id=1,
        lineage_id=0,
        parent_id=None,
        x=4,
        y=4,
        traits=traits,
        config=BodyConfig(),
    )
    obs_strong_hazard = _zero_obs(hunger_level=1.0, food_signal_east=3.0, hazard_signal_east=10.0)
    # Default: pleasure=6, pain=20 -> net=-14 -> STAY.
    default_decision = GradientPolicy().decide(ctx=_ctx(observation=obs_strong_hazard, body=body))
    assert default_decision.action == Action.STAY
    # Weight=0: pain=0 -> net=+6 -> MOVE_EAST.
    invisible_decision = GradientPolicy(hazard_avoidance_weight=0.0).decide(
        ctx=_ctx(observation=obs_strong_hazard, body=body)
    )
    assert invisible_decision.action == Action.MOVE_EAST


def test_hazard_avoidance_weight_one_is_no_op_against_default() -> None:
    """Explicit weight=1.0 produces identical decisions to the default
    constructor across a basket of synthetic observations. Halt-condition
    smoke for v0.26 H14."""
    default_policy = GradientPolicy()
    explicit_policy = GradientPolicy(hazard_avoidance_weight=1.0)
    cases = [
        _zero_obs(food_signal_east=5.0),
        _zero_obs(hazard_signal_east=5.0),
        _zero_obs(food_signal_east=3.0, hazard_signal_east=2.0, hunger_level=1.0),
        _zero_obs(food_signal_north=2.0, food_signal_south=2.0),
    ]
    for obs in cases:
        d1 = default_policy.decide(ctx=_ctx(observation=obs, seed=42))
        d2 = explicit_policy.decide(ctx=_ctx(observation=obs, seed=42))
        assert d1.action == d2.action


def test_hazard_avoidance_weight_negative_rejected() -> None:
    """Validator rejects negative weights at construction time."""
    import pytest

    with pytest.raises(ValueError, match="hazard_avoidance_weight"):
        GradientPolicy(hazard_avoidance_weight=-0.1)


def test_gradient_policy_steps_in_model_without_raising() -> None:
    """End-to-end: a model with GradientPolicy founders runs N ticks without
    error and the agents take valid actions."""
    world_cfg = WorldConfig(seed=1, width=8, height=8, food_density=0.0, hazard_density=0.0)
    model = HHModel(
        world_cfg,
        founders=[
            FounderSpec(x=2, y=2, policy_factory=GradientPolicy),
            FounderSpec(x=5, y=5, policy_factory=GradientPolicy),
        ],
        body_config=BodyConfig(),
        reproduction_config=ReproductionConfig(min_age=10),
    )
    for _ in range(5):
        model.step()
    living = [a for a in model.agents if isinstance(a, HHAgent) and a.body.alive]
    assert len(living) >= 1  # at least one agent alive after 5 ticks
