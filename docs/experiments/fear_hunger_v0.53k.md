# fear_hunger v0.53k — perception-reach mechanism probe at FOOD_NEAR1 (sensor_radius=8 override on `widened_food_near1` × V0_25 × combined founder-budget envelope at `n_ticks=400`)

**Slice:** v0.53k
**Type:** **first-class observational sweep** with 4-arm asymmetric-horizon reducer (no `src/` changes — both novel C and D layouts constructed script-local; v0.53e's `body_config` seam carries forward; `n_ticks` already exposed; `effective_sensor_radius_override` already exposed in `BodyConfig`; no intervention; **single perception knob** on the C arm under FOOD_NEAR1 — v0.53k is a mechanism probe asking whether the sharp v0.53j FOOD_NEAR1/FOOD_NEAR2 boundary is perception-bound or policy/hazard-bound; D arm is the in-slice positive anchor reproducing v0.53i/v0.53j FOOD_NEAR2 result).
**Predecessors:** v0.46–v0.52b (full predecessor stack), v0.53 (`BRIDGE_PARTIALLY_GENERALIZES`), v0.53b (`WIDENED_BELOW_REACHABILITY_THRESHOLD_AT_TICK_100`), v0.53c (`WIDENED_BELOW_REACHABILITY_THRESHOLD_AT_TICK_200`), v0.53d (`WIDENED_BELOW_REACHABILITY_THRESHOLD_UNDER_RELAXED_INFLUX`), v0.53e (`RELAXED_OPPOSITE_SIGN_HALT`), v0.53f (`WIDENED_BELOW_REACHABILITY_THRESHOLD_UNDER_BASE_METABOLIC_COST_010`), v0.53g (`WIDENED_BELOW_REACHABILITY_THRESHOLD_UNDER_COMBINED_SE100_BMC010`), v0.53h (`WIDENED_BELOW_REACHABILITY_THRESHOLD_AT_TIME_HORIZON_400`), v0.53i (`WIDENED_BRIDGE_RESCUED_BY_FOOD_NEAR2` — first RESCUED outcome since v0.53d→v0.53h null stack), v0.53j (`WIDENED_BELOW_REACHABILITY_THRESHOLD_UNDER_FOOD_NEAR1` — sharp threshold-like discontinuity at the FOOD_NEAR1/FOOD_NEAR2 boundary; D positive anchor reproduced v0.53i with zero drift).
**Question being asked (locked):** Is the sharp v0.53j FOOD_NEAR1/FOOD_NEAR2 boundary perception-bound, OR policy / hazard-avoidance / movement-bound? Specifically: with the script-local `widened_food_near1` layout (`food_x∈[9,13]`, 1-column corridor at `x=8`), `BodyConfig(starting_energy=100.0, base_metabolic_cost=0.10, effective_sensor_radius_override=8)`, and `n_ticks=400`, does C tick-400 reachability cross 0.25?

v0.53j established that the dose-response on the food-distance axis is **sharp at the tested 1-column resolution**: 0-column corridor (FOOD_NEAR2: `food_x∈[8,12]`) rescues to 35/64 reachability; 1-column corridor (FOOD_NEAR1: `food_x∈[9,13]`) yields 0/64 reachability AND full extinction by tick-400. The 1-column reduction is empirically equivalent to the widened baseline. v0.53k probes the mechanism behind this discontinuity by varying perception-reach independently of food distance.

The chosen perception lever is `BodyConfig.effective_sensor_radius_override`. Per `src/hedonism_harness/core/sensors.py:138-142`, this override **bypasses `body.traits.sensor_radius` for the perception calculation only** — the metabolic-drain formula in `src/hedonism_harness/core/body.py:81` continues to use `traits.sensor_radius` directly. This decouples perception-reach from per-tick metabolic cost: founders see further WITHOUT paying additional sensor-cost. The intervention is information-channel-only, not cost-confounded.

The chosen dose is **`effective_sensor_radius_override = 8`**. Per `src/hedonism_harness/core/sensors.py:11`: "out to `traits.sensor_radius` cells. Per §10.2: `signal += value / distance`"; per `src/hedonism_harness/experiments/layouts.py:25-28`: "Sensor model reminder (`core/sensors._scan_axial`): radius scans go along the four cardinal rays only, NOT a square box. So 'visible eastward from `spawn_x`' means cells at `y == spawn_y` in `[spawn_x+1 .. spawn_x+r]`." With `spawn_x=1` and `r=8`, the east ray scans `x ∈ [2..9]`, which **just** includes `FOOD_NEAR1.food_x_min=9` at the far edge of the ray. r=8 is the minimum override value that grants tick-0 east-ray perception of FOOD_NEAR1's food band from spawn. (Compare: r=7 reaches `x ∈ [2..8]`, which includes `FOOD_NEAR2.food_x_min=8` but NOT `FOOD_NEAR1.food_x_min=9`. This is consistent with v0.53i/j's observation that FOOD_NEAR2 was reachable under default sensor distribution while FOOD_NEAR1 was not.)

**The minimum-perception design question:** if r=8 (just barely enough perceptual reach) rescues C reachability under the same combined-budget × n_ticks=400 envelope as v0.53j's null FOOD_NEAR1, the v0.53j FOOD_NEAR1/FOOD_NEAR2 boundary is **consistent with sensor-reach being a binding constraint** under the tested envelope. If r=8 does NOT rescue, sensor-reach alone is not the explanation, and the candidate space shifts toward policy / hazard-avoidance / movement mechanics.

