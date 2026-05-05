# v0.22 — narrow hazard-damage sweep on food_ladder under strict-transfer reproduction

**Status:** pre-registration; not yet executed.
**Date:** 2026-05-05
**Branch:** `claude/hedonism-harness-0.22-4gshB`
**Predecessors:** v0.18 (food respawn cooldown — first compounding under
non-saturating food), v0.19 (strict mass-energy conservation — substrate
compounds when budget or steady-state influx covers demand), v0.20
(parent-transfer + pool-gap reproduction — eliminating reproduction heat
loss lifts compounding in v0.19's binding regimes), v0.21 (influx
frontier under strict-transfer reproduction — chamber-asymmetric
frontier shape: food_ladder is a phase transition saturating at
influx≥1.0/tick to 143/92, tight_gradient is a graded gradient; primary
i\* food_ladder=0.5/tick, primary i\* tight=1.5/tick — a 1.0/tick gap
consistent with hazard-residual recycling but not yet a direct test of
the mechanism).
**Spec:** [[docs/specs/v0.2_reflex_cell_spec.md]] §"Comparison framework"
(substrate axis).

## Question

v0.21 produced a striking chamber asymmetry under strict-transfer
reproduction at `pool_initial=1500`: food_ladder reaches the v0.18 K-50
productivity plateau (143 / 92 b>50) at `ambient_influx_rate=1.0/tick`,
while tight_gradient needs 1.5/tick to clear primary i\*. The 1.0/tick
gap is **consistent with** the hypothesis that food_ladder receives an
effective extra ~1.0/tick of usable energy from hazard-injury deaths
crediting residual body energy back to the pool, but the v0.21 sweep
**did not test the mechanism directly**. Three candidate explanations
sit on the table:

(a) **Recycling-as-effective-influx.** Hazard-injury deaths credit
`max(0, body.energy)` to the pool on every AgentDied; on food_ladder
this back-of-envelope was ~80 energy/seed/200 ticks ≈ 0.4/tick of
"effective" recycling. Population growth and discrete-deposit timing
could amplify this above the linear estimate.

(b) **Death timing × population growth.** Recycled energy may be more
"useful" than ambient influx because deposits arrive at
population-correlated timings (cohorts dying together flood the pool
when the surviving population most needs to fund respawn / births), so
the same total energy buys more births than continuous ambient influx
would.

(c) **Chamber geometry as buffer.** food_ladder's pre-food band permits
multi-step refueling without crossing the hazard wall; capacity layout
plus food spatial distribution could fund productivity independent of
recycling.

**v0.22 isolates (a) + (b) from (c) with the cleanest possible control:
sweep `hazard_damage ∈ {0, 4, 8, 12}` on food_ladder under transfer mode
at `pool_initial=1500`, `ambient_influx_rate=1.0/tick` (the v0.21
productive transition point), and read the productivity response.** At
`hazard_damage=0` no agent dies of injury — INJURY deaths are zero by
construction, STARVATION deaths credit 0 residual by definition (energy
≤ 0 was the trigger), so `pool_in_death_residual` collapses toward zero.
The chamber's geometry (pre-food band, hazard tile *positions*, food
spatial layout) is preserved exactly. **If productivity drops at
hazard=0, recycling/injury dynamics are load-bearing under this layout.
If productivity is preserved or rises, geometry/capacity is the lever.**

## What this slice tests, and what it does NOT test

### Tests

- The **causal role of hazard-residual recycling** in the v0.21
  food_ladder productivity plateau, by removing the recycling channel
  while preserving chamber geometry exactly.
- The **shape of the productivity response to hazard_damage** across
  {0, 4, 8, 12}. Smooth, sharp, or non-monotone? hazard=4 and hazard=12
  bracket the v0.21 default (8.0); hazard=0 is the crucial control.
- Whether **injury deaths are net-positive (fuel via recycling) or
  net-negative (cull above geometric capacity)** for productivity at
  this layout + substrate. The v0.21 finding that food_ladder saturates
  at 92 b>50 was framed as a chamber-capacity ceiling; if hazard_damage=0
  lifts b>50 above 92, injury deaths were a *cull*, not a fuel.

### Does NOT test

- **The same mechanism at other influx rates.** v0.22 holds influx=1.0
  fixed (the v0.21 productivity transition for food_ladder); the
  recycling channel may interact non-linearly with influx, but
  characterising that surface is a v0.23+ question conditional on the
  v0.22 result.
- **The mechanism on tight_gradient.** tight is starvation-dominated
  with near-zero recycling already; sweeping hazard_damage on tight
  would test a near-null channel and is not informative.
- **Other geometric variations.** Chamber width, hazard density (count
  of hazard *tiles*), pre-food band length, food spatial distribution,
  and capacity all stay fixed. v0.22 is deliberately not a "geometry
  sweep" — it is a single-variable test of one mechanism. A narrow
  hazard-density sweep may follow if the v0.22 result motivates it.
- **POOL_FULL mode.** v0.22 stays under PARENT_TRANSFER_POOL_GAP. The
  recycling-vs-geometry question is mode-orthogonal, but the v0.21
  frontier was characterised under TRANSFER and that's where the
  asymmetry lives.
- **Reproduction efficiency < 1.0.** Deferred per the post-v0.20 plan;
  v0.23+ candidate.

### Deferred (v0.23+ candidates)

- **Hazard-density sweep** (vary the number of hazard *tiles* at fixed
  hazard_damage), conditional on v0.22 indicating recycling matters.
- **Reproduction efficiency parameterisation** (continuous heat-loss
  fraction). Conditional on a clean conservation-faithful frontier.
- **Pool-debit timing split** (separate budgets for respawn-side vs
  birth-side draws) — follow-on to the v0.20/v0.21 b_blk/r_blk
  redistribution finding.
- **Multi-cell-tier directional EMA** still deferred until the
  substrate question is settled.
