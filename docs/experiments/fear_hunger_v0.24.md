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
