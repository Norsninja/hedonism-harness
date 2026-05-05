# v0.28 — food_ladder w=0.75 trajectory diagnostic: routing flip, population artefact, or geometry interaction?

**Status:** pre-registration; not yet executed.
**Date:** 2026-05-05
**Branch:** `claude/v0.28-food-ladder-trajectory-diagnostic`
**Predecessors:** v0.21 (chamber-asymmetric influx frontier at hzd=8),
v0.22 (hazard sweep on food_ladder under transfer + influx=1.0;
recycling-as-net-tax confirmed), v0.23 (chamber-dependent hazard sign),
v0.24 (population-governor reading falsified; pool-exhaustion-timing
substituted; `population_dynamics` library introduced), v0.25
(hazard × influx sweep — tight interior optimum at h=8), v0.26
(perception-vs-damage decoupling 2×2 — Reading A confirmed; avoidance
load-bearing on both chambers), v0.27 (avoidance-weight frontier on
both chambers — both chambers exhibit interior optima; food_ladder
w*=0.5 strong / +6 b>50 vs w=1.0; tight w*=0.75 weak / +2 b>50;
**food_ladder b>50 dips to 89 at w=0.75** — flagged in the v0.27 doc
as "aggregate large enough to flag, not a stable regime").
**Spec:** [[docs/specs/v0.2_reflex_cell_spec.md]] §"Comparison framework"
(substrate axis).

## Question

v0.27 measured the avoidance-weight axis at five points on food_ladder:
b>50 = 88 / 97 / 98 / **89** / 92 across w ∈ {0.0, 0.25, 0.5, 0.75, 1.0}.
The w=0.75 cell is **9 births below w=0.5 and 3 below w=1.0**, breaking
monotonicity by an aggregate margin large enough to flag but not large
enough to call a stable regime — three qualitatively different
mechanisms could produce it:

(A) **Routing-threshold flip.** At w=0.75 the avoidance-vs-food pull
balance crosses some threshold and a subset of seeds reroute through
a worse food_ladder corridor (longer, more energy-costly, or
food-scarcer). The signature is **per-seed bimodality**: some seeds
behave like w=0.5, others behave qualitatively differently and drag
the mean down. Routing observables (hazard entries, food-consumption
distribution by location-band) should differ between the two seed
subgroups at w=0.75 specifically, not at w=0.5 or w=1.0.

(B) **Population-dynamics artefact.** A small number of seeds suffer a
mid-run crash (population dips below the late-window compounding
threshold) at w=0.75 specifically. The signature is **per-seed
trajectory divergence**: one or two seeds at w=0.75 show a sharp
late-window population drop or earlier `pool_birth_denied` onset,
while the same seeds at w=0.5 and w=1.0 do not. Mean is dragged by
those tail seeds.

(C) **Chamber-geometry interaction.** At w=0.75 the time-resolved
balance of food consumption vs hazard exposure shifts uniformly
across seeds — every seed runs a slightly worse trajectory at
w=0.75, with no per-seed bimodality and no tail crashes. The
signature is **uniform per-seed degradation**: all 8 seeds show a
small but consistent b>50 drop at w=0.75 vs w=0.5 / w=1.0,
correlated with shifted per-tick food / hazard / birth bands.

Mechanism (A) and (B) are seed-level findings (the dip is real but
narrow); mechanism (C) is the broadest possible reading (the dip is
real and population-wide). v0.28 discriminates them by paired
seed-level inspection across the **same 8 seeds (1..8)** at
w ∈ {0.5, 0.75, 1.0}.

## What this slice tests, and what it does NOT test

### Tests

- **Whether the v0.27 food_ladder w=0.75 b>50=89 dip is a per-seed
  bimodal effect (mechanism A), a tail-seed crash (mechanism B), a
  uniform population-wide effect (mechanism C), or none of the above
  (no clean signature — the dip is statistical noise that aggregated
  unfortunately).**
- **Whether routing observables (hazard entries, food consumption,
  birth-tick distribution) shift in a tick-band-resolved or
  location-resolved way at w=0.75 vs w=0.5 / w=1.0** on the SAME
  seeds.
