"""Tests for the v0.37 dominance-timing decomposition reducer
(``scripts/lock_in_timing_replay.py``).

Synthetic-fixture coverage of the contract committed in
[[docs/experiments/fear_hunger_v0.37.md]]:

  - Per-tick leader semantics (lowest lineage_id tie-break).
  - O1 winner_first_leader_tick: tick-0 winner==leader edge,
    sentinel n_ticks when winner never leads, mid-window case,
    leader-then-loses-and-regains case (O1 captures FIRST tick).
  - O2 leader_turnover_count_25_to_100: 0/1/3 turnover cases;
    range [0, 3].
  - O3 margin_rank1_minus_rank2_at_tick_50: tied tick-50 (margin=0),
    unique top, rank2_zero edge case (theoretical).
  - Indicator rules: monotone-pass + spread-pass / spread-fail /
    monotone-fail for each of O1, O2, O3.
  - Four-way verdict mapping over all four indicator-pair states.
  - Re-anchor halt: v0.34 mismatch, v0.35 mismatch.
  - Substrate-immutability: byte-identity of imported v0.34 / v0.35
    constants and helpers; B_POOL_ANCHORS + EXPECTED_FOUNDERS
    re-assertion.
  - End-to-end on a tmp_path 4-run synthetic corpus; halts on drift.
"""

from __future__ import annotations

import csv
import importlib.util
import json
import sys
from pathlib import Path

import pytest

_LIT_PATH = Path(__file__).parent.parent / "scripts" / "lock_in_timing_replay.py"
_spec = importlib.util.spec_from_file_location("lock_in_timing_replay", _LIT_PATH)
assert _spec is not None
assert _spec.loader is not None
lit = importlib.util.module_from_spec(_spec)
sys.modules["lock_in_timing_replay"] = lit
_spec.loader.exec_module(lit)
lr = lit.lr
ls = lit.ls


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _agent(
    *,
    agent_id: int,
    lineage_id: int,
    parent_id: int | None,
    birth_tick_normalized: int,
    death_tick: int | None,
    born_after_tick_50: bool | None = None,
    survived_to_end: bool | None = None,
    n_ticks: int = 200,
) -> lr.AgentRow:
    return lr.AgentRow(
        source_version="vX",
        arm_label="arm",
        hazard=8,
        seed=1,
        agent_id=agent_id,
        lineage_id=lineage_id,
        parent_id=parent_id,
        is_founder=parent_id is None,
        birth_tick=None if parent_id is None else birth_tick_normalized,
        birth_tick_normalized=birth_tick_normalized,
        death_tick=death_tick,
        lifespan=(n_ticks if death_tick is None else death_tick) - birth_tick_normalized,
        death_cause="" if death_tick is None else "STARVATION",
        generation_depth=0 if parent_id is None else 1,
        offspring_count=0,
        born_after_tick_50=(
            (birth_tick_normalized > 50) if born_after_tick_50 is None else born_after_tick_50
        ),
        survived_to_end=((death_tick is None) if survived_to_end is None else survived_to_end),
    )


def _five_founders() -> list[lr.AgentRow]:
    """Five founders, all alive throughout, no descendants. Births_so_far at
    every tick = 1 per lineage; leader is always lineage 0 (tie-break)."""
    return [
        _agent(
            agent_id=lineage_id + 1,
            lineage_id=lineage_id,
            parent_id=None,
            birth_tick_normalized=0,
            death_tick=None,
        )
        for lineage_id in range(5)
    ]


# ---------------------------------------------------------------------------
# Substrate immutability / locked constants
# ---------------------------------------------------------------------------


def test_v0_34_constants_match() -> None:
    assert lr.EXPECTED_FOUNDERS == 5
    assert lr.B50_THRESHOLD_TICK == 50
    assert lr.B_POOL_ANCHORS == {4: 312, 8: 321, 12: 312}
    assert lr.HAZARDS == (0, 4, 8, 12)


def test_v0_35_helpers_imported() -> None:
    """Module-level reference pins v0.35 to the imported module object."""
    assert ls is not None
    assert hasattr(ls, "compute_births_so_far")
    assert hasattr(ls, "compute_eventual_top_lineage")
    assert hasattr(ls, "is_weak_monotone_non_increasing")
    assert hasattr(ls, "is_weak_monotone_non_decreasing")
    assert hasattr(ls, "load_run_agents")


