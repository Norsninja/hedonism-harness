# fear_hunger v0.53h — time-horizon extension probe on `widened_gradient` × V0_25 × combined founder-budget envelope at `n_ticks=400`

**Slice:** v0.53h
**Type:** **first-class observational sweep** with 3-arm asymmetric-horizon reducer (no `src/` changes — `n_ticks` is already exposed on `run_chamber()`; the v0.53e `body_config` seam carries forward; no intervention; **time-horizon variation** on the C arm — the first slice in the v0.53d→v0.53h substrate-axis stack to vary `n_ticks` while preserving the v0.53g combined-budget envelope; reuses existing named layouts).
**Predecessors:** v0.46–v0.52b (full predecessor stack), v0.53 (`BRIDGE_PARTIALLY_GENERALIZES`), v0.53b (`WIDENED_BELOW_REACHABILITY_THRESHOLD_AT_TICK_100`), v0.53c (`WIDENED_BELOW_REACHABILITY_THRESHOLD_AT_TICK_200`), v0.53d (`WIDENED_BELOW_REACHABILITY_THRESHOLD_UNDER_RELAXED_INFLUX` — doubled `ambient_influx_rate` was mechanically inert), v0.53e (`RELAXED_OPPOSITE_SIGN_HALT` — `BodyConfig.starting_energy=100` extended survival ~9% at tick-200 but did not lift reachability; methodological lesson logged), v0.53f (`WIDENED_BELOW_REACHABILITY_THRESHOLD_UNDER_BASE_METABOLIC_COST_010` — `BodyConfig.base_metabolic_cost=0.10` extended survival ~16% at tick-200 but did not lift reachability; reachability-gated priority-3 trigger introduced and validated), v0.53g (`WIDENED_BELOW_REACHABILITY_THRESHOLD_UNDER_COMBINED_SE100_BMC010` — combined `BodyConfig(starting_energy=100, base_metabolic_cost=0.10)` extended survival ~87.5% at tick-200 but did not lift reachability; survival-extension and food-reachability decoupled on `widened_gradient`; central finding).
**Question being asked (locked):** Given the v0.53g combined founder-facing budget envelope, does `widened_gradient` reachability remain `0/64` when the simulation horizon is extended from `n_ticks=200` to `n_ticks=400`? Specifically: with `BodyConfig(starting_energy=100.0, base_metabolic_cost=0.10)` held identical to v0.53g C, and `n_ticks` doubled from 200 to 400 on the C arm only, does C reachability cross 0.25 at tick-400?

The v0.53d→v0.53g stack established that no conservative single- or two-knob founder-facing budget envelope tested lifts `widened_gradient` reachability above `0/64` at `n_ticks=200`. v0.53g's central finding — survival-extension and food-reachability are decoupled on `widened_gradient` — leaves four candidate bottlenecks: simulation horizon (founders run out of ticks before traversing the corridor), policy / hazard-avoidance (founders never enter the corridor regardless of budget), geometry (corridor / hazard-band / food placement structurally bars traversal), or unmodeled dynamics. v0.53h tests the first candidate. The v0.53g C arm reached tick-200 with ~87.5% population alive — substantial unused horizon for traversal. If doubling `n_ticks` to 400 lifts C reachability above 0.25, the bottleneck on `widened_gradient` × V0_25 × combined-budget envelope is the simulation horizon; the candidate space narrows to "how long until founders reach food given enough budget". If reachability remains below 0.25 at tick-400, the bottleneck is structural (policy / geometry / unmodeled) — not horizon — and the candidate space for v0.53i+ shifts toward geometry calibration or policy / hazard-avoidance probes.

If C tick-400 reachability ≥ 25% AND tick-400 sub-verdict resolves PRESENT, the v0.53c–v0.53g reachability ceiling on `widened_gradient` × V0_25 × combined-budget envelope is bounded by the `n_ticks=200` simulation horizon — extending the horizon admits the bridge. If reachability ≥ 25% AND sub-verdict ∈ {PARTIAL, NOT_FOUND}, the extended horizon admits measurement but the bridge fails to fully fire. If reachability ≥ 25% AND sub-verdict = OPPOSITE_SIGN_HALT, the reachability-gated priority-3 trigger fires (bridge framework is meaningful at this measurement). If reachability < 25% even at `n_ticks=400`, **the (V0_25 × `widened_gradient` × combined-budget) reachability ceiling is not lifted by doubling the simulation horizon to `n_ticks=400`** — the candidate space for v0.53i+ shifts toward non-horizon, non-budget axes: geometry calibration (corridor width, food placement, hazard-band geometry), policy / hazard-avoidance dynamics, or unmodeled-dynamics probes. v0.53h does not claim "horizon-fundamental"; the verdict scope is bounded to the tested `n_ticks=400` doubling under the v0.53g combined-budget envelope.

## Pre-implementation note (2026-05-09, before any reducer code)

The pre-reg's design was confirmed with the user before drafting:

- **3 arms (asymmetric `n_ticks`).** A_null_V0_25 (tight_gradient, V0_25 substrate, `n_ticks=200`, anchor). B_widened_V0_25 (widened_gradient, V0_25 substrate, `n_ticks=200`; predecessor lock from v0.53c–v0.53g). C_widened_combined_se100_bmc010_n400 (widened_gradient, V0_25 substrate **except** `BodyConfig(starting_energy=100.0, base_metabolic_cost=0.10)`, `n_ticks=400`). Same 64-tuple corpus.
- **Time-horizon variation only.** `n_ticks` doubled from 200 to 400 on C alone. `BodyConfig` on C identical to v0.53g C. All other WorldConfig / ReproductionConfig / ActionConfig parameters held at V0_25 baseline. A and B run to `n_ticks=200` exactly as in v0.53c–v0.53g.
- **Asymmetric horizon, parallel windows.** Four windows pre50 / pre100 / pre200 / pre400. A and B accumulate pre50 / pre100 / pre200 (their loop terminates at tick-200; pre400 is undefined / NaN on these arms). C accumulates all four windows. The verdict gates on C's pre400 panel only; pre50 / pre100 / pre200 on C remain descriptive cross-slice anchors against v0.53e–v0.53g.
- **No `src/` modifications.** `n_ticks` is already a `run_chamber()` parameter (default 200); v0.53e's `body_config: BodyConfig | None = None` seam carries forward unchanged. v0.53h passes `n_ticks=400` for the C arm and `n_ticks=200` for A and B (the existing default). Test #8 pinning is identical to v0.53e / v0.53f / v0.53g.
- **Reachability-gated priority 3 (carries forward from v0.53f / v0.53g).** Priority 3 fires iff C tick-400 sub-verdict = OPPOSITE_SIGN_HALT AND `c_reachability_tick_400 ≥ 0.25`. Under reachability < 0.25, wrong-sign cells logged descriptively in `wrong_sign_cells_under_reachability_below_threshold` section; rollup falls through to priority 5.
- **Tick-400 verdict gating on C; tick-200 descriptive on A/B and predecessor-sanity on C.** C's per-tick observer accumulates through tick-400. A and B accumulate through tick-200 (canonical v0.53c–v0.53g three-window template).
- **Tier-2 categorical anchor on B_widened_V0_25 preserved.** Reachability at tick-200 must equal `0/64` exactly.
- **NEW Tier-3 predecessor-sanity anchor on C tick-200 reachability.** C's body_config and other WorldConfig parameters match v0.53g C exactly; through tick-200 the C arm in v0.53h is byte-identical to v0.53g C under matched RNG. C tick-200 reachability must therefore equal `0/64` exactly. This locks v0.53g's predecessor finding into v0.53h's anchor stack and protects against accidental drift in arm-construction.
- **Pool / ecology preserved.** A, B, and C all retain V0_25 baseline `ambient_influx_rate=1.0`, `energy_pool_initial=1500.0`, `food_respawn_cooldown=50`, `child_funding_mode=PARENT_TRANSFER_POOL_GAP`, hazard_damage per (version, hazard) corpus row. Only `body_config` AND `n_ticks` differ on C — `body_config` on the v0.53e seam, `n_ticks` on the existing chamber-driver parameter.
- **Expected behavioral identity between C v0.53h and C v0.53g through tick-200.** Same `body_config`, same WorldConfig, same RNG. C v0.53h tick-200 reachability is mechanically guaranteed to match v0.53g's `0/64`. The empirical question is whether ticks 200..400 admit any food contact.

## Conservation framing — observational, no `src/` changes, asymmetric `n_ticks` on C only

- **No `src/` modifications.** `n_ticks` is already a `run_chamber()` parameter; v0.53e's `body_config` seam carries forward. The five science-core files AND `fear_hunger_chamber.py` all remain byte-identical to their v0.53e-tip / v0.52b-tip values. Test #8 enforces both pinning categories.
- **No modifications to prior reducer or audit scripts.** v0.34's `lineage_replay.py`, ..., v0.53g's reducer remain byte-identical to their merged forms.
- **A_null_V0_25 arm is byte-identical to v0.48–v0.53g A_null path AT TICK-50.** Tier-1 re-anchor enforces this within 1e-3.
- **B_widened_V0_25 arm is byte-identical to v0.53–v0.53g's B_widened arm at every tick 0..200.** Tier-2 categorical anchor enforces `b_widened_v025_reachability_run_share_tick_200 == 0.0`.
- **C_widened_combined_se100_bmc010_n400 arm is byte-identical to v0.53g's C_widened_combined_se100_bmc010 arm at every tick 0..200.** Tier-3 predecessor-sanity anchor enforces `c_reachability_tick_200 == 0.0`. The arms diverge only because v0.53h's C continues the simulation through ticks 201..400.
- **C_widened_combined_se100_bmc010_n400 differs from B_widened_V0_25 by exactly two BodyConfig knobs AND `n_ticks`.** `starting_energy` (60.0 → 100.0), `base_metabolic_cost` (0.25 → 0.10), `n_ticks` (200 → 400). All other BodyConfig fields preserved at default. All other WorldConfig / ReproductionConfig / ActionConfig parameters identical to V0_25 baseline.
- **No intervention at any level on any arm.** No founder body trait modification post-construction, no override patching, no helper RNG, no shuffle, no clamp, no permutation. The combined-knob change is config-time; the horizon change is loop-time on C only.

