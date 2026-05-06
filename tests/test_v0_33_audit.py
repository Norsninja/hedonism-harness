"""Tests for the v0.33 pooled 24-seed hazard-axis classifier (reuses
``scripts/v0.30_audit.py:evaluate_audit`` with ``POOLED_THRESHOLDS`` and
``candidate_label="h=8"``) and for the 4-arm cross-stream dict merge.

v0.33 reuses the v0.31 pooled rule (15/15/3/15) verbatim — only the
slot-to-axis mapping and ``candidate_label`` change. Synthetic-fixture
coverage targets the v0.33-specific surface area:

  - ``candidate_label="h=8"`` propagates into pooled H7 / H8 labels.
  - 1..16 hazard-axis pre-committed observation (B_16 = (204, 212, 208);
    Δ_low=+8, Δ_high=+4) fires H6 at 16-seed-scaled thresholds
    (10/10/2/10).
  - Hazard-slot cross-stream merge with the v0.32 / v0.33 4-slot key
    space (0.0 baseline + 0.5/0.75/1.0 classifier slice).
  - Pooled positive fixtures still fire correctly when invoked with
    ``candidate_label="h=8"`` — guards against any axis-coupling
    regression in the classifier.
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

# Classifier slot keys are positional placeholders for hazards
# {h=4, h=8, h=12} (mirrors scripts/v0.32_audit.py / scripts/v0.33_audit.py).
SLOT_LOW = 0.50
SLOT_MED = 0.75
SLOT_HIGH = 1.00


def _fixture(rows: list[tuple[int, int, int, int]]) -> dict[tuple[int, float], int]:
    """Build per-seed b50 dict from rows of (seed, b@h=4, b@h=8, b@h=12)."""
    return {
        (s, slot): v
        for s, *_vs in rows
        for slot, v in zip((SLOT_LOW, SLOT_MED, SLOT_HIGH), _vs, strict=True)
    }


# ---------------------------------------------------------------------------
# v0.33 reuses v0.31 pooled thresholds verbatim
# ---------------------------------------------------------------------------


def test_v0_33_pooled_thresholds_match_v0_31() -> None:
    """v0.33 must reuse the v0.31 pooled threshold values
    (15/15/3/15) — no axis-specific scaling."""
    assert POOLED_THRESHOLDS.h5_delta_min == 15
    assert POOLED_THRESHOLDS.h5_favoring_min == 15
    assert POOLED_THRESHOLDS.h6_delta_min == 3
    assert POOLED_THRESHOLDS.h8_neighbor_lead_min == 15


# ---------------------------------------------------------------------------
# candidate_label="h=8" propagates into pooled H7 / H8 labels
# ---------------------------------------------------------------------------


def test_pooled_h8_label_uses_h8_when_candidate_label_overridden() -> None:
    """Pooled H8 verdict's label MUST reference 'h=8' (not 'w=0.75')."""
    rows = [(s, 13, 10, 10) for s in POOLED_SEEDS]  # H8 (low neighbour leads).
    obs = _fixture(rows)
    out = v030.evaluate_audit(
        obs, POOLED_SEEDS, thresholds=POOLED_THRESHOLDS, candidate_label="h=8"
    )
    assert out.hypothesis == "H8"
    assert "h=8" in out.label
    assert "w=0.75" not in out.label
    assert ">= 15" in out.label  # pooled threshold visible.


def test_pooled_h7_label_uses_h8_when_candidate_label_overridden() -> None:
    """Pooled H7 verdict's label MUST reference 'h=8' (not 'w=0.75')."""
    # Δ_low=+3, Δ_high=+2 (H6 fails on Δ_high; H7 fires).
    rows = (
        [(s, 10, 11, 10) for s in range(1, 4)]
        + [(4, 10, 10, 11)]
        + [(s, 10, 10, 10) for s in range(5, 25)]
    )
    obs = _fixture(rows)
    out = v030.evaluate_audit(
        obs, POOLED_SEEDS, thresholds=POOLED_THRESHOLDS, candidate_label="h=8"
    )
    assert out.hypothesis == "H7"
    assert "h=8" in out.label
    assert "w=0.75" not in out.label


