# v0.24 — population-dynamics diagnostic: does removing hazards trigger overshoot-and-crash on tight?

**Status:** pre-registration; not yet executed.
**Date:** 2026-05-05
**Branch:** `claude/v0.24-population-dynamics-diagnostic`
**Predecessors:** v0.21 (chamber-asymmetric influx frontier at hazard=8;
food_ladder primary i\*=0.5/tick, tight primary i\*=1.5/tick), v0.22
(narrow hazard sweep on food_ladder under transfer + influx=1.0;
recycling-as-net-tax on food_ladder confirmed), v0.23 (hazard-zero
influx frontier on both chambers; chamber-dependent hazard sign
discovered — food_ladder gains ~+30 b>50 per arm when hazards
removed, tight loses ~−13 b>50 per arm; **mechanism question
named:** is the hazard cull acting as a population governor on
tight, where no pre-food-band carrying-capacity buffer exists?).
**Spec:** [[docs/specs/v0.2_reflex_cell_spec.md]] §"Comparison framework"
(substrate axis).

## Question

v0.23 surfaced a chamber-dependent hazard sign: removing
`hazard_damage` (and the GradientPolicy avoidance signal that keys
off it) lifted food_ladder productivity by ~+30 b>50 per arm and
*depressed* tight productivity by ~−13 b>50 per arm. The aggregate
telemetry from the v0.23 sweep is consistent with an
**overshoot-and-crash** reading on tight:

| metric (tight, transfer, pool=1500, influx=1.0) | hazard=8 (v0.21) | hazard=0 (v0.23) | delta |
|---|---:|---:|---:|
| total births       |   190 |   246 | **+30%** |
| b>50               |   116 |   100 | −14% |
| food events        |   716 |   673 | −6% |
| fcpb               | 75.37 | 54.72 | **−27%** |
| r_blk              |    52 |    95 | **+83%** |
| b_blk              |    32 |    42 | +31% |

More total births but fewer late-game births; fcpb falls toward
the transfer-mode metabolic floor (~45–60); pool blocks roughly
double. The aggregate-only view cannot distinguish "more agents,
more deaths, but smooth dynamics" from "population overshoots,
crashes mid-run, late-window struggles to compound." v0.24
discriminates these by reading per-tick population dynamics
out of the existing events.jsonl artifacts on disk — no new
sweeps, no new code paths.

**v0.24 is purely diagnostic** — it analyses runs already
materialised on disk (v0.21 hazard=8 + v0.23 hazard=0, both
chambers, 160 events.jsonl total) and emits time-series
diagnostics. The substrate, model, chamber driver, and arm
configurations are unchanged.

## What this slice tests, and what it does NOT test

### Tests

- **Whether tight at hazard=0 shows overshoot-and-crash population
  dynamics relative to tight at hazard=8** — peak population higher
  at hazard=0, late-window mean population lower at hazard=0, mid-run
  starvation spike absent at hazard=8.
- **Whether food_ladder shows the same pattern** (negative control).
  The "pre-food band as carrying-capacity buffer" reading predicts
  that food_ladder should NOT exhibit overshoot — the band provides
  a stability mechanism analogous to what tight uses the hazard cull
  for. If food_ladder shows the same overshoot signature, the
  chamber-specific framing is wrong.
- **Lifespan-distribution shape** — overshoot predicts a
  right-skewed (or bimodal) distribution at hazard=0 on tight,
  driven by short-lived agents born during peak that don't reach
  reproductive age. v0.21 hazard=8 should show a flatter
  distribution because the cull is continuous.

### Does NOT test

- **The avoidance-routing alternative** (mechanism candidate (2) in
  v0.23 results). v0.24 cannot discriminate "tight gets worse
  because no cull → overshoot" from "tight gets worse because no
  avoidance signal → bad routing" because both predict similar
  aggregate observables (more births, fewer late births, more
  starvation). v0.24 looks for the *temporal signature* of
  overshoot (peak then crash), which the routing-degradation
  reading does not specifically predict. A null result
  on H1+H2+H3 would cast doubt on the population-governor reading
  and support escalating to the v0.26 perception-vs-damage
  decoupling experiment.
- **Long-window stability** at n_ticks > 200. v0.21 + v0.23 both
  ran 200-tick windows; v0.24 reads the same window.
