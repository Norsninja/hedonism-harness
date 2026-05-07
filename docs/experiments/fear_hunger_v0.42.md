# v0.42 — leader-lineage hard-kill intervention (first causal slice)

**Status:** pre-registered 2026-05-07; sweep + intervention module +
audit not yet executed.
**Date:** 2026-05-07
**Branch:** `claude/v0.42-leader-kill-intervention`
**Predecessors:** v0.21..v0.27 (aggregate-optimum audit, closed),
v0.28..v0.33 (calibration arc, closed by v0.33 H6_pool WEAK), v0.34
(lineage observability MVP — H7 mostly-concentrated;
`mean_top_lineage_b50_share` pooled 0.635 → 0.785), v0.35 (founder-
survival timing — **H6 EXPANSION-SUPPORTED**; pooled `wad_rate`
0.458 → 0.792), v0.36 (founder-trait heritability —
**H6 TRAIT-LINKED-FLAT**), v0.37 (dominance timing decomposition —
**H6 STABLER-EARLY-LEADERSHIP**), v0.38 (leader post-50 advantage —
**H5 LEADER-ADVANTAGE-AMPLIFIED**; pooled 3.948 → 8.990), v0.39
(fresh-stream calibration of v0.38 — **H5_POOLED_ONLY**), v0.40
(cross-stream stability audit — **H5 STREAM-STABLE** on 3 of 4
streams), v0.41 (second fresh-stream calibration —
**v0.41_OLD_LIKE + H5_STREAM_STABLE_N5** on 4 of 5 streams; v0.39
reframed as one-off n=8 noise excursion).
**Spec:** [[docs/specs/v0.2_reflex_cell_spec.md]] §"Comparison framework".

## Question

v0.34..v0.41 established that **post-50 lineage dominance correlates
with hazard pressure** across 4 of 5 seed streams under the locked
M1/M2/M3 family (top_lineage_b50_share, wad_rate, leader_advantage).
The v0.41 manifest's strategic state names mechanism as the
**only remaining science move that crosses the causal boundary**.

The v0.34..v0.41 reducers cannot test mechanism because every
event-stream they consume was produced under the unmodified policy
+ chamber. To test mechanism we must **intervene** on the system
state and observe whether the post-50 dominance pattern collapses,
relocates, or persists.

The active question for v0.42 is:

> **Is the tick-50 leader lineage NECESSARY for the post-50 dominance
> pattern? If we extinct the leader lineage at the tick-50/tick-51
> boundary, does post-50 dominance fail to reconstitute among the
> surviving lineages, or does it simply transfer to a new dominant
> lineage?**

This is a **necessity probe**, not a biological-realism intervention.
Hard kill is the cleanest causal perturbation; if a lineage's
identity at tick 50 carries the mechanism, removing the lineage
should leave the surviving population unable to produce a post-50
dominance pattern of comparable concentration. If post-50 dominance
re-emerges from a different lineage at comparable concentration, the
"leader-identity" framing is mechanistically weak — the pattern is
likely a property of the substrate (any large lineage post-50
expands), not of the specific leader.

This is the **first sim-mechanics change** in the science arc since
v0.27. v0.34..v0.41 maintained zero `src/` modifications by design
(post-hoc reducer discipline). v0.42 explicitly breaks that
discipline because no reducer can recover an intervention from
existing artifacts.

## What this slice tests, and what it does NOT test

### Tests

- Whether **`post_intervention_top_lineage_b50_share`** in the
  hard-kill arm B drops by ≥ 0.15 relative to the null arm A at
  h=8, AND the size-matched control arm C remains within ±0.10 of
  arm A at h=8. **This is the primary mechanism necessity test.**
- Whether the B-vs-A reduction is larger at h=8 than at h=0
  (secondary observable; tests hazard-amplification specificity of
  the necessity effect).
- Whether the intervention's `LineageKilledByIntervention` summary
  events are emitted exactly once per intervention-firing run, with
  the correct `lineage_role` and `lineage_id` fields.
- Whether the intervention's `AgentDied(cause="intervention_killed")`
  events conserve pool residual and total-agent invariants normally.
- Whether the **default-None intervention path** (i.e., legacy
  arm A_null configuration) produces output **byte-identical** to
  what the v0.41 sweep produces on the same seeds + parameters,
  preserving the v0.21..v0.41 determinism contract.

### Does NOT test

- **Mechanism sufficiency.** This slice tests necessity only. Even
  if B fully collapses and C does not, we cannot conclude that
  leader identity is sufficient to produce dominance — only that
  it is necessary under the tested substrate. Sufficiency requires
  a separate intervention (e.g., injecting an artificial leader at
  a non-canonical lineage; deferred indefinitely).
- **Mechanism specificity** (which property of the leader carries
  the effect). v0.42 cannot distinguish reproductive priority,
  spatial position, energy stockpile, founder traits, local food
  control, or descendants-already-distributed-on-map. Birth-
  suppression / energy-drain / spatial-relocation interventions
  are reserved for v0.43+ conditional on v0.42 firing.
