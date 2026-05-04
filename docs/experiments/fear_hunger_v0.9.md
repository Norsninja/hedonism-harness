# Fear-Hunger Chamber — v0.9 memory-arm grid sweep

**Experiment:** Does per-agent valence memory increase repeat foraging
in the hard ``tight_gradient`` chamber enough to produce more births,
holding reproduction economics, layout, and core valence math fixed?
**Branch:** `claude/v0.9-memory-arm`
**Date:** 2026-05-04
**Run:** `runs/fear-hunger-v0.9/`

## Question

The v0.8 sweep produced the harness's first reproducing population on
``food_ladder`` (winner ``ladder-sr1``: 5 births / 4 seeds). The
``tight_gradient`` chamber — where v0.4 first demonstrated phenotype
expression — remained the *hard problem*: even with sensor-radius
widening, only 1 birth in 1 seed. v0.8 left an open question:

> Holding reproduction economics, layout, and core valence math fixed
> at the v0.7/v0.8 winners, can per-agent valence memory increase
> repeat foraging enough to produce more births in tight_gradient?

The valence harness already plumbs ``remembered_good_*`` (into
``novelty_pleasure``) and ``remembered_bad_*`` (into the
``predicted_hazard_risk`` term of ``fear``); they read 0 because no
policy populated agent memory. v0.9 turns memory on.

## Setup

- **Layout**: ``tight_gradient`` (the hard problem).
- **Policy**: ``HedonismPolicy(exploration_noise=0.05)`` (held fixed).
  No new policy class — ``HedonismPolicy`` already consumes
  ``ctx.memory`` and the valence harness already reads the memory
  signals; the only seam needed is whether each agent has a
  ``ValenceMemory`` instance or ``None``.
- **Reproduction config**: ``tuned_reproduction_config(et=50, ec=35)``
  (the v0.7 threshold-positive cell, frozen since v0.8).
- **Trait base**: v0.6 winner with memory-range overrides per cell.
  Every other axis matches the v0.6 winner identity.
- **``BodyConfig``**: SPEC defaults (held fixed).
- **Hyperparameters**: 5 founders, 200 ticks, 8 seeds (``1, 2, 3, 4,
  5, 42, 100, 2024``).
- **Independent variables**:

| axis                       | levels                | meaning |
|---|---|---|
| ``use_memory``             | False, True           | founders get ``ValenceMemory`` or ``None`` |
| ``memory_strength_min``    | 0.0, 0.5, 1.0         | floor on per-agent ``memory_strength`` sample |
| ``memory_decay_rate_max``  | 0.02, 0.05, 0.1       | ceiling on per-agent ``memory_decay_rate`` sample |

Asymmetric grid: **1 ``mem-off`` baseline + 9 memory-on cells × 8
seeds = 80 runs**. The ``mem-off`` baseline is the v0.6/v0.7/v0.8
``tight-sr1`` identity (verified bit-identical to v0.8 in the
artifact) and serves as the criterion-3 food-floor reference. The
SPEC-permissive memory cell ``(ms_min=0.0, md_max=0.1)`` is the
within-memory-on tie-break reference.

Four pre-registered diagnostic fields surface the *behavioral*
question without gating qualification:

- ``agents_with_memory_updates`` (memory-active sanity)
- ``total_memory_updates`` (memory-active sanity)
- ``repeat_food_visits`` — **headline behavioral metric**
- ``median_food_event_tick`` (when AteFood clusters in the run)

## Pre-registered viability rule (six criteria)

Identical to v0.7b/v0.8 for narrative consistency:

1. ``total_births >= 2``
2. ``seeds_with_any_births >= 2``
3. ``total_food_events >= baseline.total_food_events − total_births``
4. ``seeds_with_any_starvation > 0``
5. ``max_population_end <= 3 × n_founders = 15``
6. ``total_reproduction_requests >= total_births``

Pre-registered failure → action mapping:

- **The ``mem-off`` baseline qualifies** → v0.8 ``tight-sr1`` was
  non-deterministic; investigate before promoting.
- **0 memory cells qualify** → memory alone is insufficient under
  this geometry. Negative-control reading from pre-registration: if
  memory metrics are non-zero but ``repeat_food_visits`` and births
  do not improve, conclude *"memory active but not behaviorally
  effective under tight_gradient"*.
- **Multiple memory cells qualify** → primary score is
  ``total_births`` (highest wins). Tie-break: cell **closest to
  SPEC-permissive memory** ``(ms_min=0.0, md_max=0.1)`` by Euclidean
  distance in ``(memory_strength_min, memory_decay_rate_max)`` space.

## Mid-experiment finding — decay was unwired (and the bug fix)

Running the v0.9 grid as initially designed produced bit-identical
rows across ``memory_decay_rate_max ∈ {0.02, 0.05, 0.1}`` within each
``memory_strength_min`` tier. A grep audit confirmed:

> ``decay_all`` was defined in ``core/memory.py`` and exercised by
> ``tests/test_memory.py``, but no caller ever invoked it from the
> simulation tick loop. ``traits.memory_decay_rate`` was a dormant
> parameter across the entire project history; stale food attractors
> never faded after consumption.

This is a real plumbing gap (SPEC §13.3 mandates per-tick decay),
not an interpretation issue. v0.9 was paused, the wiring was added
(``HHAgent.apply_memory_decay`` called from ``HHModel.step`` step 4
alongside metabolism), and the grid was re-run as **v0.9b**.
Determinism north star + ``v0.8`` re-run confirmed bit-identical
output for ``use_memory=False`` runs (the wiring is gated on
``self.memory is not None``).

The v0.9 (pre-fix) and v0.9b (post-fix) results are both reported
below — the comparison itself is informative: the v0.9 readings show
"memory active but stale-attractor-pulled"; v0.9b shows "memory
active with proper temporal decay."

## Result — strict no winner across both runs

```
qualifiers: 0 / 9    (both pre-fix and post-decay)
winner:     none
baseline:   cell_id=mem-off  food=10  haz=23  surv=1/8  starv=8/8  births=1  reqs=1
            mem_updates=0  repeat_food=7
```

### v0.9 (pre-fix, decay dormant)

```
cell_id        births sw_b reqs food haz surv  mUp  agUp rpt  medT
mem-off             1    1    1   10  23  1/8     0    0   7  37.7
ms0-md0.02          1    1    1    5  84  0/8  2801   41   3  31.8
ms0-md0.05          1    1    1    5  84  0/8  2801   41   3  31.8
ms0-md0.1           1    1    1    5  84  0/8  2801   41   3  31.8
ms0.5-md0.02        1    1    1    2  62  0/8  3078   41   1  16.5
ms0.5-md0.05        1    1    1    2  62  0/8  3078   41   1  16.5
ms0.5-md0.1         1    1    1    2  62  0/8  3078   41   1  16.5
ms1-md0.02          1    1    1    8  30  0/8  3376   41   6  33.8
ms1-md0.05          1    1    1    8  30  0/8  3376   41   6  33.8
ms1-md0.1           1    1    1    8  30  0/8  3376   41   6  33.8
```

`sw_b` = seeds_with_any_births, `mUp` = total_memory_updates,
`agUp` = total_agents_with_memory_updates, `rpt` =
total_repeat_food_visits, `medT` = mean_median_food_event_tick.

Decay axis is bit-identical across cells within each strength tier
(visible above as triplicate rows) — confirms ``decay_all`` was never
fired.

### v0.9b (post-fix, decay wired)

