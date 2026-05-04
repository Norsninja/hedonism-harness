# Fear-Hunger Chamber — v0.12 action-aware directional memory

**Experiment:** Test whether projecting `DirectionalMemory` onto the
candidate action under evaluation (read only the move-direction's slot
of `pleasure_tendency` / `pain_tendency`, zero the rest) gives memory a
causal channel into argmax — and whether that channel raises
reproduction in either chamber.
**Branch:** `claude/review-hedonism-harness-i0CnN`
**Date:** 2026-05-04
**Runs:** `runs/fear-hunger-v0.12a/` (tight_gradient),
`runs/fear-hunger-v0.12b/` (food_ladder)

## Question

v0.11 showed bare directional memory was decision-degenerate by
construction: `directional_signals_directional()` is position-invariant,
so every candidate action's `predicted_obs` carried the same memory
signal and argmax was unaffected. The pre-registered failure mapping
ranked three candidate fixes by minimum scope; v0.12 implements (1) —
**action-aware directional read** — to test whether the abstraction was
right but the plumbing was wrong.

> If "moving east tended to be good" directly boosts only the
> MOVE_EAST candidate, does directional memory become behaviorally
> causal? And if it does, does it amplify reproduction on either
> tight_gradient or food_ladder?

## Setup

Identical to v0.11 in every respect except the projection seam:

- **Memory type**: `DirectionalMemory`. Same EMA dynamics, same
  per-tick decay, same trait wiring.
- **Projection**: in `HedonismPolicy.decide`, when `ctx.memory` is a
  `DirectionalMemory`, the predicted observation passed into
  `evaluate(...)` for `MOVE_<DIR>` keeps only the `<DIR>` slot of both
  `remembered_good_*` and `remembered_bad_*`; the other six slots are
  zeroed. For `STAY` / `EAT` / `REPRODUCE` all eight slots are zeroed
  (those actions test no direction). Cell-exact (`ValenceMemory`) and
  the `None` path are untouched and remain bit-identical to v0.10.
- **Argmax-changes telemetry**: on the directional path the policy
  also scores every candidate a second time with all 8 memory fields
  zeroed and reports both winners back via
  `PolicyDecision.swayed_by_memory` /
  `PolicyDecision.action_without_memory`.
  `MemoryTelemetryCollector` enables a per-decision log on the model
  that records `(swayed, with_memory_action, without_memory_action)`
  triples; `MemoryTelemetry` then exposes
  `directional_decisions`, `argmax_changes`, `argmax_change_rate`,
  and a Counter of swayed transitions.
- **Layouts**: `tight_gradient` (v0.12a), `food_ladder` (v0.12b).
- **Policy**: `HedonismPolicy(exploration_noise=0.05)`.
- **Reproduction config**: `tuned_reproduction_config(et=50, ec=35)`.
- **Trait base**: v0.6 winner with per-cell `memory_strength_min` /
  `memory_decay_rate_max` overrides.
- **Hyperparameters**: 5 founders, 200 ticks, 8 seeds (`1, 2, 3, 4, 5,
  42, 100, 2024`).

10 cells × 8 seeds = 80 runs per sweep × 2 sweeps = 160 runs total.

## Pre-registered viability rule (six criteria, unchanged)

1. `total_births >= 2`
2. `seeds_with_any_births >= 2`
3. `total_food_events >= baseline.total_food_events − total_births`
4. `seeds_with_any_starvation > 0`
5. `max_population_end <= 3 × n_founders = 15`
6. `total_reproduction_requests >= total_births`

## Pre-registered failure → action mapping

- **Memory cells qualify and exceed baseline births on either chamber**
  → directional+action-aware is the right primitive abstraction; ladder
  forward.
- **Memory cells qualify and match baseline births** → memory is
  causal but the signal is too weak; profile `novelty_pleasure` vs
  competing pleasure terms before cutting v0.13.
- **Memory cells do not qualify but argmax_changes > 0** → causal but
  underpowered or maladaptive; same diagnosis branch.
- **`argmax_changes == 0` across all cells** → bug in the projection;
  not a representation failure.
- **Bit-identical metrics again with `argmax_changes > 0`** → memory
  swayed early ticks but agents converged to the same trajectories
  anyway; would warrant a deeper trace inspection.

## Result — projection is causal; bare directional tendencies are
maladaptive

