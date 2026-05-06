"""Tests for v0.31 ``V0_31_TIGHT_W_ARMS`` (3-arm subset of V0_27_ARMS at
w in {0.5, 0.75, 1.0} on the tight_gradient w*=0.75 audit cell, used
with seeds 17..24 for the third-stream pooled-24-seed calibration).

Covers:
  - V0_31_TIGHT_W_ARMS shape: exactly 3 arms with weights {0.5, 0.75, 1.0}.
  - V0_31_TIGHT_W_ARMS literal-subset identity to V0_27_ARMS at the
    matched labels (H1 substrate-identity-by-construction).
  - V0_31_TIGHT_W_ARMS arm-object identity to V0_29_ARMS and
    V0_30_TIGHT_W_ARMS at the matched labels (H1b cross-version arm-
    object equivalence; chamber differs at run time, arm objects do not).
  - Substrate-byte-identity to V0_27_ARMS by field-equality fallback.
  - Prior arm tuples (ARMS, V0_15..V0_27_ARMS, V0_29_ARMS,
    V0_30_TIGHT_W_ARMS) untouched.
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
)

EXPECTED_LABELS: tuple[str, ...] = (
    "hzd8-avd0.50",
    "hzd8-avd0.75",
    "hzd8-avd1.00",
)
EXPECTED_WEIGHTS: tuple[float, ...] = (0.5, 0.75, 1.0)


# ---------------------------------------------------------------------------
# Shape + parameter pinning
# ---------------------------------------------------------------------------


def test_v0_31_tight_w_arms_have_exactly_three_arms() -> None:
    assert len(V0_31_TIGHT_W_ARMS) == 3


def test_v0_31_tight_w_arms_have_expected_labels() -> None:
    labels = tuple(arm.label for arm in V0_31_TIGHT_W_ARMS)
    assert labels == EXPECTED_LABELS


def test_v0_31_tight_w_arms_have_expected_avoidance_weights() -> None:
    weights = tuple(arm.hazard_avoidance_weight for arm in V0_31_TIGHT_W_ARMS)
    assert weights == EXPECTED_WEIGHTS


def test_v0_31_tight_w_arms_pinned_to_hazard_eight() -> None:
    for arm in V0_31_TIGHT_W_ARMS:
        assert arm.hazard_damage == 8.0


def test_v0_31_tight_w_arms_share_substrate() -> None:
    """Every v0.31 arm holds the v0.21 substrate constant (only
    hazard_avoidance_weight varies; influx fixed at 1.0)."""
    for arm in V0_31_TIGHT_W_ARMS:
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
# H1 — V0_31_TIGHT_W_ARMS is a literal subset of V0_27_ARMS
# ---------------------------------------------------------------------------


def _find_arm(arms: tuple, label: str):
    for arm in arms:
        if arm.label == label:
            return arm
    msg = f"arm with label {label!r} not found"
    raise AssertionError(msg)


def test_v0_31_tight_w_arms_are_literal_v0_27_subset() -> None:
    """Every V0_31_TIGHT_W_ARMS member is the SAME Arm instance as the
    matching V0_27_ARMS member (identity, not just equality).
    By-construction guard against substrate drift."""
    for arm in V0_31_TIGHT_W_ARMS:
        v27_arm = _find_arm(V0_27_ARMS, arm.label)
        assert arm is v27_arm, (
            f"V0_31_TIGHT_W_ARMS[{arm.label}] is not the same Arm instance "
            f"as V0_27_ARMS[{arm.label}]; substrate-identity-by-construction "
            f"broken — likely an accidental copy / mutation."
        )


def test_v0_31_substrate_byte_identical_to_v0_27_at_matched_labels() -> None:
    """Equality fallback for the substrate-identity guard."""
    for arm in V0_31_TIGHT_W_ARMS:
        v27 = _find_arm(V0_27_ARMS, arm.label)
        assert arm.hazard_damage == v27.hazard_damage
        assert arm.hazard_avoidance_weight == v27.hazard_avoidance_weight
        assert arm.ambient_influx_rate == v27.ambient_influx_rate
        assert arm.energy_pool_initial == v27.energy_pool_initial
        assert arm.energy_cost == v27.energy_cost
        assert arm.energy_threshold == v27.energy_threshold
        assert arm.offspring_start_energy == v27.offspring_start_energy
        assert arm.food_respawn_cooldown == v27.food_respawn_cooldown
        assert arm.child_funding_mode == v27.child_funding_mode
        assert arm.auto_reproduction == v27.auto_reproduction
        assert arm.memory_type == v27.memory_type


# ---------------------------------------------------------------------------
# H1b — arm-object identity to V0_29_ARMS and V0_30_TIGHT_W_ARMS
# ---------------------------------------------------------------------------


def test_v0_31_tight_w_arms_share_arm_objects_with_v0_29_arms() -> None:
    """H1b: arm-object identity only, not chamber identity. V0_29_ARMS
    (food_ladder) and V0_31_TIGHT_W_ARMS (tight_gradient, seeds 17..24)
    should reference the same underlying V0_27_ARMS instances for the
    shared avoidance-weight labels."""
    for arm in V0_31_TIGHT_W_ARMS:
        v29_arm = _find_arm(V0_29_ARMS, arm.label)
        assert arm is v29_arm, (
            f"V0_31_TIGHT_W_ARMS[{arm.label}] is not the same Arm instance "
            f"as V0_29_ARMS[{arm.label}]; arm-object equivalence broken — "
            f"one of the tuples has drifted off the V0_27_ARMS slice contract."
        )


def test_v0_31_tight_w_arms_share_arm_objects_with_v0_30_tight_w_arms() -> None:
    """H1b: same-chamber two-stream arm-object identity. V0_30_TIGHT_W_ARMS
    (seeds 9..16) and V0_31_TIGHT_W_ARMS (seeds 17..24) run on the same
    chamber; the arm objects MUST be identical so the substrate axis is
    fixed by-construction across streams 2 and 3."""
    for arm in V0_31_TIGHT_W_ARMS:
        v30_arm = _find_arm(V0_30_TIGHT_W_ARMS, arm.label)
        assert arm is v30_arm, (
            f"V0_31_TIGHT_W_ARMS[{arm.label}] is not the same Arm instance "
            f"as V0_30_TIGHT_W_ARMS[{arm.label}]; same-chamber stream-pair "
            f"substrate identity broken."
        )


# ---------------------------------------------------------------------------
# H4 (prior arms unchanged)
# ---------------------------------------------------------------------------


def test_pre_v0_26_arms_still_have_no_avoidance_weight_override() -> None:
    """No v0.31 mutation of pre-v0.26 arm tuples."""
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


def test_v0_26_arms_unchanged_by_v0_31() -> None:
    assert len(V0_26_ARMS) == 4
    weights = tuple(arm.hazard_avoidance_weight for arm in V0_26_ARMS)
    assert weights == (1.0, 0.0, 1.0, 0.0)
    damages = tuple(arm.hazard_damage for arm in V0_26_ARMS)
    assert damages == (8.0, 8.0, 0.0, 0.0)


def test_v0_27_arms_unchanged_by_v0_31() -> None:
    assert len(V0_27_ARMS) == 5
    weights = tuple(arm.hazard_avoidance_weight for arm in V0_27_ARMS)
    assert weights == (0.0, 0.25, 0.5, 0.75, 1.0)
    for arm in V0_27_ARMS:
        assert arm.hazard_damage == 8.0


def test_v0_29_arms_unchanged_by_v0_31() -> None:
    """V0_29_ARMS is exactly 3 arms with weights (0.5, 0.75, 1.0);
    v0.31 must not mutate it."""
    assert len(V0_29_ARMS) == 3
    weights = tuple(arm.hazard_avoidance_weight for arm in V0_29_ARMS)
    assert weights == (0.5, 0.75, 1.0)
    for arm in V0_29_ARMS:
        assert arm.hazard_damage == 8.0


def test_v0_30_tight_w_arms_unchanged_by_v0_31() -> None:
    """V0_30_TIGHT_W_ARMS is exactly 3 arms with weights (0.5, 0.75, 1.0);
    v0.31 must not mutate it."""
    assert len(V0_30_TIGHT_W_ARMS) == 3
    weights = tuple(arm.hazard_avoidance_weight for arm in V0_30_TIGHT_W_ARMS)
    assert weights == (0.5, 0.75, 1.0)
    for arm in V0_30_TIGHT_W_ARMS:
        assert arm.hazard_damage == 8.0
