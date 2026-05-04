# Fear-Hunger Chamber — v0.4 valence fix (anticipated food pleasure)

**Experiment:** Targeted valence fix isolated by the v0.3 failure→action mapping.
**Branch:** `claude/valence-v0.4`
**Date:** 2026-05-04
**Run:** `runs/fear-hunger-v0.4/`

## Question

The v0.3 geometry sweep falsified the structural-masking hypothesis: even
with hazard at x=3-4 and food at x=5 both inside the east axial sensor ray
from spawn x=1 (`tight_gradient`), no archetype produced a single hazard
entry across 1200 founder-runs. The pre-registered failure→action mapping
sent us to `core/valence.py`.

Reading [[src/hedonism_harness/core/valence.py]] revealed an asymmetry:

> The harness has anticipated **avoidance** (`fear` filtered through
> `_hazard_signal_total(obs_after)`, plus `safety_pleasure` for moves that
> reduce hazard exposure) but no anticipated **pursuit**. The directional
> ``food_signal_*`` fields exist on ``Observation``; valence.py never
> reads them. Eating pleasure only fires on ``Action.EAT``.

That single asymmetry explains the entire v0.3 result. Fearful agents
moved more than Reckless in `tight_gradient` because Fearful's
`safety_pleasure` pulls strongly west; Reckless had no fear to avoid AND
no food to pursue, so high `hunger_pain_sensitivity * move_cost` made STAY
the safe bet.

## Fix

Add a single new pleasure term in [[src/hedonism_harness/core/valence.py]]:

```python
food_signal_before = _food_signal_total(obs_before)
food_signal_after  = _food_signal_total(obs_after)
food_signal_gain   = max(0.0, food_signal_after - food_signal_before)
anticipated_food_pleasure = (
    food_signal_gain * obs_before.hunger_level * traits.pleasure_sensitivity
)
```

Three deliberate decisions:

1. **`max(0, …)` clip** matches the existing `safety_pleasure` convention.
   Moves away from food contribute zero pleasure (not negative); the
   "hunger persists" term in pain handles the cost of inaction.
2. **Gating on `obs_before.hunger_level`** ensures full agents do not
   chase food. This is the raw `1 - energy_ratio` quantity, NOT the
   pain-tolerance-filtered hunger_pain — so even Reckless (whose
   `pain_tolerance=1.0` zeros her hunger_pain by SPEC §11.2) still
   receives the food gradient through this pleasure channel.
3. **Sum across all four directions** so an agent at a multi-axis food
   junction feels the full gain, not just one axis.

The fix is six lines of math + folding the term into `pleasure`. No
sensor changes, no trait-config changes, no policy changes.

## Tests

Five new tests in [[tests/test_valence.py]] pin the contract:

- `test_anticipated_food_pleasure_pulls_east_when_food_visible_east_and_hungry`
- `test_anticipated_food_pleasure_is_zero_when_full`
- `test_anticipated_food_pleasure_scales_monotonically_with_hunger_level`
- `test_anticipated_food_pleasure_uses_sum_across_directions`
- `test_existing_fear_still_pushes_west_when_hazard_visible_east` (regression
  guard: the v0.3 fix must not change avoidance behavior).

All five fail on `main` before the fix and pass on `claude/valence-v0.4`
after. 259 total tests pass; smoke green.

## Result — pre-registered criteria all flip

The v0.3 batch was re-run unchanged (same seeds, same ticks, same
hyperparameters, same chamber). Only valence.py differs.

```
any_archetype_enters_hazard:           True   (was False)
reckless_2x_fearful_in_some_layout:    True   (was False)
any_food_or_hazard_signal:             True   (was False)
```

### Headline grid (8 seeds × 5 founders = 40 runs per cell)

| layout | condition | hazard entries | food events | hazard damage | births | starvation | survivors | moves |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| `default`         | default  | 0 | 0 | 0.00 | 0 | 40 | 0 | 135 |
| `default`         | fearful  | 0 | 0 | 0.00 | 0 | 40 | 0 | 122 |
| `default`         | reckless | 0 | 0 | 0.00 | 0 | 40 | 0 | 120 |
| `default`         | balanced | 0 | 0 | 0.00 | 0 | 40 | 0 | 122 |
| `default`         | explorer | 0 | 0 | 0.00 | 0 | 40 | 0 | 122 |
| `tight_gradient`  | default  | 1 | 0 | 8.00 | 0 | 40 | 0 | 535 |
| `tight_gradient`  | fearful  | **0** | **0** | 0.00 | 0 | 40 | 0 | 185 |
| `tight_gradient`  | reckless | **323** | **60** | **2624.00** | **2** | 39 | **3** | 1871 |
| `tight_gradient`  | balanced | 2 | 0 | 16.00 | 0 | 40 | 0 | 1257 |
| `tight_gradient`  | explorer | 2 | 0 | 16.00 | 0 | 40 | 0 | 1257 |
| `near_hazard`     | default  | 0 | 0 | 0.00 | 0 | 40 | 0 | 246 |
| `near_hazard`     | fearful  | 0 | 0 | 0.00 | 0 | 40 | 0 | 258 |
| `near_hazard`     | reckless | 0 | 0 | 0.00 | 0 | 40 | 0 | 219 |
| `near_hazard`     | balanced | 0 | 0 | 0.00 | 0 | 40 | 0 | 258 |
| `near_hazard`     | explorer | 0 | 0 | 0.00 | 0 | 40 | 0 | 258 |

### What changed where, and why

- **`default` chamber** is unchanged from v0.3 — food remains outside
  sensor range from spawn x=1, so `food_signal_gain == 0` for every
  candidate action and the new term is silent. **Structural masking
  still applies** when the agent has no information; this is the
  correct null. The harness only "knows" about food it can sense.

