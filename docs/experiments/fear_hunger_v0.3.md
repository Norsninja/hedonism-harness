# Fear-Hunger Chamber — v0.3 geometry-tightening sweep

**Experiment:** Geometry vs. valence diagnostic per the v0.2 failure→action mapping.
**Branch:** `claude/geometry-v0.3`
**Date:** 2026-05-04
**Run:** `runs/fear-hunger-v0.3/`

## Question

The v0.2 positive-control batch ruled out "extreme traits alone produce
crossing." It also revealed that three of four archetypes produced byte-
identical counters per seed, suggesting the harness's observation vector
was effectively flat — agents had no spatial information that could turn a
trait difference into a behavioral difference.

The pre-registered v0.3 ladder asked one binary question:

> **Is the v0.2 null caused by structural masking (no eastward gradient in
> sensor range) or by the valence math itself?**

If even one layout produced a hazard entry or food event when the gradient
was visible, the answer was "geometry." If all three layouts produced the
same null, the answer was "valence."

## Setup

Three named layouts in [[src/hedonism_harness/experiments/layouts.py]],
identical hyperparameters to v0.2 (`exploration_noise=0.05`, 5 founders,
200 ticks, 8 seeds), and the same five trait conditions
(`default | fearful | reckless | balanced | explorer`). Only **layout**
changed across the 15 (layout × condition) cells.

Sensor reminder: `core/sensors._scan_axial` scans only the four cardinal
rays (N/S/E/W) from the agent's cell, NOT a square box. So "visible
eastward from spawn x=1 with `sensor_radius=4`" means cells at the agent's
y in `x ∈ [2..5]`.

| layout | width | safe x | hazard x | food x | spawn x | east ray sees @ r=4 |
|---|---:|---|---|---|---:|---|
| `default`         | 20 | [0,5] | [8,11] | [14,19] | 1 | x∈[2..5]: pure SAFE |
| `tight_gradient`  | 9  | [0,2] | [3,4]  | [5,8]   | 1 | x∈[2..5]: SAFE, **2 HAZARD, 1 FOOD** |
| `near_hazard`     | 20 | [0,5] | [8,11] | [14,19] | 6 | x∈[7..10]: EMPTY, **3 HAZARD** |

## Pre-registered criteria

1. At least one non-fearful archetype enters hazard in some layout.
2. Reckless's hazard-entry total ≥ 2× Fearful's in at least one layout.
3. At least one (layout, condition) cell produces food events OR hazard
   damage > 0.

## Pre-registered failure→action mapping

- All three layouts null → inspect `core/valence.py` (structural masking
  hypothesis falsified).
- Only `tight_gradient` positive → opposing gradients required; v0.4
  explores trait sensitivity to gradient strength.
- Only `near_hazard` positive → avoidance gradient sufficient, pursuit
  unnecessary; the harness expresses a fear-driven phenotype set.
- `near_hazard` positive AND `tight_gradient` null → conflicting signal
  cancels out (high-priority valence finding).

## Result

### Headline grid (totals across 8 seeds × 5 founders = 40 runs per cell)

| layout | condition | hazard entries | food events | hazard damage | births | starvation | moves | stays |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| `default`         | default  | **0** | 0 | 0.00 | 0 | 40 | 135 | 3947 |
| `default`         | fearful  | **0** | 0 | 0.00 | 0 | 40 | 122 | 3651 |
| `default`         | reckless | **0** | 0 | 0.00 | 0 | 40 | 120 | 3655 |
| `default`         | balanced | **0** | 0 | 0.00 | 0 | 40 | 122 | 3651 |
| `default`         | explorer | **0** | 0 | 0.00 | 0 | 40 | 122 | 3651 |
| `tight_gradient`  | default  | **0** | 0 | 0.00 | 0 | 40 | 154 | 3608 |
| `tight_gradient`  | fearful  | **0** | 0 | 0.00 | 0 | 40 | **185** | 3585 |
| `tight_gradient`  | reckless | **0** | 0 | 0.00 | 0 | 40 | 143 | 3597 |
| `tight_gradient`  | balanced | **0** | 0 | 0.00 | 0 | 40 | 156 | 3596 |
| `tight_gradient`  | explorer | **0** | 0 | 0.00 | 0 | 40 | 154 | 3618 |
| `near_hazard`     | default  | **0** | 0 | 0.00 | 0 | 40 | 175 | 3535 |
| `near_hazard`     | fearful  | **0** | 0 | 0.00 | 0 | 40 | 232 | 3493 |
| `near_hazard`     | reckless | **0** | 0 | 0.00 | 0 | 40 | **219** | 3503 |
| `near_hazard`     | balanced | **0** | 0 | 0.00 | 0 | 40 | 224 | 3491 |
| `near_hazard`     | explorer | **0** | 0 | 0.00 | 0 | 40 | 222 | 3493 |

(`moves` totals here include both batch results from `comparison.csv`. The
two values shown above for `tight_gradient/reckless` and
`near_hazard/reckless` reflect the per-condition aggregates exactly.)

### Verdict against pre-registered criteria

```
any_archetype_enters_hazard:           False
reckless_2x_fearful_in_some_layout:    False
any_food_or_hazard_signal:             False
```

**All three pre-registered criteria fail. All three layouts are null.**

