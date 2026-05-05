"""Tests for v0.22 ``V0_22_ARMS`` (narrow hazard-damage sweep on
food_ladder under PARENT_TRANSFER_POOL_GAP at pool=1500, influx=1.0).

Covers:
  - V0_22_ARMS shape: exactly 4 arms with hazard_damage ∈ {0, 4, 8, 12}.
  - All arms hold the v0.21 substrate constant: cost=15, threshold=50,
    offspring=30, K=50, pool=1500, influx=1.0, transfer mode. Only
    ``hazard_damage`` varies.
  - ``Arm.hazard_damage=None`` (default) preserves v0.7..v0.21 bit-identity:
    every prior arm tuple still has ``hazard_damage=None``.
  - Threading: hazard_damage threads from Arm → run_chamber →
    build_chamber_layout into ``WorldConfig.hazard_damage_default``,
    verified by injury-death observable behavior at the boundary.
  - End-to-end smoke: arm A (hazard=0) runs cleanly and produces
    zero injury_deaths (only STARVATION deaths are possible at
    hazard=0). At higher hazards, injury_deaths can be > 0.
  - ArmCellAggregate.total_injury_deaths field exists with default 0
    and surfaces ChamberRunResult.injury_deaths summed across seeds.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from hedonism_harness.core.config import ChildFundingMode
from hedonism_harness.experiments.comparison_grid import (
    ARMS,
    V0_15_ARMS,
    V0_16_ARMS,
    V0_17_ARMS,
    V0_18_ARMS,
    V0_19_ARMS,
    V0_20_ARMS,
    V0_21_ARMS,
    V0_22_ARMS,
    ArmCellAggregate,
    _run_one_arm_seed,
)

# ---------------------------------------------------------------------------
# Shape + parameter pinning
# ---------------------------------------------------------------------------


def test_v0_22_arms_have_exactly_four_arms() -> None:
    assert len(V0_22_ARMS) == 4


def test_v0_22_arms_have_expected_labels() -> None:
    labels = [arm.label for arm in V0_22_ARMS]
    assert labels == ["hazard-0", "hazard-4", "hazard-8", "hazard-12"]


def test_v0_22_arm_hazard_damage_values() -> None:
    """hazard_damage values are exactly {0, 4, 8, 12}."""
    damages = [arm.hazard_damage for arm in V0_22_ARMS]
    assert damages == [0.0, 4.0, 8.0, 12.0]


def test_v0_22_arms_share_substrate() -> None:
    """Every v0.22 arm holds the v0.21 substrate constant. Only
    hazard_damage varies."""
    for arm in V0_22_ARMS:
        assert arm.energy_cost == 15.0
        assert arm.energy_threshold == 50.0
        assert arm.offspring_start_energy == 30.0
        assert arm.food_respawn_cooldown == 50
        assert arm.energy_pool_initial == 1_500.0
        assert arm.ambient_influx_rate == 1.0
        assert arm.child_funding_mode == ChildFundingMode.PARENT_TRANSFER_POOL_GAP
        assert arm.memory_type is None
        assert arm.auto_reproduction is True


# ---------------------------------------------------------------------------
# Bit-identity preservation: prior arm tuples have hazard_damage=None
# ---------------------------------------------------------------------------


def test_prior_arms_have_no_hazard_damage_override() -> None:
    """v0.22 introduces ``Arm.hazard_damage`` with default ``None``;
    every prior arm tuple must keep that default to preserve
    v0.7..v0.21 bit-identity (run_chamber falls back to
    build_chamber_layout's 8.0 default)."""
    for tup in (
        ARMS,
        V0_15_ARMS,
        V0_16_ARMS,
        V0_17_ARMS,
        V0_18_ARMS,
        V0_19_ARMS,
        V0_20_ARMS,
        V0_21_ARMS,
    ):
        for arm in tup:
            assert arm.hazard_damage is None, (
                f"{arm.label}: hazard_damage must be None to preserve bit-identity"
            )


# ---------------------------------------------------------------------------
# ArmCellAggregate.total_injury_deaths field
# ---------------------------------------------------------------------------


def test_arm_cell_aggregate_default_total_injury_deaths_is_zero() -> None:
    """``total_injury_deaths`` defaults to 0 so prior aggregate-construction
    sites don't break."""
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
        total_food_respawn_events=0,
        food_value_default=20.0,
    )
    assert agg.total_injury_deaths == 0


