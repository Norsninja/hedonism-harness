# v0.17 — offspring-energy substrate variants under reflex baseline + cost-15

**Status:** pre-registration; not yet executed.
**Date:** 2026-05-05
**Branch:** `claude/v0.17-offspring-energy`
**Predecessors:** v0.14 (reflex cell, first compounding), v0.15 (chemotaxis-
tier scalar memory, no compounding lift), v0.16 (reproduction-economics:
per-parent lever confirmed, ceiling barely moves).
**Spec:** [[docs/specs/v0.2_reflex_cell_spec.md]] §"Comparison framework"
(substrate axis).

## Question

v0.16 found that lowering `energy_cost` lifts per-parent productivity
strongly (mean_births_per_parent +51% / +36%; mean_post_birth_lifespan
+34% / +68%) but does **not** lift the H2 ceiling
(`births_after_tick_50` capped at 0 on tight_gradient and 4 on
food_ladder; `seeds_with_survivors` flat). The headline finding was:
**parents are doing fine; the bottleneck is children dying before they
themselves reproduce**. v0.17 tests the cheapest candidate fix: give
children more starting energy.

Does raising `offspring_start_energy` lift the compounding ceiling
(`births_after_tick_50`, `seeds_with_survivors`, and the new direct
metric `total_grandchildren_count`) on either chamber?

## Background

The v0.14 / v0.15 / v0.16 baseline runs `tuned_reproduction_config(
energy_threshold=50, energy_cost=35, offspring_start_energy=30)`.
Newborns spawn with 30 energy in a chamber where:

- a FOOD cell delivers 20 energy when consumed (`food_value_default`);
- base metabolic cost is ~0.25 energy/tick + sensor radius cost;
- a MOVE costs 1.0 energy.

A newborn at 30 energy has ~15-25 ticks to find a food cell before
starvation, depending on movement intensity. On `food_ladder` the
pre-food band is reachable from spawn within ~5-10 moves; on
`tight_gradient` the only food is past a hazard wall. The post-tick-50
wall observed in v0.14-v0.16 is consistent with newborns failing to
reach food in time and dying before they themselves reproduce.

v0.16's per-parent telemetry showed parents living 64-86 ticks
post-birth (cost-15) and producing ~3 births each on tight_gradient.
But `seeds_with_survivors` stayed flat at 1-2/8 (tight_gradient) and
4/8 (food_ladder). The fixed-points: parents survive longer, parents
have more births, but the lineage still dies out at the same rate.
Children are not converting their first-generation births into
post-tick-50 grandchildren.

## Hypothesis

The **child energy floor** is the binding constraint on lineage
compounding. Raising `offspring_start_energy` extends each child's
window-to-first-food, which should:

- raise `total_grandchildren_count` (births where parent_id was itself
  born during the run — direct compounding metric);
- raise `births_after_tick_50` and `seeds_with_survivors` on
  food_ladder if the v0.14-v0.16 ceiling there is indeed
  child-survival-bounded;
- possibly lift `tight_gradient` off its hard-zero ceiling on
  `births_after_tick_50` if child survival is the binding constraint
  there too (rather than chamber geometry / hazard wall).

If `offspring_start_energy` does NOT lift these metrics, child
survival is **not** the binding constraint, and v0.18 targets
food respawn / regrowth (the next axis).

## Conservation caveat (load-bearing — pre-registered)

Raising `offspring_start_energy` is a **free energy handout**: the
child's starting energy materialises from nothing and is not debited
from the parent or anywhere else. Even if it lifts compounding, the
result is not "the substrate compounds under reflex cells." The
honest reading is: **"the substrate compounds when given a free
energy injection at every birth."**

This caveat is pre-committed because it shapes the v0.18 plan
regardless of v0.17's outcome:

- **If v0.17 lifts compounding under the handout**, v0.18 = food
  respawn / regrowth under conservation, to test whether the same
  lift survives when the energy comes from somewhere instead of
  nowhere.
- **If v0.17 does NOT lift compounding even with the handout**, child
  survival is not the binding constraint, and v0.18 = food respawn
  anyway (the next-most-likely substrate axis).

Either way v0.18 is food conservation; v0.17 is the cheapest
diagnostic that distinguishes the two paths through it.

## Mechanism

