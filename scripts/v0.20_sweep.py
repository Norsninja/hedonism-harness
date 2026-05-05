"""v0.20 parent-transfer + pool-gap sweep driver.

Runs ``V0_20_ARMS`` (6 arms) x 2 chambers (tight_gradient, food_ladder)
x 8 seeds = 96 runs, persisting per-arm comparison.csv into
``runs/fear-hunger-v0.20-{chamber}/``. Pre-reg:
``docs/experiments/fear_hunger_v0.20.md``.

Usage:
    uv run python scripts/v0.20_sweep.py
"""

from __future__ import annotations

import time
from pathlib import Path

from hedonism_harness.experiments.comparison_grid import V0_20_ARMS, run_comparison_grid

RUNS_ROOT = Path("runs")
CHAMBERS = ("tight_gradient", "food_ladder")
SEEDS = tuple(range(1, 9))
N_TICKS = 200
N_FOUNDERS = 5


def main() -> None:
    RUNS_ROOT.mkdir(parents=True, exist_ok=True)
    overall_start = time.time()
    for chamber in CHAMBERS:
        batch_id = f"fear-hunger-v0.20-{chamber}"
        print(f"=== {batch_id} ===", flush=True)
        chamber_start = time.time()
        aggregates = run_comparison_grid(
            seeds=SEEDS,
            runs_root=RUNS_ROOT,
            batch_id=batch_id,
            layout_name=chamber,
            n_ticks=N_TICKS,
            n_founders=N_FOUNDERS,
            arms=V0_20_ARMS,
        )
        elapsed = time.time() - chamber_start
        print(f"  done in {elapsed:.1f}s", flush=True)
        # Tight headline table — adds the v0.20 conservation-ledger
        # accumulators to the v0.19 layout.
        for agg in aggregates:
            fcpb = agg.food_consumed_per_birth
            pool_end = f"{agg.mean_pool_end:.0f}" if agg.mean_pool_end is not None else "—"
            print(
                f"  {agg.arm_label:>20} | "
                f"births={agg.total_births:4d} "
                f"b>50={agg.births_after_tick_50:4d} "
                f"surv={agg.seeds_with_survivors}/{agg.n_seeds} "
                f"food={agg.total_food_events:4d} "
                f"respawn={agg.total_food_respawn_events:4d} "
                f"fcpb={fcpb:6.2f} "
                f"pool_end={pool_end:>6} "
                f"r_blk={agg.total_pool_respawn_denied:3d} "
                f"b_blk={agg.total_pool_birth_denied:3d} "
                f"pe_blk={agg.total_births_blocked_by_parent_energy:3d} "
                f"heat={agg.total_reproduction_heat_loss:6.0f} "
                f"xfer={agg.total_parent_energy_transferred_to_child:6.0f}",
                flush=True,
            )
    print(f"\nTOTAL elapsed: {time.time() - overall_start:.1f}s", flush=True)


if __name__ == "__main__":
    main()
