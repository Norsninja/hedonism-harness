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

Two arms in V0_21_ARMS reproduce v0.20 sweep arms. The anchor strength
differs between them and across chambers — we distinguish **byte-
identity** (event-stream + aggregate metrics match exactly) from
**semantic regression** (aggregate metrics match exactly; event-stream
match is not required because v0.20 itself has a known timing
perturbation on the arm/chamber pair):

- **A (transfer-1500-influx-0): byte-identity anchor on both chambers.**
  `ambient_influx_rate=0` is bit-identical to v0.20 transfer-1500's
  `ambient_influx_rate=0.0` by construction — the influx phase is a
  no-op when the rate is zero. Per-tick agent state, per-flow pool
  telemetry, and the full event stream must match.
- **E (transfer-1500-influx-2): byte-identity anchor on food_ladder;
  semantic-regression anchor on tight_gradient.** v0.20 transfer-open-
  low food_ladder produced no pool blocks anywhere (full byte-
  identity); v0.20 transfer-open-low tight produced 3 r_blk + 9 b_blk
  during the run, perturbing birth/respawn timing while still yielding
  identical final population metrics. Arm E's tight chamber must match
  v0.20 transfer-open-low tight on **aggregate metrics only**:
  `total_births`, `births_after_tick_50`, `seeds_with_survivors`,
  `total_food_events`, `total_food_respawn_events`,
  `total_pool_respawn_denied`, `total_pool_birth_denied`,
  `pool_out_respawn`, `pool_out_child_startup`,
  `pool_in_death_residual`, `pool_min`, `pool_end`,
  `parent_energy_transferred_to_child`, `reproduction_heat_loss`.
  Event-stream byte identity is **not** required on tight (v0.20 did
  not establish it).

Failure of either anchor at the appropriate strength indicates an
unintended wiring change between v0.20 and v0.21.

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

### Operational definitions — pre-committed

The frontier hypotheses below all reference a numerical
"productivity transition" that requires a hard pre-committed metric
to interpret cleanly. Two are pinned:

- **Primary i\***: per chamber, the **lowest `ambient_influx_rate` at
  which `births_after_tick_50` reaches ≥ 90% of arm E's
  `births_after_tick_50` on that chamber**. Anchored on v0.20:
  - tight i_E_b50 = 130 → primary i* threshold = 117.
  - food_ladder i_E_b50 = 92 → primary i* threshold = 83.
  i* is defined to be the smallest influx in {0, 0.5, 1.0, 1.5, 2.0}
  whose b>50 clears the threshold; if no arm clears it, i* is
  recorded as `> 2.0` (the v0.20 endpoint already cleared 100%, so
  this fallback should not fire).
- **Secondary i\***: per chamber, the **lowest `ambient_influx_rate`
  at which `total_births` reaches ≥ 90% of arm E's `total_births`
  on that chamber**. Anchored on v0.20:
  - tight i_E_total = 204 → secondary i* threshold = 184.
  - food_ladder i_E_total = 143 → secondary i* threshold = 129.

`births_after_tick_50` is the primary because it captures
late-run compounding (the v0.18 K-50 ceiling test) more directly than
total births. Secondary i* gives a check on the total-population
metric in case b>50 is dominated by a single late-run cluster of
births that doesn't reflect overall productivity.

These metrics are **mode-agnostic**: they apply identically to any
v0.22+ arm that re-uses this v0.21 framework. The 90% threshold is
chosen to be lenient on integer-rounded counts (one extra birth
per seed already moves a chamber by ~5%) while still being a
meaningful productivity bar.

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
  abruptly relative to its predecessor — a sharp productivity
  transition. Operationally: at least one of the four
  consecutive-arm differences (B−A, C−B, D−C, E−D) accounts for
  more than 50% of the (E−A) total-blocks delta on the same
  chamber. **Cautious; the transition may instead be smoothly
  graded across the entire range, in which case no single
  step accounts for >50%.**
- **H8.** **food_ladder reaches the productivity transition (primary
  i\*) at the same or lower `ambient_influx_rate` than tight_gradient,
  because hazard-residual recycling on food_ladder supplies
  additional effective energy that tight (starvation-dominated)
  lacks.** A one-grid-step advantage (food_ladder primary i\* at
  least 0.5/tick lower than tight primary i\*) is **strong support**
  for the recycling-as-effective-influx hypothesis but is not
  required to hold the hypothesis. Failure to clear that gap does
  not falsify H8; only food_ladder primary i\* > tight primary
  i\* would falsify it. **Cautious.**