def test_reassert_b_pool_anchors_passes_on_unmodified_v0_34() -> None:
    lit.reassert_b_pool_anchors()


def test_v0_37_locked_thresholds() -> None:
    assert lit.LEADER_TICK_O3 == 50
    assert lit.O2_SNAPSHOT_TICKS == (25, 50, 75, 100)
    assert lit.O1_SPREAD_THRESHOLD == 25
    assert lit.O2_SPREAD_THRESHOLD == 0.25
    assert lit.O3_SPREAD_THRESHOLD == 1.0
    assert lit.EXPECTED_N_TICKS == 200


def test_locked_phrases_present_for_each_verdict() -> None:
    assert "Eventual-winner lock-in occurs earlier with hazard" in lit.LOCKED_H5_PHRASE
    assert "Early-leadership turnover drops with hazard" in lit.LOCKED_H6_PHRASE
    assert (
        "Both eventual-winner timing and early-leadership stability tighten" in lit.LOCKED_H7_PHRASE
    )
    assert (
        "Neither eventual-winner-timing nor early-leadership-turnover indicators separate"
        in lit.LOCKED_H8_PHRASE
    )


# ---------------------------------------------------------------------------
# leader_at_tick: lowest-lineage_id tie-break
# ---------------------------------------------------------------------------


def test_leader_at_tick_zero_is_lowest_lineage_id_under_universal_tie() -> None:
    """At tick 0, every founder has births_so_far=1; tie-break gives lineage 0."""
    rows = _five_founders()
    assert lit.leader_at_tick(rows, 0) == 0


def test_leader_at_tick_uniquely_higher_births_wins() -> None:
    """Lineage 2 has 2 births by tick 30 (founder + 1 descendant); should
    win regardless of tie-break."""
    rows = _five_founders()
    rows.append(
        _agent(agent_id=10, lineage_id=2, parent_id=3, birth_tick_normalized=20, death_tick=None)
    )
    assert lit.leader_at_tick(rows, 30) == 2


def test_leader_at_tick_changes_when_descendant_born() -> None:
    """Lineage 3 takes over at tick 25 via a descendant born at tick 25."""
    rows = _five_founders()
    rows.append(
        _agent(agent_id=10, lineage_id=3, parent_id=4, birth_tick_normalized=25, death_tick=None)
    )
    # At tick 24: still all tied, leader = 0.
    assert lit.leader_at_tick(rows, 24) == 0
    # At tick 25: lineage 3 has births_so_far = 2; wins outright.
    assert lit.leader_at_tick(rows, 25) == 3


# ---------------------------------------------------------------------------
# compute_o1: winner_first_leader_tick + sentinel
# ---------------------------------------------------------------------------


def test_compute_o1_winner_is_leader_at_tick_zero_returns_zero() -> None:
    """Winner == lineage 0 (which wins tick-0 tie-break) -> O1 = 0."""
    rows = _five_founders()
    assert lit.compute_o1(rows, winner_id=0, n_ticks=200) == 0


def test_compute_o1_winner_takes_lead_via_descendant() -> None:
    """Winner = lineage 3 takes lead at tick 25 via a descendant. O1 = 25."""
    rows = _five_founders()
    rows.append(
        _agent(agent_id=10, lineage_id=3, parent_id=4, birth_tick_normalized=25, death_tick=None)
    )
    assert lit.compute_o1(rows, winner_id=3, n_ticks=200) == 25


def test_compute_o1_sentinel_when_winner_never_leads() -> None:
    """Winner = lineage 4 has no descendants in this fixture. Lineage 0 always
    leads via tie-break. O1 = sentinel = n_ticks (= 200)."""
    rows = _five_founders()
    assert lit.compute_o1(rows, winner_id=4, n_ticks=200) == 200


def test_compute_o1_captures_first_tick_when_winner_loses_and_regains() -> None:
    """Winner = lineage 3 takes lead at tick 25, loses at tick 30 to lineage 1
    via lineage-1 descendant, regains at tick 60 via second lineage-3
    descendant. O1 = 25 (first tick), not 60."""
    rows = _five_founders()
    rows.append(
        _agent(agent_id=10, lineage_id=3, parent_id=4, birth_tick_normalized=25, death_tick=None)
    )
    rows.append(
        _agent(agent_id=11, lineage_id=1, parent_id=2, birth_tick_normalized=30, death_tick=None)
    )
    rows.append(
        _agent(agent_id=12, lineage_id=1, parent_id=2, birth_tick_normalized=40, death_tick=None)
    )
    rows.append(
        _agent(agent_id=13, lineage_id=3, parent_id=4, birth_tick_normalized=60, death_tick=None)
    )
    rows.append(
        _agent(agent_id=14, lineage_id=3, parent_id=4, birth_tick_normalized=61, death_tick=None)
    )
    assert lit.compute_o1(rows, winner_id=3, n_ticks=200) == 25


