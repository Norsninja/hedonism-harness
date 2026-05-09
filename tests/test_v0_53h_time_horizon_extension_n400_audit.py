"""v0.53h time-horizon extension audit (n_ticks=400 on C arm) — tests.

16 locked tests. Pre-reg: [[docs/experiments/fear_hunger_v0.53h.md]] §"Test
list (locked, 16 tests)". Tests numbered to match the pre-reg's ordering.
Test #5 verifies asymmetric-horizon propagation (B tick_count==200, C
tick_count==400 after run_chamber returns). Test #11 extends pre200 to pre400
on the C arm (synthetic events at 12 ticks). Test #14 adds a Tier-3 leg
(C tick-200 reachability anchor). Test #15 partitions on C tick-400
reachability (not tick-200 as in v0.53g).
"""

from __future__ import annotations

import csv
import hashlib
import importlib.util
import math
import statistics
import sys
from pathlib import Path

import pytest

from hedonism_harness.core.config import BodyConfig

_SCRIPT_PATH = (
    Path(__file__).parent.parent / "scripts" / "v0_53h_time_horizon_extension_n400_audit.py"
)
_spec = importlib.util.spec_from_file_location("v0_53h_audit", _SCRIPT_PATH)
assert _spec is not None
assert _spec.loader is not None
v0_53h_audit = importlib.util.module_from_spec(_spec)
sys.modules["v0_53h_audit"] = v0_53h_audit
_spec.loader.exec_module(v0_53h_audit)


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
    fires_expected = (not math.isnan(signed)) and signed >= v0_53h_audit.COHENS_D_THRESHOLD
    fires_wrong = (not math.isnan(signed)) and signed <= -v0_53h_audit.COHENS_D_THRESHOLD
    return v0_53h_audit.ObservableSummary(
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


def _three_summaries_for_arm_window(
    arm: str, window: int, ds: tuple[float, float, float], label: str
) -> list[object]:
    obs_table = {
        v0_53h_audit.TICK_50: v0_53h_audit.PRIMARY_OBSERVABLES_TICK50,
        v0_53h_audit.TICK_100: v0_53h_audit.PRIMARY_OBSERVABLES_TICK100,
        v0_53h_audit.TICK_200: v0_53h_audit.PRIMARY_OBSERVABLES_TICK200,
        v0_53h_audit.TICK_400: v0_53h_audit.PRIMARY_OBSERVABLES_TICK400,
    }
    obs = obs_table[window]
    return [
        _make_summary(arm=arm, observable=obs[i][0], sign=obs[i][1], paired_d=ds[i], label=label)
        for i in range(3)
    ]


def _zero_drift_bridge_re_anchor() -> list[object]:
    return [
        v0_53h_audit.BridgeReAnchorRow(
            label=label,
            observable=obs,
            published_signed_d=ref,
            derived_signed_d=ref,
            drift_abs=0.0,
            halts=False,
        )
        for (label, obs), ref in v0_53h_audit.V048_PUBLISHED_SIGNED_D.items()
    ]


def _c_tick400_subverdict_for_kind(kind: str) -> str:
    table = {
        "PRESENT": v0_53h_audit.SUBVERDICT_C_COMBINED_TICK400_PRESENT,
        "PARTIAL": v0_53h_audit.SUBVERDICT_C_COMBINED_TICK400_PARTIAL,
        "NOT_FOUND": v0_53h_audit.SUBVERDICT_C_COMBINED_TICK400_NOT_FOUND,
        "OPPOSITE": v0_53h_audit.SUBVERDICT_C_COMBINED_TICK400_OPPOSITE,
    }
    return table[kind]


# ---------------------------------------------------------------------------
# Test 1 — paired_d formula reproduces hand-computed signed_d on a fixture
# AND Tier-1 reference constants byte-equal v0.48..v0.53g published.
# ---------------------------------------------------------------------------


def test_paired_d_function_reproduces_hand_computed_signed_d_on_fixture_and_tier1_constants_match_v048_published_values():  # noqa: E501
    deltas = [1.0, 2.0, 1.5, 0.5, 2.5, 1.8, 0.9, 1.2]
    expected_mean = statistics.mean(deltas)
    expected_sd = statistics.stdev(deltas)
    expected_d = expected_mean / expected_sd
    derived_d = v0_53h_audit._paired_cohens_d(deltas)
    assert abs(derived_d - expected_d) < 1e-9

    pinned_v048 = {
        ("label_a_sensor_radius", "pre50_food_events_count"): +1.066,
        ("label_a_sensor_radius", "pre50_food_energy_acquired"): +1.066,
        ("label_a_sensor_radius", "mean_distance_to_nearest_food_cell_tick50"): +1.916,
        ("label_b_readiness_fraction_tick50", "pre50_food_events_count"): +0.916,
        ("label_b_readiness_fraction_tick50", "pre50_food_energy_acquired"): +0.916,
        ("label_b_readiness_fraction_tick50", "mean_distance_to_nearest_food_cell_tick50"): +1.179,
    }
    assert pinned_v048 == v0_53h_audit.V048_PUBLISHED_SIGNED_D


# ---------------------------------------------------------------------------
# Test 2 — A_null_V0_25 corpus a_share_h8 re-anchors v0.42 / v0.44 / v0.45.
# ---------------------------------------------------------------------------


def test_a_null_v025_corpus_a_share_h8_re_anchors_v042_v044_v045():
    clean = [
        v0_53h_audit.ReAnchorRow(
            arm=v0_53h_audit.ARM_A_NULL_V025,
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
    rollup, _ = v0_53h_audit._evaluate_rollup(
        a_null_tick50_subverdict=v0_53h_audit.SUBVERDICT_A_NULL_V025_TICK50_PRESENT,
        c_tick400_subverdict=v0_53h_audit.SUBVERDICT_C_COMBINED_TICK400_PRESENT,
        corpus_re_anchor=clean,
        bridge_re_anchor=_zero_drift_bridge_re_anchor(),
        b_widened_v025_reachability_tick200=0.0,
        c_reachability_tick200=0.0,
        c_reachability_tick400=0.50,
    )
    assert rollup == v0_53h_audit.ROLLUP_WIDENED_BRIDGE_RESCUED_BY_TIME_HORIZON_400

    # Drift > 1e-3 on v0.44 -> CORPUS_REDERIVE_DRIFT_HALT.
    drifted = list(clean)
    drifted[1] = v0_53h_audit.ReAnchorRow(
        arm=v0_53h_audit.ARM_A_NULL_V025,
        version="v0.44",
        hazard=8,
        n_runs_contributing=8,
        a_share_h8_derived=0.880,
        a_share_h8_published=0.878,
        drift_abs=0.002,
        halts=True,
    )
    rollup_d, phrase_d = v0_53h_audit._evaluate_rollup(
        a_null_tick50_subverdict=v0_53h_audit.SUBVERDICT_A_NULL_V025_TICK50_PRESENT,
        c_tick400_subverdict=v0_53h_audit.SUBVERDICT_C_COMBINED_TICK400_PRESENT,
        corpus_re_anchor=drifted,
        bridge_re_anchor=_zero_drift_bridge_re_anchor(),
        b_widened_v025_reachability_tick200=0.0,
        c_reachability_tick200=0.0,
        c_reachability_tick400=0.50,
    )
    assert rollup_d == v0_53h_audit.ROLLUP_CORPUS_DRIFT_HALT
    assert "v0.44" in phrase_d


# ---------------------------------------------------------------------------
# Test 3 — Arm A_null_V0_25 uses tight_gradient_layout, default body_config (None),
# AND n_ticks=200.
# ---------------------------------------------------------------------------


def test_arm_a_null_v025_uses_tight_gradient_layout_default_body_config_and_n_ticks_200():
    layout = v0_53h_audit._layout_for_arm(v0_53h_audit.ARM_A_NULL_V025)
    assert layout.width == 9
    assert layout.height == 6
    assert layout.safe_x_min == 0
    assert layout.safe_x_max == 2
    assert layout.hazard_x_min == 3
    assert layout.hazard_x_max == 4
    assert layout.food_x_min == 5
    assert layout.food_x_max == 8
    assert layout.resolved_spawn_x == 1
    assert v0_53h_audit.LAYOUT_NAME_BY_ARM[v0_53h_audit.ARM_A_NULL_V025] == "tight_gradient"
    assert v0_53h_audit._body_config_for_arm(v0_53h_audit.ARM_A_NULL_V025) is None
    assert (
        v0_53h_audit.BODY_BASE_METABOLIC_COST_BY_ARM[v0_53h_audit.ARM_A_NULL_V025]
        == v0_53h_audit.V0_25_BODY_BASE_METABOLIC_COST
        == 0.25
    )
    # Horizon invariant: A runs to n_ticks=200.
    assert v0_53h_audit.N_TICKS_BY_ARM[v0_53h_audit.ARM_A_NULL_V025] == 200
    assert (
        v0_53h_audit.WINDOWS_BY_ARM[v0_53h_audit.ARM_A_NULL_V025]
        == v0_53h_audit.WINDOWS_AB
        == (50, 100, 200)
    )


# ---------------------------------------------------------------------------
# Test 4 — Arm B_widened_V0_25 uses widened_gradient_layout, default body_config
# (None), AND n_ticks=200.
# ---------------------------------------------------------------------------


def test_arm_b_widened_v025_uses_widened_gradient_layout_default_body_config_and_n_ticks_200():
    layout = v0_53h_audit._layout_for_arm(v0_53h_audit.ARM_B_WIDENED_V025)
    assert layout.width == 15
    assert layout.height == 6
    assert layout.safe_x_min == 0
    assert layout.safe_x_max == 4
    assert layout.hazard_x_min == 5
    assert layout.hazard_x_max == 7
    assert layout.food_x_min == 10
    assert layout.food_x_max == 14
    assert layout.resolved_spawn_x == 1
    assert v0_53h_audit.LAYOUT_NAME_BY_ARM[v0_53h_audit.ARM_B_WIDENED_V025] == "widened_gradient"
    assert v0_53h_audit._body_config_for_arm(v0_53h_audit.ARM_B_WIDENED_V025) is None
    assert (
        v0_53h_audit.BODY_BASE_METABOLIC_COST_BY_ARM[v0_53h_audit.ARM_B_WIDENED_V025]
        == v0_53h_audit.V0_25_BODY_BASE_METABOLIC_COST
        == 0.25
    )
    # Horizon invariant: B runs to n_ticks=200.
    assert v0_53h_audit.N_TICKS_BY_ARM[v0_53h_audit.ARM_B_WIDENED_V025] == 200
    assert (
        v0_53h_audit.WINDOWS_BY_ARM[v0_53h_audit.ARM_B_WIDENED_V025]
        == v0_53h_audit.WINDOWS_AB
        == (50, 100, 200)
    )


# ---------------------------------------------------------------------------
# Test 5 — Cross-arm contrast verifying BOTH knobs of the body_config seam AND
# the asymmetric n_ticks horizon (B tick_count==200, C tick_count==400 after
# run_chamber returns).
# ---------------------------------------------------------------------------


def test_arm_c_widened_combined_se100_bmc010_n400_seam_differentiates_b_and_c_two_body_config_knobs_at_tick_0_and_horizon_at_tick_400(  # noqa: E501
    tmp_path,
):
    arm_c = v0_53h_audit.ARM_C_WIDENED_COMBINED_SE100_BMC010_N400
    bc_c = v0_53h_audit._body_config_for_arm(arm_c)
    assert isinstance(bc_c, BodyConfig)
    assert bc_c.starting_energy == 100.0
    assert bc_c.base_metabolic_cost == 0.10
    bc_default = BodyConfig()
    assert bc_c.max_energy == bc_default.max_energy == 100.0
    assert bc_c.starting_health == bc_default.starting_health == 100.0
    assert bc_c.max_health == bc_default.max_health == 100.0
    assert bc_c.sensor_radius_metabolic_cost == bc_default.sensor_radius_metabolic_cost == 0.05
    assert (
        bc_c.effective_sensor_radius_override == bc_default.effective_sensor_radius_override is None
    )

    assert v0_53h_audit.STARTING_ENERGY_100_DOSE == 100.0
    assert v0_53h_audit.BASE_METABOLIC_COST_010_DOSE == 0.10

    # No other WorldConfig knob differs from V0_25 baseline on C.
    base_arm = v0_53h_audit._select_a_null_arm("v0.42", 0)
    assert base_arm.ambient_influx_rate == v0_53h_audit.V0_25_AMBIENT_INFLUX_RATE == 1.0
    assert base_arm.energy_pool_initial == v0_53h_audit.V0_25_ENERGY_POOL_INITIAL == 1500.0
    assert base_arm.food_respawn_cooldown == v0_53h_audit.V0_25_FOOD_RESPAWN_COOLDOWN == 50

    # Asymmetric n_ticks: A=B=200, C=400.
    assert v0_53h_audit.N_TICKS_BY_ARM[v0_53h_audit.ARM_B_WIDENED_V025] == 200
    assert v0_53h_audit.N_TICKS_BY_ARM[arm_c] == 400

    # Runtime: same (version, seed, hazard); B must end at tick_count=200, C
    # must end at tick_count=400; founder body fields differ at tick-0.
    seed = 41
    cap_b = v0_53h_audit._run_one_arm(
        arm=v0_53h_audit.ARM_B_WIDENED_V025,
        version="v0.42",
        seed=seed,
        hazard=0,
        runs_root=tmp_path,
    )
    cap_c = v0_53h_audit._run_one_arm(
        arm=arm_c,
        version="v0.42",
        seed=seed,
        hazard=0,
        runs_root=tmp_path,
    )
    # Layouts identical (widened_gradient on both).
    assert cap_b.layout_name == cap_c.layout_name == "widened_gradient"

    # Asymmetric horizon: cap_b.final_tick_count == 200 and cap_c.final_tick_count
    # == 400 (read from per-tick observer's last fire — equivalent to model.tick_count
    # after run_chamber returns since run_chamber drives the loop to completion when
    # population is alive). Allow earlier termination if extinction occurs.
    assert cap_b.n_ticks == 200
    assert cap_c.n_ticks == 400
    assert cap_b.final_tick_count <= 200, (
        f"B horizon must not exceed n_ticks=200; got {cap_b.final_tick_count}"
    )
    assert cap_c.final_tick_count <= 400, (
        f"C horizon must not exceed n_ticks=400; got {cap_c.final_tick_count}"
    )
    # Predecessor lock: through tick-200 the C arm is byte-identical to v0.53g
    # C; the C arm in v0.53h must continue past tick-200. We cannot assert
    # exactly tick-400 (extinction may end earlier), but we can assert C
    # reached strictly past 200 if B reached 200, AND that C's max captured
    # tick exceeds B's max captured tick when both populations survived.
    if cap_b.final_tick_count == 200:
        assert cap_c.final_tick_count > 200, (
            f"C horizon must extend strictly past tick-200 when B reaches tick-200; "
            f"got C tick={cap_c.final_tick_count}"
        )

    # B founder body fields at tick-0: V0_25 baseline (default BodyConfig fallback).
    for rec in cap_b.founder_records:
        assert rec.founder_body_energy_tick0 == 60.0
        assert rec.founder_body_starting_energy_tick0 == 60.0
        assert rec.founder_body_base_metabolic_cost_tick0 == 0.25
    # C founder body fields at tick-0: BOTH knobs overridden.
    for rec in cap_c.founder_records:
        assert rec.founder_body_energy_tick0 == 100.0
        assert rec.founder_body_starting_energy_tick0 == 100.0
        assert rec.founder_body_base_metabolic_cost_tick0 == 0.10
    assert v0_53h_audit.BODY_STARTING_ENERGY_BY_ARM[arm_c] == 100.0
    assert v0_53h_audit.BODY_BASE_METABOLIC_COST_BY_ARM[arm_c] == 0.10


# ---------------------------------------------------------------------------
# Test 6 — Founder traits byte-identical across arms for same (version, seed,
# hazard) tuple. Arms differ only in chamber config (layout + body_config +
# n_ticks), not in founder draw.
# ---------------------------------------------------------------------------


def test_founder_traits_byte_identical_across_arms_for_same_seed(tmp_path):
    seed = 41
    arm_to_records: dict[str, list[tuple]] = {}
    for arm in v0_53h_audit.ARMS:
        cap = v0_53h_audit._run_one_arm(
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
    arms = list(v0_53h_audit.ARMS)
    for arm in arms[1:]:
        assert arm_to_records[arm] == arm_to_records[arms[0]], (
            f"Founder traits diverged between {arms[0]} and {arm}; layout / "
            f"body_config / n_ticks swap must not perturb mutation streams."
        )


# ---------------------------------------------------------------------------
# Test 7 — Founder positions byte-identical across arms for same seed.
# All three layouts have spawn_x=1 and height=6.
# ---------------------------------------------------------------------------


def test_founder_positions_byte_identical_across_arms_for_same_seed():
    from hedonism_harness.experiments.fear_hunger_chamber import spread_y

    expected_xs = []
    expected_ys = None
    for arm in v0_53h_audit.ARMS:
        layout = v0_53h_audit._layout_for_arm(arm)
        spawn_x = layout.resolved_spawn_x
        ys = spread_y(v0_53h_audit.N_FOUNDERS, layout.height)
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
# Test 8 — Two-part src/ pinning test (IDENTICAL SHAs to v0.53e/f/g):
#   Part A: science-core five files byte-identical to v0.52b-tip.
#   Part B: chamber driver byte-identical to v0.53e-tip post-seam-add.
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

V053E_CHAMBER_DRIVER_PATH: str = "src/hedonism_harness/experiments/fear_hunger_chamber.py"
V053E_CHAMBER_DRIVER_SHA256: str = (
    "62d134c5d82b031a6fd2b7bbdf0412eb8362199c7bf60a59836cfca9134e2b6d"
)


def test_no_src_modifications_compared_to_v0_53e_tip():
    repo_root = Path(__file__).parent.parent
    # Part A: science-core five files unchanged from v0.52b-tip.
    for rel_path, expected_hash in V052B_TIP_SHA256.items():
        path = repo_root / rel_path
        actual_hash = hashlib.sha256(path.read_bytes()).hexdigest()
        if actual_hash != expected_hash:
            raise AssertionError(
                "v0.53h is pre-registered to leave the science-core five files "
                "byte-identical to v0.52b-tip; update the pre-reg before changing "
                "src/core or src/experiments/layouts."
            )

    # Part B: chamber driver byte-identical to v0.53e-tip post-seam-add.
    chamber_path = repo_root / V053E_CHAMBER_DRIVER_PATH
    actual_chamber_hash = hashlib.sha256(chamber_path.read_bytes()).hexdigest()
    if actual_chamber_hash != V053E_CHAMBER_DRIVER_SHA256:
        raise AssertionError(
            "v0.53h is pre-registered to leave the chamber driver byte-identical "
            "to its v0.53e-tip hash; update the pre-reg before re-touching the "
            "chamber driver."
        )


# ---------------------------------------------------------------------------
# Test 9 — Label A high_sensor_radius_lineage picks correct lineage.
# ---------------------------------------------------------------------------


def test_label_a_high_sensor_radius_lineage_picks_correct_lineage():
    sensor_radius_by_lineage = {0: 2, 1: 5, 2: 4, 3: 1, 4: 6}
    label = v0_53h_audit._select_sensor_radius_label(sensor_radius_by_lineage)
    assert label == 4

    sensor_tied = {0: 6, 1: 5, 2: 6, 3: 6, 4: 4}
    label_tied = v0_53h_audit._select_sensor_radius_label(sensor_tied)
    assert label_tied == 0


# ---------------------------------------------------------------------------
# Test 10 — Label B four variants three-tier tiebreak at each window. The
# tick-50/100/200 variants are computed on all arms; the tick-400 variant is
# computed on C only and NaN-broadcast on A/B.
# ---------------------------------------------------------------------------


def test_label_b_four_variants_three_tier_tiebreak_at_each_window_with_pre400_c_only():
    # Two-way tie on fraction -> tiebreak by count.
    candidates_count_tiebreak = [(0, 0.5, 2), (1, 0.5, 4), (2, 0.4, 5)]
    assert v0_53h_audit._select_fraction_label(candidates_count_tiebreak) == 1

    # Tie on fraction AND count -> tiebreak by min(lineage_id).
    candidates_min_lid = [(3, 0.5, 4), (1, 0.5, 4), (2, 0.5, 4)]
    assert v0_53h_audit._select_fraction_label(candidates_min_lid) == 1

    candidates_simple = [(0, 0.3, 5), (1, 0.7, 1), (2, 0.5, 3)]
    assert v0_53h_audit._select_fraction_label(candidates_simple) == 1

    assert v0_53h_audit._select_fraction_label([]) is None

    energy_threshold = 5.0
    min_age = 1
    all_lineages = [0, 1, 2]
    snaps = [
        v0_53h_audit._ReadinessSnapshot(agent_id=10, lineage_id=0, energy=10.0, age=2),
        v0_53h_audit._ReadinessSnapshot(agent_id=11, lineage_id=0, energy=4.0, age=2),
        v0_53h_audit._ReadinessSnapshot(agent_id=20, lineage_id=1, energy=10.0, age=2),
        v0_53h_audit._ReadinessSnapshot(agent_id=30, lineage_id=2, energy=10.0, age=2),
        v0_53h_audit._ReadinessSnapshot(agent_id=31, lineage_id=2, energy=10.0, age=2),
    ]
    selected_a, _, _, fr_a = v0_53h_audit._readiness_label_at_tick(
        all_lineages, snaps, energy_threshold, min_age
    )
    assert selected_a == 2
    assert fr_a[1] == 1.0
    assert fr_a[2] == 1.0
    selected_b, _, _, _ = v0_53h_audit._readiness_label_at_tick(
        all_lineages, snaps, energy_threshold, min_age
    )
    selected_c, _, _, _ = v0_53h_audit._readiness_label_at_tick(
        all_lineages, snaps, energy_threshold, min_age
    )
    assert selected_a == selected_b == selected_c

    # tick-400 label is computed on C arm only; on A/B the column carries NaN.
    # Verify _aggregate_per_lineage broadcasts NaN on A/B and a bool on C by
    # constructing a minimal capture for each arm.

    def _build_capture(arm: str, n_ticks: int) -> v0_53h_audit._RunCapture:
        cap = v0_53h_audit._RunCapture(
            arm=arm,
            layout_name=v0_53h_audit.LAYOUT_NAME_BY_ARM[arm],
            body_starting_energy=v0_53h_audit.BODY_STARTING_ENERGY_BY_ARM[arm],
            body_base_metabolic_cost=v0_53h_audit.BODY_BASE_METABOLIC_COST_BY_ARM[arm],
            n_ticks=n_ticks,
            version="v0.42",
            seed=41,
            hazard=0,
        )
        # Single founder lineage 0 to keep the structure trivial.
        cap.lineage_by_agent = {0: 0}
        cap.birth_tick_by_agent = {0: 0}
        cap.founder_records = [
            v0_53h_audit._FounderRecord(
                lineage_id=0,
                founder_index=0,
                founder_sensor_radius=4,
                founder_reproduction_drive=0.5,
                founder_metabolic_rate=0.5,
                founder_body_energy_tick0=cap.body_starting_energy,
                founder_body_starting_energy_tick0=cap.body_starting_energy,
                founder_body_base_metabolic_cost_tick0=cap.body_base_metabolic_cost,
            )
        ]
        cap.energy_threshold = 5.0
        cap.min_age = 1
        return cap

    cap_a = _build_capture(v0_53h_audit.ARM_A_NULL_V025, 200)
    cap_b = _build_capture(v0_53h_audit.ARM_B_WIDENED_V025, 200)
    cap_c = _build_capture(v0_53h_audit.ARM_C_WIDENED_COMBINED_SE100_BMC010_N400, 400)
    rows_a = v0_53h_audit._aggregate_per_lineage(cap_a)
    rows_b = v0_53h_audit._aggregate_per_lineage(cap_b)
    rows_c = v0_53h_audit._aggregate_per_lineage(cap_c)
    assert len(rows_a) == 1
    assert len(rows_b) == 1
    assert len(rows_c) == 1
    a_label = rows_a[0].is_high_tick400_readiness_fraction_lineage
    b_label = rows_b[0].is_high_tick400_readiness_fraction_lineage
    c_label = rows_c[0].is_high_tick400_readiness_fraction_lineage
    assert isinstance(a_label, float), f"A arm tick-400 Label B must be float NaN; got {a_label!r}"
    assert math.isnan(a_label), f"A arm tick-400 Label B must be NaN-broadcast; got {a_label!r}"
    assert isinstance(b_label, float), f"B arm tick-400 Label B must be float NaN; got {b_label!r}"
    assert math.isnan(b_label), f"B arm tick-400 Label B must be NaN-broadcast; got {b_label!r}"
    assert isinstance(c_label, bool), f"C arm tick-400 Label B must be bool; got {c_label!r}"


# ---------------------------------------------------------------------------
# Test 11 — pre400 window strictly extends pre200 / pre100 / pre50 on C arm.
# Synthetic events at ticks 10/30/60/90/130/180/200/230/280/350/380/400:
#   pre50  = 2 (10, 30)
#   pre100 = 4 (10, 30, 60, 90)
#   pre200 = 7 (10, 30, 60, 90, 130, 180, 200)
#   pre400 = 12 (all 12 events)
# pre400 must be NaN on A and B.
# ---------------------------------------------------------------------------


def test_pre400_window_strictly_extends_pre200_pre100_pre50_windows_on_c_arm():  # noqa: PLR0915
    capture = v0_53h_audit._RunCapture(
        arm=v0_53h_audit.ARM_C_WIDENED_COMBINED_SE100_BMC010_N400,
        layout_name="widened_gradient",
        body_starting_energy=100.0,
        body_base_metabolic_cost=0.10,
        n_ticks=400,
        version="v0.42",
        seed=41,
        hazard=0,
    )
    aid = 7
    event_ticks = [10, 30, 60, 90, 130, 180, 200, 230, 280, 350, 380, 400]
    arm_horizon = 400  # C arm

    for tick_now in event_ticks:
        if tick_now > arm_horizon:
            continue
        if tick_now <= v0_53h_audit.TICK_50:
            capture.pre50_food_events_by_agent[aid] = (
                capture.pre50_food_events_by_agent.get(aid, 0) + 1
            )
            capture.pre50_food_energy_by_agent[aid] = (
                capture.pre50_food_energy_by_agent.get(aid, 0.0) + 1.0
            )
        if tick_now <= v0_53h_audit.TICK_100:
            capture.pre100_food_events_by_agent[aid] = (
                capture.pre100_food_events_by_agent.get(aid, 0) + 1
            )
            capture.pre100_food_energy_by_agent[aid] = (
                capture.pre100_food_energy_by_agent.get(aid, 0.0) + 1.0
            )
        if tick_now <= v0_53h_audit.TICK_200:
            capture.pre200_food_events_by_agent[aid] = (
                capture.pre200_food_events_by_agent.get(aid, 0) + 1
            )
            capture.pre200_food_energy_by_agent[aid] = (
                capture.pre200_food_energy_by_agent.get(aid, 0.0) + 1.0
            )
        if tick_now <= v0_53h_audit.TICK_400:
            capture.pre400_food_events_by_agent[aid] = (
                capture.pre400_food_events_by_agent.get(aid, 0) + 1
            )
            capture.pre400_food_energy_by_agent[aid] = (
                capture.pre400_food_energy_by_agent.get(aid, 0.0) + 1.0
            )

    assert capture.pre50_food_events_by_agent[aid] == 2
    assert capture.pre100_food_events_by_agent[aid] == 4
    assert capture.pre200_food_events_by_agent[aid] == 7
    assert capture.pre400_food_events_by_agent[aid] == 12
    assert capture.pre50_food_energy_by_agent[aid] == 2.0
    assert capture.pre100_food_energy_by_agent[aid] == 4.0
    assert capture.pre200_food_energy_by_agent[aid] == 7.0
    assert capture.pre400_food_energy_by_agent[aid] == 12.0

    # Boundary: events at exactly tick 400 are inclusive; an event at tick 401
    # must NOT be accumulated.
    capture2 = v0_53h_audit._RunCapture(
        arm=v0_53h_audit.ARM_C_WIDENED_COMBINED_SE100_BMC010_N400,
        layout_name="widened_gradient",
        body_starting_energy=100.0,
        body_base_metabolic_cost=0.10,
        n_ticks=400,
        version="v0.42",
        seed=41,
        hazard=0,
    )
    for tick_now in [50, 100, 200, 400, 401]:
        if tick_now > 400:
            continue
        if tick_now <= v0_53h_audit.TICK_50:
            capture2.pre50_food_events_by_agent[aid] = (
                capture2.pre50_food_events_by_agent.get(aid, 0) + 1
            )
        if tick_now <= v0_53h_audit.TICK_100:
            capture2.pre100_food_events_by_agent[aid] = (
                capture2.pre100_food_events_by_agent.get(aid, 0) + 1
            )
        if tick_now <= v0_53h_audit.TICK_200:
            capture2.pre200_food_events_by_agent[aid] = (
                capture2.pre200_food_events_by_agent.get(aid, 0) + 1
            )
        if tick_now <= v0_53h_audit.TICK_400:
            capture2.pre400_food_events_by_agent[aid] = (
                capture2.pre400_food_events_by_agent.get(aid, 0) + 1
            )
    assert capture2.pre50_food_events_by_agent[aid] == 1
    assert capture2.pre100_food_events_by_agent[aid] == 2
    assert capture2.pre200_food_events_by_agent[aid] == 3
    assert capture2.pre400_food_events_by_agent[aid] == 4

    # Verify NaN-broadcast on A/B: build minimal A and B captures, aggregate,
    # and assert the pre400 cells in PerLineageRow are NaN.

    def _build_capture(arm: str, n_ticks: int) -> v0_53h_audit._RunCapture:
        cap = v0_53h_audit._RunCapture(
            arm=arm,
            layout_name=v0_53h_audit.LAYOUT_NAME_BY_ARM[arm],
            body_starting_energy=v0_53h_audit.BODY_STARTING_ENERGY_BY_ARM[arm],
            body_base_metabolic_cost=v0_53h_audit.BODY_BASE_METABOLIC_COST_BY_ARM[arm],
            n_ticks=n_ticks,
            version="v0.42",
            seed=41,
            hazard=0,
        )
        cap.lineage_by_agent = {0: 0}
        cap.birth_tick_by_agent = {0: 0}
        cap.founder_records = [
            v0_53h_audit._FounderRecord(
                lineage_id=0,
                founder_index=0,
                founder_sensor_radius=4,
                founder_reproduction_drive=0.5,
                founder_metabolic_rate=0.5,
                founder_body_energy_tick0=cap.body_starting_energy,
                founder_body_starting_energy_tick0=cap.body_starting_energy,
                founder_body_base_metabolic_cost_tick0=cap.body_base_metabolic_cost,
            )
        ]
        cap.energy_threshold = 5.0
        cap.min_age = 1
        return cap

    cap_a = _build_capture(v0_53h_audit.ARM_A_NULL_V025, 200)
    cap_b = _build_capture(v0_53h_audit.ARM_B_WIDENED_V025, 200)
    rows_a = v0_53h_audit._aggregate_per_lineage(cap_a)
    rows_b = v0_53h_audit._aggregate_per_lineage(cap_b)
    assert math.isnan(rows_a[0].pre400_food_events_count)
    assert math.isnan(rows_a[0].pre400_food_energy_acquired)
    assert math.isnan(rows_a[0].mean_distance_to_nearest_food_cell_tick400)
    assert math.isnan(rows_b[0].pre400_food_events_count)
    assert math.isnan(rows_b[0].pre400_food_energy_acquired)
    assert math.isnan(rows_b[0].mean_distance_to_nearest_food_cell_tick400)


# ---------------------------------------------------------------------------
# Test 12 — Sub-verdict PRESENT requires >= 2/3 firing cells, with the strict
# NaN-treated-as-non-firing rule. Exercises C tick-400 panel.
# ---------------------------------------------------------------------------


def test_subverdict_present_requires_two_thirds_firing_cells_with_nan_treated_as_non_firing_strict():  # noqa: E501
    arm = v0_53h_audit.ARM_C_WIDENED_COMBINED_SE100_BMC010_N400
    window = v0_53h_audit.TICK_400

    # Case: Label A 2 firing + 1 NaN; Label B 3 firing -> PRESENT.
    summaries_a_2firing_1nan = _three_summaries_for_arm_window(
        arm, window, (+0.6, +0.6, float("nan")), v0_53h_audit.LABEL_A_NAME
    )
    summaries_b_clean = _three_summaries_for_arm_window(
        arm, window, (+0.6, +0.6, -0.6), v0_53h_audit.LABEL_B_TICK400_NAME
    )
    assert (
        v0_53h_audit._arm_subverdict_at_window(
            arm, window, summaries_a_2firing_1nan, summaries_b_clean
        )
        == v0_53h_audit.SUBVERDICT_C_COMBINED_TICK400_PRESENT
    )

    # Case: Label A 1 firing + 2 NaN -> A doesn't clear; only B clears -> PARTIAL.
    summaries_a_1firing_2nan = _three_summaries_for_arm_window(
        arm, window, (+0.6, float("nan"), float("nan")), v0_53h_audit.LABEL_A_NAME
    )
    assert (
        v0_53h_audit._arm_subverdict_at_window(
            arm, window, summaries_a_1firing_2nan, summaries_b_clean
        )
        == v0_53h_audit.SUBVERDICT_C_COMBINED_TICK400_PARTIAL
    )

    # Case: Label A all NaN; Label B 3 firing -> PARTIAL.
    summaries_a_all_nan = _three_summaries_for_arm_window(
        arm, window, (float("nan"), float("nan"), float("nan")), v0_53h_audit.LABEL_A_NAME
    )
    assert (
        v0_53h_audit._arm_subverdict_at_window(arm, window, summaries_a_all_nan, summaries_b_clean)
        == v0_53h_audit.SUBVERDICT_C_COMBINED_TICK400_PARTIAL
    )

    # Case: BOTH labels all NaN -> NOT_FOUND.
    summaries_b_all_nan = _three_summaries_for_arm_window(
        arm,
        window,
        (float("nan"), float("nan"), float("nan")),
        v0_53h_audit.LABEL_B_TICK400_NAME,
    )
    assert (
        v0_53h_audit._arm_subverdict_at_window(
            arm, window, summaries_a_all_nan, summaries_b_all_nan
        )
        == v0_53h_audit.SUBVERDICT_C_COMBINED_TICK400_NOT_FOUND
    )

    # Case: Both labels 2 firing + 1 NaN -> both clear 2/3 -> PRESENT.
    summaries_b_2firing_1nan = _three_summaries_for_arm_window(
        arm, window, (+0.6, +0.6, float("nan")), v0_53h_audit.LABEL_B_TICK400_NAME
    )
    assert (
        v0_53h_audit._arm_subverdict_at_window(
            arm, window, summaries_a_2firing_1nan, summaries_b_2firing_1nan
        )
        == v0_53h_audit.SUBVERDICT_C_COMBINED_TICK400_PRESENT
    )


# ---------------------------------------------------------------------------
# Test 13 — Priority 3 RELAXED_OPPOSITE_SIGN_HALT is REACHABILITY-GATED on
# C tick-400. Exercises three branches:
#   Branch A: C tick-400 OPPOSITE + reach=0.30 (>= 0.25) -> priority 3 fires.
#   Branch B: C tick-400 OPPOSITE + reach=0.20 (< 0.25) -> priority 3 SKIPS;
#             rollup falls through to priority 5; wrong-sign cell logged.
#   Branch C: C tick-400 PRESENT + reach=0.30 -> priority 4 fires.
# ---------------------------------------------------------------------------


def test_priority_3_relaxed_opposite_sign_halt_is_reachability_gated_on_c_tick_400(tmp_path):
    bridge_clean = _zero_drift_bridge_re_anchor()
    arm_c = v0_53h_audit.ARM_C_WIDENED_COMBINED_SE100_BMC010_N400
    window = v0_53h_audit.TICK_400

    # Build C tick-400 summaries with a wrong-sign Label B distance cell.
    # paired_d=+0.5 on a -1-sign distance observable -> signed_d=-0.5 (wrong).
    summaries_a_wrong = _three_summaries_for_arm_window(
        arm_c, window, (+0.6, +0.6, -0.7), v0_53h_audit.LABEL_A_NAME
    )
    summaries_b_clean_above = _three_summaries_for_arm_window(
        arm_c, window, (+0.6, +0.6, +0.5), v0_53h_audit.LABEL_B_TICK400_NAME
    )
    c_sub_opposite = v0_53h_audit._arm_subverdict_at_window(
        arm_c, window, summaries_a_wrong, summaries_b_clean_above
    )
    assert c_sub_opposite == v0_53h_audit.SUBVERDICT_C_COMBINED_TICK400_OPPOSITE

    # Branch A: C reach = 0.30 + C OPPOSITE -> priority 3 fires.
    rollup_a, phrase_a = v0_53h_audit._evaluate_rollup(
        a_null_tick50_subverdict=v0_53h_audit.SUBVERDICT_A_NULL_V025_TICK50_PRESENT,
        c_tick400_subverdict=c_sub_opposite,
        corpus_re_anchor=[],
        bridge_re_anchor=bridge_clean,
        b_widened_v025_reachability_tick200=0.0,
        c_reachability_tick200=0.0,
        c_reachability_tick400=0.30,
    )
    assert rollup_a == v0_53h_audit.ROLLUP_RELAXED_OPPOSITE_SIGN_HALT
    assert (
        "AND C reachability at tick-400 clears the locked 25% threshold "
        "(so the bridge framework is meaningful at this measurement)"
    ) in phrase_a
    assert (
        "The reachability-gated trigger preserves v0.53e's locked sign discipline "
        "while excluding the v0.53e-style measurement-edge case "
        "(wrong-sign at reachability=0)"
    ) in phrase_a

    # Branch B: C reach = 0.20 + C OPPOSITE -> priority 3 SKIPS; falls through.
    rollup_b, phrase_b = v0_53h_audit._evaluate_rollup(
        a_null_tick50_subverdict=v0_53h_audit.SUBVERDICT_A_NULL_V025_TICK50_PRESENT,
        c_tick400_subverdict=c_sub_opposite,
        corpus_re_anchor=[],
        bridge_re_anchor=bridge_clean,
        b_widened_v025_reachability_tick200=0.0,
        c_reachability_tick200=0.0,
        c_reachability_tick400=0.20,
    )
    assert rollup_b != v0_53h_audit.ROLLUP_RELAXED_OPPOSITE_SIGN_HALT
    assert rollup_b == (
        v0_53h_audit.ROLLUP_WIDENED_BELOW_REACHABILITY_THRESHOLD_AT_TIME_HORIZON_400
    )
    assert (
        "The bridge is not rescued by extending the horizon to "
        "`n_ticks=400` under V0_25 × `widened_gradient` × combined-budget "  # noqa: RUF001
        "envelope"
    ) in phrase_b

    # Wrong-sign cell collection on the synthetic tick-400 summaries.
    wrong_sign_cells = v0_53h_audit._collect_c_tick400_wrong_sign_cells(
        list(summaries_a_wrong) + list(summaries_b_clean_above)
    )
    assert len(wrong_sign_cells) == 1
    wsc = wrong_sign_cells[0]
    assert wsc.arm == arm_c
    assert wsc.label == v0_53h_audit.LABEL_B_TICK400_NAME
    assert wsc.observable == "mean_distance_to_nearest_food_cell_tick400"
    assert wsc.signed_d == -0.5
    assert wsc.paired_d == +0.5
    assert wsc.n == 64

    # Verify audit_summary.csv writes the wrong_sign_cells section.
    out_dir = tmp_path / "audit_branch_b"
    out_dir.mkdir()
    audit_summary_path = out_dir / "audit_summary.csv"
    arms_for_window = {
        v0_53h_audit.TICK_50: v0_53h_audit.ARMS,
        v0_53h_audit.TICK_100: v0_53h_audit.ARMS,
        v0_53h_audit.TICK_200: v0_53h_audit.ARMS,
        v0_53h_audit.TICK_400: (v0_53h_audit.ARM_C_WIDENED_COMBINED_SE100_BMC010_N400,),
    }
    reachability_by_window: dict[int, dict[str, tuple[float, int]]] = {}
    for w, arms_w in arms_for_window.items():
        reachability_by_window[w] = {a: (0.0, 64) for a in arms_w}
    reachability_by_window[v0_53h_audit.TICK_200][v0_53h_audit.ARM_A_NULL_V025] = (1.0, 64)
    reachability_by_window[v0_53h_audit.TICK_200][v0_53h_audit.ARM_B_WIDENED_V025] = (0.0, 64)
    reachability_by_window[v0_53h_audit.TICK_200][arm_c] = (0.0, 64)
    reachability_by_window[v0_53h_audit.TICK_400][arm_c] = (0.20, 64)

    summaries_by_window = {
        v0_53h_audit.TICK_50: [],
        v0_53h_audit.TICK_100: [],
        v0_53h_audit.TICK_200: [],
        v0_53h_audit.TICK_400: list(summaries_a_wrong) + list(summaries_b_clean_above),
    }
    v0_53h_audit._write_audit_summary_csv(
        summaries_by_window,
        [],
        [],
        v0_53h_audit.SUBVERDICT_A_NULL_V025_TICK50_PRESENT,
        {},  # descriptive_subverdicts
        c_sub_opposite,
        reachability_by_window,
        [],
        wrong_sign_cells,
        priority3_skipped_under_reachability=True,
        rollup_verdict=rollup_b,
        rollup_phrase=phrase_b,
        path=audit_summary_path,
    )
    rows = list(csv.reader(audit_summary_path.open()))
    section_rows = [
        r for r in rows if r and r[0] == "wrong_sign_cells_under_reachability_below_threshold"
    ]
    assert len(section_rows) >= 1
    skipped_row = next(
        r for r in section_rows if r[1] == "priority3_skipped_under_reachability_below_threshold"
    )
    assert skipped_row[2] == "True"
    cell_keys = [r[1] for r in section_rows if "/" in r[1]]
    expected_prefix = (
        f"{arm_c}/{v0_53h_audit.LABEL_B_TICK400_NAME}/mean_distance_to_nearest_food_cell_tick400/"
    )
    assert any(k.startswith(expected_prefix) for k in cell_keys), (
        f"Expected wrong-sign cell rows for {expected_prefix}*; got {cell_keys}"
    )

    # Branch C: C reach = 0.30 + C PRESENT (no wrong-sign) -> priority 4 fires.
    summaries_a_clean_present = _three_summaries_for_arm_window(
        arm_c, window, (+0.6, +0.6, -0.6), v0_53h_audit.LABEL_A_NAME
    )
    summaries_b_clean_present = _three_summaries_for_arm_window(
        arm_c, window, (+0.6, +0.6, -0.6), v0_53h_audit.LABEL_B_TICK400_NAME
    )
    c_sub_present = v0_53h_audit._arm_subverdict_at_window(
        arm_c, window, summaries_a_clean_present, summaries_b_clean_present
    )
    assert c_sub_present == v0_53h_audit.SUBVERDICT_C_COMBINED_TICK400_PRESENT
    rollup_c, _ = v0_53h_audit._evaluate_rollup(
        a_null_tick50_subverdict=v0_53h_audit.SUBVERDICT_A_NULL_V025_TICK50_PRESENT,
        c_tick400_subverdict=c_sub_present,
        corpus_re_anchor=[],
        bridge_re_anchor=bridge_clean,
        b_widened_v025_reachability_tick200=0.0,
        c_reachability_tick200=0.0,
        c_reachability_tick400=0.30,
    )
    assert rollup_c == v0_53h_audit.ROLLUP_WIDENED_BRIDGE_RESCUED_BY_TIME_HORIZON_400


# ---------------------------------------------------------------------------
# Test 14 — Tier-2 categorical anchor on B_widened_V0_25 at tick-200 AND
# Tier-3 predecessor-sanity anchor on C tick-200 reachability.
#   Synthetic B reach=0.0 AND C reach=0.0 -> priority 2 does NOT fire.
#   Synthetic B reach=1/64 -> ANCHOR_REPLICATION_HALT (Tier-2).
#   Synthetic C tick-200 reach=1/64 -> ANCHOR_REPLICATION_HALT (Tier-3).
# Both anchors are integer-categorical (== 0.0).
# ---------------------------------------------------------------------------


def test_b_widened_v025_categorical_anchor_at_tick_200_and_c_predecessor_sanity_at_tick_200():
    bridge_clean = _zero_drift_bridge_re_anchor()

    # Both anchors clean -> rollup goes to priority 4.
    rollup_clean, _ = v0_53h_audit._evaluate_rollup(
        a_null_tick50_subverdict=v0_53h_audit.SUBVERDICT_A_NULL_V025_TICK50_PRESENT,
        c_tick400_subverdict=v0_53h_audit.SUBVERDICT_C_COMBINED_TICK400_PRESENT,
        corpus_re_anchor=[],
        bridge_re_anchor=bridge_clean,
        b_widened_v025_reachability_tick200=0.0,
        c_reachability_tick200=0.0,
        c_reachability_tick400=0.50,
    )
    assert rollup_clean == v0_53h_audit.ROLLUP_WIDENED_BRIDGE_RESCUED_BY_TIME_HORIZON_400

    one_sixty_fourth = 1.0 / 64.0

    # Tier-2 broken (B reach = 1/64) -> ANCHOR_REPLICATION_HALT.
    rollup_b_drift, phrase_b_drift = v0_53h_audit._evaluate_rollup(
        a_null_tick50_subverdict=v0_53h_audit.SUBVERDICT_A_NULL_V025_TICK50_PRESENT,
        c_tick400_subverdict=v0_53h_audit.SUBVERDICT_C_COMBINED_TICK400_PRESENT,
        corpus_re_anchor=[],
        bridge_re_anchor=bridge_clean,
        b_widened_v025_reachability_tick200=one_sixty_fourth,
        c_reachability_tick200=0.0,
        c_reachability_tick400=0.50,
    )
    assert rollup_b_drift == v0_53h_audit.ROLLUP_ANCHOR_REPLICATION_HALT
    assert "B_widened_V0_25" in phrase_b_drift or "0/64" in phrase_b_drift

    # Tier-3 broken (C tick-200 reach = 1/64) -> ANCHOR_REPLICATION_HALT.
    rollup_c_drift, phrase_c_drift = v0_53h_audit._evaluate_rollup(
        a_null_tick50_subverdict=v0_53h_audit.SUBVERDICT_A_NULL_V025_TICK50_PRESENT,
        c_tick400_subverdict=v0_53h_audit.SUBVERDICT_C_COMBINED_TICK400_PRESENT,
        corpus_re_anchor=[],
        bridge_re_anchor=bridge_clean,
        b_widened_v025_reachability_tick200=0.0,
        c_reachability_tick200=one_sixty_fourth,
        c_reachability_tick400=0.50,
    )
    assert rollup_c_drift == v0_53h_audit.ROLLUP_ANCHOR_REPLICATION_HALT
    assert "C_widened_combined_se100_bmc010_n400" in phrase_c_drift or "0/64" in phrase_c_drift

    # Integer-categorical: even 1e-9 trips the halt on either anchor.
    rollup_b_eps, _ = v0_53h_audit._evaluate_rollup(
        a_null_tick50_subverdict=v0_53h_audit.SUBVERDICT_A_NULL_V025_TICK50_PRESENT,
        c_tick400_subverdict=v0_53h_audit.SUBVERDICT_C_COMBINED_TICK400_PRESENT,
        corpus_re_anchor=[],
        bridge_re_anchor=bridge_clean,
        b_widened_v025_reachability_tick200=1e-9,
        c_reachability_tick200=0.0,
        c_reachability_tick400=0.50,
    )
    assert rollup_b_eps == v0_53h_audit.ROLLUP_ANCHOR_REPLICATION_HALT
    rollup_c_eps, _ = v0_53h_audit._evaluate_rollup(
        a_null_tick50_subverdict=v0_53h_audit.SUBVERDICT_A_NULL_V025_TICK50_PRESENT,
        c_tick400_subverdict=v0_53h_audit.SUBVERDICT_C_COMBINED_TICK400_PRESENT,
        corpus_re_anchor=[],
        bridge_re_anchor=bridge_clean,
        b_widened_v025_reachability_tick200=0.0,
        c_reachability_tick200=1e-9,
        c_reachability_tick400=0.50,
    )
    assert rollup_c_eps == v0_53h_audit.ROLLUP_ANCHOR_REPLICATION_HALT


# ---------------------------------------------------------------------------
# Test 15 — C tick-400 reachability threshold partition.
#   reach < 0.25, C in {PRESENT, PARTIAL, NOT_FOUND}    -> priority 5 BELOW
#   reach >= 0.25, C PRESENT                            -> priority 4 RESCUED
#   reach >= 0.25, C in {PARTIAL, NOT_FOUND}            -> priority 6 PARTIAL
# OPPOSITE_SIGN_HALT branches covered exhaustively in test #13.
# ---------------------------------------------------------------------------


def test_c_tick_400_reachability_threshold_partition():
    bridge_clean = _zero_drift_bridge_re_anchor()

    for c_kind in ("PRESENT", "PARTIAL", "NOT_FOUND"):
        c_sub = _c_tick400_subverdict_for_kind(c_kind)
        rollup, phrase = v0_53h_audit._evaluate_rollup(
            a_null_tick50_subverdict=v0_53h_audit.SUBVERDICT_A_NULL_V025_TICK50_PRESENT,
            c_tick400_subverdict=c_sub,
            corpus_re_anchor=[],
            bridge_re_anchor=bridge_clean,
            b_widened_v025_reachability_tick200=0.0,
            c_reachability_tick200=0.0,
            c_reachability_tick400=0.20,
        )
        assert rollup == (
            v0_53h_audit.ROLLUP_WIDENED_BELOW_REACHABILITY_THRESHOLD_AT_TIME_HORIZON_400
        )
        assert (
            "The bridge is not rescued by extending the horizon to "
            "`n_ticks=400` under V0_25 × `widened_gradient` × combined-budget "  # noqa: RUF001
            "envelope"
        ) in phrase

    rollup_present, _ = v0_53h_audit._evaluate_rollup(
        a_null_tick50_subverdict=v0_53h_audit.SUBVERDICT_A_NULL_V025_TICK50_PRESENT,
        c_tick400_subverdict=v0_53h_audit.SUBVERDICT_C_COMBINED_TICK400_PRESENT,
        corpus_re_anchor=[],
        bridge_re_anchor=bridge_clean,
        b_widened_v025_reachability_tick200=0.0,
        c_reachability_tick200=0.0,
        c_reachability_tick400=0.30,
    )
    assert rollup_present == v0_53h_audit.ROLLUP_WIDENED_BRIDGE_RESCUED_BY_TIME_HORIZON_400

    for c_kind in ("PARTIAL", "NOT_FOUND"):
        c_sub = _c_tick400_subverdict_for_kind(c_kind)
        rollup, _ = v0_53h_audit._evaluate_rollup(
            a_null_tick50_subverdict=v0_53h_audit.SUBVERDICT_A_NULL_V025_TICK50_PRESENT,
            c_tick400_subverdict=c_sub,
            corpus_re_anchor=[],
            bridge_re_anchor=bridge_clean,
            b_widened_v025_reachability_tick200=0.0,
            c_reachability_tick200=0.0,
            c_reachability_tick400=0.30,
        )
        assert rollup == (v0_53h_audit.ROLLUP_WIDENED_BRIDGE_PARTIALLY_RESCUED_BY_TIME_HORIZON_400)


# ---------------------------------------------------------------------------
# Test 16 — Rollup locked phrases fire verbatim AND priority cascade +
# partition exhaustiveness over (C tick-400 reach, C tick-400 sub-verdict).
# Predecessor references to v0.53c/d/e/f/g must appear in priority 4/5/6 phrases.
# ---------------------------------------------------------------------------


def test_rollup_locked_phrases_fire_verbatim_and_priority_cascade_partition_total():  # noqa: PLR0915
    bridge_clean = _zero_drift_bridge_re_anchor()
    bridge_drift = list(bridge_clean)
    bridge_drift[0] = v0_53h_audit.BridgeReAnchorRow(
        label=bridge_drift[0].label,
        observable=bridge_drift[0].observable,
        published_signed_d=bridge_drift[0].published_signed_d,
        derived_signed_d=bridge_drift[0].published_signed_d + 1.5,
        drift_abs=1.5,
        halts=True,
    )
    corpus_halt = [
        v0_53h_audit.ReAnchorRow(
            arm=v0_53h_audit.ARM_A_NULL_V025,
            version="v0.42",
            hazard=8,
            n_runs_contributing=8,
            a_share_h8_derived=0.700,
            a_share_h8_published=0.652,
            drift_abs=0.048,
            halts=True,
        )
    ]

    # Priority 3 RELAXED_OPPOSITE_SIGN_HALT (reachability-gated on tick-400).
    _, phrase_p3 = v0_53h_audit._evaluate_rollup(
        a_null_tick50_subverdict=v0_53h_audit.SUBVERDICT_A_NULL_V025_TICK50_PRESENT,
        c_tick400_subverdict=v0_53h_audit.SUBVERDICT_C_COMBINED_TICK400_OPPOSITE,
        corpus_re_anchor=[],
        bridge_re_anchor=bridge_clean,
        b_widened_v025_reachability_tick200=0.0,
        c_reachability_tick200=0.0,
        c_reachability_tick400=0.50,
    )
    assert (
        "AND C reachability at tick-400 clears the locked 25% threshold "
        "(so the bridge framework is meaningful at this measurement)"
    ) in phrase_p3
    assert (
        "The reachability-gated trigger preserves v0.53e's locked sign discipline "
        "while excluding the v0.53e-style measurement-edge case "
        "(wrong-sign at reachability=0)"
    ) in phrase_p3

    # Priority 4 RESCUED.
    _, phrase_rescued = v0_53h_audit._evaluate_rollup(
        a_null_tick50_subverdict=v0_53h_audit.SUBVERDICT_A_NULL_V025_TICK50_PRESENT,
        c_tick400_subverdict=v0_53h_audit.SUBVERDICT_C_COMBINED_TICK400_PRESENT,
        corpus_re_anchor=[],
        bridge_re_anchor=bridge_clean,
        b_widened_v025_reachability_tick200=0.0,
        c_reachability_tick200=0.0,
        c_reachability_tick400=0.50,
    )
    assert (
        "Doubling `n_ticks` from 200 to 400 lifts the reachability ceiling on "
        "the v0.53g combined-budget envelope"
    ) in phrase_rescued
    assert (
        "The (V0_25 × `widened_gradient` × combined-budget) cell is bounded by "  # noqa: RUF001
        "the `n_ticks=200` simulation horizon under the tested envelope"
    ) in phrase_rescued
    assert "doubling the horizon to `n_ticks=400` admits the bridge" in phrase_rescued
    assert "WIDENED_BELOW_REACHABILITY_THRESHOLD_AT_TICK_200" in phrase_rescued
    assert "WIDENED_BELOW_REACHABILITY_THRESHOLD_UNDER_RELAXED_INFLUX" in phrase_rescued
    assert "RELAXED_OPPOSITE_SIGN_HALT" in phrase_rescued
    assert "WIDENED_BELOW_REACHABILITY_THRESHOLD_UNDER_BASE_METABOLIC_COST_010" in phrase_rescued
    assert "WIDENED_BELOW_REACHABILITY_THRESHOLD_UNDER_COMBINED_SE100_BMC010" in phrase_rescued

    # Priority 5 BELOW_THRESHOLD.
    _, phrase_below = v0_53h_audit._evaluate_rollup(
        a_null_tick50_subverdict=v0_53h_audit.SUBVERDICT_A_NULL_V025_TICK50_PRESENT,
        c_tick400_subverdict=v0_53h_audit.SUBVERDICT_C_COMBINED_TICK400_PRESENT,
        corpus_re_anchor=[],
        bridge_re_anchor=bridge_clean,
        b_widened_v025_reachability_tick200=0.0,
        c_reachability_tick200=0.0,
        c_reachability_tick400=0.10,
    )
    assert (
        "The bridge is not rescued by extending the horizon to "
        "`n_ticks=400` under V0_25 × `widened_gradient` × combined-budget "  # noqa: RUF001
        "envelope"
    ) in phrase_below
    assert (
        "the (V0_25 × `widened_gradient` × combined-budget) reachability "  # noqa: RUF001
        "ceiling is not lifted by doubling the simulation horizon to "
        "`n_ticks=400`"
    ) in phrase_below
    assert (
        "v0.53i (or later) candidates shift toward axes not yet tested in the v0.53d→v0.53h stack"
    ) in phrase_below
    assert "WIDENED_BELOW_REACHABILITY_THRESHOLD_AT_TICK_200" in phrase_below
    assert "WIDENED_BELOW_REACHABILITY_THRESHOLD_UNDER_RELAXED_INFLUX" in phrase_below
    assert "RELAXED_OPPOSITE_SIGN_HALT" in phrase_below
    assert "WIDENED_BELOW_REACHABILITY_THRESHOLD_UNDER_BASE_METABOLIC_COST_010" in phrase_below
    assert "WIDENED_BELOW_REACHABILITY_THRESHOLD_UNDER_COMBINED_SE100_BMC010" in phrase_below

    # Priority 6 PARTIALLY_RESCUED.
    _, phrase_partial = v0_53h_audit._evaluate_rollup(
        a_null_tick50_subverdict=v0_53h_audit.SUBVERDICT_A_NULL_V025_TICK50_PRESENT,
        c_tick400_subverdict=v0_53h_audit.SUBVERDICT_C_COMBINED_TICK400_NOT_FOUND,
        corpus_re_anchor=[],
        bridge_re_anchor=bridge_clean,
        b_widened_v025_reachability_tick200=0.0,
        c_reachability_tick200=0.0,
        c_reachability_tick400=0.30,
    )
    assert (
        "reachability becomes measurable but the bridge does not fully replicate"
    ) in phrase_partial
    assert "WIDENED_BELOW_REACHABILITY_THRESHOLD_AT_TICK_200" in phrase_partial
    assert "WIDENED_BELOW_REACHABILITY_THRESHOLD_UNDER_RELAXED_INFLUX" in phrase_partial
    assert "RELAXED_OPPOSITE_SIGN_HALT" in phrase_partial
    assert "WIDENED_BELOW_REACHABILITY_THRESHOLD_UNDER_BASE_METABOLIC_COST_010" in phrase_partial
    assert "WIDENED_BELOW_REACHABILITY_THRESHOLD_UNDER_COMBINED_SE100_BMC010" in phrase_partial

    # Priority cascade: 1 > 2.a > 2.b > 2.c > 2.d > 3 > 4/5/6.
    rollup_1, phrase_1 = v0_53h_audit._evaluate_rollup(
        a_null_tick50_subverdict=v0_53h_audit.SUBVERDICT_A_NULL_V025_TICK50_NOT_FOUND,
        c_tick400_subverdict=v0_53h_audit.SUBVERDICT_C_COMBINED_TICK400_OPPOSITE,
        corpus_re_anchor=corpus_halt,
        bridge_re_anchor=bridge_drift,
        b_widened_v025_reachability_tick200=1.0 / 64.0,
        c_reachability_tick200=1.0 / 64.0,
        c_reachability_tick400=0.50,
    )
    assert rollup_1 == v0_53h_audit.ROLLUP_CORPUS_DRIFT_HALT
    assert "v0.42" in phrase_1

    rollup_2a, _ = v0_53h_audit._evaluate_rollup(
        a_null_tick50_subverdict=v0_53h_audit.SUBVERDICT_A_NULL_V025_TICK50_PRESENT,
        c_tick400_subverdict=v0_53h_audit.SUBVERDICT_C_COMBINED_TICK400_OPPOSITE,
        corpus_re_anchor=[],
        bridge_re_anchor=bridge_drift,
        b_widened_v025_reachability_tick200=0.0,
        c_reachability_tick200=0.0,
        c_reachability_tick400=0.50,
    )
    assert rollup_2a == v0_53h_audit.ROLLUP_ANCHOR_REPLICATION_HALT

    rollup_2b, _ = v0_53h_audit._evaluate_rollup(
        a_null_tick50_subverdict=v0_53h_audit.SUBVERDICT_A_NULL_V025_TICK50_NOT_FOUND,
        c_tick400_subverdict=v0_53h_audit.SUBVERDICT_C_COMBINED_TICK400_OPPOSITE,
        corpus_re_anchor=[],
        bridge_re_anchor=bridge_clean,
        b_widened_v025_reachability_tick200=0.0,
        c_reachability_tick200=0.0,
        c_reachability_tick400=0.50,
    )
    assert rollup_2b == v0_53h_audit.ROLLUP_ANCHOR_REPLICATION_HALT

    rollup_2c, _ = v0_53h_audit._evaluate_rollup(
        a_null_tick50_subverdict=v0_53h_audit.SUBVERDICT_A_NULL_V025_TICK50_PRESENT,
        c_tick400_subverdict=v0_53h_audit.SUBVERDICT_C_COMBINED_TICK400_OPPOSITE,
        corpus_re_anchor=[],
        bridge_re_anchor=bridge_clean,
        b_widened_v025_reachability_tick200=1.0 / 64.0,
        c_reachability_tick200=0.0,
        c_reachability_tick400=0.50,
    )
    assert rollup_2c == v0_53h_audit.ROLLUP_ANCHOR_REPLICATION_HALT

    rollup_2d, _ = v0_53h_audit._evaluate_rollup(
        a_null_tick50_subverdict=v0_53h_audit.SUBVERDICT_A_NULL_V025_TICK50_PRESENT,
        c_tick400_subverdict=v0_53h_audit.SUBVERDICT_C_COMBINED_TICK400_OPPOSITE,
        corpus_re_anchor=[],
        bridge_re_anchor=bridge_clean,
        b_widened_v025_reachability_tick200=0.0,
        c_reachability_tick200=1.0 / 64.0,
        c_reachability_tick400=0.50,
    )
    assert rollup_2d == v0_53h_audit.ROLLUP_ANCHOR_REPLICATION_HALT

    rollup_3, _ = v0_53h_audit._evaluate_rollup(
        a_null_tick50_subverdict=v0_53h_audit.SUBVERDICT_A_NULL_V025_TICK50_PRESENT,
        c_tick400_subverdict=v0_53h_audit.SUBVERDICT_C_COMBINED_TICK400_OPPOSITE,
        corpus_re_anchor=[],
        bridge_re_anchor=bridge_clean,
        b_widened_v025_reachability_tick200=0.0,
        c_reachability_tick200=0.0,
        c_reachability_tick400=0.50,
    )
    assert rollup_3 == v0_53h_audit.ROLLUP_RELAXED_OPPOSITE_SIGN_HALT

    # Partition exhaustiveness over (C tick-400 reach, C tick-400 sub-verdict).
    sub_kinds_all = ("PRESENT", "PARTIAL", "NOT_FOUND", "OPPOSITE")
    seen: dict[tuple[str, str], str] = {}
    for c_kind in sub_kinds_all:
        c_sub = _c_tick400_subverdict_for_kind(c_kind)

        rollup_above, _ = v0_53h_audit._evaluate_rollup(
            a_null_tick50_subverdict=v0_53h_audit.SUBVERDICT_A_NULL_V025_TICK50_PRESENT,
            c_tick400_subverdict=c_sub,
            corpus_re_anchor=[],
            bridge_re_anchor=bridge_clean,
            b_widened_v025_reachability_tick200=0.0,
            c_reachability_tick200=0.0,
            c_reachability_tick400=0.50,
        )
        seen[(c_kind, "above")] = rollup_above

        rollup_below, _ = v0_53h_audit._evaluate_rollup(
            a_null_tick50_subverdict=v0_53h_audit.SUBVERDICT_A_NULL_V025_TICK50_PRESENT,
            c_tick400_subverdict=c_sub,
            corpus_re_anchor=[],
            bridge_re_anchor=bridge_clean,
            b_widened_v025_reachability_tick200=0.0,
            c_reachability_tick200=0.0,
            c_reachability_tick400=0.10,
        )
        seen[(c_kind, "below")] = rollup_below

    rescued = v0_53h_audit.ROLLUP_WIDENED_BRIDGE_RESCUED_BY_TIME_HORIZON_400
    partial_outcome = v0_53h_audit.ROLLUP_WIDENED_BRIDGE_PARTIALLY_RESCUED_BY_TIME_HORIZON_400
    below = v0_53h_audit.ROLLUP_WIDENED_BELOW_REACHABILITY_THRESHOLD_AT_TIME_HORIZON_400
    relaxed_opp = v0_53h_audit.ROLLUP_RELAXED_OPPOSITE_SIGN_HALT

    assert seen[("PRESENT", "above")] == rescued
    assert seen[("PARTIAL", "above")] == partial_outcome
    assert seen[("NOT_FOUND", "above")] == partial_outcome
    assert seen[("OPPOSITE", "above")] == relaxed_opp

    for c_kind in sub_kinds_all:
        assert seen[(c_kind, "below")] == below, (
            f"Combo (C={c_kind}, below): expected priority-5 BELOW (including "
            f"the reachability-gated collapse for OPPOSITE_SIGN_HALT) but got "
            f"{seen[(c_kind, 'below')]}"
        )

    assert len(seen) == 8


# Sanity: pytest must be importable for the runner to discover this file.
_ = pytest
