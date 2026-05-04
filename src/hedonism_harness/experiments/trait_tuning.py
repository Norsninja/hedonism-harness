"""Fear-Hunger v0.5 trait-tuning sweep.

Tests whether shifting the default ``TraitConfig`` ranges within SPEC §8.1
master bounds produces mixed-phenotype populations under random sampling.

The v0.4 valence fix proved archetype phenotypes work in ``tight_gradient``,
but the ``default`` condition (i.i.d.-uniform from SPEC defaults) still
produced 1 hazard entry / 0 food events across 40 founder-runs. v0.5 holds
the chamber, valence, and hyperparameters constant; varies only the
``TraitConfig`` ranges that random sampling draws from.

Pre-registered binary criteria (against ``tight_gradient``):

  1. Pursuit emerges: permissive produces >= 1 food event across the
     8-seed * 5-founder = 40 random-traits population.
  2. Significant improvement: permissive food_events > baseline food_events.
  3. Diversity preserved: permissive does NOT show 100% survival across
     every seed -- at least one founder still dies of starvation.

Pre-registered failure -> action mapping:

  - All criteria fail: shifting trait ranges is not sufficient; v0.6
    explores distribution shape (Beta sampling) or wider ranges.
  - Criteria 1 + 2 pass, 3 fails: the shift over-tunes; narrow it.
  - All three pass: permissive_trait_config is a viable default
    candidate; user decides whether to promote to ``core/traits.py``.
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
from hedonism_harness.experiments.fear_hunger_chamber import (
    ChamberLayout,
    ChamberRunResult,
    paint_chamber,
    run_chamber,
)
from hedonism_harness.experiments.layouts import tight_gradient_layout
from hedonism_harness.experiments.snapshots import render_model_snapshot
from hedonism_harness.experiments.trait_configs import ALL_TRAIT_CONFIGS, trait_config_by_name
from hedonism_harness.model import FounderSpec, HHModel
from hedonism_harness.policies.hedonism_policy import HedonismPolicy


def _policy_factory() -> HedonismPolicy:
    """Match the v0.1 pilot's exploration_noise so v0.5 differs only in trait config."""
    return HedonismPolicy(exploration_noise=0.05)


@dataclass(frozen=True)
class TraitConfigAggregate:
    """Per-trait-config aggregates over the seed sweep."""

    trait_config: str
    n_seeds: int
    mean_population_end: float
    seeds_with_survivors: int
    seeds_with_any_starvation: int
    total_starvation_deaths: int
    total_injury_deaths: int
    total_food_events: int
    total_hazard_entries: int
    total_hazard_damage: float
    total_births: int
    total_reproduction_requests: int
    total_moves: int
    total_stays: int


