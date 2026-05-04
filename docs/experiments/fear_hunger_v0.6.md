# Fear-Hunger Chamber — v0.6 trait-config grid sweep

**Experiment:** Validate whether v0.5 ``permissive`` is a hand-tuned local optimum or a lucky point.
**Branch:** `claude/trait-grid-v0.6`
**Date:** 2026-05-04
**Run:** `runs/fear-hunger-v0.6/`

## Question

The v0.5 result showed a hand-picked permissive ``TraitConfig`` produced
mixed-phenotype populations under random sampling. But six numbers were
chosen by reading the v0.4 evidence — was that point a local optimum or
just a lucky cell? v0.6 sweeps a 3×3×3 grid over the three load-bearing
trait-range knobs to answer that, holding everything else fixed.

## Setup

- **Layout**: `tight_gradient` (the only chamber where v0.4 demonstrated
  phenotype expression).
- **Hyperparameters**: `exploration_noise=0.05`, 5 founders, 200 ticks,
  8 seeds (`1, 2, 3, 4, 5, 42, 100, 2024`).
- **Condition**: random-sampling only (no archetypes).
- **Independent variables**: three knobs in the load-bearing axes from v0.4:

| knob | levels | SPEC §8.1 master | meaning |
|---|---|---|---|
| `fear_max`   | {1.0, 1.5, 2.0}    | [0.0, 3.0]  | ceiling on `fear_sensitivity` range |
| `hunger_min` | {0.75, 1.0, 1.25}  | [0.25, 2.5] | floor on `hunger_pain_sensitivity` range |
| `risk_min`   | {0.25, 0.4, 0.55}  | [0.0, 1.0]  | floor on `risk_tolerance` range |

All other ranges (injury ceiling, pleasure floor, pain-tolerance floor,
plus all SPEC-default axes) match `permissive_trait_config()` from v0.5.
This isolates the three-axis grid from confounding range changes.

3 × 3 × 3 = **27 cells × 8 seeds = 216 runs**, plus the SPEC-default
baseline (1 cell × 8 seeds = 8 runs). Total: 224 runs, ~4 minutes wall
time. The v0.5 cell `(fear_max=1.5, hunger_min=1.0, risk_min=0.4)` is one
of the 27 cells, so v0.5 vs grid is a built-in comparison.

## Pre-registered viability rule

A cell qualifies iff **all four** hold:

1. `food_events > baseline.food_events`
2. `hazard_entries > baseline.hazard_entries`
3. `seeds_with_survivors >= 1` (cliff filter — at least one seed produces a
   founder alive at tick 200)
4. `seeds_with_any_starvation > 0` (diversity guard — not every seed full
   of survivors)

## Pre-registered failure→action mapping

- **0 cells qualify** → range-shifting alone insufficient; v0.6.5 explores
  distribution shape (Beta sampling) before continuing the ladder.
- **Multiple cells qualify** → primary score is `total_food_events`
  (highest wins). Tie-break: cell **closest to SPEC defaults** by
  Euclidean distance in the (fear_max, hunger_min, risk_min) space.
  Conservative-tightening rule.
- **Only the v0.5 cell qualifies** → v0.5 hand-tuning was a local optimum;
  promote and proceed.
- **A different cell qualifies more strongly** → adopt that cell as the
  v0.7 fixed config.

## Result — every cell qualifies

```
qualifiers: 27 / 27
winner:     f1.5-h1-r0.55  (food_events=11, distance-to-SPEC tie-break)
baseline:   food=0  haz=1  surv=0  starv=8/8
```

**The entire 27-cell zone is viable.** Every cell beats baseline on food
events and hazard entries, every cell produces ≥1 survivor seed, every
cell preserves diversity (starvation in 8/8 seeds). v0.5 was not a lucky
point — the harness is robust across this slice of the permissive zone.

### `food_events` heatmap (3 panels, one per `risk_min`)

The number in each cell is `total_food_events` across 8 seeds × 5 founders
= 40 random-traits population. Every cell here has `survivors=1` and
`starvation_seeds=8`.

```
risk_min = 0.25
                hunger=0.75   hunger=1.00   hunger=1.25
fear_max=1.0          8             8             8
fear_max=1.5          8             8             8
fear_max=2.0          4             4             4

risk_min = 0.40
                hunger=0.75   hunger=1.00   hunger=1.25
fear_max=1.0          8             8            11
fear_max=1.5          8             8 (v0.5)     8
fear_max=2.0          8             8             8

risk_min = 0.55
                hunger=0.75   hunger=1.00   hunger=1.25
fear_max=1.0          4             4             7
fear_max=1.5          8            11(*)        11
fear_max=2.0          8             8             8

(*) = winner per SPEC-distance tie-break
```

### `hazard_entries` heatmap (3 panels)

Hazard entries scale similarly but with more variance — some seeds enter
the hazard band repeatedly without finding food, so high hazard with low
food indicates "reckless but unlucky" populations.

```
risk_min = 0.25
                hunger=0.75   hunger=1.00   hunger=1.25
fear_max=1.0         22            22            22
fear_max=1.5         18            18            18
fear_max=2.0         22            22            22

risk_min = 0.40
                hunger=0.75   hunger=1.00   hunger=1.25
fear_max=1.0         24            22            19
fear_max=1.5         20            19 (v0.5)    19
fear_max=2.0         16            16            16

risk_min = 0.55
                hunger=0.75   hunger=1.00   hunger=1.25
fear_max=1.0         28            28            30
fear_max=1.5         23            24            24
fear_max=2.0         20            19            19
```

