# fear_hunger v0.48 — sensor_radius → space → readiness bridge

**Slice:** v0.48
**Type:** post-hoc reducer (decomposition, NOT intervention)
**Predecessors:** v0.21..v0.27 (substrate / aggregate-optimum), v0.34 (lineage MVP), v0.35 (eventual-top survival framework), v0.36 (trait-heritability decomposition; `sensor_radius` fired as aligned-flat under b50/winner label), v0.42..v0.45 (substrate-causal arc), v0.46 (`READINESS_PREDICTS_DOMINANCE`: pre-50 reproductive momentum + tick-50 readiness fraction predict eventual dominance on the modern A_null corpus), v0.47 (`READINESS_TRAITS_PARTIALLY_PREDICTIVE`: `sensor_radius` is the only firing primary trait predicting tick-50 readiness fraction).
**Question being asked (locked):** Is the founder-level `sensor_radius` advantage observed by v0.47 mediated by a measurable pre-50 spatial / foraging advantage that — under the same effect-size discipline — also tracks the v0.47 readiness-fraction label?

v0.46 established that the eventual top lineage is already differentially advantaged at tick 50 along readiness axes. v0.47 fingered `sensor_radius` as the single firing founder-trait predictor of tick-50 readiness fraction (signed paired_d = +0.937, large effect). v0.47's locked phrase is correlational; the trait→readiness link is consistent with — but does not establish — a spatial/foraging mechanism. v0.48 is the **first observational bridge slice** asking whether the same lineages that win on `sensor_radius` (label A) and on tick-50 readiness fraction (label B) also win on three pre-committed pre-50 spatial / foraging observables. Bridge-present is the strongest claim allowed; mechanism declarations are forbidden.

## Conservation framing — unchanged from v0.46 / v0.47

- **No `src/` modifications.** v0.48 is a pure consumer of `setup_observer` + `tick_observer` + `AgentBorn` / `AteFood` blinker signals. It adds nothing to the simulation surface and does not modify any chamber / population / policy / event module.
- **No new sweep.** Corpus is the same 64 A_null runs from v0.42 / v0.43R / v0.44 / v0.45.
- **No modifications to prior reducer scripts.** v0.34's `lineage_replay.py`, v0.35's `lineage_survival_replay.py`, v0.36's `trait_replay.py`, the four intervention audits, and v0.46 / v0.47's reducers remain byte-identical to their merged forms. v0.48's reducer copy-locals any helpers it needs.
- **Pre-50 reproduction byte-identity** through v0.48 is preserved by construction: v0.48 makes no `src/` change.

## Corpus (locked, identical to v0.46 / v0.47)

| version | seeds | hazards | arms used | runs |
|---|---|---|---|---|
| v0.42 | 41..48 | {0, 8} | A_null only | 16 |
| v0.43R | 49..56 | {0, 8} | A_null only | 16 |
| v0.44 | 57..64 | {0, 8} | A_null only | 16 |
| v0.45 | 65..72 | {0, 8} | A_null only | 16 |
| **total** | | | | **64** |

V0_25 anchor: GradientPolicy + `auto_reproduction=True` + `TraitConfig(unbounded_mutation=True)`, `tight_gradient` layout, 5 founders, 200 ticks, `food_respawn_cooldown=50`, `ambient_influx_rate=1.0`, transfer-pool funding, `energy_pool_initial=1500`, `hazard_avoidance_weight` from V0_25. A_null arm = `InterventionConfig(kind=KIND_NULL)`, byte-identical to `optional_intervention=None` (verified each version by H2e regression).

## Labels (locked, two)

Each run is labelled twice — independently — and each label produces an independent paired_d set per primary observable. The verdict (below) consults both label-conditioned paired_d sets.

### Label A — `high_sensor_radius_lineage`

For each run:

```
high_sensor_radius_lineage = argmax_lineage(founder_sensor_radius)
                             tiebreak: min(lineage_id)
```