```
cell_id        births sw_b reqs food haz surv  mUp  agUp rpt  medT
mem-off             1    1    1   10  23  1/8     0    0   7  37.7
ms0-md0.02          1    1    1    5  77  0/8  2830   41   3  31.8
ms0-md0.05          1    1    1    5  79  0/8  2847   41   3  31.8
ms0-md0.1           1    1    1    5  82  0/8  2817   41   3  31.8
ms0.5-md0.02        1    1    1    4  70  0/8  3112   41   2  30.8
ms0.5-md0.05        1    1    1    4  68  0/8  3111   41   2  30.8
ms0.5-md0.1         1    1    1   11  67  0/8  3299   41   9  54.0
ms1-md0.02          1    1    1    8  29  0/8  3354   41   6  33.0
ms1-md0.05          1    1    1   13  29  0/8  3428   41  11  61.8
ms1-md0.1           1    1    1   13  26  0/8  3432   41  11  51.2
```

The v0.9b stored ``runs/fear-hunger-v0.9/comparison.csv`` is the
post-fix run. Decay axis now varies (rows are no longer bit-identical
across ``md`` levels), confirming the wiring works end-to-end.

## Reading the result

**The headline answer is "no": memory alone does not rescue
tight_gradient.** Every cell, including the most permissive memory
range, produces exactly 1 birth in 1 seed — the same single-survivor
seed that drives v0.7's threshold-positive result and v0.8's
``tight-sr1`` baseline. Criterion 2 (``seeds_with_any_births >= 2``)
fails everywhere.

**But the v0.9 → v0.9b comparison is informative on its own.**

1. **Pre-fix (v0.9): memory was actively counterproductive.** Compared
   to ``mem-off`` baseline (food=10, haz=23, repeat=7), the
   permissive memory cells dropped foraging (food 5, 2, 8 across
   ``ms_min`` tiers) and inflated hazard exposure (haz 84, 62, 30).
   With cell-exact ``pleasure_ema`` set to a positive value at every
   consumed food cell *and never decaying*, the directional scan
   pulled agents toward stale attractors — locations that *were*
   pleasurable but were now empty. Agents pursued ghosts across the
   hazard band.

2. **Post-fix (v0.9b): memory becomes neutral-to-slightly-helpful at
   the right parameters.** With decay wired, cells varied along the
   ``md`` axis. Two regimes emerge:

   - **Slow EMA + slow decay (``ms_min ∈ {0.0, 0.5}``, low
     ``md_max``)**: still slightly worse than baseline — the
     attractor pull is weaker but not gone.
   - **Slow EMA + fast decay (``ms1-md0.05``, ``ms1-md0.1``)**:
     foraging *exceeds* baseline (food=13 vs 10, repeat=11 vs 7) at
     comparable hazard exposure (haz=29, 26 vs 23). Memory at this
     setting acts approximately like recency-weighted directional
     reward — it leans the agent toward locations that have *recently*
     been good, which the decay term keeps fresh.

3. **The behavioral pattern is real but sub-eligibility-threshold.**
   ``ms1-md0.1`` produces 13 food events vs baseline's 10 and
   doubles repeat foraging (11 vs 7) — the "repeat food visits" metric
   is exactly the headline behavioral signal pre-registered as
   evidence for memory's intended effect. But under v0.7's
   reproduction economics + tight_gradient geometry, no second seed
   crosses the eligibility threshold within 200 ticks. Memory shifts
   *behavior* but not *eligibility supply*.

### What v0.9 + v0.9b confirm about the harness

1. **The decay-not-wired bug was real and silent.** Every prior
   experiment that involved ``traits.memory_decay_rate`` (no full
   sweep had been run) read a parameter the simulation ignored. The
   fix is a 3-line change in ``HHAgent`` + 1 call site in
   ``HHModel.step``; v0.7/v0.7b/v0.8 sweeps re-ran bit-identically
   because they used ``use_memory=False``.
2. **Memory works mechanically but is ecologically out of phase with
   single-use food.** The harness routes
   ``remembered_good_*`` into ``novelty_pleasure``; with cell-exact
   memory and consumable terminal food, memory becomes a stale
   attractor without runtime decay. v0.9b's decay-wired runs show
   memory's behavioral effect can be made approximately
   recency-weighted at high strength + high decay, but the underlying
   representation (cell-exact valence) is mismatched to a sparse,
   consumable-food ecology.
