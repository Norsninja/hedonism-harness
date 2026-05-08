# fear_hunger v0.52b — sensor_radius information-radius assignment shuffle

**Slice:** v0.52b
**Type:** **first-class intervention** (NOT a post-hoc reducer); paired channel-decoupling probe (between-lineage information-radius shuffle, global ecology preserved).
**Predecessors:** v0.21..v0.27, v0.34..v0.36, v0.42..v0.45, v0.46 (`READINESS_PREDICTS_DOMINANCE`), v0.47 (`READINESS_TRAITS_PARTIALLY_PREDICTIVE`), v0.48 (`SENSOR_RADIUS_SPATIAL_BRIDGE_PRESENT`), v0.49 (`SENSOR_RADIUS_CAUSAL_CONTRIBUTION_SUPPORTED`), v0.50 (`SENSOR_RADIUS_ROBUST_TO_POSITION`), v0.51 (`FOUNDER_CLAMP_REPRODUCED`), v0.52 (`INTERVENTION_OPPOSITE_SIGN_HALT` — B confirms metabolic-cost channel not necessary for the bridge; C uniform-max-radius produced wrong-sign Label B and the locked halt fired).
**Question being asked (locked):** Does the `sensor_radius` spatial / foraging bridge depend on between-lineage information-radius assignment when the global information economy is preserved?

v0.52 closed the metabolic-cost-channel question (the bridge survives `sensor_radius_metabolic_cost = 0.0` cleanly) but its information-channel arm (`C_uniform_effective_radius_6`) was not a clean information-radius probe — uniform max sensing is intervention-incompatible with the locked expected signs and the priority-2 halt fired. v0.52's locked `What v0.52 cannot claim` list explicitly forbade reading the C halt as evidence either FOR or AGAINST information radius being load-bearing for the bridge.

v0.52b reframes the information-channel question with a different intervention design: instead of equalizing every agent to a uniform value (which globally changes the sensory economy), **shuffle the per-lineage effective `sensor_radius` over a corpus-wide preserved distribution**. Each lineage receives a different agent's draw of `sensor_radius` as its `effective_sensor_radius_override`; the population-level distribution of effective sensing radii is exactly preserved, but the trait↔lineage link is broken. Metabolic cost continues to follow the original (unchanged) trait `sensor_radius` — the metabolic-cost channel is unchanged from A_null. Only the between-lineage information-radius assignment is perturbed.

If the bridge still fires under shuffle (Label A defined from the *assigned* effective override), the information-radius assignment is sufficient to track the bridge under preserved global ecology — supporting the information-radius channel's contribution. If the bridge does not fire, the original trait/lineage package or another confound is implicated; information-radius assignment alone is not sufficient.

## Pre-implementation correction (2026-05-08, before any reducer code)

The implementation path was investigated post-design-review per CLAUDE.md "pre-reg stands as the historical record". Recorded here for transparency. No data has been seen yet.

### One minimal `src/` extension to support per-lineage information-radius assignment

v0.52 added `BodyConfig.effective_sensor_radius_override: int | None = None` (a single model-wide int). v0.52b's per-lineage shuffle requires *per-agent* override semantics, which `BodyConfig` cannot represent. Three default-preserving touches:

1. **`src/hedonism_harness/core/traits.py`**:
   - Add `effective_sensor_radius_override: int | None = None` field to `Traits` (default None preserves backward compat).
   - **Filter the new field out of `TRAIT_NAMES`**: change to `tuple(f.name for f in fields(Traits) if f.name != "effective_sensor_radius_override")`. This keeps `random_traits`, `mutate_traits`, `validate_traits`, archetype-builder, and metrics collectors unaware of the experimental field — they continue to iterate only over biological traits, exactly as today. The override is on `Traits` for the data layout but is NOT treated as a biologically-mutable trait.
   - **Update `mutate_traits` to use `dataclasses.replace(parent, **values)` instead of `Traits(**values)`**. Behaviorally identical when `values` covers all fields (which is the case for the existing 13 biological traits); the change unlocks inheritance of fields not in `TRAIT_NAMES`. **Descendants automatically inherit the parent's `effective_sensor_radius_override` via `replace`** — no `AgentBorn` listener required for inheritance. This is the user-locked Option α (lineage-coherent).
2. **`src/hedonism_harness/core/sensors.py:123`** (observe): updated resolver checks per-agent override first, then per-model override, then falls back to trait:
   ```python
   override = (
       body.traits.effective_sensor_radius_override
       if body.traits.effective_sensor_radius_override is not None
       else body_config.effective_sensor_radius_override
   )
   radius = override if override is not None else int(body.traits.sensor_radius)
   ```
3. **`src/hedonism_harness/core/sensors.py:196`** (`_read_memory_directional`, ValenceMemory branch only): same resolver pattern. DirectionalMemory branch unchanged.

`apply_metabolism` is **NOT** modified. The metabolic-cost channel continues to read `body_config.sensor_radius_metabolic_cost * body.traits.sensor_radius` — the per-agent override has no effect on metabolic cost.

### Determinism story (locked)

