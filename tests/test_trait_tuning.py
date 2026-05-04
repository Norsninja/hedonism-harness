"""Smoke + structural tests for the v0.5 trait-tuning sweep driver."""

from __future__ import annotations

import csv
from pathlib import Path

from hedonism_harness.experiments.trait_configs import ALL_TRAIT_CONFIGS
from hedonism_harness.experiments.trait_tuning import (
    TraitConfigAggregate,
    aggregate,
    evaluate_criteria,
    run_trait_tuning,
)


def test_smoke_run_produces_full_artifact_tree(tmp_path: Path) -> None:
    """One seed across both trait configs, short tick budget."""
    by_config = run_trait_tuning(
        seeds=[1],
        runs_root=tmp_path,
        batch_id="smoke",
        n_ticks=15,
        n_founders=2,
        snapshot_tick=5,
    )
    assert set(by_config.keys()) == set(ALL_TRAIT_CONFIGS.keys())

    batch_root = tmp_path / "smoke"
    assert (batch_root / "comparison.csv").is_file()
    rows = list(csv.DictReader((batch_root / "comparison.csv").open()))
    assert {r["trait_config"] for r in rows} == set(ALL_TRAIT_CONFIGS.keys())

    for name in ALL_TRAIT_CONFIGS:
        cfg_dir = batch_root / name
        assert (cfg_dir / "summary.csv").is_file()
        assert (cfg_dir / "seed-1").is_dir()
        snap = batch_root / "snapshots" / f"{name}.txt"
        assert snap.is_file()
        assert f"trait_config={name}" in snap.read_text()


def _agg(name: str, **kwargs: object) -> TraitConfigAggregate:
    base: dict[str, object] = {
        "trait_config": name,
        "n_seeds": 8,
        "mean_population_end": 0.0,
        "seeds_with_survivors": 0,
        "seeds_with_any_starvation": 0,
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
    return TraitConfigAggregate(**base)  # type: ignore[arg-type]


def test_evaluate_criteria_all_null_returns_all_false() -> None:
    aggregates = {
        "default": _agg("default"),
        "permissive": _agg("permissive"),
    }
    assert evaluate_criteria(aggregates) == {
        "pursuit_emerges": False,
        "improvement_over_baseline": False,
        "diversity_preserved": False,
    }


def test_evaluate_criteria_passes_all_three_when_permissive_is_better() -> None:
    aggregates = {
        "default": _agg("default", total_food_events=0, seeds_with_any_starvation=8),
        "permissive": _agg(
            "permissive",
            total_food_events=10,
            seeds_with_any_starvation=4,  # diversity preserved (some starvations)
        ),
    }
    assert evaluate_criteria(aggregates) == {
        "pursuit_emerges": True,
        "improvement_over_baseline": True,
        "diversity_preserved": True,
    }


def test_evaluate_criteria_diversity_fails_when_no_starvation() -> None:
    """Permissive that produces 100% survival across all seeds fails diversity."""
    aggregates = {
        "default": _agg("default", total_food_events=0),
        "permissive": _agg(
            "permissive",
            total_food_events=20,
            seeds_with_any_starvation=0,  # no seed had any starvation -> over-tuned
        ),
    }
    verdict = evaluate_criteria(aggregates)
    assert verdict["pursuit_emerges"] is True
    assert verdict["improvement_over_baseline"] is True
    assert verdict["diversity_preserved"] is False


def test_aggregate_with_no_results_is_zero_filled() -> None:
    agg = aggregate("nobody", [])
    assert agg.n_seeds == 0
    assert agg.total_food_events == 0
    assert agg.seeds_with_survivors == 0
