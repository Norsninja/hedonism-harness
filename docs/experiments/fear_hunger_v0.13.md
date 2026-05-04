# Fear-Hunger Chamber — v0.13 memory-channel calibration

**Experiment:** Profile `novelty_pleasure` magnitude against peer
harness terms (Phase 1, pre-registered as a read-only diagnostic),
then ship the smallest targeted wiring fix the profile implied —
gating `novelty_pleasure` on `obs_before.hunger_level` to mirror
`anticipated_food_pleasure` — and re-run the v0.12 directional +
action-aware sweep on both chambers (Phase 2).
**Branch:** `claude/v0.13-memory-channel-calibration`
**Date:** 2026-05-04
**Runs:** `runs/fear-hunger-v0.13-profile/` (Phase 1),
`runs/fear-hunger-v0.13a/` (Phase 2 tight_gradient),
`runs/fear-hunger-v0.13b/` (Phase 2 food_ladder).
**Status:** Phase 1 confirmed H1 (wiring asymmetry) and H2
(late-stage stall) independently — see
[[docs/experiments/fear_hunger_v0.13_profile.md]]. Phase 2 shipped
the hunger-gate; results below.

## Question

v0.12 demonstrated that action-aware directional projection is causal
(argmax_change_rate 1.0–16.4 % across cells, vs 0.0 % in v0.11) but
the projection's design choice — zero memory fields for non-MOVE
actions — creates a structural asymmetry: `MOVE_<DIR>` candidates
receive a `novelty_pleasure` bonus from
`remembered_good_<DIR> * traits.novelty_drive`, while `EAT` /
`STAY` / `REPRODUCE` receive zero memory contribution. On
tight_gradient, **49 % of swayed decisions are `EAT -> MOVE_*`**:
the agent walks off food chasing remembered tendencies. v0.10
cell-exact memory and v0.12 directional memory both produced the
"substrate up, births flat" pattern on food_ladder, neither produced
a survival win, and v0.12 actually regressed seeds-with-survivors
0/8 vs v0.10's 1/8.

Two hypotheses compete:

- **H1 — wiring asymmetry:** `novelty_pleasure` is mis-scaled and
  un-gated relative to its peer pleasure terms. Comparing
  `core/valence.py:141` and `core/valence.py:157`,
  `anticipated_food_pleasure` is `* obs_before.hunger_level *
  pleasure_sensitivity`; `novelty_pleasure` is just
  `* novelty_drive`. A sated agent's anticipated-food channel goes
  silent while its memory channel keeps full strength — exactly the
  wrong direction. Fix: gate `novelty_pleasure` on hunger.
- **H2 — economics or tick budget:** even with a clean memory channel
  the chamber yields a first birth and then stalls; the bottleneck is
  energy_threshold / energy_cost or 200 ticks being too short for
  lineage compounding (the v0.10 substrate-up-births-flat pattern
  reproduces on a different representation, suggesting a fixed
  ceiling).