3. **The eligibility bottleneck is upstream of memory benefit at this
   throughput.** Even ``ms1-md0.1``'s 13 food events / 11 repeat
   visits — a clear improvement on the substrate — leave 7 of 8
   seeds short of clearing ``min_age=10 + energy_threshold=50`` once.
   The v0.7b/v0.8 finding holds: tight_gradient is brutal in a way
   that perceptual or representational tweaks alone cannot rescue.

### What v0.9 + v0.9b rule out

- *"Memory rescues tight_gradient."* — false at this configuration.
- *"The decay axis was active before this slice."* — false; v0.9
  surfaces a project-wide unwired-decay bug.
- *"Memory has no behavioral effect."* — false; v0.9b ``ms1-md0.05/0.1``
  improves foraging and repeat visits over baseline. The effect is
  real but sub-threshold for reproduction.

## Decision

**Adopt v0.9b — the decay-wired result — as the v0.9 record.**
The pre-fix table is preserved above for transparency, but the
post-fix run is the science: ``runs/fear-hunger-v0.9/comparison.csv``
is the v0.9b artifact (v0.9-pre-fix is not retained on disk).

**No formal winner; memory cannot promote a cell.** The pre-registered
negative-control conclusion applies:

> Memory metrics increased substantially (``total_memory_updates``
> 2817–3432, ``total_agents_with_memory_updates`` 41) and
> ``repeat_food_visits`` improved over baseline at high
> strength + decay, but ``total_births`` and ``seeds_with_any_births``
> did not — therefore "memory active but not behaviorally effective
> *enough* to convert eligibility under tight_gradient geometry."

## What v0.9 leaves open

1. **Does memory help on a permissive ecology?** v0.9 only ran on
   tight_gradient. The matching positive-control sweep on
   ``food_ladder`` (where v0.8 already produced reproduction without
   memory) was scoped out as v0.9c during pre-registration but not
   run. If memory raises ``ladder-sr1``'s 5 births by *any* margin,
   we have evidence that memory *works when ecology supports it* —
   which would corroborate the "tight_gradient is too brutal a stage
   for memory bootstrap" hypothesis.

2. **Is cell-exact memory the wrong representation?** The harness
   stores ``pleasure_ema[x, y]`` — exact-cell. With single-use food
   the cell is empty after consumption; even with decay wired, the
   memory representation is "the cell at (10, 3) was once good"
   rather than the more biologically plausible "this region tends
   to have food" or "moving east improved energy." v0.10+ may want
   to test region/gradient/resource-class memory abstractions; this
   is a project-direction decision, not a bug-fix.

3. **Does the harness need a curriculum?** The progression
   suggested by senior-dev synthesis: Stage A (abundant gradients) →
   Stage B (clustered consumable food) → Stage C (hazards near food)
   → Stage D (sparse food + memory) → Stage E (reproduction under
   scarcity). v0.8 demonstrated Stage B/C works (food_ladder); v0.9
   demonstrates Stage D is too far ahead under cell-exact memory.
   This is a v0.10+ research-direction question.

## What changed

- [[src/hedonism_harness/mesa_agents.py]] — new
  ``HHAgent.apply_memory_decay()`` method calling
  ``core.memory.decay_all`` with ``traits.memory_decay_rate``;
  no-op when ``self.memory is None`` or the agent is dead. SPEC §13.3
  decay is now wired into the simulation tick loop.
- [[src/hedonism_harness/model.py]] — ``HHModel.step`` step 4 (per-tick
  decay processes) now invokes ``apply_memory_decay`` alongside
  ``apply_metabolism_step``. Tick-order docstring updated.