- **Hazard generalisation.** Only h=0 and h=8 are tested. h=4 and
  h=12 are reserved for v0.43+ if the v0.42 result motivates
  hazard-grid expansion.
- **Cross-stream calibration of the intervention.** v0.42 runs only
  seeds 41..48 (one stream). If v0.42 fires, calibrating on a
  second seed stream is a v0.43+ candidate.
- **The v0.34..v0.41 corpus.** The five-stream corpus is sealed and
  unchanged. v0.42 does NOT re-run any prior reducer.
- **Magnitude framing as "spread" or "amplification".** v0.42's
  primary uses absolute-share differences at h=8, NOT a hazard-
  axis spread (mean(h=12) − mean(h=0)) like v0.34..v0.41 used.
  The secondary explicitly compares B-vs-A reductions across h=0
  and h=8 instead.

### Deferred (v0.43+ candidates, conditional on v0.42 outcome)

- **If MECHANISM_NECESSITY_SUPPORTED fires** (B collapses; C does
  not). v0.43 candidates re-open: (a) hazard-grid expansion
  (h ∈ {4, 12}); (b) intervention-type refinement (birth-
  suppression, energy-drain) to identify which property of the
  leader carries the effect; (c) sufficiency probe (inject
  artificial leader); (d) cross-stream calibration on a second
  seed band.
- **If MECHANISM_GENERAL_DISRUPTION fires** (both B and C collapse;
  any large-lineage removal disrupts the pattern). v0.43 candidate:
  refine the intervention to test whether tick-50-leader identity
  is distinguishable from generic biomass shock at all (e.g., kill
  random non-leader vs. kill smaller non-leader; spread across
  size buckets). Mechanism is "size-dependent system fragility,"
  not "leader-specific."
- **If MECHANISM_NOT_NECESSARY fires** (neither B nor C collapses;
  the system reconstitutes dominance regardless). v0.43 candidate:
  ask whether the post-50 dominance pattern is produced by a
  property-of-the-substrate (e.g., resource concentration, hazard-
  driven niche separation) rather than lineage-level dynamics at
  all. Mechanism work pivots to substrate-level.
- **If MECHANISM_INDETERMINATE fires** (B or C lands in the gap
  between locked thresholds). v0.43 candidate: increase n per arm
  (e.g., 16 seeds instead of 8) to tighten the noise floor.

### Quarantined (not v0.42 inputs)

- v0.34..v0.41 reducer outputs. These remain on disk but are not
  re-read by v0.42's audit. v0.42's primary observable is computed
  from v0.42's own sweep events.jsonl.
- HedonismPolicy comparisons. Deferred indefinitely.
- Mesa migration. Closed indefinitely.
- v0.36 founder-trait observables. Orthogonal.

## Conservation framing — first `src/` modification since v0.27

v0.42 modifies `src/` for the first time in the v0.34..v0.42 arc.
Specifically, the following ARE modified:

- **New module:** `src/hedonism_harness/core/interventions.py`
  - `InterventionConfig` (frozen dataclass; intervention type +
    parameters).
  - `InterventionResult` (frozen dataclass; what fired, on which
    lineage, n_killed, etc.).
  - `Tick50LineageKillIntervention` (the only intervention class
    v0.42 ships).
- **New event types:** added to the central event spec.
  - `LineageKilledByIntervention(lineage_id, n_killed,
    lineage_role, intervention_tick, effective_tick)`.
  - Killed agents emit existing `AgentDied(cause="intervention_killed")`
    using the existing event constructor; the new cause string is
    additive.