# ---------------------------------------------------------------------------
# compute_o2: leader_turnover_count_25_to_100
# ---------------------------------------------------------------------------


def test_compute_o2_zero_turnover_when_one_lineage_dominates_throughout() -> None:
    """Lineage 1 leads at every snapshot in {25, 50, 75, 100}; O2 = 0."""
    rows = _five_founders()
    # Add 4 descendants to lineage 1, all before tick 25.
    for i in range(4):
        rows.append(
            _agent(
                agent_id=20 + i,
                lineage_id=1,
                parent_id=2,
                birth_tick_normalized=10,
                death_tick=None,
            )
        )
    assert lit.compute_o2(rows) == 0


def test_compute_o2_one_turnover_25_to_50() -> None:
    """Lineage 1 leads at tick 25, lineage 2 takes over at tick 50 and holds.
    O2 = 1 (only the (25,50) pair changes)."""
    rows = _five_founders()
    # Lineage 1 leads at tick 25.
    rows.append(
        _agent(agent_id=20, lineage_id=1, parent_id=2, birth_tick_normalized=10, death_tick=None)
    )
    rows.append(
        _agent(agent_id=21, lineage_id=1, parent_id=2, birth_tick_normalized=15, death_tick=None)
    )
    # Lineage 2 catches up at tick 50 and pulls ahead.
    rows.append(
        _agent(agent_id=30, lineage_id=2, parent_id=3, birth_tick_normalized=40, death_tick=None)
    )
    rows.append(
        _agent(agent_id=31, lineage_id=2, parent_id=3, birth_tick_normalized=45, death_tick=None)
    )
    rows.append(
        _agent(agent_id=32, lineage_id=2, parent_id=3, birth_tick_normalized=49, death_tick=None)
    )
    assert lit.compute_o2(rows) == 1


def test_compute_o2_three_turnovers_full_churn() -> None:
    """Leader changes at every adjacent pair: 25 -> 50 -> 75 -> 100. O2 = 3."""
    rows = _five_founders()
    # Lineage 1 leads at 25.
    rows.append(
        _agent(agent_id=20, lineage_id=1, parent_id=2, birth_tick_normalized=10, death_tick=None)
    )
    # Lineage 2 leads at 50.
    rows.append(
        _agent(agent_id=21, lineage_id=2, parent_id=3, birth_tick_normalized=40, death_tick=None)
    )
    rows.append(
        _agent(agent_id=22, lineage_id=2, parent_id=3, birth_tick_normalized=45, death_tick=None)
    )
    # Lineage 3 leads at 75.
    rows.append(
        _agent(agent_id=23, lineage_id=3, parent_id=4, birth_tick_normalized=60, death_tick=None)
    )
    rows.append(
        _agent(agent_id=24, lineage_id=3, parent_id=4, birth_tick_normalized=65, death_tick=None)
    )
    rows.append(
        _agent(agent_id=25, lineage_id=3, parent_id=4, birth_tick_normalized=70, death_tick=None)
    )
    # Lineage 4 leads at 100.
    for tick in (80, 85, 90, 95):
        rows.append(
            _agent(
                agent_id=30 + tick,
                lineage_id=4,
                parent_id=5,
                birth_tick_normalized=tick,
                death_tick=None,
            )
        )
    assert lit.compute_o2(rows) == 3


# ---------------------------------------------------------------------------
# compute_o3: margin_rank1_minus_rank2_at_tick_50
# ---------------------------------------------------------------------------


def test_compute_o3_zero_margin_when_top_two_tied() -> None:
    """All five founders have births_so_far = 1 at tick 50; rank1 = rank2 = 1;
    margin = 0; rank2_zero_flag = False (rank2 has 1 birth)."""
    rows = _five_founders()
    r1, r2, margin, rank2_zero = lit.compute_o3(rows)
    assert r1 == 1
    assert r2 == 1
    assert margin == 0
    assert rank2_zero is False