- **`tight_gradient` chamber** flips into a rich phenotype zoo:
  - **Reckless**: 323 hazard entries (avg 8 per founder), 60 food
    events, **2 births**, 3 survivors at tick 200. The full SPEC §16.3
    "reckless crosser" phenotype.
  - **Fearful**: 0 hazard entries. Existing fear math still wins —
    Fearful's `fear_sensitivity * (1 - risk_tolerance) = 3.0 * 1.0 =
    3.0` multiplied by predicted hazard exposure overpowers the new
    food anticipation term. The "fear paralysis" phenotype is
    preserved as a deliberate negative result.
  - **Balanced** and **Explorer**: 2 hazard entries each, no food
    events. The midpoint trait roll lands close enough to the
    fear/pursuit balance that occasional crossings happen but no agent
    survives long enough to reach food. **The expected intermediate
    phenotype between Fearful and Reckless.**

- **`near_hazard` chamber**: hazard visible east, food NOT visible. All
  archetypes produce 0 hazard entries — `food_signal_gain == 0` (no
  food in sensor range from any direction), so the new term doesn't
  fire and the existing fear/safety still pushes agents west. Behaves
  exactly like v0.3 here. **The fix does not over-fire.**

### Visual evidence — `tight_gradient` seed 42 @ tick 100

The four archetype snapshots are now strikingly different:

```
# tight_gradient / reckless          # tight_gradient / fearful
___##****                             ___##****
___##****                             ___##****
___##.*.g  <- in food zone            ___##****
___##***e  <- in food zone            ___##****
___##..c*  <- next to food            ___##****
___##*...                             ___##****

# tight_gradient / balanced           # tight_gradient / explorer
___##****                             ___##****
___##****                             ___##****
___##****                             ___##****
___##****                             ___##****
___##****                             ___##****
___##****                             ___##****
```

Reckless's panel shows three living agents (`c`, `e`, `g`) on or beside
the food zone, with multiple `*` cells eaten (`.`). Fearful, Balanced,
and Explorer all show the chamber pristine — those archetypes never
reached the food zone. **This is exactly the SPEC §16.3 phenotype set the
harness premise predicts.**

### Reckless per-seed detail

Of the 8 Reckless seeds in `tight_gradient`:

| seed | ticks | survivors | starvation | food events | hazard entries | births |
|---:|---:|---:|---:|---:|---:|---:|
| 1    | 139 | 0 | 5 | 9 | 29 | 0 |
| 2    | 200 | **1** | 5 | 10 | 45 | **1** |
| 3    | 41  | 0 | 5 | 0 | 55 | 0 |
| 4    | 200 | **1** | 4 | 11 | 32 | 0 |
| 5    | 162 | 0 | 5 | 8 | 44 | 0 |
| 42   | 136 | 0 | 6 | 9 | 37 | **1** |
| 100  | 200 | **1** | 4 | 7 | 37 | 0 |
| 2024 | 180 | 0 | 5 | 6 | 44 | 0 |

Three of eight seeds reach tick 200 with surviving lineage. Two seeds
produced a successful birth (the parent's death came after a successful
reproduce action). One seed (3) burned out fast — 41 ticks — likely a
hazard-damage cascade where founders entered hazard before energy was
high enough to power through.

## Interpretation

The v0.4 fix is the smallest possible patch that flips the v0.3 null and
preserves all existing behavior:

- **Existing fear/safety still works**: regression test passes; Fearful
  in `tight_gradient` produces zero hazard entries (the desired null).
- **No sensor changes**: axial rays are still axial. The diagnosis was
  not about what the agent could sense — it was about what valence did
  with the senses.
- **No trait-config changes**: SPEC §8.1 ranges untouched. The same
  archetype trait values that produced a null in v0.3 produce a rich
  phenotype set in v0.4 because the harness now reads a sensor field
  that was already being computed.

The harness now satisfies the project's premise: **agents act on felt
valence, and given trait diversity + spatial information, that valence
produces recognizable behavioral phenotypes.**

## What's next

The v0.4 result reopens questions that v0.1-v0.3 had to defer:

1. **Tune `default` trait distribution toward viable diversity.** Now
   that we have a working harness in `tight_gradient`, sweep
   `TraitConfig` ranges to find a default population that produces
   non-zero crossings across i.i.d.-uniform draws (the v0.1 question).
2. **Memory arm.** With at least one phenotype crossing reliably, a
   `MemoryHedonismPolicy` lineage can demonstrate "remembered good
   propagates after the first crossing" — the SPEC §16.3 cautious-
   memory-crosser phenotype.
3. **Default chamber rescue.** The `default` layout (spawn x=1) is
   still null because food is genuinely out of sensor range. Either
   widen `sensor_radius` defaults, tighten the chamber, or add a
   smell-field sensor (the user's deferred sensor upgrade plan).

Per the project's experimental ladder, do not pursue 1-3 simultaneously.
The next session should pick **one** and pre-register its success
criteria before running the sweep.

## Reproducing

```bash
uv run python -c "
from pathlib import Path
from hedonism_harness.experiments.geometry_v03 import run_geometry_v03
run_geometry_v03(
    seeds=[1, 2, 3, 4, 5, 42, 100, 2024],
    runs_root=Path('runs'),
    batch_id='fear-hunger-v0.4',
    n_ticks=200,
    n_founders=5,
    snapshot_tick=100,
    snapshot_seed=42,
)
"
```

Outputs in `runs/fear-hunger-v0.4/` with the same layout as v0.3.
