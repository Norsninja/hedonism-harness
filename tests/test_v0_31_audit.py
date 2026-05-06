"""Tests for the v0.31 pooled 24-seed classifier (reuses
``scripts/v0.30_audit.py:evaluate_audit`` with ``POOLED_THRESHOLDS``)
and for the cross-stream dict merge.

Synthetic-fixture coverage of the pooled partition contract committed
in [[docs/experiments/fear_hunger_v0.31.md]]:

  Pooled thresholds: AuditThresholds(15, 15, 3, 15)
  Priority order (first match wins):
    H8 — REVERSAL:  max(B(0.5), B(1.0)) - B(0.75) >= 15
    H5 — ROBUST:    Δ_low >= 15 AND Δ_high >= 15 AND n_favoring >= 15
    H6 — WEAK:      Δ_low >= 3 AND Δ_high >= 3, NOT H5
    H7 — FAILURE:   none of H5 / H6 / H8

Linear scaling from the v0.30 8-seed thresholds (5/5/1/5 -> 15/15/3/15)
preserves per-seed semantics: 5/8 = 15/24 = 62.5% favoring rate.

Coverage:
  - Default-preserving refactor: ``evaluate_audit(...)`` with no
    ``thresholds`` argument yields identical results to
    ``thresholds=DEFAULT_THRESHOLDS``.
  - Each pooled outcome (H5/H6/H7/H8) has positive fixture(s) and
    boundary cases at the threshold cut-points.
  - Priority H8_pool over H5_pool when a neighbour leads by >= 15.
  - 1..16 pre-committed observation: B_16 = (204, 215, 212);
    Δ_low_16=+11, Δ_high_16=+3 fires H6 at 16-seed-scaled thresholds
    (10/10/2/10). Sanity check on linear scaling.
  - Cross-stream merge: three 8-seed dicts merge cleanly into a
    24-seed dict with no key collisions and correct lookups.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

_AUDIT_PATH = Path(__file__).parent.parent / "scripts" / "v0.30_audit.py"
_spec = importlib.util.spec_from_file_location("v030_audit", _AUDIT_PATH)
assert _spec is not None
assert _spec.loader is not None
v030 = importlib.util.module_from_spec(_spec)
sys.modules["v030_audit"] = v030
_spec.loader.exec_module(v030)


POOLED_THRESHOLDS = v030.AuditThresholds(
    h5_delta_min=15,
    h5_favoring_min=15,
    h6_delta_min=3,
    h8_neighbor_lead_min=15,
)
POOLED_SEEDS: tuple[int, ...] = tuple(range(1, 25))


def _fixture(rows: list[tuple[int, int, int, int]]) -> dict[tuple[int, float], int]:
    """Build per-seed b50 dict from rows of (seed, b@0.5, b@0.75, b@1.0)."""
    return {(s, w): v for s, *_vs in rows for w, v in zip((0.50, 0.75, 1.00), _vs, strict=True)}


# ---------------------------------------------------------------------------
# Default-preserving refactor anchor
# ---------------------------------------------------------------------------


def test_evaluate_audit_default_thresholds_match_explicit_default() -> None:
    """``evaluate_audit(b50, seeds)`` (no thresholds) MUST equal
    ``evaluate_audit(b50, seeds, thresholds=DEFAULT_THRESHOLDS)`` on
    every fixture. Anchor for the additive refactor."""
    rows = [(s, 10, 11, 10) for s in range(1, 9)]
    obs = _fixture(rows)
    out_default = v030.evaluate_audit(obs, tuple(range(1, 9)))
    out_explicit = v030.evaluate_audit(obs, tuple(range(1, 9)), thresholds=v030.DEFAULT_THRESHOLDS)
    assert out_default == out_explicit


def test_default_thresholds_are_5_5_1_5() -> None:
    """Pin the v0.30 default threshold values."""
    assert v030.DEFAULT_THRESHOLDS.h5_delta_min == 5
    assert v030.DEFAULT_THRESHOLDS.h5_favoring_min == 5
    assert v030.DEFAULT_THRESHOLDS.h6_delta_min == 1
    assert v030.DEFAULT_THRESHOLDS.h8_neighbor_lead_min == 5


def test_pooled_thresholds_are_15_15_3_15() -> None:
    """Pin the v0.31 pooled threshold values (linear scaling of 5/5/1/5
    at 8 seeds -> 15/15/3/15 at 24 seeds)."""
    assert POOLED_THRESHOLDS.h5_delta_min == 15
    assert POOLED_THRESHOLDS.h5_favoring_min == 15
    assert POOLED_THRESHOLDS.h6_delta_min == 3
    assert POOLED_THRESHOLDS.h8_neighbor_lead_min == 15


# ---------------------------------------------------------------------------
# Pooled H5 — ROBUST positive fixture and boundaries
# ---------------------------------------------------------------------------


def test_pooled_h5_robust_fires_when_both_deltas_ge_15_and_favoring_ge_15() -> None:
    """20 seeds strictly favor w=0.75 with Δ_low=Δ_high=+1 each;
    4 seeds flat. Aggregate Δ_low=Δ_high=+20; n_favoring=24 (20 strict
    + 4 ties). Pooled H5 fires."""
    favoring = [(s, 10, 11, 10) for s in range(1, 21)]
    flat = [(s, 10, 10, 10) for s in range(21, 25)]
    obs = _fixture(favoring + flat)
    out = v030.evaluate_audit(obs, POOLED_SEEDS, thresholds=POOLED_THRESHOLDS)
    assert out.hypothesis == "H5"
    assert out.delta_low == 20
    assert out.delta_high == 20
    assert out.n_favoring == 24
    assert out.n_strict_favoring == 20


def test_pooled_h5_just_meets_thresholds() -> None:
    """Δ_low=Δ_high=+15 exactly; n_favoring=24 (15 strict + 9 tie);
    fires H5 at the boundary."""
    # 15 seeds (1, 2, 1) -> per-seed Δ_low=+1, Δ_high=+1; strict favor.
    # 9 seeds (10, 10, 10) -> tie-favor (no aggregate contribution).
    strict = [(s, 1, 2, 1) for s in range(1, 16)]
    flat = [(s, 10, 10, 10) for s in range(16, 25)]
    obs = _fixture(strict + flat)
    out = v030.evaluate_audit(obs, POOLED_SEEDS, thresholds=POOLED_THRESHOLDS)
    assert out.delta_low == 15
    assert out.delta_high == 15
    assert out.n_favoring == 24
    assert out.n_strict_favoring == 15
    assert out.hypothesis == "H5"


def test_pooled_h5_fails_when_favoring_short_one_seed() -> None:
    """Aggregate Δ_low and Δ_high both >= 15 but only 14 seeds favor —
    falls to H6 (Δ thresholds for H6 are 3/3 which are met)."""
    # 14 seeds: (1, 20, 1) -> per-seed Δ_low=+19, Δ_high=+19, strict favor.
    # 10 seeds: (20, 10, 20) -> per-seed Δ_low=-10, Δ_high=-10, do not favor.
    favoring = [(s, 1, 20, 1) for s in range(1, 15)]
    not_favoring = [(s, 20, 10, 20) for s in range(15, 25)]
    obs = _fixture(favoring + not_favoring)
    out = v030.evaluate_audit(obs, POOLED_SEEDS, thresholds=POOLED_THRESHOLDS)
    # B(0.5) = 14*1 + 10*20 = 214; B(0.75) = 14*20 + 10*10 = 380;
    # B(1.0) = 14*1 + 10*20 = 214. Δ_low=+166, Δ_high=+166.
    assert out.delta_low >= 15
    assert out.delta_high >= 15
    assert out.n_favoring == 14
    assert out.hypothesis == "H6"


# ---------------------------------------------------------------------------
# Pooled H6 — WEAK positive fixture and boundaries
# ---------------------------------------------------------------------------


def test_pooled_h6_clear_weak_fixture() -> None:
    """Δ_low=+10, Δ_high=+5 (both < 15, both >= 3) — fires H6_pool."""
    # 5 seeds: (10, 12, 11) -> per-seed Δ_low=+2, Δ_high=+1, strict favor.
    # 19 seeds: flat (10, 10, 10).
    rows = [(s, 10, 12, 11) for s in range(1, 6)] + [(s, 10, 10, 10) for s in range(6, 25)]
    obs = _fixture(rows)
    out = v030.evaluate_audit(obs, POOLED_SEEDS, thresholds=POOLED_THRESHOLDS)
    # B(0.5) = 5*10 + 19*10 = 240; B(0.75) = 5*12 + 19*10 = 250;
    # B(1.0) = 5*11 + 19*10 = 245. Δ_low=+10, Δ_high=+5.
    assert out.delta_low == 10
    assert out.delta_high == 5
    assert 3 <= out.delta_low < 15
    assert 3 <= out.delta_high < 15
    assert out.hypothesis == "H6"


def test_pooled_h6_just_meets_minimum_margin() -> None:
    """Δ_low=Δ_high=+3 — both at H6 threshold; fires H6_pool."""
    # 3 seeds: (10, 11, 10) contribute Δ_low=+3, Δ_high=+3.
    # 21 seeds: flat (10, 10, 10).
    rows = [(s, 10, 11, 10) for s in range(1, 4)] + [(s, 10, 10, 10) for s in range(4, 25)]
    obs = _fixture(rows)
    out = v030.evaluate_audit(obs, POOLED_SEEDS, thresholds=POOLED_THRESHOLDS)
    assert out.delta_low == 3
    assert out.delta_high == 3
    assert out.hypothesis == "H6"


def test_pooled_h6_falls_to_h7_when_delta_high_is_2() -> None:
    """Δ_low=+3 but Δ_high=+2 (sub-threshold) — H6_pool fails; H8 also
    fails (no neighbour leads); falls to H7_pool."""
    # 3 seeds: (10, 11, 10) -> +3 / +3 contribution.
    # 1 seed: (10, 10, 11) -> 0 / -1 contribution.
    # 20 seeds: flat (10, 10, 10).
    rows = (
        [(s, 10, 11, 10) for s in range(1, 4)]
        + [(4, 10, 10, 11)]
        + [(s, 10, 10, 10) for s in range(5, 25)]
    )
    obs = _fixture(rows)
    out = v030.evaluate_audit(obs, POOLED_SEEDS, thresholds=POOLED_THRESHOLDS)
    assert out.delta_low == 3
    assert out.delta_high == 2
    assert out.hypothesis == "H7"


# ---------------------------------------------------------------------------
# Pooled H7 — FAILURE positive fixtures
# ---------------------------------------------------------------------------


def test_pooled_h7_fires_when_w075_ties_one_neighbour() -> None:
    """Δ_low=0, Δ_high=+8 — w=0.75 doesn't beat w=0.5 (tie); H7 fires
    (H6 needs Δ_low >= 3; H8 needs lead >= 15)."""
    rows = [(s, 10, 10, 9) for s in POOLED_SEEDS]
    # B(0.5)=240, B(0.75)=240, B(1.0)=216. Δ_low=0, Δ_high=+24.
    obs = _fixture(rows)
    out = v030.evaluate_audit(obs, POOLED_SEEDS, thresholds=POOLED_THRESHOLDS)
    assert out.delta_low == 0
    assert out.delta_high == 24
    assert out.hypothesis == "H7"


def test_pooled_h7_fires_when_w075_loses_to_one_neighbour_by_lt_15() -> None:
    """Δ_high=-14 (just under H8 threshold 15); H6 fails (Δ_high < 3);
    H8 fails (lead 14 < 15) — falls to H7_pool."""
    # All 24 seeds: (10, 11, 12) -> Δ_low=+24, Δ_high=-24. That's H8.
    # Need lead exactly 14: 14 seeds (10, 10, 11), 10 seeds flat (10, 10, 10).
    # B(0.5)=240, B(0.75)=240, B(1.0)=14*11 + 10*10 = 254. Lead = 14.
    rows = [(s, 10, 10, 11) for s in range(1, 15)] + [(s, 10, 10, 10) for s in range(15, 25)]
    obs = _fixture(rows)
    out = v030.evaluate_audit(obs, POOLED_SEEDS, thresholds=POOLED_THRESHOLDS)
    assert max(out.b_low, out.b_high) - out.b_med == 14
    assert out.hypothesis == "H7"


# ---------------------------------------------------------------------------
# Pooled H8 — REVERSAL positive fixture and boundaries
# ---------------------------------------------------------------------------


def test_pooled_h8_fires_when_neighbour_leads_by_exactly_15() -> None:
    """B(1.0) - B(0.75) = +15 — H8 fires at the pooled threshold."""
    # 15 seeds (10, 10, 11), 9 seeds flat (10, 10, 10).
    # B(0.5)=240, B(0.75)=240, B(1.0)=15*11 + 9*10 = 255. Lead = 15.
    rows = [(s, 10, 10, 11) for s in range(1, 16)] + [(s, 10, 10, 10) for s in range(16, 25)]
    obs = _fixture(rows)
    out = v030.evaluate_audit(obs, POOLED_SEEDS, thresholds=POOLED_THRESHOLDS)
    assert max(out.b_low, out.b_high) - out.b_med == 15
    assert out.hypothesis == "H8"


def test_pooled_h8_does_not_fire_when_lead_is_14() -> None:
    """Lead = 14 (below H8 pooled 15); falls to H7."""
    # 14 seeds (10, 10, 11), 10 seeds flat. Lead = 14.
    rows = [(s, 10, 10, 11) for s in range(1, 15)] + [(s, 10, 10, 10) for s in range(15, 25)]
    obs = _fixture(rows)
    out = v030.evaluate_audit(obs, POOLED_SEEDS, thresholds=POOLED_THRESHOLDS)
    assert max(out.b_low, out.b_high) - out.b_med == 14
    assert out.hypothesis == "H7"


def test_pooled_h8_fires_when_low_neighbour_leads() -> None:
    """The reversal condition is symmetric — B(0.5) leading by >= 15
    fires H8_pool."""
    rows = [(s, 13, 10, 10) for s in POOLED_SEEDS]
    # B(0.5)=312, B(0.75)=240, B(1.0)=240. Low lead = 72.
    obs = _fixture(rows)
    out = v030.evaluate_audit(obs, POOLED_SEEDS, thresholds=POOLED_THRESHOLDS)
    assert out.hypothesis == "H8"
    assert out.b_low - out.b_med == 72


# ---------------------------------------------------------------------------
# Pooled priority — H8 dominates H5 when a neighbour leads by >= 15
# ---------------------------------------------------------------------------


def test_pooled_h8_takes_priority_over_h5_when_one_neighbour_dominates() -> None:
    """Construct Δ_low >= 15 (would satisfy H5 against w=0.5) but
    Δ_high <= -15 (H8 reversal against w=1.0). Pooled priority MUST
    return H8."""
    rows = [(s, 5, 12, 18) for s in POOLED_SEEDS]
    # B(0.5)=120, B(0.75)=288, B(1.0)=432. Δ_low=+168, Δ_high=-144.
    # Lead by w=1.0 = 144 >> 15 -> H8.
    obs = _fixture(rows)
    out = v030.evaluate_audit(obs, POOLED_SEEDS, thresholds=POOLED_THRESHOLDS)
    assert out.hypothesis == "H8"


# ---------------------------------------------------------------------------
# Pre-committed observation: 1..16 pool fires H6 at 16-seed-scaled thresholds
# ---------------------------------------------------------------------------


def test_existing_16_seed_pool_fires_h6_at_16_seed_scaled_thresholds() -> None:
    """Documented in the v0.31 pre-reg: applying the pooled rule to the
    existing 1..16 data (B_16 = (204, 215, 212), Δ_low=+11, Δ_high=+3)
    at 16-seed-scaled thresholds (5*16/8=10; 1*16/8=2; lead=10) fires
    H6_16. Pins the linear-scaling logic as a sanity check."""
    # Synthesise a fixture aggregating to (204, 215, 212).
    # Use 16 seeds. Distribute the +11 / +3 deltas across a few seeds.
    rows = (
        [
            # First 11 seeds contribute the +11 Δ_low: (12, 13, 13).
            (s, 12, 13, 13)
            for s in range(1, 12)
        ]
        + [
            # Seeds 12..14: (13, 13, 12) contribute Δ_low=0, Δ_high=+1 each (sum +3).
            (s, 13, 13, 12)
            for s in range(12, 15)
        ]
        + [
            # Seeds 15..16: pad to hit (204, 215, 212).
            (15, 13, 14, 13),
            (16, 14, 14, 14),
        ]
    )
    # Compute aggregate to verify:
    # B(0.5) = 12*11 + 13*3 + 13 + 14 = 132 + 39 + 27 = 198. Wrong; adjust.
    # Let me reconstruct: target B(0.5)=204, B(0.75)=215, B(1.0)=212.
    # Use 16 seeds at b50 = (12.75, 13.4375, 13.25) on average.
    # Simpler: 4 seeds (13, 14, 13) + 12 seeds (b, b, b) where 4*13 + 12*b = 204
    # -> b = (204-52)/12 = 12.667. Non-integer. Try a different split.
    # 8 seeds (13, 14, 13): contrib 104/112/104.
    # 8 seeds at (b1, b2, b3) summing to 100/103/108.
    # Use 8 seeds at (12.5, 12.875, 13.5) — non-integer. Try integer split:
    # 4 seeds (10, 12, 14) -> 40/48/56.
    # 4 seeds (15, 13, 13) -> 60/52/52.
    # 8 seeds (13, 14, 13) -> 104/112/104.
    # Total: 204/212/212. Off by 3 on B(0.75). Replace 1 of the 8 (13,14,13) with (13,17,13):
    # gain +3 on B(0.75): now 204/215/212. ✓
    rows = (
        [(s, 10, 12, 14) for s in range(1, 5)]
        + [(s, 15, 13, 13) for s in range(5, 9)]
        + [(s, 13, 14, 13) for s in range(9, 16)]
        + [(16, 13, 17, 13)]
    )
    obs = _fixture(rows)
    seeds_16 = tuple(range(1, 17))
    thresholds_16 = v030.AuditThresholds(
        h5_delta_min=10, h5_favoring_min=10, h6_delta_min=2, h8_neighbor_lead_min=10
    )
    out = v030.evaluate_audit(obs, seeds_16, thresholds=thresholds_16)
    assert out.b_low == 204
    assert out.b_med == 215
    assert out.b_high == 212
    assert out.delta_low == 11
    assert out.delta_high == 3
    # Δ_low=+11 >= H5's 10 ✓ but Δ_high=+3 < H5's 10 -> H5 fails.
    # H8 lead = max(204, 212) - 215 = -3 -> H8 fails.
    # Δ_low=+11 >= H6's 2 ✓; Δ_high=+3 >= H6's 2 ✓ -> H6 fires.
    assert out.hypothesis == "H6"


# ---------------------------------------------------------------------------
# Cross-stream merge correctness
# ---------------------------------------------------------------------------


def test_cross_stream_merge_three_eight_seed_dicts_form_clean_24_seed_dict() -> None:
    """Merging three per-stream b50 dicts (seeds 1..8, 9..16, 17..24)
    produces a 24-seed dict with no key collisions and correct lookups.
    Anchor for the v0.31 audit driver's stream-merge step."""
    stream1 = {(s, w): s + int(w * 10) for s in range(1, 9) for w in (0.50, 0.75, 1.00)}
    stream2 = {(s, w): s + int(w * 10) for s in range(9, 17) for w in (0.50, 0.75, 1.00)}
    stream3 = {(s, w): s + int(w * 10) for s in range(17, 25) for w in (0.50, 0.75, 1.00)}
    merged: dict[tuple[int, float], int] = {}
    for d in (stream1, stream2, stream3):
        # Verify no collisions before merging.
        for key in d:
            assert key not in merged, f"unexpected key collision: {key}"
        merged.update(d)
    assert len(merged) == 24 * 3
    # Spot-check lookups across stream boundaries.
    assert merged[(1, 0.50)] == stream1[(1, 0.50)]
    assert merged[(12, 0.75)] == stream2[(12, 0.75)]
    assert merged[(20, 1.00)] == stream3[(20, 1.00)]
    # Classifier accepts the merged dict.
    out = v030.evaluate_audit(merged, POOLED_SEEDS, thresholds=POOLED_THRESHOLDS)
    assert out.hypothesis in {"H5", "H6", "H7", "H8"}


# ---------------------------------------------------------------------------
# Label parameterisation — pooled labels reflect pooled thresholds
# ---------------------------------------------------------------------------


def test_pooled_h8_label_uses_pooled_threshold_value() -> None:
    """The H8 label string MUST contain the pooled threshold (15), not
    the v0.30 default (5). Guards against label drift after the
    additive refactor."""
    rows = [(s, 13, 10, 10) for s in POOLED_SEEDS]  # H8 fires.
    obs = _fixture(rows)
    out = v030.evaluate_audit(obs, POOLED_SEEDS, thresholds=POOLED_THRESHOLDS)
    assert out.hypothesis == "H8"
    assert ">= 15" in out.label
    assert ">= 5" not in out.label


def test_default_h8_label_uses_default_threshold_value() -> None:
    """The H8 label string under DEFAULT_THRESHOLDS must use 5, not 15."""
    rows = [(s, 13, 10, 10) for s in range(1, 9)]  # H8 fires.
    obs = _fixture(rows)
    out = v030.evaluate_audit(obs, tuple(range(1, 9)))
    assert out.hypothesis == "H8"
    assert ">= 5" in out.label
    assert ">= 15" not in out.label
