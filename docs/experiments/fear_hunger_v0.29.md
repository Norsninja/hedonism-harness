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
- **H8b (v0.29 artifact pre-flight).** After the sweep, every
  expected per-seed events.jsonl exists at
  `runs/fear-hunger-v0.29-food_ladder/arms/{label}/seed-{N}/events.jsonl`
  for `label ∈ {hzd8-avd0.50, hzd8-avd0.75, hzd8-avd1.00}` and
  `N ∈ {9..16}` (24 files), each non-empty. The diagnostic driver
  asserts this before computing observables. Not a scientific anchor
  — protects against path / labeling errors.

### Operational definitions — pre-committed

The decision is made on the **paired-seed b>50 vector** at
w ∈ {0.5, 0.75, 1.0} for seeds 9..16, plus the v0.28
H5 / H6 / H7 / H8 mechanism classification re-run on those seeds.

Define `B(w)` = aggregate b>50 across seeds 9..16 at weight w.

Define the **shared `dip_present` predicate** (used by every cautious
hypothesis below):

```
dip_present := B(0.75) <= B(0.5) − 5  AND  B(0.75) <= B(1.0) − 5
```

I.e., w=0.75 is a strict valley with at least a 5-birth aggregate
margin against both neighbors. Rationale:

- A 5-birth aggregate deficit across 8 seeds is the cleanest single-
  digit threshold above plausible single-seed noise (the v0.28
  per-seed deltas had max magnitude 5 on a single seed; a 5-birth
  *aggregate* requires either two seeds dropping by ~3 each or a
  broader pattern).
- Requiring the deficit against **both** neighbors (not just w=0.5)
  ensures the dip is a true valley shape rather than the asymmetric
  shoulder observed on (1..8) (where the deficit was 9 against w=0.5
  but only 3 against w=1.0). On the (1..8) seed set this stricter
  predicate would *not* fire — `B(0.75) − B(1.0) = 89 − 92 = −3 > −5`.
  v0.29 is therefore deliberately set up to require a cleaner
  reproduction than the v0.28 result itself satisfied.
- Integer-valued thresholds: `≤ B(neighbor) − 5` avoids the off-by-one
  ambiguity of `< B(neighbor) − 4` (the two are equivalent for
  integers but the former is clearer).

### Cautious form (outcome discrimination)

