# fear_hunger v0.53g — substrate-axis disambiguation: combined founder starting-energy + per-tick metabolic-cost rescue probe on `widened_gradient` × tick-200

**Slice:** v0.53g
**Type:** **first-class observational sweep** with 3-arm tick-200 reducer (no `src/` changes — the v0.53e `body_config` seam carries forward; no intervention; **multi-knob substrate variation** on the C arm — the first slice in the v0.53d→v0.53g substrate-axis stack to vary two `BodyConfig` knobs simultaneously; reuses existing named layouts).
**Predecessors:** v0.46–v0.52b (full predecessor stack), v0.53 (`BRIDGE_PARTIALLY_GENERALIZES`), v0.53b (`WIDENED_BELOW_REACHABILITY_THRESHOLD_AT_TICK_100`), v0.53c (`WIDENED_BELOW_REACHABILITY_THRESHOLD_AT_TICK_200`), v0.53d (`WIDENED_BELOW_REACHABILITY_THRESHOLD_UNDER_RELAXED_INFLUX` — doubled `ambient_influx_rate` was mechanically inert), v0.53e (`RELAXED_OPPOSITE_SIGN_HALT` — `BodyConfig.starting_energy=100` extended survival ~9% at tick-200 but did not lift reachability; methodological lesson logged), v0.53f (`WIDENED_BELOW_REACHABILITY_THRESHOLD_UNDER_BASE_METABOLIC_COST_010` — `BodyConfig.base_metabolic_cost=0.10` extended survival ~16% at tick-200 but did not lift reachability; reachability-gated priority-3 trigger introduced and validated).
**Question being asked (locked):** Does the combined effect of v0.53e's and v0.53f's single-knob founder-facing budget relaxations — applied together on the same C arm — lift `widened_gradient` reachability above the locked 25% threshold at tick-200 AND admit a measurable v0.48 sensor_radius spatial / foraging bridge? Specifically: with `BodyConfig.starting_energy = 100.0` (the maximal legal one-knob value under `max_energy=100`) AND `BodyConfig.base_metabolic_cost = 0.10` (a 60% reduction from V0_25 baseline `0.25`) applied together, with all other V0_25 substrate parameters held identical, does C reachability cross 0.25 at tick-200?

The v0.53d→v0.53f stack established that **both tested single-knob founder-facing budget relaxations failed to lift reachability above 0/64** on `widened_gradient` × V0_25 × N_TICKS=200. v0.53e's `starting_energy=100` extended the survival horizon ~2× (9.4% alive at tick-200 vs B's 0%); v0.53f's `base_metabolic_cost=0.10` extended it ~3× (15.6% alive at tick-200). Both knobs are responsive at the per-arm population level (B and C diverge from tick-100 onward) but neither alone clears the reachability ceiling.

v0.53g tests whether the **combined effect** lifts reachability. Under V0_25 baseline founders consume 0.25 energy per tick from a starting budget of 60 (~240-tick raw runway). Under v0.53e's relaxation (starting_energy=100, V0_25 metabolic cost) raw runway is ~400 ticks. Under v0.53f's relaxation (V0_25 starting energy, base_metabolic_cost=0.10) raw runway is ~600 ticks. **Under v0.53g's combined relaxation (starting_energy=100, base_metabolic_cost=0.10), raw runway is ~1000 ticks** — well beyond the N_TICKS=200 simulation horizon, given no food contact and no other depletion sinks. This is the most aggressive defensible single-arm budget relaxation along the founder-facing axis without raising `max_energy` (which would require a separate slice).

If C_widened_combined_se100_bmc010 reachability ≥ 25% at tick-200 AND tick-200 sub-verdict resolves PRESENT, v0.53c–v0.53f's reachability ceiling on `widened_gradient` × V0_25 is bounded by the combined founder-facing budget envelope — neither single-knob axis alone is sufficient, but the conjunction is. If reachability ≥ 25% AND sub-verdict ∈ {PARTIAL, NOT_FOUND}, the combined relaxation admits measurement but the bridge fails to fully fire. If reachability ≥ 25% AND sub-verdict = OPPOSITE_SIGN_HALT, the reachability-gated priority-3 trigger fires (reachability is now in the "bridge framework meaningful" regime). If reachability < 25% even at the combined founder-facing budget envelope, **the (V0_25 × `widened_gradient`) reachability ceiling is bounded by something other than founder-facing budget at any conservative single- or two-knob envelope** — the candidate space for v0.53h (or later) shifts toward non-budget axes: geometry calibration (corridor width, food placement, hazard-band geometry), policy / hazard-avoidance dynamics, or N_TICKS=200 horizon extension. v0.53g does not claim "geometry fundamental"; the verdict scope is bounded to the tested two-knob envelope.

## Pre-implementation note (2026-05-09, before any reducer code)

The pre-reg's design was confirmed with the user before drafting:

- **3 arms (asymmetric).** A_null_V0_25 (tight_gradient, V0_25 substrate, anchor). B_widened_V0_25 (widened_gradient, V0_25 substrate; predecessor lock from v0.53c–v0.53f). C_widened_combined_se100_bmc010 (widened_gradient, V0_25 substrate **except** `BodyConfig(starting_energy=100.0, base_metabolic_cost=0.10)`). Same 64-tuple corpus.
- **Two BodyConfig knobs, one dose each.** v0.53e's `starting_energy=100` AND v0.53f's `base_metabolic_cost=0.10` applied together on C. Other doses (e.g., `starting_energy=80`, `base_metabolic_cost=0.05`) and other knobs (e.g., `max_energy` co-raised) are deferred to later slices.
- **First multi-knob slice in the v0.53d→v0.53g substrate-axis stack.** v0.53d, v0.53e, v0.53f each varied one knob. v0.53g varies two knobs — the natural conjunctive follow-up given that both single-knob axes failed independently.
- **No `src/` modifications.** v0.53e's `body_config: BodyConfig | None = None` seam in `fear_hunger_chamber.py` carries forward. v0.53g exercises the seam without modification. Test #8 pinning is identical to v0.53e / v0.53f.
- **Reachability-gated priority 3 (carries forward from v0.53f).** Priority 3 fires iff C tick-200 sub-verdict = OPPOSITE_SIGN_HALT AND `c_reachability_tick_200 ≥ 0.25`. Under reachability < 0.25, wrong-sign cells logged descriptively in `wrong_sign_cells_under_reachability_below_threshold` section; rollup falls through to priority 5.
- **Tick-200 verdict gating.** Per-tick observer accumulates through tick-200 (canonical v0.53c–v0.53f three-window template).
- **Tier-2 categorical anchor on B_widened_V0_25 preserved.** Reachability at tick-200 must equal `0/64` exactly.
- **Pool / ecology preserved.** A, B, and C all retain V0_25 baseline `ambient_influx_rate=1.0`, `energy_pool_initial=1500.0`, `food_respawn_cooldown=50`, `child_funding_mode=PARENT_TRANSFER_POOL_GAP`, hazard_damage per (version, hazard) corpus row. Only `body_config` differs on C — and only on two specific BodyConfig fields.
- **Expected behavioral divergence between B and C from tick-0 onward.** Both knobs perturb founder energy dynamics from agent-construction time. The byte-identity-with-B observation that surfaced in v0.53d will not recur. The empirical question is whether the divergence is large enough to cross reachability=0.25.

## Conservation framing — observational, no `src/` changes, two-knob substrate variation on C only

