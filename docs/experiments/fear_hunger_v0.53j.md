# fear_hunger v0.53j — FOOD_NEAR1 below threshold; FOOD_NEAR2 positive anchor reproduces (food-distance dose-response on `widened_gradient`-shape × V0_25 × combined founder-budget envelope at `n_ticks=400`)

**Slice:** v0.53j
**Type:** **first-class observational sweep** with 4-arm asymmetric-horizon reducer (no `src/` changes — both novel C and D layouts constructed script-local; v0.53e's `body_config` seam carries forward; `n_ticks` already exposed; no intervention; **single geometry knob with two doses** on the C and D arms — v0.53j is a dose-response slice probing the rescue boundary established by v0.53i; D arm is the in-slice positive anchor).
**Predecessors:** v0.46–v0.52b (full predecessor stack), v0.53 (`BRIDGE_PARTIALLY_GENERALIZES`), v0.53b (`WIDENED_BELOW_REACHABILITY_THRESHOLD_AT_TICK_100`), v0.53c (`WIDENED_BELOW_REACHABILITY_THRESHOLD_AT_TICK_200`), v0.53d (`WIDENED_BELOW_REACHABILITY_THRESHOLD_UNDER_RELAXED_INFLUX`), v0.53e (`RELAXED_OPPOSITE_SIGN_HALT`), v0.53f (`WIDENED_BELOW_REACHABILITY_THRESHOLD_UNDER_BASE_METABOLIC_COST_010`), v0.53g (`WIDENED_BELOW_REACHABILITY_THRESHOLD_UNDER_COMBINED_SE100_BMC010` — central finding: survival ⊥ reachability), v0.53h (`WIDENED_BELOW_REACHABILITY_THRESHOLD_AT_TIME_HORIZON_400` — central finding: survival horizon also has a ceiling), v0.53i (`WIDENED_BRIDGE_RESCUED_BY_FOOD_NEAR2` — first RESCUED outcome since v0.53d→v0.53h null stack; reducing post-hazard food distance by 2 columns lifts both reachability AND bridge expression to PRESENT under both labels).
**Question being asked (locked):** Is a 1-column reduction of post-hazard food distance sufficient to rescue reachability and bridge expression under the v0.53g/h combined-budget × `n_ticks=400` envelope, OR does the rescue boundary lie between FOOD_NEAR1 (1-column) and FOOD_NEAR2 (2-column)? Specifically: with a script-local `widened_food_near1` layout (`food_x∈[9,13]`; 1-column corridor remaining at `x=8`; hazard band, food width, spawn position, safe band, and chamber height held identical to v0.53i FOOD_NEAR2), `BodyConfig(starting_energy=100.0, base_metabolic_cost=0.10)`, and `n_ticks=400`, does C tick-400 reachability cross 0.25?

v0.53i established that a 2-column reduction of post-hazard food distance (food band moved from `widened_gradient`'s `x∈[10,14]` to `x∈[8,12]`; corridor removed) is sufficient to lift the v0.53c–v0.53h null reachability ceiling to 35/64 (~54.7%) AND fire BRIDGE_PRESENT under both gating labels at C tick-400. v0.53j tests the rescue boundary by introducing the intermediate dose: `food_x∈[9,13]`, with 1 column of corridor remaining at `x=8`. The dose names map cleanly: FOOD_NEAR1 (1-column reduction; 1-column corridor remaining; world width 14) and FOOD_NEAR2 (2-column reduction; 0-column corridor; world width 13).

The arm structure is asymmetric across both horizon and dose. A_null_V0_25 and B_widened_V0_25 are the V0_25-baseline anchors at `n_ticks=200` — Tier-1 (A tick-50 six-cell paired_d drift) and Tier-2 (B tick-200 reachability == `0/64`) carry forward from v0.53c–v0.53i. C_widened_food_near1_combined_N400 is the **primary verdict-gating arm** at `n_ticks=400` under the combined-budget envelope. D_widened_food_near2_combined_N400 is the **in-slice positive anchor** at `n_ticks=400` under the same combined-budget envelope; it is byte-identical to v0.53i's C arm under matched RNG (same layout, same body_config, same horizon, same corpus). v0.53j enforces a **full Tier-3-equivalent positive anchor on D**: D tick-400 reachability == exactly 35/64 (categorical), D tick-400 sub-verdict == `D_WIDENED_FOOD_NEAR2_TICK400_BRIDGE_PRESENT`, AND D's six tick-400 paired_d cells (`+1.036 / +1.036 / +1.062 / +5.304 / +5.304 / +6.295`) reproduce v0.53i's published values within 1e-3 drift. If D fails ANY of these checks, `ANCHOR_REPLICATION_HALT` fires — v0.53j cannot interpret the C cells without reproducing both the V0_25 baseline anchors AND the v0.53i FOOD_NEAR2 positive anchor.

If C tick-400 reachability ≥ 25% AND tick-400 sub-verdict resolves PRESENT, the rescue boundary is at or below 1-column reduction — the 2-column reduction tested by v0.53i is NOT minimal under the tested envelope. If reachability ≥ 25% AND sub-verdict ∈ {PARTIAL, NOT_FOUND}, the 1-column reduction admits measurement but the bridge fails to fully fire. If reachability ≥ 25% AND sub-verdict = OPPOSITE_SIGN_HALT, the reachability-gated priority-3 trigger fires (bridge framework is meaningful at this measurement). If reachability < 25%, **the tested rescue boundary lies between the historical widened baseline (`food_x∈[10,14]`, 2-column corridor) and FOOD_NEAR2 (`food_x∈[8,12]`, 0-column corridor), with FOOD_NEAR1 (`food_x∈[9,13]`, 1-column corridor) failing** — the 1-column reduction is INsufficient under the tested envelope. v0.53j does NOT claim "1 column is the universal minimum" or "the boundary is at exactly 1.5 columns"; the verdict scope is bounded to the tested two doses.

## Pre-implementation note (2026-05-09, before any reducer code)

The pre-reg's design was confirmed with the user before drafting:

- **4 arms (asymmetric `n_ticks`).** A_null_V0_25 (tight_gradient, V0_25 substrate, `n_ticks=200`, anchor). B_widened_V0_25 (widened_gradient, V0_25 substrate, `n_ticks=200`; predecessor lock from v0.53c–v0.53i). C_widened_food_near1_combined_N400 (script-local widened-modified layout `food_x∈[9,13]`, V0_25 substrate **except** `BodyConfig(starting_energy=100.0, base_metabolic_cost=0.10)`, `n_ticks=400`; primary verdict-gating). D_widened_food_near2_combined_N400 (script-local widened-modified layout `food_x∈[8,12]` — byte-identical to v0.53i's `WIDENED_FOOD_NEAR2_LAYOUT`; same body_config; `n_ticks=400`; in-slice positive anchor). Same 64-tuple corpus.
- **Single geometry knob with two doses.** v0.53i tested one dose (FOOD_NEAR2). v0.53j adds a second dose (FOOD_NEAR1) and re-runs the v0.53i positive dose in-slice as D. The corpus / RNG seeds / hazards / body_config / n_ticks are otherwise identical between C and D — the only difference is `food_x_min` / `food_x_max` (and the consequent `world_width`).
- **Both novel layouts constructed script-local — no `src/` change.** Module-level constants `FOOD_NEAR1_LAYOUT` (food_x∈[9,13], width=14) and `FOOD_NEAR2_LAYOUT` (food_x∈[8,12], width=13) defined inside the v0.53j reducer module. NOT added to `layouts.py`. Test #8 pinning unchanged from v0.53e/f/g/h/i — `layouts.py` SHA still `d4521cb5...`.
- **D arm is the in-slice predecessor positive anchor.** Through tick-400, D is byte-identical to v0.53i's C arm under matched RNG. v0.53j enforces a strict Tier-3-equivalent anchor on D (full reproduction within 1e-3 of all six v0.53i C tick-400 paired_d cells, plus categorical reachability == 35/64 AND sub-verdict == BRIDGE_PRESENT). v0.53j is a dose-response slice; if the known positive dose does not reproduce, the near1 result is not interpretable.
- **Reachability-gated priority 3 (carries forward from v0.53f/g/h/i, retains v0.53i's `GEOMETRY_OPPOSITE_SIGN_HALT` name).** Priority 3 fires iff C tick-400 sub-verdict = `OPPOSITE_SIGN_HALT` AND `c_reachability_tick_400 ≥ 0.25`.
- **Tick-400 verdict gating on C; tick-400 anchor on D; tick-200 descriptive on A/B.** Same 4-window observer structure as v0.53i. C and D both accumulate pre50/pre100/pre200/pre400; A and B accumulate pre50/pre100/pre200.
- **Tier-2 categorical anchor on B_widened_V0_25 preserved** (reachability tick-200 == `0/64`).
- **Tier-3 positive anchor on D_widened_food_near2_combined_N400 NEW** (reachability tick-400 == 35/64 exact AND sub-verdict == BRIDGE_PRESENT AND six paired_d cells within 1e-3 of v0.53i published values).
- **Pool / ecology preserved.** A, B, C, and D all retain V0_25 baseline `ambient_influx_rate=1.0`, `energy_pool_initial=1500.0`, `food_respawn_cooldown=50`, `child_funding_mode=PARENT_TRANSFER_POOL_GAP`, hazard_damage per (version, hazard) corpus row. Only `layout`, `body_config`, AND `n_ticks` differ. No `src/` modifications.
- **Expected behavioral identity between v0.53j D and v0.53i C through tick-400.** Same layout, same body_config, same n_ticks, same RNG. D tick-400 reachability is mechanically guaranteed to match v0.53i's 35/64. The empirical question is whether v0.53j C tick-400 reachability matches D's 35/64 (rescue at 1 column) or remains low (rescue boundary between 1 and 2 columns).

## Conservation framing — observational, no `src/` changes, single geometry knob with two doses

- **No `src/` modifications.** Both C and D layouts constructed script-local. The five science-core files AND `fear_hunger_chamber.py` AND `layouts.py` all remain byte-identical to their v0.52b-tip / v0.53e-tip values. Test #8 enforces both pinning categories.
- **No modifications to prior reducer or audit scripts.** v0.53i's reducer remains byte-identical to its merged form.
- **A_null_V0_25 arm is byte-identical to v0.48–v0.53i A_null path AT TICK-50.** Tier-1 re-anchor enforces this within 1e-3.
- **B_widened_V0_25 arm is byte-identical to v0.53–v0.53i's B_widened arm at every tick 0..200.** Tier-2 categorical anchor enforces `b_widened_v025_reachability_run_share_tick_200 == 0.0`.
- **D_widened_food_near2_combined_N400 arm is byte-identical to v0.53i's C arm at every tick 0..400.** Tier-3 positive anchor enforces (a) reachability_run_share_tick_400 == 35/64 exact, (b) sub-verdict == BRIDGE_PRESENT, (c) six paired_d cells within 1e-3 of v0.53i published values.
- **C_widened_food_near1_combined_N400 differs from D_widened_food_near2_combined_N400 by exactly the layout** (food_x_min: 8 → 9; food_x_max: 12 → 13; world_width: 13 → 14; corridor at x=8 added). Hazard band, safe band, food width, spawn, height all identical. Body_config and n_ticks identical.
- **No intervention at any level on any arm.**

## Corpus (locked, 64 × 4 arms = 256 runs; asymmetric wall time)

Same shape as v0.53–v0.53i:

| version | seeds | hazards | runs per arm | total runs |
|---|---|---|---|---|
| v0.42 | 41..48 | {0, 8} | 16 | 64 |
| v0.43R | 49..56 | {0, 8} | 16 | 64 |
| v0.44 | 57..64 | {0, 8} | 16 | 64 |
| v0.45 | 65..72 | {0, 8} | 16 | 64 |
| **total** | | | | **256** |

V0_25 substrate identical to v0.53–v0.53i on A and B; C and D identical to v0.53i C except for the layout substitution on C. Wall time estimate ~25–50 minutes total (asymmetric: 128 runs at `n_ticks=200`, 128 runs at `n_ticks=400`).

## Arms (locked, 4 — asymmetric layout AND `n_ticks`; identical body_config on C and D)

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

Byte-identical to v0.48–v0.53i A_null path at every tick 0..200. **Tier-1 anchor at tick-50.**

### B_widened_V0_25

```
ChamberLayout = widened_gradient_layout()
  (safe x=[0,4], hazard x=[5,7], corridor x=[8,9], food x=[10,14], spawn_x=1, height=6, width=15)
... (V0_25 baseline; body_config=None; n_ticks=200)
```

Byte-identical to v0.53–v0.53i's B_widened arm at every tick 0..200. **Tier-2 categorical anchor on tick-200 reachability.**

### C_widened_food_near1_combined_N400 (PRIMARY VERDICT-GATING)

```
ChamberLayout = ChamberLayout(  # script-local FOOD_NEAR1_LAYOUT, NOT in layouts.py
    safe_x_min=0, safe_x_max=4,
    hazard_x_min=5, hazard_x_max=7,
    food_x_min=9, food_x_max=13,
    height=6, spawn_x=1,
)
  (safe x=[0,4], hazard x=[5,7], corridor x=[8] (1-column),
   food x=[9,13], spawn_x=1, height=6, width=14)
... (V0_25 baseline pool/ecology;
    body_config = BodyConfig(starting_energy=100.0, base_metabolic_cost=0.10);
    n_ticks = 400)
```

Differs from D by exactly the layout (food band shifted 1 column right; 1 column of corridor remaining at x=8). Differs from B by layout AND two BodyConfig knobs AND `n_ticks`. **The primary arm of v0.53j**: the verdict gates on C's tick-400 reachability and tick-400 sub-verdict.

### D_widened_food_near2_combined_N400 (IN-SLICE POSITIVE ANCHOR)

```
ChamberLayout = ChamberLayout(  # script-local FOOD_NEAR2_LAYOUT, NOT in layouts.py;
                                # byte-identical to v0.53i's WIDENED_FOOD_NEAR2_LAYOUT
    safe_x_min=0, safe_x_max=4,
    hazard_x_min=5, hazard_x_max=7,
    food_x_min=8, food_x_max=12,
    height=6, spawn_x=1,
)
  (safe x=[0,4], hazard x=[5,7], food x=[8,12] (corridor removed),
   spawn_x=1, height=6, width=13)
... (V0_25 baseline pool/ecology;
    body_config = BodyConfig(starting_energy=100.0, base_metabolic_cost=0.10);
    n_ticks = 400)
```

Byte-identical to v0.53i's C arm at every tick 0..400. **Tier-3 positive anchor:** the merged v0.53i Results' reachability == 35/64 AND sub-verdict == BRIDGE_PRESENT AND the six tick-400 paired_d cells within 1e-3.

## Labels (locked, two — with four Label B variants on C/D, three on A/B)

### Label A — `high_sensor_radius_lineage`

Trait-resolved (`int(founder.body.traits.sensor_radius)`); tiebreak `min(lineage_id)`. Identical to v0.48–v0.53i.

### Label B — variants computed in parallel

- **`high_tick50_readiness_fraction_lineage`** — Tier-1 anchor against v0.48–v0.53i (computed on all arms).
- **`high_tick100_readiness_fraction_lineage`** — descriptive (computed on all arms; NOT gating).
- **`high_tick200_readiness_fraction_lineage`** — descriptive (computed on all arms; NOT gating).
- **`high_tick400_readiness_fraction_lineage`** — **verdict-gating on C, anchor on D** (computed on C and D; undefined / NaN on A and B because their loops terminate at tick-200).

## Primary observables (locked, 3, computed at four windows on C/D, three on A/B)

| # | name pattern | windows on A/B | windows on C/D | expected sign |
|---|---|---|---|:-:|
| 1 | `pre{N}_food_events_count` | N ∈ {50, 100, 200} | N ∈ {50, 100, 200, 400} | + |
| 2 | `pre{N}_food_energy_acquired` | N ∈ {50, 100, 200} | N ∈ {50, 100, 200, 400} | + |
| 3 | `mean_distance_to_nearest_food_cell_tick{N}` | N ∈ {50, 100, 200} | N ∈ {50, 100, 200, 400} | − |

Definitions / aggregation rules / NaN handling: copy-local from v0.48–v0.53i.

**Note on observable 3 (mean distance to nearest food cell):** the value depends on the layout's food cells. Each arm's metric uses its own layout's food cells. Cross-arm signed_d is therefore NOT directly cross-arm interpretable; sub-verdict firing is per-arm only.

## Effect-size rule (locked, sign-aware, identical to v0.48–v0.53i)

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
    (TIER-2 ANCHOR — must equal 0.0 exactly)

c_widened_food_near1_combined_N400_reachability_run_share_tick_400 =
    fraction of C_widened_food_near1_combined_N400 runs where at least one
    founder lineage has pre400_food_events_count > 0
    (VERDICT-GATING; threshold 0.25)

d_widened_food_near2_combined_N400_reachability_run_share_tick_400 =
    fraction of D_widened_food_near2_combined_N400 runs where at least one
    founder lineage has pre400_food_events_count > 0
    (TIER-3 POSITIVE ANCHOR — must equal 35/64 = 0.546875 exactly)
```

Domain: 64 runs per arm. Threshold: **`B_REACHABILITY_THRESHOLD = 0.25`** (preserved from v0.53b–v0.53i).

## Tier-3 positive anchor on D (locked, pre-data, six paired_d cells)

| label | observable | published v0.53i signed_d | tolerance |
|---|---|:-:|:-:|
| `label_a_sensor_radius` | `pre400_food_events_count` | **+1.036** | 1e-3 |
| `label_a_sensor_radius` | `pre400_food_energy_acquired` | **+1.036** | 1e-3 |
| `label_a_sensor_radius` | `mean_distance_to_nearest_food_cell_tick400` | **+1.062** | 1e-3 |
| `label_b_readiness_fraction_tick400` | `pre400_food_events_count` | **+5.304** | 1e-3 |
| `label_b_readiness_fraction_tick400` | `pre400_food_energy_acquired` | **+5.304** | 1e-3 |
| `label_b_readiness_fraction_tick400` | `mean_distance_to_nearest_food_cell_tick400` | **+6.295** | 1e-3 |

All six must reproduce within 1e-3 absolute drift. Plus categorical: D tick-400 reachability == 0.546875 (35/64) exact, AND D tick-400 sub-verdict == `D_WIDENED_FOOD_NEAR2_TICK400_BRIDGE_PRESENT`.

## Population-stability and degenerate-label descriptive metrics (locked, pre-data, per arm × window)

Identical structure to v0.53c–v0.53i; on C and D extended for the tick-400 panel.

## Per-arm sub-verdicts (locked, 4-way each — verdict-gating window is C tick-400 only; anchor window is D tick-400)

| condition | A_null_V0_25 (tick-50 anchor) | B_widened_V0_25 (tick-200 informational) | C_widened_food_near1_combined_N400 (tick-400 **verdict-gating**) | D_widened_food_near2_combined_N400 (tick-400 **anchor**) |
|---|---|---|---|---|
| both labels clear ≥ 2/3 cells, NaN non-firing, 0 wrong-sign | `A_NULL_V025_TICK{50,100,200}_BRIDGE_PRESENT` | `B_WIDENED_V025_TICK200_BRIDGE_PRESENT` | `C_WIDENED_FOOD_NEAR1_TICK400_BRIDGE_PRESENT` | `D_WIDENED_FOOD_NEAR2_TICK400_BRIDGE_PRESENT` |
| exactly one label clears ≥ 2/3 cells, NaN non-firing, 0 wrong-sign | `..._BRIDGE_PARTIAL` | `B_WIDENED_V025_TICK200_BRIDGE_PARTIAL` | `C_WIDENED_FOOD_NEAR1_TICK400_BRIDGE_PARTIAL` | `D_WIDENED_FOOD_NEAR2_TICK400_BRIDGE_PARTIAL` |
| neither label clears ≥ 2/3 cells, NaN non-firing, 0 wrong-sign | `..._BRIDGE_NOT_FOUND` | `B_WIDENED_V025_TICK200_BRIDGE_NOT_FOUND` | `C_WIDENED_FOOD_NEAR1_TICK400_BRIDGE_NOT_FOUND` | `D_WIDENED_FOOD_NEAR2_TICK400_BRIDGE_NOT_FOUND` |
| any primary signed_d ≤ −0.5 under either label | `..._OPPOSITE_SIGN_HALT` | `B_WIDENED_V025_TICK200_OPPOSITE_SIGN_HALT` | `C_WIDENED_FOOD_NEAR1_TICK400_OPPOSITE_SIGN_HALT` | `D_WIDENED_FOOD_NEAR2_TICK400_OPPOSITE_SIGN_HALT` |

C's and D's tick-50/100/200 sub-verdicts are computed and logged descriptively. The verdict gates on C's tick-400 panel; the Tier-3 anchor enforces D's tick-400 panel.

**Strict NaN-treated-as-non-firing rule preserved.**

## Slice rollup verdicts (locked, 6 outcomes, priority-ordered — PRIORITY 3 IS REACHABILITY-GATED ON C TICK-400)

Priority order (first-matching wins). The non-halt outcomes (priorities 4–6) gate **only on C_widened_food_near1_combined_N400 at tick-400**.

1. `CORPUS_REDERIVE_DRIFT_HALT`
2. `ANCHOR_REPLICATION_HALT` (Tier-1 A tick-50 + Tier-2 B tick-200 + Tier-3 D tick-400 positive anchor)
3. `GEOMETRY_OPPOSITE_SIGN_HALT` (**reachability-gated** on C tick-400)
4. `WIDENED_BRIDGE_RESCUED_BY_FOOD_NEAR1`
5. `WIDENED_BELOW_REACHABILITY_THRESHOLD_UNDER_FOOD_NEAR1`
6. `WIDENED_BRIDGE_PARTIALLY_RESCUED_BY_FOOD_NEAR1`

### Halt conditions

| priority | rollup verdict | trigger | locked phrase (verbatim) |
|---|---|---|---|
| 1 | `CORPUS_REDERIVE_DRIFT_HALT` | A_null_V0_25 arm `a_share_h8` for any of v0.42 / v0.44 / v0.45 drifts > 1e-3 | "Halt: A_null_V0_25 re-anchor drifted from the published Results value for {version}; v0.53j's deterministic re-execution of the V0_25 corpus does not reproduce the published metric within 1e-3." |
| 2 | `ANCHOR_REPLICATION_HALT` | (a) A_null_V0_25 tick-50 signed_d for any of the six v0.48–v0.53i cells drifts > 1e-3, OR (b) A_null_V0_25 tick-50 sub-verdict ≠ PRESENT, OR (c) `b_widened_v025_reachability_run_share_tick_200` ≠ `0.0`, OR (d) `d_widened_food_near2_combined_N400_reachability_run_share_tick_400` ≠ `0.546875` (35/64) exact, OR (e) D tick-400 sub-verdict ≠ `D_WIDENED_FOOD_NEAR2_TICK400_BRIDGE_PRESENT`, OR (f) D tick-400 signed_d for any of the six v0.53i published cells drifts > 1e-3 | "Halt: v0.53j's A_null_V0_25 arm does not reproduce v0.48–v0.53i's tick-50 spatial bridge, OR v0.53j's B_widened_V0_25 arm does not reproduce v0.53c–v0.53i's `0/64` reachability lock at tick-200, OR v0.53j's D_widened_food_near2_combined_N400 arm does not reproduce v0.53i's tick-400 positive anchor (categorical reachability `35/64` AND sub-verdict `BRIDGE_PRESENT` AND six published paired_d cells within 1e-3). v0.53j cannot interpret the C_widened_food_near1_combined_N400 cells without reproducing both the V0_25 baseline anchors and the v0.53i FOOD_NEAR2 positive anchor." |
| 3 | `GEOMETRY_OPPOSITE_SIGN_HALT` (**reachability-gated**) | C tick-400 sub-verdict = `C_WIDENED_FOOD_NEAR1_TICK400_OPPOSITE_SIGN_HALT` AND `c_widened_food_near1_combined_N400_reachability_run_share_tick_400 ≥ 0.25` | "Halt: a v0.53j C_widened_food_near1_combined_N400 tick-400 spatial / foraging primary fires in the WRONG direction under a gating label, AND C reachability at tick-400 clears the locked 25% threshold. The 1-column geometric intervention (food band moved from `x∈[10,14]` under `widened_gradient` to `x∈[9,13]`; 1-column corridor remaining at `x=8`) under the v0.53g/h/i combined founder-facing budget envelope at `n_ticks = 400` surfaces a regime where the locked expected signs do not hold under measurable food access. The reachability-gated trigger preserves v0.53e's locked sign discipline while excluding the v0.53e-style measurement-edge case (wrong-sign at reachability=0)." |

### Tier-1 (priority 2.a) re-anchor — A_null_V0_25 tick-50 cells

Identical six cells to v0.48–v0.53i; published signed_d: +1.066 / +1.066 / +1.916 / +0.916 / +0.916 / +1.179. Drift tolerance = 1e-3.

### Tier-2 (priority 2.c) categorical anchor — B_widened_V0_25 tick-200 reachability

| anchor | locked value | tolerance |
|---|:-:|---|
| `b_widened_v025_reachability_run_share_tick_200` | **0.0** (i.e., `0/64`) | exact (categorical) |

Locked from v0.53c–v0.53i.

### Tier-3 (priority 2.d / 2.e / 2.f) positive anchor — D_widened_food_near2_combined_N400 tick-400

| anchor | locked value | tolerance |
|---|:-:|---|
| `d_widened_food_near2_combined_N400_reachability_run_share_tick_400` | **0.546875** (35/64) | exact (categorical) |
| D tick-400 sub-verdict | **`D_WIDENED_FOOD_NEAR2_TICK400_BRIDGE_PRESENT`** | exact (categorical) |
| D tick-400 paired_d (six cells, see Tier-3 table above) | published v0.53i values | 1e-3 absolute drift |

Locked from v0.53i merged Results.

### Outcome conditions (only consulted if no halt fires)

| priority | rollup verdict | trigger | locked phrase (verbatim) |
|---|---|---|---|
| 4 | `WIDENED_BRIDGE_RESCUED_BY_FOOD_NEAR1` | `c_widened_food_near1_combined_N400_reachability_run_share_tick_400 ≥ 0.25` AND C tick-400 sub-verdict = `C_WIDENED_FOOD_NEAR1_TICK400_BRIDGE_PRESENT` | "On the modern A_null corpus with the V0_25 substrate held constant except for the combined founder-facing budget relaxation `BodyConfig(starting_energy=100.0, base_metabolic_cost=0.10)` AND the simulation horizon doubled to `n_ticks=400` AND the post-hazard food distance reduced by ONE column (food band moved from `x∈[10,14]` under `widened_gradient` to `x∈[9,13]` under the script-local `widened_food_near1` layout; 1-column corridor remaining at `x=8`; hazard band, food width, spawn position, safe band, and chamber height preserved), the v0.48 sensor_radius spatial / foraging bridge fires PRESENT under the locked +0.5 paired_d threshold at tick-400. The geometry/substrate cell that v0.53c locked as `WIDENED_BELOW_REACHABILITY_THRESHOLD_AT_TICK_200`, v0.53d locked as `WIDENED_BELOW_REACHABILITY_THRESHOLD_UNDER_RELAXED_INFLUX`, v0.53e locked as `RELAXED_OPPOSITE_SIGN_HALT`, v0.53f locked as `WIDENED_BELOW_REACHABILITY_THRESHOLD_UNDER_BASE_METABOLIC_COST_010`, v0.53g locked as `WIDENED_BELOW_REACHABILITY_THRESHOLD_UNDER_COMBINED_SE100_BMC010`, v0.53h locked as `WIDENED_BELOW_REACHABILITY_THRESHOLD_AT_TIME_HORIZON_400`, and v0.53i locked as `WIDENED_BRIDGE_RESCUED_BY_FOOD_NEAR2` admits a measurable bridge under the 1-column intervention: B_widened_V0_25 reachability remains `0/64` at tick-200 (predecessor lock holds), D_widened_food_near2_combined_N400 reachability reproduces v0.53i's `35/64` positive anchor at tick-400 (positive lock holds), C reachability at tick-400 clears the locked 25% threshold, and ≥ 2/3 spatial / foraging primaries fire PRESENT under both gating labels at the C tick-400 panel. The tested rescue boundary is at or below 1-column reduction; the 2-column reduction tested by v0.53i is NOT minimal under the tested envelope. This does NOT prove `1 column is the universal minimum` or `the boundary is at exactly 1.5 columns` — only that this specific 1-column reduction is sufficient under the tested envelope: `WIDENED_BRIDGE_RESCUED_BY_FOOD_NEAR1`." |
| 5 | `WIDENED_BELOW_REACHABILITY_THRESHOLD_UNDER_FOOD_NEAR1` | `c_widened_food_near1_combined_N400_reachability_run_share_tick_400 < 0.25` | "On the modern A_null corpus with the V0_25 substrate held constant except for the combined founder-facing budget relaxation `BodyConfig(starting_energy=100.0, base_metabolic_cost=0.10)` AND the simulation horizon doubled to `n_ticks=400` AND the post-hazard food distance reduced by ONE column (food band moved from `x∈[10,14]` under `widened_gradient` to `x∈[9,13]` under the script-local `widened_food_near1` layout; 1-column corridor remaining at `x=8`), fewer than 25% of C runs have any founder lineage with pre400 food events. C's reachability is below the locked 25% threshold at tick-400; D_widened_food_near2_combined_N400 reproduces v0.53i's `35/64` positive anchor at tick-400 in-slice. The tested rescue boundary lies between the historical `widened_gradient` baseline (`food_x∈[10,14]`, 2-column corridor) and FOOD_NEAR2 (`food_x∈[8,12]`, 0-column corridor), with FOOD_NEAR1 (`food_x∈[9,13]`, 1-column corridor) failing — the 1-column reduction is INsufficient under the tested envelope. The geometry/substrate cell that v0.53c locked as `WIDENED_BELOW_REACHABILITY_THRESHOLD_AT_TICK_200`, v0.53d locked as `WIDENED_BELOW_REACHABILITY_THRESHOLD_UNDER_RELAXED_INFLUX`, v0.53e locked as `RELAXED_OPPOSITE_SIGN_HALT`, v0.53f locked as `WIDENED_BELOW_REACHABILITY_THRESHOLD_UNDER_BASE_METABOLIC_COST_010`, v0.53g locked as `WIDENED_BELOW_REACHABILITY_THRESHOLD_UNDER_COMBINED_SE100_BMC010`, v0.53h locked as `WIDENED_BELOW_REACHABILITY_THRESHOLD_AT_TIME_HORIZON_400`, and v0.53i locked as `WIDENED_BRIDGE_RESCUED_BY_FOOD_NEAR2` is partially generalized along the food-distance axis: the rescue requires reduction beyond 1 column under the tested envelope. This does NOT prove `the minimum is 2 columns universally` or `1 column is irrelevant` — only that this specific 1-column reduction does not lift reachability under the tested envelope: `WIDENED_BELOW_REACHABILITY_THRESHOLD_UNDER_FOOD_NEAR1`." |
| 6 | `WIDENED_BRIDGE_PARTIALLY_RESCUED_BY_FOOD_NEAR1` | `c_widened_food_near1_combined_N400_reachability_run_share_tick_400 ≥ 0.25` AND C tick-400 sub-verdict ∈ {`C_WIDENED_FOOD_NEAR1_TICK400_BRIDGE_PARTIAL`, `C_WIDENED_FOOD_NEAR1_TICK400_BRIDGE_NOT_FOUND`} | "On the modern A_null corpus with the V0_25 substrate held constant except for the combined founder-facing budget relaxation `BodyConfig(starting_energy=100.0, base_metabolic_cost=0.10)` AND the simulation horizon doubled to `n_ticks=400` AND the post-hazard food distance reduced by ONE column (food band moved from `x∈[10,14]` under `widened_gradient` to `x∈[9,13]` under the script-local `widened_food_near1` layout), C's reachability clears the locked 25% threshold at tick-400 but the v0.48 sensor_radius spatial / foraging bridge does not fully fire PRESENT — fewer than 2/3 primaries fire across both gating labels at tick-400 under the strict NaN rule. D_widened_food_near2_combined_N400 reproduces v0.53i's `35/64` positive anchor at tick-400 in-slice. The 1-column intervention admits measurable food access but does not fully replicate v0.53i's PRESENT bridge expression. Layout-specific partial-rescue logged in Results: `WIDENED_BRIDGE_PARTIALLY_RESCUED_BY_FOOD_NEAR1`." |

The 3 non-halt outcomes form a total partition of (C tick-400 reachability ≥ 0.25, C tick-400 sub-verdict ∈ {PRESENT, PARTIAL, NOT_FOUND, OPPOSITE_SIGN_HALT}) ∪ (C tick-400 reachability < 0.25). Under the reachability-gated priority-3 trigger:
- **C reachability ≥ 0.25 AND C sub-verdict = OPPOSITE_SIGN_HALT** → priority 3 fires (halt).
- **C reachability ≥ 0.25 AND C sub-verdict = PRESENT** → priority 4 fires.
- **C reachability ≥ 0.25 AND C sub-verdict ∈ {PARTIAL, NOT_FOUND}** → priority 6 fires.
- **C reachability < 0.25** → priority 5 fires.

Test #16 enforces the partition exhaustively.

## Cautious framing (per CLAUDE.md)

- "**The tested rescue boundary is at or below 1-column reduction**" (priority 4) — NOT "1 column is the universal minimum", NOT "the boundary is at exactly 1.5 columns". Bounded to the tested two doses (1-column and 2-column) under the tested envelope.
- "**The tested rescue boundary lies between the historical widened_gradient baseline (2-column corridor) and FOOD_NEAR2 (0-column corridor), with FOOD_NEAR1 (1-column corridor) failing**" (priority 5) — NOT "the minimum is 2 columns universally", NOT "1 column is irrelevant". Bounded to the tested envelope; does NOT establish behavior at non-integer reductions, alternative geometric perturbations, or non-V0_25 substrates.
- v0.53j explicitly does not establish: cross-layout generalization beyond the named layouts (`tight_gradient`, `widened_gradient`, `widened_food_near1`, `widened_food_near2`), mechanism for any rescue or non-rescue outcome at FOOD_NEAR1, generalization to non-V0_25 substrates, behavior at non-`n_ticks=400` horizons under the same geometry, dose-response below 1-column or above 2-column.

## What v0.53j cannot establish (logged here pre-data, not retrofittable)

- ✗ **"Distance is the binding constraint"** under priority 4. v0.53j establishes that a 1-column reduction is sufficient (or insufficient); it does not establish that distance is the sole or even principal explanation.
- ✗ **"The minimum sufficient reduction is exactly 1 column"** under priority 4. v0.53j does NOT test 0-column (already excluded — that is widened_gradient baseline; null per v0.53c–v0.53h) or 0.5-column (cells are integer-indexed). The bounded claim is that this specific 1-column reduction is sufficient under the tested envelope, not that it is the minimum.
- ✗ **"FOOD_NEAR2 is the minimum sufficient reduction"** under priority 5. v0.53j establishes that FOOD_NEAR1 fails AND FOOD_NEAR2 passes; the boundary lies between them. v0.53j does NOT test alternative interventions (e.g., reduced hazard thickness) that might admit reachability at the 1-column food distance.
- ✗ **A revised v0.53–v0.53i verdict.** All nine predecessor verdicts stand as historical contracts.
- ✗ **Mechanism behind any C outcome.** Population dynamics under V0_25 × `widened_food_near1` × combined-budget × `n_ticks=400` are descriptively logged; no mechanism is formally established.
- ✗ **Generalization beyond the tested arms.**

## Open framing (NOT in v0.53j primary)

- **If priority 4 fires** (1-column rescues): natural follow-ups include dose-response below 1 column (only possible via non-integer interventions like alternative spawn positions or reduced hazard thickness — not direct food-distance variants since the next integer reduction is 0-column = widened_gradient baseline), Reading-A causal-generalization on `widened_food_near1`, and substrate cross-corpus calibration.
- **If priority 5 fires** (1-column insufficient): natural follow-ups include hazard-band traversal mechanics probe, policy / hazard-avoidance probe under the same geometric envelopes, alternative spawn position to test perceptual reach independently of distance.
- **v0.53k candidate (open) — hazard-band traversal mechanics.** Vary `hazard_damage` dose or hazard-band thickness on `widened_food_near1` (or `widened_food_near2`) under V0_25 × combined-budget × `n_ticks=400`.
- **v0.53l candidate — policy / hazard-avoidance probe.** Vary `hazard_avoidance_weight` or other policy knobs.
- **v0.53m candidate — Reading-A causal-generalization on `widened_food_near2` and (if priority 4 fires) `widened_food_near1`.**
- **v0.54 — joint ablation** (zero-cost AND shuffle).
- **Eventual fresh-stream calibration** on the v0.46–v0.53j conclusion stack.

## Re-anchor (locked — Tier-1 and corpus only at tick-50)

| version | published `a_share_h8` |
|---|---|
| v0.42 | 0.652 |
| v0.43R | NOT PUBLISHED (informational-only) |
| v0.44 | 0.878 |
| v0.45 | 0.818 |

## Outputs (locked)

```
runs/v0.53j-food-distance-dose-response/per_run_per_lineage_v053j.csv
  columns: arm, layout_name,
           safe_x_min, safe_x_max, hazard_x_min, hazard_x_max,
           food_x_min, food_x_max, world_width, spawn_x, height,
           body_starting_energy, body_base_metabolic_cost, n_ticks,
           version, seed, hazard, run_id, lineage_id,
           founder_sensor_radius, founder_reproduction_drive, founder_metabolic_rate,
           pre50_food_events_count, pre50_food_energy_acquired,
           pre100_food_events_count, pre100_food_energy_acquired,
           pre200_food_events_count, pre200_food_energy_acquired,
           pre400_food_events_count, pre400_food_energy_acquired,        # C/D only; NaN on A/B
           mean_distance_to_nearest_food_cell_tick50,
           mean_distance_to_nearest_food_cell_tick100,
           mean_distance_to_nearest_food_cell_tick200,
           mean_distance_to_nearest_food_cell_tick400,                   # C/D only; NaN on A/B
           tick50_living_count, tick50_above_threshold_count, tick50_above_threshold_fraction,
           tick100_living_count, tick100_above_threshold_count, tick100_above_threshold_fraction,
           tick200_living_count, tick200_above_threshold_count, tick200_above_threshold_fraction,
           tick400_living_count, tick400_above_threshold_count, tick400_above_threshold_fraction,  # C/D only; NaN on A/B
           b50_count, is_eventual_top_b50_label,
           is_high_sensor_radius_lineage,
           is_high_tick50_readiness_fraction_lineage,
           is_high_tick100_readiness_fraction_lineage,
           is_high_tick200_readiness_fraction_lineage,
           is_high_tick400_readiness_fraction_lineage                   # C/D only; NaN on A/B

runs/v0.53j-food-distance-dose-response/audit_summary.csv
  (includes the wrong_sign_cells_under_reachability_below_threshold section
   carried forward from v0.53f/g/h/i; gates on C tick-400 reachability)

runs/v0.53j-food-distance-dose-response/audit_log.txt
```

## Implementation plan (locked)

1. **No `src/` changes.** Both novel layouts constructed script-local. v0.53e's `body_config` seam carries forward; `n_ticks` already exposed.
2. Fresh script `scripts/v0_53j_food_distance_dose_response_audit.py`. CLI: `uv run python scripts/v0_53j_food_distance_dose_response_audit.py [--out-dir runs/v0.53j-food-distance-dose-response]`.
3. Define module-level constants:
   ```python
   FOOD_NEAR1_LAYOUT = ChamberLayout(safe_x_min=0, safe_x_max=4, hazard_x_min=5, hazard_x_max=7, food_x_min=9, food_x_max=13, height=6, spawn_x=1)
   FOOD_NEAR2_LAYOUT = ChamberLayout(safe_x_min=0, safe_x_max=4, hazard_x_min=5, hazard_x_max=7, food_x_min=8, food_x_max=12, height=6, spawn_x=1)
   ```
4. Per (version, seed, hazard) tuple, run **4 arms**.
5. Setup_observer order: capture founder audit table including `body.energy`, `body_config.starting_energy`, `body_config.base_metabolic_cost`, layout column geometry, and `n_ticks` per arm at tick 0.
6. Per-tick observer accumulates pre50/pre100/pre200 rollups in parallel on all arms; pre400 rollups on C and D only.
7. Use the relaxed contiguous-prefix tick-records invariant from v0.53b–v0.53i.
8. Aggregate per-lineage primaries at three windows on A/B and four windows on C/D. Compute Label A and four Label B variants (the tick-400 variant computed on C and D only; NaN-broadcast on A/B).
9. Compute paired_d per (arm, gating-label, observable, window) cell.
10. Compute per-arm reachability_run_share at every window the arm reaches.
11. Compute per-arm population-stability metrics.
12. **Tier-1 bridge re-anchor** (priority 2.a / 2.b): A_null_V0_25 arm's six tick-50 cells vs v0.48–v0.53i published; halt if drift > 1e-3 OR if A tick-50 sub-verdict ≠ PRESENT.
13. **Tier-2 categorical anchor** (priority 2.c): `b_widened_v025_reachability_run_share_tick_200 == 0.0` exactly.
14. **Tier-3 positive anchor** (priority 2.d / 2.e / 2.f): D_widened_food_near2_combined_N400 tick-400 reachability == 35/64 exact AND D tick-400 sub-verdict == BRIDGE_PRESENT AND D tick-400 six paired_d cells reproduce v0.53i within 1e-3.
15. **Corpus re-anchor** (priority 1): A_null_V0_25 arm only; halt if `a_share_h8` for v0.42 / v0.44 / v0.45 drifts > 1e-3.
16. **Reachability-gated geometry opposite-sign halt** (priority 3, gates on C tick-400): scan all C tick-400 gating-label cells; if any signed_d ≤ −0.5 AND `c_reachability_tick_400 ≥ 0.25` → halt loud (`GEOMETRY_OPPOSITE_SIGN_HALT`). Otherwise: log descriptively; do NOT halt.
17. Compute slice rollup verdict per the locked priority + (C tick-400 reachability, C tick-400 sub-verdict) decision matrix; print + write the locked phrase verbatim.

The reducer is fully self-contained: it reads no `runs/` artifacts. Wall time estimate ~25–50 minutes for 256 runs.

## Test list (locked, 16 tests)

`tests/test_v0_53j_food_distance_dose_response_audit.py`:

1. **`test_paired_d_function_reproduces_hand_computed_signed_d_on_fixture_and_tier1_v048_constants_and_tier3_v053i_constants`** *(re-anchor test, three-part: paired_d hand-fixture; six v0.48 published Tier-1 constants; six v0.53i published Tier-3 constants for D)*.
2. **`test_a_null_v025_corpus_a_share_h8_re_anchors_v042_v044_v045`** — drift halt fires if any drift > 1e-3.
3. `test_arm_a_null_v025_uses_tight_gradient_layout_default_body_config_and_n_ticks_200_with_explicit_geometry_asserts` — assert all nine ChamberLayout fields including world_width=9, body_config=None, n_ticks=200.
4. `test_arm_b_widened_v025_uses_widened_gradient_layout_default_body_config_and_n_ticks_200_with_explicit_geometry_asserts` — assert food_x_min=10, food_x_max=14, hazard_x_min=5, hazard_x_max=7, safe_x_min=0, safe_x_max=4, spawn_x=1, height=6, world_width=15, body_config=None, n_ticks=200.
5. **`test_arms_c_and_d_use_food_near1_and_food_near2_layouts_combined_body_config_and_n_ticks_400_with_explicit_geometry_asserts`** — verifies the script-local layout constants AND BodyConfig knobs AND horizon for both novel arms:
   - **C founder body fields at tick-0**: `body.energy == 100.0`, `body_config.starting_energy == 100.0`, `body_config.base_metabolic_cost == 0.10`.
   - **C layout geometry**: `food_x_min == 9`, `food_x_max == 13`, `hazard_x_min == 5`, `hazard_x_max == 7`, `safe_x_min == 0`, `safe_x_max == 4`, `spawn_x == 1`, `height == 6`, `world_width == 14`.
   - **C model end-state**: `_RunCapture.final_tick_count == 400`.
   - **D founder body fields at tick-0**: identical to C (`body.energy == 100.0`, etc.).
   - **D layout geometry**: `food_x_min == 8`, `food_x_max == 12`, hazard / safe / spawn / height match C, `world_width == 13`.
   - **D model end-state**: `_RunCapture.final_tick_count == 400`.
6. **`test_cross_arm_layout_dose_contrast_b_c_d_food_x_min_shift_and_preserved_invariants`** *(four-arm contrast — verifies dose-response geometry)* — for the same (version, seed, hazard) tuple under matched RNG:
   - **Positive intervention (B → D)**: `B.food_x_min == 10` AND `D.food_x_min == 8` (2-column shift; v0.53i intervention).
   - **Intermediate dose (B → C)**: `B.food_x_min == 10` AND `C.food_x_min == 9` (1-column shift; v0.53j intervention).
   - **Dose ordering**: `D.food_x_min < C.food_x_min < B.food_x_min`.
   - **Preserved invariants across B, C, D**: `B.hazard_x_min == C.hazard_x_min == D.hazard_x_min == 5`; `B.hazard_x_max == C.hazard_x_max == D.hazard_x_max == 7`; `B.safe_x_min == C.safe_x_min == D.safe_x_min == 0`; `B.safe_x_max == C.safe_x_max == D.safe_x_max == 4`; `B.spawn_x == C.spawn_x == D.spawn_x == 1`; `B.height == C.height == D.height == 6`; food width = 5 columns on all three (`B.food_x_max - B.food_x_min + 1 == 5`, same for C and D).
   - **Secondary invariants**: `B.world_width == 15`, `C.world_width == 14`, `D.world_width == 13`.
   - **C and D body_config matches v0.53i C body_config**: `C.body_starting_energy == D.body_starting_energy == 100.0`, `C.body_base_metabolic_cost == D.body_base_metabolic_cost == 0.10`.
7. **`test_founder_traits_byte_identical_across_arms_for_same_seed`**.
8. **`test_no_src_modifications_compared_to_v0_53e_tip`** *(two-part src/ pinning test, IDENTICAL to v0.53e/f/g/h/i)*:
   - Part A: SHA-256 of five science-core files match v0.52b-tip values (including layouts.py at `d4521cb5...`). Failure message: `"v0.53j is pre-registered to leave the science-core five files byte-identical to v0.52b-tip; update the pre-reg before changing src/core or src/experiments/layouts."`
   - Part B: SHA-256 of `src/hedonism_harness/experiments/fear_hunger_chamber.py` matches `62d134c5...`. Failure message: `"v0.53j is pre-registered to leave the chamber driver byte-identical to its v0.53e-tip hash; update the pre-reg before re-touching the chamber driver."`
9. `test_label_a_high_sensor_radius_lineage_picks_correct_lineage`.
10. **`test_label_b_four_variants_three_tier_tiebreak_at_each_window_with_pre400_c_and_d_only`** — tick-50/100/200 variants computed on all arms; tick-400 variant computed on C and D and NaN-broadcast on A/B.
11. **`test_pre400_window_strictly_extends_pre200_pre100_pre50_windows_on_c_and_d_arms`** — synthetic events; assert pre50/pre100/pre200/pre400 counts on both C and D; assert pre400 NaN on A and B.
12. **`test_subverdict_present_requires_two_thirds_firing_cells_with_nan_treated_as_non_firing_strict`**.
13. **`test_priority_3_geometry_opposite_sign_halt_is_reachability_gated_on_c_tick_400`** — three branches at the C tick-400 panel; halt name `GEOMETRY_OPPOSITE_SIGN_HALT`.
14. **`test_b_widened_v025_categorical_anchor_at_tick_200_and_d_food_near2_positive_anchor_at_tick_400`** — synthetic B reachability=0.0 + D reachability=35/64 + D sub-verdict=BRIDGE_PRESENT + D paired_d cells matching → priority 2 does NOT fire. Synthetic B reachability=1/64 → ANCHOR_REPLICATION_HALT (Tier-2). Synthetic D reachability=34/64 → ANCHOR_REPLICATION_HALT (Tier-3 categorical reachability). Synthetic D sub-verdict=PARTIAL → ANCHOR_REPLICATION_HALT (Tier-3 sub-verdict). Synthetic D paired_d cell drifted by 0.005 → ANCHOR_REPLICATION_HALT (Tier-3 paired_d drift).
15. **`test_c_tick_400_reachability_threshold_partition`** — synthetic C reachability 0.20 / 0.30 × {PRESENT, PARTIAL, NOT_FOUND} → priorities 4/5/6 fire correctly.
16. **`test_rollup_locked_phrases_fire_verbatim_and_priority_cascade_partition_total`** — assert locked phrase contains diagnostic substring verbatim:
    - Priority 3 (GEOMETRY_OPPOSITE_SIGN_HALT): `"AND C reachability at tick-400 clears the locked 25% threshold"` AND `"The reachability-gated trigger preserves v0.53e's locked sign discipline"`.
    - Priority 4 RESCUED: `"the post-hazard food distance reduced by ONE column"` AND `"D_widened_food_near2_combined_N400 reachability reproduces v0.53i's \`35/64\` positive anchor at tick-400 (positive lock holds)"` AND `"The tested rescue boundary is at or below 1-column reduction; the 2-column reduction tested by v0.53i is NOT minimal under the tested envelope"` AND substring references to v0.53c, v0.53d, v0.53e, v0.53f, v0.53g, v0.53h, v0.53i verdict names.
    - Priority 5 BELOW_THRESHOLD: `"the post-hazard food distance reduced by ONE column"` AND `"D_widened_food_near2_combined_N400 reproduces v0.53i's \`35/64\` positive anchor at tick-400 in-slice"` AND `"The tested rescue boundary lies between the historical \`widened_gradient\` baseline (\`food_x∈[10,14]\`, 2-column corridor) and FOOD_NEAR2 (\`food_x∈[8,12]\`, 0-column corridor), with FOOD_NEAR1 (\`food_x∈[9,13]\`, 1-column corridor) failing — the 1-column reduction is INsufficient under the tested envelope"` AND substring references to v0.53c–v0.53i verdict names.
    - Priority 6 PARTIALLY_RESCUED: `"D_widened_food_near2_combined_N400 reproduces v0.53i's \`35/64\` positive anchor at tick-400 in-slice"` AND substring references to v0.53c–v0.53i verdict names.
    Synthesize halt cascade (priorities 1 / 2.a / 2.b / 2.c / 2.d / 2.e / 2.f / 3); assert priority order. Exhaustively iterate (C tick-400 reachability ≥ 0.25, C tick-400 sub-verdict ∈ {PRESENT, PARTIAL, NOT_FOUND, OPPOSITE_SIGN_HALT}) ∪ (C tick-400 reachability < 0.25, any sub-verdict); assert unique outcome per cell.

## Watch-outs (for future-Chronus)

- **No `src/` changes.** Both novel layouts constructed script-local; v0.53e's seam carries forward unchanged. Test #8 pins both science-core five files (at v0.52b-tip including `layouts.py`) AND chamber driver (at v0.53e-tip).
- **First 4-arm slice in the substrate-axis stack.** Adds D as in-slice positive anchor.
- **Tier-3 positive anchor on D is NEW in v0.53j.** It locks v0.53i's central rescue result into v0.53j's anchor stack via deterministic re-execution. If ANY of the three D anchor sub-conditions fail, the slice halts.
- **Reachability-gated priority 3 carries forward, retains `GEOMETRY_OPPOSITE_SIGN_HALT` name.**
- **Per-arm sub-verdict structure unchanged (4-way) — verdict-gating window is C tick-400 only.**
- **Tier-2 (B reachability tick-200) and Tier-3 (D reachability tick-400) anchors are integer-categorical.**
- **Pool / ecology preserved.** Only `layout`, `body_config`, AND `n_ticks` differ across arms.
- **Founder positions byte-identical across all 4 arms** (all use `spawn_x=1`).
- **Asymmetric pre400 windows.** Pre400 NaN on A and B; computed on C and D.
- **Locked phrase discipline** verbatim. Priority-4 / -5 / -6 phrases reference v0.53c–v0.53i (predecessor stack now SEVEN long).
- **No `1 column is the universal minimum` claims under priority 4.** No `the minimum is 2 columns universally` claims under priority 5. The empirical claim is bounded to the tested two doses under the tested envelope.
- **Determinism north star** ([[scripts/core_smoke_test.py]]) must continue to pass. v0.53j makes no `src/` changes.
- **The science-core question is the dose-response shape.** v0.53j is the first dose-response slice in the geometry axis. If C rescues, the rescue threshold is at or below 1-column reduction. If C fails, the threshold is between 1 and 2 columns. Either outcome localizes the boundary to within ±1 column of the FOOD_NEAR1/FOOD_NEAR2 transition.

## Files this slice will create / modify

- `docs/experiments/fear_hunger_v0.53j.md` (this file; Results section appended after reducer run)
- `scripts/v0_53j_food_distance_dose_response_audit.py` (new)
- `tests/test_v0_53j_food_distance_dose_response_audit.py` (new, 16 tests)

No `src/` modifications. No prior reducer / audit / test / pre-reg files modified. `layouts.py` UNCHANGED.

## Results

**Status:** reducer executed 2026-05-09 against the 256-run corpus (4 arms × 64 (version, seed, hazard) tuples). Wall time well under the 25–50 minute estimate. **All four anchors PASS:** Tier-1 (A tick-50 six published v0.48 cells; max drift 0.000389 ≪ 1e-3), Tier-2 (B tick-200 reachability == 0/64 exact), **Tier-3 NEW** (D tick-400 reachability == 35/64 exact AND D tick-400 sub-verdict == `D_WIDENED_FOOD_NEAR2_TICK400_BRIDGE_PRESENT` AND **all six paired_d cells reproduce v0.53i with ZERO drift**), and corpus a_share_h8 (max drift 0.000312). **The reducer landed on priority 5** — C tick-400 reachability is `0/64` (categorical zero, NOT just below threshold), AND C tick-400 sub-verdict = `C_WIDENED_FOOD_NEAR1_TICK400_BRIDGE_NOT_FOUND`. The reachability-gated `GEOMETRY_OPPOSITE_SIGN_HALT` framework code path is exercised by test #13 with synthetic fixtures; on live data it did not activate (C reachability < 0.25, so wrong-sign cells are descriptively logged not halted; in fact only 1 of C's 6 tick-400 cells produced a finite signed_d at all — `+0.226` from the label_a / mean_distance_to_nearest_food_cell pair, which is below the +0.5 firing threshold; the other 5 cells are NaN due to absence of food contact and tick-400 lineage extinction).

### Rollup verdict — `WIDENED_BELOW_REACHABILITY_THRESHOLD_UNDER_FOOD_NEAR1` fires

> **Locked phrase fires verbatim:** "On the modern A_null corpus with the V0_25 substrate held constant except for the combined founder-facing budget relaxation `BodyConfig(starting_energy=100.0, base_metabolic_cost=0.10)` AND the simulation horizon doubled to `n_ticks=400` AND the post-hazard food distance reduced by ONE column (food band moved from `x∈[10,14]` under `widened_gradient` to `x∈[9,13]` under the script-local `widened_food_near1` layout; 1-column corridor remaining at `x=8`), fewer than 25% of C runs have any founder lineage with pre400 food events. C's reachability is below the locked 25% threshold at tick-400; D_widened_food_near2_combined_N400 reproduces v0.53i's `35/64` positive anchor at tick-400 in-slice. The tested rescue boundary lies between the historical `widened_gradient` baseline (`food_x∈[10,14]`, 2-column corridor) and FOOD_NEAR2 (`food_x∈[8,12]`, 0-column corridor), with FOOD_NEAR1 (`food_x∈[9,13]`, 1-column corridor) failing — the 1-column reduction is INsufficient under the tested envelope. The geometry/substrate cell that v0.53c locked as `WIDENED_BELOW_REACHABILITY_THRESHOLD_AT_TICK_200`, v0.53d locked as `WIDENED_BELOW_REACHABILITY_THRESHOLD_UNDER_RELAXED_INFLUX`, v0.53e locked as `RELAXED_OPPOSITE_SIGN_HALT`, v0.53f locked as `WIDENED_BELOW_REACHABILITY_THRESHOLD_UNDER_BASE_METABOLIC_COST_010`, v0.53g locked as `WIDENED_BELOW_REACHABILITY_THRESHOLD_UNDER_COMBINED_SE100_BMC010`, v0.53h locked as `WIDENED_BELOW_REACHABILITY_THRESHOLD_AT_TIME_HORIZON_400`, and v0.53i locked as `WIDENED_BRIDGE_RESCUED_BY_FOOD_NEAR2` is partially generalized along the food-distance axis: the rescue requires reduction beyond 1 column under the tested envelope. This does NOT prove `the minimum is 2 columns universally` or `1 column is irrelevant` — only that this specific 1-column reduction does not lift reachability under the tested envelope: `WIDENED_BELOW_REACHABILITY_THRESHOLD_UNDER_FOOD_NEAR1`."

**Bounded claim:** Under V0_25 × `widened_food_near1` × combined SE100/BMC010 × `n_ticks=400`, the 1-column reduction is INsufficient to lift reachability above the locked 25% threshold. The tested rescue boundary lies between FOOD_NEAR1 (1-column corridor) and FOOD_NEAR2 (0-column corridor).

Sub-verdicts:

| arm | tick-50 | tick-100 | tick-200 | tick-400 |
|---|---|---|---|---|
| A_null_V0_25 | `A_NULL_V025_TICK50_BRIDGE_PRESENT` (anchor) | PRESENT | PRESENT (descriptive) | n/a |
| B_widened_V0_25 | NOT_FOUND | NOT_FOUND | NOT_FOUND (Tier-2 anchor on reachability) | n/a |
| C_widened_food_near1_combined_N400 | NOT_FOUND | NOT_FOUND | NOT_FOUND | **NOT_FOUND** (drives priority-5 verdict via reachability < 0.25) |
| D_widened_food_near2_combined_N400 | PARTIAL | PRESENT | PRESENT | **PRESENT** (Tier-3 positive anchor — matches v0.53i C exactly) |

### Central scientific finding — sharp dose-response on the food-distance axis

C and D differ by **exactly one column** of food-band placement (C: `food_x∈[9,13]`; D: `food_x∈[8,12]`). All other parameters identical. Yet the outcomes are **categorically opposite**:

| arm | corridor_columns | C tick-400 reachability | C tick-400 sub-verdict | C tick-400 living_share |
|---|:-:|:-:|---|:-:|
| B_widened_V0_25 (no body_config / no n_ticks=400; baseline reference at tick-200) | 2 | 0/64 (tick-200) | NOT_FOUND | 0% (extinct) |
| **C_widened_food_near1_combined_N400** | **1** | **0/64** | **NOT_FOUND** | **0%** (full extinction) |
| **D_widened_food_near2_combined_N400** | **0** | **35/64 (~54.7%)** | **PRESENT** | **~36%** |

The 1-column reduction is **indistinguishable from baseline** on every measured outcome: zero food contact at every window (tick-50/100/200/400 all 0/64), zero population alive at tick-400 (matches v0.53h's combined-budget × widened-baseline trajectory exactly). The 2-column reduction in contrast rescues both reachability AND survival.

**The dose-response curve is therefore sharp, not graded.** Within the tested 1-column dose-spacing, the rescue is binary: 0-column corridor rescues; 1-column corridor produces no measurable food access. Bounded claim: this 1-column reduction is INsufficient under the tested envelope; v0.53j does NOT establish where between FOOD_NEAR1 and FOOD_NEAR2 the rescue threshold lies (the next finer dose would require non-integer interventions, e.g., alternative spawn position or hazard thickness modification).

### Tier-3 positive anchor on D — perfect reproduction of v0.53i

D_widened_food_near2_combined_N400 is byte-identical to v0.53i's C arm under matched RNG. The Tier-3 anchor enforces this:

| anchor cell | locked v0.53i value | derived v0.53j D value | drift_abs |
|---|:-:|:-:|:-:|
| reachability_tick400 | 0.546875 (35/64) | 0.546875 | 0.0 (exact categorical) |
| sub-verdict_tick400 | `D_WIDENED_FOOD_NEAR2_TICK400_BRIDGE_PRESENT` | same | 0.0 (exact categorical) |
| label_a / pre400_food_events_count | +1.0357354787853512 | +1.0357354787853512 | **0.0** |
| label_a / pre400_food_energy_acquired | +1.0357354787853512 | +1.0357354787853512 | **0.0** |
| label_a / mean_distance_to_nearest_food_cell_tick400 | +1.061633559034245 | +1.061633559034245 | **0.0** |
| label_b / pre400_food_events_count | +5.3040008005819095 | +5.3040008005819095 | **0.0** |
| label_b / pre400_food_energy_acquired | +5.3040008005819095 | +5.3040008005819095 | **0.0** |
| label_b / mean_distance_to_nearest_food_cell_tick400 | +6.294727858398778 | +6.294727858398778 | **0.0** |

All six paired_d cells reproduce v0.53i's published values **with zero drift** — a perfect deterministic re-execution. This confirms that the v0.53e `body_config` seam, the script-local layout passing, and the n_ticks asymmetric horizon all behave deterministically across slices given matched RNG.

### Reachability across all four windows

| window | A_null_V0_25 | B_widened_V0_25 | C_widened_food_near1_combined_N400 | D_widened_food_near2_combined_N400 | C ≥ 0.25? |
|---|:-:|:-:|:-:|:-:|:-:|
| tick-50 | 1.0000 | 0.0000 | **0.0000** | 0.5313 (34/64) | False (descriptive) |
| tick-100 | 1.0000 | 0.0000 | **0.0000** | 0.5469 (35/64) | False (descriptive) |
| tick-200 | 1.0000 | 0.0000 (Tier-2) | **0.0000** | 0.5469 (35/64) | False (descriptive) |
| tick-400 | n/a | n/a | **0.0000** | **0.5469 (35/64)** (Tier-3) | **False (priority 5)** |

C reachability is **categorical zero across every window** — not "below threshold but non-zero", but zero food contact in any of the 64 C runs at any of the four measured windows. D's reachability stabilises at 35/64 from tick-100 onward (matches v0.53i exactly).

### Population-stability trajectory

| arm | tick-50 living_share | tick-100 | tick-200 | tick-400 |
|---|:-:|:-:|:-:|:-:|
| A_null_V0_25 | 1.0000 | 1.0000 | 1.0000 | n/a |
| B_widened_V0_25 | 1.0000 | 0.5000 | **0.0000** (extinct) | n/a |
| C_widened_food_near1_combined_N400 | 1.0000 | 1.0000 | 0.8750 | **0.0000** (extinct) |
| D_widened_food_near2_combined_N400 | 1.0000 | 1.0000 | 0.9375 | **0.3594** |

C arm goes **fully extinct by tick-400** — same fate as v0.53h's combined-budget × widened-baseline arm (which also went extinct by tick-400 at 0/64 reachability). The 1-column corridor reduction did not rescue survival either; combined-budget × n_ticks=400 × 1-column-corridor reduction is empirically equivalent to combined-budget × n_ticks=400 × widened-baseline. D's ~36% tick-400 living_share (matching v0.53i C's value) confirms the 2-column reduction is the qualitative threshold for both survival AND reachability rescue.

### `GEOMETRY_OPPOSITE_SIGN_HALT` did not activate this slice

C tick-400 sub-verdict = `BRIDGE_NOT_FOUND` (no wrong-sign cells; in fact only 1 of 6 cells has a finite signed_d, at +0.226 below the +0.5 firing threshold). C tick-400 reachability = 0.0 < 0.25. The reachability-gated priority-3 trigger does NOT fire on either condition. Wrong-sign cells under reachability < 0.25 logged descriptively in `wrong_sign_cells_under_reachability_below_threshold` (empty in v0.53j). Framework remains battle-tested via v0.53f only on live data.

### Tier-1 bridge re-anchor — A_null_V0_25 tick-50 reproduces v0.48–v0.53i within 1e-3

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

Locked value 0.0 (0/64); derived 0.0 (0/64). PASS.

### Tier-3 positive anchor — D_widened_food_near2_combined_N400 tick-400

Three sub-conditions, all PASS:
- D tick-400 reachability: 0.546875 == locked 0.546875 (exact)
- D tick-400 sub-verdict: `D_WIDENED_FOOD_NEAR2_TICK400_BRIDGE_PRESENT` == locked
- D tick-400 six paired_d cells: max drift 0.0 (perfect reproduction)

### Corpus re-anchor

A_null_V0_25 arm — all PASS (max drift 0.000312):

| version | derived `a_share_h8` | published | drift |
|---|:-:|:-:|:-:|
| v0.42 | 0.6523 | 0.652 | 0.000312 |
| v0.43R | 0.6743 | — (informational) | — |
| v0.44 | 0.8781 | 0.878 | 0.000091 |
| v0.45 | 0.8182 | 0.818 | 0.000182 |

### What v0.53j can safely claim

- ✓ **All four anchor tiers PASS** within tolerance. Tier-1 max drift 0.000389; Tier-2 exact categorical match; Tier-3 exact categorical match on reachability/sub-verdict + zero drift on all six paired_d cells; corpus a_share_h8 max drift 0.000312.
- ✓ **D arm reproduces v0.53i with zero drift** — the v0.53e seam, script-local layout passing, and n_ticks asymmetric horizon all behave deterministically across slices.
- ✓ **The 1-column post-hazard food distance reduction (FOOD_NEAR1) does NOT lift reachability under the tested envelope.** C reachability is 0/64 at every window; population goes fully extinct by tick-400.
- ✓ **The dose-response on the food-distance axis is sharp at the tested resolution.** 0-column corridor rescues; 1-column corridor produces categorically zero food contact AND full extinction by tick-400. The rescue boundary lies between FOOD_NEAR1 and FOOD_NEAR2.
- ✓ **The 1-column reduction is empirically equivalent to baseline** on every measured outcome under combined-budget × n_ticks=400. The corridor's 1-column shrinkage neither gives founders a higher reachability nor extends survival beyond v0.53h's combined-budget × widened-baseline trajectory.

### What v0.53j cannot claim

- ✗ **"The minimum sufficient reduction is exactly 2 columns universally"** under priority 5. v0.53j tests two doses (1-column and 2-column); whether non-integer interventions (alternative spawn position, hazard thickness, food width) at the 1-column food distance would admit reachability is empirically untested.
- ✗ **"1 column is irrelevant"** under priority 5. The 1-column reduction did slightly extend population trajectory (C tick-200 living_share 0.875 vs B's 0.0 at the same tick — but B is at n_ticks=200 horizon and combined-budget=None, so this comparison is across multiple knobs simultaneously). Within tracked windows, the 1-column reduction is null on reachability and null on tick-400 survival.
- ✗ **"Distance is the sole binding constraint"**. The 1-column reduction failing AND the 2-column reduction succeeding together establishes that distance does matter at the FOOD_NEAR1 → FOOD_NEAR2 transition; whether other knobs (policy, hazard mechanics, sensor reach overlap) co-determine the threshold is not established.
- ✗ **A revised v0.53–v0.53i verdict.** All nine predecessor verdicts stand as historical contracts.
- ✗ **Mechanism behind the sharp dose-response.** C and D differ by 1 column; they yield categorically opposite outcomes. Plausible interpretations (not formally established): C founders' east-ray sensor under `sensor_radius=4` from `spawn_x=1` scans `x∈[2..5]` (3 SAFE + 1 HAZARD) — same as both D and B; sensor reach into the food band at C requires `sensor_radius ≥ 8` whereas at D requires `sensor_radius ≥ 7`; the 1-column shift may push the food-band perception event past the v0.36 sensor_radius distribution's effective tail; alternatively, the policy's east-bias may be sub-threshold to overcome the 1-column corridor under reachability requirements that are met at 0-column.

### Cross-corpus context

| slice | corpus | claim | strength |
|---|---|---|---|
| v0.46 | modern A_null | tick-50 readiness predicts dominance | observational (PRESENT) |
| ... | ... | ... | ... |
| v0.53h | modern A_null | doubling `n_ticks` to 400 under combined envelope does NOT lift reachability AND C goes fully extinct by tick-400 | observational (BELOW_REACHABILITY_THRESHOLD_AT_TIME_HORIZON_400; central finding) |
| v0.53i | modern A_null | reducing post-hazard food distance by 2 columns under combined envelope at `n_ticks=400` lifts reachability to 35/64 AND fires PRESENT under both gating labels at C tick-400 | observational (BRIDGE_RESCUED_BY_FOOD_NEAR2; the v0.53c–v0.53h reachability ceiling is lifted) |
| v0.53j | modern A_null | reducing post-hazard food distance by 1 column under same envelope yields 0/64 reachability AND full extinction by tick-400; D tick-400 anchor reproduces v0.53i exactly; the dose-response is sharp between 1- and 2-column reductions | observational (BELOW_REACHABILITY_THRESHOLD_UNDER_FOOD_NEAR1; rescue boundary localized between FOOD_NEAR1 and FOOD_NEAR2) |

The v0.46→v0.53j stack now reads: ... → v0.53i's 2-column reduction lifts reachability to 35/64 → **v0.53j's 1-column reduction yields 0/64 reachability AND full extinction; the dose-response is sharp at the tested resolution; rescue boundary lies between FOOD_NEAR1 (fails) and FOOD_NEAR2 (rescues).**

### Next-step candidates (open)

The sharp dose-response narrows the rescue-boundary localization to within ±1 column. Further dose-response on integer food-distance reductions (e.g., FOOD_NEAR3 at `food_x∈[7,11]`) would test the larger-reduction direction; FOOD_NEAR0 = baseline (already null per v0.53c–v0.53h). Whether non-distance axes (policy, hazard mechanics, alternative spawn) admit reachability at the 1-column corridor remains an open question.

- **v0.53k candidate — hazard-band traversal mechanics under FOOD_NEAR1.** Vary `hazard_damage` dose or hazard-band thickness on `widened_food_near1` to test whether reduced hazard exposure (independent of distance) admits reachability at the 1-column corridor.
- **v0.53l candidate — policy / hazard-avoidance probe under FOOD_NEAR1.**
- **v0.53m candidate — alternative spawn position under widened_gradient (no food-near).** Tests whether perceptual reach alone, holding distance constant, suffices.
- **v0.53n candidate — Reading-A causal-generalization on `widened_food_near2`** (with v0.53j's positive anchor on D firmly established).
- **v0.54 — joint ablation** (zero-cost AND shuffle).
- **Eventual fresh-stream calibration** on the v0.46–v0.53j conclusion stack.

User has not locked which slice is next.

### CI gate at v0.53j close

```
uv run ruff check .             ok
uv run ruff format --check .    ok (242 files already formatted)
uv run pytest                   1856 passed, 7 skipped (was 1840; +16 v0.53j)
uv run python scripts/core_smoke_test.py                                ok (determinism north star intact; no src/ changes)
uv run python scripts/v0_53j_food_distance_dose_response_audit.py       WIDENED_BELOW_REACHABILITY_THRESHOLD_UNDER_FOOD_NEAR1 (priority 5; geometry-gating did not activate; D Tier-3 anchor reproduces v0.53i with zero drift on all six cells)
```
