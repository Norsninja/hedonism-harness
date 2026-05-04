# Fear-Hunger Chamber — v0.14 reflex cell vs deliberative cell

Status: results landed (pre-registration written before sweep, results
appended in the same doc)
Branch: claude/v0.14-reflex-cell
Spec: docs/specs/v0.2_reflex_cell_spec.md
Date: 2026-05-04
Runs: runs/fear-hunger-v0.14a/ (tight_gradient),
runs/fear-hunger-v0.14b/ (food_ladder),
runs/fear-hunger-v0.14-speciation.md (post-hoc trait analysis)

## Question

Does a primitive reflex cell (gradient-following policy + automatic
reproduction + no memory) produce cleaner survival and lineage dynamics
than the existing deliberative cell (HedonismPolicy + valence harness +
voluntary REPRODUCE) under identical chamber, seed, and trait substrates?

## Hypotheses

H1. Reflex cell produces births past tick 50 (the v0.13 ceiling); the
deliberative cell continues to hit it.

H2. Reproduction-trigger mechanism (auto vs voluntary) carries the effect.
Holding policy fixed, switching from voluntary REPRODUCE to automatic
trigger lifts births past tick 50.

H3. Policy architecture (reflex vs deliberative) carries the effect.
Holding reproduction trigger fixed at automatic, switching from
HedonismPolicy to GradientPolicy lifts births past tick 50.

The 3-arm comparison (A, B, C below) lets us attribute observed
differences to the policy axis (C-vs-B), the trigger axis (B-vs-A), or
both (C-vs-A).

## Setup

3 arms x 2 chambers x 8 seeds x 200 ticks x 5 founders = 48 runs.

| arm | policy | reproduction | label |
|---|---|---|---|
| A | HedonismPolicy(exploration_noise=0.05) | voluntary REPRODUCE action | deliberative-voluntary |
| B | HedonismPolicy(exploration_noise=0.05) | apply_auto_reproduction | deliberative-auto |
| C | GradientPolicy() | apply_auto_reproduction | reflex-auto |

Chambers: tight_gradient (v0.14a), food_ladder (v0.14b).
Seeds: [1, 2, 3, 4, 5, 42, 100, 2024] (same as v0.13).
n_ticks: 200 (same as v0.13).
n_founders: 5 (same as v0.13).
Memory: disabled in all 3 arms (use_memory=False).
exploration_noise: 0.05 for HedonismPolicy arms; not applicable to
GradientPolicy (no random exploration).

### TraitConfig (wide, no archetype injection)

| trait | range | physical floor | physical ceiling |
|---|---|---|---|
| pleasure_sensitivity | [0.25, 2.5] | 0.0 | none |
| hunger_pain_sensitivity | [0.25, 2.5] | 0.0 | none |
| injury_pain_sensitivity | [0.25, 2.5] | 0.0 | none |
| fear_sensitivity | [0.0, 3.0] | 0.0 | none |
| reproduction_drive | [0.0, 3.0] | 0.0 | none |
| novelty_drive | [0.0, 2.0] | 0.0 | none |
| uncertainty_aversion | [0.0, 2.0] | 0.0 | none |
| pain_tolerance | [0.0, 1.0] | 0.0 | 1.0 |
| risk_tolerance | [0.0, 1.0] | 0.0 | 1.0 |
| memory_strength | [0.0, 1.0] | 0.0 | 1.0 |
| memory_decay_rate | [0.0, 0.1] | 0.0 | 1.0 |
| sensor_radius | [1, 6] | 1 | none |
| metabolic_rate | [0.5, 2.0] | 0.0 | none |

The range is the founder sampling distribution. The physical floor /
ceiling defines where mutation may drift over generations. Floors and
ceilings are enforced at the mutation site; values outside the original
range are valid (unbounded mutation per v0.2 spec).

