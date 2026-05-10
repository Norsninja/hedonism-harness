"""v0.53e substrate-axis disambiguation audit (starting-energy=100 tick-200) — tests (16 locked).

Pre-reg: [[docs/experiments/fear_hunger_v0.53e.md]] §"Test list (locked, 16 tests)".
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

from hedonism_harness.core.config import BodyConfig
from tests import sha_pins

_SCRIPT_PATH = (
    Path(__file__).parent.parent / "scripts" / "v0_53e_substrate_axis_starting_energy_audit.py"
)
_spec = importlib.util.spec_from_file_location("v0_53e_audit", _SCRIPT_PATH)
assert _spec is not None
assert _spec.loader is not None
v0_53e_audit = importlib.util.module_from_spec(_spec)
sys.modules["v0_53e_audit"] = v0_53e_audit
_spec.loader.exec_module(v0_53e_audit)


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
    fires_expected = (not math.isnan(signed)) and signed >= v0_53e_audit.COHENS_D_THRESHOLD
    fires_wrong = (not math.isnan(signed)) and signed <= -v0_53e_audit.COHENS_D_THRESHOLD
    return v0_53e_audit.ObservableSummary(
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


def _three_summaries_for_arm_tick200(
    arm: str, ds: tuple[float, float, float], label: str
) -> list[object]:
    obs = v0_53e_audit.PRIMARY_OBSERVABLES_TICK200
    return [
        _make_summary(arm=arm, observable=obs[i][0], sign=obs[i][1], paired_d=ds[i], label=label)
        for i in range(3)
    ]


def _zero_drift_bridge_re_anchor() -> list[object]:
    return [
        v0_53e_audit.BridgeReAnchorRow(
            label=label,
            observable=obs,
            published_signed_d=ref,
            derived_signed_d=ref,
            drift_abs=0.0,
            halts=False,
        )
        for (label, obs), ref in v0_53e_audit.V048_PUBLISHED_SIGNED_D.items()
    ]


def _arm_subverdict_for_tick200(arm: str, kind: str) -> str:
    """Return locked tick-200 sub-verdict constant for (arm, kind)."""
    table = {
        v0_53e_audit.ARM_A_NULL_V025: {
            "PRESENT": v0_53e_audit.SUBVERDICT_A_NULL_V025_TICK200_PRESENT,
            "PARTIAL": v0_53e_audit.SUBVERDICT_A_NULL_V025_TICK200_PARTIAL,
            "NOT_FOUND": v0_53e_audit.SUBVERDICT_A_NULL_V025_TICK200_NOT_FOUND,
            "OPPOSITE": v0_53e_audit.SUBVERDICT_A_NULL_V025_TICK200_OPPOSITE,
        },
        v0_53e_audit.ARM_B_WIDENED_V025: {
            "PRESENT": v0_53e_audit.SUBVERDICT_B_WIDENED_V025_TICK200_PRESENT,
            "PARTIAL": v0_53e_audit.SUBVERDICT_B_WIDENED_V025_TICK200_PARTIAL,
            "NOT_FOUND": v0_53e_audit.SUBVERDICT_B_WIDENED_V025_TICK200_NOT_FOUND,
            "OPPOSITE": v0_53e_audit.SUBVERDICT_B_WIDENED_V025_TICK200_OPPOSITE,
        },
        v0_53e_audit.ARM_C_WIDENED_STARTING_ENERGY_100: {
            "PRESENT": v0_53e_audit.SUBVERDICT_C_STARTING_ENERGY_100_TICK200_PRESENT,
            "PARTIAL": v0_53e_audit.SUBVERDICT_C_STARTING_ENERGY_100_TICK200_PARTIAL,
            "NOT_FOUND": v0_53e_audit.SUBVERDICT_C_STARTING_ENERGY_100_TICK200_NOT_FOUND,
            "OPPOSITE": v0_53e_audit.SUBVERDICT_C_STARTING_ENERGY_100_TICK200_OPPOSITE,
        },
    }
    return table[arm][kind]


def _b_v025_zero_reach() -> float:
    """Return B_widened_V0_25 reachability=0.0 (Tier-2 categorical pass)."""
    return 0.0


# ---------------------------------------------------------------------------
# Test 1 — paired_d formula reproduces hand-computed signed_d on a fixture
# AND Tier-1 reference constants byte-equal v0.48 / v0.53 / v0.53b / v0.53c / v0.53d published.
# ---------------------------------------------------------------------------


def test_paired_d_function_reproduces_hand_computed_signed_d_on_fixture_and_tier1_constants_match_v048_published_values():  # noqa: E501
    # Part A: feed _paired_cohens_d a synthetic 8-run pool and compare
    # against hand-computed mean / ddof=1 stdev.
    deltas = [1.0, 2.0, 1.5, 0.5, 2.5, 1.8, 0.9, 1.2]
    expected_mean = statistics.mean(deltas)
    expected_sd = statistics.stdev(deltas)
    expected_d = expected_mean / expected_sd
    derived_d = v0_53e_audit._paired_cohens_d(deltas)
    assert abs(derived_d - expected_d) < 1e-9

    # Part B: locked Tier-1 reference constants byte-equal pinned
    # v0.48 / v0.53 / v0.53b / v0.53c / v0.53d values.
    pinned_v048 = {
        ("label_a_sensor_radius", "pre50_food_events_count"): +1.066,
        ("label_a_sensor_radius", "pre50_food_energy_acquired"): +1.066,
        ("label_a_sensor_radius", "mean_distance_to_nearest_food_cell_tick50"): +1.916,
        ("label_b_readiness_fraction_tick50", "pre50_food_events_count"): +0.916,
        ("label_b_readiness_fraction_tick50", "pre50_food_energy_acquired"): +0.916,
        ("label_b_readiness_fraction_tick50", "mean_distance_to_nearest_food_cell_tick50"): +1.179,
    }
    assert pinned_v048 == v0_53e_audit.V048_PUBLISHED_SIGNED_D


# ---------------------------------------------------------------------------
# Test 2 — A_null_V0_25 corpus a_share_h8 re-anchors v0.42 / v0.44 / v0.45.
# ---------------------------------------------------------------------------


def test_a_null_v025_corpus_a_share_h8_re_anchors_v042_v044_v045():
    clean = [
        v0_53e_audit.ReAnchorRow(
            arm=v0_53e_audit.ARM_A_NULL_V025,
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
    rollup, _ = v0_53e_audit._evaluate_rollup(
        a_null_tick50_subverdict=v0_53e_audit.SUBVERDICT_A_NULL_V025_TICK50_PRESENT,
        a_null_tick200_subverdict=v0_53e_audit.SUBVERDICT_A_NULL_V025_TICK200_PRESENT,
        b_tick200_subverdict=v0_53e_audit.SUBVERDICT_B_WIDENED_V025_TICK200_NOT_FOUND,
        c_tick200_subverdict=v0_53e_audit.SUBVERDICT_C_STARTING_ENERGY_100_TICK200_PRESENT,
        corpus_re_anchor=clean,
        bridge_re_anchor=_zero_drift_bridge_re_anchor(),
        b_widened_v025_reachability_tick200=_b_v025_zero_reach(),
        c_widened_starting_energy_100_reachability_tick200=0.50,
    )
    assert rollup == v0_53e_audit.ROLLUP_WIDENED_BRIDGE_RESCUED_BY_STARTING_ENERGY_100

    # Drift > 1e-3 on v0.44 -> CORPUS_REDERIVE_DRIFT_HALT.
    drifted = list(clean)
    drifted[1] = v0_53e_audit.ReAnchorRow(
        arm=v0_53e_audit.ARM_A_NULL_V025,
        version="v0.44",
        hazard=8,
        n_runs_contributing=8,
        a_share_h8_derived=0.880,
        a_share_h8_published=0.878,
        drift_abs=0.002,
        halts=True,
    )
    rollup_d, phrase_d = v0_53e_audit._evaluate_rollup(
        a_null_tick50_subverdict=v0_53e_audit.SUBVERDICT_A_NULL_V025_TICK50_PRESENT,
        a_null_tick200_subverdict=v0_53e_audit.SUBVERDICT_A_NULL_V025_TICK200_PRESENT,
        b_tick200_subverdict=v0_53e_audit.SUBVERDICT_B_WIDENED_V025_TICK200_NOT_FOUND,
        c_tick200_subverdict=v0_53e_audit.SUBVERDICT_C_STARTING_ENERGY_100_TICK200_PRESENT,
        corpus_re_anchor=drifted,
        bridge_re_anchor=_zero_drift_bridge_re_anchor(),
        b_widened_v025_reachability_tick200=_b_v025_zero_reach(),
        c_widened_starting_energy_100_reachability_tick200=0.50,
    )
    assert rollup_d == v0_53e_audit.ROLLUP_CORPUS_DRIFT_HALT
    assert "v0.44" in phrase_d


# ---------------------------------------------------------------------------
# Test 3 — Arm A_null_V0_25 uses tight_gradient_layout AND default body_config (None).
# ---------------------------------------------------------------------------


def test_arm_a_null_v025_uses_tight_gradient_layout_and_default_body_config():
    layout = v0_53e_audit._layout_for_arm(v0_53e_audit.ARM_A_NULL_V025)
    assert layout.width == 9
    assert layout.height == 6
    assert layout.safe_x_min == 0
    assert layout.safe_x_max == 2
    assert layout.hazard_x_min == 3
    assert layout.hazard_x_max == 4
    assert layout.food_x_min == 5
    assert layout.food_x_max == 8
    assert layout.resolved_spawn_x == 1
    assert v0_53e_audit.LAYOUT_NAME_BY_ARM[v0_53e_audit.ARM_A_NULL_V025] == "tight_gradient"
    # body_config = None on A (default BodyConfig fallback in run_chamber).
    assert v0_53e_audit._body_config_for_arm(v0_53e_audit.ARM_A_NULL_V025) is None
    assert (
        v0_53e_audit.BODY_STARTING_ENERGY_BY_ARM[v0_53e_audit.ARM_A_NULL_V025]
        == v0_53e_audit.V0_25_BODY_STARTING_ENERGY
        == 60.0
    )


# ---------------------------------------------------------------------------
# Test 4 — Arm B_widened_V0_25 uses widened_gradient_layout AND default body_config (None).
# ---------------------------------------------------------------------------


def test_arm_b_widened_v025_uses_widened_gradient_layout_and_default_body_config():
    layout = v0_53e_audit._layout_for_arm(v0_53e_audit.ARM_B_WIDENED_V025)
    assert layout.width == 15
    assert layout.height == 6
    assert layout.safe_x_min == 0
    assert layout.safe_x_max == 4
    assert layout.hazard_x_min == 5
    assert layout.hazard_x_max == 7
    assert layout.food_x_min == 10
    assert layout.food_x_max == 14
    assert layout.resolved_spawn_x == 1
    assert v0_53e_audit.LAYOUT_NAME_BY_ARM[v0_53e_audit.ARM_B_WIDENED_V025] == "widened_gradient"
    # body_config = None on B (default BodyConfig fallback in run_chamber).
    assert v0_53e_audit._body_config_for_arm(v0_53e_audit.ARM_B_WIDENED_V025) is None
    assert (
        v0_53e_audit.BODY_STARTING_ENERGY_BY_ARM[v0_53e_audit.ARM_B_WIDENED_V025]
        == v0_53e_audit.V0_25_BODY_STARTING_ENERGY
        == 60.0
    )


# ---------------------------------------------------------------------------
# Test 5 — Cross-arm contrast verifying the body_config seam differentiates B
# and C founder body energies at tick-0. Read-only via setup_observer snapshot.
# ---------------------------------------------------------------------------


def test_arm_c_widened_starting_energy_100_seam_differentiates_b_and_c_body_energy_at_tick_0(
    tmp_path,
):
    # ---- Pre-reg constants (verify before runtime).
    # C arm body_config: starting_energy=100.0; all other BodyConfig fields default.
    bc_c = v0_53e_audit._body_config_for_arm(v0_53e_audit.ARM_C_WIDENED_STARTING_ENERGY_100)
    assert isinstance(bc_c, BodyConfig)
    assert bc_c.starting_energy == 100.0
    # All other BodyConfig fields preserved at default.
    bc_default = BodyConfig()
    assert bc_c.max_energy == bc_default.max_energy == 100.0
    assert bc_c.starting_health == bc_default.starting_health == 100.0
    assert bc_c.max_health == bc_default.max_health == 100.0
    assert bc_c.base_metabolic_cost == bc_default.base_metabolic_cost == 0.25
    assert bc_c.sensor_radius_metabolic_cost == bc_default.sensor_radius_metabolic_cost == 0.05
    assert (
        bc_c.effective_sensor_radius_override == bc_default.effective_sensor_radius_override is None
    )

    # The starting_energy=100 dose constant is locked.
    assert v0_53e_audit.STARTING_ENERGY_100_DOSE == 100.0

    # No other WorldConfig knob differs from V0_25 baseline on C.
    base_arm = v0_53e_audit._select_a_null_arm("v0.42", 0)
    assert base_arm.ambient_influx_rate == v0_53e_audit.V0_25_AMBIENT_INFLUX_RATE == 1.0
    assert base_arm.energy_pool_initial == v0_53e_audit.V0_25_ENERGY_POOL_INITIAL == 1500.0
    assert base_arm.food_respawn_cooldown == v0_53e_audit.V0_25_FOOD_RESPAWN_COOLDOWN == 50

    # ---- Runtime: same (version, seed, hazard); B founder energy=60.0,
    # C founder energy=100.0; layouts identical (widened_gradient).
    seed = 41
    cap_b = v0_53e_audit._run_one_arm(
        arm=v0_53e_audit.ARM_B_WIDENED_V025,
        version="v0.42",
        seed=seed,
        hazard=0,
        runs_root=tmp_path,
    )
    cap_c = v0_53e_audit._run_one_arm(
        arm=v0_53e_audit.ARM_C_WIDENED_STARTING_ENERGY_100,
        version="v0.42",
        seed=seed,
        hazard=0,
        runs_root=tmp_path,
    )
    # Layouts identical (widened_gradient on both).
    assert cap_b.layout_name == cap_c.layout_name == "widened_gradient"
    # Founder body energy at tick-0: B = 60.0 (V0_25 baseline); C = 100.0 (overridden).
    for rec in cap_b.founder_records:
        assert rec.founder_body_energy_tick0 == 60.0, (
            f"B founder lineage_id={rec.lineage_id} body.energy at tick-0 "
            f"expected 60.0, got {rec.founder_body_energy_tick0}"
        )
    for rec in cap_c.founder_records:
        assert rec.founder_body_energy_tick0 == 100.0, (
            f"C founder lineage_id={rec.lineage_id} body.energy at tick-0 "
            f"expected 100.0, got {rec.founder_body_energy_tick0}"
        )
    assert (
        v0_53e_audit.BODY_STARTING_ENERGY_BY_ARM[v0_53e_audit.ARM_C_WIDENED_STARTING_ENERGY_100]
        == 100.0
    )


# ---------------------------------------------------------------------------
# Test 6 — Founder traits byte-identical across arms for same (version, seed,
# hazard) tuple. Arms differ only in chamber config (layout + body_config), not
# in founder draw.
# ---------------------------------------------------------------------------


def test_founder_traits_byte_identical_across_arms_for_same_seed(tmp_path):
    seed = 41
    arm_to_records: dict[str, list[tuple]] = {}
    for arm in v0_53e_audit.ARMS:
        cap = v0_53e_audit._run_one_arm(
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
    arms = list(v0_53e_audit.ARMS)
    for arm in arms[1:]:
        assert arm_to_records[arm] == arm_to_records[arms[0]], (
            f"Founder traits diverged between {arms[0]} and {arm}; layout / "
            f"body_config swap must not perturb mutation streams."
        )


# ---------------------------------------------------------------------------
# Test 7 — Founder positions byte-identical across arms for same seed.
# All three layouts have spawn_x=1 and height=6 -> identical (x, y) per founder.
# ---------------------------------------------------------------------------


def test_founder_positions_byte_identical_across_arms_for_same_seed():
    """All three layouts have spawn_x=1 and height=6, so spread_y(5, 6) yields
    identical y positions and spawn_x identical x positions across arms.
    body_config variation does not affect founder positions."""
    from hedonism_harness.experiments.fear_hunger_chamber import spread_y

    expected_xs = []
    expected_ys = None
    for arm in v0_53e_audit.ARMS:
        layout = v0_53e_audit._layout_for_arm(arm)
        spawn_x = layout.resolved_spawn_x
        ys = spread_y(v0_53e_audit.N_FOUNDERS, layout.height)
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
# Test 8 — Two-part src/ pinning test:
#   Part A: science-core five files byte-identical to v0.52b-tip.
#   Part B: chamber driver byte-identical to v0.53e-tip post-seam-add.
# ---------------------------------------------------------------------------


# Science-core five files at v0.52b-tip (unchanged across v0.53/53b/53c/53d/53e).
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

# Chamber driver at v0.53e-tip (post-seam-add): the one-time additive
# body_config seam. Future slices that re-touch this file MUST update Part B's
# pinned hash AND its locked failure message together.
V053E_CHAMBER_DRIVER_PATH: str = "src/hedonism_harness/experiments/fear_hunger_chamber.py"
# v0.53l: chamber-driver SHA pin migrated to shared tests/sha_pins.py module
# (chamber driver gained per_founder_traits_overrides parameter and model.py
# adopted always-consume founder-construction invariant). Bookkeeping only —
# v0.53e's verdict / anchor / locked phrases are not changed. See
# docs/experiments/fear_hunger_v0.53l.md "Test #8 maintenance policy".
V053E_CHAMBER_DRIVER_SHA256: str = sha_pins.CHAMBER_DRIVER_SHA


def test_no_src_modifications_to_science_core_compared_to_v0_52b_tip_AND_chamber_driver_re_pinned():  # noqa: N802
    repo_root = Path(__file__).parent.parent
    # Part A: science-core five files unchanged from v0.52b-tip.
    for rel_path, expected_hash in V052B_TIP_SHA256.items():
        path = repo_root / rel_path
        actual_hash = hashlib.sha256(path.read_bytes()).hexdigest()
        if actual_hash != expected_hash:
            raise AssertionError(
                "v0.53e is pre-registered to leave the science-core five files "
                "byte-identical to v0.52b-tip; update the pre-reg before changing "
                "src/core or src/experiments/layouts."
            )

    # Part B: chamber driver byte-identical to v0.53e-tip post-seam-add.
    chamber_path = repo_root / V053E_CHAMBER_DRIVER_PATH
    actual_chamber_hash = hashlib.sha256(chamber_path.read_bytes()).hexdigest()
    if actual_chamber_hash != V053E_CHAMBER_DRIVER_SHA256:
        raise AssertionError(
            "v0.53e's chamber-driver seam is pre-registered to be a one-time "
            "additive change; the chamber driver must remain byte-identical to "
            "its v0.53e-tip hash going forward."
        )


# ---------------------------------------------------------------------------
# Test 9 — Label A high_sensor_radius_lineage picks correct lineage.
# ---------------------------------------------------------------------------


def test_label_a_high_sensor_radius_lineage_picks_correct_lineage():
    sensor_radius_by_lineage = {0: 2, 1: 5, 2: 4, 3: 1, 4: 6}
    label = v0_53e_audit._select_sensor_radius_label(sensor_radius_by_lineage)
    assert label == 4

    # Tiebreak min(lineage_id) on ties.
    sensor_tied = {0: 6, 1: 5, 2: 6, 3: 6, 4: 4}
    label_tied = v0_53e_audit._select_sensor_radius_label(sensor_tied)
    assert label_tied == 0


# ---------------------------------------------------------------------------
# Test 10 — Label B three variants three-tier tiebreak at each window.
# ---------------------------------------------------------------------------


def test_label_b_three_variants_three_tier_tiebreak_at_each_window():
    # Two-way tie on fraction -> tiebreak by count.
    candidates_count_tiebreak = [
        (0, 0.5, 2),
        (1, 0.5, 4),
        (2, 0.4, 5),
    ]
    assert v0_53e_audit._select_fraction_label(candidates_count_tiebreak) == 1

    # Tie on fraction AND count -> tiebreak by min(lineage_id).
    candidates_min_lid = [
        (3, 0.5, 4),
        (1, 0.5, 4),
        (2, 0.5, 4),
    ]
    assert v0_53e_audit._select_fraction_label(candidates_min_lid) == 1

    # Highest fraction wins outright.
    candidates_simple = [(0, 0.3, 5), (1, 0.7, 1), (2, 0.5, 3)]
    assert v0_53e_audit._select_fraction_label(candidates_simple) == 1

    # NaN-loses: empty candidate list returns None.
    assert v0_53e_audit._select_fraction_label([]) is None

    # Verify _readiness_label_at_tick produces identical winners across the
    # three windows when given equivalent readiness snapshots.
    energy_threshold = 5.0
    min_age = 1
    all_lineages = [0, 1, 2]
    snaps_a = [
        v0_53e_audit._ReadinessSnapshot(agent_id=10, lineage_id=0, energy=10.0, age=2),
        v0_53e_audit._ReadinessSnapshot(agent_id=11, lineage_id=0, energy=4.0, age=2),
        v0_53e_audit._ReadinessSnapshot(agent_id=20, lineage_id=1, energy=10.0, age=2),
        v0_53e_audit._ReadinessSnapshot(agent_id=30, lineage_id=2, energy=10.0, age=2),
        v0_53e_audit._ReadinessSnapshot(agent_id=31, lineage_id=2, energy=10.0, age=2),
    ]
    selected_a, _, _, fr_a = v0_53e_audit._readiness_label_at_tick(
        all_lineages, snaps_a, energy_threshold, min_age
    )
    assert selected_a == 2
    assert fr_a[1] == 1.0
    assert fr_a[2] == 1.0
    selected_b, _, _, _ = v0_53e_audit._readiness_label_at_tick(
        all_lineages, snaps_a, energy_threshold, min_age
    )
    selected_c, _, _, _ = v0_53e_audit._readiness_label_at_tick(
        all_lineages, snaps_a, energy_threshold, min_age
    )
    assert selected_a == selected_b == selected_c


# ---------------------------------------------------------------------------
# Test 11 — pre200 window strictly extends pre100 and pre50 windows.
# Synthetic events at ticks 10, 30, 60, 90, 130, 180, 200.
#   pre50_food_events_count  = 2 (ticks 10, 30 <= 50)
#   pre100_food_events_count = 4 (ticks 10, 30, 60, 90 <= 100)
#   pre200_food_events_count = 7 (ticks 10, 30, 60, 90, 130, 180, 200 <= 200)
# ---------------------------------------------------------------------------


def test_pre200_window_strictly_extends_pre100_and_pre50_windows():
    capture = v0_53e_audit._RunCapture(
        arm=v0_53e_audit.ARM_C_WIDENED_STARTING_ENERGY_100,
        layout_name="widened_gradient",
        body_starting_energy=100.0,
        version="v0.42",
        seed=41,
        hazard=0,
    )
    aid = 7
    event_ticks = [10, 30, 60, 90, 130, 180, 200]

    for tick_now in event_ticks:
        if tick_now > v0_53e_audit.TICK_200:
            continue
        if tick_now <= v0_53e_audit.TICK_50:
            capture.pre50_food_events_by_agent[aid] = (
                capture.pre50_food_events_by_agent.get(aid, 0) + 1
            )
            capture.pre50_food_energy_by_agent[aid] = (
                capture.pre50_food_energy_by_agent.get(aid, 0.0) + 1.0
            )
        if tick_now <= v0_53e_audit.TICK_100:
            capture.pre100_food_events_by_agent[aid] = (
                capture.pre100_food_events_by_agent.get(aid, 0) + 1
            )
            capture.pre100_food_energy_by_agent[aid] = (
                capture.pre100_food_energy_by_agent.get(aid, 0.0) + 1.0
            )
        capture.pre200_food_events_by_agent[aid] = (
            capture.pre200_food_events_by_agent.get(aid, 0) + 1
        )
        capture.pre200_food_energy_by_agent[aid] = (
            capture.pre200_food_energy_by_agent.get(aid, 0.0) + 1.0
        )

    assert capture.pre50_food_events_by_agent[aid] == 2
    assert capture.pre100_food_events_by_agent[aid] == 4
    assert capture.pre200_food_events_by_agent[aid] == 7
    assert capture.pre50_food_energy_by_agent[aid] == 2.0
    assert capture.pre100_food_energy_by_agent[aid] == 4.0
    assert capture.pre200_food_energy_by_agent[aid] == 7.0

    # Boundary: events at exactly tick 50, 100, 200 are inclusive; an event
    # at tick 201 must NOT be accumulated.
    capture2 = v0_53e_audit._RunCapture(
        arm=v0_53e_audit.ARM_C_WIDENED_STARTING_ENERGY_100,
        layout_name="widened_gradient",
        body_starting_energy=100.0,
        version="v0.42",
        seed=41,
        hazard=0,
    )
    for tick_now in [50, 100, 200, 201]:
        if tick_now > v0_53e_audit.TICK_200:
            continue
        if tick_now <= v0_53e_audit.TICK_50:
            capture2.pre50_food_events_by_agent[aid] = (
                capture2.pre50_food_events_by_agent.get(aid, 0) + 1
            )
        if tick_now <= v0_53e_audit.TICK_100:
            capture2.pre100_food_events_by_agent[aid] = (
                capture2.pre100_food_events_by_agent.get(aid, 0) + 1
            )
        capture2.pre200_food_events_by_agent[aid] = (
            capture2.pre200_food_events_by_agent.get(aid, 0) + 1
        )
    assert capture2.pre50_food_events_by_agent[aid] == 1  # only tick 50
    assert capture2.pre100_food_events_by_agent[aid] == 2  # ticks 50, 100
    assert capture2.pre200_food_events_by_agent[aid] == 3  # ticks 50, 100, 200


# ---------------------------------------------------------------------------
# Test 12 — Sub-verdict PRESENT requires >= 2/3 firing cells, with the strict
# NaN-counts-toward-denominator rule.
# ---------------------------------------------------------------------------


def test_subverdict_present_requires_two_thirds_firing_cells_with_nan_treated_as_non_firing_strict():  # noqa: E501
    arm = v0_53e_audit.ARM_C_WIDENED_STARTING_ENERGY_100

    # Case: Label A 2 firing + 1 NaN (clears 2/3); Label B 3 firing + 0 NaN.
    summaries_a_2firing_1nan = _three_summaries_for_arm_tick200(
        arm, (+0.6, +0.6, float("nan")), v0_53e_audit.LABEL_A_NAME
    )
    summaries_b_clean = _three_summaries_for_arm_tick200(
        arm, (+0.6, +0.6, -0.6), v0_53e_audit.LABEL_B_TICK200_NAME
    )
    assert (
        v0_53e_audit._arm_subverdict_tick200(arm, summaries_a_2firing_1nan, summaries_b_clean)
        == v0_53e_audit.SUBVERDICT_C_STARTING_ENERGY_100_TICK200_PRESENT
    )

    # Case: Label A 1 firing + 2 NaN (clears 1/3 -> does NOT clear); Label B
    # 3 firing -> only B clears -> PARTIAL.
    summaries_a_1firing_2nan = _three_summaries_for_arm_tick200(
        arm, (+0.6, float("nan"), float("nan")), v0_53e_audit.LABEL_A_NAME
    )
    assert (
        v0_53e_audit._arm_subverdict_tick200(arm, summaries_a_1firing_2nan, summaries_b_clean)
        == v0_53e_audit.SUBVERDICT_C_STARTING_ENERGY_100_TICK200_PARTIAL
    )

    # Case: Label A 3 NaN cells (clears 0/3); Label B 3 firing -> PARTIAL.
    summaries_a_all_nan = _three_summaries_for_arm_tick200(
        arm, (float("nan"), float("nan"), float("nan")), v0_53e_audit.LABEL_A_NAME
    )
    assert (
        v0_53e_audit._arm_subverdict_tick200(arm, summaries_a_all_nan, summaries_b_clean)
        == v0_53e_audit.SUBVERDICT_C_STARTING_ENERGY_100_TICK200_PARTIAL
    )

    # Case: BOTH labels all NaN -> NOT_FOUND.
    summaries_b_all_nan = _three_summaries_for_arm_tick200(
        arm,
        (float("nan"), float("nan"), float("nan")),
        v0_53e_audit.LABEL_B_TICK200_NAME,
    )
    assert (
        v0_53e_audit._arm_subverdict_tick200(arm, summaries_a_all_nan, summaries_b_all_nan)
        == v0_53e_audit.SUBVERDICT_C_STARTING_ENERGY_100_TICK200_NOT_FOUND
    )

    # Case: Both labels 2 firing + 1 NaN -> both clear 2/3 -> PRESENT.
    summaries_b_2firing_1nan = _three_summaries_for_arm_tick200(
        arm, (+0.6, +0.6, float("nan")), v0_53e_audit.LABEL_B_TICK200_NAME
    )
    assert (
        v0_53e_audit._arm_subverdict_tick200(
            arm, summaries_a_2firing_1nan, summaries_b_2firing_1nan
        )
        == v0_53e_audit.SUBVERDICT_C_STARTING_ENERGY_100_TICK200_PRESENT
    )


# ---------------------------------------------------------------------------
# Test 13 — paired_d signed_d <= -0.5 fires RELAXED_OPPOSITE_SIGN_HALT for C arm.
# Synthesized A or B tick-200 wrong-sign does NOT fire priority 3 (priority 2
# catches A via tick-50 sub-verdict; priority 2 catches B via categorical
# anchor if B reachability shifts).
# ---------------------------------------------------------------------------


def test_paired_d_signed_d_le_neg_05_fires_relaxed_opposite_sign_halt_for_c_arm():
    bridge_clean = _zero_drift_bridge_re_anchor()

    # C arm sub-verdict OPPOSITE -> priority 3 RELAXED_OPPOSITE_SIGN_HALT.
    arm_c = v0_53e_audit.ARM_C_WIDENED_STARTING_ENERGY_100
    summaries_a_c = _three_summaries_for_arm_tick200(
        arm_c, (+0.6, +0.6, -0.7), v0_53e_audit.LABEL_A_NAME
    )
    # paired_d = +0.5 on a -1-sign observable -> signed_d = -0.5 -> wrong-sign.
    summaries_b_c = _three_summaries_for_arm_tick200(
        arm_c, (+0.6, +0.6, +0.5), v0_53e_audit.LABEL_B_TICK200_NAME
    )
    c_sub = v0_53e_audit._arm_subverdict_tick200(arm_c, summaries_a_c, summaries_b_c)
    assert c_sub == v0_53e_audit.SUBVERDICT_C_STARTING_ENERGY_100_TICK200_OPPOSITE

    rollup, phrase = v0_53e_audit._evaluate_rollup(
        a_null_tick50_subverdict=v0_53e_audit.SUBVERDICT_A_NULL_V025_TICK50_PRESENT,
        a_null_tick200_subverdict=v0_53e_audit.SUBVERDICT_A_NULL_V025_TICK200_PRESENT,
        b_tick200_subverdict=v0_53e_audit.SUBVERDICT_B_WIDENED_V025_TICK200_NOT_FOUND,
        c_tick200_subverdict=c_sub,
        corpus_re_anchor=[],
        bridge_re_anchor=bridge_clean,
        b_widened_v025_reachability_tick200=0.0,
        c_widened_starting_energy_100_reachability_tick200=0.50,
    )
    assert rollup == v0_53e_audit.ROLLUP_RELAXED_OPPOSITE_SIGN_HALT
    assert "C_widened_starting_energy_100" in phrase

    # B arm OPPOSITE alone does NOT fire priority 3 in v0.53e (B is anchor-only).
    rollup_b_only_opp, _ = v0_53e_audit._evaluate_rollup(
        a_null_tick50_subverdict=v0_53e_audit.SUBVERDICT_A_NULL_V025_TICK50_PRESENT,
        a_null_tick200_subverdict=v0_53e_audit.SUBVERDICT_A_NULL_V025_TICK200_PRESENT,
        b_tick200_subverdict=v0_53e_audit.SUBVERDICT_B_WIDENED_V025_TICK200_OPPOSITE,
        c_tick200_subverdict=v0_53e_audit.SUBVERDICT_C_STARTING_ENERGY_100_TICK200_PRESENT,
        corpus_re_anchor=[],
        bridge_re_anchor=bridge_clean,
        b_widened_v025_reachability_tick200=0.0,
        c_widened_starting_energy_100_reachability_tick200=0.50,
    )
    assert rollup_b_only_opp != v0_53e_audit.ROLLUP_RELAXED_OPPOSITE_SIGN_HALT
    assert rollup_b_only_opp == v0_53e_audit.ROLLUP_WIDENED_BRIDGE_RESCUED_BY_STARTING_ENERGY_100

    # A arm OPPOSITE at tick-200 alone does NOT fire priority 3 directly.
    rollup_a_only_opp, _ = v0_53e_audit._evaluate_rollup(
        a_null_tick50_subverdict=v0_53e_audit.SUBVERDICT_A_NULL_V025_TICK50_PRESENT,
        a_null_tick200_subverdict=v0_53e_audit.SUBVERDICT_A_NULL_V025_TICK200_OPPOSITE,
        b_tick200_subverdict=v0_53e_audit.SUBVERDICT_B_WIDENED_V025_TICK200_NOT_FOUND,
        c_tick200_subverdict=v0_53e_audit.SUBVERDICT_C_STARTING_ENERGY_100_TICK200_PRESENT,
        corpus_re_anchor=[],
        bridge_re_anchor=bridge_clean,
        b_widened_v025_reachability_tick200=0.0,
        c_widened_starting_energy_100_reachability_tick200=0.50,
    )
    assert rollup_a_only_opp != v0_53e_audit.ROLLUP_RELAXED_OPPOSITE_SIGN_HALT


# ---------------------------------------------------------------------------
# Test 14 — Tier-2 categorical anchor on B_widened_V0_25 at tick-200.
# Synthetic B reach=0.0 -> priority 2 does NOT fire.
# Synthetic B reach=1/64 -> priority 2 ANCHOR_REPLICATION_HALT fires.
# Verifies integer-categorical (== 0.0) comparison, not float-tolerance.
# ---------------------------------------------------------------------------


def test_b_widened_v025_categorical_anchor_at_tick_200():
    bridge_clean = _zero_drift_bridge_re_anchor()

    # B reach = 0.0 exactly -> priority 2.c does NOT fire (categorical lock holds).
    rollup_clean, _ = v0_53e_audit._evaluate_rollup(
        a_null_tick50_subverdict=v0_53e_audit.SUBVERDICT_A_NULL_V025_TICK50_PRESENT,
        a_null_tick200_subverdict=v0_53e_audit.SUBVERDICT_A_NULL_V025_TICK200_PRESENT,
        b_tick200_subverdict=v0_53e_audit.SUBVERDICT_B_WIDENED_V025_TICK200_NOT_FOUND,
        c_tick200_subverdict=v0_53e_audit.SUBVERDICT_C_STARTING_ENERGY_100_TICK200_PRESENT,
        corpus_re_anchor=[],
        bridge_re_anchor=bridge_clean,
        b_widened_v025_reachability_tick200=0.0,
        c_widened_starting_energy_100_reachability_tick200=0.50,
    )
    assert rollup_clean == v0_53e_audit.ROLLUP_WIDENED_BRIDGE_RESCUED_BY_STARTING_ENERGY_100

    # B reach = 1/64 = 0.015625 -> priority 2 fires (categorical lock broken).
    one_sixty_fourth = 1.0 / 64.0
    rollup_drift, phrase_drift = v0_53e_audit._evaluate_rollup(
        a_null_tick50_subverdict=v0_53e_audit.SUBVERDICT_A_NULL_V025_TICK50_PRESENT,
        a_null_tick200_subverdict=v0_53e_audit.SUBVERDICT_A_NULL_V025_TICK200_PRESENT,
        b_tick200_subverdict=v0_53e_audit.SUBVERDICT_B_WIDENED_V025_TICK200_NOT_FOUND,
        c_tick200_subverdict=v0_53e_audit.SUBVERDICT_C_STARTING_ENERGY_100_TICK200_PRESENT,
        corpus_re_anchor=[],
        bridge_re_anchor=bridge_clean,
        b_widened_v025_reachability_tick200=one_sixty_fourth,
        c_widened_starting_energy_100_reachability_tick200=0.50,
    )
    assert rollup_drift == v0_53e_audit.ROLLUP_ANCHOR_REPLICATION_HALT
    assert "B_widened_V0_25" in phrase_drift or "0/64" in phrase_drift

    # Comparison is integer-categorical (== 0.0), not float-tolerance: even a
    # tiny non-zero reachability value (e.g., 1e-9) trips the halt.
    rollup_eps, _ = v0_53e_audit._evaluate_rollup(
        a_null_tick50_subverdict=v0_53e_audit.SUBVERDICT_A_NULL_V025_TICK50_PRESENT,
        a_null_tick200_subverdict=v0_53e_audit.SUBVERDICT_A_NULL_V025_TICK200_PRESENT,
        b_tick200_subverdict=v0_53e_audit.SUBVERDICT_B_WIDENED_V025_TICK200_NOT_FOUND,
        c_tick200_subverdict=v0_53e_audit.SUBVERDICT_C_STARTING_ENERGY_100_TICK200_PRESENT,
        corpus_re_anchor=[],
        bridge_re_anchor=bridge_clean,
        b_widened_v025_reachability_tick200=1e-9,
        c_widened_starting_energy_100_reachability_tick200=0.50,
    )
    assert rollup_eps == v0_53e_audit.ROLLUP_ANCHOR_REPLICATION_HALT


# ---------------------------------------------------------------------------
# Test 15 — C_widened_starting_energy_100 reachability threshold partition at tick-200.
#   reach < 0.25                       -> priority 5 BELOW_REACHABILITY (regardless of C sub)
#   reach >= 0.25, C PRESENT           -> priority 4 RESCUED
#   reach >= 0.25, C in {PARTIAL, NF}  -> priority 6 PARTIALLY_RESCUED
# ---------------------------------------------------------------------------


def test_c_widened_starting_energy_100_reachability_threshold_partition_at_tick_200():
    bridge_clean = _zero_drift_bridge_re_anchor()

    # Below threshold (0.20 < 0.25): priority 5 fires regardless of C sub-verdict.
    for c_kind in ("PRESENT", "PARTIAL", "NOT_FOUND"):
        c_sub = _arm_subverdict_for_tick200(v0_53e_audit.ARM_C_WIDENED_STARTING_ENERGY_100, c_kind)
        rollup, phrase = v0_53e_audit._evaluate_rollup(
            a_null_tick50_subverdict=v0_53e_audit.SUBVERDICT_A_NULL_V025_TICK50_PRESENT,
            a_null_tick200_subverdict=v0_53e_audit.SUBVERDICT_A_NULL_V025_TICK200_PRESENT,
            b_tick200_subverdict=v0_53e_audit.SUBVERDICT_B_WIDENED_V025_TICK200_NOT_FOUND,
            c_tick200_subverdict=c_sub,
            corpus_re_anchor=[],
            bridge_re_anchor=bridge_clean,
            b_widened_v025_reachability_tick200=0.0,
            c_widened_starting_energy_100_reachability_tick200=0.20,
        )
        assert rollup == (
            v0_53e_audit.ROLLUP_WIDENED_BELOW_REACHABILITY_THRESHOLD_UNDER_STARTING_ENERGY_100
        )
        assert (
            "The bridge is not rescued by `BodyConfig.starting_energy = 100` "
            "under V0_25 × `widened_gradient` × N_TICKS=200"  # noqa: RUF001
        ) in phrase

    # Above threshold + C PRESENT -> priority 4.
    rollup_present, _ = v0_53e_audit._evaluate_rollup(
        a_null_tick50_subverdict=v0_53e_audit.SUBVERDICT_A_NULL_V025_TICK50_PRESENT,
        a_null_tick200_subverdict=v0_53e_audit.SUBVERDICT_A_NULL_V025_TICK200_PRESENT,
        b_tick200_subverdict=v0_53e_audit.SUBVERDICT_B_WIDENED_V025_TICK200_NOT_FOUND,
        c_tick200_subverdict=v0_53e_audit.SUBVERDICT_C_STARTING_ENERGY_100_TICK200_PRESENT,
        corpus_re_anchor=[],
        bridge_re_anchor=bridge_clean,
        b_widened_v025_reachability_tick200=0.0,
        c_widened_starting_energy_100_reachability_tick200=0.30,
    )
    assert rollup_present == v0_53e_audit.ROLLUP_WIDENED_BRIDGE_RESCUED_BY_STARTING_ENERGY_100

    # Above threshold + C PARTIAL or NOT_FOUND -> priority 6.
    for c_kind in ("PARTIAL", "NOT_FOUND"):
        c_sub = _arm_subverdict_for_tick200(v0_53e_audit.ARM_C_WIDENED_STARTING_ENERGY_100, c_kind)
        rollup, _ = v0_53e_audit._evaluate_rollup(
            a_null_tick50_subverdict=v0_53e_audit.SUBVERDICT_A_NULL_V025_TICK50_PRESENT,
            a_null_tick200_subverdict=v0_53e_audit.SUBVERDICT_A_NULL_V025_TICK200_PRESENT,
            b_tick200_subverdict=v0_53e_audit.SUBVERDICT_B_WIDENED_V025_TICK200_NOT_FOUND,
            c_tick200_subverdict=c_sub,
            corpus_re_anchor=[],
            bridge_re_anchor=bridge_clean,
            b_widened_v025_reachability_tick200=0.0,
            c_widened_starting_energy_100_reachability_tick200=0.30,
        )
        assert rollup == v0_53e_audit.ROLLUP_WIDENED_BRIDGE_PARTIALLY_RESCUED_BY_STARTING_ENERGY_100


# ---------------------------------------------------------------------------
# Test 16 — Rollup locked phrases fire verbatim with diagnostic substrings AND
# priority cascade + partition exhaustiveness. Predecessor references to v0.53c
# (WIDENED_BELOW_REACHABILITY_THRESHOLD_AT_TICK_200) and v0.53d
# (WIDENED_BELOW_REACHABILITY_THRESHOLD_UNDER_RELAXED_INFLUX) must appear in
# the priority-4 / -5 / -6 locked phrases verbatim.
# ---------------------------------------------------------------------------


def test_rollup_locked_phrases_fire_verbatim_and_priority_cascade_partition_total():
    bridge_clean = _zero_drift_bridge_re_anchor()
    bridge_drift = list(bridge_clean)
    bridge_drift[0] = v0_53e_audit.BridgeReAnchorRow(
        label=bridge_drift[0].label,
        observable=bridge_drift[0].observable,
        published_signed_d=bridge_drift[0].published_signed_d,
        derived_signed_d=bridge_drift[0].published_signed_d + 1.5,
        drift_abs=1.5,
        halts=True,
    )
    corpus_halt = [
        v0_53e_audit.ReAnchorRow(
            arm=v0_53e_audit.ARM_A_NULL_V025,
            version="v0.42",
            hazard=8,
            n_runs_contributing=8,
            a_share_h8_derived=0.700,
            a_share_h8_published=0.652,
            drift_abs=0.048,
            halts=True,
        )
    ]

    # ----- Part A: locked-phrase verbatim substrings (priorities 4 / 5 / 6).
    # RESCUED (priority 4).
    _, phrase_rescued = v0_53e_audit._evaluate_rollup(
        a_null_tick50_subverdict=v0_53e_audit.SUBVERDICT_A_NULL_V025_TICK50_PRESENT,
        a_null_tick200_subverdict=v0_53e_audit.SUBVERDICT_A_NULL_V025_TICK200_PRESENT,
        b_tick200_subverdict=v0_53e_audit.SUBVERDICT_B_WIDENED_V025_TICK200_NOT_FOUND,
        c_tick200_subverdict=v0_53e_audit.SUBVERDICT_C_STARTING_ENERGY_100_TICK200_PRESENT,
        corpus_re_anchor=[],
        bridge_re_anchor=bridge_clean,
        b_widened_v025_reachability_tick200=0.0,
        c_widened_starting_energy_100_reachability_tick200=0.50,
    )
    assert (
        "The (V0_25 × `widened_gradient`) reachability ceiling is bounded by the V0_25 "  # noqa: RUF001
        "founder starting-energy budget at the `max_energy` bound, not by the geometry alone"
    ) in phrase_rescued
    assert "WIDENED_BELOW_REACHABILITY_THRESHOLD_AT_TICK_200" in phrase_rescued
    assert "WIDENED_BELOW_REACHABILITY_THRESHOLD_UNDER_RELAXED_INFLUX" in phrase_rescued

    # BELOW_THRESHOLD (priority 5).
    _, phrase_below = v0_53e_audit._evaluate_rollup(
        a_null_tick50_subverdict=v0_53e_audit.SUBVERDICT_A_NULL_V025_TICK50_PRESENT,
        a_null_tick200_subverdict=v0_53e_audit.SUBVERDICT_A_NULL_V025_TICK200_PRESENT,
        b_tick200_subverdict=v0_53e_audit.SUBVERDICT_B_WIDENED_V025_TICK200_NOT_FOUND,
        c_tick200_subverdict=v0_53e_audit.SUBVERDICT_C_STARTING_ENERGY_100_TICK200_PRESENT,
        corpus_re_anchor=[],
        bridge_re_anchor=bridge_clean,
        b_widened_v025_reachability_tick200=0.0,
        c_widened_starting_energy_100_reachability_tick200=0.10,
    )
    assert (
        "The bridge is not rescued by `BodyConfig.starting_energy = 100` under V0_25 × "  # noqa: RUF001
        "`widened_gradient` × N_TICKS=200"  # noqa: RUF001
    ) in phrase_below
    assert "WIDENED_BELOW_REACHABILITY_THRESHOLD_AT_TICK_200" in phrase_below
    assert "WIDENED_BELOW_REACHABILITY_THRESHOLD_UNDER_RELAXED_INFLUX" in phrase_below

    # PARTIALLY_RESCUED (priority 6).
    _, phrase_partial = v0_53e_audit._evaluate_rollup(
        a_null_tick50_subverdict=v0_53e_audit.SUBVERDICT_A_NULL_V025_TICK50_PRESENT,
        a_null_tick200_subverdict=v0_53e_audit.SUBVERDICT_A_NULL_V025_TICK200_PRESENT,
        b_tick200_subverdict=v0_53e_audit.SUBVERDICT_B_WIDENED_V025_TICK200_NOT_FOUND,
        c_tick200_subverdict=v0_53e_audit.SUBVERDICT_C_STARTING_ENERGY_100_TICK200_NOT_FOUND,
        corpus_re_anchor=[],
        bridge_re_anchor=bridge_clean,
        b_widened_v025_reachability_tick200=0.0,
        c_widened_starting_energy_100_reachability_tick200=0.30,
    )
    assert (
        "reachability becomes measurable but the bridge does not fully replicate"
    ) in phrase_partial
    assert "WIDENED_BELOW_REACHABILITY_THRESHOLD_AT_TICK_200" in phrase_partial
    assert "WIDENED_BELOW_REACHABILITY_THRESHOLD_UNDER_RELAXED_INFLUX" in phrase_partial

    # ----- Part B: priority cascade (1 > 2.a > 2.b > 2.c > 3 > 4/5/6).
    # All priority-1/2/3 halt classes simultaneously: priority 1 wins.
    rollup_1, phrase_1 = v0_53e_audit._evaluate_rollup(
        a_null_tick50_subverdict=v0_53e_audit.SUBVERDICT_A_NULL_V025_TICK50_NOT_FOUND,
        a_null_tick200_subverdict=v0_53e_audit.SUBVERDICT_A_NULL_V025_TICK200_PRESENT,
        b_tick200_subverdict=v0_53e_audit.SUBVERDICT_B_WIDENED_V025_TICK200_NOT_FOUND,
        c_tick200_subverdict=v0_53e_audit.SUBVERDICT_C_STARTING_ENERGY_100_TICK200_OPPOSITE,
        corpus_re_anchor=corpus_halt,
        bridge_re_anchor=bridge_drift,
        b_widened_v025_reachability_tick200=1.0 / 64.0,
        c_widened_starting_energy_100_reachability_tick200=0.50,
    )
    assert rollup_1 == v0_53e_audit.ROLLUP_CORPUS_DRIFT_HALT
    assert "v0.42" in phrase_1

    # Priority 2.a only (Tier-1 drift): wins over downstream halts.
    rollup_2a, _ = v0_53e_audit._evaluate_rollup(
        a_null_tick50_subverdict=v0_53e_audit.SUBVERDICT_A_NULL_V025_TICK50_PRESENT,
        a_null_tick200_subverdict=v0_53e_audit.SUBVERDICT_A_NULL_V025_TICK200_PRESENT,
        b_tick200_subverdict=v0_53e_audit.SUBVERDICT_B_WIDENED_V025_TICK200_NOT_FOUND,
        c_tick200_subverdict=v0_53e_audit.SUBVERDICT_C_STARTING_ENERGY_100_TICK200_OPPOSITE,
        corpus_re_anchor=[],
        bridge_re_anchor=bridge_drift,
        b_widened_v025_reachability_tick200=0.0,
        c_widened_starting_energy_100_reachability_tick200=0.50,
    )
    assert rollup_2a == v0_53e_audit.ROLLUP_ANCHOR_REPLICATION_HALT

    # Priority 2.b only (A_null tick-50 sub-verdict != PRESENT).
    rollup_2b, _ = v0_53e_audit._evaluate_rollup(
        a_null_tick50_subverdict=v0_53e_audit.SUBVERDICT_A_NULL_V025_TICK50_NOT_FOUND,
        a_null_tick200_subverdict=v0_53e_audit.SUBVERDICT_A_NULL_V025_TICK200_PRESENT,
        b_tick200_subverdict=v0_53e_audit.SUBVERDICT_B_WIDENED_V025_TICK200_NOT_FOUND,
        c_tick200_subverdict=v0_53e_audit.SUBVERDICT_C_STARTING_ENERGY_100_TICK200_OPPOSITE,
        corpus_re_anchor=[],
        bridge_re_anchor=bridge_clean,
        b_widened_v025_reachability_tick200=0.0,
        c_widened_starting_energy_100_reachability_tick200=0.50,
    )
    assert rollup_2b == v0_53e_audit.ROLLUP_ANCHOR_REPLICATION_HALT

    # Priority 2.c only (B_widened categorical anchor broken).
    rollup_2c, _ = v0_53e_audit._evaluate_rollup(
        a_null_tick50_subverdict=v0_53e_audit.SUBVERDICT_A_NULL_V025_TICK50_PRESENT,
        a_null_tick200_subverdict=v0_53e_audit.SUBVERDICT_A_NULL_V025_TICK200_PRESENT,
        b_tick200_subverdict=v0_53e_audit.SUBVERDICT_B_WIDENED_V025_TICK200_NOT_FOUND,
        c_tick200_subverdict=v0_53e_audit.SUBVERDICT_C_STARTING_ENERGY_100_TICK200_OPPOSITE,
        corpus_re_anchor=[],
        bridge_re_anchor=bridge_clean,
        b_widened_v025_reachability_tick200=1.0 / 64.0,
        c_widened_starting_energy_100_reachability_tick200=0.50,
    )
    assert rollup_2c == v0_53e_audit.ROLLUP_ANCHOR_REPLICATION_HALT

    # Priority 3 alone (C OPPOSITE; all priority-2 conditions clean).
    rollup_3, _ = v0_53e_audit._evaluate_rollup(
        a_null_tick50_subverdict=v0_53e_audit.SUBVERDICT_A_NULL_V025_TICK50_PRESENT,
        a_null_tick200_subverdict=v0_53e_audit.SUBVERDICT_A_NULL_V025_TICK200_PRESENT,
        b_tick200_subverdict=v0_53e_audit.SUBVERDICT_B_WIDENED_V025_TICK200_NOT_FOUND,
        c_tick200_subverdict=v0_53e_audit.SUBVERDICT_C_STARTING_ENERGY_100_TICK200_OPPOSITE,
        corpus_re_anchor=[],
        bridge_re_anchor=bridge_clean,
        b_widened_v025_reachability_tick200=0.0,
        c_widened_starting_energy_100_reachability_tick200=0.50,
    )
    assert rollup_3 == v0_53e_audit.ROLLUP_RELAXED_OPPOSITE_SIGN_HALT

    # ----- Part C: partition exhaustiveness over (C reachability, C sub-verdict).
    # A_null_V0_25 / B_widened_V0_25 non-OPPOSITE tick-200 sub-verdicts do NOT
    # affect priority 4/5/6 (C-only gating).
    sub_kinds_non_opp = ("PRESENT", "PARTIAL", "NOT_FOUND")
    seen: dict[tuple[str, str, str, str], str] = {}
    for a_kind in sub_kinds_non_opp:
        for b_kind in sub_kinds_non_opp:
            for c_kind in sub_kinds_non_opp:
                a_sub = _arm_subverdict_for_tick200(v0_53e_audit.ARM_A_NULL_V025, a_kind)
                b_sub = _arm_subverdict_for_tick200(v0_53e_audit.ARM_B_WIDENED_V025, b_kind)
                c_sub = _arm_subverdict_for_tick200(
                    v0_53e_audit.ARM_C_WIDENED_STARTING_ENERGY_100, c_kind
                )

                # C reach >= 0.25 (above threshold).
                rollup_above, _ = v0_53e_audit._evaluate_rollup(
                    a_null_tick50_subverdict=v0_53e_audit.SUBVERDICT_A_NULL_V025_TICK50_PRESENT,
                    a_null_tick200_subverdict=a_sub,
                    b_tick200_subverdict=b_sub,
                    c_tick200_subverdict=c_sub,
                    corpus_re_anchor=[],
                    bridge_re_anchor=bridge_clean,
                    b_widened_v025_reachability_tick200=0.0,
                    c_widened_starting_energy_100_reachability_tick200=0.50,
                )
                seen[(a_kind, b_kind, c_kind, "above")] = rollup_above

                # C reach < 0.25 (below threshold).
                rollup_below, _ = v0_53e_audit._evaluate_rollup(
                    a_null_tick50_subverdict=v0_53e_audit.SUBVERDICT_A_NULL_V025_TICK50_PRESENT,
                    a_null_tick200_subverdict=a_sub,
                    b_tick200_subverdict=b_sub,
                    c_tick200_subverdict=c_sub,
                    corpus_re_anchor=[],
                    bridge_re_anchor=bridge_clean,
                    b_widened_v025_reachability_tick200=0.0,
                    c_widened_starting_energy_100_reachability_tick200=0.10,
                )
                seen[(a_kind, b_kind, c_kind, "below")] = rollup_below

    # Above threshold: rollup gates only on C sub-verdict (A/B irrelevant).
    rescued = v0_53e_audit.ROLLUP_WIDENED_BRIDGE_RESCUED_BY_STARTING_ENERGY_100
    partial = v0_53e_audit.ROLLUP_WIDENED_BRIDGE_PARTIALLY_RESCUED_BY_STARTING_ENERGY_100
    below = v0_53e_audit.ROLLUP_WIDENED_BELOW_REACHABILITY_THRESHOLD_UNDER_STARTING_ENERGY_100
    for (a_kind, b_kind, c_kind, regime), rollup in seen.items():
        if regime == "above":
            if c_kind == "PRESENT":
                assert rollup == rescued, (
                    f"Combo (A={a_kind}, B={b_kind}, C={c_kind}, above): "
                    f"expected RESCUED but got {rollup}"
                )
            else:
                assert rollup == partial, (
                    f"Combo (A={a_kind}, B={b_kind}, C={c_kind}, above): "
                    f"expected PARTIALLY_RESCUED but got {rollup}"
                )
        else:  # below
            assert rollup == below, (
                f"Combo (A={a_kind}, B={b_kind}, C={c_kind}, below): "
                f"expected BELOW_REACHABILITY_THRESHOLD_UNDER_STARTING_ENERGY_100 "
                f"but got {rollup}"
            )

    # 27 (A,B,C combos non-opposite) * 2 (above/below) = 54 entries.
    assert len(seen) == 54


# Sanity: pytest must be importable for the runner to discover this file.
_ = pytest