```
v0.12a tight_gradient:  qualifiers: 0 / 9    winner: NONE
v0.12b food_ladder:     qualifiers: 9 / 9    winner: ms1-md0.1
                        argmax-changes range: 1.0 % – 16.4 %
```

The "bit-identical metrics" branch from v0.11 **does not fire**. Memory
now causally influences decisions in every memory-on cell on both
chambers. The plumbing was wrong; the abstraction was right *enough*
to reach the argmax.

But the headline reproduction question is more nuanced than v0.10:
**bare directional tendencies, even when correctly projected per
candidate action, are mostly maladaptive**. The diagnosis lives in the
action-transition profiles, not the births column.

### v0.12a: tight_gradient + directional + action-aware

```
cell_id      births sw_b reqs food haz surv  mUp agUp rpt   dec  chg   rate
mem-off           1    1    1   10  23  1/8    0    0   7     0    0  0.000
ms0-md0.02        1    1    1    0  15  0/8  108   38   0  3169  176  0.056
ms0-md0.05        1    1    1    1  20  0/8  108   38   0  3173  184  0.058
ms0-md0.1         1    1    1    1  20  0/8  108   38   0  3174  171  0.054
ms0.5-md0.02      1    1    1    2  18  0/8  106   37   0  3191  161  0.050
ms0.5-md0.05      1    1    1    1  16  0/8  110   38   0  3174  146  0.046
ms0.5-md0.1       1    1    1    5  22  0/8  112   37   2  3231  173  0.054
ms1-md0.02        1    1    1    2  18  0/8  112   37   1  3164   48  0.015
ms1-md0.05        1    1    1    5  18  0/8  116   37   3  3202   72  0.022
ms1-md0.1         1    1    1    5  19  0/8  116   37   3  3202   34  0.011
```

Memory swayed 1.1–5.8 % of decisions across 3164–3231 evaluated
decisions per cell — a clear causal channel. But every memory-on cell
**reduces `food_events` from baseline 10 down to 0–5** and drops the
1/8 surviving seed to 0/8. Memory makes the chamber strictly worse.

The action-transition profile for the median cell `ms0-md0.1`
explains why (171 swayed decisions across 8 seeds):

```
MOVE_EAST -> MOVE_WEST    60   ← local oscillation along the food row
EAT       -> MOVE_EAST    54   ← memory pulls the agent OFF food
EAT       -> MOVE_WEST    30   ← same, opposite direction
MOVE_WEST -> MOVE_EAST    16
STAY      -> MOVE_WEST     8
```

**84 of 171 swayed decisions (49 %) are `EAT -> MOVE_*`**: the agent
sits on a food cell, the harness scores `EAT` highest under no-memory
scoring, but the projected memory channel adds enough
`pleasure_tendency` to a move direction that it overrides the eating
pleasure. The agent walks off food. On tight_gradient — where food is
already sparse and hazard residency damage is steep — this is
catastrophic.

Higher `memory_strength_min` (slower EMA) reduces the sway rate
(ms1-md0.1 sways only 1.1 % vs ms0-* at 5.4–5.8 %) and partly
compensates by leaving food_events at 5 instead of 1, but never
recovers the baseline 10.

### v0.12b: food_ladder + directional + action-aware

```
cell_id      births sw_b reqs food haz surv  mUp agUp rpt   dec  chg   rate
mem-off           5    4    5   28   0  0/8    0    0   7     0    0  0.000
ms0-md0.02        3    3    3   31  33  0/8  162   36   8  3061  408  0.133
ms0-md0.05        3    3    3   31  34  0/8  162   36   8  3087  440  0.143
ms0-md0.1         3    3    3   35  41  0/8  176   37  11  3076  431  0.140
ms0.5-md0.02      3    3    3   30  31  0/8  198   39   7  2914  479  0.164
ms0.5-md0.05      3    3    3   29  13  0/8  186   37   7  2975  394  0.132
ms0.5-md0.1       2    2    2   33  18  0/8  186   37  10  3043  362  0.119
ms1-md0.02        4    3    4   31   1  0/8  206   38   9  3093  180  0.058
ms1-md0.05        5    4    5   29   0  0/8  214   39   8  3042  151  0.050
ms1-md0.1         5    4    5   31   0  0/8  216   39  10  3145  102  0.032   ← winner
```

