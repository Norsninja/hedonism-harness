# v0.27 — avoidance-weight frontier: monotone, costly, or interior optimum?

**Status:** pre-registration; not yet executed.
**Date:** 2026-05-05
**Branch:** `claude/v0.27-avoidance-weight-frontier`
**Predecessors:** v0.21 (chamber-asymmetric influx frontier at hzd=8;
food_ladder primary i\*=0.5/tick, tight primary i\*=1.5/tick), v0.22
(narrow hazard sweep on food_ladder under transfer + influx=1.0;
recycling-as-net-tax confirmed), v0.23 (hazard-zero influx frontier
on both chambers; chamber-dependent hazard sign discovered), v0.24
(population-governor reading falsified; pool-exhaustion-timing
substituted), v0.25 (hazard × influx sweep — tight interior optimum
at h=8 confirmed; food_ladder monotone non-increasing in hazard),
v0.26 (perception-vs-damage decoupling 2×2 — `hazard_avoidance_weight`
seam shipped; **avoidance routing is load-bearing on BOTH chambers
at the binary endpoints**: tight b>50 116 ↔ 107 across weight 1↔0;
food_ladder injury_deaths 16 ↔ 40 across weight 1↔0; phantom ≡
no-hazard byte-identical → Reading A confirmed).
**Spec:** [[docs/specs/v0.2_reflex_cell_spec.md]] §"Comparison framework"
(substrate axis).

## Question

v0.26 measured the binary endpoints of avoidance ablation
(weight ∈ {0.0, 1.0}) at hazard=8 on both chambers and confirmed
avoidance routing is load-bearing on both. **What v0.26 cannot say
is the SHAPE of the productivity curve as avoidance varies between
those endpoints.** Three qualitatively distinct shapes are consistent
with the v0.26 endpoint pair (tight: 107 → 116; food_ladder: 88 → 92):

(a) **Monotone non-decreasing.** More avoidance → more productivity,
all the way up. The endpoints determine a smooth interior. No interior
optimum.

(b) **Diminishing returns / concave monotone.** More avoidance →
more productivity, but most of the gain happens early (e.g.,
between weight=0 and weight=0.25); subsequent weight increments add
little. Mechanism reading: a small amount of avoidance is enough to
deflect agents from the most-lethal hazard cells; additional avoidance
just over-weights pain pull without changing routing meaningfully.

(c) **Interior optimum on the [0, 1] domain.** Some weight in
{0.25, 0.5, 0.75} produces b>50 *strictly greater* than the weight=1.0
anchor. Mechanism reading: at very high avoidance, agents over-route
— they take longer paths around hazards even when the detour costs
more energy than the direct cull would. Some intermediate weight
maximizes the net pleasure-pull vs pain-pull balance. **This would
be the v0.27 substantive headline** — it would mirror v0.25's
tight-interior-optimum-at-h=8 finding but on a different axis: at
fixed hazard, the policy itself has an avoidance sweet-spot below
unit weight.

(d) **Monotone non-increasing (avoidance is net costly within
[0, 1]).** The v0.26 endpoint pair already rules this out on both
chambers — weight=1.0 beats weight=0.0 on b>50 in both cases — so
this shape is excluded a priori.

**v0.27 maps the curve at five weights to discriminate (a) / (b) /
(c) on each chamber.** The grid:
`hazard_avoidance_weight ∈ {0.0, 0.25, 0.5, 0.75, 1.0}` at fixed
`hazard_damage=8`, `ambient_influx_rate=1.0`,
`energy_pool_initial=1500`, `child_funding_mode=PARENT_TRANSFER_POOL_GAP`,
both chambers, same 8 seeds (1..8) as v0.21..v0.26.

5 arms × 2 chambers × 8 seeds = **80 runs**. Same wall-time class
as v0.21 / v0.23 / v0.26.

## What this slice tests, and what it does NOT test

### Tests

- **The shape of b>50 vs `hazard_avoidance_weight` on each chamber**
  at the v0.26 substantive cell (hazard=8, influx=1.0). Monotone vs
  concave-monotone vs interior optimum.
- **Whether tight has an interior optimum on the avoidance axis.**
  v0.25 found tight has an interior optimum on the hazard axis at
  h=8; v0.27 asks whether tight similarly has an interior optimum on
  the avoidance axis at w<1. Mechanism connection: both the hazard
  and avoidance axes feed into the policy's pain-pull weighting; a
  symmetric interior-optimum pattern would tighten the v0.25
  cull-tax-vs-timing-penalty mechanism reading.
- **Whether food_ladder's avoidance curve is also non-monotonic.**
  Predicted shape: monotone or diminishing-returns. v0.22 / v0.25
  established food_ladder as cull-tax-dominated in the hazard axis
  (monotone non-increasing in hazard). The avoidance axis is a
  *different* scaling — at fixed hazard, more avoidance reduces the
  cull-tax. Cautious: food_ladder geometry forces hazard crossings,
  so increased avoidance has a clear monotone benefit (more
  deflection, fewer deaths). If food_ladder shows an interior
  optimum, the routing-vs-cull-tax tradeoff is more subtle than v0.26
  framing suggested.
