# Fear-Hunger Chamber — v0.2 positive-control batch

**Experiment:** Positive-control trait archetypes against the v0.1 chamber.
**Branch:** `claude/positive-control-traits`
**Date:** 2026-05-04
**Run:** `runs/fear-hunger-v0.2/`

## Question

The v0.1 pilot produced **fear paralysis across all 8 seeds** under the
i.i.d.-uniform default trait distribution: 40/40 starvation, 0 hazard
entries, 0 food events. The next question was not "what should defaults
be?" but the binary positive control:

> Can the harness express SPEC §16.3 phenotypes *at all* when traits are
> biased to known extremes?

If yes → tune defaults. If no → inspect the diagnostic ladder before
declaring a valence bug.

## Setup

Identical chamber to v0.1 (20 × 6 grid, safe x∈[0,5], hazard x∈[8,11], food
x∈[14,19]) and identical hyperparameters (`exploration_noise=0.05`, 5
founders, 200 ticks). The only changing variable is **traits**.

Five conditions, 8 seeds each (40 runs):

| Condition | Hunger | Fear | Injury pain | Pain tol. | Risk tol. | Novelty | Uncert. avoid. |
|---|---:|---:|---:|---:|---:|---:|---:|
| `default`  | random | random | random | random | random | random | random |
| `fearful`  | min (0.25) | **max (3.0)** | max (2.5) | min (0.0) | min (0.0) | mid | mid |
| `reckless` | **max (2.5)** | min (0.0) | min (0.25) | max (1.0) | max (1.0) | mid | mid |
| `balanced` | mid (1.375) | mid (1.5) | mid | mid | mid | mid | mid |
| `explorer` | mid | mid | mid | mid | mid | **max (2.0)** | min (0.0) |

Unspecified traits sit at their SPEC §8.1 midpoint. Within an archetype, all
five founders share **identical** traits; variance comes only from the
`agent_order` / `action_noise` / `hazard_resolution` RNG streams. The
`default` condition is re-run from v0.1 for self-contained comparison.

## Result

### Aggregates (8 seeds × 5 founders = 40 runs per condition)

| condition | mean pop end | starvation | injury | food events | hazard entries | births | total moves | total stays |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| `default`  | 0 | 40 | 0 | 0 | **0** | 0 | 135 | 3947 |
| `fearful`  | 0 | 40 | 0 | 0 | **0** | 0 | 122 | 3651 |
| `reckless` | 0 | 40 | 0 | 0 | **0** | 0 | 120 | 3655 |
| `balanced` | 0 | 40 | 0 | 0 | **0** | 0 | 122 | 3651 |
| `explorer` | 0 | 40 | 0 | 0 | **0** | 0 | 122 | 3651 |

### Verdict against the success criterion

The pre-registered binary criterion was:

> **At least one archetype produces ≥1 hazard entry across 8 seeds, AND
> archetypes differ on hazard / food outcomes from the Fearful floor.**

Outcome: **Negative.** Total hazard entries across all 200 episodes = 0.
All 200 founders died of starvation in their natal column.

### What's notable about *how* it failed

`fearful`, `balanced`, and `explorer` produced **byte-identical** counters
per seed (122 moves, 3651 stays). `reckless` differs by 2 moves total
across 8 seeds — a sub-noise leak. The four archetypes act effectively
identically despite spanning the full width of SPEC §8.1 on five orthogonal
trait axes.

The `default` condition is the *only* meaningfully different one (135 moves,
3947 stays; ~10% longer mean lifespan). This separation comes not from
behavior change but from the metabolic-rate roll: random traits sometimes
draw `metabolic_rate < 1.25`, the archetype midpoint, lengthening lifespan
without changing the action distribution.

### Visual evidence — seed 42 @ tick 100

`default` is the only condition still showing live agents at this tick
(three of five survive); the four archetype conditions are already empty
because their fixed midpoint metabolic_rate burns through energy slightly
faster than the lower tail of the default distribution.

```
# fearful
______..####..******
______..####..******
______..####..******
______..####..******
______..####..******
______..####..******

# reckless
______..####..******
______..####..******
______..####..******
______..####..******
______..####..******
______..####..******

# explorer
______..####..******
______..####..******
______..####..******
______..####..******
______..####..******
______..####..******

# balanced
______..####..******
______..####..******
______..####..******
______..####..******
______..####..******
______..####..******

# default (3 alive: b, d, e)
______..####..******
______..####..******
_e____..####..******
______..####..******
d_b___..####..******
______..####..******
```

