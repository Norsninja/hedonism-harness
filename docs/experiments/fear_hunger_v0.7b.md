# Fear-Hunger Chamber — v0.7b reproduction-motivation grid sweep

**Experiment:** If ``energy_threshold`` is permissive or reachable, does
higher ``reproduction_drive_min`` convert eligibility into multiple
births across seeds?
**Branch:** `claude/review-handoff-docs-XVPTd`
**Date:** 2026-05-04
**Run:** `runs/fear-hunger-v0.7b/`

## Question

The v0.7 sweep falsified "cost is the main blocker" and supported
"threshold is the first blocker." Lowering ``energy_threshold`` from 70
to 50 unlocked exactly **1 birth in 1 seed**. ``energy_cost`` was
dormant because the parent reproduces at most once. The v0.7b question
splits the threshold finding from the motivation question:

> Is the harness's reproductive scarcity an *eligibility* problem
> (parents rarely become eligible to reproduce) or an *intent* problem
> (parents become eligible but don't choose REPRODUCE)?

If the bottleneck is intent, raising ``reproduction_drive_min`` should
amplify the reproductive pleasure term in valence (SPEC §11.4) enough
to convert any threshold-eligible parent into a successful birth. If
the bottleneck is eligibility, drive is dormant.

## Setup

- **Layout**: ``tight_gradient`` (held fixed since v0.4).
- **Policy**: ``HedonismPolicy(exploration_noise=0.05)`` (held fixed).
- **Trait base**: v0.6 winner with ``reproduction_drive_min`` overridden
  per cell (every other axis matches the v0.6 winner).
- **``energy_cost``**: SPEC default 35 (frozen — v0.7 showed it was
  dormant).
- **Hyperparameters**: 5 founders, 200 ticks, 8 seeds (``1, 2, 3, 4, 5,
  42, 100, 2024``).
- **Independent variables**:

| knob | levels | SPEC §8.1 / §7 | meaning |
|---|---|---|---|
| ``energy_threshold``      | {50, 60, 70} | [0, 100] | parent must clear this energy to reproduce |
| ``reproduction_drive_min``| {0.0, 0.5, 1.0} | [0, 3] | floor on per-agent reproduction-drive sample |

3 × 3 = **9 cells × 8 seeds = 72 runs**. The ``(et=70, dm=0.0)`` cell
is the joint SPEC default and acts as the baseline reference. Two new
metrics tracked:

- ``seeds_with_reproduction_requests`` — how many seeds had at least
  one REPRODUCE intent (distinguishes "one obsessive seed" from "drive
  generalized intent across seeds").
- ``births_per_request`` — total_births / total_reproduction_requests
  (0.0 when no requests). Lower means the placement layer is rejecting
  intents; higher means the placement layer is accepting them.

## Pre-registered viability rule (six criteria)

A cell qualifies iff **all six** hold:

1. ``total_births >= 2``
2. ``seeds_with_any_births >= 2``
3. ``total_food_events >= baseline.total_food_events − total_births``
   *(principled corrected food rule from v0.7)*
4. ``seeds_with_any_starvation > 0``
5. ``max_population_end <= 3 × n_founders = 15``
6. ``total_reproduction_requests >= total_births``
   *(invariant guard — should always hold structurally now)*

## Pre-registered failure → action mapping

- **0 cells qualify** → reproduction motivation alone is insufficient;
  layered structural changes (sensor expansion, layout enlargement) are
  next.
- **Multiple cells qualify** → primary score is ``total_births``
  (highest wins). Tie-break: cell **closest to joint SPEC defaults**
  by Euclidean distance in (energy_threshold, drive_min) space.
- **The (70, 0.0) baseline cell qualifies** → the v0.7 result was
  non-deterministic; investigate before promoting.

## Result — drive is dormant, eligibility is the bottleneck

```
qualifiers: 0 / 9
winner:     none
baseline:   cell_id=et70-dm0  food=11  haz=24  surv=1/8  starv=8/8  births=0  reqs=0
```

Per-cell totals across 8 seeds × 5 founders. ``sw_b`` =
seeds_with_any_births, ``sw_r`` = seeds_with_reproduction_requests,
``bpr`` = births_per_request:

```
cell_id     births  sw_b  reqs  sw_r    bpr  food  haz  surv  starv  max_p
et50-dm0         1     1     1     1  1.000    10   23   1/8   8/8      1
et50-dm0.5       1     1     1     1  1.000    10   23   1/8   8/8      1
et50-dm1         1     1     1     1  1.000    10   23   1/8   8/8      1
et60-dm0         0     0     0     0  0.000    11   24   1/8   8/8      1
et60-dm0.5       0     0     0     0  0.000    11   24   1/8   8/8      1
et60-dm1         0     0     0     0  0.000    11   24   1/8   8/8      1
et70-dm0         0     0     0     0  0.000    11   24   1/8   8/8      1   ← baseline
et70-dm0.5       0     0     0     0  0.000    11   24   1/8   8/8      1
et70-dm1         0     0     0     0  0.000    11   24   1/8   8/8      1
```

### Reading the result

**``reproduction_drive_min`` showed no measurable effect across any
threshold level.** The three et=50 cells produced identical outcomes
(1 birth, 1 request, ``bpr=1.0``) regardless of whether the drive
floor was 0.0, 0.5, or 1.0. The et=60 and et=70 cells stayed at 0
births across every drive level.

Three diagnostic readings emerge from the new metrics:

1. **``births_per_request = 1.0`` at every cell that produced any
   intent.** Every REPRODUCE intent was accepted; the placement layer
   (capacity=1 grid + adjacent-empty cell requirement, per
   ``core/reproduction.find_adjacent_empty_cell``) is **not** the
   bottleneck. Acceptance is not the problem.
2. **``seeds_with_reproduction_requests = 1`` at et=50 cells, 0
   elsewhere.** Only seed=1 (the lone survivor seed) ever reaches
   reproductive eligibility under any condition. Eight seeds, one
   ever-eligible parent, one accepted request, one birth. The drive
   axis cannot fire because the eligibility filter never opens.
3. **The food/hazard/survival metrics are bit-identical to v0.7.**
   Foraging behavior, hazard exposure, and survival are unchanged
   across the entire drive grid — exactly what we'd expect if drive
   only affects the (rarely-evaluated) reproductive pleasure term.

**Interpretation:** raising the drive floor cannot manufacture
eligibility. ``HedonismPolicy`` only weighs ``reproduction_drive`` when
``REPRODUCE`` is in the valid-action set, and ``can_reproduce``
(SPEC §27.7) returns ``False`` until energy ≥ threshold *and* age ≥
min_age. By the time the founder is past ``min_age=10``, baseline
metabolism has drained the 60-energy starting pool; only at et=50 does
the parent ever clear the threshold (after foraging refills it). At
that point the parent reproduces once, dies, and there is no second
window for higher drive to exploit. Drive is acting on an empty set.

### What v0.7b confirms about the harness

1. **The harness has now falsified two parameter-only blockers**:
   - v0.7: ``energy_cost`` is dormant at this birth frequency.
   - v0.7b: ``reproduction_drive_min`` is dormant at this throughput.
2. **The bottleneck is upstream of the reproduction subsystem.** It
   is *not* the request→birth path (``bpr=1.0``), *not* the cost
   (v0.7), *not* the motivation (v0.7b). It is the rate at which
   agents become eligible at all — which depends on
   *survival × foraging throughput*, not on reproduction parameters.
3. **The metrics layer is now sound.** The
   ``ReproductionRequested`` signal flows through the bus (fixed in
   v0.7), the request-vs-birth invariant
   (``reproduction_requests >= births``) is asserted by tests and
   confirmed by the data, and the two new metrics
   (``seeds_with_reproduction_requests``, ``births_per_request``)
   distinguish "intent generalized" from "intent concentrated" /
   "placement rejected" from "placement accepted" — both of which
   would have been invisible without the v0.7 bug fix.

### What v0.7b rules out

- "If we make agents *want* to reproduce more, they will."  — false
  at this throughput.
- "The placement layer is rejecting many requests under capacity=1." —
  false; ``bpr=1.0`` confirms acceptance.
- "Reproduction is hidden behind a motivation gate." — false; it is
  hidden behind an *eligibility* gate that motivation cannot open.

## Decision

**v0.7b records: no formal winner; drive-dormant diagnostic result.**
Do not promote any cell. Do not relax the criteria. Do not run another
parameter sweep on the reproduction subsystem.

**The next experiment must be structural, not parametric.**  Two
options on the project ladder:

- **v0.8 — memory arm (``MemoryHedonismPolicy``).** Memory could let
  surviving agents *return* to known food cells repeatedly, raising
  per-agent food throughput and therefore the rate at which agents
  clear the eligibility threshold. This is in the original ladder
  and unblocked.
- **v0.9 — sensor expansion / layout rescue.** Wider sensor radius or
  a more forgiving chamber could let *more* seeds produce a survivor,
  multiplying the eligibility events. Also in the original ladder.

The user's call on which lands first. v0.8 is closer to the
"behavioral substrate" question; v0.9 is closer to the "harness
calibration" question.

## What changed

- [[src/hedonism_harness/experiments/trait_configs.py]] —
  ``motivation_trait_config(*, drive_min)`` factory: v0.6 winner
  ranges with overridden ``reproduction_drive`` floor. SPEC-distance
  validated; identity at ``drive_min=0.0``.
- [[src/hedonism_harness/experiments/motivation_grid.py]] (new) —
  9-cell driver, six-criterion evaluator (incl. corrected food rule
  + invariant guard), SPEC-distance tie-break, winner selector,
  comparison.csv + winner.txt artifacts.
- [[tests/test_motivation_grid.py]] (new) — 23 tests pinning the
  factory bounds, the new metrics
  (``seeds_with_reproduction_requests``, ``births_per_request``,
  including the obsessive-vs-general distinguisher),  every branch of
  the six-criterion evaluator, the failure-mapping winner selection
  (no qualifier / highest births / SPEC-distance tie-break), and
  smoke.

No changes to: ``core/`` (zero), ``mesa_agents.py``,
``policies/``, layouts, archetypes, sensors, valence, ``v0.7``
artifacts.

## Reproducing

```bash
uv run python -c "
from pathlib import Path
from hedonism_harness.experiments.motivation_grid import run_motivation_grid
run_motivation_grid(
    seeds=[1, 2, 3, 4, 5, 42, 100, 2024],
    runs_root=Path('runs'),
    batch_id='fear-hunger-v0.7b',
    n_ticks=200,
    n_founders=5,
    snapshot_tick=100,
    snapshot_seed=1,
)
"
```

Outputs in ``runs/fear-hunger-v0.7b/``:

```
fear-hunger-v0.7b/
    comparison.csv             # 9 cell rows; baseline first (et70-dm0)
                               # includes births_per_request and
                               # seeds_with_reproduction_requests columns
    winner.txt                 # "no qualifying cell" + failure-mode note
    snapshots/                 # empty when no winner
    cells/
        et50-dm0/seed-{N}/...
        et50-dm0.5/seed-{N}/...
        ...
        et70-dm1/seed-{N}/...
```
