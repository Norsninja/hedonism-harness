"""Fear-Hunger v0.9 memory-arm grid sweep.

The v0.7 + v0.7b sweeps showed reproduction parameters were dormant;
v0.8 showed structural rescue (food_ladder layout) produces a first
reproducing population, but **tight_gradient remains the hard problem**
with only 1 birth in 1 seed. v0.9 asks the next-smallest question:

> Holding reproduction economics, layout, and core valence math
> fixed at v0.7/v0.8 winners, can per-agent valence memory increase
> repeat foraging in tight_gradient enough to produce more births?

The grid is intentionally asymmetric: one ``mem-off`` baseline cell
(``use_memory=False``, the v0.6/v0.7/v0.8 tight_gradient identity) plus
a 3 x 3 memory-on grid sweeping the trait-range bounds.

  - ``mem-off`` baseline: ``use_memory=False`` + v0.6 winner trait
    config + tight_gradient + ``tuned_reproduction_config(et=50,
    ec=35)``. Reproduces the v0.8 ``tight-sr1`` cell exactly.
  - 9 memory cells: same setup but ``use_memory=True`` + per-cell
    ``memory_trait_config(memory_strength_min, memory_decay_rate_max)``.
    Floors / ceilings stay inside SPEC §8.1.

Sweep axes:

  - ``memory_strength_min`` in {0.0, 0.5, 1.0}
  - ``memory_decay_rate_max`` in {0.02, 0.05, 0.1}

10 cells x 8 seeds = 80 runs. The ``mem-off`` cell is the criterion-3
food-floor reference. The "permissive memory" reference cell is
``ms0-md0.1`` (memory-on with SPEC-default range bounds); tie-break
distance is computed against this cell within the memory-on subgrid.

Pre-registered viability rule (cell qualifies iff all six, identical
to v0.7b/v0.8 for narrative consistency):

  1. total_births >= 2
  2. seeds_with_any_births >= 2
  3. total_food_events >= baseline.total_food_events - cell.total_births
  4. seeds_with_any_starvation > 0
  5. max_population_end <= 3 * n_founders
  6. total_reproduction_requests >= total_births

Four diagnostic fields (the v0.9 minimum-viable set) surface the
*behavioral* question without gating qualification:

  - agents_with_memory_updates
  - total_memory_updates
  - repeat_food_visits      <- headline behavioral metric
  - median_food_event_tick

Pre-registered failure -> action mapping:

  - The ``mem-off`` baseline qualifies -> v0.8 result was
    non-deterministic on tight_gradient; investigate before promoting.
  - 0 memory cells qualify -> memory alone is insufficient under this
    geometry. Per the negative-control framing: if memory metrics are
    non-zero but ``repeat_food_visits`` and births do not improve,
    conclude "memory active but not behaviorally effective under this
    chamber".
  - Multiple memory cells qualify -> primary score is ``total_births``
    (highest wins). Tie-break: cell **closest to the SPEC-permissive
    memory cell** ``(ms_min=0.0, md_max=0.1)`` by Euclidean distance in
    (memory_strength_min, memory_decay_rate_max) space.
"""

from __future__ import annotations

import csv
import itertools
import math
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
from hedonism_harness.experiments.memory_telemetry import (
    MemoryTelemetry,
    MemoryTelemetryCollector,
    empty_telemetry,
)
from hedonism_harness.experiments.repro_configs import tuned_reproduction_config
from hedonism_harness.experiments.snapshots import render_model_snapshot
from hedonism_harness.experiments.trait_configs import (
    memory_trait_config,
    tuned_trait_config,
)
from hedonism_harness.model import FounderSpec, HHModel
from hedonism_harness.policies.hedonism_policy import HedonismPolicy

# ---------------------------------------------------------------------------
# Grid definition
# ---------------------------------------------------------------------------