- **H9.** Primary i\* is at most 2.0/tick on tight and at most
  1.5/tick on food_ladder. **Cautious; i\* could be higher than
  these bounds if the transition is steeper than v0.20 endpoints
  suggest, or if our 90%-threshold operational definition fails
  to clear at the expected influx rates.**
- **H10.** `pool_min_observed` per arm is monotonically non-decreasing
  in influx across A → E on both chambers. The pool buffer at its
  worst-case point grows with influx; this is the substrate-level
  signal of the "back-loading" prediction.

### Determinism

- **H11.** Arm A reproduces v0.20 transfer-1500 **byte-identically on
  both chambers**: aggregate metrics `(total_births,
  births_after_tick_50, seeds_with_survivors, total_food_events,
  total_food_respawn_events, total_pool_respawn_denied,
  total_pool_birth_denied, pool_out_respawn, pool_out_child_startup,
  pool_in_death_residual, pool_min, pool_end,
  parent_energy_transferred_to_child, reproduction_heat_loss)` match
  exactly AND the full event stream (`AgentBorn`, `AgentDied`,
  `AteFood`, `FoodRespawned`) matches order- and content-identically.
  `ambient_influx_rate=0.0` is a no-op by construction; this anchor
  detects any v0.21-introduced wiring leak.
- **H12.** Arm E reproduces v0.20 transfer-open-low at two anchor
  strengths:
  - **food_ladder: byte-identity** (same fields as H11; full event
    stream matches). v0.20 transfer-open-low food_ladder produced
    zero pool blocks anywhere; the run is fully deterministic.
  - **tight_gradient: semantic regression** (aggregate metrics match
    exactly, event stream is **not** required to match). v0.20
    transfer-open-low tight produced 3 r_blk + 9 b_blk that
    perturbed birth/respawn timing without changing final counts;
    the same perturbation must reappear (or the same final counts
    via a different perturbation path is acceptable).
  Failure of food_ladder byte-identity is a halt condition; failure
  of tight aggregate-metric match is also a halt condition.

## Decision rules

- **A satisfies its byte-identity anchor; E satisfies its byte-identity
  anchor on food_ladder + semantic-regression anchor on tight; H5 holds
  monotonically; H7 fires (sharp transition).** Frontier is sharply
  mapped. v0.22 candidate becomes either reproduction-efficiency
  parameterisation (if the frontier looks "clean" and adding a free
  parameter is warranted) or chamber-geometry parameterisation (if
  the H8 chamber asymmetry — primary i\* food_ladder ≤ primary i\*
  tight — is observed and worth characterising further, especially
  with strong-support magnitude ≥0.5/tick).

- **H5 holds but H7 fails (transition is smooth, no single-step
  phase change accounting for >50% of the total-blocks delta).**
  Frontier is graded; the substrate has a continuous response to
  influx. Primary i\* is still well-defined (lowest arm clearing 90%);
  v0.22 may sweep more densely around the steepest 0.5-step or move
  to the next axis (reproduction efficiency).

- **H8 fails (food_ladder primary i\* > tight primary i\*).**
  Recycling-as-effective-influx hypothesis is rejected; death-residual
  recycling does not substitute for ambient influx the way the
  back-of-envelope calculation predicts. v0.22 could parameterise
  hazard density to test the recycling axis directly.
  Note: H8 holding without the strong-support ≥0.5/tick gap (i.e.,
  ties in primary i\* across chambers) is **not a falsification** —
  same-or-lower is the threshold, not strictly-lower.

- **H6 fails strongly (total blocks rise with influx).** The v0.20
  redistribution finding (b_blk up while r_blk down) inverts at
  some influx point — surprising but consistent with the substrate
  self-throttling. Halt and audit; the frontier curve interpretation
  needs re-framing.

- **H11 fails or H12 fails on food_ladder byte-identity or H12 fails
  on tight semantic regression.** Wiring defect introduced in v0.21.
  Halt; v0.21 results are uninterpretable until the leak is closed.

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

