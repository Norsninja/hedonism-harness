# Fear-Hunger Chamber — v0.7 reproduction-config grid sweep

**Experiment:** Does lowering ``ReproductionConfig.energy_threshold`` and/or
``energy_cost`` unlock first-generation births while preserving the v0.6
foraging behavior?
**Branch:** `claude/review-handoff-docs-XVPTd`
**Date:** 2026-05-04
**Run:** `runs/fear-hunger-v0.7/`

## Question

The v0.6 trait-grid sweep validated the v0.5 permissive zone (27/27 cells
qualified) but **0 births in any cell**. SPEC defaults set
``starting_energy=60`` and ``energy_threshold=70`` — so a founder cannot
reproduce until it has eaten at least once *and* aged past ``min_age=10``.
v0.7 holds layout, policy, and trait config fixed at the v0.6 winner and
sweeps only the two energy-economics knobs:

  - ``energy_threshold`` ∈ {50, 60, 70}
  - ``energy_cost`` ∈ {15, 25, 35}

3 × 3 = **9 cells × 8 seeds = 72 runs**. The ``(70, 35)`` cell is the SPEC
default and acts as the baseline reference for criterion comparison.

## Setup

- **Layout**: ``tight_gradient`` (the only chamber where v0.4 demonstrated
  phenotype expression).
- **Policy**: ``HedonismPolicy(exploration_noise=0.05)``.
- **Trait config**: ``tuned_trait_config(fear_max=1.5, hunger_min=1.0,
  risk_min=0.55)`` — the v0.6 winner.
- **Hyperparameters**: 5 founders, 200 ticks, 8 seeds (``1, 2, 3, 4, 5,
  42, 100, 2024``).
- **Other ``ReproductionConfig`` fields**: SPEC defaults
  (``min_age=10``, ``hazard_threshold=0.5``,
  ``offspring_start_energy=30``).

## Pre-registered viability rule

A cell qualifies iff **all four** hold:

1. ``total_births >= 1`` — the headline test.
2. ``total_food_events >= baseline.total_food_events`` — foraging
   preserved (the trait config is fixed across the grid; any drop
   indicates the cheaper repro drained behavior).
3. ``seeds_with_any_starvation > 0`` — diversity guard (not every seed
   becomes a runaway lineage).
4. ``max_population_end <= 3 × n_founders = 15`` — overpopulation guard
   (one explosive seed disqualifies the cell).

## Pre-registered failure → action mapping

- **0 cells qualify** → economics alone is insufficient. v0.7b raises the
  ``reproduction_drive`` floor (the trait-range knob deliberately deferred
  from v0.7).
- **Multiple cells qualify** → primary score is ``total_births`` (highest
  wins). Tie-break: cell **closest to SPEC defaults** by Euclidean
  distance in (energy_threshold, energy_cost) space.
- **The (70, 35) baseline cell qualifies** → SPEC defaults already work
  and v0.6's zero-births was layout/throughput, not economics; investigate
  before promoting any cell.

## Result — strict no winner, diagnostic threshold-positive

```
qualifiers: 0 / 9
winner:     none
baseline:   cell_id=et70-ec35  food=11  haz=24  surv=1/8  starv=8/8  births=0  reqs=0
```

Per-cell totals across 8 seeds × 5 founders:

```
cell_id      births  reqs  food  haz  surv  starv  max_pop
et50-ec15         1     1    10   23   1/8   8/8       1
et50-ec25         1     1    10   23   1/8   8/8       1
et50-ec35         1     1    10   23   1/8   8/8       1
et60-ec15         0     0    11   24   1/8   8/8       1
et60-ec25         0     0    11   24   1/8   8/8       1
et60-ec35         0     0    11   24   1/8   8/8       1
et70-ec15         0     0    11   24   1/8   8/8       1
et70-ec25         0     0    11   24   1/8   8/8       1
et70-ec35         0     0    11   24   1/8   8/8       1   ← baseline (SPEC default)
```

### Why no formal winner

