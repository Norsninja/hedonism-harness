# fear_hunger v0.53c — reachability disambiguation at tick-200 (pure window extension)

**Slice:** v0.53c
**Type:** **first-class observational sweep** with 3-arm tick-200 reducer (no `src/` changes; no intervention; no substrate variation; reuses existing named layouts).
**Predecessors:** v0.46–v0.52b (full predecessor stack), v0.53 (`BRIDGE_PARTIALLY_GENERALIZES`), v0.53b (`WIDENED_BELOW_REACHABILITY_THRESHOLD_AT_TICK_100` — B_widened reachability = 0.0 at tick-100, 50% B_widened population extinction before tick-100).
**Question being asked (locked):** Does extending the observation window from tick-100 to tick-200 (the full simulation length under V0_25) reveal whether v0.53b's `WIDENED_BELOW_REACHABILITY_THRESHOLD_AT_TICK_100` is a tick-100-window artifact (reachability crosses 25% at tick-200) or persists at the maximum-window measurement (reachability still < 25% at tick-200, suggesting the layout × V0_25 substrate combination is incompatible with food access in the available simulation lifetime)?

v0.53b closed the question "is v0.53's B_widened NOT_FOUND a 50-tick-window artifact" with `WIDENED_BELOW_REACHABILITY_THRESHOLD_AT_TICK_100`: zero of 64 runs reach food by tick-100, and 50% of populations are extinct by then. v0.53b's locked Results explicitly flagged tick-150 / tick-200 as the deferred candidate.

v0.53c is that maximum-window probe. It re-runs the same 192-run corpus shape with the per-tick observer extended to tick-200 (the full `N_TICKS=200` simulation length — no `n_ticks` change, no `src/` modification). It asks whether B_widened's reachability eventually crosses 25% under the longest measurable window on this substrate, OR whether the geometry × V0_25 substrate combination structurally prevents food access in the available lifetime.

If B_widened reachability ≥ 25% at tick-200 AND tick-200 sub-verdict resolves PRESENT, v0.53b's tick-100 NOT_FOUND was window-bound; the bridge is measurable on `widened_gradient` given maximum observation. If reachability ≥ 25% AND tick-200 sub-verdict ∈ {PARTIAL, NOT_FOUND}, the bridge fails to fire under maximum observation despite measurable reachability — a layout-specific failure not reducible to window-censoring. If reachability < 25% even at tick-200, **the V0_25 substrate cannot measure the bridge on `widened_gradient` in any window the available simulation can deliver**. That outcome formally bounds v0.53's `BRIDGE_PARTIALLY_GENERALIZES` verdict scope to the V0_25 substrate × `widened_gradient` × N_TICKS=200 combination AND motivates v0.53d as a substrate-variation slice.

## Pre-implementation note (2026-05-09, before any reducer code)

The pre-reg's design was confirmed with the user before drafting:

- **3 arms (symmetric).** Same as v0.53 / v0.53b: A_null_V0_25 (`tight_gradient`), B_widened_gradient, C_food_ladder. Same 64-tuple corpus.
- **Tick-200 observation window.** Per-tick observer accumulates through tick 200 (the full sim length). EMITS `pre50_*`, `pre100_*`, AND `pre200_*` rollups in parallel. Three Label B variants computed in parallel: `tick50` (Tier-1 anchor), `tick100` (descriptive context), `tick200` (verdict-gating).
- **No substrate variation.** Same V0_25 substrate (auto_reproduction, unbounded mutation, energy pool, influx, hazard_avoidance_weight, etc.). Substrate-vs-geometry disambiguation along the parameter axis is the deferred v0.53d candidate, NOT in v0.53c scope.
- **No `src/` modifications.** v0.53c inherits v0.52b-tip src/ (= v0.53 / v0.53b tip src/, since neither slice touched src/). The window extension is purely script-local: per-tick observer accumulates through tick-200 instead of tick-100.
- **Explicit extinction and degenerate-label handling.** v0.53b's tick-100 reduction surfaced 50% B_widened extinction → `n=32` on Label B tick-100 cells. At tick-200 extinction will likely be more severe. v0.53c locks the handling pre-data to avoid retrofitting in Results: degenerate cells (`n=0` paired_d) are treated as `nan`; per-arm `tickN_living_population_run_share` is logged as a descriptive metric; the sub-verdict rule is unchanged from v0.53b (`nan` cells cannot fire; a label with all 3 cells `nan` cannot contribute to PRESENT/PARTIAL gating; if both labels are fully degenerate AND zero firing cells exist, sub-verdict = NOT_FOUND, **NOT** a separate halt).

## Conservation framing — observational, no `src/`, no intervention, no substrate change

- **No `src/` modifications.** v0.53c inherits v0.53 / v0.53b's src/ state. The window extension is script-local; the per-tick observer wires through tick-200 instead of tick-100.
- **No modifications to prior reducer or audit scripts.** v0.34's `lineage_replay.py`, ..., v0.53's reducer, v0.53b's reducer remain byte-identical to their merged forms.
- **A_null_V0_25 arm is byte-identical to v0.48–v0.53b A_null path AT TICK-50.** Tier-1 re-anchor enforces this.
- **B_widened_gradient and C_food_ladder arms are byte-identical to v0.53 / v0.53b's B and C arms AT EVERY TICK 0..200.** Same `streams.mutation`, founder draws, per-agent RNGs, world layouts. The only difference between v0.53b and v0.53c is the *upper bound of the observation window*: v0.53b stops accumulation at tick-100; v0.53c continues through tick-200.
- **No intervention at any level.** No founder body trait modification, no override patching, no helper RNG, no shuffle, no clamp, no permutation.
- **No substrate change.** All BodyConfig / ReproductionConfig / WorldConfig parameters identical to v0.53 / v0.53b A_null arm.
- **Single observation-window-channel variation.** v0.53c differs from v0.53b only in the per-tick observer's upper bound. Simulation engine, world initialization, agent construction, per-tick dynamics are byte-identical to v0.53b across all three arms.

## Corpus (locked, 64 × 3 arms = 192 runs)

Same shape as v0.53 / v0.53b:

| version | seeds | hazards | runs per arm | total runs |
|---|---|---|---|---|
| v0.42 | 41..48 | {0, 8} | 16 | 48 |
| v0.43R | 49..56 | {0, 8} | 16 | 48 |
| v0.44 | 57..64 | {0, 8} | 16 | 48 |
| v0.45 | 65..72 | {0, 8} | 16 | 48 |
| **total** | | | | **192** |

V0_25 substrate identical to v0.53 / v0.53b. Wall time estimate ~18–30 minutes total (slightly longer than v0.53b due to 100 extra observation ticks per run; sim itself runs the same 200 ticks).

## Arms (locked, 3 — same layout selection as v0.53 / v0.53b)

### A_null_V0_25

```
ChamberLayout = tight_gradient_layout()
FounderSpec(traits_override=None)
no patch, no body_config override, no per-agent override
```

