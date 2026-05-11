"""v0.53n per-lineage perception heterogeneity probe — tests (16 locked).

Pre-reg: [[docs/experiments/fear_hunger_v0.53n.md]] §"Test list (locked,
16 tests…)". Tests numbered to match the pre-reg's ordering. Test #5 is
byte-identical to v0.53m #5 (same C arm config). Test #6 is NEW: D arm
min-only per-founder override asserts. Test #9 is NEW: bottom-K helper +
min-only per-founder override targeting. Test #11 verifies Label A
indexes the MAX-sensor lineage on D (the alignment-control mechanism).
Test #15 has six branches (A/B/C/D/E/F) covering the asymmetric-halt
rule. Test #16 combines anchor reproduction + D partition + locked
phrase substring assertions with the ELEVEN-long predecessor stack.
"""

from __future__ import annotations

import csv
import hashlib
import importlib.util
import math
import statistics
import sys
from dataclasses import replace
from pathlib import Path

import pytest

from hedonism_harness.core.config import BodyConfig
from hedonism_harness.core.rng import make_streams
from hedonism_harness.core.traits import TraitConfig, random_traits
from hedonism_harness.experiments.fear_hunger_chamber import ChamberLayout, run_chamber
from tests import sha_pins

_SCRIPT_PATH = (
    Path(__file__).parent.parent
    / "scripts"
    / "v0_53n_perception_min_lineage_sensor_radius_8_audit.py"
)
_spec = importlib.util.spec_from_file_location("v0_53n_audit", _SCRIPT_PATH)
assert _spec is not None
assert _spec.loader is not None
v0_53n_audit = importlib.util.module_from_spec(_spec)
sys.modules["v0_53n_audit"] = v0_53n_audit
_spec.loader.exec_module(v0_53n_audit)


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
    fires_expected = (not math.isnan(signed)) and signed >= v0_53n_audit.COHENS_D_THRESHOLD
    fires_wrong = (not math.isnan(signed)) and signed <= -v0_53n_audit.COHENS_D_THRESHOLD
    return v0_53n_audit.ObservableSummary(
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
        v0_53n_audit.TICK_50: v0_53n_audit.PRIMARY_OBSERVABLES_TICK50,
        v0_53n_audit.TICK_100: v0_53n_audit.PRIMARY_OBSERVABLES_TICK100,
        v0_53n_audit.TICK_200: v0_53n_audit.PRIMARY_OBSERVABLES_TICK200,
        v0_53n_audit.TICK_400: v0_53n_audit.PRIMARY_OBSERVABLES_TICK400,
    }
    obs = obs_table[window]
    return [
        _make_summary(arm=arm, observable=obs[i][0], sign=obs[i][1], paired_d=ds[i], label=label)
        for i in range(3)
    ]


def _zero_drift_bridge_re_anchor() -> list[object]:
    return [
        v0_53n_audit.BridgeReAnchorRow(
            label=label,
            observable=obs,
            published_signed_d=ref,
            derived_signed_d=ref,
            drift_abs=0.0,
            halts=False,
        )
        for (label, obs), ref in v0_53n_audit.V048_PUBLISHED_SIGNED_D.items()
    ]


def _green_anchor_kwargs() -> dict[str, object]:
    """Return rollup kwargs for C/E anchors that pass all sub-conditions."""
    return {
        "c_reachability_tick400": v0_53n_audit.C_INSLICE_REACHABILITY_LOCKED,
        "c_tick400_subverdict": v0_53n_audit.SUBVERDICT_C_FOOD_NEAR1_TICK400_PRESENT,
        "c_tick400_signed_d": dict(v0_53n_audit.V053L_C_TIER3_ANCHOR_PUBLISHED),
        "e_reachability_tick400": v0_53n_audit.E_INSLICE_REACHABILITY_LOCKED,
        "e_tick400_subverdict": v0_53n_audit.SUBVERDICT_E_FOOD_NEAR1_TICK400_PARTIAL,
        "e_tick400_signed_d": dict(v0_53n_audit.V053K_C_TIER3_ANCHOR_PUBLISHED),
    }


def _d_label_summaries_present() -> list[object]:
    """Three Label A or Label B summaries on D, all firing PRESENT."""
    arm_d = v0_53n_audit.ARM_D_WIDENED_FOOD_NEAR1_COMBINED_MIN_LINEAGE_SR8_N400
    return _three_summaries_for_arm_window(
        arm_d, v0_53n_audit.TICK_400, (+0.6, +0.6, -0.6), v0_53n_audit.LABEL_A_NAME
    )


def _d_summaries_kind(kind: str, label_name: str) -> list[object]:
    """Build D tick-400 summaries for a label triple based on kind.

    kind = "PRESENT": 3 expected fires.
    kind = "NOT_PRESENT": 1 expected fire only.
    kind = "WRONG_SIGN": 1 wrong-sign cell + 2 NaN.
    """
    arm_d = v0_53n_audit.ARM_D_WIDENED_FOOD_NEAR1_COMBINED_MIN_LINEAGE_SR8_N400
    window = v0_53n_audit.TICK_400
    if kind == "PRESENT":
        return _three_summaries_for_arm_window(arm_d, window, (+0.6, +0.6, -0.6), label_name)
    if kind == "NOT_PRESENT":
        return _three_summaries_for_arm_window(
            arm_d, window, (+0.6, float("nan"), float("nan")), label_name
        )
    if kind == "WRONG_SIGN":
        # Note: sign on third observable is -1, so paired_d=+0.7 -> signed_d=-0.7.
        return _three_summaries_for_arm_window(
            arm_d, window, (float("nan"), float("nan"), +0.7), label_name
        )
    msg = f"unknown kind {kind!r}"
    raise ValueError(msg)


# ---------------------------------------------------------------------------
# Test 1 — paired_d formula + Tier-1 v0.48 + v0.53l C anchor + v0.53k E anchor.
# ---------------------------------------------------------------------------


def test_paired_d_function_reproduces_hand_computed_signed_d_on_fixture_AND_tier1_v048_constants_AND_v053l_published_C_anchor_AND_v053k_published_E_anchor():  # noqa: E501, N802
    deltas = [1.0, 2.0, 1.5, 0.5, 2.5, 1.8, 0.9, 1.2]
    expected_mean = statistics.mean(deltas)
    expected_sd = statistics.stdev(deltas)
    expected_d = expected_mean / expected_sd
    derived_d = v0_53n_audit._paired_cohens_d(deltas)
    assert abs(derived_d - expected_d) < 1e-9

    pinned_v048 = {
        ("label_a_sensor_radius", "pre50_food_events_count"): +1.066,
        ("label_a_sensor_radius", "pre50_food_energy_acquired"): +1.066,
        ("label_a_sensor_radius", "mean_distance_to_nearest_food_cell_tick50"): +1.916,
        ("label_b_readiness_fraction_tick50", "pre50_food_events_count"): +0.916,
        ("label_b_readiness_fraction_tick50", "pre50_food_energy_acquired"): +0.916,
        ("label_b_readiness_fraction_tick50", "mean_distance_to_nearest_food_cell_tick50"): +1.179,
    }
    assert pinned_v048 == v0_53n_audit.V048_PUBLISHED_SIGNED_D

    pinned_v053l_c_anchor = {
        ("label_a_sensor_radius", "pre400_food_events_count"): +4.407500095034808,
        ("label_a_sensor_radius", "pre400_food_energy_acquired"): +4.407500095034808,
        (
            "label_a_sensor_radius",
            "mean_distance_to_nearest_food_cell_tick400",
        ): +3.8177086030179344,
        ("label_b_readiness_fraction_tick400", "pre400_food_events_count"): +44.79447381457056,
        ("label_b_readiness_fraction_tick400", "pre400_food_energy_acquired"): +44.79447381457056,
        (
            "label_b_readiness_fraction_tick400",
            "mean_distance_to_nearest_food_cell_tick400",
        ): +7.203121884647769,
    }
    assert pinned_v053l_c_anchor == v0_53n_audit.V053L_C_TIER3_ANCHOR_PUBLISHED
    expected_rounded_c = {
        ("label_a_sensor_radius", "pre400_food_events_count"): +4.4075,
        ("label_a_sensor_radius", "pre400_food_energy_acquired"): +4.4075,
        ("label_a_sensor_radius", "mean_distance_to_nearest_food_cell_tick400"): +3.8177,
        ("label_b_readiness_fraction_tick400", "pre400_food_events_count"): +44.7945,
        ("label_b_readiness_fraction_tick400", "pre400_food_energy_acquired"): +44.7945,
        (
            "label_b_readiness_fraction_tick400",
            "mean_distance_to_nearest_food_cell_tick400",
        ): +7.2031,
    }
    for key, exact in pinned_v053l_c_anchor.items():
        assert abs(exact - expected_rounded_c[key]) < 1e-3

    pinned_v053k_e_anchor = {
        ("label_a_sensor_radius", "pre400_food_events_count"): -0.019198889380801876,
        ("label_a_sensor_radius", "pre400_food_energy_acquired"): -0.019198889380801876,
        (
            "label_a_sensor_radius",
            "mean_distance_to_nearest_food_cell_tick400",
        ): -0.002295569212554338,
        ("label_b_readiness_fraction_tick400", "pre400_food_events_count"): +0.6978345195653476,
        ("label_b_readiness_fraction_tick400", "pre400_food_energy_acquired"): +0.6978345195653476,
        (
            "label_b_readiness_fraction_tick400",
            "mean_distance_to_nearest_food_cell_tick400",
        ): +0.5878534807527567,
    }
    assert pinned_v053k_e_anchor == v0_53n_audit.V053K_C_TIER3_ANCHOR_PUBLISHED
    expected_rounded_e = {
        ("label_a_sensor_radius", "pre400_food_events_count"): -0.0192,
        ("label_a_sensor_radius", "pre400_food_energy_acquired"): -0.0192,
        ("label_a_sensor_radius", "mean_distance_to_nearest_food_cell_tick400"): -0.0023,
        ("label_b_readiness_fraction_tick400", "pre400_food_events_count"): +0.6978,
        ("label_b_readiness_fraction_tick400", "pre400_food_energy_acquired"): +0.6978,
        (
            "label_b_readiness_fraction_tick400",
            "mean_distance_to_nearest_food_cell_tick400",
        ): +0.5879,
    }
    for key, exact in pinned_v053k_e_anchor.items():
        assert abs(exact - expected_rounded_e[key]) < 1e-3
    assert v0_53n_audit.C_INSLICE_REACHABILITY_LOCKED == 61.0 / 64.0
    assert v0_53n_audit.E_INSLICE_REACHABILITY_LOCKED == 64.0 / 64.0
    assert v0_53n_audit.INSLICE_PAIRED_D_TOLERANCE == 1e-3