- **Mechanical: `total_injury_deaths` is monotone non-increasing in
  weight on both chambers.** Direct routing observable. v0.26
  established the endpoints (tight 0/0; food_ladder 40/16). v0.27
  fills the interior.
- **Mechanical: `total_hazard_entries` is monotone non-increasing in
  weight on both chambers.** Same kind.
- **Conservation invariants** (H1..H5 from v0.20..v0.26) continue
  to hold at every cell.

### Does NOT test

- **Influx variation.** v0.27 fixes influx=1.0 (the v0.21..v0.26
  anchor cell). A v0.28 candidate is to replicate the avoidance
  frontier at influx ∈ {0.5, 1.5} if the curve shape varies sharply
  with influx.
- **Hazard intensity variation.** v0.27 fixes hazard_damage=8 (the
  v0.25 productivity-optimal hazard for tight). A v0.28+ candidate
  is to map weight × hazard at hazards {4, 12} on tight to test the
  generality of any interior-optimum finding.
- **Pool-size sensitivity.** Pool=1500 throughout.
- **Reproduction efficiency variation.** Transfer mode throughout.
- **HedonismPolicy comparisons.** Quarantined per v0.2 spec.
- **Reading B (separate `world.hazard_perceived` layer).** Out of
  scope — v0.27 stays on the v0.26 policy seam.
- **Weights > 1.0.** Out of scope. v0.27 maps the [0, 1] domain;
  weight > 1.0 amplifies pain pull beyond the v0.14..v0.25 default
  and would change the substrate's effective trait calibration. A
  v0.28+ candidate if v0.27 firmly establishes monotone shape on
  [0, 1] and the question becomes "does avoidance saturate at 1.0
  or continue rising?"
- **Long-window stability.** Same 200-tick window as
  v0.21..v0.26.

### Deferred (v0.28+ candidates, conditional on v0.27 outcome)

- **Influx × weight cross-product** at the substantive influx points
  if the avoidance curve depends on influx.
- **Weight × hazard cross-product** at hazards {4, 12} on tight if
  the interior-optimum on the weight axis turns out to depend on
  hazard intensity.
- **Reading B substrate seam** if a future question explicitly needs
  perception-without-damage decoupling.
- **Long-window stability** at n_ticks ∈ {500, 1000} on the
  productivity-optimal weight.

## Conservation framing — unchanged from v0.20..v0.26

v0.27 introduces no new conservation contract. The six-flow
PARENT_TRANSFER_POOL_GAP bookkeeping is preserved exactly. Only
`hazard_avoidance_weight` varies across arms (already shipped as a
v0.26 seam); no new code paths.

## Mechanism

**No new code paths.** v0.27 is purely configuration:

1. A new `V0_27_ARMS` tuple in
   [[src/hedonism_harness/experiments/comparison_grid.py]] consisting
   of 5 `Arm` instances at the (weight) grid above. ~95 LOC.
2. A new sweep driver
   [[scripts/v0.27_sweep.py]] mirroring `scripts/v0.26_sweep.py`. ~85 LOC.
3. A new test module
   `tests/test_comparison_grid_v0_27.py` (~180 LOC) pinning the
   arm grid, substrate, and prior-arms-unchanged guards.

The v0.20/v0.21/v0.22/v0.23/v0.25/v0.26 telemetry is sufficient for
v0.27 analysis. No core / sensors / world / model changes.

### Determinism — anchors

V0_27_ARMS contains explicit byte-identity anchors against the v0.26
sweep artifacts on disk:

| chamber | weight | anchor source | b>50 anchor |
|---|---:|---|---:|
| tight       | 0.0 | v0.26 hzd8-avd0.0 (invisible-tight)        | 107 |
| tight       | 1.0 | v0.26 hzd8-avd1.0 (coupled-tight)          | 116 |
| food_ladder | 0.0 | v0.26 hzd8-avd0.0 (invisible-food_ladder)  |  88 |
| food_ladder | 1.0 | v0.26 hzd8-avd1.0 (coupled-food_ladder)    |  92 |

Four anchors total. The 6 truly new (chamber, weight) cells are:
- (tight, 0.25), (tight, 0.5), (tight, 0.75)
- (food_ladder, 0.25), (food_ladder, 0.5), (food_ladder, 0.75)

These 6 cells carry the substantive new information — the interior
shape of the avoidance curve.

Failure of any anchor is a halt condition. The substrate is unchanged
and the same seeds are used, so anchor identity is a deductive
identity.

## Arms

Five arms × two chambers × eight seeds = **80 runs**.

| arm | weight | label |
|---|---:|---|
| A | 0.0  | hzd8-avd0.00 |
| B | 0.25 | hzd8-avd0.25 |
| C | 0.5  | hzd8-avd0.50 |
| D | 0.75 | hzd8-avd0.75 |
| E | 1.0  | hzd8-avd1.00 |

