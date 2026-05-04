"""Smoke + determinism tests for the Fear-Hunger Conflict Chamber."""

from __future__ import annotations

import csv
import json
from pathlib import Path

from hedonism_harness.core.world import CellKind
from hedonism_harness.experiments.batch import run_chamber_batch
from hedonism_harness.experiments.fear_hunger_chamber import (
    ChamberLayout,
    build_chamber_layout,
    paint_chamber,
    run_chamber,
)
from hedonism_harness.model import HHModel


def test_layout_columns_paint_correctly() -> None:
    layout = ChamberLayout()
    cfg = build_chamber_layout(layout).model_copy(update={"seed": 0})
    model = HHModel(cfg, founders=[])
    paint_chamber(model, layout)

    # Sample a row and verify column kinds.
    y = layout.height // 2
    for x in range(layout.safe_x_min, layout.safe_x_max + 1):
        assert model.world.kind_layer[x, y] == CellKind.SAFE
    for x in range(layout.hazard_x_min, layout.hazard_x_max + 1):
        assert model.world.kind_layer[x, y] == CellKind.HAZARD
        assert model.world.hazard_damage[x, y] > 0
    for x in range(layout.food_x_min, layout.food_x_max + 1):
        assert model.world.kind_layer[x, y] == CellKind.FOOD
        assert model.world.food_value[x, y] > 0
    # Gap columns between zones remain EMPTY.
    gap_x = layout.safe_x_max + 1
    assert model.world.kind_layer[gap_x, y] == CellKind.EMPTY


def test_run_chamber_writes_all_artifacts(tmp_path: Path) -> None:
    result = run_chamber(
        seed=42,
        runs_root=tmp_path,
        run_id="t1",
        n_founders=3,
        n_ticks=20,
    )
    assert result.run_id == "t1"
    assert result.population_start == 3
    assert result.ticks_completed > 0

    out_dir = tmp_path / "t1"
    expected = [
        "config.json",
        "manifest.json",
        "episode_metrics.csv",
        "agent_lifetimes.csv",
        "lineages.csv",
        "events.jsonl",
        "summary.md",
    ]
    for name in expected:
        f = out_dir / name
        assert f.is_file(), f"missing {name}"
        assert f.stat().st_size > 0

    # episode_metrics.csv has the seed we passed.
    rows = list(csv.DictReader((out_dir / "episode_metrics.csv").open()))
    assert len(rows) == 1
    assert rows[0]["seed"] == "42"

    # events.jsonl is in envelope shape: {"tick": int, "type": str, "event": dict}.
    lines = (out_dir / "events.jsonl").read_text().strip().splitlines()
    assert lines, "events.jsonl should not be empty"
    payload = json.loads(lines[0])
    assert {"tick", "type", "event"} <= set(payload.keys())


def test_run_chamber_is_deterministic_under_same_seed(tmp_path: Path) -> None:
    """Same seed -> same per-run summary fields. Validates the chamber driver
    didn't introduce hidden RNG (e.g. via wall-clock or dict ordering)."""
    a = run_chamber(seed=42, runs_root=tmp_path, run_id="a", n_founders=3, n_ticks=15)
    b = run_chamber(seed=42, runs_root=tmp_path, run_id="b", n_founders=3, n_ticks=15)

    fields_to_compare = (
        "ticks_completed",
        "population_end",
        "starvation_deaths",
        "injury_deaths",
        "food_events",
        "hazard_entries",
        "hazard_damage_total",
        "births",
        "reproduction_requests",
        "moves",
        "stays",
    )
    for f in fields_to_compare:
        assert getattr(a, f) == getattr(b, f), f"{f} diverged across same-seed runs"


def test_run_chamber_different_seed_produces_different_outcome(tmp_path: Path) -> None:
    """Seeds that change the trait roll + exploration_noise sequence must change
    at least one observed counter over a long-enough run.

    Short runs in the safe zone tend to alias (agents STAY, noise rarely
    fires), so we run long enough that metabolism + occasional moves diverge.
    """
    a = run_chamber(seed=42, runs_root=tmp_path, run_id="a", n_founders=3, n_ticks=80)
    b = run_chamber(seed=12345, runs_root=tmp_path, run_id="b", n_founders=3, n_ticks=80)
    # At least one non-trivial counter differs across seeds.
    assert (
        a.moves != b.moves
        or a.food_events != b.food_events
        or a.hazard_entries != b.hazard_entries
        or a.starvation_deaths != b.starvation_deaths
        or a.injury_deaths != b.injury_deaths
    )


def test_aggregator_sender_filtering_isolates_runs(tmp_path: Path) -> None:
    """Two chamber runs sharing a process must not cross-contaminate metrics.

    This is the practical test of the sender-filtering decision: the
    aggregators inside ``run_chamber`` are scoped to their model, so each
    run reports its own counters.
    """
    run_chamber(seed=1, runs_root=tmp_path, run_id="a", n_founders=2, n_ticks=10)
    run_chamber(seed=2, runs_root=tmp_path, run_id="b", n_founders=2, n_ticks=10)
    # If sender filtering were broken, run b would inherit run a's tallies
    # (running totals would never reset). They are independent objects, so
    # any equality is coincidence — but at least one counter usually differs.
    # The real guarantee is "they each only saw their own model's events" —
    # we assert this by counting per-run lifetime records.
    rows_a = list(csv.DictReader((tmp_path / "a" / "agent_lifetimes.csv").open()))
    rows_b = list(csv.DictReader((tmp_path / "b" / "agent_lifetimes.csv").open()))
    assert len(rows_a) == 2
    assert len(rows_b) == 2


def test_batch_runner_writes_summary_csv(tmp_path: Path) -> None:
    results = run_chamber_batch(
        seeds=[1, 2, 3],
        runs_root=tmp_path,
        batch_id="batch-A",
        n_ticks=10,
        n_founders=2,
    )
    assert len(results) == 3
    summary_csv = tmp_path / "batch-A" / "summary.csv"
    assert summary_csv.is_file()
    rows = list(csv.DictReader(summary_csv.open()))
    assert [r["seed"] for r in rows] == ["1", "2", "3"]
    # Each per-seed run dir exists.
    for seed in (1, 2, 3):
        run_dir = tmp_path / "batch-A" / f"seed-{seed}"
        assert run_dir.is_dir()
        assert (run_dir / "summary.md").is_file()
