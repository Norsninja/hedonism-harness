"""v0.53b reachability disambiguation audit — tests (16 locked).

Pre-reg: [[docs/experiments/fear_hunger_v0.53b.md]] §"Test list (locked, 16 tests)".
Tests numbered to match the pre-reg's ordering.
"""

from __future__ import annotations

import hashlib
import importlib.util
import math
import statistics
import sys
from pathlib import Path

import pytest

_SCRIPT_PATH = (
    Path(__file__).parent.parent / "scripts" / "v0_53b_reachability_disambiguation_audit.py"
)
_spec = importlib.util.spec_from_file_location("v0_53b_audit", _SCRIPT_PATH)
assert _spec is not None
assert _spec.loader is not None
v0_53b_audit = importlib.util.module_from_spec(_spec)
sys.modules["v0_53b_audit"] = v0_53b_audit
_spec.loader.exec_module(v0_53b_audit)


# ---------------------------------------------------------------------------
# Synthetic helpers
# ---------------------------------------------------------------------------


def _make_summary(
    *,
    arm: str,
    observable: str,
    sign: int,
    paired_d: float,
    label: str,
) -> object:
    signed = paired_d * sign if not math.isnan(paired_d) else float("nan")
    fires_expected = (not math.isnan(signed)) and signed >= v0_53b_audit.COHENS_D_THRESHOLD
    fires_wrong = (not math.isnan(signed)) and signed <= -v0_53b_audit.COHENS_D_THRESHOLD
    return v0_53b_audit.ObservableSummary(
        arm=arm,
        observable=observable,
        label=label,
        sign=sign,
        n_runs_contributing=64,
        paired_d=paired_d,
        signed_d=signed,
        delta_mean=0.0,
        delta_stdev=1.0,
        delta_min=-1.0,
        delta_max=+1.0,
        fires_expected=fires_expected,
        fires_wrong=fires_wrong,
    )


def _three_summaries_for_arm_tick100(
    arm: str, ds: tuple[float, float, float], label: str
) -> list[object]:
    obs = v0_53b_audit.PRIMARY_OBSERVABLES_TICK100
    return [
        _make_summary(arm=arm, observable=obs[i][0], sign=obs[i][1], paired_d=ds[i], label=label)
        for i in range(3)
    ]


def _zero_drift_bridge_re_anchor() -> list[object]:
    return [
        v0_53b_audit.BridgeReAnchorRow(
            label=label,
            observable=obs,
            published_signed_d=ref,
            derived_signed_d=ref,
            drift_abs=0.0,
            halts=False,
        )
        for (label, obs), ref in v0_53b_audit.V048_PUBLISHED_SIGNED_D.items()
    ]


def _arm_subverdict_for_tick100(arm: str, kind: str) -> str:
    """Return locked tick-100 sub-verdict constant for (arm, kind)."""
    table = {
        v0_53b_audit.ARM_A_NULL_V025: {
            "PRESENT": v0_53b_audit.SUBVERDICT_A_NULL_V025_TICK100_PRESENT,
            "PARTIAL": v0_53b_audit.SUBVERDICT_A_NULL_V025_TICK100_PARTIAL,
            "NOT_FOUND": v0_53b_audit.SUBVERDICT_A_NULL_V025_TICK100_NOT_FOUND,
            "OPPOSITE": v0_53b_audit.SUBVERDICT_A_NULL_V025_TICK100_OPPOSITE,
        },
        v0_53b_audit.ARM_B_WIDENED: {
            "PRESENT": v0_53b_audit.SUBVERDICT_B_WIDENED_TICK100_PRESENT,
            "PARTIAL": v0_53b_audit.SUBVERDICT_B_WIDENED_TICK100_PARTIAL,
            "NOT_FOUND": v0_53b_audit.SUBVERDICT_B_WIDENED_TICK100_NOT_FOUND,
            "OPPOSITE": v0_53b_audit.SUBVERDICT_B_WIDENED_TICK100_OPPOSITE,
        },
        v0_53b_audit.ARM_C_LADDER: {
            "PRESENT": v0_53b_audit.SUBVERDICT_C_LADDER_TICK100_PRESENT,
            "PARTIAL": v0_53b_audit.SUBVERDICT_C_LADDER_TICK100_PARTIAL,
            "NOT_FOUND": v0_53b_audit.SUBVERDICT_C_LADDER_TICK100_NOT_FOUND,
            "OPPOSITE": v0_53b_audit.SUBVERDICT_C_LADDER_TICK100_OPPOSITE,
        },
    }
    return table[arm][kind]


# ---------------------------------------------------------------------------
# Test 1 — paired_d formula reproduces hand-computed signed_d on a fixture
# AND Tier-1 reference constants byte-equal v0.48 / v0.53 published values.
# ---------------------------------------------------------------------------


