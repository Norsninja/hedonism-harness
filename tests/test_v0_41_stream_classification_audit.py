"""v0.41 stream classification audit + n=5 stability re-run tests.

Coverage:
  - Locked constants (thresholds, hazards, expected stream ids, counts,
    paths, cell + verdict labels).
  - Locked phrase regression guards (3 v0.41 cells + 3 n=5 verdicts).
  - Sealed-CSV halts (missing file, row-count drift) on the 3 new
    FRESH-v0.41 inputs.
  - Stream-id halts (unexpected source_version in any tier).
  - Bucket-count halt (per-(stream, hazard) != 8).
  - Cross-CSV alignment halt within FRESH-v0.41 tier.
  - Per-(stream, hazard) aggregation grouping.
  - Per-stream signed spread + agreement (M3 boundary at +1.5).
  - v0.41 bitmap classification (OLD_LIKE / V039_LIKE / NOVEL_MIXED).
  - n=5 verdict thresholds (H5 m3>=4 fam>=2; H6 m3==3 or m3==4 fam<2;
    H7 m3<=1 — guardrail branch).
  - Combined summary headline.
  - End-to-end synthetic fixture (9 CSVs in tmp_path).
"""

from __future__ import annotations

import csv
import importlib.util
import sys
from pathlib import Path

import pytest


def _load_audit():
    path = Path(__file__).resolve().parents[1] / "scripts" / "v0_41_stream_classification_audit.py"
    spec = importlib.util.spec_from_file_location("v0_41_stream_classification_audit", path)
    assert spec is not None
    assert spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    sys.modules["v0_41_stream_classification_audit"] = mod
    spec.loader.exec_module(mod)
    return mod


# ---------------------------------------------------------------------------
# Locked constants
# ---------------------------------------------------------------------------


def test_locked_thresholds():
    m = _load_audit()
    assert m.M3_SPREAD_THRESHOLD == 1.5
    assert m.H5_M3_MIN_STREAMS_N5 == 4
    assert m.H5_FAMILY_MIN_METRICS_N5 == 2
    assert m.H7_M3_MAX_STREAMS_N5 == 1


def test_locked_hazards_and_streams():
    m = _load_audit()
    assert m.EXPECTED_HAZARDS == (0, 4, 8, 12)
    assert m.EXPECTED_STREAMS_OLD == ("v0.25", "v0.32", "v0.33")
    assert m.EXPECTED_STREAMS_FRESH_V039 == ("v0.39",)
    assert m.EXPECTED_STREAMS_FRESH_V041 == ("v0.41",)
    assert m.EXPECTED_STREAMS_ALL == ("v0.25", "v0.32", "v0.33", "v0.39", "v0.41")


def test_locked_run_counts():
    m = _load_audit()
    assert m.EXPECTED_RUNS_OLD == 96
    assert m.EXPECTED_RUNS_FRESH_V039 == 32
    assert m.EXPECTED_RUNS_FRESH_V041 == 32
    assert m.EXPECTED_RUNS_PER_STREAM_PER_HAZARD == 8


def test_locked_bitmap_cells():
    m = _load_audit()
    assert m.V0_41_BITMAP_OLD_LIKE == (True, True, True)
    assert m.V0_41_BITMAP_V039_LIKE == (True, False, False)
    assert m.CELL_OLD_LIKE == "v0.41_OLD_LIKE"
    assert m.CELL_V039_LIKE == "v0.41_V039_LIKE"
    assert m.CELL_NOVEL_MIXED == "v0.41_NOVEL_MIXED"


def test_locked_n5_verdict_labels():
    m = _load_audit()
    assert m.VERDICT_STABLE_N5 == "H5_STREAM_STABLE_N5"
    assert m.VERDICT_MIXED_N5 == "H6_STREAM_MIXED_N5"
    assert m.VERDICT_UNSTABLE_N5 == "H7_STREAM_UNSTABLE_N5"


def test_locked_paths():
    m = _load_audit()
    assert Path("runs/lineage-v0.34/run_summary.csv") == m.V0_34_OLD_RUN_SUMMARY
    assert Path("runs/lineage-v0.35/pre_post_dominance.csv") == m.V0_35_OLD_PRE_POST
    assert Path("runs/lineage-v0.38/per_run.csv") == m.V0_38_OLD_PER_RUN
    assert Path("runs/lineage-v0.34-fresh/run_summary.csv") == m.V0_34_FRESH_V039
    assert Path("runs/lineage-v0.35-fresh/pre_post_dominance.csv") == m.V0_35_FRESH_V039
    assert Path("runs/lineage-v0.39/per_run.csv") == m.V0_38_FRESH_V039
    assert Path("runs/lineage-v0.34-v0_41-fresh/run_summary.csv") == m.V0_34_FRESH_V041
    assert Path("runs/lineage-v0.35-v0_41-fresh/pre_post_dominance.csv") == m.V0_35_FRESH_V041
    assert Path("runs/lineage-v0.38-v0_41-fresh/per_run.csv") == m.V0_38_FRESH_V041
    assert Path("runs/lineage-v0.41") == m.OUT_DIR