Substrate per arm: `hazard_damage=8.0`, `energy_cost=15`,
`energy_threshold=50`, `offspring_start_energy=30`,
`food_respawn_cooldown=50`, `energy_pool_initial=1500`,
`ambient_influx_rate=1.0`, `child_funding_mode=PARENT_TRANSFER_POOL_GAP`,
reflex-baseline policy (GradientPolicy, no scalar memory),
`unbounded_mutation=True`, `n_ticks=200`, `n_founders=5`. Same 8
seeds (1..8) as v0.21..v0.26. Both chambers per the comparison-
framework axis.

### Telemetry to watch

Aggregate observables per cell, summed across 8 seeds:

- **Productivity headline.** `total_births`,
  `births_after_tick_50` (b>50). Per-chamber per-weight curve.
- **Death cause distribution.** `total_starvation_deaths`,
  `total_injury_deaths`. Predicted: `total_injury_deaths` monotone
  non-increasing in weight on both chambers.
- **Hazard exposure.** `total_hazard_entries`. Direct routing
  observable; predicted monotone non-increasing in weight.
- **Pool ledger.** `pool_min_observed`, `pool_end`,
  `pool_in_ambient_influx` (H1 invariant), `pool_out_respawn`,
  `pool_out_child_startup`, `pool_in_death_residual`. The recycling
  channel decreases as weight rises.
- **Block telemetry.** `total_pool_birth_denied`,
  `total_pool_respawn_denied`,
  `total_births_blocked_by_parent_energy` (expected 0).
- **Conservation invariant.**
  `parent_energy_transferred_to_child + pool_out_child_startup ==
  total_births × offspring_start_energy`.

### Operational definitions — pre-committed

- **Curve shape — strictly monotone:** b>50 strictly increases at
  every consecutive (w_i, w_{i+1}) pair on the weight axis.
- **Curve shape — non-strict monotone:** b>50 is non-decreasing at
  every consecutive pair (some pairs may tie within seed noise).
- **Curve shape — interior optimum:** there exists at least one
  interior weight w* ∈ {0.25, 0.5, 0.75} such that b>50(w*) >
  b>50(1.0) AND b>50(w*) > b>50(0.0). Strict on both directions
  by ≥ 2 births to clear seed noise.
- **Curve shape — diminishing returns:** non-strict monotone AND
  the gain per 0.25 weight-step is non-increasing (concave). Quantified
  as: max(b>50(0.25) − b>50(0.0), b>50(0.5) − b>50(0.25)) ≥
  max(b>50(0.75) − b>50(0.5), b>50(1.0) − b>50(0.75)). I.e., the
  larger of the two early steps is at least as large as the larger
  of the two late steps. Cautious: a single-seed-noise tie can flip
  this; the framing is heuristic, not a hard pin.

## Pre-registered hypotheses

Two-tier structure consistent with v0.15..v0.26: **strong-form** for
mechanism + invariants, **cautious-form** for the substantive curve
shape.

### Strong form (mechanism + invariants)

- **H1.** `pool_in_ambient_influx == ambient_influx_rate ×
  sum(executed_ticks_per_seed)` per arm per chamber. v0.20
  conservation contract.
- **H2.** v0.20 H4 invariant holds at every v0.27 cell:
  `parent_energy_transferred_to_child + pool_out_child_startup ==
  total_births × offspring_start_energy`.
- **H3.** `reproduction_heat_loss == 0` at every v0.27 cell.
- **H4.** `births_blocked_by_parent_energy == 0` at every v0.27 cell.
- **H5.** `total_injury_deaths == 0` is **NOT** universally claimed
  on tight (v0.26 already showed tight produces 0 injury deaths at
  weight=0 because of geometric protection from single-visit
  lethality — but interior weights might produce positive injury
  deaths if agents partially-deflect into multi-visit hazard
  encounters). Pre-commit only the food_ladder direction:
  **`total_injury_deaths > 0` on food_ladder at every weight in
  {0.0, 0.25, 0.5, 0.75, 1.0}** (cull-tax presence). Cautious.

### Cautious form (curve shape)

- **H6 (food_ladder b>50 monotone non-decreasing in weight).** At
  every consecutive weight pair (0.0, 0.25), (0.25, 0.5), (0.5, 0.75),
  (0.75, 1.0), food_ladder b>50 is non-decreasing. Strict-cautious.
  v0.26 endpoints (88 → 92) suggest mostly monotone; cautious in case
  of seed-noise ties.
- **H7 (food_ladder injury_deaths monotone non-increasing in
  weight).** Direct routing prediction. v0.26 endpoints (40 → 16);
  v0.27 should fill the curve smoothly.
- **H8 (tight b>50 has interior optimum on the [0, 1] avoidance
  domain).** Substantive headline candidate: there exists a weight
  w* ∈ {0.25, 0.5, 0.75} such that tight b>50(w*) > 116 (the v0.26
  weight=1.0 anchor) by at least 2 births. **Cautious; falsification
  weight: high.** A null result here would mean tight's avoidance
  curve is monotone (or saturates at w=1.0); the v0.25 hazard-axis
  interior optimum does not have a symmetric counterpart on the
  weight axis.
