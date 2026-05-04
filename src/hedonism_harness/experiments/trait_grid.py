"""Fear-Hunger v0.6 trait-config grid sweep.

Validates whether the v0.5 ``permissive`` config is a hand-tuned local
optimum or just a lucky point. Holds layout, valence, sensors, repro,
ticks, founders constant; varies only the three load-bearing trait
range knobs from the v0.4 evidence:

  - ``fear_max``     in {1.0, 1.5, 2.0}    (fear_sensitivity ceiling)
  - ``hunger_min``   in {0.75, 1.0, 1.25}  (hunger_pain_sensitivity floor)
  - ``risk_min``     in {0.25, 0.4, 0.55}  (risk_tolerance floor)

3 * 3 * 3 = 27 cells * 8 seeds = 216 runs.

Pre-registered "viable candidate" rule (a cell qualifies iff all four):

  1. food_events > baseline (SPEC default condition).
  2. hazard_entries > baseline.
  3. >= 1 survivor at tick 200 in at least one seed (cliff filter).
  4. starvation still present in some seed (no total collapse).

Pre-registered failure -> action mapping:

  - All 27 cells fail -> range-shifting alone is insufficient; v0.6.5
    explores distribution shape (Beta sampling) before continuing.
  - Multiple cells qualify -> pick the cell **closest to SPEC defaults**
    (least permissive among qualifiers). Conservative tightening rule.
  - Only the v0.5 cell qualifies -> hand-tuning was a local optimum;
    promote ``permissive`` as documented and proceed to v0.7.
  - A different cell qualifies more strongly -> adopt that cell as the
    v0.7 fixed config; document v0.5 as suboptimal.

Primary score for "more strongly" tie-break: ``food_events``.
``survivors`` is the cliff filter (any cell with 0 survivors is
disqualified regardless of food_events).
"""

from __future__ import annotations

import csv
import itertools
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
from hedonism_harness.experiments.layouts import tight_gradient_layout
from hedonism_harness.experiments.snapshots import render_model_snapshot
from hedonism_harness.experiments.trait_configs import cell_id, tuned_trait_config
from hedonism_harness.model import FounderSpec, HHModel
from hedonism_harness.policies.hedonism_policy import HedonismPolicy

# ---------------------------------------------------------------------------
# Grid definition
# ---------------------------------------------------------------------------

FEAR_MAX_LEVELS: tuple[float, ...] = (1.0, 1.5, 2.0)
HUNGER_MIN_LEVELS: tuple[float, ...] = (0.75, 1.0, 1.25)
RISK_MIN_LEVELS: tuple[float, ...] = (0.25, 0.4, 0.55)


@dataclass(frozen=True)
class GridCell:
    """One point in the (fear_max, hunger_min, risk_min) grid."""

    fear_max: float
    hunger_min: float
    risk_min: float

    @property
    def id(self) -> str:
        return cell_id(fear_max=self.fear_max, hunger_min=self.hunger_min, risk_min=self.risk_min)

    def to_trait_config(self) -> TraitConfig:
        return tuned_trait_config(
            fear_max=self.fear_max, hunger_min=self.hunger_min, risk_min=self.risk_min
        )


def all_grid_cells() -> list[GridCell]:
    """Return the 27 (fear_max, hunger_min, risk_min) cells in stable order."""
    return [
        GridCell(fear_max=f, hunger_min=h, risk_min=r)
        for f, h, r in itertools.product(FEAR_MAX_LEVELS, HUNGER_MIN_LEVELS, RISK_MIN_LEVELS)
    ]


# ---------------------------------------------------------------------------
# Aggregates and criterion evaluation
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class GridCellAggregate:
    """Per-cell aggregates across the seed sweep."""

    cell_id: str
    fear_max: float
    hunger_min: float
    risk_min: float
    n_seeds: int
    seeds_with_survivors: int
    seeds_with_any_starvation: int
    total_starvation_deaths: int
    total_food_events: int
    total_hazard_entries: int
    total_hazard_damage: float
    total_births: int
    total_moves: int
    total_stays: int
    mean_population_end: float