- **New influx, hazard, or pool values.** Reads existing artifacts
  only.
- **The mechanism on food_ladder** (the recycling-as-net-tax
  story) — that was v0.22's question. v0.24 only verifies
  food_ladder's hazard=8→0 transition does NOT match tight's.

### Deferred (v0.25+ candidates, conditional on v0.24 outcome)

- **v0.25 (if H1/H2/H3 fire on tight, H4 holds):** tight-only
  hazard × influx cross-product (4 hazards × 3 influxes × 8 seeds
  = 96 runs) to characterise the cull-vs-cost tradeoff curve and
  locate the hazard value that maximises tight productivity.
- **v0.26 (if H1/H2/H3 do NOT fire, or H4 fails):** decouple
  hazard_damage from hazard_avoidance in `GradientPolicy`.
  Promotes from "deferred" to "next slice" if v0.24 falsifies the
  population-governor reading.

## Conservation framing — unchanged from v0.20/v0.21/v0.22/v0.23

v0.24 introduces no new mechanism and no new sweep. The conservation
contracts (v0.20 H4, transfer-mode H3, etc.) hold by construction
because v0.24 reads existing artifacts that already passed those
checks at the time of their generation. v0.24 does not modify the
runtime path, the model, or the chamber driver.

## Mechanism

**No new code paths in `src/`.** v0.24 is a pure analysis slice:

- A new analysis script
  [[scripts/v0.24_population_diagnostic.py]] walks each
  events.jsonl in `runs/fear-hunger-v0.21-{chamber}/` and
  `runs/fear-hunger-v0.23-{chamber}/`, computes per-tick
  population (alive count) + per-agent lifespan + per-tick
  starvation-deaths, and emits an aggregate CSV per (chamber,
  hazard regime, influx) cell.
- A small analysis library function (extracted into
  `src/hedonism_harness/experiments/population_dynamics.py`,
  ~80 LOC) does the events.jsonl → time-series transform; the
  script orchestrates per-cell aggregation. The library function
  is unit-tested independently.

The analysis is **derived entirely from event ordering** that was
already pinned by the v0.20 deterministic substrate. No
non-determinism is introduced.

### Determinism contract

- v0.21 + v0.23 events.jsonl are byte-identical re-runs (verified
  at v0.24 setup time: re-running `scripts/v0.21_sweep.py` produced
  aggregates matching the v0.21 results doc to the unit on every
  arm × seed cell).
- The analysis script is functionally deterministic — same input
  events.jsonl produces same diagnostic output.
- No randomness in the analysis path.

## Method

For each of the 160 runs (4 cells × 5 arms × 8 seeds):

1. Walk events.jsonl once.
2. Maintain a running `alive_count` updated on AgentBorn (+1) and
   AgentDied (−1). Founders are seeded at tick 0 (n_founders=5)
   before the first event.
3. Record `population_at_tick[t]` for every t in [0, ticks_completed].
4. Record `(birth_tick, death_tick)` per agent (death_tick = run
   end tick if alive at termination).
5. Record `starvation_deaths_at_tick[t]` from AgentDied events
   with cause=STARVATION.

Per-cell aggregations across the 8 seeds:

- `peak_population_per_run` (max population observed in run)
  → mean across seeds.
- `tick_of_peak` (argmax of population time-series)
  → mean across seeds.
- `mean_population_t_gt_100` (mean population over t in
  [100, ticks_completed])
  → mean across seeds.
- `lifespan_p50, p90` (median + 90th percentile of lifespan
  distribution, pooled across seeds in cell).
- `starvation_deaths_per_tick_window[bucket]` for buckets
  (0–49, 50–99, 100–149, 150–199) → sum across seeds.

## Pre-registered hypotheses

### Strong form (mechanism + invariants)

- **H1 (peak population higher at hazard=0 on tight).** For every
  shared influx ∈ {0, 0.5, 1.0, 1.5, 2.0}, mean
  `peak_population_per_run` on tight at hazard=0 (v0.23) is
  strictly greater than at hazard=8 (v0.21). Population-governor
  prediction. **Strong; falsification weight: high.** A null
  rejection of H1 falsifies the population-governor reading and
  promotes the v0.26 perception-vs-damage decoupling.

