# v0.15 — chemotaxis-style scalar memory under reflex cell

**Status:** pre-registration; not yet executed.
**Date:** 2026-05-04
**Branch:** `claude/v0.15-scalar-memory`
**Predecessor:** v0.14 (reflex-cell substrate, first compounding result; see
[[docs/experiments/fear_hunger_v0.14.md]]).
**Spec:** [[docs/specs/v0.2_reflex_cell_spec.md]] §"Memory" (deferred slot).

## Question

Does adding *minimal*, biologically-honest memory to the v0.14 reflex cell
lift compounding past the v0.14 ceiling (3 post-tick-50 births on
`food_ladder`; 0 on `tight_gradient`)? Specifically: does giving the cell
a one-tick concentration comparator plus last-move persistence let it keep
walking a previously-rewarding direction during a sensor blackout, instead
of freezing into STAY?

## Background

v0.14 found that the reflex-cell substrate breaks the v0.13 H2 ceiling on
`food_ladder` (3 post-tick-50 births vs 0 for both deliberative arms) and
produces the first surviving lineages of the project (2 on `tight_gradient`,
4 on `food_ladder`). Compounding on `tight_gradient` remains 0 under any
arm. The v0.14 reflex cell freezes into STAY whenever no direction has
strictly-positive net pull — i.e. whenever no food is in sensor range.
This is the v0.15 target.

## Memory budget — scale-graded

The project's memory budget is graded by entity scale, not maximised at every
scale. v0.15 adopts the prokaryotic chemotaxis tier:

| scale | memory | mechanism |
|---|---|---|
| reflex cell (v0.2 / this slice) | 1 scalar + last move direction | derivative comparator + run/tumble |
| multi-cell colony (later) | 4-vector directional EMA | what v0.11 / v0.13 modelled |
| organism with neural tissue (much later) | spatial map | what v0.7..v0.10 `ValenceMemory` modelled |

A directional EMA at the cell tier overstates the entity's biology. v0.15
gives the cell the minimum that yields directional behaviour: a scalar
record of "how strong was the food signal a moment ago" and a record of
"which way did I just move."

## Mechanism

### State (`ScalarMemory`, new in `core/memory.py`)

```
@dataclass
class ScalarMemory:
    last_total_food_signal: float   # sum of obs.food_signal_{n,s,e,w} at last tick.
    last_move_action: Action        # the action selected last tick (defaults Action.STAY).
```

Two fields. No EMA, no spatial map, no per-direction history. The cell
carries one float and one categorical of state.

### Update (`HHAgent.step`, after `commit_delta`)

```
total = obs.food_signal_n + obs.food_signal_s + obs.food_signal_e + obs.food_signal_w
memory.last_total_food_signal = total
memory.last_move_action = decision.action
```

The update reads the *pre-action* observation (the same `ctx.observation`
the policy decided from), so the comparator captures "what the cell sensed
when it chose this action." Mirrors how `ValenceMemory` updates against
`result.body.{x,y}` post-action — the right reference frame for "did the
last decision improve the situation."

### Decision (`GradientPolicy.decide`)

The v0.14 gradient computation runs unchanged. The new branches fire
**only when `best_net == 0`** — i.e. only in the sensor-blackout case
that v0.14 resolves into STAY. Inside that branch:

```
current_total = obs.food_signal_n + ... + obs.food_signal_w
dS = current_total - memory.last_total_food_signal

# Sated veto: a sated cell does not waste energy in a blackout.
if obs.hunger_level <= 0.0:
    return STAY

if dS >= 0 and memory.last_move_action in MOVE_ACTIONS:
    return memory.last_move_action   # persist (run)
elif dS < 0:
    return tumble(rng, valid_moves) # random direction (uniform)
else:
    return STAY                  # no info, no recent info -> rest
```

`tumble(rng, valid_moves)` samples uniformly from the valid MOVE actions at
the agent's current cell (in-bounds, not occupied). If no MOVE is valid
the cell STAYs. The tumble bypasses the gradient but is bounded by the
existing `get_valid_actions` set, so the determinism contract is unchanged.

### Hunger gate — hard sated veto