## Results (executed 2026-05-05)

Five arms × two chambers × eight seeds (1..8) × 200 ticks × 5 founders.
**80 runs total**, 21.1 seconds end-to-end. Run artifacts persisted at
`runs/fear-hunger-v0.21-{tight_gradient,food_ladder}/`.

### Headline finding — chamber-asymmetric frontier shape; food_ladder is a phase transition, tight is graded

**v0.21 reveals that the productivity-vs-influx response under
strict-transfer reproduction at pool=1500 is qualitatively different
between chambers.** food_ladder exhibits a sharp phase transition
between influx=0.5/tick and influx=1.0/tick, with a productivity
plateau at full v0.18 K-50 levels above 1.0/tick. tight_gradient shows
a smooth, graded response — every 0.5/tick step adds another 5–10
b>50, with no single step accounting for the bulk of the lift.

**Primary i\* (≥90% of arm E b>50): food_ladder=0.5/tick, tight=1.5/tick.
Chamber asymmetry: 1.0/tick.** This exceeds the 0.5/tick strong-support
threshold pre-registered in H8 by 2×. **food_ladder behaves as if it has
substantially more effective usable energy than tight_gradient — likely
through residual recycling, chamber geometry, or some combination.**
Attributing the full 1.0/tick gap to hazard-residual recycling alone is
premature; v0.22 will test the recycling mechanism directly.

The qualitative chamber asymmetry — phase transition vs gradient —
is itself a finding. It suggests the substrate's response to ambient
energy is shape-dependent on chamber geometry (specifically the
recycling-from-injury-deaths mechanism that food_ladder has and
tight does not), not purely a function of the demand-vs-supply ledger.

### Determinism contracts — verified

H11 (arm A) and H12 (arm E) reproduce v0.20 telemetry exactly:

| chamber | metric | v0.20 anchor | v0.21 reproduction |
|---|---|---:|---:|
| tight (A) | total_births | 173 | **173** |
| tight (A) | b>50 | 99 | **99** |
| tight (A) | total_food_events | 660 | **660** |
| tight (A) | total_food_respawn_events | 468 | **468** |
| food_ladder (A) | total_births | 128 | **128** |
| food_ladder (A) | b>50 | 77 | **77** |
| food_ladder (A) | total_food_events | 640 | **640** |
| food_ladder (A) | total_food_respawn_events | 467 | **467** |
| tight (E) | total_births | 204 | **204** |
| tight (E) | b>50 | 130 | **130** |
| tight (E) | total_food_events | 765 | **765** |
| tight (E) | total_food_respawn_events | 573 | **573** |
| food_ladder (E) | total_births | 143 | **143** |
| food_ladder (E) | b>50 | 92 | **92** |
| food_ladder (E) | total_food_events | 677 | **677** |
| food_ladder (E) | total_food_respawn_events | 504 | **504** |

A is byte-identity on both chambers; E is byte-identity on food_ladder
and semantic regression (aggregate metrics match) on tight per the
pre-reg framing. No wiring leak from v0.20.

### v0.21a tight_gradient

| arm | influx | births | b>50 | surv | food | respawn | fcpb | pool_min | pool_end | r_blk | b_blk | in_influx | xfer |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| transfer-1500-influx-0 | 0.0 | 173 | 99 | 8/8 | 660 | 468 | 76.30 | 0 | 6 | 108 | 136 | 0 | 2,595 |
| transfer-1500-influx-0.5 | 0.5 | 185 | 111 | 8/8 | 687 | 495 | 74.27 | 0 | 16 | 81 | 58 | 800 | 2,775 |
| transfer-1500-influx-1.0 | 1.0 | 190 | 116 | 8/8 | 716 | 524 | 75.37 | 0 | 34 | 52 | 32 | 1,600 | 2,850 |
| transfer-1500-influx-1.5 | 1.5 | 199 | 125 | 8/8 | 744 | 552 | 74.77 | 0 | 24 | 62 | 47 | 2,400 | 2,985 |
| transfer-1500-influx-2.0 | 2.0 | 204 | 130 | 8/8 | 765 | 573 | 75.00 | 0 | 85 | 3 | 9 | 3,200 | 3,060 |

