# fear_hunger v0.51 — descendant-drift probe (founder + lineage-wide sensor_radius clamp)

**Slice:** v0.51
**Type:** **first-class intervention** (NOT a post-hoc reducer); founder-time + descendant-time `sensor_radius` clamp.
**Predecessors:** v0.21..v0.27 (substrate / aggregate-optimum), v0.34..v0.36 (lineage observability + heritability), v0.42..v0.45 (substrate-causal arc), v0.46 (`READINESS_PREDICTS_DOMINANCE`), v0.47 (`READINESS_TRAITS_PARTIALLY_PREDICTIVE`), v0.48 (`SENSOR_RADIUS_SPATIAL_BRIDGE_PRESENT`), v0.49 (`SENSOR_RADIUS_CAUSAL_CONTRIBUTION_SUPPORTED`: founder clamp + permutation establishes single-channel founder-time causal probe; descendants of clamped founders mutate freely), v0.50 (`SENSOR_RADIUS_ROBUST_TO_POSITION`: shifted-top + permuted founder positions do not break the bridge).
**Question being asked (locked):** Does v0.49's founder-clamp result depend on the *founder-only* clamp leaving descendants free to mutate `sensor_radius`, or does the result hold (or strengthen) when `sensor_radius` is clamped throughout the lineage?

v0.49's `B_sensor_radius_founder_clamp_4` arm clamps founders at `sensor_radius=4` but leaves the per-tick mutation pipeline untouched, so descendants of clamped founders are free to drift away from 4 via `mutate_traits`. The pre-50 window has limited reproductive opportunity, but reproduction does occur (see `model.trait_fingerprints` records of post-tick-0 births in v0.49 logs). v0.51 closes that residual channel by additionally patching every newborn's `sensor_radius` back to 4 immediately after birth, before the newborn's first `model.step()`. The slice asks whether the v0.49 founder-clamp NOT_FOUND verdict reproduces under lineage-wide clamping (consistent with founder variation being the load-bearing channel) or weakens further (consistent with descendant drift contributing on top of founder variation).

## Pre-implementation correction (2026-05-08, before any reducer code)

The descendant-clamp implementation path was investigated by sub-agent and locked at design time per the v0.51 handoff. The locked design is **Option 1**: a script-local `AgentBorn` listener applied per-run inside `setup_observer`, single-channel-patching the newborn's `body.traits.sensor_radius` to 4 before the newborn takes its first step. The user has further refined this design with three implementation locks; recorded here for the historical record. No data has been seen yet.

### Listener safety (locked)

The `AgentBorn` listener is connected with **both** strong-reference protections, redundantly:

```python
def _on_agent_born(_sender: object, *, event: AgentBorn) -> None:
    ...

signal_for(AgentBorn).connect(_on_agent_born, sender=model, weak=False)
disconnect_callbacks.append(
    lambda: signal_for(AgentBorn).disconnect(_on_agent_born, sender=model)
)
```

`weak=False` removes any ambiguity about blinker's reference handling; the closure capture in `disconnect_callbacks` is belt-and-braces. Disconnect happens in a `finally` block in the per-run scope so a failed run does not leak a sender-scoped listener into later runs:

```python
try:
    run_chamber(... setup_observer=setup, tick_observer=...)
finally:
    for disconnect in disconnect_callbacks:
        disconnect()
```

### Descendant patch counters (locked)

The C-arm reducer logs four counters per run for audit transparency:

| counter | semantics |
|---|---|
| `n_births_seen` | total `AgentBorn` events the listener observed in ticks 1..200 |
| `n_births_patched` | number of newborn body patches actually written by the listener (every birth gets a patch write — even no-op writes, see below) |
| `n_births_already_sensor_radius_4` | number of births where `original_sensor_radius == 4` already (mutated draw landed on the clamp value); the patch is a no-op write, NOT a failure |
| `n_birth_patch_failures` | number of births where the single-channel invariant raised; expected = 0 |

A child whose mutated `sensor_radius` happens to equal 4 is a legitimate no-op patch — the listener still runs the `dataclasses.replace(...)` write and the single-channel invariant should still pass on every non-`sensor_radius` field. `n_births_patched == n_births_seen` always; `n_birth_patch_failures == 0` always under correct implementation (loud halt otherwise via `V051ReducerError`).

### Audit-truth: do not consume `model.trait_fingerprints` for v0.51

`HHModel._record_trait_fingerprint` (model.py ~line 386 for founders; descendants recorded via the equivalent path inside `_spawn_child` before `AgentBorn` emits) records the **pre-patch** trait vector for descendants. After v0.51's listener patches the newborn body, the body's `sensor_radius` differs from `model.trait_fingerprints`'s record. This is not a behavioral problem (the simulator continues with the patched body), but it is an audit-truth problem: any v0.51 metric that reads `model.trait_fingerprints` would observe pre-patch values and would not measure what the slice claims to measure.

**Locked**: v0.51's reducer ignores `model.trait_fingerprints` entirely for the C-arm audit. It captures its own audit table from live `model.agents` post-patch, with explicit columns:

```
founder_original_sensor_radius
founder_assigned_sensor_radius
child_original_sensor_radius          # mutated draw value, captured immediately before listener patch
child_assigned_sensor_radius          # post-patch value (always 4 for arm C)
```

`model.trait_fingerprints` is left untouched (no mutation, no read) — same conservative treatment as v0.49's option A.

This correction does not change the verdict structure, arm count, corpus, observable definitions, label-A-degeneracy semantics, two-tier re-anchor, slice rollup outcomes, or locked phrases. It locks the listener-side implementation discipline and the audit-table schema.

## Conservation framing — interventional, not observational

