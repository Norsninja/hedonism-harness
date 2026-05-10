# fear_hunger v0.53l — per-lineage perception heterogeneity probe (single max-sensor founder gets `effective_sensor_radius_override = 8`; Label A definition unchanged)

**Slice:** v0.53l
**Type:** **first-class observational sweep** with 4-arm asymmetric-horizon reducer. **Two additive `src/` carve-outs** are required and locked pre-reg: (1) `per_founder_traits_overrides` parameter on `run_chamber()` (`fear_hunger_chamber.py`); and (2) a **founder-construction RNG-invariance correction** in `model.py:_spawn_founder` — every founder construction consumes exactly one `random_traits(...)` draw from the mutation stream, regardless of whether that founder ultimately uses sampled traits, a global `traits_override`, or a per-founder override. v0.53e's `body_config` seam carries forward; `n_ticks` already exposed; `effective_sensor_radius_override` already a per-`Traits` field. The C-arm intervention assigns the override to **only the single max-sensor founder per run**, leaving the other four founders on default trait fallback; D arm is the in-slice positive anchor reproducing v0.53i / v0.53j / v0.53k D verbatim.
**Predecessors:** v0.46–v0.52b (full predecessor stack), v0.53 (`BRIDGE_PARTIALLY_GENERALIZES`), v0.53b (`WIDENED_BELOW_REACHABILITY_THRESHOLD_AT_TICK_100`), v0.53c (`WIDENED_BELOW_REACHABILITY_THRESHOLD_AT_TICK_200`), v0.53d (`WIDENED_BELOW_REACHABILITY_THRESHOLD_UNDER_RELAXED_INFLUX`), v0.53e (`RELAXED_OPPOSITE_SIGN_HALT`), v0.53f (`WIDENED_BELOW_REACHABILITY_THRESHOLD_UNDER_BASE_METABOLIC_COST_010`), v0.53g (`WIDENED_BELOW_REACHABILITY_THRESHOLD_UNDER_COMBINED_SE100_BMC010`), v0.53h (`WIDENED_BELOW_REACHABILITY_THRESHOLD_AT_TIME_HORIZON_400`), v0.53i (`WIDENED_BRIDGE_RESCUED_BY_FOOD_NEAR2`), v0.53j (`WIDENED_BELOW_REACHABILITY_THRESHOLD_UNDER_FOOD_NEAR1`), v0.53k (`WIDENED_BRIDGE_PARTIALLY_RESCUED_BY_SENSOR_RADIUS_8` — model-wide override rescued reachability `0/64 → 64/64` AND label-B bridge expression, but Label A collapsed by construction of the homogenizing intervention).
**Question being asked (locked):** Does **lineage-specific** perception rescue restore the v0.48 Label A bridge fingerprint? Specifically: with the script-local `widened_food_near1` layout (`food_x∈[9,13]`, 1-column corridor at `x=8`), `BodyConfig(starting_energy=100.0, base_metabolic_cost=0.10)`, `n_ticks=400`, AND **only the single max-sensor founder per run receiving `Traits(effective_sensor_radius_override=8)`** (other four founders: trait-fallback default), does C tick-400 reachability cross 0.25 AND does the v0.48 Label A bridge fire PRESENT?

v0.53k established that a model-wide `effective_sensor_radius_override = 8` lifts FOOD_NEAR1 reachability from `0/64` (v0.53j C) to `64/64` while collapsing Label A's three-cell expression into the ±0.5 deadband (signed_d −0.019, −0.019, −0.002). The collapse is **expected by construction** of the homogenizing intervention: under model-wide override, every lineage perceives at the same effective radius, so the trait-indexed bridge has no remaining access gradient to track. v0.53k's clean claim was: *model-wide sensor_radius=8 rescues FOOD_NEAR1 access and readiness-indexed bridge expression, but it does not preserve the original trait-indexed sensor_radius bridge fingerprint*.

v0.53l directly probes the next question: if perception heterogeneity **between** lineages is preserved while still granting sufficient perceptual reach to the labeled lineage, does the v0.48 Label A bridge return? The intervention is constructed to align exactly with the existing v0.48 label definition: per `src/hedonism_harness/model.py:1441`, `is_high_sensor_radius_lineage` is a single-lineage tag (the founder with maximum `traits.sensor_radius` per run, with tiebreak `min(lineage_id)`). v0.53l grants `effective_sensor_radius_override = 8` to **that exact lineage**, and that lineage only.

The chosen seam is **a single additive parameter on `run_chamber()`** plus a **founder-construction RNG-invariance correction** in `model.py`. The parameter — `per_founder_traits_overrides: Sequence[Traits | None] | None = None` — must have length `n_founders` when provided and is mutually exclusive with the existing global `traits_override` (both non-None raises `ValueError`). The RNG-invariance correction replaces the current short-circuit founder-construction pattern (`spec.traits_override if spec.traits_override is not None else random_traits(...)`) with an always-consume pattern (`sampled_traits = random_traits(...); traits = spec.traits_override if spec.traits_override is not None else sampled_traits`), so founder trait sampling consumes exactly one mutation-stream draw per founder regardless of override presence. **Without this correction, the per-founder override would change two things at once — which lineage gets the override AND the downstream mutation RNG state — poisoning the experiment's interpretation.** Default no-override paths remain byte-identical for all v0.1..v0.53k callers; override paths become stream-invariant by construction. Per `src/hedonism_harness/core/traits.py:60-66`, `effective_sensor_radius_override` is excluded from `TRAIT_NAMES`, never mutated by `mutate_traits` / `random_traits`, and **automatically inherited through reproduction** via `dataclasses.replace(parent, **values)` (the field is on `parent` and not in `values`, so `replace` preserves it). The override therefore propagates from the targeted founder to all descendants of that lineage at zero additional cost; the intervention is genuinely lineage-level, not founder-only.

**The single-max design's interpretive value (locked):** if C tick-400 reachability ≥ 25% AND C tick-400 sub-verdict resolves PRESENT under both labels, the v0.48 Label A bridge can be restored by **targeted lineage-specific perceptual access** while between-lineage trait heterogeneity is preserved. v0.53k's Label A collapse is then attributable to model-wide homogenization, not to sensor-reach itself. If reachability rises but only Label B fires, perception is sufficient for access but the original trait bridge does not recover under single-lineage override — implying the bridge is more outcome / readiness-mediated than trait-mediated under FOOD_NEAR1. If reachability < 25%, single-max perception is insufficient, and v0.53m candidates (top-K, threshold-based, multi-lineage perception) become justified.

## Pre-implementation note (2026-05-10, before any reducer code)