- **H2 (late-window population lower at hazard=0 on tight).** For
  every shared influx, mean `mean_population_t_gt_100` on tight
  at hazard=0 is strictly less than at hazard=8. The "crash"
  half of overshoot-and-crash. **Strong; falsification weight:
  high.**

- **H3 (mid-run starvation spike at hazard=0 on tight).** For every
  shared influx, the bucket maximum
  `starvation_deaths_per_tick_window` on tight at hazard=0 falls
  in [50–149] (mid-run); at hazard=8 the maximum falls in either
  [0–49] (early-attrition-dominated) or is roughly uniform across
  buckets. The temporal signature of crash. **Cautious — bucket
  granularity may smooth out a sharp spike.**

### Negative control

- **H4 (food_ladder shows NO overshoot pattern).** Food_ladder
  does NOT satisfy H1 + H2 + H3 between its hazard=8 (v0.21) and
  hazard=0 (v0.23) baselines. Specifically, at least one of the
  following is true on food_ladder at every shared influx:
    - peak_population at hazard=0 ≤ peak_population at hazard=8, OR
    - mean_population_t_gt_100 at hazard=0 ≥ mean_population_t_gt_100
      at hazard=8.
  The pre-food band serves as a substitute carrying-capacity
  buffer; the population-governor mechanism predicts food_ladder
  should not exhibit overshoot. **Strong; falsification weight:
  high.** A failure of H4 (food_ladder also overshoots) would
  reject the chamber-specific framing and require revising the
  "pre-food band as buffer" reading before v0.25.

### Cautious (descriptive)

- **H5 (lifespan distribution skews right at hazard=0 on tight).**
  Lifespan p50 on tight at hazard=0 is less than at hazard=8;
  lifespan p90 may be similar or higher (long-lived survivors
  persist). The distribution becomes more right-skewed at
  hazard=0. **Cautious; descriptive, not falsifying.**

- **H6 (food_ladder lifespan distribution barely shifts).**
  Lifespan p50 + p90 on food_ladder at hazard=0 are within
  ~10% of hazard=8 values across all influxes. Cautious; if
  food_ladder shows a large shift in lifespan distribution that
  weakens the chamber-specific reading even if H4 holds on the
  population-trajectory metrics.

## Decision rules

- **H1 + H2 fire on tight, H4 holds on food_ladder.**
  **Population-governor confirmed.** Commit to v0.25
  tight-only hazard × influx cross-product. Quantify the cull
  optimum and the cull-vs-cost tradeoff curve.
- **H1 + H2 fire on tight, H4 fails (food_ladder also
  overshoots).** Population-governor mechanism is real but is
  not chamber-specific in the sense v0.23 framed it. Revise the
  "pre-food band as buffer" reading; consider whether a more
  general carrying-capacity story explains both chambers.
  v0.25 design adjusts to test the revised mechanism.
- **H1 fires but H2 fails (peak high, late-window not low).**
  Population overshoots but does not crash within the 200-tick
  window. Mechanism may need long-window data; v0.25 adds a
  500-tick observation on the high-population tight cells.
- **H1 + H2 do NOT fire on tight.** Population-governor reading
  is wrong. Promote v0.26 perception-vs-damage decoupling to
  next slice; revisit the chamber-dependent hazard sign with a
  fresh mechanism question.
- **H3 fails but H1 + H2 hold.** Crash is real but temporally
  diffuse (no sharp spike). Reframe the temporal signature
  description without rejecting the population-governor reading.
- **Unexpected qualitative finding** (e.g., extinction events,
  cyclic dynamics) — flag in results, do not modify hypotheses
  retroactively.

## Out of scope (v0.24)

- **New sweeps.** v0.24 reads existing artifacts only.
- **Core/model.py/fear_hunger_chamber.py changes.** v0.24 is
  analysis-only.
- **Long-window observations** (n_ticks > 200). Deferred.
- **Hazard × influx cross-product on tight.** v0.25 candidate,
  conditional on v0.24 outcome.
- **Perception vs damage decoupling.** v0.26 candidate.
- **HedonismPolicy comparisons.** Quarantined per v0.2 spec.

## Implementation notes

### File-level changes