def aggregate(cell: GridCell, results: Sequence[ChamberRunResult]) -> GridCellAggregate:
    n = len(results)
    if n == 0:
        return GridCellAggregate(
            cell_id=cell.id,
            fear_max=cell.fear_max,
            hunger_min=cell.hunger_min,
            risk_min=cell.risk_min,
            n_seeds=0,
            seeds_with_survivors=0,
            seeds_with_any_starvation=0,
            total_starvation_deaths=0,
            total_food_events=0,
            total_hazard_entries=0,
            total_hazard_damage=0.0,
            total_births=0,
            total_moves=0,
            total_stays=0,
            mean_population_end=0.0,
        )
    return GridCellAggregate(
        cell_id=cell.id,
        fear_max=cell.fear_max,
        hunger_min=cell.hunger_min,
        risk_min=cell.risk_min,
        n_seeds=n,
        seeds_with_survivors=sum(1 for r in results if r.population_end > 0),
        seeds_with_any_starvation=sum(1 for r in results if r.starvation_deaths > 0),
        total_starvation_deaths=sum(r.starvation_deaths for r in results),
        total_food_events=sum(r.food_events for r in results),
        total_hazard_entries=sum(r.hazard_entries for r in results),
        total_hazard_damage=sum(r.hazard_damage_total for r in results),
        total_births=sum(r.births for r in results),
        total_moves=sum(r.moves for r in results),
        total_stays=sum(r.stays for r in results),
        mean_population_end=sum(r.population_end for r in results) / n,
    )


def cell_qualifies(cell_agg: GridCellAggregate, baseline: GridCellAggregate) -> bool:
    """Apply the four pre-registered v0.6 viability criteria to one cell."""
    return (
        cell_agg.total_food_events > baseline.total_food_events
        and cell_agg.total_hazard_entries > baseline.total_hazard_entries
        and cell_agg.seeds_with_survivors >= 1
        and cell_agg.seeds_with_any_starvation > 0
    )


def _distance_to_spec_default(cell: GridCell) -> float:
    """Euclidean-ish distance from this cell to SPEC §8.1 defaults.

    SPEC defaults: fear_max=3.0, hunger_min=0.25, risk_min=0.0. Smaller
    distance = closer to SPEC = less permissive.

    Used to break ties among multiple qualifying cells per the
    pre-registered "pick the closest-to-SPEC qualifier" rule (v0.6
    failure-mapping mode 2).
    """
    return (3.0 - cell.fear_max) ** 2 + (cell.hunger_min - 0.25) ** 2 + (cell.risk_min - 0.0) ** 2


def select_winning_cell(
    aggregates: Sequence[GridCellAggregate],
    baseline: GridCellAggregate,
) -> GridCellAggregate | None:
    """Pick the v0.6 winner per the pre-registered failure-mapping rules.

    Returns None if no cell qualifies (all-fail branch). When multiple
    cells qualify, the primary score is ``total_food_events`` (highest
    wins). The tie-break is "closest to SPEC defaults" (least permissive).
    """
    qualifiers = [a for a in aggregates if cell_qualifies(a, baseline)]
    if not qualifiers:
        return None

    max_food = max(a.total_food_events for a in qualifiers)
    top_food = [a for a in qualifiers if a.total_food_events == max_food]
    if len(top_food) == 1:
        return top_food[0]

    # Tie on food_events: pick the one closest to SPEC defaults.
    return min(
        top_food,
        key=lambda a: _distance_to_spec_default(
            GridCell(fear_max=a.fear_max, hunger_min=a.hunger_min, risk_min=a.risk_min)
        ),
    )


# ---------------------------------------------------------------------------
# Driver
# ---------------------------------------------------------------------------


def _policy_factory() -> HedonismPolicy:
    return HedonismPolicy(exploration_noise=0.05)


