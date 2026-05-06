"""v0.33 tight h*=8 hazard-axis third-stream calibration sweep driver.

Runs ``V0_33_TIGHT_H_ARMS`` (4 arms — h in {0, 4, 8, 12} at influx=1.0,
element-wise identical to V0_32_TIGHT_H_ARMS by construction;
substrate-byte-identity to V0_25_ARMS at the matched labels)
x tight_gradient x seeds 17..24 = 32 runs, persisting per-arm
comparison.csv into ``runs/fear-hunger-v0.33-tight_gradient/``.

Pre-reg: [[docs/experiments/fear_hunger_v0.33.md]].

Central question: does the v0.32 H6 WEAK directional signal on the
hazard axis compound across three independent 8-seed streams (v0.25
1..8 + v0.32 9..16 + v0.33 17..24), or does it collapse? Mirrors the
v0.30 -> v0.31 weight-axis trajectory.

The v0.33 audit (`scripts/v0.33_audit.py`) consumes these artifacts
plus the v0.25 (1..8) and v0.32 (9..16) artifacts on disk, applies
single-stream diagnostic verdicts to all three streams, and applies a
pre-committed pooled 24-seed verdict (linearly-scaled thresholds
15/15/3/15) as the v0.33 headline.

Usage:
    uv run python scripts/v0.33_sweep.py
"""

from __future__ import annotations

import time
from pathlib import Path

from hedonism_harness.experiments.comparison_grid import V0_33_TIGHT_H_ARMS, run_comparison_grid

RUNS_ROOT = Path("runs")
CHAMBER = "tight_gradient"
SEEDS = tuple(range(17, 25))
N_TICKS = 200
N_FOUNDERS = 5
BATCH_ID = "fear-hunger-v0.33-tight_gradient"


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
        arms=V0_33_TIGHT_H_ARMS,
    )
    elapsed = time.time() - chamber_start
    print(f"  done in {elapsed:.1f}s", flush=True)
    for arm, agg in zip(V0_33_TIGHT_H_ARMS, aggregates, strict=True):
        fcpb = agg.food_consumed_per_birth
        pool_end = f"{agg.mean_pool_end:.0f}" if agg.mean_pool_end is not None else "—"
        pool_min = f"{agg.pool_min_observed:.0f}" if agg.pool_min_observed is not None else "—"
        print(
            f"  {agg.arm_label:>30} | "
            f"hzd={arm.hazard_damage:4.1f} "
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