If C tick-400 reachability ≥ 25% AND tick-400 sub-verdict resolves PRESENT, the v0.53j FOOD_NEAR1 null is consistent with sensor-reach being a binding constraint under the tested envelope. v0.53k does NOT establish that perception is the **exclusive** or **sole** cause — sensor radius may alter policy gradients, hazard anticipation, or food-attraction signal strength beyond simple visibility (the gradient `signal += value / distance` from sensors.py:11 means farther food still contributes attractive signal once visible). If reachability ≥ 25% AND sub-verdict ∈ {PARTIAL, NOT_FOUND}, the perception override admits measurement but the bridge fails to fully fire. If reachability ≥ 25% AND sub-verdict = OPPOSITE_SIGN_HALT, the reachability-gated priority-3 trigger fires (bridge framework is meaningful at this measurement). If reachability < 25%, **the sharp FOOD_NEAR1/FOOD_NEAR2 boundary is NOT explained by sensor-reach alone under the tested envelope** — the candidate space for v0.53l+ shifts toward policy / hazard-avoidance / movement-mechanics probes. v0.53k does NOT claim "perception is irrelevant" or "the binding cause is policy specifically"; the verdict scope is bounded to the tested r=8 perception override.

## Pre-implementation note (2026-05-09, before any reducer code)

The pre-reg's design was confirmed with the user before drafting:

- **4 arms (asymmetric `n_ticks`).** A_null_V0_25 (tight_gradient, V0_25, `n_ticks=200`, anchor). B_widened_V0_25 (widened_gradient, V0_25, `n_ticks=200`; predecessor lock). C_widened_food_near1_combined_sr8_N400 (script-local FOOD_NEAR1 layout, V0_25 substrate **except** `BodyConfig(starting_energy=100.0, base_metabolic_cost=0.10, effective_sensor_radius_override=8)`, `n_ticks=400`; primary verdict-gating). D_widened_food_near2_combined_N400 (script-local FOOD_NEAR2 layout — byte-identical to v0.53i C / v0.53j D; `BodyConfig(starting_energy=100.0, base_metabolic_cost=0.10)`; default sensor (no override); `n_ticks=400`; in-slice positive anchor). Same 64-tuple corpus. **256 runs.**
- **Single perception knob on C; D matches v0.53i/v0.53j positive anchor exactly.** v0.53j tested two food-distance doses (FOOD_NEAR1 fails; FOOD_NEAR2 rescues). v0.53k holds FOOD_NEAR1 layout fixed and varies one perception parameter (`effective_sensor_radius_override`) on C. The corpus / RNG seeds / hazards / `body_config.starting_energy` / `body_config.base_metabolic_cost` / `n_ticks` are otherwise identical between C and D. C and D differ by exactly two things: layout (FOOD_NEAR1 vs FOOD_NEAR2) AND `body_config.effective_sensor_radius_override` (8 vs None).
- **No fifth in-slice negative anchor on FOOD_NEAR1 + default sensor.** v0.53j C established 0/64 reachability + full extinction at that config; cross-slice reference is sufficient (logical predecessor). The fifth arm would cost ~6-12 min wall time without changing the verdict.
- **Both novel layouts constructed script-local — no `src/` change.** Module-level constants `FOOD_NEAR1_LAYOUT` and `FOOD_NEAR2_LAYOUT` (identical to v0.53j). NOT added to `layouts.py`. Test #8 pinning unchanged from v0.53e/f/g/h/i/j — `layouts.py` SHA still `d4521cb5...`.
- **`BodyConfig.effective_sensor_radius_override` is the chosen perception lever.** Per `src/hedonism_harness/core/sensors.py:138-142`, the override applies model-wide and bypasses `body.traits.sensor_radius` for the sensor calculation. Per `src/hedonism_harness/core/body.py:81`, the metabolic-drain formula uses `traits.sensor_radius` directly — the override does NOT affect metabolic cost. This is the perception-only, cost-decoupled lever.
- **D arm is the in-slice predecessor positive anchor** — byte-identical to v0.53i C / v0.53j D under matched RNG. v0.53k enforces the same Tier-3 anchor as v0.53j: D tick-400 reachability == 35/64 exact, D tick-400 sub-verdict == BRIDGE_PRESENT, AND D's six paired_d cells reproduce v0.53i published values within 1e-3 drift.
- **Reachability-gated priority 3 (carries forward, RENAMED `PERCEPTION_OPPOSITE_SIGN_HALT`).** v0.53i renamed `RELAXED_OPPOSITE_SIGN_HALT` (v0.53e/f/g/h) to `GEOMETRY_OPPOSITE_SIGN_HALT`; v0.53k renames again to `PERCEPTION_OPPOSITE_SIGN_HALT` reflecting the perception-axis intervention. Same gating logic: priority 3 fires iff C tick-400 sub-verdict = `OPPOSITE_SIGN_HALT` AND `c_reachability_tick_400 ≥ 0.25`.
- **Tick-400 verdict gating on C; tick-400 anchor on D; tick-200 descriptive on A/B.** Same 4-window observer structure as v0.53i/j.
- **Tier-2 categorical anchor on B_widened_V0_25 preserved** (reachability tick-200 == `0/64`).
- **Tier-3 positive anchor on D preserved** (identical to v0.53j).
- **Pool / ecology preserved.** Only `layout`, `body_config`, AND `n_ticks` differ across arms. No `src/` modifications.
- **Expected behavioral identity between v0.53k D and v0.53j D / v0.53i C through tick-400.** Same layout, same body_config, same n_ticks, same RNG. D tick-400 reachability is mechanically guaranteed to match v0.53i's 35/64.

## Conservation framing — observational, no `src/` changes, single perception knob on C

