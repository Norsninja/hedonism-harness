# v0.21 — influx frontier under strict-transfer reproduction

**Status:** pre-registration; not yet executed.
**Date:** 2026-05-05
**Branch:** `claude/v0.21-influx-frontier`
**Predecessors:** v0.18 (food respawn cooldown — first compounding under
non-saturating food), v0.19 (strict mass-energy conservation — substrate
compounds when budget or steady-state influx covers demand), v0.20
(parent-transfer + pool-gap reproduction — eliminating reproduction heat
loss lifts compounding in v0.19's binding regimes; transfer-open-low at
influx=2/tick fully recovers v0.18 K-50 productive population-level
outcomes on both chambers).
**Spec:** [[docs/specs/v0.2_reflex_cell_spec.md]] §"Comparison framework"
(substrate axis).

## Question

v0.20 surfaced a striking result: under strict-transfer reproduction
(`ChildFundingMode.PARENT_TRANSFER_POOL_GAP`), the partial-rescue arm at
`pool_initial=1500` + `ambient_influx_rate=2/tick` fully recovers v0.18
K-50 productive dynamics on both chambers. The same arm under v0.19
POOL_FULL gave only partial recovery (175/101 vs 204/130 tight; 136/85
vs 143/92 food_ladder). Eliminating reproduction heat loss roughly
halves the per-birth pool draw and pushes the influx-supplemented
substrate over the productivity threshold.

That observation immediately raises a sharper question: **how much
ambient influx is actually required to sustain productive compounding
under conservation-faithful reproduction?** v0.19 needed 7/tick (the
open-equiv arm). v0.20 transfer mode succeeded at 2/tick. The minimum
energy inflow for productivity has clearly fallen — but where exactly
is the frontier between closed-1500 transfer (partial recovery: 173/99
tight, 128/77 food_ladder) and open-low transfer (full recovery:
204/130 tight, 143/92 food_ladder)?

**v0.21 maps the influx frontier.** A single sweep along
`ambient_influx_rate ∈ {0, 0.5, 1.0, 1.5, 2.0}` under transfer mode at
`pool_initial=1500` across both chambers, all other v0.20 parameters
held fixed. The frontier curve answers two things:

1. **Where is the productivity transition?** Smooth gradient across
   arms, or a sharp phase change at one influx step?
2. **Is the transition chamber-asymmetric?** food_ladder receives
   ~80 energy/seed of death-residual recycling under transfer mode
   (hazard-injury deaths credit residual body energy back to pool),
   which is roughly equivalent to an extra ~0.4/tick of "effective"
   influx. tight_gradient is starvation-dominated and recycles zero.
   The frontier on food_ladder should sit at a lower nominal influx
   than on tight.

## What this slice tests, and what it does NOT test

### Tests
- The **shape** of the productivity-vs-influx curve under
  PARENT_TRANSFER_POOL_GAP at fixed `pool_initial=1500`. Smooth, sharp,
  or staircase?
- The **chamber asymmetry** of the productivity transition (i*),
  predicted lower on food_ladder than on tight by ~0.4/tick from
  death-residual recycling.
- The **back-loading** prediction: most of the lift between influx=0
  and influx=2 happens in the last 50 ticks (when the closed-pool
  variant runs dry). `pool_min_observed` and `pool_end` per arm should
  show late-run trajectory differences corresponding to the b>50 lift.

### Does NOT test
- **POOL_FULL at the same influx points.** v0.19 already mapped
  POOL_FULL at influx ∈ {0, 2, 7}. Adding the missing intermediate
  POOL_FULL points doubles the run count without sharpening the
  v0.21 question (which is specifically about the transfer-mode
  frontier). v0.22+ may revisit if the cross-mode comparison becomes
  load-bearing.
- **Variable pool size.** All arms hold `pool_initial=1500` to
  isolate the influx variable. v0.22+ may sweep pool size at the
  most informative influx rate.
- **Non-zero death-residual variance via chamber geometry tweaks.**
  We use the v0.18 chambers unchanged; the food_ladder asymmetry
  prediction tests the existing recycling effect at face value.
  v0.22+ may parameterise hazard density to vary the recycling rate.