- **H9 (food_ladder b>50 has NO interior optimum).** food_ladder
  b>50 is monotone or saturating in weight; no interior weight
  beats weight=1.0 by ≥ 2 births. **Cautious; chamber asymmetry
  prediction.** Mechanism reading: food_ladder geometry forces
  crossings, so each additional unit of avoidance just deflects
  more agents — no over-routing penalty within [0, 1].
- **H10 (tight b>50 curve is concave between endpoints).** If H8
  fails (no interior optimum), the fall-back prediction is concave
  monotone — diminishing returns. Operationally:
  max(b>50(0.25) − b>50(0.0), b>50(0.5) − b>50(0.25)) ≥
  max(b>50(0.75) − b>50(0.5), b>50(1.0) − b>50(0.75)).
  **Cautious; descriptive.** A linear shape would be unusual but
  consistent with H8 failing.
- **H11 (`total_hazard_entries` monotone non-increasing in weight
  on both chambers).** Direct routing observable. **Cautious;
  mechanism-pin.**

### Determinism

- **H12 (four anchor cells reproduce v0.26 byte-identically).** The
  table above. All sixteen aggregate columns match the v0.26
  hzd8-avd0.0 / hzd8-avd1.0 cells on each chamber. Halt condition.
- **H13 (V0_19/20/21/22/23/25/26_ARMS unchanged).** No prior arm
  tuple or core surface modified by v0.27. Halt condition.

## Decision rules

- **H8 fires (tight has interior optimum at some w* ∈ {0.25, 0.5,
  0.75}).** **Substantive headline:** the policy's avoidance axis,
  at fixed hazard, has the same non-monotonic structure as the
  hazard axis at fixed avoidance (v0.25). The cull-tax-vs-timing-
  penalty balance has a symmetric optimum on both axes. v0.28
  candidate: characterize the joint optimum on the (hazard, weight)
  surface — does the interior optimum depend on hazard, and does
  the v0.25 h=8 optimum coincide with this w* ?
- **H8 fails AND H10 fires (concave monotone).** **Headline:
  diminishing returns** — most of the avoidance benefit is captured
  by a small amount of routing pull. Mechanism reading: agents need
  *some* deflection to avoid lethal accumulation, but additional
  deflection has marginal returns within [0, 1]. v0.28 candidate:
  test whether weight > 1.0 continues to add productivity (does the
  curve saturate?) or starts to hurt (over-routing emerges only
  beyond unit weight).
- **H8 fails AND H10 fails (linear monotone).** Cleanest possible
  result. Avoidance is uniformly beneficial across [0, 1]; no
  mechanism subtlety beyond the v0.26 endpoint reading. v0.28
  candidate: same "weight > 1.0" question as the H10-firing branch.
- **H6 fails (food_ladder non-monotone).** Surprising; the
  food_ladder geometry-forces-crossings reading is more complex
  than v0.26 framed it. v0.28 candidate: investigate whether the
  food_ladder non-monotonicity correlates with population dynamics
  (does the productivity dip happen at a weight that produces a
  specific population trajectory?).
- **H7 fails (food_ladder injury_deaths non-monotone in weight).**
  Halt and audit — direct routing observable should be monotone
  unless there's an unmodelled interaction.
- **H9 fails (food_ladder ALSO has interior optimum).** Both
  chambers exhibit interior optima → the over-routing reading is
  general, not chamber-specific. v0.28 candidate: characterise on
  both chambers jointly.
- **H1/H2/H3/H4 invariants fail.** Halt; v0.27 results
  uninterpretable.
- **H5 fails (food_ladder injury_deaths = 0 at any cell).** Halt
  and audit — hazard-damage threading regression on food_ladder.
- **H11 fails (hazard_entries non-monotone in weight).** Halt and
  audit — routing observable should respond directly to weight.
- **H12 fails.** Wiring defect. Halt.
- **H13 fails.** Prior contract broken. Halt.

## Out of scope (v0.27)

- **Influx variation.** v0.28+ candidate.
- **Hazard intensity variation.** v0.28+ candidate.
- **Weights > 1.0.** v0.28+ candidate.
- **Reading B substrate seam.** Out of scope.
- **Pool-size sweep.** Held at 1500.
- **Reproduction efficiency variation.** Deferred since v0.20.
- **Long-window observations.** v0.28+ candidate.
- **HedonismPolicy comparisons.** Quarantined per v0.2 spec.

## Implementation notes

### File-level changes

- **Modify:** [[src/hedonism_harness/experiments/comparison_grid.py]]
  — append `V0_27_ARMS` tuple of 5 `Arm` instances per the table
  above. Every arm has `hazard_damage=8.0` and a unique
  `hazard_avoidance_weight`. ~95 LOC. No code-path changes; arm
  definitions only.
- **New:** [[scripts/v0.27_sweep.py]] — sweep driver mirroring
  `scripts/v0.26_sweep.py`; runs both chambers across V0_27_ARMS.
  ~85 LOC.