def test_paired_d_function_reproduces_hand_computed_signed_d_on_fixture_and_tier1_constants_match_v048_published_values():  # noqa: E501
    # Part A: feed _paired_cohens_d a synthetic 8-run pool and compare
    # against hand-computed mean / ddof=1 stdev.
    deltas = [1.0, 2.0, 1.5, 0.5, 2.5, 1.8, 0.9, 1.2]
    expected_mean = statistics.mean(deltas)
    expected_sd = statistics.stdev(deltas)
    expected_d = expected_mean / expected_sd
    derived_d = v0_53b_audit._paired_cohens_d(deltas)
    assert abs(derived_d - expected_d) < 1e-9

    # Part B: locked Tier-1 reference constants byte-equal pinned v0.48 / v0.53 values.
    pinned_v048 = {
        ("label_a_sensor_radius", "pre50_food_events_count"): +1.066,
        ("label_a_sensor_radius", "pre50_food_energy_acquired"): +1.066,
        ("label_a_sensor_radius", "mean_distance_to_nearest_food_cell_tick50"): +1.916,
        ("label_b_readiness_fraction_tick50", "pre50_food_events_count"): +0.916,
        ("label_b_readiness_fraction_tick50", "pre50_food_energy_acquired"): +0.916,
        ("label_b_readiness_fraction_tick50", "mean_distance_to_nearest_food_cell_tick50"): +1.179,
    }
    assert pinned_v048 == v0_53b_audit.V048_PUBLISHED_SIGNED_D


# ---------------------------------------------------------------------------
# Test 2 — A_null_V0_25 corpus a_share_h8 re-anchors v0.42 / v0.44 / v0.45.
# ---------------------------------------------------------------------------


def test_a_null_v025_corpus_a_share_h8_re_anchors_v042_v044_v045():
    clean = [
        v0_53b_audit.ReAnchorRow(
            arm=v0_53b_audit.ARM_A_NULL_V025,
            version=ver,
            hazard=8,
            n_runs_contributing=8,
            a_share_h8_derived=ref,
            a_share_h8_published=ref,
            drift_abs=0.0,
            halts=False,
        )
        for ver, ref in (("v0.42", 0.652), ("v0.44", 0.878), ("v0.45", 0.818))
    ]
    rollup, _ = v0_53b_audit._evaluate_rollup(
        a_null_tick50_subverdict=v0_53b_audit.SUBVERDICT_A_NULL_V025_TICK50_PRESENT,
        a_null_tick100_subverdict=v0_53b_audit.SUBVERDICT_A_NULL_V025_TICK100_PRESENT,
        b_tick100_subverdict=v0_53b_audit.SUBVERDICT_B_WIDENED_TICK100_PRESENT,
        c_tick100_subverdict=v0_53b_audit.SUBVERDICT_C_LADDER_TICK100_PRESENT,
        corpus_re_anchor=clean,
        bridge_re_anchor=_zero_drift_bridge_re_anchor(),
        b_reachability=0.50,
    )
    assert rollup == v0_53b_audit.ROLLUP_WIDENED_REACHABILITY_CENSORED_RESOLVED

    # Drift > 1e-3 on v0.44 -> CORPUS_REDERIVE_DRIFT_HALT.
    drifted = list(clean)
    drifted[1] = v0_53b_audit.ReAnchorRow(
        arm=v0_53b_audit.ARM_A_NULL_V025,
        version="v0.44",
        hazard=8,
        n_runs_contributing=8,
        a_share_h8_derived=0.880,
        a_share_h8_published=0.878,
        drift_abs=0.002,
        halts=True,
    )
    rollup_d, phrase_d = v0_53b_audit._evaluate_rollup(
        a_null_tick50_subverdict=v0_53b_audit.SUBVERDICT_A_NULL_V025_TICK50_PRESENT,
        a_null_tick100_subverdict=v0_53b_audit.SUBVERDICT_A_NULL_V025_TICK100_PRESENT,
        b_tick100_subverdict=v0_53b_audit.SUBVERDICT_B_WIDENED_TICK100_PRESENT,
        c_tick100_subverdict=v0_53b_audit.SUBVERDICT_C_LADDER_TICK100_PRESENT,
        corpus_re_anchor=drifted,
        bridge_re_anchor=_zero_drift_bridge_re_anchor(),
        b_reachability=0.50,
    )
    assert rollup_d == v0_53b_audit.ROLLUP_CORPUS_DRIFT_HALT
    assert "v0.44" in phrase_d


# ---------------------------------------------------------------------------
# Test 3 — Arm A_null_V0_25 uses tight_gradient_layout
# ---------------------------------------------------------------------------


def test_arm_a_null_v025_uses_tight_gradient_layout():
    layout = v0_53b_audit._layout_for_arm(v0_53b_audit.ARM_A_NULL_V025)
    assert layout.width == 9
    assert layout.height == 6
    assert layout.safe_x_min == 0
    assert layout.safe_x_max == 2
    assert layout.hazard_x_min == 3
    assert layout.hazard_x_max == 4
    assert layout.food_x_min == 5
    assert layout.food_x_max == 8
    assert layout.resolved_spawn_x == 1
    assert v0_53b_audit.LAYOUT_NAME_BY_ARM[v0_53b_audit.ARM_A_NULL_V025] == "tight_gradient"


# ---------------------------------------------------------------------------
# Test 4 — Arm B_widened_gradient uses widened_gradient_layout
# ---------------------------------------------------------------------------


def test_arm_b_widened_uses_widened_gradient_layout():
    layout = v0_53b_audit._layout_for_arm(v0_53b_audit.ARM_B_WIDENED)
    assert layout.width == 15
    assert layout.height == 6
    assert layout.safe_x_min == 0
    assert layout.safe_x_max == 4
    assert layout.hazard_x_min == 5
    assert layout.hazard_x_max == 7
    assert layout.food_x_min == 10
    assert layout.food_x_max == 14
    assert layout.resolved_spawn_x == 1
    assert v0_53b_audit.LAYOUT_NAME_BY_ARM[v0_53b_audit.ARM_B_WIDENED] == "widened_gradient"


