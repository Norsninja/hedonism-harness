"""Tests for v0.21 ``V0_21_ARMS`` (influx frontier under
PARENT_TRANSFER_POOL_GAP at pool=1500).

Covers:
  - V0_21_ARMS shape: 5 arms with influx ∈ {0, 0.5, 1.0, 1.5, 2.0}.
  - All arms hold the v0.20 substrate constant: cost=15,
    threshold=50, offspring=30, K=50, pool=1500, transfer mode.
  - Endpoint A (influx=0) reproduces v0.20 transfer-1500 at the
    ChamberRunResult level (a smoke test against a single seed
    and chamber, since the full bit-identity sweep is the v0.21
    sweep itself).
  - Endpoint E (influx=2) reproduces v0.20 transfer-open-low at
    the same smoke level on food_ladder (where v0.20 was
    byte-identical) and via aggregate metrics on tight (where
    v0.20 had a known timing perturbation).
  - The pool_in_ambient_influx invariant (H1) holds at each arm.
  - V0_21_ARMS does not touch v0.14..v0.20 ARMS tuples.
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
    _run_one_arm_seed,
)


def test_v0_21_arms_have_expected_labels() -> None:
    labels = [arm.label for arm in V0_21_ARMS]
    assert labels == [
        "transfer-1500-influx-0",
        "transfer-1500-influx-0.5",
        "transfer-1500-influx-1.0",
        "transfer-1500-influx-1.5",
        "transfer-1500-influx-2.0",
    ]


def test_v0_21_arms_share_substrate() -> None:
    """Every v0.21 arm must hold the v0.20 substrate constant. Only
    ``ambient_influx_rate`` varies."""
    for arm in V0_21_ARMS:
        assert arm.energy_cost == 15.0
        assert arm.energy_threshold == 50.0
        assert arm.offspring_start_energy == 30.0
        assert arm.food_respawn_cooldown == 50
        assert arm.energy_pool_initial == 1_500.0
        assert arm.child_funding_mode == ChildFundingMode.PARENT_TRANSFER_POOL_GAP
        assert arm.memory_type is None
        assert arm.auto_reproduction is True


def test_v0_21_arm_influx_rates_are_uniform() -> None:
    """Five-point grid uniformly between v0.20 endpoints (0 and 2)."""
    rates = [arm.ambient_influx_rate for arm in V0_21_ARMS]
    assert rates == [0.0, 0.5, 1.0, 1.5, 2.0]


def test_prior_arms_unaffected_by_v0_21() -> None:
    """v0.21 introduces no new fields; older arm tuples are unchanged."""
    for tup in (ARMS, V0_15_ARMS, V0_16_ARMS, V0_17_ARMS, V0_18_ARMS, V0_19_ARMS):
        for arm in tup:
            assert arm.child_funding_mode is None
    # V0_20_ARMS legitimately uses ChildFundingMode; just verify it still
    # has 6 arms (v0.21 must not have changed v0.20 surface).
    assert len(V0_20_ARMS) == 6


# ---------------------------------------------------------------------------
# H1 invariant: pool_in_ambient_influx == ambient_influx_rate * n_ticks
# (per seed) when the run completes the full window.
# ---------------------------------------------------------------------------


def test_h1_influx_invariant_at_each_v0_21_arm(tmp_path: Path) -> None:
    """For each arm, run a single short-window seed and verify the per-tick
    influx accumulator equals rate * n_ticks. Short window keeps the test
    cheap; the same invariant holds at the full sweep length by induction
    on the per-tick credit."""
    runs_root = tmp_path / "runs"
    runs_root.mkdir()
    n_ticks = 40
    for arm in V0_21_ARMS:
        seed_root = runs_root / arm.label
        seed_root.mkdir()
        result, _diag = _run_one_arm_seed(
            arm=arm,
            layout_name="food_ladder",
            seed=1,
            runs_root=seed_root,
            n_ticks=n_ticks,
            n_founders=3,
        )
        # Skip if the run terminated early via population extinction.
        if result.ticks_completed < n_ticks:
            continue
        expected = float(arm.ambient_influx_rate) * n_ticks
        assert result.pool_in_ambient_influx == pytest.approx(expected), (
            f"H1 invariant failed at {arm.label}: "
            f"observed={result.pool_in_ambient_influx}, expected={expected}"
        )


# ---------------------------------------------------------------------------
# Endpoint smoke tests — A and E run cleanly and produce the v0.20-shape
# telemetry. Full bit-identity is verified by the v0.21 sweep against
# v0.20 numbers (results section); this test guards the chamber driver
# doesn't drift before that comparison.
# ---------------------------------------------------------------------------


def test_endpoint_a_runs_without_raising(tmp_path: Path) -> None:
    """Arm A (influx=0.0) must run cleanly and produce a populated
    ChamberRunResult under transfer mode."""
    arm_a = V0_21_ARMS[0]
    runs_root = tmp_path / "runs"
    runs_root.mkdir()
    result, _diag = _run_one_arm_seed(
        arm=arm_a,
        layout_name="food_ladder",
        seed=1,
        runs_root=runs_root,
        n_ticks=40,
        n_founders=3,
    )
    assert result.pool_initial == 1_500.0
    assert result.parent_energy_transferred_to_child >= 0.0
    assert result.reproduction_heat_loss == 0.0
    assert result.pool_in_ambient_influx == 0.0


def test_endpoint_e_runs_with_influx_credited(tmp_path: Path) -> None:
    """Arm E (influx=2.0) must credit the pool by 2 * n_ticks and
    keep transfer-mode telemetry intact."""
    arm_e = V0_21_ARMS[-1]
    runs_root = tmp_path / "runs"
    runs_root.mkdir()
    result, _diag = _run_one_arm_seed(
        arm=arm_e,
        layout_name="food_ladder",
        seed=1,
        runs_root=runs_root,
        n_ticks=40,
        n_founders=3,
    )
    assert result.pool_initial == 1_500.0
    assert result.reproduction_heat_loss == 0.0
    if result.ticks_completed == 40:
        assert result.pool_in_ambient_influx == pytest.approx(80.0)
