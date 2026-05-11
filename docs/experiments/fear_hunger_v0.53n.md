# fear_hunger v0.53n — alignment-control / negative-control on the lineage-perception axis (min-sensor lineage `effective_sensor_radius_override=8` under FOOD_NEAR1 × combined-budget × n_ticks=400)

**Slice:** v0.53n
**Type:** **alignment-control / negative-control sweep** with 5-arm asymmetric-horizon reducer. **Zero `src/` modifications** — v0.53l-tip's `per_founder_traits_overrides` parameter + always-consume founder-construction invariant cover all three intervention arms (max-only / min-only / model-wide). One new reducer-local helper `build_bottom_k_per_founder_overrides(seed, trait_config, n_founders, k)` mirrors v0.53m's `build_top_k_per_founder_overrides` shape — same pre-sampling pattern, argmin-with-`min(lineage_id)`-tiebreak selection instead of argmax.
**Predecessors:** v0.46–v0.52b (full predecessor stack), v0.53 (`BRIDGE_PARTIALLY_GENERALIZES`), v0.53b (`WIDENED_BELOW_REACHABILITY_THRESHOLD_AT_TICK_100`), v0.53c (`WIDENED_BELOW_REACHABILITY_THRESHOLD_AT_TICK_200`), v0.53d (`WIDENED_BELOW_REACHABILITY_THRESHOLD_UNDER_RELAXED_INFLUX`), v0.53e (`RELAXED_OPPOSITE_SIGN_HALT`), v0.53f (`WIDENED_BELOW_REACHABILITY_THRESHOLD_UNDER_BASE_METABOLIC_COST_010`), v0.53g (`WIDENED_BELOW_REACHABILITY_THRESHOLD_UNDER_COMBINED_SE100_BMC010`), v0.53h (`WIDENED_BELOW_REACHABILITY_THRESHOLD_AT_TIME_HORIZON_400`), v0.53i (`WIDENED_BRIDGE_RESCUED_BY_FOOD_NEAR2`), v0.53j (`WIDENED_BELOW_REACHABILITY_THRESHOLD_UNDER_FOOD_NEAR1`), v0.53k (`WIDENED_BRIDGE_PARTIALLY_RESCUED_BY_SENSOR_RADIUS_8` — model-wide override rescued reachability but Label A collapsed by construction), v0.53l (`WIDENED_BRIDGE_RESCUED_BY_MAX_LINEAGE_SENSOR_RADIUS_8` — per-lineage override on max-sensor founder restored Label A AND reachability), v0.53m (`WIDENED_BRIDGE_RESCUED_BY_TOP2_LINEAGE_SENSOR_RADIUS_8` — top-2 coverage preserves Label A bridge with sharper-than-expected dilution; coverage curve mapped at 1/5 → 2/5 → 5/5 with monotone Label A decay and monotone survival increase).

**Question being asked (locked, verbatim per user direction):** Does assigning r=8 perception access to the lowest-sensor founder lineage rescue reachability without rescuing the original max-sensor Label A bridge, under FOOD_NEAR1 × combined-budget × n_ticks=400?

v0.53k/l/m together mapped the **lineage-coverage curve** at three coverage points where the override was always assigned to the highest-sensor lineage(s): model-wide (5/5; v0.53k) collapsed Label A into the deadband; top-2 (2/5; v0.53m) preserved Label A with sharper-than-expected dilution; max-only (1/5; v0.53l) restored Label A with `signed_d ≈ +4.4`. All three v0.53k/l/m arms confound two variables: the COVERAGE of the perception boost AND the ALIGNMENT of the boost with the max-sensor lineage that Label A indexes. v0.53n disentangles those two variables by holding coverage fixed at 1/5 (matching v0.53l) while inverting alignment: the override is assigned to the **min-sensor** lineage (`argmin(sensor_radius)`, `min(lineage_id)` tiebreak) per run, the absolute lowest perceiver instead of the absolute highest. The v0.48 `is_high_sensor_radius_lineage` selector still picks the max-sensor lineage for Label A indexing — that lineage now receives NO override.

**The alignment-control design's interpretive value (locked).** This is **not** a "same bridge, different target" rescue probe. It is an alignment-control / negative-control slice that tests whether the v0.53l/m Label A firing tracks (a) the underlying max-sensor TRAIT or (b) the boosted-access CHANNEL. If D reachability ≥ 0.25 AND D Label B fires PRESENT AND D Label A does NOT fire PRESENT (NOT_FOUND / PARTIAL <2/3 / deadband / wrong-sign / NaN-nonfiring all count), the result is **consistent with the v0.53l/m Label A rescue depending on alignment between the boosted perception channel and the max-sensor lineage label, while reachability itself can be rescued by perception access assigned to a non-max lineage** — the headline DECOUPLES outcome. If D reachability ≥ 0.25 AND both labels fire PRESENT, the result is surprising and demands audit: the max-sensor lineage somehow still dominates despite receiving no override, OR the lineage labels / override targeting / measurement wiring need review. If D reachability < 0.25, lowest-lineage override is **not symmetric** with max-lineage override — starting position, early survival, or trait package interactions matter beyond raw perception radius. **D Label A wrong-sign is non-halting by design**; under the alignment-control framing, Label A wrong-sign or deadband on D is substantive decoupling evidence, not a framework failure. (See sub-verdict wording note below.)

## Pre-implementation note (2026-05-11, before any reducer code)

The pre-reg's design was confirmed with the user before drafting. The key locked design points:

- **5 arms, 320 runs.** A_null_V0_25 (Tier-1 anchor); B_widened_V0_25 (Tier-2 anchor); **C_widened_food_near1_combined_max_lineage_sr8_N400** (max-only — single max-sensor founder boosted; in-slice predecessor anchor against v0.53l C published Results); **D_widened_food_near1_combined_min_lineage_sr8_N400** (min-only — single min-sensor founder boosted; **the new alignment-control intervention; verdict-gating on tick-400**); **E_widened_food_near1_combined_modelwide_sr8_N400** (model-wide via `body_config.effective_sensor_radius_override=8`; in-slice predecessor anchor against v0.53k C published Results). Same 64-tuple corpus shape.
- **No `src/` modifications.** v0.53l-tip's seams (chamber `per_founder_traits_overrides` + model always-consume invariant) cover all three intervention arms. `tests/sha_pins.py` carries forward unchanged. The new bottom-K helper lives in the v0.53n reducer module only.
- **Min-sensor selection rule (locked).** Sort the five founders by `traits.sensor_radius` ascending, with `min(lineage_id)` tiebreak; take the single lowest. The new helper `build_bottom_k_per_founder_overrides(seed, trait_config, n_founders, k)` mirrors v0.53m's `build_top_k_per_founder_overrides` shape and returns `(overrides, bottom_lineage_ids)`. The audit CSV records `bottom1_lineage_id_in_run` and `bottom1_sensor_radius_in_run` per D run. **The verdict naming uses `MIN_LINEAGE` rather than `NONMAX_LINEAGE`** (per user direction): `NONMAX` is too broad — a runner-up lineage and the absolute lowest lineage are different controls. `MIN_LINEAGE_SENSOR_RADIUS_8` clearly states the adversarial alignment.
- **C/E triangulation bracket D.** C max-only at 1/5 (trait-aligned, PRESENT) and E model-wide at 5/5 (homogenized, PARTIAL with Label A deadband) are predecessor-anchor arms that bracket D min-only at 1/5 (trait-OPPOSED) — same coverage as C but inverted alignment, same intervention magnitude as E but at single-lineage scope. The C ⊥ E ⊥ D triangle is a stronger control than a 4-arm slice would provide.
- **Anchor cascade structure (priority 2) — eight sub-conditions.** (a) Tier-1 A tick-50 paired_d drift, (b) Tier-2 B tick-200 reachability, (c) C tick-400 reachability == 61/64 exact, (d) C tick-400 sub-verdict == `C_..._TICK400_BRIDGE_PRESENT`, (e) C tick-400 six paired_d cells reproduce v0.53l within 1e-3, (f) E tick-400 reachability == 64/64 exact, (g) E tick-400 sub-verdict suffix == `_TICK400_BRIDGE_PARTIAL` (arm prefix is `E_WIDENED_FOOD_NEAR1_MODELWIDE_SR8`; categorical resolution PARTIAL is what v0.53k C produced), (h) E tick-400 six paired_d cells reproduce v0.53k within 1e-3. Anchor wrong-sign is **not** its own halt class; any anchor failure collapses into `ANCHOR_REPLICATION_HALT`.
- **Asymmetric halt rule on D — the central design correction.** Label A wrong-sign or deadband on D is **substantive decoupling evidence, not a halt**. Label B wrong-sign on D **is** halt-eligible (reachability-gated): Label B indexes outcome/readiness rather than trait-driven access, so a Label B reversal would indicate the min-sensor boost actively HURT food acquisition on the boosted lineage — a finding that demands investigation before priority-4/5/6 interpretation. Anchor (C/E) wrong-sign collapses into priority 2 (predecessor lock). Priority 3 halt name: `MIN_LINEAGE_LABEL_B_OPPOSITE_SIGN_HALT`.
- **D's sub-verdict family retains the v0.48 4-way shape** (`BRIDGE_PRESENT` / `BRIDGE_PARTIAL` / `BRIDGE_NOT_FOUND` / `OPPOSITE_SIGN_HALT`) for cross-slice test machinery reuse, but D's `OPPOSITE_SIGN_HALT` sub-verdict resolution is **non-halting at the rollup level** in v0.53n — the priority-3 trigger requires Label B specifically wrong-sign, not "any primary wrong-sign." When D sub-verdict resolves to `OPPOSITE_SIGN_HALT` because of Label A wrong-sign cells only (and Label B has no wrong-sign cells), the rollup routes to priority 4 (DECOUPLES) since "Label A wrong-sign" ⊂ "Label A NOT PRESENT." Results section will state this asymmetry explicitly.
- **Cautious framing carries forward.** Label B magnitude on D, if it fires PRESENT, is interpretable as a structural-concentration channel (the boosted lineage acquires food via perception access; non-label lineages do not) — **not** as a generic strengthening of the underlying trait correlation. Locked phrases on D use "consistent with access-mediated bridge expression" not "access-mediated bridge"; "consistent with the v0.53l/m Label A rescue depending on alignment" not "Label A is access-aligned."

## Conservation framing — observational, zero `src/` changes, single new reducer-local helper

- **No `src/` modifications.** v0.53l-tip's `fear_hunger_chamber.py` (`per_founder_traits_overrides`) and `model.py` (always-consume invariant) seams cover all three intervention arms. The science-core five files remain pinned to v0.52b-tip. Chamber driver SHA and model SHA remain at v0.53l-tip values (`tests/sha_pins.py` constants unchanged).
- **No modifications to prior reducer / audit / pre-reg / test files.** v0.53l's and v0.53m's reducers remain byte-identical to their merged forms. v0.53n's reducer reuses `_select_sensor_radius_label` from v0.53k via cross-script import and introduces the new sibling `_select_bottom_k_sensor_radius_lineages`.
- **Pre-sampling pattern carries forward.** For each (version, seed, hazard) on the C, D, and E arms, the reducer pre-samples founder Traits using `make_streams(seed).mutation` + `random_traits` 5× to compute the override target lineage, then calls `run_chamber()` with the appropriate override list. v0.53l-tip's always-consume invariant guarantees the chamber's internal `random_traits` draws produce the same five sampled Traits regardless of override presence.
- **A_null_V0_25 arm is byte-identical to v0.48–v0.53m A_null path AT TICK-50.** Tier-1 re-anchor enforces this within 1e-3.
- **B_widened_V0_25 arm is byte-identical to v0.53–v0.53m B_widened arm at every tick 0..200.** Tier-2 categorical anchor enforces `b_widened_v025_reachability_run_share_tick_200 == 0.0`.
- **C arm is byte-identical to v0.53l C at every tick 0..400.** In-slice predecessor anchor enforces categorical reachability + sub-verdict + six paired_d cells within 1e-3 of v0.53l Results.
- **E arm is byte-identical to v0.53k C at every tick 0..400.** In-slice predecessor anchor enforces categorical reachability + sub-verdict (PARTIAL) + six paired_d cells within 1e-3 of v0.53k Results.
- **D arm differs from C by exactly one knob:** override target lineage is `bottom_lineage_ids[0]` instead of `top_lineage_ids[0]`. Layout, body_config, n_ticks, corpus, override magnitude (r=8) all identical to C.
- **D arm differs from E by exactly two knobs:** override is per-lineage on a single founder (D, the min-sensor lineage) vs model-wide via `body_config` (E); `body_config.effective_sensor_radius_override` is `None` on D vs `8` on E.

## Test #8 SHA-pinning policy — unchanged from v0.53l-tip

`fear_hunger_chamber.py` SHA = `e9aaca0584ef763277131ab348140b186ca60d9210f34d0245239bb4217863fd` (`sha_pins.CHAMBER_DRIVER_SHA` at v0.53l-tip). `model.py` SHA = `d45413712b0fcaa1b131e0f73c237264563e6a3c9e41c69d1d2b5402fddc093b` (`sha_pins.MODEL_SHA` at v0.53l-tip). Science-core five files at v0.52b-tip historical pins. v0.53n's test #8 uses the same three-part structure as v0.53l/m (Part A historical; Part B chamber via sha_pins; Part C model via sha_pins).

No `sha_pins.py` updates this slice — the seams from v0.53l are sufficient. No prior test file modifications.

## Corpus (locked, 64 × 5 arms = 320 runs)

Same shape as v0.53m on the A/B/C/E corpus; v0.53n replaces the v0.53m top-2 D arm with a min-only D arm on the same 64-tuple to maintain matched RNG:

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

Byte-identical to v0.48–v0.53m A_null. **Tier-1 anchor at tick-50.**

### B_widened_V0_25

```
ChamberLayout = widened_gradient_layout()
... (V0_25 baseline; body_config=None; per_founder_traits_overrides=None; n_ticks=200)
```

Byte-identical to v0.53–v0.53m B_widened. **Tier-2 categorical anchor on tick-200 reachability.**

### C_widened_food_near1_combined_max_lineage_sr8_N400 (IN-SLICE PREDECESSOR ANCHOR vs v0.53l C)

```
ChamberLayout = ChamberLayout(  # script-local FOOD_NEAR1_LAYOUT (identical to v0.53j/k/l/m)
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

Where `top1_lid = top_lineage_ids[0] = _select_sensor_radius_label(...)`. Byte-identical to v0.53l C / v0.53m C at every tick 0..400. **In-slice predecessor anchor:** C tick-400 reachability == 61/64 exact AND sub-verdict == `C_WIDENED_FOOD_NEAR1_MAX_LINEAGE_SR8_TICK400_BRIDGE_PRESENT` AND six paired_d cells reproduce v0.53l within 1e-3.

### D_widened_food_near1_combined_min_lineage_sr8_N400 (PRIMARY VERDICT-GATING — the new alignment-control intervention)

```
ChamberLayout = FOOD_NEAR1_LAYOUT (identical to C)
... (V0_25 baseline pool/ecology;
    body_config = BodyConfig(starting_energy=100.0, base_metabolic_cost=0.10);
    per_founder_traits_overrides[bottom1_lid] = Traits(..., effective_sensor_radius_override=8);  # NEW: min-sensor lineage
    per_founder_traits_overrides[other 4 lids] = None;
    n_ticks = 400)