## Corpus (locked, 64 × 3 arms = 192 runs; asymmetric wall time)

Same shape as v0.53–v0.53g:

| version | seeds | hazards | runs per arm | total runs |
|---|---|---|---|---|
| v0.42 | 41..48 | {0, 8} | 16 | 48 |
| v0.43R | 49..56 | {0, 8} | 16 | 48 |
| v0.44 | 57..64 | {0, 8} | 16 | 48 |
| v0.45 | 65..72 | {0, 8} | 16 | 48 |
| **total** | | | | **192** |

V0_25 substrate identical to v0.53–v0.53g on A and B; C identical to v0.53g C except `n_ticks=400` (vs 200). Wall time estimate ~18–35 minutes total (A and B at ~6–10 min each as v0.53g; C ~6–15 min for the 64 runs at 2× tick count).

## Arms (locked, 3 — asymmetric BodyConfig AND asymmetric `n_ticks`)

### A_null_V0_25

```
ChamberLayout = tight_gradient_layout()
ambient_influx_rate = 1.0  (V0_25 baseline)
energy_pool_initial = 1500.0
food_respawn_cooldown = 50
child_funding_mode = PARENT_TRANSFER_POOL_GAP
hazard_damage = per (version, hazard) corpus row
body_config = None  (default BodyConfig)
n_ticks = 200
FounderSpec(traits_override=None)
```

Byte-identical to v0.48–v0.53g A_null path at every tick 0..200. Used for:
1. **Tier-1 anchor at tick-50** (against v0.48–v0.53g published cells).
2. **Descriptive context at tick-100 and tick-200**.

### B_widened_V0_25

```
ChamberLayout = widened_gradient_layout()
ambient_influx_rate = 1.0  (V0_25 baseline; same as A)
energy_pool_initial = 1500.0
food_respawn_cooldown = 50
child_funding_mode = PARENT_TRANSFER_POOL_GAP
hazard_damage = per (version, hazard) corpus row
body_config = None  (default BodyConfig — same as A)
n_ticks = 200
FounderSpec(traits_override=None)
```

Byte-identical to v0.53–v0.53g's B_widened arm at every tick 0..200.

### C_widened_combined_se100_bmc010_n400

```
ChamberLayout = widened_gradient_layout()
ambient_influx_rate = 1.0  (V0_25 baseline)
energy_pool_initial = 1500.0  (V0_25 baseline)
food_respawn_cooldown = 50  (V0_25 baseline)
child_funding_mode = PARENT_TRANSFER_POOL_GAP  (V0_25 baseline)
hazard_damage = per (version, hazard) corpus row  (V0_25 baseline)
body_config = BodyConfig(starting_energy=100.0, base_metabolic_cost=0.10)
  (identical to v0.53g C body_config)
n_ticks = 400
  (RELAXED — doubled from V0_25 / v0.53c–v0.53g baseline of 200)
FounderSpec(traits_override=None)
```

Differs from v0.53g's C by exactly one knob: `n_ticks` (200 → 400). Differs from B_widened_V0_25 by exactly two BodyConfig knobs AND `n_ticks`. **The primary arm of v0.53h**: the verdict gates on C's tick-400 reachability and tick-400 sub-verdict.

## Labels (locked, two — with four Label B variants on C, three on A/B)

### Label A — `high_sensor_radius_lineage`

Trait-resolved (`int(founder.body.traits.sensor_radius)`); tiebreak `min(lineage_id)`. Identical to v0.48–v0.53g.

### Label B — variants computed in parallel

- **`high_tick50_readiness_fraction_lineage`** — Tier-1 anchor against v0.48–v0.53g (computed on all arms).
- **`high_tick100_readiness_fraction_lineage`** — descriptive (computed on all arms; NOT gating).
- **`high_tick200_readiness_fraction_lineage`** — descriptive (computed on all arms; on A/B this is the predecessor verdict-gating window; on C this is the predecessor-sanity panel — NOT gating in v0.53h).
- **`high_tick400_readiness_fraction_lineage`** — **verdict-gating** (computed on C only; undefined / NaN on A and B because their loops terminate at tick-200).

## Primary observables (locked, 3, computed at four windows on C, three on A/B)

| # | name pattern | windows on A/B | windows on C | expected sign |
|---|---|---|---|:-:|
| 1 | `pre{N}_food_events_count` | N ∈ {50, 100, 200} | N ∈ {50, 100, 200, 400} | + |
| 2 | `pre{N}_food_energy_acquired` | N ∈ {50, 100, 200} | N ∈ {50, 100, 200, 400} | + |
| 3 | `mean_distance_to_nearest_food_cell_tick{N}` | N ∈ {50, 100, 200} | N ∈ {50, 100, 200, 400} | − |

Definitions / aggregation rules / NaN handling: copy-local from v0.48–v0.53g. Pre400 windows on A and B are not computed (out of horizon); descriptive cross-slice anchors at pre50 / pre100 / pre200 are computed on all three arms.

## Effect-size rule (locked, sign-aware, identical to v0.48–v0.53g)

```
per_run_delta_O = label_lineage_value_O − mean(non_label_lineage_values_O)
paired_d_O      = mean(per_run_delta_O) / stdev(per_run_delta_O, ddof=1)
signed_d_O      = paired_d_O × expected_sign
fires_expected  iff signed_d_O ≥ +0.5
fires_wrong     iff signed_d_O ≤ −0.5
```

## Reachability metrics (locked, pre-data)

```
b_widened_v025_reachability_run_share_tick_200 =
    fraction of B_widened_V0_25 runs where at least one founder lineage
    has pre200_food_events_count > 0

c_widened_combined_se100_bmc010_n400_reachability_run_share_tick_200 =
    fraction of C_widened_combined_se100_bmc010_n400 runs where at least one
    founder lineage has pre200_food_events_count > 0
    (PREDECESSOR SANITY ANCHOR — must equal 0.0 exactly per v0.53g)

c_widened_combined_se100_bmc010_n400_reachability_run_share_tick_400 =
    fraction of C_widened_combined_se100_bmc010_n400 runs where at least one
    founder lineage has pre400_food_events_count > 0
    (VERDICT-GATING; threshold 0.25)
```

Domain: 64 runs per arm. Threshold: **`B_REACHABILITY_THRESHOLD = 0.25`** (preserved from v0.53b–v0.53g).

The B_widened_V0_25 metric is the Tier-2 categorical predecessor anchor (must equal `0.0` exactly). The C tick-200 metric is the Tier-3 predecessor-sanity anchor (must equal `0.0` exactly per v0.53g determinism). The C tick-400 metric is the verdict-gating reachability AND the priority-3 reachability gate.

## Population-stability and degenerate-label descriptive metrics (locked, pre-data, per arm × window)

Identical structure to v0.53c–v0.53g; extended for C with a tick-400 panel. Living-share, above-threshold-share, and degenerate-label descriptors all computed at every window the arm reaches.

## Per-arm sub-verdicts (locked, 4-way each — verdict-gating window differs per arm)

| condition | A_null_V0_25 (tick-50 anchor; tick-100/200 descriptive) | B_widened_V0_25 (tick-200 informational) | C_widened_combined_se100_bmc010_n400 (tick-400 **verdict-gating**) |
|---|---|---|---|
| both labels clear ≥ 2/3 of the three locked cells, with NaN treated as non-firing, 0 wrong-sign | `A_NULL_V025_TICK{50,100,200}_BRIDGE_PRESENT` | `B_WIDENED_V025_TICK200_BRIDGE_PRESENT` | `C_COMBINED_SE100_BMC010_N400_TICK400_BRIDGE_PRESENT` |
| exactly one label clears ≥ 2/3 of the three locked cells, with NaN treated as non-firing, 0 wrong-sign | `A_NULL_V025_TICK{50,100,200}_BRIDGE_PARTIAL` | `B_WIDENED_V025_TICK200_BRIDGE_PARTIAL` | `C_COMBINED_SE100_BMC010_N400_TICK400_BRIDGE_PARTIAL` |
| neither label clears ≥ 2/3 of the three locked cells, with NaN treated as non-firing, 0 wrong-sign | `A_NULL_V025_TICK{50,100,200}_BRIDGE_NOT_FOUND` | `B_WIDENED_V025_TICK200_BRIDGE_NOT_FOUND` | `C_COMBINED_SE100_BMC010_N400_TICK400_BRIDGE_NOT_FOUND` |
| any primary signed_d ≤ −0.5 under either label | `A_NULL_V025_TICK{50,100,200}_OPPOSITE_SIGN_HALT` | `B_WIDENED_V025_TICK200_OPPOSITE_SIGN_HALT` | `C_COMBINED_SE100_BMC010_N400_TICK400_OPPOSITE_SIGN_HALT` |