def test_compute_o3_unique_top_with_descendants() -> None:
    """Lineage 2 has 4 descendants by tick 50 -> r1=5; rank2 has 1 (founder
    only) -> margin = 4."""
    rows = _five_founders()
    for i in range(4):
        rows.append(
            _agent(
                agent_id=20 + i,
                lineage_id=2,
                parent_id=3,
                birth_tick_normalized=10 + i,
                death_tick=None,
            )
        )
    r1, r2, margin, rank2_zero = lit.compute_o3(rows)
    assert r1 == 5
    assert r2 == 1
    assert margin == 4
    assert rank2_zero is False


def test_compute_o3_rank2_zero_flag_when_only_one_lineage_present() -> None:
    """Single-lineage corpus (theoretical edge): rank2 falls to 0; flag True."""
    rows = [
        _agent(
            agent_id=1,
            lineage_id=0,
            parent_id=None,
            birth_tick_normalized=0,
            death_tick=None,
        )
    ]
    r1, r2, margin, rank2_zero = lit.compute_o3(rows)
    assert r1 == 1
    assert r2 == 0
    assert margin == 1
    assert rank2_zero is True


# ---------------------------------------------------------------------------
# Indicator rules (O1/O2 drivers, O3 supporting)
# ---------------------------------------------------------------------------


def _per_hazard(values_by_h: dict[int, tuple[float, float, float]]) -> list[lit.PerHazardRow]:
    """Build a 4-row PerHazardRow list from {h: (mean_o1, mean_o2, mean_o3)}."""
    return [
        lit.PerHazardRow(
            hazard=h,
            n_runs=24,
            n_never_leads=0,
            n_no_winner=0,
            mean_o1=values_by_h[h][0],
            mean_o2=values_by_h[h][1],
            mean_o3=values_by_h[h][2],
        )
        for h in (0, 4, 8, 12)
    ]


def test_indicator_o1_passes_when_monotone_and_spread_meets_threshold() -> None:
    """O1 spread = 30 ticks (>= 25), strictly monotone non-increasing."""
    per_hazard = _per_hazard(
        {0: (60.0, 0.0, 0.0), 4: (50.0, 0.0, 0.0), 8: (40.0, 0.0, 0.0), 12: (30.0, 0.0, 0.0)}
    )
    indicators = lit.evaluate_indicators(per_hazard)
    o1 = next(i for i in indicators if i.observable == "O1")
    assert o1.monotone_pass is True
    assert o1.spread_value == 30.0
    assert o1.indicator_passes is True


def test_indicator_o1_fails_on_spread_when_under_threshold() -> None:
    """O1 monotone but spread = 20 ticks (< 25)."""
    per_hazard = _per_hazard(
        {0: (60.0, 0.0, 0.0), 4: (55.0, 0.0, 0.0), 8: (45.0, 0.0, 0.0), 12: (40.0, 0.0, 0.0)}
    )
    indicators = lit.evaluate_indicators(per_hazard)
    o1 = next(i for i in indicators if i.observable == "O1")
    assert o1.monotone_pass is True
    assert o1.spread_value == 20.0
    assert o1.threshold_passes is False
    assert o1.indicator_passes is False


def test_indicator_o1_fails_on_monotone_when_non_increasing_violated() -> None:
    """O1 has spread = 30 but is non-monotonic (h=8 > h=4)."""
    per_hazard = _per_hazard(
        {0: (60.0, 0.0, 0.0), 4: (40.0, 0.0, 0.0), 8: (45.0, 0.0, 0.0), 12: (30.0, 0.0, 0.0)}
    )
    indicators = lit.evaluate_indicators(per_hazard)
    o1 = next(i for i in indicators if i.observable == "O1")
    assert o1.monotone_pass is False
    assert o1.indicator_passes is False


def test_indicator_o2_passes_at_exactly_threshold() -> None:
    """O2 spread = 0.25 (== threshold)."""
    per_hazard = _per_hazard(
        {0: (0.0, 0.30, 0.0), 4: (0.0, 0.20, 0.0), 8: (0.0, 0.10, 0.0), 12: (0.0, 0.05, 0.0)}
    )
    indicators = lit.evaluate_indicators(per_hazard)
    o2 = next(i for i in indicators if i.observable == "O2")
    assert o2.monotone_pass is True
    assert o2.spread_value == pytest.approx(0.25)
    assert o2.indicator_passes is True