- **No `src/` modifications.** Both novel layouts constructed script-local; `n_ticks` and `body_config` (including `effective_sensor_radius_override`) already exposed. The five science-core files AND `fear_hunger_chamber.py` AND `layouts.py` all remain byte-identical to their v0.52b-tip / v0.53e-tip values. Test #8 enforces both pinning categories.
- **No modifications to prior reducer or audit scripts.** v0.53j's reducer remains byte-identical to its merged form.
- **A_null_V0_25 arm is byte-identical to v0.48–v0.53j A_null path AT TICK-50.** Tier-1 re-anchor enforces this within 1e-3.
- **B_widened_V0_25 arm is byte-identical to v0.53–v0.53j's B_widened arm at every tick 0..200.** Tier-2 categorical anchor enforces `b_widened_v025_reachability_run_share_tick_200 == 0.0`.
- **D_widened_food_near2_combined_N400 arm is byte-identical to v0.53i C and v0.53j D at every tick 0..400.** Tier-3 positive anchor enforces (a) reachability_tick_400 == 35/64 exact, (b) sub-verdict == BRIDGE_PRESENT, (c) six paired_d cells within 1e-3 of v0.53i published values.
- **C_widened_food_near1_combined_sr8_N400 differs from v0.53j C by exactly one knob:** `body_config.effective_sensor_radius_override` (None → 8). All other layout / body_config / n_ticks / corpus parameters identical to v0.53j C.
- **No intervention at any level on any arm.** No founder body trait modification post-construction, no override patching, no helper RNG, no shuffle, no clamp, no permutation.

## Corpus (locked, 64 × 4 arms = 256 runs; asymmetric wall time)

Same shape as v0.53d–v0.53j:

| version | seeds | hazards | runs per arm | total runs |
|---|---|---|---|---|
| v0.42 | 41..48 | {0, 8} | 16 | 64 |
| v0.43R | 49..56 | {0, 8} | 16 | 64 |
| v0.44 | 57..64 | {0, 8} | 16 | 64 |
| v0.45 | 65..72 | {0, 8} | 16 | 64 |
| **total** | | | | **256** |

Wall time estimate ~25–50 minutes total (asymmetric: 128 runs at `n_ticks=200`, 128 runs at `n_ticks=400`).

## Arms (locked, 4)

### A_null_V0_25

```
ChamberLayout = tight_gradient_layout()
... (V0_25 baseline; body_config=None; n_ticks=200)
```

Byte-identical to v0.48–v0.53j A_null. **Tier-1 anchor at tick-50.**

### B_widened_V0_25

```
ChamberLayout = widened_gradient_layout()
... (V0_25 baseline; body_config=None; n_ticks=200)
```

Byte-identical to v0.53–v0.53j's B_widened. **Tier-2 categorical anchor on tick-200 reachability.**

### C_widened_food_near1_combined_sr8_N400 (PRIMARY VERDICT-GATING)

```
ChamberLayout = ChamberLayout(  # script-local FOOD_NEAR1_LAYOUT (identical to v0.53j C)
    safe_x_min=0, safe_x_max=4,
    hazard_x_min=5, hazard_x_max=7,
    food_x_min=9, food_x_max=13,
    height=6, spawn_x=1,
)
... (V0_25 baseline pool/ecology;
    body_config = BodyConfig(
        starting_energy=100.0,
        base_metabolic_cost=0.10,
        effective_sensor_radius_override=8,   # PERCEPTION OVERRIDE — NEW in v0.53k
    );
    n_ticks = 400)
```

Differs from v0.53j C by exactly one knob: `body_config.effective_sensor_radius_override` (None → 8). Differs from D by layout (FOOD_NEAR1 vs FOOD_NEAR2) AND the override (8 vs None). **The primary arm of v0.53k**: the verdict gates on C's tick-400 reachability and tick-400 sub-verdict.

### D_widened_food_near2_combined_N400 (IN-SLICE POSITIVE ANCHOR)

```
ChamberLayout = ChamberLayout(  # script-local FOOD_NEAR2_LAYOUT (identical to v0.53j D / v0.53i C)
    safe_x_min=0, safe_x_max=4,
    hazard_x_min=5, hazard_x_max=7,
    food_x_min=8, food_x_max=12,
    height=6, spawn_x=1,
)
... (V0_25 baseline pool/ecology;
    body_config = BodyConfig(starting_energy=100.0, base_metabolic_cost=0.10);
                  # NO effective_sensor_radius_override; matches v0.53i/v0.53j D
    n_ticks = 400)
```

Byte-identical to v0.53i's C arm and v0.53j's D arm at every tick 0..400. **Tier-3 positive anchor:** D tick-400 reachability == 35/64 exact AND sub-verdict == BRIDGE_PRESENT AND six paired_d cells reproduce v0.53i within 1e-3.

## Labels (locked, two — with four Label B variants on C/D, three on A/B)

Identical to v0.53j: Label A (`high_sensor_radius_lineage` — trait-resolved); Label B variants `high_tick{50,100,200,400}_readiness_fraction_lineage` (tick-400 variant computed on C and D only; NaN-broadcast on A/B).

## Primary observables (locked, 3, four windows on C/D, three on A/B)

Identical to v0.53j. Note: observable 3 (`mean_distance_to_nearest_food_cell_tick{N}`) uses each arm's layout food cells; cross-arm signed_d is NOT directly cross-arm interpretable.

## Effect-size rule (locked, sign-aware, identical to v0.48–v0.53j)

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
    (TIER-2 ANCHOR — must equal 0.0 exactly)

c_widened_food_near1_combined_sr8_N400_reachability_run_share_tick_400 =
    (VERDICT-GATING; threshold 0.25)

d_widened_food_near2_combined_N400_reachability_run_share_tick_400 =
    (TIER-3 POSITIVE ANCHOR — must equal 35/64 = 0.546875 exactly)
