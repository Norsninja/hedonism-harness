"""Smoke + structural tests for the v0.2 positive-control runner."""

from __future__ import annotations

import csv
from pathlib import Path

from hedonism_harness.experiments.positive_control import (
    ALL_CONDITIONS,
    DEFAULT_CONDITION,
    aggregate,
    run_positive_control,
)


def test_all_conditions_includes_default_plus_archetypes() -> None:
    assert ALL_CONDITIONS[0] == DEFAULT_CONDITION
    assert set(ALL_CONDITIONS) == {"default", "fearful", "reckless", "balanced", "explorer"}


def test_aggregate_with_no_results_is_zero_filled() -> None:
    agg = aggregate("nobody", [])
    assert agg.n_seeds == 0
    assert agg.mean_population_end == 0.0
    assert agg.total_food_events == 0


def test_run_positive_control_writes_full_artifact_tree(tmp_path: Path) -> None:
    """One seed across five conditions, short tick budget — verifies the layout."""
    by_condition = run_positive_control(
        seeds=[1],
        runs_root=tmp_path,
        batch_id="smoke",
        n_ticks=20,
        n_founders=2,
        snapshot_tick=5,
    )
    assert set(by_condition.keys()) == set(ALL_CONDITIONS)
    for condition, results in by_condition.items():
        assert len(results) == 1, f"{condition}: expected 1 seed, got {len(results)}"

    batch_root = tmp_path / "smoke"
    assert (batch_root / "comparison.csv").is_file()

    rows = list(csv.DictReader((batch_root / "comparison.csv").open()))
    assert {r["condition"] for r in rows} == set(ALL_CONDITIONS)

    # One per-condition summary CSV + at least one per-seed run dir per condition.
    for condition in ALL_CONDITIONS:
        cond_dir = batch_root / condition
        assert (cond_dir / "summary.csv").is_file()
        assert (cond_dir / "seed-1").is_dir()
        assert (cond_dir / "seed-1" / "manifest.json").is_file()

    # ASCII snapshot per condition.
    for condition in ALL_CONDITIONS:
        snap = batch_root / "snapshots" / f"{condition}.txt"
        assert snap.is_file()
        text = snap.read_text()
        assert f"condition={condition}" in text


def test_per_condition_summary_csvs_carry_seed_rows(tmp_path: Path) -> None:
    """Per-condition summary.csv should have exactly one row per seed."""
    run_positive_control(
        seeds=[1, 2],
        runs_root=tmp_path,
        batch_id="smoke3",
        n_ticks=15,
        n_founders=2,
        snapshot_tick=5,
    )
    for condition in ALL_CONDITIONS:
        rows = list(csv.DictReader((tmp_path / "smoke3" / condition / "summary.csv").open()))
        assert [r["seed"] for r in rows] == ["1", "2"], f"{condition}: {rows}"