Per the pre-registered four-criterion rule, the et50 cells fail
criterion 2 (food preservation): they score 10 food events vs the
baseline's 11. The exact 1-event drop is the *time-cost of reproducing
once* — the parent's reproduction tick displaces a foraging tick.

We do **not** retroactively relax criterion 2. v0.7 records this as a
**criterion-design finding**: a successful reproduction consumes an
action tick and can displace one food event without indicating collapse
of foraging behavior. v0.7b will use the principled corrected form
``total_food_events >= baseline.total_food_events − total_births`` so
the test stays strict but accounts for the structural time-cost.

### Reading the result

v0.7 produced no formal winner under the pre-registered four-criterion
rule. However, the result is **diagnostic rather than null**:

1. **``energy_threshold`` is confirmed as a binding constraint.**
   Lowering it from 70 to 50 produced one accepted birth in the same
   seed class (seed=1) that generated the lone survivor under the
   baseline. ``et=60`` is silent because ``min_age=10`` ticks of
   metabolism drain the founder's starting energy below the 60 threshold
   before reproduction becomes selectable.
2. **``energy_cost`` showed no measurable effect.** All three et50 cells
   scored identically because the parent reproduces at most once before
   dying; the cost is only debited once and never amortized across
   repeated reproductions. Second-order cost dynamics never activate at
   this birth frequency.
3. **The behavioral substrate did not change.** Foraging
   (food_events: 10 vs 11), hazard exposure (23 vs 24), survival
   (1/8 across all cells), and diversity (8/8 starvation) are
   essentially unchanged. The cheaper economics did not destabilize
   the v0.6 zone.

So the result is not "nothing happened." It is:

- v0.7 **falsified** "cost is the main blocker."
- v0.7 **supported** "threshold is the first blocker."
- v0.7 **did not yet produce** robust lineage emergence (1 birth in
  1 seed is below any reasonable threshold for "lineage").

That is a good experiment.

## Bug fix shipped alongside v0.7

While running v0.7 we discovered that ``ReproductionRequested`` events
were routed via ``model.queue_birth(self)`` only — they bypassed
``model.record_event(event)`` entirely. The signal-bus subscriber in
``EpisodeAggregator._on_repro_request`` therefore never fired, and
``tally.reproduction_requests`` was permanently 0 across every prior
experiment in the project history. SPEC §14 distinguishes intent
(request) from completion (birth); the metric was meant to be
observable.

The fix is a 2-line change in [[src/hedonism_harness/mesa_agents.py]]:

```python
if isinstance(event, ReproductionRequested):
    model.record_event(event)   # NEW: emit + log
    model.queue_birth(self)
```

Pinned by two new regression tests in [[tests/test_newborn_defer.py]]:

- ``test_reproduction_request_is_observable_through_signal_and_birth_follows``
  — the ``EpisodeAggregator`` handler increments
  ``tally.reproduction_requests``, the birth queue still produces
  ``AgentBorn``, and ``births <= reproduction_requests`` holds as a
  tally invariant.
- ``test_reproduction_request_is_persisted_to_event_log`` — both the
  request and the birth appear in ``model.event_log`` on the same tick
  (request first, birth from queue processing later in the tick).

Simulation behavior is unchanged — the queue still drives birth
processing — only the metrics layer became observable. The v0.7 sweep
above was rerun with the fix in place; ``reqs=1`` for each et50 cell
is now trustworthy and confirms the request-vs-birth invariant.

## Decision

**v0.7 records: no formal winner; threshold-positive diagnostic
result.** Do not promote any cell. Do not retroactively relax the
criterion. Do not run an open-ended sweep.

**Next experiment is v0.7b: reproduction motivation sweep.** With
``energy_cost`` confirmed dormant at current birth frequency, the
v0.7b grid swaps the cost axis for ``reproduction_drive_min``:

  - ``energy_threshold`` ∈ {50, 60, 70}
  - ``reproduction_drive_min`` ∈ {0.0, 0.5, 1.0}
  - ``energy_cost`` fixed at SPEC default 35

