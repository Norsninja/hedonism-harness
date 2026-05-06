"""Tests for v0.32 ``V0_32_TIGHT_H_ARMS`` (4-arm subset of V0_25_ARMS at
influx=1.0 across hazards {0, 4, 8, 12}, used with seeds 9..16 for the
tight h*=8 hazard-axis reproducibility audit).

Covers:
  - V0_32_TIGHT_H_ARMS shape: exactly 4 arms with hazards {0, 4, 8, 12},
    all at influx=1.0, all with hazard_avoidance_weight=None
    (pre-v0.26 default substrate).
  - V0_32_TIGHT_H_ARMS literal-subset identity to V0_25_ARMS at the
    matched labels (H1 substrate-identity-by-construction).
  - Substrate-byte-identity to V0_25_ARMS by field-equality fallback.
  - Prior arm tuples (ARMS, V0_15..V0_27_ARMS, V0_29_ARMS,
    V0_30_TIGHT_W_ARMS, V0_31_TIGHT_W_ARMS) untouched.
"""

from __future__ import annotations

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
    V0_29_ARMS,
    V0_30_TIGHT_W_ARMS,
    V0_31_TIGHT_W_ARMS,
    V0_32_TIGHT_H_ARMS,
)

EXPECTED_LABELS: tuple[str, ...] = (
    "transfer-1500-hzd0-influx-1.0",
    "transfer-1500-hzd4-influx-1.0",
    "transfer-1500-hzd8-influx-1.0",
    "transfer-1500-hzd12-influx-1.0",
)
EXPECTED_HAZARDS: tuple[float, ...] = (0.0, 4.0, 8.0, 12.0)


# ---------------------------------------------------------------------------
# Shape + parameter pinning
# ---------------------------------------------------------------------------


def test_v0_32_tight_h_arms_have_exactly_four_arms() -> None:
    assert len(V0_32_TIGHT_H_ARMS) == 4


def test_v0_32_tight_h_arms_have_expected_labels() -> None:
    labels = tuple(arm.label for arm in V0_32_TIGHT_H_ARMS)
    assert labels == EXPECTED_LABELS


def test_v0_32_tight_h_arms_have_expected_hazards() -> None:
    hazards = tuple(arm.hazard_damage for arm in V0_32_TIGHT_H_ARMS)
    assert hazards == EXPECTED_HAZARDS


def test_v0_32_tight_h_arms_pinned_to_influx_one() -> None:
    for arm in V0_32_TIGHT_H_ARMS:
        assert arm.ambient_influx_rate == 1.0


def test_v0_32_tight_h_arms_have_no_avoidance_weight_override() -> None:
    """v0.32 uses the true v0.25 substrate (pre-v0.26 default avoidance
    behaviour). hazard_avoidance_weight=None is the contract."""
    for arm in V0_32_TIGHT_H_ARMS:
        assert arm.hazard_avoidance_weight is None


def test_v0_32_tight_h_arms_share_substrate() -> None:
    """Every v0.32 arm holds the v0.21 substrate constant (only
    hazard_damage varies; influx fixed at 1.0)."""
    for arm in V0_32_TIGHT_H_ARMS:
        assert arm.energy_cost == 15.0
        assert arm.energy_threshold == 50.0
        assert arm.offspring_start_energy == 30.0
        assert arm.food_respawn_cooldown == 50
        assert arm.energy_pool_initial == 1_500.0
        assert arm.child_funding_mode == ChildFundingMode.PARENT_TRANSFER_POOL_GAP
        assert arm.memory_type is None
        assert arm.auto_reproduction is True


# ---------------------------------------------------------------------------
# H1 — V0_32_TIGHT_H_ARMS is a literal subset of V0_25_ARMS
# ---------------------------------------------------------------------------


def _find_arm(arms: tuple, label: str):
    for arm in arms:
        if arm.label == label:
            return arm
    msg = f"arm with label {label!r} not found"
    raise AssertionError(msg)


def test_v0_32_tight_h_arms_are_literal_v0_25_subset() -> None:
    """Every V0_32_TIGHT_H_ARMS member is the SAME Arm instance as the
    matching V0_25_ARMS member (identity, not just equality).
    By-construction guard against substrate drift."""
    for arm in V0_32_TIGHT_H_ARMS:
        v25_arm = _find_arm(V0_25_ARMS, arm.label)
        assert arm is v25_arm, (
            f"V0_32_TIGHT_H_ARMS[{arm.label}] is not the same Arm instance "
            f"as V0_25_ARMS[{arm.label}]; substrate-identity-by-construction "
            f"broken — likely an accidental copy / mutation."
        )


def test_v0_32_substrate_byte_identical_to_v0_25_at_matched_labels() -> None:
    """Equality fallback for the substrate-identity guard."""
    for arm in V0_32_TIGHT_H_ARMS:
        v25 = _find_arm(V0_25_ARMS, arm.label)
        assert arm.hazard_damage == v25.hazard_damage
        assert arm.ambient_influx_rate == v25.ambient_influx_rate
        assert arm.energy_pool_initial == v25.energy_pool_initial
        assert arm.energy_cost == v25.energy_cost
        assert arm.energy_threshold == v25.energy_threshold
        assert arm.offspring_start_energy == v25.offspring_start_energy
        assert arm.food_respawn_cooldown == v25.food_respawn_cooldown
        assert arm.child_funding_mode == v25.child_funding_mode
        assert arm.auto_reproduction == v25.auto_reproduction
        assert arm.memory_type == v25.memory_type
        assert arm.hazard_avoidance_weight == v25.hazard_avoidance_weight


# ---------------------------------------------------------------------------
# H4 (prior arms unchanged)
# ---------------------------------------------------------------------------


def test_pre_v0_26_arms_still_have_no_avoidance_weight_override() -> None:
    """No v0.32 mutation of pre-v0.26 arm tuples."""
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
            assert arm.hazard_avoidance_weight is None


def test_v0_25_arms_unchanged_by_v0_32() -> None:
    """V0_25_ARMS is exactly 12 arms; v0.32 must not mutate it."""
    assert len(V0_25_ARMS) == 12
    hazards = tuple(arm.hazard_damage for arm in V0_25_ARMS)
    # 4 hazards x 3 influxes
    assert sorted(set(hazards)) == [0.0, 4.0, 8.0, 12.0]


def test_v0_26_arms_unchanged_by_v0_32() -> None:
    assert len(V0_26_ARMS) == 4
    weights = tuple(arm.hazard_avoidance_weight for arm in V0_26_ARMS)
    assert weights == (1.0, 0.0, 1.0, 0.0)


def test_v0_27_arms_unchanged_by_v0_32() -> None:
    assert len(V0_27_ARMS) == 5
    weights = tuple(arm.hazard_avoidance_weight for arm in V0_27_ARMS)
    assert weights == (0.0, 0.25, 0.5, 0.75, 1.0)


def test_v0_29_arms_unchanged_by_v0_32() -> None:
    assert len(V0_29_ARMS) == 3


def test_v0_30_tight_w_arms_unchanged_by_v0_32() -> None:
    assert len(V0_30_TIGHT_W_ARMS) == 3


def test_v0_31_tight_w_arms_unchanged_by_v0_32() -> None:
    assert len(V0_31_TIGHT_W_ARMS) == 3
