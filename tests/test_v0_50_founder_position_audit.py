"""v0.50 founder-position confound probe — tests (16 locked).

Pre-reg: [[docs/experiments/fear_hunger_v0.50.md]] §"Test list (locked)".
Tests numbered to match the pre-reg's ordering.
"""

from __future__ import annotations

import importlib.util
import math
import sys
from pathlib import Path

import numpy as np

_SCRIPT_PATH = Path(__file__).parent.parent / "scripts" / "v0_50_founder_position_audit.py"
_spec = importlib.util.spec_from_file_location("v0_50_audit", _SCRIPT_PATH)
assert _spec is not None
assert _spec.loader is not None
v0_50_audit = importlib.util.module_from_spec(_spec)
sys.modules["v0_50_audit"] = v0_50_audit
_spec.loader.exec_module(v0_50_audit)


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
    fires_expected = (not math.isnan(signed)) and signed >= v0_50_audit.COHENS_D_THRESHOLD
    fires_wrong = (not math.isnan(signed)) and signed <= -v0_50_audit.COHENS_D_THRESHOLD
    return v0_50_audit.ObservableSummary(
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
    """Three summaries with the given paired_d values, in PRIMARY_OBSERVABLES order."""
    obs = v0_50_audit.PRIMARY_OBSERVABLES
    return [
        _make_summary(arm=arm, observable=obs[i][0], sign=obs[i][1], paired_d=ds[i], label=label)
        for i in range(3)
    ]


def _arm_subverdict_for_pattern(
    arm: str, ds_a: tuple[float, float, float], ds_b: tuple[float, float, float]
) -> str:
    """Helper: compute sub-verdict from two (3-tuple) signed_d patterns."""
    sa = _three_summaries_for_arm(arm, ds_a, v0_50_audit.LABEL_A_NAME)
    sb = _three_summaries_for_arm(arm, ds_b, v0_50_audit.LABEL_B_NAME)
    return v0_50_audit._arm_subverdict(arm, sa, sb)


def _bridge_anchor_clean() -> list[object]:
    return [
        v0_50_audit.BridgeReAnchorRow(
            label=label,
            observable=obs,
            published_signed_d=ref,
            derived_signed_d=ref,
            drift_abs=0.0,
            halts=False,
        )
        for (label, obs), ref in v0_50_audit.V048_PUBLISHED_SIGNED_D.items()
    ]


def _present_pattern_a() -> tuple[float, float, float]:
    """3 primaries firing under label A (signed_d's well above +0.5)."""
    return (+0.7, +0.7, -0.7)  # signs are +, +, -; signed_d's = +0.7, +0.7, +0.7


def _present_pattern_b() -> tuple[float, float, float]:
    """3 primaries firing under label B."""
    return (+0.6, +0.6, -0.6)


def _not_found_pattern_a() -> tuple[float, float, float]:
    """0/3 firing, no wrong-sign."""
    return (+0.2, +0.2, -0.2)


def _not_found_pattern_b() -> tuple[float, float, float]:
    return (+0.1, +0.1, -0.1)


def _partial_pattern_a() -> tuple[float, float, float]:
    """1/3 firing, no wrong-sign."""
    return (+0.7, +0.2, -0.1)


# ---------------------------------------------------------------------------
# Test 1 — all arms construct founders via the normal A_null path
# ---------------------------------------------------------------------------


def test_all_arms_construct_founders_via_normal_a_null_path(tmp_path):
    """Run all three arms for a single (version, seed, hazard) tuple and
    assert that ``original_x`` / ``original_y`` per founder is identical
    across arms — proving every arm took the same model-side founder
    placement path (no traits_override; no helper-RNG consumption of
    streams.mutation).
    """
    seed = 41
    captures: dict[str, object] = {}
    for arm in v0_50_audit.ARMS:
        cap = v0_50_audit._run_one_arm(
            arm=arm, version="v0.42", seed=seed, hazard=0, runs_root=tmp_path
        )
        captures[arm] = cap
    arms = list(v0_50_audit.ARMS)
    base = captures[arms[0]]
    for arm in arms[1:]:
        cap = captures[arm]
        for r_base, r in zip(base.founder_records, cap.founder_records, strict=True):
            assert r_base.original_x == r.original_x
            assert r_base.original_y == r.original_y


# ---------------------------------------------------------------------------
# Test 2 — B shifted_top patch replaces only x/y on live bodies
# ---------------------------------------------------------------------------


def test_b_shifted_top_patch_replaces_only_x_y_on_live_bodies(tmp_path):
    cap = v0_50_audit._run_one_arm(
        arm=v0_50_audit.ARM_B_SHIFTED_TOP,
        version="v0.42",
        seed=41,
        hazard=0,
        runs_root=tmp_path,
    )
    # All assigned positions match the locked shifted-top band [1,2,3,4,5] at spawn_x.
    for rec in cap.founder_records:
        # founder_index corresponds to position in the shifted_y band.
        assert rec.assigned_y == v0_50_audit.B_SHIFTED_TOP_Y[rec.founder_index]
    # All 5 founders share spawn_x; assigned_x equals original_x for every founder.
    for rec in cap.founder_records:
        assert rec.assigned_x == rec.original_x


# ---------------------------------------------------------------------------
# Test 3 — A_null streams.mutation byte-identical across arms (same founder traits)
# ---------------------------------------------------------------------------


def test_a_null_arm_streams_mutation_state_byte_identical_across_arms(tmp_path):
    """The intervention patch never consumes streams.mutation, so founder
    Traits captured at setup_observer time are byte-identical across arms
    for the same seed."""
    seed = 41
    arm_to_traits: dict[str, list[tuple[float, ...]]] = {}
    for arm in v0_50_audit.ARMS:
        cap = v0_50_audit._run_one_arm(
            arm=arm, version="v0.42", seed=seed, hazard=8, runs_root=tmp_path
        )
        arm_to_traits[arm] = sorted(
            (
                lid,
                t["sensor_radius"],
                t["reproduction_drive"],
                t["metabolic_rate"],
            )
            for lid, t in cap.founder_traits_by_lineage.items()
        )
    arms = list(v0_50_audit.ARMS)
    for arm in arms[1:]:
        assert arm_to_traits[arm] == arm_to_traits[arms[0]]


# ---------------------------------------------------------------------------
# Test 4 — C position permutation rotate-by-one fallback fires on identity draw
# ---------------------------------------------------------------------------


class _IdentityRng:
    """Stub that returns the identity permutation regardless of n."""

    def permutation(self, n: int) -> np.ndarray:
        return np.arange(n)


def test_c_position_permutation_is_non_identity():
    perm, applied = v0_50_audit._compute_permutation_with_rotate_fallback(_IdentityRng(), 5)
    assert applied is True
    assert perm == [1, 2, 3, 4, 0]
    # Verify non-identity element exists.
    assert any(perm[i] != i for i in range(5))


# ---------------------------------------------------------------------------
# Test 5 — C position patch replaces only x/y; assigned set is permutation of original
# ---------------------------------------------------------------------------


def test_c_position_patch_replaces_only_x_y_on_live_bodies(tmp_path):
    cap = v0_50_audit._run_one_arm(
        arm=v0_50_audit.ARM_C_PERMUTATION,
        version="v0.42",
        seed=41,
        hazard=0,
        runs_root=tmp_path,
    )
    originals = sorted((rec.original_x, rec.original_y) for rec in cap.founder_records)
    assigned = sorted((rec.assigned_x, rec.assigned_y) for rec in cap.founder_records)
    # Multiset equality: assigned positions are a permutation of originals.
    assert originals == assigned


# ---------------------------------------------------------------------------
# Test 6 — B shifted_top band is reflection of V0_25's band
# ---------------------------------------------------------------------------


def test_b_shifted_top_band_is_top_shifted_reflection_of_v025():
    """For tight_gradient (height=6), assert B's shifted_y = [1,2,3,4,5]
    (mean 3.0; lineage 4 at the top edge y=5) vs V0_25's [0,1,2,3,4]
    (mean 2.0; lineage 0 at the bottom edge y=0). Neither is centered
    on the geometric mid-row y=2.5."""
    assert v0_50_audit.B_SHIFTED_TOP_Y == (1, 2, 3, 4, 5)
    shifted = v0_50_audit.B_SHIFTED_TOP_Y
    v025 = (0, 1, 2, 3, 4)
    assert sum(shifted) / 5 == 3.0
    assert sum(v025) / 5 == 2.0
    # Reflection: lineage 0 at bottom edge under V0_25; lineage 4 at top edge under B.
    assert v025[0] == 0  # bottom edge
    assert shifted[-1] == 5  # top edge (height-1)


# ---------------------------------------------------------------------------
# Test 7 — capacity-1 invariant preserved after patch
# ---------------------------------------------------------------------------


def test_capacity_1_invariant_preserved_after_patch(tmp_path):
    """Under B and C, all 5 patched cells are pairwise distinct."""
    for arm in (v0_50_audit.ARM_B_SHIFTED_TOP, v0_50_audit.ARM_C_PERMUTATION):
        cap = v0_50_audit._run_one_arm(
            arm=arm, version="v0.42", seed=41, hazard=0, runs_root=tmp_path
        )
        assigned = [(rec.assigned_x, rec.assigned_y) for rec in cap.founder_records]
        assert len(set(assigned)) == 5, f"arm {arm} produced duplicate cells: {assigned}"


# ---------------------------------------------------------------------------
# Test 8 — Mesa cell pointer aligned after patch (verified via tick-0 snapshot)
# ---------------------------------------------------------------------------


def test_mesa_cell_pointer_aligned_after_patch(tmp_path):
    """The tick-0 snapshot reads agent.body.x / agent.body.y. After the
    patch, the snapshot must reflect the assigned positions, proving the
    cell pointer was updated in lockstep with body coordinates (otherwise
    the simulation would reconcile them in step 1, but the tick-0 snapshot
    would still show the patched coords).
    """
    cap = v0_50_audit._run_one_arm(
        arm=v0_50_audit.ARM_B_SHIFTED_TOP,
        version="v0.42",
        seed=41,
        hazard=0,
        runs_root=tmp_path,
    )
    tick0 = cap.tick_records[0]
    snapshot_xy = sorted((row[2], row[3]) for row in tick0.agents)
    expected_xy = sorted((rec.assigned_x, rec.assigned_y) for rec in cap.founder_records)
    assert snapshot_xy == expected_xy


# ---------------------------------------------------------------------------
# Test 9 — A_null sub-verdict PRESENT requires both labels clear
# ---------------------------------------------------------------------------


def test_per_arm_subverdict_a_null_present_requires_both_labels_clear():
    sub = _arm_subverdict_for_pattern(
        v0_50_audit.ARM_A_NULL,
        ds_a=(+0.6, +0.7, -0.6),  # signed_d's = +0.6, +0.7, +0.6 -> 3/3 fire
        ds_b=(+0.6, +0.8, -0.6),  # 3/3 fire
    )
    assert sub == v0_50_audit.SUBVERDICT_A_NULL_PRESENT


# ---------------------------------------------------------------------------
# Test 10 — B shifted_top sub-verdict PARTIAL when only one label clears
# ---------------------------------------------------------------------------


def test_per_arm_subverdict_b_shifted_top_partial_when_only_one_label_clears():
    sub = _arm_subverdict_for_pattern(
        v0_50_audit.ARM_B_SHIFTED_TOP,
        ds_a=(+0.6, +0.7, -0.6),  # 3/3 fire
        ds_b=(+0.6, +0.2, -0.1),  # 1/3 fire
    )
    assert sub == v0_50_audit.SUBVERDICT_B_SHIFTED_PARTIAL


# ---------------------------------------------------------------------------
# Test 11 — Rollup ROBUST: A_null PRESENT, B PRESENT, C PRESENT
# ---------------------------------------------------------------------------


def test_rollup_robust_when_all_three_arms_present():
    rollup, phrase = v0_50_audit._evaluate_rollup(
        a_null_subverdict=v0_50_audit.SUBVERDICT_A_NULL_PRESENT,
        b_subverdict=v0_50_audit.SUBVERDICT_B_SHIFTED_PRESENT,
        c_subverdict=v0_50_audit.SUBVERDICT_C_PERM_PRESENT,
        corpus_re_anchor=[],
        bridge_re_anchor=_bridge_anchor_clean(),
    )
    assert rollup == v0_50_audit.ROLLUP_ROBUST
    assert "survives founder-position controls" in phrase


# ---------------------------------------------------------------------------
# Test 12 — Rollup SUPPORTED when both B and C weaken (4 combinations)
# ---------------------------------------------------------------------------


def test_rollup_supported_when_both_b_and_c_weaken():
    weakened_b = (
        v0_50_audit.SUBVERDICT_B_SHIFTED_PARTIAL,
        v0_50_audit.SUBVERDICT_B_SHIFTED_NOT_FOUND,
    )
    weakened_c = (
        v0_50_audit.SUBVERDICT_C_PERM_PARTIAL,
        v0_50_audit.SUBVERDICT_C_PERM_NOT_FOUND,
    )
    for b_sub in weakened_b:
        for c_sub in weakened_c:
            rollup, phrase = v0_50_audit._evaluate_rollup(
                a_null_subverdict=v0_50_audit.SUBVERDICT_A_NULL_PRESENT,
                b_subverdict=b_sub,
                c_subverdict=c_sub,
                corpus_re_anchor=[],
                bridge_re_anchor=_bridge_anchor_clean(),
            )
            assert rollup == v0_50_audit.ROLLUP_INTERACTION_SUPPORTED, (
                f"(b={b_sub}, c={c_sub}) should map to SUPPORTED"
            )
            assert "weakens under both shifted-top and permuted" in phrase


# ---------------------------------------------------------------------------
# Test 13 — Rollup MIXED when exactly one arm weakens (4 combinations)
# ---------------------------------------------------------------------------


def test_rollup_mixed_when_exactly_one_arm_weakens():
    mixed_combos = [
        # B PRESENT, C weakens.
        (v0_50_audit.SUBVERDICT_B_SHIFTED_PRESENT, v0_50_audit.SUBVERDICT_C_PERM_PARTIAL),
        (v0_50_audit.SUBVERDICT_B_SHIFTED_PRESENT, v0_50_audit.SUBVERDICT_C_PERM_NOT_FOUND),
        # B weakens, C PRESENT.
        (v0_50_audit.SUBVERDICT_B_SHIFTED_PARTIAL, v0_50_audit.SUBVERDICT_C_PERM_PRESENT),
        (v0_50_audit.SUBVERDICT_B_SHIFTED_NOT_FOUND, v0_50_audit.SUBVERDICT_C_PERM_PRESENT),
    ]
    for b_sub, c_sub in mixed_combos:
        rollup, phrase = v0_50_audit._evaluate_rollup(
            a_null_subverdict=v0_50_audit.SUBVERDICT_A_NULL_PRESENT,
            b_subverdict=b_sub,
            c_subverdict=c_sub,
            corpus_re_anchor=[],
            bridge_re_anchor=_bridge_anchor_clean(),
        )
        assert rollup == v0_50_audit.ROLLUP_INTERACTION_MIXED, (
            f"(b={b_sub}, c={c_sub}) should map to MIXED"
        )
        assert "weakens under exactly one of" in phrase


# ---------------------------------------------------------------------------
# Test 14 — Rollup partition is total under A_null PRESENT
# ---------------------------------------------------------------------------


def test_rollup_partition_is_total_under_a_null_present():
    """Exhaustively iterate the 9 (B sub-verdict, C sub-verdict) combinations
    where each is in {PRESENT, PARTIAL, NOT_FOUND}; assert each maps to
    exactly one of {ROBUST, SUPPORTED, MIXED}. Counts: ROBUST = 1,
    SUPPORTED = 4, MIXED = 4."""
    b_states = (
        v0_50_audit.SUBVERDICT_B_SHIFTED_PRESENT,
        v0_50_audit.SUBVERDICT_B_SHIFTED_PARTIAL,
        v0_50_audit.SUBVERDICT_B_SHIFTED_NOT_FOUND,
    )
    c_states = (
        v0_50_audit.SUBVERDICT_C_PERM_PRESENT,
        v0_50_audit.SUBVERDICT_C_PERM_PARTIAL,
        v0_50_audit.SUBVERDICT_C_PERM_NOT_FOUND,
    )
    counts = {
        v0_50_audit.ROLLUP_ROBUST: 0,
        v0_50_audit.ROLLUP_INTERACTION_SUPPORTED: 0,
        v0_50_audit.ROLLUP_INTERACTION_MIXED: 0,
    }
    for b_sub in b_states:
        for c_sub in c_states:
            rollup, _phrase = v0_50_audit._evaluate_rollup(
                a_null_subverdict=v0_50_audit.SUBVERDICT_A_NULL_PRESENT,
                b_subverdict=b_sub,
                c_subverdict=c_sub,
                corpus_re_anchor=[],
                bridge_re_anchor=_bridge_anchor_clean(),
            )
            assert rollup in counts, f"unexpected rollup {rollup} for (b={b_sub}, c={c_sub})"
            counts[rollup] += 1
    assert counts[v0_50_audit.ROLLUP_ROBUST] == 1
    assert counts[v0_50_audit.ROLLUP_INTERACTION_SUPPORTED] == 4
    assert counts[v0_50_audit.ROLLUP_INTERACTION_MIXED] == 4
    assert sum(counts.values()) == 9


# ---------------------------------------------------------------------------
# Test 15 — Bridge replication halt on signed_d drift
# ---------------------------------------------------------------------------


def test_bridge_replication_halt_on_signed_d_drift():
    bridge_re_anchor = []
    for (label, obs), ref in v0_50_audit.V048_PUBLISHED_SIGNED_D.items():
        if label == v0_50_audit.LABEL_A_NAME and obs == "pre50_food_events_count":
            derived = ref + 1.5
            drift = abs(derived - ref)
            halts = drift > v0_50_audit.RE_ANCHOR_DRIFT_TOLERANCE
        else:
            derived = ref
            drift = 0.0
            halts = False
        bridge_re_anchor.append(
            v0_50_audit.BridgeReAnchorRow(
                label=label,
                observable=obs,
                published_signed_d=ref,
                derived_signed_d=derived,
                drift_abs=drift,
                halts=halts,
            )
        )
    rollup, phrase = v0_50_audit._evaluate_rollup(
        a_null_subverdict=v0_50_audit.SUBVERDICT_A_NULL_PRESENT,
        b_subverdict=v0_50_audit.SUBVERDICT_B_SHIFTED_PRESENT,
        c_subverdict=v0_50_audit.SUBVERDICT_C_PERM_PRESENT,
        corpus_re_anchor=[],
        bridge_re_anchor=bridge_re_anchor,
    )
    assert rollup == v0_50_audit.ROLLUP_BRIDGE_REPLICATION_HALT
    assert "does not reproduce v0.48's spatial bridge" in phrase


# ---------------------------------------------------------------------------
# Test 16 — Corpus drift halt has priority over bridge replication halt
# ---------------------------------------------------------------------------


def test_corpus_rederive_drift_halt_priority_over_bridge_replication_halt():
    corpus_re_anchor = [
        v0_50_audit.ReAnchorRow(
            arm=v0_50_audit.ARM_A_NULL,
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
        v0_50_audit.BridgeReAnchorRow(
            label=label,
            observable=obs,
            published_signed_d=ref,
            derived_signed_d=ref + 1.0,
            drift_abs=1.0,
            halts=True,
        )
        for (label, obs), ref in v0_50_audit.V048_PUBLISHED_SIGNED_D.items()
    ]
    rollup, phrase = v0_50_audit._evaluate_rollup(
        a_null_subverdict=v0_50_audit.SUBVERDICT_A_NULL_PRESENT,
        b_subverdict=v0_50_audit.SUBVERDICT_B_SHIFTED_PRESENT,
        c_subverdict=v0_50_audit.SUBVERDICT_C_PERM_PRESENT,
        corpus_re_anchor=corpus_re_anchor,
        bridge_re_anchor=bridge_re_anchor,
    )
    assert rollup == v0_50_audit.ROLLUP_CORPUS_DRIFT_HALT
    assert "v0.42" in phrase