def aggregate(trait_config: str, results: Sequence[ChamberRunResult]) -> TraitConfigAggregate:
    n = len(results)
    if n == 0:
        return TraitConfigAggregate(
            trait_config=trait_config,
            n_seeds=0,
            mean_population_end=0.0,
            seeds_with_survivors=0,
            seeds_with_any_starvation=0,
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
    return TraitConfigAggregate(
        trait_config=trait_config,
        n_seeds=n,
        mean_population_end=sum(r.population_end for r in results) / n,
        seeds_with_survivors=sum(1 for r in results if r.population_end > 0),
        seeds_with_any_starvation=sum(1 for r in results if r.starvation_deaths > 0),
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
    trait_config_name: str,
) -> str:
    """Re-run a single seed up to ``snapshot_tick`` to capture an ASCII frame.

    Mirrors ``positive_control._capture_snapshot`` but takes a trait_config
    name instead of a condition; uses random_traits sampling (no overrides).
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
    step = max(1, layout.height // n_founders) if n_founders > 1 else 1
    spawn_ys = (
        [layout.height // 2]
        if n_founders <= 1
        else [min(layout.height - 1, i * step) for i in range(n_founders)]
    )
    founders = [FounderSpec(x=spawn_x, y=y, policy_factory=_policy_factory) for y in spawn_ys]
    model = HHModel(
        world_cfg,
        founders=founders,
        body_config=BodyConfig(),
        action_config=ActionConfig(),
        reproduction_config=ReproductionConfig(),
        trait_config=trait_config_by_name(trait_config_name),
    )
    paint_chamber(model, layout)
    for _ in range(snapshot_tick):
        model.step()
    return render_model_snapshot(model)


def run_trait_tuning(
    *,
    seeds: Iterable[int],
    runs_root: Path,
    batch_id: str = "fear-hunger-v0.5",
    n_ticks: int = 200,
    n_founders: int = 5,
    snapshot_tick: int = 100,
    snapshot_seed: int | None = None,
    layout: ChamberLayout | None = None,
    trait_config_names: Sequence[str] = tuple(ALL_TRAIT_CONFIGS.keys()),
) -> dict[str, list[ChamberRunResult]]:
    """Run all (trait_config, seed) pairs in ``layout``; return results-by-config.

    Output layout::

        runs_root/batch_id/
            comparison.csv             # one row per trait_config (aggregates)
            snapshots/{name}.txt       # one ASCII frame per config
            {name}/
                summary.csv            # per-config seed-level summary
                seed-{N}/...           # per-run dir from run_chamber
    """
    layout = layout or tight_gradient_layout()
    seeds_list = list(seeds)
    if not seeds_list:
        msg = "run_trait_tuning requires at least one seed"
        raise ValueError(msg)
    snapshot_seed = snapshot_seed if snapshot_seed is not None else min(seeds_list)

    batch_root = runs_root / batch_id
    batch_root.mkdir(parents=True, exist_ok=True)
    snapshots_dir = batch_root / "snapshots"
    snapshots_dir.mkdir(exist_ok=True)

    by_config: dict[str, list[ChamberRunResult]] = {}
    for cfg_name in trait_config_names:
        cfg = trait_config_by_name(cfg_name)
        config_root = batch_root / cfg_name
        config_root.mkdir(parents=True, exist_ok=True)

        results: list[ChamberRunResult] = []
        for seed in seeds_list:
            result = run_chamber(
                seed=seed,
                runs_root=config_root,
                run_id=f"seed-{seed}",
                n_founders=n_founders,
                n_ticks=n_ticks,
                layout=layout,
                policy_factory=_policy_factory,
                trait_config=cfg,
                condition=cfg_name,
            )
            results.append(result)
        by_config[cfg_name] = results

        _write_per_config_summary(config_root / "summary.csv", results)

        snapshot = _capture_snapshot(
            seed=snapshot_seed,
            n_founders=n_founders,
            layout=layout,
            snapshot_tick=snapshot_tick,
            trait_config_name=cfg_name,
        )
        (snapshots_dir / f"{cfg_name}.txt").write_text(
            f"# trait_config={cfg_name} seed={snapshot_seed} tick={snapshot_tick}\n{snapshot}\n"
        )

    aggregates = [aggregate(c, by_config[c]) for c in trait_config_names]
    _write_comparison_csv(batch_root / "comparison.csv", aggregates)

    return by_config


def evaluate_criteria(
    aggregates: dict[str, TraitConfigAggregate],
) -> dict[str, bool]:
    """Apply the three pre-registered v0.5 success criteria.

    Compares ``permissive`` against ``default``. Returns a dict of bools.
    Missing configs make all criteria False.
    """
    baseline = aggregates.get("default")
    permissive = aggregates.get("permissive")
    if baseline is None or permissive is None:
        return {
            "pursuit_emerges": False,
            "improvement_over_baseline": False,
            "diversity_preserved": False,
        }
    return {
        "pursuit_emerges": permissive.total_food_events >= 1,
        "improvement_over_baseline": permissive.total_food_events > baseline.total_food_events,
        # Diversity = at least one seed where someone starved. If every seed
        # produces zero starvation, the shift collapsed phenotype variance.
        "diversity_preserved": permissive.seeds_with_any_starvation > 0,
    }


def _write_per_config_summary(path: Path, results: Sequence[ChamberRunResult]) -> None:
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


def _write_comparison_csv(path: Path, aggregates: Sequence[TraitConfigAggregate]) -> None:
    fieldnames = [
        "trait_config",
        "n_seeds",
        "mean_population_end",
        "seeds_with_survivors",
        "seeds_with_any_starvation",
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
