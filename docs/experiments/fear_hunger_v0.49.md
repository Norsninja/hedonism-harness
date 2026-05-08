# fear_hunger v0.49 — sensor_radius causal probe (clamp + permutation)

**Slice:** v0.49
**Type:** **first-class intervention** (NOT a post-hoc reducer); founder-time `sensor_radius` clamp + permutation arms.
**Predecessors:** v0.21..v0.27 (substrate / aggregate-optimum), v0.34..v0.36 (lineage observability + heritability), v0.42..v0.45 (substrate-causal arc), v0.46 (`READINESS_PREDICTS_DOMINANCE`), v0.47 (`READINESS_TRAITS_PARTIALLY_PREDICTIVE`: founder `sensor_radius` is the only firing primary trait predicting tick-50 readiness fraction), v0.48 (`SENSOR_RADIUS_SPATIAL_BRIDGE_PRESENT`: 3/3 spatial / foraging primaries fire under both `high_sensor_radius_lineage` (label A) and `high_tick50_readiness_fraction_lineage` (label B); AND-gate satisfied cleanly).
**Question being asked (locked):** If the founder-level `sensor_radius` distribution is removed (clamp) or reassigned (permutation) at tick 0, does the v0.48 pre-50 spatial / foraging bridge persist, weaken, reverse, or disappear?

v0.46–v0.48 are observational decompositions over the modern A_null corpus. v0.48's `_PRESENT` verdict is correlational — it cannot distinguish "founder `sensor_radius` is causal for the spatial bridge" from "founder `sensor_radius` is correlated with some other founder feature (position, trait covariance, lineage luck) that drives the bridge". v0.49 is the **first interventional probe**: it manipulates the founder `sensor_radius` distribution at tick 0 (before any agent step) and observes whether the locked v0.48 paired_d cells continue to clear the +0.5 threshold under the same observables and labels.

## Pre-implementation correction (2026-05-08, before any reducer code)

The original pre-reg draft specified the intervention via `FounderSpec.traits_override` plus a helper RNG (`np.random.default_rng(seed)`) to pre-draw founder trait vectors. This is **not single-channel** and was caught at design review before any code was written. Recorded here for the historical record (per CLAUDE.md "pre-reg stands as the historical record"). No data has been seen yet.

**The bug.** `HHModel._spawn_founder` (model.py:355) draws each founder's traits via `random_traits(self.trait_config, self.streams.mutation)`, then calls `spawn_agent_rng(self.streams.mutation)` for the agent's per-agent RNG (model.py:377). When `traits_override` is supplied, `random_traits(...)` is skipped — but `spawn_agent_rng(...)` is still consumed. So `streams.mutation` reaches a *different* state at the start of the second founder's construction in B/C than under A_null. Every downstream `streams.mutation` consumer (subsequent founders' agent_rngs, every `mutate_traits` call during reproduction) thus diverges from A_null even before tick 0. That makes B/C multi-channel interventions: they vary founder `sensor_radius` AND every per-agent / per-mutation RNG draw thereafter.

The helper-RNG path was also not equivalent to A_null's draws: A_null draws traits from `streams.mutation`, while the helper used `np.random.default_rng(seed)` directly. So even the "non-`sensor_radius` fields" the helper produced were not the values A_null would have produced for the same (version, seed, hazard) tuple.

**The fix (locked).** All arms construct founders through the normal A_null path with `traits_override=None`. `HHModel` draws founder traits and agent RNGs exactly as A_null. **For B / C only**, the v0.49 reducer applies a **pre-tick-0 founder-body trait patch inside its `setup_observer` callback**, after `HHModel(...)` returns and before any `model.step()` runs. The patch is delivered as:

```python
# Read original traits from the live founder bodies.
original_traits = agent.body.traits
# Single-channel replacement of sensor_radius only.
assigned_traits = dataclasses.replace(original_traits, sensor_radius=NEW_VALUE)
# Atomically replace the body's traits field on the live agent.
agent.body = dataclasses.replace(agent.body, traits=assigned_traits)
```

This preserves: normal founder trait draw order, normal `spawn_agent_rng` consumption, normal per-agent RNG streams, normal descendant mutation streams, and normal non-`sensor_radius` founder traits. Only the `sensor_radius` field on the founder bodies is changed, after construction and before tick 0 observation begins.

**`HHModel.trait_fingerprints` warning.** `_record_trait_fingerprint` (model.py:386) is called inside `_spawn_founder` with the original (pre-patch) traits. After the v0.49 patch, `model.trait_fingerprints` will be stale for B / C. **v0.49 does NOT use `model.trait_fingerprints`** for any audit; it captures its own founder audit table from `model.agents` after the patch. `model.trait_fingerprints` is left untouched, byte-identical to its A_null form. This is the conservative choice (option A in the design discussion); option B (post-update the founder fingerprint entries) is rejected to avoid mutating historical machinery.