- **One hook** in `src/hedonism_harness/core/world.py` (or the
  chamber runner — exact site chosen at implementation time):
  `optional_intervention: InterventionConfig | None = None`. When
  None, the path is byte-identical to pre-v0.42 behaviour. When
  set, the intervention fires at the tick-50/tick-51 boundary
  (after tick 50's update closes, before tick 51 begins).

The following are NOT modified:

- Existing chamber, policy, or population-dynamics behaviour outside
  the intervention hook. Default `optional_intervention=None`
  preserves byte-identity on all v0.21..v0.41 sweeps.
- `src/hedonism_harness/policies/gradient_policy.py`,
  `src/hedonism_harness/policies/hedonism_policy.py`. No policy
  changes.
- `src/hedonism_harness/experiments/comparison_grid.py` arm tuples
  (V0_25_ARMS, V0_27_ARMS, V0_31_TIGHT_W_ARMS, V0_32_TIGHT_H_ARMS,
  V0_33_TIGHT_H_ARMS, V0_39_TIGHT_H_ARMS, V0_41_TIGHT_H_ARMS). One
  new constant `V0_42_INTERVENTION_ARMS` is added (additive only).
- All v0.34..v0.41 reducer scripts and audit. Byte-identical before
  and after v0.42.
- Pre-v0.42 events on disk. Re-running prior sweeps with default
  `optional_intervention=None` produces byte-identical events.jsonl
  files (this is a regression-guarded invariant).

## Mechanism

v0.42 ships:

1. The intervention module + hook (`src/`).
2. A new sweep driver and arm tuple.
3. A v0.42 audit reducer that consumes the v0.42 sweep events.
4. Paired test files for each new module.
5. This pre-reg.
6. A new manifest doc post-Results.

### 1. Intervention module (`src/hedonism_harness/core/interventions.py`)

```python
@dataclass(frozen=True)
class InterventionConfig:
    kind: Literal["null", "kill_tick50_leader", "kill_size_matched_nonleader"]
    intervention_tick: int = 50  # tick AT WHICH leader is identified
    effective_tick: int = 51     # tick BEFORE WHICH agents are killed
    # Future: add `kind` variants here for v0.43+ (birth-suppression,
    # energy-drain, etc.) without touching this file's existing logic.

@dataclass(frozen=True)
class InterventionResult:
    fired: bool
    lineage_id: int | None
    lineage_role: Literal["leader", "size_matched_nonleader", "none"]
    n_killed: int
    control_unavailable: bool  # True if kind=kill_size_matched_nonleader
                                # and no non-leader lineage exists at tick 50

class Tick50LineageKillIntervention:
    """Fires once at the tick-50/tick-51 boundary on a chamber world.
    Identifies leader (or size-matched non-leader) from tick 50 living-agent
    counts; kills all agents of the chosen lineage; emits the summary event.
    """
```

Selection rules:

- **`leader`**: at tick 50 close, the lineage with the most living
  agents. Tie-break: lowest `lineage_id` (mirrors v0.35/v0.37/v0.38
  convention).
- **`size_matched_nonleader`**: at tick 50 close, among all
  non-leader lineages with ≥ 1 living agent, choose the one whose
  living-agent count is **closest** to the leader's. Tie-break:
  lowest `lineage_id`. If no non-leader lineage has any living
  agents, set `control_unavailable=True` and **do not kill**;
  subsequent ticks proceed unmodified.

Determinism contract:

- Selection is a pure function of tick-50 living-agent state, which
  is itself deterministic given the seed. No new RNG is introduced.
- For a given (seed, hazard, intervention_kind), the intervention
  fires on the same lineage_id every time (or `control_unavailable`
  fires every time).

### 2. World hook (`src/hedonism_harness/core/world.py`)

A single new optional parameter on the run-orchestration entry point:

```python
def run_world(
    ...,
    optional_intervention: InterventionConfig | None = None,
) -> ...:
    # Existing tick loop, unchanged when optional_intervention is None.
    # When set, AFTER tick 50's complete update closes (after pool
    # influx, after deaths, after births, after manifest snapshot),
    # AND BEFORE tick 51's first state mutation, run:
    #     intervention_result = apply_intervention(world, optional_intervention)
    #     emit LineageKilledByIntervention(...) into events.jsonl
    #     for each killed agent: emit AgentDied(cause="intervention_killed")
    # Then continue tick 51 normally.
```

Default `None` path is byte-identical to pre-v0.42. **An additive
regression test re-runs a v0.41 seed and asserts events.jsonl bytes
match a sealed v0.41 reference.**

### 3. Sweep + arm tuple (`scripts/v0.42_sweep.py`,
   `src/hedonism_harness/experiments/comparison_grid.py` additions)

Three arms × 2 hazards × 8 seeds = **48 runs**. Arm tuple:

```python
V0_42_INTERVENTION_ARMS: tuple[Arm, ...] = (
    # A_null: no intervention (mirror v0.41 substrate at h=0, h=8 only)
    Arm(label="v042-A_null-hzd0-influx-1.0",  hazard_damage=0.0, ..., intervention_kind="null"),
    Arm(label="v042-A_null-hzd8-influx-1.0",  hazard_damage=8.0, ..., intervention_kind="null"),
    # B_kill_tick50_leader
    Arm(label="v042-B_kill_leader-hzd0-influx-1.0",  hazard_damage=0.0, ..., intervention_kind="kill_tick50_leader"),
    Arm(label="v042-B_kill_leader-hzd8-influx-1.0",  hazard_damage=8.0, ..., intervention_kind="kill_tick50_leader"),
    # C_kill_size_matched_nonleader
    Arm(label="v042-C_kill_smnonleader-hzd0-influx-1.0", hazard_damage=0.0, ..., intervention_kind="kill_size_matched_nonleader"),
    Arm(label="v042-C_kill_smnonleader-hzd8-influx-1.0", hazard_damage=8.0, ..., intervention_kind="kill_size_matched_nonleader"),
)
```

Seeds: 41..48. All other substrate fields (chamber=tight_gradient,
ambient_influx_rate=1.0, n_ticks=200, n_founders=5) inherited from
v0.41 unchanged.

The Arm dataclass gets one additive field `intervention_kind` (or
the chamber-runner reads it from arm metadata; exact wiring chosen
at implementation time). Default value preserves byte-identity for
all v0.21..v0.41 arms.

### 4. v0.42 audit (`scripts/v0_42_intervention_audit.py`)

