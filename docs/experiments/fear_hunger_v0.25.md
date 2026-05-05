# v0.25 — hazard × influx timing-regulation sweep: testing pool-exhaustion-timing on both chambers

**Status:** pre-registration; not yet executed.
**Date:** 2026-05-05
**Branch:** `claude/v0.25-hazard-influx-timing-sweep`
**Predecessors:** v0.21 (chamber-asymmetric influx frontier at hazard=8;
food_ladder primary i\*=0.5/tick, tight primary i\*=1.5/tick), v0.22
(narrow hazard sweep on food_ladder at influx=1.0; recycling-as-net-tax
confirmed; food_ladder b>50 monotone non-increasing in hazard:
116/96/92/65), v0.23 (hazard-zero influx frontier on both chambers;
chamber-dependent hazard sign discovered — food_ladder gains ~+30
b>50 per arm when hazards removed, tight loses ~−13), v0.24
(population-dynamics diagnostic falsified the strict population-governor
"overshoot-and-crash" reading — late-window populations *rise* at
hazard=0 on both chambers, not crash. Substituting mechanism candidate:
**pool-exhaustion-timing** — earlier population peak under hazard=0
drains the pool earlier, throttling late-game births).
**Spec:** [[docs/specs/v0.2_reflex_cell_spec.md]] §"Comparison framework"
(substrate axis).

## Question

v0.24 surfaced **pool-exhaustion-timing** as the mechanism candidate
for v0.23's chamber-dependent b>50 sign. Under this reading the v0.23
finding is the relative magnitude of two effects that hazard damage
mediates simultaneously:

1. **Direct cull-tax.** Hazard kills agents directly, reducing total
   productivity. Large on food_ladder (per v0.22's recycling-as-
   net-tax — agents cross the pre-food band hazard repeatedly), small
   on tight (agents avoid the hazard wall via GradientPolicy routing
   when avoidance signal is active).
2. **Pool-exhaustion-timing.** Hazard cull *delays* the population
   peak; without the cull, founders bloom earlier, the pool drains
   earlier, and late-game births (b>50) are throttled. Symmetric
   on both chambers (v0.24 observed peak shifts of 26 ticks earlier
   on tight, 40 ticks earlier on food_ladder when hazards removed).

The chamber-dependent b>50 sign is whichever effect dominates:
- **food_ladder** at hazard=0: cull-tax relief (large) > timing penalty
  (large but smaller magnitude on b>50). NET POSITIVE.
- **tight** at hazard=0: cull-tax relief (small) < timing penalty.
  NET NEGATIVE.

**v0.25 tests the pool-exhaustion-timing mechanism by sweeping hazard
× influx on both chambers.** The mechanism makes specific, falsifiable
predictions:

(a) **Tick of peak monotonically decreases as hazard decreases on
both chambers.** This is the direct timing observable — if the
hazard cull truly delays peak, removing more cull should systematically
shift peak earlier. Mechanism-pinning.

(b) **food_ladder b>50 monotone non-increasing in hazard at every
shared influx.** The cull-tax dominates throughout on food_ladder;
reducing hazard always helps. Already supported by the v0.22 narrow
sweep at influx=1.0 (b>50: 116/96/92/65 across hazards 0/4/8/12);
v0.25 verifies the monotonicity survives at influx ∈ {0.5, 1.5}.

(c) **tight b>50 non-monotonic in hazard at some shared influx.**
The cull-tax (small) and timing penalty (large) net out non-monotonically
on tight; some intermediate hazard maximises b>50. v0.21 anchored
hazard=8 at b>50=116; v0.23 anchored hazard=0 at b>50=100. v0.25 should
locate hazards in {4, 12} that produce b>50 outside the [100, 116]
interval — strict non-monotonicity (some hazard value's b>50
exceeds both 100 and 116) confirms the mechanism.

If (a) holds AND (b) holds AND (c) holds, pool-exhaustion-timing is
confirmed and v0.26 (perception-vs-damage decoupling) becomes the
clean next slice.

## What this slice tests, and what it does NOT test

### Tests

- **The shape of b>50 vs hazard on each chamber, at three influxes.**
  Monotone vs non-monotone, where any optima sit.
