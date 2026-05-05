"""Tests for v0.17 offspring-energy overrides on Arm + grandchildren telemetry.

The v0.17 axis adds an optional ``offspring_start_energy`` field on
``Arm``; ``None`` (default) preserves v0.14/v0.15/v0.16 bit-identity by
falling back to ``tuned_reproduction_config``'s default of ``30.0``.
Non-None values flow into ``tuned_reproduction_config``.

The bit-identity contract for arm ``start-30`` vs v0.16 cost-15 is
verified end-to-end by the v0.17 sweep itself; these tests cover the
wiring layer plus the new ``total_grandchildren_count`` telemetry.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from hedonism_harness.experiments.comparison_grid import (
    V0_15_ARMS,
    V0_16_ARMS,
    V0_17_ARMS,
    Arm,
    _gradient_policy_factory,
    _read_run_diagnostics,
    _run_one_arm_seed,
)
from hedonism_harness.experiments.repro_configs import tuned_reproduction_config


def test_arm_offspring_start_energy_default_to_none() -> None:
    """Existing v0.15 / v0.16 arms have no offspring-energy override; the
    v0.14/v0.15/v0.16 bit-identity contract holds via the
    ``tuned_reproduction_config`` default of 30.0."""
    for arm in V0_15_ARMS + V0_16_ARMS:
        assert arm.offspring_start_energy is None


def test_v0_17_arms_carry_explicit_offspring_energy() -> None:
    """V0_17_ARMS spans offspring_start_energy ∈ {30, 60, 100} at
    cost-15 economics."""
    labels = [arm.label for arm in V0_17_ARMS]
    assert labels == ["start-30", "start-60", "start-100"]
    assert [arm.offspring_start_energy for arm in V0_17_ARMS] == [30.0, 60.0, 100.0]
    for arm in V0_17_ARMS:
        assert arm.energy_cost == 15.0
        assert arm.energy_threshold == 50.0
        assert arm.memory_type is None  # single-arm: no scalar memory.


def test_explicit_offspring_energy_runs_to_completion(tmp_path: Path) -> None:
    """Arm with offspring_start_energy=80 runs without raising and
    produces a deterministic ChamberRunResult. The override flows
    through tuned_reproduction_config; that factory's contract is
    asserted in test_offspring_start_energy_bounds_validated."""
    arm = Arm(
        label="probe-offspring",
        policy_factory=_gradient_policy_factory,
        auto_reproduction=True,
        energy_cost=15.0,
        energy_threshold=50.0,
        offspring_start_energy=80.0,
    )
    runs_root = tmp_path / "runs"
    runs_root.mkdir()
    result, _diag = _run_one_arm_seed(
        arm=arm,
        layout_name="food_ladder",
        seed=1,
        runs_root=runs_root,
        n_ticks=3,
        n_founders=2,
    )
    assert result.population_end >= 0


def test_offspring_start_energy_bounds_validated() -> None:
    """tuned_reproduction_config enforces [0.0, 100.0] on offspring_start_energy."""
    with pytest.raises(ValueError, match="offspring_start_energy"):
        tuned_reproduction_config(
            energy_threshold=50.0, energy_cost=15.0, offspring_start_energy=-1.0
        )
    with pytest.raises(ValueError, match="offspring_start_energy"):
        tuned_reproduction_config(
            energy_threshold=50.0, energy_cost=15.0, offspring_start_energy=101.0
        )


def test_tuned_reproduction_config_propagates_offspring_start_energy() -> None:
    """Direct contract: the factory output carries the override value."""
    cfg = tuned_reproduction_config(
        energy_threshold=50.0, energy_cost=15.0, offspring_start_energy=60.0
    )
    assert cfg.offspring_start_energy == 60.0
    # Defaults preserved when omitted.
    cfg_default = tuned_reproduction_config(energy_threshold=50.0, energy_cost=15.0)
    assert cfg_default.offspring_start_energy == 30.0


def test_arm_default_omits_offspring_start_energy_in_factory_call(tmp_path: Path) -> None:
    """An Arm with offspring_start_energy=None must not pass the field
    through to ``tuned_reproduction_config``; the factory default (30.0)
    is what produces v0.7..v0.16 bit-identity. Smoke-checked via a
    short run that completes without error."""
    arm = Arm(
        label="probe-default-offspring",
        policy_factory=_gradient_policy_factory,
        auto_reproduction=True,
        energy_cost=15.0,
        energy_threshold=50.0,
        # offspring_start_energy=None implicitly.
    )
    runs_root = tmp_path / "runs"
    runs_root.mkdir()
    result, _diag = _run_one_arm_seed(
        arm=arm,
        layout_name="food_ladder",
        seed=1,
        runs_root=runs_root,
        n_ticks=3,
        n_founders=2,
    )
    assert result.population_start == 2


# ---------------------------------------------------------------------------
# Grandchildren telemetry — synthetic events.jsonl unit test.
# ---------------------------------------------------------------------------


def _write_events(path: Path, rows: list[dict]) -> None:
    with path.open("w") as f:
        for row in rows:
            f.write(json.dumps(row) + "\n")


def test_grandchildren_count_zero_when_only_first_generation(tmp_path: Path) -> None:
    """Founders 1, 2 each produce one child (101, 102). No second-generation
    births; total_grandchildren_count = 0."""
    events_path = tmp_path / "events.jsonl"
    _write_events(
        events_path,
        [
            {"tick": 5, "type": "AgentBorn", "event": {"agent_id": 101, "parent_id": 1}},
            {"tick": 6, "type": "AgentBorn", "event": {"agent_id": 102, "parent_id": 2}},
        ],
    )
    diag = _read_run_diagnostics(events_path)
    assert diag.total_grandchildren_count == 0


def test_grandchildren_count_counts_second_generation(tmp_path: Path) -> None:
    """Founder 1 → 101 → 1001 (grandchild). Founder 2 → 102 (no grandchild).
    total_grandchildren_count = 1."""
    events_path = tmp_path / "events.jsonl"
    _write_events(
        events_path,
        [
            {"tick": 5, "type": "AgentBorn", "event": {"agent_id": 101, "parent_id": 1}},
            {"tick": 6, "type": "AgentBorn", "event": {"agent_id": 102, "parent_id": 2}},
            {"tick": 60, "type": "AgentBorn", "event": {"agent_id": 1001, "parent_id": 101}},
        ],
    )
    diag = _read_run_diagnostics(events_path)
    assert diag.total_grandchildren_count == 1


def test_grandchildren_count_handles_great_grandchildren(tmp_path: Path) -> None:
    """Three-generation lineage: 1 → 101 → 1001 → 10001. Both 1001 (parent
    101 was born) and 10001 (parent 1001 was born) count. Total = 2."""
    events_path = tmp_path / "events.jsonl"
    _write_events(
        events_path,
        [
            {"tick": 5, "type": "AgentBorn", "event": {"agent_id": 101, "parent_id": 1}},
            {"tick": 60, "type": "AgentBorn", "event": {"agent_id": 1001, "parent_id": 101}},
            {"tick": 120, "type": "AgentBorn", "event": {"agent_id": 10001, "parent_id": 1001}},
        ],
    )
    diag = _read_run_diagnostics(events_path)
    assert diag.total_grandchildren_count == 2


def test_grandchildren_count_zero_when_no_births(tmp_path: Path) -> None:
    """No AgentBorn events at all → grandchildren count is 0 (not undefined)."""
    events_path = tmp_path / "events.jsonl"
    _write_events(
        events_path,
        [
            {"tick": 1, "type": "AgentStayed", "event": {"agent_id": 1}},
            {"tick": 2, "type": "AgentMoved", "event": {"agent_id": 1}},
        ],
    )
    diag = _read_run_diagnostics(events_path)
    assert diag.total_grandchildren_count == 0
    assert diag.total_distinct_parents == 0


def test_arm_cell_aggregate_mean_grandchildren_per_seed() -> None:
    """``mean_grandchildren_per_seed`` = total / n_seeds (per-seed denominator,
    distinct from ``mean_births_per_parent``'s parent denominator)."""
    from hedonism_harness.experiments.comparison_grid import ArmCellAggregate

    agg = ArmCellAggregate(
        arm_label="probe",
        layout_name="food_ladder",
        n_seeds=8,
        total_births=40,
        seeds_with_any_births=8,
        births_after_tick_50=4,
        max_population_end=3,
        seeds_with_survivors=4,
        still_tick_fraction=0.9,
        total_food_events=174,
        total_hazard_entries=0,
        total_starvation_deaths=0,
        total_reproduction_requests=40,
        total_distinct_parents=20,
        total_post_birth_lifespan_ticks=1600,
        total_grandchildren_count=12,
    )
    assert agg.mean_grandchildren_per_seed == pytest.approx(12 / 8)
    assert agg.mean_births_per_parent == pytest.approx(40 / 20)


def test_arm_cell_aggregate_mean_grandchildren_per_seed_zero_seeds() -> None:
    """Empty aggregate (n_seeds=0) returns 0.0 instead of dividing by zero."""
    from hedonism_harness.experiments.comparison_grid import ArmCellAggregate

    agg = ArmCellAggregate(
        arm_label="probe",
        layout_name="food_ladder",
        n_seeds=0,
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
    )
    assert agg.mean_grandchildren_per_seed == 0.0
