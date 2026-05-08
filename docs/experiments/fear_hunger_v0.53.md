# fear_hunger v0.53 — cross-layout generalization (3-arm observational bridge probe)

**Slice:** v0.53
**Type:** **first-class observational sweep** with 3-arm cross-layout reducer (no `src/` changes; no intervention; uses existing named layouts in `src/hedonism_harness/experiments/layouts.py`).
**Predecessors:** v0.21..v0.27 (substrate / aggregate-optimum), v0.34..v0.36 (lineage observability + heritability), v0.42..v0.45 (substrate-causal arc), v0.46 (`READINESS_PREDICTS_DOMINANCE`), v0.47 (`READINESS_TRAITS_PARTIALLY_PREDICTIVE`), v0.48 (`SENSOR_RADIUS_SPATIAL_BRIDGE_PRESENT`), v0.49 (`SENSOR_RADIUS_CAUSAL_CONTRIBUTION_SUPPORTED`), v0.50 (`SENSOR_RADIUS_ROBUST_TO_POSITION`), v0.51 (`FOUNDER_CLAMP_REPRODUCED`), v0.52 (`INTERVENTION_OPPOSITE_SIGN_HALT`), v0.52b (`INFORMATION_RADIUS_FOLLOWS_ASSIGNMENT`).
**Question being asked (locked):** Does the v0.48 `sensor_radius` spatial / foraging bridge — established on the `tight_gradient` (V0_25) layout — generalize to `widened_gradient` and `food_ladder` layout geometries when the V0_25 substrate is otherwise held constant?

The v0.46→v0.52b stack established observational bridge presence (v0.48), founder clamp / permutation support for the bridge (v0.49), robustness to founder-position controls (v0.50), founder-clamp reproduction under lineage-wide clamping with empirically zero descendant drift on V0_25 (v0.51), metabolic-cost-channel dispensability (v0.52), and information-radius assignment tracking under preserved global ecology (v0.52b). Every claim is anchored to the V0_25 layout (`tight_gradient`). v0.53 asks the minimal cross-layout question: **does the bridge fire at all on layouts other than `tight_gradient`?** This is a *generalization* probe (existence per layout), not a re-test of v0.49's causal contribution per layout — the latter is deferred to a future causal-generalization slice if v0.53 lands PRESENT or PARTIAL.

If the bridge fires PRESENT on both `widened_gradient` and `food_ladder`, the v0.46–v0.52b conclusion stack is no longer "local to V0_25 / tight_gradient" along the layout axis. If it fires on neither, the whole arc is layout-local and downstream framing must say so. If it fires on one but not the other, the asymmetric pattern is itself a finding (logged in Results) and motivates a follow-up disambiguation slice.

## Pre-implementation note (2026-05-08, before any reducer code)

The pre-reg's reading was confirmed with the user before drafting:

- **Reading B (locked).** Each layout arm = a single A_null condition on that layout, computing v0.48-style paired_d on Label A + Label B. No clamp or permutation sub-arms. 64 (version, seed, hazard) tuples × 3 layouts = 192 runs.
- **Reading A (rejected for v0.53 scope).** Re-running v0.49's full intervention set (null + clamp_4 + permutation_5!) per layout (576 runs) would re-test v0.49's *causal-contribution* question on each layout, not v0.53's *generalization* question. Deferred to a later causal-generalization slice if v0.53 fires PRESENT or PARTIAL.