# ---------------------------------------------------------------------------
# Test 2 — Corpus a_share_h8 re-anchor for v0.42/v0.44/v0.45.
# ---------------------------------------------------------------------------


def test_a_null_v025_corpus_a_share_h8_re_anchors_v042_v044_v045():
    clean = [
        v0_53n_audit.ReAnchorRow(
            arm=v0_53n_audit.ARM_A_NULL_V025,
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
    rollup, _ = v0_53n_audit._evaluate_rollup(
        a_null_tick50_subverdict=v0_53n_audit.SUBVERDICT_A_NULL_V025_TICK50_PRESENT,
        d_tick400_label_a_summaries=_d_summaries_kind("NOT_PRESENT", v0_53n_audit.LABEL_A_NAME),
        d_tick400_label_b_summaries=_d_summaries_kind("PRESENT", v0_53n_audit.LABEL_B_TICK400_NAME),
        corpus_re_anchor=clean,
        bridge_re_anchor=_zero_drift_bridge_re_anchor(),
        b_widened_v025_reachability_tick200=0.0,
        d_reachability_tick400=0.50,
        **_green_anchor_kwargs(),
    )
    assert (
        rollup == v0_53n_audit.ROLLUP_MIN_LINEAGE_ACCESS_RESCUES_REACHABILITY_AND_DECOUPLES_LABEL_A
    )

    drifted = list(clean)
    drifted[1] = v0_53n_audit.ReAnchorRow(
        arm=v0_53n_audit.ARM_A_NULL_V025,
        version="v0.44",
        hazard=8,
        n_runs_contributing=8,
        a_share_h8_derived=0.880,
        a_share_h8_published=0.878,
        drift_abs=0.002,
        halts=True,
    )
    rollup_d, phrase_d = v0_53n_audit._evaluate_rollup(
        a_null_tick50_subverdict=v0_53n_audit.SUBVERDICT_A_NULL_V025_TICK50_PRESENT,
        d_tick400_label_a_summaries=_d_summaries_kind("NOT_PRESENT", v0_53n_audit.LABEL_A_NAME),
        d_tick400_label_b_summaries=_d_summaries_kind("PRESENT", v0_53n_audit.LABEL_B_TICK400_NAME),
        corpus_re_anchor=drifted,
        bridge_re_anchor=_zero_drift_bridge_re_anchor(),
        b_widened_v025_reachability_tick200=0.0,
        d_reachability_tick400=0.50,
        **_green_anchor_kwargs(),
    )
    assert rollup_d == v0_53n_audit.ROLLUP_CORPUS_DRIFT_HALT
    assert "v0.44" in phrase_d


# ---------------------------------------------------------------------------
# Test 3 — Arm A_null_V0_25 uses tight_gradient_layout.
# ---------------------------------------------------------------------------


def test_arm_a_null_v025_uses_tight_gradient_layout_default_body_config_and_n_ticks_200_with_explicit_geometry_asserts():  # noqa: E501
    layout = v0_53n_audit._layout_for_arm(v0_53n_audit.ARM_A_NULL_V025)
    assert layout.safe_x_min == 0
    assert layout.safe_x_max == 2
    assert layout.hazard_x_min == 3
    assert layout.hazard_x_max == 4
    assert layout.food_x_min == 5
    assert layout.food_x_max == 8
    assert layout.resolved_spawn_x == 1
    assert layout.height == 6
    assert layout.width == 9
    assert v0_53n_audit.LAYOUT_NAME_BY_ARM[v0_53n_audit.ARM_A_NULL_V025] == "tight_gradient"
    assert v0_53n_audit._body_config_for_arm(v0_53n_audit.ARM_A_NULL_V025) is None
    assert (
        v0_53n_audit.BODY_BASE_METABOLIC_COST_BY_ARM[v0_53n_audit.ARM_A_NULL_V025]
        == v0_53n_audit.V0_25_BODY_BASE_METABOLIC_COST
        == 0.25
    )
    assert v0_53n_audit.N_TICKS_BY_ARM[v0_53n_audit.ARM_A_NULL_V025] == 200
    assert (
        v0_53n_audit.WINDOWS_BY_ARM[v0_53n_audit.ARM_A_NULL_V025]
        == v0_53n_audit.WINDOWS_AB
        == (50, 100, 200)
    )
    assert (
        v0_53n_audit.BODY_EFFECTIVE_SENSOR_RADIUS_OVERRIDE_BY_ARM[v0_53n_audit.ARM_A_NULL_V025]
        is None
    )


# ---------------------------------------------------------------------------
# Test 4 — Arm B_widened_V0_25 uses widened_gradient_layout.
# ---------------------------------------------------------------------------


def test_arm_b_widened_v025_uses_widened_gradient_layout_default_body_config_and_n_ticks_200_with_explicit_geometry_asserts():  # noqa: E501
    layout = v0_53n_audit._layout_for_arm(v0_53n_audit.ARM_B_WIDENED_V025)
    assert layout.safe_x_min == 0
    assert layout.safe_x_max == 4
    assert layout.hazard_x_min == 5
    assert layout.hazard_x_max == 7
    assert layout.food_x_min == 10
    assert layout.food_x_max == 14
    assert layout.resolved_spawn_x == 1
    assert layout.height == 6
    assert layout.width == 15
    assert v0_53n_audit.LAYOUT_NAME_BY_ARM[v0_53n_audit.ARM_B_WIDENED_V025] == "widened_gradient"
    assert v0_53n_audit._body_config_for_arm(v0_53n_audit.ARM_B_WIDENED_V025) is None
    assert v0_53n_audit.N_TICKS_BY_ARM[v0_53n_audit.ARM_B_WIDENED_V025] == 200


# ---------------------------------------------------------------------------
# Test 5 — Arm C uses FOOD_NEAR1, max-only override (byte-identical to v0.53m #5).
# ---------------------------------------------------------------------------


def test_arm_c_widened_food_near1_combined_max_lineage_sr8_N400_uses_food_near1_layout_per_founder_override_on_max_sensor_lineage_only_and_n_ticks_400_with_explicit_geometry_and_per_lineage_perception_asserts(  # noqa: E501, N802
    tmp_path,
):
    arm_c = v0_53n_audit.ARM_C_WIDENED_FOOD_NEAR1_COMBINED_MAX_LINEAGE_SR8_N400

    bc_c = v0_53n_audit._body_config_for_arm(arm_c)
    assert isinstance(bc_c, BodyConfig)
    assert bc_c.starting_energy == 100.0
    assert bc_c.base_metabolic_cost == 0.10
    assert bc_c.effective_sensor_radius_override is None

    assert isinstance(v0_53n_audit.FOOD_NEAR1_LAYOUT, ChamberLayout)
    fn1 = v0_53n_audit.FOOD_NEAR1_LAYOUT
    assert fn1.food_x_min == 9
    assert fn1.food_x_max == 13
    assert fn1.width == 14
    assert fn1.height == 6

    assert v0_53n_audit.N_TICKS_BY_ARM[arm_c] == 400
    assert v0_53n_audit.BODY_EFFECTIVE_SENSOR_RADIUS_OVERRIDE_BY_ARM[arm_c] is None
    assert v0_53n_audit.ARM_OVERRIDE_K[arm_c] == 1

    seed = 41
    cap_c = v0_53n_audit._run_one_arm(
        arm=arm_c, version="v0.42", seed=seed, hazard=0, runs_root=tmp_path
    )

    for rec in cap_c.founder_records:
        assert rec.founder_body_energy_tick0 == 100.0
        assert rec.founder_body_starting_energy_tick0 == 100.0
        assert rec.founder_body_base_metabolic_cost_tick0 == 0.10
        assert rec.founder_body_effective_sensor_radius_override_tick0 is None

    overridden = [
        rec
        for rec in cap_c.founder_records
        if rec.founder_traits_effective_sensor_radius_override_tick0 == 8
    ]
    assert len(overridden) == 1
    sensor_radius_by_lineage = {
        rec.lineage_id: rec.founder_sensor_radius for rec in cap_c.founder_records
    }
    expected_max_lid = v0_53n_audit._select_sensor_radius_label(sensor_radius_by_lineage)
    assert overridden[0].lineage_id == expected_max_lid

    non_overridden = [
        rec
        for rec in cap_c.founder_records
        if rec.founder_traits_effective_sensor_radius_override_tick0 is None
    ]
    assert len(non_overridden) == 4

    assert cap_c.layout_name == "widened_food_near1"
    assert cap_c.n_ticks == 400
    assert cap_c.body_effective_sensor_radius_override is None
    assert cap_c.final_tick_count <= 400


# ---------------------------------------------------------------------------
# Test 6 — Arm D uses FOOD_NEAR1, min-only override (NEW).
# ---------------------------------------------------------------------------


def test_arm_d_widened_food_near1_combined_min_lineage_sr8_N400_uses_food_near1_layout_per_founder_override_on_min_sensor_lineage_only_and_n_ticks_400_with_explicit_geometry_and_min_lineage_perception_asserts(  # noqa: E501, N802
    tmp_path,
):
    arm_d = v0_53n_audit.ARM_D_WIDENED_FOOD_NEAR1_COMBINED_MIN_LINEAGE_SR8_N400

    bc_d = v0_53n_audit._body_config_for_arm(arm_d)
    assert isinstance(bc_d, BodyConfig)
    assert bc_d.starting_energy == 100.0
    assert bc_d.base_metabolic_cost == 0.10
    # D has NO body_config override (per-lineage override lives on Traits).
    assert bc_d.effective_sensor_radius_override is None

    assert v0_53n_audit.LAYOUT_NAME_BY_ARM[arm_d] == "widened_food_near1"
    assert v0_53n_audit.N_TICKS_BY_ARM[arm_d] == 400
    assert v0_53n_audit.BODY_EFFECTIVE_SENSOR_RADIUS_OVERRIDE_BY_ARM[arm_d] is None
    assert v0_53n_audit.ARM_OVERRIDE_K[arm_d] == 1

    seed = 41
    cap_d = v0_53n_audit._run_one_arm(
        arm=arm_d, version="v0.42", seed=seed, hazard=0, runs_root=tmp_path
    )

    for rec in cap_d.founder_records:
        assert rec.founder_body_energy_tick0 == 100.0
        assert rec.founder_body_starting_energy_tick0 == 100.0
        assert rec.founder_body_base_metabolic_cost_tick0 == 0.10
        assert rec.founder_body_effective_sensor_radius_override_tick0 is None

    # Exactly 1 of 5 founders has traits.override == 8 — the min-sensor lineage.
    overridden = [
        rec
        for rec in cap_d.founder_records
        if rec.founder_traits_effective_sensor_radius_override_tick0 == 8
    ]
    assert len(overridden) == 1
    sensor_radius_by_lineage = {
        rec.lineage_id: rec.founder_sensor_radius for rec in cap_d.founder_records
    }
    expected_bottom = v0_53n_audit._select_bottom_k_sensor_radius_lineages(
        sensor_radius_by_lineage, 1
    )
    assert len(expected_bottom) == 1
    assert overridden[0].lineage_id == expected_bottom[0]

    # The OTHER 4 founders have traits.override == None.
    non_overridden = [
        rec
        for rec in cap_d.founder_records
        if rec.founder_traits_effective_sensor_radius_override_tick0 is None
    ]
    assert len(non_overridden) == 4

    # Cross-arm anti-confusion: synthetic fixture with distinct sensor_radii
    # confirms bottom_lineage_ids[0] != top_lineage_ids[0].
    distinct = {0: 7, 1: 3, 2: 5, 3: 6, 4: 4}
    bot1 = v0_53n_audit._select_bottom_k_sensor_radius_lineages(distinct, 1)
    top1 = v0_53n_audit._select_top_k_sensor_radius_lineages(distinct, 1)
    assert bot1 == [1]
    assert top1 == [0]
    assert bot1[0] != top1[0]

    assert cap_d.layout_name == "widened_food_near1"
    assert cap_d.n_ticks == 400
    assert cap_d.body_effective_sensor_radius_override is None
    assert cap_d.final_tick_count <= 400

    # bottom1 captured in the run.
    assert cap_d.bottom1_lineage_id_in_run == expected_bottom[0]


# ---------------------------------------------------------------------------
# Test 7 — Arm E uses FOOD_NEAR1, body_config override 8 (byte-identical to v0.53m #7).
# ---------------------------------------------------------------------------


def test_arm_e_widened_food_near1_combined_modelwide_sr8_N400_uses_food_near1_layout_body_config_override_8_no_per_founder_override_and_n_ticks_400_with_explicit_geometry_and_modelwide_perception_asserts(  # noqa: E501, N802
    tmp_path,
):
    arm_e = v0_53n_audit.ARM_E_WIDENED_FOOD_NEAR1_COMBINED_MODELWIDE_SR8_N400

    bc_e = v0_53n_audit._body_config_for_arm(arm_e)
    assert isinstance(bc_e, BodyConfig)
    assert bc_e.starting_energy == 100.0
    assert bc_e.base_metabolic_cost == 0.10
    assert bc_e.effective_sensor_radius_override == 8

    assert v0_53n_audit.LAYOUT_NAME_BY_ARM[arm_e] == "widened_food_near1"
    assert v0_53n_audit.N_TICKS_BY_ARM[arm_e] == 400
    assert v0_53n_audit.BODY_EFFECTIVE_SENSOR_RADIUS_OVERRIDE_BY_ARM[arm_e] == 8
    assert v0_53n_audit.ARM_OVERRIDE_K[arm_e] is None

    seed = 41
    cap_e = v0_53n_audit._run_one_arm(
        arm=arm_e, version="v0.42", seed=seed, hazard=0, runs_root=tmp_path
    )

    for rec in cap_e.founder_records:
        assert rec.founder_body_energy_tick0 == 100.0
        assert rec.founder_body_starting_energy_tick0 == 100.0
        assert rec.founder_body_base_metabolic_cost_tick0 == 0.10
        assert rec.founder_body_effective_sensor_radius_override_tick0 == 8
        assert rec.founder_traits_effective_sensor_radius_override_tick0 is None

    assert cap_e.layout_name == "widened_food_near1"
    assert cap_e.n_ticks == 400
    assert cap_e.body_effective_sensor_radius_override == 8
    assert cap_e.final_tick_count <= 400


# ---------------------------------------------------------------------------
# Test 8 — Three-part SHA pinning (UNCHANGED from v0.53l/m).
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

V053N_CHAMBER_DRIVER_PATH: str = "src/hedonism_harness/experiments/fear_hunger_chamber.py"
V053N_MODEL_PATH: str = "src/hedonism_harness/model.py"


def test_no_src_modifications_compared_to_v0_53l_tip():
    """Three-part SHA pinning (v0.53n)."""
    repo_root = Path(__file__).parent.parent

    for rel_path, expected_hash in V052B_TIP_SHA256.items():
        path = repo_root / rel_path
        actual_hash = hashlib.sha256(path.read_bytes()).hexdigest()
        if actual_hash != expected_hash:
            raise AssertionError(
                "v0.53n is pre-registered to leave the science-core five files "
                "byte-identical to v0.52b-tip; update the pre-reg before changing "
                "src/core or src/experiments/layouts."
            )

    chamber_path = repo_root / V053N_CHAMBER_DRIVER_PATH
    actual_chamber_hash = hashlib.sha256(chamber_path.read_bytes()).hexdigest()
    if actual_chamber_hash != sha_pins.CHAMBER_DRIVER_SHA:
        raise AssertionError(
            "v0.53n is pre-registered to leave the chamber driver byte-identical "
            "to its v0.53l-tip hash recorded in tests/sha_pins.py."
        )

    model_path = repo_root / V053N_MODEL_PATH
    actual_model_hash = hashlib.sha256(model_path.read_bytes()).hexdigest()
    if actual_model_hash != sha_pins.MODEL_SHA:
        raise AssertionError(
            "v0.53n is pre-registered to leave model.py byte-identical to its "
            "v0.53l-tip hash recorded in tests/sha_pins.py."
        )


# ---------------------------------------------------------------------------
# Test 9 — bottom-K helper + min-lineage per-founder override targeting (NEW).
# ---------------------------------------------------------------------------


def test_bottom_k_helper_and_min_lineage_per_founder_override_targeting():
    # (9.a) Returns the bottom K lineages by sensor_radius (ascending).
    simple = {0: 2, 1: 5, 2: 4, 3: 1, 4: 6}
    assert v0_53n_audit._select_bottom_k_sensor_radius_lineages(simple, 1) == [3]
    assert v0_53n_audit._select_bottom_k_sensor_radius_lineages(simple, 2) == [3, 0]
    assert v0_53n_audit._select_bottom_k_sensor_radius_lineages(simple, 3) == [3, 0, 2]

    # (9.b) Tiebreak: {0: 3, 1: 3, 2: 5, 3: 6, 4: 4} with k=1 returns [0].
    tied = {0: 3, 1: 3, 2: 5, 3: 6, 4: 4}
    assert v0_53n_audit._select_bottom_k_sensor_radius_lineages(tied, 1) == [0]
    assert v0_53n_audit._select_bottom_k_sensor_radius_lineages(tied, 2) == [0, 1]

    # (9.c) Asymmetry vs top: {0: 7, 1: 3, 2: 5, 3: 6, 4: 4} —
    # bottom-K returns [1]; top-K returns [0].
    asymm = {0: 7, 1: 3, 2: 5, 3: 6, 4: 4}
    assert v0_53n_audit._select_bottom_k_sensor_radius_lineages(asymm, 1) == [1]
    assert v0_53n_audit._select_top_k_sensor_radius_lineages(asymm, 1) == [0]

    # (9.d) build_bottom_k_per_founder_overrides returns (overrides, bottom_lineage_ids)
    # with exactly 1 non-None entry at the matching position.
    seed = 41
    trait_cfg = TraitConfig(unbounded_mutation=True)
    overrides_k1, bottom_one = v0_53n_audit.build_bottom_k_per_founder_overrides(
        seed=seed, trait_config=trait_cfg, n_founders=5, k=1
    )
    assert len(overrides_k1) == 5
    assert len(bottom_one) == 1
    non_none_positions = [i for i, t in enumerate(overrides_k1) if t is not None]
    assert sorted(non_none_positions) == sorted(bottom_one)
    for lid in bottom_one:
        assert overrides_k1[lid] is not None
        assert overrides_k1[lid].effective_sensor_radius_override == 8

    # k=1 single-element output reproduces argmin-sensor-radius selection.
    streams = make_streams(seed)
    sampled = [random_traits(trait_cfg, streams.mutation) for _ in range(5)]
    sensor_radius_by_lineage = {i: int(sampled[i].sensor_radius) for i in range(5)}
    expected_min = v0_53n_audit._select_bottom_k_sensor_radius_lineages(
        sensor_radius_by_lineage, 1
    )[0]
    assert bottom_one[0] == expected_min


# ---------------------------------------------------------------------------
# Test 10 — per_founder_traits_overrides seam validation carries forward.
# ---------------------------------------------------------------------------


_SEAM_TEST_LAYOUT = v0_53n_audit.FOOD_NEAR1_LAYOUT
_SEAM_TEST_N_TICKS = 5
_SEAM_TEST_N_FOUNDERS = 5
_SEAM_TEST_TRAIT_CFG = TraitConfig(unbounded_mutation=True)


def _captured_founder_traits(model_obj) -> list:
    founders = sorted(model_obj.agents, key=lambda a: int(a.body.lineage_id))
    return [a.body.traits for a in founders]


def _run_chamber_with_setup_capture(
    *,
    seed: int,
    n_founders: int,
    n_ticks: int,
    layout,
    body_config,
    trait_config,
    per_founder_traits_overrides,
    runs_root,
):
    captured: dict[str, list] = {"founders": []}

    def setup(model_obj):
        captured["founders"] = _captured_founder_traits(model_obj)

    run_chamber(
        seed=seed,
        runs_root=runs_root,
        run_id=f"seam-{seed}",
        n_founders=n_founders,
        n_ticks=n_ticks,
        layout=layout,
        trait_config=trait_config,
        body_config=body_config,
        per_founder_traits_overrides=per_founder_traits_overrides,
        write_outputs=False,
        setup_observer=setup,
    )
    return captured["founders"]


def test_per_founder_traits_overrides_seam_validation_carries_forward_from_v0_53l_m(tmp_path):
    seed = 41
    bc = BodyConfig(starting_energy=100.0, base_metabolic_cost=0.10)
    layout = _SEAM_TEST_LAYOUT
    n_founders = _SEAM_TEST_N_FOUNDERS
    n_ticks = _SEAM_TEST_N_TICKS
    trait_cfg = _SEAM_TEST_TRAIT_CFG

    dummy_traits = random_traits(trait_cfg, make_streams(seed).mutation)
    with pytest.raises(ValueError, match=r".*mutually exclusive.*"):
        run_chamber(
            seed=seed,
            runs_root=tmp_path / "mut_exc",
            run_id="seam-mutual-exclusion",
            n_founders=n_founders,
            n_ticks=n_ticks,
            layout=layout,
            trait_config=trait_cfg,
            body_config=bc,
            traits_override=dummy_traits,
            per_founder_traits_overrides=[None] * n_founders,
            write_outputs=False,
        )

    with pytest.raises(ValueError, match=r".*length.*"):
        run_chamber(
            seed=seed,
            runs_root=tmp_path / "len_check",
            run_id="seam-length-check",
            n_founders=n_founders,
            n_ticks=n_ticks,
            layout=layout,
            trait_config=trait_cfg,
            body_config=bc,
            per_founder_traits_overrides=[None] * (n_founders - 1),
            write_outputs=False,
        )

    founders_default = _run_chamber_with_setup_capture(
        seed=seed,
        n_founders=n_founders,
        n_ticks=n_ticks,
        layout=layout,
        body_config=bc,
        trait_config=trait_cfg,
        per_founder_traits_overrides=None,
        runs_root=tmp_path / "default_a",
    )
    captured_b: dict[str, list] = {"founders": []}

    def setup_b(model_obj):
        captured_b["founders"] = _captured_founder_traits(model_obj)

    run_chamber(
        seed=seed,
        runs_root=tmp_path / "default_b",
        run_id="seam-default-no-param",
        n_founders=n_founders,
        n_ticks=n_ticks,
        layout=layout,
        trait_config=trait_cfg,
        body_config=bc,
        write_outputs=False,
        setup_observer=setup_b,
    )
    founders_no_param = captured_b["founders"]
    assert len(founders_default) == len(founders_no_param) == n_founders
    for a, b in zip(founders_default, founders_no_param, strict=True):
        assert a == b


# ---------------------------------------------------------------------------
# Test 11 — Label A picks MAX-sensor lineage on C/D/E; on D this is the
# alignment-control mechanism (the MAX-sensor lineage receives NO override).
# ---------------------------------------------------------------------------


def test_label_a_high_sensor_radius_lineage_picks_correct_lineage_AND_matches_c_max_only_target_AND_label_a_indexes_max_not_min_on_d(  # noqa: E501, N802
    tmp_path,
):
    # Synthetic selector validation.
    sensor_radius_by_lineage = {0: 2, 1: 5, 2: 4, 3: 1, 4: 6}
    label = v0_53n_audit._select_sensor_radius_label(sensor_radius_by_lineage)
    assert label == 4
    sensor_tied = {0: 6, 1: 5, 2: 6, 3: 6, 4: 4}
    label_tied = v0_53n_audit._select_sensor_radius_label(sensor_tied)
    assert label_tied == 0

    arm_c = v0_53n_audit.ARM_C_WIDENED_FOOD_NEAR1_COMBINED_MAX_LINEAGE_SR8_N400
    arm_d = v0_53n_audit.ARM_D_WIDENED_FOOD_NEAR1_COMBINED_MIN_LINEAGE_SR8_N400
    seed = 41

    # On C: Label A == max-sensor lineage == override recipient.
    cap_c = v0_53n_audit._run_one_arm(
        arm=arm_c, version="v0.42", seed=seed, hazard=0, runs_root=tmp_path
    )
    rows_c = v0_53n_audit._aggregate_per_lineage(cap_c)
    label_a_lid_c = next(
        (r.lineage_id for r in rows_c if r.is_high_sensor_radius_lineage),
        None,
    )
    override_lid_c = next(
        (
            rec.lineage_id
            for rec in cap_c.founder_records
            if rec.founder_traits_effective_sensor_radius_override_tick0 == 8
        ),
        None,
    )
    assert label_a_lid_c is not None
    assert override_lid_c is not None
    assert label_a_lid_c == override_lid_c

    # On D: Label A == max-sensor lineage; the OVERRIDE recipient is the
    # MIN-sensor lineage (NOT the same lineage). This is the
    # alignment-control mechanism.
    cap_d = v0_53n_audit._run_one_arm(
        arm=arm_d, version="v0.42", seed=seed, hazard=0, runs_root=tmp_path
    )
    rows_d = v0_53n_audit._aggregate_per_lineage(cap_d)
    label_a_lid_d = next(
        (r.lineage_id for r in rows_d if r.is_high_sensor_radius_lineage),
        None,
    )
    override_lid_d = next(
        (
            rec.lineage_id
            for rec in cap_d.founder_records
            if rec.founder_traits_effective_sensor_radius_override_tick0 == 8
        ),
        None,
    )
    assert label_a_lid_d is not None
    assert override_lid_d is not None
    # The lineage Label A picks is the max-sensor lineage on D.
    assert cap_d.top1_lineage_id_in_run == label_a_lid_d
    # The lineage that received the override is the min-sensor lineage.
    assert cap_d.bottom1_lineage_id_in_run == override_lid_d
    # Under matched seed, Label A pick is the same on C and D.
    assert label_a_lid_c == label_a_lid_d
    # Sensor_radius values differ enough that bottom1 != top1 on this fixture.
    sensor_radius_by_lineage_d = {
        rec.lineage_id: rec.founder_sensor_radius for rec in cap_d.founder_records
    }
    # If sensor_radii are not all equal, label_a (max) != override (min).
    distinct_radii = len(set(sensor_radius_by_lineage_d.values())) > 1
    if distinct_radii:
        assert label_a_lid_d != override_lid_d


# ---------------------------------------------------------------------------
# Test 12 — Label B four variants tiebreak at each window.
# ---------------------------------------------------------------------------


def _build_capture_minimal(arm: str, n_ticks: int) -> object:
    layout = v0_53n_audit._layout_for_arm(arm)
    cap = v0_53n_audit._RunCapture(
        arm=arm,
        layout_name=v0_53n_audit.LAYOUT_NAME_BY_ARM[arm],
        safe_x_min=int(layout.safe_x_min),
        safe_x_max=int(layout.safe_x_max),
        hazard_x_min=int(layout.hazard_x_min),
        hazard_x_max=int(layout.hazard_x_max),
        food_x_min=int(layout.food_x_min),
        food_x_max=int(layout.food_x_max),
        world_width=int(layout.width),
        spawn_x=int(layout.resolved_spawn_x),
        height=int(layout.height),
        body_starting_energy=v0_53n_audit.BODY_STARTING_ENERGY_BY_ARM[arm],
        body_base_metabolic_cost=v0_53n_audit.BODY_BASE_METABOLIC_COST_BY_ARM[arm],
        body_effective_sensor_radius_override=(
            v0_53n_audit.BODY_EFFECTIVE_SENSOR_RADIUS_OVERRIDE_BY_ARM[arm]
        ),
        n_ticks=n_ticks,
        version="v0.42",
        seed=41,
        hazard=0,
    )
    cap.lineage_by_agent = {0: 0}
    cap.birth_tick_by_agent = {0: 0}
    cap.founder_records = [
        v0_53n_audit._FounderRecord(
            lineage_id=0,
            founder_index=0,
            founder_sensor_radius=4,
            founder_reproduction_drive=0.5,
            founder_metabolic_rate=0.5,
            founder_body_energy_tick0=cap.body_starting_energy,
            founder_body_starting_energy_tick0=cap.body_starting_energy,
            founder_body_base_metabolic_cost_tick0=cap.body_base_metabolic_cost,
            founder_body_effective_sensor_radius_override_tick0=(
                cap.body_effective_sensor_radius_override
            ),
            founder_traits_effective_sensor_radius_override_tick0=None,
        )
    ]
    cap.energy_threshold = 5.0
    cap.min_age = 1
    return cap


def test_label_b_four_variants_three_tier_tiebreak_at_each_window_with_pre400_c_and_d_and_e_only():
    candidates_count_tiebreak = [(0, 0.5, 2), (1, 0.5, 4), (2, 0.4, 5)]
    assert v0_53n_audit._select_fraction_label(candidates_count_tiebreak) == 1

    candidates_min_lid = [(3, 0.5, 4), (1, 0.5, 4), (2, 0.5, 4)]
    assert v0_53n_audit._select_fraction_label(candidates_min_lid) == 1

    candidates_simple = [(0, 0.3, 5), (1, 0.7, 1), (2, 0.5, 3)]
    assert v0_53n_audit._select_fraction_label(candidates_simple) == 1

    assert v0_53n_audit._select_fraction_label([]) is None

    energy_threshold = 5.0
    min_age = 1
    all_lineages = [0, 1, 2]
    snaps = [
        v0_53n_audit._ReadinessSnapshot(agent_id=10, lineage_id=0, energy=10.0, age=2),
        v0_53n_audit._ReadinessSnapshot(agent_id=11, lineage_id=0, energy=4.0, age=2),
        v0_53n_audit._ReadinessSnapshot(agent_id=20, lineage_id=1, energy=10.0, age=2),
        v0_53n_audit._ReadinessSnapshot(agent_id=30, lineage_id=2, energy=10.0, age=2),
        v0_53n_audit._ReadinessSnapshot(agent_id=31, lineage_id=2, energy=10.0, age=2),
    ]
    selected_a, _, _, fr_a = v0_53n_audit._readiness_label_at_tick(
        all_lineages, snaps, energy_threshold, min_age
    )
    assert selected_a == 2
    assert fr_a[1] == 1.0
    assert fr_a[2] == 1.0

    # pre400 NaN on A/B; bool on C/D/E.
    cap_a = _build_capture_minimal(v0_53n_audit.ARM_A_NULL_V025, 200)
    cap_b = _build_capture_minimal(v0_53n_audit.ARM_B_WIDENED_V025, 200)
    cap_c = _build_capture_minimal(
        v0_53n_audit.ARM_C_WIDENED_FOOD_NEAR1_COMBINED_MAX_LINEAGE_SR8_N400, 400
    )
    cap_d = _build_capture_minimal(
        v0_53n_audit.ARM_D_WIDENED_FOOD_NEAR1_COMBINED_MIN_LINEAGE_SR8_N400, 400
    )
    cap_e = _build_capture_minimal(
        v0_53n_audit.ARM_E_WIDENED_FOOD_NEAR1_COMBINED_MODELWIDE_SR8_N400, 400
    )
    rows_a = v0_53n_audit._aggregate_per_lineage(cap_a)
    rows_b = v0_53n_audit._aggregate_per_lineage(cap_b)
    rows_c = v0_53n_audit._aggregate_per_lineage(cap_c)
    rows_d = v0_53n_audit._aggregate_per_lineage(cap_d)
    rows_e = v0_53n_audit._aggregate_per_lineage(cap_e)
    a_label = rows_a[0].is_high_tick400_readiness_fraction_lineage
    b_label = rows_b[0].is_high_tick400_readiness_fraction_lineage
    c_label = rows_c[0].is_high_tick400_readiness_fraction_lineage
    d_label = rows_d[0].is_high_tick400_readiness_fraction_lineage
    e_label = rows_e[0].is_high_tick400_readiness_fraction_lineage
    assert isinstance(a_label, float)
    assert math.isnan(a_label)
    assert isinstance(b_label, float)
    assert math.isnan(b_label)
    assert isinstance(c_label, bool)
    assert isinstance(d_label, bool)
    assert isinstance(e_label, bool)


# ---------------------------------------------------------------------------
# Test 13 — pre400 strictly extends pre200/pre100/pre50 on C/D/E.
# ---------------------------------------------------------------------------


def _seed_pre_buckets(capture: object, event_ticks: list[int]) -> None:
    aid = 7
    for tick_now in event_ticks:
        if tick_now <= v0_53n_audit.TICK_50:
            capture.pre50_food_events_by_agent[aid] = (
                capture.pre50_food_events_by_agent.get(aid, 0) + 1
            )
            capture.pre50_food_energy_by_agent[aid] = (
                capture.pre50_food_energy_by_agent.get(aid, 0.0) + 1.0
            )
        if tick_now <= v0_53n_audit.TICK_100:
            capture.pre100_food_events_by_agent[aid] = (
                capture.pre100_food_events_by_agent.get(aid, 0) + 1
            )
            capture.pre100_food_energy_by_agent[aid] = (
                capture.pre100_food_energy_by_agent.get(aid, 0.0) + 1.0
            )
        if tick_now <= v0_53n_audit.TICK_200:
            capture.pre200_food_events_by_agent[aid] = (
                capture.pre200_food_events_by_agent.get(aid, 0) + 1
            )
            capture.pre200_food_energy_by_agent[aid] = (
                capture.pre200_food_energy_by_agent.get(aid, 0.0) + 1.0
            )
        if tick_now <= v0_53n_audit.TICK_400:
            capture.pre400_food_events_by_agent[aid] = (
                capture.pre400_food_events_by_agent.get(aid, 0) + 1
            )
            capture.pre400_food_energy_by_agent[aid] = (
                capture.pre400_food_energy_by_agent.get(aid, 0.0) + 1.0
            )


def _build_capture_for_pre_extends(arm: str) -> object:
    layout = v0_53n_audit._layout_for_arm(arm)
    return v0_53n_audit._RunCapture(
        arm=arm,
        layout_name=v0_53n_audit.LAYOUT_NAME_BY_ARM[arm],
        safe_x_min=int(layout.safe_x_min),
        safe_x_max=int(layout.safe_x_max),
        hazard_x_min=int(layout.hazard_x_min),
        hazard_x_max=int(layout.hazard_x_max),
        food_x_min=int(layout.food_x_min),
        food_x_max=int(layout.food_x_max),
        world_width=int(layout.width),
        spawn_x=int(layout.resolved_spawn_x),
        height=int(layout.height),
        body_starting_energy=100.0,
        body_base_metabolic_cost=0.10,
        body_effective_sensor_radius_override=(
            v0_53n_audit.BODY_EFFECTIVE_SENSOR_RADIUS_OVERRIDE_BY_ARM[arm]
        ),
        n_ticks=400,
        version="v0.42",
        seed=41,
        hazard=0,
    )


def test_pre400_window_strictly_extends_pre200_pre100_pre50_windows_on_c_and_d_and_e_arms():
    event_ticks = [10, 30, 60, 90, 130, 180, 200, 230, 280, 350, 380, 400]
    aid = 7
    cap_c = _build_capture_for_pre_extends(
        v0_53n_audit.ARM_C_WIDENED_FOOD_NEAR1_COMBINED_MAX_LINEAGE_SR8_N400
    )
    cap_d = _build_capture_for_pre_extends(
        v0_53n_audit.ARM_D_WIDENED_FOOD_NEAR1_COMBINED_MIN_LINEAGE_SR8_N400
    )
    cap_e = _build_capture_for_pre_extends(
        v0_53n_audit.ARM_E_WIDENED_FOOD_NEAR1_COMBINED_MODELWIDE_SR8_N400
    )
    _seed_pre_buckets(cap_c, event_ticks)
    _seed_pre_buckets(cap_d, event_ticks)
    _seed_pre_buckets(cap_e, event_ticks)
    for cap in (cap_c, cap_d, cap_e):
        assert cap.pre50_food_events_by_agent[aid] == 2
        assert cap.pre100_food_events_by_agent[aid] == 4
        assert cap.pre200_food_events_by_agent[aid] == 7
        assert cap.pre400_food_events_by_agent[aid] == 12

    cap_a = _build_capture_minimal(v0_53n_audit.ARM_A_NULL_V025, 200)
    cap_b = _build_capture_minimal(v0_53n_audit.ARM_B_WIDENED_V025, 200)
    rows_a = v0_53n_audit._aggregate_per_lineage(cap_a)
    rows_b = v0_53n_audit._aggregate_per_lineage(cap_b)
    assert math.isnan(rows_a[0].pre400_food_events_count)
    assert math.isnan(rows_b[0].pre400_food_events_count)


# ---------------------------------------------------------------------------
# Test 14 — Sub-verdict PRESENT requires >= 2/3 firing cells; strict NaN.
# ---------------------------------------------------------------------------


def test_subverdict_present_requires_two_thirds_firing_cells_with_nan_treated_as_non_firing_strict():  # noqa: E501
    arm = v0_53n_audit.ARM_D_WIDENED_FOOD_NEAR1_COMBINED_MIN_LINEAGE_SR8_N400
    window = v0_53n_audit.TICK_400

    summaries_a_2firing_1nan = _three_summaries_for_arm_window(
        arm, window, (+0.6, +0.6, float("nan")), v0_53n_audit.LABEL_A_NAME
    )
    summaries_b_clean = _three_summaries_for_arm_window(
        arm, window, (+0.6, +0.6, -0.6), v0_53n_audit.LABEL_B_TICK400_NAME
    )
    assert (
        v0_53n_audit._arm_subverdict_at_window(
            arm, window, summaries_a_2firing_1nan, summaries_b_clean
        )
        == v0_53n_audit.SUBVERDICT_D_FOOD_NEAR1_TICK400_PRESENT
    )

    summaries_a_1firing_2nan = _three_summaries_for_arm_window(
        arm, window, (+0.6, float("nan"), float("nan")), v0_53n_audit.LABEL_A_NAME
    )
    assert (
        v0_53n_audit._arm_subverdict_at_window(
            arm, window, summaries_a_1firing_2nan, summaries_b_clean
        )
        == v0_53n_audit.SUBVERDICT_D_FOOD_NEAR1_TICK400_PARTIAL
    )

    summaries_a_all_nan = _three_summaries_for_arm_window(
        arm, window, (float("nan"), float("nan"), float("nan")), v0_53n_audit.LABEL_A_NAME
    )
    assert (
        v0_53n_audit._arm_subverdict_at_window(arm, window, summaries_a_all_nan, summaries_b_clean)
        == v0_53n_audit.SUBVERDICT_D_FOOD_NEAR1_TICK400_PARTIAL
    )

    summaries_b_all_nan = _three_summaries_for_arm_window(
        arm,
        window,
        (float("nan"), float("nan"), float("nan")),
        v0_53n_audit.LABEL_B_TICK400_NAME,
    )
    assert (
        v0_53n_audit._arm_subverdict_at_window(
            arm, window, summaries_a_all_nan, summaries_b_all_nan
        )
        == v0_53n_audit.SUBVERDICT_D_FOOD_NEAR1_TICK400_NOT_FOUND
    )


# ---------------------------------------------------------------------------
# Test 15 — Priority 3 asymmetric halt rule (six branches A/B/C/D/E/F).
# ---------------------------------------------------------------------------


def test_priority_3_min_lineage_label_b_opposite_sign_halt_is_reachability_gated_AND_label_a_specific_AND_d_label_a_wrong_sign_does_not_halt():  # noqa: E501, N802
    bridge_clean = _zero_drift_bridge_re_anchor()

    # Helpers for D summaries.
    label_a_present = _d_summaries_kind("PRESENT", v0_53n_audit.LABEL_A_NAME)
    label_a_not_present = _d_summaries_kind("NOT_PRESENT", v0_53n_audit.LABEL_A_NAME)
    label_a_wrong = _d_summaries_kind("WRONG_SIGN", v0_53n_audit.LABEL_A_NAME)
    label_b_present = _d_summaries_kind("PRESENT", v0_53n_audit.LABEL_B_TICK400_NAME)
    label_b_wrong = _d_summaries_kind("WRONG_SIGN", v0_53n_audit.LABEL_B_TICK400_NAME)

    # Branch A: D Label B wrong-sign + D reach 0.30 -> priority 3 fires.
    rollup_a, phrase_a = v0_53n_audit._evaluate_rollup(
        a_null_tick50_subverdict=v0_53n_audit.SUBVERDICT_A_NULL_V025_TICK50_PRESENT,
        d_tick400_label_a_summaries=label_a_present,
        d_tick400_label_b_summaries=label_b_wrong,
        corpus_re_anchor=[],
        bridge_re_anchor=bridge_clean,
        b_widened_v025_reachability_tick200=0.0,
        d_reachability_tick400=0.30,
        **_green_anchor_kwargs(),
    )
    assert rollup_a == v0_53n_audit.ROLLUP_MIN_LINEAGE_LABEL_B_OPPOSITE_SIGN_HALT
    assert "AND D reachability at tick-400 clears the locked 25% threshold" in phrase_a

    # Branch B: D Label B wrong-sign + D reach 0.20 -> priority 3 SKIPS; priority 7 fires.
    rollup_b, _ = v0_53n_audit._evaluate_rollup(
        a_null_tick50_subverdict=v0_53n_audit.SUBVERDICT_A_NULL_V025_TICK50_PRESENT,
        d_tick400_label_a_summaries=label_a_present,
        d_tick400_label_b_summaries=label_b_wrong,
        corpus_re_anchor=[],
        bridge_re_anchor=bridge_clean,
        b_widened_v025_reachability_tick200=0.0,
        d_reachability_tick400=0.20,
        **_green_anchor_kwargs(),
    )
    assert rollup_b == v0_53n_audit.ROLLUP_MIN_LINEAGE_ACCESS_BELOW_REACHABILITY_THRESHOLD

    # Branch C: D Label A wrong-sign only (Label B no wrong-sign) + reach 0.30
    # -> priority 3 does NOT fire; asymmetric-halt routes to priority 4 (DECOUPLES).
    rollup_c, _ = v0_53n_audit._evaluate_rollup(
        a_null_tick50_subverdict=v0_53n_audit.SUBVERDICT_A_NULL_V025_TICK50_PRESENT,
        d_tick400_label_a_summaries=label_a_wrong,
        d_tick400_label_b_summaries=label_b_present,
        corpus_re_anchor=[],
        bridge_re_anchor=bridge_clean,
        b_widened_v025_reachability_tick200=0.0,
        d_reachability_tick400=0.30,
        **_green_anchor_kwargs(),
    )
    assert (
        rollup_c
        == v0_53n_audit.ROLLUP_MIN_LINEAGE_ACCESS_RESCUES_REACHABILITY_AND_DECOUPLES_LABEL_A
    )

    # Branch D: both Label A AND Label B have wrong-sign cells + reach 0.30
    # -> priority 3 fires (Label B wrong-sign alone is sufficient).
    rollup_d, _ = v0_53n_audit._evaluate_rollup(
        a_null_tick50_subverdict=v0_53n_audit.SUBVERDICT_A_NULL_V025_TICK50_PRESENT,
        d_tick400_label_a_summaries=label_a_wrong,
        d_tick400_label_b_summaries=label_b_wrong,
        corpus_re_anchor=[],
        bridge_re_anchor=bridge_clean,
        b_widened_v025_reachability_tick200=0.0,
        d_reachability_tick400=0.30,
        **_green_anchor_kwargs(),
    )
    assert rollup_d == v0_53n_audit.ROLLUP_MIN_LINEAGE_LABEL_B_OPPOSITE_SIGN_HALT

    # Branch E: D Label B PRESENT + D Label A NOT PRESENT + reach 0.30 -> priority 4.
    rollup_e, _ = v0_53n_audit._evaluate_rollup(
        a_null_tick50_subverdict=v0_53n_audit.SUBVERDICT_A_NULL_V025_TICK50_PRESENT,
        d_tick400_label_a_summaries=label_a_not_present,
        d_tick400_label_b_summaries=label_b_present,
        corpus_re_anchor=[],
        bridge_re_anchor=bridge_clean,
        b_widened_v025_reachability_tick200=0.0,
        d_reachability_tick400=0.30,
        **_green_anchor_kwargs(),
    )
    assert (
        rollup_e
        == v0_53n_audit.ROLLUP_MIN_LINEAGE_ACCESS_RESCUES_REACHABILITY_AND_DECOUPLES_LABEL_A
    )

    # Branch F: D Label A PRESENT + D Label B PRESENT + reach 0.30 -> priority 5.
    rollup_f, _ = v0_53n_audit._evaluate_rollup(
        a_null_tick50_subverdict=v0_53n_audit.SUBVERDICT_A_NULL_V025_TICK50_PRESENT,
        d_tick400_label_a_summaries=label_a_present,
        d_tick400_label_b_summaries=label_b_present,
        corpus_re_anchor=[],
        bridge_re_anchor=bridge_clean,
        b_widened_v025_reachability_tick200=0.0,
        d_reachability_tick400=0.30,
        **_green_anchor_kwargs(),
    )
    assert rollup_f == v0_53n_audit.ROLLUP_MIN_LINEAGE_ACCESS_RESCUES_FULL_BRIDGE


# ---------------------------------------------------------------------------
# Test 16 — Comprehensive: C/E anchor + D partition + locked-phrase verbatim
# substring assertions + priority cascade.
# ---------------------------------------------------------------------------


def test_c_anchor_v053l_AND_e_anchor_v053k_AND_d_tick_400_reachability_threshold_partition_AND_rollup_locked_phrases_fire_verbatim_AND_priority_cascade_partition_total():  # noqa: E501, N802, PLR0915
    bridge_clean = _zero_drift_bridge_re_anchor()
    bridge_drift = list(bridge_clean)
    bridge_drift[0] = v0_53n_audit.BridgeReAnchorRow(
        label=bridge_drift[0].label,
        observable=bridge_drift[0].observable,
        published_signed_d=bridge_drift[0].published_signed_d,
        derived_signed_d=bridge_drift[0].published_signed_d + 1.5,
        drift_abs=1.5,
        halts=True,
    )

    # Predecessor stack (ELEVEN long: v0.53c..v0.53m) preserved verbatim.
    eleven_predecessor_tags = (
        "WIDENED_BELOW_REACHABILITY_THRESHOLD_AT_TICK_200",
        "WIDENED_BELOW_REACHABILITY_THRESHOLD_UNDER_RELAXED_INFLUX",
        "RELAXED_OPPOSITE_SIGN_HALT",
        "WIDENED_BELOW_REACHABILITY_THRESHOLD_UNDER_BASE_METABOLIC_COST_010",
        "WIDENED_BELOW_REACHABILITY_THRESHOLD_UNDER_COMBINED_SE100_BMC010",
        "WIDENED_BELOW_REACHABILITY_THRESHOLD_AT_TIME_HORIZON_400",
        "WIDENED_BRIDGE_RESCUED_BY_FOOD_NEAR2",
        "WIDENED_BELOW_REACHABILITY_THRESHOLD_UNDER_FOOD_NEAR1",
        "WIDENED_BRIDGE_PARTIALLY_RESCUED_BY_SENSOR_RADIUS_8",
        "WIDENED_BRIDGE_RESCUED_BY_MAX_LINEAGE_SENSOR_RADIUS_8",
        "WIDENED_BRIDGE_RESCUED_BY_TOP2_LINEAGE_SENSOR_RADIUS_8",
    )
    eleven_predecessor_versions = (
        "v0.53c",
        "v0.53d",
        "v0.53e",
        "v0.53f",
        "v0.53g",
        "v0.53h",
        "v0.53i",
        "v0.53j",
        "v0.53k",
        "v0.53l",
        "v0.53m",
    )

    label_a_present = _d_summaries_kind("PRESENT", v0_53n_audit.LABEL_A_NAME)
    label_a_not_present = _d_summaries_kind("NOT_PRESENT", v0_53n_audit.LABEL_A_NAME)
    label_b_present = _d_summaries_kind("PRESENT", v0_53n_audit.LABEL_B_TICK400_NAME)
    label_b_not_present = _d_summaries_kind("NOT_PRESENT", v0_53n_audit.LABEL_B_TICK400_NAME)
    label_b_wrong = _d_summaries_kind("WRONG_SIGN", v0_53n_audit.LABEL_B_TICK400_NAME)

    # ----- Priority 3 locked phrase verbatim substrings -----
    _, phrase_p3 = v0_53n_audit._evaluate_rollup(
        a_null_tick50_subverdict=v0_53n_audit.SUBVERDICT_A_NULL_V025_TICK50_PRESENT,
        d_tick400_label_a_summaries=label_a_present,
        d_tick400_label_b_summaries=label_b_wrong,
        corpus_re_anchor=[],
        bridge_re_anchor=bridge_clean,
        b_widened_v025_reachability_tick200=0.0,
        d_reachability_tick400=0.30,
        **_green_anchor_kwargs(),
    )
    assert (
        "a v0.53n D_widened_food_near1_combined_min_lineage_sr8_N400 tick-400 "
        "**Label B** spatial / foraging primary fires in the WRONG direction"
    ) in phrase_p3
    assert "D Label A wrong-sign or deadband is NOT a halt" in phrase_p3
    assert "AND D reachability at tick-400 clears the locked 25% threshold" in phrase_p3

    # ----- Priority 4 DECOUPLES locked phrase verbatim substrings -----
    _, phrase_p4 = v0_53n_audit._evaluate_rollup(
        a_null_tick50_subverdict=v0_53n_audit.SUBVERDICT_A_NULL_V025_TICK50_PRESENT,
        d_tick400_label_a_summaries=label_a_not_present,
        d_tick400_label_b_summaries=label_b_present,
        corpus_re_anchor=[],
        bridge_re_anchor=bridge_clean,
        b_widened_v025_reachability_tick200=0.0,
        d_reachability_tick400=0.50,
        **_green_anchor_kwargs(),
    )
    assert "the **min-sensor-lineage** per-lineage perception intervention" in phrase_p4
    assert (
        "the v0.48 `is_high_sensor_radius_lineage` selector still picks the "
        "MAX-sensor lineage for Label A indexing — that lineage receives NO override"
    ) in phrase_p4
    assert (
        "**The result is consistent with the v0.53l/m Label A rescue depending on "
        "alignment between the boosted perception channel and the max-sensor "
        "lineage label, while reachability itself can be rescued by perception "
        "access assigned to a non-max lineage.**"
    ) in phrase_p4
    for tag in eleven_predecessor_tags:
        assert tag in phrase_p4
    for ver in eleven_predecessor_versions:
        assert ver in phrase_p4

    # ----- Priority 5 FULL_BRIDGE locked phrase verbatim substrings -----
    _, phrase_p5 = v0_53n_audit._evaluate_rollup(
        a_null_tick50_subverdict=v0_53n_audit.SUBVERDICT_A_NULL_V025_TICK50_PRESENT,
        d_tick400_label_a_summaries=label_a_present,
        d_tick400_label_b_summaries=label_b_present,
        corpus_re_anchor=[],
        bridge_re_anchor=bridge_clean,
        b_widened_v025_reachability_tick200=0.0,
        d_reachability_tick400=0.50,
        **_green_anchor_kwargs(),
    )
    assert "**This is the surprising and high-information outcome.**" in phrase_p5
    assert "the lineage labels / override targeting / measurement wiring need audit" in phrase_p5
    assert "flagged for audit and follow-up" in phrase_p5

    # ----- Priority 6 PARTIAL_OR_MIXED locked phrase verbatim substrings -----
    # Label A NOT PRESENT + Label B NOT PRESENT (catch-all).
    _, phrase_p6 = v0_53n_audit._evaluate_rollup(
        a_null_tick50_subverdict=v0_53n_audit.SUBVERDICT_A_NULL_V025_TICK50_PRESENT,
        d_tick400_label_a_summaries=label_a_not_present,
        d_tick400_label_b_summaries=label_b_not_present,
        corpus_re_anchor=[],
        bridge_re_anchor=bridge_clean,
        b_widened_v025_reachability_tick200=0.0,
        d_reachability_tick400=0.50,
        **_green_anchor_kwargs(),
    )
    assert (
        "a mixed or partial bridge signal that does not cleanly localize the alignment requirement"
    ) in phrase_p6

    # ----- Priority 7 BELOW_THRESHOLD locked phrase verbatim substrings -----
    _, phrase_p7 = v0_53n_audit._evaluate_rollup(
        a_null_tick50_subverdict=v0_53n_audit.SUBVERDICT_A_NULL_V025_TICK50_PRESENT,
        d_tick400_label_a_summaries=label_a_not_present,
        d_tick400_label_b_summaries=label_b_not_present,
        corpus_re_anchor=[],
        bridge_re_anchor=bridge_clean,
        b_widened_v025_reachability_tick200=0.0,
        d_reachability_tick400=0.10,
        **_green_anchor_kwargs(),
    )
    assert (
        "**Min-lineage override is NOT symmetric with max-lineage override "
        "under this corpus and implementation.**"
    ) in phrase_p7
    assert "starting position, early survival, trait package interactions" in phrase_p7
    for tag in eleven_predecessor_tags:
        assert tag in phrase_p7
    for ver in eleven_predecessor_versions:
        assert ver in phrase_p7

    # ----- Anchor cascade — 8 branches (priority 2 sub-conditions a-h) -----
    # Baseline GREEN -> priority 4 reachable.
    rollup_green, _ = v0_53n_audit._evaluate_rollup(
        a_null_tick50_subverdict=v0_53n_audit.SUBVERDICT_A_NULL_V025_TICK50_PRESENT,
        d_tick400_label_a_summaries=label_a_not_present,
        d_tick400_label_b_summaries=label_b_present,
        corpus_re_anchor=[],
        bridge_re_anchor=bridge_clean,
        b_widened_v025_reachability_tick200=0.0,
        d_reachability_tick400=0.50,
        **_green_anchor_kwargs(),
    )
    assert (
        rollup_green
        == v0_53n_audit.ROLLUP_MIN_LINEAGE_ACCESS_RESCUES_REACHABILITY_AND_DECOUPLES_LABEL_A
    )

    # 2.a — Tier-1 A drift halt.
    rollup_2a, _ = v0_53n_audit._evaluate_rollup(
        a_null_tick50_subverdict=v0_53n_audit.SUBVERDICT_A_NULL_V025_TICK50_PRESENT,
        d_tick400_label_a_summaries=label_a_present,
        d_tick400_label_b_summaries=label_b_present,
        corpus_re_anchor=[],
        bridge_re_anchor=bridge_drift,
        b_widened_v025_reachability_tick200=0.0,
        d_reachability_tick400=0.50,
        **_green_anchor_kwargs(),
    )
    assert rollup_2a == v0_53n_audit.ROLLUP_ANCHOR_REPLICATION_HALT

    # 2.b — Tier-2 B reachability halt.
    rollup_2b, _ = v0_53n_audit._evaluate_rollup(
        a_null_tick50_subverdict=v0_53n_audit.SUBVERDICT_A_NULL_V025_TICK50_PRESENT,
        d_tick400_label_a_summaries=label_a_present,
        d_tick400_label_b_summaries=label_b_present,
        corpus_re_anchor=[],
        bridge_re_anchor=bridge_clean,
        b_widened_v025_reachability_tick200=1.0 / 64.0,
        d_reachability_tick400=0.50,
        **_green_anchor_kwargs(),
    )
    assert rollup_2b == v0_53n_audit.ROLLUP_ANCHOR_REPLICATION_HALT

    # 2.c — C reachability drift halt.
    kw_2c = _green_anchor_kwargs()
    kw_2c["c_reachability_tick400"] = 60.0 / 64.0
    rollup_2c, _ = v0_53n_audit._evaluate_rollup(
        a_null_tick50_subverdict=v0_53n_audit.SUBVERDICT_A_NULL_V025_TICK50_PRESENT,
        d_tick400_label_a_summaries=label_a_present,
        d_tick400_label_b_summaries=label_b_present,
        corpus_re_anchor=[],
        bridge_re_anchor=bridge_clean,
        b_widened_v025_reachability_tick200=0.0,
        d_reachability_tick400=0.50,
        **kw_2c,
    )
    assert rollup_2c == v0_53n_audit.ROLLUP_ANCHOR_REPLICATION_HALT

    # 2.d — C sub-verdict drift halt.
    kw_2d = _green_anchor_kwargs()
    kw_2d["c_tick400_subverdict"] = v0_53n_audit.SUBVERDICT_C_FOOD_NEAR1_TICK400_PARTIAL
    rollup_2d, _ = v0_53n_audit._evaluate_rollup(
        a_null_tick50_subverdict=v0_53n_audit.SUBVERDICT_A_NULL_V025_TICK50_PRESENT,
        d_tick400_label_a_summaries=label_a_present,
        d_tick400_label_b_summaries=label_b_present,
        corpus_re_anchor=[],
        bridge_re_anchor=bridge_clean,
        b_widened_v025_reachability_tick200=0.0,
        d_reachability_tick400=0.50,
        **kw_2d,
    )
    assert rollup_2d == v0_53n_audit.ROLLUP_ANCHOR_REPLICATION_HALT

    # 2.e — C paired_d drift halt.
    kw_2e = _green_anchor_kwargs()
    drifted_c = dict(v0_53n_audit.V053L_C_TIER3_ANCHOR_PUBLISHED)
    drift_key_c = (v0_53n_audit.LABEL_A_NAME, "pre400_food_events_count")
    drifted_c[drift_key_c] = drifted_c[drift_key_c] + 0.005
    kw_2e["c_tick400_signed_d"] = drifted_c
    rollup_2e, _ = v0_53n_audit._evaluate_rollup(
        a_null_tick50_subverdict=v0_53n_audit.SUBVERDICT_A_NULL_V025_TICK50_PRESENT,
        d_tick400_label_a_summaries=label_a_present,
        d_tick400_label_b_summaries=label_b_present,
        corpus_re_anchor=[],
        bridge_re_anchor=bridge_clean,
        b_widened_v025_reachability_tick200=0.0,
        d_reachability_tick400=0.50,
        **kw_2e,
    )
    assert rollup_2e == v0_53n_audit.ROLLUP_ANCHOR_REPLICATION_HALT

    # 2.f — E reachability drift halt.
    kw_2f = _green_anchor_kwargs()
    kw_2f["e_reachability_tick400"] = 63.0 / 64.0
    rollup_2f, _ = v0_53n_audit._evaluate_rollup(
        a_null_tick50_subverdict=v0_53n_audit.SUBVERDICT_A_NULL_V025_TICK50_PRESENT,
        d_tick400_label_a_summaries=label_a_present,
        d_tick400_label_b_summaries=label_b_present,
        corpus_re_anchor=[],
        bridge_re_anchor=bridge_clean,
        b_widened_v025_reachability_tick200=0.0,
        d_reachability_tick400=0.50,
        **kw_2f,
    )
    assert rollup_2f == v0_53n_audit.ROLLUP_ANCHOR_REPLICATION_HALT

    # 2.g — E sub-verdict suffix drift halt.
    kw_2g = _green_anchor_kwargs()
    kw_2g["e_tick400_subverdict"] = v0_53n_audit.SUBVERDICT_E_FOOD_NEAR1_TICK400_PRESENT
    rollup_2g, _ = v0_53n_audit._evaluate_rollup(
        a_null_tick50_subverdict=v0_53n_audit.SUBVERDICT_A_NULL_V025_TICK50_PRESENT,
        d_tick400_label_a_summaries=label_a_present,
        d_tick400_label_b_summaries=label_b_present,
        corpus_re_anchor=[],
        bridge_re_anchor=bridge_clean,
        b_widened_v025_reachability_tick200=0.0,
        d_reachability_tick400=0.50,
        **kw_2g,
    )
    assert rollup_2g == v0_53n_audit.ROLLUP_ANCHOR_REPLICATION_HALT

    # 2.h — E paired_d drift halt.
    kw_2h = _green_anchor_kwargs()
    drifted_e = dict(v0_53n_audit.V053K_C_TIER3_ANCHOR_PUBLISHED)
    drift_key_e = (v0_53n_audit.LABEL_A_NAME, "pre400_food_events_count")
    drifted_e[drift_key_e] = drifted_e[drift_key_e] + 0.005
    kw_2h["e_tick400_signed_d"] = drifted_e
    rollup_2h, _ = v0_53n_audit._evaluate_rollup(
        a_null_tick50_subverdict=v0_53n_audit.SUBVERDICT_A_NULL_V025_TICK50_PRESENT,
        d_tick400_label_a_summaries=label_a_present,
        d_tick400_label_b_summaries=label_b_present,
        corpus_re_anchor=[],
        bridge_re_anchor=bridge_clean,
        b_widened_v025_reachability_tick200=0.0,
        d_reachability_tick400=0.50,
        **kw_2h,
    )
    assert rollup_2h == v0_53n_audit.ROLLUP_ANCHOR_REPLICATION_HALT

    # ----- Halt cascade priority order: priority 1 wins over all -----
    corpus_halt = [
        v0_53n_audit.ReAnchorRow(
            arm=v0_53n_audit.ARM_A_NULL_V025,
            version="v0.42",
            hazard=8,
            n_runs_contributing=8,
            a_share_h8_derived=0.700,
            a_share_h8_published=0.652,
            drift_abs=0.048,
            halts=True,
        )
    ]
    rollup_1, phrase_1 = v0_53n_audit._evaluate_rollup(
        a_null_tick50_subverdict=v0_53n_audit.SUBVERDICT_A_NULL_V025_TICK50_NOT_FOUND,
        d_tick400_label_a_summaries=label_a_present,
        d_tick400_label_b_summaries=label_b_wrong,
        corpus_re_anchor=corpus_halt,
        bridge_re_anchor=bridge_drift,
        b_widened_v025_reachability_tick200=1.0 / 64.0,
        d_reachability_tick400=0.50,
        **_green_anchor_kwargs(),
    )
    assert rollup_1 == v0_53n_audit.ROLLUP_CORPUS_DRIFT_HALT
    assert "v0.42" in phrase_1

    # Priority 2 wins when no priority 1.
    rollup_2_over_3, _ = v0_53n_audit._evaluate_rollup(
        a_null_tick50_subverdict=v0_53n_audit.SUBVERDICT_A_NULL_V025_TICK50_PRESENT,
        d_tick400_label_a_summaries=label_a_present,
        d_tick400_label_b_summaries=label_b_wrong,
        corpus_re_anchor=[],
        bridge_re_anchor=bridge_drift,
        b_widened_v025_reachability_tick200=0.0,
        d_reachability_tick400=0.50,
        **_green_anchor_kwargs(),
    )
    assert rollup_2_over_3 == v0_53n_audit.ROLLUP_ANCHOR_REPLICATION_HALT

    # ----- Partition exhaustiveness — all label-combinations route to a unique outcome -----
    label_a_kinds = ("PRESENT", "NOT_PRESENT")
    label_b_kinds = ("PRESENT", "NOT_PRESENT", "WRONG_SIGN")
    seen: dict[tuple[str, str, str], str] = {}
    for la_kind in label_a_kinds:
        for lb_kind in label_b_kinds:
            la_sums = _d_summaries_kind(la_kind, v0_53n_audit.LABEL_A_NAME)
            lb_sums = _d_summaries_kind(lb_kind, v0_53n_audit.LABEL_B_TICK400_NAME)
            for reach_kind, reach_val in (("above", 0.50), ("below", 0.10)):
                rollup_x, _ = v0_53n_audit._evaluate_rollup(
                    a_null_tick50_subverdict=v0_53n_audit.SUBVERDICT_A_NULL_V025_TICK50_PRESENT,
                    d_tick400_label_a_summaries=la_sums,
                    d_tick400_label_b_summaries=lb_sums,
                    corpus_re_anchor=[],
                    bridge_re_anchor=bridge_clean,
                    b_widened_v025_reachability_tick200=0.0,
                    d_reachability_tick400=reach_val,
                    **_green_anchor_kwargs(),
                )
                seen[(la_kind, lb_kind, reach_kind)] = rollup_x

    decouples = v0_53n_audit.ROLLUP_MIN_LINEAGE_ACCESS_RESCUES_REACHABILITY_AND_DECOUPLES_LABEL_A
    full_bridge = v0_53n_audit.ROLLUP_MIN_LINEAGE_ACCESS_RESCUES_FULL_BRIDGE
    mixed = v0_53n_audit.ROLLUP_MIN_LINEAGE_ACCESS_PARTIAL_OR_MIXED
    below = v0_53n_audit.ROLLUP_MIN_LINEAGE_ACCESS_BELOW_REACHABILITY_THRESHOLD
    halt_b = v0_53n_audit.ROLLUP_MIN_LINEAGE_LABEL_B_OPPOSITE_SIGN_HALT

    # Above-threshold partition (reach=0.50).
    assert seen[("PRESENT", "PRESENT", "above")] == full_bridge
    assert seen[("PRESENT", "NOT_PRESENT", "above")] == mixed
    assert seen[("PRESENT", "WRONG_SIGN", "above")] == halt_b
    assert seen[("NOT_PRESENT", "PRESENT", "above")] == decouples
    assert seen[("NOT_PRESENT", "NOT_PRESENT", "above")] == mixed
    assert seen[("NOT_PRESENT", "WRONG_SIGN", "above")] == halt_b

    # Below-threshold partition (reach=0.10) — all route to priority 7.
    for la_kind in label_a_kinds:
        for lb_kind in label_b_kinds:
            assert seen[(la_kind, lb_kind, "below")] == below


# Sanity imports retained.
_ = pytest
_ = replace
_ = csv
