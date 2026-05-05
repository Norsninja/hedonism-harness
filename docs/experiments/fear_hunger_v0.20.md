# v0.20 — parent-transfer + pool-gap reproduction (strict-transfer conservation)

**Status:** pre-registration; not yet executed.
**Date:** 2026-05-05
**Branch:** `claude/v0.20-parent-funds-child`
**Predecessors:** v0.14 (reflex cell, first compounding), v0.15 (chemotaxis-tier
scalar memory, no compounding lift), v0.16 (reproduction-economics: per-parent
lever, ceiling barely moves), v0.17 (offspring-energy: child energy is the
binding constraint, but under a free handout), v0.18 (food-respawn cooldown:
substrate compounds under non-saturating food, but respawn still creates energy
from nowhere on a delay), v0.19 (strict mass-energy conservation: substrate
compounds under finite/open energy accounting given sufficient initial budget
or steady-state influx; pool exhaustion is gradient not cliff;
`pool_out_child_startup` is 30–35% of total drain in the binding regime).
**Spec:** [[docs/specs/v0.2_reflex_cell_spec.md]] §"Comparison framework"
(substrate axis).

## Question

v0.19 proved the substrate compounds under explicit finite/open energy
accounting: when the initial pool budget exceeds the 200-tick demand
(closed-3000) or ambient influx matches the productive flux (open-equiv at
7/tick), v0.18 K-50 dynamics are reproduced byte-identically. Conservation
binds in proportion to the deficit, not all-or-nothing.

But v0.19 retained one biologically-suspect bookkeeping choice that the v0.19
pre-reg flagged for v0.20: **the parent's `energy_cost` was destroyed as heat
loss at every reproduction, while the child's startup energy was drawn entirely
from the global pool**. In real cells, the energy a parent spends on
reproduction is not destroyed — it is largely incorporated into the offspring.
v0.19's heat-loss-per-birth bookkeeping (15 energy / birth) is a substantive
biological deviation: every birth removed 15 energy from the closed system that
biology would have preserved as offspring mass.

v0.19's per-flow telemetry showed `pool_out_child_startup` was 30–35% of total
pool drain in the binding regime (closed-1500: 4,680 of 11,940 across 8 seeds).
The v0.19 pre-reg pre-committed (c) parent-funds-child as the next-slice
candidate specifically to test whether routing this energy biologically would
shift the conservation gradient.

v0.20 makes that routing strict. The parent's `reproduction_cost` (15) is
**transferred** into the child's body energy, not destroyed; the pool funds
only the remaining gap (`offspring_start_energy − reproduction_cost = 15`).
Reproduction stops being a heat sink and becomes an energy-routing event.

**v0.20 tests whether routing the parent's reproduction cost into offspring
startup energy, with the finite pool funding only the remaining gap, improves
lineage compounding relative to v0.19's pool-funded-child-startup +
reproduction-heat-loss — under regimes where v0.19's pool was the binding
constraint.**

## What this slice tests, and what it does NOT test

### Tests
- Whether **eliminating reproduction heat loss** (parent's 15 energy preserved
  as offspring mass) lifts compounding under partial-conservation arms where
  v0.19's pool was binding (closed-1500, open-low at 2/tick).
- Whether the lift, if any, scales with **pool-binding severity**: the deeper
  v0.19's deficit, the more the per-birth pool-draw reduction matters.
- The **negative-control contract**: when the pool is not binding (closed-3000),
  PARENT_TRANSFER_POOL_GAP must produce byte-identical compounding metrics to
  POOL_FULL — because per-agent dynamics are arithmetically identical in both
  modes when neither pool gate fires.

### Does NOT test
- **Reproduction efficiency below 1.0.** v0.20 sets transfer = `reproduction_cost`
  exactly, so the parent's contribution to the child is 100% of the
  reproduction cost (zero heat loss at reproduction). A future slice may
  introduce a heat-loss fraction (e.g. 80% of reproduction cost transfers,
  20% destroyed) to model the biological efficiency loss; that adds a free
  parameter without resolving the current conservation question and is
  deferred.
- **Variable per-birth pool draw under transfer mode.** The pool funds exactly
  `offspring_start_energy − reproduction_cost`; no fractional or
  population-conditional top-up. v0.21+ may explore.
- **Open-equiv (influx=7/tick) under transfer mode.** v0.19 already showed
  open-equiv reproduces v0.18 K-50 byte-identically — pool not binding,
  transfer mode would produce the same byte-identical output by construction.
  Including it in v0.20 would be testing a deductive identity, not an
  empirical question.

### Deferred (v0.21+ candidates)
- **Reproduction efficiency < 1.0** (heat-loss fraction on transfer). Parameterised
  partial-transfer mode to model real-cell biological inefficiency.
