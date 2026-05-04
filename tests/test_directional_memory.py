"""Tests for ``core/memory.DirectionalMemory`` (SPEC §13, v0.11 abstraction).

The v0.11 alternative to cell-exact memory: 4-vector pleasure/pain
tendencies indexed by cardinal direction, updated only when the agent
actually moves. Bacterial-chemotaxis-style — survives food consumption
naturally because the abstraction was never about specific cells.
"""

from __future__ import annotations

import dataclasses

import numpy as np
import pytest

from hedonism_harness.core.actions import Action, get_valid_actions
from hedonism_harness.core.body import make_body
from hedonism_harness.core.config import BodyConfig, ReproductionConfig, WorldConfig
from hedonism_harness.core.memory import (
    DIRECTION_NAMES,
    DirectionalMemory,
    decay_directional,
    directional_signals_directional,
    make_directional_memory,
    update_directional,
)
from hedonism_harness.core.sensors import observe
from hedonism_harness.core.traits import TraitConfig, random_traits
from hedonism_harness.core.world import build_world
from hedonism_harness.mesa_agents import HHAgent
from hedonism_harness.model import FounderSpec, HHModel
from hedonism_harness.policies.base import PolicyDecision


def _traits_with(memory_strength: float = 0.5, memory_decay_rate: float = 0.1):
    base = random_traits(TraitConfig(), np.random.default_rng(0))
    return dataclasses.replace(
        base, memory_strength=memory_strength, memory_decay_rate=memory_decay_rate
    )


# ---------------------------------------------------------------------------
# Construction
# ---------------------------------------------------------------------------


def test_make_directional_memory_returns_zero_tendencies() -> None:
    mem = make_directional_memory()
    assert mem.pleasure_tendency.shape == (4,)
    assert mem.pain_tendency.shape == (4,)
    assert mem.pleasure_tendency.dtype == np.float32
    assert mem.pain_tendency.dtype == np.float32
    assert float(mem.pleasure_tendency.sum()) == 0.0
    assert float(mem.pain_tendency.sum()) == 0.0


def test_direction_names_are_nsew_in_order() -> None:
    """Index convention is (N, S, E, W) — north=+y, east=+x."""
    assert DIRECTION_NAMES == ("north", "south", "east", "west")


# ---------------------------------------------------------------------------
# update_directional
# ---------------------------------------------------------------------------


def test_update_directional_writes_only_to_move_direction_slot() -> None:
    """Moving north (dx=0, dy=1) must update only the north slot."""
    mem = make_directional_memory()
    traits = _traits_with(memory_strength=0.5)  # alpha = 0.5
    update_directional(mem, dx=0, dy=1, pleasure=4.0, pain=1.0, traits=traits)
    # north slot moves toward target by alpha
    assert mem.pleasure_tendency[0] == 2.0  # (1 - 0.5) * 0 + 0.5 * 4 = 2
    assert mem.pain_tendency[0] == 0.5
    # other slots untouched
    assert float(mem.pleasure_tendency[1:].sum()) == 0.0
    assert float(mem.pain_tendency[1:].sum()) == 0.0


def test_update_directional_dispatches_each_cardinal_to_its_slot() -> None:
    """Each of N/S/E/W lands in the right slot; distinct vectors stay distinct."""
    traits = _traits_with(memory_strength=0.5)
    cases = [
        ((0, 1), 0, "north"),
        ((0, -1), 1, "south"),
        ((1, 0), 2, "east"),
        ((-1, 0), 3, "west"),
    ]
    for (dx, dy), idx, _name in cases:
        mem = make_directional_memory()
        update_directional(mem, dx=dx, dy=dy, pleasure=10.0, pain=0.0, traits=traits)
        assert mem.pleasure_tendency[idx] == 5.0
        # All other slots are 0.
        for j in range(4):
            if j == idx:
                continue
            assert mem.pleasure_tendency[j] == 0.0


def test_update_directional_skips_stay_and_diagonal() -> None:
    """STAY (dx=0, dy=0) and any non-unit displacement must be a no-op."""
    traits = _traits_with(memory_strength=0.5)
    mem = make_directional_memory()
    update_directional(mem, dx=0, dy=0, pleasure=99.0, pain=99.0, traits=traits)
    assert float(mem.pleasure_tendency.sum()) == 0.0
    assert float(mem.pain_tendency.sum()) == 0.0
    # Diagonals never appear in MOVE_DIRECTIONS but guard regardless.
    update_directional(mem, dx=1, dy=1, pleasure=99.0, pain=99.0, traits=traits)
    assert float(mem.pleasure_tendency.sum()) == 0.0