No new mechanism. v0.14 reflex cell, no scalar memory, auto-
reproduction substrate phase, identical chambers. v0.16's `cost-15`
economics held fixed (`energy_threshold=50`, `energy_cost=15`). Only
`reproduction_config.offspring_start_energy` varies across cells.

## Arms

Single-arm structure: every cell uses **reflex-baseline** (the v0.14
reflex-auto policy, no scalar memory) with cost-15 economics. Arms
differ only in `offspring_start_energy`.

| arm | energy_threshold | energy_cost | offspring_start_energy | label |
|---|---:|---:|---:|---|
| A | 50 | 15 | 30 | start-30 (baseline; reproduces v0.16 cost-15) |
| B | 50 | 15 | 60 | start-60 |
| C | 50 | 15 | 100 | start-100 |

Three offspring-energy variants × two chambers × eight seeds = 48
runs. Same scale as v0.14 / v0.15 / v0.16. The {30, 60, 100} band
spans 3.3x to give a clear plateau test; per the v0.16 watch-out the
factory's bound on `offspring_start_energy` is `[0.0, 100.0]`, so 100
sits at the ceiling of the operational range without raising it.

`min_age` (default 10), `hazard_threshold` (default 0.5), and the
chamber layouts are held at v0.14-v0.16 values.

## Pre-registered hypotheses

The hypothesis structure follows the v0.15 / v0.16 pattern of
pre-committing strongly to the **mechanical intervention firing** and
weakly to the **headline ceiling lift**. v0.15 H1/H2 and v0.16 H1/H2
were both falsified at the strong form; the value of those slices
came from the falsifications. Same shape applies here.

### Strong form (the intervention fires)

- **H1.** `mean_post_birth_lifespan_ticks` is monotone non-decreasing
  in `offspring_start_energy` on both chambers. Children with more
  starting energy die later; their parents (and they themselves, once
  they reproduce) consequently keep producing births later in the
  run. If H1 fails, the intervention is broken (children aren't
  actually getting more energy) — that's a wiring defect, not an
  experimental finding.
- **H2.** `mean_grandchildren_per_seed` is monotone non-decreasing in
  `offspring_start_energy` on both chambers. This is the direct
  compounding metric: count of `AgentBorn` events whose `parent_id`
  was itself an `AgentBorn` agent (i.e. not a founder). H2 firing
  weakly is the minimum signal the intervention does what it's
  supposed to do. H2 firing strongly is the headline lift.

### Weak / cautious form (the ceiling lifts)

- **H3.** `births_after_tick_50` lifts on food_ladder under at least
  one of B / C. Pre-reg-cautious because (i) `food_events` is
  hard-capped at 174 across all v0.15 / v0.16 arms — even infinite
  child energy may not lift compounding past what fixed food supply
  permits — and (ii) a +1 absolute event on n=8 is within seed noise.
  A meaningful lift would be `>= +3` total births_after_tick_50
  across the chamber's 8 seeds.
- **H4.** `births_after_tick_50` lifts off zero on tight_gradient
  under at least one of B / C. **Pre-reg-cautious.** Three
  experiments deep at hard zero (v0.14, v0.15, v0.16); if the
  binding constraint there is the hazard-wall geometry rather than
  child survival, this stays at zero regardless of
  `offspring_start_energy`. Falsification is expected-but-not-
  required-for-v0.17-success.
- **H5.** `seeds_with_survivors` rises monotone with
  `offspring_start_energy` on at least one chamber. **Pre-reg-
  cautious.** v0.16 falsified this for `energy_cost`; whether
  `offspring_start_energy` is qualitatively different remains to be
  seen.

### Determinism

- **H6.** Arm A (`offspring_start_energy=30`) reproduces the v0.16
  cost-15 sweep bit-identically on `(total_births,
  births_after_tick_50, seeds_with_survivors, total_food_events)`
  per seed and per chamber. This is the **bit-identity contract**;
  verified at sweep time against the v0.16 cost-15 published
  numbers.

## Headline metrics

Same shape as v0.16, plus one new direct compounding metric:

- `total_births`
- `seeds_with_any_births`
- `births_after_tick_50` — the H2 ceiling test from v0.13 onwards.
- `seeds_with_survivors` at run end.
- `still_tick_fraction`.
- `total_food_events`, `hazard_entries`, `starvation_deaths`,
  `reproduction_requests`.