Imports only `LineageReplayError` via `importlib.util` (project
standard halt class). Otherwise pure stdlib + `csv.DictReader` /
`json.loads`.

Reads:

- Per-arm `comparison.csv` files from `runs/fear-hunger-v0.42-tight_gradient/arms/`.
- Per-run `events.jsonl` files (specifically: `LineageKilledByIntervention`
  events + post-50 `AgentBorn` events to compute the primary observable).

Halt invariants (5):

- **H2a (run count):** exactly 6 arms × 8 seeds = 48 runs on disk.
- **H2b (intervention-fire count per arm):**
  - A_null arms: 0 `LineageKilledByIntervention` events per run.
  - B_kill_leader arms: exactly 1 event per run with
    `lineage_role="leader"`.
  - C_kill_smnonleader arms: exactly 0 or 1 event per run with
    `lineage_role="size_matched_nonleader"`. (0 means
    `control_unavailable`.)
- **H2c (effective_tick):** every fired intervention has
  `effective_tick=51`.
- **H2d (intervention conservation):** for every B/C run that
  fired, the count of `AgentDied(cause="intervention_killed")` at
  tick 51 equals the `n_killed` field on the
  `LineageKilledByIntervention` event.
- **H2e (regression):** A_null with optional_intervention=null
  produces events.jsonl byte-identical to v0.41 seed (sampled on
  one specific seed; sealed reference fingerprint stored in audit
  module).

Computes per-(arm, seed):

- `post_intervention_top_lineage_b50_share` =
  count_of_post_50_AgentBorn(top_surviving_lineage) /
  count_of_post_50_AgentBorn(all_surviving_lineages).
  Where "top surviving lineage" = the surviving lineage with the
  most post-50 births; if tie, lowest lineage_id. "Surviving" =
  lineage_id that is NOT in {killed_lineage_id} for this run.
  For A_null runs, no exclusion (5-lineage pool). For B and C,
  4-lineage pool (or 5-lineage if `control_unavailable=True`,
  in which case the run is excluded from C's primary aggregation
  and counted only in `c_control_unavailable_count`).
- `total_post_50_births` (for context).
- `n_killed` and `lineage_role` (from event).

Aggregates per-(arm, hazard) and computes the locked decision rule.

Outputs eight CSVs under `runs/lineage-v0.42/`:

- `per_run.csv` — 48 rows: arm, hazard, seed, fired, lineage_id,
  lineage_role, n_killed, control_unavailable, total_post_50_births,
  top_lineage_post50_births, post_intervention_top_lineage_b50_share.
- `per_arm_per_hazard.csv` — 6 rows: arm, hazard, n_runs,
  n_fired, n_control_unavailable, mean_share, median_share.
- `intervention_summary.csv` — 6 rows: arm, hazard,
  mean_post_intervention_top_lineage_b50_share, n_runs_used.
- `primary_test.csv` — 1 row: a_share_h8, b_share_h8, c_share_h8,
  delta_b_minus_a_h8, delta_c_minus_a_h8, b_passes (b−a ≤ −0.15),
  c_passes (|c−a| ≤ 0.10), primary_fires (both pass).
- `secondary_test.csv` — 1 row: delta_b_minus_a_h0, delta_b_minus_a_h8,
  hazard_amplified (|delta_h8| > |delta_h0|), secondary_fires.
- `verdict.csv` — 1 row: verdict, locked_phrase, primary_fires,
  secondary_fires.
- `c_control_availability.csv` — 1 row: n_runs_total_C,
  n_control_unavailable, availability_rate.
- `byte_identity_anchor.csv` — 1 row: regression-guard sample seed,
  expected fingerprint, observed fingerprint, anchor_ok.

### Locked constants

```python
EXPECTED_HAZARDS: tuple[int, ...] = (0, 8)
EXPECTED_SEEDS: tuple[int, ...] = tuple(range(41, 49))  # 41..48
EXPECTED_N_FOUNDERS: int = 5
EXPECTED_N_TICKS: int = 200
EXPECTED_INTERVENTION_TICK: int = 50
EXPECTED_EFFECTIVE_TICK: int = 51
EXPECTED_RUNS_TOTAL: int = 48  # 6 arms × 8 seeds

# Locked thresholds (item 1 of v0.42 sign-off)
PRIMARY_B_REDUCTION_THRESHOLD: float = 0.15  # B share <= A share - 0.15
PRIMARY_C_TOLERANCE: float = 0.10            # |C share - A share| <= 0.10

# Arm labels
ARM_A_NULL: str = "v042-A_null"
ARM_B_KILL_LEADER: str = "v042-B_kill_leader"
ARM_C_KILL_SMNONLEADER: str = "v042-C_kill_smnonleader"

# Intervention kind labels
KIND_NULL: str = "null"
KIND_KILL_LEADER: str = "kill_tick50_leader"
KIND_KILL_SMNONLEADER: str = "kill_size_matched_nonleader"

# Lineage role labels
ROLE_LEADER: str = "leader"
ROLE_SMNONLEADER: str = "size_matched_nonleader"
ROLE_NONE: str = "none"
```

