"""v0.53l per-lineage perception heterogeneity probe — tests (16 locked).

Pre-reg: [[docs/experiments/fear_hunger_v0.53l.md]] §"Test list (locked,
16 tests)". Tests numbered to match the pre-reg's ordering. Test #5 / #6
extend v0.53k tests #5/#6 with per-founder override asserts. Test #7 is
the per-lineage reshape of the cross-arm contrast. Test #8 is the
three-part SHA pinning (Part A historical + Part B chamber + Part C model
via shared ``tests/sha_pins.py``). Test #9 is NEW: consolidated
six-pre-data seam-validation suite for ``per_founder_traits_overrides``
(mutual-exclusion / length / default-preserving / founder targeting /
non-target identity / stream-invariance proxy). Test #10 is NEW:
Label A high_sensor_radius_lineage picks the same lineage targeted by
the C-arm per-founder override. Tests #11..#16 carry forward from v0.53k
tests #10..#16 with v0.53l metadata updates.
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
    / "v0_53l_perception_max_lineage_sensor_radius_8_audit.py"
)
_spec = importlib.util.spec_from_file_location("v0_53l_audit", _SCRIPT_PATH)
assert _spec is not None
assert _spec.loader is not None
v0_53l_audit = importlib.util.module_from_spec(_spec)
sys.modules["v0_53l_audit"] = v0_53l_audit
_spec.loader.exec_module(v0_53l_audit)


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
    fires_expected = (not math.isnan(signed)) and signed >= v0_53l_audit.COHENS_D_THRESHOLD
    fires_wrong = (not math.isnan(signed)) and signed <= -v0_53l_audit.COHENS_D_THRESHOLD
    return v0_53l_audit.ObservableSummary(
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
        v0_53l_audit.TICK_50: v0_53l_audit.PRIMARY_OBSERVABLES_TICK50,
        v0_53l_audit.TICK_100: v0_53l_audit.PRIMARY_OBSERVABLES_TICK100,
        v0_53l_audit.TICK_200: v0_53l_audit.PRIMARY_OBSERVABLES_TICK200,
        v0_53l_audit.TICK_400: v0_53l_audit.PRIMARY_OBSERVABLES_TICK400,
    }
    obs = obs_table[window]
    return [
        _make_summary(arm=arm, observable=obs[i][0], sign=obs[i][1], paired_d=ds[i], label=label)
        for i in range(3)
    ]


def _zero_drift_bridge_re_anchor() -> list[object]:
    return [
        v0_53l_audit.BridgeReAnchorRow(
            label=label,
            observable=obs,
            published_signed_d=ref,
            derived_signed_d=ref,
            drift_abs=0.0,
            halts=False,
        )
        for (label, obs), ref in v0_53l_audit.V048_PUBLISHED_SIGNED_D.items()
    ]


def _green_d_anchor_kwargs() -> dict[str, object]:
    """Return rollup kwargs for D anchor that pass all three Tier-3 sub-conditions."""
    return {
        "d_reachability_tick400": v0_53l_audit.D_TIER3_REACHABILITY_LOCKED,
        "d_tick400_subverdict": v0_53l_audit.SUBVERDICT_D_FOOD_NEAR2_TICK400_PRESENT,
        "d_tick400_signed_d": dict(v0_53l_audit.D_TIER3_ANCHOR_PUBLISHED),
    }


def _c_tick400_subverdict_for_kind(kind: str) -> str:
    table = {
        "PRESENT": v0_53l_audit.SUBVERDICT_C_FOOD_NEAR1_TICK400_PRESENT,
        "PARTIAL": v0_53l_audit.SUBVERDICT_C_FOOD_NEAR1_TICK400_PARTIAL,
        "NOT_FOUND": v0_53l_audit.SUBVERDICT_C_FOOD_NEAR1_TICK400_NOT_FOUND,
        "OPPOSITE": v0_53l_audit.SUBVERDICT_C_FOOD_NEAR1_TICK400_OPPOSITE,
    }
    return table[kind]


# ---------------------------------------------------------------------------
# Test 1 — paired_d formula reproduces hand-computed signed_d on a fixture
# AND Tier-1 reference constants byte-equal v0.48..v0.53j published values
# AND Tier-3 D anchor reference constants byte-equal v0.53i published values.
# ---------------------------------------------------------------------------


def test_paired_d_function_reproduces_hand_computed_signed_d_on_fixture_and_tier1_v048_constants_and_tier3_v053i_constants():  # noqa: E501
    deltas = [1.0, 2.0, 1.5, 0.5, 2.5, 1.8, 0.9, 1.2]
    expected_mean = statistics.mean(deltas)
    expected_sd = statistics.stdev(deltas)
    expected_d = expected_mean / expected_sd
    derived_d = v0_53l_audit._paired_cohens_d(deltas)
    assert abs(derived_d - expected_d) < 1e-9

    pinned_v048 = {
        ("label_a_sensor_radius", "pre50_food_events_count"): +1.066,
        ("label_a_sensor_radius", "pre50_food_energy_acquired"): +1.066,
        ("label_a_sensor_radius", "mean_distance_to_nearest_food_cell_tick50"): +1.916,
        ("label_b_readiness_fraction_tick50", "pre50_food_events_count"): +0.916,
        ("label_b_readiness_fraction_tick50", "pre50_food_energy_acquired"): +0.916,
        ("label_b_readiness_fraction_tick50", "mean_distance_to_nearest_food_cell_tick50"): +1.179,
    }
    assert pinned_v048 == v0_53l_audit.V048_PUBLISHED_SIGNED_D

    # Tier-3 D anchor: six v0.53i published cells; tolerance 1e-3 absolute.
    pinned_v053i_d_anchor = {
        ("label_a_sensor_radius", "pre400_food_events_count"): +1.0357354787853512,
        ("label_a_sensor_radius", "pre400_food_energy_acquired"): +1.0357354787853512,
        ("label_a_sensor_radius", "mean_distance_to_nearest_food_cell_tick400"): +1.061633559034245,
        ("label_b_readiness_fraction_tick400", "pre400_food_events_count"): +5.3040008005819095,
        ("label_b_readiness_fraction_tick400", "pre400_food_energy_acquired"): +5.3040008005819095,
        (
            "label_b_readiness_fraction_tick400",
            "mean_distance_to_nearest_food_cell_tick400",
        ): +6.294727858398778,
    }
    assert pinned_v053i_d_anchor == v0_53l_audit.D_TIER3_ANCHOR_PUBLISHED
    expected_rounded = {
        ("label_a_sensor_radius", "pre400_food_events_count"): +1.036,
        ("label_a_sensor_radius", "pre400_food_energy_acquired"): +1.036,
        ("label_a_sensor_radius", "mean_distance_to_nearest_food_cell_tick400"): +1.062,
        ("label_b_readiness_fraction_tick400", "pre400_food_events_count"): +5.304,
        ("label_b_readiness_fraction_tick400", "pre400_food_energy_acquired"): +5.304,
        (
            "label_b_readiness_fraction_tick400",
            "mean_distance_to_nearest_food_cell_tick400",
        ): +6.295,
    }
    for key, exact in pinned_v053i_d_anchor.items():
        assert abs(exact - expected_rounded[key]) < 1e-3
    assert v0_53l_audit.D_TIER3_REACHABILITY_LOCKED == 35.0 / 64.0
    assert v0_53l_audit.D_TIER3_PAIRED_D_TOLERANCE == 1e-3


# ---------------------------------------------------------------------------
# Test 2 — A_null_V0_25 corpus a_share_h8 re-anchors v0.42 / v0.44 / v0.45.
# ---------------------------------------------------------------------------


def test_a_null_v025_corpus_a_share_h8_re_anchors_v042_v044_v045():
    clean = [
        v0_53l_audit.ReAnchorRow(
            arm=v0_53l_audit.ARM_A_NULL_V025,
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
    rollup, _ = v0_53l_audit._evaluate_rollup(
        a_null_tick50_subverdict=v0_53l_audit.SUBVERDICT_A_NULL_V025_TICK50_PRESENT,
        c_tick400_subverdict=v0_53l_audit.SUBVERDICT_C_FOOD_NEAR1_TICK400_PRESENT,
        corpus_re_anchor=clean,
        bridge_re_anchor=_zero_drift_bridge_re_anchor(),
        b_widened_v025_reachability_tick200=0.0,
        c_reachability_tick400=0.50,
        **_green_d_anchor_kwargs(),
    )
    assert rollup == v0_53l_audit.ROLLUP_WIDENED_BRIDGE_RESCUED_BY_MAX_LINEAGE_SENSOR_RADIUS_8

    drifted = list(clean)
    drifted[1] = v0_53l_audit.ReAnchorRow(
        arm=v0_53l_audit.ARM_A_NULL_V025,
        version="v0.44",
        hazard=8,
        n_runs_contributing=8,
        a_share_h8_derived=0.880,
        a_share_h8_published=0.878,
        drift_abs=0.002,
        halts=True,
    )
    rollup_d, phrase_d = v0_53l_audit._evaluate_rollup(
        a_null_tick50_subverdict=v0_53l_audit.SUBVERDICT_A_NULL_V025_TICK50_PRESENT,
        c_tick400_subverdict=v0_53l_audit.SUBVERDICT_C_FOOD_NEAR1_TICK400_PRESENT,
        corpus_re_anchor=drifted,
        bridge_re_anchor=_zero_drift_bridge_re_anchor(),
        b_widened_v025_reachability_tick200=0.0,
        c_reachability_tick400=0.50,
        **_green_d_anchor_kwargs(),
    )
    assert rollup_d == v0_53l_audit.ROLLUP_CORPUS_DRIFT_HALT
    assert "v0.44" in phrase_d


# ---------------------------------------------------------------------------
# Test 3 — Arm A_null_V0_25 uses tight_gradient_layout, default body_config (None),
# AND n_ticks=200 with explicit geometry asserts.
# ---------------------------------------------------------------------------


def test_arm_a_null_v025_uses_tight_gradient_layout_default_body_config_and_n_ticks_200_with_explicit_geometry_asserts():  # noqa: E501
    layout = v0_53l_audit._layout_for_arm(v0_53l_audit.ARM_A_NULL_V025)
    assert layout.safe_x_min == 0
    assert layout.safe_x_max == 2
    assert layout.hazard_x_min == 3
    assert layout.hazard_x_max == 4
    assert layout.food_x_min == 5
    assert layout.food_x_max == 8
    assert layout.resolved_spawn_x == 1
    assert layout.height == 6
    assert layout.width == 9
    assert v0_53l_audit.LAYOUT_NAME_BY_ARM[v0_53l_audit.ARM_A_NULL_V025] == "tight_gradient"
    assert v0_53l_audit._body_config_for_arm(v0_53l_audit.ARM_A_NULL_V025) is None
    assert (
        v0_53l_audit.BODY_BASE_METABOLIC_COST_BY_ARM[v0_53l_audit.ARM_A_NULL_V025]
        == v0_53l_audit.V0_25_BODY_BASE_METABOLIC_COST
        == 0.25
    )
    assert v0_53l_audit.N_TICKS_BY_ARM[v0_53l_audit.ARM_A_NULL_V025] == 200
    assert (
        v0_53l_audit.WINDOWS_BY_ARM[v0_53l_audit.ARM_A_NULL_V025]
        == v0_53l_audit.WINDOWS_AB
        == (50, 100, 200)
    )
    assert (
        v0_53l_audit.BODY_EFFECTIVE_SENSOR_RADIUS_OVERRIDE_BY_ARM[v0_53l_audit.ARM_A_NULL_V025]
        is None
    )


# ---------------------------------------------------------------------------
# Test 4 — Arm B_widened_V0_25 uses widened_gradient_layout, default body_config
# (None), AND n_ticks=200 with explicit geometry asserts.
# ---------------------------------------------------------------------------


def test_arm_b_widened_v025_uses_widened_gradient_layout_default_body_config_and_n_ticks_200_with_explicit_geometry_asserts():  # noqa: E501
    layout = v0_53l_audit._layout_for_arm(v0_53l_audit.ARM_B_WIDENED_V025)
    assert layout.safe_x_min == 0
    assert layout.safe_x_max == 4
    assert layout.hazard_x_min == 5
    assert layout.hazard_x_max == 7
    assert layout.food_x_min == 10
    assert layout.food_x_max == 14
    assert layout.resolved_spawn_x == 1
    assert layout.height == 6
    assert layout.width == 15
    assert v0_53l_audit.LAYOUT_NAME_BY_ARM[v0_53l_audit.ARM_B_WIDENED_V025] == "widened_gradient"
    assert v0_53l_audit._body_config_for_arm(v0_53l_audit.ARM_B_WIDENED_V025) is None
    assert (
        v0_53l_audit.BODY_BASE_METABOLIC_COST_BY_ARM[v0_53l_audit.ARM_B_WIDENED_V025]
        == v0_53l_audit.V0_25_BODY_BASE_METABOLIC_COST
        == 0.25
    )
    assert v0_53l_audit.N_TICKS_BY_ARM[v0_53l_audit.ARM_B_WIDENED_V025] == 200
    assert (
        v0_53l_audit.WINDOWS_BY_ARM[v0_53l_audit.ARM_B_WIDENED_V025]
        == v0_53l_audit.WINDOWS_AB
        == (50, 100, 200)
    )
    assert (
        v0_53l_audit.BODY_EFFECTIVE_SENSOR_RADIUS_OVERRIDE_BY_ARM[v0_53l_audit.ARM_B_WIDENED_V025]
        is None
    )


# ---------------------------------------------------------------------------
# Test 5 — Arm C uses FOOD_NEAR1 layout, combined body_config (NO model-wide
# override), AND per-founder override on the SINGLE max-sensor lineage only,
# AND n_ticks=400.
# ---------------------------------------------------------------------------


def test_arm_c_widened_food_near1_combined_max_lineage_sr8_N400_uses_food_near1_layout_per_founder_override_on_max_sensor_lineage_only_and_n_ticks_400_with_explicit_geometry_and_per_lineage_perception_asserts(  # noqa: E501, N802, PLR0915
    tmp_path,
):
    arm_c = v0_53l_audit.ARM_C_WIDENED_FOOD_NEAR1_COMBINED_MAX_LINEAGE_SR8_N400

    bc_c = v0_53l_audit._body_config_for_arm(arm_c)
    assert isinstance(bc_c, BodyConfig)
    assert bc_c.starting_energy == 100.0
    assert bc_c.base_metabolic_cost == 0.10
    # v0.53l drops the model-wide body_config override (v0.53k had it set to 8).
    assert bc_c.effective_sensor_radius_override is None

    # All other BodyConfig fields at default.
    bc_default = BodyConfig()
    assert bc_c.max_energy == bc_default.max_energy == 100.0
    assert bc_c.starting_health == bc_default.starting_health == 100.0
    assert bc_c.max_health == bc_default.max_health == 100.0
    assert bc_c.sensor_radius_metabolic_cost == bc_default.sensor_radius_metabolic_cost == 0.05

    # Module-level layout constant exposed and constructed script-local.
    assert isinstance(v0_53l_audit.FOOD_NEAR1_LAYOUT, ChamberLayout)
    fn1 = v0_53l_audit.FOOD_NEAR1_LAYOUT
    assert fn1.food_x_min == 9
    assert fn1.food_x_max == 13
    assert fn1.width == 14
    assert fn1.hazard_x_min == 5
    assert fn1.hazard_x_max == 7
    assert fn1.safe_x_min == 0
    assert fn1.safe_x_max == 4
    assert fn1.resolved_spawn_x == 1
    assert fn1.height == 6

    assert v0_53l_audit.N_TICKS_BY_ARM[arm_c] == 400
    assert v0_53l_audit.BODY_EFFECTIVE_SENSOR_RADIUS_OVERRIDE_BY_ARM[arm_c] is None
    assert v0_53l_audit.ARM_USES_MAX_LINEAGE_OVERRIDE[arm_c] is True

    seed = 41
    cap_c = v0_53l_audit._run_one_arm(
        arm=arm_c, version="v0.42", seed=seed, hazard=0, runs_root=tmp_path
    )

    # C founder body fields at tick-0.
    for rec in cap_c.founder_records:
        assert rec.founder_body_energy_tick0 == 100.0
        assert rec.founder_body_starting_energy_tick0 == 100.0
        assert rec.founder_body_base_metabolic_cost_tick0 == 0.10
        # No model-wide body_config override on C in v0.53l.
        assert rec.founder_body_effective_sensor_radius_override_tick0 is None

    # NEW v0.53l per-founder override asserts: exactly 1 of 5 founders has
    # traits.effective_sensor_radius_override == 8 (the max-sensor lineage).
    overridden = [
        rec
        for rec in cap_c.founder_records
        if rec.founder_traits_effective_sensor_radius_override_tick0 == 8
    ]
    assert len(overridden) == 1
    sensor_radius_by_lineage = {
        rec.lineage_id: rec.founder_sensor_radius for rec in cap_c.founder_records
    }
    expected_max_lid = v0_53l_audit._select_sensor_radius_label(sensor_radius_by_lineage)
    assert overridden[0].lineage_id == expected_max_lid

    # The OTHER 4 founders have it None.
    non_overridden = [
        rec
        for rec in cap_c.founder_records
        if rec.founder_traits_effective_sensor_radius_override_tick0 is None
    ]
    assert len(non_overridden) == 4

    # C layout geometry.
    assert cap_c.food_x_min == 9
    assert cap_c.food_x_max == 13
    assert cap_c.hazard_x_min == 5
    assert cap_c.hazard_x_max == 7
    assert cap_c.safe_x_min == 0
    assert cap_c.safe_x_max == 4
    assert cap_c.spawn_x == 1
    assert cap_c.height == 6
    assert cap_c.world_width == 14
    assert cap_c.layout_name == "widened_food_near1"
    assert cap_c.n_ticks == 400
    assert cap_c.body_effective_sensor_radius_override is None
    # Pre-reg test #5 locks `final_tick_count <= 400` (carries forward v0.53k
    # convention; deterministic early-extinction permitted under horizon cap).
    assert cap_c.final_tick_count <= 400


# ---------------------------------------------------------------------------
# Test 6 — Arm D uses FOOD_NEAR2 layout, combined body_config with NO
# override on body_config OR per founder (the v0.53i/j/k D anchor preserved
# byte-identical), AND n_ticks=400.
# ---------------------------------------------------------------------------


def test_arm_d_widened_food_near2_combined_N400_uses_food_near2_layout_combined_body_config_no_override_and_n_ticks_400_with_explicit_geometry_and_no_perception_override_asserts(  # noqa: E501, N802
    tmp_path,
):
    arm_d = v0_53l_audit.ARM_D_WIDENED_FOOD_NEAR2_COMBINED_N400

    bc_d = v0_53l_audit._body_config_for_arm(arm_d)
    assert isinstance(bc_d, BodyConfig)
    assert bc_d.starting_energy == 100.0
    assert bc_d.base_metabolic_cost == 0.10
    # D matches v0.53i/j/k default — no model-wide body_config override.
    assert bc_d.effective_sensor_radius_override is None

    # Module-level layout constant exposed and constructed script-local.
    assert isinstance(v0_53l_audit.FOOD_NEAR2_LAYOUT, ChamberLayout)
    fn2 = v0_53l_audit.FOOD_NEAR2_LAYOUT
    assert fn2.food_x_min == 8
    assert fn2.food_x_max == 12
    assert fn2.width == 13

    assert v0_53l_audit.N_TICKS_BY_ARM[arm_d] == 400
    assert v0_53l_audit.BODY_EFFECTIVE_SENSOR_RADIUS_OVERRIDE_BY_ARM[arm_d] is None
    assert v0_53l_audit.ARM_USES_MAX_LINEAGE_OVERRIDE[arm_d] is False

    seed = 41
    cap_d = v0_53l_audit._run_one_arm(
        arm=arm_d, version="v0.42", seed=seed, hazard=0, runs_root=tmp_path
    )

    for rec in cap_d.founder_records:
        assert rec.founder_body_energy_tick0 == 100.0
        assert rec.founder_body_starting_energy_tick0 == 100.0
        assert rec.founder_body_base_metabolic_cost_tick0 == 0.10
        # No model-wide body_config override on D in v0.53l (carries forward).
        assert rec.founder_body_effective_sensor_radius_override_tick0 is None
        # v0.53l NEW negative per-founder assert: ALL 5 D founders have
        # traits.effective_sensor_radius_override == None.
        assert rec.founder_traits_effective_sensor_radius_override_tick0 is None

    assert cap_d.food_x_min == 8
    assert cap_d.food_x_max == 12
    assert cap_d.layout_name == "widened_food_near2"
    assert cap_d.n_ticks == 400
    assert cap_d.body_effective_sensor_radius_override is None
    # Pre-reg test #6 locks `final_tick_count <= 400` (deterministic
    # early-extinction permitted under horizon cap).
    assert cap_d.final_tick_count <= 400


# ---------------------------------------------------------------------------
# Test 7 — Cross-arm per-lineage perception contrast: C max-sensor founder has
# Traits.effective_sensor_radius_override == 8, D has NO override anywhere,
# layouts differ by food_x_min (carries forward v0.53j's food_x_min contrast).
# ---------------------------------------------------------------------------


def test_cross_arm_per_lineage_perception_contrast_c_max_sensor_founder_has_override_8_d_has_no_override_layouts_differ_by_food_x_min(  # noqa: E501
    tmp_path,
):
    seed = 41
    cap_c = v0_53l_audit._run_one_arm(
        arm=v0_53l_audit.ARM_C_WIDENED_FOOD_NEAR1_COMBINED_MAX_LINEAGE_SR8_N400,
        version="v0.42",
        seed=seed,
        hazard=0,
        runs_root=tmp_path,
    )
    cap_d = v0_53l_audit._run_one_arm(
        arm=v0_53l_audit.ARM_D_WIDENED_FOOD_NEAR2_COMBINED_N400,
        version="v0.42",
        seed=seed,
        hazard=0,
        runs_root=tmp_path,
    )

    # C: exactly 1 of 5 founders has traits.override == 8 — the max-sensor lineage.
    c_overridden = [
        rec
        for rec in cap_c.founder_records
        if rec.founder_traits_effective_sensor_radius_override_tick0 == 8
    ]
    assert len(c_overridden) == 1
    c_sensor_radius_by_lineage = {
        rec.lineage_id: rec.founder_sensor_radius for rec in cap_c.founder_records
    }
    c_expected_max_lid = v0_53l_audit._select_sensor_radius_label(c_sensor_radius_by_lineage)
    assert c_overridden[0].lineage_id == c_expected_max_lid
    # C model-wide body_config override is None in v0.53l.
    assert cap_c.body_effective_sensor_radius_override is None

    # D: 0 of 5 founders have traits.override == 8.
    d_overridden = [
        rec
        for rec in cap_d.founder_records
        if rec.founder_traits_effective_sensor_radius_override_tick0 == 8
    ]
    assert len(d_overridden) == 0
    for rec in cap_d.founder_records:
        assert rec.founder_traits_effective_sensor_radius_override_tick0 is None
    assert cap_d.body_effective_sensor_radius_override is None

    # Body-config invariants (everything else identical).
    assert cap_c.body_starting_energy == cap_d.body_starting_energy == 100.0
    assert cap_c.body_base_metabolic_cost == cap_d.body_base_metabolic_cost == 0.10
    assert cap_c.n_ticks == cap_d.n_ticks == 400

    # Layout differentiator carries forward from v0.53j (food_x_min shift).
    assert cap_c.food_x_min == 9
    assert cap_d.food_x_min == 8

    # All other layout fields identical between C and D.
    assert cap_c.hazard_x_min == cap_d.hazard_x_min == 5
    assert cap_c.hazard_x_max == cap_d.hazard_x_max == 7
    assert cap_c.safe_x_min == cap_d.safe_x_min == 0
    assert cap_c.safe_x_max == cap_d.safe_x_max == 4
    assert cap_c.spawn_x == cap_d.spawn_x == 1
    assert cap_c.height == cap_d.height == 6


# ---------------------------------------------------------------------------
# Test 8 — Two-part src/ pinning test (IDENTICAL SHAs to v0.53e/f/g/h/i/j).
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

V053L_CHAMBER_DRIVER_PATH: str = "src/hedonism_harness/experiments/fear_hunger_chamber.py"
V053L_MODEL_PATH: str = "src/hedonism_harness/model.py"


def test_no_src_modifications_compared_to_v0_53l_tip():
    """Three-part SHA pinning (v0.53l).

    Part A: science-core five files match v0.52b-tip historical pins
    (unchanged from v0.53e..v0.53k).
    Part B: chamber driver matches ``sha_pins.CHAMBER_DRIVER_SHA``
    (v0.53l-tip; gained ``per_founder_traits_overrides`` parameter).
    Part C (NEW): model.py matches ``sha_pins.MODEL_SHA``
    (v0.53l-tip; adopted always-consume founder-trait sampling invariant).
    """
    repo_root = Path(__file__).parent.parent

    # Part A — science-core, historical.
    for rel_path, expected_hash in V052B_TIP_SHA256.items():
        path = repo_root / rel_path
        actual_hash = hashlib.sha256(path.read_bytes()).hexdigest()
        if actual_hash != expected_hash:
            raise AssertionError(
                "v0.53l is pre-registered to leave the science-core five files "
                "byte-identical to v0.52b-tip; update the pre-reg before changing "
                "src/core or src/experiments/layouts."
            )

    # Part B — chamber driver, current via shared tests/sha_pins.py.
    chamber_path = repo_root / V053L_CHAMBER_DRIVER_PATH
    actual_chamber_hash = hashlib.sha256(chamber_path.read_bytes()).hexdigest()
    if actual_chamber_hash != sha_pins.CHAMBER_DRIVER_SHA:
        raise AssertionError(
            "v0.53l is pre-registered to leave the chamber driver byte-identical "
            "to its v0.53l-tip hash recorded in tests/sha_pins.py; update the "
            "pre-reg before re-touching the chamber driver."
        )

    # Part C — model.py, current via shared tests/sha_pins.py.
    model_path = repo_root / V053L_MODEL_PATH
    actual_model_hash = hashlib.sha256(model_path.read_bytes()).hexdigest()
    if actual_model_hash != sha_pins.MODEL_SHA:
        raise AssertionError(
            "v0.53l is pre-registered to leave model.py byte-identical to its "
            "v0.53l-tip hash recorded in tests/sha_pins.py; update the pre-reg "
            "before re-touching model.py."
        )


# ---------------------------------------------------------------------------
# Test 9 — per_founder_traits_overrides seam validation + stream invariance.
# Consolidates the six required pre-data seam validations (mutual exclusivity,
# length validation, default-preserving, founder targeting, non-target
# founder identity, stream-invariance proxy) into a single test.
# ---------------------------------------------------------------------------


_SEAM_TEST_LAYOUT = v0_53l_audit.FOOD_NEAR1_LAYOUT
_SEAM_TEST_N_TICKS = 5  # Tiny horizon for fast seam fixtures (pre-data only).
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
    """Run a tiny chamber and capture each founder's Traits at setup time."""
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