```

## Tier-3 positive anchor on D (locked, pre-data, identical to v0.53j)

Six paired_d cells reproduced from v0.53i Results, 1e-3 absolute tolerance:

| label | observable | published v0.53i signed_d | tolerance |
|---|---|:-:|:-:|
| `label_a_sensor_radius` | `pre400_food_events_count` | **+1.036** (precise: `+1.0357354787853512`) | 1e-3 |
| `label_a_sensor_radius` | `pre400_food_energy_acquired` | **+1.036** | 1e-3 |
| `label_a_sensor_radius` | `mean_distance_to_nearest_food_cell_tick400` | **+1.062** (precise: `+1.061633559034245`) | 1e-3 |
| `label_b_readiness_fraction_tick400` | `pre400_food_events_count` | **+5.304** (precise: `+5.3040008005819095`) | 1e-3 |
| `label_b_readiness_fraction_tick400` | `pre400_food_energy_acquired` | **+5.304** | 1e-3 |
| `label_b_readiness_fraction_tick400` | `mean_distance_to_nearest_food_cell_tick400` | **+6.295** (precise: `+6.294727858398778`) | 1e-3 |

Plus categorical: D tick-400 reachability == 0.546875 (35/64) exact AND D tick-400 sub-verdict == `D_WIDENED_FOOD_NEAR2_TICK400_BRIDGE_PRESENT`.

Note: v0.53j Results recorded D anchor reproduction with **drift_abs = 0.0** on every cell (perfect determinism). v0.53k expects the same.

## Per-arm sub-verdicts (locked, 4-way each — verdict-gating on C tick-400; anchor on D tick-400)

| condition | A_null_V0_25 | B_widened_V0_25 | C_widened_food_near1_combined_sr8_N400 (tick-400 **verdict-gating**) | D_widened_food_near2_combined_N400 (tick-400 **anchor**) |
|---|---|---|---|---|
| both labels clear ≥ 2/3 cells, NaN non-firing, 0 wrong-sign | `A_NULL_V025_TICK{50,100,200}_BRIDGE_PRESENT` | `B_WIDENED_V025_TICK200_BRIDGE_PRESENT` | `C_WIDENED_FOOD_NEAR1_SR8_TICK400_BRIDGE_PRESENT` | `D_WIDENED_FOOD_NEAR2_TICK400_BRIDGE_PRESENT` |
| exactly one label clears ≥ 2/3 cells | `..._BRIDGE_PARTIAL` | ... | `..._BRIDGE_PARTIAL` | `..._BRIDGE_PARTIAL` |
| neither clears ≥ 2/3 cells | `..._BRIDGE_NOT_FOUND` | ... | `..._BRIDGE_NOT_FOUND` | `..._BRIDGE_NOT_FOUND` |
| any primary signed_d ≤ −0.5 | `..._OPPOSITE_SIGN_HALT` | ... | `..._OPPOSITE_SIGN_HALT` | `..._OPPOSITE_SIGN_HALT` |

**Strict NaN-treated-as-non-firing rule preserved.** C's sub-verdict prefix is `C_WIDENED_FOOD_NEAR1_SR8_TICK{N}_BRIDGE_{...}` (the `_SR8` suffix distinguishes from v0.53j's C_WIDENED_FOOD_NEAR1_TICK{N}).

## Slice rollup verdicts (locked, 6 outcomes, priority-ordered)

1. `CORPUS_REDERIVE_DRIFT_HALT`
2. `ANCHOR_REPLICATION_HALT` (Tier-1 + Tier-2 + Tier-3; same six sub-conditions as v0.53j)
3. `PERCEPTION_OPPOSITE_SIGN_HALT` (**reachability-gated** on C tick-400; renamed from v0.53i/j's `GEOMETRY_OPPOSITE_SIGN_HALT` — reflects perception-axis intervention)
4. `WIDENED_BRIDGE_RESCUED_BY_SENSOR_RADIUS_8`
5. `WIDENED_BELOW_REACHABILITY_THRESHOLD_UNDER_SENSOR_RADIUS_8`
6. `WIDENED_BRIDGE_PARTIALLY_RESCUED_BY_SENSOR_RADIUS_8`

### Halt conditions

| priority | rollup verdict | trigger | locked phrase (verbatim) |
|---|---|---|---|
| 1 | `CORPUS_REDERIVE_DRIFT_HALT` | A `a_share_h8` for v0.42/v0.44/v0.45 drifts > 1e-3 | "Halt: A_null_V0_25 re-anchor drifted from the published Results value for {version}; v0.53k's deterministic re-execution of the V0_25 corpus does not reproduce the published metric within 1e-3." |
| 2 | `ANCHOR_REPLICATION_HALT` | (a) A tick-50 paired_d drift > 1e-3, (b) A tick-50 sub-verdict ≠ PRESENT, (c) B tick-200 reachability ≠ 0, (d) D tick-400 reachability ≠ 35/64 exact, (e) D tick-400 sub-verdict ≠ BRIDGE_PRESENT, (f) D tick-400 paired_d drift > 1e-3 | "Halt: v0.53k's A_null_V0_25 arm does not reproduce v0.48–v0.53j's tick-50 spatial bridge, OR v0.53k's B_widened_V0_25 arm does not reproduce v0.53c–v0.53j's `0/64` reachability lock at tick-200, OR v0.53k's D_widened_food_near2_combined_N400 arm does not reproduce v0.53i's tick-400 positive anchor (categorical reachability `35/64` AND sub-verdict `BRIDGE_PRESENT` AND six published paired_d cells within 1e-3). v0.53k cannot interpret the C_widened_food_near1_combined_sr8_N400 cells without reproducing both the V0_25 baseline anchors and the v0.53i FOOD_NEAR2 positive anchor." |
| 3 | `PERCEPTION_OPPOSITE_SIGN_HALT` (**reachability-gated**) | C tick-400 sub-verdict = `OPPOSITE_SIGN_HALT` AND `c_reachability_tick_400 ≥ 0.25` | "Halt: a v0.53k C_widened_food_near1_combined_sr8_N400 tick-400 spatial / foraging primary fires in the WRONG direction under a gating label, AND C reachability at tick-400 clears the locked 25% threshold. The perception-only intervention (`BodyConfig.effective_sensor_radius_override = 8`) under FOOD_NEAR1 + combined founder-facing budget envelope at `n_ticks = 400` surfaces a regime where the locked expected signs do not hold under measurable food access. The reachability-gated trigger preserves v0.53e's locked sign discipline while excluding the v0.53e-style measurement-edge case (wrong-sign at reachability=0)." |

### Outcome conditions (only consulted if no halt fires)

| priority | rollup verdict | trigger | locked phrase (verbatim) |
|---|---|---|---|
| 4 | `WIDENED_BRIDGE_RESCUED_BY_SENSOR_RADIUS_8` | `c_widened_food_near1_combined_sr8_N400_reachability_run_share_tick_400 ≥ 0.25` AND C tick-400 sub-verdict = `C_WIDENED_FOOD_NEAR1_SR8_TICK400_BRIDGE_PRESENT` | "On the modern A_null corpus with the V0_25 substrate held constant except for the combined founder-facing budget relaxation `BodyConfig(starting_energy=100.0, base_metabolic_cost=0.10)` AND the simulation horizon doubled to `n_ticks=400` AND the `widened_food_near1` layout (`food_x∈[9,13]`, 1-column corridor at `x=8`; identical to v0.53j C) AND the perception-only override `BodyConfig.effective_sensor_radius_override = 8` (the minimum east-ray reach from `spawn_x=1` to FOOD_NEAR1's `food_x_min=9`; metabolic cost UNAFFECTED per the override's information-channel-only contract), the v0.48 sensor_radius spatial / foraging bridge fires PRESENT under the locked +0.5 paired_d threshold at tick-400. The geometry/substrate cell that v0.53c locked as `WIDENED_BELOW_REACHABILITY_THRESHOLD_AT_TICK_200`, v0.53d locked as `WIDENED_BELOW_REACHABILITY_THRESHOLD_UNDER_RELAXED_INFLUX`, v0.53e locked as `RELAXED_OPPOSITE_SIGN_HALT`, v0.53f locked as `WIDENED_BELOW_REACHABILITY_THRESHOLD_UNDER_BASE_METABOLIC_COST_010`, v0.53g locked as `WIDENED_BELOW_REACHABILITY_THRESHOLD_UNDER_COMBINED_SE100_BMC010`, v0.53h locked as `WIDENED_BELOW_REACHABILITY_THRESHOLD_AT_TIME_HORIZON_400`, v0.53i locked as `WIDENED_BRIDGE_RESCUED_BY_FOOD_NEAR2`, and v0.53j locked as `WIDENED_BELOW_REACHABILITY_THRESHOLD_UNDER_FOOD_NEAR1` admits a measurable bridge under the perception-only intervention: B_widened_V0_25 reachability remains `0/64` at tick-200 (predecessor lock holds), D_widened_food_near2_combined_N400 reachability reproduces v0.53i's `35/64` positive anchor at tick-400 (positive lock holds), C reachability at tick-400 clears the locked 25% threshold, and ≥ 2/3 spatial / foraging primaries fire PRESENT under both gating labels at the C tick-400 panel. The v0.53j FOOD_NEAR1/FOOD_NEAR2 boundary is **consistent with sensor-reach being a binding constraint** under the tested envelope. This is strong evidence but NOT exclusive causality — sensor-radius override may alter policy gradients, hazard anticipation, or food-attraction signal strength beyond simple visibility (per the `signal += value/distance` gradient in `core/sensors.py:11`). This does NOT prove `perception is the binding cause` universally; NOT `policy/hazard/movement are ruled out` (other interventions could also rescue): `WIDENED_BRIDGE_RESCUED_BY_SENSOR_RADIUS_8`." |
| 5 | `WIDENED_BELOW_REACHABILITY_THRESHOLD_UNDER_SENSOR_RADIUS_8` | `c_widened_food_near1_combined_sr8_N400_reachability_run_share_tick_400 < 0.25` | "On the modern A_null corpus with the V0_25 substrate held constant except for the combined founder-facing budget relaxation `BodyConfig(starting_energy=100.0, base_metabolic_cost=0.10)` AND the simulation horizon doubled to `n_ticks=400` AND the `widened_food_near1` layout AND the perception-only override `BodyConfig.effective_sensor_radius_override = 8`, fewer than 25% of C runs have any founder lineage with pre400 food events. C's reachability is below the locked 25% threshold at tick-400; D_widened_food_near2_combined_N400 reproduces v0.53i's `35/64` positive anchor at tick-400 in-slice. The v0.53j FOOD_NEAR1/FOOD_NEAR2 boundary is **NOT explained by sensor-reach alone** under the tested envelope. The geometry/substrate cell that v0.53c locked as `WIDENED_BELOW_REACHABILITY_THRESHOLD_AT_TICK_200`, ..., v0.53j locked as `WIDENED_BELOW_REACHABILITY_THRESHOLD_UNDER_FOOD_NEAR1` is not rescued by the perception-only intervention at `r=8`. This does NOT prove `perception is irrelevant` or `the binding cause is policy specifically` — only that this specific perception override does not lift reachability under the tested envelope. v0.53l (or later) candidates shift toward policy / hazard-avoidance / movement-mechanics probes: `WIDENED_BELOW_REACHABILITY_THRESHOLD_UNDER_SENSOR_RADIUS_8`." |
| 6 | `WIDENED_BRIDGE_PARTIALLY_RESCUED_BY_SENSOR_RADIUS_8` | `c_widened_food_near1_combined_sr8_N400_reachability_run_share_tick_400 ≥ 0.25` AND C tick-400 sub-verdict ∈ {PARTIAL, NOT_FOUND} | "On the modern A_null corpus with the V0_25 substrate held constant except for the combined founder-facing budget relaxation AND the perception-only override `effective_sensor_radius_override = 8` on FOOD_NEAR1 at `n_ticks=400`, C's reachability clears the locked 25% threshold at tick-400 but the v0.48 sensor_radius spatial / foraging bridge does not fully fire PRESENT — fewer than 2/3 primaries fire across both gating labels at tick-400 under the strict NaN rule. D_widened_food_near2_combined_N400 reproduces v0.53i's `35/64` positive anchor at tick-400 in-slice. The perception override admits measurable food access but does not fully replicate v0.53i's PRESENT bridge expression. Layout-specific partial-rescue logged in Results: `WIDENED_BRIDGE_PARTIALLY_RESCUED_BY_SENSOR_RADIUS_8`." |

The 3 non-halt outcomes form a total partition (same as v0.53j). Test #16 enforces the partition exhaustively.

## Cautious framing (per CLAUDE.md, refined per user direction)

- **"Consistent with sensor-reach being a binding constraint under the tested envelope"** (priority 4) — NOT "perception was binding"; NOT "perception is the binding cause"; NOT "policy/hazard/movement are ruled out". Strong evidence is not exclusive causality. Sensor-radius override may alter policy gradients, hazard anticipation, or food-attraction signal strength beyond simple visibility (the `signal += value/distance` gradient is non-trivial).
- **"NOT explained by sensor-reach alone under the tested envelope"** (priority 5) — NOT "perception is irrelevant"; NOT "the binding cause is policy specifically". The bounded claim is that this specific r=8 override does not lift reachability under FOOD_NEAR1 + combined-budget × n_ticks=400.
- "Tested override" means `effective_sensor_radius_override = 8` specifically. v0.53k does NOT establish behavior at smaller (r=6/7) or larger (r=10/12) overrides; those require separate slices.
- v0.53k explicitly does not establish: cross-layout generalization beyond the named layouts, mechanism for any rescue or non-rescue outcome at SR_8, generalization to non-V0_25 substrates, behavior at non-`n_ticks=400` horizons under the same intervention, dose-response below or above r=8.

## What v0.53k cannot establish

- ✗ **"Perception is the binding cause"** under priority 4. Strong evidence ≠ exclusive causality. Other interventions (policy / hazard-avoidance / movement) might ALSO rescue reachability under FOOD_NEAR1.
- ✗ **"Perception is irrelevant"** under priority 5. The v0.53k null at r=8 establishes that this perception override is INsufficient under the tested envelope; it does not establish that perception plays no role at any other parameter setting.
- ✗ **"r=8 is the minimum sufficient override"** under priority 4. v0.53k does NOT test r=7 (potential converse boundary); whether smaller overrides also rescue is empirically untested. v0.53l candidate.
- ✗ **A revised v0.53–v0.53j verdict.** All ten predecessor verdicts stand as historical contracts.
- ✗ **Mechanism behind any rescue or non-rescue outcome.** Population dynamics under V0_25 × FOOD_NEAR1 × combined-budget × `n_ticks=400` × `effective_sensor_radius_override=8` are descriptively logged; no mechanism is formally established.

## Open framing (NOT in v0.53k primary)

- **If priority 4 fires (perception override rescues):**
  - **v0.53l candidate — sensor_radius dose curve.** Test r=6, r=7, r=10 to localize the threshold and characterize the dose-response shape.
  - **v0.53m candidate — Reading-A causal-generalization on FOOD_NEAR1 + sr=8.** With reachability rescued, the v0.49–v0.52b causal-generalization framework can re-anchor.
  - **v0.53n candidate — FOOD_NEAR2 with reduced default sensor.** Tests the converse: does reducing perception in the rescued FOOD_NEAR2 layout break the rescue?
- **If priority 5 fires (perception override insufficient):**
  - **v0.53l candidate — policy / hazard-avoidance probe.** Vary `hazard_avoidance_weight` or other policy knobs on FOOD_NEAR1 under combined-budget × n_ticks=400.
  - **v0.53m candidate — hazard-band traversal mechanics.** Vary hazard_damage dose or hazard-band thickness under FOOD_NEAR1.
  - **v0.53n candidate — movement-mechanics probe.** Test alternative spawn position closer to hazard.
- **v0.54 — joint ablation.** Eventually fresh-stream calibration on the full v0.46–v0.53k stack.

## Re-anchor (locked — Tier-1 and corpus only at tick-50)

| version | published `a_share_h8` |
|---|---|
| v0.42 | 0.652 |
| v0.43R | NOT PUBLISHED (informational-only) |
| v0.44 | 0.878 |
| v0.45 | 0.818 |

## Outputs (locked)

```
runs/v0.53k-perception-sensor-radius-8/per_run_per_lineage_v053k.csv
  columns: arm, layout_name,
           safe_x_min, safe_x_max, hazard_x_min, hazard_x_max,
           food_x_min, food_x_max, world_width, spawn_x, height,
           body_starting_energy, body_base_metabolic_cost,
           body_effective_sensor_radius_override,   # NEW in v0.53k (None on A/B/D, 8 on C)
           n_ticks,
           version, seed, hazard, run_id, lineage_id,
           founder_sensor_radius, founder_reproduction_drive, founder_metabolic_rate,
           pre50_food_events_count, pre50_food_energy_acquired,
           pre100_food_events_count, pre100_food_energy_acquired,
           pre200_food_events_count, pre200_food_energy_acquired,
           pre400_food_events_count, pre400_food_energy_acquired,        # C/D only
           mean_distance_to_nearest_food_cell_tick50/100/200/400,
           tick{50,100,200,400}_living_count / above_threshold_count / above_threshold_fraction,
           b50_count, is_eventual_top_b50_label,
           is_high_sensor_radius_lineage,
           is_high_tick{50,100,200,400}_readiness_fraction_lineage