H9 / H10 / H11 / H12 partition the outcome space by construction
(the conjuncts on `dip_present` and on the v0.28 classifier verdict
are mutually exclusive given v0.28's tie-break rules):

- **H9 (Outcome α — sample artefact, no dip).** **FIRES iff**
  **NOT** `dip_present`. I.e., w=0.75 is not a strict valley on
  seeds 9..16. Reading: the (1..8) dip was sample-specific; the
  question closes.
- **H10 (Outcome β — stochastic seed-concentrated mechanism).**
  **FIRES iff** `dip_present` AND the v0.28 driver classification
  on seeds 9..16 returns either "TAIL-SEED CRASH (H6)" or
  "ROUTING-LINKED TAIL CRASH (H5+H6)" (i.e., v0.28's H6 fires).
  Reading: the dip is real but stochastically concentrated on a
  small subset of seeds; the specific seeds differ from (1, 5).
- **H11 (Outcome γ — broad uniform regime).** **FIRES iff**
  `dip_present` AND the v0.28 driver classification on seeds 9..16
  returns "UNIFORM POPULATION-WIDE DEGRADATION (H7)". Reading: the
  broad-population reading the (1..8) set was unable to support is
  real; the (hazard, weight, influx) grid expansion deferred since
  v0.27 is warranted.
- **H12 (Outcome δ — ambiguous / mixed).** **FIRES iff**
  `dip_present` AND the v0.28 driver returns either
  "STATISTICAL NOISE (H8 fallback)" or "ROUTING-THRESHOLD FLIP (H5)"
  alone. Reading: the dip is real on this seed stream but the
  mechanism signature is different from the (1..8) set; the dip is
  more sample-noisy than v0.28 framed it.

By construction exactly one of H9 / H10 / H11 / H12 fires. If none
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

**Status:** executed 2026-05-06. 24 runs (3 weights × 8 seeds × 1
chamber, food_ladder), 6.7s wall time. v0.29 sweep wrote artifacts
to `runs/fear-hunger-v0.29-food_ladder/`; v0.29 diagnostic wrote
the per-seed report to `runs/fear-hunger-v0.29-food_ladder/diagnostic.md`.
All determinism / invariant hypotheses hold (H1–H8b: substrate
identity to V0_27_ARMS pinned by the literal-subset construction;
prior arms unchanged; v0.28 H9 anchor against v0.27 artifacts still
green; artifact pre-flight passes; suite 716 → 748 → still green).

**Headline:** **H9 fires — Outcome α (sample artefact, no dip).** The
(1..8) dip does not reproduce on seeds 9..16: aggregate b>50 at
w=0.75 is **not** a strict valley with the pre-committed ≥5-birth
margin against both neighbors (Δ(0.75−0.50)=−2; Δ(0.75−1.00)=−8;
need both ≤ −5). The v0.28 classifier returns
**STATISTICAL NOISE (H8 fallback)** on the new seeds — none of
H5 / H6 / H7 fires.

**Secondary finding (not pre-registered): the v0.27 food_ladder
"interior optimum at w=0.5" claim reverses sign on seeds 9..16.**
v0.27 reported food_ladder w*=0.5 as a "decisive" interior optimum
(+6 b>50 vs w=1.0; 98 vs 92, 1..8 seeds). v0.29 reports
**w*=1.0 as the optimum** on seeds 9..16, with **the same +6
magnitude** in the opposite direction (98 vs 92, 9..16 seeds). The
location of the food_ladder interior optimum is itself
sample-stream-dependent at the 8-seed sample size — a methodological
finding about the resolution power of the historical convention as
much as a scientific finding about the avoidance-weight curve.

### Aggregate b>50 — paired against the v0.27 / v0.28 (1..8) result

| weight | (1..8) b>50 | (9..16) b>50 | Δ | (9..16) − (1..8) location |
|-------:|------------:|-------------:|----:|------------------------:|
| 0.50   | **98** (max) | 92          | −6 | optimum **moves away** |
| 0.75   | 89 (min)     | 90          | +1 | dip **does not reproduce** |
| 1.00   | 92           | **98** (max) | +6 | optimum **moves here** |
| sum    | 279          | 280         | +1 | total productivity ≈ equal |

Total productivity across the three weights is essentially identical
(279 vs 280); the **distribution across weights inverts**.

### Hypothesis adjudication

| H | claim | result |
|---|---|---|
| H1 | influx conservation | **HOLDS** (24 runs at 1.0/tick × 200 ticks; in_influx=1600 per arm). |
| H2 | transfer-mode contract | **HOLDS** (xfer = births × 15 across all cells). |
| H3 | reproduction_heat_loss == 0 | **HOLDS**. |
| H4 | births_blocked_by_parent_energy == 0 | **HOLDS**. |
| H5 | food_ladder injury_deaths > 0 at every weight | **HOLDS** (34 / 30 / 30 across w=0.5 / 0.75 / 1.0). |
| H6 | V0_29_ARMS substrate identity to V0_27_ARMS subset | **HOLDS** (literal-subset construction; tested in `test_v0_29_arms_are_literal_v0_27_subset`). |
| H7 | prior arms unchanged | **HOLDS** (suite 737 → 748; pure addition). |
| H8 | v0.28 H9 byte-identity against v0.27 artifacts still passes | **HOLDS** (re-running v0.28 driver on seeds 1..8 produces byte-identical diagnostic.md). |
| H8b | v0.29 artifact pre-flight | **HOLDS** (24 events.jsonl files present, non-empty; `assert_artifacts_present` succeeds). |
| H9 | NOT dip_present | **FIRES.** Δ(0.75−0.50)=−2; Δ(0.75−1.00)=−8; only one of the two ≤−5 thresholds met. **dip_present is False**. **Outcome α: sample artefact, no dip.** |
| H10 | dip_present AND v0.28 H6 fires | does not fire (dip_present is False). |
| H11 | dip_present AND v0.28 H7 fires | does not fire (dip_present is False; v0.28 H7 also fails on these seeds: 2 of 8 seeds with negative delta vs ≥6 required). |
| H12 | dip_present AND v0.28 H8/H5-alone | does not fire (dip_present is False). |

Exactly one outcome partition member fires (H9), as required by the
pre-reg. Halt conditions hold across the full hypothesis suite.

### v0.28 classifier verdicts on seeds 9..16

For completeness — what the v0.28 classifier saw:

- **H5 (routing flip):** 0 flipped seeds (need ≥ 2). Bimodality
  utterly fails — the maximum-magnitude single-seed delta is −2,
  well above the −5 flipped threshold.
- **H6 (tail crash):** Tail seeds [9, 16] carry 100% of the
  aggregate (small) negative deficit. But no crash signatures fire
  (no late-population drop ≥30%, no `PoolBirthDenied`-earlier-by-30
  signature on the tail seeds), and the safe-at-neighbors check
  fails — seed 9 has b50=7 at w=0.5 vs the (9..16) median of 12,
  flagging seed 9 as a low-productivity seed across all weights
  rather than a w=0.75-specific crasher.
- **H7 (uniform):** Only 2 of 8 seeds have negative
  Δ(0.75−0.50) (need ≥6). The shape is neither a tail-concentration
  (H6) nor a uniform shift (H7); the deltas are very nearly zero
  for most seeds.

### Per-seed b>50 — strong cross-seed-stream pattern: weight-insensitivity

The (1..8) result had **5 of 8 seeds** with b>50 byte-identical
across all three weights. The (9..16) result has **6 of 8 seeds**
with `|Δ(0.75−0.50)| ≤ 1`:

| seed | w=0.50 | w=0.75 | w=1.00 | Δ(0.75−0.50) | Δ(0.75−1.00) |
|-----:|-------:|-------:|-------:|-------------:|-------------:|
| 9    | 7      | 5      | 14     | −2           | **−9**       |
| 10   | 12     | 13     | 11     | +1           | +2           |
| 11   | 11     | 12     | 15     | +1           | −3           |
| 12   | 14     | 14     | 14     | +0           | +0           |
| 13   | 14     | 14     | 11     | +0           | +3           |
| 14   | 11     | 11     | 12     | +0           | −1           |
| 15   | 12     | 12     | 12     | +0           | +0           |
| 16   | 11     | 9      | 9      | −2           | +0           |

The cross-stream observation: **most food_ladder seeds at the
v0.21 substrate are nearly insensitive to avoidance weight in
[0.5, 1.0]**. Both seed sets show this. The dip / interior-optimum
debate is being driven by the 2-3 weight-sensitive seeds in each
sample, whose specific direction of sensitivity is not stable
across RNG streams.

Worth flagging at the seed level: **seed 9 has b>50=14 at w=1.0 but
only 7 at w=0.5 (Δ=−9 against w=1.0)** — the largest single-seed
weight-sensitivity in the (9..16) set. Seed 9 alone accounts for
most of the +6 aggregate advantage of w=1.0 over w=0.5 on this seed
stream. Symmetric with how seed 5 alone drove most of the (1..8)
+6 advantage of w=0.5 over w=1.0.

### Routing channel: monotone in weight, robustly across seed streams

The v0.27 framing of "monotone routing, non-monotone productivity"
**survives on seeds 9..16**:

| observable        | w=0.50 | w=0.75 | w=1.00 | shape (vs weight) |
|-------------------|-------:|-------:|-------:|-------------------|
| hazard_entries    | 218    | 189    | 170    | **strict monotone non-increasing** |
| injury_deaths     | 34     | 30     | 30     | non-increasing |
| starvation_deaths | 65     | 62     | 55     | monotone non-increasing |
| food_events       | 764    | 759    | 752    | weakly non-increasing |
| in_death_residual | 1256.4 | 1032.2 | 1161.1 | non-monotone (small) |

The routing channel responds to avoidance weight as expected; the
productivity (b>50) channel does not. Same pattern as v0.27 on
(1..8).

### What v0.29 changes about prior framings

- **v0.27 / v0.28 cautious framing of the w=0.75 dip is fully
  vindicated.** "Aggregate large enough to flag, not a stable
  regime" was the right call. The dip is sample-specific.
- **v0.27 "food_ladder interior optimum at w=0.5 (+6 b>50 vs w=1.0)"
  finding is also sample-specific.** The +6 reverses sign on seeds
  9..16. The qualitative observation "food_ladder b>50 is
  non-monotone in w" survives across both streams; the **location**
  of the optimum does not. 8 seeds is at the limit of what can
  resolve a stable interior optimum at this signal magnitude.
- **v0.27 "monotone routing" finding survives** on the new seed
  stream (hazard entries, injury deaths, starvation deaths all
  non-increasing in weight). The routing channel is robustly
  weight-responsive across both samples.
- **The v0.26 "Reading A confirmed" finding remains intact**
  (perception is purely damage-derived; v0.29 does not test it).
- **The v0.25 "tight interior optimum at h=8" hazard-axis finding
  remains intact** (v0.29 does not test it; tight is out of scope).

### v0.30 candidates

In rough priority order, conditional on the v0.29 result:

1. **(Highest priority — methodological)** Larger seed sample on
   food_ladder × w ∈ {0.5, 0.75, 1.0} to characterise the actual
   shape of the avoidance-weight curve at this productivity range,
   given that the 8-seed sample size cannot resolve a stable
   interior optimum. A 24-seed pool (combining seeds 1..16 plus
   17..24, 72 runs, ≤ 20s) would tighten the standard error by
   ~√3 and either confirm a flat curve (in which case v0.27's
   non-monotonicity finding is downgraded to sample noise) or
   surface whichever direction of asymmetry is actually robust.
2. **Per-seed lifespan / lineage / trait-distribution inspection**
   on the cross-stream "weight-sensitive" seeds (5 and 1 from
   (1..8); 9 and 16 from (9..16)) at w ∈ {0.5, 0.75, 1.0}.
   Originally a v0.30 candidate from v0.28 conditional on
   Outcome β firing in v0.29. Outcome β did not fire — so this
   slice is now less motivated; do it only after (1) clarifies
   whether the per-seed sensitivity has a stable substrate.
3. **No expansion of the (hazard, weight, influx) parameter grid.**
   The v0.27 / v0.28 / v0.29 watch-out continues: do not expand the
   grid until a stable mechanism is identified. v0.29 demonstrates
   the food_ladder avoidance-weight finding is not stable at the
   current sample size; expanding the grid would multiply the
   sample-size problem.
4. **Re-examine v0.21..v0.27 conventions on 8 seeds.** The
   methodological finding (8 seeds is at the limit of resolving
   ±6-birth interior optima) has implications for prior slices
   that reported small-magnitude interior optima with similar
   aggregate margins (v0.25 tight h*=8 cull-tax interactions;
   v0.27 tight w*=0.75 +2-birth boundary). v0.30+ candidate:
   re-run those v0.25 / v0.27 cells on a fresh seed stream as a
   sanity check before treating those small-margin findings as
   robust.

### Implementation summary

- **Configuration:** ~20 LOC `V0_29_ARMS` in
  `experiments/comparison_grid.py` — a literal 3-tuple slice of
  V0_27_ARMS. Substrate-byte-identity by construction.
- **Diagnostic refactor:** ~100 LOC additive change to
  `scripts/v0.28_trajectory_diagnostic.py` — extracted
  `DiagnosticConfig`, `run_diagnostic`, `assert_artifacts_present`,
  `DiagnosticOutcome`. **v0.28 byte-identity confirmed**: re-running
  the v0.28 entrypoint produces byte-identical diagnostic.md
  against the pre-refactor baseline. The H5 / H6 / H7 classifier
  is unchanged.
- **Sweep driver:** ~85 LOC `scripts/v0.29_sweep.py`.
- **Diagnostic wrapper:** ~130 LOC `scripts/v0.29_diagnostic.py` —
  thin caller that reuses the v0.28 module via a spec-based import,
  applies the v0.29 H9 / H10 / H11 / H12 outcome partition over
  the shared `dip_present` predicate.
- **Tests:** ~190 LOC `tests/test_comparison_grid_v0_29.py`
  (11 new tests; suite 737 → 748). Pinning V0_29_ARMS shape /
  literal-subset identity / equality-fallback substrate identity /
  prior-arms-unchanged / H5 mechanical sanity at one seed.
- **Wall time:** sweep 6.7s on 24 runs; diagnostic < 1s.
- **No simulation-mechanics changes; no `core/` / `model.py` /
  `experiments/fear_hunger_chamber.py` /
  `policies/gradient_policy.py` /
  `policies/hedonism_policy.py` changes.** Source additions are
  limited to a configuration cut (V0_29_ARMS) + the additive
  refactor of the v0.28 diagnostic + the v0.29 sweep / diagnostic
  drivers + tests.
- **CI gate at handoff time:**
  ```
  uv run ruff check .                          ok
  uv run ruff format --check .                 ok
  uv run pytest                                748 passed
  uv run python scripts/core_smoke_test.py     ok
  uv run python scripts/v0.28_trajectory_diagnostic.py  TAIL-SEED CRASH (H6); byte-identical
  uv run python scripts/v0.29_sweep.py         6.7s; 24 runs
  uv run python scripts/v0.29_diagnostic.py    Outcome α (H9) — sample artefact, no dip
  ```
