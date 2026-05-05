"""v0.22 hazard-damage sweep driver.

Runs ``V0_22_ARMS`` (4 arms) x 1 chamber (food_ladder only) x 8 seeds
= 32 runs, persisting per-arm comparison.csv into
``runs/fear-hunger-v0.22-food_ladder/``. Pre-reg:
``docs/experiments/fear_hunger_v0.22.md``.

The headline table includes the v0.22 decisive columns:
  - hazard: per-tile hazard damage (the one swept variable)
  - residual: pool_in_death_residual (recycling channel observable)
  - starv / inj: starvation vs injury death split (distinguishes
    "no injuries because hazard=0" from "no injuries because agents
    avoided hazards" — both produce low residual but mean different
    things mechanistically)
  - hazard_entries: agent hazard exposure (channel mechanically
    active when this is non-trivial alongside injury_deaths)

tight_gradient is deliberately excluded — it is starvation-dominated
with near-zero recycling already, so sweeping hazard_damage there
tests a near-null channel and is not informative.

Usage:
    uv run python scripts/v0.22_sweep.py
"""

from __future__ import annotations

import time
from pathlib import Path

from hedonism_harness.experiments.comparison_grid import V0_22_ARMS, run_comparison_grid

RUNS_ROOT = Path("runs")
CHAMBER = "food_ladder"
SEEDS = tuple(range(1, 9))
N_TICKS = 200
N_FOUNDERS = 5


def main() -> None:
    RUNS_ROOT.mkdir(parents=True, exist_ok=True)
    overall_start = time.time()
    batch_id = f"fear-hunger-v0.22-{CHAMBER}"
    print(f"=== {batch_id} ===", flush=True)
    chamber_start = time.time()
    aggregates = run_comparison_grid(
        seeds=SEEDS,
        runs_root=RUNS_ROOT,
        batch_id=batch_id,
        layout_name=CHAMBER,
        n_ticks=N_TICKS,
        n_founders=N_FOUNDERS,
        arms=V0_22_ARMS,
    )
    elapsed = time.time() - chamber_start
    print(f"  done in {elapsed:.1f}s", flush=True)
    # v0.22 headline: hazard up front, then productivity, then the
    # decisive recycling-vs-geometry telemetry (residual flux,
    # starvation/injury death split, hazard entries, blocks).
    for arm, agg in zip(V0_22_ARMS, aggregates, strict=True):
        fcpb = agg.food_consumed_per_birth
        pool_end = f"{agg.mean_pool_end:.0f}" if agg.mean_pool_end is not None else "—"
        pool_min = f"{agg.pool_min_observed:.0f}" if agg.pool_min_observed is not None else "—"
        hazard = arm.hazard_damage if arm.hazard_damage is not None else 8.0
        print(
            f"  {agg.arm_label:>10} | "
            f"hazard={hazard:4.1f} "
            f"births={agg.total_births:4d} "
            f"b>50={agg.births_after_tick_50:4d} "
            f"surv={agg.seeds_with_survivors}/{agg.n_seeds} "
            f"food={agg.total_food_events:4d} "
            f"respawn={agg.total_food_respawn_events:4d} "
            f"fcpb={fcpb:6.2f} "
            f"pool_min={pool_min:>6} "
            f"pool_end={pool_end:>6} "
            f"residual={agg.total_pool_in_death_residual:7.1f} "
            f"starv={agg.total_starvation_deaths:3d} "
            f"inj={agg.total_injury_deaths:3d} "
            f"haz_entries={agg.total_hazard_entries:4d} "
            f"r_blk={agg.total_pool_respawn_denied:3d} "
            f"b_blk={agg.total_pool_birth_denied:3d} "
            f"xfer={agg.total_parent_energy_transferred_to_child:6.0f}",
            flush=True,
        )
    print(f"\nTOTAL elapsed: {time.time() - overall_start:.1f}s", flush=True)


if __name__ == "__main__":
    main()
