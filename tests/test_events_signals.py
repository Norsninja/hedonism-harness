"""Blinker signal wiring + HazardDamageApplied emission + defensive valid-action check."""

from __future__ import annotations

import pytest

from hedonism_harness.core.actions import Action
from hedonism_harness.core.config import BodyConfig, ReproductionConfig, WorldConfig
from hedonism_harness.core.events import (
    AgentMoved,
    AteFood,
    HazardDamageApplied,
    signal_for,
)
from hedonism_harness.core.world import CellKind
from hedonism_harness.mesa_agents import HHAgent
from hedonism_harness.model import FounderSpec, HHModel
from hedonism_harness.policies.base import DecisionContext, PolicyDecision
from hedonism_harness.policies.random_policy import RandomPolicy


class _Capture:
    """Subscribes to a signal; collects events; ``close()`` disconnects."""

    def __init__(self, event_type: type) -> None:
        self.events: list[object] = []
        self._sig = signal_for(event_type)
        self._handler = self._on_event
        self._sig.connect(self._handler)

    def _on_event(self, sender: object, event: object) -> None:
        self.events.append(event)

    def close(self) -> None:
        self._sig.disconnect(self._handler)


# ---------------------------------------------------------------------------
# Signal emission
# ---------------------------------------------------------------------------


def test_signal_for_returns_named_singletons() -> None:
    a = signal_for(AgentMoved)
    b = signal_for(AgentMoved)
    assert a is b


def test_record_event_fires_signal() -> None:
    cap = _Capture(AteFood)
    try:
        cfg = WorldConfig(seed=1, width=4, height=4, food_density=0.0, hazard_density=0.0)
        model = HHModel(cfg, founders=[FounderSpec(x=1, y=1, policy_factory=RandomPolicy)])
        ev = AteFood(agent_id=1, x=1, y=1, food_gained=10.0)
        model.record_event(ev)
        assert cap.events == [ev]
    finally:
        cap.close()


# ---------------------------------------------------------------------------
# HazardDamageApplied wiring
# ---------------------------------------------------------------------------


class _StayPolicy:
    def decide(self, ctx: DecisionContext) -> PolicyDecision:
        return PolicyDecision(action=Action.STAY, breakdown=None)


def test_hazard_damage_applied_event_fires_on_residency() -> None:
    cfg = WorldConfig(seed=1, width=5, height=5, food_density=0.0, hazard_density=0.0)
    model = HHModel(cfg, founders=[FounderSpec(x=2, y=2, policy_factory=_StayPolicy)])
    # Place a hazard ON the agent so step's residency check applies damage.
    model.world.kind_layer[2, 2] = CellKind.HAZARD
    model.world.hazard_damage[2, 2] = 5.0

    cap = _Capture(HazardDamageApplied)
    try:
        model.step()
    finally:
        cap.close()

    assert len(cap.events) == 1
    ev = cap.events[0]
    assert isinstance(ev, HazardDamageApplied)
    assert ev.damage == pytest.approx(5.0)
    assert ev.x == 2
    assert ev.y == 2
    # And the body's HP dropped accordingly.
    agent = next(a for a in model.agents if isinstance(a, HHAgent))
    assert agent.body.health == pytest.approx(95.0)


# ---------------------------------------------------------------------------
# Defensive valid-action assertion
# ---------------------------------------------------------------------------


class _RogueRepoducePolicy:
    """Always claims REPRODUCE — invalid when reproduction config not provided."""

    def decide(self, ctx: DecisionContext) -> PolicyDecision:
        return PolicyDecision(action=Action.REPRODUCE, breakdown=None)


def test_defensive_assertion_rejects_invalid_action() -> None:
    """A policy that returns an action outside get_valid_actions(...) must fail loudly."""
    cfg = WorldConfig(seed=1, width=4, height=4, food_density=0.0, hazard_density=0.0)
    body_cfg = BodyConfig(starting_energy=10.0)  # too low to reproduce
    repro_cfg = ReproductionConfig(energy_threshold=70.0, min_age=10)
    model = HHModel(
        cfg,
        founders=[FounderSpec(x=1, y=1, policy_factory=_RogueRepoducePolicy)],
        body_config=body_cfg,
        reproduction_config=repro_cfg,
    )
    with pytest.raises(AssertionError, match="not in get_valid_actions"):
        model.step()


# ---------------------------------------------------------------------------
# Determinism: signal subscribers do not perturb model state
# ---------------------------------------------------------------------------


def test_subscribers_do_not_perturb_state() -> None:
    """Connecting a passive subscriber must not change the simulation outcome."""
    cfg = WorldConfig(seed=42, width=8, height=8, food_density=0.0, hazard_density=0.0)

    def build() -> HHModel:
        return HHModel(
            cfg,
            founders=[
                FounderSpec(x=2, y=2, policy_factory=RandomPolicy),
                FounderSpec(x=5, y=5, policy_factory=RandomPolicy),
            ],
        )

    # Run A: no subscribers.
    a = build()
    for _ in range(10):
        a.step()
    state_a = (
        a.world.kind_layer.tobytes(),
        tuple(repr(x.body) for x in a.agents if isinstance(x, HHAgent)),
    )

    # Run B: passive subscriber on every signal.
    captured: list[object] = []

    def _listener(_sender: object, event: object) -> None:
        captured.append(event)

    handlers = []
    for cls in (AgentMoved, HazardDamageApplied, AteFood):
        signal_for(cls).connect(_listener)
        handlers.append((cls, _listener))

    try:
        b = build()
        for _ in range(10):
            b.step()
        state_b = (
            b.world.kind_layer.tobytes(),
            tuple(repr(x.body) for x in b.agents if isinstance(x, HHAgent)),
        )
    finally:
        for cls, h in handlers:
            signal_for(cls).disconnect(h)

    assert state_a == state_b