- **Inf-pool under transfer mode**. The current contract rejects this config
  (validator). A future slice may admit a degenerate "child gets only
  parent's contribution" semantics if biologically motivated.
- **Multi-cell tier directional EMA** still deferred until the substrate
  question is settled.
- **HedonismPolicy on conservation substrate** still quarantined per
  v0.2 spec.

## Conservation framing — strict-transfer bookkeeping

The v0.19 six-flow accounting is preserved with one critical change to the
"child startup" and "parent reproduction cost" rows under
PARENT_TRANSFER_POOL_GAP. The new flow is enumerated below; the v0.19 flow
table for reference is in [[docs/experiments/fear_hunger_v0.19.md]].

### Flow table — PARENT_TRANSFER_POOL_GAP mode (pre-registered)

| flow | direction | accounting |
|---|---|---|
| initial chamber paint (FOOD tiles at run start) | none | **NOT debited** from pool. Same as v0.19. |
| food respawn (cooldown refill at phase 0) | pool → tile (food_value) | **debits pool** by `food_value_default`. Fails-soft if pool < `food_value_default`. Same as v0.19. |
| eat (agent on FOOD tile) | tile → agent body | no pool change. Same as v0.19. |
| **child startup at birth (transfer portion)** | **parent body → child body** | **transfers** `reproduction_cost` from parent to child. **Not destroyed.** **Not credited to pool.** This is the v0.20 mechanism. |
| **child startup at birth (gap portion)** | **pool → child body** | **debits pool** by `offspring_start_energy − reproduction_cost`. Fails-atomically if pool can't fund the gap (birth denied; parent retains its energy; parent re-eligible next tick). |
| baseline + sensor metabolism per tick | agent body → destroyed | **heat loss** (not credited to pool). Same as v0.19. |
| death residual at AgentDied | agent body → pool | **credits pool** by `max(0.0, body.energy)`. Same as v0.19. |
| ambient influx (open-ecology arms only) | external → pool | **credits pool** by `ambient_influx_rate` per tick. Same as v0.19. |

### Per-birth conservation — v0.19 vs v0.20

Under v0.19's POOL_FULL mode (preserved as the v0.20 default):

```
Parent: -reproduction_cost   (15, destroyed as heat)
Pool:   -offspring_start_energy   (30, draws to fund child)
Child:  +offspring_start_energy   (30)
System energy delta per birth:    -reproduction_cost   (-15, heat loss)
```

Under v0.20's PARENT_TRANSFER_POOL_GAP mode:

```
Parent: -reproduction_cost   (15, transferred to child)
Pool:   -(offspring_start_energy - reproduction_cost)   (15, funds the gap)
Child:  +offspring_start_energy   (30, comprising 15 from parent + 15 from pool)
System energy delta per birth:    0   (no heat loss at reproduction)
```

The parent and child body trajectories are **identical between modes** — parent
loses 15, child gains 30, regardless of mode. The only difference is the pool
ledger: 30/birth (POOL_FULL) vs 15/birth (PARENT_TRANSFER_POOL_GAP). This is the
load-bearing observation: agent dynamics are mode-invariant; pool drains differ.

### Why strict-transfer is real (not bookkeeping)

The strict-transfer mechanism is implemented at the **system-ledger level**:
the existing parent debit and child startup body deltas are unchanged between
modes, while the pool debit is reduced to the remaining gap
(`offspring_start_energy − reproduction_cost = 15`). This makes the **total
parent + child + pool energy delta zero** under transfer mode (vs −15 under
POOL_FULL). The parent's 15 is not destroyed in the accounting; it is
represented as the difference between the child's 30-energy gain and the
pool's reduced 15-energy contribution. A future reviewer noting "you claimed
transfer but reproduction.py did not change" should be referred to this
section: the transfer is realised by the pool ledger, not by re-routing
operations on agent bodies.

### Why the negative-control arm matters

Because per-agent state is mode-invariant, in any regime where the pool gates
(respawn-deny, birth-deny) never fire, every per-tick agent observable —
births, food events, deaths, ages, lineages — must be byte-identical between
modes. closed-3000 in v0.19 had pool_end=795/8-seeds with zero blocks. Running
PARENT_TRANSFER_POOL_GAP at closed-3000 (arm F) is therefore a deductive
identity test against POOL_FULL at closed-3000 (arm E). If F ≠ E byte-for-byte
(modulo new v0.20-only telemetry events), there is a defect in the mechanism
and the pre-reg's substantive arms (B, D) cannot be interpreted.

### Why initial paint and metabolism stay as v0.19

Initial paint is fixed seed environment (not ongoing creation); metabolism is
biologically faithful as heat loss (cellular respiration is genuinely
exothermic). The v0.19 framing remains correct on both. v0.20 changes only the
reproduction step.