**Affected pre-reg sections.** Conservation framing, the B_clamp_4 and C_permutation arm specs, the implementation plan, and three of the locked tests (#2, #3, #5) are revised in-place below to reflect the fix. The verdict structure, arm count, corpus, observable definitions, label definitions, effect-size rule, sub-verdict structure, slice rollup, and re-anchor halts are unchanged.

## Conservation framing — interventional, not observational

v0.42–v0.48 preserved pre-50 reproduction byte-identity by construction (post-50 hooks only or read-only observation). v0.49 deliberately violates pre-50 byte-identity for the **B and C arms only** — the founder-time intervention is the slice's whole point. Specific guarantees:

- **No `src/` modifications.** The intervention is script-local and mutates founder body traits before tick 0 observation. All arms construct founders through the normal A_null path (`FounderSpec(traits_override=None)`); for B / C, the reducer's `setup_observer` callback applies a single-channel patch to `agent.body.traits.sensor_radius` after `HHModel(...)` returns and before any `model.step()` runs.
- **No modifications to prior reducer or audit scripts.** v0.34's `lineage_replay.py`, v0.35's `lineage_survival_replay.py`, v0.36's `trait_replay.py`, the four substrate audits (v0.42 / v0.43R / v0.44 / v0.45), and v0.46 / v0.47 / v0.48's reducers remain byte-identical to their merged forms.
- **A_null arm is byte-identical to v0.48's A_null path.** v0.49's A_null arm applies no patch. Founder traits, agent RNGs, and `streams.mutation` state at every tick are identical to v0.48's A_null arm for the same (version, seed, hazard). Byte-identity verified by the bridge re-anchor halt below.
- **B / C arms diverge from A_null at tick 0.** Only because `sensor_radius` differs on founder bodies. RNG streams (`streams.mutation`, per-agent RNGs) are byte-identical at the moment of the first `model.step()` across all three arms — only the founder-body trait values differ. Pre-50 byte-identity vs A_null does NOT hold for B / C from tick 1 onward (different sensor radii produce different sensing, action, and metabolic trajectories), but the divergence is *single-channel by construction*. The slice's interpretive frame is "does the v0.48 bridge fire under the intervention", not "is the metric the same as v0.48".
- **Single-channel intervention.** B / C modify ONLY the `sensor_radius` field of the founder body trait vector. All other founder fields (`reproduction_drive`, `metabolic_rate`, `hunger_pain_sensitivity`, ...) come from the model's normal `random_traits(...)` draw. A runtime invariant (`V049ReducerError`) compares `original_traits` (read from `model.agents` before the patch) against `assigned_traits` (read after the patch) per founder and asserts equality on every field except `sensor_radius`.
- **Descendant mutation proceeds normally.** Neither arm clamps descendants. v0.49 does NOT modify `mutate_traits`. Descendants of B-arm founders may drift away from `sensor_radius=4` via the normal mutation pipeline; descendants of C-arm founders mutate from their post-permutation parent traits. This is a deliberate design choice (see "Open framing" below).
- **`model.trait_fingerprints` is left as-is.** It records original (pre-patch) founder traits because `_record_trait_fingerprint` runs inside `_spawn_founder` before the v0.49 reducer can intervene. v0.49's audit ignores `model.trait_fingerprints` and captures its own founder audit table from live bodies after the patch. The fingerprint machinery is not mutated for B / C.

## Corpus (locked, 64 × 3 arms = 192 runs)

| version | seeds | hazards | runs per arm | total runs |
|---|---|---|---|---|
| v0.42 | 41..48 | {0, 8} | 16 | 48 |
| v0.43R | 49..56 | {0, 8} | 16 | 48 |
| v0.44 | 57..64 | {0, 8} | 16 | 48 |
| v0.45 | 65..72 | {0, 8} | 16 | 48 |
| **total** | | | | **192** |

V0_25 anchor unchanged: GradientPolicy + `auto_reproduction=True` + `TraitConfig(unbounded_mutation=True)`, `tight_gradient` layout, 5 founders, 200 ticks, `food_respawn_cooldown=50`, `ambient_influx_rate=1.0`, transfer-pool funding, `energy_pool_initial=1500`, `hazard_avoidance_weight` from V0_25. Each (version, seed, hazard) tuple is run **3 times** — once per arm — so cross-arm comparisons are pairable on (version, seed, hazard). Per-arm seed bands are identical; arm differs only in the founder intervention applied at tick 0.

The full 192-run corpus matches v0.48's statistical support per arm. Wall time ~15–30 minutes total at ~5–10 s per run.

## Arms (locked, 3)

### A_null

```
traits_override = None
```

Model draws each founder's traits via `random_traits(self.trait_config, self.streams.mutation)` exactly as v0.42–v0.48's A_null path. Byte-identical to v0.48's A_null arm. Used as the bridge replication baseline.

### B_sensor_radius_founder_clamp_4

For each (version, seed, hazard) tuple, the reducer constructs `HHModel` normally (`FounderSpec(traits_override=None)` for every founder) and applies the patch inside its `setup_observer` callback, before any `model.step()` runs:

1. `HHModel(...)` returns with 5 founder agents constructed normally; `random_traits` and `spawn_agent_rng` consume from `streams.mutation` exactly as A_null.
2. `run_chamber` calls `setup_observer(model)` (chamber.py:462). At this point the model is fully built, no step has been taken, and `setup_observer` fires with `model.tick_count == 0`.
3. Inside `setup_observer`, for each agent in `model.agents`:
   ```python
   original_traits = agent.body.traits
   assigned_traits = dataclasses.replace(original_traits, sensor_radius=4)
   agent.body = dataclasses.replace(agent.body, traits=assigned_traits)
   ```
4. Runtime invariant: for every founder, every field of `original_traits` other than `sensor_radius` is equal to the corresponding field of `assigned_traits`. Violation halts loud (`V049ReducerError`).
5. `setup_observer` then captures the v0.49 founder audit (lineage_id → original_sensor_radius, assigned_sensor_radius, all other founder traits) by reading the patched bodies from `model.agents`.
6. The v0.49 tick-0 snapshot (per-tick observer's tick-0 capture, copy-local from v0.48) is taken *after* the patch is applied, so tick 0 already reflects the assigned `sensor_radius`.

The model's `streams.mutation` is **not** consumed by the patch. Per-agent RNGs (`agent_rng`, populated by `spawn_agent_rng` during normal `_spawn_founder`) are unchanged by the patch.

**Choice of clamp value (locked, pre-data).** V0_25's `TraitConfig` draws `sensor_radius` uniformly from {1, 2, 3, 4, 5, 6} → expectation 3.5. No integer equals 3.5; the rounded-up midpoint (4) is the locked clamp value. Rationale (per design discussion): rounding up avoids depressing the arm's mean sensory reach below A_null's expectation; rounding down would make the clamp arm subtly sensory-poor and confound interpretation. **Watch-out**: under arm B, every agent's per-tick metabolic cost is `sensor_radius_metabolic_cost × 4` — slightly higher than A_null's expectation `sensor_radius_metabolic_cost × 3.5`. v0.49 cannot disentangle "loss of sensor_radius variation" from "small uniform metabolic uplift" if B's Label-B bridge weakens; flagged in "What v0.49 cannot establish".

**Label A degenerates under arm B.** All 5 founders have `assigned_sensor_radius == 4`. `argmax(founder_sensor_radius)` is a 5-way tie → `min(lineage_id)` always wins → label A is always lineage 0. Label A is therefore **diagnostic-only** under arm B (computed and reported in the per-lineage CSV, but does not gate B's verdict, does not feed paired_d cells, does not feed the slice rollup). CSV adds `label_a_gating_valid = False` and `label_a_degenerate_reason = "all founders assigned sensor_radius=4"` for arm B rows.

### C_sensor_radius_founder_permutation

For each (version, seed, hazard) tuple, identical setup to B (normal `HHModel` construction; patch in `setup_observer` before tick 0):

1. `HHModel(...)` returns with 5 founders constructed normally.
2. `run_chamber` calls `setup_observer(model)`.
3. Inside `setup_observer`:
   - Read the 5 `original_sensor_radius` values from the live founder bodies in lineage-id order:
     ```python
     founders = sorted(model.agents, key=lambda a: int(a.body.lineage_id))
     original_sr = [int(a.body.traits.sensor_radius) for a in founders]
     ```
   - Generate a permutation using a script-local helper RNG (used **only** for the permutation map, never for trait values):
     ```python
     helper_rng = np.random.default_rng(seed)
     perm = helper_rng.permutation(5)
     if list(perm) == [0, 1, 2, 3, 4]:
         perm = np.array([1, 2, 3, 4, 0])  # rotate-by-one fallback
     ```
   - Compute assigned values: `assigned_sr[i] = original_sr[perm[i]]`.
   - For each founder `i`, patch the body atomically:
     ```python
     assigned_traits = dataclasses.replace(founders[i].body.traits, sensor_radius=int(assigned_sr[i]))
     founders[i].body = dataclasses.replace(founders[i].body, traits=assigned_traits)
     ```
4. Runtime invariant: for every founder, every field of `original_traits` other than `sensor_radius` equals the corresponding field of `assigned_traits`. Violation halts loud.
5. Log per-founder `original_sensor_radius`, `assigned_sensor_radius`, `permutation_map_index = perm[i]`, `non_identity_permutation = True` (always — by construction of the rotate-by-one fallback), `applied_identity_rotation_fallback = True iff drawn perm was identity`.
6. Compute and log per-run `effective_sensor_radius_changed_count = sum(1 for i in range(5) if original_sr[i] != assigned_sr[i])`. **A non-identity permutation map does NOT guarantee that any founder's assigned `sensor_radius` value differs from its original.** When the original founder draw contains duplicate `sensor_radius` values (e.g., original `[3, 3, 3, 5, 5]`, perm `[1, 2, 3, 4, 0]` → assigned `[3, 3, 5, 5, 3]` — only 2 founders have changed values; the rest are duplicates being shuffled). `effective_sensor_radius_changed_count` is the honest measure of how much the assignment actually moved. v0.49 logs it per run, reports its distribution in the audit log, and **does not** exclude low-changed-count runs from C's paired_d pool — they are part of C's natural distribution given the V0_25 trait config (uniform over {1..6}, expected duplicates per 5-draw). If the distribution is dominated by low-changed-count runs in a way that compromises C's interpretive power, that is itself a finding to log in Results.

The helper RNG is fully isolated from the model's RNG streams (see watch-outs). It does not touch `model.streams.mutation` or any per-agent `agent_rng`. Founder trait values come from the model's normal draw, modified only on the `sensor_radius` axis.

**Label A under arm C is defined from `assigned_sensor_radius`.** That is, label A picks `argmax_lineage(assigned_sensor_radius)` — the lineage that received the highest `sensor_radius` after permutation, NOT the lineage whose founder originally drew the highest. This is the entire point of the arm: ask whether the bridge follows the *reassigned* trait. Tiebreak `min(lineage_id)` per v0.48.

## Labels (locked, two)

Label B is unchanged from v0.48 (tick-50 readiness fraction with the 3-tier tiebreak); copy-local from v0.48's reducer.

Label A is unchanged in **definition** (`argmax_lineage(founder_sensor_radius)` with `min(lineage_id)` tiebreak), but the *value* of `founder_sensor_radius` consulted differs by arm:

| arm | founder_sensor_radius source for label A |
|---|---|
| A_null | original (= assigned; no intervention) |
| B_clamp_4 | assigned (= 4 for all → degenerate; label A diagnostic-only) |
| C_perm | **assigned** (post-permutation) |

For arms A and C, label A is well-defined and gates the sub-verdict. For arm B, label A is computed for audit transparency but does not gate.

## Primary observables (locked, identical to v0.48, three with expected signs)

| # | name | expected sign |
|---|---|:-:|
| 1 | `pre50_food_events_count` | + |
| 2 | `pre50_food_energy_acquired` | + |
| 3 | `mean_distance_to_nearest_food_cell` | − |

Definitions, aggregation rules, and NaN handling are copy-local from v0.48 (per-tick lineage mean then mean over ticks 0..50 for #3; sum of `AteFood` events / sum of `AteFood.food_gained` for #1, #2). The per-tick observer firing semantics are unchanged from v0.48 (tick 0 captured at `setup_observer` time; ticks 1..50 captured by `tick_observer`).

## Effect-size rule (locked, sign-aware, identical to v0.48)

Per (arm, gating-label, observable):

```
per_run_delta_O = label_lineage_value_O − mean(non_label_lineage_values_O)
paired_d_O      = mean(per_run_delta_O) / stdev(per_run_delta_O, ddof=1)
signed_d_O      = paired_d_O × expected_sign
fires_expected  iff signed_d_O ≥ +0.5
fires_wrong     iff signed_d_O ≤ −0.5
```

Same threshold, same NaN handling, same `ddof=1`. Cross-arm pairing on (version, seed, hazard) is descriptive only; per-cell paired_d is computed per arm independently.

## Per-arm sub-verdicts (locked, 4-way each)

### A_null arm — gating: Label A AND Label B

| condition | sub-verdict |
|---|---|
| both labels clear ≥ 2/3, 0 wrong-sign | `A_NULL_BRIDGE_PRESENT` |
| exactly one label clears ≥ 2/3, 0 wrong-sign | `A_NULL_BRIDGE_PARTIAL` |
| neither label clears ≥ 2/3, 0 wrong-sign | `A_NULL_BRIDGE_NOT_FOUND` |
| any primary signed_d ≤ −0.5 under either label | `A_NULL_BRIDGE_OPPOSITE_SIGN_HALT` |

### B_clamp_4 arm — gating: Label B only

| condition | sub-verdict |
|---|---|
| Label B clears ≥ 2/3, 0 wrong-sign | `B_CLAMP_LABEL_B_BRIDGE_PRESENT` |
| Label B clears < 2/3, 0 wrong-sign | `B_CLAMP_LABEL_B_BRIDGE_NOT_FOUND` |
| any Label B primary signed_d ≤ −0.5 | `B_CLAMP_LABEL_B_OPPOSITE_SIGN_HALT` |

### C_permutation arm — gating: Label A (assigned) AND Label B

| condition | sub-verdict |
|---|---|
| both labels clear ≥ 2/3, 0 wrong-sign | `C_PERM_BRIDGE_PRESENT` |
| exactly one label clears ≥ 2/3, 0 wrong-sign | `C_PERM_BRIDGE_PARTIAL` |
| neither label clears ≥ 2/3, 0 wrong-sign | `C_PERM_BRIDGE_NOT_FOUND` |
| any primary signed_d ≤ −0.5 under either gating label | `C_PERM_BRIDGE_OPPOSITE_SIGN_HALT` |

Each arm's paired_d cells (3 observables × gating labels) are computed independently from the arm's 64-run pool. Per-arm NaN handling identical to v0.48.

## Slice-level rollup verdicts (locked, 6 outcomes, priority-ordered)

Priority order (first-matching wins):

1. `CORPUS_REDERIVE_DRIFT_HALT`
2. `INTERVENTION_OPPOSITE_SIGN_HALT`
3. `BRIDGE_REPLICATION_HALT`
4. `SENSOR_RADIUS_CAUSAL_CONTRIBUTION_SUPPORTED`
5. `SENSOR_RADIUS_CAUSAL_CONTRIBUTION_NOT_SUPPORTED`
6. `SENSOR_RADIUS_CAUSAL_CONTRIBUTION_MIXED`

### Halt conditions

| priority | rollup verdict | trigger | locked phrase (verbatim) |
|---|---|---|---|
| 1 | `CORPUS_REDERIVE_DRIFT_HALT` | A_null arm's re-derived `a_share_h8` for any of v0.42 / v0.44 / v0.45 drifts > 1e-3 from the published reference (0.652 / 0.878 / 0.818) | "Halt: A_null re-anchor drifted from the published Results value for {version}; v0.49's deterministic re-execution does not reproduce the published metric within 1e-3." |
| 2 | `INTERVENTION_OPPOSITE_SIGN_HALT` | any arm's gating-label primary fires wrong-sign (signed_d ≤ −0.5) | "Halt: a v0.49 spatial / foraging primary fires in the WRONG direction under a gating label; the founder-trait intervention is incompatible with the locked expected signs." |
| 3 | `BRIDGE_REPLICATION_HALT` | **(a)** A_null arm's signed_d for any of the six v0.48 cells drifts > 1e-3 from the v0.48 published value, OR **(b)** A_null arm sub-verdict ≠ `A_NULL_BRIDGE_PRESENT` | "Halt: v0.49's A_null arm does not reproduce v0.48's spatial bridge — either a paired_d cell drifts beyond 1e-3 of the published value, or the A_null sub-verdict does not resolve to PRESENT. v0.49 cannot interpret the B / C arms without an established baseline." |

The bridge re-anchor's hardcoded references (extracted from v0.48's merged Results §"Paired Cohen's d per (label, primary observable) — all six cells fire"):

| label | observable | sign | published signed_d |
|---|---|:-:|:-:|
| `label_a_sensor_radius` | `pre50_food_events_count` | + | **+1.066** |
| `label_a_sensor_radius` | `pre50_food_energy_acquired` | + | **+1.066** |
| `label_a_sensor_radius` | `mean_distance_to_nearest_food_cell` | − | **+1.916** |
| `label_b_readiness_fraction` | `pre50_food_events_count` | + | **+0.916** |
| `label_b_readiness_fraction` | `pre50_food_energy_acquired` | + | **+0.916** |
| `label_b_readiness_fraction` | `mean_distance_to_nearest_food_cell` | − | **+1.179** |

Drift tolerance = 1e-3 (published precision; matches v0.46 / v0.47 / v0.48 protocol). Rationale: v0.49's A_null arm runs the same code path as v0.48 (same V0_25 anchor, same per-tick observer, same aggregation, no `traits_override`), so the cells must reproduce v0.48's values bytewise modulo float-arithmetic edge cases. A drift > 1e-3 indicates an implementation bug or RNG-stream offset (e.g., a B/C helper RNG accidentally consuming `streams.mutation`).

### Outcome conditions (only consulted if no halt fires)

| priority | rollup verdict | (A_null, B_clamp, C_perm) sub-verdicts | locked phrase (verbatim) |
|---|---|---|---|
| 4 | `SENSOR_RADIUS_CAUSAL_CONTRIBUTION_SUPPORTED` | (PRESENT, NOT_FOUND, PRESENT) | "Founder `sensor_radius` variation supports a causal contribution to the v0.48 pre-50 spatial / foraging bridge: the bridge follows reassigned founder sensor_radius and weakens when founder variation is removed." |
| 5 | `SENSOR_RADIUS_CAUSAL_CONTRIBUTION_NOT_SUPPORTED` | (PRESENT, PRESENT, NOT_FOUND) | "Founder `sensor_radius` variation is not supported as a causal contributor to the v0.48 pre-50 spatial / foraging bridge: the bridge persists without founder variation and does not follow reassigned founder sensor_radius." |
| 6 | `SENSOR_RADIUS_CAUSAL_CONTRIBUTION_MIXED` | A_null PRESENT and any other non-halt (B, C) combination | "Founder `sensor_radius` variation shows mixed evidence as a causal contributor to the v0.48 pre-50 spatial / foraging bridge: the B / C arms do not resolve cleanly under the locked criteria." |

The rollup is **conservative by construction**: the SUPPORTED phrase says "supports a causal contribution", not "is causal for"; the NOT_SUPPORTED phrase says "is not supported as a causal contributor", not "is not causal". Mechanism declarations require fresh-stream calibration analogous to v0.30..v0.33 plus first-class instrumentation; v0.49 is a single-channel founder-time intervention and cannot rule out founder-position confounds, trait covariance with non-`sensor_radius` fields, or stochastic lineage dynamics.

## Cautious framing (per CLAUDE.md)

- "**Supports a causal contribution**" — NOT "**causes**" or "**proves causality**".
- "**Bridge follows reassigned founder sensor_radius**" — descriptive of the joint distribution under the C_perm intervention, not a mechanism claim.
- "**On the modern A_null corpus / under the locked V0_25 anchor**" — NOT a chamber-config-independent claim.
- v0.49 explicitly does **not** rule out: founder-position advantage, lineage-luck dynamics, trait covariance among non-`sensor_radius` fields, non-V0_25 anchors, or post-tick-200 effects.

## What v0.49 cannot establish (logged here pre-data, not retrofittable)

- ✗ **Mechanism**. v0.49 is single-channel: it varies *only* founder `sensor_radius`. It does not compare against an "all-founder-traits-clamped" baseline. A bridge that weakens under B and follows under C is *consistent* with `sensor_radius` being a causal driver; it is also consistent with `sensor_radius` being correlated with another causally-relevant founder feature that varies with it.
- ✗ **Metabolic equivalence between A_null and B_clamp_4**. Arm B fixes `sensor_radius = 4`; A_null draws from {1..6} → expectation 3.5. Per-tick metabolic cost differs by `0.5 × sensor_radius_metabolic_cost`. If B's Label-B bridge weakens, v0.49 cannot disentangle "loss of variation" from "small uniform metabolic uplift". Locked here as a known confound; future slices may probe it (see "Open framing").
- ✗ **Generalisation beyond V0_25**. Layout, policy, reproduction config, and trait config are all V0_25 anchor.
- ✗ **Causality for post-tick-50 dominance**. v0.49 measures the v0.48 *bridge* (pre-50 spatial / foraging primaries vs. labels A and B). It does not directly probe the b50-share dominance label of v0.46.

## Open framing (NOT in v0.49)

- v0.50 candidate: equalise founder positions (deterministic spawn pattern instead of `spread_y`) to test the founder-position confound.
- v0.51 candidate: clamp `sensor_radius` *throughout the lineage* (override `mutate_traits` for the field) to remove the descendant-drift channel.
- v0.52 candidate: hold `sensor_radius_metabolic_cost = 0` to decouple sensing radius from metabolic cost, isolating the "information radius" channel.

These are NOT locked v0.49 deliverables; flagged for handoff continuity.

## Re-anchor (locked, A_null arm only, identical to v0.46 / v0.47 / v0.48)

Each predecessor version's audit emits a pooled A_null `a_share_h8` (top-lineage b50 share at h=8). v0.49's A_null arm re-derives this and asserts drift ≤ 1e-3:

| version | published `a_share_h8` |
|---|---|
| v0.42 | 0.652 |
| v0.43R | NOT PUBLISHED (informational-only) |
| v0.44 | 0.878 |
| v0.45 | 0.818 |

B and C arms re-derive their own `a_share_h8` for their own A_null-of-the-arm pool; these are logged informationally and **do not gate the verdict** (B and C are different counterfactual worlds; the published references are A_null-only).

## Outputs (locked)

```
runs/v0.49-causal-probe/per_run_per_lineage_v049.csv
  columns: arm, version, seed, hazard, run_id, lineage_id,
           original_sensor_radius, assigned_sensor_radius, intervention_delta,
           founder_reproduction_drive, founder_metabolic_rate,
           pre50_food_events_count, pre50_food_energy_acquired,
           mean_distance_to_nearest_food_cell,
           tick50_living_count, tick50_above_threshold_count, tick50_above_threshold_fraction,
           b50_count, is_eventual_top_b50_label,
           is_high_sensor_radius_lineage, is_high_tick50_readiness_fraction_lineage,
           label_a_gating_valid, label_a_degenerate_reason

runs/v0.49-causal-probe/per_run_intervention_audit.csv
  columns: arm, version, seed, hazard, lineage_id, founder_index,
           original_sensor_radius, assigned_sensor_radius,
           permutation_map_index, applied_identity_rotation_fallback,
           effective_sensor_radius_changed_count  (per-run, repeated on each row of the run)

runs/v0.49-causal-probe/audit_summary.csv
  columns: section, key, value
  sections:
    - reanchor_a_share_h8: per (arm, version, h=8) derived + (A_null only) published + drift_abs
    - bridge_reanchor: per (label, observable) v0.48 published signed_d + v0.49 A_null derived signed_d + drift_abs
    - paired_d: per (arm, gating-label, observable) cell — paired_d, signed_d, n_runs, fires_expected, fires_wrong
    - sub_verdicts: per arm — sub-verdict + locked sub-phrase
    - rollup_verdict: locked rollup verdict + locked rollup phrase

runs/v0.49-causal-probe/audit_log.txt
  human-readable echo with all six locked phrases printed verbatim where they fire.
```

## Implementation plan (locked)

1. Fresh script `scripts/v0_49_sensor_radius_causal_probe_audit.py`. CLI: `uv run python scripts/v0_49_sensor_radius_causal_probe_audit.py [--out-dir runs/v0.49-causal-probe]`.
2. Per (version, seed, hazard) tuple, run **3 arms**. Every arm constructs `HHModel` via the normal A_null path (`FounderSpec(traits_override=None)`):
   - **A_null**: no patch. `setup_observer` reads founder traits from `model.agents` and records them as `original == assigned`.
   - **B_clamp_4**: inside `setup_observer`, before the tick-0 snapshot, replace `agent.body.traits.sensor_radius` with `4` on every founder via `dataclasses.replace`. Assert single-channel invariant (every non-`sensor_radius` field equal to the original).
   - **C_permutation**: inside `setup_observer`, use a script-local `helper_rng = np.random.default_rng(seed)` to generate a non-identity permutation of `[0..4]` (rotate-by-one fallback if identity). Read original `sensor_radius` values from the founder bodies, compute assigned values via the permutation, and patch each founder's body. Assert single-channel invariant.
3. For each arm-run, attach v0.48-style `setup_observer` + `tick_observer` (copy-local from v0.48). The setup_observer applies the trait patch (B / C) before capturing tick 0. Capture per-tick records for ticks 0..50 inclusive (51 snapshots); `AgentBorn` / `AteFood` / `HazardDamageApplied` listeners filtered by `sender=model`.
4. Aggregate per-lineage primaries identical to v0.48. Compute per-arm label A and label B per the arm's specific sources (assigned for B/C; original = assigned for A_null).
5. Compute paired_d per (arm, gating-label, observable) cell; classify per-arm sub-verdicts.
6. **Bridge re-anchor** (priority-3 halt): for the A_null arm's six cells, compare derived signed_d to v0.48's hardcoded references; halt if any drift > 1e-3.
7. **Corpus re-anchor** (priority-1 halt): for the A_null arm only, derive `a_share_h8` for v0.42 / v0.44 / v0.45; halt if any drift > 1e-3.
8. **Opposite-sign halt** (priority-2): scan all (arm, gating-label, observable) cells; halt if any signed_d ≤ −0.5.
9. Compute slice rollup verdict per the locked priority order; print + write the locked phrase verbatim.

The reducer is fully self-contained: it reads no `runs/` artifacts. Wall time ~15–30 minutes for 192 runs. Determinism guaranteed by passing each (version, seed) the same V0_25 anchor config; the helper RNG (used only for the C-arm permutation map) is deterministic per run and does not consume from `streams.mutation`, so A_null's RNG state at every tick is byte-identical to v0.48's.

## Test list (locked, 16 tests; extends v0.46–v0.48 7-point review pattern)

`tests/test_v0_49_sensor_radius_causal_probe_audit.py`:

1. `test_all_arms_construct_founders_via_normal_a_null_path` — assert that for every arm the reducer constructs `FounderSpec` with `traits_override=None`. The intervention lives in `setup_observer`, not in `FounderSpec`.
2. `test_b_clamp_patch_replaces_only_sensor_radius_on_live_bodies` — construct `HHModel` for a representative (version, seed, hazard) tuple; capture pre-patch founder body traits; apply the B-arm patch; assert every founder's `body.traits.sensor_radius == 4` and every other field of `body.traits` is byte-identical to the pre-patch value.
3. `test_a_null_arm_streams_mutation_state_byte_identical_across_arms` — for the same (version, seed, hazard), construct `HHModel` once; record `model.streams.mutation`'s state via a deterministic probe (next 8 draws); apply the B and C `setup_observer` patches in two separate model instances; assert the next 8 draws from `streams.mutation` are byte-identical across all three arms (the patch never consumes `streams.mutation`).
4. `test_c_permutation_is_non_identity` — generate permutations under a deterministic helper seed that lands on identity; assert the rotate-by-one fallback fires and `assigned != original` for at least one founder.
5. `test_c_permutation_patch_replaces_only_sensor_radius_on_live_bodies` — construct `HHModel` for a representative tuple; capture pre-patch founder body traits; apply the C-arm permutation patch; assert non-`sensor_radius` fields are byte-identical to pre-patch for every founder, and the assigned `sensor_radius` set equals a permutation of the original set.
6. `test_c_permutation_label_a_uses_assigned_sensor_radius` — synthetic founder traits with original `[2, 5, 4, 1, 6]` and permutation `[1, 2, 3, 4, 0]` → assigned `[5, 4, 1, 6, 2]`; assert label A picks lineage 3 (highest assigned = 6).
7. `test_b_clamp_label_a_is_diagnostic_only_with_csv_flag` — synthetic B-arm rows; assert `label_a_gating_valid = False` and that label A does not feed B's sub-verdict computation.
8. `test_per_arm_subverdict_a_null_present_requires_both_labels_clear` — synthetic paired_d under A_null such that label A is (+0.6, +0.7, −0.3) and label B is (+0.6, +0.8, −0.2); assert sub-verdict = `A_NULL_BRIDGE_PRESENT`.
9. `test_per_arm_subverdict_b_clamp_present_requires_label_b_only` — synthetic paired_d under B_clamp such that label B clears 2/3, label A trivially degenerate; assert sub-verdict = `B_CLAMP_LABEL_B_BRIDGE_PRESENT`.
10. `test_per_arm_subverdict_c_perm_partial_when_only_one_label_clears` — synthetic paired_d under C_perm such that label A clears 2/3 but label B clears 1/3; assert sub-verdict = `C_PERM_BRIDGE_PARTIAL`.
11. `test_rollup_supported_when_a_null_present_b_not_found_c_present` — assert rollup = `SENSOR_RADIUS_CAUSAL_CONTRIBUTION_SUPPORTED`.
12. `test_rollup_not_supported_when_a_null_present_b_present_c_not_found` — assert rollup = `SENSOR_RADIUS_CAUSAL_CONTRIBUTION_NOT_SUPPORTED`.
13. `test_rollup_mixed_for_other_non_halt_combinations` — synthetic (PRESENT, PRESENT, PRESENT); assert rollup = `SENSOR_RADIUS_CAUSAL_CONTRIBUTION_MIXED`.
14. `test_bridge_replication_halt_on_signed_d_drift` — synthesise A_null arm cells where one cell drifts +1.5 signed_d (vs. published +1.066); assert `BRIDGE_REPLICATION_HALT` raised loud.
15. `test_bridge_replication_halt_on_a_null_subverdict_partial` — synthesise A_null sub-verdict = PARTIAL while all signed_d cells are within 1e-3 of published; assert `BRIDGE_REPLICATION_HALT` raised loud (catches the case where subtle code-path drift shifts the verdict without shifting the headline metric — though under correct implementation neither path should fire).
16. `test_corpus_rederive_drift_halt_priority_over_bridge_replication_halt` — synthesise both an `a_share_h8` drift on v0.42 AND a bridge cell drift; assert `CORPUS_REDERIVE_DRIFT_HALT` fires (priority 1) and the bridge halt does not.

## Watch-outs (for future-Chronus)

- **B's metabolic uplift confound (logged above).** If B's Label-B bridge weakens, the slice cannot disentangle "loss of sensor_radius variation" from "uniform metabolic uplift +0.5 × sensor_radius_metabolic_cost". Future calibration may probe this.
- **`AteFood.food_gained` is constant 20.0 per event under V0_25 defaults.** Observables #1 and #2 are perfectly proportional on this corpus (verified post-hoc in v0.48). Their per-arm paired_d values will be identical by construction. The 3-observable primary set has 2 effectively-independent channels; the AND-gate is unaffected because observable #3 (distance) is genuinely independent.
- **Helper RNG is fully isolated from the model's RNG streams.** The C-arm permutation map is generated from a script-local `np.random.default_rng(seed)`; this helper instance is never used to draw founder trait values, never mixed into `model.streams.mutation`, never consumed by per-agent `agent_rng`s, and never seeded from any model state. Founder traits come exclusively from the model's normal `random_traits` path. A_null and B arms do not use the helper RNG at all. Test #3 enforces that `streams.mutation` state is byte-identical across arms after `setup_observer` returns.
- **Patch order matters.** The trait patch must happen inside `setup_observer` *before* the v0.49 tick-0 snapshot is captured (which is also inside `setup_observer`, per the v0.48 pre-implementation correction pattern). The reducer's `setup_observer` applies the patch first, then captures founder audit + tick-0 snapshot from the patched bodies.
- **`AgentBody` is `@dataclass(frozen=True)`; `HHAgent.body` is a reassignable attribute.** Verified: `body.py:31` declares `AgentBody` frozen; `mesa_agents.py:73, 184, 217, 231` reassign `self.body` to new `AgentBody` instances during normal simulation steps (e.g., after `apply_action` / `apply_metabolism` / `apply_damage`). The v0.49 patch follows the same idiom: `agent.body = dataclasses.replace(agent.body, traits=dataclasses.replace(agent.body.traits, sensor_radius=NEW_VALUE))`. No `src/` change is required to support this.
- **A_null arm is byte-identical to v0.48's A_null path by construction.** The bridge re-anchor halt (priority 3) catches any drift; this is the v0.49 analog of v0.46's `CORPUS_REDERIVE_DRIFT_HALT`.
- **C_perm's identity fallback fires deterministically** when the helper RNG draws identity. Logged per-run via `applied_identity_rotation_fallback`. The expected fallback rate is 1/120 (1/5!).
- **Single-channel invariant must halt loud** on any non-`sensor_radius` field difference between original and assigned trait vectors. This guards against `dataclasses.replace` semantics drift (e.g., if a future Traits field is added and not preserved).
- **Pre-50 byte-identity vs. v0.48 holds for A_null only.** B and C arms diverge from A_null at founder spawn and must NOT be expected to reproduce v0.48's A_null cells. This is the slice's design.
- **Locked phrase discipline:** all locked sub-verdict phrases AND the rollup phrase fire verbatim where the verdict fires. No paraphrase.
- **Determinism north star** ([[scripts/core_smoke_test.py]]) must continue to pass; v0.49 makes no `src/` change, so this is preserved by construction.

## Files this slice will create

- `docs/experiments/fear_hunger_v0.49.md` (this file; Results section appended after reducer run)
- `scripts/v0_49_sensor_radius_causal_probe_audit.py`
- `tests/test_v0_49_sensor_radius_causal_probe_audit.py`

No other files modified.

## Results

(appended after reducer execution)