MEMORY_STRENGTH_MIN_LEVELS: tuple[float, ...] = (0.0, 0.5, 1.0)
MEMORY_DECAY_RATE_MAX_LEVELS: tuple[float, ...] = (0.02, 0.05, 0.1)

# The SPEC-permissive memory reference cell — tight_gradient + memory-on
# at SPEC default range bounds (memory_strength floor 0.0, memory_decay_rate
# ceiling 0.1). Tie-break distance is computed against this cell.
PERMISSIVE_MEMORY_STRENGTH_MIN: float = 0.0
PERMISSIVE_MEMORY_DECAY_RATE_MAX: float = 0.1

# Reproduction config FROZEN at v0.7's threshold-positive cell, identical
# to v0.8.
FIXED_ENERGY_THRESHOLD: float = 50.0
FIXED_ENERGY_COST: float = 35.0

# The lone non-memory baseline cell id.
BASELINE_CELL_ID: str = "mem-off"

DEFAULT_N_FOUNDERS: int = 5
OVERPOPULATION_MULTIPLIER: int = 3


def memory_cell_label(*, memory_strength_min: float, memory_decay_rate_max: float) -> str:
    """Filesystem-safe id for a memory-on grid cell.

    Same format as ``trait_configs.memory_cell_id`` but kept locally so the
    grid driver does not depend on cross-module string formatting.
    """
    return f"ms{memory_strength_min:g}-md{memory_decay_rate_max:g}"


@dataclass(frozen=True)
class MemoryCell:
    """One point in the v0.9 grid.

    The single ``mem-off`` cell sets ``use_memory=False`` and uses the v0.6
    winner trait config directly; its ``memory_strength_min`` /
    ``memory_decay_rate_max`` fields are SPEC defaults but ignored at run
    time because the founders have no memory to update. Memory-on cells
    carry the per-cell trait-range bounds.
    """

    use_memory: bool
    memory_strength_min: float
    memory_decay_rate_max: float

    @property
    def id(self) -> str:
        if not self.use_memory:
            return BASELINE_CELL_ID
        return memory_cell_label(
            memory_strength_min=self.memory_strength_min,
            memory_decay_rate_max=self.memory_decay_rate_max,
        )

    def to_layout(self) -> ChamberLayout:
        # All v0.9 cells run on tight_gradient (the hard problem).
        return tight_gradient_layout()

    def to_trait_config(self) -> TraitConfig:
        if not self.use_memory:
            # The v0.6 winner identity (matches v0.8 tight-sr1).
            return tuned_trait_config(fear_max=1.5, hunger_min=1.0, risk_min=0.55)
        return memory_trait_config(
            memory_strength_min=self.memory_strength_min,
            memory_decay_rate_max=self.memory_decay_rate_max,
        )

    def to_reproduction_config(self) -> ReproductionConfig:
        return tuned_reproduction_config(
            energy_threshold=FIXED_ENERGY_THRESHOLD,
            energy_cost=FIXED_ENERGY_COST,
        )


def all_grid_cells() -> list[MemoryCell]:
    """Return the 1 baseline + 9 memory cells in stable order.

    Baseline first (so it appears at the top of comparison.csv), then
    the 9 memory cells in (strength_min, decay_max) lexicographic order.
    """
    cells: list[MemoryCell] = [baseline_cell()]
    for ms_min, md_max in itertools.product(
        MEMORY_STRENGTH_MIN_LEVELS, MEMORY_DECAY_RATE_MAX_LEVELS
    ):
        cells.append(
            MemoryCell(
                use_memory=True,
                memory_strength_min=ms_min,
                memory_decay_rate_max=md_max,
            )
        )
    return cells


def baseline_cell() -> MemoryCell:
    """The non-memory baseline: tight_gradient + use_memory=False."""
    return MemoryCell(
        use_memory=False,
        memory_strength_min=PERMISSIVE_MEMORY_STRENGTH_MIN,
        memory_decay_rate_max=PERMISSIVE_MEMORY_DECAY_RATE_MAX,
    )


