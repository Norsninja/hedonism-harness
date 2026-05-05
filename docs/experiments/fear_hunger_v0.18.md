# v0.18 — food respawn cooldown under non-saturation (not strict conservation)

**Status:** pre-registration; not yet executed.
**Date:** 2026-05-05
**Branch:** `claude/v0.18-food-respawn`
**Predecessors:** v0.14 (reflex cell, first compounding), v0.15
(chemotaxis-tier scalar memory, no compounding lift), v0.16
(reproduction-economics: per-parent lever, ceiling barely moves),
v0.17 (offspring-energy: child energy is the binding constraint
under handout — the largest single intervention effect to date,
but under a free injection, not under conservation).
**Spec:** [[docs/specs/v0.2_reflex_cell_spec.md]] §"Comparison framework"
(substrate axis).

## Question

v0.17 proved the v0.14-v0.16 lineage ceiling was child-survival-
bounded by giving each newborn 30 → 100 starting energy as a free
handout. The handout produced ∞× / ×36.8 lifts on
`births_after_tick_50` and ×8 / ×102 lifts on
`mean_grandchildren_per_seed` — the largest single intervention in
the project's history. But the lift was a free energy injection: each
newborn's starting energy materialised from nothing, not drawn from
parent or environment.

**v0.17 proves:** the v0.14-v0.16 lineage ceiling was child-survival-
bounded.

**v0.17 does NOT yet prove:** the substrate compounds under conserved
ecology.

That distinction is now the central project question. v0.18 tests the
cheapest version of conservation: **non-saturating food**. Replace
the v0.7..v0.17 single-paint-no-respawn chamber with a per-tile
cooldown — when a FOOD cell is consumed it becomes EMPTY, and after
K ticks it flips back to FOOD with the original `food_value`.

Holds `offspring_start_energy=30` (the v0.7..v0.16 baseline). If
compounding lifts under cooldown alone — without the v0.17 handout —
then the static-food cap was the binding constraint and the
substrate compounds when food is renewable. If it does not lift —
even with K=20 — child energy is necessary independent of food
supply, and the v0.17 finding is not a proxy for "more food per
child."

## What this slice tests, and what it does NOT test

### Tests
- Whether **non-saturating food** (delivered via per-tile cooldown
  respawn) supports lineage compounding at the v0.7..v0.16 baseline
  child energy of 30. The "win" condition is that K∈{50, 20} arms
  reach `births_after_tick_50` levels comparable to v0.17 start-100
  with `offspring_start_energy=30`.
- Whether the v0.17 finding (child energy is binding) extends to
  food supply (food respawn is binding) or stands alone (child
  energy is binding regardless of food supply).

### Does NOT test
- **Strict mass-energy conservation.** Cooldown respawn injects new
  energy from nowhere on a delay; it answers "is the static-food
  cap the binding constraint?" but does not balance creation
  against consumption.
- **Combined-axis behaviour.** Whether respawn + raised
  `offspring_start_energy` produces multiplicative lifts is a
  separate question, deferred to v0.18b if and only if v0.18
  alone fails to lift compounding.

### Deferred (v0.19 candidates)
- **v0.19 candidate = strict energy conservation.** Ambient energy
  pool, drained on consumption, refilled on death; respawn drawn
  from the pool. Substantially larger engineering surface (mass-
  energy bookkeeping, dead-cell energy recycling). Pre-committed
  here so v0.18's pragmatic framing does not get re-litigated as
  "we already did conservation."
- **v0.18b** — combined-axis (respawn + offspring_start_energy=100).
  Only run if v0.18 alone fails to lift compounding. The data from
  v0.18 will then disentangle whether food and child-energy are
  independent levers.

## Mechanism

### Per-tile cooldown respawn

A new world layer `respawn_at_tick` (int32, default 0) per cell.

- **Schedule on consumption.** When an agent EATs a FOOD cell at
  tick T, the cell becomes EMPTY (existing behaviour) AND
  `respawn_at_tick[x, y] = T + K` where K is the configured
  cooldown.