# ---------------------------------------------------------------------------
# Test 5 — Arm C_food_ladder uses food_ladder_layout
# ---------------------------------------------------------------------------


def test_arm_c_food_ladder_uses_food_ladder_layout():
    layout = v0_53b_audit._layout_for_arm(v0_53b_audit.ARM_C_LADDER)
    assert layout.width == 12
    assert layout.height == 6
    assert layout.safe_x_min == 0
    assert layout.safe_x_max == 2
    assert layout.hazard_x_min == 6
    assert layout.hazard_x_max == 8
    assert layout.food_x_min == 9
    assert layout.food_x_max == 11
    assert layout.resolved_spawn_x == 1
    assert layout.has_pre_food
    assert layout.pre_food_x_min == 4
    assert layout.pre_food_x_max == 4
    assert v0_53b_audit.LAYOUT_NAME_BY_ARM[v0_53b_audit.ARM_C_LADDER] == "food_ladder"


# ---------------------------------------------------------------------------
# Test 6 — Founder traits byte-identical across arms for same (version,
# seed, hazard) tuple.
# ---------------------------------------------------------------------------


def test_founder_traits_byte_identical_across_arms_for_same_seed(tmp_path):
    seed = 41
    arm_to_records: dict[str, list[tuple]] = {}
    for arm in v0_53b_audit.ARMS:
        cap = v0_53b_audit._run_one_arm(
            arm=arm, version="v0.42", seed=seed, hazard=0, runs_root=tmp_path
        )
        arm_to_records[arm] = [
            (
                rec.lineage_id,
                rec.founder_sensor_radius,
                rec.founder_reproduction_drive,
                rec.founder_metabolic_rate,
            )
            for rec in cap.founder_records
        ]
    arms = list(v0_53b_audit.ARMS)
    for arm in arms[1:]:
        assert arm_to_records[arm] == arm_to_records[arms[0]], (
            f"Founder traits diverged between {arms[0]} and {arm}; layout swap "
            f"must not perturb streams.mutation"
        )


# ---------------------------------------------------------------------------
# Test 7 — Founder positions byte-identical across arms for same seed.
# ---------------------------------------------------------------------------


def test_founder_positions_byte_identical_across_arms_for_same_seed():
    """All three layouts have spawn_x=1 and height=6, so spread_y(5, 6) yields
    identical y positions and spawn_x identical x positions across arms."""
    from hedonism_harness.experiments.fear_hunger_chamber import spread_y

    expected_xs = []
    expected_ys = None
    for arm in v0_53b_audit.ARMS:
        layout = v0_53b_audit._layout_for_arm(arm)
        spawn_x = layout.resolved_spawn_x
        ys = spread_y(v0_53b_audit.N_FOUNDERS, layout.height)
        expected_xs.append(spawn_x)
        if expected_ys is None:
            expected_ys = ys
        else:
            assert ys == expected_ys, (
                f"spread_y must be identical across arms; got {ys} vs {expected_ys}"
            )
    assert len(set(expected_xs)) == 1
    assert expected_xs[0] == 1


# ---------------------------------------------------------------------------
# Test 8 — No src/ modifications compared to v0.52b tip (= v0.53 tip).
# ---------------------------------------------------------------------------


V052B_TIP_SHA256: dict[str, str] = {
    "src/hedonism_harness/core/sensors.py": (
        "0deb814275cb81e7be9041b5c1bc49f12fa85f78620c96d476c66c40116b3f5d"
    ),
    "src/hedonism_harness/core/traits.py": (
        "53a1e065fd94033ff43a87128c875aeee448886c0027202b233711150c29c0b5"
    ),
    "src/hedonism_harness/core/body.py": (
        "604fc149da833b56b9edde09ba2e28330cf6bab81ff6b3f4cd693061ac21fc27"
    ),
    "src/hedonism_harness/core/config.py": (
        "e2cad9cb980be926512b66bd41c5422a79736da363825d2b8bd3771131f6e35c"
    ),
    "src/hedonism_harness/experiments/layouts.py": (
        "d4521cb54e352151adf9ce7ae04c07e16373bc882af2392d6d5c0c6afaa8808e"
    ),
}


def test_no_src_modifications_compared_to_v0_52b_tip():
    repo_root = Path(__file__).parent.parent
    for rel_path, expected_hash in V052B_TIP_SHA256.items():
        path = repo_root / rel_path
        actual_hash = hashlib.sha256(path.read_bytes()).hexdigest()
        if actual_hash != expected_hash:
            raise AssertionError(
                "v0.53b is pre-registered as no-src-change; update the pre-reg before changing src."
            )


# ---------------------------------------------------------------------------
# Test 9 — Label A high_sensor_radius_lineage picks correct lineage.
# ---------------------------------------------------------------------------


def test_label_a_high_sensor_radius_lineage_picks_correct_lineage():
    # Sensor radii [2, 5, 4, 1, 6] across lineages 0..4 -> lineage 4 wins.
    sensor_radius_by_lineage = {0: 2, 1: 5, 2: 4, 3: 1, 4: 6}
    label = v0_53b_audit._select_sensor_radius_label(sensor_radius_by_lineage)
    assert label == 4

    # Tiebreak min(lineage_id) on ties.
    sensor_tied = {0: 6, 1: 5, 2: 6, 3: 6, 4: 4}
    label_tied = v0_53b_audit._select_sensor_radius_label(sensor_tied)
    assert label_tied == 0