# ---------------------------------------------------------------------------
# Aggregates and criterion evaluation
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class MemoryCellAggregate:
    """Per-cell aggregates across the seed sweep — v0.7b set + memory diagnostics."""

    cell_id: str
    use_memory: bool
    memory_strength_min: float
    memory_decay_rate_max: float
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
    # Memory diagnostics
    total_agents_with_memory_updates: int
    total_memory_updates: int
    total_repeat_food_visits: int
    mean_median_food_event_tick: float  # NaN if no seed observed AteFood


def aggregate(
    cell: MemoryCell,
    pairs: Sequence[tuple[ChamberRunResult, MemoryTelemetry]],
) -> MemoryCellAggregate:
    n = len(pairs)
    if n == 0:
        return MemoryCellAggregate(
            cell_id=cell.id,
            use_memory=cell.use_memory,
            memory_strength_min=cell.memory_strength_min,
            memory_decay_rate_max=cell.memory_decay_rate_max,
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
            total_agents_with_memory_updates=0,
            total_memory_updates=0,
            total_repeat_food_visits=0,
            mean_median_food_event_tick=math.nan,
        )
    results = [r for r, _t in pairs]
    telems = [t for _r, t in pairs]
    total_births = sum(r.births for r in results)
    total_requests = sum(r.reproduction_requests for r in results)
    medians = [t.median_food_event_tick for t in telems if not math.isnan(t.median_food_event_tick)]
    mean_median = sum(medians) / len(medians) if medians else math.nan
    return MemoryCellAggregate(
        cell_id=cell.id,
        use_memory=cell.use_memory,
        memory_strength_min=cell.memory_strength_min,
        memory_decay_rate_max=cell.memory_decay_rate_max,
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
        total_agents_with_memory_updates=sum(t.agents_with_memory_updates for t in telems),
        total_memory_updates=sum(t.total_memory_updates for t in telems),
        total_repeat_food_visits=sum(t.repeat_food_visits for t in telems),
        mean_median_food_event_tick=mean_median,
    )


def cell_qualifies(
    cell_agg: MemoryCellAggregate,
    baseline: MemoryCellAggregate,
    *,
    n_founders: int = DEFAULT_N_FOUNDERS,
) -> bool:
    """v0.7b 6-criterion rule, applied unchanged for narrative consistency."""
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


def _distance_to_permissive(cell_agg: MemoryCellAggregate) -> float:
    """Squared Euclidean distance from a memory-on cell to the SPEC-permissive
    memory reference (``ms_min=0.0``, ``md_max=0.1``).

    Defined only for memory-on cells; the ``mem-off`` baseline cell is never
    a tie-break candidate (it is the comparison anchor, not a contestant).
    """
    ms_d = cell_agg.memory_strength_min - PERMISSIVE_MEMORY_STRENGTH_MIN
    md_d = cell_agg.memory_decay_rate_max - PERMISSIVE_MEMORY_DECAY_RATE_MAX
    return float(ms_d * ms_d + md_d * md_d)


def select_winning_cell(
    aggregates: Sequence[MemoryCellAggregate],
    baseline: MemoryCellAggregate,
    *,
    n_founders: int = DEFAULT_N_FOUNDERS,
) -> MemoryCellAggregate | None:
    """Pick the v0.9 winner per pre-registered failure-mapping rules.

    The ``mem-off`` baseline is NOT eligible to win. Memory cells that
    qualify are ranked by ``total_births`` (highest wins); ties broken by
    distance to the SPEC-permissive memory cell.
    """
    candidates = [a for a in aggregates if a.use_memory]
    qualifiers = [a for a in candidates if cell_qualifies(a, baseline, n_founders=n_founders)]
    if not qualifiers:
        return None
    max_births = max(a.total_births for a in qualifiers)
    top_births = [a for a in qualifiers if a.total_births == max_births]
    if len(top_births) == 1:
        return top_births[0]
    return min(top_births, key=_distance_to_permissive)


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
    use_memory: bool,
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
    founders = [
        FounderSpec(
            x=spawn_x,
            y=y,
            policy_factory=_policy_factory,
            use_memory=use_memory,
        )
        for y in spawn_ys
    ]
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


