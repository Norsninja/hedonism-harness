"""Tests for the v0.32 hazard-axis audit (reuses
``scripts/v0.30_audit.py:evaluate_audit`` with ``candidate_label="h=8"``
on the {h=4, h=8, h=12} classifier slice).

Covers:
  - Default-preserving refactor (H4b): ``evaluate_audit(...)`` without
    ``candidate_label`` produces output identical to the v0.30 default.
  - ``candidate_label`` parameterisation: passing ``candidate_label=
    "h=8"`` produces H7 / H8 labels containing ``"h=8"`` and not
    containing ``"w=0.75"``.
  - Hazard slot mapping: a v0.32-style fixture with hazards
    {h=4, h=8, h=12} mapped onto the (0.50, 0.75, 1.00) classifier
    keys produces a correct verdict.
  - v0.25 source-data fixture (seeds 1..8 -> 113/116/114 at influx=1.0):
    aggregates to B=113/116/114, Δ_low=+3, Δ_high=+2; fires H6 WEAK
    under default thresholds. Pins the documented pre-committed
    observation.
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


SEEDS: tuple[int, ...] = tuple(range(1, 9))


def _fixture(rows: list[tuple[int, int, int, int]]) -> dict[tuple[int, float], int]:
    """Build per-seed b50 dict from rows of (seed, b@slot=0.5, b@0.75, b@1.0)."""
    return {(s, w): v for s, *_vs in rows for w, v in zip((0.50, 0.75, 1.00), _vs, strict=True)}


# ---------------------------------------------------------------------------
# Default-preserving refactor anchor (H4b)
# ---------------------------------------------------------------------------


def test_evaluate_audit_default_candidate_label_matches_pre_refactor() -> None:
    """``evaluate_audit(b50, seeds)`` with no ``candidate_label`` MUST
    produce output equivalent to passing ``candidate_label="w=0.75"``.
    Anchor for the additive default-preserving refactor."""
    rows = [(s, 13, 10, 10) for s in SEEDS]  # H8 fires (low neighbour leads)
    obs = _fixture(rows)
    out_default = v030.evaluate_audit(obs, SEEDS)
    out_explicit = v030.evaluate_audit(obs, SEEDS, candidate_label="w=0.75")
    assert out_default == out_explicit


def test_default_h8_label_still_says_w_0_75() -> None:
    """Without ``candidate_label`` argument, the H8 label preserves
    v0.30 / v0.31 wording — `w=0.75` appears in the label."""
    rows = [(s, 13, 10, 10) for s in SEEDS]
    obs = _fixture(rows)
    out = v030.evaluate_audit(obs, SEEDS)
    assert out.hypothesis == "H8"
    assert "w=0.75" in out.label


def test_default_h7_label_still_says_w_0_75() -> None:
    """Without ``candidate_label`` argument, the H7 label preserves
    v0.30 / v0.31 wording — `w=0.75` appears in the label."""
    # All seeds flat at 10 except seed 1 wins +1 at slot 0.5; produces
    # delta_low=-1 (slot 0.5 leads) and delta_high=0; H8 lead = 1 < 5;
    # H6 fails on delta_low<1; H7 fires.
    rows = [(1, 11, 10, 10)] + [(s, 10, 10, 10) for s in range(2, 9)]
    obs = _fixture(rows)
    out = v030.evaluate_audit(obs, SEEDS)
    assert out.hypothesis == "H7"
    assert "w=0.75" in out.label


# ---------------------------------------------------------------------------
# candidate_label parameterisation — v0.32 invokes with "h=8"
# ---------------------------------------------------------------------------


def test_h8_label_uses_h8_when_candidate_label_overridden() -> None:
    """Passing ``candidate_label="h=8"`` produces an H8 label that
    references h=8 instead of w=0.75."""
    rows = [(s, 13, 10, 10) for s in SEEDS]
    obs = _fixture(rows)
    out = v030.evaluate_audit(obs, SEEDS, candidate_label="h=8")
    assert out.hypothesis == "H8"
    assert "h=8" in out.label
    assert "w=0.75" not in out.label


def test_h7_label_uses_h8_when_candidate_label_overridden() -> None:
    """Passing ``candidate_label="h=8"`` produces an H7 label that
    references h=8 instead of w=0.75."""
    rows = [(1, 11, 10, 10)] + [(s, 10, 10, 10) for s in range(2, 9)]
    obs = _fixture(rows)
    out = v030.evaluate_audit(obs, SEEDS, candidate_label="h=8")
    assert out.hypothesis == "H7"
    assert "h=8" in out.label
    assert "w=0.75" not in out.label


def test_h5_h6_labels_are_threshold_only_and_unaffected_by_candidate_label() -> None:
    """H5 / H6 labels do not embed the candidate identifier — they're
    threshold-only ('both Δ >= 5 and n_favoring >= 5' / 'beats both
    neighbours'). Confirm passing ``candidate_label="h=8"`` does not
    change these labels."""
    # H6 fixture: Δ_low=+1, Δ_high=+1.
    rows_h6 = [(1, 10, 11, 10)] + [(s, 10, 10, 10) for s in range(2, 9)]
    obs_h6 = _fixture(rows_h6)
    out_h6_default = v030.evaluate_audit(obs_h6, SEEDS)
    out_h6_h8 = v030.evaluate_audit(obs_h6, SEEDS, candidate_label="h=8")
    assert out_h6_default.label == out_h6_h8.label

    # H5 fixture: clean ROBUST.
    rows_h5 = [
        (1, 10, 16, 13),
        (2, 11, 17, 14),
        (3, 12, 18, 15),
        (4, 13, 19, 16),
        (5, 14, 20, 17),
        (6, 15, 21, 18),
        (7, 16, 22, 19),
        (8, 19, 17, 18),
    ]
    obs_h5 = _fixture(rows_h5)
    out_h5_default = v030.evaluate_audit(obs_h5, SEEDS)
    out_h5_h8 = v030.evaluate_audit(obs_h5, SEEDS, candidate_label="h=8")
    assert out_h5_default.label == out_h5_h8.label


# ---------------------------------------------------------------------------
# Hazard slot mapping smoke test
# ---------------------------------------------------------------------------


def test_hazard_slot_mapping_produces_expected_verdict() -> None:
    """Construct a fixture interpreted as hazards {h=4, h=8, h=12}
    (mapped to slots 0.50, 0.75, 1.00). h=8 strictly beats both
    neighbours by +3 / +2 — should fire H6 with default thresholds."""
    # Per-seed (h=4, h=8, h=12) values aggregating to (113, 116, 114).
    rows = [
        # Aggregates to B = 113 / 116 / 114 -> Δ_low=+3, Δ_high=+2.
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
    out = v030.evaluate_audit(obs, SEEDS, candidate_label="h=8")
    assert out.b_low == 113
    assert out.b_med == 116
    assert out.b_high == 114
    assert out.delta_low == 3
    assert out.delta_high == 2
    assert out.hypothesis == "H6"


# ---------------------------------------------------------------------------
# v0.25 source-data pre-committed observation
# ---------------------------------------------------------------------------


def test_v0_25_source_data_at_influx_1_fires_h6_under_default_classifier() -> None:
    """Documented in the v0.32 pre-reg: applying the default 8-seed
    classifier to the v0.25 source data on the {h=4, h=8, h=12} slice
    at influx=1.0 (113 / 116 / 114) yields H6 WEAK (Δ_low=+3,
    Δ_high=+2). Pins the pre-committed observation against the
    implementation.

    Per-seed v0.25 numbers were not preserved across versions in a
    pinned table; the aggregate B values (113, 116, 114) are pinned
    so we synthesise per-seed values that aggregate to those totals
    with a plausible per-seed pattern. Only the aggregate verdict is
    contractual; the per-seed pattern is illustrative."""
    rows = [
        # Aggregates to B = 113 / 116 / 114 -> Δ_low=+3, Δ_high=+2.
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
    out = v030.evaluate_audit(obs, SEEDS, candidate_label="h=8")
    assert out.b_low == 113
    assert out.b_med == 116
    assert out.b_high == 114
    assert out.delta_low == 3
    assert out.delta_high == 2
    # Δ_high < 5 -> H5 fails -> H6 fires (both Δ >= 1).
    assert out.hypothesis == "H6"
