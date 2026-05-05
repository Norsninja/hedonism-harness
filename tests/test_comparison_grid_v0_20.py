"""Tests for v0.20 ``Arm.child_funding_mode``, V0_20_ARMS, and the
v0.20 telemetry fields on ``RunDiagnostics`` and ``ArmCellAggregate``.

Mirrors the v0.19 test_comparison_grid_energy_pool.py pattern.
"""

from __future__ import annotations

import json
from pathlib import Path

from hedonism_harness.core.config import ChildFundingMode
from hedonism_harness.experiments.comparison_grid import (
    ARMS,
    V0_15_ARMS,
    V0_16_ARMS,
    V0_17_ARMS,
    V0_18_ARMS,
    V0_19_ARMS,
    V0_20_ARMS,
    Arm,
    ArmCellAggregate,
    _aggregate,
    _gradient_policy_factory,
    _read_run_diagnostics,
    _run_one_arm_seed,
)


def test_arm_child_funding_mode_defaults_to_none_on_all_prior_arms() -> None:
    """All v0.14-v0.19 arms have no funding-mode override; v0.20 bit-
    identity contract holds via the ReproductionConfig default
    (POOL_FULL)."""
    for arm in ARMS + V0_15_ARMS + V0_16_ARMS + V0_17_ARMS + V0_18_ARMS + V0_19_ARMS:
        assert arm.child_funding_mode is None


def test_v0_20_arms_have_expected_labels() -> None:
    labels = [arm.label for arm in V0_20_ARMS]
    assert labels == [
        "pool-full-1500",
        "transfer-1500",
        "pool-full-open-low",
        "transfer-open-low",
        "pool-full-3000",
        "transfer-3000",
    ]


def test_v0_20_arm_pairs_match_on_substrate_and_pool() -> None:
    """Each (POOL_FULL, TRANSFER) pair holds every substrate field
    constant. The only variation across the pair is child_funding_mode."""
    pairs = [
        ("pool-full-1500", "transfer-1500"),
        ("pool-full-open-low", "transfer-open-low"),
        ("pool-full-3000", "transfer-3000"),
    ]
    by_label = {arm.label: arm for arm in V0_20_ARMS}
    for full_label, transfer_label in pairs:
        full = by_label[full_label]
        trans = by_label[transfer_label]
        assert full.child_funding_mode == ChildFundingMode.POOL_FULL
        assert trans.child_funding_mode == ChildFundingMode.PARENT_TRANSFER_POOL_GAP
        assert full.energy_cost == trans.energy_cost == 15.0
        assert full.energy_threshold == trans.energy_threshold == 50.0
        assert full.offspring_start_energy == trans.offspring_start_energy == 30.0
        assert full.food_respawn_cooldown == trans.food_respawn_cooldown == 50
        assert full.energy_pool_initial == trans.energy_pool_initial
        assert full.ambient_influx_rate == trans.ambient_influx_rate
        assert full.policy_factory is trans.policy_factory


def test_v0_20_brackets_anchor_on_v0_19_regimes() -> None:
    by_label = {arm.label: arm for arm in V0_20_ARMS}
    # closed-1500 — v0.19's binding regime
    assert by_label["pool-full-1500"].energy_pool_initial == 1_500.0
    assert by_label["pool-full-1500"].ambient_influx_rate == 0.0
    # open-low (influx=2) — v0.19's partial-rescue regime
    assert by_label["pool-full-open-low"].energy_pool_initial == 1_500.0
    assert by_label["pool-full-open-low"].ambient_influx_rate == 2.0
    # closed-3000 — v0.19's null regime (negative control)
    assert by_label["pool-full-3000"].energy_pool_initial == 3_000.0
    assert by_label["pool-full-3000"].ambient_influx_rate == 0.0


# ---------------------------------------------------------------------------
# RunDiagnostics counts BirthDeniedParentEnergy from JSONL
# ---------------------------------------------------------------------------


def _write_events(path: Path, rows: list[dict]) -> None:
    with path.open("w") as f:
        for row in rows:
            f.write(json.dumps(row) + "\n")


def test_birth_denied_parent_energy_counted_from_jsonl(tmp_path: Path) -> None:
    events_path = tmp_path / "events.jsonl"
    _write_events(
        events_path,
        [
            {
                "tick": 5,
                "type": "BirthDeniedParentEnergy",
                "event": {"parent_id": 1, "x": 0, "y": 0, "tick": 5},
            },
            {
                "tick": 6,
                "type": "BirthDeniedParentEnergy",
                "event": {"parent_id": 2, "x": 1, "y": 0, "tick": 6},
            },
            {"tick": 7, "type": "AgentBorn", "event": {"agent_id": 100, "parent_id": 1}},
        ],
    )
    diag = _read_run_diagnostics(events_path)
    assert diag.total_births_blocked_by_parent_energy == 2


