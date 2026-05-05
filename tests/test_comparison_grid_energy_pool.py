"""Tests for v0.19 ``Arm`` energy-pool overrides + telemetry plumbing.

The v0.19 axis adds two optional fields on ``Arm``:
  - ``energy_pool_initial: float | None``
  - ``ambient_influx_rate: float | None``

``None`` (default) on either preserves v0.14/v0.15/v0.16/v0.17/v0.18
bit-identity by leaving the pool path off.

Tests cover:
  - Existing arms (V0_15/16/17/18) carry no pool override.
  - V0_19_ARMS shape: 7 arms, expected labels and pool / influx values.
  - End-to-end run with override; ChamberRunResult carries pool fields.
  - RunDiagnostics counts PoolRespawnDenied + PoolBirthDenied from
    synthetic events.jsonl.
  - ArmCellAggregate sums per-flow pool counters across seeds.
"""

from __future__ import annotations

import json
from pathlib import Path

from hedonism_harness.experiments.comparison_grid import (
    ARMS,
    V0_15_ARMS,
    V0_16_ARMS,
    V0_17_ARMS,
    V0_18_ARMS,
    V0_19_ARMS,
    Arm,
    ArmCellAggregate,
    _aggregate,
    _gradient_policy_factory,
    _read_run_diagnostics,
    _run_one_arm_seed,
)


def test_arm_energy_pool_defaults_to_none_on_all_prior_arms() -> None:
    """All v0.14-v0.18 arms have no pool override; v0.19 bit-identity
    contract holds via the WorldConfig defaults (None / 0.0)."""
    for arm in ARMS + V0_15_ARMS + V0_16_ARMS + V0_17_ARMS + V0_18_ARMS:
        assert arm.energy_pool_initial is None
        assert arm.ambient_influx_rate is None


def test_v0_19_arms_have_expected_labels() -> None:
    labels = [arm.label for arm in V0_19_ARMS]
    assert labels == [
        "inf-pool",
        "closed-500",
        "closed-1500",
        "closed-3000",
        "closed-1500-K100",
        "open-low",
        "open-equiv",
    ]


def test_v0_19_inf_pool_arm_is_no_pool_arm() -> None:
    """The reference arm has no pool — preserves v0.18 K-50 bit-
    identity."""
    inf = next(arm for arm in V0_19_ARMS if arm.label == "inf-pool")
    assert inf.energy_pool_initial is None
    assert inf.ambient_influx_rate is None
    assert inf.food_respawn_cooldown == 50


def test_v0_19_closed_arms_have_finite_pool_no_influx() -> None:
    """Brackets anchor on the empirically-observed per-RUN drain of
    ~2,200 energy at v0.18 K-50 tight_gradient: 500 starves early,
    1500 sits near demand, 3000 has comfortable margin."""
    closed_500 = next(arm for arm in V0_19_ARMS if arm.label == "closed-500")
    closed_1500 = next(arm for arm in V0_19_ARMS if arm.label == "closed-1500")
    closed_3000 = next(arm for arm in V0_19_ARMS if arm.label == "closed-3000")
    assert closed_500.energy_pool_initial == 500.0
    assert closed_1500.energy_pool_initial == 1_500.0
    assert closed_3000.energy_pool_initial == 3_000.0
    for arm in (closed_500, closed_1500, closed_3000):
        assert arm.ambient_influx_rate == 0.0
        assert arm.food_respawn_cooldown == 50


def test_v0_19_k100_hedge_arm_has_higher_cooldown() -> None:
    hedge = next(arm for arm in V0_19_ARMS if arm.label == "closed-1500-K100")
    assert hedge.food_respawn_cooldown == 100
    assert hedge.energy_pool_initial == 1_500.0
    assert hedge.ambient_influx_rate == 0.0