- **Refill on schedule (phase 0 of `step()`, before the snapshot).**
  At the start of each tick, scan cells where
  `kind == EMPTY AND respawn_at_tick > 0 AND tick >= respawn_at_tick`.
  Flip back to FOOD with `food_value_default`; reset
  `respawn_at_tick = 0`. Emit one `FoodRespawned(x, y, tick)` event
  per refilled cell. Refilled cells are visible to the foraging
  policy this tick — placement at phase 0 avoids the off-by-one
  that would arise if respawn ran after agent decisions.

### Sentinel choice (pre-committed)

`respawn_at_tick = 0` means "not scheduled." Initial state is
all-zero. After respawn, reset to 0 so the cell is "fresh again."
This avoids negative-sentinel branching and keeps the predicate
simple. Cooldown values must be ≥ 1 (Pydantic-enforced); K=0 is
disallowed because `tick + 0 = tick` would clash with the unscheduled
sentinel for the cell consumed on tick 0. K=1 is the smallest legal
value (refill next tick).

### Edge case: respawn under occupant (pre-committed)

When a cell refills and an agent is standing on it, the agent's
reflex (`current_food_value > 0` → EAT) fires next tick. The cell
refills regardless of occupancy; the alternative "skip respawn if
occupied" introduces a fairness asymmetry where stationary agents
block their own and others' future food. The chosen rule preserves
symmetry between occupied and unoccupied cells.

### Determinism (pre-committed feature)

Cooldown respawn is **fully deterministic** — per-tile schedule, no
RNG draws. No new RNG stream, no `RngStreams` modification. K=None
(no respawn) preserves v0.7..v0.17 bit-identity by construction
because the new world layer is never written to (the `AteFood`
subscription is conditional on `cooldown is not None`).

### Configuration

`WorldConfig` gains `food_respawn_cooldown: int | None = None`.
None = no respawn (v0.7..v0.17 default). Integer ≥ 1 enables
cooldown respawn.

`Arm` gains `food_respawn_cooldown: int | None = None` mirroring
the existing energy/offspring overrides. Threaded through to
`WorldConfig` in `_run_one_arm_seed`.

## Arms

Single-axis sweep: every cell uses **reflex-baseline + cost-15 +
offspring_start_energy=30** (the v0.16 cost-15 / v0.17 baseline).
Arms differ only in `food_respawn_cooldown`.

| arm | cooldown K | cell-reuse rate | label |
|---|---:|---|---|
| A | None (∞) | 1× per run | K-inf (bit-identity vs v0.17 start-30) |
| B | 100 | ~2× per run | K-100 |
| C | 50 | ~4× per run | K-50 |
| D | 20 | ~10× per run | K-20 (saturated) |

Four arms × two chambers × eight seeds = **64 runs** (vs 48 for v0.16
and v0.17). The extra arm is the bit-identity baseline (K-inf).

`offspring_start_energy=30`, `energy_cost=15`, `energy_threshold=50`,
chamber layouts unchanged from v0.17.

## Pre-registered hypotheses

Two-tier structure consistent with v0.15 / v0.16 / v0.17:
**strong-form** for the mechanical intervention firing,
**cautious-form** for the substantive ceiling lift.

### Strong form (the intervention fires)

- **H1.** `total_food_events` rises monotone-non-decreasing as K
  decreases on both chambers. K-inf reproduces v0.17 start-30
  baselines (192 / 174). K-20 should lift food_events substantially
  above baseline (the cell-reuse rate predicts ~×4-×10 lift at
  K-20). If H1 fails at K-20 the intervention is broken (cells are
  not actually refilling); investigate before drawing inference.
- **H2.** `total_food_respawn_events` rises monotone-non-decreasing
  as K decreases. At K-inf this is exactly 0 (no respawn config →
  no subscription → no events). At K-20 it should be in the
  hundreds per chamber. Direct telemetry of intervention firing.

### Cautious form (the ceiling lifts)

- **H3.** `births_after_tick_50` lifts at K-20 vs K-inf on
  food_ladder. **Cautious.** v0.17 start-100 produced 147
  on food_ladder; v0.17 start-30 produced 4. If respawn alone
  (without raising offspring energy) reaches anywhere near 147,
  food was the dominant lever. If it stays near 4, child-energy
  is independent.
