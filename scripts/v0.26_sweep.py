"""v0.26 perception-vs-damage decoupling sweep driver.

Runs ``V0_26_ARMS`` (4 arms — the hazard x avoidance_weight 2x2 grid)
x 2 chambers (tight_gradient, food_ladder) x 8 seeds = 64 runs,
persisting per-arm comparison.csv into
``runs/fear-hunger-v0.26-{chamber}/``. Pre-reg:
``docs/experiments/fear_hunger_v0.26.md``.

The headline table mirrors v0.25 with one new column (``avd``) so the
2x2 grid reads cleanly. Anchors against v0.25 (hzd8-influx-1.0 and
hzd0-influx-1.0 on each chamber) verify the new seam preserves
bit-identity at the hzd8/avd1.0 (coupled) and hzd0/* (phantom and
no-hazard) cells.

Usage:
    uv run python scripts/v0.26_sweep.py
"""

from __future__ import annotations

import time
from pathlib import Path

from hedonism_harness.experiments.comparison_grid import V0_26_ARMS, run_comparison_grid

RUNS_ROOT = Path("runs")
CHAMBERS = ("tight_gradient", "food_ladder")
SEEDS = tuple(range(1, 9))
N_TICKS = 200
N_FOUNDERS = 5


def main() -> None:
    RUNS_ROOT.mkdir(parents=True, exist_ok=True)
    overall_start = time.time()
    for chamber in CHAMBERS:
        batch_id = f"fear-hunger-v0.26-{chamber}"
        print(f"=== {batch_id} ===", flush=True)
        chamber_start = time.time()
        aggregates = run_comparison_grid(
            seeds=SEEDS,
            runs_root=RUNS_ROOT,
            batch_id=batch_id,
            layout_name=chamber,
            n_ticks=N_TICKS,
            n_founders=N_FOUNDERS,
            arms=V0_26_ARMS,
        )
        elapsed = time.time() - chamber_start
        print(f"  done in {elapsed:.1f}s", flush=True)
        for arm, agg in zip(V0_26_ARMS, aggregates, strict=True):
            fcpb = agg.food_consumed_per_birth
            pool_end = f"{agg.mean_pool_end:.0f}" if agg.mean_pool_end is not None else "—"
            pool_min = f"{agg.pool_min_observed:.0f}" if agg.pool_min_observed is not None else "—"
            hazard = arm.hazard_damage if arm.hazard_damage is not None else 8.0
            avd = arm.hazard_avoidance_weight if arm.hazard_avoidance_weight is not None else 1.0
            print(
                f"  {agg.arm_label:>16} | "
                f"haz={hazard:4.1f} avd={avd:3.1f} "
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
    print(f"\nTOTAL elapsed: {time.time() - overall_start:.1f}s", flush=True)


if __name__ == "__main__":
    main()
