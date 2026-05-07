"""v0.43R substrate-rewrite intervention sweep driver.

Runs ``V0_43R_INTERVENTION_ARMS`` (6 arms — A_null,
B_reduce_food_density_50pct, C_density_preserving_perturbation at hazards
{0, 8} on substrate-byte-identical V0_25/V0_42 footing) x tight_gradient
x seeds 49..56 (a fresh band beyond v0.42's 41..48). Total: 6 arms x
8 seeds = **48 runs**.

Pre-reg: [[docs/experiments/fear_hunger_v0.43R.md]].

Replacement for the halted v0.43 sweep (see SUBSTRATE_PREFLIGHT_HALT
addendum in [[docs/experiments/fear_hunger_v0.43.md]]). v0.43's
flatten/shuffle code paths remain dispatchable but are NOT exercised
by V0_43R_INTERVENTION_ARMS.

Central question: does halving the food density at the tick-50/tick-51
boundary disrupt the post-50 dominance pattern, while the
density-preserving 25/75 pair-perturbation control (per-cell magnitude
matched to B at uniform substrate) does not? If yes, food density at
tick 50 is **necessary** for the v0.34..v0.41 pattern.

The v0.43R audit (``scripts/v0_43R_intervention_audit.py``) consumes
the per-arm comparison.csv + per-run events.jsonl, computing
``post_intervention_top_lineage_b50_share`` over the 5-lineage pool
and applying the locked decision rule:
  B reduces share at h=8 by at least 0.15 AND
  C remains within +/- 0.10 of A at h=8.

Usage:
    uv run python scripts/v0.43R_sweep.py
"""

from __future__ import annotations

import time
from pathlib import Path

from hedonism_harness.experiments.comparison_grid import (
    V0_43R_INTERVENTION_ARMS,
    run_comparison_grid,
)

RUNS_ROOT = Path("runs")
CHAMBER = "tight_gradient"
SEEDS = tuple(range(49, 57))
N_TICKS = 200
N_FOUNDERS = 5
BATCH_ID = "fear-hunger-v0.43R-tight_gradient"


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
        arms=V0_43R_INTERVENTION_ARMS,
    )
    elapsed = time.time() - chamber_start
    print(f"  done in {elapsed:.1f}s", flush=True)
    for arm, agg in zip(V0_43R_INTERVENTION_ARMS, aggregates, strict=True):
        fcpb = agg.food_consumed_per_birth
        pool_end = f"{agg.mean_pool_end:.0f}" if agg.mean_pool_end is not None else "—"
        pool_min = f"{agg.pool_min_observed:.0f}" if agg.pool_min_observed is not None else "—"
        print(
            f"  {agg.arm_label:>54} | "
            f"hzd={arm.hazard_damage:4.1f} "
            f"kind={arm.intervention_kind:>42} "
            f"births={agg.total_births:4d} "
            f"b>50={agg.births_after_tick_50:4d} "
            f"surv={agg.seeds_with_survivors}/{agg.n_seeds} "
            f"food={agg.total_food_events:4d} "
            f"fcpb={fcpb:6.2f} "
            f"pool_min={pool_min:>6} "
            f"pool_end={pool_end:>6} "
            f"residual={agg.total_pool_in_death_residual:6.1f} "
            f"starv={agg.total_starvation_deaths:3d} "
            f"inj={agg.total_injury_deaths:3d}",
            flush=True,
        )


if __name__ == "__main__":
    main()
