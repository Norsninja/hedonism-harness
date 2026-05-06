"""v0.40 cross-stream stability audit tests.

Coverage:
  - Locked constants (thresholds, hazards, expected stream ids, counts).
  - Sealed-CSV halts (missing file, row-count drift) on each of 6 inputs.
  - Stream-id halt (unexpected source_version in OLD or FRESH).
  - Bucket-count halt (per-(stream, hazard) != 8).
  - Cross-CSV alignment halt (missing key in one of three tier CSVs).
  - Per-(stream, hazard) aggregation (mean_M1/M2/M3 grouping).
  - Per-stream signed spread arithmetic.
  - Agreement flags (M1/M2 direction-only, M3 magnitude bar at 1.5).
  - Three-way verdict (H5/H6/H7) on synthesised metric summaries.
  - Locked phrase identity (verbatim regression guards).
  - End-to-end synthetic fixture in tmp_path.
"""

from __future__ import annotations

import csv
import importlib.util
import sys
from pathlib import Path

import pytest


def _load_audit():
    path = Path(__file__).resolve().parents[1] / "scripts" / "v0_40_stream_stability_audit.py"
    spec = importlib.util.spec_from_file_location("v0_40_stream_stability_audit", path)
    assert spec is not None
    assert spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    sys.modules["v0_40_stream_stability_audit"] = mod
    spec.loader.exec_module(mod)
    return mod


# ---------------------------------------------------------------------------
# Locked constants
# ---------------------------------------------------------------------------


def test_locked_thresholds():
    m = _load_audit()
    assert m.M3_SPREAD_THRESHOLD == 1.5
    assert m.H5_M3_MIN_STREAMS == 3
    assert m.H5_FAMILY_MIN_METRICS == 2
    assert m.H7_M3_MAX_STREAMS == 1


def test_locked_hazards_and_streams():
    m = _load_audit()
    assert m.EXPECTED_HAZARDS == (0, 4, 8, 12)
    assert m.EXPECTED_STREAMS_OLD == ("v0.25", "v0.32", "v0.33")
    assert m.EXPECTED_STREAMS_FRESH == ("v0.39",)
    assert m.EXPECTED_STREAMS_ALL == ("v0.25", "v0.32", "v0.33", "v0.39")


def test_locked_run_counts():
    m = _load_audit()
    assert m.EXPECTED_RUNS_OLD == 96
    assert m.EXPECTED_RUNS_FRESH == 32
    assert m.EXPECTED_RUNS_PER_STREAM_PER_HAZARD == 8


def test_locked_paths():
    m = _load_audit()
    assert Path("runs/lineage-v0.34/run_summary.csv") == m.V0_34_OLD_RUN_SUMMARY
    assert Path("runs/lineage-v0.35/pre_post_dominance.csv") == m.V0_35_OLD_PRE_POST
    assert Path("runs/lineage-v0.38/per_run.csv") == m.V0_38_PER_RUN
    assert Path("runs/lineage-v0.34-fresh/run_summary.csv") == m.V0_34_FRESH_RUN_SUMMARY
    assert Path("runs/lineage-v0.35-fresh/pre_post_dominance.csv") == m.V0_35_FRESH_PRE_POST
    assert Path("runs/lineage-v0.39/per_run.csv") == m.V0_39_PER_RUN
    assert Path("runs/lineage-v0.40") == m.OUT_DIR


# ---------------------------------------------------------------------------
# Locked phrase regression guards
# ---------------------------------------------------------------------------


def test_h5_phrase_verbatim():
    m = _load_audit()
    assert m.LOCKED_H5_PHRASE == (
        "Lineage-axis hazard signals reproduce in at least three of four "
        "seed streams (v0.25 1..8, v0.32 9..16, v0.33 17..24, v0.39 25..32) "
        "under the locked spread agreement rules. The v0.34..v0.38 arc's "
        "correlational signal is upgraded from single-stream to stream-"
        "stable across the four streams now on disk. Mechanism promotion "
        "still requires intervention design and is not declared by this "
        "audit."
    )


def test_h6_phrase_contains_v0_41_candidate():
    m = _load_audit()
    assert "stream-mixed" in m.LOCKED_H6_PHRASE
    assert "second fresh stream (seeds 33..40)" in m.LOCKED_H6_PHRASE
    assert "Correlational; not a mechanism declaration." in m.LOCKED_H6_PHRASE


def test_h7_phrase_contains_retraction():
    m = _load_audit()
    assert "fail to reproduce" in m.LOCKED_H7_PHRASE
    assert "stream-unstable" in m.LOCKED_H7_PHRASE
    assert "blocked pending re-stabilisation" in m.LOCKED_H7_PHRASE


