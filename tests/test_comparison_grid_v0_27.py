"""Tests for v0.27 ``V0_27_ARMS`` (avoidance-weight frontier on both
chambers at fixed hazard=8, influx=1.0, transfer/pool=1500).

Covers:
  - V0_27_ARMS shape: exactly 5 arms covering
    hazard_avoidance_weight ∈ {0.0, 0.25, 0.5, 0.75, 1.0}.
  - Substrate fixed across all arms (cost=15, threshold=50,
    offspring=30, K=50, pool=1500, transfer mode, influx=1.0,
    hazard=8); only hazard_avoidance_weight varies.
  - Prior arm tuples (V0_19/20/21/22/23/25/26) keep their fields
    (no v0.27 mutation).
  - Anchor substrate identity: V0_27 weight=0.0 / weight=1.0 cells
    match V0_26 hzd8-avd0.0 / hzd8-avd1.0 substrates.
  - H5 mechanical sanity: weight=0.0 on food_ladder produces some
    injury deaths (cull-tax presence at hzd=8 with no avoidance).
  - H11 mechanical sanity: weight=1.0 on food_ladder has fewer
    hazard entries than weight=0.0 (avoidance routing functional).
"""

from __future__ import annotations

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
    V0_21_ARMS,
    V0_22_ARMS,
    V0_23_ARMS,
    V0_25_ARMS,
    V0_26_ARMS,
    V0_27_ARMS,
    _run_one_arm_seed,
)

EXPECTED_WEIGHTS: tuple[float, ...] = (0.0, 0.25, 0.5, 0.75, 1.0)
EXPECTED_LABELS: tuple[str, ...] = (
    "hzd8-avd0.00",
    "hzd8-avd0.25",
    "hzd8-avd0.50",
    "hzd8-avd0.75",
    "hzd8-avd1.00",
)


# ---------------------------------------------------------------------------
# Shape + parameter pinning
# ---------------------------------------------------------------------------


def test_v0_27_arms_have_exactly_five_arms() -> None:
    assert len(V0_27_ARMS) == 5


def test_v0_27_arms_have_expected_labels() -> None:
    labels = tuple(arm.label for arm in V0_27_ARMS)
    assert labels == EXPECTED_LABELS


def test_v0_27_arm_avoidance_weights() -> None:
    """hazard_avoidance_weight grids through {0.0, 0.25, 0.5, 0.75, 1.0}
    in declaration order."""
    weights = tuple(arm.hazard_avoidance_weight for arm in V0_27_ARMS)
    assert weights == EXPECTED_WEIGHTS


def test_v0_27_arm_hazard_pinned_to_eight() -> None:
    """Every v0.27 arm holds hazard_damage=8.0 (only weight varies)."""
    for arm in V0_27_ARMS:
        assert arm.hazard_damage == 8.0


def test_v0_27_arms_share_substrate() -> None:
    """Every v0.27 arm holds the v0.21 substrate constant. Only
    hazard_avoidance_weight varies; influx fixed at 1.0."""
    for arm in V0_27_ARMS:
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
# Anchor substrate identity against v0.26
# ---------------------------------------------------------------------------


def _find_arm(arms: tuple, label: str):
    for arm in arms:
        if arm.label == label:
            return arm
    msg = f"arm with label {label!r} not found"
    raise AssertionError(msg)


def test_v0_27_weight_zero_substrate_matches_v0_26_invisible() -> None:
    """V0_27 hzd8-avd0.00 substrate matches V0_26 hzd8-avd0.0 on every
    field. Halt-condition pin under H12."""
    v27 = _find_arm(V0_27_ARMS, "hzd8-avd0.00")
    v26 = _find_arm(V0_26_ARMS, "hzd8-avd0.0")
    assert v27.hazard_damage == v26.hazard_damage == 8.0
    assert v27.hazard_avoidance_weight == v26.hazard_avoidance_weight == 0.0
    assert v27.ambient_influx_rate == v26.ambient_influx_rate == 1.0
    assert v27.energy_pool_initial == v26.energy_pool_initial == 1_500.0
    assert v27.energy_cost == v26.energy_cost == 15.0
    assert v27.offspring_start_energy == v26.offspring_start_energy == 30.0
    assert v27.child_funding_mode == v26.child_funding_mode


def test_v0_27_weight_one_substrate_matches_v0_26_coupled() -> None:
    """V0_27 hzd8-avd1.00 substrate matches V0_26 hzd8-avd1.0."""
    v27 = _find_arm(V0_27_ARMS, "hzd8-avd1.00")
    v26 = _find_arm(V0_26_ARMS, "hzd8-avd1.0")
    assert v27.hazard_damage == v26.hazard_damage == 8.0
    assert v27.hazard_avoidance_weight == v26.hazard_avoidance_weight == 1.0
    assert v27.ambient_influx_rate == v26.ambient_influx_rate == 1.0