def _run_baseline(
    *,
    seeds: Sequence[int],
    runs_root: Path,
    n_ticks: int,
    n_founders: int,
    layout: ChamberLayout,
) -> GridCellAggregate:
    """Run the SPEC default ``TraitConfig`` as the comparison baseline."""
    baseline_root = runs_root / "baseline-spec-default"
    baseline_root.mkdir(parents=True, exist_ok=True)
    results: list[ChamberRunResult] = []
    for seed in seeds:
        result = run_chamber(
            seed=seed,
            runs_root=baseline_root,
            run_id=f"seed-{seed}",
            n_founders=n_founders,
            n_ticks=n_ticks,
            layout=layout,
            policy_factory=_policy_factory,
            trait_config=TraitConfig(),  # SPEC §8.1 defaults
            condition="baseline-spec-default",
        )
        results.append(result)

    # Wrap in GridCellAggregate using sentinel knob values so the row appears
    # in the comparison CSV with a clearly-labeled cell_id.
    n = len(results)
    return GridCellAggregate(
        cell_id="baseline-spec-default",
        fear_max=3.0,
        hunger_min=0.25,
        risk_min=0.0,
        n_seeds=n,
        seeds_with_survivors=sum(1 for r in results if r.population_end > 0),
        seeds_with_any_starvation=sum(1 for r in results if r.starvation_deaths > 0),
        total_starvation_deaths=sum(r.starvation_deaths for r in results),
        total_food_events=sum(r.food_events for r in results),
        total_hazard_entries=sum(r.hazard_entries for r in results),
        total_hazard_damage=sum(r.hazard_damage_total for r in results),
        total_births=sum(r.births for r in results),
        total_moves=sum(r.moves for r in results),
        total_stays=sum(r.stays for r in results),
        mean_population_end=sum(r.population_end for r in results) / n if n else 0.0,
    )


def _capture_snapshot(
    *,
    seed: int,
    n_founders: int,
    layout: ChamberLayout,
    snapshot_tick: int,
    trait_config: TraitConfig,
) -> str:
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
    founders = [FounderSpec(x=spawn_x, y=y, policy_factory=_policy_factory) for y in spawn_ys]
    model = HHModel(
        world_cfg,
        founders=founders,
        body_config=BodyConfig(),
        action_config=ActionConfig(),
        reproduction_config=ReproductionConfig(),
        trait_config=trait_config,
    )
    paint_chamber(model, layout)
    for _ in range(snapshot_tick):
        model.step()
    return render_model_snapshot(model)