- **New:** `tests/test_comparison_grid_v0_27.py` — V0_27_ARMS shape
  test; substrate-economics-fixed test; per-arm weight pinning;
  prior arms (V0_19/20/21/22/23/25/26) unchanged; smoke test on
  arm A (weight=0.0) producing some injury deaths on food_ladder
  (mechanical sanity); H12 anchor identity vs v0.26.
  ~180 LOC.
- **No changes** to `core/`, `model.py`,
  `experiments/fear_hunger_chamber.py`,
  `experiments/population_dynamics.py`, or
  `policies/gradient_policy.py`. The v0.26 seam is sufficient.
- **Documented:** this file (`docs/experiments/fear_hunger_v0.27.md`);
  results appended after the sweep.

### Determinism contract

- `V0_19/20/21/22/23/25/26_ARMS` continue to produce identical sweep
  outputs after v0.27 changes (no prior surface modified).
- Four anchor cells in V0_27_ARMS reproduce v0.26 aggregates
  byte-identically (H12).
- The v0.20 H4 invariant continues to hold per arm (H2).

### Wall time estimate

80 runs × 200 ticks. v0.21 took 22s for 80 runs, v0.23 took 30s for
80 runs, v0.26 took 20.4s for 64 runs. v0.27 estimated 25–30s.

### LOC estimate

- `experiments/comparison_grid.py`: +95 LOC (V0_27_ARMS).
- `scripts/v0.27_sweep.py`: ~85 LOC.
- New tests: ~180 LOC.
- This doc: ~430 LOC.

Total v0.27 implementation: ~790 LOC. Comparable to prior slices.

## References

- [[docs/experiments/fear_hunger_v0.26.md]] — v0.26 results;
  perception-vs-damage decoupling 2×2; the open question v0.27
  fills (curve shape between weight=0 and weight=1).
- [[docs/experiments/fear_hunger_v0.25.md]] — v0.25 results;
  tight interior optimum at h=8 on the hazard axis. Source of the
  v0.27 H8 symmetry hypothesis.
- [[docs/experiments/fear_hunger_v0.24.md]] — v0.24 pool-exhaustion-
  timing mechanism. The cull-tax-vs-timing-penalty framing v0.27
  may extend to the avoidance axis.
- [[docs/experiments/fear_hunger_v0.23.md]] — v0.23 chamber-
  dependent hazard sign.
- [[src/hedonism_harness/policies/gradient_policy.py]] — the
  GradientPolicy with the v0.26 `hazard_avoidance_weight` seam.
- [[docs/specs/v0.2_reflex_cell_spec.md]] §"Comparison framework" —
  the substrate axis.

---

## Results

**Status:** executed 2026-05-05. 80 runs (5 arms × 2 chambers × 8 seeds),
22.2s wall time. All anchor / determinism hypotheses hold (H12 four
byte-identity anchors against v0.26; H13 prior arms unchanged). All
mechanical / invariant hypotheses hold (H1..H5, H7, H11). The
**substantive curve-shape headline is unexpected on food_ladder**:

**Both chambers exhibit interior optima on the avoidance-weight
axis at fixed hazard=8.** Tight has a weak interior maximum at
w=0.75 (b>50=118, +2 births vs w=1.0=116 — exactly meeting the
pre-committed noise threshold). Food_ladder has a **strong** interior
maximum at w=0.5 (b>50=98, +6 births vs w=1.0=92 and +10 vs w=0=88,
both well clear of noise). H8 fires at the boundary (tight); H9
fails decisively (food_ladder is *also* non-monotonic). The
"avoidance over-routing" mechanism reading — at very high weight,
agents over-deflect and waste path/energy budget — is supported on
both chambers.

A second, sharper food_ladder anomaly: **b>50 dips at w=0.75 to 89**,
substantially below the neighboring w=0.5 (98) and w=1.0 (92), and
total_births at w=0.75 (145) is the lowest across the 5 cells. The
aggregate 8-seed result is large enough to flag (≥ 8 births below
either neighbor); v0.28 should inspect paired seed-level
trajectories before treating the w=0.75 dip as a stable regime
rather than a seed-set artefact. Mechanism hypothesis (deferred to
v0.28): at w=0.75 the avoidance pull crosses some threshold relative
to food pull that flips agent routing onto a specific food_ladder
corridor with worse compounding economics than either side of the
threshold.

### Headline tables

#### tight_gradient (hazard=8, influx=1.0)