- **No `src/` modifications.** v0.53e's `body_config` seam carries forward; v0.53g exercises it. The five science-core files AND `fear_hunger_chamber.py` all remain byte-identical to their v0.53e-tip values. Test #8 enforces both pinning categories.
- **No modifications to prior reducer or audit scripts.** v0.34's `lineage_replay.py`, ..., v0.53f's reducer remain byte-identical to their merged forms.
- **A_null_V0_25 arm is byte-identical to v0.48–v0.53f A_null path AT TICK-50.** Tier-1 re-anchor enforces this within 1e-3.
- **B_widened_V0_25 arm is byte-identical to v0.53–v0.53f's B_widened arm at every tick 0..200.** Tier-2 categorical anchor enforces `b_widened_v025_reachability_run_share_tick_200 == 0.0`.
- **C_widened_combined_se100_bmc010 differs from B_widened_V0_25 by exactly two BodyConfig knobs.** `starting_energy` (60.0 → 100.0) AND `base_metabolic_cost` (0.25 → 0.10). All other BodyConfig fields preserved at default (`max_energy=100.0`, `starting_health=100.0`, `max_health=100.0`, `sensor_radius_metabolic_cost=0.05`, `effective_sensor_radius_override=None`). All other WorldConfig / ReproductionConfig / ActionConfig parameters identical to V0_25 baseline.
- **No intervention at any level on any arm.** No founder body trait modification post-construction, no override patching, no helper RNG, no shuffle, no clamp, no permutation. The combined-knob change is config-time, not setup-observer-time.

## Corpus (locked, 64 × 3 arms = 192 runs)

Same shape as v0.53–v0.53f:

| version | seeds | hazards | runs per arm | total runs |
|---|---|---|---|---|
| v0.42 | 41..48 | {0, 8} | 16 | 48 |
| v0.43R | 49..56 | {0, 8} | 16 | 48 |
| v0.44 | 57..64 | {0, 8} | 16 | 48 |
| v0.45 | 65..72 | {0, 8} | 16 | 48 |
| **total** | | | | **192** |

V0_25 substrate identical to v0.53–v0.53f on A and B; C identical except `BodyConfig(starting_energy=100.0, base_metabolic_cost=0.10)`. Wall time estimate ~12–25 minutes total.

## Arms (locked, 3 — asymmetric BodyConfig)

### A_null_V0_25

```
ChamberLayout = tight_gradient_layout()
ambient_influx_rate = 1.0  (V0_25 baseline)
energy_pool_initial = 1500.0
food_respawn_cooldown = 50
child_funding_mode = PARENT_TRANSFER_POOL_GAP
hazard_damage = per (version, hazard) corpus row
body_config = None  (default BodyConfig: starting_energy=60.0, base_metabolic_cost=0.25, ...)
FounderSpec(traits_override=None)
```

Byte-identical to v0.48–v0.53f A_null path at every tick 0..200. Used for:
1. **Tier-1 anchor at tick-50** (against v0.48–v0.53f published cells).
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
FounderSpec(traits_override=None)
```

Byte-identical to v0.53–v0.53f's B_widened arm at every tick 0..200.

### C_widened_combined_se100_bmc010

```
ChamberLayout = widened_gradient_layout()
ambient_influx_rate = 1.0  (V0_25 baseline)
energy_pool_initial = 1500.0  (V0_25 baseline)
food_respawn_cooldown = 50  (V0_25 baseline)
child_funding_mode = PARENT_TRANSFER_POOL_GAP  (V0_25 baseline)
hazard_damage = per (version, hazard) corpus row  (V0_25 baseline)
body_config = BodyConfig(starting_energy=100.0, base_metabolic_cost=0.10)
  (RELAXED — TWO knobs:
   starting_energy raised from V0_25 baseline 60.0 to 100.0
                   (the maximal legal one-knob value under max_energy=100.0)
   base_metabolic_cost lowered from V0_25 baseline 0.25 to 0.10
                       (a 60% reduction)
   All other BodyConfig fields default,
   including max_energy=100.0, sensor_radius_metabolic_cost=0.05)
FounderSpec(traits_override=None)
```

Differs from B_widened_V0_25 by exactly two knobs: `BodyConfig.starting_energy` (60.0 → 100.0) AND `BodyConfig.base_metabolic_cost` (0.25 → 0.10). All other BodyConfig fields preserved at default. **The primary arm of v0.53g**: the verdict gates on C's tick-200 reachability and tick-200 sub-verdict.

## Labels (locked, two — with three Label B variants; identical to v0.48–v0.53f)

### Label A — `high_sensor_radius_lineage`

Trait-resolved (`int(founder.body.traits.sensor_radius)`); tiebreak `min(lineage_id)`.

### Label B — three variants computed in parallel

- **`high_tick50_readiness_fraction_lineage`** — Tier-1 anchor against v0.48–v0.53f.
- **`high_tick100_readiness_fraction_lineage`** — descriptive (NOT gating).
- **`high_tick200_readiness_fraction_lineage`** — verdict-gating.

## Primary observables (locked, 3, computed at three windows)

| # | name pattern | windows | expected sign |
|---|---|---|:-:|
| 1 | `pre{N}_food_events_count` | N ∈ {50, 100, 200} | + |
| 2 | `pre{N}_food_energy_acquired` | N ∈ {50, 100, 200} | + |
| 3 | `mean_distance_to_nearest_food_cell_tick{N}` | N ∈ {50, 100, 200} | − |

Definitions / aggregation rules / NaN handling: copy-local from v0.48–v0.53f.

## Effect-size rule (locked, sign-aware, identical to v0.48–v0.53f)

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

c_widened_combined_se100_bmc010_reachability_run_share_tick_200 =
    fraction of C_widened_combined_se100_bmc010 runs where at least one
    founder lineage has pre200_food_events_count > 0
```

Domain: 64 runs per arm. Threshold: **`B_REACHABILITY_THRESHOLD = 0.25`** (preserved from v0.53b–v0.53f).

The B_widened_V0_25 metric is the Tier-2 categorical predecessor anchor (must equal `0.0` exactly). The C_widened_combined_se100_bmc010 metric is the verdict-gating reachability AND the priority-3 reachability gate.

## Population-stability and degenerate-label descriptive metrics (locked, pre-data, per arm × window)

Identical structure to v0.53c–v0.53f.

## Per-arm sub-verdicts (locked, 4-way each — UNCHANGED from v0.53d / v0.53e / v0.53f)

| condition | A_null_V0_25 (tick-200) | B_widened_V0_25 (tick-200) | C_widened_combined_se100_bmc010 (tick-200) |
|---|---|---|---|
| both labels clear ≥ 2/3 of the three locked cells, with NaN treated as non-firing, 0 wrong-sign | `A_NULL_V025_TICK200_BRIDGE_PRESENT` | `B_WIDENED_V025_TICK200_BRIDGE_PRESENT` | `C_COMBINED_SE100_BMC010_TICK200_BRIDGE_PRESENT` |
| exactly one label clears ≥ 2/3 of the three locked cells, with NaN treated as non-firing, 0 wrong-sign | `A_NULL_V025_TICK200_BRIDGE_PARTIAL` | `B_WIDENED_V025_TICK200_BRIDGE_PARTIAL` | `C_COMBINED_SE100_BMC010_TICK200_BRIDGE_PARTIAL` |
| neither label clears ≥ 2/3 of the three locked cells, with NaN treated as non-firing, 0 wrong-sign | `A_NULL_V025_TICK200_BRIDGE_NOT_FOUND` | `B_WIDENED_V025_TICK200_BRIDGE_NOT_FOUND` | `C_COMBINED_SE100_BMC010_TICK200_BRIDGE_NOT_FOUND` |
| any primary signed_d ≤ −0.5 under either label | `A_NULL_V025_TICK200_OPPOSITE_SIGN_HALT` | `B_WIDENED_V025_TICK200_OPPOSITE_SIGN_HALT` | `C_COMBINED_SE100_BMC010_TICK200_OPPOSITE_SIGN_HALT` |