def test_indicator_o2_fails_under_threshold() -> None:
    """O2 monotone but spread = 0.20 (< 0.25)."""
    per_hazard = _per_hazard(
        {0: (0.0, 0.30, 0.0), 4: (0.0, 0.20, 0.0), 8: (0.0, 0.15, 0.0), 12: (0.0, 0.10, 0.0)}
    )
    indicators = lit.evaluate_indicators(per_hazard)
    o2 = next(i for i in indicators if i.observable == "O2")
    assert o2.monotone_pass is True
    assert o2.spread_value == pytest.approx(0.20)
    assert o2.indicator_passes is False


def test_indicator_o3_supporting_role_does_not_change_verdict_logic() -> None:
    """O3 passes at spread = 1.5, but role is supporting; not a verdict input."""
    per_hazard = _per_hazard(
        {0: (0.0, 0.0, 1.0), 4: (0.0, 0.0, 1.5), 8: (0.0, 0.0, 2.0), 12: (0.0, 0.0, 2.5)}
    )
    indicators = lit.evaluate_indicators(per_hazard)
    o3 = next(i for i in indicators if i.observable == "O3")
    assert o3.verdict_role == "supporting"
    assert o3.indicator_passes is True
    # No O1/O2 firing -> verdict still UNRESOLVED regardless of O3.
    verdict, _, firing = lit.evaluate_verdict(indicators)
    assert verdict == lit.VERDICT_UNRESOLVED
    assert firing == []


def test_indicator_o3_direction_is_non_decreasing_with_hazard() -> None:
    """If O3 declines with hazard, monotone_pass is False (direction inverted)."""
    per_hazard = _per_hazard(
        {0: (0.0, 0.0, 5.0), 4: (0.0, 0.0, 4.0), 8: (0.0, 0.0, 3.0), 12: (0.0, 0.0, 2.0)}
    )
    indicators = lit.evaluate_indicators(per_hazard)
    o3 = next(i for i in indicators if i.observable == "O3")
    assert o3.monotone_pass is False
    assert o3.indicator_passes is False


# ---------------------------------------------------------------------------
# Four-way verdict mapping
# ---------------------------------------------------------------------------


def _indicators(o1_passes: bool, o2_passes: bool) -> list[lit.IndicatorSummaryRow]:
    return [
        lit.IndicatorSummaryRow(
            observable="O1",
            verdict_role="driver",
            monotone_pass=o1_passes,
            spread_value=100.0 if o1_passes else 0.0,
            spread_threshold=lit.O1_SPREAD_THRESHOLD,
            threshold_passes=o1_passes,
            indicator_passes=o1_passes,
        ),
        lit.IndicatorSummaryRow(
            observable="O2",
            verdict_role="driver",
            monotone_pass=o2_passes,
            spread_value=1.0 if o2_passes else 0.0,
            spread_threshold=lit.O2_SPREAD_THRESHOLD,
            threshold_passes=o2_passes,
            indicator_passes=o2_passes,
        ),
        lit.IndicatorSummaryRow(
            observable="O3",
            verdict_role="supporting",
            monotone_pass=True,
            spread_value=2.0,
            spread_threshold=lit.O3_SPREAD_THRESHOLD,
            threshold_passes=True,
            indicator_passes=True,
        ),
    ]


def test_verdict_h5_when_o1_passes_o2_fails() -> None:
    verdict, phrase, firing = lit.evaluate_verdict(_indicators(True, False))
    assert verdict == lit.VERDICT_EARLIER
    assert phrase == lit.LOCKED_H5_PHRASE
    assert firing == ["O1"]


def test_verdict_h6_when_o2_passes_o1_fails() -> None:
    verdict, phrase, firing = lit.evaluate_verdict(_indicators(False, True))
    assert verdict == lit.VERDICT_STABLER
    assert phrase == lit.LOCKED_H6_PHRASE
    assert firing == ["O2"]


def test_verdict_h7_when_both_pass() -> None:
    verdict, phrase, firing = lit.evaluate_verdict(_indicators(True, True))
    assert verdict == lit.VERDICT_COMPOUND
    assert phrase == lit.LOCKED_H7_PHRASE
    assert firing == ["O1", "O2"]


def test_verdict_h8_when_neither_passes() -> None:
    verdict, phrase, firing = lit.evaluate_verdict(_indicators(False, False))
    assert verdict == lit.VERDICT_UNRESOLVED
    assert phrase == lit.LOCKED_H8_PHRASE
    assert firing == []


