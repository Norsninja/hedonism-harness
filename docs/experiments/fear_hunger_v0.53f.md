# fear_hunger v0.53f — substrate-axis disambiguation: founder per-tick metabolic-cost rescue probe on `widened_gradient` × tick-200

**Slice:** v0.53f
**Type:** **first-class observational sweep** with 3-arm tick-200 reducer (no `src/` changes — the v0.53e `body_config` seam carries forward; no intervention; one-knob substrate variation on the C arm only; reuses existing named layouts).
**Predecessors:** v0.46–v0.52b (full predecessor stack), v0.53 (`BRIDGE_PARTIALLY_GENERALIZES`), v0.53b (`WIDENED_BELOW_REACHABILITY_THRESHOLD_AT_TICK_100`), v0.53c (`WIDENED_BELOW_REACHABILITY_THRESHOLD_AT_TICK_200`), v0.53d (`WIDENED_BELOW_REACHABILITY_THRESHOLD_UNDER_RELAXED_INFLUX` — doubled `ambient_influx_rate` was mechanically inert), v0.53e (`RELAXED_OPPOSITE_SIGN_HALT` — `BodyConfig.starting_energy=100` extended survival ~2× on `widened_gradient` but did not lift reachability; locked priority cascade fired on a measurement-edge wrong-sign cell at n=6 under reachability=0; methodological lesson logged to reachability-gate future opposite-sign halts).
**Question being asked (locked):** Is v0.53c / v0.53d / v0.53e's reachability-bound result on `widened_gradient` driven by the per-tick metabolic depletion rate? Specifically: does lowering `BodyConfig.base_metabolic_cost` from the V0_25 baseline of `0.25` to `0.10` (a 60% reduction; the orthogonal founder-facing budget axis to v0.53e's `starting_energy=100`), with all other V0_25 substrate parameters held identical, lift `widened_gradient` reachability above the locked 25% threshold at tick-200 AND admit a measurable v0.48 sensor_radius spatial / foraging bridge?

v0.53e's locked Results explicitly named **`base_metabolic_cost = 0.10`** as the v0.53f candidate: per-tick depletion rate is the orthogonal founder-facing budget axis to one-time starting energy. Where `starting_energy=100` extended the survival horizon at the same depletion rate, `base_metabolic_cost=0.10` slows the depletion rate at the same starting energy. At a 60% reduction, founders deplete energy ~2.5× more slowly per tick, providing ~2.5× the effective survival horizon at V0_25 baseline starting_energy=60.

The choice of `base_metabolic_cost=0.10` (rather than `0.05`, `0.15`, or other values) is locked pre-data on the following grounds: (i) it is a strong but not extreme dose — a 60% reduction is large enough to substantially perturb the survival equation but does not approach the floor (`base_metabolic_cost=0.0` would eliminate metabolism entirely, a regime change); (ii) at the V0_25 starting_energy=60 budget, lowering depletion by 60% gives founders runway comparable to v0.53e's starting_energy=100 boost (which scaled survival by ~2× at the V0_25 depletion rate); (iii) the dose is sufficiently aggressive that if even this fails to lift reachability, the bottleneck on `widened_gradient` is not founder per-tick depletion at any conservatively-defended dose.

If C_widened_metabolic_010 reachability ≥ 25% at tick-200 AND tick-200 sub-verdict resolves PRESENT, v0.53c / v0.53d / v0.53e's reachability ceiling on `widened_gradient` × V0_25 is bounded by founder per-tick metabolic depletion — the geometry-substrate cell admits measurement once founders deplete energy slowly enough to traverse the corridor. If reachability ≥ 25% AND tick-200 sub-verdict ∈ {PARTIAL, NOT_FOUND, OPPOSITE_SIGN_HALT}, the budget rescue admits measurement but the bridge fails to fully fire (or fires wrong-sign under measurable food access). If reachability < 25% at tick-200 even at 60%-reduced metabolic cost, the (V0_25 × `widened_gradient`) cell **is not rescued by `base_metabolic_cost=0.10` under N_TICKS=200** along the founder-facing budget axis; v0.53g (multi-knob co-variation: `starting_energy=100 + base_metabolic_cost=0.10` together) remains the natural follow-up.

## v0.53f's reachability-gated priority 3 — forward-looking design improvement informed by v0.53e

v0.53e's Results section logged a methodological lesson:

> "Future widened_gradient rescue slices should reachability-gate opposite-sign halts, or at minimum classify wrong-sign signals under reachability=0 separately from wrong-sign signals under measurable food access."

v0.53f incorporates this as **a forward-looking design improvement, NOT a retroactive correction to v0.53e**. v0.53e's locked priority cascade and locked phrases stand as historical contract per CLAUDE.md.

The improvement: priority 3 (`RELAXED_OPPOSITE_SIGN_HALT`) is now **reachability-gated** at tick-200:

```
Priority 3 fires iff:
    C tick-200 sub-verdict == OPPOSITE_SIGN_HALT
    AND
    c_reachability_run_share_tick_200 >= 0.25
```

If C tick-200 sub-verdict == OPPOSITE_SIGN_HALT AND `c_reachability_tick_200 < 0.25`: **priority 3 SKIPS**; rollup falls through to priority 5 (`WIDENED_BELOW_REACHABILITY_THRESHOLD_UNDER_BASE_METABOLIC_COST_010`). The wrong-sign cell(s) are logged descriptively in `audit_summary.csv` under a new `wrong_sign_cells_under_reachability_below_threshold` section and called out descriptively in Results — but they do not fire a halt.

The per-arm sub-verdict structure is **unchanged** (4-way: PRESENT / PARTIAL / NOT_FOUND / OPPOSITE_SIGN_HALT); the `OPPOSITE_SIGN_HALT` per-arm label retains its v0.53d/e meaning (any tick-200 wrong-sign cell exists for the arm). Only the rollup-level priority-3 trigger is reachability-gated. This is the minimum-change path that resolves the v0.53e edge-case without altering the predecessor sub-verdict structure shared across v0.53/b/c/d/e.