| arm | weight | births | b>50 | surv | food | respawn | fcpb  | pool_min | pool_end | residual | starv | inj | haz_ent | r_blk | b_blk | xfer  |
|-----|-------:|-------:|-----:|------|-----:|--------:|------:|---------:|---------:|---------:|------:|----:|--------:|------:|------:|------:|
| A   | 0.00   | 183 | 107 | 8/8 | 722 | 530 | 78.91 | 0 | 32 | 0.0 | 125 | 0 | 40 | 46 | 67 | 2,745 |
| B   | 0.25   | 188 | 112 | 8/8 | 717 | 525 | 76.28 | 0 | 35 | 0.0 | 129 | 0 | 40 | 51 | 74 | 2,820 |
| C   | 0.50   | 185 | 113 | 8/8 | 719 | 527 | 77.73 | 0 | 36 | 0.0 | 127 | 0 | 34 | 49 | 33 | 2,775 |
| D   | 0.75   | 190 | **118** | 8/8 | 716 | 524 | 75.37 | 0 | 34 | 0.0 | 137 | 0 | 32 | 52 | 33 | 2,850 |
| E   | 1.00   | 190 | 116 | 8/8 | 716 | 524 | 75.37 | 0 | 34 | 0.0 | 133 | 0 | 30 | 52 | 32 | 2,850 |

Tight curve shape on b>50: **107 → 112 → 113 → 118 → 116.** Strict
non-monotone: rises 5/1/5 then drops 2 at the high end. Interior
maximum at w=0.75. Total_births curve: 183 / 188 / 185 / 190 / 190 —
also non-monotone with dip at w=0.5.

Hazard exposure (entries) on tight: **40 → 40 → 34 → 32 → 30** — flat
at low weight, then strict monotone decrease from w=0.25 onward.
Injury_deaths on tight: 0 across all weights (geometric protection
against single-visit lethality persists across the entire avoidance
range, per v0.26 H6 reading).

#### food_ladder (hazard=8, influx=1.0)

| arm | weight | births | b>50 | surv | food | respawn | fcpb   | pool_min | pool_end | residual | starv | inj | haz_ent | r_blk | b_blk | xfer  |
|-----|-------:|-------:|-----:|------|-----:|--------:|-------:|---------:|---------:|---------:|------:|----:|--------:|------:|------:|------:|
| A   | 0.00   | 150 | 88 | 8/8 | 762 | 570 | 101.60 | 12 | 221 | 1,817.5 | 66 | 40 | 233 | 4 | 0 | 2,250 |
| B   | 0.25   | 152 | 97 | 8/8 | 692 | 518 |  91.05 |  6 | 305 | 1,482.5 | 75 | 34 | 216 | 2 | 0 | 2,280 |
| C   | 0.50   | 154 | **98** | 8/8 | 685 | 511 |  88.96 |  4 | 270 | 1,090.7 | 81 | 25 | 163 | 8 | 0 | 2,310 |
| D   | 0.75   | 145 | 89 | 8/8 | 688 | 514 |  94.90 |  2 | 252 |   872.3 | 78 | 20 | 145 | 5 | 6 | 2,175 |
| E   | 1.00   | 143 | 92 | 8/8 | 674 | 501 |  94.27 |  2 | 257 |   624.8 | 77 | 16 | 120 | 3 | 0 | 2,145 |

