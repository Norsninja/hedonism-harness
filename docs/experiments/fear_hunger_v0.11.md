# Fear-Hunger Chamber — v0.11 directional-gradient memory

**Experiment:** Test whether a chemotaxis-style directional-gradient memory
representation (4-vector `pleasure_tendency[N,S,E,W]` + `pain_tendency`,
updated only on movement) raises reproduction in either the hard
`tight_gradient` chamber or the permissive `food_ladder` chamber.
**Branch:** `claude/v0.11-directional-memory`
**Date:** 2026-05-04
**Runs:** `runs/fear-hunger-v0.11a/` (tight_gradient), `runs/fear-hunger-v0.11b/` (food_ladder)

## Question

v0.10's pre-registered failure-mapping branch fired: "1+ memory cells
qualify but match baseline births" → cell-exact `pleasure_ema` is at the
edge of usefulness; representation is the next bottleneck. v0.11 tests
the hypothesis that an alternative representation — directional gradient
memory, the smallest representation that genuinely changes the
abstraction (not just precision) and matches bacterial chemotaxis —
amplifies reproduction where cell-exact could not.

> Holding everything else fixed, does directional-gradient memory
> raise total_births on tight_gradient or food_ladder?

The test is structured as two sweeps mirroring the v0.9/v0.10 pattern:

- **v0.11a**: directional memory on tight_gradient (the hard problem)
- **v0.11b**: directional memory on food_ladder (the positive control)

## Setup

Identical to v0.9/v0.10 in every respect except the memory representation:

- **Memory type**: `DirectionalMemory` (new in v0.11). Two 4-vectors —
  `pleasure_tendency` and `pain_tendency` — indexed by direction
  (N, S, E, W). Updated only on movement: when the agent moves direction
  D and experiences pleasure P, pain Q, the slot D absorbs (P, Q) via
  the same EMA recurrence as `ValenceMemory` (`alpha = alpha_for_strength
  (traits.memory_strength)`). Per-tick decay (`traits.memory_decay_rate`)
  applies via the SPEC §13.3 plumbing wired in v0.9b.
- **Layout**: `tight_gradient` (v0.11a) / `food_ladder` (v0.11b).
- **Policy**: `HedonismPolicy(exploration_noise=0.05)` (held fixed).
- **Reproduction config**: `tuned_reproduction_config(et=50, ec=35)`
  (frozen since v0.7).
- **Trait base**: v0.6 winner with `memory_strength` and
  `memory_decay_rate` overrides per cell. Same `memory_trait_config`
  factory as v0.9/v0.10.
- **Hyperparameters**: 5 founders, 200 ticks, 8 seeds (`1, 2, 3, 4, 5,
  42, 100, 2024`).
- **Independent variables**: same axes as v0.9/v0.10.

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
  → directional memory is the right primitive abstraction.
- **Memory cells qualify but match baseline births** (the v0.10 pattern,
  but on the new representation) → directional representation is no
  better than cell-exact at amplifying births. v0.12 tests the next
  abstraction (spatially-projected directional memory, or per-cell-kind
  categorical).
- **Memory cells do not qualify and produce no behavioral change** →
  the directional implementation as designed has no decision-influencing
  signal. Diagnose and either fix the implementation or pivot.
- **Memory cells produce bit-identical metrics to mem-off baseline
  across all parameter combinations** → strong diagnostic that the
  representation is decision-degenerate.

## Result — directional memory has zero decision-influence

```
v0.11a tight_gradient:  qualifiers: 0 / 9    winner: NONE
v0.11b food_ladder:     qualifiers: 9 / 9    winner: ms0-md0.1   (degenerate tie)
```

### v0.11a: tight_gradient + directional

```
cell_id      births sw_b reqs food haz surv  mUp agUp rpt
mem-off           1    1    1   10  23  1/8    0    0   7   ← baseline
ms0-md0.02        1    1    1   10  23  1/8  122   37   7
ms0-md0.05        1    1    1   10  23  1/8  122   37   7
ms0-md0.1         1    1    1   10  23  1/8  122   37   7
ms0.5-md0.02      1    1    1   10  23  1/8  122   37   7
ms0.5-md0.05      1    1    1   10  23  1/8  122   37   7
ms0.5-md0.1       1    1    1   10  23  1/8  122   37   7
ms1-md0.02        1    1    1   10  23  1/8  122   37   7
ms1-md0.05        1    1    1   10  23  1/8  122   37   7
ms1-md0.1         1    1    1   10  23  1/8  122   37   7
```

