"""v0.31 tight w*=0.75 third-stream calibration sweep driver.

Runs ``V0_31_TIGHT_W_ARMS`` (3 arms — w in {0.5, 0.75, 1.0},
substrate-byte-identical to V0_27_ARMS / V0_29_ARMS / V0_30_TIGHT_W_ARMS
at the matched labels) x tight_gradient x seeds 17..24 = 24 runs,
persisting per-arm comparison.csv into
``runs/fear-hunger-v0.31-tight_gradient/``.

Pre-reg: [[docs/experiments/fear_hunger_v0.31.md]].

Central question: does the v0.30 H6 WEAK directional signal compound
across a third independent 8-seed stream, or does it collapse, when
streams 1..8, 9..16, 17..24 are pooled and audited under the
pre-committed pooled 4-tier classifier (linear-scaled thresholds
15/15/3/15)?

The v0.31 audit (`scripts/v0.31_audit.py`) consumes these artifacts
together with v0.27 and v0.30 artifacts to produce the per-stream
single-stream verdicts plus the pooled 24-seed verdict.

Usage:
    uv run python scripts/v0.31_sweep.py
"""

from __future__ import annotations

import time
from pathlib import Path

from hedonism_harness.experiments.comparison_grid import V0_31_TIGHT_W_ARMS, run_comparison_grid

RUNS_ROOT = Path("runs")
CHAMBER = "tight_gradient"
SEEDS = tuple(range(17, 25))
N_TICKS = 200
N_FOUNDERS = 5
BATCH_ID = "fear-hunger-v0.31-tight_gradient"


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
        arms=V0_31_TIGHT_W_ARMS,
    )
    elapsed = time.time() - chamber_start
    print(f"  done in {elapsed:.1f}s", flush=True)
    for arm, agg in zip(V0_31_TIGHT_W_ARMS, aggregates, strict=True):
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