- **HedonismPolicy on conservation substrate** still quarantined per
  v0.2 spec.

## Conservation framing — unchanged from v0.20

v0.22 introduces no new mechanism. The six-flow conservation
bookkeeping under PARENT_TRANSFER_POOL_GAP is preserved exactly:

```
Parent: -reproduction_cost   (15, transferred to child via system ledger)
Pool:   -(offspring_start_energy - reproduction_cost)   (15, gap)
Pool:   +ambient_influx_rate per tick   (1.0/tick, all arms)
Pool:   +max(0, body.energy) on AgentDied   (death residual; varies by hazard_damage)
Child:  +offspring_start_energy   (30)
System energy delta per birth: 0   (no heat loss at reproduction)
```

The only knob that varies across arms is `hazard_damage`. All other
v0.20/v0.21 parameters (`reproduction_cost=15`, `offspring_start_energy=30`,
`pool_initial=1500`, `ambient_influx_rate=1.0`, `food_respawn_cooldown=50`,
`child_funding_mode=PARENT_TRANSFER_POOL_GAP`, reflex-baseline policy,
`unbounded_mutation=True`, `n_ticks=200`, `n_founders=5`) are held
constant.

### Why fix `ambient_influx_rate=1.0`

1.0/tick is the v0.21 productivity transition point on food_ladder —
the lowest influx at which the substrate reaches the 143 / 92 plateau.
Any lower and the substrate is influx-bound (recycling can't compensate
fast enough); any higher and the substrate is in the saturation plateau
(excess influx accumulates in pool buffer, masking the recycling
contribution). 1.0/tick is the operating point where the recycling
channel's contribution should be most measurable.

### Why these hazard_damage points

`{0, 4, 8, 12}` brackets the current chamber default (`hazard_damage=8.0`,
the value `build_chamber_layout` has used through v0.18..v0.21):

- **0** is the crucial control: zero injury deaths → zero hazard-residual
  recycling. Geometry preserved.
- **4** is sub-default: agents can survive ~25 ticks of continuous
  hazard residency (vs ~12 at default). Recycling pressure reduced but
  not eliminated.
- **8** is the v0.18..v0.21 default: **byte-identity anchor against
  v0.21 transfer-1500-influx-1.0 food_ladder** (143 / 92).
- **12** is super-default: agents can survive ~8 ticks of continuous
  hazard residency. Higher cull rate; more recycling pressure.

Even spacing privileges no prior on the response shape. The hazard=8
byte-identity anchor is a free determinism check (`run_chamber` will
default to `hazard_damage=8.0` when the v0.22 seam is `None`, so the
hazard=8 arm reproduces v0.21 transfer-1500-influx-1.0 by construction).

## Mechanism

### `Arm.hazard_damage` seam

A single new optional field on
[[src/hedonism_harness/experiments/comparison_grid.py]]:

```python
hazard_damage: float | None = None
```

`None` (default) preserves v0.7..v0.21 bit-identity for every existing
arm: `_run_one_arm_seed` does not pass the kwarg, `run_chamber` does
not pass it to `build_chamber_layout`, and the default `hazard_damage=8.0`
holds. A finite value threads into the chamber layout's
`hazard_damage_default` field on the resolved `WorldConfig`.

### Threading path

Mirrors the v0.18 `food_respawn_cooldown`, v0.19 `energy_pool_initial`,
and v0.20 `child_funding_mode` patterns:

1. [[src/hedonism_harness/experiments/comparison_grid.py]] —
   `Arm.hazard_damage: float | None = None`. In `_run_one_arm_seed`,
   pass `hazard_damage=arm.hazard_damage` into `run_chamber`.
2. [[src/hedonism_harness/experiments/fear_hunger_chamber.py]] —
   `run_chamber` accepts `hazard_damage: float | None = None` kwarg.
   When non-None, replace the `build_chamber_layout(layout)` call with
   `build_chamber_layout(layout, hazard_damage=hazard_damage)`. The
   existing `build_chamber_layout` already accepts a `hazard_damage`
   kwarg and threads it into `WorldConfig.hazard_damage_default`.

No changes to `core/`, `model.py`, `events.py`, the energy pool, or
the reproduction path. The mechanism is unchanged; only the per-tile
hazard damage value varies.

### Determinism — endpoints anchor against v0.21

The hazard=8 arm reproduces v0.21 transfer-1500-influx-1.0 food_ladder
**byte-identically** by construction: when the v0.22 seam is
`hazard_damage=8.0`, the threaded value matches the
`build_chamber_layout` default that v0.21 ran with. Per-tick agent
state, per-flow pool telemetry, and the full event stream must match
v0.21 sweep telemetry on food_ladder (143 births, 92 b>50, 674 food
events, 501 respawn events, pool_min=2, pool_end=257, r_blk=3, b_blk=0,
xfer=2,145).

`V0_19_ARMS`, `V0_20_ARMS`, and `V0_21_ARMS` continue to produce
identical sweep outputs after v0.22 changes (no v0.19/v0.20/v0.21
surface modified). The new `Arm.hazard_damage` field defaults to `None`,
which preserves the existing `_run_one_arm_seed → run_chamber` call
shape exactly.

## Arms

Four arms × one chamber (food_ladder) × eight seeds = **32 runs**.

| arm | tier | hazard_damage | label |
|---|---|---:|---|
| A | crucial control | 0.0 | hazard-0 (zero injury deaths; recycling-vs-geometry control) |
| B | frontier | 4.0 | hazard-4 (sub-default; reduced recycling) |
| C | endpoint anchor | 8.0 | hazard-8 (= v0.21 transfer-1500-influx-1.0 default) |
| D | frontier | 12.0 | hazard-12 (super-default; elevated recycling) |