9 cells, same seeds and founders. The question becomes: *if threshold
is permissive or reachable, does higher reproduction-drive convert
eligibility into robust reproduction?*

Pre-registered v0.7b acceptance criteria (refined from v0.7):

1. ``total_births >= 2``
2. ``seeds_with_any_births >= 2``
3. ``total_food_events >= baseline − total_births``
   *(the principled corrected form of criterion 2)*
4. ``seeds_with_any_starvation > 0``
5. ``max_population_end <= 15``
6. ``reproduction_requests >= total_births``
   *(invariant guard, observable now that the metric works)*

Criterion 3 is **not** a post-hoc relaxation for v0.7; it is a
pre-registered correction for v0.7b that absorbs the
one-tick-displaces-one-food-event structural artifact identified by
v0.7.

## What v0.7 confirms about the harness

1. **The threshold is the first blocker, not the cost.** SPEC defaults
   make first-generation reproduction possible *in principle* but
   unreachable *in practice* under the v0.6 winner trait config: by the
   time the founder is past ``min_age=10``, metabolism has drained the
   60-energy starting pool below the 70 threshold. Lowering the
   threshold to 50 gives the parent a shot once foraging refills.
2. **The metrics layer is now trustworthy for reproduction-related
   experiments.** The ``ReproductionRequested`` signal flows through the
   bus and the ``request -> birth`` ordering is asserted by tests.
3. **The harness pipeline (run_chamber + grid driver + criterion
   evaluator + winner selector) generalizes to ``ReproductionConfig``
   without code in core.** Only the experiments layer changed for
   v0.7 itself; the bug fix touched ``mesa_agents.py`` (model
   boundary), not core.

## What changed

- [[src/hedonism_harness/mesa_agents.py]] — 2-line bug fix:
  ``ReproductionRequested`` now flows through ``record_event`` so the
  metrics signal observes it.
- [[src/hedonism_harness/experiments/fear_hunger_chamber.py]] —
  ``run_chamber`` gains ``reproduction_config`` kwarg
  (``None`` keeps SPEC defaults).
- [[src/hedonism_harness/experiments/repro_configs.py]] (new) —
  ``tuned_reproduction_config(*, energy_threshold, energy_cost)`` +
  ``repro_cell_id()`` helper.
- [[src/hedonism_harness/experiments/repro_grid.py]] (new) — 9-cell
  driver, four-criterion evaluator, SPEC-distance tie-break, winner
  selector, comparison.csv + winner.txt artifacts.
- [[tests/test_newborn_defer.py]] — 2 new regression tests pinning the
  request-vs-birth signal flow.
- [[tests/test_repro_grid.py]] (new) — 16 tests pinning the parametric
  factory bounds, the four-criterion evaluator (every branch including
  overpopulation), the failure-mapping logic (no qualifier / highest
  births / SPEC-distance tie-break), and a smoke test.

No changes to: ``core/config.py``, ``core/reproduction.py``,
``core/valence.py``, layouts, archetypes, sensors, or trait ranges.

## Reproducing

```bash
uv run python -c "
from pathlib import Path
from hedonism_harness.experiments.repro_grid import run_repro_grid
run_repro_grid(
    seeds=[1, 2, 3, 4, 5, 42, 100, 2024],
    runs_root=Path('runs'),
    batch_id='fear-hunger-v0.7',
    n_ticks=200,
    n_founders=5,
    snapshot_tick=100,
    snapshot_seed=1,
)
"
```

Outputs in ``runs/fear-hunger-v0.7/``:

```
fear-hunger-v0.7/
    comparison.csv             # 9 cell rows; baseline first (et70-ec35)
    winner.txt                 # "no qualifying cell" + failure-mode note
    snapshots/                 # empty when no winner
    cells/
        et50-ec15/seed-{N}/...
        et50-ec25/seed-{N}/...
        ...
        et70-ec35/seed-{N}/...
```