### v0.11b: food_ladder + directional

```
cell_id      births sw_b reqs food haz surv  mUp agUp rpt
mem-off           5    4    5   28   0  0/8    0    0   7   ← baseline
ms0-md0.02        5    4    5   28   0  0/8  214   39   7
ms0-md0.05        5    4    5   28   0  0/8  214   39   7
ms0-md0.1         5    4    5   28   0  0/8  214   39   7   ← formal winner
ms0.5-md0.02      5    4    5   28   0  0/8  212   39   7
ms0.5-md0.05      5    4    5   28   0  0/8  212   39   7
ms0.5-md0.1       5    4    5   28   0  0/8  212   39   7
ms1-md0.02        5    4    5   28   0  0/8  212   39   7
ms1-md0.05        5    4    5   28   0  0/8  212   39   7
ms1-md0.1         5    4    5   28   0  0/8  212   39   7
```

`mUp` = total_memory_updates (count of nonzero direction slots; max 8
per agent), `agUp` = total_agents_with_memory_updates,
`rpt` = total_repeat_food_visits.

The pre-registered "memory cells produce bit-identical metrics to
mem-off baseline across all parameter combinations" branch fires.
Memory is mechanically active (`mUp` 122–214, `agUp` 37–39 per cell)
but **every memory configuration produces identical headline metrics
to the baseline** in both chambers and across all 80 runs per sweep.

The v0.11b "winner" `ms0-md0.1` is a tie-break artifact: 9 memory
cells all qualify by matching baseline (births=5, sw_b=4, food=28); the
tie-break selects the cell closest to SPEC-permissive memory. The
qualification is structurally degenerate — none of the 9 cells exceeds
baseline on any tracked metric.

### Diagnosis — directional memory as implemented is decision-degenerate

The data is sharper than a typical experiment: all 9 memory cells in
each sweep produce bit-identical metrics across all 8 seeds. That
level of identity is not statistical noise — it is a structural
property of the implementation. The mechanism:

1. `directional_signals_directional(memory)` returns the four
   `pleasure_tendency` slots and four `pain_tendency` slots **as is**,
   with no dependence on the agent's position. Compare to the
   cell-exact `directional_signals(memory, x, y, radius)`, which scans
   the `pleasure_ema` array along each cardinal ray *starting at*
   `(x, y)` — different positions produce different signal totals,
   which is what gives cell-exact memory its decision-influencing
   power.

2. The `HedonismPolicy` evaluates each candidate action by calling
   `observe(world, predicted_body, body_config, memory)` for the
   post-action state. For DirectionalMemory, every `predicted_body`
   produces the *same* `remembered_good_*` / `remembered_bad_*`
   readings — because the directional signals don't depend on
   `predicted_body.x/y`.

3. The valence harness adds these constants to `predicted_hazard_risk`
   (feeding fear) and `novelty_pleasure` (feeding pleasure). Adding
   the same constant to every candidate action's predicted total
   does not change the argmax. The agent's choices are unaffected by
   memory state.

4. Memory state still updates correctly (when the agent moves, the
   move-direction's slot absorbs the breakdown's pleasure/pain via
   EMA — confirmed by `mUp` / `agUp` non-zero readings). The state
   just has no causal path back to behavior.

This is an architectural property of *bare* directional memory, not a
parameter-tuning issue. Sweeping `memory_strength_min` or
`memory_decay_rate_max` cannot rescue a representation that doesn't
differentiate candidate actions in the first place.

### What v0.11 confirms

1. **Cell-exact memory's decision influence comes from its position-
   dependent scan, not from the EMA recurrence.** Replacing the
   spatial map with 4-vector tendencies removes the position-dependence
   and silences the memory channel — but the EMA dynamics are
   identical between the two representations. The "interesting" part
   of cell-exact memory was the spatial-scan readout, not the
   accumulator.
