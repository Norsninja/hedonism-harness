"""Tests for v0.2 substrate-triggered auto-reproduction.

Three layers:
  - HHModel.auto_reproduction_enabled defaults to False (preserves
    v0.1/v0.7..v0.13 voluntary-REPRODUCE bit-identity).
  - When False, HHAgent.apply_auto_reproduction is a no-op even when
    body state satisfies can_reproduce.
  - When True, eligible bodies queue births via the existing
    _birth_queue infrastructure; ReproductionRequested is emitted so
    metrics aggregators count them.
  - trait_fingerprints log is populated at every spawn (founder +
    child) regardless of which trigger pathway fired.
"""

from __future__ import annotations

import dataclasses

import numpy as np

from hedonism_harness.core.config import (
    ActionConfig,
    BodyConfig,
    ReproductionConfig,
    WorldConfig,
)
from hedonism_harness.core.events import AgentBorn, ReproductionRequested, signal_for
from hedonism_harness.core.traits import TraitConfig, random_traits
from hedonism_harness.mesa_agents import HHAgent
from hedonism_harness.model import FounderSpec, HHModel
from hedonism_harness.policies.gradient_policy import GradientPolicy
from hedonism_harness.policies.reflex_policy import ReflexPolicy


def _traits():
    return random_traits(TraitConfig(), np.random.default_rng(0))


def _build_model(*, seed: int = 1) -> HHModel:
    world_cfg = WorldConfig(seed=seed, width=8, height=8, food_density=0.0, hazard_density=0.0)
    body_cfg = BodyConfig()
    repro_cfg = ReproductionConfig(min_age=2, energy_threshold=20.0, energy_cost=10.0)
    return HHModel(
        world_cfg,
        founders=[
            FounderSpec(x=2, y=3, policy_factory=GradientPolicy),
            FounderSpec(x=5, y=5, policy_factory=GradientPolicy),
        ],
        body_config=body_cfg,
        action_config=ActionConfig(),
        reproduction_config=repro_cfg,
    )


def test_auto_reproduction_disabled_by_default() -> None:
    model = _build_model()
    assert model.auto_reproduction_enabled is False


def test_apply_auto_reproduction_is_noop_when_disabled() -> None:
    """Eligible body, but flag off — no birth queued, no event emitted."""
    model = _build_model()
    agent = next(a for a in model.agents if isinstance(a, HHAgent))
    # Make agent eligible: high energy, old enough.
    agent.body = dataclasses.replace(agent.body, energy=100.0, age=10)
    seen: list = []

    def _on_request(_sender, event):
        seen.append(event)

    signal_for(ReproductionRequested).connect(_on_request, sender=model, weak=False)
    agent.apply_auto_reproduction()
    assert seen == []
    assert model._birth_queue == []  # type: ignore[attr-defined]


def test_apply_auto_reproduction_queues_birth_and_emits_when_enabled() -> None:
    model = _build_model()
    model.auto_reproduction_enabled = True
    agent = next(a for a in model.agents if isinstance(a, HHAgent))
    agent.body = dataclasses.replace(agent.body, energy=100.0, age=10)

    seen_requests: list = []

    def _on_request(_sender, event):
        seen_requests.append(event)

    signal_for(ReproductionRequested).connect(_on_request, sender=model, weak=False)
    agent.apply_auto_reproduction()

    assert len(seen_requests) == 1
    assert agent in model._birth_queue  # type: ignore[attr-defined]


def test_apply_auto_reproduction_skips_dead_agent() -> None:
    model = _build_model()
    model.auto_reproduction_enabled = True
    agent = next(a for a in model.agents if isinstance(a, HHAgent))
    agent.body = dataclasses.replace(agent.body, alive=False)
    agent.apply_auto_reproduction()
    assert model._birth_queue == []  # type: ignore[attr-defined]


def test_apply_auto_reproduction_skips_when_can_reproduce_false() -> None:
    """Low energy: not eligible -> no birth queued."""
    model = _build_model()
    model.auto_reproduction_enabled = True
    agent = next(a for a in model.agents if isinstance(a, HHAgent))
    agent.body = dataclasses.replace(agent.body, energy=5.0, age=10)
    agent.apply_auto_reproduction()
    assert model._birth_queue == []  # type: ignore[attr-defined]


def test_model_step_runs_phase_45_when_enabled() -> None:
    """Full model.step() with auto enabled fires apply_auto_reproduction
    for every living agent and produces births under suitable trait state."""
    model = _build_model()
    model.auto_reproduction_enabled = True
    # Make all founders immediately eligible.
    for agent in list(model.agents):
        if isinstance(agent, HHAgent):
            agent.body = dataclasses.replace(agent.body, energy=100.0, age=10)

    born_events: list = []

    def _on_born(_sender, event):
        born_events.append(event)

    signal_for(AgentBorn).connect(_on_born, sender=model, weak=False)

    for _ in range(3):
        model.step()

    assert len(born_events) >= 1


def test_trait_fingerprints_populated_for_founders() -> None:
    model = _build_model()
    # Two founders -> two fingerprints.
    assert len(model.trait_fingerprints) == 2
    for entry in model.trait_fingerprints:
        assert entry["parent_id"] is None  # founders have no parent
        assert entry["birth_tick"] == 0
        assert "pleasure_sensitivity" in entry
        assert "fear_sensitivity" in entry


def test_trait_fingerprints_populated_for_births() -> None:
    """When a child is born, its trait fingerprint is appended to the model log."""
    model = _build_model()
    model.auto_reproduction_enabled = True
    for agent in list(model.agents):
        if isinstance(agent, HHAgent):
            agent.body = dataclasses.replace(agent.body, energy=100.0, age=10)
    fingerprints_before = len(model.trait_fingerprints)
    for _ in range(3):
        model.step()
    fingerprints_after = len(model.trait_fingerprints)
    assert fingerprints_after > fingerprints_before


def test_v07_v013_default_remains_voluntary_reproduction() -> None:
    """Building a model without setting auto_reproduction_enabled keeps
    the v0.7..v0.13 behavior. Eligibility is checked via voluntary
    REPRODUCE in apply_action; no auto trigger fires."""
    world_cfg = WorldConfig(seed=1, width=6, height=4, food_density=0.0, hazard_density=0.0)
    model = HHModel(
        world_cfg,
        founders=[FounderSpec(x=1, y=1, policy_factory=ReflexPolicy)],
        body_config=BodyConfig(),
        reproduction_config=ReproductionConfig(min_age=2, energy_threshold=20.0, energy_cost=10.0),
    )
    assert model.auto_reproduction_enabled is False
    # The founder steps; if auto-trigger were active, they'd queue a
    # birth eventually — but with reflex policy + no eligibility-pumping
    # they don't reach threshold quickly. The invariant we assert is the
    # flag itself.
    for _ in range(3):
        model.step()
    assert model.auto_reproduction_enabled is False