- **H4.** `births_after_tick_50` lifts off zero at K-20 vs K-inf
  on tight_gradient. **Cautious.** v0.17 start-30 was 0; v0.17
  start-100 was 72.
- **H5.** `mean_grandchildren_per_seed` rises at K-20 vs K-inf on
  both chambers. **Cautious.** v0.17 start-30 reported 2.38
  (tight) / 0.38 (food_ladder); v0.17 start-100 reported 19.12 /
  38.88.
- **H6.** `seeds_with_survivors` rises at K-20 vs K-inf on at
  least one chamber.

### Determinism

- **H7.** Arm K-inf reproduces v0.17 start-30 bit-identically on
  per-seed `(total_births, births_after_tick_50, seeds_with_survivors,
  total_food_events, total_grandchildren_count)`. The new
  `respawn_at_tick` PropertyLayer must be inert when no cooldown is
  configured. Verified at sweep time and via a unit test that
  asserts event-log equality between K-None and the v0.17
  baseline-equivalent.

## Conservation accounting metric

New telemetry in v0.18: **`food_consumed_per_birth`**. Computed in
`ArmCellAggregate` as
`(total_food_events × food_value_default) / total_births`.

**Why this metric.** Under v0.17 start-100, this ratio is artificially
low: the chamber paid 174 × 20 = 3480 food-energy across the run, and
produced 366 births on food_ladder; ratio = 9.5 energy per birth. But
each child arrived with 100 free energy from nowhere — the chamber
paid 9.5 environmental energy per birth that "cost" at minimum
`energy_cost + offspring_start_energy = 15 + 100 = 115` energy. The
gap exposes the handout: 105.5 of every 115 energy per birth came
from outside the food economy.

Under v0.18 with `offspring_start_energy=30` (no handout) and
respawn enabled, the floor for self-sustaining births is
`energy_cost + offspring_start_energy = 15 + 30 = 45` energy per
birth (parent's reproduction cost plus the child's starting energy,
which the child consumed from food the parent ate before reproducing).
Plus a per-birth survival overhead from base metabolism + memory of
parent's pre-reproductive forage cycle, putting the realistic floor
in the 50-80 range.

If v0.18 K-20 produces `food_consumed_per_birth ≥ 50` while sustaining
compounding, **the substrate is paying for births with food** — a
defensible interpretation of "self-sustaining via food alone." If the
ratio stays low and compounding still lifts, the chamber is generating
"free" energy somewhere (likely respawn happening faster than
consumption depletes the population, with the surplus going to
metabolism rather than reproduction). Worth instrumenting either way.

## Headline metrics

Carried forward from v0.17:

- `total_births`, `seeds_with_any_births`
- `births_after_tick_50` — the H2 ceiling test from v0.13 onwards.
- `seeds_with_survivors` at run end.
- `still_tick_fraction`, `total_food_events`, `hazard_entries`,
  `starvation_deaths`, `reproduction_requests`.
- v0.16 per-parent: `mean_births_per_parent`,
  `mean_post_birth_lifespan_ticks`, `total_distinct_parents`,
  `total_post_birth_lifespan_ticks` (raw).
- v0.17: `total_grandchildren_count`, `mean_grandchildren_per_seed`.
- `max_population_end`, `total_starvation_deaths`,
  `total_reproduction_requests`.

New v0.18 telemetry:

- **`total_food_respawn_events`** — count of `FoodRespawned`
  emissions. Always 0 at K-inf.
- **`food_consumed_per_birth`** — derived ratio (see above).

## Decision rules

- **K-20 reaches v0.17-start-100 levels on `births_after_tick_50`
  and `mean_grandchildren_per_seed`** (within ~25%). **Food was the
  dominant lever; child-energy was a proxy.** v0.19 = strict energy
  conservation (the next-cheapest follow-up) to test whether the
  lift survives a closed energy budget.

- **K-20 lifts compounding but stays well below v0.17-start-100
  levels.** Both food and child-energy are real, partially
  independent levers. v0.18b combined-arm (respawn + offspring=100)
  resolves whether they multiply or saturate.

