# fear_hunger v0.52 — sensor_radius information vs metabolic-cost decoupling

**Slice:** v0.52
**Type:** **first-class intervention** (NOT a post-hoc reducer); paired channel-decoupling probe (zero-cost arm + uniform-effective-radius arm).
**Predecessors:** v0.21..v0.27 (substrate / aggregate-optimum), v0.34..v0.36 (lineage observability + heritability), v0.42..v0.45 (substrate-causal arc), v0.46 (`READINESS_PREDICTS_DOMINANCE`), v0.47 (`READINESS_TRAITS_PARTIALLY_PREDICTIVE`), v0.48 (`SENSOR_RADIUS_SPATIAL_BRIDGE_PRESENT`), v0.49 (`SENSOR_RADIUS_CAUSAL_CONTRIBUTION_SUPPORTED`), v0.50 (`SENSOR_RADIUS_ROBUST_TO_POSITION`), v0.51 (`FOUNDER_CLAMP_REPRODUCED`).
**Question being asked (locked):** Does the v0.48 / v0.49 sensor_radius bridge depend on **information radius**, **metabolic cost**, or their **coupling**?

The v0.49 founder-clamp + permutation evidence implicates founder `sensor_radius` as causally contributing to the v0.48 spatial / foraging bridge, and v0.50 / v0.51 confirm that contribution survives founder-position controls and lineage-wide clamping. But "higher `sensor_radius`" means two things simultaneously in the V0_25 simulator:

1. **Information radius** — wider sensing footprint at every step, via `sensors.observe` and `_read_memory_directional` (ValenceMemory directional scan).
2. **Metabolic cost** — proportionally higher per-tick energy drain, via `apply_metabolism`'s `body_config.sensor_radius_metabolic_cost * body.traits.sensor_radius` term.

v0.49's founder clamp held both channels constant simultaneously and observed bridge weakening; the locked v0.49 phrase explicitly flagged this as a confound (see v0.49 pre-reg §"What v0.49 cannot establish" → "Metabolic equivalence between A_null and B_clamp_4"). v0.52 is the first slice that decouples the two channels and asks which one carries the bridge.

The probe is **paired**: B holds the metabolic-cost channel constant (zero) while leaving information-radius variation intact; C holds the information-radius channel constant (uniform max) while leaving metabolic-cost variation intact. The 2 × 2 categorical decision matrix (B {PRESENT, NOT_FOUND} × C {PRESENT, NOT_FOUND}) cleanly partitions the channel-attribution outcome space.

## Pre-implementation correction (2026-05-08, before any reducer code)

The implementation path was investigated post-design-review per CLAUDE.md "pre-reg stands as the historical record". Recorded here for transparency. No data has been seen yet.

### B is script-local; no `src/` change required

`HHModel.__init__` accepts `body_config: BodyConfig | None = None` (model.py:162) and stores it as `self.body_config` (model.py:175). `apply_metabolism_step` (mesa_agents.py:231) reads `self.model.body_config` at every tick — a live attribute access, not a snapshot at agent construction time. `BodyConfig` is `pydantic.BaseModel` with `model_config = ConfigDict(frozen=True, extra="forbid")` (config.py:138), so we cannot mutate the field in place — but we can REPLACE the entire `model.body_config` attribute with a frozen-clone via `model_copy(update=...)`. Inside the v0.52 reducer's `setup_observer`:

```python
model.body_config = model.body_config.model_copy(
    update={"sensor_radius_metabolic_cost": 0.0}
)
```

All subsequent `apply_metabolism` calls pick up the new config from `self.model.body_config`. **No `src/` change** is needed for the B arm.

### C requires a minimal, default-preserving `src/` change

The information-radius channel is consumed at two read sites in `core/sensors.py`:

- **`sensors.observe(...)` line 123** — `radius = int(body.traits.sensor_radius)` for the external axial scan over `world.food_value` and `world.hazard_damage`.
- **`sensors._read_memory_directional(...)` line 196** — `directional_signals(memory, body.x, body.y, int(body.traits.sensor_radius))` for the ValenceMemory directional scan over the per-cell pleasure/pain EMA layers. (The `DirectionalMemory` branch of the same function does NOT consume `sensor_radius`; it reads pre-aggregated 4-vector tendencies directly.)

`BodyConfig` has `extra="forbid"`, so a new field cannot be monkey-patched onto an instance — it must be added in `src/`. Three minimal touches, all default-preserving:

1. **`src/hedonism_harness/core/config.py`** — add to `BodyConfig`:
   ```python
   effective_sensor_radius_override: int | None = Field(default=None, ge=0)
   ```
2. **`src/hedonism_harness/core/sensors.py:123`** — replace the hardcoded read with a resolver:
   ```python
   override = body_config.effective_sensor_radius_override
   radius = override if override is not None else int(body.traits.sensor_radius)
   ```
3. **`src/hedonism_harness/core/sensors.py:196`** — same resolver pattern in `_read_memory_directional`'s `ValenceMemory` branch:
   ```python
   override = body_config.effective_sensor_radius_override
   radius = override if override is not None else int(body.traits.sensor_radius)
   return directional_signals(memory, body.x, body.y, radius)
   ```
   (The `DirectionalMemory` branch is intentionally NOT modified — `DirectionalMemory` does not consume `sensor_radius`, and the v0.52 corpus uses `cell_exact` / `ValenceMemory` per V0_25 anchor.)