### Determinism — anchors

- v0.21..v0.41 events.jsonl + sidecar artifacts on disk are not
  re-read by the audit. The audit reads ONLY v0.42's own sweep
  output.
- v0.21..v0.41 test suites continue to pass (additive guard).
- Default `optional_intervention=None` is byte-identical to
  pre-v0.42 behaviour — re-running any pre-v0.42 sweep produces
  byte-identical events.jsonl files (regression test).
- All v0.34..v0.41 reducer modules are imported only insofar as the
  v0.42 audit needs `LineageReplayError`. **No mutation of any
  pre-v0.42 module.**

### Wall-time estimate

- v0.42 sweep: ~12s (2 hazards × 3 arms × 8 seeds = 48 runs at
  locked parameters; comparable to v0.41's 32-run sweep at ~10s).
- v0.42 audit: ~3s on the 48-row aggregate plus events.jsonl
  parsing for the 48 runs.
- **Total v0.42 incremental wall-time:** ~15s.

## Observables — pre-committed before reading the data

### Per-run — 48 rows total

- `arm` ∈ {A_null, B_kill_leader, C_kill_smnonleader}.
- `hazard` ∈ {0, 8}.
- `seed` ∈ {41..48}.
- `fired`: bool. True iff the intervention (B or C) fired and an
  agent kill occurred. False for A_null, and for C runs where
  `control_unavailable=True`.
- `lineage_id`: int | None. The killed lineage's id (or None for
  A_null / control_unavailable).
- `lineage_role`: "leader" | "size_matched_nonleader" | "none".
- `n_killed`: int. Count of agents killed at tick 51 by this
  intervention.
- `control_unavailable`: bool. True iff arm == C and no non-leader
  lineage existed at tick 50.
- `total_post_50_births`: int. Count of `AgentBorn` events with
  `tick > 50` in this run.
- `top_lineage_post50_births`: int. Among lineages NOT killed by
  the intervention, the count of post-50 births of the lineage
  that has the most.
- `post_intervention_top_lineage_b50_share`: float in [0, 1].
  `top_lineage_post50_births / total_post_50_births_among_surviving_lineages`.
  NaN if `total_post_50_births_among_surviving_lineages == 0` (run
  excluded from arm aggregation; counted as `n_excluded`).

### Per-(arm, hazard) — 6 rows total

- `mean_post_intervention_top_lineage_b50_share` over the 8 runs
  in the bucket, excluding NaN runs and `control_unavailable`
  runs.
- `n_runs_used`: number of runs contributing to the mean.
- `n_excluded`: NaN excluded.
- `n_control_unavailable`: only relevant for arm C.

### Primary test (`primary_test.csv` — 1 row)

- `a_share_h8`, `b_share_h8`, `c_share_h8`.
- `delta_b_minus_a_h8 := b_share_h8 - a_share_h8`.
- `delta_c_minus_a_h8 := c_share_h8 - a_share_h8`.
- `b_passes := delta_b_minus_a_h8 <= -PRIMARY_B_REDUCTION_THRESHOLD`
  (i.e., B share is at least 0.15 BELOW A share).
- `c_passes := abs(delta_c_minus_a_h8) <= PRIMARY_C_TOLERANCE`
  (i.e., C share is within ±0.10 of A share).
- `primary_fires := b_passes AND c_passes`.

### Secondary test (`secondary_test.csv` — 1 row)

- `delta_b_minus_a_h0`, `delta_b_minus_a_h8`.
- `hazard_amplified := abs(delta_b_minus_a_h8) > abs(delta_b_minus_a_h0)`.
- `secondary_fires := primary_fires AND hazard_amplified`.

## Pre-registered hypotheses

### Strong form (substrate identity + invariants)

- **H1 (additive `src/` modification).** Only the new intervention
  module + one optional hook in `world.py` (or chamber runner).
  All pre-v0.42 default-None paths are byte-identical. **Includes
  a regression test on a sampled v0.41 seed.**
- **H2a (run count).** Exactly 48 runs on disk after v0.42 sweep.
- **H2b (intervention-fire count per arm).** A_null: 0 fires per
  run. B: exactly 1 leader-role fire per run. C: 0 or 1
  smnonleader-role fire per run (0 only iff `control_unavailable`).
- **H2c (effective_tick).** Every `LineageKilledByIntervention`
  event has `effective_tick=51`.
- **H2d (intervention conservation).** For B/C runs that fired,
  count of `AgentDied(cause="intervention_killed")` at tick 51
  equals `n_killed` on the summary event. Pool residual conserved
  via existing semantics.
- **H2e (regression byte-identity).** Sampled v0.41 seed re-run
  with `optional_intervention=None` produces events.jsonl
  byte-identical to sealed v0.41 reference. Halt if fingerprint
  drifts.
- **H3 (additive guard).** v0.21..v0.41 prior tests still pass
  after v0.42 additions.