`pool_initial=1500`, `ambient_influx_rate=1.0`, `food_respawn_cooldown=50`,
`child_funding_mode=PARENT_TRANSFER_POOL_GAP`, `offspring_start_energy=30`,
`energy_cost=15`, `energy_threshold=50`, `unbounded_mutation=True`,
reflex-baseline policy, `n_ticks=200`, `n_founders=5`. Chamber layout
unchanged from v0.18/v0.19/v0.20/v0.21; only the per-tile hazard damage
value varies. **Same 8 seeds (1..8) as v0.21** so per-seed comparisons
are interpretable.

### Demand-math projection (anchored on v0.21 transfer-1500-influx-1.0 food_ladder)

v0.21 transfer-1500-influx-1.0 food_ladder telemetry per 8-seed
aggregate: births=143, b>50=92, food=674, respawn=501, pool_min=2,
pool_end=257, r_blk=3, b_blk=0, in_influx=1,600 (= 1.0 × 200 × 8),
xfer=2,145 (= 143 × 15). Pool flow per run: out_respawn ≈ 1,253/seed
(62.6 events × 20), out_child_startup ≈ 268/seed (17.9 births × 15),
in_ambient_influx = 200/seed, in_death_residual ≈ unknown but predicted
~80–100/seed (extrapolating from v0.20 transfer-1500 food_ladder's
~80/seed at influx=0). Net drain ≈ 1,253 + 268 − 200 − ~90 = ~1,231/seed
across 200 ticks ≈ 6.16/tick. Initial pool 1,500/seed → ends at ~270/seed
(close to observed 257/seed).

Under v0.22:

- **hazard=0**: in_death_residual collapses to ~0 (STARVATION-only deaths
  credit 0). Net drain rises by ~90/seed → ~1,321/seed ≈ 6.61/tick. Naive
  projection: pool runs ~90/seed lower. **But:** with no injury culling,
  the surviving population is larger throughout the run, which raises
  food consumption → respawn drain → net drain. The naive projection
  understates the substrate's response. The empirical question is
  whether the post-cull-removal substrate still funds productive
  compounding.
- **hazard=4**: agents survive longer in hazard residency; injury deaths
  fall and shift later in the run. Recycling deposits arrive less often
  but with higher residual energy each. Net effect uncertain.
- **hazard=8**: anchor. Reproduces v0.21 exactly.
- **hazard=12**: agents die in hazard residency more quickly. Recycling
  deposits arrive earlier and more often, with lower residual energy
  each. Total residual flux probably similar to hazard=8; timing shifts.

### Telemetry to watch

The decisive comparison is mode-of-mechanism, not just population
counts. v0.22 tracks:

- **Productivity headline.** `total_births`,
  `births_after_tick_50`, `seeds_with_survivors`, `population_end`.
- **Pool late-run trajectory.** `pool_min_observed`, `pool_end`,
  `pool_in_death_residual`, `pool_in_ambient_influx` (invariant check),
  `pool_out_respawn`, `pool_out_child_startup`.
- **Death cause distribution.** `total_starvation_deaths` AND
  `total_injury_deaths` per arm. `ChamberRunResult` already tracks
  both; `ArmCellAggregate` currently only surfaces
  `total_starvation_deaths` and v0.22 adds
  `total_injury_deaths: int = 0` (default 0 preserves bit-identity
  for prior aggregates). At hazard=0 `total_injury_deaths = 0` by
  construction; at higher hazards the STARVATION:INJURY ratio
  shifts. **The decisive disambiguation in the ambiguous band
  (84–90)** is the injury-vs-starvation split: low injury_deaths +
  high hazard_entries = "agents avoided hazards" (recycling channel
  was mechanically dormant); high injury_deaths = "channel active".
- **Hazard exposure.** `total_hazard_entries`. If agents avoid hazard
  tiles at all damage levels, the recycling channel is mechanically
  dead even before hazard=0. If `total_hazard_entries` is
  approximately constant across arms but `pool_in_death_residual`
  scales with hazard_damage, the channel is operating as expected.
- **Block telemetry.** `total_pool_birth_denied`,
  `total_pool_respawn_denied`,
  `total_births_blocked_by_parent_energy` (expected 0 throughout per
  v0.20/v0.21 prior).
- **Throughput stability.** `food_consumed_per_birth` — should stay
  in food_ladder's transfer-mode range (~94–100 from v0.20/v0.21).
  Wild deviation indicates a mechanism leak.
- **v0.20 conservation invariant.**
  `parent_energy_transferred_to_child + pool_out_child_startup ==
  total_births × offspring_start_energy` (H4 from v0.20).

### Operational definitions — pre-committed

The v0.22 hypotheses below reference numerical thresholds against
arm A's `births_after_tick_50` (b>50). The reference plateau from
v0.21 is **food_ladder b>50 = 92** at influx≥1.0 (the saturation
ceiling under transfer mode + hazard=8 default). The v0.21 i\*
anchor at influx=0.5 was b>50 = 85. We pre-commit four bands:

| arm A b>50 | interpretation |
|---:|---|
| ≤ 83 | **strong evidence recycling/injury dynamics matter**; productivity collapses back below the v0.21 i\*=0.5 anchor (b>50=85); recycling was load-bearing |
| 84–90 | **ambiguous boundary**; inspect pool_in_death_residual, total_starvation_deaths, total_hazard_entries, b_blk, r_blk to disambiguate |
| 91–94 | **strong evidence geometry/capacity is sufficient**; productivity preserved within rounding of the 92 plateau; recycling is not load-bearing under this layout |
| ≥ 95 | **injury-deaths-as-cull hypothesis fires**; removing the cull lifts productivity above what recycling-supplemented runs achieved. Recycling is a *tax* not a *fuel* on this layout. |