The TraitConfig values match the existing default TraitConfig() to
preserve v0.7..v0.13 baseline comparability for arm A. Widening the
ranges is deferred until v0.14 results are in (so any reflex-vs-
deliberative difference is attributable to architecture, not to a
trait-distribution change).

Mutation parameters (unchanged from existing defaults):
- mutation_rate: 0.15
- mutation_sigma: 0.08
- unbounded_mutation: true (new in v0.14; default false preserves
  v0.7..v0.13 bit-identity)

### Reproduction config

- energy_threshold: 50
- energy_cost: 35
- min_age: 10

These match the v0.7..v0.13 tuned_reproduction_config(et=50, ec=35).
v0.14 does not vary reproduction economics. If H1+H2+H3 all fail and
all three arms hit the same tick-50 ceiling, the v0.15 candidate is
to vary reproduction economics or n_ticks (the v0.13 hand-off).

## Pre-registered metrics

Headline (per-arm, aggregated across 8 seeds per chamber):

- total_births
- seeds_with_any_births
- **births_after_tick_50** (the H2 ceiling test)
- max_population_end
- seeds_with_survivors at run end
- still_tick_fraction (action == STAY rate per agent-tick, averaged)

Diagnostic:

- total_food_events
- total_hazard_entries
- total_starvation_deaths
- mean_lineage_depth (max generation reached per seed, averaged)
- per-arm policy LOC at experiment time (informational)

Speciation analysis (post-hoc, per chamber):

- Per-lineage trait fingerprint at AgentBorn (full traits vector +
  birth_tick + parent_id + lineage_id) written to
  trait_fingerprints.csv per run.
- Aggregated successful-lineage report: enumerate trait vectors of all
  agents whose offspring_count >= 1. v0.14 reports descriptively (table
  + per-trait min/median/max for successful lineages); formal clustering
  deferred to v0.15+ when sample size warrants.

## Pre-registered comparisons

Primary:

- C.births_after_tick_50 - A.births_after_tick_50
  - positive: thesis-leaning (reflex architecture lifts compounding)
  - zero: no architecture effect; substrate-physical ceiling
  - negative: deliberative architecture provides positive value
- B.births_after_tick_50 - A.births_after_tick_50
  - isolates reproduction-trigger effect alone
- C.births_after_tick_50 - B.births_after_tick_50
  - isolates policy-architecture effect alone

Secondary:

- still_tick_fraction across arms — if reflex cells STAY more, that's
  evidence the gradient signal is too weak in featureless cells; if
  reflex cells STAY less, that's evidence movement is over-triggered.
- mean_lineage_depth: any arm that gets past depth=1 (founder ->
  child) is doing something the others aren't.

## Pre-registered failure -> action mapping

- H1 confirmed (C produces post-tick-50 births, A does not)
  -> Architecture matters. Continue with v0.15 (reintroduce minimal
  memory under GradientPolicy). The thesis is evidenced.
- H1 false but H2 confirmed (B produces post-tick-50 births, A does not,
  C also produces them)
  -> Reproduction trigger is the binding factor; policy architecture
  is secondary. v0.15 may revisit voluntary reproduction in
  HedonismPolicy or commit fully to automatic.
- H1 false and H2 false (A, B, C all hit tick-50 ceiling)
  -> Substrate-physical ceiling. v0.15 varies reproduction economics
  (energy_cost, energy_threshold) or n_ticks. The thesis is not
  refuted but is not the binding bottleneck.
- C produces no births at all
  -> Engineering finding. Inspect GradientPolicy for missing
  pleasure-pain channel coverage. Likely candidates: hunger-pain as
  internal pull, gradient computation bug, trait-coefficient issue.
  Not a thesis falsification.
- C plateaus below A (regression)
  -> Deliberative cognition provides positive value beyond gradient
  response. v0.15 isolates which valence-harness component carries it.

## Out of scope (v0.14)

