# v0.23 — chamber-asymmetry mechanism: hazard-zero influx frontier on both chambers

**Status:** pre-registration; not yet executed.
**Date:** 2026-05-05
**Branch:** `claude/v0.23-hazard-zero-frontier`
**Predecessors:** v0.18 (food respawn cooldown — first compounding under
non-saturating food), v0.19 (strict mass-energy conservation —
substrate compounds when budget or steady-state influx covers demand),
v0.20 (parent-transfer + pool-gap reproduction — eliminating
reproduction heat loss lifts compounding under v0.19's binding regime),
v0.21 (influx frontier under transfer mode — chamber-asymmetric
frontier shape: food_ladder primary i\*=0.5/tick, tight primary
i\*=1.5/tick, a 1.0/tick gap consistent with hazard-residual recycling
but not directly tested), v0.22 (narrow hazard-damage sweep on
food_ladder under transfer + influx=1.0 — band 4 fires:
**injury-deaths-as-cull confirmed, recycling was a net tax not a
fuel**; arm A hazard=0 produces b>50=116, substantially above the
v0.21 saturation plateau b>50=92).
**Spec:** [[docs/specs/v0.2_reflex_cell_spec.md]] §"Comparison framework"
(substrate axis).

## Question

v0.21 reported a 1.0/tick chamber asymmetry — food_ladder reaches the
v0.18 K-50 productivity plateau (b>50=92) at influx=1.0/tick while
tight_gradient needs 1.5/tick. v0.21 hypothesised this gap was supplied
by hazard-injury death-residual recycling on food_ladder (~0.4/tick
back-of-envelope effective influx). v0.22 falsified that mechanism:
at hazard=0 on food_ladder under influx=1.0, productivity *exceeds*
the v0.21 saturation plateau by 26% (b>50=116). The recycling channel
was a net tax, not a fuel — the hazard cull was the binding force.

This leaves the v0.21 chamber asymmetry **mechanism-unknown**.
Three candidates remain:

(a) **Geometry / food accessibility.** food_ladder's pre-food band
permits multi-step refueling without crossing the hazard wall;
tight_gradient lacks an analogous refuel corridor. Even at hazard=0
this geometric difference may produce different productivity
transitions because path-length-to-food differs.

(b) **Hazard-interaction artifact.** The v0.21 asymmetry was
constructed entirely by hazard-cull dynamics — agents on tight
hit hazards differently than on food_ladder, and removing hazards
collapses the gap. (Note: v0.22 already showed *food_ladder*'s
plateau is hazard-cull-supplemented; (b) extends this to claim
the *cross-chamber gap* is also hazard-mediated.)

(c) **Tight was hazard-wall-constrained, not energy-throughput-
constrained.** Removing hazards lets tight reach productivity at much
lower influx, possibly tight primary i\* drops from 1.5/tick (hazard=8)
to ≤1.0/tick (hazard=0). Tight's binding constraint at hazard=8 was
the hazard wall itself, not the substrate's energy supply.

**v0.23 isolates these three mechanisms with the cleanest possible
test: rerun the v0.21 influx frontier (`ambient_influx_rate ∈
{0, 0.5, 1.0, 1.5, 2.0}`) at `hazard_damage=0` on both chambers
(food_ladder AND tight_gradient), under transfer mode at
`pool_initial=1500`. All other v0.20/v0.21 substrate parameters
fixed.** Same 8 seeds as v0.21/v0.22 so per-seed cross-version
comparisons are interpretable. The chamber-asymmetry mechanism
question reduces to: when injury/cull/recycling is removed, does
food_ladder still have a lower productivity transition than
tight_gradient, and if so, by how much?

## What this slice tests, and what it does NOT test

### Tests

- The **shape of the hazard-zero productivity-vs-influx curve on
  both chambers** under transfer mode at fixed pool=1500. Smooth,
  sharp, or staircase, on each chamber.
- The **chamber-asymmetry gap at hazard=0**: how does food_ladder's
  primary i\* compare to tight's at hazard=0, and how does that
  compare to v0.21's hazard=8 anchors (food_ladder=0.5, tight=1.5)?
- The **causal contribution of geometry vs hazard-interaction** to
  the v0.21 1.0/tick gap, by reading the gap at hazard=0 against
  the gap at hazard=8 (v0.21).
- Whether **tight_gradient is hazard-wall-constrained** at
  hazard=8: if tight's primary i\* drops from 1.5 to ≤1.0 at
  hazard=0, the v0.21 binding regime on tight was the hazard wall,
  not energy throughput.

### Does NOT test

- **Long-window stability of the hazard=0 substrate.** v0.22 arm A
  showed pool-bound starvation pressure at 200 ticks (249 births,
  206 starvations, fcpb=53.82 near transfer-mode floor). Whether
  the substrate remains productive at n_ticks > 200 is a v0.24+
  question.
- **Pool-size sensitivity at hazard=0.** All arms hold
  pool_initial=1500. v0.24+ may sweep pool_initial at hazard=0 to
  characterise the new cliff.
- **Hazard parameterisation between 0 and 8.** v0.22 sampled
  {0, 4, 8, 12} on food_ladder at influx=1.0 only. Cross-product of
  hazard × influx is deferred.
- **Reproduction efficiency < 1.0** (heat-loss fraction on transfer).
  Deferred per the post-v0.20 plan.
- **Multi-cell-tier directional EMA** still deferred until the
  substrate question is settled.
- **HedonismPolicy on conservation substrate** still quarantined per
  v0.2 spec.

### Deferred (v0.24+ candidates)

- **Long-window (n_ticks ∈ {500, 1000}) stability test on the v0.23
  high-productivity arms.** Conditional on v0.23 mapping a clean
  frontier; tests whether the hazard=0 substrate is genuinely
  productive long-run or only over the v0.21/v0.22 200-tick window.
- **Pool-size sweep at hazard=0** to characterise the new cliff
  position now that the hazard cull is removed.
- **Hazard × influx cross-product** to map the recycling-vs-cull
  tradeoff surface.
- **Reproduction efficiency parameterisation** (continuous heat-loss
  fraction) deferred since v0.20.
- **Pool-debit timing split** (separate budgets for respawn-side
  and birth-side pool draws) — follow-on to the v0.20/v0.21/v0.22
  b_blk/r_blk redistribution finding.

## Conservation framing — unchanged from v0.20/v0.21

v0.23 introduces no new mechanism. The six-flow conservation
bookkeeping under PARENT_TRANSFER_POOL_GAP is preserved exactly:

```
Parent: -reproduction_cost   (15, transferred to child via system ledger)
Pool:   -(offspring_start_energy - reproduction_cost)   (15, gap)
Pool:   +ambient_influx_rate per tick   (variable, 0 → 2 across arms)
Pool:   +max(0, body.energy) on AgentDied   (death residual)
Child:  +offspring_start_energy   (30)
System energy delta per birth: 0   (no heat loss at reproduction)
```

The two knobs that vary across the v0.23 sweep are
`ambient_influx_rate` (5 levels) and `layout_name` (2 chambers).
**`hazard_damage` is fixed at 0** across every arm in V0_23_ARMS —
this is the core experimental control. All other parameters held
constant: `reproduction_cost=15`, `offspring_start_energy=30`,
`pool_initial=1500`, `food_respawn_cooldown=50`,
`child_funding_mode=PARENT_TRANSFER_POOL_GAP`, reflex-baseline policy,
`unbounded_mutation=True`, `n_ticks=200`, `n_founders=5`.

### Why fix `pool_initial=1500` and `hazard_damage=0`

`pool_initial=1500` is the v0.19/v0.20/v0.21/v0.22 binding pool size
where conservation actually matters; cross-version anchors are
strongest at this value.

`hazard_damage=0` is the experimental control: it removes the
recycling/cull channel entirely, isolating chamber geometry / food
accessibility as the only remaining mechanism that could produce a
chamber asymmetry.

### Why these influx points

`{0, 0.5, 1.0, 1.5, 2.0}` mirrors v0.21 exactly so cross-version
comparisons against the hazard=8 frontier are direct. Same 5-point
grid; same 8 seeds. The only difference is hazard_damage.

## Mechanism

**No new code paths.** v0.23 is purely configuration: a new
`V0_23_ARMS` tuple in
[[src/hedonism_harness/experiments/comparison_grid.py]] consisting of
five `Arm` instances at the influx points above (each with
`hazard_damage=0.0`), plus a sweep driver
[[scripts/v0.23_sweep.py]] mirroring v0.21 but running both chambers.

The v0.20/v0.21/v0.22 telemetry is sufficient for the chamber-asymmetry
analysis: the mode-specific accumulators (`reproduction_heat_loss`,
`parent_energy_transferred_to_child`,
`births_blocked_by_parent_energy`), the pool ledger (`pool_min`,
`pool_end`, `pool_out_respawn`, `pool_out_child_startup`,
`pool_in_death_residual`, `pool_in_ambient_influx`), the v0.18/19
event-block counters, and the v0.22 starvation/injury death split
(`total_starvation_deaths`, `total_injury_deaths`).

### Determinism — one byte-identity anchor

V0_23_ARMS contains one anchor against v0.22 sweep telemetry:

- **C (transfer-1500-hzd0-influx-1.0): byte-identity anchor on
  food_ladder.** v0.22 hazard-0 (arm A) at influx=1.0/tick on
  food_ladder produced births=249, b>50=116, food=670, respawn=478,
  pool_min=0, pool_end=38, r_blk=98, b_blk=12, residual=0.0,
  starv=206, inj=0, hazard_entries=200, xfer=3,735. v0.23 arm C on
  food_ladder must reproduce these aggregates **byte-identically**;
  the seam (`hazard_damage=0`, all other params identical) and the
  same 8 seeds make this a deductive identity. No event-stream
  comparison required (the v0.22 sweep itself didn't pin event
  ordering separately from aggregates).

**No tight_gradient byte-identity anchor exists** — neither v0.21
(at hazard=8) nor v0.22 (food_ladder only) ran at hazard=0 on tight.
The tight chamber's productivity at hazard=0 is a v0.23 first
observation. The food_ladder C anchor is sufficient to detect any
v0.23-introduced wiring drift; tight's substrate is exposed by
the same code paths.

Failure of the food_ladder C anchor is a halt condition.

## Arms

Five arms × two chambers × eight seeds = **80 runs** (matches v0.21
size).

| arm | tier | hazard | influx | label |
|---|---|---:|---:|---|
| A | endpoint | 0.0 | 0.0 | transfer-1500-hzd0-influx-0 (closed-pool, no influx, no recycling) |
| B | frontier | 0.0 | 0.5 | transfer-1500-hzd0-influx-0.5 |
| C | byte-identity anchor | 0.0 | 1.0 | transfer-1500-hzd0-influx-1.0 (= v0.22 hazard-0 on food_ladder) |
| D | frontier | 0.0 | 1.5 | transfer-1500-hzd0-influx-1.5 |
| E | endpoint | 0.0 | 2.0 | transfer-1500-hzd0-influx-2.0 |

`offspring_start_energy=30`, `energy_cost=15`, `energy_threshold=50`,
`food_respawn_cooldown=50`, `unbounded_mutation=True`, reflex-baseline
policy, `n_ticks=200`, `n_founders=5`,
`child_funding_mode=PARENT_TRANSFER_POOL_GAP`,
`energy_pool_initial=1500`, `hazard_damage=0`. Chamber layouts
(food_ladder, tight_gradient) unchanged from v0.18/v0.19/v0.20/v0.21/v0.22.

### Demand-math projection (anchored on v0.22 hazard=0 at influx=1.0 food_ladder)

v0.22 hazard-0 food_ladder telemetry per 8-seed aggregate:
births=249, b>50=116, food=670, respawn=478, pool_min=0, pool_end=38,
r_blk=98, b_blk=12, residual=0, in_influx=1,600 (= 1.0 × 200 × 8),
xfer=3,735 (= 249 × 15). Pool flow per run: out_respawn ≈ 1,195/seed
(59.75 events × 20), out_child_startup ≈ 467/seed (31.1 births × 15),
in_ambient_influx = 200/seed, in_death_residual = 0. Net drain ≈
1,195 + 467 − 200 = 1,462/seed across 200 ticks ≈ 7.31/tick.
Initial pool 1,500/seed → ends at 38/seed (close to projected
~38/seed).

The hazard=0 substrate is **already pool-bound at the v0.22 single
point**: pool_min=0 (drains to zero in every seed), r_blk=98
(respawn-side binding), b_blk=12 (birth-side binding), starvation
deaths=206 (population pressure binding agents). Adding influx is
expected to relieve starvation pressure progressively; removing
influx is expected to push the system into a more starved regime.

Under v0.23:

- **food_ladder arm A (influx=0)**: no ambient credit. Pool drains
  ~7.3/tick from a 1500 budget = ~205/run remaining; but population
  is bigger so actual drain is much higher. Likely heavy starvation,
  significantly fewer births than v0.22 hazard=0 (249).
- **food_ladder arm E (influx=2)**: 400/run influx replenishes
  pool. Births likely well above 249; starvation pressure
  diminishes; pool_end likely high.
- **tight_gradient arm A (influx=0)**: tight's hazard-wall behavior
  at hazard=0 is unobserved. With no hazard wall, agents path
  freely; food consumption rises. Birth count uncertain.
- **tight_gradient arm E (influx=2)**: best case for tight at
  hazard=0. If tight is hazard-wall-bound at hazard=8, removing
  the wall could lift productivity well above v0.21 anchor's 130
  b>50.

### Telemetry to watch

- **Productivity headline.** `total_births`, `births_after_tick_50`,
  `seeds_with_survivors`, `population_end`. Per-chamber per-arm.
- **Pool late-run trajectory.** `pool_min_observed`, `pool_end`,
  `pool_in_ambient_influx` (invariant check), `pool_out_respawn`,
  `pool_out_child_startup`. `pool_in_death_residual` ≈ 0 by
  construction at hazard=0.
- **Death cause distribution.** `total_starvation_deaths` AND
  `total_injury_deaths` per arm. At hazard=0 every arm has
  `total_injury_deaths = 0` by construction. The starvation count
  is the binding-pressure observable.
- **Block telemetry.** `total_pool_birth_denied`,
  `total_pool_respawn_denied`,
  `total_births_blocked_by_parent_energy` (expected 0 throughout).
- **Throughput.** `food_consumed_per_birth`. Under transfer mode
  the system-energy floor per birth is 30 (gap-only); fcpb near
  60 is roughly the metabolic floor for sustainability.
- **Hazard exposure (sanity).** `total_hazard_entries`. At hazard=0
  agents will still enter hazard tiles (the gradient policy's
  damage signal is zero since damage is zero, so avoidance behavior
  is dormant). Comparing entries on food_ladder vs tight at
  hazard=0 isolates "how much do agents enter hazards when
  damage is the only thing absent."
- **v0.20 conservation invariant.**
  `parent_energy_transferred_to_child + pool_out_child_startup ==
  total_births × offspring_start_energy` (H4 from v0.20).

### Operational definitions — pre-committed

- **Primary i\***: per chamber, the **lowest `ambient_influx_rate` at
  which `births_after_tick_50` reaches ≥ 90% of arm E's
  `births_after_tick_50` on that chamber**. Self-referential
  threshold (anchors on each chamber's own arm E observation, not
  on a v0.21/v0.22 prior); we don't yet know what arm E delivers
  on either chamber at hazard=0. If no arm clears 90%, primary
  i\* is recorded as `> 2.0` (the arm-E endpoint should always
  clear 90% of itself, so this fallback should not fire).
- **Secondary i\***: per chamber, the **lowest `ambient_influx_rate`
  at which `total_births` reaches ≥ 90% of arm E's `total_births`
  on that chamber**. Same self-referential structure. Carries the
  v0.21 diagnostic value: when primary and secondary i\* diverge,
  the chamber has a different cost structure for late-run
  compounding (b>50) vs total population.

These definitions are **mode-agnostic and substrate-agnostic** — they
re-use the v0.21 framework with an arm-E reference. The 90% threshold
is the same.

### Three pre-committed outcome bands for the chamber-asymmetry gap

Let `Δ_primary = tight_primary_i* − food_ladder_primary_i*` (positive
means food_ladder transitions earlier). At v0.21 hazard=8,
Δ_primary = 1.0/tick (tight 1.5 − food_ladder 0.5).

| Δ_primary at hazard=0 | interpretation |
|---:|---|
| ≥ +0.5/tick | **Gap survives.** Chamber geometry / food accessibility is load-bearing. food_ladder still transitions earlier; the v0.21 1.0/tick gap was not entirely a hazard-interaction artifact. v0.24+ direction: characterise which geometric feature of food_ladder produces the advantage (pre-food band length, food spatial distribution, capacity). |
| 0 to <+0.5/tick | **Gap collapses.** The v0.21 chamber asymmetry was hazard-interaction-mediated. Both chambers transition at similar i\* once hazards are removed. v0.24+ direction: re-frame the chamber-comparison axis around hazard-interaction dynamics rather than geometry. |
| ≤ −0.5/tick | **Reverses.** tight transitions earlier than food_ladder at hazard=0. Surprising but possible: food_ladder's pre-food band might be net-positive only when the hazard wall makes the alternative path expensive; without hazards, tight's compactness wins. v0.24+ direction: investigate why food_ladder degrades at hazard=0 (is fcpb deeper than tight? are agents wasting steps on the long food_ladder corridor?). |

Tight-improves-dramatically (the third v0.23-call notes outcome) is
not a separate band — it is observed via **tight primary i\* at
hazard=0** independent of the gap. We pre-commit:

| tight primary i\* at hazard=0 | interpretation |
|---:|---|
| ≥ 1.5/tick | tight remained energy-throughput-bound; hazard wall was not the limiting factor. |
| 1.0–1.4/tick | partial relief; hazard wall contributed to v0.21's tight=1.5 anchor but other factors (energy supply, geometry) still bind. |
| ≤ 1.0/tick | **tight was hazard-wall-constrained**. Removing the wall lifts tight's transition substantially. v0.24+ would investigate the mechanism — does the wall block path-length-to-food, or block movement options, or both? |

The gap-band and the tight-i\*-band are independent; both are
read off the v0.23 results.

## Pre-registered hypotheses

Two-tier structure consistent with v0.15..v0.22: **strong-form** for
mechanism + invariants, **cautious-form** for the substantive
chamber-asymmetry question, plus **determinism** for the byte-identity
anchor.

### Strong form (mechanism + invariants)

- **H1.** `pool_in_ambient_influx == ambient_influx_rate ×
  sum(executed_ticks_per_seed)` per arm per chamber. v0.22 hazard=0
  food_ladder had 8/8 survivors (no extinction); v0.23 may produce
  extinction at the lowest-influx arm on either chamber, especially
  tight_gradient arm A. The invariant uses the per-seed executed-tick
  sum; if any v0.23 seed terminates early, the arm's row in the
  sweep report annotates seeds-with-early-termination separately.
- **H2.** v0.20 H4 invariant holds at every v0.23 arm:
  `parent_energy_transferred_to_child + pool_out_child_startup ==
  total_births × offspring_start_energy`.
- **H3.** `reproduction_heat_loss == 0` at every v0.23 arm (transfer
  mode contract).
- **H4.** `births_blocked_by_parent_energy == 0` at every v0.23 arm
  (defensive parent-energy gate; v0.20/v0.21/v0.22 verified empirical
  irrelevance under cost=15, threshold=50 across all transfer-mode
  sweeps to date).
- **H5.** `total_injury_deaths == 0` at every v0.23 arm (hazard=0
  by construction). Direct hard pin.
- **H6.** `pool_in_death_residual == 0` at every v0.23 arm (no
  injury deaths can credit non-zero residual; STARVATION credits
  zero by definition). Direct hard pin.

### Cautious form (frontier shape + chamber asymmetry)

- **H7.** `births_after_tick_50` is monotonically non-decreasing in
  `ambient_influx_rate` across arms A → E on **both chambers**.
  **Cautious in monotonicity strictness; some seeds may produce ties.**
- **H8.** `total_pool_birth_denied + total_pool_respawn_denied` is
  monotonically non-increasing in `ambient_influx_rate` across arms
  A → E on both chambers. **Cautious — the v0.20/v0.21/v0.22
  redistribution finding (transfer mode shifts pool binding from
  respawn-side to birth-side as productivity rises) may produce
  non-monotone components even if the total trends downward.**
- **H9.** **Δ_primary at hazard=0 is in the "gap survives" band
  (≥ +0.5/tick).** Geometry/food-accessibility hypothesis.
  **Cautious; this is the substantive headline.**
- **H10.** **Δ_primary at hazard=0 is in the "gap collapses" band
  (0 to <+0.5/tick).** Hazard-interaction-artifact hypothesis.
  **Cautious; the alternative reading of H9.**
- **H11.** **Δ_primary at hazard=0 is in the "reverses" band
  (≤ −0.5/tick).** food_ladder-degrades-at-hazard=0 hypothesis.
  **Cautious; the inverse outcome.**
  H9/H10/H11 are mutually exclusive; exactly one fires.
- **H12.** **tight primary i\* at hazard=0 ≤ 1.0/tick.**
  Tight-was-hazard-wall-constrained hypothesis.
  **Cautious; independent of H9/H10/H11.** If tight i\* falls below
  1.0/tick, the v0.21 tight=1.5 anchor was driven substantially by
  hazard-wall mechanics rather than energy throughput.
- **H13.** **food_ladder primary i\* at hazard=0 falls below v0.21's
  food_ladder=0.5/tick anchor** (i.e., food_ladder reaches 90% of
  its arm-E b>50 at influx=0/tick — the closed-pool regime).
  Possible because v0.22 already showed food_ladder at influx=1.0,
  hazard=0 substantially exceeds v0.21's plateau; the same dynamic
  may extend to lower influx. **Cautious.**

### Determinism

- **H14.** Arm C on **food_ladder** reproduces v0.22 hazard-0
  byte-identically: aggregate metrics `(total_births,
  births_after_tick_50, seeds_with_survivors, total_food_events,
  total_food_respawn_events, total_pool_respawn_denied,
  total_pool_birth_denied, total_starvation_deaths,
  total_injury_deaths, total_hazard_entries, pool_out_respawn,
  pool_out_child_startup, pool_in_death_residual, pool_min,
  pool_end, parent_energy_transferred_to_child,
  reproduction_heat_loss)` match v0.22 hazard-0 food_ladder exactly.
  The v0.22 anchor: births=249, b>50=116, food=670, respawn=478,
  r_blk=98, b_blk=12, starv=206, inj=0, residual=0.0,
  hazard_entries=200, pool_min=0, pool_end=38.125, xfer=3,735.
  Failure of H14 is a halt condition — wiring leak introduced by
  v0.23.
- **H15.** `V0_19_ARMS`, `V0_20_ARMS`, `V0_21_ARMS`, `V0_22_ARMS`
  continue to produce identical sweep outputs after v0.23 changes
  (no prior surface modified; new `V0_23_ARMS` is purely additive).
  Verified by re-running existing test suites; halt condition.

## Decision rules

- **H9 fires (Δ_primary ≥ +0.5/tick at hazard=0): gap survives.**
  Chamber geometry / food accessibility is load-bearing.
  **Headline finding: the v0.21 1.0/tick chamber asymmetry has
  both a hazard-mediated component AND a geometry component.**
  v0.24 candidate: characterise which food_ladder geometric
  feature is load-bearing (pre-food band length, food spatial
  distribution, chamber width).

- **H10 fires (Δ_primary in 0 to <+0.5/tick at hazard=0): gap
  collapses.** The v0.21 chamber asymmetry was substantially
  hazard-interaction-mediated. **Headline: chamber geometry
  contributes minimally to the productivity transition under
  the conservation substrate; the v0.21 asymmetry was a
  hazard-cull artifact specific to the chambers' hazard
  configurations.** v0.24 candidate: re-frame chamber comparison
  around hazard-interaction dynamics; possibly retire chamber
  asymmetry as a primary axis.

- **H11 fires (Δ_primary ≤ −0.5/tick at hazard=0): reverses.**
  food_ladder degrades at hazard=0; tight transitions earlier.
  **Headline: food_ladder's "advantage" was entirely
  hazard-cull-supplemented (the v0.22 finding extends — even
  the chamber-asymmetric component is hazard-mediated, and
  removing hazards inverts the relationship).** v0.24
  investigates the mechanism (fcpb on each chamber, action-tick
  efficiency, path-length-to-food).

- **H12 fires (tight primary i\* ≤ 1.0/tick at hazard=0): tight
  was hazard-wall-constrained.** Independent of the gap-band
  outcome. **Refines: tight_gradient at hazard=8 was binding on
  the hazard wall, not energy throughput.** v0.24 could lift
  hazard_damage on tight specifically (parameterise tight's
  hazard density / wall depth) to characterise the
  wall-vs-throughput tradeoff on that chamber.

- **H13 fires (food_ladder primary i\* < 0.5/tick at hazard=0):**
  the v0.22 food_ladder finding extends to the broader frontier.
  food_ladder under transfer + hazard=0 is **not pool-bound at
  any influx in {0..2.0}**, or at least reaches its plateau
  earlier than v0.21 anchored. This is mechanism-consistent
  with H9 (geometry-supports-productivity) but doesn't
  discriminate it from H10 — both can produce H13.

- **H1/H2 invariant fails.** Influx accounting bug or
  transfer-mode ledger bug. Halt; v0.23 results uninterpretable.

- **H5 fails (any v0.23 arm produces injury_deaths > 0).**
  hazard_damage threading regression. Halt and audit.

- **H6 fails (any v0.23 arm produces pool_in_death_residual >
  0).** Death-cause mapping regression (some non-STARVATION,
  non-INJURY death credit-path active). Halt and audit.

- **H14 fails.** Wiring defect. Halt; v0.23 results
  uninterpretable.

- **H15 fails.** v0.19/v0.20/v0.21/v0.22 contracts broken.
  Halt.

## Out of scope (v0.23)

- **Long-window observations.** v0.24+ candidate.
- **Pool-size sweep at hazard=0.** v0.24+ candidate.
- **Hazard × influx cross-product.** v0.24+ candidate.
- **Reproduction efficiency < 1.0.** v0.24+ candidate.
- **Other chamber variations** (width, food band, capacity).
  v0.24+ candidate, conditional on the v0.23 result.
- **POOL_FULL at hazard=0.** Out of scope; the chamber-asymmetry
  question was characterised under TRANSFER and that's the
  controlled regime.
- **Other influx grids.** Held at v0.21's 5-point grid for
  cross-version comparability.
- **Other pool sizes.** Held at 1500.
- **HedonismPolicy comparisons.** Quarantined per v0.2 spec.

## Implementation notes

### File-level changes

- **Modify:** [[src/hedonism_harness/experiments/comparison_grid.py]]
  — add `V0_23_ARMS` tuple of five `Arm` instances per the table
  above. Every arm has `hazard_damage=0.0`. ~70 LOC. No code-path
  changes; arm definitions only.
- **New:** [[scripts/v0.23_sweep.py]] — sweep driver mirroring
  `scripts/v0.21_sweep.py`; runs both chambers (food_ladder AND
  tight_gradient). Headline table includes the v0.22 starvation/
  injury split columns. ~80 LOC.
- **New:** `tests/test_comparison_grid_v0_23.py` — V0_23_ARMS shape
  test; substrate-economics-fixed test; `hazard_damage=0` across
  every arm; bit-identity anchor smoke test (arm C on food_ladder
  runs without raising and produces ChamberRunResult with
  `injury_deaths=0`). ~120 LOC.
- **No changes** to `core/`, `model.py`,
  `experiments/fear_hunger_chamber.py`, or any v0.20/v0.21/v0.22
  surface. The mechanism is unchanged; only configuration varies.
- **Documented:** this file (`docs/experiments/fear_hunger_v0.23.md`);
  results appended after the sweep.

### Determinism contract

- `V0_19_ARMS`, `V0_20_ARMS`, `V0_21_ARMS`, `V0_22_ARMS` continue
  to produce identical sweep outputs after v0.23 changes (no prior
  surface modified).
- Arm C on food_ladder reproduces v0.22 hazard-0 byte-identically
  (H14).
- The v0.20 H4 invariant continues to hold per arm (H2).

### LOC estimate

- `experiments/comparison_grid.py`: +70 LOC (V0_23_ARMS).
- `scripts/v0.23_sweep.py`: ~80 LOC (sweep driver, two chambers).
- New tests: ~120 LOC.
- This doc: ~520 LOC.

Total v0.23 implementation: ~790 LOC. Comparable to v0.21
(~690 LOC) and v0.22 (~725 LOC). v0.23 introduces no new mechanism
— it is a focused chamber-asymmetry isolation on the v0.22
hazard=0 substrate.

## References

- [[docs/experiments/fear_hunger_v0.22.md]] — v0.22 results;
  the recycling-as-net-tax finding that opened the chamber-asymmetry
  mechanism question. Source of the v0.23 byte-identity anchor
  (food_ladder hazard-0 at influx=1.0: 249 / 116 / 670 / 478).
- [[docs/experiments/fear_hunger_v0.21.md]] — v0.21 results;
  the original chamber-asymmetric frontier (food_ladder primary
  i\*=0.5, tight primary i\*=1.5, gap=1.0/tick) at hazard=8 default,
  the comparison anchor for the gap-band decision rule.
- [[docs/experiments/fear_hunger_v0.20.md]] — v0.20 results;
  strict-transfer reproduction mechanism that v0.23 inherits.
  Source of the H4 conservation invariant carried forward to v0.23 H2.
- [[docs/specs/v0.2_reflex_cell_spec.md]] §"Comparison framework" —
  the substrate axis.

---

## Results

**Status:** executed 2026-05-05. 80 runs (5 arms × 2 chambers × 8 seeds),
30s wall time. All hard pins hold (H1/H5/H6/H14/H15). The
chamber-asymmetry gap survives hazard removal at the H9/H10 boundary
(Δ_primary = +0.5/tick). Unexpected sub-finding: **tight_gradient
gets worse at hazard=0**, not better — tight primary i\* rises from
1.5/tick (hazard=8 v0.21) to 2.0/tick (hazard=0 v0.23). The hazard
wall was net-supportive on tight, mirroring v0.22's "recycling was a
net tax" finding on food_ladder but with the opposite sign relative
to expectations.

### Headline tables

#### tight_gradient (hazard=0)

| arm | influx | births | b>50 | surv | food | respawn | fcpb  | pool_min | pool_end | residual | starv | inj | haz_ent | r_blk | b_blk | xfer  |
|-----|-------:|-------:|-----:|------|-----:|--------:|------:|---------:|---------:|---------:|------:|----:|--------:|------:|------:|------:|
| A   | 0.0    | 238    |  92  | 8/8  |  611 |    419  | 51.34 |       0  |       6  |     0.0  |  233  |  0  |     42  |  157  |   61  | 3,570 |
| B   | 0.5    | 243    |  97  | 8/8  |  640 |    448  | 52.67 |       0  |      24  |     0.0  |  219  |  0  |     42  |  128  |   20  | 3,645 |
| C   | 1.0    | 246    | 100  | 8/8  |  673 |    481  | 54.72 |       0  |      36  |     0.0  |  202  |  0  |     42  |   95  |   42  | 3,690 |
| D   | 1.5    | 253    | 107  | 8/8  |  703 |    511  | 55.57 |       0  |      48  |     0.0  |  189  |  0  |     42  |   65  |   38  | 3,795 |
| E   | 2.0    | 265    | 119  | 8/8  |  733 |    541  | 55.32 |       0  |      51  |     0.0  |  186  |  0  |     42  |   35  |   90  | 3,975 |

#### food_ladder (hazard=0)

| arm | influx | births | b>50 | surv | food | respawn | fcpb  | pool_min | pool_end | residual | starv | inj | haz_ent | r_blk | b_blk | xfer  |
|-----|-------:|-------:|-----:|------|-----:|--------:|------:|---------:|---------:|---------:|------:|----:|--------:|------:|------:|------:|
| A   | 0.0    | 239    | 106  | 8/8  |  610 |    418  | 51.05 |       0  |       7  |     0.0  |  234  |  0  |    188  |  158  |   69  | 3,585 |
| B   | 0.5    | 246    | 113  | 8/8  |  639 |    447  | 51.95 |       0  |      21  |     0.0  |  220  |  0  |    197  |  129  |   28  | 3,690 |
| C   | 1.0    | 249    | 116  | 8/8  |  670 |    478  | 53.82 |       0  |      38  |     0.0  |  206  |  0  |    200  |   98  |   12  | 3,735 |
| D   | 1.5    | 258    | 125  | 8/8  |  702 |    510  | 54.42 |       0  |      41  |     0.0  |  195  |  0  |    208  |   66  |   33  | 3,870 |
| E   | 2.0    | 264    | 131  | 8/8  |  733 |    541  | 55.53 |       0  |      52  |     0.0  |  185  |  0  |    216  |   35  |   51  | 3,960 |

### Hypothesis adjudication

| H | claim | result |
|---|---|---|
| H1 | `pool_in_ambient_influx == ambient_influx_rate × sum(executed_ticks)` | **HOLDS.** Every arm 8/8 survivors → executed-tick sum = 1,600. Influx products: 0/800/1,600/2,400/3,200 — match every arm on both chambers. |
| H2 | `parent_energy_transferred + pool_out_child_startup == total_births × offspring_start_energy` | **HOLDS.** Transfer-mode contract: xfer = births × 15 across all 10 arms; pool_out_child_startup = births × 15 by definition; sum = births × 30. |
| H3 | `reproduction_heat_loss == 0` | **HOLDS** (transfer mode contract). |
| H4 | `births_blocked_by_parent_energy == 0` | **HOLDS.** No arm produced parent-energy-gate blocks. |
| H5 | `total_injury_deaths == 0` | **HOLDS — hard pin.** All 10 arms reported inj=0. |
| H6 | `pool_in_death_residual == 0` | **HOLDS — hard pin.** All 10 arms reported residual=0.0. |
| H7 | b>50 monotone non-decreasing in influx | **HOLDS — strong form.** tight: 92→97→100→107→119; food_ladder: 106→113→116→125→131. Strictly monotonic on both chambers. |
| H8 | r_blk + b_blk monotone non-increasing in influx | **PARTIAL.** food_ladder: 227→157→110→99→86 — strictly monotonic. tight: 218→148→137→103→125 — non-monotonic at the high end (b_blk component: 61→20→42→38→90). The redistribution finding (v0.20/v0.21/v0.22) extends to v0.23 tight: as productivity rises, pool binding migrates from respawn-side to birth-side. Cautious form held. |
| H9 | Δ_primary ≥ +0.5/tick (gap survives) | **FIRES at the boundary.** Δ_primary = 0.5/tick exactly. food_ladder primary i\* = 1.5; tight primary i\* = 2.0. Geometry/food-accessibility is load-bearing; the v0.21 1.0/tick gap was approximately half hazard-mediated, half geometric. |
| H10 | 0 ≤ Δ_primary < +0.5/tick (gap collapses) | **DOES NOT FIRE** (boundary case resolves to H9 per pre-reg's `≥ +0.5` band). |
| H11 | Δ_primary ≤ −0.5/tick (reverses) | **DOES NOT FIRE.** food_ladder still transitions earlier than tight. |
| H12 | tight primary i\* ≤ 1.0/tick (tight was hazard-wall-constrained) | **DOES NOT FIRE.** tight primary i\* at hazard=0 is **2.0/tick**, *worse* than the v0.21 hazard=8 anchor (1.5/tick). Tight is not hazard-wall-constrained; removing the wall made tight harder, not easier. |
| H13 | food_ladder primary i\* < 0.5/tick at hazard=0 | **DOES NOT FIRE** under the self-referential criterion (food_ladder i\* = 1.5/tick at hazard=0 because arm E rose to b>50=131, lifting the 90% threshold to 117.9). In **absolute** terms, food_ladder at hazard=0 influx=0 produces b>50=106 — already 15% above v0.21's hazard=8 plateau (92), so the v0.22 finding extends qualitatively even though the relative-criterion threshold did not catch it. |
| H14 | byte-identity arm C food_ladder vs v0.22 hazard-0 | **HOLDS — exact match.** births=249, b>50=116, food=670, respawn=478, r_blk=98, b_blk=12, starv=206, inj=0, residual=0.0, haz_entries=200, pool_min=0, pool_end=38, xfer=3,735. Identical to v0.22 anchor on every column. |
| H15 | V0_19/20/21/22 unchanged | **HOLDS.** Test suite 652→662 (purely additive); ruff clean; core_smoke_test green. |

### Headline finding: chamber asymmetry has both hazard and geometry components

The v0.21 1.0/tick chamber-asymmetry gap (food_ladder 0.5 vs tight 1.5
at hazard=8) **partially survives hazard removal**: at hazard=0 the
gap is +0.5/tick (food_ladder 1.5 vs tight 2.0). H9 fires at the band
boundary. Geometry/food-accessibility is **load-bearing**, and the
hazard-mediated component is roughly half of the v0.21 gap. The
chamber comparison axis remains a meaningful experimental dimension
under the conservation substrate.

Cross-chamber productivity at every shared influx (b>50 ratio
food_ladder/tight): 1.15, 1.16, 1.16, 1.17, 1.10. food_ladder
out-produces tight by 10–17% at every influx point under hazard=0 —
a clean geometric advantage independent of the hazard mechanism.

### Sub-finding: tight gets worse at hazard=0 (the v0.22 mirror, opposite sign)

v0.22 found that recycling on food_ladder was a **net tax** —
removing hazards lifted food_ladder productivity 26% above the v0.21
plateau. v0.23 reveals the **opposite sign on tight**: tight primary
i\* rises from 1.5/tick (hazard=8) to 2.0/tick (hazard=0). Removing
the hazard cull made tight harder, not easier.

Mechanism candidates (deferred to v0.24+ to discriminate):

1. **Hazard cull was throughput-relieving on tight.** At hazard=8,
   tight's hazard wall culled agents that would otherwise contribute
   to pool drain via metabolism + respawn pressure. The cull
   functioned as a population-control mechanism specific to tight's
   geometry; without it, more agents survive into deeper starvation
   regimes and the pool-bound binding intensifies.

2. **Hazard avoidance on tight was load-bearing for food access.**
   At hazard=8, the GradientPolicy's avoidance signal routed tight
   agents around the hazard wall toward the food zone. At hazard=0,
   that signal is dormant. tight's compact geometry means the
   straight-line "through hazard" path may not actually reach
   food more efficiently than the v0.21 routing, and the loss of
   the avoidance signal degrades tight's effective food access.

3. **Combination.** Both mechanisms are plausible and not
   mutually exclusive. v0.24+ candidate to discriminate is
   parameterising hazard-avoidance independently of hazard-damage
   in `GradientPolicy`.

food_ladder shows the opposite pattern: haz_entries clustered at
188–216 across influx points (vs 200 at the v0.22 hazard=0 anchor —
consistent), and productivity rose smoothly across all influx
points. food_ladder's pre-food band remains accessible regardless
of hazard signal; tight's geometry depends on the avoidance behavior
more than was previously visible.

### Sub-finding: hazard=0 substrate is pool-bound across all influxes

Every arm on both chambers hit `pool_min_observed = 0` and produced
substantial r_blk + b_blk. Even arm E (influx=2.0) on tight hit
pool_min=0 with 35 r_blk + 90 b_blk (b_blk increased D→E),
indicating birth-side pool binding intensifies as influx relieves
respawn-side binding (the v0.20–v0.22 redistribution). Starvation
pressure remains the binding observable: 185–234 starvations per
arm across the sweep. fcpb clusters at 51–56, near the transfer-mode
metabolic floor (~60), confirming the substrate is paying for
births close to its energetic limit.

### Hazard exposure asymmetry at hazard=0

A telemetry-only observation: at hazard=0, agents enter hazard
tiles freely (no avoidance). On food_ladder the per-arm
haz_entries ranged 188–216 (mildly influx-dependent). On tight,
**every arm reported haz_entries=42 exactly** — a striking
constant. tight's compact geometry and reflex-baseline policy
constrain hazard-tile residency to a fixed pattern independent of
influx-driven population dynamics. Possibly reflects that tight's
hazard band is small enough that early agents establish a stable
transit pattern that later cohorts inherit; on food_ladder the
larger hazard surface produces population-size-dependent exposure.

### What this changes about the v0.21 framing

- v0.21's chamber asymmetry is **partially preserved** under
  hazard removal: ~half geometric, ~half hazard-mediated. The
  geometric component is real and worth characterising further
  (v0.24+ candidate).
- v0.21's tight=1.5/tick anchor was **not hazard-wall-constrained**
  in the sense H12 anticipated. Tight's hazard wall was
  net-supportive (mirrors v0.22's food_ladder finding); removing
  it lifts the i\* threshold rather than lowers it.
- v0.21/v0.22 framing of "tight is starvation-dominated, food_ladder
  is hazard-dominated" survives and sharpens: tight at hazard=0 is
  even more starvation-dominated (no recycling/cull buffer);
  food_ladder at hazard=0 has more headroom because its geometry
  self-supplies the food access that tight's hazard avoidance was
  providing on tight.

### Hazard-perception caveat (interpretation note)

`hazard_damage=0` zeroes both the per-tile damage applied at
runtime AND the avoidance signal — `GradientPolicy` keys avoidance
off the per-tile damage value, so at damage=0 the avoidance
behavior is dormant (haz_entries telemetry above confirms this).
v0.23 is therefore the **broader hazard-removal test** in this
taxonomy: damage AND avoidance both go to zero; only the cell-kind
geometry (the hazard band still exists as a region of non-FOOD,
non-SAFE cells agents traverse) is preserved.

A geometry-isolated test (damage=0 with avoidance still active)
would require a `GradientPolicy` parameterisation decoupling
perceived-hazard from actual-damage. That is a v0.24+ candidate
and is not in scope here. Any v0.23 attribution of "tight was not
hazard-wall-constrained" should be read as "tight does not benefit
from removing both damage and avoidance simultaneously" — the
discrimination between damage-only and avoidance-only effects on
tight is the natural follow-up.

### v0.24+ candidates surfaced by v0.23

- **Decouple hazard damage from hazard avoidance.** A
  parameterised `GradientPolicy` (e.g.,
  `hazard_avoidance_weight` independent of damage) would
  discriminate "geometry-only" from "perception-only" effects on
  tight, and test the two mechanism candidates above.
- **Long-window stability** at hazard=0 on the high-productivity
  food_ladder arms — does the substrate stay productive at
  n_ticks ∈ {500, 1000} or does the pool eventually exhaust?
- **Pool-size sweep at hazard=0** to characterise the new cliff
  position now that the hazard cull is removed.
- **Hazard × influx cross-product** — both v0.22 (food_ladder)
  and v0.23 (both chambers at hazard=0) suggest the
  hazard-vs-influx tradeoff surface is non-trivial and
  chamber-asymmetric; mapping it fully would clarify the
  population-control dynamics.

### Implementation summary

- **Code:** ~95 LOC (`V0_23_ARMS` in `comparison_grid.py`).
- **Tests:** ~190 LOC (`tests/test_comparison_grid_v0_23.py`,
  10 new tests; suite 652→662).
- **Sweep driver:** ~95 LOC (`scripts/v0.23_sweep.py`).
- **Wall time:** 30s on 80 runs (every seed completed 200 ticks;
  no early-termination).
- **No core/model.py/fear_hunger_chamber.py changes.** The seam
  v0.22 shipped (`Arm.hazard_damage`, `total_injury_deaths`)
  was sufficient.
- **CI gate at handoff time:**
  ```
  uv run ruff check .             ok
  uv run ruff format --check .    ok
  uv run --all-extras pytest      662 passed
  uv run --all-extras python scripts/core_smoke_test.py  ok
  ```