# ---------------------------------------------------------------------------
# Re-anchor halt
# ---------------------------------------------------------------------------


def test_cross_check_double_anchor_passes_on_match() -> None:
    derived = {("vX", "arm-0", 1): 2}
    v34 = {("vX", "arm-0", 1): 2}
    v35 = {("vX", "arm-0", 1): 2}
    lit.cross_check_double_anchor(derived, v34, v35)


def test_cross_check_halts_on_v0_34_mismatch() -> None:
    derived = {("vX", "arm-0", 1): 2}
    v34 = {("vX", "arm-0", 1): 3}  # mismatch
    v35 = {("vX", "arm-0", 1): 2}
    with pytest.raises(lr.LineageReplayError, match=r"H2a v0\.34 re-anchor mismatch"):
        lit.cross_check_double_anchor(derived, v34, v35)


def test_cross_check_halts_on_v0_35_mismatch() -> None:
    derived = {("vX", "arm-0", 1): 2}
    v34 = {("vX", "arm-0", 1): 2}
    v35 = {("vX", "arm-0", 1): 4}  # mismatch
    with pytest.raises(lr.LineageReplayError, match=r"H2b v0\.35 re-anchor mismatch"):
        lit.cross_check_double_anchor(derived, v34, v35)


def test_cross_check_halts_on_missing_v0_34_anchor() -> None:
    derived = {("vX", "arm-0", 1): 2}
    v34: dict[tuple[str, str, int], int | None] = {}  # missing
    v35 = {("vX", "arm-0", 1): 2}
    with pytest.raises(lr.LineageReplayError, match=r"v0\.34 anchor missing"):
        lit.cross_check_double_anchor(derived, v34, v35)


def test_load_v0_34_anchors_round_trip(tmp_path) -> None:
    path = tmp_path / "run_summary.csv"
    with path.open("w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(
            [
                "source_version",
                "arm_label",
                "hazard",
                "seed",
                "total_b50",
                "top_lineage_id",
                "top_lineage_b50",
                "top_lineage_b50_share",
                "n_lineages_with_b50_ge_1",
                "n_lineages_alive_at_end",
            ]
        )
        writer.writerow(["vX", "arm-0", 0, 1, 5, 2, 3, 0.6, 3, 5])
        writer.writerow(["vX", "arm-0", 0, 2, 0, "", "", "", 0, 5])
    anchors = lit.load_v0_34_anchors(path)
    assert anchors[("vX", "arm-0", 1)] == 2
    assert anchors[("vX", "arm-0", 2)] is None


def test_load_v0_34_anchors_halts_on_missing_file(tmp_path) -> None:
    with pytest.raises(lr.LineageReplayError, match=r"v0\.34 run_summary\.csv missing"):
        lit.load_v0_34_anchors(tmp_path / "does-not-exist.csv")


def test_load_v0_35_anchors_halts_on_missing_file(tmp_path) -> None:
    with pytest.raises(lr.LineageReplayError, match=r"v0\.35 pre_post_dominance\.csv missing"):
        lit.load_v0_35_anchors(tmp_path / "does-not-exist.csv")


# ---------------------------------------------------------------------------
# End-to-end on tmp_path synthetic corpus
# ---------------------------------------------------------------------------


def _write_synthetic_run(
    run_dir: Path,
    *,
    seed: int,
    hazard: int,
    n_ticks: int,
    agents: list[dict],
) -> None:
    run_dir.mkdir(parents=True, exist_ok=True)
    (run_dir / "config.json").write_text(
        json.dumps({"world": {"seed": seed, "hazard_damage_default": hazard}})
    )
    (run_dir / "manifest.json").write_text(json.dumps({"ticks_completed": n_ticks}))
    with (run_dir / "agent_lifetimes.csv").open("w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(
            [
                "agent_id",
                "lineage_id",
                "parent_id",
                "birth_tick",
                "death_tick",
                "death_cause",
                "offspring_count",
            ]
        )
        for a in agents:
            writer.writerow(
                [
                    a["agent_id"],
                    a.get("lineage_id", ""),
                    a.get("parent_id", "") if a.get("parent_id") is not None else "",
                    a.get("birth_tick", "") if a.get("birth_tick") is not None else "",
                    a.get("death_tick", "") if a.get("death_tick") is not None else "",
                    a.get("death_cause", ""),
                    a.get("offspring_count", 0),
                ]
            )


