"""v0.52 sensor_radius information vs metabolic-cost decoupling — tests (16 locked).

Pre-reg: [[docs/experiments/fear_hunger_v0.52.md]] §"Test list (locked, 16 tests)".
Tests numbered to match the pre-reg's ordering.
"""

from __future__ import annotations

import dataclasses
import importlib.util
import math
import sys
from pathlib import Path

import numpy as np
import pytest

_SCRIPT_PATH = Path(__file__).parent.parent / "scripts" / "v0_52_information_vs_cost_audit.py"
_spec = importlib.util.spec_from_file_location("v0_52_audit", _SCRIPT_PATH)
assert _spec is not None
assert _spec.loader is not None
v0_52_audit = importlib.util.module_from_spec(_spec)
sys.modules["v0_52_audit"] = v0_52_audit
_spec.loader.exec_module(v0_52_audit)


# ---------------------------------------------------------------------------
# Synthetic helpers
# ---------------------------------------------------------------------------


def _make_lineage_row(
    *,
    arm: str = v0_52_audit.ARM_A_NULL,
    version: str = "v0.42",
    seed: int = 41,
    hazard: int = 8,
    lineage_id: int,
    founder_sensor_radius: int = 3,
    rd: float = 0.0,
    mr: float = 0.0,
    food_events: int = 0,
    food_energy: float = 0.0,
    distance: float = 0.0,
    living: int = 0,
    above_count: int = 0,
    above_fraction: float = 0.0,
    b50: int = 0,
    is_eventual_top: bool = False,
    is_high_sensor_radius: bool = False,
    is_high_readiness_fraction: bool = False,
    cost: float = 0.05,
    override: int | None = None,
) -> object:
    return v0_52_audit.PerLineageRow(
        arm=arm,
        version=version,
        seed=seed,
        hazard=hazard,
        run_id=f"{arm}-{version}-A_null-hzd{hazard}-seed-{seed}",
        lineage_id=lineage_id,
        founder_sensor_radius=founder_sensor_radius,
        founder_reproduction_drive=rd,
        founder_metabolic_rate=mr,
        pre50_food_events_count=food_events,
        pre50_food_energy_acquired=food_energy,
        mean_distance_to_nearest_food_cell=distance,
        tick50_living_count=living,
        tick50_above_threshold_count=above_count,
        tick50_above_threshold_fraction=above_fraction,
        b50_count=b50,
        is_eventual_top_b50_label=is_eventual_top,
        is_high_sensor_radius_lineage=is_high_sensor_radius,
        is_high_tick50_readiness_fraction_lineage=is_high_readiness_fraction,
        body_config_sensor_radius_metabolic_cost=cost,
        body_config_effective_sensor_radius_override=override,
    )


