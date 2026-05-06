"""v0.29 food_ladder w=0.75 dip reproducibility sweep driver.

Runs ``V0_29_ARMS`` (3 arms — w in {0.5, 0.75, 1.0}, substrate-byte-
identical to V0_27_ARMS at the matched labels) x food_ladder x
seeds 9..16 = 24 runs, persisting per-arm comparison.csv into
``runs/fear-hunger-v0.29-food_ladder/``.

Pre-reg: [[docs/experiments/fear_hunger_v0.29.md]].

Central question: does a fresh RNG stream (seeds 9..16) reproduce the
v0.27 / v0.28 b>50=89 dip at w=0.75 on food_ladder, or was the dip
sample-specific to the (1..8) seed set?

The v0.29 diagnostic (`scripts/v0.29_diagnostic.py`) consumes these
artifacts and produces the per-seed paired-comparison report.

Usage:
    uv run python scripts/v0.29_sweep.py
"""

from __future__ import annotations

import time
from pathlib import Path

from hedonism_harness.experiments.comparison_grid import V0_29_ARMS, run_comparison_grid

RUNS_ROOT = Path("runs")
CHAMBER = "food_ladder"
SEEDS = tuple(range(9, 17))
N_TICKS = 200
N_FOUNDERS = 5
BATCH_ID = "fear-hunger-v0.29-food_ladder"


def main() -> None:
    RUNS_ROOT.mkdir(parents=True, exist_ok=True)
    print(f"=== {BATCH_ID} (seeds {SEEDS[0]}..{SEEDS[-1]}) ===", flush=True)
    chamber_start = time.time()
    aggregates = run_comparison_grid(
        seeds=SEEDS,
        runs_root=RUNS_ROOT,
        batch_id=BATCH_ID,
        layout_name=CHAMBER,
        n_ticks=N_TICKS,
        n_founders=N_FOUNDERS,
        arms=V0_29_ARMS,
    )
    elapsed = time.time() - chamber_start
    print(f"  done in {elapsed:.1f}s", flush=True)
    for arm, agg in zip(V0_29_ARMS, aggregates, strict=True):
        fcpb = agg.food_consumed_per_birth
        pool_end = f"{agg.mean_pool_end:.0f}" if agg.mean_pool_end is not None else "—"
        pool_min = f"{agg.pool_min_observed:.0f}" if agg.pool_min_observed is not None else "—"
        avd = arm.hazard_avoidance_weight if arm.hazard_avoidance_weight is not None else 1.0
        print(
            f"  {agg.arm_label:>16} | "
            f"avd={avd:4.2f} "
            f"births={agg.total_births:4d} "
            f"b>50={agg.births_after_tick_50:4d} "
            f"surv={agg.seeds_with_survivors}/{agg.n_seeds} "
            f"food={agg.total_food_events:4d} "
            f"respawn={agg.total_food_respawn_events:4d} "
            f"fcpb={fcpb:6.2f} "
            f"pool_min={pool_min:>6} "
            f"pool_end={pool_end:>6} "
            f"residual={agg.total_pool_in_death_residual:6.1f} "
            f"starv={agg.total_starvation_deaths:3d} "
            f"inj={agg.total_injury_deaths:3d} "
            f"haz_entries={agg.total_hazard_entries:4d} "
            f"r_blk={agg.total_pool_respawn_denied:3d} "
            f"b_blk={agg.total_pool_birth_denied:3d} "
            f"in_influx={agg.total_pool_in_ambient_influx:6.0f} "
            f"xfer={agg.total_parent_energy_transferred_to_child:6.0f}",
            flush=True,
        )


if __name__ == "__main__":
    main()