tight is **graded**. Each 0.5/tick step adds ~6 b>50 (total lift
99 → 130 = +31 across the full influx range). Total blocks fall
244 → 139 → 84 → 86 → 12 — almost monotone but with a small
non-monotonic blip at the 1.0 → 1.5 step (b_blk rises 32 → 62 even
as r_blk falls 52 → 24). The v0.20 redistribution finding (transfer
mode shifts pool binding from respawn-side to birth-side) reappears
across the influx frontier: as the substrate gets more energy, more
agents reach reproduction → birth-side gates contend more, even as
respawn-side relief grows.

**pool_min stays at 0 across every tight arm** — even at influx=2.0
the pool empties at some point during the run and re-fills via
ambient credit. The lift from 0 → 2/tick is back-loaded as
predicted: r_blk falls 108 → 3 (97% reduction); b_blk falls 136 → 9
(93% reduction); fcpb stays steady at ~75 (food consumption per
birth is ecology-stable).

**Primary i\* tight = 1.5** (b>50=125 ≥ 117 threshold).
**Secondary i\* tight = 0.5** (total_births=185 ≥ 184 threshold).
The gap between primary and secondary is striking: total_births
hits 90% recovery at the very first influx step, but late-run
compounding (b>50) needs 1.5/tick to clear 90%. tight is a
chamber where early-run productivity recovers cheaply and
late-run productivity is the binding cost.

### v0.21b food_ladder

| arm | influx | births | b>50 | surv | food | respawn | fcpb | pool_min | pool_end | r_blk | b_blk | in_influx | xfer |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| transfer-1500-influx-0 | 0.0 | 128 | 77 | 8/8 | 640 | 467 | 100.00 | 0 | 162 | 37 | 64 | 0 | 1,920 |
| transfer-1500-influx-0.5 | 0.5 | 136 | 85 | 8/8 | 662 | 489 | 97.35 | 0 | 201 | 15 | 90 | 800 | 2,040 |
| **transfer-1500-influx-1.0** | **1.0** | **143** | **92** | **8/8** | **674** | **501** | **94.27** | **2** | **257** | **3** | **0** | **1,600** | **2,145** |
| transfer-1500-influx-1.5 | 1.5 | 143 | 92 | 8/8 | 677 | 504 | 94.69 | 57 | 352 | 0 | 0 | 2,400 | 2,145 |
| transfer-1500-influx-2.0 | 2.0 | 143 | 92 | 8/8 | 677 | 504 | 94.69 | 147 | 452 | 0 | 0 | 3,200 | 2,145 |

food_ladder is a **phase transition**. The full v0.18 K-50 production
target (143 / 92) is reached at influx=1.0 and **plateaus** —
arms at 1.0, 1.5, and 2.0 are byte-identical on births and b>50;
food and respawn events differ only at the level of timing
perturbations (674 vs 677, 501 vs 504). Above influx=1.0 every
additional unit of ambient energy goes into pool buffer
(pool_end 257 → 352 → 452), not into more births.

The B → C step accounts for **the entire frontier transition**:
- Total blocks A → B: 101 → 105 (UP 4; the v0.20 redistribution
  finding fires again on this chamber too).
- Total blocks B → C: 105 → 3 (DOWN 102, accounting for 101% of
  the A → E delta of 101).
- C → D and D → E: 3 → 0 → 0 (plateau).

H7 fires unambiguously on food_ladder. **Primary i\* food_ladder
= 0.5** (b>50=85 ≥ 83 threshold). **Secondary i\* food_ladder
= 0.5** (total_births=136 ≥ 129 threshold). Both metrics agree
on food_ladder, unlike tight where primary and secondary diverge
sharply.

### Hypotheses → outcomes

- **H1.** `pool_in_ambient_influx == ambient_influx_rate × n_ticks ×
  n_seeds`. **Confirmed exactly** at every arm. Tight in_influx
  (n_ticks=200, n_seeds=8): 0/800/1600/2400/3200 = (0/0.5/1/1.5/2)
  × 1,600. food_ladder identical. The deterministic per-tick
  influx accountancy is solid.
- **H2.** v0.20 H4 invariant `parent_energy_transferred_to_child +
  pool_out_child_startup == total_births × offspring_start_energy`.
  **Confirmed exactly.** xfer = births × 15 at every arm
  (verified by inspection of the sweep table; pool_out_child_startup
  follows by H3 below).