## Mechanism

### ChildFundingMode StrEnum

A new `ChildFundingMode` StrEnum on [[src/hedonism_harness/core/config.py]]
parameterizes the reproduction routing:

```python
class ChildFundingMode(StrEnum):
    POOL_FULL = "pool_full"                                # v0.19 default
    PARENT_TRANSFER_POOL_GAP = "parent_transfer_pool_gap"  # v0.20 mechanism
```

`ReproductionConfig` gains:

```python
child_funding_mode: ChildFundingMode = ChildFundingMode.POOL_FULL
```

`POOL_FULL` (the new default) preserves v0.19 byte-identity for every
existing arm by construction. `PARENT_TRANSFER_POOL_GAP` enables the
v0.20 mechanism.

### Cross-field validators

Two pydantic validators are added to `ReproductionConfig`:

1. `offspring_start_energy >= energy_cost` — required under
   `PARENT_TRANSFER_POOL_GAP` so the pool gap is non-negative. The check
   fires only under transfer mode: under POOL_FULL the parent's
   `energy_cost` is heat loss independent of `offspring_start_energy`,
   and the v0.7..v0.19 bare-default `ReproductionConfig()` (cost=35,
   offspring=30) remains legal — preserving bit-identity for every
   pre-v0.20 test and sweep that relies on those defaults.
2. (At `WorldConfig`+`ReproductionConfig` join — applied at chamber-driver
   construction time, not on `ReproductionConfig` alone) — when
   `child_funding_mode == PARENT_TRANSFER_POOL_GAP`,
   `WorldConfig.energy_pool_initial is not None` is required. Inf-pool under
   transfer mode is a degenerate config (no pool to top up the gap); we reject
   it explicitly rather than silently degrading to a fallback. The check fires
   in `run_chamber` after both configs are resolved.

### Tick-loop integration

The v0.19 phase-0a/0b influx/respawn pipeline is unchanged. The change is
localized to phase 7 (`_process_birth_queue`):

Under `child_funding_mode == POOL_FULL` (v0.19 path, preserved):

1. Pre-check `find_adjacent_empty_cell` (existing).
2. `try_debit_child_startup(offspring_start_energy)` (existing).
3. On success, call `process_reproduction` (debits parent's `energy_cost` as
   heat; constructs child with `offspring_start_energy`).

Under `child_funding_mode == PARENT_TRANSFER_POOL_GAP` (v0.20 path):

1. Pre-check `find_adjacent_empty_cell`.
2. Pre-check `parent.body.energy >= reproduction_cost` (new — defensive against
   the rare case where the parent's energy dropped between queueing and birth
   processing). On fail: emit `BirthDeniedParentEnergy(parent_id, x, y, tick)`,
   parent stays alive and re-eligible, no debit fires.
3. `try_debit_child_startup(offspring_start_energy − reproduction_cost)` —
   the pool funds only the gap. On fail: emit `PoolBirthDenied` (existing
   v0.19 event), parent stays alive and re-eligible.
4. On both successes, call `process_reproduction` with the transfer mode
   threaded through. `process_reproduction` debits parent's `reproduction_cost`
   as before, but routes that 15 energy into the child's body energy
   (rather than destroying it). The child body is constructed with
   `offspring_start_energy` — comprising the parent's 15 + the pool's 15.

### Atomic-deny semantics