- **The shape of tick-of-peak vs hazard on each chamber.**
  Monotonic timing prediction.
- **The shape of peak population vs hazard on each chamber.**
  Cull-strength prediction.
- **Whether the v0.22 food_ladder monotonicity (b>50 116/96/92/65 at
  influx=1.0) generalises to other influxes.**
- **Whether tight at intermediate hazard (4 or 12) produces b>50
  outside the v0.21 (h=8: 116) and v0.23 (h=0: 100) anchors.**

### Does NOT test

- **The avoidance-routing alternative.** v0.25 does not decouple the
  GradientPolicy avoidance signal from the per-tile damage value;
  changes in `hazard_damage` change both. v0.26 candidate.
- **Long-window stability** (n_ticks > 200). Same window as
  v0.21/v0.22/v0.23/v0.24.
- **Pool-size sensitivity.** Pool=1500 throughout (v0.21+ anchor).
- **Reproduction efficiency variation.** Transfer mode throughout.
- **HedonismPolicy comparisons.** Quarantined.
- **Influx grid extension.** Influxes restricted to {0.5, 1.0, 1.5}
  — the transition region. Endpoints (0 and 2) covered by v0.23.

### Deferred (v0.26+ candidates, conditional on v0.25 outcome)

- **v0.26 (if H5/H6/H7 fire):** decouple `hazard_damage` from
  `hazard_avoidance_weight` in `GradientPolicy`. Tests whether the
  avoidance-routing reading is independently important once the
  pool-exhaustion-timing mechanism is characterised.
- **v0.27+ (further deferred):** long-window stability, pool-size
  sweep at hazard=0, reproduction-efficiency variation,
  HedonismPolicy on conservation substrate (still quarantined).

## Conservation framing — unchanged from v0.20/v0.21/v0.22/v0.23

v0.25 introduces no new mechanism. The six-flow conservation
bookkeeping under PARENT_TRANSFER_POOL_GAP is preserved exactly:

```
Parent: -reproduction_cost   (15, transferred to child via system ledger)
Pool:   -(offspring_start_energy - reproduction_cost)   (15, gap)
Pool:   +ambient_influx_rate per tick   (variable, 0.5 → 1.5 across arms)
Pool:   +max(0, body.energy) on AgentDied   (death residual; non-zero
                                              under hazard > 0 INJURY deaths)
Child:  +offspring_start_energy   (30)
System energy delta per birth: 0   (no heat loss at reproduction)
```

The two knobs that vary across the v0.25 sweep are
`hazard_damage` ∈ {0, 4, 8, 12} and `ambient_influx_rate` ∈
{0.5, 1.0, 1.5} (a 4 × 3 = 12-arm grid). Chambers (food_ladder,
tight_gradient) are the second axis. All other parameters held
constant: `reproduction_cost=15`, `offspring_start_energy=30`,
`pool_initial=1500`, `food_respawn_cooldown=50`,
`child_funding_mode=PARENT_TRANSFER_POOL_GAP`, reflex-baseline
policy, `unbounded_mutation=True`, `n_ticks=200`, `n_founders=5`.

### Why these influx points

`{0.5, 1.0, 1.5}` is the transition region of the v0.21/v0.23
influx frontier. Endpoint 0 (closed-pool) and endpoint 2.0
(saturation) are already mapped at hazard=0 (v0.23) and hazard=8
(v0.21); v0.25 does NOT re-run them. Restricting to the transition
region keeps the design compact (192 runs total) while covering
the regime where pool-exhaustion-timing should produce its
strongest non-monotonicity signal.

### Why these hazards

`{0, 4, 8, 12}` matches v0.22's hazard sweep grid (which had a
single influx point on food_ladder only). Extending the same
hazard grid to three influxes on both chambers tests the
v0.22 monotonicity claim broadly and locates any non-monotonic
optimum on tight.

## Mechanism

**No new code paths in `core/`, `model.py`, or `fear_hunger_chamber.py`.**
The seam v0.22 shipped (`Arm.hazard_damage`, `total_injury_deaths`)
already supports per-arm hazard variation. v0.25 is purely
configuration:

- A new `V0_25_ARMS` tuple in
  [[src/hedonism_harness/experiments/comparison_grid.py]]
  consisting of 12 `Arm` instances at the (hazard, influx) grid
  above. ~180 LOC. Mirrors `V0_22_ARMS` (hazard variation) ×
  `V0_23_ARMS` (influx variation) patterns.
- A new sweep driver
  [[scripts/v0.25_sweep.py]] mirroring `scripts/v0.23_sweep.py`
  but iterating across the 12 arms × 2 chambers. ~110 LOC.
- A new test module
  `tests/test_comparison_grid_v0_25.py` (~180 LOC) pinning the
  arm grid, substrate, and prior-arms-unchanged guards.

The v0.20/v0.21/v0.22/v0.23 telemetry is sufficient for the
mechanism analysis. The v0.24 population-dynamics library
(`src/hedonism_harness/experiments/population_dynamics.py`) is
re-used by the sweep results doc to compute tick-of-peak across
the v0.25 cells.

### Determinism — anchors

V0_25_ARMS contains 14 byte-identity anchors against prior sweep
artifacts (existing on disk after v0.21, v0.22, v0.23 sweeps run
this session):

| chamber | hazard | influx | anchor source | b>50 anchor |
|---|---:|---:|---|---:|
| tight       | 0 | 0.5 | v0.23 arm B (transfer-1500-hzd0-influx-0.5)  |  97 |
| tight       | 0 | 1.0 | v0.23 arm C (transfer-1500-hzd0-influx-1.0)  | 100 |
| tight       | 0 | 1.5 | v0.23 arm D (transfer-1500-hzd0-influx-1.5)  | 107 |
| tight       | 8 | 0.5 | v0.21 arm B (transfer-1500-influx-0.5)       | 111 |
| tight       | 8 | 1.0 | v0.21 arm C (transfer-1500-influx-1.0)       | 116 |
| tight       | 8 | 1.5 | v0.21 arm D (transfer-1500-influx-1.5)       | 125 |
| food_ladder | 0 | 0.5 | v0.23 arm B (transfer-1500-hzd0-influx-0.5)  | 113 |
| food_ladder | 0 | 1.0 | v0.23 arm C (transfer-1500-hzd0-influx-1.0)  | 116 |
| food_ladder | 0 | 1.5 | v0.23 arm D (transfer-1500-hzd0-influx-1.5)  | 125 |
| food_ladder | 4 | 1.0 | v0.22 arm hazard-4                           |  96 |
| food_ladder | 8 | 0.5 | v0.21 arm B (transfer-1500-influx-0.5)       |  85 |
| food_ladder | 8 | 1.0 | v0.21 arm C (= v0.22 hazard-8 anchor)        |  92 |
| food_ladder | 8 | 1.5 | v0.21 arm D (transfer-1500-influx-1.5)       |  92 |
| food_ladder | 12 | 1.0 | v0.22 arm hazard-12                         |  65 |

Failure of any anchor is a halt condition — the v0.25
configuration must reproduce prior aggregates byte-identically
because the substrate is unchanged and the same seeds are used.

The 10 truly new (chamber, hazard, influx) cells are:
- (tight, 4, 0.5), (tight, 4, 1.0), (tight, 4, 1.5)
- (tight, 12, 0.5), (tight, 12, 1.0), (tight, 12, 1.5)
- (food_ladder, 4, 0.5), (food_ladder, 4, 1.5)
- (food_ladder, 12, 0.5), (food_ladder, 12, 1.5)

These 10 cells carry the substantive new information.

## Arms

Twelve arms × two chambers × eight seeds = **192 runs**.

| arm | hazard | influx | label |
|---|---:|---:|---|
| A1 | 0  | 0.5 | transfer-1500-hzd0-influx-0.5 |
| A2 | 0  | 1.0 | transfer-1500-hzd0-influx-1.0 |
| A3 | 0  | 1.5 | transfer-1500-hzd0-influx-1.5 |
| B1 | 4  | 0.5 | transfer-1500-hzd4-influx-0.5 |
| B2 | 4  | 1.0 | transfer-1500-hzd4-influx-1.0 |
| B3 | 4  | 1.5 | transfer-1500-hzd4-influx-1.5 |
| C1 | 8  | 0.5 | transfer-1500-hzd8-influx-0.5 |
| C2 | 8  | 1.0 | transfer-1500-hzd8-influx-1.0 |
| C3 | 8  | 1.5 | transfer-1500-hzd8-influx-1.5 |
| D1 | 12 | 0.5 | transfer-1500-hzd12-influx-0.5 |
| D2 | 12 | 1.0 | transfer-1500-hzd12-influx-1.0 |
| D3 | 12 | 1.5 | transfer-1500-hzd12-influx-1.5 |