- **A_null arm**: byte-identical to v0.48 / v0.49 / v0.50 / v0.51 / v0.52 A_null path. All agents have `body.traits.effective_sensor_radius_override = None`; `body_config.effective_sensor_radius_override = None`; resolver falls through to `int(body.traits.sensor_radius)` exactly as before. Tier-1 re-anchor enforces this within 1e-3.
- **B arm**: founder bodies are patched at `setup_observer` time with `dataclasses.replace(agent.body, traits=dataclasses.replace(agent.body.traits, effective_sensor_radius_override=assigned_value))`. RNG streams (`streams.mutation`, per-agent RNGs) are byte-identical to A_null at the moment of the first `model.step()`. Pre-50 trajectories diverge from A_null because effective sensing differs per agent, NOT because of RNG offset.
- **Default-equivalence test** (locked, see Test list #5): with both override fields `None` and default `sensor_radius_metabolic_cost = 0.05`, the modified `sensors.py` and `traits.py` reproduce existing A_null outputs byte-identically. Corpus-level enforcement: the 1680-test pytest suite (which includes v0.52's tests under the modified `sensors.py`) continues to pass without modification under the v0.52b src/ change.

### Lineage-coherent inheritance via `mutate_traits` (locked Option α)

Descendants inherit the parent's `effective_sensor_radius_override` automatically via `dataclasses.replace(parent, **values)`. The override is **not biologically mutated** in v0.52b — it is an experimental lineage assignment propagated through descent to preserve intervention coherence. If a future slice wants to mutate the override (e.g., add Gaussian noise per generation), it would be a separate locked design decision; v0.52b explicitly does NOT mutate it.

**Halt-loud invariant on inheritance failure** (locked): at end of each B-arm run, the reducer walks all newborn agents (collected via `AgentBorn` listener log) and verifies every newborn's `body.traits.effective_sensor_radius_override` is non-None. Any descendant with `None` increments `descendant_override_missing_count`; if the corpus-wide total is > 0, the slice rollup fires `SHUFFLE_DESCENDANT_INHERITANCE_HALT` (priority 4). This guards against silent inheritance failures (e.g., a future refactor of `_spawn_child` that bypasses `mutate_traits`).

This correction does not change the verdict structure, arm count, corpus, observable definitions, label gating, re-anchor strategy, or rollup outcome set.

## Conservation framing — interventional, with one minimal `src/` extension

- **One `src/` modification, building on v0.52's existing `BodyConfig` field**:
  - `core/traits.py`: new `effective_sensor_radius_override: int | None = None` field on `Traits`; `TRAIT_NAMES` filtered to exclude it; `mutate_traits` uses `dataclasses.replace`.
  - `core/sensors.py`: resolver pattern updated at two read sites to check per-agent override first.
  - **Default `None` preserves byte-identity** for every existing test, every prior reducer's A_null arm, and `core_smoke_test.py`. v0.52b is the second slice in the v0.46+ stack to touch `src/`; both touches are minimum-viable and forward-compatible.
- **No modifications to prior reducer or audit scripts.** v0.34's `lineage_replay.py`, v0.35's `lineage_survival_replay.py`, v0.36's `trait_replay.py`, the four substrate audits, and v0.46 / v0.47 / v0.48 / v0.49 / v0.50 / v0.51 / v0.52's reducers remain byte-identical to their merged forms.
- **A_null arm is byte-identical to v0.48 / v0.49 / v0.50 / v0.51 / v0.52's A_null path** (default `effective_sensor_radius_override = None` everywhere). Tier-1 re-anchor enforces this at metric level.
- **No `traits_override`.** All arms use `FounderSpec(traits_override=None)`; v0.52b manipulates the per-agent override field on the post-construction body's traits.
- **No agent body trait mutation of biological traits.** v0.52b modifies only the `effective_sensor_radius_override` field on `body.traits`, which is not a biologically-mutable trait (filtered out of `TRAIT_NAMES`).
- **No mutation pipeline modification beyond the `dataclasses.replace` widening.** `mutate_traits` continues to iterate `TRAIT_NAMES` and apply the existing per-trait Gaussian mutation logic. The override propagates through inheritance precisely because it is NOT in `TRAIT_NAMES` — `replace` preserves it from the parent.
- **No descendant-time intervention.** Unlike v0.51, v0.52b does NOT register an `AgentBorn` listener for the intervention itself (inheritance is mechanical via `mutate_traits`). An `AgentBorn` listener IS registered for the descendant audit (counts inheritance vs missing) but does not modify any agent state.
- **No Mesa cell occupancy modification.**
- **Single-channel intervention.** The B arm modifies ONLY the `effective_sensor_radius_override` field on each founder's `body.traits`. A runtime invariant (`V052bReducerError`) compares pre-patch and post-patch trait vectors on every founder and asserts every field except `effective_sensor_radius_override` is byte-identical. Halts loud on any non-override field difference.
- **`apply_metabolism` is unaffected.** The metabolic-cost channel continues to follow the original (unchanged) trait `sensor_radius`.

## Corpus (locked, 64 × 2 arms = 128 runs)

| version | seeds | hazards | runs per arm | total runs |
|---|---|---|---|---|
| v0.42 | 41..48 | {0, 8} | 16 | 32 |
| v0.43R | 49..56 | {0, 8} | 16 | 32 |
| v0.44 | 57..64 | {0, 8} | 16 | 32 |
| v0.45 | 65..72 | {0, 8} | 16 | 32 |
| **total** | | | | **128** |

V0_25 anchor unchanged from v0.46–v0.52. Each (version, seed, hazard) tuple is run **2 times** — once per arm. Wall time estimate ~7 minutes for 128 runs (2/3 of v0.52's 3-arm wall time).

## Default V0_25 founder draw (for reference)

`tight_gradient` layout, 5 founders. `TraitConfig(unbounded_mutation=True)` draws integer-valued `sensor_radius` from {1..6}. Founder positions per `spread_y(5, 6)` = `[(1,0), (1,1), (1,2), (1,3), (1,4)]`. Same as v0.48–v0.52.

## Arms (locked, 2)

### A_null

```
no patch, no body_config override, no per-agent override
```

`HHModel` constructed with default `body_config=None` → `BodyConfig()` with default `sensor_radius_metabolic_cost=0.05`, `effective_sensor_radius_override=None`. All founders have `body.traits.effective_sensor_radius_override = None` (default from `random_traits`). Founder traits, agent RNGs, and `streams.mutation` byte-identical to v0.48 / v0.49 / v0.50 / v0.51 / v0.52 A_null.

### B_effective_radius_shuffle_distribution

For each (version, seed, hazard) tuple, the reducer constructs `HHModel` normally and patches founder traits inside `setup_observer`, before tick-0 capture:

1. `HHModel(...)` returns with 5 founder agents constructed normally; `random_traits` and `spawn_agent_rng` consume from `streams.mutation` exactly as A_null.
2. Inside `setup_observer`, sort founders by lineage_id and read `original_sr = [int(a.body.traits.sensor_radius) for a in founders]`.
3. Generate a permutation using a script-local helper RNG (used **only** for the permutation map, never for trait values):
   ```python
   helper_rng = np.random.default_rng(seed)
   perm = helper_rng.permutation(5)
   if list(perm) == [0, 1, 2, 3, 4]:
       perm = np.array([1, 2, 3, 4, 0])  # rotate-by-one fallback
   ```
4. Compute `assigned_effective = [original_sr[perm[i]] for i in range(5)]`.
5. For each founder `i`, atomically replace the body and traits:
   ```python
   new_traits = dataclasses.replace(
       founders[i].body.traits,
       effective_sensor_radius_override=int(assigned_effective[i]),
   )
   founders[i].body = dataclasses.replace(founders[i].body, traits=new_traits)
   ```
6. **Single-channel founder invariant** (locked): for every founder, every Traits field except `effective_sensor_radius_override` is byte-identical between original and assigned. Halts loud (`V052bReducerError`) on any non-override field difference. In particular, `body.traits.sensor_radius` is unchanged — metabolic cost remains trait-tied.
7. Capture the v0.52b founder audit (lineage_id → original_sensor_radius, assigned_effective_sensor_radius, permutation_map_index, applied_identity_rotation_fallback) by reading the patched bodies from `model.agents`.
8. Compute and log per-run `effective_sensor_radius_changed_count = sum(1 for i in range(5) if assigned_effective[i] != original_sr[i])`. As under v0.49 C-arm: a non-identity permutation does NOT guarantee that any founder's assigned value differs from its original (the V0_25 trait config draws integer `sensor_radius` from {1..6}, so duplicates are common — e.g., original `[3, 3, 3, 5, 5]` with perm `[1, 2, 3, 4, 0]` → assigned `[3, 3, 5, 5, 3]`, only 2 founders changed). Logged for transparency; does NOT exclude low-changed-count runs from the paired_d pool.

The helper RNG is fully isolated from the model's RNG streams (same idiom as v0.49 / v0.50 C-arm). It does not touch `model.streams.mutation` or any per-agent `agent_rng`.

**Lineage-coherent descendant inheritance** (Option α, locked): descendants of B-arm founders automatically inherit the parent's `effective_sensor_radius_override` via the widened `mutate_traits` (`dataclasses.replace(parent, **values)` preserves fields not in `TRAIT_NAMES`). No `AgentBorn` listener intervention needed for inheritance. The pre-50 corpus shows ~24 births/run on average (v0.51 measurement); every descendant in B's pool inherits a non-None override from its parent.

**Audit listener** (locked): an `AgentBorn` listener is registered (separately from inheritance — it does not modify state) to count descendant inheritance and surface any violations:
- `descendant_override_inheritance_count`: number of births where `body.traits.effective_sensor_radius_override is not None` at AgentBorn-emit time.
- `descendant_override_missing_count`: number where it IS None — must be 0 under correct implementation.

## Labels (locked, two)

Both labels gate the verdict for **both arms**. Founder `sensor_radius` (the trait) is preserved in every arm; the override is the new degree of freedom under B.

### Label A — `high_information_radius_lineage`

```
high_information_radius_lineage =
    argmax_lineage(
        founder.body.traits.effective_sensor_radius_override
        if not None
        else int(founder.body.traits.sensor_radius)
    )
    tiebreak: min(lineage_id)
```

- Under **A_null**: every founder has `effective_sensor_radius_override = None` → falls through to `int(founder.body.traits.sensor_radius)` → identical to v0.48–v0.52 A_null Label A definition.
- Under **B**: every founder has `effective_sensor_radius_override = assigned_effective[i]` (an integer in {1..6}) → Label A picks the lineage with the **highest assigned effective override**, NOT the highest original trait. This is the entire point of the arm: ask whether the bridge follows the *assigned* information radius.

Tiebreak `min(lineage_id)` per v0.48–v0.52 convention; integer-valued override will tie frequently among 5 founders.

### Label B — `high_tick50_readiness_fraction_lineage`

Identical to v0.47–v0.52 (3-tier tiebreak: fraction → count → min(lineage_id), NaN-loses). Copy-local from v0.48 reducer.

## Primary observables (locked, 3, identical to v0.48–v0.52)

| # | name | expected sign |
|---|---|:-:|
| 1 | `pre50_food_events_count` | + |
| 2 | `pre50_food_energy_acquired` | + |
| 3 | `mean_distance_to_nearest_food_cell` | − |

Definitions, aggregation rules, NaN handling: copy-local from v0.48–v0.52. Per-tick observer firing semantics unchanged (tick 0 captured at `setup_observer` time AFTER the founder trait patch; ticks 1..50 captured by `tick_observer`).

## Effect-size rule (locked, sign-aware, identical to v0.48–v0.52)

```
per_run_delta_O = label_lineage_value_O − mean(non_label_lineage_values_O)
paired_d_O      = mean(per_run_delta_O) / stdev(per_run_delta_O, ddof=1)
signed_d_O      = paired_d_O × expected_sign
fires_expected  iff signed_d_O ≥ +0.5
fires_wrong     iff signed_d_O ≤ −0.5
```

## Per-arm sub-verdicts (locked, 4-way each)

Both arms gate on Label A AND Label B (no diagnostic-only label degeneracy):

| condition | A_null sub-verdict | B sub-verdict |
|---|---|---|
| both labels clear ≥ 2/3, 0 wrong-sign | `A_NULL_BRIDGE_PRESENT` | `B_SHUFFLE_BRIDGE_PRESENT` |
| exactly one label clears ≥ 2/3, 0 wrong-sign | `A_NULL_BRIDGE_PARTIAL` | `B_SHUFFLE_BRIDGE_PARTIAL` |
| neither label clears ≥ 2/3, 0 wrong-sign | `A_NULL_BRIDGE_NOT_FOUND` | `B_SHUFFLE_BRIDGE_NOT_FOUND` |
| any primary signed_d ≤ −0.5 under either label | `A_NULL_BRIDGE_OPPOSITE_SIGN_HALT` | `B_SHUFFLE_OPPOSITE_SIGN_HALT` |

Each arm's paired_d cells (3 observables × 2 labels = 6 cells per arm; 12 cells total across both arms) are computed independently from the arm's 64-run pool.

## Slice rollup verdicts (locked, 7 outcomes, priority-ordered)

Priority order (first-matching wins):

1. `CORPUS_REDERIVE_DRIFT_HALT`
2. `INTERVENTION_OPPOSITE_SIGN_HALT`
3. `BRIDGE_REPLICATION_HALT` (Tier-1 A_null vs v0.48)
4. `SHUFFLE_DESCENDANT_INHERITANCE_HALT` (lineage coherence guard)
5. `INFORMATION_RADIUS_FOLLOWS_ASSIGNMENT`
6. `INFORMATION_RADIUS_DOES_NOT_FOLLOW_ASSIGNMENT`
7. `INFORMATION_RADIUS_ASSIGNMENT_PARTIAL`

### Halt conditions

| priority | rollup verdict | trigger | locked phrase (verbatim) |
|---|---|---|---|
| 1 | `CORPUS_REDERIVE_DRIFT_HALT` | A_null arm `a_share_h8` for any of v0.42 / v0.44 / v0.45 drifts > 1e-3 from the published reference | "Halt: A_null re-anchor drifted from the published Results value for {version}; v0.52b's deterministic re-execution does not reproduce the published metric within 1e-3." |
| 2 | `INTERVENTION_OPPOSITE_SIGN_HALT` | any arm's gating-label primary signed_d ≤ −0.5 | "Halt: a v0.52b spatial / foraging primary fires in the WRONG direction under a gating label; the between-lineage information-radius shuffle is incompatible with the locked expected signs." |
| 3 | `BRIDGE_REPLICATION_HALT` | (a) A_null arm's signed_d for any of the six v0.48 cells drifts > 1e-3 from the v0.48 published value, OR (b) A_null sub-verdict ≠ `A_NULL_BRIDGE_PRESENT` | "Halt: v0.52b's A_null arm does not reproduce v0.48's spatial bridge — either a paired_d cell drifts beyond 1e-3 of the published value, or the A_null sub-verdict does not resolve to PRESENT. v0.52b cannot interpret the B arm without an established baseline." |
| 4 | `SHUFFLE_DESCENDANT_INHERITANCE_HALT` | corpus-wide `descendant_override_missing_count` > 0 in arm B (any descendant under shuffle has `effective_sensor_radius_override = None` at AgentBorn-emit time) | "Halt: at least one descendant agent in v0.52b's shuffle arm has `effective_sensor_radius_override = None` at end-of-run, violating lineage coherence. v0.52b cannot interpret the shuffle arm without verified descendant inheritance." |

### Tier-1 (priority 3) re-anchor — A_null vs v0.48

A_null arm's six paired_d cells must reproduce v0.48's published signed_d values within 1e-3:

| label | observable | sign | v0.48 published signed_d |
|---|---|:-:|:-:|
| `label_a_information_radius` | `pre50_food_events_count` | + | **+1.066** |
| `label_a_information_radius` | `pre50_food_energy_acquired` | + | **+1.066** |
| `label_a_information_radius` | `mean_distance_to_nearest_food_cell` | − | **+1.916** |
| `label_b_readiness_fraction` | `pre50_food_events_count` | + | **+0.916** |
| `label_b_readiness_fraction` | `pre50_food_energy_acquired` | + | **+0.916** |
| `label_b_readiness_fraction` | `mean_distance_to_nearest_food_cell` | − | **+1.179** |

Drift tolerance = 1e-3. Same protocol as v0.49–v0.52. Note: the label name changes from `label_a_sensor_radius` (v0.48–v0.52) to `label_a_information_radius` (v0.52b) because under B the label picks by *effective override*, not by trait `sensor_radius`. Under A_null the resolved value is identical (override is None → trait), so the Tier-1 cells reproduce v0.48 byte-equivalently.

**No Tier-2 re-anchor.** B is a new intervention never run before; there is no published reference cell to byte-anchor it against. Validity is anchored by Tier-1 + the four locked implementation-equivalence tests (default-equivalence, no RNG offset, override reaches both information-radius reads, override does NOT affect apply_metabolism or DirectionalMemory) + the `mutate_traits` inheritance test.

### Outcome conditions (only consulted if no halt fires)

| priority | rollup verdict | (A_null, B) sub-verdicts | locked phrase (verbatim) |
|---|---|---|---|
| 5 | `INFORMATION_RADIUS_FOLLOWS_ASSIGNMENT` | (A_NULL_BRIDGE_PRESENT, B_SHUFFLE_BRIDGE_PRESENT) | "On the modern A_null corpus with global information economy preserved (between-lineage shuffle of effective `sensor_radius` over a corpus-wide preserved distribution), the v0.48 spatial / foraging bridge follows the assigned effective information radius. The information-radius assignment is sufficient to track the bridge under the locked V0_25 anchor." |
| 6 | `INFORMATION_RADIUS_DOES_NOT_FOLLOW_ASSIGNMENT` | (A_NULL_BRIDGE_PRESENT, B_SHUFFLE_BRIDGE_NOT_FOUND) | "On the modern A_null corpus with global information economy preserved, the v0.48 spatial / foraging bridge does not follow the assigned effective information radius under between-lineage shuffle. The original trait/lineage package or another confound is implicated; the information-radius assignment alone is not sufficient to track the bridge." |
| 7 | `INFORMATION_RADIUS_ASSIGNMENT_PARTIAL` | (A_NULL_BRIDGE_PRESENT, B_SHUFFLE_BRIDGE_PARTIAL) | "On the modern A_null corpus, v0.52b's shuffle arm does not resolve to a single categorical outcome under the locked criteria; the bridge fires under one label but not the other. The planned v0.52b uniform-4 secondary follow-up is recommended for disambiguation." |

The rollup is **categorical-only** — no magnitude-delta rule between A_null and B. Magnitude differences in B vs A_null signed_d cells are reported descriptively in Results but do not alter the verdict. PARTIAL is preserved as a first-class outcome routed to its own catch-all (`INFORMATION_RADIUS_ASSIGNMENT_PARTIAL`); it is NOT halted on, NOT coerced to NOT_FOUND, and NOT coerced to PRESENT.

The 3 non-halt outcomes form a total partition of the (A_null PRESENT, B sub-verdict ∈ {PRESENT, PARTIAL, NOT_FOUND}) space. Halts cover the OPPOSITE_SIGN, drift, replication, and inheritance-violation cases. Test #16 enforces the partition exhaustively.

The rollup is **conservative**: locked phrases use "follows the assigned", "does not follow the assigned", "does not resolve" — NOT "is causal for", "proves", or "rules out". Mechanism declarations require fresh-stream calibration analogous to v0.30..v0.33; v0.52b is a between-lineage information-radius shuffle and cannot rule out higher-order interactions, trait-covariance effects, or non-V0_25-anchor behavior.

## Cautious framing (per CLAUDE.md)

- "**Follows the assigned**", "**does not follow the assigned**", "**not sufficient to track**" — NOT "**proves**", "**causes**", or "**rules out**".
- "**Between-lineage information-radius assignment**" specifically refers to: each lineage's founder body has `effective_sensor_radius_override` set to a value drawn from the corpus-wide distribution of the run's 5 founder `sensor_radius` traits, via shuffled permutation. Descendants inherit this assignment via the widened `mutate_traits`. Metabolic cost continues to follow the original (unchanged) trait `sensor_radius`. The information channel and the metabolic-cost channel are deliberately decoupled.
- "**Global information economy preserved**" specifically means: the corpus-wide distribution of effective sensing radii is exactly preserved (it is a permutation of the original 5-element draw); only the trait↔lineage link is broken. Contrast with v0.52's C arm (uniform max radius 6) which globally raised the effective sensing distribution.
- "**On the modern A_null corpus**" / "**under the locked V0_25 anchor**" — NOT a chamber-config-independent claim.
- v0.52b explicitly does not establish: cross-layout generalisation, mechanism (the *route* by which assigned information radius produces spatial advantage), trait-covariance effects beyond `sensor_radius` itself, post-tick-50 dominance dynamics, or behavior under non-V0_25 anchors.

## What v0.52b cannot establish (logged here pre-data, not retrofittable)

- ✗ **Mechanism behind the bridge's response to information-radius assignment**. If `INFORMATION_RADIUS_FOLLOWS_ASSIGNMENT` fires, v0.52b establishes that the bridge tracks the assigned effective information radius — but does not isolate the route (e.g., earlier food detection, better hazard avoidance, longer-range gradient following). If `INFORMATION_RADIUS_DOES_NOT_FOLLOW_ASSIGNMENT` fires, v0.52b establishes that information-radius assignment alone is not sufficient — but does not identify the load-bearing factor (e.g., trait-package coherence, founder spawn position interaction with original trait, lineage-internal correlations, etc.).
- ✗ **Generalisation beyond V0_25 / tight_gradient / 5 founders / height-6 grid**. As locked.
- ✗ **Causality for post-tick-50 dominance**. v0.52b measures the v0.48 *bridge* (pre-50 spatial / foraging primaries vs Labels A and B). It does not directly probe v0.46's b50-share dominance label.
- ✗ **Resolution of `INFORMATION_RADIUS_ASSIGNMENT_PARTIAL`** between "label-A-clears" vs "label-B-clears" cases without external structure. The partial outcome is a planned trigger for the v0.52b uniform-4 secondary follow-up, which can disambiguate.
- ✗ **Detection of higher-order interactions** between the information-radius and metabolic-cost channels. v0.52 closed the cost channel; v0.52b varies only the information channel. Joint ablation is a deferred candidate (v0.54).

## Open framing (NOT in v0.52b primary)

- **v0.52b secondary candidate (planned follow-up only if PARTIAL fires) — `C_uniform_effective_radius_4`.** Uniform effective radius = 4 (V0_25 mean draw, rounded up from 3.5). Removes between-agent information-radius variation without globally maxing the sensory economy. Simpler than shuffle, but disturbs the population mean (low-radius agents buffed, high-radius nerfed) and carries a known buff/nerf semantic caveat. Documented here as a planned follow-up; not in v0.52b's primary scope unless the shuffle arm lands in PARTIAL.
- v0.53 candidate: cross-layout generalisation (run v0.48–v0.52b on `widened_gradient` and / or `food_ladder`).
- v0.54 candidate: joint ablation (`sensor_radius_metabolic_cost = 0` AND between-lineage shuffle of `effective_sensor_radius_override`). Tests for higher-order interactions.
- Eventual fresh-stream calibration (v0.30-style) on the v0.46–v0.52b conclusion stack — needed for any "mechanism" declaration. Longer-horizon.

## Re-anchor (locked — Tier-1 only)

| version | published `a_share_h8` |
|---|---|
| v0.42 | 0.652 |
| v0.43R | NOT PUBLISHED (informational-only) |
| v0.44 | 0.878 |
| v0.45 | 0.818 |

A_null arm only gates the rollup. B arm re-derives its own `a_share_h8` for descriptive logging; does NOT gate the verdict.

## Outputs (locked)

```
runs/v0.52b-information-radius-shuffle/per_run_per_lineage_v052b.csv
  columns: arm, version, seed, hazard, run_id, lineage_id,
           founder_original_sensor_radius, founder_assigned_effective_sensor_radius,
           permutation_map_index, applied_identity_rotation_fallback,
           effective_sensor_radius_changed_count,
           founder_reproduction_drive, founder_metabolic_rate,
           pre50_food_events_count, pre50_food_energy_acquired,
           mean_distance_to_nearest_food_cell,
           tick50_living_count, tick50_above_threshold_count, tick50_above_threshold_fraction,
           b50_count, is_eventual_top_b50_label,
           is_high_information_radius_lineage, is_high_tick50_readiness_fraction_lineage

runs/v0.52b-information-radius-shuffle/per_run_descendant_audit.csv
  columns: arm, version, seed, hazard, run_id,
           n_births_seen, descendant_override_inheritance_count,
           descendant_override_missing_count
  (arm in {B} only; A_null contributes informational rows showing 0/0/0)

runs/v0.52b-information-radius-shuffle/audit_summary.csv
  columns: section, key, value
  sections:
    - reanchor_a_share_h8: per (arm, version, h=8) derived + (A_null only) published + drift_abs
    - bridge_reanchor: per (label, observable) v0.48 published signed_d + v0.52b A_null derived + drift_abs
    - paired_d: per (arm, gating-label, observable) cell — paired_d, signed_d, n_runs, fires_expected, fires_wrong
    - descendant_audit: corpus-wide totals across all B-arm runs (n_births_seen,
      descendant_override_inheritance_count, descendant_override_missing_count)
    - sub_verdicts: per arm — sub-verdict + locked sub-phrase
    - rollup_verdict: locked rollup verdict + locked rollup phrase

runs/v0.52b-information-radius-shuffle/audit_log.txt
  human-readable echo with all locked phrases printed verbatim where they fire,
  plus per-arm paired_d tables and the descendant audit aggregate.
```

## Implementation plan (locked)

1. **`src/` changes (one-time, default-preserving)**:
   - `src/hedonism_harness/core/traits.py`: add `effective_sensor_radius_override: int | None = None` field to `Traits`; filter the field out of `TRAIT_NAMES`; update `mutate_traits` to use `dataclasses.replace(parent, **values)` instead of `Traits(**values)`.
   - `src/hedonism_harness/core/sensors.py:123`: per-agent override resolver in `observe()`, falling through to per-model override (v0.52) and then to trait.
   - `src/hedonism_harness/core/sensors.py:196` (ValenceMemory branch only): same resolver pattern.
   - `apply_metabolism` (`src/hedonism_harness/core/body.py:81`): NOT modified.
   - DirectionalMemory branch: NOT modified.
2. Fresh script `scripts/v0_52b_information_radius_shuffle_audit.py`. CLI: `uv run python scripts/v0_52b_information_radius_shuffle_audit.py [--out-dir runs/v0.52b-information-radius-shuffle]`.
3. Per (version, seed, hazard) tuple, run **2 arms**. Every arm constructs `HHModel` via the normal A_null path (`FounderSpec(traits_override=None)`):
   - **A_null**: no patch.
   - **B_effective_radius_shuffle_distribution**: inside `setup_observer`, generate non-identity permutation via `np.random.default_rng(seed).permutation(5)` (rotate-by-one fallback). Read original founder `sensor_radius` values; compute assigned via permutation; patch each founder body's `traits.effective_sensor_radius_override` (single-channel invariant enforced).
4. For each arm-run, attach v0.48-style `setup_observer` + `tick_observer` (copy-local from v0.48 / v0.49 / v0.50 / v0.51 / v0.52). The setup_observer order is: (a) apply founder trait patch (B) or no-op (A_null), (b) capture v0.52b founder audit table from live bodies, (c) wire `AgentBorn` (lineage tracking + descendant audit) / `AteFood` / `HazardDamageApplied` listeners (`sender=model`), (d) capture tick 0 snapshot.
5. The B-arm `AgentBorn` listener increments `descendant_override_inheritance_count` if the newborn body's `traits.effective_sensor_radius_override is not None`, else increments `descendant_override_missing_count`. Both counters are per-run; corpus-wide totals are computed at end-of-audit.
6. Aggregate per-lineage primaries identical to v0.48–v0.52. Compute Label A and Label B per the v0.52b definitions (Label A resolves via override-or-trait, identical resolution under A_null; Label B identical to v0.47–v0.52).
7. Compute paired_d per (arm, gating-label, observable) cell (12 cells total). Classify per-arm sub-verdicts.
8. **Tier-1 bridge re-anchor** (priority 3): A_null arm's six cells vs v0.48 published; halt if drift > 1e-3 OR if A_null sub-verdict ≠ PRESENT.
9. **Corpus re-anchor** (priority 1): A_null arm only; halt if `a_share_h8` for v0.42 / v0.44 / v0.45 drifts > 1e-3.
10. **Opposite-sign halt** (priority 2): scan all gating-label cells across both arms; halt if any signed_d ≤ −0.5.
11. **Descendant inheritance halt** (priority 4): scan B-arm `descendant_override_missing_count`; halt if corpus-wide total > 0.
12. Compute slice rollup verdict per the locked priority + (A_null, B) decision matrix; print + write the locked phrase verbatim.

The reducer is fully self-contained: it reads no `runs/` artifacts. Wall time estimate ~7 minutes for 128 runs.

## Test list (locked, 16 tests; extends v0.46–v0.52 7-point review pattern)

`tests/test_v0_52b_information_radius_shuffle_audit.py`:

1. `test_all_arms_construct_founders_via_normal_a_null_path` — for both arms, founder original `sensor_radius` per founder is byte-identical across arms for the same (version, seed, hazard) tuple.
2. `test_b_shuffle_assigns_permutation_of_founder_sensor_radii` — synthetic original `sensor_radii = [2, 5, 4, 1, 6]` with permutation `[1, 2, 3, 4, 0]` → assigned `[5, 4, 1, 6, 2]`. Multiset equality: sorted(original) == sorted(assigned).
3. `test_b_shuffle_uses_v0_49_helper_rng_with_rotate_fallback` — when the helper RNG draws identity, the rotate-by-one fallback fires and produces `[1, 2, 3, 4, 0]`.
4. `test_b_shuffle_label_a_uses_assigned_effective_override` — synthetic founders with original `[2, 5, 4, 1, 6]` and permutation `[1, 2, 3, 4, 0]` → assigned `[5, 4, 1, 6, 2]`. Label A picks lineage 3 (highest assigned = 6), NOT lineage 4 (highest original = 6).
5. **`test_default_equivalence_preserves_byte_identity`** *(implementation-equivalence test)* — with `effective_sensor_radius_override=None` on both `body.traits` and `body_config`, modified `sensors.observe` and `_read_memory_directional` produce byte-identical outputs to a baseline `int(body.traits.sensor_radius)` resolution. Verifies the resolver's None-default branch is byte-equivalent to pre-modification behavior.
6. `test_per_agent_override_takes_precedence_over_per_model_override` — with `body.traits.effective_sensor_radius_override = 6` AND `body_config.effective_sensor_radius_override = 4`, the resolved radius is 6 (per-agent wins). With per-agent None and per-model 4, the resolved radius is 4 (per-model wins). With both None, falls through to trait. Documents priority order.
7. `test_per_agent_override_reaches_observe_axial_scan` — set `body.traits.effective_sensor_radius_override = 6`; trait `sensor_radius = 2`; place food at distance 5 east. Without the override the axial scan would not detect it (distance 5 > radius 2); with the override it is detected (distance 5 ≤ radius 6).
8. `test_per_agent_override_reaches_valence_memory_directional_scan` — same probe on the ValenceMemory directional path. Pleasure marker at distance 5 east; trait radius 2 → memory east signal 0; per-agent override 6 → memory east signal > 0.
9. **`test_per_agent_override_does_not_affect_apply_metabolism`** *(implementation-equivalence test)* — set `body.traits.effective_sensor_radius_override = 6`; trait `sensor_radius = 2`; assert `apply_metabolism` cost reflects the trait (cost diff between two bodies with trait sensor_radius 2 vs 6 = 0.05 × 4 = 0.2). The metabolic-cost channel must remain trait-tied even under v0.52b.
10. **`test_mutate_traits_preserves_effective_sensor_radius_override`** *(inheritance test)* — construct a parent `Traits` with `sensor_radius=3, effective_sensor_radius_override=6`. Call `mutate_traits(parent, TraitConfig(unbounded_mutation=True), rng)`. Assert the child Traits has `effective_sensor_radius_override == 6` (preserved through `dataclasses.replace`). Repeat 100x with different RNG seeds; in every child the override is preserved at 6 (NOT mutated, NOT reset to None).
11. `test_random_traits_defaults_effective_sensor_radius_override_to_none` — call `random_traits(TraitConfig(unbounded_mutation=True), rng)`. Assert the resulting Traits has `effective_sensor_radius_override is None`. The override is not biologically initialized.
12. **`test_no_rng_setup_offset_across_arms`** *(implementation-equivalence test)* — for the same (version, seed, hazard), founder original `sensor_radius` AND every other founder trait (full Traits records) byte-identical across A_null and B at setup_observer end. Proves the body-trait patch + helper RNG do not consume `streams.mutation`.
13. `test_per_arm_subverdict_a_null_present_requires_both_labels_clear` — synthetic A_null paired_d (Label A 2/3, Label B 2/3) → A_NULL_BRIDGE_PRESENT. Synthetic (Label A 1/3, Label B 2/3) → A_NULL_BRIDGE_PARTIAL.
14. `test_rollup_information_radius_follows_assignment_when_present_present` — synthetic (A_null PRESENT, B PRESENT); assert rollup = `INFORMATION_RADIUS_FOLLOWS_ASSIGNMENT` and locked phrase contains "follows the assigned effective information radius" verbatim.
15. `test_rollup_does_not_follow_and_partial_outcomes` — (A_null PRESENT, B NOT_FOUND) → `INFORMATION_RADIUS_DOES_NOT_FOLLOW_ASSIGNMENT`. (A_null PRESENT, B PARTIAL) → `INFORMATION_RADIUS_ASSIGNMENT_PARTIAL`. Both locked phrases verified.
16. **`test_shuffle_descendant_inheritance_halt_priority_and_partition_total`** — synthesize a scenario where the corpus-wide `descendant_override_missing_count > 0` (any descendant under shuffle had the override revert to None); assert `SHUFFLE_DESCENDANT_INHERITANCE_HALT` fires (priority 4) before any outcome verdict. Synthesize a `BRIDGE_REPLICATION_HALT` (priority 3) alongside an inheritance violation; assert priority 3 fires first. Synthesize a `CORPUS_REDERIVE_DRIFT_HALT` (priority 1); assert it fires over all other halts. Exhaustively iterate the (B sub-verdict ∈ {PRESENT, PARTIAL, NOT_FOUND}) space under A_null PRESENT and zero halts; assert each maps to exactly one of {FOLLOWS_ASSIGNMENT, DOES_NOT_FOLLOW_ASSIGNMENT, ASSIGNMENT_PARTIAL}.

## Watch-outs (for future-Chronus)

- **Two `src/` changes in v0.52b cumulative on top of v0.52's**: this is the second slice in the v0.46+ stack to touch `src/`. The change is minimum-viable (one new optional Traits field + filter on TRAIT_NAMES + `dataclasses.replace` widening + resolver-pattern update at two sensors.py call sites) and default-preserving (`override=None` reproduces the original code path byte-identically). All 1680 existing tests must continue to pass without modification — the modified `src/` is forward-compatible.
- **The override is on `Traits` but is NOT a biologically-mutable trait.** It is filtered out of `TRAIT_NAMES` so `random_traits` / `mutate_traits` / `validate_traits` / archetype-builder / metrics collectors never iterate over it. It exists on `Traits` for the data layout (so per-agent state lives on the agent without a separate dataclass) but its semantic role is "experimental lineage assignment".
- **Inheritance is mechanical via `mutate_traits`**, not via an `AgentBorn` listener. The widened `mutate_traits` uses `dataclasses.replace(parent, **values)`, which preserves any field of `parent` not in `values` — including `effective_sensor_radius_override`. Test #10 enforces this with 100x seeds.
- **Inheritance halt-loud invariant (priority 4)**: every newborn under arm B must have `body.traits.effective_sensor_radius_override is not None` at AgentBorn-emit time. The `AgentBorn` listener increments `descendant_override_missing_count` if it is None; corpus-wide total > 0 fires `SHUFFLE_DESCENDANT_INHERITANCE_HALT`. This guards against future refactors of `_spawn_child` that bypass `mutate_traits`.
- **Per-agent override takes precedence over per-model override** (test #6 enforces). v0.52's `BodyConfig.effective_sensor_radius_override` (model-wide uniform) and v0.52b's `Traits.effective_sensor_radius_override` (per-agent) coexist; the per-agent value wins when both are set. The resolver order is documented in the docstring of `observe`.
- **Single-channel invariant must halt loud** on any non-`effective_sensor_radius_override` field difference between original and assigned trait vectors. In v0.52b the patched field is the override, NOT `sensor_radius` (which is unchanged). Different from v0.49 / v0.51 where the patched field was `sensor_radius` itself.
- **`apply_metabolism` is unaffected** by the per-agent override (test #9 enforces). The metabolic-cost channel continues to follow trait `sensor_radius`. v0.52b's interpretive frame depends on this.
- **DirectionalMemory branch is unaffected** by the per-agent override (the v0.52 src/ touch left it that way; v0.52b inherits). The modern A_null corpus uses `cell_exact` / `ValenceMemory`; DirectionalMemory is not consulted.
- **Helper RNG is fully isolated** (same idiom as v0.49 / v0.50 C-arm). The script-local `np.random.default_rng(seed).permutation(5)` does not touch `model.streams.mutation` or any per-agent `agent_rng`. Test #12 enforces founder-trait byte-identity across arms.
- **Hazard-paired runs share permutation maps** (same as v0.49 / v0.50 C-arm). Because the helper RNG is seeded from `seed` alone (not `(seed, hazard)`), the two B-arm runs for the same (version, seed) at h=0 and h=8 receive identical permutations.
- **Effective-changed-count is not always 5** (same as v0.49 / v0.50 C-arm). With duplicate sensor_radii in the original draw (common at V0_25), a non-identity permutation may produce few effective changes. Logged per run; does not exclude low-count runs from the paired_d pool.
- **Label A under shuffle picks by ASSIGNED effective override**, not by original trait. Mirrors v0.49 C-arm logic. The interpretive question is "does the bridge follow the assigned information radius" — which requires Label A to track the assigned value.
- **Locked phrase discipline:** all sub-verdict and rollup locked phrases fire verbatim where the verdict fires. No paraphrase.
- **Determinism north star** ([[scripts/core_smoke_test.py]]) must continue to pass under the modified `src/`. Default behavior is byte-identical by construction; verify explicitly during implementation.

## Files this slice will create / modify

- `docs/experiments/fear_hunger_v0.52b.md` (this file; Results section appended after reducer run)
- `scripts/v0_52b_information_radius_shuffle_audit.py` (new)
- `tests/test_v0_52b_information_radius_shuffle_audit.py` (new, 16 tests)
- `src/hedonism_harness/core/traits.py` (one new optional `Traits` field; `TRAIT_NAMES` filter; `mutate_traits` `dataclasses.replace` widening)
- `src/hedonism_harness/core/sensors.py` (resolver pattern updated at two read sites: per-agent first, then per-model, then trait fallback)

No other files modified.

## Results

**Status:** reducer executed 2026-05-08 against the 128-run corpus (2 arms × 64 (version, seed, hazard) tuples). Wall time ~7 minutes. **Tier-1 bridge re-anchor PASSES** (A_null arm reproduces v0.48's six published signed_d cells within max drift 0.0004 ≪ 1e-3 tolerance). Corpus re-anchor (`a_share_h8`) max drift 0.0003. **Descendant inheritance audit PASSES** (1667 / 1667 B-arm newborns inherited the override; 0 missing). No opposite-sign firings under any gating label.

### Rollup verdict — `INFORMATION_RADIUS_FOLLOWS_ASSIGNMENT` fires

> **Locked phrase fires verbatim:** "On the modern A_null corpus with global information economy preserved (between-lineage shuffle of effective `sensor_radius` over a corpus-wide preserved distribution), the v0.48 spatial / foraging bridge follows the assigned effective information radius. The information-radius assignment is sufficient to track the bridge under the locked V0_25 anchor."

Sub-verdicts:

| arm | sub-verdict |
|---|---|
| A_null | `A_NULL_BRIDGE_PRESENT` |
| B_effective_radius_shuffle_distribution | `B_SHUFFLE_BRIDGE_PRESENT` |

The (PRESENT, PRESENT) triple is the FOLLOWS_ASSIGNMENT pattern — both labels under B fire 3/3 with effect sizes comparable to A_null, despite the trait↔lineage link being broken by the per-founder shuffle. Label A under B picks by the *assigned* effective override (not the original trait `sensor_radius`); the bridge primaries fire cleanly against this re-pointed label.

### Tier-1 bridge re-anchor — A_null reproduces v0.48 within 1e-3

| label | observable | published | derived | drift |
|---|---|:-:|:-:|:-:|
| label_a_information_radius | pre50_food_events_count | +1.066 | +1.066 | 0.0004 |
| label_a_information_radius | pre50_food_energy_acquired | +1.066 | +1.066 | 0.0004 |
| label_a_information_radius | mean_distance_to_nearest_food_cell | +1.916 | +1.916 | 0.0001 |
| label_b_readiness_fraction | pre50_food_events_count | +0.916 | +0.916 | 0.0001 |
| label_b_readiness_fraction | pre50_food_energy_acquired | +0.916 | +0.916 | 0.0001 |
| label_b_readiness_fraction | mean_distance_to_nearest_food_cell | +1.179 | +1.179 | 0.0004 |

Max drift 0.0004 ≪ 1e-3. v0.52b's A_null arm is byte-compatible with v0.48 / v0.49 / v0.50 / v0.51 / v0.52 A_null path. The src/ extension (one new optional `Traits` field + `TRAIT_NAMES` filter + `mutate_traits` `dataclasses.replace` widening + sensors.py resolver update) is default-preserving — corpus-level enforcement is the 1680 prior tests passing without modification.

### Per-arm signed_d (sign-aware)

#### Arm A_null — sub-verdict `A_NULL_BRIDGE_PRESENT`

| label | observable | sign | signed_d | fires |
|---|---|:-:|:-:|:-:|
| label_a_information_radius | pre50_food_events_count | + | **+1.066** | YES |
| label_a_information_radius | pre50_food_energy_acquired | + | **+1.066** | YES |
| label_a_information_radius | mean_distance_to_nearest_food_cell | − | **+1.916** | YES |
| label_b_readiness_fraction | pre50_food_events_count | + | **+0.916** | YES |
| label_b_readiness_fraction | pre50_food_energy_acquired | + | **+0.916** | YES |
| label_b_readiness_fraction | mean_distance_to_nearest_food_cell | − | **+1.179** | YES |

#### Arm B_effective_radius_shuffle_distribution — sub-verdict `B_SHUFFLE_BRIDGE_PRESENT`

| label | observable | sign | signed_d | fires |
|---|---|:-:|:-:|:-:|
| label_a_information_radius (assigned) | pre50_food_events_count | + | **+1.057** | YES |
| label_a_information_radius (assigned) | pre50_food_energy_acquired | + | **+1.057** | YES |
| label_a_information_radius (assigned) | mean_distance_to_nearest_food_cell | − | **+1.689** | YES |
| label_b_readiness_fraction | pre50_food_events_count | + | **+0.983** | YES |
| label_b_readiness_fraction | pre50_food_energy_acquired | + | **+0.983** | YES |
| label_b_readiness_fraction | mean_distance_to_nearest_food_cell | − | **+1.391** | YES |

3/3 primaries fire under both labels with 0 wrong-sign. Effect sizes are comparable to A_null on Label A observables 1/2 (+1.057 vs +1.066) and slightly weaker on observable 3 (+1.689 vs +1.916). Label B observables 1/2 show a small uplift under B (+0.983 vs +0.916); observable 3 also uplifted (+1.391 vs +1.179). The shuffle preserves the bridge's directional structure with magnitude shifts within ±0.3 of A_null on all six cells.

### Descendant audit — perfect lineage coherence

| arm | n_births_seen | n_overrides_inherited | n_overrides_missing |
|---|:-:|:-:|:-:|
| A_null | n/a (audit only meaningful under B) | n/a | n/a |
| B_effective_radius_shuffle_distribution | **1667** | **1667** | **0** |

Every newborn under arm B across the 64-run corpus inherited a non-None `effective_sensor_radius_override` from its parent, via the widened `mutate_traits` (`dataclasses.replace(parent, **values)` preserves the field through reproduction). The locked priority-4 `SHUFFLE_DESCENDANT_INHERITANCE_HALT` invariant did not fire. **Lineage-coherent inheritance via `mutate_traits` works as designed.**

### Corpus re-anchor

A_null arm — all PASS (max drift 0.0003):

| version | derived `a_share_h8` | published | drift |
|---|:-:|:-:|:-:|
| v0.42 | 0.652 | 0.652 | 0.0003 |
| v0.43R | 0.674 | — (informational) | — |
| v0.44 | 0.878 | 0.878 | 0.0001 |
| v0.45 | 0.818 | 0.818 | 0.0002 |

B arm (informational only — different counterfactual):

| version | B `a_share_h8` |
|---|:-:|
| v0.42 | 0.691 |
| v0.43R | 0.619 |
| v0.44 | 0.765 |
| v0.45 | 0.822 |

B's `a_share_h8` shifts modestly relative to A_null in both directions (v0.42 +0.039, v0.43R −0.055, v0.44 −0.113, v0.45 +0.004) — consistent with a different counterfactual world rather than a systematic change in dominance dynamics.

### What v0.52b can safely claim

- ✓ **A_null replicated.** Tier-1 re-anchor reproduces v0.48's six published signed_d cells within 0.0004. The corpus re-anchor reproduces v0.42 / v0.44 / v0.45 within 0.0003. The src/ extension is byte-equivalent to default v0.48–v0.52 behavior under both per-agent and per-model overrides at None.
- ✓ **B_effective_radius_shuffle_distribution remained PRESENT** (3/3 under both labels, 0 wrong-sign). Effect sizes within ±0.3 of A_null across all six cells.
- ✓ **Therefore, between-lineage information-radius assignment over a preserved global distribution is sufficient to track the v0.48 spatial / foraging bridge on this corpus.** The bridge follows the *assigned* effective information radius, not the original trait `sensor_radius` (Label A under B picks by assigned override, and the primaries still fire 3/3).
- ✓ **Lineage-coherent inheritance via `mutate_traits` (Option α) works as designed.** Every newborn (1667/1667) inherited the override; halt-loud invariant did not fire. The `dataclasses.replace(parent, **values)` widening cleanly propagates the experimental override through reproduction without modifying the biological mutation pipeline.
- ✓ **Combined with v0.52's findings**: v0.52 B (zero cost) showed the metabolic-cost channel is not necessary for the bridge; v0.52b B (shuffle) shows the bridge follows the assigned information-radius distribution under preserved global ecology. The information-radius channel does positive work in tracking the bridge — but see "What v0.52b cannot claim" for the discipline limits.

### What v0.52b cannot claim

- ✗ **"The information-radius channel IS load-bearing for the bridge."** v0.52b's evidence is that information-radius *assignment* tracks the bridge under preserved global ecology. That is not the same as proving the channel is causally load-bearing — there could be other channels that co-track the assignment under shuffle (e.g., correlations between assigned override and original trait values that survive permutation). v0.52b's verdict is "follows the assigned" (correlational, locked phrase), not "is causally load-bearing".
- ✗ **"Information-radius assignment is necessary for the bridge."** v0.52b only tested whether shuffle preserves the bridge; it did not test removing assignment entirely (which would be logically equivalent to A_null minus information-radius variation, and not separately probed).
- ✗ **Mechanism behind the bridge's response to assignment**. The route from "lineage gets reassigned a high effective radius" → "lineage achieves higher pre-50 spatial / foraging primaries" is not isolated. Plausible: wider effective sensing → earlier food detection → more pre-50 food events / energy / shorter distance. v0.52b is consistent with this but does not establish it.
- ✗ **Generalisation beyond V0_25 / tight_gradient / 5 founders / height-6 grid**. As locked.
- ✗ **Causality for post-tick-50 dominance**. v0.52b measures the v0.48 bridge cells; v0.46's b50-share dominance question remains separate.

### Cross-corpus context

| slice | corpus | claim | strength |
|---|---|---|---|
| v0.46 | modern A_null | tick-50 readiness predicts dominance | observational (PRESENT) |
| v0.47 | modern A_null | founder `sensor_radius` predicts tick-50 readiness | observational (PARTIAL) |
| v0.48 | modern A_null | `sensor_radius` ↔ spatial bridge | observational (PRESENT under both labels) |
| v0.49 | modern A_null | founder `sensor_radius` causal contribution | interventional (SUPPORTED) |
| v0.50 | modern A_null | v0.49's contribution survives position controls | interventional (ROBUST) |
| v0.51 | modern A_null | founder-clamp NOT_FOUND result preserved under lineage-wide clamp | interventional (REPRODUCED; descendant-drift channel empirically zero under V0_25) |
| v0.52 | modern A_null | metabolic-cost channel not necessary for bridge (B PRESENT); C arm halt-loud | interventional (B PRESENT confirms cost dispensable; C uniform-max regime-shift halt) |
| v0.52b | modern A_null | bridge follows between-lineage information-radius assignment under preserved global ecology | interventional (FOLLOWS_ASSIGNMENT; lineage-coherent inheritance verified clean) |

The v0.46→v0.52b stack now reads: tick-50 readiness predicts dominance → founder `sensor_radius` predicts readiness → `sensor_radius` co-occurs with spatial advantage → causal contribution from `sensor_radius` survives clamp + permutation → that contribution survives shifted-top + permuted founder positions → and the founder-clamp NOT_FOUND result is preserved under lineage-wide clamping → and the metabolic-cost channel of `sensor_radius` is not necessary for the bridge → and the bridge follows the assigned effective information radius when global information economy is preserved (information-radius assignment is sufficient to track the bridge).

### Next-step candidates (open; not locked)

The v0.52b primary arm fired PRESENT cleanly; the planned uniform-4 secondary follow-up (which would have triggered on PARTIAL) is therefore NOT activated and remains a deferred candidate only if a future question demands disambiguating "any information uniformity" vs "max-radius specifically".

- **v0.52b uniform-4 secondary (deferred).** Documented in pre-reg; not run. Available if a follow-up question demands probing whether the uniform-4 case behaves like the shuffle (PRESENT, supports preserved-distribution reading) or like v0.52's uniform-6 (regime-shift halt, suggests max-radius specifically caused the wrong-sign). Optional.
- **v0.53 — cross-layout generalisation.** Run v0.48–v0.52b on `widened_gradient` and / or `food_ladder`. Layout differences may reveal whether the FOLLOWS_ASSIGNMENT result is geometry-specific.
- **v0.54 — joint ablation.** `sensor_radius_metabolic_cost = 0` AND between-lineage shuffle of `effective_sensor_radius_override`. Tests for higher-order interactions between the two channels v0.52 + v0.52b separately addressed.
- **Eventual fresh-stream calibration** (v0.30-style) on the v0.46–v0.52b conclusion stack — needed for any "mechanism" declaration. Longer-horizon.

### CI gate at v0.52b close

```
uv run ruff check .             ok
uv run ruff format --check .    ok
uv run pytest                   1696 passed, 7 skipped (was 1680; +16 v0.52b)
uv run python scripts/core_smoke_test.py                              ok (default behavior preserved)
uv run python scripts/v0_52b_information_radius_shuffle_audit.py      INFORMATION_RADIUS_FOLLOWS_ASSIGNMENT
```