**Strict NaN-treated-as-non-firing rule preserved.**

## Slice rollup verdicts (locked, 6 outcomes, priority-ordered — PRIORITY 3 IS REACHABILITY-GATED, carrying forward from v0.53f)

Priority order (first-matching wins). The non-halt outcomes (priorities 4–6) gate **only on C_widened_combined_se100_bmc010**.

1. `CORPUS_REDERIVE_DRIFT_HALT`
2. `ANCHOR_REPLICATION_HALT`
3. `RELAXED_OPPOSITE_SIGN_HALT` (**reachability-gated** — fires iff C sub-verdict = OPPOSITE_SIGN_HALT AND `c_reachability_tick_200 ≥ 0.25`)
4. `WIDENED_BRIDGE_RESCUED_BY_COMBINED_SE100_BMC010`
5. `WIDENED_BELOW_REACHABILITY_THRESHOLD_UNDER_COMBINED_SE100_BMC010`
6. `WIDENED_BRIDGE_PARTIALLY_RESCUED_BY_COMBINED_SE100_BMC010`

### Halt conditions

| priority | rollup verdict | trigger | locked phrase (verbatim) |
|---|---|---|---|
| 1 | `CORPUS_REDERIVE_DRIFT_HALT` | A_null_V0_25 arm `a_share_h8` for any of v0.42 / v0.44 / v0.45 drifts > 1e-3 from the published reference | "Halt: A_null_V0_25 re-anchor drifted from the published Results value for {version}; v0.53g's deterministic re-execution of the V0_25 corpus does not reproduce the published metric within 1e-3." |
| 2 | `ANCHOR_REPLICATION_HALT` | (a) A_null_V0_25 tick-50 signed_d for any of the six v0.48–v0.53f cells drifts > 1e-3 from the published value, OR (b) A_null_V0_25 tick-50 sub-verdict ≠ PRESENT, OR (c) `b_widened_v025_reachability_run_share_tick_200` ≠ `0.0` | "Halt: v0.53g's A_null_V0_25 arm does not reproduce v0.48–v0.53f's tick-50 spatial bridge, OR v0.53g's B_widened_V0_25 arm does not reproduce v0.53c–v0.53f's `0/64` reachability lock at tick-200. v0.53g cannot interpret the C_widened_combined_se100_bmc010 cells without an established baseline on the V0_25 substrate." |
| 3 | `RELAXED_OPPOSITE_SIGN_HALT` (**reachability-gated**) | C_widened_combined_se100_bmc010 tick-200 sub-verdict = `C_COMBINED_SE100_BMC010_TICK200_OPPOSITE_SIGN_HALT` (any wrong-sign cell) **AND** `c_widened_combined_se100_bmc010_reachability_run_share_tick_200 ≥ 0.25` | "Halt: a v0.53g C_widened_combined_se100_bmc010 tick-200 spatial / foraging primary fires in the WRONG direction under a gating label, AND C reachability at tick-200 clears the locked 25% threshold (so the bridge framework is meaningful at this measurement). The combined founder-facing budget relaxation (`BodyConfig.starting_energy = 100.0` AND `BodyConfig.base_metabolic_cost = 0.10`) on the `widened_gradient` layout surfaces a regime where the locked expected signs do not hold under measurable food access. The reachability-gated trigger preserves v0.53e's locked sign discipline while excluding the v0.53e-style measurement-edge case (wrong-sign at reachability=0)." |

### Tier-1 (priority 2.a) re-anchor — A_null_V0_25 tick-50 cells

Identical six cells to v0.48–v0.53f:

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

Locked from v0.53c–v0.53f.

### Outcome conditions (only consulted if no halt fires)

| priority | rollup verdict | trigger | locked phrase (verbatim) |
|---|---|---|---|
| 4 | `WIDENED_BRIDGE_RESCUED_BY_COMBINED_SE100_BMC010` | `c_widened_combined_se100_bmc010_reachability_run_share_tick_200 ≥ 0.25` AND C tick-200 sub-verdict = `C_COMBINED_SE100_BMC010_TICK200_BRIDGE_PRESENT` | "On the modern A_null corpus with the V0_25 substrate held constant except for the combined founder-facing budget relaxation `BodyConfig(starting_energy=100.0, base_metabolic_cost=0.10)` on `widened_gradient` (starting_energy raised from V0_25 baseline 60.0 to the maximal legal 100.0 AND base_metabolic_cost lowered from V0_25 baseline 0.25 to 0.10, a 60% reduction), the v0.48 sensor_radius spatial / foraging bridge fires PRESENT under the locked +0.5 paired_d threshold at tick-200. The geometry/substrate cell that v0.53c locked as `WIDENED_BELOW_REACHABILITY_THRESHOLD_AT_TICK_200`, v0.53d locked as `WIDENED_BELOW_REACHABILITY_THRESHOLD_UNDER_RELAXED_INFLUX`, v0.53e locked as `RELAXED_OPPOSITE_SIGN_HALT`, and v0.53f locked as `WIDENED_BELOW_REACHABILITY_THRESHOLD_UNDER_BASE_METABOLIC_COST_010` admits a measurable bridge under the combined founder-facing budget envelope: B_widened_V0_25 reachability remains `0/64` at tick-200 (predecessor lock holds), C_widened_combined_se100_bmc010 reachability clears the locked 25% threshold, and ≥ 2/3 spatial / foraging primaries fire PRESENT under both gating labels. Neither single-knob axis alone was sufficient (v0.53e: `starting_energy=100` extended survival ~9% but reachability=0; v0.53f: `base_metabolic_cost=0.10` extended survival ~16% but reachability=0); the conjunction lifts the reachability ceiling. The (V0_25 × `widened_gradient`) cell is bounded by the combined founder-facing budget envelope, not by the geometry alone: `WIDENED_BRIDGE_RESCUED_BY_COMBINED_SE100_BMC010`." |
| 5 | `WIDENED_BELOW_REACHABILITY_THRESHOLD_UNDER_COMBINED_SE100_BMC010` | `c_widened_combined_se100_bmc010_reachability_run_share_tick_200 < 0.25` | "On the modern A_null corpus with the V0_25 substrate held constant except for the combined founder-facing budget relaxation `BodyConfig(starting_energy=100.0, base_metabolic_cost=0.10)` on `widened_gradient`, fewer than 25% of C_widened_combined_se100_bmc010 runs have any founder lineage with pre200 food events. C_widened_combined_se100_bmc010's reachability is below the locked 25% threshold at tick-200; the geometry/substrate cell that v0.53c locked as `WIDENED_BELOW_REACHABILITY_THRESHOLD_AT_TICK_200`, v0.53d locked as `WIDENED_BELOW_REACHABILITY_THRESHOLD_UNDER_RELAXED_INFLUX`, v0.53e locked as `RELAXED_OPPOSITE_SIGN_HALT`, and v0.53f locked as `WIDENED_BELOW_REACHABILITY_THRESHOLD_UNDER_BASE_METABOLIC_COST_010` remains below the reachability threshold under the combined founder-facing budget envelope. The bridge is not rescued by `BodyConfig(starting_energy=100.0, base_metabolic_cost=0.10)` under V0_25 × `widened_gradient` × N_TICKS=200; the (V0_25 × `widened_gradient`) reachability ceiling is not lifted by any conservative single- or two-knob founder-facing budget envelope tested in the v0.53d→v0.53g stack. v0.53h (or later) candidates shift toward non-budget axes: geometry calibration (corridor width, food placement, hazard-band geometry), policy / hazard-avoidance dynamics, or N_TICKS=200 horizon extension: `WIDENED_BELOW_REACHABILITY_THRESHOLD_UNDER_COMBINED_SE100_BMC010`." |
| 6 | `WIDENED_BRIDGE_PARTIALLY_RESCUED_BY_COMBINED_SE100_BMC010` | `c_widened_combined_se100_bmc010_reachability_run_share_tick_200 ≥ 0.25` AND C tick-200 sub-verdict ∈ {`C_COMBINED_SE100_BMC010_TICK200_BRIDGE_PARTIAL`, `C_COMBINED_SE100_BMC010_TICK200_BRIDGE_NOT_FOUND`} | "On the modern A_null corpus with the V0_25 substrate held constant except for the combined founder-facing budget relaxation `BodyConfig(starting_energy=100.0, base_metabolic_cost=0.10)` on `widened_gradient`, C_widened_combined_se100_bmc010's reachability clears the locked 25% threshold at tick-200 but the v0.48 sensor_radius spatial / foraging bridge does not fully fire PRESENT — fewer than 2/3 primaries fire across both gating labels at tick-200 under the strict NaN rule. The geometry/substrate cell that v0.53c locked as `WIDENED_BELOW_REACHABILITY_THRESHOLD_AT_TICK_200`, v0.53d locked as `WIDENED_BELOW_REACHABILITY_THRESHOLD_UNDER_RELAXED_INFLUX`, v0.53e locked as `RELAXED_OPPOSITE_SIGN_HALT`, and v0.53f locked as `WIDENED_BELOW_REACHABILITY_THRESHOLD_UNDER_BASE_METABOLIC_COST_010` is partially rescued under the combined founder-facing budget envelope: reachability becomes measurable but the bridge does not fully replicate. Layout-specific partial-rescue logged in Results: `WIDENED_BRIDGE_PARTIALLY_RESCUED_BY_COMBINED_SE100_BMC010`." |