Byte-identical to v0.48–v0.53b A_null path at every tick 0..200. Used for:
1. **Tier-1 anchor at tick-50** (against v0.48 / v0.53 published cells).
2. **Descriptive context at tick-100 and tick-200** (no published anchor; magnitude shifts reported in Results, do not gate the verdict).

### B_widened_gradient

```
ChamberLayout = widened_gradient_layout()
FounderSpec(traits_override=None)
no patch, no body_config override, no per-agent override
```

Byte-identical to v0.53 / v0.53b's B_widened arm at every tick 0..200. **The primary arm of v0.53c**: the verdict gates on B's tick-200 reachability and tick-200 sub-verdict.

### C_food_ladder

```
ChamberLayout = food_ladder_layout()
FounderSpec(traits_override=None)
no patch, no body_config override, no per-agent override
```

Byte-identical to v0.53 / v0.53b's C arm at every tick 0..200. **Descriptive context at tick-100 and tick-200** (no published anchor; halt-loud only on opposite-sign).

## Labels (locked, two — with three Label B variants)

### Label A — `high_sensor_radius_lineage`

Identical to v0.48–v0.53b. Trait-resolved (`int(founder.body.traits.sensor_radius)`); tiebreak `min(lineage_id)`. Time-window-independent.

### Label B — three variants computed in parallel

Each is `argmax_lineage(tickN_above_threshold_fraction)` with the v0.47 3-tier tiebreak (fraction → count → min(lineage_id), NaN-loses):

