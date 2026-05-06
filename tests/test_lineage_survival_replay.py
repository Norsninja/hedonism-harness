"""Tests for the v0.35 founder survival timing reducer
(``scripts/lineage_survival_replay.py``).

Synthetic-fixture coverage of the contract committed in
[[docs/experiments/fear_hunger_v0.35.md]]:

  - Snapshot-tick semantics: half-open interval
    [birth_tick_normalized, death_tick or n_ticks).
  - Tick-0 founder-active invariant (H2c): all 5 founders active at T=0.
  - Extinction tick: max(death_tick) when all members dead; None when
    any member is extant.
  - Births so far at T: counts members with birth_tick_normalized <= T;
    founders count.
  - Leader at tick 50: max births_so_far with lowest lineage_id tie-break.
  - Eventual top lineage: matches v0.34's summarise_run algorithm; lowest
    lineage_id tie-break; (None, None) when total_b50 == 0.
  - winner_already_dominant_at_tick_50: leader == eventual_top; None
    when eventual_top is None.
  - Pruning indicator: monotone non-increasing + spread >= 0.5.
  - Expansion indicator: monotone non-decreasing + spread >= 0.15.
  - Three-way verdict mapping over all four indicator-pair states.
  - End-to-end on a tmp_path 5-run synthetic corpus; halts on
    re-anchor drift; halts on founder count != 5.
  - v0.34 helper imports succeed; constants byte-match.
"""

from __future__ import annotations

import csv
import importlib.util
import json
import sys
from pathlib import Path

import pytest

_LSR_PATH = Path(__file__).parent.parent / "scripts" / "lineage_survival_replay.py"
_spec = importlib.util.spec_from_file_location("lineage_survival_replay", _LSR_PATH)
assert _spec is not None
assert _spec.loader is not None
lsr = importlib.util.module_from_spec(_spec)
sys.modules["lineage_survival_replay"] = lsr
_spec.loader.exec_module(lsr)
lr = lsr.lr


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


# ---------------------------------------------------------------------------
# v0.34 helper imports / anchors
# ---------------------------------------------------------------------------


def test_v0_34_constants_match() -> None:
    """v0.34's locked constants must remain byte-identical at v0.35
    reducer entry."""
    assert lr.EXPECTED_FOUNDERS == 5
    assert lr.B50_THRESHOLD_TICK == 50
    assert lr.SINGLE_LINEAGE_MAJORITY_THRESHOLD == 0.5
    assert lr.B_POOL_ANCHORS == {4: 312, 8: 321, 12: 312}
    assert lr.HAZARDS == (0, 4, 8, 12)


def test_reassert_b_pool_anchors_passes_on_unmodified_v0_34() -> None:
    lsr.reassert_b_pool_anchors()


def test_v0_35_locked_thresholds() -> None:
    assert lsr.SNAPSHOT_TICKS == (0, 25, 50, 75, 100, 150, 200)
    assert lsr.LEADER_TICK == 50
    assert lsr.PRUNING_FOUNDER_SPREAD_THRESHOLD == 0.5
    assert lsr.EXPANSION_RATE_SPREAD_THRESHOLD == 0.15


def test_locked_h7_phrase_present() -> None:
    expected_substr = "Late-window concentration is consistent with both pruning and expansion"
    assert expected_substr in lsr.LOCKED_H7_PHRASE


# ---------------------------------------------------------------------------
# Snapshot-tick semantics: half-open interval
# ---------------------------------------------------------------------------


def test_active_at_tick_lower_bound_inclusive() -> None:
    a = _agent(agent_id=1, lineage_id=0, parent_id=None, birth_tick_normalized=10, death_tick=50)
    assert lsr.compute_founder_active_at_tick([a], 10, n_ticks=200) is True


def test_active_at_tick_upper_bound_exclusive() -> None:
    a = _agent(agent_id=1, lineage_id=0, parent_id=None, birth_tick_normalized=10, death_tick=50)
    assert lsr.compute_founder_active_at_tick([a], 50, n_ticks=200) is False
    assert lsr.compute_founder_active_at_tick([a], 49, n_ticks=200) is True


def test_active_before_birth_returns_false() -> None:
    a = _agent(agent_id=1, lineage_id=0, parent_id=None, birth_tick_normalized=10, death_tick=50)
    assert lsr.compute_founder_active_at_tick([a], 9, n_ticks=200) is False


