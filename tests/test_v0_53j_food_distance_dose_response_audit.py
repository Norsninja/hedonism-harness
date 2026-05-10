"""v0.53j food-distance dose-response audit (4-arm; n_ticks=400 on C/D) — tests.

16 locked tests. Pre-reg: [[docs/experiments/fear_hunger_v0.53j.md]] §"Test
list (locked, 16 tests)". Tests numbered to match the pre-reg's ordering.
Test #5 verifies the script-local C and D layouts, BOTH BodyConfig knobs, AND
the asymmetric-horizon propagation. Test #14 exercises the Tier-3 D positive
anchor cascade (three independent halt branches: reachability, sub-verdict,
paired_d drift).
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
from hedonism_harness.experiments.fear_hunger_chamber import ChamberLayout
from tests import sha_pins

_SCRIPT_PATH = (
    Path(__file__).parent.parent / "scripts" / "v0_53j_food_distance_dose_response_audit.py"
)
_spec = importlib.util.spec_from_file_location("v0_53j_audit", _SCRIPT_PATH)
assert _spec is not None
assert _spec.loader is not None
v0_53j_audit = importlib.util.module_from_spec(_spec)
sys.modules["v0_53j_audit"] = v0_53j_audit
_spec.loader.exec_module(v0_53j_audit)


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
    fires_expected = (not math.isnan(signed)) and signed >= v0_53j_audit.COHENS_D_THRESHOLD
    fires_wrong = (not math.isnan(signed)) and signed <= -v0_53j_audit.COHENS_D_THRESHOLD
    return v0_53j_audit.ObservableSummary(
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
        v0_53j_audit.TICK_50: v0_53j_audit.PRIMARY_OBSERVABLES_TICK50,
        v0_53j_audit.TICK_100: v0_53j_audit.PRIMARY_OBSERVABLES_TICK100,
        v0_53j_audit.TICK_200: v0_53j_audit.PRIMARY_OBSERVABLES_TICK200,
        v0_53j_audit.TICK_400: v0_53j_audit.PRIMARY_OBSERVABLES_TICK400,
    }
    obs = obs_table[window]
    return [
        _make_summary(arm=arm, observable=obs[i][0], sign=obs[i][1], paired_d=ds[i], label=label)
        for i in range(3)
    ]


def _zero_drift_bridge_re_anchor() -> list[object]:
    return [
        v0_53j_audit.BridgeReAnchorRow(
            label=label,
            observable=obs,
            published_signed_d=ref,
            derived_signed_d=ref,
            drift_abs=0.0,
            halts=False,
        )
        for (label, obs), ref in v0_53j_audit.V048_PUBLISHED_SIGNED_D.items()
    ]


def _green_d_anchor_kwargs() -> dict[str, object]:
    """Return rollup kwargs for D anchor that pass all three Tier-3 sub-conditions."""
    return {
        "d_reachability_tick400": v0_53j_audit.D_TIER3_REACHABILITY_LOCKED,
        "d_tick400_subverdict": v0_53j_audit.SUBVERDICT_D_FOOD_NEAR2_TICK400_PRESENT,
        "d_tick400_signed_d": dict(v0_53j_audit.D_TIER3_ANCHOR_PUBLISHED),
    }


def _c_tick400_subverdict_for_kind(kind: str) -> str:
    table = {
        "PRESENT": v0_53j_audit.SUBVERDICT_C_FOOD_NEAR1_TICK400_PRESENT,
        "PARTIAL": v0_53j_audit.SUBVERDICT_C_FOOD_NEAR1_TICK400_PARTIAL,
        "NOT_FOUND": v0_53j_audit.SUBVERDICT_C_FOOD_NEAR1_TICK400_NOT_FOUND,
        "OPPOSITE": v0_53j_audit.SUBVERDICT_C_FOOD_NEAR1_TICK400_OPPOSITE,
    }
    return table[kind]


# ---------------------------------------------------------------------------
# Test 1 — paired_d formula reproduces hand-computed signed_d on a fixture
# AND Tier-1 reference constants byte-equal v0.48..v0.53i published values
# AND Tier-3 D anchor reference constants byte-equal v0.53i published values.
# ---------------------------------------------------------------------------


def test_paired_d_function_reproduces_hand_computed_signed_d_on_fixture_and_tier1_v048_constants_and_tier3_v053i_constants():  # noqa: E501
    deltas = [1.0, 2.0, 1.5, 0.5, 2.5, 1.8, 0.9, 1.2]
    expected_mean = statistics.mean(deltas)
    expected_sd = statistics.stdev(deltas)
    expected_d = expected_mean / expected_sd
    derived_d = v0_53j_audit._paired_cohens_d(deltas)
    assert abs(derived_d - expected_d) < 1e-9

    pinned_v048 = {
        ("label_a_sensor_radius", "pre50_food_events_count"): +1.066,
        ("label_a_sensor_radius", "pre50_food_energy_acquired"): +1.066,
        ("label_a_sensor_radius", "mean_distance_to_nearest_food_cell_tick50"): +1.916,
        ("label_b_readiness_fraction_tick50", "pre50_food_events_count"): +0.916,
        ("label_b_readiness_fraction_tick50", "pre50_food_energy_acquired"): +0.916,
        ("label_b_readiness_fraction_tick50", "mean_distance_to_nearest_food_cell_tick50"): +1.179,
    }
    assert pinned_v048 == v0_53j_audit.V048_PUBLISHED_SIGNED_D

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
    assert pinned_v053i_d_anchor == v0_53j_audit.D_TIER3_ANCHOR_PUBLISHED
    # All within 1e-3 tolerance of rounded summary values from pre-reg.
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
    assert v0_53j_audit.D_TIER3_REACHABILITY_LOCKED == 35.0 / 64.0
    assert v0_53j_audit.D_TIER3_PAIRED_D_TOLERANCE == 1e-3


# ---------------------------------------------------------------------------
# Test 2 — A_null_V0_25 corpus a_share_h8 re-anchors v0.42 / v0.44 / v0.45.
# ---------------------------------------------------------------------------


def test_a_null_v025_corpus_a_share_h8_re_anchors_v042_v044_v045():
    clean = [
        v0_53j_audit.ReAnchorRow(
            arm=v0_53j_audit.ARM_A_NULL_V025,
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
    rollup, _ = v0_53j_audit._evaluate_rollup(
        a_null_tick50_subverdict=v0_53j_audit.SUBVERDICT_A_NULL_V025_TICK50_PRESENT,
        c_tick400_subverdict=v0_53j_audit.SUBVERDICT_C_FOOD_NEAR1_TICK400_PRESENT,
        corpus_re_anchor=clean,
        bridge_re_anchor=_zero_drift_bridge_re_anchor(),
        b_widened_v025_reachability_tick200=0.0,
        c_reachability_tick400=0.50,
        **_green_d_anchor_kwargs(),
    )
    assert rollup == v0_53j_audit.ROLLUP_WIDENED_BRIDGE_RESCUED_BY_FOOD_NEAR1

    drifted = list(clean)
    drifted[1] = v0_53j_audit.ReAnchorRow(
        arm=v0_53j_audit.ARM_A_NULL_V025,
        version="v0.44",
        hazard=8,
        n_runs_contributing=8,
        a_share_h8_derived=0.880,
        a_share_h8_published=0.878,
        drift_abs=0.002,
        halts=True,
    )
    rollup_d, phrase_d = v0_53j_audit._evaluate_rollup(
        a_null_tick50_subverdict=v0_53j_audit.SUBVERDICT_A_NULL_V025_TICK50_PRESENT,
        c_tick400_subverdict=v0_53j_audit.SUBVERDICT_C_FOOD_NEAR1_TICK400_PRESENT,
        corpus_re_anchor=drifted,
        bridge_re_anchor=_zero_drift_bridge_re_anchor(),
        b_widened_v025_reachability_tick200=0.0,
        c_reachability_tick400=0.50,
        **_green_d_anchor_kwargs(),
    )
    assert rollup_d == v0_53j_audit.ROLLUP_CORPUS_DRIFT_HALT
    assert "v0.44" in phrase_d


# ---------------------------------------------------------------------------
# Test 3 — Arm A_null_V0_25 uses tight_gradient_layout, default body_config (None),
# AND n_ticks=200 with explicit geometry asserts.
# ---------------------------------------------------------------------------


def test_arm_a_null_v025_uses_tight_gradient_layout_default_body_config_and_n_ticks_200_with_explicit_geometry_asserts():  # noqa: E501
    layout = v0_53j_audit._layout_for_arm(v0_53j_audit.ARM_A_NULL_V025)
    assert layout.safe_x_min == 0
    assert layout.safe_x_max == 2
    assert layout.hazard_x_min == 3
    assert layout.hazard_x_max == 4
    assert layout.food_x_min == 5
    assert layout.food_x_max == 8
    assert layout.resolved_spawn_x == 1
    assert layout.height == 6
    assert layout.width == 9
    assert v0_53j_audit.LAYOUT_NAME_BY_ARM[v0_53j_audit.ARM_A_NULL_V025] == "tight_gradient"
    assert v0_53j_audit._body_config_for_arm(v0_53j_audit.ARM_A_NULL_V025) is None
    assert (
        v0_53j_audit.BODY_BASE_METABOLIC_COST_BY_ARM[v0_53j_audit.ARM_A_NULL_V025]
        == v0_53j_audit.V0_25_BODY_BASE_METABOLIC_COST
        == 0.25
    )
    assert v0_53j_audit.N_TICKS_BY_ARM[v0_53j_audit.ARM_A_NULL_V025] == 200
    assert (
        v0_53j_audit.WINDOWS_BY_ARM[v0_53j_audit.ARM_A_NULL_V025]
        == v0_53j_audit.WINDOWS_AB
        == (50, 100, 200)
    )


# ---------------------------------------------------------------------------
# Test 4 — Arm B_widened_V0_25 uses widened_gradient_layout, default body_config
# (None), AND n_ticks=200 with explicit geometry asserts.
# ---------------------------------------------------------------------------


def test_arm_b_widened_v025_uses_widened_gradient_layout_default_body_config_and_n_ticks_200_with_explicit_geometry_asserts():  # noqa: E501
    layout = v0_53j_audit._layout_for_arm(v0_53j_audit.ARM_B_WIDENED_V025)
    assert layout.safe_x_min == 0
    assert layout.safe_x_max == 4
    assert layout.hazard_x_min == 5
    assert layout.hazard_x_max == 7
    assert layout.food_x_min == 10
    assert layout.food_x_max == 14
    assert layout.resolved_spawn_x == 1
    assert layout.height == 6
    assert layout.width == 15
    assert v0_53j_audit.LAYOUT_NAME_BY_ARM[v0_53j_audit.ARM_B_WIDENED_V025] == "widened_gradient"
    assert v0_53j_audit._body_config_for_arm(v0_53j_audit.ARM_B_WIDENED_V025) is None
    assert (
        v0_53j_audit.BODY_BASE_METABOLIC_COST_BY_ARM[v0_53j_audit.ARM_B_WIDENED_V025]
        == v0_53j_audit.V0_25_BODY_BASE_METABOLIC_COST
        == 0.25
    )
    assert v0_53j_audit.N_TICKS_BY_ARM[v0_53j_audit.ARM_B_WIDENED_V025] == 200
    assert (
        v0_53j_audit.WINDOWS_BY_ARM[v0_53j_audit.ARM_B_WIDENED_V025]
        == v0_53j_audit.WINDOWS_AB
        == (50, 100, 200)
    )


# ---------------------------------------------------------------------------
# Test 5 — C and D arms use FOOD_NEAR1 / FOOD_NEAR2 layouts, identical
# combined-budget body_config, AND n_ticks=400 with explicit geometry asserts.
# ---------------------------------------------------------------------------


def test_arms_c_and_d_use_food_near1_and_food_near2_layouts_combined_body_config_and_n_ticks_400_with_explicit_geometry_asserts(  # noqa: E501, PLR0915
    tmp_path,
):
    arm_c = v0_53j_audit.ARM_C_WIDENED_FOOD_NEAR1_COMBINED_N400
    arm_d = v0_53j_audit.ARM_D_WIDENED_FOOD_NEAR2_COMBINED_N400

    bc_c = v0_53j_audit._body_config_for_arm(arm_c)
    bc_d = v0_53j_audit._body_config_for_arm(arm_d)
    assert isinstance(bc_c, BodyConfig)
    assert isinstance(bc_d, BodyConfig)
    for bc in (bc_c, bc_d):
        assert bc.starting_energy == 100.0
        assert bc.base_metabolic_cost == 0.10
    bc_default = BodyConfig()
    assert bc_c.max_energy == bc_default.max_energy == 100.0
    assert bc_c.starting_health == bc_default.starting_health == 100.0
    assert bc_c.max_health == bc_default.max_health == 100.0

    # Module-level layout constants exposed and constructed script-local.
    assert isinstance(v0_53j_audit.FOOD_NEAR1_LAYOUT, ChamberLayout)
    assert isinstance(v0_53j_audit.FOOD_NEAR2_LAYOUT, ChamberLayout)
    fn1 = v0_53j_audit.FOOD_NEAR1_LAYOUT
    fn2 = v0_53j_audit.FOOD_NEAR2_LAYOUT
    assert fn1.food_x_min == 9
    assert fn1.food_x_max == 13
    assert fn1.width == 14
    assert fn2.food_x_min == 8
    assert fn2.food_x_max == 12
    assert fn2.width == 13

    assert v0_53j_audit.N_TICKS_BY_ARM[arm_c] == 400
    assert v0_53j_audit.N_TICKS_BY_ARM[arm_d] == 400

    seed = 41
    cap_c = v0_53j_audit._run_one_arm(
        arm=arm_c, version="v0.42", seed=seed, hazard=0, runs_root=tmp_path
    )
    cap_d = v0_53j_audit._run_one_arm(
        arm=arm_d, version="v0.42", seed=seed, hazard=0, runs_root=tmp_path
    )

    # C founder body fields at tick-0.
    for rec in cap_c.founder_records:
        assert rec.founder_body_energy_tick0 == 100.0
        assert rec.founder_body_starting_energy_tick0 == 100.0
        assert rec.founder_body_base_metabolic_cost_tick0 == 0.10
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
    assert cap_c.final_tick_count <= 400
    if cap_c.final_tick_count > 0:
        assert cap_c.final_tick_count <= 400

    # D founder body fields at tick-0.
    for rec in cap_d.founder_records:
        assert rec.founder_body_energy_tick0 == 100.0
        assert rec.founder_body_starting_energy_tick0 == 100.0
        assert rec.founder_body_base_metabolic_cost_tick0 == 0.10
    # D layout geometry.
    assert cap_d.food_x_min == 8
    assert cap_d.food_x_max == 12
    assert cap_d.hazard_x_min == 5
    assert cap_d.hazard_x_max == 7
    assert cap_d.safe_x_min == 0
    assert cap_d.safe_x_max == 4
    assert cap_d.spawn_x == 1
    assert cap_d.height == 6
    assert cap_d.world_width == 13
    assert cap_d.layout_name == "widened_food_near2"
    assert cap_d.n_ticks == 400
    assert cap_d.final_tick_count <= 400


# ---------------------------------------------------------------------------
# Test 6 — Cross-arm layout dose contrast: B/C/D food_x_min shift and
# preserved invariants.
# ---------------------------------------------------------------------------


def test_cross_arm_layout_dose_contrast_b_c_d_food_x_min_shift_and_preserved_invariants(tmp_path):
    seed = 41
    cap_b = v0_53j_audit._run_one_arm(
        arm=v0_53j_audit.ARM_B_WIDENED_V025,
        version="v0.42",
        seed=seed,
        hazard=0,
        runs_root=tmp_path,
    )
    cap_c = v0_53j_audit._run_one_arm(
        arm=v0_53j_audit.ARM_C_WIDENED_FOOD_NEAR1_COMBINED_N400,
        version="v0.42",
        seed=seed,
        hazard=0,
        runs_root=tmp_path,
    )
    cap_d = v0_53j_audit._run_one_arm(
        arm=v0_53j_audit.ARM_D_WIDENED_FOOD_NEAR2_COMBINED_N400,
        version="v0.42",
        seed=seed,
        hazard=0,
        runs_root=tmp_path,
    )

    # Positive intervention (B -> D): 2-column shift.
    assert cap_b.food_x_min == 10
    assert cap_d.food_x_min == 8
    # Intermediate dose (B -> C): 1-column shift.
    assert cap_c.food_x_min == 9
    # Dose ordering.
    assert cap_d.food_x_min < cap_c.food_x_min < cap_b.food_x_min

    # Preserved invariants across B, C, D.
    assert cap_b.hazard_x_min == cap_c.hazard_x_min == cap_d.hazard_x_min == 5
    assert cap_b.hazard_x_max == cap_c.hazard_x_max == cap_d.hazard_x_max == 7
    assert cap_b.safe_x_min == cap_c.safe_x_min == cap_d.safe_x_min == 0
    assert cap_b.safe_x_max == cap_c.safe_x_max == cap_d.safe_x_max == 4
    assert cap_b.spawn_x == cap_c.spawn_x == cap_d.spawn_x == 1
    assert cap_b.height == cap_c.height == cap_d.height == 6
    # Food width = 5 columns on all three.
    assert (cap_b.food_x_max - cap_b.food_x_min + 1) == 5
    assert (cap_c.food_x_max - cap_c.food_x_min + 1) == 5
    assert (cap_d.food_x_max - cap_d.food_x_min + 1) == 5

    # Secondary invariants (consequences of food band shift).
    assert cap_b.world_width == 15
    assert cap_c.world_width == 14
    assert cap_d.world_width == 13

    # C and D body_config matches v0.53i C body_config.
    assert cap_c.body_starting_energy == cap_d.body_starting_energy == 100.0
    assert cap_c.body_base_metabolic_cost == cap_d.body_base_metabolic_cost == 0.10


# ---------------------------------------------------------------------------
# Test 7 — Founder traits byte-identical across arms for same seed.
# ---------------------------------------------------------------------------


def test_founder_traits_byte_identical_across_arms_for_same_seed(tmp_path):
    seed = 41
    arm_to_records: dict[str, list[tuple]] = {}
    for arm in v0_53j_audit.ARMS:
        cap = v0_53j_audit._run_one_arm(
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
    arms = list(v0_53j_audit.ARMS)
    for arm in arms[1:]:
        assert arm_to_records[arm] == arm_to_records[arms[0]], (
            f"Founder traits diverged between {arms[0]} and {arm}; layout / "
            f"body_config / n_ticks swap must not perturb mutation streams."
        )


# ---------------------------------------------------------------------------
# Test 8 — Two-part src/ pinning test (IDENTICAL SHAs to v0.53e/f/g/h/i).
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
# v0.53l: chamber-driver SHA pin migrated to shared tests/sha_pins.py module.
# Bookkeeping only — v0.53j's verdict / anchor / locked phrases are not changed.
V053E_CHAMBER_DRIVER_SHA256: str = sha_pins.CHAMBER_DRIVER_SHA


def test_no_src_modifications_compared_to_v0_53e_tip():
    repo_root = Path(__file__).parent.parent
    for rel_path, expected_hash in V052B_TIP_SHA256.items():
        path = repo_root / rel_path
        actual_hash = hashlib.sha256(path.read_bytes()).hexdigest()
        if actual_hash != expected_hash:
            raise AssertionError(
                "v0.53j is pre-registered to leave the science-core five files "
                "byte-identical to v0.52b-tip; update the pre-reg before changing "
                "src/core or src/experiments/layouts."
            )

    chamber_path = repo_root / V053E_CHAMBER_DRIVER_PATH
    actual_chamber_hash = hashlib.sha256(chamber_path.read_bytes()).hexdigest()
    if actual_chamber_hash != V053E_CHAMBER_DRIVER_SHA256:
        raise AssertionError(
            "v0.53j is pre-registered to leave the chamber driver byte-identical "
            "to its v0.53e-tip hash; update the pre-reg before re-touching the "
            "chamber driver."
        )


# ---------------------------------------------------------------------------
# Test 9 — Label A high_sensor_radius_lineage picks correct lineage.
# ---------------------------------------------------------------------------


def test_label_a_high_sensor_radius_lineage_picks_correct_lineage():
    sensor_radius_by_lineage = {0: 2, 1: 5, 2: 4, 3: 1, 4: 6}
    label = v0_53j_audit._select_sensor_radius_label(sensor_radius_by_lineage)
    assert label == 4

    sensor_tied = {0: 6, 1: 5, 2: 6, 3: 6, 4: 4}
    label_tied = v0_53j_audit._select_sensor_radius_label(sensor_tied)
    assert label_tied == 0


# ---------------------------------------------------------------------------
# Test 10 — Label B four variants three-tier tiebreak at each window. The
# tick-50/100/200 variants are computed on all arms; the tick-400 variant is
# computed on C and D and NaN-broadcast on A/B.
# ---------------------------------------------------------------------------


def _build_capture_minimal(arm: str, n_ticks: int) -> object:
    layout = v0_53j_audit._layout_for_arm(arm)
    cap = v0_53j_audit._RunCapture(
        arm=arm,
        layout_name=v0_53j_audit.LAYOUT_NAME_BY_ARM[arm],
        safe_x_min=int(layout.safe_x_min),
        safe_x_max=int(layout.safe_x_max),
        hazard_x_min=int(layout.hazard_x_min),
        hazard_x_max=int(layout.hazard_x_max),
        food_x_min=int(layout.food_x_min),
        food_x_max=int(layout.food_x_max),
        world_width=int(layout.width),
        spawn_x=int(layout.resolved_spawn_x),
        height=int(layout.height),
        body_starting_energy=v0_53j_audit.BODY_STARTING_ENERGY_BY_ARM[arm],
        body_base_metabolic_cost=v0_53j_audit.BODY_BASE_METABOLIC_COST_BY_ARM[arm],
        n_ticks=n_ticks,
        version="v0.42",
        seed=41,
        hazard=0,
    )
    cap.lineage_by_agent = {0: 0}
    cap.birth_tick_by_agent = {0: 0}
    cap.founder_records = [
        v0_53j_audit._FounderRecord(
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


def test_label_b_four_variants_three_tier_tiebreak_at_each_window_with_pre400_c_and_d_only():
    candidates_count_tiebreak = [(0, 0.5, 2), (1, 0.5, 4), (2, 0.4, 5)]
    assert v0_53j_audit._select_fraction_label(candidates_count_tiebreak) == 1

    candidates_min_lid = [(3, 0.5, 4), (1, 0.5, 4), (2, 0.5, 4)]
    assert v0_53j_audit._select_fraction_label(candidates_min_lid) == 1

    candidates_simple = [(0, 0.3, 5), (1, 0.7, 1), (2, 0.5, 3)]
    assert v0_53j_audit._select_fraction_label(candidates_simple) == 1

    assert v0_53j_audit._select_fraction_label([]) is None

    energy_threshold = 5.0
    min_age = 1
    all_lineages = [0, 1, 2]
    snaps = [
        v0_53j_audit._ReadinessSnapshot(agent_id=10, lineage_id=0, energy=10.0, age=2),
        v0_53j_audit._ReadinessSnapshot(agent_id=11, lineage_id=0, energy=4.0, age=2),
        v0_53j_audit._ReadinessSnapshot(agent_id=20, lineage_id=1, energy=10.0, age=2),
        v0_53j_audit._ReadinessSnapshot(agent_id=30, lineage_id=2, energy=10.0, age=2),
        v0_53j_audit._ReadinessSnapshot(agent_id=31, lineage_id=2, energy=10.0, age=2),
    ]
    selected_a, _, _, fr_a = v0_53j_audit._readiness_label_at_tick(
        all_lineages, snaps, energy_threshold, min_age
    )
    assert selected_a == 2
    assert fr_a[1] == 1.0
    assert fr_a[2] == 1.0

    # tick-400 label: computed on C and D; NaN-broadcast on A and B.
    cap_a = _build_capture_minimal(v0_53j_audit.ARM_A_NULL_V025, 200)
    cap_b = _build_capture_minimal(v0_53j_audit.ARM_B_WIDENED_V025, 200)
    cap_c = _build_capture_minimal(v0_53j_audit.ARM_C_WIDENED_FOOD_NEAR1_COMBINED_N400, 400)
    cap_d = _build_capture_minimal(v0_53j_audit.ARM_D_WIDENED_FOOD_NEAR2_COMBINED_N400, 400)
    rows_a = v0_53j_audit._aggregate_per_lineage(cap_a)
    rows_b = v0_53j_audit._aggregate_per_lineage(cap_b)
    rows_c = v0_53j_audit._aggregate_per_lineage(cap_c)
    rows_d = v0_53j_audit._aggregate_per_lineage(cap_d)
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
# Test 11 — pre400 window strictly extends pre200/pre100/pre50 on C AND D arms.
# pre400 must be NaN on A and B.
# ---------------------------------------------------------------------------


def _seed_pre_buckets(capture: object, event_ticks: list[int]) -> None:
    aid = 7
    for tick_now in event_ticks:
        if tick_now <= v0_53j_audit.TICK_50:
            capture.pre50_food_events_by_agent[aid] = (
                capture.pre50_food_events_by_agent.get(aid, 0) + 1
            )
            capture.pre50_food_energy_by_agent[aid] = (
                capture.pre50_food_energy_by_agent.get(aid, 0.0) + 1.0
            )
        if tick_now <= v0_53j_audit.TICK_100:
            capture.pre100_food_events_by_agent[aid] = (
                capture.pre100_food_events_by_agent.get(aid, 0) + 1
            )
            capture.pre100_food_energy_by_agent[aid] = (
                capture.pre100_food_energy_by_agent.get(aid, 0.0) + 1.0
            )
        if tick_now <= v0_53j_audit.TICK_200:
            capture.pre200_food_events_by_agent[aid] = (
                capture.pre200_food_events_by_agent.get(aid, 0) + 1
            )
            capture.pre200_food_energy_by_agent[aid] = (
                capture.pre200_food_energy_by_agent.get(aid, 0.0) + 1.0
            )
        if tick_now <= v0_53j_audit.TICK_400:
            capture.pre400_food_events_by_agent[aid] = (
                capture.pre400_food_events_by_agent.get(aid, 0) + 1
            )
            capture.pre400_food_energy_by_agent[aid] = (
                capture.pre400_food_energy_by_agent.get(aid, 0.0) + 1.0
            )


def _build_capture_for_pre_extends(arm: str) -> object:
    layout = v0_53j_audit._layout_for_arm(arm)
    return v0_53j_audit._RunCapture(
        arm=arm,
        layout_name=v0_53j_audit.LAYOUT_NAME_BY_ARM[arm],
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
        n_ticks=400,
        version="v0.42",
        seed=41,
        hazard=0,
    )


def test_pre400_window_strictly_extends_pre200_pre100_pre50_windows_on_c_and_d_arms():
    event_ticks = [10, 30, 60, 90, 130, 180, 200, 230, 280, 350, 380, 400]
    aid = 7
    cap_c = _build_capture_for_pre_extends(v0_53j_audit.ARM_C_WIDENED_FOOD_NEAR1_COMBINED_N400)
    cap_d = _build_capture_for_pre_extends(v0_53j_audit.ARM_D_WIDENED_FOOD_NEAR2_COMBINED_N400)
    _seed_pre_buckets(cap_c, event_ticks)
    _seed_pre_buckets(cap_d, event_ticks)
    for cap in (cap_c, cap_d):
        assert cap.pre50_food_events_by_agent[aid] == 2
        assert cap.pre100_food_events_by_agent[aid] == 4
        assert cap.pre200_food_events_by_agent[aid] == 7
        assert cap.pre400_food_events_by_agent[aid] == 12

    # Pre400 NaN-broadcast on A/B.
    cap_a = _build_capture_minimal(v0_53j_audit.ARM_A_NULL_V025, 200)
    cap_b = _build_capture_minimal(v0_53j_audit.ARM_B_WIDENED_V025, 200)
    rows_a = v0_53j_audit._aggregate_per_lineage(cap_a)
    rows_b = v0_53j_audit._aggregate_per_lineage(cap_b)
    assert math.isnan(rows_a[0].pre400_food_events_count)
    assert math.isnan(rows_a[0].pre400_food_energy_acquired)
    assert math.isnan(rows_a[0].mean_distance_to_nearest_food_cell_tick400)
    assert math.isnan(rows_b[0].pre400_food_events_count)
    assert math.isnan(rows_b[0].pre400_food_energy_acquired)
    assert math.isnan(rows_b[0].mean_distance_to_nearest_food_cell_tick400)


# ---------------------------------------------------------------------------
# Test 12 — Sub-verdict PRESENT requires >= 2/3 firing cells; strict NaN rule.
# ---------------------------------------------------------------------------


def test_subverdict_present_requires_two_thirds_firing_cells_with_nan_treated_as_non_firing_strict():  # noqa: E501
    arm = v0_53j_audit.ARM_C_WIDENED_FOOD_NEAR1_COMBINED_N400
    window = v0_53j_audit.TICK_400

    summaries_a_2firing_1nan = _three_summaries_for_arm_window(
        arm, window, (+0.6, +0.6, float("nan")), v0_53j_audit.LABEL_A_NAME
    )
    summaries_b_clean = _three_summaries_for_arm_window(
        arm, window, (+0.6, +0.6, -0.6), v0_53j_audit.LABEL_B_TICK400_NAME
    )
    assert (
        v0_53j_audit._arm_subverdict_at_window(
            arm, window, summaries_a_2firing_1nan, summaries_b_clean
        )
        == v0_53j_audit.SUBVERDICT_C_FOOD_NEAR1_TICK400_PRESENT
    )

    summaries_a_1firing_2nan = _three_summaries_for_arm_window(
        arm, window, (+0.6, float("nan"), float("nan")), v0_53j_audit.LABEL_A_NAME
    )
    assert (
        v0_53j_audit._arm_subverdict_at_window(
            arm, window, summaries_a_1firing_2nan, summaries_b_clean
        )
        == v0_53j_audit.SUBVERDICT_C_FOOD_NEAR1_TICK400_PARTIAL
    )

    summaries_a_all_nan = _three_summaries_for_arm_window(
        arm, window, (float("nan"), float("nan"), float("nan")), v0_53j_audit.LABEL_A_NAME
    )
    assert (
        v0_53j_audit._arm_subverdict_at_window(arm, window, summaries_a_all_nan, summaries_b_clean)
        == v0_53j_audit.SUBVERDICT_C_FOOD_NEAR1_TICK400_PARTIAL
    )

    summaries_b_all_nan = _three_summaries_for_arm_window(
        arm,
        window,
        (float("nan"), float("nan"), float("nan")),
        v0_53j_audit.LABEL_B_TICK400_NAME,
    )
    assert (
        v0_53j_audit._arm_subverdict_at_window(
            arm, window, summaries_a_all_nan, summaries_b_all_nan
        )
        == v0_53j_audit.SUBVERDICT_C_FOOD_NEAR1_TICK400_NOT_FOUND
    )


# ---------------------------------------------------------------------------
# Test 13 — Priority 3 GEOMETRY_OPPOSITE_SIGN_HALT is REACHABILITY-GATED on
# C tick-400. Three branches.
# ---------------------------------------------------------------------------


def test_priority_3_geometry_opposite_sign_halt_is_reachability_gated_on_c_tick_400(tmp_path):
    bridge_clean = _zero_drift_bridge_re_anchor()
    arm_c = v0_53j_audit.ARM_C_WIDENED_FOOD_NEAR1_COMBINED_N400
    window = v0_53j_audit.TICK_400

    summaries_a_wrong = _three_summaries_for_arm_window(
        arm_c, window, (+0.6, +0.6, -0.7), v0_53j_audit.LABEL_A_NAME
    )
    summaries_b_clean_above = _three_summaries_for_arm_window(
        arm_c, window, (+0.6, +0.6, +0.5), v0_53j_audit.LABEL_B_TICK400_NAME
    )
    c_sub_opposite = v0_53j_audit._arm_subverdict_at_window(
        arm_c, window, summaries_a_wrong, summaries_b_clean_above
    )
    assert c_sub_opposite == v0_53j_audit.SUBVERDICT_C_FOOD_NEAR1_TICK400_OPPOSITE

    # Branch A: C reach = 0.30 + C OPPOSITE -> priority 3 fires.
    rollup_a, phrase_a = v0_53j_audit._evaluate_rollup(
        a_null_tick50_subverdict=v0_53j_audit.SUBVERDICT_A_NULL_V025_TICK50_PRESENT,
        c_tick400_subverdict=c_sub_opposite,
        corpus_re_anchor=[],
        bridge_re_anchor=bridge_clean,
        b_widened_v025_reachability_tick200=0.0,
        c_reachability_tick400=0.30,
        **_green_d_anchor_kwargs(),
    )
    assert rollup_a == v0_53j_audit.ROLLUP_GEOMETRY_OPPOSITE_SIGN_HALT
    assert "AND C reachability at tick-400 clears the locked 25% threshold" in phrase_a
    assert "The reachability-gated trigger preserves v0.53e's locked sign discipline" in phrase_a

    # Branch B: C reach = 0.20 + C OPPOSITE -> priority 3 SKIPS; falls through.
    rollup_b, phrase_b = v0_53j_audit._evaluate_rollup(
        a_null_tick50_subverdict=v0_53j_audit.SUBVERDICT_A_NULL_V025_TICK50_PRESENT,
        c_tick400_subverdict=c_sub_opposite,
        corpus_re_anchor=[],
        bridge_re_anchor=bridge_clean,
        b_widened_v025_reachability_tick200=0.0,
        c_reachability_tick400=0.20,
        **_green_d_anchor_kwargs(),
    )
    assert rollup_b != v0_53j_audit.ROLLUP_GEOMETRY_OPPOSITE_SIGN_HALT
    assert rollup_b == v0_53j_audit.ROLLUP_WIDENED_BELOW_REACHABILITY_THRESHOLD_UNDER_FOOD_NEAR1
    assert "the post-hazard food distance reduced by ONE column" in phrase_b

    wrong_sign_cells = v0_53j_audit._collect_c_tick400_wrong_sign_cells(
        list(summaries_a_wrong) + list(summaries_b_clean_above)
    )
    assert len(wrong_sign_cells) == 1
    wsc = wrong_sign_cells[0]
    assert wsc.arm == arm_c
    assert wsc.label == v0_53j_audit.LABEL_B_TICK400_NAME
    assert wsc.observable == "mean_distance_to_nearest_food_cell_tick400"

    # Branch C: C reach = 0.30 + C PRESENT -> priority 4 fires.
    summaries_a_clean_present = _three_summaries_for_arm_window(
        arm_c, window, (+0.6, +0.6, -0.6), v0_53j_audit.LABEL_A_NAME
    )
    summaries_b_clean_present = _three_summaries_for_arm_window(
        arm_c, window, (+0.6, +0.6, -0.6), v0_53j_audit.LABEL_B_TICK400_NAME
    )
    c_sub_present = v0_53j_audit._arm_subverdict_at_window(
        arm_c, window, summaries_a_clean_present, summaries_b_clean_present
    )
    assert c_sub_present == v0_53j_audit.SUBVERDICT_C_FOOD_NEAR1_TICK400_PRESENT
    rollup_c, _ = v0_53j_audit._evaluate_rollup(
        a_null_tick50_subverdict=v0_53j_audit.SUBVERDICT_A_NULL_V025_TICK50_PRESENT,
        c_tick400_subverdict=c_sub_present,
        corpus_re_anchor=[],
        bridge_re_anchor=bridge_clean,
        b_widened_v025_reachability_tick200=0.0,
        c_reachability_tick400=0.30,
        **_green_d_anchor_kwargs(),
    )
    assert rollup_c == v0_53j_audit.ROLLUP_WIDENED_BRIDGE_RESCUED_BY_FOOD_NEAR1

    # Verify audit_summary.csv writes the wrong_sign_cells section under branch B.
    out_dir = tmp_path / "audit_branch_b"
    out_dir.mkdir()
    audit_summary_path = out_dir / "audit_summary.csv"
    arms_for_window = {
        v0_53j_audit.TICK_50: v0_53j_audit.ARMS,
        v0_53j_audit.TICK_100: v0_53j_audit.ARMS,
        v0_53j_audit.TICK_200: v0_53j_audit.ARMS,
        v0_53j_audit.TICK_400: (
            v0_53j_audit.ARM_C_WIDENED_FOOD_NEAR1_COMBINED_N400,
            v0_53j_audit.ARM_D_WIDENED_FOOD_NEAR2_COMBINED_N400,
        ),
    }
    reachability_by_window: dict[int, dict[str, tuple[float, int]]] = {}
    for w, arms_w in arms_for_window.items():
        reachability_by_window[w] = {a: (0.0, 64) for a in arms_w}
    reachability_by_window[v0_53j_audit.TICK_200][v0_53j_audit.ARM_B_WIDENED_V025] = (0.0, 64)
    reachability_by_window[v0_53j_audit.TICK_400][arm_c] = (0.20, 64)
    reachability_by_window[v0_53j_audit.TICK_400][
        v0_53j_audit.ARM_D_WIDENED_FOOD_NEAR2_COMBINED_N400
    ] = (v0_53j_audit.D_TIER3_REACHABILITY_LOCKED, 64)

    summaries_by_window = {
        v0_53j_audit.TICK_50: [],
        v0_53j_audit.TICK_100: [],
        v0_53j_audit.TICK_200: [],
        v0_53j_audit.TICK_400: list(summaries_a_wrong) + list(summaries_b_clean_above),
    }
    d_tier3_anchor_rows = [
        v0_53j_audit.DTier3AnchorRow(
            label=label,
            observable=obs,
            published_signed_d=ref,
            derived_signed_d=ref,
            drift_abs=0.0,
            halts=False,
        )
        for (label, obs), ref in v0_53j_audit.D_TIER3_ANCHOR_PUBLISHED.items()
    ]
    v0_53j_audit._write_audit_summary_csv(
        summaries_by_window,
        [],
        [],
        v0_53j_audit.SUBVERDICT_A_NULL_V025_TICK50_PRESENT,
        {},
        c_sub_opposite,
        v0_53j_audit.SUBVERDICT_D_FOOD_NEAR2_TICK400_PRESENT,
        d_tier3_anchor_rows,
        v0_53j_audit.D_TIER3_REACHABILITY_LOCKED,
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
# Test 14 — Tier-2 categorical anchor on B_widened_V0_25 at tick-200 AND
# Tier-3 D_food_near2 positive anchor at tick-400 (three independent halt
# branches: reachability, sub-verdict, paired_d drift).
# ---------------------------------------------------------------------------


def test_b_widened_v025_categorical_anchor_at_tick_200_and_d_food_near2_positive_anchor_at_tick_400():  # noqa: E501
    bridge_clean = _zero_drift_bridge_re_anchor()

    # Branch 1: GREEN baseline -> rollup goes to priority 4.
    rollup_clean, _ = v0_53j_audit._evaluate_rollup(
        a_null_tick50_subverdict=v0_53j_audit.SUBVERDICT_A_NULL_V025_TICK50_PRESENT,
        c_tick400_subverdict=v0_53j_audit.SUBVERDICT_C_FOOD_NEAR1_TICK400_PRESENT,
        corpus_re_anchor=[],
        bridge_re_anchor=bridge_clean,
        b_widened_v025_reachability_tick200=0.0,
        c_reachability_tick400=0.50,
        **_green_d_anchor_kwargs(),
    )
    assert rollup_clean == v0_53j_audit.ROLLUP_WIDENED_BRIDGE_RESCUED_BY_FOOD_NEAR1

    one_sixty_fourth = 1.0 / 64.0

    # Branch 2: Tier-2 broken (B reach = 1/64) -> ANCHOR_REPLICATION_HALT.
    rollup_b_drift, phrase_b_drift = v0_53j_audit._evaluate_rollup(
        a_null_tick50_subverdict=v0_53j_audit.SUBVERDICT_A_NULL_V025_TICK50_PRESENT,
        c_tick400_subverdict=v0_53j_audit.SUBVERDICT_C_FOOD_NEAR1_TICK400_PRESENT,
        corpus_re_anchor=[],
        bridge_re_anchor=bridge_clean,
        b_widened_v025_reachability_tick200=one_sixty_fourth,
        c_reachability_tick400=0.50,
        **_green_d_anchor_kwargs(),
    )
    assert rollup_b_drift == v0_53j_audit.ROLLUP_ANCHOR_REPLICATION_HALT
    assert "B_widened_V0_25" in phrase_b_drift or "0/64" in phrase_b_drift

    # Branch 3: Tier-3 reachability halt (D reach = 34/64).
    d_kwargs_reach_halt = _green_d_anchor_kwargs()
    d_kwargs_reach_halt["d_reachability_tick400"] = 34.0 / 64.0
    rollup_d_reach, phrase_d_reach = v0_53j_audit._evaluate_rollup(
        a_null_tick50_subverdict=v0_53j_audit.SUBVERDICT_A_NULL_V025_TICK50_PRESENT,
        c_tick400_subverdict=v0_53j_audit.SUBVERDICT_C_FOOD_NEAR1_TICK400_PRESENT,
        corpus_re_anchor=[],
        bridge_re_anchor=bridge_clean,
        b_widened_v025_reachability_tick200=0.0,
        c_reachability_tick400=0.50,
        **d_kwargs_reach_halt,
    )
    assert rollup_d_reach == v0_53j_audit.ROLLUP_ANCHOR_REPLICATION_HALT
    assert "35/64" in phrase_d_reach or "FOOD_NEAR2" in phrase_d_reach

    # Branch 4: Tier-3 sub-verdict halt (D sub-verdict = PARTIAL).
    d_kwargs_sub_halt = _green_d_anchor_kwargs()
    d_kwargs_sub_halt["d_tick400_subverdict"] = v0_53j_audit.SUBVERDICT_D_FOOD_NEAR2_TICK400_PARTIAL
    rollup_d_sub, phrase_d_sub = v0_53j_audit._evaluate_rollup(
        a_null_tick50_subverdict=v0_53j_audit.SUBVERDICT_A_NULL_V025_TICK50_PRESENT,
        c_tick400_subverdict=v0_53j_audit.SUBVERDICT_C_FOOD_NEAR1_TICK400_PRESENT,
        corpus_re_anchor=[],
        bridge_re_anchor=bridge_clean,
        b_widened_v025_reachability_tick200=0.0,
        c_reachability_tick400=0.50,
        **d_kwargs_sub_halt,
    )
    assert rollup_d_sub == v0_53j_audit.ROLLUP_ANCHOR_REPLICATION_HALT
    assert "BRIDGE_PRESENT" in phrase_d_sub

    # Branch 5: Tier-3 paired_d drift halt (one cell drifted by 0.005).
    d_kwargs_pd_halt = _green_d_anchor_kwargs()
    drifted_signed_d = dict(v0_53j_audit.D_TIER3_ANCHOR_PUBLISHED)
    drift_key = (v0_53j_audit.LABEL_A_NAME, "pre400_food_events_count")
    drifted_signed_d[drift_key] = drifted_signed_d[drift_key] + 0.005
    d_kwargs_pd_halt["d_tick400_signed_d"] = drifted_signed_d
    rollup_d_pd, phrase_d_pd = v0_53j_audit._evaluate_rollup(
        a_null_tick50_subverdict=v0_53j_audit.SUBVERDICT_A_NULL_V025_TICK50_PRESENT,
        c_tick400_subverdict=v0_53j_audit.SUBVERDICT_C_FOOD_NEAR1_TICK400_PRESENT,
        corpus_re_anchor=[],
        bridge_re_anchor=bridge_clean,
        b_widened_v025_reachability_tick200=0.0,
        c_reachability_tick400=0.50,
        **d_kwargs_pd_halt,
    )
    assert rollup_d_pd == v0_53j_audit.ROLLUP_ANCHOR_REPLICATION_HALT
    assert "1e-3" in phrase_d_pd or "paired_d" in phrase_d_pd


# ---------------------------------------------------------------------------
# Test 15 — C tick-400 reachability threshold partition.
#   reach < 0.25, C in {PRESENT, PARTIAL, NOT_FOUND}    -> priority 5 BELOW
#   reach >= 0.25, C PRESENT                            -> priority 4 RESCUED
#   reach >= 0.25, C in {PARTIAL, NOT_FOUND}            -> priority 6 PARTIAL
# ---------------------------------------------------------------------------


def test_c_tick_400_reachability_threshold_partition():
    bridge_clean = _zero_drift_bridge_re_anchor()

    for c_kind in ("PRESENT", "PARTIAL", "NOT_FOUND"):
        c_sub = _c_tick400_subverdict_for_kind(c_kind)
        rollup, _ = v0_53j_audit._evaluate_rollup(
            a_null_tick50_subverdict=v0_53j_audit.SUBVERDICT_A_NULL_V025_TICK50_PRESENT,
            c_tick400_subverdict=c_sub,
            corpus_re_anchor=[],
            bridge_re_anchor=bridge_clean,
            b_widened_v025_reachability_tick200=0.0,
            c_reachability_tick400=0.20,
            **_green_d_anchor_kwargs(),
        )
        assert rollup == v0_53j_audit.ROLLUP_WIDENED_BELOW_REACHABILITY_THRESHOLD_UNDER_FOOD_NEAR1

    rollup_present, _ = v0_53j_audit._evaluate_rollup(
        a_null_tick50_subverdict=v0_53j_audit.SUBVERDICT_A_NULL_V025_TICK50_PRESENT,
        c_tick400_subverdict=v0_53j_audit.SUBVERDICT_C_FOOD_NEAR1_TICK400_PRESENT,
        corpus_re_anchor=[],
        bridge_re_anchor=bridge_clean,
        b_widened_v025_reachability_tick200=0.0,
        c_reachability_tick400=0.30,
        **_green_d_anchor_kwargs(),
    )
    assert rollup_present == v0_53j_audit.ROLLUP_WIDENED_BRIDGE_RESCUED_BY_FOOD_NEAR1

    for c_kind in ("PARTIAL", "NOT_FOUND"):
        c_sub = _c_tick400_subverdict_for_kind(c_kind)
        rollup, _ = v0_53j_audit._evaluate_rollup(
            a_null_tick50_subverdict=v0_53j_audit.SUBVERDICT_A_NULL_V025_TICK50_PRESENT,
            c_tick400_subverdict=c_sub,
            corpus_re_anchor=[],
            bridge_re_anchor=bridge_clean,
            b_widened_v025_reachability_tick200=0.0,
            c_reachability_tick400=0.30,
            **_green_d_anchor_kwargs(),
        )
        assert rollup == v0_53j_audit.ROLLUP_WIDENED_BRIDGE_PARTIALLY_RESCUED_BY_FOOD_NEAR1


# ---------------------------------------------------------------------------
# Test 16 — Rollup locked phrases fire verbatim AND priority cascade +
# partition exhaustiveness.
# ---------------------------------------------------------------------------


def test_rollup_locked_phrases_fire_verbatim_and_priority_cascade_partition_total():  # noqa: PLR0915
    bridge_clean = _zero_drift_bridge_re_anchor()
    bridge_drift = list(bridge_clean)
    bridge_drift[0] = v0_53j_audit.BridgeReAnchorRow(
        label=bridge_drift[0].label,
        observable=bridge_drift[0].observable,
        published_signed_d=bridge_drift[0].published_signed_d,
        derived_signed_d=bridge_drift[0].published_signed_d + 1.5,
        drift_abs=1.5,
        halts=True,
    )
    corpus_halt = [
        v0_53j_audit.ReAnchorRow(
            arm=v0_53j_audit.ARM_A_NULL_V025,
            version="v0.42",
            hazard=8,
            n_runs_contributing=8,
            a_share_h8_derived=0.700,
            a_share_h8_published=0.652,
            drift_abs=0.048,
            halts=True,
        )
    ]

    # Priority 3 GEOMETRY_OPPOSITE_SIGN_HALT (reachability-gated on tick-400).
    _, phrase_p3 = v0_53j_audit._evaluate_rollup(
        a_null_tick50_subverdict=v0_53j_audit.SUBVERDICT_A_NULL_V025_TICK50_PRESENT,
        c_tick400_subverdict=v0_53j_audit.SUBVERDICT_C_FOOD_NEAR1_TICK400_OPPOSITE,
        corpus_re_anchor=[],
        bridge_re_anchor=bridge_clean,
        b_widened_v025_reachability_tick200=0.0,
        c_reachability_tick400=0.50,
        **_green_d_anchor_kwargs(),
    )
    assert "AND C reachability at tick-400 clears the locked 25% threshold" in phrase_p3
    assert "The reachability-gated trigger preserves v0.53e's locked sign discipline" in phrase_p3

    # Priority 4 RESCUED.
    _, phrase_rescued = v0_53j_audit._evaluate_rollup(
        a_null_tick50_subverdict=v0_53j_audit.SUBVERDICT_A_NULL_V025_TICK50_PRESENT,
        c_tick400_subverdict=v0_53j_audit.SUBVERDICT_C_FOOD_NEAR1_TICK400_PRESENT,
        corpus_re_anchor=[],
        bridge_re_anchor=bridge_clean,
        b_widened_v025_reachability_tick200=0.0,
        c_reachability_tick400=0.50,
        **_green_d_anchor_kwargs(),
    )
    assert "the post-hazard food distance reduced by ONE column" in phrase_rescued
    assert (
        "D_widened_food_near2_combined_N400 reachability reproduces v0.53i's "
        "`35/64` positive anchor at tick-400 (positive lock holds)"
    ) in phrase_rescued
    assert (
        "The tested rescue boundary is at or below 1-column reduction; the "
        "2-column reduction tested by v0.53i is NOT minimal under the tested envelope"
    ) in phrase_rescued
    for tag in (
        "WIDENED_BELOW_REACHABILITY_THRESHOLD_AT_TICK_200",
        "WIDENED_BELOW_REACHABILITY_THRESHOLD_UNDER_RELAXED_INFLUX",
        "RELAXED_OPPOSITE_SIGN_HALT",
        "WIDENED_BELOW_REACHABILITY_THRESHOLD_UNDER_BASE_METABOLIC_COST_010",
        "WIDENED_BELOW_REACHABILITY_THRESHOLD_UNDER_COMBINED_SE100_BMC010",
        "WIDENED_BELOW_REACHABILITY_THRESHOLD_AT_TIME_HORIZON_400",
        "WIDENED_BRIDGE_RESCUED_BY_FOOD_NEAR2",
    ):
        assert tag in phrase_rescued

    # Priority 5 BELOW_THRESHOLD.
    _, phrase_below = v0_53j_audit._evaluate_rollup(
        a_null_tick50_subverdict=v0_53j_audit.SUBVERDICT_A_NULL_V025_TICK50_PRESENT,
        c_tick400_subverdict=v0_53j_audit.SUBVERDICT_C_FOOD_NEAR1_TICK400_PRESENT,
        corpus_re_anchor=[],
        bridge_re_anchor=bridge_clean,
        b_widened_v025_reachability_tick200=0.0,
        c_reachability_tick400=0.10,
        **_green_d_anchor_kwargs(),
    )
    assert "the post-hazard food distance reduced by ONE column" in phrase_below
    assert (
        "D_widened_food_near2_combined_N400 reproduces v0.53i's `35/64` "
        "positive anchor at tick-400 in-slice"
    ) in phrase_below
    assert (
        "The tested rescue boundary lies between the historical "
        "`widened_gradient` baseline (`food_x∈[10,14]`, 2-column corridor) and "
        "FOOD_NEAR2 (`food_x∈[8,12]`, 0-column corridor), with FOOD_NEAR1 "
        "(`food_x∈[9,13]`, 1-column corridor) failing — the 1-column reduction "
        "is INsufficient under the tested envelope"
    ) in phrase_below
    for tag in (
        "WIDENED_BELOW_REACHABILITY_THRESHOLD_AT_TICK_200",
        "WIDENED_BELOW_REACHABILITY_THRESHOLD_UNDER_RELAXED_INFLUX",
        "RELAXED_OPPOSITE_SIGN_HALT",
        "WIDENED_BELOW_REACHABILITY_THRESHOLD_UNDER_BASE_METABOLIC_COST_010",
        "WIDENED_BELOW_REACHABILITY_THRESHOLD_UNDER_COMBINED_SE100_BMC010",
        "WIDENED_BELOW_REACHABILITY_THRESHOLD_AT_TIME_HORIZON_400",
        "WIDENED_BRIDGE_RESCUED_BY_FOOD_NEAR2",
    ):
        assert tag in phrase_below

    # Priority 6 PARTIALLY_RESCUED.
    _, phrase_partial = v0_53j_audit._evaluate_rollup(
        a_null_tick50_subverdict=v0_53j_audit.SUBVERDICT_A_NULL_V025_TICK50_PRESENT,
        c_tick400_subverdict=v0_53j_audit.SUBVERDICT_C_FOOD_NEAR1_TICK400_NOT_FOUND,
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
    rollup_1, phrase_1 = v0_53j_audit._evaluate_rollup(
        a_null_tick50_subverdict=v0_53j_audit.SUBVERDICT_A_NULL_V025_TICK50_NOT_FOUND,
        c_tick400_subverdict=v0_53j_audit.SUBVERDICT_C_FOOD_NEAR1_TICK400_OPPOSITE,
        corpus_re_anchor=corpus_halt,
        bridge_re_anchor=bridge_drift,
        b_widened_v025_reachability_tick200=1.0 / 64.0,
        c_reachability_tick400=0.50,
        **_green_d_anchor_kwargs(),
    )
    assert rollup_1 == v0_53j_audit.ROLLUP_CORPUS_DRIFT_HALT
    assert "v0.42" in phrase_1

    rollup_2a, _ = v0_53j_audit._evaluate_rollup(
        a_null_tick50_subverdict=v0_53j_audit.SUBVERDICT_A_NULL_V025_TICK50_PRESENT,
        c_tick400_subverdict=v0_53j_audit.SUBVERDICT_C_FOOD_NEAR1_TICK400_OPPOSITE,
        corpus_re_anchor=[],
        bridge_re_anchor=bridge_drift,
        b_widened_v025_reachability_tick200=0.0,
        c_reachability_tick400=0.50,
        **_green_d_anchor_kwargs(),
    )
    assert rollup_2a == v0_53j_audit.ROLLUP_ANCHOR_REPLICATION_HALT

    rollup_2b, _ = v0_53j_audit._evaluate_rollup(
        a_null_tick50_subverdict=v0_53j_audit.SUBVERDICT_A_NULL_V025_TICK50_NOT_FOUND,
        c_tick400_subverdict=v0_53j_audit.SUBVERDICT_C_FOOD_NEAR1_TICK400_OPPOSITE,
        corpus_re_anchor=[],
        bridge_re_anchor=bridge_clean,
        b_widened_v025_reachability_tick200=0.0,
        c_reachability_tick400=0.50,
        **_green_d_anchor_kwargs(),
    )
    assert rollup_2b == v0_53j_audit.ROLLUP_ANCHOR_REPLICATION_HALT

    rollup_2c, _ = v0_53j_audit._evaluate_rollup(
        a_null_tick50_subverdict=v0_53j_audit.SUBVERDICT_A_NULL_V025_TICK50_PRESENT,
        c_tick400_subverdict=v0_53j_audit.SUBVERDICT_C_FOOD_NEAR1_TICK400_OPPOSITE,
        corpus_re_anchor=[],
        bridge_re_anchor=bridge_clean,
        b_widened_v025_reachability_tick200=1.0 / 64.0,
        c_reachability_tick400=0.50,
        **_green_d_anchor_kwargs(),
    )
    assert rollup_2c == v0_53j_audit.ROLLUP_ANCHOR_REPLICATION_HALT

    # 2.d: D reach != 35/64 -> ANCHOR_REPLICATION_HALT.
    d_kwargs_2d = _green_d_anchor_kwargs()
    d_kwargs_2d["d_reachability_tick400"] = 34.0 / 64.0
    rollup_2d, _ = v0_53j_audit._evaluate_rollup(
        a_null_tick50_subverdict=v0_53j_audit.SUBVERDICT_A_NULL_V025_TICK50_PRESENT,
        c_tick400_subverdict=v0_53j_audit.SUBVERDICT_C_FOOD_NEAR1_TICK400_OPPOSITE,
        corpus_re_anchor=[],
        bridge_re_anchor=bridge_clean,
        b_widened_v025_reachability_tick200=0.0,
        c_reachability_tick400=0.50,
        **d_kwargs_2d,
    )
    assert rollup_2d == v0_53j_audit.ROLLUP_ANCHOR_REPLICATION_HALT

    # 2.e: D sub-verdict != PRESENT -> ANCHOR_REPLICATION_HALT.
    d_kwargs_2e = _green_d_anchor_kwargs()
    d_kwargs_2e["d_tick400_subverdict"] = v0_53j_audit.SUBVERDICT_D_FOOD_NEAR2_TICK400_PARTIAL
    rollup_2e, _ = v0_53j_audit._evaluate_rollup(
        a_null_tick50_subverdict=v0_53j_audit.SUBVERDICT_A_NULL_V025_TICK50_PRESENT,
        c_tick400_subverdict=v0_53j_audit.SUBVERDICT_C_FOOD_NEAR1_TICK400_OPPOSITE,
        corpus_re_anchor=[],
        bridge_re_anchor=bridge_clean,
        b_widened_v025_reachability_tick200=0.0,
        c_reachability_tick400=0.50,
        **d_kwargs_2e,
    )
    assert rollup_2e == v0_53j_audit.ROLLUP_ANCHOR_REPLICATION_HALT

    # 2.f: D paired_d drift > 1e-3 -> ANCHOR_REPLICATION_HALT.
    d_kwargs_2f = _green_d_anchor_kwargs()
    drifted = dict(v0_53j_audit.D_TIER3_ANCHOR_PUBLISHED)
    drift_key = (v0_53j_audit.LABEL_A_NAME, "pre400_food_events_count")
    drifted[drift_key] = drifted[drift_key] + 0.005
    d_kwargs_2f["d_tick400_signed_d"] = drifted
    rollup_2f, _ = v0_53j_audit._evaluate_rollup(
        a_null_tick50_subverdict=v0_53j_audit.SUBVERDICT_A_NULL_V025_TICK50_PRESENT,
        c_tick400_subverdict=v0_53j_audit.SUBVERDICT_C_FOOD_NEAR1_TICK400_OPPOSITE,
        corpus_re_anchor=[],
        bridge_re_anchor=bridge_clean,
        b_widened_v025_reachability_tick200=0.0,
        c_reachability_tick400=0.50,
        **d_kwargs_2f,
    )
    assert rollup_2f == v0_53j_audit.ROLLUP_ANCHOR_REPLICATION_HALT

    rollup_3, _ = v0_53j_audit._evaluate_rollup(
        a_null_tick50_subverdict=v0_53j_audit.SUBVERDICT_A_NULL_V025_TICK50_PRESENT,
        c_tick400_subverdict=v0_53j_audit.SUBVERDICT_C_FOOD_NEAR1_TICK400_OPPOSITE,
        corpus_re_anchor=[],
        bridge_re_anchor=bridge_clean,
        b_widened_v025_reachability_tick200=0.0,
        c_reachability_tick400=0.50,
        **_green_d_anchor_kwargs(),
    )
    assert rollup_3 == v0_53j_audit.ROLLUP_GEOMETRY_OPPOSITE_SIGN_HALT

    # Partition exhaustiveness over (C tick-400 reach, C tick-400 sub-verdict).
    sub_kinds_all = ("PRESENT", "PARTIAL", "NOT_FOUND", "OPPOSITE")
    seen: dict[tuple[str, str], str] = {}
    for c_kind in sub_kinds_all:
        c_sub = _c_tick400_subverdict_for_kind(c_kind)

        rollup_above, _ = v0_53j_audit._evaluate_rollup(
            a_null_tick50_subverdict=v0_53j_audit.SUBVERDICT_A_NULL_V025_TICK50_PRESENT,
            c_tick400_subverdict=c_sub,
            corpus_re_anchor=[],
            bridge_re_anchor=bridge_clean,
            b_widened_v025_reachability_tick200=0.0,
            c_reachability_tick400=0.50,
            **_green_d_anchor_kwargs(),
        )
        seen[(c_kind, "above")] = rollup_above

        rollup_below, _ = v0_53j_audit._evaluate_rollup(
            a_null_tick50_subverdict=v0_53j_audit.SUBVERDICT_A_NULL_V025_TICK50_PRESENT,
            c_tick400_subverdict=c_sub,
            corpus_re_anchor=[],
            bridge_re_anchor=bridge_clean,
            b_widened_v025_reachability_tick200=0.0,
            c_reachability_tick400=0.10,
            **_green_d_anchor_kwargs(),
        )
        seen[(c_kind, "below")] = rollup_below

    rescued = v0_53j_audit.ROLLUP_WIDENED_BRIDGE_RESCUED_BY_FOOD_NEAR1
    partial_outcome = v0_53j_audit.ROLLUP_WIDENED_BRIDGE_PARTIALLY_RESCUED_BY_FOOD_NEAR1
    below = v0_53j_audit.ROLLUP_WIDENED_BELOW_REACHABILITY_THRESHOLD_UNDER_FOOD_NEAR1
    geometry_opp = v0_53j_audit.ROLLUP_GEOMETRY_OPPOSITE_SIGN_HALT

    assert seen[("PRESENT", "above")] == rescued
    assert seen[("PARTIAL", "above")] == partial_outcome
    assert seen[("NOT_FOUND", "above")] == partial_outcome
    assert seen[("OPPOSITE", "above")] == geometry_opp

    for c_kind in sub_kinds_all:
        assert seen[(c_kind, "below")] == below

    assert len(seen) == 8


# Sanity: pytest must be importable.
_ = pytest
