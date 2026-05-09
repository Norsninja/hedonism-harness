# fear_hunger v0.53d — substrate-axis disambiguation: open-ecology influx rescue probe on `widened_gradient` × tick-200

**Slice:** v0.53d
**Type:** **first-class observational sweep** with 3-arm tick-200 reducer (no `src/` changes; no intervention; one-knob substrate variation on the C arm only; reuses existing named layouts).
**Predecessors:** v0.46–v0.52b (full predecessor stack), v0.53 (`BRIDGE_PARTIALLY_GENERALIZES`), v0.53b (`WIDENED_BELOW_REACHABILITY_THRESHOLD_AT_TICK_100`), v0.53c (`WIDENED_BELOW_REACHABILITY_THRESHOLD_AT_TICK_200` — B_widened reachability = 0/64 at every window 50 / 100 / 200 under V0_25 substrate; full population extinction by tick-200).
**Question being asked (locked):** Is v0.53c's `WIDENED_BELOW_REACHABILITY_THRESHOLD_AT_TICK_200` verdict V0_25-substrate-specific, or geometry-fundamental? Specifically: does relaxing one substrate parameter — doubling `ambient_influx_rate` from the V0_25 baseline of `1.0` / tick to `2.0` / tick, with all other V0_25 substrate parameters held identical — lift `widened_gradient` reachability above the locked 25% threshold at tick-200 AND admit a measurable v0.48 sensor_radius spatial / foraging bridge?

v0.53c closed the window-extension question definitively: under V0_25 substrate, `widened_gradient` reachability is exactly `0/64` at every window from tick-50 through tick-200, and B_widened populations go to full extinction by tick-200. v0.53c's locked Results explicitly flagged **substrate-variation disambiguation** as the natural follow-up. v0.53d is that probe along a single substrate axis: open-ecology energy influx.

The choice of `ambient_influx_rate` (rather than `food_respawn_cooldown`, `energy_pool_initial`, `base_metabolic_cost`, or other knobs) is locked pre-data on the following grounds: (i) it is the most thermodynamically-direct knob — increasing it raises the rate at which energy enters the shared ambient pool, which under V0_25's `PARENT_TRANSFER_POOL_GAP` child-funding mode directly lifts the budget founders draw on as they traverse `widened_gradient`; (ii) v0.21 already mapped a productivity transition in `ambient_influx_rate ∈ [0.0, 2.0]` on `tight_gradient` and `food_ladder` (V0_25 sits at the `1.0` midpoint of that interval); (iii) `2.0` is v0.21's locked upper endpoint, so the dose has historical precedent and is not an arbitrary choice.

If C_widened_relaxed reachability ≥ 25% at tick-200 AND tick-200 sub-verdict resolves PRESENT, v0.53c's `WIDENED_BELOW_REACHABILITY_THRESHOLD_AT_TICK_200` is substrate-bounded — the (V0_25 × `widened_gradient`) cell's reachability ceiling is bounded by the V0_25 ambient influx, not by the geometry alone. If reachability ≥ 25% AND tick-200 sub-verdict ∈ {PARTIAL, NOT_FOUND}, the relaxed substrate admits measurement but the bridge does not fully fire — a partial-rescue outcome. If reachability < 25% at tick-200 even under doubled influx, the (V0_25 × `widened_gradient`) cell **is not rescued by `ambient_influx_rate = 2.0` under N_TICKS=200**; v0.53e (or later) substrate disambiguation along a different knob, a stronger dose, or a multi-knob co-variation remains the natural follow-up. v0.53d does not claim "geometry-fundamental"; the verdict scope is bounded to the tested relaxed-influx envelope.

## Pre-implementation note (2026-05-09, before any reducer code)

The pre-reg's design was confirmed with the user before drafting:

- **3 arms (asymmetric).** A_null_V0_25 (`tight_gradient`, V0_25 substrate, anchor). B_widened_V0_25 (`widened_gradient`, V0_25 substrate; predecessor lock from v0.53c). C_widened_relaxed (`widened_gradient`, V0_25 substrate **except** `ambient_influx_rate = 2.0`). Same 64-tuple corpus.
- **One substrate knob, one dose.** Only `ambient_influx_rate` is varied on C, and only between V0_25 baseline (`1.0`) and the locked test dose (`2.0`). Dose-response (multiple doses or multiple knobs) is deferred to v0.53e contingent on v0.53d's outcome.
- **Tick-200 verdict gating.** Per-tick observer accumulates through tick-200 (matches v0.53c's canonical three-window template). Three Label B variants (`tick50` anchor / `tick100` descriptive / `tick200` verdict-gating) computed in parallel.
- **No `src/` modifications.** v0.53d inherits v0.52b-tip src/ (= v0.53 / v0.53b / v0.53c tip src/, since none touched src/). The substrate variation is purely chamber-config-local: C arm calls `run_chamber(..., ambient_influx_rate=2.0)`; A and B preserve the V0_25 baseline (`ambient_influx_rate=1.0`).
- **Pool requirement preserved.** `ambient_influx_rate > 0` requires `energy_pool_initial` to be set. C arm preserves `energy_pool_initial=1500.0` (V0_25 baseline) — only the influx is overridden, not the pool itself. C is a relaxed-V0_25, not a non-pool config.
- **Categorical Tier-2 anchor on B_widened_V0_25.** v0.53d locks B_widened_V0_25's reachability at tick-200 as `0/64` (the v0.53c result), categorical, not float-tolerance. ANCHOR_REPLICATION_HALT fires on integer mismatch. This is a stronger predecessor coupling than a tolerance-bounded float anchor and matches the all-zero structure v0.53c established.
- **Explicit extinction and degenerate-label handling.** v0.53c's Results showed B_widened goes to full extinction at tick-200 (label_b_n=0). Under V0_25 substrate, this is locked-in via the categorical Tier-2 anchor: B_widened_V0_25 will be fully extinct, all 6 Label-A/Label-B × 3-observable cells will be NaN or near-zero, and B's tick-200 sub-verdict is informationally NOT_FOUND. This is the predecessor-locked baseline; v0.53d does not gate the rollup on B's sub-verdict, only on its categorical reachability anchor. C_widened_relaxed's extinction trajectory is the open question — population-stability metrics are logged for C at all three windows.

## Conservation framing — observational, no `src/`, no intervention, one-knob substrate variation on C only

- **No `src/` modifications.** v0.53d inherits v0.53 / v0.53b / v0.53c's src/ state. The relaxed-influx variation is `run_chamber(... ambient_influx_rate=2.0)` on C only.
- **No modifications to prior reducer or audit scripts.** v0.34's `lineage_replay.py`, v0.35's `lineage_survival_replay.py`, v0.36's `trait_replay.py`, v0.48's reducer, v0.53 / v0.53b / v0.53c's reducers remain byte-identical to their merged forms.
- **A_null_V0_25 arm is byte-identical to v0.48 / v0.53 / v0.53b / v0.53c A_null path AT TICK-50.** Tier-1 re-anchor enforces this within 1e-3.
- **B_widened_V0_25 arm is byte-identical to v0.53 / v0.53b / v0.53c's B_widened_gradient arm at every tick 0..200.** Same `streams.mutation`, founder draws, per-agent RNGs, world layout. Tier-2 categorical anchor enforces `b_widened_v025_reachability_run_share_tick_200 == 0.0`.
- **C_widened_relaxed differs from B_widened_V0_25 only via `ambient_influx_rate` (1.0 → 2.0).** All other WorldConfig / BodyConfig / ReproductionConfig / ActionConfig parameters identical to V0_25 baseline. Same chamber layout (`widened_gradient_layout()`), same founder draw, same per-agent RNGs.
- **No intervention at any level on any arm.** No founder body trait modification, no override patching, no helper RNG, no shuffle, no clamp, no permutation.
- **Single-axis substrate variation.** v0.53d differs from v0.53c only on the C arm's `ambient_influx_rate`; A and B arms preserve V0_25 baseline byte-identically.

## Corpus (locked, 64 × 3 arms = 192 runs)

Same shape as v0.53 / v0.53b / v0.53c:

| version | seeds | hazards | runs per arm | total runs |
|---|---|---|---|---|
| v0.42 | 41..48 | {0, 8} | 16 | 48 |
| v0.43R | 49..56 | {0, 8} | 16 | 48 |
| v0.44 | 57..64 | {0, 8} | 16 | 48 |
| v0.45 | 65..72 | {0, 8} | 16 | 48 |
| **total** | | | | **192** |

V0_25 substrate identical to v0.53 / v0.53b / v0.53c on A and B; C identical except `ambient_influx_rate=2.0`. Wall time estimate ~18–30 minutes total.

## Arms (locked, 3 — asymmetric substrate)

### A_null_V0_25

```
ChamberLayout = tight_gradient_layout()
ambient_influx_rate = 1.0  (V0_25 baseline)
energy_pool_initial = 1500.0
food_respawn_cooldown = 50
child_funding_mode = PARENT_TRANSFER_POOL_GAP
hazard_damage = per (version, hazard) corpus row
FounderSpec(traits_override=None)
no patch, no body_config override, no per-agent override
```

Byte-identical to v0.48 / v0.53 / v0.53b / v0.53c A_null path at every tick 0..200. Used for:
1. **Tier-1 anchor at tick-50** (against v0.48 / v0.53 / v0.53b / v0.53c published cells).
2. **Descriptive context at tick-100 and tick-200** (no published anchor; magnitude shifts reported in Results, do not gate the verdict).

### B_widened_V0_25

```
ChamberLayout = widened_gradient_layout()
ambient_influx_rate = 1.0  (V0_25 baseline; same as A)
energy_pool_initial = 1500.0
food_respawn_cooldown = 50
child_funding_mode = PARENT_TRANSFER_POOL_GAP
hazard_damage = per (version, hazard) corpus row
FounderSpec(traits_override=None)
no patch, no body_config override, no per-agent override
```

Byte-identical to v0.53 / v0.53b / v0.53c's B_widened_gradient arm at every tick 0..200. **Predecessor-lock arm for v0.53d**: the rollup gates on B_widened_V0_25's categorical reachability anchor (`reachability_run_share_tick_200 == 0.0`), not on its sub-verdict. The arm exists in v0.53d only to enforce the v0.53c categorical lock (any drift halts loud) and to provide the V0_25-baseline contrast for C.

### C_widened_relaxed

```
ChamberLayout = widened_gradient_layout()
ambient_influx_rate = 2.0  (RELAXED — V0_25 baseline doubled)
energy_pool_initial = 1500.0  (V0_25 baseline; preserves pool requirement)
food_respawn_cooldown = 50  (V0_25 baseline)
child_funding_mode = PARENT_TRANSFER_POOL_GAP  (V0_25 baseline)
hazard_damage = per (version, hazard) corpus row  (V0_25 baseline)
FounderSpec(traits_override=None)
no patch, no body_config override, no per-agent override
```

Differs from B_widened_V0_25 by exactly one knob: `ambient_influx_rate` (1.0 → 2.0). **The primary arm of v0.53d**: the verdict gates on C's tick-200 reachability and tick-200 sub-verdict.

## Labels (locked, two — with three Label B variants)

### Label A — `high_sensor_radius_lineage`

Identical to v0.48–v0.53c. Trait-resolved (`int(founder.body.traits.sensor_radius)`); tiebreak `min(lineage_id)`. Time-window-independent.

### Label B — three variants computed in parallel

Each is `argmax_lineage(tickN_above_threshold_fraction)` with the v0.47 3-tier tiebreak (fraction → count → min(lineage_id), NaN-loses):

- **`high_tick50_readiness_fraction_lineage`** — used for the Tier-1 anchor against v0.48 / v0.53 / v0.53b / v0.53c on the A arm.
- **`high_tick100_readiness_fraction_lineage`** — used for descriptive context (NOT gating).
- **`high_tick200_readiness_fraction_lineage`** — used for the v0.53d **verdict** on the C arm.

If at tick-N **no lineage has any agent above the readiness threshold** (everyone NaN or zero), Label B for that run is undefined; the per-run paired_d delta cells are `nan` and the per-arm cell's `n` decrements.

## Primary observables (locked, 3, computed at three windows)

| # | name pattern | windows | expected sign |
|---|---|---|:-:|
| 1 | `pre{N}_food_events_count` | N ∈ {50, 100, 200} | + |
| 2 | `pre{N}_food_energy_acquired` | N ∈ {50, 100, 200} | + |
| 3 | `mean_distance_to_nearest_food_cell_tick{N}` | N ∈ {50, 100, 200} | − |

Definitions / aggregation rules / NaN handling: copy-local from v0.48–v0.53c. Primaries 1 / 2 accumulate `AteFood` events through tick-N inclusive (`tick_now <= TICK_N`). Primary 3 is a snapshot at tick-N over living agents per lineage.

The reducer captures all three windows from the same 192 sim runs in a single per-tick observer pass.

## Effect-size rule (locked, sign-aware, identical to v0.48–v0.53c)

```
per_run_delta_O = label_lineage_value_O − mean(non_label_lineage_values_O)
paired_d_O      = mean(per_run_delta_O) / stdev(per_run_delta_O, ddof=1)
signed_d_O      = paired_d_O × expected_sign
fires_expected  iff signed_d_O ≥ +0.5
fires_wrong     iff signed_d_O ≤ −0.5
```

## Reachability metrics at tick-200 (locked, pre-data)

```
b_widened_v025_reachability_run_share_tick_200 =
    fraction of B_widened_V0_25 runs where at least one founder lineage
    has pre200_food_events_count > 0

c_widened_relaxed_reachability_run_share_tick_200 =
    fraction of C_widened_relaxed runs where at least one founder lineage
    has pre200_food_events_count > 0
```

Domain: 64 runs per arm. Threshold: **`B_REACHABILITY_THRESHOLD = 0.25`** (preserved from v0.53b / v0.53c).

The B_widened_V0_25 metric is the Tier-2 categorical predecessor anchor (must equal `0.0` exactly, i.e., `0/64`). The C_widened_relaxed metric is the verdict-gating reachability (compared against the 0.25 threshold).

## Population-stability and degenerate-label descriptive metrics (locked, pre-data, per arm × window)

Identical structure to v0.53c:

```
arm_living_population_run_share_tick_N =
    fraction of arm runs where at least one agent is alive at tick-N

arm_label_a_n_runs_tick_N =
    number of arm runs where Label A produces a non-nan winner at tick-N

arm_label_b_n_runs_tick_N =
    number of arm runs where Label B produces a non-nan winner at tick-N
```

Descriptive only — no halt or outcome gates on them directly. Reported in Results and feed the interpretive frame for tick-200 cells with low `n`.

## Per-arm sub-verdicts (locked, 4-way each)

Identical structure to v0.53c, one verdict per arm at tick-200:

| condition | A_null_V0_25 (tick-200) | B_widened_V0_25 (tick-200) | C_widened_relaxed (tick-200) |
|---|---|---|---|
| both labels clear ≥ 2/3 of the three locked cells, with NaN treated as non-firing, 0 wrong-sign | `A_NULL_V025_TICK200_BRIDGE_PRESENT` | `B_WIDENED_V025_TICK200_BRIDGE_PRESENT` | `C_RELAXED_TICK200_BRIDGE_PRESENT` |
| exactly one label clears ≥ 2/3 of the three locked cells, with NaN treated as non-firing, 0 wrong-sign | `A_NULL_V025_TICK200_BRIDGE_PARTIAL` | `B_WIDENED_V025_TICK200_BRIDGE_PARTIAL` | `C_RELAXED_TICK200_BRIDGE_PARTIAL` |
| neither label clears ≥ 2/3 of the three locked cells, with NaN treated as non-firing, 0 wrong-sign | `A_NULL_V025_TICK200_BRIDGE_NOT_FOUND` | `B_WIDENED_V025_TICK200_BRIDGE_NOT_FOUND` | `C_RELAXED_TICK200_BRIDGE_NOT_FOUND` |
| any primary signed_d ≤ −0.5 under either label | `A_NULL_V025_TICK200_OPPOSITE_SIGN_HALT` | `B_WIDENED_V025_TICK200_OPPOSITE_SIGN_HALT` | `C_RELAXED_TICK200_OPPOSITE_SIGN_HALT` |

**Strict NaN-counts-toward-denominator rule preserved from v0.48–v0.53c.** A label with 3 cells of which 2 are NaN and 1 fires expected has 1/3 firing-cell ratio (NaN counts toward 3, not toward 1) → does not clear 2/3. A label with 3 NaN cells clears 0/3 → does not fire. Test #12 enforces.

Each arm's tick-200 paired_d cells (3 observables × 2 labels = 6 cells per arm; 18 cells total across the three arms) are computed independently from the arm's 64-run pool with NaN-runs excluded from the per-cell `n`.

## Slice rollup verdicts (locked, 6 outcomes, priority-ordered)

Priority order (first-matching wins). The non-halt outcomes (priorities 4–6) gate **only on C_widened_relaxed**; A_null_V0_25 and B_widened_V0_25 tick-200 sub-verdicts are descriptive in Results unless the A_null sub-verdict ≠ PRESENT (priority 2) or the B_widened_V0_25 categorical reachability anchor drifts (priority 2).

1. `CORPUS_REDERIVE_DRIFT_HALT`
2. `ANCHOR_REPLICATION_HALT`
3. `RELAXED_OPPOSITE_SIGN_HALT`
4. `WIDENED_BRIDGE_RESCUED_BY_RELAXED_INFLUX`
5. `WIDENED_BELOW_REACHABILITY_THRESHOLD_UNDER_RELAXED_INFLUX`
6. `WIDENED_BRIDGE_PARTIALLY_RESCUED_BY_RELAXED_INFLUX`

### Halt conditions

| priority | rollup verdict | trigger | locked phrase (verbatim) |
|---|---|---|---|
| 1 | `CORPUS_REDERIVE_DRIFT_HALT` | A_null_V0_25 arm `a_share_h8` for any of v0.42 / v0.44 / v0.45 drifts > 1e-3 from the published reference | "Halt: A_null_V0_25 re-anchor drifted from the published Results value for {version}; v0.53d's deterministic re-execution of the V0_25 corpus does not reproduce the published metric within 1e-3." |
| 2 | `ANCHOR_REPLICATION_HALT` | (a) A_null_V0_25 tick-50 signed_d for any of the six v0.48 / v0.53 / v0.53b / v0.53c cells drifts > 1e-3 from the published value, OR (b) A_null_V0_25 tick-50 sub-verdict ≠ PRESENT, OR (c) `b_widened_v025_reachability_run_share_tick_200` ≠ `0.0` (i.e., any B_widened_V0_25 run has at least one founder lineage with `pre200_food_events_count > 0`, contradicting v0.53c's `0/64` lock) | "Halt: v0.53d's A_null_V0_25 arm does not reproduce v0.48 / v0.53 / v0.53b / v0.53c's tick-50 spatial bridge, OR v0.53d's B_widened_V0_25 arm does not reproduce v0.53c's `0/64` reachability lock at tick-200. v0.53d cannot interpret the C_widened_relaxed cells without an established baseline on the V0_25 substrate." |
| 3 | `RELAXED_OPPOSITE_SIGN_HALT` | C_widened_relaxed has finite `signed_d ≤ −0.5` under either gating label on a tick-200 primary observable | "Halt: a v0.53d C_widened_relaxed tick-200 spatial / foraging primary fires in the WRONG direction under a gating label; doubling `ambient_influx_rate` from V0_25 baseline `1.0` to `2.0` / tick on the `widened_gradient` layout surfaces a regime incompatible with the locked expected signs." |

### Tier-1 (priority 2.a) re-anchor — A_null_V0_25 tick-50 cells

Identical six cells to v0.48 / v0.53 / v0.53b / v0.53c:

| label | observable | sign | published signed_d |
|---|---|:-:|:-:|
| `label_a_sensor_radius` | `pre50_food_events_count` | + | **+1.066** |
| `label_a_sensor_radius` | `pre50_food_energy_acquired` | + | **+1.066** |
| `label_a_sensor_radius` | `mean_distance_to_nearest_food_cell_tick50` | − | **+1.916** |
| `label_b_readiness_fraction_tick50` | `pre50_food_events_count` | + | **+0.916** |
| `label_b_readiness_fraction_tick50` | `pre50_food_energy_acquired` | + | **+0.916** |
| `label_b_readiness_fraction_tick50` | `mean_distance_to_nearest_food_cell_tick50` | − | **+1.179** |

Drift tolerance = 1e-3.

### Tier-2 (priority 2.c) categorical anchor — B_widened_V0_25 tick-200 reachability

| anchor | locked value | tolerance |
|---|:-:|---|
| `b_widened_v025_reachability_run_share_tick_200` | **0.0** (i.e., `0/64`) | exact (categorical) |

Locked from v0.53c's measured result. Any non-zero value (i.e., any single B_widened_V0_25 run with at least one founder lineage producing `pre200_food_events_count > 0`) halts loud under priority 2.

### Outcome conditions (only consulted if no halt fires)

| priority | rollup verdict | trigger | locked phrase (verbatim) |
|---|---|---|---|
| 4 | `WIDENED_BRIDGE_RESCUED_BY_RELAXED_INFLUX` | `c_widened_relaxed_reachability_run_share_tick_200 ≥ 0.25` AND C_widened_relaxed tick-200 sub-verdict = `C_RELAXED_TICK200_BRIDGE_PRESENT` | "On the modern A_null corpus with the V0_25 substrate held constant except for `ambient_influx_rate = 2.0` / tick (doubled from the V0_25 baseline of `1.0` / tick) on `widened_gradient`, the v0.48 sensor_radius spatial / foraging bridge fires PRESENT under the locked +0.5 paired_d threshold at tick-200. The geometry/substrate cell that v0.53c locked as `WIDENED_BELOW_REACHABILITY_THRESHOLD_AT_TICK_200` admits a measurable bridge under the relaxed-influx envelope: B_widened_V0_25 reachability remains `0/64` at tick-200 (predecessor lock holds), C_widened_relaxed reachability clears the locked 25% threshold, and ≥ 2/3 spatial / foraging primaries fire PRESENT under both gating labels. The (V0_25 × `widened_gradient`) reachability ceiling is bounded by the V0_25 ambient influx, not by the geometry alone: `WIDENED_BRIDGE_RESCUED_BY_RELAXED_INFLUX`." |
| 5 | `WIDENED_BELOW_REACHABILITY_THRESHOLD_UNDER_RELAXED_INFLUX` | `c_widened_relaxed_reachability_run_share_tick_200 < 0.25` | "On the modern A_null corpus with the V0_25 substrate held constant except for `ambient_influx_rate = 2.0` / tick (doubled from the V0_25 baseline of `1.0` / tick) on `widened_gradient`, fewer than 25% of C_widened_relaxed runs have any founder lineage with pre200 food events. C_widened_relaxed's reachability is below the locked 25% threshold at tick-200; the geometry/substrate cell that v0.53c locked as `WIDENED_BELOW_REACHABILITY_THRESHOLD_AT_TICK_200` remains below the reachability threshold under the tested relaxed-influx envelope. The bridge is not rescued by `ambient_influx_rate = 2.0` under V0_25 × `widened_gradient` × N_TICKS=200; v0.53e (or later) substrate disambiguation along a different knob, a stronger dose, or multi-knob co-variation remains the natural follow-up: `WIDENED_BELOW_REACHABILITY_THRESHOLD_UNDER_RELAXED_INFLUX`." |
| 6 | `WIDENED_BRIDGE_PARTIALLY_RESCUED_BY_RELAXED_INFLUX` | `c_widened_relaxed_reachability_run_share_tick_200 ≥ 0.25` AND C_widened_relaxed tick-200 sub-verdict ∈ {`C_RELAXED_TICK200_BRIDGE_PARTIAL`, `C_RELAXED_TICK200_BRIDGE_NOT_FOUND`} | "On the modern A_null corpus with the V0_25 substrate held constant except for `ambient_influx_rate = 2.0` / tick (doubled from the V0_25 baseline of `1.0` / tick) on `widened_gradient`, C_widened_relaxed's reachability clears the locked 25% threshold at tick-200 but the v0.48 sensor_radius spatial / foraging bridge does not fully fire PRESENT — fewer than 2/3 primaries fire across both gating labels at tick-200 under the strict NaN rule. The geometry/substrate cell that v0.53c locked as `WIDENED_BELOW_REACHABILITY_THRESHOLD_AT_TICK_200` is partially rescued under the relaxed-influx envelope: reachability becomes measurable but the bridge does not fully replicate. Layout-specific partial-rescue logged in Results: `WIDENED_BRIDGE_PARTIALLY_RESCUED_BY_RELAXED_INFLUX`." |

The rollup is **categorical-only**. Magnitude differences in A_null_V0_25 / B_widened_V0_25 / C_widened_relaxed tick-100 cells (or descriptive A / B tick-200 cells) are reported in Results but do not alter the verdict.

The 3 non-halt outcomes form a total partition of (C reachability ≥ 0.25, C sub-verdict ∈ {PRESENT, PARTIAL, NOT_FOUND}) ∪ (C reachability < 0.25). Halts cover OPPOSITE_SIGN, drift, replication. Test #16 enforces the partition exhaustively.

## Cautious framing (per CLAUDE.md)

- "**Bridge rescued by relaxed influx**", "**reachability ceiling bounded by V0_25 ambient influx, not by the geometry alone**", "**bridge is not rescued by `ambient_influx_rate = 2.0` under V0_25 × `widened_gradient` × N_TICKS=200**", "**substrate-bounded, not geometry-fundamental**" — NOT "**proves**", "**causes**", or "**rules out**".
- "**Tested relaxed-influx envelope**" specifically means `ambient_influx_rate ∈ {1.0 (V0_25 baseline), 2.0 (v0.53d test dose)}` at `N_TICKS=200`. v0.53d does NOT establish behavior at influx rates between 1.0 and 2.0, above 2.0, or under multi-knob co-variation; those require separate slices.
- "**(V0_25 × `widened_gradient`) cell**" means the specific layout × substrate combination tested. v0.53d's verdict is bounded to the relaxed-influx variant only — the verdict does NOT generalize to layouts not in the v0.53/b/c set, to substrates not in the V0_25 family with `ambient_influx_rate ∈ {1.0, 2.0}`, or to N_TICKS > 200.
- v0.53d explicitly does not establish: cross-layout generalization beyond the three v0.53 layouts, mechanism for any rescue or non-rescue outcome, generalization to non-V0_25 substrates beyond the influx axis, behavior at `n_ticks > 200`, causal contribution per layout (Reading-A causal-generalization slice remains the deferred candidate).

## What v0.53d cannot establish (logged here pre-data, not retrofittable)

- ✗ **"`widened_gradient` is geometry-fundamental"** if priority 5 fires. v0.53d tests V0_25 substrate × `ambient_influx_rate=2.0` × N_TICKS=200 only. Different metabolic / energy / pool / cooldown parameters (single-knob or multi-knob), or stronger influx doses, may admit reachability. v0.53e remains the natural follow-up.
- ✗ **"The bridge IS or IS NOT load-bearing on `widened_gradient`"** under any priority-4/5/6 outcome. The observation tells us about reachability and bridge-firing under doubled influx; it does not establish channel-level causal contribution (deferred Reading-A slice).
- ✗ **A revised v0.53 / v0.53b / v0.53c verdict.** All three stand as historical contracts for their respective windows / substrates. v0.53d is the *substrate-axis* probe; its scope is v0.53c's deferred follow-up question along a single knob and dose.
- ✗ **Mechanism behind any rescue or non-rescue outcome.** Population dynamics under V0_25 × `widened_gradient` × `ambient_influx_rate=2.0` are descriptively logged; no mechanism is formally established.
- ✗ **Generalization beyond the tested arms.** The verdict is bounded to (`tight_gradient` × V0_25, `widened_gradient` × V0_25, `widened_gradient` × V0_25 with `ambient_influx_rate=2.0`) at `N_TICKS=200`.

## Open framing (NOT in v0.53d primary)

- **v0.53e — substrate-axis disambiguation along a different knob or stronger dose.** Triggered if v0.53d fires priority 5. Candidate knobs: `food_respawn_cooldown` (faster food regrowth), `energy_pool_initial` (more starting headroom), `base_metabolic_cost` (slower energy depletion). Or a stronger dose along `ambient_influx_rate` (e.g., `3.0` / `4.0`). Independent observational slice.
- **v0.53f (or later) — investigate the C_food_ladder Label B degradation trajectory.** Why does Label B's bridge weaken from tick-50 to tick-200 specifically on `food_ladder` while Label A holds? Per-tick-window paired_d trajectory probe. Independent of v0.53d outcome.
- **v0.53g (or later) — Reading-A causal-generalization slice on layouts admitting the bridge.** Re-run v0.49's null + clamp_4 + permutation_5! per layout that admits measurement. Includes `tight_gradient` and `food_ladder` from v0.53c; includes `widened_gradient` only if v0.53d (or later substrate slice) admits measurement under any envelope.
- **v0.54 — joint ablation** (zero-cost AND shuffle). Channel-interaction question. Independent of layout × substrate-axis findings.
- **Eventual fresh-stream calibration** on the v0.46–v0.53d conclusion stack — needed for any "mechanism" declaration. Longer-horizon.

## Re-anchor (locked — Tier-1 and corpus only at tick-50)

| version | published `a_share_h8` |
|---|---|
| v0.42 | 0.652 |
| v0.43R | NOT PUBLISHED (informational-only) |
| v0.44 | 0.878 |
| v0.45 | 0.818 |

A_null_V0_25 arm only gates the corpus rollup. B_widened_V0_25 and C_widened_relaxed arms re-derive their own `a_share_h8` for descriptive logging; do NOT gate the verdict on `a_share_h8`.

## Outputs (locked)

```
runs/v0.53d-substrate-axis-relaxed-influx/per_run_per_lineage_v053d.csv
  columns: arm, layout_name, ambient_influx_rate, version, seed, hazard, run_id, lineage_id,
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

runs/v0.53d-substrate-axis-relaxed-influx/audit_summary.csv
  columns: section, key, value
  sections:
    - reanchor_a_share_h8: per (arm, version, h=8) derived + (A_null_V0_25 only) published + drift_abs
    - bridge_reanchor_tick50: per (label, observable) v0.48 / v0.53 / v0.53b / v0.53c published signed_d + v0.53d A_null_V0_25 derived + drift_abs (Tier-1 anchor)
    - paired_d_tick50: per (arm, gating-label, observable) — descriptive
    - paired_d_tick100: per (arm, gating-label, observable) — descriptive
    - paired_d_tick200: per (arm, gating-label, observable) — VERDICT-GATING for C_widened_relaxed
    - reachability_tick50: per arm reachability_run_share_tick_50 (descriptive)
    - reachability_tick100: per arm reachability_run_share_tick_100 (descriptive)
    - reachability_tick200: per arm reachability_run_share_tick_200 (B_widened_V0_25 = Tier-2 categorical anchor; C_widened_relaxed = verdict-gating)
    - population_stability: per (arm, window) living_population_run_share + label_a_n_runs + label_b_n_runs (descriptive)
    - sub_verdicts_tick200: per arm — sub-verdict + locked sub-phrase
    - rollup_verdict: locked rollup verdict + locked rollup phrase

runs/v0.53d-substrate-axis-relaxed-influx/audit_log.txt
  human-readable echo with all locked phrases verbatim where they fire,
  plus per-arm three-window paired_d tables, per-arm three-window
  reachability table, and per-arm population-stability table.
```

## Implementation plan (locked)

1. **No `src/` changes.** Confirmed.
2. Fresh script `scripts/v0_53d_substrate_axis_relaxed_influx_audit.py`. CLI: `uv run python scripts/v0_53d_substrate_axis_relaxed_influx_audit.py [--out-dir runs/v0.53d-substrate-axis-relaxed-influx]`.
3. Per (version, seed, hazard) tuple, run **3 arms**. A and B construct `HHModel` via the V0_25 path with `ambient_influx_rate=1.0`; C constructs the same path but with `ambient_influx_rate=2.0`. Tick observer accumulates events through tick-200 on all three arms.
4. Setup_observer order (matches v0.53c merged implementation): (a) capture v0.53d founder audit table, (b) wire `AgentBorn` / `AteFood` / `HazardDamageApplied` listeners, (c) read back `model.world.width` and assert layout match per-arm, (d) capture tick-0 snapshot.
5. Per-tick observer accumulates `pre50_*` / `pre100_*` / `pre200_*` rollups in parallel; emits all three at end-of-run.
6. Use the relaxed contiguous-prefix tick-records invariant from v0.53b / v0.53c (handles early extinction; tick-0 always present; `1 ≤ len ≤ TICK_200 + 1`).
7. Aggregate per-lineage primaries at all three windows. Compute Label A and three Label B variants (tick50 / tick100 / tick200).
8. Compute paired_d per (arm, gating-label, observable, window) cell. 18 cells per window × 3 windows = 54 cells total. Tick-200 cells gate the C_widened_relaxed sub-verdict (which gates the rollup); tick-50 cells gate the A_null_V0_25 Tier-1 anchor; tick-100 cells are descriptive. Apply the strict "≥ 2/3 firing cells excluding NaN" rule for sub-verdicts.
9. Compute per-arm reachability_run_share at all three windows. The B_widened_V0_25 tick-200 value is the Tier-2 categorical anchor (must equal `0.0` exactly). The C_widened_relaxed tick-200 value is the verdict-gating reachability.
10. Compute per-arm population-stability metrics (living_population_run_share, label_a_n_runs, label_b_n_runs at all three windows).
11. **Tier-1 bridge re-anchor** (priority 2.a / 2.b): A_null_V0_25 arm's six tick-50 cells vs v0.48 / v0.53 / v0.53b / v0.53c published; halt if drift > 1e-3 OR if A_null_V0_25 tick-50 sub-verdict ≠ PRESENT.
12. **Tier-2 categorical anchor** (priority 2.c): `b_widened_v025_reachability_run_share_tick_200 == 0.0` exactly; halt if any single B_widened_V0_25 run has `pre200_food_events_count > 0` for any lineage.
13. **Corpus re-anchor** (priority 1): A_null_V0_25 arm only; halt if `a_share_h8` for v0.42 / v0.44 / v0.45 drifts > 1e-3.
14. **Relaxed opposite-sign halt** (priority 3): scan all C_widened_relaxed tick-200 gating-label cells; halt if any signed_d ≤ −0.5.
15. Compute slice rollup verdict per the locked priority + (C reachability tick-200, C sub-verdict tick-200) decision matrix; print + write the locked phrase verbatim.

The reducer is fully self-contained: it reads no `runs/` artifacts. Wall time estimate ~18–30 minutes for 192 runs.

## Test list (locked, 16 tests; extends v0.53c's pattern)

`tests/test_v0_53d_substrate_axis_relaxed_influx_audit.py`:

1. **`test_paired_d_function_reproduces_hand_computed_signed_d_on_fixture_and_tier1_constants_match_v048_published_values`** *(re-anchor test, two-part)* — Part A: paired_d formula on a hand-computed fixture pool (8 runs) within 1e-9. Part B: Tier-1 constants byte-equal to v0.48 published values.
2. **`test_a_null_v025_corpus_a_share_h8_re_anchors_v042_v044_v045`** — drift halt fires if any drift > 1e-3.
3. `test_arm_a_null_v025_uses_tight_gradient_layout_and_v025_influx` — chamber driver receives `tight_gradient_layout()` AND `ambient_influx_rate=1.0`; layout invariant assert.
4. `test_arm_b_widened_v025_uses_widened_gradient_layout_and_v025_influx` — chamber driver receives `widened_gradient_layout()` AND `ambient_influx_rate=1.0`; layout invariant assert.
5. **`test_arm_c_widened_relaxed_uses_widened_gradient_layout_and_relaxed_influx`** — chamber driver receives `widened_gradient_layout()` AND `ambient_influx_rate=2.0`; `energy_pool_initial=1500.0` preserved (pool requirement); layout invariant assert; explicit assertion that no other WorldConfig knob differs from V0_25 baseline.
6. **`test_founder_traits_byte_identical_across_arms_for_same_seed`** — full Traits records byte-identical across all three arms at setup_observer end. Arms differ only in chamber config (layout + influx), not in founder draw.
7. **`test_founder_positions_byte_identical_across_arms_for_same_seed`** — founder (x, y) byte-identical (all three arms have spawn_x=1, height=6).
8. **`test_no_src_modifications_compared_to_v0_52b_tip`** — SHA-256 hashes of five pinned src/ files match v0.52b tip's values. Failure message verbatim: `"v0.53d is pre-registered as no-src-change; update the pre-reg before changing src."`
9. `test_label_a_high_sensor_radius_lineage_picks_correct_lineage` — synthetic 5-founder draw; tiebreak `min(lineage_id)`.
10. **`test_label_b_three_variants_three_tier_tiebreak_at_each_window`** — synthetic readiness fractions at tick-50 / tick-100 / tick-200 with two-way tie on fraction → tiebreak by count → tiebreak by min(lineage_id). NaN-loses. Verifies all three Label B variants behave identically except for the snapshot tick.
11. **`test_pre200_window_strictly_extends_pre100_and_pre50_windows`** *(window-extension test; preserved from v0.53c)* — synthetic per-tick AteFood events at ticks 10, 30, 60, 90, 130, 180, 200; assert `pre50_food_events_count = 2`, `pre100_food_events_count = 4`, `pre200_food_events_count = 7`. Confirms inclusive-upper-bound at tick-200 boundary.
12. **`test_subverdict_present_requires_two_thirds_firing_cells_excluding_nan_strict`** — synthetic 3-cell label with 2 firing + 1 NaN → label clears 2/3 → sub-verdict considers this label PRESENT-contributing. Synthetic 3-cell label with 1 firing + 2 NaN → does NOT contribute. Synthetic 3-cell label with 0 firing + 3 NaN → does NOT contribute.
13. `test_paired_d_signed_d_le_neg_05_fires_relaxed_opposite_sign_halt_for_c_arm` — synthetic any C_widened_relaxed tick-200 cell signed_d = −0.5 → tick-200 sub-verdict OPPOSITE_SIGN_HALT for C → priority 3 RELAXED_OPPOSITE_SIGN_HALT fires. Synthetic A or B tick-200 wrong-sign does NOT fire priority 3 (caught by priority 2 via sub-verdict ≠ PRESENT for A; caught by priority 2 categorical anchor for B if reachability shifts).
14. **`test_b_widened_v025_categorical_anchor_at_tick_200`** *(NEW Tier-2 anchor test)* — synthetic B_widened_V0_25 reachability=0.0 → priority 2 does NOT fire (categorical lock holds). Synthetic B_widened_V0_25 reachability=0.015625 (1/64) → priority 2 ANCHOR_REPLICATION_HALT fires (categorical lock broken). Verifies the integer-categorical (`== 0.0`) comparison, not float-tolerance.
15. **`test_c_widened_relaxed_reachability_threshold_partition_at_tick_200`** — synthetic `c_reachability_tick200 = 0.20` (< 0.25) → priority 5 BELOW_REACHABILITY_THRESHOLD fires regardless of C sub-verdict. Synthetic `c_reachability_tick200 = 0.30` AND C sub-verdict = PRESENT → priority 4 RESCUED. Synthetic `c_reachability_tick200 = 0.30` AND C sub-verdict ∈ {PARTIAL, NOT_FOUND} → priority 6 PARTIALLY_RESCUED.
16. **`test_rollup_locked_phrases_fire_verbatim_and_priority_cascade_partition_total`** — synthetic each priority-4/5/6 outcome → assert locked phrase contains diagnostic substring verbatim:
    - RESCUED: `"the (V0_25 × \`widened_gradient\`) reachability ceiling is bounded by the V0_25 ambient influx, not by the geometry alone"` AND `"WIDENED_BELOW_REACHABILITY_THRESHOLD_AT_TICK_200"` (predecessor reference).
    - BELOW_THRESHOLD: `"The bridge is not rescued by \`ambient_influx_rate = 2.0\` under V0_25 × \`widened_gradient\` × N_TICKS=200"` AND `"WIDENED_BELOW_REACHABILITY_THRESHOLD_AT_TICK_200"`.
    - PARTIALLY_RESCUED: `"reachability becomes measurable but the bridge does not fully replicate"` AND `"WIDENED_BELOW_REACHABILITY_THRESHOLD_AT_TICK_200"`.
    Synthesize halt cascade (priorities 1 / 2.a / 2.b / 2.c / 3); assert priority order. Exhaustively iterate (C reachability ≥ 0.25, C sub-verdict ∈ {PRESENT, PARTIAL, NOT_FOUND}) ∪ (C reachability < 0.25); assert unique outcome per cell.

## Watch-outs (for future-Chronus)

- **No `src/` changes.** Single-knob substrate variation is chamber-config-local. Smoke test unaffected. Test #8 pins same v0.52b-tip SHA-256 hashes as v0.53 / v0.53b / v0.53c.
- **C_widened_relaxed is the primary gating arm.** A_null_V0_25 / B_widened_V0_25 tick-200 cells are descriptive (or anchor-gating only).
- **Tier-2 categorical anchor on B_widened_V0_25 is integer-categorical.** Compare to `0.0` exactly. Any single B_widened_V0_25 run producing `pre200_food_events_count > 0` halts loud. This is stronger than a float-tolerance anchor and matches the all-zero structure v0.53c established.
- **Pool requirement for ambient_influx_rate.** `ambient_influx_rate > 0` requires `energy_pool_initial` to be set. C must preserve `energy_pool_initial=1500.0`. Test #5 enforces.
- **Three windows in parallel, single observer pass.** Per-tick observer must accumulate `pre50_*` / `pre100_*` / `pre200_*` AND snapshot `mean_distance_*_tick50` / `_tick100` / `_tick200` from a single iteration. Per-event accumulation logic must check `tick_now <= TICK_50` / `<= TICK_100` / `<= TICK_200` independently.
- **Three Label B variants.** Computed in parallel from the same per-lineage `tickN_above_threshold_fraction` values. Each variant is independent (different snapshot tick); tick-200 gates the C arm's sub-verdict.
- **Strict "≥ 2/3 firing cells, NaN counts toward denominator" sub-verdict rule.** A label with 3 NaN cells cannot fire PRESENT under that label. Test #12 enforces.
- **C_widened_relaxed extinction trajectory is the open question.** B_widened_V0_25 is locked to full extinction (predecessor lock from v0.53c); C may extinct at a different rate under doubled influx. Population-stability metrics logged at all three windows for all three arms.
- **Relaxed contiguous-prefix tick-records invariant** (from v0.53b / v0.53c) is required: any arm's populations going extinct mid-window are normal; the per-tick observer will not be called for ticks after the last living agent dies.
- **Tier-1 anchor at tick-50 only.** Tick-100 cells are descriptive. Tick-200 cells are the verdict driver via the C arm.
- **Locked phrase discipline** verbatim where verdicts fire. Layout names backticked. The priority-4 / -5 / -6 phrases all explicitly reference v0.53c's `WIDENED_BELOW_REACHABILITY_THRESHOLD_AT_TICK_200` verdict by name. The priority-2 phrase references v0.48 / v0.53 / v0.53b / v0.53c collectively.
- **No `geometry-fundamental` claims under priority 5.** The locked phrase explicitly bounds the verdict to `ambient_influx_rate = 2.0 under V0_25 × widened_gradient × N_TICKS=200` and names v0.53e as the open-frame follow-up. Cautious framing per CLAUDE.md.
- **Determinism north star** ([[scripts/core_smoke_test.py]]) must continue to pass. v0.53d makes no src/ changes.

## Files this slice will create / modify

- `docs/experiments/fear_hunger_v0.53d.md` (this file; Results section appended after reducer run)
- `scripts/v0_53d_substrate_axis_relaxed_influx_audit.py` (new)
- `tests/test_v0_53d_substrate_axis_relaxed_influx_audit.py` (new, 16 tests)

No `src/` modifications. No prior reducer / audit / test / pre-reg files modified.

## Results

(To be appended after the reducer run.)