## Pre-implementation note (2026-05-09, before any reducer code)

The pre-reg's design was confirmed with the user before drafting:

- **3 arms (asymmetric).** A_null_V0_25 (tight_gradient, V0_25 substrate, anchor). B_widened_V0_25 (widened_gradient, V0_25 substrate; predecessor lock from v0.53c / v0.53d / v0.53e). C_widened_metabolic_010 (widened_gradient, V0_25 substrate **except** `BodyConfig.base_metabolic_cost=0.10`). Same 64-tuple corpus.
- **One BodyConfig knob, one dose.** Only `base_metabolic_cost` is varied on C, and only between V0_25 baseline (`0.25`) and the locked test dose (`0.10`, a 60% reduction). Multi-knob co-variation (`starting_energy=100 + base_metabolic_cost=0.10` together) is deferred to v0.53g contingent on v0.53f's outcome.
- **No `src/` modifications.** v0.53e's `body_config: BodyConfig | None = None` seam in `fear_hunger_chamber.py` carries forward. v0.53f exercises the seam — does not modify it. Test #8 pinning is identical to v0.53e: Part A (science-core five files at v0.52b-tip SHA-256) + Part B (chamber driver at v0.53e-tip SHA-256 `62d134c5d82b031a6fd2b7bbdf0412eb8362199c7bf60a59836cfca9134e2b6d`).
- **Reachability-gated priority 3 (NEW).** See section above. Methodological lesson from v0.53e applied as a forward-looking design improvement.
- **Tick-200 verdict gating.** Per-tick observer accumulates through tick-200 (canonical v0.53c / v0.53d / v0.53e three-window template). Three Label B variants (tick50 anchor / tick100 descriptive / tick200 verdict-gating) computed in parallel.
- **Tier-2 categorical anchor on B_widened_V0_25 preserved.** v0.53f re-locks B_widened_V0_25's reachability at tick-200 as `0/64` (the v0.53c / v0.53d / v0.53e categorical lock), exact integer comparison.
- **Pool / ecology / starting_energy preserved.** A, B, and C all retain V0_25 baseline `ambient_influx_rate=1.0`, `energy_pool_initial=1500.0`, `food_respawn_cooldown=50`, `child_funding_mode=PARENT_TRANSFER_POOL_GAP`, hazard_damage per (version, hazard) corpus row, AND `starting_energy=60.0` (v0.53e's `100` is NOT carried forward — v0.53f isolates the `base_metabolic_cost` axis). Only `body_config.base_metabolic_cost` differs on C.
- **Expected behavioral divergence between B and C from tick-0 onward.** `base_metabolic_cost=0.10` directly perturbs every per-tick metabolic depletion. The byte-identity-with-B observation that surfaced in v0.53d will not recur. Whether the divergence is large enough to cross reachability=0.25 is the open question.

## Conservation framing — observational, no `src/` changes, one-knob substrate variation on C only

- **No `src/` modifications.** v0.53e added the additive `body_config: BodyConfig | None = None` seam to `run_chamber()` in `fear_hunger_chamber.py`. v0.53f exercises this existing seam without modification. The five science-core files (`core/sensors.py`, `core/traits.py`, `core/body.py`, `core/config.py`, `experiments/layouts.py`) AND `experiments/fear_hunger_chamber.py` all remain byte-identical to their v0.53e-tip values. Test #8 enforces both pinning categories.
- **No modifications to prior reducer or audit scripts.** v0.34's `lineage_replay.py`, v0.35's `lineage_survival_replay.py`, v0.36's `trait_replay.py`, v0.48's reducer, v0.53 / v0.53b / v0.53c / v0.53d / v0.53e's reducers remain byte-identical to their merged forms.
- **A_null_V0_25 arm is byte-identical to v0.48 / v0.53 / v0.53b / v0.53c / v0.53d / v0.53e A_null path AT TICK-50.** Tier-1 re-anchor enforces this within 1e-3.
- **B_widened_V0_25 arm is byte-identical to v0.53 / v0.53b / v0.53c / v0.53d / v0.53e's B_widened arm at every tick 0..200.** Tier-2 categorical anchor enforces `b_widened_v025_reachability_run_share_tick_200 == 0.0`.
- **C_widened_metabolic_010 differs from B_widened_V0_25 only via `BodyConfig.base_metabolic_cost` (0.25 → 0.10).** All other BodyConfig fields preserved at default (`max_energy=100.0`, `starting_energy=60.0`, `starting_health=100.0`, `max_health=100.0`, `sensor_radius_metabolic_cost=0.05`, `effective_sensor_radius_override=None`). All other WorldConfig / ReproductionConfig / ActionConfig parameters identical to V0_25 baseline.
- **No intervention at any level on any arm.** No founder body trait modification post-construction, no override patching, no helper RNG, no shuffle, no clamp, no permutation. The `base_metabolic_cost=0.10` change is config-time, not setup-observer-time.

## Corpus (locked, 64 × 3 arms = 192 runs)

Same shape as v0.53 / v0.53b / v0.53c / v0.53d / v0.53e:

| version | seeds | hazards | runs per arm | total runs |
|---|---|---|---|---|
| v0.42 | 41..48 | {0, 8} | 16 | 48 |
| v0.43R | 49..56 | {0, 8} | 16 | 48 |
| v0.44 | 57..64 | {0, 8} | 16 | 48 |
| v0.45 | 65..72 | {0, 8} | 16 | 48 |
| **total** | | | | **192** |

V0_25 substrate identical to v0.53/b/c/d/e on A and B; C identical except `BodyConfig(base_metabolic_cost=0.10)`. Wall time estimate ~12–25 minutes total.

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

Byte-identical to v0.48 / v0.53 / v0.53b / v0.53c / v0.53d / v0.53e A_null path at every tick 0..200. Used for:
1. **Tier-1 anchor at tick-50** (against v0.48 / v0.53 / v0.53b / v0.53c / v0.53d / v0.53e published cells).
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

Byte-identical to v0.53 / v0.53b / v0.53c / v0.53d / v0.53e's B_widened arm at every tick 0..200. **Predecessor-lock arm for v0.53f**: the rollup gates on B_widened_V0_25's categorical reachability anchor, not on its sub-verdict.

### C_widened_metabolic_010

```
ChamberLayout = widened_gradient_layout()
ambient_influx_rate = 1.0  (V0_25 baseline)
energy_pool_initial = 1500.0  (V0_25 baseline)
food_respawn_cooldown = 50  (V0_25 baseline)
child_funding_mode = PARENT_TRANSFER_POOL_GAP  (V0_25 baseline)
hazard_damage = per (version, hazard) corpus row  (V0_25 baseline)
body_config = BodyConfig(base_metabolic_cost=0.10)
  (RELAXED — base_metabolic_cost lowered from V0_25 baseline 0.25 to 0.10,
   a 60% reduction; all other BodyConfig fields default,
   including starting_energy=60.0)
FounderSpec(traits_override=None)
```

Differs from B_widened_V0_25 by exactly one knob: `BodyConfig.base_metabolic_cost` (0.25 → 0.10). All other BodyConfig fields preserved at default. **The primary arm of v0.53f**: the verdict gates on C's tick-200 reachability and tick-200 sub-verdict.

## Labels (locked, two — with three Label B variants)

### Label A — `high_sensor_radius_lineage`

Identical to v0.48–v0.53e. Trait-resolved (`int(founder.body.traits.sensor_radius)`); tiebreak `min(lineage_id)`. Time-window-independent.

### Label B — three variants computed in parallel

Each is `argmax_lineage(tickN_above_threshold_fraction)` with the v0.47 3-tier tiebreak (fraction → count → min(lineage_id), NaN-loses):

- **`high_tick50_readiness_fraction_lineage`** — used for the Tier-1 anchor against v0.48 / v0.53 / v0.53b / v0.53c / v0.53d / v0.53e on the A arm.
- **`high_tick100_readiness_fraction_lineage`** — used for descriptive context (NOT gating).
- **`high_tick200_readiness_fraction_lineage`** — used for the v0.53f **verdict** on the C arm.

If at tick-N **no lineage has any agent above the readiness threshold** (everyone NaN or zero), Label B for that run is undefined; the per-run paired_d delta cells are `nan` and the per-arm cell's `n` decrements.

## Primary observables (locked, 3, computed at three windows)

| # | name pattern | windows | expected sign |
|---|---|---|:-:|
| 1 | `pre{N}_food_events_count` | N ∈ {50, 100, 200} | + |
| 2 | `pre{N}_food_energy_acquired` | N ∈ {50, 100, 200} | + |
| 3 | `mean_distance_to_nearest_food_cell_tick{N}` | N ∈ {50, 100, 200} | − |

Definitions / aggregation rules / NaN handling: copy-local from v0.48–v0.53e.

## Effect-size rule (locked, sign-aware, identical to v0.48–v0.53e)

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

c_widened_metabolic_010_reachability_run_share_tick_200 =
    fraction of C_widened_metabolic_010 runs where at least one
    founder lineage has pre200_food_events_count > 0
```

Domain: 64 runs per arm. Threshold: **`B_REACHABILITY_THRESHOLD = 0.25`** (preserved from v0.53b / v0.53c / v0.53d / v0.53e).

The B_widened_V0_25 metric is the Tier-2 categorical predecessor anchor (must equal `0.0` exactly, i.e., `0/64`). The C_widened_metabolic_010 metric is the verdict-gating reachability AND the priority-3 reachability gate.

## Population-stability and degenerate-label descriptive metrics (locked, pre-data, per arm × window)

Identical structure to v0.53c / v0.53d / v0.53e:

```
arm_living_population_run_share_tick_N
arm_label_a_n_runs_tick_N
arm_label_b_n_runs_tick_N
```

Descriptive only — no halt or outcome gates on them directly. Reported in Results.

## Per-arm sub-verdicts (locked, 4-way each — UNCHANGED from v0.53d / v0.53e)

| condition | A_null_V0_25 (tick-200) | B_widened_V0_25 (tick-200) | C_widened_metabolic_010 (tick-200) |
|---|---|---|---|
| both labels clear ≥ 2/3 of the three locked cells, with NaN treated as non-firing, 0 wrong-sign | `A_NULL_V025_TICK200_BRIDGE_PRESENT` | `B_WIDENED_V025_TICK200_BRIDGE_PRESENT` | `C_METABOLIC_010_TICK200_BRIDGE_PRESENT` |
| exactly one label clears ≥ 2/3 of the three locked cells, with NaN treated as non-firing, 0 wrong-sign | `A_NULL_V025_TICK200_BRIDGE_PARTIAL` | `B_WIDENED_V025_TICK200_BRIDGE_PARTIAL` | `C_METABOLIC_010_TICK200_BRIDGE_PARTIAL` |
| neither label clears ≥ 2/3 of the three locked cells, with NaN treated as non-firing, 0 wrong-sign | `A_NULL_V025_TICK200_BRIDGE_NOT_FOUND` | `B_WIDENED_V025_TICK200_BRIDGE_NOT_FOUND` | `C_METABOLIC_010_TICK200_BRIDGE_NOT_FOUND` |
| any primary signed_d ≤ −0.5 under either label | `A_NULL_V025_TICK200_OPPOSITE_SIGN_HALT` | `B_WIDENED_V025_TICK200_OPPOSITE_SIGN_HALT` | `C_METABOLIC_010_TICK200_OPPOSITE_SIGN_HALT` |

**The per-arm `OPPOSITE_SIGN_HALT` label retains its v0.53d / v0.53e meaning** (any tick-200 wrong-sign cell exists for the arm). Whether the rollup escalates to priority-3 `RELAXED_OPPOSITE_SIGN_HALT` is now reachability-gated — see "Slice rollup verdicts" below.

**Strict NaN-treated-as-non-firing rule preserved from v0.48–v0.53e.**

## Slice rollup verdicts (locked, 6 outcomes, priority-ordered — PRIORITY 3 IS NOW REACHABILITY-GATED)

Priority order (first-matching wins). The non-halt outcomes (priorities 4–6) gate **only on C_widened_metabolic_010**.

1. `CORPUS_REDERIVE_DRIFT_HALT`
2. `ANCHOR_REPLICATION_HALT`
3. `RELAXED_OPPOSITE_SIGN_HALT` (**reachability-gated** — fires iff C sub-verdict = OPPOSITE_SIGN_HALT AND `c_reachability_tick_200 ≥ 0.25`)
4. `WIDENED_BRIDGE_RESCUED_BY_BASE_METABOLIC_COST_010`
5. `WIDENED_BELOW_REACHABILITY_THRESHOLD_UNDER_BASE_METABOLIC_COST_010`
6. `WIDENED_BRIDGE_PARTIALLY_RESCUED_BY_BASE_METABOLIC_COST_010`

### Halt conditions

| priority | rollup verdict | trigger | locked phrase (verbatim) |
|---|---|---|---|
| 1 | `CORPUS_REDERIVE_DRIFT_HALT` | A_null_V0_25 arm `a_share_h8` for any of v0.42 / v0.44 / v0.45 drifts > 1e-3 from the published reference | "Halt: A_null_V0_25 re-anchor drifted from the published Results value for {version}; v0.53f's deterministic re-execution of the V0_25 corpus does not reproduce the published metric within 1e-3." |
| 2 | `ANCHOR_REPLICATION_HALT` | (a) A_null_V0_25 tick-50 signed_d for any of the six v0.48 / v0.53 / v0.53b / v0.53c / v0.53d / v0.53e cells drifts > 1e-3 from the published value, OR (b) A_null_V0_25 tick-50 sub-verdict ≠ PRESENT, OR (c) `b_widened_v025_reachability_run_share_tick_200` ≠ `0.0` (any B_widened_V0_25 run with `pre200_food_events_count > 0` for any lineage, contradicting v0.53c / v0.53d / v0.53e's `0/64` lock) | "Halt: v0.53f's A_null_V0_25 arm does not reproduce v0.48 / v0.53 / v0.53b / v0.53c / v0.53d / v0.53e's tick-50 spatial bridge, OR v0.53f's B_widened_V0_25 arm does not reproduce v0.53c / v0.53d / v0.53e's `0/64` reachability lock at tick-200. v0.53f cannot interpret the C_widened_metabolic_010 cells without an established baseline on the V0_25 substrate." |
| 3 | `RELAXED_OPPOSITE_SIGN_HALT` (**reachability-gated**) | C_widened_metabolic_010 tick-200 sub-verdict = `C_METABOLIC_010_TICK200_OPPOSITE_SIGN_HALT` (any wrong-sign cell) **AND** `c_widened_metabolic_010_reachability_run_share_tick_200 ≥ 0.25` | "Halt: a v0.53f C_widened_metabolic_010 tick-200 spatial / foraging primary fires in the WRONG direction under a gating label, AND C reachability at tick-200 clears the locked 25% threshold (so the bridge framework is meaningful at this measurement). Lowering `BodyConfig.base_metabolic_cost` from V0_25 baseline `0.25` to `0.10` on the `widened_gradient` layout surfaces a regime where the locked expected signs do not hold under measurable food access. The reachability-gated trigger preserves v0.53e's locked sign discipline while excluding the v0.53e-style measurement-edge case (wrong-sign at reachability=0)." |

### Tier-1 (priority 2.a) re-anchor — A_null_V0_25 tick-50 cells

Identical six cells to v0.48 / v0.53 / v0.53b / v0.53c / v0.53d / v0.53e:

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

Locked from v0.53c / v0.53d / v0.53e's measured result.

### Outcome conditions (only consulted if no halt fires)

| priority | rollup verdict | trigger | locked phrase (verbatim) |
|---|---|---|---|
| 4 | `WIDENED_BRIDGE_RESCUED_BY_BASE_METABOLIC_COST_010` | `c_widened_metabolic_010_reachability_run_share_tick_200 ≥ 0.25` AND C_widened_metabolic_010 tick-200 sub-verdict = `C_METABOLIC_010_TICK200_BRIDGE_PRESENT` | "On the modern A_null corpus with the V0_25 substrate held constant except for `BodyConfig.base_metabolic_cost = 0.10` (a 60% reduction from the V0_25 baseline of `0.25` per tick) on `widened_gradient`, the v0.48 sensor_radius spatial / foraging bridge fires PRESENT under the locked +0.5 paired_d threshold at tick-200. The geometry/substrate cell that v0.53c locked as `WIDENED_BELOW_REACHABILITY_THRESHOLD_AT_TICK_200`, v0.53d locked as `WIDENED_BELOW_REACHABILITY_THRESHOLD_UNDER_RELAXED_INFLUX`, and v0.53e locked as `RELAXED_OPPOSITE_SIGN_HALT` (with extended-survival-without-reachability secondary finding) admits a measurable bridge under the relaxed-metabolic-cost envelope: B_widened_V0_25 reachability remains `0/64` at tick-200 (predecessor lock holds), C_widened_metabolic_010 reachability clears the locked 25% threshold, and ≥ 2/3 spatial / foraging primaries fire PRESENT under both gating labels. The (V0_25 × `widened_gradient`) reachability ceiling is bounded by the V0_25 founder per-tick metabolic depletion rate, not by the geometry alone: `WIDENED_BRIDGE_RESCUED_BY_BASE_METABOLIC_COST_010`." |
| 5 | `WIDENED_BELOW_REACHABILITY_THRESHOLD_UNDER_BASE_METABOLIC_COST_010` | `c_widened_metabolic_010_reachability_run_share_tick_200 < 0.25` | "On the modern A_null corpus with the V0_25 substrate held constant except for `BodyConfig.base_metabolic_cost = 0.10` (a 60% reduction from the V0_25 baseline of `0.25` per tick) on `widened_gradient`, fewer than 25% of C_widened_metabolic_010 runs have any founder lineage with pre200 food events. C_widened_metabolic_010's reachability is below the locked 25% threshold at tick-200; the geometry/substrate cell that v0.53c locked as `WIDENED_BELOW_REACHABILITY_THRESHOLD_AT_TICK_200`, v0.53d locked as `WIDENED_BELOW_REACHABILITY_THRESHOLD_UNDER_RELAXED_INFLUX`, and v0.53e locked as `RELAXED_OPPOSITE_SIGN_HALT` remains below the reachability threshold under the relaxed-metabolic-cost envelope. The bridge is not rescued by `BodyConfig.base_metabolic_cost = 0.10` under V0_25 × `widened_gradient` × N_TICKS=200; v0.53g multi-knob co-variation (`starting_energy=100 + base_metabolic_cost=0.10` together) remains the natural follow-up: `WIDENED_BELOW_REACHABILITY_THRESHOLD_UNDER_BASE_METABOLIC_COST_010`." |
| 6 | `WIDENED_BRIDGE_PARTIALLY_RESCUED_BY_BASE_METABOLIC_COST_010` | `c_widened_metabolic_010_reachability_run_share_tick_200 ≥ 0.25` AND C_widened_metabolic_010 tick-200 sub-verdict ∈ {`C_METABOLIC_010_TICK200_BRIDGE_PARTIAL`, `C_METABOLIC_010_TICK200_BRIDGE_NOT_FOUND`} | "On the modern A_null corpus with the V0_25 substrate held constant except for `BodyConfig.base_metabolic_cost = 0.10` (a 60% reduction from the V0_25 baseline of `0.25` per tick) on `widened_gradient`, C_widened_metabolic_010's reachability clears the locked 25% threshold at tick-200 but the v0.48 sensor_radius spatial / foraging bridge does not fully fire PRESENT — fewer than 2/3 primaries fire across both gating labels at tick-200 under the strict NaN rule. The geometry/substrate cell that v0.53c locked as `WIDENED_BELOW_REACHABILITY_THRESHOLD_AT_TICK_200`, v0.53d locked as `WIDENED_BELOW_REACHABILITY_THRESHOLD_UNDER_RELAXED_INFLUX`, and v0.53e locked as `RELAXED_OPPOSITE_SIGN_HALT` is partially rescued under the relaxed-metabolic-cost envelope: reachability becomes measurable but the bridge does not fully replicate. Layout-specific partial-rescue logged in Results: `WIDENED_BRIDGE_PARTIALLY_RESCUED_BY_BASE_METABOLIC_COST_010`." |

The rollup is **categorical-only**.

The 3 non-halt outcomes form a total partition of (C reachability ≥ 0.25, C sub-verdict ∈ {PRESENT, PARTIAL, NOT_FOUND, OPPOSITE_SIGN_HALT}) ∪ (C reachability < 0.25). Note: under the reachability-gated priority-3 trigger:
- **C reachability ≥ 0.25 AND C sub-verdict = OPPOSITE_SIGN_HALT** → priority 3 fires (halt).
- **C reachability ≥ 0.25 AND C sub-verdict ∈ {PRESENT}** → priority 4 fires.
- **C reachability ≥ 0.25 AND C sub-verdict ∈ {PARTIAL, NOT_FOUND}** → priority 6 fires.
- **C reachability < 0.25** → priority 5 fires (regardless of C sub-verdict, including OPPOSITE_SIGN_HALT — wrong-sign cells logged descriptively but no halt).

Test #16 enforces the partition exhaustively, including both branches of the reachability-gated priority-3 trigger.

## Cautious framing (per CLAUDE.md)

- "**Bridge rescued by relaxed metabolic cost at the 0.10 dose**", "**reachability ceiling bounded by the V0_25 founder per-tick metabolic depletion rate, not by the geometry alone**", "**bridge is not rescued by `BodyConfig.base_metabolic_cost = 0.10` under V0_25 × widened_gradient × N_TICKS=200**" — NOT "**proves**", "**causes**", or "**rules out**".
- "**Tested relaxed-metabolic-cost envelope**" specifically means `base_metabolic_cost ∈ {0.25 (V0_25 baseline), 0.10 (v0.53f test dose)}` at `N_TICKS=200`. v0.53f does NOT establish behavior at intermediate doses, behavior at lower doses, or behavior under multi-knob co-variation; those require separate slices.
- "**Reachability-gated priority 3**" means the locked sign discipline is preserved under measurable food access (reachability ≥ 0.25); under reachability < 0.25 the wrong-sign signal is logged descriptively. This is a forward-looking design improvement informed by v0.53e Results, NOT a retroactive correction.
- v0.53f explicitly does not establish: cross-layout generalization beyond the three v0.53 layouts, mechanism for any rescue or non-rescue outcome, generalization to non-V0_25 substrates beyond the metabolic-cost axis, behavior at `n_ticks > 200`, causal contribution per layout (Reading-A causal-generalization slice remains the deferred candidate).

## What v0.53f cannot establish (logged here pre-data, not retrofittable)

- ✗ **"`widened_gradient` is geometry-fundamental"** if priority 5 fires. v0.53f tests V0_25 substrate × `BodyConfig.base_metabolic_cost=0.10` × N_TICKS=200 only. Multi-knob founder-budget co-variations (e.g., `starting_energy=100 + base_metabolic_cost=0.10` together) remain untested. v0.53g remains the natural follow-up if priority 5 fires.
- ✗ **"The bridge IS or IS NOT load-bearing on `widened_gradient`"** under any priority-4/5/6 outcome. The observation tells us about reachability and bridge-firing under one substrate axis variation; it does not establish channel-level causal contribution.
- ✗ **A revised v0.53 / v0.53b / v0.53c / v0.53d / v0.53e verdict.** All five stand as historical contracts.
- ✗ **Mechanism behind any rescue or non-rescue outcome.** Population dynamics under V0_25 × `widened_gradient` × `base_metabolic_cost=0.10` are descriptively logged; no mechanism is formally established.
- ✗ **Generalization beyond the tested arms.** The verdict is bounded to (`tight_gradient` × V0_25, `widened_gradient` × V0_25, `widened_gradient` × V0_25 with `base_metabolic_cost=0.10`) at `N_TICKS=200`.

## Open framing (NOT in v0.53f primary)

- **v0.53g — multi-knob founder-budget co-variation.** Triggered if v0.53f fires priority 5 (or partial-rescue). Could test `starting_energy=100 + base_metabolic_cost=0.10` together; or test variants like `starting_energy + max_energy` co-raised to e.g., `120` along with the metabolic reduction. Independent observational slice.
- **v0.53h (or later) — investigate the C_food_ladder Label B degradation trajectory.** Per-tick-window paired_d trajectory probe. Independent of v0.53f outcome.
- **v0.53i (or later) — Reading-A causal-generalization slice on layouts admitting the bridge.**
- **v0.54 — joint ablation** (zero-cost AND shuffle).
- **Eventual fresh-stream calibration** on the v0.46–v0.53f conclusion stack — needed for any "mechanism" declaration.

## Re-anchor (locked — Tier-1 and corpus only at tick-50)

| version | published `a_share_h8` |
|---|---|
| v0.42 | 0.652 |
| v0.43R | NOT PUBLISHED (informational-only) |
| v0.44 | 0.878 |
| v0.45 | 0.818 |

A_null_V0_25 arm only gates the corpus rollup.

## Outputs (locked)

```
runs/v0.53f-substrate-axis-base-metabolic-cost-010/per_run_per_lineage_v053f.csv
  columns: arm, layout_name, body_base_metabolic_cost, version, seed, hazard, run_id, lineage_id,
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

runs/v0.53f-substrate-axis-base-metabolic-cost-010/audit_summary.csv
  (includes a new `wrong_sign_cells_under_reachability_below_threshold` section
   when C reachability < 0.25 AND any C tick-200 cell has signed_d ≤ −0.5;
   each row records (arm, label, observable, paired_d, signed_d, n) for the
   wrong-sign cell as a descriptive non-halting log)

runs/v0.53f-substrate-axis-base-metabolic-cost-010/audit_log.txt
```

## Implementation plan (locked)

1. **No `src/` changes.** v0.53e's `body_config: BodyConfig | None = None` seam in `run_chamber()` carries forward and supports v0.53f's BodyConfig override directly.
2. Fresh script `scripts/v0_53f_substrate_axis_base_metabolic_cost_audit.py`. CLI: `uv run python scripts/v0_53f_substrate_axis_base_metabolic_cost_audit.py [--out-dir runs/v0.53f-substrate-axis-base-metabolic-cost-010]`.
3. Per (version, seed, hazard) tuple, run **3 arms**. A and B pass `body_config=None`; C passes `body_config=BodyConfig(base_metabolic_cost=0.10)`.
4. Setup_observer order (matches v0.53c / v0.53d / v0.53e merged implementation): (a) capture v0.53f founder audit table including `body.energy` AND `body.config.base_metabolic_cost` at tick 0 (verifies the seam wired the BodyConfig override correctly), (b) wire event listeners, (c) read back `model.world.width` and assert layout match per-arm, (d) capture tick-0 snapshot.
5. Per-tick observer accumulates `pre50_*` / `pre100_*` / `pre200_*` rollups in parallel.
6. Use the relaxed contiguous-prefix tick-records invariant from v0.53b / v0.53c / v0.53d / v0.53e.
7. Aggregate per-lineage primaries at all three windows. Compute Label A and three Label B variants.
8. Compute paired_d per (arm, gating-label, observable, window) cell. 18 cells per window × 3 windows = 54 cells total.
9. Compute per-arm reachability_run_share at all three windows. The B_widened_V0_25 tick-200 value is the Tier-2 categorical anchor. The C_widened_metabolic_010 tick-200 value is the verdict-gating reachability AND the priority-3 reachability gate.
10. Compute per-arm population-stability metrics.
11. **Tier-1 bridge re-anchor** (priority 2.a / 2.b): A_null_V0_25 arm's six tick-50 cells vs v0.48 / v0.53 / v0.53b / v0.53c / v0.53d / v0.53e published; halt if drift > 1e-3 OR if A_null_V0_25 tick-50 sub-verdict ≠ PRESENT.
12. **Tier-2 categorical anchor** (priority 2.c): `b_widened_v025_reachability_run_share_tick_200 == 0.0` exactly.
13. **Corpus re-anchor** (priority 1): A_null_V0_25 arm only; halt if `a_share_h8` for v0.42 / v0.44 / v0.45 drifts > 1e-3.
14. **Reachability-gated relaxed opposite-sign halt** (priority 3): scan all C_widened_metabolic_010 tick-200 gating-label cells; **if** any signed_d ≤ −0.5 **AND** `c_reachability_tick_200 ≥ 0.25` → halt loud. **Otherwise** (wrong-sign exists but reachability < 0.25): log descriptively in `audit_summary.csv` under `wrong_sign_cells_under_reachability_below_threshold`; do NOT halt. Fall through to priority 4/5/6 evaluation.
15. Compute slice rollup verdict per the locked priority + (C reachability tick-200, C sub-verdict tick-200) decision matrix; print + write the locked phrase verbatim.

The reducer is fully self-contained: it reads no `runs/` artifacts. Wall time estimate ~12–25 minutes for 192 runs.

## Test list (locked, 16 tests; extends v0.53e's pattern with reachability-gated priority-3 test)

`tests/test_v0_53f_substrate_axis_base_metabolic_cost_audit.py`:

1. **`test_paired_d_function_reproduces_hand_computed_signed_d_on_fixture_and_tier1_constants_match_v048_published_values`** *(re-anchor test, two-part)*.
2. **`test_a_null_v025_corpus_a_share_h8_re_anchors_v042_v044_v045`** — drift halt fires if any drift > 1e-3.
3. `test_arm_a_null_v025_uses_tight_gradient_layout_and_default_body_config` — chamber driver receives `tight_gradient_layout()` AND `body_config=None`; layout invariant assert.
4. `test_arm_b_widened_v025_uses_widened_gradient_layout_and_default_body_config` — chamber driver receives `widened_gradient_layout()` AND `body_config=None`; layout invariant assert.
5. **`test_arm_c_widened_metabolic_010_seam_differentiates_b_and_c_body_metabolic_cost_at_tick_0`** *(cross-arm contrast — verifies the `body_config` seam took effect at config-time founder construction)* — for the same (version, seed, hazard) tuple under matched RNG streams, assert:
   - **B_widened_V0_25 founder `body.config.base_metabolic_cost` at tick-0 == `0.25`** (V0_25 baseline from the default `BodyConfig()` fallback). Founder `body.energy` at tick-0 == `60.0`.
   - **C_widened_metabolic_010 founder `body.config.base_metabolic_cost` at tick-0 == `0.10`** (overridden via `body_config=BodyConfig(base_metabolic_cost=0.10)`). Founder `body.energy` at tick-0 == `60.0` (V0_25 baseline preserved — only `base_metabolic_cost` differs).
   - Both arms use `widened_gradient_layout()`; the only configured difference is `body_config.base_metabolic_cost`.
   - For C, explicitly assert that no other `BodyConfig` field differs from default (`max_energy=100.0`, `starting_energy=60.0`, `starting_health=100.0`, `max_health=100.0`, `sensor_radius_metabolic_cost=0.05`, `effective_sensor_radius_override=None`) AND no other WorldConfig knob differs from V0_25 baseline.
   - Founder body fields are read (not written) via `setup_observer` snapshot at tick-0.
6. **`test_founder_traits_byte_identical_across_arms_for_same_seed`**.
7. **`test_founder_positions_byte_identical_across_arms_for_same_seed`**.
8. **`test_no_src_modifications_compared_to_v0_53e_tip`** *(two-part src/ pinning test, IDENTICAL to v0.53e's test #8)*:
   Part A: SHA-256 of five science-core files match v0.52b-tip values exactly. Failure message verbatim: `"v0.53f is pre-registered to leave the science-core five files byte-identical to v0.52b-tip; update the pre-reg before changing src/core or src/experiments/layouts."`
   Part B: SHA-256 of `src/hedonism_harness/experiments/fear_hunger_chamber.py` matches the v0.53e-tip post-seam-add value `62d134c5d82b031a6fd2b7bbdf0412eb8362199c7bf60a59836cfca9134e2b6d`. Failure message verbatim: `"v0.53f is pre-registered to leave the chamber driver byte-identical to its v0.53e-tip hash; update the pre-reg before re-touching the chamber driver."`
9. `test_label_a_high_sensor_radius_lineage_picks_correct_lineage`.
10. **`test_label_b_three_variants_three_tier_tiebreak_at_each_window`**.
11. **`test_pre200_window_strictly_extends_pre100_and_pre50_windows`** — synthetic events at ticks 10/30/60/90/130/180/200; assert counts 2/4/7.
12. **`test_subverdict_present_requires_two_thirds_firing_cells_with_nan_treated_as_non_firing_strict`**.
13. **`test_priority_3_relaxed_opposite_sign_halt_is_reachability_gated`** *(NEW vs v0.53e — exercises both branches of the reachability-gated trigger)*:
    - **Branch A**: synthetic C tick-200 sub-verdict = OPPOSITE_SIGN_HALT (any wrong-sign cell, e.g., signed_d = −0.5 on Label A distance) AND `c_reachability_tick_200 = 0.30` (≥ 0.25) → priority 3 fires; rollup verdict = `RELAXED_OPPOSITE_SIGN_HALT`; locked priority-3 phrase substring verified.
    - **Branch B**: synthetic C tick-200 sub-verdict = OPPOSITE_SIGN_HALT (same wrong-sign cell) AND `c_reachability_tick_200 = 0.20` (< 0.25) → priority 3 does NOT fire; rollup verdict = `WIDENED_BELOW_REACHABILITY_THRESHOLD_UNDER_BASE_METABOLIC_COST_010` (priority 5); the wrong-sign cell is recorded in `audit_summary.csv` under `wrong_sign_cells_under_reachability_below_threshold` (test asserts the section exists and contains the (arm, label, observable, paired_d, signed_d, n) row); locked priority-5 phrase substring verified.
    - **Branch C**: synthetic C tick-200 sub-verdict = PRESENT AND `c_reachability_tick_200 = 0.30` → priority 4 fires (sanity check that priority 3 doesn't fire when sub-verdict isn't OPPOSITE_SIGN_HALT).
14. **`test_b_widened_v025_categorical_anchor_at_tick_200`** *(Tier-2 anchor test, preserved from v0.53d / v0.53e)* — synthetic B reachability=0.0 → priority 2 does NOT fire on this leg. Synthetic B reachability=1/64=0.015625 → priority 2 ANCHOR_REPLICATION_HALT fires.
15. **`test_c_widened_metabolic_010_reachability_threshold_partition_at_tick_200`** — synthetic C reachability 0.20 / 0.30 × {PRESENT, PARTIAL, NOT_FOUND} → priorities 4/5/6 fire correctly. (OPPOSITE_SIGN_HALT branches covered in test #13.)
16. **`test_rollup_locked_phrases_fire_verbatim_and_priority_cascade_partition_total`** — synthetic each priority-3/4/5/6 outcome → assert locked phrase contains diagnostic substring verbatim:
    - Priority 3 (RELAXED_OPPOSITE_SIGN_HALT, **reachability-gated**): `"AND C reachability at tick-200 clears the locked 25% threshold (so the bridge framework is meaningful at this measurement)"` AND `"The reachability-gated trigger preserves v0.53e's locked sign discipline while excluding the v0.53e-style measurement-edge case (wrong-sign at reachability=0)"`.
    - Priority 4 RESCUED: `"the (V0_25 × \`widened_gradient\`) reachability ceiling is bounded by the V0_25 founder per-tick metabolic depletion rate, not by the geometry alone"` AND substring references to v0.53c, v0.53d, v0.53e verdict names.
    - Priority 5 BELOW_THRESHOLD: `"The bridge is not rescued by \`BodyConfig.base_metabolic_cost = 0.10\` under V0_25 × \`widened_gradient\` × N_TICKS=200"` AND substring references to v0.53c, v0.53d, v0.53e verdict names.
    - Priority 6 PARTIALLY_RESCUED: `"reachability becomes measurable but the bridge does not fully replicate"` AND substring references to v0.53c, v0.53d, v0.53e verdict names.
    Synthesize halt cascade (priorities 1 / 2.a / 2.b / 2.c / 3); assert priority order. Exhaustively iterate (C reachability ≥ 0.25, C sub-verdict ∈ {PRESENT, PARTIAL, NOT_FOUND, OPPOSITE_SIGN_HALT}) ∪ (C reachability < 0.25, C sub-verdict ∈ {PRESENT, PARTIAL, NOT_FOUND, OPPOSITE_SIGN_HALT}); assert unique outcome per cell. Verify the reachability-gated priority-3 trigger collapses (C reachability < 0.25, OPPOSITE_SIGN_HALT) into priority 5 along with the other low-reachability cells.

## Watch-outs (for future-Chronus)

- **No `src/` changes.** v0.53e's seam carries forward; v0.53f exercises it. Test #8 pins both science-core five files (at v0.52b-tip) AND chamber driver (at v0.53e-tip) byte-identically.
- **C_widened_metabolic_010 is the primary gating arm.** A_null_V0_25 / B_widened_V0_25 tick-200 cells are descriptive (or anchor-gating only).
- **Reachability-gated priority 3.** This is the v0.53f methodological improvement vs v0.53d / v0.53e. Wrong-sign cells under C reachability < 0.25 are logged descriptively in `audit_summary.csv` and do NOT fire a halt; the rollup falls through to priority 5. Wrong-sign cells under C reachability ≥ 0.25 fire priority 3 as before. Test #13 exercises both branches.
- **Per-arm sub-verdict structure unchanged (4-way).** The `OPPOSITE_SIGN_HALT` per-arm label retains its v0.53d / v0.53e meaning (any wrong-sign cell). Only the rollup-level priority-3 trigger is reachability-gated. This is the minimum-change path that preserves predecessor sub-verdict structure.
- **Tier-2 categorical anchor on B_widened_V0_25 is integer-categorical.** Compare to `0.0` exactly. Test #14 enforces.
- **Pool / ecology / starting_energy preserved.** Only `body_config.base_metabolic_cost` differs on C. v0.53e's `starting_energy=100` is NOT carried forward — v0.53f isolates the metabolic-cost axis.
- **Three windows in parallel, single observer pass.**
- **Three Label B variants.** tick-200 gates the C arm's sub-verdict.
- **Strict NaN-treated-as-non-firing rule preserved.**
- **B and C are expected to diverge from tick-0 onward.** `base_metabolic_cost=0.10` directly perturbs every per-tick metabolic depletion.
- **C extinction trajectory is the open question.** B_widened_V0_25 is locked to full extinction at tick-200 (predecessor lock); v0.53e showed `starting_energy=100` extended C's survival to ~9% alive at tick-200. v0.53f's `base_metabolic_cost=0.10` (orthogonal axis) may produce a different trajectory.
- **Locked phrase discipline** verbatim where verdicts fire. The priority-3 / -4 / -5 / -6 phrases all explicitly reference v0.53c / v0.53d / v0.53e by name where appropriate.
- **No `geometry-fundamental` claims under priority 5.** The locked phrase explicitly bounds the verdict to `BodyConfig.base_metabolic_cost = 0.10` under V0_25 × `widened_gradient` × N_TICKS=200 and names v0.53g (multi-knob co-variation) as the open-frame follow-up.
- **Methodological improvement vs retroactive correction.** v0.53f's reachability-gated priority 3 is a forward-looking design improvement informed by v0.53e Results. v0.53e's locked priority cascade and locked phrases stand unchanged as historical contract.
- **Determinism north star** ([[scripts/core_smoke_test.py]]) must continue to pass. v0.53f makes no `src/` changes.

## Files this slice will create / modify

- `docs/experiments/fear_hunger_v0.53f.md` (this file; Results section appended after reducer run)
- `scripts/v0_53f_substrate_axis_base_metabolic_cost_audit.py` (new)
- `tests/test_v0_53f_substrate_axis_base_metabolic_cost_audit.py` (new, 16 tests)

No `src/` modifications. No prior reducer / audit / test / pre-reg files modified.

## Results

(To be appended after the reducer run.)