def test_v0_19_open_arms_have_influx() -> None:
    """Influx rates anchored on v0.18 K-50 productive per-RUN flux
    (~7 energy/tick): open-low at 2/tick (well below productive
    demand of ~11/tick), open-equiv at 7/tick (matches v0.18
    productive flux per run)."""
    low = next(arm for arm in V0_19_ARMS if arm.label == "open-low")
    eq = next(arm for arm in V0_19_ARMS if arm.label == "open-equiv")
    assert low.ambient_influx_rate == 2.0
    assert eq.ambient_influx_rate == 7.0
    for arm in (low, eq):
        assert arm.energy_pool_initial == 1_500.0
        assert arm.food_respawn_cooldown == 50


def test_v0_19_arms_share_substrate_economics() -> None:
    """All v0.19 arms hold cost-15, threshold-50, offspring=30 fixed."""
    for arm in V0_19_ARMS:
        assert arm.energy_cost == 15.0
        assert arm.energy_threshold == 50.0
        assert arm.offspring_start_energy == 30.0
        assert arm.memory_type is None


def test_explicit_pool_arm_runs_to_completion(tmp_path: Path) -> None:
    """Smoke: a closed-pool arm runs without raising and emits
    ChamberRunResult with non-None pool telemetry."""
    arm = Arm(
        label="probe-pool",
        policy_factory=_gradient_policy_factory,
        auto_reproduction=True,
        energy_cost=15.0,
        energy_threshold=50.0,
        offspring_start_energy=30.0,
        food_respawn_cooldown=10,
        energy_pool_initial=1_000.0,
        ambient_influx_rate=0.0,
    )
    runs_root = tmp_path / "runs"
    runs_root.mkdir()
    result, diag = _run_one_arm_seed(
        arm=arm,
        layout_name="food_ladder",
        seed=1,
        runs_root=runs_root,
        n_ticks=30,
        n_founders=2,
    )
    assert result.population_end >= 0
    assert result.pool_initial == 1_000.0
    assert result.pool_min is not None
    assert result.pool_max is not None
    assert result.pool_end is not None
    # Diagnostics counters at least exist.
    assert diag.total_pool_respawn_denied >= 0
    assert diag.total_pool_birth_denied >= 0


def test_default_arm_emits_no_pool_telemetry(tmp_path: Path) -> None:
    """An Arm with no pool override produces ChamberRunResult.pool_*
    fields all None / 0, mirroring the v0.7..v0.18 default path."""
    arm = Arm(
        label="probe-default",
        policy_factory=_gradient_policy_factory,
        auto_reproduction=True,
        energy_cost=15.0,
        energy_threshold=50.0,
        offspring_start_energy=30.0,
        # No pool overrides — falls back to WorldConfig defaults.
    )
    runs_root = tmp_path / "runs"
    runs_root.mkdir()
    result, diag = _run_one_arm_seed(
        arm=arm,
        layout_name="food_ladder",
        seed=1,
        runs_root=runs_root,
        n_ticks=20,
        n_founders=2,
    )
    assert result.pool_initial is None
    assert result.pool_min is None
    assert result.pool_max is None
    assert result.pool_end is None
    assert result.pool_out_respawn == 0.0
    assert result.pool_out_child_startup == 0.0
    assert diag.total_pool_respawn_denied == 0
    assert diag.total_pool_birth_denied == 0


# ---------------------------------------------------------------------------
# RunDiagnostics — count PoolRespawnDenied / PoolBirthDenied from JSONL.
# ---------------------------------------------------------------------------


def _write_events(path: Path, rows: list[dict]) -> None:
    with path.open("w") as f:
        for row in rows:
            f.write(json.dumps(row) + "\n")


def test_pool_respawn_denied_events_counted_from_jsonl(tmp_path: Path) -> None:
    events_path = tmp_path / "events.jsonl"
    _write_events(
        events_path,
        [
            {"tick": 5, "type": "PoolRespawnDenied", "event": {"x": 1, "y": 1, "tick": 5}},
            {"tick": 6, "type": "PoolRespawnDenied", "event": {"x": 2, "y": 1, "tick": 6}},
            {"tick": 7, "type": "FoodRespawned", "event": {"x": 3, "y": 1, "tick": 7}},
        ],
    )
    diag = _read_run_diagnostics(events_path)
    assert diag.total_pool_respawn_denied == 2
    assert diag.total_food_respawn_events == 1
    assert diag.total_pool_birth_denied == 0