def test_pooled_h5_h6_labels_unaffected_by_candidate_label() -> None:
    """H5 / H6 pooled labels are threshold-only — they do not embed
    'h=8' or 'w=0.75'. Pin that adding candidate_label does not
    accidentally change the H5 / H6 wording."""
    # H6 fixture: Δ_low=Δ_high=+3.
    h6_rows = [(s, 10, 11, 10) for s in range(1, 4)] + [(s, 10, 10, 10) for s in range(4, 25)]
    obs_h6 = _fixture(h6_rows)
    out_h6_default = v030.evaluate_audit(obs_h6, POOLED_SEEDS, thresholds=POOLED_THRESHOLDS)
    out_h6_h8 = v030.evaluate_audit(
        obs_h6, POOLED_SEEDS, thresholds=POOLED_THRESHOLDS, candidate_label="h=8"
    )
    assert out_h6_default.label == out_h6_h8.label
    assert out_h6_h8.hypothesis == "H6"

    # H5 fixture: 20 strict-favoring seeds + 4 flat.
    h5_rows = [(s, 10, 11, 10) for s in range(1, 21)] + [(s, 10, 10, 10) for s in range(21, 25)]
    obs_h5 = _fixture(h5_rows)
    out_h5_default = v030.evaluate_audit(obs_h5, POOLED_SEEDS, thresholds=POOLED_THRESHOLDS)
    out_h5_h8 = v030.evaluate_audit(
        obs_h5, POOLED_SEEDS, thresholds=POOLED_THRESHOLDS, candidate_label="h=8"
    )
    assert out_h5_default.label == out_h5_h8.label
    assert out_h5_h8.hypothesis == "H5"


# ---------------------------------------------------------------------------
# Pooled positive fixtures still classify correctly with candidate_label
# ---------------------------------------------------------------------------


def test_pooled_h5_robust_with_h8_label() -> None:
    """Pooled H5 fires on hazard-axis fixture invoked with
    candidate_label='h=8'. Classifier behaviour does not change."""
    favoring = [(s, 10, 11, 10) for s in range(1, 21)]
    flat = [(s, 10, 10, 10) for s in range(21, 25)]
    obs = _fixture(favoring + flat)
    out = v030.evaluate_audit(
        obs, POOLED_SEEDS, thresholds=POOLED_THRESHOLDS, candidate_label="h=8"
    )
    assert out.hypothesis == "H5"
    assert out.delta_low == 20
    assert out.delta_high == 20
    assert out.n_favoring == 24


def test_pooled_h8_takes_priority_over_h5_with_h8_label() -> None:
    """Pooled priority H8 > H5 holds with candidate_label='h=8'."""
    rows = [(s, 5, 12, 18) for s in POOLED_SEEDS]
    # Δ_low=+168, Δ_high=-144 -> H8 fires by high-neighbour lead.
    obs = _fixture(rows)
    out = v030.evaluate_audit(
        obs, POOLED_SEEDS, thresholds=POOLED_THRESHOLDS, candidate_label="h=8"
    )
    assert out.hypothesis == "H8"
    assert "h=8" in out.label


# ---------------------------------------------------------------------------
# 1..16 hazard-axis pre-committed observation
# ---------------------------------------------------------------------------


def test_hazard_axis_16_seed_pool_fires_h6_at_16_seed_scaled_thresholds() -> None:
    """Documented in the v0.33 pre-reg: applying the pooled rule to
    the existing 1..16 hazard-axis data (B_16 = (204, 212, 208) at
    h ∈ {4, 8, 12}, influx=1.0) at 16-seed-scaled thresholds
    (5*16/8=10; 1*16/8=2; lead=10) fires H6_16. Pins the
    proportional-scaling logic on the hazard axis.

    Stream 1 (v0.25, 1..8): B = (113, 116, 114).
    Stream 2 (v0.32, 9..16): B = (91, 96, 94).
    Pool: B_16 = (204, 212, 208) -> Δ_low=+8, Δ_high=+4."""
    # 16 seeds aggregating to (204, 212, 208).
    # 4 seeds (10, 12, 11) -> 40/48/44.
    # 4 seeds (15, 14, 14) -> 60/56/56.
    # 8 seeds (13, 13.5, 13.5) — non-integer. Try:
    # 8 seeds (13, 14, 14) -> 104/112/112.
    # Total so far: 4 + 4 + 8 = 16 seeds; 40+60+104=204, 48+56+112=216, 44+56+112=212.
    # Wrong: B_med=216, target 212; B_high=212, target 208. Difference: B_med +4, B_high +4.
    # Reduce one of (13, 14, 14) to (13, 13, 13): B_med 14->13 (-1), B_high 14->13 (-1).
    # Need -4 each on B_med and B_high. Replace 4 of the 8 (13, 14, 14) with (13, 13, 13):
    # 4 seeds (10, 12, 11) -> 40/48/44.
    # 4 seeds (15, 14, 14) -> 60/56/56.
    # 4 seeds (13, 14, 14) -> 52/56/56.
    # 4 seeds (13, 13, 13) -> 52/52/52.
    # Total: 204/212/208. ✓
    rows = (
        [(s, 10, 12, 11) for s in range(1, 5)]
        + [(s, 15, 14, 14) for s in range(5, 9)]
        + [(s, 13, 14, 14) for s in range(9, 13)]
        + [(s, 13, 13, 13) for s in range(13, 17)]
    )
    obs = _fixture(rows)
    seeds_16 = tuple(range(1, 17))
    thresholds_16 = v030.AuditThresholds(
        h5_delta_min=10, h5_favoring_min=10, h6_delta_min=2, h8_neighbor_lead_min=10
    )
    out = v030.evaluate_audit(obs, seeds_16, thresholds=thresholds_16, candidate_label="h=8")
    assert out.b_low == 204
    assert out.b_med == 212
    assert out.b_high == 208
    assert out.delta_low == 8
    assert out.delta_high == 4
    # Δ_low=+8 < H5's 10 -> H5 fails. H8 lead = max(204, 208) - 212 = -4 -> H8 fails.
    # Δ_low=+8 >= H6's 2 ✓; Δ_high=+4 >= H6's 2 ✓ -> H6 fires.
    assert out.hypothesis == "H6"


