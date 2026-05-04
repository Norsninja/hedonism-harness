"""Fear-Hunger v0.2 positive-control batch driver.

Runs the canonical Fear-Hunger Chamber under five trait conditions:

    default | fearful | reckless | balanced | explorer

The default condition uses the v0.1 i.i.d.-uniform trait distribution; the
four archetype conditions inject deterministic ``Traits`` from
``trait_archetypes`` so every founder in a condition shares identical traits.

For each (condition, seed) pair this driver runs ``run_chamber``, then captures
one ASCII snapshot per condition (using the lowest seed) at a fixed tick. A
top-level ``comparison.csv`` aggregates per-condition counters across seeds.

Goal (binary): does at least one archetype condition produce ≥1 hazard entry
across all seeds AND differ in food / hazard outcomes from the Fearful floor?
If yes the harness is phenotype-capable and v0.2 succeeds. If no, the next
move is inspecting ``core/valence.py`` rather than tuning trait defaults.
"""

from __future__ import annotations

import csv
from collections.abc import Iterable, Sequence
from dataclasses import asdict, dataclass
from pathlib import Path

from hedonism_harness.core.config import (
    ActionConfig,
    BodyConfig,
    ReproductionConfig,
    WorldConfig,
)
from hedonism_harness.core.traits import TraitConfig
from hedonism_harness.experiments.fear_hunger_chamber import (
    ChamberLayout,
    ChamberRunResult,
    paint_chamber,
    run_chamber,
    spread_y,
)
from hedonism_harness.experiments.snapshots import render_model_snapshot
from hedonism_harness.experiments.trait_archetypes import ARCHETYPE_NAMES, archetype_traits
from hedonism_harness.model import FounderSpec, HHModel
from hedonism_harness.policies.hedonism_policy import HedonismPolicy

DEFAULT_CONDITION = "default"
ALL_CONDITIONS: tuple[str, ...] = (DEFAULT_CONDITION, *ARCHETYPE_NAMES)


def _policy_factory() -> HedonismPolicy:
    """Match the v0.1 pilot's exploration_noise so v0.2 differs only in traits."""
    return HedonismPolicy(exploration_noise=0.05)


@dataclass(frozen=True)
class ConditionAggregate:
    """Per-condition aggregates over the seed sweep."""

    condition: str
    n_seeds: int
    mean_population_end: float
    total_starvation_deaths: int
    total_injury_deaths: int
    total_food_events: int
    total_hazard_entries: int
    total_hazard_damage: float
    total_births: int
    total_reproduction_requests: int
    total_moves: int
    total_stays: int


def aggregate(condition: str, results: Sequence[ChamberRunResult]) -> ConditionAggregate:
    n = len(results)
    if n == 0:
        return ConditionAggregate(
            condition=condition,
            n_seeds=0,
            mean_population_end=0.0,
            total_starvation_deaths=0,
            total_injury_deaths=0,
            total_food_events=0,
            total_hazard_entries=0,
            total_hazard_damage=0.0,
            total_births=0,
            total_reproduction_requests=0,
            total_moves=0,
            total_stays=0,
        )
    return ConditionAggregate(
        condition=condition,
        n_seeds=n,
        mean_population_end=sum(r.population_end for r in results) / n,
        total_starvation_deaths=sum(r.starvation_deaths for r in results),
        total_injury_deaths=sum(r.injury_deaths for r in results),
        total_food_events=sum(r.food_events for r in results),
        total_hazard_entries=sum(r.hazard_entries for r in results),
        total_hazard_damage=sum(r.hazard_damage_total for r in results),
        total_births=sum(r.births for r in results),
        total_reproduction_requests=sum(r.reproduction_requests for r in results),
        total_moves=sum(r.moves for r in results),
        total_stays=sum(r.stays for r in results),
    )