All three pre-checks (placement, parent energy, pool gap) fire **before** any
mutation. On any failure, no state changes: parent retains its full
`energy_cost`, pool is untouched, no child is created, no partial birth, no
parent penalty. The parent re-enters the eligibility pool next tick (mirrors
v0.19's birth-denied contract).

This pre-check ordering is deterministic and pre-committed:
1. placement (cheapest, most likely to fail in dense populations)
2. parent energy (rare; defensive)
3. pool gap (rare unless pool is binding)

The order matters only for which counter fires first; the atomic-deny
guarantee is mode-invariant.

### Telemetry layering

The `EnergyPool` primitive remains **mode-agnostic**:
- `pool.out_child_startup` continues to mean "pool's contribution to child
  startup energy." Under POOL_FULL it accumulates `offspring_start_energy`
  per birth (= 30); under PARENT_TRANSFER_POOL_GAP it accumulates the gap
  (= 15). The semantic meaning shifts with mode; the field is unchanged.
- `pool.blocked_count_child_startup` continues to mean "pool insufficient to
  fund child startup," with the threshold being mode-dependent
  (`offspring_start_energy` vs `gap`). Same field.
- `pool.in_death_residual`, `pool.in_ambient_influx`, `pool.out_respawn`,
  `pool.blocked_count_respawn` are unchanged from v0.19.

Mode-specific accumulators live on `HHModel`:
- `model.parent_energy_transferred_to_child: float` — total energy routed
  from parent → child via the transfer mechanism. Always 0 under POOL_FULL;
  equals `reproduction_cost × successful_births` under PARENT_TRANSFER_POOL_GAP.
- `model.reproduction_heat_loss: float` — total energy destroyed at the
  parent reproduction step. Equals `reproduction_cost × successful_births`
  under POOL_FULL; always 0 under PARENT_TRANSFER_POOL_GAP.
- `model.births_blocked_by_parent_energy: int` — count of births denied
  because parent's energy was below `reproduction_cost` at process time.
  Always 0 under POOL_FULL (we do not add the gate to the v0.19 path; doing
  so would change v0.19's bit-identity contract — see "Bit-identity"
  below). Active under PARENT_TRANSFER_POOL_GAP only.

### Pre-registered invariant (verifiable at run end)

```
parent_energy_transferred_to_child + pool_out_child_startup == total_births × offspring_start_energy
```

— under PARENT_TRANSFER_POOL_GAP (with `pool_out_child_startup` being the gap
contribution, i.e. `(offspring_start_energy − reproduction_cost) ×
successful_births`).

Under POOL_FULL the simpler v0.19 invariant holds:

```
pool_out_child_startup == total_births × offspring_start_energy
parent_energy_transferred_to_child == 0
```

Both invariants are encoded as integration tests
([[tests/test_v0_20_transfer_mode.py]]) and re-verified per-arm in the sweep
analysis.

### Determinism

All transfer-mode transitions are deterministic — no new RNG draws.
`child_funding_mode == POOL_FULL` (the new default) preserves v0.7..v0.19
bit-identity by construction: the new branch in `_process_birth_queue` is
guarded behind the mode flag, the new accumulators stay at their initial
values, and the new event type is never emitted.

The new gate `parent.body.energy >= reproduction_cost` fires **only under
PARENT_TRANSFER_POOL_GAP**. Under POOL_FULL the gate is bypassed entirely —
this preserves v0.19's exact semantics (parent goes negative and dies if
energy < cost; rare edge case). Adding the gate to POOL_FULL would change
v0.19 dynamics on the rare edge case and break bit-identity. Deferred as a
v0.21+ hygiene clean-up under POOL_FULL if and only if it can be shown
empirically irrelevant on every existing v0.19 sweep.

### Configuration

`ReproductionConfig` gains `child_funding_mode` (default `POOL_FULL`).
`Arm` gains an optional `child_funding_mode: ChildFundingMode | None = None`;
`None` preserves bit-identity against `V0_14..V0_19_ARMS` by leaving the
ReproductionConfig default.

`run_chamber` accepts a `child_funding_mode` kwarg and threads it into the
resolved `ReproductionConfig` via `model_copy(update=...)` (mirrors the v0.18
`food_respawn_cooldown` and v0.19 `energy_pool_initial` patterns).

## Arms

Six arms × two chambers × eight seeds = **96 runs** (vs 112 for v0.19). The
arm count is reduced because we drop conservation-neutral arms (open-equiv,
closed-1500-K100) that v0.19 settled, and add only one orthogonal pairing
(POOL_FULL × PARENT_TRANSFER_POOL_GAP) at three regime points.

| arm | tier | mode | K | pool_initial | influx | label |
|---|---|---|---:|---:|---:|---|
| A | binding-ref | POOL_FULL | 50 | 1,500 | 0 | pool-full-1500 (v0.19 closed-1500 reference) |
| B | binding-test | PARENT_TRANSFER_POOL_GAP | 50 | 1,500 | 0 | **transfer-1500** (headline test) |
| C | rescue-ref | POOL_FULL | 50 | 1,500 | 2 | pool-full-open-low (v0.19 open-low reference) |
| D | rescue-test | PARENT_TRANSFER_POOL_GAP | 50 | 1,500 | 2 | **transfer-open-low** (does transfer push to productivity?) |
| E | null-ref | POOL_FULL | 50 | 3,000 | 0 | pool-full-3000 (v0.19 closed-3000 reference) |
| F | null-control | PARENT_TRANSFER_POOL_GAP | 50 | 3,000 | 0 | transfer-3000 (negative control — must equal E byte-identically) |

`offspring_start_energy=30`, `reproduction_cost=15`, `energy_threshold=50`,
`unbounded_mutation=True`, reflex-baseline policy, `n_ticks=200`,
`n_founders=5`, chamber layouts unchanged from v0.18/v0.19. K=50 throughout.

### Demand-math projection (anchored on v0.19 telemetry)