- **`high_tick50_readiness_fraction_lineage`** — used for the Tier-1 anchor against v0.48 / v0.53 / v0.53b.
- **`high_tick100_readiness_fraction_lineage`** — used for descriptive context (also re-anchors v0.53b's tick-100 sub-verdicts within 1e-3 as a within-session sanity check; SECONDARY anchor only, NOT gating).
- **`high_tick200_readiness_fraction_lineage`** — used for the v0.53c **verdict**.

If at tick-N **no lineage has any agent above the readiness threshold** (everyone NaN or zero), Label B for that run is undefined; the per-run paired_d delta cells are `nan` and the per-arm cell's `n` decrements.

## Primary observables (locked, 3, computed at three windows)

| # | name pattern | windows | expected sign |
|---|---|---|:-:|
| 1 | `pre{N}_food_events_count` | N ∈ {50, 100, 200} | + |
| 2 | `pre{N}_food_energy_acquired` | N ∈ {50, 100, 200} | + |
| 3 | `mean_distance_to_nearest_food_cell_tick{N}` | N ∈ {50, 100, 200} | − |

Definitions / aggregation rules / NaN handling: copy-local from v0.48–v0.53b. Primaries 1 / 2 accumulate `AteFood` events through tick-N inclusive. Primary 3 is a snapshot at tick-N over living agents per lineage.

The reducer captures all three windows from the same 192 sim runs in a single per-tick observer pass.

## Effect-size rule (locked, sign-aware, identical to v0.48–v0.53b)

```
per_run_delta_O = label_lineage_value_O − mean(non_label_lineage_values_O)
paired_d_O      = mean(per_run_delta_O) / stdev(per_run_delta_O, ddof=1)
signed_d_O      = paired_d_O × expected_sign
fires_expected  iff signed_d_O ≥ +0.5
fires_wrong     iff signed_d_O ≤ −0.5
```

## B_widened reachability metric at tick-200 (locked, pre-data)

```
b_reachability_run_share_tick_200 =
    fraction of B_widened runs where at least one founder lineage has
    pre200_food_events_count > 0
```

Domain: 64 runs (B_widened arm only). Threshold: **`B_REACHABILITY_THRESHOLD = 0.25`** (same as v0.53b). A run with extinct population by tick-200 cannot have any lineage with `pre200_food_events_count > 0` (founders die before food reach), so extinction implicitly counts as "non-reaching" — the metric correctly captures both "alive but didn't reach" and "dead before reaching" without double-counting.

## Population-stability and degenerate-label descriptive metrics (locked, pre-data)

In addition to the verdict-gating reachability metric, v0.53c logs three descriptive metrics per arm × window:

```
arm_living_population_run_share_tick_N =
    fraction of arm runs where at least one agent is alive at tick-N
    (across all lineages, snapshotted from model.agents at tick-N)

arm_label_a_n_runs_tick_N =
    number of arm runs where Label A produces a non-nan winner at tick-N
    (Label A is trait-resolved per founder; it is undefined only if zero
    founders exist, which can occur post-extinction — but founders are
    always recorded at tick 0, so this should equal arm size unless an
    invariant fails)

arm_label_b_n_runs_tick_N =
    number of arm runs where Label B produces a non-nan winner at tick-N
    (3-tier tiebreak NaN-loses; degenerate when no lineage at tick-N has
    any living agent above the readiness threshold)
```

These are descriptive only — no halt or outcome gates on them directly. They are reported in Results and feed the interpretive frame for tick-200 cells with low `n`.

## Per-arm sub-verdicts (locked, 4-way each)

Identical structure to v0.53b; sub-verdict labels rename to tick-200 tier:

| condition | A_null_V0_25 (tick-200) | B_widened_gradient (tick-200) | C_food_ladder (tick-200) |
|---|---|---|---|
| both labels clear ≥ 2/3 firing cells (NaN cells excluded), 0 wrong-sign | `A_NULL_V025_TICK200_BRIDGE_PRESENT` | `B_WIDENED_TICK200_BRIDGE_PRESENT` | `C_LADDER_TICK200_BRIDGE_PRESENT` |
| exactly one label clears ≥ 2/3 firing cells, 0 wrong-sign | `A_NULL_V025_TICK200_BRIDGE_PARTIAL` | `B_WIDENED_TICK200_BRIDGE_PARTIAL` | `C_LADDER_TICK200_BRIDGE_PARTIAL` |
| neither label clears ≥ 2/3 firing cells, 0 wrong-sign | `A_NULL_V025_TICK200_BRIDGE_NOT_FOUND` | `B_WIDENED_TICK200_BRIDGE_NOT_FOUND` | `C_LADDER_TICK200_BRIDGE_NOT_FOUND` |
| any primary signed_d ≤ −0.5 under either label | `A_NULL_V025_TICK200_OPPOSITE_SIGN_HALT` | `B_WIDENED_TICK200_OPPOSITE_SIGN_HALT` | `C_LADDER_TICK200_OPPOSITE_SIGN_HALT` |

**The "≥ 2/3 firing cells" rule explicitly excludes NaN cells from the count.** A label with 3 cells of which 2 are NaN and 1 fires expected has 1/1 firing-cell ratio = 100% → Label clears 1/1 = trivially "≥ 2/3 of non-nan cells"? No — the v0.48–v0.53b rule is "≥ 2/3 of the 3 cells fire expected", treating NaN as "doesn't fire". v0.53c preserves that strict rule: NaN cells count toward the denominator but not the numerator. A label with 3 NaN cells clears 0/3 → does not fire. A label with 2 NaN + 1 firing clears 1/3 → does not fire ≥ 2/3.

This means tick-200 cells with high NaN counts cannot fire PRESENT under their label. The reachability-bound nature of the corpus is preserved in the sub-verdict.

Each arm's tick-200 paired_d cells (3 observables × 2 labels = 6 cells per arm; 18 cells total across the three arms) are computed independently from the arm's 64-run pool with NaN-runs excluded from the per-cell `n`.

## Slice rollup verdicts (locked, 6 outcomes, priority-ordered)

Priority order (first-matching wins). The non-halt outcomes (priorities 4–6) gate **only on B_widened**; A_null_V0_25 and C_food_ladder tick-200 sub-verdicts are descriptive in Results unless they fire opposite-sign (priority 3).

1. `CORPUS_REDERIVE_DRIFT_HALT`
2. `BRIDGE_REPLICATION_HALT` (Tier-1 A_null_V0_25 tick-50 vs v0.48 / v0.53 / v0.53b)
3. `LAYOUT_OPPOSITE_SIGN_HALT` (any tick-200 wrong-sign across A_null_V0_25, B_widened_gradient, or C_food_ladder)
4. `WIDENED_REACHABILITY_RESOLVED_AT_TICK_200`
5. `WIDENED_REACHABILITY_RESOLVED_BRIDGE_NOT_FOUND_AT_TICK_200`
6. `WIDENED_BELOW_REACHABILITY_THRESHOLD_AT_TICK_200`

### Halt conditions

| priority | rollup verdict | trigger | locked phrase (verbatim) |
|---|---|---|---|
| 1 | `CORPUS_REDERIVE_DRIFT_HALT` | A_null_V0_25 arm `a_share_h8` for any of v0.42 / v0.44 / v0.45 drifts > 1e-3 from the published reference | "Halt: A_null_V0_25 re-anchor drifted from the published Results value for {version}; v0.53c's deterministic re-execution of the V0_25 corpus does not reproduce the published metric within 1e-3." |
| 2 | `BRIDGE_REPLICATION_HALT` | (a) A_null_V0_25 tick-50 signed_d for any of the six v0.48 / v0.53 / v0.53b cells drifts > 1e-3 from the published value, OR (b) A_null_V0_25 tick-50 sub-verdict ≠ PRESENT | "Halt: v0.53c's A_null_V0_25 arm does not reproduce v0.48 / v0.53 / v0.53b's tick-50 spatial bridge — either a paired_d cell drifts beyond 1e-3 of the published value, or the tick-50 sub-verdict does not resolve to PRESENT. v0.53c cannot interpret the tick-200 cells without an established baseline." |
| 3 | `LAYOUT_OPPOSITE_SIGN_HALT` | any tick-200 gating-label primary signed_d ≤ −0.5 under arm A_null_V0_25, B_widened_gradient, or C_food_ladder | "Halt: a v0.53c tick-200 spatial / foraging primary fires in the WRONG direction under a gating label; the maximum-window extension surfaces a regime incompatible with the locked expected signs." |

### Tier-1 (priority 2) re-anchor — A_null_V0_25 tick-50 cells

Identical six cells to v0.48 / v0.53 / v0.53b:

| label | observable | sign | published signed_d |
|---|---|:-:|:-:|
| `label_a_sensor_radius` | `pre50_food_events_count` | + | **+1.066** |
| `label_a_sensor_radius` | `pre50_food_energy_acquired` | + | **+1.066** |
| `label_a_sensor_radius` | `mean_distance_to_nearest_food_cell_tick50` | − | **+1.916** |
| `label_b_readiness_fraction_tick50` | `pre50_food_events_count` | + | **+0.916** |
| `label_b_readiness_fraction_tick50` | `pre50_food_energy_acquired` | + | **+0.916** |
| `label_b_readiness_fraction_tick50` | `mean_distance_to_nearest_food_cell_tick50` | − | **+1.179** |

Drift tolerance = 1e-3. v0.53c also re-derives v0.53b's tick-100 cells as a SECONDARY within-session sanity check (NOT gating; logged in `audit_summary.csv` only).

### Outcome conditions (only consulted if no halt fires)

| priority | rollup verdict | trigger | locked phrase (verbatim) |
|---|---|---|---|
| 4 | `WIDENED_REACHABILITY_RESOLVED_AT_TICK_200` | B_widened reachability ≥ 25% AND B_widened tick-200 sub-verdict = `B_WIDENED_TICK200_BRIDGE_PRESENT` | "On the modern A_null corpus with the V0_25 substrate held constant and the observation window extended from tick-100 to tick-200 (the full simulation length), the v0.48 spatial / foraging bridge fires PRESENT on `widened_gradient` under the locked +0.5 paired_d threshold. v0.53b's `WIDENED_BELOW_REACHABILITY_THRESHOLD_AT_TICK_100` was a tick-100-window artifact; the bridge is measurable on `widened_gradient` given the maximum simulation window on this substrate." |
| 5 | `WIDENED_REACHABILITY_RESOLVED_BRIDGE_NOT_FOUND_AT_TICK_200` | B_widened reachability ≥ 25% AND B_widened tick-200 sub-verdict ∈ {`B_WIDENED_TICK200_BRIDGE_PARTIAL`, `B_WIDENED_TICK200_BRIDGE_NOT_FOUND`} | "On the modern A_null corpus with the V0_25 substrate held constant and the observation window extended from tick-100 to tick-200 (the full simulation length), the v0.48 spatial / foraging bridge does NOT fire PRESENT on `widened_gradient` despite measurable reachability (≥ 25% of runs producing pre200 food access). The NOT_FOUND outcome under maximum observation is not reducible to window-censoring on this layout × substrate; the bridge fails to fire even when food primaries become measurable. Layout-specific failure logged in Results." |
| 6 | `WIDENED_BELOW_REACHABILITY_THRESHOLD_AT_TICK_200` | B_widened reachability < 25% | "On the modern A_null corpus with the V0_25 substrate held constant and the observation window extended from tick-100 to tick-200 (the full simulation length), fewer than 25% of `widened_gradient` runs have any founder lineage with pre200 food events. B_widened's reachability is below the locked 25% threshold under maximum observation; the bridge cannot be measured on `widened_gradient` at any window length the V0_25 substrate's `N_TICKS=200` simulation can deliver. v0.53's `BRIDGE_PARTIALLY_GENERALIZES` verdict scope is now formally bounded along the (V0_25 substrate × `widened_gradient`) cell; substrate-variation disambiguation (v0.53d candidate) is the natural follow-up." |

The rollup is **categorical-only**. Magnitude differences in A_null_V0_25 / C_food_ladder tick-200 cells are reported descriptively in Results but do not alter the verdict. PARTIAL on B_widened folds into priority 5.

The 3 non-halt outcomes form a total partition of (B reachability ≥ 0.25, B sub-verdict ∈ {PRESENT, PARTIAL, NOT_FOUND}) ∪ (B reachability < 0.25). Halts cover OPPOSITE_SIGN, drift, and replication. Test #16 enforces the partition exhaustively.

## Cautious framing (per CLAUDE.md)

- "**Reachability-resolved at tick-200**", "**below the locked 25% reachability threshold under maximum observation**", "**tick-100-window artifact**", "**measurable on `widened_gradient` given the maximum simulation window on this substrate**", "**not reducible to window-censoring**" — NOT "**proves**", "**causes**", or "**rules out**".
- "**Maximum simulation window on this substrate**" specifically means `N_TICKS=200` — the locked V0_25 sim length. v0.53c does NOT establish behavior beyond tick-200; that requires a separate `n_ticks` increase (out of scope here).
- "**Layout × V0_25 substrate combination**" — NOT "the `widened_gradient` layout in general". v0.53c's verdict is bounded to the V0_25 substrate. Substrate variation (v0.53d candidate) is required to make a layout-only claim.
- v0.53c explicitly does not establish: cross-layout generalization to layouts not in the v0.53 set, mechanism for any layout-specific outcome, generalization to non-V0_25 substrates, behavior at `n_ticks > 200`, causal contribution per layout (Reading-A causal-generalization slice remains the deferred candidate).

## What v0.53c cannot establish (logged here pre-data, not retrofittable)

- ✗ **"`widened_gradient` is universally unreachable"** if priority 6 fires. v0.53c tests V0_25 substrate × N_TICKS=200 only. Different metabolic / energy / policy parameters may admit reachability. v0.53d (substrate variation) remains the natural follow-up.
- ✗ **"The bridge IS or IS NOT load-bearing on `widened_gradient`"** under any priority-4/5/6 outcome. The observation tells us about reachability and bridge-firing; it does not establish channel-level causal contribution (deferred Reading-A slice).
- ✗ **A revised v0.53 / v0.53b verdict.** Both stand as historical contracts for their respective windows. v0.53c is the *maximum-window* probe; its scope is v0.53b's deferred follow-up question.
- ✗ **Mechanism behind any extinction or bridge-firing outcome.** Population dynamics under V0_25 × `widened_gradient` are descriptively logged; no mechanism is formally established.
- ✗ **Generalization beyond the three tested layouts** (`tight_gradient`, `widened_gradient`, `food_ladder`) or beyond the V0_25 substrate.

## Open framing (NOT in v0.53c primary)

- **v0.53d — substrate-variation disambiguation on `widened_gradient`.** Triggered if v0.53c fires priority 6. Modifies V0_25 substrate parameters (lower `base_metabolic_cost`, higher `starting_energy`, higher `max_energy`, etc.) on `widened_gradient` only; tests whether reachability is parameter-bound. Independent observational slice.
- **v0.53e (or later) — Reading-A causal-generalization slice on layouts admitting the bridge.** Re-run v0.49's null + clamp_4 + permutation_5! per layout that admits measurement. Independent of v0.53c outcome.
- **v0.54 — joint ablation** (zero-cost AND shuffle). Channel-interaction question. Independent of layout-axis findings.
- **Eventual fresh-stream calibration** on the v0.46–v0.53c conclusion stack — needed for any "mechanism" declaration. Longer-horizon.

## Re-anchor (locked — Tier-1 only at tick-50)

| version | published `a_share_h8` |
|---|---|
| v0.42 | 0.652 |
| v0.43R | NOT PUBLISHED (informational-only) |
| v0.44 | 0.878 |
| v0.45 | 0.818 |

A_null_V0_25 arm only gates the rollup. B and C arms re-derive their own `a_share_h8` for descriptive logging; do NOT gate the verdict.

## Outputs (locked)

```
runs/v0.53c-reachability-disambiguation-tick200/per_run_per_lineage_v053c.csv
  columns: arm, layout_name, version, seed, hazard, run_id, lineage_id,
           founder_sensor_radius, founder_reproduction_drive, founder_metabolic_rate,
           pre50_food_events_count, pre50_food_energy_acquired,
           pre100_food_events_count, pre100_food_energy_acquired,
           pre200_food_events_count, pre200_food_energy_acquired,
           mean_distance_to_nearest_food_cell_tick50,
           mean_distance_to_nearest_food_cell_tick100,
           mean_distance_to_nearest_food_cell_tick200,
           tick50_living_count, tick50_above_threshold_count, tick50_above_threshold_fraction,
           tick100_living_count, tick100_above_threshold_count, tick100_above_threshold_fraction,
           tick200_living_count, tick200_above_threshold_count, tick200_above_threshold_fraction,
           b50_count, is_eventual_top_b50_label,
           is_high_sensor_radius_lineage,
           is_high_tick50_readiness_fraction_lineage,
           is_high_tick100_readiness_fraction_lineage,
           is_high_tick200_readiness_fraction_lineage

runs/v0.53c-reachability-disambiguation-tick200/audit_summary.csv
  columns: section, key, value
  sections:
    - reanchor_a_share_h8: per (arm, version, h=8) derived + (A_null_V0_25 only) published + drift_abs
    - bridge_reanchor_tick50: per (label, observable) v0.48 / v0.53 / v0.53b published signed_d + v0.53c A_null_V0_25 derived + drift_abs (Tier-1 anchor)
    - bridge_reanchor_tick100: per (label, observable) v0.53b published signed_d + v0.53c A_null_V0_25 derived + drift_abs (SECONDARY sanity check; NOT gating)
    - paired_d_tick50: per (arm, gating-label, observable) — descriptive
    - paired_d_tick100: per (arm, gating-label, observable) — descriptive
    - paired_d_tick200: per (arm, gating-label, observable) — VERDICT-GATING for B_widened
    - b_reachability_tick50: B_widened reachability_run_share_tick_50 (descriptive; should match v0.53)
    - b_reachability_tick100: B_widened reachability_run_share_tick_100 (descriptive; should match v0.53b)
    - b_reachability_tick200: B_widened reachability_run_share_tick_200 (verdict-gating)
    - population_stability: per (arm, window) living_population_run_share + label_a_n_runs + label_b_n_runs (descriptive)
    - sub_verdicts_tick200: per arm — sub-verdict + locked sub-phrase
    - rollup_verdict: locked rollup verdict + locked rollup phrase

runs/v0.53c-reachability-disambiguation-tick200/audit_log.txt
  human-readable echo with all locked phrases verbatim where they fire,
  plus per-arm three-window paired_d tables, B_widened three-window
  reachability table, and per-arm population-stability table.
```

## Implementation plan (locked)

1. **No `src/` changes.** Confirmed.
2. Fresh script `scripts/v0_53c_reachability_disambiguation_tick200_audit.py`. CLI: `uv run python scripts/v0_53c_reachability_disambiguation_tick200_audit.py [--out-dir runs/v0.53c-reachability-disambiguation-tick200]`.
3. Per (version, seed, hazard) tuple, run **3 arms**. Every arm constructs `HHModel` via the normal A_null path; tick observer accumulates events through tick-200.
4. Setup_observer order (matches v0.53 / v0.53b merged implementation): (a) capture v0.53c founder audit table, (b) wire `AgentBorn` / `AteFood` / `HazardDamageApplied` listeners, (c) read back `model.world.width` and assert layout match, (d) capture tick-0 snapshot.
5. Per-tick observer accumulates `pre50_*` / `pre100_*` / `pre200_*` rollups in parallel; emits all three at end-of-run.
6. Use the relaxed contiguous-prefix tick-records invariant from v0.53b (handles early extinction; tick-0 always present).
7. Aggregate per-lineage primaries at all three windows. Compute Label A and three Label B variants (tick50 / tick100 / tick200).
8. Compute paired_d per (arm, gating-label, observable, window) cell. 18 cells per window × 3 windows = 54 cells total. Tick-200 cells gate the verdict; tick-50 / tick-100 are anchor / descriptive. Apply the strict "≥ 2/3 firing cells excluding NaN" rule for sub-verdicts.
9. Compute B_widened reachability_run_share at all three windows. Compute per-arm population-stability metrics (living_population_run_share, label_a_n_runs, label_b_n_runs at all three windows).
10. **Tier-1 bridge re-anchor** (priority 2): A_null_V0_25 arm's six tick-50 cells vs v0.48 / v0.53 / v0.53b published; halt if drift > 1e-3 OR if A_null_V0_25 tick-50 sub-verdict ≠ PRESENT.
11. **Corpus re-anchor** (priority 1): A_null_V0_25 arm only; halt if `a_share_h8` for v0.42 / v0.44 / v0.45 drifts > 1e-3.
12. **Layout opposite-sign halt** (priority 3): scan all tick-200 gating-label cells across all three arms; halt if any signed_d ≤ −0.5.
13. Compute slice rollup verdict per the locked priority + (B reachability tick-200, B sub-verdict tick-200) decision matrix; print + write the locked phrase verbatim.

The reducer is fully self-contained: it reads no `runs/` artifacts. Wall time estimate ~18–30 minutes for 192 runs.

## Test list (locked, 16 tests; extends v0.53b's pattern)

`tests/test_v0_53c_reachability_disambiguation_tick200_audit.py`:

1. **`test_paired_d_function_reproduces_hand_computed_signed_d_on_fixture_and_tier1_constants_match_v048_published_values`** *(re-anchor test, two-part)* — Part A: paired_d formula on a hand-computed fixture pool (8 runs) within 1e-9. Part B: Tier-1 constants byte-equal to v0.48 published values.
2. **`test_a_null_v025_corpus_a_share_h8_re_anchors_v042_v044_v045`** — drift halt fires if any drift > 1e-3.
3. `test_arm_a_null_v025_uses_tight_gradient_layout` — chamber driver receives `tight_gradient_layout()`; layout invariant assert at setup_observer end.
4. `test_arm_b_widened_uses_widened_gradient_layout` — layout invariant assert.
5. `test_arm_c_food_ladder_uses_food_ladder_layout` — layout invariant assert.
6. **`test_founder_traits_byte_identical_across_arms_for_same_seed`** — full Traits records (13 biological + override = None) byte-identical across all three arms at setup_observer end.
7. **`test_founder_positions_byte_identical_across_arms_for_same_seed`** — founder (x, y) byte-identical (all three layouts have spawn_x=1, height=6).
8. **`test_no_src_modifications_compared_to_v0_52b_tip`** — SHA-256 hashes of five pinned src/ files match v0.52b tip's values. Failure message verbatim: `"v0.53c is pre-registered as no-src-change; update the pre-reg before changing src."`
9. `test_label_a_high_sensor_radius_lineage_picks_correct_lineage` — synthetic 5-founder draw; tiebreak `min(lineage_id)`.
10. **`test_label_b_three_variants_three_tier_tiebreak_at_each_window`** — synthetic readiness fractions at tick-50 / tick-100 / tick-200 with two-way tie on fraction → tiebreak by count → tiebreak by min(lineage_id). NaN-loses. Verifies all three Label B variants behave identically except for the snapshot tick.
11. **`test_pre200_window_strictly_extends_pre100_and_pre50_windows`** *(window-extension test)* — synthetic per-tick AteFood events at ticks 10, 30, 60, 90, 130, 180, 200; assert `pre50_food_events_count = 2` (ticks ≤ 50: 10, 30), `pre100_food_events_count = 4` (ticks ≤ 100: 10, 30, 60, 90), `pre200_food_events_count = 7` (ticks ≤ 200: 10, 30, 60, 90, 130, 180, 200). The tick-200 event verifies the inclusive-upper-bound at the window boundary (`tick_now <= TICK_200`); without it the test would not distinguish "≤ 200" from "< 200". Confirms three-window accumulation including the boundary.
12. **`test_subverdict_present_requires_two_thirds_firing_cells_excluding_nan_strict`** — synthetic 3-cell label with 2 firing + 1 NaN → label clears 2/3 (firing count ≥ 2 of 3 total) → arm sub-verdict considers this label PRESENT-contributing. Synthetic 3-cell label with 1 firing + 2 NaN → label clears 1/3 → does NOT contribute. Synthetic 3-cell label with 0 firing + 3 NaN → does NOT contribute. Verifies the locked NaN-strict rule.
13. `test_paired_d_signed_d_le_neg_05_fires_opposite_sign_halt_per_arm` — synthetic any tick-200 cell signed_d = −0.5 → tick-200 sub-verdict OPPOSITE_SIGN_HALT for that arm.
14. **`test_b_reachability_threshold_partition_at_tick_200`** — synthetic `b_reachability_tick200 = 0.20` (< 0.25) → priority 6 BELOW_REACHABILITY_THRESHOLD fires regardless of sub-verdict. Synthetic `b_reachability_tick200 = 0.30` AND B sub-verdict = PRESENT → priority 4 RESOLVED. Synthetic `b_reachability_tick200 = 0.30` AND B sub-verdict ∈ {PARTIAL, NOT_FOUND} → priority 5 RESOLVED_BRIDGE_NOT_FOUND.
15. `test_rollup_locked_phrases_fire_verbatim` — synthetic each priority-4/5/6 outcome → assert locked phrase contains diagnostic substring verbatim:
    - RESOLVED_AT_TICK_200: `"v0.53b's \`WIDENED_BELOW_REACHABILITY_THRESHOLD_AT_TICK_100\` was a tick-100-window artifact"`
    - RESOLVED_BRIDGE_NOT_FOUND_AT_TICK_200: `"the bridge fails to fire even when food primaries become measurable"`
    - BELOW_REACHABILITY_THRESHOLD_AT_TICK_200: `"the bridge cannot be measured on \`widened_gradient\` at any window length the V0_25 substrate's \`N_TICKS=200\` simulation can deliver"`
16. **`test_rollup_priority_cascade_and_partition_total`** — synthesize halt cascade (priorities 1 / 2 / 3); assert priority order. Exhaustively iterate (B reachability ≥ 0.25, B sub-verdict ∈ {PRESENT, PARTIAL, NOT_FOUND}) ∪ (B reachability < 0.25); assert unique outcome per cell. Verify A_null_V0_25 / C_food_ladder non-OPPOSITE outcomes do NOT affect priority 4/5/6.

## Watch-outs (for future-Chronus)

- **No `src/` changes.** Window extension is per-tick observer accumulation only. Smoke test unaffected.
- **B_widened is the primary gating arm.** A_null_V0_25 / C_food_ladder tick-200 cells are descriptive only.
- **Three windows in parallel, single observer pass.** The per-tick observer must accumulate `pre50_*` / `pre100_*` / `pre200_*` AND snapshot `mean_distance_*_tick50` / `_tick100` / `_tick200` from a single iteration. No double-counting; per-event accumulation logic must check `tick_now <= TICK_50` / `<= TICK_100` / `<= TICK_200` independently.
- **Three Label B variants.** Computed in parallel from the same per-lineage `tickN_above_threshold_fraction` values. Each variant is independent (different snapshot tick); tick-200 gates the verdict.
- **Strict "≥ 2/3 firing cells, NaN counts toward denominator" sub-verdict rule.** A label with 3 NaN cells cannot fire PRESENT under that label. Test #12 enforces.
- **Population extinction is expected to be high under B_widened at tick-200** (v0.53b showed 50% by tick-100; tick-200 is likely worse). Reachability metric correctly handles this — extinct populations contribute 0 to reachability numerator.
- **Relaxed contiguous-prefix tick-records invariant** (from v0.53b) is required: B_widened populations going extinct mid-window are normal; the per-tick observer will not be called for ticks after the last living agent dies.
- **Tier-1 anchor at tick-50 only.** Tick-100 cells are a SECONDARY anchor (sanity check vs v0.53b; logged but not gating). Tick-200 cells are the verdict.
- **Locked phrase discipline** verbatim where verdicts fire. Layout names backticked. The priority-4 phrase explicitly references v0.53b's verdict by name; the priority-6 phrase explicitly references v0.53's `BRIDGE_PARTIALLY_GENERALIZES` verdict by name.
- **Determinism north star** ([[scripts/core_smoke_test.py]]) must continue to pass. v0.53c makes no src/ changes.

## Files this slice will create / modify

- `docs/experiments/fear_hunger_v0.53c.md` (this file; Results section appended after reducer run)
- `scripts/v0_53c_reachability_disambiguation_tick200_audit.py` (new)
- `tests/test_v0_53c_reachability_disambiguation_tick200_audit.py` (new, 16 tests)

No `src/` modifications. No prior reducer / audit / test / pre-reg files modified.

## Results

**Status:** reducer executed 2026-05-09 against the 192-run corpus (3 arms × 64 (version, seed, hazard) tuples). Wall time ~15 minutes. **Tier-1 bridge re-anchor PASSES at tick-50** (A_null_V0_25 reproduces v0.48 / v0.53 / v0.53b's six published signed_d cells within max drift 0.0004 ≪ 1e-3). Corpus re-anchor (`a_share_h8`) max drift 0.0003 on v0.42. **Zero opposite-sign halts** under any tick-200 gating-label cell on any of the three arms.

### Rollup verdict — `WIDENED_BELOW_REACHABILITY_THRESHOLD_AT_TICK_200` fires

> **Locked phrase fires verbatim:** "On the modern A_null corpus with the V0_25 substrate held constant and the observation window extended from tick-100 to tick-200 (the full simulation length), fewer than 25% of `widened_gradient` runs have any founder lineage with pre200 food events. B_widened's reachability is below the locked 25% threshold under maximum observation; the bridge cannot be measured on `widened_gradient` at any window length the V0_25 substrate's `N_TICKS=200` simulation can deliver. v0.53's `BRIDGE_PARTIALLY_GENERALIZES` verdict scope is now formally bounded along the (V0_25 substrate × `widened_gradient`) cell; substrate-variation disambiguation (v0.53d candidate) is the natural follow-up."

Sub-verdicts:

| arm | tick-50 (anchor) | tick-100 (descriptive) | tick-200 (verdict-gating) |
|---|---|---|---|
| A_null_V0_25 | `A_NULL_V025_TICK50_BRIDGE_PRESENT` | PRESENT | `A_NULL_V025_TICK200_BRIDGE_PRESENT` (descriptive) |
| B_widened_gradient | n/a | n/a | `B_WIDENED_TICK200_BRIDGE_NOT_FOUND` (drives priority-6 verdict) |
| C_food_ladder | n/a | PARTIAL | `C_LADDER_TICK200_BRIDGE_PARTIAL` (descriptive) |

The locked verdict is gated only on B_widened's reachability metric: `b_reachability_run_share_tick_200 = 0.0000` (0 of 64 runs have any founder lineage with `pre200_food_events_count > 0`). Far below the locked 25% threshold; priority 6 fires with full margin.

### B_widened reachability across all three windows — central finding

| window | reachability | n_runs | passes 25% threshold? |
|---|:-:|:-:|:-:|
| tick-50 | **0.0000** | 64 | False |
| tick-100 | **0.0000** | 64 | False |
| tick-200 | **0.0000** | 64 | False (verdict-gating) |

**Triple-zero reachability across the entire V0_25 simulation lifetime.** On `widened_gradient` no founder lineage produces a single `AteFood` event in any of the 64 runs at any tick from 0 to 200. The 9-cell traversal from spawn (x=1) to food (x ∈ [10..14]) past a 3-wide hazard band is unreachable at every window length the V0_25 substrate's `N_TICKS=200` simulation can deliver.

### B_widened population-stability trajectory

| window | living_population_run_share | label_a_n | label_b_n |
|---|:-:|:-:|:-:|
| tick-50 | 1.0000 | 64 | 64 |
| tick-100 | 0.5000 | 64 | 32 |
| tick-200 | **0.0000** | 64 | **0** |

By tick-200, **every B_widened population is extinct in every one of the 64 runs**. The label_a_n stays at 64 (Label A is trait-resolved on founder records, which persist after extinction); label_b_n drops to 0 (no living lineages → 3-tier readiness-fraction tiebreak resolves to no winner). This is consistent with the V0_25 starting-energy + base-metabolic-cost budget: with no food access, founders deplete energy at the V0_25 metabolic rate × tick count and die before reproducing. Reachability and survival fail together on this layout × substrate.

### Tier-1 bridge re-anchor — A_null_V0_25 tick-50 reproduces v0.48 / v0.53 / v0.53b within 1e-3

Same six cells as v0.48 / v0.53 / v0.53b; max drift 0.0004 (within 1e-3). All cells PASS.

### A_null_V0_25 — three-window paired_d (anchor + descriptive)

| label | observable | tick-50 | tick-100 | tick-200 |
|---|---|:-:|:-:|:-:|
| label_a_sensor_radius | events | +1.066 | +1.028 | **+0.929** (FIRES) |
| label_a_sensor_radius | energy | +1.066 | +1.028 | **+0.929** (FIRES) |
| label_a_sensor_radius | distance | +1.916 | +2.153 | **+2.170** (FIRES) |
| label_b_readiness_fraction_tick{N} | events | +0.916 | +0.790 | **+1.155** (FIRES) |
| label_b_readiness_fraction_tick{N} | energy | +0.916 | +0.790 | **+1.155** (FIRES) |
| label_b_readiness_fraction_tick{N} | distance | +1.179 | +1.264 | **+2.141** (FIRES) |

All 6 tick-200 cells FIRE under both labels (sub-verdict PRESENT). **Notable secondary finding:** Label B (`high_tickN_readiness_fraction_lineage`) strengthens substantially from tick-100 to tick-200 on `tight_gradient` — events/energy go +0.790 → +1.155 (43% increase), distance goes +1.264 → +2.141 (69% increase). The bridge is more discriminative under longer observation on the V0_25-anchored layout, not less. This is descriptive only — does not gate the verdict — but the trajectory is interpretively interesting: dominance dynamics produce stronger Label B–bridge alignment as runs progress, suggesting the lineage that's leading at tick-200 is more strongly correlated with the highest founder sensor_radius than the lineage leading at tick-50.

### B_widened_gradient — three-window paired_d (descriptive at tick-50/100; verdict-gating at tick-200)

| label | observable | tick-50 | tick-100 | tick-200 |
|---|---|:-:|:-:|:-:|
| label_a_sensor_radius | events | nan (n=64) | nan (n=64) | nan (n=64) |
| label_a_sensor_radius | energy | nan (n=64) | nan (n=64) | nan (n=64) |
| label_a_sensor_radius | distance | −0.062 (n=64) | −0.078 (n=64) | −0.041 (n=64) |
| label_b_readiness_fraction_tick{N} | events | nan (n=64) | nan (n=32) | nan (**n=0**) |
| label_b_readiness_fraction_tick{N} | energy | nan (n=64) | nan (n=32) | nan (**n=0**) |
| label_b_readiness_fraction_tick{N} | distance | +7.766 (n=64; degenerate) | +0.460 (n=32) | nan (**n=0**) |

Label B at tick-200 is **fully degenerate** (`n=0` on all 3 cells — no surviving lineages to assign Label B). Label A's food-events / food-energy cells are uniformly zero across all 64 runs (no `AteFood` events ever fired). The lone non-`nan` Label A distance cell at signed_d = −0.041 is far above the −0.5 opposite-sign threshold; no halt fires.

Per the locked strict NaN-counts-toward-denominator sub-verdict rule: Label A clears 0/3 firing cells at tick-200 (3 NaN cells under the rule); Label B clears 0/3 (all NaN due to n=0). **Sub-verdict NOT_FOUND.** B_widened tick-200 is gated by reachability (priority 6); the sub-verdict NOT_FOUND is consistent with reachability=0 and provides no additional information about bridge presence.

### C_food_ladder — three-window paired_d (descriptive)

| label | observable | tick-50 | tick-100 | tick-200 |
|---|---|:-:|:-:|:-:|
| label_a_sensor_radius | events | +1.186 (FIRES) | +1.148 (FIRES) | **+1.039** (FIRES) |
| label_a_sensor_radius | energy | +1.186 (FIRES) | +1.148 (FIRES) | **+1.039** (FIRES) |
| label_a_sensor_radius | distance | +1.804 (FIRES) | +1.882 (FIRES) | **+1.789** (FIRES) |
| label_b_readiness_fraction_tick{N} | events | +0.621 (FIRES) | +0.342 | **+0.211** |
| label_b_readiness_fraction_tick{N} | energy | +0.621 (FIRES) | +0.342 | **+0.211** |
| label_b_readiness_fraction_tick{N} | distance | +0.939 (FIRES) | +0.730 (FIRES) | **+0.800** (FIRES) |

Sub-verdict trajectory across windows: PRESENT (tick-50) → PARTIAL (tick-100) → PARTIAL (tick-200). **Notable secondary finding:** Label B's bridge degrades systematically across windows on `food_ladder`. Events/energy go +0.621 → +0.342 → +0.211 (steady decline below the +0.5 threshold from tick-100 onward); distance stays above threshold (+0.939 → +0.730 → +0.800) but weakens from tick-50 to tick-100 then partially recovers at tick-200. Label A holds across all three windows (3/3 FIRES at every window). The asymmetric Label A vs Label B trajectory on `food_ladder` is interesting — it suggests dominance dynamics at tick-100/200 on `food_ladder` are **less aligned** with the lineage that produces highest tick-N readiness fraction, possibly because the pre-food column at x=4 lets multiple lineages reach reproductive eligibility at similar rates (compressing Label B's discriminative power) while sensor_radius continues to track spatial advantage. Descriptive only — does not gate the verdict.

### v0.53b's tick-100 cells re-anchor (SECONDARY, non-gating)

A_null_V0_25 tick-100 cells reproduce v0.53b's tick-100 measurements byte-equivalently (logged in `audit_summary.csv` `bridge_reanchor_tick100` section). Same RNG / founder draw / per-tick world dynamics under tick-100 accumulation across v0.53b → v0.53c. No drift; the SECONDARY anchor passes as expected.

### Corpus re-anchor

A_null_V0_25 arm — all PASS (max drift 0.0003):

| version | derived `a_share_h8` | published | drift |
|---|:-:|:-:|:-:|
| v0.42 | 0.652 | 0.652 | 0.0003 |
| v0.43R | 0.674 | — (informational) | — |
| v0.44 | 0.878 | 0.878 | 0.0001 |
| v0.45 | 0.818 | 0.818 | 0.0002 |

### What v0.53c can safely claim

- ✓ **A_null_V0_25 tick-50 anchor PASSES** within 0.0004 of v0.48 / v0.53 / v0.53b. Reducer machinery (paired_d formula, three-window observer, three Label B variants, label assignment) is correct.
- ✓ **A_null_V0_25 tick-200 sub-verdict is PRESENT** (6/6 cells fire) — the bridge holds on `tight_gradient` under maximum observation. Label B's bridge **strengthens** at tick-200 (events/energy +0.790 → +1.155; distance +1.264 → +2.141). Descriptive — does not gate.
- ✓ **B_widened reachability is exactly 0.0000 at all three windows** (tick-50, tick-100, tick-200). 0 of 64 runs produce any `AteFood` event. The `widened_gradient` layout × V0_25 substrate combination structurally prevents food access at every window length the available 200-tick simulation can deliver.
- ✓ **B_widened populations go to full extinction by tick-200** (living_population_run_share = 0.0000 at tick-200; was 0.5000 at tick-100 and 1.0000 at tick-50). Reachability and survival fail together on this layout × substrate.
- ✓ **v0.53's `BRIDGE_PARTIALLY_GENERALIZES` verdict scope is now formally bounded along the (V0_25 substrate × `widened_gradient`) cell.** The B_widened NOT_FOUND is reachability-bound at every measurable window; it is NOT a window artifact. The verdict scope is "the V0_25 substrate cannot measure the bridge on `widened_gradient` in any window the available simulation can deliver".
- ✓ **C_food_ladder Label A bridge holds at every window** (3/3 FIRES at tick-50, tick-100, tick-200). The bridge magnitude on `food_ladder` is comparable to V0_25 across windows under Label A.
- ✓ **No opposite-sign halts.** All 18 tick-200 paired_d cells across the three arms either fire expected, fall sub-threshold, or are `nan`; none falls below −0.5.

### What v0.53c cannot claim

- ✗ **"`widened_gradient` is universally unreachable."** v0.53c tests V0_25 substrate × N_TICKS=200 only. Different metabolic / energy / policy parameters may admit reachability. v0.53d (substrate variation) is the natural follow-up.
- ✗ **"Population extinction on `widened_gradient` is layout-caused."** The triple-zero reachability + full extinction under V0_25 is consistent with both "geometry too far for the substrate's energy budget" and "substrate's energy budget too small for the geometry's traversal cost". v0.53c does not isolate which.
- ✗ **A revised v0.53 / v0.53b verdict.** Both stand. v0.53c is the maximum-window probe within the locked V0_25 substrate.
- ✗ **Causal contribution of `sensor_radius` per layout.** v0.53c is observational. Reading-A causal-generalization slice remains the deferred candidate (and would naturally exclude `widened_gradient` per v0.53c's finding).
- ✗ **Mechanism behind the A_null_V0_25 Label B strengthening at tick-200** (a notable secondary finding — events/energy go +0.790 → +1.155). Plausible: tick-200 dominance dynamics filter for high-sensor_radius lineages more strongly than tick-100 readiness alone. Not formally established.
- ✗ **Mechanism behind the C_food_ladder Label B degradation across windows** (events/energy go +0.621 → +0.342 → +0.211). Plausible: pre-food column compresses Label B's discriminative power as multiple lineages converge on similar readiness fractions. Not formally established.

### Cross-corpus context

| slice | corpus | claim | strength |
|---|---|---|---|
| v0.46 | modern A_null | tick-50 readiness predicts dominance | observational (PRESENT) |
| v0.47 | modern A_null | founder `sensor_radius` predicts tick-50 readiness | observational (PARTIAL) |
| v0.48 | modern A_null | `sensor_radius` ↔ spatial bridge | observational (PRESENT under both labels) |
| v0.49 | modern A_null | founder `sensor_radius` causal contribution | interventional (SUPPORTED) |
| v0.50 | modern A_null | v0.49's contribution survives position controls | interventional (ROBUST) |
| v0.51 | modern A_null | founder-clamp NOT_FOUND result preserved under lineage-wide clamp | interventional (REPRODUCED) |
| v0.52 | modern A_null | metabolic-cost channel not necessary for bridge | interventional (B PRESENT) |
| v0.52b | modern A_null | bridge follows information-radius assignment under preserved global ecology | interventional (FOLLOWS_ASSIGNMENT) |
| v0.53 | modern A_null | bridge fires PRESENT on `tight_gradient` and `food_ladder`, NOT_FOUND on `widened_gradient` | observational (PARTIALLY_GENERALIZES) |
| v0.53b | modern A_null | `widened_gradient` NOT_FOUND at tick-100 is reachability-bound (0/64 reach food, 50% extinction) | observational (BELOW_REACHABILITY_THRESHOLD_AT_TICK_100) |
| v0.53c | modern A_null | `widened_gradient` reachability = 0/64 at every window 50/100/200; full extinction by tick-200; v0.53's `BRIDGE_PARTIALLY_GENERALIZES` verdict scope is now formally bounded to (V0_25 substrate × `widened_gradient`) cell | observational (BELOW_REACHABILITY_THRESHOLD_AT_TICK_200; substrate-variation = v0.53d candidate) |

The v0.46→v0.53c stack now reads: ... → v0.53 says the bridge fires on `tight_gradient` and `food_ladder` but not on `widened_gradient` at tick-50 → v0.53b says `widened_gradient`'s tick-100 NOT_FOUND is reachability-bound → **v0.53c says `widened_gradient`'s reachability is zero at every window the V0_25 substrate's 200-tick simulation can deliver, and populations go to full extinction by tick-200; the layout × V0_25 substrate combination structurally prevents food access; v0.53's verdict scope is formally bounded to layouts that admit reachability under V0_25.**

### Notable secondary findings (descriptive only)

1. **A_null_V0_25 Label B bridge strengthens at tick-200** on `tight_gradient`: events/energy go +0.790 (tick-100) → +1.155 (tick-200), distance goes +1.264 → +2.141. Suggests tick-200 dominance dynamics filter for high-sensor_radius lineages more strongly than tick-100 readiness alone. Worth tracking in any future Reading-A causal-generalization slice on `tight_gradient`.

2. **C_food_ladder Label B bridge degrades systematically across windows** on `food_ladder`: events/energy go +0.621 (tick-50) → +0.342 (tick-100) → +0.211 (tick-200). Below the +0.5 threshold from tick-100 onward. Distance cell stays above threshold across all windows. The asymmetric Label A vs Label B trajectory on `food_ladder` warrants flagging as a layout-window interaction worth investigating in future slices.

### Next-step candidates (open; not locked)

The v0.53c verdict closes the window-extension question definitively for `widened_gradient` × V0_25 and motivates substrate variation as the next disambiguation:

- **v0.53d — substrate-variation disambiguation on `widened_gradient`.** Modify V0_25 substrate parameters (lower `base_metabolic_cost`, higher `starting_energy` / `max_energy`, etc.) on `widened_gradient` only; tests whether reachability is parameter-bound or geometry-bound. Independent observational slice; introduces 1+ new arms with explicit substrate variants.
- **v0.53e (or later) — Reading-A causal-generalization slice on layouts admitting the bridge.** Re-run v0.49's null + clamp_4 + permutation_5! per layout that admits measurement (`tight_gradient` + `food_ladder`); skip `widened_gradient` per v0.53c's finding. ~384 runs.
- **v0.53f (or later) — investigate the C_food_ladder Label B degradation trajectory.** Why does Label B's bridge weaken from tick-50 to tick-200 specifically on `food_ladder` while Label A holds? Could be a dominance-dynamics question or a readiness-fraction-discriminative-power question. Per-tick-window paired_d trajectory probe.
- **v0.54 — joint ablation** (zero-cost AND shuffle). Channel-interaction question. Independent of layout-axis findings.
- **Eventual fresh-stream calibration** on the v0.46–v0.53c conclusion stack — needed for any "mechanism" declaration. Longer-horizon.

User has not locked which slice is next.

### CI gate at v0.53c close

```
uv run ruff check .             ok
uv run ruff format --check .    ok
uv run pytest                   1744 passed, 7 skipped (was 1728; +16 v0.53c)
uv run python scripts/core_smoke_test.py                                ok (default behavior preserved; src/ untouched)
uv run python scripts/v0_53c_reachability_disambiguation_tick200_audit.py        WIDENED_BELOW_REACHABILITY_THRESHOLD_AT_TICK_200
```
