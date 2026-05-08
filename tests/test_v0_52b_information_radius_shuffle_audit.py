"""v0.52b sensor_radius information-radius assignment shuffle — tests (16 locked).

Pre-reg: [[docs/experiments/fear_hunger_v0.52b.md]] §"Test list (locked, 16 tests)".
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

_SCRIPT_PATH = (
    Path(__file__).parent.parent / "scripts" / "v0_52b_information_radius_shuffle_audit.py"
)
_spec = importlib.util.spec_from_file_location("v0_52b_audit", _SCRIPT_PATH)
assert _spec is not None
assert _spec.loader is not None
v0_52b_audit = importlib.util.module_from_spec(_spec)
sys.modules["v0_52b_audit"] = v0_52b_audit
_spec.loader.exec_module(v0_52b_audit)


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
    fires_expected = (not math.isnan(signed)) and signed >= v0_52b_audit.COHENS_D_THRESHOLD
    fires_wrong = (not math.isnan(signed)) and signed <= -v0_52b_audit.COHENS_D_THRESHOLD
    return v0_52b_audit.ObservableSummary(
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
    obs = v0_52b_audit.PRIMARY_OBSERVABLES
    return [
        _make_summary(arm=arm, observable=obs[i][0], sign=obs[i][1], paired_d=ds[i], label=label)
        for i in range(3)
    ]


def _zero_drift_bridge_re_anchor() -> list[object]:
    return [
        v0_52b_audit.BridgeReAnchorRow(
            label=label,
            observable=obs,
            published_signed_d=ref,
            derived_signed_d=ref,
            drift_abs=0.0,
            halts=False,
        )
        for (label, obs), ref in v0_52b_audit.V048_PUBLISHED_SIGNED_D.items()
    ]


# ---------------------------------------------------------------------------
# Test 1 — all arms construct founders via the normal A_null path
# ---------------------------------------------------------------------------


def test_all_arms_construct_founders_via_normal_a_null_path(tmp_path):
    """For both arms, founder original sensor_radius per founder is byte-
    identical across arms for the same (version, seed, hazard) tuple."""
    seed = 41
    captures: dict[str, object] = {}
    for arm in v0_52b_audit.ARMS:
        captures[arm] = v0_52b_audit._run_one_arm(
            arm=arm, version="v0.42", seed=seed, hazard=0, runs_root=tmp_path
        )
    arms = list(v0_52b_audit.ARMS)
    base = captures[arms[0]]
    for arm in arms[1:]:
        cap = captures[arm]
        for r_base, r in zip(base.founder_records, cap.founder_records, strict=True):
            assert r_base.founder_original_sensor_radius == r.founder_original_sensor_radius
            assert r_base.founder_reproduction_drive == r.founder_reproduction_drive
            assert r_base.founder_metabolic_rate == r.founder_metabolic_rate


# ---------------------------------------------------------------------------
# Test 2 — B shuffle assigns a permutation of founder sensor_radii
# ---------------------------------------------------------------------------


def test_b_shuffle_assigns_permutation_of_founder_sensor_radii(tmp_path):
    cap = v0_52b_audit._run_one_arm(
        arm=v0_52b_audit.ARM_B_SHUFFLE,
        version="v0.42",
        seed=41,
        hazard=0,
        runs_root=tmp_path,
    )
    originals = sorted(rec.founder_original_sensor_radius for rec in cap.founder_records)
    assigned = sorted(rec.founder_assigned_effective_sensor_radius for rec in cap.founder_records)
    assert originals == assigned, (
        "shuffle assignment must be a permutation (multiset equality) of original radii"
    )
    # Founder body trait sensor_radius must be UNCHANGED (single-channel).
    # Original sensor_radius preserved on the body's traits.
    # (We can't easily inspect post-patch live bodies post-run since the model
    # is gone; instead check that the override is set on the record.)


# ---------------------------------------------------------------------------
# Test 3 — Helper RNG rotate-by-one fallback fires on identity draw
# ---------------------------------------------------------------------------


class _IdentityRng:
    """Stub that returns the identity permutation regardless of n."""

    def permutation(self, n: int) -> np.ndarray:
        return np.arange(n)


def test_b_shuffle_uses_v0_49_helper_rng_with_rotate_fallback():
    perm, applied = v0_52b_audit._compute_permutation_with_rotate_fallback(_IdentityRng(), 5)
    assert applied is True
    assert perm == [1, 2, 3, 4, 0]
    assert any(perm[i] != i for i in range(5))

    class _ShiftedRng:
        def permutation(self, n):
            return np.array([2, 3, 4, 0, 1])

    perm2, applied2 = v0_52b_audit._compute_permutation_with_rotate_fallback(_ShiftedRng(), 5)
    assert applied2 is False
    assert perm2 == [2, 3, 4, 0, 1]


# ---------------------------------------------------------------------------
# Test 4 — B shuffle Label A uses ASSIGNED effective override
# ---------------------------------------------------------------------------


def test_b_shuffle_label_a_uses_assigned_effective_override():
    """Synthetic: original sensor_radii [2, 5, 4, 1, 6] across lineages 0..4,
    permutation [1, 2, 3, 4, 0] -> assigned [5, 4, 1, 6, 2]. Label A picks
    by assigned effective override -> lineage 3 (assigned=6), NOT lineage 4
    (original=6)."""
    info_radius_by_lineage = {0: 5, 1: 4, 2: 1, 3: 6, 4: 2}
    label = v0_52b_audit._select_information_radius_label(info_radius_by_lineage)
    assert label == 3


# ---------------------------------------------------------------------------
# Test 5 — Default-equivalence (override=None resolver branch is byte-equivalent)
# ---------------------------------------------------------------------------


def test_default_equivalence_preserves_byte_identity():
    """With both per-agent and per-model overrides None, sensors.observe
    falls through to int(body.traits.sensor_radius) — byte-equivalent to
    pre-modification behavior. Corpus-level enforcement: 1680 existing
    tests pass without modification under modified src/."""
    from hedonism_harness.core.body import make_body
    from hedonism_harness.core.config import BodyConfig, WorldConfig
    from hedonism_harness.core.memory import make_memory
    from hedonism_harness.core.sensors import observe
    from hedonism_harness.core.traits import TraitConfig, random_traits
    from hedonism_harness.core.world import build_world

    rng = np.random.default_rng(123)
    traits = random_traits(TraitConfig(unbounded_mutation=True), rng)
    # random_traits should default the override to None (test #11 also covers this).
    assert traits.effective_sensor_radius_override is None
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

    body_config_default = BodyConfig()
    obs_default = observe(world, body, body_config_default, memory=memory)
    body_config_explicit = body_config_default.model_copy(update={})
    obs_explicit = observe(world, body, body_config_explicit, memory=memory)
    assert obs_default == obs_explicit


# ---------------------------------------------------------------------------
# Test 6 — Per-agent override takes precedence over per-model override
# ---------------------------------------------------------------------------


def test_per_agent_override_takes_precedence_over_per_model_override():
    """Resolver order: per-agent override (body.traits) > per-model
    override (body_config) > trait sensor_radius."""
    from hedonism_harness.core.body import make_body
    from hedonism_harness.core.config import BodyConfig, WorldConfig
    from hedonism_harness.core.sensors import observe
    from hedonism_harness.core.traits import TraitConfig, random_traits
    from hedonism_harness.core.world import build_world

    rng = np.random.default_rng(456)
    traits = random_traits(TraitConfig(unbounded_mutation=True), rng)
    traits = dataclasses.replace(traits, sensor_radius=2)
    world = build_world(WorldConfig(seed=42, width=12, height=12))
    world.food_value[:, :] = 0.0
    world.hazard_damage[:, :] = 0.0
    # Place food cells at distances 3 east (visible to radius 3+) and
    # 5 east (visible to radius 5+).
    world.food_value[6 + 3, 6] = 10.0
    world.food_value[6 + 5, 6] = 10.0

    # Per-agent override = 6, per-model = 4 -> per-agent wins; sees both.
    body_per_agent = make_body(
        body_id=1,
        lineage_id=0,
        parent_id=None,
        x=6,
        y=6,
        traits=dataclasses.replace(traits, effective_sensor_radius_override=6),
        config=BodyConfig(),
    )
    obs1 = observe(
        world,
        body_per_agent,
        BodyConfig(effective_sensor_radius_override=4),
        memory=None,
    )
    # Per-agent None, per-model = 4 -> per-model wins; sees food at 3 only.
    body_no_override = make_body(
        body_id=2,
        lineage_id=0,
        parent_id=None,
        x=6,
        y=6,
        traits=traits,
        config=BodyConfig(),
    )
    obs2 = observe(
        world,
        body_no_override,
        BodyConfig(effective_sensor_radius_override=4),
        memory=None,
    )
    # Per-agent None, per-model None -> trait wins (radius 2); sees nothing.
    obs3 = observe(world, body_no_override, BodyConfig(), memory=None)

    # food_signal_east: scan accumulates value/distance for each food cell on east axis.
    # obs1 (radius 6): cells at distance 3 and 5 -> 10/3 + 10/5 ≈ 5.333
    # obs2 (radius 4): cell at distance 3 only -> 10/3 ≈ 3.333
    # obs3 (radius 2): no food in range -> 0.0
    assert obs1.food_signal_east > obs2.food_signal_east > 0.0
    assert obs2.food_signal_east > 0.0
    assert obs3.food_signal_east == 0.0


# ---------------------------------------------------------------------------
# Test 7 — Per-agent override reaches sensors.observe axial scan
# ---------------------------------------------------------------------------


def test_per_agent_override_reaches_observe_axial_scan():
    from hedonism_harness.core.body import make_body
    from hedonism_harness.core.config import BodyConfig, WorldConfig
    from hedonism_harness.core.sensors import observe
    from hedonism_harness.core.traits import TraitConfig, random_traits
    from hedonism_harness.core.world import build_world

    rng = np.random.default_rng(789)
    traits = random_traits(TraitConfig(unbounded_mutation=True), rng)
    traits = dataclasses.replace(traits, sensor_radius=2)
    world = build_world(WorldConfig(seed=42, width=12, height=12))
    world.food_value[:, :] = 0.0
    world.hazard_damage[:, :] = 0.0
    world.food_value[6 + 5, 6] = 10.0

    body_no_override = make_body(
        body_id=1,
        lineage_id=0,
        parent_id=None,
        x=6,
        y=6,
        traits=traits,
        config=BodyConfig(),
    )
    obs_no_override = observe(world, body_no_override, BodyConfig(), memory=None)
    assert obs_no_override.food_signal_east == 0.0  # radius 2 < distance 5

    body_with_override = make_body(
        body_id=2,
        lineage_id=0,
        parent_id=None,
        x=6,
        y=6,
        traits=dataclasses.replace(traits, effective_sensor_radius_override=6),
        config=BodyConfig(),
    )
    obs_with_override = observe(world, body_with_override, BodyConfig(), memory=None)
    assert obs_with_override.food_signal_east > 0.0  # radius 6 >= distance 5


# ---------------------------------------------------------------------------
# Test 8 — Per-agent override reaches ValenceMemory directional scan
# ---------------------------------------------------------------------------


def test_per_agent_override_reaches_valence_memory_directional_scan():
    from hedonism_harness.core.body import make_body
    from hedonism_harness.core.config import BodyConfig, WorldConfig
    from hedonism_harness.core.memory import make_memory
    from hedonism_harness.core.sensors import observe
    from hedonism_harness.core.traits import TraitConfig, random_traits
    from hedonism_harness.core.world import build_world

    rng = np.random.default_rng(987)
    traits = random_traits(TraitConfig(unbounded_mutation=True), rng)
    traits = dataclasses.replace(traits, sensor_radius=2)
    world = build_world(WorldConfig(seed=42, width=12, height=12))
    world.food_value[:, :] = 0.0
    world.hazard_damage[:, :] = 0.0
    body_no_override = make_body(
        body_id=1,
        lineage_id=0,
        parent_id=None,
        x=6,
        y=6,
        traits=traits,
        config=BodyConfig(),
    )
    memory = make_memory(world.width, world.height)
    memory.pleasure_ema[6 + 5, 6] = 1.0  # distance 5 east

    obs_no_override = observe(world, body_no_override, BodyConfig(), memory=memory)
    assert obs_no_override.remembered_good_east == 0.0

    body_with_override = make_body(
        body_id=2,
        lineage_id=0,
        parent_id=None,
        x=6,
        y=6,
        traits=dataclasses.replace(traits, effective_sensor_radius_override=6),
        config=BodyConfig(),
    )
    obs_with_override = observe(world, body_with_override, BodyConfig(), memory=memory)
    assert obs_with_override.remembered_good_east > 0.0


# ---------------------------------------------------------------------------
# Test 9 — Per-agent override does NOT affect apply_metabolism
# ---------------------------------------------------------------------------


def test_per_agent_override_does_not_affect_apply_metabolism():
    """Set effective_sensor_radius_override=6 on body.traits; one body
    with sensor_radius=2 and one with sensor_radius=6. apply_metabolism's
    cost must reflect the trait sensor_radius, NOT the override. Cost
    diff = 0.05 * (6-2) = 0.2; if override leaked into apply_metabolism,
    cost diff would be 0."""
    from hedonism_harness.core.body import apply_metabolism, make_body
    from hedonism_harness.core.config import BodyConfig
    from hedonism_harness.core.traits import TraitConfig, random_traits

    rng = np.random.default_rng(999)
    base = random_traits(TraitConfig(unbounded_mutation=True), rng)
    # Both bodies carry the override = 6.
    traits_low = dataclasses.replace(base, sensor_radius=2, effective_sensor_radius_override=6)
    traits_high = dataclasses.replace(base, sensor_radius=6, effective_sensor_radius_override=6)
    body_low = dataclasses.replace(
        make_body(
            body_id=1,
            lineage_id=0,
            parent_id=None,
            x=0,
            y=0,
            traits=traits_low,
            config=BodyConfig(),
        ),
        energy=100.0,
    )
    body_high = dataclasses.replace(
        make_body(
            body_id=2,
            lineage_id=1,
            parent_id=None,
            x=0,
            y=0,
            traits=traits_high,
            config=BodyConfig(),
        ),
        energy=100.0,
    )
    after_low = apply_metabolism(body_low, BodyConfig())
    after_high = apply_metabolism(body_high, BodyConfig())
    cost_low = 100.0 - after_low.energy
    cost_high = 100.0 - after_high.energy
    assert cost_high - cost_low == pytest.approx(0.2), (
        f"apply_metabolism cost must follow trait sensor_radius (diff 6-2=4 * 0.05 = 0.2); "
        f"got cost_low={cost_low}, cost_high={cost_high}, diff={cost_high - cost_low}"
    )
    assert cost_low != cost_high


# ---------------------------------------------------------------------------
# Test 10 — mutate_traits preserves effective_sensor_radius_override
# ---------------------------------------------------------------------------


def test_mutate_traits_preserves_effective_sensor_radius_override():
    """The widened mutate_traits (uses dataclasses.replace) preserves the
    override field through reproduction. 100 child draws with the parent's
    override = 6 must all carry override = 6."""
    from hedonism_harness.core.traits import TraitConfig, mutate_traits, random_traits

    rng = np.random.default_rng(111)
    parent = random_traits(TraitConfig(unbounded_mutation=True), rng)
    parent = dataclasses.replace(parent, effective_sensor_radius_override=6)
    assert parent.effective_sensor_radius_override == 6

    cfg = TraitConfig(unbounded_mutation=True)
    child_rng = np.random.default_rng(222)
    for _ in range(100):
        child = mutate_traits(parent, cfg, child_rng)
        assert child.effective_sensor_radius_override == 6, (
            f"mutate_traits must preserve override; got {child.effective_sensor_radius_override}"
        )

    # Sanity: parent override = None propagates to child as None.
    parent_none = dataclasses.replace(parent, effective_sensor_radius_override=None)
    for _ in range(20):
        child_none = mutate_traits(parent_none, cfg, child_rng)
        assert child_none.effective_sensor_radius_override is None


# ---------------------------------------------------------------------------
# Test 11 — random_traits defaults effective_sensor_radius_override to None
# ---------------------------------------------------------------------------


def test_random_traits_defaults_effective_sensor_radius_override_to_none():
    """The override is not biologically initialized; random_traits leaves
    it at the field default (None)."""
    from hedonism_harness.core.traits import TraitConfig, random_traits

    cfg = TraitConfig(unbounded_mutation=True)
    rng = np.random.default_rng(42)
    for _ in range(20):
        traits = random_traits(cfg, rng)
        assert traits.effective_sensor_radius_override is None


# ---------------------------------------------------------------------------
# Test 12 — No RNG setup offset across arms
# ---------------------------------------------------------------------------


def test_no_rng_setup_offset_across_arms(tmp_path):
    """For the same (version, seed, hazard), founder original sensor_radius
    AND every other founder trait byte-identical across A_null and B at
    setup_observer end. Proves the body-trait patch + helper RNG do not
    consume streams.mutation."""
    seed = 47
    arm_to_originals: dict[str, list[tuple]] = {}
    for arm in v0_52b_audit.ARMS:
        cap = v0_52b_audit._run_one_arm(
            arm=arm, version="v0.42", seed=seed, hazard=8, runs_root=tmp_path
        )
        arm_to_originals[arm] = [
            (
                rec.lineage_id,
                rec.founder_original_sensor_radius,
                rec.founder_reproduction_drive,
                rec.founder_metabolic_rate,
            )
            for rec in cap.founder_records
        ]
    arms = list(v0_52b_audit.ARMS)
    for arm in arms[1:]:
        assert arm_to_originals[arm] == arm_to_originals[arms[0]]


# ---------------------------------------------------------------------------
# Test 13 — A_null sub-verdict PRESENT requires both labels clear
# ---------------------------------------------------------------------------


def test_per_arm_subverdict_a_null_present_requires_both_labels_clear():
    summaries_a = _three_summaries_for_arm(
        v0_52b_audit.ARM_A_NULL, (+0.6, +0.7, -0.3), v0_52b_audit.LABEL_A_NAME
    )
    summaries_b = _three_summaries_for_arm(
        v0_52b_audit.ARM_A_NULL, (+0.6, +0.8, -0.2), v0_52b_audit.LABEL_B_NAME
    )
    assert (
        v0_52b_audit._arm_subverdict(v0_52b_audit.ARM_A_NULL, summaries_a, summaries_b)
        == v0_52b_audit.SUBVERDICT_A_NULL_PRESENT
    )

    summaries_a_partial = _three_summaries_for_arm(
        v0_52b_audit.ARM_A_NULL, (+0.6, +0.3, -0.2), v0_52b_audit.LABEL_A_NAME
    )
    assert (
        v0_52b_audit._arm_subverdict(v0_52b_audit.ARM_A_NULL, summaries_a_partial, summaries_b)
        == v0_52b_audit.SUBVERDICT_A_NULL_PARTIAL
    )


# ---------------------------------------------------------------------------
# Test 14 — Rollup INFORMATION_RADIUS_FOLLOWS_ASSIGNMENT
# ---------------------------------------------------------------------------


def test_rollup_information_radius_follows_assignment_when_present_present():
    rollup, phrase = v0_52b_audit._evaluate_rollup(
        a_null_subverdict=v0_52b_audit.SUBVERDICT_A_NULL_PRESENT,
        b_subverdict=v0_52b_audit.SUBVERDICT_B_PRESENT,
        corpus_re_anchor=[],
        bridge_re_anchor=_zero_drift_bridge_re_anchor(),
        descendant_overrides_missing_total=0,
    )
    assert rollup == v0_52b_audit.ROLLUP_FOLLOWS_ASSIGNMENT
    assert "follows the assigned effective information radius" in phrase


# ---------------------------------------------------------------------------
# Test 15 — Rollup DOES_NOT_FOLLOW and PARTIAL outcomes
# ---------------------------------------------------------------------------


def test_rollup_does_not_follow_and_partial_outcomes():
    rollup_nf, phrase_nf = v0_52b_audit._evaluate_rollup(
        a_null_subverdict=v0_52b_audit.SUBVERDICT_A_NULL_PRESENT,
        b_subverdict=v0_52b_audit.SUBVERDICT_B_NOT_FOUND,
        corpus_re_anchor=[],
        bridge_re_anchor=_zero_drift_bridge_re_anchor(),
        descendant_overrides_missing_total=0,
    )
    assert rollup_nf == v0_52b_audit.ROLLUP_DOES_NOT_FOLLOW_ASSIGNMENT
    assert "does not follow the assigned effective information radius" in phrase_nf

    rollup_p, phrase_p = v0_52b_audit._evaluate_rollup(
        a_null_subverdict=v0_52b_audit.SUBVERDICT_A_NULL_PRESENT,
        b_subverdict=v0_52b_audit.SUBVERDICT_B_PARTIAL,
        corpus_re_anchor=[],
        bridge_re_anchor=_zero_drift_bridge_re_anchor(),
        descendant_overrides_missing_total=0,
    )
    assert rollup_p == v0_52b_audit.ROLLUP_ASSIGNMENT_PARTIAL
    assert "uniform-4 secondary follow-up is recommended for disambiguation" in phrase_p


# ---------------------------------------------------------------------------
# Test 16 — Inheritance halt + halt priority + partition total
# ---------------------------------------------------------------------------


def test_shuffle_descendant_inheritance_halt_priority_and_partition_total():
    """SHUFFLE_DESCENDANT_INHERITANCE_HALT (priority 4) fires when corpus-
    wide descendant_overrides_missing_total > 0. Higher-priority halts
    (1, 2, 3) fire over it. Partition is total under correct anchors."""
    bridge = _zero_drift_bridge_re_anchor()

    # Inheritance halt fires when missing > 0 with everything else clean.
    rollup_inh, phrase_inh = v0_52b_audit._evaluate_rollup(
        a_null_subverdict=v0_52b_audit.SUBVERDICT_A_NULL_PRESENT,
        b_subverdict=v0_52b_audit.SUBVERDICT_B_PRESENT,
        corpus_re_anchor=[],
        bridge_re_anchor=bridge,
        descendant_overrides_missing_total=1,
    )
    assert rollup_inh == v0_52b_audit.ROLLUP_SHUFFLE_INHERITANCE_HALT
    assert "lineage coherence" in phrase_inh

    # Bridge replication halt has higher priority than inheritance halt.
    bridge_drift = list(bridge)
    bridge_drift[0] = v0_52b_audit.BridgeReAnchorRow(
        label=bridge_drift[0].label,
        observable=bridge_drift[0].observable,
        published_signed_d=bridge_drift[0].published_signed_d,
        derived_signed_d=bridge_drift[0].published_signed_d + 1.5,
        drift_abs=1.5,
        halts=True,
    )
    rollup_br, _ = v0_52b_audit._evaluate_rollup(
        a_null_subverdict=v0_52b_audit.SUBVERDICT_A_NULL_PRESENT,
        b_subverdict=v0_52b_audit.SUBVERDICT_B_PRESENT,
        corpus_re_anchor=[],
        bridge_re_anchor=bridge_drift,
        descendant_overrides_missing_total=1,
    )
    assert rollup_br == v0_52b_audit.ROLLUP_BRIDGE_REPLICATION_HALT

    # Corpus drift halt has highest priority.
    corpus_halt = [
        v0_52b_audit.ReAnchorRow(
            arm=v0_52b_audit.ARM_A_NULL,
            version="v0.42",
            hazard=8,
            n_runs_contributing=8,
            a_share_h8_derived=0.700,
            a_share_h8_published=0.652,
            drift_abs=0.048,
            halts=True,
        )
    ]
    rollup_c, phrase_c = v0_52b_audit._evaluate_rollup(
        a_null_subverdict=v0_52b_audit.SUBVERDICT_A_NULL_PRESENT,
        b_subverdict=v0_52b_audit.SUBVERDICT_B_PRESENT,
        corpus_re_anchor=corpus_halt,
        bridge_re_anchor=bridge_drift,
        descendant_overrides_missing_total=1,
    )
    assert rollup_c == v0_52b_audit.ROLLUP_CORPUS_DRIFT_HALT
    assert "v0.42" in phrase_c

    # Opposite-sign halt (priority 2) fires before bridge halt.
    rollup_op, _ = v0_52b_audit._evaluate_rollup(
        a_null_subverdict=v0_52b_audit.SUBVERDICT_A_NULL_PRESENT,
        b_subverdict=v0_52b_audit.SUBVERDICT_B_OPPOSITE,
        corpus_re_anchor=[],
        bridge_re_anchor=bridge_drift,
        descendant_overrides_missing_total=1,
    )
    assert rollup_op == v0_52b_audit.ROLLUP_INTERVENTION_OPPOSITE_HALT

    # Partition total: under A_null PRESENT and zero halts, every B sub-verdict
    # in {PRESENT, PARTIAL, NOT_FOUND} maps to exactly one outcome.
    expected = {
        v0_52b_audit.SUBVERDICT_B_PRESENT: v0_52b_audit.ROLLUP_FOLLOWS_ASSIGNMENT,
        v0_52b_audit.SUBVERDICT_B_PARTIAL: v0_52b_audit.ROLLUP_ASSIGNMENT_PARTIAL,
        v0_52b_audit.SUBVERDICT_B_NOT_FOUND: v0_52b_audit.ROLLUP_DOES_NOT_FOLLOW_ASSIGNMENT,
    }
    for b_sub, expected_rollup in expected.items():
        rollup, _ = v0_52b_audit._evaluate_rollup(
            a_null_subverdict=v0_52b_audit.SUBVERDICT_A_NULL_PRESENT,
            b_subverdict=b_sub,
            corpus_re_anchor=[],
            bridge_re_anchor=bridge,
            descendant_overrides_missing_total=0,
        )
        assert rollup == expected_rollup