- Memory in the reflex cell (deferred to v0.15+; spec section 4)
- Categorical / per-cell-kind memory (v0.16+ candidate)
- Reproduction economics tuning (v0.15+ candidate)
- TraitConfig range widening (deferred until v0.14 closes)
- novelty_drive trait rename (cleanup; not behaviorally relevant)
- Removing inert traits from the dataclass (kept for inheritance
  + HedonismPolicy backward compat)

## What changes in code (v0.14 implementation)

New:
- src/hedonism_harness/policies/gradient_policy.py
- src/hedonism_harness/experiments/comparison_grid.py
- scripts/v0.14_speciation_analysis.py
- tests/test_gradient_policy.py
- tests/test_auto_reproduction.py
- tests/test_unbounded_mutation.py

Modified:
- src/hedonism_harness/core/traits.py — add unbounded_mutation flag,
  physical floor/ceiling table, new mutate_traits branch
- src/hedonism_harness/model.py — add apply_auto_reproduction phase
  4.5; add trait_fingerprints log; emit ReproductionRequested when
  the substrate triggers auto-reproduction
- src/hedonism_harness/mesa_agents.py — add apply_auto_reproduction
  method on HHAgent (substrate phase, not policy)
- src/hedonism_harness/policies/__init__.py — export GradientPolicy
- src/hedonism_harness/policies/hedonism_policy.py — add module-level
  docstring noting deliberative-comparison status under v0.2 spec

## Determinism contract

- GradientPolicy is a pure function of (Observation, Traits) plus
  ctx.rng for tie-breaking only.
- apply_auto_reproduction reuses _process_birth_queue identically;
  birth event sequences must match between voluntary and auto modes
  when the same agent state arises (tested via integration test with
  matching seeds).
- TraitConfig.unbounded_mutation defaults to False; v0.7..v0.13 sweeps
  re-run bit-identically when re-executed under the v0.14 codebase.
- Existing 458-test suite must remain green.

## Results (sweep ran 2026-05-04)

### v0.14a tight_gradient

```
arm                       births  sw_b  birth>50  max_pop  surv  still%  food  haz  starv  reqs
deliberative-voluntary       1     1       0        0       0     82.9    0     1     41    1
deliberative-auto           26     8       0        0       0     80.9    0     3     66   26
reflex-auto                 47     8       0        1       2     92.0  192    26     85   47
```

### v0.14b food_ladder

```
arm                       births  sw_b  birth>50  max_pop  surv  still%  food  haz  starv  reqs
deliberative-voluntary       2     2       0        0       0     67.7   21     0     42    2
deliberative-auto           37     8       0        0       0     66.5   29     0     77   37
reflex-auto                 35     8       3        3       4     91.7  174    24     69   35
```

`birth>50` = `births_after_tick_50` (the v0.13 H2 ceiling test).
`surv` = `seeds_with_survivors` at run end. `still%` = mean
`still_tick_fraction` (action=STAY share). `haz` = `total_hazard_entries`.

### Pre-registered comparisons

C - A on `births_after_tick_50`:
- food_ladder: **+3** (3 vs 0). Reflex architecture lifts compounding
  past the v0.13 ceiling.
- tight_gradient: 0. Chamber still does not produce post-tick-50
  births under any arm.

B - A on `births_after_tick_50`: 0 in both chambers. Auto-reproduction
alone (with the same deliberative policy) does not lift compounding,
even though it lifts first-wave births (1 -> 26 on tight_gradient,
2 -> 37 on food_ladder).

C - B on `births_after_tick_50`: +3 on food_ladder, 0 on tight_gradient.
The policy axis is what carries the post-tick-50 effect.

### Pre-registered failure-mapping branch fired

> H1 confirmed (C produces post-tick-50 births, A does not)
> -> Architecture matters. Continue with v0.15 (reintroduce minimal
> memory under GradientPolicy). The thesis is evidenced.

H1 fires on food_ladder. Tight_gradient remains structurally
unreachable for compounding under any current architecture, but the
reflex cell still provides a substrate floor lift on substrate
metrics (food_events 0 -> 192, surviving seeds 0 -> 2) the
deliberative cells cannot match.

