"""Fear-Hunger v0.8 structural eligibility-rescue grid sweep.

The v0.7 + v0.7b sweeps showed both ``energy_cost`` and
``reproduction_drive_min`` are dormant at the current throughput: the
single-survivor seed reaches reproductive eligibility once and dies.
The v0.8 question is upstream:

> Can structural perception/space changes (wider sensors, more
> forgiving layouts) increase the *supply* of eligibility-ticks
> enough that reproduction becomes a recurring possibility across
> seeds?

Holds policy, fixed reproduction config (et=50, ec=35, drive_min=0.0),
and the v0.6 winner trait base; sweeps:

  - ``layout`` in {tight_gradient, widened_gradient, food_ladder}
  - ``sensor_radius_min`` in {1, 2, 3}

3 * 3 = 9 cells * 8 seeds = 72 runs. The (tight_gradient, sr_min=1)
cell is the v0.7-winner identity and acts as the baseline reference.

Reproduction parameters are FIXED (per v0.7b decision): ``et=50``
(the only threshold that produced any birth in v0.7), ``ec=35`` (SPEC
default, dormant in v0.7), ``drive_min=0.0`` (SPEC default, dormant
in v0.7b). ``BodyConfig.sensor_radius_metabolic_cost`` stays at the
SPEC default 0.05 — raising the sensor floor *also* raises per-tick
metabolism, and the new telemetry surfaces whether the wider-sensor
metabolic cost shortens lifespans.

Pre-registered viability rule (cell qualifies iff all six, identical
to v0.7b for narrative consistency):

  1. total_births >= 2
  2. seeds_with_any_births >= 2
  3. total_food_events >= baseline.total_food_events - cell.total_births
  4. seeds_with_any_starvation > 0
  5. max_population_end <= 3 * n_founders
  6. total_reproduction_requests >= total_births

Seven new diagnostic fields surface the *why* of pass/fail without
gating qualification (per the v0.8 design — eligibility is the
question, criteria 1-6 are the downstream consequence):

  - eligible_agent_ticks
  - seeds_with_reproduction_eligibility
  - first_eligibility_tick
  - max_energy_after_min_age
  - food_events_after_min_age
  - deaths_before_min_age
  - median_death_age

Pre-registered failure -> action mapping:

  - 0 cells qualify -> structural changes alone are insufficient.
    The next move is v0.9 memory arm (``MemoryHedonismPolicy``):
    if perception cannot manufacture eligibility, recall might.
  - Multiple cells qualify -> primary score is ``total_births``
    (highest wins). Tie-break: cell **closest to baseline** by
    Euclidean distance in (layout-axis, sensor_radius_min) space,
    with layout encoded as the ordinal {tight_gradient: 0,
    widened_gradient: 1, food_ladder: 2}.
  - The (tight_gradient, sr_min=1) baseline cell qualifies -> v0.7b
    was non-deterministic; investigate before promoting any cell.
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
from hedonism_harness.experiments.eligibility_telemetry import (
    EligibilityTelemetry,
    EligibilityTelemetryCollector,
    empty_telemetry,
)
from hedonism_harness.experiments.fear_hunger_chamber import (
    ChamberLayout,
    ChamberRunResult,
    paint_chamber,
    run_chamber,
)
from hedonism_harness.experiments.layouts import (
    food_ladder_layout,
    tight_gradient_layout,
    widened_gradient_layout,
)
from hedonism_harness.experiments.repro_configs import tuned_reproduction_config
from hedonism_harness.experiments.snapshots import render_model_snapshot
from hedonism_harness.experiments.trait_configs import eligibility_trait_config
from hedonism_harness.model import FounderSpec, HHModel
from hedonism_harness.policies.hedonism_policy import HedonismPolicy

# ---------------------------------------------------------------------------
# Grid definition
# ---------------------------------------------------------------------------

# Layout axis — ordered so the baseline (tight_gradient) is index 0 and
# the SPEC-distance tie-break uses ordinal distance among layouts.
LAYOUT_NAMES: tuple[str, ...] = ("tight_gradient", "widened_gradient", "food_ladder")
SENSOR_RADIUS_MIN_LEVELS: tuple[int, ...] = (1, 2, 3)

# Reproduction config FROZEN at v0.7's threshold-positive cell — the only
# permissive cell that produced any birth in the v0.7 sweep.
FIXED_ENERGY_THRESHOLD: float = 50.0
FIXED_ENERGY_COST: float = 35.0
FIXED_DRIVE_MIN: float = 0.0  # SPEC default; v0.7b confirmed dormant.

# Baseline cell axis-values.
BASELINE_LAYOUT_NAME: str = "tight_gradient"
BASELINE_SENSOR_RADIUS_MIN: int = 1

DEFAULT_N_FOUNDERS: int = 5
OVERPOPULATION_MULTIPLIER: int = 3


def eligibility_cell_id(*, layout_name: str, sensor_radius_min: int) -> str:
    """Filesystem-safe id for a v0.8 grid cell.

    Format: ``{layout_short}-sr{sensor_radius_min}``. The layout short
    forms (``tight``, ``widened``, ``ladder``) keep filenames brief.
    """
    short = {
        "tight_gradient": "tight",
        "widened_gradient": "widened",
        "food_ladder": "ladder",
    }[layout_name]
    return f"{short}-sr{sensor_radius_min}"


def _layout_factory(name: str) -> ChamberLayout:
    if name == "tight_gradient":
        return tight_gradient_layout()
    if name == "widened_gradient":
        return widened_gradient_layout()
    if name == "food_ladder":
        return food_ladder_layout()
    msg = f"Unknown layout {name!r}; valid: {LAYOUT_NAMES}"
    raise ValueError(msg)


def _layout_ordinal(name: str) -> int:
    return LAYOUT_NAMES.index(name)


@dataclass(frozen=True)
class EligibilityCell:
    """One point in the (layout, sensor_radius_min) grid."""

    layout_name: str
    sensor_radius_min: int

    @property
    def id(self) -> str:
        return eligibility_cell_id(
            layout_name=self.layout_name, sensor_radius_min=self.sensor_radius_min
        )

    def to_layout(self) -> ChamberLayout:
        return _layout_factory(self.layout_name)

    def to_trait_config(self) -> TraitConfig:
        return eligibility_trait_config(sensor_radius_min=self.sensor_radius_min)

    def to_reproduction_config(self) -> ReproductionConfig:
        return tuned_reproduction_config(
            energy_threshold=FIXED_ENERGY_THRESHOLD,
            energy_cost=FIXED_ENERGY_COST,
        )


def all_grid_cells() -> list[EligibilityCell]:
    """Return the 9 (layout, sensor_radius_min) cells in stable order."""
    return [
        EligibilityCell(layout_name=name, sensor_radius_min=sr_min)
        for name, sr_min in itertools.product(LAYOUT_NAMES, SENSOR_RADIUS_MIN_LEVELS)
    ]


def baseline_cell() -> EligibilityCell:
    """The baseline cell: tight_gradient layout + sensor_radius_min=1."""
    return EligibilityCell(
        layout_name=BASELINE_LAYOUT_NAME,
        sensor_radius_min=BASELINE_SENSOR_RADIUS_MIN,
    )


# ---------------------------------------------------------------------------
# Aggregates and criterion evaluation
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class EligibilityCellAggregate:
    """Per-cell aggregates across the seed sweep — v0.7b set + telemetry."""

    cell_id: str
    layout_name: str
    sensor_radius_min: int
    n_seeds: int
    seeds_with_survivors: int
    seeds_with_any_starvation: int
    seeds_with_any_births: int
    seeds_with_reproduction_requests: int
    seeds_with_reproduction_eligibility: int
    total_starvation_deaths: int
    total_food_events: int
    total_hazard_entries: int
    total_hazard_damage: float
    total_births: int
    total_reproduction_requests: int
    total_eligible_agent_ticks: int
    total_food_events_after_min_age: int
    total_deaths_before_min_age: int
    total_moves: int
    total_stays: int
    mean_population_end: float
    max_population_end: int
    births_per_request: float
    mean_first_eligibility_tick: float  # NaN when no eligibility ever observed
    max_energy_after_min_age: float
    median_death_age: float  # mean across seeds; NaN if no seed had deaths


def _mean(values: Sequence[float]) -> float:
    finite = [v for v in values if not math.isnan(v)]
    if not finite:
        return math.nan
    return sum(finite) / len(finite)


def aggregate(
    cell: EligibilityCell,
    pairs: Sequence[tuple[ChamberRunResult, EligibilityTelemetry]],
) -> EligibilityCellAggregate:
    n = len(pairs)
    if n == 0:
        return EligibilityCellAggregate(
            cell_id=cell.id,
            layout_name=cell.layout_name,
            sensor_radius_min=cell.sensor_radius_min,
            n_seeds=0,
            seeds_with_survivors=0,
            seeds_with_any_starvation=0,
            seeds_with_any_births=0,
            seeds_with_reproduction_requests=0,
            seeds_with_reproduction_eligibility=0,
            total_starvation_deaths=0,
            total_food_events=0,
            total_hazard_entries=0,
            total_hazard_damage=0.0,
            total_births=0,
            total_reproduction_requests=0,
            total_eligible_agent_ticks=0,
            total_food_events_after_min_age=0,
            total_deaths_before_min_age=0,
            total_moves=0,
            total_stays=0,
            mean_population_end=0.0,
            max_population_end=0,
            births_per_request=0.0,
            mean_first_eligibility_tick=math.nan,
            max_energy_after_min_age=0.0,
            median_death_age=math.nan,
        )
    results = [r for r, _t in pairs]
    telems = [t for _r, t in pairs]
    total_births = sum(r.births for r in results)
    total_requests = sum(r.reproduction_requests for r in results)
    return EligibilityCellAggregate(
        cell_id=cell.id,
        layout_name=cell.layout_name,
        sensor_radius_min=cell.sensor_radius_min,
        n_seeds=n,
        seeds_with_survivors=sum(1 for r in results if r.population_end > 0),
        seeds_with_any_starvation=sum(1 for r in results if r.starvation_deaths > 0),
        seeds_with_any_births=sum(1 for r in results if r.births > 0),
        seeds_with_reproduction_requests=sum(1 for r in results if r.reproduction_requests > 0),
        seeds_with_reproduction_eligibility=sum(1 for t in telems if t.had_any_eligibility),
        total_starvation_deaths=sum(r.starvation_deaths for r in results),
        total_food_events=sum(r.food_events for r in results),
        total_hazard_entries=sum(r.hazard_entries for r in results),
        total_hazard_damage=sum(r.hazard_damage_total for r in results),
        total_births=total_births,
        total_reproduction_requests=total_requests,
        total_eligible_agent_ticks=sum(t.eligible_agent_ticks for t in telems),
        total_food_events_after_min_age=sum(t.food_events_after_min_age for t in telems),
        total_deaths_before_min_age=sum(t.deaths_before_min_age for t in telems),
        total_moves=sum(r.moves for r in results),
        total_stays=sum(r.stays for r in results),
        mean_population_end=sum(r.population_end for r in results) / n,
        max_population_end=max(r.population_end for r in results),
        births_per_request=(total_births / total_requests) if total_requests else 0.0,
        mean_first_eligibility_tick=_mean(
            [
                float(t.first_eligibility_tick)
                for t in telems
                if t.first_eligibility_tick is not None
            ]
        ),
        max_energy_after_min_age=max((t.max_energy_after_min_age for t in telems), default=0.0),
        median_death_age=_mean([t.median_death_age for t in telems]),
    )


def cell_qualifies(
    cell_agg: EligibilityCellAggregate,
    baseline: EligibilityCellAggregate,
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


def _distance_to_baseline(cell: EligibilityCell) -> float:
    """Euclidean distance to baseline (tight_gradient, sr_min=1) in
    (layout_ordinal, sensor_radius_min) space."""
    layout_d = _layout_ordinal(cell.layout_name) - _layout_ordinal(BASELINE_LAYOUT_NAME)
    sr_d = cell.sensor_radius_min - BASELINE_SENSOR_RADIUS_MIN
    return float(layout_d * layout_d + sr_d * sr_d)


def select_winning_cell(
    aggregates: Sequence[EligibilityCellAggregate],
    baseline: EligibilityCellAggregate,
    *,
    n_founders: int = DEFAULT_N_FOUNDERS,
) -> EligibilityCellAggregate | None:
    """Pick the v0.8 winner per the pre-registered failure-mapping rules."""
    qualifiers = [a for a in aggregates if cell_qualifies(a, baseline, n_founders=n_founders)]
    if not qualifiers:
        return None
    max_births = max(a.total_births for a in qualifiers)
    top_births = [a for a in qualifiers if a.total_births == max_births]
    if len(top_births) == 1:
        return top_births[0]
    return min(
        top_births,
        key=lambda a: _distance_to_baseline(
            EligibilityCell(layout_name=a.layout_name, sensor_radius_min=a.sensor_radius_min)
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


def _run_one_cell_seed(
    *,
    cell: EligibilityCell,
    seed: int,
    runs_root: Path,
    n_ticks: int,
    n_founders: int,
) -> tuple[ChamberRunResult, EligibilityTelemetry]:
    """Run one (cell, seed) pair with telemetry instrumentation."""
    layout = cell.to_layout()
    trait_cfg = cell.to_trait_config()
    repro_cfg = cell.to_reproduction_config()

    # We need a handle to the model for the telemetry collector. Construct
    # the collector lazily via a closure — the first observer call sees the
    # model and instantiates + connects the collector.
    collector_holder: list[EligibilityTelemetryCollector | None] = [None]

    def observer(model: HHModel) -> None:
        if collector_holder[0] is None:
            c = EligibilityTelemetryCollector(model, repro_cfg)
            c.connect()
            collector_holder[0] = c
        # mypy: collector_holder[0] is non-None after the branch above
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
            condition=cell.id,
            tick_observer=observer,
        )
    finally:
        if collector_holder[0] is not None:
            collector_holder[0].disconnect()

    telemetry = (
        collector_holder[0].finalize() if collector_holder[0] is not None else empty_telemetry()
    )
    return result, telemetry


def run_eligibility_grid(
    *,
    seeds: Iterable[int],
    runs_root: Path,
    batch_id: str = "fear-hunger-v0.8",
    n_ticks: int = 200,
    n_founders: int = DEFAULT_N_FOUNDERS,
    snapshot_tick: int = 100,
    snapshot_seed: int | None = None,
    cells: Sequence[EligibilityCell] | None = None,
    write_snapshots_for_winner: bool = True,
) -> tuple[
    list[EligibilityCellAggregate],
    EligibilityCellAggregate,
    EligibilityCellAggregate | None,
]:
    """Run the v0.8 9-cell grid, write artifacts, return (aggs, baseline, winner)."""
    seeds_list = list(seeds)
    if not seeds_list:
        msg = "run_eligibility_grid requires at least one seed"
        raise ValueError(msg)
    snapshot_seed = snapshot_seed if snapshot_seed is not None else min(seeds_list)
    cells = cells or all_grid_cells()

    batch_root = runs_root / batch_id
    batch_root.mkdir(parents=True, exist_ok=True)

    cells_root = batch_root / "cells"
    cells_root.mkdir(parents=True, exist_ok=True)
    aggregates: list[EligibilityCellAggregate] = []
    baseline_id = baseline_cell().id
    baseline_agg: EligibilityCellAggregate | None = None

    for cell in cells:
        cell_root = cells_root / cell.id
        cell_root.mkdir(parents=True, exist_ok=True)
        pairs: list[tuple[ChamberRunResult, EligibilityTelemetry]] = []
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
            "v0.8 requires the (tight_gradient, sr_min=1) cell to be present"
        )
        raise RuntimeError(msg)

    _write_comparison_csv(batch_root / "comparison.csv", baseline_agg, aggregates)
    winner = select_winning_cell(aggregates, baseline_agg, n_founders=n_founders)
    _write_winner_text(batch_root / "winner.txt", winner, baseline_agg)

    if write_snapshots_for_winner and winner is not None:
        snapshots_dir = batch_root / "snapshots"
        snapshots_dir.mkdir(exist_ok=True)
        winner_layout = _layout_factory(winner.layout_name)
        snapshot = _capture_snapshot(
            seed=snapshot_seed,
            n_founders=n_founders,
            layout=winner_layout,
            snapshot_tick=snapshot_tick,
            trait_config=eligibility_trait_config(sensor_radius_min=winner.sensor_radius_min),
            reproduction_config=tuned_reproduction_config(
                energy_threshold=FIXED_ENERGY_THRESHOLD,
                energy_cost=FIXED_ENERGY_COST,
            ),
        )
        (snapshots_dir / f"{winner.cell_id}.txt").write_text(
            f"# winner cell={winner.cell_id} seed={snapshot_seed} tick={snapshot_tick}\n"
            f"{snapshot}\n"
        )

    return aggregates, baseline_agg, winner


def _write_comparison_csv(
    path: Path,
    baseline: EligibilityCellAggregate,
    cells: Sequence[EligibilityCellAggregate],
) -> None:
    fieldnames = [
        "cell_id",
        "layout_name",
        "sensor_radius_min",
        "n_seeds",
        "seeds_with_survivors",
        "seeds_with_any_starvation",
        "seeds_with_any_births",
        "seeds_with_reproduction_requests",
        "seeds_with_reproduction_eligibility",
        "total_starvation_deaths",
        "total_food_events",
        "total_hazard_entries",
        "total_hazard_damage",
        "total_births",
        "total_reproduction_requests",
        "total_eligible_agent_ticks",
        "total_food_events_after_min_age",
        "total_deaths_before_min_age",
        "total_moves",
        "total_stays",
        "mean_population_end",
        "max_population_end",
        "births_per_request",
        "mean_first_eligibility_tick",
        "max_energy_after_min_age",
        "median_death_age",
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
            data["mean_first_eligibility_tick"] = (
                round(row.mean_first_eligibility_tick, 4)
                if not math.isnan(row.mean_first_eligibility_tick)
                else ""
            )
            data["max_energy_after_min_age"] = round(row.max_energy_after_min_age, 4)
            data["median_death_age"] = (
                round(row.median_death_age, 4) if not math.isnan(row.median_death_age) else ""
            )
            writer.writerow(data)


def _write_winner_text(
    path: Path,
    winner: EligibilityCellAggregate | None,
    baseline: EligibilityCellAggregate,
) -> None:
    if winner is None:
        path.write_text(
            "no qualifying cell\n\n"
            "All 9 cells failed at least one of the six v0.7b criteria.\n"
            "Per the pre-registered failure mapping, structural changes\n"
            "alone are insufficient — the next move is v0.9 memory arm\n"
            "(MemoryHedonismPolicy). If perception cannot manufacture\n"
            "eligibility, recall might.\n"
        )
        return
    food_floor = baseline.total_food_events - winner.total_births
    path.write_text(
        f"winner: {winner.cell_id}\n"
        f"layout={winner.layout_name} sensor_radius_min={winner.sensor_radius_min}\n"
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
        f"-- diagnostic telemetry --\n"
        f"eligible_agent_ticks={winner.total_eligible_agent_ticks}\n"
        f"seeds_with_reproduction_eligibility={winner.seeds_with_reproduction_eligibility}\n"
        f"food_events_after_min_age={winner.total_food_events_after_min_age}\n"
        f"deaths_before_min_age={winner.total_deaths_before_min_age}\n"
        f"max_energy_after_min_age={winner.max_energy_after_min_age:.2f}\n"
    )