- [[src/hedonism_harness/experiments/fear_hunger_chamber.py]] —
  ``run_chamber`` gains ``use_memory: bool = False`` kwarg threaded
  into ``FounderSpec.use_memory``. Default keeps SPEC behavior.
- [[src/hedonism_harness/experiments/trait_configs.py]] —
  ``memory_trait_config(*, memory_strength_min, memory_decay_rate_max)``
  factory + ``memory_cell_id()`` helper. Identity at
  ``(memory_strength_min=0.0, memory_decay_rate_max=0.1)``.
- [[src/hedonism_harness/experiments/memory_telemetry.py]] (new) —
  ``MemoryTelemetry`` dataclass + ``MemoryTelemetryCollector``:
  ``agents_with_memory_updates`` / ``total_memory_updates`` (per-tick
  ``visits.sum()`` snapshot, max-ever per agent_id), ``repeat_food_visits``
  via ``AteFood`` event subscription, ``median_food_event_tick``.
- [[src/hedonism_harness/experiments/memory_grid.py]] (new) —
  10-cell driver (1 ``mem-off`` + 9 memory-on), v0.7b 6-criterion
  evaluator, distance-to-permissive tie-break, ``mem-off`` excluded
  from candidates, comparison.csv with all memory-diagnostic columns
  + winner.txt artifacts.
- [[tests/test_experiments_fear_hunger.py]] — 3 new tests pinning the
  ``use_memory`` seam: ``False`` ⇒ founders have ``memory=None``;
  ``True`` ⇒ founders have fresh ``ValenceMemory`` sized to the
  chamber; children of memory-enabled parents receive fresh memory
  (SPEC §13.4) on the reproduction tick.
- [[tests/test_memory_decay_wiring.py]] (new) — 8 tests pinning the
  decay-wiring: ``apply_memory_decay`` no-op when memory is ``None`` /
  agent is dead; uses ``traits.memory_decay_rate``; zero-rate is a
  no-op; ``model.step()`` calls it each tick; planted-pleasure decays
  exponentially under repeated steps; visits / last_seen are
  unaffected.
- [[tests/test_memory_grid.py]] (new) — 27 tests pinning the
  ``memory_trait_config`` factory bounds, telemetry collector behavior
  on real models (memory updates, repeat-food via signal bus, median
  tick using the model clock), evaluator branches, ``mem-off``-excluded
  winner selection, distance-to-permissive tie-break, and a smoke test.

No changes to: ``core/`` math (``valence.py`` already wired memory
signals; ``memory.py`` already had ``decay_all`` defined), policies
(``HedonismPolicy`` already consumes ``ctx.memory``), other layouts,
trait master ranges, or v0.7/v0.7b/v0.8 artifacts (the v0.8 sweep
re-ran bit-identically post-decay-wiring, since ``use_memory=False``
agents have ``memory=None`` and decay is gated on that).

## Reproducing

```bash
uv run python -c "
from pathlib import Path
from hedonism_harness.experiments.memory_grid import run_memory_grid
run_memory_grid(
    seeds=[1, 2, 3, 4, 5, 42, 100, 2024],
    runs_root=Path('runs'),
    batch_id='fear-hunger-v0.9',
    n_ticks=200,
    n_founders=5,
    snapshot_tick=100,
    snapshot_seed=1,
)
"
```

Outputs in ``runs/fear-hunger-v0.9/``:

```
fear-hunger-v0.9/
    comparison.csv             # 10 cell rows; baseline (mem-off) first
                               # includes use_memory, memory_strength_min,
                               # memory_decay_rate_max, total_agents_with_memory_updates,
                               # total_memory_updates, total_repeat_food_visits,
                               # mean_median_food_event_tick
    winner.txt                 # "no qualifying cell" + negative-control note
    snapshots/                 # empty when no winner
    cells/
        mem-off/seed-{N}/...
        ms0-md0.02/seed-{N}/...
        ms0-md0.05/seed-{N}/...
        ...
        ms1-md0.1/seed-{N}/...
```
