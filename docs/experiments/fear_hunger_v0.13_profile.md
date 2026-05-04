# Fear-Hunger Chamber — v0.13 Phase 1 profile (memory-channel calibration)

**Phase:** 1 of 2 (read-only diagnostic; no `core/` math change)
**Branch:** `claude/v0.13-memory-channel-calibration`
**Date:** 2026-05-04
**Outputs:** `runs/fear-hunger-v0.13-profile/traces.md`,
this document, and one new script
[[scripts/v0.13_profile.py]].

## Question

v0.12 found that action-aware directional memory is causally
influential (argmax sway 1.1–16.4 % across cells, vs. 0.0 % in v0.11)
but mostly *maladaptive*: 49 % of swayed decisions on tight_gradient
were `EAT -> MOVE_*`. Two competing hypotheses for the
substrate-up-births-flat ceiling:

- **H1 — wiring asymmetry.** `novelty_pleasure` is mis-scaled and
  un-gated relative to its peer pleasure terms. `MOVE_*` candidates
  receive a memory bonus that `EAT` cannot, and `novelty_pleasure`
  has no hunger-gating while `anticipated_food_pleasure` does.
- **H2 — late-stage stall.** Births cluster in a first burst then
  stop; reproduction economics or 200-tick budget cap headline gains
  irrespective of representation.

Phase 1 profiles both with the existing v0.12 codebase. Phase 2 (see
[[docs/experiments/fear_hunger_v0.13.md]]) ships the wiring fix only
if Phase 1 supports H1.

## Setup

Identical to v0.12 in every respect except instrumentation:

- Three scenario traces, computed by walking the v0.12 directional
  cells with the existing harness and dumping `breakdown.details` for
  every valid candidate action at the matching tick. Trace 1 is
  swept across seeds 1..8 looking for a real "swayed-on-food" capture
  (where with-memory argmax differs from no-memory argmax). Traces 2
  and 3 are synthetic — agent state hand-set to isolate the H1
  fingerprint.
- One by-tick birth-distribution histogram across the v0.12b
  food_ladder winner cell, the v0.12b mem-off baseline (control),
  and the v0.12a tight_gradient ms1-md0.1 cell, all 8 seeds. Read
  from existing `events.jsonl` artifacts; no re-run.

## Results

### Trace 1 — hungry agent on food (organic capture)

Three variants on the same scenario differ only in cell parameters
and chamber. The smoking gun for H1 lives in **trace 1b** and
**trace 1c**.

#### Trace 1a: ms1-md0.1 (winner), food_ladder, seed=1, tick=2

| action     | total_proj | total_zero |   Δ   | novelty_pleasure | eating_pleasure |
|------------|-----------:|-----------:|------:|-----------------:|----------------:|
| STAY       |     -1.387 |     -1.387 | +0.00 |             0.00 |            0.00 |
| MOVE_EAST  |     -5.205 |     -5.479 | +0.27 |             0.30 |            0.00 |
| MOVE_WEST  |      7.023 |      7.023 | +0.00 |             0.00 |            0.00 |
| **EAT**    |  **10.946**|  **10.946**| +0.00 |             0.00 |       **11.93** |

Agent: `pos=(4,0) energy=55.4 hunger=0.45 on_food=True
pleasure_tendency=[N=0.00 S=0.00 E=0.73 W=0.00]`.

**EAT wins decisively.** At slow EMA (`memory_strength_min=1.0`,
`alpha=0.05`) the east-tendency hasn't built up by tick 2; memory's
contribution to MOVE_EAST is 0.30 vs eating_pleasure 11.93. No
override. This matches the v0.12 transition profile for the winner
(only 5 EAT->MOVE_EAST swayed decisions across 8 seeds × 200 ticks).

#### Trace 1b: ms0-md0.1 (fast EMA), food_ladder, seed=2, tick=11 — **swayed-on-food**

| action     | total_proj | total_zero |    Δ   | novelty_pleasure | eating_pleasure |
|------------|-----------:|-----------:|-------:|-----------------:|----------------:|
| STAY       |     -2.329 |     -2.329 |  +0.00 |             0.00 |            0.00 |
| MOVE_NORTH |      3.847 |      3.847 |  +0.00 |             0.00 |            0.00 |
| MOVE_SOUTH |     -4.995 |     -4.995 |  +0.00 |             0.00 |            0.00 |
| **MOVE_EAST** |  **37.387** |   -7.309 | **+44.70** |       **44.96** |        0.00 |
| MOVE_WEST  |      8.775 |      8.775 |  +0.00 |             0.00 |            0.00 |
| EAT        |     15.691 |     15.691 |  +0.00 |             0.00 |           17.68 |

Agent: `pos=(4,1) energy=47.4 hunger=0.53 on_food=True
pleasure_tendency=[E=29.09]`.

**Memory swayed argmax from EAT to MOVE_EAST.** With memory zeroed
EAT wins at 15.69 (vs MOVE_EAST=-7.31). With the projection, MOVE_EAST
scores 37.39 — `novelty_pleasure=44.96` overrides
`eating_pleasure=17.68` by ~2.5×. This is **H1's load-bearing
fingerprint**: the agent is hungry, on food, and memory pulls it off
food into a direction with no actual food signal.