- **No `src/` modifications.** v0.51's intervention is fully script-local: founder-time body trait patches inside `setup_observer` (B and C arms), and descendant-time body trait patches inside an `AgentBorn` listener registered for the duration of one run (C arm only).
- **No modifications to prior reducer or audit scripts.** v0.34's `lineage_replay.py`, v0.35's `lineage_survival_replay.py`, v0.36's `trait_replay.py`, the four substrate audits (v0.42 / v0.43R / v0.44 / v0.45), and v0.46 / v0.47 / v0.48 / v0.49 / v0.50's reducers remain byte-identical to their merged forms.
- **No `traits_override`.** All arms construct founders through the normal A_null path with `FounderSpec(traits_override=None)`. The B and C founder patches are applied post-construction inside `setup_observer`, identical to v0.49's locked pattern.
- **No `model.trait_fingerprints` consumption for the v0.51 descendant audit.** v0.51 captures its own audit table from live bodies post-patch (see Pre-implementation correction).
- **A_null arm is byte-identical to v0.48 / v0.49 / v0.50's A_null path.** No patch applied. RNG streams (`streams.mutation`, per-agent RNGs) and per-tick state are identical for the same (version, seed, hazard) tuple. Byte-identity verified by the Tier-1 bridge re-anchor halt below.
- **B arm copies v0.49's founder-clamp logic verbatim.** Same `dataclasses.replace(traits, sensor_radius=4)` on each founder body inside `setup_observer`, before tick-0 capture. Byte-identity verified by the Tier-2 founder-clamp re-anchor halt below.
- **C arm extends B with a per-run `AgentBorn` listener** that single-channel-patches every newborn's `body.traits.sensor_radius` to 4 before the newborn's first `model.step()`. The listener is registered inside `setup_observer` after the founder patch and the v0.48-style signal listeners, and is disconnected in a `finally` block at run end.
- **B and C arms diverge from A_null at tick 0.** Only because founder `sensor_radius` differs. C also diverges from B at every newborn's first step because newborn `sensor_radius` is 4 under C and the parent-mutated draw under B. RNG streams (`streams.mutation`, per-agent RNGs) are byte-identical at the moment of the first `model.step()` across all three arms; the listener does not consume any RNG.
- **Single-channel intervention.** B and C modify ONLY the `sensor_radius` field of body trait vectors (founders for B; founders + descendants for C). All other fields come from the model's normal draw / mutation pipeline. A runtime invariant (`V051ReducerError`) enforces this on every founder patch (B, C) and every newborn patch (C). Loud halt on any non-`sensor_radius` field difference between `original_traits` and `assigned_traits`.
- **No mutation pipeline modification.** v0.51 does NOT override `mutate_traits`. Descendants under arm C still mutate `sensor_radius` *during* `mutate_traits` — the listener overwrites the mutated value back to 4 *after* birth, before the newborn first steps. From the lineage's behavioral perspective, every agent has `sensor_radius=4` at every step it takes; from the mutation pipeline's perspective, nothing is unusual.
- **Mesa cell occupancy unchanged.** v0.51 does not modify `agent.body.x`, `agent.body.y`, or `agent.cell` — only the `traits.sensor_radius` field. No two-phase patch is required (contrast v0.50 which had to detach + re-attach for the capacity-1 grid).

## Corpus (locked, 64 × 3 arms = 192 runs)

| version | seeds | hazards | runs per arm | total runs |
|---|---|---|---|---|
| v0.42 | 41..48 | {0, 8} | 16 | 48 |
| v0.43R | 49..56 | {0, 8} | 16 | 48 |
| v0.44 | 57..64 | {0, 8} | 16 | 48 |
| v0.45 | 65..72 | {0, 8} | 16 | 48 |
| **total** | | | | **192** |

V0_25 anchor unchanged from v0.46–v0.50. Each (version, seed, hazard) tuple is run **3 times** — once per arm. Wall time estimate: ~10 minutes for 192 runs (matches v0.49 / v0.50).

## Default V0_25 founder draw (for reference)

`tight_gradient` layout, 5 founders at `(spawn_x=1, spread_y(5, 6))` = `[(1,0), (1,1), (1,2), (1,3), (1,4)]`. `TraitConfig(unbounded_mutation=True)` draws integer-valued `sensor_radius` from {1..6}. v0.49's per-run audit logs original founder `sensor_radius` values; v0.51's A_null arm is byte-identical to v0.49 A_null in this respect.

## Arms (locked, 3)

### A_null

```
no patch
```

Founder traits, agent RNGs, and `streams.mutation` byte-identical to v0.48 / v0.49 / v0.50's A_null arm. Used as the bridge replication baseline for the Tier-1 re-anchor.

### B_founder_clamp_4

For each (version, seed, hazard) tuple, the reducer constructs `HHModel` normally and applies the founder patch inside `setup_observer`, before tick-0 capture:

1. `HHModel(...)` returns with 5 founder agents constructed normally; `random_traits` and `spawn_agent_rng` consume from `streams.mutation` exactly as A_null.
2. Inside `setup_observer`, for each founder agent (sorted by lineage_id):
   ```python
   original_traits = agent.body.traits
   assigned_traits = dataclasses.replace(original_traits, sensor_radius=4)
   agent.body = dataclasses.replace(agent.body, traits=assigned_traits)
   ```
