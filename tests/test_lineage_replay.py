"""Tests for the v0.34 lineage observability reducer
(``scripts/lineage_replay.py``).

Synthetic-fixture coverage of the contract committed in
[[docs/experiments/fear_hunger_v0.34.md]]:

  - Founder identification (parent_id is None).
  - Founder lineage_id assignment (sorted by agent_id, starting at 0).
  - Cross-check that non-founder lineage_id matches founder-ancestor
    lineage_id; mismatch raises LineageReplayError.
  - Generation-depth BFS: founders=0; child=1; grandchild=2.
  - Broken parent reference raises LineageReplayError.
  - Cycle in parent chain raises LineageReplayError.
  - Wrong founder count raises LineageReplayError.
  - birth_tick_normalized: 0 for founders, unchanged for descendants.
  - born_after_tick_50: founders never qualify.
  - lifespan: with and without death_tick.
  - survived_to_end: agents without death rows.
  - Lineage aggregation: n_agents_total = 1 + descendants; b50_count;
    b50_share NaN when total_b50 == 0; tie-break by lowest lineage_id.
  - Run summary: top_lineage_b50_share defined when total_b50 > 0;
    NaN otherwise; tie-break.
  - Pool summary: mean / median / single_lineage_majority counts.
  - End-to-end: synthetic 5-run mini-corpus → expected CSVs.
"""

from __future__ import annotations

import importlib.util
import json
import math
import sys
from pathlib import Path

import pytest

_LR_PATH = Path(__file__).parent.parent / "scripts" / "lineage_replay.py"
_spec = importlib.util.spec_from_file_location("lineage_replay", _LR_PATH)
assert _spec is not None
assert _spec.loader is not None
lr = importlib.util.module_from_spec(_spec)
sys.modules["lineage_replay"] = lr
_spec.loader.exec_module(lr)


# ---------------------------------------------------------------------------
# Fixture helpers
# ---------------------------------------------------------------------------


def _make_parsed(rows: list[dict]) -> list[dict]:
    """Helper to fill in default fields for parsed agent_lifetimes rows."""
    out = []
    for r in rows:
        out.append(
            {
                "agent_id": r["agent_id"],
                "lineage_id": r.get("lineage_id"),
                "parent_id": r.get("parent_id"),
                "birth_tick": r.get("birth_tick"),
                "death_tick": r.get("death_tick"),
                "death_cause": r.get("death_cause", ""),
                "offspring_count": r.get("offspring_count", 0),
            }
        )
    return out


def _five_founders(extra: list[dict] | None = None) -> list[dict]:
    """Return parsed rows with 5 valid founders + optional extras."""
    rows = [{"agent_id": i, "lineage_id": None, "parent_id": None} for i in range(1, 6)]
    if extra:
        rows.extend(extra)
    return _make_parsed(rows)


# ---------------------------------------------------------------------------
# Founder identification + lineage assignment
# ---------------------------------------------------------------------------


def test_founders_get_lineage_ids_zero_through_four() -> None:
    """Five founders sorted by agent_id get lineage_id 0..4."""
    parsed = _five_founders()
    lineage_by_agent = lr.assign_founder_lineages(parsed)
    assert lineage_by_agent == {1: 0, 2: 1, 3: 2, 4: 3, 5: 4}


def test_descendants_inherit_founder_lineage_id() -> None:
    """Child of founder agent_id=1 → lineage_id 0; child-of-child too."""
    parsed = _five_founders(
        [
            {"agent_id": 6, "lineage_id": 0, "parent_id": 1, "birth_tick": 9},
            {"agent_id": 7, "lineage_id": 0, "parent_id": 6, "birth_tick": 30},
            {"agent_id": 8, "lineage_id": 4, "parent_id": 5, "birth_tick": 12},
        ]
    )
    lineage_by_agent = lr.assign_founder_lineages(parsed)
    assert lineage_by_agent[6] == 0
    assert lineage_by_agent[7] == 0
    assert lineage_by_agent[8] == 4


def test_non_founder_with_mismatched_lineage_id_raises() -> None:
    """Declared lineage_id that disagrees with founder ancestor raises."""
    parsed = _five_founders([{"agent_id": 6, "lineage_id": 99, "parent_id": 1, "birth_tick": 9}])
    with pytest.raises(lr.LineageReplayError, match="lineage_id=99"):
        lr.assign_founder_lineages(parsed)


def test_wrong_founder_count_raises() -> None:
    """Fewer than 5 (or more than 5) founders raises."""
    rows = [{"agent_id": i, "lineage_id": None, "parent_id": None} for i in range(1, 5)]
    parsed = _make_parsed(rows)
    with pytest.raises(lr.LineageReplayError, match="expected exactly 5 founders"):
        lr.assign_founder_lineages(parsed)


