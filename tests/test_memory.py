"""Tests for ``core/memory.py`` — ValenceMemory + sensor wiring (SPEC §13)."""

from __future__ import annotations

import dataclasses

import numpy as np
import pytest
from hypothesis import given
from hypothesis import strategies as st

from hedonism_harness.core.body import make_body
from hedonism_harness.core.config import BodyConfig, WorldConfig
from hedonism_harness.core.memory import (
    ValenceMemory,
    alpha_for_strength,
    decay_all,
    directional_signals,
    make_memory,
    update_at,
)
from hedonism_harness.core.sensors import observe
from hedonism_harness.core.traits import TraitConfig, random_traits
from hedonism_harness.core.world import build_world


def _traits_with(memory_strength: float, memory_decay_rate: float, sensor_radius: int = 3):
    base = random_traits(TraitConfig(), np.random.default_rng(0))
    return dataclasses.replace(
        base,
        memory_strength=memory_strength,
        memory_decay_rate=memory_decay_rate,
        sensor_radius=sensor_radius,
    )


# ---------------------------------------------------------------------------
# make_memory
# ---------------------------------------------------------------------------


def test_make_memory_zero_initialized() -> None:
    mem = make_memory(8, 6)
    assert mem.pleasure_ema.shape == (8, 6)
    assert mem.pain_ema.shape == (8, 6)
    assert mem.visits.shape == (8, 6)
    assert mem.last_seen_tick.shape == (8, 6)
    assert mem.pleasure_ema.dtype == np.float32
    assert mem.pain_ema.dtype == np.float32
    assert mem.visits.dtype == np.uint32
    assert mem.last_seen_tick.dtype == np.int32
    assert float(mem.pleasure_ema.sum()) == 0.0
    assert float(mem.pain_ema.sum()) == 0.0
    assert int(mem.visits.sum()) == 0
    assert int((mem.last_seen_tick == -1).sum()) == 8 * 6


# ---------------------------------------------------------------------------
# alpha_for_strength
# ---------------------------------------------------------------------------


def test_alpha_for_strength_is_inversely_related_to_memory_strength() -> None:
    assert alpha_for_strength(0.0) > alpha_for_strength(0.5)
    assert alpha_for_strength(0.5) > alpha_for_strength(1.0)


def test_alpha_for_strength_has_floor() -> None:
    """Even at memory_strength=1, alpha must be > 0 so memory still updates at all."""
    assert alpha_for_strength(1.0) > 0.0


@given(strength=st.floats(min_value=0.0, max_value=1.0, allow_nan=False))
def test_alpha_for_strength_is_in_unit_interval(strength: float) -> None:
    a = alpha_for_strength(strength)
    assert 0.0 <= a <= 1.0


# ---------------------------------------------------------------------------
# update_at
# ---------------------------------------------------------------------------


def test_update_at_increments_visits_and_records_tick() -> None:
    mem = make_memory(5, 5)
    traits = _traits_with(memory_strength=0.5, memory_decay_rate=0.0)
    update_at(mem, 2, 2, pleasure=1.0, pain=0.0, traits=traits, tick=7)
    assert int(mem.visits[2, 2]) == 1
    assert int(mem.last_seen_tick[2, 2]) == 7


def test_update_at_blends_old_and_new_via_ema() -> None:
    mem = make_memory(3, 3)
    traits = _traits_with(memory_strength=0.0, memory_decay_rate=0.0)
    # alpha at memory_strength=0 is 1.0 -> immediate overwrite.
    update_at(mem, 1, 1, pleasure=10.0, pain=0.0, traits=traits, tick=0)
    assert float(mem.pleasure_ema[1, 1]) == pytest.approx(10.0)

    update_at(mem, 1, 1, pleasure=0.0, pain=0.0, traits=traits, tick=1)
    assert float(mem.pleasure_ema[1, 1]) == pytest.approx(0.0)


def test_update_at_with_high_memory_strength_changes_slowly() -> None:
    mem = make_memory(3, 3)
    traits = _traits_with(memory_strength=0.95, memory_decay_rate=0.0)
    # alpha is small -> new readings barely change the EMA.
    update_at(mem, 1, 1, pleasure=10.0, pain=0.0, traits=traits, tick=0)
    first = float(mem.pleasure_ema[1, 1])
    update_at(mem, 1, 1, pleasure=0.0, pain=0.0, traits=traits, tick=1)
    second = float(mem.pleasure_ema[1, 1])
    assert second < first
    assert second > 0.5 * first  # less than half of the value was bled off


def test_update_at_only_touches_target_cell() -> None:
    mem = make_memory(4, 4)
    traits = _traits_with(memory_strength=0.0, memory_decay_rate=0.0)
    update_at(mem, 1, 1, pleasure=10.0, pain=5.0, traits=traits, tick=0)
    # Every other cell should still be zero.
    mask = np.ones_like(mem.pleasure_ema, dtype=bool)
    mask[1, 1] = False
    assert float(mem.pleasure_ema[mask].sum()) == 0.0
    assert float(mem.pain_ema[mask].sum()) == 0.0


# ---------------------------------------------------------------------------
# decay_all
# ---------------------------------------------------------------------------


def test_decay_all_shrinks_emas() -> None:
    mem = make_memory(3, 3)
    mem.pleasure_ema[1, 1] = 10.0
    mem.pain_ema[1, 1] = 4.0
    decay_all(mem, decay_rate=0.1)
    assert float(mem.pleasure_ema[1, 1]) == pytest.approx(9.0)
    assert float(mem.pain_ema[1, 1]) == pytest.approx(3.6)