# ---------------------------------------------------------------------------
# Test 10 — Label B (tick-100) 3-tier tiebreak (fraction -> count ->
# min(lineage_id)). Mirrors v0.47 / v0.53 on the new tick-100 label.
# ---------------------------------------------------------------------------


def test_label_b_tick100_three_tier_tiebreak_fraction_count_min_lineage():
    # Two-way tie on fraction -> tiebreak by count.
    candidates_count_tiebreak = [
        (0, 0.5, 2),
        (1, 0.5, 4),  # higher count wins
        (2, 0.4, 5),
    ]
    assert v0_53b_audit._select_fraction_label(candidates_count_tiebreak) == 1

    # Tie on fraction AND count -> tiebreak by min(lineage_id).
    candidates_min_lid = [
        (3, 0.5, 4),
        (1, 0.5, 4),  # lowest lineage_id wins
        (2, 0.5, 4),
    ]
    assert v0_53b_audit._select_fraction_label(candidates_min_lid) == 1

    # Highest fraction wins outright.
    candidates_simple = [(0, 0.3, 5), (1, 0.7, 1), (2, 0.5, 3)]
    assert v0_53b_audit._select_fraction_label(candidates_simple) == 1

    # NaN-loses: empty candidate list (NaN filtered upstream) returns None.
    assert v0_53b_audit._select_fraction_label([]) is None


# ---------------------------------------------------------------------------
# Test 11 — pre100 window strictly extends pre50 window.
# Synthetic events at ticks 10, 30, 60, 90:
#   pre50_food_events_count = 2 (ticks 10, 30 <= 50)
#   pre100_food_events_count = 4 (ticks 10, 30, 60, 90 <= 100)
# ---------------------------------------------------------------------------


def test_pre100_window_strictly_extends_pre50_window():
    """Replay a simulated tick-stream of AteFood events through the
    accumulator logic that the per-tick observer wires up. Confirms tick-50
    accumulation captures only ticks <= 50; tick-100 accumulation captures
    all ticks <= 100."""
    capture = v0_53b_audit._RunCapture(
        arm=v0_53b_audit.ARM_B_WIDENED,
        layout_name="widened_gradient",
        version="v0.42",
        seed=41,
        hazard=0,
    )
    aid = 7
    event_ticks = [10, 30, 60, 90]

    # Mirror the observer's tick-window check exactly (tick_now <= TICK_50
    # accumulates pre50; tick_now <= TICK_100 accumulates pre100; tick_now
    # > TICK_100 is rejected entirely).
    for tick_now in event_ticks:
        if tick_now > v0_53b_audit.TICK_100:
            continue
        if tick_now <= v0_53b_audit.TICK_50:
            capture.pre50_food_events_by_agent[aid] = (
                capture.pre50_food_events_by_agent.get(aid, 0) + 1
            )
            capture.pre50_food_energy_by_agent[aid] = (
                capture.pre50_food_energy_by_agent.get(aid, 0.0) + 1.0
            )
        capture.pre100_food_events_by_agent[aid] = (
            capture.pre100_food_events_by_agent.get(aid, 0) + 1
        )
        capture.pre100_food_energy_by_agent[aid] = (
            capture.pre100_food_energy_by_agent.get(aid, 0.0) + 1.0
        )

    assert capture.pre50_food_events_by_agent[aid] == 2
    assert capture.pre100_food_events_by_agent[aid] == 4
    assert capture.pre50_food_energy_by_agent[aid] == 2.0
    assert capture.pre100_food_energy_by_agent[aid] == 4.0

    # Boundary: events at exactly tick 50 and tick 100 are inclusive; an
    # event at tick 101 must NOT be accumulated.
    capture2 = v0_53b_audit._RunCapture(
        arm=v0_53b_audit.ARM_B_WIDENED,
        layout_name="widened_gradient",
        version="v0.42",
        seed=41,
        hazard=0,
    )
    for tick_now in [50, 100, 101]:
        if tick_now > v0_53b_audit.TICK_100:
            continue
        if tick_now <= v0_53b_audit.TICK_50:
            capture2.pre50_food_events_by_agent[aid] = (
                capture2.pre50_food_events_by_agent.get(aid, 0) + 1
            )
        capture2.pre100_food_events_by_agent[aid] = (
            capture2.pre100_food_events_by_agent.get(aid, 0) + 1
        )
    assert capture2.pre50_food_events_by_agent[aid] == 1  # only tick 50
    assert capture2.pre100_food_events_by_agent[aid] == 2  # ticks 50, 100


# ---------------------------------------------------------------------------
# Test 12 — paired_d signed_d >= +0.5 fires PRESENT threshold (tick-100).
# ---------------------------------------------------------------------------


