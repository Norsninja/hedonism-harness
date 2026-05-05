"""Tests for the v0.24 population-dynamics analysis library.

Covers:
  - PopulationTrajectory construction from synthetic events.jsonl
    fixtures (no I/O on disk runs).
  - Founder inference (founders that die early; founders alive at
    run end; mixed cases).
  - Lifespan accounting for born + died, born + alive, founder + died,
    founder + alive.
  - STARVATION vs INJURY death-cause split per tick.
  - aggregate_cell over multiple trajectories: mean peak, mean
    late-window, percentile shape, starvation bucket totals.
  - Smoke test against a real on-disk events.jsonl from the v0.23
    sweep (verifies the loader handles the production event format).
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from hedonism_harness.experiments.population_dynamics import (
    STARVATION_WINDOWS,
    CellAggregate,
    _percentile,
    aggregate_cell,
    load_population_trajectory,
)


def _write_events(path: Path, rows: list[dict]) -> None:
    with path.open("w") as f:
        for row in rows:
            f.write(json.dumps(row) + "\n")


# ---------------------------------------------------------------------------
# PopulationTrajectory: synthetic events
# ---------------------------------------------------------------------------


def test_empty_events_only_founders(tmp_path: Path) -> None:
    """No births, no deaths -> population sits at n_founders for the
    full window; lifespans = (0, n_ticks) for each founder."""
    events = tmp_path / "events.jsonl"
    _write_events(events, [])
    traj = load_population_trajectory(events, n_founders=5, n_ticks=10)
    assert traj.population_at_tick == (5,) * 10
    assert len(traj.lifespans) == 5
    assert all(bt == 0 and dt == 10 for bt, dt in traj.lifespans)
    assert traj.starvation_deaths_per_tick == (0,) * 10
    assert traj.injury_deaths_per_tick == (0,) * 10
    assert traj.peak_population == 5
    assert traj.tick_of_peak == 0


def test_single_birth_at_tick_3(tmp_path: Path) -> None:
    events = tmp_path / "events.jsonl"
    _write_events(
        events,
        [
            {
                "type": "AgentBorn",
                "tick": 3,
                "event": {"agent_id": 99, "parent_id": 1, "tick": 3, "x": 0, "y": 0},
            }
        ],
    )
    traj = load_population_trajectory(events, n_founders=2, n_ticks=5)
    assert traj.population_at_tick == (2, 2, 2, 3, 3)
    assert traj.peak_population == 3
    assert traj.tick_of_peak == 3
    # 2 founders alive + 1 born (alive at end).
    assert sorted(traj.lifespans) == [(0, 5), (0, 5), (3, 5)]


def test_starvation_and_injury_split(tmp_path: Path) -> None:
    events = tmp_path / "events.jsonl"
    _write_events(
        events,
        [
            {
                "type": "AgentDied",
                "tick": 2,
                "event": {"agent_id": 1, "cause": "STARVATION", "tick": 2},
            },
            {
                "type": "AgentDied",
                "tick": 2,
                "event": {"agent_id": 2, "cause": "INJURY", "tick": 2},
            },
            {
                "type": "AgentDied",
                "tick": 4,
                "event": {"agent_id": 3, "cause": "STARVATION", "tick": 4},
            },
        ],
    )
    traj = load_population_trajectory(events, n_founders=3, n_ticks=5)
    # Pop: 3 founders -> tick 0: 3, tick 1: 3, tick 2: 3-2=1, tick 3: 1,
    #      tick 4: 1-1=0.
    assert traj.population_at_tick == (3, 3, 1, 1, 0)
    assert traj.starvation_deaths_per_tick == (0, 0, 1, 0, 1)
    assert traj.injury_deaths_per_tick == (0, 0, 1, 0, 0)


def test_founder_dies_versus_alive(tmp_path: Path) -> None:
    """Founder 1 dies at tick 4; founders 2 and 3 alive at run end."""
    events = tmp_path / "events.jsonl"
    _write_events(
        events,
        [
            {
                "type": "AgentDied",
                "tick": 4,
                "event": {"agent_id": 1, "cause": "STARVATION", "tick": 4},
            },
        ],
    )
    traj = load_population_trajectory(events, n_founders=3, n_ticks=10)
    lifespan_pairs = sorted(traj.lifespans)
    # 1 dead founder (0, 4); 2 alive founders (0, 10).
    assert lifespan_pairs == [(0, 4), (0, 10), (0, 10)]


def test_born_then_dies(tmp_path: Path) -> None:
    """Agent born at tick 5, dies at tick 8."""
    events = tmp_path / "events.jsonl"
    _write_events(
        events,
        [
            {
                "type": "AgentBorn",
                "tick": 5,
                "event": {"agent_id": 7, "parent_id": 1, "tick": 5, "x": 0, "y": 0},
            },
            {
                "type": "AgentDied",
                "tick": 8,
                "event": {"agent_id": 7, "cause": "STARVATION", "tick": 8},
            },
        ],
    )
    traj = load_population_trajectory(events, n_founders=1, n_ticks=10)
    # Pop: 1 founder; +1 at tick 5; -1 at tick 8.
    assert traj.population_at_tick == (1, 1, 1, 1, 1, 2, 2, 2, 1, 1)
    pairs = sorted(traj.lifespans)
    # 1 founder alive (0, 10); 1 born and died (5, 8).
    assert pairs == [(0, 10), (5, 8)]


def test_negative_n_founders_rejected(tmp_path: Path) -> None:
    events = tmp_path / "events.jsonl"
    _write_events(events, [])
    with pytest.raises(ValueError, match="n_founders"):
        load_population_trajectory(events, n_founders=-1, n_ticks=10)


def test_negative_n_ticks_rejected(tmp_path: Path) -> None:
    events = tmp_path / "events.jsonl"
    _write_events(events, [])
    with pytest.raises(ValueError, match="n_ticks"):
        load_population_trajectory(events, n_founders=5, n_ticks=-1)


def test_population_window_clipping(tmp_path: Path) -> None:
    """``mean_population_window`` clips to available indices."""
    events = tmp_path / "events.jsonl"
    _write_events(events, [])
    traj = load_population_trajectory(events, n_founders=4, n_ticks=10)
    # Constant 4; mean over any window is 4.
    assert traj.mean_population_window(0, 9) == 4.0
    assert traj.mean_population_window(-5, 9) == 4.0  # clipped at 0
    assert traj.mean_population_window(0, 1000) == 4.0  # clipped at 9
    assert traj.mean_population_window(15, 20) == 0.0  # entirely outside


# ---------------------------------------------------------------------------
# Percentile helper
# ---------------------------------------------------------------------------


def test_percentile_empty() -> None:
    assert _percentile([], 0.5) == 0.0


def test_percentile_single_value() -> None:
    assert _percentile([42], 0.5) == 42.0
    assert _percentile([42], 0.0) == 42.0
    assert _percentile([42], 1.0) == 42.0


def test_percentile_interpolated() -> None:
    """Linear interpolation: p50 of [1,2,3,4] sits at index 1.5 -> 2.5."""
    assert _percentile([1, 2, 3, 4], 0.5) == 2.5
    assert _percentile([1, 2, 3, 4], 0.0) == 1.0
    assert _percentile([1, 2, 3, 4], 1.0) == 4.0


# ---------------------------------------------------------------------------
# aggregate_cell
# ---------------------------------------------------------------------------


def test_aggregate_cell_empty() -> None:
    agg = aggregate_cell([], n_ticks=10)
    assert agg.n_seeds == 0
    assert agg.mean_peak_population == 0.0
    assert agg.starvation_deaths_by_window == {w[0]: 0 for w in STARVATION_WINDOWS}


def test_aggregate_cell_basic(tmp_path: Path) -> None:
    """Two synthetic trajectories: peaks 3 and 5, late-window means."""
    events1 = tmp_path / "ev1.jsonl"
    events2 = tmp_path / "ev2.jsonl"
    _write_events(
        events1,
        [
            {"type": "AgentBorn", "tick": 5, "event": {"agent_id": 10, "parent_id": 1}},
        ],
    )
    _write_events(
        events2,
        [
            {"type": "AgentBorn", "tick": 5, "event": {"agent_id": 20, "parent_id": 1}},
            {"type": "AgentBorn", "tick": 6, "event": {"agent_id": 21, "parent_id": 1}},
            {"type": "AgentBorn", "tick": 7, "event": {"agent_id": 22, "parent_id": 1}},
        ],
    )
    t1 = load_population_trajectory(events1, n_founders=2, n_ticks=10)
    t2 = load_population_trajectory(events2, n_founders=2, n_ticks=10)
    # t1 peaks at 3 (2 founders + 1 born); t2 peaks at 5.
    assert t1.peak_population == 3
    assert t2.peak_population == 5
    agg = aggregate_cell([t1, t2], n_ticks=10, late_window_start=5)
    assert agg.n_seeds == 2
    assert agg.mean_peak_population == 4.0  # (3 + 5) / 2
    assert agg.lifespan_p50 > 0  # at least some agent lifespans recorded


def test_aggregate_cell_starvation_buckets(tmp_path: Path) -> None:
    """Starvation deaths in different windows aggregate into the right
    buckets."""
    events = tmp_path / "ev.jsonl"
    _write_events(
        events,
        [
            {"type": "AgentDied", "tick": 25, "event": {"agent_id": 1, "cause": "STARVATION"}},
            {"type": "AgentDied", "tick": 75, "event": {"agent_id": 2, "cause": "STARVATION"}},
            {"type": "AgentDied", "tick": 75, "event": {"agent_id": 3, "cause": "STARVATION"}},
            {"type": "AgentDied", "tick": 175, "event": {"agent_id": 4, "cause": "STARVATION"}},
        ],
    )
    traj = load_population_trajectory(events, n_founders=4, n_ticks=200)
    agg = aggregate_cell([traj], n_ticks=200)
    assert agg.starvation_deaths_by_window["0-49"] == 1
    assert agg.starvation_deaths_by_window["50-99"] == 2
    assert agg.starvation_deaths_by_window["100-149"] == 0
    assert agg.starvation_deaths_by_window["150-199"] == 1
    # peak bucket = 50-99 (count 2).
    assert agg.starvation_peak_window == "50-99"


# ---------------------------------------------------------------------------
# Smoke test against a real on-disk events.jsonl from the v0.23 sweep.
# Skipped if the artifact is absent (e.g., on a fresh checkout).
# ---------------------------------------------------------------------------


def test_smoke_against_v0_23_artifact() -> None:
    """The v0.23 sweep on this repo's runs/ directory produces a
    realistic events.jsonl. Loader must walk it without raising and
    produce sensible aggregates."""
    p = Path(
        "runs/fear-hunger-v0.23-tight_gradient/arms/transfer-1500-hzd0-influx-1.0/seed-1/events.jsonl"
    )
    if not p.exists():
        pytest.skip(f"smoke artifact {p} absent")
    traj = load_population_trajectory(p, n_founders=5, n_ticks=200)
    assert len(traj.population_at_tick) == 200
    # Founders + at least some births -> peak >= n_founders.
    assert traj.peak_population >= 5
    # Population trajectory must be non-negative.
    assert all(p >= 0 for p in traj.population_at_tick)
    # Lifespans must be non-negative.
    assert all(dt >= bt for bt, dt in traj.lifespans)
    # Aggregate shape sanity.
    agg = aggregate_cell([traj], n_ticks=200)
    assert isinstance(agg, CellAggregate)
    assert agg.n_seeds == 1
    assert agg.lifespan_p50 >= 0