- **H4 (no mutation of pre-v0.42 surface).** All
  `scripts/v0.NN_*.py`, `scripts/lineage_replay.py`,
  `scripts/lineage_survival_replay.py`, `scripts/trait_replay.py`,
  `scripts/lock_in_timing_replay.py`,
  `scripts/leader_advantage_replay.py`,
  `scripts/lineage_replay_v0_39_extension.py`,
  `scripts/lineage_survival_replay_v0_39_extension.py`,
  `scripts/v0_39_leader_advantage_fresh_replay.py`,
  `scripts/v0_40_stream_stability_audit.py`,
  `scripts/lineage_replay_v0_41_extension.py`,
  `scripts/lineage_survival_replay_v0_41_extension.py`,
  `scripts/leader_advantage_replay_v0_41_extension.py`,
  `scripts/v0_41_stream_classification_audit.py`,
  pre-v0.42 arm tuples in
  [[src/hedonism_harness/experiments/comparison_grid.py]],
  chamber / population / policy modules — byte-identical before
  and after v0.42 (modulo the additive intervention hook + arm
  field).

### Cautious form — three-way verdict on v0.42's necessity question

The verdict is intentionally three-way (mutually exclusive by
construction):

**MECHANISM_NECESSITY_SUPPORTED.** **FIRES iff** `primary_fires ==
True` (i.e., B share ≤ A share − 0.15 at h=8, AND |C share − A
share| ≤ 0.10 at h=8). Headline: removing the tick-50 leader
lineage materially disrupts post-50 dominance, while removing a
size-matched non-leader does not. The tick-50 leader's identity is
**necessary** for the post-50 dominance pattern under the tested
substrate.

**MECHANISM_GENERAL_DISRUPTION.** **FIRES iff** B share ≤ A share −
0.15 at h=8 AND C share also drops by ≥ 0.15 (|C share − A share| >
0.10 AND C share ≤ A share − 0.10 — the C-collapse cell). Headline:
both the leader and a size-matched non-leader removal disrupt
post-50 dominance. The pattern is **size-shock-sensitive**; tick-50
leader identity is not separable from generic large-lineage shock.

**MECHANISM_NOT_NECESSARY.** **FIRES iff** B share > A share − 0.15
at h=8. Headline: removing the leader does not materially disrupt
post-50 dominance; some surviving lineage reconstitutes the
pattern. The tick-50 leader's identity is **not necessary**;
post-50 dominance is a property of the substrate (or of any
sufficiently large surviving lineage), not of leader identity.

(All three exhaust the cell space. Any other arrangement collapses
into one of the three above by the locked rules: e.g.,
"B share is above A share − 0.15" forces MECHANISM_NOT_NECESSARY
regardless of C; "B drops AND C also drops" forces
MECHANISM_GENERAL_DISRUPTION.)

### Locked phrases for each verdict

> **MECHANISM_NECESSITY_SUPPORTED phrase:** "Hard-killing the
> tick-50 leader lineage at the tick-50/tick-51 boundary materially
> disrupts the post-50 dominance pattern at h=8: the surviving four
> lineages do not reconstitute concentration of comparable share.
> The size-matched non-leader control does not produce the same
> disruption. Under the tested substrate, the tick-50 leader's
> identity is **necessary** for the v0.34..v0.41 dominance pattern.
> v0.42 does not declare a specific mechanism (reproductive
> priority, spatial position, energy stockpile, founder traits, or
> local food control); refinement interventions in v0.43+ are
> required. Necessity is established at one hazard level (h=8) on
> one seed band (41..48); cross-stream calibration of this finding
> is reserved for v0.43+. Sufficiency is NOT tested."

> **MECHANISM_GENERAL_DISRUPTION phrase:** "Hard-killing the
> tick-50 leader lineage disrupts post-50 dominance at h=8, but a
> size-matched non-leader removal produces a comparable disruption.
> The post-50 dominance pattern is **size-shock-sensitive**, not
> leader-identity-specific. The v0.34..v0.41 leader-advantage
> framing names a correlate but not a mechanism. v0.43 candidate:
> finer-grained control sweep (kill smaller non-leaders; spread
> across size buckets) to test whether any large-lineage shock
> disrupts the pattern equivalently, or whether there is a graded
> size-effect. Mechanism remains unidentified at the leader-
> identity level."

> **MECHANISM_NOT_NECESSARY phrase:** "Hard-killing the tick-50
> leader lineage does not materially disrupt the post-50 dominance
> pattern at h=8. A surviving lineage reconstitutes concentration
> of comparable share. The tick-50 leader's identity is **not
> necessary** under the tested substrate; post-50 dominance is a
> property of the chamber + population dynamics, not of the
> specific tick-50 leader lineage. v0.34..v0.41's leader-advantage
> correlation reflects which lineage HAPPENED to be ahead at tick
> 50, not a causal lever the leader holds. v0.43 candidate: pivot
> to substrate-level interventions (resource concentration shock,
> hazard relocation) rather than lineage-level interventions."

To be reused verbatim if the corresponding verdict fires.