# ---------------------------------------------------------------------------
# Prior arms unchanged
# ---------------------------------------------------------------------------


def test_pre_v0_26_arms_still_have_no_avoidance_weight_override() -> None:
    """v0.7..v0.25 arm tuples must still have hazard_avoidance_weight=None
    after v0.27 adds V0_27_ARMS. Pure addition; no mutation of priors."""
    for tup in (
        ARMS,
        V0_15_ARMS,
        V0_16_ARMS,
        V0_17_ARMS,
        V0_18_ARMS,
        V0_19_ARMS,
        V0_20_ARMS,
        V0_21_ARMS,
        V0_22_ARMS,
        V0_23_ARMS,
        V0_25_ARMS,
    ):
        for arm in tup:
            assert arm.hazard_avoidance_weight is None, (
                f"{arm.label}: hazard_avoidance_weight must be None on pre-v0.26 arms"
            )


def test_v0_26_arms_unchanged_by_v0_27() -> None:
    """V0_26_ARMS (4 arms, the 2x2 grid) is purely v0.26 territory;
    v0.27 must not mutate its structure."""
    assert len(V0_26_ARMS) == 4
    weights = tuple(arm.hazard_avoidance_weight for arm in V0_26_ARMS)
    assert weights == (1.0, 0.0, 1.0, 0.0)
    damages = tuple(arm.hazard_damage for arm in V0_26_ARMS)
    assert damages == (8.0, 8.0, 0.0, 0.0)


# ---------------------------------------------------------------------------
# H5 mechanical sanity: weight=0.0 on food_ladder produces injury deaths
# ---------------------------------------------------------------------------


def test_v0_27_weight_zero_food_ladder_produces_injury_deaths(tmp_path: Path) -> None:
    """At weight=0.0 with hazard=8 on food_ladder, agents enter the
    pre-food band freely and accumulate injury deaths. Aggregated
    across 3 seeds at n_ticks=120 to clear single-seed noise.
    Mechanical sanity for the routing-side seam."""
    arm_a = _find_arm(V0_27_ARMS, "hzd8-avd0.00")
    runs_root = tmp_path / "runs"
    runs_root.mkdir()
    total_injuries = 0
    for seed in (1, 2, 3):
        result, _ = _run_one_arm_seed(
            arm=arm_a,
            layout_name="food_ladder",
            seed=seed,
            runs_root=runs_root,
            n_ticks=120,
            n_founders=5,
        )
        total_injuries += result.injury_deaths
    # Aggregated across 3 seeds at hazard=8, weight=0 on food_ladder we
    # expect a positive injury count (the v0.26 sweep saw inj=40 across
    # 8 seeds x 200 ticks; 3 seeds x 120 ticks should produce > 0).
    assert total_injuries > 0


# ---------------------------------------------------------------------------
# H11 mechanical sanity: weight=1.0 has fewer hazard entries than weight=0.0
# ---------------------------------------------------------------------------


def test_v0_27_avoidance_reduces_hazard_entries_food_ladder(tmp_path: Path) -> None:
    """At hazard=8 on food_ladder, increasing weight from 0.0 to 1.0
    monotonically reduces hazard entries (direct routing observable).
    Aggregated across 3 seeds at n_ticks=120 to clear single-seed noise."""
    arm_a = _find_arm(V0_27_ARMS, "hzd8-avd0.00")
    arm_e = _find_arm(V0_27_ARMS, "hzd8-avd1.00")
    runs_root = tmp_path / "runs"
    runs_root.mkdir()
    (runs_root / "w0").mkdir()
    (runs_root / "w1").mkdir()
    w0_total = 0
    w1_total = 0
    for seed in (1, 2, 3):
        r0, _ = _run_one_arm_seed(
            arm=arm_a,
            layout_name="food_ladder",
            seed=seed,
            runs_root=runs_root / "w0",
            n_ticks=120,
            n_founders=5,
        )
        r1, _ = _run_one_arm_seed(
            arm=arm_e,
            layout_name="food_ladder",
            seed=seed,
            runs_root=runs_root / "w1",
            n_ticks=120,
            n_founders=5,
        )
        w0_total += r0.hazard_entries
        w1_total += r1.hazard_entries
    # Avoidance routing is functional: more weight → fewer entries.
    assert w1_total < w0_total