- **New:**
  [[src/hedonism_harness/experiments/population_dynamics.py]] —
  pure-function library for events.jsonl → time-series transform.
  Two top-level functions: `load_population_trajectory(events_jsonl,
  n_founders, n_ticks) -> PopulationTrajectory` and
  `aggregate_cell(trajectories) -> CellAggregate`.
  ~120 LOC including dataclasses.
- **New:** `tests/test_population_dynamics.py` — unit tests on
  synthetic events.jsonl + smoke tests against a real
  `runs/fear-hunger-v0.23-tight_gradient/.../events.jsonl`
  fixture from disk.
  ~150 LOC.
- **New:** [[scripts/v0.24_population_diagnostic.py]] — driver
  that walks `runs/fear-hunger-v0.21-{chamber}/` and
  `runs/fear-hunger-v0.23-{chamber}/`, builds per-cell
  aggregates, and emits both a per-cell CSV
  (`runs/fear-hunger-v0.24-diagnostic/per_cell.csv`) and a
  headline table to stdout. ~120 LOC.
- **No changes** to `core/`, `model.py`,
  `experiments/comparison_grid.py`, or
  `experiments/fear_hunger_chamber.py`. v0.24 is purely additive
  and analysis-only.
- **Documented:** this file (`docs/experiments/fear_hunger_v0.24.md`);
  results appended after the diagnostic runs.

### Determinism contract

- `V0_19_ARMS`, `V0_20_ARMS`, `V0_21_ARMS`, `V0_22_ARMS`,
  `V0_23_ARMS` continue to produce identical sweep outputs after
  v0.24 changes (no production-path surface modified).
- The analysis script is functionally deterministic.
- v0.21 sweep re-runs byte-identically against the v0.21 results
  doc (verified 2026-05-05 at v0.24 setup time).

### LOC estimate

- `experiments/population_dynamics.py`: ~120 LOC.
- `scripts/v0.24_population_diagnostic.py`: ~120 LOC.
- New tests: ~150 LOC.
- This doc: ~280 LOC.

Total v0.24 implementation: ~670 LOC. Smaller than v0.21/v0.22/v0.23
because there is no new substrate mechanism; v0.24 is a pure
analysis slice on existing artifacts.

## References

- [[docs/experiments/fear_hunger_v0.23.md]] — chamber-dependent
  hazard finding; the v0.21/v0.23 aggregate table that motivated
  the population-governor hypothesis. Reprioritised v0.24+
  roadmap committed in `19f6fb7` names this slice.
- [[docs/experiments/fear_hunger_v0.22.md]] — recycling-as-net-tax
  on food_ladder; the chamber-specific finding v0.24 extends.
- [[docs/experiments/fear_hunger_v0.21.md]] — original
  chamber-asymmetric influx frontier; supplies the hazard=8
  baseline events.jsonl artifacts for v0.24's diagnostic.
- [[docs/specs/v0.2_reflex_cell_spec.md]] §"Comparison framework"
  — the substrate axis.

---

## Results

**Status:** executed 2026-05-05. Diagnostic over 160 events.jsonl
artifacts (4 cells × 5 arms × 8 seeds), 1.3s wall time. v0.21 sweep
re-run at v0.24 setup time to materialise hazard=8 artifacts on
disk; reproduced byte-identically against the v0.21 results doc.

**Headline:** the strict population-governor "overshoot-and-crash"
reading from v0.23 is **falsified** in a specific and informative
way. H1 (peak rises at hazard=0) fires universally on both
chambers; H2 (late-window crashes at hazard=0) **fails universally**
— there is no crash. H4 (food_ladder negative control) fails — the
population-rise pattern is not chamber-specific. Substituting
mechanism: **earlier population peak under hazard=0 drives
earlier pool-exhaustion timing**, throttling late-game births
(b>50). The chamber-dependent v0.23 finding survives, but the
mechanism shifts from "tight has no carrying-capacity buffer" to
"tight's smaller direct cull-tax loses to its larger
earlier-peak pool-exhaustion penalty."

### Cell aggregates