v0.19 closed-1500 tight_gradient telemetry per 8-seed aggregate:
`out_respawn=7,260, out_child_startup=4,680, total drain=11,940; pool_end=8;
188 r_blk + 126 b_blk; 156 births / 82 b>50`.

Under v0.20 PARENT_TRANSFER_POOL_GAP at closed-1500 tight, the per-birth pool
draw at the child-startup step halves (30 → 15 = the gap). If birth count
were unchanged, `out_child_startup` would drop from 4,680 → ~2,340. But pool
relief shifts more births past the deny gate, so total births rise toward
inf-pool's 204; respawn count rises proportionally; agents that would have
starved past tick 130 now reproduce later in the run.

Projected numbers (rough; the experiment will measure):
- births: 156 → ~190
- b>50 (tight): 82 → ~115 (lift toward but probably not reaching inf-pool's 130)
- r_blk: 188 → 100–140 (still pool-bound; lower flux through the respawn
  drain still leaves pool empty late in the run)
- b_blk: 126 → 30–60 (transfer mode halves the per-birth draw, so pool
  exhaustion blocks roughly half as many births, more if total drain falls)
- pool_out_child_startup (gap-only): ~2,850 (= 190 × 15)
- parent_energy_transferred_to_child: ~2,850 (= 190 × 15)
- reproduction_heat_loss: 0 (mechanism)

closed-1500 stays in the productive-binding regime — exactly where the
comparison is most informative.

For closed-3000 (arms E and F): v0.19 pool_end=795/8-seeds, zero blocks. Under
F, pool ends ~2× higher (pool drain halves on the child step from 6,120 →
3,060 across 8 seeds). Still zero blocks. **F's compounding metrics must
equal E's byte-for-byte.**

For open-low at influx=2/tick (arms C and D): v0.19 closed-1500 + open-low gave
175 births / 101 b>50 / 102 r_blk + 56 b_blk on tight. Transfer mode at
influx=2/tick should produce a stronger lift than transfer mode at closed-1500
because the influx supplements the pool — the gap-only draw may push the
system into a near-productive steady state on open-low where v0.19 needed
influx=7/tick.

### v0.20 first-sweep risk surface

If the projected numbers are off by an order of magnitude (e.g. transfer
mode under closed-1500 produces *fewer* births than POOL_FULL closed-1500),
the implementation has a defect — most likely the parent's energy debit
double-fired or the child's startup did not include the parent's transfer.
The integration test suite ([[tests/test_v0_20_transfer_mode.py]] §
"Per-birth invariant under transfer mode") guards against this directly.

## Pre-registered hypotheses

Two-tier structure consistent with v0.15 / v0.16 / v0.17 / v0.18 / v0.19:
**strong-form** for mechanism firing, **cautious-form** for substantive
ceiling lift, plus **determinism + invariant** for bit-identity and
conservation contracts.

### Strong form (the mechanism fires)

- **H1.** Under PARENT_TRANSFER_POOL_GAP arms (B, D, F), the new accumulator
  `model.parent_energy_transferred_to_child` is positive; under POOL_FULL
  arms (A, C, E) it is zero. Direct telemetry of the transfer mechanism
  firing.
- **H2.** Under PARENT_TRANSFER_POOL_GAP arms, `model.reproduction_heat_loss`
  is zero; under POOL_FULL arms it equals `reproduction_cost ×
  successful_births`. Direct telemetry of the heat-loss elimination.
- **H3.** Under PARENT_TRANSFER_POOL_GAP arms (B, D), `pool.out_child_startup`
  per birth equals `offspring_start_energy − reproduction_cost = 15`
  (within floating-point noise); under POOL_FULL arms it equals
  `offspring_start_energy = 30`. Direct telemetry of the gap-funding
  semantics.
- **H4.** The pre-registered invariant
  `parent_energy_transferred_to_child + pool_out_child_startup ==
  total_births × offspring_start_energy` holds exactly under
  PARENT_TRANSFER_POOL_GAP arms (B, D, F). The strict-conservation invariant.

### Cautious form (the ceiling lifts under transfer mode)

- **H5.** `births_after_tick_50` lifts at transfer-1500 (B) vs pool-full-1500
  (A) on at least one chamber. **Cautious in magnitude.** The substantive
  test of the v0.20 hypothesis: removing reproduction heat loss from a
  pool-binding regime relieves the binding constraint and lifts compounding.
- **H6.** `total_pool_birth_denied` falls at transfer-1500 (B) vs
  pool-full-1500 (A) on both chambers. **Expected in direction, but not
  guaranteed**: transfer mode halves per-birth pool demand, but the
  resulting reduction in pool blocks may produce more successful births
  → more food consumption → more respawn demand → more late-run pool
  pressure that partially offsets the smaller per-birth draw. Cautious
  in both direction and magnitude.
- **H7.** `births_after_tick_50` lifts at transfer-open-low (D) vs
  pool-full-open-low (C) on at least one chamber. The partial-rescue regime
  test. **Cautious.**
- **H8.** Transfer-mode arms (B, D, F) satisfy the mode-specific birth
  ledger: per successful birth,
  `pool_out_child_startup_per_birth = offspring_start_energy −
  reproduction_cost = 15`,
  `parent_energy_transferred_to_child_per_birth = reproduction_cost = 15`,
  `reproduction_heat_loss_per_birth = 0`, and the H4 invariant
  `parent_energy_transferred_to_child + pool_out_child_startup =
  total_births × offspring_start_energy` holds. POOL_FULL arms (A, C, E)
  satisfy the v0.19 ledger: `pool_out_child_startup_per_birth =
  offspring_start_energy = 30`,
  `reproduction_heat_loss_per_birth = reproduction_cost = 15`,
  total per-birth reproduction burden = 45.

  The v0.19 `food_consumed_per_birth >= 45` self-sustaining floor does
  **not** apply to transfer-mode arms. Under PARENT_TRANSFER_POOL_GAP, the
  per-birth reproduction burden at the system level is 30 (15 from parent
  body energy + 15 from pool gap), not 45 — the parent's 15 is recycled
  into offspring rather than destroyed as heat. A transfer-mode lineage
  can be perfectly conservative at fcpb < 45, because part of child
  startup is now recycled parent body energy. fcpb is reported as an
  observational ecological-throughput metric in v0.20, not as a hard
  self-sustaining floor under transfer mode. For POOL_FULL arms the v0.19
  floor still applies and is reported as before.
- **H9.** `seeds_with_survivors` is non-decreasing at transfer-1500 (B) vs
  pool-full-1500 (A). The transfer mechanism should not degrade survival.
  **Cautious in either direction.**

### Determinism + negative control

- **H10.** Arm A (pool-full-1500) reproduces v0.19 closed-1500 byte-identically
  on per-seed `(total_births, births_after_tick_50, seeds_with_survivors,
  total_food_events, total_food_respawn_events, total_grandchildren_count,
  pool_end, pool_min, pool_max, pool_out_respawn, pool_out_child_startup,
  pool_in_death_residual, pool_in_ambient_influx,
  total_pool_respawn_denied, total_pool_birth_denied)`. Filters: v0.20-only
  fields (`parent_energy_transferred_to_child`, `reproduction_heat_loss`,
  `births_blocked_by_parent_energy`, new event type
  `BirthDeniedParentEnergy`) excluded from comparison.
- **H11.** Arm C (pool-full-open-low) reproduces v0.19 open-low
  byte-identically (same metric set as H10).
- **H12.** Arm E (pool-full-3000) reproduces v0.19 closed-3000
  byte-identically (same metric set as H10).
- **H13.** Arm F (transfer-3000) reproduces arm E byte-identically on
  **per-agent observables only** — births, food events, deaths, ages,
  lineages, AgentBorn/AgentDied/AteFood/HazardEntered/HazardDamageApplied
  events, and the per-tile FoodRespawned event sequence. **Pool ledger
  fields legitimately differ between modes** (see "v0.20-only field
  expected non-equivalences" table below) and are excluded from the
  byte-identity comparison. The negative-control contract: per-agent
  state is mode-invariant when the pool is not binding; pool ledger is
  mode-defined by construction. If H13 fails on agent observables, the
  mechanism has an unintended leak into agent dynamics and the
  substantive arms (B, D) cannot be interpreted.

### v0.20-only field expected non-equivalences (H13)

Even when the pool is not binding, the following fields legitimately differ
between modes (and so are excluded from H13's byte-identity comparison):

| field | E (POOL_FULL closed-3000) | F (TRANSFER closed-3000) |
|---|---|---|
| `pool.out_child_startup` | 6,120 (= births × 30) | 3,060 (= births × 15) |
| `model.parent_energy_transferred_to_child` | 0 | 3,060 (= births × 15) |
| `model.reproduction_heat_loss` | 3,060 (= births × 15) | 0 |
| `pool.current` (and `pool_end`) | as v0.19 closed-3000 | strictly higher (extra 3,060 retained in pool) |
| `pool.min_observed` | as v0.19 closed-3000 | likely higher (less drain pressure) |

These differences are mode-defined; H13 compares everything else.

## Decision rules

- **B clears H5/H6 on both chambers AND D clears H7 on at least one chamber.**
  Routing reproduction cost into offspring measurably relieves the
  conservation deficit. **Headline finding: the substrate compounds more
  effectively under strict-transfer reproduction than under v0.19's
  pool-funded-with-heat-loss reproduction in the binding regime.** v0.21
  candidate becomes either reproduction-efficiency parameterisation
  (heat-loss fraction < 1) or multi-cell-tier directional EMA depending
  on the lift magnitude.

- **B clears H6 (pool-blocks fall) but not H5 (b>50 doesn't lift).** Pool
  relief is real but downstream constraints (parent post-birth viability,
  child survival, spatial access) bound compounding before the pool
  re-binds. v0.21 reframes around parent-state-after-birth telemetry.

- **B fails H6 (pool-blocks do not fall meaningfully under transfer).**
  Implementation defect or the gap-funding accounting is wrong. Halt and
  audit the per-birth invariant (H4); if H4 holds, the projection model
  was wrong (transfer mode produces enough additional respawn drain to
  exhaust the pool at a faster compensating rate, which would itself be
  a finding).

- **F ≠ E byte-identically (H13 fails).** Mechanism defect — per-agent
  state is unintentionally mode-dependent. Halt; v0.20 results are
  uninterpretable until the leak is closed.

- **A/C/E fail bit-identity against v0.19 (H10/H11/H12 fail).** Wiring
  defect in the mode-default path; the new field/branch leaked into the
  v0.19 path. Halt.

- **B and D both clear H5/H7 strongly.** Open ecology and finite ecology
  both benefit from transfer; v0.21 explores reproduction-efficiency
  parameterisation as the next conservation-axis question.

- **B clears H5 but D ~= C (open-low does not lift under transfer).**
  Influx-supplemented pools were already near-productive enough that
  transfer mode adds nothing; v0.19's open-low partial-rescue regime is
  pool-bound rather than reproduction-cost-bound. Useful refinement.

## Out of scope (v0.20)

- **Reproduction efficiency < 1.0** (heat-loss fraction). v0.21+
  candidate.
- **Inf-pool under transfer mode.** Validator-rejected per pre-reg.
- **closed-500 under transfer mode.** v0.19's cliff probe; under transfer
  mode the cliff likely shifts but characterising the new cliff is not
  the core hypothesis. v0.21 can sweep more pool sizes if interesting.
- **Voluntary-REPRODUCE policy under transfer mode.** Reflex-baseline
  only, per the v0.2 quarantine.
- **Variable food yield, density-dependent respawn, spatial pool fields.**
  v0.21+.
- **Long-window (n_ticks > 200) observations.** v0.20 follow-up if
  half-life dynamics become the central question.

## Implementation notes

### File-level changes

- **Modify:** [[src/hedonism_harness/core/config.py]] — add
  `ChildFundingMode` StrEnum (with `POOL_FULL` and `PARENT_TRANSFER_POOL_GAP`
  members); `ReproductionConfig.child_funding_mode: ChildFundingMode =
  ChildFundingMode.POOL_FULL`; cross-field validator
  `offspring_start_energy >= energy_cost` on `ReproductionConfig`.
  ~30 LOC.
- **Unchanged:** [[src/hedonism_harness/core/reproduction.py]]. The
  per-agent operations under both modes are identical: parent debits
  `reproduction_cost` from its body via `charge_parent`; child is
  constructed with `offspring_start_energy` via `make_child`. The
  *system-energy* difference between modes is realised entirely through
  the pool ledger (30 debited under POOL_FULL vs 15 debited under
  PARENT_TRANSFER_POOL_GAP) and the model-level conservation
  accumulators. Per the v0.20 conservation arithmetic above, parent and
  child body trajectories are mode-invariant; only pool levels and the
  semantic "where did the parent's 15 go" labels differ. Leaving
  `reproduction.py` untouched keeps the v0.19 contract bit-identical and
  isolates the mechanism to one branch in `model._process_birth_queue`.
- **Modify:** [[src/hedonism_harness/core/events.py]] — add
  `BirthDeniedParentEnergy(parent_id, x, y, tick)` event + signal
  registration. Listed in `AnyEvent` union. ~15 LOC.
- **Modify:** [[src/hedonism_harness/model.py]] —
  - in `_process_birth_queue`: branch on
    `reproduction_config.child_funding_mode`. Under POOL_FULL, preserve
    the v0.19 path exactly. Under PARENT_TRANSFER_POOL_GAP, add the
    parent-energy pre-check and the gap-only pool debit; emit
    `BirthDeniedParentEnergy` and `PoolBirthDenied` per the failure
    paths above.
  - add model-level accumulators
    `parent_energy_transferred_to_child: float = 0.0`,
    `reproduction_heat_loss: float = 0.0`,
    `births_blocked_by_parent_energy: int = 0`. Update at each successful
    birth (under the appropriate mode) and at each parent-energy denial.
  - add chamber-driver-time validator: when
    `reproduction_config.child_funding_mode ==
    PARENT_TRANSFER_POOL_GAP`, `world_config.energy_pool_initial is not
    None` is required. Implement in `run_chamber` or a small helper at
    `core/config.py`.
  ~60 LOC.
- **Modify:** [[src/hedonism_harness/experiments/comparison_grid.py]] —
  `Arm.child_funding_mode: ChildFundingMode | None = None`; thread to
  `ReproductionConfig` in `_run_one_arm_seed`. Add `V0_20_ARMS` tuple of
  six arms per the table above. `RunDiagnostics` gains
  `total_births_blocked_by_parent_energy`,
  `parent_energy_transferred_to_child`, `reproduction_heat_loss`.
  `ArmCellAggregate` gains the same fields summed across seeds.
  ~60 LOC.
- **Modify:** [[src/hedonism_harness/experiments/fear_hunger_chamber.py]]
  — `run_chamber` accepts `child_funding_mode` kwarg, threaded into the
  resolved `ReproductionConfig` via `model_copy(update=...)` (mirrors
  v0.19's `energy_pool_initial` pattern). `ChamberRunResult` gains
  `parent_energy_transferred_to_child`, `reproduction_heat_loss`,
  `births_blocked_by_parent_energy`. ~15 LOC.
- **New:** `tests/test_v0_20_transfer_mode.py` — POOL_FULL bit-identity
  contract (vs v0.19); PARENT_TRANSFER_POOL_GAP per-birth invariant
  (H4); BirthDeniedParentEnergy emission under contrived low-parent-energy
  scenario; validator rejects inf-pool under transfer; validator rejects
  `offspring_start_energy < energy_cost`; mode-agnostic pool primitive
  test (pool counters meaning depends only on what's debited, not on
  mode). ~250 LOC.
- **New:** `tests/test_comparison_grid_v0_20.py` — V0_20_ARMS shape,
  Arm.child_funding_mode threading, RunDiagnostics + ArmCellAggregate
  v0.20 fields. ~100 LOC.
- **New:** `scripts/v0.20_sweep.py` — sweep driver, prints per-arm
  headline tables. ~60 LOC. Mirrors `scripts/v0.19_sweep.py`.
- **Documented:** this file (`docs/experiments/fear_hunger_v0.20.md`);
  results appended after the sweep.

### Determinism contract

- Arm A (pool-full-1500) reproduces v0.19 closed-1500 byte-identically on
  per-seed and per-event metrics (H10).
- Arm C reproduces v0.19 open-low (H11).
- Arm E reproduces v0.19 closed-3000 (H12).
- Arm F reproduces arm E on per-agent observables (H13); v0.20-only fields
  legitimately differ.
- The default `ChildFundingMode.POOL_FULL` preserves bit-identity for every
  pre-v0.20 arm (V0_14..V0_19_ARMS) by construction. The new branch in
  `_process_birth_queue` is guarded behind the mode check.
- New event `BirthDeniedParentEnergy` is emitted only under
  PARENT_TRANSFER_POOL_GAP. Existing events (`AgentBorn`, `PoolBirthDenied`,
  `PoolRespawnDenied`, etc.) are unchanged in semantics and emission
  conditions.

### LOC estimate

- `core/config.py`: +30 LOC (StrEnum, field, validator).
- `core/reproduction.py`: +0 LOC (unchanged — see "Unchanged" note above).
- `core/events.py`: +15 LOC (new event + signal).
- `model.py`: +60 LOC (mode branch in birth queue, three new accumulators,
  cross-config validator hook).
- `experiments/comparison_grid.py`: +60 LOC (Arm field, V0_20_ARMS,
  RunDiagnostics + ArmCellAggregate fields).
- `experiments/fear_hunger_chamber.py`: +15 LOC (kwarg threaded, result
  fields).
- New tests: ~350 LOC across two files.
- `scripts/v0.20_sweep.py`: ~60 LOC.
- This doc: ~600 LOC.

Total v0.20 implementation: ~1,180 LOC. Slightly smaller than v0.19
(~1,250) because reproduction.py is unchanged and we reuse the v0.19
`EnergyPool` primitive without modification. The core/ changes remain
well-scoped — one new enum, one new field + validator, one new event,
one branch in `_process_birth_queue`.

## References

- [[docs/experiments/fear_hunger_v0.19.md]] — v0.19 results and the v0.20
  candidate (c) flag; per-flow telemetry that anchors the demand-math
  projection above.
- [[docs/experiments/fear_hunger_v0.18.md]] — v0.18 K-50 productive
  reference (transitively reproduced by v0.20 arm A through arm-E
  bit-identity chains).
- [[docs/specs/v0.2_reflex_cell_spec.md]] §"Comparison framework" —
  the substrate axis.
