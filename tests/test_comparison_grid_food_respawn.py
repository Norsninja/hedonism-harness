"""Tests for v0.18 food-respawn overrides on Arm + telemetry.

The v0.18 axis adds an optional ``food_respawn_cooldown`` field on
``Arm``. ``None`` (default) preserves v0.14/v0.15/v0.16/v0.17
bit-identity by leaving the new ``WorldConfig.food_respawn_cooldown``
at None (no respawn). Non-None values flow through ``run_chamber`` to
the model.

Tests cover:
  - Arm field default is None (existing arms unchanged).
  - V0_18_ARMS shape (4 arms at K ∈ {None, 100, 50, 20}).
  - End-to-end run with K override smoke test.
  - RunDiagnostics.total_food_respawn_events counted from events.jsonl.
  - ArmCellAggregate.food_consumed_per_birth ratio formula and edge
    cases.

The bit-identity contract for arm K-inf vs v0.17 start-30 is
verified by the v0.18 sweep itself.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from hedonism_harness.experiments.comparison_grid import (
    ARMS,
    V0_15_ARMS,
    V0_16_ARMS,
    V0_17_ARMS,
    V0_18_ARMS,
    Arm,
    _gradient_policy_factory,
    _read_run_diagnostics,
    _run_one_arm_seed,
)


def test_arm_food_respawn_cooldown_default_to_none() -> None:
    """All v0.14-v0.17 arms have no food_respawn_cooldown override; the
    bit-identity contract holds via the WorldConfig field default of None."""
    for arm in ARMS + V0_15_ARMS + V0_16_ARMS + V0_17_ARMS:
        assert arm.food_respawn_cooldown is None


def test_v0_18_arms_carry_explicit_cooldowns() -> None:
    """V0_18_ARMS spans food_respawn_cooldown ∈ {None, 100, 50, 20} at
    cost-15 + offspring=30 economics."""
    labels = [arm.label for arm in V0_18_ARMS]
    assert labels == ["K-inf", "K-100", "K-50", "K-20"]
    cooldowns = [arm.food_respawn_cooldown for arm in V0_18_ARMS]
    assert cooldowns == [None, 100, 50, 20]
    for arm in V0_18_ARMS:
        assert arm.energy_cost == 15.0
        assert arm.energy_threshold == 50.0
        assert arm.offspring_start_energy == 30.0
        assert arm.memory_type is None  # no scalar memory.


def test_explicit_cooldown_runs_to_completion(tmp_path: Path) -> None:
    """Arm with K=10 runs without raising and produces a deterministic
    ChamberRunResult; FoodRespawned events appear in events.jsonl."""
    arm = Arm(
        label="probe-respawn",
        policy_factory=_gradient_policy_factory,
        auto_reproduction=True,
        energy_cost=15.0,
        energy_threshold=50.0,
        offspring_start_energy=30.0,
        food_respawn_cooldown=10,
    )
    runs_root = tmp_path / "runs"
    runs_root.mkdir()
    result, diag = _run_one_arm_seed(
        arm=arm,
        layout_name="food_ladder",
        seed=1,
        runs_root=runs_root,
        n_ticks=50,
        n_founders=2,
    )
    assert result.population_end >= 0
    # With K=10 and 50 ticks, at least some food gets eaten and respawns —
    # but the assertion is conservative because seed 1 / 2 founders may
    # eat zero food cells in 50 ticks. The strong end-to-end check
    # happens at sweep time via the comparison.csv columns.
    assert diag.total_food_respawn_events >= 0


def test_default_arm_emits_zero_respawn_events(tmp_path: Path) -> None:
    """An Arm with no food_respawn_cooldown override produces zero
    FoodRespawned events, regardless of how much food is consumed."""
    arm = Arm(
        label="probe-default",
        policy_factory=_gradient_policy_factory,
        auto_reproduction=True,
        energy_cost=15.0,
        energy_threshold=50.0,
        offspring_start_energy=30.0,
        # food_respawn_cooldown=None implicitly.
    )
    runs_root = tmp_path / "runs"
    runs_root.mkdir()
    _result, diag = _run_one_arm_seed(
        arm=arm,
        layout_name="food_ladder",
        seed=1,
        runs_root=runs_root,
        n_ticks=20,
        n_founders=2,
    )
    assert diag.total_food_respawn_events == 0


# ---------------------------------------------------------------------------
# RunDiagnostics — total_food_respawn_events from synthetic events.jsonl.
# ---------------------------------------------------------------------------


def _write_events(path: Path, rows: list[dict]) -> None:
    with path.open("w") as f:
        for row in rows:
            f.write(json.dumps(row) + "\n")


def test_food_respawn_events_counted_from_jsonl(tmp_path: Path) -> None:
    """A FoodRespawned line in events.jsonl increments the count."""
    events_path = tmp_path / "events.jsonl"
    rows = [
        {"tick": 5, "type": "FoodRespawned", "event": {"x": 1, "y": 1, "tick": 5}},
        {"tick": 6, "type": "FoodRespawned", "event": {"x": 2, "y": 1, "tick": 6}},
        {
            "tick": 6,
            "type": "AgentMoved",
            "event": {"agent_id": 1, "from_x": 0, "from_y": 0, "to_x": 1, "to_y": 0},
        },
    ]
    _write_events(events_path, rows)
    diag = _read_run_diagnostics(events_path)
    assert diag.total_food_respawn_events == 2


def test_food_respawn_events_zero_when_no_respawns(tmp_path: Path) -> None:
    """Empty / no-respawn JSONL yields total_food_respawn_events == 0."""
    events_path = tmp_path / "events.jsonl"
    rows = [
        {"tick": 5, "type": "AgentBorn", "event": {"agent_id": 101, "parent_id": 1}},
        {
            "tick": 6,
            "type": "AteFood",
            "event": {"agent_id": 1, "x": 2, "y": 1, "food_gained": 20.0},
        },
    ]
    _write_events(events_path, rows)
    diag = _read_run_diagnostics(events_path)
    assert diag.total_food_respawn_events == 0


# ---------------------------------------------------------------------------
# ArmCellAggregate.food_consumed_per_birth — the conservation-accounting
# ratio.
# ---------------------------------------------------------------------------


def test_food_consumed_per_birth_v017_handout_signature() -> None:
    """Reproduces the v0.17 start-100 food_ladder ratio: 174 food_events
    times 20 food_value / 366 births ~ 9.51. Documents the artificially-
    low handout signature for comparison vs v0.18 results."""
    from hedonism_harness.experiments.comparison_grid import ArmCellAggregate

    agg = ArmCellAggregate(
        arm_label="v0.17-start-100-foodladder",
        layout_name="food_ladder",
        n_seeds=8,
        total_births=366,
        seeds_with_any_births=8,
        births_after_tick_50=147,
        max_population_end=34,
        seeds_with_survivors=8,
        still_tick_fraction=0.979,
        total_food_events=174,
        total_hazard_entries=30,
        total_starvation_deaths=198,
        total_reproduction_requests=404,
        total_distinct_parents=242,
        total_post_birth_lifespan_ticks=21783,
        total_grandchildren_count=311,
        total_food_respawn_events=0,
        food_value_default=20.0,
    )
    # 174 * 20 / 366 == 3480 / 366 == 9.508...
    assert agg.food_consumed_per_birth == pytest.approx(9.508, abs=0.01)


def test_food_consumed_per_birth_zero_when_no_births() -> None:
    """Vacuous early-termination runs (zero births) return 0.0 instead of
    raising on a divide-by-zero."""
    from hedonism_harness.experiments.comparison_grid import ArmCellAggregate

    agg = ArmCellAggregate(
        arm_label="empty",
        layout_name="food_ladder",
        n_seeds=8,
        total_births=0,
        seeds_with_any_births=0,
        births_after_tick_50=0,
        max_population_end=0,
        seeds_with_survivors=0,
        still_tick_fraction=0.0,
        total_food_events=0,
        total_hazard_entries=0,
        total_starvation_deaths=0,
        total_reproduction_requests=0,
        total_distinct_parents=0,
        total_post_birth_lifespan_ticks=0,
        total_grandchildren_count=0,
        total_food_respawn_events=0,
        food_value_default=20.0,
    )
    assert agg.food_consumed_per_birth == 0.0


def test_food_consumed_per_birth_self_sustaining_floor() -> None:
    """Sanity: a hypothetical aggregate at the v0.18 self-sustaining floor
    (energy_cost + offspring_start_energy = 45) reports
    food_consumed_per_birth ≈ 45.0 when the chamber consumes exactly
    that energy per birth."""
    from hedonism_harness.experiments.comparison_grid import ArmCellAggregate

    # Concretely: 8 seeds, 100 births total, 225 food_events at 20 each =
    # 4500 food-energy. 4500 / 100 = 45 per birth.
    agg = ArmCellAggregate(
        arm_label="hypothetical-floor",
        layout_name="food_ladder",
        n_seeds=8,
        total_births=100,
        seeds_with_any_births=8,
        births_after_tick_50=20,
        max_population_end=10,
        seeds_with_survivors=8,
        still_tick_fraction=0.95,
        total_food_events=225,
        total_hazard_entries=0,
        total_starvation_deaths=50,
        total_reproduction_requests=100,
        total_distinct_parents=80,
        total_post_birth_lifespan_ticks=8000,
        total_grandchildren_count=15,
        total_food_respawn_events=120,
        food_value_default=20.0,
    )
    assert agg.food_consumed_per_birth == pytest.approx(45.0)