The east-tendency is 29.09 because at fast EMA (`alpha=0.95`) every
move-east-then-eat cycle pumps roughly the full pleasure breakdown
into the slot, with only a 10 %-per-tick decay countering it.

#### Trace 1c: ms0-md0.1 (fast EMA), tight_gradient, seed=2024, tick=39 — **swayed-on-food**

| action     |     total_proj |     total_zero |          Δ | novelty_pleasure | eating_pleasure |
|------------|---------------:|---------------:|-----------:|-----------------:|----------------:|
| STAY       |         -1.201 |         -1.201 |     +0.00  |             0.00 |            0.00 |
| MOVE_NORTH |          6.503 |          6.503 |     +0.00  |             0.00 |            0.00 |
| MOVE_SOUTH |         -3.172 |         -3.172 |     +0.00  |             0.00 |            0.00 |
| **MOVE_EAST** | **1280.981** |          4.366 | **+1276.62** |    **1276.71** |            0.00 |
| MOVE_WEST  |         83.868 |         -3.531 |    +87.40  |            87.43 |            0.00 |
| EAT        |         37.809 |         37.809 |     +0.00  |             0.00 |           38.70 |

Agent: `pos=(6,1) energy=2.0 (1.0% remaining) hunger=0.98 on_food=True
pleasure_tendency=[E=680.42 W=46.59]`.

**Pathological.** The east-tendency has compounded to 680 over 39
ticks of fast EMA. With novelty_pleasure scaled at 1276.71, MOVE_EAST
beats EAT (38.70) by ~33×. The agent is one tick from starvation —
energy=2.0 with hunger=0.98 — sitting on food, and memory tells it to
walk east. There is no semantic check on memory_score magnitude; the
EMA can grow without bound in dense-feedback regimes.

This is the most extreme example of the asymmetry: in a tightly
constrained chamber, the bare directional signal accumulates faster
than it decays, and `novelty_pleasure` becomes the dominant term in
the harness — uncoupled from any actual food contact.

### Trace 2 — hungry agent off food, food visible east, memory pointing east (synthetic)

| action      | total_proj | total_zero |    Δ   | novelty_pleasure | anticipated_food_pleasure | safety_pleasure |
|-------------|-----------:|-----------:|-------:|-----------------:|--------------------------:|----------------:|
| STAY        |    -18.770 |    -18.770 |  +0.00 |             0.00 |                      0.00 |            0.00 |
| MOVE_NORTH  |    -11.373 |    -11.373 |  +0.00 |             0.00 |                      0.00 |            8.71 |
| MOVE_SOUTH  |    -21.210 |    -21.210 |  +0.00 |             0.00 |                      0.00 |            0.00 |
| **MOVE_EAST** | **121.795** | 114.342 |  +7.45 |             7.45 |                     52.24 |           69.66 |
| MOVE_WEST   |    -22.339 |    -22.339 |  +0.00 |             0.00 |                      0.00 |            0.00 |

Agent: `pos=(8,3) energy=25.0 hunger=0.75 on_hazard=True
pleasure_tendency=[E=8.00]`.

**Memory adds coherently to anticipated food.** MOVE_EAST is correct
(food is east; agent is hungry). With or without memory, MOVE_EAST
wins by a wide margin. Memory's +7.45 contribution is small relative
to anticipated_food_pleasure=52.24 + safety_pleasure=69.66 — it
nudges in the right direction without distorting. This is the
**case where memory is supposed to help**, and it does.

### Trace 3 — sated agent off food, memory pointing east (synthetic)

| action      | total_proj | total_zero |    Δ   | novelty_pleasure | anticipated_food_pleasure |
|-------------|-----------:|-----------:|-------:|-----------------:|--------------------------:|
| **STAY (zero-mem winner)** |  -0.271 |  -0.271 | +0.00 |    0.00 |                      0.00 |
| MOVE_NORTH  |     -2.711 |     -2.711 |  +0.00 |             0.00 |                      0.00 |
| MOVE_SOUTH  |     -2.711 |     -2.711 |  +0.00 |             0.00 |                      0.00 |
| **MOVE_EAST (proj winner)** | **3.990** | -3.464 | **+7.45** | **7.45** |              0.00 |
| MOVE_WEST   |     -2.711 |     -2.711 |  +0.00 |             0.00 |                      0.00 |

Agent: `pos=(2,3) energy=100.0 hunger=0.00 on_safe=True
pleasure_tendency=[E=8.00]`.

**The missing-hunger-gate fingerprint.** A sated agent in the safe
zone with all four MOVE_* options scoring -2.71 (movement cost) and
STAY scoring -0.27 (idle metabolism). Without memory, STAY wins
correctly — the agent should sit and conserve. With memory's
projected contribution, MOVE_EAST gets `novelty_pleasure=7.45`
(unconditionally on memory state, **no hunger gating**), bumping its
total to +3.99 and beating STAY. The sated agent walks toward
remembered-good when it has no metabolic reason to.