Substrate per arm: `energy_cost=15`, `energy_threshold=50`,
`offspring_start_energy=30`, `food_respawn_cooldown=50`,
`energy_pool_initial=1500`,
`child_funding_mode=PARENT_TRANSFER_POOL_GAP`, reflex-baseline policy,
`unbounded_mutation=True`, `n_ticks=200`, `n_founders=5`.

Same 8 seeds as v0.21/v0.22/v0.23 so per-seed cross-version
comparisons remain interpretable. Both chambers (food_ladder,
tight_gradient) per the comparison-framework axis.

### Telemetry to watch

Aggregate observables (per cell, summed across 8 seeds):

- **Productivity headline.** `total_births`, `births_after_tick_50`
  (b>50), `seeds_with_survivors`, `population_end`.
- **Death cause distribution.** `total_starvation_deaths`,
  `total_injury_deaths`. Hazard sweep should produce monotonic
  `total_injury_deaths` with hazard.
- **Pool ledger.** `pool_min_observed`, `pool_end`,
  `pool_in_ambient_influx` (H1 invariant), `pool_out_respawn`,
  `pool_out_child_startup`, `pool_in_death_residual`.
- **Block telemetry.** `total_pool_birth_denied`,
  `total_pool_respawn_denied`,
  `total_births_blocked_by_parent_energy` (expected 0).
- **Hazard exposure.** `total_hazard_entries`.
- **Conservation invariant.**
  `parent_energy_transferred_to_child + pool_out_child_startup ==
  total_births × offspring_start_energy`.

Population-dynamics observables (per cell, computed by the v0.24
library on the v0.25 events.jsonl):

- **Mean peak population per run** (from
  `PopulationTrajectory.peak_population`).
- **Mean tick of peak** (from `tick_of_peak`).
- **Mean late-window population** (t ≥ 100).
- **Lifespan p50, p90.**

The sweep driver computes the aggregate telemetry directly via
`run_comparison_grid`; the population-dynamics observables are
computed in a follow-up pass on the resulting events.jsonl files
using the v0.24 library.

## Pre-registered hypotheses

Two-tier structure consistent with v0.15..v0.24: **strong-form** for
mechanism + invariants, **cautious-form** for the substantive
mechanism predictions, plus **determinism** for the byte-identity
anchors.

### Strong form (mechanism + invariants)

- **H1.** `pool_in_ambient_influx == ambient_influx_rate ×
  sum(executed_ticks_per_seed)` per arm per chamber. The v0.20
  conservation contract.
- **H2.** v0.20 H4 invariant holds at every v0.25 cell:
  `parent_energy_transferred_to_child + pool_out_child_startup ==
  total_births × offspring_start_energy`.
- **H3.** `reproduction_heat_loss == 0` at every v0.25 cell
  (transfer mode contract).
- **H4.** `births_blocked_by_parent_energy == 0` at every v0.25 cell.
- **H5.** `total_injury_deaths == 0` at every hazard=0 cell;
  `total_injury_deaths > 0` at every hazard > 0 cell. Threading
  proof.

### Cautious form (pool-exhaustion-timing predictions)

- **H6 (tick-of-peak monotonic in hazard, both chambers).** At every
  shared influx, mean tick-of-peak monotonically *decreases* as hazard
  decreases (or equivalently: increases as hazard increases). Direct
  mechanism observable. **Strong-cautious; falsification weight: high.**
  If tick-of-peak is non-monotonic in hazard, the timing mechanism
  is wrong.