def test_pool_birth_denied_events_counted_from_jsonl(tmp_path: Path) -> None:
    events_path = tmp_path / "events.jsonl"
    _write_events(
        events_path,
        [
            {
                "tick": 5,
                "type": "PoolBirthDenied",
                "event": {"parent_id": 1, "x": 0, "y": 0, "tick": 5},
            },
            {
                "tick": 6,
                "type": "PoolBirthDenied",
                "event": {"parent_id": 2, "x": 1, "y": 1, "tick": 6},
            },
            {
                "tick": 7,
                "type": "PoolBirthDenied",
                "event": {"parent_id": 3, "x": 2, "y": 0, "tick": 7},
            },
            {"tick": 5, "type": "AgentBorn", "event": {"agent_id": 100, "parent_id": 1}},
        ],
    )
    diag = _read_run_diagnostics(events_path)
    assert diag.total_pool_birth_denied == 3


def test_pool_events_zero_when_absent(tmp_path: Path) -> None:
    events_path = tmp_path / "events.jsonl"
    _write_events(
        events_path,
        [
            {"tick": 5, "type": "AgentBorn", "event": {"agent_id": 100, "parent_id": 1}},
            {
                "tick": 6,
                "type": "AteFood",
                "event": {"agent_id": 1, "x": 2, "y": 1, "food_gained": 20.0},
            },
        ],
    )
    diag = _read_run_diagnostics(events_path)
    assert diag.total_pool_respawn_denied == 0
    assert diag.total_pool_birth_denied == 0


# ---------------------------------------------------------------------------
# ArmCellAggregate — pool fields default to safe values; aggregator sums.
# ---------------------------------------------------------------------------


def _aggregate_field_default_check() -> ArmCellAggregate:
    """Construct an aggregate without v0.19 pool fields; assert defaults."""
    return ArmCellAggregate(
        arm_label="probe",
        layout_name="food_ladder",
        n_seeds=8,
        total_births=10,
        seeds_with_any_births=8,
        births_after_tick_50=3,
        max_population_end=4,
        seeds_with_survivors=6,
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


def test_arm_cell_aggregate_pool_defaults_zero_or_none() -> None:
    agg = _aggregate_field_default_check()
    assert agg.total_pool_respawn_denied == 0
    assert agg.total_pool_birth_denied == 0
    assert agg.total_pool_out_respawn == 0.0
    assert agg.total_pool_out_child_startup == 0.0
    assert agg.total_pool_in_death_residual == 0.0
    assert agg.total_pool_in_ambient_influx == 0.0
    assert agg.pool_min_observed is None
    assert agg.pool_max_observed is None
    assert agg.mean_pool_end is None


def test_aggregate_sums_pool_telemetry_across_seeds(tmp_path: Path) -> None:
    """End-to-end aggregator path: a finite-pool arm with 2 seeds
    populates pool fields and sums per-flow counters."""
    arm = Arm(
        label="probe-pool-sum",
        policy_factory=_gradient_policy_factory,
        auto_reproduction=True,
        energy_cost=15.0,
        energy_threshold=50.0,
        offspring_start_energy=30.0,
        food_respawn_cooldown=10,
        energy_pool_initial=1_000.0,
        ambient_influx_rate=10.0,
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
            n_ticks=20,
            n_founders=2,
        )
        pairs.append(pair)

    agg = _aggregate(arm, "food_ladder", pairs)
    # Per-flow counters at the aggregate level equal the sum across
    # seeds — basic sanity that the aggregator wires the new fields.
    assert agg.total_pool_in_ambient_influx == sum(r.pool_in_ambient_influx for r, _ in pairs)
    assert agg.total_pool_out_respawn == sum(r.pool_out_respawn for r, _ in pairs)
    assert agg.total_pool_out_child_startup == sum(r.pool_out_child_startup for r, _ in pairs)
    assert agg.pool_min_observed is not None
    assert agg.pool_max_observed is not None
    assert agg.mean_pool_end is not None