def test_active_for_extant_agent_uses_n_ticks_as_upper() -> None:
    a = _agent(agent_id=1, lineage_id=0, parent_id=None, birth_tick_normalized=0, death_tick=None)
    assert lsr.compute_founder_active_at_tick([a], 199, n_ticks=200) is True
    assert lsr.compute_founder_active_at_tick([a], 200, n_ticks=200) is False


def test_active_lineage_with_descendant_overlapping_gap() -> None:
    """Founder dies at tick 30; descendant born tick 40 lives to end —
    lineage is active at both T=20 (founder) and T=100 (descendant) but
    NOT at T=35 (gap)."""
    founder = _agent(
        agent_id=1, lineage_id=0, parent_id=None, birth_tick_normalized=0, death_tick=30
    )
    descendant = _agent(
        agent_id=2, lineage_id=0, parent_id=1, birth_tick_normalized=40, death_tick=None
    )
    members = [founder, descendant]
    assert lsr.compute_founder_active_at_tick(members, 20, n_ticks=200) is True
    assert lsr.compute_founder_active_at_tick(members, 35, n_ticks=200) is False
    assert lsr.compute_founder_active_at_tick(members, 100, n_ticks=200) is True


def test_n_alive_in_lineage_counts_overlap() -> None:
    a = _agent(agent_id=1, lineage_id=0, parent_id=None, birth_tick_normalized=0, death_tick=100)
    b = _agent(agent_id=2, lineage_id=0, parent_id=1, birth_tick_normalized=50, death_tick=150)
    c = _agent(agent_id=3, lineage_id=0, parent_id=2, birth_tick_normalized=120, death_tick=None)
    members = [a, b, c]
    # T=75: a alive (0<=75<100), b alive (50<=75<150), c not yet born.
    assert lsr.compute_n_alive_in_lineage(members, 75, n_ticks=200) == 2
    # T=130: a dead, b alive (50<=130<150), c alive (120<=130<200).
    assert lsr.compute_n_alive_in_lineage(members, 130, n_ticks=200) == 2


# ---------------------------------------------------------------------------
# Births so far / extinction tick / last birth tick
# ---------------------------------------------------------------------------


def test_births_so_far_counts_founder_at_tick_zero() -> None:
    founder = _agent(
        agent_id=1, lineage_id=0, parent_id=None, birth_tick_normalized=0, death_tick=None
    )
    assert lsr.compute_births_so_far([founder], 0) == 1
    assert lsr.compute_births_so_far([founder], 50) == 1


def test_births_so_far_counts_pre_50_descendants_only() -> None:
    members = [
        _agent(agent_id=1, lineage_id=0, parent_id=None, birth_tick_normalized=0, death_tick=None),
        _agent(agent_id=2, lineage_id=0, parent_id=1, birth_tick_normalized=30, death_tick=None),
        _agent(agent_id=3, lineage_id=0, parent_id=1, birth_tick_normalized=50, death_tick=None),
        _agent(agent_id=4, lineage_id=0, parent_id=2, birth_tick_normalized=51, death_tick=None),
    ]
    assert lsr.compute_births_so_far(members, 50) == 3  # birth_tick == 50 included
    assert lsr.compute_births_so_far(members, 49) == 2
    assert lsr.compute_births_so_far(members, 200) == 4


def test_extinction_tick_extant_when_any_member_alive() -> None:
    members = [
        _agent(agent_id=1, lineage_id=0, parent_id=None, birth_tick_normalized=0, death_tick=100),
        _agent(agent_id=2, lineage_id=0, parent_id=1, birth_tick_normalized=50, death_tick=None),
    ]
    assert lsr.compute_extinction_tick(members) is None


def test_extinction_tick_returns_max_death_tick_when_all_dead() -> None:
    members = [
        _agent(agent_id=1, lineage_id=0, parent_id=None, birth_tick_normalized=0, death_tick=100),
        _agent(agent_id=2, lineage_id=0, parent_id=1, birth_tick_normalized=50, death_tick=150),
    ]
    assert lsr.compute_extinction_tick(members) == 150