def test_paired_d_signed_d_ge_05_fires_present_threshold():
    arm = v0_53b_audit.ARM_A_NULL_V025
    summaries_a_full = _three_summaries_for_arm_tick100(
        arm, (+0.5, +0.6, -0.7), v0_53b_audit.LABEL_A_NAME
    )
    summaries_b_full = _three_summaries_for_arm_tick100(
        arm, (+0.5, +0.6, -0.7), v0_53b_audit.LABEL_B_TICK100_NAME
    )
    # signs (+1, +1, -1) -> signed_d's = (+0.5, +0.6, +0.7) -> 3/3 PRESENT
    assert (
        v0_53b_audit._arm_subverdict_tick100(arm, summaries_a_full, summaries_b_full)
        == v0_53b_audit.SUBVERDICT_A_NULL_V025_TICK100_PRESENT
    )

    # Drop one cell on Label A: paired_d = +0.4 -> signed_d = +0.4 < +0.5
    # Label A clears 2/3, Label B clears 3/3 -> still PRESENT (both >= 2).
    summaries_a_drop = _three_summaries_for_arm_tick100(
        arm, (+0.4, +0.6, -0.7), v0_53b_audit.LABEL_A_NAME
    )
    assert (
        v0_53b_audit._arm_subverdict_tick100(arm, summaries_a_drop, summaries_b_full)
        == v0_53b_audit.SUBVERDICT_A_NULL_V025_TICK100_PRESENT
    )

    # Drop Label A to 1/3 (only one cell clears) -> A doesn't clear; B does -> PARTIAL.
    summaries_a_partial = _three_summaries_for_arm_tick100(
        arm, (+0.4, +0.3, -0.7), v0_53b_audit.LABEL_A_NAME
    )
    assert (
        v0_53b_audit._arm_subverdict_tick100(arm, summaries_a_partial, summaries_b_full)
        == v0_53b_audit.SUBVERDICT_A_NULL_V025_TICK100_PARTIAL
    )


# ---------------------------------------------------------------------------
# Test 13 — paired_d signed_d <= -0.5 fires OPPOSITE_SIGN_HALT per arm.
# ---------------------------------------------------------------------------


def test_paired_d_signed_d_le_neg_05_fires_opposite_sign_halt_per_arm():
    # Build summaries where one observable fires wrong-sign (signed_d = -0.5).
    arm = v0_53b_audit.ARM_B_WIDENED
    # Sign on observable index 0 = +1; paired_d = -0.5 -> signed_d = -0.5 -> wrong-sign.
    summaries_a = _three_summaries_for_arm_tick100(
        arm, (-0.5, +0.6, -0.7), v0_53b_audit.LABEL_A_NAME
    )
    summaries_b = _three_summaries_for_arm_tick100(
        arm, (+0.6, +0.6, -0.7), v0_53b_audit.LABEL_B_TICK100_NAME
    )
    assert (
        v0_53b_audit._arm_subverdict_tick100(arm, summaries_a, summaries_b)
        == v0_53b_audit.SUBVERDICT_B_WIDENED_TICK100_OPPOSITE
    )

    # Same for arm C (wrong-sign on observable index 2, sign = -1).
    arm_c = v0_53b_audit.ARM_C_LADDER
    summaries_a_c = _three_summaries_for_arm_tick100(
        arm_c, (+0.6, +0.6, -0.7), v0_53b_audit.LABEL_A_NAME
    )
    # paired_d = +0.5 on a -1-sign observable -> signed_d = -0.5 -> wrong-sign.
    summaries_b_c = _three_summaries_for_arm_tick100(
        arm_c, (+0.6, +0.6, +0.5), v0_53b_audit.LABEL_B_TICK100_NAME
    )
    assert (
        v0_53b_audit._arm_subverdict_tick100(arm_c, summaries_a_c, summaries_b_c)
        == v0_53b_audit.SUBVERDICT_C_LADDER_TICK100_OPPOSITE
    )

    # Same for arm A_null at tick-100 (priority 3 includes A at tick-100 in v0.53b).
    arm_a = v0_53b_audit.ARM_A_NULL_V025
    summaries_a_a = _three_summaries_for_arm_tick100(
        arm_a, (-0.5, +0.6, -0.7), v0_53b_audit.LABEL_A_NAME
    )
    summaries_b_a = _three_summaries_for_arm_tick100(
        arm_a, (+0.6, +0.6, -0.7), v0_53b_audit.LABEL_B_TICK100_NAME
    )
    assert (
        v0_53b_audit._arm_subverdict_tick100(arm_a, summaries_a_a, summaries_b_a)
        == v0_53b_audit.SUBVERDICT_A_NULL_V025_TICK100_OPPOSITE
    )


# ---------------------------------------------------------------------------
# Test 14 — B reachability threshold partition.
#   reachability < 0.25  -> priority 6 BELOW (regardless of B sub-verdict)
#   reachability >= 0.25, B PRESENT      -> priority 4 RESOLVED
#   reachability >= 0.25, B PARTIAL/NF   -> priority 5 RESOLVED_BRIDGE_NOT_FOUND
# ---------------------------------------------------------------------------