2. **Directional memory needs spatial coupling to bite.** A primitive
   chemotaxis-style learner needs *some* way to map "I learned moving
   east is good" into "MOVE_EAST is more attractive than MOVE_WEST
   right now." Either the memory's read function must be action-aware
   (read only the slot matching the predicted move direction), or
   the agent needs a "current heading" reference that lets the
   tendencies project onto candidate actions.
3. **The harness pipeline supports memory-type dispatch cleanly.**
   The `memory_type` axis on `FounderSpec` / `MemoryCell` /
   `run_chamber` / `all_grid_cells` works end-to-end; the dispatch
   chain (sensor read, agent step update, agent decay, model spawn,
   child spawn) flows through `isinstance` checks at each junction
   without conflating the two memory types. v0.7/v0.7b/v0.8/v0.9/v0.10
   sweeps remain bit-identical (defaulting to `memory_type="cell_exact"`).

### What v0.11 rules out

- *"Bare directional memory amplifies reproduction in tight_gradient."*
  — false. No behavioral change from baseline at all.
- *"Bare directional memory amplifies reproduction in food_ladder."*
  — false. Same as baseline across all 9 parameter cells.
- *"Memory parameter tuning can rescue any representation."* — false.
  Some representations are decision-degenerate by construction; no
  amount of strength/decay tuning produces behavior.

## Decision

**No formal v0.11 winner is meaningful.** The v0.11b tie-break
selection of `ms0-md0.1` is a syntactic artifact of the criterion
rule firing on 9 baseline-matching cells; we explicitly do not promote
it. Instead, v0.11 records a clean diagnostic finding:

> Bare directional-gradient memory as implemented (4-vector tendencies
> read without spatial coupling) provides zero decision-influencing
> signal under HedonismPolicy + the current valence harness. The
> representation needs either an action-aware read function or
> spatial projection to affect behavior.

**Per the pre-registered failure mapping**, the "memory cells produce
bit-identical metrics" branch fires. v0.12 should test a representation
that fixes the position-coupling gap. Three candidate approaches,
ranked by minimum scope:

1. **Action-aware directional read** (smallest change): in the policy
   or sensor, when evaluating MOVE_X, return only the X slot of
   `pleasure_tendency` / `pain_tendency` instead of all four. Requires
   exposing the candidate action to the read path or projecting the
   move-direction onto the observation. Tests whether the *abstraction*
   was right but the *plumbing* was wrong.
2. **Per-cell-kind categorical memory** (medium scope): record valence
   per `CellKind` (FOOD, HAZARD, SAFE, EMPTY) — Pavlovian associative
   learning. Since the `on_*` sensor fields already differ across
   candidate actions' destinations, this naturally has decision
   influence. Compact (3–4 floats per agent).