v0.13 tests H1 first, with a falsification path that surfaces H2 as
the next stop if H1 closes cleanly. Categorical memory (the v0.12
ranking's option (2)) stays parked.

## Plan — two phases, one slice

### Phase 1: profile (read-only, no harness math change)

Pre-register **three traces**, computed by running the v0.12 winner
configuration and dumping `breakdown.details` for every candidate
action at hand-picked tick / agent boundaries:

1. **Hungry agent on food.** Hunger_level high, on_food=True,
   directional memory's east slot loaded by recent eating. Compare
   `eating_pleasure` (from EAT) against `novelty_pleasure` (from
   MOVE_*). Tests H1 directly: if `novelty_pleasure(MOVE_*) >
   eating_pleasure(EAT)`, the override pathology is mechanically
   confirmed.
2. **Hungry agent off food, food visible at sensor radius, memory
   pointing at it.** Tests whether memory + anticipated_food
   *coherently* steer the agent — the case memory is supposed to
   help. If `novelty_pleasure + anticipated_food_pleasure` on the
   correct MOVE direction beats STAY's zero, foraging supply works.
3. **Sated agent off food, memory pointing at known-good direction.**
   Sated is the regime where the missing hunger-gate on
   `novelty_pleasure` matters most. If the agent moves toward
   remembered-good when it should be saving energy / sitting safe,
   that's H1's clearest fingerprint.

Plus a **by-tick birth distribution** read on existing v0.10 / v0.12
winner runs (`runs/fear-hunger-v0.10/cells/ms1-md0.1/seed-*/events.jsonl`):
how many births fall in each 25-tick bucket of the 200-tick run? If
all births cluster in the first ~50 ticks and nothing happens after,
that's H2's signature ("first birth happens; subsequent ones don't"
== reproduction economics or tick budget pinching). If births spread
across the run, H2 is weaker.

Phase 1 outputs: `docs/experiments/fear_hunger_v0.13_profile.md` with
the three trace tables + the birth-distribution histogram. No code
in `core/` changes.

### Phase 2: targeted wiring fix + sweep (only if Phase 1 supports H1)

If Phase 1 traces show `novelty_pleasure >= eating_pleasure` in
trace 1 (or anywhere `novelty_pleasure` overrides another channel
that should win), apply **one** wiring change:

```python
# core/valence.py — line 156–157, current:
novelty_score = _remembered_good_total(obs_after)
novelty_pleasure = novelty_score * traits.novelty_drive

# Phase 2 candidate fix — mirror anticipated_food_pleasure's
# hunger-gating pattern. Gates memory's pleasure channel on
# hunger_level so a sated agent does not chase remembered-good
# when it should be conserving energy / staying safe.
novelty_score = _remembered_good_total(obs_after)
novelty_pleasure = (
    novelty_score * obs_before.hunger_level * traits.novelty_drive
)
```

This is the minimum-scope intervention. It does **not** rename the
trait, does **not** add a `memory_drive` trait, and does **not**
touch the projection. If the profile implies a different fix
(e.g., multiplicative cap on novelty_pleasure ≤ eating_pleasure), the
pre-reg branch below covers that — but this is the leading candidate.

Then re-run the v0.12 directional sweep on both chambers under the
new harness:

- **v0.13a**: `tight_gradient` + `directional` + action-aware
  projection + hunger-gated `novelty_pleasure`.
- **v0.13b**: `food_ladder` + `directional` + action-aware
  projection + hunger-gated `novelty_pleasure`.

Hyperparameters identical to v0.12: 10 cells × 8 seeds = 80 runs per
chamber.

## Pre-registered viability rule (six criteria, unchanged)

1. `total_births >= 2`
2. `seeds_with_any_births >= 2`
3. `total_food_events >= baseline.total_food_events − total_births`
4. `seeds_with_any_starvation > 0`
5. `max_population_end <= 3 × n_founders = 15`
6. `total_reproduction_requests >= total_births`

Plus the v0.12 telemetry counters
(`directional_decisions`, `argmax_changes`, `argmax_change_rate`,
`action_transitions`) carry forward unchanged. The
`EAT -> MOVE_*` transition count is the headline phase-2 diagnostic.

## Pre-registered failure → action mapping

### Phase 1 outcomes

- **`novelty_pleasure(MOVE_*) >> eating_pleasure(EAT)` in trace 1**
  → H1 confirmed mechanically. Proceed to Phase 2 with the
  hunger-gate fix.
- **`novelty_pleasure` is comparable to or smaller than
  `eating_pleasure` in trace 1** → H1's leading candidate is wrong.
  EAT-override may come from a different channel
  (`safety_pleasure`? `anticipated_food_pleasure` on a *different*
  direction outweighing eating?). Profile output redirects Phase 2
  toward the actual dominating channel.
- **Profile is uninterpretable / `breakdown.details` doesn't capture
  the right magnitudes** → file a tooling task; do not ship a Phase 2
  fix on insufficient evidence. (Risk mitigation; expected to be a
  no-op since `details` already carries every named subcomponent.)
- **Birth-distribution histogram clusters in first 50 ticks across
  v0.10 / v0.12 winners** → H2 is corroborated independently. Phase 2
  still ships (cheap, isolated), but v0.14 candidates start with
  reproduction economics / tick budget regardless of Phase 2 outcome.
- **Birth distribution is broad** → H2 weaker; survival ceiling is
  more likely a representation/wiring issue, supporting Phase 2's
  premise.

### Phase 2 sweep outcomes

- **Cells qualify and `total_births > baseline` on either chamber,
  AND `EAT -> MOVE_*` transition counts drop substantially** → H1
  was the bottleneck. Headline win for the project ladder. Validate
  the v0.10 cell-exact sweep under the same gating to confirm the
  fix isn't directional-only.
- **Cells qualify and match baseline births, EAT-override drops, but
  births do not increase** → wiring was real but H2 is the binding
  ceiling. Pivot v0.14 to reproduction economics and/or tick budget.
- **Cells qualify, EAT-override does NOT drop substantially** →
  hunger-gate is not the right intervention even if the profile
  predicted it. Means the profile metric was indicative but not
  causal; revisit the diagnostic.
- **Cells regress vs v0.12 baseline** → unexpected; the gate broke
  more than it fixed. Roll back Phase 2 and reconsider.
- **`tight_gradient` still produces 0/9 qualifiers** → the chamber
  remains unreachable under any current memory representation; H2
  becomes the only remaining lever. (`food_ladder` is the positive
  control.)

## What v0.13 explicitly does NOT do

- **No new memory representation.** Per-cell-kind categorical was the
  v0.12 ranking's option (2); it stays parked. v0.13 is a calibration
  slice on the *existing* directional + action-aware abstraction.
- **No reproduction-economics changes.** `tuned_reproduction_config(et=50,
  ec=35)` stays frozen. Trait master ranges, layouts, and reproduction
  rules are untouched.
- **No semantic-debt cleanup of `novelty_drive`.** The trait is
  semantically wrong (it gates `_remembered_good_total`, which is
  *familiarity / expected reward*, not novelty). A future
  `memory_drive` trait or a fold into `pleasure_sensitivity` is the
  right fix, but it is a refactor, not an experiment. v0.13 keeps the
  current name and only changes the multiplier composition. The
  semantic debt is logged for v0.14+.
- **No projection redesign.** The "zero non-MOVE memory fields"
  choice from v0.12 is preserved. If hunger-gating fails the
  projection-design choice itself becomes a candidate intervention,
  but only after H1's leading candidate is ruled out.

## Watch-outs

- **The Phase 1 traces require a deterministic seed + tick boundary.**
  Use `seed=1, tick=50` from the v0.12b ms1-md0.1 winner run; that
  trace is reproducible and known to contain swayed `EAT -> MOVE_*`
  transitions. Capture the agent's full breakdown.details across all
  valid actions at that exact tick.
- **`obs_before.hunger_level` is in `[0, 1]`** — when an agent is
  fully sated (energy_ratio = 1.0) the gated `novelty_pleasure`
  collapses to 0. That is the desired behavior; just confirm it
  doesn't accidentally silence memory at moderate hunger via numerical
  underflow.
- **The trait-master range for `novelty_drive` is unchanged**, so
  agents inheriting from prior generations carry the same trait
  distribution. Determinism is preserved when memory is `None` or
  `ValenceMemory`; v0.10 / v0.11 / v0.12 sweeps with `memory_type` at
  default re-run bit-identically (verify via existing
  `test_memory_decay_wiring.py` + `test_simulation_determinism_mesa.py`
  before declaring Phase 2 ready).
- **Argmax-changes telemetry remains directional-only.** Phase 2's
  EAT-override drop is measured via the `action_transitions` Counter
  on the per-cell aggregate; we do not need new telemetry. Confirm
  the existing transitions plumbing surfaces `EAT -> MOVE_*`
  separately (it does, see v0.12 results section).
- **Phase 1 trace dumping is small but new code.** Add a one-shot
  helper in `experiments/` (not in `core/` — pure observation, no
  math change) that takes a model + tick + agent and dumps the per-
  candidate breakdown into a markdown / CSV row.
- **If Phase 1 redirects Phase 2 to a different fix**, document the
  branch firing and the new fix in this doc (post-hoc) before
  running the sweep. Pre-registration is preserved if the *decision
  rule* was specified beforehand, even when the chosen branch wasn't
  the leading candidate.

## Watching the project ladder beyond v0.13

If H1 closes (Phase 2 lifts births on at least one chamber): v0.14
revisits cell-exact memory under the same harness (does the
hunger-gate help v0.10's representation too?), then per-cell-kind
categorical (option (2) from v0.12) as a second positive control.

If H1 closes but H2 binds (Phase 2 fixes EAT-override but births stay
flat): v0.14 sweeps reproduction economics and/or extends the tick
budget. The ratchet then becomes "find the H2 axis that lets
foraging gains compound."

If H1 fails (Phase 1 / Phase 2 do not implicate `novelty_pleasure`):
re-evaluate whether `HedonismPolicy` predict-one-step + harness
scoring can express memory-driven behavior at all, before adding
representation #4.

## Phase 1 results — H1 and H2 both confirmed

Full write-up: [[docs/experiments/fear_hunger_v0.13_profile.md]].
Headline:

- **H1 confirmed mechanically.** Trace 1b (`ms0-md0.1`, food_ladder,
  seed=2, tick=11): `novelty_pleasure` on MOVE_EAST = 44.96 vs
  `eating_pleasure` on EAT = 17.68. Memory swayed argmax from EAT to
  MOVE_EAST on a hungry-on-food agent. Trace 1c (`ms0-md0.1`,
  tight_gradient, seed=2024, tick=39): EMA compounded to 680;
  `novelty_pleasure` dominated by ~33×. Agent at energy=2.0 walked off
  food. Trace 3 (sated, memory pointing east): without memory STAY
  wins; with memory MOVE_EAST wins —
  `anticipated_food_pleasure` silenced itself via its hunger gate;
  `novelty_pleasure` did not.
- **H2 confirmed independently.** 100 % of v0.12b winner births fell
  in ticks 0–49; **zero births in ticks 50–199**. Mem-off baseline
  showed the identical step-function distribution. Memory
  representation is not the late-stage cause; the ceiling is
  architectural (economics, crowding, or post-first-birth energy
  state).

Pre-registered branch: "`novelty_pleasure(MOVE_*) >> eating_pleasure(EAT)`
in trace 1 → H1 confirmed mechanically. Proceed to Phase 2 with the
hunger-gate fix." Branch fired; we proceeded.

## Phase 2 results — hunger-gate fix lands; EAT-overrides drop sharply

The wiring fix is one line in `core/valence.py:166`:

```python
# Before (v0.12)
novelty_pleasure = novelty_score * traits.novelty_drive

# After (v0.13)
novelty_pleasure = novelty_score * obs_before.hunger_level * traits.novelty_drive
```

That's the entire change to harness math. Plus 6 new tests pinning
the gating semantics + an updated v0.12 telemetry test that drains
energy before sweeping memory (so the gate is open). The v0.12
projection seam, telemetry plumbing, trait ranges, layouts,
reproduction economics, and tick budget are all unchanged.

### v0.13a tight_gradient

```
cell_id      births sw_b reqs food haz surv  mUp agUp rpt   dec  chg   rate
mem-off           1    1    1   10  23  1/8    0    0   7     0    0  0.000
ms0-md0.02        1    1    1    2  22  0/8  108   38   1  3194  160  0.050
ms0-md0.05        1    1    1    3  22  0/8  108   38   1  3206  154  0.048
ms0-md0.1         1    1    1    5  26  0/8  110   37   2  3240  130  0.040
ms0.5-md0.02      1    1    1    3  19  0/8  110   38   2  3211   88  0.027
ms0.5-md0.05      1    1    1    3  20  0/8  112   38   2  3211   88  0.027
ms0.5-md0.1       1    1    1    4  25  0/8  112   37   3  3207   88  0.027
ms1-md0.02        1    1    1    5  18  0/8  116   37   3  3204   31  0.010
ms1-md0.05        1    1    1    6  18  0/8  116   37   4  3216   31  0.010
ms1-md0.1         1    1    1    3  22  0/8  116   37   2  3160   18  0.006
```

`tight_gradient` is still 0/9 qualifiers — same as v0.11 and v0.12.
Births stay at 1 across all cells; the chamber is unreachable under
any current memory representation. But the substrate-regression vs
mem-off has narrowed: v0.12 had `food_events ∈ {0, 1, 1, 2, 1, 5, 2,
5, 5}` for the 9 memory cells; v0.13 has `{2, 3, 5, 3, 3, 4, 5, 6,
3}` — a 1.7–3× lift on the worst cells. `argmax_change_rate` is
also lower across the board (1.6–5.0 % vs v0.12's 1.1–5.8 %).

EAT-override transition counts on `ms0-md0.1` (the cell where v0.12
overrides clustered most densely):

```
v0.12: 84 EAT->MOVE_*  out of 171 swayed (49.1 %)
v0.13: 44 EAT->MOVE_*  out of 130 swayed (33.8 %)
```

A ~46 % drop in EAT-override count and a ~24 % drop in total swayed
decisions. Not eliminated — at fast EMA on tight_gradient, even mild
hunger keeps the gate partly open and tendencies still grow large
relative to `eating_pleasure`.

### v0.13b food_ladder

```
cell_id      births sw_b reqs food haz surv  mUp agUp rpt   dec  chg   rate
mem-off           5    4    5   28   0  0/8    0    0   7     0    0  0.000
ms0-md0.02        5    3    5   28  20  0/8  200   37   6  2956  295  0.100
ms0-md0.05        5    3    5   30  18  0/8  200   38   8  3077  305  0.099
ms0-md0.1         5    3    5   28  20  0/8  202   38   7  2991  264  0.088   ← winner
ms0.5-md0.02      4    3    4   32  11  0/8  214   38   9  3012  336  0.112
ms0.5-md0.05      4    3    4   32   7  0/8  212   38   9  3088  282  0.091
ms0.5-md0.1       4    3    4   30  12  0/8  216   38   9  3025  238  0.079
ms1-md0.02        5    4    5   30   0  0/8  212   39   8  3136  142  0.045
ms1-md0.05        5    4    5   30   0  0/8  214   39   9  3095  110  0.036
ms1-md0.1         5    4    5   31   0  0/8  220   39   9  3125   72  0.023
```

**The v0.12 regression at low memory_strength is gone.** Direct
comparison on births at the cells most affected by the EAT-override
pathology:

| cell | v0.12 births | v0.13 births |
|---|---:|---:|
| ms0-md0.02 | 3 | **5** |
| ms0-md0.05 | 3 | **5** |
| ms0-md0.1  | 3 | **5** |
| ms0.5-md0.02 | 3 | 4 |
| ms0.5-md0.05 | 3 | 4 |
| ms0.5-md0.1 | 2 | 4 |
| ms1-md0.02 | 4 | 5 |
| ms1-md0.05 | 5 | 5 |
| ms1-md0.1 | 5 | 5 |

Every cell at or above v0.12 baseline; ms0-* and ms1-* now match
the mem-off baseline of 5 births.

`select_winning_cell` picks **`ms0-md0.1`** under the v0.7b rule:
all 9 cells qualify, three reach `total_births=5` (ms0-md0.1,
ms1-md0.05, ms1-md0.1), tie-broken by Euclidean distance to the
SPEC-permissive memory anchor `(ms_min=0.0, md_max=0.1)`. ms0-md0.1
**is** the anchor (distance² = 0.0).

The v0.13b winner differs from v0.12b's (ms1-md0.1) — the gate
unblocked the fast-EMA cells. But the new winner does not exceed
baseline births (5 = 5). H2 binds the headline.

Action-transition profile of `ms1-md0.1` (v0.12 winner identity, for
comparison continuity):

```
v0.12: 102 swayed; EAT->MOVE_EAST = 5
v0.13:  72 swayed; EAT->MOVE_EAST = 0   ← eliminated
```

The largest transition class becomes `MOVE_WEST -> MOVE_EAST` (47),
which is the *desired* memory effect: an agent on the wrong side of
the chamber gets pulled back toward known food.

### Diagnosis

**H1 fix is working as designed.** The hunger-gate eliminates EAT
overrides at the v0.12 winner cell, halves them at the worst-case
fast-EMA cells, and unblocks every food_ladder cell that was
regressing in v0.12. Substrate metrics are maintained or improved.
`argmax_change_rate` drops on every cell.

**H2 still binds.** Total births still cap at the baseline 5 on
food_ladder; tight_gradient still produces 1 birth across all 9
cells. The substrate gains do not translate to extra births. The
by-tick birth distribution from Phase 1 already showed why: 100 %
of births fall in the first 50 ticks; founders reproduce once during
the energy-rich initial window and the surviving pool then never
reaches reproduction threshold again.

**Net read of v0.13:** the wiring fix was necessary and correct.
Memory's reward channel is no longer mis-scaled relative to its
peers. But fixing the wiring did not lift the births ceiling because
the binding constraint is reproduction economics / tick budget, not
memory representation. v0.14 should test that ceiling directly.

### Pre-registered failure → action mapping (Phase 2 outcomes)

The pre-registered branch that fired:

> **Cells qualify and match baseline births, EAT-override drops,
> births do not increase** → wiring was real but H2 is the binding
> ceiling. Pivot v0.14 to reproduction economics and/or tick budget.

food_ladder: 9/9 qualify, EAT-overrides eliminated at the
representative cell, births match (don't exceed) baseline.
tight_gradient: 0/9 qualify (births=1), but EAT-overrides dropped
46 %.

The "regression vs v0.12" branch did **not** fire on either chamber.
The "exceeds baseline births" branch did **not** fire either, exactly
as Phase 1 predicted via the birth-distribution histogram.

### What v0.13 confirms

- **The hunger-gate is the right intervention.** Profile predicted
  it; sweep validates it. EAT-override pattern that load-bore v0.12's
  maladaptive behavior is now substantially attenuated.
- **`novelty_pleasure` was structurally mis-scaled relative to
  `anticipated_food_pleasure`.** The same hunger-gate that was
  already on anticipated_food makes the memory channel symmetric.
  Should have been there from the start; v0.13 retro-fits it.
- **Substrate gains compound when the wiring is right.** v0.12's
  ms0-* cells were *worse* than baseline on births; v0.13's are
  *equal* to baseline. The wiring fix moves the floor.

### What v0.13 rules out

- *"The EAT-override pathology is unfixable without changing the
  representation."* — false. It's a wiring asymmetry, fully fixed by
  one line in valence.py.
- *"The substrate-up-births-flat ceiling is a symptom of memory
  representation."* — false. mem-off baseline shows the same
  step-function birth distribution; representation is not the late-
  stage cause.

## What v0.13 leaves open (the v0.14 hand-off)

1. **Reproduction economics or tick budget** — the binding ceiling.
   Three sub-questions:
   - Does extending `n_ticks=200 -> 500` (or 1000) produce a second
     birth wave? Trivial to test.
   - Does relaxing `tuned_reproduction_config(et=50, ec=35)` toward
     `et=40, ec=30` allow surviving agents to reproduce again?
   - Does post-first-birth energy distribution show all surviving
     agents below the reproduction threshold? Diagnostic histogram.
2. **Cell-exact memory under the v0.13 hunger-gate.** v0.10 showed
   cell-exact's substrate-up-births-flat pattern; the new gate may
   or may not change that. Worth a one-arm regression sweep.
3. **Per-cell-kind categorical memory** (the v0.12 ranking's
   option (2)) is still parked. Re-evaluate after the H2 question
   closes.
4. **`novelty_drive` semantic debt** — name still wrong (the channel
   rewards familiarity, not novelty). Pure refactor; defer to a
   cleanup slice that touches `core/traits.py` and `core/valence.py`
   together.

## What changed

- [[src/hedonism_harness/core/valence.py]] — one-line edit to
  `novelty_pleasure`: now multiplied by `obs_before.hunger_level`
  (line 166). 9-line block comment above it explains why and points
  at the v0.13 profile doc.
- [[tests/test_valence.py]] — 5 new tests pinning the gating
  semantics: zero when sated, linear scaling with hunger, gate uses
  obs_before not obs_after (mirror of anticipated_food_pleasure),
  identity at hunger=1.0 (regression-catch for an accidental gate
  removal), and the trace-3 fingerprint scenario.
- [[tests/test_action_aware_directional.py]] — one v0.12 test
  updated to drain agent energy before exercising the swayed-argmax
  path (the gate would silence memory on a sated agent — the
  test was unintentionally exercising both v0.12 and the now-fixed
  v0.13 pathology). Plus one new test asserting that a sated agent
  is NOT swayed under the new gate, to lock the v0.13 invariant in
  policy-level integration too.
- [[scripts/v0.13_profile.py]] — Phase 1 read-only profiler (shipped
  separately in `1e6308f`).
- [[docs/experiments/fear_hunger_v0.13_profile.md]] — Phase 1
  results (shipped separately in `1e6308f`).
- This document — Phase 2 results appended, status updated.

No changes to: `core/sensors.py`, `core/memory.py`, `core/actions.py`,
`policies/`, the projection seam, the trait master ranges, layouts,
reproduction economics, or any prior experiment's artifacts. v0.7..v0.12
sweeps with `memory_type` defaulting to `"cell_exact"` re-run
bit-identically when `traits.novelty_drive` produces zero memory
contribution (the cell-exact path's `novelty_score` is zero whenever
the agent is on a never-visited cell — verified via the existing
458-test suite, including the v0.7..v0.12 regression tests).

## Reproducing

Phase 1:

```bash
# Trace dump for the three pre-registered scenarios + by-tick birth
# distribution from existing v0.12 winner runs.
uv run python scripts/v0.13_profile.py
# wrote runs/fear-hunger-v0.13-profile/traces.md
```

Phase 2:

```bash
uv run python -c "
from pathlib import Path
from hedonism_harness.experiments.memory_grid import all_grid_cells, run_memory_grid

# v0.13a: tight_gradient under hunger-gated novelty_pleasure.
run_memory_grid(
    seeds=[1, 2, 3, 4, 5, 42, 100, 2024],
    runs_root=Path('runs'),
    batch_id='fear-hunger-v0.13a',
    n_ticks=200, n_founders=5,
    snapshot_tick=100, snapshot_seed=1,
    cells=all_grid_cells(layout_name='tight_gradient', memory_type='directional'),
)

# v0.13b: food_ladder under hunger-gated novelty_pleasure.
run_memory_grid(
    seeds=[1, 2, 3, 4, 5, 42, 100, 2024],
    runs_root=Path('runs'),
    batch_id='fear-hunger-v0.13b',
    n_ticks=200, n_founders=5,
    snapshot_tick=100, snapshot_seed=1,
    cells=all_grid_cells(layout_name='food_ladder', memory_type='directional'),
)
"
```

Expected diff scope: ~3-line change in [[src/hedonism_harness/core/valence.py]]
(hunger-gating on the `novelty_pleasure` line) + new
`scripts/v0.13_profile.py` (Phase 1) + new tests pinning the gating
behavior + the v0.13 doc updated post-run with results.