A sated cell (`hunger_level <= 0`) STAYs in the blackout case rather than
running or tumbling. This is energy economy, not biology — real bacteria
chemotax continuously. The gate aligns with v0.13's `novelty_pleasure`
hunger-gate philosophy: trait-modulated channels should not override
substrate energy economy when there is nothing to gain. The gate is a
**hard sated veto**, not a multiplicative tumble probability — the cleaner
shape for this slice. A probabilistic / multiplicative gate is deferred
unless H4 evidence requires it.

### What the v0.14 cell does NOT change

- `best_net > 0` branch: pure v0.14. Strictly-positive gradients still win.
- Auto-EAT reflex on food: pure v0.14.
- STAY default: pure v0.14 when `dS == 0` and no last move.
- Auto-reproduction substrate phase: pure v0.14.
- Trait coefficients (`pleasure_sensitivity`, `fear_sensitivity`,
  `risk_tolerance`): pure v0.14. No new trait field.

`memory_strength` and `memory_decay_rate` are inert under v0.15
`ScalarMemory` (the scalar has no decay; one-tick lag is already the
shortest possible window). Same status as in v0.14: they mutate across
generations and remain in lineage records but do not affect this slice.

## Arms

Three arms on each chamber. Eight seeds per (arm, chamber). 200 ticks,
5 founders, identical trait config to v0.14. 3 × 2 × 8 = 48 runs.

| arm | policy | scalar memory | label |
|---|---|---|---|
| A | GradientPolicy + auto-reproduction | none | reflex-baseline (= v0.14 reflex-auto) |
| B | GradientPolicy + auto-reproduction | persistence only | reflex-persistence |
| C | GradientPolicy + auto-reproduction | persistence + derivative-tumble | reflex-chemotaxis |

Arm A reproduces v0.14 reflex-auto bit-identically — one of the v0.15
correctness contracts.

Arm B is "run while gradient pull is zero, never tumble." The blackout
branch returns `last_move_action` regardless of `dS`. Tests whether
persistence alone carries any compounding effect.

Arm C is the full chemotaxis story. Run while improving or steady; tumble
while worsening. Tests whether the derivative comparator adds value over
pure persistence.

The B-vs-A and C-vs-B contrasts isolate the two mechanism components:
B-A = persistence effect; C-B = derivative-tumble effect.

## Pre-registered hypotheses

- **H1.** `births_after_tick_50` C > A on `food_ladder`. The chemotaxis
  cell finds and re-finds food cells better than the v0.14 reflex cell;
  more compounding follows.
- **H2.** `births_after_tick_50` C > A on `tight_gradient`. The hazard wall
  ceiling is partly information-bounded — the cell needs to know when to
  give up and reorient.
- **H3.** B carries some of C's effect. Pure persistence is non-trivial
  even without a derivative comparator (`B - A > 0` on `births_after_tick_50`).
- **H4.** `still_tick_fraction` decreases under B and C vs A; the magnitude
  of decrease is bounded (cells should not flail). A drop from ≈92% under A
  to ≈70-85% under B/C is the expected band.
- **H5.** Determinism contract: arm A reproduces v0.14 reflex-auto results
  bit-identically (same `total_births`, `births_after_tick_50`,
  `seeds_with_survivors` cell-by-cell when scalar memory is `None`).

## Headline metrics

- `total_births`
- `seeds_with_any_births`
- `births_after_tick_50` — the ceiling test from v0.13 / v0.14.
- `seeds_with_survivors` at run end.
- `still_tick_fraction` — action == STAY rate per agent-tick.
- `move_after_blackout_fraction` — fraction of ticks where the cell moved
  via a scalar-memory branch (i.e. `best_net == 0` triggered persistence
  or tumble). v0.15-specific instrumentation.
- `food_events`, `hazard_entries`, `starvation_deaths`,
  `reproduction_requests` (carried forward from v0.14 for continuity).

## Decision rules

- **C > A on `births_after_tick_50` for at least one chamber.**
  Chemotaxis-tier scalar memory is sufficient at the cell scale. v0.16:
  scale richness on the substrate axis (chamber variants, more chambers,
  multi-founder topologies). Memory tier stays at scalar until the
  organism scale demands more.