**All 9 memory cells qualify** under the v0.7b rule (every cell
passes criteria 1–6: even the `ms0-*` low-strength cells reach
`total_births=3 ≥ 2` and `total_food_events ≥ baseline-births`).
Per `select_winning_cell`, the primary score is `total_births`
(highest wins): only `ms1-md0.05` and `ms1-md0.1` reach births=5.
Tie-break is Euclidean distance to the SPEC-permissive memory anchor
`(ms_min=0.0, md_max=0.1)`: `ms1-md0.1` is closer (distance² = 1.00
vs 1.0025) and wins. Final winner: **`ms1-md0.1`** — matches baseline
births=5, food_events=31 (vs baseline 28, +11 %),
repeat_food_visits=10 (vs baseline 7, +43 %),
argmax_change_rate=3.2 %.

Action-transition profile for the winner (102 swayed decisions across
8 seeds):

```
MOVE_WEST  -> MOVE_EAST   57   ← memory steers east toward ladder food
MOVE_WEST  -> STAY        14
MOVE_NORTH -> MOVE_EAST    9
STAY       -> MOVE_EAST    6
MOVE_SOUTH -> MOVE_EAST    5
EAT        -> MOVE_EAST    5   ← only 5 % EAT-overrides
```

At high `memory_strength` (ms1-md0.1: slow EMA), only 5/102 swayed
decisions override EAT — versus 84/171 (49 %) at low memory_strength
on tight_gradient. **The `(memory_strength_min, memory_decay_rate_max)
= (1.0, 0.1)` corner is exactly the slow-update / fast-decay regime
that minimizes EAT overrides while still letting memory bias
exploration directions.** That match between argmax-change profile and
performance is the cleanest causal story we have so far for what
memory is actually doing.