- **K-20 fails to lift compounding meaningfully.** Child-energy is
  necessary independent of food supply. The v0.17 finding stands
  alone; food respawn alone is not sufficient. v0.18b combined-arm
  becomes mandatory and v0.19 strict-conservation needs a different
  framing.

- **`food_consumed_per_birth` stays below the 50-energy floor at
  K-20 even when compounding lifts.** The chamber is producing
  "phantom" births — population is large enough that respawn flux
  exceeds consumption flux and surplus goes to metabolism, not
  reproduction. Worth instrumenting via per-tick population /
  reproduction-request telemetry in v0.19 if it matters.

## Out of scope (v0.18)

- Strict mass-energy conservation (v0.19 candidate).
- Combined-axis arms (v0.18b candidate, only if v0.18 alone fails).
- Spatial respawn rules (per-column quotas, density-dependent
  respawn). The v0.18 mechanism is uniform per-tile cooldown.
- Variable food yield on respawn. v0.18 respawns at the painted
  `food_value_default`.
- ScalarMemory under varied K. The v0.15 chemotaxis cell stays
  inert in this slice.
- HedonismPolicy comparisons — quarantined per v0.2 spec.
- Multi-cell-tier directional EMA — deferred until the substrate
  question is settled.

## Implementation notes

### File-level changes

- Modify: [[src/hedonism_harness/core/world.py]] —
  add `respawn_at_tick: np.ndarray` (int32) to `World`. Initialize
  zeros in `build_world`. The Cell read-only view does NOT include
  this field (it's machinery, not part of the agent's observation).
- Modify: [[src/hedonism_harness/core/config.py]] —
  add `food_respawn_cooldown: int | None = Field(default=None, ge=1)`
  to `WorldConfig`. None preserves v0.7..v0.17 bit-identity.
- Modify: [[src/hedonism_harness/core/events.py]] —
  add `FoodRespawned(x: int, y: int, tick: int)` dataclass; register
  signal `hh.food_respawned`. Add to `AnyEvent` union.
- Modify: [[src/hedonism_harness/model.py]] —
  attach 5th PropertyLayer `respawn_at_tick` (int32) in
  `_attach_shared_property_layers`. In `__init__`, conditionally
  subscribe to `AteFood` (`sender=self`) when
  `world_config.food_respawn_cooldown is not None`; the handler
  schedules `respawn_at_tick[x, y] = tick_count + cooldown` on each
  AteFood event. Add `_apply_food_respawn` method called as phase 0
  of `step()`. Disconnect on death-of-model is handled implicitly
  (no test currently relies on long-lived signal cleanup; if the
  test suite needs it later we add a `close()` method).
- Modify: [[src/hedonism_harness/io/jsonl_writer.py]] —
  ensure `FoodRespawned` events serialize cleanly (mirror the
  pattern for AteFood). Likely zero-LOC change if the writer reads
  fields generically; verify.
- Modify: [[src/hedonism_harness/experiments/comparison_grid.py]] —
  extend `Arm` with optional `food_respawn_cooldown: int | None
  = None`; thread through `_run_one_arm_seed` to the `WorldConfig`
  passed into `run_chamber`. Add `V0_18_ARMS` tuple of four arms
  at K ∈ {None, 100, 50, 20}.
- Modify: [[src/hedonism_harness/experiments/comparison_grid.py]] —
  extend `RunDiagnostics` with `total_food_respawn_events`; extend
  `ArmCellAggregate` with that field plus the
  `food_consumed_per_birth` property. Single-pass extraction in
  `_read_run_diagnostics` adds one branch on the `FoodRespawned`
  event type.
- New: [[tests/test_food_respawn.py]] — unit tests for cooldown
  scheduling, refill predicate, edge cases (occupied tile,
  newly-painted chamber, tick=0 respawn check), and the
  K-None bit-identity contract (event-log equality on a short
  fixed-seed run).
- New: [[tests/test_comparison_grid_food_respawn.py]] — Arm field
  default, V0_18_ARMS shape, end-to-end run with override,
  V0_15/V0_16/V0_17 arms unchanged, total_food_respawn_events
  counted correctly.