# ---------------------------------------------------------------------------
# Locked phrase regression guards
# ---------------------------------------------------------------------------


def test_old_like_phrase_verbatim():
    m = _load_audit()
    assert m.LOCKED_OLD_LIKE_PHRASE == (
        "Seeds 33..40 reproduce the OLD-stream M1/M2/M3 agreement pattern in "
        "full. v0.39 is the lone outlier across the now-five-stream corpus and "
        "is best read as a one-off n=8 noise excursion rather than evidence of "
        "a systematic post-v0.33 deviation. The v0.34..v0.38 lineage-axis arc's "
        "stream-stability claim is reinforced from 3 of 4 streams to 4 of 5 "
        "streams. Mechanism promotion still requires intervention design and is "
        "not declared by this audit."
    )


def test_v039_like_phrase_verbatim():
    m = _load_audit()
    assert m.LOCKED_V039_LIKE_PHRASE == (
        "Seeds 33..40 reproduce v0.39's exact dissent pattern: M1 agrees, M2 "
        "and M3 do not. The OLD-vs-FRESH split observed in v0.39 is now seen "
        "across two independent fresh streams. v0.39 was not a one-off; "
        "something systematic distinguishes the post-v0.33 seed band from the "
        "OLD pool's 1..24 region. The v0.34..v0.38 arc's stream-stability "
        "claim is conditional on OLD streams only; cross-band generalisation "
        "is unsupported. Mechanism work on the OLD signal is blocked pending "
        "investigation of the OLD-vs-FRESH split."
    )


def test_novel_mixed_phrase_verbatim():
    m = _load_audit()
    assert m.LOCKED_NOVEL_MIXED_PHRASE == (
        "Seeds 33..40 do not cleanly match either the OLD-stream pattern or "
        "v0.39's dissent pattern. Cross-stream variability becomes the "
        "immediate object of study. The v0.34..v0.38 arc's stream-stability "
        "claim weakens; how much depends on which metrics agreed and which "
        "did not (see v041_bitmap.csv). Mechanism work remains blocked. "
        "v0.42 candidates: third fresh stream OR per-stream founder-trait "
        "variance characterisation."
    )


def test_h5_n5_phrase_contains_4_of_5():
    m = _load_audit()
    assert "four of five seed streams" in m.LOCKED_H5_N5_PHRASE
    assert "v0.41 33..40" in m.LOCKED_H5_N5_PHRASE
    assert "stream-stable on 5 streams" in m.LOCKED_H5_N5_PHRASE


def test_h6_n5_phrase_contains_4_5_bar():
    m = _load_audit()
    assert "H5_STREAM_STABLE_N5 bar" in m.LOCKED_H6_N5_PHRASE
    assert ">= 4/5 on M3" in m.LOCKED_H6_N5_PHRASE
    assert "Correlational; not a mechanism declaration." in m.LOCKED_H6_N5_PHRASE


def test_h7_n5_phrase_contains_retraction():
    m = _load_audit()
    assert "fail to reproduce in at least four of five" in m.LOCKED_H7_N5_PHRASE
    assert "stream-unstable at n=5" in m.LOCKED_H7_N5_PHRASE
    assert "blocked pending re-stabilisation" in m.LOCKED_H7_N5_PHRASE


# ---------------------------------------------------------------------------
# Sealed CSV halts (FRESH-v0.41 tier)
# ---------------------------------------------------------------------------