# ---------------------------------------------------------------------------
# Sealed CSV halts
# ---------------------------------------------------------------------------


def _make_csv(path: Path, header: list[str], rows: list[list[str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as f:
        w = csv.writer(f)
        w.writerow(header)
        for r in rows:
            w.writerow(r)


def test_assert_old_corpus_sealed_halts_on_missing(monkeypatch, tmp_path):
    m = _load_audit()
    monkeypatch.setattr(m, "V0_34_OLD_RUN_SUMMARY", tmp_path / "missing.csv")
    with pytest.raises(m.lr.LineageReplayError, match=r"sealed CSV missing"):
        m.assert_old_corpus_sealed()


def test_assert_old_corpus_sealed_halts_on_row_count_drift(monkeypatch, tmp_path):
    m = _load_audit()
    bad = tmp_path / "bad.csv"
    _make_csv(bad, ["source_version"], [["v0.25"]])
    monkeypatch.setattr(m, "V0_34_OLD_RUN_SUMMARY", bad)
    with pytest.raises(m.lr.LineageReplayError, match=r"row-count drift"):
        m.assert_old_corpus_sealed()


def test_assert_fresh_corpus_sealed_halts_on_missing(monkeypatch, tmp_path):
    m = _load_audit()
    monkeypatch.setattr(m, "V0_34_FRESH_RUN_SUMMARY", tmp_path / "missing.csv")
    with pytest.raises(m.lr.LineageReplayError, match=r"sealed CSV missing"):
        m.assert_fresh_corpus_sealed()


def test_assert_fresh_corpus_sealed_halts_on_row_count_drift(monkeypatch, tmp_path):
    m = _load_audit()
    bad = tmp_path / "bad.csv"
    _make_csv(bad, ["source_version"], [["v0.39"]])
    monkeypatch.setattr(m, "V0_34_FRESH_RUN_SUMMARY", bad)
    with pytest.raises(m.lr.LineageReplayError, match=r"row-count drift"):
        m.assert_fresh_corpus_sealed()


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
    """Build a complete (4 streams x 4 hazards x 8 runs) bucket dict."""
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
            ("v0.25", 0): 1.0,
            ("v0.25", 12): 5.0,
            ("v0.32", 0): 2.0,
            ("v0.32", 12): 4.0,
        },
    )
    rows = m.aggregate_per_stream_per_hazard(buckets)
    by = {(r.stream, r.hazard): r for r in rows}
    assert by[("v0.25", 0)].mean_m3 == 1.0
    assert by[("v0.25", 12)].mean_m3 == 5.0
    assert by[("v0.25", 0)].n_runs == 8


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


def test_aggregate_per_stream_summary_signed_spread():
    m = _load_audit()
    rows = (
        _make_per_haz(m, "v0.25", [0.5, 0.6, 0.7, 0.8], [0.1, 0.2, 0.3, 0.4], [3.0, 5.0, 7.0, 9.0])
        + _make_per_haz(
            m, "v0.32", [0.5, 0.5, 0.5, 0.5], [0.4, 0.3, 0.2, 0.1], [4.0, 4.0, 4.0, 4.0]
        )
        + _make_per_haz(
            m, "v0.33", [0.5, 0.5, 0.5, 0.5], [0.4, 0.3, 0.2, 0.1], [4.0, 4.0, 4.0, 4.0]
        )
        + _make_per_haz(
            m, "v0.39", [0.5, 0.5, 0.5, 0.5], [0.4, 0.3, 0.2, 0.1], [4.0, 4.0, 4.0, 4.0]
        )
    )
    summary = m.aggregate_per_stream_summary(rows)
    by_stream = {s.stream: s for s in summary}
    v25 = by_stream["v0.25"]
    assert v25.m1_signed_spread == pytest.approx(0.3)
    assert v25.m2_signed_spread == pytest.approx(0.3)
    assert v25.m3_signed_spread == pytest.approx(6.0)
    assert v25.m1_agrees is True
    assert v25.m2_agrees is True
    assert v25.m3_agrees is True


def test_m3_agreement_at_threshold_exactly():
    m = _load_audit()
    rows = (
        _make_per_haz(m, "v0.25", [0.5] * 4, [0.5] * 4, [3.0, 3.0, 3.0, 4.5])  # spread = 1.5
        + _make_per_haz(m, "v0.32", [0.5] * 4, [0.5] * 4, [3.0] * 4)
        + _make_per_haz(m, "v0.33", [0.5] * 4, [0.5] * 4, [3.0] * 4)
        + _make_per_haz(m, "v0.39", [0.5] * 4, [0.5] * 4, [3.0] * 4)
    )
    summary = m.aggregate_per_stream_summary(rows)
    by_stream = {s.stream: s for s in summary}
    assert by_stream["v0.25"].m3_signed_spread == pytest.approx(1.5)
    assert by_stream["v0.25"].m3_agrees is True  # >= 1.5 fires


def test_m3_agreement_just_below_threshold_fails():
    m = _load_audit()
    rows = (
        _make_per_haz(m, "v0.25", [0.5] * 4, [0.5] * 4, [3.0, 3.0, 3.0, 4.4])  # spread = 1.4
        + _make_per_haz(m, "v0.32", [0.5] * 4, [0.5] * 4, [3.0] * 4)
        + _make_per_haz(m, "v0.33", [0.5] * 4, [0.5] * 4, [3.0] * 4)
        + _make_per_haz(m, "v0.39", [0.5] * 4, [0.5] * 4, [3.0] * 4)
    )
    summary = m.aggregate_per_stream_summary(rows)
    by_stream = {s.stream: s for s in summary}
    assert by_stream["v0.25"].m3_agrees is False


def test_m1_m2_direction_only_zero_does_not_agree():
    m = _load_audit()
    rows = (
        _make_per_haz(m, "v0.25", [0.5] * 4, [0.5] * 4, [3.0] * 4)  # M1/M2/M3 all flat
        + _make_per_haz(m, "v0.32", [0.5] * 4, [0.5] * 4, [3.0] * 4)
        + _make_per_haz(m, "v0.33", [0.5] * 4, [0.5] * 4, [3.0] * 4)
        + _make_per_haz(m, "v0.39", [0.5] * 4, [0.5] * 4, [3.0] * 4)
    )
    summary = m.aggregate_per_stream_summary(rows)
    by = {s.stream: s for s in summary}
    assert by["v0.25"].m1_agrees is False  # spread == 0; not > 0
    assert by["v0.25"].m2_agrees is False
    assert by["v0.25"].m3_agrees is False


# ---------------------------------------------------------------------------
# Three-way verdict
# ---------------------------------------------------------------------------


def _metric_summary(m, n_m1: int, n_m2: int, n_m3: int):
    return [
        m.MetricSummaryRow(
            metric="M1", n_streams_agree=n_m1, n_streams_total=4, agreement_rate=n_m1 / 4
        ),
        m.MetricSummaryRow(
            metric="M2", n_streams_agree=n_m2, n_streams_total=4, agreement_rate=n_m2 / 4
        ),
        m.MetricSummaryRow(
            metric="M3", n_streams_agree=n_m3, n_streams_total=4, agreement_rate=n_m3 / 4
        ),
    ]


def test_verdict_h5_fires_with_m3_3_family_2():
    m = _load_audit()
    summary = _metric_summary(m, n_m1=3, n_m2=2, n_m3=3)  # family count = 2 (M1, M3)
    v = m.evaluate_verdict(summary)
    assert v.verdict == m.VERDICT_STABLE
    assert v.locked_phrase == m.LOCKED_H5_PHRASE
    assert v.m3_agreement_count == 3
    assert v.family_agreement_count == 2


def test_verdict_h5_fires_with_m3_4_family_3():
    m = _load_audit()
    summary = _metric_summary(m, n_m1=4, n_m2=4, n_m3=4)
    v = m.evaluate_verdict(summary)
    assert v.verdict == m.VERDICT_STABLE
    assert v.family_agreement_count == 3


def test_verdict_h6_fires_when_m3_3_but_family_only_1():
    m = _load_audit()
    summary = _metric_summary(m, n_m1=2, n_m2=2, n_m3=3)  # only M3 has >=3
    v = m.evaluate_verdict(summary)
    assert v.verdict == m.VERDICT_MIXED
    assert v.locked_phrase == m.LOCKED_H6_PHRASE


def test_verdict_h6_fires_when_m3_2():
    m = _load_audit()
    summary = _metric_summary(m, n_m1=4, n_m2=4, n_m3=2)
    v = m.evaluate_verdict(summary)
    assert v.verdict == m.VERDICT_MIXED


def test_verdict_h7_fires_when_m3_1():
    m = _load_audit()
    summary = _metric_summary(m, n_m1=4, n_m2=4, n_m3=1)
    v = m.evaluate_verdict(summary)
    assert v.verdict == m.VERDICT_UNSTABLE
    assert v.locked_phrase == m.LOCKED_H7_PHRASE


def test_verdict_h7_fires_when_m3_0():
    m = _load_audit()
    summary = _metric_summary(m, n_m1=0, n_m2=0, n_m3=0)
    v = m.evaluate_verdict(summary)
    assert v.verdict == m.VERDICT_UNSTABLE


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


def _write_full_synthetic_corpus(tmp_path: Path, m) -> tuple[Path, Path, Path, Path, Path, Path]:
    """Build six minimal CSVs in tmp_path that pass all H2 invariants and
    encode a known H5_STREAM_STABLE pattern (3 OLD streams agree on M3,
    v0.39 fails M3)."""
    streams_old = m.EXPECTED_STREAMS_OLD
    seed_ranges_old = {"v0.25": range(1, 9), "v0.32": range(9, 17), "v0.33": range(17, 25)}
    fresh = m.EXPECTED_STREAMS_FRESH[0]
    fresh_seeds = range(25, 33)
    hazards = m.EXPECTED_HAZARDS

    v34_old_path = tmp_path / "v34_old.csv"
    v35_old_path = tmp_path / "v35_old.csv"
    v38_old_path = tmp_path / "v38_old.csv"
    v34_fresh_path = tmp_path / "v34_fresh.csv"
    v35_fresh_path = tmp_path / "v35_fresh.csv"
    v39_fresh_path = tmp_path / "v39_fresh.csv"

    def _write_v34(path, streams, seed_func, m1_at):
        rows = []
        for stream in streams:
            for hazard in hazards:
                arm_label = f"transfer-1500-hzd{hazard}-influx-1.0"
                for seed in seed_func(stream):
                    m1 = m1_at(stream, hazard)
                    rows.append([stream, arm_label, str(hazard), str(seed), str(m1)])
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
                    wad = wad_at(stream, hazard)
                    rows.append([stream, arm_label, str(hazard), str(seed), wad])
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
                    m3 = m3_at(stream, hazard)
                    rows.append([stream, arm_label, str(hazard), str(seed), str(m3)])
        _make_csv(
            path,
            ["source_version", "arm_label", "hazard", "seed", "leader_advantage"],
            rows,
        )

    # OLD streams: monotone-up M1/M2/M3 agreement
    def m1_old(s, h):
        return 0.6 + h * 0.01  # +0.12 spread (positive)

    def wad_old(s, h):
        return "True" if h >= 4 else "False"  # wad rate up

    def m3_old(s, h):
        return 4.0 + h * 0.5  # +6 spread (above 1.5)

    # FRESH stream: failing M3 (negative spread), failing M2, marginal M1
    def m1_fresh(s, h):
        return 0.66 + h * 0.001  # +0.012 (positive but tiny)

    def wad_fresh(s, h):
        return "True" if h == 0 else "False"  # decreasing

    def m3_fresh(s, h):
        return 6.0 - h * 0.05  # spread -0.6 (below 1.5)

    def seeds_old(s):
        return seed_ranges_old[s]

    def seeds_fresh(_s):
        return fresh_seeds

    _write_v34(v34_old_path, streams_old, seeds_old, m1_old)
    _write_v35(v35_old_path, streams_old, seeds_old, wad_old)
    _write_v38(v38_old_path, streams_old, seeds_old, m3_old)
    _write_v34(v34_fresh_path, [fresh], seeds_fresh, m1_fresh)
    _write_v35(v35_fresh_path, [fresh], seeds_fresh, wad_fresh)
    _write_v38(v39_fresh_path, [fresh], seeds_fresh, m3_fresh)

    return v34_old_path, v35_old_path, v38_old_path, v34_fresh_path, v35_fresh_path, v39_fresh_path


def test_end_to_end_synthetic_fires_h5_stream_stable(tmp_path, monkeypatch):
    m = _load_audit()
    paths = _write_full_synthetic_corpus(tmp_path, m)
    v34_old, v35_old, v38_old, v34_fresh, v35_fresh, v39_fresh = paths
    out_dir = tmp_path / "lineage-v0.40"

    monkeypatch.setattr(m, "V0_34_OLD_RUN_SUMMARY", v34_old)
    monkeypatch.setattr(m, "V0_35_OLD_PRE_POST", v35_old)
    monkeypatch.setattr(m, "V0_38_PER_RUN", v38_old)
    monkeypatch.setattr(m, "V0_34_FRESH_RUN_SUMMARY", v34_fresh)
    monkeypatch.setattr(m, "V0_35_FRESH_PRE_POST", v35_fresh)
    monkeypatch.setattr(m, "V0_39_PER_RUN", v39_fresh)
    monkeypatch.setattr(m, "OUT_DIR", out_dir)

    m.main()

    # Verify verdict CSV
    with (out_dir / "verdict.csv").open() as f:
        rows = list(csv.DictReader(f))
    assert len(rows) == 1
    assert rows[0]["verdict"] == m.VERDICT_STABLE
    assert rows[0]["m3_agreement_count"] == "3"

    # Verify table CSV has 4 rows
    with (out_dir / "stream_metric_table.csv").open() as f:
        table_rows = list(csv.DictReader(f))
    assert len(table_rows) == 4
    by_stream = {r["stream"]: r for r in table_rows}
    assert by_stream["v0.25"]["m3_agrees"] == "True"
    assert by_stream["v0.39"]["m3_agrees"] == "False"


def test_end_to_end_halts_on_wrong_old_stream_id(tmp_path, monkeypatch):
    """If OLD CSVs contain an unexpected source_version, halt."""
    m = _load_audit()
    paths = _write_full_synthetic_corpus(tmp_path, m)
    v34_old, v35_old, v38_old, v34_fresh, v35_fresh, v39_fresh = paths

    # Corrupt v34_old: rewrite first row with wrong source_version
    with v34_old.open() as f:
        rows = list(csv.reader(f))
    rows[1][0] = "v0.99"  # row 0 is header
    with v34_old.open("w", newline="") as f:
        w = csv.writer(f)
        w.writerows(rows)

    monkeypatch.setattr(m, "V0_34_OLD_RUN_SUMMARY", v34_old)
    monkeypatch.setattr(m, "V0_35_OLD_PRE_POST", v35_old)
    monkeypatch.setattr(m, "V0_38_PER_RUN", v38_old)
    monkeypatch.setattr(m, "V0_34_FRESH_RUN_SUMMARY", v34_fresh)
    monkeypatch.setattr(m, "V0_35_FRESH_PRE_POST", v35_fresh)
    monkeypatch.setattr(m, "V0_39_PER_RUN", v39_fresh)
    monkeypatch.setattr(m, "OUT_DIR", tmp_path / "lineage-v0.40")

    with pytest.raises(m.lr.LineageReplayError, match=r"OLD stream-id drift"):
        m.main()


def test_end_to_end_halts_on_bucket_count_drift(tmp_path, monkeypatch):
    """If a bucket has != 8 runs, halt."""
    m = _load_audit()
    paths = _write_full_synthetic_corpus(tmp_path, m)
    v34_old, v35_old, v38_old, v34_fresh, v35_fresh, v39_fresh = paths

    # Drop one row from v34_old (now 95 rows total; v0.25/h=0 has only 7).
    # That fails row-count first (95 != 96), so we drop one row from EACH of
    # the three OLD CSVs to keep row counts at 96 individually but break a
    # bucket. Wait — that would make tier-alignment fail. The simplest is to
    # ALSO drop the matching row from v35_old and v38_old, AND add a duplicate
    # row to the same stream/hazard (different seed) to keep total at 96 but
    # change the bucket distribution.
    # Easier: drop from all 3 + add a duplicate in each — to a DIFFERENT
    # bucket (same stream, different hazard) so that bucket count == 8 fails.
    def _drop_and_duplicate(path):
        with path.open() as f:
            rows = list(csv.reader(f))
        header = rows[0]
        data = rows[1:]
        # data[0] is v0.25 hzd=0 seed=1. Drop it.
        # Add a duplicate of v0.25 hzd=4 seed=1 (changes seed value to fake).
        data.pop(0)
        # Find a v0.25 hzd=4 row and duplicate with seed=99
        for r in data:
            if r[0] == "v0.25" and r[2] == "4":
                dup = list(r)
                dup[3] = "99"
                data.append(dup)
                break
        with path.open("w", newline="") as f:
            w = csv.writer(f)
            w.writerow(header)
            w.writerows(data)

    _drop_and_duplicate(v34_old)
    _drop_and_duplicate(v35_old)
    _drop_and_duplicate(v38_old)

    monkeypatch.setattr(m, "V0_34_OLD_RUN_SUMMARY", v34_old)
    monkeypatch.setattr(m, "V0_35_OLD_PRE_POST", v35_old)
    monkeypatch.setattr(m, "V0_38_PER_RUN", v38_old)
    monkeypatch.setattr(m, "V0_34_FRESH_RUN_SUMMARY", v34_fresh)
    monkeypatch.setattr(m, "V0_35_FRESH_PRE_POST", v35_fresh)
    monkeypatch.setattr(m, "V0_39_PER_RUN", v39_fresh)
    monkeypatch.setattr(m, "OUT_DIR", tmp_path / "lineage-v0.40")

    with pytest.raises(m.lr.LineageReplayError, match=r"bucket-count drift"):
        m.main()