def test_cycle_in_parent_chain_raises() -> None:
    """A cycle in the parent chain raises (defensive — should not occur
    in real artifacts)."""
    parsed = _make_parsed(
        [{"agent_id": i, "lineage_id": None, "parent_id": None} for i in range(1, 6)]
        + [
            # Synthetic cycle: 6 -> 7 -> 6.
            {"agent_id": 6, "lineage_id": 0, "parent_id": 7, "birth_tick": 10},
            {"agent_id": 7, "lineage_id": 0, "parent_id": 6, "birth_tick": 11},
        ]
    )
    with pytest.raises(lr.LineageReplayError, match="cycle"):
        lr.assign_founder_lineages(parsed)


# ---------------------------------------------------------------------------
# Generation-depth BFS
# ---------------------------------------------------------------------------


def test_generation_depth_founders_are_zero() -> None:
    parsed = _five_founders()
    depth = lr.compute_generation_depths(parsed)
    assert all(depth[a] == 0 for a in range(1, 6))


def test_generation_depth_three_levels() -> None:
    """Founder → child (1) → grandchild (2)."""
    parsed = _five_founders(
        [
            {"agent_id": 6, "lineage_id": 0, "parent_id": 1, "birth_tick": 9},
            {"agent_id": 7, "lineage_id": 0, "parent_id": 6, "birth_tick": 30},
            {"agent_id": 8, "lineage_id": 0, "parent_id": 7, "birth_tick": 60},
        ]
    )
    depth = lr.compute_generation_depths(parsed)
    assert depth[6] == 1
    assert depth[7] == 2
    assert depth[8] == 3


def test_broken_parent_reference_raises() -> None:
    """parent_id pointing at an absent agent_id raises."""
    parsed = _five_founders([{"agent_id": 6, "lineage_id": 0, "parent_id": 99, "birth_tick": 9}])
    with pytest.raises(lr.LineageReplayError, match="broken parent reference"):
        lr.compute_generation_depths(parsed)


# ---------------------------------------------------------------------------
# Per-agent assembly
# ---------------------------------------------------------------------------


def _build_rows_for_test(parsed: list[dict], n_ticks: int = 200):
    lineage_by_agent = lr.assign_founder_lineages(parsed)
    depth_by_agent = lr.compute_generation_depths(parsed)
    return lr.build_agent_rows(
        parsed,
        lineage_by_agent,
        depth_by_agent,
        n_ticks,
        source_version="vTEST",
        arm_label="transfer-1500-hzd8-influx-1.0",
        hazard=8,
        seed=17,
    )


def test_founder_birth_tick_normalized_is_zero() -> None:
    parsed = _five_founders()
    rows = _build_rows_for_test(parsed)
    for row in rows:
        assert row.is_founder is True
        assert row.birth_tick_normalized == 0
        assert row.born_after_tick_50 is False


def test_descendant_born_after_tick_50_threshold() -> None:
    parsed = _five_founders(
        [
            {"agent_id": 6, "lineage_id": 0, "parent_id": 1, "birth_tick": 50},
            {"agent_id": 7, "lineage_id": 0, "parent_id": 1, "birth_tick": 51},
            {"agent_id": 8, "lineage_id": 0, "parent_id": 1, "birth_tick": 52},
        ]
    )
    rows = _build_rows_for_test(parsed)
    by_id = {r.agent_id: r for r in rows}
    assert by_id[6].born_after_tick_50 is False  # 50 is NOT > 50
    assert by_id[7].born_after_tick_50 is True
    assert by_id[8].born_after_tick_50 is True


def test_lifespan_with_death_tick() -> None:
    parsed = _five_founders(
        [
            {
                "agent_id": 6,
                "lineage_id": 0,
                "parent_id": 1,
                "birth_tick": 30,
                "death_tick": 100,
                "death_cause": "STARVATION",
            }
        ]
    )
    rows = _build_rows_for_test(parsed, n_ticks=200)
    by_id = {r.agent_id: r for r in rows}
    assert by_id[6].lifespan == 70
    assert by_id[6].survived_to_end is False
    assert by_id[6].death_cause == "STARVATION"