3. Single-channel founder invariant: every non-`sensor_radius` field of `original_traits` equals the corresponding field of `assigned_traits`. Loud halt (`V051ReducerError`) on any difference.
4. Capture v0.51's founder audit row per founder: `(lineage_id, founder_original_sensor_radius, founder_assigned_sensor_radius=4, all_other_founder_traits)`.
5. **No `AgentBorn` listener.** Descendants of B-arm founders mutate freely via the normal pipeline (this is exactly v0.49's B arm).

By construction, B's per-run, per-tick state is byte-identical to v0.49's `B_sensor_radius_founder_clamp_4` arm for the same (version, seed, hazard) tuple. Tier-2 re-anchor below verifies this at metric level.

### C_lineage_clamp_4

For each (version, seed, hazard) tuple, identical setup to B (normal `HHModel` construction; founder patch in `setup_observer` before tick 0). **Additionally**, inside `setup_observer` after the founder patch and the v0.48-style signal listeners are wired, the reducer registers a per-run `AgentBorn` listener:

```python
patch_counters = {
    "n_births_seen": 0,
    "n_births_patched": 0,
    "n_births_already_sensor_radius_4": 0,
    "n_birth_patch_failures": 0,
}

def _on_agent_born(_sender: object, *, event: AgentBorn) -> None:
    patch_counters["n_births_seen"] += 1
    aid = int(event.agent_id)
    target = next((a for a in model.agents if int(a.body.id) == aid), None)
    if target is None:
        patch_counters["n_birth_patch_failures"] += 1
        msg = f"v0.51 C arm: AgentBorn event for agent_id={aid} but no live body found"
        raise V051ReducerError(msg)
    original = target.body.traits
    if int(original.sensor_radius) == 4:
        patch_counters["n_births_already_sensor_radius_4"] += 1
    assigned = dataclasses.replace(original, sensor_radius=4)
    # Single-channel invariant on child: every non-sensor_radius field equal.
    _assert_single_channel_invariant(original, assigned)
    target.body = dataclasses.replace(target.body, traits=assigned)
    capture.child_audit_rows.append(
        ChildAudit(
            tick=int(event.tick),
            agent_id=aid,
            lineage_id=int(event.lineage_id),
            child_original_sensor_radius=int(original.sensor_radius),
            child_assigned_sensor_radius=4,
        )
    )
    patch_counters["n_births_patched"] += 1

signal_for(AgentBorn).connect(_on_agent_born, sender=model, weak=False)
disconnect_callbacks.append(
    lambda: signal_for(AgentBorn).disconnect(_on_agent_born, sender=model)
)
```

The per-run scope wraps the `run_chamber(...)` call in a `try / finally`, with the disconnect loop in `finally` (executes whether the run succeeds, raises, or is interrupted). This guarantees no sender-scoped listener leaks into a later run's `HHModel`.

**Birth-pipeline ordering invariants** (verified by sub-agent investigation; locked in handoff):

- Births fire at phase 7 of `model.step()` (after metabolism / hazard).
- The blinker `send()` is synchronous; the listener fires before `del child_agent`.
- The newborn is reachable via `model.agents` immediately after Mesa registration.
- The listener fires **before** the newborn first steps — its first `model.step()` consumes the patched body.
- `model.trait_fingerprints` for the newborn is recorded by `_record_trait_fingerprint` *before* `AgentBorn` emits and is therefore stale relative to the patched body. v0.51's audit ignores `model.trait_fingerprints` per the Pre-implementation correction above.

The model's `streams.mutation` and per-agent RNGs are NOT consumed by the listener; only the body's `traits.sensor_radius` is overwritten.

## Labels (locked, two)

Label B is unchanged from v0.48 / v0.49 / v0.50 (tick-50 readiness fraction with the 3-tier tiebreak); copy-local from v0.48's reducer.

Label A definition is unchanged (`argmax_lineage(founder_sensor_radius)`, tiebreak `min(lineage_id)`), but **degenerate under both B and C** (all 5 founders have `assigned_sensor_radius == 4` → 5-way tie → `min(lineage_id)` always wins → label A is always lineage 0). Label A is therefore **diagnostic-only** under arms B and C: computed and reported in the per-lineage CSV (`label_a_gating_valid = False`, `label_a_degenerate_reason = "all founders assigned sensor_radius=4"`), but does NOT feed the arm's sub-verdict computation, does NOT enter the per-arm paired_d cells, and does NOT trigger `INTERVENTION_OPPOSITE_SIGN_HALT` even if its descriptive signed_d's are below −0.5.

| arm | Label A gating | Label B gating |
|---|:-:|:-:|
| A_null | gates | gates |
| B_founder_clamp_4 | diagnostic-only (degenerate) | gates |
| C_lineage_clamp_4 | diagnostic-only (degenerate) | gates |

## Primary observables (locked, 3, identical to v0.48 / v0.49 / v0.50)

| # | name | expected sign |
|---|---|:-:|
| 1 | `pre50_food_events_count` | + |
| 2 | `pre50_food_energy_acquired` | + |
| 3 | `mean_distance_to_nearest_food_cell` | − |

Definitions, aggregation rules, NaN handling: copy-local from v0.48 / v0.49 / v0.50. Per-tick observer firing semantics unchanged (tick 0 captured at `setup_observer` time *after* the B/C founder patch; ticks 1..50 captured by `tick_observer`).

## Effect-size rule (locked, sign-aware, identical to v0.48 / v0.49 / v0.50)

```
per_run_delta_O = label_lineage_value_O − mean(non_label_lineage_values_O)
paired_d_O      = mean(per_run_delta_O) / stdev(per_run_delta_O, ddof=1)
signed_d_O      = paired_d_O × expected_sign
fires_expected  iff signed_d_O ≥ +0.5
fires_wrong     iff signed_d_O ≤ −0.5
```

Per-arm NaN handling identical to v0.48 / v0.49 / v0.50. Cross-arm pairing on (version, seed, hazard) is descriptive only.

## Per-arm sub-verdicts (locked)

### A_null arm — gating: Label A AND Label B

| condition | sub-verdict |
|---|---|
| both labels clear ≥ 2/3, 0 wrong-sign | `A_NULL_BRIDGE_PRESENT` |
| exactly one label clears ≥ 2/3, 0 wrong-sign | `A_NULL_BRIDGE_PARTIAL` |
| neither label clears ≥ 2/3, 0 wrong-sign | `A_NULL_BRIDGE_NOT_FOUND` |
| any primary signed_d ≤ −0.5 under either label | `A_NULL_BRIDGE_OPPOSITE_SIGN_HALT` |

### B_founder_clamp_4 arm — gating: Label B only (Label A diagnostic)

| condition | sub-verdict |
|---|---|
| Label B clears ≥ 2/3, 0 wrong-sign | `B_FOUNDER_CLAMP_LABEL_B_BRIDGE_PRESENT` |
| Label B clears < 2/3, 0 wrong-sign | `B_FOUNDER_CLAMP_LABEL_B_BRIDGE_NOT_FOUND` |
| any Label B primary signed_d ≤ −0.5 | `B_FOUNDER_CLAMP_LABEL_B_OPPOSITE_SIGN_HALT` |

### C_lineage_clamp_4 arm — gating: Label B only (Label A diagnostic)

| condition | sub-verdict |
|---|---|
| Label B clears ≥ 2/3, 0 wrong-sign | `C_LINEAGE_CLAMP_LABEL_B_BRIDGE_PRESENT` |
| Label B clears < 2/3, 0 wrong-sign | `C_LINEAGE_CLAMP_LABEL_B_BRIDGE_NOT_FOUND` |
| any Label B primary signed_d ≤ −0.5 | `C_LINEAGE_CLAMP_LABEL_B_OPPOSITE_SIGN_HALT` |

Each arm's paired_d cells are computed independently from the arm's 64-run pool. Label A's paired_d cells under B and C are computed and CSV-reported but do not gate.

## Slice-level rollup verdicts (locked, 8 outcomes, priority-ordered)

Priority order (first-matching wins):

1. `CORPUS_REDERIVE_DRIFT_HALT`
2. `INTERVENTION_OPPOSITE_SIGN_HALT`
3. `BRIDGE_REPLICATION_HALT` (A_null vs v0.48)
4. `FOUNDER_CLAMP_REPLICATION_HALT` (B vs v0.49 B cells)
5. `FOUNDER_CLAMP_REPRODUCED`
6. `LINEAGE_CLAMP_ADDITIONAL_WEAKENING`
7. `LINEAGE_CLAMP_NO_ADDITIONAL_WEAKENING`
8. `LINEAGE_DRIFT_MIXED`

### Halt conditions

| priority | rollup verdict | trigger | locked phrase (verbatim) |
|---|---|---|---|
| 1 | `CORPUS_REDERIVE_DRIFT_HALT` | A_null arm `a_share_h8` for any of v0.42 / v0.44 / v0.45 drifts > 1e-3 from the published reference | "Halt: A_null re-anchor drifted from the published Results value for {version}; v0.51's deterministic re-execution does not reproduce the published metric within 1e-3." |
| 2 | `INTERVENTION_OPPOSITE_SIGN_HALT` | any arm's gating-label primary fires wrong-sign (signed_d ≤ −0.5). Diagnostic-only Label A under B / C does NOT trigger this halt. | "Halt: a v0.51 spatial / foraging primary fires in the WRONG direction under a gating label; the founder + descendant `sensor_radius` clamp intervention is incompatible with the locked expected signs." |
| 3 | `BRIDGE_REPLICATION_HALT` | (a) A_null arm's signed_d for any of the six v0.48 cells drifts > 1e-3 from the v0.48 published value, OR (b) A_null sub-verdict ≠ `A_NULL_BRIDGE_PRESENT` | "Halt: v0.51's A_null arm does not reproduce v0.48's spatial bridge — either a paired_d cell drifts beyond 1e-3 of the published value, or the A_null sub-verdict does not resolve to PRESENT. v0.51 cannot interpret the B / C arms without an established baseline." |
| 4 | `FOUNDER_CLAMP_REPLICATION_HALT` | B arm's six (Label A diagnostic + Label B gating) signed_d cells drift > 1e-3 from v0.49's B-arm published values | "Halt: v0.51's B_founder_clamp_4 arm does not reproduce v0.49's founder-clamp signed_d cells — at least one cell drifts beyond 1e-3 of the v0.49 published value. v0.51 cannot interpret the C arm without an established founder-clamp baseline." |

### Tier-1 (priority 3) re-anchor — A_null vs v0.48

A_null arm's six paired_d cells must reproduce v0.48's published signed_d values within 1e-3:

| label | observable | sign | v0.48 published signed_d |
|---|---|:-:|:-:|
| `label_a_sensor_radius` | `pre50_food_events_count` | + | **+1.066** |
| `label_a_sensor_radius` | `pre50_food_energy_acquired` | + | **+1.066** |
| `label_a_sensor_radius` | `mean_distance_to_nearest_food_cell` | − | **+1.916** |
| `label_b_readiness_fraction` | `pre50_food_events_count` | + | **+0.916** |
| `label_b_readiness_fraction` | `pre50_food_energy_acquired` | + | **+0.916** |
| `label_b_readiness_fraction` | `mean_distance_to_nearest_food_cell` | − | **+1.179** |

Drift tolerance = 1e-3. Same protocol as v0.49 / v0.50.

### Tier-2 (priority 4) re-anchor — B vs v0.49 B cells

B arm's six (Label A diagnostic + Label B gating) signed_d cells must reproduce v0.49's published B-arm values within 1e-3:

| label | observable | sign | v0.49 published B signed_d (Label A diagnostic) |
|---|---|:-:|:-:|
| `label_a_sensor_radius` (diagnostic) | `pre50_food_events_count` | + | **−0.243** |
| `label_a_sensor_radius` (diagnostic) | `pre50_food_energy_acquired` | + | **−0.243** |
| `label_a_sensor_radius` (diagnostic) | `mean_distance_to_nearest_food_cell` | − | **−0.732** (paired_d ≈ +0.732 → signed_d −0.732 with sign=−1) |

| label | observable | sign | v0.49 published B signed_d (Label B gating) |
|---|---|:-:|:-:|
| `label_b_readiness_fraction` | `pre50_food_events_count` | + | **+0.182** |
| `label_b_readiness_fraction` | `pre50_food_energy_acquired` | + | **+0.182** |
| `label_b_readiness_fraction` | `mean_distance_to_nearest_food_cell` | − | **−0.181** |

Drift tolerance = 1e-3. Source: `docs/experiments/fear_hunger_v0.49.md` Results §"Per-arm paired_d (sign-aware) → Arm B".

Rationale: v0.51's B arm runs the same code path as v0.49's B arm (same V0_25 anchor, same founder-clamp-4 patch via `setup_observer`, same `streams.mutation` consumption order, no descendant listener on this arm). The cells must reproduce v0.49's values bytewise modulo float-arithmetic edge cases. A drift > 1e-3 indicates an implementation bug or an RNG-stream offset — most likely a misplaced listener wire-up that consumed bytes from `streams.mutation`.

### Outcome conditions (only consulted if no halt fires)

| priority | rollup verdict | (A_null, B_founder_clamp, C_lineage_clamp) sub-verdicts | locked phrase (verbatim) |
|---|---|---|---|
| 5 | `FOUNDER_CLAMP_REPRODUCED` | (A_NULL_BRIDGE_PRESENT, B_FOUNDER_CLAMP_LABEL_B_BRIDGE_NOT_FOUND, C_LINEAGE_CLAMP_LABEL_B_BRIDGE_NOT_FOUND) | "v0.51 reproduces v0.49's founder-clamp finding under both founder-only and lineage-wide `sensor_radius` clamps on the modern A_null corpus: the v0.48 spatial / foraging bridge does not fire under Label B in either arm, and clamping descendants in addition to founders does not change the verdict." |
| 6 | `LINEAGE_CLAMP_ADDITIONAL_WEAKENING` | (A_NULL_BRIDGE_PRESENT, B_FOUNDER_CLAMP_LABEL_B_BRIDGE_PRESENT, C_LINEAGE_CLAMP_LABEL_B_BRIDGE_NOT_FOUND) | "v0.51's lineage-wide `sensor_radius` clamp produces an additional weakening of the v0.48 spatial / foraging bridge beyond founder clamping alone on the modern A_null corpus: the bridge fires under founder-only clamp but does not fire under lineage-wide clamp." |
| 7 | `LINEAGE_CLAMP_NO_ADDITIONAL_WEAKENING` | (A_NULL_BRIDGE_PRESENT, B_FOUNDER_CLAMP_LABEL_B_BRIDGE_PRESENT, C_LINEAGE_CLAMP_LABEL_B_BRIDGE_PRESENT) | "v0.51's lineage-wide `sensor_radius` clamp produces no additional weakening of the v0.48 spatial / foraging bridge beyond founder clamping alone on the modern A_null corpus: the bridge fires under both founder-only and lineage-wide clamps." |
| 8 | `LINEAGE_DRIFT_MIXED` | A_NULL_BRIDGE_PRESENT and any other non-halt (B, C) sub-verdict combination | "v0.51's descendant-clamp arm shows mixed evidence on the modern A_null corpus; the locked categorical rules do not select a single outcome under the observed sub-verdict triple." |

The rollup is **categorical-only** — no magnitude-delta rule between B and C. Magnitude differences in B vs C signed_d cells are reported descriptively in Results but do not alter the verdict. Per the v0.51 handoff: this is a deliberate user-locked choice; report magnitude differences in Results without firing a verdict on them.

The rollup is **conservative**: locked phrases use "reproduces", "produces additional weakening", and "produces no additional weakening" — not "is causal for", "proves", or "rules out". Mechanism declarations require fresh-stream calibration analogous to v0.30..v0.33; v0.51 is a single-channel founder + descendant `sensor_radius` clamp and cannot rule out trait-covariance effects, founder-position confounds (already addressed by v0.50 but not eliminated), or non-V0_25-anchor effects.

## Cautious framing (per CLAUDE.md)

- "**Reproduces**", "**additional weakening**", "**no additional weakening**" — NOT "**proves**", "**causes**", or "**rules out**".
- "**Founder + descendant `sensor_radius` clamped**" — NOT "**no `sensor_radius` variation in the lineage**" (the mutation pipeline still draws variant values; the listener overwrites them).
- "**On the modern A_null corpus**" / "**under the locked V0_25 anchor**" — NOT a chamber-config-independent claim.
- v0.51 explicitly does not establish: cross-layout generalisation, mechanism (information vs cost), trait-covariance with non-`sensor_radius` fields, or post-tick-50 dominance dynamics.

## What v0.51 cannot establish (logged here pre-data, not retrofittable)

- ✗ **Mechanism**. v0.51 is single-channel: it varies *only* the `sensor_radius` field of body trait vectors (founders for B; founders + descendants for C). It does not separate "information radius" from "metabolic cost".
- ✗ **Trait-covariance closure**. v0.51 holds non-`sensor_radius` traits at the model's normal draw / mutation. If `sensor_radius` interacts non-trivially with another trait via reproduction inheritance, v0.51 cannot detect it. (v0.50's preflight showed pairwise |ρ| < 0.15 for founder traits, but that does not exclude descendant-time interactions.)
- ✗ **Generalisation beyond V0_25 / tight_gradient / 5 founders / height-6**. Layout, policy, reproduction config, and trait config are all V0_25 anchor.
- ✗ **Causality for post-tick-50 dominance**. v0.51 measures the v0.48 *bridge* (pre-50 spatial / foraging primaries vs Label B). It does not directly probe v0.46's b50-share dominance label.
- ✗ **Reachability of every locked outcome**. If B's Tier-2 re-anchor passes, B's sub-verdict is structurally pinned to v0.49's B sub-verdict (NOT_FOUND). Outcomes #6 (`LINEAGE_CLAMP_ADDITIONAL_WEAKENING`) and #7 (`LINEAGE_CLAMP_NO_ADDITIONAL_WEAKENING`) require B sub-verdict = PRESENT, which is incompatible with re-anchor success. They are locked here for outcome-space completeness; under correct implementation, the live verdict will be #5 `FOUNDER_CLAMP_REPRODUCED` if v0.49's NOT_FOUND result is real and reproducible. Outcome #6 / #7 firing without halt would itself be a finding — it would mean B drifted within tolerance from v0.49 numerically yet a sub-verdict boundary was crossed (a thresholding edge effect at +0.5 cohens d).

