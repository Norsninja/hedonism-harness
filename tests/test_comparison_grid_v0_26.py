"""Tests for v0.26 ``V0_26_ARMS`` (perception-vs-damage decoupling 2x2
on both chambers under PARENT_TRANSFER_POOL_GAP at pool=1500, influx=1.0).

Covers:
  - V0_26_ARMS shape: exactly 4 arms covering hazard ∈ {0, 8} x
    hazard_avoidance_weight ∈ {0.0, 1.0}.
  - Substrate fixed across all arms (cost=15, threshold=50, offspring=30,
    K=50, pool=1500, transfer mode, influx=1.0); only hazard_damage
    and hazard_avoidance_weight vary.
  - Prior arm tuples (V0_19/20/21/22/23/25) keep hazard_avoidance_weight=None
    to preserve bit-identity.
  - Anchor substrate identity: V0_26 hazard=8 weight=1.0 substrate is
    identical to V0_25 transfer-1500-hzd8-influx-1.0 minus the new
    hazard_avoidance_weight field; same for hazard=0 cells against V0_25
    hzd0-influx-1.0.
  - H14 GradientPolicy seam: weight=1.0 default is no-op (covered in
    test_gradient_policy.py).
  - H12 phantom ≡ no-hazard: arms C and D produce identical aggregates
    on a smoke-test seed.
  - H5 hard pin: hazard_damage=0 cells produce 0 injury deaths regardless
    of avoidance weight.
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
    _run_one_arm_seed,
)

EXPECTED_HAZARDS: tuple[float, ...] = (8.0, 8.0, 0.0, 0.0)
EXPECTED_WEIGHTS: tuple[float, ...] = (1.0, 0.0, 1.0, 0.0)
EXPECTED_LABELS: tuple[str, ...] = (
    "hzd8-avd1.0",
    "hzd8-avd0.0",
    "hzd0-avd1.0",
    "hzd0-avd0.0",
)


# ---------------------------------------------------------------------------
# Shape + parameter pinning
# ---------------------------------------------------------------------------


def test_v0_26_arms_have_exactly_four_arms() -> None:
    assert len(V0_26_ARMS) == 4


def test_v0_26_arms_have_expected_labels() -> None:
    labels = tuple(arm.label for arm in V0_26_ARMS)
    assert labels == EXPECTED_LABELS


def test_v0_26_arm_hazard_values() -> None:
    """hazard_damage covers {8, 8, 0, 0} in declaration order."""
    damages = tuple(arm.hazard_damage for arm in V0_26_ARMS)
    assert damages == EXPECTED_HAZARDS


def test_v0_26_arm_avoidance_weights() -> None:
    """hazard_avoidance_weight covers {1.0, 0.0, 1.0, 0.0} in declaration order."""
    weights = tuple(arm.hazard_avoidance_weight for arm in V0_26_ARMS)
    assert weights == EXPECTED_WEIGHTS


def test_v0_26_arms_share_substrate() -> None:
    """Every v0.26 arm holds the v0.21 substrate constant. Only
    hazard_damage and hazard_avoidance_weight vary; influx is fixed at 1.0."""
    for arm in V0_26_ARMS:
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
# Anchor substrate identity against v0.25
# ---------------------------------------------------------------------------


def _find_arm(arms: tuple, label: str):
    for arm in arms:
        if arm.label == label:
            return arm
    msg = f"arm with label {label!r} not found"
    raise AssertionError(msg)


def test_v0_26_hazard_eight_substrate_matches_v0_25_anchor() -> None:
    """V0_26 hzd8-avd1.0 substrate matches V0_25 transfer-1500-hzd8-influx-1.0
    on every field except the new hazard_avoidance_weight (which v0.25 leaves
    None and v0.26 sets to 1.0 — both produce the policy default 1.0)."""
    v26 = _find_arm(V0_26_ARMS, "hzd8-avd1.0")
    v25 = _find_arm(V0_25_ARMS, "transfer-1500-hzd8-influx-1.0")
    assert v26.hazard_damage == v25.hazard_damage == 8.0
    assert v26.ambient_influx_rate == v25.ambient_influx_rate == 1.0
    assert v26.energy_pool_initial == v25.energy_pool_initial == 1_500.0
    assert v26.energy_cost == v25.energy_cost == 15.0
    assert v26.offspring_start_energy == v25.offspring_start_energy == 30.0
    assert v26.child_funding_mode == v25.child_funding_mode
    assert v26.hazard_avoidance_weight == 1.0
    assert v25.hazard_avoidance_weight is None  # v0.25 unaware of the seam


def test_v0_26_hazard_zero_substrate_matches_v0_25_anchor() -> None:
    """V0_26 hzd0-avd1.0 substrate matches V0_25 transfer-1500-hzd0-influx-1.0
    on every field except hazard_avoidance_weight."""
    v26 = _find_arm(V0_26_ARMS, "hzd0-avd1.0")
    v25 = _find_arm(V0_25_ARMS, "transfer-1500-hzd0-influx-1.0")
    assert v26.hazard_damage == v25.hazard_damage == 0.0
    assert v26.ambient_influx_rate == v25.ambient_influx_rate == 1.0
    assert v26.energy_pool_initial == v25.energy_pool_initial == 1_500.0


# ---------------------------------------------------------------------------
# Prior arms unchanged
# ---------------------------------------------------------------------------


def test_pre_v0_26_arms_have_no_avoidance_weight_override() -> None:
    """v0.7..v0.25 arm tuples must keep hazard_avoidance_weight=None to
    preserve bit-identity. v0.26 is the first tuple to set it explicitly."""
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


def test_v0_25_arms_unchanged_by_v0_26() -> None:
    """V0_25_ARMS is purely v0.25 territory; v0.26 must not mutate its
    structure or hazard_damage settings."""
    assert len(V0_25_ARMS) == 12
    damages = tuple(arm.hazard_damage for arm in V0_25_ARMS)
    expected = (0.0, 0.0, 0.0, 4.0, 4.0, 4.0, 8.0, 8.0, 8.0, 12.0, 12.0, 12.0)
    assert damages == expected


# ---------------------------------------------------------------------------
# H5 hard pin: hazard=0 cells produce 0 injury deaths regardless of weight
# ---------------------------------------------------------------------------


def test_v0_26_hazard_zero_phantom_smoke_food_ladder(tmp_path: Path) -> None:
    """Arm C (phantom: hazard=0, weight=1.0) on food_ladder produces zero
    injury deaths and zero pool_in_death_residual, mirroring v0.23/v0.25
    hazard=0 hard pins. Halt-condition smoke."""
    arm_c = _find_arm(V0_26_ARMS, "hzd0-avd1.0")
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
    assert result.injury_deaths == 0
    assert result.pool_in_death_residual == 0.0
    assert result.reproduction_heat_loss == 0.0


def test_v0_26_hazard_zero_no_hazard_smoke_tight(tmp_path: Path) -> None:
    """Arm D (no-hazard: hazard=0, weight=0.0) on tight produces zero
    injury deaths regardless of weight value (damage=0 means nothing
    can credit injury deaths)."""
    arm_d = _find_arm(V0_26_ARMS, "hzd0-avd0.0")
    runs_root = tmp_path / "runs"
    runs_root.mkdir()
    result, _diag = _run_one_arm_seed(
        arm=arm_d,
        layout_name="tight_gradient",
        seed=1,
        runs_root=runs_root,
        n_ticks=40,
        n_founders=3,
    )
    assert result.injury_deaths == 0
    assert result.pool_in_death_residual == 0.0


# ---------------------------------------------------------------------------
# H12 phantom ≡ no-hazard byte-identity (Reading A deductive identity)
# ---------------------------------------------------------------------------


def test_v0_26_phantom_equals_no_hazard_food_ladder(tmp_path: Path) -> None:
    """Phantom (damage=0, weight=1.0) and no-hazard (damage=0, weight=0.0)
    must produce identical aggregates on the same seed: at damage=0 the
    hazard_signal_* fields are zero, so any weight multiplier is dormant.
    Deductive identity under Reading A."""
    arm_c = _find_arm(V0_26_ARMS, "hzd0-avd1.0")
    arm_d = _find_arm(V0_26_ARMS, "hzd0-avd0.0")
    runs_root = tmp_path / "runs"
    runs_root.mkdir()
    (runs_root / "phantom").mkdir()
    (runs_root / "no_hazard").mkdir()
    result_c, _ = _run_one_arm_seed(
        arm=arm_c,
        layout_name="food_ladder",
        seed=2,
        runs_root=runs_root / "phantom",
        n_ticks=60,
        n_founders=3,
    )
    result_d, _ = _run_one_arm_seed(
        arm=arm_d,
        layout_name="food_ladder",
        seed=2,
        runs_root=runs_root / "no_hazard",
        n_ticks=60,
        n_founders=3,
    )
    assert result_c.births == result_d.births
    assert result_c.starvation_deaths == result_d.starvation_deaths
    assert result_c.injury_deaths == result_d.injury_deaths
    assert result_c.food_events == result_d.food_events
    assert result_c.hazard_entries == result_d.hazard_entries
    assert result_c.pool_min == result_d.pool_min
    assert result_c.pool_end == result_d.pool_end
    assert result_c.population_end == result_d.population_end


def test_v0_26_phantom_equals_no_hazard_tight(tmp_path: Path) -> None:
    """Same H12 identity on tight chamber."""
    arm_c = _find_arm(V0_26_ARMS, "hzd0-avd1.0")
    arm_d = _find_arm(V0_26_ARMS, "hzd0-avd0.0")
    runs_root = tmp_path / "runs"
    runs_root.mkdir()
    (runs_root / "phantom").mkdir()
    (runs_root / "no_hazard").mkdir()
    result_c, _ = _run_one_arm_seed(
        arm=arm_c,
        layout_name="tight_gradient",
        seed=3,
        runs_root=runs_root / "phantom",
        n_ticks=60,
        n_founders=3,
    )
    result_d, _ = _run_one_arm_seed(
        arm=arm_d,
        layout_name="tight_gradient",
        seed=3,
        runs_root=runs_root / "no_hazard",
        n_ticks=60,
        n_founders=3,
    )
    assert result_c.births == result_d.births
    assert result_c.starvation_deaths == result_d.starvation_deaths
    assert result_c.injury_deaths == result_d.injury_deaths
    assert result_c.hazard_entries == result_d.hazard_entries
    assert result_c.pool_end == result_d.pool_end


# ---------------------------------------------------------------------------
# Substantive smoke: invisible hazard produces injury deaths on tight
# ---------------------------------------------------------------------------


def test_v0_26_invisible_tight_produces_more_hazard_entries_than_coupled(
    tmp_path: Path,
) -> None:
    """Mechanical sanity for the substantive arm: at (tight, hazard=8)
    the invisible cell (weight=0) should produce MORE hazard_entries
    than the coupled cell (weight=1) because avoidance is dormant.
    Aggregated across 3 seeds at n_ticks=120 — single-seed comparisons
    can coincide for small founder cohorts (similar to v0.25 H10's
    aggregate-only signature). Precise aggregates are the domain of
    the sweep; this is bidirectional-threading sanity."""
    arm_a = _find_arm(V0_26_ARMS, "hzd8-avd1.0")
    arm_b = _find_arm(V0_26_ARMS, "hzd8-avd0.0")
    runs_root = tmp_path / "runs"
    runs_root.mkdir()
    (runs_root / "coupled").mkdir()
    (runs_root / "invisible").mkdir()
    coupled_total = 0
    invisible_total = 0
    for seed in (1, 2, 3):
        result_coupled, _ = _run_one_arm_seed(
            arm=arm_a,
            layout_name="tight_gradient",
            seed=seed,
            runs_root=runs_root / "coupled",
            n_ticks=120,
            n_founders=5,
        )
        result_invisible, _ = _run_one_arm_seed(
            arm=arm_b,
            layout_name="tight_gradient",
            seed=seed,
            runs_root=runs_root / "invisible",
            n_ticks=120,
            n_founders=5,
        )
        coupled_total += result_coupled.hazard_entries
        invisible_total += result_invisible.hazard_entries
    # The substantive direction: aggregated hazard entries strictly
    # increase when avoidance is dormant on tight.
    assert invisible_total > coupled_total