3. **Position-projected directional memory** (largest scope): give
   directional memory access to a spatial reference (e.g., cell-kind
   gradient at the agent's current position) so tendencies modulate
   based on environmental structure. Probably v0.13+ if v0.12 also
   doesn't bite.

## What v0.11 leaves open

1. **Is the cell-exact-memory result from v0.9/v0.10 the *only* useful
   memory pattern under HedonismPolicy?** Possibly. The behavioral
   improvements at `ms1-md0.1` on food_ladder (v0.10) come from the
   spatial scan, not the EMA dynamics. If no alternative representation
   produces decision influence in v0.12, the project may need to revisit
   policy structure (predict-one-step + harness scoring) before adding
   more memory abstractions.
2. **Could a stateful "recent-heading" memory replace position
   coupling?** A vector indexed by the agent's recent move direction
   could approximate "what direction am I currently betting on?" This
   is a v0.13+ design.
3. **Is novelty_pleasure the right channel for memory output?** The
   valence harness routes `_remembered_good_total` into
   `novelty_pleasure = novelty_score * traits.novelty_drive`. With
   ``traits.novelty_drive`` averaging ~1.0 (SPEC default), memory's
   signal-to-noise vs other pleasure terms (eating, safety, anticipated
   food) may be too weak to influence decisions even when the signal
   IS position-dependent. Worth profiling in v0.12.

## What changed

- [[src/hedonism_harness/core/memory.py]] — new `DirectionalMemory`
  dataclass with `pleasure_tendency` / `pain_tendency` (4-vectors);
  helper functions `make_directional_memory`, `update_directional`,
  `decay_directional`, `directional_signals_directional`. Module
  docstring updated with comparison to cell-exact `ValenceMemory`.
  Index convention: `(north, south, east, west) = (0, 1, 2, 3)`.
- [[src/hedonism_harness/core/sensors.py]] — `_read_memory_directional`
  now dispatches on memory type: `ValenceMemory` → existing axial scan;
  `DirectionalMemory` → direct 4-vector read; `None` → zeros (unchanged).
- [[src/hedonism_harness/mesa_agents.py]] — `HHAgent.step()` dispatches
  the memory update on type (cell-exact uses `update_at(memory, x, y,
  ...)`, directional uses `update_directional(memory, dx, dy, ...)`
  with displacement computed from old/new body position).
  `apply_memory_decay()` dispatches `decay_all` vs `decay_directional`.
- [[src/hedonism_harness/model.py]] — `FounderSpec` gains `memory_type`
  field (`"cell_exact"` default keeps v0.9/v0.10 callers bit-identical).
  `_spawn_founder` and `_process_birth_queue` dispatch via
  `_make_memory_for_spec` / `isinstance(parent.memory, ...)`.
- [[src/hedonism_harness/experiments/fear_hunger_chamber.py]] —
  `run_chamber` gains `memory_type` kwarg threaded into `FounderSpec`.
- [[src/hedonism_harness/experiments/memory_grid.py]] — `MemoryCell`
  gains `memory_type` field; `all_grid_cells` and `baseline_cell`
  accept `memory_type=` kwarg; driver threads to `run_chamber`.
- [[src/hedonism_harness/experiments/memory_telemetry.py]] —
  `MemoryTelemetryCollector.observe_tick` dispatches on memory type;
  for `DirectionalMemory`, "activity" is the count of nonzero direction
  slots (max 8 per agent), used as a sanity proxy distinct from the
  cell-exact `visits.sum()` interpretation.
- [[tests/test_directional_memory.py]] (new) — 17 tests pinning
  construction, cardinal dispatch, EMA dynamics, decay, signal
  read-out (with negative-value clamping), sensor integration via
  `observe`, end-to-end dispatch via `model.step` (update + decay both
  fire), and `FounderSpec` validation of `memory_type` strings.
- [[tests/test_memory_grid.py]] — 5 new tests pinning the
  `memory_type` parameterization on the grid driver: default keeps
  cell-exact, `directional` selection works end-to-end, baseline
  records type, `run_chamber` dispatch produces the right memory
  class on founders.

No changes to: `core/valence.py`, `core/actions.py`, `core/reproduction.py`,
trait master ranges, layouts, reproduction economics, or any prior
experiment's artifacts (v0.7/v0.7b/v0.8/v0.9/v0.10 sweeps re-run
bit-identically when `memory_type` defaults to `"cell_exact"`).

## Reproducing

```bash
uv run python -c "
from pathlib import Path
from hedonism_harness.experiments.memory_grid import all_grid_cells, run_memory_grid

# v0.11a: tight_gradient + directional
cells_a = all_grid_cells(layout_name='tight_gradient', memory_type='directional')
run_memory_grid(
    seeds=[1, 2, 3, 4, 5, 42, 100, 2024],
    runs_root=Path('runs'),
    batch_id='fear-hunger-v0.11a',
    n_ticks=200,
    n_founders=5,
    snapshot_tick=100,
    snapshot_seed=1,
    cells=cells_a,
)

# v0.11b: food_ladder + directional
cells_b = all_grid_cells(layout_name='food_ladder', memory_type='directional')
run_memory_grid(
    seeds=[1, 2, 3, 4, 5, 42, 100, 2024],
    runs_root=Path('runs'),
    batch_id='fear-hunger-v0.11b',
    n_ticks=200,
    n_founders=5,
    snapshot_tick=100,
    snapshot_seed=1,
    cells=cells_b,
)
"
```

Outputs in `runs/fear-hunger-v0.11a/` and `runs/fear-hunger-v0.11b/`,
same artifact tree shape as v0.9/v0.10. The "winner" snapshot in
v0.11b is the tie-break artifact `ms0-md0.1`; treat it as a structural
artifact, not a behavioral signal.
