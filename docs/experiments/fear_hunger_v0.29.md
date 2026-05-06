# v0.29 — food_ladder w=0.75 dip reproducibility on a fresh seed stream

**Status:** pre-registration draft; not yet executed.
**Date:** 2026-05-06
**Branch:** `claude/v0.29-w075-reproducibility-fresh-seeds`
**Predecessors:** v0.21 (chamber-asymmetric influx frontier at hzd=8),
v0.22 (hazard sweep on food_ladder), v0.23 (chamber-dependent hazard
sign), v0.24 (population-dynamics diagnostic; pool-exhaustion-timing),
v0.25 (hazard × influx — tight interior optimum at h=8), v0.26
(perception-vs-damage decoupling — Reading A confirmed; avoidance
load-bearing on both chambers), v0.27 (avoidance-weight frontier on
both chambers — interior optima; food_ladder b>50=89 dip at w=0.75
flagged as "aggregate large enough to flag, not a stable regime"),
v0.28 (per-seed trajectory diagnostic on existing v0.27 artifacts —
TAIL-SEED CRASH classification; seeds 5 and 1 carry 89% of the −9
aggregate deficit; 5 of 8 seeds have byte-identical b>50 at every
weight; v0.27 cautious framing confirmed; named v0.29 reproducibility
on seeds 9..16 as the highest-priority next step).
**Spec:** [[docs/specs/v0.2_reflex_cell_spec.md]] §"Comparison framework"
(substrate axis).

## Question

The v0.27 / v0.28 food_ladder b>50=89 dip at w=0.75 was driven by 2 of
8 seeds (5 and 1) on the (1..8) seed set. **Does a fresh RNG stream
(seeds 9..16) at the same configuration show the same dip, a
differently-distributed dip, no dip at all, or a broader uniform
effect?**

This is the cleanest possible discrimination between three readings
of the v0.28 result that the (1..8) seed set cannot distinguish:

(α) **Sample artefact.** The dip on seeds (1..8) was a
small-sample concentration that happens to net negative on that
specific seed set. A fresh seed stream produces a different aggregate
at w=0.75 — possibly no dip, possibly a dip in a different direction.
Reading: there is no stable mechanism; the v0.27 cautious framing
("aggregate large enough to flag, not a stable regime") closes the
question.

(β) **Stochastic seed-concentrated mechanism.** Some seeds, regardless
of which set, exhibit a w=0.75 late-births contraction (population
dip per seed 5; population pressure / birth compression per seed 1).
The fresh seed stream concentrates the deficit on a *different* small
subset of seeds (1-2 of 8), yielding a similar aggregate dip. Reading:
the mechanism is real but stochastically distributed; the per-seed
late-window dynamics at w=0.75 are interesting and warrant
per-agent / lineage inspection on the new flipped seeds.