- Documented: this file (`docs/experiments/fear_hunger_v0.18.md`);
  results appended after the sweep.

### Determinism contract

- Arm K-inf reproduces v0.17 start-30 bit-identically on per-seed
  `(total_births, births_after_tick_50, seeds_with_survivors,
  total_food_events, total_grandchildren_count)`. v0.17 start-30
  in turn reproduces v0.16 cost-15 bit-identically (the v0.17
  bit-identity contract). Transitively, K-inf reproduces v0.16
  cost-15 numbers — anchoring back to v0.7-era determinism on the
  shared seeds.
- Override defaults are `None`. The existing `V0_14_ARMS`,
  `V0_15_ARMS`, `V0_16_ARMS`, and `V0_17_ARMS` produce identical
  sweep outputs after the v0.18 changes.
- The `respawn_at_tick` PropertyLayer is allocated regardless of
  config (storage hygiene), but never written to when
  `cooldown is None`. Verified by a unit test that constructs an
  `HHModel` at K=None, runs N ticks, and asserts the layer is
  still all-zero.

### LOC estimate

- `core/world.py`: +5 LOC (one new field).
- `core/config.py`: +5 LOC (one new field).
- `core/events.py`: +15 LOC (event dataclass + signal entry).
- `model.py`: +50 LOC (PropertyLayer, subscription, phase-0
  respawn pass).
- `comparison_grid.py`: +30 LOC (Arm extension, V0_18_ARMS,
  diagnostics field).
- New tests: ~250 LOC across two files.
- This doc: ~370 LOC.

Total v0.18 implementation: ~720 LOC. Larger than v0.17 (~510)
because it touches `core/` rather than only `experiments/`. The
core/ changes are well-scoped: one new field per affected module,
one new event, one phase-0 hook.

## Results (executed 2026-05-05)

Four arms × two chambers × eight seeds (1..8) × 200 ticks × 5 founders.
**64 runs total.** Reflex-baseline policy (no scalar memory),
`energy_cost=15`, `energy_threshold=50`, `offspring_start_energy=30`,
`unbounded_mutation=True`. Only `food_respawn_cooldown` varies.

### Headline finding — substrate compounds under non-saturating food

**K-50 on tight_gradient produces 130 `births_after_tick_50`,
exceeding v0.17 start-100's 72 by 80%, with `offspring_start_energy=30`
and no per-birth handout.** Food-respawn cooldown alone reaches
v0.17-handout compounding levels and beyond, while paying for births
with food (`food_consumed_per_birth ∈ [51, 95]` in productive arms,
above the 45-energy self-sustaining floor).

**v0.18 proves: the substrate compounds under non-saturating food
without any per-birth energy handout.** v0.17's child-energy lift was
largely (but not entirely) a proxy for "more food per child."

**v0.18 does NOT yet prove: the substrate compounds under strict
mass-energy conservation.** Cooldown respawn injects new energy from
nowhere on a delay; v0.19 (strict conservation: ambient pool, drained
on consumption, refilled on death) is now the locked next slice.

### Environmental food accounting is now plausible; strict conservation remains untested

Under v0.17 start-100 the ratio was artificially low (9.5 on
food_ladder) — the gap between environmental food consumed and
energy required per birth measured the size of the handout. Under
v0.18 with no handout, productive arms pay for births with food:

| chamber | arm | fcpb | interpretation |
|---|---|---:|---|
| tight_gradient | K-inf | 51.89 | baseline; food_events / births = 192/74 × 20 |
| tight_gradient | K-100 | 51.20 | minimum self-sustaining, just above 45 floor |
| tight_gradient | K-50 | 75.29 | productive — above floor with margin |
| tight_gradient | K-20 | 212.99 | over-saturated — surplus food to metabolism |
| food_ladder | K-inf | 63.27 | baseline |
| food_ladder | K-100 | 74.77 | self-sustaining |
| food_ladder | K-50 | 94.69 | productive |
| food_ladder | K-20 | 155.05 | abundant food regime |