def test_last_birth_tick_returns_max_birth_tick_normalized() -> None:
    members = [
        _agent(agent_id=1, lineage_id=0, parent_id=None, birth_tick_normalized=0, death_tick=None),
        _agent(agent_id=2, lineage_id=0, parent_id=1, birth_tick_normalized=80, death_tick=None),
        _agent(agent_id=3, lineage_id=0, parent_id=1, birth_tick_normalized=40, death_tick=None),
    ]
    assert lsr.compute_last_birth_tick(members) == 80


# ---------------------------------------------------------------------------
# Leader at tick 50 / eventual top lineage / winner_already_dominant
# ---------------------------------------------------------------------------


def _five_founder_synthetic_run(
    pre_50_births_per_lineage: dict[int, int],
    post_50_births_per_lineage: dict[int, int],
) -> list[lr.AgentRow]:
    """Synthesise 5 founders + variable descendants per lineage. Each
    descendant is born at tick 30 (pre-50) or tick 100 (post-50)."""
    rows: list[lr.AgentRow] = []
    next_id = 1
    for lineage_id in range(5):
        founder_id = next_id
        rows.append(
            _agent(
                agent_id=founder_id,
                lineage_id=lineage_id,
                parent_id=None,
                birth_tick_normalized=0,
                death_tick=None,
            )
        )
        next_id += 1
        # Founder counts as 1 pre-50 birth; add (n - 1) more pre-50 descendants.
        n_pre = pre_50_births_per_lineage.get(lineage_id, 1)
        for _ in range(n_pre - 1):
            rows.append(
                _agent(
                    agent_id=next_id,
                    lineage_id=lineage_id,
                    parent_id=founder_id,
                    birth_tick_normalized=30,
                    death_tick=None,
                )
            )
            next_id += 1
        for _ in range(post_50_births_per_lineage.get(lineage_id, 0)):
            rows.append(
                _agent(
                    agent_id=next_id,
                    lineage_id=lineage_id,
                    parent_id=founder_id,
                    birth_tick_normalized=100,
                    death_tick=None,
                )
            )
            next_id += 1
    return rows


def test_leader_at_tick_50_returns_max_birth_count() -> None:
    rows = _five_founder_synthetic_run(
        pre_50_births_per_lineage={0: 2, 1: 5, 2: 1, 3: 3, 4: 1},
        post_50_births_per_lineage={},
    )
    leader_id, leader_births = lsr.compute_leader_at_tick_50(rows)
    assert leader_id == 1
    assert leader_births == 5


def test_leader_at_tick_50_tie_break_lowest_lineage_id() -> None:
    rows = _five_founder_synthetic_run(
        pre_50_births_per_lineage={0: 3, 1: 3, 2: 3, 3: 3, 4: 3},
        post_50_births_per_lineage={},
    )
    leader_id, leader_births = lsr.compute_leader_at_tick_50(rows)
    assert leader_id == 0
    assert leader_births == 3


def test_eventual_top_lineage_returns_max_b50() -> None:
    rows = _five_founder_synthetic_run(
        pre_50_births_per_lineage={0: 1, 1: 1, 2: 1, 3: 1, 4: 1},
        post_50_births_per_lineage={0: 2, 1: 7, 2: 0, 3: 3, 4: 1},
    )
    top_id, top_b50 = lsr.compute_eventual_top_lineage(rows)
    assert top_id == 1
    assert top_b50 == 7


def test_eventual_top_lineage_returns_none_when_total_b50_zero() -> None:
    rows = _five_founder_synthetic_run(
        pre_50_births_per_lineage={0: 1, 1: 1, 2: 1, 3: 1, 4: 1},
        post_50_births_per_lineage={},
    )
    top_id, top_b50 = lsr.compute_eventual_top_lineage(rows)
    assert top_id is None
    assert top_b50 is None


def test_eventual_top_lineage_tie_break_lowest_lineage_id() -> None:
    rows = _five_founder_synthetic_run(
        pre_50_births_per_lineage={0: 1, 1: 1, 2: 1, 3: 1, 4: 1},
        post_50_births_per_lineage={0: 5, 1: 5, 2: 0, 3: 0, 4: 0},
    )
    top_id, _ = lsr.compute_eventual_top_lineage(rows)
    assert top_id == 0


# ---------------------------------------------------------------------------
# Pruning indicator / expansion indicator / three-way verdict
# ---------------------------------------------------------------------------