## Open framing (NOT in v0.51)

- v0.52 candidate: set `sensor_radius_metabolic_cost = 0` (decouple sensing radius from metabolic burden; isolate "information" from "cost").
- v0.53 candidate: cross-layout generalisation (v0.48–v0.51 on `widened_gradient` / `food_ladder`).
- Eventual fresh-stream calibration (v0.30-style) on the v0.46–v0.51 conclusion stack — needed for any "mechanism" declaration.

## Re-anchor (locked, A_null arm only, identical to v0.46–v0.50)

| version | published `a_share_h8` |
|---|---|
| v0.42 | 0.652 |
| v0.43R | NOT PUBLISHED (informational-only) |
| v0.44 | 0.878 |
| v0.45 | 0.818 |

B and C arms re-derive their own `a_share_h8` for descriptive logging; do NOT gate the verdict.

## Outputs (locked)

```
runs/v0.51-descendant-drift/per_run_per_lineage_v051.csv
  columns: arm, version, seed, hazard, run_id, lineage_id,
           founder_original_sensor_radius, founder_assigned_sensor_radius,
           founder_reproduction_drive, founder_metabolic_rate,
           pre50_food_events_count, pre50_food_energy_acquired,
           mean_distance_to_nearest_food_cell,
           tick50_living_count, tick50_above_threshold_count, tick50_above_threshold_fraction,
           b50_count, is_eventual_top_b50_label,
           is_high_sensor_radius_lineage, is_high_tick50_readiness_fraction_lineage,
           label_a_gating_valid, label_a_degenerate_reason

runs/v0.51-descendant-drift/per_run_child_audit.csv
  columns: arm, version, seed, hazard, run_id, tick, agent_id, lineage_id,
           child_original_sensor_radius, child_assigned_sensor_radius
  (arm in {C_lineage_clamp_4} only; A_null and B contribute zero rows)

runs/v0.51-descendant-drift/per_run_listener_counters.csv
  columns: arm, version, seed, hazard, run_id,
           n_births_seen, n_births_patched,
           n_births_already_sensor_radius_4, n_birth_patch_failures
  (arm in {C_lineage_clamp_4} only)

runs/v0.51-descendant-drift/audit_summary.csv
  columns: section, key, value
  sections:
    - reanchor_a_share_h8: per (arm, version, h=8) derived + (A_null only) published + drift_abs
    - bridge_reanchor: per (label, observable) v0.48 published signed_d + A_null derived signed_d + drift_abs
    - founder_clamp_reanchor: per (label, observable) v0.49 B published signed_d + v0.51 B derived signed_d + drift_abs
    - paired_d: per (arm, gating-label, observable) cell — paired_d, signed_d, n_runs, fires_expected, fires_wrong
    - paired_d_diagnostic: per (B, C, label_a, observable) cell — descriptive only
    - listener_aggregates: total per arm of n_births_seen / n_births_patched / n_births_already_sr4 / n_birth_patch_failures
    - sub_verdicts: per arm — sub-verdict + locked sub-phrase (where applicable)
    - rollup_verdict: locked rollup verdict + locked rollup phrase

runs/v0.51-descendant-drift/audit_log.txt
  human-readable echo with all locked phrases printed verbatim where they fire,
  plus the listener counter aggregate and the n_births distribution per arm.
```