```

Where `bottom1_lid = bottom_lineage_ids[0] = _select_bottom_k_sensor_radius_lineages(..., k=1)[0]` — the founder with the **lowest** `sensor_radius`, with `min(lineage_id)` tiebreak. Differs from C by exactly one knob: the override target lineage is the absolute lowest perceiver, not the absolute highest. Same 1/5 coverage as C; inverted alignment. **The verdict gates on D's tick-400 reachability + sub-verdict.**

### E_widened_food_near1_combined_modelwide_sr8_N400 (IN-SLICE PREDECESSOR ANCHOR vs v0.53k C)

```
ChamberLayout = FOOD_NEAR1_LAYOUT (identical to C/D)
... (V0_25 baseline pool/ecology;
    body_config = BodyConfig(starting_energy=100.0, base_metabolic_cost=0.10, effective_sensor_radius_override=8);
    per_founder_traits_overrides = None;  # model-wide path, NOT per-lineage
    n_ticks = 400)
```

Byte-identical to v0.53k C / v0.53m E at every tick 0..400 (modulo the v0.53l-tip always-consume invariant, which is no-op on E since `per_founder_traits_overrides` is `None`). **In-slice predecessor anchor:** E tick-400 reachability == 64/64 exact AND sub-verdict suffix == `_TICK400_BRIDGE_PARTIAL` AND six paired_d cells reproduce v0.53k within 1e-3.

## Labels (locked, two — with four Label B variants on C/D/E, three on A/B)

Identical to v0.53j/k/l/m: Label A (`high_sensor_radius_lineage` — trait-resolved via `_select_sensor_radius_label`); Label B variants `high_tick{50,100,200,400}_readiness_fraction_lineage` (tick-400 variant computed on C/D/E only; NaN-broadcast on A/B). Label A on D still picks `top_lineage_ids[0]` (the max-sensor lineage) — that is the lineage that does NOT receive the override under D. This is the alignment-control mechanism.

## Primary observables (locked, 3, four windows on C/D/E, three on A/B)

Identical to v0.53j/k/l/m. Note: observable 3 (`mean_distance_to_nearest_food_cell_tick{N}`) uses each arm's layout food cells; cross-arm signed_d is NOT directly cross-arm interpretable.

## Effect-size rule (locked, sign-aware, identical to v0.48–v0.53m)

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

d_widened_food_near1_combined_min_lineage_sr8_N400_reachability_run_share_tick_400 =
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

Plus categorical: E tick-400 reachability == 1.0 (64/64) exact AND E tick-400 sub-verdict suffix == `_TICK400_BRIDGE_PARTIAL` (arm prefix is `E_WIDENED_FOOD_NEAR1_MODELWIDE_SR8`; the categorical resolution `PARTIAL` is what v0.53k C produced under the same body_config / layout / RNG configuration).

**Note on determinism:** v0.53l observed drift_abs = 0.0 across all six FOOD_NEAR2 anchor cells; v0.53m observed drift_abs = 0.0 across all twelve in-slice anchor cells (six C + six E). v0.53n expects the same. The always-consume invariant (v0.53l-tip) guarantees this for both override-path (C/D) and no-per-founder-override-path (E).

## Per-arm sub-verdicts (locked, 4-way each — verdict-gating on D tick-400; anchors on C and E tick-400)

| condition | A_null_V0_25 | B_widened_V0_25 | C max-only (tick-400 **anchor**) | D min-only (tick-400 **verdict-gating**) | E model-wide (tick-400 **anchor**) |
|---|---|---|---|---|---|
| both labels clear ≥ 2/3 cells, NaN non-firing, 0 wrong-sign | `A_NULL_V025_TICK{50,100,200}_BRIDGE_PRESENT` | `B_WIDENED_V025_TICK200_BRIDGE_PRESENT` | `C_WIDENED_FOOD_NEAR1_MAX_LINEAGE_SR8_TICK400_BRIDGE_PRESENT` | `D_WIDENED_FOOD_NEAR1_MIN_LINEAGE_SR8_TICK400_BRIDGE_PRESENT` | `E_WIDENED_FOOD_NEAR1_MODELWIDE_SR8_TICK400_BRIDGE_PRESENT` |
| exactly one label clears ≥ 2/3 cells | `..._BRIDGE_PARTIAL` | ... | `..._BRIDGE_PARTIAL` | `..._BRIDGE_PARTIAL` | `..._BRIDGE_PARTIAL` |
| neither clears ≥ 2/3 cells | `..._BRIDGE_NOT_FOUND` | ... | `..._BRIDGE_NOT_FOUND` | `..._BRIDGE_NOT_FOUND` | `..._BRIDGE_NOT_FOUND` |
| any primary signed_d ≤ −0.5 | `..._OPPOSITE_SIGN_HALT` | ... | `..._OPPOSITE_SIGN_HALT` | `..._OPPOSITE_SIGN_HALT` | `..._OPPOSITE_SIGN_HALT` |

**Strict NaN-treated-as-non-firing rule preserved.** D's sub-verdict prefix is `D_WIDENED_FOOD_NEAR1_MIN_LINEAGE_SR8_TICK{N}_BRIDGE_{...}`. E's sub-verdict prefix is `E_WIDENED_FOOD_NEAR1_MODELWIDE_SR8_TICK{N}_BRIDGE_{...}`.

**Asymmetric halt at the rollup level on D (alignment-control framing — central design correction).** D's sub-verdict `OPPOSITE_SIGN_HALT` resolution is **non-halting at the rollup level** in v0.53n. The priority-3 halt requires **Label B specifically** wrong-sign (any cell signed_d ≤ −0.5) AND D reachability ≥ 0.25; Label A wrong-sign cells alone do NOT route to priority 3. When D sub-verdict resolves to `OPPOSITE_SIGN_HALT` because of Label A wrong-sign cells only (and Label B has no wrong-sign cells), the rollup routes to priority 4 (DECOUPLES) since "Label A wrong-sign" is one of the cases captured by "Label A NOT PRESENT" in priority 4's trigger.

## Slice rollup verdicts (locked, 7 outcomes, priority-ordered)

1. `CORPUS_REDERIVE_DRIFT_HALT`
2. `ANCHOR_REPLICATION_HALT` (Tier-1 + Tier-2 + C in-slice anchor + E in-slice anchor; eight sub-conditions)
3. `MIN_LINEAGE_LABEL_B_OPPOSITE_SIGN_HALT` (**reachability-gated** on D tick-400; **Label B specifically**)
4. `MIN_LINEAGE_ACCESS_RESCUES_REACHABILITY_AND_DECOUPLES_LABEL_A` (**the expected headline outcome**)
5. `MIN_LINEAGE_ACCESS_RESCUES_FULL_BRIDGE` (surprising / demands audit)
6. `MIN_LINEAGE_ACCESS_PARTIAL_OR_MIXED`
7. `MIN_LINEAGE_ACCESS_BELOW_REACHABILITY_THRESHOLD`

### Halt conditions

| priority | rollup verdict | trigger | locked phrase (verbatim) |
|---|---|---|---|
| 1 | `CORPUS_REDERIVE_DRIFT_HALT` | A `a_share_h8` for v0.42/v0.44/v0.45 drifts > 1e-3 | "Halt: A_null_V0_25 re-anchor drifted from the published Results value for {version}; v0.53n's deterministic re-execution of the V0_25 corpus does not reproduce the published metric within 1e-3." |
| 2 | `ANCHOR_REPLICATION_HALT` | (a) A tick-50 paired_d drift > 1e-3, (b) A tick-50 sub-verdict ≠ PRESENT, (c) B tick-200 reachability ≠ 0, (d) C tick-400 reachability ≠ 61/64 exact, (e) C tick-400 sub-verdict ≠ `C_WIDENED_FOOD_NEAR1_MAX_LINEAGE_SR8_TICK400_BRIDGE_PRESENT`, (f) C tick-400 six paired_d cells drift > 1e-3 vs v0.53l, (g) E tick-400 reachability ≠ 64/64 exact, (h) E tick-400 sub-verdict suffix ≠ `_TICK400_BRIDGE_PARTIAL` OR six paired_d cells drift > 1e-3 vs v0.53k | "Halt: v0.53n's A_null_V0_25 arm does not reproduce v0.48–v0.53m's tick-50 spatial bridge, OR v0.53n's B_widened_V0_25 arm does not reproduce v0.53c–v0.53m's `0/64` reachability lock at tick-200, OR v0.53n's C_widened_food_near1_combined_max_lineage_sr8_N400 arm does not reproduce v0.53l's tick-400 anchor (categorical reachability `61/64` AND sub-verdict `BRIDGE_PRESENT` AND six published paired_d cells within 1e-3), OR v0.53n's E_widened_food_near1_combined_modelwide_sr8_N400 arm does not reproduce v0.53k's tick-400 anchor (categorical reachability `64/64` AND categorical resolution `PARTIAL` AND six published paired_d cells within 1e-3). v0.53n cannot interpret the D_widened_food_near1_combined_min_lineage_sr8_N400 cells without reproducing both the V0_25 baseline anchors AND both heterogeneity-alignment anchors that bracket the min-only measurement on the same FOOD_NEAR1 × combined-budget × n_ticks=400 mechanism axis. Anchor wrong-sign on C or E is captured here; D Label A wrong-sign is NOT a halt under v0.53n's alignment-control framing." |
| 3 | `MIN_LINEAGE_LABEL_B_OPPOSITE_SIGN_HALT` (**reachability-gated, Label B specifically**) | D reachability ≥ 0.25 AND D Label B has any wrong-sign cell (signed_d ≤ −0.5) | "Halt: a v0.53n D_widened_food_near1_combined_min_lineage_sr8_N400 tick-400 **Label B** spatial / foraging primary fires in the WRONG direction, AND D reachability at tick-400 clears the locked 25% threshold. Under v0.53n's alignment-control framing, Label B is expected to track outcome / readiness on the boosted lineage (the min-sensor founder receiving the perception override); a Label B reversal indicates the min-sensor boost actively reduced food acquisition on the boosted lineage relative to the non-label pool — a result that demands investigation before priority-4/5/6 interpretation. D Label A wrong-sign or deadband is NOT a halt; under the alignment-control framing it is substantive decoupling evidence (routed to priority 4). The reachability-gated trigger preserves v0.53e's locked sign discipline while excluding the v0.53e-style measurement-edge case (wrong-sign at reachability=0)." |

### Outcome conditions (only consulted if no halt fires)

| priority | rollup verdict | trigger | locked phrase (verbatim) |
|---|---|---|---|
| 4 | `MIN_LINEAGE_ACCESS_RESCUES_REACHABILITY_AND_DECOUPLES_LABEL_A` | `d_reachability_run_share_tick_400 ≥ 0.25` AND D Label B fires PRESENT (≥2/3 cells expected-sign, NaN non-firing, 0 wrong-sign Label B cells) AND D Label A NOT PRESENT (anything except ≥2/3 firing-expected — includes NOT_FOUND, PARTIAL <2/3, deadband, wrong-sign, NaN-nonfiring) | "On the modern A_null corpus with the V0_25 substrate held constant except for the combined founder-facing budget relaxation `BodyConfig(starting_energy=100.0, base_metabolic_cost=0.10)` AND the simulation horizon doubled to `n_ticks=400` AND the `widened_food_near1` layout AND the **min-sensor-lineage** per-lineage perception intervention `per_founder_traits_overrides[bottom_lineage_ids[0]] = Traits(effective_sensor_radius_override=8)` (the override applies ONLY to the single min-`sensor_radius` founder per run, with `argmin(sensor_radius)` selection and `min(lineage_id)` tiebreak; the v0.48 `is_high_sensor_radius_lineage` selector still picks the MAX-sensor lineage for Label A indexing — that lineage receives NO override; metabolic cost UNAFFECTED per the override's information-channel-only contract; override propagates to all descendants via `dataclasses.replace`'s preservation), D reachability at tick-400 clears the locked 25% threshold and D Label B fires PRESENT under the locked +0.5 paired_d threshold, while D Label A does NOT fire PRESENT (NOT_FOUND, PARTIAL <2/3, deadband, wrong-sign, or NaN-nonfiring). C_widened_food_near1_combined_max_lineage_sr8_N400 reproduces v0.53l's `61/64` anchor at tick-400 (max-only / trait-aligned lock holds), E_widened_food_near1_combined_modelwide_sr8_N400 reproduces v0.53k's `64/64` anchor at tick-400 (model-wide / homogenized lock holds). The geometry/substrate cell that v0.53c locked as `WIDENED_BELOW_REACHABILITY_THRESHOLD_AT_TICK_200`, v0.53d locked as `WIDENED_BELOW_REACHABILITY_THRESHOLD_UNDER_RELAXED_INFLUX`, v0.53e locked as `RELAXED_OPPOSITE_SIGN_HALT`, v0.53f locked as `WIDENED_BELOW_REACHABILITY_THRESHOLD_UNDER_BASE_METABOLIC_COST_010`, v0.53g locked as `WIDENED_BELOW_REACHABILITY_THRESHOLD_UNDER_COMBINED_SE100_BMC010`, v0.53h locked as `WIDENED_BELOW_REACHABILITY_THRESHOLD_AT_TIME_HORIZON_400`, v0.53i locked as `WIDENED_BRIDGE_RESCUED_BY_FOOD_NEAR2`, v0.53j locked as `WIDENED_BELOW_REACHABILITY_THRESHOLD_UNDER_FOOD_NEAR1`, v0.53k locked as `WIDENED_BRIDGE_PARTIALLY_RESCUED_BY_SENSOR_RADIUS_8`, v0.53l locked as `WIDENED_BRIDGE_RESCUED_BY_MAX_LINEAGE_SENSOR_RADIUS_8`, and v0.53m locked as `WIDENED_BRIDGE_RESCUED_BY_TOP2_LINEAGE_SENSOR_RADIUS_8` admits an alignment-decoupled outcome at the min-sensor-lineage adversarial control point: D reachability clears the 25% threshold, D Label B fires PRESENT, and D Label A does NOT fire PRESENT. **The result is consistent with the v0.53l/m Label A rescue depending on alignment between the boosted perception channel and the max-sensor lineage label, while reachability itself can be rescued by perception access assigned to a non-max lineage.** This is strong evidence but NOT exclusive causality and NOT a claim that the v0.48 bridge is purely access-mediated — the min-sensor boost may also produce Label A decoupling through secondary channels (asymmetric early survival of the boosted lineage, reproduction-rate differential, pleiotropy with other heritable traits, structural-concentration effects on Label B that obscure the trait signal). This does NOT prove `the v0.48 bridge is purely access-mediated`; NOT `the v0.53l/m Label A rescue was purely access-mediated` (max-only's trait-aligned access is consistent with both readings; v0.53n's adversarial control localizes the alignment requirement to the boosted-lineage channel): `MIN_LINEAGE_ACCESS_RESCUES_REACHABILITY_AND_DECOUPLES_LABEL_A`." |
| 5 | `MIN_LINEAGE_ACCESS_RESCUES_FULL_BRIDGE` | `d_reachability_run_share_tick_400 ≥ 0.25` AND D Label A fires PRESENT AND D Label B fires PRESENT | "On the modern A_null corpus with the V0_25 substrate held constant except for the combined founder-facing budget relaxation AND the simulation horizon doubled to `n_ticks=400` AND the `widened_food_near1` layout AND the min-sensor-lineage per-lineage perception intervention `per_founder_traits_overrides[bottom_lineage_ids[0]] = Traits(effective_sensor_radius_override=8)`, D reachability clears the 25% threshold AND both Label A AND Label B fire PRESENT at tick-400. **This is the surprising and high-information outcome.** Under v0.53n's alignment-control design, Label A indexes the MAX-sensor lineage — which receives NO override on D. For Label A to fire PRESENT despite not receiving the override implies one of: (i) the max-sensor lineage dominates food acquisition on D anyway via trait-level expression (e.g., reproduction-rate / metabolic-rate / hazard-tolerance pleiotropy with sensor_radius gives the max-sensor lineage an outcome edge once any access is rescued); (ii) the lineage labels / override targeting / measurement wiring need audit (verify `bottom_lineage_ids[0]` actually received the override; verify Label A picks `top_lineage_ids[0]`; verify the override propagated to descendants); (iii) some non-perception channel of the v0.48 bridge is dominant. The geometry/substrate cell that v0.53c through v0.53m locked admits a full-bridge rescue under min-lineage adversarial alignment: `MIN_LINEAGE_ACCESS_RESCUES_FULL_BRIDGE` — flagged for audit and follow-up. Results must include explicit checks of override targeting, descendant propagation, lineage-label resolution, and per-lineage population dynamics before assigning mechanistic interpretation. v0.53l/m's trait-aligned interpretation is NOT falsified by this outcome but requires additional non-perception mechanism to be operating in concert. v0.53o candidate: per-lineage population-dynamics audit + dose-response on `r=8` magnitude under min-lineage scope." |
| 6 | `MIN_LINEAGE_ACCESS_PARTIAL_OR_MIXED` | `d_reachability_run_share_tick_400 ≥ 0.25` AND none of priority 3 / 4 / 5 conditions hold (catch-all: Label B PARTIAL, Label A PRESENT + Label B PARTIAL, Label A NOT_FOUND + Label B PARTIAL, etc.) | "On the modern A_null corpus with the V0_25 substrate held constant except for the combined founder-facing budget relaxation AND the min-sensor-lineage per-lineage perception intervention on FOOD_NEAR1 at `n_ticks=400`, D's reachability clears the locked 25% threshold but neither the clean DECOUPLES outcome (Label B PRESENT + Label A NOT PRESENT) nor the FULL_BRIDGE outcome (both labels PRESENT) holds, and D Label B has no wrong-sign cells (else priority 3 would have fired). C_widened_food_near1_combined_max_lineage_sr8_N400 reproduces v0.53l's `61/64` anchor at tick-400 in-slice; E_widened_food_near1_combined_modelwide_sr8_N400 reproduces v0.53k's `64/64` anchor at tick-400 in-slice. The min-sensor-lineage adversarial intervention admits measurable food access on the boosted lineage but produces a mixed or partial bridge signal that does not cleanly localize the alignment requirement. Layout-specific partial-or-mixed alignment-control outcome logged in Results: `MIN_LINEAGE_ACCESS_PARTIAL_OR_MIXED`. Results section should describe which label fires under which cells, and whether the per-cell pattern hints at population-dynamics interference (e.g., the min-sensor boosted lineage having low reproductive fitness despite gaining access)." |
| 7 | `MIN_LINEAGE_ACCESS_BELOW_REACHABILITY_THRESHOLD` | `d_reachability_run_share_tick_400 < 0.25` | "On the modern A_null corpus with the V0_25 substrate held constant except for the combined founder-facing budget relaxation AND the simulation horizon doubled to `n_ticks=400` AND the `widened_food_near1` layout AND the min-sensor-lineage per-lineage perception intervention, fewer than 25% of D runs have any founder lineage with pre400 food events. C_widened_food_near1_combined_max_lineage_sr8_N400 reproduces v0.53l's `61/64` anchor at tick-400 in-slice; E_widened_food_near1_combined_modelwide_sr8_N400 reproduces v0.53k's `64/64` anchor at tick-400 in-slice. **Min-lineage override is NOT symmetric with max-lineage override under this corpus and implementation.** The geometry/substrate cell that v0.53c through v0.53m locked is not rescued at tick-400 when the same intervention magnitude (`r=8`) and same coverage (1/5) are assigned to the lowest-sensor lineage instead of the highest-sensor lineage. This implies that starting position, early survival, trait package interactions (the min-sensor founder may also carry low-fitness values on other traits via correlated sampling within the V0_25 TraitConfig), or reproduction-rate differential matter beyond raw perception radius — the boosted access does NOT translate into measurable food acquisition for the min-sensor lineage under the tested envelope. This does NOT prove `non-max lineages cannot use perception access` — only that this specific min-sensor adversarial scheme does not clear the threshold under the tested envelope. v0.53o candidate: per-lineage survival / reproduction diagnostics on D + dose-response on `r=8` magnitude under min-lineage scope: `MIN_LINEAGE_ACCESS_BELOW_REACHABILITY_THRESHOLD`." |

The 4 non-halt outcomes (priorities 4–7) form a total partition. Test #16 enforces the partition exhaustively.

## Cautious framing (per CLAUDE.md, refined per user direction)

- **"The result is consistent with the v0.53l/m Label A rescue depending on alignment between the boosted perception channel and the max-sensor lineage label, while reachability itself can be rescued by perception access assigned to a non-max lineage"** (priority 4) — NOT "the v0.48 bridge is purely access-mediated"; NOT "the v0.53l/m Label A rescue was purely access-mediated"; NOT "trait-mediated reading is falsified." v0.53n's adversarial control localizes the alignment requirement to the boosted-lineage channel under one specific intervention scope (min-sensor lineage at 1/5 coverage with `r=8`).
- **"Min-lineage override is NOT symmetric with max-lineage override under this corpus and implementation"** (priority 7) — NOT "non-max lineages cannot use perception access in any setting"; NOT "the asymmetry is fully explained by trait pleiotropy." The bounded claim is that this specific min-sensor scheme at `r=8` does not clear the reachability threshold under FOOD_NEAR1 + combined-budget × n_ticks=400.
- **"This is the surprising and high-information outcome"** (priority 5) — NOT "v0.53l/m's trait-aligned reading is falsified"; NOT "the wiring is broken by default." Priority 5 is flagged for audit and follow-up before any mechanistic interpretation.
- The structural-concentration intuition for Label B (carried forward from v0.53l/m Results) applies on D when only one lineage receives the override: Label B magnitudes on D are interpreted as structural-concentration channels, not as linear biological-strength measures. Descriptive Results discussion only; not verdict-gating.
- v0.53n explicitly does not establish: cross-magnitude generalization at smaller / larger `r` doses on min-lineage scope; behavior at min-2 / min-3 coverage; generalization to non-V0_25 substrates; behavior at non-`n_ticks=400` horizons; dose-response on `r=8` magnitude under min-lineage scope; the precise per-lineage mechanism driving any decoupling or rescue outcome.

## What v0.53n cannot establish

- ✗ **"The v0.48 bridge is purely access-mediated."** Priority 4 is strong evidence for alignment dependence, but it does not exclude trait-level contributions through secondary channels (early survival, reproduction-rate, pleiotropy).
- ✗ **"The v0.53l/m Label A rescue was purely access-mediated."** Both max-only (v0.53l) and top-2 (v0.53m) had trait-aligned access; v0.53n's adversarial control breaks the alignment but does not retroactively reinterpret v0.53l/m.
- ✗ **"Trait-mediated reading is falsified."** The trait-and-access readings of the v0.48 bridge are not mutually exclusive. v0.53n localizes the alignment requirement under one specific scope.
- ✗ **A revised v0.53–v0.53m verdict.** All thirteen predecessor verdicts stand as historical contracts.
- ✗ **Mechanism behind any rescue or non-rescue outcome.** Population dynamics under V0_25 × FOOD_NEAR1 × combined-budget × `n_ticks=400` × min-lineage `r=8` are descriptively logged; no mechanism is formally established.
- ✗ **"r=8 is the right magnitude for the adversarial control."** v0.53o candidate: dose-response under min-lineage scope.

## Open framing (NOT in v0.53n primary)

- **If priority 4 fires (DECOUPLES — the expected headline outcome):** the v0.48 Label A bridge requires alignment between the boosted perception channel and the max-sensor lineage label under the FOOD_NEAR1 × combined-budget × n_ticks=400 envelope at 1/5 coverage with `r=8`. v0.54 synthesis becomes the natural arc-closing artifact; v0.53o is optional. Reframe the v0.53 mechanism arc Results writeup to integrate the trait-vs-access disambiguation.
- **If priority 5 fires (FULL_BRIDGE — surprising):** audit before interpretation. Per-lineage population-dynamics diagnostics + override-targeting verification + Label-A resolution verification + descendant propagation verification. v0.53o becomes mandatory.
- **If priority 6 fires (PARTIAL_OR_MIXED):** mixed result — partial decoupling. Surface for discussion; v0.53o candidate: dose-response under min-lineage scope OR per-lineage survival diagnostics.
- **If priority 7 fires (BELOW_THRESHOLD):** lowest-lineage override is not symmetric with max-lineage override under the tested envelope. v0.53o candidate: per-lineage survival / reproduction diagnostics on D + investigation of starting position vs trait package vs perception channel as the asymmetry mechanism.
- **v0.53o (provisional, NOT auto-locked).** Will be discussed with user after v0.53n Results, per the locked goal-tree honesty thread: v0.53n is the cleanest remaining trait-vs-access disambiguation; v0.53o is optional and depends on what v0.53n finds. Do NOT propose v0.53o reflexively — surface the synthesis/wrap question to user after v0.53n Results.
- **v0.54 — synthesis / fresh-stream calibration.** Eventually fresh-stream calibration on the full v0.46–v0.53n stack. The natural arc-closing artifact.

## Re-anchor (locked — Tier-1 and corpus only at tick-50)

| version | published `a_share_h8` |
|---|---|
| v0.42 | 0.652 |
| v0.43R | NOT PUBLISHED (informational-only) |
| v0.44 | 0.878 |
| v0.45 | 0.818 |

## Outputs (locked)

```
runs/v0.53n-perception-min-lineage-sensor-radius-8/per_run_per_lineage_v053n.csv
  columns: arm, layout_name,
           safe_x_min, safe_x_max, hazard_x_min, hazard_x_max,
           food_x_min, food_x_max, world_width, spawn_x, height,
           body_starting_energy, body_base_metabolic_cost,
           body_effective_sensor_radius_override,                    # 8 on E rows; None elsewhere
           founder_effective_sensor_radius_override,                 # 8 on C max-sensor + D min-sensor founders; None elsewhere
           is_max_sensor_lineage_in_run,                             # True iff lineage_id == top_lineage_ids[0]
           is_min_sensor_lineage_in_run,                             # NEW in v0.53n: True iff lineage_id == bottom_lineage_ids[0]
           top1_lineage_id_in_run,                                   # int (the max-sensor lineage_id; used by C + Label A on all C/D/E)
           top1_sensor_radius_in_run,                                # int (top-1 founder's sampled sensor_radius)
           bottom1_lineage_id_in_run,                                # NEW in v0.53n: int (the min-sensor lineage_id; used by D)
           bottom1_sensor_radius_in_run,                             # NEW in v0.53n: int (bottom-1 founder's sampled sensor_radius)
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