- **C ≈ A across both chambers (no lift).** Cell-tier memory is not
  load-bearing for compounding under the current substrate. Two
  interpretations:
  - The chambers are the binding constraint (geometry / hazard wall /
    reproduction economics). v0.16: substrate variants under arm A.
  - The memory tier is mismatched. v0.16 (alternate): jump to multi-cell
    tier (directional EMA) and re-test.

- **B ≈ C >> A.** Persistence carries the effect; the derivative is not
  load-bearing. Simplifies v0.16: drop the derivative branch, keep
  persistence, document.

- **C < A (regression).** Chemotaxis induces wandering away from food. The
  `dS >= 0` persistence criterion is too permissive (a steady-zero blackout
  satisfies it and the cell runs into nothing). v0.16: tighten the criterion
  to require `dS > 0` strict, OR add a "give up after N ticks of zero" cap.

- **`move_after_blackout_fraction` near zero in arms B and C.** The new
  mechanism is not firing; check the `best_net == 0` condition. Likely a
  bug, not an experimental finding.

## Out of scope (v0.15)

- EMA windows beyond one-tick lag.
- Spatial maps.
- Directional EMA per cardinal (= multi-cell tier; deferred to v0.20+).
- New trait fields. The v0.14 trait schema is fixed for this slice.
- Hunger-gate refinements (sigmoid, multiplicative tumble probability,
  threshold-based, etc.) — the v0.15 default is a hard sated veto;
  revisit only if H4 shows the cell flails when sated.
- Receptor-level methylation analog. Over-engineering at the cell scale.
- Reintroducing `memory_strength` / `memory_decay_rate` as live trait
  modulators — they remain inert in v0.15 (the scalar lag has no rate).
- Multi-cell interactions, energy transfer, signalling.
- HedonismPolicy modifications. The deliberative branch stays quarantined.

## Implementation notes

### File-level changes

