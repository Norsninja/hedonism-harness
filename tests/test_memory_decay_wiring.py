"""SPEC §13.3 — per-tick memory decay must fire for memory-enabled agents.

Pre-v0.9b regression: ``decay_all`` was defined in ``core/memory.py`` and
exercised by ``tests/test_memory.py`` but no caller invoked it from the
simulation tick loop. Memory accumulated indefinitely, so
``traits.memory_decay_rate`` was a dormant parameter and stale food
attractors never faded after consumption.

This module pins the v0.9b wiring: ``HHAgent.apply_memory_decay`` exists,
runs once per tick alongside ``apply_metabolism_step`` (SPEC §27.4 step
4), is a no-op for non-memory agents and dead agents, and shrinks the
EMA layers by ``(1 - traits.memory_decay_rate)`` each tick.
"""

from __future__ import annotations

import dataclasses

import numpy as np

from hedonism_harness.core.actions import Action
from hedonism_harness.core.config import BodyConfig, ReproductionConfig, WorldConfig
from hedonism_harness.core.memory import update_at
from hedonism_harness.core.traits import TraitConfig, random_traits
from hedonism_harness.mesa_agents import HHAgent
from hedonism_harness.model import FounderSpec, HHModel
from hedonism_harness.policies.base import PolicyDecision


class _AlwaysStayPolicy:
    def decide(self, ctx):  # type: ignore[no-untyped-def]
        return PolicyDecision(action=Action.STAY, breakdown=None)


def _build_model(
    *,
    use_memory: bool,
    memory_strength: float = 0.5,
    memory_decay_rate: float = 0.1,
) -> HHModel:
    world_cfg = WorldConfig(seed=42, width=4, height=4, food_density=0.0, hazard_density=0.0)
    body_cfg = BodyConfig(starting_energy=100.0)
    repro_cfg = ReproductionConfig(min_age=10)
    base_traits = random_traits(TraitConfig(), np.random.default_rng(0))
    traits = dataclasses.replace(
        base_traits,
        memory_strength=memory_strength,
        memory_decay_rate=memory_decay_rate,
    )
    return HHModel(
        world_cfg,
        founders=[
            FounderSpec(
                x=2,
                y=2,
                policy_factory=_AlwaysStayPolicy,
                use_memory=use_memory,
                traits_override=traits,
            )
        ],
        body_config=body_cfg,
        reproduction_config=repro_cfg,
    )


def _agent(model: HHModel) -> HHAgent:
    return next(a for a in model.agents if isinstance(a, HHAgent))


def test_apply_memory_decay_is_noop_when_memory_is_none() -> None:
    """``use_memory=False`` agents have ``memory=None``; decay must not crash."""
    model = _build_model(use_memory=False)
    agent = _agent(model)
    assert agent.memory is None
    agent.apply_memory_decay()  # must not raise
    assert agent.memory is None


def test_apply_memory_decay_is_noop_when_dead() -> None:
    """Dead agents must not have their memory decayed (defensive)."""
    model = _build_model(use_memory=True)
    agent = _agent(model)
    # Plant a positive value that decay would shrink.
    agent.memory.pleasure_ema[1, 1] = 5.0
    agent.body = dataclasses.replace(agent.body, alive=False)
    agent.apply_memory_decay()
    assert agent.memory.pleasure_ema[1, 1] == 5.0


def test_apply_memory_decay_uses_traits_memory_decay_rate() -> None:
    """One call shrinks ``pleasure_ema`` and ``pain_ema`` by ``1 - rate``."""
    model = _build_model(use_memory=True, memory_decay_rate=0.2)
    agent = _agent(model)
    agent.memory.pleasure_ema[0, 0] = 10.0
    agent.memory.pain_ema[0, 0] = 4.0
    agent.apply_memory_decay()
    assert agent.memory.pleasure_ema[0, 0] == 8.0  # 10 * (1 - 0.2)
    assert agent.memory.pain_ema[0, 0] == 3.2  # 4 * (1 - 0.2)


