# fear_hunger v0.53i — geometry calibration probe on `widened_gradient` × V0_25 × combined founder-budget envelope at `n_ticks=400`: post-hazard food distance reduced by two columns (`FOOD_NEAR2`)

**Slice:** v0.53i
**Type:** **first-class observational sweep** with 3-arm asymmetric-horizon reducer (no `src/` changes — `ChamberLayout` is directly constructible per `src/hedonism_harness/experiments/layouts.py:36-37` (`return ChamberLayout()`); v0.53e's `body_config` seam carries forward; `n_ticks` already exposed; no intervention; **single geometry knob** on the C arm — the first slice in the v0.53d→v0.53i substrate-axis stack to vary chamber geometry; the C layout is a script-local `ChamberLayout` instance constructed inside the v0.53i reducer).
**Predecessors:** v0.46–v0.52b (full predecessor stack), v0.53 (`BRIDGE_PARTIALLY_GENERALIZES`), v0.53b (`WIDENED_BELOW_REACHABILITY_THRESHOLD_AT_TICK_100`), v0.53c (`WIDENED_BELOW_REACHABILITY_THRESHOLD_AT_TICK_200`), v0.53d (`WIDENED_BELOW_REACHABILITY_THRESHOLD_UNDER_RELAXED_INFLUX`), v0.53e (`RELAXED_OPPOSITE_SIGN_HALT`), v0.53f (`WIDENED_BELOW_REACHABILITY_THRESHOLD_UNDER_BASE_METABOLIC_COST_010`), v0.53g (`WIDENED_BELOW_REACHABILITY_THRESHOLD_UNDER_COMBINED_SE100_BMC010` — survival-extension and food-reachability decoupled on `widened_gradient`; central finding), v0.53h (`WIDENED_BELOW_REACHABILITY_THRESHOLD_AT_TIME_HORIZON_400` — doubling `n_ticks` to 400 under the combined envelope did not lift reachability AND C population goes fully extinct by tick-400; survival horizon also has a ceiling; central finding).
**Question being asked (locked):** Does reducing post-hazard food distance restore measurable food access on `widened_gradient` under the combined SE100/BMC010 envelope at `n_ticks=400`? Specifically: with `widened_gradient`'s 2-column post-hazard corridor (`x∈[8,9]`) removed by sliding the food band 2 columns left (`food_x∈[10,14]` → `food_x∈[8,12]`), holding hazard band thickness (3 columns at `x∈[5,7]`), spawn position (`spawn_x=1`), height (6), safe band (`x∈[0,4]`), food width (5 columns), `BodyConfig(starting_energy=100.0, base_metabolic_cost=0.10)`, and `n_ticks=400` constant, does C tick-400 reachability cross 0.25?

The v0.53d→v0.53h stack established that no conservative single- or two-knob founder-facing budget envelope, AND no doubling of the simulation horizon to `n_ticks=400`, lifts `widened_gradient` reachability above `0/64`. v0.53g's central finding (survival-extension and food-reachability decoupled on `widened_gradient`) and v0.53h's central finding (survival horizon ALSO has a ceiling — C population transitions from ~87.5% alive at tick-200 to fully extinct by tick-400 under the combined envelope, with no food contact in the extended horizon) together rule out the simple "they just die before reaching food" explanation for the v0.53d–v0.53h null results. The candidate space narrows to non-budget, non-horizon axes. v0.53i tests the geometry axis.

The chosen geometric intervention is the cleanest minimal perturbation: remove the 2-column post-hazard corridor by moving the food band 2 columns left. This preserves hazard band thickness (3 columns), hazard position (`x∈[5,7]`), spawn position (`spawn_x=1`), safe band (`x∈[0,4]`), food band width (5 columns), and chamber height (6). It varies exactly one thing: post-hazard food distance from `corridor_columns + 1` cells (3) to `1` cell (food immediately follows hazard). It does NOT reduce hazard thickness, does NOT add pre-food, does NOT alter policy, and does NOT add budget. The resulting world width shrinks from 15 to 13 columns. The dose name is `FOOD_NEAR2` (food band moved 2 columns nearer to the hazard).

If C tick-400 reachability ≥ 25% AND tick-400 sub-verdict resolves PRESENT, the v0.53c–v0.53h reachability ceiling on `widened_gradient` × V0_25 × combined-budget envelope is bounded by the post-hazard corridor distance — reducing that distance by two columns is sufficient to restore measurable reachability AND admit a measurable v0.48 sensor_radius spatial / foraging bridge. This does NOT prove "geometry solved" — only that this specific 2-column reduction is sufficient under the tested envelope. If reachability ≥ 25% AND sub-verdict ∈ {PARTIAL, NOT_FOUND}, the geometric intervention admits measurement but the bridge fails to fully fire. If reachability ≥ 25% AND sub-verdict = OPPOSITE_SIGN_HALT, the reachability-gated priority-3 trigger fires (bridge framework is meaningful at this measurement). If reachability < 25%, **the (V0_25 × `widened_gradient` × combined-budget × n_ticks=400) reachability ceiling is not lifted by reducing post-hazard food distance by two columns** — the candidate space for v0.53j+ shifts toward policy / hazard-avoidance dynamics, hazard-band traversal mechanics, or larger geometric perturbations (e.g., further food-near, or reduced hazard thickness). v0.53i does NOT claim "geometry irrelevant" or "corridor removal proves distance was not the problem"; the verdict scope is bounded to the tested 2-column reduction under the v0.53g/h combined-budget × n_ticks=400 envelope.

## Pre-implementation note (2026-05-09, before any reducer code)

The pre-reg's design was confirmed with the user before drafting:

- **3 arms (asymmetric `n_ticks`).** A_null_V0_25 (tight_gradient, V0_25 substrate, `n_ticks=200`, anchor). B_widened_V0_25 (widened_gradient, V0_25 substrate, `n_ticks=200`; predecessor lock from v0.53c–v0.53h). C_widened_food_near2_combined_N400 (script-local widened-modified layout, V0_25 substrate **except** `BodyConfig(starting_energy=100.0, base_metabolic_cost=0.10)`, `n_ticks=400`). Same 64-tuple corpus.
- **Single geometry knob.** Only post-hazard food distance varies. v0.53h's combined-budget × n_ticks=400 configuration carries forward unchanged; the geometric intervention is the lone independent variable on C.
- **Layout constructed script-local — no `src/` change.** `ChamberLayout` is a frozen dataclass exported from `src/hedonism_harness/experiments/fear_hunger_chamber.py` (lines 71-98); `layouts.py:36-37` demonstrates direct construction (`return ChamberLayout()`). The v0.53i reducer constructs a script-local `ChamberLayout(safe_x_min=0, safe_x_max=4, hazard_x_min=5, hazard_x_max=7, food_x_min=8, food_x_max=12, height=6, spawn_x=1)` and passes it to `run_chamber()` via the existing `layout: ChamberLayout | None = None` parameter. Test #8 pinning unchanged from v0.53e/f/g/h.
- **No D arm; no Tier-3 anchor.** v0.53h's combined-budget × widened × n_ticks=400 = `0/64` result is referenced as a logical predecessor in pre-reg prose and locked phrases verbatim, but is NOT re-executed as a fourth arm. The anchor stack reverts to v0.53d/e/f/g shape: Tier-1 (A_null_V0_25 tick-50 six published cells) + Tier-2 (B_widened_V0_25 tick-200 reachability == `0/64`).
- **Reachability-gated priority 3 carries forward, renamed to `GEOMETRY_OPPOSITE_SIGN_HALT`.** Priority 3 fires iff C tick-400 sub-verdict = `OPPOSITE_SIGN_HALT` AND `c_reachability_tick_400 ≥ 0.25`. The rename reflects that v0.53i's intervention is geometric (not a body-config relaxation as in v0.53e/f/g/h), so the halt-name carries the intervention type. Under reachability < 0.25, wrong-sign cells logged descriptively in `wrong_sign_cells_under_reachability_below_threshold` section; rollup falls through to priority 5.
- **Tick-400 verdict gating on C; tick-200 descriptive on A/B; pre50/100/200 on C are descriptive cross-slice anchors against v0.53e–v0.53h.** Same window structure as v0.53h. C accumulates pre50/pre100/pre200/pre400; A and B accumulate pre50/pre100/pre200.
- **Tier-2 categorical anchor on B_widened_V0_25 preserved.** Reachability at tick-200 must equal `0/64` exactly.
- **Pool / ecology preserved.** A, B, and C all retain V0_25 baseline `ambient_influx_rate=1.0`, `energy_pool_initial=1500.0`, `food_respawn_cooldown=50`, `child_funding_mode=PARENT_TRANSFER_POOL_GAP`, hazard_damage per (version, hazard) corpus row. Only `layout`, `body_config`, AND `n_ticks` differ on C — `layout` via the existing `run_chamber()` parameter (script-local `ChamberLayout` instance), `body_config` via the v0.53e seam, `n_ticks` via the existing chamber-driver parameter. No `src/` modifications.
- **Expected behavioral divergence between B and C from tick-0 onward.** Different layouts produce different sensor readings at tick-0 (C's east ray from `spawn_x=1` with `sensor_radius=4` scans `x∈[2..5]`: 3 SAFE, 1 HAZARD; B's same ray scans the same cells under widened baseline; C's perceptual change emerges as agents move east into the corridor). Combined-budget founder dynamics still apply on C as v0.53g/h.

## Conservation framing — observational, no `src/` changes, single geometry knob on C only

- **No `src/` modifications.** `ChamberLayout` is constructed script-local in the v0.53i reducer; `n_ticks` and `body_config` already exposed on `run_chamber()`. The five science-core files AND `fear_hunger_chamber.py` AND `layouts.py` all remain byte-identical to their v0.52b-tip / v0.53e-tip values. Test #8 enforces both pinning categories (and continues to assert `layouts.py` unchanged at `d4521cb5...` since the C layout is NOT added to `layouts.py`).
- **No modifications to prior reducer or audit scripts.** v0.34's `lineage_replay.py`, ..., v0.53h's reducer remain byte-identical to their merged forms.
- **A_null_V0_25 arm is byte-identical to v0.48–v0.53h A_null path AT TICK-50.** Tier-1 re-anchor enforces this within 1e-3.
- **B_widened_V0_25 arm is byte-identical to v0.53–v0.53h's B_widened arm at every tick 0..200.** Tier-2 categorical anchor enforces `b_widened_v025_reachability_run_share_tick_200 == 0.0`.
- **C_widened_food_near2_combined_N400 arm differs from B_widened_V0_25 by exactly the layout (food band moved 2 columns left, corridor removed) AND the v0.53g/h combined body_config AND `n_ticks=400`.** All three differences match v0.53g/h's C_widened_combined_se100_bmc010 / v0.53h's C arm except for the layout substitution.
- **C is NOT byte-identical to v0.53h's C through tick-200.** The layout differs from tick-0 onward; the only category-equality comparison to v0.53h is in spirit (combined-budget × widened-shape × n_ticks=400 envelope). v0.53h's `0/64` reachability is referenced as a logical predecessor in locked phrases; no anchor enforces byte-equality across v0.53h C and v0.53i C.
- **No intervention at any level on any arm.** No founder body trait modification post-construction, no override patching, no helper RNG, no shuffle, no clamp, no permutation. The combined-knob change is config-time; the horizon change is loop-time on C only; the layout change is `run_chamber(layout=…)` time on C only.

## Corpus (locked, 64 × 3 arms = 192 runs; asymmetric wall time)

Same shape as v0.53–v0.53h:

| version | seeds | hazards | runs per arm | total runs |
|---|---|---|---|---|
| v0.42 | 41..48 | {0, 8} | 16 | 48 |
| v0.43R | 49..56 | {0, 8} | 16 | 48 |
| v0.44 | 57..64 | {0, 8} | 16 | 48 |
| v0.45 | 65..72 | {0, 8} | 16 | 48 |
| **total** | | | | **192** |

V0_25 substrate identical to v0.53–v0.53h on A and B; C identical to v0.53h C except for the layout substitution. Wall time estimate ~18–35 minutes total (asymmetric: 128 runs at `n_ticks=200`, 64 runs at `n_ticks=400`).

## Arms (locked, 3 — asymmetric layout AND BodyConfig AND `n_ticks`)

### A_null_V0_25

```
ChamberLayout = tight_gradient_layout()
  (safe x=[0,2], hazard x=[3,4], food x=[5,8], spawn_x=1, height=6, width=9)
ambient_influx_rate = 1.0  (V0_25 baseline)
energy_pool_initial = 1500.0
food_respawn_cooldown = 50
child_funding_mode = PARENT_TRANSFER_POOL_GAP
hazard_damage = per (version, hazard) corpus row
body_config = None  (default BodyConfig)
n_ticks = 200
FounderSpec(traits_override=None)
```

Byte-identical to v0.48–v0.53h A_null path at every tick 0..200. Used for:
1. **Tier-1 anchor at tick-50** (against v0.48–v0.53h published cells).
2. **Descriptive context at tick-100 and tick-200**.

### B_widened_V0_25

```
ChamberLayout = widened_gradient_layout()
  (safe x=[0,4], hazard x=[5,7], corridor x=[8,9], food x=[10,14], spawn_x=1, height=6, width=15)
ambient_influx_rate = 1.0  (V0_25 baseline; same as A)
energy_pool_initial = 1500.0
food_respawn_cooldown = 50
child_funding_mode = PARENT_TRANSFER_POOL_GAP
hazard_damage = per (version, hazard) corpus row
body_config = None  (default BodyConfig — same as A)
n_ticks = 200
FounderSpec(traits_override=None)
```

Byte-identical to v0.53–v0.53h's B_widened arm at every tick 0..200.

### C_widened_food_near2_combined_N400

```
ChamberLayout = ChamberLayout(  # script-local, NOT in layouts.py
    safe_x_min=0, safe_x_max=4,
    hazard_x_min=5, hazard_x_max=7,
    food_x_min=8, food_x_max=12,
    height=6, spawn_x=1,
)
  (safe x=[0,4], hazard x=[5,7], food x=[8,12], spawn_x=1, height=6, width=13)
  (corridor x=[8,9] from widened_gradient_layout REMOVED;
   food band slid 2 columns left; food width preserved at 5 columns;
   hazard band thickness preserved at 3 columns; spawn position unchanged)
ambient_influx_rate = 1.0  (V0_25 baseline)
energy_pool_initial = 1500.0  (V0_25 baseline)
food_respawn_cooldown = 50  (V0_25 baseline)
child_funding_mode = PARENT_TRANSFER_POOL_GAP  (V0_25 baseline)
hazard_damage = per (version, hazard) corpus row  (V0_25 baseline)
body_config = BodyConfig(starting_energy=100.0, base_metabolic_cost=0.10)
  (identical to v0.53g/h C body_config)
n_ticks = 400
  (identical to v0.53h C horizon)
FounderSpec(traits_override=None)
```

Differs from v0.53h's C by exactly one knob: the layout (`widened_gradient_layout()` replaced by script-local `widened_food_near2`). Differs from B_widened_V0_25 by exactly the layout AND two BodyConfig knobs AND `n_ticks`. **The primary arm of v0.53i**: the verdict gates on C's tick-400 reachability and tick-400 sub-verdict.

## Labels (locked, two — with four Label B variants on C, three on A/B)

### Label A — `high_sensor_radius_lineage`

Trait-resolved (`int(founder.body.traits.sensor_radius)`); tiebreak `min(lineage_id)`. Identical to v0.48–v0.53h.

### Label B — variants computed in parallel

- **`high_tick50_readiness_fraction_lineage`** — Tier-1 anchor against v0.48–v0.53h (computed on all arms).
- **`high_tick100_readiness_fraction_lineage`** — descriptive (computed on all arms; NOT gating).
- **`high_tick200_readiness_fraction_lineage`** — descriptive (computed on all arms; NOT gating; on A/B is the predecessor verdict-gating window of v0.53c–v0.53g, on C is descriptive cross-slice anchor against v0.53e–v0.53h).
- **`high_tick400_readiness_fraction_lineage`** — **verdict-gating** (computed on C only; undefined / NaN on A and B because their loops terminate at tick-200).

## Primary observables (locked, 3, computed at four windows on C, three on A/B)

| # | name pattern | windows on A/B | windows on C | expected sign |
|---|---|---|---|:-:|
| 1 | `pre{N}_food_events_count` | N ∈ {50, 100, 200} | N ∈ {50, 100, 200, 400} | + |
| 2 | `pre{N}_food_energy_acquired` | N ∈ {50, 100, 200} | N ∈ {50, 100, 200, 400} | + |
| 3 | `mean_distance_to_nearest_food_cell_tick{N}` | N ∈ {50, 100, 200} | N ∈ {50, 100, 200, 400} | − |

Definitions / aggregation rules / NaN handling: copy-local from v0.48–v0.53h. Pre400 windows on A and B are not computed (out of horizon); descriptive cross-slice anchors at pre50 / pre100 / pre200 are computed on all three arms.

**Note on observable 3 (mean distance to nearest food cell):** the value depends on the layout's food cells. C's distance metric uses `food_x∈[8,12]`; A's uses `food_x∈[5,8]`; B's uses `food_x∈[10,14]`. The signed_d cross-arm comparison is therefore NOT directly cross-arm interpretable; sub-verdict firing is per-arm only.

## Effect-size rule (locked, sign-aware, identical to v0.48–v0.53h)

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

c_widened_food_near2_combined_N400_reachability_run_share_tick_400 =
    fraction of C_widened_food_near2_combined_N400 runs where at least one
    founder lineage has pre400_food_events_count > 0
    (VERDICT-GATING; threshold 0.25)
```

Domain: 64 runs per arm. Threshold: **`B_REACHABILITY_THRESHOLD = 0.25`** (preserved from v0.53b–v0.53h).

The B_widened_V0_25 metric is the Tier-2 categorical predecessor anchor (must equal `0.0` exactly). The C tick-400 metric is the verdict-gating reachability AND the priority-3 reachability gate. C's tick-50/100/200 reachability is computed and logged for descriptive cross-slice context but is NOT verdict-gating in v0.53i.

## Population-stability and degenerate-label descriptive metrics (locked, pre-data, per arm × window)

Identical structure to v0.53c–v0.53h; on C extended for the tick-400 panel. Living-share, above-threshold-share, and degenerate-label descriptors all computed at every window the arm reaches.

## Per-arm sub-verdicts (locked, 4-way each — verdict-gating window is C tick-400 only)

| condition | A_null_V0_25 (tick-50 anchor; tick-100/200 descriptive) | B_widened_V0_25 (tick-200 informational) | C_widened_food_near2_combined_N400 (tick-400 **verdict-gating**) |
|---|---|---|---|
| both labels clear ≥ 2/3 of the three locked cells, with NaN treated as non-firing, 0 wrong-sign | `A_NULL_V025_TICK{50,100,200}_BRIDGE_PRESENT` | `B_WIDENED_V025_TICK200_BRIDGE_PRESENT` | `C_WIDENED_FOOD_NEAR2_TICK400_BRIDGE_PRESENT` |
| exactly one label clears ≥ 2/3 of the three locked cells, with NaN treated as non-firing, 0 wrong-sign | `A_NULL_V025_TICK{50,100,200}_BRIDGE_PARTIAL` | `B_WIDENED_V025_TICK200_BRIDGE_PARTIAL` | `C_WIDENED_FOOD_NEAR2_TICK400_BRIDGE_PARTIAL` |
| neither label clears ≥ 2/3 of the three locked cells, with NaN treated as non-firing, 0 wrong-sign | `A_NULL_V025_TICK{50,100,200}_BRIDGE_NOT_FOUND` | `B_WIDENED_V025_TICK200_BRIDGE_NOT_FOUND` | `C_WIDENED_FOOD_NEAR2_TICK400_BRIDGE_NOT_FOUND` |
| any primary signed_d ≤ −0.5 under either label | `A_NULL_V025_TICK{50,100,200}_OPPOSITE_SIGN_HALT` | `B_WIDENED_V025_TICK200_OPPOSITE_SIGN_HALT` | `C_WIDENED_FOOD_NEAR2_TICK400_OPPOSITE_SIGN_HALT` |

C's tick-50 / tick-100 / tick-200 sub-verdicts are computed and logged descriptively (cross-slice anchor against v0.53e–v0.53h) but NOT verdict-gating in v0.53i. The verdict gates on the tick-400 panel only.

**Strict NaN-treated-as-non-firing rule preserved.**

## Slice rollup verdicts (locked, 6 outcomes, priority-ordered — PRIORITY 3 IS REACHABILITY-GATED ON C TICK-400, RENAMED `GEOMETRY_OPPOSITE_SIGN_HALT`)

Priority order (first-matching wins). The non-halt outcomes (priorities 4–6) gate **only on C_widened_food_near2_combined_N400 at tick-400**.

1. `CORPUS_REDERIVE_DRIFT_HALT`
2. `ANCHOR_REPLICATION_HALT` (Tier-1 A tick-50 + Tier-2 B tick-200 only — NO Tier-3 in v0.53i)
3. `GEOMETRY_OPPOSITE_SIGN_HALT` (**reachability-gated** — fires iff C tick-400 sub-verdict = OPPOSITE_SIGN_HALT AND `c_reachability_tick_400 ≥ 0.25`)
4. `WIDENED_BRIDGE_RESCUED_BY_FOOD_NEAR2`
5. `WIDENED_BELOW_REACHABILITY_THRESHOLD_UNDER_FOOD_NEAR2`
6. `WIDENED_BRIDGE_PARTIALLY_RESCUED_BY_FOOD_NEAR2`

### Halt conditions

| priority | rollup verdict | trigger | locked phrase (verbatim) |
|---|---|---|---|
| 1 | `CORPUS_REDERIVE_DRIFT_HALT` | A_null_V0_25 arm `a_share_h8` for any of v0.42 / v0.44 / v0.45 drifts > 1e-3 from the published reference | "Halt: A_null_V0_25 re-anchor drifted from the published Results value for {version}; v0.53i's deterministic re-execution of the V0_25 corpus does not reproduce the published metric within 1e-3." |
| 2 | `ANCHOR_REPLICATION_HALT` | (a) A_null_V0_25 tick-50 signed_d for any of the six v0.48–v0.53h cells drifts > 1e-3 from the published value, OR (b) A_null_V0_25 tick-50 sub-verdict ≠ PRESENT, OR (c) `b_widened_v025_reachability_run_share_tick_200` ≠ `0.0` | "Halt: v0.53i's A_null_V0_25 arm does not reproduce v0.48–v0.53h's tick-50 spatial bridge, OR v0.53i's B_widened_V0_25 arm does not reproduce v0.53c–v0.53h's `0/64` reachability lock at tick-200. v0.53i cannot interpret the C_widened_food_near2_combined_N400 cells without an established baseline on the V0_25 substrate." |
| 3 | `GEOMETRY_OPPOSITE_SIGN_HALT` (**reachability-gated**) | C_widened_food_near2_combined_N400 tick-400 sub-verdict = `C_WIDENED_FOOD_NEAR2_TICK400_OPPOSITE_SIGN_HALT` (any wrong-sign cell at the tick-400 panel) **AND** `c_widened_food_near2_combined_N400_reachability_run_share_tick_400 ≥ 0.25` | "Halt: a v0.53i C_widened_food_near2_combined_N400 tick-400 spatial / foraging primary fires in the WRONG direction under a gating label, AND C reachability at tick-400 clears the locked 25% threshold (so the bridge framework is meaningful at this measurement). The geometric intervention (post-hazard food distance reduced by two columns; food band moved from `x∈[10,14]` to `x∈[8,12]`) under the v0.53g/h combined founder-facing budget envelope (`BodyConfig.starting_energy = 100.0` AND `BodyConfig.base_metabolic_cost = 0.10`) at `n_ticks = 400` surfaces a regime where the locked expected signs do not hold under measurable food access. The reachability-gated trigger preserves v0.53e's locked sign discipline while excluding the v0.53e-style measurement-edge case (wrong-sign at reachability=0)." |

### Tier-1 (priority 2.a) re-anchor — A_null_V0_25 tick-50 cells

Identical six cells to v0.48–v0.53h:

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

Locked from v0.53c–v0.53h.

### NO Tier-3 anchor

v0.53i does NOT enforce a Tier-3 anchor on C. v0.53h's `0/64` C tick-400 reachability under combined-budget × widened × n_ticks=400 is the logical predecessor for v0.53i's C arm shape (combined-budget × geometry-modified × n_ticks=400) and is referenced in pre-reg prose and locked phrases. v0.53i deliberately does NOT re-execute v0.53h's C arm to enforce byte-equality; the runtime cost is not justified by a sanity-anchor that is satisfied logically by the merged v0.53h Results.

### Outcome conditions (only consulted if no halt fires)

| priority | rollup verdict | trigger | locked phrase (verbatim) |
|---|---|---|---|
| 4 | `WIDENED_BRIDGE_RESCUED_BY_FOOD_NEAR2` | `c_widened_food_near2_combined_N400_reachability_run_share_tick_400 ≥ 0.25` AND C tick-400 sub-verdict = `C_WIDENED_FOOD_NEAR2_TICK400_BRIDGE_PRESENT` | "On the modern A_null corpus with the V0_25 substrate held constant except for the combined founder-facing budget relaxation `BodyConfig(starting_energy=100.0, base_metabolic_cost=0.10)` AND the simulation horizon doubled to `n_ticks=400` AND the post-hazard food distance reduced by two columns (food band moved from `x∈[10,14]` under `widened_gradient` to `x∈[8,12]` under the script-local `widened_food_near2` layout; corridor removed; hazard band, food width, spawn position, safe band, and chamber height preserved), the v0.48 sensor_radius spatial / foraging bridge fires PRESENT under the locked +0.5 paired_d threshold at tick-400. The geometry/substrate cell that v0.53c locked as `WIDENED_BELOW_REACHABILITY_THRESHOLD_AT_TICK_200`, v0.53d locked as `WIDENED_BELOW_REACHABILITY_THRESHOLD_UNDER_RELAXED_INFLUX`, v0.53e locked as `RELAXED_OPPOSITE_SIGN_HALT`, v0.53f locked as `WIDENED_BELOW_REACHABILITY_THRESHOLD_UNDER_BASE_METABOLIC_COST_010`, v0.53g locked as `WIDENED_BELOW_REACHABILITY_THRESHOLD_UNDER_COMBINED_SE100_BMC010`, and v0.53h locked as `WIDENED_BELOW_REACHABILITY_THRESHOLD_AT_TIME_HORIZON_400` admits a measurable bridge under the geometric intervention: B_widened_V0_25 reachability remains `0/64` at tick-200 (predecessor lock holds), C reachability at tick-400 clears the locked 25% threshold, and ≥ 2/3 spatial / foraging primaries fire PRESENT under both gating labels at the tick-400 panel. Reducing post-hazard food distance by two columns is sufficient to restore measurable reachability and bridge expression under the combined-budget envelope at `n_ticks=400` on the V0_25 substrate. The v0.53c–v0.53h reachability ceiling is lifted by reducing post-hazard food distance under the tested envelope; this does NOT prove `geometry solved` — only that this specific 2-column reduction is sufficient under the tested envelope: `WIDENED_BRIDGE_RESCUED_BY_FOOD_NEAR2`." |
| 5 | `WIDENED_BELOW_REACHABILITY_THRESHOLD_UNDER_FOOD_NEAR2` | `c_widened_food_near2_combined_N400_reachability_run_share_tick_400 < 0.25` | "On the modern A_null corpus with the V0_25 substrate held constant except for the combined founder-facing budget relaxation `BodyConfig(starting_energy=100.0, base_metabolic_cost=0.10)` AND the simulation horizon doubled to `n_ticks=400` AND the post-hazard food distance reduced by two columns (food band moved from `x∈[10,14]` under `widened_gradient` to `x∈[8,12]` under the script-local `widened_food_near2` layout; corridor removed; hazard band, food width, spawn position, safe band, and chamber height preserved), fewer than 25% of C runs have any founder lineage with pre400 food events. C's reachability is below the locked 25% threshold at tick-400; the geometry/substrate cell that v0.53c locked as `WIDENED_BELOW_REACHABILITY_THRESHOLD_AT_TICK_200`, v0.53d locked as `WIDENED_BELOW_REACHABILITY_THRESHOLD_UNDER_RELAXED_INFLUX`, v0.53e locked as `RELAXED_OPPOSITE_SIGN_HALT`, v0.53f locked as `WIDENED_BELOW_REACHABILITY_THRESHOLD_UNDER_BASE_METABOLIC_COST_010`, v0.53g locked as `WIDENED_BELOW_REACHABILITY_THRESHOLD_UNDER_COMBINED_SE100_BMC010`, and v0.53h locked as `WIDENED_BELOW_REACHABILITY_THRESHOLD_AT_TIME_HORIZON_400` remains below the reachability threshold under the geometric intervention. The bridge is not rescued by reducing post-hazard food distance by two columns under V0_25 × `widened_gradient`-shape × combined-budget envelope × `n_ticks=400`; the tested 2-column reduction does NOT prove `geometry irrelevant` or `corridor removal proves distance was not the problem` — only that this specific intervention does not lift reachability under the tested envelope. v0.53j (or later) candidates shift toward policy / hazard-avoidance dynamics, hazard-band traversal mechanics, or larger geometric perturbations (e.g., further food-near, reduced hazard thickness, or alternative spawn position): `WIDENED_BELOW_REACHABILITY_THRESHOLD_UNDER_FOOD_NEAR2`." |
| 6 | `WIDENED_BRIDGE_PARTIALLY_RESCUED_BY_FOOD_NEAR2` | `c_widened_food_near2_combined_N400_reachability_run_share_tick_400 ≥ 0.25` AND C tick-400 sub-verdict ∈ {`C_WIDENED_FOOD_NEAR2_TICK400_BRIDGE_PARTIAL`, `C_WIDENED_FOOD_NEAR2_TICK400_BRIDGE_NOT_FOUND`} | "On the modern A_null corpus with the V0_25 substrate held constant except for the combined founder-facing budget relaxation `BodyConfig(starting_energy=100.0, base_metabolic_cost=0.10)` AND the simulation horizon doubled to `n_ticks=400` AND the post-hazard food distance reduced by two columns (food band moved from `x∈[10,14]` under `widened_gradient` to `x∈[8,12]` under the script-local `widened_food_near2` layout), C's reachability clears the locked 25% threshold at tick-400 but the v0.48 sensor_radius spatial / foraging bridge does not fully fire PRESENT — fewer than 2/3 primaries fire across both gating labels at tick-400 under the strict NaN rule. The geometry/substrate cell that v0.53c locked as `WIDENED_BELOW_REACHABILITY_THRESHOLD_AT_TICK_200`, v0.53d locked as `WIDENED_BELOW_REACHABILITY_THRESHOLD_UNDER_RELAXED_INFLUX`, v0.53e locked as `RELAXED_OPPOSITE_SIGN_HALT`, v0.53f locked as `WIDENED_BELOW_REACHABILITY_THRESHOLD_UNDER_BASE_METABOLIC_COST_010`, v0.53g locked as `WIDENED_BELOW_REACHABILITY_THRESHOLD_UNDER_COMBINED_SE100_BMC010`, and v0.53h locked as `WIDENED_BELOW_REACHABILITY_THRESHOLD_AT_TIME_HORIZON_400` is partially rescued under the geometric intervention: reachability becomes measurable but the bridge does not fully replicate. Layout-specific partial-rescue logged in Results: `WIDENED_BRIDGE_PARTIALLY_RESCUED_BY_FOOD_NEAR2`." |

The 3 non-halt outcomes form a total partition of (C tick-400 reachability ≥ 0.25, C tick-400 sub-verdict ∈ {PRESENT, PARTIAL, NOT_FOUND, OPPOSITE_SIGN_HALT}) ∪ (C tick-400 reachability < 0.25). Under the reachability-gated priority-3 trigger:
- **C tick-400 reachability ≥ 0.25 AND C tick-400 sub-verdict = OPPOSITE_SIGN_HALT** → priority 3 fires (halt).
- **C tick-400 reachability ≥ 0.25 AND C tick-400 sub-verdict = PRESENT** → priority 4 fires.
- **C tick-400 reachability ≥ 0.25 AND C tick-400 sub-verdict ∈ {PARTIAL, NOT_FOUND}** → priority 6 fires.
- **C tick-400 reachability < 0.25** → priority 5 fires (regardless of C tick-400 sub-verdict, including OPPOSITE_SIGN_HALT — wrong-sign cells logged descriptively but no halt).

Test #16 enforces the partition exhaustively.

## Cautious framing (per CLAUDE.md)

- "**Reducing post-hazard food distance by two columns is sufficient to restore measurable reachability and bridge expression under the combined-budget envelope at `n_ticks=400` on the V0_25 substrate**" (priority 4) — NOT "geometry solved", NOT "distance is the binding constraint", NOT "policy/hazard-avoidance ruled out".
- "**The bridge is not rescued by reducing post-hazard food distance by two columns under V0_25 × `widened_gradient`-shape × combined-budget envelope × `n_ticks=400`**" (priority 5) — NOT "geometry irrelevant", NOT "corridor removal proves distance was not the problem", NOT "hazard-avoidance is the bottleneck". The empirical claim is bounded: this specific 2-column intervention does not lift reachability under the tested envelope.
- "**Tested intervention**" specifically means `food_x∈[8,12]` (corridor removed; food band moved 2 columns left; hazard band thickness, food width, spawn position, safe band, chamber height all preserved) under `BodyConfig(starting_energy=100.0, base_metabolic_cost=0.10)` at `n_ticks=400`. v0.53i does NOT establish behavior at smaller (`food_x∈[9,13]`, 1-column near) or larger (`food_x∈[6,10]`, 4-column near; or removing hazard thickness; or moving spawn) interventions; those require separate slices.
- v0.53i explicitly does not establish: cross-layout generalization beyond the four named layouts (`tight_gradient`, `widened_gradient`, `widened_food_near2`, plus the un-tested `food_ladder`), mechanism for any rescue or non-rescue outcome, generalization to non-V0_25 substrates beyond the founder-facing budget axes, behavior at non-`n_ticks=400` horizons under the same geometry, causal contribution per layout (Reading-A causal-generalization slice remains the deferred candidate).

## What v0.53i cannot establish (logged here pre-data, not retrofittable)

- ✗ **"`widened_gradient` is geometry-fundamental"** under priority 5. v0.53i tests one geometric intervention (2-column food-near) under one combined-knob envelope at one horizon. Stronger geometric interventions, larger budget envelopes, longer horizons, or non-budget-non-geometry axes (policy / hazard-avoidance) remain untested.
- ✗ **"Distance to food is exhausted as an axis."** v0.53i tests one distance reduction. Whether further reduction (e.g., adjacent food, food at hazard exit) would behave differently is empirically untested. The bounded claim is: this 2-column reduction does or does not lift reachability under the tested envelope.
- ✗ **"Geometry solved"** under priority 4. The bounded claim is that this specific 2-column reduction is sufficient under the tested envelope; whether it generalizes to other geometric perturbations or other envelopes is not established by v0.53i alone.
- ✗ **A revised v0.53–v0.53h verdict.** All eight predecessor verdicts stand as historical contracts.
- ✗ **Mechanism behind any rescue or non-rescue outcome.** Population dynamics under V0_25 × `widened_food_near2` × combined-budget × `n_ticks=400` are descriptively logged through ticks 0..400; no mechanism is formally established.
- ✗ **Generalization beyond the tested arms.** Verdict scope is bounded to (`tight_gradient` × V0_25 at `n_ticks=200`, `widened_gradient` × V0_25 at `n_ticks=200`, `widened_food_near2` × V0_25 with `BodyConfig(se100, bmc010)` at `n_ticks=400`).

## Open framing (NOT in v0.53i primary)

- **If priority 4 fires** (geometric intervention rescues the bridge): the natural follow-ups become Reading-A causal-generalization on `widened_food_near2` under the combined envelope, dose-response within the food-near axis (`food_x∈[9,13]`, `food_x∈[7,11]`, `food_x∈[6,10]`), and substrate cross-corpus calibration on the geometric variant.
- **If priority 5 fires** (geometric intervention insufficient): the candidate space shifts away from food-near distance and toward other axes:
  - **v0.53j candidate — policy / hazard-avoidance probe.** Vary `hazard_avoidance_weight` or other policy knobs on `widened_gradient` (or `widened_food_near2`) under V0_25 × combined-budget × `n_ticks=400`. The leading-suspect candidate per cautious framing.
  - **v0.53k candidate — hazard-band traversal mechanics probe.** Vary hazard_damage dose or hazard-band thickness under V0_25 × widened-shape × combined-budget × `n_ticks=400`.
  - **v0.53l candidate — larger geometric perturbation.** Further food-near (`food_x∈[6,10]`, 4-column near) or reduced hazard thickness (`hazard_x∈[5,6]`, 2-column).
  - **v0.53m candidate — alternative spawn position.** Move spawn closer to hazard (e.g., `spawn_x=3`) under the v0.53h-style envelope to test whether perceptual reach shifts the dynamic.
  - **v0.53n candidate — three-knob founder-budget co-variation.** Add `max_energy=200` (or similar) to v0.53g/h's two-knob envelope. Deferred per the v0.53g pivot.
- **v0.53o (or later) — investigate the C_food_ladder Label B degradation trajectory.** Per-tick-window paired_d trajectory probe.
- **v0.53p (or later) — Reading-A causal-generalization slice on layouts admitting the bridge.**
- **v0.54 — joint ablation** (zero-cost AND shuffle).
- **Eventual fresh-stream calibration** on the v0.46–v0.53i conclusion stack.

## Re-anchor (locked — Tier-1 and corpus only at tick-50)

| version | published `a_share_h8` |
|---|---|
| v0.42 | 0.652 |
| v0.43R | NOT PUBLISHED (informational-only) |
| v0.44 | 0.878 |
| v0.45 | 0.818 |

## Outputs (locked)

```
runs/v0.53i-geometry-food-near2/per_run_per_lineage_v053i.csv
  columns: arm, layout_name,
           safe_x_min, safe_x_max, hazard_x_min, hazard_x_max,
           food_x_min, food_x_max, world_width, spawn_x, height,
           body_starting_energy, body_base_metabolic_cost, n_ticks,
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

runs/v0.53i-geometry-food-near2/audit_summary.csv
  (includes the wrong_sign_cells_under_reachability_below_threshold section
   carried forward from v0.53f/g/h; gates on C tick-400 reachability)

runs/v0.53i-geometry-food-near2/audit_log.txt
```

## Implementation plan (locked)

1. **No `src/` changes.** `ChamberLayout` constructed script-local in the v0.53i reducer; `n_ticks` and `body_config` already exposed on `run_chamber()`. v0.53i passes `layout=<script-local widened_food_near2 ChamberLayout>`, `body_config=BodyConfig(starting_energy=100.0, base_metabolic_cost=0.10)`, `n_ticks=400` for the C arm; A passes `layout=tight_gradient_layout(), body_config=None, n_ticks=200`; B passes `layout=widened_gradient_layout(), body_config=None, n_ticks=200`.
2. Fresh script `scripts/v0_53i_geometry_food_near2_audit.py`. CLI: `uv run python scripts/v0_53i_geometry_food_near2_audit.py [--out-dir runs/v0.53i-geometry-food-near2]`.
3. Define module-level constant `WIDENED_FOOD_NEAR2_LAYOUT = ChamberLayout(safe_x_min=0, safe_x_max=4, hazard_x_min=5, hazard_x_max=7, food_x_min=8, food_x_max=12, height=6, spawn_x=1)`.
4. Per (version, seed, hazard) tuple, run **3 arms**.
5. Setup_observer order (matches v0.53c–v0.53h merged implementation): (a) capture v0.53i founder audit table including `body.energy`, `body_config.starting_energy`, `body_config.base_metabolic_cost`, AND `model.world.width`, `model.world_config.layout` column geometry (read from the `WorldConfig.layout`-equivalent or from the layout passed in via `run_chamber()`'s captured kwargs) at tick 0, AND record `n_ticks` per arm, (b) wire event listeners, (c) read back `model.world.width` and assert layout match per-arm, (d) capture tick-0 snapshot.
6. Per-tick observer accumulates `pre50_*` / `pre100_*` / `pre200_*` rollups in parallel on all arms; `pre400_*` rollups on C only (gated by `n_ticks` reaching that window).
7. Use the relaxed contiguous-prefix tick-records invariant from v0.53b–v0.53h.
8. Aggregate per-lineage primaries at three windows on A/B and four windows on C. Compute Label A and four Label B variants (the tick-400 variant computed only on C; NaN-broadcast on A/B).
9. Compute paired_d per (arm, gating-label, observable, window) cell. Cells where the window is undefined (pre400 on A/B) are recorded as NaN; strict NaN-treated-as-non-firing rule applies.
10. Compute per-arm reachability_run_share at every window the arm reaches (3 windows on A/B; 4 windows on C).
11. Compute per-arm population-stability metrics at every window the arm reaches.
12. **Tier-1 bridge re-anchor** (priority 2.a / 2.b): A_null_V0_25 arm's six tick-50 cells vs v0.48–v0.53h published; halt if drift > 1e-3 OR if A_null_V0_25 tick-50 sub-verdict ≠ PRESENT.
13. **Tier-2 categorical anchor** (priority 2.c): `b_widened_v025_reachability_run_share_tick_200 == 0.0` exactly.
14. **Corpus re-anchor** (priority 1): A_null_V0_25 arm only; halt if `a_share_h8` for v0.42 / v0.44 / v0.45 drifts > 1e-3.
15. **Reachability-gated geometry opposite-sign halt** (priority 3, gates on C tick-400): scan all C tick-400 gating-label cells; if any signed_d ≤ −0.5 AND `c_reachability_tick_400 ≥ 0.25` → halt loud (`GEOMETRY_OPPOSITE_SIGN_HALT`). Otherwise: log descriptively in `audit_summary.csv` under `wrong_sign_cells_under_reachability_below_threshold`; do NOT halt. Fall through to priority 4/5/6 evaluation.
16. Compute slice rollup verdict per the locked priority + (C tick-400 reachability, C tick-400 sub-verdict) decision matrix; print + write the locked phrase verbatim.

The reducer is fully self-contained: it reads no `runs/` artifacts. Wall time estimate ~18–35 minutes for 192 runs.

## Test list (locked, 16 tests; extends v0.53h's pattern with explicit geometry-asserts in test #5 and layout-name in CSV column-presence test)

`tests/test_v0_53i_geometry_food_near2_audit.py`:

1. **`test_paired_d_function_reproduces_hand_computed_signed_d_on_fixture_and_tier1_constants_match_v048_published_values`** *(re-anchor test, two-part)*.
2. **`test_a_null_v025_corpus_a_share_h8_re_anchors_v042_v044_v045`** — drift halt fires if any drift > 1e-3.
3. `test_arm_a_null_v025_uses_tight_gradient_layout_default_body_config_and_n_ticks_200_with_explicit_geometry_asserts` — chamber driver receives `tight_gradient_layout()` (assert `safe_x_min=0, safe_x_max=2, hazard_x_min=3, hazard_x_max=4, food_x_min=5, food_x_max=8, spawn_x=1, height=6, world_width=9`), `body_config=None`, `n_ticks=200`.
4. `test_arm_b_widened_v025_uses_widened_gradient_layout_default_body_config_and_n_ticks_200_with_explicit_geometry_asserts` — chamber driver receives `widened_gradient_layout()` (assert `safe_x_min=0, safe_x_max=4, hazard_x_min=5, hazard_x_max=7, food_x_min=10, food_x_max=14, spawn_x=1, height=6, world_width=15`), `body_config=None`, `n_ticks=200`.
5. **`test_arm_c_widened_food_near2_combined_N400_seam_differentiates_b_and_c_layout_food_x_min_shift_body_config_two_knobs_and_horizon_at_tick_400`** *(cross-arm contrast — verifies the script-local layout, BOTH BodyConfig knobs, AND C's horizon)* — for the same (version, seed, hazard) tuple under matched RNG streams, assert:
   - **A founder body fields at tick-0**: `body.energy == 60.0`, default body_config; AND assert A's layout geometry per test #3.
   - **B founder body fields at tick-0**: `body.energy == 60.0`, `body_config.starting_energy == 60.0`, `body_config.base_metabolic_cost == 0.25`; AND assert B's layout geometry: `food_x_min == 10, food_x_max == 14, hazard_x_min == 5, hazard_x_max == 7, spawn_x == 1, world_width == 15`.
   - **B model end-state**: `_RunCapture.final_tick_count == 200` after `run_chamber()` returns.
   - **C founder body fields at tick-0**: `body.energy == 100.0`, `body_config.starting_energy == 100.0`, `body_config.base_metabolic_cost == 0.10`.
   - **C layout geometry at tick-0**: assert `food_x_min == 8` (NOT 10), `food_x_max == 12` (NOT 14), `hazard_x_min == 5`, `hazard_x_max == 7`, `safe_x_min == 0`, `safe_x_max == 4`, `spawn_x == 1`, `height == 6`, `world_width == 13` (NOT 15).
   - **B vs C layout cross-arm contrast (positive intervention)**: `B.food_x_min == 10` AND `C.food_x_min == 8` (specifically asserts the food band shift, the positive intervention).
   - **B vs C layout cross-arm contrast (preserved invariants)**: `(B.food_x_max - B.food_x_min + 1) == (C.food_x_max - C.food_x_min + 1) == 5` (food width preserved at 5 columns); `B.hazard_x_min == C.hazard_x_min == 5` AND `B.hazard_x_max == C.hazard_x_max == 7` (hazard band preserved); `B.safe_x_min == C.safe_x_min == 0` AND `B.safe_x_max == C.safe_x_max == 4` (safe band preserved); `B.spawn_x == C.spawn_x == 1` (spawn preserved); `B.height == C.height == 6` (height preserved).
   - **B vs C layout cross-arm contrast (secondary)**: `B.food_x_max == 14` AND `C.food_x_max == 12`; `B.world_width == 15` AND `C.world_width == 13` (world width change is the consequence of the food-band shift, asserted as a secondary invariant; the food-band shift and the preserved invariants above are primary).
   - **C model end-state**: `_RunCapture.final_tick_count == 400` after `run_chamber()` returns; strict-extension invariant (when B reaches tick-200, C reaches strictly past tick-200).
6. **`test_founder_traits_byte_identical_across_arms_for_same_seed`**.
7. **`test_founder_positions_byte_identical_across_arms_for_same_seed`** — note: founder positions on C use `spawn_x=1` (same as A and B), so positions ARE byte-identical across arms for the same seed.
8. **`test_no_src_modifications_compared_to_v0_53e_tip`** *(two-part src/ pinning test, IDENTICAL to v0.53e/f/g/h's test #8)*:
   Part A: SHA-256 of five science-core files match v0.52b-tip values exactly. Failure message verbatim: `"v0.53i is pre-registered to leave the science-core five files byte-identical to v0.52b-tip; update the pre-reg before changing src/core or src/experiments/layouts."`
   Part B: SHA-256 of `src/hedonism_harness/experiments/fear_hunger_chamber.py` matches v0.53e-tip value `62d134c5d82b031a6fd2b7bbdf0412eb8362199c7bf60a59836cfca9134e2b6d`. Failure message verbatim: `"v0.53i is pre-registered to leave the chamber driver byte-identical to its v0.53e-tip hash; update the pre-reg before re-touching the chamber driver."`
9. `test_label_a_high_sensor_radius_lineage_picks_correct_lineage`.
10. **`test_label_b_four_variants_three_tier_tiebreak_at_each_window_with_pre400_c_only`** — tick-50/100/200 variants computed on all arms; tick-400 variant computed on C only and NaN-broadcast on A/B.
11. **`test_pre400_window_strictly_extends_pre200_pre100_pre50_windows_on_c_arm`** — synthetic events at ticks 10/30/60/90/130/180/200/230/280/350/380/400; assert pre50/pre100/pre200/pre400 counts 2/4/7/12 on C; assert pre400 NaN on A and B.
12. **`test_subverdict_present_requires_two_thirds_firing_cells_with_nan_treated_as_non_firing_strict`** — exercises C tick-400 panel with NaN cells treated as non-firing.
13. **`test_priority_3_geometry_opposite_sign_halt_is_reachability_gated_on_c_tick_400`** *(carries forward from v0.53f/g/h — exercises both branches at the tick-400 panel; halt name renamed to `GEOMETRY_OPPOSITE_SIGN_HALT`)*:
    - **Branch A**: synthetic C tick-400 sub-verdict = OPPOSITE_SIGN_HALT AND `c_reachability_tick_400 = 0.30` → priority 3 fires; rollup verdict = `GEOMETRY_OPPOSITE_SIGN_HALT`.
    - **Branch B**: synthetic C tick-400 sub-verdict = OPPOSITE_SIGN_HALT AND `c_reachability_tick_400 = 0.20` → priority 3 does NOT fire; rollup = `WIDENED_BELOW_REACHABILITY_THRESHOLD_UNDER_FOOD_NEAR2` (priority 5); wrong-sign cell recorded.
    - **Branch C**: synthetic C tick-400 sub-verdict = PRESENT AND `c_reachability_tick_400 = 0.30` → priority 4 fires.
14. **`test_b_widened_v025_categorical_anchor_at_tick_200_no_tier3_in_v053i`** — synthetic B reachability_tick_200=0.0 → priority 2 does NOT fire on this leg. Synthetic B reachability_tick_200=1/64 → ANCHOR_REPLICATION_HALT fires (Tier-2). Assert NO Tier-3 leg exists in v0.53i (the rollup function does NOT accept a `c_reachability_tick200` parameter; if a future patch adds one, this test halts).
15. **`test_c_tick_400_reachability_threshold_partition`** — synthetic C tick-400 reachability 0.20 / 0.30 × {PRESENT, PARTIAL, NOT_FOUND} → priorities 4/5/6 fire correctly.
16. **`test_rollup_locked_phrases_fire_verbatim_and_priority_cascade_partition_total`** — synthetic each priority-3/4/5/6 outcome → assert locked phrase contains diagnostic substring verbatim:
    - Priority 3 (GEOMETRY_OPPOSITE_SIGN_HALT, reachability-gated on tick-400): `"AND C reachability at tick-400 clears the locked 25% threshold (so the bridge framework is meaningful at this measurement)"` AND `"The reachability-gated trigger preserves v0.53e's locked sign discipline while excluding the v0.53e-style measurement-edge case (wrong-sign at reachability=0)"`.
    - Priority 4 RESCUED: `"Reducing post-hazard food distance by two columns is sufficient to restore measurable reachability and bridge expression under the combined-budget envelope at \`n_ticks=400\` on the V0_25 substrate"` AND `"The v0.53c–v0.53h reachability ceiling is lifted by reducing post-hazard food distance under the tested envelope"` AND `"this does NOT prove \`geometry solved\` — only that this specific 2-column reduction is sufficient under the tested envelope"` AND substring references to v0.53c, v0.53d, v0.53e, v0.53f, v0.53g, v0.53h verdict names.
    - Priority 5 BELOW_THRESHOLD: `"The bridge is not rescued by reducing post-hazard food distance by two columns under V0_25 × \`widened_gradient\`-shape × combined-budget envelope × \`n_ticks=400\`"` AND `"the tested 2-column reduction does NOT prove \`geometry irrelevant\` or \`corridor removal proves distance was not the problem\`"` AND `"v0.53j (or later) candidates shift toward policy / hazard-avoidance dynamics, hazard-band traversal mechanics, or larger geometric perturbations"` AND substring references to v0.53c, v0.53d, v0.53e, v0.53f, v0.53g, v0.53h verdict names.
    - Priority 6 PARTIALLY_RESCUED: `"reachability becomes measurable but the bridge does not fully replicate"` AND substring references to v0.53c, v0.53d, v0.53e, v0.53f, v0.53g, v0.53h verdict names.
    Synthesize halt cascade (priorities 1 / 2.a / 2.b / 2.c / 3); assert priority order. Exhaustively iterate (C tick-400 reachability ≥ 0.25, C tick-400 sub-verdict ∈ {PRESENT, PARTIAL, NOT_FOUND, OPPOSITE_SIGN_HALT}) ∪ (C tick-400 reachability < 0.25, any sub-verdict); assert unique outcome per cell.

## Watch-outs (for future-Chronus)

- **No `src/` changes.** `ChamberLayout` constructed script-local; `n_ticks` and `body_config` already exposed. Test #8 pins both science-core five files (at v0.52b-tip including `layouts.py`) AND chamber driver (at v0.53e-tip) byte-identically.
- **First geometry-axis slice in the substrate-axis stack.** v0.53d–v0.53g varied body_config; v0.53h varied n_ticks; v0.53i varies the layout. The script-local `WIDENED_FOOD_NEAR2_LAYOUT` is NOT added to `layouts.py` (preserves v0.52b-tip pinning); reducer constructs it at module load.
- **No D arm; no Tier-3 anchor.** v0.53h's combined-budget × widened × N400 = 0/64 is referenced as a logical predecessor only. Test #14 explicitly asserts no Tier-3 leg exists in the rollup function.
- **Reachability-gated priority 3 carries forward but renamed `GEOMETRY_OPPOSITE_SIGN_HALT`.** Wrong-sign cells under C tick-400 reachability < 0.25 are logged descriptively and do NOT fire a halt.
- **Per-arm sub-verdict structure unchanged (4-way) — verdict-gating window is C tick-400.** A and B's tick-50 / tick-100 / tick-200 sub-verdicts are anchor / descriptive only. C's tick-50 / tick-100 / tick-200 sub-verdicts are descriptive cross-slice anchors against v0.53e–v0.53h; C's tick-400 sub-verdict is the verdict-gating panel.
- **Tier-2 categorical anchor on B_widened_V0_25 is integer-categorical.** Compare to `0.0` exactly.
- **Pool / ecology preserved.** Only `layout`, `body_config`, AND `n_ticks` differ on C.
- **Founder positions byte-identical across arms** (all arms use `spawn_x=1`).
- **B and C are expected to diverge from tick-0 onward** because C's east ray scans different cells (C: `x∈[2..5]` returns 4 SAFE under widened_food_near2; B: `x∈[2..5]` returns 4 SAFE under widened_gradient — actually the same at tick-0 because both have safe `x∈[0,4]`). Divergence emerges as agents move east into the corridor (C has no corridor; food cells are at `x=8..12`; B has corridor at `x=8..9` and food at `x=10..14`).
- **Asymmetric pre400 windows on A/B.** Pre400 cells on A and B are NaN by construction (loop terminated at tick-200). The strict NaN-treated-as-non-firing rule means these NaN cells cannot fire any sub-verdict; they are descriptively logged only on C.
- **Layout geometry recorded per-row in CSV.** `safe_x_min`, `safe_x_max`, `hazard_x_min`, `hazard_x_max`, `food_x_min`, `food_x_max`, `world_width`, `spawn_x`, `height`. Test #5 reads these to verify the cross-arm contrast.
- **Locked phrase discipline** verbatim where verdicts fire. The priority-4 / -5 / -6 phrases all explicitly reference v0.53c / v0.53d / v0.53e / v0.53f / v0.53g / v0.53h by name — the predecessor stack is now SIX slices long.
- **No `geometry-solved` claims under priority 4.** The locked phrase explicitly bounds the verdict to the tested 2-column reduction under the v0.53g/h combined-budget × `n_ticks=400` envelope.
- **No `geometry-irrelevant` claims, NO `distance was not the problem` claims under priority 5.** The empirical claim is bounded: this specific 2-column intervention does not lift reachability under the tested envelope.
- **Methodological lesson from v0.53e applies** — the reachability-gated priority-3 trigger is now a battle-tested pattern; rename to `GEOMETRY_OPPOSITE_SIGN_HALT` reflects intervention type only.
- **Determinism north star** ([[scripts/core_smoke_test.py]]) must continue to pass. v0.53i makes no `src/` changes.
- **Survival-extension-vs-reachability decoupling AND survival-horizon-also-has-a-ceiling** (v0.53g/h central findings) carry into v0.53i as the operative interpretive frame — don't relitigate them. If priority 5 fires, the bounded claim is stacked: v0.53d–v0.53h's null reachability across budget AND horizon doublings, plus this 2-column geometric intervention's null. The cumulative narrowing points the candidate space toward policy / hazard-avoidance dynamics next.

## Files this slice will create / modify

- `docs/experiments/fear_hunger_v0.53i.md` (this file; Results section appended after reducer run)
- `scripts/v0_53i_geometry_food_near2_audit.py` (new)
- `tests/test_v0_53i_geometry_food_near2_audit.py` (new, 16 tests)

No `src/` modifications. No prior reducer / audit / test / pre-reg files modified. `layouts.py` UNCHANGED (the v0.53i C layout is script-local in the reducer; not added to `ALL_LAYOUTS`).

## Results

**Status:** reducer executed 2026-05-09 against the 192-run corpus (3 arms × 64 (version, seed, hazard) tuples). Wall time well under the 18–35 minute estimate. **Tier-1 bridge re-anchor PASSES at tick-50** (A_null_V0_25 reproduces v0.48–v0.53h's six published signed_d cells within max drift 0.000389 ≪ 1e-3). **Tier-2 categorical anchor PASSES** (B_widened_V0_25 reachability = exactly 0/64 at tick-200, matching v0.53c–v0.53h's lock). Corpus re-anchor (`a_share_h8`) max drift 0.000312 on v0.42. **The reducer landed on priority 4** — C tick-400 reachability = 35/64 (~54.7%) clears the locked 25% threshold, AND C tick-400 sub-verdict = `C_WIDENED_FOOD_NEAR2_TICK400_BRIDGE_PRESENT` (all 6 cells fire PRESENT under both gating labels, 0 wrong-sign). The reachability-gated `GEOMETRY_OPPOSITE_SIGN_HALT` framework code path is exercised by test #13 with synthetic fixtures; on live data no wrong-sign cells emerged at C tick-400.

### Rollup verdict — `WIDENED_BRIDGE_RESCUED_BY_FOOD_NEAR2` fires

> **Locked phrase fires verbatim:** "On the modern A_null corpus with the V0_25 substrate held constant except for the combined founder-facing budget relaxation `BodyConfig(starting_energy=100.0, base_metabolic_cost=0.10)` AND the simulation horizon doubled to `n_ticks=400` AND the post-hazard food distance reduced by two columns (food band moved from `x∈[10,14]` under `widened_gradient` to `x∈[8,12]` under the script-local `widened_food_near2` layout; corridor removed; hazard band, food width, spawn position, safe band, and chamber height preserved), the v0.48 sensor_radius spatial / foraging bridge fires PRESENT under the locked +0.5 paired_d threshold at tick-400. The geometry/substrate cell that v0.53c locked as `WIDENED_BELOW_REACHABILITY_THRESHOLD_AT_TICK_200`, v0.53d locked as `WIDENED_BELOW_REACHABILITY_THRESHOLD_UNDER_RELAXED_INFLUX`, v0.53e locked as `RELAXED_OPPOSITE_SIGN_HALT`, v0.53f locked as `WIDENED_BELOW_REACHABILITY_THRESHOLD_UNDER_BASE_METABOLIC_COST_010`, v0.53g locked as `WIDENED_BELOW_REACHABILITY_THRESHOLD_UNDER_COMBINED_SE100_BMC010`, and v0.53h locked as `WIDENED_BELOW_REACHABILITY_THRESHOLD_AT_TIME_HORIZON_400` admits a measurable bridge under the geometric intervention: B_widened_V0_25 reachability remains `0/64` at tick-200 (predecessor lock holds), C reachability at tick-400 clears the locked 25% threshold, and ≥ 2/3 spatial / foraging primaries fire PRESENT under both gating labels at the tick-400 panel. Reducing post-hazard food distance by two columns is sufficient to restore measurable reachability and bridge expression under the combined-budget envelope at `n_ticks=400` on the V0_25 substrate. The v0.53c–v0.53h reachability ceiling is lifted by reducing post-hazard food distance under the tested envelope; this does NOT prove `geometry solved` — only that this specific 2-column reduction is sufficient under the tested envelope: `WIDENED_BRIDGE_RESCUED_BY_FOOD_NEAR2`."

**Bounded claim:** Under V0_25 × `widened_food_near2` × combined SE100/BMC010 × `n_ticks=400`, the v0.53c–v0.53h reachability ceiling is lifted by reducing post-hazard food distance under the tested envelope.

Sub-verdicts:

| arm | tick-50 | tick-100 | tick-200 | tick-400 (verdict-gating on C) |
|---|---|---|---|---|
| A_null_V0_25 | `A_NULL_V025_TICK50_BRIDGE_PRESENT` (anchor) | PRESENT | PRESENT (descriptive) | n/a |
| B_widened_V0_25 | NOT_FOUND (informational; reachability=0) | NOT_FOUND | NOT_FOUND (Tier-2 anchor on reachability) | n/a |
| C_widened_food_near2_combined_N400 | PARTIAL (descriptive) | PRESENT (descriptive) | PRESENT (descriptive) | **PRESENT** (drives priority-4 verdict) |

### Central scientific finding — geometric intervention rescues both reachability and bridge expression

The 2-column reduction of post-hazard food distance is the **lone slice in the v0.53d→v0.53i substrate-axis stack** where C reachability goes from `0/64` (v0.53d–v0.53h null) to substantially above the locked 25% threshold. Comparative trajectory:

| slice | C arm intervention | C verdict-window | C living_share | C reachability | C verdict-window sub-verdict |
|---|---|:-:|:-:|:-:|---|
| v0.53e | `starting_energy=100` | tick-200 | ~9.4% | 0/64 | OPPOSITE_SIGN_HALT (edge) |
| v0.53f | `base_metabolic_cost=0.10` | tick-200 | ~15.6% | 0/64 | NOT_FOUND |
| v0.53g | combined SE100/BMC010 | tick-200 | ~87.5% | 0/64 | NOT_FOUND |
| v0.53h | combined + `n_ticks=400` | tick-400 | 0% (extinct) | 0/64 | NOT_FOUND |
| **v0.53i** | **combined + `n_ticks=400` + FOOD_NEAR2** | **tick-400** | **~35.9%** | **35/64 (~54.7%)** | **PRESENT** |

The single 2-column geometric intervention lifts both the survival horizon (v0.53h's 0% extinct → v0.53i's ~36% alive at tick-400) AND the reachability ceiling (v0.53d–v0.53h's 0/64 → v0.53i's 35/64). All six tick-400 paired_d cells fire PRESENT under both gating labels:

| label | observable | signed_d | n_runs | fires_expected |
|---|---|:-:|:-:|:-:|
| `label_a_sensor_radius` | `pre400_food_events_count` | **+1.036** | 64 | True |
| `label_a_sensor_radius` | `pre400_food_energy_acquired` | **+1.036** | 64 | True |
| `label_a_sensor_radius` | `mean_distance_to_nearest_food_cell_tick400` | **+1.062** | 64 | True |
| `label_b_readiness_fraction_tick400` | `pre400_food_events_count` | **+5.304** | 23 | True |
| `label_b_readiness_fraction_tick400` | `pre400_food_energy_acquired` | **+5.304** | 23 | True |
| `label_b_readiness_fraction_tick400` | `mean_distance_to_nearest_food_cell_tick400` | **+6.295** | 23 | True |

All 6 cells ≥ +0.5 (firing threshold); 0 wrong-sign cells. Bridge expression is **strongly above threshold** under both labels. Label B paired_d at tick-400 is computed on n_runs=23 (the subset of C runs where the lineage with the highest tick-400 readiness fraction survives to tick-400); Label A on the full n=64.

### Reachability across all four windows on C; three on A/B

| window | A_null_V0_25 | B_widened_V0_25 | C_widened_food_near2_combined_N400 | C ≥ 0.25? |
|---|:-:|:-:|:-:|:-:|
| tick-50 | 1.0000 | 0.0000 | **0.5313 (34/64)** | True (descriptive) |
| tick-100 | 1.0000 | 0.0000 | **0.5469 (35/64)** | True (descriptive) |
| tick-200 | 1.0000 | 0.0000 (Tier-2 categorical anchor) | **0.5469 (35/64)** | True (descriptive) |
| tick-400 | n/a (out of horizon) | n/a (out of horizon) | **0.5469 (35/64)** | **True (priority-4 trigger)** |

C reachability stabilises at 35/64 from tick-100 onward — the bridge fires early, not late. Under v0.53d–v0.53h's null reachability, C reached zero food contact at every window; under v0.53i's geometric intervention, C reaches food contact in 53–55% of runs across all measured windows.

### Population-stability trajectory — substrate-axis stack on C

| arm | tick-50 living_share | tick-100 living_share | tick-200 living_share | tick-400 living_share |
|---|:-:|:-:|:-:|:-:|
| A_null_V0_25 | 1.0000 | 1.0000 | 1.0000 | n/a |
| B_widened_V0_25 | 1.0000 | 0.5000 | **0.0000** (full extinction; predecessor lock) | n/a |
| C_widened_food_near2_combined_N400 | 1.0000 | 1.0000 | **0.9375** | **0.3594** |

C maintains 100% population through tick-100, ~94% through tick-200 (slightly above v0.53g's ~87.5%), and ~36% at tick-400 (vs v0.53h's full extinction at tick-400 under the same body_config × horizon). The geometric intervention extends the survival horizon AND lifts the reachability ceiling — survival-extension and food-reachability are no longer decoupled under this geometry.

### `GEOMETRY_OPPOSITE_SIGN_HALT` did not activate this slice

Per the v0.53f-introduced reachability-gated priority 3 trigger (renamed `GEOMETRY_OPPOSITE_SIGN_HALT` in v0.53i), priority 3 fires iff (C tick-400 sub-verdict = `OPPOSITE_SIGN_HALT`) AND (`c_reachability_tick_400 ≥ 0.25`). The first condition did not hold (no wrong-sign cells at C tick-400 — all 6 cells fire PRESENT in the expected direction). The second condition did hold (reachability 0.547 ≥ 0.25). Priority 4 fires instead (the cells are PRESENT, not OPPOSITE_SIGN). The `wrong_sign_cells_under_reachability_below_threshold` section in `audit_summary.csv` is empty. The reachability-gating framework remains battle-tested via v0.53f only on live data; v0.53i did not exercise the framework on live data because no wrong-sign cells emerged. (The framework code path is exercised in v0.53i's test #13 with synthetic fixtures.)

### Tier-1 bridge re-anchor — A_null_V0_25 tick-50 reproduces v0.48–v0.53h within 1e-3

| label | observable | published | derived | drift |
|---|---|:-:|:-:|:-:|
| `label_a_sensor_radius` | `pre50_food_events_count` | +1.066 | +1.066 | 0.000366 |
| `label_a_sensor_radius` | `pre50_food_energy_acquired` | +1.066 | +1.066 | 0.000366 |
| `label_a_sensor_radius` | `mean_distance_to_nearest_food_cell_tick50` | +1.916 | +1.916 | 0.000068 |
| `label_b_readiness_fraction_tick50` | `pre50_food_events_count` | +0.916 | +0.916 | 0.000119 |
| `label_b_readiness_fraction_tick50` | `pre50_food_energy_acquired` | +0.916 | +0.916 | 0.000119 |
| `label_b_readiness_fraction_tick50` | `mean_distance_to_nearest_food_cell_tick50` | +1.179 | +1.179 | 0.000389 |

Max drift 0.000389 (≤ 1e-3). All cells PASS.

### Tier-2 categorical anchor — B_widened_V0_25 reachability_run_share at tick-200

| anchor | locked value | derived | passes |
|---|:-:|:-:|:-:|
| `b_widened_v025_reachability_run_share_tick_200` | **0.0** (0/64) | 0.0000 (0/64) | True (categorical match) |

v0.53c–v0.53h's locked `0/64` reachability anchor holds.

### Corpus re-anchor

A_null_V0_25 arm — all PASS (max drift 0.000312):

| version | derived `a_share_h8` | published | drift |
|---|:-:|:-:|:-:|
| v0.42 | 0.6523 | 0.652 | 0.000312 |
| v0.43R | 0.6743 | — (informational) | — |
| v0.44 | 0.8781 | 0.878 | 0.000091 |
| v0.45 | 0.8182 | 0.818 | 0.000182 |

### What v0.53i can safely claim

- ✓ **A_null_V0_25 tick-50 anchor PASSES** within 0.000389 of v0.48–v0.53h. Reducer machinery (paired_d formula, four-window observer, four Label B variants, script-local layout propagation through `run_chamber()`, layout-geometry CSV capture) is correct.
- ✓ **B_widened_V0_25 categorical Tier-2 anchor PASSES exactly** (0/64 at tick-200). Predecessor lock holds.
- ✓ **The script-local `WIDENED_FOOD_NEAR2_LAYOUT` propagates correctly** through the chamber driver. C arm world width = 13, food_x_min = 8, food_x_max = 12, hazard band preserved at [5,7], spawn preserved at 1, safe band preserved at [0,4], height preserved at 6. Cross-arm contrast in test #5 verified end-to-end.
- ✓ **The 2-column geometric intervention restores reachability above the locked 25% threshold.** C tick-400 reachability = 35/64 (~54.7%). At every measured window (tick-50 through tick-400), C reachability is in the range 0.531–0.547, well above 0.25.
- ✓ **The v0.48 sensor_radius spatial / foraging bridge fires PRESENT** under both gating labels at the C tick-400 panel. All 6 cells fire ≥ +0.5; 0 wrong-sign cells. Label B signed_d values are particularly large (+5.304 / +5.304 / +6.295) reflecting strong concentration of food contact in the highest tick-400 readiness lineages.
- ✓ **Reducing post-hazard food distance by two columns is sufficient to restore measurable reachability and bridge expression under the combined-budget envelope at `n_ticks=400` on the V0_25 substrate.**
- ✓ **The v0.53c–v0.53h reachability ceiling is lifted by reducing post-hazard food distance under the tested envelope** — the lone slice in the v0.53d→v0.53i stack to lift the ceiling.
- ✓ **The reachability-gated priority-3 framework continues to behave correctly** (no wrong-sign cells emerged on live data; the synthetic test fixture in test #13 still passes; halt name renamed `GEOMETRY_OPPOSITE_SIGN_HALT` reflects the geometric-intervention class).

### What v0.53i cannot claim

- ✗ **"Geometry solved"** under priority 4. v0.53i tested ONE geometric intervention (2-column food-near) under one combined-knob envelope at one horizon. Whether smaller (1-column) or larger (4-column) reductions, alternative geometric perturbations (corridor variation, hazard thickness, spawn shift), or non-V0_25 substrates would behave similarly is empirically untested.
- ✗ **"Distance to food is the binding constraint."** The bounded claim is that this 2-column reduction is sufficient under the tested envelope — not that distance is the sole or even the principal explanation. v0.53i does NOT test smaller reductions (e.g., 1-column, food_x∈[9,13]) which could dose-respond and inform the role of distance more precisely.
- ✗ **"Policy / hazard-avoidance is ruled out."** The intervention removed the post-hazard corridor; whether founders successfully traverse the hazard band itself (still 3 columns thick, hazard_x∈[5,7]) under v0.53i remains an open empirical question — the geometric change reduced cells founders need to traverse east of the hazard band, but the hazard band itself is unchanged. v0.53j+ probes can disambiguate hazard-band traversal mechanics from food-distance specifically.
- ✗ **A revised v0.53–v0.53h verdict.** All eight predecessor verdicts stand as historical contracts.
- ✗ **Mechanism behind the rescue.** Population dynamics and per-tick reachability trajectory under V0_25 × `widened_food_near2` × combined-budget × `n_ticks=400` are descriptively logged; no mechanism is formally established. Plausible interpretations (not formally established): the 2-column reduction shrinks the per-traverse hazard exposure window; sensor reach now overlaps the food band from spawn AFTER hazard traversal at sensor_radius ≥ ~7; the 2 corridor columns of B were stochastic-loss territory under the policy.
- ✗ **Generalization beyond the tested arms.** Verdict scope is bounded to (`tight_gradient` × V0_25 at `n_ticks=200`, `widened_gradient` × V0_25 at `n_ticks=200`, `widened_food_near2` × V0_25 with `BodyConfig(se100, bmc010)` at `n_ticks=400`).

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
| v0.53d | modern A_null | doubling `ambient_influx_rate` is mechanically inert | observational (BELOW_REACHABILITY_THRESHOLD_UNDER_RELAXED_INFLUX) |
| v0.53e | modern A_null | `BodyConfig.starting_energy=100` extends survival ~9% but does NOT lift reachability | observational (RELAXED_OPPOSITE_SIGN_HALT) |
| v0.53f | modern A_null | `BodyConfig.base_metabolic_cost=0.10` extends survival ~16% but does NOT lift reachability | observational (BELOW_REACHABILITY_THRESHOLD_UNDER_BASE_METABOLIC_COST_010) |
| v0.53g | modern A_null | combined SE100/BMC010 extends survival ~87.5% at tick-200 but does NOT lift reachability; survival-extension and food-reachability decoupled | observational (BELOW_REACHABILITY_THRESHOLD_UNDER_COMBINED_SE100_BMC010; central finding) |
| v0.53h | modern A_null | doubling `n_ticks` to 400 under combined envelope does NOT lift reachability AND C goes fully extinct by tick-400; survival horizon also has a ceiling | observational (BELOW_REACHABILITY_THRESHOLD_AT_TIME_HORIZON_400; central finding) |
| v0.53i | modern A_null | reducing post-hazard food distance by 2 columns under combined envelope at `n_ticks=400` lifts reachability to 35/64 AND fires PRESENT under both gating labels at C tick-400 | observational (BRIDGE_RESCUED_BY_FOOD_NEAR2; the v0.53c–v0.53h reachability ceiling is lifted) |

The v0.46→v0.53i stack now reads: ... → v0.53d–v0.53h's null reachability across budget AND horizon doublings (all priority 5) → **v0.53i's geometric intervention lifts the ceiling: reducing post-hazard food distance by 2 columns under the same combined-budget × `n_ticks=400` envelope rescues both reachability (0/64 → 35/64) and bridge expression (NOT_FOUND → PRESENT under both labels) at C tick-400.**

### Next-step candidates (open)

The geometric intervention's success opens a new design space:

- **v0.53j candidate — dose-response within food-near axis.** Test `food_x∈[9,13]` (1-column near; corridor reduced from 2 to 1) and `food_x∈[7,11]` (3-column near; food band overlapping hazard?) to map the dose curve. The 2-column reduction is sufficient; whether smaller reductions also rescue reachability is an open question (Reading-A causal-generalization on the geometric axis).
- **v0.53k candidate — disambiguate distance vs hazard-band traversal.** Hold food-near at 2 columns but vary hazard-band thickness. Tests whether the rescue is specifically about food being closer or about reduced-distance-east-of-hazard.
- **v0.53l candidate — Reading-A causal-generalization slice on `widened_food_near2`.** With reachability now rescued on C, the v0.49–v0.52b causal-generalization framework can be re-anchored on this layout under the combined-budget × `n_ticks=400` envelope.
- **v0.53m candidate — substrate cross-corpus calibration on `widened_food_near2`.** Test whether the v0.42–v0.45 corpus signed_d values reproduce on the new layout, anchoring whether the rescue is specific to V0_25 × widened_food_near2 or generalizes to non-V0_25 substrates.
- **v0.53n candidate — alternative spawn position.** Move spawn closer to the hazard (e.g., `spawn_x=3`) on `widened_gradient` (NOT food-near2) to test whether perceptual reach alone, holding distance constant, suffices.
- **v0.54 — joint ablation** (zero-cost AND shuffle).
- **Eventual fresh-stream calibration** on the v0.46–v0.53i conclusion stack.

User has not locked which slice is next.

### CI gate at v0.53i close

```
uv run ruff check .             ok
uv run ruff format --check .    ok (240 files already formatted)
uv run pytest                   1840 passed, 7 skipped (was 1824; +16 v0.53i)
uv run python scripts/core_smoke_test.py                                ok (determinism north star intact; no src/ changes)
uv run python scripts/v0_53i_geometry_food_near2_audit.py               WIDENED_BRIDGE_RESCUED_BY_FOOD_NEAR2 (priority 4; geometry-gating did not activate — no wrong-sign cells)
```