def test_pruning_indicator_passes_on_monotone_decline_with_meaningful_spread() -> None:
    m = {0: 5.0, 4: 4.5, 8: 4.2, 12: 4.0}  # spread = 1.0, monotone non-increasing
    assert lsr.evaluate_pruning_indicator(m) is True


def test_pruning_indicator_fails_on_insufficient_spread() -> None:
    m = {0: 5.0, 4: 4.9, 8: 4.8, 12: 4.7}  # spread = 0.3, monotone but too small
    assert lsr.evaluate_pruning_indicator(m) is False


def test_pruning_indicator_fails_on_non_monotone() -> None:
    m = {0: 5.0, 4: 4.0, 8: 4.5, 12: 3.0}  # spread = 2.0 but reverses at h=8
    assert lsr.evaluate_pruning_indicator(m) is False


def test_pruning_indicator_passes_on_weak_monotone_with_ties() -> None:
    m = {0: 5.0, 4: 4.5, 8: 4.5, 12: 4.4}  # ties allowed
    assert lsr.evaluate_pruning_indicator(m) is True


def test_expansion_indicator_passes_on_monotone_rise_with_meaningful_spread() -> None:
    r = {0: 0.4, 4: 0.5, 8: 0.55, 12: 0.6}  # spread = 0.20
    assert lsr.evaluate_expansion_indicator(r) is True


def test_expansion_indicator_fails_on_insufficient_spread() -> None:
    r = {0: 0.5, 4: 0.55, 8: 0.6, 12: 0.6}  # spread = 0.10
    assert lsr.evaluate_expansion_indicator(r) is False


def test_expansion_indicator_fails_on_non_monotone() -> None:
    r = {0: 0.4, 4: 0.6, 8: 0.5, 12: 0.6}  # reverses at h=8
    assert lsr.evaluate_expansion_indicator(r) is False


def test_three_way_verdict_pruning_supported() -> None:
    assert lsr.evaluate_three_way_verdict(True, False) == lsr.VERDICT_PRUNING


def test_three_way_verdict_expansion_supported() -> None:
    assert lsr.evaluate_three_way_verdict(False, True) == lsr.VERDICT_EXPANSION


def test_three_way_verdict_mixed_when_both_pass() -> None:
    assert lsr.evaluate_three_way_verdict(True, True) == lsr.VERDICT_MIXED


def test_three_way_verdict_unresolved_when_neither_pass() -> None:
    assert lsr.evaluate_three_way_verdict(False, False) == lsr.VERDICT_MIXED


# ---------------------------------------------------------------------------
# summarise_run_survival end-to-end on synthetic agent_rows
# ---------------------------------------------------------------------------


def test_summarise_run_survival_basic_invariants() -> None:
    rows = _five_founder_synthetic_run(
        pre_50_births_per_lineage={0: 1, 1: 1, 2: 1, 3: 3, 4: 1},
        post_50_births_per_lineage={0: 0, 1: 0, 2: 0, 3: 5, 4: 0},
    )
    timeline_rows, extinction_rows, dominance_row = lsr.summarise_run_survival(
        rows,
        n_ticks=200,
        source_version="v0.test",
        arm_label="arm",
        hazard=8,
        seed=1,
    )
    # 5 lineages x 7 snapshot ticks.
    assert len(timeline_rows) == 5 * 7
    # All founders alive at T=0.
    t0_active = [r.active for r in timeline_rows if r.snapshot_tick == 0]
    assert all(t0_active)
    # 5 extinction rows; all extant (founders never die in fixture).
    assert len(extinction_rows) == 5
    assert all(r.extinction_tick is None for r in extinction_rows)
    # Lineage 3 leads at T=50 (3 births vs others at 1).
    assert dominance_row.leader_lineage_id_at_tick_50 == 3
    assert dominance_row.leader_births_at_tick_50 == 3
    # Lineage 3 wins post-50 (5 b50 vs 0 elsewhere).
    assert dominance_row.eventual_top_lineage_id == 3
    assert dominance_row.eventual_top_b50 == 5
    # Winner already dominant at tick 50: True.
    assert dominance_row.winner_already_dominant_at_tick_50 is True
    # Only lineage 3 has post-50 births.
    assert dominance_row.n_lineages_with_post50_birth == 1


