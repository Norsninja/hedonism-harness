# fear_hunger v0.50 — founder-position confound probe

**Slice:** v0.50
**Type:** **first-class intervention** (NOT a post-hoc reducer); founder-time spawn-position clamp + permutation arms.
**Predecessors:** v0.21..v0.27 (substrate / aggregate-optimum), v0.34..v0.36 (lineage observability + heritability), v0.42..v0.45 (substrate-causal arc), v0.46 (`READINESS_PREDICTS_DOMINANCE`), v0.47 (`READINESS_TRAITS_PARTIALLY_PREDICTIVE`), v0.48 (`SENSOR_RADIUS_SPATIAL_BRIDGE_PRESENT`), v0.49 (`SENSOR_RADIUS_CAUSAL_CONTRIBUTION_SUPPORTED`: founder `sensor_radius` clamp + permutation establishes a single-channel causal probe).
**Question being asked (locked):** Does v0.49's `sensor_radius` causal contribution survive when founder starting positions are controlled or equalized?

v0.49 supports a causal contribution from founder `sensor_radius` to the v0.48 spatial / foraging bridge. v0.49 explicitly does NOT rule out four confounds, of which the strongest is **founder position**. Direct empirical motivation: under v0.49 arm B (sensor_radius clamped to 4 → label A degenerates to lineage 0), `mean_distance_to_nearest_food_cell` for lineage 0 fired wrong-sign at signed_d = **−0.732** under label A. That number does not measure sensor_radius (it was clamped); it measures whatever lineage 0 inherits from being lineage 0. The most likely structural source: V0_25's `spread_y(5, layout.height)` places founders at deterministic y-coordinates ([0,1,2,3,4] under `tight_gradient`'s height=6), so lineage 0 is always at the bottom edge with asymmetric topology vs lineages 1..4. v0.50 manipulates founder spawn positions at tick 0 and tests whether the v0.48 bridge cells continue to clear under the same observables and labels.

## Pre-implementation correction (2026-05-08, before any reducer code)

The v0.50 design follows v0.49's **post-`HHModel`-construction body-patch pattern** to preserve single-channel intervention. Locked here for transparency; identical in spirit to v0.49's correction:

- `HHModel(...)` is called normally with `FounderSpec(traits_override=None)` and the V0_25 layout's default spawn coordinates. The model draws founder traits, agent RNGs, and grid placements via the normal A_null path.
- Inside the v0.50 reducer's `setup_observer` callback (fires once after `HHModel(...)` returns and before any `model.step()`), the reducer patches each founder's `body.x`, `body.y`, AND `agent.cell` for arms B / C.
- `streams.mutation` byte-identical across arms after `setup_observer` returns; per-agent RNGs are unchanged; only founder body coordinates and Mesa cell pointers differ.
- **Single-channel position invariant**: for B / C, the patch modifies ONLY `body.x` / `body.y` (and the corresponding `agent.cell` reference). All other `AgentBody` fields (`id`, `lineage_id`, `parent_id`, `traits`, `energy`, `health`, `age`, `alive`) and all `HHAgent` fields (`policy`, `memory`, `agent_rng`, `policy_factory`) remain byte-identical to A_null. A runtime invariant (`V050ReducerError`) compares `original_body` against `assigned_body` field-by-field and asserts equality on every field except `x` and `y`.
- **Mesa cell occupancy**: after `agent.body = dataclasses.replace(agent.body, x=NEW_X, y=NEW_Y)`, the reducer also assigns `agent.cell = model.cell_at(NEW_X, NEW_Y)` to keep the Mesa grid pointer aligned with the new body coordinates. This is the same idiom used inside `HHAgent.step` (mesa_agents.py:184–187) when actions move agents during normal simulation.
- `model.trait_fingerprints` records the original (pre-patch) `spawn_x` / `spawn_y` per founder. v0.50's audit captures its own founder position table from live bodies after the patch; `model.trait_fingerprints` is left untouched (option A from v0.49 design).

## Conservation framing — interventional, not observational

- **No `src/` modifications.** The intervention is script-local and mutates founder body coordinates + Mesa cell pointers before tick 0 observation. All arms construct founders through the normal A_null path; for B / C, the reducer's `setup_observer` callback applies a single-channel position patch.
- **No modifications to prior reducer or audit scripts.** v0.34's `lineage_replay.py`, v0.35's `lineage_survival_replay.py`, v0.36's `trait_replay.py`, the four substrate audits (v0.42 / v0.43R / v0.44 / v0.45), and v0.46 / v0.47 / v0.48 / v0.49's reducers remain byte-identical to their merged forms.
- **A_null arm is byte-identical to v0.48/v0.49's A_null path.** v0.50's A_null arm applies no patch. Founder positions, traits, agent RNGs, and `streams.mutation` state at every tick are identical. Byte-identity verified by the bridge re-anchor halt below.
- **B / C arms diverge from A_null at tick 0.** Only because founder body coordinates differ. RNG streams (`streams.mutation`, per-agent RNGs) are byte-identical at the moment of the first `model.step()` across all three arms — only founder positions differ. Pre-50 byte-identity vs A_null does NOT hold for B / C from tick 1 onward (different positions produce different sensing geometry, action eligibility, and metabolism trajectories), but the divergence is *single-channel by construction*.
- **Single-channel position intervention.** B / C modify ONLY `body.x` / `body.y` (and the matching `agent.cell` pointer). All other body, agent, and trait fields come from the model's normal draw. Runtime invariant guards this on every (arm, founder) pair.
- **No descendant position modification.** Neither arm clamps descendant positions. Births proceed through the normal birth queue; offspring spawn positions are determined by the existing reproduction pipeline (which places offspring at parent-adjacent cells per `core/reproduction.py`).
- **Capacity-1 invariant preserved.** All three arms place founders at 5 distinct cells. B and C's patched positions are validated to be pairwise distinct before the patch is applied.

