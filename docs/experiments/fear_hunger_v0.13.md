# Fear-Hunger Chamber — v0.13 memory-channel calibration (pre-registration)

**Experiment:** Profile the magnitude of `novelty_pleasure` (memory's
output channel) against the rest of the harness on representative
traces, then apply the smallest targeted wiring fix the profile
implies, and re-run the v0.12 directional + action-aware sweep on
both chambers.
**Branch:** TBD — cut from `claude/review-hedonism-harness-i0CnN` tip.
**Date:** TBD (this is a pre-registration; written 2026-05-04, before
running.)
**Runs:** `runs/fear-hunger-v0.13-profile/`,
`runs/fear-hunger-v0.13a/` (tight_gradient),
`runs/fear-hunger-v0.13b/` (food_ladder).

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

## Reproducing (post-run, this section will be filled in)

Phase 1:

```bash
# Trace dump for the three pre-registered scenarios.
uv run python scripts/v0.13_profile.py \
    --seed 1 --tick 50 \
    --winner-cell-id ms1-md0.1 \
    --output runs/fear-hunger-v0.13-profile/traces.md
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