`founder_sensor_radius` is the unmutated initial draw captured at `setup_observer` time (i.e., the lineage's founder's `traits.sensor_radius`, integer-valued under the V0_25 anchor's `TraitConfig`). v0.47 reducer's founder-trait capture pattern is reused verbatim (copy-local). Tiebreak `min(lineage_id)` matches v0.34 / v0.35 / v0.46 conventions; integer-valued sensor_radius is expected to tie frequently among the 5 founders.

### Label B — `high_tick50_readiness_fraction_lineage`

Reuse v0.47's primary fraction label exactly. For each run:

```
high_tick50_readiness_fraction_lineage = argmax_lineage(tick50_above_threshold_fraction)
  3-tier tiebreak:
    1. argmax tick50_above_threshold_fraction
    2. argmax tick50_above_threshold_count
    3. min(lineage_id)
  NaN-loses: lineages with zero living agents at tick 50 (fraction = NaN) cannot win.
  Run yields no label B if all lineages are NaN at tick 50 — those runs contribute nothing to label B's paired_d pools (per-observable NaN drop).
```

Identical to v0.47's `high_tick50_readiness_fraction_lineage` definition (see `docs/experiments/fear_hunger_v0.47.md`); the readiness predicate is `energy ≥ reproduction_config.energy_threshold AND age ≥ reproduction_config.min_age` evaluated on the in-process tick-50 snapshot.

### Agreement rate (descriptive)

For each run where both A and B exist (i.e., A always exists; B exists when ≥ 1 lineage has ≥ 1 living agent at tick 50), report `agreement = 1 if label_A_lineage == label_B_lineage else 0`. The mean agreement rate across runs is reported descriptively in the audit log; it does NOT fire any verdict.

## Primary observables (locked, 3, with expected signs)

Each is computed **per (run, lineage)** by aggregating the per-tick observer's snapshots over ticks 0..50. Per-run paired delta = `label_lineage_value − mean(non_label_lineage_values)`, computed once per label.

| # | name | definition (per lineage, ticks 0..50) | expected sign |
|---|---|---|:-:|
| 1 | `pre50_food_events_count` | total `AteFood` events with `tick ≤ 50` whose `agent_id` belongs to lineage at the time the event fired (sum over all lineage agents living or dead) | **+** |
| 2 | `pre50_food_energy_acquired` | sum of `AteFood.food_gained` over the same event set | **+** |
| 3 | `mean_distance_to_nearest_food_cell` | per-tick lineage mean of Manhattan distance from each living lineage agent at tick t to the nearest cell where `world.food_value > 0`, then mean across ticks t ∈ {0, 1, ..., 50} where the lineage had ≥ 1 living agent | **−** |

Notes on observable #3 (per the locked aggregation rule):

```
per_tick_lineage_mean(t) = mean over (agents in lineage living at tick t) of:
                            min over (cells (cx, cy) with world.food_value[cx, cy] > 0 at tick t) of:
                              |agent.x - cx| + |agent.y - cy|
                            (Manhattan distance)
mean_distance_to_nearest_food_cell = mean over t ∈ {0, ..., 50} where the
                                     lineage had ≥ 1 living agent at tick t
                                     of per_tick_lineage_mean(t).
```

If the lineage has 0 living agents across **all** of ticks 0..50 → NaN (run dropped from observable's pool, per NaN handling). If the world has 0 food cells at some tick t (theoretically possible after enough food consumption with respawn cooldown), per_tick_lineage_mean(t) is undefined for that tick and that tick is dropped from the lineage's mean (logged in audit). Per-tick lineage means avoid agent-tick pooling, which would otherwise weight crowded ticks more heavily.

**NaN handling.** A lineage with zero `AgentBorn` events and zero founders is impossible (5 founders are guaranteed at tick 0). Observables #1, #2 are always well-defined (count = 0 if no events). Observable #3 is NaN only if the lineage has zero living agents across all of ticks 0..50 — i.e., all 1+ founders died at tick 0 and no births. Per-run paired delta is computed only when (a) the labelled lineage has a non-NaN value AND (b) ≥ 1 non-labelled lineage has a non-NaN value. Runs failing either gate are dropped from that observable's pool (count reported in the audit). Runs where label B does not exist (no living agents at tick 50 in any lineage) drop entirely from label B's pool but not from label A's pool.

## Per-tick observer (locked specification)

The reducer registers one `tick_observer` callback that fires after every `model.step()` for `model.tick_count ∈ {0, 1, ..., 50}` (i.e., 51 fires per run). At each fire it captures, in-memory:

- For each living agent: `(agent_id, lineage_id, x, y)`.
- The set of cells where `world.food_value > 0` at that tick (positions only; values not needed for distance — only positions).

The observer is **read-only**: it reads `model.agents` and `world.food_value` but does not mutate either. The reducer also reuses v0.46's `setup_observer` pattern to attach `AgentBorn` (lineage map + birth_tick) and `AteFood` (food event + food_gained accumulation, filtered by tick ≤ 50) signal listeners — both filtered by `sender=model` so concurrent runs do not cross-pollinate.

The tick-50 readiness-predicate snapshot (label B's input) is captured by the same per-tick observer when `tick_count == 50`: per-living-agent `(energy, age)` plus the lineage's `tick50_above_threshold_count` and `tick50_living_count`.

End-of-run capture (b50 by lineage, end-of-run living count) is unchanged from v0.46/v0.47 and produced for audit-log diagnostics only — v0.48 does NOT condition on the b50/winner label (that is v0.46's label, distinct from labels A and B above).

## Effect-size rule (locked, sign-aware)

For each (label, primary observable) pair:

```
per_run_delta_i  = label_lineage_value_i − mean(non_label_lineage_values_i)
paired_d         = mean(per_run_delta) / stdev(per_run_delta, ddof=1)
signed_d         = paired_d × expected_sign     (expected_sign ∈ {+1, −1})
fires_expected   iff signed_d ≥ +0.5
fires_wrong_sign iff signed_d ≤ −0.5
```

For observables #1 and #2 the expected sign is **+1** so `signed_d == paired_d`. For observable #3 the expected sign is **−1** so a *negative* paired_d corresponds to a *positive* signed_d (lineage closer to food than peers, in the expected direction).

No p-values, no FDR. Multiple-comparison protection is the small pre-committed primary set of size 3 × 2 = 6 paired_d cells (3 observables × 2 labels), all six pre-committed before code runs (per v0.36 / v0.46 / v0.47 fishing-protection pattern). Stdev uses Bessel's correction (ddof=1).

## Verdicts (locked, 3-way + 1 halt)

For each label `L ∈ {A, B}`, count `n_fire(L)` = number of primary observables where `signed_d_L ≥ +0.5` and `n_wrong(L)` = number where `signed_d_L ≤ −0.5`.

| condition | verdict | locked phrase (verbatim) |
|---|---|---|
| `n_wrong(A) > 0 OR n_wrong(B) > 0` (any wrong-sign primary under either label) | `SPATIAL_BRIDGE_OPPOSITE_SIGN_HALT` | "Halt: a v0.48 spatial / foraging primary fires in the WRONG direction under at least one of the two labels; the trait→space→readiness bridge hypothesis is incompatible with the locked expected signs." |
| `n_wrong(both) == 0 AND n_fire(A) ≥ 2 AND n_fire(B) ≥ 2` | `SENSOR_RADIUS_SPATIAL_BRIDGE_PRESENT` | "Founder `sensor_radius` advantage co-occurs with a pre-50 spatial / foraging advantage that also tracks tick-50 readiness fraction on the modern A_null corpus." |
| `n_wrong(both) == 0 AND exactly one of (n_fire(A), n_fire(B)) ≥ 2` (the other < 2) | `SENSOR_RADIUS_SPATIAL_BRIDGE_PARTIAL` | "A pre-50 spatial / foraging advantage tracks one of (founder `sensor_radius`, tick-50 readiness fraction) but not the other on the modern A_null corpus; the bridge is partial." |
| `n_wrong(both) == 0 AND n_fire(A) < 2 AND n_fire(B) < 2` | `SENSOR_RADIUS_SPATIAL_BRIDGE_NOT_FOUND` | "No pre-50 spatial / foraging advantage tracks either label on the modern A_null corpus; the trait→space→readiness bridge does not fire under the locked observables and threshold." |
| any of v0.42 / v0.44 / v0.45's re-derived A_null h=8 share drifts > 1e-3 from its hardcoded reference | `CORPUS_REDERIVE_DRIFT_HALT` | "Halt: A_null re-anchor drifted from the published Results value for v0.NN; v0.48's deterministic re-execution does not reproduce the published metric within 1e-3." |

The verdict is **AND-gated** for `_PRESENT`: both labels must independently clear ≥ 2/3 in the expected direction with 0/3 wrong. `_PARTIAL` is reserved for the asymmetric case where exactly one label clears the bar. `_NOT_FOUND` covers all other no-wrong-sign cases (including 1/3 under both, 0/3 under both, etc.). Any wrong-sign firing under either label halts loud — the bridge hypothesis must be sign-consistent with v0.47's `sensor_radius` direction.

The `_PRESENT` phrase is **correlational, not causal**: it does not claim `sensor_radius` *causes* a spatial advantage or that the spatial advantage *causes* readiness — only that the three signals co-occur within run.

## Re-anchor (locked, identical protocol to v0.46 / v0.47)

Each predecessor version's audit emits a pooled A_null top-lineage `b50_share` at h=8. v0.48 re-derives that share from its own deterministic re-execution and asserts that the derived value matches the published reference within `1e-3`. Halt-loud on drift (`CORPUS_REDERIVE_DRIFT_HALT`).

| version | published `a_share_h8` | source |
|---|---|---|
| v0.42 | **0.652** | `docs/experiments/fear_hunger_v0.42.md` |
| v0.43R | **NOT PUBLISHED** | informational-only; logged but does not gate verdict |
| v0.44 | **0.878** | `docs/experiments/fear_hunger_v0.44.md` |
| v0.45 | **0.818** | `docs/experiments/fear_hunger_v0.45.md` |

`a_share_h8(version) = mean over A_null h=8 runs of max_lineage(b50_count) / sum_lineages(b50_count)`. v0.46 and v0.47 reproduced these to within 0.0003 in their own deterministic re-executions; v0.48 is expected to reproduce them identically since it uses the same `(seed, V0_25, A_null)` execution path (per-tick observer is read-only).

## Cautious framing (per CLAUDE.md)

- "Founder `sensor_radius` advantage co-occurs with a pre-50 spatial / foraging advantage" — NOT "sensor_radius causes a spatial advantage".
- "Tracks tick-50 readiness fraction" — NOT "produces readiness".
- "On the modern A_null corpus" — NOT a chamber-config-independent claim.
- v0.48 explicitly does **not** rule out: pre-50 spatial sorting that is independent of `sensor_radius`, founder-position advantage, topology-mediated energy access, or any post-tick-200 dynamic. These remain live causal candidates regardless of v0.48's verdict.
- v0.48 does **not** establish a heritability mechanism for the spatial advantage, even if `_PRESENT` fires. Mechanism declarations require fresh-stream calibration analogous to v0.30..v0.33.

## Secondary descriptive metrics (cannot fire verdict)

Captured by the per-tick observer for transparency; reported in `runs/v0.48-spatial-bridge/per_run_per_lineage_spatial.csv` and the audit log. Do NOT influence the verdict.

- `mean_axial_food_signal_own_radius` per lineage — per-tick lineage mean of (count of food cells along N/S/E/W axes within each agent's own `traits.sensor_radius`), then mean across ticks 0..50. Uses each agent's own (mutable) radius rather than a fixed radius — descriptive, NOT a clean comparison.
- `mean_axial_hazard_signal_own_radius` per lineage — same structure, hazard cells.
- `tick50_centroid_distance_to_nearest_food` per lineage — Manhattan distance from the lineage's living-agent centroid `(mean x, mean y)` at tick 50 to the nearest live food cell. NaN if 0 living agents.
- `tick50_centroid_distance_to_nearest_hazard` per lineage — same structure, nearest hazard cell.
- `pre50_hazard_damage_received_count` per lineage (cumulative `HazardDamageApplied` events with tick ≤ 50, by `agent_id`) — descriptive; carry-over from v0.46 schema for cross-version readability.
- `tick50_living_count`, `tick50_above_threshold_count`, `tick50_above_threshold_fraction` per lineage — carry-over from v0.46/v0.47 schema.
- `founder_sensor_radius`, `founder_metabolic_rate`, `founder_reproduction_drive` per lineage — carry-over from v0.47 schema.
- `b50_count`, `is_eventual_top_b50_label` per lineage — for cross-readability with v0.46's dominance label (NOT used by v0.48's verdict).

These are descriptive only. Even if a secondary metric shows a large effect size, it does NOT fire the verdict; the verdict is determined exclusively by the three primary observables under the two labels.

## Outputs (locked)

```
runs/v0.48-spatial-bridge/per_run_per_lineage_spatial.csv
  columns: version, seed, hazard, run_id, lineage_id,
           founder_sensor_radius, founder_metabolic_rate, founder_reproduction_drive,
           pre50_food_events_count, pre50_food_energy_acquired,
           mean_distance_to_nearest_food_cell,
           mean_axial_food_signal_own_radius, mean_axial_hazard_signal_own_radius,
           tick50_centroid_distance_to_nearest_food, tick50_centroid_distance_to_nearest_hazard,
           tick50_living_count, tick50_above_threshold_count, tick50_above_threshold_fraction,
           pre50_hazard_damage_received_count,
           b50_count, is_eventual_top_b50_label,
           is_label_a_high_sensor_radius, is_label_b_high_readiness_fraction

runs/v0.48-spatial-bridge/audit_summary.csv
  columns: section, key, value
  sections:
    - reanchor: per (version, h=8) re-derived A_null share + reference + drift_abs
    - paired_d: per (label, primary observable) cell — paired_d, signed_d, n_runs, fires_expected, fires_wrong
    - agreement: mean(label_A == label_B) across runs where both labels exist + n_runs_both_defined
    - verdict: locked verdict + locked phrase

runs/v0.48-spatial-bridge/audit_log.txt
  human-readable echo including the locked phrase verbatim, the 6-cell paired_d table, and the agreement rate.
```

## Implementation plan (locked)

1. Fresh script `scripts/v0_48_sensor_radius_spatial_bridge_audit.py`. CLI: `uv run python scripts/v0_48_sensor_radius_spatial_bridge_audit.py [--out-dir runs/v0.48-spatial-bridge]`.
2. Per (version, seed, hazard) tuple in the locked corpus, build the same V0_25 + A_null arm config the version's sweep used (re-using `V0_42_INTERVENTION_ARMS[0]` etc. — the A_null arm — from `comparison_grid.py`). Same as v0.46 / v0.47.
3. Run `run_chamber(...)` once per tuple with two observers:
   - **`setup_observer`**: copy-local from v0.47 — registers `AgentBorn` listener (birth_tick + lineage map), `AteFood` listener (filtered by tick ≤ 50, stores `food_gained`), `HazardDamageApplied` listener (descriptive). Captures founder traits per lineage at setup time.
   - **`tick_observer`**: fires for every `tick_count ∈ {0, 1, ..., 50}` (51 fires). Per fire: snapshot `(lineage_id, x, y)` per living agent + the set of food-cell positions at that tick + (if `tick_count == 50`) the readiness-predicate snapshot. Stores per-tick records in per-run dict keyed by `(version, seed, hazard)`.
   - End-of-run capture: walk `model.agents` for end-of-run living count + b50 (descriptive-only — for cross-readability with v0.46).
4. Per (run, lineage) at tick 50: aggregate the 3 primary observables + secondary descriptive metrics. Per run: assign label A (`argmax(founder_sensor_radius)`, tiebreak `min(lineage_id)`) and label B (v0.47 3-tier readiness fraction tiebreak).
5. Compute paired_d per (label, observable) pair across all 64 runs (NaN-aware drops per "NaN handling"). 6 paired_d cells total.
6. Re-anchor: for v0.42 / v0.44 / v0.45 only, compute `a_share_h8`; halt-loud on |drift| > 1e-3.
7. Emit verdict per the locked decision rule; print + write the locked phrase verbatim.

The reducer is fully self-contained: it reads no `runs/` artifacts. Wall time ~5–10 minutes for 64 runs (per-tick observer is cheap; food-cell scan is O(width × height) per tick which is negligible at the 12×12 layout scale).

## Test list (locked, per v0.46 / v0.47 7-point review pattern)

`tests/test_v0_48_sensor_radius_spatial_bridge_audit.py`:

1. `test_per_tick_observer_fires_for_each_tick_0_through_50` — run `run_chamber` for 100 ticks with a counting `tick_observer`; assert the v0.48 observer captures snapshots for each `tick_count ∈ {0, ..., 50}` exactly once.
2. `test_label_a_argmax_founder_sensor_radius_with_tiebreak` — synthetic 3-lineage run with sensor_radius (5, 7, 7); assert label A picks the lower lineage_id of the two 7s.
3. `test_label_b_three_tier_tiebreak_matches_v0_47` — synthetic two-lineage run where fractions tie but counts differ; assert label B follows the count then min(lineage_id) tiebreak.
4. `test_pre50_food_events_filtered_by_tick_inclusive_50` — synthetic events at ticks 30, 50, 75; assert count = 2 (inclusive ≤ 50).
5. `test_pre50_food_energy_uses_food_gained_field` — synthetic AteFood events with food_gained ∈ {1.0, 2.5, 0.5} all at ticks ≤ 50; assert sum = 4.0.
6. `test_distance_uses_per_tick_lineage_mean_then_mean_over_ticks` — synthetic capture: tick 0 has 1 agent at distance 3 (per_tick mean = 3); tick 1 has 2 agents at distances (1, 5) (per_tick mean = 3); ticks 2..50 have 0 living agents; assert observable = mean(3, 3) = 3.0 (NOT agent-tick pooled which would also give 3 here, so vary the synthetic to differ).
7. `test_distance_nan_when_lineage_has_no_living_agents_across_window` — synthetic lineage with 0 living agents at every tick 0..50; assert NaN and the run is dropped from the observable's pool.
8. `test_signed_d_for_negative_expected_sign_observable` — synthetic delta vector for observable #3 with `mean(delta) = -2.0, stdev = 1.0` → paired_d = -2.0 → signed_d = +2.0 (expected sign -1) → fires expected.
9. `test_verdict_present_requires_both_labels_clear_two_of_three` — synthetic paired_d such that under label A, signed_d = (0.6, 0.7, 0.3) (2/3 fire); under label B, (0.6, 0.8, 0.2) (2/3 fire); assert `SENSOR_RADIUS_SPATIAL_BRIDGE_PRESENT`.
10. `test_verdict_partial_when_only_one_label_clears` — under A, (0.6, 0.7, 0.3); under B, (0.3, 0.4, 0.2); assert `SENSOR_RADIUS_SPATIAL_BRIDGE_PARTIAL`.
11. `test_verdict_not_found_when_neither_label_clears` — under A, (0.4, 0.3, 0.2); under B, (0.3, 0.2, 0.4); assert `SENSOR_RADIUS_SPATIAL_BRIDGE_NOT_FOUND`.
12. `test_verdict_halt_on_wrong_sign_under_either_label` — under A, (0.6, -0.7, 0.3); under B, (0.6, 0.6, 0.6); assert `SPATIAL_BRIDGE_OPPOSITE_SIGN_HALT` raised loud.
13. `test_reanchor_drift_halt` — synthetic published-share value 0.5; replay yields 0.6; assert `CORPUS_REDERIVE_DRIFT_HALT` raised loud.
14. `test_secondary_metrics_in_csv_but_do_not_affect_verdict` — synthetic run where centroid distance and axial-signal observables would fire but primaries do not; assert verdict = `SENSOR_RADIUS_SPATIAL_BRIDGE_NOT_FOUND`.

## Watch-outs (for future-Chronus)

- **Per-tick observer is read-only.** It must NOT mutate `model.agents`, `world.food_value`, or any other in-memory simulation state. Verified by running the reducer once with the observer attached and once without (under `tempfile.TemporaryDirectory`) and asserting end-of-run state is identical for a small (`n=1`) re-execution; the re-anchor at h=8 is the production-scale check.
- **`AteFood.food_gained` is the canonical field** (verified via `core/events.py:48`); the pre-reg uses this name verbatim. No "energy_gained" — that field does not exist.
- **`sensor_radius` is integer-valued** under V0_25's `TraitConfig`. Per-lineage `argmax` will tie frequently among 5 founders; `min(lineage_id)` tiebreak fires often. Cohen's d arithmetic coerces to float per v0.47 pattern.
- **Distance metric is Manhattan**, not Euclidean — consistent with the grid's 4-connected action set.
- **Per-tick lineage mean** — observable #3's aggregation rule is per-tick mean *then* mean over ticks; agent-tick pooling is explicitly excluded (would over-weight crowded ticks).
- **Food cells can respawn** within ticks 0..50 if `food_respawn_cooldown ≤ 50` (V0_25 has `food_respawn_cooldown = 50`, so any food consumed at tick 0 respawns at tick 50). The per-tick food-cell snapshot tracks the live food set at each tick correctly; the distance metric uses the per-tick set.
- **0 food cells at tick t** is theoretically possible but unobserved on the V0_25 anchor in the live corpus; if it occurs the per-tick mean for that tick is undefined and the tick is dropped from the lineage's window mean (logged in audit).
- **Label B can be missing** for runs where every lineage has 0 living agents at tick 50; those runs drop from label B's pool entirely (per-observable NaN drop). Label A always exists (founder sensor_radius is captured at tick 0 unconditionally).
- **Agreement rate is descriptive only.** Even if A and B always disagree (agreement = 0), the verdict is unaffected; the AND-gate is on signed_d ≥ +0.5 under each label independently.
- **Causal language is forbidden.** "Bridge present" is the strongest claim allowed under `_PRESENT`. v0.48 is observational, not interventional.
- **Cross-version pooling** valid by H2e regression on each version's branch (A_null arms byte-identical to `optional_intervention=None`); same as v0.46/v0.47.
- **Locked phrase discipline:** when the verdict fires, the locked-phrase string in the Results section MUST match the table above verbatim. No paraphrase.

## Files this slice will create

- `docs/experiments/fear_hunger_v0.48.md` (this file; Results section appended after reducer run)
- `scripts/v0_48_sensor_radius_spatial_bridge_audit.py`
- `tests/test_v0_48_sensor_radius_spatial_bridge_audit.py`

No other files modified.

## Results

(appended after reducer execution)