def test_v0_25_stream1_alone_fires_h6_under_default_classifier() -> None:
    """Pinning the pre-committed v0.25 source observation (already
    anchored in test_v0_32_audit.py): B(1..8) = (113, 116, 114)
    fires H6 under the default 8-seed thresholds with
    candidate_label='h=8'. Reaffirmed for v0.33's stream-1 reload."""
    rows = [
        (1, 14, 14, 14),
        (2, 14, 15, 14),
        (3, 14, 15, 14),
        (4, 14, 14, 14),
        (5, 14, 15, 14),
        (6, 14, 14, 14),
        (7, 14, 14, 14),
        (8, 15, 15, 16),
    ]
    obs = _fixture(rows)
    out = v030.evaluate_audit(obs, tuple(range(1, 9)), candidate_label="h=8")
    assert out.b_low == 113
    assert out.b_med == 116
    assert out.b_high == 114
    assert out.delta_low == 3
    assert out.delta_high == 2
    assert out.hypothesis == "H6"


# ---------------------------------------------------------------------------
# 4-arm cross-stream merge correctness (hazard-axis slot space)
# ---------------------------------------------------------------------------


def test_hazard_axis_cross_stream_merge_three_eight_seed_dicts_form_24_seed_dict() -> None:
    """Merging three per-stream b50 dicts on the v0.33 4-slot key space
    (0.0 baseline + 0.5/0.75/1.0 classifier slice) produces a clean
    24-seed dict with no key collisions and correct lookups across
    stream boundaries."""
    slots = (0.00, 0.50, 0.75, 1.00)
    stream1 = {(s, slot): s + int(slot * 10) for s in range(1, 9) for slot in slots}
    stream2 = {(s, slot): s + int(slot * 10) for s in range(9, 17) for slot in slots}
    stream3 = {(s, slot): s + int(slot * 10) for s in range(17, 25) for slot in slots}
    merged: dict[tuple[int, float], int] = {}
    for d in (stream1, stream2, stream3):
        for key in d:
            assert key not in merged, f"unexpected key collision: {key}"
        merged.update(d)
    assert len(merged) == 24 * 4
    # Spot-check across stream boundaries.
    assert merged[(1, 0.00)] == stream1[(1, 0.00)]
    assert merged[(12, 0.75)] == stream2[(12, 0.75)]
    assert merged[(20, 1.00)] == stream3[(20, 1.00)]


def test_classifier_slice_extraction_from_4_slot_merged_dict() -> None:
    """The v0.33 audit driver drops the h=0 baseline (slot 0.0) when
    constructing the classifier-slice b50_at dict. Verify the standard
    pattern produces a 3-slot-per-seed dict accepted by evaluate_audit."""
    slots_full = (0.00, 0.50, 0.75, 1.00)
    slots_classifier = (0.50, 0.75, 1.00)
    full = {(s, slot): 10 + (1 if slot == 0.75 else 0) for s in POOLED_SEEDS for slot in slots_full}
    sliced = {(s, slot): full[(s, slot)] for s in POOLED_SEEDS for slot in slots_classifier}
    assert len(sliced) == 24 * 3
    out = v030.evaluate_audit(
        sliced, POOLED_SEEDS, thresholds=POOLED_THRESHOLDS, candidate_label="h=8"
    )
    # 24 seeds, each contributing +1 to B(0.75) and 0 to B(0.5)/B(1.0).
    # B(0.5)=240, B(0.75)=264, B(1.0)=240. Δ_low=+24, Δ_high=+24.
    # n_favoring=24 (all strict). Pooled H5 fires.
    assert out.delta_low == 24
    assert out.delta_high == 24
    assert out.n_favoring == 24
    assert out.hypothesis == "H5"