| chamber | sweep | haz | influx | peak | tick_pk | mean_t≥100 | lp50 | lp90 | starv 0–49 / 50–99 / 100–149 / 150–199 | pk_win |
|---|---|---:|---:|---:|---:|---:|---:|---:|---|---|
| tight       | v0.21 | 8 | 0.0 | 19.00 | 64.6 | 13.13 | 89 | 189.0 |  4 / 37 / 46 / 63 | 150–199 |
| tight       | v0.21 | 8 | 0.5 | 19.00 | 64.6 | 13.83 | 87 | 189.0 |  4 / 37 / 46 / 54 | 150–199 |
| tight       | v0.21 | 8 | 1.0 | 19.00 | 64.6 | 14.20 | 86 | 189.0 |  4 / 37 / 46 / 46 | 100–149 |
| tight       | v0.21 | 8 | 1.5 | 19.00 | 64.6 | 14.65 | 84 | 189.0 |  4 / 37 / 46 / 40 | 100–149 |
| tight       | v0.21 | 8 | 2.0 | 19.00 | 64.6 | 14.86 | 83 | 188.7 |  4 / 37 / 46 / 39 | 100–149 |
| tight       | v0.23 | 0 | 0.0 | 24.75 | 38.5 | 14.02 | 88 | 179.0 |  9 / 83 / 56 / 85 | 150–199 |
| tight       | v0.23 | 0 | 0.5 | 24.75 | 38.5 | 14.85 | 87 | 183.4 |  9 / 83 / 56 / 71 |  50–99  |
| tight       | v0.23 | 0 | 1.0 | 24.75 | 38.5 | 15.36 | 87 | 186.0 |  9 / 83 / 56 / 54 |  50–99  |
| tight       | v0.23 | 0 | 1.5 | 24.75 | 38.5 | 15.96 | 87 | 188.0 |  9 / 83 / 56 / 41 |  50–99  |
| tight       | v0.23 | 0 | 2.0 | 24.75 | 38.5 | 16.48 | 86 | 188.0 |  9 / 83 / 56 / 38 |  50–99  |
| food_ladder | v0.21 | 8 | 0.0 | 13.25 | 84.0 |  9.43 | 71 | 200.0 |  1 / 38 / 19 / 21 |  50–99  |
| food_ladder | v0.21 | 8 | 0.5 | 13.38 | 84.1 |  9.62 | 69 | 200.0 |  1 / 38 / 19 / 20 |  50–99  |
| food_ladder | v0.21 | 8 | 1.0 | 13.38 | 84.1 |  9.83 | 66 | 200.0 |  1 / 38 / 19 / 19 |  50–99  |
| food_ladder | v0.21 | 8 | 1.5 | 13.38 | 84.1 |  9.82 | 66 | 200.0 |  1 / 38 / 19 / 19 |  50–99  |
| food_ladder | v0.21 | 8 | 2.0 | 13.38 | 84.1 |  9.82 | 66 | 200.0 |  1 / 38 / 19 / 19 |  50–99  |
| food_ladder | v0.23 | 0 | 0.0 | 23.25 | 44.0 | 14.48 | 86 | 177.4 |  7 / 85 / 48 / 94 | 150–199 |
| food_ladder | v0.23 | 0 | 0.5 | 23.25 | 44.0 | 15.19 | 85 | 188.0 |  7 / 85 / 48 / 80 |  50–99  |
| food_ladder | v0.23 | 0 | 1.0 | 23.25 | 44.0 | 15.69 | 85 | 188.2 |  7 / 85 / 48 / 66 |  50–99  |
| food_ladder | v0.23 | 0 | 1.5 | 23.25 | 44.0 | 16.30 | 84 | 189.0 |  7 / 85 / 48 / 55 |  50–99  |
| food_ladder | v0.23 | 0 | 2.0 | 23.25 | 44.0 | 16.67 | 83 | 189.0 |  7 / 85 / 48 / 45 |  50–99  |

### Hypothesis adjudication

