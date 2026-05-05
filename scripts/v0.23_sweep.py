"""v0.23 hazard-zero influx-frontier sweep driver.

Runs ``V0_23_ARMS`` (5 arms) x 2 chambers (tight_gradient, food_ladder)
x 8 seeds = 80 runs, persisting per-arm comparison.csv into
``runs/fear-hunger-v0.23-{chamber}/``. Pre-reg:
``docs/experiments/fear_hunger_v0.23.md``.

The headline table mirrors v0.21 + v0.22:
  - influx column up front so the frontier curve reads top-to-bottom.
  - starvation/injury death split (carried from v0.22). At hazard=0,
    every arm has injury_deaths=0 by H5; the column is a runtime
    halt-condition observable. Likewise residual ≈ 0 by H6.
  - hazard_entries: at hazard=0, agents enter hazard tiles freely
    because the GradientPolicy avoidance signal keys on damage value
    (see fear_hunger_v0.23.md §"Watch-outs"). This column documents
    the routing-side hazard exposure.
  - in_influx accumulator so the H1 conservation invariant
    (pool_in_ambient_influx == ambient_influx_rate * sum(executed_ticks))
    is visible at a glance.

Usage:
    uv run python scripts/v0.23_sweep.py
"""

from __future__ import annotations

import time
from pathlib import Path

from hedonism_harness.experiments.comparison_grid import V0_23_ARMS, run_comparison_grid

RUNS_ROOT = Path("runs")
CHAMBERS = ("tight_gradient", "food_ladder")
SEEDS = tuple(range(1, 9))
N_TICKS = 200
N_FOUNDERS = 5


def main() -> None:
    RUNS_ROOT.mkdir(parents=True, exist_ok=True)
    overall_start = time.time()
    for chamber in CHAMBERS:
        batch_id = f"fear-hunger-v0.23-{chamber}"
        print(f"=== {batch_id} ===", flush=True)
        chamber_start = time.time()
        aggregates = run_comparison_grid(
            seeds=SEEDS,
            runs_root=RUNS_ROOT,
            batch_id=batch_id,
            layout_name=chamber,
            n_ticks=N_TICKS,
            n_founders=N_FOUNDERS,
            arms=V0_23_ARMS,
        )
        elapsed = time.time() - chamber_start
        print(f"  done in {elapsed:.1f}s", flush=True)
        for arm, agg in zip(V0_23_ARMS, aggregates, strict=True):
            fcpb = agg.food_consumed_per_birth
            pool_end = f"{agg.mean_pool_end:.0f}" if agg.mean_pool_end is not None else "—"
            pool_min = f"{agg.pool_min_observed:.0f}" if agg.pool_min_observed is not None else "—"
            influx = arm.ambient_influx_rate if arm.ambient_influx_rate is not None else 0.0
            print(
                f"  {agg.arm_label:>32} | "
                f"influx={influx:3.1f} "
                f"births={agg.total_births:4d} "
                f"b>50={agg.births_after_tick_50:4d} "
                f"surv={agg.seeds_with_survivors}/{agg.n_seeds} "
                f"food={agg.total_food_events:4d} "
                f"respawn={agg.total_food_respawn_events:4d} "
                f"fcpb={fcpb:6.2f} "
                f"pool_min={pool_min:>6} "
                f"pool_end={pool_end:>6} "
                f"residual={agg.total_pool_in_death_residual:5.1f} "
                f"starv={agg.total_starvation_deaths:3d} "
                f"inj={agg.total_injury_deaths:3d} "
                f"haz_entries={agg.total_hazard_entries:4d} "
                f"r_blk={agg.total_pool_respawn_denied:3d} "
                f"b_blk={agg.total_pool_birth_denied:3d} "
                f"in_influx={agg.total_pool_in_ambient_influx:6.0f} "
                f"xfer={agg.total_parent_energy_transferred_to_child:6.0f}",
                flush=True,
            )
    print(f"\nTOTAL elapsed: {time.time() - overall_start:.1f}s", flush=True)


if __name__ == "__main__":
    main()