The bands deliberately give the ambiguous middle (84–90) explicit
mass — b>50 is an integer count across 8 seeds, so single-birth-per-seed
differences are sub-noise on a 92-baseline. Anything in the ambiguous
band needs the secondary mechanism telemetry (residual flux, death
distribution, blocks) to resolve.

These bands are **mode-agnostic** within v0.22's parameterisation (same
chamber, influx, pool, mode) and apply to arm A only. Arms B/C/D are
read against arm A and the v0.21 reference (92).

## Pre-registered hypotheses

Two-tier structure consistent with v0.15..v0.21: **strong-form** for
mechanism + invariants, **cautious-form** for the substantive
causal-mechanism question, plus **determinism** for the byte-identity
anchor.

### Strong form (mechanism + invariants)

- **H1.** `pool_in_ambient_influx == ambient_influx_rate ×
  sum(executed_ticks_per_seed)` per arm. `run_chamber` breaks the
  per-tick loop early when `_any_alive(model)` returns False (no
  surviving agents), so an extinct seed contributes
  `executed_ticks < n_ticks`. v0.21 had no extinct seeds (every arm
  recorded `in_influx = 1.0 × 200 × 8 = 1,600`); v0.22 is expected to
  match (8/8 survivors throughout v0.20/v0.21 transfer arms on
  food_ladder). If any v0.22 seed terminates early, the invariant uses
  the per-seed executed-tick sum, and the arm's row in the sweep
  report annotates seeds-with-early-termination separately. Direct
  invariant on the deterministic per-tick credit; halt only if the
  invariant fails after accounting for early termination.
- **H2.** v0.20 H4 invariant holds at every v0.22 arm:
  `parent_energy_transferred_to_child + pool_out_child_startup ==
  total_births × offspring_start_energy`.
- **H3.** `reproduction_heat_loss == 0` at every v0.22 arm (transfer
  mode contract).
- **H4.** `births_blocked_by_parent_energy == 0` at every v0.22 arm
  (defensive parent-energy gate; v0.20/v0.21 verified empirical
  irrelevance under cost=15, threshold=50 across all transfer-mode
  sweeps to date).
- **H5.** `pool_in_death_residual` is **low at arm A (hazard=0) and
  materially non-zero at arms B/C/D (hazard>0) when the recycling
  channel is active**. Strict monotonicity in hazard_damage is
  diagnostic but **not required**: higher damage can kill agents
  sooner, change population size during the run, alter the
  starvation:injury ratio, or shift hazard residency / avoidance
  behavior, any of which could produce a non-monotone but still
  causally-consistent residual flux. A useful non-monotone result
  (e.g. residual at hazard=12 below residual at hazard=8) is
  **not a hypothesis failure**; it is information about how
  damage-rate interacts with population dynamics. The hard pin is
  H7 (residual at A bounded above by ~5/seed avg).
- **H6.** `total_starvation_deaths` **non-increasing in hazard_damage
  across arms A → D**. As hazard_damage rises, agents are increasingly
  culled by INJURY before they can starve. **Cautious; ties expected
  in some seed-arm pairs.**