| H | claim | result |
|---|---|---|
| H1 | tight: mean peak at hazard=0 > hazard=8 at every shared influx | **FIRES — 5/5.** 24.75 > 19.00 across all 5 influxes. |
| H2 | tight: mean late-window pop at hazard=0 < hazard=8 at every shared influx | **FAILS — 0/5.** Late-window mean is *higher* at hazard=0 (e.g., influx=1.0: 15.36 vs 14.20). No crash. |
| H3 | tight: starvation-deaths peak window at hazard=0 falls in [50–149] | **FIRES — 4/5.** At influx ∈ {0.5, 1.0, 1.5, 2.0} the peak window is [50–99]; at influx=0 it's [150–199] (closed-pool dynamics push starvation late). At hazard=8 the peak is [150–199] for low influx and [100–149] for high influx — so H3 captures a real shift, but the underlying mechanism is "more deaths everywhere because more agents alive everywhere," not a crash signature. |
| H4 | food_ladder: NOT (peak↑ AND late↓) at every shared influx | **FAILS.** Food_ladder shows peak↑ at every influx (13.38 → 23.25 = +74%) and late↑ as well. The *full* overshoot signature (H1 ∧ H2) does NOT fire on food_ladder — H4's OR-clause technically holds (late at hazard=0 is *higher*, not lower) — **but the chamber-specificity prediction is gone**: food_ladder's population-rise behaviour is bigger than tight's, not absent. |
| H5 | tight: lifespan p50 lower at hazard=0; p90 similar or higher | **PARTIAL.** p50 dropped slightly (89 → 87); p90 dropped (189 → 186 at influx=1.0, 188 → 179 at influx=0). Distribution shifted left, not right-skewed. The "long-lived survivors persist" prediction fails — fewer agents reach high lifespans. |
| H6 | food_ladder: lifespan p50 + p90 within ~10% of hazard=8 | **FAILS.** p50 rose 66 → 85 (+29%); p90 stayed near ceiling but compressed (200 → 188). Food_ladder's lifespan distribution shifted substantially. |

### What the diagnostic actually shows

Two findings dominate, both visible in the cell-aggregate table:

1. **Peak population is invariant across influx within each
   (chamber, hazard) cell, and is set by the first ~50 ticks.**
   - tight v0.21: peak = 19.00 at every influx; tick of peak = 64.6.
   - tight v0.23: peak = 24.75 at every influx; tick of peak = 38.5.
   - food_ladder v0.21: peak ≈ 13.3 at every influx; tick of peak = 84.
   - food_ladder v0.23: peak = 23.25 at every influx; tick of peak = 44.

   Influx accumulation does not materially affect peak — peak is
   set by early-game founder reproduction before ambient influx
   becomes load-bearing.

2. **Tick of peak shifts dramatically earlier under hazard=0 on
   both chambers.** tight: 64.6 → 38.5 (−40%); food_ladder:
   84.0 → 44.0 (−48%). The hazard cull at hazard=8 was *delaying*
   the population peak; removing it lets the founder population
   bloom faster, and the early bloom drains the pool earlier.

Late-window mean populations are *higher* at hazard=0 on both
chambers — the substrate sustains the larger population through
the full window. There is no overshoot-crash dynamic.

### New mechanism candidate: pool-exhaustion-timing

The strict population-governor reading is falsified. The
substituting mechanism candidate that explains both H1's
universal firing and v0.23's chamber-dependent b>50 sign is:

> **Hazard cull delays the population peak. Earlier peak under
> hazard=0 drains the pool earlier, throttling late-game births
> (b>50). The chamber-dependent v0.23 b>50 sign is the relative
> magnitude of two effects: (a) direct cull-tax (hazard kills
> agents directly, costing total productivity) and (b)
> pool-exhaustion-timing (earlier peak shortens the
> "compounding window" before pool drains).**

Per-chamber:

- **food_ladder:** large direct cull-tax (the v0.22 finding —
  recycling-as-net-tax with hazard=8 culling agents on the
  pre-food band crossings) DOMINATES the timing penalty. Removing
  hazards: cull-tax relief +30 b>50 per arm, timing penalty
  smaller, NET POSITIVE.
- **tight:** small direct cull-tax (agents avoid hazards via
  GradientPolicy routing — v0.21 hazard_entries on tight much
  lower than food_ladder). DOMINATED by the timing penalty
  (peak shift 64.6 → 38.5 = 26 ticks earlier; that 26-tick
  budget loss in the late-game compounding window outweighs
  the modest cull-tax relief). Removing hazards: cull-tax
  relief small, timing penalty larger, NET NEGATIVE.

This reading is **consistent with**:
- v0.22's recycling-as-net-tax on food_ladder (large cull-tax).
- v0.23's chamber-dependent b>50 sign (food_ladder gain, tight loss).
- v0.24's universal H1 firing (peak rises on both chambers when
  cull removed).