- **H7 (food_ladder b>50 monotone non-increasing in hazard).** At every
  shared influx ∈ {0.5, 1.0, 1.5}, food_ladder mean b>50 is
  monotone non-increasing in hazard across hazards 0 → 4 → 8 → 12.
  cull-tax dominates throughout. **Strong-cautious.** v0.22 already
  established this at influx=1.0; H7 verifies it generalises.

- **H8 (tight b>50 non-monotonic in hazard at some shared influx).**
  At at least one shared influx ∈ {0.5, 1.0, 1.5}, tight b>50 has a
  strict interior maximum: there exists a hazard h* ∈ {4, 8} such
  that tight b>50 at h* exceeds tight b>50 at both h=0 and h=12.
  **Cautious; the substantive headline.** If tight b>50 is monotone
  in hazard at every shared influx, the cull-tax is either
  negligible (entire effect is timing) or tight has its own
  monotonic relationship and the v0.23 chamber-dependence is more
  complicated than pool-exhaustion-timing alone explains.

- **H9 (peak population monotone non-increasing in hazard, both
  chambers).** Stronger hazard reduces peak via direct cull. At every
  shared influx, peak population on each chamber decreases as hazard
  increases. **Cautious; corroborating mechanism observable.** v0.24
  established the endpoints (peak↑ at hazard=0 vs hazard=8 on both
  chambers); H9 verifies the monotonic shape at intermediate
  hazards.

- **H10 (total_injury_deaths monotone non-decreasing in hazard).** At
  every shared influx and chamber, `total_injury_deaths` increases
  with hazard. Mechanical sanity check on the cull strength.
  **Cautious.**

### Determinism

- **H11 (byte-identity on the 14 anchors).** All 14 anchor cells
  (listed in the table above) reproduce prior aggregates byte-identically
  on every column (`total_births`, `births_after_tick_50`,
  `total_food_events`, `total_food_respawn_events`,
  `total_pool_respawn_denied`, `total_pool_birth_denied`,
  `total_starvation_deaths`, `total_injury_deaths`,
  `total_hazard_entries`, `pool_out_respawn`, `pool_out_child_startup`,
  `pool_in_death_residual`, `pool_min`, `pool_end`,
  `parent_energy_transferred_to_child`, `reproduction_heat_loss`).
  Halt condition. The substrate is unchanged and the same seeds are
  used, so this is a deductive identity.
- **H12 (V0_19/20/21/22/23_ARMS unchanged).** No prior arm tuple
  modified by v0.25 changes; every prior test continues to pass.

## Decision rules

- **H6 + H7 + H8 fire.** Pool-exhaustion-timing **confirmed**.
  Headline: hazard cull regulates timing on both chambers; the
  chamber-dependent v0.23 b>50 sign is the cull-tax-vs-timing-penalty
  balance. Commit to v0.26 (perception-vs-damage decoupling) as the
  next slice — the mechanism is settled enough that the avoidance-
  routing question becomes the next discriminator.

- **H6 fires + H7 holds + H8 fails (tight is monotone).**
  food_ladder behaves as predicted; tight does not have a non-monotonic
  interior maximum. Possibilities: (i) cull-tax on tight is so small
  that even small hazard hurts on net; (ii) the timing penalty
  asymmetry between chambers needs a different observable. Revise
  the chamber-dependence reading. v0.26 may pivot to first
  characterising why tight has no interior optimum (e.g., is the
  cull-tax on tight literally zero?) before doing perception
  decoupling.

- **H6 fires + H7 fails (food_ladder non-monotonic at some influx).**
  Unexpected. food_ladder also has a timing optimum at some hazard,
  contradicting the "cull-tax dominates throughout" reading. Revise
  the chamber-dependence story; investigate whether food_ladder's
  behaviour at high influx is qualitatively different from
  influx=1.0 (where v0.22 confirmed monotonicity).

- **H6 fails (tick-of-peak NOT monotone in hazard).** Pool-exhaustion-
  timing mechanism is wrong. Re-examine the v0.24 finding —
  possibly the peak shifts observed at the hazard=0/hazard=8
  endpoints are not driven by the cull-strength axis but by some
  other discontinuity. Consider promoting v0.26 (perception
  decoupling) earlier or designing a fresh diagnostic.