- **Reproduction efficiency < 1.0** (heat-loss fraction on transfer).
  Deferred per the post-v0.20 plan: first map the conservation-
  faithful frontier, then introduce graded biological inefficiency.

### Deferred (v0.22+ candidates)
- **Reproduction efficiency parameterisation** (continuous heat-loss
  fraction). Conditional on v0.21 mapping a clean frontier.
- **Pool-debit timing split** (separate budgets for respawn-side
  and birth-side pool draws) — potential follow-on to the v0.20
  b_blk/r_blk redistribution finding, conditional on whether the
  v0.21 frontier behaves as predicted.
- **Multi-cell-tier directional EMA** still deferred until the
  substrate question is settled.
- **HedonismPolicy on conservation substrate** still quarantined per
  v0.2 spec.

## Conservation framing — unchanged from v0.20

v0.21 introduces no new mechanism. The six-flow conservation
bookkeeping under PARENT_TRANSFER_POOL_GAP is preserved exactly:

```
Parent: -reproduction_cost   (15, transferred to child via system ledger)
Pool:   -(offspring_start_energy - reproduction_cost)   (15, gap)
Pool:   +ambient_influx_rate per tick   (variable, 0 → 2 across arms)
Pool:   +max(0, body.energy) on AgentDied   (death residual)
Child:  +offspring_start_energy   (30)
System energy delta per birth: 0   (no heat loss at reproduction)
```

The only knob that varies across arms is `ambient_influx_rate`. All
other v0.20 parameters (`reproduction_cost=15`,
`offspring_start_energy=30`, `pool_initial=1500`,
`food_respawn_cooldown=50`, `child_funding_mode=PARENT_TRANSFER_POOL_GAP`,
reflex-baseline policy, `unbounded_mutation=True`, `n_ticks=200`,
`n_founders=5`) are held constant.

### Why fix `pool_initial=1500`

1500 is the v0.19/v0.20 "binding" pool size — the regime where
conservation actually matters. At 3000 the pool is comfortable under
both modes and influx is irrelevant to the headline metrics; at 500 the
substrate is past the cliff regardless. 1500 sits at the productive-
binding sweet spot where small input changes produce measurable output
deltas.

### Why these influx points

v0.20 measured the endpoints:

- influx=0 (transfer-1500): 173 / 99 b>50 tight; 128 / 77 food_ladder.
- influx=2 (transfer-open-low): 204 / 130 tight; 143 / 92 food_ladder.

The 5-point grid {0, 0.5, 1.0, 1.5, 2.0} samples uniformly between
these endpoints. Even spacing privileges no prior on where the
transition lies; 0.5/tick steps are fine enough to detect a sharp
single-step phase change yet coarse enough to keep the run count at
80.

## Mechanism

**No new code paths.** v0.21 is purely configuration: a new
`V0_21_ARMS` tuple in
[[src/hedonism_harness/experiments/comparison_grid.py]] consisting of
five `Arm` instances at the influx points above, plus a sweep driver
[[scripts/v0.21_sweep.py]] mirroring v0.19/v0.20.

The v0.20 telemetry is sufficient for the frontier analysis: the
mode-specific accumulators (`reproduction_heat_loss`,
`parent_energy_transferred_to_child`,
`births_blocked_by_parent_energy`), the pool ledger (`pool_min`,
`pool_end`, `pool_out_respawn`, `pool_out_child_startup`,
`pool_in_death_residual`, `pool_in_ambient_influx`), and the v0.18/19
event-block counters (`total_pool_respawn_denied`,
`total_pool_birth_denied`).

### Determinism — endpoints anchor against v0.20

Two arms in V0_21_ARMS are deliberate byte-identical reproductions of
v0.20 sweep arms:

- **A (transfer-1500-influx-0)** must reproduce v0.20 transfer-1500
  byte-identically on per-tick agent state and per-flow pool telemetry
  on both chambers (the v0.20 sweep already verified that
  `ambient_influx_rate=0` is bit-identical to `ambient_influx_rate=0.0`
  by construction; this serves as a regression detector for any
  v0.21-introduced wiring error).