### Caveats — locked, must appear in Results

- **Per-arm n is 8.** Each arm × hazard mean is over 8 runs. The
  ±0.15 / ±0.10 thresholds are conservative on n=8 but not bullet-
  proof against noise excursions. v0.43 may increase n if v0.42
  lands in MECHANISM_INDETERMINATE territory or near the threshold
  boundaries.
- **Necessity only.** v0.42 does NOT test sufficiency. Even on
  MECHANISM_NECESSITY_SUPPORTED, the mechanism (which property of
  the leader produces the necessity effect) is not identified;
  v0.43+ refinement is required.
- **One seed band.** Seeds 41..48 only. Cross-stream calibration of
  the intervention is a v0.43+ candidate. Inheriting the v0.39 →
  v0.40 → v0.41 lesson: a single-stream intervention result can be
  noise-driven; if v0.42 fires, calibrating on a second seed band
  (49..56) is the discipline-canonical follow-up.
- **Two hazards only.** h=0 and h=8. The secondary test treats
  these as the contrast set. Hazard-grid expansion to h=4 / h=12
  is a v0.43+ candidate.
- **`control_unavailable` runs are excluded from C's aggregation.**
  They are reported in `c_control_availability.csv` as a separate
  rate. If `n_control_unavailable / n_runs_total_C > 0.25`, the
  control sample is structurally compromised and the verdict is
  flagged in Results (but the locked rule still fires whatever it
  fires; this is reported, not gated).
- **Intervention is hard kill.** All agents of the chosen lineage
  are extincted at the tick-50/tick-51 boundary. Pool residual is
  credited normally. No biological-realism claim is made. Hard
  kill is the cleanest causal probe, not the most realistic.
- **No mechanism declaration even on the strongest outcome.** Even
  on MECHANISM_NECESSITY_SUPPORTED, v0.42 only establishes that
  leader-identity is necessary at one hazard, on one seed band,
  under one intervention type. Mechanism specificity (which
  property of the leader carries the effect) requires v0.43+
  intervention refinement.
- **Effect-size budget.** v0.38's pooled M3 spread was +5.042;
  v0.41's per-stream M3 spreads ranged +2.031 to +6.125. The
  primary observable here is `top_lineage_b50_share` (range [0,
  1]), not leader_advantage; the 0.15 threshold corresponds to
  ~20% of the typical baseline share (0.66–0.78). This is large
  enough to be meaningful but small enough to be statistically
  detectable on n=8.

### Reachability — sanity check

All three verdicts are arithmetically reachable:

- **MECHANISM_NECESSITY_SUPPORTED**: requires B share to drop by
  ≥ 0.15 from A AND C share to stay within ±0.10 of A. Both bars
  are independent and live; a real mechanism would land here.
- **MECHANISM_GENERAL_DISRUPTION**: requires B share AND C share
  both to drop by ≥ 0.10 from A. If the system is fragile to any
  large-lineage removal, this is where it lands.
- **MECHANISM_NOT_NECESSARY**: requires B share to NOT drop by
  ≥ 0.15. If post-50 dominance reconstitutes from any survivor,
  this is where it lands.

The rule space genuinely separates the three.

### Anchor identity

- v0.42 inherits no cross-version artifact-identity anchors against
  prior reducer outputs (its corpus is new). It does inherit one
  byte-identity anchor: re-running a sampled v0.41 seed with
  `optional_intervention=None` must produce events.jsonl byte-
  identical to v0.41's sealed reference (regression guard, H2e).

## Decision rules

### Primary

| `b_passes` | `c_passes` | verdict                          |
|:----------:|:----------:|----------------------------------|
| True       | True       | **MECHANISM_NECESSITY_SUPPORTED** |
| True       | False (C drops too) | **MECHANISM_GENERAL_DISRUPTION** |
| True       | False (C non-comparable) | **MECHANISM_NECESSITY_SUPPORTED** ⚠ flag c_control_availability |
| False      | any        | **MECHANISM_NOT_NECESSARY**      |