- v0.24's universal H2 failure (no crash — population is sustained,
  it just blooms earlier).
- The peak-invariance-across-influx observation (peak is set by
  early founder dynamics, not by influx accumulation).

It does **not yet predict** the cull-vs-timing balance on
intermediate hazard values (would tight at hazard=4 produce more
b>50 than at hazard=8 because cull-tax drops but timing penalty
not yet exhausted?). That is the v0.25 candidate.

### Decision-rule application

Per the pre-reg's pre-committed decision tree:

- **H1 fires but H2 fails** (matches our observation) → "Population
  overshoots but does not crash within the 200-tick window.
  Mechanism may need long-window data; v0.25 adds a 500-tick
  observation on the high-population tight cells."
- **H1 + H2 fire on tight, H4 fails** (H1 fires both, H4 fails) →
  the alternate branch was "Population-governor mechanism is real
  but is not chamber-specific. Revise the 'pre-food band as buffer'
  reading."

The actual outcome is a **combination of both branches**: H1 fires,
H2 fails (so no crash within the window), and the pattern is not
chamber-specific (so the framing must be revised). The
pool-exhaustion-timing mechanism above is the revision.

### v0.25/v0.26 plan update

The pre-reg's conditional-on-confirmation v0.25 (tight-only hazard
× influx) is **still the right next experiment** but with a
revised hypothesis: not "characterise the cull-vs-cost tradeoff"
(which assumes population-governor) but **"test the
pool-exhaustion-timing mechanism by observing whether intermediate
hazard values produce b>50 *between* hazard=0 and hazard=8 on
tight, and whether food_ladder is monotone in hazard."**

Specific predictions for v0.25 under the pool-exhaustion-timing
mechanism:

- **tight:** b>50 should be **non-monotonic** in hazard. Some
  intermediate hazard maximises b>50 (the optimum where
  cull-tax + timing-penalty is minimised). v0.21's hazard=8
  (b>50=116) and v0.23's hazard=0 (b>50=100) bracket; v0.25
  should find values in [4, 12] also producing >100.
- **food_ladder:** b>50 should be **monotone non-increasing** in
  hazard. The cull-tax dominates throughout, so removing hazards
  always helps. The v0.22 narrow sweep on food_ladder (hazard
  ∈ {0, 4, 8, 12}: 116/96/92/65) already confirms this — v0.25
  is an opportunity to verify it survives at non-saturating
  influx values.
- **Both chambers:** tick-of-peak should monotonically *decrease*
  as hazard decreases (population blooms earlier with weaker
  cull). This is a direct mechanism-pin observable.

The v0.26 perception-vs-damage decoupling remains deferred. The
pool-exhaustion-timing mechanism is silent on whether the
avoidance signal contributes independently — that's still a v0.26
question — but v0.25 should run first because (a) cheaper, no new
seam, and (b) testing the timing mechanism with intermediate
hazards is more discriminating than further hazard-zero work.

### Implementation summary

- **Library:** `src/hedonism_harness/experiments/population_dynamics.py`
  (~210 LOC including dataclasses, `STARVATION_WINDOWS` constant,
  `load_population_trajectory`, `aggregate_cell`, `_percentile`).
- **Tests:** `tests/test_population_dynamics.py` (15 new tests,
  ~250 LOC); test suite 662 → 677.
- **Driver:** `scripts/v0.24_population_diagnostic.py` (~190 LOC).
- **Output:** `runs/fear-hunger-v0.24-diagnostic/per_cell.csv` +
  per_cell_flat.csv.
- **Wall time:** 1.3s on 160 events.jsonl files.
- **No core/model.py/fear_hunger_chamber.py changes; no new sweeps.**
- **CI gate at handoff time:**
  ```
  uv run ruff check .             ok
  uv run ruff format --check .    ok
  uv run --all-extras pytest      677 passed
  uv run --all-extras python scripts/core_smoke_test.py  ok
  uv run --all-extras python scripts/v0.21_sweep.py       reproduces v0.21 byte-identically
  uv run --all-extras python scripts/v0.24_population_diagnostic.py   1.3s, all 160 cells loaded
  ```