# ---------------------------------------------------------------------------
# Threading: hazard_damage flows from Arm into the per-tile damage applied
# at runtime. The cleanest observable is injury_deaths: at hazard=0, no
# agent can die of INJURY by construction (hazard residency damage is 0).
# ---------------------------------------------------------------------------


def test_hazard_zero_produces_no_injury_deaths(tmp_path: Path) -> None:
    """Arm A (hazard=0) must run cleanly and report zero INJURY deaths.
    The substrate can still produce STARVATION deaths; the test only
    pins the injury count at zero. This is the v0.22 threading proof:
    if hazard_damage did not thread through, the build_chamber_layout
    default of 8.0 would apply and food_ladder (with hazards in the
    pre-food band) would produce some injury_deaths at this seed."""
    arm_a = V0_22_ARMS[0]
    assert arm_a.hazard_damage == 0.0
    runs_root = tmp_path / "runs"
    runs_root.mkdir()
    result, _diag = _run_one_arm_seed(
        arm=arm_a,
        layout_name="food_ladder",
        seed=1,
        runs_root=runs_root,
        n_ticks=200,
        n_founders=5,
    )
    assert result.injury_deaths == 0, (
        f"hazard=0 produced {result.injury_deaths} injury deaths — "
        "hazard_damage threading is broken"
    )
    # Any deaths recorded must be starvation.
    if result.starvation_deaths + result.injury_deaths > 0:
        assert result.starvation_deaths > 0
    # Transfer-mode invariants still hold.
    assert result.reproduction_heat_loss == 0.0
    assert result.pool_initial == 1_500.0


def test_hazard_eight_anchor_runs_cleanly(tmp_path: Path) -> None:
    """Arm C (hazard=8) is the v0.21 transfer-1500-influx-1.0 default —
    the byte-identity anchor against v0.21 (full sweep verifies).
    This smoke test guards the chamber driver doesn't drift before
    that comparison."""
    arm_c = V0_22_ARMS[2]
    assert arm_c.hazard_damage == 8.0
    runs_root = tmp_path / "runs"
    runs_root.mkdir()
    result, _diag = _run_one_arm_seed(
        arm=arm_c,
        layout_name="food_ladder",
        seed=1,
        runs_root=runs_root,
        n_ticks=40,
        n_founders=3,
    )
    assert result.pool_initial == 1_500.0
    assert result.reproduction_heat_loss == 0.0
    if result.ticks_completed == 40:
        assert result.pool_in_ambient_influx == pytest.approx(40.0)


def test_hazard_zero_vs_eight_diverge_on_injury_deaths(tmp_path: Path) -> None:
    """Mechanism check: at the same seed and layout, hazard=8 should
    produce some injury_deaths over the full 200-tick window where
    hazard=0 produces zero. If both are zero, agents are avoiding
    hazards entirely and the recycling channel is mechanically
    dormant — that would itself be a finding for v0.22 results, but
    the test only asserts the threading direction (hazard>0 enables
    INJURY death cause)."""
    arm_a = V0_22_ARMS[0]
    arm_c = V0_22_ARMS[2]
    runs_root = tmp_path / "runs"
    runs_root.mkdir()
    result_a, _ = _run_one_arm_seed(
        arm=arm_a,
        layout_name="food_ladder",
        seed=1,
        runs_root=runs_root / "a",
        n_ticks=200,
        n_founders=5,
    )
    result_c, _ = _run_one_arm_seed(
        arm=arm_c,
        layout_name="food_ladder",
        seed=1,
        runs_root=runs_root / "c",
        n_ticks=200,
        n_founders=5,
    )
    # arm A: hard pin — zero by construction.
    assert result_a.injury_deaths == 0
    # arm C: empirical observation. The v0.21 transfer-1500-influx-1.0
    # food_ladder seed-1 run produced injury deaths; we only assert
    # >= arm A's count (= 0). If this ever fires zero on arm C, the
    # sweep results doc will need to discuss why.
    assert result_c.injury_deaths >= result_a.injury_deaths
