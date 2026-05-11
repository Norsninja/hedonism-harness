# fear_hunger v0.53m — lineage-coverage curve probe (max-only vs top-2 vs model-wide `effective_sensor_radius_override=8` at FOOD_NEAR1)

**Slice:** v0.53m
**Type:** **first-class observational sweep** with 5-arm asymmetric-horizon reducer. **Zero `src/` modifications** — v0.53l-tip's `per_founder_traits_overrides` parameter + always-consume founder-construction invariant cover all three intervention arms (max-only / top-2 / model-wide). One new reducer-local helper `build_top_k_per_founder_overrides(seed, trait_config, n_founders, k)` extends the v0.53l pre-sampling pattern to general top-K targeting.
**Predecessors:** v0.46–v0.52b (full predecessor stack), v0.53 (`BRIDGE_PARTIALLY_GENERALIZES`), v0.53b (`WIDENED_BELOW_REACHABILITY_THRESHOLD_AT_TICK_100`), v0.53c (`WIDENED_BELOW_REACHABILITY_THRESHOLD_AT_TICK_200`), v0.53d (`WIDENED_BELOW_REACHABILITY_THRESHOLD_UNDER_RELAXED_INFLUX`), v0.53e (`RELAXED_OPPOSITE_SIGN_HALT`), v0.53f (`WIDENED_BELOW_REACHABILITY_THRESHOLD_UNDER_BASE_METABOLIC_COST_010`), v0.53g (`WIDENED_BELOW_REACHABILITY_THRESHOLD_UNDER_COMBINED_SE100_BMC010`), v0.53h (`WIDENED_BELOW_REACHABILITY_THRESHOLD_AT_TIME_HORIZON_400`), v0.53i (`WIDENED_BRIDGE_RESCUED_BY_FOOD_NEAR2`), v0.53j (`WIDENED_BELOW_REACHABILITY_THRESHOLD_UNDER_FOOD_NEAR1`), v0.53k (`WIDENED_BRIDGE_PARTIALLY_RESCUED_BY_SENSOR_RADIUS_8` — model-wide override rescued reachability but Label A collapsed by construction), v0.53l (`WIDENED_BRIDGE_RESCUED_BY_MAX_LINEAGE_SENSOR_RADIUS_8` — per-lineage override on max-sensor founder restored Label A AND reachability).
**Question being asked (locked):** Where on the lineage-coverage curve does the v0.48 Label A bridge begin to dilute? With `widened_food_near1` layout + `BodyConfig(starting_energy=100.0, base_metabolic_cost=0.10)` + `n_ticks=400` held constant, does the **top-2** override scheme (the two highest-`sensor_radius` founders per run both receive `effective_sensor_radius_override=8`) preserve Label A's tick-400 bridge expression, or does adding one more boosted lineage already weaken the trait-indexed fingerprint into PARTIAL?

v0.53k and v0.53l together created a sharp two-point contrast on the lineage-coverage axis: model-wide (5 of 5 lineages boosted) collapsed Label A into the deadband; max-only (1 of 5 lineages boosted) restored Label A with `signed_d ≈ +4.4`. v0.53m measures the intermediate point — **2 of 5 lineages boosted** — to characterize where the trait-bridge fingerprint begins to dilute as more lineages gain access. The slice is deliberately focused: one new intervention arm (D top-2) plus two in-slice predecessor-reproduction anchor arms (C max-only reproducing v0.53l C; E model-wide reproducing v0.53k C) bracketing the new measurement on the same `FOOD_NEAR1 × combined-budget × n_ticks=400 × sensor-override` mechanism.

## Pre-implementation note (2026-05-10, before any reducer code)

The pre-reg's design was confirmed with the user before drafting. The key locked design points:

- **5 arms, 320 runs.** A_null_V0_25 (Tier-1 anchor); B_widened_V0_25 (Tier-2 anchor); **C_widened_food_near1_combined_max_lineage_sr8_N400** (max-only — single max-sensor founder boosted; in-slice predecessor anchor against v0.53l C published Results); **D_widened_food_near1_combined_top2_lineage_sr8_N400** (top-2 — two highest-sensor founders boosted; **the new intervention; verdict-gating on tick-400**); **E_widened_food_near1_combined_modelwide_sr8_N400** (model-wide via `body_config.effective_sensor_radius_override=8`; in-slice predecessor anchor against v0.53k C published Results). Same 64-tuple corpus shape.
- **No `src/` modifications.** v0.53l-tip's seams (chamber `per_founder_traits_overrides` + model always-consume invariant) cover all three intervention arms. `tests/sha_pins.py` carries forward unchanged. The new top-K helper lives in the v0.53m reducer module only.
- **FOOD_NEAR2 Tier-3 anchor dropped from v0.53m.** v0.53j/k/l's FOOD_NEAR2 D anchor served as a cross-layout positive-control sanity check while the substrate stack was still varying things on FOOD_NEAR1. v0.53m holds layout fixed at FOOD_NEAR1 and varies override coverage; the in-slice C/E anchors directly bracket the new D arm on the same mechanism axis, which is a stronger consistency test than a FOOD_NEAR2 sanity check. The always-consume invariant matured at v0.53l (drift_abs=0.0 on every FOOD_NEAR2 anchor cell); the byte-stability check no longer needs re-running every slice.
- **Top-2 selection rule (locked).** Sort the five founders by `traits.sensor_radius` descending, with v0.48 tiebreak `min(lineage_id)`; take the two highest. The new helper `build_top_k_per_founder_overrides(seed, trait_config, n_founders, k)` extends v0.53l's `build_c_arm_per_founder_overrides` and returns `(overrides, top_lineage_ids)`. The audit CSV records `top2_lineage_ids` per C/D run (max-only is `top2_lineage_ids[:1]` when interpreted as k=1; full `top2_lineage_ids` recorded on D and on C for cross-check).
- **Anchor cascade structure (priority 2).** Eight sub-conditions: (a) Tier-1 A tick-50 paired_d drift, (b) Tier-2 B tick-200 reachability, (c) C tick-400 reachability == 61/64 exact, (d) C tick-400 sub-verdict == BRIDGE_PRESENT, (e) C tick-400 six paired_d cells reproduce v0.53l within 1e-3, (f) E tick-400 reachability == 64/64 exact, (g) E tick-400 sub-verdict resolves to BRIDGE_PARTIAL (suffix match — E's arm prefix is different from v0.53k C's), (h) E tick-400 six paired_d cells reproduce v0.53k within 1e-3.
- **Cautious framing carries forward.** Label A's expected dilution behavior under top-2 (structural intuition: the override-targeted lineage Label A picks is one of two boosted lineages; the runner-up is in the non-label pool with equal effective sensor radius, so `delta_mean(label_a) ≈ 0.75 × max-only_delta_mean` — yielding `signed_d ≈ +3.3`) is **NOT in the verdict table**; it lives in this pre-implementation note as interpretive prior only. The verdict is empirical, not predictive. A linear-dilution model is NOT implied.
- **Random-lineage control deferred to v0.53n.** The clean arc is v0.53k (all) → v0.53l (max-only) → v0.53m (top-2) → v0.53n (random/non-max). Each slice answers one question.