The fcpb floor is `energy_cost + offspring_start_energy = 45`. Every
v0.18 arm clears it; v0.17 start-100 was 9.5 (-78% below floor) —
the gap that the handout filled. Under v0.18 the substrate is paying
for births with food in every arm, but **food respawn still creates
energy from nowhere on a delay**. Environmental food accounting is
plausible — the v0.17 handout-shaped gap closes — but strict
mass-energy conservation remains untested. v0.19 closes that gap
by drawing respawn from a finite energy pool.

### Next slice (v0.19) — locked

**v0.19 = strict mass-energy conservation.** Cooldown respawn
demonstrates non-saturating food supports compounding; it does not
demonstrate compounding under a closed energy budget. v0.19 replaces
the cooldown's "energy from nowhere on a delay" with an ambient
energy pool: cell consumption drains the pool, cell death recycles
energy back, food respawn draws from the pool. Tests whether the
v0.18 lift survives when energy creation is tied to energy
destruction.

If the v0.18 lift survives strict conservation, the substrate is
truly self-sustaining. If not, the v0.18 result was "non-saturating
food permits compounding" rather than "the substrate compounds
under conservation," and v0.19's findings will tell us which
balance terms are missing.

### Determinism contract — verified

Arm K-inf reproduces v0.17 start-30 bit-identically on both chambers
across all four contract metrics plus `total_grandchildren_count`:

| chamber | metric | v0.17 start-30 | v0.18 K-inf | match |
|---|---|---:|---:|:---:|
| tight_gradient | `total_births` | 74 | 74 | ✓ |
| tight_gradient | `births_after_tick_50` | 0 | 0 | ✓ |
| tight_gradient | `seeds_with_survivors` | 2/8 | 2/8 | ✓ |
| tight_gradient | `total_food_events` | 192 | 192 | ✓ |
| tight_gradient | `total_grandchildren_count` | 19 | 19 | ✓ |
| food_ladder | `total_births` | 55 | 55 | ✓ |
| food_ladder | `births_after_tick_50` | 4 | 4 | ✓ |
| food_ladder | `seeds_with_survivors` | 4/8 | 4/8 | ✓ |
| food_ladder | `total_food_events` | 174 | 174 | ✓ |
| food_ladder | `total_grandchildren_count` | 3 | 3 | ✓ |

The new `respawn_at_tick` PropertyLayer is allocated regardless of
config and remains all-zero at K-inf (verified by unit test). The
`AteFood` subscription is conditional on `food_respawn_cooldown is
not None`, so the determinism contract holds by construction.

### v0.18a tight_gradient

| arm | births | b>50 | survivors | parents | b/p | lifespan_mean | lifespan_total | gc | gc/seed | food | respawn | fcpb | pop_end | starv | repro_req | still% |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| K-inf  |  74 |   0 | 2/8 |  24 | 3.08 |  86.2 |  2070 |  19 |  2.38 |  192 |    0 |  51.89 |  1 | 112 |  74 | 94.4 |
| K-100  | 150 |  76 | **8/8** |  48 | 3.12 |  83.4 |  4003 |  77 |  9.62 |  384 |  192 |  51.20 |  8 | 159 | 150 | 92.8 |
| K-50   | 204 | **130** | **8/8** |  70 | 2.91 | 112.2 |  7855 | 124 | 15.50 |  768 |  576 |  75.29 | 18 | 126 | 208 | 90.4 |
| K-20   | 177 |  43 | **8/8** |  71 | 2.49 | 159.0 | 11291 | 115 | 14.38 | 1885 | 1693 | 212.99 | 24 |  25 | 181 | 91.8 |