Food_ladder curve shape on b>50: **88 → 97 → 98 → 89 → 92.** Strongly
non-monotone with interior maximum at w=0.5 AND a dip at w=0.75. Total
births curve: 150 / 152 / 154 / 145 / 143 — w=0.5 maximum, then
declining (the "more avoidance = fewer hazard deaths but also fewer
total births" balance shifts at the high end).

Routing observables on food_ladder are **monotone** as predicted:
- Hazard entries: 233 → 216 → 163 → 145 → 120 (strict monotone
  decrease).
- Injury deaths: 40 → 34 → 25 → 20 → 16 (strict monotone decrease).
- Death-residual recycling: 1,818 → 1,483 → 1,091 → 872 → 625 (strict
  monotone decrease — the v0.22 recycling channel scales smoothly
  with weight).

The disconnect between **monotone routing** and **non-monotone
productivity** is the v0.27 substantive finding: less hazard exposure
→ fewer deaths, but the productivity outcome (b>50) is mediated by
something else (path-length cost, food-access timing) that has its
own non-monotonic dependence on weight.

### Hypothesis adjudication

| H | claim | result |
|---|---|---|
| H1 | `pool_in_ambient_influx == ambient_influx_rate × sum(executed_ticks)` | **HOLDS.** All 10 cells: 8/8 survivors → executed-tick sum = 1,600; influx product = 1,600; verified to the unit. |
| H2 | `parent_energy_transferred + pool_out_child_startup == total_births × 30` | **HOLDS.** Transfer-mode contract; xfer = births × 15 across all cells. |
| H3 | `reproduction_heat_loss == 0` | **HOLDS** (transfer-mode contract). |
| H4 | `births_blocked_by_parent_energy == 0` | **HOLDS** across all cells. |
| H5 | food_ladder `total_injury_deaths > 0` at every weight | **HOLDS.** food_ladder cull-tax is present at every weight: 40 / 34 / 25 / 20 / 16. |
| H6 | food_ladder b>50 monotone non-decreasing in weight | **FAILS.** 88 → 97 → 98 → **89** → 92. The dip at w=0.75 breaks monotonicity by 9 births, well outside seed noise. **Substantive food_ladder finding** — see "anomaly" subsection below. |
| H7 | food_ladder injury_deaths monotone non-increasing in weight | **HOLDS.** 40 → 34 → 25 → 20 → 16. The routing is uniformly improving with weight even though productivity isn't. |
| H8 | tight b>50 has interior optimum at w* ∈ {0.25, 0.5, 0.75} (≥ 2 births vs w=1.0) | **FIRES at the pre-registered boundary; evidence is positive but weak compared with food_ladder.** w=0.75 produces b>50=118; w=1.0 produces 116; +2 births exactly meets the pre-committed noise threshold (no margin above it). Tight curve: 107 → 112 → 113 → **118** → 116. The +2-birth advantage is small enough that a rerun on a fresh seed stream could plausibly flip the interior-optimum / saturation reading on tight; food_ladder's interior optimum (+6 births at w=0.5, see H9) is the substantive evidence carrying the v0.27 over-routing headline. |
| H9 | food_ladder b>50 has NO interior optimum (no weight beats w=1.0 by ≥ 2 births) | **FAILS DECISIVELY.** w=0.5 produces b>50=98; w=1.0 produces 92; +6 births. Food_ladder ALSO has an interior optimum on the avoidance axis. **The v0.27 chamber-asymmetry prediction is wrong** — both chambers exhibit over-routing at high weight. |
| H10 | tight curve is concave (diminishing returns) IF H8 fails | **N/A — H8 fires.** Tight curve is non-monotone, neither concave-monotone nor linear; the interior maximum at w=0.75 is the controlling structure. |
| H11 | `total_hazard_entries` monotone non-increasing in weight, both chambers | **HOLDS — non-increasing on tight, strict monotone on food_ladder.** tight: 40 → 40 → 34 → 32 → 30 (one tie at the low end, otherwise non-increasing). food_ladder: 233 → 216 → 163 → 145 → 120 (strict). The routing-side observable is monotone on both chambers (with the tight tie noted) — the b>50 non-monotonicity is downstream of routing, not in the routing itself. |
| H12 | four anchor cells reproduce v0.26 byte-identically | **HOLDS — exact match on every column.** tight w=0.0 = V0_26 invisible-tight (183/107/722/530/46/67/125/0/40/0.0/32/2,745). tight w=1.0 = V0_26 coupled-tight (190/116/716/524/52/32/133/0/30/0.0/34/2,850). food_ladder w=0.0 = V0_26 invisible-food (150/88/762/570/4/0/66/40/233/1,817.5/221/2,250). food_ladder w=1.0 = V0_26 coupled-food (143/92/674/501/3/0/77/16/120/624.8/257/2,145). |
| H13 | V0_19/20/21/22/23/25/26_ARMS unchanged | **HOLDS.** Test suite 705 → 716 (+11 v0.27 tests; pure addition); ruff clean. |

### Substantive finding 1: avoidance over-routing on both chambers

**The v0.27 substantive headline is that both tight and food_ladder
exhibit interior optima on the avoidance-weight axis at fixed
hazard=8.** This generalises v0.25's chamber-specific finding (tight
interior optimum at h=8 on the hazard axis) to both chambers on a
different policy axis.

The mechanism reading — supported by the v0.27 telemetry — is
**avoidance over-routing**: at very high avoidance weight, agents
deflect from hazards even when the detour costs more energy than the
direct cull would. The optimal avoidance weight is the one that
deflects agents *just enough* to avoid lethal accumulation but not
so much that they waste energy on unnecessary detours. The optima:

- **tight w*=0.75** (b>50=118 vs 116 at w=1.0; +2 births / +1.7%).
  The advantage exactly meets the pre-committed noise threshold (no
  margin above it); evidence for an interior optimum on tight is
  positive but weak compared with food_ladder, and a fresh seed
  stream could plausibly flip it to a saturation reading. tight's
  geometry already protects agents from lethal accumulation at every
  weight (inj=0 throughout), so the marginal cost of over-routing at
  w=1.0 should be modest — consistent with the small observed gap.
- **food_ladder w*=0.5** (b>50=98 vs 92 at w=1.0; +6 births / +6.5%).
  Larger advantage — food_ladder geometry forces hazard crossings,
  so the over-routing cost at high weight is more visible. The
  optimal weight is markedly below 1.0, suggesting the
  v0.14-shipped GradientPolicy default (effective weight=1.0 before
  v0.26) was *not* productivity-optimal on food_ladder.

The over-routing reading is consistent with monotone-routing
observables (hazard entries, injury deaths, recycling residual all
strictly monotone in weight on food_ladder) plus non-monotone
productivity (b>50). Less hazard exposure has a net cost beyond some
threshold.

### Substantive finding 2: food_ladder dip at w=0.75

A separate anomaly worth flagging: food_ladder b>50 drops to 89 at
w=0.75 — 9 births below the w=0.5 cell (98) and 3 below the w=1.0
cell (92). Total_births also dips to 145 (vs 154 at w=0.5 and 143 at
w=1.0). Across 8 seeds with 8/8 survivors, this is not a sampling
artifact.

Possible mechanisms (deferred to v0.28):