def test_summarise_run_survival_winner_not_already_dominant() -> None:
    rows = _five_founder_synthetic_run(
        pre_50_births_per_lineage={0: 5, 1: 1, 2: 1, 3: 1, 4: 1},
        post_50_births_per_lineage={0: 0, 1: 7, 2: 0, 3: 0, 4: 0},
    )
    _, _, dominance_row = lsr.summarise_run_survival(
        rows, n_ticks=200, source_version="vX", arm_label="arm", hazard=8, seed=1
    )
    assert dominance_row.leader_lineage_id_at_tick_50 == 0
    assert dominance_row.eventual_top_lineage_id == 1
    assert dominance_row.winner_already_dominant_at_tick_50 is False


def test_summarise_run_survival_no_post50_births_yields_none_winner() -> None:
    rows = _five_founder_synthetic_run(
        pre_50_births_per_lineage={0: 2, 1: 1, 2: 1, 3: 1, 4: 1},
        post_50_births_per_lineage={},
    )
    _, _, dominance_row = lsr.summarise_run_survival(
        rows, n_ticks=200, source_version="vX", arm_label="arm", hazard=8, seed=1
    )
    assert dominance_row.eventual_top_lineage_id is None
    assert dominance_row.eventual_top_b50 is None
    assert dominance_row.winner_already_dominant_at_tick_50 is None


def test_summarise_run_survival_halts_when_founder_count_wrong() -> None:
    rows = [
        _agent(agent_id=1, lineage_id=0, parent_id=None, birth_tick_normalized=0, death_tick=None),
        _agent(agent_id=2, lineage_id=1, parent_id=None, birth_tick_normalized=0, death_tick=None),
    ]
    with pytest.raises(lr.LineageReplayError, match="exactly 5 lineages"):
        lsr.summarise_run_survival(
            rows, n_ticks=200, source_version="vX", arm_label="arm", hazard=8, seed=1
        )


def test_summarise_run_survival_halts_when_founder_dies_before_tick_zero_check() -> None:
    """If somehow a founder has death_tick=0 (impossible by construction
    in the corpus, but defensive), founders_alive_at_t0 fails."""
    rows: list[lr.AgentRow] = []
    for lineage_id in range(5):
        rows.append(
            _agent(
                agent_id=lineage_id + 1,
                lineage_id=lineage_id,
                parent_id=None,
                birth_tick_normalized=0,
                death_tick=0 if lineage_id == 0 else None,
            )
        )
    with pytest.raises(lr.LineageReplayError, match="founders_alive_at_t0"):
        lsr.summarise_run_survival(
            rows, n_ticks=200, source_version="vX", arm_label="arm", hazard=8, seed=1
        )


# ---------------------------------------------------------------------------
# Per-hazard aggregation
# ---------------------------------------------------------------------------