## Trait-covariance preflight (already completed)

A descriptive preflight (`scripts/v0_50_founder_trait_covariance_preflight.py`, committed at `d8c3e20` on this branch) computed Pearson and Spearman correlations between `founder_sensor_radius` and the other 12 founder trait fields across 160 unique founder rows (32 unique seeds × 5 founders). All correlations |ρ| < 0.15 (max: `metabolic_rate` ρ = −0.144, `novelty_drive` ρ = −0.136, `pain_tolerance` ρ = +0.134). **Trait covariance is low-priority for v0.50**: pairwise founder-trait correlations with `sensor_radius` are small in this corpus, so v0.50 focuses on the position confound. Pairwise correlations do not exclude nonlinear or interaction effects; trait covariance remains a deferred consideration for future slices, just not the next-step priority.

## Corpus (locked, 64 × 3 arms = 192 runs)

| version | seeds | hazards | runs per arm | total runs |
|---|---|---|---|---|
| v0.42 | 41..48 | {0, 8} | 16 | 48 |
| v0.43R | 49..56 | {0, 8} | 16 | 48 |
| v0.44 | 57..64 | {0, 8} | 16 | 48 |
| v0.45 | 65..72 | {0, 8} | 16 | 48 |
| **total** | | | | **192** |

V0_25 anchor unchanged from v0.46–v0.49. Each (version, seed, hazard) tuple is run **3 times** — once per arm.

## Default V0_25 founder spawn pattern (for reference)

`tight_gradient` layout: width=9, height=6, `spawn_x=1`, food at `x ∈ [5, 8]`, hazard at `x ∈ [3, 4]`, safe at `x ∈ [0, 2]`. `spread_y(5, 6)` → `[0, 1, 2, 3, 4]`. Default founder positions (in lineage_id order):

```
lineage 0 → (x=1, y=0)
lineage 1 → (x=1, y=1)
lineage 2 → (x=1, y=2)
lineage 3 → (x=1, y=3)
lineage 4 → (x=1, y=4)
```