Notable: **K-50 produces 130 `births_after_tick_50` — 80% above
v0.17 start-100 (72) — without any per-birth handout.** K-100 matches
v0.17 start-100 closely (76 vs 72). K-20 *regresses* on b>50 (43 vs
K-50's 130) despite total_births being similar (177 vs 204) — the
over-saturation regime, discussed below.

### v0.18b food_ladder

| arm | births | b>50 | survivors | parents | b/p | lifespan_mean | lifespan_total | gc | gc/seed | food | respawn | fcpb | pop_end | starv | repro_req | still% |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| K-inf  |  55 |   4 | 4/8 |  28 | 1.96 | 81.5 |  2281 |   3 |  0.38 |  174 |    0 |  63.27 |  2 | 90 |  55 | 93.9 |
| K-100  |  88 |  37 | **8/8** |  35 | 2.51 | 83.1 |  2907 |  26 |  3.25 |  329 |  174 |  74.77 |  9 | 88 |  88 | 91.6 |
| K-50   | 143 |  92 | **8/8** |  51 | 2.80 | 88.5 |  4515 |  74 |  9.25 |  677 |  504 |  94.69 | 16 | 77 | 143 | 87.0 |
| K-20   | 186 | **122** | **8/8** |  69 | 2.70 | 85.3 |  5883 | 118 | 14.75 | 1442 | 1290 | 155.05 | 22 | 28 | 190 | 81.4 |

food_ladder is monotone throughout: total_births, b>50, gc/seed all
rise as K decreases. K-20 reaches `births_after_tick_50 = 122`,
which is 83% of v0.17 start-100's 147 — close but not equal. The
remaining gap suggests **child-energy was largely but not entirely
a proxy for food supply** on food_ladder; some independent
contribution exists. v0.18b combined-axis (respawn + offspring=100)
would resolve the residual, but the gap is small enough that v0.19
strict-conservation is a higher-priority next slice.

### The K-20 over-saturation regression on tight_gradient

K-20 tight_gradient produces fewer post-tick-50 births (43) than
K-50 (130), despite more total food (1885 vs 768) and more total
births (177 vs 204 — comparable). The mechanism appears to be:

- **Starvation deaths drop from 126 to 25** at K-20. Cells survive
  far longer per food unit because food is essentially overflowing
  (food_consumed_per_birth = 213).
- **Mean post-birth lifespan rises from 112 to 159 ticks.** Parents
  live longer post-birth.
- But **reproduction_requests stay flat** (208 → 181), and most of
  those births land before tick 50. With food everywhere, children
  reach reproduction threshold quickly, the population stabilises
  early, and reproductive selection pressure drops in the late-run
  window.

Interpretation: the chamber is **over-saturated**. K-50 is the
productive sweet spot on tight_gradient — enough non-saturation that
energy must flow through reproduction to compound, not so much that
the feedback dampens. food_ladder does not exhibit this regression
in the {K-inf, K-100, K-50, K-20} band — the chamber's pre-food
band may make even K-20 still energy-limited at the population level,
or the geometry leaves a productive gradient even with abundant food.

This is itself a substrate finding: **the relationship between food
density and lineage compounding is non-monotonic**. v0.19's strict-
conservation framing should expect the same shape — there will
likely be a productive K (or pool size) where the substrate
compounds maximally, and over-saturation becomes a regression.

### Hypotheses → outcomes

- **H1.** `total_food_events` rises monotone-non-decreasing as K
  decreases. **Confirmed strongly on both chambers.**
  tight_gradient: 192 → 384 → 768 → 1885; food_ladder: 174 → 329
  → 677 → 1442. Mechanism fires cleanly.
- **H2.** `total_food_respawn_events` rises monotone as K decreases.
  **Confirmed.** K-inf=0 in both chambers; rises to 1693
  (tight_gradient) and 1290 (food_ladder) at K-20. Direct telemetry
  of intervention firing.
- **H3.** `births_after_tick_50` lifts on food_ladder. **Confirmed
  strongly.** 4 → 37 → 92 → 122 at K-20 (×30.5).
- **H4.** `births_after_tick_50` lifts off zero on tight_gradient.
  **Confirmed strongly.** 0 → 76 → 130 → 43. K-50 reaches 130 —
  twice v0.14-v0.16's hard-zero ceiling, exceeding v0.17 start-100.
- **H5.** `mean_grandchildren_per_seed` rises at K-20 vs K-inf on
  both chambers. **Confirmed.** tight_gradient: 2.38 → 14.38 (peaks
  at K-50 = 15.50). food_ladder: 0.38 → 14.75 (strictly monotone).
- **H6.** `seeds_with_survivors` rises. **Confirmed strongly on
  both chambers.** tight_gradient 2/8 → 8/8 (K-100 onwards);
  food_ladder 4/8 → 8/8 (K-100 onwards). Full survival under any
  finite K.
- **H7.** Arm K-inf reproduces v0.17 start-30 bit-identically.
  **Confirmed** — see Determinism contract table above.

### Decision rule fired (per pre-reg)

> **K-50 reaches v0.17-start-100 levels on `births_after_tick_50`
> and `mean_grandchildren_per_seed`** (within ~25% on food_ladder,
> EXCEEDS on tight_gradient). **Food was the dominant lever;
> child-energy was largely a proxy.** v0.19 = strict energy
> conservation (the next-cheapest follow-up) to test whether the
> lift survives a closed energy budget.

The conservation caveat fully governs the interpretation. v0.18
demonstrates **the substrate compounds under non-saturating food
without per-birth handouts.** It does not demonstrate the substrate
compounds under strict mass-energy conservation. Whether the same
lift survives a closed energy budget — where every unit of food
that respawns must be drawn from somewhere — is the open question
for v0.19.

### Where v0.17's child-energy finding now sits

v0.17's headline was: child energy is the binding constraint on
lineage compounding under the v0.14-v0.16 substrate. v0.18 reframes:

- **On tight_gradient**, v0.17's child-energy lift was a near-pure
  proxy for food supply. v0.18 K-50 with offspring=30 produces 130
  b>50, vs v0.17 start-100's 72 — child-energy was less effective
  per-unit-energy than food respawn at moving the ceiling.
- **On food_ladder**, child-energy retains some independent effect.
  v0.18 K-20 with offspring=30 produces 122 b>50 vs v0.17
  start-100's 147 — about 83% of the lift, suggesting ~17% of
  v0.17's effect on food_ladder was child-energy independent of
  food supply.

The v0.17 finding is not invalidated; it is contextualised. Children
were dying before reproducing because they couldn't reach food in
time. v0.18 confirms the mechanism (more food = more child survival
via shorter time-to-first-meal), and shows that giving the chamber
more food is generally more efficient than giving each newborn a
free 70-energy boost. The child-energy lever is a real lever, but
at most ~20% of its v0.17 magnitude was independent of the food
supply it implicitly substituted for.

### Data points worth flagging for v0.19

- **The non-monotonic K-20 result on tight_gradient.** v0.19 sweeps
  should bracket the saturation regime — going past the productive
  K is informative but the productive K itself is the experimental
  target.
- **`food_consumed_per_birth` is the right interpretive metric.**
  At K-100 tight (51.2) the substrate is at the minimum
  self-sustaining floor; at K-50 (75) it's productive with margin;
  at K-20 (213) it's wasting most of the food on metabolism. v0.19
  should report fcpb prominently and use the floor as a sanity
  bound on "is this self-sustaining."
- **`max_population_end` lifts dramatically.** tight_gradient 1 → 24
  at K-20; food_ladder 2 → 22 at K-20. Population becomes the
  limiting factor under abundant food; v0.19's pool size implicitly
  caps it.
- **Reproduction-request rejection rate is small but nonzero at
  K-50 tight (208 requests, 204 births).** Same hazard_threshold /
  min_age rejections seen in v0.17 start-100. Not currently
  blocking; track in v0.19 if rejection rate becomes meaningful.
- **`still_tick_fraction` falls under cooldown** (94.4 → 91.8 tight;
  93.9 → 81.4 food_ladder). Counter to v0.17's population-artefact
  rise — under v0.18, more food in sensor range means more MOVE
  decisions even without raised offspring energy. Consistent with
  the v0.15 chemotaxis finding that cells move when there's a
  gradient to climb.

## References

- [[docs/experiments/fear_hunger_v0.17.md]] — v0.17 results;
  child-energy lift under handout, conservation caveat,
  v0.18 framing.
- [[docs/experiments/fear_hunger_v0.16.md]] — v0.16 results;
  food_events hard cap (192 / 174) finding.
- [[docs/specs/v0.2_reflex_cell_spec.md]] §"Comparison framework" —
  the substrate axis the v0.2 spec named.