def test_per_founder_traits_overrides_seam_and_stream_invariance(tmp_path):
    seed = 41
    bc = BodyConfig(starting_energy=100.0, base_metabolic_cost=0.10)
    layout = _SEAM_TEST_LAYOUT
    n_founders = _SEAM_TEST_N_FOUNDERS
    n_ticks = _SEAM_TEST_N_TICKS
    trait_cfg = _SEAM_TEST_TRAIT_CFG

    # (9.a) Mutual exclusivity: both traits_override and
    # per_founder_traits_overrides non-None raises ValueError.
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

    # (9.b) Length validation: len != n_founders raises ValueError.
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

    # (9.c) Default-preserving: per_founder_traits_overrides=None produces
    # a result byte-identical (founder Traits) to omitting the parameter.
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
    # Omit the parameter entirely.
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

    # (9.d) Founder targeting: per_founder_traits_overrides[max_lid] applies
    # only to that founder. Use the reducer's pre-sampling helper for the
    # override list; assert exactly one founder has override == 8, that
    # one is the lineage selected by _select_sensor_radius_label, and the
    # other four have None.
    overrides, max_lid = v0_53l_audit.build_c_arm_per_founder_overrides(
        seed=seed, trait_config=trait_cfg, n_founders=n_founders
    )
    assert max_lid is not None
    founders_with_override = _run_chamber_with_setup_capture(
        seed=seed,
        n_founders=n_founders,
        n_ticks=n_ticks,
        layout=layout,
        body_config=bc,
        trait_config=trait_cfg,
        per_founder_traits_overrides=overrides,
        runs_root=tmp_path / "founder_target",
    )
    targeted = [
        (i, t)
        for i, t in enumerate(founders_with_override)
        if t.effective_sensor_radius_override == 8
    ]
    assert len(targeted) == 1
    assert targeted[0][0] == max_lid
    for i, t in enumerate(founders_with_override):
        if i != max_lid:
            assert t.effective_sensor_radius_override is None
    # Cross-check: the targeted lineage matches the v0.48 selector on the
    # actual chamber-sampled founder Traits.
    sensor_radius_by_lineage = {
        i: int(t.sensor_radius) for i, t in enumerate(founders_with_override)
    }
    assert v0_53l_audit._select_sensor_radius_label(sensor_radius_by_lineage) == max_lid

    # (9.e) Non-target founder identity (the always-consume invariant): with
    # the SAME seed, the four non-overridden founders have byte-identical
    # Traits whether or not the per-founder override is provided. The
    # targeted founder's Traits differ only in the override field.
    for i, (t_default, t_override) in enumerate(
        zip(founders_default, founders_with_override, strict=True)
    ):
        if i == max_lid:
            # The targeted founder: every field except override matches.
            stripped_default = replace(t_default, effective_sensor_radius_override=8)
            assert stripped_default == t_override
        else:
            # Non-target founders: byte-identical between the two runs.
            assert t_default == t_override

    # (9.f) Stream-invariance proxy: the reducer's pre-sampling and the
    # chamber's internal sampling pick the same max lineage. (The full
    # integration-level guarantor is the reducer's halt cascade — priorities
    # 1, 2.a..2.f — which reproduces Tier-1 / Tier-2 / Tier-3 anchors within
    # their locked tolerances on a live corpus run.)
    pre_sampling_streams = make_streams(seed)
    pre_sampled = [
        random_traits(trait_cfg, pre_sampling_streams.mutation) for _ in range(n_founders)
    ]
    pre_sampled_sensor_radius = {i: int(t.sensor_radius) for i, t in enumerate(pre_sampled)}
    pre_sampled_max_lid = v0_53l_audit._select_sensor_radius_label(pre_sampled_sensor_radius)
    chamber_sampled_sensor_radius = {
        i: int(t.sensor_radius) for i, t in enumerate(founders_default)
    }
    chamber_max_lid = v0_53l_audit._select_sensor_radius_label(chamber_sampled_sensor_radius)
    assert pre_sampled_max_lid == chamber_max_lid == max_lid