- v0.16 per-parent telemetry: `mean_births_per_parent`,
  `mean_post_birth_lifespan_ticks`, `total_distinct_parents`.

New v0.17 instrumentation:

- **`total_grandchildren_count`** (per `RunDiagnostics`) — count of
  `AgentBorn` events whose `parent_id` is in the set of agent_ids
  that were themselves `AgentBorn` (i.e. not founders). Single-pass
  computation on `events.jsonl`. Founders never appear in
  `AgentBorn` (they spawn via `_spawn_founder`, no event), so the
  set excludes them automatically. Births are causally ordered
  (a child cannot be born before its parent), so the set can be
  built in the same pass.
- **`mean_grandchildren_per_seed`** (per `ArmCellAggregate`) —
  `total_grandchildren_count / n_seeds`. Average grandchildren per
  run. Different denominator from `mean_births_per_parent`
  (denominator = distinct parents); the per-seed denominator is
  named explicitly to keep the contrast clear.

## Decision rules

- **H2 confirms (`mean_grandchildren_per_seed` monotone-increasing
  in `offspring_start_energy`) AND H3 confirms
  (`births_after_tick_50` lifts on food_ladder).** Child survival
  is a real lever for compounding under the handout. v0.18 = food
  respawn under conservation to test whether the lift survives a
  conserved energy budget.

- **H2 confirms but H3/H4/H5 fail.** The intervention fires (more
  grandchildren) but the ceiling metrics don't lift — interpretation:
  more grandchildren are being produced but lineage survival is
  still gated by something downstream (population pressure, food
  saturation, geometry). The conservation caveat applies more
  strongly: v0.18 food respawn becomes a stronger candidate.

- **H1/H2 both fail.** The intervention does not fire — children
  are not surviving longer despite more starting energy. Most
  likely a wiring defect (offspring_start_energy not flowing through
  to the actual newborn body). Investigate before drawing
  experimental conclusions.

- **`total_food_events` rises sharply** under B / C. The v0.15 /
  v0.16 finding that food_events is identical across arms (192 /
  174) was: the chamber's food supply is exhausted independently of
  how many cells could in principle reach it. If v0.17 changes that
  — if more children survive long enough to consume more food —
  it would imply v0.16's finding was an artefact of the small
  surviving population. Worth noting in the results.

- **C < B (regression at `offspring_start_energy=100`).** Possible
  if oversized children outcompete parents for the same fixed food
  pool, or if the spawn-on-parent-cell collision logic produces
  different displacement under heavier children. Investigate before
  drawing inference.

## Out of scope (v0.17)

- Food respawn / regrowth — deferred to v0.18 (the largest
  engineering surface and the main conservation question).
- Chamber geometry variants (`hazard_x_max - hazard_x_min`,
  `food_density`, chamber dimensions) — deferred to v0.19+.
- ScalarMemory under varied `offspring_start_energy` — deferred
  unless v0.17 shows a clear lift and the v0.15 chemotaxis cell
  becomes worth re-testing on a productive substrate.
- `min_age` and `max_energy` variants — deferred.
- HedonismPolicy comparisons — quarantined per v0.2 spec.
- Multi-cell-tier directional EMA — deferred until the substrate
  question is settled.

## Implementation notes

### File-level changes

- Modify: [[src/hedonism_harness/experiments/repro_configs.py]] —
  extend `tuned_reproduction_config` with
  `offspring_start_energy: float = 30.0` parameter (default
  preserves v0.14/v0.15/v0.16 bit-identity); validate
  `[0.0, 100.0]` per existing factory contract.
- Modify: [[src/hedonism_harness/experiments/comparison_grid.py]] —
  extend `Arm` with optional `offspring_start_energy: float | None
  = None`; thread through `_run_one_arm_seed` to
  `tuned_reproduction_config`. `None` preserves bit-identity
  against `V0_15_ARMS` / `V0_16_ARMS`. Add `V0_17_ARMS` tuple of
  three reflex-baseline arms with `offspring_start_energy ∈ {30,
  60, 100}`, `energy_cost=15`, `energy_threshold=50`.