def test_decay_all_with_zero_rate_is_noop() -> None:
    mem = make_memory(3, 3)
    mem.pleasure_ema[1, 1] = 10.0
    decay_all(mem, decay_rate=0.0)
    assert float(mem.pleasure_ema[1, 1]) == 10.0


def test_decay_all_does_not_touch_visits_or_tick() -> None:
    mem = make_memory(3, 3)
    mem.pleasure_ema[1, 1] = 10.0
    mem.visits[1, 1] = 5
    mem.last_seen_tick[1, 1] = 42
    decay_all(mem, decay_rate=0.5)
    assert int(mem.visits[1, 1]) == 5
    assert int(mem.last_seen_tick[1, 1]) == 42


# ---------------------------------------------------------------------------
# directional_signals
# ---------------------------------------------------------------------------


def test_directional_signals_pleasure_north() -> None:
    mem = make_memory(7, 7)
    mem.pleasure_ema[3, 5] = 4.0  # 2 cells north of (3, 3)
    out = directional_signals(mem, 3, 3, radius=3)
    assert out["remembered_good_north"] == pytest.approx(4.0 / 2)
    assert out["remembered_good_south"] == 0.0


def test_directional_signals_decays_with_distance() -> None:
    mem = make_memory(7, 7)
    mem.pleasure_ema[3, 4] = 6.0  # distance 1 north
    mem.pleasure_ema[3, 6] = 9.0  # distance 3 north
    out = directional_signals(mem, 3, 3, radius=5)
    assert out["remembered_good_north"] == pytest.approx(6.0 + 9.0 / 3)


def test_directional_signals_respects_world_edge() -> None:
    mem = make_memory(4, 4)
    out = directional_signals(mem, 3, 3, radius=10)  # asks past the edge
    for v in out.values():
        assert v == 0.0


def test_directional_signals_pain_separate_from_pleasure() -> None:
    mem = make_memory(7, 7)
    mem.pain_ema[5, 3] = 2.0  # 2 cells east
    out = directional_signals(mem, 3, 3, radius=3)
    assert out["remembered_bad_east"] == pytest.approx(2.0 / 2)
    assert out["remembered_good_east"] == 0.0


# ---------------------------------------------------------------------------
# Sensor wiring
# ---------------------------------------------------------------------------


def test_observe_reads_memory_when_provided() -> None:
    body_config = BodyConfig()
    cfg = WorldConfig(seed=1, width=11, height=11, food_density=0.0, hazard_density=0.0)
    world = build_world(cfg)
    traits = _traits_with(memory_strength=0.0, memory_decay_rate=0.0, sensor_radius=3)
    body = make_body(
        body_id=1, lineage_id=1, parent_id=None, x=5, y=5, traits=traits, config=body_config
    )
    mem = make_memory(world.width, world.height)
    mem.pleasure_ema[5, 7] = 4.0  # 2 cells north -> remembered_good_north = 2.0

    obs_no_mem = observe(world, body, body_config, memory=None)
    obs_mem = observe(world, body, body_config, memory=mem)

    assert obs_no_mem.remembered_good_north == 0.0
    assert obs_mem.remembered_good_north == pytest.approx(2.0)


def test_observe_with_unknown_memory_type_returns_zero_signals() -> None:
    """Belt-and-suspenders: passing some non-ValenceMemory object still scores 0."""
    body_config = BodyConfig()
    cfg = WorldConfig(seed=1, width=8, height=8, food_density=0.0, hazard_density=0.0)
    world = build_world(cfg)
    traits = _traits_with(memory_strength=0.0, memory_decay_rate=0.0)
    body = make_body(
        body_id=1, lineage_id=1, parent_id=None, x=3, y=3, traits=traits, config=body_config
    )
    obs = observe(world, body, body_config, memory="not a memory")  # type: ignore[arg-type]
    assert obs.remembered_good_north == 0.0
    assert obs.remembered_bad_east == 0.0


# ---------------------------------------------------------------------------
# Integration with policies
# ---------------------------------------------------------------------------


def test_memory_hedonism_policy_can_be_constructed_and_decide() -> None:
    """Smoke: MemoryHedonismPolicy is a Policy and runs end-to-end with memory."""
    from hedonism_harness.core.actions import get_valid_actions
    from hedonism_harness.core.config import ActionConfig
    from hedonism_harness.policies import MemoryHedonismPolicy
    from hedonism_harness.policies.base import DecisionContext

    body_config = BodyConfig()
    action_config = ActionConfig()
    cfg = WorldConfig(seed=1, width=8, height=8, food_density=0.0, hazard_density=0.0)
    world = build_world(cfg)
    traits = _traits_with(memory_strength=0.5, memory_decay_rate=0.05)
    body = make_body(
        body_id=1, lineage_id=1, parent_id=None, x=3, y=3, traits=traits, config=body_config
    )
    mem = make_memory(world.width, world.height)
    obs = observe(world, body, body_config, memory=mem)
    ctx = DecisionContext(
        world=world,
        body=body,
        observation=obs,
        rng=np.random.default_rng(0),
        body_config=body_config,
        action_config=action_config,
        memory=mem,
    )
    decision = MemoryHedonismPolicy(exploration_noise=0.0).decide(ctx)
    assert decision.action in set(get_valid_actions(world, body))
    assert decision.breakdown is not None
    assert isinstance(mem, ValenceMemory)