### Reading the panels

Three patterns are visible:

1. **`risk_min=0.55` produces the most hazard entries.** Expected:
   higher risk-tolerance floor lets more agents push into hazard cells.
2. **`fear_max=1.0` is the bravest column.** Lower fear ceiling means
   even the most fearful agents can't be paralyzed. Pairs with high
   `risk_min` to produce the highest hazard counts (e.g., `f1-r0.55`).
3. **Food events plateau around 8-11**, not monotonic in any single
   axis. The harness shows a "good-enough" plateau — once the trait
   floor/ceilings reach the permissive zone, additional permissiveness
   doesn't help much. There's a ceiling on how much pursuit the
   single-survivor seed can produce.

The food-event ceiling at 11 across multiple cells is the single survivor
seed (`seed=1`) producing slightly more eating events under different
trait rolls before death. **None of the 27 cells produce a second
surviving seed** — the 1/8 survival rate is the harness's limit on this
chamber under random sampling.

### Visual evidence — winner cell `f1.5-h1-r0.55`, seed 1, tick 100

```
___##****
___##.***
___##*..*
c__##***f  ← agents c (alive in safe) and f (alive in food zone)
___##****
___##****
```

Two living agents at tick 100: `c` in the safe zone column, `f` in the
food zone with three eaten food cells visible. The same survivor pattern
seen in v0.5's permissive cell — confirming the grid sweep is sampling a
real plateau, not noise.

## Decision

**Adopt `f1.5-h1-r0.55` as the v0.7 fixed trait config.** Per the
pre-registered failure mapping (multiple-qualifiers branch + tie-break
rule).

Rationale:

- **v0.5 was viable but suboptimal.** The v0.5 cell scored
  food_events=8; the winner scores 11. A 38% relative improvement on
  the primary score for a single-knob change (`risk_min` 0.4 → 0.55).
- **Closest to SPEC defaults among top scorers.** Three cells tied at
  food_events=11: `f1-h1.25-r0.4`, `f1.5-h1-r0.55`, `f1.5-h1.25-r0.55`.
  Of these, `f1.5-h1-r0.55` is closest to the SPEC corner
  (fear=3, hunger=0.25, risk=0) by Euclidean distance — the
  conservative-tightening rule.
- **Diversity is preserved.** 8/8 seeds still produced starvation, so
  the harness has not collapsed into "everyone Reckless."

We do **not** promote this to `core/traits.py` defaults yet. The same
v0.5 reasoning still holds: reproduction has not emerged under any of
the 27 cells (all `births = 0`). A trait config that doesn't sustain
lineage is incomplete. Add `tuned_default_trait_config()` (mapping the
winner) as an experiments fixture; v0.7 holds it fixed and sweeps
`ReproductionConfig`.

## What v0.6 confirms about the harness

1. **The v0.4 valence fix + v0.5 range direction is robust.** Across
   216 runs, every permissive variant produces qualifying populations.
   The harness is not balanced on a knife-edge.
2. **Food events plateau at ~11 across the permissive zone.** Improving
   beyond 11 in this chamber requires either a different layout (v0.9
   sensor expansion or chamber rescue) or a different policy (v0.8
   memory arm) — not more trait tuning.
3. **Birth emergence is the next bottleneck.** All 27 cells produce 0
   births. The energy threshold for `REPRODUCE` (default 70) sits above
   starting energy (60), and food-event count per agent is too low for
   most agents to climb above 70. v0.7 sweeps reproduction parameters.

## What changed

- [[src/hedonism_harness/experiments/trait_configs.py]] —
  `tuned_trait_config(*, fear_max, hunger_min, risk_min)` parametric
  factory + `cell_id()` helper.
- [[src/hedonism_harness/experiments/trait_grid.py]] (new) — 27-cell
  driver, four-criterion evaluator, SPEC-distance tie-break, winner
  selector, comparison.csv + winner.txt artifacts.
- [[tests/test_trait_grid.py]] (new) — 13 tests pinning the parametric
  factory, the four-criterion evaluator, the failure-mapping logic
  (no-qualifier / multi-qualifier-by-food / tie-break-by-distance), and
  a smoke that runs a 2-cell mini grid.

No changes to: `core/`, `policies/`, layouts, archetypes, valence,
sensors, or `ReproductionConfig`.

## Reproducing

```bash
uv run python -c "
from pathlib import Path
from hedonism_harness.experiments.trait_grid import run_trait_grid
run_trait_grid(
    seeds=[1, 2, 3, 4, 5, 42, 100, 2024],
    runs_root=Path('runs'),
    batch_id='fear-hunger-v0.6',
    n_ticks=200,
    n_founders=5,
    snapshot_tick=100,
    snapshot_seed=1,
)
"
```

Outputs in `runs/fear-hunger-v0.6/`:

```
fear-hunger-v0.6/
    comparison.csv             # baseline + 27 cell rows
    winner.txt                 # chosen cell + criterion details
    snapshots/
        {winner_cell_id}.txt
    baseline-spec-default/
        seed-{N}/...
    cells/
        {cell_id}/
            seed-{N}/...
```