The override is `None` by default, so every existing caller (every prior version's A_null arm + every reducer test + every `core_smoke_test.py` run) goes through the original `int(body.traits.sensor_radius)` path. Determinism preserved by construction.

For the C arm, the v0.52 reducer constructs the override at body-config build time:

```python
body_config = BodyConfig(effective_sensor_radius_override=6)
model.body_config = body_config  # or replace post-construction inside setup_observer
```

`apply_metabolism` is NOT modified — it continues to read `body_config.sensor_radius_metabolic_cost * body.traits.sensor_radius`, so under arm C every agent's metabolic cost remains tied to its actual trait `sensor_radius`. Only the information-radius channel is flattened.

### Determinism story (locked)

- **A_null arm**: byte-identical to v0.48 / v0.49 / v0.50 / v0.51 A_null path. `body_config = BodyConfig()` with default `effective_sensor_radius_override=None`. Tier-1 re-anchor enforces this within 1e-3.
- **B arm**: `model.body_config` replaced with `body_config.model_copy(update={"sensor_radius_metabolic_cost": 0.0})` inside `setup_observer`. No trait mutation; no override. RNG streams (`streams.mutation`, per-agent RNGs) byte-identical to A_null at the moment of the first `model.step()`. Pre-50 trajectories diverge from A_null because metabolism cost differs, NOT because of RNG offset.
- **C arm**: `model.body_config` replaced with `body_config.model_copy(update={"effective_sensor_radius_override": 6})` inside `setup_observer`. No trait mutation; no metabolic-cost change. RNG streams byte-identical to A_null at the moment of the first `model.step()`. Pre-50 trajectories diverge from A_null because sensing output differs (every agent observes with radius 6 regardless of trait), NOT because of RNG offset.
- **Default-equivalence test** (locked, see Test list #6): with `effective_sensor_radius_override=None` and `sensor_radius_metabolic_cost=0.05`, the modified `src/` pipeline reproduces the existing A_null outputs byte-identically. This is enforced both by the existing 1664-test pytest suite continuing to pass without modification AND by an explicit v0.52 test that runs `core_smoke_test.py`'s state-hash check on a representative seed under the modified `sensors.py` path.

This correction does not change the verdict structure, arm count, corpus, observable definitions, label gating, re-anchor strategy (Tier-1 only — see "Re-anchor"), or the rollup outcome set.

## Conservation framing — interventional, with one minimal `src/` change

- **One `src/` modification**: a single optional field on `BodyConfig` (`effective_sensor_radius_override: int | None = None`) plus the two-line resolver pattern at `sensors.observe` (line 123) and `_read_memory_directional`'s `ValenceMemory` branch (line 196). **Default `None` preserves byte-identity** for every existing test, every prior reducer's A_null arm, and `core_smoke_test.py`. v0.52 is the first slice in the v0.46+ stack that touches `src/`; the touch is minimum-viable, default-preserving, and forward-compatible.
- **No modifications to prior reducer or audit scripts.** v0.34's `lineage_replay.py`, v0.35's `lineage_survival_replay.py`, v0.36's `trait_replay.py`, the four substrate audits (v0.42 / v0.43R / v0.44 / v0.45), and v0.46 / v0.47 / v0.48 / v0.49 / v0.50 / v0.51's reducers remain byte-identical to their merged forms.
- **A_null arm is byte-identical to v0.48 / v0.49 / v0.50 / v0.51's A_null path** (default override=None; default cost=0.05). Tier-1 re-anchor enforces this at metric level.
- **No `traits_override`.** All arms use `FounderSpec(traits_override=None)`; v0.52 manipulates `body_config`, not founder body traits.
- **No agent body trait mutation.** Unlike v0.49 / v0.50 / v0.51, v0.52 does NOT modify any `agent.body.traits` field. The intervention happens at the `body_config` level, which `apply_metabolism` and `sensors.observe` consult on every read.
- **No mutation pipeline modification.** v0.52 does NOT override `mutate_traits`. Descendants under all three arms inherit and mutate `sensor_radius` normally; the override is global to the model and applies uniformly to every agent.
- **No descendant-time intervention.** Unlike v0.51, v0.52 does NOT register an `AgentBorn` listener. The `body_config` swap is one-shot at `setup_observer` time and applies model-wide.
- **No Mesa cell occupancy modification** (unlike v0.50). v0.52 does NOT modify `agent.body.x`, `agent.body.y`, or `agent.cell`.

## Corpus (locked, 64 × 3 arms = 192 runs)

| version | seeds | hazards | runs per arm | total runs |
|---|---|---|---|---|
| v0.42 | 41..48 | {0, 8} | 16 | 48 |
| v0.43R | 49..56 | {0, 8} | 16 | 48 |
| v0.44 | 57..64 | {0, 8} | 16 | 48 |
| v0.45 | 65..72 | {0, 8} | 16 | 48 |
| **total** | | | | **192** |

V0_25 anchor unchanged from v0.46–v0.51. Each (version, seed, hazard) tuple is run **3 times** — once per arm. Wall time estimate ~10 minutes for 192 runs (matches v0.49 / v0.50 / v0.51).

## Arms (locked, 3)

### A_null

```
no patch, no body_config override
```

`HHModel` constructed with default `body_config=None` → `BodyConfig()` with default `sensor_radius_metabolic_cost=0.05`, default `effective_sensor_radius_override=None`. Founder traits, agent RNGs, and `streams.mutation` byte-identical to v0.48 / v0.49 / v0.50 / v0.51 A_null. Used as the bridge replication baseline (Tier-1 re-anchor target).

### B_zero_sensor_cost

For each (version, seed, hazard) tuple, the reducer constructs `HHModel` normally and replaces `model.body_config` inside `setup_observer`, before tick-0 capture:

```python
model.body_config = model.body_config.model_copy(
    update={"sensor_radius_metabolic_cost": 0.0}
)
```

After the swap:

- `apply_metabolism` reads the new config at every tick: `0.0 * body.traits.sensor_radius == 0.0` for the radius-dependent term. The base metabolic cost (`base_metabolic_cost = 0.25`) and other terms are unchanged.
- `sensors.observe` and `_read_memory_directional` see `effective_sensor_radius_override=None` → use `body.traits.sensor_radius` exactly as A_null. **Information-radius variation is preserved.**
- No agent body trait is mutated. No founder is touched.

**Channel decoupling under B**: the metabolic-cost channel of `sensor_radius` variation is removed (every founder pays the same `base_metabolic_cost` regardless of `sensor_radius`); the information-radius channel is retained (each agent senses out to its own draw of `sensor_radius`). If the bridge fires under B, the information-radius channel is sufficient to produce the bridge on its own.

### C_uniform_effective_radius_6

For each (version, seed, hazard) tuple, identical setup pattern (replace `model.body_config` in `setup_observer`):

```python
model.body_config = model.body_config.model_copy(
    update={"effective_sensor_radius_override": 6}
)
```

After the swap:

- `sensors.observe` (line 123, post-modification) reads `radius = body_config.effective_sensor_radius_override = 6` for every agent. **Every agent senses with radius 6 regardless of its trait `sensor_radius`.**
- `_read_memory_directional` (line 196, post-modification, ValenceMemory branch) reads the same override → 6. Memory directional scan also uses radius 6 for every agent.
- `apply_metabolism` is NOT modified — it continues to read `body_config.sensor_radius_metabolic_cost (0.05) * body.traits.sensor_radius (per-founder draw)`. **Metabolic-cost variation is preserved**: founders with high `sensor_radius` still pay more per tick.
- No agent body trait is mutated.

**Choice of override value (locked, pre-data).** V0_25's `TraitConfig(unbounded_mutation=True)` draws `sensor_radius` uniformly from {1, 2, 3, 4, 5, 6}. The override is set to **6** — the **maximum** of the V0_25 draw range — so that no agent loses sensing ability relative to its V0_25 capability ceiling. Lower-radius agents receive an information uplift (their effective sensing widens to 6 even though their trait says e.g. 2); higher-radius agents experience no information change (they already had the maximum). This is **NOT** a neutral subtraction of information from high-radius agents; it is an **equalizing uplift** that flattens between-agent variation in effective sensing radius without nerfing anyone. See "Cautious framing" and "What v0.52 cannot establish" for the explicit semantic caveat. The alternative override of `mean(V0_25 sensor_radius) ≈ 3.5` rounded to 4 would create an avoidable ambiguity (low-radius agents helped, high-radius agents nerfed); the max-radius choice is cleaner because it is monotone-non-decreasing in information for every agent.

**Channel decoupling under C**: the information-radius channel of `sensor_radius` variation is flattened (every agent senses with radius 6 regardless of trait); the metabolic-cost channel is retained (each agent's per-tick cost still scales with its own trait `sensor_radius`). If the bridge fires under C, the metabolic-cost channel is sufficient to produce the bridge on its own.

## Labels (locked, two)

Both labels gate the verdict for **all three arms**. Unlike v0.49 / v0.51 (where the founder clamp made all founders share `sensor_radius=4` → Label A degenerated), v0.52 preserves founder `sensor_radius` variation in every arm. Label A is therefore well-defined and gates under A_null, B, and C alike.

Label A definition is unchanged from v0.48 / v0.49 / v0.50 / v0.51:

```
high_sensor_radius_lineage = argmax_lineage(founder_sensor_radius)
                             tiebreak: min(lineage_id)
```

`founder_sensor_radius` is the unmutated initial draw captured at `setup_observer` time. Identical across all three arms (same `traits_override=None` path, same `streams.mutation` byte-identity).

Label B is unchanged (tick-50 readiness fraction with the 3-tier tiebreak; copy-local from v0.48).

| arm | Label A gating | Label B gating |
|---|:-:|:-:|
| A_null | gates | gates |
| B_zero_sensor_cost | gates | gates |
| C_uniform_effective_radius_6 | gates | gates |

The interpretive framing under C is worth flagging explicitly: under C, Label A still picks the lineage whose founder drew the highest `sensor_radius`, but that founder's *effective sensing* under C is the same as everyone else's (radius 6). The question Label A asks under C is therefore: **does the original founder `sensor_radius` advantage still predict the bridge when its information-radius component is flattened?** That's exactly the channel-decomposition question the slice is designed to answer.

## Primary observables (locked, 3, identical to v0.48 / v0.49 / v0.50 / v0.51)

| # | name | expected sign |
|---|---|:-:|
| 1 | `pre50_food_events_count` | + |
| 2 | `pre50_food_energy_acquired` | + |
| 3 | `mean_distance_to_nearest_food_cell` | − |

Definitions, aggregation rules, NaN handling: copy-local from v0.48 / v0.49 / v0.50 / v0.51. Per-tick observer firing semantics unchanged (tick 0 captured at `setup_observer` time AFTER the body_config swap; ticks 1..50 captured by `tick_observer`).

## Effect-size rule (locked, sign-aware, identical to v0.48–v0.51)

```
per_run_delta_O = label_lineage_value_O − mean(non_label_lineage_values_O)
paired_d_O      = mean(per_run_delta_O) / stdev(per_run_delta_O, ddof=1)
signed_d_O      = paired_d_O × expected_sign
fires_expected  iff signed_d_O ≥ +0.5
fires_wrong     iff signed_d_O ≤ −0.5
```

## Per-arm sub-verdicts (locked, 4-way each)

Each arm gates on Label A AND Label B (no diagnostic-only label degeneracy):

| condition | A_null sub-verdict | B sub-verdict | C sub-verdict |
|---|---|---|---|
| both labels clear ≥ 2/3, 0 wrong-sign | `A_NULL_BRIDGE_PRESENT` | `B_ZERO_COST_BRIDGE_PRESENT` | `C_UNIFORM_RADIUS_BRIDGE_PRESENT` |
| exactly one label clears ≥ 2/3, 0 wrong-sign | `A_NULL_BRIDGE_PARTIAL` | `B_ZERO_COST_BRIDGE_PARTIAL` | `C_UNIFORM_RADIUS_BRIDGE_PARTIAL` |
| neither label clears ≥ 2/3, 0 wrong-sign | `A_NULL_BRIDGE_NOT_FOUND` | `B_ZERO_COST_BRIDGE_NOT_FOUND` | `C_UNIFORM_RADIUS_BRIDGE_NOT_FOUND` |
| any primary signed_d ≤ −0.5 under either label | `A_NULL_BRIDGE_OPPOSITE_SIGN_HALT` | `B_ZERO_COST_OPPOSITE_SIGN_HALT` | `C_UNIFORM_RADIUS_OPPOSITE_SIGN_HALT` |

Each arm's paired_d cells (3 observables × 2 labels = 6 cells per arm; 18 cells total across all arms) are computed independently from the arm's 64-run pool.

## Slice rollup verdicts (locked, 8 outcomes, priority-ordered)

Priority order (first-matching wins):

1. `CORPUS_REDERIVE_DRIFT_HALT`
2. `INTERVENTION_OPPOSITE_SIGN_HALT`
3. `BRIDGE_REPLICATION_HALT` (A_null vs v0.48 — Tier-1, only re-anchor)
4. `INFORMATION_RADIUS_LOAD_BEARING`
5. `METABOLIC_COST_LOAD_BEARING`
6. `BOTH_CHANNELS_INDEPENDENTLY_SUFFICIENT`
7. `CHANNELS_COUPLED_OR_SHARED_CONFOUND`
8. `CHANNELS_MIXED`

### Halt conditions

| priority | rollup verdict | trigger | locked phrase (verbatim) |
|---|---|---|---|
| 1 | `CORPUS_REDERIVE_DRIFT_HALT` | A_null arm `a_share_h8` for any of v0.42 / v0.44 / v0.45 drifts > 1e-3 from the published reference | "Halt: A_null re-anchor drifted from the published Results value for {version}; v0.52's deterministic re-execution does not reproduce the published metric within 1e-3." |
| 2 | `INTERVENTION_OPPOSITE_SIGN_HALT` | any arm's gating-label primary signed_d ≤ −0.5 | "Halt: a v0.52 spatial / foraging primary fires in the WRONG direction under a gating label; the channel-decoupling intervention is incompatible with the locked expected signs." |
| 3 | `BRIDGE_REPLICATION_HALT` | (a) A_null arm's signed_d for any of the six v0.48 cells drifts > 1e-3 from the v0.48 published value, OR (b) A_null sub-verdict ≠ `A_NULL_BRIDGE_PRESENT` | "Halt: v0.52's A_null arm does not reproduce v0.48's spatial bridge — either a paired_d cell drifts beyond 1e-3 of the published value, or the A_null sub-verdict does not resolve to PRESENT. v0.52 cannot interpret the B / C arms without an established baseline." |

The Tier-1 bridge re-anchor's hardcoded references (extracted from v0.48 Results §"Paired Cohen's d per (label, primary observable) — all six cells fire"):

| label | observable | sign | published signed_d |
|---|---|:-:|:-:|
| `label_a_sensor_radius` | `pre50_food_events_count` | + | **+1.066** |
| `label_a_sensor_radius` | `pre50_food_energy_acquired` | + | **+1.066** |
| `label_a_sensor_radius` | `mean_distance_to_nearest_food_cell` | − | **+1.916** |
| `label_b_readiness_fraction` | `pre50_food_events_count` | + | **+0.916** |
| `label_b_readiness_fraction` | `pre50_food_energy_acquired` | + | **+0.916** |
| `label_b_readiness_fraction` | `mean_distance_to_nearest_food_cell` | − | **+1.179** |

Drift tolerance = 1e-3. Same protocol as v0.49 / v0.50 / v0.51.

**No Tier-2 re-anchor.** B and C are new interventions never run before; there are no published reference cells against which to byte-anchor them. Their interpretive validity is anchored by (a) the Tier-1 A_null re-anchor (proves the simulator is in the same baseline state v0.48 measured) plus (b) the four locked implementation-equivalence tests below (prove the `src/` changes preserve A_null byte-identity AND that B/C arms reach the intended channel hooks without RNG offset).

### Outcome conditions (only consulted if no halt fires)

The 2 × 3 sub-verdict matrix over (B sub-verdict, C sub-verdict) ∈ {PRESENT, PARTIAL, NOT_FOUND} × {PRESENT, PARTIAL, NOT_FOUND} = 9 cells, partitioned into the four locked categorical outcomes plus a `CHANNELS_MIXED` catch-all for any cell containing PARTIAL.

| priority | rollup verdict | (A_null, B, C) sub-verdicts | locked phrase (verbatim) |
|---|---|---|---|
| 4 | `INFORMATION_RADIUS_LOAD_BEARING` | (A_NULL_BRIDGE_PRESENT, B_ZERO_COST_BRIDGE_PRESENT, C_UNIFORM_RADIUS_BRIDGE_NOT_FOUND) | "On the modern A_null corpus, the v0.48 spatial / foraging bridge survives flattening of the metabolic-cost channel and disappears under flattening of the information-radius channel; the information-radius channel is the load-bearing component of the founder `sensor_radius` causal contribution." |
| 5 | `METABOLIC_COST_LOAD_BEARING` | (A_NULL_BRIDGE_PRESENT, B_ZERO_COST_BRIDGE_NOT_FOUND, C_UNIFORM_RADIUS_BRIDGE_PRESENT) | "On the modern A_null corpus, the v0.48 spatial / foraging bridge survives flattening of the information-radius channel and disappears under flattening of the metabolic-cost channel; the metabolic-cost channel is the load-bearing component of the founder `sensor_radius` causal contribution." |
| 6 | `BOTH_CHANNELS_INDEPENDENTLY_SUFFICIENT` | (A_NULL_BRIDGE_PRESENT, B_ZERO_COST_BRIDGE_PRESENT, C_UNIFORM_RADIUS_BRIDGE_PRESENT) | "On the modern A_null corpus, the v0.48 spatial / foraging bridge survives independent flattening of either the metabolic-cost channel or the information-radius channel; both channels can independently support the bridge under the locked V0_25 anchor." |
| 7 | `CHANNELS_COUPLED_OR_SHARED_CONFOUND` | (A_NULL_BRIDGE_PRESENT, B_ZERO_COST_BRIDGE_NOT_FOUND, C_UNIFORM_RADIUS_BRIDGE_NOT_FOUND) | "On the modern A_null corpus, the v0.48 spatial / foraging bridge does not survive independent flattening of either the metabolic-cost channel or the information-radius channel; the bridge requires the coupled `sensor_radius` trait, OR a shared confound v0.52 does not probe (e.g., trait covariance, founder-position interaction, or a non-linear interaction between the two channels)." |
| 8 | `CHANNELS_MIXED` | A_NULL_BRIDGE_PRESENT and at least one of (B sub-verdict, C sub-verdict) ∈ {PARTIAL} | "On the modern A_null corpus, v0.52's intervention arms do not resolve to a single load-bearing channel under the locked categorical criteria; at least one arm is in PARTIAL state and the channel decomposition is therefore not definitive." |

The rollup is **categorical-only** — no magnitude-delta rule between B and C. Magnitude differences in B vs C signed_d cells are reported descriptively in Results but do not alter the verdict. PARTIAL is preserved as a first-class sub-verdict and routed to `CHANNELS_MIXED`; it is NOT halted on, NOT coerced to NOT_FOUND, and NOT coerced to PRESENT.

The 5 non-halt outcomes form a total partition of the 3 × 3 (B, C) sub-verdict space under A_null PRESENT:

| B \ C | PRESENT | PARTIAL | NOT_FOUND |
|:-:|:-:|:-:|:-:|
| **PRESENT** | BOTH_INDEP_SUFFICIENT (6) | MIXED (8) | INFO_RADIUS_LOAD_BEARING (4) |
| **PARTIAL** | MIXED (8) | MIXED (8) | MIXED (8) |
| **NOT_FOUND** | METABOLIC_COST_LOAD_BEARING (5) | MIXED (8) | CHANNELS_COUPLED_OR_CONFOUND (7) |

Total partition: 9 cells → 4 single-outcome cells (corners) + 5 MIXED cells (anywhere a PARTIAL appears). Test #16 enforces this partition exhaustively.

The rollup is **conservative**: locked phrases use "load-bearing", "independently sufficient", "coupled or shared confound" — NOT "is causal for", "proves", or "rules out". Mechanism declarations require fresh-stream calibration analogous to v0.30..v0.33; v0.52 is a paired channel-decoupling probe and cannot rule out higher-order interactions, trait-covariance effects, or non-V0_25-anchor behavior.

## Cautious framing (per CLAUDE.md)

- "**Load-bearing**", "**independently sufficient**", "**coupled or shared confound**" — NOT "**proves**", "**causes**", or "**rules out**".
- "**On the modern A_null corpus**" / "**under the locked V0_25 anchor**" — NOT a chamber-config-independent claim.
- "**Information radius**" and "**metabolic cost**" refer specifically to the two `sensor_radius` consumption channels in the V0_25 simulator: (a) `sensors.observe` + `_read_memory_directional` external/memory radius reads, (b) `apply_metabolism`'s `sensor_radius_metabolic_cost * body.traits.sensor_radius` term. They do NOT generalize to "information vs cost" in any broader cognitive-science sense.
- **C is an equalizing uplift, not a neutral subtraction.** Under C, every agent senses with radius 6 — the V0_25 max draw value. Low-radius agents experience an information uplift; high-radius agents experience no information change. C is therefore a probe of "what happens when between-agent information variation is removed by raising everyone to the maximum", not "what happens when information is uniformly reduced". The alternative override (e.g., uniform radius 4 = mean draw) would create a distinct asymmetry (low-radius helped, high-radius nerfed); v0.52 does not test that.
- v0.52 explicitly does not establish: cross-layout generalisation, mechanism (the *route* by which the load-bearing channel produces spatial advantage), trait-covariance effects beyond `sensor_radius` itself, post-tick-50 dominance dynamics, or behavior under non-V0_25 anchors.

## What v0.52 cannot establish (logged here pre-data, not retrofittable)

- ✗ **Mechanism for the load-bearing channel**. If `INFORMATION_RADIUS_LOAD_BEARING` fires, v0.52 establishes that wider sensing access is sufficient for the bridge — but does not isolate WHY (e.g., earlier food detection, better hazard avoidance, longer-range gradient following). If `METABOLIC_COST_LOAD_BEARING` fires, v0.52 establishes that cost-asymmetry is sufficient — but does not isolate the route (e.g., low-radius founders out-survive high-radius founders pre-50, founder energy-budget-driven reproduction timing, or some emergent population-dynamic effect).
- ✗ **Generalisation beyond V0_25 anchor / tight_gradient layout / 5 founders / height-6 grid**. Layout, policy, reproduction config, and trait config are all V0_25 anchor.
- ✗ **Causality for post-tick-50 dominance**. v0.52 measures the v0.48 *bridge* (pre-50 spatial / foraging primaries vs Labels A and B). It does not directly probe v0.46's b50-share dominance label.
- ✗ **Channel-attribution under uniform-mean-radius (4)**. C uses the maximum radius (6) as the uniform-effective override; it does NOT test uniform mean (4). The asymmetry between "uplifting low-radius agents to the max" vs "moving every agent to the population mean" is a deliberate design choice (avoids the buff/nerf ambiguity); a future v0.52b could probe it if a follow-up question demands.
- ✗ **Detection of higher-order interactions between the two channels.** The 4-cell decision matrix assumes the two channels are independent. If the bridge's behavior under (B AND C ablated jointly) is non-additive — e.g., the bridge fires under both B alone and C alone but disappears when both are ablated — v0.52's locked outcomes don't have a verdict for that. A "both ablated" arm could be added in a follow-up; it is intentionally not in v0.52's scope to keep the 3-arm wall time bounded and the rollup tractable.
- ✗ **Resolution of `CHANNELS_COUPLED_OR_SHARED_CONFOUND` between "coupling" and "shared confound"**. If the (NOT_FOUND, NOT_FOUND) cell fires, v0.52 cannot tell whether the bridge needs the coupled trait or whether it actually depends on something v0.52 didn't probe (trait covariance, founder-position-interaction, etc.). The locked phrase is deliberately disjunctive; resolution requires further intervention slices.

## Open framing (NOT in v0.52)

- v0.53 candidate: cross-layout generalisation (run v0.48–v0.52 on `widened_gradient` and / or `food_ladder`).
- v0.54 candidate: "both ablated" arm — `sensor_radius_metabolic_cost = 0` AND `effective_sensor_radius_override = 6`. Tests for higher-order interactions between the two channels.
- v0.55 candidate: uniform-mean-radius (4) probe — symmetric to C but with the buff/nerf semantics. Optional follow-up if a question specifically demands it.
- Eventual fresh-stream calibration (v0.30-style) on the v0.46–v0.52 conclusion stack — needed for any "mechanism" declaration.

## Re-anchor (locked — Tier-1 only)

| version | published `a_share_h8` |
|---|---|
| v0.42 | 0.652 |
| v0.43R | NOT PUBLISHED (informational-only) |
| v0.44 | 0.878 |
| v0.45 | 0.818 |

A_null arm only gates the rollup. B and C arms re-derive their own `a_share_h8` for descriptive logging; they do NOT gate the verdict.

**No Tier-2 re-anchor against v0.49 / v0.50 / v0.51.** B and C are new channel-decoupling interventions; there are no published reference cells to byte-anchor them against. Their validity is anchored by:

1. The Tier-1 A_null re-anchor (proves the simulator is in the same baseline state v0.48 measured).
2. The four locked implementation-equivalence tests below (prove the `src/` change preserves A_null byte-identity AND that B/C reach the intended channel hooks without RNG offset).

## Outputs (locked)

```
runs/v0.52-information-vs-cost/per_run_per_lineage_v052.csv
  columns: arm, version, seed, hazard, run_id, lineage_id,
           founder_sensor_radius, founder_reproduction_drive, founder_metabolic_rate,
           pre50_food_events_count, pre50_food_energy_acquired,
           mean_distance_to_nearest_food_cell,
           tick50_living_count, tick50_above_threshold_count, tick50_above_threshold_fraction,
           b50_count, is_eventual_top_b50_label,
           is_high_sensor_radius_lineage, is_high_tick50_readiness_fraction_lineage,
           body_config_sensor_radius_metabolic_cost,
           body_config_effective_sensor_radius_override

runs/v0.52-information-vs-cost/audit_summary.csv
  columns: section, key, value
  sections:
    - reanchor_a_share_h8: per (arm, version, h=8) derived + (A_null only) published + drift_abs
    - bridge_reanchor: per (label, observable) v0.48 published signed_d + v0.52 A_null derived + drift_abs
    - paired_d: per (arm, gating-label, observable) cell — paired_d, signed_d, n_runs, fires_expected, fires_wrong
    - sub_verdicts: per arm — sub-verdict + locked sub-phrase
    - rollup_verdict: locked rollup verdict + locked rollup phrase

runs/v0.52-information-vs-cost/audit_log.txt
  human-readable echo with all locked phrases printed verbatim where they fire,
  plus per-arm paired_d tables and the 9-cell (B, C) decision matrix.
```

## Implementation plan (locked)

1. **`src/` changes (one-time, default-preserving)**:
   - `src/hedonism_harness/core/config.py`: add `effective_sensor_radius_override: int | None = Field(default=None, ge=0)` to `BodyConfig` (between `sensor_radius_metabolic_cost` and the validator).
   - `src/hedonism_harness/core/sensors.py:123`: replace `radius = int(body.traits.sensor_radius)` with the override-resolver pattern.
   - `src/hedonism_harness/core/sensors.py:196` (ValenceMemory branch only): same override-resolver pattern.
   - DirectionalMemory branch (line 198+): NOT modified.
   - `apply_metabolism` (`src/hedonism_harness/core/body.py:81`): NOT modified.
2. Fresh script `scripts/v0_52_information_vs_cost_audit.py`. CLI: `uv run python scripts/v0_52_information_vs_cost_audit.py [--out-dir runs/v0.52-information-vs-cost]`.
3. Per (version, seed, hazard) tuple, run **3 arms**. Every arm constructs `HHModel` via the normal A_null path (`FounderSpec(traits_override=None)`):
   - **A_null**: no `body_config` swap. Default `BodyConfig()`.
   - **B_zero_sensor_cost**: inside `setup_observer`, replace `model.body_config` with `model.body_config.model_copy(update={"sensor_radius_metabolic_cost": 0.0})`. No trait mutation.
   - **C_uniform_effective_radius_6**: inside `setup_observer`, replace `model.body_config` with `model.body_config.model_copy(update={"effective_sensor_radius_override": 6})`. No trait mutation.
4. For each arm-run, attach v0.48-style `setup_observer` + `tick_observer` (copy-local from v0.48 / v0.49 / v0.50 / v0.51). The setup_observer order is: (a) apply body_config swap (B / C) or no-op (A_null), (b) capture v0.52 founder audit table from live bodies, (c) wire `AgentBorn` / `AteFood` / `HazardDamageApplied` listeners (`sender=model`), (d) capture tick 0 snapshot.
5. Aggregate per-lineage primaries identical to v0.48–v0.51. Compute Label A and Label B per the standard definitions (founder `sensor_radius` from the unmutated draw; tick-50 readiness fraction).
6. Compute paired_d per (arm, gating-label, observable) cell (18 cells total). Classify per-arm sub-verdicts.
7. **Tier-1 bridge re-anchor** (priority 3): A_null arm's six cells vs v0.48 published; halt if drift > 1e-3 OR if A_null sub-verdict ≠ PRESENT.
8. **Corpus re-anchor** (priority 1): A_null arm only; halt if `a_share_h8` for v0.42 / v0.44 / v0.45 drifts > 1e-3.
9. **Opposite-sign halt** (priority 2): scan all gating-label cells across all three arms; halt if any signed_d ≤ −0.5.
10. Compute slice rollup verdict per the locked priority + (B, C) decision matrix; print + write the locked phrase verbatim.

The reducer is fully self-contained: it reads no `runs/` artifacts. Wall time estimate ~10 minutes for 192 runs (matches v0.49 / v0.50 / v0.51).

## Test list (locked, 16 tests; extends v0.46–v0.51 7-point review pattern)

`tests/test_v0_52_information_vs_cost_audit.py`:

1. `test_all_arms_construct_founders_via_normal_a_null_path` — for every arm, `FounderSpec` is constructed with `traits_override=None`; founder original `sensor_radius` per founder is byte-identical across arms for the same (version, seed, hazard) tuple.
2. `test_b_replaces_body_config_with_zero_sensor_cost` — construct `HHModel` for a representative tuple, run B's `setup_observer`; assert `model.body_config.sensor_radius_metabolic_cost == 0.0` and every other `BodyConfig` field byte-identical to the default. Assert no `agent.body.traits` field is mutated for any agent.
3. `test_c_passes_effective_sensor_radius_override_via_body_config` — construct `HHModel` for a representative tuple, run C's `setup_observer`; assert `model.body_config.effective_sensor_radius_override == 6` and every other `BodyConfig` field (including `sensor_radius_metabolic_cost == 0.05`) byte-identical to the default. Assert no `agent.body.traits` field is mutated for any agent.
4. **`test_default_equivalence_preserves_byte_identity`** *(implementation-equivalence test)* — with `BodyConfig()` defaults (override=None, cost=0.05) the modified `sensors.observe` and `_read_memory_directional` produce byte-identical outputs to a synthetic baseline computation using `int(body.traits.sensor_radius)` directly. Verifies the resolver pattern's None-default branch is byte-equivalent to the original code path for every `(world, body, memory)` triple in a small synthetic test grid (pre-modification behavior preserved).
5. `test_c_override_reaches_observe_axial_scan` — set `effective_sensor_radius_override=6` on a synthetic `body_config`; call `sensors.observe(world, body, body_config, memory)` with a synthetic body whose `traits.sensor_radius=2`; assert the axial-scan output reflects radius 6 (probes cells 1..6 along each axis) NOT radius 2.
6. `test_c_override_reaches_valence_memory_directional_scan` — set `effective_sensor_radius_override=6`; build a synthetic `ValenceMemory` with markers at distances 3, 4, 5, 6 along one axis from `(body.x, body.y)`; call `_read_memory_directional` with a body whose `traits.sensor_radius=2`; assert the directional signal includes contributions from distances 3..6 (would be 0 for distance > 2 if the override didn't reach this path).
7. **`test_c_override_does_not_affect_apply_metabolism`** *(implementation-equivalence test)* — set `effective_sensor_radius_override=6` on `body_config`; call `apply_metabolism(body, body_config)` with a body whose `traits.sensor_radius=2`; assert the post-step energy reflects the cost computation `body_config.sensor_radius_metabolic_cost * 2` (the trait value), NOT `body_config.sensor_radius_metabolic_cost * 6` (the override). The metabolic-cost channel must remain trait-tied even under C.
8. `test_c_override_does_not_affect_directional_memory_path` — build a synthetic `DirectionalMemory` (the v0.11 4-vector path); set `effective_sensor_radius_override=6`; call `_read_memory_directional` with a body whose `traits.sensor_radius=2`; assert the output equals the unmodified DirectionalMemory tendencies. The `DirectionalMemory` branch does not consume `sensor_radius`, so the override has no effect there. (Defensive against future refactors that might accidentally route the override through the DirectionalMemory branch.)
9. **`test_no_rng_setup_offset_across_arms`** *(implementation-equivalence test)* — for the same (version, seed, hazard), run all three arms; assert that each arm's tick-0 founder audit table (lineage_id → original sensor_radius, reproduction_drive, metabolic_rate) is byte-identical across arms. Verifies that neither the body_config swap (B, C) nor the modified `sensors.observe` resolver consumes RNG during `setup_observer`.
10. `test_per_arm_subverdict_a_null_present_requires_both_labels_clear` — synthetic (Label A 2/3, Label B 2/3) → A_NULL_BRIDGE_PRESENT. Synthetic (Label A 1/3, Label B 2/3) → A_NULL_BRIDGE_PARTIAL.
11. `test_per_arm_subverdict_b_zero_cost_present_requires_both_labels_clear` — same logic for B; PRESENT requires both labels clear; PARTIAL when only one clears.
12. `test_per_arm_subverdict_c_uniform_radius_present_requires_both_labels_clear` — same logic for C.
13. `test_rollup_information_radius_load_bearing_when_present_notfound` — synthetic (A_null PRESENT, B PRESENT, C NOT_FOUND); assert rollup = `INFORMATION_RADIUS_LOAD_BEARING` and locked phrase contains "information-radius channel is the load-bearing component" verbatim.
14. `test_rollup_metabolic_cost_load_bearing_when_notfound_present` — synthetic (A_null PRESENT, B NOT_FOUND, C PRESENT); assert rollup = `METABOLIC_COST_LOAD_BEARING`.
15. `test_rollup_both_independently_sufficient_and_coupled_or_confound` — synthetic (PRESENT, PRESENT, PRESENT) → `BOTH_CHANNELS_INDEPENDENTLY_SUFFICIENT`; (PRESENT, NOT_FOUND, NOT_FOUND) → `CHANNELS_COUPLED_OR_SHARED_CONFOUND`. Both locked phrases verified.
16. **`test_rollup_channels_mixed_for_partial_and_priority_halt_partition_total`** — exhaustively iterate the 3 × 3 (B sub-verdict, C sub-verdict) ∈ {PRESENT, PARTIAL, NOT_FOUND}² space under A_null PRESENT; assert each cell maps to exactly one of the 5 outcome verdicts; assert the 5 PARTIAL-containing cells all map to `CHANNELS_MIXED`. Also synthesise a `BRIDGE_REPLICATION_HALT` (priority 3) and assert it fires before the outcome verdicts; synthesise a `CORPUS_REDERIVE_DRIFT_HALT` (priority 1) and assert it fires before the bridge halt.

## Watch-outs (for future-Chronus)

- **One `src/` change in v0.52.** Unlike v0.46–v0.51, this slice modifies `src/`. The change is minimum-viable (one new optional pydantic field + two-line resolver pattern at two call sites) and default-preserving (`override=None` reproduces the original code path byte-identically). All 1664 existing tests must continue to pass without modification — the modified `src/` is forward-compatible. If any prior-version test fails after the `src/` change, halt loud and investigate before proceeding to the v0.52 reducer.
- **B replaces `model.body_config`, does not mutate fields.** `BodyConfig` is `frozen=True`; mutating `model.body_config.sensor_radius_metabolic_cost` directly would raise `ValidationError`. The correct idiom is `model.body_config = model.body_config.model_copy(update={...})` which produces a frozen-clone and rebinds the attribute. Test #2 enforces this.
- **C does NOT modify `apply_metabolism`.** The C arm's whole point is to leave the metabolic-cost channel intact. If a future refactor routes the `effective_sensor_radius_override` through `apply_metabolism`, the channel decoupling collapses and the slice's verdict structure breaks. Test #7 enforces this.
- **DirectionalMemory branch is intentionally not modified.** v0.51 (and the modern A_null corpus) uses `cell_exact` / `ValenceMemory`, not `DirectionalMemory`. The v0.52 `effective_sensor_radius_override` should not be consulted in the `DirectionalMemory` branch because that branch reads pre-aggregated 4-vector tendencies that have no spatial-radius parameter. Test #8 enforces this.
- **C is an equalizing uplift to max radius, NOT a neutral subtraction.** Documented in "Choice of override value" above and elevated to first-class caveat in Cautious framing. Future readers should not interpret a `C_UNIFORM_RADIUS_BRIDGE_NOT_FOUND` outcome as "removing information kills the bridge"; the correct interpretation is "removing between-agent variation in effective sensing radius (by raising everyone to the maximum) kills the bridge".
- **Label A under C is well-defined but interpretively subtle.** Label A picks the lineage whose founder *originally drew* the highest `sensor_radius`, but under C every agent senses with radius 6 regardless of trait. The question Label A asks under C is therefore: "does the original founder `sensor_radius` advantage still predict the bridge when its information-radius component is flattened?" — exactly the channel-decomposition question the slice is designed to answer. Pre-reg this for clarity; do not retrofit the interpretation post-data.
- **No Tier-2 re-anchor for B and C.** B and C are new interventions; there are no v0.49 / v0.50 / v0.51 published cells they should byte-reproduce. Their validity rests on Tier-1 + the four implementation-equivalence tests. If a future slice extends v0.52, those new arms can use v0.52's B/C signed_d cells as a Tier-2 reference.
- **`src/` change preserves the A_null re-anchor by construction.** Default `effective_sensor_radius_override=None` plus default `sensor_radius_metabolic_cost=0.05` exactly reproduces today's behavior. Test #4 enforces the byte-identity of the resolver's None-default branch; the existing 1664-test pytest suite passing without modification is the corpus-level enforcement.
- **B and C consume no RNG at setup.** `model_copy(update=...)` is a pure pydantic clone; no random draws. Test #9 enforces founder-trait byte-identity across arms.
- **Locked phrase discipline:** all sub-verdict and rollup locked phrases fire verbatim where the verdict fires. No paraphrase.
- **Determinism north star** ([[scripts/core_smoke_test.py]]) must continue to pass under the modified `src/`. Default behavior is byte-identical by construction, so the smoke test passes without modification; verify explicitly during implementation.

## Files this slice will create / modify

- `docs/experiments/fear_hunger_v0.52.md` (this file; Results section appended after reducer run)
- `scripts/v0_52_information_vs_cost_audit.py` (new)
- `tests/test_v0_52_information_vs_cost_audit.py` (new, 16 tests)
- `src/hedonism_harness/core/config.py` (one new optional `BodyConfig` field)
- `src/hedonism_harness/core/sensors.py` (two-line resolver at lines ~123 and ~196 ValenceMemory branch)

No other files modified.

## Results

**Status:** pending reducer run.
