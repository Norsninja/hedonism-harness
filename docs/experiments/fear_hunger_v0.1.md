# Fear-Hunger Chamber — v0.1 pilot

**Experiment:** First canonical experiment from [SPEC §16](../SPEC.md).
**Branch:** `claude/mesa-wrapper`
**Run script:** `uv run python -c "from hedonism_harness.experiments.batch import run_chamber_batch; ..."`
**Date:** 2026-05-04

## Question

Can agents with inherited pleasure/pain thresholds — given no hard-coded
"seek food" or "explore" rules — produce recognizable survival strategies in
a 2D world?

In the chamber's specific framing: **does hunger pain ever override fear
paralysis under the default trait distribution?**

## Setup

- 20 × 6 grid arranged as horizontal sandwich:
  - `safe_x ∈ [0, 5]`: SAFE cells (8 columns wide on the left)
  - `hazard_x ∈ [8, 11]`: HAZARD cells (4-column band, hazard_damage = 8.0)
  - `food_x ∈ [14, 19]`: FOOD cells (food_value = 20.0)
  - 2-cell EMPTY corridors between zones
- 5 founders per run, spawned along `x=1` in the safe zone with even y-spread
- Policy: `HedonismPolicy(exploration_noise=0.05)`
- Reproduction enabled (default `ReproductionConfig`)
- 500 ticks per run, early termination when population reaches zero
- Seeds: `1, 2, 3, 4, 5, 42, 100, 2024`

## Result

| seed | ticks | pop_end | starvation | injury | food_events | hazard_entries | moves |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 1    | 156 | 0 | 5 | 0 | 0 | 0 | 19 |
| 2    | 146 | 0 | 5 | 0 | 0 | 0 | 15 |
| 3    | 137 | 0 | 5 | 0 | 0 | 0 | 17 |
| 4    |  94 | 0 | 5 | 0 | 0 | 0 | 14 |
| 5    | 119 | 0 | 5 | 0 | 0 | 0 | 22 |
| 42   | 118 | 0 | 5 | 0 | 0 | 0 | 13 |
| 100  | 142 | 0 | 5 | 0 | 0 | 0 | 21 |
| 2024 | 155 | 0 | 5 | 0 | 0 | 0 | 14 |
| **mean** | — | **0** | **5** | **0** | **0** | **0** | **16.9** |

Across all 8 seeds:
- **40 / 40 founders died of starvation.**
- **Zero hazard entries.** No agent ever crossed into the hazard band.
- **Zero food events.** No agent ever reached the food zone.
- **Zero births.** Reproduction never triggered (the energy threshold of 70
  is never met because energy decays from the starting 60 toward zero).
- Agents made an average of **17 moves** over **130 ticks** of life — almost
  all of those moves stayed within the safe zone (final positions cluster in
  `x ∈ [0, 4]`).

## Interpretation

This is **fear paralysis**, the first phenotype SPEC §16.3 calls out. The
default trait distribution does not produce a single individual whose
hunger-pain sensitivity, low fear sensitivity, or high risk tolerance is
strong enough to override the harness's "the safe zone is fine" verdict.

The harness reads as designed:

1. In the safe zone, hazard signals are zero. Fear is zero. Hunger pain is
   small while energy is high.
2. STAY costs less than MOVE_*, so STAY wins on net valence.
3. As energy drops, hunger pain rises — but the agent's gradient cannot find
   food because *food is invisible from the safe zone*. Sensor radius
   defaults max out at 6, the food zone starts at x=14, and a founder at x=1
   sees nothing east of itself except EMPTY and (further) HAZARD.
4. The HAZARD band is reachable by sensor before the food zone is, so the
   only directional signal pointing east is **fear**.
5. The agent has no novelty drive strong enough (default range 0.0 - 2.0) to
   override the local-gradient negative pull, and the 5% exploration noise
   produces moves but only 1 in 4 land east, half of which return west on
   the next tick because of the same pull.

The experiment behaves consistently with the harness premise: the agent is
not rewarded for "trying," it acts on felt valence. With this trait
distribution and chamber geometry, no felt valence ever recommends crossing
the hazard.

## Implications for v0.1

This is a **clean negative result**, not a bug. It tells us three things
that matter for the rest of v0.1:

1. **The harness is working.** Predicted-step + valence scoring is
   internally consistent — agents follow the gradient they see.
2. **The default trait distribution is too risk-averse for the chamber.**
   To produce the SPEC §16.3 phenotype set (paralysis vs. reckless crossing
   vs. cautious memory crossing) we need to either:
   - Widen the default trait ranges (raise `hunger_pain_sensitivity` upper
     bound, lower `fear_sensitivity` lower bound, raise `risk_tolerance`
     upper bound, raise `novelty_drive`).
   - Or seed the founder population with a known-diverse trait roll instead
     of i.i.d. uniform draws.
3. **Sensor geometry matters.** With `sensor_radius` ≤ 6 and the food zone
   starting at x=14, founders at x=1 receive zero signal from food. Either
   the layout needs to be tighter, or sensors need to project further (with
   the metabolic-cost tradeoff already specified).

## Suggested follow-ups

- Re-run the chamber with `TraitConfig` tuned for diversity. Adversarial:
  pick a trait profile we *expect* will cross (high hunger sensitivity, low
  fear, high risk tolerance) and confirm it does.
- Tighter chamber: shrink the EMPTY corridors so the food zone is within
  default sensor radius.
- Memory: add founders that use `MemoryHedonismPolicy` and observe whether
  "remembered good" propagates after the first crossing.
- Reproduction-cost scoring fix (already shipped this commit) should reduce
  any remaining tendency for non-reproducers to mispredict reproduction
  pleasure under future runs.

## Reproducing

```bash
uv run python -c "
from pathlib import Path
from hedonism_harness.experiments.batch import run_chamber_batch
run_chamber_batch(
    seeds=[1, 2, 3, 4, 5, 42, 100, 2024],
    runs_root=Path('runs'),
    batch_id='fear-hunger-v0.1',
    n_ticks=500,
    n_founders=5,
)
"
```

Outputs land in `runs/fear-hunger-v0.1/`:

```
fear-hunger-v0.1/
    summary.csv
    seed-1/
        config.json
        manifest.json
        episode_metrics.csv
        agent_lifetimes.csv
        lineages.csv
        events.jsonl
        summary.md
    seed-2/
        ...
```