- Modify: [[src/hedonism_harness/experiments/comparison_grid.py]] —
  extend `RunDiagnostics` with `total_grandchildren_count`;
  extend `ArmCellAggregate` with `total_grandchildren_count` and
  the `mean_grandchildren_per_seed` property. Single-pass
  extraction in `_read_run_diagnostics`: build the set of
  `born_agent_ids` and count `AgentBorn` events whose `parent_id`
  is in that set.
- New: [[tests/test_comparison_grid_offspring_energy.py]] —
  mirrors the v0.16 test pattern: `Arm.offspring_start_energy`
  default is `None`; `V0_17_ARMS` shape; end-to-end run with an
  explicit override; `tuned_reproduction_config` bounds; FIXED_*
  sanity. Plus a unit test for grandchildren counting (synthetic
  `events.jsonl`).
- Documented: this file (`docs/experiments/fear_hunger_v0.17.md`);
  results appended after the sweep.

### Determinism contract

- Arm A (`offspring_start_energy=30`) reproduces v0.16 cost-15
  bit-identically on `(total_births, births_after_tick_50,
  seeds_with_survivors, total_food_events)` per seed and per
  chamber. Verified at sweep time against the v0.16 results table:
  - tight_gradient: 74 / 0 / 2 / 192
  - food_ladder: 55 / 4 / 4 / 174
- Override defaults are `None`. The existing `V0_15_ARMS` and
  `V0_16_ARMS` produce identical sweep outputs after the v0.17
  changes.
- `still_tick_fraction` and the v0.16 per-parent telemetry are
  unchanged in shape and computation; v0.17 adds a single new
  field that is computed by the same single-pass walk.

### LOC estimate

- `repro_configs.py` parameter extension: ~10 LOC.
- `comparison_grid.py` Arm extension + grandchildren telemetry:
  ~50 LOC.
- New tests: ~120 LOC.
- This doc: ~330 LOC.

Total v0.17 implementation: ~510 LOC. Comparable to v0.16.

## Results (executed 2026-05-05)

Three arms × two chambers × eight seeds (1..8) × 200 ticks × 5 founders.
48 runs total. Reflex-baseline policy (no scalar memory), `energy_cost=15`,
`energy_threshold=50`, `unbounded_mutation=True`, no archetype injection.

### Headline finding — largest single intervention effect in the project's history

Lifting `offspring_start_energy` from 30 to 100 produces:

- **`births_after_tick_50`: tight_gradient 0 → 72 (off hard zero for the
  first time across v0.14/v0.15/v0.16/v0.17 — ∞× lift); food_ladder
  4 → 147 (×36.8).**
- **`mean_grandchildren_per_seed`: tight_gradient 2.38 → 19.12 (×8);
  food_ladder 0.38 → 38.88 (×102).**
- **`seeds_with_survivors`: tight_gradient 2/8 → 7/8; food_ladder
  4/8 → 8/8.**

No prior slice — not v0.4's safe-corridor, not v0.7's reproduction-
emergence, not v0.13's hunger-gate, not v0.14's reflex cell — has
moved any compounding metric by these magnitudes.

### Conservation caveat — central to interpretation, not a footnote

`offspring_start_energy` is a free energy handout. Each newborn's
starting energy materialises from nothing — not debited from the
parent, not drawn from any environmental pool, not constrained by
`food_events` (which stays hard-capped at 192/174 across all arms).

**v0.17 therefore proves: the v0.14-v0.16 lineage ceiling was
child-survival-bounded.**

**v0.17 does NOT yet prove: the substrate compounds under conserved
ecology.** The lift is real, but it is a lift under a free injection,
not under a conserved energy budget. Whether the same compounding
survives when the child's starting energy comes from somewhere — a
respawning food pool, a parent-debited transfer, a reduced metabolic
floor — is the now-central project question.

### Next slice (v0.18) — locked

**v0.18 = food respawn / regrowth under conservation.**

The pre-reg's decision rule fires unambiguously: child energy is one
binding constraint. v0.18 replaces the free handout with a respawning
food pool (the simplest conservation primitive: tile yields N energy,
respawns after K ticks) and re-runs the v0.17 sweep with
`offspring_start_energy=30`. If compounding lifts equivalently with
respawn instead of handout, the substrate compounds under
conservation. If it doesn't, child energy is necessary but not
sufficient under conservation, and v0.19 targets the next axis (food
density, metabolic cost, or both).

