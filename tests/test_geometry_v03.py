"""Smoke + structural tests for the v0.3 geometry sweep driver."""

from __future__ import annotations

import csv
from pathlib import Path

from hedonism_harness.experiments.geometry_v03 import (
    LayoutConditionRow,
    evaluate_criteria,
    run_geometry_v03,
)
from hedonism_harness.experiments.layouts import ALL_LAYOUTS
from hedonism_harness.experiments.positive_control import ALL_CONDITIONS


def test_smoke_run_produces_full_artifact_tree(tmp_path: Path) -> None:
    """One seed across all layouts and all conditions, short tick budget."""
    by_layout = run_geometry_v03(
        seeds=[1],
        runs_root=tmp_path,
        batch_id="smoke",
        n_ticks=15,
        n_founders=2,
        snapshot_tick=5,
    )
    assert set(by_layout.keys()) == set(ALL_LAYOUTS.keys())
    for layout_name, by_condition in by_layout.items():
        assert set(by_condition.keys()) == set(ALL_CONDITIONS), layout_name
        for condition, results in by_condition.items():
            assert len(results) == 1, f"{layout_name}/{condition}: expected 1 seed"

    batch_root = tmp_path / "smoke"
    assert (batch_root / "layout_comparison.csv").is_file()
    rows = list(csv.DictReader((batch_root / "layout_comparison.csv").open()))
    expected_pairs = {(layout, cond) for layout in ALL_LAYOUTS for cond in ALL_CONDITIONS}
    actual_pairs = {(r["layout"], r["condition"]) for r in rows}
    assert actual_pairs == expected_pairs

    # Each per-layout sub-batch has its own comparison + snapshots.
    for layout_name in ALL_LAYOUTS:
        assert (batch_root / layout_name / "comparison.csv").is_file()
        for condition in ALL_CONDITIONS:
            assert (batch_root / layout_name / "snapshots" / f"{condition}.txt").is_file()


def _row(layout: str, condition: str, **kwargs: object) -> LayoutConditionRow:
    base: dict[str, object] = {
        "layout": layout,
        "condition": condition,
        "n_seeds": 8,
        "mean_population_end": 0.0,
        "total_starvation_deaths": 0,
        "total_injury_deaths": 0,
        "total_food_events": 0,
        "total_hazard_entries": 0,
        "total_hazard_damage": 0.0,
        "total_births": 0,
        "total_reproduction_requests": 0,
        "total_moves": 0,
        "total_stays": 0,
    }
    base.update(kwargs)
    return LayoutConditionRow(**base)  # type: ignore[arg-type]


def test_evaluate_criteria_all_null_returns_all_false() -> None:
    rows = {(layout, cond): _row(layout, cond) for layout in ALL_LAYOUTS for cond in ALL_CONDITIONS}
    verdict = evaluate_criteria(rows)
    assert verdict == {
        "any_archetype_enters_hazard": False,
        "reckless_2x_fearful_in_some_layout": False,
        "any_food_or_hazard_signal": False,
    }


def test_evaluate_criteria_reckless_with_zero_fearful_passes_2x_rule() -> None:
    rows = {
        ("default", "fearful"): _row("default", "fearful", total_hazard_entries=0),
        ("default", "reckless"): _row("default", "reckless", total_hazard_entries=3),
    }
    verdict = evaluate_criteria(rows)
    assert verdict["any_archetype_enters_hazard"] is True
    assert verdict["reckless_2x_fearful_in_some_layout"] is True
    assert verdict["any_food_or_hazard_signal"] is False  # damage still zero


def test_evaluate_criteria_food_event_alone_satisfies_signal_criterion() -> None:
    rows = {
        ("tight_gradient", "reckless"): _row("tight_gradient", "reckless", total_food_events=2),
    }
    verdict = evaluate_criteria(rows)
    assert verdict["any_food_or_hazard_signal"] is True


def test_evaluate_criteria_reckless_below_2x_floor_fails_rule() -> None:
    """Reckless with hazard_entries==fearful's must NOT pass the 2x rule."""
    rows = {
        ("default", "fearful"): _row("default", "fearful", total_hazard_entries=5),
        ("default", "reckless"): _row("default", "reckless", total_hazard_entries=6),
    }
    verdict = evaluate_criteria(rows)
    assert verdict["reckless_2x_fearful_in_some_layout"] is False