def test_lifespan_for_survivor() -> None:
    """survived_to_end -> lifespan = n_ticks - birth_tick_normalized."""
    parsed = _five_founders(
        [
            {"agent_id": 6, "lineage_id": 0, "parent_id": 1, "birth_tick": 40},
        ]
    )
    rows = _build_rows_for_test(parsed, n_ticks=200)
    by_id = {r.agent_id: r for r in rows}
    assert by_id[6].survived_to_end is True
    assert by_id[6].lifespan == 160
    # founder agent_id=1 is also a survivor (n_ticks - 0 = 200).
    assert by_id[1].lifespan == 200


# ---------------------------------------------------------------------------
# Lineage aggregation
# ---------------------------------------------------------------------------


def test_lineage_aggregation_includes_founder_in_n_agents_total() -> None:
    parsed = _five_founders(
        [
            {"agent_id": 6, "lineage_id": 0, "parent_id": 1, "birth_tick": 60},
            {"agent_id": 7, "lineage_id": 0, "parent_id": 6, "birth_tick": 80},
        ]
    )
    rows = _build_rows_for_test(parsed)
    lineage_rows = lr.aggregate_lineages(
        rows,
        source_version="vTEST",
        arm_label="transfer-1500-hzd8-influx-1.0",
        hazard=8,
        seed=17,
    )
    by_id = {lr_row.lineage_id: lr_row for lr_row in lineage_rows}
    # Lineage 0 has founder + 2 descendants = 3 agents.
    assert by_id[0].n_agents_total == 3
    assert by_id[0].b50_count == 2  # both descendants born after tick 50
    # Lineage 1..4 each have just the founder.
    for lid in range(1, 5):
        assert by_id[lid].n_agents_total == 1
        assert by_id[lid].b50_count == 0


def test_lineage_b50_share_is_nan_when_total_b50_zero() -> None:
    """All-founders run: total_b50 = 0 → every lineage's b50_share is NaN."""
    parsed = _five_founders()
    rows = _build_rows_for_test(parsed)
    lineage_rows = lr.aggregate_lineages(
        rows, source_version="vTEST", arm_label="x", hazard=0, seed=1
    )
    for lr_row in lineage_rows:
        assert math.isnan(lr_row.b50_share)


def test_lineage_b50_share_sums_to_one_when_nonzero() -> None:
    parsed = _five_founders(
        [
            {"agent_id": 6, "lineage_id": 0, "parent_id": 1, "birth_tick": 60},
            {"agent_id": 7, "lineage_id": 1, "parent_id": 2, "birth_tick": 70},
            {"agent_id": 8, "lineage_id": 1, "parent_id": 2, "birth_tick": 90},
        ]
    )
    rows = _build_rows_for_test(parsed)
    lineage_rows = lr.aggregate_lineages(
        rows, source_version="vTEST", arm_label="x", hazard=4, seed=2
    )
    total = sum(lr_row.b50_share for lr_row in lineage_rows if not math.isnan(lr_row.b50_share))
    # Three b50 agents total; lineage 0 has 1, lineage 1 has 2.
    assert math.isclose(total, 1.0)


# ---------------------------------------------------------------------------
# Run summary
# ---------------------------------------------------------------------------


def test_run_summary_top_lineage_share_when_distributed() -> None:
    parsed = _five_founders(
        [
            {"agent_id": 6, "lineage_id": 0, "parent_id": 1, "birth_tick": 60},
            {"agent_id": 7, "lineage_id": 1, "parent_id": 2, "birth_tick": 70},
            {"agent_id": 8, "lineage_id": 1, "parent_id": 2, "birth_tick": 90},
        ]
    )
    rows = _build_rows_for_test(parsed)
    lineage_rows = lr.aggregate_lineages(
        rows, source_version="vTEST", arm_label="x", hazard=4, seed=2
    )
    summary = lr.summarise_run(
        lineage_rows, source_version="vTEST", arm_label="x", hazard=4, seed=2
    )
    assert summary.total_b50 == 3
    assert summary.top_lineage_id == 1
    assert summary.top_lineage_b50 == 2
    assert math.isclose(summary.top_lineage_b50_share, 2 / 3)
    assert summary.n_lineages_with_b50_ge_1 == 2


def test_run_summary_nan_when_total_b50_zero() -> None:
    parsed = _five_founders()
    rows = _build_rows_for_test(parsed)
    lineage_rows = lr.aggregate_lineages(
        rows, source_version="vTEST", arm_label="x", hazard=0, seed=1
    )
    summary = lr.summarise_run(
        lineage_rows, source_version="vTEST", arm_label="x", hazard=0, seed=1
    )
    assert summary.total_b50 == 0
    assert summary.top_lineage_id is None
    assert summary.top_lineage_b50 is None
    assert math.isnan(summary.top_lineage_b50_share)