Earlier framing of v0.53l considered a top-2 / threshold variant on the grounds that single-max override might cap reachability at ~`1/64` per run. **This framing was incorrect**: reachability is a run-level metric (a run clears the threshold if ANY founder lineage produces a food event), not a lineage-count metric. A single max-lineage override can therefore still produce `64/64` reachability if the targeted lineage successfully reaches food in every run. The stronger reason for the single-max design is **intervention-to-label alignment**: v0.53l assigns `effective_sensor_radius_override = 8` to the exact lineage used by the existing v0.48 Label A definition (`is_high_sensor_radius_lineage = (lineage_id == argmax(sensor_radius), tiebreak min(lineage_id))` per `model.py:1441` and `_select_sensor_radius_label` reused verbatim from v0.53k's reducer at line 1205). Preserving the original bridge label while restoring heterogeneous perception is the cleanest, most falsifiable, most historically continuous test of the v0.48 bridge.

The pre-reg's design was confirmed with the user before drafting:

- **4 arms (asymmetric `n_ticks`).** A_null_V0_25 (tight_gradient, V0_25, `n_ticks=200`, anchor). B_widened_V0_25 (widened_gradient, V0_25, `n_ticks=200`; predecessor lock). **C_widened_food_near1_combined_max_lineage_sr8_N400** (script-local FOOD_NEAR1 layout; V0_25 substrate **except** `BodyConfig(starting_energy=100.0, base_metabolic_cost=0.10)` AND **per-founder override**: `effective_sensor_radius_override=8` on the single max-sensor founder per run, `None` on the other four; `n_ticks=400`; primary verdict-gating). D_widened_food_near2_combined_N400 (script-local FOOD_NEAR2 layout — byte-identical to v0.53i C / v0.53j D / v0.53k D; `BodyConfig(starting_energy=100.0, base_metabolic_cost=0.10)`; default sensor (no override); `n_ticks=400`; in-slice positive anchor). Same 64-tuple corpus. **256 runs.**
- **Single perception knob on C; D matches v0.53i/v0.53j/v0.53k positive anchor exactly.** v0.53l holds FOOD_NEAR1 layout fixed and varies the override granularity from model-wide (v0.53k) to single-lineage (v0.53l). C and D differ by exactly two things: layout (FOOD_NEAR1 vs FOOD_NEAR2) AND the per-founder override scheme (single-max=8 vs no override on D).
- **Per-founder override is constructed at C-arm setup**, not via the existing global `traits_override` (which v0.53l does not use on any arm).
- **Both novel layouts constructed script-local — no `src/` change to `layouts.py`.** Module-level constants `FOOD_NEAR1_LAYOUT` and `FOOD_NEAR2_LAYOUT` carry forward IDENTICAL geometry from v0.53j/k. `layouts.py` SHA still `d4521cb5...`.
- **Two additive `src/` carve-outs.** (1) `run_chamber()` gains `per_founder_traits_overrides: Sequence[Traits | None] | None = None`. Mutual-exclusion check (raise `ValueError` if both `traits_override` and `per_founder_traits_overrides` are non-None). Length check (raise `ValueError` if `len(per_founder_traits_overrides) != n_founders`). Default `None` preserves byte-identity for v0.1..v0.53k callers. (2) `model.py:_spawn_founder` (or the founder-construction loop) is changed from short-circuit (`override if override is not None else random_traits(...)`) to always-consume (`sampled = random_traits(...); traits = override if override is not None else sampled`). This is a **named conservation carve-out**: it is one line in practice but it is a behavioral invariant change for override paths — the mutation stream now advances exactly once per founder regardless of override presence. No-override paths remain byte-identical. Determinism north star (`scripts/core_smoke_test.py`) must continue to pass.
- **`Traits.effective_sensor_radius_override` carries forward from v0.52b.** Excluded from `TRAIT_NAMES`; never mutated by `mutate_traits` / `random_traits` / `validate_traits`; automatically inherited through reproduction via `dataclasses.replace(parent, **values)`. The targeted founder's lineage retains the override across all descendants at zero additional cost; the intervention is genuinely lineage-level.
- **Reachability-gated priority 3 (carries forward, RENAMED `MAX_LINEAGE_PERCEPTION_OPPOSITE_SIGN_HALT`).** Same gating logic: priority 3 fires iff C tick-400 sub-verdict = `OPPOSITE_SIGN_HALT` AND `c_reachability_tick_400 ≥ 0.25`.
- **Tick-400 verdict gating on C; tick-400 anchor on D; tick-200 descriptive on A/B.** Same 4-window observer structure as v0.53i/j/k.
- **Tier-2 categorical anchor on B_widened_V0_25 preserved** (reachability tick-200 == `0/64`).
- **Tier-3 positive anchor on D preserved verbatim from v0.53j/k** (categorical reachability + sub-verdict + six paired_d cells reproducing v0.53i within 1e-3).
- **Predecessor stack now NINE long**: v0.53c..v0.53k (matching the chain length recorded in v0.53k's locked phrases plus v0.53k itself).
- **Label A definition is locked unchanged from v0.48.** Same `is_high_sensor_radius_lineage` selector with `argmax(sensor_radius), tiebreak min(lineage_id)`. The intervention targets the exact lineage the label picks.
- **Expected behavioral identity between v0.53l D and v0.53j D / v0.53k D / v0.53i C through tick-400.** Same layout, same body_config, same n_ticks, same RNG, no override on D. D tick-400 reachability is mechanically guaranteed to match v0.53i's `35/64`.

## Conservation framing — observational, two additive `src/` carve-outs, single per-lineage perception knob on C

v0.53l introduces **one additive chamber seam AND one founder-construction RNG-invariance correction**. The correction forces founder construction to consume exactly one mutation-stream trait draw per founder before applying any trait override. Default no-override paths remain byte-identical; override paths become stream-invariant by construction.

- **Carve-out (1): `run_chamber()` gains `per_founder_traits_overrides`.** Default `None` preserves all prior slice behavior (v0.1..v0.53k callers unchanged). `fear_hunger_chamber.py` SHA changes from v0.53e-tip `62d134c5...` to a NEW v0.53l-tip SHA recorded at implementation time.
- **Carve-out (2): `model.py:_spawn_founder` adopts the always-consume invariant.** `random_traits(self.trait_config, self.streams.mutation)` is called exactly once per founder regardless of override presence. The result is used iff `spec.traits_override is None`; otherwise discarded. `model.py` SHA changes to a NEW v0.53l-tip value.
- **Science-core five files (sensors / traits / body / config / layouts) remain byte-identical to v0.52b-tip.** Pinned in test #8 Part A.
- **No modifications to prior reducer or audit scripts.** v0.53k's reducer remains byte-identical to its merged form. v0.53l's reducer reuses `_select_sensor_radius_label` from v0.53k's reducer via cross-script import (the established `importlib.util` pattern per CLAUDE.md "Cross-script imports").
- **A_null_V0_25 arm is byte-identical to v0.48–v0.53k A_null path AT TICK-50.** Tier-1 re-anchor enforces this within 1e-3.
- **B_widened_V0_25 arm is byte-identical to v0.53–v0.53k's B_widened arm at every tick 0..200.** Tier-2 categorical anchor enforces `b_widened_v025_reachability_run_share_tick_200 == 0.0`.
- **D_widened_food_near2_combined_N400 arm is byte-identical to v0.53i C and v0.53j D and v0.53k D at every tick 0..400.** Tier-3 positive anchor enforces (a) reachability_tick_400 == 35/64 exact, (b) sub-verdict == BRIDGE_PRESENT, (c) six paired_d cells within 1e-3 of v0.53i published values.
- **C arm differs from v0.53k C by exactly the override-granularity knob:** model-wide `body_config.effective_sensor_radius_override = 8` (v0.53k C) → per-founder `per_founder_traits_overrides[max_lid] = Traits(..., effective_sensor_radius_override=8)`, others `None` (v0.53l C). Body config on C drops the `effective_sensor_radius_override` field from `BodyConfig` (back to `BodyConfig(starting_energy=100.0, base_metabolic_cost=0.10)`).
- **No intervention at any level on any arm beyond the documented per-founder override on C.** No founder body trait modification post-construction, no override patching, no helper RNG, no shuffle, no clamp, no permutation.

## Test #8 maintenance policy (locked, pre-implementation) — shared `tests/sha_pins.py`

**v0.53l introduces a second intentional `src/` carve-out. Science-core files remain pinned to their historical v0.52b hashes. Mutable experiment-seam files are now pinned through `tests/sha_pins.py` so the active test suite checks the current approved chamber/model state rather than stale per-slice literals. This is test-maintenance only; prior slice verdict logic and locked phrases are not changed.**

A new shared module `tests/sha_pins.py` exposes the current approved mutable-seam pins:

```python
# tests/sha_pins.py
"""Current-tree SHA pins for mutable experiment-seam files.

Science-core files (sensors / traits / body / config / layouts) are pinned
to their historical v0.52b hashes in each slice's test #8 Part A and do NOT
move. Mutable experiment-seam files (chamber driver, model) are pinned here
to the current approved tree state and updated only when an intentional
additive src/ carve-out lands (e.g., v0.53e's body_config seam, v0.53l's
per_founder_traits_overrides + always-consume invariant).
"""

CHAMBER_DRIVER_SHA: str = "<v0.53l-tip sha; recorded at implementation>"
MODEL_SHA: str = "<v0.53l-tip sha; recorded at implementation>"
```

**v0.53l's test #8** (in `tests/test_v0_53l_perception_max_lineage_sensor_radius_8_audit.py`) checks:
- Part A: science-core five files match v0.52b-tip historical SHAs (unchanged from v0.53e–v0.53k).
- Part B: `fear_hunger_chamber.py` matches `sha_pins.CHAMBER_DRIVER_SHA`.
- Part C (NEW): `model.py` matches `sha_pins.MODEL_SHA`.

**v0.53e–v0.53k's prior test #8s** are migrated to import from `tests/sha_pins.py` instead of hardcoded `62d134c5...` literals. **This is bookkeeping, not logic** — verdict logic, anchor logic, and historical claims of those prior slices are not touched. Each prior test file's chamber-driver assertion now reads `assert chamber_sha == sha_pins.CHAMBER_DRIVER_SHA` (or equivalent), and any future intentional chamber/model carve-out updates a single value in `sha_pins.py` rather than fanning out across N prior test files.

Migration scope:
```
tests/sha_pins.py                                           (new — shared pins)
tests/test_v0_53e_substrate_axis_starting_energy_audit.py   (chamber pin → import)
tests/test_v0_53f_substrate_axis_base_metabolic_cost_audit.py
tests/test_v0_53g_substrate_axis_combined_se100_bmc010_audit.py
tests/test_v0_53h_time_horizon_extension_n400_audit.py
tests/test_v0_53i_geometry_food_near2_audit.py
tests/test_v0_53j_food_distance_dose_response_audit.py
tests/test_v0_53k_perception_sensor_radius_8_audit.py
tests/test_v0_53l_perception_max_lineage_sensor_radius_8_audit.py   (new — Parts A/B/C)
```

Skipping the assertions is explicitly **not** the policy: skips would let accidental src drift pass unnoticed. The shared module preserves the value of every prior slice's SHA check while routing the SHA through one maintenance surface.

## Corpus (locked, 64 × 4 arms = 256 runs; asymmetric wall time)

Same shape as v0.53d–v0.53k:

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
... (V0_25 baseline; body_config=None; per_founder_traits_overrides=None; n_ticks=200)
```

Byte-identical to v0.48–v0.53k A_null. **Tier-1 anchor at tick-50.**

### B_widened_V0_25

```
ChamberLayout = widened_gradient_layout()
... (V0_25 baseline; body_config=None; per_founder_traits_overrides=None; n_ticks=200)
```

Byte-identical to v0.53–v0.53k's B_widened. **Tier-2 categorical anchor on tick-200 reachability.**

### C_widened_food_near1_combined_max_lineage_sr8_N400 (PRIMARY VERDICT-GATING)

```
ChamberLayout = ChamberLayout(  # script-local FOOD_NEAR1_LAYOUT (identical to v0.53j C / v0.53k C)
    safe_x_min=0, safe_x_max=4,
    hazard_x_min=5, hazard_x_max=7,
    food_x_min=9, food_x_max=13,
    height=6, spawn_x=1,
)
... (V0_25 baseline pool/ecology;
    body_config = BodyConfig(starting_energy=100.0, base_metabolic_cost=0.10);
                  # NO body_config.effective_sensor_radius_override (v0.53k carried this; v0.53l does NOT)
    per_founder_traits_overrides[max_lid] = Traits(  # PER-FOUNDER OVERRIDE — NEW in v0.53l
        ..., effective_sensor_radius_override=8,
    );
    per_founder_traits_overrides[other_lids] = None;
    n_ticks = 400)
```

Where `max_lid` is selected per run by `_select_sensor_radius_label` (argmax(sensor_radius), tiebreak min(lineage_id)). The override propagates to that lineage's descendants automatically via `mutate_traits`'s `dataclasses.replace`.

Differs from v0.53k C by the override granularity knob: model-wide → per-founder, single-max only. Differs from D by layout (FOOD_NEAR1 vs FOOD_NEAR2) AND the per-founder override (single-max=8 vs all None). **The primary arm of v0.53l**: the verdict gates on C's tick-400 reachability and tick-400 sub-verdict.

### D_widened_food_near2_combined_N400 (IN-SLICE POSITIVE ANCHOR)

```
ChamberLayout = ChamberLayout(  # script-local FOOD_NEAR2_LAYOUT (identical to v0.53j D / v0.53k D / v0.53i C)
    safe_x_min=0, safe_x_max=4,
    hazard_x_min=5, hazard_x_max=7,
    food_x_min=8, food_x_max=12,
    height=6, spawn_x=1,
)
... (V0_25 baseline pool/ecology;
    body_config = BodyConfig(starting_energy=100.0, base_metabolic_cost=0.10);
    per_founder_traits_overrides = None;  # default; matches v0.53i/j/k D
    n_ticks = 400)
```

Byte-identical to v0.53i's C arm, v0.53j's D arm, AND v0.53k's D arm at every tick 0..400. **Tier-3 positive anchor:** D tick-400 reachability == 35/64 exact AND sub-verdict == BRIDGE_PRESENT AND six paired_d cells reproduce v0.53i within 1e-3.

## Labels (locked, two — Label A definition unchanged from v0.48)

Identical to v0.53j/k: Label A (`is_high_sensor_radius_lineage` — selected via `_select_sensor_radius_label`, the argmax-with-min-lineage-tiebreak rule from v0.48); Label B variants `is_high_tick{50,100,200,400}_readiness_fraction_lineage` (tick-400 variant computed on C and D only; NaN-broadcast on A/B). **The C-arm intervention deliberately targets the same lineage Label A picks.**

## Primary observables (locked, 3, four windows on C/D, three on A/B)

Identical to v0.53j/k. Note: observable 3 (`mean_distance_to_nearest_food_cell_tick{N}`) uses each arm's layout food cells; cross-arm signed_d is NOT directly cross-arm interpretable.

## Effect-size rule (locked, sign-aware, identical to v0.48–v0.53k)

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
    (VERDICT-GATING; threshold 0.25)

d_widened_food_near2_combined_N400_reachability_run_share_tick_400 =
    (TIER-3 POSITIVE ANCHOR — must equal 35/64 = 0.546875 exactly)
```

## Tier-3 positive anchor on D (locked, pre-data, identical to v0.53j/k)

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

Note: v0.53j and v0.53k Results both recorded D anchor reproduction with **drift_abs = 0.0** on every cell (perfect determinism). v0.53l expects the same. The new `per_founder_traits_overrides` parameter defaults to `None` on D, so the chamber-driver code path on D is byte-identical to v0.53k D.

## Per-arm sub-verdicts (locked, 4-way each — verdict-gating on C tick-400; anchor on D tick-400)

| condition | A_null_V0_25 | B_widened_V0_25 | C_widened_food_near1_combined_max_lineage_sr8_N400 (tick-400 **verdict-gating**) | D_widened_food_near2_combined_N400 (tick-400 **anchor**) |
|---|---|---|---|---|
| both labels clear ≥ 2/3 cells, NaN non-firing, 0 wrong-sign | `A_NULL_V025_TICK{50,100,200}_BRIDGE_PRESENT` | `B_WIDENED_V025_TICK200_BRIDGE_PRESENT` | `C_WIDENED_FOOD_NEAR1_MAX_LINEAGE_SR8_TICK400_BRIDGE_PRESENT` | `D_WIDENED_FOOD_NEAR2_TICK400_BRIDGE_PRESENT` |
| exactly one label clears ≥ 2/3 cells | `..._BRIDGE_PARTIAL` | ... | `..._BRIDGE_PARTIAL` | `..._BRIDGE_PARTIAL` |
| neither clears ≥ 2/3 cells | `..._BRIDGE_NOT_FOUND` | ... | `..._BRIDGE_NOT_FOUND` | `..._BRIDGE_NOT_FOUND` |
| any primary signed_d ≤ −0.5 | `..._OPPOSITE_SIGN_HALT` | ... | `..._OPPOSITE_SIGN_HALT` | `..._OPPOSITE_SIGN_HALT` |

**Strict NaN-treated-as-non-firing rule preserved.** C's sub-verdict prefix is `C_WIDENED_FOOD_NEAR1_MAX_LINEAGE_SR8_TICK{N}_BRIDGE_{...}` (the `_MAX_LINEAGE_SR8` suffix distinguishes from v0.53k's `_SR8` and v0.53j's bare `_TICK{N}`).

## Slice rollup verdicts (locked, 6 outcomes, priority-ordered)

1. `CORPUS_REDERIVE_DRIFT_HALT`
2. `ANCHOR_REPLICATION_HALT` (Tier-1 + Tier-2 + Tier-3; same six sub-conditions as v0.53j/k)
3. `MAX_LINEAGE_PERCEPTION_OPPOSITE_SIGN_HALT` (**reachability-gated** on C tick-400; renamed from v0.53k's `PERCEPTION_OPPOSITE_SIGN_HALT` to reflect the per-lineage scope)
4. `WIDENED_BRIDGE_RESCUED_BY_MAX_LINEAGE_SENSOR_RADIUS_8`
5. `WIDENED_BELOW_REACHABILITY_THRESHOLD_UNDER_MAX_LINEAGE_SENSOR_RADIUS_8`
6. `WIDENED_BRIDGE_PARTIALLY_RESCUED_BY_MAX_LINEAGE_SENSOR_RADIUS_8`

### Halt conditions

| priority | rollup verdict | trigger | locked phrase (verbatim) |
|---|---|---|---|
| 1 | `CORPUS_REDERIVE_DRIFT_HALT` | A `a_share_h8` for v0.42/v0.44/v0.45 drifts > 1e-3 | "Halt: A_null_V0_25 re-anchor drifted from the published Results value for {version}; v0.53l's deterministic re-execution of the V0_25 corpus does not reproduce the published metric within 1e-3." |
| 2 | `ANCHOR_REPLICATION_HALT` | (a) A tick-50 paired_d drift > 1e-3, (b) A tick-50 sub-verdict ≠ PRESENT, (c) B tick-200 reachability ≠ 0, (d) D tick-400 reachability ≠ 35/64 exact, (e) D tick-400 sub-verdict ≠ BRIDGE_PRESENT, (f) D tick-400 paired_d drift > 1e-3 | "Halt: v0.53l's A_null_V0_25 arm does not reproduce v0.48–v0.53k's tick-50 spatial bridge, OR v0.53l's B_widened_V0_25 arm does not reproduce v0.53c–v0.53k's `0/64` reachability lock at tick-200, OR v0.53l's D_widened_food_near2_combined_N400 arm does not reproduce v0.53i's tick-400 positive anchor (categorical reachability `35/64` AND sub-verdict `BRIDGE_PRESENT` AND six published paired_d cells within 1e-3). v0.53l cannot interpret the C_widened_food_near1_combined_max_lineage_sr8_N400 cells without reproducing both the V0_25 baseline anchors and the v0.53i FOOD_NEAR2 positive anchor." |
| 3 | `MAX_LINEAGE_PERCEPTION_OPPOSITE_SIGN_HALT` (**reachability-gated**) | C tick-400 sub-verdict = `OPPOSITE_SIGN_HALT` AND `c_reachability_tick_400 ≥ 0.25` | "Halt: a v0.53l C_widened_food_near1_combined_max_lineage_sr8_N400 tick-400 spatial / foraging primary fires in the WRONG direction under a gating label, AND C reachability at tick-400 clears the locked 25% threshold. The per-lineage perception intervention (`per_founder_traits_overrides[max_lid] = Traits(effective_sensor_radius_override=8)`) under FOOD_NEAR1 + combined founder-facing budget envelope at `n_ticks = 400` surfaces a regime where the locked expected signs do not hold under measurable food access. The reachability-gated trigger preserves v0.53e's locked sign discipline while excluding the v0.53e-style measurement-edge case (wrong-sign at reachability=0)." |

### Outcome conditions (only consulted if no halt fires)

| priority | rollup verdict | trigger | locked phrase (verbatim) |
|---|---|---|---|
| 4 | `WIDENED_BRIDGE_RESCUED_BY_MAX_LINEAGE_SENSOR_RADIUS_8` | `c_widened_food_near1_combined_max_lineage_sr8_N400_reachability_run_share_tick_400 ≥ 0.25` AND C tick-400 sub-verdict = `C_WIDENED_FOOD_NEAR1_MAX_LINEAGE_SR8_TICK400_BRIDGE_PRESENT` | "On the modern A_null corpus with the V0_25 substrate held constant except for the combined founder-facing budget relaxation `BodyConfig(starting_energy=100.0, base_metabolic_cost=0.10)` AND the simulation horizon doubled to `n_ticks=400` AND the `widened_food_near1` layout (`food_x∈[9,13]`, 1-column corridor at `x=8`; identical to v0.53j C / v0.53k C) AND the per-lineage perception intervention `per_founder_traits_overrides[max_lid] = Traits(effective_sensor_radius_override=8)` (the override applies ONLY to the single max-`sensor_radius` founder per run, with the v0.48 `is_high_sensor_radius_lineage` selector — argmax with min-lineage-id tiebreak — picking the same lineage Label A indexes; metabolic cost UNAFFECTED per the override's information-channel-only contract; override propagates to all descendants via `dataclasses.replace`'s preservation), the v0.48 sensor_radius spatial / foraging bridge fires PRESENT under the locked +0.5 paired_d threshold at tick-400 under both gating labels. The geometry/substrate cell that v0.53c locked as `WIDENED_BELOW_REACHABILITY_THRESHOLD_AT_TICK_200`, v0.53d locked as `WIDENED_BELOW_REACHABILITY_THRESHOLD_UNDER_RELAXED_INFLUX`, v0.53e locked as `RELAXED_OPPOSITE_SIGN_HALT`, v0.53f locked as `WIDENED_BELOW_REACHABILITY_THRESHOLD_UNDER_BASE_METABOLIC_COST_010`, v0.53g locked as `WIDENED_BELOW_REACHABILITY_THRESHOLD_UNDER_COMBINED_SE100_BMC010`, v0.53h locked as `WIDENED_BELOW_REACHABILITY_THRESHOLD_AT_TIME_HORIZON_400`, v0.53i locked as `WIDENED_BRIDGE_RESCUED_BY_FOOD_NEAR2`, v0.53j locked as `WIDENED_BELOW_REACHABILITY_THRESHOLD_UNDER_FOOD_NEAR1`, and v0.53k locked as `WIDENED_BRIDGE_PARTIALLY_RESCUED_BY_SENSOR_RADIUS_8` admits a measurable bridge under the per-lineage perception intervention: B_widened_V0_25 reachability remains `0/64` at tick-200 (predecessor lock holds), D_widened_food_near2_combined_N400 reachability reproduces v0.53i's `35/64` positive anchor at tick-400 (positive lock holds), C reachability at tick-400 clears the locked 25% threshold, and ≥ 2/3 spatial / foraging primaries fire PRESENT under both gating labels at the C tick-400 panel. **The v0.53k Label A collapse is consistent with model-wide perception homogenization being the proximate cause of bridge-fingerprint loss, not sensor-reach itself**: lineage-specific perception heterogeneity restores Label A under sufficient targeted access. This is strong evidence but NOT exclusive causality — the targeted lineage may also drive Label A firing through secondary channels (asymmetric early survival, reproduction-rate differential, pleiotropy with other heritable traits). This does NOT prove `the v0.48 bridge is exclusively trait-mediated`; NOT `model-wide perception interventions are inferior in all settings`: `WIDENED_BRIDGE_RESCUED_BY_MAX_LINEAGE_SENSOR_RADIUS_8`." |
| 5 | `WIDENED_BELOW_REACHABILITY_THRESHOLD_UNDER_MAX_LINEAGE_SENSOR_RADIUS_8` | `c_widened_food_near1_combined_max_lineage_sr8_N400_reachability_run_share_tick_400 < 0.25` | "On the modern A_null corpus with the V0_25 substrate held constant except for the combined founder-facing budget relaxation `BodyConfig(starting_energy=100.0, base_metabolic_cost=0.10)` AND the simulation horizon doubled to `n_ticks=400` AND the `widened_food_near1` layout AND the per-lineage perception intervention `per_founder_traits_overrides[max_lid] = Traits(effective_sensor_radius_override=8)`, fewer than 25% of C runs have any founder lineage with pre400 food events. C's reachability is below the locked 25% threshold at tick-400; D_widened_food_near2_combined_N400 reproduces v0.53i's `35/64` positive anchor at tick-400 in-slice. The single-max-lineage perception intervention is **insufficient** to lift FOOD_NEAR1 reachability under the tested envelope. The geometry/substrate cell that v0.53c locked as `WIDENED_BELOW_REACHABILITY_THRESHOLD_AT_TICK_200`, ..., v0.53k locked as `WIDENED_BRIDGE_PARTIALLY_RESCUED_BY_SENSOR_RADIUS_8` is not rescued by the per-lineage perception intervention at single-max scope. This does NOT prove `lineage-specific perception is irrelevant` — only that this specific single-lineage scheme does not clear the threshold. v0.53m (or later) candidates shift toward broader lineage coverage (top-K, threshold-based) or policy / hazard-avoidance / movement probes: `WIDENED_BELOW_REACHABILITY_THRESHOLD_UNDER_MAX_LINEAGE_SENSOR_RADIUS_8`." |
| 6 | `WIDENED_BRIDGE_PARTIALLY_RESCUED_BY_MAX_LINEAGE_SENSOR_RADIUS_8` | `c_widened_food_near1_combined_max_lineage_sr8_N400_reachability_run_share_tick_400 ≥ 0.25` AND C tick-400 sub-verdict ∈ {PARTIAL, NOT_FOUND} | "On the modern A_null corpus with the V0_25 substrate held constant except for the combined founder-facing budget relaxation AND the per-lineage perception intervention `per_founder_traits_overrides[max_lid] = Traits(effective_sensor_radius_override=8)` on FOOD_NEAR1 at `n_ticks=400`, C's reachability clears the locked 25% threshold at tick-400 but the v0.48 sensor_radius spatial / foraging bridge does not fully fire PRESENT — fewer than 2/3 primaries fire across both gating labels at tick-400 under the strict NaN rule. D_widened_food_near2_combined_N400 reproduces v0.53i's `35/64` positive anchor at tick-400 in-slice. The single-max-lineage perception intervention admits measurable food access but does not fully replicate v0.53i's PRESENT bridge expression under the matched corpus. Layout-specific partial-rescue logged in Results: `WIDENED_BRIDGE_PARTIALLY_RESCUED_BY_MAX_LINEAGE_SENSOR_RADIUS_8`." |

The 3 non-halt outcomes form a total partition (same as v0.53j/k). Test #16 enforces the partition exhaustively.

## Cautious framing (per CLAUDE.md, refined per user direction)

- **"Consistent with model-wide perception homogenization being the proximate cause of bridge-fingerprint loss, not sensor-reach itself"** (priority 4) — NOT "the v0.48 bridge is exclusively trait-mediated"; NOT "model-wide perception interventions are inferior in all settings"; NOT exclusive causality. The targeted lineage may also drive Label A firing through secondary channels (asymmetric early survival, reproduction-rate differential, pleiotropy with other heritable traits).
- **"Single-max-lineage perception intervention is insufficient to lift FOOD_NEAR1 reachability under the tested envelope"** (priority 5) — NOT "lineage-specific perception is irrelevant"; NOT "the v0.48 bridge cannot be restored". The bounded claim is that the single-max scheme at `r=8` does not clear the threshold under FOOD_NEAR1 + combined-budget × n_ticks=400.
- **"Tested intervention" means `per_founder_traits_overrides[max_lid] = Traits(effective_sensor_radius_override=8)`** with the v0.48 selector specifically. v0.53l does NOT establish behavior at top-2, threshold-based, or random-lineage assignment; those require separate slices.
- v0.53l explicitly does not establish: cross-layout generalization beyond the named layouts, mechanism for any rescue or non-rescue outcome at single-max=8, generalization to non-V0_25 substrates, behavior at non-`n_ticks=400` horizons under the same intervention, dose-response below or above r=8 under the per-lineage scheme, behavior under reproduction failure (if the targeted founder dies before reproducing, the override is lost from the population — descriptively logged).

## What v0.53l cannot establish

- ✗ **"The v0.48 bridge is exclusively trait-mediated"** under priority 4. Strong evidence ≠ exclusive causality. Single-max override targets the same lineage as Label A; secondary channels (early-survival differential, reproduction success, trait pleiotropy) cannot be ruled out.
- ✗ **"Lineage-specific perception is irrelevant"** under priority 5. The v0.53l null at single-max-only establishes that this specific scheme is insufficient under the tested envelope; it does not establish that broader lineage coverage cannot rescue.
- ✗ **"r=8 is the minimum sufficient override"** under priority 4. v0.53l does NOT test r=7 or smaller under the per-lineage scheme.
- ✗ **A revised v0.53–v0.53k verdict.** All eleven predecessor verdicts stand as historical contracts.
- ✗ **Mechanism behind any rescue or non-rescue outcome.** Population dynamics under V0_25 × FOOD_NEAR1 × combined-budget × `n_ticks=400` × single-max `r=8` are descriptively logged; no mechanism is formally established.

## Open framing (NOT in v0.53l primary)

- **If priority 4 fires (per-lineage rescue restores Label A):**
  - **v0.53m candidate — top-2 / threshold variant.** Test whether broader lineage coverage retains Label A firing or whether the high-radius runner-up dilutes the contrast.
  - **v0.53n candidate — Reading-A causal-generalization on FOOD_NEAR1 + max-lineage sr=8.** With Label A's bridge restored, the v0.49–v0.52b causal-generalization framework re-anchors on the rescued cell.
  - **v0.53o candidate — random-lineage override (control).** Test whether assigning `r=8` to a NON-max lineage (e.g., min-sensor lineage) breaks Label A firing despite restored access.
- **If priority 5 fires (single-max insufficient):**
  - **v0.53m candidate — top-2 lineage perception probe.**
  - **v0.53n candidate — threshold-based perception (`sensor_radius >= T → r=8`).**
  - **v0.53o candidate — policy / hazard-avoidance probe at FOOD_NEAR1.**
- **If priority 6 fires (partial rescue under single-max):**
  - **v0.53m candidate — diagnostic descriptive expansion.** Characterize which of label A's three cells fires and which doesn't; correlate with reproduction success of the targeted lineage.
- **v0.54 — joint ablation.** Eventually fresh-stream calibration on the full v0.46–v0.53l stack.

## Re-anchor (locked — Tier-1 and corpus only at tick-50)

| version | published `a_share_h8` |
|---|---|
| v0.42 | 0.652 |
| v0.43R | NOT PUBLISHED (informational-only) |
| v0.44 | 0.878 |
| v0.45 | 0.818 |

## Outputs (locked)

```
runs/v0.53l-perception-max-lineage-sensor-radius-8/per_run_per_lineage_v053l.csv
  columns: arm, layout_name,
           safe_x_min, safe_x_max, hazard_x_min, hazard_x_max,
           food_x_min, food_x_max, world_width, spawn_x, height,
           body_starting_energy, body_base_metabolic_cost,
           body_effective_sensor_radius_override,                    # carried from v0.53k (None on v0.53l everywhere — body_config has no override field set)
           founder_effective_sensor_radius_override,                 # NEW in v0.53l (8 on max-sensor founder of C; None elsewhere)
           is_max_sensor_lineage_in_run,                             # NEW in v0.53l (descriptive — True iff lineage_id == _select_sensor_radius_label per run)
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

runs/v0.53l-perception-max-lineage-sensor-radius-8/audit_summary.csv
runs/v0.53l-perception-max-lineage-sensor-radius-8/audit_log.txt
```

The CSV gets two new columns relative to v0.53k: `founder_effective_sensor_radius_override` (8 on the C max-sensor founder in each C run; None elsewhere; auditable per row) AND `is_max_sensor_lineage_in_run` (True iff `lineage_id == _select_sensor_radius_label(sensor_radius_by_lineage)` per run; descriptive cross-check that `founder_effective_sensor_radius_override == 8` iff `is_max_sensor_lineage_in_run` AND `arm == "C_widened_food_near1_combined_max_lineage_sr8_N400"`).

## Implementation plan (locked)

1. **Two additive `src/` carve-outs** (must be implemented together; the seam is unsafe without the invariant):

   **(1a) `fear_hunger_chamber.py: run_chamber()` gains `per_founder_traits_overrides: Sequence[Traits | None] | None = None`:**
   - If provided, raise `ValueError` when `traits_override` is also provided (mutual exclusion).
   - If provided, raise `ValueError` when `len(per_founder_traits_overrides) != n_founders` (length check).
   - Founder loop assigns `per_founder_traits_overrides[i]` (if not None) to `FounderSpec(traits_override=...)`; otherwise passes `None`.
   - Default `None` keeps v0.1..v0.53k callers byte-identical.

   **(1b) `model.py:_spawn_founder` (or the founder-construction loop) adopts the always-consume invariant.** Replace the current short-circuit pattern (`spec.traits_override if spec.traits_override is not None else random_traits(self.trait_config, self.streams.mutation)`) with the always-consume pattern:
   ```python
   sampled_traits = random_traits(self.trait_config, self.streams.mutation)
   traits = (
       spec.traits_override
       if spec.traits_override is not None
       else sampled_traits
   )
   ```
   Every founder construction now consumes exactly one `random_traits(...)` draw from the mutation stream regardless of whether that founder uses sampled traits, a global `traits_override`, or a per-founder override. **This is the locked invariant**: it is a behavioral change for override paths, not a refactor — the mutation stream now advances exactly once per founder.

   **Determinism north star** (`scripts/core_smoke_test.py`) must continue to pass after both carve-outs land. No-override paths remain byte-identical to v0.53k. Tier-1 / Tier-2 / Tier-3 anchors must reproduce within their existing tolerances on the v0.53l reducer.
2. Fresh script `scripts/v0_53l_perception_max_lineage_sensor_radius_8_audit.py`. CLI: `uv run python scripts/v0_53l_perception_max_lineage_sensor_radius_8_audit.py [--out-dir runs/v0.53l-perception-max-lineage-sensor-radius-8]`.
3. Define module-level constants (identical to v0.53j/k):
   ```python
   FOOD_NEAR1_LAYOUT = ChamberLayout(safe_x_min=0, safe_x_max=4, hazard_x_min=5, hazard_x_max=7, food_x_min=9, food_x_max=13, height=6, spawn_x=1)
   FOOD_NEAR2_LAYOUT = ChamberLayout(safe_x_min=0, safe_x_max=4, hazard_x_min=5, hazard_x_max=7, food_x_min=8, food_x_max=12, height=6, spawn_x=1)
   ```
4. Reuse `_select_sensor_radius_label` from v0.53k's reducer via `importlib.util` (CLAUDE.md cross-script-import pattern).
5. C-arm setup builds the per-founder overrides:
   - Build the 5 founders' candidate Traits via the v0.53k-equivalent path (sample under V0_25 distribution).
   - Compute `max_lid = _select_sensor_radius_label({lid: traits.sensor_radius for lid, traits in candidates.items()})`.
   - Construct `per_founder_traits_overrides = [traits if lid == max_lid else None for lid, traits in candidates.items()]` where the `traits` for `max_lid` is `dataclasses.replace(candidates[max_lid], effective_sensor_radius_override=8)`.
   - Wait — the chamber driver normally samples founders inside `run_chamber`. To inject per-founder overrides, the reducer must pre-sample the founder Traits, identify the max, and pass the per-founder override list. This is the same pattern v0.2 / v0.36 use for archetype injection. The reducer is responsible for stream determinism: use a deterministic per-run founder-trait sampler keyed on (version, seed, hazard) that produces the same Traits as the chamber driver would for that run, identify max_lid, then call `run_chamber(per_founder_traits_overrides=...)` with the override applied to that lineage.
   - **Determinism critical:** the founder-trait pre-sampling MUST produce the same Traits the chamber would have sampled internally. This is verified by Tier-1 anchor (A arm reproduces v0.48 a_share_h8 within 1e-3) and a new test #11b: B / C / D founder Traits are byte-identical to v0.53k's founder Traits at the same (version, seed, hazard) — the only divergence is C's `effective_sensor_radius_override` field.
6. Setup_observer captures founder audit table including `body.energy`, `body_config.starting_energy`, `body_config.base_metabolic_cost`, `body_config.effective_sensor_radius_override` (None for v0.53l everywhere), **`body.traits.effective_sensor_radius_override`** (8 on C max-sensor founder; None elsewhere — NEW captured field), layout column geometry, `n_ticks` per arm at tick 0.
7. Per-tick observer: pre50/100/200 on all arms; pre400 on C and D.
8. Aggregate per-lineage primaries; compute Label A and four Label B variants (Label A definition uses the same `_select_sensor_radius_label` selector applied to founder Traits).
9. Compute paired_d, reachability_run_share, population-stability metrics.
10. **Tier-1, Tier-2, Tier-3 anchors** as per v0.53j/k (priority 2.a–2.f).
11. **Corpus re-anchor** (priority 1): A `a_share_h8` for v0.42/v0.44/v0.45 within 1e-3.
12. **Reachability-gated MAX_LINEAGE_PERCEPTION_OPPOSITE_SIGN_HALT** (priority 3): C tick-400 wrong-sign cells AND C reachability ≥ 0.25 → halt; otherwise descriptive log.
13. Compute slice rollup verdict; print + write the locked phrase verbatim.

The reducer is self-contained beyond the cross-script import of `_select_sensor_radius_label`. Wall time estimate ~25–50 minutes.

## Test list (locked, 16 tests; mirrors v0.53k with per-founder seam additions)

`tests/test_v0_53l_perception_max_lineage_sensor_radius_8_audit.py`:

1. **`test_paired_d_function_reproduces_hand_computed_signed_d_on_fixture_and_tier1_v048_constants_and_tier3_v053i_constants`** *(three-part: hand-fixture + Tier-1 + Tier-3)*.
2. **`test_a_null_v025_corpus_a_share_h8_re_anchors_v042_v044_v045`**.
3. `test_arm_a_null_v025_uses_tight_gradient_layout_default_body_config_and_n_ticks_200_with_explicit_geometry_asserts`.
4. `test_arm_b_widened_v025_uses_widened_gradient_layout_default_body_config_and_n_ticks_200_with_explicit_geometry_asserts`.
5. **`test_arm_c_widened_food_near1_combined_max_lineage_sr8_N400_uses_food_near1_layout_per_founder_override_on_max_sensor_lineage_only_and_n_ticks_400_with_explicit_geometry_and_per_lineage_perception_asserts`**:
   - C body_config asserts: `body.energy == 100.0`, `body_config.starting_energy == 100.0`, `body_config.base_metabolic_cost == 0.10`, `body_config.effective_sensor_radius_override is None` (v0.53l drops the model-wide override that v0.53k carried).
   - C all OTHER BodyConfig fields at default (max_energy=100.0, starting_health=100.0, max_health=100.0, sensor_radius_metabolic_cost=0.05).
   - C layout asserts (FOOD_NEAR1: world_width=14, food_x_min=9, food_x_max=13, hazard_x_min=5, hazard_x_max=7, safe_x_min=0, safe_x_max=4, spawn_x=1, height=6).
   - **NEW per-founder override asserts**: exactly 1 founder per C run has `traits.effective_sensor_radius_override == 8`; that founder is the one selected by `_select_sensor_radius_label(sensor_radius_by_lineage)`; the OTHER 4 founders have `traits.effective_sensor_radius_override is None`.
   - C `_RunCapture.final_tick_count <= 400` (carries forward v0.53k convention).
6. **`test_arm_d_widened_food_near2_combined_N400_uses_food_near2_layout_combined_body_config_no_override_and_n_ticks_400_with_explicit_geometry_and_no_perception_override_asserts`**:
   - D body_config asserts: `body.energy == 100.0`, `body_config.starting_energy == 100.0`, `body_config.base_metabolic_cost == 0.10`, `body_config.effective_sensor_radius_override is None`.
   - **NEW negative per-founder asserts**: ALL 5 D founders have `traits.effective_sensor_radius_override is None`.
   - D layout asserts (FOOD_NEAR2: world_width=13, food_x_min=8, food_x_max=12).
   - D `_RunCapture.final_tick_count <= 400`.
7. **`test_cross_arm_per_lineage_perception_contrast_c_max_sensor_founder_has_override_8_d_has_no_override_layouts_differ_by_food_x_min`** *(extends v0.53k test #7 with per-founder semantics)*:
   - C: exactly 1 of 5 founders has `traits.effective_sensor_radius_override == 8`; that founder is the max-sensor lineage; AND `body_config.effective_sensor_radius_override is None`.
   - D: 0 of 5 founders have `traits.effective_sensor_radius_override == 8`; ALL D founders have it None.
   - `C.body_starting_energy == D.body_starting_energy == 100.0`; `C.body_base_metabolic_cost == D.body_base_metabolic_cost == 0.10`; `C.n_ticks == D.n_ticks == 400`.
   - `C.food_x_min == 9, D.food_x_min == 8` (layout differentiator carries forward).
   - All other layout fields (hazard / safe / spawn / height) identical between C and D.
8. **`test_no_src_modifications_compared_to_v0_53l_tip`** *(three-part SHA pinning; uses shared `tests/sha_pins.py` for Parts B and C)*:
   - **Part A (science-core, historical):** five science-core SHAs match v0.52b-tip historical pins (`d4521cb5...` for layouts.py; unchanged from v0.53e–v0.53k).
   - **Part B (chamber driver, current):** `fear_hunger_chamber.py` SHA matches `sha_pins.CHAMBER_DRIVER_SHA` (v0.53l-tip; recorded at implementation time).
   - **Part C (model, current — NEW):** `model.py` SHA matches `sha_pins.MODEL_SHA` (v0.53l-tip; recorded at implementation time).
   - Companion migration: prior test #8s in v0.53e–v0.53k are migrated to import from `tests/sha_pins.py` rather than hardcoding chamber-driver SHA. Bookkeeping only — no verdict / anchor / historical claim of any prior slice is changed.
9. **`test_per_founder_traits_overrides_seam_and_stream_invariance`** *(NEW in v0.53l; consolidates the six required pre-data seam validations into a single comprehensive test)*:
   - **(9.a) Mutual exclusivity:** `run_chamber(traits_override=X, per_founder_traits_overrides=Y)` with both non-None raises `ValueError`.
   - **(9.b) Length validation:** `run_chamber(per_founder_traits_overrides=[None]*4)` with `n_founders=5` raises `ValueError`.
   - **(9.c) Default-preserving:** `run_chamber(per_founder_traits_overrides=None)` produces a `_RunCapture` byte-identical to calling without the parameter; A_null / B_widened / D anchor configs reproduce v0.53k anchor behavior under matched (version, seed, hazard).
   - **(9.d) Founder targeting:** when `per_founder_traits_overrides[max_lid] = Traits(..., effective_sensor_radius_override=8)` is provided on the C arm, exactly that one founder has `body.traits.effective_sensor_radius_override == 8` post-construction, and the four other founders have it `None`. The targeted lineage matches `_select_sensor_radius_label(sensor_radius_by_lineage)` per run.
   - **(9.e) Non-target founder identity:** non-overridden founders retain the **exact** sampled `Traits` they would have had in the no-override run under the same (version, seed, hazard). This proves the always-consume invariant: stream state at simulation start is identical between override and no-override runs, modulo the one targeted founder's `effective_sensor_radius_override` field.
   - **(9.f) Stream-invariance proxy:** Tier-1 / Tier-2 / Tier-3 anchors reproduce within their locked tolerances on the v0.53l reducer (corpus re-anchor `a_share_h8` within 1e-3; B `0/64` exact; D `35/64` exact + `BRIDGE_PRESENT` + six paired_d cells with `drift_abs <= 1e-3` to v0.53i published values). If the always-consume invariant were absent, the override path's RNG drift would manifest as anchor drift on B/D; this test is the integration-level guarantor.
10. `test_label_a_high_sensor_radius_lineage_picks_correct_lineage_and_matches_per_founder_override_target`:
    - The lineage Label A picks per run == the lineage targeted by the C-arm per-founder override.
11. **`test_label_b_four_variants_three_tier_tiebreak_at_each_window_with_pre400_c_and_d_only`**.
12. **`test_pre400_window_strictly_extends_pre200_pre100_pre50_windows_on_c_and_d_arms`**.
13. **`test_subverdict_present_requires_two_thirds_firing_cells_with_nan_treated_as_non_firing_strict`**.
14. **`test_priority_3_max_lineage_perception_opposite_sign_halt_is_reachability_gated_on_c_tick_400`** *(carries forward from v0.53k test #13; halt name renamed `MAX_LINEAGE_PERCEPTION_OPPOSITE_SIGN_HALT`)*:
    - Branch A: C tick-400 sub-verdict = OPPOSITE_SIGN_HALT, c_reachability_tick_400 = 0.30 → priority 3 fires.
    - Branch B: same sub-verdict but reachability = 0.20 → priority 5.
    - Branch C: PRESENT + reachability = 0.30 → priority 4.
15. **`test_b_widened_v025_categorical_anchor_at_tick_200_and_d_food_near2_positive_anchor_at_tick_400`** *(five independent synthetic-fixture branches; identical to v0.53j/k test #14)*: baseline GREEN, Tier-2 halt, Tier-3 reachability halt, Tier-3 sub-verdict halt, Tier-3 paired_d halt.
16. **`test_rollup_locked_phrases_fire_verbatim_and_priority_cascade_partition_total`** — substring assertions VERBATIM from priority 4/5/6 locked phrases:
    - Priority 4: `"the per-lineage perception intervention \`per_founder_traits_overrides[max_lid] = Traits(effective_sensor_radius_override=8)\`"` AND `"the v0.48 \`is_high_sensor_radius_lineage\` selector — argmax with min-lineage-id tiebreak — picking the same lineage Label A indexes"` AND `"metabolic cost UNAFFECTED per the override's information-channel-only contract"` AND `"override propagates to all descendants via \`dataclasses.replace\`'s preservation"` AND `"The v0.53k Label A collapse is consistent with model-wide perception homogenization being the proximate cause of bridge-fingerprint loss, not sensor-reach itself"` AND `"This is strong evidence but NOT exclusive causality"` AND substring references to v0.53c, v0.53d, v0.53e, v0.53f, v0.53g, v0.53h, v0.53i, v0.53j, v0.53k verdict names (NINE-long predecessor stack).
    - Priority 5: `"the per-lineage perception intervention \`per_founder_traits_overrides[max_lid] = Traits(effective_sensor_radius_override=8)\`"` AND `"D_widened_food_near2_combined_N400 reproduces v0.53i's \`35/64\` positive anchor at tick-400 in-slice"` AND `"The single-max-lineage perception intervention is **insufficient**"` AND `"v0.53m (or later) candidates shift toward broader lineage coverage (top-K, threshold-based) or policy / hazard-avoidance / movement probes"` AND substring references to v0.53c–v0.53k verdict names.
    - Priority 6: `"D_widened_food_near2_combined_N400 reproduces v0.53i's \`35/64\` positive anchor at tick-400 in-slice"`.
    Synthesize halt cascade (priorities 1 / 2.a / 2.b / 2.c / 2.d / 2.e / 2.f / 3); assert priority order. Exhaustively iterate the partition; assert unique outcome per cell.

## Watch-outs (for future-Chronus)

- **Two additive `src/` carve-outs** are mandatory and locked together: (1) `run_chamber()` parameter `per_founder_traits_overrides`, and (2) `model.py:_spawn_founder` always-consume invariant. **The seam is unsafe without the invariant** — without always-consume, providing a per-founder override changes both the targeted lineage's traits AND the downstream mutation RNG state, conflating two interventions.
- **Stream-invariance is the locked invariant.** Every founder construction consumes exactly one `random_traits(...)` draw from the mutation stream, regardless of whether that founder ultimately uses sampled traits, a global `traits_override`, or a per-founder override. Implementation pattern: `sampled_traits = random_traits(...)` is called UNCONDITIONALLY; `traits = override if override is not None else sampled_traits`. The discarded sample under override is intentional — it preserves stream state.
- **Mutual exclusion + length check on `per_founder_traits_overrides` are mandatory and must raise `ValueError`.** Default `None` preserves byte-identity for all v0.1..v0.53k callers.
- **Test #8 SHA-pinning policy** uses a shared `tests/sha_pins.py` module for chamber-driver and model SHAs. Prior test #8s in v0.53e–v0.53k are migrated to import from there — bookkeeping only, no logic change. Future intentional carve-outs update one constant in `sha_pins.py`, not N prior test files.
- **`Traits.effective_sensor_radius_override` is automatically inherited** through reproduction (per `traits.py:60-66` and `mutate_traits`'s `dataclasses.replace(parent, **values)`). The targeted founder's lineage retains the override across all descendants — the intervention is genuinely lineage-level. No opt-in needed.
- **Determinism north star** ([[scripts/core_smoke_test.py]]) must continue to pass after the seam-add. Default-None behavior preserves byte-identity for all prior callers.
- **Founder-trait pre-sampling determinism is critical.** The reducer pre-samples founder Traits before calling `run_chamber()` so it can identify `max_lid` and construct the per-founder override list. This pre-sampling MUST produce the same Traits the chamber would have sampled internally for the same (version, seed, hazard). Verified by Tier-1 anchor and test-level founder-trait byte-identity cross-checks against v0.53k.
- **Label A now points at the override-targeted lineage by construction.** This is the design — the intervention aligns intervention-target with label-target. Note that this means a positive Label A firing in v0.53l does NOT prove "the v0.48 bridge is exclusively trait-mediated"; secondary channels (early-survival differential, reproduction-rate, pleiotropy) cannot be ruled out.
- **Tier-3 positive anchor on D is preserved from v0.53j/k.** v0.53j and v0.53k both observed drift_abs = 0.0 across all six cells; v0.53l expects the same. The new `per_founder_traits_overrides=None` default on D is a no-op against the v0.53k D code path.
- **No `the v0.48 bridge is exclusively trait-mediated` claims under priority 4.** Bounded-causality language preserved.
- **No `lineage-specific perception is irrelevant` claims under priority 5.** Bounded to single-max=8 specifically.
- **Locked phrase discipline verbatim.** Predecessor stack now NINE long: v0.53c/d/e/f/g/h/i/j/k.
- **Bulk metadata rename trap** (caught the v0.53i→v0.53j build last session): when copying v0.53k templates as starting seed, predecessor refs to `v0.53k` in priority-4/5/6 locked phrases AND test #16 substring assertions must be PRESERVED VERBATIM, NOT bulk-replaced to v0.53l. Only the slice's own self-reference (version label, output dir, file name, current verdict name) becomes v0.53l.
- **Sensor radius interacts with food-attraction signal beyond simple visibility.** Per `core/sensors.py:11`, `signal += value / distance`. Same caveat as v0.53k.

## Files this slice will create / modify

**New files:**
- `docs/experiments/fear_hunger_v0.53l.md` (this file; Results appended after reducer run)
- `scripts/v0_53l_perception_max_lineage_sensor_radius_8_audit.py`
- `tests/test_v0_53l_perception_max_lineage_sensor_radius_8_audit.py` (16 tests)
- `tests/sha_pins.py` (shared chamber-driver + model SHA pins; new shared module)

**Modified `src/`:**
- `src/hedonism_harness/experiments/fear_hunger_chamber.py` — add `per_founder_traits_overrides` parameter (carve-out 1). Chamber-driver SHA changes from v0.53e-tip `62d134c5...` to v0.53l-tip.
- `src/hedonism_harness/model.py` — adopt always-consume invariant in `_spawn_founder` / founder-construction loop (carve-out 2). Model SHA changes to v0.53l-tip.

**Modified prior test files (bookkeeping only — chamber-driver SHA constant migrated to `sha_pins.CHAMBER_DRIVER_SHA` import; no verdict / anchor / historical claim changed):**
- `tests/test_v0_53e_substrate_axis_starting_energy_audit.py`
- `tests/test_v0_53f_substrate_axis_base_metabolic_cost_audit.py`
- `tests/test_v0_53g_substrate_axis_combined_se100_bmc010_audit.py`
- `tests/test_v0_53h_time_horizon_extension_n400_audit.py`
- `tests/test_v0_53i_geometry_food_near2_audit.py`
- `tests/test_v0_53j_food_distance_dose_response_audit.py`
- `tests/test_v0_53k_perception_sensor_radius_8_audit.py`

`layouts.py` UNCHANGED. `core/sensors.py` / `core/traits.py` / `core/body.py` / `core/config.py` UNCHANGED. No prior reducer / audit / pre-reg files modified.

## Results

**Run completed 2026-05-10 on the locked 256-run corpus** (4 arms × 64 runs; v0.42/43R/44/45 × seeds 41..72 × hazards {0,8}; A/B at `n_ticks=200`, C/D at `n_ticks=400`). All halt-class checks pass (no priority 1/2/3 halt). **Rollup verdict: `WIDENED_BRIDGE_RESCUED_BY_MAX_LINEAGE_SENSOR_RADIUS_8` (priority 4 — full rescue under both gating labels).**

### Locked phrase (verbatim)

> On the modern A_null corpus with the V0_25 substrate held constant except for the combined founder-facing budget relaxation `BodyConfig(starting_energy=100.0, base_metabolic_cost=0.10)` AND the simulation horizon doubled to `n_ticks=400` AND the `widened_food_near1` layout (`food_x∈[9,13]`, 1-column corridor at `x=8`; identical to v0.53j C / v0.53k C) AND the per-lineage perception intervention `per_founder_traits_overrides[max_lid] = Traits(effective_sensor_radius_override=8)` (the override applies ONLY to the single max-`sensor_radius` founder per run, with the v0.48 `is_high_sensor_radius_lineage` selector — argmax with min-lineage-id tiebreak — picking the same lineage Label A indexes; metabolic cost UNAFFECTED per the override's information-channel-only contract; override propagates to all descendants via `dataclasses.replace`'s preservation), the v0.48 sensor_radius spatial / foraging bridge fires PRESENT under the locked +0.5 paired_d threshold at tick-400 under both gating labels. The geometry/substrate cell that v0.53c locked as `WIDENED_BELOW_REACHABILITY_THRESHOLD_AT_TICK_200`, v0.53d locked as `WIDENED_BELOW_REACHABILITY_THRESHOLD_UNDER_RELAXED_INFLUX`, v0.53e locked as `RELAXED_OPPOSITE_SIGN_HALT`, v0.53f locked as `WIDENED_BELOW_REACHABILITY_THRESHOLD_UNDER_BASE_METABOLIC_COST_010`, v0.53g locked as `WIDENED_BELOW_REACHABILITY_THRESHOLD_UNDER_COMBINED_SE100_BMC010`, v0.53h locked as `WIDENED_BELOW_REACHABILITY_THRESHOLD_AT_TIME_HORIZON_400`, v0.53i locked as `WIDENED_BRIDGE_RESCUED_BY_FOOD_NEAR2`, v0.53j locked as `WIDENED_BELOW_REACHABILITY_THRESHOLD_UNDER_FOOD_NEAR1`, and v0.53k locked as `WIDENED_BRIDGE_PARTIALLY_RESCUED_BY_SENSOR_RADIUS_8` admits a measurable bridge under the per-lineage perception intervention: B_widened_V0_25 reachability remains `0/64` at tick-200 (predecessor lock holds), D_widened_food_near2_combined_N400 reachability reproduces v0.53i's `35/64` positive anchor at tick-400 (positive lock holds), C reachability at tick-400 clears the locked 25% threshold, and ≥ 2/3 spatial / foraging primaries fire PRESENT under both gating labels at the C tick-400 panel. **The v0.53k Label A collapse is consistent with model-wide perception homogenization being the proximate cause of bridge-fingerprint loss, not sensor-reach itself**: lineage-specific perception heterogeneity restores Label A under sufficient targeted access. This is strong evidence but NOT exclusive causality — the targeted lineage may also drive Label A firing through secondary channels (asymmetric early survival, reproduction-rate differential, pleiotropy with other heritable traits). This does NOT prove `the v0.48 bridge is exclusively trait-mediated`; NOT `model-wide perception interventions are inferior in all settings`: `WIDENED_BRIDGE_RESCUED_BY_MAX_LINEAGE_SENSOR_RADIUS_8`.

### Reachability run-share (locked)

| arm | tick-50 | tick-100 | tick-200 | tick-400 |
|---|:-:|:-:|:-:|:-:|
| A_null_V0_25 | 1.000 (64/64) | 1.000 | 1.000 | — |
| B_widened_V0_25 | 0.000 (0/64) | 0.000 | **0.000** *(Tier-2 anchor)* | — |
| **C_widened_food_near1_combined_max_lineage_sr8_N400** | progressively rising | rising | rising | **0.953 (61/64)** *(verdict-gating ≥ 0.25 ✓)* |
| D_widened_food_near2_combined_N400 | 0.531 (34/64) | 0.547 | 0.547 | **0.547 (35/64)** *(Tier-3 anchor)* |

C tick-400 reachability `61/64 = 0.953` clears the locked 25% threshold by a wide margin. v0.53j C (FOOD_NEAR1, no perception override) was `0/64`; v0.53k C (FOOD_NEAR1, **model-wide** override) was `64/64`; v0.53l C (FOOD_NEAR1, **per-lineage** override on max-sensor lineage only) is `61/64`. Targeting only the max-sensor lineage with `r=8` lifts reachability nearly to v0.53k's universal-access ceiling, because the override-targeted lineage and its descendants successfully reach food in 95% of runs.

### C tick-400 sub-verdict (verdict-gating panel)

`C_WIDENED_FOOD_NEAR1_MAX_LINEAGE_SR8_TICK400_BRIDGE_PRESENT` — both labels clear ≥ 2/3 cells under the strict NaN-treated-as-non-firing rule, with all six cells firing under expected sign and zero wrong-sign cells.

| label | observable | signed_d | fires_expected | fires_wrong | n_runs |
|---|---|:-:|:-:|:-:|:-:|
| label_a_sensor_radius | pre400_food_events_count | **+4.408** | **True** | False | 64 |
| label_a_sensor_radius | pre400_food_energy_acquired | **+4.408** | **True** | False | 64 |
| label_a_sensor_radius | mean_distance_to_nearest_food_cell_tick400 | **+3.818** | **True** | False | 64 |
| label_b_readiness_fraction_tick400 | pre400_food_events_count | **+44.794** | **True** | False | 38 |
| label_b_readiness_fraction_tick400 | pre400_food_energy_acquired | **+44.794** | **True** | False | 38 |
| label_b_readiness_fraction_tick400 | mean_distance_to_nearest_food_cell_tick400 | **+7.203** | **True** | False | 38 |

**Both labels: 3/3 firing under expected sign; 0/3 wrong-sign.** The v0.48 sensor_radius spatial / foraging bridge is fully expressed at C tick-400 under per-lineage perception heterogeneity. Compared to v0.53k (model-wide override):

| panel | v0.53k Label A | v0.53l Label A | v0.53k Label B | v0.53l Label B |
|---|:-:|:-:|:-:|:-:|
| pre400_food_events_count | −0.019 | **+4.408** | +0.698 | **+44.794** |
| pre400_food_energy_acquired | −0.019 | **+4.408** | +0.698 | **+44.794** |
| mean_distance_to_nearest_food_cell_tick400 | −0.002 | **+3.818** | +0.588 | **+7.203** |

Label A's three cells move from the v0.53k deadband (`|signed_d| < 0.05`) to firmly above the +0.5 threshold under v0.53l. Label A's reactivation under per-lineage override is consistent with the locked priority-4 reading: **v0.53k's collapse is consistent with model-wide perception homogenization being the proximate cause of bridge-fingerprint loss, not sensor-reach itself.**

**Label B magnitude interpretation (framing nuance).** The Label B magnitudes (+44.8 on food-events / energy cells; +7.2 on the distance cell) are extreme because the high-readiness lineage is overwhelmingly the same lineage family receiving the only effective FOOD_NEAR1 perception access. **This is not interpreted as a generic strengthening of the original bridge; it is interpreted as a concentrated outcome channel created by the targeted perception intervention.** Non-label lineages' food acquisition is near zero, producing very large `delta_mean` over small `delta_stdev` — a structural separation, not an effect-size finding about Label B's underlying trait correlation.

### Tier-3 D anchor (locked, identical to v0.53j/k)

D tick-400 reachability `= 35/64 = 0.546875` exact ✓. D tick-400 sub-verdict `= D_WIDENED_FOOD_NEAR2_TICK400_BRIDGE_PRESENT` ✓. Six paired_d cells reproduce v0.53i's published values with **drift_abs = 0.0 on every cell**. This is the empirical guarantor that **no-override paths remain byte-stable after the always-consume invariant and per-founder seam**: D uses `per_founder_traits_overrides=None`, so its chamber-path should be byte-identical to v0.53k D / v0.53j D / v0.53i C under the new `model.py` invariant — the zero drift confirms it. (The dedicated stream-invariance tests in test #9.e/9.f cover the override-path side of the invariant separately.)

| label | observable | derived signed_d | published v0.53i | drift_abs |
|---|---|:-:|:-:|:-:|
| label_a_sensor_radius | pre400_food_events_count | +1.0357354787853512 | +1.0357354787853512 | 0.000 |
| label_a_sensor_radius | pre400_food_energy_acquired | +1.0357354787853512 | +1.0357354787853512 | 0.000 |
| label_a_sensor_radius | mean_distance_to_nearest_food_cell_tick400 | +1.061633559034245 | +1.061633559034245 | 0.000 |
| label_b_readiness_fraction_tick400 | pre400_food_events_count | +5.3040008005819095 | +5.3040008005819095 | 0.000 |
| label_b_readiness_fraction_tick400 | pre400_food_energy_acquired | +5.3040008005819095 | +5.3040008005819095 | 0.000 |
| label_b_readiness_fraction_tick400 | mean_distance_to_nearest_food_cell_tick400 | +6.294727858398778 | +6.294727858398778 | 0.000 |

**Tier-1 A re-anchor.** A `a_share_h8` for v0.42 / v0.44 / v0.45 within 1e-3 of published values (matched to v0.53k's drift values: 0.6523 vs 0.652 → drift 0.00031; 0.8781 vs 0.878 → drift 9.1e-05; 0.8182 vs 0.818 → drift 0.00018). All within tolerance ✓. **Tier-2 B anchor.** B reachability at tick-200 = `0.000` exact ✓.

### Population survival (descriptive)

| arm | tick-50 | tick-100 | tick-200 | tick-400 |
|---|:-:|:-:|:-:|:-:|
| C_widened_food_near1_combined_max_lineage_sr8_N400 | 1.000 | 1.000 | 0.969 | **0.594** (38/64) |
| D_widened_food_near2_combined_N400 | 1.000 | 1.000 | 0.938 | **0.359** (23/64) |

C tick-400 survival is 0.594 vs D's 0.359 — under the targeted single-lineage override, C still survives better than D (which uses default sensor at FOOD_NEAR2). However, C's tick-400 survival is lower than v0.53k C's 0.875 under model-wide override — when only the max-sensor lineage and its descendants can reach food, the four other founder lineages cannot acquire food and most of them die before tick-400. This is descriptive — not verdict-gating — but worth flagging: the targeted intervention produces strong bridge expression at the cost of lower population survival than the universal-access intervention.

### C tick-50/100/200 sub-verdicts (descriptive)

| window | sub-verdict |
|---|---|
| tick-50 | `C_WIDENED_FOOD_NEAR1_MAX_LINEAGE_SR8_TICK50_BRIDGE_PARTIAL` |
| tick-100 | `C_WIDENED_FOOD_NEAR1_MAX_LINEAGE_SR8_TICK100_BRIDGE_PRESENT` |
| tick-200 | `C_WIDENED_FOOD_NEAR1_MAX_LINEAGE_SR8_TICK200_BRIDGE_PRESENT` |
| tick-400 | `C_WIDENED_FOOD_NEAR1_MAX_LINEAGE_SR8_TICK400_BRIDGE_PRESENT` *(verdict-gating)* |

The PARTIAL → PRESENT trajectory mirrors D's progressively-strengthening bridge expression under default sensor at FOOD_NEAR2 (v0.53i). Under per-lineage override at FOOD_NEAR1, the bridge clears PRESENT by tick-100 and stays PRESENT through tick-400.

### What v0.53l establishes (bounded)

- **The v0.48 trait-indexed sensor_radius bridge can be restored under FOOD_NEAR1 by lineage-specific perceptual access.** v0.53j C (no override) had categorical null reachability + no bridge expression; v0.53k C (model-wide override) had universal access but Label A collapse; v0.53l C (per-lineage override on the same lineage Label A indexes) has 95% reachability AND full bridge expression under both labels.
- **v0.53k's Label A collapse is consistent with model-wide perception homogenization being the proximate cause of bridge-fingerprint loss, not sensor-reach itself.** The result follows from the locked design: v0.53l's per-lineage intervention preserves between-lineage perception heterogeneity (only one of five founders crosses the override threshold) while still granting sufficient perceptual reach to the labeled lineage. Label A's reactivation under this exact design supports the priority-4 reading.
- **The intervention-to-Label-A alignment is empirically supported.** `_select_sensor_radius_label` picks lineage X; the override is applied to lineage X; if the targeted lineage is unique under the access channel, Label A fires. v0.53l confirms this expected behavior under the tested envelope.

### What v0.53l does NOT establish

- ✗ **"The v0.48 bridge is exclusively trait-mediated."** Strong evidence ≠ exclusive causality. The targeted lineage may also drive Label A firing through secondary channels: asymmetric early survival (the override-targeted lineage's descendants survive while non-overridden lineages die from starvation), reproduction-rate differential (more food → more reproduction → more lineage representation), or pleiotropy (other heritable traits correlated with `sensor_radius` may co-drive food acquisition). v0.53m candidates (random-lineage control, top-K override, threshold-based override) test these alternatives.
- ✗ **"r=8 is the minimum sufficient override for per-lineage rescue."** v0.53l does NOT test r=7 or smaller under the per-lineage scheme.
- ✗ **"Model-wide perception interventions are inferior in all settings."** v0.53k's PARTIAL outcome captures real population-survival benefits (0.875 vs v0.53l's 0.594); the universal-access design has descriptive merit.
- ✗ **A revised v0.53–v0.53k verdict.** All eleven predecessor verdicts stand as historical contracts.

### Continuity statement

Predecessor stack now NINE long: v0.53c → v0.53d → v0.53e → v0.53f → v0.53g → v0.53h → v0.53i → v0.53j → v0.53k → **v0.53l (`WIDENED_BRIDGE_RESCUED_BY_MAX_LINEAGE_SENSOR_RADIUS_8`).**

The substrate-axis stack is now multi-dimensional with multi-granular interventions: body_config (energy / metabolic_cost), n_ticks (horizon), geometry (food_x_min), perception model-wide (`body_config.effective_sensor_radius_override`), perception per-lineage (`per_founder_traits_overrides[max_lid]` + always-consume invariant). v0.53l is the SECOND priority-4 outcome in the v0.53c–v0.53l chain (v0.53i `RESCUED_BY_FOOD_NEAR2`; v0.53l `RESCUED_BY_MAX_LINEAGE_SENSOR_RADIUS_8`); v0.53k stands as the unique priority-6 PARTIAL.

### Open framing for v0.53m+

Per priority-4 outcome's locked branches:
- **v0.53m candidate — sensor_radius dose curve under per-lineage scheme.** Test r=6, r=7, r=10 to localize the minimum sufficient single-lineage override.
- **v0.53n candidate — random-lineage override (control).** Assign `r=8` to a NON-max lineage (e.g., min-sensor lineage) under matched corpus. If Label A fires anyway, the v0.48 bridge is more access-mediated than trait-mediated. If Label A does NOT fire, the trait-correlation requires the override AND the trait to coincide.
- **v0.53o candidate — top-K extension.** Now that single-max rescues, test whether top-2 / top-3 override preserves Label A firing (heterogeneity dilution test).
- **v0.53p candidate — Reading-A causal-generalization on FOOD_NEAR1 + per-lineage sr=8.** With Label A's bridge restored, the v0.49–v0.52b causal-generalization framework can re-anchor on this newly-accessible cell.
- **v0.54 — joint ablation.** Eventually fresh-stream calibration on the full v0.46–v0.53l stack.