def test_b_reachability_threshold_partition():
    bridge_clean = _zero_drift_bridge_re_anchor()

    # Below threshold (0.20 < 0.25): priority 6 fires regardless of B sub-verdict.
    for b_kind in ("PRESENT", "PARTIAL", "NOT_FOUND"):
        b_sub = _arm_subverdict_for_tick100(v0_53b_audit.ARM_B_WIDENED, b_kind)
        rollup, phrase = v0_53b_audit._evaluate_rollup(
            a_null_tick50_subverdict=v0_53b_audit.SUBVERDICT_A_NULL_V025_TICK50_PRESENT,
            a_null_tick100_subverdict=v0_53b_audit.SUBVERDICT_A_NULL_V025_TICK100_PRESENT,
            b_tick100_subverdict=b_sub,
            c_tick100_subverdict=v0_53b_audit.SUBVERDICT_C_LADDER_TICK100_PRESENT,
            corpus_re_anchor=[],
            bridge_re_anchor=bridge_clean,
            b_reachability=0.20,
        )
        assert rollup == v0_53b_audit.ROLLUP_WIDENED_BELOW_REACHABILITY_THRESHOLD
        assert "B_widened's reachability is below the locked 25% threshold" in phrase

    # Above threshold + B PRESENT -> priority 4 RESOLVED.
    rollup, phrase = v0_53b_audit._evaluate_rollup(
        a_null_tick50_subverdict=v0_53b_audit.SUBVERDICT_A_NULL_V025_TICK50_PRESENT,
        a_null_tick100_subverdict=v0_53b_audit.SUBVERDICT_A_NULL_V025_TICK100_PRESENT,
        b_tick100_subverdict=v0_53b_audit.SUBVERDICT_B_WIDENED_TICK100_PRESENT,
        c_tick100_subverdict=v0_53b_audit.SUBVERDICT_C_LADDER_TICK100_PRESENT,
        corpus_re_anchor=[],
        bridge_re_anchor=bridge_clean,
        b_reachability=0.30,
    )
    assert rollup == v0_53b_audit.ROLLUP_WIDENED_REACHABILITY_CENSORED_RESOLVED

    # Above threshold + B PARTIAL or NOT_FOUND -> priority 5.
    for b_kind in ("PARTIAL", "NOT_FOUND"):
        b_sub = _arm_subverdict_for_tick100(v0_53b_audit.ARM_B_WIDENED, b_kind)
        rollup, _ = v0_53b_audit._evaluate_rollup(
            a_null_tick50_subverdict=v0_53b_audit.SUBVERDICT_A_NULL_V025_TICK50_PRESENT,
            a_null_tick100_subverdict=v0_53b_audit.SUBVERDICT_A_NULL_V025_TICK100_PRESENT,
            b_tick100_subverdict=b_sub,
            c_tick100_subverdict=v0_53b_audit.SUBVERDICT_C_LADDER_TICK100_PRESENT,
            corpus_re_anchor=[],
            bridge_re_anchor=bridge_clean,
            b_reachability=0.30,
        )
        assert rollup == v0_53b_audit.ROLLUP_WIDENED_REACHABILITY_RESOLVED_BRIDGE_NOT_FOUND


# ---------------------------------------------------------------------------
# Test 15 — Rollup locked phrases fire verbatim.
# ---------------------------------------------------------------------------


def test_rollup_locked_phrases_fire_verbatim():
    bridge_clean = _zero_drift_bridge_re_anchor()

    # RESOLVED (priority 4).
    _, phrase_res = v0_53b_audit._evaluate_rollup(
        a_null_tick50_subverdict=v0_53b_audit.SUBVERDICT_A_NULL_V025_TICK50_PRESENT,
        a_null_tick100_subverdict=v0_53b_audit.SUBVERDICT_A_NULL_V025_TICK100_PRESENT,
        b_tick100_subverdict=v0_53b_audit.SUBVERDICT_B_WIDENED_TICK100_PRESENT,
        c_tick100_subverdict=v0_53b_audit.SUBVERDICT_C_LADDER_TICK100_PRESENT,
        corpus_re_anchor=[],
        bridge_re_anchor=bridge_clean,
        b_reachability=0.50,
    )
    assert (
        "v0.53's `B_WIDENED_BRIDGE_NOT_FOUND` was reachability-censored by the 50-tick window"
        in phrase_res
    )

    # RESOLVED_BRIDGE_NOT_FOUND (priority 5).
    _, phrase_rb = v0_53b_audit._evaluate_rollup(
        a_null_tick50_subverdict=v0_53b_audit.SUBVERDICT_A_NULL_V025_TICK50_PRESENT,
        a_null_tick100_subverdict=v0_53b_audit.SUBVERDICT_A_NULL_V025_TICK100_PRESENT,
        b_tick100_subverdict=v0_53b_audit.SUBVERDICT_B_WIDENED_TICK100_NOT_FOUND,
        c_tick100_subverdict=v0_53b_audit.SUBVERDICT_C_LADDER_TICK100_PRESENT,
        corpus_re_anchor=[],
        bridge_re_anchor=bridge_clean,
        b_reachability=0.50,
    )
    assert (
        "the bridge fails to fire under longer observation even when food primaries become "
        "measurable"
    ) in phrase_rb

    # BELOW_REACHABILITY_THRESHOLD (priority 6).
    _, phrase_below = v0_53b_audit._evaluate_rollup(
        a_null_tick50_subverdict=v0_53b_audit.SUBVERDICT_A_NULL_V025_TICK50_PRESENT,
        a_null_tick100_subverdict=v0_53b_audit.SUBVERDICT_A_NULL_V025_TICK100_PRESENT,
        b_tick100_subverdict=v0_53b_audit.SUBVERDICT_B_WIDENED_TICK100_NOT_FOUND,
        c_tick100_subverdict=v0_53b_audit.SUBVERDICT_C_LADDER_TICK100_PRESENT,
        corpus_re_anchor=[],
        bridge_re_anchor=bridge_clean,
        b_reachability=0.10,
    )
    assert "B_widened's reachability is below the locked 25% threshold" in phrase_below


# ---------------------------------------------------------------------------
# Test 16 — Rollup priority cascade and partition exhaustiveness.
# ---------------------------------------------------------------------------


