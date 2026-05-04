"""Fear-Hunger v0.7 reproduction-config grid sweep.

The v0.6 trait-grid sweep validated the permissive trait zone but every
cell scored zero births. The v0.7 hypothesis: reproduction does not
emerge because ``energy_threshold=70`` sits above ``starting_energy=60``
and ``energy_cost=35`` punishes successful parents. Lowering threshold
and/or cost should unlock first-generation births without collapsing
the v0.6 foraging behavior.

Holds layout (``tight_gradient``), policy
(``HedonismPolicy(exploration_noise=0.05)``), and trait config
(``tuned_trait_config(fear_max=1.5, hunger_min=1.0, risk_min=0.55)`` —
the v0.6 winner) constant. Varies only:

  - ``energy_threshold`` in {50, 60, 70}
  - ``energy_cost``      in {15, 25, 35}

3 * 3 = 9 cells * 8 seeds = 72 runs. The (70, 35) cell is the SPEC
default and serves as the baseline reference for criterion comparison.

Pre-registered "viable candidate" rule (a cell qualifies iff all four):

  1. total_births >= 1   (the headline test).
  2. total_food_events >= baseline.total_food_events
                         (foraging preserved; trait config is fixed
                          so any drop indicates the cheaper repro
                          drained behavior).
  3. seeds_with_any_starvation > 0
                         (diversity guard; not every seed becomes
                          a runaway lineage).
  4. max_population_end <= 3 * n_founders
                         (overpopulation guard; with n_founders=5
                          this is max_pop_end <= 15 across the seed
                          sweep — one explosive seed disqualifies).

Pre-registered failure -> action mapping:

  - 0 cells qualify -> economics alone is insufficient. v0.7b
    explores raising the ``reproduction_drive`` floor (the only
    trait-range knob we deliberately deferred).
  - Multiple cells qualify -> primary score is ``total_births``
    (highest wins). Tie-break: cell **closest to SPEC defaults** by
    Euclidean distance in (energy_threshold, energy_cost) space.
    Conservative-tightening rule.
  - The (70, 35) baseline cell qualifies -> SPEC defaults already
    work and the v0.6 zero-births was layout/throughput, not
    economics; investigate before promoting any cell.
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
from hedonism_harness.experiments.repro_configs import (
    SPEC_ENERGY_COST,
    SPEC_ENERGY_THRESHOLD,
    repro_cell_id,
    tuned_reproduction_config,
)
from hedonism_harness.experiments.snapshots import render_model_snapshot
from hedonism_harness.experiments.trait_configs import tuned_trait_config
from hedonism_harness.model import FounderSpec, HHModel
from hedonism_harness.policies.hedonism_policy import HedonismPolicy

# ---------------------------------------------------------------------------
# Grid definition
# ---------------------------------------------------------------------------

ENERGY_THRESHOLD_LEVELS: tuple[float, ...] = (50.0, 60.0, 70.0)
ENERGY_COST_LEVELS: tuple[float, ...] = (15.0, 25.0, 35.0)

# v0.7 holds the trait config fixed at the v0.6 winner.
V06_WINNER_TRAIT_CONFIG: TraitConfig = tuned_trait_config(
    fear_max=1.5, hunger_min=1.0, risk_min=0.55
)

# Overpopulation guard threshold = 3 * n_founders. Hard-coded for n_founders=5
# so the criterion is unambiguous in the report.
DEFAULT_N_FOUNDERS: int = 5
OVERPOPULATION_MULTIPLIER: int = 3


@dataclass(frozen=True)
class GridCell:
    """One point in the (energy_threshold, energy_cost) grid."""

    energy_threshold: float
    energy_cost: float

    @property
    def id(self) -> str:
        return repro_cell_id(
            energy_threshold=self.energy_threshold,
            energy_cost=self.energy_cost,
        )

    def to_reproduction_config(self) -> ReproductionConfig:
        return tuned_reproduction_config(
            energy_threshold=self.energy_threshold,
            energy_cost=self.energy_cost,
        )


def all_grid_cells() -> list[GridCell]:
    """Return the 9 (energy_threshold, energy_cost) cells in stable order."""
    return [
        GridCell(energy_threshold=et, energy_cost=ec)
        for et, ec in itertools.product(ENERGY_THRESHOLD_LEVELS, ENERGY_COST_LEVELS)
    ]


def baseline_cell() -> GridCell:
    """The (et=70, ec=35) cell that pins the SPEC default ReproductionConfig.

    Acts as the reference point for criterion 2 (food preservation) and
    the SPEC-distance tie-break.
    """
    return GridCell(energy_threshold=SPEC_ENERGY_THRESHOLD, energy_cost=SPEC_ENERGY_COST)


# ---------------------------------------------------------------------------
# Aggregates and criterion evaluation
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class GridCellAggregate:
    """Per-cell aggregates across the seed sweep."""

    cell_id: str
    energy_threshold: float
    energy_cost: float
    n_seeds: int
    seeds_with_survivors: int
    seeds_with_any_starvation: int
    seeds_with_any_births: int
    total_starvation_deaths: int
    total_food_events: int
    total_hazard_entries: int
    total_hazard_damage: float
    total_births: int
    total_reproduction_requests: int
    total_moves: int
    total_stays: int
    mean_population_end: float
    max_population_end: int


def aggregate(cell: GridCell, results: Sequence[ChamberRunResult]) -> GridCellAggregate:
    n = len(results)
    if n == 0:
        return GridCellAggregate(
            cell_id=cell.id,
            energy_threshold=cell.energy_threshold,
            energy_cost=cell.energy_cost,
            n_seeds=0,
            seeds_with_survivors=0,
            seeds_with_any_starvation=0,
            seeds_with_any_births=0,
            total_starvation_deaths=0,
            total_food_events=0,
            total_hazard_entries=0,
            total_hazard_damage=0.0,
            total_births=0,
            total_reproduction_requests=0,
            total_moves=0,
            total_stays=0,
            mean_population_end=0.0,
            max_population_end=0,
        )
    return GridCellAggregate(
        cell_id=cell.id,
        energy_threshold=cell.energy_threshold,
        energy_cost=cell.energy_cost,
        n_seeds=n,
        seeds_with_survivors=sum(1 for r in results if r.population_end > 0),
        seeds_with_any_starvation=sum(1 for r in results if r.starvation_deaths > 0),
        seeds_with_any_births=sum(1 for r in results if r.births > 0),
        total_starvation_deaths=sum(r.starvation_deaths for r in results),
        total_food_events=sum(r.food_events for r in results),
        total_hazard_entries=sum(r.hazard_entries for r in results),
        total_hazard_damage=sum(r.hazard_damage_total for r in results),
        total_births=sum(r.births for r in results),
        total_reproduction_requests=sum(r.reproduction_requests for r in results),
        total_moves=sum(r.moves for r in results),
        total_stays=sum(r.stays for r in results),
        mean_population_end=sum(r.population_end for r in results) / n,
        max_population_end=max(r.population_end for r in results),
    )


def cell_qualifies(
    cell_agg: GridCellAggregate,
    baseline: GridCellAggregate,
    *,
    n_founders: int = DEFAULT_N_FOUNDERS,
) -> bool:
    """Apply the four pre-registered v0.7 viability criteria to one cell.

    1. total_births >= 1
    2. total_food_events >= baseline.total_food_events
    3. seeds_with_any_starvation > 0
    4. max_population_end <= OVERPOPULATION_MULTIPLIER * n_founders
    """
    overpop_cap = OVERPOPULATION_MULTIPLIER * n_founders
    return (
        cell_agg.total_births >= 1
        and cell_agg.total_food_events >= baseline.total_food_events
        and cell_agg.seeds_with_any_starvation > 0
        and cell_agg.max_population_end <= overpop_cap
    )


def _distance_to_spec_default(cell: GridCell) -> float:
    """Squared Euclidean distance from this cell to SPEC defaults.

    SPEC defaults: energy_threshold=70, energy_cost=35. Smaller distance
    = closer to SPEC = more conservative tightening. Used to break ties
    among multiple qualifying cells.
    """
    return (cell.energy_threshold - SPEC_ENERGY_THRESHOLD) ** 2 + (
        cell.energy_cost - SPEC_ENERGY_COST
    ) ** 2


def select_winning_cell(
    aggregates: Sequence[GridCellAggregate],
    baseline: GridCellAggregate,
    *,
    n_founders: int = DEFAULT_N_FOUNDERS,
) -> GridCellAggregate | None:
    """Pick the v0.7 winner per the pre-registered failure-mapping rules.

    Returns None if no cell qualifies. When multiple cells qualify, the
    primary score is ``total_births`` (highest wins). The tie-break is
    "closest to SPEC defaults" (least permissive).
    """
    qualifiers = [a for a in aggregates if cell_qualifies(a, baseline, n_founders=n_founders)]
    if not qualifiers:
        return None

    max_births = max(a.total_births for a in qualifiers)
    top_births = [a for a in qualifiers if a.total_births == max_births]
    if len(top_births) == 1:
        return top_births[0]

    return min(
        top_births,
        key=lambda a: _distance_to_spec_default(
            GridCell(energy_threshold=a.energy_threshold, energy_cost=a.energy_cost)
        ),
    )


# ---------------------------------------------------------------------------
# Driver
# ---------------------------------------------------------------------------


def _policy_factory() -> HedonismPolicy:
    return HedonismPolicy(exploration_noise=0.05)


def _capture_snapshot(
    *,
    seed: int,
    n_founders: int,
    layout: ChamberLayout,
    snapshot_tick: int,
    trait_config: TraitConfig,
    reproduction_config: ReproductionConfig,
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
        reproduction_config=reproduction_config,
        trait_config=trait_config,
    )
    paint_chamber(model, layout)
    for _ in range(snapshot_tick):
        model.step()
    return render_model_snapshot(model)


def run_repro_grid(
    *,
    seeds: Iterable[int],
    runs_root: Path,
    batch_id: str = "fear-hunger-v0.7",
    n_ticks: int = 200,
    n_founders: int = DEFAULT_N_FOUNDERS,
    snapshot_tick: int = 100,
    snapshot_seed: int | None = None,
    layout: ChamberLayout | None = None,
    cells: Sequence[GridCell] | None = None,
    trait_config: TraitConfig | None = None,
    write_snapshots_for_winner: bool = True,
) -> tuple[list[GridCellAggregate], GridCellAggregate, GridCellAggregate | None]:
    """Run the v0.7 9-cell grid, write artifacts, return (aggs, baseline, winner).

    Output layout::

        runs_root/batch_id/
            cells/{cell_id}/seed-{N}/...
            comparison.csv          # 9 cell rows
            winner.txt              # the chosen cell + criterion details
            snapshots/              # winner snapshot at snapshot_tick

    The (et=70, ec=35) cell IS the SPEC-default baseline — no separate
    baseline tree is needed because the trait config is held fixed at
    the v0.6 winner across the entire sweep.
    """
    layout = layout or tight_gradient_layout()
    seeds_list = list(seeds)
    if not seeds_list:
        msg = "run_repro_grid requires at least one seed"
        raise ValueError(msg)
    snapshot_seed = snapshot_seed if snapshot_seed is not None else min(seeds_list)
    cells = cells or all_grid_cells()
    trait_cfg = trait_config if trait_config is not None else V06_WINNER_TRAIT_CONFIG

    batch_root = runs_root / batch_id
    batch_root.mkdir(parents=True, exist_ok=True)

    cells_root = batch_root / "cells"
    cells_root.mkdir(parents=True, exist_ok=True)
    aggregates: list[GridCellAggregate] = []
    baseline_id = baseline_cell().id
    baseline_agg: GridCellAggregate | None = None

    for cell in cells:
        cell_root = cells_root / cell.id
        cell_root.mkdir(parents=True, exist_ok=True)
        cell_results: list[ChamberRunResult] = []
        cell_repro = cell.to_reproduction_config()
        for seed in seeds_list:
            result = run_chamber(
                seed=seed,
                runs_root=cell_root,
                run_id=f"seed-{seed}",
                n_founders=n_founders,
                n_ticks=n_ticks,
                layout=layout,
                policy_factory=_policy_factory,
                trait_config=trait_cfg,
                reproduction_config=cell_repro,
                condition=cell.id,
            )
            cell_results.append(result)
        agg = aggregate(cell, cell_results)
        aggregates.append(agg)
        if cell.id == baseline_id:
            baseline_agg = agg

    if baseline_agg is None:
        msg = (
            f"baseline cell {baseline_id!r} not found among grid cells; "
            "v0.7 requires the SPEC-default cell to act as the baseline"
        )
        raise RuntimeError(msg)

    _write_comparison_csv(batch_root / "comparison.csv", baseline_agg, aggregates)
    winner = select_winning_cell(aggregates, baseline_agg, n_founders=n_founders)
    _write_winner_text(batch_root / "winner.txt", winner, baseline_agg)

    if write_snapshots_for_winner and winner is not None:
        snapshots_dir = batch_root / "snapshots"
        snapshots_dir.mkdir(exist_ok=True)
        snapshot = _capture_snapshot(
            seed=snapshot_seed,
            n_founders=n_founders,
            layout=layout,
            snapshot_tick=snapshot_tick,
            trait_config=trait_cfg,
            reproduction_config=tuned_reproduction_config(
                energy_threshold=winner.energy_threshold,
                energy_cost=winner.energy_cost,
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
        "energy_threshold",
        "energy_cost",
        "n_seeds",
        "seeds_with_survivors",
        "seeds_with_any_starvation",
        "seeds_with_any_births",
        "total_starvation_deaths",
        "total_food_events",
        "total_hazard_entries",
        "total_hazard_damage",
        "total_births",
        "total_reproduction_requests",
        "total_moves",
        "total_stays",
        "mean_population_end",
        "max_population_end",
    ]
    # Baseline first, then the rest (skipping baseline if it appears in cells
    # to avoid duplicate rows when baseline is also one of the grid cells).
    others = [c for c in cells if c.cell_id != baseline.cell_id]
    with path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in (baseline, *others):
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
            "All 9 cells failed at least one of the four criteria. Per the\n"
            "pre-registered failure mapping, the next move is v0.7b: raise\n"
            "the reproduction_drive floor (the trait-range knob deliberately\n"
            "deferred from v0.7). Reproduction did not emerge from energy\n"
            "economics alone.\n"
        )
        return
    path.write_text(
        f"winner: {winner.cell_id}\n"
        f"energy_threshold={winner.energy_threshold} energy_cost={winner.energy_cost}\n"
        f"births={winner.total_births} (>= 1 required)\n"
        f"food_events={winner.total_food_events} (baseline={baseline.total_food_events})\n"
        f"seeds_with_any_starvation={winner.seeds_with_any_starvation} (> 0 required)\n"
        f"max_population_end={winner.max_population_end} "
        f"(<= {OVERPOPULATION_MULTIPLIER * DEFAULT_N_FOUNDERS} required)\n"
        f"reproduction_requests={winner.total_reproduction_requests}\n"
    )