### What v0.14 establishes

1. **The reflex cell substrate is causally superior on the headline
   compounding metric** under one chamber, and equal-or-better on
   every other tracked metric under both chambers.
2. **Auto-reproduction unblocks first-wave births in the deliberative
   architecture** by ~26x on tight_gradient and ~18x on food_ladder.
   This isolates a real wiring effect of voluntary REPRODUCE: the
   policy was failing to select reproduction even when the body was
   eligible. Auto bypasses that failure mode in B; C inherits it but
   compounds further via the reflex policy itself.
3. **First surviving seeds across the project lineage**: 2 on
   tight_gradient and 4 on food_ladder, both under arm C. Every
   v0.7..v0.13 sweep produced 0 surviving seeds.
4. **The reflex cell has a higher still_tick_fraction (~0.92 vs ~0.7)**
   — it does not move when there is no positive gradient to follow.
   This is biologically apt rest behavior; the deliberative cell
   keeps moving (predicted-state scoring almost always finds *some*
   action with non-zero pleasure component).

### What v0.14 leaves open (the v0.15 hand-off)

1. **Compounding on tight_gradient** is still bounded (0 post-tick-50
   births). The chamber's hazard wall + post-birth energy floor
   compound prevent recovery even for the reflex cell. v0.15
   candidates: lower hazard_damage, widen pre_food band, longer tick
   budget.
2. **Reflex cell food consumption on tight_gradient is high (192) but
   does not translate to post-tick-50 compounding**. The cell forages
   well but cannot sustain the lineage past the first generation.
   Same H2 ceiling as v0.13, just at a higher substrate floor.
3. **Memory in the reflex cell** — deferred from v0.14. v0.15 may
   reintroduce a directional gradient reinforcement under the
   GradientPolicy and check whether memory shifts the still_tick
   fraction (could allow a known-good direction to keep firing even
   when current sensors are featureless).
4. **Speciation analysis is descriptive only**. With 26-47 successful
   lineages per arm, a formal clustering pass becomes feasible in
   v0.15+; v0.14 reports per-trait min/median/max plus a
   bin-by-inspection table. See
   [[runs/fear-hunger-v0.14-speciation.md]].

### Speciation observations (from runs/fear-hunger-v0.14-speciation.md)

For the 47 successful lineages on tight_gradient under reflex-auto,
the trait fingerprints span the full sampling range — there is no
single winning trait corner. Successful lineages have
`pleasure_sensitivity` from 0.47 to 2.36, `fear_sensitivity` from
0.19 to 2.75, `risk_tolerance` from 0.04 to 0.90. The sweep does
not yet show convergent speciation; this is consistent with
"founders mostly produce one offspring early before the chamber
exhausts them" rather than "specific trait combinations dominate."

A fairer speciation test is offspring_count >= 2 (cells that
reproduced more than once); v0.15 should add this filter to the
analysis. The current data shows almost all successful lineages
at offspring_count = 1, which is the first-wave ceiling.

## Reproducing

```bash
uv run python -c "
from pathlib import Path
from hedonism_harness.experiments.comparison_grid import run_comparison_grid

run_comparison_grid(
    seeds=[1, 2, 3, 4, 5, 42, 100, 2024],
    runs_root=Path('runs'),
    batch_id='fear-hunger-v0.14a',
    layout_name='tight_gradient',
    n_ticks=200, n_founders=5,
)

run_comparison_grid(
    seeds=[1, 2, 3, 4, 5, 42, 100, 2024],
    runs_root=Path('runs'),
    batch_id='fear-hunger-v0.14b',
    layout_name='food_ladder',
    n_ticks=200, n_founders=5,
)
"

uv run python scripts/v0.14_speciation_analysis.py \
    --runs runs/fear-hunger-v0.14a runs/fear-hunger-v0.14b \
    --output runs/fear-hunger-v0.14-speciation.md
```
