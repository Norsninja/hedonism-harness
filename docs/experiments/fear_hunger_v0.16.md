# v0.16 — reproduction-economics substrate variants under reflex baseline

**Status:** pre-registration; not yet executed.
**Date:** 2026-05-04
**Branch:** `claude/v0.16-energy-economics`
**Predecessors:** v0.14 (reflex cell, first compounding) and v0.15
(chemotaxis-tier scalar memory, no compounding lift).
**Spec:** [[docs/specs/v0.2_reflex_cell_spec.md]] §"Comparison framework"
(substrate axis).

## Question

Is the v0.14/v0.15 H2 ceiling (`births_after_tick_50` capped at 3 on
food_ladder, 0 on tight_gradient) imposed by the **reproduction
economics** of the substrate — specifically the parent's post-birth
energy retention — rather than by policy architecture or memory tier?
v0.15 ruled out cell-tier memory as the lifter. v0.16 tests the
cheapest substrate axis: `energy_cost`.

## Background

v0.15 found:

- `food_events` identical across all v0.15 arms on both chambers
  (192 / 174). The chamber's consumable food supply is fixed and the
  v0.14 reflex cell already saturates it.
- Chemotaxis cells produced +15 total births on food_ladder (≈+38%)
  but the same `births_after_tick_50` (3) and same surviving seeds
  (4/8). More first-generation reproductions; no compounding.
- The v0.14 watch-out flagged "post-birth energy floor still binding."
  Parents reproduce at `energy >= energy_threshold`, lose
  `energy_cost` to the child, retain `(energy_at_birth - energy_cost)`
  post-birth, and then must forage to refill. If that residual is
  below the survival floor for the time-to-next-food, the parent dies
  before re-reproducing. Children inherit `offspring_start_energy`
  and face the same regime.

The v0.14/v0.15 baseline uses
`tuned_reproduction_config(energy_threshold=50.0, energy_cost=35.0)`.
A parent at exactly threshold retains 15 post-birth — a tight margin.

## Hypothesis

The **post-birth energy floor** is the binding constraint on
compounding. Lowering `energy_cost` raises the parent's residual
energy after each birth, which should:

- extend the parent's post-birth lifetime;
- enable second / third / fourth births from the same parent;
- raise `births_after_tick_50` if the binding constraint is indeed
  energy economics.

If `energy_cost` does NOT lift `births_after_tick_50`, the binding
constraint is elsewhere (chamber geometry, food respawn, population
dynamics), and v0.17 targets one of those instead.

## Mechanism

No new mechanism. v0.14 reflex cell, no scalar memory, auto-
reproduction substrate phase, identical chambers. Only
`reproduction_config.energy_cost` varies across cells.

## Arms

Single-arm structure: every cell uses **reflex-baseline** (the v0.14
reflex-auto policy, no scalar memory). Arms differ only in
`energy_cost`.

| arm | energy_threshold | energy_cost | parent retains | label |
|---|---:|---:|---:|---|
| A | 50 | 35 | 15 | cost-35 (baseline; reproduces v0.14/v0.15 arm A) |
| B | 50 | 25 | 25 | cost-25 |
| C | 50 | 15 | 35 | cost-15 |

`energy_threshold` held at 50 (v0.14/v0.15 baseline) so the same
threshold-crossing dynamics apply; only the post-birth retention
differs. `offspring_start_energy` (30, default) and `min_age` (default
2 in v0.14 layouts) held constant.

Three energy-cost variants × two chambers × eight seeds = 48 runs.
Same scale as v0.14 / v0.15.

## Pre-registered hypotheses

- **H1.** `births_after_tick_50` on food_ladder is monotone in
  decreasing `energy_cost`. C > B > A. Lifts of +1 to +N at C-A would
  be the substrate-economics signal.
- **H2.** `births_after_tick_50` on tight_gradient lifts off zero
  under at least one of B / C. The v0.14/v0.15 ceiling on
  tight_gradient is hard zero across every arm; any non-zero lift
  here is meaningful.
- **H3.** `seeds_with_survivors` rises monotone with decreasing
  `energy_cost`. Parents that retain more energy survive past their
  first birth into the next forage cycle.
- **H4.** `total_food_events` rises modestly under B / C. With more
  surviving foragers (parents + post-tick-50 children), more food
  cells get visited and consumed.
- **H5.** `total_births` rises monotone with decreasing `energy_cost`
  on both chambers — direct consequence of compounding.
- **H6.** `still_tick_fraction` is roughly invariant across arms
  (substrate-economics changes do not modify the policy's STAY
  pattern; they affect downstream survival).