The 3 non-halt outcomes form a total partition of (C reachability ≥ 0.25, C sub-verdict ∈ {PRESENT, PARTIAL, NOT_FOUND, OPPOSITE_SIGN_HALT}) ∪ (C reachability < 0.25). Under the reachability-gated priority-3 trigger:
- **C reachability ≥ 0.25 AND C sub-verdict = OPPOSITE_SIGN_HALT** → priority 3 fires (halt).
- **C reachability ≥ 0.25 AND C sub-verdict = PRESENT** → priority 4 fires.
- **C reachability ≥ 0.25 AND C sub-verdict ∈ {PARTIAL, NOT_FOUND}** → priority 6 fires.
- **C reachability < 0.25** → priority 5 fires (regardless of C sub-verdict, including OPPOSITE_SIGN_HALT — wrong-sign cells logged descriptively but no halt).

Test #16 enforces the partition exhaustively.

## Cautious framing (per CLAUDE.md)

- "**Bridge rescued by combined founder-facing budget envelope**", "**bridge is not rescued by `BodyConfig(starting_energy=100.0, base_metabolic_cost=0.10)` under V0_25 × widened_gradient × N_TICKS=200**", "**reachability ceiling is bounded by something other than founder-facing budget at any conservative single- or two-knob envelope tested in the v0.53d→v0.53g stack**" — NOT "**proves**", "**causes**", "**rules out**", or "**geometry-fundamental**".
- "**Tested combined envelope**" specifically means `BodyConfig(starting_energy=100.0, base_metabolic_cost=0.10)` at `N_TICKS=200`. v0.53g does NOT establish behavior at intermediate doses, behavior with additional knobs co-raised (e.g., `max_energy`), or behavior under N_TICKS > 200; those require separate slices.
- v0.53g explicitly does not establish: cross-layout generalization beyond the three v0.53 layouts, mechanism for any rescue or non-rescue outcome, generalization to non-V0_25 substrates beyond the founder-facing budget axes, behavior at `n_ticks > 200`, causal contribution per layout (Reading-A causal-generalization slice remains the deferred candidate).

## What v0.53g cannot establish (logged here pre-data, not retrofittable)

- ✗ **"`widened_gradient` is geometry-fundamental"** if priority 5 fires. v0.53g tests V0_25 substrate × `BodyConfig(starting_energy=100.0, base_metabolic_cost=0.10)` × N_TICKS=200 only. Stronger doses, additional knobs (e.g., `max_energy` co-raised), or N_TICKS extension may admit reachability. Geometry calibration (corridor width, food placement, hazard-band) and policy / hazard-avoidance dynamics also remain untested. v0.53h (or later) candidates open.
- ✗ **"Founder-facing budget axes are exhausted."** v0.53g tested one combined dose. Stronger doses (e.g., `starting_energy + max_energy` co-raised to 120; `base_metabolic_cost = 0.05`) or three-knob co-variations remain untested.
- ✗ **A revised v0.53–v0.53f verdict.** All six stand as historical contracts.
- ✗ **Mechanism behind any rescue or non-rescue outcome.** Population dynamics under V0_25 × `widened_gradient` × `BodyConfig(se100, bmc010)` are descriptively logged; no mechanism is formally established.
- ✗ **Generalization beyond the tested arms.** Verdict scope is bounded to (`tight_gradient` × V0_25, `widened_gradient` × V0_25, `widened_gradient` × V0_25 with `BodyConfig(se100, bmc010)`) at `N_TICKS=200`.

## Open framing (NOT in v0.53g primary)

- **If priority 4 fires** (combined relaxation rescues the bridge): the natural follow-ups become Reading-A causal-generalization on `widened_gradient` under the combined envelope, dose-response within the founder-facing budget axes, and substrate cross-corpus calibration.
- **If priority 5 fires** (combined relaxation insufficient): the candidate space shifts away from founder-facing budget axes:
  - **v0.53h candidate — geometry calibration probe.** Vary corridor width, food placement, hazard-band placement on `widened_gradient`. May require new layout(s) and possibly src/ change to expose layout parameters.
  - **v0.53i candidate — policy / hazard-avoidance probe.** Vary `hazard_avoidance_weight` or other policy knobs on `widened_gradient` under V0_25 substrate.
  - **v0.53j candidate — N_TICKS extension probe.** Test N_TICKS=400 or higher under V0_25 substrate (likely requires src/ change to expose N_TICKS override).
  - **v0.53k candidate — three-knob co-variation.** Add `max_energy=200` (or similar) to v0.53g's two-knob envelope; test whether further headroom lifts reachability.
- **v0.53l (or later) — investigate the C_food_ladder Label B degradation trajectory.** Per-tick-window paired_d trajectory probe.
- **v0.53m (or later) — Reading-A causal-generalization slice on layouts admitting the bridge.**
- **v0.54 — joint ablation** (zero-cost AND shuffle).
- **Eventual fresh-stream calibration** on the v0.46–v0.53g conclusion stack.

## Re-anchor (locked — Tier-1 and corpus only at tick-50)

| version | published `a_share_h8` |
|---|---|
| v0.42 | 0.652 |
| v0.43R | NOT PUBLISHED (informational-only) |
| v0.44 | 0.878 |
| v0.45 | 0.818 |