runs/v0.53k-perception-sensor-radius-8/audit_summary.csv
runs/v0.53k-perception-sensor-radius-8/audit_log.txt
```

The CSV gets one new column relative to v0.53j: `body_effective_sensor_radius_override` (`None` on A/B/D, `8` on C). This makes the perception intervention auditable per row.

## Implementation plan (locked)

1. **No `src/` changes.** All levers (`layout`, `body_config` including `effective_sensor_radius_override`, `n_ticks`) already exposed on `run_chamber()`.
2. Fresh script `scripts/v0_53k_perception_sensor_radius_8_audit.py`. CLI: `uv run python scripts/v0_53k_perception_sensor_radius_8_audit.py [--out-dir runs/v0.53k-perception-sensor-radius-8]`.
3. Define module-level constants (identical to v0.53j):
   ```python
   FOOD_NEAR1_LAYOUT = ChamberLayout(safe_x_min=0, safe_x_max=4, hazard_x_min=5, hazard_x_max=7, food_x_min=9, food_x_max=13, height=6, spawn_x=1)
   FOOD_NEAR2_LAYOUT = ChamberLayout(safe_x_min=0, safe_x_max=4, hazard_x_min=5, hazard_x_max=7, food_x_min=8, food_x_max=12, height=6, spawn_x=1)
   ```
4. C body_config: `BodyConfig(starting_energy=100.0, base_metabolic_cost=0.10, effective_sensor_radius_override=8)`.
5. D body_config: `BodyConfig(starting_energy=100.0, base_metabolic_cost=0.10)` (no override; default for that field is None).
6. Setup_observer captures founder audit table including `body.energy`, `body_config.starting_energy`, `body_config.base_metabolic_cost`, `body_config.effective_sensor_radius_override`, layout column geometry, `n_ticks` per arm at tick 0.
7. Per-tick observer: pre50/100/200 on all arms; pre400 on C and D.
8. Aggregate per-lineage primaries; compute Label A and four Label B variants.
9. Compute paired_d, reachability_run_share, population-stability metrics.
10. **Tier-1, Tier-2, Tier-3 anchors** as per v0.53j (priority 2.a–2.f).
11. **Corpus re-anchor** (priority 1): A `a_share_h8` for v0.42/v0.44/v0.45 within 1e-3.
12. **Reachability-gated PERCEPTION_OPPOSITE_SIGN_HALT** (priority 3): C tick-400 wrong-sign cells AND C reachability ≥ 0.25 → halt; otherwise descriptive log.
13. Compute slice rollup verdict; print + write the locked phrase verbatim.

The reducer is fully self-contained. Wall time estimate ~25–50 minutes.

## Test list (locked, 16 tests; mirrors v0.53j with one extra perception-override assertion in test #5)

`tests/test_v0_53k_perception_sensor_radius_8_audit.py`:

1. **`test_paired_d_function_reproduces_hand_computed_signed_d_on_fixture_and_tier1_v048_constants_and_tier3_v053i_constants`** *(three-part: hand-fixture + Tier-1 + Tier-3)*.
2. **`test_a_null_v025_corpus_a_share_h8_re_anchors_v042_v044_v045`**.
3. `test_arm_a_null_v025_uses_tight_gradient_layout_default_body_config_and_n_ticks_200_with_explicit_geometry_asserts`.
4. `test_arm_b_widened_v025_uses_widened_gradient_layout_default_body_config_and_n_ticks_200_with_explicit_geometry_asserts`.
5. **`test_arm_c_widened_food_near1_combined_sr8_N400_uses_food_near1_layout_combined_body_config_with_sensor_override_8_and_n_ticks_400_with_explicit_geometry_and_perception_asserts`**:
   - C body_config asserts: `body.energy == 100.0`, `body_config.starting_energy == 100.0`, `body_config.base_metabolic_cost == 0.10`, **`body_config.effective_sensor_radius_override == 8`** (NEW perception assert).
   - C all OTHER BodyConfig fields at default (max_energy=100.0, starting_health=100.0, max_health=100.0, sensor_radius_metabolic_cost=0.05; effective_sensor_radius_override is the ONLY new non-default field vs v0.53j).
   - C layout asserts (FOOD_NEAR1: world_width=14, food_x_min=9, food_x_max=13, hazard_x_min=5, hazard_x_max=7, safe_x_min=0, safe_x_max=4, spawn_x=1, height=6).
   - C model end-state: `_RunCapture.final_tick_count == 400`.
6. **`test_arm_d_widened_food_near2_combined_N400_uses_food_near2_layout_combined_body_config_no_sensor_override_and_n_ticks_400_with_explicit_geometry_and_perception_asserts`**:
   - D body_config asserts: `body.energy == 100.0`, `body_config.starting_energy == 100.0`, `body_config.base_metabolic_cost == 0.10`, **`body_config.effective_sensor_radius_override is None`** (NEW perception negative assert — D has NO override; matches v0.53i/j default).
   - D layout asserts (FOOD_NEAR2: world_width=13, food_x_min=8, food_x_max=12).
   - D model end-state: `_RunCapture.final_tick_count == 400`.
7. **`test_cross_arm_perception_contrast_c_has_override_8_d_has_no_override_layouts_differ_by_food_x_min`** *(new in v0.53k — verifies perception axis as the unique C/D differentiator beyond layout)*:
   - `C.body_config.effective_sensor_radius_override == 8` AND `D.body_config.effective_sensor_radius_override is None`.
   - `C.body_starting_energy == D.body_starting_energy == 100.0`; `C.body_base_metabolic_cost == D.body_base_metabolic_cost == 0.10`; `C.n_ticks == D.n_ticks == 400`.
   - `C.food_x_min == 9, D.food_x_min == 8` (layout differentiator carries forward).
   - All other layout fields identical between C and D (hazard / safe / spawn / height).
8. **`test_no_src_modifications_compared_to_v0_53e_tip`** *(two-part SHA pinning, IDENTICAL to v0.53e–v0.53j; v0.53k-named failure messages)*:
   - Part A: five science-core SHAs match v0.52b-tip (`d4521cb5...` for layouts.py).
   - Part B: chamber driver SHA `62d134c5...`.
9. `test_label_a_high_sensor_radius_lineage_picks_correct_lineage`.
10. **`test_label_b_four_variants_three_tier_tiebreak_at_each_window_with_pre400_c_and_d_only`**.
11. **`test_pre400_window_strictly_extends_pre200_pre100_pre50_windows_on_c_and_d_arms`**.
12. **`test_subverdict_present_requires_two_thirds_firing_cells_with_nan_treated_as_non_firing_strict`**.
13. **`test_priority_3_perception_opposite_sign_halt_is_reachability_gated_on_c_tick_400`** *(carries forward from v0.53i/j; halt name renamed `PERCEPTION_OPPOSITE_SIGN_HALT`)*:
    - Branch A: C tick-400 sub-verdict = OPPOSITE_SIGN_HALT, c_reachability_tick_400 = 0.30 → priority 3 fires (`PERCEPTION_OPPOSITE_SIGN_HALT`).
    - Branch B: same sub-verdict but reachability = 0.20 → priority 5 (`WIDENED_BELOW_REACHABILITY_THRESHOLD_UNDER_SENSOR_RADIUS_8`).
    - Branch C: PRESENT + reachability = 0.30 → priority 4.
14. **`test_b_widened_v025_categorical_anchor_at_tick_200_and_d_food_near2_positive_anchor_at_tick_400`** *(five independent synthetic-fixture branches; identical to v0.53j test #14)*:
    - Baseline GREEN; Tier-2 halt; Tier-3 reachability halt; Tier-3 sub-verdict halt; Tier-3 paired_d halt.
15. **`test_c_tick_400_reachability_threshold_partition`** — synthetic 0.20 / 0.30 × {PRESENT, PARTIAL, NOT_FOUND} → priorities 4/5/6 fire correctly. D anchor must pass for priorities 4/5/6 to be reachable.
16. **`test_rollup_locked_phrases_fire_verbatim_and_priority_cascade_partition_total`** — substring assertions VERBATIM:
    - Priority 3: `"AND C reachability at tick-400 clears the locked 25% threshold"` AND `"The reachability-gated trigger preserves v0.53e's locked sign discipline"` AND `"perception-only intervention (\`BodyConfig.effective_sensor_radius_override = 8\`)"`.
    - Priority 4: `"the perception-only override \`BodyConfig.effective_sensor_radius_override = 8\`"` AND `"the minimum east-ray reach from \`spawn_x=1\` to FOOD_NEAR1's \`food_x_min=9\`"` AND `"metabolic cost UNAFFECTED per the override's information-channel-only contract"` AND `"The v0.53j FOOD_NEAR1/FOOD_NEAR2 boundary is **consistent with sensor-reach being a binding constraint** under the tested envelope"` AND `"This is strong evidence but NOT exclusive causality"` AND substring references to v0.53c, v0.53d, v0.53e, v0.53f, v0.53g, v0.53h, v0.53i, v0.53j verdict names.
    - Priority 5: `"the perception-only override \`BodyConfig.effective_sensor_radius_override = 8\`"` AND `"D_widened_food_near2_combined_N400 reproduces v0.53i's \`35/64\` positive anchor at tick-400 in-slice"` AND `"The v0.53j FOOD_NEAR1/FOOD_NEAR2 boundary is **NOT explained by sensor-reach alone** under the tested envelope"` AND `"v0.53l (or later) candidates shift toward policy / hazard-avoidance / movement-mechanics probes"` AND substring references to v0.53c–v0.53j verdict names.
    - Priority 6: `"D_widened_food_near2_combined_N400 reproduces v0.53i's \`35/64\` positive anchor at tick-400 in-slice"` AND substring references to v0.53c–v0.53j verdict names.
    Synthesize halt cascade (priorities 1 / 2.a / 2.b / 2.c / 2.d / 2.e / 2.f / 3); assert priority order. Exhaustively iterate the partition; assert unique outcome per cell.

## Watch-outs (for future-Chronus)

- **No `src/` changes.** `effective_sensor_radius_override` already exposed in `BodyConfig`; v0.53e seam carries forward unchanged.
- **First perception-axis slice in the substrate-axis stack.** v0.53d–v0.53g varied body_config (energy / metabolic_cost); v0.53h varied n_ticks; v0.53i/j varied geometry; v0.53k varies perception. The substrate-axis stack is now genuinely multi-dimensional.
- **`effective_sensor_radius_override` is information-channel-only.** Per `core/sensors.py:138-142` the override drives the perception calculation; per `core/body.py:81` the metabolic-drain formula uses `traits.sensor_radius` directly. The override does NOT raise per-tick metabolic cost. This is the cost-decoupled perception lever.
- **r=8 is the MINIMUM sufficient east-ray reach to FOOD_NEAR1's food band from spawn.** spawn_x=1, ray scans `[2..r+1]`, food_x_min=9. r=7 reaches `[2..8]` (insufficient); r=8 reaches `[2..9]` (just sufficient). v0.53l candidate: r=7 to test the converse.
- **Sensor radius interacts with food-attraction signal beyond simple visibility.** Per `core/sensors.py:11`, `signal += value / distance` — the gradient is stronger when food is closer to the perceiver. Raising sensor reach allows the founder to "see" food at greater distance, but the attractive signal weakens with distance. v0.53k tests whether r=8 is sufficient for behavior; it does NOT separate visibility from gradient strength.
- **Tier-3 positive anchor on D is preserved from v0.53j** (categorical reachability + sub-verdict + six paired_d cells). v0.53j observed drift_abs = 0.0 across all six cells; v0.53k expects the same.
- **No `perception is binding` claims under priority 4.** Locked phrase: "consistent with sensor-reach being a binding constraint under the tested envelope". Not exclusive causality.
- **No `perception is irrelevant` claims under priority 5.** Bounded to this specific override (r=8) under FOOD_NEAR1 + combined-budget × n_ticks=400.
- **Locked phrase discipline verbatim.** Predecessor stack now EIGHT long: v0.53c/d/e/f/g/h/i/j.
- **Determinism north star** ([[scripts/core_smoke_test.py]]) must continue to pass. v0.53k makes no `src/` changes.

## Files this slice will create / modify

- `docs/experiments/fear_hunger_v0.53k.md` (this file; Results appended after reducer run)
- `scripts/v0_53k_perception_sensor_radius_8_audit.py` (new)
- `tests/test_v0_53k_perception_sensor_radius_8_audit.py` (new, 16 tests)

No `src/` modifications. No prior reducer / audit / test / pre-reg files modified. `layouts.py` UNCHANGED.

## Results

*(To be appended after reducer run.)*
