"""v0.39 leader_advantage_fresh_replay reducer tests.

Coverage:
  - Locked constants (LEADER_TICK, SPREAD_THRESHOLD, paths, expected counts).
  - Sealed-artifact halt (H2c/H2d): missing v0.34 / v0.35 OLD outputs.
  - Fresh-anchor-presence halt: missing v0.34-fresh / v0.35-fresh.
  - Per-run cross-anchor halt (H2a/H2b).
  - Three-way fresh verdict (H5/H6/H7).
  - Three-way pooled verdict (H5/H6/H7).
  - Combined classification lookup (all 6 reachable cells + 1 halt cell).
  - Locked-phrase identity.
  - End-to-end fixture (synthetic).
"""

from __future__ import annotations

import csv
import importlib.util
import sys
from pathlib import Path

import pytest


def _load_v0_39():
    path = (
        Path(__file__).resolve().parents[1] / "scripts" / "v0_39_leader_advantage_fresh_replay.py"
    )
    spec = importlib.util.spec_from_file_location("v0_39_leader_advantage_fresh_replay", path)
    assert spec is not None
    assert spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    sys.modules["v0_39_leader_advantage_fresh_replay"] = mod
    spec.loader.exec_module(mod)
    return mod


# ---------------------------------------------------------------------------
# Locked constants
# ---------------------------------------------------------------------------


def test_locked_constants():
    m = _load_v0_39()
    assert m.LEADER_TICK == 50
    assert m.N_NON_LEADERS == 4
    assert m.EXPECTED_N_TICKS == 200
    assert m.SPREAD_THRESHOLD == 1.5
    assert tuple(range(25, 33)) == m.FRESH_SEEDS
    assert m.EXPECTED_OLD_ROW_COUNT == 96
    assert m.EXPECTED_FRESH_ROW_COUNT == 32


def test_locked_paths():
    m = _load_v0_39()
    assert Path("runs/lineage-v0.34/run_summary.csv") == m.V0_34_OLD_RUN_SUMMARY
    assert Path("runs/lineage-v0.35/pre_post_dominance.csv") == m.V0_35_OLD_PRE_POST
    assert Path("runs/lineage-v0.34-fresh/run_summary.csv") == m.V0_34_FRESH_RUN_SUMMARY
    assert Path("runs/lineage-v0.35-fresh/pre_post_dominance.csv") == m.V0_35_FRESH_PRE_POST
    assert Path("runs/lineage-v0.38/per_run.csv") == m.V0_38_PER_RUN
    assert Path("runs/lineage-v0.39") == m.OUT_DIR


def test_locked_phrases_present():
    m = _load_v0_39()
    assert "fresh seed stream (25..32)" in m.LOCKED_H5_FRESH_AND_POOLED_PHRASE
    assert "cross-stream reproducible" in m.LOCKED_H5_FRESH_AND_POOLED_PHRASE
    assert "Not a mechanism declaration." in m.LOCKED_H5_FRESH_AND_POOLED_PHRASE
    assert "not reproduced on the fresh" in m.LOCKED_H5_POOLED_ONLY_PHRASE
    assert "not reproduced" in m.LOCKED_NEITHER_H5_PHRASE
    assert "directionally contradicted" in m.LOCKED_H7_FRESH_HEADLINE_PHRASE


# ---------------------------------------------------------------------------
# Sealed-artifact halts
# ---------------------------------------------------------------------------