- **H1/H2/H3/H4/H5 invariants fail.** Halt; v0.25 results
  uninterpretable.

- **H10 fails (injury deaths not monotone in hazard).** Halt;
  threading regression in `Arm.hazard_damage` or in event
  emission.

- **H11 fails (byte-identity anchor breaks).** Wiring defect;
  halt and audit.

- **H12 fails.** Prior arm tuples broken; halt.

## Out of scope (v0.25)

- **Long-window observations.** v0.27+ candidate.
- **Pool-size sweep.** Held at 1500.
- **Influx grid extension** (re-running 0 and 2 endpoints).
  Already mapped at hazard=0 (v0.23) and hazard=8 (v0.21).
- **Reproduction efficiency variation.** Deferred since v0.20.
- **Perception vs damage decoupling.** v0.26 candidate.
- **Multi-cell-tier directional EMA.** Deferred until substrate
  question settled.
- **HedonismPolicy on conservation substrate.** Quarantined per
  v0.2 spec.

## Implementation notes

### File-level changes

- **Modify:** [[src/hedonism_harness/experiments/comparison_grid.py]]
  — append `V0_25_ARMS` tuple of 12 `Arm` instances per the table
  above. ~180 LOC. No code-path changes; arm definitions only.
- **New:** [[scripts/v0.25_sweep.py]] — sweep driver mirroring
  `scripts/v0.23_sweep.py`; runs both `tight_gradient` AND
  `food_ladder` over `V0_25_ARMS`. Headline table preserves the
  v0.22/v0.23 column structure. ~110 LOC.
- **New:** `tests/test_comparison_grid_v0_25.py` — V0_25_ARMS
  shape test; substrate-economics-fixed test; per-arm
  (hazard, influx) pinning; prior arms (V0_19/20/21/22/23)
  unchanged; smoke test on arm A2 (hazard=0, influx=1.0); H10
  mechanical-sanity test on a hazard>0 arm. ~180 LOC.
- **No changes** to `core/`, `model.py`,
  `experiments/fear_hunger_chamber.py`, or
  `experiments/population_dynamics.py`. The mechanism is unchanged;
  only configuration varies.
- **Documented:** this file (`docs/experiments/fear_hunger_v0.25.md`);
  results appended after the sweep.

### Determinism contract

- `V0_19_ARMS`, `V0_20_ARMS`, `V0_21_ARMS`, `V0_22_ARMS`, `V0_23_ARMS`
  continue to produce identical sweep outputs after v0.25 changes
  (no prior surface modified).
- 14 anchor cells in V0_25_ARMS reproduce prior aggregates
  byte-identically (H11).
- The v0.20 H4 invariant continues to hold per arm (H2).

### LOC estimate

- `experiments/comparison_grid.py`: +180 LOC (V0_25_ARMS).
- `scripts/v0.25_sweep.py`: ~110 LOC.
- New tests: ~180 LOC.
- This doc: ~520 LOC.

Total v0.25 implementation: ~990 LOC. Comparable to v0.21/v0.22/v0.23
because the doc + arms grid are slightly larger; no new mechanism.

### Wall time estimate

192 runs × 200 ticks. Based on v0.21's 22s for 80 runs and v0.23's
30s for 80 runs, scaling ~linearly: estimated 50–70s for the v0.25
sweep.

## References

- [[docs/experiments/fear_hunger_v0.24.md]] — v0.24 results;
  pool-exhaustion-timing mechanism candidate. Source of v0.25's
  H6 / H8 framing.
- [[docs/experiments/fear_hunger_v0.23.md]] — v0.23 results;
  chamber-dependent hazard sign and the i\* + absolute-productivity
  data. Source of 6 v0.25 anchors.
- [[docs/experiments/fear_hunger_v0.22.md]] — v0.22 results;
  food_ladder hazard monotonicity at influx=1.0
  (b>50: 116/96/92/65). Source of 3 v0.25 anchors.
- [[docs/experiments/fear_hunger_v0.21.md]] — v0.21 results;
  hazard=8 influx frontier on both chambers. Source of 6 v0.25
  anchors.
- [[docs/specs/v0.2_reflex_cell_spec.md]] §"Comparison framework"
  — the substrate axis.