## Conservation framing — observational, zero `src/` changes, single new reducer-local helper

- **No `src/` modifications.** v0.53l-tip's `fear_hunger_chamber.py` (`per_founder_traits_overrides`) and `model.py` (always-consume invariant) seams cover all three intervention arms. The science-core five files remain pinned to v0.52b-tip. Chamber driver SHA and model SHA remain at v0.53l-tip values (`tests/sha_pins.py` constants unchanged).
- **No modifications to prior reducer / audit / pre-reg / test files.** v0.53l's reducer remains byte-identical to its merged form. v0.53m's reducer reuses `_select_sensor_radius_label` (and the new sibling `_select_top_k_sensor_radius_lineages`) via cross-script import.
- **Pre-sampling pattern carries forward.** For each (version, seed, hazard) on the C, D, and E arms, the reducer pre-samples founder Traits using `make_streams(seed).mutation` + `random_traits` 5× to compute the override target set, then calls `run_chamber()` with the appropriate override list. v0.53l-tip's always-consume invariant guarantees the chamber's internal `random_traits` draws produce the same five sampled Traits regardless of override presence.
- **A_null_V0_25 arm is byte-identical to v0.48–v0.53l A_null path AT TICK-50.** Tier-1 re-anchor enforces this within 1e-3.
- **B_widened_V0_25 arm is byte-identical to v0.53–v0.53l B_widened arm at every tick 0..200.** Tier-2 categorical anchor enforces `b_widened_v025_reachability_run_share_tick_200 == 0.0`.
- **C arm is byte-identical to v0.53l C at every tick 0..400.** In-slice predecessor anchor enforces categorical reachability + sub-verdict + six paired_d cells within 1e-3 of v0.53l Results.
- **E arm is byte-identical to v0.53k C at every tick 0..400.** In-slice predecessor anchor enforces categorical reachability + sub-verdict (PARTIAL) + six paired_d cells within 1e-3 of v0.53k Results.
- **D arm differs from C by exactly one knob:** override target set is `top_lineage_ids[:2]` instead of `top_lineage_ids[:1]`. Layout, body_config, n_ticks, corpus all identical to C.
- **D arm differs from E by exactly two knobs:** override is per-lineage on top-2 (D) vs model-wide via `body_config` (E); `body_config.effective_sensor_radius_override` is `None` on D vs `8` on E. Same intervention magnitude (r=8) at different coverage.

## Test #8 SHA-pinning policy — unchanged from v0.53l-tip

`fear_hunger_chamber.py` SHA = `e9aaca0584ef763277131ab348140b186ca60d9210f34d0245239bb4217863fd` (`sha_pins.CHAMBER_DRIVER_SHA` at v0.53l-tip). `model.py` SHA = `d45413712b0fcaa1b131e0f73c237264563e6a3c9e41c69d1d2b5402fddc093b` (`sha_pins.MODEL_SHA` at v0.53l-tip). Science-core five files at v0.52b-tip historical pins. v0.53m's test #8 uses the same three-part structure as v0.53l (Part A historical; Part B chamber via sha_pins; Part C model via sha_pins).

No `sha_pins.py` updates this slice — the seams from v0.53l are sufficient. No prior test file modifications.

## Corpus (locked, 64 × 5 arms = 320 runs)

Same shape as v0.53d–v0.53l on A/B/D corpus; v0.53m adds C and E arms on the same 64-tuple to maintain matched RNG:

| version | seeds | hazards | runs per arm | total runs |
|---|---|---|---|---|
| v0.42 | 41..48 | {0, 8} | 16 | 80 |
| v0.43R | 49..56 | {0, 8} | 16 | 80 |
| v0.44 | 57..64 | {0, 8} | 16 | 80 |
| v0.45 | 65..72 | {0, 8} | 16 | 80 |
| **total** | | | | **320** |

Wall time estimate ~35–60 minutes (asymmetric: 128 runs at `n_ticks=200`, 192 runs at `n_ticks=400`).

## Arms (locked, 5)

### A_null_V0_25

```
ChamberLayout = tight_gradient_layout()
... (V0_25 baseline; body_config=None; per_founder_traits_overrides=None; n_ticks=200)
```

Byte-identical to v0.48–v0.53l A_null. **Tier-1 anchor at tick-50.**

### B_widened_V0_25

```
ChamberLayout = widened_gradient_layout()
... (V0_25 baseline; body_config=None; per_founder_traits_overrides=None; n_ticks=200)
```

Byte-identical to v0.53–v0.53l B_widened. **Tier-2 categorical anchor on tick-200 reachability.**

### C_widened_food_near1_combined_max_lineage_sr8_N400 (IN-SLICE PREDECESSOR ANCHOR vs v0.53l C)

```
ChamberLayout = ChamberLayout(  # script-local FOOD_NEAR1_LAYOUT (identical to v0.53j/k/l)
    safe_x_min=0, safe_x_max=4,
    hazard_x_min=5, hazard_x_max=7,
    food_x_min=9, food_x_max=13,
    height=6, spawn_x=1,
)
... (V0_25 baseline pool/ecology;
    body_config = BodyConfig(starting_energy=100.0, base_metabolic_cost=0.10);
    per_founder_traits_overrides[top1_lid] = Traits(..., effective_sensor_radius_override=8);
    per_founder_traits_overrides[other 4 lids] = None;
    n_ticks = 400)
```

Where `top1_lid = top_lineage_ids[0] = _select_sensor_radius_label(...)`. Byte-identical to v0.53l C at every tick 0..400. **Tier-3-equivalent in-slice anchor:** C tick-400 reachability == 61/64 exact AND sub-verdict == `C_WIDENED_FOOD_NEAR1_MAX_LINEAGE_SR8_TICK400_BRIDGE_PRESENT` AND six paired_d cells reproduce v0.53l within 1e-3.

### D_widened_food_near1_combined_top2_lineage_sr8_N400 (PRIMARY VERDICT-GATING — the new intervention)

```
ChamberLayout = FOOD_NEAR1_LAYOUT (identical to C)
... (V0_25 baseline pool/ecology;
    body_config = BodyConfig(starting_energy=100.0, base_metabolic_cost=0.10);
    per_founder_traits_overrides[top1_lid] = Traits(..., effective_sensor_radius_override=8);
    per_founder_traits_overrides[top2_lid] = Traits(..., effective_sensor_radius_override=8);  # NEW
    per_founder_traits_overrides[other 3 lids] = None;
    n_ticks = 400)
```