def _make_csv(path: Path, header: list[str], rows: list[list[str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as f:
        w = csv.writer(f)
        w.writerow(header)
        for r in rows:
            w.writerow(r)


def test_assert_old_corpus_sealed_halts_on_missing(monkeypatch, tmp_path):
    m = _load_v0_39()
    monkeypatch.setattr(m, "V0_34_OLD_RUN_SUMMARY", tmp_path / "missing34.csv")
    with pytest.raises(m.lr.LineageReplayError, match=r"v0\.34 old run_summary missing"):
        m.assert_old_corpus_sealed()


def test_assert_old_corpus_sealed_halts_on_row_count_drift(monkeypatch, tmp_path):
    m = _load_v0_39()
    bad_path_34 = tmp_path / "bad34.csv"
    _make_csv(bad_path_34, ["source_version", "arm_label", "seed"], [["v0.25", "x", "1"]])
    monkeypatch.setattr(m, "V0_34_OLD_RUN_SUMMARY", bad_path_34)
    monkeypatch.setattr(m, "V0_35_OLD_PRE_POST", bad_path_34)
    with pytest.raises(m.lr.LineageReplayError, match="row-count drift"):
        m.assert_old_corpus_sealed()


def test_assert_fresh_anchors_present_halts_on_missing(monkeypatch, tmp_path):
    m = _load_v0_39()
    monkeypatch.setattr(m, "V0_34_FRESH_RUN_SUMMARY", tmp_path / "missing.csv")
    with pytest.raises(m.lr.LineageReplayError, match="missing at"):
        m.assert_fresh_anchors_present()


def test_assert_fresh_anchors_present_halts_on_row_count_drift(monkeypatch, tmp_path):
    m = _load_v0_39()
    bad = tmp_path / "bad.csv"
    _make_csv(bad, ["source_version", "arm_label", "seed"], [["v0.39", "x", "25"]])
    monkeypatch.setattr(m, "V0_34_FRESH_RUN_SUMMARY", bad)
    monkeypatch.setattr(m, "V0_35_FRESH_PRE_POST", bad)
    with pytest.raises(m.lr.LineageReplayError, match="row-count drift"):
        m.assert_fresh_anchors_present()


# ---------------------------------------------------------------------------
# Anchor loaders
# ---------------------------------------------------------------------------


def test_load_v0_38_per_run_halts_on_missing(monkeypatch, tmp_path):
    m = _load_v0_39()
    monkeypatch.setattr(m, "V0_38_PER_RUN", tmp_path / "missing.csv")
    with pytest.raises(m.lr.LineageReplayError, match=r"v0\.38 per_run.csv missing"):
        m.load_v0_38_per_run_leader_advantage()


def test_load_v0_38_per_run_halts_on_row_count_drift(monkeypatch, tmp_path):
    m = _load_v0_39()
    bad = tmp_path / "bad.csv"
    _make_csv(
        bad,
        ["source_version", "arm_label", "hazard", "seed", "leader_advantage"],
        [["v0.25", "x", "0", "1", "3.5"]],
    )
    monkeypatch.setattr(m, "V0_38_PER_RUN", bad)
    with pytest.raises(m.lr.LineageReplayError, match="sealed artifact has drifted"):
        m.load_v0_38_per_run_leader_advantage()


# ---------------------------------------------------------------------------
# Cross-anchor halt
# ---------------------------------------------------------------------------


def _make_per_run(
    la_module,
    *,
    source_version: str = "v0.39",
    arm_label: str = "transfer-1500-hzd0-influx-1.0",
    hazard: int = 0,
    seed: int = 25,
    leader_lineage_id: int = 0,
    eventual_top_lineage_id: int | None = 0,
    leader_advantage: float = 3.0,
    wad_flag: bool = True,
):
    return la_module.PerRunRow(
        source_version=source_version,
        arm_label=arm_label,
        hazard=hazard,
        seed=seed,
        n_ticks=200,
        leader_lineage_id=leader_lineage_id,
        eventual_top_lineage_id=eventual_top_lineage_id,
        wad_flag=wad_flag,
        b50_lineage_0=0,
        b50_lineage_1=0,
        b50_lineage_2=0,
        b50_lineage_3=0,
        b50_lineage_4=0,
        leader_b50=10,
        non_leader_mean_b50=7.0,
        leader_advantage=leader_advantage,
        winner_b50=10,
        winner_overtake=0,
    )


def test_cross_anchor_halts_on_missing_v0_34_key():
    m = _load_v0_39()
    row = _make_per_run(m.la, seed=99)  # not in anchor dict
    v34 = {("v0.39", "transfer-1500-hzd0-influx-1.0", 25): 0}
    v35 = {("v0.39", "transfer-1500-hzd0-influx-1.0", 25): (0, 0)}
    with pytest.raises(m.lr.LineageReplayError, match=r"v0\.34-fresh anchor missing"):
        m.cross_anchor_fresh_run(row, v34, v35)


def test_cross_anchor_halts_on_missing_v0_35_key():
    m = _load_v0_39()
    row = _make_per_run(m.la, seed=25)
    v34 = {("v0.39", "transfer-1500-hzd0-influx-1.0", 25): 0}
    v35 = {("v0.39", "transfer-1500-hzd0-influx-1.0", 99): (0, 0)}
    with pytest.raises(m.lr.LineageReplayError, match=r"v0\.35-fresh anchor missing"):
        m.cross_anchor_fresh_run(row, v34, v35)


def test_cross_anchor_halts_on_v0_34_top_id_mismatch():
    m = _load_v0_39()
    row = _make_per_run(m.la, eventual_top_lineage_id=0)
    v34 = {("v0.39", "transfer-1500-hzd0-influx-1.0", 25): 1}  # disagrees
    v35 = {("v0.39", "transfer-1500-hzd0-influx-1.0", 25): (0, 0)}
    with pytest.raises(m.lr.LineageReplayError, match=r"v0\.34-fresh re-anchor mismatch"):
        m.cross_anchor_fresh_run(row, v34, v35)


def test_cross_anchor_halts_on_v0_35_leader_mismatch():
    m = _load_v0_39()
    row = _make_per_run(m.la, leader_lineage_id=0, eventual_top_lineage_id=0)
    v34 = {("v0.39", "transfer-1500-hzd0-influx-1.0", 25): 0}
    v35 = {("v0.39", "transfer-1500-hzd0-influx-1.0", 25): (3, 0)}  # leader disagrees
    with pytest.raises(m.lr.LineageReplayError, match=r"v0\.35-fresh re-anchor mismatch"):
        m.cross_anchor_fresh_run(row, v34, v35)


def test_cross_anchor_halts_on_v0_35_eventual_mismatch():
    m = _load_v0_39()
    row = _make_per_run(m.la, leader_lineage_id=0, eventual_top_lineage_id=0)
    v34 = {("v0.39", "transfer-1500-hzd0-influx-1.0", 25): 0}
    v35 = {("v0.39", "transfer-1500-hzd0-influx-1.0", 25): (0, 3)}  # eventual disagrees
    with pytest.raises(m.lr.LineageReplayError, match=r"v0\.35-fresh re-anchor mismatch"):
        m.cross_anchor_fresh_run(row, v34, v35)


def test_cross_anchor_passes_on_clean_match():
    m = _load_v0_39()
    row = _make_per_run(m.la, leader_lineage_id=2, eventual_top_lineage_id=2)
    v34 = {("v0.39", "transfer-1500-hzd0-influx-1.0", 25): 2}
    v35 = {("v0.39", "transfer-1500-hzd0-influx-1.0", 25): (2, 2)}
    m.cross_anchor_fresh_run(row, v34, v35)  # no raise


# ---------------------------------------------------------------------------
# Aggregation
# ---------------------------------------------------------------------------


def test_aggregate_per_hazard_fresh_groups_by_hazard():
    m = _load_v0_39()
    rows = [
        _make_per_run(m.la, hazard=0, seed=25, leader_advantage=2.0),
        _make_per_run(m.la, hazard=0, seed=26, leader_advantage=4.0),
        _make_per_run(m.la, hazard=12, seed=25, leader_advantage=8.0),
    ]
    out = m.aggregate_per_hazard_fresh(rows)
    by_h = {r.hazard: r for r in out}
    assert by_h[0].n_runs == 2
    assert by_h[0].mean_leader_advantage == 3.0
    assert by_h[12].n_runs == 1
    assert by_h[12].mean_leader_advantage == 8.0
    assert by_h[4].n_runs == 0
    assert by_h[8].n_runs == 0


def test_aggregate_per_hazard_fresh_counts_wad():
    m = _load_v0_39()
    rows = [
        _make_per_run(m.la, hazard=0, seed=25, wad_flag=True),
        _make_per_run(m.la, hazard=0, seed=26, wad_flag=False),
        _make_per_run(m.la, hazard=0, seed=27, wad_flag=True),
    ]
    out = m.aggregate_per_hazard_fresh(rows)
    by_h = {r.hazard: r for r in out}
    assert by_h[0].n_wad_true == 2


def test_aggregate_per_hazard_pooled_combines_old_and_fresh():
    m = _load_v0_39()
    fresh = [
        _make_per_run(m.la, hazard=0, seed=25, leader_advantage=10.0),
        _make_per_run(m.la, hazard=0, seed=26, leader_advantage=10.0),
    ]
    old = {
        ("v0.25", "transfer-1500-hzd0-influx-1.0", 1): (0, 4.0),
        ("v0.25", "transfer-1500-hzd0-influx-1.0", 2): (0, 4.0),
    }
    out = m.aggregate_per_hazard_pooled(fresh, old)
    by_h = {r.hazard: r for r in out}
    assert by_h[0].n_runs == 4
    assert by_h[0].n_old == 2
    assert by_h[0].n_fresh == 2
    assert by_h[0].mean_leader_advantage == 7.0  # (4+4+10+10)/4


# ---------------------------------------------------------------------------
# Three-way verdict logic
# ---------------------------------------------------------------------------


def _fresh_rows(m, means: list[float]):
    return [
        m.PerHazardFreshRow(hazard=h, n_runs=8, n_wad_true=0, mean_leader_advantage=mu)
        for h, mu in zip((0, 4, 8, 12), means, strict=True)
    ]


def _pooled_rows(m, means: list[float]):
    return [
        m.PerHazardPooledRow(hazard=h, n_runs=32, n_old=24, n_fresh=8, mean_leader_advantage=mu)
        for h, mu in zip((0, 4, 8, 12), means, strict=True)
    ]


def test_evaluate_fresh_h5_fires_on_monotone_up_and_spread():
    m = _load_v0_39()
    rows = _fresh_rows(m, [3.0, 5.0, 7.0, 5.0])
    # 3->5->7 up but 7->5 down: not strict non-decreasing
    v = m.evaluate_fresh_verdict(rows)
    assert v.verdict == m.VERDICT_H6_FRESH

    rows = _fresh_rows(m, [3.0, 5.0, 7.0, 9.0])  # monotone-up; spread = +6 >= 1.5
    v = m.evaluate_fresh_verdict(rows)
    assert v.verdict == m.VERDICT_H5_FRESH
    assert v.monotone_pass_up
    assert v.spread_value == pytest.approx(6.0)
    assert v.threshold_passes_up


def test_evaluate_fresh_h6_fires_on_neither():
    m = _load_v0_39()
    rows = _fresh_rows(m, [3.0, 4.0, 3.5, 4.0])  # spread +1.0 < 1.5; not monotone strictly
    v = m.evaluate_fresh_verdict(rows)
    assert v.verdict == m.VERDICT_H6_FRESH


def test_evaluate_fresh_h7_fires_on_monotone_down_and_reverse_spread():
    m = _load_v0_39()
    rows = _fresh_rows(m, [10.0, 7.0, 5.0, 3.0])
    v = m.evaluate_fresh_verdict(rows)
    assert v.verdict == m.VERDICT_H7_FRESH
    assert v.monotone_pass_down
    assert v.spread_value == pytest.approx(-7.0)
    assert v.threshold_passes_down


def test_evaluate_fresh_spread_at_threshold_exactly_passes():
    m = _load_v0_39()
    rows = _fresh_rows(m, [3.0, 4.0, 4.0, 4.5])  # spread = 1.5; monotone up
    v = m.evaluate_fresh_verdict(rows)
    assert v.verdict == m.VERDICT_H5_FRESH


def test_evaluate_fresh_h6_on_nan_means():
    m = _load_v0_39()
    import math

    rows = _fresh_rows(m, [3.0, math.nan, 5.0, 7.0])
    v = m.evaluate_fresh_verdict(rows)
    assert v.verdict == m.VERDICT_H6_FRESH
    assert math.isnan(v.spread_value)


def test_evaluate_pooled_three_way():
    m = _load_v0_39()
    rows = _pooled_rows(m, [4.0, 7.0, 8.0, 9.0])
    v = m.evaluate_pooled_verdict(rows)
    assert v.verdict == m.VERDICT_H5_POOLED

    rows = _pooled_rows(m, [4.0, 4.5, 4.7, 4.8])  # spread 0.8 < 1.5
    v = m.evaluate_pooled_verdict(rows)
    assert v.verdict == m.VERDICT_H6_POOLED


# ---------------------------------------------------------------------------
# Combined classification
# ---------------------------------------------------------------------------


def _verdict(m, name: str):
    """Helper: synthesise a VerdictRow with just the verdict id set."""
    return m.VerdictRow(
        verdict=name,
        locked_phrase="",
        monotone_pass_up=False,
        monotone_pass_down=False,
        spread_value=0.0,
        spread_threshold=1.5,
        threshold_passes_up=False,
        threshold_passes_down=False,
    )


def test_combined_h5_fresh_and_pooled():
    m = _load_v0_39()
    out = m.evaluate_combined_classification(
        _verdict(m, m.VERDICT_H5_FRESH),
        _verdict(m, m.VERDICT_H5_POOLED),
    )
    assert out.combined_classification == m.COMBINED_H5_FRESH_AND_POOLED
    assert out.headline_locked_phrase == m.LOCKED_H5_FRESH_AND_POOLED_PHRASE


def test_combined_h5_fresh_only():
    m = _load_v0_39()
    out = m.evaluate_combined_classification(
        _verdict(m, m.VERDICT_H5_FRESH),
        _verdict(m, m.VERDICT_H6_POOLED),
    )
    assert out.combined_classification == m.COMBINED_H5_FRESH_ONLY
    assert out.headline_locked_phrase == m.LOCKED_H5_FRESH_ONLY_PHRASE


def test_combined_h5_pooled_only():
    m = _load_v0_39()
    out = m.evaluate_combined_classification(
        _verdict(m, m.VERDICT_H6_FRESH),
        _verdict(m, m.VERDICT_H5_POOLED),
    )
    assert out.combined_classification == m.COMBINED_H5_POOLED_ONLY
    assert out.headline_locked_phrase == m.LOCKED_H5_POOLED_ONLY_PHRASE


def test_combined_neither_h5():
    m = _load_v0_39()
    out = m.evaluate_combined_classification(
        _verdict(m, m.VERDICT_H6_FRESH),
        _verdict(m, m.VERDICT_H6_POOLED),
    )
    assert out.combined_classification == m.COMBINED_NEITHER_H5
    assert out.headline_locked_phrase == m.LOCKED_NEITHER_H5_PHRASE


def test_combined_h6_fresh_pooled_down():
    m = _load_v0_39()
    out = m.evaluate_combined_classification(
        _verdict(m, m.VERDICT_H6_FRESH),
        _verdict(m, m.VERDICT_H7_POOLED),
    )
    assert out.combined_classification == m.COMBINED_H6_FRESH_POOLED_DOWN


def test_combined_h7_fresh_headline():
    m = _load_v0_39()
    for pooled in (m.VERDICT_H5_POOLED, m.VERDICT_H6_POOLED, m.VERDICT_H7_POOLED):
        out = m.evaluate_combined_classification(
            _verdict(m, m.VERDICT_H7_FRESH),
            _verdict(m, pooled),
        )
        assert out.combined_classification == m.COMBINED_H7_FRESH


def test_combined_halts_on_h5_fresh_x_h7_pooled():
    """Structurally near-impossible. Halt and investigate."""
    m = _load_v0_39()
    with pytest.raises(m.lr.LineageReplayError, match="structurally"):
        m.evaluate_combined_classification(
            _verdict(m, m.VERDICT_H5_FRESH),
            _verdict(m, m.VERDICT_H7_POOLED),
        )


# ---------------------------------------------------------------------------
# Integration: locked phrase exact-string lookup
# ---------------------------------------------------------------------------


def test_h5_pooled_only_phrase_matches_locked():
    """Regression guard: the headline phrase must remain verbatim."""
    m = _load_v0_39()
    out = m.evaluate_combined_classification(
        _verdict(m, m.VERDICT_H6_FRESH),
        _verdict(m, m.VERDICT_H5_POOLED),
    )
    assert out.headline_locked_phrase == (
        "The fresh seed stream (25..32) does not show monotone-up + "
        "spread->=1.5 on mean_leader_advantage. The pooled 128-run effect "
        "persists on the strength of the 96 old runs alone. v0.38's H5 "
        "LEADER-ADVANTAGE-AMPLIFIED is not reproduced on the fresh "
        "stream; it remains a same-corpus correlational finding pending "
        "further calibration."
    )
