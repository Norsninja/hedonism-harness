"""v0.24 population-dynamics diagnostic driver.

Walks the v0.21 (hazard=8) and v0.23 (hazard=0) sweep artifacts on
disk and emits per-(chamber, hazard, influx) cell aggregates testing
the population-governor hypothesis from
``docs/experiments/fear_hunger_v0.24.md``.

For each cell the diagnostic computes:
  - mean peak population per run (H1 observable)
  - mean tick of peak
  - mean late-window (t >= 100) population (H2 observable)
  - lifespan p50 / p90 across pooled agents
  - starvation deaths bucketed in 50-tick windows (H3 observable)

Usage:
    uv run python scripts/v0.24_population_diagnostic.py

Requires v0.21 + v0.23 sweeps to have been materialised on disk
(``scripts/v0.21_sweep.py`` and ``scripts/v0.23_sweep.py``); the
diagnostic does NOT run any sweeps itself.
"""

from __future__ import annotations

import csv
import time
from dataclasses import asdict, dataclass
from pathlib import Path

from hedonism_harness.experiments.population_dynamics import (
    CellAggregate,
    aggregate_cell,
    load_population_trajectory,
)

RUNS_ROOT = Path("runs")
DIAG_ROOT = RUNS_ROOT / "fear-hunger-v0.24-diagnostic"

CHAMBERS: tuple[str, ...] = ("tight_gradient", "food_ladder")
INFLUXES: tuple[str, ...] = ("0", "0.5", "1.0", "1.5", "2.0")
SEEDS: tuple[int, ...] = tuple(range(1, 9))
N_FOUNDERS: int = 5
N_TICKS: int = 200

# v0.21 arm labels: transfer-1500-influx-{influx}
# v0.23 arm labels: transfer-1500-hzd0-influx-{influx}
HAZARD_REGIMES: tuple[tuple[str, int, str], ...] = (
    ("v0.21", 8, "transfer-1500-influx-{influx}"),
    ("v0.23", 0, "transfer-1500-hzd0-influx-{influx}"),
)


@dataclass(frozen=True)
class DiagnosticCell:
    """One (chamber, hazard, influx) row in the diagnostic output."""

    chamber: str
    sweep: str  # "v0.21" or "v0.23"
    hazard: int
    influx: str
    aggregate: CellAggregate


def _arm_dir(sweep: str, chamber: str, arm_label: str) -> Path:
    return RUNS_ROOT / f"fear-hunger-{sweep}-{chamber}" / "arms" / arm_label


def _events_path(sweep: str, chamber: str, arm_label: str, seed: int) -> Path:
    return _arm_dir(sweep, chamber, arm_label) / f"seed-{seed}" / "events.jsonl"


def _build_cells() -> list[DiagnosticCell]:
    cells: list[DiagnosticCell] = []
    for chamber in CHAMBERS:
        for sweep, hazard, label_template in HAZARD_REGIMES:
            for influx in INFLUXES:
                arm_label = label_template.format(influx=influx)
                trajectories = []
                missing = []
                for seed in SEEDS:
                    p = _events_path(sweep, chamber, arm_label, seed)
                    if not p.exists():
                        missing.append(p)
                        continue
                    trajectories.append(
                        load_population_trajectory(p, n_founders=N_FOUNDERS, n_ticks=N_TICKS)
                    )
                if missing:
                    msg = (
                        f"Missing events.jsonl for {sweep}/{chamber}/{arm_label}: "
                        f"{len(missing)} of {len(SEEDS)} seeds absent. Re-run the "
                        f"corresponding sweep before invoking this diagnostic."
                    )
                    raise FileNotFoundError(msg)
                agg = aggregate_cell(trajectories, n_ticks=N_TICKS, late_window_start=100)
                cells.append(
                    DiagnosticCell(
                        chamber=chamber, sweep=sweep, hazard=hazard, influx=influx, aggregate=agg
                    )
                )
    return cells


def _write_cells_csv(path: Path, cells: list[DiagnosticCell]) -> None:
    if not cells:
        path.write_text("")
        return
    sample = cells[0]
    flat_keys = [
        "chamber",
        "sweep",
        "hazard",
        "influx",
        "n_seeds",
        "mean_peak_population",
        "mean_tick_of_peak",
        "mean_population_t_gt_100",
        "lifespan_p50",
        "lifespan_p90",
    ]
    bucket_keys = [f"starv_{w}" for w in sample.aggregate.starvation_deaths_by_window]
    fieldnames = flat_keys + bucket_keys + ["starvation_peak_window"]
    with path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for c in cells:
            row: dict[str, object] = {
                "chamber": c.chamber,
                "sweep": c.sweep,
                "hazard": c.hazard,
                "influx": c.influx,
                "n_seeds": c.aggregate.n_seeds,
                "mean_peak_population": round(c.aggregate.mean_peak_population, 3),
                "mean_tick_of_peak": round(c.aggregate.mean_tick_of_peak, 3),
                "mean_population_t_gt_100": round(c.aggregate.mean_population_t_gt_100, 3),
                "lifespan_p50": round(c.aggregate.lifespan_p50, 3),
                "lifespan_p90": round(c.aggregate.lifespan_p90, 3),
                "starvation_peak_window": c.aggregate.starvation_peak_window,
            }
            for w, count in c.aggregate.starvation_deaths_by_window.items():
                row[f"starv_{w}"] = count
            writer.writerow(row)