- **H7.** Arm A (hazard=0) has `pool_in_death_residual ≤ 5/seed
  averaged across the 8 seeds`. Hard threshold; STARVATION credits 0
  by definition, and only edge-case death paths produce non-zero
  residual at hazard=0. (Reserved as an absolute pin: if A's residual
  is more than ~5/seed, there is a death-mode we haven't catalogued.)

### Cautious form (the causal-mechanism question)

- **H8.** Arm A's `births_after_tick_50` falls in **band 1 (≤ 83)**:
  recycling/injury dynamics are load-bearing under this layout.
  **Cautious — this is the v0.22 substantive headline; predicting band 1
  is the recycling-as-effective-influx hypothesis from v0.21's H8 +
  the over-prediction analysis.**
- **H9.** Arm A's `births_after_tick_50` falls in **band 3 (91–94)**:
  geometry/capacity is sufficient; the v0.21 chamber asymmetry is not
  load-bearing on the recycling channel under this influx. **Cautious;
  the alternative reading.**
- **H10.** Arm A's `births_after_tick_50` falls in **band 4 (≥ 95)**:
  injury deaths were a net cull above geometric capacity; removing the
  cull lifts productivity. **Cautious; the inverse-recycling reading.**
  H8/H9/H10 are mutually exclusive; exactly one fires unless arm A
  lands in the ambiguous band.
- **H11.** Productivity at arms B/C/D is **non-decreasing in
  hazard_damage** if recycling is a fuel (H8-favored) — i.e., b>50
  rises 0 → 4 → 8 → 12. **Falsified if** arm D shows lower b>50 than
  arm C (would suggest the cull-vs-fuel balance flips at high hazard).
- **H12.** **Total pool blocks (b_blk + r_blk) at arm A vs arm C**.
  If recycling is load-bearing (H8), arm A should show b_blk + r_blk
  rising substantially (the substrate falls back into the pool-bound
  regime that influx=0.5 sat in: ~105 total blocks per v0.21 sweep).
  If geometry is sufficient (H9), arm A's blocks stay near zero
  (per-arm blocks at hazard=8 were r_blk=3, b_blk=0). **Cautious in
  magnitude.**

### Determinism

- **H13.** Arm C (hazard=8) reproduces v0.21 transfer-1500-influx-1.0
  food_ladder **byte-identically**: aggregate metrics
  `(total_births, births_after_tick_50, seeds_with_survivors,
  total_food_events, total_food_respawn_events,
  total_pool_respawn_denied, total_pool_birth_denied,
  pool_out_respawn, pool_out_child_startup, pool_in_death_residual,
  pool_min, pool_end, parent_energy_transferred_to_child,
  reproduction_heat_loss)` match v0.21 exactly AND the full event
  stream (`AgentBorn`, `AgentDied`, `AteFood`, `FoodRespawned`,
  `HazardEntered`, `HazardDamageApplied`) matches order- and
  content-identically. `hazard_damage=8.0` is the
  `build_chamber_layout` default that v0.21 inherited; the v0.22 seam
  threading the same value is a deductive identity. Failure of H13 is
  a halt condition — wiring leak introduced by the v0.22 seam.
- **H14.** `V0_19_ARMS`, `V0_20_ARMS`, and `V0_21_ARMS` continue to
  produce identical sweep outputs after v0.22 changes (no v0.19/v0.20/v0.21
  surface modified; new `Arm.hazard_damage` field defaults to `None`).
  Verified by re-running existing test suites; halt condition.

## Decision rules

- **Arm A b>50 in band 1 (≤ 83) AND H5 holds AND H12 fires (blocks
  rise back toward i\*=0.5 levels).** Recycling/injury dynamics
  load-bearing under this layout. **Headline finding: the v0.21
  food_ladder productivity plateau under transfer + influx=1.0 is
  fueled by hazard-injury death recycling; without it, the substrate
  falls back into pool-bound binding.** v0.23 candidate becomes
  hazard-density sweep (number of hazard *tiles*) to characterise
  the recycling-vs-tile-count dose-response, or reproduction-efficiency
  parameterisation if the recycling story is settled.

- **Arm A b>50 in band 3 (91–94) AND arm A's blocks near zero.**
  Geometry/capacity is sufficient. **Headline: chamber geometry, not
  recycling, accounts for the v0.21 food_ladder productivity
  plateau under transfer + influx=1.0.** v0.23 candidate becomes
  reproduction-efficiency parameterisation; the chamber-asymmetry
  question moves to "what aspect of food_ladder geometry is
  load-bearing" via narrow geometric variation.

- **Arm A b>50 in band 4 (≥ 95) AND H11 inverts (D < A).** Injury
  deaths were a net cull above the geometric capacity ceiling.
  **Headline: hazard tiles function as population control on
  food_ladder under productive influx; removing them lifts
  productivity above the recycling-supplemented v0.21 anchor.**
  Surprising; v0.23 designs would test the cull dose-response and
  whether the same finding holds at influx<1.0 (where recycling
  presumably contributed more).

- **Arm A b>50 in band 2 (84–90).** Ambiguous; the secondary telemetry
  (residual flux distribution per arm, death-cause split, hazard
  entries, block redistribution) determines the read. The pre-reg
  commits to publishing the band-2 interpretation case-by-case from
  the secondary metrics; if a clean read can't be made, v0.22 lands
  as "recycling channel was active mechanically (H5 holds) but its
  contribution to productivity is bounded by ~5–10 b>50 — not
  load-bearing in either direction." In that case, v0.23 sweeps
  hazard at a different influx (e.g. 0.5/tick, where recycling
  should matter more) to see whether the channel becomes load-bearing
  under more pool pressure.

- **H1/H2 invariant fails.** Influx accounting bug or transfer-mode
  ledger bug. Halt; v0.22 results uninterpretable.

- **H7 fails (arm A pool_in_death_residual > 5/seed avg).** Unknown
  death path produces non-zero residual at hazard=0. Halt and audit.

- **H13 fails.** Wiring defect introduced by the `Arm.hazard_damage`
  seam. Halt; v0.22 results uninterpretable.

- **H14 fails.** v0.19/v0.20/v0.21 contracts broken. Halt.

## Out of scope (v0.22)

- **Hazard-density sweep** (number of hazard tiles). v0.23+ candidate.
- **Other geometric variations** (chamber width, food band, capacity).
  v0.23+ candidate, conditional on the v0.22 result.
- **Reproduction efficiency < 1.0.** v0.23+ candidate.
- **POOL_FULL at varied hazard_damage.** Out of scope; the
  recycling-vs-geometry question is mode-orthogonal but the v0.21
  asymmetry was characterised under TRANSFER and that's the
  controlled regime.
- **Other influx rates.** Held at 1.0/tick; v0.23+ may revisit.
- **Other pool sizes.** Held at 1500; v0.23+ may revisit.
- **tight_gradient at varied hazard_damage.** Near-null channel; not
  informative.
- **Long-window (n_ticks > 200) observations.** v0.23+ if half-life
  dynamics become central.
- **HedonismPolicy comparisons.** Quarantined per v0.2 spec.

## Implementation notes

### File-level changes

- **Modify:** [[src/hedonism_harness/experiments/comparison_grid.py]] —
  add `Arm.hazard_damage: float | None = None` field. Thread to
  `run_chamber` in `_run_one_arm_seed`: pass
  `hazard_damage=arm.hazard_damage`. Add
  `ArmCellAggregate.total_injury_deaths: int = 0` (default 0 preserves
  bit-identity for prior aggregates) and sum
  `injury_deaths` from `results` in `_aggregate`. Add `V0_22_ARMS`
  tuple of four `Arm` instances per the table above. ~35 LOC.
- **Modify:** [[src/hedonism_harness/experiments/fear_hunger_chamber.py]] —
  `run_chamber` accepts `hazard_damage: float | None = None` kwarg.
  When non-None, replace the `build_chamber_layout(layout)` call with
  `build_chamber_layout(layout, hazard_damage=hazard_damage)`. The
  existing `build_chamber_layout` already accepts the kwarg (default
  8.0) and threads it into `WorldConfig.hazard_damage_default`. ~5
  LOC.
- **No changes** to `core/`, `model.py`, `events.py`,
  `experiments/layouts.py`, the energy pool, or the reproduction
  path. The mechanism is unchanged; only configuration varies.
- **New:** [[scripts/v0.22_sweep.py]] — sweep driver mirroring
  `scripts/v0.21_sweep.py`; food_ladder only (no tight_gradient call).
  Prints per-arm headline tables including the decisive death-mode
  and residual-flux columns. ~70 LOC.
- **New:** `tests/test_comparison_grid_v0_22.py` —
  - `V0_22_ARMS` shape: exactly 4 arms.
  - `hazard_damage` values are `{0.0, 4.0, 8.0, 12.0}`.
  - `Arm.hazard_damage=None` (default) preserves v0.21 bit-identity
    (existing arm shapes unchanged).
  - `Arm.hazard_damage=8.0` smoke-runs without raising and produces
    a `ChamberRunResult` whose `WorldConfig.hazard_damage_default ==
    8.0` (threading verified).
  - One end-to-end smoke test: arm A (hazard=0) runs to completion
    and produces `total_starvation_deaths > 0` as the only death
    cause emitted.
  ~120 LOC.
- **Documented:** this file (`docs/experiments/fear_hunger_v0.22.md`);
  results appended after the sweep.

### Determinism contract

- `V0_19_ARMS`, `V0_20_ARMS`, and `V0_21_ARMS` continue to produce
  identical sweep outputs after v0.22 changes (H14).
- Arm C (hazard=8) reproduces v0.21 transfer-1500-influx-1.0
  food_ladder byte-identically (H13).
- The v0.20 H4 invariant continues to hold per arm (H2).
- The new `Arm.hazard_damage` field defaults to `None`. With the
  default, `_run_one_arm_seed` calls `run_chamber` without the
  `hazard_damage` kwarg, which keeps the call shape exactly matching
  v0.21. The new field threads through `run_chamber → build_chamber_layout`
  only when explicitly set.

### LOC estimate

- `experiments/comparison_grid.py`: +35 LOC (Arm field, V0_22_ARMS,
  threading in `_run_one_arm_seed`, `total_injury_deaths` on
  ArmCellAggregate).
- `experiments/fear_hunger_chamber.py`: +5 LOC (kwarg + threading).
- `scripts/v0.22_sweep.py`: ~70 LOC (sweep driver, food_ladder only).
- New tests: ~120 LOC.
- This doc: ~500 LOC.

Total v0.22 implementation: ~725 LOC. Comparable to v0.21 (~690).
v0.22 introduces no new mechanism — it is a focused single-variable
test of one mechanism on one chamber.

## References

- [[docs/experiments/fear_hunger_v0.21.md]] — v0.21 results;
  the chamber-asymmetric frontier shape and the H8 chamber-asymmetry
  finding (1.0/tick gap consistent with recycling-as-effective-influx).
  Source of the v0.22 endpoint anchor (transfer-1500-influx-1.0
  food_ladder: 143 / 92).
- [[docs/experiments/fear_hunger_v0.20.md]] — v0.20 results;
  strict-transfer reproduction mechanism that v0.22 inherits.
  Source of the H4 conservation invariant carried forward to v0.22 H2.
- [[docs/experiments/fear_hunger_v0.19.md]] — v0.19 results; the
  death-residual recycling primitive that v0.22 sweeps the dose-response
  on.
- [[docs/specs/v0.2_reflex_cell_spec.md]] §"Comparison framework" —
  the substrate axis.

## Results (executed 2026-05-05)

Four arms × food_ladder × eight seeds (1..8) × 200 ticks × 5 founders.
**32 runs total**, 8.8 seconds end-to-end. Run artifacts persisted at
`runs/fear-hunger-v0.22-food_ladder/`.

### Headline finding — injury deaths were a net cull on a hazard-constrained productivity plateau; band 4 fires

**v0.22 falsifies the recycling-as-effective-influx reading of v0.21's
food_ladder productivity plateau.** At `hazard_damage=0` (zero injury
deaths, zero residual recycling), `births_after_tick_50 = 116` —
substantially **above** the v0.21 saturation plateau (b>50=92) at
hazard=8. Across the full hazard sweep, productivity is **strictly
decreasing** in hazard_damage:

| hazard | total_births | b>50 | starv | inj | residual |
|---:|---:|---:|---:|---:|---:|
| 0 | **249** | **116** | 206 | 0 | 0.0 |
| 4 | 152 | 96 | 90 | 14 | 505.8 |
| 8 | 143 | 92 | 77 | 16 | 624.8 |
| 12 | 112 | 65 | 67 | 18 | 579.7 |

Decision rule **band 4 (b>50 ≥ 95) AND H11 inverts (arm D b>50 < arm A
b>50)** fires unambiguously. **Hazard tiles function as population
control on food_ladder under productive influx; removing them lifts
productivity above the recycling-supplemented v0.21 anchor by 26%
(b>50) and 74% (total_births).** The recycling channel was active
mechanically (residual=505.8/624.8/579.7 at hazard=4/8/12) but its
contribution was net-negative for productivity: hazard culling
removed more reproductive capacity than the recycled energy bought.

The v0.21 finding that food_ladder "saturates at 143 / 92" was a
**hazard-constrained productivity plateau with recycling subsidy**,
not a pure geometric ceiling. The hazard cull was the binding force
holding population below the geometric+nutritional ceiling; the
recycling channel partially offset the energy cost of that cull,
but the cull itself dominated the productivity outcome. Removing
the cull lets the substrate press to a different binding regime:
pool-bound under starvation pressure (arm A: pool_min=0, r_blk=98,
starvation_deaths=206) rather than hazard-constrained productivity.
The geometric+nutritional
ceiling on this chamber under transfer + influx=1.0 is at least
b>50 ≈ 116, possibly higher under different pool/influx
configurations.

This refines but does not refute the v0.21 chamber-asymmetry framing:
food_ladder still has lower primary i\* than tight_gradient. v0.22
shows the *mechanism* of that asymmetry is **not** recycling-as-fuel;
the asymmetry is more likely chamber geometry interacting with
starvation/cull dynamics in a way that v0.22 has now opened up for
direct study.

### Determinism contracts — verified

H13 (arm C, hazard=8) reproduces v0.21 transfer-1500-influx-1.0
food_ladder **byte-identically** across all 9 anchor metrics:

| metric | v0.21 anchor | v0.22 hazard-8 |
|---|---:|---:|
| total_births | 143 | **143** |
| births_after_tick_50 | 92 | **92** |
| total_food_events | 674 | **674** |
| total_food_respawn_events | 501 | **501** |
| total_pool_respawn_denied | 3 | **3** |
| total_pool_birth_denied | 0 | **0** |
| pool_min_observed | 2 | **2.00** |
| mean_pool_end | 257 | **257.48** |
| parent_energy_transferred_to_child | 2,145 | **2,145** |

H14 verified by full pytest pass (652 tests, including all v0.19/v0.20/v0.21
suites unchanged).

### v0.22 sweep — food_ladder

| arm | hazard | births | b>50 | surv | food | respawn | fcpb | pool_min | pool_end | residual | starv | inj | haz_entries | r_blk | b_blk | xfer |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| hazard-0 | 0.0 | **249** | **116** | 8/8 | 670 | 478 | 53.82 | 0 | 38 | **0.0** | **206** | **0** | 200 | 98 | 12 | 3,735 |
| hazard-4 | 4.0 | 152 | 96 | 8/8 | 680 | 506 | 89.47 | 0 | 213 | 505.8 | 90 | 14 | 186 | 13 | 18 | 2,280 |
| hazard-8 | 8.0 | 143 | 92 | 8/8 | 674 | 501 | 94.27 | 2 | 257 | 624.8 | 77 | 16 | 120 | 3 | 0 | 2,145 |
| hazard-12 | 12.0 | 112 | 65 | 8/8 | 544 | 406 | 97.14 | 0 | 547 | 579.7 | 67 | 18 | 58 | 8 | 13 | 1,680 |

`pool_in_ambient_influx = 1,600` per arm (= 1.0 × 200 × 8) — H1
invariant exact at every arm. `reproduction_heat_loss = 0` per arm
— H3 exact (transfer mode contract). `births_blocked_by_parent_energy
= 0` per arm — H4 exact (defensive gate dormant, continuing v0.20/v0.21
prior). `parent_energy_transferred_to_child + pool_out_child_startup =
total_births × 30` exact at every arm — H2 (v0.20 H4 invariant) holds.

`seeds_with_survivors = 8/8` across every arm: extinction never fires
under any hazard level on this chamber + substrate. Population
collapse is not a v0.22 outcome.

### Hypotheses → outcomes

- **H1.** `pool_in_ambient_influx == 1.0 × executed_ticks × n_seeds`.
  **Confirmed exactly.** All seeds completed 200 ticks (8/8 surv);
  in_influx=1,600 per arm.
- **H2.** v0.20 H4 invariant. **Confirmed exactly** at every arm
  (xfer + pool_out_child_startup = births × 30).
- **H3.** `reproduction_heat_loss == 0`. **Confirmed exactly.**
- **H4.** `births_blocked_by_parent_energy == 0`. **Confirmed
  exactly.** The defensive parent-energy gate did not fire across any
  of the 32 runs (continuing the v0.20/v0.21 finding).
- **H5.** Residual low at hazard=0, materially non-zero at
  hazard>0. **Confirmed.** hazard=0 → 0.0 (exact); hazard=4/8/12 →
  505.8 / 624.8 / 579.7 (all materially non-zero). Strict monotonicity
  is **mildly falsified** at the 8 → 12 step (residual drops
  624.8 → 579.7) — exactly the soft-monotone case the pre-reg
  anticipated: at hazard=12 agents avoid hazards more aggressively
  (haz_entries drops 120 → 58), reducing total injury exposure even
  though per-injury residual deposits are larger. The mechanism
  reading is informative, not a hypothesis failure.
- **H6.** `total_starvation_deaths` non-increasing in hazard_damage.
  **Confirmed.** 206 → 90 → 77 → 67 (strictly monotone non-increasing).
- **H7.** Arm A `pool_in_death_residual ≤ 5/seed averaged across 8
  seeds`. **Confirmed exactly.** Arm A residual = 0.0 (= 0.0/seed).
  STARVATION-only deaths credit zero residual by construction.
- **H8.** Arm A b>50 in band 1 (≤ 83) — recycling load-bearing.
  **Falsified strongly.** Arm A b>50 = 116 (band 4).
- **H9.** Arm A b>50 in band 3 (91–94) — geometry sufficient.
  **Falsified strongly.** Arm A b>50 = 116, well above band 3.
- **H10.** Arm A b>50 in band 4 (≥ 95) — injury-deaths-as-cull.
  **Confirmed strongly.** Arm A b>50 = 116; total_births = 249
  (74% above the recycling-supplemented anchor).
- **H11.** Productivity non-decreasing in hazard_damage if recycling
  is a fuel. **Inverted.** b>50 strictly *decreases* with
  hazard_damage: 116 → 96 → 92 → 65. total_births: 249 → 152 → 143
  → 112. The inversion is the load-bearing falsification of the
  recycling-as-fuel reading.
- **H12.** Arm A blocks rise vs arm C if recycling is load-bearing
  (arm A should fall back into pool-bound binding like influx=0.5).
  **Partially confirmed but for a different reason than predicted.**
  Arm A: r_blk=98, b_blk=12 (total=110). Arm C: r_blk=3, b_blk=0
  (total=3). Arm A blocks DO rise dramatically — but not because
  recycling was the fuel that prevented blocks at C. Arm A is
  pool-bound because population pressure is much higher (249 births
  vs 143 at C → 50% more pool draws), not because recycling is
  missing. The directional prediction holds; the causal mechanism
  is different (population pressure vs missing recycling).
- **H13.** Arm C reproduces v0.21 transfer-1500-influx-1.0
  food_ladder byte-identically. **Confirmed exactly** — see the
  Determinism contracts table above.
- **H14.** v0.19/v0.20/v0.21 contracts unchanged. **Confirmed**
  by full pytest pass (652 tests).

### Decision rule fired (per pre-reg)

> **Arm A b>50 in band 4 (≥ 95) AND H11 inverts (D < A).** Injury
> deaths were a net cull above the geometric capacity ceiling.
> Headline: hazard tiles function as population control on
> food_ladder under productive influx; removing them lifts
> productivity above the recycling-supplemented v0.21 anchor.

Both conditions fire. The v0.21 i\* anchor (b>50=85 at influx=0.5)
is *not* what arm A returns to — arm A presses to b>50=116, far
above the v0.21 saturation plateau at influx≥1.0 (b>50=92). The
v0.21 plateau was not a hard chamber-capacity ceiling; it was a
hazard-constrained productivity plateau with recycling subsidy,
where the hazard cull was the binding force and the recycling
channel partially offset its energy cost.

### Three findings worth flagging for v0.23

1. **The chamber-asymmetry mechanism is now an open question, not a
   recycling story.** v0.21 reported a 1.0/tick chamber asymmetry
   (food_ladder primary i\*=0.5/tick vs tight=1.5/tick) with the
   working hypothesis that hazard-residual recycling supplied
   ~1.0/tick effective extra energy on food_ladder. v0.22 falsifies
   that mechanism: at hazard=0 on food_ladder under influx=1.0,
   productivity *exceeds* the v0.21 saturation plateau by 26%. The
   chamber asymmetry is real; its mechanism is **not** recycling.
   Likely candidates: (a) food_ladder's pre-food band lets agents
   refuel before hazard exposure where tight does not; (b) chamber
   width / agent-density / spatial distribution effects; (c) the
   gradient policy's hazard-avoidance behavior interacts with
   chamber geometry in ways tight_gradient cannot replicate. v0.23
   could test (a) directly by re-running the v0.21 influx frontier
   at hazard=0 on both chambers — the asymmetry magnitude under no
   recycling is the cleanest read.

2. **The hazard=0 substrate is in a new binding regime — pool-bound
   under starvation pressure.** Arm A: 249 births, 206 starvations,
   r_blk=98, b_blk=12, pool_min=0, pool_end=38, fcpb=53.82 (well
   below the v0.18 self-sustaining floor of 45 because births are
   cheap under transfer mode + recycling-tax-lifted, but food
   throughput per birth is dropping toward unsustainable). The
   substrate is reproducing fast, the pool drains fast, and
   starvation is the dominant cull. **This is a regime v0.18..v0.21
   never observed.** v0.23 candidates: sweep pool_initial at
   hazard=0, influx=1.0 to characterise the new cliff; sweep
   ambient_influx_rate at hazard=0 to find the new productivity
   transition (likely lower than v0.21's 0.5/tick because no
   recycling tax to overcome).

3. **Behavioral hazard-avoidance is a non-trivial confound in the
   recycling channel.** total_hazard_entries: 200 → 186 → 120 → 58
   across hazard {0, 4, 8, 12}. As damage rises, the gradient
   policy's avoidance gets more aggressive (the hazard-damage signal
   is what the policy senses). At hazard=12, agents enter hazards
   only 58 times across 32 runs — the channel is mechanically
   thin. The non-monotone residual at hazard=8→12 (624.8 → 579.7)
   is a direct consequence: fewer entries × deeper bodies = roughly
   constant total residual. **The recycling channel's effective
   energy supply saturates at ~600/seed in this layout regardless
   of damage rate above some threshold.** v0.23+ explorations of
   hazard parameterisation should track avoidance behavior
   alongside the channel observables.