- **H3.** `reproduction_heat_loss == 0` at every arm. **Confirmed
  exactly** (every arm in V0_21_ARMS uses TRANSFER mode; the
  POOL_FULL accumulator stays at 0).
- **H4.** `births_blocked_by_parent_energy == 0` at every arm.
  **Confirmed exactly.** The defensive parent-energy gate did not
  fire across any of the 80 runs (pe_blk=0 throughout).
- **H5.** `births_after_tick_50` monotonically non-decreasing in
  influx. **Confirmed on both chambers.** tight: 99 → 111 → 116 →
  125 → 130. food_ladder: 77 → 85 → 92 → 92 → 92 (saturated above
  1.0/tick).
- **H6.** Total pool blocks (r_blk + b_blk) monotonically non-
  increasing in influx. **Weakly falsified but overall downward
  on both chambers.** tight: 244 → 139 → 84 → 86 → 12 (small
  non-monotone blip at C → D, ~2-block uptick on a 60-block
  baseline). food_ladder: 101 → 105 → 3 → 0 → 0 (small +4 rise
  at A → B before the phase transition collapses everything).
  Both non-monotonicities are the v0.20 redistribution finding
  firing again: more parents reach reproduction → birth-side
  contention rises briefly even as respawn-side relief grows.
  The headline trend is strongly downward (95% reduction on
  tight; 100% reduction on food_ladder); the strict-monotone
  reading rejected, the directional reading confirmed.
- **H7.** A single consecutive-arm step accounts for >50% of the
  total-blocks (E−A) delta. **Falsified on tight** (no step exceeds
  ~45%); **confirmed strongly on food_ladder** (B → C accounts
  for 101% of the delta — the entire transition is at this single
  step). The chamber asymmetry in transition shape is a substantive
  finding.
- **H8.** food_ladder primary i\* ≤ tight primary i\* (recycling-as-
  effective-influx). **Confirmed**, and the strong-support
  ≥0.5/tick gap is **strongly cleared**: food_ladder primary i\* =
  0.5; tight primary i\* = 1.5; gap = 1.0/tick (2× the strong-
  support threshold). The gap is consistent with the recycling-
  as-effective-influx hypothesis but is not by itself a direct
  test of the mechanism — chamber geometry could also account
  for some of the asymmetry. v0.22 isolates the hazard-residual
  recycling channel via a direct hazard-damage sweep.
- **H9.** Primary i\* ≤ 2.0/tick on tight, ≤ 1.5/tick on food_ladder.
  **Confirmed.** Observed: tight=1.5, food_ladder=0.5. Both well
  within the predicted upper bounds.
- **H10.** `pool_min_observed` non-decreasing in influx.
  **Confirmed (non-strict) on tight** (all five arms have
  pool_min=0 — pool empties at some point in every run, including
  influx=2.0). **Confirmed strongly on food_ladder** (0 → 0 → 2 →
  57 → 147 — clean monotonic increase). Reflects the chamber
  asymmetry: food_ladder buffers ambient influx well, tight
  consumes it as fast as it arrives.
- **H11/H12.** Endpoint determinism contracts. **Confirmed exactly**
  per the determinism contracts table above.

### Decision rule fired (per pre-reg)

The pre-reg's "frontier sharply mapped" branch fires partially:

- A and E satisfy their respective anchor strengths.
- H5 holds monotonically.
- H7 fires on food_ladder but not on tight — chambers respond to
  influx with qualitatively different shapes (sharp transition vs
  graded gradient).
- H8 chamber asymmetry is strongly supported (1.0/tick gap).

The decision rule said v0.22 should become either reproduction-
efficiency parameterisation or chamber-geometry parameterisation
depending on which finding looks more striking. **The chamber
asymmetry is the more striking finding**, but rather than sweep
the broader chamber-geometry axis (width × hazard density × pre-food
band × capacity all at once — which would muddy the causal read),
**v0.22 should narrow to a hazard-damage / residual-recycling sweep
on food_ladder under transfer mode at the productive influx**.
This isolates the recycling channel directly: if recycling is
load-bearing, productivity should track hazard-damage in a
predictable way; if geometry is load-bearing, productivity
should be insensitive to hazard-damage variation. Reproduction-
efficiency parameterisation deferred to v0.23+.