runs/v0.53n-perception-min-lineage-sensor-radius-8/audit_summary.csv
runs/v0.53n-perception-min-lineage-sensor-radius-8/audit_log.txt
```

Three new columns relative to v0.53m: `is_min_sensor_lineage_in_run`, `bottom1_lineage_id_in_run`, `bottom1_sensor_radius_in_run`. The v0.53m top-2 columns (`is_top2_sensor_lineage_in_run`, `top2_lineage_id_in_run`, `top2_sensor_radius_in_run`) are NOT carried forward — v0.53n has no top-2 arm. The `founder_effective_sensor_radius_override` column gets `8` on C max-sensor founder + D min-sensor founder; `None` elsewhere (A/B/E founders + non-targeted C/D founders).

## Implementation plan (locked)

1. **Zero `src/` changes.** v0.53l-tip seams cover everything.
2. Fresh script `scripts/v0_53n_perception_min_lineage_sensor_radius_8_audit.py`. CLI: `uv run python scripts/v0_53n_perception_min_lineage_sensor_radius_8_audit.py [--out-dir runs/v0.53n-perception-min-lineage-sensor-radius-8]`.
3. Define module-level constant identical to v0.53m: `FOOD_NEAR1_LAYOUT` (FOOD_NEAR2 NOT needed in this slice).
4. Reuse `_select_sensor_radius_label` from v0.53k's reducer via cross-script import (CLAUDE.md pattern). Optionally reuse `_select_top_k_sensor_radius_lineages` from v0.53m's reducer for the C arm.
5. Define a new sibling helper `_select_bottom_k_sensor_radius_lineages(sensor_radius_by_lineage, k)` in v0.53n's reducer (returns `list[int]` of bottom-K lineage_ids, ascending by sensor_radius with `min(lineage_id)` tiebreak). Single-element output (k=1) is the verdict-gating selection.
6. Pre-sampling helper `build_bottom_k_per_founder_overrides(seed, trait_config, n_founders, k)` mirrors v0.53m's `build_top_k_per_founder_overrides` shape: replicates `make_streams(seed).mutation` + `random_traits` `n_founders` times, computes `bottom_lineage_ids = _select_bottom_k_sensor_radius_lineages(..., k)`, and constructs `overrides` where targeted lineages get `dataclasses.replace(sampled[lid], effective_sensor_radius_override=8)` and others get `None`. Returns `(overrides, bottom_lineage_ids)`.
7. C arm: max-only via `build_top_k_per_founder_overrides(..., k=1)` (reused). D arm: min-only via `build_bottom_k_per_founder_overrides(..., k=1)` (new). E arm: `per_founder_traits_overrides=None`; `body_config.effective_sensor_radius_override=8`.
8. Setup_observer captures founder audit table including per-trait override field; also records `top1_lineage_id_in_run`, `top1_sensor_radius_in_run`, `bottom1_lineage_id_in_run`, and `bottom1_sensor_radius_in_run` per C/D run for the new CSV columns. (The sensor-radius values are pre-sampled `int(sampled[target_lid].sensor_radius)` from `build_{top,bottom}_k_per_founder_overrides`; they ease later interpretation of ties or narrow top/bottom gaps.)
9. Per-tick observer: pre50/100/200 on all arms; pre400 on C/D/E.
10. Aggregate per-lineage primaries; compute Label A and four Label B variants. Label A definition uses the same `_select_sensor_radius_label` selector applied to founder Traits (top_lineage_ids[0]) — **on D, this is NOT the founder that received the override**.
11. Compute paired_d, reachability_run_share, population-stability metrics for each arm.
12. **In-slice predecessor anchors** (priority 2 sub-conditions c-h): C tick-400 reachability + sub-verdict + six paired_d cells; E tick-400 reachability + sub-verdict suffix + six paired_d cells.
13. **Corpus re-anchor** (priority 1): A `a_share_h8` for v0.42/v0.44/v0.45 within 1e-3.
14. **Reachability-gated MIN_LINEAGE_LABEL_B_OPPOSITE_SIGN_HALT** (priority 3): D tick-400 Label B wrong-sign cells AND D reachability ≥ 0.25 → halt; otherwise descriptive log. **D Label A wrong-sign is NOT a halt trigger; it routes to priority 4.**
15. Compute slice rollup verdict; print + write the locked phrase verbatim.

Wall time estimate ~35–60 minutes. C and E arms each replay published predecessor configurations; D is the only genuinely new computation.

## Test list (locked, 16 tests; mirrors v0.53m with min-lineage and asymmetric-halt adaptations)

`tests/test_v0_53n_perception_min_lineage_sensor_radius_8_audit.py`:

1. **`test_paired_d_function_reproduces_hand_computed_signed_d_on_fixture_AND_tier1_v048_constants_AND_v053l_published_C_anchor_AND_v053k_published_E_anchor`** *(four-part: hand-fixture + Tier-1 + v0.53l C anchor + v0.53k E anchor — identical to v0.53m #1)*.
2. **`test_a_null_v025_corpus_a_share_h8_re_anchors_v042_v044_v045`**.
3. `test_arm_a_null_v025_uses_tight_gradient_layout_default_body_config_and_n_ticks_200_with_explicit_geometry_asserts`.
4. `test_arm_b_widened_v025_uses_widened_gradient_layout_default_body_config_and_n_ticks_200_with_explicit_geometry_asserts`.
5. **`test_arm_c_widened_food_near1_combined_max_lineage_sr8_N400_uses_food_near1_layout_per_founder_override_on_max_sensor_lineage_only_and_n_ticks_400_with_explicit_geometry_and_per_lineage_perception_asserts`** *(byte-identical to v0.53m #5; verifies in-slice anchor configuration)*.
6. **`test_arm_d_widened_food_near1_combined_min_lineage_sr8_N400_uses_food_near1_layout_per_founder_override_on_min_sensor_lineage_only_and_n_ticks_400_with_explicit_geometry_and_min_lineage_perception_asserts`** *(NEW)*:
   - D body_config asserts: `body_config.effective_sensor_radius_override is None`.
   - D layout asserts (FOOD_NEAR1).
   - **Per-founder asserts:** exactly 1 of 5 founders has `body.traits.effective_sensor_radius_override == 8`; that founder is `bottom_lineage_ids[0]` from `_select_bottom_k_sensor_radius_lineages(..., k=1)`; the OTHER 4 founders have it `None`.
   - **Cross-arm anti-confusion assert:** `bottom_lineage_ids[0] != top_lineage_ids[0]` on D (the min-sensor founder is NOT the max-sensor founder; if the founder population is degenerate so that all five share the same sensor_radius, the tiebreak rule still picks `min(lineage_id)` on both selectors and they would coincide — assert via a synthetic-fixture branch that verifies the helpers produce different lineages when the founder sensor_radii are distinct).
   - D `_RunCapture.final_tick_count <= 400`.
7. **`test_arm_e_widened_food_near1_combined_modelwide_sr8_N400_uses_food_near1_layout_body_config_override_8_no_per_founder_override_and_n_ticks_400_with_explicit_geometry_and_modelwide_perception_asserts`** *(byte-identical to v0.53m #7; verifies in-slice anchor configuration)*.
8. **`test_no_src_modifications_compared_to_v0_53l_tip`** *(three-part SHA pinning via shared `tests/sha_pins.py`; UNCHANGED from v0.53l/m's test #8 — confirms no `sha_pins` updates this slice)*:
   - Part A: science-core five files at v0.52b-tip historical pins.
   - Part B: `fear_hunger_chamber.py` matches `sha_pins.CHAMBER_DRIVER_SHA` (still v0.53l-tip).
   - Part C: `model.py` matches `sha_pins.MODEL_SHA` (still v0.53l-tip).
9. **`test_bottom_k_helper_and_min_lineage_per_founder_override_targeting`** *(NEW; validates the new bottom-K helper + the override targeting at k=1)*:
   - `_select_bottom_k_sensor_radius_lineages` returns the bottom K lineages by sensor_radius (ascending) with `min(lineage_id)` tiebreak.
   - k=1 output is a single-element list of the argmin-sensor-radius lineage_id (with `min(lineage_id)` tiebreak on ties).
   - Tiebreak: `{0: 3, 1: 3, 2: 5, 3: 6, 4: 4}` with k=1 returns `[0]` (both 0 and 1 have sensor_radius=3; `min(lineage_id)` picks 0).
   - Asymmetry vs top: `{0: 7, 1: 3, 2: 5, 3: 6, 4: 4}` — `_select_bottom_k_sensor_radius_lineages(k=1) = [1]`, `_select_top_k_sensor_radius_lineages(k=1) = [0]`.
   - `build_bottom_k_per_founder_overrides(seed, trait_config, n_founders=5, k=1)` returns `(overrides, bottom_lineage_ids)` where exactly 1 of the 5 overrides is non-None and that position matches `bottom_lineage_ids[0]`.
10. **`test_per_founder_traits_overrides_seam_validation_carries_forward_from_v0_53l_m`** *(carry-forward; subset of v0.53l #9)*:
    - Mutual exclusivity raises `ValueError`.
    - Length validation raises `ValueError`.
    - Default-preserving: `per_founder_traits_overrides=None` is byte-identical to no argument.
11. **`test_label_a_high_sensor_radius_lineage_picks_correct_lineage_AND_matches_c_max_only_target_AND_label_a_indexes_max_not_min_on_d`** *(asymmetric — verifies Label A still picks the MAX-sensor lineage on D, which is the alignment-control mechanism)*:
    - On C: `is_high_sensor_radius_lineage` rows match `lineage_id == top_lineage_ids[0]`.
    - **On D: `is_high_sensor_radius_lineage` rows match `lineage_id == top_lineage_ids[0]` — NOT `lineage_id == bottom_lineage_ids[0]`. This is the alignment-control mechanism: the lineage Label A picks receives NO override on D.**
    - On E: `is_high_sensor_radius_lineage` rows match `lineage_id == top_lineage_ids[0]` (model-wide path; Label A indexes the same lineage but every lineage shares the same effective sensor radius).
12. **`test_label_b_four_variants_three_tier_tiebreak_at_each_window_with_pre400_c_and_d_and_e_only`** *(carry-forward shape from v0.53m #12)*.
13. **`test_pre400_window_strictly_extends_pre200_pre100_pre50_windows_on_c_and_d_and_e_arms`** *(carry-forward shape)*.
14. **`test_subverdict_present_requires_two_thirds_firing_cells_with_nan_treated_as_non_firing_strict`** *(carry-forward shape from v0.53m #14)*.
15. **`test_priority_3_min_lineage_label_b_opposite_sign_halt_is_reachability_gated_AND_label_a_specific_AND_d_label_a_wrong_sign_does_not_halt`** *(NEW shape — the asymmetric-halt central design point)*:
    - Branch A: D tick-400 Label B has a wrong-sign cell AND D reachability = 0.30 → priority 3 fires (`MIN_LINEAGE_LABEL_B_OPPOSITE_SIGN_HALT`).
    - Branch B: D tick-400 Label B has a wrong-sign cell BUT D reachability = 0.20 → priority 3 does NOT fire; priority 7 (`MIN_LINEAGE_ACCESS_BELOW_REACHABILITY_THRESHOLD`) fires instead.
    - Branch C: D tick-400 Label A has a wrong-sign cell (and Label B has NO wrong-sign cell) AND D reachability = 0.30 → priority 3 does NOT fire; **the asymmetric-halt rule routes this to priority 4 (DECOUPLES)** since Label A wrong-sign ⊂ Label A NOT PRESENT.
    - Branch D: D tick-400 both Label A AND Label B have wrong-sign cells AND D reachability = 0.30 → priority 3 fires (Label B wrong-sign alone is sufficient; Label A wrong-sign is additionally observed but does NOT contribute to the halt trigger).
    - Branch E: D Label B PRESENT + D Label A NOT PRESENT + D reachability = 0.30 → priority 4 fires.
    - Branch F: D Label A PRESENT + D Label B PRESENT + D reachability = 0.30 → priority 5 fires.
16. **`test_c_anchor_v053l_AND_e_anchor_v053k_AND_d_tick_400_reachability_threshold_partition_AND_rollup_locked_phrases_fire_verbatim_AND_priority_cascade_partition_total`** *(eight-or-more independent synthetic-fixture branches; combines v0.53m's #14/#15/#16 shapes)*:
    - C anchor reproduction: baseline GREEN; C reach drift halt; C sub-verdict drift halt; C paired_d drift halt.
    - E anchor reproduction: baseline GREEN; E reach drift halt; E sub-verdict-suffix drift halt; E paired_d drift halt.
    - D synthetic partition: 0.20 / 0.30 × {Label A: {PRESENT, NOT PRESENT}} × {Label B: {PRESENT, PARTIAL, NOT_FOUND, wrong-sign}} → priorities 3/4/5/6/7 fire correctly.
    - **Substring assertions VERBATIM:**
      - Priority 3: `"a v0.53n D_widened_food_near1_combined_min_lineage_sr8_N400 tick-400 **Label B** spatial / foraging primary fires in the WRONG direction"` AND `"D Label A wrong-sign or deadband is NOT a halt"` AND `"AND D reachability at tick-400 clears the locked 25% threshold"`.
      - Priority 4: `"the **min-sensor-lineage** per-lineage perception intervention"` AND `"the v0.48 \`is_high_sensor_radius_lineage\` selector still picks the MAX-sensor lineage for Label A indexing — that lineage receives NO override"` AND `"**The result is consistent with the v0.53l/m Label A rescue depending on alignment between the boosted perception channel and the max-sensor lineage label, while reachability itself can be rescued by perception access assigned to a non-max lineage.**"` AND substring references to v0.53c, v0.53d, v0.53e, v0.53f, v0.53g, v0.53h, v0.53i, v0.53j, v0.53k, v0.53l, v0.53m verdict names (ELEVEN-long predecessor stack).
      - Priority 5: `"**This is the surprising and high-information outcome.**"` AND `"the lineage labels / override targeting / measurement wiring need audit"` AND `"flagged for audit and follow-up"`.
      - Priority 6: `"a mixed or partial bridge signal that does not cleanly localize the alignment requirement"`.
      - Priority 7: `"**Min-lineage override is NOT symmetric with max-lineage override under this corpus and implementation.**"` AND `"starting position, early survival, trait package interactions"` AND substring references to v0.53c–v0.53m verdict names (ELEVEN-long predecessor stack).
    - Synthesize halt cascade (priorities 1 / 2.a / 2.b / 2.c / 2.d / 2.e / 2.f / 2.g / 2.h / 3); assert priority order. Exhaustively iterate the partition over priorities 4/5/6/7; assert unique outcome per cell.

## Watch-outs (for future-Chronus)

- **Alignment-control framing is the central design.** This is NOT a "same rescue, different target" probe. D Label A wrong-sign / deadband is **substantive decoupling evidence, not a halt**. The asymmetric halt rule (Label B specifically, not "any primary") is the design's load-bearing piece.
- **No `src/` changes.** v0.53l-tip's `per_founder_traits_overrides` + always-consume invariant seams cover all three intervention arms. `tests/sha_pins.py` unchanged.
- **Cross-script imports** of `_select_sensor_radius_label` from v0.53k's reducer (and optionally `_select_top_k_sensor_radius_lineages` from v0.53m's reducer for C). Test #11 must verify Label A indexing on D picks the MAX-sensor lineage, not the boosted MIN-sensor lineage — this is the alignment-control mechanism.
- **`_select_bottom_k_sensor_radius_lineages` tiebreak.** When two founders share the lowest sensor_radius, `min(lineage_id)` picks the one with the lower lineage_id — mirroring the top-K helper. Test #9 covers this with explicit tied fixtures.
- **`bottom_lineage_ids[0] != top_lineage_ids[0]` in the generic case.** If all five founders happen to share the same `sensor_radius` (degenerate edge case), both helpers return `[0]` (tied at min lineage_id). The test #6 cross-arm anti-confusion assert uses a synthetic fixture with distinct sensor_radii to verify the helpers diverge in the non-degenerate case. The reducer should descriptively log any run where `top_lineage_ids[0] == bottom_lineage_ids[0]` (it would indicate a degenerate sensor_radius sample) so the audit_log captures it; under V0_25 + the standard TraitConfig the probability is empirically low but non-zero.
- **Tier-1 / Tier-2 / Tier-3 anchor invariants on C and E are byte-stability checks for v0.53l-tip seams.** v0.53m observed drift_abs = 0.0 on all twelve in-slice anchor cells; v0.53n expects the same. Any drift on C or E surfaces a regression in the always-consume invariant or in `dataclasses.replace`'s preservation of trait fields under override propagation.
- **`is_high_sensor_radius_lineage` on D still picks the max-sensor founder** — i.e., the founder that does NOT receive the override. This is intentional and is the alignment-control mechanism. Future-Chronus tempted to "fix" this by re-pointing Label A at the boosted lineage on D would destroy the experiment.
- **Locked phrase discipline verbatim.** Predecessor stack now ELEVEN long: v0.53c/d/e/f/g/h/i/j/k/l/m. Test #16 substring asserts must reference all eleven verdict names in priorities 4 and 7.
- **Bounded-causality framing.** Priority 4 phrase says "**consistent with** the v0.53l/m Label A rescue depending on alignment" — not "the v0.48 bridge IS access-mediated." Strong evidence ≠ exclusive causality. The bounded claim is the load-bearing distinction between this slice and a stronger mechanistic conclusion.
- **Anti-rename trap (carried forward from v0.53k/l/m).** When copying v0.53m templates as starting seed, predecessor refs to v0.53m (and earlier) in priority-4/5/7 locked phrases AND test #16 substring assertions must be PRESERVED VERBATIM, NOT bulk-replaced to v0.53n. Only the slice's own self-reference (version label, output dir, file name, current verdict names) becomes v0.53n.
- **Reducer wall time** ~35–60 min on 320 runs. Use `run_in_background: true` on the Bash launching the reducer.
- **Branch is `claude/review-hedonism-harness-Ryyx0`**. Force-with-lease cleanup after squash-merge is the canonical pattern (used 3× last session).
- **Determinism north star** ([[scripts/core_smoke_test.py]]) must continue to pass after the new reducer + tests land. v0.53n makes no `src/` changes; the smoke test is a regression guard, not a verdict gate.

## Files this slice will create / modify

- `docs/experiments/fear_hunger_v0.53n.md` (this file; Results appended after reducer run)
- `scripts/v0_53n_perception_min_lineage_sensor_radius_8_audit.py` (new)
- `tests/test_v0_53n_perception_min_lineage_sensor_radius_8_audit.py` (new, 16 tests)

No `src/` modifications. No prior reducer / audit / test / pre-reg files modified. `tests/sha_pins.py` UNCHANGED.

## Results

*(Appended after reducer run on the locked 320-run corpus.)*