## Implementation plan (locked)

1. Fresh script `scripts/v0_51_descendant_drift_audit.py`. CLI: `uv run python scripts/v0_51_descendant_drift_audit.py [--out-dir runs/v0.51-descendant-drift]`.
2. Per (version, seed, hazard) tuple, run **3 arms**. Every arm constructs `HHModel` via the normal A_null path (`FounderSpec(traits_override=None)`):
   - **A_null**: no patch, no listener.
   - **B_founder_clamp_4**: inside `setup_observer`, apply v0.49's founder-clamp patch verbatim. No listener.
   - **C_lineage_clamp_4**: inside `setup_observer`, apply the founder-clamp patch (verbatim from B), then register the `AgentBorn` listener (`weak=False` + closure capture in `disconnect_callbacks`). The listener single-channel-patches every newborn body's `traits.sensor_radius` to 4 before the newborn first steps; logs to `patch_counters` and `capture.child_audit_rows`.
3. For each arm-run, attach v0.48-style `setup_observer` + `tick_observer` (copy-local from v0.48 / v0.49 / v0.50). The `setup_observer` order is: (a) apply founder patch (B / C), (b) capture v0.51 founder audit table from live bodies, (c) capture tick-0 snapshot, (d) wire `AgentBorn` / `AteFood` / `HazardDamageApplied` listeners (filtered by `sender=model`), (e) for C only, wire the descendant-clamp listener (also `sender=model`).
4. Wrap `run_chamber(...)` in `try / finally`. On `finally`, iterate `disconnect_callbacks` and call each — guarantees no listener leak even on failure.
5. Aggregate per-lineage primaries identical to v0.48 / v0.49 / v0.50. Compute Label A and Label B per the arm's specific source (founder-original = founder-assigned for A_null; assigned = 4 for B and C). Under B and C, report Label A diagnostically with `label_a_gating_valid = False`.
6. Compute paired_d per (arm, gating-label, observable) cell. For B and C, also compute Label A diagnostic paired_d cells (CSV-reported, do NOT gate). Classify per-arm sub-verdicts under the gating rules above.
7. **Tier-1 bridge re-anchor** (priority 3): A_null arm's six cells vs v0.48 published; halt if drift > 1e-3 OR if A_null sub-verdict ≠ PRESENT.
8. **Tier-2 founder-clamp re-anchor** (priority 4): B arm's six cells vs v0.49 B published; halt if drift > 1e-3.
9. **Corpus re-anchor** (priority 1): A_null arm only; halt if `a_share_h8` for v0.42 / v0.44 / v0.45 drifts > 1e-3.
10. **Opposite-sign halt** (priority 2): scan all gating-label cells (Label A under A_null + Label B under all three); halt if any signed_d ≤ −0.5. Diagnostic-only Label A cells under B / C are excluded from the halt scan.
11. Compute slice rollup verdict per the locked priority order; print + write the locked phrase verbatim.