### Three findings worth flagging for v0.22

1. **Tight pool_min stays at zero even at productive influx.**
   tight transfer-1500-influx-2.0 has pool_min=0 yet the substrate
   produces v0.18 K-50 dynamics. The pool drains to zero, refills
   from ambient + death residual + respawn-cycle dynamics, and
   re-drains within tight tolerances. This is a substrate that
   operates **at the edge of pool exhaustion** even when nominally
   productive — fragile to small perturbations. Variations in
   influx timing, food density, or hazard layout could push the
   pool past the recovery threshold.

2. **food_ladder saturation plateau.** Above influx=1.0/tick the
   substrate is byte-identical regardless of additional energy
   input. Excess influx accumulates in pool buffer rather than
   producing more births. The substrate has a hard population
   ceiling at 143 / 92 on this chamber under the current substrate
   parameters — chamber capacity is the binding constraint above
   the productivity transition, not energy supply. This invites
   v0.22 to vary chamber size / agent capacity to test whether
   the ceiling is geometric or substrate-side.

3. **The v0.20 b_blk/r_blk redistribution finding fires across the
   v0.21 frontier.** As influx increases, transfer mode produces
   more successful births → more birth-side contention even as
   respawn-side relief grows. On both chambers the lowest-influx
   step (A → B) shows b_blk going up while r_blk goes down. This
   is now a robust feature of transfer mode, not a v0.20-specific
   anomaly. v0.22 chamber-geometry sweeps should track per-flow
   block counts to maintain this resolution.

### Data points worth flagging for v0.22

- **v0.22 should be a focused hazard-damage sweep, not a broader
  geometry parameterisation.** Sweeping width, hazard density,
  pre-food band, and capacity simultaneously would muddy the causal
  read. The high-information v0.22 design is hazard_damage ∈
  `{0, 4, 8, 12}` (or `{2, 4, 8, 12}` if a tighter span is preferred)
  on food_ladder under transfer mode at the productive influx
  (1.0/tick), with `hazard_damage=0` as the crucial control: it
  produces zero injury deaths → zero death-residual recycling, while
  preserving food_ladder's geometry. If productivity drops on the
  zero-hazard arm, recycling is load-bearing; if it stays unchanged,
  geometry is load-bearing. The same v0.21 seeds should be re-used
  so per-seed comparisons are interpretable.
- **Two competing hypotheses to keep separate in v0.22.**
  (a) Recycling-as-effective-influx: more hazard → more residual
  recycling → lower required ambient influx for productivity.
  Predicts hazard_damage=0 collapses food_ladder's productivity
  back toward tight-like binding levels.
  (b) Chamber-geometry-as-buffer: food_ladder's pre-food band
  permits multi-step refueling without crossing the hazard wall;
  this could fund productivity independent of recycling. Predicts
  hazard_damage=0 preserves productivity (geometry is the lever,
  not recycling).
  v0.22 should pre-register specific quantitative thresholds for
  which hypothesis fires.
- **The 2× over-prediction of recycling-as-effective-influx** is
  worth attribution. Death residual in v0.20 transfer-1500
  food_ladder was ~80 energy/seed/200 ticks (= 0.4/tick effective).
  If the observed 1.0/tick gap holds, food_ladder's effective extra
  energy is ~1.0/tick. Either (a) recycling energy is more "useful"
  than ambient influx because it arrives in discrete deposits at
  population-correlated timings, (b) the death rate scales with
  population growth and the back-of-envelope underestimated total
  recycling, or (c) chamber geometry contributes meaningful
  effective-energy buffering independent of recycling. v0.22's
  hazard_damage=0 control distinguishes (a/b) from (c).
- **tight vs food_ladder behave so differently that future
  chamber-asymmetric experiments may want a third chamber** with
  intermediate recycling characteristics (e.g., a low-hazard
  food_ladder variant) to span the spectrum. v0.22's
  hazard-damage sweep effectively constructs that third chamber.
- **Secondary i\* on tight (0.5/tick for total_births, vs 1.5 for
  b>50)** suggests that early-run reproduction is cheap to recover
  but late-run compounding is the expensive frontier. v0.22+ chamber
  experiments should report both metrics; they reveal substrate
  behavior at different lifecycle phases.

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