def _five_founder_run_records(*, dominant_lineage: int) -> list[dict]:
    """5 founders + 6 post-50 descendants of `dominant_lineage`."""
    records: list[dict] = []
    next_id = 1
    for lineage_id in range(5):
        records.append(
            {
                "agent_id": next_id,
                "lineage_id": lineage_id,
                "parent_id": None,
                "birth_tick": None,
                "death_tick": None,
                "death_cause": "",
                "offspring_count": 6 if lineage_id == dominant_lineage else 0,
            }
        )
        next_id += 1
    for _ in range(6):
        records.append(
            {
                "agent_id": next_id,
                "lineage_id": dominant_lineage,
                "parent_id": dominant_lineage + 1,
                "birth_tick": 100,
                "death_tick": None,
                "death_cause": "",
                "offspring_count": 0,
            }
        )
        next_id += 1
    return records


def test_summarise_run_end_to_end_produces_expected_per_run_row(tmp_path) -> None:
    run_dir = tmp_path / "v0.test" / "transfer-1500-hzd0-influx-1.0" / "seed-1"
    _write_synthetic_run(
        run_dir,
        seed=1,
        hazard=0,
        n_ticks=200,
        agents=_five_founder_run_records(dominant_lineage=2),
    )
    row = lit.summarise_run("v0.test", "transfer-1500-hzd0-influx-1.0", 0, 1, run_dir)
    assert row.eventual_top_lineage_id == 2
    assert row.n_ticks == 200
    # Lineage 0 leads tick 0..99 by tie-break (all founders == 1 birth);
    # Lineage 2 takes leadership at tick 100 when first descendant born.
    # O1 = 100 (winner first becomes leader at tick 100).
    assert row.o1_winner_first_leader_tick == 100
    # O2 snapshot ticks {25, 50, 75, 100}: leaders are 0, 0, 0, 2 -> 1 turnover.
    assert row.o2_leader_turnover_count_25_to_100 == 1
    # At tick 50, all founders tied at 1 birth -> O3 margin = 0.
    assert row.o3_margin == 0
    assert row.never_leads_flag is False


def test_summarise_run_halts_on_n_ticks_drift(tmp_path) -> None:
    run_dir = tmp_path / "v0.test" / "transfer-1500-hzd0-influx-1.0" / "seed-1"
    _write_synthetic_run(
        run_dir,
        seed=1,
        hazard=0,
        n_ticks=150,  # not 200
        agents=_five_founder_run_records(dominant_lineage=2),
    )
    with pytest.raises(lr.LineageReplayError, match="H2d n_ticks drift"):
        lit.summarise_run("v0.test", "transfer-1500-hzd0-influx-1.0", 0, 1, run_dir)


# ---------------------------------------------------------------------------
# Per-hazard aggregation
# ---------------------------------------------------------------------------


def test_aggregate_per_hazard_means_match_synthetic_corpus() -> None:
    """Build 2-runs-per-hazard PerRunRow list with known per-run values; check
    aggregations are arithmetic means."""
    per_run: list[lit.PerRunRow] = []
    for hazard in (0, 4, 8, 12):
        for seed in (1, 2):
            per_run.append(
                lit.PerRunRow(
                    source_version="vX",
                    arm_label=f"arm-{hazard}",
                    hazard=hazard,
                    seed=seed,
                    n_ticks=200,
                    eventual_top_lineage_id=0,
                    o1_winner_first_leader_tick=10 if seed == 1 else 30,
                    o2_leader_turnover_count_25_to_100=1 if seed == 1 else 0,
                    o3_rank1_births=5,
                    o3_rank2_births=2,
                    o3_margin=3,
                    never_leads_flag=False,
                    rank2_zero_flag=False,
                    L25=0,
                    L50=0,
                    L75=0,
                    L100=0,
                )
            )
    summary = lit.aggregate_per_hazard(per_run)
    by_hazard = {row.hazard: row for row in summary}
    for hazard in (0, 4, 8, 12):
        assert by_hazard[hazard].n_runs == 2
        assert by_hazard[hazard].mean_o1 == 20.0  # (10 + 30) / 2
        assert by_hazard[hazard].mean_o2 == 0.5  # (1 + 0) / 2
        assert by_hazard[hazard].mean_o3 == 3.0