def _print_headline_table(cells: list[DiagnosticCell]) -> None:
    """One block per chamber; one row per (sweep, influx) cell."""
    by_chamber: dict[str, list[DiagnosticCell]] = {c: [] for c in CHAMBERS}
    for cell in cells:
        by_chamber[cell.chamber].append(cell)
    for chamber, rows in by_chamber.items():
        print(f"\n=== {chamber} ===", flush=True)
        print(
            f"  {'sweep':>6} {'haz':>3} {'influx':>6}  "
            f"{'peak':>6} {'tpk':>5} {'late>100':>9} "
            f"{'lp50':>6} {'lp90':>6}  "
            f"{'starv 0-49':>10} {'50-99':>6} {'100-149':>8} {'150-199':>8} "
            f"{'pk_win':>8}",
            flush=True,
        )
        # Sort: hazard=8 first, then hazard=0; within each, influx ascending.
        rows.sort(key=lambda c: (-c.hazard, float(c.influx)))
        for c in rows:
            agg = c.aggregate
            buckets = agg.starvation_deaths_by_window
            print(
                f"  {c.sweep:>6} {c.hazard:>3} {c.influx:>6}  "
                f"{agg.mean_peak_population:6.2f} "
                f"{agg.mean_tick_of_peak:5.1f} "
                f"{agg.mean_population_t_gt_100:9.2f} "
                f"{agg.lifespan_p50:6.2f} "
                f"{agg.lifespan_p90:6.2f}  "
                f"{buckets.get('0-49', 0):10d} "
                f"{buckets.get('50-99', 0):6d} "
                f"{buckets.get('100-149', 0):8d} "
                f"{buckets.get('150-199', 0):8d} "
                f"{agg.starvation_peak_window:>8}",
                flush=True,
            )


def _adjudicate(cells: list[DiagnosticCell]) -> None:
    """Print a brief H1/H2/H3/H4 adjudication summary."""
    by_key: dict[tuple[str, int, str], CellAggregate] = {
        (c.chamber, c.hazard, c.influx): c.aggregate for c in cells
    }
    print("\n=== Hypothesis adjudication ===", flush=True)
    for chamber in CHAMBERS:
        h1_fires = []
        h2_fires = []
        h3_fires = []
        for influx in INFLUXES:
            haz0 = by_key.get((chamber, 0, influx))
            haz8 = by_key.get((chamber, 8, influx))
            if haz0 is None or haz8 is None:
                continue
            h1 = haz0.mean_peak_population > haz8.mean_peak_population
            h2 = haz0.mean_population_t_gt_100 < haz8.mean_population_t_gt_100
            h3 = haz0.starvation_peak_window in {"50-99", "100-149"}
            h1_fires.append(h1)
            h2_fires.append(h2)
            h3_fires.append(h3)
            print(
                f"  {chamber:<14} influx={influx:>4}  "
                f"H1(peak↑): {('yes' if h1 else ' no')}  "
                f"H2(late↓): {('yes' if h2 else ' no')}  "
                f"H3(spike): {('yes' if h3 else ' no')}",
                flush=True,
            )
        print(
            f"  {chamber:<14} summary: "
            f"H1 {sum(h1_fires)}/{len(h1_fires)}  "
            f"H2 {sum(h2_fires)}/{len(h2_fires)}  "
            f"H3 {sum(h3_fires)}/{len(h3_fires)}",
            flush=True,
        )


def main() -> None:
    DIAG_ROOT.mkdir(parents=True, exist_ok=True)
    start = time.time()
    cells = _build_cells()
    elapsed = time.time() - start
    _print_headline_table(cells)
    _adjudicate(cells)
    out_csv = DIAG_ROOT / "per_cell.csv"
    _write_cells_csv(out_csv, cells)
    # Also write a flat dataclass CSV for downstream tooling.
    flat_csv = DIAG_ROOT / "per_cell_flat.csv"
    if cells:
        with flat_csv.open("w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["chamber", "sweep", "hazard", "influx", *asdict(cells[0].aggregate)])
            for c in cells:
                writer.writerow(
                    [c.chamber, c.sweep, c.hazard, c.influx, *asdict(c.aggregate).values()]
                )
    print(
        f"\nElapsed: {elapsed:.1f}s. Wrote {out_csv}.",
        flush=True,
    )


if __name__ == "__main__":
    main()