def test_run_summary_tie_break_lowest_lineage_id_wins() -> None:
    """Two lineages with equal b50_count → tie-break to lowest lineage_id."""
    parsed = _five_founders(
        [
            {"agent_id": 6, "lineage_id": 2, "parent_id": 3, "birth_tick": 60},
            {"agent_id": 7, "lineage_id": 4, "parent_id": 5, "birth_tick": 60},
        ]
    )
    rows = _build_rows_for_test(parsed)
    lineage_rows = lr.aggregate_lineages(
        rows, source_version="vTEST", arm_label="x", hazard=4, seed=2
    )
    summary = lr.summarise_run(
        lineage_rows, source_version="vTEST", arm_label="x", hazard=4, seed=2
    )
    assert summary.top_lineage_b50 == 1
    assert summary.top_lineage_id == 2


def test_run_summary_single_lineage_majority_definition() -> None:
    """top_lineage_b50_share >= 0.5 ⇒ single-lineage majority."""
    parsed = _five_founders(
        [
            {"agent_id": 6, "lineage_id": 0, "parent_id": 1, "birth_tick": 60},
            {"agent_id": 7, "lineage_id": 0, "parent_id": 1, "birth_tick": 70},
            {"agent_id": 8, "lineage_id": 1, "parent_id": 2, "birth_tick": 80},
        ]
    )
    rows = _build_rows_for_test(parsed)
    lineage_rows = lr.aggregate_lineages(
        rows, source_version="vTEST", arm_label="x", hazard=4, seed=2
    )
    summary = lr.summarise_run(
        lineage_rows, source_version="vTEST", arm_label="x", hazard=4, seed=2
    )
    # 2/3 of b50s are in lineage 0 — majority threshold (0.5) met.
    assert summary.top_lineage_b50_share >= 0.5


# ---------------------------------------------------------------------------
# Pool summary
# ---------------------------------------------------------------------------


def test_pool_summary_aggregates_per_hazard() -> None:
    """Mix of single-lineage-majority and distributed runs at one
    hazard; verify mean / median / counts."""
    runs = [
        lr.RunSummaryRow("vTEST", "x", 8, seed, total_b50, top_id, top_b50, share, 1, 1)
        for (seed, total_b50, top_id, top_b50, share) in [
            (1, 4, 0, 4, 1.0),
            (2, 4, 0, 2, 0.5),
            (3, 4, 0, 1, 0.25),
            (4, 0, None, None, float("nan")),
        ]
    ]
    pool = lr.aggregate_pool(runs)
    by_hazard = {p.hazard: p for p in pool}
    p8 = by_hazard[8]
    assert p8.n_runs == 4
    assert p8.total_b50 == 12
    # Non-NaN shares: [1.0, 0.5, 0.25] → mean=0.583..., median=0.5.
    assert math.isclose(p8.mean_top_lineage_b50_share, (1.0 + 0.5 + 0.25) / 3)
    assert math.isclose(p8.median_top_lineage_b50_share, 0.5)
    # majority threshold 0.5 inclusive → seeds 1 and 2 qualify.
    assert p8.n_runs_single_lineage_majority == 2
    assert p8.n_runs_total_b50_zero == 1
    # Other hazards default to empty.
    for h in (0, 4, 12):
        assert by_hazard[h].n_runs == 0
        assert math.isnan(by_hazard[h].mean_top_lineage_b50_share)


# ---------------------------------------------------------------------------
# Cross-check anchors
# ---------------------------------------------------------------------------


def test_cross_check_b50_anchors_passes_when_correct() -> None:
    pool = [
        lr.PoolSummaryRow(0, 24, 291, 0.0, 0.0, 0, 0),
        lr.PoolSummaryRow(4, 24, 312, 0.0, 0.0, 0, 0),
        lr.PoolSummaryRow(8, 24, 321, 0.0, 0.0, 0, 0),
        lr.PoolSummaryRow(12, 24, 312, 0.0, 0.0, 0, 0),
    ]
    lr.cross_check_b50_anchors(pool)


def test_cross_check_b50_anchors_raises_on_mismatch() -> None:
    pool = [
        lr.PoolSummaryRow(0, 24, 291, 0.0, 0.0, 0, 0),
        lr.PoolSummaryRow(4, 24, 312, 0.0, 0.0, 0, 0),
        lr.PoolSummaryRow(8, 24, 999, 0.0, 0.0, 0, 0),  # wrong
        lr.PoolSummaryRow(12, 24, 312, 0.0, 0.0, 0, 0),
    ]
    with pytest.raises(lr.LineageReplayError, match=r"h=8.*B_pool\(8\)=321"):
        lr.cross_check_b50_anchors(pool)


