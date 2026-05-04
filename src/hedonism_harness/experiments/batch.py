"""Thin wrapper for running multiple Fear-Hunger Chamber seeds.

Per SPEC §17, batch runs land each in its own ``runs/{run_id}/`` directory
and produce a top-level summary CSV ``runs/{batch_id}/summary.csv`` with one
row per seed.

This is deliberately simple — no parallelism, no parameter sweeps yet. Once
``mesa.batch_run`` integration becomes worth the dependency, this module is
the seam to swap in.
"""

from __future__ import annotations

import csv
from dataclasses import asdict
from pathlib import Path
from typing import TYPE_CHECKING

from hedonism_harness.experiments.fear_hunger_chamber import (
    ChamberLayout,
    run_chamber,
)

if TYPE_CHECKING:
    from collections.abc import Callable, Iterable

    from hedonism_harness.experiments.fear_hunger_chamber import ChamberRunResult
    from hedonism_harness.policies.base import Policy


def run_chamber_batch(
    *,
    seeds: Iterable[int],
    runs_root: Path,
    batch_id: str,
    n_ticks: int = 200,
    n_founders: int = 5,
    layout: ChamberLayout | None = None,
    policy_factory: Callable[[], Policy] | None = None,
) -> list[ChamberRunResult]:
    """Run the chamber for each seed; write per-run files + a batch summary CSV."""
    batch_root = runs_root / batch_id
    batch_root.mkdir(parents=True, exist_ok=True)

    results: list[ChamberRunResult] = []
    for seed in seeds:
        kwargs: dict[str, object] = {
            "seed": seed,
            "runs_root": batch_root,
            "run_id": f"seed-{seed}",
            "n_founders": n_founders,
            "n_ticks": n_ticks,
            "layout": layout,
        }
        if policy_factory is not None:
            kwargs["policy_factory"] = policy_factory
        result = run_chamber(**kwargs)  # type: ignore[arg-type]
        results.append(result)

    _write_batch_summary(batch_root / "summary.csv", results)
    return results


def _write_batch_summary(path: Path, results: list[ChamberRunResult]) -> None:
    if not results:
        path.write_text("")
        return
    fieldnames = [
        "run_id",
        "seed",
        "ticks_completed",
        "population_start",
        "population_end",
        "survivors",
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
