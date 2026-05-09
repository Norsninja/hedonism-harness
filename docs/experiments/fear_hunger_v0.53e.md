# fear_hunger v0.53e — substrate-axis disambiguation: founder starting-energy rescue probe on `widened_gradient` × tick-200

**Slice:** v0.53e
**Type:** **first-class observational sweep** with 3-arm tick-200 reducer (one additive `src/` seam in `fear_hunger_chamber.py`; no changes to core body, config, traits, sensors, layouts, metabolism, or policy logic; no intervention; one-knob substrate variation on the C arm only; reuses existing named layouts).
**Predecessors:** v0.46–v0.52b (full predecessor stack), v0.53 (`BRIDGE_PARTIALLY_GENERALIZES`), v0.53b (`WIDENED_BELOW_REACHABILITY_THRESHOLD_AT_TICK_100`), v0.53c (`WIDENED_BELOW_REACHABILITY_THRESHOLD_AT_TICK_200`), v0.53d (`WIDENED_BELOW_REACHABILITY_THRESHOLD_UNDER_RELAXED_INFLUX` — doubling `ambient_influx_rate` from `1.0` to `2.0` did not lift reachability on `widened_gradient` × V0_25 × N_TICKS=200; B_widened_V0_25 and C_widened_relaxed produced byte-identical metrics across all windows, consistent with the influx knob's effect path being inactive under no-food-contact extinction).
**Question being asked (locked):** Is v0.53c / v0.53d's reachability-bound result on `widened_gradient` driven by founder per-agent energy budget, rather than by ambient-pool dynamics? Specifically: does raising `BodyConfig.starting_energy` from the V0_25 baseline of `60.0` to `100.0` (the maximal legal one-knob founder-energy-budget increase under the existing `BodyConfig.max_energy=100.0` bound), with all other V0_25 substrate parameters held identical, lift `widened_gradient` reachability above the locked 25% threshold at tick-200 AND admit a measurable v0.48 sensor_radius spatial / foraging bridge?

v0.53d's locked Results explicitly named **founder-facing budget knobs** as the natural v0.53e candidate, with `base_metabolic_cost` lowered as primary and `starting_energy` raised as secondary. Subsequent design discussion (locked pre-data) inverted that priority on cleanliness grounds: `starting_energy` is a single one-time boost at tick-0 that does not perturb per-tick metabolism, ecology, or trait-cost structure; `base_metabolic_cost` perturbs every tick and changes the survival equation throughout the simulation. A clean single-axis negative on the cleaner knob is more informative than a partial result on the noisier one. v0.53e is therefore that probe along **`starting_energy = 100.0`**.

The choice of `starting_energy = 100.0` (rather than `80.0`, `120.0`, or any value requiring `max_energy` to also be raised) is locked pre-data on the following grounds: **`starting_energy = 100` is the maximal legal one-knob founder-energy-budget increase under the existing `BodyConfig.max_energy=100` bound** (Pydantic model_validator enforces `starting_energy ≤ max_energy`). Anything stronger requires a two-knob co-variation. v0.53e tests the strongest one-knob founder-energy-budget rescue available; if even this fails, the bottleneck on `widened_gradient` is not founder-energy-budget under V0_25's metabolic schedule.

If C_widened_starting_energy_100 reachability ≥ 25% at tick-200 AND tick-200 sub-verdict resolves PRESENT, v0.53c / v0.53d's reachability ceiling on `widened_gradient` × V0_25 is bounded by founder starting-energy — the geometry-substrate cell admits measurement once founders have the maximum legal initial budget. If reachability ≥ 25% AND tick-200 sub-verdict ∈ {PARTIAL, NOT_FOUND}, the budget rescue admits measurement but the bridge does not fully fire — a partial-rescue outcome. If reachability < 25% at tick-200 even at maximum legal `starting_energy`, the (V0_25 × `widened_gradient`) cell **is not rescued by `starting_energy=100` under N_TICKS=200**; v0.53f remains the natural follow-up along `base_metabolic_cost` lowered (per-tick depletion rate, the orthogonal founder-facing budget axis). v0.53e does not claim "geometry-fundamental"; the verdict scope is bounded to the tested one-knob envelope.

## Pre-implementation note (2026-05-09, before any reducer code)

The pre-reg's design was confirmed with the user before drafting:

- **3 arms (asymmetric).** A_null_V0_25 (`tight_gradient`, V0_25 substrate, anchor). B_widened_V0_25 (`widened_gradient`, V0_25 substrate; predecessor lock from v0.53c / v0.53d). C_widened_starting_energy_100 (`widened_gradient`, V0_25 substrate **except** `BodyConfig.starting_energy = 100.0`). Same 64-tuple corpus.
- **One BodyConfig knob, one dose.** Only `starting_energy` is varied on C, and only between V0_25 baseline (`60.0`) and the locked test dose (`100.0` = `max_energy` bound). Dose-response (multiple doses) and additional knob variation (e.g., `base_metabolic_cost`) are deferred to v0.53f / later contingent on v0.53e's outcome.
- **One additive `src/` seam.** v0.53e adds a `body_config: BodyConfig | None = None` parameter to `run_chamber()` in `src/hedonism_harness/experiments/fear_hunger_chamber.py`. The default-preserving fallback is `body_cfg = body_config if body_config is not None else BodyConfig()`. **No changes** to `src/hedonism_harness/core/body.py`, `core/config.py`, `core/traits.py`, `core/sensors.py`, `experiments/layouts.py`, `metrics/`, `policies/`, or `model.py`. The seam is additive, default-preserving, and confined to the chamber driver.
- **Tick-200 verdict gating.** Per-tick observer accumulates through tick-200 (canonical v0.53c / v0.53d three-window template). Three Label B variants (`tick50` anchor / `tick100` descriptive / `tick200` verdict-gating) computed in parallel.
- **Tier-2 categorical anchor on B_widened_V0_25 preserved.** v0.53e re-locks B_widened_V0_25's reachability at tick-200 as `0/64` (the v0.53c / v0.53d categorical lock), exact integer comparison. ANCHOR_REPLICATION_HALT fires on integer mismatch.
- **Pool / ecology preserved.** A, B, and C all retain V0_25 baseline `ambient_influx_rate=1.0`, `energy_pool_initial=1500.0`, `food_respawn_cooldown=50`, `child_funding_mode=PARENT_TRANSFER_POOL_GAP`, hazard_damage per (version, hazard) corpus row. Only `body_config` differs on C.
- **Expected behavioral divergence between B and C from tick-0** (unlike v0.53d). `starting_energy` directly perturbs founder body energy at agent-construction time and propagates through every per-tick metabolic depletion. The byte-identity-with-B observation that surfaced in v0.53d will not recur on v0.53e regardless of rescue outcome — interpretation is cleaner in either direction.

## Conservation framing — observational, additive chamber-driver seam, one-knob substrate variation on C only

- **One additive `src/` seam in `fear_hunger_chamber.py`; no changes to core body, config, traits, sensors, layouts, metabolism, or policy logic.** The seam adds a `body_config: BodyConfig | None = None` parameter to `run_chamber()` with a default-preserving fallback. SHA-256 of `fear_hunger_chamber.py` updates from v0.52b-tip; SHA-256 of the science-core five files (`core/sensors.py`, `core/traits.py`, `core/body.py`, `core/config.py`, `experiments/layouts.py`) remain byte-identical to v0.52b-tip. Test #8 enforces both pinning categories.
- **No modifications to prior reducer or audit scripts.** v0.34's `lineage_replay.py`, v0.35's `lineage_survival_replay.py`, v0.36's `trait_replay.py`, v0.48's reducer, v0.53 / v0.53b / v0.53c / v0.53d's reducers remain byte-identical to their merged forms.
- **Default-preserving seam.** Every v0.NN reducer / sweep / test that calls `run_chamber()` without `body_config=...` continues to receive `BodyConfig()` defaults (the v0.7..v0.52b path). The seam is callable-additive, not behavior-changing on existing call sites. CI smoke (`scripts/core_smoke_test.py`) and existing reducer pytest paths verify this.
- **A_null_V0_25 arm is byte-identical to v0.48 / v0.53 / v0.53b / v0.53c / v0.53d A_null path AT TICK-50.** Tier-1 re-anchor enforces this within 1e-3.
- **B_widened_V0_25 arm is byte-identical to v0.53 / v0.53b / v0.53c / v0.53d's B_widened arm at every tick 0..200.** Tier-2 categorical anchor enforces `b_widened_v025_reachability_run_share_tick_200 == 0.0`.
- **C_widened_starting_energy_100 differs from B_widened_V0_25 only via `BodyConfig.starting_energy` (60.0 → 100.0).** All other WorldConfig / BodyConfig / ReproductionConfig / ActionConfig parameters identical to V0_25 baseline. Same chamber layout (`widened_gradient_layout()`), same founder draw, same per-agent RNGs.
- **No intervention at any level on any arm.** No founder body trait modification post-construction, no override patching, no helper RNG, no shuffle, no clamp, no permutation. The `starting_energy=100.0` change is config-time, not setup-observer-time — distinct from the v0.49 founder-clamp pattern.

## Corpus (locked, 64 × 3 arms = 192 runs)

Same shape as v0.53 / v0.53b / v0.53c / v0.53d:

| version | seeds | hazards | runs per arm | total runs |
|---|---|---|---|---|
| v0.42 | 41..48 | {0, 8} | 16 | 48 |
| v0.43R | 49..56 | {0, 8} | 16 | 48 |
| v0.44 | 57..64 | {0, 8} | 16 | 48 |
| v0.45 | 65..72 | {0, 8} | 16 | 48 |
| **total** | | | | **192** |

V0_25 substrate identical to v0.53 / v0.53b / v0.53c / v0.53d on A and B; C identical except `BodyConfig.starting_energy=100.0`. Wall time estimate ~12–25 minutes total (faster than v0.53d if rescue admits longer survival; slower if it admits later extinction with more events).

## Arms (locked, 3 — asymmetric BodyConfig)

### A_null_V0_25

```
ChamberLayout = tight_gradient_layout()
ambient_influx_rate = 1.0  (V0_25 baseline)
energy_pool_initial = 1500.0
food_respawn_cooldown = 50
child_funding_mode = PARENT_TRANSFER_POOL_GAP
hazard_damage = per (version, hazard) corpus row
body_config = None  (default BodyConfig: starting_energy=60.0, max_energy=100.0, base_metabolic_cost=0.25, ...)
FounderSpec(traits_override=None)
no patch, no body_config override, no per-agent override
```

Byte-identical to v0.48 / v0.53 / v0.53b / v0.53c / v0.53d A_null path at every tick 0..200. Used for:
1. **Tier-1 anchor at tick-50** (against v0.48 / v0.53 / v0.53b / v0.53c / v0.53d published cells).
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
no patch, no body_config override, no per-agent override
```

Byte-identical to v0.53 / v0.53b / v0.53c / v0.53d's B_widened arm at every tick 0..200. **Predecessor-lock arm for v0.53e**: the rollup gates on B_widened_V0_25's categorical reachability anchor, not on its sub-verdict.

### C_widened_starting_energy_100

```
ChamberLayout = widened_gradient_layout()
ambient_influx_rate = 1.0  (V0_25 baseline)
energy_pool_initial = 1500.0  (V0_25 baseline)
food_respawn_cooldown = 50  (V0_25 baseline)
child_funding_mode = PARENT_TRANSFER_POOL_GAP  (V0_25 baseline)
hazard_damage = per (version, hazard) corpus row  (V0_25 baseline)
body_config = BodyConfig(starting_energy=100.0)
  (RELAXED — starting_energy raised from V0_25 baseline 60.0 to 100.0;
   max_energy=100.0 default preserved; all other BodyConfig fields default)
FounderSpec(traits_override=None)
no patch, no per-agent override
```

Differs from B_widened_V0_25 by exactly one knob: `BodyConfig.starting_energy` (60.0 → 100.0). All other BodyConfig fields preserved at default (`max_energy=100.0`, `starting_health=100.0`, `max_health=100.0`, `base_metabolic_cost=0.25`, `sensor_radius_metabolic_cost=0.05`, `effective_sensor_radius_override=None`). **The primary arm of v0.53e**: the verdict gates on C's tick-200 reachability and tick-200 sub-verdict.

## Labels (locked, two — with three Label B variants)

### Label A — `high_sensor_radius_lineage`

Identical to v0.48–v0.53d. Trait-resolved (`int(founder.body.traits.sensor_radius)`); tiebreak `min(lineage_id)`. Time-window-independent.

### Label B — three variants computed in parallel

Each is `argmax_lineage(tickN_above_threshold_fraction)` with the v0.47 3-tier tiebreak (fraction → count → min(lineage_id), NaN-loses):

- **`high_tick50_readiness_fraction_lineage`** — used for the Tier-1 anchor against v0.48 / v0.53 / v0.53b / v0.53c / v0.53d on the A arm.
- **`high_tick100_readiness_fraction_lineage`** — used for descriptive context (NOT gating).
- **`high_tick200_readiness_fraction_lineage`** — used for the v0.53e **verdict** on the C arm.

If at tick-N **no lineage has any agent above the readiness threshold** (everyone NaN or zero), Label B for that run is undefined; the per-run paired_d delta cells are `nan` and the per-arm cell's `n` decrements.

## Primary observables (locked, 3, computed at three windows)

| # | name pattern | windows | expected sign |
|---|---|---|:-:|
| 1 | `pre{N}_food_events_count` | N ∈ {50, 100, 200} | + |
| 2 | `pre{N}_food_energy_acquired` | N ∈ {50, 100, 200} | + |
| 3 | `mean_distance_to_nearest_food_cell_tick{N}` | N ∈ {50, 100, 200} | − |

Definitions / aggregation rules / NaN handling: copy-local from v0.48–v0.53d. Primaries 1 / 2 accumulate `AteFood` events through tick-N inclusive (`tick_now <= TICK_N`). Primary 3 is a snapshot at tick-N over living agents per lineage.

## Effect-size rule (locked, sign-aware, identical to v0.48–v0.53d)

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

c_widened_starting_energy_100_reachability_run_share_tick_200 =
    fraction of C_widened_starting_energy_100 runs where at least one
    founder lineage has pre200_food_events_count > 0
```

Domain: 64 runs per arm. Threshold: **`B_REACHABILITY_THRESHOLD = 0.25`** (preserved from v0.53b / v0.53c / v0.53d).

The B_widened_V0_25 metric is the Tier-2 categorical predecessor anchor (must equal `0.0` exactly, i.e., `0/64`). The C_widened_starting_energy_100 metric is the verdict-gating reachability (compared against the 0.25 threshold).

## Population-stability and degenerate-label descriptive metrics (locked, pre-data, per arm × window)

Identical structure to v0.53c / v0.53d:

```
arm_living_population_run_share_tick_N
arm_label_a_n_runs_tick_N
arm_label_b_n_runs_tick_N
```

Descriptive only — no halt or outcome gates on them directly. Reported in Results.

## Per-arm sub-verdicts (locked, 4-way each)

| condition | A_null_V0_25 (tick-200) | B_widened_V0_25 (tick-200) | C_widened_starting_energy_100 (tick-200) |
|---|---|---|---|
| both labels clear ≥ 2/3 of the three locked cells, with NaN treated as non-firing, 0 wrong-sign | `A_NULL_V025_TICK200_BRIDGE_PRESENT` | `B_WIDENED_V025_TICK200_BRIDGE_PRESENT` | `C_STARTING_ENERGY_100_TICK200_BRIDGE_PRESENT` |
| exactly one label clears ≥ 2/3 of the three locked cells, with NaN treated as non-firing, 0 wrong-sign | `A_NULL_V025_TICK200_BRIDGE_PARTIAL` | `B_WIDENED_V025_TICK200_BRIDGE_PARTIAL` | `C_STARTING_ENERGY_100_TICK200_BRIDGE_PARTIAL` |
| neither label clears ≥ 2/3 of the three locked cells, with NaN treated as non-firing, 0 wrong-sign | `A_NULL_V025_TICK200_BRIDGE_NOT_FOUND` | `B_WIDENED_V025_TICK200_BRIDGE_NOT_FOUND` | `C_STARTING_ENERGY_100_TICK200_BRIDGE_NOT_FOUND` |
| any primary signed_d ≤ −0.5 under either label | `A_NULL_V025_TICK200_OPPOSITE_SIGN_HALT` | `B_WIDENED_V025_TICK200_OPPOSITE_SIGN_HALT` | `C_STARTING_ENERGY_100_TICK200_OPPOSITE_SIGN_HALT` |

**Strict NaN-treated-as-non-firing rule preserved from v0.48–v0.53d.** A label clears 2/3 iff at least 2 of its 3 cells fire expected; NaN counts toward the denominator (3) and as non-firing. Test #12 enforces.

Each arm's tick-200 paired_d cells (3 observables × 2 labels = 6 cells per arm; 18 cells total across the three arms) are computed independently from the arm's 64-run pool with NaN-runs excluded from the per-cell `n`.

## Slice rollup verdicts (locked, 6 outcomes, priority-ordered)

Priority order (first-matching wins). The non-halt outcomes (priorities 4–6) gate **only on C_widened_starting_energy_100**.

1. `CORPUS_REDERIVE_DRIFT_HALT`
2. `ANCHOR_REPLICATION_HALT`
3. `RELAXED_OPPOSITE_SIGN_HALT`
4. `WIDENED_BRIDGE_RESCUED_BY_STARTING_ENERGY_100`
5. `WIDENED_BELOW_REACHABILITY_THRESHOLD_UNDER_STARTING_ENERGY_100`
6. `WIDENED_BRIDGE_PARTIALLY_RESCUED_BY_STARTING_ENERGY_100`

### Halt conditions

| priority | rollup verdict | trigger | locked phrase (verbatim) |
|---|---|---|---|
| 1 | `CORPUS_REDERIVE_DRIFT_HALT` | A_null_V0_25 arm `a_share_h8` for any of v0.42 / v0.44 / v0.45 drifts > 1e-3 from the published reference | "Halt: A_null_V0_25 re-anchor drifted from the published Results value for {version}; v0.53e's deterministic re-execution of the V0_25 corpus does not reproduce the published metric within 1e-3." |
| 2 | `ANCHOR_REPLICATION_HALT` | (a) A_null_V0_25 tick-50 signed_d for any of the six v0.48 / v0.53 / v0.53b / v0.53c / v0.53d cells drifts > 1e-3 from the published value, OR (b) A_null_V0_25 tick-50 sub-verdict ≠ PRESENT, OR (c) `b_widened_v025_reachability_run_share_tick_200` ≠ `0.0` (any B_widened_V0_25 run with `pre200_food_events_count > 0` for any lineage, contradicting v0.53c / v0.53d's `0/64` lock) | "Halt: v0.53e's A_null_V0_25 arm does not reproduce v0.48 / v0.53 / v0.53b / v0.53c / v0.53d's tick-50 spatial bridge, OR v0.53e's B_widened_V0_25 arm does not reproduce v0.53c / v0.53d's `0/64` reachability lock at tick-200. v0.53e cannot interpret the C_widened_starting_energy_100 cells without an established baseline on the V0_25 substrate." |
| 3 | `RELAXED_OPPOSITE_SIGN_HALT` | C_widened_starting_energy_100 has finite `signed_d ≤ −0.5` under either gating label on a tick-200 primary observable | "Halt: a v0.53e C_widened_starting_energy_100 tick-200 spatial / foraging primary fires in the WRONG direction under a gating label; raising `BodyConfig.starting_energy` from V0_25 baseline `60.0` to the maximal legal `100.0` on the `widened_gradient` layout surfaces a regime incompatible with the locked expected signs." |

### Tier-1 (priority 2.a) re-anchor — A_null_V0_25 tick-50 cells

Identical six cells to v0.48 / v0.53 / v0.53b / v0.53c / v0.53d:

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

Locked from v0.53c / v0.53d's measured result. Any non-zero value halts loud under priority 2.

### Outcome conditions (only consulted if no halt fires)

| priority | rollup verdict | trigger | locked phrase (verbatim) |
|---|---|---|---|
| 4 | `WIDENED_BRIDGE_RESCUED_BY_STARTING_ENERGY_100` | `c_widened_starting_energy_100_reachability_run_share_tick_200 ≥ 0.25` AND C_widened_starting_energy_100 tick-200 sub-verdict = `C_STARTING_ENERGY_100_TICK200_BRIDGE_PRESENT` | "On the modern A_null corpus with the V0_25 substrate held constant except for `BodyConfig.starting_energy = 100.0` (raised from the V0_25 baseline of `60.0` to the maximal legal one-knob value under the existing `BodyConfig.max_energy = 100.0` bound) on `widened_gradient`, the v0.48 sensor_radius spatial / foraging bridge fires PRESENT under the locked +0.5 paired_d threshold at tick-200. The geometry/substrate cell that v0.53c locked as `WIDENED_BELOW_REACHABILITY_THRESHOLD_AT_TICK_200` and v0.53d locked as `WIDENED_BELOW_REACHABILITY_THRESHOLD_UNDER_RELAXED_INFLUX` admits a measurable bridge under the maximal one-knob founder starting-energy envelope: B_widened_V0_25 reachability remains `0/64` at tick-200 (predecessor lock holds), C_widened_starting_energy_100 reachability clears the locked 25% threshold, and ≥ 2/3 spatial / foraging primaries fire PRESENT under both gating labels. The (V0_25 × `widened_gradient`) reachability ceiling is bounded by the V0_25 founder starting-energy budget at the `max_energy` bound, not by the geometry alone: `WIDENED_BRIDGE_RESCUED_BY_STARTING_ENERGY_100`." |
| 5 | `WIDENED_BELOW_REACHABILITY_THRESHOLD_UNDER_STARTING_ENERGY_100` | `c_widened_starting_energy_100_reachability_run_share_tick_200 < 0.25` | "On the modern A_null corpus with the V0_25 substrate held constant except for `BodyConfig.starting_energy = 100.0` (raised from the V0_25 baseline of `60.0` to the maximal legal one-knob value under the existing `BodyConfig.max_energy = 100.0` bound) on `widened_gradient`, fewer than 25% of C_widened_starting_energy_100 runs have any founder lineage with pre200 food events. C_widened_starting_energy_100's reachability is below the locked 25% threshold at tick-200; the geometry/substrate cell that v0.53c locked as `WIDENED_BELOW_REACHABILITY_THRESHOLD_AT_TICK_200` and v0.53d locked as `WIDENED_BELOW_REACHABILITY_THRESHOLD_UNDER_RELAXED_INFLUX` remains below the reachability threshold under the maximal one-knob founder starting-energy envelope. The bridge is not rescued by `BodyConfig.starting_energy = 100` under V0_25 × `widened_gradient` × N_TICKS=200; v0.53f along `base_metabolic_cost` lowered (per-tick depletion rate, the orthogonal founder-facing budget axis) remains the natural follow-up: `WIDENED_BELOW_REACHABILITY_THRESHOLD_UNDER_STARTING_ENERGY_100`." |
| 6 | `WIDENED_BRIDGE_PARTIALLY_RESCUED_BY_STARTING_ENERGY_100` | `c_widened_starting_energy_100_reachability_run_share_tick_200 ≥ 0.25` AND C_widened_starting_energy_100 tick-200 sub-verdict ∈ {`C_STARTING_ENERGY_100_TICK200_BRIDGE_PARTIAL`, `C_STARTING_ENERGY_100_TICK200_BRIDGE_NOT_FOUND`} | "On the modern A_null corpus with the V0_25 substrate held constant except for `BodyConfig.starting_energy = 100.0` (raised from the V0_25 baseline of `60.0` to the maximal legal one-knob value under the existing `BodyConfig.max_energy = 100.0` bound) on `widened_gradient`, C_widened_starting_energy_100's reachability clears the locked 25% threshold at tick-200 but the v0.48 sensor_radius spatial / foraging bridge does not fully fire PRESENT — fewer than 2/3 primaries fire across both gating labels at tick-200 under the strict NaN rule. The geometry/substrate cell that v0.53c locked as `WIDENED_BELOW_REACHABILITY_THRESHOLD_AT_TICK_200` and v0.53d locked as `WIDENED_BELOW_REACHABILITY_THRESHOLD_UNDER_RELAXED_INFLUX` is partially rescued under the maximal one-knob founder starting-energy envelope: reachability becomes measurable but the bridge does not fully replicate. Layout-specific partial-rescue logged in Results: `WIDENED_BRIDGE_PARTIALLY_RESCUED_BY_STARTING_ENERGY_100`." |

The rollup is **categorical-only**. Magnitude differences in tick-100 cells (or descriptive A / B tick-200 cells) are reported in Results but do not alter the verdict.

The 3 non-halt outcomes form a total partition of (C reachability ≥ 0.25, C sub-verdict ∈ {PRESENT, PARTIAL, NOT_FOUND}) ∪ (C reachability < 0.25). Halts cover OPPOSITE_SIGN, drift, replication. Test #16 enforces the partition exhaustively.

## Cautious framing (per CLAUDE.md)

- "**Bridge rescued by starting-energy at the max_energy bound**", "**reachability ceiling bounded by the V0_25 founder starting-energy budget at the `max_energy` bound, not by the geometry alone**", "**bridge is not rescued by `BodyConfig.starting_energy = 100` under V0_25 × widened_gradient × N_TICKS=200**" — NOT "**proves**", "**causes**", or "**rules out**".
- "**Maximal one-knob founder starting-energy envelope**" specifically means `starting_energy ∈ {60.0 (V0_25 baseline), 100.0 (v0.53e test dose, = max_energy bound)}` at `N_TICKS=200`. v0.53e does NOT establish behavior at intermediate doses, behavior with `max_energy` also raised, or behavior under multi-knob co-variation; those require separate slices.
- "**(V0_25 × `widened_gradient`) cell**" means the specific layout × substrate combination tested. v0.53e's verdict is bounded to the starting-energy variant only — the verdict does NOT generalize to layouts not in the v0.53/b/c/d set, to substrates not in the V0_25 family with `starting_energy ∈ {60.0, 100.0}`, or to N_TICKS > 200.
- v0.53e explicitly does not establish: cross-layout generalization beyond the three v0.53 layouts, mechanism for any rescue or non-rescue outcome, generalization to non-V0_25 substrates beyond the starting-energy axis, behavior at `n_ticks > 200`, causal contribution per layout (Reading-A causal-generalization slice remains the deferred candidate).

## What v0.53e cannot establish (logged here pre-data, not retrofittable)

- ✗ **"`widened_gradient` is geometry-fundamental"** if priority 5 fires. v0.53e tests V0_25 substrate × `BodyConfig.starting_energy=100.0` × N_TICKS=200 only. Different metabolic / pool / cooldown / co-varied parameters (single-knob or multi-knob), or multi-axis founder-budget co-variations (e.g., `max_energy` raised together with `starting_energy`), may admit reachability. v0.53f along `base_metabolic_cost` remains the natural follow-up.
- ✗ **"The bridge IS or IS NOT load-bearing on `widened_gradient`"** under any priority-4/5/6 outcome. The observation tells us about reachability and bridge-firing under maximum legal one-knob starting-energy; it does not establish channel-level causal contribution (deferred Reading-A slice).
- ✗ **A revised v0.53 / v0.53b / v0.53c / v0.53d verdict.** All four stand as historical contracts. v0.53e is the *founder-starting-energy axis* probe; its scope is v0.53d's deferred follow-up question along a different (founder-facing) knob.
- ✗ **Mechanism behind any rescue or non-rescue outcome.** Population dynamics under V0_25 × `widened_gradient` × `BodyConfig.starting_energy=100.0` are descriptively logged; no mechanism is formally established.
- ✗ **Generalization beyond the tested arms.** The verdict is bounded to (`tight_gradient` × V0_25, `widened_gradient` × V0_25, `widened_gradient` × V0_25 with `starting_energy=100.0`) at `N_TICKS=200`.

## Open framing (NOT in v0.53e primary)

- **v0.53f — substrate-axis disambiguation along `base_metabolic_cost` lowered.** Triggered if v0.53e fires priority 5 (or, descriptively, if v0.53e's rescue is partial). Per-tick depletion rate is the orthogonal founder-facing budget axis to `starting_energy`. Candidate dose: `0.10` (down from V0_25 baseline `0.25`, a 60% reduction). Independent observational slice; no `src/` change required (the seam from v0.53e already supports `BodyConfig` overrides).
- **v0.53g (or later) — multi-knob founder-budget co-variation.** Triggered if v0.53f also fires priority 5. Could test `starting_energy=100` AND `base_metabolic_cost=0.10` together; or `starting_energy + max_energy` co-raised to e.g., `120`. Independent observational slice.
- **v0.53h (or later) — investigate the C_food_ladder Label B degradation trajectory.** Why does Label B's bridge weaken from tick-50 to tick-200 specifically on `food_ladder` while Label A holds? Per-tick-window paired_d trajectory probe. Independent of v0.53e outcome.
- **v0.53i (or later) — Reading-A causal-generalization slice on layouts admitting the bridge.** Re-run v0.49's null + clamp_4 + permutation_5! per layout that admits measurement.
- **v0.54 — joint ablation** (zero-cost AND shuffle). Channel-interaction question. Independent of layout × substrate-axis findings.
- **Eventual fresh-stream calibration** on the v0.46–v0.53e conclusion stack — needed for any "mechanism" declaration. Longer-horizon.

## Re-anchor (locked — Tier-1 and corpus only at tick-50)

| version | published `a_share_h8` |
|---|---|
| v0.42 | 0.652 |
| v0.43R | NOT PUBLISHED (informational-only) |
| v0.44 | 0.878 |
| v0.45 | 0.818 |

A_null_V0_25 arm only gates the corpus rollup. B_widened_V0_25 and C_widened_starting_energy_100 arms re-derive their own `a_share_h8` for descriptive logging; do NOT gate the verdict on `a_share_h8`.

## Outputs (locked)

```
runs/v0.53e-substrate-axis-starting-energy-100/per_run_per_lineage_v053e.csv
  columns: arm, layout_name, body_starting_energy, version, seed, hazard, run_id, lineage_id,
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

runs/v0.53e-substrate-axis-starting-energy-100/audit_summary.csv
runs/v0.53e-substrate-axis-starting-energy-100/audit_log.txt
```

## Implementation plan (locked)

1. **One additive `src/` seam in `fear_hunger_chamber.py`:**
   - Add parameter `body_config: BodyConfig | None = None` to `run_chamber()` signature.
   - At the existing `body_cfg = BodyConfig()` line (currently `experiments/fear_hunger_chamber.py:391`), change to:
     ```python
     body_cfg = body_config if body_config is not None else BodyConfig()
     ```
   - No other changes anywhere in `src/`. The seam is additive, default-preserving, and confined to the chamber driver.
2. Fresh script `scripts/v0_53e_substrate_axis_starting_energy_audit.py`. CLI: `uv run python scripts/v0_53e_substrate_axis_starting_energy_audit.py [--out-dir runs/v0.53e-substrate-axis-starting-energy-100]`.
3. Per (version, seed, hazard) tuple, run **3 arms**. A and B pass `body_config=None` (default BodyConfig); C passes `body_config=BodyConfig(starting_energy=100.0)`.
4. Setup_observer order (matches v0.53c / v0.53d merged implementation): (a) capture v0.53e founder audit table including `body.energy` at tick 0 (verifies the seam took effect), (b) wire `AgentBorn` / `AteFood` / `HazardDamageApplied` listeners, (c) read back `model.world.width` and assert layout match per-arm, (d) capture tick-0 snapshot.
5. Per-tick observer accumulates `pre50_*` / `pre100_*` / `pre200_*` rollups in parallel; emits all three at end-of-run.
6. Use the relaxed contiguous-prefix tick-records invariant from v0.53b / v0.53c / v0.53d (handles early extinction; tick-0 always present).
7. Aggregate per-lineage primaries at all three windows. Compute Label A and three Label B variants (tick50 / tick100 / tick200).
8. Compute paired_d per (arm, gating-label, observable, window) cell. 18 cells per window × 3 windows = 54 cells total. Tick-200 cells gate the C_widened_starting_energy_100 sub-verdict; tick-50 cells gate the A_null_V0_25 Tier-1 anchor; tick-100 cells are descriptive.
9. Compute per-arm reachability_run_share at all three windows. The B_widened_V0_25 tick-200 value is the Tier-2 categorical anchor (must equal `0.0` exactly). The C_widened_starting_energy_100 tick-200 value is the verdict-gating reachability.
10. Compute per-arm population-stability metrics (living_population_run_share, label_a_n_runs, label_b_n_runs at all three windows).
11. **Tier-1 bridge re-anchor** (priority 2.a / 2.b): A_null_V0_25 arm's six tick-50 cells vs v0.48 / v0.53 / v0.53b / v0.53c / v0.53d published; halt if drift > 1e-3 OR if A_null_V0_25 tick-50 sub-verdict ≠ PRESENT.
12. **Tier-2 categorical anchor** (priority 2.c): `b_widened_v025_reachability_run_share_tick_200 == 0.0` exactly.
13. **Corpus re-anchor** (priority 1): A_null_V0_25 arm only; halt if `a_share_h8` for v0.42 / v0.44 / v0.45 drifts > 1e-3.
14. **Relaxed opposite-sign halt** (priority 3): scan all C_widened_starting_energy_100 tick-200 gating-label cells; halt if any signed_d ≤ −0.5.
15. Compute slice rollup verdict per the locked priority + (C reachability tick-200, C sub-verdict tick-200) decision matrix; print + write the locked phrase verbatim.

The reducer is fully self-contained: it reads no `runs/` artifacts. Wall time estimate ~12–25 minutes for 192 runs.

## Test list (locked, 16 tests; extends v0.53d's pattern with seam-test additions)

`tests/test_v0_53e_substrate_axis_starting_energy_audit.py`:

1. **`test_paired_d_function_reproduces_hand_computed_signed_d_on_fixture_and_tier1_constants_match_v048_published_values`** *(re-anchor test, two-part)*.
2. **`test_a_null_v025_corpus_a_share_h8_re_anchors_v042_v044_v045`** — drift halt fires if any drift > 1e-3.
3. `test_arm_a_null_v025_uses_tight_gradient_layout_and_default_body_config` — chamber driver receives `tight_gradient_layout()` AND `body_config=None`; layout invariant assert.
4. `test_arm_b_widened_v025_uses_widened_gradient_layout_and_default_body_config` — chamber driver receives `widened_gradient_layout()` AND `body_config=None`; layout invariant assert.
5. **`test_arm_c_widened_starting_energy_100_seam_differentiates_b_and_c_body_energy_at_tick_0`** *(cross-arm contrast — verifies the `body_config` seam took effect at config-time founder construction)* — for the same (version, seed, hazard) tuple under matched RNG streams, assert:
   - **B_widened_V0_25 founder `body.energy` at tick-0 == `60.0`** (V0_25 baseline `starting_energy` from the default `BodyConfig()` fallback).
   - **C_widened_starting_energy_100 founder `body.energy` at tick-0 == `100.0`** (overridden `starting_energy` via `body_config=BodyConfig(starting_energy=100.0)`).
   - Both arms use `widened_gradient_layout()`; the only configured difference is the `body_config` parameter.
   - For C, explicitly assert that no other `BodyConfig` field differs from default (`max_energy=100.0`, `starting_health=100.0`, `max_health=100.0`, `base_metabolic_cost=0.25`, `sensor_radius_metabolic_cost=0.05`, `effective_sensor_radius_override=None`) AND no other WorldConfig knob differs from V0_25 baseline.
   - Founder body energies are read (not written) via `setup_observer` snapshot at tick-0; the test does NOT patch any founder body field.
6. **`test_founder_traits_byte_identical_across_arms_for_same_seed`** — full Traits records byte-identical across all three arms at setup_observer end. Arms differ only in chamber config (layout + body_config), not in founder draw.
7. **`test_founder_positions_byte_identical_across_arms_for_same_seed`** — founder (x, y) byte-identical (all three arms have spawn_x=1, height=6).
8. **`test_no_src_modifications_to_science_core_compared_to_v0_52b_tip_AND_chamber_driver_re_pinned`** *(two-part src/ pinning test)* —
   Part A: SHA-256 of five science-core files (`core/sensors.py`, `core/traits.py`, `core/body.py`, `core/config.py`, `experiments/layouts.py`) match v0.52b-tip values exactly. Failure message verbatim: `"v0.53e is pre-registered to leave the science-core five files byte-identical to v0.52b-tip; update the pre-reg before changing src/core or src/experiments/layouts."`
   Part B: SHA-256 of `src/hedonism_harness/experiments/fear_hunger_chamber.py` matches the v0.53e-tip post-seam-add value (locked at implementation time). Failure message verbatim: `"v0.53e's chamber-driver seam is pre-registered to be a one-time additive change; the chamber driver must remain byte-identical to its v0.53e-tip hash going forward."`
9. `test_label_a_high_sensor_radius_lineage_picks_correct_lineage` — synthetic 5-founder draw; tiebreak `min(lineage_id)`.
10. **`test_label_b_three_variants_three_tier_tiebreak_at_each_window`** — synthetic readiness fractions at tick-50 / tick-100 / tick-200 with two-way tie on fraction → tiebreak by count → tiebreak by min(lineage_id). NaN-loses.
11. **`test_pre200_window_strictly_extends_pre100_and_pre50_windows`** *(window-extension test; preserved from v0.53c / v0.53d)* — synthetic per-tick AteFood events at ticks 10, 30, 60, 90, 130, 180, 200; assert counts 2 / 4 / 7.
12. **`test_subverdict_present_requires_two_thirds_firing_cells_with_nan_treated_as_non_firing_strict`** — synthetic 3-cell label with 2 firing + 1 NaN → label clears 2/3 → contributes PRESENT. Synthetic 3-cell label with 1 firing + 2 NaN → does NOT contribute. Synthetic 3-cell label with 0 firing + 3 NaN → does NOT contribute.
13. `test_paired_d_signed_d_le_neg_05_fires_relaxed_opposite_sign_halt_for_c_arm` — synthetic any C tick-200 cell signed_d = −0.5 → priority 3 RELAXED_OPPOSITE_SIGN_HALT fires.
14. **`test_b_widened_v025_categorical_anchor_at_tick_200`** *(Tier-2 anchor test, preserved from v0.53d)* — synthetic B reachability=0.0 → priority 2 does NOT fire on this leg. Synthetic B reachability=0.015625 (1/64) → priority 2 ANCHOR_REPLICATION_HALT fires (categorical lock broken). Integer-categorical comparison.
15. **`test_c_widened_starting_energy_100_reachability_threshold_partition_at_tick_200`** — synthetic C reachability 0.20 / 0.30 × {PRESENT, PARTIAL, NOT_FOUND} → priorities 4/5/6 fire correctly.
16. **`test_rollup_locked_phrases_fire_verbatim_and_priority_cascade_partition_total`** — synthetic each priority-4/5/6 outcome → assert locked phrase contains diagnostic substring verbatim:
    - RESCUED: `"the (V0_25 × \`widened_gradient\`) reachability ceiling is bounded by the V0_25 founder starting-energy budget at the \`max_energy\` bound, not by the geometry alone"` AND `"WIDENED_BELOW_REACHABILITY_THRESHOLD_AT_TICK_200"` AND `"WIDENED_BELOW_REACHABILITY_THRESHOLD_UNDER_RELAXED_INFLUX"` (predecessor references to v0.53c and v0.53d).
    - BELOW_THRESHOLD: `"The bridge is not rescued by \`BodyConfig.starting_energy = 100\` under V0_25 × \`widened_gradient\` × N_TICKS=200"` AND `"WIDENED_BELOW_REACHABILITY_THRESHOLD_AT_TICK_200"` AND `"WIDENED_BELOW_REACHABILITY_THRESHOLD_UNDER_RELAXED_INFLUX"`.
    - PARTIALLY_RESCUED: `"reachability becomes measurable but the bridge does not fully replicate"` AND `"WIDENED_BELOW_REACHABILITY_THRESHOLD_AT_TICK_200"` AND `"WIDENED_BELOW_REACHABILITY_THRESHOLD_UNDER_RELAXED_INFLUX"`.
    Synthesize halt cascade (priorities 1 / 2.a / 2.b / 2.c / 3); assert priority order. Exhaustively iterate (C reachability ≥ 0.25, C sub-verdict ∈ {PRESENT, PARTIAL, NOT_FOUND}) ∪ (C reachability < 0.25); assert unique outcome per cell.

## Watch-outs (for future-Chronus)

- **Additive chamber-driver seam (one-time src/ touch).** Test #8 splits into Part A (science-core five files at v0.52b-tip SHA-256, unchanged) and Part B (chamber driver at v0.53e-tip SHA-256, locked at implementation time). Any future slice that re-touches `fear_hunger_chamber.py` must update Part B's pinned hash AND its locked failure message.
- **C_widened_starting_energy_100 is the primary gating arm.** A_null_V0_25 / B_widened_V0_25 tick-200 cells are descriptive (or anchor-gating only).
- **Tier-2 categorical anchor on B_widened_V0_25 is integer-categorical.** Compare to `0.0` exactly. Test #14 enforces.
- **`starting_energy=100` is the maximal legal one-knob founder-energy-budget increase under the existing `BodyConfig.max_energy=100` bound.** Anything stronger requires `max_energy` co-raised — that is a two-knob co-variation, deferred to v0.53g (or later).
- **Pool / ecology preserved.** Only `body_config` differs on C; `ambient_influx_rate=1.0`, `energy_pool_initial=1500.0`, `food_respawn_cooldown=50`, `child_funding_mode=PARENT_TRANSFER_POOL_GAP` all preserved at V0_25 baseline.
- **Three windows in parallel, single observer pass.** Per-tick observer must accumulate `pre50_*` / `pre100_*` / `pre200_*` AND snapshot `mean_distance_*_tick50` / `_tick100` / `_tick200` from a single iteration.
- **Three Label B variants.** tick-200 gates the C arm's sub-verdict.
- **Strict NaN-treated-as-non-firing rule preserved.** Test #12 enforces.
- **B and C are expected to diverge from tick-0** (unlike v0.53d). `starting_energy=100` perturbs founder body energy at agent-construction time. The byte-identity-with-B observation that surfaced in v0.53d will not recur on v0.53e regardless of rescue outcome — interpretation is cleaner in either direction.
- **`setup_observer` is read-only on `founder.body.energy` (and on every other founder body field).** The `starting_energy=100` change must propagate via the `body_config` parameter to `run_chamber()` at config-time founder construction, NOT via any post-construction body patch. v0.53e is a substrate-axis slice, not a v0.49-style founder-clamp intervention. Any future slice that wants to patch founder body fields at setup_observer time is a separate intervention slice and requires a fresh pre-reg with intervention framing.
- **C extinction trajectory is the open question.** B_widened_V0_25 is locked to full extinction (predecessor lock); C may extinct later, partially, or not at all under the maximum legal one-knob starting-energy boost. Population-stability metrics logged at all three windows.
- **Locked phrase discipline** verbatim where verdicts fire. The priority-4 / -5 / -6 phrases all explicitly reference v0.53c's `WIDENED_BELOW_REACHABILITY_THRESHOLD_AT_TICK_200` AND v0.53d's `WIDENED_BELOW_REACHABILITY_THRESHOLD_UNDER_RELAXED_INFLUX` by name.
- **No `geometry-fundamental` claims under priority 5.** The locked phrase explicitly bounds the verdict to `BodyConfig.starting_energy = 100` under V0_25 × `widened_gradient` × N_TICKS=200 and names v0.53f along `base_metabolic_cost` as the open-frame follow-up. Cautious framing per CLAUDE.md.
- **Determinism north star** ([[scripts/core_smoke_test.py]]) must continue to pass after the chamber-driver seam-add. The smoke test calls `run_chamber()` without `body_config=...` — the default-preserving fallback ensures byte-identity. CI smoke verifies.

## Files this slice will create / modify

- `docs/experiments/fear_hunger_v0.53e.md` (this file; Results section appended after reducer run)
- `src/hedonism_harness/experiments/fear_hunger_chamber.py` (one additive seam: `body_config: BodyConfig | None = None` parameter + default-preserving fallback at `body_cfg = ...`)
- `scripts/v0_53e_substrate_axis_starting_energy_audit.py` (new)
- `tests/test_v0_53e_substrate_axis_starting_energy_audit.py` (new, 16 tests)

No other `src/` modifications. No prior reducer / audit / test / pre-reg files modified.

## Results

(To be appended after the reducer run.)