## Outputs (locked)

```
runs/v0.53g-substrate-axis-combined-se100-bmc010/per_run_per_lineage_v053g.csv
  columns: arm, layout_name, body_starting_energy, body_base_metabolic_cost,
           version, seed, hazard, run_id, lineage_id,
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

runs/v0.53g-substrate-axis-combined-se100-bmc010/audit_summary.csv
  (includes the wrong_sign_cells_under_reachability_below_threshold section
   carried forward from v0.53f)

runs/v0.53g-substrate-axis-combined-se100-bmc010/audit_log.txt
```

## Implementation plan (locked)

1. **No `src/` changes.** v0.53e's `body_config: BodyConfig | None = None` seam in `run_chamber()` carries forward; v0.53g passes `body_config=BodyConfig(starting_energy=100.0, base_metabolic_cost=0.10)` for the C arm.
2. Fresh script `scripts/v0_53g_substrate_axis_combined_se100_bmc010_audit.py`. CLI: `uv run python scripts/v0_53g_substrate_axis_combined_se100_bmc010_audit.py [--out-dir runs/v0.53g-substrate-axis-combined-se100-bmc010]`.
3. Per (version, seed, hazard) tuple, run **3 arms**. A and B pass `body_config=None`; C passes `body_config=BodyConfig(starting_energy=100.0, base_metabolic_cost=0.10)`.
4. Setup_observer order (matches v0.53c–v0.53f merged implementation): (a) capture v0.53g founder audit table including `body.energy` AND `body_config.starting_energy` AND `body_config.base_metabolic_cost` at tick 0 (verifies BOTH knobs propagated correctly), (b) wire event listeners, (c) read back `model.world.width` and assert layout match per-arm, (d) capture tick-0 snapshot.
5. Per-tick observer accumulates `pre50_*` / `pre100_*` / `pre200_*` rollups in parallel.
6. Use the relaxed contiguous-prefix tick-records invariant from v0.53b–v0.53f.
7. Aggregate per-lineage primaries at all three windows. Compute Label A and three Label B variants.
8. Compute paired_d per (arm, gating-label, observable, window) cell.
9. Compute per-arm reachability_run_share at all three windows.
10. Compute per-arm population-stability metrics.
11. **Tier-1 bridge re-anchor** (priority 2.a / 2.b): A_null_V0_25 arm's six tick-50 cells vs v0.48–v0.53f published; halt if drift > 1e-3 OR if A_null_V0_25 tick-50 sub-verdict ≠ PRESENT.
12. **Tier-2 categorical anchor** (priority 2.c): `b_widened_v025_reachability_run_share_tick_200 == 0.0` exactly.
13. **Corpus re-anchor** (priority 1): A_null_V0_25 arm only; halt if `a_share_h8` for v0.42 / v0.44 / v0.45 drifts > 1e-3.
14. **Reachability-gated relaxed opposite-sign halt** (priority 3, carries forward from v0.53f): scan all C tick-200 gating-label cells; if any signed_d ≤ −0.5 AND `c_reachability_tick_200 ≥ 0.25` → halt loud. Otherwise: log descriptively in `audit_summary.csv` under `wrong_sign_cells_under_reachability_below_threshold`; do NOT halt. Fall through to priority 4/5/6 evaluation.
15. Compute slice rollup verdict per the locked priority + (C reachability tick-200, C sub-verdict tick-200) decision matrix; print + write the locked phrase verbatim.

The reducer is fully self-contained: it reads no `runs/` artifacts. Wall time estimate ~12–25 minutes for 192 runs.

## Test list (locked, 16 tests; extends v0.53f's pattern with two-knob seam-verification in test #5)

`tests/test_v0_53g_substrate_axis_combined_se100_bmc010_audit.py`:

1. **`test_paired_d_function_reproduces_hand_computed_signed_d_on_fixture_and_tier1_constants_match_v048_published_values`** *(re-anchor test, two-part)*.
2. **`test_a_null_v025_corpus_a_share_h8_re_anchors_v042_v044_v045`** — drift halt fires if any drift > 1e-3.
3. `test_arm_a_null_v025_uses_tight_gradient_layout_and_default_body_config` — chamber driver receives `tight_gradient_layout()` AND `body_config=None`; layout invariant assert.
4. `test_arm_b_widened_v025_uses_widened_gradient_layout_and_default_body_config` — chamber driver receives `widened_gradient_layout()` AND `body_config=None`; layout invariant assert.
5. **`test_arm_c_widened_combined_se100_bmc010_seam_differentiates_b_and_c_two_body_config_knobs_at_tick_0`** *(cross-arm contrast — verifies BOTH knobs of the `body_config` seam took effect at config-time founder construction)* — for the same (version, seed, hazard) tuple under matched RNG streams, assert:
   - **B founder body fields at tick-0**: `body.energy == 60.0`, `body_config.starting_energy == 60.0`, `body_config.base_metabolic_cost == 0.25` (V0_25 baseline from default `BodyConfig()` fallback).
   - **C founder body fields at tick-0**: `body.energy == 100.0` (overridden via `starting_energy=100.0`), `body_config.starting_energy == 100.0`, `body_config.base_metabolic_cost == 0.10` (overridden via `base_metabolic_cost=0.10`).
   - Both arms use `widened_gradient_layout()`; the configured difference is `body_config` (TWO knobs differ).
   - For C, explicitly assert that no other `BodyConfig` field differs from default (`max_energy=100.0`, `starting_health=100.0`, `max_health=100.0`, `sensor_radius_metabolic_cost=0.05`, `effective_sensor_radius_override=None`) AND no other WorldConfig knob differs from V0_25 baseline.
   - Founder body fields are read (not written) via `setup_observer` snapshot at tick-0.