def test_aggregate_pruning_summary_means_match_synthetic_corpus() -> None:
    """Build a tiny 2-runs-per-hazard synthetic corpus and check
    aggregations."""
    timeline: list[lsr.FounderTimelineRow] = []
    extinction: list[lsr.FounderExtinctionRow] = []
    dominance: list[lsr.PrePostDominanceRow] = []
    for hazard in (0, 4, 8, 12):
        for seed in (1, 2):
            # 5 lineages, 4 active at T=50 in run 1 and 3 in run 2 of hazard h.
            n_active_at_50 = 4 if seed == 1 else 3
            for lineage_id in range(5):
                active = lineage_id < n_active_at_50
                for tick in lsr.SNAPSHOT_TICKS:
                    timeline.append(
                        lsr.FounderTimelineRow(
                            source_version="vX",
                            arm_label=f"arm-{hazard}",
                            hazard=hazard,
                            seed=seed,
                            lineage_id=lineage_id,
                            snapshot_tick=tick,
                            active=active if tick > 0 else True,
                            n_alive_in_lineage=1 if (active if tick > 0 else True) else 0,
                            births_so_far=1,
                        )
                    )
                extinction.append(
                    lsr.FounderExtinctionRow(
                        source_version="vX",
                        arm_label=f"arm-{hazard}",
                        hazard=hazard,
                        seed=seed,
                        lineage_id=lineage_id,
                        extinction_tick=None if active else 100,
                        last_birth_tick=0,
                        n_members=1,
                    )
                )
            dominance.append(
                lsr.PrePostDominanceRow(
                    source_version="vX",
                    arm_label=f"arm-{hazard}",
                    hazard=hazard,
                    seed=seed,
                    leader_lineage_id_at_tick_50=0,
                    leader_births_at_tick_50=1,
                    eventual_top_lineage_id=0 if seed == 1 else 1,
                    eventual_top_b50=3,
                    winner_already_dominant_at_tick_50=(seed == 1),
                    n_lineages_with_post50_birth=2,
                )
            )
    summary = lsr.aggregate_pruning_summary(timeline, extinction, dominance)
    by_hazard = {ps.hazard: ps for ps in summary}
    # Mean active at T=50 per hazard: (4 + 3) / 2 = 3.5.
    for hazard in (0, 4, 8, 12):
        assert by_hazard[hazard].n_runs == 2
        assert by_hazard[hazard].mean_founders_alive_at_t0 == 5.0
        assert by_hazard[hazard].mean_founders_alive_at_t50 == 3.5
        # winner_already_dominant rate: 1/2 = 0.5.
        assert by_hazard[hazard].winner_already_dominant_at_tick_50_rate == 0.5
        # mean n_post50: 2.0 (each run has 2 lineages with post50 birth).
        assert by_hazard[hazard].mean_n_lineages_with_post50_birth == 2.0


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
        founder_id = next_id
        records.append(
            {
                "agent_id": founder_id,
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


def test_end_to_end_re_anchor_passes(tmp_path, monkeypatch) -> None:
    run_dir = tmp_path / "v0.test" / "transfer-1500-hzd0-influx-1.0" / "seed-1"
    _write_synthetic_run(
        run_dir, seed=1, hazard=0, n_ticks=200, agents=_five_founder_run_records(dominant_lineage=2)
    )
    agents, n_ticks = lsr.load_run_agents("v0.test", "transfer-1500-hzd0-influx-1.0", 0, 1, run_dir)
    _, _, dominance = lsr.summarise_run_survival(
        agents,
        n_ticks=n_ticks,
        source_version="v0.test",
        arm_label="transfer-1500-hzd0-influx-1.0",
        hazard=0,
        seed=1,
    )
    anchors = {("v0.test", "transfer-1500-hzd0-influx-1.0", 1): (6, 2)}
    lsr.cross_check_top_lineage_b50_against_v0_34([dominance], anchors)


def test_end_to_end_re_anchor_halts_on_drift(tmp_path) -> None:
    run_dir = tmp_path / "v0.test" / "transfer-1500-hzd0-influx-1.0" / "seed-1"
    _write_synthetic_run(
        run_dir, seed=1, hazard=0, n_ticks=200, agents=_five_founder_run_records(dominant_lineage=2)
    )
    agents, n_ticks = lsr.load_run_agents("v0.test", "transfer-1500-hzd0-influx-1.0", 0, 1, run_dir)
    _, _, dominance = lsr.summarise_run_survival(
        agents,
        n_ticks=n_ticks,
        source_version="v0.test",
        arm_label="transfer-1500-hzd0-influx-1.0",
        hazard=0,
        seed=1,
    )
    anchors_wrong = {("v0.test", "transfer-1500-hzd0-influx-1.0", 1): (99, 2)}
    with pytest.raises(lr.LineageReplayError, match="re-anchor mismatch"):
        lsr.cross_check_top_lineage_b50_against_v0_34([dominance], anchors_wrong)


def test_load_v0_34_anchors_round_trip(tmp_path) -> None:
    path = tmp_path / "run_summary.csv"
    path.write_text(
        "source_version,arm_label,hazard,seed,total_b50,top_lineage_id,"
        "top_lineage_b50,top_lineage_b50_share,n_lineages_with_b50_ge_1,"
        "n_lineages_alive_at_end\n"
        "v0.test,arm-A,0,1,10,3,10,1.0,1,5\n"
        "v0.test,arm-B,0,2,0,,,,0,5\n"
    )
    loaded = lsr.load_v0_34_anchors(path)
    assert loaded[("v0.test", "arm-A", 1)] == (10, 3)
    assert loaded[("v0.test", "arm-B", 2)] == (None, None)


def test_load_v0_34_anchors_halts_on_missing_file(tmp_path) -> None:
    with pytest.raises(lr.LineageReplayError, match="missing"):
        lsr.load_v0_34_anchors(tmp_path / "does-not-exist.csv")