# ---------------------------------------------------------------------------
# Test 10 — Label A high_sensor_radius_lineage picks correct lineage AND
# matches the lineage targeted by the C-arm per-founder override (the
# intervention-to-label alignment that is v0.53l's central scientific move).
# ---------------------------------------------------------------------------


def test_label_a_high_sensor_radius_lineage_picks_correct_lineage_and_matches_per_founder_override_target(  # noqa: E501
    tmp_path,
):
    # Synthetic-fixture branch: the selector returns the expected argmax /
    # tiebreak lineage.
    sensor_radius_by_lineage = {0: 2, 1: 5, 2: 4, 3: 1, 4: 6}
    label = v0_53l_audit._select_sensor_radius_label(sensor_radius_by_lineage)
    assert label == 4
    sensor_tied = {0: 6, 1: 5, 2: 6, 3: 6, 4: 4}
    label_tied = v0_53l_audit._select_sensor_radius_label(sensor_tied)
    assert label_tied == 0

    # Live-chamber branch: the lineage Label A picks per run == the lineage
    # targeted by the C-arm per-founder override. This is v0.53l's central
    # scientific design: intervention-to-label alignment.
    arm_c = v0_53l_audit.ARM_C_WIDENED_FOOD_NEAR1_COMBINED_MAX_LINEAGE_SR8_N400
    seed = 41
    cap_c = v0_53l_audit._run_one_arm(
        arm=arm_c, version="v0.42", seed=seed, hazard=0, runs_root=tmp_path
    )
    rows_c = v0_53l_audit._aggregate_per_lineage(cap_c)
    label_a_lid = next(
        (r.lineage_id for r in rows_c if r.is_high_sensor_radius_lineage),
        None,
    )
    override_lid = next(
        (
            rec.lineage_id
            for rec in cap_c.founder_records
            if rec.founder_traits_effective_sensor_radius_override_tick0 == 8
        ),
        None,
    )
    assert label_a_lid is not None
    assert override_lid is not None
    assert label_a_lid == override_lid