`anticipated_food_pleasure` correctly silences itself here because
of its `* obs_before.hunger_level` gate (hunger_level=0.0). The
`novelty_pleasure` lacks that gate; it remains at full strength
regardless of how full the agent is.

### By-tick birth distribution (v0.12 winners + baseline)

```
v0.12b food_ladder ms1-md0.1 (winner) — 8 seeds
   0– 24 | 4 ####
  25– 49 | 1 #
  50–199 | 0
  total | 5

v0.12b food_ladder mem-off (baseline) — 8 seeds
   0– 24 | 4 ####
  25– 49 | 1 #
  50–199 | 0
  total | 5

v0.12a tight_gradient ms1-md0.1 — 8 seeds
   0– 24 | 1 #
  25–199 | 0
  total | 1
```

**100 % of births fall in the first 50 ticks** across both v0.12b
food_ladder cells (winner + baseline) and v0.12a tight_gradient.
**No births occur in ticks 50–199** anywhere in the v0.12 sweep.
The histogram is a clean step function: founders reproduce once
during the initial energy-rich window, then nothing.

This is **H2's signature** independent of the memory question:
something about the post-first-birth state — energy distribution,
crowding, or trait composition of the surviving pool — prevents
subsequent reproduction even in the positive-control chamber. The
fact that the **mem-off baseline shows the exact same histogram**
rules out memory as the late-stage cause; the ceiling is architectural.

## Diagnosis

**H1 is confirmed.** Trace 1b shows the EAT-override at moderate
hunger and a medium-fast EMA — exactly the pattern v0.12's
transition counts indicated. Trace 1c shows the same pathology in an
extreme regime where the EMA has compounded to 680 and `novelty_pleasure`
dominates the harness by orders of magnitude. Trace 3 isolates the
hunger-gating asymmetry as the structural cause: without a hunger
gate, `novelty_pleasure` retains full strength on a sated agent
while `anticipated_food_pleasure` correctly goes silent.

**H2 is independently confirmed.** The birth-distribution histograms
are step functions: 5/5 v0.12b winner births in the first 50 ticks,
then zero for 150 ticks. The mem-off baseline shows the same
distribution, so memory representation is not what gates late-stage
reproduction.

**Phase 2 should ship**, but with realistic expectations: the
hunger-gate fix addresses H1 only. The headline-births question is
answered by H2 and will require a separate slice (v0.14 candidate:
extend the tick budget, profile post-first-birth energy and
crowding, or revisit reproduction economics). Phase 2's success
metric should therefore be:

1. EAT->MOVE_* transition counts drop substantially across all cells
   (the load-bearing diagnostic).
2. `argmax_change_rate` drops on tight_gradient where the regression
   was worst.
3. Substrate metrics (food_events, repeat_food_visits) match or
   exceed v0.12 winners.

Phase 2 is **not** expected to lift `total_births` past baseline —
H2 is the binding ceiling there. We log that as the v0.14 hand-off.

## Pre-registered failure-mapping branch fired

> **`novelty_pleasure(MOVE_*) >> eating_pleasure(EAT)` in trace 1**
> → H1 confirmed mechanically. Proceed to Phase 2 with the
> hunger-gate fix.

Trace 1b: novelty_pleasure on MOVE_EAST = 44.96 vs eating_pleasure
on EAT = 17.68 (~2.5×).
Trace 1c: novelty_pleasure on MOVE_EAST = 1276.71 vs eating_pleasure
on EAT = 38.70 (~33×).

The leading candidate fix from the pre-reg —
`novelty_pleasure *= obs_before.hunger_level` — is the right
intervention. We proceed to Phase 2.

## What changed

- [[scripts/v0.13_profile.py]] (new) — read-only profiler. Sweeps
  seeds 1..8 across three trace-1 variants (ms1+food_ladder,
  ms0+food_ladder, ms0+tight_gradient) preferring "swayed-on-food"
  captures, synthesizes traces 2 + 3, and reads existing
  `events.jsonl` to histogram by-tick births. Renders every
  breakdown at match time so subsequent ticks cannot mutate the
  captured agent's state. Output:
  `runs/fear-hunger-v0.13-profile/traces.md`.
- This document — Phase 1 results write-up.

No changes to: `core/`, `policies/`, tests, or any prior experiment.
Phase 1 is read-only by design.

## Reproducing

```bash
uv run python scripts/v0.13_profile.py
# wrote runs/fear-hunger-v0.13-profile/traces.md
#   131 lines
```

## Next step

Phase 2: implement the hunger-gate fix in [[src/hedonism_harness/core/valence.py]]
(one-line change to `novelty_pleasure`), add the regression tests
called out in the v0.13 pre-reg's "What changed" section, re-run the
v0.12 directional sweep on both chambers, and write up the result
in `docs/experiments/fear_hunger_v0.13.md` (currently the
pre-registration; will be updated post-Phase-2 with results).