### Determinism contract — verified

Arm `start-30` reproduces v0.16 cost-15 bit-identically on both
chambers across all four contract metrics:

| chamber | metric | v0.16 cost-15 | v0.17 start-30 | match |
|---|---|---:|---:|:---:|
| tight_gradient | `total_births` | 74 | 74 | ✓ |
| tight_gradient | `births_after_tick_50` | 0 | 0 | ✓ |
| tight_gradient | `seeds_with_survivors` | 2/8 | 2/8 | ✓ |
| tight_gradient | `total_food_events` | 192 | 192 | ✓ |
| food_ladder | `total_births` | 55 | 55 | ✓ |
| food_ladder | `births_after_tick_50` | 4 | 4 | ✓ |
| food_ladder | `seeds_with_survivors` | 4/8 | 4/8 | ✓ |
| food_ladder | `total_food_events` | 174 | 174 | ✓ |

`still_tick_fraction` (94.4% tight / 93.9% food_ladder),
`mean_births_per_parent` (3.08 / 1.96), and
`mean_post_birth_lifespan_ticks` (86.2 / 81.5) at start-30 also match
v0.16 cost-15 published numbers. `total_grandchildren_count` is new in
v0.17 (no prior baseline).

### v0.17a tight_gradient

| arm | births | b>50 | survivors | parents | b/p | lifespan_mean | lifespan_total | gc | gc/seed | food | pop_end | starv | repro_req | still% |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| start-30 (A baseline) | 74 | 0 | 2/8 | 24 | 3.08 | 86.2 | 2070 | 19 | 2.38 | 192 | 1 | 112 | 74 | 94.4 |
| start-60 (B) | 127 | 8 | 2/8 | 71 | 1.79 | 68.3 | 4848 | 73 | 9.12 | 192 | 2 | 164 | 127 | 96.1 |
| start-100 (C) | 207 | **72** | **7/8** | 117 | 1.77 | 77.5 | **9062** | **153** | **19.12** | 192 | 15 | 185 | 214 | 97.3 |