def run_trait_grid(
    *,
    seeds: Iterable[int],
    runs_root: Path,
    batch_id: str = "fear-hunger-v0.6",
    n_ticks: int = 200,
    n_founders: int = 5,
    snapshot_tick: int = 100,
    snapshot_seed: int | None = None,
    layout: ChamberLayout | None = None,
    cells: Sequence[GridCell] | None = None,
    write_snapshots_for_winner: bool = True,
) -> tuple[list[GridCellAggregate], GridCellAggregate, GridCellAggregate | None]:
    """Run baseline + 27-cell grid, write artifacts, return (aggs, baseline, winner).

    Output layout::

        runs_root/batch_id/
            baseline-spec-default/seed-{N}/...
            cells/{cell_id}/seed-{N}/...
            comparison.csv          # baseline + 27 cell rows
            winner.txt              # the chosen cell + criterion details
            snapshots/              # winner snapshot at snapshot_tick (seed=snapshot_seed)
    """
    layout = layout or tight_gradient_layout()
    seeds_list = list(seeds)
    if not seeds_list:
        msg = "run_trait_grid requires at least one seed"
        raise ValueError(msg)
    snapshot_seed = snapshot_seed if snapshot_seed is not None else min(seeds_list)
    cells = cells or all_grid_cells()

    batch_root = runs_root / batch_id
    batch_root.mkdir(parents=True, exist_ok=True)

    baseline_agg = _run_baseline(
        seeds=seeds_list,
        runs_root=batch_root,
        n_ticks=n_ticks,
        n_founders=n_founders,
        layout=layout,
    )

    cells_root = batch_root / "cells"
    cells_root.mkdir(parents=True, exist_ok=True)
    aggregates: list[GridCellAggregate] = []

    for cell in cells:
        cell_root = cells_root / cell.id
        cell_root.mkdir(parents=True, exist_ok=True)
        cell_results: list[ChamberRunResult] = []
        cell_cfg = cell.to_trait_config()
        for seed in seeds_list:
            result = run_chamber(
                seed=seed,
                runs_root=cell_root,
                run_id=f"seed-{seed}",
                n_founders=n_founders,
                n_ticks=n_ticks,
                layout=layout,
                policy_factory=_policy_factory,
                trait_config=cell_cfg,
                condition=cell.id,
            )
            cell_results.append(result)
        aggregates.append(aggregate(cell, cell_results))

    _write_comparison_csv(batch_root / "comparison.csv", baseline_agg, aggregates)
    winner = select_winning_cell(aggregates, baseline_agg)
    _write_winner_text(batch_root / "winner.txt", winner, baseline_agg)

    if write_snapshots_for_winner and winner is not None:
        snapshots_dir = batch_root / "snapshots"
        snapshots_dir.mkdir(exist_ok=True)
        snapshot = _capture_snapshot(
            seed=snapshot_seed,
            n_founders=n_founders,
            layout=layout,
            snapshot_tick=snapshot_tick,
            trait_config=tuned_trait_config(
                fear_max=winner.fear_max,
                hunger_min=winner.hunger_min,
                risk_min=winner.risk_min,
            ),
        )
        (snapshots_dir / f"{winner.cell_id}.txt").write_text(
            f"# winner cell={winner.cell_id} seed={snapshot_seed} tick={snapshot_tick}\n"
            f"{snapshot}\n"
        )

    return aggregates, baseline_agg, winner


def _write_comparison_csv(
    path: Path,
    baseline: GridCellAggregate,
    cells: Sequence[GridCellAggregate],
) -> None:
    fieldnames = [
        "cell_id",
        "fear_max",
        "hunger_min",
        "risk_min",
        "n_seeds",
        "seeds_with_survivors",
        "seeds_with_any_starvation",
        "total_starvation_deaths",
        "total_food_events",
        "total_hazard_entries",
        "total_hazard_damage",
        "total_births",
        "total_moves",
        "total_stays",
        "mean_population_end",
    ]
    with path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in (baseline, *cells):
            data = asdict(row)
            data["mean_population_end"] = round(row.mean_population_end, 4)
            data["total_hazard_damage"] = round(row.total_hazard_damage, 6)
            writer.writerow(data)


def _write_winner_text(
    path: Path,
    winner: GridCellAggregate | None,
    baseline: GridCellAggregate,
) -> None:
    if winner is None:
        path.write_text(
            "no qualifying cell\n\n"
            "All 27 cells failed at least one of the four criteria. Per the\n"
            "pre-registered failure mapping, the next move is v0.6.5: explore\n"
            "distribution shape (Beta sampling) instead of further range\n"
            "tightening.\n"
        )
        return
    path.write_text(
        f"winner: {winner.cell_id}\n"
        f"fear_max={winner.fear_max} hunger_min={winner.hunger_min} risk_min={winner.risk_min}\n"
        f"food_events={winner.total_food_events} (baseline={baseline.total_food_events})\n"
        f"hazard_entries={winner.total_hazard_entries} (baseline={baseline.total_hazard_entries})\n"
        f"seeds_with_survivors={winner.seeds_with_survivors} (>= 1 required)\n"
        f"seeds_with_any_starvation={winner.seeds_with_any_starvation} (>= 1 required)\n"
        f"births={winner.total_births}\n"
    )