- **Whether pool-pressure timing (first `PoolBirthDenied` tick,
  count of `PoolBirthDenied` per 50-tick band) shifts at w=0.75
  vs neighbors.**
- **Determinism of the v0.27 events.jsonl artifacts** — re-loading
  the on-disk events for w ∈ {0.5, 0.75, 1.0} reproduces the v0.27
  aggregate b>50 / hazard_entries / injury_deaths exactly.

### Does NOT test

- **No new sweep is mandatory.** The 24 runs needed (3 weights × 8
  seeds, food_ladder only) are already on disk in
  `runs/fear-hunger-v0.27-food_ladder/arms/hzd8-avd0.{50,75,1.00}/seed-{1..8}/events.jsonl`.
  v0.28 is purely an analysis on existing artifacts.
- **No tight-chamber inspection.** v0.27's tight w*=0.75 finding
  was weak (+2 births, exactly meeting noise threshold) — diagnosing
  it would require a different kind of analysis (saturation vs
  interior optimum) and is out of scope.
- **No additional weights.** v0.28 inspects only w ∈ {0.5, 0.75, 1.0}.
  w ∈ {0.0, 0.25} are anchors of the monotone-rising part of the
  curve; the dip lives between w=0.5 and w=1.0.
- **No new chambers.** food_ladder only.
- **No new seeds.** Same 8 seeds (1..8) as v0.21..v0.27. The handoff
  flagged seeds 9..16 as a possible reproducibility test if the
  diagnostic is inconclusive — out of scope for the pre-reg, may be
  added as a follow-up sweep.
- **No new mechanics.** No GradientPolicy changes, no new world
  layers, no Reading B substrate seam, no heritability changes, no
  new event types.
- **No expansion of the (hazard, weight, influx) parameter grid.**
  Per the handoff watch-out: do NOT expand the grid until the dip
  is explained.
- **No long-window observation.** Same 200-tick window as v0.21..v0.27.
- **No per-tick pool-current trajectory.** `AgentDied` events do not
  carry the dying agent's residual energy, so pool inflow from
  death-residual recycling cannot be reconstructed per-tick from
  events alone. v0.28 uses `PoolBirthDenied` / `PoolRespawnDenied`
  tick events as the pool-pressure observable instead. The
  per-run `pool_min` aggregate (already on disk via the chamber
  result CSV) gives a coarse cross-seed signal.
- **No HedonismPolicy comparisons.** Quarantined per v0.2 spec.

### Deferred (v0.29+ candidates, conditional on v0.28 outcome)

- **Reproducibility test on seeds 9..16** at w ∈ {0.5, 0.75, 1.0} on
  food_ladder (~24 runs, ~5s) if the v0.28 diagnostic is inconclusive
  on the 1..8 seed set.
- **Finer weight grid** at w ∈ {0.6, 0.7, 0.75, 0.8, 0.9} on
  food_ladder if mechanism (A) fires and the threshold-flip
  hypothesis warrants narrowing the threshold location.
- **Influx × weight cross-product** if mechanism (C) fires (uniform
  population-wide degradation) — pool-exhaustion-timing dependence
  on influx may shift the optimum.
- **Joint (hazard, weight) characterisation on tight** at h ∈ {4, 12},
  w ∈ {0.5, 0.75, 1.0} — only after the food_ladder dip is explained.

## Conservation framing — unchanged from v0.20..v0.27

v0.28 introduces no new conservation contract. No mutations to
`world.py` / `body.py` / `model.py` / `gradient_policy.py` /
`fear_hunger_chamber.py`. The library extension to
`population_dynamics.py` is purely-functional event aggregation; it
adds no event types, no mutation, no determinism risk.

## Mechanism

**No new code paths in production.** v0.28 is a diagnostic on existing
events.jsonl artifacts. Two additions:

1. **Library extension** in
   [[src/hedonism_harness/experiments/population_dynamics.py]]:
   - **`EventBandTrajectory`** dataclass exposing per-tick aggregates
     for the events the v0.24 `PopulationTrajectory` does not already
     carry: `births_per_tick`, `food_events_per_tick`,
     `hazard_entries_per_tick`, `hazard_damage_per_tick`,
     `pool_birth_denied_per_tick`, `pool_respawn_denied_per_tick`.
     All `tuple[int, ...]` of length `n_ticks` (or `tuple[float, ...]`
     for `hazard_damage_per_tick`). `lifespans` and `population_at_tick`
     remain on `PopulationTrajectory` (no mutation of the v0.24
     dataclass).
   - **`load_event_band_trajectory(events_jsonl, n_ticks)`** —
     single-pass loader producing `EventBandTrajectory`.
   - **`bucket_by_window(per_tick, windows=STARVATION_WINDOWS)`** —
     re-uses v0.24's pre-committed 50-tick bands to bucket any
     per-tick series. (Generalises the v0.24 `aggregate_cell`
     internal logic into a pure helper.)

2. **Diagnostic driver** in
   [[scripts/v0.28_trajectory_diagnostic.py]]:
   - Loads `(seed, weight) -> (PopulationTrajectory,
     EventBandTrajectory)` for the 24 runs.
   - Computes the per-seed observables listed below.
   - Emits paired-seed comparison tables (per-seed b>50 across
     w ∈ {0.5, 0.75, 1.0}, paired-seed bimodality detector for
     mechanism A, paired-seed late-window population trajectory for
     mechanism B, paired-seed band-resolved aggregates for mechanism C).
   - Writes the diagnostic output as a markdown report under
     `runs/fear-hunger-v0.28-food_ladder/diagnostic.md` and
     appends a `## Results` section to this pre-reg.

The v0.20..v0.27 telemetry surface is sufficient. No new event types,
no chamber changes, no policy changes.

### Determinism — anchors

The v0.28 library extension is an additive read of events on disk.
Determinism is verified by **byte-identity reproduction of v0.27
aggregates** from the same events.jsonl files:

- For each of the 24 runs (3 weights × 8 seeds, food_ladder), the
  loaded `PopulationTrajectory` plus `EventBandTrajectory` reproduce
  the v0.27 chamber-result aggregates for `total_births`,
  `births_after_tick_50`, `total_food_events`,
  `total_hazard_entries`, `total_starvation_deaths`,
  `total_injury_deaths`, `total_pool_birth_denied`,
  `total_pool_respawn_denied` — summed across the 8 seeds at each
  weight, these must match the v0.27 results doc exactly. This is
  the v0.28 H7 halt condition.

The 24 events.jsonl files on disk are the ground truth; v0.28 does
not regenerate them.

## Observables — pre-committed before reading the data

For each of the 24 runs (8 seeds × 3 weights), v0.28 computes the
following per-seed observables from `events.jsonl`. Quantities marked
**(L)** come from the existing v0.24 library; **(N)** require the new
`EventBandTrajectory`.

### Per-seed scalar observables

- `b>50` per seed (sum of `AgentBorn` events with `tick > 50`). **(N)**
  Aggregates to v0.27's `births_after_tick_50` when summed across
  seeds.
- `total_births` per seed. **(N)**
- `tick_of_peak` per seed (argmax of `population_at_tick`). **(L)**
- `peak_population` per seed. **(L)**
- `mean_population_window(100, 199)` per seed (late-window mean). **(L)**
- `first_pool_birth_denied_tick` per seed (first tick with
  `PoolBirthDenied`; `None` if never). **(N)** Pool-pressure-onset
  proxy in lieu of `pool_min_tick`.
- `total_pool_birth_denied` per seed. **(N)**
- `total_food_events` per seed. **(N)**
- `total_hazard_entries` per seed. **(N)**
- `total_starvation_deaths` / `total_injury_deaths` per seed. **(L)**

### Per-seed band-resolved observables (50-tick windows from v0.24)

Bands: `0-49`, `50-99`, `100-149`, `150-199` (per
`population_dynamics.STARVATION_WINDOWS`).