# ---------------------------------------------------------------------------
# End-to-end: synthetic run directory → process_run
# ---------------------------------------------------------------------------


def _write_synthetic_run(tmp_path: Path, *, seed: int, hazard: int) -> Path:
    """Write a tiny synthetic run directory mimicking the real layout."""
    run_dir = tmp_path / f"transfer-1500-hzd{hazard}-influx-1.0" / f"seed-{seed}"
    run_dir.mkdir(parents=True)
    # Five founders + 3 descendants, two of which are b50.
    lifetimes = [
        # founders (empty lineage_id / parent_id / birth_tick)
        ["1", "", "", "", "", "", "1"],
        ["2", "", "", "", "", "", "0"],
        ["3", "", "", "", "30", "STARVATION", "0"],
        ["4", "", "", "", "40", "STARVATION", "0"],
        ["5", "", "", "", "", "", "0"],
        # descendants
        ["6", "0", "1", "20", "", "", "0"],
        ["7", "0", "1", "60", "", "", "0"],
        ["8", "0", "6", "80", "", "", "0"],
    ]
    with (run_dir / "agent_lifetimes.csv").open("w") as f:
        f.write("agent_id,lineage_id,parent_id,birth_tick,death_tick,death_cause,offspring_count\n")
        for row in lifetimes:
            f.write(",".join(row) + "\n")
    with (run_dir / "config.json").open("w") as f:
        json.dump({"world": {"seed": seed, "hazard_damage_default": hazard}}, f)
    with (run_dir / "manifest.json").open("w") as f:
        json.dump({"ticks_completed": 200}, f)
    return run_dir


def test_process_run_end_to_end(tmp_path: Path) -> None:
    """End-to-end on a synthetic run directory: 5 founders + 3
    descendants, 2 of which are b50 (agent 7 birth_tick=60 and
    agent 8 birth_tick=80; both in lineage 0). Expect total_b50=2,
    top_lineage_b50_share=1.0."""
    run_dir = _write_synthetic_run(tmp_path, seed=42, hazard=8)
    agents, _lineages, summary = lr.process_run(
        "vTEST", "transfer-1500-hzd8-influx-1.0", 8, 42, run_dir
    )
    assert len(agents) == 8
    assert summary.total_b50 == 2
    assert summary.top_lineage_id == 0
    assert summary.top_lineage_b50 == 2
    assert math.isclose(summary.top_lineage_b50_share, 1.0)
    # Descendant agent_id=7 is born at tick 60 in lineage 0.
    by_id = {a.agent_id: a for a in agents}
    assert by_id[7].born_after_tick_50 is True
    assert by_id[6].born_after_tick_50 is False  # birth_tick=20
    # Generation depth: founder=0, agent 6=1, agent 8 (child of 6)=2.
    assert by_id[1].generation_depth == 0
    assert by_id[6].generation_depth == 1
    assert by_id[8].generation_depth == 2
    # Lifespan for survivors uses n_ticks=200.
    assert by_id[1].lifespan == 200
    assert by_id[3].lifespan == 30  # death_tick - 0


def test_process_run_seed_mismatch_raises(tmp_path: Path) -> None:
    """If config.json's seed does not match the expected seed, halt."""
    run_dir = _write_synthetic_run(tmp_path, seed=42, hazard=8)
    with pytest.raises(lr.LineageReplayError, match="seed mismatch"):
        lr.process_run("vTEST", "transfer-1500-hzd8-influx-1.0", 8, 99, run_dir)


# ---------------------------------------------------------------------------
# Discovery / configuration sanity
# ---------------------------------------------------------------------------


def test_discover_runs_returns_96_tuples() -> None:
    runs = lr.discover_runs()
    assert len(runs) == 96
    # 24 distinct seeds, 4 distinct hazards = 96 (arm, seed) pairs.
    seeds = {seed for _, _, _, seed, _ in runs}
    hazards = {h for _, _, h, _, _ in runs}
    assert seeds == set(range(1, 25))
    assert hazards == {0, 4, 8, 12}


def test_b_pool_anchors_match_v0_33_audit() -> None:
    """The anchors hard-coded in lineage_replay.py MUST match the
    v0.33 audit's pre-committed B_pool(h) values."""
    assert lr.B_POOL_ANCHORS == {4: 312, 8: 321, 12: 312}


def test_single_lineage_majority_threshold_is_one_half() -> None:
    """Locked threshold per pre-reg: top_lineage_b50_share >= 0.5."""
    assert lr.SINGLE_LINEAGE_MAJORITY_THRESHOLD == 0.5