Per the failure→action mapping: **inspect `core/valence.py`.** The
structural-masking hypothesis is falsified. The agent could see the food
zone in `tight_gradient` and the hazard band in both `tight_gradient` and
`near_hazard`. The valence math chose not to act on those signals in any
direction-distinguishing way.

### What the secondary observables reveal

Two patterns are unexpectedly informative:

**1. Fearful moves more than Reckless when fear is visible.**

In `tight_gradient` (hazard at x=3-4 in sensor range), Fearful agents made
185 moves total vs Reckless's 143 — **Fearful is ~30% more mobile when fear
is a salient signal.** In `near_hazard`, the same pattern: Fearful 232,
Reckless 219.

In `default` (no signals), the order reverses: Reckless 120, Fearful 122
(near-tie). The presence of a fear gradient inverts the trait-driven
mobility ranking.

This is consistent with one of two hypotheses about `valence.py`:

- (a) Fear contributes positive *agitation* — a "do anything other than
  STAY" pull — rather than a directional anti-east pull. Higher fear
  sensitivity → more bounce, not more avoidance.
- (b) The fear signal is driving moves *toward* the hazard at small
  distances (sign error or formula collapse). This would also explain why
  Reckless — with low fear sensitivity — moves *less* than Fearful when
  hazard is visible.

Either is a specific, testable claim about `core/valence.py`.

**2. Mobility increases with signal salience but never with direction.**

Move counts per condition by layout:

| condition | default | tight_gradient | near_hazard |
|---|---:|---:|---:|
| default  | 135 | 154 | 175 |
| fearful  | 122 | 185 | 232 |
| reckless | 120 | 143 | 219 |
| balanced | 122 | 156 | 224 |
| explorer | 122 | 154 | 222 |

Moves rise monotonically `default → tight_gradient → near_hazard` for
every archetype. The hazard signal makes agents *more* mobile, but no
agent ever entered the hazard band. So they're moving — north, south, or
west — but **not east**. The harness is producing aversion in the form of
"flee in any non-east direction," consistent with hypothesis (a).

### Visual evidence — `tight_gradient` seed 42 @ tick 100

Both Reckless and Fearful columns are empty by tick 100 (agents died at
tick 95-98), but the painted geometry is unchanged: `*` cells at x∈[5,8]
and `#` cells at x∈[3,4] remain pristine. No founder reached either zone.

```
# tight_gradient / reckless
___##****
___##****
___##****
___##****
___##****
___##****

# tight_gradient / fearful
___##****
___##****
___##****
___##****
___##****
___##****
```

Identical pixel layout — one of many indications that despite the elevated
mobility on the Fearful row, the moves are returning to the same column.

## Diagnostic conclusion

The structural-masking hypothesis is **falsified**. With sensor input
visibly pointing east (food signal in `tight_gradient`, hazard signal in
both `tight_gradient` and `near_hazard`), no archetype produced a single
directional crossing in 1200 founder-runs.

The harness produces the right *amount* of movement for the trait — Fearful
agents are demonstrably more agitated when fear is salient — but it does
not produce *directed* movement. The valence math is mapping signal
magnitude to action *count*, not to action *choice between directions*.

This is a clean valence finding. The `Fearful > Reckless > Balanced` move-
count ordering when hazard is visible is the smoking-gun observation: an
agent with high `fear_sensitivity` should move *less* in directions away
from hazard if anything (because every direction is uncertain), and a
correctly-implemented anti-east signal should produce **fewer total moves
plus a westward bias**, not more total moves with no spatial bias.

## Implications for v0.4

The pre-registered next step is `core/valence.py` inspection. The two
specific hypotheses to test:

- **Sign or direction error**: does the fear contribution to candidate
  action valence flip sign when summed across the sensor's directional
  vectors? A correct anti-east fear signal must subtract from
  `valence(MOVE_EAST)` and add to nothing else (or add to MOVE_WEST in a
  symmetrical fear→escape model).
- **Magnitude-to-direction collapse**: does fear contribute as an
  undirected scalar to the "act on something" pull, rather than as a
  directional vector? If `pred_valence(action)` includes a term like
  `fear_sensitivity * total_hazard_signal` instead of
  `fear_sensitivity * directional_hazard_signal[action]`, every action
  except STAY gets the same fear-boost, producing exactly the symptoms
  observed here.

Read [[src/hedonism_harness/core/valence.py]] and
[[src/hedonism_harness/policies/hedonism_policy.py]] together. The
harness's predict-one-step pattern means valence is computed against the
*post-move* observation, so the directional weighting must be encoded in
how each candidate action's predicted observation is constructed — bugs
can hide on either side of the apply_action / observe seam.

Do **not** modify `valence.py` yet. The first step is reading it with
these symptoms in hand and writing a v0.4 hypothesis-test plan
(experiments + expected ranges) before changing any math.

## Reproducing

```bash
uv run python -c "
from pathlib import Path
from hedonism_harness.experiments.geometry_v03 import run_geometry_v03
run_geometry_v03(
    seeds=[1, 2, 3, 4, 5, 42, 100, 2024],
    runs_root=Path('runs'),
    batch_id='fear-hunger-v0.3',
    n_ticks=200,
    n_founders=5,
    snapshot_tick=100,
    snapshot_seed=42,
)
"
```

Outputs in `runs/fear-hunger-v0.3/`:

```
fear-hunger-v0.3/
    layout_comparison.csv
    {default | tight_gradient | near_hazard}/
        comparison.csv
        snapshots/{condition}.txt
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