def _capture_snapshot(
    *,
    seed: int,
    n_founders: int,
    layout: ChamberLayout,
    snapshot_tick: int,
    condition: str,
) -> str:
    """Re-run a single seed up to ``snapshot_tick`` to capture an ASCII frame.

    The chamber driver doesn't expose a per-tick callback yet, so we rebuild
    a model directly here. This re-runs the same deterministic sequence the
    persisted run already executed (same seed -> same trajectory), so the
    snapshot is faithful to that run's tick ``snapshot_tick`` state.
    """
    world_cfg = WorldConfig(
        seed=seed,
        width=layout.width,
        height=layout.height,
        food_density=0.0,
        hazard_density=0.0,
        hazard_damage_default=8.0,
        food_value_default=20.0,
        safe_value_default=1.0,
    )
    spawn_x = layout.resolved_spawn_x
    spawn_ys = spread_y(n_founders, layout.height)
    traits_override = None if condition == DEFAULT_CONDITION else archetype_traits(condition)
    founders = [
        FounderSpec(
            x=spawn_x,
            y=y,
            policy_factory=_policy_factory,
            traits_override=traits_override,
        )
        for y in spawn_ys
    ]
    model = HHModel(
        world_cfg,
        founders=founders,
        body_config=BodyConfig(),
        action_config=ActionConfig(),
        reproduction_config=ReproductionConfig(),
        trait_config=TraitConfig(),
    )
    paint_chamber(model, layout)
    for _ in range(snapshot_tick):
        model.step()
    return render_model_snapshot(model)


def run_positive_control(
    *,
    seeds: Iterable[int],
    runs_root: Path,
    batch_id: str = "fear-hunger-v0.2",
    n_ticks: int = 200,
    n_founders: int = 5,
    snapshot_tick: int = 100,
    snapshot_seed: int | None = None,
    layout: ChamberLayout | None = None,
    conditions: Sequence[str] = ALL_CONDITIONS,
) -> dict[str, list[ChamberRunResult]]:
    """Run all (condition, seed) pairs, write artifacts, return results-by-condition.

    Output layout under ``runs_root/batch_id/``::

        comparison.csv             # one row per condition (aggregates)
        snapshots/{condition}.txt  # one ASCII frame per condition
        {condition}/seed-{seed}/   # per-run dir from run_chamber
        {condition}/summary.csv    # per-condition seed-level summary
    """
    layout = layout or ChamberLayout()
    seeds_list = list(seeds)
    if not seeds_list:
        msg = "run_positive_control requires at least one seed"
        raise ValueError(msg)
    snapshot_seed = snapshot_seed if snapshot_seed is not None else min(seeds_list)

    batch_root = runs_root / batch_id
    batch_root.mkdir(parents=True, exist_ok=True)
    snapshots_dir = batch_root / "snapshots"
    snapshots_dir.mkdir(exist_ok=True)

    by_condition: dict[str, list[ChamberRunResult]] = {}
    for condition in conditions:
        traits_override = None if condition == DEFAULT_CONDITION else archetype_traits(condition)
        condition_root = batch_root / condition
        condition_root.mkdir(parents=True, exist_ok=True)

        results: list[ChamberRunResult] = []
        for seed in seeds_list:
            result = run_chamber(
                seed=seed,
                runs_root=condition_root,
                run_id=f"seed-{seed}",
                n_founders=n_founders,
                n_ticks=n_ticks,
                layout=layout,
                policy_factory=_policy_factory,
                traits_override=traits_override,
                condition=condition,
            )
            results.append(result)
        by_condition[condition] = results

        _write_per_condition_summary(condition_root / "summary.csv", results)

        snapshot = _capture_snapshot(
            seed=snapshot_seed,
            n_founders=n_founders,
            layout=layout,
            snapshot_tick=snapshot_tick,
            condition=condition,
        )
        (snapshots_dir / f"{condition}.txt").write_text(
            f"# condition={condition} seed={snapshot_seed} tick={snapshot_tick}\n{snapshot}\n"
        )

    aggregates = [aggregate(c, by_condition[c]) for c in conditions]
    _write_comparison_csv(batch_root / "comparison.csv", aggregates)

    return by_condition


def _write_per_condition_summary(path: Path, results: Sequence[ChamberRunResult]) -> None:
    fieldnames = [
        "run_id",
        "seed",
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
    ]
    with path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for result in results:
            row = {k: v for k, v in asdict(result).items() if k in fieldnames}
            row["hazard_damage_total"] = round(result.hazard_damage_total, 6)
            writer.writerow(row)


def _write_comparison_csv(path: Path, aggregates: Sequence[ConditionAggregate]) -> None:
    fieldnames = [
        "condition",
        "n_seeds",
        "mean_population_end",
        "total_starvation_deaths",
        "total_injury_deaths",
        "total_food_events",
        "total_hazard_entries",
        "total_hazard_damage",
        "total_births",
        "total_reproduction_requests",
        "total_moves",
        "total_stays",
    ]
    with path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for agg in aggregates:
            row = asdict(agg)
            row["mean_population_end"] = round(agg.mean_population_end, 4)
            row["total_hazard_damage"] = round(agg.total_hazard_damage, 6)
            writer.writerow(row)