C's tick-50 / tick-100 / tick-200 sub-verdicts are computed and logged descriptively (cross-slice anchor against v0.53e–v0.53g) but NOT verdict-gating in v0.53h. The verdict gates on the tick-400 panel only.

**Strict NaN-treated-as-non-firing rule preserved.**

## Slice rollup verdicts (locked, 6 outcomes, priority-ordered — PRIORITY 3 IS REACHABILITY-GATED ON C TICK-400)

Priority order (first-matching wins). The non-halt outcomes (priorities 4–6) gate **only on C_widened_combined_se100_bmc010_n400 at tick-400**.

1. `CORPUS_REDERIVE_DRIFT_HALT`
2. `ANCHOR_REPLICATION_HALT` (now includes Tier-3 predecessor sanity on C tick-200 reachability)
3. `RELAXED_OPPOSITE_SIGN_HALT` (**reachability-gated** — fires iff C tick-400 sub-verdict = OPPOSITE_SIGN_HALT AND `c_reachability_tick_400 ≥ 0.25`)
4. `WIDENED_BRIDGE_RESCUED_BY_TIME_HORIZON_400`
5. `WIDENED_BELOW_REACHABILITY_THRESHOLD_AT_TIME_HORIZON_400`
6. `WIDENED_BRIDGE_PARTIALLY_RESCUED_BY_TIME_HORIZON_400`

### Halt conditions

| priority | rollup verdict | trigger | locked phrase (verbatim) |
|---|---|---|---|
| 1 | `CORPUS_REDERIVE_DRIFT_HALT` | A_null_V0_25 arm `a_share_h8` for any of v0.42 / v0.44 / v0.45 drifts > 1e-3 from the published reference | "Halt: A_null_V0_25 re-anchor drifted from the published Results value for {version}; v0.53h's deterministic re-execution of the V0_25 corpus does not reproduce the published metric within 1e-3." |
| 2 | `ANCHOR_REPLICATION_HALT` | (a) A_null_V0_25 tick-50 signed_d for any of the six v0.48–v0.53g cells drifts > 1e-3 from the published value, OR (b) A_null_V0_25 tick-50 sub-verdict ≠ PRESENT, OR (c) `b_widened_v025_reachability_run_share_tick_200` ≠ `0.0`, OR (d) `c_widened_combined_se100_bmc010_n400_reachability_run_share_tick_200` ≠ `0.0` | "Halt: v0.53h's A_null_V0_25 arm does not reproduce v0.48–v0.53g's tick-50 spatial bridge, OR v0.53h's B_widened_V0_25 arm does not reproduce v0.53c–v0.53g's `0/64` reachability lock at tick-200, OR v0.53h's C_widened_combined_se100_bmc010_n400 arm does not reproduce v0.53g's `0/64` reachability lock at tick-200. v0.53h cannot interpret the C tick-400 cells without an established baseline on the V0_25 substrate AND on the predecessor combined-budget envelope." |
| 3 | `RELAXED_OPPOSITE_SIGN_HALT` (**reachability-gated**) | C_widened_combined_se100_bmc010_n400 tick-400 sub-verdict = `C_COMBINED_SE100_BMC010_N400_TICK400_OPPOSITE_SIGN_HALT` (any wrong-sign cell at the tick-400 panel) **AND** `c_widened_combined_se100_bmc010_n400_reachability_run_share_tick_400 ≥ 0.25` | "Halt: a v0.53h C_widened_combined_se100_bmc010_n400 tick-400 spatial / foraging primary fires in the WRONG direction under a gating label, AND C reachability at tick-400 clears the locked 25% threshold (so the bridge framework is meaningful at this measurement). The combined founder-facing budget relaxation (`BodyConfig.starting_energy = 100.0` AND `BodyConfig.base_metabolic_cost = 0.10`) on the `widened_gradient` layout under doubled simulation horizon (`n_ticks = 400`) surfaces a regime where the locked expected signs do not hold under measurable food access. The reachability-gated trigger preserves v0.53e's locked sign discipline while excluding the v0.53e-style measurement-edge case (wrong-sign at reachability=0)." |

### Tier-1 (priority 2.a) re-anchor — A_null_V0_25 tick-50 cells

Identical six cells to v0.48–v0.53g:

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

Locked from v0.53c–v0.53g.

### Tier-3 (priority 2.d) predecessor-sanity anchor — C tick-200 reachability

| anchor | locked value | tolerance |
|---|:-:|---|
| `c_widened_combined_se100_bmc010_n400_reachability_run_share_tick_200` | **0.0** (i.e., `0/64`) | exact (categorical) |

Locked from v0.53g. Through tick-200, v0.53h's C arm is byte-identical to v0.53g's C arm under matched RNG (same `body_config`, same WorldConfig, same `n_ticks` up to that point). Reachability at tick-200 must therefore match v0.53g exactly.

### Outcome conditions (only consulted if no halt fires)

| priority | rollup verdict | trigger | locked phrase (verbatim) |
|---|---|---|---|
| 4 | `WIDENED_BRIDGE_RESCUED_BY_TIME_HORIZON_400` | `c_widened_combined_se100_bmc010_n400_reachability_run_share_tick_400 ≥ 0.25` AND C tick-400 sub-verdict = `C_COMBINED_SE100_BMC010_N400_TICK400_BRIDGE_PRESENT` | "On the modern A_null corpus with the V0_25 substrate held constant except for the combined founder-facing budget relaxation `BodyConfig(starting_energy=100.0, base_metabolic_cost=0.10)` on `widened_gradient` AND the simulation horizon doubled from `n_ticks=200` to `n_ticks=400` on the C arm only, the v0.48 sensor_radius spatial / foraging bridge fires PRESENT under the locked +0.5 paired_d threshold at tick-400. The geometry/substrate cell that v0.53c locked as `WIDENED_BELOW_REACHABILITY_THRESHOLD_AT_TICK_200`, v0.53d locked as `WIDENED_BELOW_REACHABILITY_THRESHOLD_UNDER_RELAXED_INFLUX`, v0.53e locked as `RELAXED_OPPOSITE_SIGN_HALT`, v0.53f locked as `WIDENED_BELOW_REACHABILITY_THRESHOLD_UNDER_BASE_METABOLIC_COST_010`, and v0.53g locked as `WIDENED_BELOW_REACHABILITY_THRESHOLD_UNDER_COMBINED_SE100_BMC010` admits a measurable bridge under the doubled simulation horizon: B_widened_V0_25 reachability remains `0/64` at tick-200 (predecessor lock holds), C reachability at tick-200 remains `0/64` (v0.53g predecessor-sanity lock holds), C reachability at tick-400 clears the locked 25% threshold, and ≥ 2/3 spatial / foraging primaries fire PRESENT under both gating labels at the tick-400 panel. Doubling `n_ticks` from 200 to 400 lifts the reachability ceiling on the v0.53g combined-budget envelope. The (V0_25 × `widened_gradient` × combined-budget) cell is bounded by the `n_ticks=200` simulation horizon under the tested envelope; doubling the horizon to `n_ticks=400` admits the bridge: `WIDENED_BRIDGE_RESCUED_BY_TIME_HORIZON_400`." |
| 5 | `WIDENED_BELOW_REACHABILITY_THRESHOLD_AT_TIME_HORIZON_400` | `c_widened_combined_se100_bmc010_n400_reachability_run_share_tick_400 < 0.25` | "On the modern A_null corpus with the V0_25 substrate held constant except for the combined founder-facing budget relaxation `BodyConfig(starting_energy=100.0, base_metabolic_cost=0.10)` on `widened_gradient` AND the simulation horizon doubled from `n_ticks=200` to `n_ticks=400` on the C arm only, fewer than 25% of C runs have any founder lineage with pre400 food events. C's reachability is below the locked 25% threshold at tick-400; the geometry/substrate cell that v0.53c locked as `WIDENED_BELOW_REACHABILITY_THRESHOLD_AT_TICK_200`, v0.53d locked as `WIDENED_BELOW_REACHABILITY_THRESHOLD_UNDER_RELAXED_INFLUX`, v0.53e locked as `RELAXED_OPPOSITE_SIGN_HALT`, v0.53f locked as `WIDENED_BELOW_REACHABILITY_THRESHOLD_UNDER_BASE_METABOLIC_COST_010`, and v0.53g locked as `WIDENED_BELOW_REACHABILITY_THRESHOLD_UNDER_COMBINED_SE100_BMC010` remains below the reachability threshold under the doubled simulation horizon. The bridge is not rescued by extending the horizon to `n_ticks=400` under V0_25 × `widened_gradient` × combined-budget envelope; the (V0_25 × `widened_gradient` × combined-budget) reachability ceiling is not lifted by doubling the simulation horizon to `n_ticks=400`. v0.53i (or later) candidates shift toward axes not yet tested in the v0.53d→v0.53h stack: geometry calibration (corridor width, food placement, hazard-band geometry), policy / hazard-avoidance dynamics, or unmodeled-dynamics probes: `WIDENED_BELOW_REACHABILITY_THRESHOLD_AT_TIME_HORIZON_400`." |
| 6 | `WIDENED_BRIDGE_PARTIALLY_RESCUED_BY_TIME_HORIZON_400` | `c_widened_combined_se100_bmc010_n400_reachability_run_share_tick_400 ≥ 0.25` AND C tick-400 sub-verdict ∈ {`C_COMBINED_SE100_BMC010_N400_TICK400_BRIDGE_PARTIAL`, `C_COMBINED_SE100_BMC010_N400_TICK400_BRIDGE_NOT_FOUND`} | "On the modern A_null corpus with the V0_25 substrate held constant except for the combined founder-facing budget relaxation `BodyConfig(starting_energy=100.0, base_metabolic_cost=0.10)` on `widened_gradient` AND the simulation horizon doubled from `n_ticks=200` to `n_ticks=400` on the C arm only, C's reachability clears the locked 25% threshold at tick-400 but the v0.48 sensor_radius spatial / foraging bridge does not fully fire PRESENT — fewer than 2/3 primaries fire across both gating labels at tick-400 under the strict NaN rule. The geometry/substrate cell that v0.53c locked as `WIDENED_BELOW_REACHABILITY_THRESHOLD_AT_TICK_200`, v0.53d locked as `WIDENED_BELOW_REACHABILITY_THRESHOLD_UNDER_RELAXED_INFLUX`, v0.53e locked as `RELAXED_OPPOSITE_SIGN_HALT`, v0.53f locked as `WIDENED_BELOW_REACHABILITY_THRESHOLD_UNDER_BASE_METABOLIC_COST_010`, and v0.53g locked as `WIDENED_BELOW_REACHABILITY_THRESHOLD_UNDER_COMBINED_SE100_BMC010` is partially rescued under the doubled simulation horizon: reachability becomes measurable but the bridge does not fully replicate. Layout-specific partial-rescue logged in Results: `WIDENED_BRIDGE_PARTIALLY_RESCUED_BY_TIME_HORIZON_400`." |