The reducer is fully self-contained: it reads no `runs/` artifacts. Wall time estimate: ~10 minutes for 192 runs (matches v0.49 / v0.50; the listener overhead is O(births per run) and births are bounded by the reproduction config).

Determinism guaranteed by passing each (version, seed) the same V0_25 anchor config; the listener does not consume any RNG, so A_null / B / C `streams.mutation` byte-identity at every founder spawn is structural by construction.

## Test list (locked, 16 tests; extends v0.46–v0.50 7-point review pattern)

`tests/test_v0_51_descendant_drift_audit.py`:

1. `test_all_arms_construct_founders_via_normal_a_null_path` — for every arm, `FounderSpec` is constructed with `traits_override=None`. The intervention lives in `setup_observer` (B, C) and in the `AgentBorn` listener (C only).
2. `test_b_founder_clamp_patch_replaces_only_sensor_radius_on_founder_bodies` — construct `HHModel` for a representative tuple; capture pre-patch founder body traits; apply the B-arm patch; assert every founder's `body.traits.sensor_radius == 4` and every other field byte-identical to pre-patch.
3. `test_c_founder_clamp_identical_to_b_for_founders` — construct two `HHModel` instances with the same (version, seed, hazard); apply B founder patch to one and C founder patch to the other; assert all 5 founders' bodies are byte-identical between the two models post-patch (the B and C founder paths are the same code).
4. `test_c_agent_born_listener_patches_newborn_via_synthetic_event` — register the C listener on a constructed `HHModel`; spawn a synthetic agent into `model.agents` with a non-4 `sensor_radius`; emit a synthetic `AgentBorn(agent_id=spawned, lineage_id=..., tick=...)` via `signal_for(AgentBorn).send(model, event=...)`; assert the spawned agent's `body.traits.sensor_radius == 4` post-emit and every other body trait field is byte-identical to pre-emit.
5. `test_c_listener_single_channel_invariant_on_child_patches` — register the C listener on a constructed `HHModel`; spawn a synthetic agent whose traits would, after `dataclasses.replace(..., sensor_radius=4)`, also flip a different field (simulated by monkey-patching `dataclasses.replace` for the test); assert `V051ReducerError` raised loud and `n_birth_patch_failures` increments.
6. `test_c_listener_strong_reference_via_weak_false_and_disconnect_callbacks` — construct `HHModel`; register listener with `weak=False`; drop the local Python reference to `_on_agent_born`; force a Python GC cycle; emit a synthetic `AgentBorn`; assert the listener still fires (verifies `weak=False` is honoured and the closure-capture-in-`disconnect_callbacks` belt-and-braces works).
7. `test_c_listener_disconnects_in_finally_on_run_failure` — wrap `run_chamber(...)` in `try / finally` and force the run to raise inside the chamber loop (e.g., monkey-patch a step to raise); assert the disconnect callback runs (verified by emitting a post-finally synthetic `AgentBorn` and confirming no patch occurs / no exception from a stale handler).
8. `test_c_descendant_patch_counters_increment_correctly` — synthetic A_null run with stub births at: (a) child with `sensor_radius=2` → `n_births_seen += 1`, `n_births_patched += 1`, `n_births_already_sensor_radius_4 += 0`; (b) child with `sensor_radius=4` → `n_births_seen += 1`, `n_births_patched += 1`, `n_births_already_sensor_radius_4 += 1` (no-op patch but counted as patched); (c) failed lookup → `n_birth_patch_failures += 1`. Assert counter values after each scenario.
9. `test_v051_audit_uses_live_bodies_not_trait_fingerprints` — grep test on `scripts/v0_51_descendant_drift_audit.py` source: assert the file contains zero references to `model.trait_fingerprints` or `trait_fingerprints` (the audit must use live `model.agents` only). Belt-and-braces: also test that with a synthetic model where `model.trait_fingerprints` is set to an obviously-wrong sentinel, the v0.51 founder + child audit tables do not contain the sentinel.
10. `test_streams_mutation_state_byte_identical_across_arms_at_setup_observer_end` — for the same (version, seed, hazard), construct three `HHModel` instances; record `streams.mutation` state via a deterministic 8-draw probe at the end of `setup_observer` for each arm (after founder patch + listener wire-up for C); assert the next 8 draws are byte-identical across A_null, B, and C. Verifies the listener does not consume RNG.
11. `test_label_a_diagnostic_only_under_b_and_c` — synthetic per-lineage rows for arm B and arm C; assert `label_a_gating_valid == False`, `label_a_degenerate_reason == "all founders assigned sensor_radius=4"`, and that Label A's paired_d cells do NOT feed B's or C's sub-verdict (gating uses Label B only).
12. `test_per_arm_subverdict_a_null_present_requires_both_labels_clear` — synthetic A_null paired_d such that Label A is (+0.6, +0.7, −0.3) and Label B is (+0.6, +0.8, −0.2); assert sub-verdict = `A_NULL_BRIDGE_PRESENT`. Also test that (Label A 1/3, Label B 2/3) → `A_NULL_BRIDGE_PARTIAL`.
13. `test_rollup_founder_clamp_reproduced_when_present_notfound_notfound` — synthetic (A_NULL_BRIDGE_PRESENT, B_FOUNDER_CLAMP_LABEL_B_BRIDGE_NOT_FOUND, C_LINEAGE_CLAMP_LABEL_B_BRIDGE_NOT_FOUND); assert rollup = `FOUNDER_CLAMP_REPRODUCED`.
14. `test_rollup_lineage_clamp_additional_weakening_when_present_present_notfound` — synthetic (A_NULL_BRIDGE_PRESENT, B_FOUNDER_CLAMP_LABEL_B_BRIDGE_PRESENT, C_LINEAGE_CLAMP_LABEL_B_BRIDGE_NOT_FOUND); assert rollup = `LINEAGE_CLAMP_ADDITIONAL_WEAKENING`. Also assert `LINEAGE_CLAMP_NO_ADDITIONAL_WEAKENING` fires for (PRESENT, PRESENT, PRESENT) and `LINEAGE_DRIFT_MIXED` fires for (PRESENT, NOT_FOUND, PRESENT).
15. `test_founder_clamp_replication_halt_priority_over_outcome` — synthesise B-arm signed_d cells where one cell drifts +1.5 from v0.49's B published value; assert `FOUNDER_CLAMP_REPLICATION_HALT` raised loud (priority 4) and the outcome verdicts are not consulted.
16. `test_priority_partition_total` — exhaustively iterate the 27 (B sub-verdict ∈ {PRESENT, NOT_FOUND, UNREACHABLE}, C sub-verdict ∈ {PRESENT, NOT_FOUND, UNREACHABLE}, halts ∈ {none, drift, opposite_sign, bridge, founder_clamp}) combinations under A_null PRESENT; assert each maps to exactly one rollup outcome via the priority order. Also assert that when a halt fires, no outcome verdict is consulted (the halt phrase replaces the rollup phrase).