6. **`test_founder_traits_byte_identical_across_arms_for_same_seed`**.
7. **`test_founder_positions_byte_identical_across_arms_for_same_seed`**.
8. **`test_no_src_modifications_compared_to_v0_53e_tip`** *(two-part src/ pinning test, IDENTICAL to v0.53e / v0.53f's test #8)*:
   Part A: SHA-256 of five science-core files match v0.52b-tip values exactly. Failure message verbatim: `"v0.53g is pre-registered to leave the science-core five files byte-identical to v0.52b-tip; update the pre-reg before changing src/core or src/experiments/layouts."`
   Part B: SHA-256 of `src/hedonism_harness/experiments/fear_hunger_chamber.py` matches v0.53e-tip value `62d134c5d82b031a6fd2b7bbdf0412eb8362199c7bf60a59836cfca9134e2b6d`. Failure message verbatim: `"v0.53g is pre-registered to leave the chamber driver byte-identical to its v0.53e-tip hash; update the pre-reg before re-touching the chamber driver."`
9. `test_label_a_high_sensor_radius_lineage_picks_correct_lineage`.
10. **`test_label_b_three_variants_three_tier_tiebreak_at_each_window`**.
11. **`test_pre200_window_strictly_extends_pre100_and_pre50_windows`** — synthetic events at ticks 10/30/60/90/130/180/200; assert counts 2/4/7.
12. **`test_subverdict_present_requires_two_thirds_firing_cells_with_nan_treated_as_non_firing_strict`**.
13. **`test_priority_3_relaxed_opposite_sign_halt_is_reachability_gated`** *(carries forward from v0.53f — exercises both branches)*:
    - **Branch A**: synthetic C tick-200 sub-verdict = OPPOSITE_SIGN_HALT AND `c_reachability_tick_200 = 0.30` → priority 3 fires; rollup verdict = `RELAXED_OPPOSITE_SIGN_HALT`.
    - **Branch B**: synthetic C tick-200 sub-verdict = OPPOSITE_SIGN_HALT AND `c_reachability_tick_200 = 0.20` → priority 3 does NOT fire; rollup = `WIDENED_BELOW_REACHABILITY_THRESHOLD_UNDER_COMBINED_SE100_BMC010` (priority 5); wrong-sign cell recorded in `wrong_sign_cells_under_reachability_below_threshold`.
    - **Branch C**: synthetic C tick-200 sub-verdict = PRESENT AND `c_reachability_tick_200 = 0.30` → priority 4 fires.
14. **`test_b_widened_v025_categorical_anchor_at_tick_200`** — synthetic B reachability=0.0 → priority 2 does NOT fire on this leg. Synthetic B reachability=1/64=0.015625 → priority 2 ANCHOR_REPLICATION_HALT fires.
15. **`test_c_widened_combined_se100_bmc010_reachability_threshold_partition_at_tick_200`** — synthetic C reachability 0.20 / 0.30 × {PRESENT, PARTIAL, NOT_FOUND} → priorities 4/5/6 fire correctly.
16. **`test_rollup_locked_phrases_fire_verbatim_and_priority_cascade_partition_total`** — synthetic each priority-3/4/5/6 outcome → assert locked phrase contains diagnostic substring verbatim:
    - Priority 3 (RELAXED_OPPOSITE_SIGN_HALT, reachability-gated): `"AND C reachability at tick-200 clears the locked 25% threshold (so the bridge framework is meaningful at this measurement)"` AND `"The reachability-gated trigger preserves v0.53e's locked sign discipline while excluding the v0.53e-style measurement-edge case (wrong-sign at reachability=0)"`.
    - Priority 4 RESCUED: `"the conjunction lifts the reachability ceiling"` AND `"The (V0_25 × \`widened_gradient\`) cell is bounded by the combined founder-facing budget envelope, not by the geometry alone"` AND substring references to v0.53c, v0.53d, v0.53e, v0.53f verdict names.
    - Priority 5 BELOW_THRESHOLD: `"The bridge is not rescued by \`BodyConfig(starting_energy=100.0, base_metabolic_cost=0.10)\` under V0_25 × \`widened_gradient\` × N_TICKS=200"` AND `"the (V0_25 × \`widened_gradient\`) reachability ceiling is not lifted by any conservative single- or two-knob founder-facing budget envelope tested in the v0.53d→v0.53g stack"` AND `"v0.53h (or later) candidates shift toward non-budget axes"` AND substring references to v0.53c, v0.53d, v0.53e, v0.53f verdict names.
    - Priority 6 PARTIALLY_RESCUED: `"reachability becomes measurable but the bridge does not fully replicate"` AND substring references to v0.53c, v0.53d, v0.53e, v0.53f verdict names.
    Synthesize halt cascade (priorities 1 / 2.a / 2.b / 2.c / 3); assert priority order. Exhaustively iterate (C reachability ≥ 0.25, C sub-verdict ∈ {PRESENT, PARTIAL, NOT_FOUND, OPPOSITE_SIGN_HALT}) ∪ (C reachability < 0.25, any sub-verdict); assert unique outcome per cell.

## Watch-outs (for future-Chronus)

- **No `src/` changes.** v0.53e's seam carries forward; v0.53g exercises it with TWO BodyConfig overrides instead of one. Test #8 pins both science-core five files (at v0.52b-tip) AND chamber driver (at v0.53e-tip) byte-identically.
- **First multi-knob slice in the substrate-axis stack.** v0.53g varies two BodyConfig knobs simultaneously. Test #5 verifies BOTH knobs propagated correctly to founder construction.
- **Reachability-gated priority 3 carries forward from v0.53f.** Wrong-sign cells under C reachability < 0.25 are logged descriptively and do NOT fire a halt.
- **Per-arm sub-verdict structure unchanged (4-way).**
- **Tier-2 categorical anchor on B_widened_V0_25 is integer-categorical.** Compare to `0.0` exactly.
- **Pool / ecology preserved.** Only `body_config` differs on C.
- **B and C are expected to diverge from tick-0 onward**, more strongly than v0.53e or v0.53f individually because TWO knobs perturb founder energy dynamics.
- **C extinction trajectory is the open question** — and the question whether C reaches food. The combined ~4-5× V0_25 baseline survival horizon should be enough for founders to traverse the 9-cell corridor IF the bottleneck is energy budget. If it isn't, priority 5 fires and the candidate space narrows significantly.
- **Treat the "raw runway ~1000 ticks" estimate as a budget-envelope heuristic, not a prediction.** The actual sim has sensing, movement, hazards, reproduction logic, and possible other event dynamics that perturb founder energy beyond the constant-depletion-rate idealization. Results should not lean on the runway estimate as a quantitative prediction; it stands only as an intuition that the combined two-knob envelope is the most aggressive defensible single-arm budget relaxation along the founder-facing axis without raising `max_energy`.
- **Locked phrase discipline** verbatim where verdicts fire. The priority-4 / -5 / -6 phrases all explicitly reference v0.53c / v0.53d / v0.53e / v0.53f by name — the predecessor stack is now four slices long.
- **No `geometry-fundamental` claims under priority 5.** The locked phrase explicitly bounds the verdict to the tested two-knob envelope and names v0.53h+ candidates (geometry calibration, policy probes, N_TICKS extension, three-knob co-variation) as the open-frame follow-ups.
- **Methodological lesson from v0.53e applies** — the reachability-gated priority-3 trigger is now a battle-tested pattern.
- **Determinism north star** ([[scripts/core_smoke_test.py]]) must continue to pass. v0.53g makes no `src/` changes.

## Files this slice will create / modify

- `docs/experiments/fear_hunger_v0.53g.md` (this file; Results section appended after reducer run)
- `scripts/v0_53g_substrate_axis_combined_se100_bmc010_audit.py` (new)
- `tests/test_v0_53g_substrate_axis_combined_se100_bmc010_audit.py` (new, 16 tests)

No `src/` modifications. No prior reducer / audit / test / pre-reg files modified.

## Results

**Status:** reducer executed 2026-05-09 against the 192-run corpus (3 arms × 64 (version, seed, hazard) tuples). Wall time well under the 12–25 minute estimate. **Tier-1 bridge re-anchor PASSES at tick-50** (A_null_V0_25 reproduces v0.48–v0.53f's six published signed_d cells within max drift 0.0004 ≪ 1e-3). **Tier-2 categorical anchor PASSES** (B_widened_V0_25 reachability = exactly 0/64 at tick-200, matching v0.53c–v0.53f's lock). Corpus re-anchor (`a_share_h8`) max drift 0.0003 on v0.42. **The reducer landed cleanly on priority 5** — C reachability remained `0/64` at tick-200 even under the most aggressive defensible single-arm budget envelope. **Reachability-gating did not activate** because C had no wrong-sign cells (C tick-200 sub-verdict = `BRIDGE_NOT_FOUND`, not `OPPOSITE_SIGN_HALT`); the framework remains battle-tested via v0.53f only.

### Rollup verdict — `WIDENED_BELOW_REACHABILITY_THRESHOLD_UNDER_COMBINED_SE100_BMC010` fires

> **Locked phrase fires verbatim:** "On the modern A_null corpus with the V0_25 substrate held constant except for the combined founder-facing budget relaxation `BodyConfig(starting_energy=100.0, base_metabolic_cost=0.10)` on `widened_gradient`, fewer than 25% of C_widened_combined_se100_bmc010 runs have any founder lineage with pre200 food events. C_widened_combined_se100_bmc010's reachability is below the locked 25% threshold at tick-200; the geometry/substrate cell that v0.53c locked as `WIDENED_BELOW_REACHABILITY_THRESHOLD_AT_TICK_200`, v0.53d locked as `WIDENED_BELOW_REACHABILITY_THRESHOLD_UNDER_RELAXED_INFLUX`, v0.53e locked as `RELAXED_OPPOSITE_SIGN_HALT`, and v0.53f locked as `WIDENED_BELOW_REACHABILITY_THRESHOLD_UNDER_BASE_METABOLIC_COST_010` remains below the reachability threshold under the combined founder-facing budget envelope. The bridge is not rescued by `BodyConfig(starting_energy=100.0, base_metabolic_cost=0.10)` under V0_25 × `widened_gradient` × N_TICKS=200; the (V0_25 × `widened_gradient`) reachability ceiling is not lifted by any conservative single- or two-knob founder-facing budget envelope tested in the v0.53d→v0.53g stack. v0.53h (or later) candidates shift toward non-budget axes: geometry calibration (corridor width, food placement, hazard-band geometry), policy / hazard-avoidance dynamics, or N_TICKS=200 horizon extension: `WIDENED_BELOW_REACHABILITY_THRESHOLD_UNDER_COMBINED_SE100_BMC010`."

**Bounded claim:** Under V0_25 × `widened_gradient` × N_TICKS=200, reachability is not restored by the tested conservative single- or two-knob founder-facing budget relaxations.

Sub-verdicts:

| arm | tick-50 (anchor) | tick-100 (descriptive) | tick-200 (verdict-gating) |
|---|---|---|---|
| A_null_V0_25 | `A_NULL_V025_TICK50_BRIDGE_PRESENT` | PRESENT | `A_NULL_V025_TICK200_BRIDGE_PRESENT` (descriptive) |
| B_widened_V0_25 | n/a (categorical anchor at 0/64) | n/a | `B_WIDENED_V025_TICK200_BRIDGE_NOT_FOUND` (informational; reachability anchor holds) |
| C_widened_combined_se100_bmc010 | n/a | n/a | `C_COMBINED_SE100_BMC010_TICK200_BRIDGE_NOT_FOUND` (drives priority-5 verdict via reachability < 0.25) |

### Central scientific finding — survival-extension and food-reachability are decoupled on `widened_gradient`

The combined two-knob conjunction extended survival ~9× over v0.53e and ~5.6× over v0.53f, with founders carrying the most aggressive defensible single-arm budget envelope (`starting_energy=100`, `base_metabolic_cost=0.10`) without raising `max_energy`. **At ~87.5% population alive at tick-200, the substrate axis is responsive — yet not a single founder lineage in any of the 64 C runs reached food.**

| slice | C arm knob(s) | C tick-200 living_share | C tick-200 reachability |
|---|---|:-:|:-:|
| v0.53e | `starting_energy=100` | 0.0938 (~9.4%) | 0/64 |
| v0.53f | `base_metabolic_cost=0.10` | 0.1562 (~15.6%) | 0/64 |
| **v0.53g** | **both combined** | **0.8750 (~87.5%)** | **0/64** |

This breaks the "they just die too soon" explanation for the v0.53d–v0.53f null results. Survival-extension and food-reachability are decoupled on `widened_gradient`. The combined budget relaxation worked dramatically on survival (the body_config seam is fully responsive; the substrate axis is real) but food contact remained zero. The candidate space for v0.53h+ shifts away from founder-facing budget axes; the bottleneck is something else.

### Reachability across all three windows

| window | A_null_V0_25 | B_widened_V0_25 | C_widened_combined_se100_bmc010 | C ≥ 0.25? |
|---|:-:|:-:|:-:|:-:|
| tick-50 | 1.0000 | 0.0000 | 0.0000 | False (descriptive) |
| tick-100 | 1.0000 | 0.0000 | 0.0000 | False (descriptive) |
| tick-200 | 1.0000 | 0.0000 (Tier-2 categorical anchor) | **0.0000** | False (priority 5) |

C reachability is uniformly zero across all windows — matching v0.53e/f's single-knob patterns. The seam is responsive on survival but does not propagate to reachability under any tested envelope.

### Population-stability trajectory — substrate-axis stack

| arm | tick-50 living_share | tick-100 living_share | tick-200 living_share |
|---|:-:|:-:|:-:|
| A_null_V0_25 | 1.0000 | 1.0000 | 1.0000 |
| B_widened_V0_25 | 1.0000 | 0.5000 | **0.0000** (full extinction) |
| C_widened_combined_se100_bmc010 | 1.0000 | **1.0000** | **0.8750** (~87.5% alive) |

C maintains 100% population through tick-100 (v0.53e/f also reached tick-100 fully alive on C, but tick-200 dropped to 9.4%/15.6%). v0.53g's combined relaxation maintains ~87.5% to tick-200 — a dramatic survival horizon extension that confirms the body_config seam is fully functional on both knobs.

### Reachability-gating did not activate this slice

Per the v0.53f-introduced reachability-gated priority 3 trigger, priority 3 fires iff (C sub-verdict = `OPPOSITE_SIGN_HALT`) AND (`c_reachability_tick_200 ≥ 0.25`). Neither condition held in v0.53g:

- C tick-200 sub-verdict = `C_COMBINED_SE100_BMC010_TICK200_BRIDGE_NOT_FOUND` (no wrong-sign cells; no Label A nor Label B primary signed_d ≤ −0.5 at tick-200).
- C tick-200 reachability = 0.0000 (< 0.25).

The `wrong_sign_cells_under_reachability_below_threshold` section in `audit_summary.csv` is empty. The reachability-gating framework remains battle-tested via v0.53f only; v0.53g did not exercise the framework on live data because no wrong-sign cells emerged. (The framework code path is exercised in v0.53g's test #13 with synthetic fixtures.)

### Tier-1 bridge re-anchor — A_null_V0_25 tick-50 reproduces v0.48–v0.53f within 1e-3

| label | observable | published | derived | drift |
|---|---|:-:|:-:|:-:|
| `label_a_sensor_radius` | `pre50_food_events_count` | +1.066 | +1.066 | 0.0004 |
| `label_a_sensor_radius` | `pre50_food_energy_acquired` | +1.066 | +1.066 | 0.0004 |
| `label_a_sensor_radius` | `mean_distance_to_nearest_food_cell_tick50` | +1.916 | +1.916 | 0.0001 |
| `label_b_readiness_fraction_tick50` | `pre50_food_events_count` | +0.916 | +0.916 | 0.0001 |
| `label_b_readiness_fraction_tick50` | `pre50_food_energy_acquired` | +0.916 | +0.916 | 0.0001 |
| `label_b_readiness_fraction_tick50` | `mean_distance_to_nearest_food_cell_tick50` | +1.179 | +1.179 | 0.0004 |

Max drift 0.0004 (≤ 1e-3). All cells PASS.

### Tier-2 categorical anchor — B_widened_V0_25 reachability_run_share at tick-200

| anchor | locked value | derived | passes |
|---|:-:|:-:|:-:|
| `b_widened_v025_reachability_run_share_tick_200` | **0.0** (0/64) | 0.0000 (0/64) | True (categorical match) |

v0.53c–v0.53f's locked `0/64` reachability anchor holds.

### Corpus re-anchor

A_null_V0_25 arm — all PASS (max drift 0.0003):

| version | derived `a_share_h8` | published | drift |
|---|:-:|:-:|:-:|
| v0.42 | 0.652 | 0.652 | 0.0003 |
| v0.43R | 0.674 | — (informational) | — |
| v0.44 | 0.878 | 0.878 | 0.0001 |
| v0.45 | 0.818 | 0.818 | 0.0002 |

### What v0.53g can safely claim

- ✓ **A_null_V0_25 tick-50 anchor PASSES** within 0.0004 of v0.48–v0.53f. Reducer machinery (paired_d formula, three-window observer, three Label B variants, BodyConfig override path with two simultaneous knobs, reachability-gated priority-3 trigger) is correct.
- ✓ **B_widened_V0_25 categorical Tier-2 anchor PASSES exactly** (0/64 at tick-200). Predecessor lock holds.
- ✓ **The combined two-knob `body_config` override is fully functional.** B and C diverge dramatically — C reaches tick-200 at ~87.5% population alive, an order of magnitude above v0.53e (9.4%) and v0.53f (15.6%). The substrate axis is responsive on both knobs simultaneously.
- ✓ **`BodyConfig(starting_energy=100.0, base_metabolic_cost=0.10)` does NOT restore food reachability on `widened_gradient` × V0_25 × N_TICKS=200.** C reachability_run_share remains exactly `0.0000` at every window. No founder lineage in any of the 64 C runs produces a single `AteFood` event.
- ✓ **Survival-extension and food-reachability are decoupled on `widened_gradient`.** The combined budget relaxation extended survival ~9× over v0.53e and ~5.6× over v0.53f without lifting reachability above 0/64. This breaks the "they just die too soon" explanation.
- ✓ **Under V0_25 × `widened_gradient` × N_TICKS=200, reachability is not restored by the tested conservative single- or two-knob founder-facing budget relaxations.**
- ✓ **The reachability-gated priority-3 framework continues to behave correctly** (no wrong-sign cells emerged on live data; the synthetic test fixture in test #13 still passes).

### What v0.53g cannot claim

- ✗ **"`widened_gradient` is impossible"** under priority 5. v0.53g tested one combined-knob envelope at one dose. Stronger doses, additional knobs (`max_energy` co-raised), N_TICKS extension, or other axes (geometry / policy) remain untested.
- ✗ **"Geometry is fundamental."** The empirical result is that the tested founder-facing budget envelopes are insufficient. The result does not localize the bottleneck to geometry specifically — it could equally be policy / hazard-avoidance, N_TICKS horizon, or unmodeled dynamics. Cautious framing per CLAUDE.md.
- ✗ **"Budget is irrelevant."** v0.53g (combined relaxation) extended survival ~9× over v0.53e — budget is dramatically responsive on survival. The empirical claim is that the tested founder-facing budget envelopes do not lift reachability, NOT that budget has no effect.
- ✗ **A revised v0.53–v0.53f verdict.** All six predecessor verdicts stand as historical contracts.
- ✗ **Mechanism for the survival-extension-vs-reachability decoupling.** The 87.5% population at tick-200 with 0/64 food contact is a striking observation; no mechanism is formally established. Plausible interpretations (not formally established): policy doesn't drive founders into the corridor under any budget; hazard band blocks traversal regardless of energy; corridor exceeds the per-tick step-count any policy can deliver in 200 ticks; N_TICKS=200 is the binding horizon. v0.53h+ disambiguates.
- ✗ **Generalization beyond the tested arms.** Verdict scope is bounded to (`tight_gradient` × V0_25, `widened_gradient` × V0_25, `widened_gradient` × V0_25 with `BodyConfig(se100, bmc010)`) at `N_TICKS=200`.

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
| v0.53g | modern A_null | combined `BodyConfig(starting_energy=100, base_metabolic_cost=0.10)` extends survival ~87.5% (~9× v0.53e, ~5.6× v0.53f) but does NOT lift reachability above 0/64; survival-extension and food-reachability are decoupled on `widened_gradient`; under V0_25 × `widened_gradient` × N_TICKS=200, reachability is not restored by the tested conservative single- or two-knob founder-facing budget relaxations | observational (BELOW_REACHABILITY_THRESHOLD_UNDER_COMBINED_SE100_BMC010; central finding: survival-extension ⊥ reachability) |

The v0.46→v0.53g stack now reads: ... → v0.53e/f individually extended survival ~9-16% but did not lift reachability → **v0.53g's combined two-knob relaxation extended survival to ~87.5% alive at tick-200 — vastly more than either single-knob axis — yet still produced 0/64 reachability. Survival-extension and food-reachability are decoupled on `widened_gradient`; the candidate space for v0.53h+ shifts away from founder-facing budget axes.**

### Next-step candidates (open)

The combined budget result is strong enough to pivot away from budget-axis exploration. Three-knob budget co-variation (e.g., `max_energy` co-raised, or `base_metabolic_cost=0.05`) is deferred — the empirical signal that ~87.5% C survival without any food contact is informative on its own. The natural next step is to disambiguate the bottleneck along non-budget axes:

- **v0.53h — N_TICKS extension on `widened_gradient` under combined SE100/BMC010.** Recommended next slice. Test whether the bottleneck is the 200-tick simulation horizon by extending N_TICKS (e.g., to 400 or 800) on `widened_gradient` with the v0.53g combined budget envelope. C arm has ~87.5% survival at tick-200 — there's substantial unused horizon for traversal. If extended N_TICKS lifts reachability above 0.25, the bottleneck is the simulation horizon (a question of "how long until founders reach food given enough budget"). If it doesn't, the bottleneck is structural (policy, geometry, or unmodeled dynamics). Likely requires a small additive `src/` seam to expose `n_ticks` as a `run_chamber()` override (analogous to v0.53e's body_config seam); test #8 would re-pin chamber driver.
- **v0.53i (or later) — geometry calibration probe.** Vary corridor width, food placement, or hazard-band geometry on `widened_gradient`. May require new layout(s) and possibly src/ change to expose layout parameters.
- **v0.53j (or later) — policy / hazard-avoidance probe.** Vary `hazard_avoidance_weight` or other policy knobs on `widened_gradient` under V0_25 substrate.
- **v0.53k (or later) — three-knob founder-budget co-variation.** Add `max_energy=200` (or similar) to v0.53g's two-knob envelope. Deferred per the above pivot.
- **v0.53l (or later) — investigate the C_food_ladder Label B degradation trajectory.** Per-tick-window paired_d trajectory probe.
- **v0.53m (or later) — Reading-A causal-generalization slice on layouts admitting the bridge.**
- **v0.54 — joint ablation** (zero-cost AND shuffle).
- **Eventual fresh-stream calibration** on the v0.46–v0.53g conclusion stack.

User has not locked which slice is next.

### CI gate at v0.53g close

```
uv run ruff check .             ok
uv run ruff format --check .    ok (236 files already formatted)
uv run pytest                   1808 passed, 7 skipped (was 1792; +16 v0.53g)
uv run python scripts/core_smoke_test.py                                ok (determinism north star intact; no src/ changes)
uv run python scripts/v0_53g_substrate_axis_combined_se100_bmc010_audit.py   WIDENED_BELOW_REACHABILITY_THRESHOLD_UNDER_COMBINED_SE100_BMC010 (priority 5; reachability-gating did not activate — no wrong-sign cells)
```