- **E (transfer-1500-influx-2)** must reproduce v0.20 transfer-open-low
  byte-identically on per-tick agent state and per-flow pool
  telemetry on both chambers.

Failure of either anchor indicates an unintended wiring change between
v0.20 and v0.21.

## Arms

Five arms × two chambers × eight seeds = **80 runs**.

| arm | tier | mode | K | pool_initial | influx | label |
|---|---|---|---:|---:|---:|---|
| A | endpoint | PARENT_TRANSFER_POOL_GAP | 50 | 1,500 | 0.0 | transfer-1500-influx-0 (= v0.20 transfer-1500) |
| B | frontier | PARENT_TRANSFER_POOL_GAP | 50 | 1,500 | 0.5 | transfer-1500-influx-0.5 |
| C | frontier | PARENT_TRANSFER_POOL_GAP | 50 | 1,500 | 1.0 | transfer-1500-influx-1.0 |
| D | frontier | PARENT_TRANSFER_POOL_GAP | 50 | 1,500 | 1.5 | transfer-1500-influx-1.5 |
| E | endpoint | PARENT_TRANSFER_POOL_GAP | 50 | 1,500 | 2.0 | transfer-1500-influx-2.0 (= v0.20 transfer-open-low) |

`offspring_start_energy=30`, `energy_cost=15`, `energy_threshold=50`,
`food_respawn_cooldown=50`, `unbounded_mutation=True`, reflex-baseline
policy, `n_ticks=200`, `n_founders=5`, chamber layouts unchanged from
v0.18/v0.19/v0.20.

### Demand-math projection (anchored on v0.20)

v0.20 transfer-1500 tight per-run pool flow: out_respawn ≈ 1,170/seed
(58.5 events × 20), out_child_startup ≈ 324/seed (21.6 births × 15),
in_death_residual ≈ 0, in_ambient_influx = 0. Net drain ≈ 1,494/seed
across 200 ticks ≈ 7.47/tick. Initial pool 1,500/seed → ends at ≈
0.75/seed (sweep telemetry: pool_end=6 ÷ 8 = 0.75).

Under v0.21:
- influx=0.5/tick adds 100/seed/run = ~0.5/tick of pool replenishment.
  Net drain falls to ~6.97/tick. Pool ends at ~100/seed if births
  unchanged; almost certainly more births fund (b_blk falls), pool
  ends lower than naive projection.
- influx=1.0: 200/seed/run replenishment, net drain ~6.47/tick, pool
  end ~200/seed (naive).
- influx=1.5: 300/seed/run, net drain ~5.97/tick, pool end ~300/seed
  (naive).
- influx=2.0 (= v0.20 anchor): 400/seed/run replenishment; observed
  pool_end ≈ 10.6/seed (sweep: 85/8). The naive 400/seed projection
  fails because the additional pool relief funds more births →
  more food consumption → more respawn drain.

The naive projections won't hold; the substrate self-throttles. The
question is at what influx rate the system stops binding altogether —
where pool_min stays comfortably above zero and r_blk + b_blk go to
zero or near-zero.

