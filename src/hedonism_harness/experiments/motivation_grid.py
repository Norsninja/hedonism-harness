"""Fear-Hunger v0.7b reproduction-motivation grid sweep.

The v0.7 sweep showed:

  - Lowering ``energy_threshold`` from 70 -> 50 unlocks first-generation
    reproduction (1 birth in 1 seed).
  - ``energy_cost`` is dormant at this birth frequency; the parent
    reproduces at most once.
  - Foraging behavior is preserved across the economics grid.

v0.7b asks: **if threshold is permissive or reachable, does higher
reproductive drive convert eligibility into multiple births across
seeds?**  Holds layout, policy, ``energy_cost`` (SPEC default 35), and
the v0.6 winner trait config fixed; sweeps:

  - ``energy_threshold`` in {50, 60, 70}
  - ``reproduction_drive_min`` in {0.0, 0.5, 1.0}

3 * 3 = 9 cells * 8 seeds = 72 runs. The (et=70, dm=0.0) cell is the
joint SPEC default and acts as the baseline reference for criterion
comparison.

Pre-registered "viable candidate" rule (a cell qualifies iff all six):

  1. total_births >= 2
  2. seeds_with_any_births >= 2
  3. total_food_events >= baseline.total_food_events - cell.total_births
                          (the principled corrected form of v0.7's
                           criterion 2 — absorbs the structural
                           "one reproductive tick displaces one food
                           event" finding from v0.7).
  4. seeds_with_any_starvation > 0
  5. max_population_end <= 3 * n_founders
  6. total_reproduction_requests >= total_births
                          (defense-in-depth invariant — should always
                           hold structurally now that the
                           ReproductionRequested signal flows through
                           the bus, but we re-assert in case of
                           future regressions).

Two new metrics tracked alongside the v0.7 set:

  - ``seeds_with_reproduction_requests`` — distinguishes "one obsessive
    seed requested many times" from "the drive floor generalized
    reproductive intent across seeds." High value means the drive
    knob is functioning at population scale.
  - ``births_per_request`` — total_births / total_reproduction_requests
    (0.0 when no requests). Lower value means the placement layer is
    rejecting many intents (likely capacity=1 + adjacent-empty
    constraint); higher value means most intents are accepted.

Pre-registered failure -> action mapping:

  - 0 cells qualify -> reproduction motivation alone is insufficient;
    layered changes (sensor expansion, layout enlargement) are next.
  - Multiple cells qualify -> primary score is ``total_births``
    (highest wins). Tie-break: cell **closest to SPEC defaults** by
    Euclidean distance in (energy_threshold, drive_min) space.
  - The (70, 0.0) baseline cell qualifies -> SPEC defaults already
    produce robust reproduction (impossible per v0.7 evidence, would
    indicate non-determinism — investigate first).
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
)
from hedonism_harness.experiments.layouts import tight_gradient_layout
from hedonism_harness.experiments.repro_configs import (
    SPEC_ENERGY_COST,
    SPEC_ENERGY_THRESHOLD,
    tuned_reproduction_config,
)
from hedonism_harness.experiments.snapshots import render_model_snapshot
from hedonism_harness.experiments.trait_configs import motivation_trait_config
from hedonism_harness.model import FounderSpec, HHModel
from hedonism_harness.policies.hedonism_policy import HedonismPolicy

# ---------------------------------------------------------------------------
# Grid definition
# ---------------------------------------------------------------------------

ENERGY_THRESHOLD_LEVELS: tuple[float, ...] = (50.0, 60.0, 70.0)
DRIVE_MIN_LEVELS: tuple[float, ...] = (0.0, 0.5, 1.0)

# v0.7b holds energy_cost fixed at SPEC default 35.
ENERGY_COST_FIXED: float = SPEC_ENERGY_COST

# Joint SPEC defaults — re-asserted so a future change raises a visible diff.
SPEC_DRIVE_MIN: float = 0.0

DEFAULT_N_FOUNDERS: int = 5
OVERPOPULATION_MULTIPLIER: int = 3


def motivation_cell_id(*, energy_threshold: float, drive_min: float) -> str:
    """Human-readable filesystem-safe id for a v0.7b grid cell.

    Format: ``et{energy_threshold}-dm{drive_min}``. Examples:
    ``et70-dm0`` is the joint SPEC-default cell (and v0.7b baseline).
    """
    return f"et{energy_threshold:g}-dm{drive_min:g}"


@dataclass(frozen=True)
class MotivationCell:
    """One point in the (energy_threshold, drive_min) grid."""

    energy_threshold: float
    drive_min: float

    @property
    def id(self) -> str:
        return motivation_cell_id(energy_threshold=self.energy_threshold, drive_min=self.drive_min)

    def to_reproduction_config(self) -> ReproductionConfig:
        return tuned_reproduction_config(
            energy_threshold=self.energy_threshold,
            energy_cost=ENERGY_COST_FIXED,
        )

    def to_trait_config(self) -> TraitConfig:
        return motivation_trait_config(drive_min=self.drive_min)


def all_grid_cells() -> list[MotivationCell]:
    """Return the 9 (energy_threshold, drive_min) cells in stable order."""
    return [
        MotivationCell(energy_threshold=et, drive_min=dm)
        for et, dm in itertools.product(ENERGY_THRESHOLD_LEVELS, DRIVE_MIN_LEVELS)
    ]


def baseline_cell() -> MotivationCell:
    """The (et=70, dm=0.0) cell pinning the joint SPEC defaults."""
    return MotivationCell(energy_threshold=SPEC_ENERGY_THRESHOLD, drive_min=SPEC_DRIVE_MIN)


# ---------------------------------------------------------------------------
# Aggregates and criterion evaluation
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class MotivationCellAggregate:
    """Per-cell aggregates across the seed sweep.

    Carries the v0.7 metrics plus the two v0.7b additions
    (``seeds_with_reproduction_requests`` and ``births_per_request``).
    """

    cell_id: str
    energy_threshold: float
    drive_min: float
    n_seeds: int
    seeds_with_survivors: int
    seeds_with_any_starvation: int
    seeds_with_any_births: int
    seeds_with_reproduction_requests: int
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
    births_per_request: float


def aggregate(cell: MotivationCell, results: Sequence[ChamberRunResult]) -> MotivationCellAggregate:
    n = len(results)
    if n == 0:
        return MotivationCellAggregate(
            cell_id=cell.id,
            energy_threshold=cell.energy_threshold,
            drive_min=cell.drive_min,
            n_seeds=0,
            seeds_with_survivors=0,
            seeds_with_any_starvation=0,
            seeds_with_any_births=0,
            seeds_with_reproduction_requests=0,
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
            births_per_request=0.0,
        )
    total_births = sum(r.births for r in results)
    total_requests = sum(r.reproduction_requests for r in results)
    return MotivationCellAggregate(
        cell_id=cell.id,
        energy_threshold=cell.energy_threshold,
        drive_min=cell.drive_min,
        n_seeds=n,
        seeds_with_survivors=sum(1 for r in results if r.population_end > 0),
        seeds_with_any_starvation=sum(1 for r in results if r.starvation_deaths > 0),
        seeds_with_any_births=sum(1 for r in results if r.births > 0),
        seeds_with_reproduction_requests=sum(1 for r in results if r.reproduction_requests > 0),
        total_starvation_deaths=sum(r.starvation_deaths for r in results),
        total_food_events=sum(r.food_events for r in results),
        total_hazard_entries=sum(r.hazard_entries for r in results),
        total_hazard_damage=sum(r.hazard_damage_total for r in results),
        total_births=total_births,
        total_reproduction_requests=total_requests,
        total_moves=sum(r.moves for r in results),
        total_stays=sum(r.stays for r in results),
        mean_population_end=sum(r.population_end for r in results) / n,
        max_population_end=max(r.population_end for r in results),
        births_per_request=(total_births / total_requests) if total_requests else 0.0,
    )


def cell_qualifies(
    cell_agg: MotivationCellAggregate,
    baseline: MotivationCellAggregate,
    *,
    n_founders: int = DEFAULT_N_FOUNDERS,
) -> bool:
    """Apply the six pre-registered v0.7b viability criteria.

    1. total_births >= 2
    2. seeds_with_any_births >= 2
    3. total_food_events >= baseline.total_food_events - cell.total_births
    4. seeds_with_any_starvation > 0
    5. max_population_end <= OVERPOPULATION_MULTIPLIER * n_founders
    6. total_reproduction_requests >= total_births   (invariant)
    """
    overpop_cap = OVERPOPULATION_MULTIPLIER * n_founders
    food_floor = baseline.total_food_events - cell_agg.total_births
    return (
        cell_agg.total_births >= 2
        and cell_agg.seeds_with_any_births >= 2
        and cell_agg.total_food_events >= food_floor
        and cell_agg.seeds_with_any_starvation > 0
        and cell_agg.max_population_end <= overpop_cap
        and cell_agg.total_reproduction_requests >= cell_agg.total_births
    )


def _distance_to_spec_default(cell: MotivationCell) -> float:
    """Squared Euclidean distance to joint SPEC defaults (et=70, dm=0.0)."""
    return (cell.energy_threshold - SPEC_ENERGY_THRESHOLD) ** 2 + (
        cell.drive_min - SPEC_DRIVE_MIN
    ) ** 2


def select_winning_cell(
    aggregates: Sequence[MotivationCellAggregate],
    baseline: MotivationCellAggregate,
    *,
    n_founders: int = DEFAULT_N_FOUNDERS,
) -> MotivationCellAggregate | None:
    """Pick the v0.7b winner per the pre-registered failure-mapping rules."""
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
            MotivationCell(energy_threshold=a.energy_threshold, drive_min=a.drive_min)
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
        reproduction_config=reproduction_config,
        trait_config=trait_config,
    )
    paint_chamber(model, layout)
    for _ in range(snapshot_tick):
        model.step()
    return render_model_snapshot(model)


def run_motivation_grid(
    *,
    seeds: Iterable[int],
    runs_root: Path,
    batch_id: str = "fear-hunger-v0.7b",
    n_ticks: int = 200,
    n_founders: int = DEFAULT_N_FOUNDERS,
    snapshot_tick: int = 100,
    snapshot_seed: int | None = None,
    layout: ChamberLayout | None = None,
    cells: Sequence[MotivationCell] | None = None,
    write_snapshots_for_winner: bool = True,
) -> tuple[
    list[MotivationCellAggregate],
    MotivationCellAggregate,
    MotivationCellAggregate | None,
]:
    """Run the v0.7b 9-cell grid, write artifacts, return (aggs, baseline, winner)."""
    layout = layout or tight_gradient_layout()
    seeds_list = list(seeds)
    if not seeds_list:
        msg = "run_motivation_grid requires at least one seed"
        raise ValueError(msg)
    snapshot_seed = snapshot_seed if snapshot_seed is not None else min(seeds_list)
    cells = cells or all_grid_cells()

    batch_root = runs_root / batch_id
    batch_root.mkdir(parents=True, exist_ok=True)

    cells_root = batch_root / "cells"
    cells_root.mkdir(parents=True, exist_ok=True)
    aggregates: list[MotivationCellAggregate] = []
    baseline_id = baseline_cell().id
    baseline_agg: MotivationCellAggregate | None = None

    for cell in cells:
        cell_root = cells_root / cell.id
        cell_root.mkdir(parents=True, exist_ok=True)
        cell_results: list[ChamberRunResult] = []
        cell_repro = cell.to_reproduction_config()
        cell_traits = cell.to_trait_config()
        for seed in seeds_list:
            result = run_chamber(
                seed=seed,
                runs_root=cell_root,
                run_id=f"seed-{seed}",
                n_founders=n_founders,
                n_ticks=n_ticks,
                layout=layout,
                policy_factory=_policy_factory,
                trait_config=cell_traits,
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
            "v0.7b requires the joint SPEC-default cell to act as the baseline"
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
            trait_config=motivation_trait_config(drive_min=winner.drive_min),
            reproduction_config=tuned_reproduction_config(
                energy_threshold=winner.energy_threshold,
                energy_cost=ENERGY_COST_FIXED,
            ),
        )
        (snapshots_dir / f"{winner.cell_id}.txt").write_text(
            f"# winner cell={winner.cell_id} seed={snapshot_seed} tick={snapshot_tick}\n"
            f"{snapshot}\n"
        )

    return aggregates, baseline_agg, winner


def _write_comparison_csv(
    path: Path,
    baseline: MotivationCellAggregate,
    cells: Sequence[MotivationCellAggregate],
) -> None:
    fieldnames = [
        "cell_id",
        "energy_threshold",
        "drive_min",
        "n_seeds",
        "seeds_with_survivors",
        "seeds_with_any_starvation",
        "seeds_with_any_births",
        "seeds_with_reproduction_requests",
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
        "births_per_request",
    ]
    others = [c for c in cells if c.cell_id != baseline.cell_id]
    with path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in (baseline, *others):
            data = asdict(row)
            data["mean_population_end"] = round(row.mean_population_end, 4)
            data["total_hazard_damage"] = round(row.total_hazard_damage, 6)
            data["births_per_request"] = round(row.births_per_request, 6)
            writer.writerow(data)


def _write_winner_text(
    path: Path,
    winner: MotivationCellAggregate | None,
    baseline: MotivationCellAggregate,
) -> None:
    if winner is None:
        path.write_text(
            "no qualifying cell\n\n"
            "All 9 cells failed at least one of the six criteria. Per the\n"
            "pre-registered failure mapping, reproduction motivation alone\n"
            "is insufficient — layered changes (sensor expansion, layout\n"
            "enlargement) are next.\n"
        )
        return
    food_floor = baseline.total_food_events - winner.total_births
    path.write_text(
        f"winner: {winner.cell_id}\n"
        f"energy_threshold={winner.energy_threshold} drive_min={winner.drive_min}\n"
        f"births={winner.total_births} (>= 2 required)\n"
        f"seeds_with_any_births={winner.seeds_with_any_births} (>= 2 required)\n"
        f"food_events={winner.total_food_events} "
        f"(>= baseline - births = {food_floor} required)\n"
        f"seeds_with_any_starvation={winner.seeds_with_any_starvation} (> 0 required)\n"
        f"max_population_end={winner.max_population_end} "
        f"(<= {OVERPOPULATION_MULTIPLIER * DEFAULT_N_FOUNDERS} required)\n"
        f"reproduction_requests={winner.total_reproduction_requests} "
        f"(>= births = {winner.total_births} required)\n"
        f"seeds_with_reproduction_requests={winner.seeds_with_reproduction_requests}\n"
        f"births_per_request={winner.births_per_request:.4f}\n"
    )
