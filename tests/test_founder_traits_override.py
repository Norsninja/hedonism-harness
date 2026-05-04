"""``FounderSpec.traits_override`` must short-circuit ``random_traits``.

The v0.2 positive-control runner relies on this seam to inject deterministic
archetype Traits. If the override is silently ignored — or if traits drift
through ``random_traits`` even when the spec carries an override — the entire
positive-control comparison loses its signal.
"""

from __future__ import annotations

from hedonism_harness.core.config import WorldConfig
from hedonism_harness.experiments.trait_archetypes import fearful, reckless
from hedonism_harness.mesa_agents import HHAgent
from hedonism_harness.model import FounderSpec, HHModel
from hedonism_harness.policies.hedonism_policy import HedonismPolicy


def _policy() -> HedonismPolicy:
    return HedonismPolicy(exploration_noise=0.0)


def test_traits_override_is_used_verbatim_when_provided() -> None:
    target = reckless()
    cfg = WorldConfig(seed=1, width=6, height=6, food_density=0.0, hazard_density=0.0)
    founders = [
        FounderSpec(x=2, y=2, policy_factory=_policy, traits_override=target),
        FounderSpec(x=3, y=3, policy_factory=_policy, traits_override=target),
    ]
    model = HHModel(cfg, founders=founders)

    agents = [a for a in model.agents if isinstance(a, HHAgent)]
    assert len(agents) == 2
    for agent in agents:
        assert agent.body.traits == target


def test_omitted_override_falls_back_to_random_traits() -> None:
    """Without an override, the founder samples from TraitConfig — different
    seeds should usually yield different Traits."""
    cfg_a = WorldConfig(seed=1, width=6, height=6, food_density=0.0, hazard_density=0.0)
    cfg_b = WorldConfig(seed=2, width=6, height=6, food_density=0.0, hazard_density=0.0)
    spec = lambda: [FounderSpec(x=2, y=2, policy_factory=_policy)]  # noqa: E731

    a = HHModel(cfg_a, founders=spec())
    b = HHModel(cfg_b, founders=spec())
    a_agent = next(x for x in a.agents if isinstance(x, HHAgent))
    b_agent = next(x for x in b.agents if isinstance(x, HHAgent))
    assert a_agent.body.traits != b_agent.body.traits


def test_each_founder_can_carry_a_distinct_override() -> None:
    """Per-founder overrides must NOT bleed across spec entries."""
    cfg = WorldConfig(seed=1, width=8, height=8, food_density=0.0, hazard_density=0.0)
    f_traits = fearful()
    r_traits = reckless()
    founders = [
        FounderSpec(x=1, y=1, policy_factory=_policy, traits_override=f_traits),
        FounderSpec(x=2, y=2, policy_factory=_policy, traits_override=r_traits),
    ]
    model = HHModel(cfg, founders=founders)
    agents_by_pos = {(a.body.x, a.body.y): a for a in model.agents if isinstance(a, HHAgent)}
    assert agents_by_pos[(1, 1)].body.traits == f_traits
    assert agents_by_pos[(2, 2)].body.traits == r_traits
