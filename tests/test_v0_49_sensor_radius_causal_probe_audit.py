"""v0.49 sensor_radius causal probe — tests (16 locked).

Pre-reg: [[docs/experiments/fear_hunger_v0.49.md]] §"Test list (locked)".
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
    Path(__file__).parent.parent / "scripts" / "v0_49_sensor_radius_causal_probe_audit.py"
)
_spec = importlib.util.spec_from_file_location("v0_49_audit", _SCRIPT_PATH)
assert _spec is not None
assert _spec.loader is not None
v0_49_audit = importlib.util.module_from_spec(_spec)
sys.modules["v0_49_audit"] = v0_49_audit
_spec.loader.exec_module(v0_49_audit)


# ---------------------------------------------------------------------------
# Synthetic helpers
# ---------------------------------------------------------------------------


def _make_lineage_row(
    *,
    arm: str = v0_49_audit.ARM_A_NULL,
    version: str = "v0.42",
    seed: int = 41,
    hazard: int = 8,
    lineage_id: int,
    original_sensor_radius: int = 3,
    assigned_sensor_radius: int = 3,
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
    label_a_gating_valid: bool = True,
    label_a_degenerate_reason: str = "",
    effective_changed: int = 0,
) -> object:
    return v0_49_audit.PerLineageRow(
        arm=arm,
        version=version,
        seed=seed,
        hazard=hazard,
        run_id=f"{arm}-{version}-A_null-hzd{hazard}-seed-{seed}",
        lineage_id=lineage_id,
        original_sensor_radius=original_sensor_radius,
        assigned_sensor_radius=assigned_sensor_radius,
        intervention_delta=assigned_sensor_radius - original_sensor_radius,
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
        label_a_gating_valid=label_a_gating_valid,
        label_a_degenerate_reason=label_a_degenerate_reason,
        effective_sensor_radius_changed_count=effective_changed,
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
    fires_expected = (not math.isnan(signed)) and signed >= v0_49_audit.COHENS_D_THRESHOLD
    fires_wrong = (not math.isnan(signed)) and signed <= -v0_49_audit.COHENS_D_THRESHOLD
    return v0_49_audit.ObservableSummary(
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
    """Three primary-observable summaries with the given paired_d values
    (in PRIMARY_OBSERVABLES order; expected signs +, +, -)."""
    obs = v0_49_audit.PRIMARY_OBSERVABLES
    return [
        _make_summary(arm=arm, observable=obs[i][0], sign=obs[i][1], paired_d=ds[i], label=label)
        for i in range(3)
    ]


# ---------------------------------------------------------------------------
# Test 1 — all arms construct founders via the normal A_null path
# ---------------------------------------------------------------------------


def test_all_arms_construct_founders_via_normal_a_null_path(tmp_path):
    """Run all three arms for a single (version, seed, hazard) tuple and
    assert that ``original_sensor_radius`` per founder is identical across
    arms — proving every arm took the same model-side founder draw path
    (i.e., ``traits_override=None`` and no helper RNG consumption of
    ``streams.mutation``).
    """
    seed = 41
    captures: dict[str, object] = {}
    for arm in v0_49_audit.ARMS:
        cap = v0_49_audit._run_one_arm(
            arm=arm, version="v0.42", seed=seed, hazard=0, runs_root=tmp_path
        )
        captures[arm] = cap
    arms = list(v0_49_audit.ARMS)
    base = captures[arms[0]]
    for arm in arms[1:]:
        cap = captures[arm]
        for r_base, r in zip(base.founder_records, cap.founder_records, strict=True):
            assert r_base.original_sensor_radius == r.original_sensor_radius
            assert r_base.original_reproduction_drive == r.original_reproduction_drive
            assert r_base.original_metabolic_rate == r.original_metabolic_rate


# ---------------------------------------------------------------------------
# Test 2 — B clamp patch replaces only sensor_radius on live bodies
# ---------------------------------------------------------------------------


def test_b_clamp_patch_replaces_only_sensor_radius_on_live_bodies(tmp_path):
    cap = v0_49_audit._run_one_arm(
        arm=v0_49_audit.ARM_B_CLAMP_4,
        version="v0.42",
        seed=41,
        hazard=0,
        runs_root=tmp_path,
    )
    for rec in cap.founder_records:
        assert rec.assigned_sensor_radius == v0_49_audit.CLAMP_VALUE
    # All assigned == 4; original may differ. Effective changed count should be
    # the number of founders whose original draw was != 4.
    expected_changed = sum(
        1 for rec in cap.founder_records if rec.original_sensor_radius != v0_49_audit.CLAMP_VALUE
    )
    assert cap.effective_sensor_radius_changed_count == expected_changed


# ---------------------------------------------------------------------------
# Test 3 — A_null streams.mutation byte-identical across arms
# ---------------------------------------------------------------------------


def test_a_null_arm_streams_mutation_state_byte_identical_across_arms(tmp_path):
    """The intervention patch never consumes ``streams.mutation``. Therefore
    founder draws (and thus per-agent RNG seeds and downstream mutation
    bytes) must be identical across all three arms for the same seed.

    Verified behaviorally: original founder traits (full Traits records)
    captured at setup_observer time are byte-identical across arms.
    """
    seed = 41
    arm_to_originals: dict[str, list[object]] = {}
    for arm in v0_49_audit.ARMS:
        cap = v0_49_audit._run_one_arm(
            arm=arm, version="v0.42", seed=seed, hazard=8, runs_root=tmp_path
        )
        arm_to_originals[arm] = [
            (
                rec.lineage_id,
                rec.original_sensor_radius,
                rec.original_reproduction_drive,
                rec.original_metabolic_rate,
            )
            for rec in cap.founder_records
        ]
    arms = list(v0_49_audit.ARMS)
    for arm in arms[1:]:
        assert arm_to_originals[arm] == arm_to_originals[arms[0]]


# ---------------------------------------------------------------------------
# Test 4 — C permutation rotate-by-one fallback fires on identity draw
# ---------------------------------------------------------------------------


class _IdentityRng:
    """Stub that returns the identity permutation regardless of n."""

    def permutation(self, n: int) -> np.ndarray:
        return np.arange(n)


def test_c_permutation_is_non_identity():
    perm, applied = v0_49_audit._compute_permutation_with_rotate_fallback(_IdentityRng(), 5)
    assert applied is True
    assert perm == [1, 2, 3, 4, 0]
    # Verify non-identity element exists.
    assert any(perm[i] != i for i in range(5))

    # Sanity: a non-identity draw passes through unchanged.
    class _ShiftedRng:
        def permutation(self, n):
            return np.array([2, 3, 4, 0, 1])

    perm2, applied2 = v0_49_audit._compute_permutation_with_rotate_fallback(_ShiftedRng(), 5)
    assert applied2 is False
    assert perm2 == [2, 3, 4, 0, 1]


# ---------------------------------------------------------------------------
# Test 5 — C permutation patch replaces only sensor_radius on live bodies
# ---------------------------------------------------------------------------


def test_c_permutation_patch_replaces_only_sensor_radius_on_live_bodies(tmp_path):
    cap = v0_49_audit._run_one_arm(
        arm=v0_49_audit.ARM_C_PERMUTATION,
        version="v0.42",
        seed=41,
        hazard=0,
        runs_root=tmp_path,
    )
    # Assigned set is a permutation of original set (multiset equality).
    originals = sorted(rec.original_sensor_radius for rec in cap.founder_records)
    assigned = sorted(rec.assigned_sensor_radius for rec in cap.founder_records)
    assert originals == assigned


# ---------------------------------------------------------------------------
# Test 6 — C label A uses assigned sensor_radius (not original)
# ---------------------------------------------------------------------------


def test_c_permutation_label_a_uses_assigned_sensor_radius():
    """Synthetic: original sensor_radius = [2, 5, 4, 1, 6] across lineages
    0..4. Permutation = [1, 2, 3, 4, 0] -> assigned = [5, 4, 1, 6, 2].
    Label A must pick lineage 3 (highest assigned = 6), NOT lineage 4
    (highest original = 6)."""
    assigned_by_lineage = {0: 5, 1: 4, 2: 1, 3: 6, 4: 2}
    label = v0_49_audit._select_sensor_radius_label(assigned_by_lineage)
    assert label == 3


# ---------------------------------------------------------------------------
# Test 7 — Label A under B_clamp is diagnostic-only (CSV flag false)
# ---------------------------------------------------------------------------


def test_b_clamp_label_a_is_diagnostic_only_with_csv_flag():
    rows = [
        _make_lineage_row(
            arm=v0_49_audit.ARM_B_CLAMP_4,
            lineage_id=lid,
            original_sensor_radius=3,
            assigned_sensor_radius=v0_49_audit.CLAMP_VALUE,
            label_a_gating_valid=False,
            label_a_degenerate_reason="all founders assigned sensor_radius=4",
        )
        for lid in range(5)
    ]
    for r in rows:
        assert r.label_a_gating_valid is False
        assert r.label_a_degenerate_reason == "all founders assigned sensor_radius=4"

    # The B-arm sub-verdict consults Label B only.
    summaries_a = _three_summaries_for_arm(
        v0_49_audit.ARM_B_CLAMP_4, (+0.1, +0.1, +0.1), v0_49_audit.LABEL_A_NAME
    )
    summaries_b = _three_summaries_for_arm(
        v0_49_audit.ARM_B_CLAMP_4, (+0.6, +0.7, -0.6), v0_49_audit.LABEL_B_NAME
    )
    sub = v0_49_audit._arm_subverdict(v0_49_audit.ARM_B_CLAMP_4, summaries_a, summaries_b)
    # Even though label A's signed_d is uniformly +0.1 (would not clear),
    # the sub-verdict is determined by label B alone -> label B clears 3/3 -> PRESENT.
    assert sub == v0_49_audit.SUBVERDICT_B_CLAMP_PRESENT


# ---------------------------------------------------------------------------
# Test 8 — A_null sub-verdict PRESENT requires both labels clear ≥ 2/3
# ---------------------------------------------------------------------------


def test_per_arm_subverdict_a_null_present_requires_both_labels_clear():
    summaries_a = _three_summaries_for_arm(
        v0_49_audit.ARM_A_NULL, (+0.6, +0.7, -0.3), v0_49_audit.LABEL_A_NAME
    )
    summaries_b = _three_summaries_for_arm(
        v0_49_audit.ARM_A_NULL, (+0.6, +0.8, -0.2), v0_49_audit.LABEL_B_NAME
    )
    sub = v0_49_audit._arm_subverdict(v0_49_audit.ARM_A_NULL, summaries_a, summaries_b)
    assert sub == v0_49_audit.SUBVERDICT_A_NULL_PRESENT


# ---------------------------------------------------------------------------
# Test 9 — B_clamp PRESENT requires Label B clears ≥ 2/3 (Label A ignored)
# ---------------------------------------------------------------------------


def test_per_arm_subverdict_b_clamp_present_requires_label_b_only():
    # Label A trivially zero (B's degenerate state).
    summaries_a = _three_summaries_for_arm(
        v0_49_audit.ARM_B_CLAMP_4, (0.0, 0.0, 0.0), v0_49_audit.LABEL_A_NAME
    )
    summaries_b = _three_summaries_for_arm(
        v0_49_audit.ARM_B_CLAMP_4, (+0.6, +0.7, -0.6), v0_49_audit.LABEL_B_NAME
    )
    sub = v0_49_audit._arm_subverdict(v0_49_audit.ARM_B_CLAMP_4, summaries_a, summaries_b)
    assert sub == v0_49_audit.SUBVERDICT_B_CLAMP_PRESENT


# ---------------------------------------------------------------------------
# Test 10 — C_perm PARTIAL when only one label clears
# ---------------------------------------------------------------------------


def test_per_arm_subverdict_c_perm_partial_when_only_one_label_clears():
    summaries_a = _three_summaries_for_arm(
        v0_49_audit.ARM_C_PERMUTATION, (+0.6, +0.7, -0.6), v0_49_audit.LABEL_A_NAME
    )
    summaries_b = _three_summaries_for_arm(
        v0_49_audit.ARM_C_PERMUTATION, (+0.6, +0.3, -0.2), v0_49_audit.LABEL_B_NAME
    )
    sub = v0_49_audit._arm_subverdict(v0_49_audit.ARM_C_PERMUTATION, summaries_a, summaries_b)
    assert sub == v0_49_audit.SUBVERDICT_C_PERM_PARTIAL


# ---------------------------------------------------------------------------
# Test 11 — Rollup SUPPORTED: A_null PRESENT, B NOT_FOUND, C PRESENT
# ---------------------------------------------------------------------------


def test_rollup_supported_when_a_null_present_b_not_found_c_present():
    bridge_re_anchor = [
        v0_49_audit.BridgeReAnchorRow(
            label=label,
            observable=obs,
            published_signed_d=ref,
            derived_signed_d=ref,
            drift_abs=0.0,
            halts=False,
        )
        for (label, obs), ref in v0_49_audit.V048_PUBLISHED_SIGNED_D.items()
    ]
    rollup, phrase = v0_49_audit._evaluate_rollup(
        a_null_subverdict=v0_49_audit.SUBVERDICT_A_NULL_PRESENT,
        b_clamp_subverdict=v0_49_audit.SUBVERDICT_B_CLAMP_NOT_FOUND,
        c_perm_subverdict=v0_49_audit.SUBVERDICT_C_PERM_PRESENT,
        corpus_re_anchor=[],
        bridge_re_anchor=bridge_re_anchor,
    )
    assert rollup == v0_49_audit.ROLLUP_CAUSAL_SUPPORTED
    assert "supports a causal contribution" in phrase


# ---------------------------------------------------------------------------
# Test 12 — Rollup NOT_SUPPORTED: A_null PRESENT, B PRESENT, C NOT_FOUND
# ---------------------------------------------------------------------------


def test_rollup_not_supported_when_a_null_present_b_present_c_not_found():
    bridge_re_anchor = [
        v0_49_audit.BridgeReAnchorRow(
            label=label,
            observable=obs,
            published_signed_d=ref,
            derived_signed_d=ref,
            drift_abs=0.0,
            halts=False,
        )
        for (label, obs), ref in v0_49_audit.V048_PUBLISHED_SIGNED_D.items()
    ]
    rollup, phrase = v0_49_audit._evaluate_rollup(
        a_null_subverdict=v0_49_audit.SUBVERDICT_A_NULL_PRESENT,
        b_clamp_subverdict=v0_49_audit.SUBVERDICT_B_CLAMP_PRESENT,
        c_perm_subverdict=v0_49_audit.SUBVERDICT_C_PERM_NOT_FOUND,
        corpus_re_anchor=[],
        bridge_re_anchor=bridge_re_anchor,
    )
    assert rollup == v0_49_audit.ROLLUP_CAUSAL_NOT_SUPPORTED
    assert "is not supported as a causal contributor" in phrase


# ---------------------------------------------------------------------------
# Test 13 — Rollup MIXED for other non-halt combinations
# ---------------------------------------------------------------------------


def test_rollup_mixed_for_other_non_halt_combinations():
    bridge_re_anchor = [
        v0_49_audit.BridgeReAnchorRow(
            label=label,
            observable=obs,
            published_signed_d=ref,
            derived_signed_d=ref,
            drift_abs=0.0,
            halts=False,
        )
        for (label, obs), ref in v0_49_audit.V048_PUBLISHED_SIGNED_D.items()
    ]
    # All three PRESENT -> MIXED (bridge fires regardless of intervention).
    rollup, phrase = v0_49_audit._evaluate_rollup(
        a_null_subverdict=v0_49_audit.SUBVERDICT_A_NULL_PRESENT,
        b_clamp_subverdict=v0_49_audit.SUBVERDICT_B_CLAMP_PRESENT,
        c_perm_subverdict=v0_49_audit.SUBVERDICT_C_PERM_PRESENT,
        corpus_re_anchor=[],
        bridge_re_anchor=bridge_re_anchor,
    )
    assert rollup == v0_49_audit.ROLLUP_CAUSAL_MIXED
    assert "mixed evidence" in phrase


# ---------------------------------------------------------------------------
# Test 14 — Bridge replication halt on signed_d drift
# ---------------------------------------------------------------------------


def test_bridge_replication_halt_on_signed_d_drift():
    # One bridge cell drifts beyond tolerance (+1.5 vs published +1.066).
    bridge_re_anchor = []
    for (label, obs), ref in v0_49_audit.V048_PUBLISHED_SIGNED_D.items():
        if label == v0_49_audit.LABEL_A_NAME and obs == "pre50_food_events_count":
            derived = ref + 1.5  # large drift
            drift = abs(derived - ref)
            halts = drift > v0_49_audit.RE_ANCHOR_DRIFT_TOLERANCE
        else:
            derived = ref
            drift = 0.0
            halts = False
        bridge_re_anchor.append(
            v0_49_audit.BridgeReAnchorRow(
                label=label,
                observable=obs,
                published_signed_d=ref,
                derived_signed_d=derived,
                drift_abs=drift,
                halts=halts,
            )
        )
    rollup, phrase = v0_49_audit._evaluate_rollup(
        a_null_subverdict=v0_49_audit.SUBVERDICT_A_NULL_PRESENT,
        b_clamp_subverdict=v0_49_audit.SUBVERDICT_B_CLAMP_NOT_FOUND,
        c_perm_subverdict=v0_49_audit.SUBVERDICT_C_PERM_PRESENT,
        corpus_re_anchor=[],
        bridge_re_anchor=bridge_re_anchor,
    )
    assert rollup == v0_49_audit.ROLLUP_BRIDGE_REPLICATION_HALT
    assert "does not reproduce v0.48's spatial bridge" in phrase


# ---------------------------------------------------------------------------
# Test 15 — Bridge replication halt on A_null sub-verdict PARTIAL
# ---------------------------------------------------------------------------


def test_bridge_replication_halt_on_a_null_subverdict_partial():
    # All cells within tolerance, but A_null sub-verdict is PARTIAL.
    bridge_re_anchor = [
        v0_49_audit.BridgeReAnchorRow(
            label=label,
            observable=obs,
            published_signed_d=ref,
            derived_signed_d=ref,
            drift_abs=0.0,
            halts=False,
        )
        for (label, obs), ref in v0_49_audit.V048_PUBLISHED_SIGNED_D.items()
    ]
    rollup, _phrase = v0_49_audit._evaluate_rollup(
        a_null_subverdict=v0_49_audit.SUBVERDICT_A_NULL_PARTIAL,
        b_clamp_subverdict=v0_49_audit.SUBVERDICT_B_CLAMP_PRESENT,
        c_perm_subverdict=v0_49_audit.SUBVERDICT_C_PERM_PRESENT,
        corpus_re_anchor=[],
        bridge_re_anchor=bridge_re_anchor,
    )
    assert rollup == v0_49_audit.ROLLUP_BRIDGE_REPLICATION_HALT


# ---------------------------------------------------------------------------
# Test 16 — Corpus drift halt has priority over bridge replication halt
# ---------------------------------------------------------------------------


def test_corpus_rederive_drift_halt_priority_over_bridge_replication_halt():
    # Both: corpus drift on v0.42 A_null arm AND bridge cell drift.
    corpus_re_anchor = [
        v0_49_audit.ReAnchorRow(
            arm=v0_49_audit.ARM_A_NULL,
            version="v0.42",
            hazard=8,
            n_runs_contributing=8,
            a_share_h8_derived=0.700,
            a_share_h8_published=0.652,
            drift_abs=0.048,
            halts=True,
        )
    ]
    bridge_re_anchor = [
        v0_49_audit.BridgeReAnchorRow(
            label=label,
            observable=obs,
            published_signed_d=ref,
            derived_signed_d=ref + 1.0,  # large drift
            drift_abs=1.0,
            halts=True,
        )
        for (label, obs), ref in v0_49_audit.V048_PUBLISHED_SIGNED_D.items()
    ]
    rollup, phrase = v0_49_audit._evaluate_rollup(
        a_null_subverdict=v0_49_audit.SUBVERDICT_A_NULL_PRESENT,
        b_clamp_subverdict=v0_49_audit.SUBVERDICT_B_CLAMP_NOT_FOUND,
        c_perm_subverdict=v0_49_audit.SUBVERDICT_C_PERM_PRESENT,
        corpus_re_anchor=corpus_re_anchor,
        bridge_re_anchor=bridge_re_anchor,
    )
    assert rollup == v0_49_audit.ROLLUP_CORPUS_DRIFT_HALT
    assert "v0.42" in phrase


# ---------------------------------------------------------------------------
# Bonus — single-channel invariant raises loud on tampered Traits
# ---------------------------------------------------------------------------


def test_single_channel_invariant_raises_when_non_sensor_field_changes():
    """Defensive: if a future code path accidentally mutates a non-
    sensor_radius field, _assert_single_channel_invariant must halt loud."""
    cap_v042_arm = v0_49_audit._select_a_null_arm("v0.42", 0)
    # Build a synthetic Traits via the trait config used by the arm; we just
    # need any two Traits instances to compare.
    from hedonism_harness.core.traits import TraitConfig, random_traits

    rng = np.random.default_rng(123)
    cfg = TraitConfig(unbounded_mutation=True)
    original = random_traits(cfg, rng)
    tampered = dataclasses.replace(
        original,
        sensor_radius=4,
        metabolic_rate=original.metabolic_rate + 0.1,  # second field changes too
    )
    with pytest.raises(v0_49_audit.V049ReducerError, match="single-channel invariant violated"):
        v0_49_audit._assert_single_channel_invariant(
            original, tampered, v0_49_audit.ARM_B_CLAMP_4, lineage_id=0
        )
    # Sanity: arm name appears in unused-but-required handle.
    _ = cap_v042_arm