# ---------------------------------------------------------------------------
# Test 11 — Label B four variants three-tier tiebreak at each window.
# ---------------------------------------------------------------------------


def _build_capture_minimal(arm: str, n_ticks: int) -> object:
    layout = v0_53l_audit._layout_for_arm(arm)
    cap = v0_53l_audit._RunCapture(
        arm=arm,
        layout_name=v0_53l_audit.LAYOUT_NAME_BY_ARM[arm],
        safe_x_min=int(layout.safe_x_min),
        safe_x_max=int(layout.safe_x_max),
        hazard_x_min=int(layout.hazard_x_min),
        hazard_x_max=int(layout.hazard_x_max),
        food_x_min=int(layout.food_x_min),
        food_x_max=int(layout.food_x_max),
        world_width=int(layout.width),
        spawn_x=int(layout.resolved_spawn_x),
        height=int(layout.height),
        body_starting_energy=v0_53l_audit.BODY_STARTING_ENERGY_BY_ARM[arm],
        body_base_metabolic_cost=v0_53l_audit.BODY_BASE_METABOLIC_COST_BY_ARM[arm],
        body_effective_sensor_radius_override=(
            v0_53l_audit.BODY_EFFECTIVE_SENSOR_RADIUS_OVERRIDE_BY_ARM[arm]
        ),
        n_ticks=n_ticks,
        version="v0.42",
        seed=41,
        hazard=0,
    )
    cap.lineage_by_agent = {0: 0}
    cap.birth_tick_by_agent = {0: 0}
    cap.founder_records = [
        v0_53l_audit._FounderRecord(
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


def test_label_b_four_variants_three_tier_tiebreak_at_each_window_with_pre400_c_and_d_only():
    candidates_count_tiebreak = [(0, 0.5, 2), (1, 0.5, 4), (2, 0.4, 5)]
    assert v0_53l_audit._select_fraction_label(candidates_count_tiebreak) == 1

    candidates_min_lid = [(3, 0.5, 4), (1, 0.5, 4), (2, 0.5, 4)]
    assert v0_53l_audit._select_fraction_label(candidates_min_lid) == 1

    candidates_simple = [(0, 0.3, 5), (1, 0.7, 1), (2, 0.5, 3)]
    assert v0_53l_audit._select_fraction_label(candidates_simple) == 1

    assert v0_53l_audit._select_fraction_label([]) is None

    energy_threshold = 5.0
    min_age = 1
    all_lineages = [0, 1, 2]
    snaps = [
        v0_53l_audit._ReadinessSnapshot(agent_id=10, lineage_id=0, energy=10.0, age=2),
        v0_53l_audit._ReadinessSnapshot(agent_id=11, lineage_id=0, energy=4.0, age=2),
        v0_53l_audit._ReadinessSnapshot(agent_id=20, lineage_id=1, energy=10.0, age=2),
        v0_53l_audit._ReadinessSnapshot(agent_id=30, lineage_id=2, energy=10.0, age=2),
        v0_53l_audit._ReadinessSnapshot(agent_id=31, lineage_id=2, energy=10.0, age=2),
    ]
    selected_a, _, _, fr_a = v0_53l_audit._readiness_label_at_tick(
        all_lineages, snaps, energy_threshold, min_age
    )
    assert selected_a == 2
    assert fr_a[1] == 1.0
    assert fr_a[2] == 1.0

    cap_a = _build_capture_minimal(v0_53l_audit.ARM_A_NULL_V025, 200)
    cap_b = _build_capture_minimal(v0_53l_audit.ARM_B_WIDENED_V025, 200)
    cap_c = _build_capture_minimal(
        v0_53l_audit.ARM_C_WIDENED_FOOD_NEAR1_COMBINED_MAX_LINEAGE_SR8_N400, 400
    )
    cap_d = _build_capture_minimal(v0_53l_audit.ARM_D_WIDENED_FOOD_NEAR2_COMBINED_N400, 400)
    rows_a = v0_53l_audit._aggregate_per_lineage(cap_a)
    rows_b = v0_53l_audit._aggregate_per_lineage(cap_b)
    rows_c = v0_53l_audit._aggregate_per_lineage(cap_c)
    rows_d = v0_53l_audit._aggregate_per_lineage(cap_d)
    a_label = rows_a[0].is_high_tick400_readiness_fraction_lineage
    b_label = rows_b[0].is_high_tick400_readiness_fraction_lineage
    c_label = rows_c[0].is_high_tick400_readiness_fraction_lineage
    d_label = rows_d[0].is_high_tick400_readiness_fraction_lineage
    assert isinstance(a_label, float)
    assert math.isnan(a_label)
    assert isinstance(b_label, float)
    assert math.isnan(b_label)
    assert isinstance(c_label, bool)
    assert isinstance(d_label, bool)


# ---------------------------------------------------------------------------
# Test 12 — pre400 window strictly extends pre200/pre100/pre50 on C AND D.
# pre400 must be NaN on A and B.
# ---------------------------------------------------------------------------


def _seed_pre_buckets(capture: object, event_ticks: list[int]) -> None:
    aid = 7
    for tick_now in event_ticks:
        if tick_now <= v0_53l_audit.TICK_50:
            capture.pre50_food_events_by_agent[aid] = (
                capture.pre50_food_events_by_agent.get(aid, 0) + 1
            )
            capture.pre50_food_energy_by_agent[aid] = (
                capture.pre50_food_energy_by_agent.get(aid, 0.0) + 1.0
            )
        if tick_now <= v0_53l_audit.TICK_100:
            capture.pre100_food_events_by_agent[aid] = (
                capture.pre100_food_events_by_agent.get(aid, 0) + 1
            )
            capture.pre100_food_energy_by_agent[aid] = (
                capture.pre100_food_energy_by_agent.get(aid, 0.0) + 1.0
            )
        if tick_now <= v0_53l_audit.TICK_200:
            capture.pre200_food_events_by_agent[aid] = (
                capture.pre200_food_events_by_agent.get(aid, 0) + 1
            )
            capture.pre200_food_energy_by_agent[aid] = (
                capture.pre200_food_energy_by_agent.get(aid, 0.0) + 1.0
            )
        if tick_now <= v0_53l_audit.TICK_400:
            capture.pre400_food_events_by_agent[aid] = (
                capture.pre400_food_events_by_agent.get(aid, 0) + 1
            )
            capture.pre400_food_energy_by_agent[aid] = (
                capture.pre400_food_energy_by_agent.get(aid, 0.0) + 1.0
            )


def _build_capture_for_pre_extends(arm: str) -> object:
    layout = v0_53l_audit._layout_for_arm(arm)
    return v0_53l_audit._RunCapture(
        arm=arm,
        layout_name=v0_53l_audit.LAYOUT_NAME_BY_ARM[arm],
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
            v0_53l_audit.BODY_EFFECTIVE_SENSOR_RADIUS_OVERRIDE_BY_ARM[arm]
        ),
        n_ticks=400,
        version="v0.42",
        seed=41,
        hazard=0,
    )


def test_pre400_window_strictly_extends_pre200_pre100_pre50_windows_on_c_and_d_arms():
    event_ticks = [10, 30, 60, 90, 130, 180, 200, 230, 280, 350, 380, 400]
    aid = 7
    cap_c = _build_capture_for_pre_extends(
        v0_53l_audit.ARM_C_WIDENED_FOOD_NEAR1_COMBINED_MAX_LINEAGE_SR8_N400
    )
    cap_d = _build_capture_for_pre_extends(v0_53l_audit.ARM_D_WIDENED_FOOD_NEAR2_COMBINED_N400)
    _seed_pre_buckets(cap_c, event_ticks)
    _seed_pre_buckets(cap_d, event_ticks)
    for cap in (cap_c, cap_d):
        assert cap.pre50_food_events_by_agent[aid] == 2
        assert cap.pre100_food_events_by_agent[aid] == 4
        assert cap.pre200_food_events_by_agent[aid] == 7
        assert cap.pre400_food_events_by_agent[aid] == 12

    cap_a = _build_capture_minimal(v0_53l_audit.ARM_A_NULL_V025, 200)
    cap_b = _build_capture_minimal(v0_53l_audit.ARM_B_WIDENED_V025, 200)
    rows_a = v0_53l_audit._aggregate_per_lineage(cap_a)
    rows_b = v0_53l_audit._aggregate_per_lineage(cap_b)
    assert math.isnan(rows_a[0].pre400_food_events_count)
    assert math.isnan(rows_a[0].pre400_food_energy_acquired)
    assert math.isnan(rows_a[0].mean_distance_to_nearest_food_cell_tick400)
    assert math.isnan(rows_b[0].pre400_food_events_count)
    assert math.isnan(rows_b[0].pre400_food_energy_acquired)
    assert math.isnan(rows_b[0].mean_distance_to_nearest_food_cell_tick400)


# ---------------------------------------------------------------------------
# Test 13 — Sub-verdict PRESENT requires >= 2/3 firing cells; strict NaN rule.
# ---------------------------------------------------------------------------


def test_subverdict_present_requires_two_thirds_firing_cells_with_nan_treated_as_non_firing_strict():  # noqa: E501
    arm = v0_53l_audit.ARM_C_WIDENED_FOOD_NEAR1_COMBINED_MAX_LINEAGE_SR8_N400
    window = v0_53l_audit.TICK_400

    summaries_a_2firing_1nan = _three_summaries_for_arm_window(
        arm, window, (+0.6, +0.6, float("nan")), v0_53l_audit.LABEL_A_NAME
    )
    summaries_b_clean = _three_summaries_for_arm_window(
        arm, window, (+0.6, +0.6, -0.6), v0_53l_audit.LABEL_B_TICK400_NAME
    )
    assert (
        v0_53l_audit._arm_subverdict_at_window(
            arm, window, summaries_a_2firing_1nan, summaries_b_clean
        )
        == v0_53l_audit.SUBVERDICT_C_FOOD_NEAR1_TICK400_PRESENT
    )

    summaries_a_1firing_2nan = _three_summaries_for_arm_window(
        arm, window, (+0.6, float("nan"), float("nan")), v0_53l_audit.LABEL_A_NAME
    )
    assert (
        v0_53l_audit._arm_subverdict_at_window(
            arm, window, summaries_a_1firing_2nan, summaries_b_clean
        )
        == v0_53l_audit.SUBVERDICT_C_FOOD_NEAR1_TICK400_PARTIAL
    )

    summaries_a_all_nan = _three_summaries_for_arm_window(
        arm, window, (float("nan"), float("nan"), float("nan")), v0_53l_audit.LABEL_A_NAME
    )
    assert (
        v0_53l_audit._arm_subverdict_at_window(arm, window, summaries_a_all_nan, summaries_b_clean)
        == v0_53l_audit.SUBVERDICT_C_FOOD_NEAR1_TICK400_PARTIAL
    )

    summaries_b_all_nan = _three_summaries_for_arm_window(
        arm,
        window,
        (float("nan"), float("nan"), float("nan")),
        v0_53l_audit.LABEL_B_TICK400_NAME,
    )
    assert (
        v0_53l_audit._arm_subverdict_at_window(
            arm, window, summaries_a_all_nan, summaries_b_all_nan
        )
        == v0_53l_audit.SUBVERDICT_C_FOOD_NEAR1_TICK400_NOT_FOUND
    )


# ---------------------------------------------------------------------------
# Test 14 — Priority 3 MAX_LINEAGE_PERCEPTION_OPPOSITE_SIGN_HALT is
# REACHABILITY-GATED on C tick-400. Three branches.
# ---------------------------------------------------------------------------


def test_priority_3_max_lineage_perception_opposite_sign_halt_is_reachability_gated_on_c_tick_400(
    tmp_path,
):
    bridge_clean = _zero_drift_bridge_re_anchor()
    arm_c = v0_53l_audit.ARM_C_WIDENED_FOOD_NEAR1_COMBINED_MAX_LINEAGE_SR8_N400
    window = v0_53l_audit.TICK_400

    summaries_a_wrong = _three_summaries_for_arm_window(
        arm_c, window, (+0.6, +0.6, -0.7), v0_53l_audit.LABEL_A_NAME
    )
    summaries_b_clean_above = _three_summaries_for_arm_window(
        arm_c, window, (+0.6, +0.6, +0.5), v0_53l_audit.LABEL_B_TICK400_NAME
    )
    c_sub_opposite = v0_53l_audit._arm_subverdict_at_window(
        arm_c, window, summaries_a_wrong, summaries_b_clean_above
    )
    assert c_sub_opposite == v0_53l_audit.SUBVERDICT_C_FOOD_NEAR1_TICK400_OPPOSITE

    # Branch A: C reach = 0.30 + C OPPOSITE -> priority 3 fires.
    rollup_a, phrase_a = v0_53l_audit._evaluate_rollup(
        a_null_tick50_subverdict=v0_53l_audit.SUBVERDICT_A_NULL_V025_TICK50_PRESENT,
        c_tick400_subverdict=c_sub_opposite,
        corpus_re_anchor=[],
        bridge_re_anchor=bridge_clean,
        b_widened_v025_reachability_tick200=0.0,
        c_reachability_tick400=0.30,
        **_green_d_anchor_kwargs(),
    )
    assert rollup_a == v0_53l_audit.ROLLUP_MAX_LINEAGE_PERCEPTION_OPPOSITE_SIGN_HALT
    assert "AND C reachability at tick-400 clears the locked 25% threshold" in phrase_a
    assert "The reachability-gated trigger preserves v0.53e's locked sign discipline" in phrase_a

    # Branch B: C reach = 0.20 + C OPPOSITE -> priority 3 SKIPS; priority 5 fires.
    rollup_b, phrase_b = v0_53l_audit._evaluate_rollup(
        a_null_tick50_subverdict=v0_53l_audit.SUBVERDICT_A_NULL_V025_TICK50_PRESENT,
        c_tick400_subverdict=c_sub_opposite,
        corpus_re_anchor=[],
        bridge_re_anchor=bridge_clean,
        b_widened_v025_reachability_tick200=0.0,
        c_reachability_tick400=0.20,
        **_green_d_anchor_kwargs(),
    )
    assert rollup_b != v0_53l_audit.ROLLUP_MAX_LINEAGE_PERCEPTION_OPPOSITE_SIGN_HALT
    _expected_below = (
        v0_53l_audit.ROLLUP_WIDENED_BELOW_REACHABILITY_THRESHOLD_UNDER_MAX_LINEAGE_SENSOR_RADIUS_8
    )
    assert rollup_b == _expected_below
    assert (
        "the per-lineage perception intervention "
        "`per_founder_traits_overrides[max_lid] = "
        "Traits(effective_sensor_radius_override=8)`"
    ) in phrase_b

    wrong_sign_cells = v0_53l_audit._collect_c_tick400_wrong_sign_cells(
        list(summaries_a_wrong) + list(summaries_b_clean_above)
    )
    assert len(wrong_sign_cells) == 1
    wsc = wrong_sign_cells[0]
    assert wsc.arm == arm_c
    assert wsc.label == v0_53l_audit.LABEL_B_TICK400_NAME
    assert wsc.observable == "mean_distance_to_nearest_food_cell_tick400"

    # Branch C: C reach = 0.30 + C PRESENT -> priority 4 fires.
    summaries_a_clean_present = _three_summaries_for_arm_window(
        arm_c, window, (+0.6, +0.6, -0.6), v0_53l_audit.LABEL_A_NAME
    )
    summaries_b_clean_present = _three_summaries_for_arm_window(
        arm_c, window, (+0.6, +0.6, -0.6), v0_53l_audit.LABEL_B_TICK400_NAME
    )
    c_sub_present = v0_53l_audit._arm_subverdict_at_window(
        arm_c, window, summaries_a_clean_present, summaries_b_clean_present
    )
    assert c_sub_present == v0_53l_audit.SUBVERDICT_C_FOOD_NEAR1_TICK400_PRESENT
    rollup_c, _ = v0_53l_audit._evaluate_rollup(
        a_null_tick50_subverdict=v0_53l_audit.SUBVERDICT_A_NULL_V025_TICK50_PRESENT,
        c_tick400_subverdict=c_sub_present,
        corpus_re_anchor=[],
        bridge_re_anchor=bridge_clean,
        b_widened_v025_reachability_tick200=0.0,
        c_reachability_tick400=0.30,
        **_green_d_anchor_kwargs(),
    )
    assert rollup_c == v0_53l_audit.ROLLUP_WIDENED_BRIDGE_RESCUED_BY_MAX_LINEAGE_SENSOR_RADIUS_8

    # Verify audit_summary.csv writes the wrong_sign_cells section under branch B.
    out_dir = tmp_path / "audit_branch_b"
    out_dir.mkdir()
    audit_summary_path = out_dir / "audit_summary.csv"
    arms_for_window = {
        v0_53l_audit.TICK_50: v0_53l_audit.ARMS,
        v0_53l_audit.TICK_100: v0_53l_audit.ARMS,
        v0_53l_audit.TICK_200: v0_53l_audit.ARMS,
        v0_53l_audit.TICK_400: (
            v0_53l_audit.ARM_C_WIDENED_FOOD_NEAR1_COMBINED_MAX_LINEAGE_SR8_N400,
            v0_53l_audit.ARM_D_WIDENED_FOOD_NEAR2_COMBINED_N400,
        ),
    }
    reachability_by_window: dict[int, dict[str, tuple[float, int]]] = {}
    for w, arms_w in arms_for_window.items():
        reachability_by_window[w] = {a: (0.0, 64) for a in arms_w}
    reachability_by_window[v0_53l_audit.TICK_200][v0_53l_audit.ARM_B_WIDENED_V025] = (0.0, 64)
    reachability_by_window[v0_53l_audit.TICK_400][arm_c] = (0.20, 64)
    reachability_by_window[v0_53l_audit.TICK_400][
        v0_53l_audit.ARM_D_WIDENED_FOOD_NEAR2_COMBINED_N400
    ] = (v0_53l_audit.D_TIER3_REACHABILITY_LOCKED, 64)

    summaries_by_window = {
        v0_53l_audit.TICK_50: [],
        v0_53l_audit.TICK_100: [],
        v0_53l_audit.TICK_200: [],
        v0_53l_audit.TICK_400: list(summaries_a_wrong) + list(summaries_b_clean_above),
    }
    d_tier3_anchor_rows = [
        v0_53l_audit.DTier3AnchorRow(
            label=label,
            observable=obs,
            published_signed_d=ref,
            derived_signed_d=ref,
            drift_abs=0.0,
            halts=False,
        )
        for (label, obs), ref in v0_53l_audit.D_TIER3_ANCHOR_PUBLISHED.items()
    ]
    v0_53l_audit._write_audit_summary_csv(
        summaries_by_window,
        [],
        [],
        v0_53l_audit.SUBVERDICT_A_NULL_V025_TICK50_PRESENT,
        {},
        c_sub_opposite,
        v0_53l_audit.SUBVERDICT_D_FOOD_NEAR2_TICK400_PRESENT,
        d_tier3_anchor_rows,
        v0_53l_audit.D_TIER3_REACHABILITY_LOCKED,
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


# ---------------------------------------------------------------------------
# Test 15 — Tier-2 categorical anchor on B_widened_V0_25 at tick-200 AND
# Tier-3 D_food_near2 positive anchor at tick-400 (five branches).
# ---------------------------------------------------------------------------


def test_b_widened_v025_categorical_anchor_at_tick_200_and_d_food_near2_positive_anchor_at_tick_400():  # noqa: E501
    bridge_clean = _zero_drift_bridge_re_anchor()

    rollup_clean, _ = v0_53l_audit._evaluate_rollup(
        a_null_tick50_subverdict=v0_53l_audit.SUBVERDICT_A_NULL_V025_TICK50_PRESENT,
        c_tick400_subverdict=v0_53l_audit.SUBVERDICT_C_FOOD_NEAR1_TICK400_PRESENT,
        corpus_re_anchor=[],
        bridge_re_anchor=bridge_clean,
        b_widened_v025_reachability_tick200=0.0,
        c_reachability_tick400=0.50,
        **_green_d_anchor_kwargs(),
    )
    assert rollup_clean == v0_53l_audit.ROLLUP_WIDENED_BRIDGE_RESCUED_BY_MAX_LINEAGE_SENSOR_RADIUS_8

    one_sixty_fourth = 1.0 / 64.0

    # Branch 2: Tier-2 broken (B reach = 1/64) -> ANCHOR_REPLICATION_HALT.
    rollup_b_drift, phrase_b_drift = v0_53l_audit._evaluate_rollup(
        a_null_tick50_subverdict=v0_53l_audit.SUBVERDICT_A_NULL_V025_TICK50_PRESENT,
        c_tick400_subverdict=v0_53l_audit.SUBVERDICT_C_FOOD_NEAR1_TICK400_PRESENT,
        corpus_re_anchor=[],
        bridge_re_anchor=bridge_clean,
        b_widened_v025_reachability_tick200=one_sixty_fourth,
        c_reachability_tick400=0.50,
        **_green_d_anchor_kwargs(),
    )
    assert rollup_b_drift == v0_53l_audit.ROLLUP_ANCHOR_REPLICATION_HALT
    assert "B_widened_V0_25" in phrase_b_drift or "0/64" in phrase_b_drift
    assert "v0.53l" in phrase_b_drift

    # Branch 3: Tier-3 reachability halt (D reach = 34/64).
    d_kwargs_reach_halt = _green_d_anchor_kwargs()
    d_kwargs_reach_halt["d_reachability_tick400"] = 34.0 / 64.0
    rollup_d_reach, phrase_d_reach = v0_53l_audit._evaluate_rollup(
        a_null_tick50_subverdict=v0_53l_audit.SUBVERDICT_A_NULL_V025_TICK50_PRESENT,
        c_tick400_subverdict=v0_53l_audit.SUBVERDICT_C_FOOD_NEAR1_TICK400_PRESENT,
        corpus_re_anchor=[],
        bridge_re_anchor=bridge_clean,
        b_widened_v025_reachability_tick200=0.0,
        c_reachability_tick400=0.50,
        **d_kwargs_reach_halt,
    )
    assert rollup_d_reach == v0_53l_audit.ROLLUP_ANCHOR_REPLICATION_HALT
    assert "35/64" in phrase_d_reach or "FOOD_NEAR2" in phrase_d_reach

    # Branch 4: Tier-3 sub-verdict halt (D sub-verdict = PARTIAL).
    d_kwargs_sub_halt = _green_d_anchor_kwargs()
    d_kwargs_sub_halt["d_tick400_subverdict"] = v0_53l_audit.SUBVERDICT_D_FOOD_NEAR2_TICK400_PARTIAL
    rollup_d_sub, phrase_d_sub = v0_53l_audit._evaluate_rollup(
        a_null_tick50_subverdict=v0_53l_audit.SUBVERDICT_A_NULL_V025_TICK50_PRESENT,
        c_tick400_subverdict=v0_53l_audit.SUBVERDICT_C_FOOD_NEAR1_TICK400_PRESENT,
        corpus_re_anchor=[],
        bridge_re_anchor=bridge_clean,
        b_widened_v025_reachability_tick200=0.0,
        c_reachability_tick400=0.50,
        **d_kwargs_sub_halt,
    )
    assert rollup_d_sub == v0_53l_audit.ROLLUP_ANCHOR_REPLICATION_HALT
    assert "BRIDGE_PRESENT" in phrase_d_sub

    # Branch 5: Tier-3 paired_d drift halt (one cell drifted by 0.005).
    d_kwargs_pd_halt = _green_d_anchor_kwargs()
    drifted_signed_d = dict(v0_53l_audit.D_TIER3_ANCHOR_PUBLISHED)
    drift_key = (v0_53l_audit.LABEL_A_NAME, "pre400_food_events_count")
    drifted_signed_d[drift_key] = drifted_signed_d[drift_key] + 0.005
    d_kwargs_pd_halt["d_tick400_signed_d"] = drifted_signed_d
    rollup_d_pd, phrase_d_pd = v0_53l_audit._evaluate_rollup(
        a_null_tick50_subverdict=v0_53l_audit.SUBVERDICT_A_NULL_V025_TICK50_PRESENT,
        c_tick400_subverdict=v0_53l_audit.SUBVERDICT_C_FOOD_NEAR1_TICK400_PRESENT,
        corpus_re_anchor=[],
        bridge_re_anchor=bridge_clean,
        b_widened_v025_reachability_tick200=0.0,
        c_reachability_tick400=0.50,
        **d_kwargs_pd_halt,
    )
    assert rollup_d_pd == v0_53l_audit.ROLLUP_ANCHOR_REPLICATION_HALT
    assert "1e-3" in phrase_d_pd or "paired_d" in phrase_d_pd


# ---------------------------------------------------------------------------
# Test 16 — Rollup locked phrases fire verbatim AND priority cascade +
# partition exhaustiveness. v0.53l locked phrases reference the FULL
# predecessor stack (v0.53c..v0.53k — NINE long) verbatim where the pre-reg
# locks. Partition exhaustiveness over (C tick-400 reach, sub-verdict) is
# verified directly here (this test replaces v0.53k's separate test #15
# reachability-partition test, per the v0.53l pre-reg's locked 16-test list).
# ---------------------------------------------------------------------------


def test_rollup_locked_phrases_fire_verbatim_and_priority_cascade_partition_total():  # noqa: PLR0915
    bridge_clean = _zero_drift_bridge_re_anchor()
    bridge_drift = list(bridge_clean)
    bridge_drift[0] = v0_53l_audit.BridgeReAnchorRow(
        label=bridge_drift[0].label,
        observable=bridge_drift[0].observable,
        published_signed_d=bridge_drift[0].published_signed_d,
        derived_signed_d=bridge_drift[0].published_signed_d + 1.5,
        drift_abs=1.5,
        halts=True,
    )
    corpus_halt = [
        v0_53l_audit.ReAnchorRow(
            arm=v0_53l_audit.ARM_A_NULL_V025,
            version="v0.42",
            hazard=8,
            n_runs_contributing=8,
            a_share_h8_derived=0.700,
            a_share_h8_published=0.652,
            drift_abs=0.048,
            halts=True,
        )
    ]

    # Predecessor stack (NINE long, v0.53c..v0.53k) preserved verbatim in
    # the v0.53l locked phrases — do NOT bulk-rename these to v0.53l.
    nine_predecessor_tags = (
        "WIDENED_BELOW_REACHABILITY_THRESHOLD_AT_TICK_200",
        "WIDENED_BELOW_REACHABILITY_THRESHOLD_UNDER_RELAXED_INFLUX",
        "RELAXED_OPPOSITE_SIGN_HALT",
        "WIDENED_BELOW_REACHABILITY_THRESHOLD_UNDER_BASE_METABOLIC_COST_010",
        "WIDENED_BELOW_REACHABILITY_THRESHOLD_UNDER_COMBINED_SE100_BMC010",
        "WIDENED_BELOW_REACHABILITY_THRESHOLD_AT_TIME_HORIZON_400",
        "WIDENED_BRIDGE_RESCUED_BY_FOOD_NEAR2",
        "WIDENED_BELOW_REACHABILITY_THRESHOLD_UNDER_FOOD_NEAR1",
        "WIDENED_BRIDGE_PARTIALLY_RESCUED_BY_SENSOR_RADIUS_8",
    )

    # Priority 3 MAX_LINEAGE_PERCEPTION_OPPOSITE_SIGN_HALT (reachability-gated).
    _, phrase_p3 = v0_53l_audit._evaluate_rollup(
        a_null_tick50_subverdict=v0_53l_audit.SUBVERDICT_A_NULL_V025_TICK50_PRESENT,
        c_tick400_subverdict=v0_53l_audit.SUBVERDICT_C_FOOD_NEAR1_TICK400_OPPOSITE,
        corpus_re_anchor=[],
        bridge_re_anchor=bridge_clean,
        b_widened_v025_reachability_tick200=0.0,
        c_reachability_tick400=0.50,
        **_green_d_anchor_kwargs(),
    )
    assert "AND C reachability at tick-400 clears the locked 25% threshold" in phrase_p3
    assert "The reachability-gated trigger preserves v0.53e's locked sign discipline" in phrase_p3
    assert (
        "The per-lineage perception intervention "
        "(`per_founder_traits_overrides[max_lid] = "
        "Traits(effective_sensor_radius_override=8)`)"
    ) in phrase_p3

    # Priority 4 RESCUED.
    _, phrase_rescued = v0_53l_audit._evaluate_rollup(
        a_null_tick50_subverdict=v0_53l_audit.SUBVERDICT_A_NULL_V025_TICK50_PRESENT,
        c_tick400_subverdict=v0_53l_audit.SUBVERDICT_C_FOOD_NEAR1_TICK400_PRESENT,
        corpus_re_anchor=[],
        bridge_re_anchor=bridge_clean,
        b_widened_v025_reachability_tick200=0.0,
        c_reachability_tick400=0.50,
        **_green_d_anchor_kwargs(),
    )
    # v0.53l priority 4 substring assertions (verbatim from pre-reg).
    assert (
        "the per-lineage perception intervention "
        "`per_founder_traits_overrides[max_lid] = "
        "Traits(effective_sensor_radius_override=8)`"
    ) in phrase_rescued
    assert (
        "the v0.48 `is_high_sensor_radius_lineage` selector — argmax with "
        "min-lineage-id tiebreak — picking the same lineage Label A indexes"
    ) in phrase_rescued
    assert (
        "metabolic cost UNAFFECTED per the override's information-channel-only contract"
    ) in phrase_rescued
    assert (
        "override propagates to all descendants via `dataclasses.replace`'s preservation"
    ) in phrase_rescued
    assert (
        "**The v0.53k Label A collapse is consistent with model-wide perception "
        "homogenization being the proximate cause of bridge-fingerprint loss, "
        "not sensor-reach itself**"
    ) in phrase_rescued
    assert "This is strong evidence but NOT exclusive causality" in phrase_rescued
    for tag in nine_predecessor_tags:
        assert tag in phrase_rescued

    # Priority 5 BELOW_THRESHOLD.
    _, phrase_below = v0_53l_audit._evaluate_rollup(
        a_null_tick50_subverdict=v0_53l_audit.SUBVERDICT_A_NULL_V025_TICK50_PRESENT,
        c_tick400_subverdict=v0_53l_audit.SUBVERDICT_C_FOOD_NEAR1_TICK400_PRESENT,
        corpus_re_anchor=[],
        bridge_re_anchor=bridge_clean,
        b_widened_v025_reachability_tick200=0.0,
        c_reachability_tick400=0.10,
        **_green_d_anchor_kwargs(),
    )
    assert (
        "the per-lineage perception intervention "
        "`per_founder_traits_overrides[max_lid] = "
        "Traits(effective_sensor_radius_override=8)`"
    ) in phrase_below
    assert (
        "D_widened_food_near2_combined_N400 reproduces v0.53i's `35/64` "
        "positive anchor at tick-400 in-slice"
    ) in phrase_below
    assert "The single-max-lineage perception intervention is **insufficient**" in phrase_below
    assert (
        "v0.53m (or later) candidates shift toward broader lineage coverage "
        "(top-K, threshold-based) or policy / hazard-avoidance / movement probes"
    ) in phrase_below
    for tag in nine_predecessor_tags:
        assert tag in phrase_below

    # Priority 6 PARTIALLY_RESCUED.
    _, phrase_partial = v0_53l_audit._evaluate_rollup(
        a_null_tick50_subverdict=v0_53l_audit.SUBVERDICT_A_NULL_V025_TICK50_PRESENT,
        c_tick400_subverdict=v0_53l_audit.SUBVERDICT_C_FOOD_NEAR1_TICK400_NOT_FOUND,
        corpus_re_anchor=[],
        bridge_re_anchor=bridge_clean,
        b_widened_v025_reachability_tick200=0.0,
        c_reachability_tick400=0.30,
        **_green_d_anchor_kwargs(),
    )
    assert (
        "D_widened_food_near2_combined_N400 reproduces v0.53i's `35/64` "
        "positive anchor at tick-400 in-slice"
    ) in phrase_partial

    # Priority cascade: 1 > 2.a > 2.b > 2.c > 2.d > 2.e > 2.f > 3.
    rollup_1, phrase_1 = v0_53l_audit._evaluate_rollup(
        a_null_tick50_subverdict=v0_53l_audit.SUBVERDICT_A_NULL_V025_TICK50_NOT_FOUND,
        c_tick400_subverdict=v0_53l_audit.SUBVERDICT_C_FOOD_NEAR1_TICK400_OPPOSITE,
        corpus_re_anchor=corpus_halt,
        bridge_re_anchor=bridge_drift,
        b_widened_v025_reachability_tick200=1.0 / 64.0,
        c_reachability_tick400=0.50,
        **_green_d_anchor_kwargs(),
    )
    assert rollup_1 == v0_53l_audit.ROLLUP_CORPUS_DRIFT_HALT
    assert "v0.42" in phrase_1

    rollup_2a, _ = v0_53l_audit._evaluate_rollup(
        a_null_tick50_subverdict=v0_53l_audit.SUBVERDICT_A_NULL_V025_TICK50_PRESENT,
        c_tick400_subverdict=v0_53l_audit.SUBVERDICT_C_FOOD_NEAR1_TICK400_OPPOSITE,
        corpus_re_anchor=[],
        bridge_re_anchor=bridge_drift,
        b_widened_v025_reachability_tick200=0.0,
        c_reachability_tick400=0.50,
        **_green_d_anchor_kwargs(),
    )
    assert rollup_2a == v0_53l_audit.ROLLUP_ANCHOR_REPLICATION_HALT

    rollup_2b, _ = v0_53l_audit._evaluate_rollup(
        a_null_tick50_subverdict=v0_53l_audit.SUBVERDICT_A_NULL_V025_TICK50_NOT_FOUND,
        c_tick400_subverdict=v0_53l_audit.SUBVERDICT_C_FOOD_NEAR1_TICK400_OPPOSITE,
        corpus_re_anchor=[],
        bridge_re_anchor=bridge_clean,
        b_widened_v025_reachability_tick200=0.0,
        c_reachability_tick400=0.50,
        **_green_d_anchor_kwargs(),
    )
    assert rollup_2b == v0_53l_audit.ROLLUP_ANCHOR_REPLICATION_HALT

    rollup_2c, _ = v0_53l_audit._evaluate_rollup(
        a_null_tick50_subverdict=v0_53l_audit.SUBVERDICT_A_NULL_V025_TICK50_PRESENT,
        c_tick400_subverdict=v0_53l_audit.SUBVERDICT_C_FOOD_NEAR1_TICK400_OPPOSITE,
        corpus_re_anchor=[],
        bridge_re_anchor=bridge_clean,
        b_widened_v025_reachability_tick200=1.0 / 64.0,
        c_reachability_tick400=0.50,
        **_green_d_anchor_kwargs(),
    )
    assert rollup_2c == v0_53l_audit.ROLLUP_ANCHOR_REPLICATION_HALT

    # 2.d: D reach != 35/64 -> ANCHOR_REPLICATION_HALT.
    d_kwargs_2d = _green_d_anchor_kwargs()
    d_kwargs_2d["d_reachability_tick400"] = 34.0 / 64.0
    rollup_2d, _ = v0_53l_audit._evaluate_rollup(
        a_null_tick50_subverdict=v0_53l_audit.SUBVERDICT_A_NULL_V025_TICK50_PRESENT,
        c_tick400_subverdict=v0_53l_audit.SUBVERDICT_C_FOOD_NEAR1_TICK400_OPPOSITE,
        corpus_re_anchor=[],
        bridge_re_anchor=bridge_clean,
        b_widened_v025_reachability_tick200=0.0,
        c_reachability_tick400=0.50,
        **d_kwargs_2d,
    )
    assert rollup_2d == v0_53l_audit.ROLLUP_ANCHOR_REPLICATION_HALT

    # 2.e: D sub-verdict != PRESENT -> ANCHOR_REPLICATION_HALT.
    d_kwargs_2e = _green_d_anchor_kwargs()
    d_kwargs_2e["d_tick400_subverdict"] = v0_53l_audit.SUBVERDICT_D_FOOD_NEAR2_TICK400_PARTIAL
    rollup_2e, _ = v0_53l_audit._evaluate_rollup(
        a_null_tick50_subverdict=v0_53l_audit.SUBVERDICT_A_NULL_V025_TICK50_PRESENT,
        c_tick400_subverdict=v0_53l_audit.SUBVERDICT_C_FOOD_NEAR1_TICK400_OPPOSITE,
        corpus_re_anchor=[],
        bridge_re_anchor=bridge_clean,
        b_widened_v025_reachability_tick200=0.0,
        c_reachability_tick400=0.50,
        **d_kwargs_2e,
    )
    assert rollup_2e == v0_53l_audit.ROLLUP_ANCHOR_REPLICATION_HALT

    # 2.f: D paired_d drift > 1e-3 -> ANCHOR_REPLICATION_HALT.
    d_kwargs_2f = _green_d_anchor_kwargs()
    drifted = dict(v0_53l_audit.D_TIER3_ANCHOR_PUBLISHED)
    drift_key = (v0_53l_audit.LABEL_A_NAME, "pre400_food_events_count")
    drifted[drift_key] = drifted[drift_key] + 0.005
    d_kwargs_2f["d_tick400_signed_d"] = drifted
    rollup_2f, _ = v0_53l_audit._evaluate_rollup(
        a_null_tick50_subverdict=v0_53l_audit.SUBVERDICT_A_NULL_V025_TICK50_PRESENT,
        c_tick400_subverdict=v0_53l_audit.SUBVERDICT_C_FOOD_NEAR1_TICK400_OPPOSITE,
        corpus_re_anchor=[],
        bridge_re_anchor=bridge_clean,
        b_widened_v025_reachability_tick200=0.0,
        c_reachability_tick400=0.50,
        **d_kwargs_2f,
    )
    assert rollup_2f == v0_53l_audit.ROLLUP_ANCHOR_REPLICATION_HALT

    rollup_3, _ = v0_53l_audit._evaluate_rollup(
        a_null_tick50_subverdict=v0_53l_audit.SUBVERDICT_A_NULL_V025_TICK50_PRESENT,
        c_tick400_subverdict=v0_53l_audit.SUBVERDICT_C_FOOD_NEAR1_TICK400_OPPOSITE,
        corpus_re_anchor=[],
        bridge_re_anchor=bridge_clean,
        b_widened_v025_reachability_tick200=0.0,
        c_reachability_tick400=0.50,
        **_green_d_anchor_kwargs(),
    )
    assert rollup_3 == v0_53l_audit.ROLLUP_MAX_LINEAGE_PERCEPTION_OPPOSITE_SIGN_HALT

    # Partition exhaustiveness over (C tick-400 reach, C tick-400 sub-verdict).
    sub_kinds_all = ("PRESENT", "PARTIAL", "NOT_FOUND", "OPPOSITE")
    seen: dict[tuple[str, str], str] = {}
    for c_kind in sub_kinds_all:
        c_sub = _c_tick400_subverdict_for_kind(c_kind)

        rollup_above, _ = v0_53l_audit._evaluate_rollup(
            a_null_tick50_subverdict=v0_53l_audit.SUBVERDICT_A_NULL_V025_TICK50_PRESENT,
            c_tick400_subverdict=c_sub,
            corpus_re_anchor=[],
            bridge_re_anchor=bridge_clean,
            b_widened_v025_reachability_tick200=0.0,
            c_reachability_tick400=0.50,
            **_green_d_anchor_kwargs(),
        )
        seen[(c_kind, "above")] = rollup_above

        rollup_below, _ = v0_53l_audit._evaluate_rollup(
            a_null_tick50_subverdict=v0_53l_audit.SUBVERDICT_A_NULL_V025_TICK50_PRESENT,
            c_tick400_subverdict=c_sub,
            corpus_re_anchor=[],
            bridge_re_anchor=bridge_clean,
            b_widened_v025_reachability_tick200=0.0,
            c_reachability_tick400=0.10,
            **_green_d_anchor_kwargs(),
        )
        seen[(c_kind, "below")] = rollup_below

    rescued = v0_53l_audit.ROLLUP_WIDENED_BRIDGE_RESCUED_BY_MAX_LINEAGE_SENSOR_RADIUS_8
    partial_outcome = (
        v0_53l_audit.ROLLUP_WIDENED_BRIDGE_PARTIALLY_RESCUED_BY_MAX_LINEAGE_SENSOR_RADIUS_8
    )
    below = (
        v0_53l_audit.ROLLUP_WIDENED_BELOW_REACHABILITY_THRESHOLD_UNDER_MAX_LINEAGE_SENSOR_RADIUS_8
    )
    perception_opp = v0_53l_audit.ROLLUP_MAX_LINEAGE_PERCEPTION_OPPOSITE_SIGN_HALT

    assert seen[("PRESENT", "above")] == rescued
    assert seen[("PARTIAL", "above")] == partial_outcome
    assert seen[("NOT_FOUND", "above")] == partial_outcome
    assert seen[("OPPOSITE", "above")] == perception_opp

    for c_kind in sub_kinds_all:
        assert seen[(c_kind, "below")] == below

    assert len(seen) == 8


# Sanity: pytest must be importable.
_ = pytest