Differs from C by exactly one knob: the second-highest-`sensor_radius` founder also receives the override. Differs from E by override mechanism (per-lineage on top-2 vs model-wide via body_config). **The primary arm of v0.53m**: the verdict gates on D's tick-400 reachability and tick-400 sub-verdict.

### E_widened_food_near1_combined_modelwide_sr8_N400 (IN-SLICE PREDECESSOR ANCHOR vs v0.53k C)

```
ChamberLayout = FOOD_NEAR1_LAYOUT (identical to C/D)
... (V0_25 baseline pool/ecology;
    body_config = BodyConfig(
        starting_energy=100.0,
        base_metabolic_cost=0.10,
        effective_sensor_radius_override=8,  # MODEL-WIDE — matches v0.53k C
    );
    per_founder_traits_overrides = None;
    n_ticks = 400)
```

Byte-identical to v0.53k C at every tick 0..400. **Tier-3-equivalent in-slice anchor:** E tick-400 reachability == 64/64 exact AND sub-verdict suffix == `_TICK400_BRIDGE_PARTIAL` (E's arm prefix differs from v0.53k C's; categorical resolution matches) AND six paired_d cells reproduce v0.53k within 1e-3.

## Labels (locked, two — Label A definition unchanged from v0.48)

Identical to v0.53j/k/l: Label A (`is_high_sensor_radius_lineage` — selected via `_select_sensor_radius_label`); Label B variants `is_high_tick{50,100,200,400}_readiness_fraction_lineage` (tick-400 variant computed on C/D/E only; NaN-broadcast on A/B). **The C-arm intervention targets the lineage Label A picks (top-1); the D-arm intervention targets that lineage PLUS the runner-up (top-2).**

## Primary observables (locked, 3, four windows on C/D/E, three on A/B)

Identical to v0.53j/k/l. Note: observable 3 (`mean_distance_to_nearest_food_cell_tick{N}`) uses each arm's layout food cells; arms C/D/E share FOOD_NEAR1 so are directly comparable.

## Effect-size rule (locked, sign-aware, identical to v0.48–v0.53l)

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

c_widened_food_near1_combined_max_lineage_sr8_N400_reachability_run_share_tick_400 =
    (PREDECESSOR ANCHOR — must equal 61/64 = 0.953125 exactly)

d_widened_food_near1_combined_top2_lineage_sr8_N400_reachability_run_share_tick_400 =
    (VERDICT-GATING; threshold 0.25)

e_widened_food_near1_combined_modelwide_sr8_N400_reachability_run_share_tick_400 =
    (PREDECESSOR ANCHOR — must equal 64/64 = 1.0 exactly)