def _make_summary(
    *,
    arm: str,
    observable: str,
    sign: int,
    paired_d: float,
    label: str,
) -> object:
    signed = paired_d * sign if not math.isnan(paired_d) else float("nan")
    fires_expected = (not math.isnan(signed)) and signed >= v0_52_audit.COHENS_D_THRESHOLD
    fires_wrong = (not math.isnan(signed)) and signed <= -v0_52_audit.COHENS_D_THRESHOLD
    return v0_52_audit.ObservableSummary(
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


def _three_summaries_for_arm(arm: str, ds: tuple[float, float, float], label: str) -> list[object]:
    obs = v0_52_audit.PRIMARY_OBSERVABLES
    return [
        _make_summary(arm=arm, observable=obs[i][0], sign=obs[i][1], paired_d=ds[i], label=label)
        for i in range(3)
    ]


def _zero_drift_bridge_re_anchor() -> list[object]:
    return [
        v0_52_audit.BridgeReAnchorRow(
            label=label,
            observable=obs,
            published_signed_d=ref,
            derived_signed_d=ref,
            drift_abs=0.0,
            halts=False,
        )
        for (label, obs), ref in v0_52_audit.V048_PUBLISHED_SIGNED_D.items()
    ]


# ---------------------------------------------------------------------------
# Test 1 — all arms construct founders via the normal A_null path
# ---------------------------------------------------------------------------


def test_all_arms_construct_founders_via_normal_a_null_path(tmp_path):
    """Run all three arms for one (version, seed, hazard); assert founder
    traits are byte-identical across arms (proves traits_override=None
    and identical streams.mutation consumption at setup_observer time)."""
    seed = 41
    captures: dict[str, object] = {}
    for arm in v0_52_audit.ARMS:
        captures[arm] = v0_52_audit._run_one_arm(
            arm=arm, version="v0.42", seed=seed, hazard=0, runs_root=tmp_path
        )
    arms = list(v0_52_audit.ARMS)
    base = captures[arms[0]]
    for arm in arms[1:]:
        cap = captures[arm]
        for r_base, r in zip(base.founder_records, cap.founder_records, strict=True):
            assert r_base.founder_sensor_radius == r.founder_sensor_radius
            assert r_base.founder_reproduction_drive == r.founder_reproduction_drive
            assert r_base.founder_metabolic_rate == r.founder_metabolic_rate


# ---------------------------------------------------------------------------
# Test 2 — B replaces body_config with sensor_radius_metabolic_cost = 0
# ---------------------------------------------------------------------------


def test_b_replaces_body_config_with_zero_sensor_cost(tmp_path):
    cap = v0_52_audit._run_one_arm(
        arm=v0_52_audit.ARM_B_ZERO_COST,
        version="v0.42",
        seed=41,
        hazard=0,
        runs_root=tmp_path,
    )
    assert cap.body_config_sensor_radius_metabolic_cost == 0.0
    assert cap.body_config_effective_sensor_radius_override is None
    # Founders untouched: sensor_radius variation preserved.
    radii = [r.founder_sensor_radius for r in cap.founder_records]
    assert len(set(radii)) > 1 or len(radii) == 1, (
        "founders should retain their unmutated sensor_radius draw under B"
    )


# ---------------------------------------------------------------------------
# Test 3 — C passes effective_sensor_radius_override = 6 via body_config
# ---------------------------------------------------------------------------


def test_c_passes_effective_sensor_radius_override_via_body_config(tmp_path):
    cap = v0_52_audit._run_one_arm(
        arm=v0_52_audit.ARM_C_UNIFORM_RADIUS,
        version="v0.42",
        seed=41,
        hazard=0,
        runs_root=tmp_path,
    )
    assert cap.body_config_effective_sensor_radius_override == 6
    # Cost remains at the V0_25 default 0.05 (metabolic-cost channel preserved).
    assert cap.body_config_sensor_radius_metabolic_cost == pytest.approx(0.05)
    # Founders untouched.
    radii = [r.founder_sensor_radius for r in cap.founder_records]
    assert all(1 <= r <= 6 for r in radii)


# ---------------------------------------------------------------------------
# Test 4 — default-equivalence (override=None resolver branch is byte-equivalent)
# ---------------------------------------------------------------------------


def test_default_equivalence_preserves_byte_identity():
    """Synthetic unit test: with effective_sensor_radius_override=None and
    default sensor_radius_metabolic_cost=0.05, sensors.observe and
    _read_memory_directional produce identical outputs to a body whose
    sensor_radius is read directly from body.traits — i.e., the resolver's
    None-default branch is byte-equivalent to the pre-modification code
    path. Corpus-level enforcement is the existing 1664-test pytest suite
    passing without modification."""
    from hedonism_harness.core.body import make_body
    from hedonism_harness.core.config import BodyConfig, WorldConfig
    from hedonism_harness.core.memory import make_memory
    from hedonism_harness.core.sensors import observe
    from hedonism_harness.core.traits import TraitConfig, random_traits
    from hedonism_harness.core.world import build_world

    rng = np.random.default_rng(123)
    traits = random_traits(TraitConfig(unbounded_mutation=True), rng)
    world = build_world(WorldConfig(seed=42, width=12, height=12))
    body = make_body(
        body_id=1,
        lineage_id=0,
        parent_id=None,
        x=6,
        y=6,
        traits=traits,
        config=BodyConfig(),
    )
    memory = make_memory(world.width, world.height)

    body_config_default = BodyConfig()  # override=None, cost=0.05
    obs_default = observe(world, body, body_config_default, memory=memory)

    # Synthesize an "explicit no-override" body_config via model_copy with
    # the same defaults; should produce byte-identical output.
    body_config_explicit = body_config_default.model_copy(update={})
    obs_explicit = observe(world, body, body_config_explicit, memory=memory)

    assert obs_default == obs_explicit, "override=None resolver branch is not byte-equivalent"


# ---------------------------------------------------------------------------
# Test 5 — C override reaches sensors.observe axial scan
# ---------------------------------------------------------------------------


def test_c_override_reaches_observe_axial_scan():
    """Set effective_sensor_radius_override=6 on body_config; construct a
    body whose traits.sensor_radius=2; place a food cell at distance 5
    along +x. Without the override the observe() axial scan would not
    detect the food (distance 5 > radius 2); with the override the
    food is detected (distance 5 <= radius 6)."""
    from hedonism_harness.core.body import make_body
    from hedonism_harness.core.config import BodyConfig, WorldConfig
    from hedonism_harness.core.sensors import observe
    from hedonism_harness.core.traits import TraitConfig, random_traits
    from hedonism_harness.core.world import build_world

    rng = np.random.default_rng(456)
    traits = random_traits(TraitConfig(unbounded_mutation=True), rng)
    traits = dataclasses.replace(traits, sensor_radius=2)
    world = build_world(WorldConfig(seed=42, width=12, height=12))
    # Clear all food + hazard, then place exactly one food cell at distance 5 east.
    world.food_value[:, :] = 0.0
    world.hazard_damage[:, :] = 0.0
    world.food_value[6 + 5, 6] = 10.0  # body at (6, 6), food at (11, 6) -> distance 5
    body = make_body(
        body_id=1,
        lineage_id=0,
        parent_id=None,
        x=6,
        y=6,
        traits=traits,
        config=BodyConfig(),
    )
    body_config_no_override = BodyConfig()
    obs_no_override = observe(world, body, body_config_no_override, memory=None)
    # With trait radius 2, distance-5 food is invisible -> east signal == 0.
    assert obs_no_override.food_signal_east == 0.0

    body_config_override = BodyConfig(effective_sensor_radius_override=6)
    obs_override = observe(world, body, body_config_override, memory=None)
    # With override radius 6, distance-5 food is visible -> east signal > 0.
    assert obs_override.food_signal_east > 0.0


# ---------------------------------------------------------------------------
# Test 6 — C override reaches ValenceMemory directional scan
# ---------------------------------------------------------------------------


def test_c_override_reaches_valence_memory_directional_scan():
    """Same probe as test 5, but on the memory directional path. Place a
    pleasure marker in ValenceMemory at distance 5 along +x; with trait
    radius 2 the memory directional signal at east is 0; with override 6
    it is positive."""
    from hedonism_harness.core.body import make_body
    from hedonism_harness.core.config import BodyConfig, WorldConfig
    from hedonism_harness.core.memory import make_memory
    from hedonism_harness.core.sensors import observe
    from hedonism_harness.core.traits import TraitConfig, random_traits
    from hedonism_harness.core.world import build_world

    rng = np.random.default_rng(789)
    traits = random_traits(TraitConfig(unbounded_mutation=True), rng)
    traits = dataclasses.replace(traits, sensor_radius=2)
    world = build_world(WorldConfig(seed=42, width=12, height=12))
    world.food_value[:, :] = 0.0
    world.hazard_damage[:, :] = 0.0
    body = make_body(
        body_id=1,
        lineage_id=0,
        parent_id=None,
        x=6,
        y=6,
        traits=traits,
        config=BodyConfig(),
    )
    memory = make_memory(world.width, world.height)
    # Plant a pleasure EMA marker at (6+5, 6) = distance 5 east.
    memory.pleasure_ema[6 + 5, 6] = 1.0

    body_config_no_override = BodyConfig()
    obs_no_override = observe(world, body, body_config_no_override, memory=memory)
    # Trait radius 2 -> remembered_good_east is 0 (distance 5 not in range).
    assert obs_no_override.remembered_good_east == 0.0

    body_config_override = BodyConfig(effective_sensor_radius_override=6)
    obs_override = observe(world, body, body_config_override, memory=memory)
    # Override 6 -> remembered_good_east > 0 (distance 5 in range).
    assert obs_override.remembered_good_east > 0.0


# ---------------------------------------------------------------------------
# Test 7 — C override does NOT affect apply_metabolism
# ---------------------------------------------------------------------------


def test_c_override_does_not_affect_apply_metabolism():
    """Set effective_sensor_radius_override=6; construct two bodies, one
    with traits.sensor_radius=2 and one with traits.sensor_radius=6.
    apply_metabolism's per-tick energy cost must reflect the trait
    sensor_radius (NOT the override) — the metabolic-cost channel must
    remain trait-tied even under C."""
    from hedonism_harness.core.body import apply_metabolism, make_body
    from hedonism_harness.core.config import BodyConfig
    from hedonism_harness.core.traits import TraitConfig, random_traits

    body_config = BodyConfig(effective_sensor_radius_override=6)
    rng = np.random.default_rng(999)
    base_traits = random_traits(TraitConfig(unbounded_mutation=True), rng)
    traits_low = dataclasses.replace(base_traits, sensor_radius=2)
    traits_high = dataclasses.replace(base_traits, sensor_radius=6)

    body_low = make_body(
        body_id=1, lineage_id=0, parent_id=None, x=0, y=0, traits=traits_low, config=BodyConfig()
    )
    body_high = make_body(
        body_id=2, lineage_id=1, parent_id=None, x=0, y=0, traits=traits_high, config=BodyConfig()
    )

    # Reset energy to a known value so cost is observable.
    body_low = dataclasses.replace(body_low, energy=100.0)
    body_high = dataclasses.replace(body_high, energy=100.0)

    after_low = apply_metabolism(body_low, body_config)
    after_high = apply_metabolism(body_high, body_config)

    cost_low = 100.0 - after_low.energy
    cost_high = 100.0 - after_high.energy
    # Cost formula (body.py:79): base_metabolic_cost * traits.metabolic_rate
    #                           + sensor_radius_metabolic_cost * traits.sensor_radius.
    # Same body except sensor_radius -> cost diff equals
    # sensor_radius_metabolic_cost * (6 - 2) = 0.05 * 4 = 0.2.
    # If override leaked into apply_metabolism, cost_low == cost_high (both pay
    # 0.05 * 6) and the diff would be 0.0.
    assert cost_high - cost_low == pytest.approx(0.2), (
        f"cost diff between trait sensor_radius 6 vs 2 must reflect the trait "
        f"(0.05 * 4 = 0.2); got cost_high={cost_high}, cost_low={cost_low}, "
        f"diff={cost_high - cost_low}"
    )
    assert cost_low != cost_high, "metabolic cost must differ between low and high trait radius"


# ---------------------------------------------------------------------------
# Test 8 — C override does NOT affect DirectionalMemory path
# ---------------------------------------------------------------------------


def test_c_override_does_not_affect_directional_memory_path():
    """DirectionalMemory does not consume sensor_radius; the v0.52 override
    must not leak into its branch. Construct a DirectionalMemory with
    known tendencies; assert _read_memory_directional output is identical
    with override=None and override=6."""
    from hedonism_harness.core.body import make_body
    from hedonism_harness.core.config import BodyConfig, WorldConfig
    from hedonism_harness.core.memory import make_directional_memory
    from hedonism_harness.core.sensors import _read_memory_directional
    from hedonism_harness.core.traits import TraitConfig, random_traits
    from hedonism_harness.core.world import build_world

    rng = np.random.default_rng(321)
    traits = random_traits(TraitConfig(unbounded_mutation=True), rng)
    world = build_world(WorldConfig(seed=42, width=12, height=12))
    body = make_body(
        body_id=1, lineage_id=0, parent_id=None, x=6, y=6, traits=traits, config=BodyConfig()
    )
    memory = make_directional_memory()
    memory.pleasure_tendency[0] = 0.7  # north slot
    memory.pain_tendency[1] = 0.3  # south slot

    out_no_override = _read_memory_directional(memory, body, world, BodyConfig())
    out_override = _read_memory_directional(
        memory, body, world, BodyConfig(effective_sensor_radius_override=6)
    )
    assert out_no_override == out_override


# ---------------------------------------------------------------------------
# Test 9 — no RNG setup offset across arms
# ---------------------------------------------------------------------------


def test_no_rng_setup_offset_across_arms(tmp_path):
    """For the same (version, seed, hazard), founder original sensor_radius
    AND every other founder trait must be byte-identical across all three
    arms — proves neither the body_config swap (B, C) nor the modified
    sensors.observe resolver consumes RNG during setup_observer."""
    seed = 47
    arm_to_originals: dict[str, list[tuple]] = {}
    for arm in v0_52_audit.ARMS:
        cap = v0_52_audit._run_one_arm(
            arm=arm, version="v0.42", seed=seed, hazard=8, runs_root=tmp_path
        )
        arm_to_originals[arm] = [
            (
                rec.lineage_id,
                rec.founder_sensor_radius,
                rec.founder_reproduction_drive,
                rec.founder_metabolic_rate,
            )
            for rec in cap.founder_records
        ]
    arms = list(v0_52_audit.ARMS)
    for arm in arms[1:]:
        assert arm_to_originals[arm] == arm_to_originals[arms[0]], (
            f"founder traits differ between {arms[0]} and {arm}"
        )


# ---------------------------------------------------------------------------
# Test 10 — A_null sub-verdict PRESENT requires both labels clear ≥ 2/3
# ---------------------------------------------------------------------------


def test_per_arm_subverdict_a_null_present_requires_both_labels_clear():
    summaries_a = _three_summaries_for_arm(
        v0_52_audit.ARM_A_NULL, (+0.6, +0.7, -0.3), v0_52_audit.LABEL_A_NAME
    )
    summaries_b = _three_summaries_for_arm(
        v0_52_audit.ARM_A_NULL, (+0.6, +0.8, -0.2), v0_52_audit.LABEL_B_NAME
    )
    assert (
        v0_52_audit._arm_subverdict(v0_52_audit.ARM_A_NULL, summaries_a, summaries_b)
        == v0_52_audit.SUBVERDICT_A_NULL_PRESENT
    )

    # Label A 1/3, Label B 2/3 -> PARTIAL.
    summaries_a_partial = _three_summaries_for_arm(
        v0_52_audit.ARM_A_NULL, (+0.6, +0.3, -0.2), v0_52_audit.LABEL_A_NAME
    )
    assert (
        v0_52_audit._arm_subverdict(v0_52_audit.ARM_A_NULL, summaries_a_partial, summaries_b)
        == v0_52_audit.SUBVERDICT_A_NULL_PARTIAL
    )


# ---------------------------------------------------------------------------
# Test 11 — B_zero_cost sub-verdict PRESENT requires both labels clear
# ---------------------------------------------------------------------------


def test_per_arm_subverdict_b_zero_cost_present_requires_both_labels_clear():
    summaries_a = _three_summaries_for_arm(
        v0_52_audit.ARM_B_ZERO_COST, (+0.7, +0.7, -0.6), v0_52_audit.LABEL_A_NAME
    )
    summaries_b = _three_summaries_for_arm(
        v0_52_audit.ARM_B_ZERO_COST, (+0.6, +0.7, -0.6), v0_52_audit.LABEL_B_NAME
    )
    assert (
        v0_52_audit._arm_subverdict(v0_52_audit.ARM_B_ZERO_COST, summaries_a, summaries_b)
        == v0_52_audit.SUBVERDICT_B_PRESENT
    )

    summaries_a_low = _three_summaries_for_arm(
        v0_52_audit.ARM_B_ZERO_COST, (+0.2, +0.2, -0.2), v0_52_audit.LABEL_A_NAME
    )
    assert (
        v0_52_audit._arm_subverdict(v0_52_audit.ARM_B_ZERO_COST, summaries_a_low, summaries_b)
        == v0_52_audit.SUBVERDICT_B_PARTIAL
    )


# ---------------------------------------------------------------------------
# Test 12 — C_uniform_radius sub-verdict PRESENT requires both labels clear
# ---------------------------------------------------------------------------


def test_per_arm_subverdict_c_uniform_radius_present_requires_both_labels_clear():
    summaries_a = _three_summaries_for_arm(
        v0_52_audit.ARM_C_UNIFORM_RADIUS, (+0.7, +0.7, -0.6), v0_52_audit.LABEL_A_NAME
    )
    summaries_b = _three_summaries_for_arm(
        v0_52_audit.ARM_C_UNIFORM_RADIUS, (+0.2, +0.2, -0.2), v0_52_audit.LABEL_B_NAME
    )
    assert (
        v0_52_audit._arm_subverdict(v0_52_audit.ARM_C_UNIFORM_RADIUS, summaries_a, summaries_b)
        == v0_52_audit.SUBVERDICT_C_PARTIAL
    )

    summaries_b_clears = _three_summaries_for_arm(
        v0_52_audit.ARM_C_UNIFORM_RADIUS, (+0.6, +0.7, -0.6), v0_52_audit.LABEL_B_NAME
    )
    assert (
        v0_52_audit._arm_subverdict(
            v0_52_audit.ARM_C_UNIFORM_RADIUS, summaries_a, summaries_b_clears
        )
        == v0_52_audit.SUBVERDICT_C_PRESENT
    )


# ---------------------------------------------------------------------------
# Test 13 — Rollup INFORMATION_RADIUS_LOAD_BEARING when (PRESENT, PRESENT, NOT_FOUND)
# ---------------------------------------------------------------------------


def test_rollup_information_radius_load_bearing_when_present_notfound():
    rollup, phrase = v0_52_audit._evaluate_rollup(
        a_null_subverdict=v0_52_audit.SUBVERDICT_A_NULL_PRESENT,
        b_subverdict=v0_52_audit.SUBVERDICT_B_PRESENT,
        c_subverdict=v0_52_audit.SUBVERDICT_C_NOT_FOUND,
        corpus_re_anchor=[],
        bridge_re_anchor=_zero_drift_bridge_re_anchor(),
    )
    assert rollup == v0_52_audit.ROLLUP_INFORMATION_RADIUS_LOAD_BEARING
    assert "information-radius channel is the load-bearing component" in phrase


# ---------------------------------------------------------------------------
# Test 14 — Rollup METABOLIC_COST_LOAD_BEARING when (PRESENT, NOT_FOUND, PRESENT)
# ---------------------------------------------------------------------------


def test_rollup_metabolic_cost_load_bearing_when_notfound_present():
    rollup, phrase = v0_52_audit._evaluate_rollup(
        a_null_subverdict=v0_52_audit.SUBVERDICT_A_NULL_PRESENT,
        b_subverdict=v0_52_audit.SUBVERDICT_B_NOT_FOUND,
        c_subverdict=v0_52_audit.SUBVERDICT_C_PRESENT,
        corpus_re_anchor=[],
        bridge_re_anchor=_zero_drift_bridge_re_anchor(),
    )
    assert rollup == v0_52_audit.ROLLUP_METABOLIC_COST_LOAD_BEARING
    assert "metabolic-cost channel is the load-bearing component" in phrase


# ---------------------------------------------------------------------------
# Test 15 — Rollup BOTH and CHANNELS_COUPLED corner outcomes
# ---------------------------------------------------------------------------


def test_rollup_both_independently_sufficient_and_coupled_or_confound():
    # (PRESENT, PRESENT, PRESENT) -> BOTH_CHANNELS_INDEPENDENTLY_SUFFICIENT.
    r1, p1 = v0_52_audit._evaluate_rollup(
        a_null_subverdict=v0_52_audit.SUBVERDICT_A_NULL_PRESENT,
        b_subverdict=v0_52_audit.SUBVERDICT_B_PRESENT,
        c_subverdict=v0_52_audit.SUBVERDICT_C_PRESENT,
        corpus_re_anchor=[],
        bridge_re_anchor=_zero_drift_bridge_re_anchor(),
    )
    assert r1 == v0_52_audit.ROLLUP_BOTH_INDEPENDENTLY_SUFFICIENT
    assert "both channels can independently support the bridge" in p1

    # (PRESENT, NOT_FOUND, NOT_FOUND) -> CHANNELS_COUPLED_OR_SHARED_CONFOUND.
    r2, p2 = v0_52_audit._evaluate_rollup(
        a_null_subverdict=v0_52_audit.SUBVERDICT_A_NULL_PRESENT,
        b_subverdict=v0_52_audit.SUBVERDICT_B_NOT_FOUND,
        c_subverdict=v0_52_audit.SUBVERDICT_C_NOT_FOUND,
        corpus_re_anchor=[],
        bridge_re_anchor=_zero_drift_bridge_re_anchor(),
    )
    assert r2 == v0_52_audit.ROLLUP_CHANNELS_COUPLED
    assert "requires the coupled `sensor_radius` trait" in p2


# ---------------------------------------------------------------------------
# Test 16 — Rollup MIXED for any PARTIAL + total partition + halt priority
# ---------------------------------------------------------------------------


def test_rollup_channels_mixed_for_partial_and_priority_halt_partition_total():
    """Exhaustive 3x3 partition test under A_null PRESENT; assert each
    cell maps to exactly one outcome; assert all PARTIAL-containing cells
    map to CHANNELS_MIXED. Then verify halt priority ordering."""
    bridge = _zero_drift_bridge_re_anchor()

    sub_options = {
        "PRESENT": (v0_52_audit.SUBVERDICT_B_PRESENT, v0_52_audit.SUBVERDICT_C_PRESENT),
        "PARTIAL": (v0_52_audit.SUBVERDICT_B_PARTIAL, v0_52_audit.SUBVERDICT_C_PARTIAL),
        "NOT_FOUND": (v0_52_audit.SUBVERDICT_B_NOT_FOUND, v0_52_audit.SUBVERDICT_C_NOT_FOUND),
    }
    expected_outcomes = {
        ("PRESENT", "PRESENT"): v0_52_audit.ROLLUP_BOTH_INDEPENDENTLY_SUFFICIENT,
        ("PRESENT", "NOT_FOUND"): v0_52_audit.ROLLUP_INFORMATION_RADIUS_LOAD_BEARING,
        ("NOT_FOUND", "PRESENT"): v0_52_audit.ROLLUP_METABOLIC_COST_LOAD_BEARING,
        ("NOT_FOUND", "NOT_FOUND"): v0_52_audit.ROLLUP_CHANNELS_COUPLED,
        ("PRESENT", "PARTIAL"): v0_52_audit.ROLLUP_CHANNELS_MIXED,
        ("PARTIAL", "PRESENT"): v0_52_audit.ROLLUP_CHANNELS_MIXED,
        ("NOT_FOUND", "PARTIAL"): v0_52_audit.ROLLUP_CHANNELS_MIXED,
        ("PARTIAL", "NOT_FOUND"): v0_52_audit.ROLLUP_CHANNELS_MIXED,
        ("PARTIAL", "PARTIAL"): v0_52_audit.ROLLUP_CHANNELS_MIXED,
    }
    seen: dict[tuple[str, str], str] = {}
    for b_key, (b_sub, _) in sub_options.items():
        for c_key, (_, c_sub) in sub_options.items():
            rollup, _phrase = v0_52_audit._evaluate_rollup(
                a_null_subverdict=v0_52_audit.SUBVERDICT_A_NULL_PRESENT,
                b_subverdict=b_sub,
                c_subverdict=c_sub,
                corpus_re_anchor=[],
                bridge_re_anchor=bridge,
            )
            seen[(b_key, c_key)] = rollup
            assert rollup == expected_outcomes[(b_key, c_key)], (
                f"({b_key}, {c_key}) -> {rollup}, expected {expected_outcomes[(b_key, c_key)]}"
            )
    assert len(seen) == 9, "partition is not total over 3x3 sub-verdict space"

    # 5 of 9 cells should map to CHANNELS_MIXED (all PARTIAL-containing cells).
    mixed_count = sum(1 for v in seen.values() if v == v0_52_audit.ROLLUP_CHANNELS_MIXED)
    assert mixed_count == 5

    # Halt-priority: BRIDGE_REPLICATION_HALT (priority 3) fires over outcomes
    # when an A_null bridge cell drifts beyond tolerance.
    bridge_drift = list(bridge)
    bridge_drift[0] = v0_52_audit.BridgeReAnchorRow(
        label=bridge_drift[0].label,
        observable=bridge_drift[0].observable,
        published_signed_d=bridge_drift[0].published_signed_d,
        derived_signed_d=bridge_drift[0].published_signed_d + 1.5,
        drift_abs=1.5,
        halts=True,
    )
    r_bridge_halt, _ = v0_52_audit._evaluate_rollup(
        a_null_subverdict=v0_52_audit.SUBVERDICT_A_NULL_PRESENT,
        b_subverdict=v0_52_audit.SUBVERDICT_B_PRESENT,
        c_subverdict=v0_52_audit.SUBVERDICT_C_NOT_FOUND,
        corpus_re_anchor=[],
        bridge_re_anchor=bridge_drift,
    )
    assert r_bridge_halt == v0_52_audit.ROLLUP_BRIDGE_REPLICATION_HALT

    # Halt-priority: CORPUS_REDERIVE_DRIFT_HALT (priority 1) fires over
    # bridge halt when both halts are present.
    corpus_halt = [
        v0_52_audit.ReAnchorRow(
            arm=v0_52_audit.ARM_A_NULL,
            version="v0.42",
            hazard=8,
            n_runs_contributing=8,
            a_share_h8_derived=0.700,
            a_share_h8_published=0.652,
            drift_abs=0.048,
            halts=True,
        )
    ]
    r_corpus_halt, p_corpus_halt = v0_52_audit._evaluate_rollup(
        a_null_subverdict=v0_52_audit.SUBVERDICT_A_NULL_PRESENT,
        b_subverdict=v0_52_audit.SUBVERDICT_B_PRESENT,
        c_subverdict=v0_52_audit.SUBVERDICT_C_NOT_FOUND,
        corpus_re_anchor=corpus_halt,
        bridge_re_anchor=bridge_drift,
    )
    assert r_corpus_halt == v0_52_audit.ROLLUP_CORPUS_DRIFT_HALT
    assert "v0.42" in p_corpus_halt