def _run_one_cell_seed(
    *,
    cell: MemoryCell,
    seed: int,
    runs_root: Path,
    n_ticks: int,
    n_founders: int,
) -> tuple[ChamberRunResult, MemoryTelemetry]:
    """Run one (cell, seed) pair with memory-arm telemetry instrumentation.

    Telemetry is wired via ``run_chamber``'s ``setup_observer`` so the
    ``AteFood`` subscriber is live before the first ``model.step()``.
    """
    layout = cell.to_layout()
    trait_cfg = cell.to_trait_config()
    repro_cfg = cell.to_reproduction_config()

    collector_holder: list[MemoryTelemetryCollector | None] = [None]

    def setup(model: HHModel) -> None:
        c = MemoryTelemetryCollector(model)
        c.connect()
        collector_holder[0] = c

    def observe(model: HHModel) -> None:
        # setup() ran before the first step, so the collector is always set.
        assert collector_holder[0] is not None
        collector_holder[0].observe_tick()

    try:
        result = run_chamber(
            seed=seed,
            runs_root=runs_root,
            run_id=f"seed-{seed}",
            n_founders=n_founders,
            n_ticks=n_ticks,
            layout=layout,
            policy_factory=_policy_factory,
            trait_config=trait_cfg,
            reproduction_config=repro_cfg,
            use_memory=cell.use_memory,
            condition=cell.id,
            setup_observer=setup,
            tick_observer=observe,
        )
    finally:
        if collector_holder[0] is not None:
            collector_holder[0].disconnect()

    telemetry = (
        collector_holder[0].finalize() if collector_holder[0] is not None else empty_telemetry()
    )
    return result, telemetry


def run_memory_grid(
    *,
    seeds: Iterable[int],
    runs_root: Path,
    batch_id: str = "fear-hunger-v0.9",
    n_ticks: int = 200,
    n_founders: int = DEFAULT_N_FOUNDERS,
    snapshot_tick: int = 100,
    snapshot_seed: int | None = None,
    cells: Sequence[MemoryCell] | None = None,
    write_snapshots_for_winner: bool = True,
) -> tuple[
    list[MemoryCellAggregate],
    MemoryCellAggregate,
    MemoryCellAggregate | None,
]:
    """Run the v0.9 grid, write artifacts, return (aggs, baseline, winner)."""
    seeds_list = list(seeds)
    if not seeds_list:
        msg = "run_memory_grid requires at least one seed"
        raise ValueError(msg)
    snapshot_seed = snapshot_seed if snapshot_seed is not None else min(seeds_list)
    cells = cells or all_grid_cells()

    batch_root = runs_root / batch_id
    batch_root.mkdir(parents=True, exist_ok=True)

    cells_root = batch_root / "cells"
    cells_root.mkdir(parents=True, exist_ok=True)
    aggregates: list[MemoryCellAggregate] = []
    baseline_id = baseline_cell().id
    baseline_agg: MemoryCellAggregate | None = None

    for cell in cells:
        cell_root = cells_root / cell.id
        cell_root.mkdir(parents=True, exist_ok=True)
        pairs: list[tuple[ChamberRunResult, MemoryTelemetry]] = []
        for seed in seeds_list:
            pair = _run_one_cell_seed(
                cell=cell,
                seed=seed,
                runs_root=cell_root,
                n_ticks=n_ticks,
                n_founders=n_founders,
            )
            pairs.append(pair)
        agg = aggregate(cell, pairs)
        aggregates.append(agg)
        if cell.id == baseline_id:
            baseline_agg = agg

    if baseline_agg is None:
        msg = (
            f"baseline cell {baseline_id!r} not found among grid cells; "
            "v0.9 requires the mem-off baseline cell to be present"
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
            layout=tight_gradient_layout(),
            snapshot_tick=snapshot_tick,
            trait_config=memory_trait_config(
                memory_strength_min=winner.memory_strength_min,
                memory_decay_rate_max=winner.memory_decay_rate_max,
            ),
            reproduction_config=tuned_reproduction_config(
                energy_threshold=FIXED_ENERGY_THRESHOLD,
                energy_cost=FIXED_ENERGY_COST,
            ),
            use_memory=True,
        )
        (snapshots_dir / f"{winner.cell_id}.txt").write_text(
            f"# winner cell={winner.cell_id} seed={snapshot_seed} tick={snapshot_tick}\n"
            f"{snapshot}\n"
        )

    return aggregates, baseline_agg, winner


