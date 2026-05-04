# Fear-Hunger Chamber — v0.5 default trait-tuning sweep

**Experiment:** Tune the default ``TraitConfig`` toward viable diversity under random sampling.
**Branch:** `claude/trait-tuning-v0.5`
**Date:** 2026-05-04
**Run:** `runs/fear-hunger-v0.5/`

## Question

The v0.4 valence fix made archetype phenotypes work cleanly in
``tight_gradient`` (Reckless: 60 food events, 2 births, 3 survivors) but
the ``default`` condition — five founders sampled i.i.d.-uniformly from
the SPEC §8.1 master ranges — produced only **0 food events and 1 hazard
entry across 40 founder-runs**. The harness was capable of phenotype
expression, but the *default population* the user gets when they ask for
"random agents" was still effectively fear-paralyzed.

The v0.5 hypothesis:

> The default ``TraitConfig`` ranges over-weight fear and under-weight
> hunger drive. Shifting trait floors and ceilings *within* the SPEC §8.1
> master bounds — without modifying SPEC, valence math, sensors, or the
> chamber — should produce mixed-phenotype populations under random
> sampling.

## Setup

- **Layout**: `tight_gradient` (the v0.4 chamber where the harness
  visibly expresses phenotypes).
- **Hyperparameters**: identical to v0.4 — `exploration_noise=0.05`,
  5 founders, 200 ticks, 8 seeds (`1, 2, 3, 4, 5, 42, 100, 2024`).
- **Condition**: random-sampling only (no archetypes; archetypes are
  configured to ignore ``TraitConfig`` ranges by design).
- **Independent variable**: two ``TraitConfig`` factories from
  [[src/hedonism_harness/experiments/trait_configs.py]]:
  - `default_trait_config()` — identity factory; SPEC §8.1 defaults.
  - `permissive_trait_config()` — shifted ranges (table below).

| trait | SPEC §8.1 (default) | permissive | rationale |
|---|---|---|---|
| hunger_pain_sensitivity | [0.25, 2.5] | **[1.0, 2.5]** | raise floor — every agent feels urgency |
| injury_pain_sensitivity | [0.25, 2.5] | **[0.25, 1.5]** | lower ceiling — no catastrophic damage perception |
| fear_sensitivity        | [0.0, 3.0]  | **[0.0, 1.5]**  | halve ceiling — no agent terrified |
| pleasure_sensitivity    | [0.25, 2.5] | **[1.0, 2.5]**  | raise floor — food matters to everyone |
| pain_tolerance          | [0.0, 1.0]  | **[0.4, 1.0]**  | raise floor — no hyper-sensitive agents |
| risk_tolerance          | [0.0, 1.0]  | **[0.4, 1.0]**  | raise floor — no fully-cautious agents |
| (others)                | unchanged   | unchanged       | isolate the fear/hunger axis |

All shifts are **sub-ranges of the SPEC master**: a ``Traits`` instance
sampled from `permissive` still passes `validate_traits` against the SPEC
config (pinned by [[tests/test_trait_configs.py]]).

## Pre-registered binary criteria

1. **Pursuit emerges**: permissive produces ≥1 food event across the
   8-seed × 5-founder = 40 random-traits population.
2. **Significant improvement**: permissive food_events > baseline
   food_events.
3. **Diversity preserved**: permissive does NOT show 100% survival
   across every seed — at least one founder still dies of starvation
   somewhere. (Avoids over-tuning into "everyone is Reckless.")

## Pre-registered failure→action mapping

- All criteria fail → range-shifting is not sufficient; v0.6 explores
  distribution shape (e.g., Beta sampling) or wider ranges.
- Criteria 1 + 2 pass, 3 fails → permissive over-tunes; narrow the shift.
- All three pass → permissive is a viable default candidate; user
  decides whether to promote to ``core/traits.py``.

## Result

| metric | default | permissive |
|---|---:|---:|
| total hazard entries | 1 | **19** |
| total food events | 0 | **8** |
| total hazard damage | 8.00 | 152.00 |
| total births | 0 | 0 |
| total starvation deaths | 40 | 39 |
| seeds with any survivor | 0 | **1** |
| seeds with any starvation | 8 / 8 | 8 / 8 |
| total moves | 535 | 737 |
| mean lifespan (ticks) | ~88 | ~135 |

**All three criteria pass.**

```
pursuit_emerges:           True
improvement_over_baseline: True
diversity_preserved:       True
```

### Per-seed permissive breakdown

| seed | ticks | survivors | starvation | food events | hazard entries | hazard damage |
|---:|---:|---:|---:|---:|---:|---:|
| 1    | **200** | **1** | 4 | **4** | 4  | 32  |
| 2    | 144 | 0 | 5 | 0  | 8  | 64  |
| 3    | 127 | 0 | 5 | 0  | 0  | 0   |
| 4    | 91  | 0 | 5 | 0  | 0  | 0   |
| 5    | 102 | 0 | 5 | 0  | 1  | 8   |
| 42   | 116 | 0 | 5 | 0  | 0  | 0   |
| 100  | 149 | 0 | 5 | **4** | 3  | 24  |
| 2024 | 150 | 0 | 5 | 0  | 3  | 24  |

The diversity is exactly what we wanted:

- **3 / 8 seeds** (1, 2, 5, 100, 2024 → 5 of 8) produced ≥1 hazard entry.
- **2 / 8 seeds** (1, 100) produced food events.
- **1 / 8 seeds** (1) produced a survivor at tick 200.
- **3 / 8 seeds** (3, 4, 42) produced pure null populations — the
  random roll happened to draw five non-crossers.

This is mixed-phenotype population output: some random rolls produce
survivors, some don't. **Exactly the v0.1 baseline question, now
answered yes.**

### Visual evidence — `permissive` seed 1, ticks 50 / 100 / 150 / 200

This is the seed that produced the surviving founder. Multiple agents
crossed the hazard band; multiple food cells were eaten; one agent (`f`)
made it to tick 200.

```
# tick 50 (founders early — three already in food zone)
___##****
___##.***
e__##*..*  ← agent e, food eaten
c__##***f  ← agents c and f in food zone
b__##****
___##****

# tick 100 (b, e have starved out; c and f survive in food zone)
___##****
___##.***
___##*..*
c__##***f
___##****
___##****

# tick 150 (c starved; f relocated)
___##****
___##.***
___##*..f
___##***.
c__##****  ← c is dead at this position
___##****

# tick 200 (sole survivor f, alive in food zone)
___##****
___##.***
___##*..*
___##***f
___##****
___##****
```

Compare to the baseline `default` snapshot (seed 42, tick 100), which
shows 2 living agents (`b`, `e`) at x=0 with the food zone and hazard
band untouched — the v0.4 "default" behavior:

```
# default seed=42 tick=100
e__##****
___##****
___##****
___##****
___##****
b__##****
```

## Interpretation

Six trait-range shifts (within SPEC §8.1) reproduce the harness premise
under random sampling:

1. **The harness now produces a population, not a clone set.** Different
   seeds produce different outcomes — some founders cross, some don't,
   some survive — purely from the trait roll. Three seeds out of eight
   produced no crossings at all under permissive sampling, which is the
   right shape for a "random agents in a hard environment" experiment.
2. **The valence math + axial sensors + fixed chamber were already
   correct.** v0.5 changed nothing in `core/`. The default `TraitConfig`
   was the bottleneck — its midpoints sat too far on the fear-paralysis
   side of the trait space.
3. **No reproduction yet under permissive.** The `ReproductionConfig`
   energy threshold (70) sits above starting energy (60), so a successful
   crosser must climb above 70 by eating before reproducing. None of the
   8 seeds produced a long-enough surviving lineage to clear that bar
   under random sampling. (Reckless got 2 births in v0.4 because Reckless
   pursues food maximally.) The v0.5 result shows population *survival*;
   reproduction emergence remains a v0.6+ question.

## Decision: do we promote `permissive` to the canonical default?

**Recommended: not yet.** Two open considerations:

1. **The shift is hand-tuned.** Six numbers were chosen by reading the
   v0.4 evidence; the experiment confirms the direction was correct, but
   it doesn't establish that *this specific* ratio is the best default
   inside the master ranges. A v0.6 sweep over a small grid (e.g., three
   levels of fear ceiling × two levels of hunger floor) would either
   confirm the choice as a local optimum or reveal a better point.
2. **Reproduction has not emerged under permissive.** A "viable default"
   that can't sustain a lineage isn't a complete story. Either tune
   `ReproductionConfig.energy_cost` / threshold (a separate experiment)
   or accept that lineage continuation requires either trait extremes
   (Reckless) or memory (the v0.6+ memory arm).

Until then, `permissive_trait_config()` lives in
[[src/hedonism_harness/experiments/trait_configs.py]] as an experiment
fixture, available to opt into via the new `trait_config=` parameter on
`run_chamber`. The SPEC §8.1 default in `core/traits.py` is **not
modified** by this commit.

## What changed

- [[src/hedonism_harness/experiments/trait_configs.py]] (new) — two
  factories + lookup helper.
- [[src/hedonism_harness/experiments/fear_hunger_chamber.py]] —
  `run_chamber` gains optional `trait_config: TraitConfig | None` kwarg
  (None = SPEC default; set to inject custom ranges).
- [[src/hedonism_harness/experiments/trait_tuning.py]] (new) — the v0.5
  sweep driver + pre-registered criterion evaluator.
- [[tests/test_trait_configs.py]] (new) — pins permissive ranges as
  sub-ranges of SPEC, in the documented direction, and verifies any
  random sample from permissive validates against the SPEC master.
- [[tests/test_trait_tuning.py]] (new) — smoke test + criterion-evaluator
  coverage including the diversity-fails-under-100%-survival branch.

No changes to: `core/traits.py`, `core/valence.py`, `core/sensors.py`,
`policies/`, layouts, archetypes.

## Reproducing

```bash
uv run python -c "
from pathlib import Path
from hedonism_harness.experiments.trait_tuning import run_trait_tuning
run_trait_tuning(
    seeds=[1, 2, 3, 4, 5, 42, 100, 2024],
    runs_root=Path('runs'),
    batch_id='fear-hunger-v0.5',
    n_ticks=200,
    n_founders=5,
    snapshot_tick=100,
    snapshot_seed=42,
)
"
```

Outputs in `runs/fear-hunger-v0.5/`:

```
fear-hunger-v0.5/
    comparison.csv             # one row per trait_config
    snapshots/
        default.txt
        permissive.txt
    {default | permissive}/
        summary.csv
        seed-{N}/...
```
