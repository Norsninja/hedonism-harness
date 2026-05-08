# fear_hunger v0.53b — reachability disambiguation (window extension to tick-100)

**Slice:** v0.53b
**Type:** **first-class observational sweep** with 3-arm tick-100 reducer (no `src/` changes; no intervention; reuses existing named layouts in `src/hedonism_harness/experiments/layouts.py`).
**Predecessors:** v0.46–v0.52b (full predecessor stack), v0.53 (`BRIDGE_PARTIALLY_GENERALIZES` — A_null_V0_25 PRESENT, B_widened_gradient NOT_FOUND with reachability-censored evidence stack, C_food_ladder PRESENT).
**Question being asked (locked):** Does extending the observation window from tick-50 to tick-100 reveal whether v0.53's `B_WIDENED_BRIDGE_NOT_FOUND` is reachability-censored (B's pre-window food primaries fire under longer window, sub-verdict resolves PRESENT) or structurally absent (B's pre-window food primaries remain near-zero even under longer window, OR sub-verdict remains NOT_FOUND despite measurable food access)?

v0.53 closed the cross-layout generalization frame with a `BRIDGE_PARTIALLY_GENERALIZES` verdict driven by an asymmetric (PRESENT, NOT_FOUND, PRESENT) sub-verdict triple. The B_widened_gradient NOT_FOUND was structurally driven: 4 of 6 paired_d cells were `nan` because pre50_food_events_count and pre50_food_energy_acquired were uniformly zero across all 64 runs (the 9-cell traversal across a 3-wide hazard band is unreachable in 50 ticks). v0.53's locked Results explicitly flagged this: `"v0.53's NOT_FOUND verdict is anchored to the V0_25-specific 50-tick window; longer-horizon probes are out of scope."` — and listed reachability disambiguation as the v0.54a candidate.

v0.53b is that disambiguation. It re-runs the same 192-run corpus shape with the per-tick observer extended to tick-100 (still well within the 200-tick simulation length — no sim extension needed) and asks whether B_widened's bridge-measurability and / or bridge-firing changes under the longer window. The primary question is **about B_widened only**; A_null_V0_25 and C_food_ladder tick-100 paired_d cells are descriptive context for the Results section unless they fire `LAYOUT_OPPOSITE_SIGN_HALT`.

If B_widened fires PRESENT at tick-100 with non-trivial reachability, v0.53's NOT_FOUND was the 50-tick window's artifact and the bridge generalizes given longer measurement time. If B_widened still has near-zero reachability at tick-100, the layout is structurally unreachable on this substrate and the NOT_FOUND verdict is itself reachability-bound (no claim about bridge presence is possible). If B_widened has measurable reachability AND sub-verdict still ∈ {PARTIAL, NOT_FOUND}, the bridge fails to fire on this layout despite agents reaching food — a layout-specific failure that is NOT reducible to reachability censoring.

## Pre-implementation note (2026-05-08, before any reducer code)

The pre-reg's design was confirmed with the user before drafting:

- **3 arms (symmetric).** Same as v0.53: `A_null_V0_25` (`tight_gradient`), `B_widened_gradient`, `C_food_ladder`. Re-anchor symmetry preserved.
- **Same 64 (version, seed, hazard) tuples × 3 arms = 192 runs.** Same V0_25 substrate. RNG / founder draw / position byte-identity invariants preserved.
- **Tick-100 observation window.** Per-tick observer collects through tick-100 (extended from v0.53's tick-50). 200-tick simulation length unchanged. No `src/` modification.
- **Label B generalized to `high_tick100_readiness_fraction_lineage`.** Label A unchanged (`high_sensor_radius_lineage`, trait-resolved).
- **Primary decision is B_widened_gradient only.** The rollup gates on B's reachability + B's sub-verdict; A_null_V0_25 and C_food_ladder are descriptive at tick-100 unless they fire opposite-sign halts.
- **Tier-1 re-anchor against tick-50 cells preserved.** A_null_V0_25 must still re-derive v0.48 / v0.53's six published tick-50 signed_d values within 1e-3 — this is the within-session sanity check that v0.53b's reducer machinery (paired_d formula, label assignment, observable extraction at tick-50) reproduces v0.53 byte-equivalently. v0.53b's tick-100 cells have NO published reference; validity rests on the tick-50 anchor + the implementation-equivalence tests.
- **No `src/` modifications.** v0.53b inherits the v0.52b-tip src/ (= v0.53-tip src/, since v0.53 made no src/ changes). SHA-256-pinned in tests.

## Conservation framing — observational, no `src/`, no intervention

- **No `src/` modifications.** v0.53b inherits v0.53's src/ state, which inherits v0.52b's. The window extension is script-local: the per-tick observer wires through tick-100 instead of tick-50.
- **No modifications to prior reducer or audit scripts.** v0.34's `lineage_replay.py`, v0.35's `lineage_survival_replay.py`, v0.36's `trait_replay.py`, the four substrate audits, and v0.46–v0.53's reducers remain byte-identical to their merged forms.
- **A_null_V0_25 arm is byte-identical to v0.48–v0.53 A_null path AT TICK-50.** Same `tight_gradient` layout, same V0_25 substrate, same `FounderSpec(traits_override=None)`, same RNG streams. Tier-1 re-anchor enforces this at metric level on the six tick-50 cells.
- **B_widened_gradient and C_food_ladder arms are byte-identical to v0.53's B and C arms AT EVERY TICK 0..200.** Same `streams.mutation`, same founder draws, same per-agent RNGs, same world layouts. The only difference between v0.53 and v0.53b is the *observation window*: v0.53 captures pre50 primaries; v0.53b captures pre100 primaries (and pre50 cells for the v0.53 re-anchor).
- **No intervention at any level.** No founder body trait modification, no `effective_sensor_radius_override`, no helper RNG, no shuffle, no clamp, no permutation. Pure observational extension.
- **Single observation-window-channel variation.** v0.53b differs from v0.53 only in the per-tick observer's accumulation through tick-100 vs tick-50. The simulation engine, world initialization, agent construction, and per-tick dynamics are byte-identical to v0.53 across all three arms.

## Corpus (locked, 64 × 3 arms = 192 runs)

| version | seeds | hazards | runs per arm | total runs |
|---|---|---|---|---|
| v0.42 | 41..48 | {0, 8} | 16 | 48 |
| v0.43R | 49..56 | {0, 8} | 16 | 48 |
| v0.44 | 57..64 | {0, 8} | 16 | 48 |
| v0.45 | 65..72 | {0, 8} | 16 | 48 |
| **total** | | | | **192** |

V0_25 substrate identical to v0.53. Each (version, seed, hazard) tuple is run **3 times** — once per arm (= once per layout). Per-arm seed bands identical to v0.53; arm differs only in the `ChamberLayout` factory selected. Wall time estimate ~16–28 minutes total at ~5–9 s per run (slightly longer than v0.53 due to 50 extra observation ticks per run; the simulation itself runs the full 200 ticks in both slices).

## Arms (locked, 3 — same layout selection as v0.53)

### A_null_V0_25

```
ChamberLayout = tight_gradient_layout()
FounderSpec(traits_override=None)
no patch, no body_config override, no per-agent override
```

Byte-identical to v0.48–v0.53 A_null path at every tick 0..200. Used for two purposes:
1. **Tier-1 anchor at tick-50** (against v0.48 / v0.53 published cells) — the within-session sanity check.
2. **Descriptive context at tick-100** (no published anchor; magnitude shifts are reported in Results but do not gate the verdict).

### B_widened_gradient

```
ChamberLayout = widened_gradient_layout()
FounderSpec(traits_override=None)
no patch, no body_config override, no per-agent override
```

Byte-identical to v0.53's B_widened_gradient arm at every tick 0..200. The **primary arm** of v0.53b: the verdict is gated on B's tick-100 reachability and tick-100 sub-verdict.

### C_food_ladder

```
ChamberLayout = food_ladder_layout()
FounderSpec(traits_override=None)
no patch, no body_config override, no per-agent override
```

Byte-identical to v0.53's C_food_ladder arm at every tick 0..200. **Descriptive context at tick-100** (no published anchor; halt-loud only on opposite-sign).

## Labels (locked, two)

### Label A — `high_sensor_radius_lineage`

Identical to v0.48–v0.53. Trait-resolved (`int(founder.body.traits.sensor_radius)`); tiebreak `min(lineage_id)`.

### Label B — `high_tick100_readiness_fraction_lineage`

**Generalized from v0.47–v0.53's `high_tick50_readiness_fraction_lineage`.** Per-lineage fraction of tick-100 living agents whose energy ≥ `reproduction.energy_threshold` AND age ≥ `reproduction.min_age` (same definition as v0.47, snapshot at tick-100 instead of tick-50). 3-tier tiebreak: fraction → count → min(lineage_id), NaN-loses (same as v0.47).

## Primary observables (locked, 3, generalized from v0.48–v0.53 to tick-100)

| # | name | expected sign |
|---|---|:-:|
| 1 | `pre100_food_events_count` | + |
| 2 | `pre100_food_energy_acquired` | + |
| 3 | `mean_distance_to_nearest_food_cell` | − |

Definitions, aggregation rules, NaN handling: copy-local from v0.48–v0.53, with the accumulation window extended from `tick ∈ [0, 50]` to `tick ∈ [0, 100]` for primaries 1 and 2. Primary 3 is a snapshot of mean distance from the lineage's living agents to the nearest food cell, captured at tick-100 (replaces v0.53's tick-50 snapshot).

**Tick-50 cells are also computed** (over the same `pre50` window as v0.48–v0.53) for the Tier-1 anchor. The reducer captures both tick-50 and tick-100 primaries from the same 192 sim runs; the per-tick observer accumulates events through tick-100 and emits both `pre50_*` and `pre100_*` rollups per agent.

## Effect-size rule (locked, sign-aware, identical to v0.48–v0.53)

```
per_run_delta_O = label_lineage_value_O − mean(non_label_lineage_values_O)
paired_d_O      = mean(per_run_delta_O) / stdev(per_run_delta_O, ddof=1)
signed_d_O      = paired_d_O × expected_sign
fires_expected  iff signed_d_O ≥ +0.5
fires_wrong     iff signed_d_O ≤ −0.5
```

## B_widened reachability metric (locked, pre-data)

```
b_reachability_run_share_tick_100 =
    fraction of B_widened runs where at least one founder lineage has
    pre100_food_events_count > 0
```

Domain: 64 runs (B_widened arm only, all four versions × two hazards × eight seeds, hazard ∈ {0, 8}, seeds 41..72). The metric is a fraction in [0, 1]. Locked threshold for the rollup: **`B_REACHABILITY_THRESHOLD = 0.25`** (≥ 25% of B-arm runs have ≥ 1 founder lineage with non-zero pre100 food events). Pre-committed pre-data; rationale: 25% is a conservative floor that excludes "uniformly zero or near-zero" reachability while admitting cases where a meaningful fraction (but not the full corpus) of runs achieves food access by tick-100. If reachability is ≥ 25%, paired_d cells are guaranteed to have non-degenerate variance under at least some seeds; if reachability is < 25%, the structurally-unreachable verdict is locked.

## Per-arm sub-verdicts (locked, 4-way each)

Identical structure to v0.53; **only sub-verdict labels rename to tick-100 tier**:

| condition | A_null_V0_25 (tick-100) | B_widened_gradient (tick-100) | C_food_ladder (tick-100) |
|---|---|---|---|
| both labels clear ≥ 2/3, 0 wrong-sign | `A_NULL_V025_TICK100_BRIDGE_PRESENT` | `B_WIDENED_TICK100_BRIDGE_PRESENT` | `C_LADDER_TICK100_BRIDGE_PRESENT` |
| exactly one label clears ≥ 2/3, 0 wrong-sign | `A_NULL_V025_TICK100_BRIDGE_PARTIAL` | `B_WIDENED_TICK100_BRIDGE_PARTIAL` | `C_LADDER_TICK100_BRIDGE_PARTIAL` |
| neither label clears ≥ 2/3, 0 wrong-sign | `A_NULL_V025_TICK100_BRIDGE_NOT_FOUND` | `B_WIDENED_TICK100_BRIDGE_NOT_FOUND` | `C_LADDER_TICK100_BRIDGE_NOT_FOUND` |
| any primary signed_d ≤ −0.5 under either label | `A_NULL_V025_TICK100_OPPOSITE_SIGN_HALT` | `B_WIDENED_TICK100_OPPOSITE_SIGN_HALT` | `C_LADDER_TICK100_OPPOSITE_SIGN_HALT` |

Each arm's tick-100 paired_d cells (3 observables × 2 labels = 6 cells per arm; 18 cells total across the three arms) are computed independently from the arm's 64-run pool.

## Slice rollup verdicts (locked, 6 outcomes, priority-ordered)

Priority order (first-matching wins). The non-halt outcomes (priorities 4–6) gate **only on B_widened**; A_null_V0_25 and C_food_ladder tick-100 sub-verdicts are descriptive in Results unless they fire opposite-sign (priority 3).

1. `CORPUS_REDERIVE_DRIFT_HALT`
2. `BRIDGE_REPLICATION_HALT` (Tier-1 A_null_V0_25 tick-50 vs v0.48 / v0.53)
3. `LAYOUT_OPPOSITE_SIGN_HALT` (any non-V0_25 arm wrong-sign at tick-100)
4. `WIDENED_REACHABILITY_CENSORED_RESOLVED` (B reachability ≥ 25% AND B tick-100 sub-verdict = PRESENT)
5. `WIDENED_REACHABILITY_RESOLVED_BRIDGE_NOT_FOUND` (B reachability ≥ 25% AND B tick-100 sub-verdict ∈ {PARTIAL, NOT_FOUND})
6. `WIDENED_STRUCTURALLY_UNREACHABLE_AT_TICK_100` (B reachability < 25%)

### Halt conditions

| priority | rollup verdict | trigger | locked phrase (verbatim) |
|---|---|---|---|
| 1 | `CORPUS_REDERIVE_DRIFT_HALT` | A_null_V0_25 arm `a_share_h8` for any of v0.42 / v0.44 / v0.45 drifts > 1e-3 from the published reference | "Halt: A_null_V0_25 re-anchor drifted from the published Results value for {version}; v0.53b's deterministic re-execution of the V0_25 corpus does not reproduce the published metric within 1e-3." |
| 2 | `BRIDGE_REPLICATION_HALT` | (a) A_null_V0_25 tick-50 signed_d for any of the six v0.48 / v0.53 cells drifts > 1e-3 from the published value, OR (b) A_null_V0_25 tick-50 sub-verdict ≠ PRESENT | "Halt: v0.53b's A_null_V0_25 arm does not reproduce v0.48 / v0.53's tick-50 spatial bridge — either a paired_d cell drifts beyond 1e-3 of the published value, or the tick-50 sub-verdict does not resolve to PRESENT. v0.53b cannot interpret the tick-100 cells without an established baseline." |
| 3 | `LAYOUT_OPPOSITE_SIGN_HALT` | any tick-100 gating-label primary signed_d ≤ −0.5 under arm A_null_V0_25, B, or C | "Halt: a v0.53b tick-100 spatial / foraging primary fires in the WRONG direction under a gating label; the window extension surfaces an intervention-incompatible regime that the locked expected signs do not anticipate." |

### Tier-1 (priority 2) re-anchor — A_null_V0_25 tick-50 cells

Identical six cells to v0.53 (which were identical to v0.48):

| label | observable | sign | published signed_d (v0.48 = v0.53) |
|---|---|:-:|:-:|
| `label_a_sensor_radius` | `pre50_food_events_count` | + | **+1.066** |
| `label_a_sensor_radius` | `pre50_food_energy_acquired` | + | **+1.066** |
| `label_a_sensor_radius` | `mean_distance_to_nearest_food_cell` | − | **+1.916** |
| `label_b_readiness_fraction_tick50` | `pre50_food_events_count` | + | **+0.916** |
| `label_b_readiness_fraction_tick50` | `pre50_food_energy_acquired` | + | **+0.916** |
| `label_b_readiness_fraction_tick50` | `mean_distance_to_nearest_food_cell` | − | **+1.179** |

Drift tolerance = 1e-3. Same protocol as v0.49–v0.53. `label_b_readiness_fraction_tick50` is the v0.47–v0.53 form (high_tick50_readiness_fraction_lineage); v0.53b's primary Label B at tick-100 (`high_tick100_readiness_fraction_lineage`) is a separate label whose cells have NO published reference.

**No Tier-2 re-anchor.** B_widened and C_food_ladder tick-100 cells are novel; validity rests on Tier-1 (tick-50) + corpus re-anchor + implementation-equivalence tests.

### Outcome conditions (only consulted if no halt fires)

| priority | rollup verdict | trigger | locked phrase (verbatim) |
|---|---|---|---|
| 4 | `WIDENED_REACHABILITY_CENSORED_RESOLVED` | B_widened reachability ≥ 25% AND B_widened tick-100 sub-verdict = `B_WIDENED_TICK100_BRIDGE_PRESENT` | "On the modern A_null corpus with the V0_25 substrate held constant and the observation window extended from tick-50 to tick-100, the v0.48 spatial / foraging bridge fires PRESENT on `widened_gradient` under the locked +0.5 paired_d threshold. v0.53's `B_WIDENED_BRIDGE_NOT_FOUND` was reachability-censored by the 50-tick window; the bridge is measurable on `widened_gradient` given longer observation time." |
| 5 | `WIDENED_REACHABILITY_RESOLVED_BRIDGE_NOT_FOUND` | B_widened reachability ≥ 25% AND B_widened tick-100 sub-verdict ∈ {`B_WIDENED_TICK100_BRIDGE_PARTIAL`, `B_WIDENED_TICK100_BRIDGE_NOT_FOUND`} | "On the modern A_null corpus with the V0_25 substrate held constant and the observation window extended from tick-50 to tick-100, the v0.48 spatial / foraging bridge does NOT fire PRESENT on `widened_gradient` despite measurable reachability (≥ 25% of runs producing pre100 food access). The NOT_FOUND outcome is not reducible to reachability censoring on this layout; the bridge fails to fire under longer observation even when food primaries become measurable. Layout-specific failure logged in Results." |
| 6 | `WIDENED_STRUCTURALLY_UNREACHABLE_AT_TICK_100` | B_widened reachability < 25% | "On the modern A_null corpus with the V0_25 substrate held constant and the observation window extended from tick-50 to tick-100, fewer than 25% of `widened_gradient` runs have any founder lineage with pre100 food events. The bridge cannot be measured on `widened_gradient` at this window length on this substrate; the layout is structurally unreachable at tick-100. v0.53's `B_WIDENED_BRIDGE_NOT_FOUND` is itself reachability-bound and no claim about bridge presence is established by v0.53b." |

The rollup is **categorical-only** — magnitude differences in A_null_V0_25 / C_food_ladder tick-100 cells are reported descriptively in Results but do not alter the verdict. PARTIAL on B_widened is folded into priority 5 (since the locked question is "does the bridge fire"; PARTIAL ≠ PRESENT is the relevant distinction). PARTIAL on A_null_V0_25 / C_food_ladder is descriptive only (does NOT halt or fire any outcome).

The 3 non-halt outcomes form a total partition of (B reachability ≥ 0.25, B sub-verdict ∈ {PRESENT, PARTIAL, NOT_FOUND}) ∪ (B reachability < 0.25). Halts cover the OPPOSITE_SIGN, drift, and replication cases. Test #16 enforces the partition exhaustively.

## Cautious framing (per CLAUDE.md)

- "**Reachability-censored**", "**reachability-bound**", "**structurally unreachable at tick-100**", "**measurable on this layout given longer observation time**" — NOT "**proves**", "**causes**", or "**rules out**".
- "**On the modern A_null corpus with the V0_25 substrate held constant and the observation window extended from tick-50 to tick-100**" — NOT a substrate-independent claim, NOT a window-independent claim.
- "**Layout-specific failure**" (priority 5) specifically refers to: B reachability ≥ 25% AND B tick-100 sub-verdict ∈ {PARTIAL, NOT_FOUND}. It is a categorical observation that the bridge does not fire on `widened_gradient` even when food primaries become measurable; it does NOT establish a mechanism for that failure (different food density per cell, different hazard placement, longer effective traversal, etc.).
- v0.53b explicitly does not establish: cross-layout generalization to layouts not in the {`tight_gradient`, `widened_gradient`, `food_ladder`} set, mechanism for any layout-specific outcome, generalization to non-V0_25 substrates, behavior at tick-150 / tick-200 / longer windows, causal contribution per layout (Reading-A causal-generalization slice remains the deferred candidate).

## What v0.53b cannot establish (logged here pre-data, not retrofittable)

- ✗ **"The bridge is universally absent on `widened_gradient`"** if priority 5 fires. v0.53b tests tick-100 only; longer windows (tick-150 / tick-200) may resolve the bridge; mechanism is not isolated.
- ✗ **"The bridge IS load-bearing on `widened_gradient`"** if priority 4 fires. The observation reveals the bridge is measurable under longer windows; it does not establish the channel-level question (causal contribution, mechanism, etc.) — that is the deferred Reading-A causal-generalization slice's job.
- ✗ **A revised v0.53 verdict.** v0.53's `BRIDGE_PARTIALLY_GENERALIZES` stands as the historical contract for the tick-50 window. v0.53b is a *follow-up disambiguation*, not a re-litigation.
- ✗ **Generalization to other layouts or substrates.** As locked.
- ✗ **Mechanism behind any bridge-firing or not-firing outcome.**

## Open framing (NOT in v0.53b primary)

- **v0.54 — joint ablation** (`sensor_radius_metabolic_cost = 0` AND between-lineage shuffle of `effective_sensor_radius_override`). Tests for higher-order interactions between v0.52 / v0.52b channels. Independent of v0.53b's outcome.
- **Reading-A causal-generalization slice** (re-run v0.49's null + clamp_4 + permutation_5! per layout). Triggered if v0.53b fires priority 4 (RESOLVED) on `widened_gradient` AND the user wants per-layout causal claims.
- **Eventual fresh-stream calibration** (v0.30-style) on the v0.46–v0.53b conclusion stack — needed for any "mechanism" declaration. Longer-horizon.

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
runs/v0.53b-reachability-disambiguation/per_run_per_lineage_v053b.csv
  columns: arm, layout_name, version, seed, hazard, run_id, lineage_id,
           founder_sensor_radius, founder_reproduction_drive, founder_metabolic_rate,
           pre50_food_events_count, pre50_food_energy_acquired,
           pre100_food_events_count, pre100_food_energy_acquired,
           mean_distance_to_nearest_food_cell_tick50,
           mean_distance_to_nearest_food_cell_tick100,
           tick50_living_count, tick50_above_threshold_count, tick50_above_threshold_fraction,
           tick100_living_count, tick100_above_threshold_count, tick100_above_threshold_fraction,
           b50_count, is_eventual_top_b50_label,
           is_high_sensor_radius_lineage,
           is_high_tick50_readiness_fraction_lineage,
           is_high_tick100_readiness_fraction_lineage

runs/v0.53b-reachability-disambiguation/audit_summary.csv
  columns: section, key, value
  sections:
    - reanchor_a_share_h8: per (arm, version, h=8) derived + (A_null_V0_25 only) published + drift_abs
    - bridge_reanchor_tick50: per (label, observable) v0.48 published signed_d + v0.53b A_null_V0_25 derived + drift_abs (against v0.48 / v0.53 published cells)
    - paired_d_tick50: per (arm, gating-label, observable) tick-50 cell — paired_d, signed_d, n_runs, fires_expected, fires_wrong (descriptive — not gating beyond the Tier-1 anchor)
    - paired_d_tick100: per (arm, gating-label, observable) tick-100 cell — paired_d, signed_d, n_runs, fires_expected, fires_wrong (B_widened gates the rollup; A_null_V0_25 / C_food_ladder are descriptive)
    - b_reachability: B_widened reachability_run_share_tick_100 (single value); B_widened pre100 food events distribution per version × hazard
    - sub_verdicts_tick100: per arm — sub-verdict + locked sub-phrase
    - rollup_verdict: locked rollup verdict + locked rollup phrase

runs/v0.53b-reachability-disambiguation/audit_log.txt
  human-readable echo with all locked phrases printed verbatim where they fire,
  plus per-arm tick-50 + tick-100 paired_d tables and B_widened reachability table.
```

## Implementation plan (locked)

1. **No `src/` changes.** Confirmed.
2. Fresh script `scripts/v0_53b_reachability_disambiguation_audit.py`. CLI: `uv run python scripts/v0_53b_reachability_disambiguation_audit.py [--out-dir runs/v0.53b-reachability-disambiguation]`.
3. Per (version, seed, hazard) tuple, run **3 arms** (same layout selection as v0.53). Every arm constructs `HHModel` via the normal A_null path; tick observer accumulates events through tick-100 (extended from v0.53's tick-50).
4. For each arm-run, attach v0.53-style `setup_observer` + `tick_observer` (copy-local from v0.53, with the tick-100 extension). Setup-observer order: (a) capture v0.53b founder audit table from live bodies (read-only — no patch), (b) wire `AgentBorn` (lineage tracking) / `AteFood` / `HazardDamageApplied` listeners (`sender=model`), (c) read back `model.world.width` and assert it matches the arm's expected layout's width (`V053bReducerError` on mismatch), (d) capture tick-0 snapshot. (Same order as v0.53's merged implementation; no commutative-pair note needed since v0.53b matches v0.53.)
5. Per-tick observer accumulates `pre50_*` and `pre100_*` rollups in parallel; both are emitted at end-of-run.
6. Aggregate per-lineage primaries identical to v0.48–v0.53 at tick-50, with new tick-100 counterparts. Compute Label A (`high_sensor_radius_lineage`), Label B at tick-50 (`high_tick50_readiness_fraction_lineage` — for the Tier-1 anchor), and Label B at tick-100 (`high_tick100_readiness_fraction_lineage` — for the v0.53b verdict).
7. Compute paired_d per (arm, gating-label, observable, window) cell. 18 tick-50 cells (anchor / descriptive) + 18 tick-100 cells (verdict). Classify per-arm tick-100 sub-verdicts.
8. Compute B_widened reachability_run_share_tick_100.
9. **Tier-1 bridge re-anchor** (priority 2): A_null_V0_25 arm's six tick-50 cells vs v0.48 / v0.53 published; halt if drift > 1e-3 OR if A_null_V0_25 tick-50 sub-verdict ≠ PRESENT.
10. **Corpus re-anchor** (priority 1): A_null_V0_25 arm only; halt if `a_share_h8` for v0.42 / v0.44 / v0.45 drifts > 1e-3.
11. **Layout opposite-sign halt** (priority 3): scan all tick-100 gating-label cells across all three arms; halt if any signed_d ≤ −0.5.
12. Compute slice rollup verdict per the locked priority + (B reachability, B sub-verdict) decision matrix; print + write the locked phrase verbatim.

The reducer is fully self-contained: it reads no `runs/` artifacts. Wall time estimate ~16–28 minutes for 192 runs.

## Test list (locked, 16 tests; extends v0.53's pattern)

`tests/test_v0_53b_reachability_disambiguation_audit.py`:

1. **`test_paired_d_function_reproduces_hand_computed_signed_d_on_fixture_and_tier1_constants_match_v048_published_values`** *(re-anchor test, two-part)* — Part A: feed `paired_d` a synthetic 8-run pool with hand-computed mean / ddof=1 stdev; assert returned value within 1e-9. Part B: assert the locked Tier-1 reference constants (six v0.48 / v0.53 published `signed_d`: +1.066, +1.066, +1.916, +0.916, +0.916, +1.179) are byte-equal to the pinned values.
2. **`test_a_null_v025_corpus_a_share_h8_re_anchors_v042_v044_v045`** *(re-anchor test)* — drift halt fires if any of the three published values drifts > 1e-3.
3. `test_arm_a_null_v025_uses_tight_gradient_layout` — chamber driver receives `tight_gradient_layout()`; layout invariant assert at setup_observer end.
4. `test_arm_b_widened_uses_widened_gradient_layout` — layout invariant assert at setup_observer end.
5. `test_arm_c_food_ladder_uses_food_ladder_layout` — layout invariant assert at setup_observer end.
6. **`test_founder_traits_byte_identical_across_arms_for_same_seed`** *(implementation-equivalence test)* — for the same (version, seed, hazard) tuple, founder Traits records (full 13 biological traits + override = None) byte-identical across all three arms at setup_observer end.
7. **`test_founder_positions_byte_identical_across_arms_for_same_seed`** *(implementation-equivalence test)* — founder (x, y) positions byte-identical across all three arms (all three layouts have `spawn_x = 1` and `height = 6`).
8. **`test_no_src_modifications_compared_to_v0_52b_tip`** *(implementation-equivalence test)* — assert SHA-256 hashes of the five pinned src/ files match v0.52b tip's values (= v0.53 tip's values, since v0.53 made no src/ changes). Failure message verbatim: `"v0.53b is pre-registered as no-src-change; update the pre-reg before changing src."`
9. `test_label_a_high_sensor_radius_lineage_picks_correct_lineage` — synthetic 5-founder draw with sensor_radii `[2, 5, 4, 1, 6]` → Label A picks lineage 4 (highest). Tiebreak `min(lineage_id)` on ties.
10. **`test_label_b_tick100_three_tier_tiebreak_fraction_count_min_lineage`** — synthetic readiness fractions at tick-100 with two-way tie on fraction → tiebreak by count → tiebreak by min(lineage_id). NaN-loses. Mirrors the v0.47 / v0.53 test on the new tick-100 label.
11. **`test_pre100_window_strictly_extends_pre50_window`** *(window-extension test)* — synthetic per-tick AteFood event stream with events at ticks 10, 30, 60, 90; assert `pre50_food_events_count = 2`, `pre100_food_events_count = 4`. Confirms the per-tick observer accumulates events through tick-100 (inclusive) on the upper window AND through tick-50 (inclusive) on the lower window.
12. `test_paired_d_signed_d_ge_05_fires_present_threshold` — synthetic 6-cell pool with signed_d ≥ +0.5 under both labels → tick-100 sub-verdict PRESENT.
13. `test_paired_d_signed_d_le_neg_05_fires_opposite_sign_halt_per_arm` — synthetic any tick-100 cell signed_d = −0.5 → tick-100 sub-verdict OPPOSITE_SIGN_HALT for that arm.
14. **`test_b_reachability_threshold_partition`** — synthetic `b_reachability = 0.20` (< 0.25) → priority 6 STRUCTURALLY_UNREACHABLE fires regardless of sub-verdict. Synthetic `b_reachability = 0.30` AND B sub-verdict = PRESENT → priority 4 RESOLVED. Synthetic `b_reachability = 0.30` AND B sub-verdict ∈ {PARTIAL, NOT_FOUND} → priority 5 RESOLVED_BRIDGE_NOT_FOUND.
15. `test_rollup_locked_phrases_fire_verbatim` — synthetic each of the three priority-4/5/6 outcomes → assert locked phrase contains its diagnostic substring verbatim:
    - RESOLVED: `"v0.53's \`B_WIDENED_BRIDGE_NOT_FOUND\` was reachability-censored by the 50-tick window"`
    - RESOLVED_BRIDGE_NOT_FOUND: `"the bridge fails to fire under longer observation even when food primaries become measurable"`
    - STRUCTURALLY_UNREACHABLE: `"fewer than 25% of \`widened_gradient\` runs have any founder lineage with pre100 food events"`
16. **`test_rollup_priority_cascade_and_partition_total`** — synthesize `CORPUS_REDERIVE_DRIFT_HALT` (priority 1) alongside `BRIDGE_REPLICATION_HALT` (priority 2) and `LAYOUT_OPPOSITE_SIGN_HALT` (priority 3); assert priority 1 fires first. Then priority 2 + 3 only; assert 2 fires first. Exhaustively iterate (B reachability ≥ 0.25, B sub-verdict ∈ {PRESENT, PARTIAL, NOT_FOUND}) ∪ (B reachability < 0.25) under A_null_V0_25 / C_food_ladder ∈ {PRESENT, PARTIAL, NOT_FOUND, OPPOSITE_SIGN_HALT}; assert the rollup gates only on B (A/C non-OPPOSITE outcomes have no effect on priority 4/5/6).

## Watch-outs (for future-Chronus)

- **No `src/` changes.** The window extension is purely script-local; the per-tick observer accumulates through tick-100 instead of tick-50. v0.52 + v0.52b's src/ touches stand; v0.53b inherits them with `effective_sensor_radius_override = None` everywhere → byte-identical to v0.48 A_null path under all three layouts at every tick 0..200.
- **B_widened is the primary gating arm.** A_null_V0_25 / C_food_ladder tick-100 paired_d cells are descriptive context only. Magnitude differences in A_null_V0_25 / C_food_ladder cells across tick-50 vs tick-100 are reported in Results but do NOT alter the rollup verdict.
- **A_null_V0_25 still fires `BRIDGE_REPLICATION_HALT` if its tick-50 cells drift.** The within-session sanity check is anchored at tick-50; tick-100 A_null cells are descriptive.
- **B_widened reachability threshold is 25%, pre-committed pre-data.** Lowering the threshold post-hoc is an overclaim seam — guard against it in any v0.53c follow-up.
- **PARTIAL on B_widened folds into priority 5** (RESOLVED_BRIDGE_NOT_FOUND), NOT a separate first-class outcome. The locked question is "does the bridge fire"; PARTIAL is "doesn't fire cleanly under both labels" — same substantive category as NOT_FOUND for the verdict.
- **PARTIAL on A_null_V0_25 / C_food_ladder is descriptive only.** Does NOT halt, does NOT fire any outcome. If A_null_V0_25 tick-50 sub-verdict resolves to PARTIAL, that fires `BRIDGE_REPLICATION_HALT` (priority 2) — but that's a tick-50 anchor failure, not a tick-100 PARTIAL on A_null.
- **Opposite-sign halt covers all three arms at tick-100** (unlike v0.53, which excluded A_null_V0_25 from priority 3 since priority 2 already gated on PRESENT). v0.53b's priority 2 only checks tick-50; tick-100 cells on A_null_V0_25 could fire opposite-sign without being caught by priority 2, so priority 3 expands to include all three arms.
- **`label_b_readiness_fraction_tick100`, NOT `label_b_readiness_fraction`.** Disambiguates from v0.47–v0.53's tick-50 label. The Tier-1 anchor against v0.48 uses the tick-50 form (`label_b_readiness_fraction_tick50`).
- **Tick-50 sub-verdicts are computed but NOT named as outcomes.** Only the tick-100 sub-verdicts feed the rollup. Tick-50 sub-verdicts exist for the BRIDGE_REPLICATION_HALT trigger only.
- **Locked phrase discipline:** all sub-verdict and rollup locked phrases fire verbatim where the verdict fires. No paraphrase. Layout names backticked.
- **Determinism north star** ([[scripts/core_smoke_test.py]]) must continue to pass. v0.53b makes no src/ changes; smoke test is unaffected by construction.

## Files this slice will create / modify

- `docs/experiments/fear_hunger_v0.53b.md` (this file; Results section appended after reducer run)
- `scripts/v0_53b_reachability_disambiguation_audit.py` (new)
- `tests/test_v0_53b_reachability_disambiguation_audit.py` (new, 16 tests)

No `src/` modifications. No prior reducer / audit / test / pre-reg files modified.

## Results

(To be appended after the reducer runs against the 192-run corpus. Status: pre-reg locked; reducer not yet implemented.)