## Decision rules

- **C > A on `births_after_tick_50` for at least one chamber.**
  Reproduction economics is a load-bearing constraint. v0.17 picks an
  energy_cost in the productive range and re-runs the v0.15
  3-arm comparison with the lifted ceiling — re-tests whether
  chemotaxis adds value once the substrate is tuned. The chemotaxis
  cell's foraging gain (+15 births on food_ladder under v0.15 C) may
  translate into compounding if the post-birth survival is not
  the bottleneck.

- **C ≈ A across both chambers.** Reproduction economics is **not**
  the binding constraint. v0.17 targets chamber geometry: food_density,
  food_value, food respawn, hazard wall width, chamber dimensions.

- **C < A (regression).** Lower energy_cost induces faster reproduction
  but offspring inherit too little energy to survive their first
  forage cycle. Investigate `offspring_start_energy` (currently 30)
  and consider it as the next axis.

- **H2 fires (tight_gradient lifts off zero) but H1 does not (food_ladder
  flat).** The two chambers have different binding constraints. v0.17
  decouples and runs per-chamber tuning.

## Headline metrics

Same shape as v0.14 / v0.15:

- `total_births`
- `seeds_with_any_births`
- `births_after_tick_50` — the H2 ceiling test.
- `seeds_with_survivors` at run end.
- `still_tick_fraction`.
- `total_food_events`, `hazard_entries`, `starvation_deaths`,
  `reproduction_requests`.

New v0.16 instrumentation:

- **`mean_births_per_parent`** — `total_births / total_distinct_parents`.
  A direct measure of compounding. v0.14/v0.15: ≈1 (every parent
  reproduces once and dies); compounding shows as values > 1.
- **`mean_post_birth_lifespan_ticks`** — distribution of "ticks
  between a parent's first and last birth, or first birth and death."
  Telemetry for the post-birth energy floor question.

## Out of scope (v0.16)

- Chamber geometry variants (`hazard_x_max - hazard_x_min`,
  food_density, chamber dimensions) — deferred to v0.17 if H1/H2 fail.
- `offspring_start_energy` sweep — deferred to v0.17 if C < A.
- `min_age` and `max_energy` variants.
- Food respawn / regrowth — deferred (largest engineering surface).
- ScalarMemory under varied energy_cost — deferred to a v0.17
  re-comparison if the ceiling lifts.
- Multi-cell-tier directional EMA — deferred until the substrate
  question is settled.
- HedonismPolicy comparisons — quarantined per v0.2 spec.

## Implementation notes

### File-level changes

- Modify: `src/hedonism_harness/experiments/comparison_grid.py` —
  extend `Arm` with optional `energy_cost: float | None = None` and
  `energy_threshold: float | None = None` overrides; thread to
  `tuned_reproduction_config` in `_run_one_arm_seed`. Default `None`
  preserves v0.14/v0.15 behavior (uses `FIXED_ENERGY_COST=35.0`,
  `FIXED_ENERGY_THRESHOLD=50.0`). Add `V0_16_ARMS` tuple of three
  reflex-baseline arms with `energy_cost ∈ {35, 25, 15}`.
- Modify: `src/hedonism_harness/experiments/comparison_grid.py` —
  extend `RunDiagnostics` with the per-parent telemetry fields above.
- New: `tests/test_comparison_grid_energy_overrides.py` — verify
  `energy_cost`/`energy_threshold` overrides flow into the model's
  `reproduction_config` and that the existing arms (no override)
  remain bit-identical.
- Documented: `docs/experiments/fear_hunger_v0.16.md` (this doc;
  results appended after the sweep).

### Determinism contract

- Arm A (`energy_cost=35`) reproduces v0.15 reflex-baseline and v0.14
  reflex-auto bit-identically against current code (the same triple
  `(total_births, births_after_tick_50, seeds_with_survivors)` per
  seed and chamber).
- Override defaults are `None`. The existing `V0_15_ARMS` and
  v0.14 `ARMS` produce identical sweep outputs after the v0.16 changes.

### LOC estimate

- `comparison_grid.py` Arm extension + diagnostics: ~50 LOC.
- New tests: ~80 LOC.
- This doc: ~200 LOC.

Total v0.16 implementation: ~330 LOC. Smaller than v0.15.

## Results (executed 2026-05-04)

Three arms × two chambers × eight seeds × 200 ticks × 5 founders = 48
runs. Single policy (reflex-baseline, no scalar memory). All other
substrate parameters held at v0.14 / v0.15 values.