- `births_per_band[seed][band]`. **(N)**
- `food_events_per_band[seed][band]`. **(N)**
- `hazard_entries_per_band[seed][band]`. **(N)**
- `starvation_deaths_per_band[seed][band]`. **(L → bucket_by_window)**
- `injury_deaths_per_band[seed][band]`. **(L → bucket_by_window)**
- `pool_birth_denied_per_band[seed][band]`. **(N)**

## Pre-registered hypotheses

Two-tier structure consistent with v0.15..v0.27: **strong-form** for
determinism + invariants, **cautious-form** for the substantive
mechanism prediction.

### Strong form (determinism + invariants)

- **H1.** For each of the 24 runs, the loaded `EventBandTrajectory`
  satisfies `sum(births_per_tick) == count(AgentBorn events)`,
  `sum(food_events_per_tick) == count(AteFood events)`,
  `sum(hazard_entries_per_tick) == count(HazardEntered events)`,
  `sum(pool_birth_denied_per_tick) == count(PoolBirthDenied events)`.
  Halt condition.
- **H2.** For each band-resolved per-seed observable X,
  `sum_over_bands(X) == sum_over_ticks(per_tick_X)` (the band
  aggregation is a partition of the 200-tick window). Halt condition.
- **H3.** `PopulationTrajectory` produced by
  `load_population_trajectory` is **byte-identical** before and after
  the v0.28 library extension (no mutation of v0.24 contract).
  Verified by re-running the v0.24 test suite against the new module.
  Halt condition.
- **H4.** v0.27 prior tests (test_comparison_grid_v0_27,
  test_population_dynamics from v0.24) all continue to pass after
  the v0.28 additions. Pure-additive guard. Halt condition.

### Cautious form (mechanism discrimination)

The decision is made on the **paired-seed b>50 vector** at
w ∈ {0.5, 0.75, 1.0} — eight (b50_at_0.5, b50_at_0.75, b50_at_1.0)
triples, one per seed. Pre-committed signatures:

- **H5 (mechanism A — routing-threshold flip).** **FIRES iff** the
  per-seed `b50_at_0.75 - b50_at_0.5` deltas are **bimodal**: at
  least 2 seeds show a delta ≤ −5 (a "flipped" subgroup, b>50 collapses
  by ≥ 5 births at w=0.75) AND at least 4 seeds show a delta ≥ −1
  (an "unflipped" subgroup, b>50 stable or barely changed). The
  flipped subgroup must additionally exhibit at least one of:
    (a) `hazard_entries_per_band` shifted ≥ 30% in some band vs the
        unflipped subgroup at the same w=0.75, OR
    (b) `food_events_per_band` shifted ≥ 30% in some band vs the
        unflipped subgroup at the same w=0.75, OR
    (c) `births_per_band[late]` (band 150-199) collapsed by ≥ 50%
        in the flipped subgroup vs the unflipped subgroup.
  Mechanism reading: at w=0.75, a routing threshold flips for some
  seeds (initial-condition-dependent on which corridor is sampled
  first); the policy enters a worse equilibrium for those seeds.
- **H6 (mechanism B — tail-seed crash / population-dynamics
  artefact).** **FIRES iff** at most 2 seeds account for ≥ 80% of
  the aggregate b>50 deficit at w=0.75 vs w=0.5 (i.e., 2 seeds
  contribute ≥ 0.8 × (98 − 89) = 7.2 births of the deficit) AND
  those same seeds at w=0.5 and w=1.0 do NOT show a corresponding
  crash AND the crashing seeds exhibit:
    (a) `mean_population_window(100, 199)` at w=0.75 reduced by
        ≥ 30% vs the same seed at w=0.5, OR
    (b) `first_pool_birth_denied_tick` earlier by ≥ 30 ticks at
        w=0.75 vs the same seed at w=0.5.
  Mechanism reading: a small number of seeds happen to exhibit
  population-trajectory pathology specifically at w=0.75; not a
  systemic effect.