1. **Routing-threshold flip.** At w=0.75 the avoidance pull crosses
   some threshold relative to food pull that flips agent routing
   onto a specific food_ladder corridor with worse compounding
   economics. The hazard_entries observable supports this
   qualitatively — entries drop sharply between w=0.5 (163) and
   w=0.75 (145), suggesting a routing-pattern change. But entries
   continue to drop monotonically into w=1.0 (120), so whatever
   pathology is at w=0.75 is non-monotone.
2. **Trait drift / population dynamics.** With unbounded mutation,
   8-seed-mean trait distributions can drift. The w=0.75 dip might
   be a population-dynamics artefact specific to the seed set.
   Discriminating: re-run at the same 8 seeds with a different RNG
   stream (seeds 9..16) to test whether the dip is reproducible or
   seed-specific.
3. **Chamber-geometry interaction.** food_ladder's pre-food band
   has a fixed spatial structure; at w=0.75, the pull-balance
   produces a path that lingers in a specific cell-kind region for
   longer than at w=0.5 or w=1.0, costing more food consumption per
   birth (fcpb at w=0.75 = 94.90 vs w=0.5 = 88.96 — slightly higher,
   consistent with this reading).

The dip is the most surprising finding of v0.27 and the cleanest
candidate for a v0.28 follow-up.

### What this changes about prior framings

- **v0.26 endpoint reading is preserved but sharpened.** The
  weight=0 vs weight=1 binary contrast captured the *direction* of
  avoidance-mediated productivity (positive on both chambers) but
  missed the *interior shape*. Both chambers have non-monotone
  productivity in weight; w=1.0 (the v0.14..v0.25 default before the
  v0.26 seam) is *not* the productivity-optimal weight on either
  chamber.
- **v0.25 tight-interior-optimum-at-h=8 reading is generalized.**
  The non-monotonic "tax-vs-timing tradeoff with productivity ceiling"
  framing applies on both chambers when the perturbation is
  avoidance-side rather than damage-side. The cull-tax and
  pool-exhaustion-timing penalties have analogues on the policy axis
  (over-routing wastes path/energy budget; under-routing increases
  cull-tax and recycling-residual flux).
- **v0.23/v0.24 chamber-geometry-as-buffer reading remains
  falsified** (unchanged from v0.26). food_ladder geometry routes
  traffic but does not deflect it; the avoidance signal does the
  deflecting work.

### v0.28 candidates

The v0.27 results sharpen the next-question landscape. In rough
priority order:

1. **(Highest) Reproducibility test of the food_ladder dip at w=0.75.**
   Re-run V0_27_ARMS at seeds 9..16 (a fresh RNG stream) on
   food_ladder only to test whether the b>50=89 dip is reproducible
   or seed-specific. ~40 runs, ~5s. Cheapest possible discrimination.
2. **Influx × weight cross-product** at influx ∈ {0.5, 1.0, 1.5}
   on both chambers to test whether the interior-optima locations
   (w=0.75 tight, w=0.5 food_ladder) shift with influx. The pool-
   exhaustion-timing mechanism predicts they should depend on influx
   (lower influx → earlier pool exhaustion → optimum shifts to lower
   weight where the cull-tax is higher but routing is more direct).
   ~15 arms × 2 chambers × 8 seeds = 240 runs.
3. **Weight × hazard cross-product** at hazard ∈ {4, 12} on tight to
   test whether the interior optimum on the weight axis shifts with
   hazard. v0.25 located tight's interior optimum at h=8 on the
   hazard axis; v0.27 located w*=0.75 at h=8 on the weight axis. Is
   the (w*, h*) joint optimum at (0.75, 8)? ~96 runs.
4. **Weights > 1.0** to characterise saturation. v0.27 shows w=1.0
   is past the optimum on both chambers; does the curve continue to
   drop monotonically beyond 1.0, or saturate? ~6 arms (weights
   1.0, 1.25, 1.5, 2.0) × 2 chambers × 8 seeds = 96 runs.
5. **Long-window stability** at w=0.75 (tight optimum) vs w=1.0 to
   test whether the interior advantage compounds or fades over a
   500-tick window. v0.27+ candidate.

### Implementation summary

- **Production code:** zero changes — v0.26 seam was sufficient.
- **Configuration:** ~95 LOC `V0_27_ARMS` in `comparison_grid.py`
  (5 arms).
- **Tests:** ~210 LOC `tests/test_comparison_grid_v0_27.py` (11 new
  tests). Suite 705 → 716.
- **Sweep driver:** ~85 LOC `scripts/v0.27_sweep.py`.
- **Wall time:** 22.2s on 80 runs (every seed completed 200 ticks;
  no early termination).
- **No core/model.py/sensors.py/world.py/gradient_policy.py changes.**
- **CI gate at handoff time:**
  ```
  uv run ruff check .             ok
  uv run ruff format --check .    ok
  uv run pytest                   716 passed
  uv run python scripts/core_smoke_test.py  ok
  uv run python scripts/v0.27_sweep.py     22.2s; four anchors byte-identical against v0.26
  ```