(γ) **Broad uniform regime.** Seeds (1..8)'s 5-of-8 byte-identical
b>50 across weights was itself an artefact of the (1..8) initial
conditions; a fresh seed stream distributes per-seed sensitivity more
broadly and surfaces a uniform population-wide degradation at w=0.75
(v0.28's H7 signature). Reading: the v0.27 / v0.28 framing was
incomplete; the dip is a real population-wide effect; the
(hazard, weight, influx) parameter grid expansion that has been
deferred since v0.27 becomes warranted.

## What this slice tests, and what it does NOT test

### Tests

- **Reproducibility of the v0.27 / v0.28 food_ladder w=0.75 b>50 dip
  on a fresh RNG stream** (seeds 9..16) at the same configuration:
  food_ladder, hazard_damage=8, ambient_influx_rate=1.0, energy_pool=1500,
  PARENT_TRANSFER_POOL_GAP, GradientPolicy, no scalar memory,
  unbounded_mutation, n_ticks=200, n_founders=5.
- **Whether the v0.28 H5 / H6 / H7 / H8 mechanism classification
  changes** when applied to seeds (9..16) instead of (1..8). The
  v0.28 driver re-runs on the new artifacts; classification is
  pre-committed to drive the v0.29 outcome reading.
- **Conservation invariants** continue to hold at every cell (H1..H5
  from v0.20..v0.28).

### Does NOT test

- **No new arms.** V0_29_ARMS is a 3-tuple subset of V0_27_ARMS at
  w ∈ {0.5, 0.75, 1.0} on the same hazard / influx / pool / funding-mode
  substrate. Pre-committed substrate-byte-identity test against
  V0_27_ARMS.
- **No new chambers.** food_ladder only.
- **No new weights.** w ∈ {0.5, 0.75, 1.0} only — the same three cells
  v0.28 paired-seed-compared. w ∈ {0.0, 0.25} are anchors of the
  monotone-rising part of the v0.27 curve and not part of the dip
  question.
- **No new hazard / influx / pool / funding-mode variation.** Same
  substrate as v0.21..v0.28.
- **No expansion to seeds beyond 9..16.** A specific 8-seed RNG stream
  is the test; broader cross-seed-stream robustness (e.g., 17..24) is
  a v0.30+ candidate **only if v0.29 itself produces an ambiguous
  result**.
- **No simulation-mechanics changes.** No `core/` / `model.py` /
  `experiments/fear_hunger_chamber.py` / `policies/gradient_policy.py`
  changes. v0.27's seam is sufficient.
- **No per-agent / lifespan / lineage / trait inspection.** v0.28
  named that as a v0.29 secondary candidate; this pre-reg restricts
  v0.29 to the seed-stream null-or-not check. Per-agent inspection
  is bumped to v0.30+ conditional on outcome (β).
- **No expansion of the (hazard, weight, influx) parameter grid.**
  The v0.27 / v0.28 watch-out continues: do not expand the grid until
  a uniform regime (outcome γ) is firmly established.
- **No HedonismPolicy comparisons.** Quarantined per v0.2 spec.

### Deferred (v0.30+ candidates, conditional on v0.29 outcome)

- **(Outcome α — sample artefact.)** No further follow-up on the dip;
  forward references in v0.27 / v0.28 / v0.29 close the question. v0.30
  candidate becomes a *different* slice (e.g., the v0.28 secondary
  candidate of per-agent / lineage inspection on seeds 5 and 1 — but
  with reduced motivation since the dip is sample-specific).
- **(Outcome β — stochastic seed-concentrated mechanism.)** Per-agent
  / lifespan / lineage inspection on the new flipped seeds (1-2 of
  9..16) at w ∈ {0.5, 0.75, 1.0}. Goal: characterise *why* specific
  seeds exhibit the late-births contraction. v0.30+ slice; out of
  scope for v0.29.
- **(Outcome γ — broad uniform regime.)** (hazard, weight, influx)
  cross-product on food_ladder around (h=8, w=0.75, i=1.0), still
  with seeds 9..16 only. The grid expansion deferred since v0.27
  becomes warranted; pool-exhaustion-timing dependence on influx is
  the leading mechanism candidate.
- **Cross-seed-stream robustness** (seeds 17..24 etc.) only if v0.29
  is itself ambiguous and a tie-break is needed.

## Conservation framing — unchanged from v0.20..v0.28

v0.29 introduces no new conservation contract. The six-flow
PARENT_TRANSFER_POOL_GAP bookkeeping is preserved exactly. Only the
seed set varies; substrate identity to V0_27_ARMS is pre-committed.

## Mechanism

**No simulation-mechanics changes.** v0.29 is a configuration cut +
a sweep + an analysis re-run on a fresh seed set. Implementation
surface:

1. **Configuration:** new `V0_29_ARMS` tuple in
   [[src/hedonism_harness/experiments/comparison_grid.py]], a 3-arm
   subset of V0_27_ARMS at w ∈ {0.5, 0.75, 1.0}. ~20 LOC. Substrate
   fields byte-identical to the corresponding V0_27_ARMS members
   (hazard_damage=8, energy_pool=1500, influx=1.0, transfer-mode,
   etc.); only `hazard_avoidance_weight` varies.
2. **Sweep driver:** new
   [[scripts/v0.29_sweep.py]], runs `V0_29_ARMS` × seeds 9..16 ×
   food_ladder. ~70 LOC. Persists per-arm comparison.csv into
   `runs/fear-hunger-v0.29-food_ladder/`.
3. **Diagnostic re-run:** the v0.28 driver
   [[scripts/v0.28_trajectory_diagnostic.py]] is parameterised
   (extract the per-seed-load + classification logic into a callable
   that takes `runs_root: Path` and `seeds: Sequence[int]`), and a
   thin v0.29 caller `scripts/v0.29_diagnostic.py` invokes it
   against the new artifacts. ~50 LOC of refactor + ~40 LOC of new
   driver. The refactor is **purely additive** for the existing
   v0.28 caller — its hardcoded constants become the default
   arguments of the new function.
4. **Tests:** new `tests/test_comparison_grid_v0_29.py`. V0_29_ARMS
   shape; substrate identity vs V0_27_ARMS subset; prior arms
   unchanged; H5 mechanical sanity (food_ladder injury_deaths > 0
   at every weight, on a one-seed run from the new seed range).
   ~150 LOC.

The v0.20..v0.28 telemetry surface is sufficient. No new event types,
no chamber changes, no policy changes.

### Determinism — substrate anchors

V0_29_ARMS substrate fields byte-identical to the V0_27_ARMS subset:

| weight | V0_27 label   | V0_29 label   |
|-------:|---------------|---------------|
| 0.50   | hzd8-avd0.50  | hzd8-avd0.50  |
| 0.75   | hzd8-avd0.75  | hzd8-avd0.75  |
| 1.00   | hzd8-avd1.00  | hzd8-avd1.00  |

Test pins every substrate field across the matched pairs. Halt
condition.

**No data anchors.** Seeds 9..16 are a fresh RNG stream; their
artifacts are novel. There is no byte-identity reproduction guard
against prior versions on the b>50 / haz_entries / etc. aggregate
columns — the data is the test.

## Arms

Three arms × eight seeds (9..16) × one chamber = **24 runs**.

| arm | weight | label |
|---|---:|---|
| A | 0.50 | hzd8-avd0.50 |
| B | 0.75 | hzd8-avd0.75 |
| C | 1.00 | hzd8-avd1.00 |

Substrate per arm: `hazard_damage=8.0`, `energy_cost=15`,
`energy_threshold=50`, `offspring_start_energy=30`,
`food_respawn_cooldown=50`, `energy_pool_initial=1500`,
`ambient_influx_rate=1.0`,
`child_funding_mode=PARENT_TRANSFER_POOL_GAP`,
GradientPolicy with no scalar memory, `unbounded_mutation=True`,
`n_ticks=200`, `n_founders=5`. Same as the corresponding V0_27_ARMS
members. Seeds (9, 10, 11, 12, 13, 14, 15, 16).

### Telemetry to watch

Same as v0.28 — per-seed observables computed by the v0.28 loader
(`EventBandTrajectory` + `PopulationTrajectory`) on the new
events.jsonl files:

- Per-seed b>50 across w ∈ {0.5, 0.75, 1.0}; aggregate sums; per-seed
  Δ(0.75−0.50) and Δ(0.75−1.00) deltas.
- Per-seed `mean_pop_late`, `first_pool_birth_denied_tick`,
  `tick_of_peak`, `peak_population`.
- Per-band aggregates (50-tick windows): births, food, hazard
  entries, starvation deaths, injury deaths, pool_birth_denied.

The v0.28 driver's H5 / H6 / H7 / H8 evaluation is re-run on the
seeds 9..16 observables and reported in the v0.29 diagnostic report.

## Pre-registered hypotheses

Two-tier structure: **strong-form** for invariants + determinism,
**cautious-form** for the substantive outcome discrimination.

### Strong form (invariants + determinism)

- **H1.** `pool_in_ambient_influx == ambient_influx_rate ×
  sum(executed_ticks_per_seed)` per arm. v0.20 conservation contract.
- **H2.** v0.20 H4 invariant holds at every v0.29 cell:
  `parent_energy_transferred_to_child + pool_out_child_startup ==
  total_births × offspring_start_energy`.
- **H3.** `reproduction_heat_loss == 0` at every v0.29 cell.
- **H4.** `births_blocked_by_parent_energy == 0` at every v0.29 cell.
- **H5.** `total_injury_deaths > 0` on food_ladder at every weight
  in {0.5, 0.75, 1.0} (cull-tax presence at hazard=8).
- **H6 (substrate identity).** V0_29_ARMS substrate fields
  byte-identical to V0_27_ARMS subset at the matched labels. Halt
  condition.
- **H7 (prior arms unchanged).** No prior arm tuple
  (V0_19/20/21/22/23/25/26/27_ARMS) modified. Halt condition.
- **H8 (v0.28 loader byte-identity).** Re-running the v0.28 H9
  parametrised test against the on-disk v0.27 artifacts continues to
  pass after the v0.29 additions. Pure-additive guard.

### Cautious form (outcome discrimination)

The decision is made on the **paired-seed b>50 vector** at
w ∈ {0.5, 0.75, 1.0} for seeds 9..16, plus the v0.28
H5 / H6 / H7 mechanism classification re-run on those seeds.

Define `B(w)` = aggregate b>50 across seeds 9..16 at weight w.
Define the v0.27 / v0.28 dip threshold as `B(0.75) < B(0.5) − 4`
(strict deficit clear of single-seed noise; the v0.27 / v0.28
deficit was 9, well above this threshold).

- **H9 (Outcome α — sample artefact, no dip).** **FIRES iff**
  **NOT** `B(0.75) < B(0.5) − 4` AND **NOT** `B(0.75) < B(1.0) − 4`.
  I.e., w=0.75 is not the strict aggregate minimum on seeds 9..16
  (within noise tolerance). Reading: 1..8 dip was sample-specific.
- **H10 (Outcome β — stochastic seed-concentrated mechanism).**
  **FIRES iff** `B(0.75) < B(0.5) − 4` AND the v0.28 driver
  classification on seeds 9..16 returns either "TAIL-SEED CRASH (H6)"
  or "ROUTING-LINKED TAIL CRASH" (i.e., v0.28's H6 fires). Reading:
  the dip is real but stochastically concentrated on a small subset
  of seeds; the specific seeds differ from (1, 5).
- **H11 (Outcome γ — broad uniform regime).** **FIRES iff**
  `B(0.75) < B(0.5) − 4` AND the v0.28 driver classification on seeds
  9..16 returns "UNIFORM POPULATION-WIDE DEGRADATION (H7)". Reading:
  the broad-population reading the (1..8) set was unable to support is
  real; the (hazard, weight, influx) grid expansion deferred since
  v0.27 is warranted.
- **H12 (Outcome δ — ambiguous / mixed).** **FIRES iff**
  `B(0.75) < B(0.5) − 4` AND none of v0.28's H5 / H6 / H7 fires (i.e.,
  v0.28 returns "STATISTICAL NOISE (H8 fallback)"), OR the
  classification fires "ROUTING-THRESHOLD FLIP (H5)" alone (a
  signature distinct from the (1..8) result). Reading: the dip is
  real on this seed stream but the mechanism signature is different
  from the (1..8) set; the dip is more sample-noisy than v0.28
  framed it.

H9 / H10 / H11 / H12 are designed to **partition the outcome space**:
exactly one fires by construction (the conjuncts are mutually
exclusive given the v0.28 classifier's tie-break rules). If none
fires the operational definitions are at fault and the diagnostic
must be re-evaluated — halt.

## Decision rules

- **H9 fires (Outcome α).** Headline: the v0.27 / v0.28 dip was a
  small-sample concentration on the (1..8) seed set. v0.30 candidate
  is unrelated to the dip (e.g., per-agent inspection deferred from
  v0.28, with reduced motivation; or a different slice entirely).
- **H10 fires (Outcome β).** Headline: the seed-concentrated
  late-births contraction at w=0.75 is a real stochastic mechanism
  that surfaces on different seed subsets across RNG streams.
  v0.30 candidate is per-agent / lifespan / lineage inspection on
  the new flipped seeds; possibly also a finer weight grid around
  w=0.75 (≤ 5 weights × 8 seeds × 1 chamber, ≤ 5s) on the same
  seeds 9..16 to localise the threshold.
- **H11 fires (Outcome γ).** Headline: the dip is a real
  population-wide effect that the (1..8) seed set under-sampled.
  v0.30 candidate is the (hazard, weight, influx) grid expansion
  on food_ladder that has been deferred since v0.27 — pool-
  exhaustion-timing dependence on influx is the leading mechanism
  hypothesis.
- **H12 fires (Outcome δ).** Headline: the dip is real but its
  mechanism signature is sample-stream-dependent. Cautious framing;
  v0.30 candidate is a third seed-stream check (17..24) to test
  whether the H5 / H6 / H7 classification stabilises with more
  cross-stream data.
- **None of H9 / H10 / H11 / H12 fires.** Halt and re-evaluate the
  operational definitions; the conjuncts should partition the
  outcome space.
- **H1–H8 fail.** Halt and audit (invariants / substrate identity /
  prior arms / loader determinism). Same disciplinary halt conditions
  as v0.20..v0.28.

## Out of scope (v0.29)

- **Influx variation, hazard intensity variation, weights ∉
  {0.5, 0.75, 1.0}, weights > 1.0, long-window stability, pool-size
  sweep, reproduction efficiency variation, HedonismPolicy
  comparisons, Reading B substrate seam, heritability /
  mutation-distribution analysis, per-agent / lifespan / lineage
  inspection.** All deferred to v0.30+ conditional on outcome.

## Implementation notes

### File-level changes

- **Modify (additive):**
  [[src/hedonism_harness/experiments/comparison_grid.py]] — append
  `V0_29_ARMS` tuple of 3 `Arm` instances per the table above.
  ~20 LOC. No code-path changes.
- **Modify (additive):**
  [[scripts/v0.28_trajectory_diagnostic.py]] — extract the per-seed
  load + classification logic from `main()` into a callable
  `run_diagnostic(runs_root, seeds, ...)` so v0.29 can re-run the
  same pipeline on the new artifacts. The existing v0.28 entrypoint
  becomes a thin caller using the v0.27 defaults; behavior unchanged.
  ~50 LOC of refactor.
- **New:** [[scripts/v0.29_sweep.py]] — sweep driver mirroring
  `scripts/v0.27_sweep.py`; runs food_ladder × V0_29_ARMS × seeds
  9..16. ~70 LOC.
- **New:** [[scripts/v0.29_diagnostic.py]] — thin caller invoking the
  refactored v0.28 diagnostic against the v0.29 artifacts. ~40 LOC.
- **New:** `tests/test_comparison_grid_v0_29.py` — V0_29_ARMS shape;
  substrate identity to V0_27_ARMS subset; prior arms unchanged;
  H5 mechanical sanity on one seed from the 9..16 range. ~150 LOC.
- **No changes** to `core/`, `model.py`,
  `experiments/fear_hunger_chamber.py`,
  `experiments/population_dynamics.py`,
  `policies/gradient_policy.py`, `policies/hedonism_policy.py`.
- **Documented:** this file (`docs/experiments/fear_hunger_v0.29.md`);
  results appended after the sweep + diagnostic.

### Determinism contract

- `V0_19/20/21/22/23/25/26/27_ARMS` continue to produce identical
  sweep outputs after v0.29 changes (no prior surface modified).
- `V0_29_ARMS` substrate byte-identical to the V0_27_ARMS subset at
  the matched labels.
- The v0.28 H9 byte-identity guard against the v0.27 artifacts
  continues to pass after the diagnostic refactor.

### Wall time estimate

24 runs × 200 ticks. v0.27 took 22.2s for 80 runs; v0.29 estimated
~5–7s for food_ladder only. Diagnostic re-run < 1s.

### LOC estimate

- `experiments/comparison_grid.py`: +20 LOC.
- `scripts/v0.28_trajectory_diagnostic.py`: +50 LOC (refactor; no
  behavior change).
- `scripts/v0.29_sweep.py`: ~70 LOC.
- `scripts/v0.29_diagnostic.py`: ~40 LOC.
- `tests/test_comparison_grid_v0_29.py`: ~150 LOC.
- This doc: ~390 LOC.

Total v0.29 implementation: ~720 LOC. Smaller than v0.28 (~930 LOC)
because v0.29 reuses the v0.28 loader + diagnostic library directly.
Tests should bring the suite from 737 to ~745–750.

## References

- [[docs/experiments/fear_hunger_v0.28.md]] — v0.28 results;
  TAIL-SEED CRASH classification on seeds (1..8); named v0.29
  reproducibility on seeds 9..16 as the highest-priority next step.
- [[docs/experiments/fear_hunger_v0.27.md]] — v0.27 results;
  food_ladder w=0.75 dip flagged as "aggregate large enough to flag,
  not a stable regime."
- [[src/hedonism_harness/experiments/population_dynamics.py]] —
  v0.24 + v0.28 analysis library; reused unchanged by v0.29.
- [[src/hedonism_harness/experiments/comparison_grid.py]] — receives
  the additive V0_29_ARMS tuple.
- [[scripts/v0.28_trajectory_diagnostic.py]] — receives the
  refactor that exposes `run_diagnostic(...)` to v0.29.
- [[docs/specs/v0.2_reflex_cell_spec.md]] §"Comparison framework" —
  the substrate axis.

---

## Results

**Status:** not yet executed. Sweep + diagnostic + results to be
appended after the implementation phase.
