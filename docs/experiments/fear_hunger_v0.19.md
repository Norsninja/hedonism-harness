# v0.19 — strict mass-energy conservation (closed pool + open ecology)

**Status:** pre-registration; not yet executed.
**Date:** 2026-05-05
**Branch:** `claude/v0.19-strict-conservation`
**Predecessors:** v0.14 (reflex cell, first compounding), v0.15 (chemotaxis-
tier scalar memory, no compounding lift), v0.16 (reproduction-economics:
per-parent lever, ceiling barely moves), v0.17 (offspring-energy: child
energy is the binding constraint, but under a free handout — largest single
intervention to date), v0.18 (food-respawn cooldown: substrate compounds
under non-saturating food without per-birth handout, but respawn still
creates energy from nowhere on a delay).
**Spec:** [[docs/specs/v0.2_reflex_cell_spec.md]] §"Comparison framework"
(substrate axis).

## Question

v0.18 proved the substrate compounds under non-saturating food at
`offspring_start_energy=30` (no per-birth handout). The lift was real
and clean: K-50 tight_gradient produces 130 `births_after_tick_50`,
exceeding v0.17 start-100's 72 by 80%, with `food_consumed_per_birth`
above the 45-energy self-sustaining floor in every productive arm. But
**food respawn still creates energy from nowhere on a delay** — when a
cell refills, the energy materialises from outside any energy budget.
The cooldown decoupled creation from a "tile yields, then is gone
forever" cap, but did not balance creation against consumption.

**v0.18 proves:** the substrate compounds under non-saturating food.

**v0.18 does NOT yet prove:** the substrate compounds under strict
mass-energy conservation.

That distinction is now the central project question. v0.19 closes it
by introducing a **finite ambient energy pool**: respawn debits the
pool, child startup debits the pool, agent metabolism and parent
reproduction cost are heat loss (destroyed), and agent-death residual
body energy returns to the pool. Two tiers test the question from both
sides: a **closed-pool** tier (no external influx — pool decays) and
an **open-ecology** tier (small ambient influx — pool may reach steady
state). Together they answer: does the substrate compound when energy
creation is tied to energy destruction, and how much external influx
is needed to balance the heat loss?

## What this slice tests, and what it does NOT test

### Tests
- Whether **strict mass-energy conservation** (every energy creation
  drawn from a finite pool, every energy loss tracked) supports
  lineage compounding at the v0.7..v0.18 baseline child energy of 30
  and v0.18-productive cooldown K=50.
- The **time profile of compounding under decay**: under a closed
  pool the substrate cannot sustain forever (heat loss is monotone);
  the question becomes "does compounding fire before pool exhaustion,
  and at what pool size?"
- Whether **ambient influx alone** (without a starting pool budget
  that would itself bias the experiment) can rescue a closed system
  and at what rate the influx-balanced regime resembles v0.18's free
  respawn.

### Does NOT test
- **Long-run steady state** beyond the 200-tick observation window.
  Closed-pool runs are inherently transient under heat-loss; "sustained
  through 200 ticks" is a categorical finding, not a measured half-life.
- **Parent-funds-child reproduction** (option c — parent transfers
  `energy_cost` directly to child instead of pool funding child
  startup). Biologically faithful but a different bookkeeping decision
  from heat-loss; deferred to v0.20 candidate. The v0.19 per-flow
  pool telemetry is instrumented to make that v0.20 design cheap.
- **Variable food yield, density-dependent respawn, or spatial
  pool-tile coupling.** v0.19 keeps the v0.18 cooldown mechanism and
  adds one global pool; spatial energy fields are deferred.

### Deferred (v0.20+ candidates)
- **v0.20 candidate (c):** parent-funds-child. Under (a/a) heat-loss
  v0.19, child startup is one of the largest pool drains
  (~6,120 energy under v0.18 K-50 tight). If v0.19 shows pool
  exhaustion is the binding constraint, (c) reduces per-birth pool
  draw from 30 → ~15 by routing the parent's existing cost directly
  into the child. The v0.19 per-flow telemetry tells us whether
  (c) is the right next slice or incremental.
- **Multi-cell tier directional EMA** still deferred until the
  substrate question is settled.
- **HedonismPolicy on conservation substrate** still quarantined per
  v0.2 spec.

## Conservation framing — pre-committed energy bookkeeping

The central design question for v0.19 is "where does each energy unit
come from and where does it go?" Six flows are pinned in advance so
the implementation cannot drift toward hidden injections.