- **H7 (mechanism C — uniform population-wide degradation).**
  **FIRES iff** ≥ 6 of 8 seeds show `b50_at_0.75 - b50_at_0.5 < 0`
  AND the per-seed deltas are tightly clustered (max delta − min
  delta < 4 births) AND a per-band aggregate observable shifts
  uniformly (e.g., `food_events_per_band[late]` lower at w=0.75 than
  w=0.5 for ≥ 6 seeds).
  Mechanism reading: at w=0.75 the entire population trajectory
  shifts modestly worse — this would be a real but subtle
  chamber-geometry interaction.
- **H8 (no clean mechanism — statistical noise).** Default outcome
  if **none of H5/H6/H7 fires**. The dip aggregates from
  approximately-symmetric per-seed noise that happens to net negative
  at w=0.75 on the 1..8 seed set. Mechanism reading: the v0.27 doc's
  cautious framing ("aggregate large enough to flag, not a stable
  regime") was correct; reproducibility on seeds 9..16 would likely
  show a different aggregate at w=0.75. **No mechanism is privileged
  if H8 fires; v0.29 candidate is the seed-9..16 reproducibility
  test.**

H5, H6, H7 are designed to be **mutually exclusive** at the operational
level: H5 requires bimodality (large within-group variance); H7
requires tight clustering (small within-group variance); H6 requires
a small-tail concentration of the deficit (most seeds nearly identical
across w). At most one fires; if more than one fires the operational
definitions are at fault and the diagnostic must be re-evaluated.

### Anchor identity

- **H9 (24-run v0.27 aggregate reproduction).** Summing per-seed
  `total_births`, `b>50`, `total_food_events`, `total_hazard_entries`,
  `total_starvation_deaths`, `total_injury_deaths`,
  `total_pool_birth_denied` across the 8 seeds at each weight matches
  the v0.27 results-doc cells exactly:
    - w=0.50: births=154, b>50=98, food=685, haz=163, starv=81,
      inj=25, pool_blk=0
    - w=0.75: births=145, b>50=89, food=688, haz=145, starv=78,
      inj=20, pool_blk=6
    - w=1.00: births=143, b>50=92, food=674, haz=120, starv=77,
      inj=16, pool_blk=0
  Halt condition.

## Decision rules

- **H5 fires (routing flip).** Headline: the dip is a per-seed
  routing-threshold artefact. v0.29 candidate: finer weight grid
  around the threshold (w ∈ {0.6, 0.7, 0.75, 0.8, 0.9}); inspect
  the flipped seeds' agent trajectories around the threshold tick.
- **H6 fires (tail crash).** Headline: the dip is a 1-2-seed
  population-dynamics artefact specific to those seeds at w=0.75.
  v0.29 candidate: seeds 9..16 reproducibility test; if the dip is
  absent on a fresh seed stream the 1..8 result is sample-specific.
- **H7 fires (uniform degradation).** Headline: the dip is a real
  but subtle population-wide effect at w=0.75. v0.29 candidate:
  influx × weight cross-product to test pool-exhaustion-timing
  dependence; characterise the joint optimum.
- **H8 fires (no clean mechanism).** Headline: the dip is plausibly
  statistical noise; the v0.27 cautious framing stands. v0.29
  candidate: seeds 9..16 reproducibility test as the cleanest
  discrimination.
- **H1/H2 fail** (event-count or band-partition invariants violated).
  Halt; the library extension has a defect; the diagnostic cannot run.
- **H3 fails** (v0.24 contract mutated). Halt; revert the
  `population_dynamics.py` extension and re-introduce as a separate
  module.
- **H4 fails** (prior tests broken). Halt; the v0.28 additions broke
  a v0.27-or-earlier contract.
- **H9 fails** (aggregate reproduction). Halt; the events.jsonl on
  disk is not what the v0.27 chamber-result CSVs say it is, OR the
  loader has a defect — either is a halt.
- **More than one of H5/H6/H7 fires.** Halt and re-evaluate the
  operational definitions; the signatures should be mutually
  exclusive by construction.

## Out of scope (v0.28)

- **No new sweep** unless H8 fires AND the v0.29 reproducibility
  test is requested.
- **Influx variation, hazard intensity variation, weights > 1.0,
  long-window stability, pool-size sweep, reproduction efficiency
  variation, HedonismPolicy comparisons.** All deferred per
  v0.21..v0.27 framing.
- **Reading B substrate seam.** Out of scope.
- **Heritability / mutation distribution analysis.** Out of scope.
- **Per-agent trait-distribution diagnostics.** Out of scope.
  Available as a v0.29+ slice if the seed-level diagnostic motivates
  it (e.g., the flipped seeds in H5 have systematically different
  trait distributions).

## Implementation notes

### File-level changes

- **Modify (additive only):**
  [[src/hedonism_harness/experiments/population_dynamics.py]] — add
  `EventBandTrajectory` dataclass, `load_event_band_trajectory`
  loader, `bucket_by_window` helper. **No mutation of
  `PopulationTrajectory` or `load_population_trajectory`.** ~120 LOC.
- **New:** [[scripts/v0.28_trajectory_diagnostic.py]] — diagnostic
  driver. Loads 24 runs, computes per-seed observables, emits
  paired-seed comparison tables, evaluates H5/H6/H7/H8, writes
  diagnostic.md. ~180 LOC.
- **New:** `tests/test_trajectory_diagnostic_v0_28.py` —
  `EventBandTrajectory` shape; loader determinism on a synthetic
  events.jsonl fixture; `bucket_by_window` correctness; H1/H2
  invariants on a real v0.27 events.jsonl; H9 anchor identity on
  one of the 24 cells. ~200 LOC.
- **No changes** to `core/`, `model.py`,
  `experiments/fear_hunger_chamber.py`,
  `experiments/comparison_grid.py`,
  `policies/gradient_policy.py`,
  `policies/hedonism_policy.py`. No new arms, no new events.
- **Documented:** this file (`docs/experiments/fear_hunger_v0.28.md`);
  results appended after the diagnostic runs.

### Determinism contract

- `population_dynamics.PopulationTrajectory` and
  `load_population_trajectory` are byte-identical before and after
  v0.28 (additive-only).
- The v0.24 test suite continues to pass.
- The v0.27 test suite continues to pass.
- The 24 events.jsonl files on disk are not regenerated.

### Wall time estimate

24 events.jsonl files × single-pass aggregation. Each file is
~2,400 events on disk; loading + aggregating all 24 should take
< 1s. The diagnostic driver wall time is dominated by the markdown
emission, not the analysis.

### LOC estimate

- `experiments/population_dynamics.py`: +120 LOC.
- `scripts/v0.28_trajectory_diagnostic.py`: ~180 LOC.
- `tests/test_trajectory_diagnostic_v0_28.py`: ~200 LOC.
- This doc: ~430 LOC.

Total v0.28 implementation: ~930 LOC. Comparable to prior diagnostic
slices (v0.24 was ~700 LOC; v0.28 adds the band-aggregation surface
plus the per-seed paired-comparison driver). Tests should bring the
suite from 716 to ~735.

## References

- [[docs/experiments/fear_hunger_v0.27.md]] — v0.27 results;
  food_ladder w=0.75 dip flagged. Source of the v0.28 question.
- [[docs/experiments/fear_hunger_v0.24.md]] — v0.24 population-
  dynamics diagnostic; `PopulationTrajectory` library introduced.
  v0.28 extends this library purely-additively.
- [[docs/experiments/fear_hunger_v0.26.md]] — v0.26 perception-vs-
  damage decoupling; Reading A confirmed.
- [[docs/handoffs/2026-05-05-v0.27-shipped-v0.28-planned.md]] —
  end-of-session handoff naming the v0.28 slice and the candidate
  observables.
- [[src/hedonism_harness/experiments/population_dynamics.py]] — the
  v0.24 trajectory loader receiving the v0.28 extension.
- [[docs/specs/v0.2_reflex_cell_spec.md]] §"Comparison framework" —
  the substrate axis.

---

## Results

**Status:** not yet executed. Diagnostic + results to be appended in
the next phase of v0.28.