def _write_comparison_csv(
    path: Path,
    baseline: MemoryCellAggregate,
    cells: Sequence[MemoryCellAggregate],
) -> None:
    fieldnames = [
        "cell_id",
        "use_memory",
        "memory_strength_min",
        "memory_decay_rate_max",
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
        "total_agents_with_memory_updates",
        "total_memory_updates",
        "total_repeat_food_visits",
        "mean_median_food_event_tick",
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
            data["mean_median_food_event_tick"] = (
                round(row.mean_median_food_event_tick, 4)
                if not math.isnan(row.mean_median_food_event_tick)
                else ""
            )
            writer.writerow(data)


def _write_winner_text(
    path: Path,
    winner: MemoryCellAggregate | None,
    baseline: MemoryCellAggregate,
) -> None:
    if winner is None:
        path.write_text(
            "no qualifying cell\n\n"
            "No memory-on cell passed all six v0.7b criteria on tight_gradient.\n"
            "Per the pre-registered failure mapping, memory alone is\n"
            "insufficient to rescue the hard chamber under v0.7's reproduction\n"
            "economics. Negative-control reading: if memory metrics\n"
            "(total_memory_updates, total_repeat_food_visits) are non-zero\n"
            "but births do not improve, conclude 'memory active but not\n"
            "behaviorally effective under tight_gradient geometry'.\n"
        )
        return
    food_floor = baseline.total_food_events - winner.total_births
    path.write_text(
        f"winner: {winner.cell_id}\n"
        f"use_memory={winner.use_memory} "
        f"memory_strength_min={winner.memory_strength_min} "
        f"memory_decay_rate_max={winner.memory_decay_rate_max}\n"
        f"births={winner.total_births} (>= 2 required)\n"
        f"seeds_with_any_births={winner.seeds_with_any_births} (>= 2 required)\n"
        f"food_events={winner.total_food_events} "
        f"(>= baseline - births = {food_floor} required)\n"
        f"seeds_with_any_starvation={winner.seeds_with_any_starvation} (> 0 required)\n"
        f"max_population_end={winner.max_population_end} "
        f"(<= {OVERPOPULATION_MULTIPLIER * DEFAULT_N_FOUNDERS} required)\n"
        f"reproduction_requests={winner.total_reproduction_requests} "
        f"(>= births = {winner.total_births} required)\n"
        f"\n"
        f"-- memory diagnostics --\n"
        f"agents_with_memory_updates={winner.total_agents_with_memory_updates}\n"
        f"total_memory_updates={winner.total_memory_updates}\n"
        f"repeat_food_visits={winner.total_repeat_food_visits}\n"
        f"mean_median_food_event_tick={winner.mean_median_food_event_tick}\n"
        f"\n"
        f"-- baseline (mem-off) reference --\n"
        f"baseline_births={baseline.total_births} "
        f"baseline_food={baseline.total_food_events}\n"
    )