```

## In-slice predecessor anchors (locked, pre-data)

### C anchor (vs v0.53l C published Results, committed `e271172`)

Six paired_d cells reproduced from v0.53l Results, 1e-3 absolute tolerance:

| label | observable | published v0.53l signed_d | tolerance |
|---|---|:-:|:-:|
| `label_a_sensor_radius` | `pre400_food_events_count` | **+4.4075** (precise: `+4.407500095034808`) | 1e-3 |
| `label_a_sensor_radius` | `pre400_food_energy_acquired` | **+4.4075** | 1e-3 |
| `label_a_sensor_radius` | `mean_distance_to_nearest_food_cell_tick400` | **+3.8177** (precise: `+3.8177086030179344`) | 1e-3 |
| `label_b_readiness_fraction_tick400` | `pre400_food_events_count` | **+44.7945** (precise: `+44.79447381457056`) | 1e-3 |
| `label_b_readiness_fraction_tick400` | `pre400_food_energy_acquired` | **+44.7945** | 1e-3 |
| `label_b_readiness_fraction_tick400` | `mean_distance_to_nearest_food_cell_tick400` | **+7.2031** (precise: `+7.203121884647769`) | 1e-3 |

Plus categorical: C tick-400 reachability == 0.953125 (61/64) exact AND C tick-400 sub-verdict == `C_WIDENED_FOOD_NEAR1_MAX_LINEAGE_SR8_TICK400_BRIDGE_PRESENT`.

### E anchor (vs v0.53k C published Results, committed `65f5319`)

Six paired_d cells reproduced from v0.53k Results, 1e-3 absolute tolerance:

| label | observable | published v0.53k signed_d | tolerance |
|---|---|:-:|:-:|
| `label_a_sensor_radius` | `pre400_food_events_count` | **−0.0192** (precise: `−0.019198889380801876`) | 1e-3 |
| `label_a_sensor_radius` | `pre400_food_energy_acquired` | **−0.0192** | 1e-3 |
| `label_a_sensor_radius` | `mean_distance_to_nearest_food_cell_tick400` | **−0.0023** (precise: `−0.002295569212554338`) | 1e-3 |
| `label_b_readiness_fraction_tick400` | `pre400_food_events_count` | **+0.6978** (precise: `+0.6978345195653476`) | 1e-3 |
| `label_b_readiness_fraction_tick400` | `pre400_food_energy_acquired` | **+0.6978** | 1e-3 |
| `label_b_readiness_fraction_tick400` | `mean_distance_to_nearest_food_cell_tick400` | **+0.5879** (precise: `+0.5878534807527567`) | 1e-3 |

Plus categorical: E tick-400 reachability == 1.0 (64/64) exact AND E tick-400 sub-verdict suffix == `_TICK400_BRIDGE_PARTIAL` (arm prefix is `E_WIDENED_FOOD_NEAR1_MODELWIDE_SR8` rather than `C_WIDENED_FOOD_NEAR1_SR8`; the categorical resolution `PARTIAL` is what v0.53k C produced under the same body_config / layout / RNG configuration).

**Note on determinism:** v0.53l observed drift_abs = 0.0 across all six FOOD_NEAR2 anchor cells and across all v0.53k anchor cells embedded in v0.53l's reducer. v0.53m expects the same on both C and E anchors. The always-consume invariant (v0.53l-tip) guarantees this for both override-path (C) and no-per-founder-override-path (E).

## Per-arm sub-verdicts (locked, 4-way each — verdict-gating on D tick-400; anchors on C and E tick-400)

| condition | A_null_V0_25 | B_widened_V0_25 | C max-only (tick-400 **anchor**) | D top-2 (tick-400 **verdict-gating**) | E model-wide (tick-400 **anchor**) |
|---|---|---|---|---|---|
| both labels clear ≥ 2/3 cells, NaN non-firing, 0 wrong-sign | `A_NULL_V025_TICK{50,100,200}_BRIDGE_PRESENT` | `B_WIDENED_V025_TICK200_BRIDGE_PRESENT` | `C_WIDENED_FOOD_NEAR1_MAX_LINEAGE_SR8_TICK400_BRIDGE_PRESENT` | `D_WIDENED_FOOD_NEAR1_TOP2_LINEAGE_SR8_TICK400_BRIDGE_PRESENT` | `E_WIDENED_FOOD_NEAR1_MODELWIDE_SR8_TICK400_BRIDGE_PRESENT` |
| exactly one label clears ≥ 2/3 cells | `..._BRIDGE_PARTIAL` | ... | `..._BRIDGE_PARTIAL` | `..._BRIDGE_PARTIAL` | `..._BRIDGE_PARTIAL` |
| neither clears ≥ 2/3 cells | `..._BRIDGE_NOT_FOUND` | ... | `..._BRIDGE_NOT_FOUND` | `..._BRIDGE_NOT_FOUND` | `..._BRIDGE_NOT_FOUND` |
| any primary signed_d ≤ −0.5 | `..._OPPOSITE_SIGN_HALT` | ... | `..._OPPOSITE_SIGN_HALT` | `..._OPPOSITE_SIGN_HALT` | `..._OPPOSITE_SIGN_HALT` |

**Strict NaN-treated-as-non-firing rule preserved.** D's sub-verdict prefix is `D_WIDENED_FOOD_NEAR1_TOP2_LINEAGE_SR8_TICK{N}_BRIDGE_{...}`. E's sub-verdict prefix is `E_WIDENED_FOOD_NEAR1_MODELWIDE_SR8_TICK{N}_BRIDGE_{...}`.

## Slice rollup verdicts (locked, 6 outcomes, priority-ordered)

1. `CORPUS_REDERIVE_DRIFT_HALT`
2. `ANCHOR_REPLICATION_HALT` (Tier-1 + Tier-2 + C in-slice anchor + E in-slice anchor; eight sub-conditions)
3. `TOP2_LINEAGE_PERCEPTION_OPPOSITE_SIGN_HALT` (**reachability-gated** on D tick-400)
4. `WIDENED_BRIDGE_RESCUED_BY_TOP2_LINEAGE_SENSOR_RADIUS_8`
5. `WIDENED_BELOW_REACHABILITY_THRESHOLD_UNDER_TOP2_LINEAGE_SENSOR_RADIUS_8`
6. `WIDENED_BRIDGE_PARTIALLY_RESCUED_BY_TOP2_LINEAGE_SENSOR_RADIUS_8`

### Halt conditions

| priority | rollup verdict | trigger | locked phrase (verbatim) |
|---|---|---|---|
| 1 | `CORPUS_REDERIVE_DRIFT_HALT` | A `a_share_h8` for v0.42/v0.44/v0.45 drifts > 1e-3 | "Halt: A_null_V0_25 re-anchor drifted from the published Results value for {version}; v0.53m's deterministic re-execution of the V0_25 corpus does not reproduce the published metric within 1e-3." |
| 2 | `ANCHOR_REPLICATION_HALT` | (a) A tick-50 paired_d drift > 1e-3, (b) A tick-50 sub-verdict ≠ PRESENT, (c) B tick-200 reachability ≠ 0, (d) C tick-400 reachability ≠ 61/64 exact, (e) C tick-400 sub-verdict ≠ `C_WIDENED_FOOD_NEAR1_MAX_LINEAGE_SR8_TICK400_BRIDGE_PRESENT`, (f) C tick-400 six paired_d cells drift > 1e-3 vs v0.53l, (g) E tick-400 reachability ≠ 64/64 exact, (h) E tick-400 sub-verdict suffix ≠ `_TICK400_BRIDGE_PARTIAL` OR six paired_d cells drift > 1e-3 vs v0.53k | "Halt: v0.53m's A_null_V0_25 arm does not reproduce v0.48–v0.53l's tick-50 spatial bridge, OR v0.53m's B_widened_V0_25 arm does not reproduce v0.53c–v0.53l's `0/64` reachability lock at tick-200, OR v0.53m's C_widened_food_near1_combined_max_lineage_sr8_N400 arm does not reproduce v0.53l's tick-400 anchor (categorical reachability `61/64` AND sub-verdict `BRIDGE_PRESENT` AND six published paired_d cells within 1e-3), OR v0.53m's E_widened_food_near1_combined_modelwide_sr8_N400 arm does not reproduce v0.53k's tick-400 anchor (categorical reachability `64/64` AND categorical resolution `PARTIAL` AND six published paired_d cells within 1e-3). v0.53m cannot interpret the D_widened_food_near1_combined_top2_lineage_sr8_N400 cells without reproducing both the V0_25 baseline anchors AND both heterogeneity-coverage anchors that bracket the top-2 measurement on the same FOOD_NEAR1 × combined-budget × n_ticks=400 mechanism axis." |
| 3 | `TOP2_LINEAGE_PERCEPTION_OPPOSITE_SIGN_HALT` (**reachability-gated**) | D tick-400 sub-verdict = `OPPOSITE_SIGN_HALT` AND `d_reachability_tick_400 ≥ 0.25` | "Halt: a v0.53m D_widened_food_near1_combined_top2_lineage_sr8_N400 tick-400 spatial / foraging primary fires in the WRONG direction under a gating label, AND D reachability at tick-400 clears the locked 25% threshold. The top-2 per-lineage perception intervention (`per_founder_traits_overrides[top_lineage_ids[0]] = per_founder_traits_overrides[top_lineage_ids[1]] = Traits(effective_sensor_radius_override=8)`) under FOOD_NEAR1 + combined founder-facing budget envelope at `n_ticks = 400` surfaces a regime where the locked expected signs do not hold under measurable food access. The reachability-gated trigger preserves v0.53e's locked sign discipline while excluding the v0.53e-style measurement-edge case (wrong-sign at reachability=0)." |

### Outcome conditions (only consulted if no halt fires)

| priority | rollup verdict | trigger | locked phrase (verbatim) |
|---|---|---|---|
| 4 | `WIDENED_BRIDGE_RESCUED_BY_TOP2_LINEAGE_SENSOR_RADIUS_8` | `d_reachability_run_share_tick_400 ≥ 0.25` AND D tick-400 sub-verdict = `D_WIDENED_FOOD_NEAR1_TOP2_LINEAGE_SR8_TICK400_BRIDGE_PRESENT` | "On the modern A_null corpus with the V0_25 substrate held constant except for the combined founder-facing budget relaxation `BodyConfig(starting_energy=100.0, base_metabolic_cost=0.10)` AND the simulation horizon doubled to `n_ticks=400` AND the `widened_food_near1` layout AND the **top-2** per-lineage perception intervention `per_founder_traits_overrides[top_lineage_ids[0]] = per_founder_traits_overrides[top_lineage_ids[1]] = Traits(effective_sensor_radius_override=8)` (the override applies to the TWO highest-`sensor_radius` founders per run; the v0.48 `is_high_sensor_radius_lineage` selector picks `top_lineage_ids[0]` — the same lineage Label A indexes; metabolic cost UNAFFECTED per the override's information-channel-only contract; override propagates to all descendants via `dataclasses.replace`'s preservation), the v0.48 sensor_radius spatial / foraging bridge fires PRESENT under the locked +0.5 paired_d threshold at tick-400 under both gating labels. The geometry/substrate cell that v0.53c locked as `WIDENED_BELOW_REACHABILITY_THRESHOLD_AT_TICK_200`, v0.53d locked as `WIDENED_BELOW_REACHABILITY_THRESHOLD_UNDER_RELAXED_INFLUX`, v0.53e locked as `RELAXED_OPPOSITE_SIGN_HALT`, v0.53f locked as `WIDENED_BELOW_REACHABILITY_THRESHOLD_UNDER_BASE_METABOLIC_COST_010`, v0.53g locked as `WIDENED_BELOW_REACHABILITY_THRESHOLD_UNDER_COMBINED_SE100_BMC010`, v0.53h locked as `WIDENED_BELOW_REACHABILITY_THRESHOLD_AT_TIME_HORIZON_400`, v0.53i locked as `WIDENED_BRIDGE_RESCUED_BY_FOOD_NEAR2`, v0.53j locked as `WIDENED_BELOW_REACHABILITY_THRESHOLD_UNDER_FOOD_NEAR1`, v0.53k locked as `WIDENED_BRIDGE_PARTIALLY_RESCUED_BY_SENSOR_RADIUS_8`, and v0.53l locked as `WIDENED_BRIDGE_RESCUED_BY_MAX_LINEAGE_SENSOR_RADIUS_8` admits a measurable bridge at the top-2 coverage point on the lineage-perception curve: C_widened_food_near1_combined_max_lineage_sr8_N400 reproduces v0.53l's `61/64` anchor at tick-400 (max-only lock holds), E_widened_food_near1_combined_modelwide_sr8_N400 reproduces v0.53k's `64/64` anchor at tick-400 (model-wide lock holds), D reachability at tick-400 clears the locked 25% threshold, and ≥ 2/3 spatial / foraging primaries fire PRESENT under both gating labels at the D tick-400 panel. **The v0.48 bridge tolerates at least 2/5 lineage-level perception access, under the locked top-2-by-sensor-radius selection rule, under FOOD_NEAR1 × combined-budget × n_ticks=400 without collapsing Label A.** This is strong evidence but NOT exclusive causality and NOT a minimal-sufficient-heterogeneity claim — v0.53m only tests one intermediate coverage point; the tolerance threshold may lie anywhere in [2/5, 5/5). This does NOT prove `the v0.48 bridge is monotone over coverage`; NOT `top-2 is the minimum-tolerable coverage`: `WIDENED_BRIDGE_RESCUED_BY_TOP2_LINEAGE_SENSOR_RADIUS_8`." |
| 5 | `WIDENED_BELOW_REACHABILITY_THRESHOLD_UNDER_TOP2_LINEAGE_SENSOR_RADIUS_8` | `d_reachability_run_share_tick_400 < 0.25` | "On the modern A_null corpus with the V0_25 substrate held constant except for the combined founder-facing budget relaxation AND the simulation horizon doubled to `n_ticks=400` AND the `widened_food_near1` layout AND the top-2 per-lineage perception intervention, fewer than 25% of D runs have any founder lineage with pre400 food events. If top-2 fails to restore reachability despite both max-only and model-wide predecessor anchors reproducing, v0.53m records a bounded anomaly: the selected top-2 lineage intervention does not reproduce the expected coverage interpolation under this corpus and implementation. Implementation/selection diagnostics should be reviewed before assigning mechanistic interpretation: `WIDENED_BELOW_REACHABILITY_THRESHOLD_UNDER_TOP2_LINEAGE_SENSOR_RADIUS_8`." |
| 6 | `WIDENED_BRIDGE_PARTIALLY_RESCUED_BY_TOP2_LINEAGE_SENSOR_RADIUS_8` | `d_reachability_run_share_tick_400 ≥ 0.25` AND D tick-400 sub-verdict ∈ {PARTIAL, NOT_FOUND} | "On the modern A_null corpus with the V0_25 substrate held constant except for the combined founder-facing budget relaxation AND the top-2 per-lineage perception intervention on FOOD_NEAR1 at `n_ticks=400`, D's reachability clears the locked 25% threshold at tick-400 but the v0.48 sensor_radius spatial / foraging bridge does not fully fire PRESENT — fewer than 2/3 primaries fire across both gating labels at tick-400 under the strict NaN rule. C_widened_food_near1_combined_max_lineage_sr8_N400 reproduces v0.53l's `61/64` anchor at tick-400 in-slice; E_widened_food_near1_combined_modelwide_sr8_N400 reproduces v0.53k's `64/64` anchor at tick-400 in-slice. **Access remains rescued, but the original trait bridge begins diluting once boosted access extends beyond the single max-sensor lineage.** This justifies a v0.53n random/non-max control to test whether the dilution is access-position-mediated (Label A picks one boosted lineage; runner-up is in non-label pool with equal effective sensor radius) or trait-saturation-mediated (additional lineage perception saturates the food-availability signal regardless of which lineage receives the boost). Layout-specific partial-rescue logged in Results: `WIDENED_BRIDGE_PARTIALLY_RESCUED_BY_TOP2_LINEAGE_SENSOR_RADIUS_8`." |

The 3 non-halt outcomes form a total partition (same shape as v0.53j/k/l). Test #16 enforces the partition exhaustively.

## Cautious framing (per CLAUDE.md, refined per user direction)

- **"The v0.48 bridge tolerates at least 2/5 lineage-level perception access, under the locked top-2-by-sensor-radius selection rule, under FOOD_NEAR1 × combined-budget × n_ticks=400 without collapsing Label A"** (priority 4) — NOT "top-2 is the minimum-tolerable coverage"; NOT "the bridge is monotone over coverage"; NOT "any 2-of-5 lineage selection tolerates the bridge". v0.53m tests one intermediate coverage point with one specific selection rule (top-2 by `sensor_radius`); the tolerance threshold under other selection rules is untested.
- **"Access remains rescued, but the original trait bridge begins diluting once boosted access extends beyond the single max-sensor lineage"** (priority 6) — NOT "the bridge is destroyed by top-2"; NOT "max-only is the unique optimum". The partial-rescue outcome motivates v0.53n's random-lineage control.
- The structural-concentration intuition for Label B (carried forward from v0.53l Results) applies under top-2 with TWO boosted lineages in the high-readiness pool: Label B magnitudes will be smaller than max-only's `+44.79` because the contrast is now `high − (high + 0 + 0 + 0)/4 ≈ 3*high/4` instead of `high − (0 + 0 + 0 + 0)/4 = high`. This is descriptive, not verdict-gating.
- v0.53m explicitly does not establish: cross-coverage interpolation between max-only / top-2 / model-wide (linear or non-linear), behavior at top-3 or top-4 coverage, generalization to non-V0_25 substrates, behavior at non-`n_ticks=400` horizons, dose-response on the `r=8` magnitude axis under top-2, behavior under reproduction failure (if either targeted founder dies before reproducing, the override is lost from that lineage — descriptively logged), trait-vs-access disambiguation (deferred to v0.53n random/non-max control).

## What v0.53m cannot establish

- ✗ **"Top-2 is the minimum-tolerable coverage."** v0.53m tests one intermediate point. The bridge may also tolerate top-3 or top-4 — or it may NOT tolerate top-2 (priority 6 outcome).
- ✗ **"The v0.48 bridge is monotone over coverage."** A non-monotone trade-off curve is consistent with the data even under priority 4.
- ✗ **Trait-vs-access disambiguation.** Both max-only (v0.53l) and top-2 (v0.53m) target the highest-`sensor_radius` lineage(s). Whether the Label A firing in priority 4 reflects the underlying trait OR the access channel cannot be disambiguated until v0.53n's random-lineage control runs.
- ✗ **A revised v0.53–v0.53l verdict.** All twelve predecessor verdicts stand as historical contracts.
- ✗ **Mechanism behind any rescue or non-rescue outcome.** Population dynamics under V0_25 × FOOD_NEAR1 × combined-budget × `n_ticks=400` × top-2 `r=8` are descriptively logged; no mechanism is formally established.

## Open framing (NOT in v0.53m primary)

- **If priority 4 fires (top-2 rescues with full Label A expression):** the bridge tolerates 2/5 coverage. v0.53n random-lineage control becomes critical for disambiguating trait vs access. v0.53o candidate: top-3 / top-4 to map the dilution curve.
- **If priority 6 fires (top-2 partial rescue):** dilution begins between coverage 1/5 and 2/5. v0.53n random-lineage control is even more important for disambiguating mechanism. v0.53o candidate: dose-response on the override magnitude axis at top-2 coverage.
- **If priority 5 fires (D below threshold):** very surprising. Re-run C and E in-slice; if both reproduce, surface immediately for diagnostic review before scientific interpretation.
- **v0.53n — random-lineage / non-max-lineage control.** Assign `r=8` to a NON-max lineage (e.g., min-sensor lineage). If Label A still fires, the v0.48 bridge is more access-mediated than trait-mediated. If Label A does NOT fire, the trait-correlation requires the override AND the trait to coincide.
- **v0.53o — dose-response on `r=8` magnitude under per-lineage scheme.** Test r=6, r=7, r=10 at max-only and at top-2.
- **v0.54 — joint ablation.** Eventually fresh-stream calibration on the full v0.46–v0.53m stack.

## Re-anchor (locked — Tier-1 and corpus only at tick-50)

| version | published `a_share_h8` |
|---|---|
| v0.42 | 0.652 |
| v0.43R | NOT PUBLISHED (informational-only) |
| v0.44 | 0.878 |
| v0.45 | 0.818 |

## Outputs (locked)

```
runs/v0.53m-perception-top2-lineage-sensor-radius-8/per_run_per_lineage_v053m.csv
  columns: arm, layout_name,
           safe_x_min, safe_x_max, hazard_x_min, hazard_x_max,
           food_x_min, food_x_max, world_width, spawn_x, height,
           body_starting_energy, body_base_metabolic_cost,
           body_effective_sensor_radius_override,                    # 8 on E rows; None elsewhere
           founder_effective_sensor_radius_override,                 # 8 on C max-sensor + D top-2 founders; None elsewhere
           is_max_sensor_lineage_in_run,                             # True iff lineage_id == top_lineage_ids[0]
           is_top2_sensor_lineage_in_run,                            # NEW in v0.53m: True iff lineage_id ∈ top_lineage_ids[:2]
           top1_lineage_id_in_run,                                   # NEW in v0.53m: int (the max-sensor lineage_id)
           top2_lineage_id_in_run,                                   # NEW in v0.53m: int (the second-highest-sensor lineage_id)
           top1_sensor_radius_in_run,                                # NEW in v0.53m: int (top-1 founder's sampled sensor_radius)
           top2_sensor_radius_in_run,                                # NEW in v0.53m: int (top-2 founder's sampled sensor_radius)
           n_ticks,
           version, seed, hazard, run_id, lineage_id,
           founder_sensor_radius, founder_reproduction_drive, founder_metabolic_rate,
           pre50_food_events_count, pre50_food_energy_acquired,
           pre100_food_events_count, pre100_food_energy_acquired,
           pre200_food_events_count, pre200_food_energy_acquired,
           pre400_food_events_count, pre400_food_energy_acquired,        # C/D/E only
           mean_distance_to_nearest_food_cell_tick50/100/200/400,
           tick{50,100,200,400}_living_count / above_threshold_count / above_threshold_fraction,
           b50_count, is_eventual_top_b50_label,
           is_high_sensor_radius_lineage,
           is_high_tick{50,100,200,400}_readiness_fraction_lineage