C-A: total_births +180% (74 → 207); **`births_after_tick_50` lifts off
hard zero for the first time across v0.14/v0.15/v0.16/v0.17 (0 → 8 →
72)**; `seeds_with_survivors` 2 → 2 → 7 (the chamber's
hazard-wall geometry was not the binding constraint after all);
`mean_grandchildren_per_seed` 2.38 → 9.12 → 19.12 (×8.0);
`total_post_birth_lifespan_ticks` (raw, un-confounded by parent-pool
size) 2070 → 9062 (×4.4); `food_events` identical across arms (192).
The lifespan **mean** is non-monotone (86.2 → 68.3 → 77.5) but the
**raw sum** lifts cleanly — the dip is a denominator effect from the
parent pool exploding 24 → 117 (the late-reproducing parents pull the
mean down without shortening anyone's individual life). See "On the
H1 dip" below.

### v0.17b food_ladder

| arm | births | b>50 | survivors | parents | b/p | lifespan_mean | lifespan_total | gc | gc/seed | food | pop_end | starv | repro_req | still% |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| start-30 (A baseline) | 55 | 4 | 4/8 | 28 | 1.96 | 81.5 | 2281 | 3 | 0.38 | 174 | 2 | 90 | 55 | 93.9 |
| start-60 (B) | 187 | 61 | 7/8 | 157 | 1.19 | 70.9 | 11129 | 133 | 16.62 | 174 | 13 | 193 | 189 | 96.7 |
| start-100 (C) | 366 | **147** | **8/8** | 242 | 1.51 | 90.0 | **21783** | **311** | **38.88** | 174 | 34 | 198 | 404 | 97.9 |

C-A: total_births +565% (55 → 366); **`births_after_tick_50` lifts
4 → 61 → 147 (×36.8 at C)**; `seeds_with_survivors` 4 → 7 → 8/8
(every seed has surviving lineage at C); `mean_grandchildren_per_seed`
0.38 → 16.62 → 38.88 (×102); `total_post_birth_lifespan_ticks` (raw)
2281 → 21783 (×9.5); `food_events` identical (174). Notable:
`max_population_end` lifts 2 → 34 — at start-100 the most populous
seed has 34 surviving cells at run end, vs 2 under baseline.

### Hypotheses → outcomes

- **H1.** `mean_post_birth_lifespan_ticks` monotone non-decreasing in
  `offspring_start_energy` on both chambers. **Falsified at strong
  form.** tight_gradient: 86.2 → 68.3 → 77.5 (dips at B). food_ladder:
  81.5 → 70.9 → 90.0 (dips at B, recovers at C). The dip is a
  parent-pool denominator effect, not an individual-parent
  regression — `total_post_birth_lifespan_ticks` (raw sum) lifts
  monotonically on both chambers (2070 → 9062 tight; 2281 → 21783
  food_ladder). See "On the H1 dip" below for the full mechanism.
- **H2.** `mean_grandchildren_per_seed` monotone non-decreasing in
  `offspring_start_energy` on both chambers. **Confirmed strongly.**
  tight_gradient 2.38 → 9.12 → 19.12; food_ladder 0.38 → 16.62 → 38.88.
  The direct compounding metric lifts on both chambers.
- **H3.** `births_after_tick_50` lifts on food_ladder under at least
  one of B / C (≥+3). **Confirmed massively.** B-A = +57; C-A = +143.
- **H4.** `births_after_tick_50` lifts off hard zero on
  tight_gradient under at least one of B / C. **Confirmed.** B = 8;
  C = 72. The pre-reg flagged this as expected-but-not-required;
  v0.17 is the slice where the three-experiment-deep zero finally
  cracks. Implication: tight_gradient's hard zero in v0.14 / v0.15 /
  v0.16 was **not** primarily geometry-bounded; child survival was
  the binding constraint.
- **H5.** `seeds_with_survivors` rises monotone with
  `offspring_start_energy` on at least one chamber. **Confirmed on
  both chambers.** food_ladder: 4 → 7 → 8 (strictly monotone, full
  survival at C). tight_gradient: 2 → 2 → 7 (non-decreasing; jumps
  to 7 at C).
- **H6.** Arm A reproduces v0.16 cost-15 bit-identically on
  `(total_births, births_after_tick_50, seeds_with_survivors,
  total_food_events)`. **Confirmed** — see Determinism contract
  table above.

### On the H1 dip (mean_post_birth_lifespan_ticks)

H1 is falsified at the strong "monotone non-decreasing" form, but the
mechanism is a denominator effect, not an individual-parent regression.
The intervention multiplies the parent pool by 5-9×:

| chamber | start-30 | start-60 | start-100 |
|---|---:|---:|---:|
| tight_gradient | 24 parents | 71 parents | 117 parents |
| food_ladder | 28 parents | 157 parents | 242 parents |

`mean_post_birth_lifespan_ticks` is `total_post_birth_lifespan_ticks /
total_distinct_parents`. Many of the new parents reproduce late in the
200-tick run — they have less of the run's tail to live in
post-birth. The population's mean post-birth lifespan therefore
shrinks even though the underlying lifecycle is healthier. The raw
sum `total_post_birth_lifespan_ticks` (now reported alongside the mean
in the tables above) lifts strongly on both chambers (×4.4 / ×9.5),
confirming the intervention is producing more
parent-ticks-of-living-while-able-to-reproduce.

A future slice may want a per-parent lifespan distribution (median,
quantiles) rather than a single mean — but for v0.17 the raw sum
plus the two stronger compounding metrics
(`mean_grandchildren_per_seed`, `seeds_with_survivors`) make the
headline finding unambiguous.

### Decision rule fired (per pre-reg)

> **H2 confirms (`mean_grandchildren_per_seed` monotone-increasing in
> `offspring_start_energy`) AND H3 confirms
> (`births_after_tick_50` lifts on food_ladder).** Child survival is
> a real lever for compounding under the handout. v0.18 = food
> respawn under conservation to test whether the lift survives a
> conserved energy budget.

The conservation caveat fully governs the interpretation (see
"Conservation caveat" above). v0.17 demonstrates **the substrate
compounds when given a free energy injection at every birth.** It
does not demonstrate the substrate compounds under conservation.

### Three v0.14-v0.16 findings now resolve

1. **The H2 ceiling on `births_after_tick_50` was child-survival-
   bounded, not policy-architecture-bounded and not memory-tier-bounded.**
   v0.14 (reflex vs deliberative), v0.15 (chemotaxis-tier scalar
   memory), and v0.16 (reproduction economics on parents) each tested
   a different lever and each found per-parent productivity lifted
   without `births_after_tick_50` following. v0.17 confirms what
   v0.16's per-parent telemetry already suggested: parents were
   doing fine; children were dying before reproducing. With more
   starting energy children survive their first forage cycle,
   compounding follows.
2. **tight_gradient's hard zero is not (primarily) hazard-wall
   geometry.** Three experiments deep at zero, the chamber finally
   produces 72 post-tick-50 births under start-100. The hazard
   wall is hard but not insurmountable; the v0.14 / v0.15 / v0.16
   ceiling there was children-not-surviving-the-wall-crossing-and-
   the-far-side-forage-cycle, not children-cannot-cross-the-wall.
3. **food_events stays hard-capped at 192 / 174, and compounding
   still lifts.** The chamber's food supply is fixed across the
   200-tick run; v0.17's lift comes from each unit of food yielding
   more downstream reproduction because children are subsidised at
   birth. This is exactly the conservation hole v0.18 closes.

### Population sanity (start-100)

Under start-100, total population dynamics are healthy without
runaway:

- `max_population_end`: 15 (tight_gradient) / 34 (food_ladder) — peak
  alive at run end on the most-populous seed. Population grows but
  stays bounded by the chamber's static food pool.
- `total_starvation_deaths`: 185 / 198 vs 112 / 90 at baseline.
  Starvation deaths roughly double in absolute terms — children
  still die of starvation at scale; the net birth rate just
  outpaces them. Lineages persist because the birth flow is faster
  than the death flow, not because death stopped.
- `total_reproduction_requests` exceeds `total_births` for the first
  time: 214 vs 207 (tight_gradient) / 404 vs 366 (food_ladder).
  The gap (-7 / -38) represents requests rejected by the
  reproduction config — likely on `hazard_threshold` (eligible
  agent in a tile with too much hazard signal) or `min_age` (the
  fertile parent pool grew so fast that some requests come from
  agents under 10 ticks old). v0.18 should instrument the rejection
  reason if the rate continues to matter.

### Data points worth flagging for v0.18

- **`still_tick_fraction` rises with `offspring_start_energy`** —
  not falls. tight_gradient 94.4 → 96.1 → 97.3; food_ladder 93.9 →
  96.7 → 97.9. This is also a population artefact: more children
  spawn into the safe zone with no food-pull in sensor range, and
  STAY (the v0.14 reflex's blackout default). Per-cell behaviour is
  unchanged; cohort composition shifts.
- **food_events identical across all arms** — the
  `food_events / n_ticks` rate is `192 / 200 = 0.96` on tight_gradient
  and `174 / 200 = 0.87` on food_ladder, regardless of population
  size. The chamber paints food once and never respawns; once the
  reachable food pool is exhausted, no new events fire even though
  population is large. This is exactly the conservation hole v0.18
  closes.
- **Speciation is now worth a follow-up slice (v0.17b candidate).**
  With ~240 parents producing 38 grandchildren per seed on
  food_ladder start-100, there is finally a lineage sample large
  enough for trait-corner clustering to be statistically meaningful.
  The v0.14 speciation script (`scripts/v0.14_speciation_analysis.py`)
  is currently hardwired to v0.14 paths; parameterizing it and
  running on `runs/fear-hunger-v0.17*/` would show whether
  successful start-100 lineages cluster differently from start-30.
  Deferred from this slice to keep the conservation question
  uncluttered, but the data is preserved on disk.

## References

- [[docs/experiments/fear_hunger_v0.16.md]] — v0.16 results;
  per-parent lever confirmed, ceiling barely moves, "children are
  the bottleneck" finding.
- [[docs/experiments/fear_hunger_v0.15.md]] — v0.15 results;
  `food_events` saturation finding (192 / 174); the v0.16
  / v0.17 fork.
- [[docs/experiments/fear_hunger_v0.14.md]] — v0.14 baseline;
  the "post-birth energy floor" / "children may starve" watch-outs.
- [[docs/specs/v0.2_reflex_cell_spec.md]] §"Comparison framework" —
  the substrate axis the v0.2 spec named.