All 5 founders share `x=1`, distance 4 (Manhattan) from nearest food cell at tick 0. Food fills `x∈[5,8]` for ALL y, so tick-0 distance is uniform. The y-coordinate matters only via post-tick dynamics: **edge topology** (lineage 0 at the global y=0 grid edge has only y=1 as a y-neighbor; lineages 1..3 have both y±1; lineage 4 at y=4 has y=3 and y=5 — non-edge), capacity-1 contention, and bottom-skewed placement vs the geometric mid-row of the height-6 grid (which lies between y=2 and y=3 at 2.5; V0_25's mean y=2.0 sits half a row below). A height-6 grid cannot host a perfectly centered contiguous 5-row band: the only two contiguous options are `[0,1,2,3,4]` (bottom-skewed; mean 2.0) and `[1,2,3,4,5]` (top-skewed; mean 3.0). Neither is "centered" in the geometric sense.

## Arms (locked, 3)

### A_null

No patch. Founder positions per V0_25 default. Byte-identical to v0.48/v0.49 A_null.

### B_position_shifted_top

For each (version, seed, hazard) tuple, after `HHModel(...)` returns and inside `setup_observer`:

1. Identify the 5 founders sorted by `body.lineage_id`.
2. Patch each founder to a top-shifted y-position at the same `spawn_x`:
   ```
   shifted_y = [1, 2, 3, 4, 5]  # contiguous top-shifted band; reflects V0_25's [0..4] band
   for i, agent in enumerate(founders):
       new_x, new_y = layout.spawn_x, shifted_y[i]   # = 1, shifted_y[i]
       agent.body = dataclasses.replace(agent.body, x=new_x, y=new_y)
       agent.cell = model.cell_at(new_x, new_y)
   ```
3. Assert single-channel invariant: every non-(x,y) field of original body equals the corresponding field of patched body. Assert all 5 patched cells are distinct.
4. Capture per-founder `original_x`, `original_y`, `assigned_x`, `assigned_y` to the v0.50 audit.

**Choice rationale (locked, pre-data).** A height-6 grid cannot perfectly center a contiguous 5-row band; the geometric mid-row is at y=2.5. The only two contiguous-5-cell options are `[0,1,2,3,4]` (V0_25 default — bottom-skewed, mean 2.0) and `[1,2,3,4,5]` (this arm — top-shifted, mean 3.0). `B_position_shifted_top` is **NOT** an "equalized" or "centered" placement. It is a **reflected band**: it transfers global-edge exposure from lineage 0 (which sits at y=0 in V0_25, the only founder touching the bottom grid edge) to lineage 4 (which sits at y=5 under shifted-top, the only founder touching the top grid edge). Other edge-topology asymmetries are mirrored. If the v0.48 bridge was driven by a *specific* lineage-id ↔ position structure under V0_25, B's reflected placement should perturb it; if the bridge depends on the underlying band geometry rather than its lineage-id assignment, B's signal will mirror A_null's. v0.50 thus tests whether the bridge is invariant under band reflection.

### C_position_permuted

For each (version, seed, hazard) tuple, after `HHModel(...)` returns and inside `setup_observer`:

1. Read original founder positions from the live bodies in lineage_id order:
   ```python
   founders = sorted(model.agents, key=lambda a: int(a.body.lineage_id))
   original_xy = [(int(a.body.x), int(a.body.y)) for a in founders]
   ```
2. Generate a permutation using a script-local helper RNG (used **only** for the permutation map, never for trait or position values):
   ```python
   helper_rng = np.random.default_rng(seed)
   perm = helper_rng.permutation(5)
   if list(perm) == [0, 1, 2, 3, 4]:
       perm = [1, 2, 3, 4, 0]   # rotate-by-one fallback
   ```
3. Compute assigned positions: `assigned_xy[i] = original_xy[perm[i]]`.
4. Patch each founder's body and Mesa cell. Assert single-channel invariant. Assert all 5 patched cells are distinct (guaranteed by permutation of distinct-set input).
5. Log per-founder `permutation_map_index`, `applied_identity_rotation_fallback`, and per-run `effective_position_changed_count = sum(1 for i in range(5) if assigned_xy[i] != original_xy[i])`.

**Hazard-paired runs share permutation maps.** Because the helper RNG is seeded from `seed` alone (not `(seed, hazard)`), the two C-arm runs for the same (version, seed) at h=0 and h=8 receive identical permutations and therefore identical position reassignments — only chamber hazard configuration differs between them. (Same property as v0.49's C-arm.)

## Labels (locked, two — identical to v0.49)

Label A (`is_high_sensor_radius_lineage`): `argmax_lineage(founder_sensor_radius)`, tiebreak `min(lineage_id)`. Founder `sensor_radius` is the model's normal draw under all arms (no clamp, no permutation in v0.50). Well-defined under all three arms.

Label B (`is_high_tick50_readiness_fraction_lineage`): v0.47's 3-tier fraction tiebreak. Identical to v0.48/v0.49.

Both labels gate the verdict for **all three arms** (no degeneracy concern; arm B's clustered positions still produce sensor_radius variation among founders).

## Primary observables (locked, 3, identical to v0.48/v0.49)

| # | name | expected sign |
|---|---|:-:|
| 1 | `pre50_food_events_count` | + |
| 2 | `pre50_food_energy_acquired` | + |
| 3 | `mean_distance_to_nearest_food_cell` | − |

Definitions, aggregation rules, NaN handling: copy-local from v0.48/v0.49 (per-tick lineage mean → mean over ticks 0..50 for #3; sums of `AteFood` events / `food_gained` for #1, #2). Per-tick observer firing semantics unchanged (tick 0 captured at `setup_observer` time *after* the position patch; ticks 1..50 captured by `tick_observer`).

## Effect-size rule (locked, sign-aware, identical to v0.48/v0.49)

```
per_run_delta_O = label_lineage_value_O − mean(non_label_lineage_values_O)
paired_d_O      = mean(per_run_delta_O) / stdev(per_run_delta_O, ddof=1)
signed_d_O      = paired_d_O × expected_sign
fires_expected  iff signed_d_O ≥ +0.5
fires_wrong     iff signed_d_O ≤ −0.5
```

## Per-arm sub-verdicts (locked, 4-way each, identical structure to v0.49 arms A and C)

Each arm gates on Label A AND Label B (no Label A degeneracy in v0.50 since `sensor_radius` is not clamped):

| arm | sub-verdicts |
|---|---|
| A_null | `A_NULL_BRIDGE_PRESENT` / `_PARTIAL` / `_NOT_FOUND` / `_OPPOSITE_SIGN_HALT` |
| B_position_shifted_top | `B_POS_SHIFTED_TOP_BRIDGE_PRESENT` / `_PARTIAL` / `_NOT_FOUND` / `_OPPOSITE_SIGN_HALT` |
| C_position_permuted | `C_POS_PERM_BRIDGE_PRESENT` / `_PARTIAL` / `_NOT_FOUND` / `_OPPOSITE_SIGN_HALT` |

Conditions per sub-verdict (identical for all three arms; no diagnostic-only label):
- PRESENT: both labels clear ≥ 2/3 primaries, 0 wrong-sign.
- PARTIAL: exactly one label clears ≥ 2/3, 0 wrong-sign.
- NOT_FOUND: neither clears ≥ 2/3, 0 wrong-sign.
- OPPOSITE_SIGN_HALT: any primary signed_d ≤ −0.5 under either label.

## Slice rollup verdicts (locked, 6 outcomes, priority-ordered)

Priority order (first-matching wins):

1. `CORPUS_REDERIVE_DRIFT_HALT`
2. `INTERVENTION_OPPOSITE_SIGN_HALT`
3. `BRIDGE_REPLICATION_HALT`
4. `SENSOR_RADIUS_ROBUST_TO_POSITION`
5. `SENSOR_RADIUS_POSITION_INTERACTION_SUPPORTED`
6. `SENSOR_RADIUS_POSITION_INTERACTION_MIXED`

| priority | rollup verdict | trigger | locked phrase (verbatim) |
|---|---|---|---|
| 1 | `CORPUS_REDERIVE_DRIFT_HALT` | A_null arm `a_share_h8` drifts > 1e-3 from v0.42/44/45 published | "Halt: A_null re-anchor drifted from the published Results value for {version}; v0.50's deterministic re-execution does not reproduce the published metric within 1e-3." |
| 2 | `INTERVENTION_OPPOSITE_SIGN_HALT` | any arm gating-label primary signed_d ≤ −0.5 | "Halt: a v0.50 spatial / foraging primary fires in the WRONG direction under a gating label; the founder-position intervention is incompatible with the locked expected signs." |
| 3 | `BRIDGE_REPLICATION_HALT` | A_null cell drift > 1e-3 vs v0.48 published OR A_null sub-verdict ≠ PRESENT | "Halt: v0.50's A_null arm does not reproduce v0.48's spatial bridge — either a paired_d cell drifts beyond 1e-3 of the published value, or the A_null sub-verdict does not resolve to PRESENT. v0.50 cannot interpret the B / C arms without an established baseline." |
| 4 | `SENSOR_RADIUS_ROBUST_TO_POSITION` | (A_null PRESENT, B PRESENT, C PRESENT) | "v0.49's sensor_radius causal contribution survives founder-position controls on the modern A_null corpus: the v0.48 spatial / foraging bridge fires under both shifted-top and permuted founder positions." |
| 5 | `SENSOR_RADIUS_POSITION_INTERACTION_SUPPORTED` | A_null PRESENT AND BOTH (B sub-verdict ∈ {PARTIAL, NOT_FOUND}) AND (C sub-verdict ∈ {PARTIAL, NOT_FOUND}) | "v0.49's sensor_radius causal contribution shows position interaction on the modern A_null corpus: the v0.48 spatial / foraging bridge weakens under both shifted-top and permuted founder-position interventions." |
| 6 | `SENSOR_RADIUS_POSITION_INTERACTION_MIXED` | A_null PRESENT AND exactly one of (B, C) is PRESENT and the other is in {PARTIAL, NOT_FOUND} | "v0.49's sensor_radius causal contribution shows position interaction asymmetrically on the modern A_null corpus: the v0.48 spatial / foraging bridge weakens under exactly one of (shifted-top, permuted) founder-position interventions." |

The rollup is conservative and partitions the post-A_null-PRESENT space cleanly: ROBUST = both arms PRESENT; SUPPORTED = both arms weaken; MIXED = exactly one arm weakens. Every non-halt (B, C) combination maps to exactly one rollup. (When A_null is not PRESENT, `BRIDGE_REPLICATION_HALT` fires at priority 3 and the B/C interpretations are unreachable by design.)

### Bridge re-anchor against v0.48 (priority 3, byte-level halt)

A_null arm's six paired_d cells must reproduce v0.48's published signed_d values within `1e-3`:

| label | observable | v0.48 published signed_d |
|---|---|:-:|
| label_a_sensor_radius | pre50_food_events_count | +1.066 |
| label_a_sensor_radius | pre50_food_energy_acquired | +1.066 |
| label_a_sensor_radius | mean_distance_to_nearest_food_cell | +1.916 |
| label_b_readiness_fraction | pre50_food_events_count | +0.916 |
| label_b_readiness_fraction | pre50_food_energy_acquired | +0.916 |
| label_b_readiness_fraction | mean_distance_to_nearest_food_cell | +1.179 |

Drift tolerance = 1e-3. Same protocol as v0.49.

## Re-anchor (locked, A_null arm only, identical to v0.46/v0.47/v0.48/v0.49)

| version | published `a_share_h8` |
|---|---|
| v0.42 | 0.652 |
| v0.43R | NOT PUBLISHED (informational-only) |
| v0.44 | 0.878 |
| v0.45 | 0.818 |

B / C arms re-derive their own `a_share_h8` for descriptive logging; do NOT gate the verdict.

## Cautious framing (per CLAUDE.md)

- "**Survives founder-position controls**" — NOT "**proves position is irrelevant**". v0.50 tests two specific position interventions (shifted-top reflected band, permuted assignment); other position manipulations remain unprobed.
- "**Shows position interaction**" — NOT "**position is the cause**". A weakened bridge under B or C indicates position contributes; it does not isolate the mechanism.
- "**On the modern A_null corpus**" / "**under the locked V0_25 anchor**" — NOT a chamber-config-independent claim.
- v0.50 does not establish: cross-layout generalisation, sensor_radius mechanism (information vs cost), trait-position interactions beyond position alone, descendant-position effects.

## What v0.50 cannot establish

- ✗ **Mechanism for any position effect**. v0.50's interventions move founders to a different starting configuration; they do not isolate which downstream consequence (edge topology, capacity-1 contention, axial-sensor geometry, hazard-avoidance navigation) drives the observed difference.
- ✗ **Position-trait interactions**. v0.50 holds traits at the model's normal draw; if `sensor_radius` interacts with starting position non-trivially (e.g., wide-radius founders benefit more from edge positions because they see across the boundary), v0.50 cannot disentangle the interaction from the main effect.
- ✗ **Generalisation beyond V0_25 anchor / tight_gradient layout / 5 founders / height=6**. Position effects depend on geometry by construction; results may differ on other chambers.
- ✗ **B's metabolic equivalence to A_null**. Centered positions (y∈[1..5]) may shift the lineages' encounters with hazard cells and food respawn timing in subtle ways that affect cumulative metabolic cost. v0.50 logs but does not control for this; flagged as a watch-out.

## Open framing (NOT in v0.50)

- v0.51 candidate: clamp `sensor_radius` throughout the lineage (close descendant-drift channel from v0.49).
- v0.52 candidate: set `sensor_radius_metabolic_cost = 0` (decouple sensing from metabolic burden; isolate "information" from "cost").
- v0.53 candidate: cross-layout generalisation (run v0.48–v0.50 on `widened_gradient` and/or `food_ladder`).
- Fresh-stream calibration (v0.30-style) on the v0.49+v0.50 conclusion stack — needed eventually for any "mechanism" declaration.

## Outputs (locked)

```
runs/v0.50-position-confound/per_run_per_lineage_v050.csv
  columns: arm, version, seed, hazard, run_id, lineage_id,
           original_x, original_y, assigned_x, assigned_y, position_changed,
           founder_sensor_radius, founder_reproduction_drive, founder_metabolic_rate,
           pre50_food_events_count, pre50_food_energy_acquired,
           mean_distance_to_nearest_food_cell,
           tick50_living_count, tick50_above_threshold_count, tick50_above_threshold_fraction,
           b50_count, is_eventual_top_b50_label,
           is_high_sensor_radius_lineage, is_high_tick50_readiness_fraction_lineage,
           effective_position_changed_count

runs/v0.50-position-confound/per_run_intervention_audit.csv
  columns: arm, version, seed, hazard, lineage_id, founder_index,
           original_x, original_y, assigned_x, assigned_y,
           permutation_map_index, applied_identity_rotation_fallback,
           effective_position_changed_count

runs/v0.50-position-confound/audit_summary.csv
  columns: section, key, value
  sections:
    - reanchor_a_share_h8: per (arm, version, h=8) derived + (A_null only) published + drift_abs
    - bridge_reanchor: per (label, observable) v0.48 published signed_d + A_null derived signed_d + drift_abs
    - paired_d: per (arm, gating-label, observable) cell — paired_d, signed_d, n_runs, fires_expected, fires_wrong
    - sub_verdicts: per arm — sub-verdict + locked sub-phrase
    - rollup_verdict: locked rollup verdict + locked rollup phrase

runs/v0.50-position-confound/audit_log.txt
  human-readable echo with all locked phrases printed verbatim where they fire.
```

## Implementation plan (locked)

1. Fresh script `scripts/v0_50_founder_position_audit.py`. CLI: `uv run python scripts/v0_50_founder_position_audit.py [--out-dir runs/v0.50-position-confound]`.
2. Per (version, seed, hazard) tuple, run **3 arms**. Every arm constructs `HHModel` via the normal A_null path (`FounderSpec(traits_override=None)`):
   - **A_null**: no patch.
   - **B_position_shifted_top**: inside `setup_observer`, before tick-0 capture, replace each founder's `body.x`/`body.y` with `(spawn_x, shifted_y[founder_index])` (where `shifted_y = [1, 2, 3, 4, 5]`) and update `agent.cell`. Assert single-channel invariant + distinct cells.
   - **C_position_permuted**: inside `setup_observer`, generate non-identity permutation via `np.random.default_rng(seed).permutation(5)` (rotate-by-one fallback). Permute the 5 original `(x, y)` tuples across founders. Patch bodies + cells. Assert single-channel invariant + distinct cells.
3. For each arm-run, attach v0.48-style `setup_observer` + `tick_observer` (copy-local from v0.48/v0.49). The setup_observer applies the position patch (B / C) before capturing tick 0. Capture per-tick records for ticks 0..50 inclusive (51 snapshots); `AgentBorn` / `AteFood` / `HazardDamageApplied` listeners filtered by `sender=model`.
4. Aggregate per-lineage primaries identical to v0.48/v0.49. Compute label A and label B per the arm.
5. Compute paired_d per (arm, gating-label, observable) cell; classify per-arm sub-verdicts.
6. **Bridge re-anchor** (priority-3): compare A_null derived signed_d's to v0.48's published values; halt if drift > 1e-3.
7. **Corpus re-anchor** (priority-1): A_null arm only; halt if drift > 1e-3.
8. **Opposite-sign halt** (priority-2): scan all gating-label cells; halt if any signed_d ≤ −0.5.
9. Compute slice rollup verdict per the locked priority order; print + write the locked phrase verbatim.

The reducer is fully self-contained: it reads no `runs/` artifacts. Wall time ~15–30 minutes for 192 runs (matches v0.49's measured 10 minutes).

## Test list (locked, 16 tests)

`tests/test_v0_50_founder_position_audit.py`:

1. `test_all_arms_construct_founders_via_normal_a_null_path` — all three arms invoke `FounderSpec` with `traits_override=None`; original founder positions captured from live bodies are byte-identical across arms for the same seed.
2. `test_b_shifted_top_patch_replaces_only_x_y_on_live_bodies` — construct `HHModel` for one tuple; capture pre-patch founder bodies; apply B patch; assert all founders at `(spawn_x, shifted_y[i])` and every other body field byte-identical to pre-patch.
3. `test_a_null_arm_streams_mutation_state_byte_identical_across_arms` — for the same seed, original founder traits (full Traits records) captured at setup_observer time are byte-identical across arms (the patch never consumes `streams.mutation`).
4. `test_c_position_permutation_is_non_identity` — when the helper RNG draws identity, rotate-by-one fallback fires; `assigned_xy != original_xy` for at least one founder.
5. `test_c_position_patch_replaces_only_x_y_on_live_bodies` — apply C patch; assert non-(x,y) body fields byte-identical to pre-patch; assigned `(x, y)` set is a permutation of the original set.
6. `test_b_shifted_top_band_is_top_shifted_reflection_of_v025` — for `tight_gradient` (height=6), assert `shifted_y = [1, 2, 3, 4, 5]` (mean 3.0; lineage 4 at the top edge y=5) vs V0_25's `[0, 1, 2, 3, 4]` (mean 2.0; lineage 0 at the bottom edge y=0). The two bands are reflected: edge-exposure transfers from lineage 0 (V0_25) to lineage 4 (B). Neither band is centered on the geometric mid-row y=2.5.
7. `test_capacity_1_invariant_preserved_after_patch` — under each of B and C, all 5 patched cells are pairwise distinct.
8. `test_mesa_cell_pointer_aligned_after_patch` — after patch, `agent.cell.coordinate == (agent.body.x, agent.body.y)` for every founder.
9. `test_per_arm_subverdict_a_null_present_requires_both_labels_clear` — synthetic paired_d under A_null such that label A (+0.6, +0.7, −0.3) and label B (+0.6, +0.8, −0.2); assert sub-verdict = `A_NULL_BRIDGE_PRESENT`.
10. `test_per_arm_subverdict_b_shifted_top_partial_when_only_one_label_clears` — synthetic where label A clears 2/3 but label B clears 1/3 under B; assert sub-verdict = `B_POS_SHIFTED_TOP_BRIDGE_PARTIAL`.
11. `test_rollup_robust_when_all_three_arms_present` — synthetic (A_null PRESENT, B PRESENT, C PRESENT); assert rollup = `SENSOR_RADIUS_ROBUST_TO_POSITION`.
12. `test_rollup_supported_when_both_b_and_c_weaken` — synthetic (A_null PRESENT, B NOT_FOUND, C NOT_FOUND); assert rollup = `SENSOR_RADIUS_POSITION_INTERACTION_SUPPORTED`. Also test (PRESENT, PARTIAL, NOT_FOUND), (PRESENT, NOT_FOUND, PARTIAL), and (PRESENT, PARTIAL, PARTIAL) — all four "both arms in {PARTIAL, NOT_FOUND}" combinations resolve to SUPPORTED.
13. `test_rollup_mixed_when_exactly_one_arm_weakens` — synthetic (A_null PRESENT, B PRESENT, C NOT_FOUND); assert rollup = `SENSOR_RADIUS_POSITION_INTERACTION_MIXED`. Also test (PRESENT, NOT_FOUND, PRESENT), (PRESENT, PRESENT, PARTIAL), (PRESENT, PARTIAL, PRESENT) — all four "exactly one arm in {PARTIAL, NOT_FOUND}" combinations resolve to MIXED.
14. `test_rollup_partition_is_total_under_a_null_present` — exhaustively iterate the 9 (B sub-verdict ∈ {PRESENT, PARTIAL, NOT_FOUND}, C sub-verdict ∈ {PRESENT, PARTIAL, NOT_FOUND}) combinations under A_null PRESENT; assert each maps to exactly one of {ROBUST, SUPPORTED, MIXED}. Counts: ROBUST = 1, SUPPORTED = 4, MIXED = 4.
15. `test_bridge_replication_halt_on_signed_d_drift` — synthesise A_null cells where one drifts +1.5; assert `BRIDGE_REPLICATION_HALT`.
16. `test_corpus_rederive_drift_halt_priority_over_bridge_replication_halt` — synthesise both halt conditions; assert priority-1 `CORPUS_REDERIVE_DRIFT_HALT` fires first.

## Watch-outs (for future-Chronus)

- **B may not be metabolic-equivalent to A_null.** The shifted-top band `[1..5]` interacts with hazard cells (`x∈[3,4]`) and food cell respawn dynamics differently than V0_25's bottom-skewed `[0..4]` placement. If B's bridge weakens, v0.50 cannot disentangle "band reflection itself" from "downstream metabolic / hazard-encounter consequences of the new placement".
- **`AgentBody` is `@dataclass(frozen=True)`; `HHAgent.body` is reassignable**, and Mesa's `CellAgent.cell` setter handles cell occupancy updates automatically (verified at mesa_agents.py:184–187 for the action-step pattern). v0.50's patch reuses this idiom for tick-0 placement.
- **Patch order matters.** Inside `setup_observer`: (1) read original positions, (2) compute permutation (C only), (3) patch each body + cell pointer, (4) assert distinctness, (5) capture founder audit + tick-0 snapshot. The patch must happen before any food/hazard listener fires (none should at tick 0 since no step has run yet).
- **Helper RNG isolation** (same as v0.49): the C-arm permutation RNG never touches `streams.mutation`, never seeds from any model state. Test #3 enforces.
- **Hazard-paired runs share permutation maps** (same as v0.49 C-arm).
- **Effective changed count for arm C**: in arm C, position permutation is on a set of 5 distinct (x,y) tuples, so `assigned != original` for any founder whose `perm[i] != i`. The effective changed count is 4 or 5 in every non-identity-fallback C run (a non-identity permutation on 5 distinct elements moves at least 2 elements; commonly 4–5). Logged in audit.
- **Bridge replication halt is byte-level critical.** v0.50's A_null arm runs the same code path as v0.48/v0.49 A_null. The cells must reproduce within 1e-3.
- **Locked phrase discipline**: all sub-verdict and rollup phrases fire verbatim. No paraphrase.
- **Determinism north star** (`scripts/core_smoke_test.py`) must continue to pass; v0.50 makes no `src/` change.

## Files this slice will create

- `docs/experiments/fear_hunger_v0.50.md` (this file; Results appended after reducer run)
- `scripts/v0_50_founder_trait_covariance_preflight.py` (already committed at `d8c3e20`)
- `scripts/v0_50_founder_position_audit.py`
- `tests/test_v0_50_founder_position_audit.py`

No other files modified.

## Results

**Status:** reducer executed 2026-05-08 against the 192-run corpus (3 arms × 64 (version, seed, hazard) tuples). Wall time ~10 minutes. **All bridge re-anchor cells PASS** (A_null arm reproduces v0.48's six published signed_d cells within 0.0004 ≪ 1e-3 tolerance). All A_null arm `a_share_h8` values reproduce v0.42 / v0.44 / v0.45 published references within 0.0003. No opposite-sign firings under any gating label. **Every single one of the 18 paired_d cells (3 arms × 2 labels × 3 observables) fires in the expected direction with signed_d ≥ +0.5.**

### Rollup verdict — `SENSOR_RADIUS_ROBUST_TO_POSITION` fires

> **Locked phrase fires verbatim:** "v0.49's sensor_radius causal contribution survives founder-position controls on the modern A_null corpus: the v0.48 spatial / foraging bridge fires under both shifted-top and permuted founder positions."

Sub-verdicts:

| arm | sub-verdict |
|---|---|
| A_null | `A_NULL_BRIDGE_PRESENT` |
| B_position_shifted_top | `B_POS_SHIFTED_TOP_BRIDGE_PRESENT` |
| C_position_permuted | `C_POS_PERM_BRIDGE_PRESENT` |

The (PRESENT, PRESENT, PRESENT) triple is the ROBUST pattern — the strongest possible support for v0.49's `SENSOR_RADIUS_CAUSAL_CONTRIBUTION_SUPPORTED` claim under v0.50's locked criteria.

### Bridge re-anchor — A_null arm reproduces v0.48 within 1e-3

| label | observable | published | derived | drift |
|---|---|:-:|:-:|:-:|
| label_a_sensor_radius | pre50_food_events_count | +1.066 | +1.066 | 0.0004 |
| label_a_sensor_radius | pre50_food_energy_acquired | +1.066 | +1.066 | 0.0004 |
| label_a_sensor_radius | mean_distance_to_nearest_food_cell | +1.916 | +1.916 | 0.0001 |
| label_b_readiness_fraction | pre50_food_events_count | +0.916 | +0.916 | 0.0001 |
| label_b_readiness_fraction | pre50_food_energy_acquired | +0.916 | +0.916 | 0.0001 |
| label_b_readiness_fraction | mean_distance_to_nearest_food_cell | +1.179 | +1.179 | 0.0004 |

Max drift 0.0004 ≪ 1e-3. v0.50's A_null arm is byte-compatible with v0.48 / v0.49's A_null path; B / C interpretations are anchored at the same baseline.

### Per-arm signed_d (sign-aware, all firing)

| arm | label | obs1: events | obs2: energy | obs3: distance |
|---|---|:-:|:-:|:-:|
| A_null | label_a_sensor_radius | +1.066 | +1.066 | +1.916 |
| A_null | label_b_readiness_fraction | +0.916 | +0.916 | +1.179 |
| B_position_shifted_top | label_a_sensor_radius | **+1.168** | **+1.168** | **+2.115** |
| B_position_shifted_top | label_b_readiness_fraction | **+1.041** | **+1.041** | **+1.452** |
| C_position_permuted | label_a_sensor_radius | +1.073 | +1.073 | +1.987 |
| C_position_permuted | label_b_readiness_fraction | +0.899 | +0.899 | +1.078 |

Notable: B's signed_d's are *higher* than A_null's on every label A cell (+1.168 vs +1.066; +2.115 vs +1.916), and on label B observables 1/2 (+1.041 vs +0.916). The shifted-top reflection does not weaken the bridge — it modestly strengthens it. See "Reading the result correlationally" for one plausible interpretation.

### Corpus re-anchor

A_null arm — all PASS (max drift 0.0003):

| version | derived `a_share_h8` | published | drift |
|---|:-:|:-:|:-:|
| v0.42 | 0.652 | 0.652 | 0.0003 |
| v0.43R | 0.674 | — (informational) | — |
| v0.44 | 0.878 | 0.878 | 0.0001 |
| v0.45 | 0.818 | 0.818 | 0.0002 |

B and C arms (informational only — different counterfactual worlds):

| arm | v0.42 | v0.43R | v0.44 | v0.45 |
|---|:-:|:-:|:-:|:-:|
| B_position_shifted_top | 0.718 | 0.591 | 0.798 | 0.776 |
| C_position_permuted | 0.638 | 0.606 | 0.896 | 0.805 |

B's `a_share_h8` is generally higher than A_null's at v0.42 / v0.44 (0.718 / 0.798 vs 0.652 / 0.878 — comparable to higher); v0.43R drops from 0.674 to 0.591 and v0.45 drops from 0.818 to 0.776 — small movements consistent with B being a different counterfactual world.

### Reading the result correlationally

The locked phrase is **correlational, not causal**. v0.50 establishes that the v0.48 spatial / foraging bridge **survives** two specific position interventions; it does NOT prove position is causally irrelevant. Several interpretations are consistent with the data:

- **Most parsimonious**: founder `sensor_radius` variation is the dominant within-run driver of the spatial / foraging bridge. The lineage-id ↔ position structure (V0_25's `[0..4]` band, lineage 0 at the global y=0 edge) does not contribute meaningfully on this corpus.
- **B's bridge strengthens slightly under shifted-top.** One plausible reading: V0_25's lineage 0 (at y=0) carries an edge-topology drag (only y=1 as a y-neighbor; cannot move y-down) that *weakens* the bridge when the high-`sensor_radius` lineage happens to be lineage 0. Reflecting the band to `[1..5]` (lineage 4 at the global y=5 edge) preserves *one* edge-disadvantaged founder but moves it from lineage 0 to lineage 4 — and label A's argmax-with-min-id-tiebreak no longer disproportionately picks the disadvantaged lineage. Bridge cells become slightly cleaner. **This is interpretation, not a verdict-firing finding** — the locked criteria do not distinguish "ROBUST" from "ROBUST-and-stronger".
- **C's bridge tracks A_null almost exactly.** Permuting founder positions among themselves preserves the bridge structure within ±0.1 signed_d on every cell. The bridge does not depend on which founder gets which V0_25 spawn slot.

### What v0.50 establishes (within the locked V0_25 + tight_gradient + 5-founder anchor)

- ✓ The v0.48 spatial / foraging bridge **fires under shifted-top reflection** of the V0_25 founder band, with effect sizes comparable to or slightly larger than A_null. Founder-band placement, narrowly defined as one of the two contiguous-5-cell options on a height-6 grid, does not break the bridge.
- ✓ The v0.48 spatial / foraging bridge **fires under within-band founder permutation**, with effect sizes within ±0.1 of A_null. The lineage-id ↔ position assignment under V0_25 is not the bridge's source.
- ✓ A_null arm is byte-compatible with v0.48 / v0.49 (bridge re-anchor max drift 0.0004; corpus re-anchor max drift 0.0003).
- ✓ Combined with v0.49's `SENSOR_RADIUS_CAUSAL_CONTRIBUTION_SUPPORTED`, the conclusion stack now reads: founder `sensor_radius` variation supports a causal contribution to the bridge, AND that conclusion survives shifted-top and permuted founder-position interventions on the modern A_null corpus.

### What v0.50 does NOT establish

- ✗ **General position-irrelevance**. v0.50 tests two specific position interventions (shifted-top reflection, within-band permutation). It does NOT test: cross-x positioning (e.g., founders at x=0 or x=2), cross-band positioning (e.g., scattered around the layout), founders inside the food zone, founders with different (x, y) offsets, or any position pattern outside the contiguous-5-cell-at-spawn_x band.
- ✗ **Cross-layout generalisation**. Tight_gradient height=6 only.
- ✗ **Trait-position interaction**. v0.50 holds traits at the model's normal draw; if `sensor_radius` interacts with founder position non-trivially in some untested geometry, v0.50 cannot detect it.
- ✗ **Mechanism for B's modest signed_d uplift.** The +1.168 / +2.115 vs A_null's +1.066 / +1.916 is consistent with multiple stories; v0.50 does not distinguish them.
- ✗ **Cross-anchor / cross-policy generalisation**. V0_25 anchor only.
- ✗ **Causality for post-tick-50 dominance**. v0.50 measures the v0.48 bridge cells; the v0.46 dominance question remains observational.

### Caveats

- **B is not a "no-position-variance" arm.** Both `[0..4]` and `[1..5]` have identical pairwise y-distances (just shifted by one row); the population variance of y is `Var([0..4]) = Var([1..5]) = 2.0`. v0.50's B arm tests **band reflection**, not "position equalisation". A future slice could probe true position equalisation by, for example, placing 5 founders at distinct cells with minimal pairwise y-spread (which is impossible given capacity=1 in a column-only spawn pattern).
- **Trait-covariance preflight is descriptive only.** Pearson and Spearman correlations were small (max |ρ| = 0.144) but pairwise correlations do not exclude nonlinear or interaction effects. Trait covariance remains a deferred consideration for future slices.
- **Hazard-paired runs share permutation maps for arm C.** Per pre-reg watch-out: the helper RNG is seeded from `seed` alone (not `(seed, hazard)`), so for a given (version, seed) the C-arm runs at h=0 and h=8 receive identical permutations.
- **Cross-arm signed_d differences are descriptive, not verdict-firing.** The locked verdict structure says "PRESENT vs PARTIAL vs NOT_FOUND", which captures the +0.5 threshold crossing. Magnitude differences within "PRESENT" (e.g., +1.066 vs +1.168) are not part of the locked criteria.

### Cross-corpus context

| slice | corpus | claim | strength |
|---|---|---|---|
| v0.46 | modern A_null | tick-50 readiness predicts dominance | observational (PRESENT) |
| v0.47 | modern A_null | founder `sensor_radius` predicts tick-50 readiness | observational (PARTIAL — only `sensor_radius` fires) |
| v0.48 | modern A_null | `sensor_radius` ↔ spatial bridge | observational (PRESENT under both labels) |
| v0.49 | modern A_null | founder `sensor_radius` causal contribution | interventional (SUPPORTED via clamp + permutation) |
| v0.50 | modern A_null | v0.49's contribution survives position controls | interventional (ROBUST under shifted-top + permutation) |

Each subsequent slice tightens the inferential chain. The v0.46→v0.50 stack is now: tick-50 readiness predicts dominance → founder `sensor_radius` predicts readiness → `sensor_radius` co-occurs with spatial advantage → causal contribution from `sensor_radius` survives clamp + permutation → and that causal contribution survives shifted-top + permuted founder positions.

### v0.51 candidates (open; not locked)

Per the pre-reg's "Open framing" + new follow-ups suggested by the v0.50 finding:

- **v0.51 — clamp `sensor_radius` throughout the lineage** (close descendant-drift channel from v0.49). Tests whether the bridge depends on *founder-only* `sensor_radius` variation or on lineage-wide `sensor_radius` heterogeneity.
- **v0.52 — `sensor_radius_metabolic_cost = 0`**. Decouples sensing radius from metabolic cost. Distinguishes "information radius" from "metabolic burden".
- **v0.53 — cross-layout generalisation**. Run v0.48–v0.50 on `widened_gradient` and / or `food_ladder`. Tests whether the bridge claim is layout-invariant.
- **Eventual fresh-stream calibration** (v0.30-style) on the v0.46–v0.50 stack — needed for any "mechanism" declaration; currently all claims are correlational or causal-with-confound-disclosed.

### CI gate at v0.50 close

```
uv run ruff check .             ok
uv run ruff format --check .    ok
uv run pytest                   1648 passed, 7 skipped (was 1632, +16 v0.50)
uv run python scripts/core_smoke_test.py                      ok
uv run python scripts/v0_50_founder_position_audit.py         SENSOR_RADIUS_ROBUST_TO_POSITION
```