The 3 non-halt outcomes form a total partition of (C tick-400 reachability ≥ 0.25, C tick-400 sub-verdict ∈ {PRESENT, PARTIAL, NOT_FOUND, OPPOSITE_SIGN_HALT}) ∪ (C tick-400 reachability < 0.25). Under the reachability-gated priority-3 trigger:
- **C tick-400 reachability ≥ 0.25 AND C tick-400 sub-verdict = OPPOSITE_SIGN_HALT** → priority 3 fires (halt).
- **C tick-400 reachability ≥ 0.25 AND C tick-400 sub-verdict = PRESENT** → priority 4 fires.
- **C tick-400 reachability ≥ 0.25 AND C tick-400 sub-verdict ∈ {PARTIAL, NOT_FOUND}** → priority 6 fires.
- **C tick-400 reachability < 0.25** → priority 5 fires (regardless of C tick-400 sub-verdict, including OPPOSITE_SIGN_HALT — wrong-sign cells logged descriptively but no halt).

Test #16 enforces the partition exhaustively.

## Cautious framing (per CLAUDE.md)

- "**Bridge rescued by doubled simulation horizon**", "**bridge is not rescued by `n_ticks=400` under V0_25 × widened_gradient × combined-budget envelope**", "**reachability ceiling is not lifted by doubling the simulation horizon to `n_ticks=400`**" — NOT "**proves**", "**causes**", "**rules out**", "**horizon-fundamental**", or "**geometry-fundamental**".
- "**Tested doubled horizon**" specifically means `n_ticks=400` under `BodyConfig(starting_energy=100.0, base_metabolic_cost=0.10)`. v0.53h does NOT establish behavior at intermediate horizons (e.g., `n_ticks=300`), longer horizons (`n_ticks ≥ 600`), or asymmetric body_config + horizon variations; those require separate slices.
- v0.53h explicitly does not establish: cross-layout generalization beyond the three v0.53 layouts, mechanism for any rescue or non-rescue outcome, generalization to non-V0_25 substrates beyond the founder-facing budget axes, behavior at `n_ticks > 400`, causal contribution per layout (Reading-A causal-generalization slice remains the deferred candidate).

## What v0.53h cannot establish (logged here pre-data, not retrofittable)

- ✗ **"`widened_gradient` is geometry-fundamental"** if priority 5 fires. v0.53h tests V0_25 substrate × `BodyConfig(starting_energy=100.0, base_metabolic_cost=0.10)` × `n_ticks=400` only. Stronger budget envelopes, longer horizons, non-budget axes (geometry / policy), or unmodeled-dynamics probes remain untested. v0.53i (or later) candidates open.
- ✗ **"Simulation horizon is exhausted as an axis."** v0.53h tests one horizon doubling. Larger doublings (`n_ticks=800`, `n_ticks=1600`) or interactions between horizon and other axes remain untested.
- ✗ **A revised v0.53–v0.53g verdict.** All seven stand as historical contracts.
- ✗ **Mechanism behind any rescue or non-rescue outcome.** Population dynamics under V0_25 × `widened_gradient` × `BodyConfig(se100, bmc010)` × `n_ticks=400` are descriptively logged through ticks 0..400; no mechanism is formally established.
- ✗ **Generalization beyond the tested arms.** Verdict scope is bounded to (`tight_gradient` × V0_25 at `n_ticks=200`, `widened_gradient` × V0_25 at `n_ticks=200`, `widened_gradient` × V0_25 with `BodyConfig(se100, bmc010)` at `n_ticks=400`).

## Open framing (NOT in v0.53h primary)

- **If priority 4 fires** (doubled horizon rescues the bridge): the natural follow-ups become Reading-A causal-generalization on `widened_gradient` under the combined envelope at `n_ticks=400`, dose-response within the horizon axis (`n_ticks ∈ {300, 400, 600, 800}`), and substrate cross-corpus calibration at the extended horizon.
- **If priority 5 fires** (doubled horizon insufficient): the candidate space shifts away from horizon and budget axes:
  - **v0.53i candidate — geometry calibration probe.** Vary corridor width, food placement, or hazard-band placement on `widened_gradient`. May require new layout(s) and possibly src/ change to expose layout parameters. **First geometry knob should probably be food placement / corridor distance, not hazard behavior** (per user pivot guidance).
  - **v0.53j candidate — policy / hazard-avoidance probe.** Vary `hazard_avoidance_weight` or other policy knobs on `widened_gradient` under V0_25 substrate.
  - **v0.53k candidate — longer horizon probe.** Test `n_ticks=800` or `n_ticks=1600` under V0_25 × widened_gradient × combined-budget envelope. Deferred unless v0.53h's tick-400 reachability is suggestively non-zero but below 0.25.
  - **v0.53l candidate — three-knob founder-budget co-variation.** Add `max_energy=200` (or similar) to v0.53g's two-knob envelope; test whether further headroom lifts reachability.
- **v0.53m (or later) — investigate the C_food_ladder Label B degradation trajectory.** Per-tick-window paired_d trajectory probe.
- **v0.53n (or later) — Reading-A causal-generalization slice on layouts admitting the bridge.**
- **v0.54 — joint ablation** (zero-cost AND shuffle).
- **Eventual fresh-stream calibration** on the v0.46–v0.53h conclusion stack.

## Re-anchor (locked — Tier-1 and corpus only at tick-50)

| version | published `a_share_h8` |
|---|---|
| v0.42 | 0.652 |
| v0.43R | NOT PUBLISHED (informational-only) |
| v0.44 | 0.878 |
| v0.45 | 0.818 |

## Outputs (locked)

```
runs/v0.53h-time-horizon-extension-n400/per_run_per_lineage_v053h.csv
  columns: arm, layout_name, body_starting_energy, body_base_metabolic_cost, n_ticks,
           version, seed, hazard, run_id, lineage_id,
           founder_sensor_radius, founder_reproduction_drive, founder_metabolic_rate,
           pre50_food_events_count, pre50_food_energy_acquired,
           pre100_food_events_count, pre100_food_energy_acquired,
           pre200_food_events_count, pre200_food_energy_acquired,
           pre400_food_events_count, pre400_food_energy_acquired,        # C only; NaN on A/B
           mean_distance_to_nearest_food_cell_tick50,
           mean_distance_to_nearest_food_cell_tick100,
           mean_distance_to_nearest_food_cell_tick200,
           mean_distance_to_nearest_food_cell_tick400,                   # C only; NaN on A/B
           tick50_living_count, tick50_above_threshold_count, tick50_above_threshold_fraction,
           tick100_living_count, tick100_above_threshold_count, tick100_above_threshold_fraction,
           tick200_living_count, tick200_above_threshold_count, tick200_above_threshold_fraction,
           tick400_living_count, tick400_above_threshold_count, tick400_above_threshold_fraction,  # C only; NaN on A/B
           b50_count, is_eventual_top_b50_label,
           is_high_sensor_radius_lineage,
           is_high_tick50_readiness_fraction_lineage,
           is_high_tick100_readiness_fraction_lineage,
           is_high_tick200_readiness_fraction_lineage,
           is_high_tick400_readiness_fraction_lineage                   # C only; NaN on A/B

runs/v0.53h-time-horizon-extension-n400/audit_summary.csv
  (includes the wrong_sign_cells_under_reachability_below_threshold section
   carried forward from v0.53f / v0.53g; gates on C tick-400 reachability)

runs/v0.53h-time-horizon-extension-n400/audit_log.txt
```

## Implementation plan (locked)