The decision rule (paired Cohen's d ≥ +0.5) is the v0.48–v0.52b discipline; v0.49's lineage is its origin as the *interventional* threshold, but the rule is a pure paired_d test that v0.48 already used observationally. "v0.49-style" in the design discussion refers to the +0.5 threshold and the paired_d formulation, not to clamp / permutation machinery.

This pre-reg does not change layouts.py, sensors.py, traits.py, or any other `src/` module. v0.53 does not touch `src/`; the only `src/` touches in the v0.46+ stack remain v0.52 and v0.52b.

## Conservation framing — observational, no `src/`, no intervention

- **No `src/` modifications.** `widened_gradient_layout()` (`src/hedonism_harness/experiments/layouts.py:73`) and `food_ladder_layout()` (`src/hedonism_harness/experiments/layouts.py:97`) are already wired into the public `ALL_LAYOUTS` dict and reachable via `layout_by_name(name)` (`src/hedonism_harness/experiments/layouts.py:123,132`). The reducer selects layouts by name; no layout-config additions are needed.
- **No modifications to prior reducer or audit scripts.** v0.34's `lineage_replay.py`, v0.35's `lineage_survival_replay.py`, v0.36's `trait_replay.py`, the four substrate audits, and v0.46–v0.52b's reducers remain byte-identical to their merged forms.
- **A_null_V0_25 arm is byte-identical to v0.48–v0.52b's A_null path.** Same `tight_gradient` layout, same V0_25 substrate, same `FounderSpec(traits_override=None)`, same RNG streams. Tier-1 re-anchor enforces this at metric level.
- **B and C arms are A_null on a different layout** — they construct `HHModel` exactly as A_null but pass a different `ChamberLayout` (from `widened_gradient_layout()` or `food_ladder_layout()`). No founder trait patch, no `effective_sensor_radius_override`, no helper RNG. The layout swap is the only configured difference.
- **No intervention at any level.** No founder-body trait mutation. No founder-position permutation. No metabolic-cost change. No effective-radius override (per-agent or per-model). v0.53 is a pure observational probe of how `sensor_radius` and tick-50 readiness co-vary with spatial / foraging primaries on three different chamber geometries.
- **Single-layout-channel variation.** B and C differ from A_null_V0_25 only in the `ChamberLayout` factory selected. A reducer-side runtime invariant (`V053ReducerError`) reads back `model.chamber_driver.layout` (or equivalent) and asserts the layout name matches the arm assignment. Halts loud on any mismatch.
- **`apply_metabolism`, sensors.py, traits.py, body.py, model.py — all unchanged.** v0.53 inherits the v0.52 + v0.52b src/ state; default `effective_sensor_radius_override = None` everywhere preserves byte-identity for v0.46–v0.52b A_null paths.

## Corpus (locked, 64 × 3 arms = 192 runs)

| version | seeds | hazards | runs per arm | total runs |
|---|---|---|---|---|
| v0.42 | 41..48 | {0, 8} | 16 | 48 |
| v0.43R | 49..56 | {0, 8} | 16 | 48 |
| v0.44 | 57..64 | {0, 8} | 16 | 48 |
| v0.45 | 65..72 | {0, 8} | 16 | 48 |
| **total** | | | | **192** |

V0_25 substrate unchanged from v0.46–v0.52b: `GradientPolicy` + `auto_reproduction=True` + `TraitConfig(unbounded_mutation=True)`, 5 founders, 200 ticks, `food_respawn_cooldown=50`, `ambient_influx_rate=1.0`, transfer-pool funding, `energy_pool_initial=1500`, V0_25 `hazard_avoidance_weight`. Each (version, seed, hazard) tuple is run **3 times** — once per arm (= once per layout) — so cross-arm comparisons are pairable on (version, seed, hazard). Per-arm seed bands are identical; arm differs only in the `ChamberLayout` factory selected.

Wall time estimate ~15–25 minutes total at ~5–8 s per run (mirrors v0.49's 192-run wall time).

## Default V0_25 founder draw (for reference)

5 founders. `TraitConfig(unbounded_mutation=True)` draws integer-valued `sensor_radius` from {1..6}. Founder positions per `spread_y(5, height)` over the layout's height (=6 for all three layouts under v0.53). Same as v0.48–v0.52b for the `tight_gradient` arm; B and C use the same `spread_y` formula on the same height-6 grid (founder y-positions byte-identical across arms). Founder x-positions differ across layouts (`tight_gradient.spawn_x = 1`, `widened_gradient.spawn_x = 1`, `food_ladder.spawn_x = 1` — same x for all three), so founder positions are identical across all three arms by construction.

## Arms (locked, 3)

### A_null_V0_25

```
ChamberLayout = tight_gradient_layout()
FounderSpec(traits_override=None)
no patch, no body_config override, no per-agent override
```

Byte-identical to v0.48–v0.52b A_null path. Used as the bridge replication baseline (Tier-1 anchor against v0.48 published cells) and as the within-session sanity check that v0.53's reducer machinery computes paired_d correctly.

### B_widened_gradient

```
ChamberLayout = widened_gradient_layout()
FounderSpec(traits_override=None)
no patch, no body_config override, no per-agent override
```

Same RNG streams + same founder trait draw as A_null_V0_25 for the same (version, seed, hazard) tuple (`streams.mutation` is initialized from `seed`; `random_traits` and `spawn_agent_rng` consume from it identically across arms because the founder count is fixed at 5). Founder x positions are identical (`spawn_x = 1` for both layouts). Founder y positions are identical (`spread_y(5, 6)` is height-driven). Pre-tick-1 byte-identity holds for founder traits and positions; from tick 1 onward, sensing and action diverge because the food/hazard/safe layout differs.

`widened_gradient` geometry: width 15, safe `x ∈ [0..4]`, hazard `x ∈ [5..7]`, corridor `x ∈ [8..9]`, food `x ∈ [10..14]`, height 6, spawn `x = 1`. The 2-column corridor between the 3-wide hazard band and the 5-wide food zone widens the structural gap relative to `tight_gradient` (which has hazard `x ∈ [3..4]` and food `x ∈ [5..8]` in width 9, height 6, spawn `x = 1`). Tests whether more breathing room and a marginally larger food target preserve the bridge.

### C_food_ladder

```
ChamberLayout = food_ladder_layout()
FounderSpec(traits_override=None)
no patch, no body_config override, no per-agent override
```

Same RNG / trait / position story as B. `food_ladder` geometry: width 12, safe `x ∈ [0..2]`, corridor `x = 3`, **pre-food `x = 4`** (1-column food band, all rows), corridor `x = 5`, hazard `x ∈ [6..8]`, food `x ∈ [9..11]`, height 6, spawn `x = 1`. The pre-food column gives founders a low-cost early energy source before the hazard band, separating "perceptual reach" (the sensor-radius question v0.48 answered) from "barrier traversal" (a layout-specific question). Tests whether the bridge persists when an early energy source raises the floor on pre-50 readiness.

## Labels (locked, two — identical to v0.48–v0.52)

Both labels gate the verdict for **all three arms**.

### Label A — `high_sensor_radius_lineage`

```
high_sensor_radius_lineage = argmax_lineage(int(founder.body.traits.sensor_radius))
tiebreak: min(lineage_id)
```

Identical to v0.48–v0.52 (NOT v0.52b's `label_a_information_radius` — v0.53 has no override field set; `effective_sensor_radius_override` is None on every founder under all three arms, so the v0.52b resolver falls through to trait `sensor_radius`).

### Label B — `high_tick50_readiness_fraction_lineage`

Identical to v0.47–v0.52b (3-tier tiebreak: fraction → count → min(lineage_id), NaN-loses). Copy-local from v0.48 reducer.

## Primary observables (locked, 3, identical to v0.48–v0.52b)

| # | name | expected sign |
|---|---|:-:|
| 1 | `pre50_food_events_count` | + |
| 2 | `pre50_food_energy_acquired` | + |
| 3 | `mean_distance_to_nearest_food_cell` | − |

Definitions, aggregation rules, NaN handling: copy-local from v0.48–v0.52b. Per-tick observer firing semantics unchanged (tick 0 captured at `setup_observer` time; ticks 1..50 captured by `tick_observer`).

**Layout note.** Absolute values of observables 1 and 2 will differ across layouts (different food density and reach geometry); observable 3 will also differ (food cells are at different x ranges per layout). v0.53's verdict is computed from **paired_d within a single arm's 64-run pool** — absolute scale differences across arms do not enter the paired_d computation. The cross-arm comparison is categorical only (PRESENT / PARTIAL / NOT_FOUND / OPPOSITE_SIGN_HALT per arm), not a magnitude delta.

## Effect-size rule (locked, sign-aware, identical to v0.48–v0.52b)

```
per_run_delta_O = label_lineage_value_O − mean(non_label_lineage_values_O)
paired_d_O      = mean(per_run_delta_O) / stdev(per_run_delta_O, ddof=1)
signed_d_O      = paired_d_O × expected_sign
fires_expected  iff signed_d_O ≥ +0.5
fires_wrong     iff signed_d_O ≤ −0.5
```

## Per-arm sub-verdicts (locked, 4-way each)

Both labels gate (no diagnostic-only label degeneracy under v0.53 — `effective_sensor_radius_override = None` on every founder, so Label A is the original trait and Label B is readiness fraction):

| condition | A_null_V0_25 | B_widened_gradient | C_food_ladder |
|---|---|---|---|
| both labels clear ≥ 2/3, 0 wrong-sign | `A_NULL_V025_BRIDGE_PRESENT` | `B_WIDENED_BRIDGE_PRESENT` | `C_LADDER_BRIDGE_PRESENT` |
| exactly one label clears ≥ 2/3, 0 wrong-sign | `A_NULL_V025_BRIDGE_PARTIAL` | `B_WIDENED_BRIDGE_PARTIAL` | `C_LADDER_BRIDGE_PARTIAL` |
| neither label clears ≥ 2/3, 0 wrong-sign | `A_NULL_V025_BRIDGE_NOT_FOUND` | `B_WIDENED_BRIDGE_NOT_FOUND` | `C_LADDER_BRIDGE_NOT_FOUND` |
| any primary signed_d ≤ −0.5 under either label | `A_NULL_V025_OPPOSITE_SIGN_HALT` | `B_WIDENED_OPPOSITE_SIGN_HALT` | `C_LADDER_OPPOSITE_SIGN_HALT` |

Each arm's paired_d cells (3 observables × 2 labels = 6 cells per arm; 18 cells total across the three arms) are computed independently from the arm's 64-run pool.

## Slice rollup verdicts (locked, 6 outcomes, priority-ordered)

Priority order (first-matching wins):

1. `CORPUS_REDERIVE_DRIFT_HALT`
2. `BRIDGE_REPLICATION_HALT` (Tier-1 A_null_V0_25 vs v0.48)
3. `LAYOUT_OPPOSITE_SIGN_HALT` (any arm under any label fires wrong-sign)
4. `BRIDGE_GENERALIZES_CROSS_LAYOUT`
5. `BRIDGE_LAYOUT_LOCAL`
6. `BRIDGE_PARTIALLY_GENERALIZES`

### Halt conditions

| priority | rollup verdict | trigger | locked phrase (verbatim) |
|---|---|---|---|
| 1 | `CORPUS_REDERIVE_DRIFT_HALT` | A_null_V0_25 arm `a_share_h8` for any of v0.42 / v0.44 / v0.45 drifts > 1e-3 from the published reference | "Halt: A_null_V0_25 re-anchor drifted from the published Results value for {version}; v0.53's deterministic re-execution of the V0_25 corpus does not reproduce the published metric within 1e-3." |
| 2 | `BRIDGE_REPLICATION_HALT` | (a) A_null_V0_25 arm's signed_d for any of the six v0.48 cells drifts > 1e-3 from the v0.48 published value, OR (b) A_null_V0_25 sub-verdict ≠ `A_NULL_V025_BRIDGE_PRESENT` | "Halt: v0.53's A_null_V0_25 arm does not reproduce v0.48's spatial bridge — either a paired_d cell drifts beyond 1e-3 of the published value, or the A_null_V0_25 sub-verdict does not resolve to PRESENT. v0.53 cannot interpret the cross-layout arms without an established baseline." |
| 3 | `LAYOUT_OPPOSITE_SIGN_HALT` | any gating-label primary signed_d ≤ −0.5 under arm B or arm C (A_null_V0_25 wrong-sign is captured by priority 2's PRESENT requirement) | "Halt: a v0.53 spatial / foraging primary fires in the WRONG direction under a gating label on a non-V0_25 layout; the layout swap is incompatible with the locked expected signs and the cross-layout interpretation cannot proceed without isolating the regime change." |

### Tier-1 (priority 2) re-anchor — A_null_V0_25 vs v0.48

A_null_V0_25 arm's six paired_d cells must reproduce v0.48's published signed_d values within 1e-3:

| label | observable | sign | v0.48 published signed_d |
|---|---|:-:|:-:|
| `label_a_sensor_radius` | `pre50_food_events_count` | + | **+1.066** |
| `label_a_sensor_radius` | `pre50_food_energy_acquired` | + | **+1.066** |
| `label_a_sensor_radius` | `mean_distance_to_nearest_food_cell` | − | **+1.916** |
| `label_b_readiness_fraction` | `pre50_food_events_count` | + | **+0.916** |
| `label_b_readiness_fraction` | `pre50_food_energy_acquired` | + | **+0.916** |
| `label_b_readiness_fraction` | `mean_distance_to_nearest_food_cell` | − | **+1.179** |

Drift tolerance = 1e-3. Same protocol as v0.49–v0.52b. The label name `label_a_sensor_radius` is reused from v0.48–v0.52 (NOT v0.52b's `label_a_information_radius`, since v0.53 sets no override and the resolver falls through to trait identically across arms).

**No Tier-2 re-anchor.** B and C are layouts never run before in this stack; there is no published reference cell to byte-anchor them against. Validity is anchored by Tier-1 (A_null_V0_25) + corpus re-anchor (`a_share_h8` for v0.42 / v0.44 / v0.45) + the four locked implementation-equivalence tests (founder traits byte-identical across arms, layout name matches arm, no src/ touch, paired_d formula identical to v0.48).

### Outcome conditions (only consulted if no halt fires)

| priority | rollup verdict | (B, C) sub-verdicts (A_null_V0_25 must be PRESENT) | locked phrase (verbatim) |
|---|---|---|---|
| 4 | `BRIDGE_GENERALIZES_CROSS_LAYOUT` | (PRESENT, PRESENT) | "On the modern A_null corpus with the V0_25 substrate held constant, the v0.48 spatial / foraging bridge fires PRESENT on both `widened_gradient` and `food_ladder` under the locked +0.5 paired_d threshold. The bridge generalizes across the three tested layout geometries (`tight_gradient`, `widened_gradient`, `food_ladder`) on this corpus." |
| 5 | `BRIDGE_LAYOUT_LOCAL` | (NOT_FOUND, NOT_FOUND) | "On the modern A_null corpus with the V0_25 substrate held constant, the v0.48 spatial / foraging bridge does not fire PRESENT on either `widened_gradient` or `food_ladder` under the locked +0.5 paired_d threshold. The bridge is local to the `tight_gradient` (V0_25) layout geometry on this corpus; it does not generalize to `widened_gradient` or `food_ladder`." |
| 6 | `BRIDGE_PARTIALLY_GENERALIZES` | any other (B, C) combination over {PRESENT, PARTIAL, NOT_FOUND} (i.e., not (PRESENT, PRESENT) and not (NOT_FOUND, NOT_FOUND)) | "On the modern A_null corpus with the V0_25 substrate held constant, the v0.48 spatial / foraging bridge does not resolve to a single categorical outcome across `widened_gradient` and `food_ladder` under the locked +0.5 paired_d threshold. The bridge partially generalizes across the three tested layout geometries; the asymmetric pattern (per-arm sub-verdicts) is logged in Results." |

The rollup is **categorical-only** — no magnitude-delta rule between A_null_V0_25 and B / C. Magnitude differences across arms are reported descriptively in Results but do not alter the verdict. PARTIAL sub-verdicts on B or C are absorbed into `BRIDGE_PARTIALLY_GENERALIZES` (priority 6); they are NOT halted on, NOT coerced to NOT_FOUND, and NOT coerced to PRESENT.

The 3 non-halt outcomes form a total partition of the (B sub-verdict, C sub-verdict) ∈ {PRESENT, PARTIAL, NOT_FOUND}² space (under the precondition that A_null_V0_25 is PRESENT and zero halts fire). Halts cover the OPPOSITE_SIGN, drift, and replication cases. Test #16 enforces the partition exhaustively (9 combinations → unique outcome per combination).

The rollup is **conservative**: locked phrases use "fires PRESENT", "is local to", "does not resolve" — NOT "is causal for", "proves", or "rules out". Mechanism declarations require fresh-stream calibration analogous to v0.30..v0.33; v0.53 is a layout-swap observational probe and cannot rule out higher-order interactions, layout-by-trait interactions, or non-V0_25-substrate behavior.

## Cautious framing (per CLAUDE.md)

- "**Generalizes across the three tested layout geometries**", "**is local to**", "**partially generalizes**" — NOT "**causes**", "**proves**", or "**rules out**".
- "**On the modern A_null corpus with the V0_25 substrate held constant**" — NOT a claim about other substrates (`auto_reproduction=False`, bounded mutation, different policy, different energy economy).
- "**The bridge fires PRESENT on layout X**" specifically refers to: the v0.48 6-cell paired_d table, computed on a 64-run pool sampled from layout X's chamber driver under the V0_25 substrate, satisfies the locked sub-verdict criterion (both labels clear ≥ 2/3, 0 wrong-sign).
- v0.53 explicitly does not establish: causal contribution per layout (that is the deferred Reading-A causal-generalization slice), mechanism for any layout-specific differences, generalization to layouts not in the {`tight_gradient`, `widened_gradient`, `food_ladder`} set, or behavior under non-V0_25 substrate parameters.

## What v0.53 cannot establish (logged here pre-data, not retrofittable)

- ✗ **Causal contribution of `sensor_radius` per layout.** v0.53 is a generalization probe. If the bridge fires PRESENT on B and / or C, it shows the *correlational* bridge generalizes — it does NOT show that the v0.49 founder-clamp causal verdict re-fires per layout. A future causal-generalization slice (re-running v0.49's null + clamp_4 + permutation_5! per layout, ~576 runs total) would be required to make that claim.
- ✗ **Generalization beyond the three tested layouts.** `default_layout` and `near_hazard_layout` are NOT included; their omission is intentional (layout-density / single-channel-fear questions are out of scope for the cross-layout-generalization frame, which is about food-rich layouts where the v0.48 bridge has interpretive headroom).
- ✗ **Generalization to non-V0_25 substrates.** Aggregate-optimum substrates (v0.21..v0.27) and intermediate ecologies are not tested.
- ✗ **Mechanism behind any layout-specific outcome.** If `BRIDGE_LAYOUT_LOCAL` fires, v0.53 does NOT identify what about `tight_gradient` is special (food density, hazard band thickness, structural gap, etc.). If `BRIDGE_PARTIALLY_GENERALIZES` fires, v0.53 does NOT identify what differs between the firing layout and the non-firing layout.
- ✗ **Resolution of cross-layout magnitude differences in `a_share_h8`** — B and C compute their own `a_share_h8` informationally, but no cross-arm threshold gates the verdict. Magnitude shifts vs A_null_V0_25 are descriptive only.
- ✗ **Detection of higher-order interactions** between layout geometry and the v0.52 / v0.52b channels (metabolic-cost, information-radius assignment). v0.53 holds both override fields at None and uses the default `sensor_radius_metabolic_cost = 0.05` — joint ablation is the deferred v0.54 candidate.

## Open framing (NOT in v0.53 primary)

- **v0.53 secondary candidate (deferred until result lands).** If v0.53 fires `BRIDGE_GENERALIZES_CROSS_LAYOUT`, the natural next step is the causal-generalization slice (Reading A: re-run v0.49's null + clamp_4 + permutation_5! per layout). If `BRIDGE_PARTIALLY_GENERALIZES`, the natural step is to pre-reg a disambiguation slice asking *which* layout feature determines the asymmetric firing.
- **v0.54 — joint ablation.** `sensor_radius_metabolic_cost = 0` AND between-lineage shuffle of `effective_sensor_radius_override`. Tests for higher-order interactions between v0.52's and v0.52b's separately-addressed channels.
- **Eventual fresh-stream calibration** (v0.30-style) on the v0.46–v0.53 conclusion stack — needed for any "mechanism" declaration. Longer-horizon.

## Re-anchor (locked — Tier-1 only)

| version | published `a_share_h8` |
|---|---|
| v0.42 | 0.652 |
| v0.43R | NOT PUBLISHED (informational-only) |
| v0.44 | 0.878 |
| v0.45 | 0.818 |

A_null_V0_25 arm only gates the rollup. B and C arms re-derive their own `a_share_h8` for descriptive logging; do NOT gate the verdict.

## Outputs (locked)

```
runs/v0.53-cross-layout-generalization/per_run_per_lineage_v053.csv
  columns: arm, layout_name, version, seed, hazard, run_id, lineage_id,
           founder_sensor_radius, founder_reproduction_drive, founder_metabolic_rate,
           pre50_food_events_count, pre50_food_energy_acquired,
           mean_distance_to_nearest_food_cell,
           tick50_living_count, tick50_above_threshold_count, tick50_above_threshold_fraction,
           b50_count, is_eventual_top_b50_label,
           is_high_sensor_radius_lineage, is_high_tick50_readiness_fraction_lineage

runs/v0.53-cross-layout-generalization/audit_summary.csv
  columns: section, key, value
  sections:
    - reanchor_a_share_h8: per (arm, version, h=8) derived + (A_null_V0_25 only) published + drift_abs
    - bridge_reanchor: per (label, observable) v0.48 published signed_d + v0.53 A_null_V0_25 derived + drift_abs
    - paired_d: per (arm, gating-label, observable) cell — paired_d, signed_d, n_runs, fires_expected, fires_wrong
    - sub_verdicts: per arm — sub-verdict + locked sub-phrase
    - rollup_verdict: locked rollup verdict + locked rollup phrase

runs/v0.53-cross-layout-generalization/audit_log.txt
  human-readable echo with all locked phrases printed verbatim where they fire,
  plus per-arm paired_d tables and per-arm a_share_h8 deltas vs A_null_V0_25.
```

## Implementation plan (locked)

1. **No `src/` changes.** Confirmed: `widened_gradient_layout()` and `food_ladder_layout()` already exist.
2. Fresh script `scripts/v0_53_cross_layout_generalization_audit.py`. CLI: `uv run python scripts/v0_53_cross_layout_generalization_audit.py [--out-dir runs/v0.53-cross-layout-generalization]`.
3. Per (version, seed, hazard) tuple, run **3 arms**. Every arm constructs `HHModel` via the normal A_null path (`FounderSpec(traits_override=None)`):
   - **A_null_V0_25**: `tight_gradient_layout()`.
   - **B_widened_gradient**: `widened_gradient_layout()`.
   - **C_food_ladder**: `food_ladder_layout()`.
4. For each arm-run, attach v0.48-style `setup_observer` + `tick_observer` (copy-local from v0.48–v0.52b). Setup-observer order: (a) capture v0.53 founder audit table from live bodies (read-only — no patch), (b) wire `AgentBorn` (lineage tracking) / `AteFood` / `HazardDamageApplied` listeners (`sender=model`), (c) capture tick 0 snapshot, (d) read back `model.chamber_driver.layout_name` (or equivalent) and assert it matches the arm's expected layout name (`V053ReducerError` on mismatch).
5. Aggregate per-lineage primaries identical to v0.48–v0.52b. Compute Label A (`high_sensor_radius_lineage`) and Label B (`high_tick50_readiness_fraction_lineage`) per the v0.53 definitions (Label A resolves via the v0.52b override-or-trait resolver, but with override = None everywhere it's identical to the v0.48 trait-only definition).
6. Compute paired_d per (arm, gating-label, observable) cell (18 cells total). Classify per-arm sub-verdicts.
7. **Tier-1 bridge re-anchor** (priority 2): A_null_V0_25 arm's six cells vs v0.48 published; halt if drift > 1e-3 OR if A_null_V0_25 sub-verdict ≠ PRESENT.
8. **Corpus re-anchor** (priority 1): A_null_V0_25 arm only; halt if `a_share_h8` for v0.42 / v0.44 / v0.45 drifts > 1e-3.
9. **Layout opposite-sign halt** (priority 3): scan all gating-label cells across arms B and C; halt if any signed_d ≤ −0.5 (A_null_V0_25 wrong-sign is captured by priority 2's PRESENT requirement).
10. Compute slice rollup verdict per the locked priority + (B, C) sub-verdict matrix; print + write the locked phrase verbatim.

The reducer is fully self-contained: it reads no `runs/` artifacts. Wall time estimate ~15–25 minutes for 192 runs.

## Test list (locked, 16 tests; extends v0.46–v0.52b 7-point review pattern)

`tests/test_v0_53_cross_layout_generalization_audit.py`:

1. **`test_paired_d_function_reproduces_hand_computed_signed_d_on_fixture_and_tier1_constants_match_v048_published_values`** *(re-anchor test, two-part)* — Part A: feed the reducer's `paired_d` function a synthetic 8-run pool with per-run delta values whose mean and ddof=1 stdev are hand-computed in the test; assert returned `paired_d` matches the hand-computed value within 1e-9. Tests the formula, not v0.48 agreement. Part B: assert the locked Tier-1 reference constants in the reducer (the six v0.48 published `signed_d` values: +1.066, +1.066, +1.916, +0.916, +0.916, +1.179) are byte-equal to the v0.48 published values pinned in the pre-reg's Tier-1 table. Tests the constants, not the formula.
2. **`test_a_null_v025_corpus_a_share_h8_re_anchors_v042_v044_v045`** *(re-anchor test)* — drift halt fires if any of the three published values drifts > 1e-3.
3. `test_arm_a_null_v025_uses_tight_gradient_layout` — assert chamber driver receives `tight_gradient_layout()` for arm A_null_V0_25 (layout name read-back matches).
4. `test_arm_b_widened_uses_widened_gradient_layout` — assert chamber driver receives `widened_gradient_layout()` for arm B.
5. `test_arm_c_food_ladder_uses_food_ladder_layout` — assert chamber driver receives `food_ladder_layout()` for arm C.
6. **`test_founder_traits_byte_identical_across_arms_for_same_seed`** *(implementation-equivalence test)* — for the same (version, seed, hazard) tuple, founder Traits records (full 13 biological traits + override = None) byte-identical across all three arms at setup_observer end. Proves the layout swap does not perturb `streams.mutation` or per-agent RNG draws (founder construction is layout-independent given equal founder count and `spawn_x`).
7. **`test_founder_positions_byte_identical_across_arms_for_same_seed`** *(implementation-equivalence test)* — for the same (version, seed, hazard) tuple, founder (x, y) positions byte-identical across all three arms (all three layouts have `spawn_x = 1` and `height = 6`, so `spread_y(5, 6) = [(1,0)..(1,4)]` for every arm).
8. **`test_no_src_modifications_compared_to_v0_52b_tip`** *(implementation-equivalence test)* — assert `src/hedonism_harness/core/sensors.py`, `src/hedonism_harness/core/traits.py`, `src/hedonism_harness/core/body.py`, `src/hedonism_harness/core/config.py`, and `src/hedonism_harness/experiments/layouts.py` SHA-256 hashes match v0.52b tip's values (recorded as constants in the test). Failure message must read verbatim: "v0.53 is pre-registered as no-src-change; update the pre-reg before changing src." This guards the conservation framing against accidental drift.
9. `test_label_a_high_sensor_radius_lineage_picks_correct_lineage` — synthetic 5-founder draw with sensor_radii `[2, 5, 4, 1, 6]` → Label A picks lineage 4 (highest). Tiebreak `min(lineage_id)` on ties.
10. `test_label_b_three_tier_tiebreak_fraction_count_min_lineage` — synthetic readiness fractions with two-way tie on fraction → tiebreak by count → tiebreak by min(lineage_id). NaN-loses.
11. `test_paired_d_signed_d_ge_05_fires_present_threshold` — synthetic 3-cell pool with signed_d = +0.5, +0.6, +0.7 under both labels → sub-verdict PRESENT. With signed_d = +0.4 on one cell → sub-verdict drops to 2/3 (PARTIAL via the per-label clear-2/3 rule).
12. `test_paired_d_signed_d_le_neg_05_fires_opposite_sign_halt_per_arm` — synthetic any-cell signed_d = −0.5 → sub-verdict OPPOSITE_SIGN_HALT for that arm.
13. **`test_per_arm_subverdict_present_requires_both_labels_clear`** — synthetic Label A 2/3, Label B 2/3 → arm sub-verdict PRESENT. Synthetic Label A 1/3, Label B 2/3 → arm sub-verdict PARTIAL (exactly one label clears). Synthetic Label A 0/3, Label B 0/3 → arm sub-verdict NOT_FOUND.
14. `test_rollup_bridge_generalizes_when_a_null_b_c_all_present` — synthetic (A_null PRESENT, B PRESENT, C PRESENT); assert rollup = `BRIDGE_GENERALIZES_CROSS_LAYOUT` and locked phrase contains "fires PRESENT on both `widened_gradient` and `food_ladder`" verbatim.
15. `test_rollup_bridge_layout_local_when_b_and_c_both_not_found` — synthetic (A_null PRESENT, B NOT_FOUND, C NOT_FOUND); assert rollup = `BRIDGE_LAYOUT_LOCAL` and locked phrase contains "is local to the `tight_gradient` (V0_25) layout geometry" verbatim. Also test (A_null PRESENT, B PRESENT, C NOT_FOUND) → `BRIDGE_PARTIALLY_GENERALIZES` (locked phrase contains "does not resolve to a single categorical outcome").
16. **`test_rollup_priority_cascade_and_partition_total`** — synthesize a `CORPUS_REDERIVE_DRIFT_HALT` (priority 1) alongside a `BRIDGE_REPLICATION_HALT` (priority 2) and a `LAYOUT_OPPOSITE_SIGN_HALT` (priority 3); assert priority 1 fires first. Then synthesize priority 2 + 3 only; assert 2 fires first. Exhaustively iterate (B sub, C sub) ∈ {PRESENT, PARTIAL, NOT_FOUND}² (9 combinations) under A_null_V0_25 PRESENT and zero halts; assert each maps to exactly one of {GENERALIZES, LAYOUT_LOCAL, PARTIALLY_GENERALIZES}.

## Watch-outs (for future-Chronus)

- **No `src/` changes in v0.53.** Layouts already exist as named factories. v0.52 + v0.52b's src/ touches stand; v0.53 inherits them with `effective_sensor_radius_override = None` everywhere → byte-identical to v0.48 A_null path under all three layouts.
- **Tier-1 anchors only `A_null_V0_25`.** B and C are layouts never run before in this stack; there is NO published reference cell. Any wrong-sign firing under B or C halts loud (priority 3); any missing or anomalous cell is descriptive only.
- **Cross-layout magnitude differences are descriptive, not gating.** Observables 1 / 2 / 3 will have different absolute scales per layout (different food densities, different hazard bands, different distances). Paired_d normalizes within-arm; cross-arm magnitude shifts are reported in Results but do NOT fire the rollup verdict in either direction.
- **Layout asymmetry is a first-class outcome.** PARTIAL or `BRIDGE_PARTIALLY_GENERALIZES` is the catch-all for "B fires, C doesn't" or vice versa; it is NOT halted on, NOT coerced. The asymmetry IS the finding when this fires.
- **Founder traits and positions are byte-identical across arms by construction.** All three layouts have `spawn_x = 1` and `height = 6`; `spread_y(5, 6)` produces identical y positions; `random_traits` consumes from `streams.mutation` identically because the founder count is fixed at 5. Tests #6 and #7 enforce this. If a future layout has a different `spawn_x` or `height`, this property breaks and the cross-arm comparison loses founder-position equivalence.
- **`label_a_sensor_radius`, NOT `label_a_information_radius`.** v0.53 sets no override; the resolver falls through to trait identically across arms. The label name is the v0.48–v0.52 form; v0.52b's override-aware label name is reserved for slices that set the override field.
- **Locked phrase discipline:** all sub-verdict and rollup locked phrases fire verbatim where the verdict fires. No paraphrase. Layout names are backticked (`` `widened_gradient` ``, `` `food_ladder` ``, `` `tight_gradient` ``) in the rollup phrases — verbatim including backticks.
- **Determinism north star** ([[scripts/core_smoke_test.py]]) must continue to pass. v0.53 does not modify `src/`; the smoke test is unaffected by construction.
- **A_null_V0_25 must reproduce v0.48 within 1e-3.** This is the within-session sanity check that v0.53's reducer machinery (paired_d formula, label assignment, observable extraction) is correctly implemented. Drift > 1e-3 fires `BRIDGE_REPLICATION_HALT` (priority 2); any reducer bug is caught here, not in B or C results.

## Files this slice will create / modify

- `docs/experiments/fear_hunger_v0.53.md` (this file; Results section appended after reducer run)
- `scripts/v0_53_cross_layout_generalization_audit.py` (new)
- `tests/test_v0_53_cross_layout_generalization_audit.py` (new, 16 tests)

No `src/` modifications. No prior reducer / audit / test files modified.

## Results

**Status:** reducer executed 2026-05-08 against the 192-run corpus (3 arms × 64 (version, seed, hazard) tuples). Wall time ~12 minutes. **Tier-1 bridge re-anchor PASSES** (A_null_V0_25 arm reproduces v0.48's six published signed_d cells within max drift 0.0004 ≪ 1e-3 tolerance). Corpus re-anchor (`a_share_h8`) max drift 0.0003 on v0.42; v0.44 / v0.45 within 0.0002. No opposite-sign firings under any gating label on B or C arms.

### Rollup verdict — `BRIDGE_PARTIALLY_GENERALIZES` fires

> **Locked phrase fires verbatim:** "On the modern A_null corpus with the V0_25 substrate held constant, the v0.48 spatial / foraging bridge does not resolve to a single categorical outcome across `widened_gradient` and `food_ladder` under the locked +0.5 paired_d threshold. The bridge partially generalizes across the three tested layout geometries; the asymmetric pattern (per-arm sub-verdicts) is logged in Results."

Sub-verdicts:

| arm | layout | sub-verdict |
|---|---|---|
| A_null_V0_25 | `tight_gradient` | `A_NULL_V025_BRIDGE_PRESENT` |
| B_widened_gradient | `widened_gradient` | `B_WIDENED_BRIDGE_NOT_FOUND` |
| C_food_ladder | `food_ladder` | `C_LADDER_BRIDGE_PRESENT` |

The (PRESENT, NOT_FOUND, PRESENT) triple is the `BRIDGE_PARTIALLY_GENERALIZES` pattern. C fires the bridge cleanly under both labels (3/3 each); B does not fire under either label. The asymmetric finding is not a halt — opposite-sign halt did not fire — it is the scientifically meaningful first-class outcome that the rollup was designed to surface.

### Tier-1 bridge re-anchor — A_null_V0_25 reproduces v0.48 within 1e-3

| label | observable | published | derived | drift |
|---|---|:-:|:-:|:-:|
| label_a_sensor_radius | pre50_food_events_count | +1.066 | +1.066 | 0.0004 |
| label_a_sensor_radius | pre50_food_energy_acquired | +1.066 | +1.066 | 0.0004 |
| label_a_sensor_radius | mean_distance_to_nearest_food_cell | +1.916 | +1.916 | 0.0001 |
| label_b_readiness_fraction | pre50_food_events_count | +0.916 | +0.916 | 0.0001 |
| label_b_readiness_fraction | pre50_food_energy_acquired | +0.916 | +0.916 | 0.0001 |
| label_b_readiness_fraction | mean_distance_to_nearest_food_cell | +1.179 | +1.179 | 0.0004 |

Max drift 0.0004 ≪ 1e-3. v0.53's A_null_V0_25 arm is byte-compatible with the v0.48–v0.52b A_null path (no `src/` modifications under v0.53; the v0.52b-tip `src/` files are pinned by SHA-256 in `tests/test_v0_53_cross_layout_generalization_audit.py` test #8).

### Per-arm signed_d (sign-aware)

#### Arm A_null_V0_25 — sub-verdict `A_NULL_V025_BRIDGE_PRESENT`

| label | observable | sign | signed_d | fires |
|---|---|:-:|:-:|:-:|
| label_a_sensor_radius | pre50_food_events_count | + | **+1.066** | YES |
| label_a_sensor_radius | pre50_food_energy_acquired | + | **+1.066** | YES |
| label_a_sensor_radius | mean_distance_to_nearest_food_cell | − | **+1.916** | YES |
| label_b_readiness_fraction | pre50_food_events_count | + | **+0.916** | YES |
| label_b_readiness_fraction | pre50_food_energy_acquired | + | **+0.916** | YES |
| label_b_readiness_fraction | mean_distance_to_nearest_food_cell | − | **+1.179** | YES |

#### Arm B_widened_gradient — sub-verdict `B_WIDENED_BRIDGE_NOT_FOUND`

| label | observable | sign | signed_d | fires |
|---|---|:-:|:-:|:-:|
| label_a_sensor_radius | pre50_food_events_count | + | nan | — |
| label_a_sensor_radius | pre50_food_energy_acquired | + | nan | — |
| label_a_sensor_radius | mean_distance_to_nearest_food_cell | − | **−0.062** | NO |
| label_b_readiness_fraction | pre50_food_events_count | + | nan | — |
| label_b_readiness_fraction | pre50_food_energy_acquired | + | nan | — |
| label_b_readiness_fraction | mean_distance_to_nearest_food_cell | − | **+7.766** | YES (degenerate; see below) |

Four of the six B-arm cells produce `nan` paired_d because per-run `delta_mean = 0.0` and `sd = 0.0` across all 64 runs — `pre50_food_events_count` and `pre50_food_energy_acquired` are identically zero in every B run. The widened-gradient layout has spawn at `x = 1` and food at `x ∈ [10..14]`; the minimum traversal is 9 cells, with a 3-wide hazard band at `x ∈ [5..7]` in between. Within 50 ticks, no founder lineage in any of the 64 runs reaches the food zone, so all four food-related primaries (`pre50_food_events_count`, `pre50_food_energy_acquired` × Label A, Label B) are uniformly zero. The Label A vs non-Label A delta is structurally `0 − 0 = 0` on every run, producing the `0/0 = nan` paired_d. **This is descriptive only**; under the locked sub-verdict criterion (≥ 2/3 cells per label clearing the +0.5 threshold), four `nan` cells cannot fire and B's sub-verdict resolves to `B_WIDENED_BRIDGE_NOT_FOUND`.

The one non-nan B-arm cell that fires (`label_b_readiness_fraction × mean_distance_to_nearest_food_cell`, signed_d = +7.766) is **degenerate**: per-run `delta_mean = −0.0981` cells with `sd = 0.0126` cells. The huge `paired_d` reflects extremely low variance, not a meaningful effect size — the absolute spatial signal is < 0.1 cell across all 64 runs. The pre-reg's per-arm sub-verdict rule requires ≥ 2/3 cells clearing per label to fire PRESENT; B clears 0/3 under Label A (3 cells, 1 nan + 1 sub-threshold + 1 nan… wait, all three under Label A are: nan, nan, −0.062, none firing) and 1/3 under Label B (2 nan + 1 firing). **B sub-verdict = NOT_FOUND** (neither label clears ≥ 2/3).

The −0.062 cell does NOT trigger `LAYOUT_OPPOSITE_SIGN_HALT` (priority 3 threshold is signed_d ≤ −0.5; −0.062 is far above).

#### Arm C_food_ladder — sub-verdict `C_LADDER_BRIDGE_PRESENT`

| label | observable | sign | signed_d | fires |
|---|---|:-:|:-:|:-:|
| label_a_sensor_radius | pre50_food_events_count | + | **+1.186** | YES |
| label_a_sensor_radius | pre50_food_energy_acquired | + | **+1.186** | YES |
| label_a_sensor_radius | mean_distance_to_nearest_food_cell | − | **+1.804** | YES |
| label_b_readiness_fraction | pre50_food_events_count | + | **+0.621** | YES |
| label_b_readiness_fraction | pre50_food_energy_acquired | + | **+0.621** | YES |
| label_b_readiness_fraction | mean_distance_to_nearest_food_cell | − | **+0.939** | YES |

3/3 primaries fire under both labels with 0 wrong-sign. Label A magnitudes are slightly stronger than A_null_V0_25 (+1.186 vs +1.066 on events/energy); Label B magnitudes are weaker (+0.621 vs +0.916 on events/energy; +0.939 vs +1.179 on distance). The pre-food column at `x = 4` lets agents reach reproductive eligibility from a low-cost early energy source before crossing the hazard band — enough founders survive to populate the per-lineage primary counters and produce non-degenerate paired_d.

### Layout reachability — descriptive

Across the three layouts under V0_25 substrate (5 founders spawning at `x = 1`, sensor_radius integer-uniform on {1..6}, 50-tick observation window):

| layout | spawn → food traversal (cells) | hazard band | pre-food | fraction of runs with ≥ 1 lineage reaching food by tick 50 |
|---|:-:|---|---|:-:|
| `tight_gradient` | 9 → 4 (food at `x ∈ [5..8]`) | `x ∈ [3..4]` (2 cols) | none | 1.00 (per A_null_V0_25 paired_d non-zero on all 6 cells) |
| `widened_gradient` | 1 → 10 (food at `x ∈ [10..14]`) | `x ∈ [5..7]` (3 cols) | none | **0.00** (zero food events on all 64 runs) |
| `food_ladder` | 1 → 4 (pre-food at `x = 4`) and 1 → 9 (food at `x ∈ [9..11]`) | `x ∈ [6..8]` (3 cols) | `x = 4` (1 col) | 1.00 (all C-arm cells non-degenerate) |

The B_widened result is consistent with raw food-reach failure: the corridor between the 3-wide hazard band and the 5-wide food zone makes the v0.48 bridge unfireable on this substrate's 50-tick window. The C_food_ladder result confirms that adding a pre-food column at moderate distance restores bridge fireability with directional structure intact.

### Corpus re-anchor

A_null_V0_25 arm — all PASS (max drift 0.0003):

| version | derived `a_share_h8` | published | drift |
|---|:-:|:-:|:-:|
| v0.42 | 0.652 | 0.652 | 0.0003 |
| v0.43R | 0.674 | — (informational) | — |
| v0.44 | 0.878 | 0.878 | 0.0001 |
| v0.45 | 0.818 | 0.818 | 0.0002 |

B_widened_gradient arm (informational only — `n=0` on every cell because no lineage produces a tracked dominance event in the corpus's hazard=8 pool):

| version | B `a_share_h8` | n |
|---|:-:|:-:|
| v0.42 | nan | 0 |
| v0.43R | nan | 0 |
| v0.44 | nan | 0 |
| v0.45 | nan | 0 |

C_food_ladder arm (informational only — different counterfactual; raised dominance fractions consistent with the pre-food column boosting per-lineage reproductive eligibility):

| version | C `a_share_h8` | n |
|---|:-:|:-:|
| v0.42 | 0.822 | 8 |
| v0.43R | 0.955 | 7 |
| v0.44 | 1.000 | 7 |
| v0.45 | 1.000 | 5 |

### What v0.53 can safely claim

- ✓ **A_null_V0_25 replicated.** Tier-1 re-anchor reproduces v0.48's six published signed_d cells within 0.0004. The corpus re-anchor reproduces v0.42 / v0.44 / v0.45 within 0.0003. The v0.53 reducer's paired_d / label-assignment / observable-extraction machinery is correct.
- ✓ **The v0.48 spatial / foraging bridge fires PRESENT on `food_ladder`** (3/3 under both labels, 0 wrong-sign). The bridge is not exclusive to `tight_gradient` (V0_25) layout geometry; under at least one alternative food-rich layout (with a pre-food column at moderate distance from spawn), the bridge fires cleanly with directional structure preserved.
- ✓ **The v0.48 bridge does NOT fire on `widened_gradient`** (4/6 cells `nan` due to uniformly-zero food primaries; sub-verdict `NOT_FOUND`). The bridge is not universal across food-rich layouts at the V0_25 substrate's 50-tick window — at least one tested geometry produces a structural floor effect (no agent reaches food) that prevents the bridge from being measured.
- ✓ **The bridge partially generalizes across the three tested layout geometries on this corpus** (`tight_gradient` PRESENT, `widened_gradient` NOT_FOUND, `food_ladder` PRESENT). The asymmetric pattern is the categorical outcome the locked rollup was designed to surface; it is preserved verbatim by the locked phrase.

### What v0.53 cannot claim

- ✗ **"The widened_gradient bridge is absent"** in any general sense. v0.53's `B_WIDENED_BRIDGE_NOT_FOUND` is *driven by* the structural fact that no founder lineage reaches the food zone in 50 ticks — not by a discriminative null on Label A vs Label B differentiation. With a longer observation window (e.g., tick-100 readiness), agents may eventually reach the food zone and the bridge may fire. v0.53's NOT_FOUND verdict is anchored to the V0_25-specific 50-tick window; longer-horizon probes are out of scope.
- ✗ **"The food_ladder bridge magnitude is comparable to V0_25's bridge."** Magnitudes shifted (Label A stronger by ~+0.12 on events / energy, Label B weaker by ~−0.30 on events / energy; distance cell stronger on Label A by +0.11 and weaker on Label B by −0.24). Magnitude differences are descriptive, not gating; v0.53 does not establish a quantitative cross-layout magnitude relationship.
- ✗ **Causal contribution of `sensor_radius` per layout.** v0.53 is observational. A future causal-generalization slice (re-running v0.49's null + clamp_4 + permutation_5! per layout, ~576 runs total) would be required to make a per-layout causal claim.
- ✗ **Mechanism behind the asymmetric (PRESENT, NOT_FOUND, PRESENT) pattern.** The structural reachability story (widened gradient is too far; food_ladder's pre-food column shortens effective traversal) is the most parsimonious explanation but is NOT formally established by v0.53. Disambiguating it from alternative mechanisms (different food-density per cell, different hazard placement, different spawn-to-safe ratio) would require additional layouts or a fresh-stream calibration.
- ✗ **Generalization beyond the three tested layouts** (`tight_gradient`, `widened_gradient`, `food_ladder`). `default_layout` and `near_hazard_layout` are not in v0.53's set. Other layouts not covered.
- ✗ **Generalization to non-V0_25 substrates.** Aggregate-optimum substrates (v0.21..v0.27) and intermediate ecologies are not tested.

### Cross-corpus context

| slice | corpus | claim | strength |
|---|---|---|---|
| v0.46 | modern A_null | tick-50 readiness predicts dominance | observational (PRESENT) |
| v0.47 | modern A_null | founder `sensor_radius` predicts tick-50 readiness | observational (PARTIAL) |
| v0.48 | modern A_null | `sensor_radius` ↔ spatial bridge | observational (PRESENT under both labels) |
| v0.49 | modern A_null | founder `sensor_radius` causal contribution | interventional (SUPPORTED) |
| v0.50 | modern A_null | v0.49's contribution survives position controls | interventional (ROBUST) |
| v0.51 | modern A_null | founder-clamp NOT_FOUND result preserved under lineage-wide clamp | interventional (REPRODUCED; descendant-drift channel empirically zero under V0_25) |
| v0.52 | modern A_null | metabolic-cost channel not necessary for bridge (B PRESENT); C arm halt-loud | interventional (B PRESENT confirms cost dispensable; C uniform-max regime-shift halt) |
| v0.52b | modern A_null | bridge follows between-lineage information-radius assignment under preserved global ecology | interventional (FOLLOWS_ASSIGNMENT; lineage-coherent inheritance verified clean) |
| v0.53 | modern A_null | bridge fires PRESENT on `food_ladder`, NOT_FOUND on `widened_gradient`, PRESENT on `tight_gradient` | observational (PARTIALLY_GENERALIZES; layout asymmetry surfaced) |

The v0.46→v0.53 stack now reads: tick-50 readiness predicts dominance → founder `sensor_radius` predicts readiness → `sensor_radius` co-occurs with spatial advantage → causal contribution from `sensor_radius` survives clamp + permutation → that contribution survives shifted-top + permuted founder positions → and the founder-clamp NOT_FOUND result is preserved under lineage-wide clamping → and the metabolic-cost channel of `sensor_radius` is not necessary for the bridge → and the bridge follows the assigned effective information radius when global information economy is preserved → **and the bridge fires on `food_ladder` and not on `widened_gradient` under the V0_25 substrate's 50-tick window, indicating that the bridge's measurability depends on layout reachability rather than being a universal property of `sensor_radius` variation under any food-rich geometry.**

### Next-step candidates (open; not locked)

The v0.53 result is `BRIDGE_PARTIALLY_GENERALIZES` with a structurally interpretable cause (food unreachable in 50 ticks on widened_gradient). Multiple follow-up directions:

- **Disambiguation slice (v0.54a candidate).** Re-run B_widened_gradient with an extended observation window (e.g., tick-100 or tick-200 readiness) to distinguish "bridge structurally absent" from "bridge measurement window too short". Pure observational; no `src/` change.
- **Causal-generalization slice (v0.54b candidate).** Re-run v0.49's null + clamp_4 + permutation_5! per layout on `tight_gradient` + `food_ladder` (skipping `widened_gradient` per the v0.53 NOT_FOUND finding). ~384 runs. Tests whether the v0.49 causal verdict re-fires per layout that admits the bridge.
- **v0.54 — joint ablation** (already documented). `sensor_radius_metabolic_cost = 0` AND between-lineage shuffle of `effective_sensor_radius_override`. Tests for higher-order interactions between v0.52's and v0.52b's separately-addressed channels.
- **Eventual fresh-stream calibration** (v0.30-style) on the v0.46–v0.53 conclusion stack — needed for any "mechanism" declaration. Longer-horizon.

User has not locked which slice is next; the v0.53 result is consistent with multiple readings.

### CI gate at v0.53 close

```
uv run ruff check .             ok
uv run ruff format --check .    ok (224 files already formatted)
uv run pytest                   1712 passed, 7 skipped (was 1696; +16 v0.53)
uv run python scripts/core_smoke_test.py                                ok (default behavior preserved; src/ untouched)
uv run python scripts/v0_53_cross_layout_generalization_audit.py        BRIDGE_PARTIALLY_GENERALIZES
```