### Data points worth flagging for v0.23

- **Reverse the v0.21 chamber-asymmetry hypothesis test under
  hazard=0.** A focused v0.23 sweep of `ambient_influx_rate ∈
  {0, 0.5, 1.0, 1.5, 2.0}` at hazard=0 on **both chambers** would
  isolate the geometry contribution to the asymmetry from the
  recycling-tax contribution. If food_ladder still has lower
  primary i\* than tight at hazard=0, geometry is load-bearing on
  the asymmetry. If the asymmetry collapses (both chambers
  similar), the v0.21 asymmetry was entirely a recycling-tax
  artifact.
- **The fcpb interpretation has a new floor under the recycling-tax-
  lifted regime.** Arm A fcpb=53.82 (vs 94.27 at hazard=8). Under
  transfer mode the system-energy per birth is 30 (gap-only); the
  fcpb floor that's biologically sustainable is roughly 30/0.5 = 60
  if half the food becomes children's body energy and the rest
  metabolises. Arm A's 53.82 is right at that boundary — population
  reproduces faster than food consumption can fund without
  recycling subsidy. **A long-window (n_ticks > 200) extension at
  hazard=0 would test whether arm A's substrate is genuinely
  productive long-run or only over the v0.22 200-tick window.**
- **Arm A starvation_deaths = 206 vs total_births=249.** ~83% of
  agents starve over the run; the substrate is cycling agents
  faster than v0.21 recorded under any condition. v0.23 lineage
  analysis (grandchildren count, post-birth lifespan) on arm A
  vs arm C runs would characterise whether the increased
  productivity is "deeper" (more compounding generations) or
  "wider" (more shallow first-generation births under hazard
  removal). Both readings are consistent with b>50 lift; the
  per-lineage telemetry separates them.
- **The 92 plateau is no longer a "chamber capacity" ceiling.**
  v0.21 framed it as such. v0.22 falsifies. v0.23+ should reframe
  the chamber-capacity question — what *is* the geometric
  ceiling on food_ladder under transfer mode? Likely much higher
  than 116 b>50 if the v0.22 substrate is also pool-bound. A
  pool_initial sweep at hazard=0, influx=1.0 would map the new
  geometric ceiling once pool is non-binding.