### v0.16a tight_gradient

| arm | births | birth>50 | survivors | parents | births/parent | mean_post_birth_lifespan | food | still% |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| cost-35 (A baseline) | 47 | 0 | 2/8 | 23 | 2.04 | 64.2 | 192 | 93.6 |
| cost-25 (B) | 64 | 0 | 1/8 | 28 | 2.29 | 68.5 | 192 | 94.0 |
| cost-15 (C) | 74 | 0 | 2/8 | 24 | 3.08 | 86.2 | 192 | 94.4 |

Monotone in decreasing cost: total_births +57% (47 → 74),
mean_births_per_parent +51% (2.04 → 3.08), mean_post_birth_lifespan
+34% (64.2 → 86.2). **`births_after_tick_50` is hard zero under every
cost.** `food_events` identical across arms (192).

### v0.16b food_ladder

| arm | births | birth>50 | survivors | parents | births/parent | mean_post_birth_lifespan | food | still% |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| cost-35 (A baseline) | 39 | 3 | 4/8 | 27 | 1.44 | 48.6 | 174 | 92.8 |
| cost-25 (B) | 46 | 4 | 4/8 | 27 | 1.70 | 62.6 | 174 | 93.2 |
| cost-15 (C) | 55 | 4 | 4/8 | 28 | 1.96 | 81.5 | 174 | 93.9 |

Monotone in decreasing cost: total_births +41% (39 → 55),
mean_births_per_parent +36% (1.44 → 1.96), mean_post_birth_lifespan
+68% (48.6 → 81.5). **`births_after_tick_50` lifts 3 → 4 (cost-25
and cost-15);** monotone but only +1 absolute event on n=8 — within
seed noise. `seeds_with_survivors` flat at 4/8 across all costs.
`food_events` identical (174).

### Hypotheses → outcomes

- **H1.** `births_after_tick_50` monotone-decreasing in `energy_cost`
  on food_ladder. **Weakly confirmed.** 3 → 4 → 4 (monotone but +1
  absolute; consistent with H1 being directionally correct but the
  effect size small).
- **H2.** `births_after_tick_50` lifts off zero on tight_gradient
  under at least one of B / C. **Falsified.** All three arms remain
  at 0.
- **H3.** `seeds_with_survivors` rises monotone with decreasing
  `energy_cost`. **Falsified.** food_ladder is flat at 4/8 across
  all costs; tight_gradient bounces 2/1/2 (no monotone trend).
- **H4.** `total_food_events` rises modestly under B / C.
  **Falsified.** food_events is identical across all arms (192 /
  174). The chamber's food supply is a hard ceiling.
- **H5.** `total_births` rises monotone with decreasing `energy_cost`
  on both chambers. **Confirmed strongly.** +57% on tight_gradient,
  +41% on food_ladder.
- **H6.** `still_tick_fraction` roughly invariant across arms.
  **Confirmed within ±0.8 pp** on tight_gradient (93.6/94.0/94.4) and
  food_ladder (92.8/93.2/93.9).

### Headline finding

**Reproduction economics is a real lever for compounding metrics —
but it is not the binding constraint on the H2 ceiling.**

The per-parent telemetry tells a clean substrate-economics story.
Lower `energy_cost` raises `mean_births_per_parent` from ~2 to ~3 on
tight_gradient and from ~1.4 to ~2 on food_ladder. Post-birth
lifespan rises 34-68%. Total births rise 41-57%. These all confirm
H5 cleanly and align with the "post-birth energy floor" hypothesis:
parents that retain more energy after each birth do produce more
births before dying.

But the **headline metric (births_after_tick_50)** does **not** lift
proportionally. tight_gradient stays at hard zero under any cost.
food_ladder lifts only 3 → 4 — within seed noise on n=8. And critically,
**`seeds_with_survivors` is flat across all costs** on both chambers
(food_ladder 4/8, tight_gradient ~1-2/8). Lineages still die out at the
same rate; parents just have more births before they do.

The v0.15 observation was: "children reproduce-and-die without
grandchildren." v0.16 confirms this pattern is **not** primarily about
the parent's post-birth energy. It is about the children themselves
not surviving long enough to reproduce — likely an
`offspring_start_energy` issue (children spawn with 30 energy in a
chamber where adult parents struggle), or a population-pressure issue
where children compete for the same fixed food supply, or a chamber
geometry issue specific to tight_gradient's hazard wall.

### Decision rule fired (per pre-reg)

The pre-reg's branches resolve as follows:

> **C ≈ A across both chambers** — *partial.* total_births clearly
> diverge (C > A by 41-57%), and per-parent compounding diverges
> strongly. But the headline ceiling metric `births_after_tick_50` is
> nearly flat. We treat this as **economics is load-bearing for
> per-parent productivity but not for lineage survival**.

> **H2 fires (tight_gradient lifts off zero) but H1 does not** —
> *false in both directions.* tight_gradient does NOT lift; food_ladder
> lifts only marginally.

The v0.17 recommendation in the pre-reg ("substrate variants if
economics doesn't lift the ceiling") gains a sharper question:
**why are children dying before reproduction?**

### Data points worth flagging for v0.17

- **Children are the bottleneck, not parents.** v0.16's per-parent
  telemetry shows parents are doing fine — they have multiple births
  and live ~80 ticks post-birth at low cost. But survivors and
  post-tick-50 births don't scale with this. The dying agents are
  the children.
- **`offspring_start_energy = 30` is a candidate axis.** Children
  spawn with 30 energy in a chamber where the food cells deliver
  ~20 each. A child has ~15 ticks of metabolism before starvation;
  if no food is reachable in that window, the child dies before
  contributing.
- **`food_events` identical across all costs (192 / 174).** Same
  observation as v0.15 — chamber food supply is a static ceiling that
  no economic intervention can move. Worth verifying via the
  food_ladder layout's total food count vs the n_ticks * food respawn
  rate (if any).
- **tight_gradient's hard zero on `births_after_tick_50`** is now
  three consecutive experiments deep (v0.14, v0.15, v0.16). The
  hazard wall geometry is the only candidate left untested. v0.17
  should sweep `hazard_x_max - hazard_x_min` and
  `hazard_damage_default` on tight_gradient under the cheapest arm
  (cost-15).
- **mean_post_birth_lifespan +68% on food_ladder, +34% on
  tight_gradient.** The food_ladder cells reach much further into
  post-birth lifespan with cheap reproduction (81.5 ticks). On
  tight_gradient the gain is weaker; the hazard wall is killing
  parents earlier even before children become an issue.

### Recommendation for v0.17

Two parallel axes, each cheap:

1. **`offspring_start_energy` sweep** under reflex-baseline + cost-15
   (the v0.16 best). 3 values × 2 chambers × 8 seeds = 48 runs. Tests
   whether child survival is the binding constraint on lineage
   compounding. Most likely to lift `births_after_tick_50` if true.

2. **`tight_gradient_layout` geometry sweep** (hazard wall width,
   hazard damage). Tests whether tight_gradient's hard zero is
   structural. Single-chamber, narrow.

Run them in series, not parallel — (1) is more likely to lift the
ceiling per the v0.15/v0.16 pattern. If (1) lifts compounding under
both chambers, geometry is secondary. If (1) doesn't lift, (2) is
next.

### Determinism note

Arm cost-35 reproduces v0.15 reflex-baseline bit-identically on
`total_births`, `births_after_tick_50`, `seeds_with_survivors`, and
`total_food_events`:

- tight_gradient: 47 / 0 / 2 / 192 (matches v0.15 reflex-baseline).
- food_ladder: 39 / 3 / 4 / 174 (matches v0.15 reflex-baseline on
  current code; the v0.14-doc-published 35 / 91.7 mismatch flagged in
  v0.15 §Determinism note still stands).

`still_tick_fraction` differs by ~1.4 pp (cost-35: 92.8% vs v0.15
reflex-baseline 91.4% on food_ladder). This is an **instrumentation
change in v0.16's `_read_run_diagnostics`**, not a simulation change.
v0.14/v0.15 incidentally counted `AgentBorn` (pre-threshold) and
`AgentDied` events as "other action ticks" via the catch-all `else`
branch; v0.16 dispatches them explicitly to extract `parent_id` /
`agent_id` for per-parent telemetry, removing them from the action-
tick denominator. The change is semantically cleaner (births and
deaths are not actions) but breaks `still_tick_fraction` parity with
v0.15 / v0.14 published numbers. The simulation itself is unchanged;
the bookkeeping bound to RunDiagnostics shifted.

## References

- [[docs/experiments/fear_hunger_v0.15.md]] — v0.15 results;
  `food_events` saturation finding and the substrate-vs-memory-tier
  fork.
- [[docs/experiments/fear_hunger_v0.14.md]] — v0.14 baseline; the
  "post-birth energy floor still binding" watch-out at the bottom.
- [[docs/specs/v0.2_reflex_cell_spec.md]] §"Comparison framework" —
  the substrate axis the v0.2 spec named but did not exercise.