def _make_csv(path: Path, header: list[str], rows: list[list[str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as f:
        w = csv.writer(f)
        w.writerow(header)
        for r in rows:
            w.writerow(r)


def test_assert_fresh_v041_halts_on_missing_v34(monkeypatch, tmp_path):
    m = _load_audit()
    monkeypatch.setattr(m, "V0_34_FRESH_V041", tmp_path / "missing.csv")
    with pytest.raises(m.lr.LineageReplayError, match=r"sealed CSV missing"):
        m.assert_fresh_v041_corpus_sealed()


def test_assert_fresh_v041_halts_on_missing_v35(monkeypatch, tmp_path):
    m = _load_audit()
    # Make v0.34 v0.41-fresh exist but v0.35 missing
    good = tmp_path / "v34.csv"
    _make_csv(good, ["source_version"], [["v0.41"]] * 32)
    monkeypatch.setattr(m, "V0_34_FRESH_V041", good)
    monkeypatch.setattr(m, "V0_35_FRESH_V041", tmp_path / "missing35.csv")
    with pytest.raises(m.lr.LineageReplayError, match=r"sealed CSV missing"):
        m.assert_fresh_v041_corpus_sealed()


def test_assert_fresh_v041_halts_on_missing_v38(monkeypatch, tmp_path):
    m = _load_audit()
    good = tmp_path / "v34.csv"
    _make_csv(good, ["source_version"], [["v0.41"]] * 32)
    good35 = tmp_path / "v35.csv"
    _make_csv(good35, ["source_version"], [["v0.41"]] * 32)
    monkeypatch.setattr(m, "V0_34_FRESH_V041", good)
    monkeypatch.setattr(m, "V0_35_FRESH_V041", good35)
    monkeypatch.setattr(m, "V0_38_FRESH_V041", tmp_path / "missing38.csv")
    with pytest.raises(m.lr.LineageReplayError, match=r"sealed CSV missing"):
        m.assert_fresh_v041_corpus_sealed()


def test_assert_fresh_v041_halts_on_row_count_drift(monkeypatch, tmp_path):
    m = _load_audit()
    bad = tmp_path / "bad.csv"
    _make_csv(bad, ["source_version"], [["v0.41"]])
    monkeypatch.setattr(m, "V0_34_FRESH_V041", bad)
    with pytest.raises(m.lr.LineageReplayError, match=r"row-count drift"):
        m.assert_fresh_v041_corpus_sealed()


# ---------------------------------------------------------------------------
# Per-run aggregation helpers
# ---------------------------------------------------------------------------


def _make_per_run(m, *, source_version, hazard, seed, m1=0.5, m2=0.0, m3=2.0):
    return m._PerRun(
        source_version=source_version,
        arm_label=f"transfer-1500-hzd{hazard}-influx-1.0",
        hazard=hazard,
        seed=seed,
        m1=m1,
        m2=m2,
        m3=m3,
    )


def _make_buckets_full(m, *, m3_by_stream_hazard: dict[tuple[str, int], float]):
    """Build a complete (5 streams x 4 hazards x 8 runs) bucket dict."""
    buckets: dict[tuple[str, int], list] = {}
    for stream in m.EXPECTED_STREAMS_ALL:
        for hazard in m.EXPECTED_HAZARDS:
            runs = []
            m3_val = m3_by_stream_hazard.get((stream, hazard), 0.0)
            for seed in range(8):
                runs.append(
                    _make_per_run(m, source_version=stream, hazard=hazard, seed=seed, m3=m3_val)
                )
            buckets[(stream, hazard)] = runs
    return buckets


def test_aggregate_per_stream_per_hazard_groups_correctly():
    m = _load_audit()
    buckets = _make_buckets_full(
        m,
        m3_by_stream_hazard={
            ("v0.41", 0): 1.0,
            ("v0.41", 12): 5.0,
        },
    )
    rows = m.aggregate_per_stream_per_hazard(buckets)
    by = {(r.stream, r.hazard): r for r in rows}
    assert by[("v0.41", 0)].mean_m3 == 1.0
    assert by[("v0.41", 12)].mean_m3 == 5.0
    assert by[("v0.41", 0)].n_runs == 8
    # 5 streams x 4 hazards = 20 rows total
    assert len(rows) == 20


# ---------------------------------------------------------------------------
# Per-stream signed spread + agreement
# ---------------------------------------------------------------------------


def _make_per_haz(m, stream: str, m1_seq, m2_seq, m3_seq):
    return [
        m.PerStreamPerHazardRow(
            stream=stream,
            hazard=h,
            n_runs=8,
            mean_m1=m1_seq[i],
            mean_m2=m2_seq[i],
            mean_m3=m3_seq[i],
        )
        for i, h in enumerate(m.EXPECTED_HAZARDS)
    ]


def _all_streams_per_haz(m, *, by_stream):
    out = []
    for s in m.EXPECTED_STREAMS_ALL:
        m1, m2, m3 = by_stream[s]
        out.extend(_make_per_haz(m, s, m1, m2, m3))
    return out


def test_aggregate_per_stream_summary_signed_spread():
    m = _load_audit()
    by_stream = {
        "v0.25": ([0.5, 0.6, 0.7, 0.8], [0.1, 0.2, 0.3, 0.4], [3.0, 5.0, 7.0, 9.0]),
        "v0.32": ([0.5] * 4, [0.4, 0.3, 0.2, 0.1], [4.0] * 4),
        "v0.33": ([0.5] * 4, [0.4, 0.3, 0.2, 0.1], [4.0] * 4),
        "v0.39": ([0.5] * 4, [0.4, 0.3, 0.2, 0.1], [4.0] * 4),
        "v0.41": ([0.5] * 4, [0.4, 0.3, 0.2, 0.1], [4.0] * 4),
    }
    rows = _all_streams_per_haz(m, by_stream=by_stream)
    summary = m.aggregate_per_stream_summary(rows)
    by = {s.stream: s for s in summary}
    assert by["v0.25"].m1_signed_spread == pytest.approx(0.3)
    assert by["v0.25"].m3_signed_spread == pytest.approx(6.0)
    assert by["v0.25"].m1_agrees is True
    assert by["v0.25"].m2_agrees is True
    assert by["v0.25"].m3_agrees is True
    assert len(summary) == 5


def test_m3_agreement_at_threshold_exactly():
    m = _load_audit()
    by_stream = {
        s: ([0.5] * 4, [0.5] * 4, [3.0, 3.0, 3.0, 4.5])  # spread = 1.5
        for s in m.EXPECTED_STREAMS_ALL
    }
    rows = _all_streams_per_haz(m, by_stream=by_stream)
    summary = m.aggregate_per_stream_summary(rows)
    by = {s.stream: s for s in summary}
    assert by["v0.41"].m3_signed_spread == pytest.approx(1.5)
    assert by["v0.41"].m3_agrees is True  # >= 1.5 fires


def test_m3_agreement_just_below_threshold_fails():
    m = _load_audit()
    by_stream = {
        s: ([0.5] * 4, [0.5] * 4, [3.0, 3.0, 3.0, 4.4])  # spread = 1.4
        for s in m.EXPECTED_STREAMS_ALL
    }
    rows = _all_streams_per_haz(m, by_stream=by_stream)
    summary = m.aggregate_per_stream_summary(rows)
    by = {s.stream: s for s in summary}
    assert by["v0.41"].m3_agrees is False


def test_m1_m2_direction_only_zero_does_not_agree():
    m = _load_audit()
    by_stream = {s: ([0.5] * 4, [0.5] * 4, [3.0] * 4) for s in m.EXPECTED_STREAMS_ALL}
    rows = _all_streams_per_haz(m, by_stream=by_stream)
    summary = m.aggregate_per_stream_summary(rows)
    by = {s.stream: s for s in summary}
    assert by["v0.41"].m1_agrees is False  # spread == 0; not > 0
    assert by["v0.41"].m2_agrees is False


# ---------------------------------------------------------------------------
# v0.41 bitmap classification
# ---------------------------------------------------------------------------


def _per_stream_with_v041_bitmap(m, *, m1: bool, m2: bool, m3: bool):
    """Build a 5-stream summary where v0.41 has the requested bitmap."""

    def _row(s, m1_v, m2_v, m3_v):
        return m.PerStreamSummaryRow(
            stream=s,
            n_runs=32,
            m1_signed_spread=0.1 if m1_v else -0.1,
            m1_agrees=m1_v,
            m1_monotone_up=m1_v,
            m1_monotone_down=False,
            m2_signed_spread=0.1 if m2_v else -0.1,
            m2_agrees=m2_v,
            m2_monotone_up=m2_v,
            m2_monotone_down=False,
            m3_signed_spread=2.0 if m3_v else 0.5,
            m3_agrees=m3_v,
            m3_monotone_up=m3_v,
            m3_monotone_down=False,
        )

    rows = [
        _row("v0.25", True, True, True),
        _row("v0.32", True, True, True),
        _row("v0.33", True, True, True),
        _row("v0.39", True, False, False),
        _row("v0.41", m1, m2, m3),
    ]
    return rows


def test_classify_v041_bitmap_old_like():
    m = _load_audit()
    per_stream = _per_stream_with_v041_bitmap(m, m1=True, m2=True, m3=True)
    bitmap = m.classify_v041_bitmap(per_stream)
    assert bitmap.bitmap_cell == m.CELL_OLD_LIKE


def test_classify_v041_bitmap_v039_like():
    m = _load_audit()
    per_stream = _per_stream_with_v041_bitmap(m, m1=True, m2=False, m3=False)
    bitmap = m.classify_v041_bitmap(per_stream)
    assert bitmap.bitmap_cell == m.CELL_V039_LIKE


def test_classify_v041_bitmap_novel_mixed_all_false():
    m = _load_audit()
    per_stream = _per_stream_with_v041_bitmap(m, m1=False, m2=False, m3=False)
    bitmap = m.classify_v041_bitmap(per_stream)
    assert bitmap.bitmap_cell == m.CELL_NOVEL_MIXED


def test_classify_v041_bitmap_novel_mixed_m1_pass_m3_pass_m2_fail():
    m = _load_audit()
    per_stream = _per_stream_with_v041_bitmap(m, m1=True, m2=False, m3=True)
    bitmap = m.classify_v041_bitmap(per_stream)
    assert bitmap.bitmap_cell == m.CELL_NOVEL_MIXED


def test_classify_v041_bitmap_novel_mixed_m1_fail_m2_pass_m3_pass():
    m = _load_audit()
    per_stream = _per_stream_with_v041_bitmap(m, m1=False, m2=True, m3=True)
    bitmap = m.classify_v041_bitmap(per_stream)
    assert bitmap.bitmap_cell == m.CELL_NOVEL_MIXED


def test_classify_v041_bitmap_halts_when_v041_missing():
    m = _load_audit()
    per_stream = [
        r for r in _per_stream_with_v041_bitmap(m, m1=True, m2=True, m3=True) if r.stream != "v0.41"
    ]
    with pytest.raises(m.lr.LineageReplayError, match=r"expected exactly one v0.41 row"):
        m.classify_v041_bitmap(per_stream)


def test_build_v041_classification_old_like_phrase():
    m = _load_audit()
    bitmap = m.V041BitmapRow(
        m1_agrees=True, m2_agrees=True, m3_agrees=True, bitmap_cell=m.CELL_OLD_LIKE
    )
    classification = m.build_v041_classification(bitmap)
    assert classification.locked_phrase == m.LOCKED_OLD_LIKE_PHRASE


def test_build_v041_classification_v039_like_phrase():
    m = _load_audit()
    bitmap = m.V041BitmapRow(
        m1_agrees=True, m2_agrees=False, m3_agrees=False, bitmap_cell=m.CELL_V039_LIKE
    )
    classification = m.build_v041_classification(bitmap)
    assert classification.locked_phrase == m.LOCKED_V039_LIKE_PHRASE


def test_build_v041_classification_novel_mixed_phrase():
    m = _load_audit()
    bitmap = m.V041BitmapRow(
        m1_agrees=False,
        m2_agrees=True,
        m3_agrees=False,
        bitmap_cell=m.CELL_NOVEL_MIXED,
    )
    classification = m.build_v041_classification(bitmap)
    assert classification.locked_phrase == m.LOCKED_NOVEL_MIXED_PHRASE


# ---------------------------------------------------------------------------
# n=5 verdict
# ---------------------------------------------------------------------------


def _metric_summary(m, n_m1: int, n_m2: int, n_m3: int):
    return [
        m.MetricSummaryRow(
            metric="M1", n_streams_agree=n_m1, n_streams_total=5, agreement_rate=n_m1 / 5
        ),
        m.MetricSummaryRow(
            metric="M2", n_streams_agree=n_m2, n_streams_total=5, agreement_rate=n_m2 / 5
        ),
        m.MetricSummaryRow(
            metric="M3", n_streams_agree=n_m3, n_streams_total=5, agreement_rate=n_m3 / 5
        ),
    ]


def test_verdict_n5_h5_fires_with_m3_4_family_2():
    m = _load_audit()
    # M1 = 5/5 (counts), M2 = 3/5 (does not count), M3 = 4/5 (counts) -> family=2
    summary = _metric_summary(m, n_m1=5, n_m2=3, n_m3=4)
    v = m.evaluate_n5_verdict(summary)
    assert v.verdict == m.VERDICT_STABLE_N5
    assert v.locked_phrase == m.LOCKED_H5_N5_PHRASE
    assert v.m3_agreement_count == 4
    assert v.family_agreement_count == 2


def test_verdict_n5_h5_fires_with_m3_5_family_3():
    m = _load_audit()
    summary = _metric_summary(m, n_m1=5, n_m2=5, n_m3=5)
    v = m.evaluate_n5_verdict(summary)
    assert v.verdict == m.VERDICT_STABLE_N5
    assert v.family_agreement_count == 3


def test_verdict_n5_h6_fires_when_m3_4_but_family_only_1():
    m = _load_audit()
    # Only M3 has >= 4/5; M1 and M2 below 4/5.
    summary = _metric_summary(m, n_m1=3, n_m2=3, n_m3=4)
    v = m.evaluate_n5_verdict(summary)
    assert v.verdict == m.VERDICT_MIXED_N5
    assert v.locked_phrase == m.LOCKED_H6_N5_PHRASE


def test_verdict_n5_h6_fires_when_m3_3():
    m = _load_audit()
    summary = _metric_summary(m, n_m1=5, n_m2=5, n_m3=3)
    v = m.evaluate_n5_verdict(summary)
    assert v.verdict == m.VERDICT_MIXED_N5


def test_verdict_n5_h6_fires_when_m3_2():
    m = _load_audit()
    summary = _metric_summary(m, n_m1=5, n_m2=5, n_m3=2)
    v = m.evaluate_n5_verdict(summary)
    assert v.verdict == m.VERDICT_MIXED_N5


def test_verdict_n5_h7_fires_when_m3_1():
    m = _load_audit()
    # Guardrail branch — should be unreachable under sealed v0.40 inputs but
    # tested directly on synthesised metric summaries.
    summary = _metric_summary(m, n_m1=5, n_m2=5, n_m3=1)
    v = m.evaluate_n5_verdict(summary)
    assert v.verdict == m.VERDICT_UNSTABLE_N5
    assert v.locked_phrase == m.LOCKED_H7_N5_PHRASE


def test_verdict_n5_h7_fires_when_m3_0():
    m = _load_audit()
    summary = _metric_summary(m, n_m1=0, n_m2=0, n_m3=0)
    v = m.evaluate_n5_verdict(summary)
    assert v.verdict == m.VERDICT_UNSTABLE_N5


# ---------------------------------------------------------------------------
# Combined summary
# ---------------------------------------------------------------------------


def test_build_combined_summary_old_like_h5():
    m = _load_audit()
    bitmap = m.V041BitmapRow(
        m1_agrees=True, m2_agrees=True, m3_agrees=True, bitmap_cell=m.CELL_OLD_LIKE
    )
    n5 = m.N5VerdictRow(
        verdict=m.VERDICT_STABLE_N5,
        locked_phrase=m.LOCKED_H5_N5_PHRASE,
        m3_agreement_count=4,
        family_agreement_count=2,
    )
    combined = m.build_combined_summary(bitmap, n5)
    assert combined.v041_cell == m.CELL_OLD_LIKE
    assert combined.n5_verdict == m.VERDICT_STABLE_N5
    assert "v0.41 stream classified as v0.41_OLD_LIKE" in combined.joint_headline
    assert "fires H5_STREAM_STABLE_N5" in combined.joint_headline
    assert "m3=4/5" in combined.joint_headline


def test_build_combined_summary_v039_like_h6():
    m = _load_audit()
    bitmap = m.V041BitmapRow(
        m1_agrees=True, m2_agrees=False, m3_agrees=False, bitmap_cell=m.CELL_V039_LIKE
    )
    n5 = m.N5VerdictRow(
        verdict=m.VERDICT_MIXED_N5,
        locked_phrase=m.LOCKED_H6_N5_PHRASE,
        m3_agreement_count=3,
        family_agreement_count=1,
    )
    combined = m.build_combined_summary(bitmap, n5)
    assert "v0.41_V039_LIKE" in combined.joint_headline
    assert "H6_STREAM_MIXED_N5" in combined.joint_headline


# ---------------------------------------------------------------------------
# wad_flag parsing edge cases
# ---------------------------------------------------------------------------


def test_parse_optional_bool_true():
    m = _load_audit()
    assert m._parse_optional_bool("True") == 1.0


def test_parse_optional_bool_false():
    m = _load_audit()
    assert m._parse_optional_bool("False") == 0.0


def test_parse_optional_bool_empty():
    m = _load_audit()
    assert m._parse_optional_bool("") is None


def test_parse_optional_bool_unexpected_halts():
    m = _load_audit()
    with pytest.raises(m.lr.LineageReplayError, match=r"unexpected wad_flag"):
        m._parse_optional_bool("yes")


# ---------------------------------------------------------------------------
# End-to-end synthetic fixture
# ---------------------------------------------------------------------------


def _write_full_synthetic_corpus(tmp_path: Path, m, *, v041_pattern: str):  # noqa: PLR0915
    """Build nine minimal CSVs in tmp_path passing all H2 invariants.

    OLD streams encode monotone-up M1/M2/M3 (all three pass).
    FRESH-v0.39 encodes the v0.39 dissent pattern (M1 ✓, M2 ✗, M3 ✗).
    FRESH-v0.41 follows the requested pattern:
      - "old_like": M1 ✓, M2 ✓, M3 ✓  -> v0.41_OLD_LIKE + H5_N5
      - "v039_like": M1 ✓, M2 ✗, M3 ✗ -> v0.41_V039_LIKE + H6_N5
      - "all_fail": all flat (m1/m2 spread 0 -> False; m3 spread 0 -> False)
                    -> v0.41_NOVEL_MIXED + H6_N5
    """
    streams_old = m.EXPECTED_STREAMS_OLD
    seed_ranges_old = {"v0.25": range(1, 9), "v0.32": range(9, 17), "v0.33": range(17, 25)}
    fresh_v039 = m.EXPECTED_STREAMS_FRESH_V039[0]
    fresh_v041 = m.EXPECTED_STREAMS_FRESH_V041[0]
    seeds_v039 = range(25, 33)
    seeds_v041 = range(33, 41)
    hazards = m.EXPECTED_HAZARDS

    paths = {
        "v34_old": tmp_path / "v34_old.csv",
        "v35_old": tmp_path / "v35_old.csv",
        "v38_old": tmp_path / "v38_old.csv",
        "v34_v039": tmp_path / "v34_v039.csv",
        "v35_v039": tmp_path / "v35_v039.csv",
        "v38_v039": tmp_path / "v38_v039.csv",
        "v34_v041": tmp_path / "v34_v041.csv",
        "v35_v041": tmp_path / "v35_v041.csv",
        "v38_v041": tmp_path / "v38_v041.csv",
    }

    def _write_v34(path, streams, seed_func, m1_at):
        rows = []
        for stream in streams:
            for hazard in hazards:
                arm_label = f"transfer-1500-hzd{hazard}-influx-1.0"
                for seed in seed_func(stream):
                    rows.append(
                        [stream, arm_label, str(hazard), str(seed), str(m1_at(stream, hazard))]
                    )
        _make_csv(
            path,
            ["source_version", "arm_label", "hazard", "seed", "top_lineage_b50_share"],
            rows,
        )

    def _write_v35(path, streams, seed_func, wad_at):
        rows = []
        for stream in streams:
            for hazard in hazards:
                arm_label = f"transfer-1500-hzd{hazard}-influx-1.0"
                for seed in seed_func(stream):
                    rows.append([stream, arm_label, str(hazard), str(seed), wad_at(stream, hazard)])
        _make_csv(
            path,
            [
                "source_version",
                "arm_label",
                "hazard",
                "seed",
                "winner_already_dominant_at_tick_50",
            ],
            rows,
        )

    def _write_v38(path, streams, seed_func, m3_at):
        rows = []
        for stream in streams:
            for hazard in hazards:
                arm_label = f"transfer-1500-hzd{hazard}-influx-1.0"
                for seed in seed_func(stream):
                    rows.append(
                        [stream, arm_label, str(hazard), str(seed), str(m3_at(stream, hazard))]
                    )
        _make_csv(
            path,
            ["source_version", "arm_label", "hazard", "seed", "leader_advantage"],
            rows,
        )

    # OLD: all three pass (M1 +0.12, M2 wad-up, M3 +6.0)
    def m1_old(_s, h):
        return 0.6 + h * 0.01

    def wad_old(_s, h):
        return "True" if h >= 4 else "False"

    def m3_old(_s, h):
        return 4.0 + h * 0.5

    # FRESH-v0.39: M1 ✓ tiny, M2 ✗ (decreasing), M3 ✗ (negative)
    def m1_v039(_s, h):
        return 0.66 + h * 0.001

    def wad_v039(_s, h):
        return "True" if h == 0 else "False"

    def m3_v039(_s, h):
        return 6.0 - h * 0.05

    if v041_pattern == "old_like":
        m1_v041 = m1_old
        wad_v041 = wad_old
        m3_v041 = m3_old
    elif v041_pattern == "v039_like":
        m1_v041 = m1_v039
        wad_v041 = wad_v039
        m3_v041 = m3_v039
    elif v041_pattern == "all_fail":

        def m1_v041(_s, _h):
            return 0.5

        def wad_v041(_s, _h):
            return "False"

        def m3_v041(_s, _h):
            return 4.0
    else:
        msg = f"unknown v041_pattern: {v041_pattern}"
        raise ValueError(msg)

    def seeds_old(s):
        return seed_ranges_old[s]

    def seeds_v039_func(_s):
        return seeds_v039

    def seeds_v041_func(_s):
        return seeds_v041

    _write_v34(paths["v34_old"], streams_old, seeds_old, m1_old)
    _write_v35(paths["v35_old"], streams_old, seeds_old, wad_old)
    _write_v38(paths["v38_old"], streams_old, seeds_old, m3_old)
    _write_v34(paths["v34_v039"], [fresh_v039], seeds_v039_func, m1_v039)
    _write_v35(paths["v35_v039"], [fresh_v039], seeds_v039_func, wad_v039)
    _write_v38(paths["v38_v039"], [fresh_v039], seeds_v039_func, m3_v039)
    _write_v34(paths["v34_v041"], [fresh_v041], seeds_v041_func, m1_v041)
    _write_v35(paths["v35_v041"], [fresh_v041], seeds_v041_func, wad_v041)
    _write_v38(paths["v38_v041"], [fresh_v041], seeds_v041_func, m3_v041)

    return paths


def _patch_audit_to(monkeypatch, m, paths, out_dir):
    monkeypatch.setattr(m, "V0_34_OLD_RUN_SUMMARY", paths["v34_old"])
    monkeypatch.setattr(m, "V0_35_OLD_PRE_POST", paths["v35_old"])
    monkeypatch.setattr(m, "V0_38_OLD_PER_RUN", paths["v38_old"])
    monkeypatch.setattr(m, "V0_34_FRESH_V039", paths["v34_v039"])
    monkeypatch.setattr(m, "V0_35_FRESH_V039", paths["v35_v039"])
    monkeypatch.setattr(m, "V0_38_FRESH_V039", paths["v38_v039"])
    monkeypatch.setattr(m, "V0_34_FRESH_V041", paths["v34_v041"])
    monkeypatch.setattr(m, "V0_35_FRESH_V041", paths["v35_v041"])
    monkeypatch.setattr(m, "V0_38_FRESH_V041", paths["v38_v041"])
    monkeypatch.setattr(m, "OUT_DIR", out_dir)


def test_end_to_end_synthetic_old_like_fires_h5_n5(tmp_path, monkeypatch):
    m = _load_audit()
    paths = _write_full_synthetic_corpus(tmp_path, m, v041_pattern="old_like")
    out_dir = tmp_path / "lineage-v0.41"
    _patch_audit_to(monkeypatch, m, paths, out_dir)

    m.main()

    # v0.41 bitmap should be OLD_LIKE
    with (out_dir / "v041_bitmap.csv").open() as f:
        rows = list(csv.DictReader(f))
    assert len(rows) == 1
    assert rows[0]["bitmap_cell"] == m.CELL_OLD_LIKE

    # n=5 verdict should be H5_STREAM_STABLE_N5 (m3=4/5: OLD 3 + v0.41; v0.39 fails)
    with (out_dir / "n5_verdict.csv").open() as f:
        rows = list(csv.DictReader(f))
    assert rows[0]["verdict"] == m.VERDICT_STABLE_N5
    assert rows[0]["m3_agreement_count"] == "4"

    # Combined headline mentions both
    with (out_dir / "combined_summary.csv").open() as f:
        rows = list(csv.DictReader(f))
    assert rows[0]["v041_cell"] == m.CELL_OLD_LIKE
    assert rows[0]["n5_verdict"] == m.VERDICT_STABLE_N5

    # Stream metric table has 5 rows
    with (out_dir / "stream_metric_table.csv").open() as f:
        table_rows = list(csv.DictReader(f))
    assert len(table_rows) == 5
    by_stream = {r["stream"]: r for r in table_rows}
    assert by_stream["v0.41"]["m3_agrees"] == "True"
    assert by_stream["v0.39"]["m3_agrees"] == "False"


def test_end_to_end_synthetic_v039_like_fires_h6_n5(tmp_path, monkeypatch):
    m = _load_audit()
    paths = _write_full_synthetic_corpus(tmp_path, m, v041_pattern="v039_like")
    out_dir = tmp_path / "lineage-v0.41"
    _patch_audit_to(monkeypatch, m, paths, out_dir)

    m.main()

    with (out_dir / "v041_bitmap.csv").open() as f:
        bitmap_rows = list(csv.DictReader(f))
    assert bitmap_rows[0]["bitmap_cell"] == m.CELL_V039_LIKE

    with (out_dir / "n5_verdict.csv").open() as f:
        verdict_rows = list(csv.DictReader(f))
    assert verdict_rows[0]["verdict"] == m.VERDICT_MIXED_N5
    # M3 passes only in OLD streams (3/5); H6 fires
    assert verdict_rows[0]["m3_agreement_count"] == "3"


def test_end_to_end_halts_on_wrong_v041_stream_id(tmp_path, monkeypatch):
    """If FRESH-v0.41 CSV contains an unexpected source_version, halt."""
    m = _load_audit()
    paths = _write_full_synthetic_corpus(tmp_path, m, v041_pattern="old_like")

    # Corrupt v34_v041: rewrite first row with wrong source_version
    with paths["v34_v041"].open() as f:
        rows = list(csv.reader(f))
    rows[1][0] = "v0.99"  # row 0 is header
    with paths["v34_v041"].open("w", newline="") as f:
        w = csv.writer(f)
        w.writerows(rows)

    out_dir = tmp_path / "lineage-v0.41"
    _patch_audit_to(monkeypatch, m, paths, out_dir)

    with pytest.raises(m.lr.LineageReplayError, match=r"FRESH-v0.41 stream-id drift"):
        m.main()


def test_end_to_end_halts_on_v041_bucket_count_drift(tmp_path, monkeypatch):
    """If v0.41 has != 8 runs in some (stream, hazard) bucket, halt."""
    m = _load_audit()
    paths = _write_full_synthetic_corpus(tmp_path, m, v041_pattern="old_like")

    # Drop one row from each v0.41 CSV (now 31 rows; row-count halt fires first).
    # To trigger bucket-count instead, we drop one row and add a duplicate at a
    # different hazard within the same stream, keeping total at 32.
    def _drop_and_duplicate(path):
        with path.open() as f:
            rows = list(csv.reader(f))
        header = rows[0]
        data = rows[1:]
        # data[0] is v0.41 hzd=0 first seed. Drop it, duplicate a hzd=4 row
        # with seed=99 to bump that bucket to 9 while shrinking hzd=0 to 7.
        data.pop(0)
        for r in data:
            if r[0] == "v0.41" and r[2] == "4":
                dup = list(r)
                dup[3] = "99"
                data.append(dup)
                break
        with path.open("w", newline="") as f:
            w = csv.writer(f)
            w.writerow(header)
            w.writerows(data)

    _drop_and_duplicate(paths["v34_v041"])
    _drop_and_duplicate(paths["v35_v041"])
    _drop_and_duplicate(paths["v38_v041"])

    out_dir = tmp_path / "lineage-v0.41"
    _patch_audit_to(monkeypatch, m, paths, out_dir)

    with pytest.raises(m.lr.LineageReplayError, match=r"bucket-count drift"):
        m.main()


def test_end_to_end_halts_on_v041_tier_misalignment(tmp_path, monkeypatch):
    """If a (source, arm, seed) key exists in M1 but not M3 within v0.41 tier,
    halt with H2f."""
    m = _load_audit()
    paths = _write_full_synthetic_corpus(tmp_path, m, v041_pattern="old_like")

    # Replace one v0.41 v0.38 row's seed with a non-matching value.
    with paths["v38_v041"].open() as f:
        rows = list(csv.reader(f))
    # row 1 is first data row; change its seed
    rows[1][3] = "999"
    with paths["v38_v041"].open("w", newline="") as f:
        w = csv.writer(f)
        w.writerows(rows)

    out_dir = tmp_path / "lineage-v0.41"
    _patch_audit_to(monkeypatch, m, paths, out_dir)

    with pytest.raises(m.lr.LineageReplayError, match=r"FRESH-v0.41 cross-CSV key misalignment"):
        m.main()
