"""Fear-Hunger v0.3 geometry-tightening sweep.

Holds traits, policies, hyperparameters constant; varies only chamber
geometry. The v0.2 batch ruled out "extreme traits alone produce crossing"
under the default chamber. This sweep isolates whether that null was caused
by structural masking (no eastward gradient in sensor range) or by the
valence math itself.

For each named layout in ``layouts.ALL_LAYOUTS`` the driver runs the full
positive-control grid (5 conditions across N seeds), then writes a top-level
``layout_comparison.csv`` with one row per ``(layout, condition)``.

Pre-registered binary criteria (from the v0.3 design notes):

  1. At least one non-fearful archetype enters hazard in some layout.
  2. Reckless's hazard-entry total >= 2x Fearful's in at least one layout.
  3. At least one (layout, condition) cell produces food events OR hazard
     damage > 0.

Pre-registered failure -> action mapping:

  - All three layouts null -> inspect ``core/valence.py`` (structural masking
    hypothesis falsified).
  - Only ``tight_gradient`` positive -> opposing gradients required; v0.4
    explores trait sensitivity to gradient strength.
  - Only ``near_hazard`` positive -> avoidance gradient sufficient, pursuit
    gradient unnecessary; the harness expresses a fear-driven phenotype set.
  - Both ``tight_gradient`` AND ``near_hazard`` positive -> archetypes
    differentiate whenever any gradient is present; v0.4 tunes defaults.
  - ``near_hazard`` positive but ``tight_gradient`` null -> conflicting
    signal cancels out (high-priority finding for valence inspection).
"""

from __future__ import annotations

import csv
from collections.abc import Iterable, Sequence
from dataclasses import asdict, dataclass
from pathlib import Path

from hedonism_harness.experiments.fear_hunger_chamber import ChamberRunResult
from hedonism_harness.experiments.layouts import ALL_LAYOUTS
from hedonism_harness.experiments.positive_control import (
    ALL_CONDITIONS,
    aggregate,
    run_positive_control,
)


@dataclass(frozen=True)
class LayoutConditionRow:
    """One row of the v0.3 layout-by-condition aggregate table."""

    layout: str
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


def run_geometry_v03(
    *,
    seeds: Iterable[int],
    runs_root: Path,
    batch_id: str = "fear-hunger-v0.3",
    n_ticks: int = 200,
    n_founders: int = 5,
    snapshot_tick: int = 100,
    snapshot_seed: int | None = None,
    layout_names: Sequence[str] = tuple(ALL_LAYOUTS.keys()),
) -> dict[str, dict[str, list[ChamberRunResult]]]:
    """Run all (layout, condition, seed) triples.

    Returns a nested dict keyed first by layout name, then by condition.
    Each inner value is the list of per-seed ``ChamberRunResult``s.

    Output layout::

        runs_root/batch_id/
            layout_comparison.csv         # one row per (layout, condition)
            {layout}/                     # per-layout sub-batch
                comparison.csv            # condition aggregates within layout
                snapshots/{condition}.txt
                {condition}/seed-{N}/...
    """
    seeds_list = list(seeds)
    if not seeds_list:
        msg = "run_geometry_v03 requires at least one seed"
        raise ValueError(msg)
    snapshot_seed = snapshot_seed if snapshot_seed is not None else min(seeds_list)

    batch_root = runs_root / batch_id
    batch_root.mkdir(parents=True, exist_ok=True)

    by_layout: dict[str, dict[str, list[ChamberRunResult]]] = {}
    rows: list[LayoutConditionRow] = []

    for layout_name in layout_names:
        layout = ALL_LAYOUTS[layout_name]
        by_condition = run_positive_control(
            seeds=seeds_list,
            runs_root=batch_root,
            batch_id=layout_name,
            n_ticks=n_ticks,
            n_founders=n_founders,
            snapshot_tick=snapshot_tick,
            snapshot_seed=snapshot_seed,
            layout=layout,
        )
        by_layout[layout_name] = by_condition

        for condition in ALL_CONDITIONS:
            agg = aggregate(condition, by_condition[condition])
            rows.append(
                LayoutConditionRow(
                    layout=layout_name,
                    condition=condition,
                    n_seeds=agg.n_seeds,
                    mean_population_end=agg.mean_population_end,
                    total_starvation_deaths=agg.total_starvation_deaths,
                    total_injury_deaths=agg.total_injury_deaths,
                    total_food_events=agg.total_food_events,
                    total_hazard_entries=agg.total_hazard_entries,
                    total_hazard_damage=agg.total_hazard_damage,
                    total_births=agg.total_births,
                    total_reproduction_requests=agg.total_reproduction_requests,
                    total_moves=agg.total_moves,
                    total_stays=agg.total_stays,
                )
            )

    _write_layout_comparison(batch_root / "layout_comparison.csv", rows)
    return by_layout


def _write_layout_comparison(path: Path, rows: Sequence[LayoutConditionRow]) -> None:
    fieldnames = [
        "layout",
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
        for row in rows:
            data = asdict(row)
            data["mean_population_end"] = round(row.mean_population_end, 4)
            data["total_hazard_damage"] = round(row.total_hazard_damage, 6)
            writer.writerow(data)


def evaluate_criteria(
    rows_by_layout_condition: dict[tuple[str, str], LayoutConditionRow],
) -> dict[str, bool]:
    """Apply the three pre-registered v0.3 success criteria.

    Returns a dict with boolean keys: ``any_archetype_enters_hazard``,
    ``reckless_2x_fearful_in_some_layout``, ``any_food_or_hazard_signal``.
    """
    non_fearful = {"reckless", "balanced", "explorer", "default"}

    any_archetype_enters_hazard = any(
        row.total_hazard_entries > 0
        for (_, condition), row in rows_by_layout_condition.items()
        if condition in non_fearful
    )

    reckless_2x_fearful = False
    for layout_name in {layout for (layout, _) in rows_by_layout_condition}:
        reckless = rows_by_layout_condition.get((layout_name, "reckless"))
        fearful = rows_by_layout_condition.get((layout_name, "fearful"))
        if reckless is None or fearful is None:
            continue
        # 2x rule with a floor: Reckless must show some entries, AND be at
        # least 2x Fearful's count (treating Fearful=0 as auto-pass when
        # Reckless has any entries).
        if reckless.total_hazard_entries == 0:
            continue
        if fearful.total_hazard_entries == 0:
            reckless_2x_fearful = True
            break
        if reckless.total_hazard_entries >= 2 * fearful.total_hazard_entries:
            reckless_2x_fearful = True
            break

    any_signal = any(
        row.total_food_events > 0 or row.total_hazard_damage > 0
        for row in rows_by_layout_condition.values()
    )

    return {
        "any_archetype_enters_hazard": any_archetype_enters_hazard,
        "reckless_2x_fearful_in_some_layout": reckless_2x_fearful,
        "any_food_or_hazard_signal": any_signal,
    }