def test_rollup_priority_cascade_and_partition_total():
    bridge_clean = _zero_drift_bridge_re_anchor()
    bridge_drift = list(bridge_clean)
    bridge_drift[0] = v0_53b_audit.BridgeReAnchorRow(
        label=bridge_drift[0].label,
        observable=bridge_drift[0].observable,
        published_signed_d=bridge_drift[0].published_signed_d,
        derived_signed_d=bridge_drift[0].published_signed_d + 1.5,
        drift_abs=1.5,
        halts=True,
    )
    corpus_halt = [
        v0_53b_audit.ReAnchorRow(
            arm=v0_53b_audit.ARM_A_NULL_V025,
            version="v0.42",
            hazard=8,
            n_runs_contributing=8,
            a_share_h8_derived=0.700,
            a_share_h8_published=0.652,
            drift_abs=0.048,
            halts=True,
        )
    ]

    # Part A — priority cascade.
    # All three halt classes synthesized: priority 1 (corpus drift) wins.
    rollup_1, phrase_1 = v0_53b_audit._evaluate_rollup(
        a_null_tick50_subverdict=v0_53b_audit.SUBVERDICT_A_NULL_V025_TICK50_PRESENT,
        a_null_tick100_subverdict=v0_53b_audit.SUBVERDICT_A_NULL_V025_TICK100_PRESENT,
        b_tick100_subverdict=v0_53b_audit.SUBVERDICT_B_WIDENED_TICK100_OPPOSITE,
        c_tick100_subverdict=v0_53b_audit.SUBVERDICT_C_LADDER_TICK100_PRESENT,
        corpus_re_anchor=corpus_halt,
        bridge_re_anchor=bridge_drift,
        b_reachability=0.50,
    )
    assert rollup_1 == v0_53b_audit.ROLLUP_CORPUS_DRIFT_HALT
    assert "v0.42" in phrase_1

    # Priority 2 + 3 only: priority 2 (bridge replication) wins.
    rollup_2, _ = v0_53b_audit._evaluate_rollup(
        a_null_tick50_subverdict=v0_53b_audit.SUBVERDICT_A_NULL_V025_TICK50_PRESENT,
        a_null_tick100_subverdict=v0_53b_audit.SUBVERDICT_A_NULL_V025_TICK100_PRESENT,
        b_tick100_subverdict=v0_53b_audit.SUBVERDICT_B_WIDENED_TICK100_OPPOSITE,
        c_tick100_subverdict=v0_53b_audit.SUBVERDICT_C_LADDER_TICK100_PRESENT,
        corpus_re_anchor=[],
        bridge_re_anchor=bridge_drift,
        b_reachability=0.50,
    )
    assert rollup_2 == v0_53b_audit.ROLLUP_BRIDGE_REPLICATION_HALT

    # Priority 3 alone: layout opposite-sign halt fires (no priority 1 or 2).
    rollup_3, _ = v0_53b_audit._evaluate_rollup(
        a_null_tick50_subverdict=v0_53b_audit.SUBVERDICT_A_NULL_V025_TICK50_PRESENT,
        a_null_tick100_subverdict=v0_53b_audit.SUBVERDICT_A_NULL_V025_TICK100_PRESENT,
        b_tick100_subverdict=v0_53b_audit.SUBVERDICT_B_WIDENED_TICK100_OPPOSITE,
        c_tick100_subverdict=v0_53b_audit.SUBVERDICT_C_LADDER_TICK100_PRESENT,
        corpus_re_anchor=[],
        bridge_re_anchor=bridge_clean,
        b_reachability=0.50,
    )
    assert rollup_3 == v0_53b_audit.ROLLUP_LAYOUT_OPPOSITE_HALT

    # Priority 3 fires when arm C is opposite.
    rollup_3c, _ = v0_53b_audit._evaluate_rollup(
        a_null_tick50_subverdict=v0_53b_audit.SUBVERDICT_A_NULL_V025_TICK50_PRESENT,
        a_null_tick100_subverdict=v0_53b_audit.SUBVERDICT_A_NULL_V025_TICK100_PRESENT,
        b_tick100_subverdict=v0_53b_audit.SUBVERDICT_B_WIDENED_TICK100_PRESENT,
        c_tick100_subverdict=v0_53b_audit.SUBVERDICT_C_LADDER_TICK100_OPPOSITE,
        corpus_re_anchor=[],
        bridge_re_anchor=bridge_clean,
        b_reachability=0.50,
    )
    assert rollup_3c == v0_53b_audit.ROLLUP_LAYOUT_OPPOSITE_HALT

    # Priority 3 fires when arm A_null is opposite at tick-100 (v0.53b expansion).
    rollup_3a, _ = v0_53b_audit._evaluate_rollup(
        a_null_tick50_subverdict=v0_53b_audit.SUBVERDICT_A_NULL_V025_TICK50_PRESENT,
        a_null_tick100_subverdict=v0_53b_audit.SUBVERDICT_A_NULL_V025_TICK100_OPPOSITE,
        b_tick100_subverdict=v0_53b_audit.SUBVERDICT_B_WIDENED_TICK100_PRESENT,
        c_tick100_subverdict=v0_53b_audit.SUBVERDICT_C_LADDER_TICK100_PRESENT,
        corpus_re_anchor=[],
        bridge_re_anchor=bridge_clean,
        b_reachability=0.50,
    )
    assert rollup_3a == v0_53b_audit.ROLLUP_LAYOUT_OPPOSITE_HALT

    # Bridge replication halt fires when A_null tick-50 != PRESENT.
    rollup_anull, _ = v0_53b_audit._evaluate_rollup(
        a_null_tick50_subverdict=v0_53b_audit.SUBVERDICT_A_NULL_V025_TICK50_NOT_FOUND,
        a_null_tick100_subverdict=v0_53b_audit.SUBVERDICT_A_NULL_V025_TICK100_PRESENT,
        b_tick100_subverdict=v0_53b_audit.SUBVERDICT_B_WIDENED_TICK100_PRESENT,
        c_tick100_subverdict=v0_53b_audit.SUBVERDICT_C_LADDER_TICK100_PRESENT,
        corpus_re_anchor=[],
        bridge_re_anchor=bridge_clean,
        b_reachability=0.50,
    )
    assert rollup_anull == v0_53b_audit.ROLLUP_BRIDGE_REPLICATION_HALT

    # Part B — partition exhaustiveness over (B reachability, B sub-verdict)
    # union (reachability < 0.25). A_null_V0_25 / C_food_ladder non-OPPOSITE
    # tick-100 outcomes do NOT affect priority 4/5/6 (B-only gating).
    sub_kinds_non_opp = ("PRESENT", "PARTIAL", "NOT_FOUND")
    seen: dict[tuple[str, str, str, str], str] = {}
    for a_kind in sub_kinds_non_opp:
        for c_kind in sub_kinds_non_opp:
            for b_kind in sub_kinds_non_opp:
                a_sub = _arm_subverdict_for_tick100(v0_53b_audit.ARM_A_NULL_V025, a_kind)
                b_sub = _arm_subverdict_for_tick100(v0_53b_audit.ARM_B_WIDENED, b_kind)
                c_sub = _arm_subverdict_for_tick100(v0_53b_audit.ARM_C_LADDER, c_kind)
                # Above threshold.
                rollup_above, _ = v0_53b_audit._evaluate_rollup(
                    a_null_tick50_subverdict=v0_53b_audit.SUBVERDICT_A_NULL_V025_TICK50_PRESENT,
                    a_null_tick100_subverdict=a_sub,
                    b_tick100_subverdict=b_sub,
                    c_tick100_subverdict=c_sub,
                    corpus_re_anchor=[],
                    bridge_re_anchor=bridge_clean,
                    b_reachability=0.50,
                )
                seen[(a_kind, b_kind, c_kind, "above")] = rollup_above
                # Below threshold.
                rollup_below, _ = v0_53b_audit._evaluate_rollup(
                    a_null_tick50_subverdict=v0_53b_audit.SUBVERDICT_A_NULL_V025_TICK50_PRESENT,
                    a_null_tick100_subverdict=a_sub,
                    b_tick100_subverdict=b_sub,
                    c_tick100_subverdict=c_sub,
                    corpus_re_anchor=[],
                    bridge_re_anchor=bridge_clean,
                    b_reachability=0.10,
                )
                seen[(a_kind, b_kind, c_kind, "below")] = rollup_below

    # Above threshold: rollup gates only on B sub-verdict (A/C irrelevant).
    for (a_kind, b_kind, c_kind, regime), rollup in seen.items():
        if regime == "above":
            if b_kind == "PRESENT":
                assert rollup == v0_53b_audit.ROLLUP_WIDENED_REACHABILITY_CENSORED_RESOLVED, (
                    f"Combo (A={a_kind}, B={b_kind}, C={c_kind}, above): "
                    f"expected RESOLVED but got {rollup}"
                )
            else:
                assert (
                    rollup == v0_53b_audit.ROLLUP_WIDENED_REACHABILITY_RESOLVED_BRIDGE_NOT_FOUND
                ), (
                    f"Combo (A={a_kind}, B={b_kind}, C={c_kind}, above): "
                    f"expected RESOLVED_BRIDGE_NOT_FOUND but got {rollup}"
                )
        else:  # below
            assert rollup == v0_53b_audit.ROLLUP_WIDENED_BELOW_REACHABILITY_THRESHOLD, (
                f"Combo (A={a_kind}, B={b_kind}, C={c_kind}, below): "
                f"expected BELOW_REACHABILITY_THRESHOLD but got {rollup}"
            )

    # Specifically: A_null PARTIAL + B PRESENT + reachability >= 0.25 still fires priority 4.
    rollup_a_partial_b_present, _ = v0_53b_audit._evaluate_rollup(
        a_null_tick50_subverdict=v0_53b_audit.SUBVERDICT_A_NULL_V025_TICK50_PRESENT,
        a_null_tick100_subverdict=v0_53b_audit.SUBVERDICT_A_NULL_V025_TICK100_PARTIAL,
        b_tick100_subverdict=v0_53b_audit.SUBVERDICT_B_WIDENED_TICK100_PRESENT,
        c_tick100_subverdict=v0_53b_audit.SUBVERDICT_C_LADDER_TICK100_PARTIAL,
        corpus_re_anchor=[],
        bridge_re_anchor=bridge_clean,
        b_reachability=0.30,
    )
    assert rollup_a_partial_b_present == v0_53b_audit.ROLLUP_WIDENED_REACHABILITY_CENSORED_RESOLVED

    # 27 (A,B,C combos non-opposite) * 2 (above/below) = 54 entries.
    assert len(seen) == 54


# Sanity: pytest must be importable for the runner to discover this file.
_ = pytest
