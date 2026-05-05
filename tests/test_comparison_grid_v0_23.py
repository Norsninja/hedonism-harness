"""Tests for v0.23 ``V0_23_ARMS`` (hazard-zero influx frontier on both
chambers under PARENT_TRANSFER_POOL_GAP at pool=1500).

Covers:
  - V0_23_ARMS shape: exactly 5 arms with influx ∈ {0, 0.5, 1.0, 1.5, 2.0},
    hazard_damage=0.0 on every arm.
  - All arms hold the v0.21 substrate constant: cost=15, threshold=50,
    offspring=30, K=50, pool=1500, transfer mode. Only ``ambient_influx_rate``
    varies; ``hazard_damage`` is fixed at 0.
  - Prior arm tuples (V0_19/V0_20/V0_21/V0_22) keep their hazard_damage
    settings — V0_22 still has its hazard sweep, others still default to
    None. v0.23 is purely additive.
  - End-to-end smoke: arm A (hazard=0, influx=0) on food_ladder runs
    cleanly and produces zero injury_deaths (H5 hard pin).
  - H6 hard pin: hazard=0 implies pool_in_death_residual == 0.
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
    _run_one_arm_seed,
)

# ---------------------------------------------------------------------------
# Shape + parameter pinning
# ---------------------------------------------------------------------------


def test_v0_23_arms_have_exactly_five_arms() -> None:
    assert len(V0_23_ARMS) == 5


def test_v0_23_arms_have_expected_labels() -> None:
    labels = [arm.label for arm in V0_23_ARMS]
    assert labels == [
        "transfer-1500-hzd0-influx-0",
        "transfer-1500-hzd0-influx-0.5",
        "transfer-1500-hzd0-influx-1.0",
        "transfer-1500-hzd0-influx-1.5",
        "transfer-1500-hzd0-influx-2.0",
    ]


def test_v0_23_arm_influx_values() -> None:
    """ambient_influx_rate values are exactly {0, 0.5, 1.0, 1.5, 2.0}."""
    rates = [arm.ambient_influx_rate for arm in V0_23_ARMS]
    assert rates == [0.0, 0.5, 1.0, 1.5, 2.0]


def test_v0_23_arms_all_have_hazard_damage_zero() -> None:
    """Every v0.23 arm pins hazard_damage=0.0 — the v0.23 experimental
    control."""
    for arm in V0_23_ARMS:
        assert arm.hazard_damage == 0.0


def test_v0_23_arms_share_substrate() -> None:
    """Every v0.23 arm holds the v0.21 substrate constant. Only
    ambient_influx_rate varies; hazard_damage is fixed at 0."""
    for arm in V0_23_ARMS:
        assert arm.energy_cost == 15.0
        assert arm.energy_threshold == 50.0
        assert arm.offspring_start_energy == 30.0
        assert arm.food_respawn_cooldown == 50
        assert arm.energy_pool_initial == 1_500.0
        assert arm.child_funding_mode == ChildFundingMode.PARENT_TRANSFER_POOL_GAP
        assert arm.memory_type is None
        assert arm.auto_reproduction is True
        assert arm.hazard_damage == 0.0


# ---------------------------------------------------------------------------
# Prior arms unchanged (v0.23 is purely additive)
# ---------------------------------------------------------------------------


def test_pre_v0_22_arms_have_no_hazard_damage_override() -> None:
    """v0.7..v0.21 arm tuples must keep hazard_damage=None to preserve
    bit-identity (run_chamber falls back to build_chamber_layout's 8.0
    default). v0.22 sweeps {0, 4, 8, 12} and v0.23 pins 0 — those are
    expected non-None values."""
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


def test_v0_22_arms_unchanged() -> None:
    """V0_22_ARMS still has its hazard sweep {0, 4, 8, 12}; v0.23 must
    not perturb the v0.22 surface."""
    assert len(V0_22_ARMS) == 4
    damages = [arm.hazard_damage for arm in V0_22_ARMS]
    assert damages == [0.0, 4.0, 8.0, 12.0]


# ---------------------------------------------------------------------------
# H5/H6 hard pins on a representative arm: hazard_damage=0 produces zero
# injury deaths AND zero pool_in_death_residual. This is the threading
# proof carried forward from v0.22 — every v0.23 arm inherits the pin.
# ---------------------------------------------------------------------------


def test_v0_23_arm_a_hazard_zero_produces_no_injury_deaths(tmp_path: Path) -> None:
    """Arm A (hazard=0, influx=0) on food_ladder must run cleanly and
    report zero INJURY deaths (H5). The substrate can still produce
    STARVATION deaths; only the injury count is hard-pinned."""
    arm_a = V0_23_ARMS[0]
    assert arm_a.hazard_damage == 0.0
    assert arm_a.ambient_influx_rate == 0.0
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
        f"hazard=0 produced {result.injury_deaths} injury deaths — H5 violated"
    )
    # H6: hazard=0 implies STARVATION-only deaths, which credit zero
    # body energy back to the pool.
    assert result.pool_in_death_residual == 0.0, (
        f"hazard=0 produced residual={result.pool_in_death_residual} — H6 violated"
    )
    # Transfer-mode invariants still hold.
    assert result.reproduction_heat_loss == 0.0
    assert result.pool_initial == 1_500.0


def test_v0_23_arm_c_food_ladder_smoke(tmp_path: Path) -> None:
    """Arm C (hazard=0, influx=1.0) on food_ladder is the v0.22 hazard-0
    byte-identity anchor; smoke-test that it runs without raising and
    preserves the H5/H6 pins. Full byte-identity verified by the sweep."""
    arm_c = V0_23_ARMS[2]
    assert arm_c.hazard_damage == 0.0
    assert arm_c.ambient_influx_rate == 1.0
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
    assert result.injury_deaths == 0
    assert result.pool_in_death_residual == 0.0


def test_v0_23_arm_a_tight_gradient_smoke(tmp_path: Path) -> None:
    """Arm A on tight_gradient at hazard=0 is a v0.23 first observation
    (no prior anchor). Smoke-test that the chamber driver runs cleanly
    and the H5/H6 pins hold; the run may extinct early under the
    closed-pool no-influx-no-recycling regime, but H5/H6 must hold
    for whatever ticks executed."""
    arm_a = V0_23_ARMS[0]
    runs_root = tmp_path / "runs"
    runs_root.mkdir()
    result, _diag = _run_one_arm_seed(
        arm=arm_a,
        layout_name="tight_gradient",
        seed=1,
        runs_root=runs_root,
        n_ticks=40,
        n_founders=3,
    )
    assert result.pool_initial == 1_500.0
    assert result.reproduction_heat_loss == 0.0
    assert result.injury_deaths == 0
    assert result.pool_in_death_residual == 0.0