def test_birth_denied_parent_energy_zero_when_absent(tmp_path: Path) -> None:
    events_path = tmp_path / "events.jsonl"
    _write_events(
        events_path,
        [
            {"tick": 5, "type": "AgentBorn", "event": {"agent_id": 100, "parent_id": 1}},
        ],
    )
    diag = _read_run_diagnostics(events_path)
    assert diag.total_births_blocked_by_parent_energy == 0


# ---------------------------------------------------------------------------
# ArmCellAggregate v0.20 fields default and aggregator sums
# ---------------------------------------------------------------------------


def test_arm_cell_aggregate_v0_20_fields_default_zero() -> None:
    agg = ArmCellAggregate(
        arm_label="probe",
        layout_name="food_ladder",
        n_seeds=4,
        total_births=10,
        seeds_with_any_births=4,
        births_after_tick_50=3,
        max_population_end=4,
        seeds_with_survivors=4,
        still_tick_fraction=0.9,
        total_food_events=50,
        total_hazard_entries=0,
        total_starvation_deaths=5,
        total_reproduction_requests=10,
        total_distinct_parents=8,
        total_post_birth_lifespan_ticks=400,
        total_grandchildren_count=2,
        total_food_respawn_events=10,
        food_value_default=20.0,
    )
    assert agg.total_reproduction_heat_loss == 0.0
    assert agg.total_parent_energy_transferred_to_child == 0.0
    assert agg.total_births_blocked_by_parent_energy == 0


def test_aggregate_sums_v0_20_telemetry_across_seeds(tmp_path: Path) -> None:
    """End-to-end: a TRANSFER arm with 2 seeds populates the v0.20
    accumulator fields and sums per-flow counters."""
    arm = Arm(
        label="probe-transfer",
        policy_factory=_gradient_policy_factory,
        auto_reproduction=True,
        energy_cost=15.0,
        energy_threshold=50.0,
        offspring_start_energy=30.0,
        food_respawn_cooldown=50,
        energy_pool_initial=3_000.0,
        ambient_influx_rate=0.0,
        child_funding_mode=ChildFundingMode.PARENT_TRANSFER_POOL_GAP,
    )
    runs_root = tmp_path / "runs"
    runs_root.mkdir()
    pairs = []
    for seed in (1, 2):
        seed_root = runs_root / f"s{seed}"
        seed_root.mkdir()
        pair = _run_one_arm_seed(
            arm=arm,
            layout_name="food_ladder",
            seed=seed,
            runs_root=seed_root,
            n_ticks=40,
            n_founders=3,
        )
        pairs.append(pair)

    agg = _aggregate(arm, "food_ladder", pairs)
    # Transfer-mode invariant: heat_loss is zero; transferred is non-zero
    # (assuming any births happened).
    assert agg.total_reproduction_heat_loss == 0.0
    assert agg.total_parent_energy_transferred_to_child == sum(
        r.parent_energy_transferred_to_child for r, _ in pairs
    )
    # H4 invariant at the aggregate level under TRANSFER mode.
    assert agg.total_parent_energy_transferred_to_child + agg.total_pool_out_child_startup == (
        agg.total_births * arm.offspring_start_energy
    )


def test_aggregate_sums_v0_20_telemetry_under_pool_full(tmp_path: Path) -> None:
    """Under POOL_FULL the aggregate's heat_loss is positive and the
    transfer accumulator is zero."""
    arm = Arm(
        label="probe-pool-full",
        policy_factory=_gradient_policy_factory,
        auto_reproduction=True,
        energy_cost=15.0,
        energy_threshold=50.0,
        offspring_start_energy=30.0,
        food_respawn_cooldown=50,
        energy_pool_initial=3_000.0,
        ambient_influx_rate=0.0,
        child_funding_mode=ChildFundingMode.POOL_FULL,
    )
    runs_root = tmp_path / "runs"
    runs_root.mkdir()
    pairs = []
    for seed in (1, 2):
        seed_root = runs_root / f"s{seed}"
        seed_root.mkdir()
        pair = _run_one_arm_seed(
            arm=arm,
            layout_name="food_ladder",
            seed=seed,
            runs_root=seed_root,
            n_ticks=40,
            n_founders=3,
        )
        pairs.append(pair)

    agg = _aggregate(arm, "food_ladder", pairs)
    assert agg.total_parent_energy_transferred_to_child == 0.0
    assert agg.total_reproduction_heat_loss == agg.total_births * arm.energy_cost
    assert agg.total_pool_out_child_startup == agg.total_births * arm.offspring_start_energy
    assert agg.total_births_blocked_by_parent_energy == 0