- Modify: `src/hedonism_harness/core/memory.py` — add `ScalarMemory`
  dataclass, `make_scalar_memory()`, `update_scalar()` alongside the
  existing `ValenceMemory` / `DirectionalMemory` machinery.
  `ScalarMemory.last_move_action` should hold an `Action` if importing
  from `core.actions` is clean; if a circular import surfaces, fall back
  to a small enum-safe value (e.g. the action's int code) and document
  the reason at the import site.
- New: `src/hedonism_harness/policies/gradient_policy.py` blackout branch
  (~25 LOC additional).
- Modify: `src/hedonism_harness/model.py` — `MEMORY_TYPE_SCALAR =
  "scalar"` constant; extend `_make_memory_for_spec` and
  `_process_birth_queue`'s child-memory dispatch.
- Modify: `src/hedonism_harness/mesa_agents.py` — extend the post-action
  memory update with a `ScalarMemory` branch (mirror of the existing
  `ValenceMemory` / `DirectionalMemory` branches in `step()`).
- Modify: `src/hedonism_harness/experiments/comparison_grid.py` — extend
  `Arm` with a `memory_type` field; add `reflex-persistence` and
  `reflex-chemotaxis` arm definitions; thread `memory_type` through
  `_run_one_arm_seed`.
- New: `tests/test_scalar_memory.py` — `ScalarMemory` unit tests
  (construction, update, persistence semantics).
- New: `tests/test_gradient_policy_scalar_memory.py` — policy decision
  tests (blackout-branch firing, persistence, tumble, hunger-gate, sated
  STAY, B-vs-C contrast).
- Modify: `src/hedonism_harness/policies/__init__.py` — no change
  (GradientPolicy already exported).

### Determinism contract

Arm A (no scalar memory) must reproduce v0.14 reflex-auto bit-identically.
Verified by re-running `runs/fear-hunger-v0.14a/` and `v0.14b/` arm-C
seeds and asserting equality of per-seed `(total_births,
births_after_tick_50, seeds_with_survivors)` triples.

The tumble RNG draw uses `ctx.rng` (the agent-level RNG) so the
decision remains a pure function of `(observation, traits, memory, rng)`.
Tumble does not consult `model.streams` directly; the same
agent-RNG-derived sequence is used as for existing tie-breaks.

### LOC estimate

- `ScalarMemory` + helpers: ~30 LOC.
- `GradientPolicy` blackout branch: ~25 LOC.
- `mesa_agents.py` memory update: ~15 LOC.
- `model.py` memory factory: ~10 LOC.
- `comparison_grid.py` arm extension: ~30 LOC.
- New tests: ~250 LOC.

Total v0.15 implementation: ~360 LOC. Comparable to v0.13.

## Results (executed 2026-05-04)

Three arms × two chambers × eight seeds (1..8) × 200 ticks × 5 founders.
48 runs total. Substrate parameters held identical to v0.14
(`energy_threshold=50.0`, `energy_cost=35.0`, `unbounded_mutation=True`,
no archetype injection).

### v0.15a tight_gradient

| arm | total_births | birth>50 | survivors | food_events | still% |
|---|---:|---:|---:|---:|---:|
| reflex-baseline (A) | 47 | 0 | 2/8 | 192 | 92.0 |
| reflex-persistence (B) | 46 | 0 | 1/8 | 192 | 91.7 |
| reflex-chemotaxis (C) | 52 | 0 | 1/8 | 192 | 89.4 |

C-A: total_births +5; **births_after_tick_50: 0 vs 0 (no lift)**;
survivors -1; food_events identical; still% -2.6 pp.
B-A: total_births -1; survivors -1; still% -0.3 pp.

### v0.15b food_ladder

| arm | total_births | birth>50 | survivors | food_events | still% |
|---|---:|---:|---:|---:|---:|
| reflex-baseline (A) | 39 | 3 | 4/8 | 174 | 91.4 |
| reflex-persistence (B) | 38 | 4 | 3/8 | 174 | 91.5 |
| reflex-chemotaxis (C) | 54 | 3 | 4/8 | 174 | 88.1 |

C-A: total_births +15 (≈+38%); **births_after_tick_50: 3 vs 3 (no
lift)**; survivors identical; food_events identical; still% -3.3 pp.
B-A: total_births -1; births_after_tick_50 +1 (4 vs 3) — single-event
delta on n=8, not load-bearing; survivors -1.

### Hypotheses → outcomes

- **H1.** `births_after_tick_50` C > A on food_ladder. **Falsified.**
  C and A both produce 3.
- **H2.** `births_after_tick_50` C > A on tight_gradient.
  **Falsified.** Both 0.
- **H3.** B carries some of C's effect. **Vacuous given H1/H2** —
  there is no positive effect to apportion. B's tight_gradient and
  food_ladder total_births sit within ±1 of A.
- **H4.** `still_tick_fraction` decreases under B/C vs A; magnitude
  bounded. **Confirmed for C.** -2.6 pp (tight_gradient), -3.3 pp
  (food_ladder). B is essentially flat (-0.3 / +0.1 pp).
- **H5.** Arm A reproduces v0.14 reflex-auto bit-identically.
  **Confirmed against current `claude/v0.14-reflex-cell` code.** Fresh
  re-run of v0.14 ARMS reflex-auto on `food_ladder` from current HEAD
  yields the same `(39, 3, 4/8, 174, 91.40%)` triple as v0.15
  reflex-baseline. (See "Determinism note" below — the numbers in
  [[docs/experiments/fear_hunger_v0.14.md]] published-baseline table
  are 35/91.7 on food_ladder; current code reproduces 39/91.40 from
  the same seeds. The discrepancy predates v0.15; v0.15 introduces no
  new determinism break.)

### Determinism note

The `claude/v0.14-reflex-cell` published baseline reports
food_ladder reflex-auto as 35 total_births / 91.7% still. A
re-execution from current HEAD (commit `ae25d63` immediately
post-v0.14 merge) reproduces 39 / 91.40%. tight_gradient reflex-auto
matches exactly (47 / 92.0%). All v0.15 arms execute against the same
HEAD code, so the v0.14-vs-v0.15 contrasts above are sound; the
mismatch is between the v0.14 published table and the v0.14 code as
committed, not between v0.15 and v0.14 code. Worth investigating
later as a v0.14-time provenance question; not blocking for v0.15.

### Headline finding

**Cell-tier scalar memory does not break the v0.14 H2 compounding
ceiling on either chamber.** Chemotaxis materially increases foraging
activity (+15 total_births on food_ladder, ≈+38%; -3.3 pp still%) but
the additional births do not survive into the post-tick-50 generation
window. food_events are identical across arms (192 / 174) — the
foraging itself was not constrained by the v0.14 cell's ability to
find food; what's constrained is what happens *after* a successful
forager reproduces.

Two consequences:

1. The chemotaxis cell does forage better. The +15 births on
   food_ladder under chemotaxis vs baseline isn't noise — it's a real
   foraging gain that lifts first-generation reproduction. Cells
   reach food faster, hit the energy threshold earlier, and queue
   more first births. But the children die before reproducing
   themselves.

2. The H2 ceiling is not a memory-tier mismatch under the current
   substrate. A scalar comparator + persistence/tumble does what
   bacteria do; the cell now *sees* gradients across blackouts. It
   still cannot push past the post-tick-50 wall. The wall is not
   "the cell freezes when food is out of range." It's something else.

### Decision rule fired (per pre-reg)

> **C ≈ A across both chambers (no lift).** Cell-tier memory is not
> load-bearing for compounding under the current substrate.

The pre-reg's two interpretations both stand and are not yet
distinguishable from this slice alone:

- (i) Chambers are the binding constraint (geometry / hazard wall /
  reproduction economics).
- (ii) Memory tier is mismatched at this entity scale.

### Data points worth flagging for v0.16

- **food_events identical across arms.** The number of food cells
  consumed in a 200-tick run on `food_ladder` is 174 under all three
  arms. Either the chamber's food supply is exhausted independently
  of arm, or the consumable-food pool is small enough that any
  forager hits its ceiling fast. Worth verifying via the food_ladder
  layout's total food count.
- **+15 births on food_ladder C, no survivors lift.** The chemotaxis
  cell produces ~38% more births but the same 4/8 surviving seeds.
  Children are reproducing-and-dying without grandchildren. Suggests
  a post-birth energy floor (the v0.14 watch-out) or starvation rate
  that scales with population pressure.
- **tight_gradient still 0 birth>50 under any arm.** The hazard wall
  geometry is wrong for compounding. v0.16 substrate variants
  (chamber width, hazard damage) should test (i) cleanly.
- **Speciation analysis (`runs/fear-hunger-v0.15-speciation.md`) shows
  ≥23 successful lineages per chamber under chemotaxis vs reflex
  baseline.** No clear cluster jump in trait space; the same
  `pleasure_sensitivity ≈ 0.5..2.5`, `fear_sensitivity ≈ 0.5..2.5`,
  `risk_tolerance ≈ 0.4..0.9` band wins under both arms. Memory does
  not appear to select for a different trait corner.

### Recommendation for v0.16

Pick (i) **substrate variants** as the next slice. Cheap to run
(single-arm reflex-baseline sweep, no new mechanism), tests the most
likely binding constraint (the food_events-saturation observation
points there directly), and informs whether to revisit the
multi-cell-tier memory question afterwards.

If (i) shows compounding is geometry-bounded (e.g. wider chamber +
lower hazard damage produces post-tick-50 births), v0.17 can pick
chamber design with confidence and revisit memory at the multi-cell
tier on richer substrate.

If (i) shows compounding is *not* geometry-bounded — substrate
variants don't lift birth>50 — that's evidence the H2 ceiling is
fundamentally about reproduction economics or population dynamics,
and v0.17 targets `energy_cost`, `min_age`, or population caps.

The chemotaxis mechanism stays in the codebase; v0.16+ may keep arm C
as a parallel comparison without making it the primary axis.

## References

- [[docs/specs/v0.2_reflex_cell_spec.md]] §"Memory" — the deferred slot
  this slice fills.
- [[docs/experiments/fear_hunger_v0.14.md]] — v0.14 results; the v0.15
  baseline (and the source of the determinism-note discrepancy).
- [[docs/experiments/fear_hunger_v0.13.md]] — v0.13 hunger-gate philosophy
  carried forward.
- Berg, H. C. (2004). *E. coli in Motion.* Springer. — the run-tumble +
  receptor methylation reference for prokaryotic chemotaxis.
- Block, S. M., Segall, J. E., & Berg, H. C. (1982). "Impulse responses
  in bacterial chemotaxis." *Cell* 31, 215–226. — the time-derivative
  comparator result.
