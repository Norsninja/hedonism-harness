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

## References

- [[docs/experiments/fear_hunger_v0.15.md]] — v0.15 results;
  `food_events` saturation finding and the substrate-vs-memory-tier
  fork.
- [[docs/experiments/fear_hunger_v0.14.md]] — v0.14 baseline; the
  "post-birth energy floor still binding" watch-out at the bottom.
- [[docs/specs/v0.2_reflex_cell_spec.md]] §"Comparison framework" —
  the substrate axis the v0.2 spec named but did not exercise.