### Flow table (pre-registered)

| flow | direction | accounting |
|---|---|---|
| initial chamber paint (FOOD tiles at run start) | none | **NOT debited** from pool. Initial paint is fixed seed environment, not ongoing creation. (See "Why initial paint is free" below.) |
| food respawn (cooldown refill at phase 0) | pool → tile (food_value) | **debits pool** by `food_value_default`. Fails-soft if pool < `food_value_default` (cell stays EMPTY). |
| eat (agent on FOOD tile) | tile (food_value) → agent body energy | no pool change (energy moves from tile reservoir to body). |
| child startup at birth | pool → child body energy | **debits pool** by `offspring_start_energy`. Fails-atomically if pool < `offspring_start_energy` (birth denied; parent's `energy_cost` not debited; parent re-eligible next tick). |
| parent reproduction cost | agent body → destroyed | **heat loss** (not credited to pool). |
| baseline + sensor metabolism per tick | agent body → destroyed | **heat loss** (not credited to pool). |
| death residual at AgentDied | agent body → pool | **credits pool** by `max(0.0, body.energy)`. Starvation deaths credit 0; hazard/injury deaths credit whatever was left. |
| ambient influx (open-ecology arms only) | external → pool | **credits pool** by `ambient_influx_rate` per tick at phase 0. Deterministic constant; no RNG. |

### Why initial paint is free

The chamber's initial FOOD tiles are part of the seed environment, not
ongoing creation. Debiting initial paint from pool would inflate every
pool size by `n_food_cells × food_value_default` (3,840 on
tight_gradient, 3,480 on food_ladder) without informing the
experiment, and would break the v0.19 ∞-pool bit-identity contract
against v0.18 K-50 (which never debited initial paint). The honest
accounting frame: the chamber is a **finite initial energy budget
(initial paint + initial pool) plus the configured influx rate**.
Once initial paint is consumed, only respawn (pool-funded) replaces it.

### Why parent reproduction cost and metabolism are heat loss

Second-law-faithful biology: every energy transfer in real cells loses
some fraction as heat. Crediting reproduction cost or metabolism back
to the pool would be biologically weird (heat doesn't reform into
food) and would make the closed-pool experiment a sanity check rather
than a substantive test. Under heat-loss the pool decays during
compounding; pool half-life becomes an experimental observable. The
open-ecology arms then carry the steady-state question.

### Why child startup debits pool (not parent body)

Routing child startup through the pool is the v0.17 critique honestly
applied. If child startup materialises at birth, v0.19 has just
relocated v0.17's handout from "free at birth" to "free at the pool
boundary" — same lie at a different layer. Pool-funded child startup
is what makes v0.19 strict-conservation. The alternative (parent
funds child via direct transfer) is option (c), deferred to v0.20.

### Why empty-pool denials are atomic

When pool < `offspring_start_energy`, three options exist: deny
(birth fails, parent retains `energy_cost`, re-eligible), partial-fund
(child starts with whatever pool has), or defer (queue birth for next
tick). Atomic denial is cleanest:

- matches the existing `hazard_threshold` rejection pattern (failed
  reproduction request preserves parent state);
- does not introduce a new agent-state regime (partial-fund children);
- avoids interaction with parent's `energy_cost` timing under defer.

The denial rate becomes a substrate finding: at what pool level does
the system stop reproducing? `births_blocked_by_empty_pool` telemetry
captures it directly.

## Mechanism

### Ambient energy pool

A new module [[src/hedonism_harness/core/energy_pool.py]] owns the
pool state. The pool is a single non-negative `float64` scalar held
on the `HHModel` as `self.energy_pool` (or wrapped in a small
`EnergyPool` dataclass for atomic-debit semantics — see
"Implementation notes"). Two configuration parameters control it:

- `WorldConfig.energy_pool_initial: float | None = None` — initial
  pool energy. `None` = unlimited (∞-pool reference arm; preserves
  v0.18 bit-identity by construction). Finite values enable the
  closed-pool / open-ecology mechanisms.
- `WorldConfig.ambient_influx_rate: float = 0.0` — energy credited
  to pool at phase 0 of each tick. Default 0 = closed pool.
  Deterministic; no RNG draws.

### Tick-loop integration

The pool integrates into the existing v0.18 tick loop with minimal
disturbance:

- **Phase 0 (before agent step):** apply ambient influx
  (`pool += ambient_influx_rate`); apply food respawn, but each
  refill now requires `pool >= food_value_default` to fire (else
  `pool_births_blocked` increments and the cell stays EMPTY with
  `respawn_at_tick` rescheduled or cleared per "Respawn failure
  semantics" below).
- **Phase 7 (process birth queue):** before queueing a birth,
  attempt atomic pool debit of `offspring_start_energy`. If pool
  is insufficient, the birth is denied (parent's `energy_cost`
  not debited; parent stays alive and re-eligible) and
  `births_blocked_by_empty_pool` increments.
- **Phase 6 (death sweep):** when an agent is marked dead, credit
  `max(0.0, body.energy)` to the pool synchronously in the death
  handler (sender-scoped subscription on `AgentDied`, parallel to
  the v0.18 `AteFood` handler pattern).

### Respawn failure semantics

When pool < `food_value_default` at phase-0 respawn time, the
cell that was scheduled to refill stays EMPTY. Two sub-options:

- **(i) clear the schedule** (`respawn_at_tick` → 0). The cell
  is permanently lost until eaten again. Simpler; matches "if
  the energy isn't there, the food doesn't come back." Pre-reg
  default.
- **(ii) keep the schedule** (`respawn_at_tick` unchanged). The
  cell waits for pool refill (under open-ecology arms). More
  forgiving but introduces "deferred refill" semantics not
  present in v0.18.

Pinning **(i)** for v0.19. Under closed pool the ecology is
intrinsically transient; preserving deferred schedules across a
draining pool would obscure the decay observable. Under open
ecology, fresh consumption schedules new refills, so the system
is self-healing on the relevant timescale without (ii).

### Determinism

All pool transitions are deterministic — no RNG draws.
`ambient_influx_rate` is a deterministic constant added at phase 0.
Death residual credit is synchronous in the existing death sweep.
Pool debit order under multi-event ticks (e.g. multiple cells refill
simultaneously) follows `np.argwhere` lexicographic order from
v0.18 — preserves cross-run determinism.

`energy_pool_initial=None` and `ambient_influx_rate=0.0` (the new
defaults) preserve v0.7..v0.18 bit-identity by construction: the
pool path is never touched, the death residual handler is not
registered, and the influx is zero.

### Configuration

`WorldConfig` gains:

```python
energy_pool_initial: float | None = Field(default=None, ge=0.0, ...)
ambient_influx_rate: float = Field(default=0.0, ge=0.0, ...)
```

`Arm` gains optional fields:

```python
energy_pool_initial: float | None = None
ambient_influx_rate: float | None = None
```

`None` on either preserves bit-identity against `V0_14_ARMS`,
`V0_15_ARMS`, `V0_16_ARMS`, `V0_17_ARMS`, and `V0_18_ARMS`.

## Arms

Seven arms × two chambers × eight seeds = **112 runs** (vs 64 for
v0.18). The extra arms cover closed-pool resolution (4 pool sizes
at K=50), one cooldown hedge (K=100 at the productive-guess pool
budget), and two open-ecology comparison arms.

| arm | tier | K | pool_initial | influx | label |
|---|---|---:|---:|---:|---|
| A | reference | 50 | ∞ (None) | 0 | inf-pool (v0.18 K-50 bit-identity) |
| B | closed | 50 | 5,000 | 0 | closed-5K (decay-fast probe) |
| C | closed | 50 | 15,000 | 0 | closed-15K (productive guess) |
| D | closed | 50 | 30,000 | 0 | closed-30K (comfortable margin) |
| E | closed | 100 | 15,000 | 0 | closed-15K-K100 (cooldown hedge) |
| F | open | 50 | 15,000 | 20 | open-low (low-influx rescue probe) |
| G | open | 50 | 15,000 | 60 | open-equiv (v0.18-equivalent flux) |

`offspring_start_energy=30`, `energy_cost=15`, `energy_threshold=50`,
`unbounded_mutation=True`, reflex-baseline policy, `n_ticks=200`,
`n_founders=5`, chamber layouts unchanged from v0.18.

### Demand math (sanity check on the pool brackets)

Under v0.18 K-50 tight_gradient (the productive arm v0.19 will most
directly translate), four flows determine pool demand over 200 ticks:

| flow | magnitude (tight K-50) |
|---:|---:|
| respawn out (576 events × 20) | 11,520 |
| child startup out (204 births × 30) | 6,120 |
| parent repro cost (heat loss; not pool draw) | 3,060 |
| metabolism (heat loss; not pool draw) | ~600 |
| death residual in (~50 non-starv × ~10) | ~−500 (credits in, reducing net demand) |
| **net pool demand** | **~17,140** |

5K starves quickly (decay-before-compounding probe). 15K is the
productive guess — slightly under 200-tick demand, expected to
sustain compounding through most of the run before pool exhaustion
forces stagnation. 30K provides comfortable margin and may sustain
through the full window (categorical finding). ∞ reproduces v0.18
K-50 exactly.

### Influx rate derivation (open arms)

v0.18 K-50 productive-arm respawn flux:

- tight_gradient: 576 events × 20 / 200 ticks = **57.6 energy/tick**
- food_ladder: 504 events × 20 / 200 ticks = **50.4 energy/tick**

Average ~54/tick across productive K-50 arms. Open-equiv arm uses
**60/tick** (rounded up; bracket the v0.18-productive flux from
above). Open-low uses **20/tick** (well below v0.18 productive
flux, tests whether *any* influx rescues a closed pool).

Both open arms share `pool_initial=15K` to isolate influx
contribution from initial budget — the comparison "C closed-15K vs
F open-low vs G open-equiv" cleanly separates the influx variable.

## Pre-registered hypotheses

Two-tier structure consistent with v0.15 / v0.16 / v0.17 / v0.18:
**strong-form** for the mechanical intervention firing,
**cautious-form** for the substantive ceiling lift, plus
**determinism** for bit-identity contracts.

### Strong form (the intervention fires)

- **H1.** `pool_end` decreases monotonically as `pool_initial`
  decreases under closed-pool arms (B, C, D, E). Under heat-loss the
  pool can only decrease (or stay flat under death residual ≥
  out-flow); smaller pools decay faster. If H1 fails the pool path is
  broken.
- **H2.** Open-ecology arms (F, G) show smaller `pool_initial −
  pool_end` than closed-pool arm C (same pool_initial=15K). Influx
  partially or fully balances heat loss.
- **H3.** `pool_births_blocked > 0` under at least the smallest
  closed-pool arm (B, closed-5K). Direct telemetry of pool
  exhaustion blocking respawns. **Cautious in absolute magnitude.**
- **H4.** `births_blocked_by_empty_pool > 0` under at least one
  closed-pool arm (B or C). Direct telemetry of pool exhaustion
  blocking births. **Cautious in absolute magnitude.**

### Cautious form (the ceiling lifts under conservation)

- **H5.** `births_after_tick_50` lifts at closed-30K (D) vs closed-5K
  (B) on at least one chamber. **Cautious.** The decay-fast 5K arm
  may produce nearly zero compounding; the 30K arm should clear v0.14-
  v0.16 baseline ceilings if the substrate compounds at all under
  conservation.
- **H6.** `food_consumed_per_birth` clears the 45-energy
  self-sustaining floor at closed-30K (D) on at least one chamber.
  **Cautious.** This is the strictest test of "the substrate is
  paying for births with food under conservation." If H6 fails the
  substrate is generating phantom births or pool exhaustion is
  artificially capping fcpb interpretation.
- **H7.** `mean_grandchildren_per_seed` rises at closed-30K (D) vs
  closed-5K (B) on both chambers. The direct compounding metric.
- **H8.** `seeds_with_survivors` rises at closed-30K (D) vs
  closed-5K (B) on at least one chamber.
- **H9.** Open-equiv (G, influx=60/tick) reaches v0.18 K-50
  `births_after_tick_50` levels (within ~25%). **Bridge hypothesis.**
  If G reproduces v0.18 K-50, the conservation framing has a
  steady-state regime that recovers the v0.18 finding.
- **H10.** Closed-pool arms exhibit a non-monotonic shape on the
  pool-size axis (B → C → D), or a productive sweet spot exists
  between the under- and over-pool extremes. **Pre-reg-cautious.**
  v0.18 K-20 over-saturation regression on tight_gradient is the
  precedent; v0.19 may surface a parallel non-monotonicity in pool
  size if pool exhaustion at small sizes and metabolic-overhead
  dominance at large sizes both cap compounding.

### Determinism

- **H11.** Arm A (∞-pool, K=50) reproduces v0.18 K-50
  bit-identically on per-seed `(total_births, births_after_tick_50,
  seeds_with_survivors, total_food_events, total_grandchildren_count,
  total_food_respawn_events)` AND emits identical `FoodRespawned`
  events (same ticks, same coordinates, same order). v0.19-only
  telemetry events (`PoolDebited`, `PoolCredited`, etc.) and fields
  are filtered before comparison.

## Conservation accounting metric (carried forward)

`food_consumed_per_birth` is unchanged: `(total_food_events ×
food_value_default) / total_births`. Floor still 45 (`energy_cost +
offspring_start_energy`). v0.19 interpretation:

- fcpb < 45 → not self-sustaining (substrate generating phantom
  births, or pool exhaustion has artificially capped the system).
- fcpb ≈ 45 → minimum self-sustaining; substrate paying for births
  with food at the floor.
- fcpb > 45 → productive with margin; substrate paying for births
  with food, surplus going to metabolism / pre-reproductive forage.

Under closed pool the fcpb interpretation needs care: pool
exhaustion late in the run depresses food respawn, which depresses
fcpb. **Plot fcpb against pool size across closed arms**; the
productive sweet spot should clear the floor while later (smaller-
pool) arms drop below it.

## Headline metrics

Carried forward from v0.18 unchanged:

- `total_births`, `seeds_with_any_births`,
  `births_after_tick_50`, `seeds_with_survivors` (run end),
  `still_tick_fraction`, `total_food_events`, `hazard_entries`,
  `starvation_deaths`, `reproduction_requests`.
- v0.16 per-parent: `mean_births_per_parent`,
  `mean_post_birth_lifespan_ticks`, `total_distinct_parents`,
  `total_post_birth_lifespan_ticks` (raw).
- v0.17: `total_grandchildren_count`,
  `mean_grandchildren_per_seed`.
- v0.18: `total_food_respawn_events`, `food_consumed_per_birth`.
- `max_population_end`, `total_starvation_deaths`,
  `total_reproduction_requests`.

New v0.19 telemetry:

- **`pool_min`, `pool_max`, `pool_end`** — pool trajectory snapshots
  (per `RunDiagnostics`). `pool_min` shows worst-case decay state;
  `pool_end` is the run-final pool. `pool_max` is informative for
  open-ecology arms that may climb toward steady state.
- **`pool_births_blocked`** — count of phase-0 respawn attempts
  that failed because pool < `food_value_default`. Always 0 under
  ∞-pool (A). Direct telemetry of pool exhaustion preventing
  respawn.
- **`births_blocked_by_empty_pool`** — count of birth attempts
  denied at phase 7 because pool < `offspring_start_energy`. Always
  0 under ∞-pool (A). Direct telemetry of pool exhaustion preventing
  reproduction.
- **Per-flow pool counters** (4 floats per run):
  - `pool_out_respawn` — total energy debited by successful respawns.
  - `pool_out_child_startup` — total energy debited by successful
    child startups.
  - `pool_in_death_residual` — total energy credited by AgentDied
    residuals.
  - `pool_in_ambient_influx` — total energy credited by ambient
    influx (always 0 under closed-pool arms).

The per-flow counters make the v0.20 (c) parent-funds-child design
decision cheap: if `pool_out_child_startup` is the dominant pool
drain under closed-pool arms with substantial blocking, (c) is
high-value as the next slice; if not, (c) is incremental.

## Decision rules

- **Closed-30K (D) clears H5/H6/H7 on both chambers AND open-equiv
  (G) reproduces v0.18 K-50 (H9).** The substrate compounds under
  conservation; the bridge to v0.18 holds. **Headline finding: the
  substrate compounds under strict mass-energy conservation given
  sufficient initial budget OR steady-state influx.** v0.20 candidate
  becomes (c) parent-funds-child if `pool_out_child_startup`
  dominates pool drain, otherwise multi-cell-tier directional EMA
  (the deferred substrate question from v0.13 onwards).

- **D clears H5/H6 but G fails to reproduce v0.18 (H9).** Initial
  pool budget supports compounding but the ambient-influx steady
  state does not. Possible mechanisms: 60/tick is below the actual
  required steady state; influx mechanism interacts badly with
  population dynamics. v0.20 sweeps influx rate densely.

- **D fails H5/H6 even with 30K initial budget.** The substrate
  does not compound under heat-loss conservation in the 200-tick
  window. Two sub-cases:
  - `pool_births_blocked` and `births_blocked_by_empty_pool` are
    high → pool exhaustion is binding; v0.20 (c) parent-funds-child
    is mandatory next slice.
  - blocking metrics are low → pool sustains but compounding still
    fails; the bug is elsewhere (metabolism, hazard interaction,
    population dynamics under decay). v0.20 reframes.

- **B (closed-5K) sustains compounding through the window with
  `pool_end > 0`.** The demand math is wrong — the substrate is
  cheaper than v0.18 K-50 implied. Worth investigating but not
  blocking; recompute demand from v0.19 actual flows.

- **D (closed-30K) shows lower compounding than C (closed-15K).**
  Non-monotonic shape on the pool-size axis (parallel to v0.18
  K-20 over-saturation). Interpretation: large pool floods refills,
  metabolic overhead dominates, late-run reproduction concentrates
  pre-tick-50 (same regression mechanism as v0.18 K-20 tight). H10
  confirmed; flag for v0.20 design.

## Out of scope (v0.19)

- **Parent-funds-child reproduction (option c).** v0.20 candidate;
  per-flow telemetry pre-registered to make that decision cheap.
- **Pool-tile coupling, spatial energy fields, density-dependent
  respawn.** v0.21+.
- **Variable food yield on respawn** (cell that respawns at lower
  yield depending on pool fullness). v0.21+.
- **Long-window observations (n_ticks > 200) for closed-pool arms.**
  v0.20 follow-up if pool half-life becomes the central question.
- **ScalarMemory under conservation.** The v0.15 chemotaxis cell
  stays inert in this slice.
- **HedonismPolicy comparisons** — quarantined per v0.2 spec.
- **Multi-cell-tier directional EMA** — deferred until the substrate
  question is settled (this slice is a candidate for "settling" it).

## Implementation notes

### File-level changes

- **New:** [[src/hedonism_harness/core/energy_pool.py]] — `EnergyPool`
  small dataclass-or-class with atomic-debit semantics:
  `try_debit(amount: float) -> bool` (returns True + decrements on
  success, False + leaves untouched on failure), `credit(amount:
  float) -> None`, plus `min_observed`, `max_observed`,
  `debited_total_*`, `credited_total_*` accumulators for
  per-flow telemetry. ~80 LOC.
- **Modify:** [[src/hedonism_harness/core/config.py]] —
  `WorldConfig.energy_pool_initial: float | None = None`,
  `WorldConfig.ambient_influx_rate: float = 0.0`. Pydantic bounds
  `ge=0.0` on both. Documentation block parallels the v0.18
  `food_respawn_cooldown` pattern.
- **Modify:** [[src/hedonism_harness/core/events.py]] —
  optional `PoolBirthDenied(parent_id, x, y, tick)` and
  `PoolRespawnDenied(x, y, tick)` events for v0.19-only telemetry.
  Listed in `AnyEvent` union; signal entries in `_SIGNAL_NAMES`.
  These are excluded from the bit-identity comparison filter.
- **Modify:** [[src/hedonism_harness/model.py]] —
  - construct `self.energy_pool` from
    `world_config.energy_pool_initial` (or pass-through unbounded
    sentinel under `None`);
  - phase-0 ambient influx (`self.energy_pool.credit(rate)` if
    finite pool and rate > 0);
  - gate `_apply_food_respawn` refills on `try_debit(food_value)`;
    on failure clear schedule + emit `PoolRespawnDenied` and
    increment `pool_births_blocked`;
  - in `_process_birth_queue`, attempt `try_debit(offspring_start_energy)`
    before queueing the child; on failure emit `PoolBirthDenied`
    and increment `births_blocked_by_empty_pool` (parent's
    `energy_cost` not debited; parent re-enters next tick's queue
    via existing eligibility);
  - subscribe `AgentDied` (sender-scoped, sender=self) when
    `energy_pool_initial is not None`; handler credits `max(0.0,
    body.energy)` to pool. Handler stored on instance to defeat
    blinker weak-references (same pattern as v0.18 `AteFood`).
- **Modify:** [[src/hedonism_harness/experiments/comparison_grid.py]] —
  `Arm.energy_pool_initial: float | None = None`,
  `Arm.ambient_influx_rate: float | None = None`; thread to
  `WorldConfig` in `_run_one_arm_seed`. Add `V0_19_ARMS` tuple of
  seven arms per the table above. `RunDiagnostics` gains
  `pool_min`, `pool_max`, `pool_end`, `pool_births_blocked`,
  `births_blocked_by_empty_pool`, `pool_out_respawn`,
  `pool_out_child_startup`, `pool_in_death_residual`,
  `pool_in_ambient_influx`. `ArmCellAggregate` gains the same
  fields (summed or averaged across seeds as appropriate).
- **Modify:** [[src/hedonism_harness/experiments/fear_hunger_chamber.py]]
  — `run_chamber` accepts `energy_pool_initial` and
  `ambient_influx_rate` kwargs, threaded into the frozen
  `WorldConfig` via `model_copy(update=...)` (mirrors the v0.18
  `food_respawn_cooldown` pattern).
- **Modify:** [[src/hedonism_harness/io/jsonl_writer.py]] — verify
  new event types serialize cleanly; likely zero-LOC change.
- **New:** `tests/test_energy_pool.py` — `EnergyPool` unit tests
  (atomic debit, credit, telemetry accumulators).
- **New:** `tests/test_v0_19_conservation.py` — pool integration
  tests: phase-0 influx, respawn debit (success + fail-soft), child
  startup debit (success + atomic deny), death residual credit,
  bit-identity ∞-pool vs v0.18 K-50 (events.jsonl filtered
  comparison).
- **New:** `tests/test_comparison_grid_energy_pool.py` — Arm field
  defaults, V0_19_ARMS shape, end-to-end run with override,
  V0_15..V0_18 arms unchanged.
- **Documented:** this file (`docs/experiments/fear_hunger_v0.19.md`);
  results appended after the sweep.

### Determinism contract

- Arm A (∞-pool, K=50) reproduces v0.18 K-50 bit-identically on
  per-seed `(total_births, births_after_tick_50,
  seeds_with_survivors, total_food_events,
  total_grandchildren_count, total_food_respawn_events)` AND emits
  identical `FoodRespawned` events. Filter v0.19-only events
  (`PoolBirthDenied`, `PoolRespawnDenied`) and v0.19-only fields
  (`pool_*`) before comparison; the remaining stream is
  byte-identical.
- v0.18 K-50 in turn reproduces v0.17 start-30 bit-identically (the
  v0.18 contract). Transitively, A reproduces v0.16 cost-15 numbers,
  anchoring back to v0.7-era determinism on shared seeds.
- Override defaults are `None` / `0.0`. Existing `V0_14_ARMS`,
  `V0_15_ARMS`, `V0_16_ARMS`, `V0_17_ARMS`, and `V0_18_ARMS`
  produce identical sweep outputs after the v0.19 changes.
- The `EnergyPool` is allocated regardless of config (storage
  hygiene); under `energy_pool_initial=None` it acts as an
  unbounded passthrough (every `try_debit` succeeds; every
  `credit` is a no-op accumulator update). The `AgentDied`
  subscription is conditional on `energy_pool_initial is not None`
  so the handler does not run in the bit-identity contract path.

### LOC estimate

- `core/energy_pool.py`: ~80 LOC (new module).
- `core/config.py`: +10 LOC (two new fields).
- `core/events.py`: +30 LOC (two events + signals).
- `model.py`: +120 LOC (pool wiring, phase-0 influx, gated
  respawn, atomic birth debit, death residual handler).
- `experiments/comparison_grid.py`: +80 LOC (Arm extension,
  V0_19_ARMS, expanded RunDiagnostics + ArmCellAggregate).
- `experiments/fear_hunger_chamber.py`: +10 LOC (kwargs
  threaded through `model_copy`).
- New tests: ~400 LOC across three files.
- This doc: ~520 LOC.

Total v0.19 implementation: ~1,250 LOC. Larger than v0.18 (~720)
because it touches conservation accounting end-to-end. The core/
changes remain well-scoped — one new module, two new fields per
affected module, two new events, one new phase-0 hook integrated
with the existing v0.18 phase-0 respawn pass.

## References

- [[docs/experiments/fear_hunger_v0.18.md]] — v0.18 results;
  substrate compounds under non-saturating food, K-20
  over-saturation regression, conservation caveat that v0.19 closes.
- [[docs/experiments/fear_hunger_v0.17.md]] — v0.17 results;
  child-energy lift under handout, conservation caveat first
  pre-committed.
- [[docs/experiments/fear_hunger_v0.16.md]] — food_events hard cap
  (192 / 174) finding.
- [[docs/specs/v0.2_reflex_cell_spec.md]] §"Comparison framework" —
  the substrate axis.