def test_apply_memory_decay_with_zero_rate_is_noop() -> None:
    """``memory_decay_rate == 0`` keeps the layers unchanged (matches
    ``decay_all`` early-return)."""
    model = _build_model(use_memory=True, memory_decay_rate=0.0)
    agent = _agent(model)
    agent.memory.pleasure_ema[0, 0] = 7.5
    agent.apply_memory_decay()
    assert agent.memory.pleasure_ema[0, 0] == 7.5


def test_model_step_applies_memory_decay_each_tick() -> None:
    """End-to-end pin: ``HHModel.step`` calls ``apply_memory_decay`` after
    ``apply_metabolism_step``. After N ticks of STAY (one ``update_at``
    per tick at the agent's cell), the standing-cell ``pleasure_ema``
    follows the EMA-then-decay recurrence.

    With memory_strength=0.5 and pleasure=0 (STAY produces no pleasure):
        u_{t+1} = ((1 - alpha) * u_t + alpha * 0) * (1 - decay)
                = u_t * (1 - alpha) * (1 - decay)

    Plant a positive seed value, run a few ticks, assert the value
    shrunk strictly (proves both update + decay fired)."""
    model = _build_model(use_memory=True, memory_strength=0.5, memory_decay_rate=0.1)
    agent = _agent(model)
    x0, y0 = agent.body.x, agent.body.y
    agent.memory.pleasure_ema[x0, y0] = 100.0

    model.step()

    after = float(agent.memory.pleasure_ema[x0, y0])
    # Combined EMA + decay: 100 * (1 - alpha) * (1 - 0.1) = 100 * 0.5 * 0.9 = 45.0
    # alpha = 1 - memory_strength = 0.5 (with floor 0.05).
    assert after == 45.0


def test_model_step_does_not_decay_non_memory_agents() -> None:
    """``use_memory=False`` agents pass through the decay step without
    side-effects (sanity: memory stays None)."""
    model = _build_model(use_memory=False)
    agent = _agent(model)
    assert agent.memory is None
    model.step()
    assert agent.memory is None


def test_planted_pleasure_decays_to_zero_under_repeated_steps() -> None:
    """A non-revisited pleasure attractor fades exponentially. Plant a
    value at a cell the agent never sits on and let decay drive it down."""
    model = _build_model(use_memory=True, memory_strength=0.5, memory_decay_rate=0.5)
    agent = _agent(model)
    far_x, far_y = 0, 0  # agent is at (2, 2); STAY never visits (0, 0).
    agent.memory.pleasure_ema[far_x, far_y] = 1.0

    for _ in range(10):
        model.step()

    # pleasure_ema *= (1 - 0.5) per step, no update at this cell.
    # 1.0 * 0.5^10 ~= 9.77e-4.
    assert agent.memory.pleasure_ema[far_x, far_y] < 1e-2
    assert agent.memory.pleasure_ema[far_x, far_y] > 0.0  # strictly positive (no clamp)


def test_decay_does_not_mutate_visits_or_last_seen() -> None:
    """Decay touches only the EMA layers; visits and last_seen are
    monotonic per SPEC §13. Pin via the wiring, not just the unit module."""
    model = _build_model(use_memory=True, memory_decay_rate=0.5)
    agent = _agent(model)
    # Seed a cell as visited.
    update_at(
        agent.memory,
        x=1,
        y=1,
        pleasure=0.0,
        pain=0.0,
        traits=agent.body.traits,
        tick=0,
    )
    visits_before = int(agent.memory.visits[1, 1])
    last_seen_before = int(agent.memory.last_seen_tick[1, 1])

    agent.apply_memory_decay()

    assert int(agent.memory.visits[1, 1]) == visits_before
    assert int(agent.memory.last_seen_tick[1, 1]) == last_seen_before