1. **No `src/` changes.** `n_ticks` is already a `run_chamber()` parameter (default 200). v0.53e's `body_config` seam carries forward. v0.53h passes `n_ticks=400` and `body_config=BodyConfig(starting_energy=100.0, base_metabolic_cost=0.10)` for the C arm; A and B pass the existing default (`n_ticks=200`, `body_config=None`).
2. Fresh script `scripts/v0_53h_time_horizon_extension_n400_audit.py`. CLI: `uv run python scripts/v0_53h_time_horizon_extension_n400_audit.py [--out-dir runs/v0.53h-time-horizon-extension-n400]`.
3. Per (version, seed, hazard) tuple, run **3 arms**. A and B pass `body_config=None, n_ticks=200`; C passes `body_config=BodyConfig(starting_energy=100.0, base_metabolic_cost=0.10), n_ticks=400`.
4. Setup_observer order (matches v0.53c–v0.53g merged implementation): (a) capture v0.53h founder audit table including `body.energy`, `body_config.starting_energy`, `body_config.base_metabolic_cost` at tick 0, AND record `n_ticks` per arm (from chamber-driver kwarg) — verifies BodyConfig knobs propagated correctly AND records the asymmetric-horizon configuration, (b) wire event listeners, (c) read back `model.world.width` and assert layout match per-arm, (d) capture tick-0 snapshot.
5. Per-tick observer accumulates `pre50_*` / `pre100_*` / `pre200_*` rollups in parallel on all arms; `pre400_*` rollups on C only (gated by `n_ticks` reaching that window).
6. Use the relaxed contiguous-prefix tick-records invariant from v0.53b–v0.53g.
7. Aggregate per-lineage primaries at three windows on A/B and four windows on C. Compute Label A and four Label B variants (the tick-400 variant computed only on C; NaN-broadcast on A/B).
8. Compute paired_d per (arm, gating-label, observable, window) cell. Cells where the window is undefined (pre400 on A/B) are recorded as NaN; strict NaN-treated-as-non-firing rule applies.
9. Compute per-arm reachability_run_share at every window the arm reaches (3 windows on A/B; 4 windows on C).
10. Compute per-arm population-stability metrics at every window the arm reaches.
11. **Tier-1 bridge re-anchor** (priority 2.a / 2.b): A_null_V0_25 arm's six tick-50 cells vs v0.48–v0.53g published; halt if drift > 1e-3 OR if A_null_V0_25 tick-50 sub-verdict ≠ PRESENT.
12. **Tier-2 categorical anchor** (priority 2.c): `b_widened_v025_reachability_run_share_tick_200 == 0.0` exactly.
13. **Tier-3 predecessor-sanity anchor** (priority 2.d): `c_widened_combined_se100_bmc010_n400_reachability_run_share_tick_200 == 0.0` exactly.
14. **Corpus re-anchor** (priority 1): A_null_V0_25 arm only; halt if `a_share_h8` for v0.42 / v0.44 / v0.45 drifts > 1e-3.
15. **Reachability-gated relaxed opposite-sign halt** (priority 3, gates on C tick-400): scan all C tick-400 gating-label cells; if any signed_d ≤ −0.5 AND `c_reachability_tick_400 ≥ 0.25` → halt loud. Otherwise: log descriptively in `audit_summary.csv` under `wrong_sign_cells_under_reachability_below_threshold`; do NOT halt. Fall through to priority 4/5/6 evaluation.
16. Compute slice rollup verdict per the locked priority + (C tick-400 reachability, C tick-400 sub-verdict) decision matrix; print + write the locked phrase verbatim.

The reducer is fully self-contained: it reads no `runs/` artifacts. Wall time estimate ~18–35 minutes for 192 runs (asymmetric: 128 runs at `n_ticks=200`, 64 runs at `n_ticks=400`).

## Test list (locked, 16 tests; extends v0.53g's pattern with asymmetric-horizon verification in test #5 and tick-400 panel in test #11)

`tests/test_v0_53h_time_horizon_extension_n400_audit.py`:

1. **`test_paired_d_function_reproduces_hand_computed_signed_d_on_fixture_and_tier1_constants_match_v048_published_values`** *(re-anchor test, two-part)*.
2. **`test_a_null_v025_corpus_a_share_h8_re_anchors_v042_v044_v045`** — drift halt fires if any drift > 1e-3.
3. `test_arm_a_null_v025_uses_tight_gradient_layout_default_body_config_and_n_ticks_200` — chamber driver receives `tight_gradient_layout()`, `body_config=None`, `n_ticks=200`; layout AND horizon invariant assert.
4. `test_arm_b_widened_v025_uses_widened_gradient_layout_default_body_config_and_n_ticks_200` — chamber driver receives `widened_gradient_layout()`, `body_config=None`, `n_ticks=200`; layout AND horizon invariant assert.
5. **`test_arm_c_widened_combined_se100_bmc010_n400_seam_differentiates_b_and_c_two_body_config_knobs_at_tick_0_and_horizon_at_tick_400`** *(cross-arm contrast — verifies BOTH knobs of the `body_config` seam took effect at config-time founder construction AND that C's horizon extension propagated)* — for the same (version, seed, hazard) tuple under matched RNG streams, assert:
   - **B founder body fields at tick-0**: `body.energy == 60.0`, `body_config.starting_energy == 60.0`, `body_config.base_metabolic_cost == 0.25` (V0_25 baseline from default `BodyConfig()` fallback).
   - **B model end-state**: `model.tick_count == 200` after `run_chamber()` returns.
   - **C founder body fields at tick-0**: `body.energy == 100.0`, `body_config.starting_energy == 100.0`, `body_config.base_metabolic_cost == 0.10` (overridden via combined seam).
   - **C model end-state**: `model.tick_count == 400` after `run_chamber()` returns.
   - Both arms use `widened_gradient_layout()`; the configured difference is `body_config` (TWO knobs) AND `n_ticks` (200 vs 400).
   - For C, explicitly assert that no other `BodyConfig` field differs from default AND no other WorldConfig knob differs from V0_25 baseline.
   - Founder body fields are read (not written) via `setup_observer` snapshot at tick-0; `model.tick_count` is read after `run_chamber()` returns.
6. **`test_founder_traits_byte_identical_across_arms_for_same_seed`**.
7. **`test_founder_positions_byte_identical_across_arms_for_same_seed`**.
8. **`test_no_src_modifications_compared_to_v0_53e_tip`** *(two-part src/ pinning test, IDENTICAL to v0.53e / v0.53f / v0.53g's test #8)*:
   Part A: SHA-256 of five science-core files match v0.52b-tip values exactly. Failure message verbatim: `"v0.53h is pre-registered to leave the science-core five files byte-identical to v0.52b-tip; update the pre-reg before changing src/core or src/experiments/layouts."`
   Part B: SHA-256 of `src/hedonism_harness/experiments/fear_hunger_chamber.py` matches v0.53e-tip value `62d134c5d82b031a6fd2b7bbdf0412eb8362199c7bf60a59836cfca9134e2b6d`. Failure message verbatim: `"v0.53h is pre-registered to leave the chamber driver byte-identical to its v0.53e-tip hash; update the pre-reg before re-touching the chamber driver."`
9. `test_label_a_high_sensor_radius_lineage_picks_correct_lineage`.
10. **`test_label_b_four_variants_three_tier_tiebreak_at_each_window_with_pre400_c_only`** — tick-50 / tick-100 / tick-200 variants computed on all arms; tick-400 variant computed on C only and NaN-broadcast on A/B.
11. **`test_pre400_window_strictly_extends_pre200_pre100_pre50_windows_on_c_arm`** — synthetic events at ticks 10/30/60/90/130/180/200/230/280/350/380/400; assert pre50/pre100/pre200/pre400 counts 2/4/7/12 on C; assert pre400 is NaN on A and B.
12. **`test_subverdict_present_requires_two_thirds_firing_cells_with_nan_treated_as_non_firing_strict`** — exercises C tick-400 panel with NaN cells (e.g., pre400 cells where lineage extinct before tick-400) treated as non-firing.
13. **`test_priority_3_relaxed_opposite_sign_halt_is_reachability_gated_on_c_tick_400`** *(carries forward from v0.53f / v0.53g — exercises both branches at the tick-400 panel)*:
    - **Branch A**: synthetic C tick-400 sub-verdict = OPPOSITE_SIGN_HALT AND `c_reachability_tick_400 = 0.30` → priority 3 fires; rollup verdict = `RELAXED_OPPOSITE_SIGN_HALT`.
    - **Branch B**: synthetic C tick-400 sub-verdict = OPPOSITE_SIGN_HALT AND `c_reachability_tick_400 = 0.20` → priority 3 does NOT fire; rollup = `WIDENED_BELOW_REACHABILITY_THRESHOLD_AT_TIME_HORIZON_400` (priority 5); wrong-sign cell recorded in `wrong_sign_cells_under_reachability_below_threshold`.
    - **Branch C**: synthetic C tick-400 sub-verdict = PRESENT AND `c_reachability_tick_400 = 0.30` → priority 4 fires.
14. **`test_b_widened_v025_categorical_anchor_at_tick_200_and_c_predecessor_sanity_at_tick_200`** — synthetic B reachability=0.0 AND C tick-200 reachability=0.0 → priority 2 does NOT fire. Synthetic B reachability=1/64 → priority 2 ANCHOR_REPLICATION_HALT fires (Tier-2). Synthetic C tick-200 reachability=1/64 → priority 2 ANCHOR_REPLICATION_HALT fires (Tier-3 predecessor sanity).
15. **`test_c_tick_400_reachability_threshold_partition`** — synthetic C tick-400 reachability 0.20 / 0.30 × {PRESENT, PARTIAL, NOT_FOUND} → priorities 4/5/6 fire correctly.
16. **`test_rollup_locked_phrases_fire_verbatim_and_priority_cascade_partition_total`** — synthetic each priority-3/4/5/6 outcome → assert locked phrase contains diagnostic substring verbatim:
    - Priority 3 (RELAXED_OPPOSITE_SIGN_HALT, reachability-gated on tick-400): `"AND C reachability at tick-400 clears the locked 25% threshold (so the bridge framework is meaningful at this measurement)"` AND `"The reachability-gated trigger preserves v0.53e's locked sign discipline while excluding the v0.53e-style measurement-edge case (wrong-sign at reachability=0)"`.
    - Priority 4 RESCUED: `"Doubling \`n_ticks\` from 200 to 400 lifts the reachability ceiling on the v0.53g combined-budget envelope"` AND `"The (V0_25 × \`widened_gradient\` × combined-budget) cell is bounded by the \`n_ticks=200\` simulation horizon under the tested envelope"` AND `"doubling the horizon to \`n_ticks=400\` admits the bridge"` AND substring references to v0.53c, v0.53d, v0.53e, v0.53f, v0.53g verdict names.
    - Priority 5 BELOW_THRESHOLD: `"The bridge is not rescued by extending the horizon to \`n_ticks=400\` under V0_25 × \`widened_gradient\` × combined-budget envelope"` AND `"the (V0_25 × \`widened_gradient\` × combined-budget) reachability ceiling is not lifted by doubling the simulation horizon to \`n_ticks=400\`"` AND `"v0.53i (or later) candidates shift toward axes not yet tested in the v0.53d→v0.53h stack"` AND substring references to v0.53c, v0.53d, v0.53e, v0.53f, v0.53g verdict names.
    - Priority 6 PARTIALLY_RESCUED: `"reachability becomes measurable but the bridge does not fully replicate"` AND substring references to v0.53c, v0.53d, v0.53e, v0.53f, v0.53g verdict names.
    Synthesize halt cascade (priorities 1 / 2.a / 2.b / 2.c / 2.d / 3); assert priority order. Exhaustively iterate (C tick-400 reachability ≥ 0.25, C tick-400 sub-verdict ∈ {PRESENT, PARTIAL, NOT_FOUND, OPPOSITE_SIGN_HALT}) ∪ (C tick-400 reachability < 0.25, any sub-verdict); assert unique outcome per cell.

## Watch-outs (for future-Chronus)

- **No `src/` changes.** `n_ticks` is already a `run_chamber()` parameter; v0.53e's seam carries forward unchanged. Test #8 pins both science-core five files (at v0.52b-tip) AND chamber driver (at v0.53e-tip) byte-identically.
- **First asymmetric-horizon slice in the substrate-axis stack.** v0.53d–v0.53g all ran 192 runs at `n_ticks=200`. v0.53h's C arm runs at `n_ticks=400` — 2× tick count, 2× wall time on those 64 runs. Total wall time ~1.5× v0.53g's.
- **Tier-3 predecessor-sanity anchor on C tick-200 reachability is NEW in v0.53h.** It locks v0.53g's `0/64` C result into v0.53h's anchor stack via deterministic re-execution. If the anchor fails, either v0.53h's C arm construction has drifted from v0.53g OR the v0.53e seam has changed — both halt the slice.
- **Reachability-gated priority 3 carries forward from v0.53f / v0.53g, now gating on C tick-400.** Wrong-sign cells under C tick-400 reachability < 0.25 are logged descriptively and do NOT fire a halt.
- **Per-arm sub-verdict structure unchanged (4-way) — but verdict-gating window is tick-400 on C.** A and B's tick-50 / tick-100 / tick-200 sub-verdicts are anchor / descriptive only. C's tick-50 / tick-100 / tick-200 sub-verdicts are descriptive cross-slice anchors against v0.53e–v0.53g; C's tick-400 sub-verdict is the verdict-gating panel.
- **Tier-2 categorical anchor on B_widened_V0_25 is integer-categorical.** Compare to `0.0` exactly.
- **Tier-3 predecessor-sanity anchor on C tick-200 reachability is integer-categorical.** Compare to `0.0` exactly.
- **Pool / ecology preserved.** Only `body_config` AND `n_ticks` differ on C.
- **B and C are expected to diverge from tick-0 onward** through tick-200 (matching v0.53g); from tick-200 to tick-400, B has terminated and C continues. The empirical question is whether ticks 201..400 admit any food contact.
- **Asymmetric pre400 windows on A/B.** Pre400 cells on A and B are NaN by construction (loop terminated at tick-200). The strict NaN-treated-as-non-firing rule means these NaN cells cannot fire any sub-verdict; they are descriptively logged only on C.
- **Locked phrase discipline** verbatim where verdicts fire. The priority-4 / -5 / -6 phrases all explicitly reference v0.53c / v0.53d / v0.53e / v0.53f / v0.53g by name — the predecessor stack is now FIVE slices long.
- **No `horizon-fundamental` claims under priority 5.** The locked phrase explicitly bounds the verdict to the tested `n_ticks=400` doubling under the v0.53g combined-budget envelope and names v0.53i+ candidates (geometry calibration, policy / hazard-avoidance probes, longer horizon, three-knob co-variation) as the open-frame follow-ups.
- **No `geometry-fundamental` claims under priority 5.** The empirical claim is bounded: the tested horizon doubling does not lift reachability. The result does not localize the bottleneck to geometry specifically.
- **Methodological lesson from v0.53e applies** — the reachability-gated priority-3 trigger is now a battle-tested pattern.
- **Determinism north star** ([[scripts/core_smoke_test.py]]) must continue to pass. v0.53h makes no `src/` changes.
- **Survival-extension-vs-reachability decoupling** (v0.53g central finding) carries into v0.53h as the operative interpretive frame — don't relitigate it. If priority 5 fires, the bounded claim is stacked onto v0.53g's (survival-extension dramatic; reachability ceiling persists across budget AND horizon doublings).

## Files this slice will create / modify

- `docs/experiments/fear_hunger_v0.53h.md` (this file; Results section appended after reducer run)
- `scripts/v0_53h_time_horizon_extension_n400_audit.py` (new)
- `tests/test_v0_53h_time_horizon_extension_n400_audit.py` (new, 16 tests)

No `src/` modifications. No prior reducer / audit / test / pre-reg files modified.

## Results

**Status:** reducer executed 2026-05-09 against the 192-run corpus (3 arms × 64 (version, seed, hazard) tuples; A and B at `n_ticks=200`, C at `n_ticks=400`). Wall time well under the 18–35 minute estimate. **Tier-1 bridge re-anchor PASSES at tick-50** (A_null_V0_25 reproduces v0.48–v0.53g's six published signed_d cells within max drift 0.0004 ≪ 1e-3). **Tier-2 categorical anchor PASSES** (B_widened_V0_25 reachability = exactly `0/64` at tick-200, matching v0.53c–v0.53g's lock). **Tier-3 predecessor-sanity anchor PASSES** (C tick-200 reachability = exactly `0/64`, matching v0.53g's lock — the v0.53e seam carries forward correctly under the combined two-knob configuration). Corpus re-anchor (`a_share_h8`) max drift 0.0003 on v0.42. **The reducer landed cleanly on priority 5** — C tick-400 reachability remained `0/64` even with the simulation horizon doubled to `n_ticks=400` under the v0.53g combined-budget envelope. **Reachability-gating did not activate** because C tick-400 had no wrong-sign cells (C tick-400 sub-verdict = `BRIDGE_NOT_FOUND`, not `OPPOSITE_SIGN_HALT`); the framework remains battle-tested via v0.53f only.

### Rollup verdict — `WIDENED_BELOW_REACHABILITY_THRESHOLD_AT_TIME_HORIZON_400` fires

> **Locked phrase fires verbatim:** "On the modern A_null corpus with the V0_25 substrate held constant except for the combined founder-facing budget relaxation `BodyConfig(starting_energy=100.0, base_metabolic_cost=0.10)` on `widened_gradient` AND the simulation horizon doubled from `n_ticks=200` to `n_ticks=400` on the C arm only, fewer than 25% of C runs have any founder lineage with pre400 food events. C's reachability is below the locked 25% threshold at tick-400; the geometry/substrate cell that v0.53c locked as `WIDENED_BELOW_REACHABILITY_THRESHOLD_AT_TICK_200`, v0.53d locked as `WIDENED_BELOW_REACHABILITY_THRESHOLD_UNDER_RELAXED_INFLUX`, v0.53e locked as `RELAXED_OPPOSITE_SIGN_HALT`, v0.53f locked as `WIDENED_BELOW_REACHABILITY_THRESHOLD_UNDER_BASE_METABOLIC_COST_010`, and v0.53g locked as `WIDENED_BELOW_REACHABILITY_THRESHOLD_UNDER_COMBINED_SE100_BMC010` remains below the reachability threshold under the doubled simulation horizon. The bridge is not rescued by extending the horizon to `n_ticks=400` under V0_25 × `widened_gradient` × combined-budget envelope; the (V0_25 × `widened_gradient` × combined-budget) reachability ceiling is not lifted by doubling the simulation horizon to `n_ticks=400`. v0.53i (or later) candidates shift toward axes not yet tested in the v0.53d→v0.53h stack: geometry calibration (corridor width, food placement, hazard-band geometry), policy / hazard-avoidance dynamics, or unmodeled-dynamics probes: `WIDENED_BELOW_REACHABILITY_THRESHOLD_AT_TIME_HORIZON_400`."

**Bounded claim:** Under V0_25 × `widened_gradient` × combined-budget envelope, reachability is not restored by doubling the simulation horizon from `n_ticks=200` to `n_ticks=400`.

Sub-verdicts:

| arm | tick-50 (anchor / descriptive) | tick-100 (descriptive) | tick-200 (descriptive on A; informational on B; predecessor-sanity on C) | tick-400 (verdict-gating; C only) |
|---|---|---|---|---|
| A_null_V0_25 | `A_NULL_V025_TICK50_BRIDGE_PRESENT` | PRESENT | `A_NULL_V025_TICK200_BRIDGE_PRESENT` | n/a (out of horizon) |
| B_widened_V0_25 | NOT_FOUND (informational; categorical anchor at 0/64) | NOT_FOUND | `B_WIDENED_V025_TICK200_BRIDGE_NOT_FOUND` (informational; reachability anchor holds) | n/a (out of horizon) |
| C_widened_combined_se100_bmc010_n400 | NOT_FOUND | NOT_FOUND | `C_COMBINED_SE100_BMC010_N400_TICK200_BRIDGE_NOT_FOUND` (predecessor-sanity from v0.53g; reachability anchor at 0/64) | `C_COMBINED_SE100_BMC010_N400_TICK400_BRIDGE_NOT_FOUND` (drives priority-5 verdict via reachability < 0.25) |

### Central scientific finding — survival horizon ALSO has a ceiling on `widened_gradient` × combined-budget

v0.53g established that survival-extension and food-reachability are decoupled on `widened_gradient` (~87.5% C population alive at tick-200 with 0/64 reachability). v0.53h extends the horizon to `n_ticks=400` and observes that **C population goes fully extinct by tick-400** — from 87.5% alive at tick-200 to 0/64 by tick-400, with reachability still `0/64`.

| slice | C arm knob(s) | C horizon | C tick-200 living_share | C tick-400 living_share | C verdict-window reachability |
|---|---|:-:|:-:|:-:|:-:|
| v0.53e | `starting_energy=100` | `n_ticks=200` | 0.0938 (~9.4%) | n/a | 0/64 (tick-200) |
| v0.53f | `base_metabolic_cost=0.10` | `n_ticks=200` | 0.1562 (~15.6%) | n/a | 0/64 (tick-200) |
| v0.53g | both combined | `n_ticks=200` | 0.8750 (~87.5%) | n/a | 0/64 (tick-200) |
| **v0.53h** | **both combined** | **`n_ticks=400`** | **0.8750 (~87.5%; predecessor-sanity)** | **0.0000 (full extinction)** | **0/64 (tick-400)** |

The combined budget envelope's ~1000-tick raw runway estimate (idealized constant-depletion-rate budget calculation per v0.53g) does NOT translate to ~1000-tick effective survival on `widened_gradient`. Between tick-200 and tick-400, the C population transitions from ~87.5% alive to fully extinct — and over those 200 additional ticks, no founder lineage in any of the 64 runs makes a single food contact. The empirical survival horizon under combined-budget on `widened_gradient` is bounded somewhere between tick-200 and tick-400.

This compounds v0.53g's central finding: not only is reachability decoupled from survival in the early window (tick-200), but **extending the horizon does not extend survival proportionally either** under the tested envelope. Some non-budget depletion sink — plausibly hazard-band damage on attempted traversals, sensor-radius metabolic cost on exploratory movement, reproduction overhead, or unmodeled dynamics — drains the C population well below the raw-budget runway. The descriptive log records the trajectory (87.5% → 0% in 200 ticks); no mechanism is formally established by v0.53h.

### Reachability across all four windows

| window | A_null_V0_25 | B_widened_V0_25 | C_widened_combined_se100_bmc010_n400 | C ≥ 0.25? |
|---|:-:|:-:|:-:|:-:|
| tick-50 | 1.0000 | 0.0000 | 0.0000 | False (descriptive) |
| tick-100 | 1.0000 | 0.0000 | 0.0000 | False (descriptive) |
| tick-200 | 1.0000 | 0.0000 (Tier-2 categorical anchor) | 0.0000 (Tier-3 predecessor-sanity anchor) | False (descriptive on C) |
| tick-400 | n/a (out of horizon) | n/a (out of horizon) | **0.0000** | False (priority 5 fires) |

C reachability is uniformly zero across all four windows. The doubled horizon admits zero additional food contact relative to v0.53g.

### Population-stability trajectory — v0.53d→v0.53h substrate-axis stack

| arm | tick-50 living_share | tick-100 living_share | tick-200 living_share | tick-400 living_share |
|---|:-:|:-:|:-:|:-:|
| A_null_V0_25 | 1.0000 | 1.0000 | 1.0000 | n/a |
| B_widened_V0_25 | 1.0000 | 0.5000 | **0.0000** (full extinction) | n/a |
| C_widened_combined_se100_bmc010_n400 | 1.0000 | 1.0000 | 0.8750 (~87.5%; matches v0.53g) | **0.0000** (full extinction by tick-400) |

C's tick-200 panel reproduces v0.53g exactly (87.5% alive — the deterministic re-execution under matched RNG). Through ticks 201..400, C transitions from ~87.5% population to full extinction with 0/64 food contact.

### Reachability-gating did not activate this slice

Per the v0.53f-introduced reachability-gated priority 3 trigger (carried forward from v0.53g and re-targeted to C tick-400 in v0.53h), priority 3 fires iff (C tick-400 sub-verdict = `OPPOSITE_SIGN_HALT`) AND (`c_reachability_tick_400 ≥ 0.25`). Neither condition held in v0.53h:

- C tick-400 sub-verdict = `C_COMBINED_SE100_BMC010_N400_TICK400_BRIDGE_NOT_FOUND` (no wrong-sign cells; no Label A nor Label B primary signed_d ≤ −0.5 at tick-400).
- C tick-400 reachability = 0.0000 (< 0.25).

The `wrong_sign_cells_under_reachability_below_threshold` section in `audit_summary.csv` is empty (`n_wrong_sign_cells_logged = 0`; `priority3_skipped_under_reachability_below_threshold = False`). The reachability-gating framework remains battle-tested via v0.53f only; v0.53h did not exercise the framework on live data because no wrong-sign cells emerged. (The framework code path is exercised in v0.53h's test #13 with synthetic fixtures.)

### Tier-1 bridge re-anchor — A_null_V0_25 tick-50 reproduces v0.48–v0.53g within 1e-3

| label | observable | published | derived | drift |
|---|---|:-:|:-:|:-:|
| `label_a_sensor_radius` | `pre50_food_events_count` | +1.066 | +1.0656 | 0.0004 |
| `label_a_sensor_radius` | `pre50_food_energy_acquired` | +1.066 | +1.0656 | 0.0004 |
| `label_a_sensor_radius` | `mean_distance_to_nearest_food_cell_tick50` | +1.916 | +1.9159 | 0.0001 |
| `label_b_readiness_fraction_tick50` | `pre50_food_events_count` | +0.916 | +0.9159 | 0.0001 |
| `label_b_readiness_fraction_tick50` | `pre50_food_energy_acquired` | +0.916 | +0.9159 | 0.0001 |
| `label_b_readiness_fraction_tick50` | `mean_distance_to_nearest_food_cell_tick50` | +1.179 | +1.1786 | 0.0004 |

Max drift 0.0004 (≤ 1e-3). All cells PASS.

### Tier-2 categorical anchor — B_widened_V0_25 reachability_run_share at tick-200

| anchor | locked value | derived | passes |
|---|:-:|:-:|:-:|
| `b_widened_v025_reachability_run_share_tick_200` | **0.0** (0/64) | 0.0000 (0/64) | True (categorical match) |

v0.53c–v0.53g's locked `0/64` reachability anchor holds.

### Tier-3 predecessor-sanity anchor — C tick-200 reachability_run_share

| anchor | locked value | derived | passes |
|---|:-:|:-:|:-:|
| `c_widened_combined_se100_bmc010_n400_reachability_run_share_tick_200` | **0.0** (0/64) | 0.0000 (0/64) | True (categorical match; matches v0.53g exactly under deterministic re-execution) |

v0.53g's locked `0/64` reachability anchor holds under v0.53h's re-execution. The v0.53e seam carries forward correctly under the combined two-knob configuration; through tick-200 v0.53h's C is byte-equivalent to v0.53g's C as expected.

### Corpus re-anchor

A_null_V0_25 arm — all PASS (max drift 0.0003):

| version | derived `a_share_h8` | published | drift |
|---|:-:|:-:|:-:|
| v0.42 | 0.6523 | 0.652 | 0.0003 |
| v0.43R | 0.6743 | — (informational) | — |
| v0.44 | 0.8781 | 0.878 | 0.0001 |
| v0.45 | 0.8182 | 0.818 | 0.0002 |

### What v0.53h can safely claim

- ✓ **A_null_V0_25 tick-50 anchor PASSES** within 0.0004 of v0.48–v0.53g. Reducer machinery (paired_d formula, asymmetric four-window observer on C / three-window on A/B, four Label B variants with C-only tick-400 variant, BodyConfig override + asymmetric n_ticks path, reachability-gated priority-3 trigger gating on C tick-400) is correct.
- ✓ **B_widened_V0_25 categorical Tier-2 anchor PASSES exactly** (0/64 at tick-200). Predecessor lock holds.
- ✓ **C_widened_combined_se100_bmc010_n400 categorical Tier-3 predecessor-sanity anchor PASSES exactly** (0/64 at tick-200). v0.53g's lock holds; the v0.53e seam carries forward correctly under combined two-knob × asymmetric horizon configuration.
- ✓ **The asymmetric `n_ticks` path is fully functional.** B's `_RunCapture.final_tick_count == 200`; C's `_RunCapture.final_tick_count == 400` (verified by test #5 on the v0.42/seed=41/h=0 fixture). The pre400 panel on C accumulates correctly; the pre400 panel on A and B is NaN-broadcast as designed.
- ✓ **Doubling `n_ticks` from 200 to 400 does NOT restore food reachability on `widened_gradient` × V0_25 × combined-budget envelope.** C tick-400 reachability_run_share is exactly `0.0000`. No founder lineage in any of the 64 C runs produces a single `AteFood` event in the extended horizon.
- ✓ **C population goes fully extinct by tick-400** under combined-budget × `widened_gradient`. From 87.5% alive at tick-200 (matching v0.53g) to 0/64 by tick-400. The empirical survival horizon under the tested envelope is bounded somewhere between tick-200 and tick-400 — well below the ~1000-tick raw-budget runway estimate.
- ✓ **Survival horizon also has a ceiling** under combined-budget × `widened_gradient`. v0.53g's "they survive without reaching food" finding extends to: "they survive without reaching food, then go extinct anyway by tick-400 — and the doubled horizon admits no additional food contact during the survival-tail-off window."
- ✓ **Under V0_25 × `widened_gradient` × combined-budget envelope, reachability is not restored by doubling the simulation horizon to `n_ticks=400`.**
- ✓ **The reachability-gated priority-3 framework continues to behave correctly** (no wrong-sign cells emerged on live data at the C tick-400 panel; the synthetic test fixture in test #13 still passes).

### What v0.53h cannot claim

- ✗ **"`widened_gradient` is geometry-fundamental"** under priority 5. v0.53h tested one horizon doubling (`n_ticks=400`) under one combined-knob envelope. Stronger budget envelopes, longer horizons (`n_ticks ≥ 800`), or non-budget axes (geometry / policy) remain untested.
- ✗ **"Horizon is exhausted as an axis."** v0.53h tests one horizon doubling. Whether `n_ticks=800` or `n_ticks=1600` would behave differently is empirically untested. The bounded claim is: doubling to `n_ticks=400` does not lift reachability on the v0.53g envelope.
- ✗ **"Survival horizon is universally bounded by tick-400."** The empirical observation is that C goes extinct between tick-200 and tick-400 under V0_25 × `widened_gradient` × combined-budget envelope. Behavior at other budget envelopes, on other layouts, or under intervention is not established.
- ✗ **A revised v0.53–v0.53g verdict.** All seven predecessor verdicts stand as historical contracts.
- ✗ **Mechanism behind the survival-tail-off-without-food-contact pattern.** Plausible interpretations (not formally established): hazard-band damage on attempted traversals; sensor-radius metabolic cost (0.05 per radius unit) drains energy on exploratory movement beyond the constant-rate idealization; reproduction overhead with no offspring funding return; unmodeled per-tick dynamics. v0.53i+ disambiguation candidates open.
- ✗ **Generalization beyond the tested arms.** Verdict scope is bounded to (`tight_gradient` × V0_25 at `n_ticks=200`, `widened_gradient` × V0_25 at `n_ticks=200`, `widened_gradient` × V0_25 with `BodyConfig(se100, bmc010)` at `n_ticks=400`).

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
| v0.53b | modern A_null | `widened_gradient` NOT_FOUND at tick-100 is reachability-bound | observational (BELOW_REACHABILITY_THRESHOLD_AT_TICK_100) |
| v0.53c | modern A_null | `widened_gradient` reachability = 0/64 at every window 50/100/200 under V0_25 | observational (BELOW_REACHABILITY_THRESHOLD_AT_TICK_200) |
| v0.53d | modern A_null | doubling `ambient_influx_rate` is mechanically inert under no-food-contact extinction | observational (BELOW_REACHABILITY_THRESHOLD_UNDER_RELAXED_INFLUX) |
| v0.53e | modern A_null | `BodyConfig.starting_energy=100` extends survival ~9% but does NOT lift reachability; locked-sign halt fired on measurement-edge wrong-sign cell at n=6 | observational (RELAXED_OPPOSITE_SIGN_HALT) |
| v0.53f | modern A_null | `BodyConfig.base_metabolic_cost=0.10` extends survival ~16% but does NOT lift reachability; reachability-gated priority-3 trigger validated on the v0.53e-style edge case | observational (BELOW_REACHABILITY_THRESHOLD_UNDER_BASE_METABOLIC_COST_010) |
| v0.53g | modern A_null | combined `BodyConfig(starting_energy=100, base_metabolic_cost=0.10)` extends survival ~87.5% (~9× v0.53e, ~5.6× v0.53f) at tick-200 but does NOT lift reachability above 0/64; survival-extension and food-reachability are decoupled on `widened_gradient`; under V0_25 × `widened_gradient` × N_TICKS=200, reachability is not restored by the tested conservative single- or two-knob founder-facing budget relaxations | observational (BELOW_REACHABILITY_THRESHOLD_UNDER_COMBINED_SE100_BMC010; central finding: survival-extension ⊥ reachability) |
| v0.53h | modern A_null | doubling `n_ticks` from 200 to 400 under v0.53g's combined-budget envelope does NOT lift reachability above 0/64; C population transitions from ~87.5% alive at tick-200 to fully extinct by tick-400 with no food contact in the extended horizon; survival horizon ALSO has a ceiling well below the ~1000-tick raw-budget runway estimate; under V0_25 × `widened_gradient` × combined-budget envelope, reachability is not restored by doubling the simulation horizon to `n_ticks=400` | observational (BELOW_REACHABILITY_THRESHOLD_AT_TIME_HORIZON_400; central finding: survival horizon also has a ceiling on `widened_gradient` × combined-budget) |

The v0.46→v0.53h stack now reads: ... → v0.53e/f individually extended survival ~9-16% but did not lift reachability → v0.53g's combined two-knob relaxation extended survival to ~87.5% alive at tick-200 with 0/64 reachability → **v0.53h's horizon doubling on the v0.53g envelope produced 0/64 reachability across all four windows AND drove C to full extinction by tick-400 (from 87.5% at tick-200). The candidate space for v0.53i+ shifts toward axes not yet tested in the v0.53d→v0.53h stack.**

### Next-step candidates (open)

The horizon-extension result is strong enough to confirm the user's pivot away from horizon and budget axes. The natural next step is to disambiguate the bottleneck along non-horizon, non-budget axes — and to investigate the survival-tail-off-without-food-contact pattern surfaced by v0.53h:

- **v0.53i — geometry calibration probe.** Recommended next slice per user pivot guidance. First geometry knob should probably be food placement / corridor distance, not hazard behavior. The question would be: can `widened_gradient` become measurable if food is reachable at all under the combined-budget envelope at `n_ticks=200`? May require new layout(s) and possibly a `src/` change to expose layout parameters.
- **v0.53j (or later) — policy / hazard-avoidance probe.** Vary `hazard_avoidance_weight` or other policy knobs on `widened_gradient` under V0_25 substrate. The survival-tail-off-without-food-contact pattern is consistent with founders never entering the corridor regardless of budget, which a policy probe would test.
- **v0.53k (or later) — finer-grain population trajectory probe.** Insert intermediate observer windows (e.g., tick-250/300/350) on the v0.53h C arm to localize where the 87.5% → 0% extinction transition occurs. Would be a pure-reducer slice if the seam already exposes per-tick observers; may require minor src/ wiring otherwise.
- **v0.53l (or later) — longer horizon probe.** Test `n_ticks=800` or `n_ticks=1600`. Deferred unless v0.53k localizes the extinction transition close to `n_ticks=400` (suggesting horizon could matter at higher doses).
- **v0.53m (or later) — three-knob founder-budget co-variation.** Add `max_energy=200` (or similar) to v0.53g's two-knob envelope. Deferred per the v0.53g pivot.
- **v0.53n (or later) — investigate the C_food_ladder Label B degradation trajectory.** Per-tick-window paired_d trajectory probe.
- **v0.53o (or later) — Reading-A causal-generalization slice on layouts admitting the bridge.**
- **v0.54 — joint ablation** (zero-cost AND shuffle).
- **Eventual fresh-stream calibration** on the v0.46–v0.53h conclusion stack.

User has not locked which slice is next.

### CI gate at v0.53h close

```
uv run ruff check .             ok
uv run ruff format --check .    ok (238 files already formatted)
uv run pytest                   1824 passed, 7 skipped (was 1808; +16 v0.53h)
uv run python scripts/core_smoke_test.py                                ok (determinism north star intact; no src/ changes)
uv run python scripts/v0_53h_time_horizon_extension_n400_audit.py       WIDENED_BELOW_REACHABILITY_THRESHOLD_AT_TIME_HORIZON_400 (priority 5; reachability-gating did not activate — no wrong-sign cells at C tick-400 panel)
```