For food_ladder, the same calculation gives ~6/tick base drain with
~0.4/tick of effective recycling. Productivity transition predicted
at influx ≈ 1.0–1.5/tick (i.e. lower than tight's predicted ~1.5–2.0).

### Telemetry to watch

- `births`, `births_after_tick_50`, `seeds_with_survivors` —
  productivity headline.
- `pool_min`, `pool_end` — late-run pool trajectory; productivity
  transition correlates with `pool_min` staying above zero.
- `total_pool_birth_denied`, `total_pool_respawn_denied` — when both
  go to zero, conservation no longer binds.
- `pool_in_ambient_influx` — must equal `ambient_influx_rate × n_ticks`
  per seed (= ambient_influx_rate × 1600 across 8 seeds × 200 ticks),
  modulo early-termination runs. Direct invariant.
- `parent_energy_transferred_to_child` — must equal
  `births × reproduction_cost` per arm (the v0.20 H4 invariant).

## Pre-registered hypotheses

Two-tier structure consistent with v0.15..v0.20: **strong-form** for
mechanism + invariants, **cautious-form** for the substantive frontier
shape, plus **determinism** for bit-identity contracts.

### Strong form (mechanism + invariants)

- **H1.** `pool_in_ambient_influx == ambient_influx_rate × n_ticks` per
  seed, summed across all 8 seeds in each arm (modulo seeds that
  terminate early via population extinction). Direct invariant on
  the deterministic per-tick credit.
- **H2.** v0.20 H4 invariant holds at every v0.21 arm:
  `parent_energy_transferred_to_child + pool_out_child_startup ==
  total_births × offspring_start_energy`.
- **H3.** `reproduction_heat_loss == 0` at every v0.21 arm (transfer
  mode contract).
- **H4.** `births_blocked_by_parent_energy == 0` at every v0.21 arm
  (defensive parent-energy gate; v0.20 already verified empirical
  irrelevance under cost=15, threshold=50 in the binding regime).

### Cautious form (frontier shape)

- **H5.** `births_after_tick_50` is monotonically non-decreasing in
  `ambient_influx_rate` across arms A → E on both chambers.
  **Cautious in monotonicity strictness; some seeds may produce ties.**
- **H6.** `total_pool_birth_denied + total_pool_respawn_denied` is
  monotonically non-increasing in `ambient_influx_rate` across arms
  A → E on both chambers. **Cautious — the v0.20 directional caveat
  on H6 (transfer mode redistributing binding from respawn-side to
  birth-side) may produce a non-monotone b_blk component even if the
  total monotonically falls.**
- **H7.** There exists at least one arm B/C/D where
  `total_pool_birth_denied + total_pool_respawn_denied` falls
  abruptly relative to its predecessor — the productivity transition.
  **Cautious; the transition may instead be smoothly graded across
  the entire range.**
- **H8.** The productivity-transition influx rate i* is at least
  0.5/tick lower on food_ladder than on tight_gradient.
  **Cautious. Predicted asymmetry magnitude is roughly the
  death-residual recycling rate (~0.4/tick on food_ladder); H8
  rounds up to 0.5/tick to stay testable on the 0.5-grid.**
- **H9.** `births` at the v0.18 K-50 production target (204 tight,
  143 food_ladder) is reached at `ambient_influx_rate ≤ 1.5/tick` on
  food_ladder and `ambient_influx_rate ≤ 2.0/tick` on tight.
  **Cautious in influx threshold; lower thresholds would imply a
  steeper transition than v0.20 endpoints suggest.**
- **H10.** `pool_min_observed` per arm is monotonically non-decreasing
  in influx across A → E on both chambers. The pool buffer at its
  worst-case point grows with influx; this is the substrate-level
  signal of the "back-loading" prediction.

### Determinism

- **H11.** Arm A reproduces v0.20 transfer-1500 byte-identically on
  per-seed `(total_births, births_after_tick_50, seeds_with_survivors,
  total_food_events, total_food_respawn_events,
  total_pool_respawn_denied, total_pool_birth_denied,
  pool_out_respawn, pool_out_child_startup, pool_in_death_residual,
  pool_min, pool_end, parent_energy_transferred_to_child,
  reproduction_heat_loss)` AND emits identical `AgentBorn` /
  `AgentDied` / `AteFood` / `FoodRespawned` events on both chambers.
- **H12.** Arm E reproduces v0.20 transfer-open-low byte-identically
  (same metric set as H11) on both chambers. Same caveat as v0.20:
  food_ladder is byte-identical; tight has a small event-timing
  perturbation (3 r_blk + 9 b_blk) but identical final population
  metrics.

## Decision rules

- **A and E reproduce v0.20 byte-identically (H11/H12) AND H5 holds
  monotonically AND a clear transition arm exists (H7).** Frontier
  is mapped; v0.22 candidate becomes either reproduction-efficiency
  parameterisation (if the frontier looks "clean" and adding a free
  parameter is now warranted) or chamber-geometry parameterisation
  (if the chamber asymmetry from H8 is striking and worth
  characterising).

- **H5 holds but H7 fails (transition is smooth, no clear single-step
  phase change).** Frontier is graded; the substrate has a
  continuous response to influx. v0.22 may sweep more densely
  around the steepest 0.5-step or move on to the next axis
  (reproduction efficiency).

- **H8 fails (chamber asymmetry not detected at the 0.5/tick
  resolution).** Death-residual recycling is smaller in effect than
  predicted, OR the chamber-asymmetric demand math is wrong. v0.22
  could parameterise hazard density to vary recycling.

- **H6 fails strongly (total blocks rise with influx).** The v0.20
  redistribution finding (b_blk up while r_blk down) inverts at
  some influx point — surprising but consistent with the substrate
  self-throttling. Halt and audit; the frontier curve interpretation
  needs re-framing.

- **H11 or H12 fails byte-identity.** Wiring defect introduced in
  v0.21. Halt; v0.21 results are uninterpretable until the leak is
  closed.

- **H1 invariant fails** (`pool_in_ambient_influx ≠ rate × ticks`).
  Influx accounting bug. Halt.

## Out of scope (v0.21)

- **Reproduction efficiency < 1.0.** v0.22+ candidate.
- **POOL_FULL at intermediate influx points.** Out of v0.21 scope per
  the deliberate transfer-mode-only frontier framing.
- **Pool sizes other than 1,500.** v0.22+.
- **Variable food yield, density-dependent respawn, spatial pool
  fields.** v0.22+.
- **Long-window (n_ticks > 200) observations.** v0.22+ if half-life
  dynamics become the central question.
- **HedonismPolicy comparisons** — quarantined per v0.2 spec.

## Implementation notes

### File-level changes

- **Modify:** [[src/hedonism_harness/experiments/comparison_grid.py]] —
  add `V0_21_ARMS` tuple of five `Arm` instances per the table
  above. ~70 LOC. No code-path changes; arm definitions only.
- **New:** [[scripts/v0.21_sweep.py]] — sweep driver mirroring
  `scripts/v0.20_sweep.py`; prints per-arm headline tables. ~70 LOC.
- **New:** `tests/test_comparison_grid_v0_21.py` — V0_21_ARMS shape
  test; substrate-economics-fixed test; bit-identity anchor smoke
  tests (arms A and E run without raising and produce ChamberRunResult
  with mode-specific telemetry populated). ~120 LOC.
- **No changes** to `core/`, `model.py`, `experiments/fear_hunger_chamber.py`,
  or any v0.20 surface. The mechanism is unchanged; only configuration
  varies.
- **Documented:** this file (`docs/experiments/fear_hunger_v0.21.md`);
  results appended after the sweep.

### Determinism contract

- `V0_20_ARMS` continues to produce identical sweep outputs after
  v0.21 changes (no v0.20 surface modified).
- `V0_19_ARMS` continues to produce identical outputs (no v0.19
  surface modified).
- Arm A reproduces v0.20 transfer-1500 byte-identically (H11).
- Arm E reproduces v0.20 transfer-open-low byte-identically (H12).
- The v0.20 H4 invariant continues to hold per arm (H2).

### LOC estimate

- `experiments/comparison_grid.py`: +70 LOC (V0_21_ARMS).
- `scripts/v0.21_sweep.py`: ~70 LOC (sweep driver).
- New tests: ~120 LOC.
- This doc: ~430 LOC.

Total v0.21 implementation: ~690 LOC. About half of v0.19/v0.20 because
v0.21 introduces no new mechanism — it is a focused frontier mapping
on the v0.20 substrate.

## References

- [[docs/experiments/fear_hunger_v0.20.md]] — v0.20 results;
  the closed-1500 binding regime and the open-low partial-rescue
  result that anchor v0.21's two endpoints. Also the source of the
  H4 invariant carried forward to v0.21 H2.
- [[docs/experiments/fear_hunger_v0.19.md]] — v0.19 results; original
  closed-pool / open-ecology framing and per-flow telemetry that the
  v0.21 demand math borrows from.
- [[docs/specs/v0.2_reflex_cell_spec.md]] §"Comparison framework" —
  the substrate axis.