runs/v0.53m-perception-top2-lineage-sensor-radius-8/audit_summary.csv
runs/v0.53m-perception-top2-lineage-sensor-radius-8/audit_log.txt
```

Six new columns relative to v0.53l: `is_top2_sensor_lineage_in_run`, `top1_lineage_id_in_run`, `top2_lineage_id_in_run`, `top1_sensor_radius_in_run`, `top2_sensor_radius_in_run` (the sampled `sensor_radius` values for the two targeted founders — eases later interpretation of ties or narrow top-2 gaps), and the carry-forward `is_max_sensor_lineage_in_run` (which equals `lineage_id == top1_lineage_id_in_run`). The `founder_effective_sensor_radius_override` column gets `8` on C max-sensor founder + D top-2 founders; `None` elsewhere (A/B/E founders + non-targeted C/D founders).

## Implementation plan (locked)

1. **Zero `src/` changes.** v0.53l-tip seams cover everything.
2. Fresh script `scripts/v0_53m_perception_top2_lineage_sensor_radius_8_audit.py`. CLI: `uv run python scripts/v0_53m_perception_top2_lineage_sensor_radius_8_audit.py [--out-dir runs/v0.53m-perception-top2-lineage-sensor-radius-8]`.
3. Define module-level constants identical to v0.53l: `FOOD_NEAR1_LAYOUT` (FOOD_NEAR2 NOT needed in this slice).
4. Reuse `_select_sensor_radius_label` from v0.53k's reducer via cross-script import (CLAUDE.md pattern).
5. Define a new sibling helper `_select_top_k_sensor_radius_lineages(sensor_radius_by_lineage, k)` in v0.53m's reducer (returns `list[int]` of top-K lineage_ids, descending by sensor_radius with `min(lineage_id)` tiebreak). Single-element output (k=1) must match `_select_sensor_radius_label`'s output exactly.
6. Pre-sampling helper `build_top_k_per_founder_overrides(seed, trait_config, n_founders, k)` replicates `make_streams(seed).mutation` + `random_traits` `n_founders` times, computes `top_lineage_ids = _select_top_k_sensor_radius_lineages(..., k)`, and constructs `overrides` where targeted lineages get `dataclasses.replace(sampled[lid], effective_sensor_radius_override=8)` and others get `None`. Returns `(overrides, top_lineage_ids)`.
7. C arm: `k=1` (max-only). D arm: `k=2` (top-2). E arm: `per_founder_traits_overrides=None`; `body_config.effective_sensor_radius_override=8`.
8. Setup_observer captures founder audit table including per-trait override field (per v0.53l pattern); also records `top1_lineage_id_in_run`, `top2_lineage_id_in_run`, `top1_sensor_radius_in_run`, and `top2_sensor_radius_in_run` per C/D run for the new CSV columns. (The sensor-radius values are the pre-sampled `int(sampled[top_lid].sensor_radius)` from `build_top_k_per_founder_overrides`; they ease later interpretation of ties or narrow top-2 gaps.)
9. Per-tick observer: pre50/100/200 on all arms; pre400 on C/D/E.
10. Aggregate per-lineage primaries; compute Label A and four Label B variants. Label A definition uses the same `_select_sensor_radius_label` selector applied to founder Traits (top_lineage_ids[0]).
11. Compute paired_d, reachability_run_share, population-stability metrics for each arm.
12. **In-slice predecessor anchors** (priority 2 sub-conditions c-h): C tick-400 reachability + sub-verdict + six paired_d cells; E tick-400 reachability + sub-verdict suffix + six paired_d cells.
13. **Corpus re-anchor** (priority 1): A `a_share_h8` for v0.42/v0.44/v0.45 within 1e-3.
14. **Reachability-gated TOP2_LINEAGE_PERCEPTION_OPPOSITE_SIGN_HALT** (priority 3): D tick-400 wrong-sign cells AND D reachability ≥ 0.25 → halt; otherwise descriptive log.
15. Compute slice rollup verdict; print + write the locked phrase verbatim.

Wall time estimate ~35–60 minutes. C and E arms each replay published predecessor configurations; D is the only genuinely new computation.

## Test list (locked, 16 tests; mirrors v0.53l with anchor-cascade and arm-count expansions)

`tests/test_v0_53m_perception_top2_lineage_sensor_radius_8_audit.py`:

1. **`test_paired_d_function_reproduces_hand_computed_signed_d_on_fixture_AND_tier1_v048_constants_AND_v053l_published_C_anchor_AND_v053k_published_E_anchor`** *(four-part: hand-fixture + Tier-1 + v0.53l C anchor + v0.53k E anchor)*.
2. **`test_a_null_v025_corpus_a_share_h8_re_anchors_v042_v044_v045`**.
3. `test_arm_a_null_v025_uses_tight_gradient_layout_default_body_config_and_n_ticks_200_with_explicit_geometry_asserts`.
4. `test_arm_b_widened_v025_uses_widened_gradient_layout_default_body_config_and_n_ticks_200_with_explicit_geometry_asserts`.
5. **`test_arm_c_widened_food_near1_combined_max_lineage_sr8_N400_uses_food_near1_layout_per_founder_override_on_max_sensor_lineage_only_and_n_ticks_400_with_explicit_geometry_and_per_lineage_perception_asserts`** *(byte-identical to v0.53l #5; verifies in-slice anchor configuration)*.
6. **`test_arm_d_widened_food_near1_combined_top2_lineage_sr8_N400_uses_food_near1_layout_per_founder_override_on_top2_sensor_lineages_and_n_ticks_400_with_explicit_geometry_and_top2_perception_asserts`** *(NEW)*:
   - D body_config asserts: `body_config.effective_sensor_radius_override is None`.
   - D layout asserts (FOOD_NEAR1).
   - **Per-founder asserts:** exactly 2 of 5 founders have `body.traits.effective_sensor_radius_override == 8`; those two are `top_lineage_ids[:2]` from `_select_top_k_sensor_radius_lineages(..., k=2)`; the OTHER 3 founders have it `None`.
   - D `_RunCapture.final_tick_count <= 400`.
7. **`test_arm_e_widened_food_near1_combined_modelwide_sr8_N400_uses_food_near1_layout_body_config_override_8_no_per_founder_override_and_n_ticks_400_with_explicit_geometry_and_modelwide_perception_asserts`** *(NEW, anchor-reproduction shape)*:
   - E body_config asserts: `body_config.effective_sensor_radius_override == 8`.
   - **Negative per-founder asserts:** ALL 5 E founders have `body.traits.effective_sensor_radius_override is None`.
   - E layout asserts (FOOD_NEAR1).
   - E `_RunCapture.final_tick_count <= 400`.
8. **`test_no_src_modifications_compared_to_v0_53l_tip`** *(three-part SHA pinning via shared `tests/sha_pins.py`; UNCHANGED from v0.53l's test #8 — confirms no `sha_pins` updates this slice)*:
   - Part A: science-core five files at v0.52b-tip historical pins.
   - Part B: `fear_hunger_chamber.py` matches `sha_pins.CHAMBER_DRIVER_SHA` (still v0.53l-tip).
   - Part C: `model.py` matches `sha_pins.MODEL_SHA` (still v0.53l-tip).
9. **`test_top_k_helper_and_top2_per_founder_override_targeting`** *(NEW; validates the new top-K helper + the override targeting at k=2)*:
   - `_select_top_k_sensor_radius_lineages` returns the top K lineages by sensor_radius (descending) with `min(lineage_id)` tiebreak.
   - k=1 output matches `_select_sensor_radius_label`'s output exactly (single-element).
   - k=2 returns exactly 2 lineage_ids in descending sensor_radius order.
   - Tiebreak: `{0: 6, 1: 6, 2: 6, 3: 4, 4: 5}` with k=2 returns `[0, 1]` (both have sensor_radius=6; `min(lineage_id)` picks 0 first, then 1).
   - `build_top_k_per_founder_overrides(seed, trait_config, n_founders=5, k=2)` returns `(overrides, top_lineage_ids)` where exactly 2 of the 5 overrides are non-None and those positions match `top_lineage_ids`.
10. **`test_per_founder_traits_overrides_seam_validation_carries_forward_from_v0_53l`** *(carry-forward; subset of v0.53l #9)*:
    - Mutual exclusivity raises `ValueError`.
    - Length validation raises `ValueError`.
    - Default-preserving: `per_founder_traits_overrides=None` is byte-identical to no argument.
11. **`test_label_a_high_sensor_radius_lineage_picks_correct_lineage_AND_matches_c_max_only_target_AND_top2_first_element_on_d`**:
    - On C: Label A picks `top_lineage_ids[0]` per run == the lineage targeted by the C max-only override.
    - On D: Label A picks `top_lineage_ids[0]` per run == the first element of `top_lineage_ids[:2]` (i.e., the same lineage Label A picks on C under matched seed).
12. **`test_label_b_four_variants_three_tier_tiebreak_at_each_window_with_pre400_c_d_and_e_only`**.
13. **`test_pre400_window_strictly_extends_pre200_pre100_pre50_windows_on_c_d_and_e_arms`**.
14. **`test_subverdict_present_requires_two_thirds_firing_cells_with_nan_treated_as_non_firing_strict`**.
15. **`test_priority_3_top2_lineage_perception_opposite_sign_halt_is_reachability_gated_on_d_tick_400`** *(carries forward from v0.53l test #14; halt name renamed `TOP2_LINEAGE_PERCEPTION_OPPOSITE_SIGN_HALT`)*:
    - Branch A: D tick-400 sub-verdict = OPPOSITE_SIGN_HALT, d_reachability_tick_400 = 0.30 → priority 3 fires.
    - Branch B: same sub-verdict but reachability = 0.20 → priority 5.
    - Branch C: PRESENT + reachability = 0.30 → priority 4.
16. **`test_v053l_C_and_v053k_E_in_slice_anchors_AND_rollup_locked_phrases_fire_verbatim_AND_priority_cascade_partition_total`** *(NEW comprehensive — combines v0.53l #15 anchor branches with v0.53l #16 locked-phrase substring asserts; tests both in-slice anchors AND the partition exhaustiveness)*:
    - Anchor branches (8 independent synthetic-fixture branches; priority 2 sub-conditions a-h):
      - Baseline GREEN (all anchors hold; priorities 4/5/6 reachable).
      - 2.a Tier-1 A drift halt.
      - 2.b Tier-2 B reachability halt.
      - 2.c C reachability drift halt.
      - 2.d C sub-verdict drift halt.
      - 2.e C paired_d drift halt.
      - 2.f E reachability drift halt.
      - 2.g E sub-verdict drift halt.
      - 2.h E paired_d drift halt.
    - Substring assertions VERBATIM from priority 4/5/6 locked phrases:
      - Priority 4: `"the **top-2** per-lineage perception intervention"` AND `"per_founder_traits_overrides[top_lineage_ids[0]] = per_founder_traits_overrides[top_lineage_ids[1]] = Traits(effective_sensor_radius_override=8)"` AND `"The v0.48 bridge tolerates at least 2/5 lineage-level perception access, under the locked top-2-by-sensor-radius selection rule, under FOOD_NEAR1 × combined-budget × n_ticks=400 without collapsing Label A"` AND substring references to v0.53c, v0.53d, v0.53e, v0.53f, v0.53g, v0.53h, v0.53i, v0.53j, v0.53k, v0.53l verdict names (TEN-long predecessor stack).
      - Priority 5: substring references to in-slice C / E anchor language AND `"v0.53m records a bounded anomaly"` AND `"Implementation/selection diagnostics should be reviewed before assigning mechanistic interpretation"`.
      - Priority 6: `"Access remains rescued, but the original trait bridge begins diluting once boosted access extends beyond the single max-sensor lineage"` AND `"This justifies a v0.53n random/non-max control"` AND substring references to v0.53c–v0.53l verdict names.
    - Synthesize halt cascade (priorities 1 / 2.a-2.h / 3); assert priority order. Exhaustively iterate the partition; assert unique outcome per cell.

## Watch-outs (for future-Chronus)

- **Zero `src/` changes** in v0.53m. v0.53l-tip seams cover all three intervention arms. `sha_pins.py` unchanged. Test #8 unchanged from v0.53l-tip structure.
- **Top-2 selection rule** must use `_select_sensor_radius_label` (k=1) and `_select_top_k_sensor_radius_lineages(..., k=2)` consistently. Tiebreak is `min(lineage_id)` (v0.48 rule, carried forward).
- **Pre-sampling determinism carries forward.** `build_top_k_per_founder_overrides` extends `build_c_arm_per_founder_overrides` from v0.53l. The always-consume invariant (v0.53l-tip) guarantees no RNG drift on non-targeted founders.
- **In-slice C/E anchors are the new Tier-3-equivalent.** FOOD_NEAR2 NOT carried forward in this slice; the always-consume invariant maturity at v0.53l empirically discharged the byte-stability check on FOOD_NEAR2.
- **Top-2 dilution intuition** (~0.75 × max-only signed_d under Label A) is interpretive prior, NOT a locked threshold. The verdict is empirical.
- **Predecessor stack now TEN long**: v0.53c/d/e/f/g/h/i/j/k/l.
- **Bulk metadata rename trap** (caught the v0.53i→v0.53j build): when copying v0.53l templates as starting seed, predecessor refs to `v0.53l` (and earlier) in priority-4/5/6 locked phrases AND test #16 substring assertions must be PRESERVED VERBATIM, NOT bulk-replaced to v0.53m. Only the slice's own self-reference becomes v0.53m.
- **Label B magnitude under top-2** is expected to be smaller than v0.53l's `+44.79` due to structural concentration (TWO boosted lineages in the high-readiness pool instead of one). Descriptive only.
- **D tick-400 reachability < 25% should never happen** under priority 5. If it does, treat as implementation halt first, not scientific finding.

## Files this slice will create / modify

**New files:**
- `docs/experiments/fear_hunger_v0.53m.md` (this file; Results appended after reducer run)
- `scripts/v0_53m_perception_top2_lineage_sensor_radius_8_audit.py`
- `tests/test_v0_53m_perception_top2_lineage_sensor_radius_8_audit.py` (16 tests)

**No `src/` modifications.** No prior reducer / audit / pre-reg / test file modifications. `tests/sha_pins.py` UNCHANGED.

## Results

*(To be appended after reducer run.)*