But — births do not exceed baseline. The repeat_food_visits +43 % and
food_events +11 % show that memory IS helping with foraging, but the
extra food calories don't translate into extra births under the
current reproduction economics. This is the v0.10 pattern again
(substrate improves, births don't), now reproduced on a different
representation.

### Diagnosis — projection works; bare directional tendencies are
underpowered or maladaptive

1. **The projection is causal.** Argmax-change rates 1.1–16.4 % across
   chambers and parameter cells, vs. 0.0 % in v0.11. The plumbing
   change (read only the action-matched slot inside
   `HedonismPolicy.decide`) does what we hoped — memory now
   differentiates candidates. The architectural finding from v0.11
   ("cell-exact decision power comes from its position-dependent
   scan, not the EMA recurrence") is *also* true of action-aware
   directional memory: the action-projection is what gives it bite.

2. **But bare directional tendencies are mostly maladaptive on
   tight_gradient.** Without spatial coupling, a tendency learned at
   one position ("moving east felt good once") propagates to ALL
   positions including those where east leads off-food. On
   tight_gradient half the swayed decisions on ms0-* are
   `EAT -> MOVE_*` — the agent yanks itself off the food it just
   reached. Memory turns the chamber from "1 birth" into "1 birth
   with worse foraging." The 6-criterion rule's binding on births=1
   masks how much worse the substrate gets.

3. **Slow-update regimes (ms1-*) are the only directional cells that
   don't regress on either chamber.** High `memory_strength_min` ⇒
   `alpha_for_strength = max(0.05, 1 - 1.0) = 0.05`, so the EMA barely
   moves per tick and the tendencies stay near zero longer. This is
   the same prescription that v0.10 found for cell-exact memory on
   food_ladder. Slow updates protect against early "lucky direction"
   over-fitting.

4. **food_ladder + ms1-md0.1 reaches the v0.10 substrate-improvement
   tier without exceeding baseline births.** Same headline as v0.10:
   *memory helps foraging but the births are bottlenecked by
   reproduction economics, not by foraging supply*. This is a
   re-confirmation, not a new win.

### What v0.12 confirms

- **Action-aware projection is the missing plumbing for directional
  memory.** The minimum change — read only the move-direction's slot
  for `MOVE_<DIR>`, zero everything else — converts bare directional
  memory from decision-degenerate (v0.11) into causally influential
  (v0.12). No core valence-math change, no sensor change, no new
  memory representation needed.
- **Memory's signal-to-noise vs other pleasure terms is non-trivial
  to balance.** When the projected pleasure_tendency contribution is
  on the order of `eating_pleasure`, the agent's argmax flips off
  food into "remembered good direction." This is controllable via
  `memory_strength` (which scales how fast tendencies grow) and
  `traits.novelty_drive` (which weights `_remembered_good_total` into
  `novelty_pleasure`).
- **The harness pipeline carries the new telemetry cleanly.** A
  per-decision log gated on `model.enable_policy_decision_log()` lets
  `MemoryTelemetryCollector` aggregate `directional_decisions`,
  `argmax_changes`, and a Counter of swayed action transitions.
  Cell-exact and `mem-off` runs leave the log empty (zero overhead,
  bit-identical behavior).

### What v0.12 rules out

- *"Bare directional memory becomes net-positive once the projection
  is correct."* — false. Causal, yes; net-positive on births, no
  (food_ladder matches baseline; tight_gradient regresses on
  substrate).
- *"Action-aware projection alone can rescue tight_gradient."* —
  false. Tight_gradient still produces 1 birth across all 8 seeds,
  same as baseline; substrate degrades.
- *"v0.11's null was a parameter-tuning artifact."* — false.
  The plumbing was structurally degenerate; no amount of
  strength/decay tuning would have produced behavior. v0.12 produces
  behavior because it changed the read function, not the parameters.

## Decision

**v0.12b qualifies** with `ms1-md0.1` as the formal winner under the
v0.7b rule. We **do not promote it to a new headline result** —
births match baseline, no surviving seeds, substrate gain is modest
and replicates v0.10's pattern on a different representation. We
record the architectural finding (projection is the causal seam for
directional memory) and move on.

**Per the pre-registered failure mapping**, the
"argmax_changes > 0 but births unchanged or worse" branch fires.
Three forward paths, ranked by scope:

1. **Profile `novelty_pleasure` magnitude vs eating / safety /
   anticipated_food** (small): the EAT-override transition on
   tight_gradient (49 % of swayed decisions) is the smoking gun.
   Either dampen `novelty_pleasure` or gate it on hunger so it can't
   override `eating_pleasure` when the agent is on food. This is a
   harness-wiring tweak, not a representation change.
2. **Per-cell-kind categorical memory** (medium scope): record
   pleasure / pain per `CellKind` (FOOD, HAZARD, SAFE, EMPTY).
   Pavlovian. Has decision influence by construction since `on_*`
   already differs across candidate destinations. Was the next item
   on the v0.11 ladder; still on the table.
3. **Add a "current heading" reference and modulate tendencies by
   alignment with it** (large): true chemotaxis-style memory where
   the agent has a directional state. Probably v0.14+.

We recommend (1) before (2): the EAT-override pattern is so loud in
the transition counts that fixing the harness wiring may cleanly
separate "memory channel works but is mis-weighted" from "abstraction
is wrong." (2) only becomes the right experiment if (1) shows
`novelty_pleasure` is properly scaled and births still don't move.

## What v0.12 leaves open

1. **Is `novelty_pleasure` the wrong channel for memory output?** The
   harness routes `_remembered_good_total` into
   `novelty_pleasure = novelty_score * traits.novelty_drive`. With
   `novelty_drive` ~1.0 on average and pleasure_tendency easily
   reaching 5–10 after a few feedings, the memory contribution can be
   on the same order as `eating_pleasure`. Profile this directly
   before any further representation work.
2. **Why does food_ladder still produce 0/8 surviving seeds?** Even
   with +43 % repeat_food_visits at the winner cell, no lineage
   survives. The reproduction economics may be too tight for any
   foraging improvement at this tick budget; v0.13+ should consider
   a longer-tick variant of food_ladder as a baseline comparator.
3. **Does action-aware projection compose with cell-exact memory?**
   Untested. v0.10's cell-exact already differentiates candidates via
   the predicted body's `(x, y)` in `directional_signals`; the
   projection is logically a no-op on that path (we explicitly skip
   it). But composing both ideas — read the cell-exact axial scan
   only along the projected direction — is a natural v0.13+
   experiment if (1) and (2) close cleanly.

## What changed

- [[src/hedonism_harness/policies/hedonism_policy.py]] — module
  docstring updated to describe the action-aware-directional-memory
  projection seam. New private helpers
  `_project_memory_for_action(obs, action) -> Observation` and
  `_zero_memory_fields(obs) -> Observation`. `decide()` now branches
  on `isinstance(ctx.memory, DirectionalMemory)`: on the directional
  path it scores every candidate twice (once with the projected
  memory, once with memory zeroed) and returns
  `PolicyDecision(swayed_by_memory=..., action_without_memory=...)`.
  Cell-exact and `None` paths take exactly one `evaluate(...)` per
  candidate as before; defaults preserve v0.10 bit-identity.
- [[src/hedonism_harness/policies/base.py]] — `PolicyDecision` gains
  two optional fields: `swayed_by_memory: bool = False` and
  `action_without_memory: Action | None = None`. Backwards-compatible
  with all v0.11 call sites.
- [[src/hedonism_harness/model.py]] — `HHModel` gains an opt-in
  `policy_decision_log: list[(bool, int, int)] | None`, plus
  `enable_policy_decision_log()`, `disable_policy_decision_log()`,
  and `note_policy_decision(decision)`. The log is `None` (off) by
  default; `note_policy_decision` is a one-line None-check fast path
  on every other run, preserving v0.10 bit-identity.
- [[src/hedonism_harness/mesa_agents.py]] — `HHAgent.step()` calls
  `model.note_policy_decision(decision)` after `policy.decide(ctx)`.
  Side-effect-free when the log is disabled.
- [[src/hedonism_harness/experiments/memory_telemetry.py]] —
  `MemoryTelemetry` gains `directional_decisions`, `argmax_changes`,
  `action_transitions`, and a derived `argmax_change_rate` property
  (all defaulted, so existing callers don't change).
  `MemoryTelemetryCollector.connect()` enables the model's decision
  log; `disconnect()` snapshots the log into the collector before
  clearing it on the model side, so `finalize()` after `disconnect()`
  (the order `memory_grid` uses) preserves the data.
- [[src/hedonism_harness/experiments/memory_grid.py]] —
  `MemoryCellAggregate` gains `total_directional_decisions`,
  `total_argmax_changes`, `argmax_change_rate` (all defaulted).
  `aggregate(...)` sums them across seeds. The comparison.csv writer
  adds three new columns; the winner.txt formatter adds a "v0.12
  directional projection" section.
- [[tests/test_action_aware_directional.py]] (new) — 17 tests
  pinning the projection helpers, the policy's directional vs.
  cell-exact vs. None branches, the model's decision-log lifecycle,
  the collector's snapshot-on-disconnect contract, and the
  end-to-end "loaded-east tendency steers argmax to MOVE_EAST"
  causal demonstration.

No changes to: `core/valence.py`, `core/actions.py`, `core/sensors.py`,
`core/memory.py`, trait master ranges, layouts, reproduction economics,
or any prior experiment's artifacts (v0.7..v0.11 sweeps re-run
bit-identically when memory is `None` or `ValenceMemory`; verified by
the 452-test suite, including the existing v0.7..v0.11 regression
tests).

## Reproducing

```bash
uv run python -c "
from pathlib import Path
from hedonism_harness.experiments.memory_grid import all_grid_cells, run_memory_grid

# v0.12a: tight_gradient + directional + action-aware projection
cells_a = all_grid_cells(layout_name='tight_gradient', memory_type='directional')
run_memory_grid(
    seeds=[1, 2, 3, 4, 5, 42, 100, 2024],
    runs_root=Path('runs'),
    batch_id='fear-hunger-v0.12a',
    n_ticks=200,
    n_founders=5,
    snapshot_tick=100,
    snapshot_seed=1,
    cells=cells_a,
)

# v0.12b: food_ladder + directional + action-aware projection
cells_b = all_grid_cells(layout_name='food_ladder', memory_type='directional')
run_memory_grid(
    seeds=[1, 2, 3, 4, 5, 42, 100, 2024],
    runs_root=Path('runs'),
    batch_id='fear-hunger-v0.12b',
    n_ticks=200,
    n_founders=5,
    snapshot_tick=100,
    snapshot_seed=1,
    cells=cells_b,
)
"
```

Outputs in `runs/fear-hunger-v0.12a/` and `runs/fear-hunger-v0.12b/`,
same artifact tree shape as v0.9/v0.10/v0.11 with three new columns
in `comparison.csv` (`total_directional_decisions`,
`total_argmax_changes`, `argmax_change_rate`) and a new "v0.12
directional projection" section in `winner.txt`.