(The `c_passes=False, c-share>a-share+0.10` cell — C share rises
above A — is theoretically possible but mechanistically unmotivated.
If observed, the audit halts loud with `LineageReplayError`: this
indicates a substrate artefact we don't currently model.)

### Secondary (does not fire verdict; descriptive context only)

`hazard_amplified := abs(delta_b_minus_a_h8) > abs(delta_b_minus_a_h0)`.
Reports whether the necessity effect is hazard-amplified. Strong
hazard amplification + primary firing is the strongest possible
result.

### Halt conditions

- **H1 fails** — v0.34..v0.41 reducer surface mutated, OR
  byte-identity regression test fails. Halt; revert.
- **H2a fails** — run count != 48. Halt.
- **H2b fails** — intervention fires per arm violate locked counts.
  Halt.
- **H2c fails** — `effective_tick` != 51 on any fired event. Halt.
- **H2d fails** — `AgentDied(cause="intervention_killed")` count
  mismatch with `n_killed` summary field. Halt.
- **H2e fails** — sampled v0.41 seed produces non-byte-identical
  events.jsonl with `optional_intervention=None`. Halt.
- **H3 / H4 fail** — pre-v0.42 contract broken by v0.42 additions.
  Halt; revert.
- **C-rises-above-A cell** — substrate artefact unmodeled. Halt
  loud; do NOT silently bin into one of the three verdicts.

## Out of scope (v0.42)

- Sufficiency testing.
- Mechanism specificity (which property of the leader).
- Hazard generalisation beyond {0, 8}.
- Cross-stream calibration of the intervention beyond seeds 41..48.
- HedonismPolicy comparisons.
- Mesa migration.
- Edits to existing v0.34..v0.41 reducer surface or pre-v0.42 arm
  tuples.
- Birth-suppression, energy-drain, spatial-relocation, sufficiency-
  injection interventions.
- Changes to existing chamber, policy, or population dynamics
  outside the intervention hook.

## Implementation notes

### File-level changes

- **New (in `src/`):**
  - `src/hedonism_harness/core/interventions.py` (~300 LOC).
- **Modified (in `src/`):**
  - `src/hedonism_harness/core/world.py` (or chamber runner — exact
    site at implementation time): one new optional parameter
    `optional_intervention: InterventionConfig | None = None` on
    the run-orchestration entry point, plus the apply-intervention
    block at the tick-50/tick-51 boundary. **Default-None path
    byte-identical.**
  - `src/hedonism_harness/experiments/comparison_grid.py`: one new
    constant `V0_42_INTERVENTION_ARMS`, plus possibly an additive
    field on `Arm` (`intervention_kind: str = "null"` default) if
    that's the cleanest wiring. The default value preserves
    byte-identity for all v0.21..v0.41 arms.
  - The central event spec (likely `core/events.py` or similar):
    one new event class `LineageKilledByIntervention` and one new
    `AgentDied.cause` string `"intervention_killed"`. Both purely
    additive.
- **New (in `scripts/`):**
  - `scripts/v0.42_sweep.py` (~100 LOC, mirrors v0.41 sweep).
  - `scripts/v0_42_intervention_audit.py` (~600 LOC).
- **New (in `tests/`):**
  - `tests/test_interventions.py` (~250 LOC).
  - `tests/test_world_intervention_hook.py` (~150 LOC, including
    the byte-identity regression test).
  - `tests/test_v0_42_sweep.py` (~120 LOC).
  - `tests/test_v0_42_intervention_audit.py` (~500 LOC).
- **Documented:** this pre-reg. Results appended after the audit
  runs.
- **Manifest:** new file
  `docs/artifacts/v0.34_v0.42_local_corpus_manifest.md` post-
  Results. The v0.34_v0.41 manifest is preserved as a sealed
  historical record.

### Tests required (locked at pre-reg time)

- **Intervention module:**
  - `Tick50LineageKillIntervention` selects the leader correctly
    given a synthetic tick-50 living-agent state.
  - Tie-break by lowest lineage_id when leader counts tie.
  - Size-matched non-leader selection picks the closest non-leader
    to the leader's count.
  - Tie-break by lowest lineage_id when non-leader counts tie.
  - `control_unavailable=True` when no non-leader has any living
    agents.
  - `kind="null"` returns `fired=False` and does nothing.
- **World hook:**
  - Default `optional_intervention=None` produces byte-identical
    events.jsonl on a sampled v0.41 seed.
  - Intervention fires at the correct boundary (after tick 50
    closes, before tick 51 begins).
  - `LineageKilledByIntervention` event is emitted exactly once.
  - All killed agents emit `AgentDied(cause="intervention_killed")`.
  - Pool residual is conserved (i.e., the same accounting that
    starvation/injury deaths use applies to intervention deaths).
- **Sweep:** locked constants, arm tuple, seeds, hazards.
- **Audit:** locked thresholds, all 5 H2 halts, primary/secondary
  test arithmetic, three-way verdict, locked-phrase regression
  guards, end-to-end synthetic fixture.

### Determinism contract

- Selection rules are pure functions of tick-50 living-agent state.
- No new RNG introduced.
- Default-None hook path is byte-identical to pre-v0.42.
- Re-running v0.42 sweep with the same seeds produces byte-
  identical events.jsonl files.

### LOC estimate

- `interventions.py` + world hook + arm field: ~400 LOC.
- Sweep + audit: ~700 LOC.
- 4 test files: ~1,000 LOC.
- This doc: ~700 LOC.
- Manifest (post-Results): ~200 LOC.

Total v0.42: ~3,000 LOC. Tests should bring the suite from 1,225
to ~1,265 (+~40).

### CI gate at pre-reg time

```
uv run ruff check .             ok
uv run ruff format --check .    ok
uv run pytest                   1225 passed, 6 skipped (baseline)
uv run python scripts/core_smoke_test.py   ok
```

(Pre-reg adds no executable code; CI is identical to v0.41 close.)

## Results

_To be appended after the v0.42 sweep + audit run on the 48-run
corpus._