In all four archetype panels the food zone (`x∈[14,19]`) and hazard band
(`x∈[8,11]`) are pristine — no `*` was ever consumed, no `#` was ever
entered. Every glyph east of x=5 is exactly as it was painted.

## Interpretation

This is **structural masking**, not a valence bug.

The trait differences ARE being computed — Reckless's hunger pain
sensitivity is 10× Fearful's, novelty drive in Explorer is 2× Balanced's —
but those differences scale a **sensor input that is empty**. Founders
spawn at x=1 with default `sensor_radius=4` (the midpoint of SPEC §8.1's
[1,6] range), so each agent sees the column window x∈[0,5]: pure SAFE.
Hazard at x=8 and food at x=14 are both out of sensor range. The agent
has no eastward gradient to weigh.

The decision then collapses to:

1. STAY costs less than any MOVE (action energy book-keeping).
2. Hunger pain is the only positive-pull-toward-east signal — but it has
   no spatial direction, only a magnitude. It pushes the agent to *act*,
   not to act *east*.
3. The 5% exploration noise occasionally fires a MOVE, but the four
   directions are uniform under noise, so no eastward bias accumulates.

This explains why Reckless leaks 2 extra moves over Fearful but not 200:
elevated hunger sensitivity raises the noise threshold for *any* move, but
once the move fires the direction is undirected.

## Decision

The user-specified decision tree was:

> If yes → tune defaults. If no → inspect `core/valence.py`.

The result here is **No — but not yet at the valence rung of the ladder.**
The geometry-tightening experiment (the user's pre-named step 2) is the
right next move because it isolates a different failure mode:

- v0.1 pilot ruled out: "default traits cross."
- v0.2 batch ruled out: "extreme traits cross under default geometry."
- v0.3 must rule out: "any trait set crosses *given a positive eastward
  gradient*." Until that's tested we cannot distinguish "valence math is
  wrong" from "no information ever reaches the valence math."

The cleanest design for v0.3:

1. Same chamber proportions, but tighten so the **food zone enters default
   sensor range**. Concretely: shrink the EMPTY corridors so a founder at
   x=1 with `sensor_radius=4` can see at least one food cell.
2. Re-run the same 5-condition × 8-seed grid.
3. Pre-registered question: does *any* archetype now cross? If yes,
   geometry was the bottleneck; if still no, valence math is the
   bottleneck and `core/valence.py` is the next file to read.

A secondary geometry knob worth varying separately: agents spawn at
`x=safe_x_max-1` (just inside the safe zone's east edge) instead of
`x=safe_x_min+1`. This keeps trait distribution constant and the chamber
shape constant, isolating the sensor-vs-target distance.

## Implications for the harness premise

The v0.2 result is internally consistent with the SPEC's premise that
agents "act on felt valence, not on what's good for them." When valence
inputs carry no spatial information about food, no trait setting can
recover that information. The harness is **not** silently doing the right
thing for the wrong reason; it is doing exactly what the math says — which
is "stay put" when the local gradient is flat in every direction.

The negative result also gives us a clean falsification of one
hyperparameter belief: **trait extremes alone are not sufficient**. Any
future "tune defaults" sweep must also vary either sensor radius, chamber
geometry, or the gradient-construction step in valence — otherwise the
sweep will produce the same null result with more decimals.

## Reproducing

```bash
uv run python -c "
from pathlib import Path
from hedonism_harness.experiments.positive_control import run_positive_control
run_positive_control(
    seeds=[1, 2, 3, 4, 5, 42, 100, 2024],
    runs_root=Path('runs'),
    batch_id='fear-hunger-v0.2',
    n_ticks=200,
    n_founders=5,
    snapshot_tick=100,
    snapshot_seed=42,
)
"
```

Outputs in `runs/fear-hunger-v0.2/`:

```
fear-hunger-v0.2/
    comparison.csv
    snapshots/
        default.txt
        fearful.txt
        reckless.txt
        balanced.txt
        explorer.txt
    {condition}/
        summary.csv
        seed-{N}/
            config.json
            manifest.json
            episode_metrics.csv
            agent_lifetimes.csv
            lineages.csv
            events.jsonl
            summary.md
```