def test_update_directional_uses_alpha_from_memory_strength() -> None:
    """High memory_strength -> slow EMA update (small alpha)."""
    traits_slow = _traits_with(memory_strength=1.0)  # alpha floors to 0.05
    mem = make_directional_memory()
    update_directional(mem, dx=0, dy=1, pleasure=10.0, pain=0.0, traits=traits_slow)
    assert mem.pleasure_tendency[0] == 0.5  # 0.05 * 10 = 0.5

    traits_fast = _traits_with(memory_strength=0.0)  # alpha = 1.0
    mem2 = make_directional_memory()
    update_directional(mem2, dx=0, dy=1, pleasure=10.0, pain=0.0, traits=traits_fast)
    assert mem2.pleasure_tendency[0] == 10.0


def test_update_directional_repeated_application_emas_toward_target() -> None:
    """Repeated identical updates approach the target value, not overshoot."""
    traits = _traits_with(memory_strength=0.5)
    mem = make_directional_memory()
    for _ in range(20):
        update_directional(mem, dx=1, dy=0, pleasure=8.0, pain=0.0, traits=traits)
    # After 20 EMA steps with alpha=0.5, value converges to target
    # (within float32 precision).
    assert float(mem.pleasure_tendency[2]) == pytest.approx(8.0, rel=1e-5)


# ---------------------------------------------------------------------------
# decay_directional
# ---------------------------------------------------------------------------


def test_decay_directional_shrinks_both_tendencies() -> None:
    mem = make_directional_memory()
    mem.pleasure_tendency[:] = 4.0
    mem.pain_tendency[:] = 2.0
    decay_directional(mem, decay_rate=0.25)
    assert np.allclose(mem.pleasure_tendency, 3.0)  # 4 * 0.75
    assert np.allclose(mem.pain_tendency, 1.5)


def test_decay_directional_with_zero_rate_is_noop() -> None:
    mem = make_directional_memory()
    mem.pleasure_tendency[:] = 4.0
    decay_directional(mem, decay_rate=0.0)
    assert np.allclose(mem.pleasure_tendency, 4.0)


def test_decay_directional_drives_tendencies_toward_zero_under_repetition() -> None:
    mem = make_directional_memory()
    mem.pleasure_tendency[:] = 1.0
    for _ in range(50):
        decay_directional(mem, decay_rate=0.1)
    # 1.0 * 0.9^50 ~= 5.15e-3
    assert float(mem.pleasure_tendency.max()) < 1e-2
    assert float(mem.pleasure_tendency.min()) > 0.0  # strictly positive


# ---------------------------------------------------------------------------
# directional_signals_directional
# ---------------------------------------------------------------------------


def test_directional_signals_directional_returns_eight_keys() -> None:
    mem = make_directional_memory()
    out = directional_signals_directional(mem)
    expected = {f"remembered_{kind}_{name}" for name in DIRECTION_NAMES for kind in ("good", "bad")}
    assert set(out) == expected


def test_directional_signals_directional_clamps_negative_pleasure_to_zero() -> None:
    """remembered_good_* should never report a negative value (would
    mean 'anti-pleasure' in a pleasure channel; the harness assumes
    these are non-negative)."""
    mem = make_directional_memory()
    mem.pleasure_tendency[0] = -3.0  # some unusual update history
    mem.pain_tendency[0] = -1.0
    out = directional_signals_directional(mem)
    assert out["remembered_good_north"] == 0.0
    assert out["remembered_bad_north"] == 0.0


def test_directional_signals_directional_passes_through_positive_values() -> None:
    mem = make_directional_memory()
    mem.pleasure_tendency[2] = 1.5  # east
    mem.pain_tendency[3] = 0.7  # west
    out = directional_signals_directional(mem)
    # float32 precision — values round-trip approximately.
    assert out["remembered_good_east"] == pytest.approx(1.5)
    assert out["remembered_bad_west"] == pytest.approx(0.7)
    # Other directions remain zero (exactly).
    assert out["remembered_good_north"] == 0.0
    assert out["remembered_bad_south"] == 0.0


# ---------------------------------------------------------------------------
# Sensor integration — observe() reads DirectionalMemory via dispatch
# ---------------------------------------------------------------------------