## Watch-outs (for future-Chronus)

- **Listener strong-reference**: connect with `weak=False` AND keep the closure in `disconnect_callbacks`. Both protections; either alone is sufficient on current blinker but the redundancy is cheap insurance. Documented in pre-implementation correction.
- **Listener disconnect in `finally`**: per-run scope, not module scope. A failed run must not leak its `sender=model`-scoped listener into a later run's `HHModel`. Test #7 enforces.
- **`AgentBorn` event has only `agent_id`** — no trait fields, no body reference. The listener must scan `model.agents` to find the body by id. With 5 founders + small descendant counts at pre-50, this is O(births × population) per run, negligible at this corpus scale.
- **`model.trait_fingerprints` records pre-patch.** v0.51's audit tables must NOT consume `model.trait_fingerprints` — they would observe pre-patch values (which differ from the patched values for descendants under arm C). Use live bodies + v0.51's own audit rows only. Test #9 enforces. This is a "audit-truth" issue, not a behavioral one.
- **Single-channel invariant must halt loud** on any non-`sensor_radius` field difference between original and assigned trait vectors. Applied to BOTH founder patches (B, C) and child patches (C). Guards against `dataclasses.replace` semantics drift if a future Traits field is added and not preserved.
- **No-op patches are valid.** A child whose mutated `sensor_radius` is already 4 is a legitimate no-op — the listener still runs the `dataclasses.replace(...)` write (which produces an identical object) and the single-channel invariant still passes. `n_births_already_sensor_radius_4` counts these for transparency. The expected fraction at V0_25 trait config is 1/6 ≈ 0.167.
- **Pre-50 byte-identity** vs v0.48 holds for A_null only. B and C diverge at tick 0 (founder bodies have `sensor_radius=4`); C additionally diverges from B at every newborn's first step. Tier-1 (vs v0.48) anchors A_null; Tier-2 (vs v0.49) anchors B. C has no published reference to anchor against — it's the new measurement.
- **B arm should reproduce v0.49 byte-identically.** The B path is v0.49's B path verbatim — same `setup_observer` body patch, same RNG consumption, same downstream simulation. Tier-2 enforces drift ≤ 1e-3.
- **Outcomes #6 and #7 are unreachable under correct implementation** if v0.49's B-arm NOT_FOUND verdict is real and reproducible. They are locked for outcome-space completeness; in practice the live verdict is expected to be #5 `FOUNDER_CLAMP_REPRODUCED`. If #6 or #7 fires without a halt, it indicates a thresholding edge effect at the +0.5 boundary on B's Label B paired_d cells — log as a finding in Results.
- **Label A is diagnostic-only under both B and C.** Five-way tie under min(lineage_id) tiebreak → always lineage 0. Reported in CSV with `label_a_gating_valid = False` but does NOT trigger `INTERVENTION_OPPOSITE_SIGN_HALT` even at large negative signed_d (e.g., v0.49's −0.732 on `mean_distance_to_nearest_food_cell` under B Label A). Test #11 enforces.
- **Determinism north star** ([[scripts/core_smoke_test.py]]) must continue to pass; v0.51 makes no `src/` change so this is preserved by construction.
- **All five prior intervention paths** (v0.42, v0.43R, v0.44, v0.45, v0.49, v0.50) plus the post-hoc reducers (v0.34, v0.35, v0.36, v0.46, v0.47, v0.48) remain dispatchable on main. v0.49's reducer in particular must remain byte-identical to its merged form — v0.51 does NOT modify it.
- **Locked phrase discipline:** all sub-verdict and rollup locked phrases fire verbatim where the verdict fires. No paraphrase.

## Files this slice will create

- `docs/experiments/fear_hunger_v0.51.md` (this file; Results section appended after reducer run)
- `scripts/v0_51_descendant_drift_audit.py`
- `tests/test_v0_51_descendant_drift_audit.py`

No other files modified.

## Results

**Status:** pending reducer run.