def test_observe_dispatches_to_directional_memory() -> None:
    """``sensors.observe`` must read DirectionalMemory tendencies into the
    same Observation fields as ValenceMemory does — uniform interface."""
    world_cfg = WorldConfig(seed=1, width=6, height=6, food_density=0.0, hazard_density=0.0)
    world = build_world(world_cfg)
    body = make_body(
        body_id=1,
        lineage_id=0,
        parent_id=None,
        x=3,
        y=3,
        traits=_traits_with(),
        config=BodyConfig(),
    )
    mem = make_directional_memory()
    mem.pleasure_tendency[2] = 2.0  # east
    mem.pain_tendency[1] = 1.0  # south

    obs = observe(world, body, BodyConfig(), memory=mem)
    assert obs.remembered_good_east == 2.0
    assert obs.remembered_bad_south == 1.0
    # Untouched slots stay zero.
    assert obs.remembered_good_north == 0.0
    assert obs.remembered_good_west == 0.0


# ---------------------------------------------------------------------------
# HHAgent integration — step() updates DirectionalMemory via dispatch
# ---------------------------------------------------------------------------


class _AlwaysEastPolicy:
    """Picks MOVE_EAST when valid, STAY otherwise. Test fixture so the
    agent moves in a known direction every tick."""

    def decide(self, ctx):  # type: ignore[no-untyped-def]
        valid = get_valid_actions(ctx.world, ctx.body, ctx.reproduction_config, ctx.occupied)
        if Action.MOVE_EAST in valid:
            return PolicyDecision(action=Action.MOVE_EAST, breakdown=None)
        return PolicyDecision(action=Action.STAY, breakdown=None)


def test_step_updates_directional_memory_on_move() -> None:
    """An agent moving east each tick must accumulate east-slot updates
    only. The pleasure/pain values are 0 (no breakdown), so the
    tendency stays at 0 — but the dispatch path must complete without
    raising and the agent's memory must remain a DirectionalMemory."""
    world_cfg = WorldConfig(seed=1, width=8, height=4, food_density=0.0, hazard_density=0.0)
    body_cfg = BodyConfig(starting_energy=100.0)
    repro_cfg = ReproductionConfig(min_age=10)
    model = HHModel(
        world_cfg,
        founders=[
            FounderSpec(
                x=1,
                y=1,
                policy_factory=_AlwaysEastPolicy,
                use_memory=True,
                memory_type="directional",
            )
        ],
        body_config=body_cfg,
        reproduction_config=repro_cfg,
    )
    agent: HHAgent = next(a for a in model.agents if isinstance(a, HHAgent))
    assert isinstance(agent.memory, DirectionalMemory)

    # Run a few ticks; agent walks east. No food / hazards exist, so
    # pleasure and pain are 0; the EMA stays at 0 but the dispatch path
    # must complete cleanly.
    for _ in range(3):
        model.step()
    # Tendencies are still zero (no pleasure / pain in this test setup).
    assert float(agent.memory.pleasure_tendency.sum()) == 0.0
    # Position advanced east.
    assert agent.body.x > 1


def test_step_dispatches_decay_for_directional_memory() -> None:
    """``apply_memory_decay`` must shrink DirectionalMemory tendencies
    too (not just ValenceMemory). End-to-end via model.step()."""
    world_cfg = WorldConfig(seed=1, width=6, height=4, food_density=0.0, hazard_density=0.0)
    body_cfg = BodyConfig(starting_energy=100.0)
    repro_cfg = ReproductionConfig(min_age=10)
    traits = _traits_with(memory_strength=0.5, memory_decay_rate=0.5)
    model = HHModel(
        world_cfg,
        founders=[
            FounderSpec(
                x=2,
                y=1,
                policy_factory=_AlwaysEastPolicy,
                use_memory=True,
                memory_type="directional",
                traits_override=traits,
            )
        ],
        body_config=body_cfg,
        reproduction_config=repro_cfg,
    )
    agent: HHAgent = next(a for a in model.agents if isinstance(a, HHAgent))
    assert isinstance(agent.memory, DirectionalMemory)
    # Plant a positive value at an unvisited slot (north) so we can see
    # decay shrink it without the move-east updates fighting back.
    agent.memory.pleasure_tendency[0] = 1.0  # north slot
    model.step()  # decay fires once during step 4
    # Moving east updates the east slot, but the north slot only sees
    # decay: 1.0 * (1 - 0.5) = 0.5.
    assert agent.memory.pleasure_tendency[0] == 0.5


def test_model_with_unknown_memory_type_raises() -> None:
    """FounderSpec rejects a typo at construction time."""
    import pytest

    with pytest.raises(ValueError, match="Unknown memory_type"):
        FounderSpec(
            x=0,
            y=0,
            policy_factory=_AlwaysEastPolicy,
            use_memory=True,
            memory_type="not_a_type",
        )
